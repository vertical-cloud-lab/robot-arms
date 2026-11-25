"""One compilation video of the episodes: a title card per episode, then its executed motion in
real time (the simulator pauses while the model thinks, so thinking time is not in the video).

python make_video.py OUT.mp4 SUMMARY_JSON EPISODE_NAME[:LABEL]...
"""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path

import imageio_ffmpeg
from PIL import Image, ImageDraw, ImageFont

FF = imageio_ffmpeg.get_ffmpeg_exe()
W, H, FPS = 1280, 720, 30
FONT = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
BOLD = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"

out = Path(sys.argv[1])
rows = {r["episode"]: r for r in json.loads(Path(sys.argv[2]).read_text())}
items = [a.split(":", 1) if ":" in a else (a, a) for a in sys.argv[3:]]
tmp = Path(tempfile.mkdtemp())


def card(path: Path, lines: list[tuple[str, int, bool, str]]) -> None:
    img = Image.new("RGB", (W, H), (18, 20, 24))
    d = ImageDraw.Draw(img)
    y = 150
    for text, size, bold, color in lines:
        f = ImageFont.truetype(BOLD if bold else FONT, size)
        for para in text.split("\n"):
            w = d.textlength(para, font=f)
            d.text(((W - w) / 2, y), para, font=f, fill=color)
            y += int(size * 1.45)
        y += 14
    img.save(path)


def run(*args):
    subprocess.run([FF, "-y", "-loglevel", "error", *args], check=True)


parts = []
intro = tmp / "intro.png"
card(intro, [("AMP1 (Apple, \"On Agentic Manipulation Policies\", 2026)", 34, True, "#ffffff"),
             ("Apple's harness, unchanged, on a CPU-only runner (MuJoCo)", 26, False, "#d0d4da"),
             ("Policy: Claude Opus 5.5 through Claude Code, given AMP1's own prompt", 26, False,
              "#d0d4da"),
             ("CaP-Gym robosuite tasks from the paper, then the lab's AgileX PiPER", 26, False,
              "#d0d4da"),
             ("Videos show executed motion only: the simulator pauses while the model thinks",
              22, False, "#9aa3ad"),
             ("vertical-cloud-lab/robot-arms #85", 22, False, "#9aa3ad")])
run("-loop", "1", "-i", str(intro), "-t", "5", "-r", str(FPS), "-pix_fmt", "yuv420p",
    "-c:v", "libx264", str(tmp / "p00.mp4"))
parts.append(tmp / "p00.mp4")
for i, (name, label) in enumerate(items, 1):
    r = rows[name]
    sc = r.get("scored") or {}
    ok = sc.get("success")
    verdict = {True: "SUCCESS (scored by the simulator's check)",
               False: "FAILURE (scored by the simulator's check)"}.get(ok, "not scored")
    instr = (r.get("instruction") or "").strip()
    c = tmp / f"c{i:02d}.png"
    card(c, [(label, 36, True, "#ffffff"),
             (f"\"{instr}\"", 28, False, "#e8eaed"),
             (verdict, 30, True, "#7ee2a8" if ok else "#ff8a80" if ok is False else "#d0d4da"),
             (f"{r['cells']} code cells · {r['images_shown']} images looked at · "
              f"{r['last_budget'].split(';')[0].strip('[')}", 22, False, "#9aa3ad")])
    run("-loop", "1", "-i", str(c), "-t", "4", "-r", str(FPS), "-pix_fmt", "yuv420p",
        "-c:v", "libx264", str(tmp / f"p{i:02d}a.mp4"))
    parts.append(tmp / f"p{i:02d}a.mp4")
    if r.get("video"):
        run("-i", r["video"], "-vf",
            f"scale={W}:{H}:force_original_aspect_ratio=decrease,pad={W}:{H}:(ow-iw)/2:(oh-ih)/2,"
            f"fps={FPS}", "-pix_fmt", "yuv420p", "-c:v", "libx264", "-crf", "22",
            str(tmp / f"p{i:02d}b.mp4"))
        parts.append(tmp / f"p{i:02d}b.mp4")
lst = tmp / "list.txt"
lst.write_text("".join(f"file '{p}'\n" for p in parts))
run("-f", "concat", "-safe", "0", "-i", str(lst), "-c", "copy", str(out))
print(out, out.stat().st_size // 1024, "KB")
