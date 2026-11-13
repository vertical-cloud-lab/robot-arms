"""Run the follower against the simulated arm (no piper_sdk, no CAN, no relay), a whole
teleop.py session on this machine, and the camera reader against a fake MJPEG stream.

    python "PiPER Sandbox Scripts/Teleoperation/tests/test_dry_run.py"      (or pytest)
"""
import importlib.util
import json
import os
import subprocess
import sys
import threading
import time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
FOLLOWER = os.path.join(ROOT, "follower.py")
TELEOP = os.path.join(ROOT, "teleop.py")


class Run:
    def __init__(self, *extra):
        self.p = subprocess.Popen([sys.executable, "-u", FOLLOWER, "--dry-run", *extra],
                                  stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                  stderr=subprocess.STDOUT, bufsize=0)
        self.lines, self.ready, self.seq = [], None, 0
        threading.Thread(target=self._read, daemon=True).start()

    def _read(self):
        for raw in self.p.stdout:
            line = raw.decode().rstrip()
            self.lines.append(line)
            if line.startswith("@READY"):
                self.ready = json.loads(line.split(" ", 1)[1])["ready"]

    def wait_ready(self, timeout=40):
        t0 = time.time()
        while self.ready is None and time.time() - t0 < timeout and self.p.poll() is None:
            time.sleep(0.05)
        assert self.ready, "\n".join(self.lines)
        return self.ready

    def target(self, q6, deadman=True, grip="nan"):
        self.seq += 1
        j = [q6[0], q6[1], q6[2], q6[4], q6[5]]
        self.p.stdin.write((f"T {self.seq} {time.time():.3f} {int(deadman)} "
                            + " ".join(f"{v:.2f}" for v in j) + f" {grip}\n").encode())

    def stream(self, q6, seconds, deadman=True):
        t0 = time.time()
        while time.time() - t0 < seconds:
            self.target(q6, deadman)
            time.sleep(0.01)

    def states(self):
        return [json.loads(x.split(" ", 1)[1]) for x in self.lines if x.startswith("@S ")]

    def bye(self, timeout=60):
        rc = self.p.wait(timeout=timeout)
        byes = [json.loads(x.split(" ", 1)[1]) for x in self.lines if x.startswith("@BYE")]
        return rc, (byes[-1] if byes else None)


def test_snag_holds_until_reengaged():
    r = Run("--sim-obstacle", "1,10,1")  # J1 can't pass +10 deg
    ready = r.wait_ready()
    r.stream(ready, 0.5)
    r.stream([30.0, *ready[1:]], 2.0)  # push J1 into the obstacle
    snags = [s for s in r.states() if s["why"] and s["why"].startswith("snag")]
    assert snags, "no snag reported"
    assert snags[-1]["ph"] == "hold"
    held = r.states()[-1]["q"][0]
    assert held <= 10.01, held
    r.stream([30.0, *ready[1:]], 0.5)  # still holding the deadman: stays stopped
    assert all(s["ph"] == "hold" for s in r.states()[-5:])
    r.stream(ready, 0.5, deadman=False)  # let go: back to READY is 11 deg off, too far
    r.stream(ready, 0.5)
    assert r.states()[-1]["ph"] == "hold" and "line it up" in r.states()[-1]["why"]
    r.stream(ready, 0.3, deadman=False)  # line up with where it stopped, then re-engage
    r.stream([held - 2, *ready[1:]], 0.5)
    assert r.states()[-1]["ph"] == "follow", r.states()[-1]
    r.stream(ready, 2.0)  # and bring it back
    r.p.stdin.write(b"Q\n")
    rc, bye = r.bye()
    assert rc == 0 and bye["phase"] == "parked", (rc, bye)


def test_connection_loss_parks():
    r = Run()
    ready = r.wait_ready()
    r.stream([ready[0] + 15, ready[1] + 10, *ready[2:]], 2.0)
    r.p.stdin.close()  # the SSH session drops
    rc, bye = r.bye()
    assert rc == 0 and "connection closed" in bye["why"] and bye["phase"] == "parked", bye


def test_q_parks_from_far():
    """Q finishes from any pose: the arm goes back to READY by itself, then parks."""
    r = Run()
    ready = r.wait_ready()
    r.stream(ready, 0.5)  # engage
    far = [ready[0] + 40, *ready[1:]]
    r.stream(far, 4.0)
    assert abs(r.states()[-1]["q"][0] - far[0]) < 1, r.states()[-1]
    r.stream(far, 0.2, deadman=False)
    r.p.stdin.write(b"Q\n")
    rc, bye = r.bye()
    assert rc == 0 and bye["phase"] == "parked", (rc, bye)


def test_gripper_left_alone_by_default():
    r = Run()
    ready = r.wait_ready()
    r.stream(ready, 1.0)  # engaged, but the leader's gripper target is ignored
    for _ in range(50):
        r.target(ready, grip="5.0")
        time.sleep(0.01)
    r.p.stdin.write(b"Q\n")
    rc, bye = r.bye()
    assert rc == 0 and bye["phase"] == "parked", bye
    grips = {s["grip"] for s in r.states()}
    assert len(grips) == 1, grips


def test_gripper_follows_with_flag():
    r = Run("--gripper")
    ready = r.wait_ready()
    assert any("gripper on, holding" in x for x in r.lines), "\n".join(r.lines[-20:])
    r.stream(ready, 0.5)
    for _ in range(100):
        r.target(ready, grip="5.0")
        time.sleep(0.01)
    assert r.states()[-1]["grip"] < 10, r.states()[-1]
    r.p.stdin.write(b"Q\n")
    rc, bye = r.bye()
    assert rc == 0 and bye["phase"] == "parked", bye


def test_refuses_unless_at_rest():
    r = Run("--sim-rest", "30,-1.9,2.1,1,24.3,-52.3")  # J1 swung out
    rc, bye = r.bye()
    assert rc == 0 and "refused" in bye["why"] and "J1" in bye["why"], bye
    assert not any("enabled in" in x for x in r.lines)


def test_engage_needs_pose_match():
    r = Run()
    ready = r.wait_ready()
    r.stream([ready[0] + 30, *ready[1:]], 1.0)  # deadman held, but the leader is 30 deg off
    st = r.states()[-1]
    assert st["ph"] == "hold" and "line it up" in st["why"], st
    assert abs(st["q"][0] - ready[0]) < 0.5
    r.p.stdin.write(b"Q\n")
    rc, bye = r.bye()
    assert rc == 0 and bye["phase"] == "parked", bye


def test_teleop_session_parks():
    """teleop.py end to end: fake leader, follower on this machine, simulated arm."""
    p = subprocess.run([sys.executable, TELEOP, "--fake-leader", "--local", "--dry-run",
                        "--auto", "6"], capture_output=True, text=True, timeout=120)
    out = p.stdout + p.stderr
    assert p.returncode == 0, out
    assert "parked after: the operator finished (Q)" in out, out[-2000:]
    assert "control loop:" in out and "ping round trip" in out, out[-2000:]


FAKE_CAMERA = """
import sys, cv2, numpy as np
for i in range(40):
    img = np.full((120, 160, 3), 5 * i, np.uint8)
    sys.stdout.buffer.write(cv2.imencode(".jpg", img, [cv2.IMWRITE_JPEG_QUALITY, 95])[1].tobytes())
    sys.stdout.buffer.flush()
"""


def test_camera_keeps_only_the_newest_frame():
    try:
        import cv2  # noqa: F401
        import numpy  # noqa: F401
    except ImportError:
        print("skipped: needs opencv-python and numpy")
        return
    teleop = load_teleop()
    cam = teleop.Camera(cmd=[sys.executable, "-c", FAKE_CAMERA])
    cam.proc.wait(timeout=30)
    t0 = time.time()
    while cam.err is None and time.time() - t0 < 10:
        time.sleep(0.05)
    frame, age, n = cam.latest()
    assert frame is not None and 1 <= n <= 40, n
    assert abs(int(frame.mean()) - 5 * 39) <= 2, frame.mean()  # the last frame sent


def load_teleop():
    spec = importlib.util.spec_from_file_location("teleop", TELEOP)
    teleop = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(teleop)
    return teleop


def test_leader_reads_a_simulated_bus():
    """teleop.Leader against a simulated Feetech bus on a pseudo-terminal: SYNC READ, a lost
    reply filled in without giving up SYNC READ, and an adapter that never answers it."""
    if os.name == "nt":
        print("skipped: needs a pseudo-terminal (Linux or macOS)")
        return
    import pty
    import tty

    pos = {1: 2047, 2: 1000, 3: 3000, 4: 2100, 5: 1500, 6: 2500}
    mode = {"drop": 0, "no_sync": False}

    def chk(b):
        return (~sum(b)) & 0xFF

    def status(sid):
        body = [sid, 4, 0, pos[sid] & 0xFF, pos[sid] >> 8]
        return bytes([0xFF, 0xFF, *body, chk(body)])

    master, slave = pty.openpty()
    tty.setraw(master)
    tty.setraw(slave)

    def bus():
        buf = b""
        while True:
            buf += os.read(master, 256)
            while True:
                i = buf.find(b"\xff\xff")
                if i < 0 or len(buf) < i + 4 or len(buf) < i + 4 + buf[i + 3]:
                    break
                pkt, buf = buf[i:i + 4 + buf[i + 3]], buf[i + 4 + buf[i + 3]:]
                assert chk(pkt[2:-1]) == pkt[-1]
                if pkt[4] == 0x82 and not mode["no_sync"]:
                    ids = [s for s in pkt[7:-1] if not (s == 4 and mode["drop"])]
                    mode["drop"] = max(0, mode["drop"] - 1)
                    os.write(master, b"".join(status(s) for s in ids))
                elif pkt[4] == 0x02:
                    os.write(master, status(pkt[2]))

    threading.Thread(target=bus, daemon=True).start()
    teleop = load_teleop()
    want = [pos[i] for i in range(1, 7)]
    leader = teleop.Leader(os.ttyname(slave))
    assert leader.read() == want
    mode["drop"] = 1  # servo 4's reply to one SYNC READ is lost
    assert leader.read() == want and leader.use_sync
    mode["no_sync"] = True
    other = teleop.Leader(os.ttyname(slave))
    for _ in range(4):
        got = other.read()
    assert got == want and not other.use_sync


if __name__ == "__main__":
    tests = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    for t in tests:
        t0 = time.time()
        t()
        print(f"ok  {t.__name__}  ({time.time() - t0:.0f} s)", flush=True)
