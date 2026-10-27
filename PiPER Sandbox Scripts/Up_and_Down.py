#!/usr/bin/env python3
"""Move the AgileX PiPER arm up and down, starting and ending at its folded rest pose.

Runs on the arm Pi, in the venv that has piper_sdk 0.6.2 (~/piper-venv):

    ~/piper-venv/bin/python Up_and_Down.py          # dry run: listen to the arm, print the plan
    ~/piper-venv/bin/python Up_and_Down.py --go     # turn the motors on and move

"Up" lifts the shoulder (J2) by --lift-deg and opens the elbow (J3) by the same angle, so the
forearm keeps its angle and the wrist rises: about 116 mm, and 43 mm further out, at the
default 25 deg. "Down" takes J2 and J3 back to zero, the rest pose. J1 and the wrist (J4-J6)
hold the angles they started at. can0 must already be up at 1 Mbit/s; this script never
touches the interface.

Safety:
- Without --go the script only listens: it sends nothing on the CAN bus.
- It refuses to move unless the arm's feedback is live, the arm reports NORMAL with no error
  flags, the motors are off (so no other program is driving it), and J2 and J3 are within
  --rest-tol-deg of zero.
- Each pose must be reached before the next is sent. One that isn't reached within
  --timeout-s ends the cycles early.
- However the run ends (finished, Ctrl+C, a closed terminal, `kill`, an error), it sends the
  arm back to rest, and turns the motors off only once the arm is there. Turning them off
  anywhere else would drop the arm, so then it leaves them on and holding. Ctrl+C during
  that return is ignored.
- Software is not an emergency stop: someone should be able to reach the arm's power switch.
"""
import argparse
import math
import signal
import sys
import time

MDEG = 1000  # piper_sdk reports and takes joint angles in 0.001 degree


def log(*args):
    """print() that keeps going if the terminal or SSH session has gone away."""
    try:
        print(*args, flush=True)
    except OSError:
        pass


def fmt(q):
    return "[" + ", ".join(f"{v:7.2f}" for v in q) + "]"


def joints_deg(piper):
    js = piper.GetArmJointMsgs().joint_state
    return [js.joint_1 / MDEG, js.joint_2 / MDEG, js.joint_3 / MDEG,
            js.joint_4 / MDEG, js.joint_5 / MDEG, js.joint_6 / MDEG]


def wait_until(pred, timeout_s):
    t0 = time.time()
    while time.time() - t0 < timeout_s:
        if pred():
            return True
        time.sleep(0.05)
    return False


def move_to(piper, target, speed, tol_deg, timeout_s):
    """Keep sending a joint (MOVE J) target until every joint is within tol_deg of it.

    Returns True once the arm is there, False if it still isn't after timeout_s.
    """
    t0 = time.time()
    while time.time() - t0 < timeout_s:
        piper.MotionCtrl_2(0x01, 0x01, speed, 0x00)  # CAN control, MOVE J, speed %, not MIT
        piper.JointCtrl(*[round(v * MDEG) for v in target])
        if all(abs(a - b) <= tol_deg for a, b in zip(joints_deg(piper), target)):
            log(f"  reached {fmt(target)} in {time.time() - t0:.1f} s")
            return True
        time.sleep(0.02)
    log(f"  NOT reached {fmt(target)} after {timeout_s:.0f} s, at {fmt(joints_deg(piper))}")
    return False


def interrupt(signum, frame):
    # Closing the terminal (SIGHUP) or `kill` (SIGTERM) then ends the run the way Ctrl+C
    # does: through the finally: block that takes the arm back to rest.
    raise KeyboardInterrupt(signal.Signals(signum).name)


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--go", action="store_true", help="turn the motors on and move")
    ap.add_argument("--can", default="can0", help="SocketCAN interface (default can0)")
    ap.add_argument("--cycles", type=int, default=3, help="up/down cycles (default 3, max 20)")
    ap.add_argument("--lift-deg", type=float, default=25.0,
                    help="J2 lift and J3 opening in deg (default 25, max 45)")
    ap.add_argument("--speed", type=int, default=20,
                    help="MOVE J speed in %% (default 20, max 50)")
    ap.add_argument("--pause-s", type=float, default=0.5, help="dwell at each pose (default 0.5)")
    ap.add_argument("--tol-deg", type=float, default=1.5,
                    help="how close counts as having reached a pose (default 1.5)")
    ap.add_argument("--rest-tol-deg", type=float, default=5.0,
                    help="how close J2 and J3 must be to zero to count as at rest (default 5)")
    ap.add_argument("--timeout-s", type=float, default=15.0, help="per-pose timeout (default 15)")
    args = ap.parse_args()

    if not 0 < args.lift_deg <= 45:
        sys.exit("--lift-deg must be in (0, 45]")
    if not 1 <= args.speed <= 50:
        sys.exit("--speed must be in [1, 50]")
    if not 1 <= args.cycles <= 20:
        sys.exit("--cycles must be in [1, 20]")

    try:
        state = open(f"/sys/class/net/{args.can}/operstate").read().strip()
    except OSError:
        state = "missing"
    if state not in ("up", "unknown"):
        sys.exit(f"{args.can} is {state}; bring it up at 1 Mbit/s first")

    from piper_sdk import C_PiperForwardKinematics, C_PiperInterface_V2

    # Step 1: connect. piper_init=False skips the SDK's start-up queries, so until the motors
    # are turned on the script only listens to the feedback the arm broadcasts.
    piper = C_PiperInterface_V2(args.can)
    piper.ConnectPort(piper_init=False)
    if not wait_until(lambda: piper.GetArmJointMsgs().Hz > 0 and piper.GetArmStatus().Hz > 0
                      and piper.GetArmLowSpdInfoMsgs().Hz > 0, 3.0):
        sys.exit("no feedback on the bus: is the arm powered and wired to the adapter?")

    # Step 2: read where the arm is and whether it is healthy.
    q0 = joints_deg(piper)
    st = piper.GetArmStatus().arm_status
    flags = [name for name, bad in vars(st.err_status).items() if bad]
    motors_on = piper.GetArmEnableStatus()
    log("joints (deg):", fmt(q0))
    log(f"arm status: {st.arm_status}, control mode: {st.ctrl_mode}, error code: {st.err_code},"
        f" error flags: {', '.join(flags) or 'none'}")
    log("motors on:", motors_on)

    # Step 3: plan the two poses. Only J2 and J3 move; every other joint holds where it is.
    rest = [q0[0], 0.0, 0.0, *q0[3:]]
    up = [q0[0], args.lift_deg, -args.lift_deg, *q0[3:]]
    fk = C_PiperForwardKinematics()
    (x0, y0, z0), (x1, y1, z1) = [fk.CalFK([math.radians(v) for v in q])[5][:3]
                                  for q in (rest, up)]
    log("rest (deg):  ", fmt(rest))
    log("up   (deg):  ", fmt(up))
    log(f"at 'up' the wrist is {z1 - z0:.0f} mm higher and"
        f" {math.hypot(x1, y1) - math.hypot(x0, y0):.0f} mm further out than at rest")

    problems = []
    if st.arm_status != 0 or st.err_code or flags:
        problems.append("the arm reports a fault")
    if any(motors_on):
        problems.append("the motors are already on (is another program driving the arm?)")
    if abs(q0[1]) > args.rest_tol_deg or abs(q0[2]) > args.rest_tol_deg:
        problems.append(f"J2 and J3 are not within {args.rest_tol_deg} deg of zero,"
                        " so the arm is not at rest")
    if problems:
        sys.exit("not moving: " + "; ".join(problems))
    if not args.go:
        log("dry run (no --go): nothing was sent to the arm")
        return 0

    signal.signal(signal.SIGHUP, interrupt)
    signal.signal(signal.SIGTERM, interrupt)
    completed = 0
    try:
        # Step 4: turn the motors on. EnablePiper() sends the enable command each call and
        # returns True once the feedback shows all six motors on.
        t0 = time.time()
        if not wait_until(piper.EnablePiper, 5.0):
            raise RuntimeError("the motors did not all turn on within 5 s")
        log(f"motors on after {time.time() - t0:.2f} s")

        # Step 5: up and down.
        for i in range(1, args.cycles + 1):
            log(f"cycle {i}/{args.cycles}: up")
            if not move_to(piper, up, args.speed, args.tol_deg, args.timeout_s):
                break
            time.sleep(args.pause_s)
            log(f"cycle {i}/{args.cycles}: down")
            if not move_to(piper, rest, args.speed, args.tol_deg, args.timeout_s):
                break
            time.sleep(args.pause_s)
            completed += 1
    except (KeyboardInterrupt, RuntimeError) as stop:
        log(f"stopping: {str(stop) or 'Ctrl+C'}")
    finally:
        # Step 6: end at rest, and only turn the motors off there. A second Ctrl+C, a dropped
        # SSH session or another `kill` must not cut this short and leave the motors on.
        for s in (signal.SIGINT, signal.SIGHUP, signal.SIGTERM):
            signal.signal(s, signal.SIG_IGN)
        if all(piper.GetArmEnableStatus()):
            log("returning to rest")
            move_to(piper, rest, args.speed, args.tol_deg, args.timeout_s)
        q = joints_deg(piper)
        if abs(q[1]) <= args.rest_tol_deg and abs(q[2]) <= args.rest_tol_deg:
            t0 = time.time()
            while piper.DisablePiper() and time.time() - t0 < 5:
                time.sleep(0.01)
            if any(piper.GetArmEnableStatus()):
                log("WARNING: at rest, but the motors still report on:", fmt(q))
            else:
                log("motors off at rest:", fmt(q))
        else:
            log("WARNING: not back at rest, so the motors stay on to hold the arm up:", fmt(q))
        log(f"completed {completed}/{args.cycles} cycles")
    return 0 if completed == args.cycles else 1


if __name__ == "__main__":
    sys.exit(main())
