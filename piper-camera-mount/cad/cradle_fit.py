#!/usr/bin/env python3
"""The 6 mm lens's thumbscrews in the old O33 cradle and in the O43 one, as a GIF.

The 6 mm lens has two locking thumbscrews (lenses.py: about 5 mm proud of the barrel, measured
off product photos). Focusing turns the aperture ring, and the focus ring's screw stays wherever
that ring was locked, so either can end up pointing anywhere round the lens. This turns each
screw once round the lens and draws the bracket cut through that screw, seen from in front of
the lens, with the part of the screw that would be inside the bracket in red:

  left   the bracket as printed in PLA on 2026-10-08: a O33 cradle the length of the lens;
  right  the bracket now: O43 from the pod to just past the aperture screw, O33 after that.

The red is the screw's outline in the section; the mm3 figures are the 3D overlap of the whole
screw with the bracket (piper_mount.overlap), every 10 degrees, also in ../exports/cradle_fit.json.

    python cradle_fit.py      # -> ../renders/cradle_fit.gif, ../exports/cradle_fit.json
"""
from __future__ import annotations

import dataclasses
import io
import json
import math
import subprocess
from pathlib import Path

import cadquery as cq
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
from matplotlib.patches import Circle, PathPatch  # noqa: E402
from matplotlib.path import Path as MPath  # noqa: E402
from PIL import Image  # noqa: E402
from shapely.geometry import LineString, Polygon  # noqa: E402
from shapely.ops import polygonize, unary_union  # noqa: E402

import piper_mount as pm  # noqa: E402
from lenses import lens_screws_local  # noqa: E402
from render import mesh  # noqa: E402

HERE = Path(__file__).resolve().parent
EXPORTS = HERE.parent / "exports"
RENDERS = HERE.parent / "renders"
STEP = 10                       # degrees between frames
ORANGE = pm.ORANGE
RED = (0.88, 0.08, 0.08)
TAN = pm.COLORS["hq_lens_screws"]


def old_bracket(p: pm.Params) -> cq.Workplane:
    """The bracket with the cradle it had before: the lens grown by 1.5 mm, nothing for the screws."""
    def lens_only(lens, seat_z, c):
        return pm.cyl_z(lens.od + 2 * c, seat_z - lens.front_s - c, seat_z)
    keep = pm.lens_keepout_local
    pm.lens_keepout_local = lens_only
    try:
        return pm.make_bracket(p)
    finally:
        pm.lens_keepout_local = keep


def one_screw(p: pm.Params, i: int, a: float) -> cq.Workplane:
    """Screw i alone (0 focus, 1 aperture) pointing a degrees round the axis from the camera's +X."""
    lens = p.lens_spec
    one = dataclasses.replace(lens, screws=(lens.screws[i],))
    return pm.hq_place(p)(lens_screws_local(one, -p.hq_cs_seat, (a,)))


class Frame:
    """The HQ's axis: 2D coordinates in a plane square to it, as seen from in front of the lens."""

    def __init__(self, p: pm.Params):
        o, d, up = (np.array(v.toTuple()) for v in pm.optical_axes(p)["hq"])
        up = up - d * up.dot(d)
        self.o, self.d = o, d
        self.up = up / np.linalg.norm(up)
        self.left = np.cross(self.up, d)          # screen right for a viewer looking back along -d
        self.front_s = p.lens_spec.front_s
        place = pm.hq_place(p)
        v0, vx, vy = (np.array(place(cq.Workplane().add(cq.Vertex.makeVertex(*pt))).val().toTuple())
                      for pt in ((0, 0, 0), (1, 0, 0), (0, 1, 0)))
        self.ex, self.ey = vx - v0, vy - v0        # the camera's local +X (where screw angles start) and +Y

    def centre(self, s: float) -> np.ndarray:
        return self.o - self.d * (self.front_s - s)

    def xy(self, pt, s: float) -> tuple[float, float]:
        v = np.asarray(pt) - self.centre(s)
        return float(v.dot(self.left)), float(v.dot(self.up))

    def screw_dir(self, a: float) -> tuple[float, float]:
        """Unit 2D direction of a screw at angle a (local +X turned a degrees about local +Z)."""
        w = self.ex * math.cos(math.radians(a)) + self.ey * math.sin(math.radians(a))
        return float(w.dot(self.left)), float(w.dot(self.up))


def section(solid: cq.Workplane, m, fr: Frame, s: float):
    """The solid cut by the plane square to the axis at s, as a shapely shape in the frame's 2D."""
    sl = m.slice(normal=tuple(fr.d), origin=tuple(fr.centre(s)))
    segs = []
    for i in range(sl.n_cells):
        pts = sl.points[sl.get_cell(i).point_ids]
        segs += [LineString([fr.xy(a, s), fr.xy(b, s)]) for a, b in zip(pts[:-1], pts[1:])]
    faces = []
    for poly in polygonize(unary_union(segs)):
        x, y = poly.representative_point().coords[0]
        pt = fr.centre(s) + fr.left * x + fr.up * y
        if solid.val().isInside(cq.Vector(*pt), 1e-4):
            faces.append(poly)
    return unary_union(faces)


def add_shape(ax, shape, **kw):
    geoms = getattr(shape, "geoms", [shape])
    for g in geoms:
        if g.is_empty or not isinstance(g, Polygon):
            continue
        verts, codes = [], []
        for ring in (g.exterior, *g.interiors):
            c = list(ring.coords)
            verts += c
            codes += [MPath.MOVETO] + [MPath.LINETO] * (len(c) - 2) + [MPath.CLOSEPOLY]
        ax.add_patch(PathPatch(MPath(verts, codes), **kw))


def main() -> None:
    p = pm.Params()
    parts = pm.build(p)
    lens = p.lens_spec
    brackets = {"old": old_bracket(p), "new": parts["bracket"]}
    vols = {k: round(b.val().Volume() / 1000, 2) for k, b in brackets.items()}
    print("bracket volumes (cm3):", vols, flush=True)
    fr = Frame(p)
    meshes = {k: mesh(b, 0.03) for k, b in brackets.items()}
    rows = [(i, s, what) for i, (s, what) in reversed(list(enumerate(lens.screws)))]   # aperture first
    sections = {(k, i): section(brackets[k], meshes[k], fr, s) for k in brackets for i, s, _ in rows}
    angles = list(range(0, 360, STEP))
    vol = {(k, i): [pm.overlap(one_screw(p, i, a), brackets[k]) for a in angles] for k in brackets for i, _, _ in rows}
    print({f"{k} screw {i}": sum(v > 0.05 for v in vs) for (k, i), vs in vol.items()}, flush=True)
    x0, y0, x1, y1 = unary_union(list(sections.values())).bounds
    rr = lens.screw_tip_r + 2
    lim = (min(x0, -rr) - 2, max(x1, rr) + 2), (min(y0, -rr) - 2, max(y1, rr) + 2)

    frames = []
    for n, a in enumerate(angles):
        fig, axes = plt.subplots(2, 2, figsize=(10.4, 10.0), dpi=80)
        for r, (i, s, what) in enumerate(rows):
            r0 = lens.d_at(s) / 2 - 0.5
            ux, uy = fr.screw_dir(a)
            nx, ny = -uy, ux
            w = lens.screw_d / 2
            bar = Polygon([(ux * r0 + nx * w, uy * r0 + ny * w), (ux * lens.screw_tip_r + nx * w, uy * lens.screw_tip_r + ny * w),
                           (ux * lens.screw_tip_r - nx * w, uy * lens.screw_tip_r - ny * w), (ux * r0 - nx * w, uy * r0 - ny * w)])
            for c, k in enumerate(("old", "new")):
                ax = axes[r][c]
                sec = sections[(k, i)]
                add_shape(ax, sec, facecolor=ORANGE, edgecolor=(0.45, 0.2, 0.05), lw=1.0)
                ax.add_patch(Circle((0, 0), lens.d_at(s) / 2, facecolor=(0.1, 0.1, 0.11), edgecolor="none"))
                ax.add_patch(Circle((0, 0), lens.screw_tip_r, fill=False, ls="--", lw=1.0, ec=(0.4, 0.4, 0.4)))
                hit = bar.intersection(sec)
                add_shape(ax, bar, facecolor=TAN, edgecolor=(0.35, 0.3, 0.2), lw=0.8)
                add_shape(ax, hit, facecolor=RED, edgecolor=RED, lw=0.8)
                v = vol[(k, i)][n]
                ax.set_xlim(*lim[0])
                ax.set_ylim(*lim[1])
                ax.set_aspect("equal")
                ax.set_xticks([])
                ax.set_yticks([])
                for sp in ax.spines.values():
                    sp.set_visible(False)
                hits = sum(x > 0.05 for x in vol[(k, i)])
                ax.set_title(f"{what} screw, {s:g} mm out: hits at {hits} of 36 angles", fontsize=11,
                             color=(0.2, 0.2, 0.2))
                ax.set_xlabel(f"cuts {v:.0f} mm³ into the bracket" if v > 0.05 else "clear of the bracket",
                              fontsize=13, color=RED if v > 0.05 else (0.1, 0.5, 0.15), fontweight="bold")
        fig.text(0.27, 0.955, "Before: O33 cradle\n(the PLA bracket of 8 October)", ha="center", va="top",
                 fontsize=14, fontweight="bold")
        fig.text(0.76, 0.955, "Now: O43 round the screws", ha="center", va="top", fontsize=14, fontweight="bold")
        fig.suptitle(f"Cut through each thumbscrew, seen from in front of the lens. Screws turned to {a} degrees",
                     fontsize=12, y=0.995)
        fig.text(0.5, 0.008, "dashed: the circle the screw tips sweep (20 mm radius, 5 mm proud: an estimate from "
                 "photos)", ha="center", fontsize=10, color=(0.35, 0.35, 0.35))
        fig.tight_layout(rect=(0, 0.02, 1, 0.9))
        buf = io.BytesIO()
        fig.savefig(buf, format="png")
        plt.close(fig)
        frames.append(Image.open(buf).convert("RGB"))

    out = RENDERS / "cradle_fit.gif"
    frames[0].save(out, save_all=True, append_images=frames[1:], duration=300, loop=0)
    subprocess.run(["gifsicle", "-b", "-O3", "--colors", "64", str(out)], check=False)
    table = {}
    for i, s, what in rows:
        table[f"{what} thumbscrew, {s:g} mm in front of the CS seat"] = {
            "angles (deg, round the axis from the camera's +X)": angles,
            **{f"cuts into the {k} bracket (mm3)": [round(v, 1) for v in vol[(k, i)]] for k in brackets},
            **{f"angles that hit the {k} bracket": sum(v > 0.05 for v in vol[(k, i)]) for k in brackets},
            **{f"most it cuts into the {k} bracket (mm3)": round(max(vol[(k, i)]), 1) for k in brackets},
        }
    (EXPORTS / "cradle_fit.json").write_text(json.dumps({
        "what": "The 6 mm lens's two thumbscrews (lenses.py) against the bracket's lens cradle: old, O33 the length "
                "of the lens; new, O43 from the pod to just past the aperture screw. Each screw alone, every 10 "
                "degrees round the lens; overlap in mm3 (piper_mount.overlap).",
        "bracket volume (cm3)": vols,
        "screws": table,
    }, indent=2) + "\n")
    print(json.dumps({k: {kk: vv for kk, vv in v.items() if not isinstance(vv, list)} for k, v in table.items()},
                     indent=1))


if __name__ == "__main__":
    main()
