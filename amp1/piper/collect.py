"""Copy episode results into the repo: report, transcript, finish record, the simulator's truth
file, the report's key images as JPEG (every image if the report lists none), final frame.

python collect.py EPISODES_DIR RESULTS_DIR EPISODE...

The final frame is EPISODES_DIR/finals/TASK_final.jpg if it exists, else the last frame recorded
in /tmp/amp-run/TASK/frames/TASK_epK/. The truth file is /tmp/amp-run/TASK/frames/TASK_truth.json.
"""
import json
import shutil
import sys
from pathlib import Path

from PIL import Image

src, dst = Path(sys.argv[1]), Path(sys.argv[2])
for ep in sys.argv[3:]:
    s, d = src / ep, dst / ep
    (d / "images").mkdir(parents=True, exist_ok=True)
    for f in ("report.json", "transcript.jsonl", "finish.json"):
        if (s / f).exists():
            shutil.copy(s / f, d / f)
    task, k = ep.rsplit("-ep", 1)
    run = Path("/tmp/amp-run") / task / "frames"
    if (run / f"{task}_truth.json").exists():
        shutil.copy(run / f"{task}_truth.json", d / "truth.json")
    keys = []
    try:
        keys = [Path(x["path"] if isinstance(x, dict) else x).name.split(".")[0]
                for x in json.loads((s / "report.json").read_text()).get("key_images", [])]
    except (OSError, json.JSONDecodeError, KeyError, TypeError):
        pass
    for p in sorted((s / "images").glob("*.png")) if (s / "images").exists() else []:
        stem = p.name.split(".")[0]
        if keys and stem not in keys:
            continue
        im = Image.open(p).convert("RGB")
        if max(im.size) > 1280:
            r = 1280 / max(im.size)
            im = im.resize((round(im.size[0] * r), round(im.size[1] * r)))
        im.save(d / "images" / f"{stem}.jpg", quality=82, optimize=True)
    fin = src / "finals" / f"{task}_final.jpg"
    frames = sorted((run / f"{task}_ep{k}").glob("*.jpg")) if (run / f"{task}_ep{k}").exists() else []
    if fin.exists():
        shutil.copy(fin, d / "final_frame.jpg")
    elif frames:
        shutil.copy(frames[-1], d / "final_frame.jpg")
    print(ep, sum(f.stat().st_size for f in d.rglob("*") if f.is_file()) // 1024, "KB")
