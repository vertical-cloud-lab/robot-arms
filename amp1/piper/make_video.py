"""One compilation video of the episodes.

Each episode gets a title card (task, instruction, scored outcome), then either
  * its executed motion in real time, from the frames recorded during the episode (the simulator
    pauses while the model thinks, so thinking time is not in the video), or
  * for an episode whose frames were not kept, a slideshow of the images the policy itself looked
    at during the episode (its report's key_images, with the policy's own captions).

python make_video.py OUT.mp4 PLAYLIST.json

PLAYLIST.json is a list of {"episode", "label", "instruction", "verdict", "ok" (true/false/null),
"detail", and "video" (an mp4) or "stills" ([[image path, caption], ...])}, plus optional
{"section": "title", "subtitle": "..."} entries for section cards and an optional
{"intro": [[text, size, bold, colour], ...]} that replaces the opening card.
"""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import textwrap
from pathlib import Path

import imageio_ffmpeg
from PIL import Image, ImageDraw, ImageFont

FF = imageio_ffmpeg.get_ffmpeg_exe()
W, H, FPS = 1280, 720, 30
FONT = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
BOLD = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
BG = (18, 20, 24)
STILL_S, CARD_S = 2.6, 4.0

out = Path(sys.argv[1])
playlist = json.loads(Path(sys.argv[2]).read_text())
tmp = Path(tempfile.mkdtemp())
parts: list[Path] = []


def font(size, bold=False):
    return ImageFont.truetype(BOLD if bold else FONT, size)


def card(path: Path, lines) -> None:
    img = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(img)
    total = sum(int(s * 1.45) * len(textwrap.wrap(t, width=int(2000 / s)) or [""]) + 14
                for t, s, _, _ in lines)
    y = max(40, (H - total) // 2)
    for text, size, bold, color in lines:
        f = font(size, bold)
        for para in textwrap.wrap(text, width=int(2000 / size)) or [""]:
            w = d.textlength(para, font=f)
            d.text(((W - w) / 2, y), para, font=f, fill=color)
            y += int(size * 1.45)
        y += 14
    img.save(path)


def still(path: Path, src: Path, header: str, caption: str, k: int, n: int) -> None:
    img = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(img)
    d.text((24, 14), header, font=font(24, True), fill="#ffffff")
    d.text((W - 210, 18), f"policy's image {k}/{n}", font=font(18), fill="#9aa3ad")
    im = Image.open(src).convert("RGB")
    box_w, box_h = W - 48, H - 60 - 110
    s = min(box_w / im.width, box_h / im.height)
    im = im.resize((max(1, round(im.width * s)), max(1, round(im.height * s))))
    img.paste(im, ((W - im.width) // 2, 56 + (box_h - im.height) // 2))
    y = H - 104
    for line in textwrap.wrap(caption, width=96)[:3]:
        d.text((24, y), line, font=font(22), fill="#e8eaed")
        y += 30
    img.save(path)


def run(*args):
    subprocess.run([FF, "-y", "-loglevel", "error", *args], check=True)


def from_png(png: Path, seconds: float, name: str) -> Path:
    mp4 = tmp / f"{name}.mp4"
    run("-loop", "1", "-i", str(png), "-t", f"{seconds}", "-r", str(FPS), "-pix_fmt", "yuv420p",
        "-c:v", "libx264", "-crf", "22", str(mp4))
    return mp4


intro = tmp / "intro.png"
INTRO = [("AMP1 (Apple, \"On Agentic Manipulation Policies\", 2026)", 34, True, "#ffffff"),
         ("Apple's harness, unchanged, on a CPU-only GitHub runner (MuJoCo)", 26, False,
          "#d0d4da"),
         ("Policy: Claude Opus 5.5 through Claude Code, given only AMP1's own prompt and SDK",
          26, False, "#d0d4da"),
         ("CaP-Gym robosuite and LIBERO-PRO tasks from the paper, then a simulated AgileX "
          "PiPER on the lab's tasks", 26, False, "#d0d4da"),
         ("Motion clips show executed motion in real time: the simulator pauses while the "
          "model thinks. Slideshows show the images the policy looked at.", 21, False,
          "#9aa3ad"),
         ("vertical-cloud-lab/robot-arms #85", 22, False, "#9aa3ad")]
custom = next((it["intro"] for it in playlist if "intro" in it), None)
playlist = [it for it in playlist if "intro" not in it]
card(intro, [tuple(x) for x in custom] if custom else INTRO)
parts.append(from_png(intro, 6, "p000"))

for i, it in enumerate(playlist, 1):
    if "section" in it:
        c = tmp / f"s{i:02d}.png"
        card(c, [(it["section"], 40, True, "#ffffff"), (it.get("subtitle", ""), 24, False,
                                                         "#d0d4da")])
        parts.append(from_png(c, 3.5, f"p{i:03d}s"))
        continue
    ok = it.get("ok")
    color = "#7ee2a8" if ok else "#ff8a80" if ok is False else "#ffd180"
    c = tmp / f"c{i:02d}.png"
    card(c, [(it["label"], 36, True, "#ffffff"), (f"\"{it['instruction']}\"", 26, False,
                                                  "#e8eaed"),
             (it["verdict"], 30, True, color), (it.get("detail", ""), 21, False, "#9aa3ad")])
    parts.append(from_png(c, CARD_S, f"p{i:03d}a"))
    if it.get("video"):
        mp4 = tmp / f"p{i:03d}b.mp4"
        run("-i", it["video"], "-vf",
            f"scale={W}:{H}:force_original_aspect_ratio=decrease,pad={W}:{H}:(ow-iw)/2:(oh-ih)/2,"
            f"fps={FPS}", "-pix_fmt", "yuv420p", "-c:v", "libx264", "-crf", "22", "-an", str(mp4))
        parts.append(mp4)
    for k, (src, cap) in enumerate(it.get("stills", []), 1):
        png = tmp / f"p{i:03d}_{k:02d}.png"
        still(png, Path(src), it["label"], cap, k, len(it["stills"]))
        parts.append(from_png(png, STILL_S, f"p{i:03d}_{k:02d}"))

lst = tmp / "list.txt"
lst.write_text("".join(f"file '{p}'\n" for p in parts))
run("-f", "concat", "-safe", "0", "-i", str(lst), "-c", "copy", str(out))
print(out, out.stat().st_size // 1024, "KB")
