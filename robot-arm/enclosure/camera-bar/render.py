"""Figures for the overhead camera bar (#2, #38, #24).

    xvfb-run -a python render.py      # camera-bar.png (3D view, saddle close-up, overhead view), parts.png
"""

import json

import matplotlib
import numpy as np
import pyvista as pv
from PIL import Image

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

import build as B  # noqa: E402
from piper_fk import Piper  # noqa: E402

SURFACE, INK, MUTED = "#fcfcfb", "#0b0b0b", "#8a8983"
WIRE = (0.35, 0.35, 0.38)
RES = json.loads((B.HERE / "bar-results.json").read_text())


def wires():
    """Recommended X-bracing: 1/16 in wire rope in the back and both side walls, front left open."""
    h, z0, z1 = B.H, B.Z_BOT, B.Z_TOP
    pairs = []
    for x0, y0, x1, y1 in ((-h, h, h, h), (h, h, -h, h), (-h, -h, -h, h), (-h, h, -h, -h),
                           (h, -h, h, h), (h, h, h, -h)):
        pairs.append(([x0, y0, z0], [x1, y1, z1]))
    return [B.along(a, b, 0.0012, 8) for a, b in pairs]


def plotter(size):
    pl = pv.Plotter(off_screen=True, window_size=size)
    pl.set_background(SURFACE)
    pl.enable_lightkit()
    return pl


def add_scene(pl, parts, skip=()):
    for name, m, c in parts:
        if any(name.startswith(s) for s in skip):
            continue
        pl.add_mesh(pv.wrap(m), color=c, smooth_shading=name not in ("plywood", "bar"), specular=0.25,
                    ambient=0.15)
    for w in wires():
        pl.add_mesh(pv.wrap(w), color=WIRE)


def shot(pl):
    pl.enable_anti_aliasing("ssaa")
    img = pl.screenshot(return_img=True)
    pl.close()
    return img


def main_view(parts):
    pl = plotter((1400, 1150))
    add_scene(pl, parts)
    pl.camera_position = [(2.45, -2.75, 2.05), (-0.03, 0.05, 0.60), (0, 0, 1)]
    pl.camera.view_angle = 31
    return shot(pl)


def saddle_view(parts):
    pl = plotter((900, 760))
    add_scene(pl, parts, skip=("arm", "side-cameras"))
    c = np.array([B.H, B.H, B.Z_TOP])
    pl.camera_position = [tuple(c + [-0.05, -0.36, 0.17]), tuple(c + [-0.06, -0.05, 0.0]), (0, 0, 1)]
    pl.camera.view_angle = 30
    return shot(pl)


def overhead_view(parts):
    """What the overhead camera sees: Camera Module 3 Wide, nominal lens, at the bar's middle."""
    w, h = 1152, 648
    pl = plotter((w, h))
    add_scene(pl, parts, skip=("bar", "saddle", "camera", "pi"))
    lens = B.LENS
    pl.camera_position = [tuple(lens), tuple(lens - [0, 0, 1.0]), (0, -1, 0)]
    pl.camera.view_angle = float(np.degrees(2 * np.arctan(B.CAM_H / 2 / B.CAM_F)))
    pl.camera.clipping_range = (0.005, 3.0)
    return shot(pl)


def parts_view():
    """The two printed parts on their own, as exported (mm): saddle from above and below, and the plate."""
    sad = pv.read(B.HERE / "models/corner-saddle.stl")
    plate = pv.read(B.HERE / "models/camera-plate.stl")
    imgs = []
    for pos, up in (((215, -185, 215), (0, 0, 1)), ((215, -200, -190), (0, 0, 1))):
        pl = plotter((700, 560))
        pl.add_mesh(sad, color=B.PRINT, smooth_shading=False, specular=0.2)
        pl.camera_position = [pos, (45, 45, 18), up]
        pl.camera.view_angle = 27
        imgs.append(shot(pl))
    pl = plotter((560, 560))
    pl.add_mesh(plate, color=B.PRINT, smooth_shading=False, specular=0.2)
    pl.camera_position = [(0, -120, 160), (0, 0, 4), (0, 0, 1)]
    pl.camera.view_angle = 30
    imgs.append(shot(pl))
    fig = plt.figure(figsize=(12.5, 4.3), dpi=110, facecolor=SURFACE)
    titles = ("Corner saddle, from above:\nbar socket with its end stop, 2 M5 locks, 2 pin holes",
              "Corner saddle, from below:\nrail channels; the leg ends stop against the elbow's hubs",
              "Camera plate:\n2 M5 into the bar's bottom slot, 2 M3 for #24's case")
    for k, (img, t) in enumerate(zip(imgs, titles)):
        ax = fig.add_axes([0.005 + 0.335 * k, 0.0, 0.325, 0.86])
        ax.imshow(img)
        ax.set_axis_off()
        ax.text(0.0, 1.03, t, transform=ax.transAxes, fontsize=9, color=INK, va="bottom", wrap=True)
    fig.savefig(B.HERE / "parts.png", facecolor=SURFACE)


def main():
    parts_view()
    piper = Piper()
    parts = B.scene_parts(piper)
    a, b, c = main_view(parts), saddle_view(parts), overhead_view(parts)
    cam, st = RES["camera"], RES["stiffness"]
    fig = plt.figure(figsize=(14, 8.2), dpi=110, facecolor=SURFACE)
    d, dc = st["diagonal"]["push_10N_x_at_front_left_corner"], st["diagonal+cables"]["push_10N_x_at_front_left_corner"]
    fig.text(0.01, 0.975, "Overhead camera bar on the as-built 48 in enclosure (#38)", fontsize=14, color=INK,
             va="top", weight="bold")
    fig.text(0.01, 0.935, f"A 10 N push on a top corner shifts the overhead image {d['image_shift_at_plywood_mm']:.0f} mm "
             f"on the bare frame and {dc['image_shift_at_plywood_mm']:.1f} mm with wire X-bracing in three walls "
             "(3D frame model, joints pinned).", fontsize=10.5, color=MUTED, va="top")
    ax = fig.add_axes([0.0, 0.0, 0.56, 0.86])
    ax.imshow(a)
    ax.text(0.03, 0.97, "2020 bar corner to corner; camera under its middle", transform=ax.transAxes,
            fontsize=11, color=INK, va="top")
    ax.text(0.03, 0.925, "Grey: wire X-bracing in the back and side walls (front left open).\n"
            "Side cameras on #24's corner posts.  Arm at an example reach.",
            transform=ax.transAxes, fontsize=9, color=MUTED, va="top")
    ax2 = fig.add_axes([0.57, 0.45, 0.42, 0.41])
    ax2.imshow(b)
    ax2.text(0.0, 1.02, "Corner saddle (print 2): legs stop against the elbow's hubs", transform=ax2.transAxes,
             fontsize=10.5, color=INK, va="bottom")
    ax3 = fig.add_axes([0.57, 0.02, 0.42, 0.37])
    ax3.imshow(c)
    fp = cam["footprint"]
    ax3.text(0.0, 1.02, f"Overhead view, simulated: {cam['lens_above_plywood_mm'] / 1000:.2f} m up, "
             f"{fp['margin_past_plywood_edge_m'] * 1000:.0f} mm to spare past the plywood", transform=ax3.transAxes,
             fontsize=10.5, color=INK, va="bottom")
    for x in (ax, ax2, ax3):
        x.set_axis_off()
    fig.savefig(B.HERE / "camera-bar.png", facecolor=SURFACE)
    Image.fromarray(c).save(B.HERE / "overhead-view.png")
    print("camera-bar.png, overhead-view.png, parts.png")


if __name__ == "__main__":
    main()
