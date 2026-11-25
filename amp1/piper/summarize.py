"""Summarize finished episodes: cells, steps, wall time, the policy's report, the scored outcome,
key images, and a video from the recorded frames.

python summarize.py OUT_DIR EPISODE_DIR...
"""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
from pathlib import Path

import imageio_ffmpeg

FFMPEG = imageio_ffmpeg.get_ffmpeg_exe()
out = Path(sys.argv[1])
out.mkdir(parents=True, exist_ok=True)
rows = []
for ep_dir in map(Path, sys.argv[2:]):
    name = ep_dir.name                       # e.g. tape_to_shelf-ep0, capgym_cube_lifting-ep0
    task = name.rsplit("-ep", 1)[0]
    capgym = task.startswith("capgym_")
    run = Path("/tmp/amp-run") / task
    cells = [json.loads(x) for x in (ep_dir / "transcript.jsonl").read_text().splitlines() if x]
    report = {}
    if (ep_dir / "report.json").exists():
        try:
            report = json.loads((ep_dir / "report.json").read_text())
        except json.JSONDecodeError as exc:
            report = {"unparsed": str(exc)}
    # the scored outcome: the link client's saved episode record
    result = None
    for f in sorted(run.rglob("*.json")):
        if f.name in ("server.json",) or "state" in f.parts:
            continue
        try:
            d = json.loads(f.read_text())
        except (json.JSONDecodeError, UnicodeDecodeError):
            continue
        if isinstance(d, dict) and ("success" in d) and f.name != f"{task}_truth.json":
            result = {"file": str(f), **{k: d[k] for k in ("success", "score", "steps", "reason")
                                         if k in d}}
    truth = None
    tf = run / "frames" / f"{task}_truth.json"
    if tf.exists():
        truth = json.loads(tf.read_text())
    last_budget = cells[-1]["budget"] if cells else ""
    errors = sum(1 for c in cells if c["error"])
    n_images = sum(len(c["images"]) for c in cells)
    wall_s = (cells[-1]["t"] - cells[0]["t"]) if len(cells) > 1 else 0.0
    # video
    frames = run / "frames" / f"{task}_ep0" if not capgym else run / "frames"
    video = None
    if frames.exists() and any(frames.glob("*.jpg")):
        video = out / f"{name}.mp4"
        subprocess.run([FFMPEG, "-y", "-loglevel", "error", "-framerate",
                        "20" if capgym else "15", "-i", str(frames / "%05d.jpg"),
                        "-vf", "scale=trunc(iw/2)*2:trunc(ih/2)*2", "-c:v", "libx264",
                        "-pix_fmt", "yuv420p", "-crf", "23", str(video)], check=True)
    # keep the policy's report, its transcript and its key images
    dst = out / name
    dst.mkdir(exist_ok=True)
    for f in ("report.json", "transcript.jsonl", "finish.json"):
        if (ep_dir / f).exists():
            shutil.copy(ep_dir / f, dst / f)
    for k in report.get("key_images", []) if isinstance(report.get("key_images"), list) else []:
        p = k.get("path") if isinstance(k, dict) else k
        if not p:
            continue
        src = ep_dir / p if not Path(p).is_absolute() else Path(p)
        cands = [src, src.with_suffix(".view.jpg"), ep_dir / "images" / Path(p).name]
        for c in cands:
            if c.exists():
                (dst / "images").mkdir(exist_ok=True)
                shutil.copy(c, dst / "images" / c.name)
                break
    rows.append({"episode": name, "cells": len(cells), "cell_errors": errors,
                 "images_shown": n_images, "policy_wall_min": round(wall_s / 60, 1),
                 "last_budget": last_budget, "outcome_belief": report.get("outcome_belief"),
                 "scored": result, "truth": truth, "video": str(video) if video else None})
(out / "summary.json").write_text(json.dumps(rows, indent=1))
for r in rows:
    print(json.dumps({k: r[k] for k in ("episode", "cells", "cell_errors", "images_shown",
                                          "policy_wall_min", "last_budget", "outcome_belief",
                                          "scored", "video")}))
