"""Fit the fixed camera to the arm from test 1 (writes camera_refit.json here).

    python fit_camera.py   # uses test1_trace.csv and test1_roll_detections.csv here

scripts/camera.json, which the 2026-10-16 runs used, is this fit at a 0.70 s offset (1.98 px);
the grid here picks 0.65 s (1.96 px), a camera within a few mm of it.

The green roll is a marker the arm carries: while it is held, its lowest point is 24.5 mm
under its centre, and its centre is 3.5 mm above the fingertips (forward kinematics, 150 mm
tool); on the shelf before the pick and on the table after the release it stands still at known
spots. Each video frame's detection (bbox bottom-centre, as piper_vision.py measures it live)
is paired with the trace row at the same time (the trace runs 0.7 s ahead of the video clock;
the offset is the one that fits best), and a pinhole camera with one radial distortion term,
plus a constant pixel offset for held frames (a finger hides part of the roll), is fitted by
robust least squares (scipy). camera_fit_lib.py has the pieces (build_b, fit3, ray_to_plane).
"""
import json
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, "..", "..", "..", "scripts"))
from camera_fit_lib import build_b, fit3, load_blobs_b, load_trace  # noqa: E402

t, ph, q, _ = load_trace(os.path.join(HERE, "test1_trace.csv"))
blobs = load_blobs_b(os.path.join(HERE, "test1_roll_detections.csv"), roi=(140, 850, 1520, 1296))
best = None
for off in np.arange(0.5, 0.95, 0.05):
    img, P3, kind = build_b(blobs, t, ph, q, off)
    x, r = fit3(img, P3, kind)
    print(f"time offset {off:.2f} s: median {np.median(r):.2f} px over {len(r)} frames")
    if best is None or np.median(r) < best[0]:
        best = (float(np.median(r)), float(off), x)
med, off, x = best
json.dump({"rvec": list(x[0:3]), "tvec": list(x[3:6]), "f": x[6], "k1": x[7], "cx": 1152.0,
           "cy": 648.0, "held_offset_px": list(x[8:10]), "time_offset_s": off,
           "median_resid_px": med,
           "feature": "bottom-centre of the green blob's bbox (piper_vision.py), i.e. the roll's lowest point",
           "size": [2304, 1296], "frame": "arm base frame, mm (piper_pick_tape.fk_all)",
           "fit": "2026-10-16 test 1 video (2304x1296 at 15 fps, detected at 1152x648) + 100 Hz trace"},
          open(os.path.join(HERE, "camera_refit.json"), "w"), indent=1)
print(f"camera_refit.json: time offset {off:.2f} s, median {med:.2f} px")
