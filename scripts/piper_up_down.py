#!/usr/bin/env python3
"""Raise and lower the AgileX PiPER a few times, starting and ending at zero.

Runs on the arm Pi, in the venv that has piper_sdk (~/piper-venv):

    ~/piper-venv/bin/python piper_up_down.py           # read-only: print state, move nothing
    ~/piper-venv/bin/python piper_up_down.py --go      # enable motors and move

"Up" is the shoulder (J2) lifting by --lift-deg while the elbow (J3) opens by the same
amount, so the forearm keeps roughly its angle and the whole arm rises. Every other joint
holds zero, or with --hold-wrist holds the angle it started at (the PiPER rests with its
wrist off zero, so this raises the arm without swinging the wrist). can0 must already be up
at 1 Mbit/s; this script never touches the interface.

Safety:
- Without --go nothing is sent to the arm.
- Refuses to start unless joint feedback is live and every joint is within --zero-tol-deg
  of zero (only J2 and J3 with --hold-wrist).
- Waits for each pose to be reached before the next; a pose that is not reached in
  --timeout-s aborts the cycle.
- Always commands the start pose before exiting, and disables the motors only once the arm
  is back there. Disabling elsewhere would drop the arm, so then it is left enabled and
  holding.
"""
import argparse
import os
import sys
import threading
import time

MDEG = 1000  # piper_sdk joint units are 0.001 degree


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


def move_to(piper, target_deg, speed, tol_deg, timeout_s):
    """Stream a MOVE J target until every joint is within tol_deg. Returns True if reached."""
    t0 = time.time()
    while time.time() - t0 < timeout_s:
        piper.MotionCtrl_2(0x01, 0x01, speed, 0x00)
        piper.JointCtrl(*[round(v * MDEG) for v in target_deg])
        q = joints_deg(piper)
        if all(abs(a - b) <= tol_deg for a, b in zip(q, target_deg)):
            print(f"  reached {fmt(target_deg)} in {time.time() - t0:.1f} s", flush=True)
            return True
        time.sleep(0.02)
    print(f"  NOT reached {fmt(target_deg)} after {timeout_s} s, at {fmt(joints_deg(piper))}",
          flush=True)
    return False


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--can", default="can0")
    ap.add_argument("--go", action="store_true", help="enable the motors and move")
    ap.add_argument("--cycles", type=int, default=3)
    ap.add_argument("--lift-deg", type=float, default=25.0, help="J2 lift (and J3 opening)")
    ap.add_argument("--speed", type=int, default=20, help="MOVE J speed percent (1-100)")
    ap.add_argument("--pause-s", type=float, default=0.5, help="dwell at each pose")
    ap.add_argument("--tol-deg", type=float, default=1.5, help="pose reached tolerance")
    ap.add_argument("--zero-tol-deg", type=float, default=5.0, help="start/end zero tolerance")
    ap.add_argument("--timeout-s", type=float, default=15.0, help="per-pose timeout")
    ap.add_argument("--hold-wrist", action="store_true",
                    help="hold J1 and J4-J6 at their starting angles instead of zero")
    ap.add_argument("--trace", metavar="CSV",
                    help="log joint angles and J2/J3 motor speed and current at 100 Hz to CSV")
    args = ap.parse_args()

    if not 0 < args.lift_deg <= 45:
        sys.exit("--lift-deg must be in (0, 45]")
    if not 1 <= args.speed <= 50:
        sys.exit("--speed must be in [1, 50]")

    state = open(f"/sys/class/net/{args.can}/operstate").read().strip() \
        if os.path.exists(f"/sys/class/net/{args.can}") else "missing"
    if state not in ("up", "unknown"):
        sys.exit(f"{args.can} is {state}; bring it up at 1 Mbit/s first")

    from piper_sdk import C_PiperInterface_V2

    piper = C_PiperInterface_V2(args.can)
    piper.ConnectPort()
    if not wait_for_feedback(piper):
        sys.exit("no joint feedback on the bus: is the arm powered and wired to the adapter?")

    q0 = joints_deg(piper)
    print("joints (deg):", fmt(q0))
    print("enabled:", piper.GetArmEnableStatus())
    print(piper.GetArmStatus())
    checked = q0[1:3] if args.hold_wrist else q0
    if any(abs(v) > args.zero_tol_deg for v in checked):
        sys.exit(f"arm is not within {args.zero_tol_deg} deg of zero; not moving")

    home = [q0[0], 0.0, 0.0, *q0[3:]] if args.hold_wrist else [0.0] * 6
    up = [home[0], args.lift_deg, -args.lift_deg, *home[3:]]
    print("home (deg):", fmt(home))
    print("up   (deg):", fmt(up))
    if not args.go:
        print("read-only run (no --go): nothing sent to the arm")
        return

    stop = threading.Event()
    if args.trace:
        tracer = threading.Thread(target=trace_loop, args=(piper, args.trace, stop), daemon=True)
        tracer.start()
        time.sleep(0.5)  # a little baseline before the motors enable

    t0 = time.time()
    while not piper.EnablePiper():
        if time.time() - t0 > 5:
            sys.exit("motors did not enable within 5 s")
        time.sleep(0.01)
    print(f"enabled in {time.time() - t0:.2f} s", flush=True)

    completed = 0
    try:
        for i in range(1, args.cycles + 1):
            print(f"cycle {i}/{args.cycles}: up", flush=True)
            if not move_to(piper, up, args.speed, args.tol_deg, args.timeout_s):
                break
            time.sleep(args.pause_s)
            print(f"cycle {i}/{args.cycles}: down", flush=True)
            if not move_to(piper, home, args.speed, args.tol_deg, args.timeout_s):
                break
            time.sleep(args.pause_s)
            completed += 1
    finally:
        print("returning home", flush=True)
        move_to(piper, home, args.speed, args.tol_deg, args.timeout_s)
        q = joints_deg(piper)
        if all(abs(a - b) <= args.zero_tol_deg for a, b in zip(q, home)):
            t0 = time.time()
            while piper.DisablePiper() and time.time() - t0 < 5:
                time.sleep(0.01)
            print("disabled at home:", fmt(q), flush=True)
        else:
            print("WARNING: not back home, leaving motors enabled so the arm does not drop:",
                  fmt(q), flush=True)
        print(f"completed {completed}/{args.cycles} cycles", flush=True)
        if args.trace:
            time.sleep(0.5)
            stop.set()
            tracer.join()
            print("trace written to", args.trace, flush=True)


if __name__ == "__main__":
    main()
