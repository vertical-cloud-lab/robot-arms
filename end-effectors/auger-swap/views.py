"""Still renders of the high-fidelity parts for the README (issue #42, round 2).

    xvfb-run -a python views.py            # -> renders/view_*.png

Each part is drawn against what it fits: the fixture with the tap collar, solenoid and
auger; the sleeves and custom fingers on AgileX's gripper (fetched at run time); the
tilt-lock pin with the doser's mounting plate.
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
from export_step import loc  # noqa: E402

OUT = HERE / "renders"
GRIP, FIN, STEEL = (0.20, 0.20, 0.22), (0.11, 0.11, 0.12), (0.62, 0.64, 0.68)
BLUE, GREEN, ORANGE, BRASS, FIXTURE = (0.20, 0.45, 0.95), (0.20, 0.70, 0.30), (0.95, 0.55, 0.10), (0.85, 0.75, 0.30), (0.40, 0.62, 0.86)
TUBE = (0.70, 0.85, 0.98)


def _pv(shape, tol=0.08):
    import pyvista as pv
    if isinstance(shape, cq.Workplane):
        vals = shape.vals()
        shape = vals[0] if len(vals) == 1 else cq.Compound.makeCompound(vals)
    v, f = shape.tessellate(tol, 0.2)
    v = np.array([(p.x, p.y, p.z) for p in v])
    return pv.PolyData(v, np.hstack([np.full((len(f), 1), 3), np.array(f)]).ravel())


def render(items, views, out: Path, size=(640, 600), labels=None):
    import pyvista as pv
    from PIL import Image, ImageDraw, ImageFont
    meshes = [(_pv(s), c, o) for s, c, o in items]
    tiles = []
    for k, cam in enumerate(views):
        p = pv.Plotter(off_screen=True, window_size=size)
        p.set_background("white")
        p.enable_anti_aliasing("fxaa")
        for m, c, o in meshes:
            p.add_mesh(m, color=c, opacity=o, smooth_shading=False)
        p.camera_position = cam
        p.camera.view_angle = 30
        im = Image.fromarray(p.screenshot(return_img=True))
        p.close()
        if labels:
            d = ImageDraw.Draw(im)
            f = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 17)
            d.rectangle([0, 0, im.width, 32], fill=(245, 245, 245))
            d.text((10, 7), labels[k], fill=(30, 30, 30), font=f)
        tiles.append(im)
    canvas = Image.new("RGB", (sum(t.width for t in tiles), max(t.height for t in tiles)), "white")
    x = 0
    for t in tiles:
        canvas.paste(t, (x, 0))
        x += t.width
    OUT.mkdir(exist_ok=True)
    canvas.save(out)
    print("->", out.relative_to(HERE))


def doser_part(name: str, D=np.eye(4)):
    L = S.doser_layout()
    rel, M = L.placements()[name]
    c = cq.Compound.makeCompound(cq.importers.importStep(str(S.doser_step(rel))).vals())
    return c.moved(loc(D @ M))


def fixture():
    D = S.T((G.FIX_X, 0, G.FIX_AXIS_Z - G.AXIS_Z))
    items = [(H.finger_fixture_hifi(), FIXTURE, 1.0), (doser_part("Tap collar", D), (0.95, 0.95, 0.95), 1.0),
             (doser_part("Solenoid (Adafruit 412)", D), (0.80, 0.50, 0.15), 1.0), (doser_part("Auger", D), TUBE, 0.45)]
    c = np.array([G.FIX_X, 90.0, G.FIX_AXIS_Z])
    render(items, [(tuple(c + (170, -170, 140)), tuple(c), (0, 0, 1)), (tuple(c + (0, -250, 25)), tuple(c), (0, 0, 1)),
                   (tuple(c + (210, 150, 120)), tuple(c), (0, 0, 1))], OUT / "view_fixture.png",
           labels=["fixture with the collar and auger", "from the outlet end: F1 fork, collar", "gear side: F2 fork, 44T gear"])
    c2 = np.array([G.FIX_X, 88.0, 22.0])
    render([(H.finger_fixture_hifi(), FIXTURE, 1.0)], [(tuple(c2 + (110, -110, 120)), tuple(c2), (0, 0, 1))],
           OUT / "view_fixture_alone.png", labels=["ledges are the collar's underside"])


def _gripper(opening, fingers=True):
    sol = AGX.solids()
    dz = AGX.finger_shift(opening)
    out = [(sol[i], GRIP, 1.0) for i in AGX.BODY]
    out += [(sol[i].translate(cq.Vector(0, 0, dz)), STEEL, 1.0) for i in (5, 8)]
    out += [(sol[i].translate(cq.Vector(0, 0, -dz)), STEEL, 1.0) for i in (9, 12)]
    if fingers:
        out += [(sol[i].translate(cq.Vector(0, 0, dz)), FIN, 1.0) for i in (6, 7)]
        out += [(sol[i].translate(cq.Vector(0, 0, -dz)), FIN, 1.0) for i in (10, 11)]
    return out, dz


def _both(part, dz):
    up = part.translate((0, 0, dz))
    lo = cq.Workplane().add(part.translate((0, 0, dz)).val().moved(loc(AGX.lower_of())))
    return up, lo


def sleeves():
    D = H.sleeve_opening()
    items, dz = _gripper(D)
    blue, green = H.sleeve_main_shell(), H.sleeve_fixing_shell()
    hw = cq.Workplane().add([h.val() for _, h in H.sleeve_hardware()])
    for part, col in ((blue, BLUE), (green, GREEN), (hw, BRASS)):
        for s in _both(part, dz):
            items.append((s, col, 1.0))
    tube = cq.Workplane("YZ").center(H.SL_YC, AGX.AX_Z).circle(G.TUBE_R).extrude(110).translate((-63, 0, 0))
    items.append((tube, TUBE, 0.55))
    c = np.array([-8.0, -55.0, 2.0])
    render(items, [(tuple(c + (230, -60, 30)), tuple(c), (0, 1, 0)), (tuple(c + (90, -170, 120)), tuple(c), (0, 1, 0)),
                   (tuple(c + (-60, -60, 230)), tuple(c), (0, 1, 0))], OUT / "view_sleeves.png",
           labels=["closed on the Ø25 tube (34.5 mm command)", "cradles: 180° each, 2 mm apart", "fixing shell over the back"])
    # one finger, shells apart
    sol = AGX.solids()
    one = [(sol[7], FIN, 1.0), (sol[6], FIN, 1.0), (sol[5], STEEL, 1.0), (blue.translate((0, 0, -18)), BLUE, 1.0),
           (green.translate((0, 0, 14)), GREEN, 1.0)] + [(h.translate((0, 0, -18)), BRASS, 1.0) for _, h in H.sleeve_hardware()[0::2]]
    c = np.array([-8.0, -58.0, 33.0])
    render(one, [(tuple(c + (200, -40, 10)), tuple(c), (0, 1, 0)), (tuple(c + (120, -110, -120)), tuple(c), (0, 1, 0))],
           OUT / "view_sleeve_exploded.png", labels=["main shell (blue), fixing shell (green)", "4 × M3 countersunk, 2 at each arrow"])


def custom_fingers():
    D = H.custom_opening()
    items, dz = _gripper(D, fingers=False)
    cf = H.custom_finger()
    hw = cq.Workplane().add([h.val() for _, h in H.custom_finger_hardware()])
    for part, col in ((cf, ORANGE), (hw, BRASS)):
        for s in _both(part, dz):
            items.append((s, col, 1.0))
    tube = cq.Workplane("YZ").center(H.CF_YC, AGX.AX_Z).circle(G.TUBE_R).extrude(110).translate((-63, 0, 0))
    items.append((tube, TUBE, 0.55))
    c = np.array([-8.0, -12.0, 2.0])
    render(items, [(tuple(c + (60, -200, 90)), tuple(c), (0, 1, 0)), (tuple(c + (220, -40, 30)), tuple(c), (0, 1, 0)),
                   (tuple(c + (-150, 60, 150)), tuple(c), (0, 1, 0))], OUT / "view_custom_fingers.png",
           labels=["custom fingers on the MGN7C carriages", "tube 19.5 mm from the finger plate", "M3 insert for the linkage screw"])


def pin():
    plate = doser_part("Mounting plate")
    guide, slider = H.pin_guide(), H.pin_slider()
    red, dred = (0.85, 0.22, 0.20), (0.98, 0.45, 0.35)      # guide, slider (as in the GIFs)
    items = [(plate, (0.62, 0.64, 0.68), 1.0), (guide, red, 1.0),
             (slider.translate((H.PIN_X_IN, H.PIN_Y, 0)), dred, 1.0)]
    c = np.array([55.0, H.PIN_Y, 25.0])
    render(items, [(tuple(c + (150, -170, 130)), tuple(c), (0, 0, 1)), (tuple(c + (5, -230, 20)), tuple(c), (0, 0, 1))],
           OUT / "view_pin.png", labels=["tilt-lock slider pushed in over the floor", "tip 0.5 mm over the floor, Ø25 knob"])
    # latched out: the guide cut on the slider's centre plane, so the latch beam and window show
    cut = cq.Workplane("XY").box(200, 60, 100, centered=(True, False, True)).translate((60, H.PIN_Y - 60, 30))
    items = [(plate.cut(cut.val()), (0.62, 0.64, 0.68), 1.0), (guide.cut(cut), red, 1.0),
             (slider.translate((H.PIN_X_OUT, H.PIN_Y, 0)).cut(cut), dred, 1.0)]
    c = np.array([62.0, H.PIN_Y, 24.0])
    c2 = np.array([62.5, H.PIN_Y, 24.5])
    render(items, [(tuple(c + (10, -150, 30)), tuple(c), (0, 0, 1)), (tuple(c2 + (0, -32, 2)), tuple(c2), (0, 0, 1))],
           OUT / "view_pin_latch.png", labels=["pulled out: the latch holds it (section)", "bump in the roof window"])


def knob():
    """Both cradle versions closed on the slider's knob (pushed in), looking along the knob:
    the relief notches in the jaws straddle the post."""
    from export_step import gripper_world
    red, dred = (0.85, 0.22, 0.20), (0.98, 0.45, 0.35)
    base = [(H.pin_guide(), red, 1.0), (H.pin_slider().translate((H.PIN_X_IN, H.PIN_Y, 0)), dred, 1.0)]
    at = (H.PIN_X_IN + H.KNOB_U, H.knob_grip_y(), H.BAR_Z)
    tiles = []
    for sleeves in (False, True):
        zb = H.sleeve_axis_base_z() if sleeves else H.custom_axis_base_z()
        D = H.sleeve_opening() if sleeves else H.custom_opening()
        B = gripper_world(zb, at) @ AGX.step_to_base()
        dz = AGX.finger_shift(D)
        poses = (B @ S.T((0, 0, dz)), B @ AGX.lower_of() @ S.T((0, 0, dz)))
        parts = [(H.sleeve_main_shell(), BLUE), (H.sleeve_fixing_shell(), GREEN)] if sleeves else [(H.custom_finger(), ORANGE)]
        if sleeves:
            sol = AGX.solids()
            parts += [(cq.Workplane().add(sol[i]), FIN) for i in (6, 7)]
        items = list(base)
        for part, col in parts:
            for M in poses:
                items.append((cq.Workplane().add(part.val().moved(loc(M))), col, 1.0))
        tiles.append(items)
    c = np.array([at[0], at[1], 33.0])
    cam = [(tuple(c + (25, -150, -15)), tuple(c), (0, 0, 1))]
    render(tiles[0], cam, OUT / "view_knob_custom.png", size=(560, 520), labels=["custom fingers: notches round the post"])
    render(tiles[1], cam, OUT / "view_knob_sleeves.png", size=(560, 520), labels=["sleeves: notches round the post"])


if __name__ == "__main__":
    which = sys.argv[1:] or ["fixture", "sleeves", "custom_fingers", "pin", "knob"]
    for w in which:
        globals()[w]()
