"""Swapping the powder doser's auger: take the installed one out, park it in the rack, and snap
another one in (config/powder_doser.yaml, `swap`).

    1. remove   grasp the doser's auger across its tube (fingers closing across it, between
                the gear and the back clip), then get it out of the two snap clips:
                  peel      lift the cap end about the outlet-side clip (one clip at a time,
                            like peeling a tube out of cable clips by hand), then lift
                  straight  pull straight up through both clips at once
                and check that it came out with the gripper, not left behind or slipped
    2. park     carry it over, set it into an empty rack slot, let go
    3. fetch    grasp `swap_in` in its rack slot and lift it out
    4. install  hold it level over the doser with its gear between the tap collar and the back
                clip (axial alignment), lower it onto the clips' mouths, then push down with the
                Cartesian impedance controller (a spring at the TCP) until both clips snap,
                which shows up as the push suddenly meeting no resistance
    5. verify   tube centred in every clip (seated), gear face on the pinion's (meshes), let go

Every step goes in `self.report` (forces from the clips' snap model, slip in the grip, timing),
which scenarios/swap_augers.py prints and saves as JSON.
"""
from __future__ import annotations

import numpy as np

from ..config import deg, mm
from ..transforms import axis_angle, inv, make_pose


class AugerSwap:
    def __init__(self, cell, robot, cfg):
        self.cell, self.robot, self.cfg = cell, robot, cfg
        self.e = robot.engine
        self.sw = cell.dcfg["swap"]
        self.report: list[dict] = []
        g = cfg.robot["gripper"]
        self.tube_r = cell.geo["auger"]["tube_radius"] / 1000
        self.s_grasp = self.sw["grasp_at_mm"] / 1000
        self.squeeze = self.sw.get("squeeze_n", g["default_force_n"])
        self.tip_below_axis = 0.006  # fingertips this far below the tube's axis: pads meet its equator
        self.open_margin = mm(self.sw.get("open_margin_mm", 3))  # finger-to-tube gap when open
        self.doser_clips = [c.name for c in cell.doser.clips]
        self.base_xy = cell.arm_pose[:2, 3]

    # --- geometry -----------------------------------------------------------------------------
    def grasp_pose(self, T_auger: np.ndarray, lean: float = 0.0, flip: int = 1) -> np.ndarray:
        """TCP pose gripping an auger whose frame is T_auger (world): fingers closing across
        the tube at s_grasp, the tool pointing down and tilted by `lean` toward the arm's base
        (the PiPER's wrist can't point straight down this high and this far out).

        For a round tube any tool direction works, as long as the fingers close across the
        tube's axis (closing direction = axis x tool direction): tilting across the tube just
        rolls the grip around it. Tilting ALONG the tube swings the gripper's body down toward
        the tube, so place the auger across the arm's reach (tangential) to keep that small."""
        a = T_auger[:3, 2]
        p = T_auger[:3, 3] + a * self.s_grasp
        u = np.append(p[:2] - self.base_xy, 0.0)
        u /= max(np.linalg.norm(u), 1e-9)  # horizontal, pointing away from the arm's base
        z = np.array([0, 0, -np.cos(lean)]) + u * np.sin(lean)
        d = np.cross(a, z)
        d /= np.linalg.norm(d)
        d *= flip
        x = np.cross(d, z)
        return make_pose(np.column_stack([x, d, z]), p + z * self.tip_below_axis)

    def _hits(self, q, ignore=()):
        """Would the arm or the open gripper touch the cell at q? (ignores the auger itself)"""
        e = getattr(self.robot, "engine", None)
        if e is None:
            return False
        travel = self.tube_r + self.open_margin + self.robot.sleeve_t
        hits = e.arm_collisions(q, travel)
        # The sleeves may touch the tube they are about to grip; nothing else may touch anything.
        return any(not (g1.startswith("finger") and any(g2 == f"{n}/tube" for n in ignore)) for g1, g2 in hits)

    def solve_grasp(self, T_auger, q_seed, rises=(0.0,), ignore=(), then_place=None):
        """Smallest lean (and either finger order, and grasp points across `grasp_window_mm`)
        with IK at the grasp and each `rise` above it, where nothing but the sleeves touches
        the auger's tube. Sets self.s_grasp to the point it chose."""
        s0 = self.sw["grasp_at_mm"] / 1000
        lo, hi = (v / 1000 for v in self.sw.get("grasp_window_mm", [s0 * 1000, s0 * 1000]))
        s_list = sorted({min(max(s0 + d, lo), hi) for d in np.arange(-0.03, 0.0301, 0.005)}, key=lambda v: abs(v - s0))
        for lean in deg([0, 10, 20, 30, 40, 45, 50, 55, 60]):
            best = None
            for sg in s_list:
                self.s_grasp = sg
                for flip in (1, -1):
                    T = self.grasp_pose(T_auger, lean, flip)
                    q = self.robot.ik_world(T, q_seed, extra_seeds=4)
                    if q is None or self._hits(q, ignore):
                        continue
                    qs, ok = [q], True
                    for r in rises[1:]:
                        Tr = T.copy()
                        Tr[2, 3] += r
                        qr = self.robot.ik_world(Tr, qs[-1], extra_seeds=0)
                        if qr is None or self._hits(qr, ignore):
                            ok = False
                            break
                        qs.append(qr)
                    if not ok:
                        continue
                    if then_place is not None:  # this grip must also let it be set down there
                        T_goal, hover = then_place
                        if self.place_solution(inv(T) @ T_auger, T_goal, hover, ignore[0] if ignore else "") is None:
                            continue
                    cost = float(np.sum((q - q_seed) ** 2)) + 50 * abs(sg - s0)
                    if best is None or cost < best[0]:
                        best = (cost, T, qs, sg)
                if best is not None and abs(best[3] - s0) < 1e-9:
                    break
            if best is not None:
                self.s_grasp = best[3]
                return best[1], best[2], float(lean)
        self.s_grasp = s0
        return None

    # --- moves --------------------------------------------------------------------------------
    def _log(self, step, **kw):
        kw = {k: (round(v, 4) if isinstance(v, float) else v) for k, v in kw.items()}
        self.report.append({"t": round(self.e.time, 3), "step": step, **kw})

    def transit(self, T_goal_up, label):
        """Up to a safe height, across in joint space, arrive above the goal."""
        r = self.robot
        T_now = r.tcp_world(r.q_ref)
        z_safe = max(T_now[2, 3], T_goal_up[2, 3])
        T_rise = T_now.copy()
        T_rise[2, 3] = z_safe
        if z_safe - T_now[2, 3] > 0.005:
            r.move_linear(T_rise, 0.08, label=f"{label}: rise", ignore=self._ignore())
        q_up = r.ik_world(T_goal_up, r.q_ref, extra_seeds=8)
        if q_up is None:
            self._log(label, ok=False, why="no IK above the goal")
            return False
        r.move_joints(q_up, label=f"{label}: over", ignore=self._ignore())
        return True

    def _ignore(self):
        return tuple(self.held) if getattr(self, "held", None) else ()

    def held_in_grip(self, auger) -> float:
        """Distance (mm) the auger has moved relative to the gripper since it was grasped:
        0 = held firmly, growing = slipping or rotating in the grip."""
        T_rel = inv(self.robot.tcp_world()) @ self.e.body_pose(auger)
        d = T_rel[:3, 3] - self._grip_rel[:3, 3]
        ang = np.degrees(np.arccos(np.clip((np.trace(self._grip_rel[:3, :3].T @ T_rel[:3, :3]) - 1) / 2, -1, 1)))
        return float(np.linalg.norm(d) * 1000), float(ang)

    def grasp(self, auger: str, where: str, then_place=None) -> bool:
        """Grip an auger where it lies. then_place=(target auger pose, hover): only grips from
        which the arm can also set it down there (so it needn't be re-gripped on the way)."""
        r, sw = self.robot, self.sw
        T_a = self.e.body_pose(auger)
        sol = self.solve_grasp(T_a, r.q_ref, rises=(0.0, mm(sw["approach_mm"])), ignore=(auger,),
                               then_place=then_place)
        if sol is None:
            self._log(f"grasp {auger} in {where}", ok=False, why="no IK for a top-down grasp")
            return False
        T, qs, lean = sol
        T_up = T.copy()
        T_up[2, 3] += mm(sw["approach_mm"])
        r.set_gripper(width_m=2 * (self.tube_r + self.open_margin))
        if not self.transit(T_up, f"to {auger}"):
            return False
        r.move_linear(T, label=f"down to {auger}", ignore=(auger,))
        gap = r.grip(self.squeeze)
        self.held = [auger]
        self._grip_rel = inv(r.tcp_world()) @ self.e.body_pose(auger)
        self._log(f"grasp {auger} in {where}", ok=abs(gap - 2 * self.tube_r) < 0.003, gap_mm=gap * 1000,
                  lean_deg=float(np.degrees(lean)), squeeze_n=float(self.squeeze))
        return True

    def _rotate_about(self, pivot: np.ndarray, axis: np.ndarray, angle: float, steps: int, label: str, speed=0.02):
        """Move the TCP so the held auger turns by `angle` about a line through `pivot`."""
        r = self.robot
        T0 = r.tcp_world(r.q_ref)
        ok = True
        for k in range(1, steps + 1):
            R = axis_angle(axis, angle * k / steps)
            T = T0.copy()
            T[:3, :3] = R @ T0[:3, :3]
            T[:3, 3] = pivot + R @ (T0[:3, 3] - pivot)
            ok &= r.move_linear(T, speed, label=label, ignore=tuple(self.held))
        return ok

    def remove_from_doser(self, auger: str) -> bool:
        r, sw = self.robot, self.sw
        if not self.grasp(auger, "doser"):
            return False
        n0 = len(self.cell.snap.events)
        if sw.get("extract", "peel") == "peel":
            # Lift the cap end, turning the auger about the bottom edge of the outlet-side clip
            # (where the tube presses on the cradle): the back clip lets go first (the tube
            # levers it open), then the outlet-side clip is levered open across its 12 mm width.
            T_a = self.e.body_pose(auger)
            pivot, axis = self.pivot(auger, T_a)
            self._rotate_about(pivot, axis, deg(sw["peel_deg"]), max(4, int(sw["peel_deg"] / 4)),
                               "peel: lift the cap end")
        r.move_linear(self._raised(mm(sw["lift_mm"])), 0.03, label="lift out", ignore=tuple(self.held))
        slip_mm, slip_deg = self.held_in_grip(auger)
        free = not any(self.cell.snap.seated(self.e, auger, [c], tol_mm=3.0) for c in self.doser_clips)
        ev = self.cell.snap.events[n0:]
        self._log(f"remove {auger}", ok=free and slip_mm < 5, out_of_clips=free, slip_mm=slip_mm,
                  slip_deg=slip_deg, snaps=[(e["clip"], e["event"], e["peak_force_n"]) for e in ev])
        return free

    def pivot(self, auger, T_a):
        """Bottom edge (outlet side) of the doser clip nearest the outlet, and the horizontal
        axis across the tube there, signed so a positive turn lifts the cap end."""
        seats = {c: self.e.site_pose(f"{c}_seat") for c in self.doser_clips}
        s_of = {c: (T[:3, 3] - T_a[:3, 3]) @ T_a[:3, 2] for c, T in seats.items()}
        near = min(s_of, key=s_of.get)
        a = T_a[:3, 2]
        up = np.array([0, 0, 1.0]) - a * a[2]
        up /= np.linalg.norm(up)
        w = self.cell.geo["clip"]["width"] / 2000
        pivot = seats[near][:3, 3] - a * w - up * self.tube_r
        axis = np.cross(a, up)
        axis /= np.linalg.norm(axis)
        if (axis_angle(axis, 0.1) @ a)[2] < a[2]:
            axis = -axis
        return pivot, axis

    def _raised(self, dz):
        T = self.robot.tcp_world(self.robot.q_ref)
        T[2, 3] += dz
        return T

    def place(self, auger: str, T_target_auger: np.ndarray, where: str, clips: list[str], push: bool) -> bool:
        """Set the held auger down so its frame lands on T_target_auger, push it in if `push`,
        check it is seated, let go and back off."""
        r, sw = self.robot, self.sw
        # Where the TCP must be so the auger lands on the target, keeping the grip as it is now.
        # The tube is round, so the auger may land turned any way about its own axis: pick the
        # turn the arm can reach at the seat, just above it and at the carrying height.
        T_rel = inv(r.tcp_world()) @ self.e.body_pose(auger)
        hover = 0.024 if push else 0.006  # stop with the tube just above the lips / the cradle
        T_tcp = self.place_solution(T_rel, T_target_auger, hover, auger)
        if T_tcp is None:
            self._log(f"place {auger} in {where}", ok=False, why="no reachable way to set it down")
            return False
        T_hover = T_tcp.copy()
        T_hover[2, 3] += hover
        T_up = T_tcp.copy()
        T_up[2, 3] += mm(sw["clearance_mm"])
        if not self.transit(T_up, f"carry {auger} to {where}"):
            return False
        r.move_linear(T_hover, 0.04, label=f"lower onto {where}", ignore=(auger,))
        n0 = len(self.cell.snap.events)
        if push:
            # Impedance push: aim the TCP spring below the seat so it pushes with ~insert_force_n.
            kz = self.cfg.robot["control"]["cartesian_stiffness"][2]
            depth = sw["insert_force_n"] / kz
            T_push = T_tcp.copy()
            T_push[2, 3] -= depth
            t0 = self.e.time
            while self.e.time - t0 < 3.0:
                r.compliant(T_push, 0.1, label=f"push into {where}")
                if self.cell.snap.seated(self.e, auger, clips, sw["seated_tol_mm"]):
                    break
            r.compliant(T_tcp, 0.3, label="relax")
        else:
            r.move_linear(T_tcp, 0.02, label=f"set down in {where}", ignore=(auger,))
        seated = self.cell.snap.seated(self.e, auger, clips, sw["seated_tol_mm"] if push else 1.5)
        r.set_gripper(width_m=2 * (self.tube_r + self.open_margin))
        self.held = []
        r.move_linear(self._raised(mm(sw["approach_mm"])), 0.05, label="back off")
        seated_after = self.cell.snap.seated(self.e, auger, clips, sw["seated_tol_mm"] if push else 1.5)
        ev = self.cell.snap.events[n0:]
        self._log(f"place {auger} in {where}", ok=seated_after, seated_when_pushed=seated,
                  seated_after_release=seated_after,
                  snaps=[(e["clip"], e["event"], e["peak_force_n"]) for e in ev])
        return seated_after

    def place_solution(self, T_rel, T_target_auger, hover, auger, q_seed=None):
        """TCP pose that sets an auger held as T_rel (auger in the TCP frame) down on
        T_target_auger, turned about its own axis however the arm can reach (the tube is
        round), with IK at the carrying height, the hover height and the seat. None if none."""
        r, sw = self.robot, self.sw
        best = None
        for th in np.radians(np.arange(0, 360, 15)):
            T_t = T_target_auger @ make_pose(axis_angle([0, 0, 1.0], th))
            T_tcp = T_t @ inv(T_rel)
            if T_tcp[2, 2] > -0.2:  # tool pointing up or sideways: not a way to set it down
                continue
            qs, q = [], r.q_ref if q_seed is None else q_seed
            for dz in (mm(sw["clearance_mm"]), hover, 0.0):
                Tz = T_tcp.copy()
                Tz[2, 3] += dz
                q = r.ik_world(Tz, q, extra_seeds=6 if not qs else 0)
                if q is None or self._hits(q, (auger,)):
                    break
                qs.append(q)
            if len(qs) == 3:
                cost = float(np.arccos(np.clip(-T_tcp[2, 2], -1, 1)))  # prefer the tool pointing down
                if best is None or cost < best[0]:
                    best = (cost, T_tcp)
        return None if best is None else best[1]

    def gear_check(self, auger: str) -> dict:
        """Is the gear's face centred on the pinion's (axially), and at the right distance?"""
        T_d = self.cell.poses0["doser"]
        p_pin = T_d[:3, :3] @ np.asarray(self.cell.geo["stepper_pinion"]["center"]) + T_d[:3, 3]
        T_a = self.e.body_pose(auger)
        g = self.cell.geo["auger"]["gear"]
        s_gear = (g["z"][0] + g["z"][1]) / 2000
        p_gear = T_a[:3, 3] + T_a[:3, 2] * s_gear
        d = p_pin - p_gear
        axial = float(d @ T_a[:3, 2] * 1000)
        radial = float(np.linalg.norm(d - (d @ T_a[:3, 2]) * T_a[:3, 2]) * 1000)
        ok = abs(axial) <= self.sw["gear_axial_tol_mm"]
        out = {"axial_offset_mm": round(axial, 2), "centre_distance_mm": round(radial, 2), "meshes": ok}
        self._log(f"gear check {auger}", ok=ok, **out)
        return out

    # --- the job ------------------------------------------------------------------------------
    def run(self) -> bool:
        c, sw = self.cell, self.sw
        out = c.occupant.get("doser")
        new = sw["swap_in"]
        park = sw["park_slot"]
        new_slot = next(k for k in range(c.dcfg["rack"]["slots"]) if c.occupant.get(f"rack:{k}") == new)
        self.held = []
        ok = True
        r = self.robot
        q_ready = np.radians(self.cfg.robot["joints"]["ready_deg"])
        r.move_joints(q_ready, label="ready")
        if out:
            ok &= self.remove_from_doser(out)
            if ok:
                ok &= self.place(out, c.slot_world(park), f"rack slot {park}",
                                 [f"rack_s{park}_clip0", f"rack_s{park}_clip1"], push=c.dcfg["rack"].get("snap", False))
        if ok:
            ok &= self.grasp(new, f"rack slot {new_slot}", then_place=(c.doser_seat_world, 0.024))
            if ok:
                r.move_linear(self._raised(mm(sw["lift_mm"])), 0.04, label="lift from rack", ignore=(new,))
                ok &= self.place(new, c.doser_seat_world, "doser", self.doser_clips, push=True)
                self.gear_check(new)
        r.move_joints(q_ready, label="ready")
        self._log("done", ok=bool(ok))
        return bool(ok)
