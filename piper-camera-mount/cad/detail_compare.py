#!/usr/bin/env python3
"""Fine detail: the wrist HQ with the 6 mm, against a fixed HQ with the OT-2's 8-50 mm zoom.

Bar groups 0.2 to 0.0125 mm wide (three bars, gaps as wide as the bars) as each camera would
take them at its best:

  - wrist: HQ + 6 mm, f/8, the bars 108 mm from the lens where it is focused (README);
  - fixed: HQ + the zoom at 50 mm, f/4, 250 mm away, as a camera that stays put and has the
    arm bring things to it.

Each is the ideal pattern blurred by diffraction (Airy, at the working f-number, in object
space) and averaged over the HQ's pixels, nothing else: no defocus, aberrations or noise, so
this is the best either can do, and a cheap zoom will do somewhat worse.

    python detail_compare.py        # -> ../renders/detail_compare.png
"""
from __future__ import annotations

import math
from pathlib import Path

import cv2
import matplotlib
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from scipy.special import j1

RENDERS = Path(__file__).resolve().parent.parent / "renders"
FONTS = Path(matplotlib.get_data_path()) / "fonts" / "ttf"
WAVELENGTH = 0.55e-3                    # mm
STEP = 0.002                            # mm per pixel of the ideal pattern
WIDTHS = (0.2, 0.1, 0.05, 0.025, 0.0125)
REGION = (4.1, 1.3)                     # mm shown, across x up
CAMERAS = (                             # name, focal length, f-number, distance, sensor pixel (mm)
    ("Wrist, 6 mm, 108 mm away, f/8, 2028 x 1520", 6.0, 8.0, 108.0, 2 * 1.55e-3),
    ("Wrist, 6 mm, 108 mm away, f/8, 4056 x 3040", 6.0, 8.0, 108.0, 1.55e-3),
    ("Fixed, zoom at 50 mm, 250 mm away, f/4, 2028 x 1520", 50.0, 4.0, 250.0, 2 * 1.55e-3),
)


def pattern() -> tuple[np.ndarray, list[tuple[float, float]]]:
    """White card, black bars. Returns the image and each group's (centre x, width) in mm."""
    w, h = (int(round(v / STEP)) for v in REGION)
    img = np.ones((h, w), np.float32)
    x, groups = 0.3, []
    for bw in WIDTHS:
        for k in range(3):
            x0 = x + 2 * k * bw
            img[int(0.35 / STEP):int(1.15 / STEP), int(round(x0 / STEP)):int(round((x0 + bw) / STEP))] = 0.0
        groups.append((x + 2.5 * bw, bw))
        x += 5 * bw + 0.4
    return img, groups


def airy(r0_mm: float) -> np.ndarray:
    """Airy intensity, first dark ring at r0, sampled on the pattern's grid."""
    r0 = r0_mm / STEP
    n = int(math.ceil(3 * r0))
    y, x = np.mgrid[-n:n + 1, -n:n + 1].astype(np.float64)
    v = 3.8317 * np.hypot(x, y) / r0
    k = np.where(v == 0, 1.0, (2 * j1(np.where(v == 0, 1, v)) / np.where(v == 0, 1, v)) ** 2)
    return (k / k.sum()).astype(np.float32)


def take(img: np.ndarray, f: float, n: float, u: float, px: float) -> tuple[np.ndarray, dict]:
    m = f / (u - f)                                   # magnification, thin lens
    r0 = 1.22 * WAVELENGTH * n * (1 + m) / m          # object-space Rayleigh radius
    blurred = cv2.filter2D(img, -1, airy(r0), borderType=cv2.BORDER_REPLICATE)
    obj_px = px / m
    size = (max(1, round(img.shape[1] * STEP / obj_px)), max(1, round(img.shape[0] * STEP / obj_px)))
    return cv2.resize(blurred, size, interpolation=cv2.INTER_AREA), {"pixel_mm": obj_px, "rayleigh_mm": r0}


def main() -> None:
    ideal, groups = pattern()
    disp_w = 860
    scale = disp_w / REGION[0]                        # display px per mm
    disp_h = int(REGION[1] * scale)
    left, top, row_gap, title_h = 16, 70, 64, 30
    canvas = Image.new("RGB", (left * 2 + disp_w, top + len(CAMERAS) * (disp_h + row_gap) + 10), "white")
    dr = ImageDraw.Draw(canvas)
    big, small = (ImageFont.truetype(str(FONTS / "DejaVuSans.ttf"), s) for s in (19, 15))
    bold = ImageFont.truetype(str(FONTS / "DejaVuSans-Bold.ttf"), 21)
    dr.text((left, 12), "Bars 0.2 to 0.0125 mm wide (red, mm), each camera at its best",
            fill=(20, 20, 20), font=bold)
    dr.text((left, 40), "Diffraction and pixels only: no defocus, aberrations or noise. Same scale in every row.",
            fill=(95, 95, 95), font=small)
    for i, (name, f, n, u, px) in enumerate(CAMERAS):
        shot, info = take(ideal, f, n, u, px)
        y0 = top + i * (disp_h + row_gap)
        dr.text((left, y0), f"{name}: pixel {info['pixel_mm']:.3f} mm, diffraction limit "
                            f"{info['rayleigh_mm']:.3f} mm", fill=(20, 20, 20), font=small)
        view = cv2.resize((shot * 255).clip(0, 255).astype(np.uint8), (disp_w, disp_h), interpolation=cv2.INTER_NEAREST)
        canvas.paste(Image.fromarray(view).convert("RGB"), (left, y0 + title_h - 6))
        for cx, bw in groups:
            label = f"{bw:g}"
            tw = dr.textlength(label, font=small)
            dr.text((left + cx * scale - tw / 2, y0 + title_h - 6 + int(0.05 * scale)), label,
                    fill=(200, 30, 30), font=small)
        print(name, {k: round(v, 4) for k, v in info.items()})
    out = RENDERS / "detail_compare.png"
    canvas.save(out)
    print(out)


if __name__ == "__main__":
    main()
