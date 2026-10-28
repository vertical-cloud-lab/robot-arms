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


def stl_check(name: str, part: cq.Workplane) -> dict:
    """The part's bounding box and volume against its STL in ../exports (binary, from cadquery)."""
    data = (EXPORTS / f"{name}.stl").read_bytes()
    n = int.from_bytes(data[80:84], "little")
    tri = np.dtype([("normal", "<f4", 3), ("v", "<f4", (3, 3)), ("attr", "<u2")])
    v = np.frombuffer(data, tri, count=n, offset=84)["v"].astype(float)
    stl_vol = float(np.einsum("ij,ij->i", v[:, 0], np.cross(v[:, 1], v[:, 2])).sum() / 6)
    bb = part.val().BoundingBox()
    lo, hi = v.reshape(-1, 3).min(0), v.reshape(-1, 3).max(0)
    bb_err = float(np.abs(np.r_[lo, hi] - [bb.xmin, bb.ymin, bb.zmin, bb.xmax, bb.ymax, bb.zmax]).max())
    vol = sum(s.Volume() for s in part.solids().vals())
    return {"volume_mm3": round(vol, 1), "stl_volume_mm3": round(stl_vol, 1),
            "volume_diff_pct": round(100 * (vol - stl_vol) / stl_vol, 3), "bbox_diff_mm": round(bb_err, 4),
            "solids": len(part.solids().vals()), "ok": bb_err < 0.05 and abs(vol - stl_vol) < 0.005 * stl_vol}


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
    args = ap.parse_args()
    assy, report = plate(Params())
    print(json.dumps(report, indent=2))
    if not all(report[name]["ok"] for name in PRINTED):
        raise SystemExit("a part doesn't match its STL; re-export before uploading")
    assy.export(str(args.out))
    print(f"wrote {args.out}")


if __name__ == "__main__":
    main()
