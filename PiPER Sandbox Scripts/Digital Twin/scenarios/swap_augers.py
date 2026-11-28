"""Scenario: swap the powder doser's auger (powder-doser PR 200).

The PiPER unfolds, pulls the installed auger out of the doser's two snap clips, parks it in the
rack, picks the auger named in config/powder_doser.yaml (`swap.swap_in`) out of the rack, and
snaps it into the doser with its gear on the drive pinion (tasks/auger_swap.py).

    python run_sim.py --scenario swap_augers                       # headless, prints a report
    python run_sim.py --scenario swap_augers --viewer              # watch it live
    python run_sim.py --scenario swap_augers --video output/swap_augers.mp4 --camera doser

What to edit: config/powder_doser.yaml (doser and rack placement, augers and their powders,
the swap's grasp point, squeeze and push force, the clips' material); the snap fit itself is
physics/snap_fit.py, the doser/auger/rack objects world/powder_doser.py.
"""
from __future__ import annotations

import numpy as np

from digital_twin.sim import ready
from digital_twin.tasks.auger_swap import AugerSwap
from digital_twin.world.doser_cell import DoserCell


def make_cell(cfg):
    return DoserCell(cfg)


def run(sim, args) -> dict:
    cell, e = sim.cell, sim.engine
    g = cell.clip_geom
    v, push, pull = __import__("digital_twin.physics.snap_fit", fromlist=["x"]).retention_curve(
        g, cell.geo["auger"]["tube_radius"])
    print(f"Doser clips: k = {g.stiffness():.2f} N/mm per arm; one clip takes {push.max():.1f} N to snap in "
          f"and {pull.max():.1f} N to pull out; arm root stress at full spread "
          f"{g.root_stress(cell.geo['auger']['tube_radius'] - g.lip_x):.0f} MPa (yield ~{g.yield_mpa:.0f})")
    for n, a in cell.augers.items():
        print(f"  {n:14s} {a.cfg['powder']:16s} {a.mass_kg * 1000:6.1f} g ({a.powder_g:.0f} g of powder), "
              f"starts in {a.cfg['start']}")
    ready(sim)
    task = AugerSwap(cell, sim.robot, sim.cfg)
    ok = task.run()
    print(f"Swap {'succeeded' if ok else 'FAILED'} in {e.time:.1f} s of simulated time")
    for r in task.report:
        extras = {k: v for k, v in r.items() if k not in ("t", "step", "ok")}
        print(f"  t={r['t']:6.2f}s {'ok ' if r.get('ok', True) else 'NO '} {r['step']:34s} {extras}")
    for ev in cell.snap.events:
        print(f"  snap: t={ev['t']:6.2f}s {ev['clip']:12s} {ev['auger']:14s} {ev['event']:11s} "
              f"peak {ev['peak_force_n']:.1f} N")
    if sim.robot.collisions:
        print(f"  {len(sim.robot.collisions)} planned moves touched the cell; see the report's 'collisions'")
    return {"ok": ok, "steps": task.report, "snap_events": cell.snap.events, "collisions": sim.robot.collisions,
            "augers": {n: {"mass_g": a.mass_kg * 1000, "powder": a.cfg["powder"], "powder_g": a.powder_g}
                       for n, a in cell.augers.items()},
            "clip": {"k_n_per_mm": g.stiffness(), "push_in_n": float(push.max()), "pull_out_n": float(pull.max())},
            "sim_time_s": e.time}
