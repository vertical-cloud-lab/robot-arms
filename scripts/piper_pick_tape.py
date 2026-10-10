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
the fingers open across the arm plane (confirmed on the arm). That direction is recorded in
the link-6 frame (FINGER_AXIS_6) from the rest joints, and every grasp pose keeps it across
the plane, with the tool axis pointing down (tipped --tilt-deg outward within the plane, since
straight down needs J5 = 72 deg, past its 70 deg limit). The fingers close on the flat faces.

How the PiPER moves. One MOVE J target runs every joint at the same speed (about 1.67 deg/s
per speed percent) and stops each joint when it arrives; the joints are not interpolated
together (in the stage-2 video the forearm keeps its angle until J3 arrives, then J2 carries
on alone). So a MOVE J path is not the straight joint-space line, and a chain of short MOVE J
steps stops and restarts every joint at every step, which is what made the stage-2 descent
jerky. Here only the move out to the pregrasp hover is a single MOVE J (checked as the arm
really runs it). Everything else is streamed: joint targets at STREAM_HZ along a precomputed
path with a minimum-jerk time profile, with the speed cap set 1.5x above the fastest joint so
no joint falls behind. The descent, lift and put-back follow a straight vertical fingertip
line (one IK solution per --res-mm); the return home follows the straight joint-space line.

Gripping. The gripper reports its opening and its motor effort (N*m, the SDK's unit; the
spec sheet rates the gripper at 40 N clamping, 50 N max, for efforts up to 5 N*m). It closes
with --grip-nm and lifts only if the fingers stop on the roll (wider than 3 mm) and the effort
they hold reaches --min-grip-nm. While lifting and holding, a change in opening of more than
--slip-mm or a drop in effort puts the roll back down.

Parking. J2 = 0 and J3 = 0 are firmware limits (min and max), but the arm rests at about
J2 = -2, J3 = +2 with the motors off, so disabling at home drops it about 10 mm in 50 ms.
--park estop (default) instead sends the SDK's quick stop, which it documents as letting the
arm descend slowly, waits for the arm to settle, then resets (power off, flags cleared).
If the quick stop holds the arm instead, the reset drops it as before. --park drop disables.

Stages, each starting and ending at the start pose (the arm is never left away from it):
    pregrasp  open the gripper, go to fingertips --clear-mm above the roll, photo, go home
    descend   ... then lower straight down until the fingertips overlap the roll by
              --overlap-mm, photo, rise back to pregrasp, go home (no closing)
    grasp     ... then close and check the grip, photo, lift to the pregrasp height, hold,
              photo, lower, open (the tape goes back where it was), rise, go home

Safety:
- Without --go nothing is sent to the arm; only ConnectPort's queries and feedback reads.
- Refuses to start unless joint feedback is live and J2 and J3 are within --zero-tol-deg of
  zero (the arm is folded at rest).
- Every waypoint is checked against the joint limits, and every path is sampled (the MOVE J
  as the arm runs it, the streams as streamed) so the fingertips, flange and elbow stay
  --table-margin-mm above the table and out of the space just above the roll.
- Streams start from where the arm is, so no target is ever more than one tick ahead.
- On any failure it rises to the pregrasp height before going home, and turns the motors off
  only at home (disabling elsewhere drops the arm).
"""
import argparse
import math
import os
import subprocess
import sys
import threading
import time

MDEG = 1000  # piper_sdk joint units are 0.001 degree; gripper units are 0.001 mm, 0.001 N*m
LIMITS_DEG = [(-150, 150), (0, 180), (-170, 0), (-100, 100), (-70, 70), (-120, 120)]
DEG_S_PER_PCT = 1.67  # MOVE J joint speed per speed percent (J2/J3 ran 33.4 deg/s at 20 %)
STREAM_HZ = 100

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


def clamp_limits(q):
    return [min(max(v, lo), hi) for v, (lo, hi) in zip(q, LIMITS_DEG)]


def movej_path(qa, qb, n=200):
    """Joints along one MOVE J as the PiPER runs it: every joint at the same speed, each
    stopping when it gets there (they are not interpolated together)."""
    d = [b - a for a, b in zip(qa, qb)]
    dm = max(abs(x) for x in d) or 1.0
    return [[a + math.copysign(min(abs(x), dm * k / n), x) for a, x in zip(qa, d)]
            for k in range(n + 1)]


def line_path(qa, qb, n=200):
    """Joints along a streamed move between two poses: all joints interpolated together."""
    return [[a + (b - a) * k / n for a, b in zip(qa, qb)] for k in range(n + 1)]


def path_at(path, x):
    """Joints at fractional index x of a list of joint vectors, linearly interpolated."""
    k = min(max(int(math.floor(x)), 0), len(path) - 2)
    f = x - k
    return [a + (b - a) * f for a, b in zip(path[k], path[k + 1])]


def min_jerk(s):
    return s * s * s * (10 - 15 * s + 6 * s * s)


def stream_timing(path, pct, t_min):
    """Duration (s, at least t_min) of a min-jerk stream along path whose fastest joint stays
    under 2/3 of the speed cap of pct percent; also that joint's peak speed (deg/s)."""
    rate = max(abs(b - a) for qa, qb in zip(path, path[1:]) for a, b in zip(qa, qb)) \
        * (len(path) - 1)  # deg per unit of path parameter
    t = max(t_min, 1.875 * rate * 1.5 / (pct * DEG_S_PER_PCT))
    return t, 1.875 * rate / t


def lowest_and_keep_out(path, tcp_mm, r, top, j1):
    """Lowest z (mm) of elbow, wrist, flange and fingertip along a joint path, and how far
    above the top of the roll any of them comes while within 45 mm of it."""
    low, keep_out = (math.inf, ""), math.inf
    for q in path:
        Ts = fk_all(q)
        for name, P in (("elbow", pos(Ts[2])), ("wrist", pos(Ts[4])), ("flange", pos(Ts[5])),
                        ("fingertip", tip(Ts[5], tcp_mm))):
            low = min(low, (P[2], name))
            if abs(math.hypot(P[0], P[1]) - r) < 45 and abs(dot(P[:2], plane_normal(j1)[:2])) < 45:
                keep_out = min(keep_out, P[2] - top)
    return low, keep_out


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

    # straight vertical fingertip line from pregrasp down to grasp, one IK solution per --res-mm
    n = max(1, math.ceil((z_pre - z_grasp) / args.res_mm))
    line, q = [q_pre], q_pre
    for k in range(1, n + 1):
        z = z_pre - (z_pre - z_grasp) * k / n
        q, pe, re = ik(over(z), R_t, q, args.tcp_mm)
        if pe > 0.5 or re > 0.5 or not in_limits(q):
            sys.exit(f"IK failed at fingertip z = {z:.0f} mm")
        line.append(q)
    q_park = clamp_limits(q_home)  # the folded rest sags past the J2/J3 limits; see park()

    line_s, line_peak = stream_timing(line, args.speed, (z_pre - z_grasp) / args.line_mm_s)
    home_path = line_path(q_pre, q_park)
    home_pct = min(30, max(args.speed, math.ceil(
        1.5 * 1.875 * max(abs(a - b) for a, b in zip(q_pre, q_park)) / args.home_s / DEG_S_PER_PCT)))
    home_s, home_peak = stream_timing(home_path, home_pct, args.home_s)

    print(f"arm plane J1 = {j1:.2f} deg; tape centre at r = {r:.0f} mm, top at z = {top:.0f} mm")
    print(f"fingertip = flange + {args.tcp_mm:.0f} mm along the tool axis")
    print(f"home       {fmt(q_home)}   (parks at {fmt(q_park)})")
    print(f"pregrasp   {fmt(q_pre)}   fingertips at z = {z_pre:.0f} mm")
    print(f"grasp      {fmt(line[-1])}   fingertips at z = {z_grasp:.0f} mm")
    print(f"vertical line: {n} IK points; streamed over {line_s:.1f} s at {args.speed} %, "
          f"fastest joint peaks at {line_peak:.1f} deg/s "
          f"(cap {args.speed * DEG_S_PER_PCT:.1f})")
    print(f"return home: streamed over {home_s:.1f} s at {home_pct} %, fastest joint peaks at "
          f"{home_peak:.1f} deg/s (cap {home_pct * DEG_S_PER_PCT:.1f})")

    # home -> pregrasp is one MOVE J, checked as the arm runs it; the return is streamed along
    # the joint-space line. Both stay off the table and out of the space above the roll, and
    # the descent really is a straight vertical line.
    worst = []
    for name, path in (("home -> pregrasp (MOVE J)", movej_path(q_home, q_pre)),
                       ("pregrasp -> home (streamed)", home_path)):
        (low, what), keep_out = lowest_and_keep_out(path, args.tcp_mm, r, top, j1)
        print(f"{name}: lowest point z = {low:.0f} mm ({what}), "
              f"closest above the roll {keep_out:.0f} mm")
        worst.append((low, keep_out))
    drift = max(math.dist(tip(fk_all(path_at(line, k / 10))[5], args.tcp_mm)[:2], over(0)[:2])
                for k in range(10 * n + 1))
    print(f"descent drifts {drift:.2f} mm sideways from the vertical")
    if any(low < args.table_margin_mm or keep_out < args.clear_mm - 10 for low, keep_out in worst) \
            or drift > 1.0:
        sys.exit("planned path comes too close to the table or the roll; not moving")
    return {"q_pre": q_pre, "line": line, "q_park": q_park, "line_s": line_s,
            "home_s": home_s, "home_pct": home_pct}


# ---------------------------------------------------------------- hardware
def joints_deg(piper):
    js = piper.GetArmJointMsgs().joint_state
    return [getattr(js, f"joint_{i}") / MDEG for i in range(1, 7)]


def gripper_mm(piper):
    return piper.GetArmGripperMsgs().gripper_state.grippers_angle / MDEG


def gripper_nm(piper):
    """Effort the gripper motor reports, N*m (sign dropped)."""
    return abs(piper.GetArmGripperMsgs().gripper_state.grippers_effort) / MDEG


TRACE = {"target": None, "phase": "start"}  # what the trace thread writes next to the feedback


def trace_loop(piper, path, stop):
    """Log joints, gripper opening and effort, and the commanded target at 100 Hz to CSV."""
    with open(path, "w") as f:
        f.write("t,phase," + ",".join(f"j{i}" for i in range(1, 7)) + ",grip_mm,grip_nm,"
                + ",".join(f"cmd{i}" for i in range(1, 7)) + "\n")
        t0 = time.time()
        while not stop.is_set():
            g = piper.GetArmGripperMsgs().gripper_state
            cmd = TRACE["target"]
            f.write(f"{time.time() - t0:.3f},{TRACE['phase']},"
                    + ",".join(f"{v:.3f}" for v in joints_deg(piper))
                    + f",{g.grippers_angle / MDEG:.2f},{g.grippers_effort / MDEG:.3f},"
                    + (",".join(f"{v:.3f}" for v in cmd) if cmd else ",,,,,") + "\n")
            time.sleep(0.01)


def move_to(piper, target_deg, speed, tol_deg, timeout_s):
    TRACE["target"] = target_deg
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


def stream(piper, where, duration_s, speed, check=None):
    """Send MOVE J targets at STREAM_HZ along where(s), s from 0 to 1 on a minimum-jerk time
    profile, then hold the end. Each target is a fraction of a degree past the last, so the
    joints track the path together instead of each running to a far target on its own.
    check() runs every tick; if it returns False the arm stops where it is and this returns
    False. Otherwise returns the largest joint error once settled at the end."""
    steps = max(1, round(duration_s * STREAM_HZ))
    t0 = time.time()
    for k in range(1, steps + 1):
        q = where(min_jerk(k / steps))
        TRACE["target"] = q
        piper.MotionCtrl_2(0x01, 0x01, speed, 0x00)
        piper.JointCtrl(*[round(v * MDEG) for v in q])
        if check is not None and not check():
            return False
        time.sleep(max(0.0, t0 + k / STREAM_HZ - time.time()))
    return settle(piper, q, speed)


def log_tip(piper, tcp_mm, label):
    q = joints_deg(piper)
    P = tip(fk_all(q)[5], tcp_mm)
    print(f"  {label} {fmt(q)}: fingertips at r = {math.hypot(P[0], P[1]):.0f} mm, "
          f"z = {P[2]:.0f} mm", flush=True)


def set_gripper(piper, width_mm, effort_nm, wait_s=2.0):
    width_mm = max(0.0, min(70.0, width_mm))
    t0 = time.time()
    while time.time() - t0 < wait_s:
        piper.GripperCtrl(round(width_mm * MDEG), round(effort_nm * MDEG), 0x01, 0)
        time.sleep(0.02)
    return gripper_mm(piper)


def close_on(piper, effort_nm, timeout_s=4.0, still_s=0.3):
    """Close with effort_nm until the fingers stop (opening steady to 0.2 mm for still_s);
    return the opening and the median effort over that last still_s."""
    w_start, t0, hist = gripper_mm(piper), time.time(), []
    while time.time() - t0 < timeout_s:
        piper.GripperCtrl(0, round(effort_nm * MDEG), 0x01, 0)
        hist.append((time.time(), gripper_mm(piper), gripper_nm(piper)))
        recent = [h for h in hist if h[0] >= hist[-1][0] - still_s]
        ws = [h[1] for h in recent]
        if hist[-1][0] - t0 > 0.5 and ws[-1] < w_start - 1.0 and max(ws) - min(ws) < 0.2:
            break
        time.sleep(0.02)
    recent = sorted(h[2] for h in hist if h[0] >= hist[-1][0] - still_s)
    return hist[-1][1], recent[len(recent) // 2]


def park(piper, how, settle_s=6.0):
    """Turn the motors off at home. The firmware will not hold J2 below 0 or J3 above 0, but
    the arm rests about 2 deg past both, so a plain disable drops it there in ~50 ms.
    'estop' sends the quick stop first (the SDK: "stop the robotic arm and allow it to descend
    slowly"), waits until J2 and J3 stop moving, then resets (power off, flags cleared)."""
    if how == "estop":
        q0, t0 = joints_deg(piper), time.time()
        TRACE["phase"] = "estop"
        piper.EmergencyStop(0x01)
        hist = [(t0, q0)]
        while time.time() - t0 < settle_s:
            time.sleep(0.05)
            hist.append((time.time(), joints_deg(piper)))
            old = [q for t, q in hist if t <= hist[-1][0] - 0.5]
            if time.time() - t0 > 1.5 and old and \
                    max(abs(a - b) for a, b in zip(old[-1][1:3], hist[-1][1][1:3])) < 0.05:
                break
        q = joints_deg(piper)
        print(f"  quick stop: J2 {q0[1]:.2f} -> {q[1]:.2f}, J3 {q0[2]:.2f} -> {q[2]:.2f} deg "
              f"in {time.time() - t0:.1f} s; resetting", flush=True)
        TRACE["phase"] = "reset"
        piper.ResetPiper()
        time.sleep(0.5)
    TRACE["phase"] = "disable"
    t0 = time.time()
    while piper.DisablePiper() and time.time() - t0 < 5:
        time.sleep(0.01)
    time.sleep(0.3)
    st = piper.GetArmStatus().arm_status
    print(f"disabled at home: {fmt(joints_deg(piper))}; arm status {st.arm_status}, "
          f"motors enabled {piper.GetArmEnableStatus()}", flush=True)


VIDEO = {"proc": None, "t0": None}  # set by start_video; stills are skipped while it holds the camera


def start_video(path):
    """Record MJPEG (no H.264 encoder on the Pi 5) with frame timestamps alongside, from now on."""
    VIDEO["proc"] = subprocess.Popen(
        ["rpicam-vid", "-n", "-t", "0", "--width", "1536", "--height", "864", "--framerate", "20",
         "--codec", "mjpeg", "--quality", "70", "--save-pts", path + ".pts", "-o", path],
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    time.sleep(2.0)  # let the camera start and settle exposure before anything moves
    VIDEO["t0"] = time.time()
    print(f"recording {path}", flush=True)


def stop_video():
    if VIDEO["proc"] is not None:
        time.sleep(1.0)
        VIDEO["proc"].send_signal(2)  # SIGINT: rpicam-vid closes the file cleanly
        VIDEO["proc"].wait(timeout=10)
        VIDEO["proc"] = None


def photo(outdir, name):
    if VIDEO["proc"] is not None:
        print(f"  mark {name} at t = {time.time() - VIDEO['t0']:.1f} s of the video", flush=True)
        time.sleep(1.0)  # hold still for a clean frame
        return
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
    ap.add_argument("--grip-nm", type=float, default=1.0,
                    help="gripper effort when closing on the roll, N*m (0-5)")
    ap.add_argument("--min-grip-nm", type=float, default=0.5,
                    help="lift only if the fingers hold at least this effort on the roll")
    ap.add_argument("--slip-mm", type=float, default=2.0,
                    help="put the roll back if the opening changes this much while held")
    ap.add_argument("--res-mm", type=float, default=1.0, help="IK spacing along the vertical")
    ap.add_argument("--line-mm-s", type=float, default=20.0,
                    help="average fingertip speed along the vertical (slower if a joint needs)")
    ap.add_argument("--home-s", type=float, default=6.0, help="duration of the return home")
    ap.add_argument("--park", choices=["estop", "drop"], default="estop",
                    help="how to turn the motors off at home (see the docstring)")
    ap.add_argument("--table-margin-mm", type=float, default=20.0)
    ap.add_argument("--speed", type=int, default=10,
                    help="MOVE J speed percent (1-30) out to pregrasp and along the vertical")
    ap.add_argument("--tol-deg", type=float, default=1.0)
    ap.add_argument("--zero-tol-deg", type=float, default=5.0)
    ap.add_argument("--timeout-s", type=float, default=20.0)
    ap.add_argument("--photos", default=os.path.expanduser("~/pick_tape_photos"))
    ap.add_argument("--video", help="record the run to this .mjpeg file (marks replace stills)")
    ap.add_argument("--trace", help="log joints, gripper and targets at 100 Hz to this CSV")
    args = ap.parse_args()
    if not 1 <= args.speed <= 30:
        sys.exit("--speed must be in [1, 30]")
    if not 0 < args.min_grip_nm <= args.grip_nm <= 3.0:
        sys.exit("need 0 < --min-grip-nm <= --grip-nm <= 3")

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
    print(f"start joints {fmt(q_home)}  gripper {gripper_mm(piper):.1f} mm, "
          f"{gripper_nm(piper):.2f} N*m; arm status {piper.GetArmStatus().arm_status.arm_status}")
    if any(abs(v) > args.zero_tol_deg for v in q_home[1:3]):
        sys.exit(f"J2/J3 not within {args.zero_tol_deg} deg of zero; not moving")
    p = plan(args, q_home)
    if not args.go:
        print("read-only run (no --go): nothing sent to the arm")
        return

    os.makedirs(args.photos, exist_ok=True)
    stop = threading.Event()
    tracer = threading.Thread(target=trace_loop, args=(piper, args.trace, stop), daemon=True)
    if args.trace:
        tracer.start()
    if args.video:
        start_video(args.video)
    try:
        run(args, piper, p, q_home)
    finally:
        stop_video()  # also gives the trace a second of the arm at rest after parking
        stop.set()
        if args.trace:
            tracer.join(timeout=2)


def run(args, piper, p, q_home):
    g0 = gripper_mm(piper)
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

    line = p["line"]
    n = len(line) - 1
    at = None  # position on the line (0 = pregrasp, n = grasp; fractional mid-stream)
    gripping = False  # the fingers have closed on the roll and not opened since

    def along_line(to, check=None):
        """Stream along the vertical line from where the arm is on it to index to."""
        a = at

        def where(s):
            nonlocal at
            at = a + (to - a) * s
            return path_at(line, at)

        TRACE["phase"] = "down" if to > a else "up"
        return stream(piper, where, p["line_s"] * abs(to - a) / n, args.speed, check)

    def holding(w0):
        """Per-tick grip check: the opening stays within --slip-mm of w0 and the effort stays
        above half of --min-grip-nm (5 bad ticks in a row, 50 ms, count as a slip)."""
        bad = [0]

        def check():
            w, e = gripper_mm(piper), gripper_nm(piper)
            bad[0] = bad[0] + 1 if abs(w - w0) > args.slip_mm or e < 0.5 * args.min_grip_nm else 0
            if bad[0] >= 5:
                print(f"  grip lost: opening {w:.1f} mm (was {w0:.1f}), effort {e:.2f} N*m",
                      flush=True)
                return False
            return True
        return check

    try:
        print(f"opening gripper to {args.open_mm:.0f} mm", flush=True)
        TRACE["phase"] = "open"
        print(f"  gripper at {set_gripper(piper, args.open_mm, args.grip_nm):.1f} mm", flush=True)
        print("to pregrasp", flush=True)
        TRACE["phase"] = "to_pregrasp"
        if not move_to(piper, p["q_pre"], args.speed, args.tol_deg, args.timeout_s):
            return
        settle(piper, p["q_pre"], args.speed)
        at = 0
        photo(args.photos, "pregrasp")
        if args.until == "pregrasp":
            return
        print(f"descending over {p['line_s']:.1f} s", flush=True)
        along_line(n)
        log_tip(piper, args.tcp_mm, "settled at")
        photo(args.photos, "descended")
        if args.until == "descend":
            return
        print(f"closing with {args.grip_nm:.2f} N*m", flush=True)
        TRACE["phase"] = "close"
        gripping = True
        w, e = close_on(piper, args.grip_nm)
        print(f"  fingers stopped at {w:.1f} mm, holding {e:.2f} N*m", flush=True)
        photo(args.photos, "closed")
        if w < 3.0 or e < args.min_grip_nm:
            print("  closed on nothing: not lifting" if w < 3.0 else
                  f"  grip under {args.min_grip_nm:.2f} N*m: not lifting", flush=True)
            return
        print("lifting to pregrasp height", flush=True)
        check = holding(w)
        if along_line(0, check) is False:
            return
        print(f"  holding at {gripper_mm(piper):.1f} mm, {gripper_nm(piper):.2f} N*m", flush=True)
        photo(args.photos, "lifted")
        TRACE["phase"] = "hold"
        t0 = time.time()
        while time.time() - t0 < 1.0 and check():
            time.sleep(0.01)
        print("putting it back", flush=True)
        along_line(n)
        log_tip(piper, args.tcp_mm, "settled at")
        TRACE["phase"] = "release"
        print(f"  gripper at {set_gripper(piper, args.open_mm, args.grip_nm):.1f} mm", flush=True)
        gripping = False
        photo(args.photos, "released")
    finally:
        if gripping:  # a failed grip, a slip or an interruption: set the roll down and let go
            if at < n:
                print("putting the roll back down", flush=True)
                along_line(n)
            print(f"  gripper at {set_gripper(piper, args.open_mm, args.grip_nm):.1f} mm",
                  flush=True)
        if at is not None and at > 0:
            print("rising to pregrasp", flush=True)
            along_line(0)
        print(f"returning home over {p['home_s']:.1f} s", flush=True)
        TRACE["phase"] = "home"
        q0 = joints_deg(piper)
        err = stream(piper, lambda s: [a + (b - a) * s for a, b in zip(q0, p["q_park"])],
                     p["home_s"], p["home_pct"])
        TRACE["phase"] = "gripper"
        set_gripper(piper, g0, args.grip_nm, wait_s=1.5)
        q = joints_deg(piper)
        if err <= args.tol_deg and all(abs(a - b) <= args.zero_tol_deg for a, b in zip(q, q_home)):
            piper.GripperCtrl(round(g0 * MDEG), 0, 0x00, 0)
            park(piper, args.park)
        else:
            print("WARNING: not back home, leaving motors enabled so the arm does not drop:",
                  fmt(q), flush=True)


if __name__ == "__main__":
    main()
