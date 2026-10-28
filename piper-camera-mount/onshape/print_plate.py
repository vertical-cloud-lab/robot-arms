#!/usr/bin/env python3
"""The printed parts as one STEP, laid out the way they print, for Onshape's "Print plate" tab.

Each part is read back from its STEP in ../exports, turned into its print orientation with
piper_mount.print_orientation (the same turn the STLs are exported with), and put where the
A1 mini plate puts it: render.PRINT_LAYOUT, the centre of the part's footprint on the
180 x 180 mm bed, with the bed's corner at the origin and +Z up. "tag_wedge#2" is a second
copy of tag_wedge. Nothing is rebuilt, so the plate is exactly the committed exports.

Each part is then checked against its STL, which is what the slicer printed: the bounding
boxes must agree to 0.05 mm and the volumes to 0.5 % (the STLs are tessellated at 0.02 mm).

    python print_plate.py            # writes /tmp/print_plate.step, prints the check
    python print_plate.py --out FILE
    python print_plate.py --check-stl plate.stl   # an STL exported from Onshape's Print plate tab

--check-stl measures an exported mesh against the plate: its bounding box and volume, and how far
its facets cut inside each vertical round hole, bore or boss (the sagitta between neighbouring
points on the circle), by diameter.
"""
from __future__ import annotations

import sys

sys.dont_write_bytecode = True  # importing ../cad/render.py leaves no __pycache__ in cad/

import argparse
import json
from pathlib import Path

import cadquery as cq
import numpy as np

HERE = Path(__file__).resolve().parent
EXPORTS = HERE.parent / "exports"
sys.path.insert(0, str(HERE.parent / "cad"))
from piper_mount import COLORS, PRINTED, Params, print_orientation  # noqa: E402
from render import PRINT_LAYOUT  # noqa: E402  (imports pyvista, like slice_a1mini.py does)


def read_stl(path: Path) -> np.ndarray:
    """Triangles of a binary STL, (n, 3, 3)."""
    data = path.read_bytes()
    n = int.from_bytes(data[80:84], "little")
    tri = np.dtype([("normal", "<f4", 3), ("v", "<f4", (3, 3)), ("attr", "<u2")])
    return np.frombuffer(data, tri, count=n, offset=84)["v"].astype(float)


def stl_check(name: str, part: cq.Workplane) -> dict:
    """The part's bounding box and volume against its STL in ../exports (binary, from cadquery)."""
    v = read_stl(EXPORTS / f"{name}.stl")
    stl_vol = float(np.einsum("ij,ij->i", v[:, 0], np.cross(v[:, 1], v[:, 2])).sum() / 6)
    bb = part.val().BoundingBox()
    lo, hi = v.reshape(-1, 3).min(0), v.reshape(-1, 3).max(0)
    bb_err = float(np.abs(np.r_[lo, hi] - [bb.xmin, bb.ymin, bb.zmin, bb.xmax, bb.ymax, bb.zmax]).max())
    vol = sum(s.Volume() for s in part.solids().vals())
    return {"volume_mm3": round(vol, 1), "stl_volume_mm3": round(stl_vol, 1),
            "volume_diff_pct": round(100 * (vol - stl_vol) / stl_vol, 3), "bbox_diff_mm": round(bb_err, 4),
            "solids": len(part.solids().vals()), "ok": bb_err < 0.05 and abs(vol - stl_vol) < 0.005 * stl_vol}


def mesh_check(path: Path, assy: cq.Assembly) -> dict:
    """An exported plate against the exact one: bounding box, volume, and the worst sagitta per
    vertical round hole diameter. Only edges between points less than 20 degrees apart on a circle
    count, so the long edges a flat face's triangulation runs between the ends of an arc don't."""
    t = read_stl(path)
    pts = t.reshape(-1, 3)
    solids = cq.Compound.makeCompound([x for c in assy.children for x in c.obj.solids().vals()])
    bb = solids.BoundingBox()
    exact = sum(x.Volume() for x in solids.Solids())
    vol = float(np.einsum("ij,ij->i", t[:, 0], np.cross(t[:, 1], t[:, 2])).sum() / 6)
    edges = np.concatenate([t[:, [0, 1]], t[:, [1, 2]], t[:, [2, 0]]])
    sag: dict[float, float] = {}
    for f in solids.Faces():
        if f.geomType() != "CYLINDER":
            continue
        cyl = f._geomAdaptor().Cylinder()
        if abs(cyl.Axis().Direction().Z()) < 0.999:
            continue
        r, c = cyl.Radius(), np.array([cyl.Axis().Location().X(), cyl.Axis().Location().Y()])
        fb = f.BoundingBox()
        lo, hi = np.array([fb.xmin, fb.ymin, fb.zmin]) - 1e-3, np.array([fb.xmax, fb.ymax, fb.zmax]) + 1e-3
        rel = edges[:, :, :2] - c
        on = (np.abs(np.linalg.norm(rel, axis=2) - r) < 0.003).all(1) & ((edges >= lo) & (edges <= hi)).all((1, 2))
        a = np.arctan2(rel[on][:, :, 1], rel[on][:, :, 0])
        step = np.abs((a[:, 0] - a[:, 1] + np.pi) % (2 * np.pi) - np.pi)
        mid = edges[on][(step > 1e-6) & (step < np.radians(20))].mean(1)
        if len(mid):
            d = round(2 * r, 2)
            sag[d] = max(sag.get(d, 0.0), round(float(r - np.linalg.norm(mid[:, :2] - c, axis=1).min()), 4))
    return {"file": path.name, "triangles": len(t),
            "bbox_diff_mm": round(float(np.abs(np.r_[pts.min(0), pts.max(0)] - [bb.xmin, bb.ymin, bb.zmin, bb.xmax,
                                                                                  bb.ymax, bb.zmax]).max()), 4),
            "volume_mm3": round(vol, 1), "exact_volume_mm3": round(exact, 1),
            "volume_diff_pct": round(100 * (vol - exact) / exact, 3),
            "max_sagitta_mm_by_diameter": dict(sorted(sag.items()))}


def plate(p: Params) -> tuple[cq.Assembly, dict]:
    assy, report = cq.Assembly(name="print_plate"), {}
    oriented = {}
    for name in PRINTED:
        # One compound per part, as build() makes it: the 4 spacers are one union, and
        # print_orientation centres the footprint of val() only.
        solids = cq.importers.importStep(str(EXPORTS / f"{name}.step")).solids().vals()
        oriented[name] = print_orientation(name, cq.Workplane(obj=cq.Compound.makeCompound(solids)), p)
        report[name] = stl_check(name, oriented[name])
    report["placed"] = {}
    for key, (x, y) in PRINT_LAYOUT.items():
        name = key.split("#")[0]
        bb = oriented[name].val().BoundingBox()          # print_orientation centres the footprint
        assy.add(oriented[name].translate((x, y, 0)), name=key.replace("#", "_"), color=cq.Color(*COLORS[name]))
        report["placed"][key] = {"footprint_centre_mm": [x, y], "size_mm": [round(bb.xlen, 2), round(bb.ylen, 2),
                                                                          round(bb.zlen, 2)]}
    return assy, report


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--out", type=Path, default=Path("/tmp/print_plate.step"))
    ap.add_argument("--check-stl", type=Path, help="an STL of the plate exported from Onshape, to measure")
    args = ap.parse_args()
    assy, report = plate(Params())
    if args.check_stl:
        print(json.dumps(mesh_check(args.check_stl, assy), indent=2))
        return
    print(json.dumps(report, indent=2))
    if not all(report[name]["ok"] for name in PRINTED):
        raise SystemExit("a part doesn't match its STL; re-export before uploading")
    assy.export(str(args.out))
    print(f"wrote {args.out}")


if __name__ == "__main__":
    main()
