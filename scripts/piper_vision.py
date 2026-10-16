#!/usr/bin/env python3
"""Find the green roll of tape in the fixed Pi camera's view on every frame and send where it is
(issue #19). Runs on the arm Pi in ~/vision-venv (numpy, opencv-python-headless); the arm venv
has neither, so piper_seek_tape.py starts this as its own process and reads it over UDP.

    ~/vision-venv/bin/python piper_vision.py --udp 5005 --record run.mjpeg --log run_vision.csv

Camera. The full-field 2304x1296 mode (2x2 binned) runs at up to 56 fps; the 120 fps mode is a
centre crop that cuts off the table in front of the arm, including the roll's start spot (it sits
at the crop's bottom edge). rpicam-vid scales the full field to 1152x648 YUV420 and pipes raw
frames to stdout (the Pi 5 has no H.264 encoder, and raw frames need no decoding).

Detection. Green in HSV (the same thresholds that find the roll in the run videos), inside the
part of the image the arm can reach (the camera calibration puts the reachable table and shelf in
u 140..1520, v >= 850 of the 2304x1296 image; outside that are the glass door and a green box),
then the connected blob nearest the last one (or the largest). Each frame sends one JSON datagram:
the capture time, the bbox centre and size in 2304x1296 pixels, the blob's area, and for each
surface the roll could stand on (table, 60 mm shelf) where the ray through the bbox's bottom
meets it and how well the bbox size fits that distance.

Recording. Every --record-every'th frame goes to an MJPEG file with a .pts file alongside (ms
from the first frame), the same layout rpicam-vid --save-pts writes, so the run can be turned
into a GIF on the runner.
"""
import argparse
import json
import os
import queue
import signal
import socket
import subprocess
import threading
import time

import cv2
import numpy as np

W, H = 1152, 648          # output size; image coordinates are reported at 2x (2304x1296)
ROI = (140, 850, 1520, 1296)  # u0, v0, u1, v1 in 2304x1296 pixels: the reachable table and shelf
HSV_LO, HSV_HI = (34, 100, 55), (76, 255, 255)  # roll: H 35-66, S 75-210, V 45-170
MIN_AREA = 40             # px at 1152x648; the roll is ~470 on the table, ~200 on the shelf


class Camera:
    """Pinhole + one radial term, fitted to the arm (camera.json); pixels in 2304x1296."""

    def __init__(self, path):
        c = json.load(open(path))
        self.K = np.array([[c["f"], 0, c["cx"]], [0, c["f"], c["cy"]], [0, 0, 1.0]])
        self.dist = np.array([c["k1"], 0, 0, 0, 0.0])
        self.R, _ = cv2.Rodrigues(np.array(c["rvec"], float))
        self.C = -self.R.T @ np.array(c["tvec"], float)  # camera centre, arm frame (mm)
        self.f = c["f"]

    def to_plane(self, u, v, z):
        """Where the ray through pixel (u, v) meets the horizontal plane at height z (mm)."""
        n = cv2.undistortPoints(np.array([[[u, v]]], float), self.K, self.dist).ravel()
        d = self.R.T @ np.array([n[0], n[1], 1.0])
        s = (z - self.C[2]) / d[2]
        return self.C + s * d


# The roll's bbox is about ROLL_BOX_MM tall in 3D (49 mm across plus the tape's 18 mm depth
# seen from 12 deg above: 66 px at 771 mm in the 2026-10-16 test 1 video). Which surface it
# stands on (table, or the 60 mm shelf) is the one whose distance makes that size match.
# Where it stands comes from the bottom of its bbox (its lowest point, on the surface), the
# feature the camera was fitted with: green against the black shelf or the pale table is a
# sharp edge, while the top of the ring washes out in the light.
ROLL_BOX_MM = 55.3
SURFACES = (0.0, 60.0)


def writer(q, path):
    with open(path, "wb") as f, open(path + ".pts", "w", buffering=1) as p:
        p.write("# timecode format v2\n")
        while True:
            item = q.get()
            if item is None:
                return
            ms, jpg = item
            f.write(jpg)
            p.write(f"{ms:.3f}\n")


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--udp", type=int, default=5005, help="send detections to 127.0.0.1:PORT")
    ap.add_argument("--fps", type=int, default=56)
    ap.add_argument("--record", help="MJPEG file for every --record-every'th frame")
    ap.add_argument("--record-every", type=int, default=4)
    ap.add_argument("--log", help="CSV of every frame's detection")
    ap.add_argument("--seconds", type=float, default=300.0, help="stop after this long")
    ap.add_argument("--camera", default=os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                                     "camera.json"))
    args = ap.parse_args()
    # a SIGTERM from piper_seek_tape.py must still close the recording and the log
    signal.signal(signal.SIGTERM, lambda *a: (_ for _ in ()).throw(SystemExit(0)))

    u0, v0, u1, v1 = (c // 2 for c in ROI)
    roi = np.zeros((H - v0, W), np.uint8)
    roi[:, u0:u1] = 255
    cam = Camera(args.camera)
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    proc = subprocess.Popen(
        ["rpicam-vid", "-n", "-t", "0", "--mode", "2304:1296:10:P", "--width", str(W),
         "--height", str(H), "--framerate", str(args.fps), "--codec", "yuv420", "--flush",
         "--denoise", "cdn_fast", "-o", "-"],
        stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, bufsize=0)
    q, wt = None, None
    if args.record:
        q = queue.Queue(maxsize=64)
        wt = threading.Thread(target=writer, args=(q, args.record), daemon=True)
        wt.start()
    log = open(args.log, "w", buffering=1) if args.log else None
    if log:
        log.write("k,t,u,v,bw,bh,area,n,x0,y0,s0,x60,y60,s60\n")
    n = W * H * 3 // 2
    buf = bytearray(n)
    mv = memoryview(buf)
    last, k, t_first, t_end = None, 0, None, time.time() + args.seconds
    kernel = np.ones((3, 3), np.uint8)
    try:
        while time.time() < t_end:
            got = 0
            while got < n:
                r = proc.stdout.readinto(mv[got:])
                if not r:
                    raise SystemExit("camera stream ended")
                got += r
            t = time.time()
            if t_first is None:
                t_first = t
            yuv = np.frombuffer(buf, np.uint8).reshape(H * 3 // 2, W)
            bgr = cv2.cvtColor(yuv, cv2.COLOR_YUV2BGR_I420)
            hsv = cv2.cvtColor(bgr[v0:], cv2.COLOR_BGR2HSV)
            m = cv2.inRange(hsv, HSV_LO, HSV_HI) & roi
            m = cv2.morphologyEx(m, cv2.MORPH_OPEN, kernel)
            cnt, lab, st, cen = cv2.connectedComponentsWithStats(m)
            cand = [i for i in range(1, cnt) if st[i, 4] >= MIN_AREA]
            msg = {"k": k, "t": t, "u": None, "n": len(cand)}
            if cand:
                if last is not None:
                    i = min(cand, key=lambda i: (cen[i][0] - last[0]) ** 2 + (cen[i][1] - last[1]) ** 2)
                    if (cen[i][0] - last[0]) ** 2 + (cen[i][1] - last[1]) ** 2 > 40 ** 2:
                        i = max(cand, key=lambda i: st[i, 4])
                else:
                    i = max(cand, key=lambda i: st[i, 4])
                x, y, bw, bh, area = (int(v) for v in st[i])
                last = cen[i]
                msg.update(u=2 * (x + bw / 2.0), v=2 * (v0 + y + bh / 2.0), bw=2 * bw, bh=2 * bh,
                           area=4 * area)
                # each surface hypothesis: roll centre (x, y) and how well the bbox size fits
                hyp = []
                for zs in SURFACES:
                    P = cam.to_plane(msg["u"], 2.0 * (v0 + y + bh), zs)
                    size = cam.f * ROLL_BOX_MM / float(np.linalg.norm(P - cam.C))
                    hyp.append([round(float(P[0]), 1), round(float(P[1]), 1), zs,
                                round(float(np.log(msg["bh"] / size)), 3)])
                msg["hyp"] = hyp
            sock.sendto(json.dumps(msg).encode(), ("127.0.0.1", args.udp))
            if log:
                log.write(f"{k},{t:.4f}," + (
                    f"{msg['u']:.1f},{msg['v']:.1f},{msg['bw']},{msg['bh']},{msg['area']}"
                    if msg["u"] is not None else ",,,,") + f",{len(cand)}," + (
                    ",".join(f"{h[0]},{h[1]},{h[3]}" for h in msg["hyp"])
                    if msg["u"] is not None else ",,,,,") + "\n")
            if q is not None and k % args.record_every == 0 and not q.full():
                ok, jpg = cv2.imencode(".jpg", bgr, [cv2.IMWRITE_JPEG_QUALITY, 80])
                if ok:
                    q.put(((t - t_first) * 1000.0, jpg.tobytes()))
            k += 1
    finally:
        proc.terminate()
        try:
            proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            proc.kill()
        if q is not None:
            q.put(None)
            wt.join(timeout=10)
        if log:
            log.close()


if __name__ == "__main__":
    main()
