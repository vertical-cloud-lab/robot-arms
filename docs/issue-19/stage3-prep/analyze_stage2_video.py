#!/usr/bin/env python3
"""Measure the stage-2 descent stutter and the park drop for issue #19 (run from the repo root).

    pip install opencv-python-headless numpy matplotlib
    python docs/issue-19/stage3-prep/analyze_stage2_video.py

1. Tracks the gripper through the stage-2 descent (template from frame 180, sub-pixel
   matching), scales pixels to mm with the known 75 mm descent, and writes
   stage2_gripper_track.csv. Static patches (the base, the right wall) move < 0.3 px over the
   same frames, so the camera is still and the back-steps are the arm's.
2. Plots that next to the planned streamed descent, and the wrist height through the drop at
   disable from the 100 Hz trace of the up/down run (updown_trace_2026-10-09.csv), via FK.
3. Draws the upper arm and forearm on six frames of the move out to the hover, from joint
   centres read off the frames by eye, showing the forearm keep its angle until J3 arrives.
"""
import csv
import math
import os
import sys

import cv2
import matplotlib
import numpy as np

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
sys.path.insert(0, os.path.join(ROOT, "scripts"))
import piper_pick_tape as P  # noqa: E402

SURF, INK, INK2, GRID = "#fcfcfb", "#0b0b0b", "#52514e", "#e4e3df"
BLUE, ORANGE = "#2a78d6", "#eb6834"

cap = cv2.VideoCapture(os.path.join(HERE, "..", "stage2", "stage2_descend.mp4"))
frames = []
while True:
    ok, f = cap.read()
    if not ok:
        break
    frames.append(f)
gray = [cv2.cvtColor(f, cv2.COLOR_BGR2GRAY).astype(np.float32) for f in frames]


def sub(a, b, c):
    d = a - 2 * b + c
    return 0.0 if d == 0 else 0.5 * (a - c) / d


# 1. gripper track, frames 176-201 (later the roll occludes the fingers and the match degrades)
T = gray[180][520:700, 1050:1200]
track = []
for i in range(176, 202):
    R = cv2.matchTemplate(gray[i][300:864, 850:1350], T, cv2.TM_CCOEFF_NORMED)
    _, score, _, (x, y) = cv2.minMaxLoc(R)
    track.append((i, 850 + x + sub(R[y, x - 1], R[y, x], R[y, x + 1]),
                  300 + y + sub(R[y - 1, x], R[y, x], R[y + 1, x]), score))
track = np.array(track)
y_top = track[track[:, 0] <= 181, 2].mean()
y_bot = 602.6  # mean over frames 206-215, the arm holding at the bottom
mm_per_px = 75.0 / (y_bot - y_top)
t_meas = (track[:, 0] - 181) / 20.0
h_meas = 109 - (track[:, 2] - y_top) * mm_per_px
with open(os.path.join(HERE, "stage2_gripper_track.csv"), "w") as f:
    f.write("frame,t_s,x_px,y_px,score,height_mm\n")
    for (i, x, y, s), t, h in zip(track, t_meas, h_meas):
        f.write(f"{int(i)},{t:.2f},{x:.1f},{y:.1f},{s:.3f},{h:.1f}\n")
print("back-steps (mm):", [round(float(d), 1) for d in np.diff(h_meas) if d > 0.5])

# 2. plots
Tp = 3.8
t_plan = np.linspace(0, Tp, 200)
h_plan = 109 - 75 * np.array([P.min_jerk(t / Tp) for t in t_plan])
t_plan, h_plan = np.r_[-0.25, t_plan, 4.5], np.r_[109, h_plan, 34]
rows = list(csv.DictReader(open(os.path.join(HERE, "updown_trace_2026-10-09.csv"))))
t = np.array([float(r["t_unix"]) for r in rows])
q = np.array([[float(r[f"j{i}"]) for i in range(1, 7)] for r in rows])
i_drop = max(i for i in range(len(rows)) if q[i, 1] > -0.05)  # last sample still at J2 = 0
win = list(range(i_drop - 15, i_drop + 30))
zw = np.array([P.pos(P.fk_all(q[i])[4])[2] for i in win])
zw -= np.median(zw[-10:])
t_drop = (t[win] - t[i_drop]) * 1000

plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 11, "axes.edgecolor": INK2,
                     "axes.labelcolor": INK2, "xtick.color": INK2, "ytick.color": INK2})
fig, (a, b) = plt.subplots(1, 2, figsize=(12.5, 4.6), dpi=130,
                           gridspec_kw={"width_ratios": [1.35, 1]})
fig.patch.set_facecolor(SURF)
for ax in (a, b):
    ax.set_facecolor(SURF)
    ax.grid(True, color=GRID, linewidth=0.8)
    ax.set_axisbelow(True)
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
a.plot(t_plan, h_plan, color=ORANGE, linewidth=2, label="new: streamed at 100 Hz (planned)")
a.plot(t_meas, h_meas, color=BLUE, linewidth=2, marker="o", markersize=4.5, markeredgecolor=SURF,
       markeredgewidth=1, label="stage 2: 15 MOVE J steps (from the video)")
k = int(np.argmax(np.diff(h_meas) > 2)) + 1
a.annotate("springs back ~4 mm\nat every waypoint", xy=(t_meas[k], h_meas[k]), xytext=(1.25, 95),
           color=INK2, fontsize=10, arrowprops=dict(arrowstyle="-", color=INK2, linewidth=0.8))
a.text(0.08, 55, "stage 2", color=INK, fontsize=10)
a.text(2.85, 57, "new", color=INK, fontsize=10)
a.set(xlim=(-0.25, 4.5), ylim=(25, 118), xlabel="time after leaving the hover (s)",
      ylabel="gripper height above the table (mm)")
a.set_title("Descent: 15 stop-starts in 1 s, vs one smooth 3.8 s line", color=INK, fontsize=12,
            loc="left")
a.legend(frameon=False, loc="upper right", fontsize=9.5, labelcolor=INK)
b.plot(t_drop, zw, color=BLUE, linewidth=2, marker="o", markersize=4.5, markeredgecolor=SURF,
       markeredgewidth=1)
b.axvline(0, color=INK2, linewidth=0.8, linestyle=(0, (3, 3)))
b.text(9, 8.6, "motors off", color=INK2, fontsize=10)
b.set(xlim=(t_drop[0], t_drop[-1]), xlabel="time from motors off (ms)",
      ylabel="wrist height above where it lands (mm)")
b.set_title("Drop at park: ~10 mm in ~50 ms", color=INK, fontsize=12, loc="left")
fig.tight_layout()
fig.savefig(os.path.join(HERE, "stutter_and_drop.png"), facecolor=SURF)

# 3. upper arm (J2 axis to elbow) and forearm (elbow to J5) on the move out to the hover
J2 = (785, 700)
pts = {66: ((440, 675), (750, 620)), 90: ((465, 585), (770, 530)), 108: ((515, 505), (815, 450)),
       126: ((575, 445), (875, 385)), 144: ((655, 395), (965, 380)), 162: ((740, 370), (1050, 435))}
tiles = []
for i, (e, w) in pts.items():
    im = frames[i].copy()
    cv2.line(im, J2, e, (214, 120, 42), 3)
    cv2.line(im, e, w, (52, 104, 235), 3)
    for p in (J2, e, w):
        cv2.circle(im, p, 6, (255, 255, 255), -1)
    ua = math.degrees(math.atan2(J2[1] - e[1], e[0] - J2[0]))
    fa = math.degrees(math.atan2(e[1] - w[1], w[0] - e[0]))
    crop = im[300:780, 330:1130]
    cv2.rectangle(crop, (0, 0), (800, 62), (251, 252, 252), -1)
    cv2.putText(crop, f"t = {(i - 66) / 20:.1f} s", (10, 26), cv2.FONT_HERSHEY_SIMPLEX, 0.75,
                (11, 11, 11), 2)
    cv2.putText(crop, f"upper arm {ua:5.1f} deg   forearm {fa:5.1f} deg", (10, 54),
                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (78, 81, 82), 2)
    tiles.append(cv2.resize(crop, (560, 336)))
    print(f"t = {(i - 66) / 20:.1f} s: upper arm {ua:.1f} deg, forearm {fa:.1f} deg")
cv2.imwrite(os.path.join(HERE, "movej_unsynchronized.jpg"),
            np.vstack([np.hstack(tiles[:3]), np.hstack(tiles[3:])]), [cv2.IMWRITE_JPEG_QUALITY, 85])
