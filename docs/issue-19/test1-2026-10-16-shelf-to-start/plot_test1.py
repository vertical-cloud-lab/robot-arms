"""Test 1 (2026-10-16): the roll from the shelf back to the start, and the camera fit it gave.

    python plot_test1.py   # reads test1_trace.csv, test1_roll_detections.csv,
                           # frame_after_place.jpg and ../../../scripts/camera.json
"""
import bisect
import csv
import json
import math
import os
import sys

import matplotlib.image as mpimg
import matplotlib.pyplot as plt
from matplotlib.patches import Circle, Polygon

HERE = os.path.dirname(os.path.abspath(__file__))
SCRIPTS = os.path.join(HERE, "..", "..", "..", "scripts")
sys.path.insert(0, SCRIPTS)
from piper_pick_tape import fk_all, tip  # noqa: E402
from piper_seek_tape import Cam  # noqa: E402

BLUE, ORANGE, AQUA, INK, MUTED = "#2a78d6", "#eb6834", "#1baf7a", "#222222", "#6b6b6b"
cam = Cam(os.path.join(SCRIPTS, "camera.json"))
camj = json.load(open(os.path.join(SCRIPTS, "camera.json")))
off = camj["time_offset_s"]

rows = list(csv.DictReader(open(os.path.join(HERE, "test1_trace.csv"))))
T = [float(r["t"]) for r in rows]
held = {}  # trace index -> roll centre (fingertips 28 mm into a 49 mm roll)
path = []
for i, r in enumerate(rows):
    if r["phase"] in ("up", "hold", "place"):
        T6 = fk_all([float(r[f"j{j}"]) for j in range(1, 7)])[5]
        tp = tip(T6, 150.0)
        c = [a - 3.5 * T6[k][2] for k, a in enumerate(tp)]
        held[i] = c
        path.append(c)

# detections (bbox bottom = the roll's lowest point) against the model's projection
det, pred = [], []
for r in csv.DictReader(open(os.path.join(HERE, "test1_roll_detections.csv"))):
    if int(r["area"]) < 300 or not (140 <= float(r["cx"]) <= 1520 and float(r["cy"]) >= 850):
        continue
    det.append((float(r["t"]) + off, int(r["x0"]) + int(r["bw"]) / 2, int(r["y0"]) + int(r["bh"])))
resid = []
for tt, u, v in det:
    i = min(bisect.bisect_left(T, tt), len(T) - 1)
    if i in held:
        c = held[i]
        pu, pv, _ = cam.project([c[0], c[1], c[2] - 24.5])
        pu += camj["held_offset_px"][0]
        pv += camj["held_offset_px"][1]
        pred.append((pu, pv, u, v))
        resid.append(math.hypot(pu - u, pv - v))
resid.sort()
med = resid[len(resid) // 2]

fig = plt.figure(figsize=(12.5, 5.4), constrained_layout=True)
gs = fig.add_gridspec(1, 2, width_ratios=[1, 1.15])
ax = fig.add_subplot(gs[0, 0])
ax.add_patch(Circle((0, 0), 50, color="#2b2b2b", zorder=3))
ax.text(0, -78, "arm base", ha="center", fontsize=9, color=MUTED)
ax.add_patch(Polygon([(-376, 208), (-138, 208), (-75, 351), (-313, 351)], closed=True,
                     fc="#d9d9d9", ec="#555", zorder=1))
ax.text(-226, 190, "black shelf (60 mm)", ha="center", va="top", fontsize=9, color=MUTED)
xs, ys = [p[0] for p in path], [p[1] for p in path]
ax.plot(xs, ys, color=BLUE, lw=2, zorder=4)
ax.annotate("", xy=(xs[len(xs) // 2 + 15], ys[len(ys) // 2 + 15]), xytext=(xs[len(xs) // 2], ys[len(ys) // 2]),
            arrowprops=dict(arrowstyle="-|>", color=BLUE, lw=2), zorder=5)
ax.text(40, 320, "roll carried round the base\n(forward kinematics, 100 Hz)", fontsize=9, color=BLUE)
for (x, y), lab, va in (((-231, 276), "picked here\nJ1 = 130°, r = 360", "bottom"), ((247, 0), "set down here\nJ1 = 0°, r = 247", "top")):
    ax.add_patch(Circle((x, y), 24, fc=AQUA, ec=INK, zorder=6))
    ax.text(x, y + (34 if va == "bottom" else -34), lab, ha="center", va=va, fontsize=9, color=INK)
Cw = [-sum(cam.R[k][i] * cam.t[k] for k in range(3)) for i in range(3)]  # camera centre
cxy = (Cw[0], Cw[1])
ax.plot(*cxy, marker="^", color=INK, ms=10)
ax.text(cxy[0] + 25, cxy[1], f"camera (fitted)\n{Cw[2]:.0f} mm up", fontsize=9, va="center", color=INK)
for tx, ty in ((-560, 520), (560, 230)):
    ax.plot([cxy[0], tx], [cxy[1], ty], color=MUTED, lw=1, ls="--")
ax.set_aspect("equal")
ax.set_xlim(-520, 520)
ax.set_ylim(-800, 460)
ax.set_xlabel("x (mm)")
ax.set_ylabel("y (mm)")
ax.set_title("Seen from above", loc="left", fontsize=11)
for s in ("top", "right"):
    ax.spines[s].set_visible(False)

a2 = fig.add_subplot(gs[0, 1])
img = mpimg.imread(os.path.join(HERE, "frame_after_place.jpg"))
X0, Y0 = 330, 300
a2.imshow(img, extent=(X0, X0 + img.shape[1], Y0 + img.shape[0], Y0))
pu = [p[0] for p in pred][::3]
pv = [p[1] for p in pred][::3]
du = [p[2] for p in pred][::3]
dv = [p[3] for p in pred][::3]
a2.plot(pu, pv, color=ORANGE, lw=2, label="camera model: where the arm says the roll is")
a2.scatter(du, dv, s=10, color=AQUA, edgecolor=INK, linewidths=0.3, zorder=5,
           label="camera: green blob, every 3rd frame")
a2.set_xlim(X0, X0 + img.shape[1])
a2.set_ylim(Y0 + img.shape[0], Y0)
a2.legend(loc="upper right", fontsize=8, frameon=True)
a2.set_title(f"The same carry in the camera: model vs detection, median {med:.1f} px apart",
             loc="left", fontsize=11)
a2.set_xticks([])
a2.set_yticks([])
fig.suptitle("Test 1: shelf to start, and the camera calibration it gave", x=0.01, ha="left",
             fontsize=13, fontweight="bold")
fig.savefig(os.path.join(HERE, "test1_figure.png"), dpi=110)
print(f"{len(resid)} held frames, median {med:.2f} px")
