"""Physics engines. Pick one by name (sim.yaml `engine:` or `run_sim.py --engine`):

    mujoco     full physics: contacts, friction, gripper forces, bond breaking  (mujoco_engine.py)
    kinematic  no physics engine, numpy only: poses, attach-on-grasp, drops     (kinematic_engine.py)

Add an engine: subclass base.PhysicsEngine and add it to ENGINES below.
"""
from __future__ import annotations


def _mujoco():
    from .mujoco_engine import MujocoEngine
    return MujocoEngine


def _kinematic():
    from .kinematic_engine import KinematicEngine
    return KinematicEngine


ENGINES = {"mujoco": _mujoco, "kinematic": _kinematic}


def make_engine(name: str, scene, cfg, **kw):
    try:
        cls = ENGINES[name]()
    except KeyError:
        raise KeyError(f"unknown engine {name!r}; available: {', '.join(ENGINES)}") from None
    return cls(scene, cfg, **kw)
