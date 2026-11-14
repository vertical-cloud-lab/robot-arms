"""One call that builds everything: config -> cell -> engine -> kinematics -> robot.

    from digital_twin.sim import make_sim
    sim = make_sim()                       # MuJoCo, config/*.yaml
    sim = make_sim(engine="kinematic")     # no physics engine needed
    sim.robot.move_joints(...)             # see control/sim_robot.py
"""
from __future__ import annotations

import warnings
from dataclasses import dataclass

import numpy as np

from .config import Config, load_config
from .control.sim_robot import SimRobot
from .engines import make_engine
from .kinematics.piper import PiperKinematics
from .world.cell import Cell


@dataclass
class Sim:
    cfg: Config
    cell: Cell
    engine: object
    kin: PiperKinematics
    robot: SimRobot


def make_sim(cfg: Config | None = None, engine: str | None = None, quiet: bool = False) -> Sim:
    cfg = cfg or load_config()
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        cell = Cell(cfg)
    if not quiet:
        for w in caught:
            print("warning:", w.message)
    name = engine or cfg.sim.get("engine", "mujoco")
    eng = make_engine(name, cell.scene, cfg)
    if not quiet and hasattr(eng, "start_report"):
        for line in eng.start_report():
            print("warning:", line)
    kin = PiperKinematics(cfg.robot)
    robot = SimRobot(eng, kin, cfg, cell.arm_pose)
    return Sim(cfg, cell, eng, kin, robot)


def ready(sim: Sim):
    """Unfold from the rest pose to the ready pose (robot_piper.yaml joints.ready_deg)."""
    sim.robot.move_joints(np.radians(sim.cfg.robot["joints"]["ready_deg"]), label="unfold to ready")
