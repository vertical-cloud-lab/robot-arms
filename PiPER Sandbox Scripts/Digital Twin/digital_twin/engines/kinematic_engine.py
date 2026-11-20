"""Kinematic engine: no physics engine, numpy only. The smallest complete PhysicsEngine.

Use it to check plans, layouts and reach without installing MuJoCo, or as a template for a
new engine. What it does instead of physics:

- the arm and gripper follow their targets exactly (no dynamics, no torque limits);
- a print counts as gripped once the sleeves close to its width with it between them, and then
  rides along with the gripper;
- a gripped print's bond to the plate "breaks" as soon as the gripper moves it by more than
  `break_mm` or `break_deg` (no forces here, so the adhesion model can't be evaluated);
- a released print drops straight down onto whatever is under it (plate, shelf, box floor,
  table or another print), staying upright;
- no collision checking (arm_collisions returns []): plans that pass here can still crash in
  MuJoCo.
"""
from __future__ import annotations

import numpy as np

from ..world.print_library import bounds
from .base import PhysicsEngine


class KinematicEngine(PhysicsEngine):
    name = "kinematic"
    has_dynamics = False

    def __init__(self, scene, cfg, break_mm: float = 1.0, break_deg: float = 1.5):
        super().__init__(scene, cfg)
        self._dt = cfg.sim.get("kinematic", {}).get("timestep_s", 0.004)
        self._t = 0.0
        self.break_mm, self.break_deg = break_mm, np.radians(break_deg)
        from ..kinematics.piper import PiperKinematics
        self.kin = PiperKinematics(cfg.robot)
        info = scene.info
        self.base = info["arm_pose"]
        self.sleeve_t = info["sleeve_thickness"]
        self.travel_range = info["finger_travel_range"]
        self.q = np.radians(cfg.robot["joints"]["home_deg"]).astype(float)
        self.qd = np.zeros(6)
        self.travel = self.travel_range[0] + 0.02
        self.travel_ref = self.travel
        self._speed = 0.0
        self.poses = {b.name: T for b, T in scene.root.walk()}
        self.prints = {}
        tcp = info.get("tcp_site", "tcp")
        self.tcp_name = tcp
        for b, T in scene.root.walk():
            if b.kind == "print":
                lo, hi = bounds(b.geoms)
                self.prints[b.name] = {"T": T.copy(), "lo": lo, "hi": hi, "bonded": True,
                                       "held": None, "grip_T": None}
        self._supports = self._support_boxes()

    # --- time ------------------------------------------------------------------------------
    @property
    def time(self):
        return self._t

    @property
    def dt(self):
        return self._dt

    def step(self, n: int = 1):
        for _ in range(n):
            self._t += self._dt
            self._update_gripper()
            self._update_prints()

    # --- robot -----------------------------------------------------------------------------
    def arm_q(self):
        return self.q.copy()

    def arm_qd(self):
        return self.qd.copy()

    def gripper_travel(self):
        return self.travel

    def gripper_speed(self):
        return self._speed

    def set_arm_torque(self, tau):
        pass  # no dynamics

    def set_gripper_force(self, f):
        pass

    def set_arm_target(self, q, qd=None):
        self.q = np.asarray(q, float).copy()
        self.qd = np.zeros(6) if qd is None else np.asarray(qd, float).copy()

    def set_gripper_target(self, travel):
        self.travel_ref = float(travel)

    def set_arm_q(self, q):
        self.set_arm_target(q)

    def tcp(self):
        return self.base @ self.kin.fk(self.q)

    # --- world -----------------------------------------------------------------------------
    def body_pose(self, name):
        if name in self.prints:
            return self.prints[name]["T"].copy()
        if name in ("link1", "link2", "link3", "link4", "link5", "link6"):
            return self.base @ self.kin.frames(self.q)[int(name[-1]) - 1]
        return self.poses[name].copy()

    def site_pose(self, name):
        if name == "tcp":
            return self.tcp()
        if name == "flange":
            return self.base @ self.kin.fk(self.q, tool=False)
        raise KeyError(name)

    def bonded(self, print_name):
        p = self.prints.get(print_name)
        return bool(p and p["bonded"])

    # --- the rules that stand in for physics ------------------------------------------------
    def _between_fingers(self, name):
        """Width of the print across the fingers if part of it is between the sleeves (sampled
        on the pads' area with the print's real geometry), else None."""
        from ..world.print_library import inside
        p = self.prints[name]
        T_tcp = self.tcp()
        gap = 2 * (self.travel - self.sleeve_t)
        ys = np.arange(-gap / 2, gap / 2 + 1e-9, 0.0005)
        zs = np.arange(-0.05, 0.0001, 0.002)  # pad area: from the tip up 50 mm (tool z points down)
        Y, Z = np.meshgrid(ys, zs)
        pts_tool = np.column_stack([np.zeros(Y.size), Y.ravel(), Z.ravel(), np.ones(Y.size)])
        pts = pts_tool @ (np.linalg.inv(p["T"]) @ T_tcp).T
        body = self.scene.body(name)
        mask = np.zeros(len(pts), bool)
        for g in body.geoms:
            mask |= inside(g, pts[:, :3])
        if not mask.any():
            return None
        yin = pts_tool[mask, 1]
        return float(2 * max(abs(yin.min()), abs(yin.max())))

    def _update_gripper(self):
        lo, hi = self.travel_range
        speed = 0.03  # m/s per finger
        target = float(np.clip(self.travel_ref, lo, hi))
        new = self.travel + np.clip(target - self.travel, -speed * self._dt, speed * self._dt)
        held = next((n for n, p in self.prints.items() if p["held"]), None)
        if held is None and new < self.travel:  # closing: stop at the first print in the way
            for n in self.prints:
                w = self._between_fingers(n)
                if w is not None and w / 2 + self.sleeve_t > new:
                    new = max(new, w / 2 + self.sleeve_t)
                    p = self.prints[n]
                    p["held"] = True
                    p["grip_T"] = np.linalg.inv(self.tcp()) @ p["T"]
                    p["T_at_grip"] = p["T"].copy()
                    break
        elif held is not None:
            p = self.prints[held]
            w = self._between_fingers(held) or 0.0
            if target > w / 2 + self.sleeve_t + 0.001:  # opened: let go
                p["held"] = None
                self._drop(held)
            else:
                new = max(new, w / 2 + self.sleeve_t)
        self._speed = (new - self.travel) / self._dt
        self.travel = new

    def _update_prints(self):
        for n, p in self.prints.items():
            if not p["held"]:
                continue
            T_new = self.tcp() @ p["grip_T"]
            if p["bonded"]:
                d = np.linalg.norm(T_new[:3, 3] - p["T_at_grip"][:3, 3])
                R = p["T_at_grip"][:3, :3].T @ T_new[:3, :3]
                ang = np.arccos(np.clip((np.trace(R) - 1) / 2, -1, 1))
                if d * 1000 < self.break_mm and ang < self.break_deg:
                    continue  # still stuck: the gripper strains against the bond
                p["bonded"] = False
                self.bond_log.append(dict(print=n, time=self._t, force_n=[0, 0, 0], torque_nm=[0, 0, 0],
                                          index=1.0, note=f"moved {d * 1000:.1f} mm / {np.degrees(ang):.1f} deg"))
            p["T"] = T_new

    def _support_boxes(self):
        """(x0, x1, y0, y1, top z) world rectangles prints can land on."""
        out = []
        c = self.cfg.cell
        W, D, _ = c["table"]["size"]
        out.append((-W / 2000, W / 2000, -D / 2000, D / 2000, 0.0))
        sh = self.poses["shelf"]
        sw, sd, _ = c["shelf"]["size"]
        out.append((sh[0, 3] - sw / 2000, sh[0, 3] + sw / 2000, sh[1, 3] - sd / 2000, sh[1, 3] + sd / 2000, sh[2, 3]))
        bx = self.poses["box"]
        X, Y, _ = c["box"]["outer_size"]
        out.append((bx[0, 3] - X / 2000, bx[0, 3] + X / 2000, bx[1, 3] - Y / 2000, bx[1, 3] + Y / 2000, bx[2, 3]))
        pl = self.poses["plate"]
        px, py, _ = c["printer"]["plate_size"]
        out.append((pl[0, 3] - px / 2000, pl[0, 3] + px / 2000, pl[1, 3] - py / 2000, pl[1, 3] + py / 2000, pl[2, 3]))
        return out

    def _drop(self, name):
        p = self.prints[name]
        T = p["T"]
        x, y = T[0, 3], T[1, 3]
        z = max((top for x0, x1, y0, y1, top in self._supports if x0 <= x <= x1 and y0 <= y <= y1), default=0.0)
        for n, o in self.prints.items():  # land on another print's top if it is underneath
            if n != name and not o["held"]:
                if np.hypot(o["T"][0, 3] - x, o["T"][1, 3] - y) < 0.02:
                    z = max(z, o["T"][2, 3] + o["hi"][2])
        yaw = np.arctan2(T[1, 0], T[0, 0])
        c, s = np.cos(yaw), np.sin(yaw)
        p["T"] = np.array([[c, -s, 0, x], [s, c, 0, y], [0, 0, 1, z], [0, 0, 0, 1.0]])
