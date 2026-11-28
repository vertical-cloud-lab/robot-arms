"""Modified (Craig) Denavit-Hartenberg chains: forward kinematics, frames and Jacobians.

This is the arm's kinematic "source of truth" in the twin. Every engine builds the arm's body
tree from the same DH table (config/robot_piper.yaml), so the joint angles the sim reports are
the joint angles piper_sdk reports for the real arm, and fk() here equals the SDK's FK.

Convention (the same as piper_sdk and `Arm Control/Up_and_Down.py`): row i of the table is
(a_{i-1}, alpha_{i-1}, theta_offset_i, d_i), and

    T_{i-1,i} = RotX(alpha_{i-1}) * TransX(a_{i-1}) * RotZ(theta_offset_i + q_i) * TransZ(d_i)

Units here are SI (metres, radians); the YAML file stores mm and degrees, like the SDK.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True)
class DHRow:
    a: float  # m, a_{i-1}
    alpha: float  # rad, alpha_{i-1}
    theta_offset: float  # rad, added to the joint angle
    d: float  # m


def link_transform(row: DHRow, q: float) -> np.ndarray:
    """4x4 transform from frame i-1 to frame i for joint angle q (rad)."""
    ca, sa = np.cos(row.alpha), np.sin(row.alpha)
    ct, st = np.cos(row.theta_offset + q), np.sin(row.theta_offset + q)
    return np.array([
        [ct, -st, 0.0, row.a],
        [st * ca, ct * ca, -sa, -sa * row.d],
        [st * sa, ct * sa, ca, ca * row.d],
        [0.0, 0.0, 0.0, 1.0],
    ])


def fixed_part(row: DHRow) -> tuple[np.ndarray, np.ndarray]:
    """Pose of frame i in frame i-1 with the joint at its zero *including* the theta offset, as
    (position, 3x3 rotation). Engines place body i there and add a hinge about its local z:
    rotating about z commutes with the TransZ(d) that follows it, so this is exact."""
    T = link_transform(row, 0.0)
    return T[:3, 3].copy(), T[:3, :3].copy()


class DHChain:
    """A serial chain of revolute joints described by modified DH rows."""

    def __init__(self, rows: list[DHRow], base: np.ndarray | None = None,
                 tool: np.ndarray | None = None):
        self.rows = list(rows)
        self.base = np.eye(4) if base is None else np.asarray(base, float)  # world <- frame 0
        self.tool = np.eye(4) if tool is None else np.asarray(tool, float)  # flange <- tool

    @property
    def n(self) -> int:
        return len(self.rows)

    def frames(self, q) -> list[np.ndarray]:
        """World poses of frames 1..n (frame n is the flange), without the tool."""
        T = self.base.copy()
        out = []
        for row, qi in zip(self.rows, q):
            T = T @ link_transform(row, float(qi))
            out.append(T.copy())
        return out

    def fk(self, q, tool: bool = True) -> np.ndarray:
        """4x4 world pose of the flange (tool=False) or of the tool point (tool=True)."""
        T = self.frames(q)[-1]
        return T @ self.tool if tool else T

    def jacobian(self, q, tool: bool = True) -> np.ndarray:
        """6xn geometric Jacobian [v; w] of the flange or tool point, in the world frame."""
        return self.fk_jac(q, tool)[1]

    def fk_jac(self, q, tool: bool = True) -> tuple[np.ndarray, np.ndarray]:
        """End pose and Jacobian from one pass over the chain (what IK needs every iteration)."""
        frames = self.frames(q)
        T_end = frames[-1] @ self.tool if tool else frames[-1]
        p_end = T_end[:3, 3]
        J = np.zeros((6, self.n))
        for i, T in enumerate(frames):
            z, p = T[:3, 2], T[:3, 3]  # joint i rotates about frame i's z axis
            J[:3, i] = np.cross(z, p_end - p)
            J[3:, i] = z
        return T_end, J
