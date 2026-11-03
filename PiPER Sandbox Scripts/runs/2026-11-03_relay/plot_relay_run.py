"""Plot run 3 of the relay test (2026-11-03): the arm's joints, and when the relay, the arm's
CAN feedback, the motors and Up_and_Down.py were on. Times are from mpzy's ~/arm_power.log
(to the second) and the 50 Hz trace Up_and_Down.py wrote.

    python plot_relay_run.py   # writes relay_run3.png next to this file
"""
import csv
import datetime as dt
import os

import matplotlib.pyplot as plt

HERE = os.path.dirname(os.path.abspath(__file__))
UTC = dt.timezone.utc
T0 = dt.datetime(2026, 11, 3, 1, 48, 24, tzinfo=UTC).timestamp()  # relay ON
RUN_START = dt.datetime(2026, 11, 3, 1, 48, 28, tzinfo=UTC).timestamp() - T0
RUN_END = dt.datetime(2026, 11, 3, 1, 48, 52, tzinfo=UTC).timestamp() - T0
RELAY_OFF = dt.datetime(2026, 11, 3, 1, 48, 56, tzinfo=UTC).timestamp() - T0
TALK_AFTER_ON, SILENT_AFTER_OFF = 2.1, 1.4  # from arm_power.py's own measurement

SURFACE, INK, INK2, MUTED, GRID = "#fcfcfb", "#0b0b0b", "#52514e", "#898781", "#e1e0d9"
SERIES = {"J2": "#2a78d6", "J3": "#eb6834", "J5": "#1baf7a"}  # validated, fixed order

with open(os.path.join(HERE, "run3_trace.csv")) as f:
    rows = list(csv.DictReader(f))
t = [float(r["t_unix"]) - T0 for r in rows]
enabled = [int(float(r["motors_enabled"])) > 0 for r in rows]
on_spans, start = [], None
for ti, e in zip(t, enabled):
    if e and start is None:
        start = ti
    if not e and start is not None:
        on_spans.append((start, ti))
        start = None
if start is not None:
    on_spans.append((start, t[-1]))

plt.rcParams.update({"font.size": 10, "axes.edgecolor": MUTED, "axes.labelcolor": INK2,
                     "xtick.color": MUTED, "ytick.color": MUTED, "text.color": INK})
fig, (ax, lanes) = plt.subplots(2, 1, figsize=(9, 5.6), sharex=True,
                                gridspec_kw={"height_ratios": [3, 1.35], "hspace": 0.12})
fig.patch.set_facecolor(SURFACE)
for a in (ax, lanes):
    a.set_facecolor(SURFACE)
    for s in ("top", "right"):
        a.spines[s].set_visible(False)

for name, color in SERIES.items():
    col = "j" + name[1]
    y = [float(r[col]) for r in rows]
    ax.plot(t, y, color=color, lw=2, label=f"{name} measured", solid_capstyle="round")
    ax.annotate(f"{name} {y[-1]:+.1f}°", (t[-1], y[-1]), xytext=(6, 0),
                textcoords="offset points", va="center", color=INK2, fontsize=9)
ax.axhline(0, color=GRID, lw=1, zorder=0)
ax.grid(axis="y", color=GRID, lw=0.8)
ax.set_ylabel("joint angle (deg)")
ax.legend(loc="lower left", frameon=False, ncol=1, fontsize=9)
ax.set_ylim(-24, 31)
ax.set_title("Relay test run 3: power on, up and down, park, power off only once parked",
             loc="left", fontsize=11, color=INK)
for x, label, dx, ha in ((0, "relay on", 4, "left"), (RELAY_OFF, "relay off", -4, "right")):
    ax.axvline(x, color=MUTED, lw=1, ls=(0, (3, 3)))
    ax.annotate(label, (x, 1.0), xycoords=("data", "axes fraction"), xytext=(dx, -12),
                textcoords="offset points", ha=ha, color=INK2, fontsize=9)

lane_rows = [
    ("relay (GPIO17)", [(0, RELAY_OFF)]),
    ("arm on CAN", [(TALK_AFTER_ON, RELAY_OFF + SILENT_AFTER_OFF)]),
    ("Up_and_Down.py", [(RUN_START, RUN_END)]),
    ("motors enabled", on_spans),
]
for i, (label, spans) in enumerate(lane_rows):
    y = len(lane_rows) - 1 - i
    for a, b in spans:
        lanes.barh(y, b - a, left=a, height=0.56, color=SERIES["J2"], edgecolor=SURFACE,
                   linewidth=2)
lanes.set_yticks(range(len(lane_rows)), [r[0] for r in reversed(lane_rows)], color=INK2)
lanes.tick_params(axis="y", length=0)
lanes.set_xlabel("seconds since the relay switched on (01:48:24 UTC)")
lanes.annotate(f"talking {TALK_AFTER_ON:g} s after on", (TALK_AFTER_ON, 2), xytext=(4, 9),
               textcoords="offset points", color=INK2, fontsize=8)
lanes.annotate(f"silent {SILENT_AFTER_OFF:g} s after off", (RELAY_OFF + SILENT_AFTER_OFF, 2),
               xytext=(-4, 9), textcoords="offset points", ha="right", color=INK2, fontsize=8)
lanes.set_xlim(-1, RELAY_OFF + 4)
lanes.grid(axis="x", color=GRID, lw=0.8)
lanes.set_axisbelow(True)

fig.savefig(os.path.join(HERE, "relay_run3.png"), dpi=150, bbox_inches="tight",
            facecolor=SURFACE)
print("wrote relay_run3.png")
