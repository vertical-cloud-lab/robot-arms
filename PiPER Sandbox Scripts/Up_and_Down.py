#!/usr/bin/env python3
"""Raise and lower the PiPER without letting the gripper Pi's power cord reach J2 (#54).

The gripper Pi hangs under the gripper when the camera is on top (J6 near zero), with its
USB-C power plug facing back toward J2. Disabling the motors there lets the arm drop onto its
rest and the plug lands on J2's housing. Rolled 90 degrees, with the Pi to one side (the third
photo on #54), the arm drops clear. This script keeps it rolled the whole time:

- It starts only from that pose: the Pi's side of the gripper within --side-tol-deg of
  horizontal (either side), J2 and J3 within --home-tol-deg of home, J1 within --j1-tol-deg of 0.
- It holds J1 and J4-J6 at the angles it starts with. The Pi never swings under the wrist and
  the cord never bends at the wrist; only J2 and J3 move.
- "Up" lifts J2 by --lift-deg and opens J3 by the same angle, so the forearm keeps its pitch:
  the wrist rises (94 mm for 20 degrees) and moves 30 mm forward, J1 fixed, so nothing swings
  sideways. "Down" is home, J2 = J3 = 0, never lower.
- Every move follows a smooth profile that peaks at --deg-s (10 deg/s is about 3 s each way),
  streamed at 50 Hz; the controller's own speed is capped at --speed percent as well.
- If a joint falls more than --lag-deg behind its target (a snag) on the way up, it goes back
  down to home. If that happens on the way down, or the arm reports an error, or feedback stops
  (power cut), it stops commanding motion and says so.
- It ends at home with the wrist still rolled and disables only there, so the arm drops just
  the couple of degrees onto its rest, Pi to the side. If it can't get home, it leaves the
  motors on and holding, and says so.

Runs on the arm Pi, in the venv that has piper_sdk (~/piper-venv). can0 must already be up at
1 Mbit/s; this script never touches the interface.

    ~/piper-venv/bin/python Up_and_Down.py            # read-only: check the pose, print the plan
    ~/piper-venv/bin/python Up_and_Down.py --go       # enable the motors and move
    ~/piper-venv/bin/python Up_and_Down.py --park --go
        # from a raised pose (an interrupted run): only bring J2/J3 home, then disable
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
# the arm rests just outside J2's and J3's (about -2 and +2.4 deg), so targets are clamped here.
LIMITS = [(-150, 150), (0, 180), (-170, 0), (-100, 100), (-70, 70), (-120, 120)]

# piper_sdk's DH table (C_PiperForwardKinematics, dh_is_offset=1): modified DH, mm and degrees.
DH = [  # a, alpha, theta offset, d
    (0, 0, 0, 123),
    (0, -90, -172.22, 0),
    (285.03, 0, -102.78, 0),
    (-21.98, 90, 0, 250.75),
    (0, -90, 0, 0),
    (0, 90, 0, 91),
]


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
    piper.MotionCtrl_2(0x01, 0x01, speed, 0x00)  # CAN control, MOVE J, speed percent
    piper.JointCtrl(*[round(v * MDEG) for v in clamp(target_deg)])


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


def move(piper, start, goal, args, label):
    """Stream a smooth move from start to goal. Returns None once there, else why it stopped:
    ("fault", text) if the arm reported a problem or went quiet, ("stuck", text) if a joint
    fell behind its target or didn't arrive."""
    span = max(abs(b - a) for a, b in zip(start, goal))
    duration = max(math.pi / 2 * span / args.deg_s, 0.3)  # raised cosine peaks at pi/2 x mean
    print(f"{label}: {fmt(goal)} over {duration:.1f} s", flush=True)
    t0 = time.time()
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
        lag = [abs(a - b) for a, b in zip(q, target)]
        worst = max(range(6), key=lambda i: lag[i])
        if lag[worst] > args.lag_deg:
            return "stuck", (f"J{worst + 1} at {q[worst]:.2f} deg is {lag[worst]:.1f} deg from "
                           f"its target {target[worst]:.2f}; all joints {fmt(q)}")
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


def trace_loop(piper, path, stop, period_s=0.01):
    """Log feedback joint angles and J2/J3 motor speed and current to CSV until stop is set."""
    with open(path, "w") as f:
        f.write("t_unix,j1,j2,j3,j4,j5,j6,j2_speed_rad_s,j3_speed_rad_s,j2_current_a,j3_current_a\n")
        while not stop.is_set():
            hs = piper.GetArmHighSpdInfoMsgs()
            m2, m3 = hs.motor_2, hs.motor_3
            f.write(f"{time.time():.3f}," + ",".join(f"{v:.3f}" for v in joints_deg(piper))
                    + f",{m2.motor_speed / 1000:.3f},{m3.motor_speed / 1000:.3f}"
                    + f",{m2.current / 1000:.3f},{m3.current / 1000:.3f}\n")
            time.sleep(period_s)


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--can", default="can0")
    ap.add_argument("--go", action="store_true", help="enable the motors and move")
    ap.add_argument("--park", action="store_true",
                    help="no cycles: from a raised pose, bring J2/J3 home and disable")
    ap.add_argument("--cycles", type=int, default=2)
    ap.add_argument("--lift-deg", type=float, default=20.0, help="J2 lift (and J3 opening)")
    ap.add_argument("--deg-s", type=float, default=10.0, help="peak joint speed, deg/s")
    ap.add_argument("--speed", type=int, default=15,
                    help="controller MOVE J speed cap, percent (20 was about 35 deg/s in #15)")
    ap.add_argument("--pause-s", type=float, default=1.0, help="dwell at the top and bottom")
    ap.add_argument("--tol-deg", type=float, default=1.0, help="pose reached tolerance")
    ap.add_argument("--lag-deg", type=float, default=4.0,
                    help="stop if any joint is this far from its streamed target")
    ap.add_argument("--settle-s", type=float, default=3.0,
                    help="time allowed after a profile ends to come within --tol-deg")
    ap.add_argument("--home-tol-deg", type=float, default=6.0,
                    help="J2 and J3 must start this close to 0 (the rest is about -2 and +2.4)")
    ap.add_argument("--j1-tol-deg", type=float, default=10.0, help="J1 must start this close to 0")
    ap.add_argument("--camera-up-j6-deg", type=float, default=0.0,
                    help="J6 with the camera on top and the Pi underneath, at home")
    ap.add_argument("--side-tol-deg", type=float, default=30.0,
                    help="the Pi's side must start within this of horizontal")
    ap.add_argument("--trace", metavar="CSV",
                    help="log joint angles and J2/J3 motor speed and current at 100 Hz to CSV")
    args = ap.parse_args()

    if args.park:
        args.cycles = 0
    if not 0 < args.lift_deg <= 30:
        sys.exit("--lift-deg must be in (0, 30]")
    if not 1 <= args.deg_s <= 20:
        sys.exit("--deg-s must be in [1, 20]")
    if not 1 <= args.speed <= 30:
        sys.exit("--speed must be in [1, 30]")
    if not 0 <= args.cycles <= 10:
        sys.exit("--cycles must be in [0, 10]")

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
    fault = arm_fault(piper)
    if fault:
        sys.exit(f"not moving: {fault}")

    # Where is the Pi? Its side must face sideways, not down at J2 (or up, which puts the
    # camera bracket underneath instead).
    pi = pi_direction(q0, args.camera_up_j6_deg)
    tilt = math.degrees(math.asin(max(-1.0, min(1.0, pi[2]))))
    side = "the arm's left (+y)" if pi[1] > 0 else "the arm's right (-y)"
    print(f"Pi side of the gripper points to {side}, {abs(tilt):.0f} deg "
          f"{'below' if tilt < 0 else 'above'} horizontal")
    problems = []
    if abs(tilt) > args.side_tol_deg:
        problems.append(f"the Pi is {abs(tilt):.0f} deg {'below' if tilt < 0 else 'above'} "
                        f"horizontal (limit {args.side_tol_deg:g}): roll the gripper so the Pi "
                        "is to the side, as in the third photo on #54")
    if abs(q0[0]) > args.j1_tol_deg:
        problems.append(f"J1 is {q0[0]:.1f} deg (limit +/-{args.j1_tol_deg:g})")
    if args.park:
        if not (-args.home_tol_deg <= q0[1] <= 45 and -60 <= q0[2] <= args.home_tol_deg):
            problems.append(f"J2/J3 at {q0[1]:.1f}/{q0[2]:.1f} deg is not a raised pose this "
                            "script made (J2 0..45, J3 -60..0)")
    elif any(abs(v) > args.home_tol_deg for v in q0[1:3]):
        problems.append(f"J2/J3 at {q0[1]:.1f}/{q0[2]:.1f} deg, not within "
                        f"{args.home_tol_deg:g} deg of home")
    if problems:
        sys.exit("not moving:\n  " + "\n  ".join(problems))

    if any(not lo <= v <= hi for i, (v, (lo, hi)) in enumerate(zip(q0, LIMITS)) if i not in (1, 2)):
        sys.exit(f"not moving: J1 or J4-J6 is outside the joint limits {LIMITS}, so it can't "
                 "be held where it is")

    home = [q0[0], 0.0, 0.0, *q0[3:]]
    up = [q0[0], args.lift_deg, -args.lift_deg, *q0[3:]]
    print("home (deg):", fmt(home), "  J1 and J4-J6 held as they are now")
    if args.cycles:
        rise = [b - a for a, b in zip(fk(home)[1], fk(up)[1])]
        print("up   (deg):", fmt(up))
        print(f"the wrist moves {rise[2]:.0f} mm up and {rise[0]:.0f} mm forward between them")
    print(f"{args.cycles} cycle(s) at up to {args.deg_s:g} deg/s, then disable at home")
    if not args.go:
        print("read-only run (no --go): nothing sent to the arm")
        return

    stop = threading.Event()
    if args.trace:
        tracer = threading.Thread(target=trace_loop, args=(piper, args.trace, stop), daemon=True)
        tracer.start()
        time.sleep(0.5)  # a little baseline before the motors enable

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

    completed, stopped, phase = 0, None, "start"
    try:
        stopped = move(piper, joints_deg(piper), home, args, "to home")
        for i in range(1, args.cycles + 1):
            if stopped:
                break
            time.sleep(args.pause_s)
            phase = "up"
            stopped = move(piper, joints_deg(piper), up, args, f"cycle {i}/{args.cycles} up")
            if stopped:
                break
            time.sleep(args.pause_s)
            phase = "down"
            stopped = move(piper, joints_deg(piper), home, args, f"cycle {i}/{args.cycles} down")
            if not stopped:
                completed += 1
    except KeyboardInterrupt:
        stopped = ("interrupted", "Ctrl-C")
    finally:
        # Disable only at home. Stuck on the way up: go back down first. Stuck on the way
        # down, or interrupted: hold, since something may be under the arm. Stuck leaving the
        # rest (park excepted): it's still about where it rested, so disabling is safe.
        at_home = stopped is None
        if stopped:
            kind, why = stopped
            print(f"STOPPED ({phase}, {kind}): {why}", flush=True)
            if kind == "fault":
                print("not commanding anything further", flush=True)
            elif kind == "stuck" and phase == "up":
                q = hold_here(piper, args)
                print("held at", fmt(q), "; going back down to home", flush=True)
                at_home = move(piper, q, home, args, "back to home") is None
            elif kind == "stuck" and phase == "start" and not args.park:
                at_home = True
            else:
                print("holding at", fmt(hold_here(piper, args)), flush=True)
        q = joints_deg(piper)
        near = [abs(a - b) for a, b in zip(q, home)]
        if at_home and max(near[1:3]) <= args.home_tol_deg and max(near[3:]) <= args.tol_deg * 2:
            t0 = time.time()
            while piper.DisablePiper() and time.time() - t0 < 5:
                time.sleep(0.01)
            time.sleep(1.0)
            print("disabled at home, Pi to the side:", fmt(q), flush=True)
            print("resting at:", fmt(joints_deg(piper)), flush=True)
        elif stopped and stopped[0] == "fault":
            print("WARNING: left as the fault left it, last read at", fmt(q), flush=True)
            print("  check the arm and the E-stop before rerunning (--park --go brings a raised "
                  "arm home)", flush=True)
        else:
            print("WARNING: not back home, so the motors stay on and holding:", fmt(q), flush=True)
            print("  clear whatever stopped it, then rerun with --park --go, or hold the arm "
                  "and use the E-stop", flush=True)
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
