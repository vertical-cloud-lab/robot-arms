#!/usr/bin/env python3
"""Run arm_power.py against a simulated relay and arm: no Pi, no CAN adapter, no piper_sdk.

    python3 "PiPER Sandbox Scripts/test_arm_power.py"

The relay is a fake `pinctrl` (the real script's own parsing and read-back are exercised).
The arm is a JSON file that the fake probe reads and the fake programs write: it has power
only while GPIO17 is high (unless a test wires it around the relay), it talks once it has
had power for boot_s, and its pose and motor states are whatever the last program left.
"""
import argparse
import importlib.util
import json
import os
import sys
import tempfile
import time

HERE = os.path.dirname(os.path.abspath(__file__))
SIM = tempfile.mkdtemp(prefix="arm_power_sim_")
PIN_FILE, ARM_FILE = os.path.join(SIM, "pin.json"), os.path.join(SIM, "arm.json")
PARKED = [-1.2, -2.0, 2.1, 0.5, 24.0, -52.0]

FAKE_PINCTRL = f"""#!{sys.executable}
import json, os, sys, time
st = json.load(open({PIN_FILE!r})) if os.path.exists({PIN_FILE!r}) else {{"func": "no", "level": "--"}}
a = sys.argv[1:]
if a == ["get", "17"]:
    drive = {{"hi": "dh", "lo": "dl"}}.get(st["level"], "  ") if st["func"] == "op" else "  "
    name = "output" if st["func"] == "op" else "none"
    print(f"17: {{st['func']}} {{drive}} pd | {{st['level']}} // GPIO17 = {{name}}")
elif a[:3] == ["set", "17", "op"] and a[3:] in (["dh"], ["dl"]):
    json.dump({{"func": "op", "level": "hi" if a[3] == "dh" else "lo", "since": time.time()}},
              open({PIN_FILE!r}, "w"))
else:
    sys.exit("fake pinctrl: unsupported " + " ".join(a))
"""

FAKE_PROG = f"""#!{sys.executable}
import json, os, sys
# usage: fake_prog.py EXIT_CODE [JSON updates to the arm]
arm = json.load(open({ARM_FILE!r}))
pin = json.load(open({PIN_FILE!r})) if os.path.exists({PIN_FILE!r}) else {{"level": "--"}}
arm["relay_during_prog"] = pin["level"]
if len(sys.argv) > 2:
    arm.update(json.loads(sys.argv[2]))
json.dump(arm, open({ARM_FILE!r}, "w"))
print("fake program ran, relay", pin["level"])
sys.exit(int(sys.argv[1]))
"""


def write(path, text, mode=0o755):
    with open(path, "w") as f:
        f.write(text)
    os.chmod(path, mode)
    return path


def load_module():
    spec = importlib.util.spec_from_file_location("arm_power", os.path.join(HERE, "arm_power.py"))
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    m.PINCTRL = write(os.path.join(SIM, "pinctrl"), FAKE_PINCTRL)
    m.EVENT_LOG = os.path.join(SIM, "arm_power.log")
    m.RUN_LOGS = os.path.join(SIM, "runs")
    m.LOCK = os.path.join(SIM, "arm_power.lock")
    m.can_state = lambda ch: (arm()["can"], "ERROR-ACTIVE", 1000000) if arm()["can"] != "missing" \
        else ("missing", None, None)
    m.probe = sim_probe
    m.say = lambda *p: SAID.append(" ".join(str(x) for x in p))
    return m


SAID = []


def arm():
    with open(ARM_FILE) as f:
        return json.load(f)


def sim_probe(channel, window_s=1.5):
    time.sleep(0.02)
    a = arm()
    pin = json.load(open(PIN_FILE)) if os.path.exists(PIN_FILE) else {"level": "--", "since": 0}
    powered = {"relay": pin["level"] == "hi", "always": True, "never": False}[a["power"]]
    talking = powered and (a["power"] == "always" or time.time() - pin["since"] >= a["boot_s"])
    if not talking:
        return {"frames": False, "joints": None, "span": None, "motors_seen": [False] * 6,
                "enabled": [False] * 6, "driver_errors": [[]] * 6, "volts": [0] * 6,
                "status_seen": False, "arm_status": 0, "ctrl_mode": 0, "err_code": 0}
    return {"frames": True, "joints": a["joints"], "span": [a.get("span", 0.0)] * 6,
            "motors_seen": a.get("motors_seen", [True] * 6), "enabled": a["enabled"],
            "driver_errors": [[]] * 6, "volts": [24.0] * 6, "status_seen": True,
            "arm_status": 0, "ctrl_mode": 1, "err_code": 0}


def reset(pin_level="--", **arm_state):
    state = {"power": "relay", "boot_s": 0.2, "can": "up", "joints": PARKED,
             "enabled": [False] * 6}
    state.update(arm_state)
    json.dump(state, open(ARM_FILE, "w"))
    func = "no" if pin_level == "--" else "op"
    json.dump({"func": func, "level": pin_level, "since": time.time() - 60}, open(PIN_FILE, "w"))
    SAID.clear()


def args(**kw):
    base = dict(can="can0", boot_timeout_s=2.0, off_timeout_s=2.0, settle_s=0.0, no_can=False,
                force=False, leave_on=False, prog=[])
    base.update(kw)
    return argparse.Namespace(**base)


def relay(m):
    return "on" if m.relay_is_on() else "off"


def main():
    m = load_module()
    home = m.load_home(os.path.join(HERE, "arm_home.json"))
    prog = write(os.path.join(SIM, "fake_prog.py"), FAKE_PROG)
    results = []

    def case(name, got, want, relay_now, relay_want, extra=True):
        ok = got == want and relay_now == relay_want and extra
        results.append(ok)
        print(f"{'PASS' if ok else 'FAIL'}  {name}: exit {got} (want {want}), relay {relay_now} "
              f"(want {relay_want})")
        if not ok:
            print("      said:", *SAID, sep="\n        ")

    # Parsing of the boot default, as read on mpzy on 2026-11-03.
    reset()
    case("boot default pin reads as off", 0, 0, relay(m), "off")

    # 1. on: the arm talks after boot_s.
    reset()
    case("on, arm boots", m.cmd_on(args(), home), m.OK, relay(m), "on")

    # 2. on, but the arm never talks: relay goes back off, exit 3.
    reset(power="never")
    case("on, arm silent -> relay back off", m.cmd_on(args(), home), m.BROKEN, relay(m), "off")

    # 3. on refused when the arm already has power with the relay off.
    reset(power="always")
    case("on refused: arm powered around the relay", m.cmd_on(args(), home), m.REFUSED,
         relay(m), "off")

    # 4. on refused without can0, but --no-can (lamp test) switches anyway.
    reset(can="missing")
    case("on refused without can0", m.cmd_on(args(), home), m.REFUSED, relay(m), "off")
    reset(can="missing")
    case("on --no-can (lamp test)", m.cmd_on(args(no_can=True), home), m.OK, relay(m), "on")

    # 5. off when parked: relay off, arm goes silent.
    reset("hi")
    case("off when parked", m.cmd_off(args(), home), m.OK, relay(m), "off")

    # 6. off refused: motors enabled / J6 not parked / still moving / a driver not heard.
    for name, state in [("motors enabled", {"enabled": [True] * 6}),
                        ("J6 at -23 (turned by hand)", {"joints": PARKED[:5] + [-23.4]}),
                        ("J2 raised 20 deg", {"joints": [-1.2, 20, -20, 0.5, 5, -52]}),
                        ("still moving", {"span": 1.0}),
                        ("J4's driver silent", {"motors_seen": [True] * 3 + [False] + [True] * 2})]:
        reset("hi", **state)
        case(f"off refused: {name}", m.cmd_off(args(), home), m.REFUSED, relay(m), "on")

    # 7. off refused when the arm can't report (E-stop: no feedback), --force overrides.
    reset("hi", power="never")
    case("off refused: arm silent (E-stop?)", m.cmd_off(args(), home), m.REFUSED, relay(m), "on")
    reset("hi", power="never")
    case("off --force", m.cmd_off(args(force=True), home), m.OK, relay(m), "off")

    # 8. off when the relay doesn't control the arm: exit 3.
    reset("hi", power="always")
    case("off: arm still powered after relay off", m.cmd_off(args(), home), m.BROKEN, relay(m),
         "off")

    # 9. run: program parks and exits 0 -> power on during the program, off afterwards.
    reset(joints=PARKED[:5] + [-23.4])  # starts with J6 turned back, as after #54 run 4
    rc = m.cmd_run(args(prog=["--", prog, "0", json.dumps({"joints": PARKED})]), home)
    case("run: exit 0 and parked -> off", rc, m.OK, relay(m), "off",
         arm()["relay_during_prog"] == "hi")

    # 10. run: program exits 1 although parked -> stays on.
    reset()
    rc = m.cmd_run(args(prog=["--", prog, "1"]), home)
    case("run: exit 1 -> stays on", rc, 1, relay(m), "on")

    # 11. run: program exits 0 but leaves the motors enabled up in the air -> stays on.
    reset()
    rc = m.cmd_run(args(prog=["--", prog, "0", json.dumps(
        {"enabled": [True] * 6, "joints": [-1.2, 20, -20, 0.5, 5, -52]})]), home)
    case("run: exit 0 but holding up -> stays on", rc, m.REFUSED, relay(m), "on")

    # 12. run with the relay already on (arm already up and parked): no second power-on.
    reset("hi")
    rc = m.cmd_run(args(prog=["--", prog, "0"]), home)
    case("run with relay already on", rc, m.OK, relay(m), "off")

    # 13. run refused without can0, before switching anything.
    reset(can="missing")
    rc = m.cmd_run(args(prog=["--", prog, "0"]), home)
    case("run refused without can0", rc, m.REFUSED, relay(m), "off",
         "relay_during_prog" not in arm())

    # 14. run --leave-on.
    reset()
    rc = m.cmd_run(args(leave_on=True, prog=["--", prog, "0"]), home)
    case("run --leave-on", rc, m.OK, relay(m), "on")

    # 15. a second arm_power can't switch the power off under a running one.
    reset("hi")
    with m.exclusive("arm_power run (test)"):
        try:
            m.cmd_off(args(), home)
            got = "not refused"
        except SystemExit as e:
            got = "refused" if "running" in str(e) else str(e)
    case("off refused while a run holds the lock", got, "refused", relay(m), "on")

    # 16. the event log and the run log were written.
    logs = os.listdir(m.RUN_LOGS)
    case("run logs written", len(logs) >= 3, True, relay(m), "on",
         os.path.getsize(m.EVENT_LOG) > 0)

    print(f"\n{sum(results)}/{len(results)} passed")
    sys.exit(0 if all(results) else 1)


if __name__ == "__main__":
    main()
