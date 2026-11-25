#!/usr/bin/env python3
"""Summarise results/results.csv for each box spot: how many runs got each grade, the success
rates with 95% confidence intervals, the time per run, and how repeatable the measurements were.

    python report.py                         # results/report.md and results/grades.png
    python report.py --results path/to/results

Runs anywhere (copy results/ off the Pi first). The chart needs matplotlib.

Repeatability and accuracy, from the logged numbers:
- where the camera found the holder and the box, run to run (they don't move during a spot's
  30 runs, so their spread is the vision's repeatability);
- the gripper's reading when it closed on the tube (how consistently it grips);
- with settings.AUGER_TAG, where the auger landed in the box: the mean offset from the box's
  middle is the placement accuracy, the spread its repeatability.
"""
import argparse
import csv
import math
import os
import statistics as st
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
GRADES = "ABCDF"
MEANING = {"A": "picked up and placed in the box", "B": "picked up, not placed",
           "C": "found, not picked up", "D": "not found", "F": "failed completely"}


def wilson(k, n, z=1.96):
    """95% confidence interval for a success rate of k out of n (Wilson score)."""
    if n == 0:
        return 0.0, 0.0
    p = k / n
    centre = (p + z * z / (2 * n)) / (1 + z * z / n)
    half = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / (1 + z * z / n)
    return max(0.0, centre - half), min(1.0, centre + half)


def numbers(rows, key):
    out = []
    for r in rows:
        try:
            out.append(float(r[key]))
        except (KeyError, ValueError):
            pass
    return out


def spread(rows, key):
    v = numbers(rows, key)
    return f"{st.mean(v):.1f} ± {st.stdev(v):.2f}" if len(v) > 1 else (f"{v[0]:.1f}" if v else "–")


def rate(k, n):
    lo, hi = wilson(k, n)
    return f"{k}/{n} = {100 * k / n:.0f}% ({100 * lo:.0f}–{100 * hi:.0f}%)" if n else "–"


def report(rows):
    spots = sorted({r["spot"] for r in rows}, key=lambda s: (len(s), s))
    lines = ["# Powder-Doser Workflow 1: results", "",
             f"{len(rows)} runs at {len(spots)} spot(s). Grades: "
             + "; ".join(f"**{g}** {MEANING[g]}" for g in GRADES) + ".", "",
             "| Spot | Runs | " + " | ".join(GRADES) + " | Placed (A), 95% CI | Picked up (A+B) "
             "| Found (A+B+C) | Seconds per run |",
             "|---|---|" + "---|" * len(GRADES) + "---|---|---|---|"]
    for spot in spots + ["all"]:
        rs = rows if spot == "all" else [r for r in rows if r["spot"] == spot]
        n = len(rs)
        count = {g: sum(r["grade"] == g for r in rs) for g in GRADES}
        secs = numbers(rs, "seconds")
        lines.append(f"| {spot} | {n} | " + " | ".join(str(count[g]) for g in GRADES)
                     + f" | {rate(count['A'], n)} | {rate(count['A'] + count['B'], n)} | "
                     + f"{rate(count['A'] + count['B'] + count['C'], n)} | "
                     + (f"{st.median(secs):.0f}" if secs else "–") + " |")
    lines += ["", "## Repeatability (mean ± standard deviation over the runs)", "",
              "| Spot | Holder x, y (mm) | Holder yaw (deg) | Box x, y (mm) | Box yaw (deg) "
              "| Grip on the tube (mm) |", "|---|---|---|---|---|---|"]
    for spot in spots:
        rs = [r for r in rows if r["spot"] == spot]
        lines.append(f"| {spot} | {spread(rs, 'holder_x')}, {spread(rs, 'holder_y')} | "
                     f"{spread(rs, 'holder_yaw')} | {spread(rs, 'box_x')}, {spread(rs, 'box_y')} | "
                     f"{spread(rs, 'box_yaw')} | {spread(rs, 'grip_closed_mm')} |")
    if any(r.get("auger_in_box_x") for r in rows):
        lines += ["", "## Placement (from the auger's tag, box frame: x along the box)", "",
                  "| Spot | Runs measured | x offset (mm) | y offset (mm) | Turn (deg) | "
                  "Furthest from the middle (mm) |", "|---|---|---|---|---|---|"]
        for spot in spots:
            rs = [r for r in rows if r["spot"] == spot and r.get("auger_in_box_x")]
            far = [math.hypot(float(r["auger_in_box_x"]), float(r["auger_in_box_y"])) for r in rs]
            lines.append(f"| {spot} | {len(rs)} | {spread(rs, 'auger_in_box_x')} | "
                         f"{spread(rs, 'auger_in_box_y')} | {spread(rs, 'auger_in_box_yaw')} | "
                         + (f"{max(far):.1f}" if far else "–") + " |")
    notes = [r for r in rows if r["grade"] != "A"]
    if notes:
        lines += ["", "## Runs that weren't A", ""]
        lines += [f"- spot {r['spot']} run {r['run']}: **{r['grade']}** {r['why']}"
                  + (f" (note: {r['note']})" if r.get("note") else "") for r in notes]
    return "\n".join(lines) + "\n", spots


def chart(rows, spots, path):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    colours = {"A": "#2a9d8f", "B": "#e9c46a", "C": "#f4a261", "D": "#e76f51", "F": "#6d597a"}
    fig, ax = plt.subplots(figsize=(6.5, 3.8), dpi=130)
    bottom = [0] * len(spots)
    for g in GRADES:
        counts = [sum(r["grade"] == g for r in rows if r["spot"] == s) for s in spots]
        ax.bar([f"spot {s}" for s in spots], counts, bottom=bottom, color=colours[g],
               label=f"{g}: {MEANING[g]}")
        bottom = [b + c for b, c in zip(bottom, counts)]
    ax.set_ylabel("runs")
    ax.set_title("Auger pick-and-place: grade of every run")
    ax.legend(fontsize=7, loc="upper left", bbox_to_anchor=(1.0, 1.0), frameon=False)
    fig.tight_layout()
    fig.savefig(path)
    plt.close(fig)


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--results", default=os.path.join(HERE, "results"))
    args = ap.parse_args()
    path = os.path.join(args.results, "results.csv")
    if not os.path.exists(path):
        raise SystemExit(f"no {path} yet: run auger_test.py first")
    with open(path, newline="") as f:
        rows = list(csv.DictReader(f))
    text, spots = report(rows)
    with open(os.path.join(args.results, "report.md"), "w") as f:
        f.write(text)
    print(text)
    try:
        chart(rows, spots, os.path.join(args.results, "grades.png"))
        print(f"chart: {os.path.join(args.results, 'grades.png')}")
    except ImportError:
        print("(pip install matplotlib for the chart)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
