"""Run the follower against the simulated arm (no piper_sdk, no CAN, no relay).

    python "SO-101 leader/tests/test_dry_run.py"      (or pytest)
"""
import json
import os
import subprocess
import sys
import threading
import time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
FOLLOWER = os.path.join(ROOT, "pi", "follower.py")


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


def test_far_from_ready_q_is_refused():
    r = Run()
    ready = r.wait_ready()
    far = [ready[0] + 40, *ready[1:]]
    r.stream([ready[0] + 9, *ready[1:]], 0.2)
    t0 = time.time()
    while time.time() - t0 < 3:  # walk the target out to J1 +40 within the engage window
        r.target([ready[0] + 9 + (time.time() - t0) * 15, *ready[1:]])
        time.sleep(0.01)
    r.stream(far, 1.0)
    r.p.stdin.write(b"Q\n")
    r.stream(far, 0.5)
    assert any("not finishing yet" in x for x in r.lines), "\n".join(r.lines[-20:])
    r.stream(ready, 3.0)
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


if __name__ == "__main__":
    tests = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    for t in tests:
        t0 = time.time()
        t()
        print(f"ok  {t.__name__}  ({time.time() - t0:.0f} s)", flush=True)
