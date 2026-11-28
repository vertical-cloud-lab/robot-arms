"""Test 2 (2026-10-16, run 2): the camera-guided seek for the hidden roll.

    python plot_test2.py   # reads run2_trace.csv, run2_vision.csv and ../../../scripts/camera.json

Left: where the camera put the roll (each frame's estimate on the shelf's height, which spreads
along the camera's line of sight), the fingertip path the 100 Hz loop commanded, and the same
path turned by the 7.9 deg the J1 reading jumped when the motors were enabled, which is where
the camera shows the gripper really went. Right: the commanded fingertip speed: one smooth
profile, no stops between waypoints.
"""
import csv
import math
import os
import sys

import matplotlib.pyplot as plt
from matplotlib.patches import Circle, Polygon

HERE = os.path.dirname(os.path.abspath(__file__))
SCRIPTS = os.path.join(HERE, "..", "..", "..", "scripts")
sys.path.insert(0, SCRIPTS)
from piper_seek_tape import Cam  # noqa: E402

BLUE, ORANGE, AQUA, INK, MUTED = "#2a78d6", "#eb6834", "#1baf7a", "#222222", "#6b6b6b"
J1_JUMP = 3.98 - (-3.91)  # J1 read -3.91 deg before enabling and +3.98 after, without moving

cam = Cam(os.path.join(SCRIPTS, "camera.json"))
Cw = [-sum(cam.R[k][i] * cam.t[k] for k in range(3)) for i in range(3)]
rows = list(csv.DictReader(open(os.path.join(HERE, "run2_trace.csv"))))
vis = [r for r in csv.DictReader(open(os.path.join(HERE, "run2_vision.csv"))) if r["u"]]
t0 = float(rows[0]["t"])

cmd, phys, tt, sp, ph = [], [], [], [], []
hist = []  # the trace logs r, az, z to 0.01, so speed is taken over 10 ticks (0.1 s)
for r in rows:
    if not r["r"]:
        continue
    rr, az, z, t = float(r["r"]), float(r["az"]), float(r["z"]), float(r["t"]) - t0
    if r["phase"] in ("home", "park", "gripper"):
        break
    cmd.append((rr * math.cos(math.radians(az)), rr * math.sin(math.radians(az))))
    a2 = math.radians(az - J1_JUMP)
    phys.append((rr * math.cos(a2), rr * math.sin(a2)))
    hist.append((rr, az, z))
    if len(hist) > 10:  # the loop advances its state one 10 ms step per logged tick
        p0 = hist[-11]
        dr, da, dz = rr - p0[0], math.radians(az - p0[1]) * rr, z - p0[2]
        tt.append(t)
        sp.append(math.sqrt(dr * dr + da * da + dz * dz) / 0.1)
        ph.append(r["phase"])
est = [(float(r["ex"]), float(r["ey"])) for r in rows if r["ex"]][-1]

fig = plt.figure(figsize=(12.5, 5.6), constrained_layout=True)
gs = fig.add_gridspec(1, 2, width_ratios=[1.05, 1])
ax = fig.add_subplot(gs[0, 0])
ax.add_patch(Circle((0, 0), 50, color="#2b2b2b", zorder=3))
ax.text(0, -80, "arm base", ha="center", fontsize=9, color=MUTED)
ax.add_patch(Polygon([(-376, 208), (-138, 208), (-75, 351), (-313, 351)], closed=True,
                     fc="#d9d9d9", ec="#555", zorder=1))
ax.text(-226, 190, "shelf (rough outline)", ha="center", va="top", fontsize=9, color=MUTED)
ax.plot([Cw[0], est[0] + 0.6 * (est[0] - Cw[0])], [Cw[1], est[1] + 0.6 * (est[1] - Cw[1])],
        color=MUTED, lw=1, ls="--")
ax.plot(Cw[0], Cw[1], marker="^", color=INK, ms=10)
ax.text(Cw[0] + 25, Cw[1], "camera", fontsize=9, va="center", color=INK)
ax.text(-205, -260, "camera's line of sight:\n1 px up or down = ~10 mm along it", fontsize=8.5, color=MUTED)
xs = [float(r["x60"]) for r in vis][::4]
ys = [float(r["y60"]) for r in vis][::4]
ax.scatter(xs, ys, s=30, color=AQUA, edgecolor=INK, linewidths=0.4, zorder=7)
ax.annotate("roll as the camera saw it\n(one dot per 4 frames)", xy=(xs[0], ys[0]), xytext=(-545, 40),
            fontsize=9, color=INK, arrowprops=dict(arrowstyle="-", color=INK, lw=0.8))
ax.plot([p[0] for p in cmd], [p[1] for p in cmd], color=BLUE, lw=2, zorder=5)
ax.text(330, 120, "fingertips, as commanded\n(J1 reading)", fontsize=9, color=BLUE)
ax.plot([p[0] for p in phys], [p[1] for p in phys], color=ORANGE, lw=2, ls=(0, (4, 2)), zorder=5)
ax.text(150, 380, f"where they went: J1 reading\nwas {J1_JUMP:.1f}° high (camera agrees)",
        fontsize=9, color=ORANGE)
ax.plot(*phys[-1], marker="X", color=ORANGE, ms=11, mec=INK, zorder=6)
ax.plot(*cmd[-1], marker="o", color=BLUE, ms=8, mec=INK, zorder=6)
ax.set_aspect("equal")
ax.set_xlim(-560, 560)
ax.set_ylim(-800, 520)
ax.set_xlabel("x (mm)")
ax.set_ylabel("y (mm)")
ax.set_title("Seen from above", loc="left", fontsize=11)
for s in ("top", "right"):
    ax.spines[s].set_visible(False)

a2 = fig.add_subplot(gs[0, 1])
bands = []
for t, p in zip(tt, ph):
    if not bands or bands[-1][0] != p:
        bands.append([p, t, t])
    bands[-1][2] = t
names = {"seek": "look", "approach": "steer to the roll", "down": "down", "close": "close",
         "up": "no grip: up", "release": "open"}
for k, (p, a, b) in enumerate(bands):
    if p in names and b - a > 1.0:
        a2.axvspan(a, b, color="#f1f1f1" if k % 2 else "#e6e6e6", zorder=0)
        a2.text((a + b) / 2, 54, names[p], ha="center", fontsize=8.5, color=MUTED)
a2.plot(tt, sp, color=BLUE, lw=2)
a2.axhline(50, color=MUTED, lw=1, ls="--")
a2.text(tt[-1], 51, "speed cap 50 mm/s", fontsize=8, color=MUTED, ha="right")
a2.set_ylim(0, 58)
a2.set_xlabel("time since the motors came on (s)")
a2.set_ylabel("commanded fingertip speed (mm/s)")
a2.set_title("One continuous move, re-aimed on every frame", loc="left", fontsize=11)
for s in ("top", "right"):
    a2.spines[s].set_visible(False)
a2.grid(axis="y", color="#eee")
fig.suptitle("Test 2: the camera found the roll; the grasp missed because J1's reading had shifted",
             x=0.01, ha="left", fontsize=13, fontweight="bold")
fig.savefig(os.path.join(HERE, "test2_figure.png"), dpi=110)
print("estimate", est, "commanded end", cmd[-1], "physical end", phys[-1])
