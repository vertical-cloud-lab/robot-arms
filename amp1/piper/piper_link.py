"""The simulated PiPER as an AMP link client: serves the robot server's /sim/next jobs.

python piper_link.py --server http://127.0.0.1:8765 --output-dir runs/piper
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from amp.link.client import LinkClient  # noqa: E402
from amp.robots.capgym.client import features, run_benchmark, wire_idle  # noqa: E402

import piper_sim  # noqa: E402


def main(argv=None) -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--server", required=True)
    p.add_argument("--output-dir", required=True)
    p.add_argument("--seed", type=int, default=0)
    a = p.parse_args(argv)
    adapter = piper_sim.make_adapter(seed=a.seed)
    link = LinkClient(a.server, client="capgym", embodiment=adapter.embodiment(),
                      robot=adapter.robot_description(), features=features(adapter))
    wire_idle(link, adapter)
    link.hello()
    print(f"[piper_link] hello ok: {adapter.embodiment().name}, sha {adapter._sha[:12]}", flush=True)
    stats = run_benchmark(link, adapter, a.output_dir, episodes_per_task=1000,
                          policy_label="AMP1 (Claude Opus 5.5 via Claude Code)",
                          adapter_name="piper_sim", max_steps=None, cameras="droid")
    print(f"[piper_link] done: {stats}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
