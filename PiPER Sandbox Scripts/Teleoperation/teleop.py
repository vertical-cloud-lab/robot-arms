#!/usr/bin/env python3
"""Teleoperate the lab's AgileX PiPER from an SO-101 leader arm (#46, #67). Run it on the
computer the leader is plugged into, from a clone of this repo:

    pip install -r "PiPER Sandbox Scripts/Teleoperation/requirements.txt"
    python "PiPER Sandbox Scripts/Teleoperation/teleop.py" --check     # preflight, moves nothing
    python "PiPER Sandbox Scripts/Teleoperation/teleop.py" --dry-run   # simulated arm on the Pi
    python "PiPER Sandbox Scripts/Teleoperation/teleop.py"             # the real arm
    python "PiPER Sandbox Scripts/Teleoperation/teleop.py" --record    # ... and keep the video

The first run asks for the arm Pi's address and login, and the camera Pi's (optional), and
saves them to teleop.local.json beside this file, which git ignores. Options given on the
command line win over that file. The arm Pi is the one with the USB-CAN adapter and the relay
(rpi-5-mpzy since 2026-10-30); the HQ camera is on the gripper Pi (rpi-5-76zj). This computer
needs SSH to both: the lab tailnet with a grant, or the lab network.

1. Reads the leader's six Feetech STS3215 servos (IDs 1-6, 1 Mbit/s) on --port with one SYNC
   READ per sample, --hz times a second, and maps them to PiPER joints: J1 = -pan,
   J2 = lift + 96.2, J3 = elbow - 88.4, J5 = wrist_flex - 2.8, J6 = -roll
   (analysis/joint_map.json gives the joints and their directions), each scaled so the ends
   of the leader's calibrated range are the ends of the arm's (ARM_RANGE). J4 has no SO-101
   joint; the Pi holds it centred, and keys 1 and 2 turn it.
2. Over ONE SSH connection, copies follower.py and ../Arm Control/'s Up_and_Down.py,
   fake_piper.py, arm_power.py and arm_home.json to ~/so101/ on the arm Pi, and runs the
   follower through arm_power.py's protocol (the Pi's own ~/arm_power.py when it has one). The
   relay switches the arm on now, and off only once the follower has parked it.
3. The follower raises the arm off its rest to READY. Line the leader up with it (the window
   shows each joint's difference), then HOLD SPACE to move; let go to stop. Q near READY parks
   the arm, powers it off and ends the session. If this script dies or the connection drops,
   the follower holds, then parks on its own after its --lost-s (10 s).
4. With a camera Pi set, a second SSH connection streams its HQ camera as MJPEG (rpicam-vid)
   into the window. Only the newest frame is decoded and shown, so video never queues up.
5. --record also saves every frame exactly as it arrives, and the window's text, to
   recordings/ beside this file, and once the arm has parked makes camera.mp4 (the camera
   alone) and window.mp4 (the window) from them. While the arm is driven nothing is encoded,
   and nothing more crosses the network or runs on the Pis. --render DIR makes them again.

Latency: the leader is read and commands are sent on their own thread at --hz (200 by
default), so neither the window, the video nor a recording can hold a command back. The end
of a session prints the ping round trip, the age of the newest command at the Pi, and the
leader read time.

Keys, in the teleop window: hold SPACE = move (Windows reads the key directly, so it works
whichever window has focus; elsewhere SPACE toggles); Ctrl+SPACE (Windows) = move until SPACE
is pressed again, which stops it at once; hold 1 or 2 (Windows) while moving = turn J4 slowly
one way or the other; Q = park and quit.

Test without the arm or the leader:  --fake-leader --local --dry-run --auto 10
"""
import argparse
import base64
import collections
import contextlib
import io
import json
import math
import os
import queue
import re
import shlex
import shutil
import subprocess
import sys
import tarfile
import threading
import time

HERE = os.path.dirname(os.path.abspath(__file__))
COMMON = os.path.join(os.path.dirname(HERE), "Arm Control")  # shared connect/power/park files
NAMES = ["shoulder_pan", "shoulder_lift", "elbow_flex", "wrist_flex", "wrist_roll", "gripper"]
PIPER = ["J1", "J2", "J3", "J5", "J6"]  # what the five body joints drive
PI_FILES = [os.path.join(HERE, "follower.py")] + [
    os.path.join(COMMON, n) for n in ("Up_and_Down.py", "fake_piper.py", "arm_power.py",
                                      "arm_home.json")]
# The ranges the arm was moved through by hand on 2026-11-12 (joint_watch.py), 1 deg in: the
# leader's ends map to these, and the follower clamps to them (--envelope).
ARM_RANGE = [(-150, 150), (0, 180), (-170, 0), (-70, 70), (-53.9, 179)]  # J1 J2 J3 J5 J6
LOCAL = os.path.join(HERE, "teleop.local.json")
SSH_OPTS = ["-T", "-o", "ServerAliveInterval=2", "-o", "ServerAliveCountMax=5",
            "-o", "ConnectTimeout=15", "-o", "IPQoS=ef"]
WINDOWS = os.name == "nt"


def stats_ms(xs):
    if not xs:
        return "no samples"
    xs = sorted(xs)
    return (f"median {xs[len(xs) // 2] * 1000:.1f} ms, 95th percentile "
            f"{xs[int(0.95 * (len(xs) - 1))] * 1000:.1f} ms, max {xs[-1] * 1000:.1f} ms "
            f"(n={len(xs)})")


# ------------------------------------------------------------------ the leader (Feetech bus)

class Leader:
    """Present_Position (address 56, 2 bytes) of servos 1-6, with one SYNC READ per sample."""

    ADDR, IDS = 56, (1, 2, 3, 4, 5, 6)

    def __init__(self, port, baud=1_000_000):
        import serial  # pyserial

        self.ser = serial.Serial(port, baud, timeout=0.05)
        self.ser.reset_input_buffer()
        self.use_sync, self.sync_ok, self.sync_miss = True, 0, 0

    @staticmethod
    def _chk(body):
        return (~sum(body)) & 0xFF

    def _send(self, sid, inst, params):
        body = [sid, len(params) + 2, inst, *params]
        self.ser.reset_input_buffer()
        self.ser.write(bytes([0xFF, 0xFF, *body, self._chk(body)]))

    def _parse(self, buf):
        out, i = {}, 0
        while i + 8 <= len(buf):
            if buf[i] == 0xFF and buf[i + 1] == 0xFF and buf[i + 3] == 4:
                pkt, chk = buf[i + 2:i + 7], buf[i + 7]
                if self._chk(pkt) == chk:
                    v = buf[i + 5] | buf[i + 6] << 8
                    out[buf[i + 2]] = -(v & 0x7FFF) if v & 0x8000 else v
                    i += 8
                    continue
            i += 1
        return out

    def read(self):
        got = {}
        if self.use_sync:
            self._send(0xFE, 0x82, [self.ADDR, 2, *self.IDS])
            got = self._parse(self.ser.read(8 * len(self.IDS)))
            if len(got) == len(self.IDS):
                self.sync_ok, self.sync_miss = self.sync_ok + 1, 0
                return [got[i] for i in self.IDS]
            # One lost reply only costs this sample a few single reads; SYNC READ is dropped
            # for good only if it has never answered (some adapters/firmware don't).
            self.sync_miss += 1
            if not self.sync_ok and self.sync_miss >= 3:
                self.use_sync = False
                print("leader: SYNC READ never answered, so reading the servos one at a time "
                      "(about six times slower)", flush=True)
        for sid in self.IDS:
            if sid in got:
                continue
            self._send(sid, 0x02, [self.ADDR, 2])
            one = self._parse(self.ser.read(8))
            if sid not in one:
                raise IOError(f"leader servo {sid} didn't answer on {self.ser.port}")
            got[sid] = one[sid]
        return [got[i] for i in self.IDS]


class Mapping:
    """Leader raw counts -> PiPER J1 J2 J3 J5 J6 (deg) and gripper stroke (mm). Each joint's
    calibrated range, end to end, spans the arm's (ARM_RANGE), in joint_map.json's direction."""

    def __init__(self, args):
        m = json.load(open(os.path.join(HERE, "analysis", "joint_map.json")))["nominal_map"]
        self.sign = [m[n]["sign"] for n in NAMES[:5]]
        path = args.calib or default_calib()
        if not (path and os.path.exists(path)):
            raise SystemExit("leader calibration: none found. The leader's range comes from "
                             "LeRobot's calibration: run lerobot-calibrate, or pass --calib. "
                             "Nothing was started on the Pi.")
        c = json.load(open(path))
        self.calib = {n: c[n] for n in NAMES}
        print(f"leader calibration: {path}")
        self.grip_range = args.gripper_range
        self.grip_min, self.grip_max = args.grip_min_mm, args.grip_max_mm
        self.grip_invert = args.gripper_invert

    def gripper_mm(self, raw):
        v = raw[5]
        if self.grip_range:
            lo, hi = self.grip_range
            pct = (v - lo) / (hi - lo)
        elif self.calib:
            c = self.calib["gripper"]
            pct = (v - c["range_min"]) / max(1, c["range_max"] - c["range_min"])
        else:
            return None  # unknown range: leave the PiPER's gripper alone
        pct = min(max(pct, 0.0), 1.0)
        pct = 1 - pct if self.grip_invert else pct
        return self.grip_min + pct * (self.grip_max - self.grip_min)

    def piper(self, raw):
        q = []
        for name, s, (lo, hi), v in zip(NAMES[:5], self.sign, ARM_RANGE, raw[:5]):
            c = self.calib[name]
            f = min(max((v - c["range_min"]) / max(1, c["range_max"] - c["range_min"]), 0.0), 1.0)
            if (s < 0) != bool(c.get("drive_mode")):
                f = 1 - f
            q.append(lo + f * (hi - lo))
        return q, self.gripper_mm(raw)


def default_calib():
    """Newest leader calibration; older LeRobot saves under so101_leader, newer under so_leader."""
    base = os.path.join(os.path.expanduser("~"), ".cache", "huggingface", "lerobot",
                        "calibration", "teleoperators")
    files = [os.path.join(base, d, f) for d in ("so101_leader", "so_leader")
             if os.path.isdir(os.path.join(base, d))
             for f in os.listdir(os.path.join(base, d)) if f.endswith(".json")]
    return max(files, key=os.path.getmtime) if files else None


class FakeLeader:
    """For testing without the leader: sweeps J1, J2 and the gripper around READY."""

    def __init__(self, back_at=None):
        self.t0 = None
        self.back_at = back_at  # seconds after READY to ease back to READY (for --auto)

    def piper(self, ready5):
        t = 0.0 if self.t0 is None else time.monotonic() - self.t0
        k = 1.0 if self.back_at is None else min(1.0, max(0.0, 1 - (t - self.back_at) / 2))
        q = list(ready5)
        q[0] += k * 25 * math.sin(0.8 * t)
        q[1] += k * 15 * (1 - math.cos(0.6 * t))
        q[4] += k * 20 * (1 - math.cos(0.5 * t)) / 2
        return q, k * (30 + 25 * math.sin(0.7 * t))


# ------------------------------------------------------------------ SSH and the Pi side

def ssh(host, user, extra, remote):
    return ["ssh", *SSH_OPTS, *extra, f"{user}@{host}" if user else host, remote]


def bundle():
    buf = io.BytesIO()
    with tarfile.open(fileobj=buf, mode="w:gz") as tar:
        for path in PI_FILES:
            tar.add(path, arcname=os.path.basename(path))
    return base64.b64encode(buf.getvalue()) + b"\n"


def start_follower(args):
    envelope = ",".join(f"{j}={lo:g}:{hi:g}" for j, (lo, hi) in zip(PIPER, ARM_RANGE))
    fargs = ["--envelope", envelope, *(args.follower_args or [])] + (
        ["--gripper", "--grip-max-mm", f"{args.grip_max_mm:g}"] if args.gripper else [])
    if args.dry_run:
        fargs = ["--dry-run", *fargs]
    if args.local:
        cmd = [sys.executable, "-u", os.path.join(HERE, "follower.py"), *fargs]
        blob = b""
    else:
        py = args.pi_python
        follower = f"{py} ~/so101/follower.py {shlex.join(fargs)}"
        if args.dry_run:  # simulated arm: no relay, so no arm_power.py
            run = f"exec {follower}"
        else:  # the Pi's own copy of the power protocol wins; the repo's is the fallback
            run = ('AP=~/arm_power.py; if [ ! -f "$AP" ]; then AP=~/so101/arm_power.py; '
                   'echo "@MSG ~/arm_power.py not found on the Pi: using the repo copy"; '
                   'elif ! cmp -s "$AP" ~/so101/arm_power.py; then echo "@MSG note: the Pi '
                   'copy of arm_power.py differs from the repo copy; using the Pi copy"; fi; '
                   f'exec {py} "$AP" run -- {follower}')
        blob = bundle()
        remote = (f"mkdir -p ~/so101 && head -c {len(blob)} | base64 -d | "
                  f"tar -xzf - -C ~/so101 && {run}")
        cmd = ssh(args.host, args.user, args.ssh_opt, remote)
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                            stderr=subprocess.STDOUT, bufsize=0)
    if blob:
        proc.stdin.write(blob)
        proc.stdin.flush()
    return proc


class Session:
    """The follower's output, parsed on a thread; commands written under a lock."""

    def __init__(self, proc):
        self.proc = proc
        self.hello = self.ready = self.state = self.bye = None
        self.rtt, self.rtt_all, self.age_all = [], [], []
        self.log = queue.Queue()
        self.wlock = threading.Lock()
        threading.Thread(target=self._read, daemon=True).start()

    def _read(self):
        for raw in self.proc.stdout:
            line = raw.decode("utf-8", "replace").rstrip("\r\n")
            kind, _, rest = line.partition(" ")
            try:
                if kind == "@S":
                    self.state = json.loads(rest)
                    if self.state.get("tpc") and self.state["ph"] == "follow":
                        self.age_all.append(time.time() - self.state["tpc"])
                elif kind == "@P":
                    self.rtt = (self.rtt + [time.time() - float(rest)])[-20:]
                    if self.hello:  # not the ones that waited for the follower to start
                        self.rtt_all.append(self.rtt[-1])
                elif kind == "@HELLO":
                    self.hello = json.loads(rest)
                    self.log.put(f"follower started: {rest}")
                elif kind == "@READY":
                    self.ready = json.loads(rest)["ready"]
                    self.log.put("arm at READY: line the leader up, then hold SPACE")
                elif kind == "@BYE":
                    self.bye = json.loads(rest)
                    self.log.put(f"follower exited: {rest}")
                elif kind == "@MSG":
                    self.log.put(rest)
                elif line.strip():
                    self.log.put("  pi> " + line)
            except (ValueError, KeyError):
                self.log.put("  pi> " + line)
        self.log.put("(connection to the Pi closed)")

    def send(self, text):
        with self.wlock:
            try:
                self.proc.stdin.write(text.encode() + b"\n")
                self.proc.stdin.flush()
                return True
            except (OSError, ValueError):
                return False


# ------------------------------------------------------------------ video

def full_view_mode(listing, idx):
    """From `rpicam-hello --list-cameras`: camera idx's smallest sensor mode that reads the
    whole sensor, as (rpicam --mode string, width, height), or None."""
    cam = full = bits = packed = best = None
    for line in listing.splitlines():
        m = re.match(r"\s*(\d+)\s*:\s*\S+\s*\[(\d+)x(\d+)", line)
        if m:
            cam, full = int(m.group(1)), (int(m.group(2)), int(m.group(3)))
            continue
        f = re.search(r"'[A-Z]+?(\d+)(_CSI2P)?'", line)
        if f:
            bits, packed = f.group(1), "P" if f.group(2) else "U"
        for w, h, x, y, cw, ch in re.findall(
                r"(\d+)x(\d+) \[[^\]]*?\((\d+), (\d+)\)/(\d+)x(\d+) crop\]", line):
            w, h = int(w), int(h)
            if (cam == idx and (int(x), int(y)) == (0, 0) and (int(cw), int(ch)) == full
                    and (best is None or w * h < best[1] * best[2])):
                best = (f"{w}:{h}:{bits}:{packed}", w, h)
    return best


def camera_cmd(args):
    """ssh command that streams the camera Pi's HQ camera (imx477, else camera 0) as MJPEG on
    stdout, showing the whole sensor. Left to itself, rpicam picks the sensor mode nearest the
    output size, and for 960x540 on the imx708 that is 1536x864, which reads only the middle
    2/3 of the sensor: the arm left the frame when it rose (2026-11-12)."""
    w, h = (int(v) for v in args.cam_size.lower().split("x"))
    user = args.cam_user or args.user
    if args.cam_index.isdigit():
        pick = f"IDX={int(args.cam_index)}"
    else:  # the HQ camera's index, from the camera list; else camera 0
        pick = ("IDX=$(rpicam-hello --list-cameras 2>/dev/null | awk '/imx477/ {print $1; exit}'); "
                "IDX=${IDX:-0}")
    mode = "" if args.cam_mode == "auto" else args.cam_mode
    if mode == "full":
        mode = ""
        try:
            out = subprocess.run(ssh(args.cam_host, user, args.ssh_opt,
                                     f"{pick}; echo IDX=$IDX; rpicam-hello --list-cameras 2>&1"),
                                 capture_output=True, text=True, timeout=30).stdout
            idx = re.search(r"^IDX=(\d+)", out, re.M)
            found = idx and full_view_mode(out, int(idx.group(1)))
        except (OSError, subprocess.SubprocessError):
            found = None
        if found:
            mode, mw, mh = found
            h = round(w * mh / mw / 2) * 2  # the mode's own aspect ratio: nothing cropped
            print(f"camera: sensor mode {mode} (the whole sensor), video {w}x{h}", flush=True)
        else:
            print("camera: couldn't find a whole-sensor mode, so rpicam picks (it may crop)",
                  flush=True)
    remote = (f"{pick}; exec rpicam-vid -t 0 -n --camera $IDX --codec mjpeg --width {w} "
              f"--height {h} " + (f"--mode {mode} " if mode else "")
              + f"--framerate {args.cam_fps:g} -q {int(args.cam_quality)} --flush -o -")
    return ssh(args.cam_host, user, args.ssh_opt, remote)


def split_jpegs(buf, stop):
    """Each complete JPEG in buf[:stop], oldest first."""
    out, i = [], 0
    while True:
        s = buf.find(b"\xff\xd8", i, stop)
        e = buf.find(b"\xff\xd9", s, stop) if s >= 0 else -1
        if e < 0:
            return out
        out.append(bytes(buf[s:e + 2]))
        i = e + 2


class Camera:
    """The newest frame from a video source, read and decoded on its own thread, so the control
    loop never waits for video. Frames that arrive while one is being decoded are skipped, not
    queued: what is shown is always as fresh as the link allows. A Recorder (--record) gets
    every frame, the skipped ones too."""

    def __init__(self, cmd=None, url=None, rec=None):
        self.lock = threading.Lock()
        self.frame = self.t_frame = self.err = self.proc = None
        self.n, self.stderr, self.rec = 0, [], rec
        self.decode_s = collections.deque(maxlen=2000)
        self.gap_s = collections.deque(maxlen=2000)
        if cmd:
            self.proc = subprocess.Popen(cmd, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE,
                                         stderr=subprocess.PIPE, bufsize=0)
            threading.Thread(target=self._mjpeg, args=(self.proc.stdout,), daemon=True).start()
            threading.Thread(target=self._errs, daemon=True).start()
        else:
            threading.Thread(target=self._capture, args=(url,), daemon=True).start()

    def _put(self, img, t_decode):
        now = time.monotonic()
        with self.lock:
            if self.t_frame is not None:
                self.gap_s.append(now - self.t_frame)
            self.frame, self.t_frame = img, now
            self.n += 1
            self.decode_s.append(t_decode)

    def _mjpeg(self, stream):
        import cv2
        import numpy as np

        buf = bytearray()
        while True:
            chunk = stream.read(1 << 16)
            if not chunk:
                break
            buf += chunk
            end = buf.rfind(b"\xff\xd9")  # the newest complete JPEG ends here
            if end < 0:
                if len(buf) > 1 << 23:
                    del buf[:]
                continue
            if self.rec:  # every complete frame, as the Pi encoded it
                for jpg in split_jpegs(buf, end + 2):
                    self.rec.frame(jpg)
            start = buf.rfind(b"\xff\xd8", 0, end)
            jpg = bytes(buf[start:end + 2]) if start >= 0 else None
            del buf[:end + 2]
            if jpg:
                t0 = time.perf_counter()
                img = cv2.imdecode(np.frombuffer(jpg, np.uint8), cv2.IMREAD_COLOR)
                if img is not None:
                    self._put(img, time.perf_counter() - t0)
        self.err = "camera stream ended" + (f": {' | '.join(self.stderr[-3:])}"
                                            if self.stderr else "")

    def _errs(self):
        for raw in self.proc.stderr:
            line = raw.decode("utf-8", "replace").strip()
            if line:
                self.stderr = (self.stderr + [line])[-20:]

    def _capture(self, url):
        import cv2

        cap = cv2.VideoCapture(url)
        cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
        while True:
            t0 = time.perf_counter()
            ok, img = cap.read()
            if not ok:
                self.err = f"video source {url} stopped"
                return
            self._put(img, time.perf_counter() - t0)
            if self.rec:
                self.rec.frame(img)  # decoded already, so the recorder's thread encodes it

    def latest(self):
        with self.lock:
            age = None if self.t_frame is None else time.monotonic() - self.t_frame
            return self.frame, age, self.n

    def close(self):
        if self.proc and self.proc.poll() is None:
            self.proc.terminate()


class Recorder:
    """--record: every camera frame as it arrived, and the window's text, saved for videos made
    once the session is over (render). The camera thread and the window only add to a queue;
    a thread of its own writes it out, and a full queue (a stalled disk) drops rather than
    waits, so recording can't hold up the window, the video or the commands."""

    def __init__(self, path, fps=None):
        os.makedirs(path, exist_ok=True)
        self.path, self.t0 = path, time.perf_counter()
        self.q = queue.Queue(maxsize=800)  # about 10 s of frames and window text
        self.n = self.bytes = self.dropped = 0
        self.write_s = collections.deque(maxlen=50000)
        self.done = threading.Event()
        threading.Thread(target=self._write, args=(fps,), daemon=True).start()

    def _add(self, item):
        try:
            self.q.put_nowait(item)
        except queue.Full:
            self.dropped += 1

    def frame(self, jpg):
        """JPEG bytes, or a decoded image (--video) for this thread to encode."""
        self._add(("f", time.perf_counter() - self.t0, jpg))

    def status(self, lines):
        self._add(("s", time.perf_counter() - self.t0, lines))

    def _write(self, fps):
        with open(os.path.join(self.path, "camera.mjpeg"), "wb") as video, \
                open(os.path.join(self.path, "index.jsonl"), "w") as index:
            index.write(json.dumps({"fps": fps, "started": time.strftime("%Y-%m-%d %H:%M:%S")})
                        + "\n")
            while True:
                item = self.q.get()
                if item is None:
                    break
                kind, t, data = item
                t0 = time.perf_counter()
                if kind == "s":
                    index.write(json.dumps({"t": round(t, 4), "status": data}) + "\n")
                else:
                    if not isinstance(data, bytes):
                        import cv2

                        data = cv2.imencode(".jpg", data, [cv2.IMWRITE_JPEG_QUALITY, 90])[1]
                        data = data.tobytes()
                    video.write(data)
                    index.write(json.dumps({"t": round(t, 4), "n": len(data)}) + "\n")
                    self.n, self.bytes = self.n + 1, self.bytes + len(data)
                if self.q.empty():  # caught up: onto the disk, in case the session crashes
                    video.flush()
                    index.flush()
                self.write_s.append(time.perf_counter() - t0)
        self.done.set()

    def close(self):
        self.q.put(None)
        self.done.wait(30)


# ------------------------------------------------------------------ the control loop

def space_down():
    if WINDOWS:
        import ctypes

        return bool(ctypes.windll.user32.GetAsyncKeyState(0x20) & 0x8000)
    return None  # elsewhere: SPACE toggles in the window


def ctrl_down():
    return key_down(0x11)


def key_down(vk):
    """Whether a key (a Windows virtual-key code) is held, whichever window has focus."""
    if WINDOWS:
        import ctypes

        return bool(ctypes.windll.user32.GetAsyncKeyState(vk) & 0x8000)
    return False


def j4_jog():
    """+1 while 1 is held, -1 while 2 is (top row or keypad), else 0."""
    return int(key_down(0x31) or key_down(0x61)) - int(key_down(0x32) or key_down(0x62))


class Control(threading.Thread):
    """Leader -> commands at --hz on its own thread, so the window and the video can't delay
    a command. The window reads what it shows from here."""

    def __init__(self, args, leader, mapping, sess):
        super().__init__(daemon=True)
        self.a, self.leader, self.mapping, self.sess = args, leader, mapping, sess
        self.lock = threading.Lock()
        self.q5 = self.grip = self.raw = None
        self.dm, self.toggled, self.msg = False, False, ""
        self.latched = self.space_was = self.blocked = False  # Ctrl+SPACE, on Windows
        self.read_s = collections.deque(maxlen=50000)
        self.ticks = self.late = 0
        self.auto_t0, self.t_quit = None, 0.0
        self.stop = threading.Event()

    def run(self):
        if WINDOWS:  # ahead of the window and video threads for the CPU
            import ctypes

            ctypes.windll.kernel32.SetThreadPriority(ctypes.windll.kernel32.GetCurrentThread(), 2)
        a, sess = self.a, self.sess
        period = 1.0 / a.hz
        seq, t_ping = 0, 0.0
        t_next = time.perf_counter()
        while not self.stop.is_set():
            now = time.monotonic()
            ready5, raw = None, None
            if sess.hello:
                r = sess.ready or sess.hello["ready"]
                ready5 = [r[0], r[1], r[2], r[4], r[5]]
            if a.fake_leader:
                if sess.ready and self.leader.t0 is None:
                    self.leader.t0 = now
                q5, grip = self.leader.piper(ready5) if ready5 else (None, None)
            else:
                t0 = time.perf_counter()
                try:
                    raw = self.leader.read()
                except IOError as e:
                    self.msg = str(e)
                self.read_s.append(time.perf_counter() - t0)
                q5, grip = self.mapping.piper(raw) if raw else (None, None)
            if a.auto is not None:
                if sess.ready and self.auto_t0 is None:
                    self.auto_t0 = now
                dm = self.auto_t0 is not None and now - self.auto_t0 < a.auto
                if (self.auto_t0 is not None and now - self.auto_t0 >= a.auto + 1.0
                        and now - self.t_quit > 2):
                    self.t_quit = now
                    sess.send("Q")
                    sess.log.put("auto: Q")
            else:
                sd = space_down()
                if sd is None:
                    dm = self.toggled
                else:
                    if sd and not self.space_was:  # a press
                        if self.latched:  # SPACE again: stop, until it is let go
                            self.latched, self.blocked = False, True
                        elif ctrl_down():
                            self.latched = True
                    if not sd:
                        self.blocked = False
                    self.space_was = sd
                    dm = self.latched or (sd and not self.blocked)
            if q5 is not None:
                seq += 1
                g = "nan" if grip is None else f"{grip:.1f}"
                jog = j4_jog() if a.auto is None and dm else 0
                if not sess.send(f"T {seq} {time.time():.4f} {int(bool(dm))} "
                                 + " ".join(f"{v:.2f}" for v in q5) + f" {g} {jog}"):
                    self.msg = "can't write to the Pi"
            if now - t_ping >= 1.0:
                t_ping = now
                sess.send(f"P {time.time():.4f}")
            with self.lock:
                self.q5, self.grip, self.dm = q5, grip, bool(dm)
                if raw:
                    self.raw = raw
            self.ticks += 1
            t_next += period
            pause = t_next - time.perf_counter()
            if pause > 0:
                time.sleep(pause)
            else:
                self.late += 1
                t_next = time.perf_counter()

    def snapshot(self):
        with self.lock:
            return self.q5, self.grip, self.raw, self.dm


# ------------------------------------------------------------------ setup and preflight

def load_local():
    try:
        with open(LOCAL) as f:
            return json.load(f)
    except (OSError, ValueError):
        return {}


def first_run(args):
    """Ask for the Pis once and save the answers to teleop.local.json (git ignores it)."""
    print("Where is the arm? Saved to teleop.local.json beside this script (git ignores it); "
          "edit or delete that file to change it.")
    cfg = load_local()
    args.host = cfg["host"] = input("  arm Pi address (tailnet name or LAN IP): ").strip()
    args.user = cfg["user"] = input("  login on it (blank: your login here): ").strip() or None
    cam = input("  camera Pi with the HQ camera (blank: no video): ").strip()
    if cam:
        args.cam_host = cfg["cam_host"] = cam
        args.cam_user = cfg["cam_user"] = (input("  login on the camera Pi (blank: same as the "
                                                 "arm Pi): ").strip() or None)
    if args.port and not cfg.get("port"):
        cfg["port"] = args.port
    with open(LOCAL, "w") as f:
        json.dump({k: v for k, v in cfg.items() if v}, f, indent=2)
    print(f"saved {LOCAL}")


def preflight(args):
    """Check everything a session needs without moving or powering anything."""
    ok = True

    def line(good, text):
        nonlocal ok
        ok = ok and good is not False
        print(f"  {'ok  ' if good else ('--  ' if good is None else 'FAIL')}  {text}", flush=True)

    print(f"python {sys.version.split()[0]} on {sys.platform}")
    for mod, pkg, need in (("serial", "pyserial", True), ("numpy", "numpy", True),
                           ("cv2", "opencv-python", True)):
        try:
            __import__(mod)
            line(True, pkg)
        except ImportError:
            line(False if need else None, f"{pkg} missing: pip install -r requirements.txt")
    if args.fake_leader:
        line(None, "leader: --fake-leader")
    else:
        try:
            leader = Leader(args.port)
            times = []
            for _ in range(200):
                t0 = time.perf_counter()
                raw = leader.read()
                times.append(time.perf_counter() - t0)
            q, g = Mapping(args).piper(raw)
            line(True, f"leader on {args.port}: read {stats_ms(times)}; SYNC READ "
                       f"{'on' if leader.use_sync else 'OFF'}")
            print("        maps to " + ", ".join(f"{j} {v:.1f}" for j, v in zip(PIPER, q))
                  + f", gripper {'--' if g is None else f'{g:.0f} mm'}")
            if sorted(times)[len(times) // 2] > 0.005:
                print("        slow: an FTDI adapter's USB latency timer (16 ms by default) is "
                      "the usual cause; set it to 1 ms (README, Latency)")
        except Exception as e:  # noqa: BLE001
            line(False, f"leader on {args.port}: {e}")
    if args.local or not args.host:
        line(None, "arm Pi: not checked (--local, or no --host)")
    else:
        remote = ("PY=" + args.pi_python + "; "
                  "$PY -c 'import piper_sdk' 2>/dev/null && echo 'ok piper_sdk in '$PY "
                  "|| echo 'FAIL piper_sdk not importable with '$PY; "
                  "if [ -e /sys/class/net/can0 ]; then echo \"ok can0 $(cat "
                  "/sys/class/net/can0/operstate)\"; else echo 'FAIL can0 missing: is the "
                  "USB-CAN adapter on this Pi?'; fi; "
                  "if [ -f ~/arm_power.py ]; then echo 'ok ~/arm_power.py'; else echo "
                  "'-- no ~/arm_power.py: the repo copy will be used'; fi; "
                  "P=$(pinctrl get 17 2>/dev/null | head -1); case \"$P\" in *' op '*'| hi'*) "
                  "echo '-- relay ON (GPIO17 high): the arm has power';; *) echo \"-- relay "
                  "off ($P)\";; esac; "
                  "B=$(pgrep -fa '[f]ollower\\.py|[U]p_and_Down\\.py|[a]rm_power\\.py run' "
                  "| head -3); if [ -n \"$B\" ]; then echo \"FAIL busy: $B\"; else "
                  "echo 'ok nothing else is driving the arm'; fi")
        try:
            p = subprocess.run(ssh(args.host, args.user, args.ssh_opt, remote),
                               stdin=subprocess.DEVNULL, capture_output=True, text=True,
                               timeout=60)
            outs = [ln for ln in p.stdout.splitlines() if ln.strip()]
            line(p.returncode == 0 and bool(outs),
                 f"ssh to the arm Pi (exit {p.returncode})"
                 + ("" if outs else f": {p.stderr.strip()[-300:]}"))
            for ln in outs:
                tag, _, text = ln.partition(" ")
                line({"ok": True, "FAIL": False}.get(tag), "arm Pi: " + text)
            if outs:
                line(True, "SSH round trip to the arm Pi: " + ssh_rtt(args))
        except FileNotFoundError:
            line(False, "no ssh command: install the OpenSSH client (Windows: Settings > "
                        "System > Optional features > OpenSSH Client)")
        except subprocess.TimeoutExpired:
            line(False, "ssh to the arm Pi timed out")
    if args.cam_host and not args.no_cam:
        try:
            p = subprocess.run(ssh(args.cam_host, args.cam_user or args.user, args.ssh_opt,
                                   "rpicam-hello --list-cameras 2>&1 | grep -E '^ *[0-9]+ :'"),
                               stdin=subprocess.DEVNULL, capture_output=True, text=True,
                               timeout=60)
            cams = p.stdout.strip().splitlines()
            line(bool(cams), "camera Pi: " + ("; ".join(c.strip()[:60] for c in cams)
                                              if cams else "no cameras listed "
                                              f"{p.stderr.strip()[-200:]}"))
            if cams and not any("imx477" in c for c in cams):
                print("        no HQ camera (imx477) listed; --cam-index picks another")
        except (FileNotFoundError, subprocess.TimeoutExpired) as e:
            line(False, f"camera Pi: {e}")
    else:
        line(None, "camera Pi: none set (--cam-host), so no video")
    print("preflight: " + ("all good" if ok else "fix the FAIL lines above"))
    return ok


def ssh_rtt(args, n=40):
    """Round trip of a line through the same kind of SSH channel the session uses."""
    p = subprocess.Popen(ssh(args.host, args.user, args.ssh_opt, "cat"), stdin=subprocess.PIPE,
                         stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, bufsize=0)
    rtts = []
    try:
        for i in range(n):
            t0 = time.perf_counter()
            p.stdin.write(f"{i}\n".encode())
            p.stdin.flush()
            if not p.stdout.readline():
                break
            rtts.append(time.perf_counter() - t0)
            time.sleep(0.02)
    finally:
        p.stdin.close()
        p.wait(timeout=10)
    return stats_ms(rtts[1:])  # the first one includes waking the link


def fmt_row(label, vals):
    return f"{label:8s}" + "".join(f"{'--' if v is None else f'{v:7.1f}':>8s}" for v in vals)


KEYS = [f"SPACE {'hold' if WINDOWS else 'toggle'}: move"
        + ("   Ctrl+SPACE: move until SPACE is pressed again" if WINDOWS else ""),
        ("1/2 hold (while moving): turn J4   " if WINDOWS else "")
        + "Q/Esc: back to READY, park, quit"]
RULE = "-" * 80


def screen_height():
    """Usable screen height in pixels (Windows), or None."""
    if WINDOWS:
        import ctypes

        with contextlib.suppress(Exception):
            return ctypes.windll.user32.GetSystemMetrics(17)  # SM_CYFULLSCREEN: minus taskbar
    return None


def compose(cv2, frame, status, width=960, room=None):
    """The window's picture: the video, then the text under it. The video fills the width, or
    shrinks (keeping its aspect ratio) to `room` pixels high if that is less. At any other
    width than the window's 960 (render), the text is drawn as in the window, then scaled."""
    import numpy as np

    panel = np.zeros((20 * len(status) + 10, 960, 3), np.uint8)
    for i, text in enumerate(status):
        cv2.putText(panel, str(text)[:120], (8, 20 * (i + 1)), cv2.FONT_HERSHEY_SIMPLEX, 0.45,
                    (255, 255, 255), 1, cv2.LINE_AA)
    if width != 960:  # drawing it at 1920 took 45 ms a frame at stroke 2, and was faint at 1
        panel = cv2.resize(panel, (width, round(panel.shape[0] * width / 960)),
                           interpolation=cv2.INTER_LINEAR if width > 960 else cv2.INTER_AREA)
    if frame is None:
        return panel
    h, w = frame.shape[:2]
    scale = width / w if room is None else min(width / w, max(room, 120) / h)
    fw, fh = int(w * scale), int(h * scale)
    top = np.zeros((fh, width, 3), np.uint8)
    x = (width - fw) // 2
    top[:, x:x + fw] = cv2.resize(frame, (fw, fh), interpolation=cv2.INTER_AREA)
    return np.vstack([top, panel])


def show(cv2, frame, status):
    """A fixed-size window: the text stays its size, and the video shrinks, keeping its aspect
    ratio, until the whole window fits on the screen."""
    room = (screen_height() or 1000) - 40 - (20 * len(status) + 10)  # 40: the title bar
    cv2.imshow("SO-101 -> PiPER (hold SPACE to move, Q to park and quit)",
               compose(cv2, frame, status, room=room))


# ------------------------------------------------------------------ videos from a recording

def ffmpeg_exe():
    """ffmpeg on PATH, else imageio-ffmpeg's (pip install imageio-ffmpeg), else None."""
    exe = shutil.which("ffmpeg")
    if not exe:
        with contextlib.suppress(Exception):
            import imageio_ffmpeg

            exe = imageio_ffmpeg.get_ffmpeg_exe()
    return exe


class VideoOut:
    """An MP4 written a frame at a time: H.264 through ffmpeg when there is one, else OpenCV's
    MPEG-4 Part 2. YouTube takes either."""

    def __init__(self, cv2, path, shape, fps, exe):
        self.cv2, (self.h, self.w) = cv2, shape[:2]
        self.p = self.v = None
        if exe:
            self.p = subprocess.Popen(
                [exe, "-hide_banner", "-loglevel", "error", "-y", "-f", "rawvideo",
                 "-pix_fmt", "bgr24", "-s", f"{self.w}x{self.h}", "-framerate", f"{fps:.3f}",
                 "-i", "-", "-c:v", "libx264", "-preset", "veryfast", "-crf", "18",
                 "-pix_fmt", "yuv420p", "-movflags", "+faststart", path], stdin=subprocess.PIPE)
        else:
            self.v = cv2.VideoWriter(path, cv2.VideoWriter_fourcc(*"mp4v"), fps, (self.w, self.h))
            if not self.v.isOpened():
                raise RuntimeError(f"OpenCV can't write {path}")

    def write(self, img):
        if img.shape[:2] != (self.h, self.w):
            img = self.cv2.resize(img, (self.w, self.h))
        if self.p:
            self.p.stdin.write(img.data if img.flags.c_contiguous else img.tobytes())
        else:
            self.v.write(img)

    def close(self):
        if self.p:
            self.p.stdin.close()
            return self.p.wait() == 0
        self.v.release()
        return True


def render(path, width=1920):
    """camera.mp4 (the camera alone) and window.mp4 (the video above the window's text) from a
    --record folder, `width` wide: YouTube streams a video wider than 960 at a higher bitrate.
    Each recorded frame becomes one video frame, at the camera's frame rate, with the text the
    window showed when that frame arrived."""
    import cv2
    import numpy as np

    index = os.path.join(path, "index.jsonl")
    if not os.path.exists(index):
        print(f"render: no recording in {path}")
        return False
    meta, frames, statuses = {}, [], []
    with open(index) as f:
        for line in f:
            try:
                d = json.loads(line)
            except ValueError:
                continue  # cut short when the session ended
            if "n" in d:
                frames.append((d["t"], d["n"]))
            elif "status" in d:
                statuses.append((d["t"], d["status"]))
            else:
                meta = d
    if not frames:
        print(f"render: no video frames in {path}")
        return False
    span = frames[-1][0] - frames[0][0]
    fps = meta.get("fps") or (min(max((len(frames) - 1) / span, 1.0), 120.0) if span > 0
                              else 30.0)
    rows = max((len(s) for _, s in statuses), default=0)
    exe = ffmpeg_exe()
    how = "H.264 by ffmpeg" if exe else "MPEG-4 by OpenCV (pip install imageio-ffmpeg for H.264)"
    print(f"making camera.mp4 and window.mp4: {len(frames)} frames at {fps:.3g} fps "
          f"({len(frames) / fps:.0f} s), {how}", flush=True)
    outs, img, k, t0 = {}, None, 0, time.perf_counter()
    with open(os.path.join(path, "camera.mjpeg"), "rb") as video:
        for i, (t, n) in enumerate(frames):
            new = cv2.imdecode(np.frombuffer(video.read(n), np.uint8), cv2.IMREAD_COLOR)
            if new is not None:  # else the last good frame again, to keep the timing
                h, w = new.shape[:2]
                img = cv2.resize(new, (width, round(h * width / w / 2) * 2),
                                 interpolation=cv2.INTER_CUBIC if width > w else cv2.INTER_AREA)
            if img is None:
                continue
            while k < len(statuses) and statuses[k][0] <= t:
                k += 1
            text = statuses[k - 1][1] if k else []
            win = compose(cv2, img, text + [""] * (rows - len(text)), width)
            for name, pic in (("camera", img), ("window", win[:win.shape[0] // 2 * 2])):
                if name not in outs:
                    outs[name] = VideoOut(cv2, os.path.join(path, f"{name}.mp4"), pic.shape,
                                          fps, exe)
                outs[name].write(pic)
            if (i + 1) % max(1, len(frames) // 10) == 0:
                print(f"  {round(100 * (i + 1) / len(frames))}%", end="", flush=True)
    ok = [out.close() for out in outs.values()]
    print(f"\nmade in {time.perf_counter() - t0:.0f} s: "
          + ", ".join(os.path.join(path, f"{name}.mp4") for name in outs))
    return all(ok)


def main():
    cfg = load_local()
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0],
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--port", default=cfg.get("port", "COM10"), help="the leader's serial port")
    ap.add_argument("--host", default=cfg.get("host"),
                    help="the arm Pi (tailnet name or LAN address)")
    ap.add_argument("--user", default=cfg.get("user"), help="login on the arm Pi")
    ap.add_argument("--ssh-opt", action="append", default=[], help="extra ssh option, repeatable")
    ap.add_argument("--pi-python", default="~/piper-venv/bin/python")
    ap.add_argument("--calib", help="LeRobot so101_leader/so_leader calibration JSON (default: newest in "
                                    "~/.cache/huggingface/lerobot/calibration/...)")
    ap.add_argument("--gripper-range", type=lambda s: [float(v) for v in s.split(",")],
                    help="leader gripper counts CLOSED,OPEN (default: from the calibration)")
    ap.add_argument("--gripper-invert", action="store_true")
    ap.add_argument("--gripper", action=argparse.BooleanOptionalAction, default=True,
                    help="the PiPER's gripper follows the leader's (--no-gripper: never moved)")
    # The lab PiPER's gripper reads 45.6 mm with its finger sleeves touching and 108.6 mm
    # fully open (moved by hand, 2026-11-12), not the stock 0-70 mm.
    ap.add_argument("--grip-min-mm", type=float, default=46.0,
                    help="PiPER gripper reading for the leader closed (sleeves touching: 45.6)")
    ap.add_argument("--grip-max-mm", type=float, default=108.0,
                    help="PiPER gripper reading for the leader open, and on Q (fully open: 108.6)")
    ap.add_argument("--hz", type=float, default=200.0,
                    help="leader reads and commands per second (the follower runs at 200 too)")
    ap.add_argument("--cam-host", default=cfg.get("cam_host"),
                    help="camera Pi to stream into the window (the gripper Pi, with the HQ camera)")
    ap.add_argument("--cam-user", default=cfg.get("cam_user"),
                    help="login on the camera Pi (default: --user)")
    ap.add_argument("--cam-index", default=str(cfg.get("cam_index", "hq")),
                    help="rpicam camera number, or 'hq' for the HQ camera (imx477), else 0")
    ap.add_argument("--cam-size", default=cfg.get("cam_size", "960x540"),
                    help="video width x height; the height follows the sensor mode's shape")
    ap.add_argument("--cam-mode", default=cfg.get("cam_mode", "full"),
                    help='sensor mode: "full" (smallest that sees the whole sensor), "auto" '
                         '(rpicam picks; it may crop) or an rpicam mode, W:H:BITS:P')
    ap.add_argument("--cam-fps", type=float, default=cfg.get("cam_fps", 30.0))
    ap.add_argument("--cam-quality", type=int, default=cfg.get("cam_quality", 60),
                    help="MJPEG quality 1-100: lower is less data on a slow link")
    ap.add_argument("--no-cam", action="store_true", help="no video this time")
    ap.add_argument("--video", help="any other video source cv2.VideoCapture opens, instead")
    ap.add_argument("--record", nargs="?", const="", metavar="DIR",
                    help="keep the video: save it as it arrives, with the window's text, to a "
                         "new folder in DIR (default: recordings/ here), and make camera.mp4 and "
                         "window.mp4 from it once the arm has parked")
    ap.add_argument("--render", metavar="DIR",
                    help="make camera.mp4 and window.mp4 from a --record folder, then exit")
    ap.add_argument("--check", action="store_true",
                    help="preflight: leader, packages, SSH, the arm Pi and the camera Pi, then "
                         "exit. Moves and powers nothing")
    ap.add_argument("--dry-run", action="store_true",
                    help="the Pi drives a simulated arm: no relay, no CAN frames")
    ap.add_argument("--local", action="store_true",
                    help="run the follower on this machine (only with --dry-run)")
    ap.add_argument("--fake-leader", action="store_true", help="no leader: a synthetic sweep")
    ap.add_argument("--auto", type=float, metavar="S",
                    help="no window or keyboard: hold the deadman for S seconds after READY, "
                         "then Q (only with --dry-run)")
    ap.add_argument("follower_args", nargs="*", help="after --: options for follower.py")
    args = ap.parse_args()
    if args.render:
        sys.exit(0 if render(args.render) else 1)
    if args.local and not args.dry_run:
        ap.error("--local runs the follower here, so it needs --dry-run")
    if args.auto is not None and not args.dry_run:
        ap.error("--auto holds the deadman by itself, so it is only allowed with --dry-run")
    if args.record is not None and args.auto is not None:
        ap.error("--record keeps what the window shows, and --auto has no window")
    if not args.local and not args.host:
        if not sys.stdin.isatty() or args.auto is not None:
            ap.error("--host is required (or --local --dry-run)")
        first_run(args)
    if args.check:
        sys.exit(0 if preflight(args) else 1)
    if not 20 <= args.hz <= 500:
        ap.error("--hz must be 20-500")

    sys.setswitchinterval(0.0005)  # the control thread gets the interpreter back within 0.5 ms
    if WINDOWS:
        import ctypes

        ctypes.windll.winmm.timeBeginPeriod(1)  # 1 ms sleeps and key polls, not 15.6 ms

    back_at = None if args.auto is None else max(0.0, args.auto - 3.0)
    try:
        leader = FakeLeader(back_at) if args.fake_leader else Leader(args.port)
        mapping = None if args.fake_leader else Mapping(args)
        if not args.fake_leader:
            q, g = mapping.piper(leader.read())
            print("leader now ->", dict(zip(PIPER, [round(v, 1) for v in q])),
                  "gripper", "--" if g is None else f"{g:.0f} mm")
    except Exception as e:  # noqa: BLE001  e.g. no such port, or the leader unpowered
        sys.exit(f"leader on {args.port}: {e}\nIs it plugged in and powered, and is that its "
                 "port (--port)? Nothing was started on the Pi. --check tests the leader alone.")

    cv2 = None
    if args.auto is None:
        try:
            import cv2  # noqa: F811
        except ImportError:
            print("opencv-python isn't installed: no window or video. Q/A from this console")
    if args.auto is None and space_down() is None and cv2 is None:
        sys.exit("need either Windows (hold SPACE) or opencv-python (SPACE toggles)")
    if args.record is not None and (cv2 is None or args.no_cam
                                    or not (args.video or args.cam_host)):
        sys.exit("--record needs the video: opencv-python and a camera (--cam-host or --video). "
                 "Nothing was started on the Pi.")

    print("starting the follower" + (" (DRY RUN)" if args.dry_run else
                                     ": the arm powers on through the relay"))
    try:
        sess = Session(start_follower(args))
    except FileNotFoundError:
        sys.exit("no ssh command: install the OpenSSH client (Windows: Settings > System > "
                 "Optional features > OpenSSH Client)")
    ctl = Control(args, leader, mapping, sess)
    ctl.start()
    want_cam = cv2 is not None and not args.no_cam and (args.video or args.cam_host)
    cam, rec, lines, msg = None, None, [], ""
    while True:
        while not sess.log.empty():
            m = sess.log.get()
            print(m, flush=True)
            lines = (lines + [m])[-6:]
        if sess.bye is not None or sess.proc.poll() is not None:
            break
        if want_cam and cam is None and sess.hello:  # after the arm's SSH login, not during it
            if args.record is not None:
                rec = Recorder(os.path.join(args.record or os.path.join(HERE, "recordings"),
                                            time.strftime("%Y-%m-%d_%H-%M-%S")),
                               None if args.video else args.cam_fps)
                print(f"recording to {rec.path}", flush=True)
            cam = (Camera(url=args.video, rec=rec) if args.video
                   else Camera(cmd=camera_cmd(args), rec=rec))
        if args.auto is not None:
            time.sleep(0.05)
            continue
        q5, grip, raw, dm = ctl.snapshot()
        st = sess.state or {}
        arm = st.get("q")
        arm5 = [arm[i] for i in (0, 1, 2, 4, 5)] if arm else [None] * 5
        diff = [None if a is None or b is None else b - a for a, b in zip(arm5, q5 or [None] * 5)]
        rtt = sorted(sess.rtt)[len(sess.rtt) // 2] * 1000 if sess.rtt else None
        frame, age, nf = cam.latest() if cam else (None, None, 0)
        status = [f"phase {st.get('ph', 'starting')}   deadman {'LATCHED' if ctl.latched else 'HELD' if dm else 'off'}"
                  + (f"   RTT {rtt:.0f} ms (median)" if rtt else "")
                  + (f"   Pi loop late {st['late']}" if st.get("late") else "")
                  + (f"   video {'--' if age is None else f'{age * 1000:.0f} ms old'}"
                     if cam else ""),
                  f"{st.get('why') or ''}",
                  *KEYS,
                  fmt_row("joint", []) + "".join(f"{j:>8s}" for j in PIPER),
                  fmt_row("leader", q5 or [None] * 5),
                  fmt_row("arm", arm5),
                  fmt_row("off by", diff),
                  f"gripper leader {'--' if grip is None else f'{grip:.0f}'} mm, "
                  f"arm {st.get('grip', '--')} mm   lowest point {st.get('z', '--')} mm   "
                  f"J4 {'--' if not arm else f'{arm[3]:.1f}'}",
                  (cam.err if cam and cam.err else "") or msg or ctl.msg, RULE, *lines]
        if rec:
            rec.status(status)
        key = -1
        if cv2 is not None:
            show(cv2, frame, status)
            key = cv2.waitKey(15) & 0xFF  # paces the window at about 50 Hz
        else:
            sys.stdout.write("\r" + status[0] + "  " + status[1][:60] + " " * 10)
            sys.stdout.flush()
            time.sleep(0.03)
            if WINDOWS:
                import msvcrt

                if msvcrt.kbhit():
                    key = ord(msvcrt.getwch().lower()[:1] or " ")
        if key == ord(" ") and space_down() is None:
            ctl.toggled = not ctl.toggled
        if key in (ord("q"), 27):
            sess.send("Q")
            msg = "Q sent: the arm goes back to READY by itself, then parks"
    ctl.stop.set()
    if cam:
        cam.close()
    if rec:
        rec.close()
    while not sess.log.empty():
        print(sess.log.get(), flush=True)
    try:
        sess.proc.wait(timeout=30)
    except subprocess.TimeoutExpired:
        sess.proc.kill()
    rc = sess.proc.returncode
    bye = sess.bye or {}
    print("\nlatency:")
    print(f"  ping round trip to the Pi: {stats_ms(sess.rtt_all)}")
    print(f"  newest command's age at the Pi's state report (one way plus up to one report "
          f"interval): {stats_ms(sess.age_all)}")
    if not args.fake_leader:
        print(f"  leader read: {stats_ms(list(ctl.read_s))}"
              + ("" if leader.use_sync else " (SYNC READ off)"))
    print(f"  control loop: {ctl.ticks} ticks at {args.hz:g} Hz, {ctl.late} late")
    if cam:
        print(f"  video: {cam.n} frames, between frames {stats_ms(list(cam.gap_s))}; "
              f"decode {stats_ms(list(cam.decode_s))}")
    if rec:
        print(f"  recording: {rec.n} frames, {rec.bytes / 1e6:.0f} MB, {rec.dropped} dropped; "
              f"disk writes {stats_ms(list(rec.write_s))}")
    print(f"\nsession over: follower {bye.get('why', '?')}; exit {rc}")
    if rc != 0 and not args.dry_run:
        print("The relay stays on unless the arm was parked (arm_power.py says why above). "
              "If the arm is parked: ssh to the Pi and run "
              "~/piper-venv/bin/python ~/arm_power.py off")
    if cv2 is not None:
        cv2.destroyAllWindows()
    if WINDOWS:
        import ctypes

        ctypes.windll.winmm.timeEndPeriod(1)
    if rec:  # the follower has exited: nothing here is driving the arm any more
        print(f"\nrecorded to {rec.path}. Ctrl-C skips the videos; --render makes them later")
        try:
            render(rec.path)
        except KeyboardInterrupt:
            print(f"\nstopped. To make the videos later: --render \"{rec.path}\"")
        except Exception as e:  # noqa: BLE001
            print(f"\ncouldn't make the videos ({e}). The recording is in {rec.path}, and "
                  "--render tries again")
    sys.exit(0 if rc == 0 else 1)


if __name__ == "__main__":
    main()
