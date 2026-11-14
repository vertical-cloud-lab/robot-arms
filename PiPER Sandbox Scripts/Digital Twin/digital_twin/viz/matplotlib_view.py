"""A matplotlib 3D view of the cell: works with any engine and needs nothing beyond
matplotlib. The arm is drawn from its DH frames, the cell objects and prints as boxes.

    view = MatplotlibView(sim)        # interactive window (plt.ion)
    view.sync()                       # redraw at the current state
    img = MatplotlibView(sim, show=False).image()   # RGB array, for videos
"""
from __future__ import annotations

import numpy as np

from ..world.print_library import bounds


def _box_edges(lo, hi, T):
    c = np.array([[x, y, z] for x in (lo[0], hi[0]) for y in (lo[1], hi[1]) for z in (lo[2], hi[2])])
    c = c @ T[:3, :3].T + T[:3, 3]
    edges = [(0, 1), (2, 3), (4, 5), (6, 7), (0, 2), (1, 3), (4, 6), (5, 7), (0, 4), (1, 5), (2, 6), (3, 7)]
    return [(c[a], c[b]) for a, b in edges]


class MatplotlibView:
    def __init__(self, sim, show: bool = True, size=(960, 540)):
        import matplotlib
        if not show:
            matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        self.plt, self.sim = plt, sim
        if show:
            plt.ion()
        dpi = 100
        self.fig = plt.figure(figsize=(size[0] / dpi, size[1] / dpi), dpi=dpi)
        self.ax = self.fig.add_subplot(111, projection="3d")
        self.static = self._static_boxes()

    def _static_boxes(self):
        out = []
        for b, T in self.sim.cell.scene.root.walk():
            if b.kind in ("print", "robot") or not b.geoms:
                continue
            if b.name == "shelf":  # one outline instead of every strip between the holes
                W, D, t = np.asarray(self.sim.cfg.cell["shelf"]["size"]) / 1000
                out.append((T, -np.array([W / 2, D / 2, t]), np.array([W / 2, D / 2, 0]), b.name))
                continue
            for g in b.geoms:
                if g.collide == "none" or g.type not in ("box", "cylinder"):
                    continue
                s = np.asarray(g.size if g.type == "box" else (g.size[0], g.size[0], g.size[1]))
                out.append((T @ g.pose, -s, s, b.name))
        return out

    def draw(self):
        ax, e, kin = self.ax, self.sim.engine, self.sim.kin
        ax.cla()
        colors = {"table": "#c8a878", "printer": "#9aa0a6", "printer_bed": "#333333", "plate": "#222222",
                  "shelf": "#111111", "box": "#e85aa0", "rest_stand": "#b08850"}
        for T, lo, hi, name in self.static:
            if name == "table":
                continue
            for a, b in _box_edges(lo, hi, T):
                ax.plot(*zip(a, b), color=colors.get(name, "#888888"), lw=0.6)
        # Arm: base -> DH frames -> TCP.
        q = e.arm_q()
        base = self.sim.cell.arm_pose
        pts = [base[:3, 3]] + [(base @ F)[:3, 3] for F in kin.frames(q)] + [(base @ kin.fk(q))[:3, 3]]
        pts = np.array(pts)
        ax.plot(pts[:, 0], pts[:, 1], pts[:, 2], "-o", color="#202024", lw=4, ms=3)
        T = base @ kin.fk(q)
        gap = 2 * (e.gripper_travel() - self.sim.robot.sleeve_t)
        for s in (-1, 1):
            p0 = T[:3, 3] + T[:3, 1] * s * (gap / 2 + 0.003)
            p1 = p0 - T[:3, 2] * 0.058
            ax.plot(*zip(p0, p1), color="#444444", lw=3)
        for name in e.print_names():
            b = self.sim.cell.scene.body(name)
            lo, hi = bounds(b.geoms)
            col = b.geoms[0].rgba[:3]
            for a, c in _box_edges(lo, hi, e.body_pose(name)):
                ax.plot(*zip(a, c), color=col, lw=1.2)
        ax.set_xlim(-0.55, 0.45)
        ax.set_ylim(-0.4, 0.45)
        ax.set_zlim(0, 0.6)
        ax.set_box_aspect((1.0, 0.85, 0.6))
        ax.view_init(elev=28, azim=-100)
        ax.set_title(f"t = {e.time:5.1f} s ({e.name} engine)", fontsize=9)
        ax.set_xlabel("x (m)")
        ax.set_ylabel("y (m)")

    def sync(self):
        self.draw()
        self.plt.pause(0.001)

    def is_running(self):
        return self.plt.fignum_exists(self.fig.number)

    def image(self) -> np.ndarray:
        self.draw()
        self.fig.canvas.draw()
        buf = np.asarray(self.fig.canvas.buffer_rgba())
        return buf[:, :, :3].copy()
