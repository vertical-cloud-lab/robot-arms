#!/usr/bin/env python3
"""Expected PiPER joint currents against pose and load, from the URDF's link masses.

Pure computation: no piper_sdk, no CAN, nothing is sent to the arm. It writes, next to itself:

    joint_currents.json           every number ../motion-monitoring.md quotes
    holding_current_vs_load.png   the highest holding current anywhere in the envelope, per joint
    holding_current_map.png       J2 and J3 holding current over the arm's vertical plane
    trip_force_map.png            force at the gripper needed to trip the scripts' current checks

    python3 joint_currents.py      # needs numpy and matplotlib; takes about a minute

What it models: the current each joint's motor needs to hold the arm still against gravity
(the static part), the extra current an acceleration adds (a lower bound, see below), and how
hard something would have to push on the gripper before a fixed per-joint current limit trips.
It doesn't model friction, the gearboxes' reflected rotor inertia, cable drag, or the
controller's own behaviour in a collision. Those are why ../motion-monitoring.md asks for a
measured baseline before any of these numbers is used as a threshold.

Inputs, and how sure each is (../README.md explains the marks):
- Link masses, centres of mass and joint frames: AgileX's piper_description.urdf
  (agilexrobotics/piper_ros, noetic branch, commit ac41fcb). A CAD estimate, not weighed on
  this arm. The URDF's chain reproduces piper_sdk's DH forward kinematics (the table in
  Up_and_Down.py) to 0.14 mm over 2000 random poses; check_against_dh() repeats that check.
- Current to torque: piper_sdk 0.6.2's fixed coefficients, 1.18125 N·m/A for J1-J3 and
  0.95844 N·m/A for J4-J6 (ArmMsgFeedbackHighSpd.cal_effort). AgileX's numbers, unchecked.
- Tooling on the gripper (the gripper Pi, the HQ camera, their mount, the finger sleeves, the
  USB-C cable): not weighed. Its mass is fitted so that the model's J5 current holding the
  gripper level at home matches the "about 1.5 A hanging free" Up_and_Down.py reports for it
  (#54), with the mass placed TOOL_M past the flange on the gripper's axis.
- Payload: a point mass TCP_M past the flange on the gripper's axis. TCP_M = 150 mm is the
  photo estimate from #19, not a measurement.
- Current limits: Up_and_Down.py and follower.py on main (commit 41a21f8).
"""
import json
import math
import os

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
G = np.array([0.0, 0.0, -9.81])

# ---------------------------------------------------------------- inputs
URDF_SOURCE = ("https://github.com/agilexrobotics/piper_ros/blob/"
               "ac41fcbcdda598f01b51cf6175ed9a24d0dacadc/src/piper_description/urdf/"
               "piper_description.urdf")
# Joint origins from the URDF: (xyz in m, rpy in rad). Every joint turns about its own z.
JOINTS = [
    ((0.0, 0.0, 0.123), (0.0, 0.0, 0.0)),
    ((0.0, 0.0, 0.0), (1.5708, -0.1359, -3.1416)),
    ((0.28503, 0.0, 0.0), (0.0, 0.0, -1.7939)),
    ((-0.021984, -0.25075, 0.0), (1.5708, 0.0, 0.0)),
    ((0.0, 0.0, 0.0), (-1.5708, 0.0, 0.0)),
    ((8.8259e-05, -0.091, 0.0), (1.5708, 0.0, 0.0)),
]
# Link masses (kg) and centres of mass (m, in the link's own frame). Link k is moved by
# joints 1..k; gripper_base is fixed to link6 (the flange).
LINKS = [
    ("link1", 1, 0.71, (0.000121504734057468, 0.000104632162460536, -0.00438597309559853)),
    ("link2", 2, 1.17, (0.198666145229743, -0.010926924140076, 0.00142121714502687)),
    ("link3", 3, 0.50, (-0.0202737662122021, -0.133914995944595, -0.000458682652737356)),
    ("link4", 4, 0.38, (-9.66635791618542e-05, 0.000876064475651083, -0.00496880904640868)),
    ("link5", 5, 0.383, (-4.10554118924211e-05, -0.0566486692356075, -0.0037205791677906)),
    ("link6", 6, 0.007, (-8.82590762930069e-05, 9.0598378529832e-06, -0.002)),
    ("gripper_base", 6, 0.45, (-0.000183807162235591, 8.05033155577911e-05, 0.0321436689908876)),
]
# The two fingers (0.025 kg each): their centres of mass, worked out in the gripper_base
# frame from the URDF's finger joints at half open. Small enough that the opening doesn't matter.
FINGERS = [(0.025, (0.00065, -0.0097 - 0.0175, 0.1358 - 0.0492)),
           (0.025, (-0.00065, 0.0097 + 0.0175, 0.1358 - 0.0492))]

K_NM_PER_A = np.array([1.18125] * 3 + [0.95844] * 3)  # piper_sdk 0.6.2, cal_effort
LIMITS_A = {  # per-joint current limits, J1..J6, on main at 41a21f8
    "Up_and_Down.py": [1.5, 3, 4, 1.5, 4.5, 1.5],
    "follower.py": [3, 7, 6, 2, 4.5, 1.5],
}
MEASURED = {  # #54, as recorded in Up_and_Down.py's help text
    "free_motion_peaks_a": [0.04, 1.1, 2.0, 0.2, 2.7, 0.45],
    "j5_holding_level_gripper_a": 1.5,
}
TCP_M = 0.150   # payload point past the flange, #19's photo estimate
TOOL_M = 0.060  # where the fitted tooling mass sits past the flange (assumed)
TOOL_OFFAXIS_M = 0.035  # how far the gripper Pi's mass may sit off J6's axis (assumed)
PAYLOADS_KG = [0.0, 0.25, 0.5, 1.0, 1.5]  # 1.5 kg is the listing's rated payload
FLOOR_M = 0.02  # poses with the elbow, wrist, flange or TCP below this height are left out
ENVELOPE_DEG = {"J1": (-150, 150), "J2": (0, 180), "J3": (-170, 0), "J4": (-90, 90),
                "J5": (-70, 70), "J6": (-180, 180)}  # J4: teleop's jog range
ACCEL_DEG_S2 = {"follower.py (--max-deg-s2)": 360.0,
                # Up_and_Down.py: a raised-cosine move of 20 deg peaking at 12 deg/s
                "Up_and_Down.py (20 deg lift at 12 deg/s)": (math.pi / (math.pi / 2 * 20 / 12)) ** 2 * 10}
HOME_DEG = [0.0, 0.0, 0.0, 0.0, 5.0, -52.0]   # J5 = +5 holds the gripper level at home
READY_DEG = [0.0, 20.0, -20.0, 0.0, 5.0, -52.0]  # follower.py's READY, wrist level

# ---------------------------------------------------------------- kinematics


def _rpy(r, p, y):
    cr, sr, cp, sp, cy, sy = (math.cos(r), math.sin(r), math.cos(p), math.sin(p),
                              math.cos(y), math.sin(y))
    return np.array([[cy * cp, cy * sp * sr - sy * cr, cy * sp * cr + sy * sr],
                     [sy * cp, sy * sp * sr + cy * cr, sy * sp * cr - cy * sr],
                     [-sp, cp * sr, cp * cr]])


ORIGINS = []
for _xyz, _r in JOINTS:
    _O = np.eye(4)
    _O[:3, :3] = _rpy(*_r)
    _O[:3, 3] = _xyz
    ORIGINS.append(_O)


def fk(q_deg):
    """q_deg (N, 6) -> joint origins (N, 6, 3), joint axes (N, 6, 3), link frames (N, 6, 4, 4).
    Base frame: x forward, y left, z up, origin on the mounting surface under J1."""
    q = np.radians(np.atleast_2d(np.asarray(q_deg, dtype=float)))
    n = len(q)
    T = np.broadcast_to(np.eye(4), (n, 4, 4)).copy()
    o, z, frames = np.zeros((n, 6, 3)), np.zeros((n, 6, 3)), np.zeros((n, 6, 4, 4))
    for i in range(6):
        T = T @ ORIGINS[i]
        o[:, i], z[:, i] = T[:, :3, 3], T[:, :3, 2]
        c, s = np.cos(q[:, i]), np.sin(q[:, i])
        R = np.zeros((n, 4, 4))
        R[:, 0, 0], R[:, 0, 1], R[:, 1, 0], R[:, 1, 1] = c, -s, s, c
        R[:, 2, 2] = R[:, 3, 3] = 1.0
        T = T @ R
        frames[:, i] = T
    return o, z, frames


def point(frames, link, p):
    """World position (N, 3) of point p given in link `link`'s frame (1-based)."""
    F = frames[:, link - 1]
    return F[:, :3, :3] @ np.asarray(p, dtype=float) + F[:, :3, 3]


def check_against_dh(n=2000):
    """Largest flange-position difference (mm) between this URDF chain and piper_sdk's DH."""
    dh = [(0, 0, 0, 123), (0, -90, -172.22, 0), (285.03, 0, -102.78, 0),
          (-21.98, 90, 0, 250.75), (0, -90, 0, 0), (0, 90, 0, 91)]
    rng = np.random.default_rng(0)
    lo = np.array([-150, 0, -170, -100, -70, -180.0])
    hi = np.array([150, 180, 0, 100, 70, 180.0])
    qs = rng.uniform(lo, hi, size=(n, 6))
    _, _, frames = fk(qs)
    worst = 0.0
    for q, F in zip(qs, frames):
        T = np.eye(4)
        for (a, al, th0, d), qi in zip(dh, q):
            ca, sa = math.cos(math.radians(al)), math.sin(math.radians(al))
            ct, st = math.cos(math.radians(th0 + qi)), math.sin(math.radians(th0 + qi))
            T = T @ np.array([[ct, -st, 0, a], [st * ca, ct * ca, -sa, -sa * d],
                              [st * sa, ct * sa, ca, ca * d], [0, 0, 0, 1]])
        worst = max(worst, float(np.linalg.norm(T[:3, 3] - F[5, :3, 3] * 1000)))
    return worst


# ---------------------------------------------------------------- statics


def masses(frames, tool_kg=0.0, payload_kg=0.0, tool_offaxis_m=0.0):
    """[(mass kg, world position (N, 3), last joint that carries it)], arm plus extras."""
    out = [(m, point(frames, link, com), link) for _, link, m, com in LINKS]
    out += [(m, point(frames, 6, com), 6) for m, com in FINGERS]
    if tool_kg:
        out.append((tool_kg, point(frames, 6, (tool_offaxis_m, 0.0, TOOL_M)), 6))
    if payload_kg:
        out.append((payload_kg, point(frames, 6, (0.0, 0.0, TCP_M)), 6))
    return out


def holding_torque(o, z, mlist):
    """Torque (N, 6) each motor must supply to hold the pose against gravity, N·m."""
    tau = np.zeros(o.shape[:2])
    for m, p, last in mlist:
        for i in range(last):
            tau[:, i] -= np.einsum("nk,nk->n", z[:, i], np.cross(p - o[:, i], m * G))
    return tau


def unit_torques(q_deg):
    """Holding torques for the bare arm, for 1 kg of tooling and for 1 kg of payload. The
    total for any load is arm + tool_kg * tool + payload_kg * payload (it's linear in mass)."""
    o, z, frames = fk(q_deg)
    arm = holding_torque(o, z, masses(frames))
    tool = holding_torque(o, z, masses(frames, tool_kg=1.0)) - arm
    pay = holding_torque(o, z, masses(frames, payload_kg=1.0)) - arm
    return arm, tool, pay, (o, z, frames)


def inertia_about_axes(o, z, mlist):
    """Point-mass inertia (N, 6) of everything each joint moves, about that joint's axis.
    Treats every link as a point at its centre of mass and leaves out the motors' reflected
    rotor inertia, so it is a lower bound."""
    inert = np.zeros(o.shape[:2])
    for m, p, last in mlist:
        for i in range(last):
            r = p - o[:, i]
            along = np.einsum("nk,nk->n", r, z[:, i])[:, None] * z[:, i]
            inert[:, i] += m * np.einsum("nk,nk->n", r - along, r - along)
    return inert


def level_j5(q_deg):
    """q_deg with J5 set so the gripper's axis is horizontal (bisection, J4 as given)."""
    q = np.array(q_deg, dtype=float)
    lo, hi = -70.0, 70.0
    for _ in range(40):
        mid = (lo + hi) / 2
        q[4] = mid
        _, _, F = fk(q)
        if F[0, 5, 2, 2] > 0:  # gripper axis pointing up: more J5 tips it down
            lo = mid
        else:
            hi = mid
    q[4] = (lo + hi) / 2
    return q


def key_heights(frames):
    """Heights (N, 4) of the elbow (J3), the wrist (J5), the flange and the TCP."""
    return np.stack([point(frames, 2, (0.28503, 0, 0))[:, 2],
                     point(frames, 4, (0, 0, 0))[:, 2], frames[:, 5, 2, 3],
                     point(frames, 6, (0, 0, TCP_M))[:, 2]], axis=1)


# ---------------------------------------------------------------- trip force


def fibonacci_sphere(n=600):
    i = np.arange(n) + 0.5
    phi = np.arccos(1 - 2 * i / n)
    th = math.pi * (1 + 5 ** 0.5) * i
    return np.stack([np.cos(th) * np.sin(phi), np.sin(th) * np.sin(phi), np.cos(phi)], axis=1)


DIRS = fibonacci_sphere()


def trip_force(o, z, frames, tau_hold, limits_a):
    """For each pose: the push at the TCP (N), in the direction that's hardest to detect,
    before any joint's current passes its limit; and the easiest direction. A joint already
    over its limit holding still gives 0 (the check would trip with no contact at all).

    A force F along unit vector u at the TCP adds J^T u * F to the gravity torque each motor
    has to hold, so joint i trips once |tau_i + a_i F| > L_i, i.e. F_i = (sign(a_i) L_i - tau_i)
    / a_i. The check trips at the smallest F_i; the hardest direction is the u that makes that
    smallest F largest."""
    tcp = point(frames, 6, (0, 0, TCP_M))
    Jv = np.cross(z, tcp[:, None, :] - o)          # (N, 6, 3): row i is z_i x (p - o_i)
    L = np.asarray(limits_a) * K_NM_PER_A          # N·m
    hardest, easiest = np.zeros(len(o)), np.zeros(len(o))
    for s in range(0, len(o), 500):                # in chunks, to keep memory small
        a = np.einsum("nik,dk->ndi", Jv[s:s + 500], DIRS)  # (n, D, 6) N·m per newton
        tau = tau_hold[s:s + 500, None, :]
        with np.errstate(divide="ignore", invalid="ignore"):
            Fi = (np.sign(a) * L - tau) / a
        Fi = np.where(np.abs(a) < 1e-9, np.inf, Fi)
        Fi = np.where(np.abs(tau) >= L, 0.0, Fi)    # already tripped holding still
        F = Fi.min(axis=2)                          # (n, D)
        hardest[s:s + 500], easiest[s:s + 500] = F.max(axis=1), F.min(axis=1)
    return hardest, easiest


# ---------------------------------------------------------------- run


def main():
    out = {"generated_by": "docs/safety/analysis/joint_currents.py",
           "inputs": {"urdf": URDF_SOURCE, "k_nm_per_a": K_NM_PER_A.tolist(),
                      "limits_a": LIMITS_A, "measured_54": MEASURED, "tcp_m": TCP_M,
                      "tool_m": TOOL_M, "payloads_kg": PAYLOADS_KG, "floor_m": FLOOR_M,
                      "envelope_deg": ENVELOPE_DEG}}
    out["urdf_vs_sdk_dh_max_mm"] = round(check_against_dh(), 3)
    print(f"URDF chain vs piper_sdk DH: {out['urdf_vs_sdk_dh_max_mm']} mm worst flange difference")

    # 1. Fit the tooling mass to the measured J5 current holding the gripper level at home.
    home = level_j5(HOME_DEG)
    arm, tool, pay, _ = unit_torques(home)
    i5_arm = abs(arm[0, 4]) / K_NM_PER_A[4]
    tool_kg = (MEASURED["j5_holding_level_gripper_a"] * K_NM_PER_A[4] - abs(arm[0, 4])) / abs(tool[0, 4])
    out["home_level_j5_deg"] = round(float(home[4]), 2)
    out["j5_level_model_bare_a"] = round(float(i5_arm), 3)
    out["tool_kg_fitted"] = round(float(tool_kg), 3)
    print(f"home, gripper level at J5 = {home[4]:.2f} deg: bare-arm model holds J5 with "
          f"{i5_arm:.2f} A against 1.5 A measured -> tooling fitted at {tool_kg:.2f} kg "
          f"{TOOL_M * 1000:.0f} mm past the flange")
    # J6 from the tooling's centre sitting off J6's axis (gripper level, worst roll)
    out["j6_offaxis_tool_a"] = round(float(tool_kg * 9.81 * TOOL_OFFAXIS_M / K_NM_PER_A[5]), 3)

    def total(arm, tool, pay, payload_kg):
        return arm + tool_kg * tool + payload_kg * pay

    # 2. Check against #54. The run went from the rest up to READY and back, so each joint's
    # peak current bounds its holding current at both poses. Where the model asks for more
    # than that, scale the joint down: these scales are upper bounds, and they are the
    # "anchored to #54" case. J5 needs none (the tooling was fitted to it); J1, J4 and J6
    # have nothing to anchor to and keep AgileX's coefficient.
    checks = {}
    for name, q in (("home (level)", home), ("READY (J2 +20, J3 -20, level)", level_j5(READY_DEG))):
        a_, t_, p_, _ = unit_torques(q)
        checks[name] = np.abs(total(a_, t_, p_, 0.0)[0]) / K_NM_PER_A
    peaks = np.array(MEASURED["free_motion_peaks_a"])
    scale = np.ones(6)
    for j in (1, 2):
        scale[j] = min(1.0, min(peaks[j] / v[j] for v in checks.values()))
    out["model_at_poses_a"] = {k: np.round(v, 3).tolist() for k, v in checks.items()}
    out["scale_to_54"] = np.round(scale, 3).tolist()
    for k, v in checks.items():
        print(f"model, tooling only, {k}: {np.round(v, 2).tolist()} A")
    print(f"#54 free-motion peaks: {peaks.tolist()} A -> scale {np.round(scale, 3).tolist()}")
    CASES = {"AgileX coefficient": K_NM_PER_A, "anchored to #54": K_NM_PER_A / scale}
    out["cases_k_nm_per_a"] = {c: np.round(k, 3).tolist() for c, k in CASES.items()}

    # 3. Sweep the envelope. J1 and J6 don't change the gravity load of an on-axis model.
    g2 = np.arange(0, 181, 5.0)
    g3 = np.arange(-170, 1, 5.0)
    g4 = np.array([-90, -45, 0, 45, 90.0])
    g5 = np.arange(-70, 71, 10.0)
    Q = np.array(np.meshgrid([0.0], g2, g3, g4, g5, [0.0], indexing="ij")).reshape(6, -1).T
    arm, tool, pay, (o, z, frames) = unit_torques(Q)
    ok = (key_heights(frames) >= FLOOR_M).all(axis=1)
    print(f"envelope sweep: {len(Q)} poses, {ok.sum()} with everything above {FLOOR_M * 1000:.0f} mm")
    sweep = {c: {} for c in CASES}
    torque = {}
    for pk in PAYLOADS_KG:
        tq = np.abs(total(arm, tool, pay, pk))[ok]
        torque[f"{pk:g}"] = {"max_nm": np.round(tq.max(axis=0), 2).tolist(),
                             "pose_of_max_deg": [Q[ok][int(tq[:, i].argmax())].round(0).tolist()
                                                 for i in range(6)]}
        for c, K in CASES.items():
            cur = tq / K
            sweep[c][f"{pk:g}"] = {
                "max_a": np.round(cur.max(axis=0), 2).tolist(),
                "share_of_poses_over_limit": {s_: np.round((cur > np.array(l)).mean(axis=0), 3).tolist()
                                              for s_, l in LIMITS_A.items()}}
        print(f"payload {pk:g} kg: max holding torque {torque[f'{pk:g}']['max_nm']} N·m; current "
              + "; ".join(f"{c} {sweep[c][f'{pk:g}']['max_a']} A" for c in CASES))
    out["envelope_max_torque"] = torque
    out["envelope_sweep"] = sweep
    out["envelope_sweep_poses"] = int(ok.sum())
    # payload sensitivity: extra holding current per kg at the fingertips, worst pose
    out["per_kg_payload_max_a"] = {c: np.round(np.abs(pay[ok]).max(axis=0) / K, 2).tolist()
                                   for c, K in CASES.items()}

    # 4. Acceleration: the extra current at each script's acceleration, worst pose. A lower
    # bound: point-mass links, no reflected rotor inertia, no friction.
    acc = {}
    for pk in (0.0, 1.5):
        inert = inertia_about_axes(o, z, masses(frames, tool_kg=tool_kg, payload_kg=pk))[ok]
        acc[f"{pk:g}"] = {"max_inertia_kgm2": np.round(inert.max(axis=0), 4).tolist()}
        for name, a in ACCEL_DEG_S2.items():
            acc[f"{pk:g}"][name] = {c: np.round(inert.max(axis=0) * math.radians(a) / K, 2).tolist()
                                    for c, K in CASES.items()}
    out["acceleration_extra_a"] = acc
    out["accel_deg_s2"] = {k: round(v, 1) for k, v in ACCEL_DEG_S2.items()}
    print("extra current from acceleration (worst pose, A):", json.dumps(acc))

    # 5. The arm's vertical plane, J1 = J4 = 0, gripper level: holding current and trip force.
    m2 = np.arange(0, 181, 2.0)
    m3 = np.arange(-170, 1, 2.0)
    grid = np.array([[0.0, a2, a3, 0.0, 0.0, -52.0] for a2 in m2 for a3 in m3])
    lo, hi = np.full(len(grid), -70.0), np.full(len(grid), 70.0)
    for _ in range(30):  # level the gripper at every pose at once (bisection on J5)
        mid = (lo + hi) / 2
        grid[:, 4] = mid
        _, _, F = fk(grid)
        up = F[:, 5, 2, 2] > 0
        lo, hi = np.where(up, mid, lo), np.where(up, hi, mid)
    grid[:, 4] = (lo + hi) / 2
    arm, tool, pay, (o, z, frames) = unit_torques(grid)
    levelled = np.abs(frames[:, 5, 2, 2]) < 0.02  # J5's range could level the gripper here
    tcp = point(frames, 6, (0, 0, TCP_M))
    valid = (key_heights(frames) >= FLOOR_M).all(axis=1) & levelled
    maps = {"poses": int(valid.sum())}
    tau0 = total(arm, tool, pay, 0.0)
    cur_maps = {pk: np.abs(total(arm, tool, pay, pk)) / CASES["anchored to #54"] for pk in (0.0, 1.5)}
    trip = {}
    for c, K in CASES.items():
        for s_, l in LIMITS_A.items():
            hard, easy = trip_force(o, z, frames, tau0, np.array(l) * K / K_NM_PER_A)
            trip[(c, s_)] = hard
            h = hard[valid]
            fin = h[np.isfinite(h)]
            maps[f"trip_force_N {c} {s_}"] = {
                "hardest_direction_median": round(float(np.median(fin)), 1),
                "hardest_p10": round(float(np.percentile(fin, 10)), 1),
                "hardest_p90": round(float(np.percentile(fin, 90)), 1),
                "share_tripped_holding_still": round(float((h == 0).mean()), 3),
                "share_hardest_over_140N": round(float((h > 140).mean()), 3),
                "easiest_direction_median": round(float(np.median(easy[valid])), 1)}
    for c, K in CASES.items():
        for pk in (0.0, 1.5):
            cur = np.abs(total(arm, tool, pay, pk))[valid] / K
            for s_, l in LIMITS_A.items():
                maps[f"share_over_limit_any_joint {c} {s_} payload {pk:g}"] = \
                    round(float((cur > np.array(l)).any(axis=1).mean()), 3)
    ready = level_j5(READY_DEG)
    a_, t_, p_, (o_, z_, f_) = unit_torques(ready)
    maps["READY_trip_force_N_hardest_easiest"] = {
        f"{c} {s_}": [round(float(v[0]), 1) for v in
                      trip_force(o_, z_, f_, total(a_, t_, p_, 0.0), np.array(l) * K / K_NM_PER_A)]
        for c, K in CASES.items() for s_, l in LIMITS_A.items()}
    maps["max_reach_level_m"] = round(float(np.hypot(tcp[:, 0], tcp[:, 1])[valid].max()), 3)
    out["vertical_plane"] = maps
    for k, v in maps.items():
        print(f"  {k}: {v}")

    with open(os.path.join(HERE, "joint_currents.json"), "w") as f:
        json.dump(out, f, indent=1)

    plot(sweep, tool_kg, tcp, valid, cur_maps, trip, m2, m3)


# ---------------------------------------------------------------- plots


def plot(sweep, tool_kg, tcp, valid, cur_maps, trip, m2, m3):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import matplotlib.tri as mtri
    from matplotlib.colors import LinearSegmentedColormap

    TEXT, TEXT2, GRID = "#191919", "#666666", "#e6e6e6"
    SERIES = {"AgileX coefficient": "#257de0", "anchored to #54": "#f47230"}
    blues = LinearSegmentedColormap.from_list(
        "seq_blue", ["#cce3fd", "#9dc8f7", "#6aabf1", "#338ced", "#2370cd", "#1757ac", "#0e3d7e"])
    plt.rcParams.update({"font.size": 10, "axes.edgecolor": TEXT2, "axes.labelcolor": TEXT,
                         "xtick.color": TEXT2, "ytick.color": TEXT2, "axes.titlecolor": TEXT,
                         "axes.spines.top": False, "axes.spines.right": False})
    styles = {"Up_and_Down.py": ":", "follower.py": "--"}

    # Figure 1: highest holding current anywhere in the envelope, against payload
    fig, axes = plt.subplots(1, 4, figsize=(14, 4.0))
    for ax, j in zip(axes, (1, 2, 3, 4)):
        top = max(l[j] for l in LIMITS_A.values())
        for c, col in SERIES.items():
            pk = [float(p) for p in sweep[c]]
            y = [sweep[c][k]["max_a"][j] for k in sweep[c]]
            top = max(top, max(y))
            ax.plot(pk, y, color=col, lw=2, marker="o", ms=7, mec="white", mew=1.5, zorder=3,
                    label=c)
        lims = {s_: l[j] for s_, l in LIMITS_A.items()}
        same = len(set(lims.values())) == 1
        for s_, v in lims.items():
            ax.axhline(v, color=TEXT2, lw=1.2, ls=styles[s_], zorder=2)
            if not same:
                ax.text(1.53, v, f"{s_} {v:g} A", va="center", ha="left", fontsize=7.5,
                        color=TEXT2)
        if same:
            ax.text(1.53, next(iter(lims.values())), f"both scripts {next(iter(lims.values())):g} A",
                    va="center", ha="left", fontsize=7.5, color=TEXT2)
        ax.set_title(f"J{j + 1}" + ("  (both cases identical)" if j in (3, 4) else ""),
                     loc="left", fontweight="bold")
        ax.set_xlabel("payload at the fingertips (kg)")
        ax.set_xlim(-0.05, 1.5)
        ax.set_ylim(0, top * 1.1)
        ax.grid(axis="y", color=GRID, lw=0.8)
        ax.set_axisbelow(True)
    axes[0].set_ylabel("highest holding current in the envelope (A)")
    axes[0].legend(loc="upper left", frameon=False, fontsize=8.5)
    fig.suptitle("Current needed just to hold still, at the worst pose in the envelope "
                 f"(model; {tool_kg:.2f} kg of tooling fitted to #54; J4 and J5 are the same in "
                 "both cases). Grey lines: the scripts' fixed limits",
                 x=0.01, ha="left", fontsize=10, color=TEXT)
    fig.tight_layout(rect=(0, 0, 0.965, 0.93))
    fig.savefig(os.path.join(HERE, "holding_current_vs_load.png"), dpi=150)
    plt.close(fig)

    # triangulate the (J2, J3) grid, drawn where the fingertips are in the vertical plane
    n3 = len(m3)
    tris = []
    for i in range(len(m2) - 1):
        for k in range(n3 - 1):
            a, b, c, d = i * n3 + k, i * n3 + k + 1, (i + 1) * n3 + k, (i + 1) * n3 + k + 1
            tris += [(a, b, c), (b, d, c)]
    tris = np.array(tris)
    tri = mtri.Triangulation(tcp[:, 0] * 1000, tcp[:, 2] * 1000,
                             triangles=tris[valid[tris].all(axis=1)])

    def frame(ax):
        ax.axhline(0, color=TEXT2, lw=1)
        ax.text(-340, 10, "mounting surface", fontsize=7.5, color=TEXT2)
        ax.plot([0], [0], marker="^", color=TEXT, ms=8)
        for q, name in ((HOME_DEG, "home"), (READY_DEG, "READY")):
            _, _, F = fk(level_j5(q))
            p = point(F, 6, (0, 0, TCP_M))[0] * 1000
            ax.plot(p[0], p[2], "o", ms=5, mfc="white", mec=TEXT, zorder=5)
            ax.annotate(name, (p[0], p[2]), xytext=(4, 4), textcoords="offset points",
                        fontsize=7.5, color=TEXT)
        ax.set_aspect("equal")
        ax.set_xlim(-350, 800)
        ax.set_ylim(-50, 820)
        ax.set_xlabel("forward from J1 (mm)")
        ax.set_ylabel("fingertip height (mm)")

    # Figure 2: J2 and J3 holding current over the vertical plane (anchored case)
    fig, axes = plt.subplots(2, 2, figsize=(11.5, 9.8))
    for r, j in enumerate((1, 2)):
        vmax = max(float(np.nanmax(cur_maps[1.5][valid][:, j])), 1.0)
        for c, pk in enumerate((0.0, 1.5)):
            ax = axes[r, c]
            v = cur_maps[pk][:, j]
            cs = ax.tricontourf(tri, v, levels=np.linspace(0, vmax, 15), cmap=blues)
            lv = sorted({l[j] for l in LIMITS_A.values()})
            lines = ax.tricontour(tri, v, levels=lv, colors=TEXT, linewidths=1.3,
                                  linestyles=["dotted", "dashed"][:len(lv)])
            ax.clabel(lines, fmt=lambda val: f"{val:g} A", fontsize=8)
            frame(ax)
            ax.set_title(f"J{j + 1}, " + ("tooling only" if pk == 0 else "tooling + 1.5 kg"),
                         loc="left", fontweight="bold")
        fig.colorbar(cs, ax=axes[r, :], shrink=0.85, label=f"J{j + 1} holding current (A)")
    fig.suptitle("Holding current over the arm's vertical plane (model anchored to #54; "
                 "gripper level, J1 = J4 = 0; each point is where the fingertips are).\n"
                 "Dotted contour: Up_and_Down.py's limit; dashed: follower.py's",
                 x=0.01, ha="left", fontsize=10, color=TEXT)
    fig.savefig(os.path.join(HERE, "holding_current_map.png"), dpi=130, bbox_inches="tight")
    plt.close(fig)

    # Figure 3: push at the fingertips needed to trip each script's current check
    oranges = plt.get_cmap("Oranges")
    fig, axes = plt.subplots(1, 2, figsize=(11.5, 5.4))
    cap = 300
    from matplotlib.patches import Patch
    for ax, s_ in zip(axes, LIMITS_A):
        hard = np.minimum(trip[("anchored to #54", s_)], cap)
        tripped = hard[tri.triangles].min(axis=1) <= 0  # over a limit with no contact at all
        t_ok = mtri.Triangulation(tri.x, tri.y, triangles=tri.triangles[~tripped])
        t_bad = mtri.Triangulation(tri.x, tri.y, triangles=tri.triangles[tripped]) if tripped.any() else None
        cs = ax.tricontourf(t_ok, hard, levels=np.linspace(0, cap, 13), cmap=oranges)
        if t_bad is not None:
            ax.tripcolor(t_bad, np.zeros(len(tri.x)), cmap=LinearSegmentedColormap.from_list(
                "grey", ["#bdbdbd", "#bdbdbd"]), shading="flat", edgecolors="none")
        frame(ax)
        ax.legend(handles=[Patch(color="#bdbdbd", label="over a limit just holding still")],
                  loc="upper left", frameon=False, fontsize=8)
        ax.set_title(f"{s_}: {', '.join(f'{v:g}' for v in LIMITS_A[s_])} A", loc="left",
                     fontweight="bold", fontsize=9.5)
    fig.colorbar(cs, ax=axes, shrink=0.85,
                 label=f"push needed to trip, hardest direction (N, capped at {cap})")
    fig.suptitle("How hard something has to push on the fingertips before a fixed current limit "
                 "trips (model anchored to #54, tooling only,\ngripper level, J1 = J4 = 0, arm "
                 "holding still)", x=0.01, ha="left", fontsize=10,
                 color=TEXT)
    fig.savefig(os.path.join(HERE, "trip_force_map.png"), dpi=130, bbox_inches="tight")
    plt.close(fig)


if __name__ == "__main__":
    main()
