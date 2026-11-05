#!/usr/bin/env python3
"""Summarize and plot pi_thermal_sample.py runs from the table Pis.

    python scripts/pi_thermal_plot.py DIR      # reads DIR/<pi>.json, writes DIR/summary.json and DIR/pi_thermals.png

Left: each Pi's SoC temperature, once a second, against the Pi 5 fan steps and
the firmware's throttle limits. Right: the CPU each Pi spent in the window,
split into face blurring (device.py), streaming (rpicam-vid capture plus ffmpeg
encoding and sending) and everything else, out of its 4 cores.
"""

import json
import statistics as st
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

ORDER = ["eufi", "mpzy", "76zj"]
ROLE = {"eufi": "back cam", "mpzy": "front cam", "76zj": "gripper cams"}
PI_COLOR = {"eufi": "#2a78d6", "mpzy": "#eb6834", "76zj": "#1baf7a"}  # categorical slots 1-3
BLUR, STREAM, OTHER = "#6250d6", "#52514e", "#c3c2b7"
SURFACE, INK, INK2, GRID = "#fcfcfb", "#0b0b0b", "#52514e", "#e4e3df"
# Pi 5 Active Cooler steps (kernel trip points, 5 C hysteresis) and firmware limits.
FAN_STEPS = [(50, "fan 30%"), (60, "fan 50%"), (67.5, "fan 70%"), (75, "fan 100%")]
SOFT, HARD = 80, 85


def summarize(d):
    s = d["samples"]
    soc = [x["soc_c"] for x in s if x.get("soc_c") is not None]
    procs = d["stream_procs"]

    def cores(prefix, key="cores"):
        return sum(p.get(key) or 0 for p in procs if p["role"].startswith(prefix))

    blur, enc, cap = cores("face blur"), cores("encode"), cores("capture")
    busy = d["cpu_busy_cores"]
    fps = [r[2] for r in d["fps_log"] if r[2] is not None]
    units = d["units"]
    return {
        "from_utc": s[0]["utc"], "to_utc": s[-1]["utc"],
        "soc_c": {"min": min(soc), "mean": round(st.mean(soc), 1), "max": max(soc)},
        "pmic_c_mean": round(st.mean(x["pmic_c"] for x in s if x.get("pmic_c")), 1),
        "arm_mhz": [round(min(x["arm_mhz"] for x in s)), round(max(x["arm_mhz"] for x in s))],
        "throttled": sorted({x["throttled"] for x in s}),
        "fan_rpm": [min(x["rpm"] for x in s), round(st.mean(x["rpm"] for x in s)), max(x["rpm"] for x in s)],
        "fan_pwm_pct": sorted({round(100 * x["pwm"] / 255) for x in s}),
        "uptime_h": d["static"]["uptime_h"], "boot_utc": d["static"]["boot_utc"],
        "cpus": d["static"]["cpus"],
        "cores": {"face_blur": round(blur, 2), "encode_send": round(enc, 2),
                  "capture": round(cap, 3), "other": round(busy - blur - enc - cap, 2),
                  "busy": round(busy, 2)},
        "streams_avg_cores_since_start": {u: v.get("avg_cores_since_start") for u, v in units.items()},
        "streams_hours_active": {u: v.get("hours_active") for u, v in units.items()},
        "fps_log": {"lines": len(fps), "min": min(fps, default=None), "max": max(fps, default=None),
                    "first_utc": d["fps_log"][0][0] if fps else None,
                    "last_utc": d["fps_log"][-1][0] if fps else None},
        "kernel_alerts": d["kernel_alerts"]["count"],
    }


def plot(data, summary, out):
    pis = [p for p in ORDER if p in data]
    plt.rcParams.update({"font.size": 10, "axes.edgecolor": GRID, "axes.labelcolor": INK2,
                         "xtick.color": INK2, "ytick.color": INK2, "text.color": INK})
    fig, (a, b) = plt.subplots(1, 2, figsize=(11.5, 4.6), dpi=150,
                               gridspec_kw={"width_ratios": [1.15, 1]}, facecolor=SURFACE)
    for ax in (a, b):
        ax.set_facecolor(SURFACE)
        for side in ("top", "right"):
            ax.spines[side].set_visible(False)

    # Left: temperature against the fan steps and throttle limits.
    lo, hi = 45, 88
    bands = [(lo, 50, "fan off")] + [
        (t, (FAN_STEPS + [(SOFT, None)])[i + 1][0], lbl) for i, (t, lbl) in enumerate(FAN_STEPS)]
    for i, (y0, y1, lbl) in enumerate(bands):
        a.axhspan(y0, y1, color="#f0efec" if i % 2 else SURFACE, lw=0, zorder=0)
        a.text(30.6, (y0 + y1) / 2, lbl, va="center", ha="left", fontsize=8, color=INK2)
    a.axhspan(SOFT, HARD, color="#fde7dc", lw=0, zorder=0)
    a.axhspan(HARD, hi, color="#f9cfcf", lw=0, zorder=0)
    a.text(30.6, (SOFT + HARD) / 2, "Arm cores\nthrottled", va="center", fontsize=8, color=INK2)
    a.text(30.6, (HARD + hi) / 2, "Arm + GPU\nthrottled", va="center", fontsize=8, color=INK2)
    for p in pis:
        s = data[p]["samples"]
        t = [x["t"] for x in s]
        y = [x["soc_c"] for x in s]
        a.plot(t, y, color=PI_COLOR[p], lw=2, solid_capstyle="round", zorder=3,
               label=f"{p} ({ROLE[p]}): {summary[p]['soc_c']['min']:.1f}–{summary[p]['soc_c']['max']:.1f} °C")
    a.set_xlim(0, 30)
    a.set_ylim(lo, hi)
    a.set_xlabel("seconds into the window")
    a.set_ylabel("SoC temperature (°C)")
    first = min(summary[p]["from_utc"] for p in pis)[11:19]
    a.set_title(f"SoC temperature, once a second, from {first} UTC", loc="left", fontsize=11)
    a.grid(axis="y", color=GRID, lw=0.6)
    a.set_axisbelow(True)
    a.legend(loc="center left", bbox_to_anchor=(0.01, 0.5), frameon=True, facecolor=SURFACE,
             edgecolor=GRID, fontsize=9)

    # Right: where each Pi's CPU went in the same window.
    ys = list(range(len(pis)))[::-1]
    for y, p in zip(ys, pis):
        c = summary[p]["cores"]
        ncpu = summary[p]["cpus"]
        stream = c["encode_send"] + c["capture"]
        x = 0
        for w, col, lbl in ((c["face_blur"], BLUR, "face blurring"), (stream, STREAM, "streaming"),
                            (max(c["other"], 0), OTHER, "everything else")):
            b.barh(y, w, left=x, height=0.5, color=col, edgecolor=SURFACE, lw=2,
                   label=lbl if y == ys[0] else None)
            x += w
        b.barh(y, ncpu, height=0.5, fill=False, edgecolor=GRID, lw=1, zorder=0)
        b.text(c["face_blur"] / 2, y, f"{c['face_blur']:.2f}", ha="center", va="center",
               color="white", fontsize=9, fontweight="bold")
        b.text(x + 0.06, y, f"streaming {stream:.2f}", ha="left", va="center", color=INK, fontsize=9)
    b.set_yticks(ys, [f"{p}\n{ROLE[p]}" for p in pis])
    b.set_xlim(0, 4)
    b.set_xlabel("CPU cores in use (the Pi has 4)")
    b.set_title("Where the CPU went in the same 30 s", loc="left", fontsize=11)
    b.grid(axis="x", color=GRID, lw=0.6)
    b.set_axisbelow(True)
    b.legend(loc="upper center", bbox_to_anchor=(0.5, -0.2), ncol=3, frameon=False, fontsize=9)
    fig.tight_layout()
    fig.savefig(out, facecolor=SURFACE)


def main():
    d = Path(sys.argv[1])
    data = {p: json.loads((d / f"{p}.json").read_text()) for p in ORDER if (d / f"{p}.json").exists()}
    summary = {p: summarize(v) for p, v in data.items()}
    (d / "summary.json").write_text(json.dumps(summary, indent=1) + "\n")
    plot(data, summary, d / "pi_thermals.png")
    print(json.dumps(summary, indent=1))


if __name__ == "__main__":
    main()
