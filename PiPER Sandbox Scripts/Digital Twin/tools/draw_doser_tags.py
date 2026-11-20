#!/usr/bin/env python3
"""Draw where the AprilTags go for the auger swap (config/powder_doser.yaml `apriltags`, plus
the table, arm-base and gripper tags of config/apriltags.yaml), rendered from the twin.

    MUJOCO_GL=egl python tools/draw_doser_tags.py
    -> ../AprilTags/apriltag_locations_augers.jpg

Three views (the whole cell, the doser, the rack), each tag labelled with its name, tag36h11
ID and size, and a key saying what each group is for.
"""
from __future__ import annotations

import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)

import cv2  # noqa: E402
import numpy as np  # noqa: E402

from digital_twin.config import load_config  # noqa: E402
from digital_twin.engines import make_engine  # noqa: E402
from digital_twin.world.doser_cell import DoserCell  # noqa: E402

OUT = os.path.join(os.path.dirname(ROOT), "AprilTags", "apriltag_locations_augers.jpg")
# Tag groups this job uses: prefix -> (colour BGR, what they're for)
GROUPS = {
    "W": ((40, 160, 40), "Table edges: the world frame; a moved camera shows up as all four shifting"),
    "A": ((200, 120, 0), "Arm base: puts the PiPER's base frame in the camera's view"),
    "G": ((180, 0, 180), "Gripper fingers: checks where FK says the gripper is (hand-eye)"),
    "D": ((0, 90, 230), "Doser: two on the baseplate's arms, one on the leg facing mpzy (not coplanar)"),
    "R": ((0, 170, 200), "Rack corners: the rack's pose"),
    "RS": ((0, 200, 255), "Rack slots: hidden while an auger sits there = which slots are full"),
    "U": ((60, 60, 220), "Auger caps: which powder each auger holds, and where its axis ends"),
}


def group(name):
    if name.startswith("RS"):
        return "RS"
    if name.startswith("U_"):
        return "U"
    return name[0] if name[0] in GROUPS else None


def project(cam, P, W, H):
    R, c = cam.pose[:3, :3], cam.pose[:3, 3]
    p = R.T @ (P - c)
    if p[2] >= -1e-6:
        return None
    f = (H / 2) / np.tan(np.radians(cam.fovy_deg) / 2)
    return np.array([W / 2 + f * p[0] / -p[2], H / 2 - f * p[1] / -p[2]])


def main():
    os.environ.setdefault("MUJOCO_GL", "egl")
    cfg = load_config()
    cell = DoserCell(cfg)
    seat = cell.doser_seat_world[:3, 3]
    slot = cell.slot_world(1)[:3, 3]
    arm = cell.arm_pose[:3, 3]
    views = {
        "overview": cell.add_view("tags_overview", [0.95, -0.85, 0.95], [0.14, 0.04, 0.06], 42, (1600, 1000)),
        "doser": cell.add_view("tags_doser", seat + np.array([0.20, -0.36, 0.30]), seat + np.array([0.10, 0.0, -0.07]),
                               50, (800, 560)),
        "rack": cell.add_view("tags_rack", slot + np.array([0.02, -0.42, 0.36]), slot + np.array([0.0, 0.03, -0.03]),
                              50, (800, 560)),
    }
    e = make_engine("mujoco", cell.scene, cfg)
    q = np.radians(cfg.robot["joints"]["ready_deg"])
    e.set_arm_q(q)
    e.mujoco.mj_forward(e.m, e.d)
    tags = [t for t in cell.scene.tags if group(t.name)]
    world = {t.name: (e.body_pose(t.body) @ t.pose)[:3, 3] for t in tags}
    hidden = {"RS1", "RS2"}  # under the augers that start in slots 1 and 2
    imgs = {}
    for key, cam in views.items():
        W, H = cam.resolution
        img = cv2.cvtColor(e.render(cam.name, W, H), cv2.COLOR_RGB2BGR)
        placed = []
        for t in tags:
            if key == "overview" and t.name in ("RS0", "RS1", "RS2"):
                continue
            uv = project(cam, world[t.name], W, H)
            if uv is None or not (0 <= uv[0] < W and 0 <= uv[1] < H):
                continue
            col, _ = GROUPS[group(t.name)]
            label = f"{t.name.replace('U_auger_', 'U ')} #{t.id} {t.size * 1000:.0f}mm"
            if t.name in hidden:
                label += " (under auger)"
            scale = 0.55 if key == "overview" else 0.5
            (tw, th), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, scale, 1)
            # Nudge labels apart: try a few offsets around the tag.
            for dx, dy in [(14, -14), (14, 18), (-tw - 14, -14), (-tw - 14, 18), (14, -40), (-tw - 14, -40),
                           (14, 44), (-tw - 14, 44)]:
                x0, y0 = int(uv[0] + dx), int(uv[1] + dy)
                box = (x0 - 3, y0 - th - 4, x0 + tw + 3, y0 + 5)
                if box[0] < 0 or box[2] >= W or box[1] < 0 or box[3] >= H:
                    continue
                if all(box[2] < b[0] or box[0] > b[2] or box[3] < b[1] or box[1] > b[3] for b in placed):
                    break
            placed.append(box)
            cv2.circle(img, tuple(int(v) for v in uv), 7, col, 2, cv2.LINE_AA)
            cv2.line(img, tuple(int(v) for v in uv), (box[0] if box[0] > uv[0] else box[2], (box[1] + box[3]) // 2),
                     col, 1, cv2.LINE_AA)
            cv2.rectangle(img, box[:2], box[2:], (255, 255, 255), -1)
            cv2.rectangle(img, box[:2], box[2:], col, 2)
            cv2.putText(img, label, (x0, y0), cv2.FONT_HERSHEY_SIMPLEX, scale, (20, 20, 20), 1, cv2.LINE_AA)
        imgs[key] = img
    top = imgs["overview"]
    bottom = np.hstack([imgs["doser"], imgs["rack"]])
    for im, txt in ((top, "The cell for the auger swap (doser right, rack front-right; printer and shelf tags not used)"),
                    (bottom[:, :800], "Doser: D1-D3 and the installed auger's cap tag"),
                    (bottom[:, 800:], "Rack: R1-R3 corners, a slot tag under each auger, cap tags")):
        cv2.rectangle(im, (0, 0), (im.shape[1], 30), (0, 0, 0), -1)
        cv2.putText(im, txt, (10, 21), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1, cv2.LINE_AA)
    panel = np.vstack([top, bottom])
    # Key on the right.
    key = np.full((panel.shape[0], 620, 3), 255, np.uint8)
    y = 40
    cv2.putText(key, "AprilTags for the auger swap (tag36h11)", (16, y), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 0), 2,
                cv2.LINE_AA)
    y += 20
    for g, (col, text) in GROUPS.items():
        names = [t for t in tags if group(t.name) == g]
        ids = ", ".join(f"{t.name.replace('U_auger_', '')} #{t.id}" for t in names)
        sizes = sorted({round(t.size * 1000) for t in names})
        y += 34
        cv2.rectangle(key, (16, y - 16), (36, y + 4), col, -1)
        cv2.putText(key, f"{g}  ({', '.join(str(s) for s in sizes)} mm)", (46, y), cv2.FONT_HERSHEY_SIMPLEX, 0.62,
                    (0, 0, 0), 2, cv2.LINE_AA)
        for line in _wrap(text, 58) + _wrap(ids, 62):
            y += 22
            cv2.putText(key, line, (46, y), cv2.FONT_HERSHEY_SIMPLEX, 0.48, (40, 40, 40), 1, cv2.LINE_AA)
    y += 40
    notes = ["Sizes are the black square. Print a white border one data",
             "square wide (1/8 of the black square) around every tag.",
             "IDs 90-98 and 80-82 are proposals: any unused tag36h11",
             "IDs work; change them in config/powder_doser.yaml.",
             "Rendered from the Digital Twin (the doser isn't in the cell",
             "yet): positions are the config's proposals, not measured."]
    for line in notes:
        y += 22
        cv2.putText(key, line, (16, y), cv2.FONT_HERSHEY_SIMPLEX, 0.48, (40, 40, 40), 1, cv2.LINE_AA)
    out = np.hstack([panel, key])
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    cv2.imwrite(OUT, out, [cv2.IMWRITE_JPEG_QUALITY, 90])
    print("wrote", OUT, out.shape)


def _wrap(text, n):
    words, lines, cur = text.split(), [], ""
    for w in words:
        if len(cur) + len(w) + 1 > n:
            lines.append(cur)
            cur = w
        else:
            cur = f"{cur} {w}".strip()
    return lines + ([cur] if cur else [])


if __name__ == "__main__":
    main()
