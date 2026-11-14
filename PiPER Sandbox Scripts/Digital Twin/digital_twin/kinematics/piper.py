"""The PiPER's kinematics, as configured in robot_piper.yaml: FK, Jacobian and IK.

    kin = PiperKinematics(cfg.robot)
    T = kin.fk(q)                 # TCP pose in the arm's base frame (q in rad)
    q = kin.ik(T_target, q_seed)  # joint angles (rad) or None

Everything is in the arm's base frame (piper_sdk's: x forward, y left, z up, metres).
fk(q, tool=False) is the flange, which is what piper_sdk's GetFK / end-pose reports.
"""
from __future__ import annotations

import numpy as np

from ..config import deg, mm
from ..transforms import make_pose, rotvec
from .dh import DHChain, DHRow


class PiperKinematics:
    def __init__(self, robot_cfg: dict):
        k = robot_cfg["kinematics"]
        rows = k[k["variant"]]
        self.variant = k["variant"]
        self.chain = DHChain([DHRow(float(mm(a)), float(deg(al)), float(deg(th)), float(mm(d)))
                              for a, al, th, d in rows])
        self.tcp = make_pose(None, mm(k["tcp_mm"]))
        self.chain.tool = self.tcp
        self.limits = deg(robot_cfg["joints"]["limits_deg"])
        self.max_speed = deg(robot_cfg["joints"]["max_speed_dps"])
        self.n = self.chain.n

    # --- forward ---------------------------------------------------------------------------
    def fk(self, q, tool: bool = True) -> np.ndarray:
        return self.chain.fk(q, tool)

    def frames(self, q):
        return self.chain.frames(q)

    def jacobian(self, q, tool: bool = True) -> np.ndarray:
        return self.chain.jacobian(q, tool)

    def within_limits(self, q, margin: float = 0.0) -> bool:
        q = np.asarray(q)
        return bool(np.all(q >= self.limits[:, 0] + margin) and np.all(q <= self.limits[:, 1] - margin))

    def clamp(self, q):
        return np.clip(q, self.limits[:, 0], self.limits[:, 1])

    # --- inverse ---------------------------------------------------------------------------
    def ik(self, T_target: np.ndarray, q_seed, *, tool: bool = True, extra_seeds: int = 12,
           pos_tol: float = 2e-5, rot_tol: float = 2e-4, rot_weight: float = 0.25,
           rng: np.random.Generator | None = None) -> np.ndarray | None:
        """Damped-least-squares IK with joint limits, from q_seed and then random seeds.
        Returns the solution closest to q_seed (weighted toward the big joints), or None."""
        rng = rng or np.random.default_rng(0)
        seeds = [np.asarray(q_seed, float)]
        lo, hi = self.limits[:, 0], self.limits[:, 1]
        if extra_seeds:
            # Elbow-up postures pointed at the target first (they usually converge), then random.
            p = T_target[:3, 3]
            j1 = float(np.clip(np.arctan2(p[1], p[0]), lo[0], hi[0]))
            for j2, j3, j5 in ((80, -60, 40), (100, -90, 60), (60, -30, 20), (90, -40, 0)):
                seeds.append(self.clamp(np.radians([np.degrees(j1), j2, j3, 0, j5, 0])))
            for _ in range(extra_seeds):
                seeds.append(rng.uniform(lo, hi))
        best, best_cost = None, np.inf
        W = np.array([2.0, 2.0, 1.5, 1.0, 1.0, 0.5])  # prefer moving the wrist over the shoulder
        for i, s in enumerate(seeds):
            q = self._solve(T_target, s, tool, pos_tol, rot_tol, rot_weight)
            if q is None:
                continue
            cost = float(np.sum(W * (q - seeds[0]) ** 2))
            if cost < best_cost:
                best, best_cost = q, cost
            if i == 0 and best is not None and cost < 0.05:
                break  # the seed itself converged nearby: good enough, skip the random restarts
        return best

    def _solve(self, T_target, q0, tool, pos_tol, rot_tol, rot_weight, iters: int = 120):
        q = self.clamp(np.array(q0, float))
        lam = 0.02
        for _ in range(iters):
            T, J = self.chain.fk_jac(q, tool)
            e_p = T_target[:3, 3] - T[:3, 3]
            e_r = rotvec(T_target[:3, :3] @ T[:3, :3].T)
            if np.linalg.norm(e_p) < pos_tol and np.linalg.norm(e_r) < rot_tol:
                return q
            e = np.concatenate([e_p, rot_weight * e_r])
            Jw = J.copy()
            Jw[3:] *= rot_weight
            dq = Jw.T @ np.linalg.solve(Jw @ Jw.T + lam ** 2 * np.eye(6), e)
            step = np.max(np.abs(dq))
            if step > 0.2:
                dq *= 0.2 / step
            q = self.clamp(q + dq)
        T = self.chain.fk(q, tool)
        ok = (np.linalg.norm(T_target[:3, 3] - T[:3, 3]) < pos_tol * 10 and
              np.linalg.norm(rotvec(T_target[:3, :3] @ T[:3, :3].T)) < rot_tol * 10)
        return q if ok else None
