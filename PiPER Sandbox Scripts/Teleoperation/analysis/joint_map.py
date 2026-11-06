#!/usr/bin/env python3
"""Which PiPER joint has no SO-101 counterpart, and how the other five map (issue #46).

Compares the two arms' kinematic chains and writes joint_map.json and joint_map.png next to
this file. Nothing here talks to an arm.

    python joint_map.py

- PiPER: the modified DH table from piper_sdk's C_PiperForwardKinematics (dh_is_offset=1,
  firmware S-V1.6-3 and later), the same table piper_pick_tape.py uses (#19).
- SO-101: TheRobotStudio's so101_new_calib.urdf, the URDF that matches LeRobot's calibration
  (zero = the middle of each joint's range). It is fetched at run time, pinned by commit and
  checked by sha256, and cached in .cache/ (gitignored).

The nominal map below assumes LeRobot's degrees mode reads like the URDF. The real offsets and
signs still have to be checked on the arms before anything moves.
"""
import hashlib
import json
import math
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent

URDF_URL = ("https://raw.githubusercontent.com/TheRobotStudio/SO-ARM100/"
            "385e8d7c68e24945df6c60d9bd68837a4b7411ae/Simulation/SO101/so101_new_calib.urdf")
URDF_SHA256 = "3a65d2d35e68a8d2f0c2cc176d19b884506543c93ba72980145b80abe276022c"

# PiPER, modified DH (mm, rad), from piper_sdk.kinematics.C_PiperForwardKinematics
DH_A = [0, 0, 285.03, -21.98, 0, 0]
DH_ALPHA = [0, -math.pi / 2, 0, math.pi / 2, -math.pi / 2, math.pi / 2]
DH_THETA = [0, -math.radians(172.22), -math.radians(102.78), 0, 0, 0]
DH_D = [123, 0, 0, 250.75, 0, 91]
PIPER_LIMITS_DEG = [(-150, 150), (0, 180), (-170, 0), (-100, 100), (-70, 70), (-120, 120)]
PIPER_TCP_MM = 150.0  # flange to fingertips, piper_pick_tape.py's default

SO_JOINTS = ["shoulder_pan", "shoulder_lift", "elbow_flex", "wrist_flex", "wrist_roll"]
# Which PiPER joint (1-based) each SO-101 joint drives. J4 has no SO-101 joint.
SO_TO_PIPER = {"shoulder_pan": 1, "shoulder_lift": 2, "elbow_flex": 3, "wrist_flex": 5,
               "wrist_roll": 6}
PIPER_TYPE = ["yaw", "pitch", "pitch", "roll", "pitch", "roll"]
SO_TYPE = ["yaw", "pitch", "pitch", "pitch", "roll"]


# ---------------------------------------------------------------- PiPER
def link_tf(alpha, a, theta, d):
    ca, sa, ct, st = math.cos(alpha), math.sin(alpha), math.cos(theta), math.sin(theta)
    return np.array([[ct, -st, 0, a], [st * ca, ct * ca, -sa, -sa * d],
                     [st * sa, ct * sa, ca, ca * d], [0, 0, 0, 1]])


def piper_frames(q_deg):
    """4x4 transforms of PiPER frames 1..6 in the base frame, mm. Joint i turns about z_i."""
    T, out = np.eye(4), []
    for i in range(6):
        T = T @ link_tf(DH_ALPHA[i], DH_A[i], math.radians(q_deg[i]) + DH_THETA[i], DH_D[i])
        out.append(T.copy())
    return out


def piper_points(q_deg):
    """Base, shoulder, elbow, wrist centre, flange, fingertips (mm), and the frames."""
    F = piper_frames(q_deg)
    tip = F[5][:3, 3] + PIPER_TCP_MM * F[5][:3, 2]
    pts = [np.zeros(3), F[1][:3, 3], F[2][:3, 3], F[4][:3, 3], F[5][:3, 3], tip]
    return pts, F


# ---------------------------------------------------------------- SO-101
def fetch_urdf():
    cache = HERE / ".cache" / "so101_new_calib.urdf"
    if not cache.exists():
        cache.parent.mkdir(exist_ok=True)
        with urllib.request.urlopen(URDF_URL, timeout=60) as r:
            cache.write_bytes(r.read())
    data = cache.read_bytes()
    if hashlib.sha256(data).hexdigest() != URDF_SHA256:
        raise SystemExit(f"{cache} does not match the pinned sha256; delete it and re-run")
    return cache


def rpy_matrix(r, p, y):
    cr, sr, cp, sp, cy, sy = (math.cos(r), math.sin(r), math.cos(p), math.sin(p),
                              math.cos(y), math.sin(y))
    Rx = np.array([[1, 0, 0], [0, cr, -sr], [0, sr, cr]])
    Ry = np.array([[cp, 0, sp], [0, 1, 0], [-sp, 0, cp]])
    Rz = np.array([[cy, -sy, 0], [sy, cy, 0], [0, 0, 1]])
    return Rz @ Ry @ Rx


def axis_angle(axis, theta):
    k = np.asarray(axis, float) / np.linalg.norm(axis)
    K = np.array([[0, -k[2], k[1]], [k[2], 0, -k[0]], [-k[1], k[0], 0]])
    return np.eye(3) + math.sin(theta) * K + (1 - math.cos(theta)) * K @ K


class SO101:
    def __init__(self, path):
        self.joints = {}
        for j in ET.parse(path).getroot().findall("joint"):
            o, a, lim = j.find("origin"), j.find("axis"), j.find("limit")
            self.joints[j.get("name")] = {
                "type": j.get("type"),
                "parent": j.find("parent").get("link"),
                "child": j.find("child").get("link"),
                "xyz": [float(v) for v in (o.get("xyz") if o is not None else "0 0 0").split()],
                "rpy": [float(v) for v in (o.get("rpy") if o is not None else "0 0 0").split()],
                "axis": [float(v) for v in (a.get("xyz") if a is not None else "0 0 1").split()],
                "limit_deg": (math.degrees(float(lim.get("lower"))),
                              math.degrees(float(lim.get("upper"))))
                if lim is not None and lim.get("lower") else None,
            }
        self.by_child = {j["child"]: n for n, j in self.joints.items()}

    def fk(self, q_deg, link="gripper_frame_link"):
        """End transform (mm) and each revolute joint's (world axis, world origin in mm)."""
        names, child = [], link
        while child in self.by_child:
            names.append(self.by_child[child])
            child = self.joints[names[-1]]["parent"]
        T, axes = np.eye(4), {}
        for n in reversed(names):
            j = self.joints[n]
            To = np.eye(4)
            To[:3, :3], To[:3, 3] = rpy_matrix(*j["rpy"]), j["xyz"]
            T = T @ To
            if j["type"] in ("revolute", "continuous"):
                axes[n] = (T[:3, :3] @ np.array(j["axis"]), T[:3, 3] * 1000)
                R = np.eye(4)
                R[:3, :3] = axis_angle(j["axis"], math.radians(q_deg.get(n, 0.0)))
                T = T @ R
        T = T.copy()
        T[:3, 3] *= 1000
        return T, axes

    def points(self, q_deg):
        """Foot of the pan axis, shoulder, elbow, wrist, roll joint, gripper frame (mm)."""
        T, ax = self.fk(q_deg)
        foot = ax["shoulder_pan"][1] * np.array([1.0, 1.0, 0.0])
        return [foot] + [ax[n][1] for n in SO_JOINTS[1:]] + [T[:3, 3]], ax


# ---------------------------------------------------------------- analysis
def unit(v):
    return v / np.linalg.norm(v)


def angle_deg(a, b):
    return math.degrees(math.acos(min(1.0, abs(float(np.dot(unit(a), unit(b)))))))


def structure(so):
    """Angles between joint axes over random poses: which axes stay parallel."""
    rng = np.random.default_rng(46)
    so_rows, piper_rows = [], []
    for _ in range(200):
        q = {n: rng.uniform(-60, 60) for n in SO_JOINTS}
        _, ax = so.fk(q)
        z = {n: ax[n][0] for n in SO_JOINTS}
        so_rows.append([angle_deg(z["shoulder_lift"], z["elbow_flex"]),
                        angle_deg(z["shoulder_lift"], z["wrist_flex"]),
                        angle_deg(z["wrist_flex"], z["wrist_roll"])])
        qp = [rng.uniform(lo + 5, hi - 5) for lo, hi in PIPER_LIMITS_DEG]
        z4 = [f[:3, 2] for f in piper_frames(qp)]
        qp[3] = 0.0
        z0 = [f[:3, 2] for f in piper_frames(qp)]
        piper_rows.append([angle_deg(z0[1], z0[2]), angle_deg(z0[1], z0[4]),
                           angle_deg(z4[1], z4[4])])
    so_max, piper_max = np.max(so_rows, axis=0), np.max(piper_rows, axis=0)
    piper_min = np.min(piper_rows, axis=0)
    return {
        "so101_max_angle_deg": {"shoulder_lift_vs_elbow_flex": round(so_max[0], 3),
                                "shoulder_lift_vs_wrist_flex": round(so_max[1], 3),
                                "wrist_flex_vs_wrist_roll": round(so_max[2], 3)},
        "piper_max_angle_deg": {"J2_vs_J3": round(piper_max[0], 3),
                                "J2_vs_J5_with_J4_at_0": round(piper_max[1], 3),
                                "J2_vs_J5_with_J4_free_max": round(piper_max[2], 3),
                                "J2_vs_J5_with_J4_free_min": round(piper_min[2], 3)},
    }


def so_links(p, ax):
    """SO-101 upper arm, forearm and hand. The hand is taken along the roll axis: the URDF's
    gripper frame sits about 7 deg off it, so it would swing as the wrist rolls."""
    return [p[2] - p[1], p[3] - p[2], -ax["wrist_roll"][0]]


def piper_links(pp, F):
    """PiPER upper arm, forearm (to the wrist centre) and hand (along J6)."""
    return [pp[2] - pp[1], pp[3] - pp[2], F[5][:3, 2]]


def link_pitches(vectors, forward):
    """Angles of upper arm, forearm and hand above the horizontal, in the arm plane (deg)."""
    up = np.array([0.0, 0.0, 1.0])
    return [math.degrees(math.atan2(float(np.dot(v, up)), float(np.dot(v, forward))))
            for v in vectors]


def nominal_map(so):
    """Signs and offsets so that PiPER joint = sign * SO-101 joint + offset (deg)."""
    q0 = {n: 0.0 for n in SO_JOINTS}
    p, ax = so.points(q0)
    fwd = unit(np.array([p[5][0], p[5][1], 0.0]))
    so_pitch = link_pitches(so_links(p, ax), fwd)
    pp, F = piper_points([0, 0, 0, 0, 0, 0])
    piper_pitch = link_pitches(piper_links(pp, F), np.array([1.0, 0, 0]))
    # Both arms' pitch joints turn their links the same way (checked numerically below), so
    # each link's angle is (link angle at zero) - (sum of the pitch joints before it).
    j2 = piper_pitch[0] - so_pitch[0]
    j3 = (piper_pitch[1] - so_pitch[1]) - j2
    j5 = (piper_pitch[2] - so_pitch[2]) - j2 - j3
    # Yaw: the SO-101 pan axis points down and the PiPER J1 axis up, so the signs differ.
    # Roll: the SO-101 roll axis points back along the hand and PiPER J6 out along it.
    hand = unit(p[5] - p[3])
    roll_sign = -1 if np.dot(unit(ax["wrist_roll"][0]), hand) < 0 else 1
    pan_sign = -1 if np.dot(unit(ax["shoulder_pan"][0]), F[0][:3, 2]) < 0 else 1
    return {
        "shoulder_pan": {"piper": "J1", "sign": pan_sign, "offset_deg": 0.0},
        "shoulder_lift": {"piper": "J2", "sign": 1, "offset_deg": round(j2, 1)},
        "elbow_flex": {"piper": "J3", "sign": 1, "offset_deg": round(j3, 1)},
        "(none)": {"piper": "J4", "sign": 0, "offset_deg": 0.0},
        "wrist_flex": {"piper": "J5", "sign": 1, "offset_deg": round(j5, 1)},
        "wrist_roll": {"piper": "J6", "sign": roll_sign, "offset_deg": 0.0},
    }


def to_piper(q_so, m):
    q = [0.0] * 6
    for n in SO_JOINTS:
        e = m[n]
        q[int(e["piper"][1]) - 1] = e["sign"] * q_so[n] + e["offset_deg"]
    return q


def forward(pitch_axis, sign):
    """Horizontal 'forward' of an arm plane, from its (horizontal) pitch axis."""
    v = sign * np.cross(pitch_axis, [0.0, 0.0, 1.0])
    return unit(np.array([v[0], v[1], 0.0]))


def check_map(so, m):
    """Over random poses inside both arms' limits, the worst difference between the arms in
    heading (J1) and in the angles of the upper arm, forearm and hand in the arm plane."""
    zero_so = {n: 0.0 for n in SO_JOINTS}
    s_so = 1 if forward(so.fk(zero_so)[1]["shoulder_lift"][0], 1)[0] > 0 else -1
    s_pi = 1 if forward(piper_frames([0] * 6)[1][:3, 2], 1)[0] > 0 else -1
    rng = np.random.default_rng(1)
    worst, n_ok = [0.0, 0.0, 0.0, 0.0], 0
    while n_ok < 300:
        q = {n: rng.uniform(*so.joints[n]["limit_deg"]) for n in SO_JOINTS}
        qp = to_piper(q, m)
        if not all(lo <= v <= hi for v, (lo, hi) in zip(qp, PIPER_LIMITS_DEG)):
            continue
        n_ok += 1
        sp, sax = so.points(q)
        pp, F = piper_points(qp)
        f_so = forward(sax["shoulder_lift"][0], s_so)
        f_pi = forward(F[1][:3, 2], s_pi)
        heading = math.degrees(math.atan2(f_so[1], f_so[0]) - math.atan2(f_pi[1], f_pi[0]))
        worst[3] = max(worst[3], abs((heading + 180) % 360 - 180))
        a_so = link_pitches(so_links(sp, sax), f_so)
        a_pi = link_pitches(piper_links(pp, F), f_pi)
        for k in range(3):
            worst[k] = max(worst[k], abs((a_so[k] - a_pi[k] + 180) % 360 - 180))
    return {"poses": n_ok, "worst_heading_deg": round(worst[3], 2),
            "worst_upper_arm_deg": round(worst[0], 2), "worst_forearm_deg": round(worst[1], 2),
            "worst_hand_deg": round(worst[2], 2)}


def ranges(so, m):
    out = {}
    for n in SO_JOINTS:
        lo, hi = so.joints[n]["limit_deg"]
        e = m[n]
        a, b = sorted([e["sign"] * lo + e["offset_deg"], e["sign"] * hi + e["offset_deg"]])
        plo, phi = PIPER_LIMITS_DEG[int(e["piper"][1]) - 1]
        usable = max(0.0, min(b, phi) - max(a, plo))
        out[n] = {"so101_range_deg": [round(lo, 1), round(hi, 1)],
                  "maps_to": e["piper"], "mapped_range_deg": [round(a, 1), round(b, 1)],
                  "piper_limits_deg": [plo, phi],
                  "share_of_so101_range_usable": round(usable / (hi - lo), 2),
                  "piper_range_unreachable_from_leader_deg": round((phi - plo) - usable, 1)}
    return out


def link_lengths(so):
    p, _ = so.points({n: 0.0 for n in SO_JOINTS})
    pp, _ = piper_points([0, 90, -90, 0, 0, 0])
    d = lambda a, b: round(float(np.linalg.norm(a - b)), 1)
    return {"so101_mm": {"upper_arm": d(p[1], p[2]), "forearm": d(p[2], p[3]),
                         "wrist_to_gripper_frame": d(p[3], p[5])},
            "piper_mm": {"upper_arm": d(pp[1], pp[2]), "forearm_to_wrist_centre": d(pp[2], pp[3]),
                         "wrist_centre_to_fingertips": d(pp[3], pp[5])}}


# ---------------------------------------------------------------- figure
SURFACE, INK, INK2, MUTED = "#fcfcfb", "#0b0b0b", "#52514e", "#8a8984"
TYPE_COLOR = {"yaw": "#2a78d6", "pitch": "#eb6834", "roll": "#1baf7a", "locked": "#8a8984"}


def ring(ax, centre, axis, r, color, dashed=False, lw=2.0):
    k = unit(axis)
    a = unit(np.cross(k, [0, 0, 1.0]) if abs(k[2]) < 0.9 else np.cross(k, [1.0, 0, 0]))
    b = np.cross(k, a)
    t = np.linspace(0, 2 * math.pi, 60)
    pts = centre[:, None] + r * (np.outer(a, np.cos(t)) + np.outer(b, np.sin(t)))
    ax.plot(*pts, color=color, lw=lw, ls=(0, (3, 2)) if dashed else "-")


def axis_bar(ax, origin, axis, half, color, lw=4.0):
    k = unit(axis)
    p = np.array([origin - half * k, origin + half * k]).T
    ax.plot(*p, color=color, lw=lw, solid_capstyle="round")


def label(ax, p, text, dx=0.0, dy=0.0, dz=0.0, color=INK, **kw):
    ax.text(p[0] + dx, p[1] + dy, p[2] + dz, text, fontsize=8.5, color=color, **kw)


def setup(ax, pts, title, pad):
    pts = np.array(pts)
    lo, hi = pts.min(axis=0) - pad, pts.max(axis=0) + pad
    lo[2] = 0.0
    ax.set_xlim(lo[0], hi[0]); ax.set_ylim(lo[1], hi[1]); ax.set_zlim(lo[2], hi[2])
    ax.set_box_aspect(hi - lo)
    ax.set_title(title, fontsize=11, color=INK, loc="left", pad=2)
    ax.set_facecolor(SURFACE)
    for a in (ax.xaxis, ax.yaxis, ax.zaxis):
        a.set_pane_color((0.97, 0.97, 0.96, 1.0))
        a.line.set_color(MUTED)
        a._axinfo["grid"]["color"] = (0.85, 0.85, 0.83, 1.0)
        a._axinfo["grid"]["linewidth"] = 0.5
    ax.tick_params(colors=MUTED, labelsize=7, pad=0)
    ax.set_xlabel("x (mm)", fontsize=7.5, color=INK2, labelpad=-4)
    ax.set_ylabel("y (mm)", fontsize=7.5, color=INK2, labelpad=-4)
    ax.set_zlabel("z (mm)", fontsize=7.5, color=INK2, labelpad=-4)


def draw_floor(ax, xy_lo, xy_hi):
    xs = [xy_lo[0], xy_hi[0], xy_hi[0], xy_lo[0], xy_lo[0]]
    ys = [xy_lo[1], xy_lo[1], xy_hi[1], xy_hi[1], xy_lo[1]]
    ax.plot(xs, ys, [0] * 5, color=MUTED, lw=0.6)


def tool_directions(q_pi, j4, j5):
    """Tool axis of the PiPER for joints q_pi with J4 and J5 replaced: (tilt out of the arm
    plane, elevation above the horizontal), deg."""
    q = list(q_pi)
    q[3], q[4] = j4, j5
    F = piper_frames(q)
    d, n = F[5][:3, 2], unit(F[1][:3, 2])  # tool axis; J2's axis is the arm plane's normal
    return (math.degrees(math.asin(float(np.clip(np.dot(d, n), -1, 1)))),
            math.degrees(math.asin(float(np.clip(d[2], -1, 1)))))


def figure(so, m, q_so, out_png):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.lines import Line2D
    from matplotlib.patches import Patch

    q_pi = to_piper(q_so, m)
    fig = plt.figure(figsize=(15.5, 6.0), dpi=150, facecolor=SURFACE)
    gs = fig.add_gridspec(1, 4, width_ratios=[1.15, 1.0, 0.07, 0.85], left=0.01, right=0.985,
                          top=0.93, bottom=0.17, wspace=0.06)
    view = dict(elev=18, azim=-72)

    # ---- PiPER
    ax = fig.add_subplot(gs[0], projection="3d")
    pp, F = piper_points(q_pi)
    ax.plot(*np.array(pp).T, color=INK2, lw=3.0, solid_capstyle="round")
    ax.scatter(*np.array(pp[1:5]).T, s=18, color=INK2, depthshade=False)
    axis_bar(ax, pp[1] + np.array([0, 0, -70.0]), F[0][:3, 2], 45, TYPE_COLOR["yaw"])
    axis_bar(ax, pp[1], F[1][:3, 2], 70, TYPE_COLOR["pitch"])
    axis_bar(ax, pp[2], F[2][:3, 2], 70, TYPE_COLOR["pitch"])
    fore_mid = pp[2] + 0.45 * (pp[3] - pp[2])
    ring(ax, fore_mid, pp[3] - pp[2], 42, TYPE_COLOR["locked"], dashed=True, lw=2.4)
    axis_bar(ax, pp[3], F[4][:3, 2], 60, TYPE_COLOR["pitch"])
    ring(ax, pp[4] + 0.35 * (pp[5] - pp[4]), pp[5] - pp[4], 32, TYPE_COLOR["roll"])
    label(ax, pp[1], "J1 yaw", dz=-120, dy=-30, ha="right")
    label(ax, pp[1], "J2 pitch", dz=20, dy=-80, ha="right")
    label(ax, pp[2], "J3 pitch", dz=45, dy=-25, ha="right")
    label(ax, fore_mid, "J4 forearm roll:\nno SO-101 joint,\nheld at 0\u00b0", dz=-150,
          ha="center", color=INK2)
    label(ax, pp[3], "J5 pitch", dz=60, dy=40)
    label(ax, pp[5], "J6 roll", dz=-30, dy=30)
    setup(ax, pp, "AgileX PiPER: 6 joints + gripper", 70)
    draw_floor(ax, ax.get_xlim()[:1] + ax.get_ylim()[:1], ax.get_xlim()[1:] + ax.get_ylim()[1:])
    ax.view_init(**view)

    # ---- SO-101
    ax = fig.add_subplot(gs[1], projection="3d")
    sp, sax = so.points(q_so)
    ax.plot(*np.array(sp).T, color=INK2, lw=3.0, solid_capstyle="round")
    ax.scatter(*np.array(sp[1:5]).T, s=18, color=INK2, depthshade=False)
    axis_bar(ax, sp[1] + np.array([0, 0, -45.0]), sax["shoulder_pan"][0], 25, TYPE_COLOR["yaw"])
    axis_bar(ax, sp[1], sax["shoulder_lift"][0], 30, TYPE_COLOR["pitch"])
    axis_bar(ax, sp[2], sax["elbow_flex"][0], 30, TYPE_COLOR["pitch"])
    axis_bar(ax, sp[3], sax["wrist_flex"][0], 26, TYPE_COLOR["pitch"])
    ring(ax, sp[4] + 0.3 * (sp[5] - sp[4]), sp[5] - sp[4], 14, TYPE_COLOR["roll"])
    label(ax, sp[1], "shoulder_pan \u2192 J1", dz=-50, dy=-12, ha="right")
    label(ax, sp[1], "shoulder_lift \u2192 J2", dz=8, dy=-34, ha="right")
    label(ax, sp[2], "elbow_flex \u2192 J3", dz=24, ha="center")
    label(ax, sp[3], "wrist_flex \u2192 J5", dz=24, dy=16)
    label(ax, sp[5], "wrist_roll \u2192 J6", dz=-14, dy=14)
    setup(ax, sp, "SO-101 leader, matching pose: 5 joints + gripper", 30)
    draw_floor(ax, ax.get_xlim()[:1] + ax.get_ylim()[:1], ax.get_xlim()[1:] + ax.get_ylim()[1:])
    ax.view_init(**view)

    # ---- what J4 adds: the directions the gripper can point, at this wrist position
    ax = fig.add_subplot(gs[3])
    ax.set_facecolor(SURFACE)
    phi = np.linspace(0, 360, 361)
    edge = np.array([tool_directions(q_pi, p - 90, 70) if p <= 180 else
                     tool_directions(q_pi, p - 270, -70) for p in phi])
    ax.fill(edge[:, 0], edge[:, 1], color="#e4e3df", lw=0)
    ax.plot(edge[:, 0], edge[:, 1], color=MUTED, lw=1.0)
    line = np.array([tool_directions(q_pi, 0, j5) for j5 in np.linspace(-70, 70, 141)])
    ax.plot(line[:, 0], line[:, 1], color=TYPE_COLOR["pitch"], lw=3.0, solid_capstyle="round")
    for (x, y, txt, ha, dx, dy) in [
            (0, -90, "straight down: kept", "left", 6, 2),
            (0, 0, "level, in line\nwith the arm: kept", "right", -5, 3),
            (45, -10, "tilted 45\u00b0 sideways:\nneeds J4", "center", 0, -24)]:
        kept = x == 0
        ax.plot([x], [y], marker="o", ms=7, color=TYPE_COLOR["pitch"] if kept else INK2,
                markeredgecolor=SURFACE, markeredgewidth=1.5, zorder=5)
        ax.text(x + dx, y + dy, txt, fontsize=8.5, color=INK, ha=ha, va="bottom")
    ax.text(-66, 30, "J4 free: anywhere\nin the grey patch", fontsize=8.5, color=INK2)
    ax.text(4, 20, "J4 held at 0\u00b0:\nonly this line (J5)", fontsize=8.5, color=INK)
    ax.set_xlim(-75, 75)
    ax.set_ylim(-100, 55)
    ax.set_xticks(range(-60, 61, 30))
    ax.set_yticks(range(-90, 46, 30))
    ax.grid(color="#e4e3df", lw=0.6)
    ax.set_axisbelow(True)
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    for s in ("left", "bottom"):
        ax.spines[s].set_color(MUTED)
    ax.tick_params(colors=INK2, labelsize=8)
    ax.set_xlabel("gripper tilt out of the arm's vertical plane (\u00b0)", fontsize=9, color=INK2)
    ax.set_ylabel("gripper elevation (\u00b0, \u221290 = pointing straight down)", fontsize=9,
                  color=INK2)
    ax.set_title("Where the gripper can point from this wrist position", fontsize=11, color=INK,
                 loc="left")
    ax.set_aspect("equal")

    handles = [Line2D([], [], color=TYPE_COLOR["yaw"], lw=4, label="yaw joint"),
               Line2D([], [], color=TYPE_COLOR["pitch"], lw=4, label="pitch joint"),
               Line2D([], [], color=TYPE_COLOR["roll"], lw=4, label="roll joint"),
               Line2D([], [], color=TYPE_COLOR["locked"], lw=2.4, ls=(0, (3, 2)),
                      label="PiPER J4, no SO-101 counterpart"),
               Patch(facecolor="#e4e3df", edgecolor=MUTED, label="reachable only with J4")]
    fig.legend(handles=handles, loc="lower center", ncol=5, frameon=False, fontsize=9,
               labelcolor=INK, bbox_to_anchor=(0.5, 0.0))
    pose = ", ".join(f"{n} {q_so[n]:+.0f}\u00b0" for n in SO_JOINTS)
    fig.text(0.5, 0.065, f"SO-101 pose (LeRobot degrees): {pose}.   PiPER pose from the nominal "
             "map: " + ", ".join(f"J{i + 1} {v:+.0f}\u00b0" for i, v in enumerate(q_pi))
             + ".   Each arm is drawn to its own scale.", ha="center", fontsize=8.5, color=INK2)
    fig.savefig(out_png, facecolor=SURFACE)
    plt.close(fig)


def main():
    so = SO101(fetch_urdf())
    m = nominal_map(so)
    q_so = {"shoulder_pan": 15.0, "shoulder_lift": -5.0, "elbow_flex": 25.0, "wrist_flex": 45.0,
            "wrist_roll": 0.0}
    result = {
        "piper_joint_types": dict(zip([f"J{i}" for i in range(1, 7)], PIPER_TYPE)),
        "so101_joint_types": dict(zip(SO_JOINTS, SO_TYPE)),
        "axis_check": structure(so),
        "nominal_map": m,
        "map_check": check_map(so, m),
        "ranges": ranges(so, m),
        "link_lengths": link_lengths(so),
        "figure_pose": {"so101_deg": q_so, "piper_deg": [round(v, 1) for v in to_piper(q_so, m)]},
        "sources": {"so101_urdf": URDF_URL, "so101_urdf_sha256": URDF_SHA256,
                    "piper_dh": "piper_sdk C_PiperForwardKinematics, dh_is_offset=1"},
    }
    (HERE / "joint_map.json").write_text(json.dumps(result, indent=2) + "\n")
    figure(so, m, q_so, HERE / "joint_map.png")
    print(json.dumps({k: result[k] for k in ("axis_check", "nominal_map", "map_check")}, indent=2))


if __name__ == "__main__":
    main()
