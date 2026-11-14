"""Controllers: turn targets into joint torques and a gripper force, every control step.

All three run on top of the engine's gravity model and are clipped to the joint torque limits:

    JointImpedance      tau = kp (q* - q) + kd (qd* - qd) + tau_ff + g(q)
                        = piper_sdk's JointMitCtrl(pos_ref, vel_ref, kp, kd, t_ref) plus gravity
                        compensation. With stiff gains it behaves like the firmware's position
                        mode (JointCtrl); with soft gains it is compliant.
    CartesianImpedance  tau = J^T (K (x* - x) - D v) + g(q) + null-space posture term
                        A spring at the TCP: push on the gripper and it gives like a spring of
                        stiffness K. This is the building block for compliant insertion,
                        wiping, hand-guiding and force-limited contact.
    GripperForce        force-limited position control of the fingers (GripperCtrl(angle,
                        effort)): closes until it meets something, then squeezes with `force`.
"""
from __future__ import annotations

import numpy as np

from ..transforms import rotvec


class JointImpedance:
    def __init__(self, kp, kd, torque_limit, gravity_comp: bool = True):
        self.kp, self.kd = np.asarray(kp, float), np.asarray(kd, float)
        self.limit = np.asarray(torque_limit, float)
        self.gravity_comp = gravity_comp

    def __call__(self, q, qd, q_ref, qd_ref, g, tau_ff=None):
        tau = self.kp * (q_ref - q) + self.kd * (qd_ref - qd)
        if tau_ff is not None:
            tau = tau + tau_ff
        if self.gravity_comp:
            tau = tau + g
        return np.clip(tau, -self.limit, self.limit)


class CartesianImpedance:
    def __init__(self, kin, base_pose, stiffness, damping_ratio, torque_limit, posture_kp=2.0, posture_kd=0.5):
        self.kin = kin
        self.base_inv = np.linalg.inv(base_pose)
        self.base_R = base_pose[:3, :3]
        self.K = np.diag(stiffness)
        # Critical damping for a unit effective mass: D = 2 zeta sqrt(K).
        self.D = np.diag(2 * damping_ratio * np.sqrt(np.asarray(stiffness, float)))
        self.limit = np.asarray(torque_limit, float)
        self.posture_kp, self.posture_kd = posture_kp, posture_kd

    def __call__(self, q, qd, T_ref_world, g, q_posture=None):
        T = self.kin.fk(q)  # base frame
        Tr = self.base_inv @ T_ref_world
        e = np.concatenate([Tr[:3, 3] - T[:3, 3], rotvec(Tr[:3, :3] @ T[:3, :3].T)])
        J = self.kin.jacobian(q)
        v = J @ qd
        wrench = self.K @ e - self.D @ v
        tau = J.T @ wrench + g
        if q_posture is not None:  # keep the elbow where it was, without fighting the spring
            Jp = np.linalg.pinv(J)
            N = np.eye(len(q)) - J.T @ Jp.T
            tau += N @ (self.posture_kp * (q_posture - q) - self.posture_kd * qd)
        return np.clip(tau, -self.limit, self.limit)


class GripperForce:
    def __init__(self, kp=800.0, kd=20.0, max_force=40.0):
        self.kp, self.kd = kp, kd
        self.max_force = max_force  # squeeze at each jaw, N

    def __call__(self, travel, speed, travel_ref, squeeze_n):
        """Drive force (the actuator's, = 2 x the squeeze at each jaw when holding)."""
        f = self.kp * (travel_ref - travel) - self.kd * speed
        squeeze = min(squeeze_n, self.max_force)
        return float(np.clip(f, -2 * squeeze, 2 * self.max_force))
