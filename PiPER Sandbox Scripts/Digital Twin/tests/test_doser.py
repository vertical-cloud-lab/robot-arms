"""The powder doser and the auger swap (world/powder_doser.py, physics/snap_fit.py,
tasks/auger_swap.py). The full swap takes about a minute."""
import numpy as np
import pytest

from digital_twin.config import load_config
from digital_twin.physics.snap_fit import ClipGeometry, lip_forces, retention_curve
from digital_twin.sim import make_sim, ready
from digital_twin.world.doser_cell import DoserCell


def measured_clip(**kw):
    return ClipGeometry(seat_radius=12.74, wall=2.01, width=12.0, lip_x=8.75, lip_z=10.4, **kw)


def test_clip_snap_force_from_geometry():
    g = measured_clip()
    assert 4.0 < g.stiffness() < 5.0  # N/mm per arm, Castigliano on the measured arc
    v, push, pull = retention_curve(g, 12.5)
    assert 15 < push.max() < 21 and 15 < pull.max() < 21  # ~18 N per clip
    # Seated (centre on the seat): the lips don't touch the tube; above the lips they push it
    # out, just inside them they pull it in (the snap).
    assert lip_forces(g, 12.5, 0.0, 0.0)[1] == 0.0
    assert lip_forces(g, 12.5, 0.0, 14.0)[1] > 0 and lip_forces(g, 12.5, 0.0, 8.0)[1] < 0
    # A stiffer, PETG-like material scales the force with E.
    assert measured_clip(E_mpa=1500).stiffness() == pytest.approx(g.stiffness() / 2, rel=1e-6)


@pytest.fixture(scope="module")
def doser_sim():
    return make_sim(load_config(), "mujoco", quiet=True, cell_factory=DoserCell)


def test_augers_rest_seated(doser_sim):
    sim = doser_sim
    sim.robot.run(0.5)
    cell, e = sim.cell, sim.engine
    assert cell.snap.seated(e, "auger_xanthan", [c.name for c in cell.doser.clips])
    for k, name in ((1, "auger_salt"), (2, "auger_iron")):
        assert cell.snap.seated(e, name, [f"rack_s{k}_clip0", f"rack_s{k}_clip1"], tol_mm=1.0)
    assert not cell.snap.events  # nothing snapped by itself


@pytest.mark.slow
def test_full_swap():
    from digital_twin.tasks.auger_swap import AugerSwap
    sim = make_sim(load_config(), "mujoco", quiet=True, cell_factory=DoserCell)
    ready(sim)
    task = AugerSwap(sim.cell, sim.robot, sim.cfg)
    assert task.run(), task.report
    steps = {r["step"]: r for r in task.report}
    assert steps["gear check auger_salt"]["meshes"]
    outs = [ev for ev in sim.cell.snap.events if ev["event"] == "snapped out" and ev["auger"] == "auger_xanthan"]
    ins = [ev for ev in sim.cell.snap.events if ev["event"] == "snapped in" and ev["auger"] == "auger_salt"]
    assert {ev["clip"] for ev in outs} == {"doser_clip0", "doser_clip1"}
    assert {ev["clip"] for ev in ins} == {"doser_clip0", "doser_clip1"}
    assert all(12 < ev["peak_force_n"] < 25 for ev in ins)
