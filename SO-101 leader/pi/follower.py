#!/usr/bin/env python3
"""SO-101 leader -> PiPER, the Pi side (#46, PR #47). teleop.py starts this on the Pi that has
the USB-CAN adapter and the relay (rpi-5-mpzy), through PR #60's power protocol:

    ~/piper-venv/bin/python ~/arm_power.py run -- ~/piper-venv/bin/python ~/so101/follower.py

and feeds it joint targets on stdin. --dry-run drives a simulated arm instead (fake_piper.py:
no piper_sdk, no CAN frames); run it directly then, not through arm_power.py.

1. Start. The arm must be resting at home, motors off (nobody else driving it). Like
   Up_and_Down.py, and with its code: widen J2/J3's firmware limits to just past the rest,
   enable, level the J5-J6 link, raise J2/J3 by --lift-deg and roll J6 to --park-j6-deg. That
   is the READY pose.
2. Follow. Nothing moves until the operator holds the deadman with the leader's mapped pose
   within --engage-deg of the arm's on every joint. Then:
   - targets are clamped to --envelope; J4 (no SO-101 joint) stays where it started;
   - a speed and acceleration limiter (--max-deg-s, --max-deg-s2) turns them into setpoints,
     streamed at --hz in the capped mode Up_and_Down.py uses, MotionCtrl_2(1, 1, --speed, 0);
   - the gripper's lowest point may not go below --floor-mm (base frame) while descending;
   - a joint over its --max-current-a, or more than --lag-deg behind its setpoint, is a snag:
     the arm stops where it is and stays stopped until the deadman is released and re-engaged;
   - deadman released, or no fresh command for --stale-s: hold.
3. Finish, on Q from the PC, stdin closing (SSH gone), or no command at all for --lost-s:
   back to READY at --return-deg-s, then down, land, lower the gripper and disable with
   Up_and_Down.py's code, set the firmware limits back and exit 0. arm_power.py then checks the
   arm is parked and switches the relay off. Anything that goes wrong on the way leaves the
   motors on, holding, and exits 1, so the relay stays on (the PiPER has no brakes).

Lines on stdin: "T seq t_pc deadman j1 j2 j3 j5 j6 grip_mm" (degrees; grip "nan" = leave the
gripper alone), "P t_pc" (ping), "Q" (finish). Lines this writes for the PC start with "@":
@HELLO, @READY, @S (state, --state-hz), @P (ping echo), @MSG, @BYE. Other lines are
Up_and_Down.py's, arm_power.py's or piper_sdk's own output.
"""
import argparse
import hashlib
import json
import math
import os
import sys
import threading
import time
from types import SimpleNamespace

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import Up_and_Down as UD  # noqa: E402  the copy beside this file

VERSION = 1
DRIVEN = (0, 1, 2, 4, 5)  # J1 J2 J3 J5 J6; J4 is held
OUT = threading.Lock()


class ArmFault(Exception):
    pass


class Stop(Exception):
    """A snag or failure outside teleop: hold here, motors on, exit 1."""


def emit(kind, payload=""):
    if not isinstance(payload, str):
        payload = json.dumps(payload, separators=(",", ":"))
    with OUT:
        try:
            sys.stdout.write(f"@{kind} {payload}\n")
            sys.stdout.flush()
        except (OSError, ValueError):
            pass  # the PC is gone; keep going and park


def say(text):
    emit("MSG", text)


def r1(q):
    return [round(v, 1) for v in q]


class Link:
    """Commands from the PC, read on a thread. Only the newest target counts."""

    def __init__(self, stream):
        self.lock = threading.Lock()
        self.target = None  # (t_rx, seq, t_pc, deadman, [j1 j2 j3 j5 j6], grip or None)
        self.last_rx = None
        self.quit = None
        self.eof = False
        self.bad = 0
        threading.Thread(target=self._run, args=(stream,), daemon=True).start()

    def _run(self, stream):
        try:
            for raw in stream:
                line = raw.decode("ascii", "replace").split()
                if not line:
                    continue
                now = time.monotonic()
                with self.lock:
                    self.last_rx = now
                if line[0] == "T" and len(line) == 10:
                    try:
                        seq, t_pc = int(line[1]), float(line[2])
                        q = [float(v) for v in line[4:9]]
                        grip = float(line[9])
                        if not all(math.isfinite(v) for v in q):
                            raise ValueError
                    except ValueError:
                        self.bad += 1
                        continue
                    with self.lock:
                        if self.target is None or seq > self.target[1]:
                            self.target = (now, seq, t_pc, line[3] == "1", q,
                                           grip if math.isfinite(grip) else None)
                elif line[0] == "P":
                    emit("P", line[1] if len(line) > 1 else "")
                elif line[0] == "Q":
                    with self.lock:
                        self.quit = "the operator finished (Q)"
                else:
                    self.bad += 1
        except (OSError, ValueError):
            pass
        with self.lock:
            self.eof = True

    def snapshot(self):
        with self.lock:
            return self.target, self.last_rx, self.quit, self.eof

    def clear_quit(self):
        with self.lock:
            self.quit = None


def parse_envelope(text):
    env = {"J1": (-150, 150), "J2": (0, 180), "J3": (-170, 0), "J5": (-70, 70), "J6": (-120, 120)}
    for part in text.split(","):
        name, _, rng = part.partition("=")
        lo, _, hi = rng.partition(":")
        if name not in env or float(lo) > float(hi):
            raise SystemExit(f"--envelope: bad entry {part!r}")
        flo, fhi = env[name]
        env[name] = (max(float(lo), flo), min(float(hi), fhi))
    return env


class Follower:
    def __init__(self, piper, args, link):
        self.piper, self.a, self.link = piper, args, link
        self.ua = SimpleNamespace(  # Up_and_Down.py's defaults, for its moves and checks
            speed=args.ud_speed, deg_s=args.ud_deg_s, tol_deg=1.0, lag_deg=4.0,
            max_current_a=[1.5, 3, 4, 1.5, 4.5, 1.5], backoff_deg=3.0, settle_s=3.0,
            contact_a=0.7, rest_current_a=0.7, lower_deg_s=4.0, wrist_pitch_deg=0.0,
            camera_up_j6_deg=0.0, pause_s=0.5)
        self.phase = "start"
        self.widened = False
        self.hang = None
        self.last_sent = None
        env = parse_envelope(args.envelope)
        self.env_named = env
        self.grip0 = None
        self.gripper_used = False
        self.enabled_once = False

    # ---------------------------------------------------------------- helpers
    def send(self, q, speed):
        UD.send(self.piper, q, speed)
        self.last_sent = list(UD.last_target[0])

    def check(self):
        fault = UD.arm_fault(self.piper)
        if fault:
            raise ArmFault(fault)

    def lv(self, q):
        return UD.level(q, self.ua.wrist_pitch_deg)

    def low_z(self, q):
        """Height (mm, base frame) of the lowest of the flange and the gripper's tip."""
        R, p = UD.fk(q)
        return min(p[2], p[2] + R[2][2] * self.a.tool_mm)

    def move(self, goal, label, hang=None, **over):
        ua = SimpleNamespace(**{**vars(self.ua), **over})
        why = UD.move(self.piper, UD.joints_deg(self.piper), goal, ua, label, hang)
        if why:
            if why[0] == "fault":
                raise ArmFault(why[1])
            raise Stop(f"{label}: {why[1]}")

    # ---------------------------------------------------------------- 1. start
    def start(self):
        a, ua, piper = self.a, self.ua, self.piper
        q0 = UD.joints_deg(piper)
        say(f"arm found at {r1(q0)}, enabled {piper.GetArmEnableStatus()}")
        self.check()
        if any(piper.GetArmEnableStatus()):
            raise SystemExit("refused: the motors are already on, so something else is driving "
                             "the arm. Nothing was sent.")
        problems = []
        if abs(q0[0]) > a.j1_tol_deg:
            problems.append(f"J1 is {q0[0]:.1f} deg (must start within {a.j1_tol_deg:g} of 0)")
        if not (q0[1] <= 0 and q0[2] >= 0):
            problems.append(f"J2/J3 at {q0[1]:.1f}/{q0[2]:.1f} deg: not resting on the rest")
        elif q0[1] < -UD.MAX_WIDEN_DEG + 0.5 or q0[2] > UD.MAX_WIDEN_DEG - 0.5:
            problems.append(f"J2/J3 rest at {q0[1]:.2f}/{q0[2]:.2f} is further past the limits "
                            f"than the {UD.MAX_WIDEN_DEG:g} deg Up_and_Down.py will widen them")
        if not 10 <= q0[4] <= 30:
            problems.append(f"J5 at {q0[4]:.1f}: not the gripper's usual 23-25 deg droop")
        if any(not lo <= v <= hi for v, (lo, hi) in zip(q0[3:], UD.LIMITS[3:])):
            problems.append(f"J4-J6 at {r1(q0[3:])} are outside the joint limits")
        if problems:
            raise SystemExit("refused, nothing sent:\n  " + "\n  ".join(problems))
        self.q0 = q0
        self.rest_j5 = q0[4]
        self.j4 = q0[3]
        self.start_pose = self.lv(q0)
        self.ready = self.lv([q0[0], a.lift_deg, -a.lift_deg, q0[3], q0[4], a.park_j6_deg])
        up0 = self.lv([q0[0], a.lift_deg, -a.lift_deg, *q0[3:]])
        self.home = self.lv([q0[0], 0.0, 0.0, q0[3], q0[4], a.park_j6_deg])
        self.land = [q0[0], min(q0[1] + a.land_above_deg, 0.0),
                     max(q0[2] - a.land_above_deg, 0.0)]
        widen = (min(q0[1] - 0.5, 0.0), max(q0[2] + 0.5, 0.0))
        self.envelope = [self.env_named["J1"], self.env_named["J2"], self.env_named["J3"],
                         (self.j4, self.j4), self.env_named["J5"], self.env_named["J6"]]
        for i in DRIVEN:
            lo, hi = self.envelope[i]
            if not lo <= self.ready[i] <= hi:
                raise SystemExit(f"refused: READY's J{i + 1} = {self.ready[i]:.1f} is outside "
                                 f"--envelope {lo:g}:{hi:g}")
        g = piper.GetArmGripperMsgs()
        self.grip0 = g.gripper_state.grippers_angle / 1000
        emit("HELLO", {"v": VERSION, "q0": r1(q0), "ready": r1(self.ready), "j4": self.j4,
                       "envelope": self.envelope, "grip0": round(self.grip0, 1),
                       "dry_run": a.dry_run, "sha256": self_hash()})
        if a.plan_only:
            say("--plan-only: nothing sent to the arm")
            return False
        before = UD.firmware_limits(piper, 2), UD.firmware_limits(piper, 3)
        if before[0] is None or before[1] is None or before[0][0] != 0 or before[1][1] != 0:
            raise SystemExit(f"refused: J2/J3 firmware limits read {before}, not the stock 0 deg")
        if not UD.set_rest_limits(piper, *widen):
            UD.set_rest_limits(piper, 0.0, 0.0)
            raise SystemExit("refused: couldn't widen the J2/J3 limits (set back to 0); "
                             "nothing moved")
        self.widened = True
        UD.LIMITS[1] = (widen[0], UD.LIMITS[1][1])
        UD.LIMITS[2] = (UD.LIMITS[2][0], widen[1])
        t0 = time.time()
        self.enabled_once = True
        while True:
            self.send(q0, ua.speed)
            if piper.EnablePiper():
                break
            if time.time() - t0 > 5:
                while piper.DisablePiper() and time.time() - t0 < 8:
                    time.sleep(0.01)
                raise SystemExit("motors did not all enable within 5 s; disabled again, "
                                 "nothing moved")
            time.sleep(0.01)
        self.phase = "rise"
        say(f"enabled in {time.time() - t0:.2f} s; raising to READY")
        if abs(q0[4] - self.start_pose[4]) > ua.tol_deg:
            try:
                self.move(self.start_pose, "level the J5-J6 link")
            except Stop as e:  # snag while leveling: back onto the rest and disable there
                self.lower_and_disable(str(e))
                raise
        self.hang = UD.hanging_current(piper, ua)
        self.move(up0, "up", self.hang)
        if abs(q0[5] - a.park_j6_deg) > ua.tol_deg:
            self.move(self.ready, "roll the gripper to READY", self.hang)
        self.phase = "ready"
        emit("READY", {"ready": r1(self.ready), "q": r1(UD.joints_deg(piper))})
        return True

    # ---------------------------------------------------------------- 2. follow
    def clamp(self, t5):
        q = [t5[0], t5[1], t5[2], self.j4, t5[3], t5[4]]
        return [min(max(v, lo), hi) for v, (lo, hi) in zip(q, self.envelope)]

    def limit(self, sp, v, goal, dt):
        a = self.a
        sp, v = list(sp), list(v)
        for i in DRIVEN:
            err = goal[i] - sp[i]
            v_des = math.copysign(min(a.max_deg_s, math.sqrt(2 * a.max_deg_s2 * abs(err))), err)
            vi = v[i] + max(-a.max_deg_s2 * dt, min(a.max_deg_s2 * dt, v_des - v[i]))
            step = vi * dt
            if abs(step) >= abs(err):
                sp[i], v[i] = goal[i], err / dt
            else:
                sp[i], v[i] = sp[i] + step, vi
        return sp, v

    def follow(self):
        """Returns why teleop ended."""
        a, piper = self.a, self.piper
        dt = 1.0 / a.hz
        sp = list(UD.joints_deg(piper))
        sp[3] = self.j4
        v = [0.0] * 6
        self.last_sent = None
        engaged, latch, why_hold = False, None, "waiting for the deadman"
        grip_sp = piper.GetArmGripperMsgs().gripper_state.grippers_angle / 1000
        last_state, seq, t_pc = 0.0, None, None
        t_start = t_next = time.monotonic()
        self.phase = "hold"
        while True:
            t_next += dt
            now = time.monotonic()
            target, last_rx, quit_, eof = self.link.snapshot()
            if quit_:
                far = max(abs(UD.joints_deg(piper)[i] - self.ready[i]) for i in DRIVEN)
                if far <= a.return_max_deg:
                    return quit_
                self.link.clear_quit()
                say(f"not finishing yet: the arm is {far:.0f} deg from READY on some joint "
                    f"(limit {a.return_max_deg:g}). Bring it back near READY, then Q")
            if eof:
                return "the PC's connection closed"
            silent = now - (last_rx if last_rx is not None else t_start)
            if silent > a.lost_s:
                return f"no command from the PC for {silent:.1f} s"
            self.check()
            q = UD.joints_deg(piper)
            amps = UD.currents_a(piper)
            fresh = target is not None and now - target[0] <= a.stale_s
            dm = bool(fresh and target[3])
            goal = self.clamp(target[4]) if target is not None else None
            if target is not None:
                seq, t_pc = target[1], target[2]
            if not dm:
                latch = None
            if engaged and not dm:
                engaged, v = False, [0.0] * 6
                why_hold = "deadman released" if fresh else "no fresh command (link)"
                say(f"hold: {why_hold}")
            if not engaged and dm and latch is None and goal is not None:
                off = max(abs(goal[i] - sp[i]) for i in DRIVEN)
                if off <= a.engage_deg:
                    engaged, why_hold = True, None
                    say("engaged")
                else:
                    why_hold = f"leader is {off:.0f} deg from the arm; line it up"
            floor = False
            if engaged:
                new_sp, new_v = self.limit(sp, v, goal, dt)
                if self.low_z(new_sp) < a.floor_mm and self.low_z(new_sp) < self.low_z(sp) - 1e-6:
                    v, floor = [0.0] * 6, True
                else:
                    sp, v = new_sp, new_v
            sent = self.last_sent or sp
            over = [i for i in range(6) if abs(amps[i]) > a.max_current_a[i]]
            lag = [abs(q[i] - sent[i]) for i in range(6)]
            worst = max(range(6), key=lambda i: lag[i])
            if engaged and (over or lag[worst] > a.lag_deg):
                why = ("; ".join(f"J{i + 1} drew {amps[i]:.1f} A (limit {a.max_current_a[i]:g})"
                                 for i in over) if over else
                       f"J{worst + 1} {lag[worst]:.1f} deg behind its setpoint")
                engaged, latch, v = False, why, [0.0] * 6
                sp = list(q)
                sp[3] = self.j4
                why_hold = f"snag: {why}. Let go of the deadman, then engage again"
                say(why_hold)
            self.send(sp, a.speed)
            if engaged and target[5] is not None:
                g = min(max(target[5], 0.0), a.grip_max_mm)
                grip_sp += max(-a.grip_mm_s * dt, min(a.grip_mm_s * dt, g - grip_sp))
                self.gripper_used = True
                piper.GripperCtrl(round(grip_sp * 1000), round(a.grip_effort_nm * 1000), 0x01, 0)
            if now - last_state >= 1.0 / a.state_hz:
                last_state = now
                self.phase = "follow" if engaged else "hold"
                emit("S", {"ph": self.phase, "q": r1(q), "sp": r1(sp), "seq": seq, "tpc": t_pc,
                           "dm": dm, "why": why_hold, "floor": floor,
                           "amps": [round(x, 1) for x in amps],
                           "z": round(self.low_z(q)), "grip": round(grip_sp, 1)})
            pause = t_next - time.monotonic()
            if pause > 0:
                time.sleep(pause)
            else:
                t_next = time.monotonic()

    # ---------------------------------------------------------------- 3. finish
    def lower_and_disable(self, why):
        q = UD.joints_deg(self.piper)
        say(f"{why}: lowering the gripper back onto its rest and disabling")
        UD.lower_gripper(self.piper, q, self.rest_j5, self.ua)
        self.disable()

    def disable(self):
        q = UD.joints_deg(self.piper)
        t0 = time.time()
        while self.piper.DisablePiper() and time.time() - t0 < 5:
            time.sleep(0.01)
        time.sleep(3.0)
        q2 = UD.joints_deg(self.piper)
        say("disabled; dropped (deg): " + ", ".join(f"J{i + 1} {b - a:+.2f}"
                                                   for i, (a, b) in enumerate(zip(q, q2))))
        self.restore_limits()

    def restore_limits(self):
        if self.widened and not any(self.piper.GetArmEnableStatus()):
            ok = UD.set_rest_limits(self.piper, 0.0, 0.0)
            self.widened = not ok
            say("firmware limits back to J2 >= 0, J3 <= 0" if ok else
                "WARNING: couldn't confirm the J2/J3 firmware limits are back at 0")

    def finish(self, why):
        a, piper = self.a, self.piper
        self.phase = "return"
        say(f"finishing ({why}): back to READY, then park")
        self.send(UD.hold_here(piper, self.ua), self.ua.speed)
        q = UD.joints_deg(piper)
        if self.gripper_used:  # back to the stroke it started with
            piper.GripperCtrl(round(self.grip0 * 1000), round(a.grip_effort_nm * 1000), 0x01, 0)
        if max(abs(x - y) for x, y in zip(q, self.ready)) > self.ua.tol_deg:
            z0 = self.low_z(q)
            for k in range(1, 41):
                p = [x + k / 40 * (y - x) for x, y in zip(q, self.ready)]
                if self.low_z(p) < a.floor_mm and self.low_z(p) < z0 - 5:
                    raise Stop(f"the straight way back to READY dips to {self.low_z(p):.0f} mm, "
                               f"below --floor-mm {a.floor_mm:g}; not moving it unattended")
            self.move(self.ready, "back to READY", None, deg_s=a.return_deg_s,
                      max_current_a=a.max_current_a, lag_deg=a.lag_deg, settle_s=5.0)
        self.phase = "park"
        self.move(self.home, "down to home", self.hang)
        q = UD.joints_deg(piper)
        low = self.lv([*self.land, *q[3:]])
        try:  # as Up_and_Down.py: a snag in the last 2 deg still lowers and disables there
            self.move(low, "land on the rest", None, deg_s=2.0)
        except Stop as e:
            say(f"landing stopped ({e}); lowering the gripper and disabling here")
        UD.lower_gripper(piper, UD.joints_deg(piper), self.rest_j5, self.ua)
        self.disable()
        self.phase = "parked"


def self_hash():
    with open(os.path.abspath(__file__), "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()[:12]


def floats(text, n, name):
    vals = [float(v) for v in text.split(",")]
    if len(vals) != n:
        raise SystemExit(f"{name} takes {n} comma-separated numbers")
    return vals


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0],
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--can", default="can0")
    ap.add_argument("--dry-run", action="store_true",
                    help="drive a simulated arm (fake_piper.py): no piper_sdk, no CAN frames")
    ap.add_argument("--plan-only", action="store_true",
                    help="check the arm's pose and print READY, then exit without enabling")
    ap.add_argument("--hz", type=float, default=100.0, help="setpoint rate")
    ap.add_argument("--state-hz", type=float, default=20.0, help="@S state rate to the PC")
    ap.add_argument("--speed", type=int, default=40,
                    help="MotionCtrl_2 speed percent while following (the arm's own cap)")
    ap.add_argument("--max-deg-s", type=float, default=45.0)
    ap.add_argument("--max-deg-s2", type=float, default=360.0)
    ap.add_argument("--engage-deg", type=float, default=10.0)
    ap.add_argument("--stale-s", type=float, default=0.15)
    ap.add_argument("--lost-s", type=float, default=10.0)
    ap.add_argument("--lag-deg", type=float, default=10.0)
    ap.add_argument("--max-current-a", default="3,7,6,2,4.5,1.5",
                    help="per-joint snag limits while following, J1..J6 (A)")
    ap.add_argument("--envelope", default="J1=-60:60,J2=0:100,J3=-150:0,J5=-60:60,J6=-52:0",
                    help="joint ranges while following (deg). J6 stays inside the roll the "
                         "gripper Pi's cables allowed in #54 (jam at -55)")
    ap.add_argument("--floor-mm", type=float, default=40.0)
    ap.add_argument("--tool-mm", type=float, default=140.0, help="flange to fingertips")
    ap.add_argument("--grip-max-mm", type=float, default=70.0)
    ap.add_argument("--grip-mm-s", type=float, default=80.0)
    ap.add_argument("--grip-effort-nm", type=float, default=1.0)
    ap.add_argument("--lift-deg", type=float, default=20.0, help="READY: J2 up, J3 open by this")
    ap.add_argument("--park-j6-deg", type=float, default=-52.0)
    ap.add_argument("--land-above-deg", type=float, default=0.4)
    ap.add_argument("--j1-tol-deg", type=float, default=10.0)
    ap.add_argument("--return-deg-s", type=float, default=12.0)
    ap.add_argument("--return-max-deg", type=float, default=25.0,
                    help="Q is only accepted this close to READY (each joint)")
    ap.add_argument("--ud-speed", type=int, default=15, help="speed percent for start/park moves")
    ap.add_argument("--ud-deg-s", type=float, default=12.0, help="peak deg/s for start/park")
    ap.add_argument("--sim-obstacle", help=argparse.SUPPRESS)  # tests: "J,ANGLE,SIGN"
    ap.add_argument("--sim-rest", help=argparse.SUPPRESS)  # tests: six angles
    a = ap.parse_args()
    a.max_current_a = floats(a.max_current_a, 6, "--max-current-a")
    checks = [(1 <= a.speed <= 60, "--speed must be 1-60 (capped mode)"),
              (1 <= a.max_deg_s <= 90, "--max-deg-s must be 1-90"),
              (10 <= a.max_deg_s2 <= 1000, "--max-deg-s2 must be 10-1000"),
              (20 <= a.hz <= 200, "--hz must be 20-200"),
              (1 <= a.engage_deg <= 20, "--engage-deg must be 1-20"),
              (0.05 <= a.stale_s <= 1, "--stale-s must be 0.05-1"),
              (1 <= a.lost_s <= 60, "--lost-s must be 1-60"),
              (0 <= a.grip_effort_nm <= 2, "--grip-effort-nm must be 0-2"),
              (0 < a.lift_deg <= 30, "--lift-deg must be in (0, 30]"),
              (1 <= a.return_deg_s <= 20, "--return-deg-s must be 1-20"),
              (1 <= a.ud_speed <= 30 and 1 <= a.ud_deg_s <= 20, "start/park speeds out of range"),
              (all(0 < x <= 10 for x in a.max_current_a), "--max-current-a: each in (0, 10]")]
    for ok, text in checks:
        if not ok:
            raise SystemExit(text)

    if a.dry_run:
        from fake_piper import FakePiper
        obstacle = None
        if a.sim_obstacle:
            j, ang, sign = a.sim_obstacle.split(",")
            obstacle = (int(j) - 1, float(ang), int(sign))
        piper = FakePiper(rest=floats(a.sim_rest, 6, "--sim-rest") if a.sim_rest else None,
                          obstacle=obstacle)
        say("DRY RUN: simulated arm, no CAN frames")
    else:
        if not os.path.exists(f"/sys/class/net/{a.can}"):
            raise SystemExit(f"{a.can} is missing: is the USB-CAN adapter on this Pi?")
        from piper_sdk import C_PiperInterface_V2
        piper = C_PiperInterface_V2(a.can)
        piper.ConnectPort()
    if not UD.wait_for_feedback(piper):
        raise SystemExit("no joint feedback on the bus: is the arm powered?")
    time.sleep(0.3)

    link = Link(sys.stdin.buffer)
    f = Follower(piper, a, link)
    rc, why = 1, "?"
    try:
        if not f.start():
            rc, why = 0, "plan only"
        else:
            why = f.follow()
            f.finish(why)
            rc, why = 0, f"parked after: {why}"
    except ArmFault as e:
        why = f"arm fault: {e}. Not commanding anything further"
    except Stop as e:
        why = f"stopped: {e}"
        if any(piper.GetArmEnableStatus()):
            try:
                q = UD.hold_here(piper, f.ua)
                why += f". Holding at {r1(q)} with the motors on: park it by hand or with " \
                       "Up_and_Down.py --park --go, then arm_power.py off"
            except Exception as e2:  # noqa: BLE001
                why += f". Couldn't hold ({e2})"
        else:
            why += ". Motors off"
    except SystemExit as e:  # refusals: nothing sent, unless the motors failed to enable
        why = str(e)
        rc = 1 if f.enabled_once else 0
    except KeyboardInterrupt:
        why = "interrupted"
        try:
            f.finish(why)
            rc, why = 0, "parked after Ctrl-C"
        except (Stop, ArmFault) as e:
            why = f"Ctrl-C, then: {e}"
    finally:
        if rc != 0 and f.widened and not any(piper.GetArmEnableStatus()):
            f.restore_limits()
    emit("BYE", {"rc": rc, "why": why, "phase": f.phase})
    if a.dry_run:
        piper.close()
    # os._exit, not sys.exit: the stdin reader thread is blocked in a read, and interpreter
    # shutdown would abort on it (exit -6), which arm_power.py would take as a failure.
    with OUT:
        try:
            sys.stdout.flush()
        except (OSError, ValueError):
            pass
    os._exit(rc)


if __name__ == "__main__":
    main()
