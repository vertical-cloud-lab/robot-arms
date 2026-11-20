#!/usr/bin/env python3
"""Build the AprilTag cubes in cubes.yaml: print files and the tag corners for pose estimation.

    pip install -r requirements.txt
    python make_cubes.py                 # every part in cubes.yaml
    python make_cubes.py W1 A_collar     # just these

Writes, for every part:
    print/<part>.3mf          open in Bambu Studio or OrcaSlicer: one object, two parts,
                              white body = filament 1, black tag cells = filament 2,
                              already turned the way it should print
    print/<part>_white.stl    the same two solids as STLs, for other slicers (load both at
    print/<part>_black.stl    once and say yes to "load as a single object with multiple parts")
and print/all_parts_H2D.3mf: every part on one H2D plate (black in one nozzle, white in the
other: the colour changes are per layer, so one plate costs the same changes as one part).
and cube_tags.yaml: every tag's ID, cube, face, size and its four corners in its part's frame
(the destination's frame: the table's edge, the PiPER's base, the shelf's corner, ...).
"""
from __future__ import annotations

import argparse
import os
import sys

import numpy as np
import yaml

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import tag_cubes as tc  # noqa: E402

PLA_DENSITY = 1.24  # g/cm^3
# Where both of the H2D's nozzles reach (Bambu Studio's H2D profile, extruder_printable_area:
# left nozzle x 0-325, right 25-350, y 0-320). The back-right corner is kept clear for the
# prime tower (Bambu Studio 2.9.1 sliced this plate with the tower's corner at x 255, y 245).
H2D_BOTH = (25.0, 325.0, 0.0, 320.0)
TOWER_SPOT = (245.0, 325.0, 235.0, 320.0)
GAP = 10.0                  # mm between parts on the plate


def arrange(sizes, area=H2D_BOTH, keep_clear=TOWER_SPOT, gap=GAP):
    """Shelf-pack footprints (w, d) into area (x0, x1, y0, y1), around the keep_clear
    rectangle; returns their centres, or None if they don't fit."""
    x0, x1, y0, y1 = area
    kx0, kx1, ky0, ky1 = keep_clear
    order = sorted(range(len(sizes)), key=lambda i: -sizes[i][1])
    out, x, y, row_d = [None] * len(sizes), x0 + gap, y0 + gap, 0.0
    for i in order:
        w, d = sizes[i]
        while True:
            if x + w + gap > x1:
                x, y, row_d = x0 + gap, y + row_d + gap, 0.0
            if y + d + gap > y1:
                return None
            if x < kx1 and x + w > kx0 and y < ky1 and y + d > ky0:  # would cover the tower spot
                x = x1  # next row
                continue
            break
        out[i] = (x + w / 2, y + d / 2)
        x, row_d = x + w + gap, max(row_d, d)
    return out


def load(path=os.path.join(HERE, "cubes.yaml")) -> dict:
    with open(path) as f:
        return yaml.safe_load(f)


def build_all(cfg: dict, only=None) -> list:
    parts = []
    for p in cfg["parts"]:
        if only and p["name"] not in only:
            continue
        parts.append(tc.build_part(p, cfg.get("style", {}), cfg.get("family", "tag36h11")))
    return parts


def _r(a, nd=3):
    return [round(float(x), nd) for x in np.ravel(a)]


def tags_yaml(parts: list, family: str) -> dict:
    out = {"family": family,
           "units": "mm",
           "corners": "top-left, top-right, bottom-right, bottom-left of the black square as "
                      "printed (upright = the official AprilTag image). To match a detector's "
                      "order, take corners[i] for i in: " + ", ".join(
                          f"{k} {v}" for k, v in tc.CORNER_ORDER.items() if k != "stored"),
           "R": "columns: the tag's x (right), y (up) and z (out of the face) in the part frame",
           "parts": {}}
    for p in parts:
        out["parts"][p.name] = {
            "mount": p.mount, "frame": p.frame, "notes": p.notes,
            "cubes": {pl.spec.name: {"edge": round(pl.spec.edge, 3), "pose": [_r(row, 4) for row in pl.T]}
                      for pl in p.cubes},
            "tags": {int(t["id"]): {"cube": t["cube"], "face": t["face"], "size": t["size"],
                                    "center": _r(t["center"]), "R": [_r(row, 6) for row in t["R"]],
                                    "corners": [_r(c) for c in t["corners"]]}
                     for t in p.tags}}
    return out


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("parts", nargs="*", help="part names from cubes.yaml (default: all)")
    ap.add_argument("--config", default=os.path.join(HERE, "cubes.yaml"))
    ap.add_argument("--out", default=os.path.join(HERE, "print"))
    a = ap.parse_args(argv)
    cfg = load(a.config)
    os.makedirs(a.out, exist_ok=True)
    parts = build_all(cfg, set(a.parts) or None)
    print(f"{'part':9s} {'cubes':12s} {'edge mm':>8s} {'print size mm':>20s} {'white g':>8s} "
          f"{'black g':>8s} {'2-colour layers':>15s}  tag IDs")
    plate_items = []
    for p in parts:
        for m, label in ((p.white, "white"), (p.black, "black")):
            if m.status() != tc.m3d.Error.NoError or m.is_empty():
                raise SystemExit(f"{p.name}: the {label} solid is not a valid manifold ({m.status()})")
        w, b = p.solids_for_print()
        bb = np.maximum(w.bounding_box()[3:], b.bounding_box()[3:]) - np.minimum(
            w.bounding_box()[:3], b.bounding_box()[:3])
        tc.write_3mf(os.path.join(a.out, f"{p.name}.3mf"), p.name, w, b)
        plate_items.append((p.name, w, b, (bb[0], bb[1])))
        layers = tc.colour_layers(w, b)
        tc.write_stl(os.path.join(a.out, f"{p.name}_white.stl"), w)
        tc.write_stl(os.path.join(a.out, f"{p.name}_black.stl"), b)
        ids = sorted(t["id"] for t in p.tags)
        edges = sorted({round(pl.spec.edge, 1) for pl in p.cubes})
        print(f"{p.name:9s} {','.join(pl.spec.name for pl in p.cubes):12s} "
              f"{'/'.join(map(str, edges)):>8s} {' x '.join(f'{v:.0f}' for v in bb):>20s} "
              f"{w.volume() / 1000 * PLA_DENSITY:8.1f} {b.volume() / 1000 * PLA_DENSITY:8.1f} {layers:15d}  "
              f"{ids[0]}-{ids[-1]} ({len(ids)})")
    if not a.parts:
        spots = arrange([it[3] for it in plate_items])
        if spots is None:
            print("the parts don't fit on one H2D plate: print them in two batches")
        else:
            tc.write_3mf_plate(os.path.join(a.out, "all_parts_H2D.3mf"),
                               [(n, w, b, xy) for (n, w, b, _), xy in zip(plate_items, spots)],
                               filament_maps="1 2")  # white: left nozzle, black: right
            print(f"all {len(plate_items)} parts fit on one H2D plate: print/all_parts_H2D.3mf")
    # cube_tags.yaml covers every part in cubes.yaml, so rebuild it from all of them.
    allp = parts if not a.parts else build_all(cfg)
    with open(os.path.join(HERE, "cube_tags.yaml"), "w") as f:
        f.write("# Generated by make_cubes.py from cubes.yaml: do not edit by hand.\n")
        yaml.safe_dump(tags_yaml(allp, cfg.get("family", "tag36h11")), f, sort_keys=False,
                       default_flow_style=None, width=120)
    print("grams are solid PLA; the slicer's infill makes the white lighter. A 2-colour layer costs two "
          "filament changes on one nozzle (A1 mini + AMS lite) and two nozzle switches on the H2D")
    print(f"wrote {a.out}/ and cube_tags.yaml")


if __name__ == "__main__":
    main()
