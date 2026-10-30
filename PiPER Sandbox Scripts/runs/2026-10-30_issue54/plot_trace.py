import csv, sys
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
rows = list(csv.DictReader(open(sys.argv[1])))
t0 = float(rows[0]["t_unix"])
t = [float(r["t_unix"]) - t0 for r in rows]
f = lambda k: [float(r[k]) if r[k] != "" else float("nan") for r in rows]
SURF, INK, MUTED = "#fcfcfb", "#0b0b0b", "#6b6a64"
BLUE, ORANGE, AQUA, YELLOW = "#2a78d6", "#eb6834", "#1baf7a", "#eda100"
jam = 9.336
plt.rcParams.update({"font.size": 10, "axes.edgecolor": MUTED, "axes.labelcolor": INK,
                     "xtick.color": MUTED, "ytick.color": MUTED, "text.color": INK})
fig, (a1, a2) = plt.subplots(2, 1, figsize=(9, 6.2), sharex=True, gridspec_kw={"height_ratios": [2.2, 1]},
                             facecolor=SURF)
for ax in (a1, a2):
    ax.set_facecolor(SURF); ax.grid(True, color="#e6e5e0", lw=0.8); ax.set_axisbelow(True)
    for s in ("top", "right"): ax.spines[s].set_visible(False)
    ax.axvline(jam, color=MUTED, lw=1, ls=":")
a1.plot(t, f("cmd_j6"), color=ORANGE, lw=2, ls="--", label="J6 commanded")
a1.plot(t, f("j6"), color=BLUE, lw=2, label="J6 measured")
a1.plot(t, f("j2"), color=AQUA, lw=2, label="J2 measured")
a1.plot(t, f("j3"), color=YELLOW, lw=2, label="J3 measured")
a1.set_ylabel("joint angle (deg)")
a1.legend(loc="lower left", frameon=False, ncol=4)
a1.annotate("J6 jams at -55°\n(J5 at 10°)", xy=(jam, -55.0), xytext=(jam + 1.3, -75),
            arrowprops=dict(arrowstyle="-", color=MUTED, lw=1), color=INK)
for x, txt in ((1.6, "up 20°"), (6.8, "wrist roll\ntoward J6 = -90°"), (12.6, "roll back"), (15.6, "down"), (19.2, "disabled")):
    a1.text(x, 30, txt, color=MUTED, ha="center", va="bottom", fontsize=9)
a1.set_ylim(-95, 42)
a2.plot(t, f("current_j6_a"), color=BLUE, lw=2)
a2.set_ylabel("J6 current (A)")
a2.set_xlabel("time since the trace started (s)")
a2.text(jam + 1.9, -9, "0.1 A while moving freely, 16 A against the jam", color=INK, va="center", fontsize=9)
a1.set_title("Up_and_Down.py on the PiPER, 2026-10-30 03:29 UTC: first run (#54)", loc="left", fontsize=11, color=INK)
fig.tight_layout()
fig.savefig(sys.argv[2], dpi=130, facecolor=SURF)
