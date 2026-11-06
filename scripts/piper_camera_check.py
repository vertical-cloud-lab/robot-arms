#!/usr/bin/env python3
"""Small, filmed moves of the PiPER, to check the side camera's view against the joint angles
(issue #24).

Runs on the arm Pi, in the venv that has piper_sdk (~/piper-venv), or anywhere for --plan-only.
Only the standard library, so the digital twin (piper_twin.py) can import the same protocol.

    python piper_camera_check.py --plan-only --json plan.json   # no CAN: plan from the rest
                                                                 # pose recorded on 2026-10-09
    ~/piper-venv/bin/python piper_camera_check.py               # read-only: plan from live joints
    ~/piper-venv/bin/python piper_camera_check.py --go --video run.mjpeg --trace run.csv

The protocol. From the folded rest pose the arm lifts a little to READY (J2 +15, J3 -15,
J5 25 deg; the fingertips stay within about 30 mm of where they rest), then makes one small move
per joint and comes back to READY after each, so every move starts from the same picture:
J1 -/+8, J2 +8, J3 -10, J4 +/-12, J5 +/-12, J6 +/-30 deg, then a 20 mm square with the
fingertips in the arm's plane. Each pose is held for --hold-s so the camera gets still frames;
the returns to READY measure repeatability. Then it goes home and parks.

How it moves. Every move is streamed: joint targets at 100 Hz along the straight joint-space line
with a minimum-jerk profile, all joints together (one PiPER MOVE J does not synchronize the
joints; see issue #19). No joint goes faster than --max-deg-s, and the MOVE J speed cap is set
1.5x above that so no joint lags. --repeat N runs the whole protocol N times.

Safety:
- Without --go nothing is sent to the arm; only ConnectPort's queries and feedback reads.
- Refuses to start unless joint feedback is live and J2 and J3 are within --zero-tol-deg of zero.
- Every pose is checked against the joint limits, and every streamed path is sampled so the
  elbow, wrist, flange and fingertips stay --table-margin-mm above the table, the fingertips
  stay within --max-reach-mm of the J1 axis and within --max-side-mm of the arm's starting plane
  (the shelf on the table is behind the arm in the camera view).
- On any failure it streams back to READY and then home, and turns the motors off only at home
  (disabling elsewhere drops the arm).
"""
import argparse
import json
import math
import os
import subprocess
import sys
import threading
import time

MDEG = 1000  # piper_sdk joint units are 0.001 degree
LIMITS_DEG = [(-150, 150), (0, 180), (-170, 0), (-100, 100), (-70, 70), (-120, 120)]
DEG_S_PER_PCT = 1.67  # MOVE J joint speed per speed percent (issue #19)
STREAM_HZ = 100
TIP_MM = 135.8  # flange to fingertips along the tool axis (URDF finger meshes)

# Modified DH table from piper_sdk.kinematics.C_PiperForwardKinematics (dh_is_offset=1)
DH_A = [0, 0, 285.03, -21.98, 0, 0]
DH_ALPHA = [0, -math.pi / 2, 0, math.pi / 2, -math.pi / 2, math.pi / 2]
DH_THETA = [0, -math.radians(172.22), -math.radians(102.78), 0, 0, 0]
DH_D = [123, 0, 0, 250.75, 0, 91]

# Rest pose on 2026-10-09 (joint feedback, deg, motors off), for --plan-only.
REST_JOINTS_DEG = [3.99, -1.96, 2.15, 1.38, 23.34, 64.29]

READY = {1: 15.0, 2: -15.0, 4: 25.0}  # J2, J3, J5 at READY; J1, J4, J6 keep their start values
# (label, joint index, offset from READY in deg) for the single-joint moves
JOINT_MOVES = [("J1 -8", 0, -8), ("J1 +8", 0, 8), ("J2 +8", 1, 8), ("J3 -10", 2, -10),
               ("J4 +12", 3, 12), ("J4 -12", 3, -12), ("J5 +12", 4, 12), ("J5 -12", 4, -12),
               ("J6 +30", 5, 30), ("J6 -30", 5, -30)]
SQUARE_MM = 20.0  # fingertip square in the arm plane: forward, up, back, down


# ---------------------------------------------------------------- kinematics
def matmul(A, B):
    return [[sum(A[i][k] * B[k][j] for k in range(len(B))) for j in range(len(B[0]))]
            for i in range(len(A))]


def link_tf(alpha, a, theta, d):
    ca, sa, ct, st = math.cos(alpha), math.sin(alpha), math.cos(theta), math.sin(theta)
    return [[ct, -st, 0, a], [st * ca, ct * ca, -sa, -sa * d],
            [st * sa, ct * sa, ca, ca * d], [0, 0, 0, 1]]


def fk_all(q_deg):
    """4x4 transforms of links 1..6 in the base frame (mm), matching piper_sdk's CalFK."""
    T = [[1, 0, 0, 0], [0, 1, 0, 0], [0, 0, 1, 0], [0, 0, 0, 1]]
    out = []
    for i in range(6):
        T = matmul(T, link_tf(DH_ALPHA[i], DH_A[i], math.radians(q_deg[i]) + DH_THETA[i], DH_D[i]))
        out.append(T)
    return out


def points(q_deg):
    """Elbow (J3), wrist (J5), flange and fingertip positions, mm."""
    Ts = fk_all(q_deg)
    T6 = Ts[5]
    tip = [T6[i][3] + TIP_MM * T6[i][2] for i in range(3)]
    return {"elbow": [Ts[2][i][3] for i in range(3)], "wrist": [Ts[4][i][3] for i in range(3)],
            "flange": [T6[i][3] for i in range(3)], "tip": tip}


def tip_pose(q_deg):
    """Fingertip position (mm) and tool pitch in the arm plane (rad)."""
    T6 = fk_all(q_deg)[5]
    tip = [T6[i][3] + TIP_MM * T6[i][2] for i in range(3)]
    return tip, math.atan2(T6[2][2], math.hypot(T6[0][2], T6[1][2]))


def planar_ik(q_seed, dx_mm, dz_mm, iters=60):
    """Move the fingertips by (dx along the arm plane, dz up) keeping the tool pitch, using
    J2, J3 and J5 only (Gauss-Newton with a numeric Jacobian; J1, J4, J6 stay put)."""
    p0, pitch0 = tip_pose(q_seed)
    j1 = math.radians(q_seed[0])
    u = [math.cos(j1), math.sin(j1)]
    goal = [p0[0] + dx_mm * u[0], p0[1] + dx_mm * u[1], p0[2] + dz_mm, pitch0]
    q = list(q_seed)
    idx = (1, 2, 4)

    def resid(qq):
        p, pitch = tip_pose(qq)
        r = (p[0] - goal[0]) * u[0] + (p[1] - goal[1]) * u[1]
        return [r, p[2] - goal[2], 200.0 * (pitch - goal[3])]

    for _ in range(iters):
        e = resid(q)
        if max(abs(v) for v in e) < 0.02:
            break
        J = []
        for j in idx:
            qh = list(q)
            qh[j] += 1e-3
            J.append([(a - b) / 1e-3 for a, b in zip(resid(qh), e)])
        J = [list(r) for r in zip(*J)]  # 3 x 3, rows: residuals, cols: joints
        dq = solve3(J, [-v for v in e])
        for j, d in zip(idx, dq):
            q[j] += max(-5.0, min(5.0, d))
    return q, max(abs(v) for v in resid(q))


def solve3(A, b):
    det = lambda M: (M[0][0] * (M[1][1] * M[2][2] - M[1][2] * M[2][1])
                     - M[0][1] * (M[1][0] * M[2][2] - M[1][2] * M[2][0])
                     + M[0][2] * (M[1][0] * M[2][1] - M[1][1] * M[2][0]))
    D = det(A)
    out = []
    for c in range(3):
        M = [list(r) for r in A]
        for r in range(3):
            M[r][c] = b[r]
        out.append(det(M) / D)
    return out


def in_limits(q):
    return all(lo - 1e-6 <= v <= hi + 1e-6 for v, (lo, hi) in zip(q, LIMITS_DEG))


def clamp_limits(q):
    return [min(max(v, lo), hi) for v, (lo, hi) in zip(q, LIMITS_DEG)]


def fmt(q):
    return "[" + ", ".join(f"{v:7.2f}" for v in q) + "]"


# ---------------------------------------------------------------- protocol
def min_jerk(s):
    return s * s * s * (10 - 15 * s + 6 * s * s)


def build_protocol(q_start, hold_s=1.0, max_deg_s=10.0, repeat=1):
    """Segments (label, joints from, joints to, move s, hold s), starting and ending at home.
    Home is the start pose clamped into the joint limits (J2 = J3 = 0, see issue #19)."""
    home = clamp_limits(q_start)
    ready = list(home)
    for j, v in READY.items():
        ready[j] = v
    poses = []
    for _ in range(repeat):
        for label, j, d in JOINT_MOVES:
            q = list(ready)
            q[j] += d
            poses += [(label, q), ("READY", ready)]
        for label, dx, dz in (("tip +x", SQUARE_MM, 0), ("tip +x +z", SQUARE_MM, SQUARE_MM),
                              ("tip +z", 0, SQUARE_MM)):
            q, err = planar_ik(ready, dx, dz)
            if err > 0.5:
                raise RuntimeError(f"IK for {label} is {err:.2f} off")
            poses.append((label, q))
        poses.append(("READY", ready))
    segs = []
    prev = q_start
    for label, q in [("home", home), ("READY", ready)] + poses + [("home", home)]:
        d = max(abs(a - b) for a, b in zip(prev, q))
        move_s = max(1.0, 1.875 * d / max_deg_s)  # min-jerk peak speed is 1.875x the mean
        segs.append({"label": label, "from": list(prev), "to": list(q), "move_s": move_s,
                     "hold_s": hold_s if label != "home" else 0.5})
        prev = q
    return segs


def timeline(segs, hz=20.0, lead_s=1.0):
    """(t, label, joints) samples of the whole protocol, as streamed, for the digital twin."""
    out, t = [], 0.0
    q0 = segs[0]["from"]
    for k in range(int(lead_s * hz)):
        out.append((k / hz, "start", q0))
    t = lead_s
    for s in segs:
        n = max(1, int(round(s["move_s"] * hz)))
        for k in range(1, n + 1):
            f = min_jerk(k / n)
            out.append((t + k / hz, s["label"], [a + (b - a) * f for a, b in zip(s["from"], s["to"])]))
        t += s["move_s"]
        for k in range(1, int(round(s["hold_s"] * hz)) + 1):
            out.append((t + k / hz, s["label"], s["to"]))
        t += s["hold_s"]
    return out


def check_plan(segs, args):
    """Joint limits on every pose and table, reach and side clearance along every path."""
    j1 = math.radians(segs[0]["to"][0])
    normal = [-math.sin(j1), math.cos(j1)]
    low, reach, side, ok = (math.inf, ""), 0.0, 0.0, True
    for s in segs:
        if not in_limits(s["to"]):
            print(f"  OUT OF LIMITS: {s['label']} {fmt(s['to'])}")
            ok = False
        for k in range(21):
            f = k / 20
            q = [a + (b - a) * f for a, b in zip(s["from"], s["to"])]
            P = points(q)
            for name, p in P.items():
                low = min(low, (p[2], name))
            tip = P["tip"]
            reach = max(reach, math.hypot(tip[0], tip[1]))
            side = max(side, abs(tip[0] * normal[0] + tip[1] * normal[1]))
    total = sum(s["move_s"] + s["hold_s"] for s in segs)
    print(f"{len(segs)} moves over {total:.0f} s; lowest point: {low[1]} at {low[0]:.0f} mm; "
          f"fingertips reach {reach:.0f} mm from J1 and {side:.0f} mm off the start plane")
    if low[0] < args.table_margin_mm:
        print(f"  TOO LOW: under {args.table_margin_mm} mm")
        ok = False
    if reach > args.max_reach_mm:
        print(f"  TOO FAR: over {args.max_reach_mm} mm")
        ok = False
    if side > args.max_side_mm:
        print(f"  TOO FAR SIDEWAYS: over {args.max_side_mm} mm")
        ok = False
    return ok


def plan(args, q_start):
    segs = build_protocol(q_start, args.hold_s, args.max_deg_s, args.repeat)
    print(f"start {fmt(q_start)}")
    for s in segs:
        print(f"  {s['label']:10s} {fmt(s['to'])}  move {s['move_s']:.1f} s, hold {s['hold_s']:.1f} s")
    ok = check_plan(segs, args)
    if args.json:
        json.dump({"start": q_start, "segments": segs,
                   "ready": [v for v in segs[1]["to"]], "args": vars(args)},
                  open(args.json, "w"), indent=1)
        print(f"wrote {args.json}")
    if not ok:
        sys.exit("plan failed its checks; not moving")
    return segs


# ---------------------------------------------------------------- hardware
def joints_deg(piper):
    js = piper.GetArmJointMsgs().joint_state
    return [getattr(js, f"joint_{i}") / MDEG for i in range(1, 7)]


TRACE = {"target": None, "phase": "start"}


def trace_loop(piper, path, stop):
    """Joints, gripper and the commanded target at 100 Hz to CSV, with wall-clock time."""
    with open(path, "w") as f:
        f.write("unix_t,phase," + ",".join(f"j{i}" for i in range(1, 7)) + ",grip_mm,"
                + ",".join(f"cmd{i}" for i in range(1, 7)) + "\n")
        while not stop.is_set():
            g = piper.GetArmGripperMsgs().gripper_state
            cmd = TRACE["target"]
            f.write(f"{time.time():.3f},{TRACE['phase']},"
                    + ",".join(f"{v:.3f}" for v in joints_deg(piper))
                    + f",{g.grippers_angle / MDEG:.2f},"
                    + (",".join(f"{v:.3f}" for v in cmd) if cmd else ",,,,,") + "\n")
            time.sleep(0.01)


def settle(piper, target_deg, speed, tol_deg=0.2, timeout_s=3.0):
    """Hold the target until the joints are within tol_deg; return the largest joint error."""
    t0 = time.time()
    while time.time() - t0 < timeout_s:
        piper.MotionCtrl_2(0x01, 0x01, speed, 0x00)
        piper.JointCtrl(*[round(v * MDEG) for v in target_deg])
        if all(abs(a - b) <= tol_deg for a, b in zip(joints_deg(piper), target_deg)):
            break
        time.sleep(0.02)
    return max(abs(a - b) for a, b in zip(joints_deg(piper), target_deg))


def stream(piper, qa, qb, duration_s, speed):
    """Joint targets at STREAM_HZ along the line qa -> qb on a minimum-jerk profile, then
    settle; returns the largest joint error at the end."""
    steps = max(1, round(duration_s * STREAM_HZ))
    t0 = time.time()
    for k in range(1, steps + 1):
        f = min_jerk(k / steps)
        q = [a + (b - a) * f for a, b in zip(qa, qb)]
        TRACE["target"] = q
        piper.MotionCtrl_2(0x01, 0x01, speed, 0x00)
        piper.JointCtrl(*[round(v * MDEG) for v in q])
        time.sleep(max(0.0, t0 + k / STREAM_HZ - time.time()))
    return settle(piper, qb, speed)


def hold(piper, q, speed, seconds):
    t0 = time.time()
    while time.time() - t0 < seconds:
        piper.MotionCtrl_2(0x01, 0x01, speed, 0x00)
        piper.JointCtrl(*[round(v * MDEG) for v in q])
        time.sleep(0.02)


def park(piper, how, settle_s=6.0):
    """Motors off at home. 'drop' disables (the arm falls ~2 deg onto its rest, as in the
    issue #19 runs); 'estop' sends the quick stop first, waits, then resets (untested)."""
    if how == "estop":
        TRACE["phase"] = "estop"
        piper.EmergencyStop(0x01)
        time.sleep(settle_s)
        TRACE["phase"] = "reset"
        piper.ResetPiper()
        time.sleep(0.5)
    TRACE["phase"] = "disable"
    t0 = time.time()
    while piper.DisablePiper() and time.time() - t0 < 5:
        time.sleep(0.01)
    time.sleep(0.3)
    print(f"disabled at home: {fmt(joints_deg(piper))}; arm status "
          f"{piper.GetArmStatus().arm_status.arm_status}", flush=True)


VIDEO = {"proc": None}


def start_video(path, width, height):
    """MJPEG of the full sensor field of view (the 2304x1296 mode, scaled), with frame times.
    The 1536x864 mode is a centre crop that cuts off the base, so it is not used here."""
    VIDEO["proc"] = subprocess.Popen(
        ["rpicam-vid", "-n", "-t", "0", "--mode", "2304:1296:10:P", "--width", str(width),
         "--height", str(height), "--framerate", "20", "--codec", "mjpeg", "--quality", "80",
         "--save-pts", path + ".pts", "-o", path],
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    VIDEO["start_unix"] = time.time()
    time.sleep(2.0)  # let the camera start and settle exposure before anything moves
    print(f"recording {path}", flush=True)


def stop_video():
    if VIDEO["proc"] is not None:
        time.sleep(1.0)
        VIDEO["proc"].send_signal(2)  # SIGINT: rpicam-vid closes the file cleanly
        VIDEO["proc"].wait(timeout=10)
        VIDEO["proc"] = None


def run(args, piper, segs):
    if int(piper.GetArmStatus().arm_status.arm_status) == 0x01:
        print("arm is still in the quick-stop state: resetting before enabling", flush=True)
        piper.ResetPiper()
        time.sleep(0.5)
    t0 = time.time()
    while not piper.EnablePiper():
        if time.time() - t0 > 5:
            sys.exit("motors did not enable within 5 s")
        time.sleep(0.01)
    print("enabled", flush=True)
    speed = max(1, min(30, math.ceil(1.5 * args.max_deg_s / DEG_S_PER_PCT)))
    marks = []
    done = 0
    try:
        for s in segs:
            TRACE["phase"] = s["label"]
            qa = joints_deg(piper)
            err = stream(piper, qa, s["to"], s["move_s"], speed)
            if err > args.tol_deg:
                raise RuntimeError(f"{s['label']}: {err:.2f} deg off after the move")
            t_hold = time.time()
            hold(piper, s["to"], speed, s["hold_s"])
            q = joints_deg(piper)
            marks.append({"label": s["label"], "unix_t0": t_hold, "unix_t1": time.time(),
                          "target": s["to"], "measured": q})
            print(f"  {s['label']:10s} at {fmt(q)} (target error {err:.2f} deg)", flush=True)
            done += 1
    except Exception as e:  # noqa: BLE001 - always try to get the arm home
        print(f"ABORT: {e}; going back to READY, then home", flush=True)
        ready, home = segs[1]["to"], segs[-1]["to"]
        TRACE["phase"] = "abort"
        if done > 1:
            stream(piper, joints_deg(piper), ready, 4.0, speed)
        stream(piper, joints_deg(piper), home, 4.0, speed)
    finally:
        if args.marks:
            json.dump({"video_start_unix": VIDEO.get("start_unix"), "poses": marks},
                      open(args.marks, "w"), indent=1)
    q = joints_deg(piper)
    home = segs[-1]["to"]
    if all(abs(a - b) <= args.tol_deg for a, b in zip(q, home)):
        park(piper, args.park)
    else:
        print("WARNING: not back home, leaving motors enabled so the arm does not drop:",
              fmt(q), flush=True)


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--can", default="can0")
    ap.add_argument("--plan-only", action="store_true",
                    help="no CAN: plan from the rest pose recorded on 2026-10-09")
    ap.add_argument("--go", action="store_true", help="enable the motors and move")
    ap.add_argument("--repeat", type=int, default=1, help="run the protocol this many times")
    ap.add_argument("--hold-s", type=float, default=1.0, help="hold at each pose")
    ap.add_argument("--max-deg-s", type=float, default=10.0, help="fastest any joint moves")
    ap.add_argument("--table-margin-mm", type=float, default=60.0)
    ap.add_argument("--max-reach-mm", type=float, default=260.0,
                    help="fingertips stay within this distance of the J1 axis")
    ap.add_argument("--max-side-mm", type=float, default=45.0,
                    help="fingertips stay within this distance of the arm's start plane")
    ap.add_argument("--park", choices=["drop", "estop"], default="drop")
    ap.add_argument("--tol-deg", type=float, default=1.0)
    ap.add_argument("--zero-tol-deg", type=float, default=5.0)
    ap.add_argument("--json", help="write the plan here")
    ap.add_argument("--video", help="record the run to this .mjpeg file")
    ap.add_argument("--video-size", default="1536x864")
    ap.add_argument("--trace", help="log joints and targets at 100 Hz to this CSV")
    ap.add_argument("--marks", help="write each pose's hold window and measured joints here")
    args = ap.parse_args()
    if not 1 <= args.max_deg_s <= 20:
        sys.exit("--max-deg-s must be in [1, 20]")

    if args.plan_only:
        plan(args, REST_JOINTS_DEG)
        return

    state = open(f"/sys/class/net/{args.can}/operstate").read().strip() \
        if os.path.exists(f"/sys/class/net/{args.can}") else "missing"
    if state not in ("up", "unknown"):
        sys.exit(f"{args.can} is {state}; bring it up at 1 Mbit/s first")

    from piper_sdk import C_PiperInterface_V2

    piper = C_PiperInterface_V2(args.can)
    piper.ConnectPort()
    t0 = time.time()
    while piper.GetArmJointMsgs().Hz <= 0:
        if time.time() - t0 > 3:
            sys.exit("no joint feedback on the bus: is the arm powered and wired to the adapter?")
        time.sleep(0.1)
    time.sleep(0.3)
    q_start = joints_deg(piper)
    print(f"start joints {fmt(q_start)}; arm status {piper.GetArmStatus().arm_status.arm_status}")
    if any(abs(v) > args.zero_tol_deg for v in q_start[1:3]):
        sys.exit(f"J2/J3 not within {args.zero_tol_deg} deg of zero; not moving")
    segs = plan(args, q_start)
    if not args.go:
        print("read-only run (no --go): nothing sent to the arm")
        return

    stop = threading.Event()
    tracer = threading.Thread(target=trace_loop, args=(piper, args.trace, stop), daemon=True)
    if args.trace:
        tracer.start()
    if args.video:
        w, h = (int(v) for v in args.video_size.split("x"))
        start_video(args.video, w, h)
    try:
        run(args, piper, segs)
    finally:
        stop_video()
        stop.set()
        if args.trace:
            tracer.join(timeout=2)


if __name__ == "__main__":
    main()
