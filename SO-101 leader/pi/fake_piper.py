"""A simulated PiPER with the parts of piper_sdk's C_PiperInterface_V2 that follower.py and
Up_and_Down.py use. follower.py --dry-run drives this instead of the arm: no piper_sdk import,
no CAN frames, no relay.

It is deliberately simple:
- each joint moves toward its commanded angle at up to 1.5 deg/s per speed percent, clamped to
  the firmware limits;
- J2/J3 draw a current that grows with how far the arm leans out;
- J5 holds the gripper up with -1.8 A while it hangs free, and that falls to nearly nothing
  once the gripper is lowered onto its rest, as on the real arm (#54);
- disabling lets J2, J3 and J5 sag onto the rest, and records how far anything dropped;
- an optional obstacle stops one joint at an angle and makes its current spike, which is how
  the tests check the snag handling.
"""
import threading
import time
from types import SimpleNamespace as NS

REST = [-1.2, -1.9, 2.1, 1.0, 24.3, -52.3]  # #54 / PR #60's parked pose, degrees


class FakePiper:
    def __init__(self, rest=None, obstacle=None, fault_at=None, period_s=0.005):
        self.q = list(rest or REST)
        self.rest = list(self.q)
        self.cmd = list(self.q)
        self.enabled = False
        self.speed = 10
        self.mode = None
        self.fw = {2: [0.0, 180.0], 3: [-170.0, 0.0]}  # firmware limits that can be widened
        self.limit_query = None
        self.grip = 0.0
        self.grip_cmd = 0.0
        self.obstacle = obstacle  # (joint index, angle it can't pass, direction +1/-1)
        self.fault_at = fault_at  # time.time() after which the arm "loses power"
        self.dropped = None  # max sag (deg) of J2/J3 when disabled away from the rest
        self.frames_sent = 0
        self.max_cmd_step = [0.0] * 6  # largest change between two joint commands, per joint
        self.lock = threading.Lock()
        self.stop = threading.Event()
        self.t = time.time()
        self.thread = threading.Thread(target=self._sim, args=(period_s,), daemon=True)
        self.thread.start()

    # ------------------------------------------------------------------ simulation
    def _sim(self, period_s):
        while not self.stop.is_set():
            time.sleep(period_s)
            with self.lock:
                now = time.time()
                dt, self.t = now - self.t, now
                if self.fault_at and now >= self.fault_at:
                    continue  # silent: no feedback updates, as with the E-stop pressed
                if self.enabled:
                    vmax = 1.5 * self.speed
                    for i in range(6):
                        err = self.cmd[i] - self.q[i]
                        step = max(-vmax * dt, min(vmax * dt, err))
                        self.q[i] += step
                    if self.obstacle:
                        j, ang, sign = self.obstacle
                        if (self.q[j] - ang) * sign > 0:
                            self.q[j] = ang
                    gstep = 100 * dt
                    self.grip += max(-gstep, min(gstep, self.grip_cmd - self.grip))

    def close(self):
        self.stop.set()

    def _lean(self):
        return max(0.0, self.q[1]) / 90.0

    def _currents(self):
        if not self.enabled:
            return [0.0] * 6
        amps = [0.2, 0.8 + 2.0 * self._lean(), 0.6 + 1.5 * self._lean(), 0.1, 0.0, 0.1]
        resting = self.q[4] >= self.rest[4] - 1.0
        amps[4] = -0.1 if resting else -1.8
        if self.obstacle:
            j, ang, sign = self.obstacle
            if abs(self.q[j] - ang) < 1e-6 and (self.cmd[j] - ang) * sign > 0:
                amps[j] = 9.0 * sign
        return amps

    # ------------------------------------------------------------------ piper_sdk surface
    def ConnectPort(self, *a, **k):
        return None

    def GetArmJointMsgs(self):
        with self.lock:
            ts = self.t if not (self.fault_at and time.time() >= self.fault_at) else self.fault_at
            js = NS(**{f"joint_{i + 1}": round(v * 1000) for i, v in enumerate(self.q)})
            return NS(joint_state=js, time_stamp=ts, Hz=200.0)

    def GetArmStatus(self):
        err = NS(**{f"communication_status_joint_{i}": False for i in range(1, 7)})
        return NS(arm_status=NS(arm_status=0, err_code=0, ctrl_mode=1 if self.mode else 0,
                                err_status=err), time_stamp=time.time())

    def GetArmHighSpdInfoMsgs(self):
        with self.lock:
            amps = self._currents()
        return NS(**{f"motor_{i + 1}": NS(current=round(a * 1000)) for i, a in enumerate(amps)},
                  time_stamp=time.time())

    def GetArmLowSpdInfoMsgs(self):
        with self.lock:
            en = self.enabled
        m = {f"motor_{i}": NS(can_id=0x260 + i, vol=240,
                              foc_status=NS(driver_enable_status=en)) for i in range(1, 7)}
        return NS(time_stamp=time.time(), **m)

    def GetArmEnableStatus(self):
        with self.lock:
            return [self.enabled] * 6

    def GetArmGripperMsgs(self):
        with self.lock:
            return NS(gripper_state=NS(grippers_angle=round(self.grip * 1000), grippers_effort=0),
                      time_stamp=time.time(), Hz=200.0)

    def MotionCtrl_2(self, ctrl_mode=0x01, move_mode=0x01, move_spd_rate_ctrl=50, is_mit_mode=0):
        if is_mit_mode not in (0x00,):
            raise AssertionError("follower must stay in the capped MOVE J mode")
        with self.lock:
            self.mode = (ctrl_mode, move_mode)
            self.speed = move_spd_rate_ctrl
            self.frames_sent += 1

    def JointCtrl(self, *mdeg):
        with self.lock:
            new = [v / 1000 for v in mdeg]
            for i in range(6):
                self.max_cmd_step[i] = max(self.max_cmd_step[i], abs(new[i] - self.cmd[i]))
            lo2, lo3hi = self.fw[2][0], self.fw[3][1]
            new[1] = max(new[1], lo2)
            new[2] = min(new[2], lo3hi)
            self.cmd = new
            self.frames_sent += 3

    def GripperCtrl(self, gripper_angle=0, gripper_effort=0, gripper_code=0, set_zero=0):
        if set_zero:
            raise AssertionError("follower must never set the gripper zero")
        with self.lock:
            self.grip_cmd = max(0.0, gripper_angle / 1000)
            self.frames_sent += 1

    def EnablePiper(self):
        with self.lock:
            was = self.enabled
            self.enabled = True
            self.cmd = list(self.cmd)
            return was

    def DisablePiper(self):
        with self.lock:
            was = self.enabled
            if self.enabled:
                self.enabled = False
                if self.q[1] < 1.0 and self.q[2] > -1.0:  # near the rest: it settles onto it
                    drop = max(abs(self.q[1] - self.rest[1]), abs(self.q[2] - self.rest[2]))
                    self.q[1], self.q[2] = self.rest[1], self.rest[2]
                    self.q[4] = max(self.q[4], self.rest[4] - 0.3)
                else:
                    drop = 90.0  # held up when the motors went off: it falls (no brakes)
                self.dropped = max(self.dropped or 0.0, drop)
            return was

    def SearchMotorMaxAngleSpdAccLimit(self, motor=1, search_content=0x01):
        self.limit_query = (motor, time.time())

    def GetCurrentMotorAngleLimitMaxVel(self):
        motor, ts = self.limit_query or (1, 0)
        lo, hi = self.fw.get(motor, [-150.0, 150.0])
        x = NS(motor_num=motor, min_angle_limit=round(lo * 10), max_angle_limit=round(hi * 10))
        return NS(current_motor_angle_limit_max_vel=x, time_stamp=ts + 0.01)

    def MotorAngleLimitMaxSpdSet(self, motor=1, max_angle_limit=0x7FFF, min_angle_limit=0x7FFF,
                                 max_joint_spd=0x7FFF):
        with self.lock:
            if motor in self.fw:
                if max_angle_limit != 0x7FFF:
                    self.fw[motor][1] = max_angle_limit / 10
                if min_angle_limit != 0x7FFF:
                    self.fw[motor][0] = min_angle_limit / 10
