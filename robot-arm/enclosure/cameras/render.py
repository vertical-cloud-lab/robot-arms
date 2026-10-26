"""Renderings of the PiPER table and its fixed cameras (PR #9, #24, #38, #39).

    xvfb-run -a python render.py     # 1-table.png 2-reach.png 3-cameras-edges.png 4-cameras-corners.png
                                     # fixtures.png parts.png

Needs `python build.py` first (reach.npz, results.json).
"""

import json
import textwrap

import matplotlib
import numpy as np
import pyvista as pv
import trimesh

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

import build as B  # noqa: E402
from piper_fk import Piper  # noqa: E402

SURFACE, INK, MUTED = "#fcfcfb", "#0b0b0b", "#6b6a64"
RES = json.loads((B.HERE / "results.json").read_text())
MAIN_CAM = [(-2.75, 3.0, 2.3), (0.0, -0.02, 0.22), (0, 0, 1)]     # from the front-right corner, like the photo
NAMES = {"front": "Front camera", "right": "Right camera", "top": "Top camera"}


def plotter(size):
    pl = pv.Plotter(off_screen=True, window_size=size)
    pl.set_background(SURFACE)
    pl.enable_lightkit()
    return pl


def shot(pl):
    pl.enable_anti_aliasing("ssaa")
    img = pl.screenshot(return_img=True)
    pl.close()
    return img


def add(pl, m, c, opacity=1.0, smooth=False):
    pl.add_mesh(pv.wrap(m), color=c, opacity=opacity, smooth_shading=smooth, specular=0.2, ambient=0.18)


def add_table(pl, parts, solid_enclosure=False):
    for name, m, c, op in parts:
        if solid_enclosure and name in ("frame", "cloth"):
            op = 1.0
        add(pl, m, c, op, smooth=name in ("arm", "frame"))


def side_labels(pl):
    h, zt = B.H, B.Z_TOP + 0.07
    pts = np.array([[h, 0, zt], [0, -h, zt], [0, h + 0.10, B.PLY_T], [-h - 0.10, 0, B.PLY_T]])
    pl.add_point_labels(pts, ["block wall (left)", "door (back)", "front (open)", "right side"], font_size=15,
                        text_color=MUTED, shape=None, show_points=False, always_visible=True)


def reach_meshes():
    z = np.load(B.HERE / "reach.npz")
    occ, lo, vox = np.pad(z["occ"], 1).astype(float), z["lo"] - z["voxel"], float(z["voxel"])
    g = pv.ImageData(dimensions=occ.shape, spacing=(vox,) * 3, origin=tuple(lo + vox / 2 + [0, 0, B.PLY_T]))
    g.point_data["o"] = occ.ravel(order="F")
    vol = g.contour([0.5], scalars="o").smooth(n_iter=60, relaxation_factor=0.1)
    vol = vol.clip_box([-2, 2, -2, 2, -1, B.PLY_T + 0.002], invert=True)
    touch = z["occ"][:, :, :2].any(2)
    nx, ny = touch.shape
    f = pv.ImageData(dimensions=(nx + 1, ny + 1, 1), spacing=(vox, vox, 1), origin=(z["lo"][0], z["lo"][1], B.PLY_T + 0.0015))
    f.cell_data["t"] = touch.ravel(order="F").astype(float)
    foot = f.threshold(0.5, scalars="t").extract_surface(algorithm="dataset_surface").clip_box([-B.P2, B.P2, -B.P2, B.P2, -1, 2], invert=False)
    return vol, foot


def frustum(c, nu=33, nv=19):
    """Rays through the image to where they leave the enclosure (inside of the cube, plywood floor):
    returns the seen patch and the four edge lines."""
    z = c["view"] / np.linalg.norm(c["view"])
    yv = c["up"] - z * (c["up"] @ z)
    yv /= np.linalg.norm(yv)
    xv = np.cross(z, yv)
    tu, tv = B.CAM_W / 2 / B.CAM_F, B.CAM_H / 2 / B.CAM_F
    us, vs = np.linspace(-tu, tu, nu), np.linspace(-tv, tv, nv)
    lo, hi = np.array([-B.H, -B.H, B.PLY_T]), np.array([B.H, B.H, B.Z_TOP - B.R])
    pts = np.zeros((nv, nu, 3))
    for i, v in enumerate(vs):
        for j, u in enumerate(us):
            d = z + u * xv + v * yv
            d /= np.linalg.norm(d)
            with np.errstate(divide="ignore"):
                t = np.where(d > 0, (hi - c["lens"]) / d, np.where(d < 0, (lo - c["lens"]) / d, np.inf))
            pts[i, j] = c["lens"] + d * t.min()
    grid = pv.StructuredGrid(pts[..., 0], pts[..., 1], pts[..., 2])
    corners = [pts[0, 0], pts[0, -1], pts[-1, -1], pts[-1, 0]]
    edge = np.concatenate([pts[0, :], pts[:, -1], pts[-1, ::-1], pts[::-1, 0]])
    faces = []
    allp = np.vstack([[c["lens"]], edge])
    for k in range(len(edge) - 1):
        faces += [3, 0, k + 1, k + 2]
    cone = pv.PolyData(allp, np.array(faces))
    lines = [pv.Line(c["lens"], p) for p in corners]
    loop = pv.lines_from_points(np.vstack([edge, edge[:1]]))
    return grid.extract_surface(algorithm="dataset_surface"), cone, lines, loop


def pov(parts, fix, c, size=(768, 432)):
    """What one camera sees: cloth and frame opaque, nominal lens, no distortion."""
    pl = plotter(size)
    add_table(pl, parts, solid_enclosure=True)
    for name, m, col in fix:
        add(pl, m, col)
    pl.camera_position = [tuple(c["lens"]), tuple(c["lens"] + c["view"]), tuple(c["up"])]
    pl.camera.view_angle = B.VFOV
    pl.camera.clipping_range = (0.01, 10)
    return shot(pl)


def main_view(parts, extra=(), size=(1500, 1150), labels=True):
    pl = plotter(size)
    add_table(pl, parts)
    for fn in extra:
        fn(pl)
    if labels:
        side_labels(pl)
    pl.camera_position = MAIN_CAM
    pl.camera.view_angle = 30
    return shot(pl)


def save_single(img, path, title, note):
    h, w = img.shape[:2]
    note = textwrap.fill(note, 150)
    top = 0.45 + 0.2 * (note.count("\n") + 1)
    fig = plt.figure(figsize=(w / 150, h / 150 + top), dpi=150, facecolor=SURFACE)
    ax = fig.add_axes([0, 0, 1, h / (h + top * 150)])
    ax.imshow(img)
    ax.axis("off")
    fig.text(0.02, 1 - 0.25 / (h / 150 + top), title, fontsize=15, color=INK, weight="bold", va="center")
    fig.text(0.02, 1 - 0.45 / (h / 150 + top), note, fontsize=10, color=MUTED, va="top", linespacing=1.4)
    fig.savefig(path, facecolor=SURFACE)
    plt.close(fig)


def save_with_povs(img, povs, path, title, note):
    h, w = img.shape[:2]
    ph = 3.1
    note = textwrap.fill(note, 150)
    top = 0.45 + 0.2 * (note.count("\n") + 1)
    fig = plt.figure(figsize=(w / 150, h / 150 + ph + top), dpi=150, facecolor=SURFACE)
    H_ = h / 150 + ph + top
    ax = fig.add_axes([0, (ph) / H_, 1, h / 150 / H_])
    ax.imshow(img)
    ax.axis("off")
    fig.text(0.02, 1 - 0.25 / H_, title, fontsize=15, color=INK, weight="bold", va="center")
    fig.text(0.02, 1 - 0.45 / H_, note, fontsize=10, color=MUTED, va="top", linespacing=1.4)
    n = len(povs)
    for k, (name, im, sub) in enumerate(povs):
        a = fig.add_axes([0.015 + k * (0.97 / n), 0.25 / H_, 0.97 / n - 0.012, (ph - 0.55) / H_])
        a.imshow(im)
        a.set_xticks([])
        a.set_yticks([])
        for s in a.spines.values():
            s.set_edgecolor(B.PRINT_C[name])
            s.set_linewidth(4)
        a.set_title(f"{NAMES[name]}\n{sub}", fontsize=9, color=INK, loc="left", pad=4, linespacing=1.3)
    fig.savefig(path, facecolor=SURFACE)
    plt.close(fig)


def camera_extras(lay, fix):
    def draw(pl):
        for name, m, col in fix:
            add(pl, m, col, smooth=name.endswith("post") or name == "crossbar")
        for name, c in lay.items():
            col = B.PRINT_C[name]
            seen, cone, lines, loop = frustum(c)
            pl.add_mesh(cone, color=col, opacity=0.13, lighting=False)
            pl.add_mesh(loop, color=col, line_width=4)
            for ln in lines:
                pl.add_mesh(ln, color=col, line_width=2)
        pts = np.array([c["lens"] + [0, 0, 0.09] for c in lay.values()])
        pl.add_point_labels(pts, [n for n in lay], font_size=18, text_color=INK, shape_color="white", shape_opacity=0.8,
                            show_points=False, always_visible=True, bold=True)
    return draw


def describe(lname, name, c):
    r = RES["layouts"][lname]["cameras"][name]
    if c["kind"] == "post":
        return f"on a post, lens {r['lens_above_plywood_mm']} mm up, {c['tilt']:.0f}° down"
    if c["kind"] == "crossbar":
        return f"under the crossbar, lens {r['lens_above_plywood_mm']} mm up, straight down"
    return f"on the top rail, lens {r['lens_above_plywood_mm']} mm up, {c['tilt']:.0f}° down"


# ------------------------------------------------------------------ fixture close-ups
def fixtures_figure(cams):
    parts = dict(clamp=B.head_clamp(), cap=B.clamp_cap(), cradle=B.head_cradle(), foot=B.ground_foot(), cross=B.cross_clamp())
    col, pvc, ply, board = (0.20, 0.20, 0.22), B.PVC, B.PLYC, (0.10, 0.45, 0.25)
    hw = (0.70, 0.71, 0.73)

    def head_meshes(c):
        out = [(B.mm_to_world(parts["clamp"], c["clamp_T"]), col), (B.mm_to_world(parts["cap"], c["clamp_T"]), (0.32, 0.32, 0.35)),
               (B.mm_to_world(parts["cradle"], c["cradle_T"]), col)]
        Mb = c["cradle_T"] @ B.T(t=np.array([B.PLATE_AT + B.PLATE[0] + B.STANDOFF + 0.5, 0, B.LENS_UP]) / 1e3)
        out.append((B._box([-0.0005, -0.0125, -0.012], [0.0005, 0.0125, 0.012]).apply_transform(Mb), board))
        Ml = c["cradle_T"] @ B.T(t=np.array([B.LENS_FWD - 3, 0, B.LENS_UP]) / 1e3)
        out.append((B._cyl(0.0055, 0.006, "x").apply_transform(Ml), B.DARK))
        piv = c["cradle_T"][:3, 3]
        ax = c["cradle_T"][:3, 1]
        out.append((B.along(piv - ax * 0.008, piv + ax * 0.012, 0.002, 16), hw))          # M4 pivot bolt
        return out

    panels = []
    # (a) ground camera in the front-right corner (corners layout)
    c = cams["corners"]["front"]
    x, y = c["spec"]["xy"]
    ms = [(B._box([x - 0.12, y - 0.10, 0], [-B.P2 + 0.0 + 0.0 + 0.0 + (x + B.P2) + 0.0 + 0.0, y + 0.06, B.PLY_T]), ply)]
    ms = [(B._box([-B.P2, y - 0.16, 0], [x + 0.14, B.P2, B.PLY_T]), ply)]
    ms += [(B.along([-B.H, y - 0.16, B.Z_BOT], [-B.H, B.H, B.Z_BOT], B.R), pvc), (B.along([-B.H, B.H, B.Z_BOT], [x + 0.14, B.H, B.Z_BOT], B.R), pvc),
           (B.along([-B.H, B.H, B.Z_BOT], [-B.H, B.H, B.Z_BOT + 0.55], B.R), pvc)]
    ms += [(B.mm_to_world(parts["foot"], B.T(t=[x, y, B.PLY_T])), col),
           (B.along([x, y, B.PLY_T + B.FOOT_T / 1e3], [x, y, B.POST_TOP], B.PIPE_OD / 2e3), pvc)]
    ms += head_meshes(c)
    panels.append(("a  Ground camera, front-right corner", ms,
                   [(x + 0.55, y + 0.62, 0.62), (x + 0.03, y - 0.03, 0.21), (0, 0, 1)], 30))
    # (b) the head, close up
    ms = [(B.along([x, y, B.CLAMP_Z - 0.06], [x, y, B.POST_TOP], B.PIPE_OD / 2e3), pvc)] + head_meshes(c)
    p = c["lens"]
    panels.append(("b  Head: clamp, cap, cradle, Camera Module 3", ms,
                   [tuple(p + [0.10, 0.20, 0.10]), tuple(p + [-0.035, 0.03, -0.012]), (0, 0, 1)], 30))
    # (c) top camera on the wall-side top rail (corners layout)
    c = cams["corners"]["top"]
    ms = [(B.along([B.H, -0.15, B.Z_TOP], [B.H, 0.15, B.Z_TOP], B.R), pvc)] + head_meshes(c)
    p = c["lens"]
    panels.append(("c  Top camera on the top rail (layout 4)", ms,
                   [tuple(p + [-0.20, 0.17, 0.12]), tuple(p + [0.03, 0, 0.01]), (0, 0, 1)], 30))
    # (d) top camera at the middle of the crossbar, and one cross clamp (layout 3)
    c = cams["edges"]["top"]
    zc = B.Z_TOP + B.CROSS_Z / 1e3
    ms = [(B.along([-0.18, 0, zc], [0.18, 0, zc], B.PIPE_OD / 2e3), pvc)] + head_meshes(c)
    p = c["lens"]
    panels.append(("d  Top camera under the crossbar (layout 3)", ms,
                   [tuple(p + [0.16, 0.22, 0.10]), tuple(p + [0, 0, 0.03]), (0, 0, 1)], 30))
    ms = [(B.along([B.H, -0.12, B.Z_TOP], [B.H, 0.12, B.Z_TOP], B.R), pvc), (B.along([B.H - 0.22, 0, zc], [B.H + 0.03, 0, zc], B.PIPE_OD / 2e3), pvc)]
    M = B.T(np.diag([1, 1, 1.0]), [B.H, 0, B.Z_TOP])
    ms.append((B.mm_to_world(parts["cross"], M), col))
    Mc = M @ B.T(trimesh.transformations.rotation_matrix(np.pi / 2, (0, 1, 0))[:3, :3]
                 @ trimesh.transformations.rotation_matrix(np.pi / 2, (0, 0, 1))[:3, :3])
    ms.append((B.mm_to_world(parts["cap"], Mc), (0.32, 0.32, 0.35)))
    q = np.array([B.H, 0, B.Z_TOP + 0.015])
    panels.append(("e  Cross clamp: crossbar on a top rail (layout 3)", ms,
                   [tuple(q + [-0.20, 0.17, 0.10]), tuple(q), (0, 0, 1)], 30))

    imgs = []
    for title, ms, cam, va in panels:
        pl = plotter((900, 760))
        for m, cc in ms:
            add(pl, m, cc, smooth=False)
        pl.camera_position = cam
        pl.camera.view_angle = va
        imgs.append((title, shot(pl)))
    fig = plt.figure(figsize=(15, 8.6), dpi=130, facecolor=SURFACE)
    fig.text(0.015, 0.975, "Camera fixtures: one printed head for all three cameras, on 3/4 in PVC", fontsize=15,
             weight="bold", color=INK, va="top")
    fig.text(0.015, 0.94, "Ground cameras: square foot screwed flush to the plywood's edges, 400 mm post cut from the "
             "enclosure's PVC off-cuts, head clamped at the top.  Top camera: the same head on a top rail, or under a "
             "crossbar held by two cross clamps.", fontsize=9.5, color=MUTED, va="top")
    pos = [(0.0, 0.47, 0.335, 0.44), (0.333, 0.47, 0.335, 0.44), (0.666, 0.47, 0.335, 0.44),
           (0.0, 0.0, 0.335, 0.44), (0.333, 0.0, 0.335, 0.44)]
    for (title, im), p in zip(imgs, pos):
        a = fig.add_axes(p)
        a.imshow(im)
        a.axis("off")
        a.set_title(title, fontsize=10.5, color=INK, loc="left")
    a = fig.add_axes([0.68, 0.02, 0.31, 0.40])
    a.axis("off")
    rows = [("Part (PETG)", "Qty", "cm³")]
    for n, q in (("head-clamp", 3), ("clamp-cap", 3), ("head-cradle", 3), ("ground-foot", 2), ("cross-clamp", 2),
                 ("clamp-cap (cross)", 2)):
        m = parts[{"head-clamp": "clamp", "clamp-cap": "cap", "head-cradle": "cradle", "ground-foot": "foot",
                   "cross-clamp": "cross", "clamp-cap (cross)": "cap"}[n]]
        rows.append((n, str(q), f"{m.volume / 1e3:.1f}"))
    for k, row in enumerate(rows):
        for j, (txt, xx) in enumerate(zip(row, (0.0, 0.62, 0.80))):
            a.text(xx, 0.95 - k * 0.085, txt, fontsize=10, color=INK if k else MUTED, weight="bold" if k == 0 else None,
                   transform=a.transAxes, va="top")
    a.text(0.0, 0.95 - len(rows) * 0.085 - 0.02, "Head: 24 cm³, about 30 g.  Foot 22 cm³ (feet: layouts 3 and 4).\n"
           "Cross clamps only for the crossbar in layout 3.", fontsize=9, color=MUTED, transform=a.transAxes, va="top")
    fig.savefig(B.HERE / "fixtures.png", facecolor=SURFACE)
    plt.close(fig)


def parts_figure():
    """The five STLs as exported, in print orientation."""
    import trimesh as tm
    names = ["head-clamp", "clamp-cap", "head-cradle", "ground-foot", "cross-clamp"]
    pl = plotter((1700, 520))
    x = 0.0
    for n in names:
        m = tm.load(B.HERE / f"models/{n}.stl")
        m.apply_translation([x - m.bounds[0][0], -m.bounds[0][1] - m.extents[1] / 2, 0])
        pl.add_mesh(pv.wrap(m), color=(0.25, 0.25, 0.28), specular=0.3, ambient=0.2)
        pl.add_point_labels(np.array([[x + m.extents[0] / 2, -45, 0]]), [n], font_size=16, text_color=INK, shape=None,
                            show_points=False, always_visible=True)
        x += m.extents[0] + 30
    pl.add_mesh(pv.Plane(center=(x / 2 - 15, 0, -0.3), i_size=x + 40, j_size=150), color=(0.92, 0.92, 0.90))
    pl.camera_position = [(x / 2, -330, 260), (x / 2 - 15, 0, 15), (0, 0, 1)]
    pl.camera.view_angle = 30
    img = shot(pl)
    save_single(img, B.HERE / "parts.png", "Printed parts, as exported (mm, print orientation)",
                "PETG, 0.2 mm layers, 4 walls, 40 % infill. No supports except under the cross clamp's crossbar sleeve.")


def main():
    piper = Piper()
    parts = B.table_parts(piper)
    zr = np.load(B.HERE / "reach.npz")
    reach_pts = (np.argwhere(zr["occ"]) + 0.5) * float(zr["voxel"]) + zr["lo"] + [0, 0, B.PLY_T]
    tilts = {l: {n: c["tilt_deg"] for n, c in v["cameras"].items()} for l, v in RES["layouts"].items()}
    cams = B.cameras(tilts)
    del reach_pts

    # 1: the table
    img = main_view(parts)
    save_single(img, B.HERE / "1-table.png", "1  The PiPER table, 23 Oct 2026",
                "Wooden legs, A1 mini and AMS lite on the wall side, power strip along it, magnetic switch on the front-right "
                "leg. PVC cube (#38) and its drop cloth shown see-through; front left open.")

    # 2: reach
    vol, foot = reach_meshes()

    def draw_reach(pl):
        pl.add_mesh(vol, color=B.REACH_C, opacity=0.28, smooth_shading=True, specular=0.3)
        pl.add_mesh(foot, color=B.REACH_C, opacity=0.55, lighting=False)

    img = main_view(parts, [draw_reach])
    rr = RES["reach"]
    save_single(img, B.HERE / "2-reach.png", "2  Where the gripper's fingertips can reach",
                f"Every joint inside its URDF limit (J1 ±150°, J2 0–180°, J3 −155–0°, J4 ±105°, J5 ±70°), nothing below the "
                f"plywood. Up to {rr['max_radius_from_J1_m'] * 1e3:.0f} mm from J1 and {rr['max_height_above_plywood_m'] * 1e3:.0f} mm "
                f"up; darker blue = plywood the fingertips can touch ({rr['plywood_reachable_pct']:.0f} %).")

    # 3 and 4: cameras
    for k, (lname, title) in enumerate((("edges", "3  Front and right cameras mid-edge, top camera in the middle"),
                                        ("corners", "4  Front and right cameras in the corners, top camera on a top edge")),
                                       start=3):
        lay = cams[lname]
        fix = B.fixture_parts(lay)
        img = main_view(parts, [camera_extras(lay, fix)])
        cov = RES["layouts"][lname]["coverage_work_zone"]
        note = (f"Shaded: what each camera sees (Camera Module 3 Wide, {B.HFOV:.0f}° × {B.VFOV:.0f}°). Of the reach volume's lowest "
                f"{B.WORK_Z * 1e3:.0f} mm: front {cov['front']['reach_pct']:.0f} %, right {cov['right']['reach_pct']:.0f} %, "
                f"top {cov['top']['reach_pct']:.0f} %; seen by 2+ cameras {cov['two_or_more']['reach_pct']:.0f} %.")
        povs = [(n, pov(parts, fix, lay[n]), describe(lname, n, lay[n])) for n in ("front", "right", "top")]
        save_with_povs(img, povs, B.HERE / f"{k}-cameras-{lname}.png", title, note)

    fixtures_figure(cams)
    parts_figure()


if __name__ == "__main__":
    main()
