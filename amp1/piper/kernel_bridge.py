"""AMP1's tool surface for a Claude Code agent: a persistent Python kernel behind a Unix socket.

AMP's own agent loop calls the model through its API with three tools: python(code), view_image,
finish_episode (and submit_report). Here the model is a Claude Code agent that has no such tools,
so this process plays the kernel: it keeps one namespace for the whole episode with AMP1's
preloads (rh = the amp1_basic SDK, ep = the episode, np, Image, show), runs each code cell it is
sent, and replies with stdout, stderr, the traceback, the images the cell show()ed (saved under
images/, downscaled copies to look at) and the budget line AMP appends to every tool result.

    python kernel_bridge.py serve EPISODE_DIR SERVER_URL      # one per episode
    python kernel_bridge.py run EPISODE_DIR < cell.py          # one python(code) call
    python kernel_bridge.py finish EPISODE_DIR "reason"        # finish_episode(reason)

Every cell and its result is appended to EPISODE_DIR/transcript.jsonl.
"""

from __future__ import annotations

import contextlib
import io
import json
import os
import signal
import socket
import sys
import time
import traceback
from pathlib import Path

SDK = os.environ.get("AMP_SDK_DIR", "/tmp/ext/ml-amp/src/amp/harnesses/_sdk_amp1_basic")
MAX_IMAGES = 6
VIEW_PX = 1280
OUT_CAP = 20000
WALL_LIMIT_MIN = float(os.environ.get("AMP_WALL_LIMIT_MIN", "60"))


def _sock(ep_dir: Path) -> str:
    return str(Path("/tmp/amp-sockets") / (ep_dir.name + ".sock"))


class Kernel:
    def __init__(self, ep_dir: Path, url: str):
        self.dir = ep_dir
        self.images = ep_dir / "images"
        self.images.mkdir(parents=True, exist_ok=True)
        self.t0 = time.time()
        self.n_img = 0
        self.cell = 0
        self._shown: list[str] = []
        os.chdir(ep_dir)
        sys.path.insert(0, SDK)
        import numpy as np
        import robolab_harness as rh
        from PIL import Image

        ep = rh.Episode(worker_url=url)
        (ep_dir / "episode.json").write_text(json.dumps(
            {"instruction": ep.observe().get("instruction"), "server": "direct"}))
        self.ns = {"rh": rh, "ep": ep, "np": np, "Image": Image, "show": self.show,
                   "__name__": "__main__"}
        self.ep, self.rh = ep, rh

    def show(self, x, caption=None):
        import numpy as np
        from PIL import Image
        if len(self._shown) >= MAX_IMAGES:
            print(f"[show] at most {MAX_IMAGES} images per call; this one was not attached")
            return None
        if isinstance(x, (str, os.PathLike)):
            img = Image.open(x)
        elif isinstance(x, Image.Image):
            img = x
        else:
            a = np.asarray(x)
            if a.dtype != np.uint8:
                a = np.clip(a, 0, 255).astype(np.uint8) if a.max() > 1.0 else \
                    (np.clip(a, 0, 1) * 255).astype(np.uint8)
            img = Image.fromarray(a)
        img = img.convert("RGB")
        self.n_img += 1
        stem = f"{self.n_img:03d}"
        if caption:
            safe = "".join(c if c.isalnum() else "_" for c in str(caption))[:40].strip("_")
            stem += f"_{safe}"
        full = self.images / f"{stem}.png"
        img.save(full)
        view = img
        if max(img.size) > VIEW_PX:
            s = VIEW_PX / max(img.size)
            view = img.resize((round(img.size[0] * s), round(img.size[1] * s)))
        vpath = self.images / f"{stem}.view.jpg"
        view.save(vpath, quality=88)
        self._shown.append(str(vpath))
        print(f"[show] images/{full.name}" + (f"  ({caption})" if caption else ""))
        return str(full)

    def budget(self) -> str:
        wall = (time.time() - self.t0) / 60
        try:
            b = self.ep.budget()
            return (f"[step {b['step']} of {b['max_steps']}, {b['steps_left']} left; "
                    f"wall {wall:.0f} min of {WALL_LIMIT_MIN:.0f} used]")
        except Exception as exc:  # noqa: BLE001
            return f"[episode over or unavailable ({type(exc).__name__}); wall {wall:.0f} min]"

    def run(self, code: str, timeout_s: float = 600.0) -> dict:
        self.cell += 1
        self._shown = []
        out, err = io.StringIO(), io.StringIO()
        error = None
        t = time.time()

        def alarm(signum, frame):
            raise TimeoutError(f"cell interrupted after timeout_s={timeout_s:.0f}")

        signal.signal(signal.SIGALRM, alarm)
        signal.alarm(max(1, int(timeout_s)))
        try:
            with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
                exec(compile(code, f"<cell {self.cell}>", "exec"), self.ns)  # noqa: S102
        except BaseException as exc:  # noqa: BLE001
            error = "".join(traceback.format_exception(type(exc), exc, exc.__traceback__))
        finally:
            signal.alarm(0)
        res = {"cell": self.cell, "error": error, "stdout": out.getvalue()[-OUT_CAP:],
               "stderr": err.getvalue()[-OUT_CAP:], "images": list(self._shown),
               "elapsed_s": round(time.time() - t, 2), "budget": self.budget()}
        with open(self.dir / "transcript.jsonl", "a") as f:
            f.write(json.dumps({"t": time.time(), "code": code, **res}) + "\n")
        return res


def serve(ep_dir: Path, url: str) -> None:
    k = Kernel(ep_dir, url)
    path = _sock(ep_dir)
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    with contextlib.suppress(FileNotFoundError):
        os.unlink(path)
    s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    s.bind(path)
    s.listen(1)
    print(f"kernel ready: {path}", flush=True)
    while True:
        conn, _ = s.accept()
        with conn:
            data = b""
            while not data.endswith(b"\n\x00"):
                chunk = conn.recv(65536)
                if not chunk:
                    break
                data += chunk
            req = json.loads(data.rstrip(b"\n\x00").decode())
            if req.get("op") == "finish":
                code = (f"r = ep.finish()\nprint('episode finished:', "
                        f"{json.dumps(req.get('reason', ''))})")
                res = k.run(code, 120)
                with open(ep_dir / "finish.json", "w") as f:
                    json.dump({"t": time.time(), "reason": req.get("reason", "")}, f)
            else:
                res = k.run(req["code"], float(req.get("timeout_s", 600)))
            conn.sendall(json.dumps(res).encode())


def client(ep_dir: Path, req: dict) -> None:
    s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    s.connect(_sock(ep_dir))
    s.sendall(json.dumps(req).encode() + b"\n\x00")
    data = b""
    while True:
        chunk = s.recv(1 << 20)
        if not chunk:
            break
        data += chunk
    res = json.loads(data)
    if res["error"]:
        print("ERROR (raised in this cell):\n" + res["error"])
    if res["stdout"]:
        print(res["stdout"], end="" if res["stdout"].endswith("\n") else "\n")
    if res["stderr"]:
        print("[stderr]\n" + res["stderr"])
    if res["images"]:
        print("IMAGES (open each with the Read tool to see it):")
        for p in res["images"]:
            print("  " + p)
    print(res["budget"])


if __name__ == "__main__":
    op, ep_dir = sys.argv[1], Path(sys.argv[2]).resolve()
    if op == "serve":
        serve(ep_dir, sys.argv[3])
    elif op == "run":
        args = sys.argv[3:]
        timeout = float(args[args.index("--timeout") + 1]) if "--timeout" in args else 600.0
        client(ep_dir, {"op": "run", "code": sys.stdin.read(), "timeout_s": timeout})
    elif op == "finish":
        client(ep_dir, {"op": "finish", "reason": " ".join(sys.argv[3:])})
    else:
        raise SystemExit(__doc__)
