#!/usr/bin/env python3
"""Plan, and optionally run, a top-down pick of the roll of tape in front of the PiPER (issue #19).

Runs on the arm Pi, in the venv that has piper_sdk (~/piper-venv), or anywhere for --plan-only:

    python piper_pick_tape.py --plan-only               # no CAN at all: print the plan from the
                                                          # rest pose recorded on 2026-10-09
    ~/piper-venv/bin/python piper_pick_tape.py          # read-only: plan from the live joints
    ~/piper-venv/bin/python piper_pick_tape.py --go --until pregrasp
    ~/piper-venv/bin/python piper_pick_tape.py --go --until descend
    ~/piper-venv/bin/python piper_pick_tape.py --go --until grasp

Where the tape is. The fixed Pi camera looks at the arm side-on. Fitting an affine map from
the arm plane to the image (J2, J3, wrist and base points from the SDK's forward kinematics,
residuals under 3 px) puts the roll's centre about 247 mm in front of the J1 axis and 26 mm
up, about 48 mm across. The camera cannot see depth, so the roll is assumed to straddle the
arm's vertical plane at the starting J1 angle, as stated in the issue.

Which way the fingers open. In the rest pose the camera sees the broad face of a finger, so
the fingers open across the arm plane. That direction is recorded in the link-6 frame
(FINGER_AXIS_6) from the rest joints, and every grasp pose keeps it across the plane, with
the tool axis pointing down (tipped --tilt-deg outward within the plane, since straight down
needs J5 = 72 deg, past its 70 deg limit). The fingers then close on the roll's flat faces.

Stages, each starting and ending at the start pose (the arm is never left away from it):
    pregrasp  open the gripper, go to fingertips --clear-mm above the roll, photo, go home
    descend   ... then lower straight down until the fingertips overlap the roll by
              --overlap-mm, photo, rise back to pregrasp, go home (no closing)
    grasp     ... then close with --effort-n, photo, lift back to the pregrasp height, photo,
              lower, open (the tape goes back where it was), rise, go home

Safety:
- Without --go nothing is sent to the arm; only ConnectPort's queries and feedback reads.
- Refuses to start unless joint feedback is live and J2 and J3 are within --zero-tol-deg of
  zero (the arm is folded at rest).
- Every waypoint is checked against the joint limits, and every joint-space segment is sampled
  so the fingertips, flange and elbow stay --table-margin-mm above the table.
- Below the pregrasp height the arm only moves in short straight-line vertical steps.
- On any failure it rises to the pregrasp height before going home, and disables the motors
  only at home (disabling elsewhere drops the arm).
"""
import argparse
import math
import os
import subprocess
import sys
import time

MDEG = 1000  # piper_sdk joint units are 0.001 degree; gripper units are 0.001 mm
LIMITS_DEG = [(-150, 150), (0, 180), (-170, 0), (-100, 100), (-70, 70), (-120, 120)]

# Modified DH table from piper_sdk.kinematics.C_PiperForwardKinematics (dh_is_offset=1)
DH_A = [0, 0, 285.03, -21.98, 0, 0]
DH_ALPHA = [0, -math.pi / 2, 0, math.pi / 2, -math.pi / 2, math.pi / 2]
DH_THETA = [0, -math.radians(172.22), -math.radians(102.78), 0, 0, 0]
DH_D = [123, 0, 0, 250.75, 0, 91]

# Rest pose on 2026-10-09 (joint feedback, deg) and the photo taken in it, in which the camera
# looks along the finger opening direction, i.e. across the arm plane.
REST_JOINTS_DEG = [3.99, -1.96, 2.15, 1.38, 23.34, 64.29]

# From that photo (see the module docstring), in the arm plane: radius from J1 and height, mm.
TAPE_R_MM = 247.0
TAPE_TOP_MM = 49.0


# ---------------------------------------------------------------- small linear algebra
def matmul(A, B):
    return [[sum(A[i][k] * B[k][j] for k in range(len(B))) for j in range(len(B[0]))]
            for i in range(len(A))]


def transpose(A):
    return [list(r) for r in zip(*A)]


def mat_vec(A, v):
    return [sum(a * b for a, b in zip(row, v)) for row in A]


def cross(a, b):
    return [a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0]]


def dot(a, b):
    return sum(x * y for x, y in zip(a, b))


def unit(v):
    n = math.sqrt(dot(v, v))
    return [x / n for x in v]


def solve(A, b):
    """Gaussian elimination with partial pivoting, A n x n."""
    n = len(b)
    M = [list(A[i]) + [b[i]] for i in range(n)]
    for c in range(n):
        p = max(range(c, n), key=lambda r: abs(M[r][c]))
        M[c], M[p] = M[p], M[c]
        for r in range(c + 1, n):
            f = M[r][c] / M[c][c]
            for k in range(c, n + 1):
                M[r][k] -= f * M[c][k]
    x = [0.0] * n
    for r in range(n - 1, -1, -1):
        x[r] = (M[r][n] - sum(M[r][k] * x[k] for k in range(r + 1, n))) / M[r][r]
    return x


# ---------------------------------------------------------------- kinematics
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


def rot(T):
    return [row[:3] for row in T[:3]]


def pos(T):
    return [T[0][3], T[1][3], T[2][3]]


def tip(T6, tcp_mm):
    """Fingertip point: tcp_mm along the link-6 z (tool) axis from the flange."""
    return [p + tcp_mm * T6[i][2] for i, p in enumerate(pos(T6))]


def plane_normal(j1_deg):
    t = math.radians(j1_deg)
    return [-math.sin(t), math.cos(t), 0.0]


def finger_axis_6():
    """Finger opening direction in the link-6 frame, from the rest photo."""
    R6 = rot(fk_all(REST_JOINTS_DEG)[5])
    s = mat_vec(transpose(R6), plane_normal(REST_JOINTS_DEG[0]))
    s[2] = 0.0  # the fingers open across the tool axis
    return unit(s)


def target_rotation(j1_deg, sign, tilt_deg):
    """Tool axis down, tipped outward by tilt_deg in the arm plane; fingers open across it."""
    a3, a1 = [0, 0, 1], finger_axis_6()
    A = transpose([a1, cross(a3, a1), a3])  # columns: link-6 basis
    t, j = math.radians(tilt_deg), math.radians(j1_deg)
    b3 = [math.sin(t) * math.cos(j), math.sin(t) * math.sin(j), -math.cos(t)]
    b1 = [sign * c for c in plane_normal(j1_deg)]
    B = transpose([b1, cross(b3, b1), b3])  # columns: where they go in the base frame
    return matmul(B, transpose(A))


def rot_error(Rt, Rc):
    """Rotation vector taking Rc to Rt, in the base frame (rad)."""
    E = matmul(Rt, transpose(Rc))
    c = max(-1.0, min(1.0, (E[0][0] + E[1][1] + E[2][2] - 1) / 2))
    ang = math.acos(c)
    v = [E[2][1] - E[1][2], E[0][2] - E[2][0], E[1][0] - E[0][1]]
    if ang < 1e-9:
        return [0.0, 0.0, 0.0]
    s = math.sin(ang)
    if s < 1e-6:  # ~180 deg
        k = [math.sqrt(max(0.0, (E[i][i] + 1) / 2)) for i in range(3)]
        return [ang * x for x in k]
    return [ang * x / (2 * s) for x in v]


def ik(p_tip, R_t, seed_deg, tcp_mm, iters=300):
    """Damped least squares on fingertip position (mm) and orientation (rad, weighted)."""
    q = list(seed_deg)
    w = 200.0  # mm per rad, so 1 deg of orientation error costs about 3.5 mm
    for _ in range(iters):
        T6 = fk_all(q)[5]
        e = [a - b for a, b in zip(p_tip, tip(T6, tcp_mm))] + \
            [w * x for x in rot_error(R_t, rot(T6))]
        if math.sqrt(dot(e[:3], e[:3])) < 0.05 and math.sqrt(dot(e[3:], e[3:])) < 0.05 * w / 200:
            break
        J = [[0.0] * 6 for _ in range(6)]
        h = 1e-3
        for j in range(6):
            qh = list(q)
            qh[j] += h
            T6h = fk_all(qh)[5]
            dp = [(a - b) / h for a, b in zip(tip(T6h, tcp_mm), tip(T6, tcp_mm))]
            dr = [w * x / h for x in rot_error(rot(T6h), rot(T6))]
            for i, v in enumerate(dp + dr):
                J[i][j] = v
        lam = 1.0
        JT = transpose(J)
        A = matmul(JT, J)
        for i in range(6):
            A[i][i] += lam
        dq = solve(A, mat_vec(JT, e))
        step = max(abs(x) for x in dq)
        if step > 5.0:
            dq = [x * 5.0 / step for x in dq]
        q = [a + b for a, b in zip(q, dq)]
    T6 = fk_all(q)[5]
    perr = math.dist(p_tip, tip(T6, tcp_mm))
    rerr = math.degrees(math.sqrt(dot(*(2 * [rot_error(R_t, rot(T6))]))))
    return q, perr, rerr


def in_limits(q):
    return all(lo - 1e-6 <= v <= hi + 1e-6 for v, (lo, hi) in zip(q, LIMITS_DEG))


def lowest_point(qa, qb, tcp_mm, n=60):
    """Lowest z (mm) of elbow, wrist, flange and fingertip along a joint-space segment."""
    low = (math.inf, "")
    for k in range(n + 1):
        q = [a + (b - a) * k / n for a, b in zip(qa, qb)]
        Ts = fk_all(q)
        for name, z in (("elbow", Ts[2][2][3]), ("wrist", Ts[4][2][3]),
                        ("flange", Ts[5][2][3]), ("fingertip", tip(Ts[5], tcp_mm)[2])):
            low = min(low, (z, name))
    return low


def fmt(q):
    return "[" + ", ".join(f"{v:7.2f}" for v in q) + "]"


# ---------------------------------------------------------------- planning
def plan(args, q_home):
    j1 = args.plane_deg if args.plane_deg is not None else q_home[0]
    u = [math.cos(math.radians(j1)), math.sin(math.radians(j1))]
    r, top = args.tape_r_mm, args.tape_top_mm

    def over(z):
        return [r * u[0], r * u[1], z]

    z_pre, z_grasp = top + args.clear_mm, top - args.overlap_mm
    if z_grasp < args.table_margin_mm:
        sys.exit(f"grasp puts the fingertips {z_grasp:.0f} mm above the table; "
                 f"under --table-margin-mm {args.table_margin_mm}")
    # pick the finger-axis sign that gives the J6 nearest the rest J6
    best = None
    for sign in (1, -1):
        R_t = target_rotation(j1, sign, args.tilt_deg)
        q, pe, re = ik(over(z_pre), R_t, [j1, 60, -60, 0, 60, q_home[5]], args.tcp_mm)
        if pe < 0.5 and re < 0.5 and in_limits(q):
            cost = abs(q[5] - q_home[5]) + abs(q[3])
            if best is None or cost < best[0]:
                best = (cost, R_t, q)
    if best is None:
        sys.exit("no IK solution for the pregrasp pose inside the joint limits")
    _, R_t, q_pre = best

    # straight vertical fingertip path from pregrasp down to grasp, steps of at most --step-mm
    n = max(1, math.ceil((z_pre - z_grasp) / args.step_mm))
    down, q = [], q_pre
    for k in range(1, n + 1):
        z = z_pre - (z_pre - z_grasp) * k / n
        q, pe, re = ik(over(z), R_t, q, args.tcp_mm)
        if pe > 0.5 or re > 0.5 or not in_limits(q):
            sys.exit(f"IK failed at fingertip z = {z:.0f} mm")
        down.append(q)

    print(f"arm plane J1 = {j1:.2f} deg; tape centre at r = {r:.0f} mm, top at z = {top:.0f} mm")
    print(f"fingertip = flange + {args.tcp_mm:.0f} mm along the tool axis")
    print(f"home       {fmt(q_home)}")
    print(f"pregrasp   {fmt(q_pre)}   fingertips at z = {z_pre:.0f} mm")
    print(f"grasp      {fmt(down[-1])}   fingertips at z = {z_grasp:.0f} mm "
          f"({len(down)} steps of {(z_pre - z_grasp) / n:.1f} mm)")

    # home -> pregrasp is one joint-space move: keep it off the table and out of the space
    # above the roll, then check the descent really is a straight vertical line
    low, keep_out = math.inf, math.inf
    for k in range(101):
        qk = [a + (b - a) * k / 100 for a, b in zip(q_home, q_pre)]
        Ts = fk_all(qk)
        for P in (pos(Ts[2]), pos(Ts[4]), pos(Ts[5]), tip(Ts[5], args.tcp_mm)):
            low = min(low, P[2])
            if abs(math.hypot(P[0], P[1]) - r) < 45 and abs(dot(P[:2], plane_normal(j1)[:2])) < 45:
                keep_out = min(keep_out, P[2] - top)
    drift = max(math.dist(tip(fk_all([a + (b - a) * k / 10 for a, b in zip(qa, qb)])[5],
                              args.tcp_mm)[:2], over(0)[:2])
                for qa, qb in zip([q_pre] + down[:-1], down) for k in range(11))
    print(f"home -> pregrasp: lowest point z = {low:.0f} mm, "
          f"closest above the roll {keep_out:.0f} mm; descent drifts {drift:.1f} mm sideways")
    if low < args.table_margin_mm or keep_out < args.clear_mm - 10 or drift > 2.0:
        sys.exit("planned path comes too close to the table or the roll; not moving")
    return {"q_pre": q_pre, "down": down}


# ---------------------------------------------------------------- hardware
def joints_deg(piper):
    js = piper.GetArmJointMsgs().joint_state
    return [getattr(js, f"joint_{i}") / MDEG for i in range(1, 7)]


def gripper_mm(piper):
    return piper.GetArmGripperMsgs().gripper_state.grippers_angle / MDEG


def move_to(piper, target_deg, speed, tol_deg, timeout_s):
    t0 = time.time()
    while time.time() - t0 < timeout_s:
        piper.MotionCtrl_2(0x01, 0x01, speed, 0x00)
        piper.JointCtrl(*[round(v * MDEG) for v in target_deg])
        if all(abs(a - b) <= tol_deg for a, b in zip(joints_deg(piper), target_deg)):
            return True
        time.sleep(0.02)
    print(f"  NOT reached {fmt(target_deg)} after {timeout_s} s, at {fmt(joints_deg(piper))}",
          flush=True)
    return False


def set_gripper(piper, width_mm, effort_n, wait_s=2.0):
    width_mm = max(0.0, min(70.0, width_mm))
    t0 = time.time()
    while time.time() - t0 < wait_s:
        piper.GripperCtrl(round(width_mm * MDEG), round(effort_n * 1000), 0x01, 0)
        time.sleep(0.02)
    return gripper_mm(piper)


def photo(outdir, name):
    path = os.path.join(outdir, f"{time.strftime('%H%M%S')}_{name}.jpg")
    r = subprocess.run(["rpicam-still", "-n", "-t", "800", "--width", "2304", "--height", "1296",
                        "-o", path], capture_output=True)
    print(f"  photo {path}" if r.returncode == 0 else f"  photo FAILED ({name})", flush=True)


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--can", default="can0")
    ap.add_argument("--plan-only", action="store_true",
                    help="no CAN: plan from the recorded rest pose")
    ap.add_argument("--go", action="store_true", help="enable the motors and move")
    ap.add_argument("--until", choices=["pregrasp", "descend", "grasp"], default="pregrasp")
    ap.add_argument("--tape-r-mm", type=float, default=TAPE_R_MM,
                    help="roll centre, distance from the J1 axis")
    ap.add_argument("--tape-top-mm", type=float, default=TAPE_TOP_MM,
                    help="top of the roll above the table")
    ap.add_argument("--plane-deg", type=float, help="J1 angle of the roll (default: start J1)")
    ap.add_argument("--tcp-mm", type=float, default=150.0, help="flange to fingertips")
    ap.add_argument("--tilt-deg", type=float, default=10.0,
                    help="tip the tool outward from vertical, in the arm plane (keeps J5 < 70)")
    ap.add_argument("--clear-mm", type=float, default=60.0, help="pregrasp clearance over roll")
    ap.add_argument("--overlap-mm", type=float, default=15.0,
                    help="how far the fingertips go below the top of the roll")
    ap.add_argument("--open-mm", type=float, default=65.0, help="gripper opening (max 70)")
    ap.add_argument("--effort-n", type=float, default=1.0, help="gripper effort (0-5)")
    ap.add_argument("--step-mm", type=float, default=5.0, help="vertical step below pregrasp")
    ap.add_argument("--table-margin-mm", type=float, default=20.0)
    ap.add_argument("--speed", type=int, default=10, help="MOVE J speed percent (1-30)")
    ap.add_argument("--tol-deg", type=float, default=1.0)
    ap.add_argument("--zero-tol-deg", type=float, default=5.0)
    ap.add_argument("--timeout-s", type=float, default=20.0)
    ap.add_argument("--photos", default=os.path.expanduser("~/pick_tape_photos"))
    args = ap.parse_args()
    if not 1 <= args.speed <= 30:
        sys.exit("--speed must be in [1, 30]")

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
    q_home = joints_deg(piper)
    print(f"start joints {fmt(q_home)}  gripper {gripper_mm(piper):.1f} mm")
    if any(abs(v) > args.zero_tol_deg for v in q_home[1:3]):
        sys.exit(f"J2/J3 not within {args.zero_tol_deg} deg of zero; not moving")
    p = plan(args, q_home)
    if not args.go:
        print("read-only run (no --go): nothing sent to the arm")
        return

    os.makedirs(args.photos, exist_ok=True)
    g0 = gripper_mm(piper)
    t0 = time.time()
    while not piper.EnablePiper():
        if time.time() - t0 > 5:
            sys.exit("motors did not enable within 5 s")
        time.sleep(0.01)
    print("enabled", flush=True)

    reached = lambda q: move_to(piper, q, args.speed, args.tol_deg, args.timeout_s)  # noqa: E731
    column = [p["q_pre"]] + p["down"]  # vertical line of waypoints, pregrasp first
    at = None  # index in column, once the arm is on it

    def along_column(to):
        """Step along the vertical column one waypoint at a time."""
        nonlocal at
        while at != to:
            nxt = at + (1 if to > at else -1)
            if not reached(column[nxt]):
                return False
            at = nxt
        return True

    try:
        print(f"opening gripper to {args.open_mm:.0f} mm", flush=True)
        print(f"  gripper at {set_gripper(piper, args.open_mm, args.effort_n):.1f} mm", flush=True)
        print("to pregrasp", flush=True)
        if not reached(p["q_pre"]):
            return
        at = 0
        photo(args.photos, "pregrasp")
        if args.until == "pregrasp":
            return
        print("descending", flush=True)
        if not along_column(len(column) - 1):
            return
        photo(args.photos, "descended")
        if args.until == "descend":
            return
        print("closing", flush=True)
        w = set_gripper(piper, 0.0, args.effort_n, wait_s=2.5)
        print(f"  gripper stopped at {w:.1f} mm", flush=True)
        photo(args.photos, "closed")
        if w < 3.0:
            print("  gripper closed on nothing: not lifting", flush=True)
            return
        print("lifting to pregrasp height", flush=True)
        if not along_column(0):
            return
        print(f"  holding, gripper at {gripper_mm(piper):.1f} mm", flush=True)
        photo(args.photos, "lifted")
        time.sleep(1.0)
        print("putting it back", flush=True)
        if not along_column(len(column) - 1):
            return
        print(f"  gripper at {set_gripper(piper, args.open_mm, args.effort_n):.1f} mm", flush=True)
        photo(args.photos, "released")
    finally:
        ok = True
        if at is not None:
            print("rising to pregrasp", flush=True)
            ok = along_column(0)
        print("returning home", flush=True)
        ok = ok and reached(q_home)
        set_gripper(piper, g0, args.effort_n, wait_s=1.5)
        q = joints_deg(piper)
        if ok and all(abs(a - b) <= args.zero_tol_deg for a, b in zip(q, q_home)):
            piper.GripperCtrl(round(g0 * MDEG), 0, 0x00, 0)
            t0 = time.time()
            while piper.DisablePiper() and time.time() - t0 < 5:
                time.sleep(0.01)
            print("disabled at home:", fmt(q), flush=True)
        else:
            print("WARNING: not back home, leaving motors enabled so the arm does not drop:",
                  fmt(q), flush=True)


if __name__ == "__main__":
    main()
