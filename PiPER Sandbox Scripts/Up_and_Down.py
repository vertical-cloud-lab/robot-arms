#!/usr/bin/env python3
"""Raise and lower the PiPER, then park it with the gripper Pi rolled to the side (#54).

The gripper Pi sits opposite the camera: underneath the gripper with J6 near 0, its USB-C
power plug facing back toward J2. Disabling the motors there drops the arm onto its rest and
lands the plug on J2's housing. Rolled to J6 = -90 (the third photo on #54: Pi to the arm's
right, camera to its left) the arm drops clear. With the motors off the wrist also droops
(J5 near +23, the gripper about 18 deg nose-down) until the gripper rests on something. So
the script:

1. Starts from the rest (J2 and J3 within --home-tol-deg of 0) or from a pose it raised, with
   J1 within --j1-tol-deg of 0. J1 stays where it starts the whole time, so nothing swings
   sideways toward the printer.
2. Levels the J5-J6 link first (J5 to about +5, so the gripper's axis is horizontal), which
   lifts the drooped gripper off whatever it rests on. --no-level keeps the wrist as found.
3. Raises the arm with the wrist level: J2 up by --lift-deg and J3 open by the same angle,
   so the forearm keeps its pitch and the wrist rises 94 mm (for 20 degrees) and moves 30 mm
   forward.
4. At the top, rolls the gripper to J6 = --park-j6-deg, with J4 and J5 held (a pure twist).
5. Lowers to home (J2 = J3 = 0) with the link level and the gripper rolled, and repeats up
   and down until it has done --cycles in all. "Down" is never lower than home.
6. Lands the arm --land-above-deg above the rest it started on, then lowers the gripper
   (J5) slowly toward where it was found drooped, stopping as soon as whatever it rests on
   takes its weight (J5's current falls under --rest-current-a), then disables, so nothing
   drops more than about half a degree. The firmware stops J2 at 0 and J3 at 0 while the rest
   is at about -2 and +2, so the script widens those two limits to just past the rest first
   and sets them back to 0 after disabling (--no-land skips all this and disables at home,
   which drops the arm about 2 degrees). Then it watches the arm settle for 3 s and reports
   how far each joint dropped.

Every move follows a smooth profile that peaks at --deg-s, streamed at 50 Hz, with the
controller's own speed capped at --speed percent as well. A snag is a joint drawing more than
its --max-current-a (a cable going taut shows here first), falling more than --lag-deg
behind its target, or, once the gripper hangs level, J5 carrying less than --contact-a of the
gripper's weight (something underneath is holding it up: the second run's failure). On a snag
it first backs the joints off --backoff-deg along the way they came, so nothing keeps pushing
on whatever caught, and then:
- while leveling, it lowers the gripper back onto its rest and disables;
- on the way up, or while rolling the gripper, it holds, puts the roll back as it found it,
  goes back down to home, lands and disables: no worse than before the run;
- once the gripper is rolled, on the way up, it goes back down to home, lands and disables;
- on the way down (something under the arm), it holds there with the motors on and says so.
If the arm reports an error or its feedback stops (E-stop or power cut), it stops commanding
motion and says so.

First run, 2026-10-30 (#54): from J6 = -18 the roll toward -90 (also straightening J5) jammed
at J6 = -55.0 (J5 = 11), with J6's current going from 0.1 A to 16 A. The lag check alone took
0.35 s to see it, which is why the current check and the back-off exist, and why the roll now
stops at J6 = -52 by default. Second run: rolled to -52 with the wrist drooped, the gripper
came to rest on something at home (J5's current flipped sign), and the next lift tripped J3's
current limit, which is why the wrist is now level whenever the arm moves. Third and fourth
runs, with the link level: no snags, and nothing touched at home. From the arm's own rest the
power-off drop was J2 0.25, J3 0.60, J5 0.08 deg (J3's rest wanders between +1.8 and +2.4 from
run to run, so the fixed --land-above-deg can't promise half a degree there).

Runs on the Pi that has the USB-CAN adapter (rpi-5-mpzy since 2026-10-30; the arm Pi,
rpi-5-eufi, before that), in the venv that has piper_sdk (~/piper-venv). can0 must already be
up at 1 Mbit/s; this script never touches the interface.

    ~/piper-venv/bin/python Up_and_Down.py            # read-only: check the pose, print the plan
    ~/piper-venv/bin/python Up_and_Down.py --go       # enable the motors and move
    ~/piper-venv/bin/python Up_and_Down.py --park --go
        # one cycle only (up, roll the gripper, down, land), e.g. after an interrupted run
"""
import argparse
import math
import os
import sys
import threading
import time

MDEG = 1000  # piper_sdk joint units are 0.001 degree
PERIOD_S = 0.02  # stream targets at 50 Hz
STALE_S = 0.5  # joint feedback older than this means the arm stopped talking
# Joint limits from piper_sdk's JointCtrl docstring. The SDK doesn't enforce them by default, and
# the arm rests just outside J2's and J3's (about -2 and +2), so targets are clamped here.
LIMITS = [(-150, 150), (0, 180), (-170, 0), (-100, 100), (-70, 70), (-120, 120)]
MAX_WIDEN_DEG = 4.0  # never move J2's lower or J3's upper firmware limit further than this

# piper_sdk's DH table (C_PiperForwardKinematics, dh_is_offset=1): modified DH, mm and degrees.
DH = [  # a, alpha, theta offset, d
    (0, 0, 0, 123),
    (0, -90, -172.22, 0),
    (285.03, 0, -102.78, 0),
    (-21.98, 90, 0, 250.75),
    (0, -90, 0, 0),
    (0, 90, 0, 91),
]

last_target = [None]  # the joint angles most recently sent, for the trace


def fk(q_deg):
    """Flange pose for joint angles in degrees: (3x3 rotation, position in mm), base frame
    x forward, y left, z up. Matches piper_sdk's forward kinematics."""
    T = [[1.0 if i == j else 0.0 for j in range(4)] for i in range(4)]
    for (a, alpha, theta0, d), q in zip(DH, q_deg):
        ca, sa = math.cos(math.radians(alpha)), math.sin(math.radians(alpha))
        ct, st = math.cos(math.radians(theta0 + q)), math.sin(math.radians(theta0 + q))
        link = [[ct, -st, 0, a],
                [st * ca, ct * ca, -sa, -sa * d],
                [st * sa, ct * sa, ca, ca * d],
                [0, 0, 0, 1]]
        T = [[sum(T[i][k] * link[k][j] for k in range(4)) for j in range(4)] for i in range(4)]
    return [row[:3] for row in T[:3]], [T[i][3] for i in range(3)]


def pi_direction(q_deg, camera_up_j6_deg):
    """Unit vector (base frame) from the gripper's axis toward the Pi. The Pi is opposite the
    camera, which is straight up at the all-zero pose with J6 = camera_up_j6_deg."""
    R0, _ = fk([0, 0, 0, 0, 0, camera_up_j6_deg])
    camera = [R0[2][i] for i in range(3)]  # world up, expressed in the flange frame
    R, _ = fk(q_deg)
    return [-sum(R[i][k] * camera[k] for k in range(3)) for i in range(3)]


def pi_tilt(q_deg, args):
    """Degrees above horizontal (negative: below) of the Pi's side of the gripper."""
    return math.degrees(math.asin(max(-1.0, min(1.0, pi_direction(q_deg, args.camera_up_j6_deg)[2]))))


def describe_pi(q_deg, args):
    d = pi_direction(q_deg, args.camera_up_j6_deg)
    tilt = pi_tilt(q_deg, args)
    side = "the arm's left (+y)" if d[1] > 0 else "the arm's right (-y)"
    return f"Pi side of the gripper points to {side}, {abs(tilt):.0f} deg " \
           f"{'below' if tilt < 0 else 'above'} horizontal"


def wrist_pitch(q_deg):
    """Degrees above horizontal (negative: below) of the gripper's axis, the J5-J6 link."""
    R, _ = fk(q_deg)
    return math.degrees(math.asin(max(-1.0, min(1.0, R[2][2]))))


def level(q_deg, pitch_deg=0.0):
    """q_deg with J5 set so the J5-J6 link points pitch_deg above horizontal. Raising J5 tips
    the gripper down, so bisect on that."""
    lo, hi = -60.0, 60.0
    for _ in range(40):
        mid = (lo + hi) / 2
        if wrist_pitch([*q_deg[:4], mid, q_deg[5]]) > pitch_deg:
            lo = mid
        else:
            hi = mid
    return [*q_deg[:4], round((lo + hi) / 2, 2), q_deg[5]]


def joints_deg(piper):
    js = piper.GetArmJointMsgs().joint_state
    return [js.joint_1 / MDEG, js.joint_2 / MDEG, js.joint_3 / MDEG,
            js.joint_4 / MDEG, js.joint_5 / MDEG, js.joint_6 / MDEG]


def fmt(q):
    return "[" + ", ".join(f"{v:7.2f}" for v in q) + "]"


def wait_for_feedback(piper, timeout_s=3.0):
    t0 = time.time()
    while time.time() - t0 < timeout_s:
        if piper.GetArmJointMsgs().Hz > 0:
            return True
        time.sleep(0.1)
    return False


def clamp(q_deg):
    return [min(max(v, lo), hi) for v, (lo, hi) in zip(q_deg, LIMITS)]


def send(piper, target_deg, speed):
    target = clamp(target_deg)
    last_target[0] = target
    piper.MotionCtrl_2(0x01, 0x01, speed, 0x00)  # CAN control, MOVE J, speed percent
    piper.JointCtrl(*[round(v * MDEG) for v in target])


def arm_fault(piper):
    """Why the arm can't be trusted to keep moving, or None."""
    msg = piper.GetArmJointMsgs()
    if time.time() - msg.time_stamp > STALE_S:
        return f"no joint feedback for {time.time() - msg.time_stamp:.1f} s (power cut or E-stop?)"
    st = piper.GetArmStatus().arm_status
    # Angle-limit flags aren't counted: the rest pose sits just past J2's and J3's limits.
    comms = [k for k, v in vars(st.err_status).items() if v and k.startswith("communication")]
    if st.arm_status != 0 or comms:
        return f"arm status {st.arm_status}, err code {st.err_code}, flags {comms or 'none'}"
    return None


def firmware_limits(piper, motor):
    """(min, max) firmware angle limit of one joint in degrees, or None if it didn't answer."""
    t0 = time.time()
    piper.SearchMotorMaxAngleSpdAccLimit(motor, 0x01)
    while time.time() - t0 < 1.0:
        time.sleep(0.05)
        msg = piper.GetCurrentMotorAngleLimitMaxVel()
        x = msg.current_motor_angle_limit_max_vel
        if msg.time_stamp > t0 and x.motor_num == motor:
            return x.min_angle_limit / 10, x.max_angle_limit / 10
    return None


def set_rest_limits(piper, j2_min, j3_max):
    """Set J2's lower and J3's upper firmware limit (deg; the other ends and the speed limits
    are left alone), read each back and return True if both took. The arm drops a second
    setting sent within 0.1 s of the first, so each gets its own pause and check."""
    ok = True
    for motor, hi, lo in ((2, None, j2_min), (3, j3_max, None)):
        for _ in range(3):
            piper.MotorAngleLimitMaxSpdSet(motor, 0x7FFF if hi is None else round(hi * 10),
                                           0x7FFF if lo is None else round(lo * 10), 0x7FFF)
            time.sleep(0.5)
            got = firmware_limits(piper, motor)
            if got and abs(got[0 if hi is None else 1] - (lo if hi is None else hi)) < 0.15:
                break
        else:
            ok = False
    return ok


def currents_a(piper):
    hs = piper.GetArmHighSpdInfoMsgs()
    return [getattr(hs, f"motor_{i}").current / 1000 for i in range(1, 7)]


def back_off(piper, q, start, goal, args):
    """Go back --backoff-deg the way the move came (the joint moving most by that much, the
    rest in proportion), so nothing keeps pushing on whatever caught."""
    span = max(abs(b - a) for a, b in zip(start, goal)) or 1.0
    back = [v - args.backoff_deg * (b - a) / span for v, a, b in zip(q, start, goal)]
    # Never below home: the second run (#54) snagged just above home and backed off 1.3 deg
    # below it, toward whatever was under the arm, because the landing had widened the limits.
    back[1], back[2] = max(back[1], min(q[1], 0.0)), min(back[2], max(q[2], 0.0))
    t0 = time.time()
    while time.time() - t0 < 0.5:
        send(piper, back, args.speed)
        time.sleep(PERIOD_S)
    print(f"  backed off to {fmt(joints_deg(piper))}", flush=True)


def move(piper, start, goal, args, label, hang=None):
    """Stream a smooth move from start to goal. Returns None once there, else why it stopped:
    ("fault", text) if the arm reported a problem or went quiet, ("stuck", text) if a joint
    drew too much current, fell behind its target or didn't arrive, or (with hang, J5's current
    while the gripper hangs free) J5 carried less than --contact-a of the gripper's weight.
    When a joint drew too much, fell behind or was held up, it has already backed off."""
    span = max(abs(b - a) for a, b in zip(start, goal))
    duration = max(math.pi / 2 * span / args.deg_s, 0.3)  # raised cosine peaks at pi/2 x mean
    print(f"{label}: {fmt(goal)} over {duration:.1f} s", flush=True)
    t0 = time.time()
    held_up = 0  # consecutive samples with J5 carrying less than --contact-a
    while True:
        t = time.time() - t0
        s = 0.5 - 0.5 * math.cos(math.pi * min(t / duration, 1.0))
        target = clamp([a + s * (b - a) for a, b in zip(start, goal)])
        send(piper, target, args.speed)
        time.sleep(PERIOD_S)
        fault = arm_fault(piper)
        if fault:
            return "fault", fault
        q = joints_deg(piper)
        amps = currents_a(piper)
        over = [i for i in range(6) if abs(amps[i]) > args.max_current_a[i]]
        lag = [abs(a - b) for a, b in zip(q, target)]
        worst = max(range(6), key=lambda i: lag[i])
        why = None
        if over:
            why = "; ".join(f"J{i + 1} drew {amps[i]:.1f} A (limit {args.max_current_a[i]:g})"
                            for i in over)
        elif lag[worst] > args.lag_deg:
            why = (f"J{worst + 1} at {q[worst]:.2f} deg is {lag[worst]:.1f} deg from its target "
                   f"{target[worst]:.2f}")
        held_up = held_up + 1 if hang and amps[4] * math.copysign(1, hang) < args.contact_a else 0
        if not why and held_up >= 2:
            why = (f"J5 carries {amps[4]:+.2f} A against {hang:+.2f} A hanging free: something "
                   "is holding the gripper up")
        if why:
            back_off(piper, q, start, goal, args)
            return "stuck", f"{why}; all joints {fmt(q)}"
        if t >= duration and all(abs(a - b) <= args.tol_deg for a, b in zip(q, goal)):
            print(f"  reached in {t:.1f} s: {fmt(q)}", flush=True)
            return None
        if t > duration + args.settle_s:
            return "stuck", (f"not within {args.tol_deg} deg of {fmt(goal)} {args.settle_s} s "
                             f"after the profile ended: {fmt(q)}")


def hold_here(piper, args):
    """Command the measured pose, so the arm stops wherever it is."""
    q = joints_deg(piper)
    for _ in range(10):
        send(piper, q, args.speed)
        time.sleep(PERIOD_S)
    return q


def hanging_current(piper, args):
    """J5's mean current over 0.3 s while holding still, or None if it's too small to tell a
    free-hanging gripper from one resting on something."""
    samples = []
    for _ in range(15):
        time.sleep(PERIOD_S)
        samples.append(currents_a(piper)[4])
    mean = sum(samples) / len(samples)
    return mean if abs(mean) >= args.contact_a + 0.4 else None


def lower_gripper(piper, q, rest_j5, args):
    """Tip the gripper down (raise J5) at --lower-deg-s toward rest_j5 + 0.5, where it was found
    drooped, and stop as soon as whatever it rests on takes its weight: J5's current, which
    holds the gripper up, falls under --rest-current-a. Returns why it stopped, or None if the
    gripper was already down. A fault is returned as ("fault", text)."""
    goal = rest_j5 + 0.5
    if q[4] >= rest_j5 - 0.5:
        return None
    hang = hanging_current(piper, args)
    print(f"lower the gripper: J5 from {q[4]:.2f} toward {goal:.2f} at {args.lower_deg_s:g} deg/s "
          f"until it rests (J5 holding {hang if hang is None else round(hang, 2)} A now)",
          flush=True)
    t0, below = time.time(), 0
    while True:
        t = time.time() - t0
        j5 = min(q[4] + args.lower_deg_s * t, goal)
        send(piper, [*q[:4], j5, q[5]], args.speed)
        time.sleep(PERIOD_S)
        fault = arm_fault(piper)
        if fault:
            return "fault", fault
        m = joints_deg(piper)
        amps = currents_a(piper)
        over = [i for i in range(6) if abs(amps[i]) > args.max_current_a[i]]
        below = below + 1 if hang and amps[4] * math.copysign(1, hang) < args.rest_current_a else 0
        why = None
        if t > 0.3 and below >= 2:
            why = f"resting: J5 carries {amps[4]:+.2f} A (was {hang:+.2f} A hanging free)"
        elif over:
            why = "; ".join(f"J{i + 1} drew {amps[i]:.1f} A" for i in over)
        elif abs(m[4] - j5) > 2.0:
            why = f"J5 at {m[4]:.2f} is {abs(m[4] - j5):.1f} deg behind {j5:.2f}"
        elif j5 >= goal and abs(m[4] - goal) <= 0.3:
            why = f"reached J5 = {m[4]:.2f} without J5's current dropping"
        elif t > (goal - q[4]) / args.lower_deg_s + 3:
            why = f"J5 at {m[4]:.2f} didn't reach {goal:.2f}"
        if why:
            print(f"  stopped at J5 = {hold_here(piper, args)[4]:.2f}: {why}", flush=True)
            return why


def trace_loop(piper, path, stop, period_s=0.02):
    """Log the commanded and measured joint angles, the six motor currents and how many motors
    are enabled to CSV at 50 Hz until stop is set."""
    with open(path, "w") as f:
        f.write("t_unix," + ",".join(f"cmd_j{i}" for i in range(1, 7)) + ","
                + ",".join(f"j{i}" for i in range(1, 7)) + ","
                + ",".join(f"current_j{i}_a" for i in range(1, 7)) + ",motors_enabled\n")
        while not stop.is_set():
            hs = piper.GetArmHighSpdInfoMsgs()
            cmd = last_target[0]
            currents = [getattr(hs, f"motor_{i}").current / 1000 for i in range(1, 7)]
            f.write(f"{time.time():.3f},"
                    + (",".join(f"{v:.3f}" for v in cmd) if cmd else ",,,,,") + ","
                    + ",".join(f"{v:.3f}" for v in joints_deg(piper)) + ","
                    + ",".join(f"{v:.3f}" for v in currents)
                    + f",{sum(piper.GetArmEnableStatus())}\n")
            time.sleep(period_s)


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--can", default="can0")
    ap.add_argument("--go", action="store_true", help="enable the motors and move")
    ap.add_argument("--park", action="store_true",
                    help="one cycle only: up, roll the gripper, down, land, disable")
    ap.add_argument("--cycles", type=int, default=3,
                    help="up/down cycles in all; the first rolls the gripper at the top")
    ap.add_argument("--lift-deg", type=float, default=20.0, help="J2 lift (and J3 opening)")
    ap.add_argument("--deg-s", type=float, default=12.0, help="peak joint speed, deg/s")
    ap.add_argument("--speed", type=int, default=15,
                    help="controller MOVE J speed cap, percent (20 was about 35 deg/s in #15)")
    ap.add_argument("--pause-s", type=float, default=1.0, help="dwell at the top and bottom")
    ap.add_argument("--tol-deg", type=float, default=1.0, help="pose reached tolerance")
    ap.add_argument("--lag-deg", type=float, default=4.0,
                    help="stop if any joint is this far from its streamed target")
    ap.add_argument("--max-current-a", default="1.5,3,4,1.5,4.5,1.5",
                    help="stop if a joint draws more than this, J1-J6 in A. The first run "
                         "(#54) peaked at 0.04, 1.1, 2.0, 0.2, 2.7 and 0.45 A while moving "
                         "freely; J6 reached 1.3 A 40 ms into its jam")
    ap.add_argument("--backoff-deg", type=float, default=3.0,
                    help="on a snag, go this far back the way the move came")
    ap.add_argument("--settle-s", type=float, default=3.0,
                    help="time allowed after a profile ends to come within --tol-deg")
    ap.add_argument("--home-tol-deg", type=float, default=6.0,
                    help="J2 and J3 must start this close to 0 (the rest is about -2 and +2)")
    ap.add_argument("--j1-tol-deg", type=float, default=10.0, help="J1 must start this close to 0")
    ap.add_argument("--park-j6-deg", type=float, default=-52.0,
                    help="J6 when parked, J4 held as found. The first run (#54) jammed at "
                         "J6 = -55.0, so the default stops 3 deg short; -90 would be the third "
                         "photo on #54")
    ap.add_argument("--wrist-pitch-deg", type=float, default=0.0,
                    help="pitch of the J5-J6 link (the gripper's axis) whenever the arm moves, "
                         "deg above horizontal: 0 is level, which is J5 = +5 at home")
    ap.add_argument("--no-level", action="store_true",
                    help="keep J5 as found instead (the second run's behaviour)")
    ap.add_argument("--contact-a", type=float, default=0.7,
                    help="once the gripper hangs level, stop if J5 holds less than this much of "
                         "it up (A, against about 1.5 A hanging free)")
    ap.add_argument("--rest-current-a", type=float, default=0.7,
                    help="lowering the gripper at the end, stop once J5 holds less than this")
    ap.add_argument("--lower-deg-s", type=float, default=4.0,
                    help="speed at which J5 lowers the gripper onto its rest at the end")
    ap.add_argument("--rest-j5-deg", type=float,
                    help="J5 with the gripper drooped onto its rest (default: as found when the "
                         "arm starts on its rest, else 23)")
    ap.add_argument("--land-above-deg", type=float, default=0.4,
                    help="before disabling, lower J2 and J3 to this far above the rest they "
                         "started on, so the arm drops only this far")
    ap.add_argument("--no-land", action="store_true",
                    help="leave the firmware limits alone and disable at home (J2 = J3 = 0)")
    ap.add_argument("--camera-up-j6-deg", type=float, default=0.0,
                    help="J6 with the camera on top and the Pi underneath, at home")
    ap.add_argument("--side-tol-deg", type=float, default=50.0,
                    help="parked, the Pi's side must be within this of horizontal")
    ap.add_argument("--trace", metavar="CSV",
                    help="log commanded and measured joints and motor currents at 50 Hz to CSV")
    args = ap.parse_args()

    if args.park:
        args.cycles = 1
    args.max_current_a = [float(v) for v in args.max_current_a.split(",")]
    if len(args.max_current_a) != 6 or not all(0 < v <= 10 for v in args.max_current_a):
        sys.exit("--max-current-a takes six values in (0, 10] A, J1 to J6")
    if not 0 <= args.backoff_deg <= 10:
        sys.exit("--backoff-deg must be in [0, 10]")
    if not 0 < args.lift_deg <= 30:
        sys.exit("--lift-deg must be in (0, 30]")
    if not 1 <= args.deg_s <= 20:
        sys.exit("--deg-s must be in [1, 20]")
    if not 1 <= args.speed <= 30:
        sys.exit("--speed must be in [1, 30]")
    if not 1 <= args.cycles <= 10:
        sys.exit("--cycles must be in [1, 10]")
    if not 0.1 <= args.land_above_deg <= 1.5:
        sys.exit("--land-above-deg must be in [0.1, 1.5]")
    if not -15 <= args.wrist_pitch_deg <= 15:
        sys.exit("--wrist-pitch-deg must be in [-15, 15]")
    if not 1 <= args.lower_deg_s <= 8:
        sys.exit("--lower-deg-s must be in [1, 8]")
    if not 0.2 <= args.contact_a <= args.rest_current_a <= 1.2:
        sys.exit("need 0.2 <= --contact-a <= --rest-current-a <= 1.2")

    state = open(f"/sys/class/net/{args.can}/operstate").read().strip() \
        if os.path.exists(f"/sys/class/net/{args.can}") else "missing"
    if state not in ("up", "unknown"):
        sys.exit(f"{args.can} is {state}; plug in the USB-CAN adapter and bring it up at 1 Mbit/s")

    from piper_sdk import C_PiperInterface_V2

    piper = C_PiperInterface_V2(args.can)
    piper.ConnectPort()
    if not wait_for_feedback(piper):
        sys.exit("no joint feedback on the bus: is the arm powered and wired to the adapter?")
    time.sleep(0.3)  # a few more frames, so the status below is current

    q0 = joints_deg(piper)
    print("joints (deg):", fmt(q0))
    print("enabled:", piper.GetArmEnableStatus())
    print("as found:", describe_pi(q0, args))
    fault = arm_fault(piper)
    if fault:
        sys.exit(f"not moving: {fault}")

    found = q0[3:]

    def lv(q):  # J5 set so the J5-J6 link has --wrist-pitch-deg, unless --no-level
        return list(q) if args.no_level else level(q, args.wrist_pitch_deg)

    start = lv(q0)  # the link leveled where the arm lies
    home0 = lv([q0[0], 0.0, 0.0, *found])  # where it started, raised off the rest
    up0 = lv([q0[0], args.lift_deg, -args.lift_deg, *found])
    up = lv([q0[0], args.lift_deg, -args.lift_deg, found[0], found[1], args.park_j6_deg])
    home = lv([q0[0], 0.0, 0.0, found[0], found[1], args.park_j6_deg])
    if abs(pi_tilt(home, args)) > args.side_tol_deg:
        sys.exit(f"--park-j6-deg {args.park_j6_deg:g} doesn't put the Pi to the side: "
                 f"{describe_pi(home, args)}")

    problems = []
    if abs(q0[0]) > args.j1_tol_deg:
        problems.append(f"J1 is {q0[0]:.1f} deg (limit +/-{args.j1_tol_deg:g})")
    if not (-args.home_tol_deg <= q0[1] <= 45 and -60 <= q0[2] <= args.home_tol_deg):
        problems.append(f"J2/J3 at {q0[1]:.1f}/{q0[2]:.1f} deg is neither the rest nor a pose "
                        "this script raised (J2 up to 45, J3 down to -60)")
    at_rest = q0[1] <= 0 and q0[2] >= 0  # resting below J2's and J3's firmware limits
    land = None
    if not args.no_land and at_rest:
        if q0[1] < -MAX_WIDEN_DEG + 0.5 or q0[2] > MAX_WIDEN_DEG - 0.5:
            problems.append(f"J2/J3 rest at {q0[1]:.2f}/{q0[2]:.2f} deg is further below the "
                            f"limits than the {MAX_WIDEN_DEG:g} deg this script will widen them")
        land = lv([q0[0], min(q0[1] + args.land_above_deg, 0.0),
                   max(q0[2] - args.land_above_deg, 0.0), *home[3:]])
        widen = (min(q0[1] - 0.5, 0.0), max(q0[2] + 0.5, 0.0))
    rest_j5 = args.rest_j5_deg if args.rest_j5_deg is not None else \
        q0[4] if at_rest and q0[4] > 10 else 23.0
    if not 10 <= rest_j5 <= 30:
        problems.append(f"the gripper's rest at J5 = {rest_j5:.1f} isn't the 23-25 deg droop seen "
                        "so far; give --rest-j5-deg")
    if any(not lo <= v <= hi for v, (lo, hi) in zip(found, LIMITS[3:])):
        problems.append(f"J4-J6 at {fmt(found)} are outside the joint limits {LIMITS[3:]}, so "
                        "they can't be held where they are")
    if problems:
        sys.exit("not moving:\n  " + "\n  ".join(problems))

    wrist_parked = abs(q0[5] - args.park_j6_deg) <= args.tol_deg
    leveled = abs(q0[4] - start[4]) <= args.tol_deg
    rise = [b - a for a, b in zip(fk(home0)[1], fk(up0)[1])]
    print("plan, J1 held at", f"{q0[0]:.2f} deg throughout:")
    print(f"  the J5-J6 link is at {wrist_pitch(q0):+.1f} deg now")
    if not leveled:
        print(f"  level {fmt(start)}  J5 only: the link to {wrist_pitch(start):+.1f} deg, lifting "
              "the gripper off its rest")
    print(f"  up    {fmt(up0)}  J2/J3: the wrist rises {rise[2]:.0f} mm and moves "
          f"{rise[0]:.0f} mm forward")
    if not wrist_parked:
        print(f"  then  {fmt(up)}  gripper rolled to J6 = {args.park_j6_deg:g} at the top: "
              f"{describe_pi(up, args)}")
    print(f"  down  {fmt(home)}  link at {wrist_pitch(home):+.1f} deg")
    print(f"  {args.cycles} up/down cycle(s) in all at up to {args.deg_s:g} deg/s")
    if land:
        print(f"  land  {fmt(land)}  {args.land_above_deg:g} deg above the rest; firmware limits "
              f"J2 >= {widen[0]:.1f}, J3 <= {widen[1]:.1f} for the run, back to 0 after")
    else:
        print("  stay at home (--no-land)")
    print(f"  lower the gripper: J5 toward {rest_j5 + 0.5:.1f} at {args.lower_deg_s:g} deg/s until "
          f"it rests ({describe_pi([*home[:4], rest_j5, home[5]], args)}), then disable")
    if not args.go:
        print("read-only run (no --go): nothing sent to the arm")
        return

    stop = threading.Event()
    if args.trace:
        tracer = threading.Thread(target=trace_loop, args=(piper, args.trace, stop), daemon=True)
        tracer.start()
        time.sleep(0.5)  # a little baseline before the motors enable

    if land:
        before = firmware_limits(piper, 2), firmware_limits(piper, 3)
        print("firmware limits J2, J3 (deg):", before, flush=True)
        if before[0] is None or before[1] is None or before[0][0] != 0 or before[1][1] != 0:
            sys.exit("J2/J3 firmware limits aren't the stock 0 deg; not changing them")
        if not set_rest_limits(piper, *widen):
            set_rest_limits(piper, 0.0, 0.0)
            sys.exit("couldn't widen the J2/J3 limits (tried to set them back to 0); nothing moved")
        LIMITS[1] = (widen[0], LIMITS[1][1])
        LIMITS[2] = (LIMITS[2][0], widen[1])
        print(f"firmware limits now J2 >= {widen[0]:.2f}, J3 <= {widen[1]:.2f}", flush=True)

    # Make the current pose the target before enabling, so enabling can't jump to an old one.
    t0 = time.time()
    while True:
        send(piper, q0, args.speed)
        if piper.EnablePiper():
            break
        if time.time() - t0 > 5:
            while piper.DisablePiper() and time.time() - t0 < 8:
                time.sleep(0.01)
            sys.exit("motors did not all enable within 5 s; disabled them again, nothing moved")
        time.sleep(0.01)
    print(f"enabled in {time.time() - t0:.2f} s", flush=True)

    completed, stopped, phase, hang = 0, None, "level", None
    try:
        if not leveled:
            stopped = move(piper, joints_deg(piper), start, args, "level the J5-J6 link")
            if not stopped:
                print(f"  link at {wrist_pitch(joints_deg(piper)):+.1f} deg", flush=True)
                time.sleep(args.pause_s)
        if not stopped:
            hang = hanging_current(piper, args)  # J5 holding the gripper up, hanging free
            print(f"  J5 holds the gripper up with {hang if hang is None else round(hang, 2)} A"
                  + ("" if hang else ": too little to tell, so no check for it resting on "
                     "something"), flush=True)
        for i in range(1, args.cycles + 1):
            if stopped:
                break
            phase = "up"
            stopped = move(piper, joints_deg(piper), up if wrist_parked else up0, args,
                           f"cycle {i}/{args.cycles} up", hang)
            if stopped:
                break
            time.sleep(args.pause_s)
            if not wrist_parked:
                phase = "wrist"
                stopped = move(piper, joints_deg(piper), up, args, "roll the gripper", hang)
                if stopped:
                    break
                wrist_parked = True
                print("  " + describe_pi(joints_deg(piper), args), flush=True)
                time.sleep(args.pause_s)
            phase = "down"
            stopped = move(piper, joints_deg(piper), home, args, f"cycle {i}/{args.cycles} down",
                           hang)
            if stopped:
                break
            completed += 1
            if i < args.cycles:
                time.sleep(args.pause_s)
    except KeyboardInterrupt:
        stopped = ("interrupted", "Ctrl-C")
    finally:
        # Disable only at home: rolled if the gripper got there, else where it started. A snag
        # while leveling leaves the arm on its rest, so the gripper is lowered there instead.
        target = home if wrist_parked else home0
        at_target = stopped is None
        on_rest = bool(stopped) and stopped[0] == "stuck" and phase == "level"
        if stopped:
            kind, why = stopped
            print(f"STOPPED ({phase}, {kind}): {why}", flush=True)
            if kind == "fault":
                print("not commanding anything further", flush=True)
            elif on_rest:
                print("held at", fmt(hold_here(piper, args)), flush=True)
            elif kind == "stuck" and phase in ("up", "wrist"):
                q = hold_here(piper, args)
                print("held at", fmt(q), flush=True)
                back = None
                if phase == "wrist":
                    back = move(piper, q, [*q[:5], found[2]], args, "roll the gripper back")
                    q = joints_deg(piper)
                if back is None:
                    at_target = move(piper, q, target, args, "back down to home") is None
            else:
                print("holding at", fmt(hold_here(piper, args)), flush=True)
        q = joints_deg(piper)
        near = [abs(a - b) for a, b in zip(q, target)]
        if on_rest or (at_target and max(near[1:3]) <= args.home_tol_deg
                       and max(near[3:]) <= args.tol_deg * 2):
            if land and not on_rest:
                low = lv([q0[0], land[1], land[2], *q[3:]])
                slow = argparse.Namespace(**{**vars(args), "deg_s": 2.0})  # last 2 deg slowly
                why = move(piper, q, low, slow, "land on the rest")
                if why:
                    print(f"  landing stopped ({why[1]}); lowering the gripper and disabling here",
                          flush=True)
                q = joints_deg(piper)
            lower_gripper(piper, q, rest_j5, args)
            q = joints_deg(piper)
            t0 = time.time()
            while piper.DisablePiper() and time.time() - t0 < 5:
                time.sleep(0.01)
            print(f"disabled at {fmt(q)}: {describe_pi(q, args)}", flush=True)
            for _ in range(6):
                time.sleep(0.5)
            q_off = q
            q = joints_deg(piper)
            print(f"settled 3 s later at {fmt(q)}: {describe_pi(q, args)}", flush=True)
            print("dropped (deg): " + ", ".join(f"J{i + 1} {b - a:+.2f}"
                                                for i, (a, b) in enumerate(zip(q_off, q))),
                  flush=True)
            if not wrist_parked:
                print("the gripper never got rolled, so the Pi is underneath, as it started",
                      flush=True)
        elif stopped and stopped[0] == "fault":
            print("WARNING: left as the fault left it, last read at", fmt(q), flush=True)
            print("  check the arm and the E-stop before rerunning (--park --go brings a raised "
                  "arm home and lands it)", flush=True)
        else:
            print("WARNING: not back home, so the motors stay on and holding:", fmt(q), flush=True)
            print("  clear whatever stopped it, then rerun with --park --go, or hold the arm "
                  "and use the E-stop", flush=True)
        if land and not any(piper.GetArmEnableStatus()):
            ok = set_rest_limits(piper, 0.0, 0.0)
            print("firmware limits back to J2 >= 0, J3 <= 0:" if ok else
                  "WARNING: couldn't confirm J2/J3 limits are back at 0:",
                  firmware_limits(piper, 2), firmware_limits(piper, 3), flush=True)
        elif land:
            print(f"WARNING: motors still on, so J2/J3 firmware limits left at {widen}; set them "
                  "back to 0 once it's disabled", flush=True)
        print(f"completed {completed}/{args.cycles} cycles", flush=True)
        if args.trace:
            time.sleep(0.5)
            stop.set()
            tracer.join()
            print("trace written to", args.trace, flush=True)
    if stopped:
        sys.exit(1)


if __name__ == "__main__":
    main()
