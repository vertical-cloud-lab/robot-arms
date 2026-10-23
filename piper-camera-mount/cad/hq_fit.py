#!/usr/bin/env python3
"""The HQ Camera's housing against the pod: as printed on 13 October, and now.

The pod printed on 13 October was cut for the housing as first modelled, a round body with a
plain 13.97 mm tripod foot and a focus-lock block. Raspberry Pi's drawing (RP-008200-DS-1) and
photos show more than that: the tripod mount flares out into two shoulders just under the
focus ring, a screw sits in each shoulder, and the whole housing is 51.9 mm from the top of the
lock block to the foot. This builds both pods, measures each against the housing as the drawing
has it, and draws the plate sectioned through its middle, seen from the front.

    python hq_fit.py        # writes exports/hq_fit.json and renders/hq_fit.png
"""
from __future__ import annotations

import json
from pathlib import Path

import cadquery as cq
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.collections import PolyCollection

import piper_mount as pm

HERE = Path(__file__).resolve().parent
OUT = HERE.parent


def printed_station_cuts(p: pm.Params) -> cq.Workplane:
    """hq_station_cuts as it was for the pod printed on 13 October (commit b6e2da0)."""
    s = p.hq_standoff
    cut = pm.cyl_z(p.hq_hole_d, -80, -s + 0.5)
    cut = cut.union(pm.lbox(-8.0, 8.0, -p.hq_board / 2 - 12.2, -14.0, -80, -s + 0.5))        # tripod foot
    cut = cut.union(pm.lbox(-6.0, 6.0, 14.0, p.hq_board / 2 + 2.5, -80, -s + 0.5))          # focus lock
    for x, y in pm.hq_holes(p):
        cut = cut.union(pm.cyl_z(p.m25_clear_d, -80, 5, x, y))
        cut = cut.union(pm.cyl_z(5.0, -80, -s - p.pod_t + 2.0, x, y))
    return cut


def pod_in_camera_frame(p: pm.Params, printed: bool) -> cq.Workplane:
    """make_pod_local() taken into the HQ Camera's own frame (board face at z = 0, lens toward -z)."""
    keep = pm.hq_station_cuts
    if printed:
        pm.hq_station_cuts = printed_station_cuts
    try:
        pod = pm.make_pod_local(p)
    finally:
        pm.hq_station_cuts = keep
    # inverse of hq_to_station: station (x, y, z) = (-y_cam, z_cam, -x_cam)
    return pod.rotate((0, 0, 0), (1, 0, 0), 90).rotate((0, 0, 0), (0, 0, 1), -p.hq_roll)


def features(p: pm.Params) -> dict[str, cq.Workplane]:
    """The parts of the housing the pocket has to clear, in the camera frame."""
    tripod = pm._poly_z(pm.hq_tripod_outline(), -p.hq_housing_front, 0)
    w, y0, y1 = pm.HQ_LOCK_BLOCK
    return {
        "shoulders and foot of the tripod mount": tripod,
        "screws in the shoulders": pm.hq_tripod_screws_local(),
        "focus-lock block": pm.lbox(-w, w, y0, y1, -p.hq_housing_front, -5.07),
        "round housing and focus ring": pm.cyl_z(36.0, -p.hq_cs_seat, -p.hq_cs_seat + 5.8).union(
            pm.cyl_z(p.hq_housing_d, -p.hq_cs_seat + 5.8, 0)),
    }


def faces_2d(wp: cq.Workplane) -> list:
    polys = []
    for f in wp.faces().vals():
        verts, tris = f.tessellate(0.02, 0.2)
        polys += [[(verts[i].x, verts[i].y) for i in t] for t in tris]
    return polys


def section(wp: cq.Workplane, z: float) -> cq.Workplane:
    slab = pm.lbox(-80, 80, -80, 80, z - 0.01, z + 0.01)
    return wp.intersect(slab).faces(">Z")


def main() -> None:
    p = pm.Params()
    feats = features(p)
    res = {"source": "Raspberry Pi RP-008200-DS-1 (HQ Camera CS mechanical drawing), measured off the PDF's "
                     "linework; screw heads placed from Raspberry Pi's photos",
           "pocket clearance (mm)": p.hq_pocket_c, "pods": {}}
    pods = {"printed 13 October": pod_in_camera_frame(p, True), "now": pod_in_camera_frame(p, False)}
    for name, pod in pods.items():
        r = {}
        for fn, f in feats.items():
            r[fn] = {"overlap_mm3": round(pm.overlap(f, pod), 1), "gap_mm": round(pm.gap(f, pod), 2)}
        res["pods"][name] = r
    w, _, y1 = pm.HQ_LOCK_BLOCK
    res["housing, top of the lock block to the end of the foot (mm)"] = round(y1 + 30.35, 2)
    res["shoulders across (mm)"] = 2 * 12.07
    res["screw heads across, outside to outside (mm)"] = round(2 * max(
        abs(x) for x, _ in _screw_corners()), 2)
    (OUT / "exports" / "hq_fit.json").write_text(json.dumps(res, indent=2) + "\n")
    print(json.dumps(res, indent=2))

    # The plate sectioned through its middle (4 mm standoff + half of the 6 mm plate), from the front.
    z = -p.hq_standoff - p.pod_t / 2
    fig, axs = plt.subplots(1, 2, figsize=(12, 7.8))
    for ax, (name, pod) in zip(axs, pods.items()):
        plate = section(pod, z)
        orange = (0.96, 0.58, 0.20)
        ax.add_collection(PolyCollection(faces_2d(plate), facecolor=orange, edgecolor=orange, linewidth=0.3))
        for fn, f in feats.items():
            sec = section(f, z) if fn != "screws in the shoulders" else section(f, pm.HQ_TRIPOD_SCREW[2])
            grey = (0.36, 0.36, 0.38)
            ax.add_collection(PolyCollection(faces_2d(sec), facecolor=grey, edgecolor=grey, linewidth=0.3))
            hit = f.intersect(pod)
            if hit.solids().size():
                sh = section(hit, z) if fn != "screws in the shoulders" else section(hit, pm.HQ_TRIPOD_SCREW[2])
                red = (0.85, 0.05, 0.1)
                ax.add_collection(PolyCollection(faces_2d(sh), facecolor=red, edgecolor=red, linewidth=1.5))
        b = p.hq_board / 2
        ax.plot([-b, b, b, -b, -b], [-b, -b, b, b, -b], color=(0.12, 0.48, 0.25), lw=1.2, ls="--")
        for x, y in pm.hq_holes(p):
            ax.add_patch(plt.Circle((x, y), 1.25, fill=False, color=(0.12, 0.48, 0.25), lw=1))
        r = res["pods"][name]
        lines = [f"{k}: " + ("clear by %.2f mm" % v["gap_mm"] if v["overlap_mm3"] == 0
                             else "hits it (%.0f mm³)" % v["overlap_mm3"]) for k, v in r.items()]
        ax.set_title(f"Pod {name}", fontsize=13, loc="left")
        ax.text(0.0, -0.1, "\n".join(lines), transform=ax.transAxes, va="top", fontsize=9.5)
        ax.set_xlim(-30, 30)
        ax.set_ylim(-36, 27)
        ax.set_aspect("equal")
        ax.set_xlabel("mm, across the camera")
        ax.grid(alpha=0.25)
    axs[0].set_ylabel("mm, up the camera (focus lock at the top, tripod foot at the bottom)")
    fig.suptitle("HQ Camera in the pod, seen from the lens side, plate cut through its middle: "
                 "orange = pod, grey = camera housing (Raspberry Pi's drawing), red = overlap, "
                 "green dashes = board", fontsize=9.5)
    fig.tight_layout(rect=(0, 0.12, 1, 0.97))
    (OUT / "renders").mkdir(exist_ok=True)
    fig.savefig(OUT / "renders" / "hq_fit.png", dpi=130)
    print("wrote", OUT / "renders" / "hq_fit.png")


def _screw_corners():
    d, h = pm.HQ_TRIPOD_SCREW_HEAD
    out = []
    for start, axis in pm.hq_tripod_screw_heads():
        perp = cq.Vector(-axis.y, axis.x, 0) * (d / 2)
        end = start + axis * (h + 1.0)
        out += [(q.x, q.y) for q in (start - perp, end - perp, end + perp, start + perp)]
    return out


if __name__ == "__main__":
    main()
