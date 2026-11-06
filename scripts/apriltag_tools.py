#!/usr/bin/env python3
"""AprilTag helpers for the PiPER cell (issue #24, PR #40).

    python scripts/apriltag_tools.py sheet      # true-scale print sheets (vector PDF) + a raster check
    python scripts/apriltag_tools.py detect IMAGE... [--size-mm 100] [--annotate-dir DIR]
    python scripts/apriltag_tools.py simulate   # how small / how tilted a tag can be at 1280x720
    python scripts/apriltag_tools.py figures    # tag contact sheet and the detectability figure
    python scripts/apriltag_tools.py placement  # zone markers on the two stream frames in docs/issue-24/apriltags/frames/
    python scripts/apriltag_tools.py handeye-selftest   # eye-to-hand recipe on synthetic poses with a known answer

Family: tag36h11 (IDs 0-586). The bit patterns are the official AprilRobotics/apriltag-imgs PNGs
(10x10 px: a 1-px white quiet zone around an 8x8 block, which is a 1-px black border plus 6x6 data
bits). They are fetched on first use and cached in docs/issue-24/apriltags/tags/. Do not generate the
bits with cv2.aruco.generateImageMarker(DICT_APRILTAG_36h11): its image is the official one rotated
180 degrees, so poses would disagree with every other AprilTag tool by 180 degrees about the normal.

Needs numpy, opencv-python-headless, pupil-apriltags; reportlab (sheet), pymupdf (sheet check) and
matplotlib (figures). Everything here is offline except the first download of the tag images.
"""
import argparse
import json
import sys
import urllib.request
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[1]
OUT = REPO / "docs/issue-24/apriltags"
TAGS_DIR = OUT / "tags"
OFFICIAL = "https://raw.githubusercontent.com/AprilRobotics/apriltag-imgs/master/tag36h11/tag36_11_{:05d}.png"

# Camera Module 3 Wide as the repo's twin models it (piper_camera_fixtures.py: f = 1964 px at 4608 px).
F_1280 = 1964.0 * 1280 / 4608  # 545.6 px at the 1280 x 720 the livestreams use

# What goes on the print sheets: (title, black-square size in mm, IDs).
SHEETS = [
    ("Large workspace tags, 150 mm (far from the camera)", 150, [4, 5]),
    ("Workspace tags, 100 mm", 100, [0, 1, 2, 3]),
    ("Mid-size tags, 50 mm", 50, list(range(10, 19))),
    ("Small tags, 25 mm", 25, list(range(30, 54))),
]


def tag_bits(tag_id, tags_dir=TAGS_DIR):
    """10x10 uint8 array, 1 = white, for a tag36h11 ID (the official image, incl. 1-px quiet zone)."""
    import cv2

    p = Path(tags_dir) / f"tag36_11_{tag_id:05d}.png"
    if not p.exists():
        p.parent.mkdir(parents=True, exist_ok=True)
        with urllib.request.urlopen(OFFICIAL.format(tag_id), timeout=30) as r:
            p.write_bytes(r.read())
    im = cv2.imread(str(p), cv2.IMREAD_GRAYSCALE)
    assert im is not None and im.shape == (10, 10), f"unexpected tag image {p}"
    return (im > 127).astype(np.uint8)


# ------------------------------------------------------------------ print sheets


def _draw_tag(c, cx, cy, size_mm, bits):
    """Draw a tag as one vector path, centred at (cx, cy) mm. size_mm is the black square's side."""
    from reportlab.lib.units import mm

    cell = size_mm / 8.0
    x0, y0 = cx - 5 * cell, cy + 5 * cell
    path = c.beginPath()
    for r in range(10):
        for k in range(10):
            if bits[r, k] == 0:
                path.rect((x0 + k * cell) * mm, (y0 - (r + 1) * cell) * mm, cell * mm, cell * mm)
    c.setFillGray(0)
    c.drawPath(path, stroke=0, fill=1)


def _ruler(c, x, y, length_mm):
    from reportlab.lib.units import mm

    c.setLineWidth(0.5)
    c.setStrokeGray(0)
    c.line(x * mm, y * mm, (x + length_mm) * mm, y * mm)
    for i in range(0, int(length_mm) + 1, 10):
        c.line((x + i) * mm, y * mm, (x + i) * mm, (y + (3 if i % 50 == 0 else 2)) * mm)
        if i % 50 == 0:
            c.setFont("Helvetica", 6)
            c.drawCentredString((x + i) * mm, (y + 3.6) * mm, f"{i}")
    c.setFont("Helvetica", 6)
    c.drawString((x + length_mm + 2) * mm, (y - 1) * mm, "mm")


def make_sheets(pdf_path, page_w=215.9, page_h=279.4):
    """US Letter, portrait unless a tag is too wide for it. Returns the layout actually used."""
    from reportlab.lib.units import mm
    from reportlab.pdfgen import canvas

    c = canvas.Canvas(str(pdf_path), pagesize=(page_w * mm, page_h * mm))
    c.setTitle("AprilTag tag36h11 print sheets, PiPER cell (robot-arms #24)")
    layout = []
    margin, gap, label_h, head_h, foot_h = 10.0, 4.0, 5.0, 14.0, 16.0
    for title, size, ids in SHEETS:
        foot = size * 1.25  # black square plus the 1-cell white quiet zone on every side
        best = None
        for landscape in (False, True):  # whichever orientation holds more tags
            w, h = (page_h, page_w) if landscape else (page_w, page_h)
            cols = int((w - 2 * margin + gap) // (foot + gap))
            rows = int((h - 2 * margin - head_h - foot_h + gap) // (foot + gap + label_h))
            if best is None or cols * rows > best[0]:
                best = (cols * rows, landscape, w, h, cols, rows)
        per_page, landscape, w, h, cols, rows = best
        assert per_page >= 1, f"{size} mm tag does not fit on the page"
        for start in range(0, len(ids), per_page):
            chunk = ids[start:start + per_page]
            c.setPageSize((w * mm, h * mm))
            c.setFont("Helvetica-Bold", 10)
            c.setFillGray(0)
            c.drawString(margin * mm, (h - margin - 4) * mm, f"AprilTag tag36h11, black square {size} mm: {title}")
            c.setFont("Helvetica", 7)
            c.drawString(margin * mm, (h - margin - 9) * mm,
                         "Print at 100 % / Actual size (no 'fit to page'). The white border (1 cell) is part of the tag; do not trim into it. "
                         "Measure the BLACK square, not the paper.")
            grid_w = cols * foot + (cols - 1) * gap
            x_start = (w - grid_w) / 2
            for i, tid in enumerate(chunk):
                r, k = divmod(i, cols)
                left = x_start + k * (foot + gap)
                top = h - margin - head_h - r * (foot + gap + label_h)
                cx, cy = left + foot / 2, top - foot / 2
                _draw_tag(c, cx, cy, size, tag_bits(tid))
                # cut marks just outside the quiet zone's corners
                c.setStrokeGray(0.6)
                c.setLineWidth(0.3)
                for sx in (-1, 1):
                    for sy in (-1, 1):
                        px, py = cx + sx * foot / 2, cy + sy * foot / 2
                        c.line((px + sx * 1) * mm, py * mm, (px + sx * 3) * mm, py * mm)
                        c.line(px * mm, (py + sy * 1) * mm, px * mm, (py + sy * 3) * mm)
                c.setFillGray(0)
                c.setFont("Helvetica", 7)
                c.drawCentredString(cx * mm, (cy - foot / 2 - 4) * mm, f"tag36h11  ID {tid}  |  {size} mm")
            bar = 100 if size >= 100 else 50
            c.setStrokeGray(0)
            _ruler(c, margin, margin + 4, bar)
            c.setFont("Helvetica", 7)
            c.drawString((margin + bar + 12) * mm, (margin + 3) * mm,
                         f"Check bar: it must measure {bar} mm. If not, the print was scaled.")
            c.showPage()
            layout.append({"title": title, "size_mm": size, "ids": chunk, "landscape": landscape})
    c.save()
    return layout


def check_sheets(pdf_path, layout, dpi=300):
    """Rasterise the PDF, run the AprilTag detector on every page and compare size and IDs."""
    import fitz  # pymupdf
    import cv2
    from pupil_apriltags import Detector

    det = Detector(families="tag36h11", quad_decimate=1.0, refine_edges=True)
    doc = fitz.open(str(pdf_path))
    report = []
    for page, spec in zip(doc, layout):
        pix = page.get_pixmap(dpi=dpi, colorspace=fitz.csGRAY)
        img = np.frombuffer(pix.samples, np.uint8).reshape(pix.height, pix.width)
        found = det.detect(img)
        side_mm = []
        for d in found:
            cc = d.corners
            side_px = np.mean([np.linalg.norm(cc[i] - cc[(i + 1) % 4]) for i in range(4)])
            side_mm.append(side_px / dpi * 25.4)
        ok_ids = sorted(d.tag_id for d in found) == sorted(spec["ids"])
        report.append({"size_mm": spec["size_mm"], "ids_expected": spec["ids"],
                       "ids_found": sorted(int(d.tag_id) for d in found), "ids_match": ok_ids,
                       "measured_side_mm_min": round(min(side_mm), 2) if side_mm else None,
                       "measured_side_mm_max": round(max(side_mm), 2) if side_mm else None})
    return report


def cmd_sheet(args):
    OUT.mkdir(parents=True, exist_ok=True)
    pdf = OUT / "tag36h11_print_sheets.pdf"
    layout = make_sheets(pdf)
    rep = check_sheets(pdf, layout)
    (OUT / "sheet_check.json").write_text(json.dumps({"pages": rep}, indent=1) + "\n")
    for p in rep:
        print(p)
    import fitz
    doc = fitz.open(str(pdf))
    for i, page in enumerate(doc, 1):
        page.get_pixmap(dpi=60).save(str(OUT / f"sheet_page{i}.png"))
    print("wrote", pdf, "and sheet_check.json")


# ------------------------------------------------------------------ detection


def cmd_detect(args):
    import cv2
    from pupil_apriltags import Detector

    det = Detector(families="tag36h11", quad_decimate=1.0, refine_edges=True)
    for path in args.images:
        img = cv2.imread(path)
        if img is None:
            print(path, ": cannot read")
            continue
        h, w = img.shape[:2]
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        f = args.focal_px if args.focal_px else F_1280 * w / 1280
        res = det.detect(gray, estimate_tag_pose=bool(args.size_mm), camera_params=[f, f, w / 2, h / 2],
                         tag_size=(args.size_mm or 100) / 1000.0)
        print(f"{path}: {w}x{h}, {len(res)} tag(s)")
        for d in sorted(res, key=lambda r: r.tag_id):
            cc = d.corners
            sides = [float(np.linalg.norm(cc[i] - cc[(i + 1) % 4])) for i in range(4)]
            line = f"  ID {d.tag_id:3d}  sides {min(sides):5.1f}-{max(sides):5.1f} px  margin {d.decision_margin:5.1f}"
            if args.size_mm:
                t = d.pose_t.ravel()
                nz = d.pose_R[:, 2]
                tilt = np.degrees(np.arccos(min(1.0, abs(nz @ (t / np.linalg.norm(t))))))
                line += f"  distance {np.linalg.norm(t):.3f} m  tilt {tilt:4.1f} deg  pose error {d.pose_err:.1e}"
            print(line)
            cv2.polylines(img, [cc.astype(np.int32)], True, (0, 255, 0), 2)
            cv2.putText(img, str(d.tag_id), tuple(int(v) for v in cc[3]), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2)
        if args.annotate_dir:
            Path(args.annotate_dir).mkdir(parents=True, exist_ok=True)
            cv2.imwrite(str(Path(args.annotate_dir) / (Path(path).stem + "_tags.jpg")), img)


# ------------------------------------------------------------------ simulation


def _texture(bits, cell_px=16):
    import cv2
    return cv2.resize((bits * 255).astype(np.uint8), None, fx=cell_px, fy=cell_px, interpolation=cv2.INTER_NEAREST)


def render_tag(bg, tex, quad_px, ss=4):
    """Paste the 10x10-cell texture into float image `bg` with its footprint corners at quad_px
    (TL, TR, BR, BL; image pixels). Rendered 4x oversampled then area-averaged, so edges are antialiased."""
    import cv2

    quad = np.asarray(quad_px, np.float64)
    x0, y0 = np.floor(quad.min(0)).astype(int) - 2
    x1, y1 = np.ceil(quad.max(0)).astype(int) + 2
    x0, y0 = max(x0, 0), max(y0, 0)
    x1, y1 = min(x1, bg.shape[1]), min(y1, bg.shape[0])
    if x1 <= x0 or y1 <= y0:
        return
    th, tw = tex.shape
    src = np.float32([[0, 0], [tw, 0], [tw, th], [0, th]])
    dst = ((quad - [x0, y0]) * ss).astype(np.float32)
    big = (int((x1 - x0) * ss), int((y1 - y0) * ss))
    M = cv2.getPerspectiveTransform(src, dst)
    val = cv2.warpPerspective(tex, M, big, flags=cv2.INTER_NEAREST, borderValue=0)
    msk = cv2.warpPerspective(np.full_like(tex, 255), M, big, flags=cv2.INTER_NEAREST, borderValue=0)
    val = cv2.resize(val.astype(np.float32), (x1 - x0, y1 - y0), interpolation=cv2.INTER_AREA)
    msk = cv2.resize(msk.astype(np.float32), (x1 - x0, y1 - y0), interpolation=cv2.INTER_AREA) / 255.0
    bg[y0:y1, x0:x1] = bg[y0:y1, x0:x1] * (1 - msk) + val * msk


def synth_frame(tex, size_m, frontal_px, tilt_deg, rng, W=1280, H=720, f=F_1280, roll_deg=None,
                blur_sigma=0.8, noise=3.0, jpeg_q=85):
    """A 1280x720 frame with one tag at the given frontal width (px, as if face-on) turned `tilt_deg`
    about a random in-plane axis. Returns (uint8 image, truth dict)."""
    import cv2

    Z = f * size_m / frontal_px
    cx, cy = W / 2 + rng.uniform(-200, 200), H / 2 + rng.uniform(-100, 100)
    t = np.array([(cx - W / 2) * Z / f, (cy - H / 2) * Z / f, Z])
    roll = np.deg2rad(rng.uniform(0, 360) if roll_deg is None else roll_deg)
    # reference pose: the tag faces the line of sight to its centre (so `tilt_deg` is measured from the
    # line of sight, not from the optical axis), turned by a random roll about it
    d = t / np.linalg.norm(t)
    a = np.array([0.0, 1.0, 0.0])
    u = np.cross(a, d)
    u /= np.linalg.norm(u)
    v = np.cross(d, u)
    ex0, ey0 = np.cos(roll) * u + np.sin(roll) * v, -np.sin(roll) * u + np.cos(roll) * v
    ax = np.deg2rad(rng.uniform(0, 360))  # axis of the tilt, in the tag plane
    axis = np.cos(ax) * ex0 + np.sin(ax) * ey0
    th = np.deg2rad(tilt_deg)
    def rot(v):  # Rodrigues, about `axis`
        return v * np.cos(th) + np.cross(axis, v) * np.sin(th) + axis * (axis @ v) * (1 - np.cos(th))
    ex, ey = rot(ex0), rot(ey0)
    half = size_m * 10 / 8 / 2
    K = np.array([[f, 0, W / 2], [0, f, H / 2], [0, 0, 1.0]])
    quad = []
    for X, Y in [(-half, -half), (half, -half), (half, half), (-half, half)]:
        p = K @ (t + X * ex + Y * ey)
        quad.append(p[:2] / p[2])
    # light, textured background, like the plywood
    low = cv2.GaussianBlur(rng.normal(0, 1, (H, W)).astype(np.float32), (0, 0), 25) * 60
    grain = cv2.GaussianBlur(rng.normal(0, 1, (H, W)).astype(np.float32), (0, 0), 1.5) * 12
    bg = np.clip(150 + low + grain, 40, 235).astype(np.float32)
    render_tag(bg, tex, quad)
    bg = cv2.GaussianBlur(bg, (0, 0), blur_sigma) + rng.normal(0, noise, bg.shape).astype(np.float32)
    img = np.clip(bg, 0, 255).astype(np.uint8)
    ok, enc = cv2.imencode(".jpg", img, [cv2.IMWRITE_JPEG_QUALITY, jpeg_q])
    img = cv2.imdecode(enc, cv2.IMREAD_GRAYSCALE)
    normal = np.cross(ex, ey)
    return img, {"t": t, "normal": normal, "Z": Z, "quad": np.array(quad)}


def simulate(widths, tilts, trials, size_m=0.1, tag_id=7, seed=1):
    from pupil_apriltags import Detector

    rng = np.random.default_rng(seed)
    tex = _texture(tag_bits(tag_id))
    det = Detector(families="tag36h11", quad_decimate=1.0, refine_edges=True, nthreads=4)
    cam = [F_1280, F_1280, 640.0, 360.0]
    rows = []
    for w in widths:
        for tilt in tilts:
            hit, nerr, terr = 0, [], []
            for _ in range(trials):
                img, truth = synth_frame(tex, size_m, w, tilt, rng)
                res = [r for r in det.detect(img, estimate_tag_pose=True, camera_params=cam, tag_size=size_m)
                       if r.tag_id == tag_id]
                if len(res) == 1:
                    hit += 1
                    n_est = res[0].pose_R[:, 2]
                    nerr.append(float(np.degrees(np.arccos(min(1.0, abs(n_est @ truth["normal"]))))))
                    terr.append(float(np.linalg.norm(res[0].pose_t.ravel() - truth["t"]) / truth["Z"] * 100))
            rows.append({"frontal_px": w, "tilt_deg": tilt, "trials": trials, "detected": hit,
                         "rate": hit / trials,
                         "normal_err_deg_median": float(np.median(nerr)) if nerr else None,
                         "normal_err_deg_p90": float(np.percentile(nerr, 90)) if nerr else None,
                         "position_err_pct_median": float(np.median(terr)) if terr else None})
            print(rows[-1], flush=True)
    return rows


def cmd_simulate(args):
    OUT.mkdir(parents=True, exist_ok=True)
    widths = [10, 14, 20, 28, 40, 56, 80, 120]
    tilts = [0, 30, 50, 65, 75]
    rows = simulate(widths, tilts, args.trials)
    (OUT / "detectability.json").write_text(json.dumps(
        {"note": "tag36h11, pupil-apriltags (AprilTag 3, quad_decimate 1), 1280x720, pinhole f=545.6 px, no lens "
                 "distortion, known intrinsics, blur sigma 0.8 px, noise sigma 3/255, JPEG q85, textured light "
                 "background. Best case: real accuracy also depends on calibration, print scale and flatness.",
         "frontal_px_definition": "width in px of the 8-cell black square if it faced the camera at that distance",
         "tilt_definition": "angle between the tag's normal and the line of sight to its centre; random tilt axis and roll",
         "rows": rows}, indent=1) + "\n")


# ------------------------------------------------------------------ placement figure

# Hand-placed from the two 2026-11-06 stream frames (1280x720, docs/issue-24/apriltags/frames/):
# (kind, label, x, y). Approximate: the table's contents move, so these are areas, not coordinates.
ZONES = {
    "eufi_back_2026-11-06.jpg": [
        ("A", "A", 594, 412), ("W", "W", 600, 545), ("W", "W", 850, 640), ("W", "W", 250, 600),
        ("S", "S", 420, 335), ("S", "S", 497, 420), ("X", (600, 20, 1140, 170), 0, 0)],
    "mpzy_front_2026-11-06.jpg": [
        ("A", "A", 652, 392), ("W", "W", 885, 482), ("W", "W", 935, 640), ("W", "W", 975, 410),
        ("S", "S", 490, 488), ("S", "S", 640, 445), ("X", (110, 20, 1000, 160), 0, 0)],
}
KIND_STYLE = {"A": "#009E73", "W": "#0072B2", "S": "#D55E00", "X": "#555555"}


def cmd_placement(args):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import cv2

    fig, axs = plt.subplots(1, 2, figsize=(16, 4.95))
    titles = {"eufi_back_2026-11-06.jpg": "eufi, back camera (Module 3 Wide), stream frame 2026-11-06 01:43 UTC",
              "mpzy_front_2026-11-06.jpg": "mpzy, front camera (Module 3 Wide), stream frame 2026-11-06 01:43 UTC"}
    for ax, (name, zones) in zip(axs, ZONES.items()):
        img = cv2.cvtColor(cv2.imread(str(OUT / "frames" / name)), cv2.COLOR_BGR2RGB)
        ax.imshow(img)
        for kind, label, x, y in zones:
            col = KIND_STYLE[kind]
            if kind == "X":
                x0, y0, x1, y1 = label
                ax.add_patch(plt.Rectangle((x0, y0), x1 - x0, y1 - y0, fc=col, ec=col, alpha=0.22, hatch="//"))
                ax.text((x0 + x1) / 2, (y0 + y1) / 2, "curtains: no tags", ha="center", va="center", color="white",
                        fontsize=11, bbox=dict(boxstyle="round", fc=col, ec="none", alpha=0.85))
                continue
            ax.add_patch(plt.Circle((x, y), 19, fc=col, ec="white", lw=2, alpha=0.95))
            ax.text(x, y, label, ha="center", va="center", color="white", fontsize=9.5, fontweight="bold")
        ax.set_title(titles[name], fontsize=10)
        ax.set_xlim(0, 1280); ax.set_ylim(720, 0); ax.axis("off")
    fig.suptitle("Where tags could go (approximate areas, drawn by hand on the stream frames; no tags are placed yet)", fontsize=11)
    fig.tight_layout(rect=(0, 0.045, 1, 1))
    fig.text(0.5, 0.012, "A = arm base     W = workspace tag, flat on the topper (100-150 mm)     "
             "S = station tag on a rack, plate or holder (25-50 mm)     hatched = canvas curtains",
             ha="center", fontsize=10.5)
    fig.savefig(OUT / "placement_zones.jpg", dpi=110, pil_kwargs={"quality": 88})
    print("wrote", OUT / "placement_zones.jpg")


# ------------------------------------------------------------------ hand-eye self-test


def cmd_handeye_selftest(args):
    """Check the eye-to-hand recipe on synthetic poses with a known answer: a FIXED camera, a tag on the
    gripper. Feed cv2.calibrateHandEye the INVERTED gripper poses (base->gripper) with the tag-in-camera
    poses, and the 'cam2gripper' it returns is the camera's pose in the robot base frame (cam2base)."""
    import cv2

    rng = np.random.default_rng(3)

    def T(R, t):
        M = np.eye(4)
        M[:3, :3], M[:3, 3] = R, t
        return M

    def rv(v):
        return cv2.Rodrigues(np.asarray(v, float))[0]

    def rot_err_deg(Ra, Rb):
        return float(np.degrees(np.arccos(np.clip((np.trace(Ra.T @ Rb) - 1) / 2, -1, 1))))

    T_B_C = T(rv([2.2, 0.1, -0.3]), [0.9, -0.6, 0.5])    # truth: fixed camera -> base
    T_G_T = T(rv([0.3, -0.2, 0.5]), [0.02, 0.01, 0.05])  # truth: tag -> gripper
    for noise_px_deg, label in [(0.0, "no noise"), (0.5, "0.5 deg / 2 mm noise on every tag pose")]:
        Rg, tg, Rt, tt = [], [], [], []
        for _ in range(args.poses):
            T_B_G = T(rv(rng.uniform(-1, 1, 3)), rng.uniform([0.2, -0.3, 0.1], [0.5, 0.3, 0.4]))  # gripper -> base
            T_C_T = np.linalg.inv(T_B_C) @ T_B_G @ T_G_T  # the tag as the camera sees it
            if noise_px_deg:
                T_C_T = T_C_T @ T(rv(np.radians(rng.normal(0, noise_px_deg, 3))), rng.normal(0, 0.002, 3))
            T_G_B = np.linalg.inv(T_B_G)  # base -> gripper
            Rg.append(T_G_B[:3, :3]); tg.append(T_G_B[:3, 3:]); Rt.append(T_C_T[:3, :3]); tt.append(T_C_T[:3, 3:])
        R, t = cv2.calibrateHandEye(Rg, tg, Rt, tt, method=cv2.CALIB_HAND_EYE_PARK)
        print(f"{label}: {args.poses} poses -> camera-in-base error {rot_err_deg(R, T_B_C[:3, :3]):.3f} deg, "
              f"{np.linalg.norm(t.ravel() - T_B_C[:3, 3]) * 1000:.2f} mm")


# ------------------------------------------------------------------ figures


def cmd_figures(args):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    OUT.mkdir(parents=True, exist_ok=True)
    # 1. candidate tags + anatomy
    ids = [0, 1, 2, 3, 10, 11, 12, 13]
    fig = plt.figure(figsize=(12, 5.4))
    gs = fig.add_gridspec(2, 6, width_ratios=[2.6, 1, 1, 1, 1, 0.05], hspace=0.28, wspace=0.18)
    ax = fig.add_subplot(gs[:, 0])
    ax.imshow(tag_bits(0), cmap="gray", vmin=0, vmax=1, interpolation="nearest", extent=(-1, 9, 9, -1))
    ax.add_patch(plt.Rectangle((-1, -1), 10, 10, fill=False, ls="--", ec="tab:blue", lw=1.2))
    ax.set_xlim(-1.8, 9.8); ax.set_ylim(11.4, -2.6)
    ax.annotate("", xy=(0, -1.6), xytext=(8, -1.6), arrowprops=dict(arrowstyle="<->", color="tab:red"))
    ax.text(4, -2.0, "tag size S = the black square (8 cells): measure this", color="tab:red", ha="center", fontsize=9)
    ax.text(4, 10.1, "dashed = paper edge. Keep the white border, 1 cell (S/8)\non every side, or the detector can't see the black edge.",
            color="tab:blue", ha="center", va="top", fontsize=8.5)
    ax.annotate("", xy=(6.4, 4), xytext=(4, 4), arrowprops=dict(arrowstyle="->", color="tab:green", lw=2.5))
    ax.annotate("", xy=(4, 6.4), xytext=(4, 4), arrowprops=dict(arrowstyle="->", color="tab:green", lw=2.5))
    ax.plot(4, 4, "o", mfc="none", mec="tab:green", ms=13, mew=2)
    ax.plot(4, 4, "x", c="tab:green", ms=8, mew=2)
    ax.text(6.7, 4, "x", color="tab:green", fontsize=12, va="center", fontweight="bold")
    ax.text(4, 6.9, "y", color="tab:green", fontsize=12, ha="center", fontweight="bold")
    ax.text(3.35, 3.3, "z", color="tab:green", fontsize=12, ha="right", va="bottom", fontweight="bold")
    ax.set_title("tag36h11, ID 0 (official image)\ntag frame: x right, y down, z into the tag", fontsize=10)
    ax.axis("off")
    for i, tid in enumerate(ids):
        a = fig.add_subplot(gs[i // 4, 1 + i % 4])
        a.imshow(tag_bits(tid), cmap="gray", vmin=0, vmax=1, interpolation="nearest")
        a.set_title(f"ID {tid}" + ("\nworkspace, 100 mm" if tid < 10 else "\nmid-size, 50 mm"), fontsize=9)
        a.axis("off")
    fig.suptitle("Candidate tags (tag36h11, 587 IDs): same family, different IDs", fontsize=11)
    fig.savefig(OUT / "tag_candidates.png", dpi=130, bbox_inches="tight")
    plt.close(fig)

    # 2. detectability
    p = OUT / "detectability.json"
    if p.exists():
        rows = json.loads(p.read_text())["rows"]
        widths = sorted({r["frontal_px"] for r in rows})
        tilts = sorted({r["tilt_deg"] for r in rows})
        rate = np.full((len(tilts), len(widths)), np.nan)
        err = np.full_like(rate, np.nan)
        for r in rows:
            i, j = tilts.index(r["tilt_deg"]), widths.index(r["frontal_px"])
            rate[i, j] = r["rate"] * 100
            err[i, j] = r["normal_err_deg_median"] if r["normal_err_deg_median"] is not None else np.nan
        fig, axs = plt.subplots(1, 2, figsize=(12, 4.2))
        for a, M, title, cmap, fmt, vmax in [
            (axs[0], rate, "Detected (%), 24 noisy renders each", "Greens", "{:.0f}", 100),
            (axs[1], err, "Median error of the tag's normal (deg, best case)", "Reds", "{:.1f}", 6)]:
            im = a.imshow(M, origin="lower", cmap=cmap, vmin=0, vmax=vmax, aspect="auto")
            a.set_xticks(range(len(widths))); a.set_xticklabels(widths)
            a.set_yticks(range(len(tilts))); a.set_yticklabels(tilts)
            a.set_xlabel("width of the black square if it faced the camera (px at 1280 px)")
            a.set_ylabel("tilt away from the line of sight (deg)")
            a.set_title(title, fontsize=10)
            for i in range(len(tilts)):
                for j in range(len(widths)):
                    v = M[i, j]
                    a.text(j, i, "-" if np.isnan(v) else fmt.format(v), ha="center", va="center", fontsize=8,
                           color="white" if (not np.isnan(v) and v > 0.6 * vmax and cmap == "Greens") or (not np.isnan(v) and v > 0.6 * vmax and cmap == "Reds") else "black")
            fig.colorbar(im, ax=a, fraction=0.046)
        fig.suptitle("Simulated tag36h11 (AprilTag 3 detector) at 1280x720, blur + noise + JPEG; pinhole, no lens distortion", fontsize=10)
        fig.tight_layout()
        fig.savefig(OUT / "detectability.png", dpi=130)
        plt.close(fig)
    print("figures written to", OUT)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("sheet").set_defaults(fn=cmd_sheet)
    d = sub.add_parser("detect")
    d.add_argument("images", nargs="+")
    d.add_argument("--size-mm", type=float, help="black-square size: also estimate pose")
    d.add_argument("--focal-px", type=float, help="focal length in px of the given image (default: nominal Module 3 Wide)")
    d.add_argument("--annotate-dir")
    d.set_defaults(fn=cmd_detect)
    s = sub.add_parser("simulate")
    s.add_argument("--trials", type=int, default=24)
    s.set_defaults(fn=cmd_simulate)
    sub.add_parser("placement").set_defaults(fn=cmd_placement)
    h = sub.add_parser("handeye-selftest")
    h.add_argument("--poses", type=int, default=20)
    h.set_defaults(fn=cmd_handeye_selftest)
    sub.add_parser("figures").set_defaults(fn=cmd_figures)
    args = ap.parse_args()
    args.fn(args)


if __name__ == "__main__":
    sys.exit(main())
