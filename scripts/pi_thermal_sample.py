#!/usr/bin/env python3
"""Sample a table Pi's temperature, clock, fan and CPU use for a while, read-only.

Runs on the Pi with the system python3 (stdlib only) and prints one JSON object:

    ssh … 'python3 - --seconds 30' < scripts/pi_thermal_sample.py > eufi.json

Every second it records the SoC and PMIC temperatures, the measured ARM clock,
`vcgencmd get_throttled`, the fan's speed and PWM, and the PMIC's rail powers.
Around that window it reads /proc for the CPU time of every process and of every
thread of the picam-stream units (#61), so the window's CPU can be split between
capture (rpicam-vid), face blurring (device.py) and encoding/sending (ffmpeg). It
also reports each stream process's average CPU since it started, systemd's CPU
total per unit, and the 2-minute "fps out" lines the streams logged recently.

It needs no root, writes nothing, never opens a camera and never touches a
service. It prints no hostname, no command line and nothing from broadcast.json:
process names come from /proc/<pid>/comm only.
"""

import argparse
import glob
import json
import os
import re
import subprocess
import time

CLK = os.sysconf("SC_CLK_TCK")
STREAM_UNIT = re.compile(r"^picam-stream(@[A-Za-z0-9_]+)?\.service$")


def read(path, default=None):
    try:
        with open(path) as f:
            return f.read().strip()
    except OSError:
        return default


def run(*args, timeout=10):
    try:
        r = subprocess.run(args, capture_output=True, text=True, timeout=timeout)
        return r.stdout.strip() if r.returncode == 0 else None
    except (OSError, subprocess.TimeoutExpired):
        return None


def vcgencmd(*args):
    return run("vcgencmd", *args, timeout=5)


def number(text, pattern):
    m = re.search(pattern, text or "")
    return float(m.group(1)) if m else None


def pmic():
    """Rail currents and voltages from the Pi 5 PMIC, and their product in W."""
    out = vcgencmd("pmic_read_adc")
    if not out:
        return None
    amps, volts = {}, {}
    for line in out.splitlines():
        m = re.match(r"\s*(\S+)_A current\(\d+\)=([\d.]+)A", line)
        if m:
            amps[m.group(1)] = float(m.group(2))
        m = re.match(r"\s*(\S+)_V volt\(\d+\)=([\d.]+)V", line)
        if m:
            volts[m.group(1)] = float(m.group(2))
    rails = {k: amps[k] * volts[k] for k in amps if k in volts}
    return {
        "core_w": rails.get("VDD_CORE"),
        "rails_w": sum(rails.values()) if rails else None,
        "ext5v_v": volts.get("EXT5V"),
    }


def fan():
    hw = sorted(glob.glob("/sys/devices/platform/cooling_fan/hwmon/hwmon*"))
    if not hw:
        return {"rpm": None, "pwm": None}
    rpm, pwm = read(hw[0] + "/fan1_input"), read(hw[0] + "/pwm1")
    return {"rpm": int(rpm) if rpm else None, "pwm": int(pwm) if pwm else None}


def cooling_state():
    for dev in sorted(glob.glob("/sys/class/thermal/cooling_device*")):
        if read(dev + "/type") == "pwm-fan":
            return int(read(dev + "/cur_state", "-1")), int(read(dev + "/max_state", "-1"))
    return None, None


def sample(t0):
    temp = read("/sys/class/thermal/thermal_zone0/temp")
    state, _ = cooling_state()
    return {
        "t": round(time.time() - t0, 2),
        "utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "soc_c": int(temp) / 1000 if temp else None,
        "vc_soc_c": number(vcgencmd("measure_temp"), r"temp=([\d.]+)"),
        "pmic_c": number(vcgencmd("measure_temp", "pmic"), r"temp=([\d.]+)"),
        "arm_mhz": (number(vcgencmd("measure_clock", "arm"), r"=(\d+)") or 0) / 1e6 or None,
        "throttled": (vcgencmd("get_throttled") or "").replace("throttled=", "") or None,
        "fan_level": state,
        **fan(),
        **(pmic() or {}),
    }


def cpu_stat():
    """Aggregate /proc/stat jiffies: user nice system idle iowait irq softirq steal."""
    with open("/proc/stat") as f:
        parts = f.readline().split()
    names = ["user", "nice", "system", "idle", "iowait", "irq", "softirq", "steal"]
    return dict(zip(names, map(int, parts[1:9])))


def stat_fields(path):
    s = read(path)
    if not s:
        return None
    r = s.rfind(")")
    return s[s.find("(") + 1 : r], s[r + 2 :].split()


def unit_of(pid):
    for line in (read(f"/proc/{pid}/cgroup") or "").splitlines():
        if line.startswith("0::"):
            return line[3:].rsplit("/", 1)[-1]
    return None


def processes():
    """{pid: (comm, cpu jiffies, start jiffies, unit, role)} for every process."""
    out = {}
    for pid in filter(str.isdigit, os.listdir("/proc")):
        got = stat_fields(f"/proc/{pid}/stat")
        if not got:
            continue
        comm, f = got
        unit = unit_of(pid)
        role = None
        if unit and STREAM_UNIT.match(unit):
            if comm.startswith("rpicam"):
                role = "capture (rpicam-vid)"
            elif comm == "ffmpeg":
                role = "encode + send (ffmpeg)"
            elif comm.startswith("python"):
                try:
                    with open(f"/proc/{pid}/cmdline", "rb") as fh:
                        cmd = fh.read()
                except OSError:
                    cmd = b""
                role = "face blur etc. (device.py)" if b"device.py" in cmd else "other python"
            else:
                role = "other"
        out[int(pid)] = (comm, int(f[11]) + int(f[12]), int(f[19]), unit, role)
    return out


def threads(pid):
    out = {}
    for task in glob.glob(f"/proc/{pid}/task/*"):
        got = stat_fields(task + "/stat")
        if got:
            tid = int(task.rsplit("/", 1)[-1])
            out[tid] = (got[0], int(got[1][11]) + int(got[1][12]))
    return out


def uptime():
    return float(read("/proc/uptime").split()[0])


def unit_info():
    names = run("systemctl", "list-units", "--all", "--type=service", "--no-legend", "--plain",
                "picam-stream.service", "picam-stream@*.service") or ""
    units = {}
    for line in names.splitlines():
        p = line.split()
        if len(p) < 4 or not STREAM_UNIT.match(p[0]):
            continue
        props = run("systemctl", "show", p[0], "-p", "CPUUsageNSec", "-p", "ActiveEnterTimestamp",
                    "-p", "ActiveEnterTimestampMonotonic", "-p", "NRestarts", "-p", "CPUQuotaPerSecUSec",
                    "-p", "Nice") or ""
        d = dict(kv.split("=", 1) for kv in props.splitlines() if "=" in kv)
        info = {"active": p[2], "sub": p[3], **d}
        try:
            since = int(d["ActiveEnterTimestampMonotonic"]) / 1e6
            used = int(d["CPUUsageNSec"]) / 1e9
            info["hours_active"] = round((time.monotonic() - since) / 3600, 2)
            info["avg_cores_since_start"] = round(used / (time.monotonic() - since), 3)
        except (KeyError, ValueError, ZeroDivisionError):
            pass
        units[p[0]] = info
    return units


def journal_fps(hours):
    """The streams' 2-minute lines: time, unit, fps out and slowest frame. Nothing else."""
    out = run("journalctl", "-u", "picam-stream*", "--since", f"-{hours}h", "-o", "json",
              "--output-fields=MESSAGE,_SYSTEMD_UNIT", timeout=60)
    rows = []
    for line in (out or "").splitlines():
        try:
            e = json.loads(line)
        except ValueError:
            continue
        msg = e.get("MESSAGE")
        if not isinstance(msg, str) or " fps out, " not in msg:
            continue
        fps = number(msg, r"^([\d.]+) fps out")
        slow = number(msg, r"slowest frame (\d+) ms")
        ts = int(e["__REALTIME_TIMESTAMP"]) / 1e6
        rows.append([round(ts), e.get("_SYSTEMD_UNIT"), fps, slow])
    return rows


def kernel_alerts():
    out = run("journalctl", "-k", "-b", "-o", "json", "--output-fields=MESSAGE", timeout=60)
    hits = []
    for line in (out or "").splitlines():
        try:
            e = json.loads(line)
        except ValueError:
            continue
        msg = e.get("MESSAGE")
        if isinstance(msg, str) and re.search(r"(?i)voltage|thermal|throttl|overheat|temperature", msg):
            hits.append([round(int(e["__REALTIME_TIMESTAMP"]) / 1e6), msg[:160]])
    return {"count": len(hits), "first": hits[:5], "last": hits[-5:]}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seconds", type=int, default=30)
    ap.add_argument("--journal-hours", type=int, default=16)
    a = ap.parse_args()

    trips = []
    for tp in sorted(glob.glob("/sys/class/thermal/thermal_zone0/trip_point_*_temp")):
        base = tp[: -len("_temp")]
        trips.append({"type": read(base + "_type"), "c": int(read(tp)) / 1000,
                      "hyst_c": int(read(base + "_hyst", "0")) / 1000})
    config = {}
    for line in (vcgencmd("get_config", "int") or "").splitlines():
        k, _, v = line.partition("=")
        if re.search(r"temp|arm_freq|fan|over_voltage|turbo", k):
            config[k] = v
    with open("/proc/stat") as f:
        btime = int(next(l for l in f if l.startswith("btime")).split()[1])
    _, max_state = cooling_state()
    static = {
        "model": (read("/proc/device-tree/model") or "").rstrip("\x00"),
        "mem_total_kb": int(re.search(r"MemTotal:\s+(\d+)", read("/proc/meminfo")).group(1)),
        "kernel": os.uname().release,
        "boot_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(btime)),
        "uptime_h": round(uptime() / 3600, 2),
        "trip_points": trips,
        "fan_max_level": max_state,
        "vc_config": config,
        "cpus": os.cpu_count(),
        "max_mhz": int(read("/sys/devices/system/cpu/cpu0/cpufreq/cpuinfo_max_freq", "0")) / 1000,
        "governor": read("/sys/devices/system/cpu/cpu0/cpufreq/scaling_governor"),
        "loadavg_start": read("/proc/loadavg"),
    }

    t0 = time.time()
    up0, cpu0, procs0 = uptime(), cpu_stat(), processes()
    stream_pids = [p for p, v in procs0.items() if v[4]]
    thr0 = {p: threads(p) for p in stream_pids}
    samples = []
    for i in range(a.seconds + 1):
        samples.append(sample(t0))
        if i < a.seconds:
            time.sleep(max(0.0, t0 + i + 1 - time.time()))
    up1, cpu1, procs1 = uptime(), cpu_stat(), processes()
    thr1 = {p: threads(p) for p in stream_pids}
    dt = up1 - up0

    total = {k: (cpu1[k] - cpu0[k]) / CLK / dt for k in cpu0}
    busy = sum(v for k, v in total.items() if k not in ("idle", "iowait"))
    per_proc = []
    for pid, (comm, used1, start, unit, role) in procs1.items():
        if pid not in procs0 or procs0[pid][2] != start:
            continue
        cores = (used1 - procs0[pid][1]) / CLK / dt
        age = up1 - start / CLK
        entry = {"pid": pid, "comm": comm, "unit": unit, "role": role, "cores": round(cores, 3)}
        if role:
            entry["hours_running"] = round(age / 3600, 2)
            entry["avg_cores_since_start"] = round(used1 / CLK / age, 3) if age > 0 else None
            entry["threads"] = sorted(
                ({"tid": tid, "comm": c, "main": tid == pid,
                  "cores": round((u - thr0[pid].get(tid, (c, u))[1]) / CLK / dt, 3)}
                 for tid, (c, u) in thr1.get(pid, {}).items()),
                key=lambda x: -x["cores"])
        per_proc.append(entry)
    per_proc.sort(key=lambda x: -x["cores"])

    print(json.dumps({
        "static": static,
        "window_s": round(dt, 2),
        "samples": samples,
        "cpu_cores": {k: round(v, 3) for k, v in total.items()},
        "cpu_busy_cores": round(busy, 3),
        "stream_procs": [p for p in per_proc if p["role"]],
        "top_procs": [{k: p[k] for k in ("comm", "unit", "role", "cores")} for p in per_proc[:12]],
        "units": unit_info(),
        "fps_log": journal_fps(a.journal_hours),
        "kernel_alerts": kernel_alerts(),
        "loadavg_end": read("/proc/loadavg"),
    }))


if __name__ == "__main__":
    main()
