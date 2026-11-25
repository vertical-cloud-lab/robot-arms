#!/usr/bin/env python3
"""Powder-Doser Workflow 1: pick the auger out of its holder, place it in a box, and grade the
run. Repeat for 30 runs at each of 3 box spots to measure repeatability and accuracy (PR #83).

    python auger_test.py --dry-run --spot 1 --runs 3 --go --yes   # simulated arm and camera
    ~/piper-venv/bin/python auger_test.py --spot 1                 # on mpzy: look and plan only
    ~/piper-venv/bin/python ~/arm_power.py run -- \\
        ~/piper-venv/bin/python auger_test.py --spot 1 --runs 30 --go

Without --go nothing moves: it looks, plans, prints the plan and saves results/plan.jpg.
For the first runs on the real arm, --until above (stop over the auger) and --until grasp
(close on it and let go, no pull) check the setup one step at a time.

One run:
  1. LOOK   a still from mpzy's camera; find the holder and the box by their AprilTags.
  2. PLAN   every pose and path, checked before the arm moves: reach, J1's range, J6's 90 deg
            window, the keep-out boxes (the A1 mini) and the table.
  3. PICK   above the auger, open, straight down, close, check the fingers stopped on the
            tube, pull straight up out of the clips (slowly), check it is still held.
  4. PLACE  carry it over the box at a safe height, straight down, open, straight up, READY.
  5. GRADE  a suggested grade from what happened; the operator confirms or changes it.
  6. LOG    a row in results/results.csv, and the before and after stills.

Grades (PR #83):
  A  found, picked up out of the holder and placed in the box
  B  found and picked up, but not placed in the box
  C  found, but not picked up
  D  not found (the holder's tags weren't seen, or the gripper closed on nothing)
  F  the test failed completely (no safe plan, an arm fault, ...)
"""
import argparse
import csv
import datetime as dt
import math
import os
import sys
import time

import arm as A
import kinematics as K
import settings as S
import vision as V

HERE = os.path.dirname(os.path.abspath(__file__))
TUBE_READING = S.GRIPPER_CLOSED_READING_MM + S.AUGER_TUBE_DIAMETER_MM
FIELDS = ["time_utc", "session", "spot", "run", "grade", "suggested", "why", "note",
          "holder_x", "holder_y", "holder_z", "holder_yaw", "holder_fit_px",
          "box_x", "box_y", "box_z", "box_yaw", "box_fit_px",
          "grip_closed_mm", "grip_after_pull_mm", "grip_before_release_mm",
          "auger_in_box_x", "auger_in_box_y", "auger_in_box_yaw", "seconds",
          "image_before", "image_after"]


class PlanError(Exception):
    """No safe way to do this run; the message says why. Nothing has moved."""


# ---------------------------------------------------------------- 1. LOOK
class Eyes:
    """The camera (or, with --dry-run, the simulated cell's) and what it last saw."""

    def __init__(self, args, sim=None):
        self.sim, self.args = sim, args
        if sim:
            self.camera = sim.camera
        else:
            self.camera = V.Camera.load()
            if self.camera is None and args.go:
                raise SystemExit(f"no {S.CALIBRATION_FILE}: run calibrate.py first (README)")
            if self.camera is None:
                print(f"WARNING: no {S.CALIBRATION_FILE} yet, so positions are settings.py's "
                      "rough guess of the camera: fine for checking the tags are seen, not for "
                      "moving", flush=True)
                self.camera = V.Camera.nominal()
        self.known_z = {}  # each object's height from its last look with 2+ tags

    def look(self, name):
        """(holder, box, detections, image): where the holder and the box are (None if not
        seen), from a new still. A 1600 px copy with the tags marked is kept as
        results/images/<name>.jpg (the full 12 MP still would fill the Pi's card)."""
        path = os.path.join(self.args.results, "images", f"{name}.jpg")
        os.makedirs(os.path.dirname(path), exist_ok=True)
        image = self.sim.capture() if self.sim else V.capture("/tmp/powder_doser_w1_still.jpg")
        det = V.detect(image)
        V.annotate(image, det, self.camera, path=path)
        found = {}
        for key, tags, size in (("holder", S.HOLDER_TAGS, S.HOLDER_TAG_SIZE_MM),
                                ("box", S.BOX_TAGS, S.BOX_TAG_SIZE_MM)):
            f = V.locate(det, tags, size, self.camera, self.known_z.get(key))
            if f is not None and len(f.tags) >= 2:
                self.known_z[key] = f.z
            found[key] = f
        return found["holder"], found["box"], det, image

    def auger_in_box(self, det, box):
        """Where the auger's own tag (settings.AUGER_TAG) is in the box frame: (x, y, yaw) of
        the auger's middle and direction, or None if there's no auger tag or it wasn't seen."""
        if not S.AUGER_TAG or S.AUGER_TAG["id"] not in det or box is None:
            return None
        tag = {S.AUGER_TAG["id"]: S.AUGER_TAG["pos"]}
        z = box.z + S.AUGER_GEAR_DIAMETER_MM / 2  # lying on the box's floor
        f = V.locate(det, tag, S.AUGER_TAG["size_mm"], self.camera, z)
        if f is None:
            return None
        c, s = math.cos(math.radians(box.yaw)), math.sin(math.radians(box.yaw))
        dx, dy = f.x - box.x, f.y - box.y
        return c * dx + s * dy, -s * dx + c * dy, K.wrap90(f.yaw - box.yaw)


# ---------------------------------------------------------------- 2. PLAN
class Plan:
    """Every pose and path of one run, worked out and checked before anything moves."""

    def __init__(self, holder, box, ready):
        up = [0.0, 0.0, 1.0]
        # The pick: the fingers close across the auger, at GRASP_OFFSET_MM from its middle.
        self.grasp = holder.to_arm((S.GRASP_OFFSET_MM, 0.0, 0.0))
        self.pick_yaw = K.wrap90(holder.yaw + 90.0)
        # Carry height: the auger's lowest point (its gear) CARRY_CLEARANCE_MM above the
        # clips' tops and the box's rim.
        top = max(self.grasp[2] + S.HOLDER_CLIP_TOP_ABOVE_AXIS_MM,
                  box.z + S.BOX_WALL_HEIGHT_MM)
        self.carry_z = top + S.CARRY_CLEARANCE_MM + S.AUGER_GEAR_DIAMETER_MM / 2
        above_grasp = K.add(self.grasp, up, S.APPROACH_MM)
        pulled = K.add(self.grasp, up, S.PULL_MM)
        carry_pick = [self.grasp[0], self.grasp[1], max(self.carry_z, above_grasp[2])]
        try:
            q = K.ik(carry_pick, self.pick_yaw)
            self.to_pick = K.joint_line(ready, q)
            self.down_fast = K.line(q, carry_pick, above_grasp, self.pick_yaw, self.pick_yaw)
            self.down_slow = K.line(self.down_fast[-1], above_grasp, self.grasp, self.pick_yaw,
                                    self.pick_yaw)
            q_grasp = self.down_slow[-1]
            self.pull = K.line(q_grasp, self.grasp, pulled, self.pick_yaw, self.pick_yaw)
            self.lift = K.line(self.pull[-1], pulled, carry_pick, self.pick_yaw, self.pick_yaw)
        except K.IKError as e:
            raise PlanError(f"the pick: {e}")
        # What the gripper holds: the auger's axis in the flange frame (toward its gear end).
        R, _ = K.tool(q_grasp)
        axis = holder.axis()
        self.carried = ([sum(R[i][k] * axis[i] for i in range(3)) for k in range(3)],
                        S.GRASP_OFFSET_MM)
        # The place: the auger's middle over the box's middle, along the box, its gear
        # RELEASE_HEIGHT_MM above the floor. The fingers close across the box.
        self.place_yaw = K.wrap90(box.yaw + 90.0)
        middle = box.to_arm((0.0, 0.0, S.RELEASE_HEIGHT_MM + S.AUGER_GEAR_DIAMETER_MM / 2))
        try:
            self.release = list(middle)
            for _ in range(3):  # the TCP holds the auger GRASP_OFFSET_MM from its middle
                q = K.ik(self.release, self.place_yaw, q)
                d = self.auger_axis(q)
                self.release = K.add(middle, d, S.GRASP_OFFSET_MM)
            q_release = K.ik(self.release, self.place_yaw, q)
            if abs(K.dot(self.auger_axis(q_release), box.axis())) < math.cos(math.radians(5)):
                raise PlanError("the auger wouldn't line up with the box")
            above_box = K.add(self.release, up, S.APPROACH_MM)
            carry_box = [self.release[0], self.release[1], max(self.carry_z, above_box[2])]
            self.swing = K.swing(self.lift[-1], carry_pick, carry_box, self.pick_yaw,
                                 self.place_yaw)
            self.lower_fast = K.line(self.swing[-1], carry_box, above_box, self.place_yaw,
                                     self.place_yaw)
            self.lower_slow = K.line(self.lower_fast[-1], above_box, self.release,
                                     self.place_yaw, self.place_yaw)
            self.rise = K.line(self.lower_slow[-1], self.release, carry_box, self.place_yaw,
                               self.place_yaw)
            self.to_ready = K.joint_line(self.rise[-1], ready)
        except K.IKError as e:
            raise PlanError(f"the place: {e}")
        # Check every path: the table, the keep-out boxes, J1's range, J6's window.
        try:
            for name, path, carrying in (
                    ("READY to above the auger", self.to_pick, None),
                    ("down to the auger", self.down_fast + self.down_slow, None),
                    ("pulling the auger out", self.pull, self.carried),
                    ("lifting it", self.lift, self.carried),
                    ("carrying it to the box", self.swing, self.carried),
                    ("lowering it into the box", self.lower_fast + self.lower_slow, self.carried),
                    ("rising from the box", self.rise, None),
                    ("back to READY", self.to_ready, None)):
                K.check_path(path, name, carrying, every=2)
        except K.IKError as e:
            raise PlanError(str(e))
        # The open fingers must fit inside the box if they go below its rim.
        tips_z = self.release[2] - (S.FINGERTIP_MM - S.TCP_MM)
        width = S.AUGER_TUBE_DIAMETER_MM + S.OPEN_FOR_RELEASE_MM + 2 * S.FINGER_THICKNESS_MM
        if tips_z < box.z + S.BOX_WALL_HEIGHT_MM and width > S.BOX_INSIDE_MM[1]:
            raise PlanError(f"the open fingers ({width:.0f} mm across) won't fit in the box "
                            f"({S.BOX_INSIDE_MM[1]:.0f} mm inside): lower OPEN_FOR_RELEASE_MM")
        self.ready = ready

    def auger_axis(self, q):
        R, _ = K.tool(q)
        return [K.dot(R[i], self.carried[0]) for i in range(3)]

    def summary(self):
        q_grasp, q_rel = self.down_slow[-1], self.lower_slow[-1]
        return "\n".join([
            f"  grasp   TCP ({self.grasp[0]:.0f}, {self.grasp[1]:.0f}, {self.grasp[2]:.0f}) mm, "
            f"J1 {q_grasp[0]:.1f}, J5 {q_grasp[4]:.1f}, J6 {q_grasp[5]:.1f}",
            f"  release TCP ({self.release[0]:.0f}, {self.release[1]:.0f}, "
            f"{self.release[2]:.0f}) mm, J1 {q_rel[0]:.1f}, J5 {q_rel[4]:.1f}, J6 {q_rel[5]:.1f}",
            f"  carried {self.carry_z:.0f} mm up (TCP)"])


# ---------------------------------------------------------------- 3-4. PICK and PLACE
def moved(arm, result, rec, step):
    """True if a move finished; else record why it stopped and return False."""
    if result is None:
        return True
    kind, why = result
    rec["why"] = f"{step}: {why}"
    if kind == "fault":
        rec["fault"] = True
    return False


def back_up(arm, rec):
    """After a failed pick or place, or a stop: open the gripper, go straight up, then back to
    READY. Both moves are checked first; if either isn't safe, or one stops, it records a
    fault and the arm stays holding. True once at READY."""
    q = arm.joints()
    p = K.tcp(q)
    up = None
    try:  # straight up, if the arm is in one of this script's poses (else it can't be lined up)
        path = K.line(q, p, [p[0], p[1], p[2] + S.APPROACH_MM], K.finger_yaw(q), K.finger_yaw(q))
        if max(abs(a - b) for a, b in zip(path[0], q)) < 2.0:
            K.check_path(path, "going straight up")
            up = path
    except K.IKError:
        pass
    top = up[-1] if up else q
    try:
        if up is None and p[2] < 120:
            raise K.IKError("the gripper is low and not in a pose this script can go straight "
                            "up from")
        K.check_path(K.joint_line(top, arm.ready), "back to READY")
    except K.IKError as e:
        rec["fault"], rec["why"] = True, rec.get("why", "") + f"; not backing up: {e}"
        return False
    arm.gripper_to(TUBE_READING + S.OPEN_FOR_RELEASE_MM)
    for path, label in ((up, "straight up"), ([top, arm.ready], "back to READY")):
        result = arm.follow(path, label) if path else None
        if result:
            rec["fault"], rec["why"] = True, rec.get("why", "") + f"; then {result[1]}"
            return False
    return True


def pick(arm, plan, rec, args):
    """Step 3: True if the auger came out of the holder in the gripper. With --until above or
    --until grasp it stops early (rec["practice"]), and the caller backs it up to READY."""
    if not moved(arm, arm.follow(plan.to_pick, "above the auger"), rec, "going to the auger"):
        return False
    arm.gripper_to(TUBE_READING + S.OPEN_FOR_GRASP_MM)
    if args.until == "above":
        ask("Above the auger, gripper open. Check the fingers are lined up to close across the "
            "tube, one each side. Enter = back to READY: ", args)
        rec["practice"], rec["why"] = True, "stopped above the auger (--until above)"
        return False
    for path, label, speed in ((plan.down_fast, "down", S.MOVE_MM_S),
                               (plan.down_slow, "down to the auger", S.APPROACH_MM_S)):
        if not moved(arm, arm.follow(path, label, speed), rec, label):
            return False
    rec["grip_closed_mm"] = w = arm.gripper_to(TUBE_READING - S.GRIP_SQUEEZE_MM)
    if w < TUBE_READING - S.GRIP_TOLERANCE_MM:
        rec["closed_on_nothing"] = True
        rec["why"] = f"the gripper closed on nothing ({w:.1f} mm): no auger where it was seen"
        return False
    if w > TUBE_READING + S.GRIP_TOLERANCE_MM:
        rec["why"] = f"the fingers stopped at {w:.1f} mm, not on the tube ({TUBE_READING:.1f})"
        return False
    rec["closed_on_auger"] = True
    if args.until == "grasp":
        rec["practice"], rec["why"] = True, f"closed on the tube at {w:.1f} mm (expected " \
            f"{TUBE_READING:.1f}), then let go (--until grasp)"
        return False
    if not moved(arm, arm.follow(plan.pull, "pull out of the clips", S.PULL_MM_S,
                                 S.PULL_MAX_CURRENT_A), rec, "pulling out of the clips"):
        return False
    time.sleep(0.3)  # let the gripper's reading settle
    rec["grip_after_pull_mm"] = w = arm.gripper_mm()
    if abs(w - TUBE_READING) > S.GRIP_TOLERANCE_MM:
        rec["why"] = f"lost the auger while pulling (gripper {w:.1f} mm)"
        return False
    return True


def place(arm, plan, rec):
    """Step 4: True if the auger was carried to the box and let go there."""
    for path, label, speed in ((plan.lift, "lift", S.MOVE_MM_S),
                               (plan.swing, "carry to the box", S.MOVE_MM_S),
                               (plan.lower_fast, "lower", S.MOVE_MM_S),
                               (plan.lower_slow, "lower into the box", S.APPROACH_MM_S)):
        if not moved(arm, arm.follow(path, label, speed), rec, label):
            return False
        w = arm.gripper_mm()
        if abs(w - TUBE_READING) > S.GRIP_TOLERANCE_MM:
            rec["why"] = f"dropped the auger during '{label}' (gripper {w:.1f} mm)"
            return False
    rec["grip_before_release_mm"] = arm.gripper_mm()
    arm.gripper_to(TUBE_READING + S.OPEN_FOR_RELEASE_MM)
    rec["released"] = True
    for path, label in ((plan.rise, "rise from the box"), (plan.to_ready, "to READY")):
        if not moved(arm, arm.follow(path, label), rec, label):
            rec["stop_after"] = True  # let go in the box, but stuck on the way back
            return True
    rec["at_ready"] = True
    return True


# ---------------------------------------------------------------- 5. GRADE
def suggest(rec):
    """(grade, reason) from what happened in the run."""
    if rec.get("fault") and not rec.get("released"):
        return "F", rec.get("why", "fault")
    if not rec.get("found"):
        return "D", rec.get("why", "not found")
    if rec.get("closed_on_nothing"):
        return "D", rec["why"]
    if not rec.get("picked"):
        return "C", rec.get("why", "not picked up")
    if not rec.get("released"):
        return "B", rec.get("why", "not placed")
    where = rec.get("auger_in_box")
    if where is not None:
        x, y, _ = where
        if abs(x) > (S.BOX_INSIDE_MM[0] - S.AUGER_LENGTH_MM) / 2 + 3 or \
                abs(y) > (S.BOX_INSIDE_MM[1] - S.AUGER_GEAR_DIAMETER_MM) / 2 + 3:
            return "B", f"the auger's tag says it lies {x:+.0f}, {y:+.0f} mm off the box's middle"
    return "A", "picked up and let go over the box" + (
        "" if where is None else f", lying {where[0]:+.1f}, {where[1]:+.1f} mm off its middle")


def ask(prompt, args, default=""):
    if args.yes:
        print(prompt + (f"{default}  (--yes)" if default else "(--yes)"), flush=True)
        return default
    try:
        return input(prompt).strip()
    except EOFError:
        return "q"


def grade(rec, args):
    g, why = suggest(rec)
    rec["suggested"], rec["why"] = g, why
    answer = ask(f"run {rec['run']}: suggested {g} ({why}).\n  Enter = {g}, or type "
                 "A/B/C/D/F and an optional note: ", args, "")
    letter = answer[:1].upper()
    rec["grade"] = letter if letter in "ABCDF" and letter else g
    rec["note"] = answer[1:].strip() if letter in "ABCDF" and letter else answer
    return rec["grade"]


# ---------------------------------------------------------------- 6. LOG
def log(rec, args):
    path = os.path.join(args.results, "results.csv")
    new = not os.path.exists(path)
    row = {k: rec.get(k, "") for k in FIELDS}
    for key, obj in (("holder", rec.get("holder_found")), ("box", rec.get("box_found"))):
        if obj is not None:
            row.update({f"{key}_x": f"{obj.x:.2f}", f"{key}_y": f"{obj.y:.2f}",
                        f"{key}_z": f"{obj.z:.2f}", f"{key}_yaw": f"{obj.yaw:.2f}",
                        f"{key}_fit_px": f"{obj.fit_px:.2f}"})
    if rec.get("auger_in_box"):
        row.update(dict(zip(("auger_in_box_x", "auger_in_box_y", "auger_in_box_yaw"),
                            (f"{v:.2f}" for v in rec["auger_in_box"]))))
    for k in ("grip_closed_mm", "grip_after_pull_mm", "grip_before_release_mm", "seconds"):
        if isinstance(row[k], float):
            row[k] = f"{row[k]:.2f}"
    with open(path, "a", newline="") as f:
        w = csv.DictWriter(f, FIELDS)
        if new:
            w.writeheader()
        w.writerow(row)


def next_run_number(args):
    path = os.path.join(args.results, "results.csv")
    if not os.path.exists(path):
        return 1
    with open(path, newline="") as f:
        runs = [int(r["run"]) for r in csv.DictReader(f) if r["spot"] == args.spot]
    return max(runs, default=0) + 1


# ---------------------------------------------------------------- one run, and the session
def one_run(arm, eyes, n, args, session):
    t0 = time.time()
    rec = {"time_utc": dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
           "session": session, "spot": args.spot, "run": n}
    name = f"spot{args.spot}_run{n:02d}"
    holder, box, det, _ = eyes.look(name + "_before")
    rec.update(holder_found=holder, box_found=box, image_before=f"images/{name}_before.jpg")
    rec["at_ready"] = True  # until the arm moves
    if holder is None:
        rec["why"] = f"the holder's tags weren't seen (saw tags {sorted(det)})"
    elif box is None:
        rec["found"] = True
        rec["fault"], rec["why"] = True, f"the box's tags weren't seen (saw tags {sorted(det)})"
    else:
        rec["found"] = True
        warn_if_moved(holder, box, args)
        try:
            plan = Plan(holder, box, arm.ready)
        except PlanError as e:
            rec["fault"], rec["why"] = True, f"no safe plan: {e}"
            plan = None
        if plan:
            rec["at_ready"] = False
            rec["picked"] = pick(arm, plan, rec, args)
            if rec["picked"]:
                place(arm, plan, rec)
            if not rec.get("at_ready") and not rec.get("fault") and not rec.get("stop_after"):
                rec["at_ready"] = back_up(arm, rec)
    rec["seconds"] = time.time() - t0
    if rec["at_ready"]:  # a still of how it ended (the arm is back at READY)
        _, box_after, det_after, _ = eyes.look(name + "_after")
        rec["image_after"] = f"images/{name}_after.jpg"
        rec["auger_in_box"] = eyes.auger_in_box(det_after, box_after or box)
    return rec


def warn_if_moved(holder, box, args):
    for what, f, (x, y, _) in (("holder", holder, S.HOLDER_EXPECTED),
                               (f"box (spot {args.spot})", box, S.SPOTS.get(args.spot, (0, 0, 0)))):
        off = math.hypot(f.x - x, f.y - y)
        if off > S.SPOT_TOLERANCE_MM:
            print(f"NOTE: the {what} is {off:.0f} mm from where settings.py expects it", flush=True)


def recover(arm, args):
    """After a stop: the arm holds where it is. If the operator agrees, open the gripper, go
    straight up, back to READY and park, so arm_power.py can switch it off (exit 0). Else
    leave it holding, motors on (exit 1): the PiPER has no brakes."""
    if not arm.enabled:  # never switched on: arm_power.py checks it is parked before cutting
        return 0
    arm.hold()
    print(f"holding at {A.UD.fmt(arm.joints())}, motors on", flush=True)
    try:
        answer = ask("Clear what stopped it. Enter = open the gripper, go straight up, back to "
                     "READY and park; q = leave it holding: ", args)
    except KeyboardInterrupt:
        answer = "q"
    if answer.lower().startswith("q"):
        print("left holding, motors on: the relay stays on. Run this script again later to "
              "recover, or hold the arm and use the E-stop", flush=True)
        return 1
    rec = {}
    if back_up(arm, rec):
        try:
            arm.park()
            return 0
        except A.ArmError as e:
            rec["why"] = str(e)
    print(f"couldn't park: {rec.get('why')}. Holding, motors on", flush=True)
    arm.hold()
    return 1


def recover_only(args, sim):
    """--recover: take over an arm a stopped run left holding, and park it. Where its rest is
    isn't known any more, so it lands on arm_home.json's typical rest (J2 -1.9, J3 +2.1); if
    the real rest is higher, the landing stops on it and disables there, as Up_and_Down.py does."""
    arm = A.connect(args.dry_run, sim, args.can)
    if not all(arm.piper.GetArmEnableStatus()):
        print("the motors aren't all on, so there is nothing to recover (arm_power.py run "
              "switches the power off if the arm is parked)", flush=True)
        return 0
    q = arm.joints()
    arm.enabled, arm.widened = True, True
    arm.rest = [0.0, -1.9, 2.1, S.J4_DEG, 24.0, S.PARK_J6_DEG]
    arm.ready = A.UD.level([0.0, S.READY_LIFT_DEG, -S.READY_LIFT_DEG, S.J4_DEG, 24.0,
                            S.PARK_J6_DEG])
    print(f"arm holding at {A.UD.fmt(q)}", flush=True)
    return recover(arm, args)


def plan_only(eyes, args, ready):
    holder, box, det, image = eyes.look("plan")
    print(f"tags seen: {sorted(det)}")
    print(f"holder: {holder}")
    print(f"box:    {box}")
    marks = []
    if holder and box:
        try:
            plan = Plan(holder, box, ready)
            print("plan OK:\n" + plan.summary())
            marks = [("grasp", plan.grasp, (0, 0, 255)), ("release", plan.release, (255, 0, 0))]
        except PlanError as e:
            print(f"NO SAFE PLAN: {e}")
    path = os.path.join(args.results, "plan.jpg")
    V.annotate(image, det, eyes.camera, marks, path)
    print(f"annotated still: {path}")


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0],
                                 formatter_class=argparse.RawDescriptionHelpFormatter,
                                 epilog=__doc__.split("\n", 1)[1])
    ap.add_argument("--spot", default="1", help="which box spot this is (a key of settings.SPOTS)")
    ap.add_argument("--runs", type=int, default=1, help="how many runs this session")
    ap.add_argument("--go", action="store_true", help="move the arm (without it: look and plan)")
    ap.add_argument("--until", choices=("above", "grasp"),
                    help="first runs: stop above the auger, or after closing on it (no pull), "
                         "then back to READY and park. Not graded or logged")
    ap.add_argument("--recover", action="store_true",
                    help="after a stop left the arm holding (motors on): go straight up, back "
                         "to READY and park it, so arm_power.py can switch it off")
    ap.add_argument("--yes", action="store_true",
                    help="don't ask: take every suggested grade (for --dry-run and tests)")
    ap.add_argument("--dry-run", action="store_true",
                    help="simulated arm and camera (sim.py): no CAN, no camera")
    ap.add_argument("--results", default=os.path.join(HERE, S.RESULTS_DIR))
    ap.add_argument("--can", default="can0")
    ap.add_argument("--sim", default="", help=argparse.SUPPRESS)  # tests: "missing", "stuck", "nobox"
    args = ap.parse_args()
    if args.until:
        args.runs = 1
    if args.spot not in S.SPOTS:
        raise SystemExit(f"--spot must be one of {sorted(S.SPOTS)} (settings.SPOTS)")
    os.makedirs(args.results, exist_ok=True)

    sim = None
    if args.dry_run:
        import sim as simulation
        sim = simulation.SimCell(args.spot, auger="missing" if "missing" in args.sim else "holder",
                                 stuck="stuck" in args.sim,
                                 box=False if "nobox" in args.sim else None)
        print("DRY RUN: simulated arm and camera")
    if args.recover:
        return recover_only(args, sim)
    eyes = Eyes(args, sim)
    arm = A.connect(args.dry_run, sim, args.can)
    q0 = arm.joints()
    ready = A.UD.level([q0[0], S.READY_LIFT_DEG, -S.READY_LIFT_DEG, S.J4_DEG, q0[4], S.PARK_J6_DEG])
    if not args.go:
        plan_only(eyes, args, ready)
        print("read-only (no --go): nothing was sent to the arm")
        return 0

    session = dt.datetime.now(dt.timezone.utc).strftime("%Y%m%d-%H%M%SZ")
    first = next_run_number(args)
    print(f"session {session}: spot {args.spot}, runs {first} to {first + args.runs - 1}")
    if ask("The arm will rise from its rest to READY. Workspace clear, someone at the E-stop? "
           "Enter = go, q = quit: ", args).lower().startswith("q"):
        return 0
    rc = 1
    try:
        arm.start()
        for n in range(first, first + args.runs):
            if n > first:
                if S.BETWEEN_RUNS == "park":
                    arm.park()
                answer = ask(f"Reset: auger back in its holder, box empty, stand clear. "
                             f"Enter = run {n}, q = finish: ", args)
                if answer.lower().startswith("q"):
                    break
                if sim:
                    sim.reset()
                if S.BETWEEN_RUNS == "park":
                    arm.start()
            print(f"---- run {n} (spot {args.spot})", flush=True)
            rec = one_run(arm, eyes, n, args, session)
            if rec.get("practice"):  # --until: not a graded run
                print(f"practice run: {rec['why']}", flush=True)
                if not rec["at_ready"]:
                    raise A.ArmError(rec["why"])
                continue
            g = grade(rec, args)
            log(rec, args)
            print(f"run {n}: {g}  ({rec['why']}), {rec['seconds']:.0f} s", flush=True)
            if not rec["at_ready"]:  # carry on only from READY
                raise A.ArmError(f"run {n} didn't end back at READY: {rec['why']}")
        arm.park()
        rc = 0
    except A.ArmError as e:
        print(f"STOPPED: {e}", flush=True)
        rc = recover(arm, args)
    except KeyboardInterrupt:
        print("Ctrl-C", flush=True)
        rc = recover(arm, args)
    finally:
        if sim:
            arm.piper.close()
    print(f"results: {os.path.join(args.results, 'results.csv')} (python report.py)", flush=True)
    return rc


if __name__ == "__main__":
    sys.exit(main())
