"""Figures for access.py: one per layout, a 3D view of the arm taking the print and a plan with
the distances from J1 where each kind of grasp works at bed height.

    python access.py && xvfb-run -a python access_render.py      # access-*.png
"""

import json
import sys
from pathlib import Path

import matplotlib
import numpy as np
import pyvista as pv
import trimesh
from shapely.geometry import Polygon
from shapely.geometry import box as sbox

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE))
import access as X  # noqa: E402

A, B = X.A, X.B
SURFACE, INK, MUTED = "#fcfcfb", "#0b0b0b", "#6b6a64"
OK_C, NO_C, TOP_C = (0.18, 0.62, 0.27), (0.85, 0.20, 0.20), (0.20, 0.42, 0.85)
OK_H, NO_H, TOP_H = "#2f9e44", "#d93636", "#336bd9"
PRINT_RGB = (0.98, 0.60, 0.12)
FIGS = [("corner", "45° in the corner, arm where it is"),
        ("wall", "As it was: against the wall, facing the arm"),
        ("moved", "45° in the corner, arm moved back {back} mm"),
        ("people-r", "Front-right corner, facing the E-stop side, arm where it is"),
        ("people", "Front middle, facing the E-stop side, arm moved back {back} mm, bed parked at the back")]


def arm_parts(piper, q, lay, color=None, opacity=1.0, links=None):
    Rz = trimesh.transformations.rotation_matrix(np.radians(X.ARM_TURN), (0, 0, 1))
    Rz[:3, 3] = [*lay["arm"], 0.0]
    out = []
    for name, m, c in B.CB.arm_meshes(piper, np.asarray(q)):
        if links is None or name in links:
            out.append(("arm", m.apply_transform(Rz), color or c, opacity))
    return out


def gripper_ghost(piper, p, z):
    """The gripper alone, its grasp point at p and tool axis along z, fingers opening sideways."""
    z = np.asarray(z, float) / np.linalg.norm(z)
    x = np.cross([0, 0, 1.0], z)
    x /= np.linalg.norm(x)
    T6 = np.eye(4)
    T6[:3, :3] = np.column_stack([x, np.cross(z, x), z])
    T6[:3, 3] = p - z * X.TCP
    q0 = np.zeros(6)
    poses = piper.fk(q0, grip=0.012)
    inv6 = np.linalg.inv(poses["link6"])
    out = []
    J1 = B.CB.T(t=B.CB.J1)
    for name, m, _ in B.CB.arm_meshes(piper, q0):
        if name in ("link6", "link7", "link8"):
            m.apply_transform(np.linalg.inv(J1))            # back to the arm frame
            m.apply_transform(T6 @ inv6)
            out.append(("ghost", m, NO_C, 0.45))
    return out


def printed_part(p, lay):
    M = X.combo_M(lay)
    yaw = np.arctan2(M[1, 0], M[0, 0])
    m = trimesh.creation.box((0.030, 0.030, 0.020))
    m.apply_transform(trimesh.transformations.rotation_matrix(yaw, (0, 0, 1)))
    return m.apply_translation([p[0], p[1], B.PLY_T + X.BED_TOP + 0.010])


def sector(cx, cy, r0, r1, z, n=200):
    """Annulus over the angles J1 can point to (J1 = 0 faces +y, +-147 deg), cut to the plywood."""
    a = np.radians(90) + np.radians(np.linspace(-147, 147, n))
    ring = Polygon(np.vstack([np.c_[cx + r1 * np.cos(a), cy + r1 * np.sin(a)],
                              np.c_[cx + r0 * np.cos(a), cy + r0 * np.sin(a)][::-1]]))
    cut = ring.intersection(sbox(-B.P2, -B.P2, B.P2, B.P2))
    ms = []
    for poly in getattr(cut, "geoms", [cut]):
        v, f = trimesh.creation.triangulate_polygon(poly)
        ms.append(trimesh.Trimesh(np.c_[v, np.full(len(v), z)], f, process=False))
    return trimesh.util.concatenate(ms)


def scene(piper, lay, res):
    parts = [(n, m, c, op) for n, m, c, op in B.table_parts(piper) if n not in ("a1", "strip", "arm")]
    M = X.combo_M(lay)
    parts += [("combo", m.copy().apply_transform(M), c, 1.0) for m, c in A.printer(bed_v=lay["bed_v"]) + A.ams_lite()]
    parts += [("tubes", m.transform(M, inplace=False), c, 1.0) for m, c in A.tubes()]
    best = res["best"]
    if best is not None:
        parts += arm_parts(piper, best["q"], lay)
        parts.append(("print", printed_part(best["p"], lay), PRINT_RGB, 1.0))
    else:
        parts += arm_parts(piper, res["above"]["q"], lay)
        parts.append(("print", printed_part(res["above"]["p"], lay), PRINT_RGB, 1.0))
    return parts


def plotter(size):
    pl = pv.Plotter(off_screen=True, window_size=size)
    pl.set_background(SURFACE)
    pl.enable_lightkit()
    return pl


def render(parts, cam, size, pts, parallel_scale=None, view_angle=30):
    pl = plotter(size)
    for name, m, c, op in parts:
        pl.add_mesh(m if isinstance(m, pv.PolyData) else pv.wrap(m), color=c, opacity=op,
                    smooth_shading=name in ("arm", "frame", "tubes", "ghost"), specular=0.2, ambient=0.18)
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


def close_camera(lay, g, tool, j1):
    """Side-on to the gripper at g (tool axis `tool`), from the side away from the AMS lite and a
    little behind the gripper, 22 deg above the bed."""
    t = np.r_[tool[:2], 0.0]
    t /= np.linalg.norm(t)
    ams = trimesh.transform_points([[A.COMBO_W / 2 - A.AMS_W / 2, 0.0, 0.0]], X.combo_M(lay))[0]
    perp = np.array([-t[1], t[0], 0.0])
    if perp @ (g - ams) < 0:
        perp = -perp
    look = perp - 0.45 * t
    look /= np.linalg.norm(look)
    focus = 0.62 * g + 0.38 * j1 + [0, 0, 0.10]
    eye = focus + look * 1.30 + [0, 0, 1.30 * np.tan(np.radians(22))]
    return [tuple(eye), tuple(focus), (0, 0, 1)]


def at(lay, r, deg):
    """A point on the plywood r from J1, deg anticlockwise from +x."""
    t = np.radians(deg)
    return np.array([lay["arm"][0] + r * np.cos(t), lay["arm"][1] + r * np.sin(t), B.PLY_T])


def figure(piper, name, title, res, bands):
    lay = X.layout(name, res["back_mm"] / 1e3)
    parts = scene(piper, lay, res)
    ghost = []
    if res["best"] is None:
        e, pc, nc = next((s for s in X.spots(lay) if s[0] == "front"))
        sp = next(s for s in res["spots"] if s["edge"] == "front")
        M = X.combo_M(lay)
        p = trimesh.transform_points([[*sp["spot_mm"], 0.0]], M)[0]
        p[2] = B.PLY_T + X.BED_TOP + 0.036
        n = M[:3, :3] @ np.r_[nc, 0.0] * 1e3
        ghost = gripper_ghost(piper, p, n)
    j1 = np.array([*lay["arm"], B.PLY_T])
    best = res["best"] or res["above"]
    pts = {"grip": np.array(best["p"]), "j1": j1}
    if ghost:
        pts["ghost"] = p
        g, tool = p, n
    else:
        g = np.array(best["p"])
        tool = (X.arm_M(lay) @ X.Arm.flange(_ARM, np.array(best["q"])))[:3, 2]

    # 3D: the arm at the bed
    cam = close_camera(lay, g, tool, j1)
    close = [pt for pt in parts if pt[0] not in ("frame", "cloth")]
    img3, p3 = render(close + ghost, cam, (1250, 1000), pts, view_angle=30)

    # plan: where each grasp works at bed height
    plan = [(n_, m, c, op) for n_, m, c, op in parts if n_ not in ("cloth",)]
    z = B.PLY_T + 0.0015
    plan.append(("band", sector(*lay["arm"], *bands["above"], z), TOP_C, 0.30))
    plan.append(("band", sector(*lay["arm"], *bands["level"], z + 0.0005), OK_C, 0.30))
    M = X.combo_M(lay)
    marks = {}
    for k, s in enumerate(res["spots"]):
        w = trimesh.transform_points([[*s["spot_mm"], 0.0]], M)[0]
        w[2] = B.PLY_T + X.BED_TOP + 0.002
        plan.append(("spot", trimesh.creation.cylinder(0.009, 0.004).apply_translation(w), OK_C if s["ok"] else NO_C, 1.0))
        marks[f"s{k}"] = w
    camT = [(0.0, -0.02, 5.0), (0.0, -0.02, 0.0), (0, -1, 0)]
    ptsT = dict(marks, j1=j1, door=np.array([0.0, -B.P2 - 0.045, B.PLY_T]), front=np.array([0.0, B.P2 + 0.05, B.PLY_T]),
                wall=np.array([B.P2 + 0.05, -0.30, B.PLY_T]), right=np.array([-B.P2 - 0.05, -0.30, B.PLY_T]),
                estop=np.array([-B.P2 + 0.07, B.P2 + 0.05, B.PLY_T]),
                lvl=at(lay, np.mean(bands["level"]), 215), top=at(lay, np.mean(bands["above"]), 325))
    if name in ("moved", "people"):
        ptsT["j1_old"] = np.array([0.0, 0.0, B.PLY_T])
    imgT, pT = render(plan, camT, (1000, 1000), ptsT, parallel_scale=0.70)

    # compose
    W, H = (1250 + 1000) / 150, 1080 / 150
    fig = plt.figure(figsize=(W, H), dpi=150, facecolor=SURFACE)
    top = 80 / 1080
    a3 = fig.add_axes([0, 0, 1250 / 2250, 1 - top])
    aT = fig.add_axes([1250 / 2250, 0, 1000 / 2250, 1 - top])
    for ax, img in ((a3, img3), (aT, imgT)):
        ax.imshow(img)
        ax.set_xlim(0, img.shape[1])
        ax.set_ylim(img.shape[0], 0)
        ax.axis("off")
    ok = res["best"] is not None
    fig.text(0.012, 1 - top / 2, title.format(back=res["back_mm"]), fontsize=17, color=INK, va="center")
    verdict = [("level", ok), ("from above", res["above"] is not None)]
    x = 0.985
    for label, good in reversed(verdict):
        t = fig.text(x, 1 - top / 2, f"{'✓' if good else '✗'} {label}", fontsize=17, va="center", ha="right",
                     color=OK_H if good else NO_H, fontweight="bold")
        fig.canvas.draw()
        bb = t.get_window_extent().transformed(fig.transFigure.inverted())
        x = bb.x0 - 0.02
    tag = dict(fontsize=17, ha="center", va="center", fontweight="bold",
               bbox=dict(boxstyle="round,pad=0.25", fc=SURFACE, ec="none", alpha=0.9))
    if ghost:
        a3.annotate("✗ level", p3["ghost"], p3["ghost"] + [-170, 150], color=NO_H, **tag,
                    arrowprops=dict(arrowstyle="-", color=NO_H, lw=1.4))
        a3.annotate("✓ from above", p3["grip"], p3["grip"] + [120, -260], color=OK_H, **tag,
                    arrowprops=dict(arrowstyle="-", color=OK_H, lw=1.4))
    else:
        a3.annotate("✓ level", p3["grip"], p3["grip"] + [-150, 170], color=OK_H, **tag,
                    arrowprops=dict(arrowstyle="-", color=OK_H, lw=1.4))
    side = dict(fontsize=10, color=MUTED, ha="center", va="center")
    aT.text(*pT["wall"], "block wall", rotation=90, **side)
    aT.text(*pT["right"], "right side", rotation=90, **side)
    aT.text(*pT["door"], "door", **side)
    aT.text(*pT["front"], "front (open)", **side)
    aT.text(*pT["estop"], "E-stop", fontsize=10, color=NO_H, ha="center", va="center", fontweight="bold")
    aT.plot(*pT["j1"], marker="+", color=INK, ms=12, mew=1.6)
    if "j1_old" in pT:
        aT.plot(*pT["j1_old"], marker="o", mfc="none", color=MUTED, ms=11, mew=1.2)
        aT.annotate("", pT["j1"], pT["j1_old"], arrowprops=dict(arrowstyle="-|>", color=INK, lw=1.4, shrinkA=7, shrinkB=7))
    lab = dict(fontsize=11, ha="center", va="center", fontweight="bold",
               bbox=dict(boxstyle="round,pad=0.2", fc=SURFACE, ec="none", alpha=0.85))
    aT.text(*pT["lvl"], "level", color=OK_H, **lab)
    aT.text(*pT["top"], "from\nabove", color=TOP_H, **lab)
    out = HERE / f"access-{name}.png"
    fig.savefig(out, facecolor=SURFACE)
    plt.close(fig)
    return out


_ARM = None


def main():
    global _ARM
    res = json.loads((HERE / "access.json").read_text())
    _ARM = X.Arm()
    piper = _ARM.p
    for name, title in FIGS:
        print(figure(piper, name, title, res[name], res["bands_m"]))


if __name__ == "__main__":
    main()
