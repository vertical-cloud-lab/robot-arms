"""Fit checks for the low finger fixture and the tilt-lock slider (issue #42, round 3).

    python fit_check.py          # about 3 min; prints interference volumes and gaps

* the fixture against the tap collar, solenoid and auger lying in it, and the gear's gap;
* each tool holding the tube in the fixture (Strategy 1 with its carriage down, Strategy 2's
  round-1 frame at wheel 200 deg, the sleeves, the custom fingers): the lowest point above
  the board, and any overlap with the fixture;
* the slider, in and out, against the doser (plate, clips, baseplate) and the guide;
* the gripper on the knob, in and out, with the sleeves or the custom fingers, against the
  slider, the guide, the doser and the board.

The latch's bump overlaps the guide's roof by its 1.05 mm deflection when the slider is in;
that is the beam bending, so it is reported but expected.
"""
from __future__ import annotations

import sys
from pathlib import Path

import cadquery as cq
import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import agilex as AGX  # noqa: E402
import geometry as G  # noqa: E402
import hifi as H  # noqa: E402
import scene as S  # noqa: E402
from export_step import gripper_world, loc  # noqa: E402
from s1_tool import _common_volume, _min_dist, posed_parts, solid_of  # noqa: E402

FIX = S.T((G.FIX_X, 0.0, G.FIX_AXIS_Z - G.AXIS_Z))      # an auger lying in the fixture
BOARD = cq.Solid.makeBox(900, 900, 20, pnt=cq.Vector(-400, -100, -20))
KNOB_GRIP_Y = {"sleeves": H.knob_grip_y(True), "custom": H.knob_grip_y(False)}   # gripper centre on the knob


def doser(names, M=np.eye(4)):
    L = S.doser_layout()
    P = L.placements()
    out = []
    for n in names:
        rel, Mp = P[n]
        out.append((n, solid_of(cq.importers.importStep(str(S.doser_step(rel)))).moved(loc(M @ Mp))))
    return out


def clips():
    out = []
    for tag, y in zip(("front", "rear"), G.CLIP_ROWS_Y):
        M = S.T((0, y, G.AXIS_Z))
        for nm, wp in (("base", G.clip_base()), ("arm +X", G.clip_half(+1)), ("arm -X", G.clip_half(-1))):
            out.append((f"clip ({tag}) {nm}", solid_of(wp).moved(loc(M))))
    return out


def gripper(kind: str, at) -> list:
    """AgileX gripper (+ sleeves or custom fingers) with its cradles closed on a Ø25 axis
    along Y at `at` (W), as in export_step.hifi_stock."""
    sleeves = kind == "sleeves"
    zb = H.sleeve_axis_base_z() if sleeves else H.custom_axis_base_z()
    D = H.sleeve_opening() if sleeves else H.custom_opening()
    B = gripper_world(zb, at) @ AGX.step_to_base()
    dz = AGX.finger_shift(D)
    up, lo = B @ S.T((0, 0, dz)), B @ AGX.lower_of() @ S.T((0, 0, dz))
    sol = AGX.solids()
    out = [(f"AgileX body {i}", sol[i].moved(loc(B))) for i in AGX.BODY]
    out += [(f"AgileX {i}", sol[i].moved(loc(B @ S.T((0, 0, dz))))) for i in (5, 8)]
    out += [(f"AgileX {i}", sol[i].moved(loc(B @ S.T((0, 0, -dz))))) for i in (9, 12)]
    if sleeves:
        out += [(f"AgileX finger {i}", sol[i].moved(loc(B @ S.T((0, 0, dz))))) for i in (6, 7)]
        out += [(f"AgileX finger {i}", sol[i].moved(loc(B @ S.T((0, 0, -dz))))) for i in (10, 11)]
        parts = [("main shell", H.sleeve_main_shell()), ("fixing shell", H.sleeve_fixing_shell())]
    else:
        parts = [("custom finger", H.custom_finger())]
    for n, wp in parts:
        out += [(f"{n} +", solid_of(wp).moved(loc(up))), (f"{n} -", solid_of(wp).moved(loc(lo)))]
    return out


def hits(a_list, b_list, tag):
    n = 0
    for na, a in a_list:
        for nb, b in b_list:
            v = _common_volume(a, b)
            if v > 1e-3 or v != v:
                print(f"    {tag}: {na} x {nb}: {v:.2f} mm^3")
                n += 1
    return n


def lowest(parts):
    return min(p.BoundingBox().zmin for _, p in parts)


def main():
    fixture = [("fixture", solid_of(H.finger_fixture_hifi()))]
    lying = doser(["Tap collar", "Solenoid (Adafruit 412)", "Auger", "Auger cap"], FIX)
    print("[fixture] collar, solenoid, auger lying in it:", hits(fixture, lying, "fixture"), "interference(s)")
    for n, s in lying:
        print(f"    gap to {n}: {_min_dist(fixture[0][1], s):.2f} mm")

    # Strategy 1 holding the tube in the fixture, carriage down (s = STROKE), hook closed
    for dy, tag in ((0.0, "in the fixture"), (80.0, "after the strip")):
        E = S.T((G.FIX_X, G.GRIP_Y + dy, G.FIX_AXIS_Z - G.HOOK_Z))
        s1 = [(n, solid_of(wp).moved(loc(M))) for n, wp, c, M, grp in posed_parts(G.STROKE, 0.0, E)]
        print(f"[S1 {tag}] lowest point z = {lowest(s1):.2f} mm above the board;",
              hits(s1, fixture + [("board", BOARD)], "S1"), "interference(s)")
    # Strategy 2 (round-1 frame): wheel at 200 deg, carriage 26.8 mm down, hook closed
    import animate as AN
    s, th = AN.wheel_state(200.0)
    E = S.T((G.FIX_X, G.GRIP_Y, G.FIX_AXIS_Z - (G.HOOK_Z + G.STROKE - s)))
    s2 = [("S2 frame", solid_of(G.fixed_frame("s2")).moved(loc(E)))]
    print(f"[S2 in the fixture] s = {s:.2f}, hook {th:.0f} deg; frame's lowest point z = {lowest(s2):.2f};",
          hits(s2, fixture, "S2"), "interference(s)")
    # stock gripper holding the tube behind the rear clip, tube in the fixture
    for kind in ("sleeves", "custom"):
        g = gripper(kind, (G.FIX_X, G.STOCK_GRIP_Y, G.FIX_AXIS_Z))
        print(f"[{kind} in the fixture] lowest point z = {lowest(g):.2f};",
              hits(g, fixture + [("board", BOARD)], kind), "interference(s)")

    # slider in / out
    guide = [("guide", solid_of(H.pin_guide()))]
    plate = doser(["Mounting plate", "Baseplate", "Servo pinion (+X)", "Servo MG996R (+X)"]) + clips()
    slider = solid_of(H.pin_slider())
    print("[guide] against the doser:", hits(guide, plate, "guide"), "interference(s)")
    for x, tag in ((H.PIN_X_IN, "in"), (H.PIN_X_OUT, "out (latched)")):
        sl = [("slider", slider.moved(loc(S.T((x, H.PIN_Y, 0.0)))))]
        print(f"[slider {tag}] doser:", hits(sl, plate, "slider"), "| guide:", hits(sl, guide, "slider"), "interference(s)")
        d = _min_dist(sl[0][1], plate[0][1])
        print(f"    gap to the mounting plate {d:.2f} mm")
        for kind in ("sleeves", "custom"):
            at = (x + H.KNOB_U, KNOB_GRIP_Y[kind], H.BAR_Z)
            g = gripper(kind, at)
            n = hits(g, sl + guide + plate + [("board", BOARD)], f"{kind} on the knob")
            dk = min(_min_dist(p, sl[0][1]) for nm, p in g if "shell" in nm or "custom" in nm)
            print(f"    {kind} on the knob (gripper y {at[1]:.1f}): {n} interference(s); "
                  f"lowest point z = {lowest(g):.2f}; cradles to the slider {dk:.2f} mm")
    print("latch:", {k: round(v, 4) for k, v in H.latch_numbers().items()})


if __name__ == "__main__":
    main()
