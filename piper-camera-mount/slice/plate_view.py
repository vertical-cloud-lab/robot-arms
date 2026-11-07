#!/usr/bin/env python3
"""Draw the sliced H2D plate from its own G-code: a still and a layer-by-layer GIF.

    xvfb-run -a python plate_view.py            # -> ../renders/h2d_plate.png, h2d_plate_build.gif

Reads Metadata/plate_1.gcode out of piper_camera_mount_H2D_PAHT-CF.3mf (slice_h2d.py) and the
layout out of report_h2d.json. Every extrusion move (G1, and G2/G3 arcs split into short chords)
becomes a line on the H2D's 350 x 320 mm bed, coloured by what Bambu labels it: walls, sparse
infill, or solid fill (top, bottom, internal solid, bridges). Travel, wipes, retractions and the
start G-code's purge lines are left out. The strip only the right nozzle reaches, x 325 to 350
mm, is shaded. Times in the GIF are Bambu's own, from the M73 R (minutes left) lines.
"""
from __future__ import annotations

import sys

sys.dont_write_bytecode = True

import argparse
import json
import math
import re
import zipfile
from pathlib import Path

import numpy as np
import pyvista as pv
from PIL import Image

HERE = Path(__file__).resolve().parent
RENDERS = HERE.parent / "renders"
THREE_MF = HERE / "piper_camera_mount_H2D_PAHT-CF.3mf"
BED = (350.0, 320.0)
LEFT_REACH = 325.0
# Bambu's feature labels, folded into three groups, in the categorical palette's first three slots
GROUPS = {"Outer wall": 0, "Inner wall": 0, "Overhang wall": 0, "Gap infill": 0,
          "Sparse infill": 1,
          "Internal solid infill": 2, "Top surface": 2, "Bottom surface": 2, "Bridge": 2,
          "Floating vertical shell": 2}
NAMES = ["Walls", "Sparse infill (25 %)", "Solid fill: top, bottom, bridges"]
COLOURS = ["#2a78d6", "#eb6834", "#1baf7a"]
INK, MUTED, PLATE, RIGHT_ONLY = "#1f1f1e", "#6b6a64", "#dcdbd6", "#b9b8b1"
LABELS = {"bracket": "bracket", "carrier": "carrier", "pod": "pod", "spacers": "4 spacers",
          "tag_wedge#1": "tag wedges"}


def parse(gcode: str) -> tuple[np.ndarray, np.ndarray, np.ndarray, dict[int, tuple[float, float]]]:
    """Extrusion segments [[x0, y0, z, x1, y1, z]], their group and layer, and per layer (z, minutes left)."""
    segs, group, layer = [], [], []
    layers: dict[int, tuple[float, float]] = {}
    x = y = 0.0
    z, feat, n, absolute, started, left = 0.0, None, 0, True, False, None
    num = re.compile(r"([XYZEIJ])(-?\d*\.?\d+)")
    for line in gcode.splitlines():
        if line.startswith(";"):
            if line.startswith("; CHANGE_LAYER"):
                started = True
            elif line.startswith("; Z_HEIGHT:"):
                z = float(line[11:])
            elif line.startswith("; layer num/total_layer_count:"):
                n = int(line.split(":")[1].split("/")[0])
                layers[n] = (z, left)
            elif line.startswith("; FEATURE:"):
                feat = line[10:].strip()
            continue
        cmd = line.split(";")[0].split()
        if not cmd:
            continue
        c = cmd[0]
        if c == "G90":
            absolute = True
        elif c == "G91":
            absolute = False
        elif c == "M73" and (m := re.search(r" R(\d+)", line)):
            left = float(m.group(1))
        elif c in ("G0", "G1", "G2", "G3"):
            v = {k: float(s) for k, s in num.findall(line.split(";")[0])}
            nx = (v["X"] if absolute else x + v["X"]) if "X" in v else x
            ny = (v["Y"] if absolute else y + v["Y"]) if "Y" in v else y
            draw = started and v.get("E", 0.0) > 0 and feat in GROUPS and (nx, ny) != (x, y)
            if draw and c in ("G2", "G3"):
                cx, cy = x + v.get("I", 0.0), y + v.get("J", 0.0)
                r = math.hypot(x - cx, y - cy)
                a0, a1 = math.atan2(y - cy, x - cx), math.atan2(ny - cy, nx - cx)
                if c == "G3" and a1 <= a0:
                    a1 += 2 * math.pi
                if c == "G2" and a1 >= a0:
                    a1 -= 2 * math.pi
                k = max(2, math.ceil(abs(a1 - a0) / math.radians(10)), math.ceil(abs(a1 - a0) * r / 0.5))
                a = np.linspace(a0, a1, k + 1)
                px, py = cx + r * np.cos(a), cy + r * np.sin(a)
                px[-1], py[-1] = nx, ny
                for i in range(k):
                    segs.append((px[i], py[i], z, px[i + 1], py[i + 1], z))
                group += [GROUPS[feat]] * k
                layer += [n] * k
            elif draw:
                segs.append((x, y, z, nx, ny, z))
                group.append(GROUPS[feat])
                layer.append(n)
            x, y = nx, ny
    return np.array(segs), np.array(group), np.array(layer), layers


def polylines(segs: np.ndarray, group: np.ndarray, layer: np.ndarray) -> pv.PolyData:
    pts = segs.reshape(-1, 3)
    n = len(segs)
    cells = np.column_stack([np.full(n, 2), np.arange(0, 2 * n, 2), np.arange(1, 2 * n, 2)]).ravel()
    mesh = pv.PolyData(pts, lines=cells)
    mesh.cell_data["group"] = group
    mesh.cell_data["layer"] = layer
    return mesh


def bed(pl: pv.Plotter) -> None:
    pl.add_mesh(pv.Box((0, BED[0], 0, BED[1], -2.0, -0.05)), color=PLATE, smooth_shading=False)
    pl.add_mesh(pv.Box((LEFT_REACH, BED[0], 0, BED[1], -2.0, -0.02)), color=RIGHT_ONLY, smooth_shading=False)
    pl.add_mesh(pv.Line((LEFT_REACH, 0, 0.05), (LEFT_REACH, BED[1], 0.05)), color=MUTED, line_width=2)


def add_paths(pl: pv.Plotter, mesh: pv.PolyData, width: float) -> None:
    for g, colour in enumerate(COLOURS):
        part = mesh.extract_cells(np.flatnonzero(mesh.cell_data["group"] == g))
        if part.n_cells:
            pl.add_mesh(part, color=colour, line_width=width, render_lines_as_tubes=True)


def plotter(size: tuple[int, int]) -> pv.Plotter:
    pl = pv.Plotter(off_screen=True, window_size=size)
    pl.set_background("white")
    pl.enable_anti_aliasing("ssaa")
    return pl


OBLIQUE = [(-50, -250, 330), (165, 165, 8), (0, 0, 1)]  # from the front left, at the middle of the set


def still(mesh: pv.PolyData, rep: dict, out: Path) -> None:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.patches import Patch

    shots = []
    for view in ("oblique", "top"):
        pl = plotter((1400, 1280))
        bed(pl)
        add_paths(pl, mesh, 2.0 if view == "oblique" else 1.6)
        if view == "oblique":
            pl.camera_position = OBLIQUE
            pl.camera.zoom(1.55)
        else:
            pl.enable_parallel_projection()
            pl.camera_position = [(BED[0] / 2, BED[1] / 2, 600), (BED[0] / 2, BED[1] / 2, 0), (0, 1, 0)]
            pl.camera.parallel_scale = BED[1] / 2 + 12
        shots.append(pl.screenshot(return_img=True))
        pl.close()

    p = rep["plates"][0]
    h, m = divmod(round(p["print_time_s"] / 60), 60)
    fig, axes = plt.subplots(1, 2, figsize=(14, 7.4), dpi=110, gridspec_kw={"wspace": 0.02})
    for ax, img in zip(axes, shots):
        ax.imshow(img)
        ax.set_axis_off()
    # labels on the top view: the image spans the bed plus a margin, so map bed mm to pixels
    H, W = shots[1].shape[:2]
    scale = H / (BED[1] + 24)
    to_px = lambda xb, yb: (W / 2 + (xb - BED[0] / 2) * scale, H / 2 - (yb - BED[1] / 2) * scale)
    for item in rep["layout"]:
        if item["part"] not in LABELS:
            continue
        x0, y0, x1, y1 = item["footprint"]
        if item["part"] == "tag_wedge#1":
            x1 = x1 + 16  # the label covers both wedges
        u, v = to_px((x0 + x1) / 2, y0 - 3)
        axes[1].text(u, v, LABELS[item["part"]], ha="center", va="top", fontsize=10, color=INK)
    u, v = to_px((LEFT_REACH + BED[0]) / 2, BED[1] / 2)
    axes[1].text(u, v, "right nozzle\nonly", ha="center", va="center", fontsize=9, color=INK, rotation=90)
    u, v = to_px(BED[0] / 2, -4)
    axes[1].text(u, v, "front of the plate", ha="center", va="top", fontsize=9, color=MUTED)
    axes[0].set_title(f"Close up, from the front left: all {p['layers']} layers", fontsize=11, color=INK, loc="left")
    axes[1].set_title(f"From above: the whole {BED[0]:g} x {BED[1]:g} mm Textured PEI plate",
                      fontsize=11, color=INK, loc="left")
    fig.suptitle(f"H2D, one plate: the whole PiPER camera mount in Bambu PAHT-CF, left nozzle "
                 f"(0.4 mm hardened steel)\n{h} h {m:02d} min and {p['filament_g']:.1f} g by Bambu Studio "
                 f"{rep['bambu_studio']}; 0.20 mm layers, 3 walls, 25 % infill, no supports; "
                 f"nozzle {p['nozzle_temp_c']} °C, bed {p['bed_temp_c'][0]} °C, chamber {p['chamber_temp_c']} °C",
                 fontsize=12, color=INK, x=0.02, ha="left", y=0.995)
    fig.legend(handles=[Patch(color=c, label=n) for c, n in zip(COLOURS, NAMES)], loc="lower center", ncol=3,
               frameon=False, fontsize=10, bbox_to_anchor=(0.5, -0.005))
    fig.subplots_adjust(left=0.005, right=0.995, top=0.88, bottom=0.06)
    fig.savefig(out, facecolor="white")
    plt.close(fig)


def gif(mesh: pv.PolyData, layers: dict[int, tuple[float, float]], total_s: float, out: Path) -> None:
    last = max(layers)
    stops = sorted({1, 2, 3, 5, 8, *range(12, last, 8), last})
    pl = plotter((900, 760))
    bed(pl)
    pl.camera_position = OBLIQUE
    pl.camera.zoom(1.5)
    actors, frames = [], []
    for stop in stops:
        for a in actors:
            pl.remove_actor(a)
        upto = mesh.extract_cells(np.flatnonzero(mesh.cell_data["layer"] <= stop))
        actors = []
        for g, colour in enumerate(COLOURS):
            part = upto.extract_cells(np.flatnonzero(upto.cell_data["group"] == g))
            if part.n_cells:
                actors.append(pl.add_mesh(part, color=colour, line_width=2.0, render_lines_as_tubes=True))
        z = layers[stop][0]
        # the frame shows the plate as layer `stop` ends: Bambu's minutes left as the next one starts
        done = total_s / 60 - layers[stop + 1][1] if stop < last else total_s / 60
        h, m = divmod(round(done), 60)
        th, tm = divmod(round(total_s / 60), 60)
        actors.append(pl.add_text(f"Layer {stop} of {last}, z = {z:.1f} mm\n"
                                  f"{h} h {m:02d} min of {th} h {tm:02d} min",
                                  position="upper_left", font_size=11, color=INK))
        frames.append(Image.fromarray(pl.screenshot(return_img=True)))
    pl.close()
    pal = [f.convert("P", palette=Image.ADAPTIVE, colors=128) for f in frames]
    durations = [350] * (len(pal) - 1) + [2500]
    pal[0].save(out, save_all=True, append_images=pal[1:], duration=durations, loop=0, optimize=True)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--no-gif", action="store_true")
    args = ap.parse_args()
    rep = json.loads((HERE / "report_h2d.json").read_text())
    with zipfile.ZipFile(THREE_MF) as z:
        gcode = z.read("Metadata/plate_1.gcode").decode()
    segs, group, layer, layers = parse(gcode)
    mesh = polylines(segs, group, layer)
    print(f"{len(segs)} extrusion segments in {len(layers)} layers; by group:",
          {NAMES[g]: int((group == g).sum()) for g in range(3)})
    RENDERS.mkdir(exist_ok=True)
    still(mesh, rep, RENDERS / "h2d_plate.png")
    if not args.no_gif:
        gif(mesh, layers, rep["plates"][0]["print_time_s"], RENDERS / "h2d_plate_build.gif")


if __name__ == "__main__":
    main()
