import csv, sys
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
rows = list(csv.DictReader(open(sys.argv[1])))
t0 = float(rows[0]["t_unix"])
t = [float(r["t_unix"]) - t0 for r in rows]
f = lambda k: [float(r[k]) if r[k] != "" else float("nan") for r in rows]
SURF, INK, MUTED = "#fcfcfb", "#0b0b0b", "#6b6a64"
BLUE, ORANGE, AQUA, YELLOW = "#2a78d6", "#eb6834", "#1baf7a", "#eda100"  # categorical slots 1-4
off = 38.05  # motors disabled
plt.rcParams.update({"font.size": 10, "axes.edgecolor": MUTED, "axes.labelcolor": INK,
                     "xtick.color": MUTED, "ytick.color": MUTED, "text.color": INK})
fig, (a1, a2) = plt.subplots(2, 1, figsize=(9, 6.6), sharex=True,
                             gridspec_kw={"height_ratios": [2, 1.3]}, facecolor=SURF)
for ax in (a1, a2):
    ax.set_facecolor(SURF); ax.grid(True, color="#e6e5e0", lw=0.8); ax.set_axisbelow(True)
    for s in ("top", "right"): ax.spines[s].set_visible(False)
    ax.axvline(off, color=MUTED, lw=1, ls=":")
series = (("j6", "J6", BLUE), ("j5", "J5", ORANGE), ("j2", "J2", AQUA), ("j3", "J3", YELLOW))
for k, name, c in series:
    a1.plot(t, f(k), color=c, lw=2, label=name)
    a1.text(t[-1] + 0.4, f(k)[-1], name, color=INK, va="center", fontsize=9)  # direct label
a1.set_ylabel("measured joint angle (deg)")
a1.legend(loc="lower left", frameon=False, ncol=4)
for x, txt in ((3.4, "level\nJ5"), (7.5, "up 20°"), (11.8, "roll J6\nto −52°"), (23.2, "3 down/up cycles,\nJ5–J6 link level"),
               (33.0, "land"), (36.0, "lower\ngripper"), (40.6, "motors\noff")):
    a1.text(x, 31, txt, color=MUTED, ha="center", va="bottom", fontsize=9)
a1.set_ylim(-60, 42)
a1.set_xlim(0, 44.5)
a2.plot(t, f("current_j3_a"), color=YELLOW, lw=2, label="J3")
a2.plot(t, f("current_j5_a"), color=ORANGE, lw=2, label="J5")
a2.plot(t, f("current_j6_a"), color=BLUE, lw=2, label="J6")
a2.axhline(-0.7, color=ORANGE, lw=1, ls="--")
a2.text(15.5, -0.62, "J5 at −0.7 A: something under the gripper (contact stop)", color=MUTED, fontsize=9,
        va="bottom")
a2.annotate("gripper rests:\nJ5 eases off", xy=(37.8, -0.6), xytext=(29.6, 0.55),
            arrowprops=dict(arrowstyle="-", color=MUTED, lw=1), color=INK, fontsize=9)
a2.set_ylim(-2.6, 1.3)
a2.set_ylabel("motor current (A)")
a2.set_xlabel("time since the trace started (s)")
a2.legend(loc="lower left", frameon=False, ncol=3)
a2.text(43.9, -2.5, "readings after motors off are stale", color=MUTED, fontsize=8, ha="right")
a1.set_title("Up_and_Down.py on the PiPER, 2026-10-30 04:54 UTC: third run (#54)", loc="left",
             fontsize=11, color=INK)
fig.tight_layout()
fig.savefig(sys.argv[2], dpi=130, facecolor=SURF)
