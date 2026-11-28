#!/usr/bin/env python3
"""Planning timeline for the November 2026 update (docs/update-2026-11/timeline.png).

Rows are the seven ranked projects; orange = build and prepare, blue = logged runs
(counted trials or timed steps). Dotted lines and grey bands are the deadlines and
windows from the calendar table in the update's section 7.
"""
import sys
from datetime import date, timedelta

import matplotlib

matplotlib.use("Agg")
import matplotlib.dates as mdates
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, Patch

SURFACE = "#ffffff"
TEXT = "#191919"
TEXT2 = "#666666"
GRID = "#e6e6e6"
BAND = "#f1f1f1"
PREP = "#f47230"   # categorical slot 2
RUNS = "#257de0"   # categorical slot 1

D = lambda m, d, y=None: date(y or (2026 if m >= 11 else 2027), m, d)

projects = [
    ("1  Intervention ledger", [(D(11, 30), D(12, 10), "p"), (D(12, 11), D(3, 31), "r")]),
    ("2  A1-mini plate clearing", [(D(11, 30), D(12, 9), "p"), (D(12, 10), D(12, 23), "r")]),
    ("3  DAL courier (stubs, jars, weighing)", [(D(12, 14), D(1, 3), "p"), (D(1, 4), D(2, 9), "r")]),
    ("4  Restocking the CubXL (#21)", [(D(12, 1), D(1, 29), "p"), (D(3, 5), D(3, 31), "r")]),
    ("5  PiPER metrology", [(D(12, 14), D(1, 10), "p"), (D(1, 11), D(2, 15), "r")]),
    ("6  Interventions as training data", [(D(2, 1), D(3, 4), "p"), (D(3, 5), D(3, 31), "r")]),
    ("7  Agent vs VLA vs script", [(D(2, 1), D(2, 28), "p"), (D(3, 1), D(3, 31), "r")]),
]
milestones = [
    (D(12, 1), "WRTG paper"),
    (D(12, 10), "toy drive starts"),
    (D(12, 18), "toy drive ends"),
    (D(1, 12), "Genesis fellowship"),
    (D(1, 29), "TMS drafts · #21 prereg"),
    (D(2, 26), "TMS submissions"),
    (D(3, 5), "CubXL first block"),
]
bands = [
    (D(12, 11), D(12, 18), "atomizer restart"),
    (D(1, 4), D(2, 9), "DAL Al runs"),
    (D(3, 14), D(3, 18), "TMS 2027"),
]

num = mdates.date2num
fig, ax = plt.subplots(figsize=(12.5, 5.6), dpi=160)
fig.patch.set_facecolor(SURFACE)
ax.set_facecolor(SURFACE)

x0, x1 = D(11, 28), D(4, 3)
n = len(projects)
for b0, b1, label in bands:
    ax.axvspan(num(b0), num(b1 + timedelta(days=1)), color=BAND, zorder=0, lw=0)
    ax.text(num(b0) + (num(b1) - num(b0)) / 2 + 0.5, -0.62, label, ha="center", va="bottom",
            fontsize=8, color=TEXT2, zorder=3)

bar_h = 0.42
for i, (name, segs) in enumerate(projects):
    y = n - 1 - i
    for s0, s1, kind in segs:
        w = num(s1 + timedelta(days=1)) - num(s0)
        patch = FancyBboxPatch((num(s0), y - bar_h / 2), w, bar_h,
                               boxstyle="round,pad=0,rounding_size=0.9",
                               mutation_aspect=0.06,
                               fc=PREP if kind == "p" else RUNS, ec=SURFACE, lw=2, zorder=2)
        ax.add_patch(patch)

for d, label in milestones:
    ax.axvline(num(d), color=TEXT2, lw=0.8, ls=(0, (1.5, 2.5)), zorder=1)
for k, (d, label) in enumerate(milestones):
    ax.text(num(d), n - 0.45 + (0.42 if k % 2 else 0.0), label, rotation=0, ha="center", va="bottom",
            fontsize=8, color=TEXT)

ax.set_ylim(-0.75, n + 0.55)
ax.set_xlim(num(x0), num(x1))
ax.set_yticks(range(n))
ax.set_yticklabels([p[0] for p in reversed(projects)], fontsize=9.5, color=TEXT)
ax.tick_params(axis="y", length=0)
ax.xaxis.set_major_locator(mdates.MonthLocator())
ax.xaxis.set_major_formatter(mdates.DateFormatter("%b %Y"))
ax.xaxis.set_minor_locator(mdates.WeekdayLocator(byweekday=mdates.MO))
ax.tick_params(axis="x", colors=TEXT2, labelsize=9)
ax.grid(axis="x", which="major", color=GRID, lw=1, zorder=0)
for side in ("top", "right", "left"):
    ax.spines[side].set_visible(False)
ax.spines["bottom"].set_color(GRID)

ax.legend(handles=[Patch(fc=PREP, ec=PREP, label="build and prepare"),
                   Patch(fc=RUNS, ec=RUNS, label="logged runs (counted trials, timed steps)")],
          loc="lower left", bbox_to_anchor=(0.0, -0.2), ncol=2, frameon=False, fontsize=9,
          labelcolor=TEXT, handlelength=1.4)
fig.suptitle("Ranked projects against the lab's deadlines, December 2026 – March 2027",
             x=0.012, ha="left", fontsize=12, color=TEXT, y=0.985)
fig.text(0.012, 0.925, "Projects 6–7 depend on the AI for Science award and on projects 2–4 producing failures to learn from.",
         ha="left", fontsize=8.5, color=TEXT2)
fig.tight_layout(rect=(0, 0.02, 1, 0.93))
out = sys.argv[1] if len(sys.argv) > 1 else "timeline.png"
fig.savefig(out, facecolor=SURFACE)
print("wrote", out)
