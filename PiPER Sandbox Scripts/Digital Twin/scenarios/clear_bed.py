"""Scenario: clear the A1 mini's build plate.

The PiPER unfolds, then for each print in config/prints.yaml grips it, breaks it free of the
plate, and drops it in the box or sets it on the black shelf (tasks/pick_place.py).

    python run_sim.py                              # this scenario, headless, prints a report
    python run_sim.py --viewer                     # watch it live in MuJoCo's viewer
    python run_sim.py --video output/clear_bed.mp4 # save a video from mpzy's camera
    python run_sim.py --prints action_figure,model_airplane
"""
from __future__ import annotations

import numpy as np

from digital_twin.sim import ready
from digital_twin.tasks.pick_place import PickPlace


def run(sim, args) -> dict:
    ready(sim)
    names = args.prints.split(",") if getattr(args, "prints", None) else None
    planner = PickPlace(sim.cell, sim.robot, sim.cfg)
    print(f"Clearing the plate ({sim.engine.name} engine):")
    report = planner.run(names)
    ok = sum(r["result"] == "done" for r in report)
    print(f"{ok}/{len(report)} prints delivered in {sim.engine.time:.1f} s of simulated time")
    for b in sim.engine.bond_log:
        f = np.asarray(b["force_n"])
        t = np.asarray(b["torque_nm"]) * 1000
        print(f"  bond broke: {b['print']:18s} t={b['time']:6.2f}s  pull {max(f[2], 0):.2f} N, shear "
              f"{np.hypot(f[0], f[1]):.2f} N, peel {np.hypot(t[0], t[1]):.1f} N*mm, twist {abs(t[2]):.1f} N*mm")
    if sim.robot.collisions:
        print(f"  {len(sim.robot.collisions)} planned moves touched the cell; see the report's 'collisions'")
    return {"prints": report, "bond_breaks": sim.engine.bond_log, "collisions": sim.robot.collisions,
            "sim_time_s": sim.engine.time}
