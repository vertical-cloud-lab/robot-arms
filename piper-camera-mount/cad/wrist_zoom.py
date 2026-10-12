#!/usr/bin/env python3
"""The OT-2's 8-50 mm zoom on the wrist HQ Camera, against the 6 mm the mount is built round.

The OT-2's HQ Camera has a Waveshare 8-50 mm C-mount zoom (BOM.md). This screws that lens into
the wrist HQ in place of the 6 mm, on the same camera in the same place on the pod, and renders
a GIF in three parts:

  1. the 6 mm, as ordered: the finger tags and a 20 mm target 60 mm past the tips;
  2. the zoom, turned from 8 to 50 mm: left, the gripper and mount with the lens on and the HQ's
     field of view; right, the HQ picture through it;
  3. the 6 mm back on, and the gripper moved toward a label instead of zooming in on it.

The pictures are fiducials.py's (pinhole at the lens front, 2028 x 1520, OpenCV's AprilTag
detector), blurred for depth of field and diffraction the way lens_compare.py on
claude/issue-239-20261007-2023 does (thin lens, f/8). The 6 mm is focused 108 mm out, as the
README says to set it. The zoom is treated as a thin lens of whatever focal length it is set to,
focused on the target if it can get that close: its own focus stops at 0.2 m (Waveshare's minimum
object distance), and the HQ's back-focus ring can add about 4.9 mm more (its range is 12.5 to
22.4 mm, and a C-mount lens sits at 17.53 mm). A real zoom isn't a thin lens, so read the blur at
the long end as a sketch.

    xvfb-run -a -s "-screen 0 1920x1080x24" python wrist_zoom.py
        # -> ../renders/wrist_zoom.gif, ../exports/wrist_zoom.json
"""
from __future__ import annotations

import argparse
import dataclasses
import json
import math
from pathlib import Path

import cadquery as cq
import cv2
import matplotlib
import numpy as np
import pyvista as pv
from PIL import Image, ImageDraw, ImageFont

import reference
from fiducials import FINGER_IDS, SIZE, TARGET_ID, TARGET_SIZE, detect, detector, scene_tags, tag_image, tag_quad, vec
from piper_mount import (COLORS, FINGERTIP_Y, IMX477, Params, build, cyl_z, gap, hq_fov, hq_place, optical_axes,
                         overlap, place_tag_wedges, station_vec)
from render import ALU, DARK, PAD, mesh

HERE = Path(__file__).resolve().parent
EXPORTS = HERE.parent / "exports"
RENDERS = HERE.parent / "renders"
FONTS = Path(matplotlib.get_data_path()) / "fonts" / "ttf"

BINNED = 2 * 1.55e-3            # mm: a pixel of the 2028 x 1520 mode
WAVELENGTH = 0.55e-3            # mm, green
N = 8.0                         # f-number, both lenses (the README's setting for the 6 mm)
SIX_FOCUS = 108.0               # mm in front of the 6 mm lens (README: about 20 mm past the fingertips)
OPENING = 40.0                  # finger opening in every picture
TARGET = 60.0                   # 20 mm target this far past the fingertips (acts 1 and 2)

# Waveshare "8-50mm Zoom Lens for Pi" (SKU 18245), Waveshare's figures: C mount, 8-50 mm, F1.4,
# O40 x 68.3 mm, 148 g, M.O.D. 0.2 m. It goes on the HQ through the 5 mm C-CS adapter that comes
# with the camera. The step down to the iris ring at the back is an estimate from product photos.
ZOOM_OD, ZOOM_LEN, ZOOM_THREAD, ADAPTER = 40.0, 68.3, 4.0, 5.0
ZOOM_MASS, ZOOM_MOD = 148.0, 200.0
HQ_BACK_FOCUS_MAX, C_MOUNT_FFD = 22.4, 17.526      # mm: the HQ's back-focus range tops out at 22.4

SIX_MASS = 53.0                 # g, Raspberry Pi's 6 mm


# --- optics -------------------------------------------------------------------------------------

def thin_lens_v(f: float, u: float) -> float:
    return 1.0 / (1.0 / f - 1.0 / u)


def zoom_closest_focus(f: float) -> float:
    """Nearest the zoom can focus at focal length f, lens front to object: its own 0.2 m, plus
    whatever the HQ's back-focus ring can add behind a C-mount lens (thin lens)."""
    v = thin_lens_v(f, ZOOM_MOD) + (HQ_BACK_FOCUS_MAX - C_MOUNT_FFD)
    return 1.0 / (1.0 / f - 1.0 / v)


def disk(d: float) -> np.ndarray:
    r = d / 2
    n = int(math.ceil(r))
    y, x = np.mgrid[-n:n + 1, -n:n + 1]
    k = (x * x + y * y <= r * r + 0.25).astype(np.float32)
    return k / k.sum()


def defocus(img: np.ndarray, z: np.ndarray, f: float, n: float, focus_mm: float) -> tuple[np.ndarray, np.ndarray]:
    """lens_compare.py's blur: each pixel by the defocus disk its distance gives (thin lens),
    gathered from a stack of uniformly blurred copies, then diffraction over the whole picture.
    Also returns the blur disk diameter of every pixel, in px."""
    zz = np.where(np.isfinite(z), z, 1000.0)
    zz = np.clip(zz, f * 1.5, None)
    v = 1.0 / (1.0 / f - 1.0 / zz)
    vm = thin_lens_v(f, focus_mm)
    b = (f / n) * np.abs(v - vm) / v / BINNED
    levels = [0.0, 1.5, 2.5, 4.0, 6.0, 8.0, 11.0, 16.0, 22.0, 32.0, 45.0, 64.0, 90.0, 128.0]
    src = img.astype(np.float32)
    out = np.zeros_like(src)
    prev = src
    for lo, hi in zip(levels[:-1], levels[1:]):
        if b.max() < lo:
            break
        nxt = cv2.filter2D(src, -1, disk(hi), borderType=cv2.BORDER_REPLICATE)
        w = np.clip((b - lo) / (hi - lo), 0.0, 1.0)[..., None]
        m = ((b >= lo) & (b < hi))[..., None]
        out = np.where(m, prev * (1 - w) + nxt * w, out)
        prev = nxt
    out = np.where((b >= levels[-1])[..., None], prev, out)
    sigma = 0.42 * WAVELENGTH * n * (vm / f) / BINNED
    out = cv2.GaussianBlur(out, (0, 0), sigma)
    return np.clip(out, 0, 255).astype(np.uint8), b


# --- the two lenses on the same camera -----------------------------------------------------------

def zoom_params(p6: Params, f: float) -> Params:
    """The zoom on the 6 mm's camera: the camera stays put, the lens front moves out."""
    length = ADAPTER + ZOOM_LEN
    front = station_vec(p6, 0, -(p6.hq_cs_seat + length - ZOOM_THREAD), 0)
    return dataclasses.replace(p6, lens_od=ZOOM_OD, lens_len=length, lens_thread=ZOOM_THREAD, lens_f=f,
                               hq_front_x=front.x, hq_front_y=front.y)


def zoom_body(p: Params) -> cq.Workplane:
    """Adapter, iris ring, then the zoom and focus barrel, in the HQ's frame, placed."""
    seat, front = -p.hq_cs_seat, -p.hq_cs_seat - (ADAPTER + ZOOM_LEN - ZOOM_THREAD)
    body = cyl_z(31.0, seat - ADAPTER, seat)
    body = body.union(cyl_z(34.0, seat - 16.0, seat - ADAPTER))
    body = body.union(cyl_z(ZOOM_OD, front, seat - 16.0))
    body = body.cut(cyl_z(30.0, front - 1.0, front + 2.5))
    return hq_place(p)(body)


def depth(p: Params, pt) -> float:
    o, d, _ = optical_axes(p)["hq"]
    return (cq.Vector(*pt) - o).dot(d)


# --- scene ---------------------------------------------------------------------------------------

def label_image(px_per_mm: int = 24) -> tuple[np.ndarray, tuple[float, float]]:
    """A 64 x 30 mm vial label: text 4, 2.5, 1.6 and 1 mm tall (cap height, roughly)."""
    w_mm, h_mm = 64.0, 30.0
    img = Image.new("RGB", (int(w_mm * px_per_mm), int(h_mm * px_per_mm)), (250, 250, 246))
    dr = ImageDraw.Draw(img)
    dr.rectangle([4, 4, img.width - 5, img.height - 5], outline=(30, 30, 30), width=int(0.4 * px_per_mm))
    y = 2.6 * px_per_mm
    for text, cap_mm, bold in (("CuSO4  0.10 M", 4.0, True), ("lot 47-B   2026-10-12", 2.5, False),
                               ("rinse before use, store at 4 C", 1.6, False),
                               ("exp 2027-04, keep tightly closed", 1.0, False)):
        font = ImageFont.truetype(str(FONTS / ("DejaVuSans-Bold.ttf" if bold else "DejaVuSans.ttf")),
                                  int(cap_mm * px_per_mm / 0.73))
        dr.text((3.0 * px_per_mm, y), text, fill=(15, 15, 15), font=font)
        y += cap_mm * px_per_mm * 1.75 + 1.2 * px_per_mm
    return np.asarray(img), (w_mm, h_mm)


class World:
    """Meshes that don't change between frames, built once."""

    def __init__(self, p6: Params):
        self.p6 = p6
        self.parts = build(p6)
        sol = reference.gripper_solids()
        shift = (OPENING - reference.OPENING_AS_MODELLED) / 2
        self.gripper = []
        for i, s in enumerate(sol):
            if i in reference.UPPER_FINGER:
                s = s.translate(cq.Vector(0, 0, shift))
            elif i in reference.LOWER_FINGER:
                s = s.translate(cq.Vector(0, 0, -shift))
            color = PAD if i in (6, 10) else (DARK if i in (1, 5, 8, 9, 12) else ALU)
            self.gripper.append((mesh(s, 0.15), color))
        names = ("bracket", "pod", "carrier", "pi_spacers", "hq_pcb", "hq_mount", "cm_pcb", "cm_module", "pi5")
        self.mount = [(mesh(self.parts[n]), COLORS[n]) for n in names]
        self.mount.append((mesh(place_tag_wedges(p6, OPENING)), COLORS["tag_wedge"]))
        self.six = mesh(self.parts["hq_lens"])
        pz = zoom_params(p6, 8.0)
        self.zoom_solid = zoom_body(pz)
        self.zoom = mesh(self.zoom_solid)
        g = reference.gripper()
        self.fit = {
            "zoom vs bracket (mm3)": round(overlap(self.zoom_solid, self.parts["bracket"]), 1),
            "zoom vs pod (mm3)": round(overlap(self.zoom_solid, self.parts["pod"]), 1),
            "zoom vs gripper body (mm3)": round(overlap(self.zoom_solid, g["body"]), 1),
            "6 mm lens vs bracket (mm3)": round(overlap(self.parts["hq_lens"], self.parts["bracket"]), 1),
            "zoom to the fingers, fully open (mm)": round(gap(self.zoom_solid, reference.gripper(100.0)["fingers"]), 2),
        }
        clash = []
        for other in (self.parts["bracket"], g["body"]):
            try:
                c = self.zoom_solid.intersect(other)
                if c.val().isValid() and c.val().Volume() > 1e-3:
                    clash.append(mesh(c))
            except Exception:                               # OCC on AgileX's flange; the proxy is in g
                pass
        self.clash = clash
        self.textures = {i: pv.numpy_to_texture(tag_image(i)) for i in (*FINGER_IDS.values(), TARGET_ID)}
        lab, self.label_mm = label_image()
        self.label_tex = pv.numpy_to_texture(lab)


def label_quad(p: Params, w: World, dist: float, shift=np.zeros(3)) -> pv.PolyData:
    """The label square to the HQ's axis, dist in front of the lens, its text across the picture."""
    o, d, up = (vec(v) for v in optical_axes(p)["hq"])
    up = up - d * up.dot(d)
    up /= np.linalg.norm(up)
    r = np.cross(d, up)
    c = o + d * dist + shift
    hw, hh = w.label_mm[0] / 2, w.label_mm[1] / 2
    pts = np.array([c - r * hw - up * hh, c + r * hw - up * hh, c + r * hw + up * hh, c - r * hw + up * hh])
    quad = pv.PolyData(pts, np.array([4, 0, 1, 2, 3]))
    quad.active_texture_coordinates = np.array([[0, 0], [1, 0], [1, 1], [0, 1]], float)
    return quad


def hq_picture(p: Params, w: World, scene: str, dist: float) -> tuple[np.ndarray, np.ndarray, list[dict]]:
    """The HQ's ideal picture (and its depth along the axis) through whatever lens p has. scene
    "target": the 20 mm tag on a card square to the gripper axis, dist past the fingertips.
    scene "label": the label square to the HQ's axis, dist in front of the lens."""
    pl = pv.Plotter(off_screen=True, window_size=SIZE)
    pl.set_background((0.93, 0.93, 0.90))
    for m, c in w.gripper + w.mount:
        pl.add_mesh(m, color=c, smooth_shading=False)
    tags = scene_tags(p, OPENING, dist if scene == "target" else None)
    o, d, up = (vec(v) for v in optical_axes(p)["hq"])
    if scene == "target":
        pl.add_mesh(pv.Plane(center=(p.ax_x, FINGERTIP_Y - dist - 0.2, p.ax_z), direction=(0, 1, 0),
                             i_size=900, j_size=900), color=(0.62, 0.66, 0.70))
    else:
        pl.add_mesh(pv.Plane(center=tuple(o + d * (dist + 0.2)), direction=tuple(-d), i_size=900, j_size=900),
                    color=(0.62, 0.66, 0.70))
        pl.add_mesh(label_quad(p, w, dist), texture=w.label_tex, lighting=False)
    for t in tags:
        pl.add_mesh(tag_quad(t["centre"], t["right"], t["up"], t["size"]), texture=w.textures[t["id"]], lighting=False)
    up = up - d * up.dot(d)
    up /= np.linalg.norm(up)
    vfov = hq_fov(p)[1]
    pl.camera.position = tuple(o)
    pl.camera.focal_point = tuple(o + d * 200)
    pl.camera.up = tuple(up)
    pl.camera.view_angle = vfov
    pl.camera.clipping_range = (1.0, 3000.0)
    img = pl.screenshot(return_img=True)
    z = pl.get_image_depth(fill_value=np.nan, reset_camera_clipping_range=False)
    pl.close()
    return img, np.abs(z), [dict(t, cam=(o, d, up, vfov)) for t in tags]


def frustum(p: Params, depth_mm: float) -> pv.PolyData:
    o, d, up = (vec(v) for v in optical_axes(p)["hq"])
    up = up - d * up.dot(d)
    up /= np.linalg.norm(up)
    right = np.cross(d, up)
    th, tv = (math.tan(math.radians(a / 2)) for a in hq_fov(p))
    c = o + d * depth_mm
    far = [c + right * sx * depth_mm * th + up * sy * depth_mm * tv for sx, sy in ((-1, -1), (1, -1), (1, 1), (-1, 1))]
    pts = np.array([o, *far])
    faces = np.hstack([[3, 0, 1, 2], [3, 0, 2, 3], [3, 0, 3, 4], [3, 0, 4, 1], [4, 1, 2, 3, 4]])
    return pv.PolyData(pts, faces)


CAD_CAMERA = {"target": [(-400.0, -340.0, 300.0), (-30.0, -95.0, -5.0), (0, 0, 1)],
              "label": [(-745.0, 385.0, 330.0), (-95.0, 135.0, 0.0), (0, 0, 1)]}
LABEL_AT = SIX_FOCUS            # act 3 ends with the label here, the 6 mm's sharpest distance


def cad_view(p: Params, w: World, lens: str, scene: str, dist: float, size=(1000, 750)) -> np.ndarray:
    """The gripper and mount from outside the pod, the lens on, and what the HQ sees. For the
    label, the label stays put and the gripper backs off along the HQ's axis by dist - LABEL_AT."""
    pl = pv.Plotter(off_screen=True, window_size=size)
    pl.set_background("white")
    pl.enable_anti_aliasing("ssaa")
    o, d, _ = (vec(v) for v in optical_axes(p)["hq"])
    mv = -d * (dist - LABEL_AT) if scene == "label" else np.zeros(3)
    for m, c in w.gripper + w.mount[1:]:
        pl.add_mesh(m.translate(mv, inplace=False), color=c, smooth_shading=False, specular=0.15)
    pl.add_mesh(w.mount[0][0].translate(mv, inplace=False), color=w.mount[0][1], smooth_shading=False,
                specular=0.15, opacity=0.45 if lens == "zoom" else 1.0)            # the bracket
    if lens == "zoom":
        pl.add_mesh(w.zoom, color=(0.10, 0.10, 0.11), smooth_shading=False, specular=0.3, opacity=0.55)
        for c in w.clash:
            pl.add_mesh(c, color=(0.92, 0.06, 0.06))
    else:
        pl.add_mesh(w.six.translate(mv, inplace=False), color=(0.10, 0.10, 0.11), smooth_shading=False)
    if scene == "target":
        card_y = FINGERTIP_Y - dist
        pl.add_mesh(pv.Plane(center=(p.ax_x, card_y - 0.3, p.ax_z), direction=(0, 1, 0), i_size=60, j_size=60),
                    color=(0.80, 0.82, 0.85))
        pl.add_mesh(pv.Plane(center=(p.ax_x, card_y - 0.8, p.ax_z), direction=(0, 1, 0), i_size=20, j_size=20),
                    color=(0.05, 0.05, 0.05))
        reach = depth(p, (p.ax_x, card_y, p.ax_z)) + 4.0
    else:
        c = o + d * LABEL_AT
        pl.add_mesh(pv.Plane(center=tuple(c + d * 0.4), direction=tuple(-d), i_size=80, j_size=44),
                    color=(0.80, 0.82, 0.85))
        pl.add_mesh(label_quad(p, w, LABEL_AT), texture=w.label_tex, lighting=False)
        reach = dist
    cone = frustum(p, reach).translate(mv, inplace=False)
    pl.add_mesh(cone, color=(1.0, 0.78, 0.15), opacity=0.25)
    pl.add_mesh(cone.extract_all_edges(), color=(0.85, 0.55, 0.0), line_width=2)
    pl.camera_position = CAD_CAMERA[scene]
    pl.camera.view_angle = 30.0
    img = pl.screenshot(return_img=True)
    pl.close()
    return img


# --- frames --------------------------------------------------------------------------------------

def zoom_focal_lengths(n: int) -> list[float]:
    return [8.0 * (50.0 / 8.0) ** (i / (n - 1)) for i in range(n)]


def ease(u: float) -> float:
    return 0.5 - 0.5 * math.cos(math.pi * u)


def frame_list(quick: bool) -> list[dict]:
    nz, nd = (4, 3) if quick else (22, 18)
    frames = [{"act": 1, "lens": "6mm", "f": 6.0, "scene": "target", "past": TARGET, "hold": 3.0}]
    for i, f in enumerate(zoom_focal_lengths(nz)):
        frames.append({"act": 2, "lens": "zoom", "f": round(f, 2), "scene": "target", "past": TARGET,
                       "hold": 2.2 if i == 0 else (3.0 if i == nz - 1 else 0.28)})
    far, near = 400.0, LABEL_AT
    for i in range(nd):
        dist = far + (near - far) * ease(i / (nd - 1))
        frames.append({"act": 3, "lens": "6mm", "f": 6.0, "scene": "label", "past": round(dist, 1),
                       "hold": 1.8 if i == 0 else (4.0 if i == nd - 1 else 0.22)})
    return frames


CROP = (600, 170)               # px of the 2028 x 1520 picture, shown 1:1 in part 3
CROP_AT = (-13.0, 3.0)          # mm right of and below the label's centre: the smaller lines


def render_frame(fr: dict, w: World, det) -> tuple[np.ndarray, np.ndarray, dict, np.ndarray | None]:
    p6 = w.p6
    p = zoom_params(p6, fr["f"]) if fr["lens"] == "zoom" else p6
    img, z, tags = hq_picture(p, w, fr["scene"], fr["past"])
    if fr["scene"] == "target":
        u_target = depth(p, (p.ax_x, FINGERTIP_Y - fr["past"], p.ax_z))
    else:
        u_target = fr["past"]
    if fr["lens"] == "zoom":
        closest = zoom_closest_focus(fr["f"])
        focus = max(u_target, closest)
    else:
        closest, focus = None, SIX_FOCUS
    soft, b = defocus(img, z, fr["f"], N, focus)
    res = detect(soft, tags, det)
    hf, vf = hq_fov(p)
    finger_px = [res[i]["tag_edge_px"] for i in FINGER_IDS.values() if res.get(i)]
    in_frame = {}
    o, d, up = (vec(v) for v in optical_axes(p)["hq"])
    up = up - d * up.dot(d)
    up /= np.linalg.norm(up)
    R = np.vstack([np.cross(d, up), -up, d])
    fpx = (SIZE[1] / 2) / math.tan(math.radians(vf / 2))
    quads, edge_px = {}, {}
    for t in tags:
        for s, key in ((t["size"] * 10 / 8, "white"), (t["size"], "black")):
            pts = []
            for a, b2 in ((-1, 1), (1, 1), (1, -1), (-1, -1)):
                q = R @ (t["centre"] + a * t["right"] * s / 2 + b2 * t["up"] * s / 2 - o)
                pts.append((fpx * q[0] / q[2] + SIZE[0] / 2, fpx * q[1] / q[2] + SIZE[1] / 2))
            pts = np.array(pts)
            if key == "white":                      # the printed tag, white border and all
                in_frame[t["name"]] = bool(((pts >= 0) & (pts <= SIZE)).all())
            else:
                quads[t["id"]] = pts
                edge_px[t["name"]] = round(float(np.linalg.norm(pts[0] - pts[1])), 1)
    v_t = thin_lens_v(fr["f"], u_target)
    vm = thin_lens_v(fr["f"], focus)
    blur_target = (fr["f"] / N) * abs(v_t - vm) / v_t / BINNED
    airy = 2.44 * WAVELENGTH * N * (vm / fr["f"]) / BINNED
    crop = None
    if fr["scene"] == "label":                      # 1:1 pixels round the smaller lines of text
        c = o + d * u_target + np.cross(d, up) * CROP_AT[0] - up * CROP_AT[1]
        q = R @ (c - o)
        cx, cy = int(fpx * q[0] / q[2] + SIZE[0] / 2), int(fpx * q[1] / q[2] + SIZE[1] / 2)
        x0 = min(max(cx - CROP[0] // 2, 0), SIZE[0] - CROP[0])
        y0 = min(max(cy - CROP[1] // 2, 0), SIZE[1] - CROP[1])
        crop = soft[y0:y0 + CROP[1], x0:x0 + CROP[0]].copy()
    info = {
        "lens": "6 mm" if fr["lens"] == "6mm" else "Waveshare 8-50 mm zoom",
        "focal length (mm)": fr["f"],
        "field of view (deg, across x up)": [round(hf, 1), round(vf, 1)],
        "lens front behind the fingertips (mm)": round(optical_axes(p)["hq"][0].y - FINGERTIP_Y, 1),
        "scene": fr["scene"],
        ("target past the fingertips (mm)" if fr["scene"] == "target" else "label in front of the lens (mm)"): fr["past"],
        "card distance along the axis (mm)": round(u_target, 1),
        "focused at (mm)": round(focus, 1),
        "closest focus (mm)": None if closest is None else round(closest, 1),
        "blur on the card, defocus only (px)": round(blur_target, 1),
        "blur on the card, defocus and diffraction (px)": round(math.hypot(blur_target, airy), 1),
        "px per mm on the card": round(fr["f"] / BINNED / u_target, 1),
        "wholly in the picture": in_frame,
        "tag edge, projected (px)": edge_px,
        "finger tags detected": [k for k, i in FINGER_IDS.items() if res.get(i)],
        "finger tag edge (px)": finger_px,
        "target detected": bool(res.get(TARGET_ID)),
        "target edge (px)": res[TARGET_ID]["tag_edge_px"] if res.get(TARGET_ID) else None,
    }
    cad = cad_view(p, w, fr["lens"], fr["scene"], fr["past"])
    marked = soft.copy()                            # outline every tag that is wholly in the picture
    for t in tags:
        if in_frame[t["name"]]:
            cv2.polylines(marked, [quads[t["id"]].astype(np.int32)], True, (40, 200, 60), 9, cv2.LINE_AA)
    return marked, cad, info, crop


# --- composing the GIF ---------------------------------------------------------------------------

PANEL = (600, 450)
M, TITLE_H, CAP_H = 12, 46, 76
W = M * 3 + PANEL[0] * 2
H = TITLE_H + PANEL[1] + CAP_H
GREEN, RED, INK, GREY = (20, 140, 50), (200, 30, 30), (25, 25, 25), (95, 95, 95)

TITLES = {
    1: "1/3  As ordered: the HQ with the 6 mm lens",
    2: "2/3  The OT-2's 8-50 mm zoom on the same wrist camera",
    3: "3/3  To read something small, keep the 6 mm and move the arm closer",
}


def font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(str(FONTS / ("DejaVuSans-Bold.ttf" if bold else "DejaVuSans.ttf")), size)


def compose(fr: dict, pic: np.ndarray, cad: np.ndarray, info: dict, w: World, crop=None) -> Image.Image:
    canvas = Image.new("RGB", (W, H), "white")
    dr = ImageDraw.Draw(canvas)
    dr.text((M, 11), TITLES[fr["act"]], fill=INK, font=font(22, True))
    pic_im = Image.fromarray(pic).resize(PANEL, Image.LANCZOS)
    if crop is None:
        canvas.paste(Image.fromarray(cad).resize(PANEL, Image.LANCZOS), (M, TITLE_H))
    else:
        top = PANEL[1] - CROP[1] - 4
        cad_im = Image.fromarray(cad)
        h = int(cad_im.width * top / PANEL[0])
        y0 = (cad_im.height - h) // 2
        canvas.paste(cad_im.crop((0, y0, cad_im.width, y0 + h)).resize((PANEL[0], top), Image.LANCZOS),
                     (M, TITLE_H))
        canvas.paste(Image.fromarray(crop), (M, TITLE_H + PANEL[1] - CROP[1]))
        tag = "1:1 pixels (2028 x 1520 mode); text 2.5, 1.6 and 1 mm tall"
        tw = dr.textlength(tag, font=font(14))
        box = Image.new("RGBA", (int(tw) + 12, 22), (255, 255, 255, 215))
        canvas.paste(box, (M + 4, TITLE_H + PANEL[1] - CROP[1] + 4), box)
        dr.text((M + 10, TITLE_H + PANEL[1] - CROP[1] + 6), tag, fill=INK, font=font(14))
    canvas.paste(pic_im, (2 * M + PANEL[0], TITLE_H))
    dr.rectangle([M, TITLE_H, M + PANEL[0] - 1, TITLE_H + PANEL[1] - 1], outline=(200, 200, 200))
    x0 = 2 * M + PANEL[0]
    # what the HQ sees: a status box on the picture
    f = info["focal length (mm)"]
    hf, vf = info["field of view (deg, across x up)"]
    lens = "6 mm lens" if fr["lens"] == "6mm" else f"zoom at {f:.0f} mm"
    lines = [(f"What the HQ sees: {lens}, {hf:.0f} x {vf:.0f} deg", INK)]
    n_in = sum(v for k, v in info["wholly in the picture"].items() if "finger" in k)
    n_found = len(info["finger tags detected"])
    if n_in == 2:
        lines.append(("finger tags: both in the picture" + (", both found" if n_found == 2 else ""), GREEN))
    else:
        lines.append(("finger tags: out of the picture" if n_in == 0 else "finger tags: 1 of 2 in the picture", RED))
    if fr["scene"] == "target":
        px = info["tag edge, projected (px)"]["target"]
        if info["wholly in the picture"]["target"]:
            found = ", found" if info["target detected"] and fr["act"] == 1 else ""
            lines.append((f"target: in the picture, {px:.0f} px across{found}", GREEN))
        else:
            lines.append(("target: no longer fits in the picture", RED))
    else:
        lines.append((f"label {fr['past']:.0f} mm away: {info['px per mm on the card']:.0f} px/mm, "
                      f"{info['blur on the card, defocus and diffraction (px)']:.0f} px of blur", INK))
    if fr["lens"] == "zoom" and info["focused at (mm)"] > info["card distance along the axis (mm)"] + 0.5:
        lines.append((f"can't focus nearer than {info['closest focus (mm)']:.0f} mm: target "
                      f"{info['card distance along the axis (mm)']:.0f} mm away", RED))
    fs = font(16)
    box_h = 8 + 21 * len(lines)
    box_w = max(dr.textlength(t, font=fs) for t, _ in lines) + 16
    overlay = Image.new("RGBA", (int(box_w), box_h), (255, 255, 255, 215))
    canvas.paste(overlay, (x0 + 8, TITLE_H + 8), overlay)
    for i, (t, c) in enumerate(lines):
        dr.text((x0 + 16, TITLE_H + 12 + 21 * i), t, fill=c, font=fs)
    # the lens: a label on the CAD panel
    if fr["lens"] == "zoom":
        cad_lines = [("8-50 mm zoom: O40 x 73 mm with its adapter, 148 g", INK),
                     (f"front {info['lens front behind the fingertips (mm)']:.0f} mm behind the tips "
                      f"(the 6 mm's: 90)", INK)]
        if w.clash:
            cad_lines.append(("red: where it would cut into the bracket and finger plate", RED))
    else:
        cad_lines = [("6 mm lens: O30 x 34 mm, 53 g", INK)]
        if fr["scene"] == "label":
            cad_lines.append((f"lens {fr['past']:.0f} mm from the label", INK))
    box_h = 8 + 21 * len(cad_lines)
    box_w = max(dr.textlength(t, font=fs) for t, _ in cad_lines) + 16
    overlay = Image.new("RGBA", (int(box_w), box_h), (255, 255, 255, 215))
    canvas.paste(overlay, (M + 8, TITLE_H + 8), overlay)
    for i, (t, c) in enumerate(cad_lines):
        dr.text((M + 16, TITLE_H + 12 + 21 * i), t, fill=c, font=fs)
    # caption
    cap = CAPTIONS[fr["act"]]
    for i, t in enumerate(cap):
        dr.text((M, TITLE_H + PANEL[1] + 10 + 24 * i), t, fill=GREY if i else INK, font=font(17))
    return canvas


CAPTIONS = {
    1: ["Both finger tags and a 20 mm target 60 mm past the tips in one picture, all found by the detector.",
        "Simulated from the CAD: fingers 40 mm apart, f/8, focused 108 mm out."],
    2: ["Zooming in narrows the view to a patch the fingers and then the target fall out of.",
        "The zoom is also 39 mm longer, 2.8 times heavier, and cuts into the bracket."],
    3: ["Moving the gripper in does what zooming would: the label grows to readable size.",
        "Nothing on the camera changes, so its one calibration still holds, and the fingers stay in view."],
}


def save_gif(frames: list[Image.Image], holds: list[float], path: Path) -> None:
    """One palette for every frame, taken from a strip of frames across all three parts."""
    pick = frames[:: max(1, len(frames) // 10)]
    strip = Image.new("RGB", (W // 2, H // 2 * len(pick)))
    for i, im in enumerate(pick):
        strip.paste(im.resize((W // 2, H // 2)), (0, H // 2 * i))
    pal = strip.quantize(colors=255, method=Image.Quantize.MEDIANCUT)
    q = [im.quantize(palette=pal, dither=Image.Dither.NONE) for im in frames]
    q[0].save(path, save_all=True, append_images=q[1:], duration=[int(h * 1000) for h in holds], loop=0,
              optimize=True, disposal=1)


def captions(infos: list[dict], frames: list[dict]) -> dict:
    zoom = [(fr["f"], i) for fr, i in zip(frames, infos) if fr["act"] == 2]
    lost = next((f for f, i in zoom if not i["wholly in the picture"]["target"]), None)
    blurred = next((f for f, i in zoom if i["focused at (mm)"] > i["card distance along the axis (mm)"] + 0.5), None)
    lab = [i for fr, i in zip(frames, infos) if fr["act"] == 3]
    one = infos[0]
    return {
        1: [f"Both finger tags and a 20 mm target 60 mm past the tips in one picture, all found by the AprilTag detector.",
            f"Simulated from the CAD: fingers {OPENING:.0f} mm apart, f/8, focused {SIX_FOCUS:.0f} mm out. "
            f"The target is {one['target edge (px)']:.0f} px across."],
        2: [f"Even at 8 mm the fingers are out of the picture: the zoom's front is 39 mm further forward, and it sees "
            f"43 degrees across, not 55.",
            f"The target no longer fits past {lost:.0f} mm, and from {blurred:.0f} mm the zoom can't focus that close. "
            f"It's also 2.8 times heavier, and cuts into the bracket."],
        3: [f"Moving the lens from {lab[0]['label in front of the lens (mm)']:.0f} to "
            f"{lab[-1]['label in front of the lens (mm)']:.0f} mm does what zooming would: "
            f"{lab[0]['px per mm on the card']:.0f} to {lab[-1]['px per mm on the card']:.0f} px/mm, "
            f"and into the 6 mm's sharpest distance.",
            "Nothing on the camera changes, so its one calibration still holds, and the fingers stay in view."],
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--quick", action="store_true", help="a few frames, to check the layout")
    args = ap.parse_args()
    p6 = Params()
    w = World(p6)
    det = detector()
    frames = frame_list(args.quick)
    rendered, infos = [], []
    for fr in frames:
        pic, cad, info, crop = render_frame(fr, w, det)
        rendered.append((cv2.resize(pic, PANEL, interpolation=cv2.INTER_AREA), cad, crop))
        infos.append(info)
        print(fr["act"], fr["lens"], fr["f"], fr["past"], info["finger tags detected"], info["target detected"],
              info["target edge (px)"], info["focused at (mm)"], info["blur on the card, defocus only (px)"],
              info["px per mm on the card"], flush=True)
    CAPTIONS.update(captions(infos, frames))
    images = [compose(fr, pic, cad, info, w, crop) for fr, (pic, cad, crop), info in zip(frames, rendered, infos)]
    out = RENDERS / ("wrist_zoom_quick.gif" if args.quick else "wrist_zoom.gif")
    save_gif(images, [fr["hold"] for fr in frames], out)
    if args.quick:
        for i, im in enumerate(images):
            im.save(RENDERS / f"_wrist_zoom_quick_{i}.png")
    print(out, round(out.stat().st_size / 1e6, 2), "MB")
    if not args.quick:
        (EXPORTS / "wrist_zoom.json").write_text(json.dumps({
            "lenses": {
                "6 mm": {"od x length (mm)": [30.0, 34.0], "mass (g)": SIX_MASS, "f-number": N,
                         "focused at (mm)": SIX_FOCUS},
                "Waveshare 8-50 mm zoom": {"od x length (mm)": [ZOOM_OD, ZOOM_LEN], "C-CS adapter (mm)": ADAPTER,
                                           "mass (g)": ZOOM_MASS, "minimum object distance (mm)": ZOOM_MOD,
                                           "f-number": N},
            },
            "fit": w.fit,
            "captions": CAPTIONS,
            "frames": infos,
        }, indent=1) + "\n")


if __name__ == "__main__":
    main()
