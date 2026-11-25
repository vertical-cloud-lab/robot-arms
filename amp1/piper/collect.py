"""Copy episode results into the repo: report, transcript, key images as JPEG, final frame."""
import json, shutil, sys
from pathlib import Path
from PIL import Image
src, dst = Path(sys.argv[1]), Path(sys.argv[2])
for ep in sys.argv[3:]:
    s, d = src / ep, dst / ep
    (d / "images").mkdir(parents=True, exist_ok=True)
    for f in ("report.json", "transcript.jsonl"):
        if (s / f).exists():
            shutil.copy(s / f, d / f)
    for p in sorted((s / "images").glob("*")) if (s / "images").exists() else []:
        im = Image.open(p).convert("RGB")
        if max(im.size) > 1280:
            k = 1280 / max(im.size); im = im.resize((round(im.size[0]*k), round(im.size[1]*k)))
        im.save(d / "images" / (p.name.split(".")[0] + ".jpg"), quality=82, optimize=True)
    task = ep.rsplit("-ep", 1)[0]
    fin = src / "finals" / f"{task}_final.jpg"
    if fin.exists():
        shutil.copy(fin, d / "final_frame.jpg")
    print(ep, sum(f.stat().st_size for f in d.rglob("*") if f.is_file()) // 1024, "KB")
