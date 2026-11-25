#!/usr/bin/env python3
"""Check and draw the layout in settings.py, seen from above: the arm, J1's range, the keep-out
boxes, the holder (HOLDER_EXPECTED) and the box at each spot (SPOTS), with the gripper's path
for each. No arm, camera or Pi needed:

    python layout.py              # plans every spot, prints OK or why not, writes layout.png

Use it to choose where the holder and the three box spots go before putting them on the table.
Then auger_test.py finds where they really are with the tags.
"""
import math
import os
import sys

import kinematics as K
import settings as S
import vision as V
from auger_test import Plan, PlanError

HERE = os.path.dirname(os.path.abspath(__file__))


def rectangle(obj, length, width, dx=0.0):
    """Corners (closed) of a length x width rectangle centred dx along the object's x."""
    pts = [(dx - length / 2, -width / 2), (dx + length / 2, -width / 2),
           (dx + length / 2, width / 2), (dx - length / 2, width / 2), (dx - length / 2, -width / 2)]
    return [obj.to_arm((x, y, 0))[:2] for x, y in pts]


def plan_all(holder_z=60.0, box_z=3.0):
    """{spot: Plan or the reason there's none}, from the expected layout."""
    holder = V.Found(*S.HOLDER_EXPECTED[:2], holder_z, S.HOLDER_EXPECTED[2], [], 0.0)
    ready = K.UD.level([0.0, S.READY_LIFT_DEG, -S.READY_LIFT_DEG, S.J4_DEG, 24.0, S.PARK_J6_DEG])
    out = {}
    for spot, (x, y, yaw) in S.SPOTS.items():
        box = V.Found(x, y, box_z, yaw, [], 0.0)
        try:
            out[spot] = (Plan(holder, box, ready), box)
        except PlanError as e:
            out[spot] = (str(e), box)
    return holder, out


def draw(holder, plans, path):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    fig, ax = plt.subplots(figsize=(8.5, 8.5), dpi=130)
    # The arm: base, reach rings, J1's allowed range.
    for r in (200, 300, 400):
        t = [math.radians(a) for a in range(0, 361, 2)]
        ax.plot([r * math.cos(a) for a in t], [r * math.sin(a) for a in t], color="0.85",
                lw=0.8, ls="--", zorder=0)
        ax.text(r * math.cos(math.radians(-62)), r * math.sin(math.radians(-62)), f"{r} mm",
                color="0.6", fontsize=7)
    lo, hi = S.J1_RANGE_DEG
    wedge = [(0, 0)] + [(470 * math.cos(math.radians(a)), 470 * math.sin(math.radians(a)))
                        for a in range(int(lo), int(hi) + 1)] + [(0, 0)]
    ax.fill(*zip(*wedge), color="#2a9d8f", alpha=0.08, zorder=0)
    ax.plot(*zip(*wedge), color="#2a9d8f", lw=1, zorder=1)
    ax.text(480 * math.cos(math.radians(hi)), 480 * math.sin(math.radians(hi)),
            f"J1 {hi:g}°", color="#2a9d8f", fontsize=8)
    ax.text(480 * math.cos(math.radians(lo)), 480 * math.sin(math.radians(lo)) - 20,
            f"J1 {lo:g}°", color="#2a9d8f", fontsize=8)
    ax.add_patch(plt.Circle((0, 0), 55, color="0.25", zorder=3))
    ax.annotate("", (120, 0), (0, 0), arrowprops=dict(arrowstyle="->", color="white", lw=1.5),
                zorder=4)
    ax.text(0, -75, "PiPER\n(x forward)", ha="center", va="top", fontsize=8)
    # Keep-out boxes.
    for name, (x0, y0, _, x1, y1, _) in S.KEEP_OUT_BOXES.items():
        ax.add_patch(plt.Rectangle((x0, y0), x1 - x0, y1 - y0, color="#e63946", alpha=0.15))
        ax.text((x0 + x1) / 2, (y0 + y1) / 2, f"keep out:\n{name}", ha="center", va="center",
                color="#e63946", fontsize=9)
    # The holder: the auger (tube, and the gear at its outlet end) and its tags.
    ax.fill(*zip(*rectangle(holder, S.AUGER_LENGTH_MM, S.AUGER_TUBE_DIAMETER_MM)), color="0.2")
    ax.fill(*zip(*rectangle(holder, 10, S.AUGER_GEAR_DIAMETER_MM, S.AUGER_LENGTH_MM / 2 - 42)),
            color="0.2")
    for i, p in S.HOLDER_TAGS.items():
        tag(ax, holder, p, S.HOLDER_TAG_SIZE_MM, i)
    ax.text(*holder.to_arm((0, -60, 0))[:2], "holder", ha="center", fontsize=9)
    colours = ["#e76f51", "#457b9d", "#8338ec", "#2a9d8f"]
    for k, (spot, (plan, box)) in enumerate(plans.items()):
        c = colours[k % len(colours)]
        inside = rectangle(box, *S.BOX_INSIDE_MM)
        ax.plot(*zip(*inside), color=c, lw=1.5)
        for i, p in S.BOX_TAGS.items():
            tag(ax, box, p, S.BOX_TAG_SIZE_MM, i, c)
        ok = isinstance(plan, Plan)
        ax.text(*box.to_arm((0, 0, 0))[:2], f"spot {spot}" + ("" if ok else "\nNO PLAN"),
                ha="center", va="center", color=c, fontsize=9, weight="bold")
        if ok:
            moves = plan.down_slow + plan.pull + plan.lift + plan.swing + plan.lower_fast + \
                plan.lower_slow
            pts = [K.tcp(q) for q in moves]
            ax.plot([p[0] for p in pts], [p[1] for p in pts], color=c, lw=1, ls=":")
    ax.set_aspect("equal")
    ax.set_xlim(-250, 560)
    ax.set_ylim(-500, 500)
    ax.set_xlabel("x (mm, arm frame: in front of the arm)")
    ax.set_ylabel("y (mm, arm frame: to the arm's left)")
    ax.set_title("Powder-Doser Workflow 1: layout from settings.py (seen from above)", fontsize=10)
    ax.grid(alpha=0.2)
    fig.tight_layout()
    fig.savefig(path)
    plt.close(fig)


def tag(ax, obj, p, size, label, colour="black"):
    import matplotlib.pyplot as plt
    h = size * 10 / 16  # with its white border
    pts = [obj.to_arm((p[0] + x, p[1] + y, 0))[:2] for x, y in ((-h, -h), (h, -h), (h, h), (-h, h))]
    ax.add_patch(plt.Polygon(pts, closed=True, fill=False, edgecolor=colour, lw=1))
    ax.text(*obj.to_arm((p[0], p[1], 0))[:2], str(label), ha="center", va="center", fontsize=6,
            color=colour)


def main():
    holder, plans = plan_all()
    bad = 0
    for spot, (plan, box) in plans.items():
        if isinstance(plan, Plan):
            print(f"spot {spot}: OK\n{plan.summary()}")
        else:
            bad += 1
            print(f"spot {spot}: NO PLAN: {plan}")
    path = os.path.join(HERE, "layout.png")
    try:
        draw(holder, plans, path)
        print(f"drawn: {path}")
    except ImportError:
        print("(pip install matplotlib to draw layout.png)")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
