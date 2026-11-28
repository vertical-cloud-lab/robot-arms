"""Scenario: where on the build plate can the arm pick something up?

For a grid of points on the plate (bed where cell_layout.yaml puts it), solve the grasp the
planner would use (fingers closing across the arm's reach, leaning as little as the wrist
allows), and check the arm against the printer at the grasp and 60 mm above it. Draws the
result over the prints' footprints: output/reach_map.png.

    python run_sim.py --scenario reach_map

Use it before laying out a print job, or after moving the arm or printer in cell_layout.yaml.
"""
from __future__ import annotations

import numpy as np

from digital_twin.config import mm
from digital_twin.physics.adhesion import footprint
from digital_twin.tasks.pick_place import PickPlace

CELL_MM = 15
GRASP_Z_MM = 10  # fingertip height above the plate
# Ordinal blue steps (light -> dark = more lean), then status/neutral for the failures.
LEAN_BINS = [(0, 5, "#86b6ef", "straight down"), (5, 12.5, "#5598e7", "leaning 10°"),
             (12.5, 17.5, "#2a78d6", "leaning 15°"), (17.5, 22.5, "#1c5cab", "leaning 20°"),
             (22.5, 46, "#104281", "leaning 25-45°")]
BLOCKED = ("#d03b3b", "arm hits the printer")
NO_IK = ("#c3c2b7", "out of reach")
INK, INK2, SURFACE = "#0b0b0b", "#52514e", "#fcfcfb"


def grid(sim):
    e, cell = sim.engine, sim.cell
    pp = PickPlace(cell, sim.robot, sim.cfg)
    pp.pad_half_gap = 0.022
    # Plan on an empty plate: move the prints far away so only the cell is in the way.
    if hasattr(e, "d"):
        for n in e.print_names():
            jid = e.m.body_jntadr[e.m.body(n).id]
            adr = e.m.jnt_qposadr[jid]
            e.d.qpos[adr:adr + 3] = [5, 5, -5]
            if e.bonded(n):
                e.d.eq_active[e.bonds[n]["eq"]] = 0
        e.mujoco.mj_forward(e.m, e.d)
    q_seed = np.radians(sim.cfg.robot["joints"]["ready_deg"])
    half = sim.cfg.cell["printer"]["print_area"][0] / 2
    centers = np.arange(-half + CELL_MM / 2, half, CELL_MM)
    out = []
    for y in centers:
        for x in centers:
            p = (cell.plate_pose @ np.array([mm(x), mm(y), mm(GRASP_Z_MM), 1.0]))[:3]
            u = p[:2] - cell.arm_pose[:2, 3]
            u /= np.linalg.norm(u)
            d = np.array([-u[1], u[0], 0.0])
            sol = pp.solve_grasp(p, [d], q_seed, rise=0.06)
            if sol is None:
                out.append((x, y, "no_ik", None))
                continue
            T, q, _, q_up = sol
            hits = e.arm_collisions(q, 0.015) + e.arm_collisions(q_up, 0.015)
            lean = float(np.degrees(np.arccos(np.clip(-T[2, 2], -1, 1))))
            out.append((x, y, "blocked" if hits else "ok", lean))
    return out


def plot(sim, cells, path):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.patches import Patch, Rectangle
    from scipy.spatial import ConvexHull

    fig, ax = plt.subplots(figsize=(6.6, 7.2), dpi=150)
    fig.patch.set_facecolor(SURFACE)
    ax.set_facecolor(SURFACE)
    inset = 0.9  # mm: the surface gap between cells
    for x, y, state, lean in cells:
        if state == "ok":
            color = next(c for lo, hi, c, _ in LEAN_BINS if lo <= lean < hi)
            hatch = None
        elif state == "blocked":
            color, hatch = BLOCKED[0], "///"
        else:
            color, hatch = NO_IK[0], ".."
        ax.add_patch(Rectangle((x - CELL_MM / 2 + inset, y - CELL_MM / 2 + inset), CELL_MM - 2 * inset,
                               CELL_MM - 2 * inset, facecolor=color, edgecolor=SURFACE if not hatch else SURFACE,
                               hatch=hatch, linewidth=0))
    # Print footprints (outline of what touches the plate) with their names.
    for pr in sim.cell.prints:
        fp = footprint(pr.geoms)
        if len(fp) < 3:
            continue
        T = pr.local_pose()
        pts = (np.column_stack([fp, np.zeros(len(fp)), np.ones(len(fp))]) @ T.T)[:, :2] * 1000
        hull = ConvexHull(pts)
        ring = np.vstack([pts[hull.vertices], pts[hull.vertices[:1]]])
        ax.plot(ring[:, 0], ring[:, 1], color=INK, lw=1.2)
        c = pts.mean(0)
        ax.text(c[0], c[1], pr.name.replace("_", " "), ha="center", va="center", fontsize=6.5, color=INK,
                bbox=dict(boxstyle="round,pad=0.15", fc=SURFACE, ec="none", alpha=0.85))
    half = sim.cfg.cell["printer"]["print_area"][0] / 2
    ax.add_patch(Rectangle((-half, -half), 2 * half, 2 * half, fill=False, ec=INK2, lw=0.8, ls="--"))
    ax.set_xlim(-half - 4, half + 4)
    ax.set_ylim(-half - 4, half + 4)
    ax.set_aspect("equal")
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    for s in ("left", "bottom"):
        ax.spines[s].set_color(INK2)
    ax.tick_params(colors=INK2, labelsize=8)
    ax.set_xlabel("plate x (mm), toward the printer's right", color=INK2, fontsize=8)
    ax.set_ylabel("plate y (mm), toward the back (X arm)", color=INK2, fontsize=8)
    ax.set_title(f"Where the PiPER can grasp on the A1 mini plate (bed fully forward, "
                 f"fingertips {GRASP_Z_MM} mm up)", color=INK, fontsize=9, loc="left")
    handles = [Patch(facecolor=c, label=l) for _, _, c, l in LEAN_BINS]
    handles += [Patch(facecolor=BLOCKED[0], hatch="///", edgecolor=SURFACE, label=BLOCKED[1]),
                Patch(facecolor=NO_IK[0], hatch="..", edgecolor=SURFACE, label=NO_IK[1])]
    leg = ax.legend(handles=handles, loc="upper center", bbox_to_anchor=(0.5, -0.1), ncol=4, frameon=False,
                    fontsize=7.5)
    for t in leg.get_texts():
        t.set_color(INK)
    fig.tight_layout()
    fig.savefig(path, facecolor=SURFACE)
    plt.close(fig)


def run(sim, args) -> dict:
    cells = grid(sim)
    path = sim.cfg.path("output/reach_map.png")
    plot(sim, cells, path)
    n = len(cells)
    ok = sum(c[2] == "ok" for c in cells)
    blocked = sum(c[2] == "blocked" for c in cells)
    print(f"{ok}/{n} plate cells reachable, {blocked} blocked by the printer, {n - ok - blocked} out of reach")
    print("map:", path)
    return {"cell_mm": CELL_MM, "cells": [{"x": c[0], "y": c[1], "state": c[2], "lean_deg": c[3]} for c in cells]}
