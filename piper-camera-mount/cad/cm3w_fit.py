#!/usr/bin/env python3
"""The Camera Module 3 Wide on the pod, as Raspberry Pi's drawing and STEP model have it.

The pod first had a O13 round hole for the Wide, centred where the lens was modelled from Camera
Module 2's layout: an 8.5 mm module, 9.462 mm from the edge away from the connector. Raspberry Pi's
drawing (camera-module-3-wide-mechanical-drawing.pdf, drawn 1:1 with the connector edge at the top)
has a 10.8 mm square housing, 4.07 mm deep, centred 14.4 mm from that edge. The square doesn't fit
through O13, and its centre is 4.94 mm from where the round hole was. The pod got a square hole
for it (a4f85b5).

Below the housing the drawing also outlines the flex that runs from the camera module to its
board-to-board connector (8.9 x 7.3, 7.0 wide for the 3.3 next to the housing), but no view gives
its height. Raspberry Pi's STEP model of the Wide (RP-008154-DS-1, fetched at run time into
.cache/, not committed) has it, along with the connector (a Hirose DF37) under it. The hole now
runs on over the flex, clear of both outlines by cm_flex_c.

This takes the camera from the drawing alone, sets its four holes on the pod's four screw holes and
reports, for the pod before (git ref, default a4f85b5) and now:

  - where the pod's screw holes, counterbores and bosses are (they must not move)
  - how far each of the camera's holes is from the screw hole it sits on
  - the housing and the flex against the pod: overlap, gap, and the room round them across the plate
  - Raspberry Pi's STEP model placed on the same holes: its holes, and its board and front-side
    parts against the pod
  - what changed on the pod: the old pod minus the new, and the new minus the old

    python cm3w_fit.py [--old-ref a4f85b5]   # -> ../exports/cm3w_fit.json, ../renders/cm3w_fit.png
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import subprocess
import tempfile
import urllib.request
import zipfile
from pathlib import Path

import cadquery as cq
import matplotlib
import numpy as np
from OCP.BRepAdaptor import BRepAdaptor_Surface
from OCP.GeomAbs import GeomAbs_Cylinder

import piper_mount as pm

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.collections import PolyCollection  # noqa: E402

HERE = Path(__file__).resolve().parent
RENDERS = HERE.parent / "renders"
CACHE = HERE / ".cache"

# Raspberry Pi's drawing, front view as drawn: origin at the board's lower left corner, x to the
# right, y up (toward the connector edge), z out of the lens. Every number is a label on the
# drawing, and its linework agrees to 0.001 mm at 1 mm = 1 pt * 25.4 / 72.
DRAWING = {
    "board": (25.0, 23.862, 1.12),         # width, height, thickness; corners R2.0 (linework)
    "holes": [(2.0, 2.0), (23.0, 2.0), (2.0, 14.5), (23.0, 14.5)],   # O2.2, "2.0", "14.5", "2.0" in
    "hole_d": 2.2,
    "lens": (12.5, 14.4),                  # "12.5" to the right edge, "14.4" up from the bottom
    "lens_d": 6.95,
    "housing": (10.8, 10.8, 4.07),         # square, centred on the lens; depth off the PCB front face
    "lens_tip": 8.3,
    "connector_edge": "top",               # side view: the 5.71 x 2.75 connector, behind the board
    # The flex below the housing, from the linework: "8.9" wide and "4" tall at the bottom, then
    # 7.0 wide for the "3.3" up to the housing ("7.3" in all), with R0.8 and R0.5 fillets in the
    # inside corners. No view gives a height.
    "flex": [(9.519, 9.0), (9.519, 1.7), (18.419, 1.7), (18.419, 5.7), (16.519, 5.7), (16.519, 9.0)],
}

# Raspberry Pi's STEP model of Camera Module 3 (both lenses), from pip.raspberrypi.com. Its frame is
# the drawing's turned a quarter turn: model x = drawing y, model y = drawing x, the lens toward -z,
# the board's front face (the solder mask on the lens side) at z = -0.744.
STEP_URL = "https://datasheets.raspberrypi.com/camera/camera-module-3-step.zip"
STEP_ZIP = "RP-008154-DS-1-camera-module-3-step.zip"
STEP_SHA256 = "b2e2026ea5322bddf1ddcbae97c094822ee9e0ca92d7bc5c748f60a8b5ef6683"   # as fetched 2026-10-28
STEP_MEMBER = "Camera_module_3_wide_model_simple.stp"
STEP_FRONT = -0.744
# Its solids, by name and index: U4 (named for a part it isn't) is the camera module; its solid 2 is
# the flex, 0 the plug on the flex's end; J2 is the board's DF37NC-30DS-0.4V receptacle.
STEP_FLEX = (("U4", 2), ("U4", 0), ("J2", 0))
ROOM = "room round the flex across the plate, below the housing's hole (mm)"


def drawing_to_local(x: float, y: float) -> tuple[float, float]:
    """Drawing (x, y) -> the pod's camera frame for the Wide (piper_mount.make_cm_camera_local:
    lens at the origin, connector toward -y, x unchanged). Fixed by the lens alone; the holes are
    then wherever the drawing puts them."""
    lx, ly = DRAWING["lens"]
    return x - lx, ly - y


def world_to_local(p: pm.Params, v: cq.Vector) -> np.ndarray:
    o, t = pm.station_origin(p), math.radians(p.toe_deg)
    dx, dy, dz = v.x - o.x, v.y - o.y, v.z - o.z
    sx, sy, sz = dx * math.cos(t) + dy * math.sin(t), -dx * math.sin(t) + dy * math.cos(t), dz
    return np.array([sx, p.cm_dz - sz, sy + (p.hq_standoff - p.cm_standoff)])


def dir_to_local(p: pm.Params, v: cq.Vector) -> np.ndarray:
    t = math.radians(p.toe_deg)
    sx, sy, sz = v.x * math.cos(t) + v.y * math.sin(t), -v.x * math.sin(t) + v.y * math.cos(t), v.z
    return np.array([sx, -sz, sy])


def local_box(p: pm.Params, shape: cq.Shape) -> tuple[list[float], list[float]]:
    """Bounding box in the Wide's camera frame: taken in the station frame, whose axes it shares."""
    o = pm.station_origin(p)
    bb = shape.translate(-o).rotate(cq.Vector(), cq.Vector(0, 0, 1), -p.toe_deg).BoundingBox()
    dy, dz = p.hq_standoff - p.cm_standoff, p.cm_dz
    lo = [bb.xmin, dz - bb.zmax, bb.ymin + dy]
    hi = [bb.xmax, dz - bb.zmin, bb.ymax + dy]
    return [round(v, 3) for v in lo], [round(v, 3) for v in hi]


def local_to_world_wp(p: pm.Params, wp: cq.Workplane) -> cq.Workplane:
    return pm.cm_place(p)(wp)


def outline_prism(pts: list[tuple[float, float]], z0: float, z1: float) -> cq.Workplane:
    """A polygon in the camera frame's (x, y), extruded from z0 to z1."""
    return cq.Workplane("XY").polyline(pts).close().extrude(z1 - z0).translate((0, 0, z0))


def flex_local() -> list[tuple[float, float]]:
    return [drawing_to_local(x, y) for x, y in DRAWING["flex"]]


def camera_from_drawing(p: pm.Params, flex_h: float) -> dict[str, cq.Workplane]:
    """The board, housing and flex from DRAWING, in the world, through the camera frame. The flex
    takes its height from the STEP model."""
    w, h, t = DRAWING["board"]
    x0, y0 = drawing_to_local(0, 0)
    x1, y1 = drawing_to_local(w, h)
    board = pm.lbox(min(x0, x1), max(x0, x1), min(y0, y1), max(y0, y1), 0, t)
    for x, y in DRAWING["holes"]:
        hx, hy = drawing_to_local(x, y)
        board = board.cut(pm.cyl_z(DRAWING["hole_d"], -1, t + 1, hx, hy))
    hw, hh, hd = DRAWING["housing"]
    housing = pm.lbox(-hw / 2, hw / 2, -hh / 2, hh / 2, -hd, 0)
    lens = pm.cyl_z(DRAWING["lens_d"], -DRAWING["lens_tip"], -hd)
    flex = outline_prism(flex_local(), -flex_h, 0)
    # The same outlines run right through the plate: their gap to the pod is the room across it.
    flex_through = outline_prism(flex_local(), -80, 0)
    housing_through = pm.lbox(-hw / 2, hw / 2, -hh / 2, hh / 2, -80, 0)
    return {k: local_to_world_wp(p, v) for k, v in (("board", board), ("housing", housing), ("lens", lens),
                                                    ("flex", flex), ("flex_through", flex_through),
                                                    ("housing_through", housing_through))}


def fetch_step() -> Path:
    CACHE.mkdir(exist_ok=True)
    zpath = CACHE / STEP_ZIP
    if not zpath.exists():
        req = urllib.request.Request(STEP_URL, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=300) as r:
            zpath.write_bytes(r.read())
    digest = hashlib.sha256(zpath.read_bytes()).hexdigest()
    if digest != STEP_SHA256:
        raise SystemExit(f"{zpath.name}: sha256 {digest}, expected {STEP_SHA256}; Raspberry Pi changed it?")
    out = CACHE / STEP_MEMBER
    if not out.exists():
        with zipfile.ZipFile(zpath) as z:
            out.write_bytes(z.read(STEP_MEMBER))
    return out


def step_solids(path: Path) -> dict[tuple[str, int], cq.Solid]:
    """{(reference designator, index): solid} for every component of the board, plus ("board", 0)
    for the dielectric, read with their names from the STEP's assembly tree."""
    from OCP.IFSelect import IFSelect_RetDone
    from OCP.STEPCAFControl import STEPCAFControl_Reader
    from OCP.TCollection import TCollection_ExtendedString
    from OCP.TDataStd import TDataStd_Name
    from OCP.TDF import TDF_Label, TDF_LabelSequence
    from OCP.TDocStd import TDocStd_Document
    from OCP.TopAbs import TopAbs_SOLID
    from OCP.TopExp import TopExp_Explorer
    from OCP.TopLoc import TopLoc_Location
    from OCP.TopoDS import TopoDS
    from OCP.XCAFDoc import XCAFDoc_DocumentTool

    doc = TDocStd_Document(TCollection_ExtendedString("cm3"))
    reader = STEPCAFControl_Reader()
    reader.SetNameMode(True)
    if reader.ReadFile(str(path)) != IFSelect_RetDone:
        raise SystemExit(f"can't read {path}")
    reader.Transfer(doc)
    tool = XCAFDoc_DocumentTool.ShapeTool_s(doc.Main())

    def name(lab) -> str:
        n = TDataStd_Name()
        return n.Get().ToExtString() if lab.FindAttribute(TDataStd_Name.GetID_s(), n) else ""

    out: dict[tuple[str, int], cq.Solid] = {}

    def walk(lab, loc, path_names):
        if tool.IsReference_s(lab):
            ref = TDF_Label()
            tool.GetReferredShape_s(lab, ref)
            walk(ref, loc.Multiplied(tool.GetLocation_s(lab)), path_names + [name(lab)])
            return
        if tool.IsAssembly_s(lab):
            comps = TDF_LabelSequence()
            tool.GetComponents_s(lab, comps)
            for i in range(1, comps.Length() + 1):
                walk(comps.Value(i), loc, path_names + [name(lab)])
            return
        key = "board" if name(lab) == "Dielectric" else next(
            (n for n in path_names if n in {d for d, _ in STEP_FLEX} | {"U4"}), None)
        if key is None:
            return
        exp, k = TopExp_Explorer(tool.GetShape_s(lab).Moved(loc), TopAbs_SOLID), 0
        while exp.More():
            out[(key, k)] = cq.Solid(TopoDS.Solid_s(exp.Current()))
            k += 1
            exp.Next()

    roots = TDF_LabelSequence()
    tool.GetFreeShapes(roots)
    for i in range(1, roots.Length() + 1):
        walk(roots.Value(i), TopLoc_Location(), [])
    return out


def step_to_local(s: cq.Shape) -> cq.Shape:
    """STEP model frame -> the Wide's camera frame: a quarter turn about z, the lens to the origin
    and the board's front face to z = 0."""
    lx, ly = DRAWING["lens"]
    return s.rotate(cq.Vector(), cq.Vector(0, 0, 1), -90).translate(cq.Vector(-lx, ly, -STEP_FRONT))


def camera_from_step(p: pm.Params) -> tuple[dict[str, cq.Workplane], dict]:
    """Raspberry Pi's model, in the world through the camera frame: the board, every solid of the
    camera module and connector, the flex below the housing, and the flex's outline through the
    plate. Also what it measures, in the drawing's frame and from the board's front face."""
    sol = step_solids(fetch_step())
    below = cq.Solid.makeBox(10.0, 40, 40, cq.Vector(-1, -5, -20))       # model x < 9: below the housing
    flex = [sol[("U4", 2)].intersect(below)] + [sol[k] for k in STEP_FLEX[1:]]
    flex = [s for f in flex for s in f.Solids()]
    # The room across the plate is taken below the housing's hole (model x < 8.7, 0.3 short of the
    # housing's edge). Above that the flex flares into the module, inside the housing's hole, 1.0 to
    # 1.4 mm off the board.
    short = cq.Solid.makeBox(9.7, 40, 40, cq.Vector(-1, -5, -20))
    # The flex's outline: its section 1.2 mm off the board, where all of it is (its top, but for a
    # ramp up into the module at the housing's edge, is 1.41 mm off).
    z = STEP_FRONT - 1.2
    cut = sol[("U4", 2)].intersect(cq.Solid.makeBox(60, 60, 0.002, cq.Vector(-20, -20, z - 0.001)))
    face = max((f for f in cut.Faces() if f.normalAt().z > 0.99), key=lambda f: f.Area())
    flex_through = cq.Solid.extrudeLinear(face, cq.Vector(0, 0, -100)).intersect(short)
    holes = set()
    for f in sol[("board", 0)].Faces():
        a = BRepAdaptor_Surface(f.wrapped)
        if a.GetType() == GeomAbs_Cylinder and abs(2 * a.Cylinder().Radius() - DRAWING["hole_d"]) < 0.05:
            c = a.Cylinder().Axis().Location()
            holes.add((round(c.Y(), 3), round(c.X(), 3)))
    fb = cq.Compound.makeCompound(flex).BoundingBox()
    tb = flex_through.BoundingBox()
    module = [s for (d, _), s in sol.items() if d == "U4"]
    mb = cq.Compound.makeCompound(module).BoundingBox()
    info = {
        "file": f"{STEP_ZIP} / {STEP_MEMBER}, sha256 of the zip {STEP_SHA256}",
        "holes (drawing x, y)": sorted(holes),
        "board's dielectric, z in the model's frame (front face at -0.744)": [
            round(sol[("board", 0)].BoundingBox().zmin, 3), round(sol[("board", 0)].BoundingBox().zmax, 3)],
        "flex below the housing's hole, outline (drawing x0, x1, y0, y1)": [round(v, 3) for v in (tb.ymin, tb.ymax, tb.xmin, tb.xmax)],
        "flex below the housing, off the board's front face (mm)": [round(STEP_FRONT - fb.zmax, 3),
                                                                    round(STEP_FRONT - fb.zmin, 3)],
        "flex, plug and receptacle, off the board's front face (mm)": {
            f"{d} {k}": [round(STEP_FRONT - sol[(d, k)].BoundingBox().zmax, 3),
                         round(STEP_FRONT - sol[(d, k)].BoundingBox().zmin, 3)] for d, k in STEP_FLEX},
        "camera module, furthest off the board's front face (mm)": round(STEP_FRONT - mb.zmin, 3),
    }
    to_world = lambda shapes: local_to_world_wp(p, cq.Workplane("XY").add(  # noqa: E731
        cq.Compound.makeCompound([step_to_local(s) for s in shapes])))
    parts = {"board": to_world([sol[("board", 0)]]), "front": to_world(module + [sol[("J2", 0)]]),
             "flex": to_world(flex), "flex_through": to_world([flex_through])}
    return parts, info


def cylinders(p: pm.Params, part: cq.Workplane) -> dict[str, list[list[float]]]:
    """Axis (x, y) in the Wide's camera frame of every cylindrical face along the lens axis,
    grouped by diameter."""
    out: dict[str, set] = {}
    for f in part.val().Faces():
        s = BRepAdaptor_Surface(f.wrapped)
        if s.GetType() != GeomAbs_Cylinder:
            continue
        c = s.Cylinder()
        loc, d = c.Axis().Location(), c.Axis().Direction()
        if abs(abs(dir_to_local(p, cq.Vector(d.X(), d.Y(), d.Z()))[2]) - 1) > 1e-6:
            continue
        x, y, _ = world_to_local(p, cq.Vector(loc.X(), loc.Y(), loc.Z()))
        if abs(x) > 14 or abs(y - 6) > 12:          # the Wide's station only
            continue
        out.setdefault(f"O{2 * c.Radius():.2f}", set()).add((round(x, 4), round(y, 4)))
    return {k: sorted([list(q) for q in v]) for k, v in sorted(out.items())}


def hole_walls(p: pm.Params, part: cq.Workplane) -> list[dict]:
    """The flat walls of the opening round the lens, in the camera frame: which way each faces
    (into the opening), where it is, and what it spans."""
    walls = []
    for f in part.val().Faces():
        if f.geomType() != "PLANE":
            continue
        n = dir_to_local(p, f.normalAt())
        c = world_to_local(p, f.Center())
        if abs(n[2]) > 1e-6 or abs(c[0]) > 8 or not -8 < c[1] < 15:
            continue
        lo, hi = local_box(p, f)
        ax = 0 if abs(abs(n[0]) - 1) < 1e-6 else 1
        walls.append({"at": f"{'xy'[ax]} = {c[ax]:.3f}", "faces": ("+" if n[ax] > 0 else "-") + "xy"[ax],
                      "spans": f"{'yx'[ax]} {lo[1 - ax]:.3f} to {hi[1 - ax]:.3f}"})
    return sorted(walls, key=lambda w: w["at"])


def old_pod(ref: str) -> cq.Workplane:
    blob = subprocess.run(["git", "show", f"{ref}:piper-camera-mount/exports/pod.step"], cwd=HERE,
                          check=True, capture_output=True).stdout
    with tempfile.NamedTemporaryFile(suffix=".step") as tmp:
        tmp.write(blob)
        tmp.flush()
        return cq.importers.importStep(tmp.name)


def section(p: pm.Params, part: cq.Workplane, lz: float | None = None,
            lx: float | None = None) -> tuple[list[np.ndarray], list[np.ndarray]]:
    """The part cut across the lens axis at camera-frame depth lz, as (x, y); or along it, at
    camera-frame x = lx, as (z, y). Returns (triangles, edges)."""
    t = math.radians(p.toe_deg)
    if lz is not None:
        o = pm.station_vec(p, 0, lz - (p.hq_standoff - p.cm_standoff), 0)
        n = cq.Vector(math.sin(t), -math.cos(t), 0)
        slab = cq.Solid.makeBox(400, 0.002, 400, cq.Vector(-200, -0.001, -200))
        keep = [0, 1]
    else:
        o = pm.station_vec(p, lx, -(p.hq_standoff - p.cm_standoff), p.cm_dz)
        n = cq.Vector(math.cos(t), math.sin(t), 0)
        slab = cq.Solid.makeBox(0.002, 400, 400, cq.Vector(-0.001, -200, -200))
        keep = [2, 1]
    slab = slab.rotate(cq.Vector(), cq.Vector(0, 0, 1), p.toe_deg).translate(o)
    tris, edges = [], []
    for sol in part.val().Solids():
        cut = sol.intersect(slab)
        for f in cut.Faces():
            if abs(abs(f.normalAt().dot(n)) - 1) > 1e-6 or f.Center().sub(o).dot(n) < 0:
                continue
            verts, idx = f.tessellate(0.02, 0.2)
            xy = np.array([world_to_local(p, v)[keep] for v in verts])
            tris += [xy[list(i)] for i in idx]
            for e in f.Edges():
                edges.append(np.array([world_to_local(p, v)[keep] for v in e.positions(list(np.linspace(0, 1, 96)))]))
    return tris, edges


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--old-ref", default="a4f85b5", help="commit with the pod to compare against")
    ap.add_argument("--out", type=Path, default=pm.EXPORTS / "cm3w_fit.json")
    args = ap.parse_args()
    p = pm.Params()
    pods = {"before": old_pod(args.old_ref), "now": pm.make_pod(p)}
    step, step_info = camera_from_step(p)
    flex_h = step_info["flex below the housing, off the board's front face (mm)"][1]
    cam = camera_from_drawing(p, flex_h)
    res: dict = {"drawing": DRAWING, "step model": step_info, "old_ref": args.old_ref,
                 "camera_frame": "lens at the origin, connector toward -y, mm; the pod's screw holes in it"}
    want = sorted([list(drawing_to_local(x, y)) for x, y in DRAWING["holes"]])
    step_holes = sorted([list(drawing_to_local(x, y)) for x, y in step_info["holes (drawing x, y)"]])
    for name, pod in pods.items():
        cyl = cylinders(p, pod)
        screw = cyl.get(f"O{p.m2_clear_d:.2f}", [])
        r = {"cylinders by diameter": cyl, "walls of the opening round the lens": hole_walls(p, pod)}
        r["camera hole to its screw hole (mm)"] = [round(min(math.dist(h, s) for s in screw), 4) for h in want]
        r["STEP model's hole to its screw hole (mm)"] = [round(min(math.dist(h, s) for s in screw), 4)
                                                         for h in step_holes]
        r["housing overlap (mm3)"] = round(pm.overlap(cam["housing"], pod), 2)
        r["lens overlap (mm3)"] = round(pm.overlap(cam["lens"], pod), 2)
        r["board overlap (mm3)"] = round(pm.overlap(cam["board"], pod), 2)
        r["flex overlap (mm3)"] = round(pm.overlap(cam["flex"], pod), 2)
        r["housing to the pod (mm)"] = round(pm.gap(cam["housing"], pod), 3)
        r["board to the bosses (mm)"] = round(pm.gap(cam["board"], pod), 3)
        r["flex to the pod (mm)"] = round(pm.gap(cam["flex"], pod), 3)
        r["room round the housing across the plate (mm)"] = round(pm.gap(cam["housing_through"], pod), 3)
        r[ROOM] = round(pm.gap(cam["flex_through"], pod), 3)
        r["plastic over the flex, its outline through the plate (mm3)"] = round(pm.overlap(cam["flex_through"], pod), 1)
        r["STEP model: board and front-side parts overlap (mm3)"] = round(
            pm.overlap(step["board"], pod) + pm.overlap(step["front"], pod), 2)
        r["STEP model: flex to the pod (mm)"] = round(pm.gap(step["flex"], pod), 3)
        r["STEP model: " + ROOM] = round(pm.gap(step["flex_through"], pod), 3)
        res[name] = r
    a, b = pods["before"].val(), pods["now"].val()
    removed, added = a.cut(b), b.cut(a)
    res["changed"] = {}
    for k, diff in (("old minus new", removed), ("new minus old", added)):
        solids = [q for q in diff.Solids() if q.Volume() > 1e-3]
        entry = {"volume (mm3)": round(sum(q.Volume() for q in solids), 2), "solids": len(solids)}
        if solids:
            lo, hi = local_box(p, cq.Compound.makeCompound(solids))
            entry["camera-frame box (x, y, z)"] = [lo, hi]
        res["changed"][k] = entry
    res["pod volume (mm3)"] = {"before": round(a.Volume(), 2), "now": round(b.Volume(), 2)}
    args.out.write_text(json.dumps(res, indent=2) + "\n")
    print(json.dumps(res, indent=2))
    plot(p, pods, res, cam, step)


def plot(p: pm.Params, pods: dict, res: dict, cam: dict, step: dict) -> None:
    """Both pods cut 3.3 mm in front of the Wide's board (inside the plate, where the housing
    reaches), seen from the front as the drawing's front view is, with the camera from the drawing
    on top; then the new pod cut along the lens axis through the flex, with the drawing's camera and
    Raspberry Pi's model in it. Red: plastic over the flex, or the housing inside the pod."""
    lz, lx = -3.3, 1.0
    fig, axes = plt.subplots(1, 3, figsize=(16.5, 6.6), gridspec_kw={"width_ratios": [1, 1, 0.7]})
    w, h, _ = DRAWING["board"]
    hw, hh, hd = DRAWING["housing"]
    flex = np.array(flex_local())
    titles = (f"Before ({res['old_ref']}): 11.4 mm square hole only", "Now: the hole runs on over the flex")
    for ax, (name, pod), title in zip(axes, pods.items(), titles):
        tris, edges = section(p, pod, lz=lz)
        ax.add_collection(PolyCollection(tris, fc="#f5c08a", ec="#f5c08a", lw=0.3))
        for e in edges:
            ax.plot(e[:, 0], e[:, 1], color="#b05a10", lw=1.0)
        for key in ("flex_through", "housing"):
            if pm.overlap(cam[key], pod) > 0:
                hit = cq.Workplane("XY").add(cam[key].val().intersect(pod.val()))
                ax.add_collection(PolyCollection(section(p, hit, lz=lz)[0], fc="#d02020", ec="#d02020", lw=0.3, alpha=0.9))
        x0, y0 = drawing_to_local(0, 0)
        ax.add_patch(plt.Rectangle((x0, y0 - h), w, h, fill=False, ec="#1a7a3a", lw=1.6, ls="--"))
        ax.add_patch(plt.Rectangle((-hw / 2, -hh / 2), hw, hh, fc="#222222", alpha=0.35, ec="#000000", lw=1.6))
        ax.add_patch(plt.Polygon(flex, closed=True, fc="#222222", alpha=0.2, ec="#000000", lw=1.4))
        ax.add_patch(plt.Circle((0, 0), DRAWING["lens_d"] / 2, fill=False, ec="#000000", lw=1.2))
        for x, y in DRAWING["holes"]:
            hx, hy = drawing_to_local(x, y)
            ax.add_patch(plt.Circle((hx, hy), DRAWING["hole_d"] / 2, fill=False, ec="#1a7a3a", lw=1.6))
        r = res[name]
        if r["plastic over the flex, its outline through the plate (mm3)"] > 0:
            note = (f"flex (outlined) under the plate: {r['flex to the pod (mm)']:.2f} mm below it;\n"
                    f"housing clear by {r['housing to the pod (mm)']:.1f} mm each side")
        else:
            note = (f"opening clear of the flex by {r[ROOM]:.1f} mm (drawing) and {r['STEP model: ' + ROOM]:.1f} mm "
                    "(STEP model);\n"
                    f"housing still {r['room round the housing across the plate (mm)']:.1f} mm each side")
        ax.set_title(f"{title}\n{note}", fontsize=10.5)
        ax.text(0, y0 - h - 0.6, "ribbon connector edge", ha="center", va="bottom", fontsize=8, color="#1a7a3a")
        ax.annotate("flex to its\nconnector", (flex[:, 0].max() - 1.0, 11.5), (11.0, 16.0), fontsize=8, ha="center",
                    arrowprops={"arrowstyle": "-", "color": "#000000", "lw": 0.6})
        ax.set_aspect("equal")
        ax.set_xlim(-16, 16)
        ax.set_ylim(17.5, -13)            # connector edge (toward the top of the pod) up
        ax.set_xlabel("mm, from the lens axis")
        ax.grid(alpha=0.2)
    axes[0].set_ylabel("mm, from the lens axis (up = toward the top of the pod)")
    # Along the lens axis, through the flex.
    ax = axes[2]
    for part, fc, ec in ((pods["now"], "#f5c08a", "#b05a10"), (step["board"], "#9fd4ae", "#1a7a3a"),
                         (step["front"], "#555555", "#222222")):
        tris, edges = section(p, part, lx=lx)
        ax.add_collection(PolyCollection(tris, fc=fc, ec=fc, lw=0.3))
        for e in edges:
            ax.plot(e[:, 0], e[:, 1], color=ec, lw=0.8)
    old = section(p, pods["before"], lx=lx)[1]
    for e in old:
        ax.plot(e[:, 0], e[:, 1], color="#b05a10", lw=0.8, ls=":")
    ax.add_patch(plt.Rectangle((-hd, -hh / 2), hd, hh, fill=False, ec="#000000", lw=1.0, ls="--"))
    ys = flex[:, 1]
    fh = res["step model"]["flex below the housing, off the board's front face (mm)"][1]
    ax.add_patch(plt.Rectangle((-fh, ys.min()), fh, ys.max() - ys.min(), fill=False, ec="#000000", lw=1.0, ls="--"))
    ax.annotate(f"flex: {fh:.2f} mm off the board\nboard: {p.cm_standoff:.1f} mm off the plate", (-fh, 11.0), (-9.5, 15.6),
                fontsize=8, arrowprops={"arrowstyle": "-", "color": "#000000", "lw": 0.6})
    ax.set_title(f"Now, cut along the lens axis,\n{lx:.0f} mm right of it. Grey: Raspberry Pi's\n"
                 "STEP model; dotted: the pod before", fontsize=10.5)
    ax.set_aspect("equal")
    ax.set_xlim(-10.5, 2.5)
    ax.set_ylim(17.5, -13)
    ax.set_xlabel("mm along the lens axis (− = toward the scene)")
    ax.grid(alpha=0.2)
    fig.suptitle("Camera Module 3 Wide on the pod: board (dashed), its 4 holes (green), housing and flex from Raspberry Pi's "
                 "drawing (grey), heights from its STEP model;\nthe pod (orange) cut 3.3 mm in front of the board; red: "
                 "plastic over the flex's outline", fontsize=11)
    fig.tight_layout()
    RENDERS.mkdir(exist_ok=True)
    fig.savefig(RENDERS / "cm3w_fit.png", dpi=110)


if __name__ == "__main__":
    main()
