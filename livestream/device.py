"""PiPER cell livestream with inline face blurring.

Pipeline::

    rpicam-vid (raw YUV420) -> this script (OpenCV: face blur, fixed masks,
    timestamp) -> ffmpeg (libx264) -> RTMP -> YouTube

The YouTube broadcast is created and ended through the lab's streaming Lambda
(vertical-cloud-lab/streamingLambda), with the same ``create``/``end`` calls as
the byu-vcl stream cams' ``device.py`` (ac-training-lab ``87a3ccb`` plus local
patches). Unlike those, every frame goes through Python, so faces can be
blurred before anything is encoded. Nothing unblurred is ever written to
ffmpeg: if the face detector cannot load, the script exits; if processing a
frame fails, that frame is dropped.

Settings come from ``my_secrets.py`` next to this file; see
``my_secrets_example.py``.
"""

import json
import os
import shutil
import signal
import subprocess
import sys
import threading
import time
from pathlib import Path

import cv2
import numpy as np
import requests

import my_secrets as S

HERE = Path(__file__).resolve().parent

RESOLUTION_MAP = {
    "144p": (256, 144),
    "240p": (426, 240),
    "360p": (640, 360),
    "480p": (854, 480),
    "720p": (1280, 720),
    "1080p": (1920, 1080),
}

# Required settings.
CAM_NAME = S.CAM_NAME
WORKFLOW_NAME = S.WORKFLOW_NAME
LAMBDA_FUNCTION_URL = S.LAMBDA_FUNCTION_URL
PRIVACY_STATUS = getattr(S, "PRIVACY_STATUS", "private")

# Optional settings.
RESOLUTION = getattr(S, "RESOLUTION", "720p")
FRAME_RATE = getattr(S, "FRAME_RATE", 10)
SENSOR_MODE = getattr(S, "SENSOR_MODE", "2304:1296")
CAMERA_VFLIP = getattr(S, "CAMERA_VFLIP", False)
CAMERA_HFLIP = getattr(S, "CAMERA_HFLIP", False)
TIMESTAMP_OVERLAY = getattr(S, "TIMESTAMP_OVERLAY", True)
VIDEO_BITRATE = getattr(S, "VIDEO_BITRATE", "1500k")

FACE_MODEL = getattr(S, "FACE_MODEL", str(HERE / "face_detection_yunet_2023mar.onnx"))
FACE_DETECT_WIDTH = getattr(S, "FACE_DETECT_WIDTH", 960)
FACE_SCORE_THRESHOLD = getattr(S, "FACE_SCORE_THRESHOLD", 0.5)
FACE_BOX_MARGIN = getattr(S, "FACE_BOX_MARGIN", 0.6)
FACE_HOLD_FRAMES = getattr(S, "FACE_HOLD_FRAMES", 8)
# Rectangles that are always pixelated, as (x0, y0, x1, y1) fractions of the
# frame. Use them for parts of the view that look into the rest of the lab.
MASK_RECTS = getattr(S, "MASK_RECTS", [])
# OpenCV threads. The arm Pi also runs the arm, so leave it cores to spare.
CV_THREADS = getattr(S, "CV_THREADS", 2)
# Every SNAPSHOT_SEC, the last frame sent (already blurred) is saved here, so
# what goes out can be checked over SSH without opening YouTube.
SNAPSHOT_PATH = getattr(S, "SNAPSHOT_PATH", "/tmp/picam-stream-latest.jpg")
SNAPSHOT_SEC = getattr(S, "SNAPSHOT_SEC", 30)


def call_lambda(action, privacy_status="private"):
    payload = {
        "action": action,
        "cam_name": CAM_NAME,
        "workflow_name": WORKFLOW_NAME,
        "privacy_status": privacy_status,
    }
    print(f"Sending to Lambda: {payload}", flush=True)
    try:
        response = requests.post(LAMBDA_FUNCTION_URL, json=payload, timeout=60)
    except requests.exceptions.RequestException as e:
        raise RuntimeError(f"Lambda request failed: {e}")
    print(f"Lambda status code: {response.status_code}", flush=True)
    if not response.ok:
        raise RuntimeError(f"Lambda HTTP {response.status_code}: {response.text}")
    try:
        result = response.json()
    except ValueError:
        return response.text
    if isinstance(result, dict) and "statusCode" in result and "body" in result:
        return result["body"]
    return result


def create_broadcast():
    try:
        call_lambda("end")
    except RuntimeError as e:
        print(f"Could not end previous broadcast; continuing: {e}", flush=True)
    body = call_lambda("create", privacy_status=PRIVACY_STATUS)
    result = json.loads(body) if isinstance(body, str) else body
    try:
        ffmpeg_url = result["result"]["ffmpeg_url"]
    except (KeyError, TypeError) as e:
        raise RuntimeError(f"ffmpeg_url not in Lambda response: {e}")
    # Log the watch link but never the stream key.
    info = {k: v for k, v in result["result"].items() if k != "ffmpeg_url"}
    print(f"Broadcast: {info}", flush=True)
    return ffmpeg_url


class FaceBlur:
    def __init__(self, width, height):
        if not Path(FACE_MODEL).exists():
            raise SystemExit(f"Face model missing: {FACE_MODEL}; refusing to stream")
        self.width, self.height = width, height
        self.scale = min(1.0, FACE_DETECT_WIDTH / width)
        dw, dh = int(round(width * self.scale)), int(round(height * self.scale))
        self.det_size = (dw, dh)
        self.detector = cv2.FaceDetectorYN.create(
            FACE_MODEL, "", self.det_size, FACE_SCORE_THRESHOLD, 0.3, 5000
        )
        self.held = []  # [(x0, y0, x1, y1, frames_left)]
        self.masks = [
            (int(x0 * width), int(y0 * height), int(x1 * width), int(y1 * height))
            for x0, y0, x1, y1 in MASK_RECTS
        ]

    def detect(self, frame):
        small = frame if self.scale == 1.0 else cv2.resize(frame, self.det_size)
        _, faces = self.detector.detect(small)
        boxes = []
        if faces is not None:
            for f in faces:
                x, y, w, h = (f[:4] / self.scale).tolist()
                mx, my = w * FACE_BOX_MARGIN, h * FACE_BOX_MARGIN
                boxes.append(
                    (
                        max(0, int(x - mx)),
                        max(0, int(y - my * 1.3)),  # extra room for hair
                        min(self.width, int(x + w + mx)),
                        min(self.height, int(y + h + my)),
                    )
                )
        return boxes

    @staticmethod
    def pixelate(frame, x0, y0, x1, y1, block=12):
        roi = frame[y0:y1, x0:x1]
        if roi.size == 0:
            return
        h, w = roi.shape[:2]
        small = cv2.resize(
            roi, (max(1, w // block), max(1, h // block)), interpolation=cv2.INTER_AREA
        )
        frame[y0:y1, x0:x1] = cv2.resize(small, (w, h), interpolation=cv2.INTER_NEAREST)

    def __call__(self, frame):
        new = self.detect(frame)
        # Hold every box for a few frames, so a face the detector misses for a
        # frame or two (motion blur, turning away) stays covered.
        self.held = [(*b, FACE_HOLD_FRAMES) for b in new] + [
            (*b[:4], b[4] - 1) for b in self.held if b[4] > 1
        ]
        for x0, y0, x1, y1, _ in self.held:
            self.pixelate(frame, x0, y0, x1, y1, block=max(6, (x1 - x0) // 5))
        for x0, y0, x1, y1 in self.masks:
            self.pixelate(frame, x0, y0, x1, y1, block=24)
        return len(new)


class LatestFrame(threading.Thread):
    """Reads raw I420 frames from the camera and keeps only the newest."""

    def __init__(self, stream, width, height):
        super().__init__(daemon=True)
        self.stream, self.size = stream, width * height * 3 // 2
        self.width, self.height = width, height
        self.cond = threading.Condition()
        self.frame, self.seq, self.eof = None, 0, False

    def run(self):
        while True:
            buf = self.stream.read(self.size)
            if not buf or len(buf) < self.size:
                break
            with self.cond:
                self.frame, self.seq = buf, self.seq + 1
                self.cond.notify()
        with self.cond:
            self.eof = True
            self.cond.notify()

    def get(self, last_seq, timeout=5.0):
        with self.cond:
            self.cond.wait_for(lambda: self.seq != last_seq or self.eof, timeout)
            if self.eof or self.seq == last_seq:
                return None, last_seq
            yuv = np.frombuffer(self.frame, np.uint8).reshape(
                self.height * 3 // 2, self.width
            )
            return cv2.cvtColor(yuv, cv2.COLOR_YUV2BGR_I420), self.seq


def camera_cmd(width, height):
    cmd = shutil.which("rpicam-vid") or shutil.which("libcamera-vid")
    if not cmd:
        raise SystemExit("rpicam-vid not found")
    args = [cmd, "--nopreview", "-t", "0", "--flush", "--codec", "yuv420",
            "--width", str(width), "--height", str(height),
            "--framerate", str(FRAME_RATE)]  # fmt: skip
    if SENSOR_MODE:
        args += ["--mode", SENSOR_MODE]
    if CAMERA_VFLIP:
        args.append("--vflip")
    if CAMERA_HFLIP:
        args.append("--hflip")
    return args + ["-o", "-"]


def ffmpeg_cmd(ffmpeg_url, width, height):
    gop = str(FRAME_RATE * 2)
    return [
        "ffmpeg", "-hide_banner", "-loglevel", "warning", "-stats_period", "60",
        "-f", "lavfi", "-i", "anullsrc=channel_layout=stereo:sample_rate=44100",
        "-thread_queue_size", "64", "-use_wallclock_as_timestamps", "1",
        "-f", "rawvideo", "-pix_fmt", "bgr24", "-s", f"{width}x{height}",
        "-i", "pipe:0",
        "-map", "1:v", "-map", "0:a",
        "-c:v", "libx264", "-preset", "ultrafast", "-tune", "zerolatency",
        "-pix_fmt", "yuv420p", "-r", str(FRAME_RATE), "-fps_mode", "cfr",
        "-g", gop, "-keyint_min", gop, "-sc_threshold", "0",
        "-b:v", VIDEO_BITRATE, "-maxrate", VIDEO_BITRATE, "-bufsize", "3000k",
        "-c:a", "aac", "-b:a", "64k",
        "-f", "flv", ffmpeg_url,
    ]  # fmt: skip


def draw_timestamp(frame):
    text = time.strftime("%Y-%m-%d %H:%M:%S %Z")
    scale = frame.shape[0] / 720 * 0.8
    thick = max(1, int(round(scale * 2)))
    (tw, th), base = cv2.getTextSize(text, cv2.FONT_HERSHEY_SIMPLEX, scale, thick)
    x, y = frame.shape[1] - tw - 12, 12 + th
    cv2.rectangle(frame, (x - 6, y - th - 6), (x + tw + 6, y + base + 4), (0, 0, 0), -1)
    cv2.putText(frame, text, (x, y), cv2.FONT_HERSHEY_SIMPLEX, scale,
                (255, 255, 255), thick, cv2.LINE_AA)  # fmt: skip


def stream_once(ffmpeg_url, width, height, blur):
    """Run one camera -> blur -> ffmpeg session until something exits."""
    # Buffered stdout, so read(n) returns a whole frame rather than whatever
    # the pipe holds. The camera's own log goes to the journal.
    cam = subprocess.Popen(camera_cmd(width, height), stdout=subprocess.PIPE)
    enc = subprocess.Popen(ffmpeg_cmd(ffmpeg_url, width, height), stdin=subprocess.PIPE)
    reader = LatestFrame(cam.stdout, width, height)
    reader.start()
    seq, n, faces, t0, slow = 0, 0, 0, time.monotonic(), 0.0
    last_snap = 0.0
    try:
        while enc.poll() is None:
            frame, seq = reader.get(seq)
            if frame is None:
                print("Camera stopped delivering frames", flush=True)
                break
            t = time.monotonic()
            try:
                faces += blur(frame)
            except Exception as e:  # never send a frame that was not blurred
                print(f"Frame dropped, blur failed: {e}", flush=True)
                continue
            if TIMESTAMP_OVERLAY:
                draw_timestamp(frame)
            slow = max(slow, time.monotonic() - t)
            enc.stdin.write(frame.tobytes())
            n += 1
            if SNAPSHOT_PATH and time.monotonic() - last_snap >= SNAPSHOT_SEC:
                last_snap = time.monotonic()
                cv2.imwrite(SNAPSHOT_PATH + ".tmp.jpg", frame)
                os.replace(SNAPSHOT_PATH + ".tmp.jpg", SNAPSHOT_PATH)
            if time.monotonic() - t0 >= 120:
                dt = time.monotonic() - t0
                print(f"{n / dt:.1f} fps out, {faces} face detections, "
                      f"slowest frame {slow * 1000:.0f} ms", flush=True)  # fmt: skip
                n, faces, t0, slow = 0, 0, time.monotonic(), 0.0
    except BrokenPipeError:
        print("ffmpeg closed its input", flush=True)
    finally:
        for p in (cam, enc):
            if p.poll() is None:
                p.terminate()
        for p in (cam, enc):
            try:
                p.wait(timeout=10)
            except subprocess.TimeoutExpired:
                p.kill()


def main():
    if RESOLUTION not in RESOLUTION_MAP:
        raise SystemExit(f"Invalid RESOLUTION {RESOLUTION!r}")
    if not isinstance(FRAME_RATE, int) or FRAME_RATE <= 0:
        raise SystemExit(f"Invalid FRAME_RATE {FRAME_RATE!r}")
    width, height = RESOLUTION_MAP[RESOLUTION]
    cv2.setNumThreads(CV_THREADS)
    blur = FaceBlur(width, height)  # load before going live: fail closed
    print(f"{RESOLUTION} {width}x{height} @ {FRAME_RATE} fps, sensor mode "
          f"{SENSOR_MODE or 'auto'}, face detection at {blur.det_size}, "
          f"{len(MASK_RECTS)} fixed masks", flush=True)  # fmt: skip

    signal.signal(signal.SIGTERM, lambda *_: sys.exit(0))
    ffmpeg_url = create_broadcast()
    while True:
        print("Starting stream", flush=True)
        stream_once(ffmpeg_url, width, height, blur)
        print("Stream ended; retrying in 5 s", flush=True)
        time.sleep(5)


if __name__ == "__main__":
    os.chdir(HERE)
    main()
