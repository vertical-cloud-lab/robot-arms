#!/usr/bin/env python3
"""Watch the PiPER's joints while someone moves it by hand, and report each joint's range.

Listen only: the bus is opened with piper_init=False, so nothing is sent to the arm. Power
the arm with its motors off first (`arm_power.py on`), then:

    ~/piper-venv/bin/python joint_watch.py              # until Ctrl-C (or --seconds)

With the motors off the arm is limp and has no brakes: J2 and J3 fall as soon as the arm is
lifted off its rest and let go, so keep a hand on it. Put it back on its rest, with J6 rolled
to about -52, before `arm_power.py off`.

At the end it prints each joint's min and max, saves them to
~/joint_watch_runs/<UTC time>Z.json, and prints an --envelope for follower.py that keeps
--margin degrees inside what was reached.
"""
import argparse
import datetime as dt
import json
import os
import time

NAMES = ["J1", "J2", "J3", "J4", "J5", "J6"]


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--can", default="can0")
    ap.add_argument("--seconds", type=float, default=0, help="stop after this long (0: Ctrl-C)")
    ap.add_argument("--margin", type=float, default=1.0, help="degrees inside the reached range")
    a = ap.parse_args()

    from piper_sdk import C_PiperInterface_V2, LogLevel

    piper = C_PiperInterface_V2(a.can, logger_level=LogLevel.ERROR)
    piper.ConnectPort(piper_init=False)  # listen only: no init queries go out
    time.sleep(1.0)
    lo = hi = None
    t0 = time.time()
    try:
        while not a.seconds or time.time() - t0 < a.seconds:
            msg = piper.GetArmJointMsgs()
            if msg.time_stamp < t0:
                print("\rno joint feedback yet: is the relay on and the E-stop released?", end="",
                      flush=True)
                time.sleep(0.5)
                continue
            js = msg.joint_state
            q = [js.joint_1 / 1000, js.joint_2 / 1000, js.joint_3 / 1000,
                 js.joint_4 / 1000, js.joint_5 / 1000, js.joint_6 / 1000]
            lo = list(q) if lo is None else [min(x, v) for x, v in zip(lo, q)]
            hi = list(q) if hi is None else [max(x, v) for x, v in zip(hi, q)]
            grip = piper.GetArmGripperMsgs().gripper_state.grippers_angle / 1000
            print("\r" + "  ".join(f"{n} {v:7.1f}" for n, v in zip(NAMES, q))
                  + f"  gripper {grip:6.1f} mm   ", end="", flush=True)
            time.sleep(0.1)
    except KeyboardInterrupt:
        pass
    print()
    if lo is None:
        print("no joint feedback, so no ranges")
        return
    out = os.path.expanduser("~/joint_watch_runs")
    os.makedirs(out, exist_ok=True)
    path = os.path.join(out, dt.datetime.now(dt.timezone.utc).strftime("%Y%m%d-%H%M%SZ.json"))
    with open(path, "w") as f:
        json.dump({"min_deg": [round(v, 2) for v in lo], "max_deg": [round(v, 2) for v in hi],
                   "seconds": round(time.time() - t0, 1)}, f)
    print(f"saved {path}")
    print("reached (deg):")
    for n, x, y in zip(NAMES, lo, hi):
        print(f"  {n}  {x:7.1f} .. {y:7.1f}")
    m = a.margin
    env = ",".join(f"{NAMES[i]}={lo[i] + m:.0f}:{hi[i] - m:.0f}" for i in (0, 1, 2, 4, 5)
                   if hi[i] - lo[i] > 2 * m)
    print(f"envelope {m:g} deg inside that (J4 is held, so not in it): --envelope {env}")


if __name__ == "__main__":
    main()
