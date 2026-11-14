"""The cell builds, the prints sit where prints.yaml says without overlapping, and the bond
model gives the numbers it should."""
import numpy as np
import pytest

from digital_twin.config import load_config
from digital_twin.physics import adhesion
from digital_twin.world.cell import Cell
from digital_twin.world.print_library import build_print_geoms


def test_cell_builds():
    cell = Cell(load_config())
    names = {b.name for b, _ in cell.scene.root.walk()}
    for n in ("table", "printer", "plate", "shelf", "box", "piper_base", "link6", "finger1", "finger2"):
        assert n in names
    assert {p.name for p in cell.prints} >= {"action_figure", "model_airplane"}
    tag_names = {t.name for t in cell.scene.tags}
    assert tag_names >= {"A1", "A2", "A3", "P1", "P2", "B1", "B2", "B3", "B4", "G1", "G2",
                         "S1", "S2", "S3", "S4", "W1", "W2", "W3", "W4"}


def test_no_overlaps_at_start():
    pytest.importorskip("mujoco")
    from digital_twin.sim import make_sim
    sim = make_sim(quiet=True)
    assert sim.engine.start_report() == []
    assert sim.engine.arm_collisions(sim.engine.arm_q()) == []


def test_bond_capacity_of_a_cube():
    geoms = build_print_geoms("box", {"size": [20, 20, 20]})
    cap = adhesion.capacity(geoms, stick_kpa=4.0, shear_ratio=1.0)
    assert cap.area_m2 == pytest.approx(400e-6, rel=0.01)
    assert cap.pull_n == pytest.approx(1.6, rel=0.01)
    # A square's section modulus is a^3 / 6.
    assert cap.peel_x_nm == pytest.approx(4e3 * 0.02 ** 3 / 6, rel=0.03)
    assert adhesion.failure_index(cap, np.array([0, 0, 0.5 * cap.pull_n]), np.zeros(3)) == pytest.approx(0.25)
    assert adhesion.failure_index(cap, np.array([0, 0, -10.0]), np.zeros(3)) == 0.0  # pushing never breaks it
