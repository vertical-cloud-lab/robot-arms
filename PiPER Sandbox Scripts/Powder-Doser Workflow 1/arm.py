"""The PiPER, for this workflow: rise from the rest to READY, move along planned paths, open
and close the gripper, and park again. It reuses Up_and_Down.py's moves and checks (the same
code teleop's follower.py uses), so the arm starts and parks exactly as it does there:

- start(): only from the rest with the motors off. Widen J2/J3's firmware limits to just past
  the rest, enable joints 1-6 (never the gripper with them: EnablePiper sets it hunting for
  its zero, which the finger sleeves stall), level the wrist, rise to READY.
- park(): back to READY, down, land on the rest, lower the gripper onto it, disable, put the
  firmware limits back. Only then may arm_power.py switch the power off.
- go() / follow(): every move is streamed at 50 Hz with a smooth start and stop, capped by the
  arm's own speed limit, and stops on a snag: a joint drawing more current than its limit, or
  falling more than settings.LAG_DEG behind. A snag returns ("stuck", why) and the arm holds
  where it is; a fault (E-stop, power cut, no feedback) returns ("fault", why).
"""
import math
import os
import sys
import time
from types import SimpleNamespace

import kinematics as K
import settings as S

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(HERE), "Arm Control"))
import Up_and_Down as UD  # noqa: E402

PERIOD_S = UD.PERIOD_S  # 50 Hz


class ArmError(Exception):
    """Something stopped the arm; the message says what and where it was left."""


class Arm:
    def __init__(self, piper):
        self.piper = piper
        # Up_and_Down.move's settings, for the start and park moves (its own defaults).
        self.ua = SimpleNamespace(
            speed=15, deg_s=12.0, tol_deg=1.0, lag_deg=4.0,
            max_current_a=[1.5, 3, 4, 1.5, 4.5, 1.5], backoff_deg=3.0, settle_s=3.0,
            contact_a=0.7, rest_current_a=0.7, lower_deg_s=4.0, wrist_pitch_deg=0.0,
            camera_up_j6_deg=0.0, pause_s=0.5)
        self.rest = None      # the joints as found on the rest, for landing there again
        self.ready = None     # the READY pose
        self.widened = False  # J2/J3 firmware limits widened for the landing
        self.enabled = False

    # ---------------------------------------------------------------- reading the arm
    def joints(self):
        return UD.joints_deg(self.piper)

    def gripper_mm(self):
        return self.piper.GetArmGripperMsgs().gripper_state.grippers_angle / 1000

    def check(self):
        fault = UD.arm_fault(self.piper)
        if fault:
            raise ArmError(f"arm fault: {fault}")

    # ---------------------------------------------------------------- rise and park
    def at_rest_problems(self):
        """Why the arm isn't resting on its rest with its motors off ([] = it is)."""
        q = self.joints()
        out = []
        if any(self.piper.GetArmEnableStatus()):
            out.append("the motors are on: something else is driving the arm")
        if abs(q[0]) > 10:
            out.append(f"J1 is {q[0]:.1f} deg (must start within 10 of 0)")
        if not (q[1] <= 0 and q[2] >= 0):
            out.append(f"J2/J3 at {q[1]:.1f}/{q[2]:.1f} deg: not resting on the rest")
        elif q[1] < -UD.MAX_WIDEN_DEG + 0.5 or q[2] > UD.MAX_WIDEN_DEG - 0.5:
            out.append(f"J2/J3 rest at {q[1]:.2f}/{q[2]:.2f}, further past the limits than "
                       f"the {UD.MAX_WIDEN_DEG:g} deg Up_and_Down.py will widen them")
        if not 10 <= q[4] <= 30:
            out.append(f"J5 at {q[4]:.1f}: not the gripper's usual 23-25 deg droop on its rest")
        return out

    def start(self):
        """From the rest (motors off) to READY, motors on, gripper switched on."""
        problems = self.at_rest_problems()
        if problems:
            raise ArmError("not starting, nothing sent:\n  " + "\n  ".join(problems))
        q0 = self.joints()
        self.rest = q0
        lift = S.READY_LIFT_DEG
        self.ready = UD.level([q0[0], lift, -lift, S.J4_DEG, q0[4], S.PARK_J6_DEG])
        before = UD.firmware_limits(self.piper, 2), UD.firmware_limits(self.piper, 3)
        if None in before or before[0][0] != 0 or before[1][1] != 0:
            raise ArmError(f"J2/J3 firmware limits read {before}, not the stock 0 deg; "
                           "nothing sent")
        widen = (min(q0[1] - 0.5, 0.0), max(q0[2] + 0.5, 0.0))
        if not UD.set_rest_limits(self.piper, *widen):
            UD.set_rest_limits(self.piper, 0.0, 0.0)
            raise ArmError("couldn't widen the J2/J3 limits (set back to 0); nothing moved")
        self.widened = True
        UD.LIMITS[1] = (widen[0], UD.LIMITS[1][1])
        UD.LIMITS[2] = (UD.LIMITS[2][0], widen[1])
        t0 = time.time()
        while True:  # enable joints 1-6, holding where they are so nothing jumps
            UD.send(self.piper, q0, self.ua.speed)
            if UD.enable_joints(self.piper):
                break
            if time.time() - t0 > 5:
                self.disable()
                raise ArmError("motors did not all enable within 5 s; disabled again")
            time.sleep(0.01)
        self.enabled = True
        print(f"enabled in {time.time() - t0:.2f} s; rising to READY", flush=True)
        self._ud_move(UD.level(q0), "level the wrist")
        self._ud_move(UD.level([q0[0], lift, -lift, *q0[3:]]), "up off the rest")
        self._ud_move(self.ready, "READY")
        self.gripper_on()

    def park(self):
        """From anywhere above the work, back to READY, then down onto the rest and off."""
        q = self.joints()
        if max(abs(a - b) for a, b in zip(q, self.ready)) > 1.0:
            why = self.go(self.ready, "back to READY")
            if why:
                raise ArmError(why[1])
        q0 = self.rest
        home = UD.level([q0[0], 0.0, 0.0, S.J4_DEG, q0[4], S.PARK_J6_DEG])
        self._ud_move(home, "down to home")
        land = UD.level([q0[0], min(q0[1] + 0.4, 0.0), max(q0[2] - 0.4, 0.0), *home[3:]])
        why = UD.move(self.piper, self.joints(), land, SimpleNamespace(**{**vars(self.ua),
                                                                          "deg_s": 2.0}),
                      "land on the rest")
        if why:
            print(f"  landing stopped ({why[1]}); lowering the gripper and disabling here",
                  flush=True)
        UD.lower_gripper(self.piper, self.joints(), q0[4], self.ua)
        self.disable()

    def disable(self):
        q = self.joints()
        t0 = time.time()
        while self.piper.DisablePiper() and time.time() - t0 < 5:
            time.sleep(0.01)
        self.enabled = False
        time.sleep(3.0)
        q2 = self.joints()
        print("disabled; settled (deg): " + ", ".join(f"J{i + 1} {b - a:+.2f}"
                                                      for i, (a, b) in enumerate(zip(q, q2))),
              flush=True)
        if self.widened and not any(self.piper.GetArmEnableStatus()):
            ok = UD.set_rest_limits(self.piper, 0.0, 0.0)
            self.widened = not ok
            print("firmware limits back to J2 >= 0, J3 <= 0" if ok else
                  "WARNING: couldn't confirm the J2/J3 firmware limits are back at 0", flush=True)

    def hold(self):
        """Stop where the arm is (it keeps holding there, motors on)."""
        return UD.hold_here(self.piper, self.ua)

    def _ud_move(self, goal, label):
        why = UD.move(self.piper, self.joints(), goal, self.ua, label)
        if why:
            raise ArmError(f"{label}: {why[1]}")

    # ---------------------------------------------------------------- moving
    def go(self, goal, label):
        """A joint-space move (all joints start and stop together) to goal."""
        return self.follow([self.joints(), list(goal)], label)

    def follow(self, path, label, mm_s=S.MOVE_MM_S, currents=S.MAX_CURRENT_A):
        """Stream the arm along path (a list of joint angles, a few mm apart) with a smooth
        start and stop. The time it takes comes from the TCP's path length at mm_s and the
        joints' travel at settings.JOINT_DEG_S, whichever is slower. Returns None once there,
        else ("stuck", why) or ("fault", why); after a snag the arm holds where it is."""
        n = len(path) - 1
        length = sum(math.dist(K.tcp(a), K.tcp(b)) for a, b in zip(path, path[1:]))
        travel = max(sum(abs(b[j] - a[j]) for a, b in zip(path, path[1:])) for j in range(6))
        mean_s = max(length / mm_s, travel / S.JOINT_DEG_S, 0.3)
        duration = math.pi / 2 * mean_s  # the raised cosine peaks at pi/2 x the mean speed
        print(f"{label}: {length:.0f} mm, {duration:.1f} s", flush=True)
        t0 = time.time()
        while True:
            t = time.time() - t0
            s = 0.5 - 0.5 * math.cos(math.pi * min(t / duration, 1.0))
            i = min(int(s * n), n - 1)
            f = s * n - i
            target = [a + f * (b - a) for a, b in zip(path[i], path[i + 1])]
            UD.send(self.piper, target, S.SPEED_PERCENT)
            time.sleep(PERIOD_S)
            fault = UD.arm_fault(self.piper)
            if fault:
                return "fault", fault
            q = self.joints()
            amps = UD.currents_a(self.piper)
            over = [j for j in range(6) if abs(amps[j]) > currents[j]]
            lag = [abs(a - b) for a, b in zip(q, UD.last_target[0])]
            worst = max(range(6), key=lambda j: lag[j])
            why = None
            if over:
                why = "; ".join(f"J{j + 1} drew {amps[j]:.1f} A (limit {currents[j]:g})"
                                for j in over)
            elif lag[worst] > S.LAG_DEG:
                why = f"J{worst + 1} is {lag[worst]:.1f} deg behind its target"
            if why:
                self.hold()
                return "stuck", f"{label}: {why}, at {UD.fmt(q)}"
            if t >= duration and max(abs(a - b) for a, b in zip(q, path[-1])) <= 1.0:
                return None
            if t > duration + 3.0:
                return "stuck", f"{label}: not within 1 deg of the end 3 s after: {UD.fmt(q)}"

    # ---------------------------------------------------------------- the gripper
    def gripper_on(self):
        """Switch the gripper on holding where it is, so it doesn't jump (as follower.py)."""
        hold = min(max(self.gripper_mm(), S.GRIPPER_CLOSED_READING_MM), S.GRIPPER_MAX_READING_MM)
        for _ in range(10):  # resent: a frame can be lost
            self.piper.GripperCtrl(round(hold * 1000), round(S.GRIP_EFFORT_NM * 1000), 0x01, 0)
            time.sleep(0.05)

    def gripper_to(self, reading_mm, effort_nm=S.GRIP_EFFORT_NM, timeout_s=4.0):
        """Move the gripper's target to reading_mm at settings.GRIPPER_MM_S (its own position
        control slams shut far faster), then wait until it stops: at the target, or on
        whatever is between the fingers. Returns the reading it stopped at."""
        reading_mm = min(max(reading_mm, 0.0), S.GRIPPER_MAX_READING_MM)
        start = self.gripper_mm()
        ramp_s = abs(reading_mm - start) / S.GRIPPER_MM_S
        t0, history = time.time(), []
        while True:
            t = time.time() - t0
            cmd = start + (reading_mm - start) * min(t / ramp_s, 1.0) if ramp_s else reading_mm
            self.piper.GripperCtrl(round(cmd * 1000), round(effort_nm * 1000), 0x01, 0)
            time.sleep(PERIOD_S)
            history.append((t, self.gripper_mm()))
            recent = [w for tt, w in history if tt >= t - 0.3]
            if t >= ramp_s + 0.3 and max(recent) - min(recent) < 0.2:
                return history[-1][1]
            if t > ramp_s + timeout_s:
                return history[-1][1]


def connect(dry_run=False, sim=None, can="can0"):
    """The arm: piper_sdk on can0, or with dry_run the simulated arm in sim.py."""
    if dry_run:
        piper = sim.make_arm()
    else:
        if not os.path.exists(f"/sys/class/net/{can}"):
            raise ArmError(f"{can} is missing: run this on the arm Pi (mpzy), through "
                           "arm_power.py run")
        from piper_sdk import C_PiperInterface_V2
        piper = C_PiperInterface_V2(can)
        piper.ConnectPort()
    if not UD.wait_for_feedback(piper):
        raise ArmError("no joint feedback on the bus: is the arm powered (arm_power.py run)?")
    time.sleep(0.3)
    return Arm(piper)
