"""Renderings of the PiPER table and its fixed cameras (PR #9, #24, #38, #39).

    xvfb-run -a python render.py     # 1-table.png 2-reach.png 3-cameras-edges.png 4-cameras-corners.png
                                     # fixtures.png cradles.png parts.png

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
    h, z = B.H + 0.10, B.PLY_T
    pts = np.array([[h, 0, z], [0, -h, z], [0, h, z], [-h, 0, z]])
    pl.add_point_labels(pts, ["block wall (left)", "door (back)", "front (open)", "right side"], font_size=15,
                        text_color=MUTED, shape=None, show_points=False, always_visible=True)


def reach_meshes():
    z = np.load(B.HERE / "reach.npz")
    occ, lo, vox = np.pad(z["occ"], 1).astype(float), z["lo"] - z["voxel"], float(z["voxel"])
    g = pv.ImageData(dimensions=occ.shape, spacing=(vox,) * 3, origin=tuple(lo + vox / 2 + [0, 0, B.PLY_T]))
    g.point_data["o"] = occ.ravel(order="F")
    vol = g.contour([0.5], scalars="o").smooth(n_iter=60, relaxation_factor=0.1)
    vol = vol.clip_box([-2, 2, -2, 2, -1, B.PLY_T + 0.002], invert=True)
    touch, fs = z["touch"], float(z["touch_step"])
    nx, ny = touch.shape
    f = pv.ImageData(dimensions=(nx + 1, ny + 1, 1), spacing=(fs, fs, 1), origin=(z["lo"][0], z["lo"][1], B.PLY_T + 0.0015))
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
    note = textwrap.fill(note, 128)
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
    note = textwrap.fill(note, 128)
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
    parts = dict(clamp=B.head_clamp(), cap=B.clamp_cap(), foot=B.ground_foot(), cross=B.cross_clamp(),
                 **{f"cradle-{v}": B.head_cradle(v) for v in B.CRADLES})
    cam_parts = {v: B.camera_meshes(v) for v in B.CRADLES}
    col, pvc, ply = (0.20, 0.20, 0.22), B.PVC, B.PLYC
    hw = (0.70, 0.71, 0.73)

    def head_meshes(c):
        out = [(B.mm_to_world(parts["clamp"], c["clamp_T"]), col), (B.mm_to_world(parts["cap"], c["clamp_T"]), (0.32, 0.32, 0.35)),
               (B.mm_to_world(parts[f"cradle-{c['version']}"], c["cradle_T"]), col)]
        out += [(B.mm_to_world(m, c["cradle_T"]), B.CAM_COL[n]) for n, m in cam_parts[c["version"]]]
        piv = c["cradle_T"][:3, 3]
        ax = c["cradle_T"][:3, 1]
        out.append((B.along(piv - ax * 0.008, piv + ax * 0.012, 0.002, 16), hw))          # M4 pivot bolt
        return out

    panels = []
    # (a) ground camera in the front-right corner (corners layout)
    c = cams["corners"]["front"]
    x, y = c["spec"]["xy"]
    ms = [(B._box([-B.P2, B.P2 - 0.40, 0], [-B.P2 + 0.40, B.P2, B.PLY_T]), ply)]
    ms += [(B.along([-B.H, B.P2 - 0.40, B.Z_BOT], [-B.H, B.H, B.Z_BOT], B.R), pvc),
           (B.along([-B.H, B.H, B.Z_BOT], [-B.P2 + 0.40, B.H, B.Z_BOT], B.R), pvc),
           (B.along([-B.H, B.H, B.Z_BOT], [-B.H, B.H, B.Z_BOT + 0.56], B.R), pvc)]
    ms += [(B.mm_to_world(parts["foot"], B.T(t=[x, y, B.PLY_T])), col),
           (B.along([x, y, B.PLY_T + B.FOOT_T / 1e3], [x, y, B.POST_TOP], B.PIPE_OD / 2e3), pvc)]
    ms += head_meshes(c)
    panels.append(("a  Ground camera in the front-right corner", ms,
                   [(x + 0.86, y - 0.30, 0.56), (x + 0.07, y - 0.05, 0.22), (0, 0, 1)], 34))
    # (b) the head, close up
    ms = [(B.along([x, y, B.CLAMP_Z - 0.06], [x, y, B.POST_TOP], B.PIPE_OD / 2e3), pvc)] + head_meshes(c)
    p = c["lens"]
    panels.append(("b  Head: clamp, cap, vertical cradle, Camera Module 3", ms,
                   [tuple(p + [0.19, 0.03, 0.09]), tuple(p + [-0.04, 0.035, -0.005]), (0, 0, 1)], 30))
    # (c) top camera on the wall-side top rail (corners layout)
    c = cams["corners"]["top"]
    ms = [(B.along([B.H, -0.15, B.Z_TOP], [B.H, 0.15, B.Z_TOP], B.R), pvc)] + head_meshes(c)
    p = c["lens"]
    panels.append(("c  Top camera on the top rail, horizontal cradle (layout 4)", ms,
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
                   [tuple(q + [-0.17, 0.22, 0.16]), tuple(q + [-0.01, 0, 0.005]), (0, 0, 1)], 30))

    imgs = []
    for title, ms, cam, va in panels:
        pl = plotter((900, 760))
        for m, cc in ms:
            add(pl, m, cc, smooth=False)
        pl.camera_position = cam
        pl.camera.view_angle = va
        imgs.append((title, shot(pl)))
    fig = plt.figure(figsize=(15, 8.6), dpi=130, facecolor=SURFACE)
    fig.text(0.015, 0.975, "Camera fixtures: the same clamp for all three cameras, on 3/4 in PVC", fontsize=15,
             weight="bold", color=INK, va="top")
    fig.text(0.015, 0.945, "Ground cameras: square foot screwed flush to the plywood's edges, 400 mm post cut from the "
             "enclosure's PVC off-cuts, head with the vertical cradle clamped on top.\nTop camera: the same clamp with the "
             "horizontal cradle, on a top rail or under a crossbar held by two cross clamps.", fontsize=9.5, color=MUTED,
             va="top", linespacing=1.4)
    pos = [(0.0, 0.45, 0.335, 0.42), (0.333, 0.45, 0.335, 0.42), (0.666, 0.45, 0.335, 0.42),
           (0.0, 0.0, 0.335, 0.42), (0.333, 0.0, 0.335, 0.42)]
    for (title, im), p in zip(imgs, pos):
        a = fig.add_axes(p)
        a.imshow(im)
        a.axis("off")
        a.set_title(title, fontsize=10.5, color=INK, loc="left")
    a = fig.add_axes([0.68, 0.02, 0.31, 0.40])
    a.axis("off")
    rows = [("Part (PETG)", "Qty", "cm³")]
    for n, q in (("head-clamp", 3), ("clamp-cap", 3), ("head-cradle-vertical", 2), ("head-cradle-horizontal", 1),
                 ("ground-foot", 2), ("cross-clamp", 2), ("clamp-cap (cross)", 2)):
        m = parts[{"head-clamp": "clamp", "clamp-cap": "cap", "head-cradle-vertical": "cradle-vertical",
                   "head-cradle-horizontal": "cradle-horizontal", "ground-foot": "foot",
                   "cross-clamp": "cross", "clamp-cap (cross)": "cap"}[n]]
        rows.append((n, str(q), f"{m.volume / 1e3:.1f}"))
    for k, row in enumerate(rows):
        for j, (txt, xx) in enumerate(zip(row, (0.0, 0.62, 0.80))):
            a.text(xx, 0.95 - k * 0.075, txt, fontsize=10, color=INK if k else MUTED, weight="bold" if k == 0 else None,
                   transform=a.transAxes, va="top")
    a.text(0.0, 0.95 - len(rows) * 0.075 - 0.02, "Vertical cradle on the posts, horizontal cradle on a top rail\n"
           "or the crossbar. Cross clamps only for layout 3.", fontsize=9, color=MUTED, transform=a.transAxes, va="top")
    fig.savefig(B.HERE / "fixtures.png", facecolor=SURFACE)
    plt.close(fig)



# ------------------------------------------------------------------ the two cradles, close up
def cradle_figure():
    """Both cradles on a short piece of pipe, with the camera board and its ribbon, plus each cradle bare."""
    clamp, cap = B.head_clamp(), B.clamp_cap()
    col, cap_c, pvc, hw = (0.20, 0.20, 0.22), (0.32, 0.32, 0.35), B.PVC, (0.70, 0.71, 0.73)
    cradle_c = (0.42, 0.42, 0.46)                    # lighter than the clamp, so the standoffs read
    M = B.T(t=[B.PIVOT_AT, 0, 0])                    # cradle frame -> clamp frame, tilt 0

    def head(v, mode):
        ms = [(B.along([0, 0, -45], [0, 0, 45], B.PIPE_OD / 2, 48), pvc, 1.0), (clamp, col, 1.0), (cap, cap_c, 1.0),
              (B.head_cradle(v).copy().apply_transform(M), cradle_c, 1.0),
              (B.along([B.PIVOT_AT, -9, 0], [B.PIVOT_AT, 12, 0], 2.0, 16), hw, 1.0)]
        for n, m in B.camera_meshes(v):
            if mode == "ghost" and n in ("module", "lens", "board"):
                continue
            ms.append((m.copy().apply_transform(M), B.CAM_COL[n], 1.0))
        return ms

    def at(v, s, t, h=0.0):
        return B.on_board(v, s, t, h) + [B.PIVOT_AT, 0, 0]

    def views(v):
        _, es, et = B.board_frame(v)
        ex = np.array([1.0, 0, 0])
        side = -1 if v == "vertical" else 1                    # look at the side away from the clamp's ears
        return [("front", "full", 150 * ex - 120 * side * es + 70 * et * (1 if v == "vertical" else -1) + 0 * ex,
                 at(v, 0, 11), et),
                ("side on: ribbon bends back past the open edge", "full",
                 side * 120 * es - 25 * ex + 15 * et, at(v, 0, 6, -10), et),
                ("straight on, board outlined: four standoffs", "ghost",
                 105 * ex + 10 * es + 8 * et, at(v, 0, 10, -2), et)]

    imgs, titles = {}, {}
    for v in B.CRADLES:
        titles[v] = []
        for title, mode, off, tgt, up in views(v):
            pl = plotter((760, 640))
            for m, c, op in head(v, mode):
                add(pl, m, c, op)
            if mode == "ghost":
                w, hb = B.BOARD[0] / 2, B.BOARD[1]
                rim = np.array([at(v, a, b, 1.0) for a, b in ((-w, 0), (w, 0), (w, hb), (-w, hb), (-w, 0))])
                pl.add_mesh(pv.lines_from_points(rim), color=B.CAM_COL["board"], line_width=5)
                pl.add_point_labels(np.array([at(v, 4, 2.0, 1.0), at(v, 9, B.CUT_T, -3)]),
                                    ["connector", "open edge"], font_size=15, text_color=INK, shape_color="white",
                                    shape_opacity=0.85, show_points=True, point_size=9, point_color=INK, always_visible=True)
            tgt = np.asarray(tgt, float)
            pl.camera_position = [tuple(tgt + off), tuple(tgt), tuple(up)]
            pl.camera.view_angle = 30
            imgs[(v, title)] = shot(pl)
            titles[v].append(title)
    fig = plt.figure(figsize=(15, 9.6), dpi=130, facecolor=SURFACE)
    fig.text(0.015, 0.982, "Camera cradles: a vertical one for the posts and a horizontal one for the top rail", fontsize=15,
             weight="bold", color=INK, va="top")
    fig.text(0.015, 0.952, "Four standoffs each, set for one board orientation. The plate stops short of the ribbon connector, so the "
             "connector has nothing behind it and the ribbon bends straight back past the plate's open edge.\n"
             "Vertical: connector edge down the post, image wide across it.  Horizontal: connector edge at the plate's free "
             "edge (the bottom when it hangs under a rail), image wide along the pipe.", fontsize=9.5, color=MUTED, va="top",
             linespacing=1.4)
    rows = [("vertical", "Vertical cradle (2): ground cameras on the posts"),
            ("horizontal", "Horizontal cradle (1): top camera on a top rail or the crossbar")]
    for r, (v, label) in enumerate(rows):
        y0 = 0.47 - r * 0.465
        fig.text(0.015, y0 + 0.425, label, fontsize=12, weight="bold", color=INK, va="bottom")
        for k, title in enumerate(titles[v]):
            a = fig.add_axes([0.005 + k * 0.333, y0, 0.325, 0.41])
            a.imshow(imgs[(v, title)])
            a.axis("off")
            a.set_title(title, fontsize=9.5, color=MUTED, loc="left", pad=2)
    fig.savefig(B.HERE / "cradles.png", facecolor=SURFACE)
    plt.close(fig)


def parts_figure():
    """The six STLs as exported, in print orientation."""
    import trimesh as tm
    names = ["head-clamp", "clamp-cap", "head-cradle-vertical", "head-cradle-horizontal", "ground-foot", "cross-clamp"]
    pl = plotter((1900, 560))
    x = 0.0
    for n in names:
        m = tm.load(B.HERE / f"models/{n}.stl")
        m.apply_translation([x - m.bounds[0][0], -m.bounds[0][1] - m.extents[1] / 2, 0])
        pl.add_mesh(pv.wrap(m), color=(0.25, 0.25, 0.28), specular=0.3, ambient=0.2)
        pl.add_point_labels(np.array([[x + m.extents[0] / 2, -45, 0]]), [n], font_size=14, text_color=INK, shape=None,
                            show_points=False, always_visible=True)
        x += m.extents[0] + 30
    pl.add_mesh(pv.Plane(center=(x / 2 - 15, 0, -0.3), i_size=x + 40, j_size=150), color=(0.92, 0.92, 0.90))
    pl.camera_position = [(x / 2 - 15, -215, 150), (x / 2 - 15, 0, 18), (0, 0, 1)]
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
    cradle_figure()
    parts_figure()


if __name__ == "__main__":
    main()
