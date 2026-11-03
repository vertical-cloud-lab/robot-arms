#!/usr/bin/env python3
"""Switch the PiPER's power with the IoT Relay II, and never cut it with the arm up (#57, #59).

Wiring (docs/wiring/README.md): the relay's + is on header pin 11 (GPIO17) of the Pi with the
USB-CAN adapter (rpi-5-mpzy since 2026-10-30), its - on pin 9 (GND), and the arm's power
brick is in one of the relay's normally-OFF outlets. GPIO17 high means the arm has power.
GPIO17 is pulled down at boot, so the arm is off until something switches it on.

The PiPER has no brakes, so cutting its power while the motors hold it up drops it. Power
only goes off once the arm is *parked*:
- all six motor drivers report in, and every one of them is disabled;
- no joint moves during the check;
- every joint is within the home pose ranges in arm_home.json.
For now that's #54's rest pose. When new parts change the pose, edit arm_home.json, not this
script.

    arm_power.py status          what the relay, can0 and the arm report (read-only)
    arm_power.py check           exit 0 if the arm is parked, 1 if not (read-only)
    arm_power.py on              relay on, then wait for the arm to talk on can0
    arm_power.py off             relay off, only if the arm is parked
    arm_power.py run -- PROG [ARGS...]
        The protocol for every program that talks to the arm:
        1. power on if it's off;
        2. run PROG;
        3. power off only if PROG exits 0 *and* the arm is parked.
        Anything else leaves the power on, because the arm may be holding itself up, and
        says why. Park the arm, then run `off`.

A program run this way must exit 0 only once it has left the arm parked and disabled.
Up_and_Down.py works that way: it exits 0 after it lands and disables, and 1 after any stop.

`off --force` skips the parked check. Use it only when a person at the arm can see that it
is resting, or after the E-stop, when the arm can't report.

Run it with the venv that has piper_sdk, so it can read the arm:
    ~/piper-venv/bin/python ~/arm_power.py status
can0 must already be up at 1 Mbit/s; this script never configures it. While reading the
arm it only listens: it opens the bus with piper_init=False, so it sends no frames.

The relay pin keeps its level after this script exits (pinctrl writes the register), so a
crash leaves the power as it was. A reboot or power loss on the Pi itself pulls GPIO17 low
and cuts the arm's power whatever the arm is doing. Neither this script nor the relay can
prevent that.

`run` copies PROG's output to its own output and to ~/arm_power_runs/<UTC time>Z.log. It also
ignores SIGHUP, which PROG inherits. If the SSH session that started it drops, the move
finishes and parks, and the power goes off as usual. Ctrl-C and the E-stop still stop it.
Every switch and refusal is appended to ~/arm_power.log.
"""
import argparse
import contextlib
import datetime as dt
import fcntl
import json
import os
import re
import shlex
import signal
import subprocess
import sys
import time

PIN = 17  # header pin 11
HERE = os.path.dirname(os.path.abspath(__file__))
HOME = os.path.expanduser("~")
EVENT_LOG = os.path.join(HOME, "arm_power.log")
RUN_LOGS = os.path.join(HOME, "arm_power_runs")
LOCK = "/tmp/arm_power.lock"
PINCTRL = os.environ.get("ARM_POWER_PINCTRL", "pinctrl")
PROBE = os.environ.get("ARM_POWER_PROBE")  # tests swap in a simulated arm here

OK, REFUSED, BROKEN = 0, 1, 3  # exit codes (2 is argparse's usage error)


def now():
    return dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def say(*parts):
    """Print, but never let a closed terminal (dropped SSH) raise mid-protocol."""
    with contextlib.suppress(OSError, ValueError):
        print(*parts, flush=True)


def log_event(text):
    with contextlib.suppress(OSError):
        with open(EVENT_LOG, "a") as f:
            f.write(f"{now()} {text}\n")


# ---------------------------------------------------------------- relay (GPIO17)

def pin():
    """(function, level, raw) from `pinctrl get 17`, e.g. ('op', 'hi', '17: op dh pd | hi //…')
    or ('no', '--', …) for the boot default (no function, pulled down)."""
    out = subprocess.run([PINCTRL, "get", str(PIN)], capture_output=True, text=True,
                         check=True).stdout.strip().splitlines()[0]
    left, _, right = out.partition("|")
    func = left.split(":", 1)[1].split()[0]
    level = right.split("//")[0].strip()
    return func, level, out


def relay_is_on():
    func, level, _ = pin()
    return func == "op" and level == "hi"


def set_relay(on):
    subprocess.run([PINCTRL, "set", str(PIN), "op", "dh" if on else "dl"], check=True)
    if relay_is_on() != on:
        raise RuntimeError(f"GPIO{PIN} didn't take: {pin()[2]}")
    log_event(f"relay {'ON' if on else 'OFF'} (GPIO{PIN} {'high' if on else 'low'})")


# ---------------------------------------------------------------- can0 and the arm

def can_state(channel):
    """('up', 'ERROR-ACTIVE', 1000000)-style tuple; ('missing', None, None) without the adapter."""
    path = f"/sys/class/net/{channel}"
    if not os.path.exists(path):
        return "missing", None, None
    with open(path + "/operstate") as f:
        oper = f.read().strip()
    det = subprocess.run(["ip", "-details", "link", "show", channel], capture_output=True,
                         text=True).stdout
    state = re.search(r"can (?:<[^>]*> )?state (\S+)", det)
    rate = re.search(r"bitrate (\d+)", det)
    return oper, state and state.group(1), rate and int(rate.group(1))


def can_ready(channel):
    oper, state, rate = can_state(channel)
    if oper not in ("up", "unknown"):
        return False, (f"{channel} is {oper}: plug the USB-CAN adapter into this Pi, then "
                       f"`sudo ip link set {channel} type can bitrate 1000000 && "
                       f"sudo ip link set {channel} up`")
    if state == "BUS-OFF":
        return False, (f"{channel} is BUS-OFF: `sudo ip link set {channel} down`, then bring "
                       "it up again")
    return True, f"{channel} {oper}, {state or '?'}, {rate or '?'} bit/s"


def _probe(channel, window_s):
    """Listen to the arm for window_s (sends nothing) and print one JSON line: what it said."""
    from piper_sdk import C_PiperInterface_V2, LogLevel

    piper = C_PiperInterface_V2(channel, logger_level=LogLevel.ERROR)
    piper.ConnectPort(piper_init=False)  # listen only: no init queries go out
    t0 = time.time()
    lo, hi, last = [None] * 6, [None] * 6, None
    while time.time() - t0 < window_s:
        time.sleep(0.05)
        j = piper.GetArmJointMsgs()
        if j.time_stamp > t0:
            js = j.joint_state
            last = [js.joint_1 / 1000, js.joint_2 / 1000, js.joint_3 / 1000,
                    js.joint_4 / 1000, js.joint_5 / 1000, js.joint_6 / 1000]
            lo = [v if a is None else min(a, v) for a, v in zip(lo, last)]
            hi = [v if a is None else max(a, v) for a, v in zip(hi, last)]
    ls = piper.GetArmLowSpdInfoMsgs()
    motors = [getattr(ls, f"motor_{i}") for i in range(1, 7)]
    seen = ls.time_stamp > t0
    st = piper.GetArmStatus()
    s = st.arm_status
    out = {
        "frames": last is not None,
        "joints": last,
        "span": None if last is None else [b - a for a, b in zip(lo, hi)],
        # A fresh interface starts every motor at can_id 0, so a set can_id means that driver
        # reported while this probe listened.
        "motors_seen": [seen and m.can_id == 0x260 + i for i, m in enumerate(motors, 1)],
        "enabled": [bool(m.foc_status.driver_enable_status) for m in motors],
        "driver_errors": [[k for k, v in vars(m.foc_status).items()
                           if v and k != "driver_enable_status"] for m in motors],
        "volts": [m.vol / 10 for m in motors],
        "status_seen": st.time_stamp > t0,
        "arm_status": _num(s.arm_status),
        "ctrl_mode": _num(s.ctrl_mode),
        "err_code": _num(s.err_code),
    }
    print(json.dumps(out))


def _num(v):
    try:
        return int(v)
    except (TypeError, ValueError):
        return str(v)


def probe(channel, window_s=1.5):
    """What the arm says over window_s, from a fresh listener in a child process (piper_sdk
    keeps one interface per channel for the life of a process, so a child is the only way to
    be sure nothing stale is read)."""
    cmd = shlex.split(PROBE) if PROBE else [sys.executable, os.path.abspath(__file__)]
    p = subprocess.run(cmd + ["--can", channel, "_probe", "--window", str(window_s)],
                       capture_output=True, text=True, timeout=window_s + 30)
    lines = [ln for ln in p.stdout.splitlines() if ln.startswith("{")]
    if p.returncode or not lines:
        raise RuntimeError(f"couldn't read the arm (exit {p.returncode}): "
                           f"{(p.stderr or p.stdout).strip()[-400:]}")
    return json.loads(lines[-1])


def load_home(path):
    with open(path) as f:
        cfg = json.load(f)
    ranges = [tuple(cfg["joint_ranges_deg"][f"J{i}"]) for i in range(1, 7)]
    if any(len(r) != 2 or r[0] > r[1] for r in ranges):
        raise ValueError(f"{path}: each joint range must be [low, high] in degrees")
    return ranges, float(cfg.get("still_deg", 0.3)), cfg.get("name", path)


def not_parked(s, home):
    """Reasons the arm isn't safe to power down (an empty list means it is)."""
    ranges, still, _ = home
    if not s["frames"]:
        return ["the arm isn't sending joint feedback: no power, the E-stop, or can0 not reaching it"]
    why = []
    missing = [i for i, ok in enumerate(s["motors_seen"], 1) if not ok]
    if missing:
        why.append("no driver status from " + ", ".join(f"J{i}" for i in missing)
                   + ", so it can't confirm they're disabled")
    on = [i for i, (ok, en) in enumerate(zip(s["motors_seen"], s["enabled"]), 1) if ok and en]
    if on:
        why.append("motors still enabled: " + ", ".join(f"J{i}" for i in on))
    for i, (v, (lo, hi)) in enumerate(zip(s["joints"], ranges), 1):
        if not lo <= v <= hi:
            why.append(f"J{i} is at {v:.1f} deg, outside home's {lo:g} to {hi:g}")
    moving = [f"J{i} ({sp:.2f} deg)" for i, sp in enumerate(s["span"], 1) if sp > still]
    if moving:
        why.append("still moving: " + ", ".join(moving))
    return why


def fmt(q):
    return "[" + ", ".join(f"{v:7.2f}" for v in q) + "]"


def report(s, home):
    if not s["frames"]:
        say("arm: silent (no joint feedback)")
        return
    say("arm joints (deg):", fmt(s["joints"]))
    say("motors enabled:  ", s["enabled"], "" if all(s["motors_seen"]) else
        f"(heard from {sum(s['motors_seen'])}/6 drivers)")
    errs = {f"J{i}": e for i, e in enumerate(s["driver_errors"], 1) if e}
    say(f"arm status {s['arm_status']}, ctrl mode {s['ctrl_mode']}, err code {s['err_code']}"
        + (f", driver flags {errs}" if errs else ""))
    why = not_parked(s, home)
    say("parked: yes, safe to power down" if not why else
        "parked: NO, so the power must stay on:\n  " + "\n  ".join(why))


# ---------------------------------------------------------------- the commands

@contextlib.contextmanager
def exclusive(what, wait=False):
    """One arm_power at a time, so nothing switches the power off under a running program."""
    f = open(LOCK, "a+")
    try:
        fcntl.flock(f, fcntl.LOCK_EX | (0 if wait else fcntl.LOCK_NB))
    except BlockingIOError:
        f.seek(0)
        holder = f.read().strip() or "another arm_power"
        f.close()
        raise SystemExit(f"refused: {holder} is running; wait for it to finish")
    f.seek(0)
    f.truncate()
    f.write(f"{what} (pid {os.getpid()}, since {now()})")
    f.flush()
    try:
        yield
    finally:
        fcntl.flock(f, fcntl.LOCK_UN)
        f.close()


def cmd_status(a, home):
    func, level, raw = pin()
    on = func == "op" and level == "hi"
    say(f"relay: {'ON' if on else 'off'}  ({raw})")
    ready, msg = can_ready(a.can)
    say("can:", msg)
    say("home pose:", home[2])
    if not ready:
        return OK
    s = probe(a.can)
    report(s, home)
    if s["frames"] and not on:
        say("WARNING: the arm has power with the relay off. Its brick isn't in a normally-OFF "
            "outlet, or the relay's + isn't on GPIO17.")
    if on and not s["frames"]:
        say("NOTE: relay on but the arm is silent: still booting, E-stop pressed, brick "
            "unplugged, or the CAN cable")
    return OK


def cmd_check(a, home):
    ready, msg = can_ready(a.can)
    if not ready:
        say("can't check:", msg)
        return REFUSED
    s = probe(a.can)
    report(s, home)
    return OK if not not_parked(s, home) else REFUSED


def wait_for_arm(a, timeout_s):
    """Seconds until the arm first talks after power-on, or None."""
    t0 = time.time()
    while time.time() - t0 < timeout_s:
        if probe(a.can, 0.5)["frames"]:
            return time.time() - t0
    return None


def wait_for_silence(a, timeout_s):
    t0 = time.time()
    while time.time() - t0 < timeout_s:
        if not probe(a.can, 0.5)["frames"]:
            return time.time() - t0
    return None


def power_on(a, home):
    ready, msg = can_ready(a.can)
    if not ready and not a.no_can:
        say("refused:", msg)
        log_event(f"on refused: {msg}")
        return REFUSED
    if relay_is_on():
        say("relay already on")
        if a.no_can:
            return OK
        s = probe(a.can)
        report(s, home)
        return OK if s["frames"] else BROKEN
    if not a.no_can and probe(a.can)["frames"]:
        say("refused: the arm already has power with the relay off, so the relay doesn't "
            "control it (brick not in a normally-OFF outlet, or + not on GPIO17)")
        log_event("on refused: arm powered with the relay off")
        return REFUSED
    set_relay(True)
    say(f"relay ON at {now()}")
    if a.no_can:
        say("--no-can: not waiting for the arm")
        return OK
    t = wait_for_arm(a, a.boot_timeout_s)
    if t is None:
        # Nobody can have commanded an arm that never talked, so it is disabled: safe to cut.
        set_relay(False)
        say(f"the arm didn't talk within {a.boot_timeout_s:g} s, so the relay is back off. "
            "Check the brick is in a normally-OFF outlet, the E-stop is released, and the "
            "CAN cable")
        log_event(f"on: no arm feedback in {a.boot_timeout_s:g} s, relay back off")
        return BROKEN
    s = probe(a.can)
    say(f"arm talking {t:.1f} s after the relay switched on")
    report(s, home)
    log_event(f"on: arm talking after {t:.1f} s, enabled {s['enabled']}")
    return OK


def power_off(a, home, force=False):
    ready, msg = can_ready(a.can)
    if not relay_is_on():
        if ready and probe(a.can)["frames"]:
            say("relay is already off, but the arm still has power: its brick isn't on a "
                "normally-OFF outlet, or + isn't on GPIO17")
            return BROKEN
        say("relay already off")
        return OK
    if not force:
        if not ready:
            say(f"refused: can't see the arm ({msg}), so I can't tell it's parked. "
                "Relay stays on. If a person can see it resting: `off --force`")
            log_event(f"off refused: {msg}")
            return REFUSED
        s = probe(a.can)
        why = not_parked(s, home)
        if why:
            report(s, home)
            say("refused: relay stays on")
            log_event("off refused: " + "; ".join(why))
            return REFUSED
        say("parked:", fmt(s["joints"]), "all motors disabled")
    else:
        say("--force: not checking that the arm is parked")
    set_relay(False)
    say(f"relay OFF at {now()}" + (" (forced)" if force else ""))
    if not ready:
        return OK
    t = wait_for_silence(a, a.off_timeout_s)
    if t is None:
        say(f"WARNING: the arm is still talking {a.off_timeout_s:g} s after the relay went "
            "off: the relay isn't switching its brick")
        log_event("off: arm still powered after the relay went off")
        return BROKEN
    say(f"arm silent {t:.1f} s after the relay switched off: power is off")
    log_event(f"off{' (forced)' if force else ''}: arm silent after {t:.1f} s")
    return OK


def cmd_on(a, home):
    with exclusive("arm_power on"):
        return power_on(a, home)


def cmd_off(a, home):
    with exclusive("arm_power off"):
        return power_off(a, home, a.force)


def cmd_run(a, home):
    prog = a.prog[1:] if a.prog[:1] == ["--"] else a.prog
    if not prog:
        raise SystemExit("run needs a program: arm_power.py run -- PROG [ARGS...]")
    signal.signal(signal.SIGHUP, signal.SIG_IGN)  # inherited by PROG: see the docstring
    with exclusive("arm_power run " + shlex.join(prog)):
        ready, msg = can_ready(a.can)
        if not ready:
            say("refused before switching anything:", msg)
            log_event(f"run refused: {msg}")
            return REFUSED
        rc = power_on(a, home)
        if rc != OK:
            return rc
        os.makedirs(RUN_LOGS, exist_ok=True)
        path = os.path.join(RUN_LOGS, dt.datetime.now(dt.timezone.utc).strftime("%Y%m%d-%H%M%S.%f")[:-3]
                        + "Z.log")
        say(f"running {shlex.join(prog)}  (output also in {path})")
        log_event(f"run start: {shlex.join(prog)} -> {path}")
        interrupted = False
        with open(path, "w") as log:
            log.write(f"# {now()} arm_power run: {shlex.join(prog)}\n")
            child = subprocess.Popen(prog, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                     bufsize=0)
            # Ctrl-C reaches PROG directly (same process group) and PROG decides how to stop.
            # This process waits for it either way, then checks the arm.
            signal.signal(signal.SIGINT, lambda *_: None)
            while True:
                chunk = child.stdout.read1(4096) if hasattr(child.stdout, "read1") \
                    else child.stdout.read(4096)
                if not chunk:
                    break
                log.write(chunk.decode(errors="replace"))
                log.flush()
                with contextlib.suppress(OSError, ValueError):
                    sys.stdout.buffer.write(chunk)
                    sys.stdout.flush()
            prc = child.wait()
            log.write(f"# {now()} exit {prc}\n")
        say(f"{prog[0]} exited {prc}")
        log_event(f"run end: exit {prc}")
        time.sleep(a.settle_s)  # let a just-disabled arm come to rest
        s = probe(a.can)
        report(s, home)
        why = not_parked(s, home)
        if a.leave_on:
            say("--leave-on: relay stays on")
            return OK if prc == 0 else prc
        if prc != 0 or why:
            say("NOT powering off: " + ("; ".join(
                ([f"{prog[0]} exited {prc}, not 0"] if prc else []) + why)))
            say("The relay stays on. Park the arm (e.g. Up_and_Down.py --park --go), "
                "then `arm_power.py off`.")
            log_event("run: left ON: " + "; ".join(([f"exit {prc}"] if prc else []) + why))
            return prc or REFUSED
        return power_off(a, home)


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0],
                                 formatter_class=argparse.RawDescriptionHelpFormatter,
                                 epilog="See the module docstring for the protocol.")
    ap.add_argument("--can", default="can0")
    ap.add_argument("--home", default=os.path.join(HERE, "arm_home.json"),
                    help="home pose ranges (default: arm_home.json next to this script)")
    ap.add_argument("--boot-timeout-s", type=float, default=20.0,
                    help="how long to wait for the arm to talk after power-on")
    ap.add_argument("--off-timeout-s", type=float, default=10.0,
                    help="how long to wait for the arm to go silent after power-off")
    ap.add_argument("--settle-s", type=float, default=1.0,
                    help="pause after PROG exits before checking the arm")
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("status")
    sub.add_parser("check")
    p_on = sub.add_parser("on")
    p_on.add_argument("--no-can", action="store_true",
                      help="switch the relay without watching for the arm (lamp test)")
    p_off = sub.add_parser("off")
    p_off.add_argument("--force", action="store_true",
                       help="skip the parked check: only with a person watching the arm rest")
    p_run = sub.add_parser("run")
    p_run.add_argument("--leave-on", action="store_true",
                       help="don't power off afterwards (another program follows)")
    p_run.add_argument("prog", nargs=argparse.REMAINDER)
    p_probe = sub.add_parser("_probe")  # internal: the listener child process
    p_probe.add_argument("--window", type=float, default=1.5)
    a = ap.parse_args()
    if a.cmd == "_probe":
        _probe(a.can, a.window)
        return
    a.no_can = getattr(a, "no_can", False)
    home = load_home(a.home)
    cmds = {"status": cmd_status, "check": cmd_check, "on": cmd_on, "off": cmd_off,
            "run": cmd_run}
    sys.exit(cmds[a.cmd](a, home))


if __name__ == "__main__":
    main()
