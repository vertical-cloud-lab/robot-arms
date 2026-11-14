"""SimRobot: the simulated PiPER you program against. It owns the control loop.

    robot = SimRobot(engine, kin, cfg, base_pose)
    robot.move_joints(q)                 # quintic joint move (like JointCtrl + MOVE J)
    robot.move_linear(T_world, 0.04)     # straight TCP line at 40 mm/s
    robot.set_gripper(width_m=0.04)      # open to a 40 mm gap between the sleeves
    robot.grip(squeeze_n=20)             # close until contact, squeeze with 20 N per jaw
    robot.compliant(T_world, duration)   # Cartesian impedance: a spring holds the TCP there
    robot.wait(0.5)

Each call runs the physics until the move is done, calling every function in
`robot.on_frame` (video recorders, the live viewer) as it goes. Every move is checked for
the arm hitting the cell before it runs (collision_check), and `robot.log` keeps what happened.

PiperSDK (below) wraps a SimRobot in the parts of piper_sdk's C_PiperInterface_V2 that the
lab's scripts use, with the same units (0.001 deg, 0.001 mm), so code written for the arm can
be pointed at the twin first.
"""
from __future__ import annotations

from types import SimpleNamespace as NS

import numpy as np

from .controllers import CartesianImpedance, GripperForce, JointImpedance
from .trajectory import joint_move, linear_move


class SimRobot:
    def __init__(self, engine, kin, cfg, base_pose: np.ndarray):
        self.engine, self.kin, self.cfg = engine, kin, cfg
        rc = cfg.robot
        self.base_pose = base_pose
        self.base_inv = np.linalg.inv(base_pose)
        self.task = cfg.sim["task"]
        tl = rc["joints"]["max_torque_nm"]
        self.joint_ctrl = JointImpedance(rc["control"]["kp"], rc["control"]["kd"], tl)
        self.cart_ctrl = CartesianImpedance(kin, base_pose, rc["control"]["cartesian_stiffness"],
                                            rc["control"]["cartesian_damping_ratio"], tl)
        g = rc["gripper"]
        self.grip_ctrl = GripperForce(kp=3000.0, kd=40.0, max_force=g["max_force_n"])
        self.sleeve_t = engine.scene.info["sleeve_thickness"]
        self.travel_range = engine.scene.info["finger_travel_range"]
        self.grip_speed = g["max_speed_mm_s"] / 1000 / 2  # per finger
        self.decimation = max(1, int(round(1.0 / (rc["control"]["rate_hz"] * engine.dt))))
        # Current command state.
        self.mode = "joint"
        self.traj = None
        self.traj_t0 = 0.0
        q = engine.arm_q()
        self.q_ref, self.qd_ref = q.copy(), np.zeros(6)
        self.T_ref = None
        self.q_posture = q.copy()
        self.grip_target = engine.gripper_travel()
        self.grip_ref = self.grip_target
        self.squeeze = g["max_force_n"]
        self.on_frame = []  # callables(robot) run every `frame_every` seconds
        self.frame_every = 1 / 30
        self._next_frame = 0.0
        self.log: list[dict] = []
        self.collision_check = True
        self.collisions: list[dict] = []

    # --- the loop ----------------------------------------------------------------------------
    def _control(self):
        e, t = self.engine, self.engine.time
        q, qd, g = e.arm_q(), e.arm_qd(), e.gravity_torque()
        if self.mode == "joint":
            if self.traj is not None:
                self.q_ref, self.qd_ref = self.traj.sample(t - self.traj_t0)
            tau = self.joint_ctrl(q, qd, self.q_ref, self.qd_ref, g)
        else:  # cartesian impedance
            tau = self.cart_ctrl(q, qd, self.T_ref, g, self.q_posture)
        e.set_arm_torque(tau)
        e.set_arm_target(self.q_ref, self.qd_ref)
        # Gripper: move the reference toward the target at the gripper's speed.
        step = self.grip_speed * e.dt * self.decimation
        self.grip_ref += np.clip(self.grip_target - self.grip_ref, -step, step)
        travel = e.gripper_travel()
        speed = getattr(e, "gripper_speed", lambda: 0.0)()
        e.set_gripper_force(self.grip_ctrl(travel, speed, self.grip_ref, self.squeeze))
        e.set_gripper_target(self.grip_ref)

    def run(self, duration: float):
        e = self.engine
        n = max(1, int(round(duration / e.dt)))
        for i in range(n):
            if i % self.decimation == 0:
                self._control()
            e.step(1)
            if self.on_frame and e.time >= self._next_frame:
                self._next_frame = e.time + self.frame_every
                for f in self.on_frame:
                    f(self)

    # --- helpers --------------------------------------------------------------------------------
    def tcp_world(self, q=None) -> np.ndarray:
        q = self.engine.arm_q() if q is None else q
        return self.base_pose @ self.kin.fk(q)

    def ik_world(self, T_world, q_seed=None, extra_seeds=12):
        q_seed = self.engine.arm_q() if q_seed is None else q_seed
        return self.kin.ik(self.base_inv @ T_world, q_seed, extra_seeds=extra_seeds)

    def gap(self) -> float:
        """Gap between the sleeves, m."""
        return 2 * (self.engine.gripper_travel() - self.sleeve_t)

    def _check_path(self, traj, label, ignore=()):
        if not self.collision_check:
            return []
        hits = []
        for t in np.linspace(traj.t[0], traj.t[-1], 25):
            q, _ = traj.sample(t)
            for pair in self.engine.arm_collisions(q, self.engine.gripper_travel(), ignore):
                if pair not in hits:
                    hits.append(pair)
        if hits:
            self.collisions.append({"move": label, "time": self.engine.time, "pairs": hits[:6]})
        return hits

    # --- moves -----------------------------------------------------------------------------------
    def move_joints(self, q_goal, speed_fraction=None, label="move_joints", ignore=()):
        sf = speed_fraction or self.task["speed_fraction"]
        q0 = self.q_ref.copy() if self.mode == "joint" else self.engine.arm_q()
        traj = joint_move(q0, q_goal, self.kin.max_speed, sf)
        self._check_path(traj, label, ignore)
        self.mode, self.traj, self.traj_t0 = "joint", traj, self.engine.time
        self.run(traj.duration + 0.15)
        self.traj = None
        self.q_ref, self.qd_ref = np.asarray(q_goal, float), np.zeros(6)
        self.log.append({"t": self.engine.time, "move": label, "ok": True})
        return True

    def move_linear(self, T_goal_world, speed=None, label="move_linear", ignore=()):
        speed = speed or self.task["slow_speed_mm_s"] / 1000
        q0 = self.q_ref.copy()
        traj, ok = linear_move(self.kin, self.base_inv, q0, self.tcp_world(q0), T_goal_world, speed)
        if not ok:
            self.log.append({"t": self.engine.time, "move": label, "ok": False, "why": "IK failed on the line"})
            return False
        self._check_path(traj, label, ignore)
        self.mode, self.traj, self.traj_t0 = "joint", traj, self.engine.time
        self.run(traj.duration + 0.1)
        self.traj = None
        self.q_ref, self.qd_ref = traj.q[-1].copy(), np.zeros(6)
        self.log.append({"t": self.engine.time, "move": label, "ok": True})
        return True

    def compliant(self, T_world, duration, label="compliant"):
        """Hold the TCP at T_world with the Cartesian spring (robot_piper.yaml) for duration."""
        self.mode, self.T_ref, self.q_posture = "cartesian", T_world, self.engine.arm_q()
        self.run(duration)
        self.mode = "joint"
        self.q_ref, self.qd_ref = self.engine.arm_q(), np.zeros(6)
        self.log.append({"t": self.engine.time, "move": label, "ok": True})

    def set_gripper(self, width_m=None, travel=None, wait=True):
        """Open or close to a gap between the sleeves (m), at the gripper's speed."""
        lo, hi = self.travel_range
        if travel is None:
            travel = width_m / 2 + self.sleeve_t
        self.grip_target = float(np.clip(travel, lo, hi))
        self.squeeze = self.grip_ctrl.max_force
        if wait:
            t = abs(self.grip_target - self.engine.gripper_travel()) / self.grip_speed + 0.15
            self.run(t)

    def grip(self, squeeze_n=None, settle=None, contact_n=2.0):
        """Close until the sleeves meet the print, then squeeze with squeeze_n at each jaw.
        It closes gently (contact_n) and only then ramps up the squeeze, so a print that is
        a little off-centre is nudged, not shoved, before both sleeves are on it."""
        target = squeeze_n or self.cfg.robot["gripper"]["default_force_n"]
        lo, _ = self.travel_range
        self.squeeze = contact_n
        self.grip_target = lo  # aim fully closed; the force limit is what stops it
        t0 = self.engine.time
        while self.engine.time - t0 < 2.5:
            self.run(0.05)
            if abs(getattr(self.engine, "gripper_speed", lambda: 0.0)()) < 2e-4 and self.engine.time - t0 > 0.2:
                break
        for k in range(1, 11):  # ramp the squeeze over 0.3 s
            self.squeeze = contact_n + (target - contact_n) * k / 10
            self.run(0.03)
        self.run(settle if settle is not None else self.task["grasp_settle_s"])
        return self.gap()

    def wait(self, t):
        self.run(t)


class PiperSDK:
    """piper_sdk-style facade over a SimRobot (C_PiperInterface_V2 subset, same units).
    Calls take effect immediately; call .robot.run(seconds) (or .spin(seconds)) to let time
    pass, since the sim isn't tied to the wall clock."""

    MDEG = 1000.0

    def __init__(self, robot: SimRobot):
        self.robot = robot
        self.speed_pct = 50
        self.enabled = [True] * 7
        self.offset_mm = robot.cfg.robot["gripper"]["reading_offset_mm"]

    def ConnectPort(self, *a, **k):
        return True

    def EnablePiper(self):
        self.enabled = [True] * 7
        return True

    def EnableArm(self, motor_num=7, enable_flag=0x02):
        if motor_num == 7:
            self.enabled = [True] * 7
        else:
            self.enabled[motor_num - 1] = True

    def DisablePiper(self):
        self.enabled = [False] * 7

    def GetArmEnableStatus(self):
        return list(self.enabled[:6])

    def MotionCtrl_2(self, ctrl_mode=0x01, move_mode=0x01, move_spd_rate_ctrl=50, is_mit_mode=0x00):
        self.speed_pct = max(1, min(100, int(move_spd_rate_ctrl)))

    def JointCtrl(self, *mdeg):
        q = np.radians(np.asarray(mdeg, float) / self.MDEG)
        r = self.robot
        traj = joint_move(r.engine.arm_q(), r.kin.clamp(q), r.kin.max_speed, self.speed_pct / 100)
        r.mode, r.traj, r.traj_t0 = "joint", traj, r.engine.time

    def JointMitCtrl(self, motor_num, pos_ref, vel_ref, kp, kd, t_ref):
        """One joint in MIT mode: tau = kp (pos_ref - q) + kd (vel_ref - qd) + t_ref (SI units)."""
        r = self.robot
        i = motor_num - 1
        r.traj = None
        r.joint_ctrl.kp[i], r.joint_ctrl.kd[i] = kp, kd
        r.q_ref[i], r.qd_ref[i] = pos_ref, vel_ref

    def GripperCtrl(self, gripper_angle=0, gripper_effort=0, gripper_code=0x01, set_zero=0x00):
        reading_mm = gripper_angle / 1000.0
        self.robot.grip_target = float(np.clip((reading_mm - self.offset_mm) / 2000.0, *self.robot.travel_range))
        if gripper_effort:
            self.robot.squeeze = gripper_effort / 1000.0 * 10.0  # 0.001 N*m -> N: ~10 N per N*m (estimate)

    def GetArmJointMsgs(self):
        q = np.degrees(self.robot.engine.arm_q()) * self.MDEG
        js = NS(**{f"joint_{i + 1}": int(round(v)) for i, v in enumerate(q)})
        return NS(joint_state=js, time_stamp=self.robot.engine.time, Hz=200.0)

    def GetArmGripperMsgs(self):
        reading = (2 * self.robot.engine.gripper_travel() * 1000 + self.offset_mm) * 1000
        return NS(gripper_state=NS(grippers_angle=int(round(reading)), grippers_effort=0, status_code=0),
                  time_stamp=self.robot.engine.time, Hz=200.0)

    def GetArmEndPoseMsgs(self):
        """Flange pose like the SDK: X/Y/Z in 0.001 mm, RX/RY/RZ in 0.001 deg (XYZ Euler)."""
        T = self.robot.kin.fk(self.robot.engine.arm_q(), tool=False)
        R = T[:3, :3]
        ry = np.arcsin(np.clip(-R[2, 0], -1, 1))
        rx, rz = np.arctan2(R[2, 1], R[2, 2]), np.arctan2(R[1, 0], R[0, 0])
        p = T[:3, 3] * 1e6
        e = np.degrees([rx, ry, rz]) * 1000
        return NS(end_pose=NS(X_axis=int(p[0]), Y_axis=int(p[1]), Z_axis=int(p[2]),
                              RX_axis=int(e[0]), RY_axis=int(e[1]), RZ_axis=int(e[2])),
                  time_stamp=self.robot.engine.time)

    def spin(self, seconds):
        self.robot.run(seconds)
