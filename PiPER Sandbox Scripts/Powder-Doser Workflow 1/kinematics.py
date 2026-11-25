"""Where the gripper goes: inverse kinematics for picking from above, straight-line and swing
paths, and the checks that keep the arm off the table, out of the keep-out boxes (the A1
mini) and inside its joint windows.

The forward kinematics is Up_and_Down.fk (piper_sdk's own DH table), so every joint angle
this file produces is checked against the same model the rest of the lab's scripts use.

How the gripper is posed. J4 (the forearm roll) is held at settings.J4_DEG, so J2, J3 and J5
all turn about axes parallel to each other, across the arm's vertical plane. The gripper:
- points as straight down as J5 allows: straight down needs more J5 the higher it is (more
  than its 70 deg limit above about 100 mm), so above that it tips outward, keeping J5 at
  settings.J5_COMFORT_DEG;
- is turned about its own axis by J6, so its fingers close along a chosen direction.
An auger lying ACROSS the arm's reach is parallel to the J2/J3/J5 axes, so tipping the gripper
only turns the auger about its own axis: it stays level wherever the arm carries it.
"""
import math
import os
import sys

import settings as S

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(HERE), "Arm Control"))
import Up_and_Down as UD  # noqa: E402  (the lab's shared arm code: fk, moves, limits)

LIMITS = [list(lim) for lim in UD.LIMITS]  # joint limits, deg (firmware / piper_sdk)


class IKError(Exception):
    """No joint angles reach this pose inside the limits."""


# ---------------------------------------------------------------- small vector helpers
def dot(a, b):
    return sum(x * y for x, y in zip(a, b))


def add(a, b, s=1.0):
    """a + s * b"""
    return [x + s * y for x, y in zip(a, b)]


def column(R, i):
    return [R[0][i], R[1][i], R[2][i]]


def wrap180(a):
    """An angle in degrees, wrapped to (-180, 180]."""
    return -((-a + 180.0) % 360.0 - 180.0)


def wrap90(a):
    """A direction that doesn't care about its sign (a line), wrapped to (-90, 90]."""
    return -((-a + 90.0) % 180.0 - 90.0)


# ---------------------------------------------------------------- forward kinematics
def frames(q):
    """The origin of every link frame (mm, arm frame) for joint angles q (deg), base first.
    Same DH table and maths as Up_and_Down.fk, which only returns the last one."""
    T = [[1.0 if i == j else 0.0 for j in range(4)] for i in range(4)]
    out = [[0.0, 0.0, 0.0]]
    for (a, alpha, theta0, d), qi in zip(UD.DH, q):
        ca, sa = math.cos(math.radians(alpha)), math.sin(math.radians(alpha))
        ct, st = math.cos(math.radians(theta0 + qi)), math.sin(math.radians(theta0 + qi))
        link = [[ct, -st, 0, a], [st * ca, ct * ca, -sa, -sa * d],
                [st * sa, ct * sa, ca, ca * d], [0, 0, 0, 1]]
        T = [[sum(T[i][k] * link[k][j] for k in range(4)) for j in range(4)] for i in range(4)]
        out.append([T[0][3], T[1][3], T[2][3]])
    return out


def tool(q):
    """(R, tcp): the flange's rotation (columns: its x, y, z axes; z points out of the gripper)
    and the TCP, the point between the finger pads where the tube sits (settings.TCP_MM)."""
    R, flange = UD.fk(q)
    return R, add(flange, column(R, 2), S.TCP_MM)


def tcp(q):
    return tool(q)[1]


def reach_and_pitch(q):
    """(r, z, pitch) of the TCP: r is its distance out from the J1 axis along the arm's plane,
    pitch the tool axis' angle below (negative) the horizontal: -90 = straight down."""
    R, p = tool(q)
    c, s = math.cos(math.radians(q[0])), math.sin(math.radians(q[0]))
    axis = column(R, 2)
    return (p[0] * c + p[1] * s, p[2],
            math.degrees(math.atan2(axis[2], axis[0] * c + axis[1] * s)))


# The fingers' closing direction in the flange frame, from FINGERS_ALONG_REACH_J6_DEG: with
# the gripper straight down at J1 = 0 and J6 at that angle, they close along the arm's x.
def _finger_axis_in_flange():
    q = [0.0, 90.0, -50.0, S.J4_DEG, 50.0, S.FINGERS_ALONG_REACH_J6_DEG]
    q = _solve_plane(q, 280.0, 60.0, pitch=-90.0)
    R, _ = tool(q)
    return [R[0][i] for i in range(3)]  # R^T (1, 0, 0)


def finger_yaw(q):
    """Direction (deg, arm frame, as a line in (-90, 90]) of the fingers' closing line seen
    from above. The tube they hold lies at this + 90."""
    R, _ = tool(q)
    f = [dot(R[i], FINGER_AXIS) for i in range(3)]
    return wrap90(math.degrees(math.atan2(f[1], f[0])))


# ---------------------------------------------------------------- inverse kinematics
def _solve_plane(q, r, z, pitch=None, iters=60):
    """Solve J2, J3 (and J5, unless pitch is None: then J5 stays as given) so the TCP is r out
    and z up, with the tool at pitch. Newton's method on Up_and_Down.fk, numeric Jacobian."""
    q = list(q)
    joints = (1, 2) if pitch is None else (1, 2, 4)
    w = 3.0  # mm per degree of pitch error, so both errors count about the same

    def err(qq):
        rr, zz, pp = reach_and_pitch(qq)
        e = [r - rr, z - zz]
        return e if pitch is None else e + [w * (pitch - pp)]

    for _ in range(iters):
        e = err(q)
        if max(abs(v) for v in e) < 0.005:
            break
        J = []
        for j in joints:
            qh = list(q)
            qh[j] += 1e-3
            eh = err(qh)
            J.append([(a - b) / -1e-3 for a, b in zip(eh, e)])  # d(residual)/dq, negated
        dq = _lstsq(J, e)
        big = max(abs(v) for v in dq)
        if big > 10.0:
            dq = [v * 10.0 / big for v in dq]
        for j, d in zip(joints, dq):
            q[j] += d
    return q


def _lstsq(cols, e):
    """Least-squares x for sum_j x_j * cols[j] = e (2 or 3 unknowns), via the normal equations."""
    n = len(cols)
    A = [[dot(cols[i], cols[j]) + (1e-9 if i == j else 0.0) for j in range(n)] for i in range(n)]
    b = [dot(cols[i], e) for i in range(n)]
    for i in range(n):  # Gaussian elimination, n <= 3
        p = max(range(i, n), key=lambda k: abs(A[k][i]))
        A[i], A[p], b[i], b[p] = A[p], A[i], b[p], b[i]
        for k in range(i + 1, n):
            f = A[k][i] / A[i][i]
            A[k] = [x - f * y for x, y in zip(A[k], A[i])]
            b[k] -= f * b[i]
    x = [0.0] * n
    for i in reversed(range(n)):
        x[i] = (b[i] - sum(A[i][k] * x[k] for k in range(i + 1, n))) / A[i][i]
    return x


def j6_for(q, yaw):
    """The J6 (deg) inside settings.J6_RANGE_DEG that turns the fingers' closing line to yaw
    (a line: yaw and yaw + 180 are the same grasp). Raises IKError if neither fits."""
    q = list(q)
    for _ in range(8):  # turning J6 up turns the fingers clockwise seen from above
        q[5] += wrap90(finger_yaw(q) - yaw)
    lo, hi = S.J6_RANGE_DEG
    for cand in (q[5], q[5] - 180.0, q[5] + 180.0, q[5] - 360.0, q[5] + 360.0):
        if lo - 1e-6 <= cand <= hi + 1e-6:
            return cand
    raise IKError(f"the fingers need J6 = {wrap180(q[5]):.0f} (or {wrap180(q[5] + 180):.0f}), "
                  f"outside J6's window {lo:g}..{hi:g}: turn the object by about "
                  f"{wrap90(q[5] - (lo + hi) / 2):.0f} deg")


def ik(target, yaw, seed=None):
    """Joint angles (deg) that put the TCP at target (x, y, z mm, arm frame) with the fingers'
    closing line at yaw (deg), pointing as straight down as J5 allows. seed: a nearby solution
    (the previous point of a path), for speed and continuity."""
    x, y, z = target
    r = math.hypot(x, y)
    q = list(seed) if seed else [0.0, 90.0, -50.0, S.J4_DEG, 50.0, S.FINGERS_ALONG_REACH_J6_DEG]
    q[0], q[3] = math.degrees(math.atan2(y, x)), S.J4_DEG
    q = _solve_plane(q, r, z, pitch=-90.0)
    if q[4] > S.J5_COMFORT_DEG:  # straight down needs too much J5: tip outward instead
        q[4] = S.J5_COMFORT_DEG
        q = _solve_plane(q, r, z)
    rr, zz, pitch = reach_and_pitch(q)
    if math.hypot(rr - r, zz - z) > 0.5:
        raise IKError(f"can't reach r = {r:.0f} mm, z = {z:.0f} mm")
    if not -95.0 <= pitch <= -35.0:
        raise IKError(f"at r = {r:.0f} mm, z = {z:.0f} mm the gripper would point only "
                      f"{-pitch:.0f} deg below horizontal")
    q[5] = j6_for(q, yaw)
    bad = [f"J{i + 1} = {v:.1f}" for i, (v, (lo, hi)) in enumerate(zip(q, LIMITS))
           if not lo <= v <= hi]
    if bad:
        raise IKError(f"r = {r:.0f} mm, z = {z:.0f} mm needs {', '.join(bad)}: outside the "
                      "joint limits")
    return q


# ---------------------------------------------------------------- paths
def line(seed, start, end, yaw_start, yaw_end, step_mm=2.0):
    """Joint angles every step_mm along the straight line start -> end (TCP, mm), with the
    fingers' yaw turning evenly from yaw_start to yaw_end."""
    n = max(1, math.ceil(math.dist(start, end) / step_mm))
    path, q = [], seed
    for k in range(n + 1):
        s = k / n
        p = [a + s * (b - a) for a, b in zip(start, end)]
        q = ik(p, yaw_start + s * wrap90(yaw_end - yaw_start), q)
        path.append(q)
    return _continuous(path)


def swing(seed, start, end, yaw_start, yaw_end, step_mm=4.0):
    """Joint angles from start to end (TCP, mm) around the arm's base: the angle about J1,
    the reach and the height all change evenly, as the base turns. For carrying."""
    a0, a1 = (math.atan2(p[1], p[0]) for p in (start, end))
    r0, r1 = (math.hypot(p[0], p[1]) for p in (start, end))
    length = math.hypot(abs(a1 - a0) * max(r0, r1), r1 - r0, end[2] - start[2])
    n = max(1, math.ceil(length / step_mm))
    path, q = [], seed
    for k in range(n + 1):
        s = k / n
        a, r = a0 + s * (a1 - a0), r0 + s * (r1 - r0)
        p = [r * math.cos(a), r * math.sin(a), start[2] + s * (end[2] - start[2])]
        q = ik(p, yaw_start + s * wrap90(yaw_end - yaw_start), q)
        path.append(q)
    return _continuous(path)


def joint_line(q0, q1, n=60):
    """The straight line in joint space, as Up_and_Down.move streams it (for checking)."""
    return [[a + k / n * (b - a) for a, b in zip(q0, q1)] for k in range(n + 1)]


def _continuous(path, max_jump_deg=6.0):
    for a, b in zip(path, path[1:]):
        jump = max(abs(x - y) for x, y in zip(a, b))
        if jump > max_jump_deg:
            raise IKError(f"the path jumps {jump:.0f} deg between two points (J6 reached the "
                          "end of its window?)")
    return path


# ---------------------------------------------------------------- safety checks
def body_points(q, carried=None):
    """Points along the arm (shoulder to fingertips) to keep clear, and along the auger if
    carried is given (see auger_points). (name, point) pairs, mm, arm frame."""
    f = frames(q)  # 0 base, 1 J1, 2 J2 (shoulder), 3 elbow, 4 forearm, 5 wrist, 6 flange
    R, flange = UD.fk(q)
    tip = add(flange, column(R, 2), S.FINGERTIP_MM)
    pts = []
    for name, a, b, n in (("upper arm", f[2], f[3], 6), ("forearm", f[3], f[5], 6),
                          ("wrist", f[5], flange, 2), ("gripper", flange, tip, 4)):
        pts += [(name, [x + k / n * (y - x) for x, y in zip(a, b)]) for k in range(n + 1)]
    if carried is not None:
        pts += [("auger", p) for p in auger_points(q, carried)]
    return pts


def auger_points(q, carried, n=6):
    """Points along the bottom of a carried auger. carried = (axis, offset): the auger's axis
    in the flange frame (a unit vector toward its gear end, fixed once it is gripped) and how
    far from the auger's middle the TCP holds it. Lowered by the gear's radius all along, so
    the check is conservative."""
    axis, offset = carried
    R, p = tool(q)
    d = [dot(R[i], axis) for i in range(3)]  # the auger's axis now, arm frame
    mid = add(p, d, -offset)
    half = S.AUGER_LENGTH_MM / 2
    low = [0.0, 0.0, -S.AUGER_GEAR_DIAMETER_MM / 2]
    return [add(add(mid, d, -half + k / n * 2 * half), low) for k in range(n + 1)]


def problems(q, carried=None, floor_mm=None):
    """What is wrong with pose q, as a list of strings (empty = fine): joint limits, J1's
    range, J6's window, J4 held, the table, the keep-out boxes."""
    out = []
    for i, (v, (lo, hi)) in enumerate(zip(q, LIMITS)):
        if not lo - 1e-6 <= v <= hi + 1e-6:
            out.append(f"J{i + 1} = {v:.1f} is outside its limits {lo:g}..{hi:g}")
    lo, hi = S.J1_RANGE_DEG
    if not lo - 1e-6 <= q[0] <= hi + 1e-6:
        out.append(f"J1 = {q[0]:.1f} is outside J1_RANGE_DEG {lo:g}..{hi:g}")
    lo, hi = S.J6_RANGE_DEG
    if not lo - 1e-6 <= q[5] <= hi + 1e-6:
        out.append(f"J6 = {q[5]:.1f} is outside J6_RANGE_DEG {lo:g}..{hi:g}")
    floor = S.TABLE_CLEARANCE_MM if floor_mm is None else floor_mm
    for name, p in body_points(q, carried):
        if p[2] < floor:
            out.append(f"the {name} would be {p[2]:.0f} mm above the table (< {floor:g})")
            break
    for box, (x0, y0, z0, x1, y1, z1) in S.KEEP_OUT_BOXES.items():
        for name, p in body_points(q, carried):
            if x0 <= p[0] <= x1 and y0 <= p[1] <= y1 and z0 <= p[2] <= z1:
                out.append(f"the {name} would enter the keep-out box '{box}' at "
                           f"({p[0]:.0f}, {p[1]:.0f}, {p[2]:.0f})")
                break
    return out


def check_path(path, what, carried=None, every=1):
    """Raise IKError naming the first problem anywhere along a path of joint angles."""
    for q in path[::every] + [path[-1]]:
        bad = problems(q, carried)
        if bad:
            raise IKError(f"{what}: {bad[0]}")


# The fingers' closing direction in the flange frame (see _finger_axis_in_flange).
FINGER_AXIS = _finger_axis_in_flange()
