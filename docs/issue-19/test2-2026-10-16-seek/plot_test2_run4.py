"""Test 2 (2026-10-16, run 4): the camera-guided seek that picked the hidden roll and stood it back at the start.

    python plot_test2_run4.py   # reads run4_trace.csv, run4_vision.csv and ../../../scripts/camera.json

Left: where the camera put the roll on the shelf (each frame's estimate spreads along the camera's line of sight),
the fingertip path the 100 Hz loop commanded (to the roll, then carrying it round the base), and where the camera
saw the roll after the release. Right: the commanded fingertip speed (one smooth profile while steering, no stops
between waypoints) and the fingertip height against the roll's height on the shelf and on the table. The trace
does not log the gripper close and release; their numbers come from run4.log.
"""
import csv
import math
import os
import sys

import matplotlib.pyplot as plt
from matplotlib.patches import Circle

HERE = os.path.dirname(os.path.abspath(__file__))
SCRIPTS = os.path.join(HERE, "..", "..", "..", "scripts")
sys.path.insert(0, SCRIPTS)
from piper_seek_tape import Cam  # noqa: E402

BLUE, ORANGE, AQUA, INK, MUTED = "#2a78d6", "#eb6834", "#1baf7a", "#222222", "#6b6b6b"
SHELF, ROLL = 60.0, 49.0  # shelf top and the roll's height standing on its edge, mm
TO_ROLL = ("to_look", "approach", "down")
WITH_ROLL = ("lift", "carry", "place")

cam = Cam(os.path.join(SCRIPTS, "camera.json"))
Cw = [-sum(cam.R[k][i] * cam.t[k] for k in range(3)) for i in range(3)]
rows = list(csv.DictReader(open(os.path.join(HERE, "run4_trace.csv"))))
vis = [r for r in csv.DictReader(open(os.path.join(HERE, "run4_vision.csv"))) if r["u"]]
t0 = float(rows[0]["t"])
start = {}
for r in rows:
    start.setdefault(r["phase"], float(r["t"]) - t0)

paths = {"to": [], "with": []}
tt, sp, zz, ph = [], [], [], []
hist = []  # the trace logs r, az, z to 0.01, so speed is taken over 10 ticks (0.1 s)
for r in rows:
    if r["phase"] in ("home", "park"):  # home is a joint-space move; the trace stops updating r, az, z
        break
    if not r["r"]:
        continue
    rr, az, z, t = float(r["r"]), float(r["az"]), float(r["z"]), float(r["t"]) - t0
    xy = (rr * math.cos(math.radians(az)), rr * math.sin(math.radians(az)))
    if r["phase"] in TO_ROLL + WITH_ROLL:
        paths["to" if r["phase"] in TO_ROLL else "with"].append(xy)
    hist.append((t, rr, az, z))
    if len(hist) > 10:
        p0 = hist[-11]
        if t - p0[0] < 0.15:  # skip the gaps where the gripper closes and opens
            dr, da, dz = rr - p0[1], math.radians(az - p0[2]) * rr, z - p0[3]
            tt.append(t)
            sp.append(math.sqrt(dr * dr + da * da + dz * dz) / 0.1)
            zz.append(z)
            ph.append(r["phase"])
on_shelf = [r for r in vis if float(r["t"]) - t0 < start["lift"] and r["x60"]]
after = [r for r in vis if float(r["t"]) - t0 > start["rise"] + 6 and r["x0"]]
med = lambda v: sorted(v)[len(v) // 2]
put = (med([float(r["x0"]) for r in after]), med([float(r["y0"]) for r in after]))
est = [(float(r["ex"]), float(r["ey"])) for r in rows if r["ex"]][-1]

fig = plt.figure(figsize=(13, 6.2), constrained_layout=True)
gs = fig.add_gridspec(2, 2, width_ratios=[1.0, 1.05], height_ratios=[1, 1])
ax = fig.add_subplot(gs[:, 0])
ax.add_patch(Circle((0, 0), 50, color="#2b2b2b", zorder=3))
ax.text(0, -80, "arm base", ha="center", fontsize=9, color=MUTED)
ax.plot([Cw[0], est[0] + 0.5 * (est[0] - Cw[0])], [Cw[1], est[1] + 0.5 * (est[1] - Cw[1])],
        color=MUTED, lw=1, ls="--", zorder=2)
ax.plot(Cw[0], Cw[1], marker="^", color=INK, ms=10)
ax.text(Cw[0] + 25, Cw[1], "camera", fontsize=9, va="center", color=INK)
ax.text(-560, -600, "dashed: the camera's line of sight;\nat the shelf, 1 px is ~10 mm along it",
        fontsize=8.5, color=MUTED)
ax.plot(*zip(*paths["to"]), color=BLUE, lw=2, zorder=5)
ax.plot(*zip(*paths["with"]), color=ORANGE, lw=2, zorder=5)
xs, ys = [float(r["x60"]) for r in on_shelf][::8], [float(r["y60"]) for r in on_shelf][::8]
ax.scatter(xs, ys, s=26, color=AQUA, edgecolor=INK, linewidths=0.4, zorder=7)
ax.annotate(f"roll at the back of the 60 mm shelf, as the\ncamera saw it ({len(on_shelf)} frames, one dot per 8)",
            xy=(min(xs), ys[xs.index(min(xs))]), xytext=(-560, 480), fontsize=9, color=INK,
            arrowprops=dict(arrowstyle="-", color=INK, lw=0.8))
ax.plot([330, 380], [330, 330], color=BLUE, lw=2)
ax.text(390, 330, "fingertips to the roll,\nsteered on every frame", fontsize=9, color=INK, va="center")
ax.plot([-170, -120], [190, 190], color=ORANGE, lw=2)
ax.text(-110, 190, "carrying the roll\nround the base", fontsize=9, color=INK, va="center")

ax.plot(247, 0, marker="o", ms=15, mfc="none", mec=INK, mew=1.2, zorder=6)
ax.plot(*put, marker="o", ms=8, color=AQUA, mec=INK, mew=0.8, zorder=8)
ax.annotate(f"start spot (r = 247 mm, 0°) and where the\ncamera saw the roll after the release:\n"
            f"r = {math.hypot(*put):.0f} mm, {math.degrees(math.atan2(put[1], put[0])):.1f}°, standing",
            xy=(put[0] - 4, put[1] - 12), xytext=(60, -330), fontsize=9, color=INK,
            arrowprops=dict(arrowstyle="-", color=INK, lw=0.8))
ax.set_aspect("equal")
ax.set_xlim(-580, 580)
ax.set_ylim(-790, 560)
ax.set_xlabel("x (mm)")
ax.set_ylabel("y (mm)")
ax.set_title("Seen from above", loc="left", fontsize=11)
for s in ("top", "right"):
    ax.spines[s].set_visible(False)

names = {"approach": "steer to the roll", "down": "down", "lift": "lift",
         "carry": "carry round the base", "place": "set down", "rise": "rise", "home": "home"}
bands = []
for t, p in zip(tt, ph):
    if not bands or bands[-1][0] != p:
        bands.append([p, t, t])
    bands[-1][2] = t
a2 = fig.add_subplot(gs[0, 1])
a3 = fig.add_subplot(gs[1, 1], sharex=a2)
for a, top in ((a2, 62), (a3, 196)):
    a.axvspan(0, start["approach"], color="#f1f1f1", zorder=0, lw=0)
    if a is a2:
        a.text(start["approach"] / 2, 30, "rise out\nof view", ha="center", va="top", fontsize=8, color=MUTED)
    for k, (p, b0, b1) in enumerate(bands):
        a.axvspan(b0, b1, color="#f1f1f1" if k % 2 else "#e6e6e6", zorder=0, lw=0)
        if a is a2 and b1 - b0 > 3.5:  # the rise after the release is labelled too
            a.text((b0 + b1) / 2, top - 6, names.get(p, p), ha="center", fontsize=8, color=MUTED)
    for s in ("top", "right"):
        a.spines[s].set_visible(False)
a2.plot(tt, sp, color=BLUE, lw=2, zorder=3)
for v, txt in ((50, "speed cap 50 mm/s"), (20, "20 mm/s straight up and down")):
    a2.axhline(v, color=MUTED, lw=1, ls="--", zorder=1)
    a2.text(start["home"] + 6.5, v + 1, txt, fontsize=8, color=MUTED, ha="right")
a2.set_ylim(0, 62)
a2.set_ylabel("fingertip speed (mm/s)")
a2.set_title("One continuous move, re-aimed on every camera frame", loc="left", fontsize=11)
a2.grid(axis="y", color="#e2e2e2")
a2.tick_params(labelbottom=False)

a3.plot(tt, zz, color=BLUE, lw=2, zorder=3)
g0, g1 = start["down"], start["lift"]
a3.fill_between([g0, g1 + 1], SHELF, SHELF + ROLL, color=AQUA, alpha=0.25, lw=0, zorder=1)
a3.text(g0 - 1, SHELF + ROLL / 2, "roll on\nthe shelf", ha="right", va="center", fontsize=8, color=INK)
p0, p1 = start["place"], start["rise"]
a3.fill_between([p0 + 4, p1 + 2], 0, ROLL, color=AQUA, alpha=0.25, lw=0, zorder=1)
a3.text(p1 + 2.5, 12, "roll at\nthe start", ha="left", va="center", fontsize=8, color=INK)
a3.annotate("close: fingers stop at 18.3 mm\n(5.9 N·m peak, asked 1.0), then\nhold 1.9 N·m with no slip",
            xy=(g1 - 1, 83), xytext=(37, 150), fontsize=8, color=INK,
            arrowprops=dict(arrowstyle="-", color=INK, lw=0.8))
a3.annotate("open with the roll\n5 mm above the table", xy=(p1 - 1, 27), xytext=(48, 15),
            fontsize=8, color=INK, ha="right", arrowprops=dict(arrowstyle="-", color=INK, lw=0.8))
a3.set_ylim(0, 200)
a3.set_xlim(0, start["home"] + 7)
a3.text(start["home"] + 0.5, 100, "then home\nin joint\nspace", fontsize=8, color=MUTED, va="center")
a3.set_ylabel("fingertip height (mm)")
a3.set_xlabel("time since the motors came on (s)")
a3.set_title("Fingertip height against the roll", loc="left", fontsize=11)
a3.grid(axis="y", color="#e2e2e2")
fig.suptitle("Test 2: the camera found the hidden roll; the arm picked it off the shelf and stood it back at the start",
             x=0.01, ha="left", fontsize=13, fontweight="bold")
fig.savefig(os.path.join(HERE, "test2_run4_figure.png"), dpi=110)
print("placed at", put, "r", math.hypot(*put), "estimate", est)
