#!/usr/bin/env python3
"""The Camera Module 3 Wide on the pod, as Raspberry Pi's drawing has it.

The pod first had a O13 round hole for the Wide, centred where the lens was modelled from Camera
Module 2's layout: an 8.5 mm module, 9.462 mm from the edge away from the connector. Raspberry Pi's
drawing (camera-module-3-wide-mechanical-drawing.pdf, drawn 1:1 with the connector edge at the top)
has a 10.8 mm square housing, 4.07 mm deep, centred 14.4 mm from that edge. The square doesn't fit
through O13, and its centre is 4.94 mm from where the round hole was.

This takes the camera from the drawing alone, sets its four holes on the pod's four screw holes and
reports, for the pod before (git ref, default 70dc1db) and now:

  - where the pod's screw holes, counterbores and bosses are (they must not move)
  - how far each of the camera's holes is from the screw hole it sits on
  - the housing against the pod: overlap, and the hole's walls round it
  - what changed on the pod: the old pod minus the new, and the new minus the old

    python cm3w_fit.py [--old-ref 70dc1db]   # -> ../exports/cm3w_fit.json, ../renders/cm3w_fit.png
"""
from __future__ import annotations

import argparse
import json
import math
import subprocess
import tempfile
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
}


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


def camera_from_drawing(p: pm.Params) -> dict[str, cq.Workplane]:
    """The board and housing from DRAWING, in the world, through the camera frame."""
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
    return {k: local_to_world_wp(p, v) for k, v in (("board", board), ("housing", housing), ("lens", lens))}


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


def hole_walls(p: pm.Params, part: cq.Workplane) -> dict[str, float]:
    """The flat walls of the hole round the lens, in the camera frame."""
    walls = {}
    for f in part.val().Faces():
        if f.geomType() != "PLANE":
            continue
        n = dir_to_local(p, f.normalAt())
        c = world_to_local(p, f.Center())
        if abs(n[2]) > 1e-6 or abs(c[0]) > 8 or abs(c[1]) > 8:
            continue
        if abs(abs(n[0]) - 1) < 1e-6:
            walls["x-" if c[0] < 0 else "x+"] = round(float(c[0]), 4)
        elif abs(abs(n[1]) - 1) < 1e-6:
            walls["y-" if c[1] < 0 else "y+"] = round(float(c[1]), 4)
    return walls


def old_pod(ref: str) -> cq.Workplane:
    blob = subprocess.run(["git", "show", f"{ref}:piper-camera-mount/exports/pod.step"], cwd=HERE,
                          check=True, capture_output=True).stdout
    with tempfile.NamedTemporaryFile(suffix=".step") as tmp:
        tmp.write(blob)
        tmp.flush()
        return cq.importers.importStep(tmp.name)


def section(p: pm.Params, part: cq.Workplane, lz: float) -> tuple[list[np.ndarray], list[np.ndarray]]:
    """The part cut across the lens axis at camera-frame depth lz: (triangles, edges) in (x, y)."""
    t = math.radians(p.toe_deg)
    o = pm.station_vec(p, 0, lz - (p.hq_standoff - p.cm_standoff), 0)
    n = cq.Vector(math.sin(t), -math.cos(t), 0)
    slab = cq.Solid.makeBox(400, 0.002, 400, cq.Vector(-200, -0.001, -200))
    slab = slab.rotate(cq.Vector(), cq.Vector(0, 0, 1), p.toe_deg).translate(o)
    cut = part.val().intersect(slab)
    tris, edges = [], []
    for f in cut.Faces():
        if abs(abs(f.normalAt().dot(n)) - 1) > 1e-6 or f.Center().sub(o).dot(n) > 0:
            continue
        verts, idx = f.tessellate(0.02, 0.2)
        xy = np.array([world_to_local(p, v)[:2] for v in verts])
        tris += [xy[list(i)] for i in idx]
        for e in f.Edges():
            edges.append(np.array([world_to_local(p, v)[:2] for v in e.positions(list(np.linspace(0, 1, 96)))]))
    return tris, edges


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--old-ref", default="70dc1db", help="commit with the round-hole pod")
    ap.add_argument("--out", type=Path, default=pm.EXPORTS / "cm3w_fit.json")
    args = ap.parse_args()
    p = pm.Params()
    pods = {"before": old_pod(args.old_ref), "now": pm.make_pod(p)}
    cam = camera_from_drawing(p)
    res: dict = {"drawing": DRAWING, "old_ref": args.old_ref,
                 "camera_frame": "lens at the origin, connector toward -y, mm; the pod's screw holes in it"}
    want = sorted([list(drawing_to_local(x, y)) for x, y in DRAWING["holes"]])
    for name, pod in pods.items():
        cyl = cylinders(p, pod)
        screw = cyl.get(f"O{p.m2_clear_d:.2f}", [])
        r = {"cylinders by diameter": cyl, "hole walls round the lens": hole_walls(p, pod)}
        r["camera hole to its screw hole (mm)"] = [round(min(math.dist(h, s) for s in screw), 4) for h in want]
        r["housing overlap (mm3)"] = round(pm.overlap(cam["housing"], pod), 2)
        r["lens overlap (mm3)"] = round(pm.overlap(cam["lens"], pod), 2)
        r["board overlap (mm3)"] = round(pm.overlap(cam["board"], pod), 2)
        r["housing to the pod (mm)"] = round(pm.gap(cam["housing"], pod), 3)
        r["board to the bosses (mm)"] = round(pm.gap(cam["board"], pod), 3)
        res[name] = r
    hw = DRAWING["housing"][0] / 2
    walls = res["now"]["hole walls round the lens"]
    res["now"]["clearance per side (mm)"] = {k: round(abs(v) - hw, 4) for k, v in walls.items()}
    a, b = pods["before"].val(), pods["now"].val()
    removed, added = a.cut(b), b.cut(a)
    res["changed"] = {}
    for k, diff in (("old minus new", removed), ("new minus old", added)):
        solids = [q for q in diff.Solids() if q.Volume() > 1e-3]
        lo, hi = local_box(p, cq.Compound.makeCompound(solids))
        res["changed"][k] = {"volume (mm3)": round(sum(q.Volume() for q in solids), 2), "solids": len(solids),
                             "camera-frame box (x, y, z)": [lo, hi]}
    res["pod volume (mm3)"] = {"before": round(a.Volume(), 2), "now": round(b.Volume(), 2)}
    args.out.write_text(json.dumps(res, indent=2) + "\n")
    print(json.dumps(res, indent=2))
    plot(p, pods, res)


def plot(p: pm.Params, pods: dict, res: dict) -> None:
    """Both pods cut 3.3 mm in front of the Wide's board (inside the plate, where the housing
    reaches), seen from the front as the drawing's front view is, with the camera from the drawing
    on top. Red: where the housing would be inside the pod."""
    lz = -3.3
    fig, axes = plt.subplots(1, 2, figsize=(11, 6.2))
    w, h, _ = DRAWING["board"]
    hw, hh, _ = DRAWING["housing"]
    for ax, (name, pod), title in zip(axes, pods.items(),
                                      ("As printed: Ø13 round hole", "Now: 11.4 mm square hole")):
        tris, edges = section(p, pod, lz)
        ax.add_collection(PolyCollection(tris, fc="#f5c08a", ec="#f5c08a", lw=0.3))
        for e in edges:
            ax.plot(e[:, 0], e[:, 1], color="#b05a10", lw=1.0)
        clash = pm.overlap(camera_from_drawing(p)["housing"], pod)
        if clash > 0:
            hit = cq.Workplane("XY").add(camera_from_drawing(p)["housing"].val().intersect(pod.val()))
            ax.add_collection(PolyCollection(section(p, hit, lz)[0], fc="#d02020", ec="#d02020", lw=0.3, alpha=0.9))
        x0, y0 = drawing_to_local(0, 0)
        ax.add_patch(plt.Rectangle((x0, y0 - h), w, h, fill=False, ec="#1a7a3a", lw=1.6, ls="--"))
        ax.add_patch(plt.Rectangle((-hw / 2, -hh / 2), hw, hh, fc="#222222", alpha=0.35, ec="#000000", lw=1.6))
        ax.add_patch(plt.Circle((0, 0), DRAWING["lens_d"] / 2, fill=False, ec="#000000", lw=1.2))
        for x, y in DRAWING["holes"]:
            hx, hy = drawing_to_local(x, y)
            ax.add_patch(plt.Circle((hx, hy), DRAWING["hole_d"] / 2, fill=False, ec="#1a7a3a", lw=1.6))
        if name == "now":
            d = [c for k, v in res["before"]["cylinders by diameter"].items() if float(k[1:]) > 10 for c in v]
            for (cx, cy), k in zip(d, [k for k in res["before"]["cylinders by diameter"] if float(k[1:]) > 10]):
                ax.add_patch(plt.Circle((cx, cy), float(k[1:]) / 2, fill=False, ec="#b05a10", lw=1.0, ls=":"))
                ax.annotate(f"the round hole as printed (Ø{float(k[1:]):.0f})", (cx, cy + float(k[1:]) / 2), (cx, 16.2),
                            ha="center", fontsize=8, color="#b05a10",
                            arrowprops={"arrowstyle": "-", "color": "#b05a10", "lw": 0.6})
        r = res[name]
        clash = r["housing overlap (mm3)"]
        note = (f"housing overlaps the pod by {clash:.0f} mm³" if clash > 0 else
                f"housing clear: {r['housing to the pod (mm)']:.1f} mm each side")
        ax.set_title(f"{title}\n{note}", fontsize=11)
        ax.text(0, y0 - h - 0.6, "ribbon connector edge", ha="center", va="bottom", fontsize=8, color="#1a7a3a")
        ax.set_aspect("equal")
        ax.set_xlim(-16, 16)
        ax.set_ylim(17, -13)              # connector edge (toward the top of the pod) up
        ax.set_xlabel("mm, from the lens axis")
        ax.grid(alpha=0.2)
    axes[0].set_ylabel("mm, from the lens axis (up = toward the top of the pod)")
    fig.suptitle("Camera Module 3 Wide on the pod, from Raspberry Pi's drawing: board (dashed), its 4 holes (green),\n"
                 "10.8 mm housing (grey) and lens; the pod (orange) cut 3.3 mm in front of the board; red: housing inside the pod", fontsize=11)
    fig.tight_layout()
    RENDERS.mkdir(exist_ok=True)
    fig.savefig(RENDERS / "cm3w_fit.png", dpi=110)


if __name__ == "__main__":
    main()
