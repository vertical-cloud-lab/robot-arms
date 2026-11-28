"""Top-down map and fingertip height of the 2026-10-16 place on the moved shelf (issue #19).

    python plot_place.py   # reads stage3_trace.csv here, writes place_map.png
"""
import csv
import math
import os
import sys

import matplotlib.pyplot as plt
from matplotlib.patches import Circle, Polygon

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "..", "scripts"))
from piper_pick_tape import fk_all, tip  # noqa: E402

rows = list(csv.DictReader(open(os.path.join(HERE, "stage3_trace.csv"))))
t, x, y, z, w, e, ph = [], [], [], [], [], [], []
for r in rows[::2]:
    if r["phase"] in ("estop", "reset", "disable"):  # parked: the reading after reset is not a pose
        break
    P = tip(fk_all([float(r[f"j{i}"]) for i in range(1, 7)])[5], 150.0)
    t.append(float(r["t"])); x.append(P[0]); y.append(P[1]); z.append(P[2])
    w.append(float(r["grip_mm"])); e.append(abs(float(r["grip_nm"]))); ph.append(r["phase"])

fig = plt.figure(figsize=(12, 5.6), constrained_layout=True)
gs = fig.add_gridspec(2, 2, width_ratios=[1.05, 1], height_ratios=[2, 1])
ax = fig.add_subplot(gs[:, 0])
ax.add_patch(Circle((0, 0), 50, color="#2b2b2b", zorder=3))
ax.text(0, -75, "base (J1 axis)", ha="center", fontsize=9, color="#444")
ax.add_patch(Circle((247, 0), 24, fc="#7cc242", ec="#2b2b2b", zorder=3))
ax.text(247, -45, "roll, picked\nJ1 = 0°", ha="center", va="top", fontsize=9, color="#444")
# shelf corners as estimated from the camera before the run (rough, about ±40 mm)
ax.add_patch(Polygon([(-376, 208), (-138, 208), (-75, 351), (-313, 351)], closed=True,
                     fc="#cfcfcf", ec="#2b2b2b", hatch="..", zorder=1, alpha=0.8))
ax.text(-226, 380, "black shelf (camera estimate)", ha="center", fontsize=9, color="#444")
px, py = 360 * math.cos(math.radians(130)), 360 * math.sin(math.radians(130))
ax.add_patch(Circle((px, py), 24, fc="#7cc242", ec="#2b2b2b", zorder=3))
sc = ax.scatter(x, y, c=t, cmap="viridis", s=4, zorder=4)
fig.colorbar(sc, ax=ax, label="time (s)", shrink=0.7)
ax.annotate("carry on an arc\naround the base", (150, 360), fontsize=9, color="#444")
ax.set_aspect("equal"); ax.set_xlim(-450, 420); ax.set_ylim(-150, 480)
ax.set_xlabel("x (mm)"); ax.set_ylabel("y (mm)")
ax.set_title("Fingertips seen from above", loc="left")
for s in ("top", "right"):
    ax.spines[s].set_visible(False)

a2 = fig.add_subplot(gs[0, 1])
a2.plot(t, z, color="#1f5f99", lw=2)
a2.axhline(60, color="#888", lw=1, ls="--"); a2.text(t[-1], 62, "shelf top", ha="right", fontsize=8, color="#666")
for lab, tt in (("grasp", 8.1), ("lift", 15.0), ("release", 44.3)):
    a2.axvline(tt, color="#bbb", lw=1); a2.text(tt + 0.4, 190, lab, fontsize=8, color="#666")
a2.set_ylabel("fingertip z (mm)"); a2.set_title("Height and grip over the run", loc="left")
a3 = fig.add_subplot(gs[1, 1], sharex=a2)
a3.plot(t, e, color="#b5523b", lw=2)
a3.axhline(1.0, color="#888", lw=1, ls="--"); a3.text(t[-1], 1.25, "asked for 1.0", ha="right", fontsize=8, color="#666")
a3.set_ylabel("grip effort (N·m)"); a3.set_xlabel("time (s)")
for a in (a2, a3):
    for s in ("top", "right"):
        a.spines[s].set_visible(False)
    a.grid(axis="y", color="#eee")
fig.savefig(os.path.join(HERE, "place_map.png"), dpi=130)
