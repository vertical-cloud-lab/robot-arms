"""Physics checks for the three lab-workflow scenes, run without the robot (no policy, no SDK).

    python scene_checks.py        # prints one line per check

- print_off_a1_mini: the print's bond holds a 4 N pull and breaks at 6 N, breaks under 0.06 N*m of
  twist; the magnetic sheet holds 12 N lifting its front edge.
- auger_swap: a 15 N straight pull leaves both clips shut; peeling (cap end up about the front
  clip) opens the back clip and then the front one; the old auger rests in the rack's empty slot;
  the new auger pressed down from above snaps into both clips and the task scores a success.
- atomizer_charge: cups released over the annulus, up to 2.5 mm off its centre line, slide onto
  the crucible floor upright, and four of them score a success.

Bodies are moved kinematically (their free joint set each physics step) or pushed with
xfrc_applied; the success check is piper_sim's own.
"""

from __future__ import annotations

import math
import os

import mujoco
import numpy as np

os.environ.setdefault("PIPER_SIM_DIR", "/tmp/amp-piper/model-checks")
import piper_sim as ps  # noqa: E402


def body(a, name):
    b = mujoco.mj_name2id(a.m, mujoco.mjtObj.mjOBJ_BODY, name)
    j = a.m.body_jntadr[b]
    return b, a.m.jnt_qposadr[j], a.m.jnt_dofadr[j]


def park(a, n=1):
    for _ in range(n):
        a.apply(np.r_[ps.Q_HOME, 0.0])


def push(a, name, wrench, steps=30, point=None):
    """Ramp an external wrench on a body over half the steps, holding it after."""
    b, _, _ = body(a, name)
    ext = np.zeros(6)
    for k in range(steps):
        a.d.xfrc_applied[b] -= ext
        w = np.asarray(wrench, float) * min(1.0, (k + 1) / (steps / 2))
        if point is not None:     # a force at a point offset from the body origin
            w = np.r_[w[:3], np.cross(point, w[:3])]
        ext = w
        a.d.xfrc_applied[b] += ext
        park(a)
    a.d.xfrc_applied[b] -= ext


def teleport(a, name, poses):
    _, qa, da = body(a, name)
    for pos, quat in poses:
        a.d.qpos[qa:qa + 3], a.d.qpos[qa + 3:qa + 7], a.d.qvel[da:da + 6] = pos, quat, 0
        a._step()


def quat_mul(p, q):
    out = np.zeros(4)
    mujoco.mju_mulQuat(out, p, q)
    return out


def ry(th):
    return np.array([math.cos(th / 2), 0, math.sin(th / 2), 0])


def main() -> None:
    a = ps.PiperAdapter(seed=0)
    rows = []

    # --- print_off_a1_mini
    for label, w, expect_broken in [("pull 4 N", (0, 0, 4, 0, 0, 0), False),
                                    ("pull 6 N", (0, 0, 6, 0, 0, 0), True),
                                    ("twist 0.06 N*m", (0, 0, 0, 0, 0, 0.06), True),
                                    ("rock 0.08 N*m", (0, 0, 0, 0.08, 0, 0), False)]:
        a.load("print_off_a1_mini")
        a.reset(0)
        push(a, "print", w)
        rows.append(("print bond, " + label, (not a._bond_on) == expect_broken,
                     "broke" if not a._bond_on else "held"))
    a.load("print_off_a1_mini")
    a.reset(0)
    b, _, _ = body(a, "build_plate")
    push(a, "build_plate", (0, 0, 12, 0, 0, 0), point=np.array([ps.A1_PLATE[0], 0, 0]))
    tilt = math.degrees(math.acos(min(1.0, a.d.xmat[b][8])))
    rows.append(("plate, 12 N up at its front edge", tilt < 1.0, f"tilt {tilt:.1f} deg"))

    # --- auger_swap
    a.load("auger_swap")
    a.reset(0)
    b, _, _ = body(a, "auger_old")
    push(a, "auger_old", (0, 0, 15, 0, 0, 0))          # at its centre of mass, between the clips
    rows.append(("auger, 15 N straight pull", a._clip_on == [True, True], f"clips shut {a._clip_on}"))

    a.load("auger_swap")
    a.reset(0)
    x_out, yd, h = a.meta["doser"]
    b, qa, _ = body(a, "auger_old")
    piv = np.array([x_out - 0.059, yd, h - ps.AUG_R])      # the front clip's inner lower edge
    p0, q0 = a.d.qpos[qa:qa + 3].copy(), a.d.qpos[qa + 3:qa + 7].copy()
    poses = []
    for th in np.linspace(0, math.radians(40), 1500):
        R = np.array([[math.cos(th), 0, math.sin(th)], [0, 1, 0], [-math.sin(th), 0, math.cos(th)]])
        poses.append((piv + R @ (p0 - piv), quat_mul(ry(th), q0)))
    teleport(a, "auger_old", poses)
    opened = [e["event"] for e in a.events if "opened" in e["event"]]
    rows.append(("auger, peel 40 deg about the front clip", opened[:2] == ["clip1 opened", "clip0 opened"],
                 ", ".join(f"{e['event']} at {e.get('force_N')} N" for e in a.events[:3])))
    rx, ry_, rh = a.meta["rack_slot"]
    teleport(a, "auger_old", [(np.array([rx, ry_, rh + 0.01]), q0)] * 5)
    for _ in range(300):
        a._step()
    _, qa, _ = body(a, "auger_old")
    rows.append(("auger, old one dropped onto the empty slot", abs(a.d.qpos[qa + 2] - rh) < 0.002,
                 f"axis at z {a.d.qpos[qa + 2]:.4f} (cradle {rh})"))
    _, qn, _ = body(a, "auger_new")
    qn0 = a.d.qpos[qn + 3:qn + 7].copy()
    teleport(a, "auger_new", [(np.array([x_out, yd, h + 0.03 - 0.0315 * i / 3000]), qn0)
                              for i in range(3000)])
    for _ in range(500):
        a._step()
    ok, _ = a.success()
    rows.append(("auger, new one pressed in from above", ok,
                 ", ".join(e["event"] for e in a.events[-4:]) + f"; success() {ok}"))

    # --- atomizer_charge
    a.load("atomizer_charge")
    a.reset(0)
    xc, yc, floor, rim = a.meta["crucible"]
    res = []
    for k, (ang, off) in enumerate([(0, 0.0), (90, 0.0012), (180, -0.0012), (270, 0.0025)]):
        b, qa, da = body(a, f"cup{k}")
        r = 0.0174 + off
        a.d.qpos[qa:qa + 3] = [xc + r * math.cos(math.radians(ang)),
                               yc + r * math.sin(math.radians(ang)), rim + 0.005]
        a.d.qpos[qa + 3:qa + 7], a.d.qvel[da:da + 6] = [1, 0, 0, 0], 0
        mujoco.mj_forward(a.m, a.d)
        for _ in range(600):
            a._step()
        res.append(f"{1000 * (a.d.xpos[b][2] - floor):.1f}")
    ok, _ = a.success()
    rows.append(("cups, released over the annulus", ok, f"bottoms above floor (mm): {res}; success() {ok}"))

    for name, ok, detail in rows:
        print(f"{'PASS' if ok else 'FAIL'}  {name:44s} {detail}")


if __name__ == "__main__":
    main()
