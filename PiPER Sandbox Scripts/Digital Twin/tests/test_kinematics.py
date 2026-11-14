"""The twin's kinematics are the arm's: DH FK equals the lab's Up_and_Down.fk (piper_sdk's table),
IK inverts FK, and the physics engine's TCP sits exactly where the DH chain puts it."""
import importlib.util
import os

import numpy as np
import pytest

from digital_twin.config import load_config
from digital_twin.kinematics.piper import PiperKinematics

HERE = os.path.dirname(os.path.abspath(__file__))
UP_AND_DOWN = os.path.join(HERE, "..", "..", "Arm Control", "Up_and_Down.py")
rng = np.random.default_rng(1)


def random_q(kin, n):
    lo, hi = kin.limits[:, 0], kin.limits[:, 1]
    return [rng.uniform(lo, hi) for _ in range(n)]


@pytest.fixture(scope="module")
def kin():
    return PiperKinematics(load_config().robot)


def test_fk_matches_up_and_down(kin):
    spec = importlib.util.spec_from_file_location("up_and_down", UP_AND_DOWN)
    ud = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(ud)  # piper_sdk is only imported inside main()
    assert kin.variant == "dh_is_offset_1"  # the table Up_and_Down.py uses
    for q in random_q(kin, 200):
        R_ud, p_ud = ud.fk(np.degrees(q).tolist())
        T = kin.fk(q, tool=False)
        assert np.allclose(T[:3, 3] * 1000, p_ud, atol=1e-6)
        assert np.allclose(T[:3, :3], R_ud, atol=1e-9)


def test_ik_round_trip(kin):
    for q in random_q(kin, 30):
        T = kin.fk(q)
        q_ik = kin.ik(T, q + rng.normal(0, 0.15, 6))
        assert q_ik is not None
        T_ik = kin.fk(q_ik)
        assert np.linalg.norm(T_ik[:3, 3] - T[:3, 3]) < 1e-4
        assert np.allclose(T_ik[:3, :3], T[:3, :3], atol=1e-3)


def test_engine_tcp_matches_dh():
    pytest.importorskip("mujoco")
    from digital_twin.sim import make_sim
    sim = make_sim(quiet=True)
    for q in random_q(sim.kin, 20):
        sim.engine.set_arm_q(q)
        T_engine = sim.engine.site_pose("tcp")
        T_dh = sim.cell.arm_pose @ sim.kin.fk(q)
        assert np.linalg.norm(T_engine[:3, 3] - T_dh[:3, 3]) < 1e-6
        assert np.allclose(T_engine[:3, :3], T_dh[:3, :3], atol=1e-6)
