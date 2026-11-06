"""The A1 mini and its AMS lite in Bambu's own layout, turned 45 deg into the front-left corner of
the PiPER table (PR #9, sgbaird's comment of 27 Oct 2026).

    xvfb-run -a python render.py      # a1-mini-corner.png, layout.json

Bambu's numbers: the printer takes 358 mm across, the AMS lite sits 50 mm to its right, 612 mm
in all (A1 mini FAQ, "overall space"); the bed sweeps 390 mm front to back, past the base at both
ends; the AMS lite is 397 x 208 x 342 mm. The shapes are simplified, the sizes are not.

The table, enclosure and arm come from ../cameras/build.py (same world frame: x toward the block
wall, y toward the open front, z up, metres). The arm is turned to face the front, so J1's dead
zone points at the door, as jss265 corrected on PR #9; that matches the parked arm in the photo.
The power strip is left out: it is mostly hidden down the wall side.
"""

import importlib.util
import json
from pathlib import Path

import matplotlib
import numpy as np
import pyvista as pv
import trimesh
from shapely.geometry import MultiPoint, Point
from shapely.ops import nearest_points, unary_union

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

HERE = Path(__file__).parent
_spec = importlib.util.spec_from_file_location("cameras_build", HERE.parent / "cameras/build.py")
B = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(B)
from piper_fk import Piper  # noqa: E402  (on the path once cameras/build.py is loaded)

SURFACE, INK, MUTED = "#fcfcfb", "#0b0b0b", "#6b6a64"
GREEN = "#2f9e44"

# ------------------------------------------------------------------ Bambu's dimensions (mm)
PRINTER_W, GAP, COMBO_W = 358.0, 50.0, 612.0
AMS_W, AMS_D, AMS_H = COMBO_W - PRINTER_W - GAP, 397.0, 342.0
BASE_D = 315.0
BED_U = (56.0, 242.0)                 # bed plate across the printer, from the purge end
BED_L = 192.0                         # bed plate front to back
TRAVEL = (-32.0, 358.0)               # bed's sweep, from the base's back (390 mm)
SPOOL_D, SPOOL_W = 200.0, 64.0

# ------------------------------------------------------------------ placement
TURN = -45.0                          # deg about z; the printer faces the arm, AMS lite on the wall side
MARGIN = 0.015                        # m, kept clear of the plywood's edge
ARM_TURN = 90.0                       # deg: J1 = 0 faces the open front (+y)

LIGHT, ALU, RAIL = (0.88, 0.88, 0.87), (0.76, 0.77, 0.79), (0.55, 0.56, 0.58)
WHITE, DARK, BLACK = (0.95, 0.95, 0.94), (0.30, 0.31, 0.33), (0.07, 0.07, 0.08)
ORANGE, PLATE = (0.96, 0.55, 0.12), (0.16, 0.16, 0.17)
FILAMENT = [(0.95, 0.95, 0.95), (0.20, 0.35, 0.85), (0.93, 0.35, 0.60), (0.92, 0.92, 0.92)]


def _box(lo, hi):
    lo, hi = np.asarray(lo, float), np.asarray(hi, float)
    return trimesh.creation.box(hi - lo).apply_translation((lo + hi) / 2)


def pbox(u0, u1, v0, v1, h0, h1):
    """Box in printer terms: u from the purge end to the right, v from the base's back to its
    front, h up from the table. Returned in the combo's frame (mm): x right, y toward the back."""
    return _box([u0 - COMBO_W / 2, BASE_D / 2 - v1, h0], [u1 - COMBO_W / 2, BASE_D / 2 - v0, h1])


def _cyl_x(r, x0, x1, y, z, sections=48):
    return trimesh.creation.cylinder(radius=r, segment=[[x0, y, z], [x1, y, z]], sections=sections)


def printer(bed_v=163.0):
    """A1 mini, simplified, at Bambu's sizes. bed_v: bed centre, from the base's back."""
    out = [
        (pbox(108, 193, 0, BASE_D, 0, 52), LIGHT),                 # Y-axis base under the bed
        (pbox(236, 310, 0, BASE_D, 0, 52), LIGHT),                 # column base
        (pbox(190, 236, 20, 130, 0, 30), LIGHT),                   # link between them
        (pbox(244, 304, 262, 306, 52, 57), BLACK),                 # screen, front of the column base
        (pbox(250, 302, 21, 76, 52, 375), ALU),                    # Z column
        (pbox(302, 358, 56, 103, 250, 308), WHITE),                # cable box on the column
        (pbox(236, 302, 76, 133, 245, 300), RAIL),                 # Z carriage
        (pbox(0, 262, 103, 133, 258, 284), RAIL),                  # X gantry
        (pbox(0, 26, 98, 140, 222, 292), RAIL),                    # purge-end bracket
        (pbox(0, 60, 98, 142, 205, 224), BLACK),                   # purge wiper and cutter
        (pbox(120, 185, 88, 180, 238, 345), WHITE),                # toolhead
        (pbox(112, 190, bed_v - 70, bed_v + 70, 52, 72), RAIL),    # bed carriage
        (pbox(*BED_U, bed_v - BED_L / 2, bed_v + BED_L / 2, 72, 82), PLATE),   # bed
    ]
    return out


def ams_lite():
    """AMS lite on its stand, 50 mm right of the printer: four spools, axes across, two a side."""
    xc = COMBO_W / 2 - AMS_W / 2
    out = [(_box([xc - 18, -18, 40], [xc + 18, 18, 300]), WHITE),          # post
           (_box([xc - 26, -38, 296], [xc + 26, 38, 342]), WHITE)]         # hub on top
    for sx, sy in ((-1, -1), (-1, 1), (1, -1), (1, 1)):                    # legs
        a, b = np.array([xc, 0, 60.0]), np.array([xc + sx * 90, sy * 175, 0.0])
        out.append((B.CB.beam(a, b, 22, 14), DARK))
        out.append((_box([xc + sx * 90 - 18, sy * 175 - 18, 0], [xc + sx * 90 + 18, sy * 175 + 18, 8]), DARK))
    for k, (sx, y, z) in enumerate(((-1, 98.5, 242), (-1, -98.5, 120), (1, -98.5, 242), (1, 98.5, 120))):
        x_in = xc + sx * 22
        x_out = xc + sx * (AMS_W / 2)
        x0, x1 = sorted((x_in, x_out))
        out.append((_cyl_x(SPOOL_D / 2, x0, x0 + 4, y, z), WHITE))         # flanges
        out.append((_cyl_x(SPOOL_D / 2, x1 - 4, x1, y, z), WHITE))
        out.append((_cyl_x(SPOOL_D / 2 - 14, x0 + 4, x1 - 4, y, z), FILAMENT[k]))
        out.append((_cyl_x(14, x0 - 2, x1 + 2, y, z, 24), DARK))           # rotary holder hub
        out.append((B.CB.beam(np.array([xc, 0, z]), np.array([xc, y, z]), 16, 16), WHITE))   # holder arm
        fx = xc + sx * 38                                                  # feeders by the hub
        fy = 22 * (1 if k % 2 == 0 else -1)
        out.append((_box([fx - 12, fy - 14, 300], [fx + 12, fy + 14, 336]), DARK))
        out.append((trimesh.creation.cylinder(radius=5, segment=[[fx, fy, 336], [fx, fy, 346]]), ORANGE))
    return out


def tubes():
    """Four PTFE tubes from the AMS lite's feeders, over the clip, into the toolhead; and the
    toolhead cable from the column. pyvista meshes in the combo's frame (mm)."""
    xc = COMBO_W / 2 - AMS_W / 2
    clip = np.array([241 - COMBO_W / 2, BASE_D / 2 - 110, 473])
    head = np.array([152 - COMBO_W / 2, BASE_D / 2 - 135, 352])
    out = []
    for k, (sx, sy) in enumerate(((-1, 1), (-1, -1), (1, 1), (1, -1))):
        start = np.array([xc + sx * 38, sy * 22, 346])
        pts = np.array([start, start + [0, 0, 60], (start + clip) / 2 + [0, 0, 140], clip + [6 * k - 9, 0, 0],
                        (clip + head) / 2 + [0, 0, 40], head + [0, 0, 6]])
        out.append((pv.Spline(pts, 80).tube(radius=2.2, n_sides=10), (0.97, 0.97, 0.97)))
    box_top = np.array([330 - COMBO_W / 2, BASE_D / 2 - 80, 308])
    pts = np.array([box_top, box_top + [0, 0, 90], clip + [0, -8, 10], (clip + head) / 2 + [0, -8, 50], head + [10, -10, 0]])
    out.append((pv.Spline(pts, 80).tube(radius=3.5, n_sides=10), DARK))
    return out


def travel_zone():
    """Where the bed sweeps: Bambu's green strip, 390 mm, drawn on the plywood."""
    return pbox(*BED_U, *TRAVEL, 0.3, 2.0)


def place(m):
    """Combo frame (mm) to the world (m): turned TURN deg, centred on CENTRE, on the plywood."""
    M = np.eye(4)
    M[:3, :3] = trimesh.transformations.rotation_matrix(np.radians(TURN), (0, 0, 1))[:3, :3] / 1e3
    M[:3, 3] = [*CENTRE, B.PLY_T]
    if isinstance(m, pv.PolyData):
        return m.transform(M, inplace=False)
    return m.copy().apply_transform(M)


def _rot_xy(pts):
    t = np.radians(TURN)
    R = np.array([[np.cos(t), -np.sin(t)], [np.sin(t), np.cos(t)]])
    return pts[:, :2] @ R.T / 1e3


def combo_centre():
    """Push the combo into the front-left (+x, +y) corner until something meets the margin."""
    swept = printer(bed_v=TRAVEL[0] + BED_L / 2) + printer(bed_v=TRAVEL[1] - BED_L / 2) + ams_lite()
    xy = _rot_xy(np.vstack([m.vertices for m, _ in swept]))
    lim = B.P2 - MARGIN
    return np.array([lim - xy[:, 0].max(), lim - xy[:, 1].max()])


CENTRE = combo_centre()


def footprint():
    """Footprints on the plywood (shapely, metres, world): the printer with its bed at both ends
    of its travel, and the AMS lite."""
    pr = [m for m, _ in printer(bed_v=TRAVEL[0] + BED_L / 2) + printer(bed_v=TRAVEL[1] - BED_L / 2)]
    p = unary_union([MultiPoint(_rot_xy(m.vertices) + CENTRE).convex_hull for m in pr])
    a = MultiPoint(_rot_xy(np.vstack([m.vertices for m, _ in ams_lite()])) + CENTRE).convex_hull
    return p, a


def scene(piper):
    """Table, enclosure, the parked arm facing the front, and the combo: [(name, mesh, rgb, opacity)]."""
    parts = [(n, m, c, op) for n, m, c, op in B.table_parts(piper) if n not in ("a1", "strip", "arm")]
    Rz = trimesh.transformations.rotation_matrix(np.radians(ARM_TURN), (0, 0, 1))
    parts += [("arm", m.apply_transform(Rz), c, 1.0) for _, m, c in B.CB.arm_meshes(piper, np.zeros(6))]
    parts += [("combo", place(m), c, 1.0) for m, c in printer() + ams_lite()]
    parts += [("tubes", place(m), c, 1.0) for m, c in tubes()]
    parts += [("travel", place(travel_zone()), (0.18, 0.66, 0.30), 0.55)]
    return parts


def plotter(size):
    pl = pv.Plotter(off_screen=True, window_size=size)
    pl.set_background(SURFACE)
    pl.enable_lightkit()
    return pl


def draw(pl, parts):
    for name, m, c, op in parts:
        pl.add_mesh(m if isinstance(m, pv.PolyData) else pv.wrap(m), color=c, opacity=op,
                    smooth_shading=name in ("arm", "frame", "tubes"), specular=0.2, ambient=0.18)


def render(parts, cam, size, pts, parallel_scale=None, view_angle=30):
    """Screenshot, plus where each world point in `pts` lands in it (pixels, y down)."""
    pl = plotter(size)
    draw(pl, parts)
    pl.camera_position = cam
    if parallel_scale:
        pl.enable_parallel_projection()
        pl.camera.parallel_scale = parallel_scale
    else:
        pl.camera.view_angle = view_angle
    pl.enable_anti_aliasing("ssaa")
    img = pl.screenshot(return_img=True)
    ren, h = pl.renderer, img.shape[0]
    px = {}
    for k, p in pts.items():
        ren.SetWorldPoint(*p, 1.0)
        ren.WorldToDisplay()
        x, y, _ = ren.GetDisplayPoint()
        px[k] = np.array([x, h - y])
    pl.close()
    return img, px


def w(x_l, y_l, z=0.0):
    """A point in the combo's frame (mm) to the world (m)."""
    return place(trimesh.PointCloud([[x_l, y_l, z]])).vertices[0]


def main():
    piper = Piper()
    parts = scene(piper)
    pr_fp, ams_fp = footprint()
    j1 = Point(0, 0)
    near = min((pr_fp, "printer"), (ams_fp, "AMS lite"), key=lambda t: t[0].distance(j1))
    n_pt = np.array(nearest_points(near[0], j1)[0].coords[0])
    res = dict(turn_deg=TURN, centre_m=[round(float(v), 3) for v in CENTRE],
               nearest_to_J1=dict(item=near[1], mm=round(near[0].distance(j1) * 1e3)),
               printer_to_J1_mm=round(pr_fp.distance(j1) * 1e3), ams_lite_to_J1_mm=round(ams_fp.distance(j1) * 1e3),
               footprint_m2=round(unary_union([pr_fp, ams_fp]).convex_hull.area, 3))
    (HERE / "layout.json").write_text(json.dumps(res, indent=1) + "\n")
    print(json.dumps(res, indent=1))

    z0 = B.PLY_T
    xb = BASE_D / 2
    back = max(xb, AMS_D / 2) + 45             # 612 mm dimension, behind the combo
    H = B.H
    pts = {
        "printer": w(-306 + 276, xb - 48, 380), "ams": w(204, 0, 350), "screen": w(-306 + 274, xb - 284, 57),
        "dim_a": w(-306, back), "dim_b": w(306, back), "ext_a": w(-306, 54.5), "ext_b": w(306, AMS_D / 2),
        "gap": w(77, 78, 280), "trav_a": w(-306 + BED_U[0] - 30, xb - TRAVEL[0]), "trav_b": w(-306 + BED_U[0] - 30, xb - TRAVEL[1]),
        "j1": np.array([0, 0, z0]), "near": np.array([*n_pt, z0]), "arm": np.array([0.0, -0.17, 0.26]),
        "wall": np.array([B.P2 + 0.05, -0.30, z0]), "door": np.array([0.0, -B.P2 - 0.045, z0]),
        "front": np.array([0.0, B.P2 + 0.05, z0]), "right": np.array([-B.P2 - 0.05, -0.30, z0]),
        "wall3": np.array([H, 0.0, 0.62]), "front3": np.array([-0.30, H, 0.10]), "door3": np.array([0.30, -H, 0.30]),
        "bed": w(-306 + 149, xb - 163, 82),
    }
    camT = [(0.0, -0.02, 5.0), (0.0, -0.02, 0.0), (0, -1, 0)]
    imgT, pT = render(parts, camT, (1150, 1150), pts, parallel_scale=0.70)
    cam3 = [(-1.90, 0.12, 1.42), (0.22, 0.24, 0.17), (0, 0, 1)]
    img3, p3 = render(parts, cam3, (1500, 1150), pts, view_angle=34)
    compose(img3, p3, imgT, pT, res)
    return res


def compose(img3, p3, imgT, pT, res):
    h3, w3 = img3.shape[:2]
    hT, wT = imgT.shape[:2]
    W, H = (w3 + wT) / 150, max(h3, hT) / 150
    fig = plt.figure(figsize=(W, H), dpi=150, facecolor=SURFACE)
    a3 = fig.add_axes([0, 0, w3 / 150 / W, 1])
    aT = fig.add_axes([w3 / 150 / W, 0, wT / 150 / W, 1])
    for ax, img in ((a3, img3), (aT, imgT)):
        ax.imshow(img)
        ax.set_xlim(0, img.shape[1])
        ax.set_ylim(img.shape[0], 0)
        ax.axis("off")
    lab = dict(fontsize=11, color=INK)
    lead = dict(arrowstyle="-", color=MUTED, lw=0.8)

    # perspective: name the three things and the room
    a3.annotate("A1 mini", p3["printer"], p3["printer"] + [-150, -110], arrowprops=lead, ha="center", **lab)
    a3.annotate("AMS lite", p3["ams"], p3["ams"] + [90, -130], arrowprops=lead, ha="center", **lab)
    a3.annotate("PiPER", p3["arm"], p3["arm"] + [130, -120], arrowprops=lead, ha="center", **lab)
    side3 = dict(fontsize=10, color=MUTED, ha="center", va="center")
    a3.text(*p3["wall3"], "block wall", **side3)
    a3.text(*p3["front3"], "front (open)", **side3)
    a3.text(*p3["door3"], "door", **side3)

    # plan: sides, names and the four sizes that matter
    side = dict(fontsize=10, color=MUTED, ha="center", va="center")
    aT.text(*pT["wall"], "block wall", rotation=90, **side)
    aT.text(*pT["right"], "right side", rotation=90, **side)
    aT.text(*pT["door"], "door", **side)
    aT.text(*pT["front"], "front (open)", **side)
    aT.annotate("A1 mini", pT["bed"], pT["bed"] + [235, -95], arrowprops=lead, ha="left", va="center", **lab)
    aT.annotate("AMS lite", pT["ams"], pT["ams"] + [40, -215], arrowprops=lead, ha="left", **lab)
    aT.annotate("screen", pT["screen"], pT["screen"] + [120, 25], arrowprops=lead, ha="left", va="center", fontsize=10, color=MUTED)
    dim = dict(arrowstyle="<|-|>", color=INK, lw=1.0, shrinkA=0, shrinkB=0, mutation_scale=9)

    def dimension(a, b, text, off=(0, 0), color=INK):
        d = dict(dim, color=color)
        aT.annotate("", a, b, arrowprops=d)
        m = (a + b) / 2 + off
        ang = np.degrees(np.arctan2(-(b - a)[1], (b - a)[0]))
        ang = ang - 180 if ang > 90 else ang + 180 if ang < -90 else ang
        aT.text(*m, text, rotation=ang, ha="center", va="center", fontsize=10, color=color,
                bbox=dict(boxstyle="round,pad=0.15", fc=SURFACE, ec="none", alpha=0.9))

    for e, d in (("ext_a", "dim_a"), ("ext_b", "dim_b")):
        aT.plot(*np.c_[pT[e], pT[d] + (pT[d] - pT[e]) / np.linalg.norm(pT[d] - pT[e]) * 8], color=MUTED, lw=0.7)
    dimension(pT["dim_a"], pT["dim_b"], f"{COMBO_W:.0f} mm")
    dimension(pT["trav_a"], pT["trav_b"], f"bed travel {TRAVEL[1] - TRAVEL[0]:.0f} mm", color=GREEN)
    dimension(pT["j1"], pT["near"], f"{res['nearest_to_J1']['mm']} mm")
    aT.annotate(f"{GAP:.0f} mm gap", pT["gap"], pT["gap"] + [-150, 215], arrowprops=lead, ha="center", fontsize=10, color=INK)
    fig.savefig(HERE / "a1-mini-corner.png", facecolor=SURFACE)
    plt.close(fig)


if __name__ == "__main__":
    main()
