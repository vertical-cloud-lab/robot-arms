#!/usr/bin/env python3
"""Teleoperate the lab's AgileX PiPER from an SO-101 leader arm (#46, PR #47). Run it on the PC
the leader is plugged into:

    pip install -r "SO-101 leader/requirements.txt"
    python "SO-101 leader/teleop.py" --port COM10 --host <the arm Pi> --user <its login>

The arm Pi is the one with the USB-CAN adapter and the relay: rpi-5-mpzy since 2026-10-30. Use
its tailnet name if your PC is on the lab tailnet with SSH to it, or its LAN address from the
lab network.

1. Reads the leader's six Feetech STS3215 servos (IDs 1-6, 1 Mbit/s) on --port, ~100 times a
   second, and maps them to PiPER joints: J1 = -pan, J2 = lift + 96.2, J3 = elbow - 88.4,
   J5 = wrist_flex - 2.8, J6 = -roll (analysis/joint_map.json), plus your alignment (A key).
   J4 has no SO-101 joint; the Pi holds it where it starts.
2. Over ONE SSH connection: copies pi/follower.py, pi/Up_and_Down.py and pi/fake_piper.py to
   ~/so101/ on the Pi and runs the follower through PR #60's power protocol (arm_power.py run),
   so the relay switches the arm on now and off only once the follower has parked it.
3. The follower raises the arm off its rest to READY. Line the leader up with it (the window
   shows each joint's difference), then HOLD SPACE to move; let go to stop. Q near READY parks
   the arm, powers it off and ends the session. If this script dies or the connection drops,
   the follower holds, then parks on its own after its --lost-s (10 s).

Keys, in the teleop window: hold SPACE = move (Windows reads the key directly, so it works
whichever window has focus); Q = park and quit; A = align: while holding at READY with the
leader in the same pose as the arm, take the difference as the leader's offsets (saved to
align.json beside this file, which git ignores).

Test without the arm or the leader:  --fake-leader --local --dry-run --auto 10
"""
import argparse
import base64
import io
import json
import math
import os
import queue
import shlex
import subprocess
import sys
import tarfile
import threading
import time

HERE = os.path.dirname(os.path.abspath(__file__))
NAMES = ["shoulder_pan", "shoulder_lift", "elbow_flex", "wrist_flex", "wrist_roll", "gripper"]
PIPER = ["J1", "J2", "J3", "J5", "J6"]  # what the five body joints drive
PI_FILES = ["follower.py", "Up_and_Down.py", "fake_piper.py"]
ALIGN = os.path.join(HERE, "align.json")


# ------------------------------------------------------------------ the leader (Feetech bus)

class Leader:
    """Present_Position (address 56, 2 bytes) of servos 1-6, with one SYNC READ per sample."""

    ADDR, IDS = 56, (1, 2, 3, 4, 5, 6)

    def __init__(self, port, baud=1_000_000):
        import serial  # pyserial

        self.ser = serial.Serial(port, baud, timeout=0.02)
        self.ser.reset_input_buffer()
        self.sync = True

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
        if self.sync:
            self._send(0xFE, 0x82, [self.ADDR, 2, *self.IDS])
            got = self._parse(self.ser.read(8 * len(self.IDS)))
            if len(got) == len(self.IDS):
                return [got[i] for i in self.IDS]
            self.sync = False  # some adapters/firmware don't answer SYNC READ: one at a time
            print("leader: SYNC READ didn't answer, reading the servos one at a time")
        vals = []
        for sid in self.IDS:
            self._send(sid, 0x02, [self.ADDR, 2])
            got = self._parse(self.ser.read(8))
            if sid not in got:
                raise IOError(f"leader servo {sid} didn't answer on {self.ser.port}")
            vals.append(got[sid])
        return vals


class Mapping:
    """Leader raw counts -> PiPER J1 J2 J3 J5 J6 (deg) and gripper stroke (mm)."""

    def __init__(self, args):
        m = json.load(open(os.path.join(HERE, "analysis", "joint_map.json")))["nominal_map"]
        self.sign = [m[n]["sign"] for n in NAMES[:5]]
        self.off = [m[n]["offset_deg"] for n in NAMES[:5]]
        self.calib = None
        path = args.calib or default_calib()
        if path and os.path.exists(path):
            c = json.load(open(path))
            self.calib = {n: c[n] for n in NAMES}
            print(f"leader calibration: {path}")
        else:
            print("leader calibration: none found, so each joint's zero is count 2047 (where "
                  "LeRobot's calibration puts the middle). Pass --calib to use yours.")
        self.align = [0.0] * 5
        if os.path.exists(ALIGN) and not args.no_align:
            self.align = json.load(open(ALIGN))["align_deg"]
            print(f"alignment from {ALIGN}: {[round(v, 1) for v in self.align]}")
        self.grip_range = args.gripper_range
        self.grip_max = args.grip_max_mm
        self.grip_invert = args.gripper_invert

    def degrees(self, raw):
        """LeRobot's degrees mode: (count - middle of the calibrated range) * 360 / 4095."""
        out = []
        for name, v in zip(NAMES[:5], raw[:5]):
            c = self.calib and self.calib[name]
            mid = (c["range_min"] + c["range_max"]) / 2 if c else 2047
            d = (v - mid) * 360 / 4095
            out.append(-d if c and c.get("drive_mode") else d)
        return out

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
        return (1 - pct if self.grip_invert else pct) * self.grip_max

    def piper(self, raw):
        d = self.degrees(raw)
        q = [s * x + o + a for s, x, o, a in zip(self.sign, d, self.off, self.align)]
        return q, self.gripper_mm(raw)

    def set_align(self, raw, arm5):
        d = self.degrees(raw)
        new = [t - (s * x + o) for t, s, x, o in zip(arm5, self.sign, d, self.off)]
        if max(abs(v) for v in new) > 45:
            return f"not aligned: an offset would be {max(abs(v) for v in new):.0f} deg. Put " \
                   "the leader in the arm's pose first"
        self.align = new
        with open(ALIGN, "w") as f:
            json.dump({"align_deg": [round(v, 2) for v in new], "saved": time.ctime()}, f)
        return f"aligned; offsets {[round(v, 1) for v in new]} saved to align.json"


def default_calib():
    base = os.path.join(os.path.expanduser("~"), ".cache", "huggingface", "lerobot",
                        "calibration", "teleoperators", "so101_leader")
    if os.path.isdir(base):
        files = sorted((os.path.join(base, f) for f in os.listdir(base) if f.endswith(".json")),
                       key=os.path.getmtime)
        return files[-1] if files else None
    return None


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


# ------------------------------------------------------------------ the Pi side

def bundle():
    buf = io.BytesIO()
    with tarfile.open(fileobj=buf, mode="w:gz") as tar:
        for name in PI_FILES:
            tar.add(os.path.join(HERE, "pi", name), arcname=name)
    return base64.b64encode(buf.getvalue()) + b"\n"


def start_follower(args):
    fargs = args.follower_args or []
    if args.dry_run:
        fargs = ["--dry-run", *fargs]
    if args.local:
        cmd = [sys.executable, "-u", os.path.join(HERE, "pi", "follower.py"), *fargs]
        blob = b""
    else:
        py = args.pi_python
        follower = f"{py} ~/so101/follower.py {shlex.join(fargs)}"
        run = follower if args.dry_run else f"{py} ~/arm_power.py run -- {follower}"
        blob = bundle()
        remote = (f"mkdir -p ~/so101 && head -c {len(blob)} | base64 -d | "
                  f"tar -xzf - -C ~/so101 && exec {run}")
        target = f"{args.user}@{args.host}" if args.user else args.host
        cmd = ["ssh", "-T", "-o", "ServerAliveInterval=2", "-o", "ServerAliveCountMax=5",
               "-o", "ConnectTimeout=15", *args.ssh_opt, target, remote]
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                            stderr=subprocess.STDOUT, bufsize=0)
    if blob:
        proc.stdin.write(blob)
        proc.stdin.flush()
    return proc


class Session:
    def __init__(self, proc):
        self.proc = proc
        self.hello = self.ready = self.state = self.bye = None
        self.rtt = []
        self.log = queue.Queue()
        self.lock = threading.Lock()
        self.wlock = threading.Lock()
        threading.Thread(target=self._read, daemon=True).start()

    def _read(self):
        for raw in self.proc.stdout:
            line = raw.decode("utf-8", "replace").rstrip("\r\n")
            kind, _, rest = line.partition(" ")
            try:
                if kind == "@S":
                    self.state = json.loads(rest)
                elif kind == "@P":
                    self.rtt = (self.rtt + [time.time() - float(rest)])[-20:]
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


# ------------------------------------------------------------------ keys and display

def space_down():
    if os.name == "nt":
        import ctypes

        return bool(ctypes.windll.user32.GetAsyncKeyState(0x20) & 0x8000)
    return None  # elsewhere: SPACE toggles in the window


def fmt_row(label, vals):
    return f"{label:8s}" + "".join(f"{'--' if v is None else f'{v:7.1f}':>8s}" for v in vals)


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0],
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--port", default="COM10", help="the leader's serial port")
    ap.add_argument("--host", help="the arm Pi (tailnet name or LAN address)")
    ap.add_argument("--user", help="login on the arm Pi")
    ap.add_argument("--ssh-opt", action="append", default=[], help="extra ssh option, repeatable")
    ap.add_argument("--pi-python", default="~/piper-venv/bin/python")
    ap.add_argument("--calib", help="LeRobot so101_leader calibration JSON (default: newest in "
                                    "~/.cache/huggingface/lerobot/calibration/...)")
    ap.add_argument("--no-align", action="store_true", help="ignore align.json")
    ap.add_argument("--gripper-range", type=lambda s: [float(v) for v in s.split(",")],
                    help="leader gripper counts CLOSED,OPEN (default: from the calibration)")
    ap.add_argument("--gripper-invert", action="store_true")
    ap.add_argument("--grip-max-mm", type=float, default=70.0)
    ap.add_argument("--hz", type=float, default=100.0)
    ap.add_argument("--video", help="optional video source for the window (anything "
                                    "cv2.VideoCapture opens)")
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
    if args.local and not args.dry_run:
        ap.error("--local runs the follower here, so it needs --dry-run")
    if args.auto is not None and not args.dry_run:
        ap.error("--auto holds the deadman by itself, so it is only allowed with --dry-run")
    if not args.local and not args.host:
        ap.error("--host is required (or --local --dry-run)")

    back_at = None if args.auto is None else max(0.0, args.auto - 3.0)
    leader = FakeLeader(back_at) if args.fake_leader else Leader(args.port)
    mapping = None if args.fake_leader else Mapping(args)
    raw = None if args.fake_leader else leader.read()
    if raw is not None:
        q, g = mapping.piper(raw)
        print("leader now ->", dict(zip(PIPER, [round(v, 1) for v in q])),
              "gripper", "--" if g is None else f"{g:.0f} mm")

    cv2 = None
    if args.auto is None:
        try:
            import cv2  # noqa: F811
        except ImportError:
            print("opencv-python isn't installed: no window. Q/A from this console")
    if args.auto is None and space_down() is None and cv2 is None:
        sys.exit("need either Windows (hold SPACE) or opencv-python (SPACE toggles)")

    print("starting the follower" + (" (DRY RUN)" if args.dry_run else
                                     ": the arm powers on through the relay"))
    sess = Session(start_follower(args))
    cap = None
    if cv2 is not None and args.video:
        cap = cv2.VideoCapture(args.video)
    period = 1.0 / args.hz
    seq, t_next, t_ping, t_ui = 0, time.monotonic(), 0.0, 0.0
    toggled, quitting, auto_t0, msg, t_quit = False, False, None, "", 0.0
    lines = []
    while True:
        while not sess.log.empty():
            m = sess.log.get()
            print(m, flush=True)
            lines = (lines + [m])[-6:]
        if sess.bye is not None or sess.proc.poll() is not None:
            break
        now = time.monotonic()
        ready5 = None
        if sess.hello:
            r = sess.ready or sess.hello["ready"]
            ready5 = [r[0], r[1], r[2], r[4], r[5]]
        if args.fake_leader:
            if sess.ready and leader.t0 is None:
                leader.t0 = now
            q5, grip = leader.piper(ready5) if ready5 else (None, None)
        else:
            try:
                raw = leader.read()
            except IOError as e:
                raw = None
                msg = str(e)
            q5, grip = mapping.piper(raw) if raw else (None, None)
        # deadman
        key = -1
        if cv2 is not None:
            key = cv2.waitKey(1) & 0xFF
        elif os.name == "nt":
            import msvcrt

            if msvcrt.kbhit():
                key = ord(msvcrt.getwch().lower()[:1] or " ")
        if args.auto is not None:
            if sess.ready and auto_t0 is None:
                auto_t0 = now
            dm = auto_t0 is not None and now - auto_t0 < args.auto
            if auto_t0 is not None and now - auto_t0 >= args.auto + 1.0 and now - t_quit > 2:
                t_quit = now
                sess.send("Q")
                print("auto: Q", flush=True)
        else:
            sd = space_down()
            if sd is None and key == ord(" "):
                toggled = not toggled
            dm = sd if sd is not None else toggled
        if key in (ord("q"), 27) and not quitting:
            sess.send("Q")
            msg = "Q sent: the arm parks once it's near READY"
        if key == ord("a") and not args.fake_leader and raw and sess.state:
            st = sess.state
            if st["ph"] == "hold" and not dm:
                arm5 = [st["q"][i] for i in (0, 1, 2, 4, 5)]
                msg = mapping.set_align(raw, arm5)
            else:
                msg = "align only while holding (deadman released)"
        if q5 is not None:
            seq += 1
            g = "nan" if grip is None else f"{grip:.1f}"
            ok = sess.send(f"T {seq} {time.time():.3f} {int(bool(dm))} "
                           + " ".join(f"{v:.2f}" for v in q5) + f" {g}")
            if not ok:
                msg = "can't write to the Pi"
        if now - t_ping >= 1.0:
            t_ping = now
            sess.send(f"P {time.time():.3f}")
        if now - t_ui >= 0.05:
            t_ui = now
            st = sess.state or {}
            arm = st.get("q")
            arm5 = [arm[i] for i in (0, 1, 2, 4, 5)] if arm else [None] * 5
            diff = [None if a is None or b is None else b - a
                    for a, b in zip(arm5, q5 or [None] * 5)]
            rtt = sorted(sess.rtt)[len(sess.rtt) // 2] * 1000 if sess.rtt else None
            status = [f"phase {st.get('ph', 'starting')}   deadman {'HELD' if dm else 'off'}"
                      + (f"   RTT {rtt:.0f} ms (median)" if rtt else ""),
                      f"{st.get('why') or ''}",
                      fmt_row("joint", []) + "".join(f"{j:>8s}" for j in PIPER),
                      fmt_row("leader", q5 or [None] * 5),
                      fmt_row("arm", arm5),
                      fmt_row("off by", diff),
                      f"gripper leader {'--' if grip is None else f'{grip:.0f}'} mm, "
                      f"arm {st.get('grip', '--')} mm   lowest point {st.get('z', '--')} mm",
                      msg, *lines]
            if cv2 is not None:
                show(cv2, cap, status)
            elif args.auto is None:
                sys.stdout.write("\r" + status[0] + "  " + status[1][:60] + " " * 10)
                sys.stdout.flush()
        t_next += period
        pause = t_next - time.monotonic()
        if pause > 0:
            time.sleep(pause)
        else:
            t_next = time.monotonic()
    while not sess.log.empty():
        print(sess.log.get(), flush=True)
    try:
        sess.proc.wait(timeout=30)
    except subprocess.TimeoutExpired:
        sess.proc.kill()
    rc = sess.proc.returncode
    bye = sess.bye or {}
    print(f"\nsession over: follower {bye.get('why', '?')}; exit {rc}")
    if rc != 0 and not args.dry_run:
        print("The relay stays on unless the arm was parked (arm_power.py says why above). "
              "If the arm is parked: ssh to the Pi and run "
              "~/piper-venv/bin/python ~/arm_power.py off")
    if cv2 is not None:
        cv2.destroyAllWindows()
    sys.exit(0 if rc == 0 else 1)


def show(cv2, cap, status):
    import numpy as np

    frame = None
    if cap is not None:
        ok, frame = cap.read()
        if ok:
            h, w = frame.shape[:2]
            frame = cv2.resize(frame, (960, int(960 * h / w)))
        else:
            frame = None
    panel = np.zeros((24 * len(status) + 12, 960, 3), np.uint8)
    for i, text in enumerate(status):
        cv2.putText(panel, str(text)[:110], (8, 24 * (i + 1)), cv2.FONT_HERSHEY_SIMPLEX, 0.55,
                    (255, 255, 255), 1, cv2.LINE_AA)
    img = panel if frame is None else np.vstack([frame, panel])
    cv2.imshow("SO-101 -> PiPER (hold SPACE to move, Q to park and quit)", img)


if __name__ == "__main__":
    main()
