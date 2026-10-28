#!/usr/bin/env python3
"""Draw the sliced plate from its own G-code: a still, a layer-by-layer GIF and each part's share.

    xvfb-run -a python plate_view.py            # -> plate.png, plate_build.gif, per_object.json

#45's plate_view.py (PR #10's piper-camera-mount/slice/plate_view.py), for the A1 mini's 180 x 180
mm bed. Every extrusion move (G1, and G2/G3 arcs split into short chords) in Metadata/plate_1.gcode
becomes a line, coloured by what Bambu labels it: walls, sparse infill, or solid fill (top, bottom, internal
solid, bridges). Travel, wipes, retractions and the start G-code's purge lines are left out. Times
are Bambu's own, from its M73 R (minutes left) lines. Each part's filament is the extrusion between
Bambu's "start/stop printing object" markers, scaled so the parts add up to Bambu's plate total.
"""
from __future__ import annotations

import argparse
import json
import math
import re
import xml.etree.ElementTree as ET
import zipfile
from pathlib import Path

import numpy as np
import pyvista as pv
from PIL import Image

HERE = Path(__file__).resolve().parent
BED = (180.0, 180.0)
GROUPS = {"Outer wall": 0, "Inner wall": 0, "Overhang wall": 0, "Gap infill": 0,
          "Sparse infill": 1,
          "Internal solid infill": 2, "Top surface": 2, "Bottom surface": 2, "Bridge": 2,
          "Floating vertical shell": 2}
NAMES = ["Walls", "Sparse infill", "Solid fill: top, bottom, bridges"]
COLOURS = ["#2a78d6", "#eb6834", "#1baf7a"]
INK, MUTED, PLATE = "#1f1f1e", "#6b6a64", "#dcdbd6"
OBLIQUE = [(-64, -244, 266), (90, 90, 5), (0, 0, 1)]  # from the front left, over the middle of the plate


def parse(gcode: str):
    """Extrusion segments [[x0, y0, z, x1, y1, z]], their group, layer and object label, per layer
    (z, minutes left), and the filament (mm of E) each object label used."""
    segs, group, layer = [], [], []
    layers: dict[int, tuple[float, float]] = {}
    e_by_obj: dict[int, float] = {}
    x = y = 0.0
    z, feat, n, absolute, started, left, obj = 0.0, None, 0, True, False, None, None
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
            elif line.startswith("; start printing object, unique label id:"):
                obj = int(line.rsplit(":", 1)[1])
            elif line.startswith("; stop printing object"):
                obj = None
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
            if obj is not None and v.get("E", 0.0) > 0:
                e_by_obj[obj] = e_by_obj.get(obj, 0.0) + v["E"]
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
    return np.array(segs), np.array(group), np.array(layer), layers, e_by_obj


def polylines(segs: np.ndarray, group: np.ndarray, layer: np.ndarray) -> pv.PolyData:
    pts = segs.reshape(-1, 3)
    n = len(segs)
    cells = np.column_stack([np.full(n, 2), np.arange(0, 2 * n, 2), np.arange(1, 2 * n, 2)]).ravel()
    mesh = pv.PolyData(pts, lines=cells)
    mesh.cell_data["group"] = group
    mesh.cell_data["layer"] = layer
    return mesh


def plotter(size: tuple[int, int]) -> pv.Plotter:
    pl = pv.Plotter(off_screen=True, window_size=size)
    pl.set_background("white")
    pl.enable_anti_aliasing("ssaa")
    pl.add_mesh(pv.Box((0, BED[0], 0, BED[1], -2.0, -0.05)), color=PLATE, smooth_shading=False)
    return pl


def add_paths(pl: pv.Plotter, mesh: pv.PolyData, width: float) -> list:
    actors = []
    for g, colour in enumerate(COLOURS):
        part = mesh.extract_cells(np.flatnonzero(mesh.cell_data["group"] == g))
        if part.n_cells:
            actors.append(pl.add_mesh(part, color=colour, line_width=width, render_lines_as_tubes=True))
    return actors


def per_object(z: zipfile.ZipFile, e_by_obj: dict[int, float], total_g: float) -> dict[str, float]:
    info = ET.fromstring(z.read("Metadata/slice_info.config"))
    names = {int(o.get("identify_id")): o.get("name") for o in info.iter("object")}
    total_e = sum(e_by_obj.values())
    return {names.get(k, str(k)): round(total_g * e / total_e, 1) for k, e in sorted(e_by_obj.items())}


def still(mesh: pv.PolyData, rep: dict, out: Path) -> None:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.patches import Patch

    shots = []
    for view in ("oblique", "top"):
        pl = plotter((1300, 1240))
        add_paths(pl, mesh, 2.0 if view == "oblique" else 1.5)
        if view == "oblique":
            pl.camera_position = OBLIQUE
            pl.camera.zoom(1.0)
        else:
            pl.enable_parallel_projection()
            pl.camera_position = [(BED[0] / 2, BED[1] / 2, 600), (BED[0] / 2, BED[1] / 2, 0), (0, 1, 0)]
            pl.camera.parallel_scale = BED[1] / 2 + 10
        shots.append(pl.screenshot(return_img=True))
        pl.close()

    p = rep["plate"]
    h, m = divmod(round(p["print_time_s"] / 60), 60)
    fig, axes = plt.subplots(1, 2, figsize=(14, 7.6), dpi=110, gridspec_kw={"wspace": 0.02})
    for ax, img in zip(axes, shots):
        ax.imshow(img)
        ax.set_axis_off()
    H, W = shots[1].shape[:2]
    scale = H / (BED[1] + 20)
    to_px = lambda xb, yb: (W / 2 + (xb - BED[0] / 2) * scale, H / 2 - (yb - BED[1] / 2) * scale)
    for item in rep["layout"]:
        x0, y0, x1, y1 = item["footprint"]
        label = item["object"].replace("head-", "").replace("clamp-cap", "cap")
        u, v = to_px((x0 + x1) / 2, (y0 + y1) / 2)
        axes[1].text(u, v, label, ha="center", va="center", fontsize=9, color=INK,
                     bbox=dict(boxstyle="round,pad=0.2", fc="white", ec="none", alpha=0.85))
    u, v = to_px(BED[0] / 2, -3)
    axes[1].text(u, v, "front of the plate", ha="center", va="top", fontsize=9, color=MUTED)
    axes[0].set_title(f"From the front left: all {p['layers']} layers, {p['max_z_mm']:g} mm tall",
                      fontsize=11, color=INK, loc="left")
    axes[1].set_title(f"From above: the whole {BED[0]:g} x {BED[1]:g} mm Textured PEI plate",
                      fontsize=11, color=INK, loc="left")
    fig.suptitle(f"A1 mini, one plate in black PLA Basic: the wrist-camera pod (PR #10), and one horizontal "
                 f"and two vertical camera cradles (PR #9)\n{h} h {m:02d} min and {p['filament_g']:.1f} g by Bambu "
                 f"Studio {rep['bambu_studio']}; 0.20 mm layers, no supports; pod 3 walls, 25 % infill; "
                 f"cradles 4 walls, 40 % infill", fontsize=12, color=INK, x=0.02, ha="left", y=0.995)
    fig.legend(handles=[Patch(color=c, label=n) for c, n in zip(COLOURS, NAMES)], loc="lower center", ncol=3,
               frameon=False, fontsize=10, bbox_to_anchor=(0.5, -0.005))
    fig.subplots_adjust(left=0.005, right=0.995, top=0.88, bottom=0.06)
    fig.savefig(out, facecolor="white")
    plt.close(fig)


def gif(mesh: pv.PolyData, layers: dict[int, tuple[float, float]], total_s: float, out: Path) -> None:
    last = max(layers)
    stops = sorted({1, 2, 3, 5, 8, *range(12, last, 8), last})
    pl = plotter((900, 760))
    pl.camera_position = OBLIQUE
    pl.camera.zoom(1.0)
    actors, frames = [], []
    for stop in stops:
        for a in actors:
            pl.remove_actor(a)
        actors = add_paths(pl, mesh.extract_cells(np.flatnonzero(mesh.cell_data["layer"] <= stop)), 2.0)
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
    durations = [300] * (len(pal) - 1) + [2500]
    pal[0].save(out, save_all=True, append_images=pal[1:], duration=durations, loop=0, optimize=True)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--no-gif", action="store_true")
    args = ap.parse_args()
    rep = json.loads((HERE / "report.json").read_text())
    with zipfile.ZipFile(HERE / "issue52_A1mini_PLA.3mf") as z:
        segs, group, layer, layers, e_by_obj = parse(z.read("Metadata/plate_1.gcode").decode())
        shares = per_object(z, e_by_obj, rep["plate"]["filament_g"])
    (HERE / "per_object.json").write_text(json.dumps(
        {"note": "grams of PLA per object: its share of the extrusion inside Bambu's object markers, "
                 "scaled to the plate total (which includes the purge and prime lines)",
         "plate_total_g": rep["plate"]["filament_g"], "objects_g": shares}, indent=2) + "\n")
    print(json.dumps(shares, indent=1))
    mesh = polylines(segs, group, layer)
    print(f"{len(segs)} extrusion segments in {len(layers)} layers")
    still(mesh, rep, HERE / "plate.png")
    if not args.no_gif:
        gif(mesh, layers, rep["plate"]["print_time_s"], HERE / "plate_build.gif")


if __name__ == "__main__":
    main()
