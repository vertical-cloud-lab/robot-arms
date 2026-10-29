"""STEP files of the auger-swap study, in the powder doser's frame (mm), for Onshape.

    python export_step.py            # -> cad/*.step (+ a bounding-box check of each)

* ``doser_compliant_clips.step``: the doser as placed by powder-doser's ``layout.py``, with
  the two bolted split clamps replaced by the compliant funnel clips, plus the finger
  fixture, the auger rack (three fresh augers) and the disposal bin.
* ``s1_two_servo_tool.step``, ``s2_one_servo_wheel_tool.step``: the custom tools seated on
  the doser, carriage down and hook closed around the tube (the moment before lift-out).
* ``alt_a_sleeves_pin.step``, ``alt_a_custom_fingers_pin.step``, ``alt_b_sleeves.step``: the
  two-shell sleeves or the custom fingers closed on the tube behind the rear clip (AgileX's
  gripper itself goes to a separate reference STEP); the Alt A files add the tilt-lock
  slider, pushed in, and its guide.
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
import agilex as AGX  # noqa: E402
import geometry as G  # noqa: E402
import hifi as H  # noqa: E402
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
    a.add(solid(H.finger_fixture_hifi()), name="Finger fixture (tap-collar nest, two forks)", color=cq.Color(0.40, 0.62, 0.86))
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


# ------------------------------------------------- high fidelity: stock gripper with sleeves / custom fingers
BLUE, GREEN2, ORANGE2, BRASS, DARK = ((0.20, 0.45, 0.95), (0.20, 0.70, 0.30), (0.95, 0.55, 0.10),
                                      (0.85, 0.75, 0.30), (0.20, 0.20, 0.22))


def gripper_world(axis_base_z: float, at=(0.0, None, None)) -> np.ndarray:
    """gripper_base (= link6) in W with its cradles on the doser's tube at STOCK_GRIP_Y."""
    return T((at[0], G.STOCK_GRIP_Y if at[1] is None else at[1], (G.AXIS_Z if at[2] is None else at[2]) + axis_base_z),
             S.R_TOOL_G)


def _pin(a: cq.Assembly) -> None:
    a.add(solid(H.pin_guide()), name="Tilt-lock slider guide (printed)", color=cq.Color(*RED))
    a.add(solid(H.pin_slider(deflect=H.latch_numbers()["deflection"])), name="Tilt-lock slider, Ø25 knob + latch (printed, pushed in)",
          loc=loc(T((H.PIN_X_IN, H.PIN_Y, 0.0))), color=cq.Color(0.98, 0.45, 0.35))


def hifi_stock(kind: str) -> Path:
    """alt_a: two-shell sleeves on the stock fingers; alt_a_cf: custom fingers. Only our parts go
    in the committed STEP; agilex_reference() writes AgileX's gripper at the same pose."""
    sleeves = kind != "alt_a_cf"
    zb = H.sleeve_axis_base_z() if sleeves else H.custom_axis_base_z()
    D = H.sleeve_opening() if sleeves else H.custom_opening()
    B = gripper_world(zb) @ AGX.step_to_base()
    dz = AGX.finger_shift(D)
    up, lo = B @ T((0, 0, dz)), B @ AGX.lower_of() @ T((0, 0, dz))
    title = {"alt_a": "Alt A two-shell sleeves + tilt-lock pin", "alt_a_cf": "Alt A custom fingers + tilt-lock pin",
             "alt_b": "Alt B two-shell sleeves (doser servos hold)"}[kind]
    a = cq.Assembly(name=title)
    if sleeves:
        blue, green = solid(H.sleeve_main_shell()), solid(H.sleeve_fixing_shell())
        hw = H.sleeve_hardware()
        for tag, M in (("finger +", up), ("finger -", lo)):
            a.add(blue, name=f"Sleeve main shell ({tag})", loc=loc(M), color=cq.Color(*BLUE))
            a.add(green, name=f"Sleeve fixing shell ({tag})", loc=loc(M), color=cq.Color(*GREEN2))
            for i, (n, h) in enumerate(hw):
                a.add(solid(h), name=f"{n} {tag} #{i // 2 + 1}", loc=loc(M), color=cq.Color(*BRASS))
    else:
        cf = solid(H.custom_finger())
        hw = H.custom_finger_hardware()
        for tag, M in (("+", up), ("-", lo)):
            a.add(cf, name=f"Custom finger ({tag})", loc=loc(M), color=cq.Color(*ORANGE2))
            for i, (n, h) in enumerate(hw):
                a.add(solid(h), name=f"{n} {tag} #{i + 1}", loc=loc(M), color=cq.Color(*BRASS))
    if kind != "alt_b":
        _pin(a)
    return save(a, {"alt_a": "alt_a_sleeves_pin.step", "alt_a_cf": "alt_a_custom_fingers_pin.step",
                    "alt_b": "alt_b_sleeves.step"}[kind])


def agilex_reference(kind: str) -> Path:
    """AgileX's gripper at the pose hifi_stock(kind) uses (not committed: no licence on it)."""
    sleeves = kind == "alt_a"
    zb = H.sleeve_axis_base_z() if sleeves else H.custom_axis_base_z()
    D = H.sleeve_opening() if sleeves else H.custom_opening()
    B = gripper_world(zb) @ AGX.step_to_base()
    dz = AGX.finger_shift(D)
    sol = AGX.solids()
    a = cq.Assembly(name="AgileX PiPER gripper (reference, AgileX's STEP)")
    names = {0: "motor housing", 1: "linear rail", 2: "finger plate", 3: "back cover", 4: "flange"}
    for i, n in names.items():
        a.add(sol[i], name=f"AgileX {n}", loc=loc(B), color=cq.Color(*DARK))
    keep = {5: "carriage +", 8: "spacer +", 9: "carriage -", 12: "spacer -"}
    if sleeves:
        keep.update({6: "pad +", 7: "finger +", 10: "pad -", 11: "finger -"})
    for i, n in keep.items():
        sgn = 1 if n.endswith("+") else -1
        a.add(sol[i], name=f"AgileX {n}", loc=loc(B @ T((0, 0, sgn * dz))), color=cq.Color(*(STEEL if "carriage" in n or "spacer" in n else DARK)))
    return save(a, f"agilex_gripper_ref_{kind}.step")


PRINTED = {   # STL name -> builder (each in its own print-friendly frame as built)
    "finger_fixture": lambda: H.finger_fixture_hifi(),
    "sleeve_main_shell_x2": lambda: H.sleeve_main_shell(),
    "sleeve_fixing_shell_x2": lambda: H.sleeve_fixing_shell(),
    "custom_finger_x2": lambda: H.custom_finger(),
    "pin_guide": lambda: H.pin_guide(),
    "pin_slider": lambda: H.pin_slider().rotate((0, 0, 0), (1, 0, 0), 90).translate((0, 0, H.KNOB_LEN / 2)),   # knob end down, bar on supports
}


def stls() -> None:
    import trimesh
    d = OUT / "stl"
    d.mkdir(parents=True, exist_ok=True)
    for n, b in PRINTED.items():
        p = d / f"{n}.stl"
        part = cq.Workplane().add(solid(b()).clean())
        for tol, ang in ((0.05, 0.15), (0.02, 0.1), (0.01, 0.05)):   # finer until the mesh is closed
            cq.exporters.export(part, str(p), tolerance=tol, angularTolerance=ang)
            m = trimesh.load(str(p))
            if m.is_watertight:
                break
        print(f"{p.name}: {p.stat().st_size / 1e6:.2f} MB, {m.volume / 1e3:.2f} cm3, watertight {m.is_watertight} (tolerance {tol})")


def main() -> None:
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("what", nargs="*", default=["doser", "s1", "s2", "alt_a", "alt_a_cf", "alt_b", "stl"])
    w = set(ap.parse_args().what)
    if "doser" in w:
        doser()
    if "s1" in w:
        import s1_tool
        s1_tool.export_step(OUT / "s1_two_servo_tool.step")
    if "s2" in w:
        custom_tool("s2")
    for k in ("alt_a", "alt_a_cf"):
        if k in w:
            hifi_stock(k)
            agilex_reference(k)
    if "alt_b" in w:
        hifi_stock("alt_b")
    if "stl" in w:
        stls()


if __name__ == "__main__":
    main()
