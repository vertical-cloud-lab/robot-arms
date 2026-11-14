"""The interface every physics engine implements. Controllers, the task planner, perception
and the viewers only talk to this, so engines are interchangeable.

To add an engine (PyBullet, Genesis, Drake, Isaac ...): subclass PhysicsEngine, build your
model from the engine-agnostic Scene (world/scene.py) in __init__, implement the methods
below, and register it in engines/__init__.py. Look at kinematic_engine.py for the smallest
complete example and mujoco_engine.py for the full one.
"""
from __future__ import annotations

from abc import ABC, abstractmethod

import numpy as np

from ..world.scene import Scene


class PhysicsEngine(ABC):
    name = "base"
    has_dynamics = True  # False for engines that only move things kinematically

    def __init__(self, scene: Scene, cfg):
        self.scene = scene
        self.cfg = cfg
        self.bond_log: list[dict] = []  # one entry per bond break: print, time, loads

    # --- time ----------------------------------------------------------------------------
    @property
    @abstractmethod
    def time(self) -> float: ...

    @property
    @abstractmethod
    def dt(self) -> float: ...

    @abstractmethod
    def step(self, n: int = 1) -> None:
        """Advance n physics steps with the current actuator commands held."""

    # --- robot state and commands ----------------------------------------------------------
    @abstractmethod
    def arm_q(self) -> np.ndarray: ...

    @abstractmethod
    def arm_qd(self) -> np.ndarray: ...

    @abstractmethod
    def gripper_travel(self) -> float:
        """Each finger's travel from fully closed (stock fingers touching), m."""

    @abstractmethod
    def set_arm_torque(self, tau: np.ndarray) -> None: ...

    @abstractmethod
    def set_gripper_force(self, f: float) -> None:
        """Force on the finger drive, N (+ opens, - closes); the squeeze at each jaw is f/2."""

    def gravity_torque(self) -> np.ndarray:
        """Torques that hold the arm still against gravity (and Coriolis), for feed-forward."""
        return np.zeros(6)

    def set_arm_q(self, q: np.ndarray) -> None:
        """Teleport the arm (for resets and kinematic engines)."""
        raise NotImplementedError

    def set_arm_target(self, q: np.ndarray, qd: np.ndarray | None = None) -> None:
        """Kinematic engines follow targets directly; dynamic engines ignore this."""

    def set_gripper_target(self, travel: float) -> None:
        """Kinematic engines follow targets directly; dynamic engines ignore this."""

    # --- world state ---------------------------------------------------------------------
    @abstractmethod
    def body_pose(self, name: str) -> np.ndarray: ...

    @abstractmethod
    def site_pose(self, name: str) -> np.ndarray: ...

    def print_names(self) -> list[str]:
        return [b.name for b, _ in self.scene.root.walk() if b.kind == "print"]

    # --- adhesion bonds (physics/adhesion.py decides; engines report and break) -------------
    @abstractmethod
    def bonded(self, print_name: str) -> bool: ...

    def bond_index(self, print_name: str) -> float:
        """Current failure index of a print's bond (>= 1 breaks it); 0 when not loaded."""
        return 0.0

    def contact_force(self, bodies_a, bodies_b) -> float:
        """Total normal contact force (N) between two groups of bodies (0 without physics)."""
        return 0.0

    def push(self, body: str, force_world, point_world=None) -> None:
        """Apply an external force to a body (for compliance tests); no-op without physics."""

    # --- collisions ------------------------------------------------------------------------
    def arm_collisions(self, q: np.ndarray, gripper_travel: float | None = None,
                       ignore: tuple = ()) -> list[tuple[str, str]]:
        """Pairs of (robot geom, other geom) in contact if the arm were at q. Used by the
        planner to check paths before running them. Engines without collision return []."""
        return []

    # --- rendering -------------------------------------------------------------------------
    def render(self, camera: str = "mpzy", width: int = 1280, height: int = 720) -> np.ndarray | None:
        return None

    def launch_viewer(self):
        """An interactive window, or None. Returns a handle with .sync() and .is_running()."""
        return None

    def close(self) -> None:
        pass
