"""End to end: the planner gets prints off the plate in both engines, and the tags decode."""
import numpy as np
import pytest

from digital_twin.sim import make_sim, ready
from digital_twin.tasks.pick_place import PickPlace


def run_one(engine, name):
    sim = make_sim(engine=engine, quiet=True)
    ready(sim)
    pp = PickPlace(sim.cell, sim.robot, sim.cfg)
    rec = pp.run([name])[0]
    return sim, rec


def test_kinematic_engine_clears_cube():
    sim, rec = run_one("kinematic", "calibration_cube")
    assert rec["result"] == "done", rec
    assert rec["in_box"]


def test_mujoco_cube_into_box():
    pytest.importorskip("mujoco")
    sim, rec = run_one("mujoco", "calibration_cube")
    assert rec["result"] == "done", rec
    assert not sim.engine.bonded("calibration_cube")
    assert sim.robot.collisions == []


def test_mujoco_action_figure_onto_shelf():
    pytest.importorskip("mujoco")
    sim, rec = run_one("mujoco", "action_figure")
    assert rec["result"] == "done", rec
    assert rec["shelf_tilt_deg"] < 5  # standing up


def test_tags_decode_in_rendered_frame():
    pytest.importorskip("mujoco")
    pytest.importorskip("cv2")
    from digital_twin.perception.apriltags import detect, intrinsics
    sim = make_sim(quiet=True)
    try:
        img = sim.engine.render("mpzy", 1920, 1080)
    except Exception as exc:  # no OpenGL on this machine
        pytest.skip(f"no offscreen rendering: {exc}")
    ids = {d["id"] for d in detect(img, intrinsics(67.0, 1920, 1080))}
    assert {1, 2, 3} <= ids  # W2, W3, W4: big table tags facing the camera
