"""Bring up AMP's robot server (harness amp1_basic, unchanged) and the PiPER link client, then
select a task episode and wait until it is ready for the agent.

python stack.py up            # server + link client, in the background (logs in RUN/)
python stack.py select TASK K # queue episode K of TASK and wait for "ready"
python stack.py state         # the server's api/state
python stack.py down
"""

from __future__ import annotations

import json
import os
import signal
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

HERE = Path(__file__).resolve().parent
AMP = Path(os.environ.get("AMP_ROOT", "/tmp/ext/ml-amp"))
PY = str(AMP / ".venv/bin/python")
RUN = Path(os.environ.get("PIPER_RUN_DIR", "/tmp/amp-run"))
PORT = int(os.environ.get("PIPER_SERVER_PORT", "8765"))
URL = f"http://127.0.0.1:{PORT}"


def env() -> dict:
    e = dict(os.environ)
    e.update(PYTHONPATH=f"{AMP / 'src'}:{HERE}", MUJOCO_GL="egl", PYOPENGL_PLATFORM="egl",
             OMP_NUM_THREADS="2")
    return e


def http(method: str, path: str, body: dict | None = None, timeout: float = 30.0) -> dict:
    data = None if body is None else json.dumps(body).encode()
    req = urllib.request.Request(f"{URL}/{path}", data=data, method=method,
                                 headers={"content-type": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as r:  # noqa: S310
        return json.loads(r.read())


def up() -> None:
    RUN.mkdir(parents=True, exist_ok=True)
    sys.path.insert(0, str(AMP / "src"))
    from amp.eval.robolab_slot import server_config
    cfg = server_config("amp1_basic", port=PORT, state_dir=str(RUN / "state"),
                        results_dir=str(RUN / "results"))
    (RUN / "server.json").write_text(json.dumps(cfg, indent=1))
    srv = subprocess.Popen([PY, "-m", "amp.robot_server", "--config", str(RUN / "server.json")],
                           stdout=open(RUN / "server.log", "a"), stderr=subprocess.STDOUT,
                           env=env(), start_new_session=True)
    for _ in range(120):
        try:
            http("GET", "api/state", timeout=2)
            break
        except OSError:
            time.sleep(0.5)
    link = subprocess.Popen([PY, str(HERE / "piper_link.py"), "--server", URL, "--output-dir",
                             str(RUN / "bench")], stdout=open(RUN / "link.log", "a"),
                            stderr=subprocess.STDOUT, env=env(), start_new_session=True)
    (RUN / "pids.json").write_text(json.dumps({"server": srv.pid, "link": link.pid}))
    for _ in range(120):
        st = http("GET", "api/state")
        if st.get("sim_connected") or st.get("link", {}).get("connected") or \
                "hello ok" in (RUN / "link.log").read_text():
            break
        time.sleep(0.5)
    print(json.dumps({"server": URL, "pids": json.loads((RUN / "pids.json").read_text())}))


def select(task: str, k: int, timeout_s: float = 300.0) -> None:
    print(json.dumps(http("POST", "api/tasks/select", {"task": task, "episode": k})))
    t0 = time.time()
    last = None
    while time.time() - t0 < timeout_s:
        try:
            st = http("GET", "api/state")
        except OSError as exc:
            st = {"error": str(exc)}
        state = (st.get("mode"), st.get("episode"), st.get("task"))
        if state != last:
            print("state:", state, flush=True)
            last = state
        if st.get("episode") is not None and st.get("mode") not in ("no_sim", "loading", None):
            return
        time.sleep(1.0)
    raise SystemExit("episode not ready in time")


def down() -> None:
    pids = json.loads((RUN / "pids.json").read_text())
    for name, pid in pids.items():
        try:
            os.killpg(pid, signal.SIGTERM)
        except ProcessLookupError:
            pass
        print("stopped", name, pid)


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "state"
    if cmd == "up":
        up()
    elif cmd == "select":
        select(sys.argv[2], int(sys.argv[3]) if len(sys.argv) > 3 else 0)
    elif cmd == "down":
        down()
    else:
        print(json.dumps(http("GET", "api/state"), indent=1)[:4000])
