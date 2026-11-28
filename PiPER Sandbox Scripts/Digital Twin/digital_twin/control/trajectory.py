"""Trajectories: smooth joint-space moves and straight-line Cartesian moves.

Both return a JointTrajectory that controllers sample at any time t: q(t) and qd(t). Joint
moves use a quintic (minimum-jerk) time scaling, so they start and stop with zero velocity
and acceleration, like the PiPER's own MOVE J; Cartesian moves solve IK along the line.
"""
from __future__ import annotations

import numpy as np

from ..transforms import make_pose, slerp_rot


def quintic(s: np.ndarray | float):
    """Minimum-jerk scaling of normalised time s in [0, 1]: (position, velocity) factors."""
    s = np.clip(s, 0.0, 1.0)
    return 10 * s ** 3 - 15 * s ** 4 + 6 * s ** 5, 30 * s ** 2 - 60 * s ** 3 + 30 * s ** 4


class JointTrajectory:
    """Piecewise path through joint waypoints at given times (linear between samples, which
    are dense for Cartesian moves), or one quintic segment for a joint move."""

    def __init__(self, times, waypoints, quintic_segment: bool = False):
        self.t = np.asarray(times, float)
        self.q = np.asarray(waypoints, float)
        self.quintic_segment = quintic_segment

    @property
    def duration(self) -> float:
        return float(self.t[-1] - self.t[0])

    def sample(self, t: float):
        if self.quintic_segment:
            T = max(self.duration, 1e-9)
            p, v = quintic((t - self.t[0]) / T)
            dq = self.q[1] - self.q[0]
            return self.q[0] + p * dq, v * dq / T if 0 <= t - self.t[0] <= T else 0 * dq
        if t <= self.t[0]:
            return self.q[0].copy(), np.zeros(self.q.shape[1])
        if t >= self.t[-1]:
            return self.q[-1].copy(), np.zeros(self.q.shape[1])
        i = int(np.searchsorted(self.t, t)) - 1
        h = self.t[i + 1] - self.t[i]
        a = (t - self.t[i]) / h
        return self.q[i] + a * (self.q[i + 1] - self.q[i]), (self.q[i + 1] - self.q[i]) / h


def joint_move(q0, q1, max_speed, speed_fraction: float, t0: float = 0.0, min_time: float = 0.4):
    """Quintic move from q0 to q1 with each joint under speed_fraction of its max speed."""
    q0, q1 = np.asarray(q0, float), np.asarray(q1, float)
    T = 1.875 * np.max(np.abs(q1 - q0) / (np.asarray(max_speed) * speed_fraction))  # quintic peak = 1.875 x mean
    T = max(T, min_time)
    return JointTrajectory([t0, t0 + T], [q0, q1], quintic_segment=True)


def linear_move(kin, base_inv, q0, T_start_world, T_goal_world, speed: float, t0: float = 0.0,
                n_min: int = 10, min_time: float = 0.4):
    """Straight-line TCP move (world frame) at `speed` m/s, minimum-jerk along the line.
    Returns (trajectory, ok); ok is False if IK failed somewhere along the line."""
    p0, p1 = T_start_world[:3, 3], T_goal_world[:3, 3]
    R0, R1 = T_start_world[:3, :3], T_goal_world[:3, :3]
    dist = np.linalg.norm(p1 - p0)
    ang = np.linalg.norm(np.arccos(np.clip((np.trace(R0.T @ R1) - 1) / 2, -1, 1)))
    T = max(1.875 * dist / speed, 1.875 * ang / 0.6, min_time)
    n = max(n_min, int(T * 50))
    times, qs = [], []
    q = np.asarray(q0, float)
    ok = True
    for k in range(n + 1):
        u = k / n
        s, _ = quintic(u)
        Tw = make_pose(slerp_rot(R0, R1, s), p0 + s * (p1 - p0))
        q_new = kin.ik(base_inv @ Tw, q, extra_seeds=0)
        if q_new is None or (qs and np.max(np.abs(q_new - qs[-1])) > 0.35):
            ok = False
            q_new = q
        q = q_new
        times.append(t0 + u * T)
        qs.append(q)
    return JointTrajectory(times, qs), ok
