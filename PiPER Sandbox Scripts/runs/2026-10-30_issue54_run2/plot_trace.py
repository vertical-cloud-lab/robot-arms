import csv, sys
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
rows = list(csv.DictReader(open(sys.argv[1])))
t0 = float(rows[0]["t_unix"])
t = [float(r["t_unix"]) - t0 for r in rows]
f = lambda k: [float(r[k]) if r[k] != "" else float("nan") for r in rows]
SURF, INK, MUTED = "#fcfcfb", "#0b0b0b", "#6b6a64"
BLUE, ORANGE, AQUA, YELLOW = "#2a78d6", "#eb6834", "#1baf7a", "#eda100"
stop, off = 14.30, 16.87  # J3 over its current limit; motors disabled
plt.rcParams.update({"font.size": 10, "axes.edgecolor": MUTED, "axes.labelcolor": INK,
                     "xtick.color": MUTED, "ytick.color": MUTED, "text.color": INK})
fig, (a1, a2) = plt.subplots(2, 1, figsize=(9, 6.4), sharex=True,
                             gridspec_kw={"height_ratios": [2, 1.3]}, facecolor=SURF)
for ax in (a1, a2):
    ax.set_facecolor(SURF); ax.grid(True, color="#e6e5e0", lw=0.8); ax.set_axisbelow(True)
    for s in ("top", "right"): ax.spines[s].set_visible(False)
    for x in (stop, off): ax.axvline(x, color=MUTED, lw=1, ls=":")
a1.plot(t, f("j6"), color=BLUE, lw=2, label="J6")
a1.plot(t, f("j2"), color=AQUA, lw=2, label="J2")
a1.plot(t, f("j3"), color=YELLOW, lw=2, label="J3")
a1.plot(t, f("j5"), color=ORANGE, lw=2, label="J5")
a1.set_ylabel("measured joint angle (deg)")
a1.legend(loc="lower left", frameon=False, ncol=4)
for x, txt in ((3.3, "up 20°"), (7.6, "roll J6\nto −52°"), (11.6, "down"), (14.3, "up again:\nstopped"),
               (16.0, "land"), (19.3, "disabled")):
    a1.text(x, 30, txt, color=MUTED, ha="center", va="bottom", fontsize=9)
a1.set_ylim(-60, 42)
a2.plot(t, f("current_j3_a"), color=YELLOW, lw=2, label="J3")
a2.plot(t, f("current_j5_a"), color=ORANGE, lw=2, label="J5")
a2.plot(t, f("current_j6_a"), color=BLUE, lw=2, label="J6")
a2.axhline(-4, color=YELLOW, lw=1, ls="--")
a2.text(21.5, -3.85, "J3 limit (4 A)", color=MUTED, fontsize=9, va="bottom", ha="right")
a2.annotate("at home, J5's current\nflips sign", xy=(12.9, 0.5), xytext=(8.0, 1.4),
            arrowprops=dict(arrowstyle="-", color=MUTED, lw=1), color=INK, fontsize=9)
a2.set_ylim(-5, 2.6)
a2.set_ylabel("motor current (A)")
a2.set_xlabel("time since the trace started (s)")
a2.legend(loc="lower left", frameon=False, ncol=3)
a1.set_title("Up_and_Down.py on the PiPER, 2026-10-30 04:10 UTC: second run (#54)", loc="left",
             fontsize=11, color=INK)
fig.tight_layout()
fig.savefig(sys.argv[2], dpi=130, facecolor=SURF)
