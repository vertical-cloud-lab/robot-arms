"""Clearing the build plate: pick each print, free it from the plate, and drop it in the box
or set it on the black shelf.

For every print in prints.yaml, in order:

  1. locate it          the print's pose (from the engine, or from AprilTags: --perception)
  2. plan the grasp     top-down, fingers closing across `grasp.width` at `grasp.tip_z`; the
                        gripper is symmetric, so yaw and yaw + 180 deg are both tried, and the
                        tool may lean up to 30 deg if the wrist can't point straight down there
  3. approach           up and over at a safe height, open to width + 2 x 12 mm, go straight down
  4. grip               close until the sleeves meet the print, squeeze (robot_piper.yaml)
  5. free it            twist, rock, then pull (sim.yaml release_strategy) until the bond breaks
  6. lift and verify    straight up; check the print came with the gripper
  7. deliver            box: release above the rim and let it drop
                        shelf: set it down on solid land between the holes, 2 mm up, let go
  8. retreat            straight up, then on to the next print

Every step is logged in `self.report` (time, bond loads, whether the print was held, where it
ended up), which run_sim.py prints and saves as JSON.
"""
from __future__ import annotations

import numpy as np

from ..config import deg, mm
from ..transforms import axis_angle, make_pose


class PickPlace:
    def __init__(self, cell, robot, cfg, locator=None):
        self.cell, self.robot, self.cfg = cell, robot, cfg
        self.e = robot.engine
        self.task = cfg.sim["task"]
        self.locator = locator  # callable(print_name) -> world pose, or None for ground truth
        self.report: list[dict] = []
        self.shelf_used: list[tuple[np.ndarray, float]] = []
        self.box_count = 0
        poses = cell.poses0
        self.shelf_T = poses["shelf"]
        self.box_T = poses["box"]
        self.box_rim = self.box_T[2, 3] + cell.box.cfg["outer_size"][2] / 1000 - cell.box.cfg["floor"] / 1000
        g = cfg.robot["gripper"]
        self.max_gap = 2 * (g["finger_travel_mm"][1] - g["sleeve"]["thickness_mm"]) / 1000
        self.squeeze = g["default_force_n"]
        self.pad_half_width = g["sleeve"]["width_mm"] / 2000
        self.pad_half_gap = 0.02

    # --- geometry ----------------------------------------------------------------------------
    def print_pose(self, name):
        return self.locator(name) if self.locator else self.e.body_pose(name)

    def tool_pose(self, p, closing_dir, lean=0.0):
        """TCP pose at p with the fingers closing along closing_dir (horizontal) and the tool
        pointing down, leaned by `lean` rad so the wrist sits closer to the arm's base. The
        PiPER's wrist (J5 within +-70 deg) can't point straight down this low and this far out,
        so leaning 15-30 deg is normal. The TCP is raised so the lowest fingertip corner stays
        where it would be without the lean."""
        base_xy = self.cell.arm_pose[:2, 3]
        u = np.append(p[:2] - base_xy, 0.0)
        u /= np.linalg.norm(u)  # radial, away from the arm
        z = np.array([0, 0, -np.cos(lean)]) + u * np.sin(lean)
        d = np.asarray(closing_dir, float)
        y = d - (d @ z) * z
        y /= np.linalg.norm(y)
        x = np.cross(y, z)
        half_w = self.pad_half_width
        rise = half_w * abs(x[2]) + self.pad_half_gap * abs(y[2])
        return make_pose(np.column_stack([x, y, z]), p + np.array([0, 0, rise]))

    def closing_options(self, pr, T_print):
        """Closing directions (world, horizontal) the print allows, most useful first: across
        the arm's reach, so the lean tips the fingers along their length, not across."""
        g = pr.cfg["grasp"]
        yaw0 = deg(g.get("yaw", 0))
        sym = g.get("symmetry")
        if sym is None:
            yaws = [yaw0]
        elif sym == 0:
            yaws = yaw0 + deg(np.arange(0, 180, 15))
        else:
            yaws = yaw0 + deg(np.arange(0, 180, sym))
        base_xy = self.cell.arm_pose[:2, 3]
        u = T_print[:2, 3] - base_xy
        u /= np.linalg.norm(u)
        out = []
        for a in yaws:
            d = T_print[:3, :3] @ np.array([np.cos(a), np.sin(a), 0.0])
            d[2] = 0
            d /= np.linalg.norm(d)
            out.append((abs(d[:2] @ u), d))
        return [d for _, d in sorted(out, key=lambda t: t[0])]

    def solve_grasp(self, p, closings, q_seed, rise=0.0):
        """Smallest lean (and best of yaw / yaw + 180) with IK solutions at p and p + rise.
        Returns (T, q, T_up, q_up) or None."""
        for lean in deg([0, 10, 15, 20, 25, 30, 35, 40, 45]):
            best = None
            for d in closings[:3]:
                for flip in (1, -1):
                    T = self.tool_pose(p, flip * d, lean)
                    q = self.robot.ik_world(T, q_seed, extra_seeds=2)
                    if q is None:
                        continue
                    T_up = T.copy()
                    T_up[2, 3] += rise
                    q_up = self.robot.ik_world(T_up, q, extra_seeds=0) if rise else q
                    if q_up is None:
                        continue
                    cost = float(np.sum((q_up - q_seed) ** 2))
                    if best is None or cost < best[0]:
                        best = (cost, T, q, T_up, q_up)
            if best is not None:
                return best[1:]
        return None

    # --- moves -------------------------------------------------------------------------------
    def transit(self, T_goal_up, q_goal_up, label, ignore=()):
        """Rise straight up to a safe height, swing over in joint space, and arrive above."""
        r = self.robot
        T_now = r.tcp_world(r.q_ref)
        clear = mm(self.task["transfer_clearance_mm"])
        z_safe = max(T_now[2, 3], T_goal_up[2, 3], self.cell.plate_pose[2, 3] + clear)
        if T_now[2, 3] < z_safe - 1e-3:
            T_rise = T_now.copy()
            T_rise[2, 3] = z_safe
            if not r.move_linear(T_rise, speed=0.12, label=f"{label}: rise", ignore=ignore):
                q_rise = r.ik_world(T_rise, r.q_ref)
                if q_rise is not None:
                    r.move_joints(q_rise, label=f"{label}: rise (joint)", ignore=ignore)
        T_over = T_goal_up.copy()
        T_over[2, 3] = z_safe
        q_over = r.ik_world(T_over, q_goal_up)
        if q_over is not None and z_safe > T_goal_up[2, 3] + 1e-3:
            r.move_joints(q_over, label=f"{label}: over", ignore=ignore)
            r.move_linear(T_goal_up, speed=0.12, label=f"{label}: down to approach", ignore=ignore)
        else:
            r.move_joints(q_goal_up, label=f"{label}: over", ignore=ignore)

    # --- the task ----------------------------------------------------------------------------
    def run(self, names=None):
        queue = [p for p in self.cell.prints if names is None or p.name in names]
        waits = {}
        while queue:
            pr = queue.pop(0)
            rec = self.pick_and_place(pr)
            if rec["result"] == "waiting" and waits.get(pr.name, 0) < len(queue):
                waits[pr.name] = waits.get(pr.name, 0) + 1
                print(f"  {pr.name:18s} later      ({rec['note']})", flush=True)
                queue.append(pr)
                continue
            if rec["result"] == "waiting":
                rec["result"] = "blocked"
            self.report.append(rec)
            print(f"  {pr.name:18s} {rec['result']:10s} t={rec['t_end']:6.1f}s  {rec.get('note', '')}", flush=True)
        q_ready = deg(self.cfg.robot["joints"]["ready_deg"])
        self.transit(self.robot.tcp_world(q_ready), q_ready, "finish")
        return self.report

    def pick_and_place(self, pr):
        r, e = self.robot, self.e
        g = pr.cfg["grasp"]
        rec = {"print": pr.name, "destination": pr.cfg.get("destination", "box"), "t_start": e.time,
               "mass_g": round(pr.mass_kg * 1000, 1), "bond": pr.capacity.summary()}
        T_print = self.print_pose(pr.name)
        tip_z = mm(g["tip_z"])
        xy = mm(g.get("xy", [0, 0]))
        p = (T_print @ np.array([xy[0], xy[1], tip_z, 1.0]))[:3]
        open_gap = min(mm(g["width"]) + 0.024, self.max_gap)
        self.pad_half_gap = open_gap / 2
        approach = mm(self.task["approach_height_mm"])
        # Try each way the print can be held; keep the first whose approach and grasp poses
        # are reachable and clear of the cell and the other prints.
        sol, hits = None, []
        for d in self.closing_options(pr, T_print)[:4]:
            cand = self.solve_grasp(p, [d], r.q_ref, rise=approach)
            if cand is None:
                continue
            h = [x for q in (cand[1], cand[3]) for x in e.arm_collisions(q, open_gap / 2 + r.sleeve_t, (pr.name,))]
            if not h:
                sol, hits = cand, []
                break
            if sol is None:
                sol, hits = cand, h
        if sol is None:
            rec.update(result="unreachable", t_end=e.time, note="no IK for the grasp")
            return rec
        T_grasp, q_grasp, T_pre, q_pre = sol
        if hits:
            others = sorted({h[1] for h in hits})
            prints = {p.name for p in self.cell.prints}
            in_way = sorted({o.split("/")[0] for o in others if o.split("/")[0] in prints})
            if all(o.split("/")[0] in prints for o in others):  # only other prints in the way
                rec.update(result="waiting", t_end=e.time, note="fingers would hit " + ", ".join(in_way))
            else:
                rec.update(result="blocked", t_end=e.time, note="the arm would hit " + ", ".join(others))
            return rec
        rec["lean_deg"] = round(float(np.degrees(np.arccos(np.clip(-T_grasp[2, 2], -1, 1)))), 1)
        # 3. approach
        self.transit(T_pre, q_pre, f"{pr.name}: approach")
        r.set_gripper(width_m=open_gap)
        r.move_linear(T_grasp, label=f"{pr.name}: descend", ignore=(pr.name,))
        # 4. grip
        gap = r.grip(self.squeeze)
        rec["gap_mm"] = round(gap * 1000, 1)
        if gap < 0.3 * mm(g["width"]):
            rec["note"] = "gripper closed on nothing"
        # 5. free it
        how = self.release(pr, T_grasp)
        rec["freed_by"] = how
        # 6. lift and check
        T_lift = T_grasp.copy()
        T_lift[2, 3] += mm(self.task["lift_height_mm"])
        r.move_linear(T_lift, label=f"{pr.name}: lift", ignore=(pr.name,))
        if how is None and e.bonded(pr.name):
            rec.update(result="stuck", t_end=e.time, note="bond held through the lift")
            r.set_gripper(width_m=open_gap)
            r.move_linear(T_lift, label=f"{pr.name}: back off")
            return rec
        if how is None:
            rec["freed_by"] = "pull (lift)"
        held = self.held(pr)
        rec["held_after_lift"] = held
        if not held:
            rec.update(result="dropped", t_end=e.time, note="print not in the gripper after the lift")
            r.set_gripper(width_m=open_gap)
            return rec
        # 7. deliver
        if rec["destination"] == "shelf":
            ok = self.place_on_shelf(pr, tip_z, rec)
        else:
            ok = self.drop_in_box(pr, tip_z, rec)
        rec["final_pose_mm"] = (e.body_pose(pr.name)[:3, 3] * 1000).round(1).tolist()
        rec["result"] = rec.get("result") or ("done" if ok else "failed")
        rec["t_end"] = e.time
        return rec

    def release(self, pr, T_grasp):
        """Wiggle the print free of the plate. Returns the action that broke the bond, or None."""
        r, e = self.robot, self.e
        if not e.bonded(pr.name):
            return "squeeze (it let go while gripping)"
        for attempt in range(1, int(self.task["max_release_attempts"]) + 1):
            for how in self.task["release_strategy"]:
                if how == "twist":
                    a = deg(self.task["twist_deg"]) * attempt
                    seq = [axis_angle([0, 0, 1], s * a) for s in (1, -1, 0)]
                    pivot = T_grasp[:3, 3]
                elif how == "rock":
                    a = deg(self.task["rock_deg"]) * attempt
                    seq = [axis_angle(T_grasp[:3, 0], s * a) for s in (1, -1, 0)]
                    pivot = T_grasp[:3, 3]
                elif how == "pull":
                    T_up = T_grasp.copy()
                    T_up[2, 3] += 0.002 * attempt
                    r.move_linear(T_up, speed=0.01, label=f"{pr.name}: pull", ignore=(pr.name,))
                    if not e.bonded(pr.name):
                        return "pull"
                    r.move_linear(T_grasp, speed=0.01, label=f"{pr.name}: ease back", ignore=(pr.name,))
                    continue
                else:
                    raise ValueError(f"unknown release strategy {how!r}")
                for Rk in seq:
                    T = T_grasp.copy()
                    T[:3, :3] = Rk @ T_grasp[:3, :3]
                    T[:3, 3] = pivot
                    r.move_linear(T, speed=0.02, label=f"{pr.name}: {how}", ignore=(pr.name,))
                    if not e.bonded(pr.name):
                        r.move_linear(T_grasp, speed=0.02, label=f"{pr.name}: square up", ignore=(pr.name,))
                        return how
        return None

    def held(self, pr) -> bool:
        """Is the print between the fingers? Its grasp point must be within 15 mm of the TCP."""
        T = self.e.body_pose(pr.name)
        g = pr.cfg["grasp"]
        xy = mm(g.get("xy", [0, 0]))
        p = (T @ np.array([xy[0], xy[1], mm(g["tip_z"]), 1.0]))[:3]
        return bool(np.linalg.norm(p - self.robot.tcp_world()[:3, 3]) < 0.015)

    def carry_pose(self, pr, spot, q_seed, rise=0.0):
        """Tool poses that put the held print upright with its footprint centre at `spot`
        (world), from where it actually sits in the gripper now (it may have shifted while
        breaking free). Tries yaws of the print about the vertical and keeps the reachable one
        closest to the current joints. Returns (T, q, T_up, q_up) or None."""
        T_tool_print = np.linalg.inv(self.robot.tcp_world()) @ self.e.body_pose(pr.name)
        T_print_tool = np.linalg.inv(T_tool_print)
        best = None
        for psi in deg(np.arange(0, 360, 20)):
            T_print = make_pose(axis_angle([0, 0, 1], psi), spot)
            T = T_print @ T_print_tool
            q = self.robot.ik_world(T, q_seed, extra_seeds=1)
            if q is None:
                continue
            T_up = T.copy()
            T_up[2, 3] += rise
            q_up = self.robot.ik_world(T_up, q, extra_seeds=0) if rise else q
            if q_up is None:
                continue
            cost = float(np.sum((q_up - q_seed) ** 2))
            if best is None or cost < best[0]:
                best = (cost, T, q, T_up, q_up)
        return None if best is None else best[1:]

    def drop_in_box(self, pr, tip_z, rec):
        r = self.robot
        k = self.box_count
        self.box_count += 1
        inner = np.asarray(self.cell.box.cfg["outer_size"][:2]) / 1000 - 0.05
        offs = [(0, 0), (-0.25, -0.2), (0.25, 0.2), (-0.25, 0.2), (0.25, -0.2)][k % 5]
        c = self.box_T @ np.array([offs[0] * inner[0], offs[1] * inner[1], 0, 1.0])
        spot = np.array([c[0], c[1], self.box_rim + mm(self.task["box_release_above_rim_mm"])])
        sol = self.carry_pose(pr, spot, r.q_ref)
        if sol is None:
            rec["note"] = "box drop point unreachable"
            return False
        T_rel, q_rel = sol[0], sol[1]
        self.transit(T_rel, q_rel, f"{pr.name}: to box", ignore=(pr.name,))
        r.set_gripper(width_m=min(r.gap() + 0.025, self.max_gap))
        r.wait(self.task["release_settle_s"] + 0.6)  # let go, let it land
        inside = self.in_box(pr)
        rec["in_box"] = inside
        T_up = r.tcp_world(r.q_ref)
        T_up[2, 3] += 0.05
        r.move_linear(T_up, speed=0.1, label=f"{pr.name}: retreat", ignore=(pr.name,))
        return inside

    def in_box(self, pr) -> bool:
        p = np.linalg.inv(self.box_T) @ np.append(self.e.body_pose(pr.name)[:3, 3], 1)
        X, Y = np.asarray(self.cell.box.cfg["outer_size"][:2]) / 2000
        return bool(abs(p[0]) < X and abs(p[1]) < Y and p[2] < self.box_rim - self.box_T[2, 3])

    def shelf_spot(self, pr, q_seed):
        """Nearest free land between holes (to the arm) where the arm can set the print down."""
        rad = pr.footprint_radius_mm() / 1000
        arm_xy = self.cell.arm_pose[:2, 3]
        cands = []
        for (x, y) in self.cell.shelf.spots(rad * 1000):
            w = self.shelf_T @ np.array([x / 1000, y / 1000, 0, 1.0])
            if any(np.linalg.norm(w[:2] - u) < rad + ru + 0.008 for u, ru in self.shelf_used):
                continue
            cands.append((np.linalg.norm(w[:2] - arm_xy), w[:3]))
        top = self.shelf_T[2, 3]
        for _, w in sorted(cands, key=lambda c: c[0])[:12]:
            spot = np.array([w[0], w[1], top + mm(self.task["shelf_release_gap_mm"])])
            sol = self.carry_pose(pr, spot, q_seed, rise=mm(self.task["approach_height_mm"]))
            if sol is not None:
                return w, rad, sol
        return None

    def place_on_shelf(self, pr, tip_z, rec):
        r = self.robot
        found = self.shelf_spot(pr, r.q_ref)
        if found is None:
            rec["note"] = "no free shelf spot in reach"
            return False
        w, rad, (T_place, q_place, T_above, q_above) = found
        self.transit(T_above, q_above, f"{pr.name}: to shelf", ignore=(pr.name,))
        r.move_linear(T_place, label=f"{pr.name}: set down", ignore=(pr.name,))
        r.set_gripper(width_m=min(r.gap() + 0.02, self.max_gap))
        r.wait(self.task["release_settle_s"])
        r.move_linear(T_above, speed=0.08, label=f"{pr.name}: retreat", ignore=(pr.name,))
        self.shelf_used.append((w[:2], rad))
        r.wait(0.3)
        T = self.e.body_pose(pr.name)
        rec["shelf_tilt_deg"] = round(float(np.degrees(np.arccos(np.clip(T[2, 2], -1, 1)))), 1)
        rec["on_shelf"] = bool(abs(T[2, 3] - self.shelf_T[2, 3]) < 0.01)
        return rec["on_shelf"]
