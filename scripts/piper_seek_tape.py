#!/usr/bin/env python3
"""Find the roll of tape with the fixed camera and pick it up, steering the arm continuously from
what the camera sees (issue #19, test 2), then stand it back at the start (r = 247 mm, J1 = 0).

    ~/piper-venv/bin/python piper_seek_tape.py                  # read-only: watch and report
    ~/piper-venv/bin/python piper_seek_tape.py --go --video ~/seek/run.mjpeg --trace ~/seek/run.csv

How it sees. piper_vision.py (its own process, in ~/vision-venv) finds the green roll on every
camera frame (56 fps, full field) and sends its bbox and, for each surface it could stand on
(the table, or the 60 mm shelf), where the ray through its lowest point meets that surface. The
camera model (camera.json) was fitted to the arm itself: the roll's image position in the
2026-10-16 test 1 video against its position from the forward kinematics while the arm carried
it (900 frames, 2.5 px median error). This script keeps the hypothesis that is reachable and
whose distance matches the roll's apparent size, and filters the estimate (outliers rejected).

How it moves. One 100 Hz loop. The fingertip state (radius, azimuth, height) chases a target
through a speed-limited proportional law whose velocity is low-passed (tau --tau-s), so every
start, stop and change of target is a smooth acceleration, never a step. The target is the
hover above the latest estimate of the roll, updated on every camera frame, so the path bends
as the estimate sharpens instead of running waypoint to waypoint; it moves in (r, azimuth, z),
so it swings around the base rather than across it. Joint targets come from a precomputed
table of the tool-down pose (iktable.json: J2, J3, J5 against radius and height for J1 = 0, the
fingers across the arm plane as piper_pick_tape.py grasps; J1 is the azimuth, J4 = 0, J6 fixed),
interpolated each tick and streamed with MOVE J, as piper_pick_tape.py streams its paths.

Sequence. Switch to CAN command mode, enable, and open the gripper, which proves the motors
respond (after the parking reset the arm sits in STANDBY mode and ignores commands: the
enabled-but-idle first tries). Refuse to move if a joint's reading changed on enabling (J1
jumped +7.9 deg on every such enable on 2026-10-16; see docs/issue-19/test2-2026-10-16-seek).
Rise out of the camera's way into the look pose (unfolded up and out to the camera's right,
where it hides 1.5 % of the reachable table and shelf, against 24 % folded at rest), and as
soon as the roll is locked, steer to the hover above it; descend once the hover is reached and
the estimate has settled (it is frozen from then on, and frames where the arm is between the
camera and the roll are never used), close, check the grip, lift, carry around to the start,
set it down, open, rise, and go home and park as piper_pick_tape.py does.
"""
import argparse
import json
import math
import os
import socket
import subprocess
import sys
import threading
import time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import piper_pick_tape as P  # noqa: E402

MDEG = P.MDEG
HZ = 100


class Table:
    """Tool-down joint table in (r, z) for J1 = 0, bilinear; J1 = azimuth."""

    def __init__(self, path):
        g = json.load(open(path))
        self.r0, self.r1, self.dr = g["r0"], g["r1"], g["dr"]
        self.z0, self.z1, self.dz = g["z0"], g["z1"], g["dz"]
        self.j6 = g["j6"]
        self.q = {(int(r), int(z)): q for r, col in g["rows"].items() for z, q in col.items()}

    def zmax(self, r):
        """Highest fingertip z reachable at radius r (conservative over the two columns)."""
        best = math.inf
        for rr in (self.dr * math.floor(r / self.dr), self.dr * math.ceil(r / self.dr)):
            zs = [z for (r_, z), q in self.q.items() if r_ == rr and q]
            best = min(best, max(zs) if zs else -math.inf)
        return best

    def joints(self, r, th, z):
        if not (self.r0 <= r <= self.r1 and self.z0 <= z <= self.z1):
            return None
        i0 = self.dr * math.floor(r / self.dr)
        k0 = self.dz * math.floor(z / self.dz)
        i1, k1 = min(i0 + self.dr, self.r1), min(k0 + self.dz, self.z1)
        a, b = (r - i0) / self.dr, (z - k0) / self.dz
        cs = [self.q.get((i0, k0)), self.q.get((i1, k0)), self.q.get((i0, k1)), self.q.get((i1, k1))]
        if any(c is None for c in cs):
            return None
        q = [(1 - a) * (1 - b) * c00 + a * (1 - b) * c10 + (1 - a) * b * c01 + a * b * c11
             for c00, c10, c01, c11 in zip(*cs)]
        q[0] = th
        return q


class Cam:
    """camera.json in pure Python (the arm venv has no numpy): arm frame (mm) -> 2304x1296 px."""

    def __init__(self, path):
        c = json.load(open(path))
        rv = c["rvec"]
        th = math.sqrt(sum(x * x for x in rv))
        k = [x / th for x in rv]
        K = [[0, -k[2], k[1]], [k[2], 0, -k[0]], [-k[1], k[0], 0]]
        K2 = P.matmul(K, K)
        self.R = [[(1 if i == j else 0) + math.sin(th) * K[i][j] + (1 - math.cos(th)) * K2[i][j]
                   for j in range(3)] for i in range(3)]
        self.t, self.f, self.cx, self.cy, self.k1 = c["tvec"], c["f"], c["cx"], c["cy"], c["k1"]

    def project(self, X):
        """(u, v, depth) of arm-frame point X."""
        Xc = [a + b for a, b in zip(P.mat_vec(self.R, X), self.t)]
        x, y = Xc[0] / Xc[2], Xc[1] / Xc[2]
        d = 1 + self.k1 * (x * x + y * y)
        return self.f * x * d + self.cx, self.f * y * d + self.cy, Xc[2]


def arm_segments(q):
    """The arm as thick 3D segments (a, b, radius mm): links, gripper body and its rail (about
    150 mm along the finger axis), and the finger pair."""
    Ts = P.fk_all(q)
    el, wr, fl, tp = P.pos(Ts[2]), P.pos(Ts[4]), P.pos(Ts[5]), P.tip(Ts[5], 150.0)
    fa = P.mat_vec(P.rot(Ts[5]), P.finger_axis_6())
    zt = [Ts[5][0][2], Ts[5][1][2], Ts[5][2][2]]
    gb = [a + 45 * b for a, b in zip(fl, zt)]
    ft = [a - 30 * b for a, b in zip(tp, zt)]
    return [([0, 0, 123.0], el, 50), (el, wr, 45), (wr, fl, 45), (fl, tp, 30),
            ([a - 75 * b for a, b in zip(gb, fa)], [a + 75 * b for a, b in zip(gb, fa)], 25),
            ([a - 35 * b for a, b in zip(ft, fa)], [a + 35 * b for a, b in zip(ft, fa)], 15)]


def seg_px_dist(p, a, b):
    vx, vy = b[0] - a[0], b[1] - a[1]
    n = vx * vx + vy * vy
    t = 0.0 if n == 0 else max(0.0, min(1.0, ((p[0] - a[0]) * vx + (p[1] - a[1]) * vy) / n))
    return math.hypot(p[0] - a[0] - t * vx, p[1] - a[1] - t * vy)


class Seen:
    """Latest detections from piper_vision.py over UDP, and the filtered roll estimate."""

    def __init__(self, port, cam=None, joints=None, r_lo=140, r_hi=520):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.bind(("127.0.0.1", port))
        self.sock.setblocking(False)
        self.r_lo, self.r_hi = r_lo, r_hi
        self.recent = []       # (t, x, y, zs) of the last frames that had a usable roll
        self.frames = 0
        self.last_t = None
        self.est = None        # [x, y, zs]
        self.locked_t = None
        self.frozen = False
        self.n_used = 0
        self.n_rejected = 0
        self.n_occluded = 0
        self.cam, self.joints = cam, joints  # to drop frames where the arm is in front of the roll

    def arm_in_front(self, msg, h, segs):
        """True if a part of the arm nearer the camera than the roll overlaps its bbox."""
        _, _, d_roll = self.cam.project([h[0], h[1], h[2] + 24.5])
        half = 0.5 * max(msg["bw"], msg["bh"])
        for a, b, rad in segs:
            pa, pb = self.cam.project(a), self.cam.project(b)
            if min(pa[2], pb[2]) > d_roll:
                continue
            r_px = self.cam.f * rad / max(1.0, min(pa[2], pb[2]))
            if seg_px_dist((msg["u"], msg["v"]), pa, pb) < half + r_px + 6:
                return True
        return False

    def pick(self, msg):
        ok = [h for h in msg.get("hyp", []) if self.r_lo <= math.hypot(h[0], h[1]) <= self.r_hi
              and abs(h[3]) < 0.45]
        return min(ok, key=lambda h: abs(h[3])) if ok else None

    def poll(self):
        new = 0
        segs = arm_segments(self.joints()) if self.cam and self.joints else None
        while True:
            try:
                data, _ = self.sock.recvfrom(4096)
            except BlockingIOError:
                return new
            msg = json.loads(data)
            self.frames += 1
            self.last_t = msg["t"]
            if msg.get("u") is None:
                continue
            h = self.pick(msg)
            if h is None:
                continue
            if segs is not None and self.arm_in_front(msg, h, segs):
                self.n_occluded += 1
                continue
            new += 1
            self.recent = [r for r in self.recent if r[0] > msg["t"] - 0.4] + [(msg["t"], h[0], h[1], h[2])]
            if self.frozen:
                continue
            if self.est is None:
                pts = [r for r in self.recent if r[3] == h[2]]
                if len(pts) >= 12:
                    mx = sorted(p[1] for p in pts)[len(pts) // 2]
                    my = sorted(p[2] for p in pts)[len(pts) // 2]
                    # far along the camera's line of sight one pixel is ~12 mm (shelf) on
                    # this low camera, so consistency is judged loosely and the filter smooths
                    near = [p for p in pts if math.hypot(p[1] - mx, p[2] - my) < 40]
                    if len(near) >= 10:
                        self.est = [sum(p[1] for p in near) / len(near),
                                    sum(p[2] for p in near) / len(near), h[2]]
                        self.locked_t = msg["t"]
            elif h[2] == self.est[2] and math.hypot(h[0] - self.est[0], h[1] - self.est[1]) < 60:
                self.est[0] += 0.08 * (h[0] - self.est[0])
                self.est[1] += 0.08 * (h[1] - self.est[1])
                self.n_used += 1
            else:
                self.n_rejected += 1


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--can", default="can0")
    ap.add_argument("--go", action="store_true", help="enable the motors and move")
    ap.add_argument("--table", default=os.path.join(HERE, "iktable.json"))
    ap.add_argument("--camera", default=os.path.join(HERE, "camera.json"))
    ap.add_argument("--vision-python", default=os.path.expanduser("~/vision-venv/bin/python"))
    ap.add_argument("--udp", type=int, default=5005)
    ap.add_argument("--video", help="record every 4th camera frame to this MJPEG file")
    ap.add_argument("--trace", help="100 Hz CSV: joints, gripper, targets, estimate")
    ap.add_argument("--look", default="300,0,155",
                    help="look pose r_mm,azimuth_deg,z_mm (default: unfolded up and out to the "
                         "camera's right, seen edge-on; it hides 1.5 %% of the reachable table and "
                         "shelf that the base doesn't, against 24 %% folded at rest)")
    ap.add_argument("--home-r-mm", type=float, default=247.0, help="where to stand the roll")
    ap.add_argument("--home-deg", type=float, default=0.0)
    ap.add_argument("--tape-top-mm", type=float, default=49.0)
    ap.add_argument("--clear-mm", type=float, default=60.0, help="hover above the roll's top")
    ap.add_argument("--overlap-mm", type=float, default=28.0)
    ap.add_argument("--drop-mm", type=float, default=5.0)
    ap.add_argument("--vmax", type=float, default=50.0, help="fingertip speed cap, mm/s")
    ap.add_argument("--vdown", type=float, default=20.0, help="speed cap going straight up or down")
    ap.add_argument("--gain", type=float, default=0.8, help="1/s: speed per mm of distance")
    ap.add_argument("--tau-s", type=float, default=0.3,
                    help="velocity low-pass (gain * tau <= 0.25 keeps it critically damped)")
    ap.add_argument("--speed", type=int, default=20, help="MOVE J speed cap percent")
    ap.add_argument("--open-mm", type=float, default=65.0)
    ap.add_argument("--grip-mm-s", type=float, default=60.0)
    ap.add_argument("--grip-nm", type=float, default=1.0)
    ap.add_argument("--squeeze-mm", type=float, default=3.0)
    ap.add_argument("--min-grip-nm", type=float, default=0.5)
    ap.add_argument("--slip-mm", type=float, default=2.0)
    ap.add_argument("--seek-s", type=float, default=20.0, help="give up if not seen in this long")
    ap.add_argument("--watch-s", type=float, default=8.0, help="read-only: watch this long")
    ap.add_argument("--table-margin-mm", type=float, default=20.0)
    ap.add_argument("--visit", help="instead of seeking, steer through these poses "
                                    "(r,az,z;r,az,z...), holding 2 s at each, then park: a check "
                                    "of the arm against the camera")
    args = ap.parse_args()

    table = Table(args.table)
    seen = Seen(args.udp, cam=Cam(args.camera))
    vcmd = [args.vision_python, os.path.join(HERE, "piper_vision.py"), "--udp", str(args.udp),
            "--camera", args.camera, "--seconds", "600"]
    if args.video:
        vcmd += ["--record", args.video, "--log", os.path.splitext(args.video)[0] + "_vision.csv"]
    vision = subprocess.Popen(vcmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    try:
        t0 = time.time()
        while seen.frames < 20:
            seen.poll()
            if time.time() - t0 > 8:
                sys.exit("no camera frames from piper_vision.py")
            time.sleep(0.01)
        print(f"camera: frames flowing ({seen.frames} in {time.time() - t0:.1f} s)", flush=True)
        if not args.go:
            t0 = time.time()
            while time.time() - t0 < args.watch_s:
                seen.poll()
                time.sleep(0.01)
            print(f"watched {args.watch_s:.0f} s: {seen.frames} frames, "
                  f"{len(seen.recent)} usable in the last 0.4 s", flush=True)
            if seen.est:
                e = seen.est
                print(f"roll locked at x = {e[0]:.0f}, y = {e[1]:.0f} mm on the "
                      f"{'table' if e[2] == 0 else 'shelf'} (r = {math.hypot(e[0], e[1]):.0f} mm, "
                      f"azimuth {math.degrees(math.atan2(e[1], e[0])):.1f} deg)", flush=True)
            else:
                print("roll not seen (hidden, or outside the reachable area)", flush=True)
            return
        run(args, table, seen)
    finally:
        time.sleep(1.0)
        vision.terminate()
        try:
            vision.wait(timeout=10)
        except subprocess.TimeoutExpired:
            vision.kill()


def run(args, table, seen):
    state = open(f"/sys/class/net/{args.can}/operstate").read().strip()
    if state not in ("up", "unknown"):
        sys.exit(f"{args.can} is {state}")
    from piper_sdk import C_PiperInterface_V2
    piper = C_PiperInterface_V2(args.can)
    piper.ConnectPort()
    t0 = time.time()
    while piper.GetArmJointMsgs().Hz <= 0:
        if time.time() - t0 > 3:
            sys.exit("no joint feedback on the bus")
        time.sleep(0.1)
    time.sleep(0.3)
    q_home = P.joints_deg(piper)
    seen.joints = lambda: P.joints_deg(piper)
    g0 = P.gripper_mm(piper)
    print(f"start joints {P.fmt(q_home)}  gripper {g0:.1f} mm", flush=True)
    if any(abs(v) > 5.0 for v in q_home[1:3]):
        sys.exit("J2/J3 not within 5 deg of zero (arm not folded at rest); not moving")
    q_park = P.clamp_limits(q_home)
    look = [float(v) for v in args.look.split(",")]
    q_look = table.joints(look[0], look[1], look[2])
    if q_look is None:
        sys.exit("look pose not in the IK table")

    tr = open(args.trace, "w") if args.trace else None
    if tr:
        tr.write("t,phase," + ",".join(f"j{i}" for i in range(1, 7)) + ",grip_mm,grip_nm,"
                 + ",".join(f"cmd{i}" for i in range(1, 7)) + ",r,az,z,tr,taz,tz,ex,ey,es,nseen\n")
    S = {"phase": "start", "q": None, "r": None, "az": None, "z": None, "tgt": (None, None, None)}

    def log():
        if not tr:
            return
        g = piper.GetArmGripperMsgs().gripper_state
        q = S["q"]
        e = seen.est or (None, None, None)
        tr.write(f"{time.time():.3f},{S['phase']}," + ",".join(f"{v:.3f}" for v in P.joints_deg(piper))
                 + f",{g.grippers_angle / MDEG:.2f},{g.grippers_effort / MDEG:.3f},"
                 + (",".join(f"{v:.3f}" for v in q) if q else ",,,,,")
                 + "," + ",".join("" if v is None else f"{v:.2f}" for v in (S["r"], S["az"], S["z"], *S["tgt"]))
                 + "," + ",".join("" if v is None else f"{v:.1f}" for v in e) + f",{len(seen.recent)}\n")

    def send(q):
        S["q"] = q
        piper.MotionCtrl_2(0x01, 0x01, args.speed, 0x00)
        piper.JointCtrl(*[round(v * MDEG) for v in q])

    def tick_sleep(t_next):
        seen.poll()
        log()
        time.sleep(max(0.0, t_next - time.time()))

    def enable():
        if int(piper.GetArmStatus().arm_status.arm_status) == 0x01:
            piper.ResetPiper()
            time.sleep(0.5)
        foc = piper.GetArmGripperMsgs().gripper_state.foc_status
        if foc.motor_overheating or foc.driver_error_status or foc.driver_overheating:
            for _ in range(5):
                piper.GripperCtrl(0, 0, 0x02, 0)
                time.sleep(0.1)
            time.sleep(0.5)
        # After the reset that parks the arm, it sits in STANDBY control mode and ignores joint
        # and gripper commands even with the motors enabled (the enabled-but-idle first tries on
        # 2026-10-16: a second run worked only because the first had switched the mode). So
        # switch to CAN command mode, MOVE J, before enabling.
        t0 = time.time()
        while int(piper.GetArmStatus().arm_status.ctrl_mode) != 0x01:
            piper.MotionCtrl_2(0x01, 0x01, args.speed, 0x00)
            if time.time() - t0 > 2:
                print("  control mode still not CAN after 2 s", flush=True)
                break
            time.sleep(0.02)
        t0 = time.time()
        while not (piper.EnablePiper() and all(piper.GetArmEnableStatus())):
            if time.time() - t0 > 5:
                sys.exit("motors did not enable within 5 s")
            time.sleep(0.01)
        piper.MotionCtrl_2(0x01, 0x01, args.speed, 0x00)

    # -------- enable, and prove the motors respond with a small gripper move (no arm motion)
    for attempt in range(3):
        enable()
        w_test = args.open_mm if abs(g0 - args.open_mm) > 2.0 else args.open_mm - 4.0
        S["phase"] = "open"
        w = P.set_gripper(piper, w_test, args.grip_nm, args.grip_mm_s, wait_s=0.8)
        if abs(w - g0) > 1.0:
            break
        print(f"  gripper did not move ({g0:.1f} -> {w:.1f} mm): motors enabled but idle; "
              f"cycling them", flush=True)
        t0 = time.time()
        while piper.DisablePiper() and time.time() - t0 < 3:
            time.sleep(0.01)
        time.sleep(1.5)
    else:
        sys.exit("arm does not respond after three enables; not moving")
    q_on = P.joints_deg(piper)
    print(f"enabled; gripper at {w:.1f} mm; J1 reads {q_on[0]:.2f} deg "
          f"(before enabling {q_home[0]:.2f})", flush=True)
    if abs(q_on[0] - q_home[0]) > 1.0:
        # 2026-10-16: on every run that enabled this way J1's reading jumped +7.9 deg without the
        # arm moving, so the arm went 7.9 deg short of the roll, and parking at the old reading
        # turned the folded arm 7.9 deg further each run. Don't move on a joint reference that
        # just changed.
        print(f"  J1's reading changed by {q_on[0] - q_home[0]:+.2f} deg on enabling, without "
              f"moving: its reference is not trustworthy; parking without moving", flush=True)
        piper.GripperCtrl(round(g0 * MDEG), 0, 0x00, 0)
        P.park(piper, "estop")
        sys.exit(2)
    if abs(w - args.open_mm) > 1.5:
        w = P.set_gripper(piper, args.open_mm, args.grip_nm, args.grip_mm_s, wait_s=0.5)

    gripping = False
    try:
        # -------- out of the camera's way: joint-space min-jerk from home to the look pose
        S["phase"] = "to_look"
        dur, _ = P.stream_timing(P.line_path(q_home, q_look), args.speed, 4.0)
        steps = round(dur * HZ)
        t_s = time.time()
        q0 = P.joints_deg(piper)
        for k in range(1, steps + 1):
            s = P.min_jerk(k / steps)
            send([a + (b - a) * s for a, b in zip(q0, q_look)])
            tick_sleep(t_s + k / HZ)
        print(f"at the look pose after {dur:.1f} s; roll "
              + ("locked" if seen.est else "not seen yet"), flush=True)

        # -------- the 100 Hz steering loop
        r, az, z = look
        S.update(r=r, az=az, z=z)
        v = [0.0, 0.0, 0.0]  # dr, tangential, dz in mm/s
        dt = 1.0 / HZ

        def steer(target, vmax, until, timeout_s, check=None):
            """Chase target() (r, az, z) until until() is true; return False on timeout/check."""
            nonlocal r, az, z, v
            t_s = time.time()
            k = 0
            while True:
                k += 1
                tgt = target()
                S["tgt"] = tgt
                rm = max(r, 100.0)
                # J1 stays inside [-150, 150], so the azimuth error never wraps
                e = [tgt[0] - r, math.radians(tgt[1] - az) * rm, tgt[2] - z]
                vc = [args.gain * x for x in e]
                n = math.sqrt(sum(x * x for x in vc))
                if n > vmax:
                    vc = [x * vmax / n for x in vc]
                a = dt / args.tau_s
                v = [vi + (ci - vi) * a for vi, ci in zip(v, vc)]
                r += v[0] * dt
                az += math.degrees(v[1] * dt / rm)
                z += v[2] * dt
                z = min(z, table.zmax(r) - 2.0)
                q = table.joints(r, az, z)
                if q is None or not P.in_limits(q):
                    print(f"  steering left the reachable table at r = {r:.0f}, z = {z:.0f}: "
                          f"holding", flush=True)
                    return False
                S.update(r=r, az=az, z=z)
                send(q)
                if check is not None and not check():
                    return False
                if until(e):
                    return True
                if time.time() - t_s > timeout_s:
                    print(f"  timed out steering to {tgt}", flush=True)
                    return False
                tick_sleep(t_s + k * dt)

        def speed():
            return math.sqrt(sum(x * x for x in v))

        def surface_top():
            return seen.est[2] + args.tape_top_mm

        def hover_z(rr, top):
            return min(top + args.clear_mm, table.zmax(rr) - 5.0)

        if args.visit:
            for k_, pose in enumerate(args.visit.split(";")):
                tgt = tuple(float(v) for v in pose.split(","))
                S["phase"] = f"visit{k_}"
                steer(lambda: tgt, args.vmax, lambda e: math.sqrt(sum(x * x for x in e)) < 1.0
                      and speed() < 1.0, 40.0)
                t_h = time.time()
                steer(lambda: tgt, args.vmax, lambda e: time.time() - t_h > 2.0, 10.0)
                print(f"  held at {tgt}: joints {P.fmt(P.joints_deg(piper))}", flush=True)
            return

        # wait at the look pose until the roll is locked (steering holds the pose meanwhile)
        S["phase"] = "seek"
        t_seek = time.time()
        if not seen.est:
            steer(lambda: tuple(look), args.vmax, lambda e: seen.est is not None, args.seek_s)
        if not seen.est:
            print(f"roll not found within {args.seek_s:.0f} s", flush=True)
            return
        e = seen.est
        print(f"roll locked {seen.locked_t - t_seek:+.2f} s after the look pose: x = {e[0]:.0f}, "
              f"y = {e[1]:.0f} mm on the {'table' if e[2] == 0 else 'shelf'}", flush=True)

        # steer to the hover over the latest estimate, re-aimed on every frame
        S["phase"] = "approach"

        def hover_target():
            ex, ey, _ = seen.est
            rr = math.hypot(ex, ey)
            return (rr, math.degrees(math.atan2(ey, ex)), hover_z(rr, surface_top()))

        settled = {"t": None}

        def at_hover(e):
            close = math.hypot(e[0], e[1]) < 2.0 and abs(e[2]) < 2.0 and speed() < 2.0
            if not close:
                settled["t"] = None
                return False
            settled["t"] = settled["t"] or time.time()
            return time.time() - settled["t"] > 0.4

        if not steer(hover_target, args.vmax, at_hover, 60.0):
            return
        seen.frozen = True
        ex, ey, es = seen.est
        rr, aa = math.hypot(ex, ey), math.degrees(math.atan2(ey, ex))
        z_grasp = surface_top() - args.overlap_mm
        if z_grasp - es < args.table_margin_mm:
            sys.exit("grasp height under the margin above the surface")
        print(f"over the roll: r = {rr:.1f} mm, azimuth {aa:.2f} deg ({seen.n_used} frames "
              f"refined it, {seen.n_rejected} rejected, {seen.n_occluded} with the arm in front); "
              f"descending to z = {z_grasp:.0f} mm",
              flush=True)

        # straight down (r and azimuth held)
        S["phase"] = "down"
        steer(lambda: (rr, aa, z_grasp), args.vdown,
              lambda e: abs(e[2]) < 0.8 and speed() < 1.0, 30.0)
        P.settle(piper, S["q"], args.speed)
        P.log_tip(piper, 150.0, "settled at")

        S["phase"] = "close"
        gripping = True
        w, ef = P.close_on(piper, args.grip_nm, args.grip_mm_s)
        print(f"  fingers stopped at {w:.1f} mm, holding {ef:.2f} N*m", flush=True)
        if w >= 3.0:
            piper.GripperCtrl(round(max(0.0, w - args.squeeze_mm) * MDEG),
                              round(args.grip_nm * MDEG), 0x01, 0)
            time.sleep(0.5)
            w, ef = P.gripper_mm(piper), P.gripper_nm(piper)
            print(f"  holding {w:.1f} mm, {ef:.2f} N*m", flush=True)
        if w < 3.0 or ef < args.min_grip_nm:
            print("  no grip on the roll: not lifting", flush=True)
            S["phase"] = "release"
            P.set_gripper(piper, args.open_mm, args.grip_nm, args.grip_mm_s)
            gripping = False
            S["phase"] = "up"
            steer(lambda: (rr, aa, hover_z(rr, surface_top())), args.vmax,
                  lambda e: abs(e[2]) < 1.0, 30.0)
            return

        w0, bad = w, [0]

        def holding():
            ww, ee = P.gripper_mm(piper), P.gripper_nm(piper)
            bad[0] = bad[0] + 1 if abs(ww - w0) > args.slip_mm or ee < 0.5 * args.min_grip_nm else 0
            if bad[0] >= 5:
                print(f"  grip lost: {ww:.1f} mm, {ee:.2f} N*m", flush=True)
                return False
            return True

        # lift, carry around to the start, set it down
        z_lift = hover_z(rr, surface_top())
        S["phase"] = "lift"
        if not steer(lambda: (rr, aa, z_lift), args.vdown, lambda e: abs(e[2]) < 1.0, 30.0, holding):
            return
        z_place_hover = hover_z(args.home_r_mm, args.tape_top_mm)
        z_carry = max(z_lift, z_place_hover)
        S["phase"] = "carry"
        if not steer(lambda: (args.home_r_mm, args.home_deg, min(z_carry, table.zmax(args.home_r_mm) - 5)),
                     args.vmax, lambda e: math.hypot(e[0], e[1]) < 1.0 and speed() < 1.0, 90.0, holding):
            return
        z_rel = args.drop_mm + (z_grasp - es)
        S["phase"] = "place"
        steer(lambda: (args.home_r_mm, args.home_deg, z_rel), args.vdown,
              lambda e: abs(e[2]) < 0.8 and speed() < 1.0, 30.0)
        P.settle(piper, S["q"], args.speed)
        P.log_tip(piper, 150.0, "set down at")
        S["phase"] = "release"
        w = P.set_gripper(piper, args.open_mm, args.grip_nm, args.grip_mm_s)
        gripping = False
        print(f"  released, gripper at {w:.1f} mm", flush=True)
        S["phase"] = "rise"
        steer(lambda: (args.home_r_mm, args.home_deg, z_place_hover), args.vdown,
              lambda e: abs(e[2]) < 1.0, 30.0)
    finally:
        if gripping:  # interrupted while holding: set it down where the arm is and let go
            print("  still holding: lowering and letting go", flush=True)
            S["phase"] = "abort_release"
            P.set_gripper(piper, args.open_mm, args.grip_nm, args.grip_mm_s)
        q0 = P.joints_deg(piper)
        low, _ = P.lowest_and_keep_out(P.line_path(q0, q_park, 50), 150.0, 0, 1e9, 0)
        if low[0] < 10:
            print(f"  WARNING: the way home dips to z = {low[0]:.0f} ({low[1]}); "
                  f"leaving the arm where it is, motors on", flush=True)
            return
        S["phase"] = "home"
        dur, _ = P.stream_timing(P.line_path(q0, q_park), args.speed, 6.0)
        steps = round(dur * HZ)
        t_s = time.time()
        for k in range(1, steps + 1):
            s = P.min_jerk(k / steps)
            send([a + (b - a) * s for a, b in zip(q0, q_park)])
            tick_sleep(t_s + k / HZ)
        P.settle(piper, q_park, args.speed)
        S["phase"] = "gripper"
        P.set_gripper(piper, g0, args.grip_nm, args.grip_mm_s)
        q = P.joints_deg(piper)
        if all(abs(a - b) <= 5.0 for a, b in zip(q, q_home)):
            piper.GripperCtrl(round(g0 * MDEG), 0, 0x00, 0)
            S["phase"] = "park"
            P.park(piper, "estop")
        else:
            print("WARNING: not back home, leaving motors enabled:", P.fmt(q), flush=True)
        if tr:
            for _ in range(50):
                log()
                time.sleep(0.01)
            tr.close()


if __name__ == "__main__":
    main()
