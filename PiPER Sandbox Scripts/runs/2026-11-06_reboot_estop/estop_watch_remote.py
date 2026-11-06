import json, subprocess, time, datetime as dt, os
H = os.path.expanduser("~")
PY = f"{H}/piper-venv/bin/python"
def ts(): return dt.datetime.now(dt.timezone.utc).strftime("%H:%M:%S.%f")[:-4]
def probe():
    p = subprocess.run([PY, f"{H}/arm_power.py", "_probe", "--window", "0.5"], capture_output=True, text=True, timeout=30)
    ln = [l for l in p.stdout.splitlines() if l.startswith("{")]
    return json.loads(ln[-1]) if ln else None
def status():
    print(subprocess.run([PY, f"{H}/arm_power.py", "status"], capture_output=True, text=True).stdout, flush=True)
print(ts(), "arm_power on:", flush=True)
r = subprocess.run([PY, f"{H}/arm_power.py", "on"], capture_output=True, text=True)
print(r.stdout, r.stderr, "exit", r.returncode, flush=True)
if r.returncode != 0:
    raise SystemExit(5)
t0 = time.time(); prev = None; phase = "wait_press"; silent_n = talk_n = 0; t_silent = None
while time.time() - t0 < 900:
    s = probe()
    talking = bool(s and s["frames"])
    if talking != prev:
        print(ts(), "TALKING" if talking else "SILENT", "" if not talking else f"enabled={s['enabled']} joints={[round(v,2) for v in s['joints']]}", flush=True)
        prev = talking
    if phase == "wait_press":
        silent_n = silent_n + 1 if not talking else 0
        if silent_n == 2:
            t_silent = ts(); print(t_silent, "E-STOP DETECTED (silent twice). status:", flush=True); status(); phase = "wait_release"
    elif phase == "wait_release":
        talk_n = talk_n + 1 if talking else 0
        if talk_n == 3:
            print(ts(), "RELEASED: arm talking again. status:", flush=True); status(); break
    if int(time.time() - t0) % 60 < 2:
        print(ts(), "...", phase, flush=True)
else:
    print(ts(), "TIMEOUT in phase", phase, flush=True)
