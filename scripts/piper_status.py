#!/usr/bin/env python3
"""Print the PiPER's protection settings and driver status, without moving or changing anything.

Runs on the arm Pi, in the venv that has piper_sdk (~/piper-venv):

    ~/piper-venv/bin/python piper_status.py

Shows what decides how the arm reacts when it is blocked: each joint's collision protection
level (0 means no collision detection), each driver's fault flags (under-voltage,
over-current, motor and driver over-temperature, collision, stall), the temperatures, and the
arm status code.

The only frames it sends are queries: ConnectPort's limit and firmware queries, and 0x477 with
Byte 0 = 0x02 (query collision protection level). It never enables the motors, commands
motion, or writes a setting. can0 must already be up at 1 Mbit/s; this script never touches
the interface.
"""
import argparse
import os
import sys
import time

FLAGS = ["voltage_too_low", "motor_overheating", "driver_overcurrent", "driver_overheating",
         "collision_status", "driver_error_status", "stall_status"]


def wait_for(pred, timeout_s=3.0):
    t0 = time.time()
    while time.time() - t0 < timeout_s:
        if pred():
            return True
        time.sleep(0.05)
    return False


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--can", default="can0")
    args = ap.parse_args()

    state = open(f"/sys/class/net/{args.can}/operstate").read().strip() \
        if os.path.exists(f"/sys/class/net/{args.can}") else "missing"
    if state not in ("up", "unknown"):
        sys.exit(f"{args.can} is {state}; bring it up at 1 Mbit/s first")

    from piper_sdk import C_PiperInterface_V2

    piper = C_PiperInterface_V2(args.can)
    piper.ConnectPort()
    if not wait_for(lambda: piper.GetArmLowSpdInfoMsgs().Hz > 0):
        sys.exit("no driver feedback on the bus: is the arm powered and wired to the adapter?")

    # Query only: param_setting, 0x48X feedback and end load are left at "no change".
    def crash_levels():
        piper.ArmParamEnquiryAndConfig(param_enquiry=0x02)
        time.sleep(0.05)
        return piper.GetCrashProtectionLevelFeedback().time_stamp > 0
    have_crash = wait_for(crash_levels)
    time.sleep(0.5)  # let a few more feedback frames arrive

    print("firmware:", piper.GetPiperFirmwareVersion())
    st = piper.GetArmStatus().arm_status
    print(f"ctrl mode: {st.ctrl_mode}  arm status: {st.arm_status}  motion: {st.motion_status}"
          f"  err code: {st.err_code}")
    errs = [k for k, v in vars(st.err_status).items() if v]
    print("err flags:", ", ".join(errs) or "none")

    js = piper.GetArmJointMsgs().joint_state
    q = [js.joint_1, js.joint_2, js.joint_3, js.joint_4, js.joint_5, js.joint_6]
    print("joints (deg):", "[" + ", ".join(f"{v / 1000:7.2f}" for v in q) + "]")

    if have_crash:
        c = piper.GetCrashProtectionLevelFeedback().crash_protection_level_feedback
        levels = [getattr(c, f"joint_{i}_protection_level") for i in range(1, 7)]
        print("collision protection level J1-J6:", levels, "(0 = no collision detection)")
    else:
        print("collision protection level: no reply to the 0x477 query")

    low = piper.GetArmLowSpdInfoMsgs()
    print("joint  volts  driver_C  motor_C  enabled  faults")
    for i in range(1, 7):
        m = getattr(low, f"motor_{i}")
        faults = [f for f in FLAGS if getattr(m.foc_status, f)]
        print(f"J{i}  {m.vol / 10:9.1f}  {m.foc_temp:8d}  {m.motor_temp:7d}"
              f"  {str(m.foc_status.driver_enable_status):>7}  {', '.join(faults) or 'none'}")


if __name__ == "__main__":
    main()
