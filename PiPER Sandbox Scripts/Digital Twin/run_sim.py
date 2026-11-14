#!/usr/bin/env python3
"""Run a Digital Twin scenario of the PiPER cell.

    pip install -r requirements.txt
    python run_sim.py                                  # clear the plate, headless, print a report
    python run_sim.py --viewer                         # watch it live (MuJoCo's 3D viewer)
    python run_sim.py --video output/clear_bed.mp4     # render mpzy's view to a video
    python run_sim.py --video out.mp4 --camera orbit   # a slowly orbiting view instead
    python run_sim.py --engine kinematic --video k.gif # no physics engine needed (numpy + matplotlib)
    python run_sim.py --scenario reach_map             # where on the plate the arm can pick
    python run_sim.py --scenario camera_check          # render mpzy's view, find the AprilTags
    python run_sim.py --scenario swap_augers           # swap the powder doser's auger (PR 200)
    python run_sim.py --prints action_figure,model_airplane
    python run_sim.py --config my_config_dir           # your own copy of config/

Scenarios live in scenarios/<name>.py and define run(sim, args). The report (every print's
result, when each bond broke and under what load, and any planned move that touched the cell)
is saved to output/<scenario>_report.json.

Headless Linux (CI, SSH): set MUJOCO_GL=egl (or osmesa) for --video.
"""
from __future__ import annotations

import argparse
import importlib
import json
import os
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

from digital_twin.config import load_config  # noqa: E402
from digital_twin.sim import make_sim  # noqa: E402


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--scenario", default="clear_bed", help="a module in scenarios/ (default clear_bed)")
    ap.add_argument("--engine", default=None, help="mujoco | kinematic (default: config/sim.yaml)")
    ap.add_argument("--config", default=None, help="folder with the five YAML files (default config/)")
    ap.add_argument("--viewer", action="store_true", help="open the interactive viewer")
    ap.add_argument("--speed", type=float, default=1.0, help="viewer playback speed (2 = twice real time)")
    ap.add_argument("--video", default=None, help="save a video (.mp4 or .gif)")
    ap.add_argument("--camera", default="mpzy", help="mpzy | wrist | orbit (video camera)")
    ap.add_argument("--size", default="960x540", help="video size WxH")
    ap.add_argument("--fps", type=int, default=30)
    ap.add_argument("--prints", default=None, help="comma-separated print names (default: all)")
    ap.add_argument("--no-collision-check", action="store_true", help="skip planning-time collision checks")
    args = ap.parse_args()

    if args.video and not args.viewer and sys.platform.startswith("linux") and not os.environ.get("DISPLAY"):
        os.environ.setdefault("MUJOCO_GL", "egl")
    cfg = load_config(args.config)
    scenario = importlib.import_module(f"scenarios.{args.scenario}")
    sim = make_sim(cfg, args.engine, cell_factory=getattr(scenario, "make_cell", None))
    sim.robot.collision_check = not args.no_collision_check
    rec = None
    if args.video:
        from digital_twin.viz.recorders import VideoRecorder
        w, h = (int(v) for v in args.size.lower().split("x"))
        rec = VideoRecorder(sim, args.video, camera=args.camera, width=w, height=h, fps=args.fps).attach()
    if args.viewer:
        from digital_twin.viz.recorders import LiveViewer
        LiveViewer(sim, speed=args.speed).attach()
    t0 = time.time()
    try:
        result = scenario.run(sim, args)
    except KeyboardInterrupt:
        print("stopped")
        result = {"stopped": True}
    print(f"wall time {time.time() - t0:.1f} s")
    if rec is not None and rec.frames:
        print("video:", rec.save())
    os.makedirs(cfg.path("output"), exist_ok=True)
    out = cfg.path(f"output/{args.scenario}_report.json")
    with open(out, "w") as fh:
        json.dump(result, fh, indent=1, default=lambda o: getattr(o, "tolist", lambda: str(o))())
    print("report:", out)
    sim.engine.close()


if __name__ == "__main__":
    main()
