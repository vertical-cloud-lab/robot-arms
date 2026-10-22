#!/usr/bin/env python3
"""Plot the first successful tape pick (issue #19, 2026-10-15) from its 100 Hz trace.

    pip install matplotlib
    python docs/issue-19/stage3-2026-10-15-pick/plot_pick_trace.py

Fingertip height comes from the measured joints through the script's forward kinematics
(tcp 150 mm); the gripper opening and effort are the gripper's own feedback.
"""
import csv
import os
import sys

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "..", "scripts"))
import piper_pick_tape as P  # noqa: E402

SURF, INK, INK2, MUTED, GRID, BAND = "#fcfcfb", "#0b0b0b", "#52514e", "#898781", "#e1e0d9", "#f0efec"
BLUE = "#2a78d6"
T0, T1 = 9.0, 35.5  # descent start to the end of the rise after letting go

rows = [r for r in csv.DictReader(open(os.path.join(HERE, "stage3_trace.csv")))
        if T0 <= float(r["t"]) <= T1]
t = [float(r["t"]) - T0 for r in rows]
z = [P.tip(P.fk_all([float(r[f"j{i}"]) for i in range(1, 7)])[5], 150.0)[2] for r in rows]
w = [float(r["grip_mm"]) for r in rows]
e = [abs(float(r["grip_nm"])) for r in rows]

phases = []  # (start, end, name) of each run of the same phase
for r, tt in zip(rows, t):
    if not phases or phases[-1][2] != r["phase"]:
        phases.append([tt, tt, r["phase"]])
    phases[-1][1] = tt
# the phases in order: down, close, lift, hold, set down, open, rise
LABELS = iter(["down", "close", "lift", "hold", "set down", "open", "rise"])

fig, axes = plt.subplots(3, 1, figsize=(9, 6.6), sharex=True, facecolor=SURF,
                         gridspec_kw={"hspace": 0.45})
panels = [(z, "Fingertip height above the table (mm)"), (w, "Gripper opening (mm)"),
          (e, "Gripper effort (N·m)")]
for ax, (y, title) in zip(axes, panels):
    ax.set_facecolor(SURF)
    for k, (a, b, name) in enumerate(phases):
        if name in ("close", "hold", "release"):
            ax.axvspan(a, b, color=BAND, lw=0, zorder=0)
    ax.plot(t, y, color=BLUE, lw=2, zorder=3)
    ax.set_title(title, loc="left", fontsize=10, color=INK)
    ax.grid(axis="y", color=GRID, lw=0.6)
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    for s in ("left", "bottom"):
        ax.spines[s].set_color(MUTED)
    ax.tick_params(colors=INK2, labelsize=8)
for a, b, name in phases:
    if name in ("down", "close", "up", "hold", "release"):
        axes[0].text((a + b) / 2, 122, next(LABELS), ha="center", va="bottom", fontsize=8, color=INK2)
axes[0].set_ylim(0, 140)
axes[0].axhline(49, color=MUTED, lw=1, ls=(0, (4, 3)), zorder=2)
axes[0].text(5.6, 52, "top of the roll, 49 mm", ha="left", va="bottom", fontsize=8, color=INK2)
axes[1].set_ylim(0, 70)
axes[1].annotate("stops on the roll at 27.4 mm", xy=(15.76 - T0, 27.6), xytext=(15.76 - T0 + 1.4, 45),
                 fontsize=8, color=INK2, arrowprops={"arrowstyle": "-", "color": MUTED, "lw": 0.8})
axes[2].set_ylim(0, 1.3)
axes[2].axhline(0.5, color=MUTED, lw=1, ls=(0, (4, 3)), zorder=2)
axes[2].text(T1 - T0, 0.53, "lift only above 0.5 N·m", ha="right", va="bottom", fontsize=8, color=INK2)
axes[2].set_xlabel("time from the start of the descent (s)", fontsize=9, color=INK2)
fig.savefig(os.path.join(HERE, "pick_trace.png"), dpi=130, bbox_inches="tight", facecolor=SURF)
print("wrote pick_trace.png")
