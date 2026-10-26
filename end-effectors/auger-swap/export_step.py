"""STEP files of the auger-swap study, in the powder doser's frame (mm), for Onshape.

    python export_step.py            # -> cad/*.step (+ a bounding-box check of each)

* ``doser_compliant_clips.step``: the doser as placed by powder-doser's ``layout.py``, with
  the two bolted split clamps replaced by the compliant funnel clips, plus the finger
  fixture, the auger rack (three fresh augers) and the disposal bin.
* ``s1_two_servo_tool.step``, ``s2_one_servo_wheel_tool.step``: the custom tools seated on
  the doser, carriage down and hook closed around the tube (the moment before lift-out).
* ``alt_a_sleeves_pin.step``, ``alt_b_sleeves.step``: a simplified stock PiPER gripper
  (block body, finger blocks from the URDF's sizes) with the slip-on sleeves closed on the
  tube behind the rear clip; A adds the tilt-lock pin, pushed in.
"""
from __future__ import annotations

import math
import sys
from pathlib import Path

import cadquery as cq
import numpy as np
from OCP.gp import gp_Trsf

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import geometry as G  # noqa: E402
import scene as S  # noqa: E402

OUT = HERE / "cad"

GREY, LIGHT, WHITE = (0.70, 0.72, 0.75), (0.82, 0.83, 0.85), (0.97, 0.97, 0.97)
COLOURS = {
    "Baseplate": (0.93, 0.70, 0.20), "Mounting plate": (0.62, 0.64, 0.68),
    "Servo MG996R (+X)": (0.15, 0.30, 0.75), "Servo MG996R (-X)": (0.15, 0.30, 0.75),
    "Solenoid (Adafruit 412)": (0.80, 0.50, 0.15), "Tap collar": WHITE,
}
RED, GREEN, DGREEN, BLUE, STEEL, ORANGE = ((0.85, 0.22, 0.20), (0.10, 0.62, 0.35), (0.05, 0.40, 0.22),
                                           (0.15, 0.30, 0.75), (0.55, 0.57, 0.60), (0.95, 0.60, 0.10))


def loc(M: np.ndarray) -> cq.Location:
    tr = gp_Trsf()
    tr.SetValues(*M[0, :4], *M[1, :4], *M[2, :4])
    return cq.Location(tr)


def solid(wp) -> cq.Shape:
    vals = wp.vals() if isinstance(wp, cq.Workplane) else [wp]
    return vals[0] if len(vals) == 1 else cq.Compound.makeCompound(vals)


def T(t=(0, 0, 0), R=None):
    return S.T(t, R)


def Rx(deg):
    return S.T(R=S.rot((1, 0, 0), deg))


def Ry(deg):
    return S.T(R=S.rot((0, 1, 0), deg))


def link(a, b) -> np.ndarray:
    """Rigid frame at a whose +Z points at b (for a rod of length |b - a|)."""
    a, b = np.asarray(a, float), np.asarray(b, float)
    z = (b - a) / np.linalg.norm(b - a)
    x = np.cross([0.0, 1.0, 0.0], z)
    if np.linalg.norm(x) < 1e-6:
        x = np.array([1.0, 0, 0])
    x /= np.linalg.norm(x)
    y = np.cross(z, x)
    M = np.eye(4)
    M[:3, 0], M[:3, 1], M[:3, 2], M[:3, 3] = x, y, z, a
    return M


def save(assy: cq.Assembly, name: str) -> Path:
    OUT.mkdir(exist_ok=True)
    p = OUT / name
    assy.export(str(p))
    shp = cq.importers.importStep(str(p))
    bb = cq.Compound.makeCompound(shp.vals()).BoundingBox()
    print(f"{name}: {len(shp.vals())} solid(s), {p.stat().st_size / 1e6:.1f} MB, "
          f"x[{bb.xmin:.0f},{bb.xmax:.0f}] y[{bb.ymin:.0f},{bb.ymax:.0f}] z[{bb.zmin:.0f},{bb.zmax:.0f}]")
    return p


# ----------------------------------------------------------- Onshape-friendly versions of parts
# geometry.py draws arcs as polylines (fine for the meshes in the GIFs); for Onshape the clip
# arms and the hook are rebuilt with true arcs, and the fixed frame gets two 2 mm pads where
# the legs meet the housing so the solid has no knife-edge contact with the carriage pocket
# (Onshape's translator turned that version into a sheet body).
def _pol(r, deg):
    return (r * math.cos(math.radians(deg)), r * math.sin(math.radians(deg)))


def clip_half_arcs(side: int) -> cq.Workplane:
    ro, ri = G.CLIP_RI + G.CLIP_T, G.CLIP_RI
    lip = 90 - G.MOUTH_HALF_DEG
    mid = (lip - 90) / 2
    d = (math.sin(math.radians(G.FLARE_DEG)), math.cos(math.radians(G.FLARE_DEG)))
    t_out, t_in = _pol(ro, lip), (G.CLIP_MOUTH / 2, G.LIP_Z)
    wp = (cq.Workplane("XZ").moveTo(0, -ro).threePointArc(_pol(ro, mid), t_out)
          .lineTo(t_out[0] + G.FLARE_LEN * d[0], t_out[1] + G.FLARE_LEN * d[1])
          .lineTo(t_in[0] + G.FLARE_LEN * d[0], t_in[1] + G.FLARE_LEN * d[1])
          .lineTo(*t_in).threePointArc(_pol(ri, mid), (0, -ri)).close()
          .extrude(G.CLIP_W / 2, both=True))
    return wp if side > 0 else wp.mirror("YZ")


def hook_arcs() -> cq.Workplane:
    a0, a1 = G.HOOK_ARC
    am = (a0 + a1) / 2
    arc = (cq.Workplane("XZ").moveTo(*_pol(G.HOOK_RO, a0)).threePointArc(_pol(G.HOOK_RO, am), _pol(G.HOOK_RO, a1))
           .lineTo(*_pol(G.HOOK_RI, a1)).threePointArc(_pol(G.HOOK_RI, am), _pol(G.HOOK_RI, a0)).close()
           .extrude(G.JAW_W / 2, both=True))
    px, pz = G.HOOK_PIVOT
    top = _pol(G.HOOK_RO, a0)
    arm = (cq.Workplane("XZ").polyline([(top[0] - 4.5, top[1] - 2), (px - 4, pz), (px + 4, pz),
                                        (top[0] + 0.5, top[1] - 4)]).close()
           .extrude(G.JAW_W / 2, both=True))
    boss = cq.Workplane("XZ").center(px, pz).circle(5).extrude(G.JAW_W / 2, both=True)
    return arc.union(arm).union(boss)


def frame_solid(kind: str) -> cq.Workplane:
    hb = 90.0 - G.FLANGE_Z
    gy = G.GRIP_Y
    pad_a = (cq.Workplane("XY").box(18, 134.4 - 128.9 + 2, 2, centered=False)
             .translate((-42, 128.9 - gy - 2, hb - 2)))
    pad_b = (cq.Workplane("XY").box(12, 171.0 - 152.0, 2, centered=False)
             .translate((24, 152.0 - gy, hb - 2)))
    return G.fixed_frame(kind).union(pad_a).union(pad_b)


# --------------------------------------------------------------------------------------- doser
def doser() -> Path:
    L = S.doser_layout()
    place = L.placements()
    a = cq.Assembly(name="Doser + compliant clips + finger fixture")
    shapes = {}
    for name, (rel, M) in place.items():
        if name.startswith("Bracket"):
            continue                              # old bolted split clamps: replaced by the clips
        if rel not in shapes:
            shapes[rel] = solid(cq.importers.importStep(str(S.doser_step(rel))))
        a.add(shapes[rel], name=name, loc=loc(M), color=cq.Color(*COLOURS.get(name, GREY)))
    base, cp, cn = solid(G.clip_base()), solid(clip_half_arcs(+1)), solid(clip_half_arcs(-1))
    for tag, y in zip(("front", "rear"), G.CLIP_ROWS_Y):
        M = T((0, y, G.AXIS_Z))
        a.add(base, name=f"Compliant clip ({tag}) base", loc=loc(M), color=cq.Color(*WHITE))
        a.add(cp, name=f"Compliant clip ({tag}) arm +X", loc=loc(M), color=cq.Color(*WHITE))
        a.add(cn, name=f"Compliant clip ({tag}) arm -X", loc=loc(M), color=cq.Color(*WHITE))
    a.add(solid(G.finger_fixture()), name="Finger fixture (tap-collar stripper)", color=cq.Color(0.40, 0.62, 0.86))
    a.add(solid(G.auger_rack()), name="Auger rack (fresh augers)", color=cq.Color(0.55, 0.45, 0.35))
    a.add(solid(G.disposal_bin()), name="Disposal bin", color=cq.Color(0.80, 0.80, 0.82))
    # the three fresh augers share one sub-assembly, so the STEP stores the threaded auger once
    fresh = cq.Assembly(name="Fresh auger")
    fresh.add(shapes["fusion-step/auger.step"], name="Fresh auger tube", loc=loc(place["Auger"][1]),
              color=cq.Color(0.70, 0.86, 0.98))
    fresh.add(shapes["fusion-step/auger-cap.step"], name="Fresh auger cap", loc=loc(place["Auger cap"][1]),
              color=cq.Color(0.70, 0.86, 0.98))
    for j, x in enumerate(G.RACK_X):
        D = T((x, G.RACK_OUTLET_Y - G.OUTLET_Y, G.RACK_AXIS_Z - G.AXIS_Z))
        a.add(fresh, name=f"Fresh auger {j + 1}", loc=loc(D))
    return save(a, "doser_compliant_clips.step")


# ----------------------------------------------------------------------------- custom tools
def custom_tool(kind: str) -> Path:
    E = T((0, G.GRIP_Y, G.FLANGE_Z))
    C = E @ T((0, 0, G.HOOK_Z))                   # carriage down (s = STROKE), hook centre on the axis
    px, pz = G.HOOK_PIVOT
    title = "S1 two-servo tool" if kind == "s1" else "S2 one-servo wheel tool"
    a = cq.Assembly(name=title)
    a.add(solid(G.flange_adapter()), name="PiPER flange adapter", loc=loc(E), color=cq.Color(*STEEL))
    a.add(solid(frame_solid(kind)), name="Fixed frame + legs (reaction)", loc=loc(E), color=cq.Color(*RED))
    a.add(solid(G.carriage()), name="Jaw carriage + thin finger", loc=loc(C), color=cq.Color(*DGREEN))
    a.add(solid(hook_arcs()), name="Hook jaw (closed)", loc=loc(C), color=cq.Color(*GREEN))
    if kind == "s1":
        a.add(solid(G.servo_box()), name="Servo 1 (lift, MG996R size)", loc=loc(E @ T((30, 0, -40)) @ Rx(-90)),
              color=cq.Color(*BLUE))
        a.add(solid(G.gear_disc(9.0, 6.0, 18)), name="Lift pinion", loc=loc(E @ T((12, 8, -40)) @ Rx(-90)),
              color=cq.Color(*STEEL))
        a.add(solid(G.rack_bar()), name="Lift rack", loc=loc(C @ T((0, 12, G.CARRIAGE_TOP - 2))), color=cq.Color(*STEEL))
        a.add(solid(G.micro_servo()), name="Servo 2 (hook, micro)", loc=loc(C @ T((px, -16, pz)) @ Rx(-90)),
              color=cq.Color(*BLUE))
        return save(a, "s1_two_servo_tool.step")
    W = E @ T((0, G.WHEEL_Y, G.WHEEL_Z))
    Wc = W @ Ry(90)                               # crank pin (wheel +X) at bottom dead centre
    a.add(solid(G.wheel()), name="Wheel (crank pin + face cam)", loc=loc(Wc), color=cq.Color(*ORANGE))
    a.add(solid(G.gear_disc(10.0, 5.0, 20)), name="Wheel gear 20T", loc=loc(W @ T((0, -5, 0)) @ Rx(90)),
          color=cq.Color(*STEEL))
    a.add(solid(G.gear_disc(20.0, 5.0, 40)), name="Servo gear 40T (2:1 up)", loc=loc(W @ T((30, -5, 0)) @ Rx(90)),
          color=cq.Color(*STEEL))
    a.add(solid(G.servo_box()), name="Servo (only actuator)", loc=loc(W @ T((30, 12, 0)) @ Rx(90)), color=cq.Color(*BLUE))
    a.add(solid(G.carriage_ear()), name="Carriage ear", loc=loc(C), color=cq.Color(*DGREEN))
    pin_w = (Wc @ np.array([G.CRANK_R, 2.0, 0.0, 1.0]))[:3]
    pin_c = (C @ np.array([0.0, G.WHEEL_Y + 4, G.CARRIAGE_TOP - 2.5, 1.0]))[:3]
    n = float(np.linalg.norm(pin_w - pin_c))
    a.add(solid(G.rod(n, 2.0)), name="Connecting rod", loc=loc(link(pin_c, pin_w)), color=cq.Color(*STEEL))
    return save(a, "s2_one_servo_wheel_tool.step")


# ---------------------------------------------------------------------------- stock gripper
def stock_gripper(with_pin: bool) -> Path:
    Gf = T((0, G.STOCK_GRIP_Y, G.AXIS_Z + G.SLEEVE_TUBE_Z), S.R_TOOL_G)
    d = 16.4                                      # finger travel with the sleeves closed on the tube
    title = "Alt A sleeves + tilt-lock pin" if with_pin else "Alt B sleeves"
    a = cq.Assembly(name=title)
    flange = cq.Workplane("XY").circle(17.5).extrude(-4)
    body = cq.Workplane("XY").box(70.5, 145, 63, centered=False).translate((-40, -72.5, 0))
    a.add(solid(flange), name="PiPER J6 flange", loc=loc(Gf), color=cq.Color(*STEEL))
    a.add(solid(body), name="Stock gripper body (simplified)", loc=loc(Gf), color=cq.Color(*LIGHT))
    for side, nm in ((-1, "link7"), (1, "link8")):
        y0 = d if side > 0 else -d - 26.5
        f = cq.Workplane("XY").box(56, 26.5, 76.5, centered=False).translate((-28, y0, 59.3))
        a.add(solid(f), name=f"Stock finger {nm} (simplified)", loc=loc(Gf), color=cq.Color(*LIGHT))
    a.add(solid(G.sleeve(+1)), name="Sleeve (finger link7)", loc=loc(Gf), color=cq.Color(*GREEN))
    a.add(solid(G.sleeve(-1)), name="Sleeve (finger link8)", loc=loc(Gf), color=cq.Color(*GREEN))
    if with_pin:
        a.add(solid(G.pin_housing()), name="Tilt-lock pin housing", color=cq.Color(*RED))
        a.add(solid(G.pin()), name="Tilt-lock pin (pushed in)", loc=loc(T((G.PIN_X_IN, G.PIN_Y, G.PIN_Z))),
              color=cq.Color(*RED))
        return save(a, "alt_a_sleeves_pin.step")
    return save(a, "alt_b_sleeves.step")


def main() -> None:
    doser()
    custom_tool("s1")
    custom_tool("s2")
    stock_gripper(True)
    stock_gripper(False)


if __name__ == "__main__":
    main()
