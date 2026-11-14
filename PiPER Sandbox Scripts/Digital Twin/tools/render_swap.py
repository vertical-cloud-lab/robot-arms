#!/usr/bin/env python3
"""Run the auger swap (scenarios/swap_augers.py) and save what it looked like:

    output/swap_augers.mp4            the whole run from the "swap" view (MP4, not committed)
    docs/swap_augers_frames.jpg       eight moments of it on one sheet (committed)

    MUJOCO_GL=egl python tools/render_swap.py      # headless Linux; drop MUJOCO_GL elsewhere
"""
from __future__ import annotations

import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)

import numpy as np  # noqa: E402

from digital_twin.config import load_config  # noqa: E402
from digital_twin.sim import make_sim, ready  # noqa: E402
from digital_twin.tasks.auger_swap import AugerSwap  # noqa: E402
from digital_twin.viz.recorders import VideoRecorder  # noqa: E402
from digital_twin.world.doser_cell import DoserCell  # noqa: E402

# (label, step in the task report it follows, seconds after that step's start or end)
MOMENTS = ["grasp auger_xanthan", "peel", "peel2", "place auger_xanthan", "grasp auger_salt",
           "roll", "roll2", "done"]


def main():
    cfg = load_config()
    sim = make_sim(cfg, "mujoco", quiet=True, cell_factory=DoserCell)
    rec = VideoRecorder(sim, os.path.join(ROOT, "output", "swap_augers.mp4"), camera="swap", width=960,
                        height=600, fps=15).attach()
    times = []
    sim.robot.on_frame.append(lambda r: times.append((r.engine.time, r.log[-1]["move"] if r.log else "")))
    ready(sim)
    task = AugerSwap(sim.cell, sim.robot, cfg)
    ok = task.run()
    print("swap ok:", ok, "frames:", len(rec.frames))
    rec.save()
    # Pick eight moments by the move that was running.
    def first(pred, after=0.0):
        for i, (t, mv) in enumerate(times):
            if t >= after and pred(mv):
                return i
        return len(times) - 1
    picks = []
    i = first(lambda m: m.startswith("down to auger_xanthan")); picks.append((i + 10, "1. grip the installed auger"))
    i = first(lambda m: m.startswith("peel")); j = first(lambda m: m == "lift out")
    picks.append(((i + j) // 2, "2. peel: back clip lets go")); picks.append((j, "3. levered out of the outlet clip"))
    i = first(lambda m: m.startswith("set down in rack")); picks.append((i + 5, "4. park it in the rack"))
    i = first(lambda m: m.startswith("down to auger_salt")); picks.append((i + 10, "5. grip the salt auger"))
    i = first(lambda m: m == "set the outlet end on its clip"); picks.append((i + 3, "6. tipped, outlet end on its clip"))
    j = first(lambda m: m.startswith("press into") or m == "relax"); picks.append((j, "7. rolled in: both clips snapped"))
    picks.append((len(rec.frames) - 1, "8. done: seated, gear on the pinion"))
    import cv2
    tiles = []
    for idx, label in picks:
        img = np.ascontiguousarray(rec.frames[min(idx, len(rec.frames) - 1)][36:])  # drop the time stamp bar
        cv2.rectangle(img, (0, 0), (img.shape[1], 34), (0, 0, 0), -1)
        cv2.putText(img, label, (10, 24), cv2.FONT_HERSHEY_SIMPLEX, 0.75, (255, 255, 255), 2, cv2.LINE_AA)
        tiles.append(cv2.resize(img, (img.shape[1] // 2, img.shape[0] // 2), interpolation=cv2.INTER_AREA))
    rows = [np.hstack(tiles[k:k + 4]) for k in (0, 4)]
    sheet = np.vstack(rows)
    out = os.path.join(ROOT, "docs", "swap_augers_frames.jpg")
    cv2.imwrite(out, cv2.cvtColor(sheet, cv2.COLOR_RGB2BGR), [cv2.IMWRITE_JPEG_QUALITY, 88])
    print("wrote", out)


if __name__ == "__main__":
    main()
