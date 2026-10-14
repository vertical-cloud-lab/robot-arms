#!/usr/bin/env python3
"""Where to add two fixed cameras to the PiPER cell (issue #24).

Scores candidate camera poses with the digital twin (piper_twin.py). For a few hundred arm poses
spread over the table it asks, for every camera: are the fingertips in frame, are they hidden
behind the arm, and how big is a pixel there? Then, for the taped camera plus each pair of
candidates: how well do the cameras that see the fingertips pin them down in 3D? That is 1 px of
image noise pushed through every camera that sees them (the triangulation error); one camera on
its own has no depth at all. Finally it renders what each camera would see.

    python scripts/piper_camera_placement.py --out docs/issue-24/camera-placement

Runs on the runner or a laptop (numpy, opencv, trimesh, scipy) and never talks to the arm.

Frame: the arm's base frame, mm (x forward at J1 = 0, along the wall; y toward the wall; z up
from the arm's plate). The table and wall come from the spot D model in PR #9 (table 1290 x 1360
mm, J1 in the middle of its length, 606 mm from the wall and 754 mm from the front edge); the
taped camera is docs/issue-24/camera_2026-10-13.json. The shelf is not modelled as an occluder:
today's photo shows it taller than #9's 75 mm design, and one camera at table height can't place it.
"""
import argparse
import itertools
import json
import math
import os

import cv2
import numpy as np
from scipy.optimize import least_squares

import piper_twin as pt

HERE = os.path.dirname(os.path.abspath(__file__))
LIMITS = [(-150, 150), (0, 180), (-170, 0), (-100, 100), (-70, 70), (-120, 120)]
TABLE = dict(x0=-645, x1=645, y0=-754, y1=606)  # spot D, arm frame, mm; the wall is at y1
J2 = np.array([0.0, 0.0, 123.0])
REACH_MM = 285.03 + math.hypot(250.75, 21.98) + 91 + pt.TIP_MM  # J2 to fingertips, arm straight

# Camera Module 3 Wide in rpicam's full-sensor 2304x1296 video mode (f = 2.75 mm, 2.8 um binned).
W, H, F = 2304, 1296, 982.0
PX_SIGMA = 1.0  # image noise for the triangulation error, px at 2304x1296

REST = [3.99, -1.96, 2.15, 1.38, 23.34, 64.29]  # feedback, 2026-10-09
READY = [3.99, 15.0, -15.0, 1.38, 25.0, 64.29]  # piper_camera_check.py's READY from that rest

# Candidates: eye and look-at point (mm), and where the camera would physically go.
CANDIDATES = {
    "overhead": dict(eye=(0, -75, 1200), target=(0, -75, 0), up=(0, 1, 0),
                     where="1.2 m above the table's centre, looking straight down"),
    "front-end": dict(eye=(800, 100, 420), target=(0, 150, 150),
                      where="past the table's right-hand end (+x, the way the arm faces), "
                            "0.42 m up, looking back along the wall"),
    "door-end": dict(eye=(-800, 100, 420), target=(0, 150, 150),
                     where="past the left-hand (door) end, behind the arm, 0.42 m up"),
    "raised-tape": dict(eye=(182, -755, 450), target=(0, 150, 150),
                        where="where the taped camera is, but 0.45 m up and tilted down"),
    "room-corner": dict(eye=(650, -750, 650), target=(0, 100, 150),
                        where="front right corner of the table, 0.65 m up"),
    "wall-high": dict(eye=(0, 590, 750), target=(0, -50, 100),
                      where="on the wall behind the shelf, 0.75 m up, looking at the room"),
    "room-high": dict(eye=(0, -650, 1000), target=(0, 100, 100),
                      where="above the table's front edge, 1 m up, looking down at 45-50 deg"),
    "end-back-corner": dict(eye=(720, 620, 450), target=(0, 50, 150),
                            where="right-hand end, wall-side corner, 0.45 m up"),
    "end-front-corner": dict(eye=(720, -700, 450), target=(0, 100, 150),
                             where="right-hand end, room-side corner, 0.45 m up"),
    "front-end-high": dict(eye=(850, 0, 750), target=(0, 100, 100),
                           where="past the right-hand end, 0.75 m up, looking down at 35 deg"),
}


def look_cam(eye, target, up=(0, 0, 1), w=W, h=H, f=F):
    eye, target, up = (np.asarray(v, float) for v in (eye, target, up))
    z = target - eye
    z /= np.linalg.norm(z)
    x = np.cross(z, up)
    x /= np.linalg.norm(x)
    y = np.cross(z, x)
    R = np.stack([x, y, z])
    return pt.Camera(w, h, [[f, 0, w / 2], [0, f, h / 2], [0, 0, 1]], [0] * 5,
                     cv2.Rodrigues(R)[0].ravel(), -R @ eye)


def taped_camera():
    return pt.Camera.load(os.path.join(HERE, "..", "docs", "issue-24",
                                       "camera_2026-10-13.json")).scaled(W, H)


def describe(cam):
    """Position, pointing (azimuth from +x toward +y, elevation) and roll-free summary."""
    C, d = cam.center(), cam.R().T @ [0, 0, 1]
    return dict(position_mm=C.round(0).tolist(),
                look_dir=d.round(3).tolist(),
                azimuth_deg=round(math.degrees(math.atan2(d[1], d[0])), 1),
                elevation_deg=round(math.degrees(math.asin(d[2])), 1),
                distance_from_J2_mm=round(float(np.linalg.norm(C - J2))),
                outside_reach=bool(np.linalg.norm(C - J2) > REACH_MM + 30))


# ---------------------------------------------------------------- arm poses
def tip_and_axis(q):
    T = pt.link_poses(q)
    return (T["link6"] @ [0, 0, pt.TIP_MM, 1])[:3], T["link6"][:3, 2]


def ik(tip, axis, q0=READY):
    """Joint angles (deg) that put the fingertips at tip with the tool along axis."""
    axis = np.asarray(axis, float) / np.linalg.norm(axis)
    lo, hi = np.array(LIMITS, float).T

    def res(q):
        p, a = tip_and_axis(q)
        return np.concatenate([(p - tip) / 1.0, (a - axis) * 200.0])
    best = None
    for j1 in (math.degrees(math.atan2(tip[1], tip[0])),):
        for q_start in (q0, [j1, 60, -60, 0, 40, 0], [j1, 90, -90, 0, 60, 0]):
            q_start = np.clip(np.array(q_start, float), lo + 1e-3, hi - 1e-3)
            q_start[0] = np.clip(j1, lo[0] + 1, hi[0] - 1)
            r = least_squares(res, q_start, bounds=(lo, hi))
            if best is None or r.cost < best.cost:
                best = r
    p, a = tip_and_axis(best.x)
    return best.x.round(2).tolist(), float(np.linalg.norm(p - tip)), \
        float(math.degrees(math.acos(np.clip(a @ axis, -1, 1))))


def sample_poses(n, seed=24):
    """Joint angles spread over the working range, fingertips over the table."""
    rng = np.random.default_rng(seed)
    out = []
    while len(out) < n:
        q = [rng.uniform(-120, 120), rng.uniform(0, 110), rng.uniform(-150, -5),
             rng.uniform(-90, 90), rng.uniform(-70, 70), rng.uniform(-120, 120)]
        kp = pt.keypoints_3d(q)
        tip = kp["tip"]
        if min(v[2] for k, v in kp.items() if k != "base") < 20:
            continue
        if not (15 <= tip[2] <= 500 and -600 <= tip[0] <= 620 and -700 <= tip[1] <= 540):
            continue
        out.append(q)
    return out


# ---------------------------------------------------------------- visibility and triangulation
def world_triangles(meshes, q):
    T = pt.link_poses(q)
    tris = []
    for name, (v, f) in meshes.items():
        vw = v @ T[name][:3, :3].T + T[name][:3, 3]
        tris.append(vw[f])
    return np.concatenate(tris)


def hidden(C, P, tris, tol=20.0):
    """True if the arm's surface crosses the line of sight to P more than tol mm before P
    (the fingertip point sits between the finger pads, so the last tol mm don't count)."""
    d = P - C
    L = np.linalg.norm(d)
    d /= L
    v0 = tris[:, 0]
    e1, e2 = tris[:, 1] - v0, tris[:, 2] - v0
    h = np.cross(d, e2)
    a = (e1 * h).sum(1)
    ok = np.abs(a) > 1e-9
    f = np.where(ok, 1.0 / np.where(ok, a, 1.0), 0.0)
    s = C - v0
    u = f * (s * h).sum(1)
    qv = np.cross(s, e1)
    v = f * (qv @ d)
    t = f * (qv * e2).sum(1)
    return bool((ok & (u >= 0) & (v >= 0) & (u + v <= 1) & (t > 1) & (t < L - tol)).any())


def in_frame(cam, P, margin=0.03):
    if cam.to_cam(P)[0, 2] <= 50:
        return False
    u, v = cam.project([P])[0]
    mx, my = margin * cam.width, margin * cam.height
    return mx <= u <= cam.width - mx and my <= v <= cam.height - my


def jac(cam, P, h=0.5):
    J = np.zeros((2, 3))
    for k in range(3):
        e = np.zeros(3)
        e[k] = h
        J[:, k] = (cam.project([P + e])[0] - cam.project([P - e])[0]) / (2 * h)
    return J


def tri_error(cams, P):
    """RMS 3D error (mm) of the point P triangulated from cams with PX_SIGMA px of noise."""
    if len(cams) < 2:
        return math.inf
    A = sum(jac(c, P).T @ jac(c, P) for c in cams)
    return float(PX_SIGMA * math.sqrt(np.trace(np.linalg.inv(A))))


def evaluate(cams, poses, meshes):
    """Per pose and camera: (in frame, not hidden, mm per px at the fingertips)."""
    seen = np.zeros((len(poses), len(cams)), bool)
    mmpx = np.full((len(poses), len(cams)), np.nan)
    tips = []
    for i, q in enumerate(poses):
        tip = pt.keypoints_3d(q)["tip"]
        tips.append(tip)
        tris = world_triangles(meshes, q)
        for j, cam in enumerate(cams):
            if in_frame(cam, tip) and not hidden(cam.center(), tip, tris):
                seen[i, j] = True
                mmpx[i, j] = cam.mm_per_px(tip)
    return seen, mmpx, np.array(tips)


# ---------------------------------------------------------------- drawing
def clip_near(Pc, near=30.0):
    """Sutherland-Hodgman clip of a polygon (camera frame) to z > near."""
    out = []
    for a, b in zip(Pc, np.roll(Pc, -1, 0)):
        ina, inb = a[2] > near, b[2] > near
        if ina:
            out.append(a)
        if ina != inb:
            t = (near - a[2]) / (b[2] - a[2])
            out.append(a + t * (b - a))
    return np.array(out)


def fill_poly(img, cam, pts, color, alpha=1.0, edge=None):
    Pc = clip_near(cam.to_cam(pts))
    if len(Pc) < 3:
        return
    R = cam.R()
    Pw = (Pc - cam.tvec) @ R  # back to world for projection with distortion
    uv = np.round(cam.project(Pw) * 4).astype(np.int32)
    layer = img.copy()
    cv2.fillPoly(layer, [uv], color, cv2.LINE_AA, shift=2)
    cv2.addWeighted(layer, alpha, img, 1 - alpha, 0, img)
    if edge is not None:
        cv2.polylines(img, [uv], True, edge, 1, cv2.LINE_AA, shift=2)


def draw_line3d(img, cam, a, b, color, thick=1, n=40):
    P = np.linspace(a, b, n)
    keep = cam.to_cam(P)[:, 2] > 30
    uv = cam.project(P)
    for k in range(n - 1):
        if keep[k] and keep[k + 1]:
            cv2.line(img, tuple(np.round(uv[k]).astype(int)), tuple(np.round(uv[k + 1]).astype(int)),
                     color, thick, cv2.LINE_AA)


def scene(cam, w=None, h=None):
    """Table, grid and wall as the camera would see them, before the arm is drawn."""
    img = np.full((cam.height, cam.width, 3), 236, np.uint8)
    x0, x1, y0, y1 = TABLE["x0"], TABLE["x1"], TABLE["y0"], TABLE["y1"]
    fill_poly(img, cam, [[-3000, y1, 0], [3000, y1, 0], [3000, y1, 2200], [-3000, y1, 2200]],
              (214, 214, 214))
    fill_poly(img, cam, [[x0, y0, 0], [x1, y0, 0], [x1, y1, 0], [x0, y1, 0]], (176, 206, 226),
              edge=(90, 120, 150))
    for x in range(-600, 601, 100):
        draw_line3d(img, cam, [x, y0, 0], [x, y1, 0], (150, 180, 200))
    for y in range(-700, 601, 100):
        draw_line3d(img, cam, [x0, y, 0], [x1, y, 0], (150, 180, 200))
    # the reach circle on the table: everything inside it can be touched by the fingertips
    r = math.sqrt(REACH_MM ** 2 - J2[2] ** 2)
    circ = [[r * math.cos(t), r * math.sin(t), 1] for t in np.linspace(0, 2 * math.pi, 120)]
    for a, b in zip(circ[:-1], circ[1:]):
        draw_line3d(img, cam, a, b, (60, 60, 200), 1, n=3)
    return img


def frustum(img, view, cam, color, label, size=140):
    C = cam.center()
    R = cam.R()
    hw, hh = cam.width / 2 / cam.K[0, 0], cam.height / 2 / cam.K[1, 1]
    corners = [C + R.T @ np.array([sx * hw, sy * hh, 1.0]) * size
               for sx, sy in ((-1, -1), (1, -1), (1, 1), (-1, 1))]
    uv = np.round(view.project(np.array([C] + corners))).astype(int)
    for k in range(1, 5):
        cv2.line(img, tuple(uv[0]), tuple(uv[k]), color, 2, cv2.LINE_AA)
        cv2.line(img, tuple(uv[k]), tuple(uv[1 + k % 4]), color, 2, cv2.LINE_AA)
    pt.put_text(img, label, tuple(uv[0] + np.array([10, -10])), color, box=(250, 250, 250))


COLORS = {"taped": (40, 40, 210), "A": (30, 150, 30), "B": (200, 110, 20)}


def render_views(cams, labels, poses, pose_names, meshes, photo=None, panel=(640, 360)):
    rows = []
    for cam, label in zip(cams, labels):
        small = cam.scaled(*panel)
        if photo is not None and label.startswith("taped"):
            base = cv2.resize(photo, panel, interpolation=cv2.INTER_AREA)
            base = pt.remove_arm(base, small, meshes, REST)
            base = cv2.addWeighted(base, 0.6, np.full_like(base, 255), 0.4, 0)
        else:
            base = scene(small)
        row = []
        for q, name in zip(poses, pose_names):
            img = pt.render(small, meshes, q, 0.0, base.copy(), alpha=0.95)
            pt.draw_skeleton(img, small, q, thick=1)
            pt.put_text(img, f"{label}: {name}", (8, 22), scale=0.5)
            row.append(img)
        rows.append(np.hstack(row))
    return np.vstack(rows)


def min_jerk(t):
    return 10 * t ** 3 - 15 * t ** 4 + 6 * t ** 5


def tour(named, order, move_s=2.0, hold_s=0.4, fps=10):
    """(label, joints) frames through the named poses, all joints together, minimum jerk."""
    frames = []
    for a, b in zip(order[:-1], order[1:]):
        qa, qb = np.array(named[a], float), np.array(named[b], float)
        n = int(move_s * fps)
        frames += [(f"{a} -> {b}", qa + (qb - qa) * min_jerk(k / n)) for k in range(n)]
        frames += [(b, qb)] * int(hold_s * fps)
    return frames


def animate(path, cams, labels, named, meshes, photo, fps=10, panel=(640, 360)):
    """The three camera views and an overview, side by side, as the twin tours the table."""
    import imageio.v2 as imageio
    order = ["rest", "READY", "toward the shelf", "READY", "table, in front",
             "table, room side", "READY", "rest"]
    frames = tour(named, order, fps=fps)
    low = min(min(v[2] for k, v in pt.keypoints_3d(q).items() if k != "base") for _, q in frames)
    print(f"tour: {len(frames)} frames, lowest joint or fingertip {low:.0f} mm above the plate")
    smalls = [c.scaled(*panel) for c in cams]
    bases = []
    for cam, label in zip(smalls, labels):
        if photo is not None and label.startswith("taped"):
            b = cv2.resize(photo, panel, interpolation=cv2.INTER_AREA)
            b = pt.remove_arm(b, cam, meshes, REST)
            bases.append(cv2.addWeighted(b, 0.6, np.full_like(b, 255), 0.4, 0))
        else:
            bases.append(scene(cam))
    view = pt.virtual_camera(*panel, 56, (1500, -2700, 1700), (0, 60, 330))
    vbase = scene(view)
    writer = imageio.get_writer(path, fps=fps, codec="libx264", quality=8, macro_block_size=8)
    for label, q in frames:
        tiles = []
        for cam, base, name in zip(smalls, bases, labels):
            img = pt.render(cam, meshes, q, 0.0, base.copy(), alpha=0.95)
            pt.draw_skeleton(img, cam, q, thick=1)
            pt.put_text(img, name, (8, 22), scale=0.5)
            tiles.append(img)
        ov = pt.render(view, meshes, q, 0.0, vbase.copy())
        for cam, name, col in zip(cams, labels, COLORS.values()):
            frustum(ov, view, cam, col, name.split(" (")[0])
        pt.put_text(ov, "where the cameras are", (8, 22), (40, 40, 40), scale=0.5,
                    box=(236, 236, 236))
        frame = np.vstack([np.hstack(tiles[:2]), np.hstack([tiles[2], ov])])
        bar = np.full((40, frame.shape[1], 3), 30, np.uint8)
        pt.put_text(bar, f"DIGITAL TWIN (simulated, not a recording)   {label}", (10, 27),
                    scale=0.6, box=None)
        writer.append_data(np.vstack([bar, frame])[:, :, ::-1])
    writer.close()
    pt.mp4_to_gif(path, path.replace(".mp4", ".gif"), speed=1.5, width=960)


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--out", default="docs/issue-24/camera-placement")
    ap.add_argument("--poses", type=int, default=300)
    ap.add_argument("--photo", help="today's photo from the taped camera, as the backdrop of its row")
    ap.add_argument("--pick", default="overhead,front-end", help="the two cameras to render")
    ap.add_argument("--animate", action="store_true", help="also write views.mp4 and views.gif")
    ap.add_argument("--animate-only", action="store_true", help="skip the scoring and stills")
    args = ap.parse_args()
    if args.animate_only:
        meshes = pt.load_meshes()
        a, b = args.pick.split(",")
        named = json.load(open(os.path.join(args.out, "placement.json")))["named_poses"]
        named = {k: v["joints_deg"] for k, v in named.items()}
        cams = [taped_camera()] + [look_cam(CANDIDATES[k]["eye"], CANDIDATES[k]["target"],
                                            CANDIDATES[k].get("up", (0, 0, 1))) for k in (a, b)]
        animate(os.path.join(args.out, "views.mp4"), cams,
                ["taped (today's photo)", f"A: {a}", f"B: {b}"], named, meshes,
                cv2.imread(args.photo) if args.photo else None)
        return
    os.makedirs(args.out, exist_ok=True)
    meshes = pt.load_meshes()

    taped = taped_camera()
    cands = {k: look_cam(v["eye"], v["target"], v.get("up", (0, 0, 1)))
             for k, v in CANDIDATES.items()}
    names = ["taped"] + list(cands)
    cams = [taped] + list(cands.values())

    poses = sample_poses(args.poses)
    seen, mmpx, tips = evaluate(cams, poses, meshes)

    per_cam = {}
    for j, n in enumerate(names):
        per_cam[n] = dict(**describe(cams[j]),
                          fingertips_seen_pct=round(100 * seen[:, j].mean(), 1),
                          median_mm_per_px=round(float(np.nanmedian(mmpx[:, j])), 2),
                          where=CANDIDATES.get(n, {}).get("where", "taped to the table (today)"))

    def score(idx):
        errs, n2 = [], 0
        for i in range(len(poses)):
            use = [cams[j] for j in idx if seen[i, j]]
            n2 += len(use) >= 2
            errs.append(tri_error(use, tips[i]))
        errs = np.array(errs)
        fin = errs[np.isfinite(errs)]
        return dict(cameras=[names[j] for j in idx],
                    seen_by_2plus_pct=round(100 * n2 / len(poses), 1),
                    seen_by_any_pct=round(100 * seen[:, idx].any(1).mean(), 1),
                    median_err_mm=round(float(np.median(fin)), 2) if len(fin) else None,
                    p90_err_mm=(round(float(np.percentile(errs, 90)), 2)
                                if np.isfinite(np.percentile(errs, 90)) else None),
                    within_2mm_pct=round(100 * float((errs <= 2.0).mean()), 1))

    pairs = [score([0, names.index(a), names.index(b)])
             for a, b in itertools.combinations(list(cands), 2)]
    pairs.sort(key=lambda r: (-r["within_2mm_pct"], -r["seen_by_2plus_pct"]))
    singles = [score([0, names.index(a)]) for a in cands]
    singles.sort(key=lambda r: (-r["within_2mm_pct"], -r["seen_by_2plus_pct"]))
    today = score([0])

    # named poses for the renders
    shelf_q, shelf_err, shelf_ang = ik(np.array([60.0, 300.0, 300.0]), (0, 0.707, -0.707))
    table_q, table_err, table_ang = ik(np.array([380.0, -60.0, 30.0]), (0, 0, -1))
    room_q, room_err, room_ang = ik(np.array([250.0, -380.0, 40.0]), (0, -0.5, -0.866))
    named = {"rest": REST, "READY": READY, "toward the shelf": shelf_q,
             "table, in front": table_q, "table, room side": room_q}
    out = dict(frame="arm base frame, mm; x along the wall (the way the arm faces), y toward the "
                     "wall, z up from the arm's plate",
               camera_model=f"Camera Module 3 Wide, {W}x{H}, f = {F} px, no distortion",
               pixel_noise_px=PX_SIGMA, n_poses=len(poses), reach_mm=round(REACH_MM),
               per_camera=per_cam, taped_only=today, taped_plus_one=singles,
               taped_plus_two=pairs,
               named_poses={k: dict(joints_deg=v) for k, v in named.items()},
               ik_residual_mm={"toward the shelf": round(shelf_err, 2),
                               "table, in front": round(table_err, 2),
                               "table, room side": round(room_err, 2)},
               ik_residual_deg={"toward the shelf": round(shelf_ang, 2),
                                "table, in front": round(table_ang, 2),
                                "table, room side": round(room_ang, 2)})
    json.dump(out, open(os.path.join(args.out, "placement.json"), "w"), indent=1)

    # what each camera would see
    a, b = args.pick.split(",")
    photo = cv2.imread(args.photo) if args.photo else None
    show = ["rest", "toward the shelf", "table, in front", "table, room side"]
    grid = render_views([taped, cands[a], cands[b]],
                        ["taped (today's photo)", f"A: {a}", f"B: {b}"],
                        [named[k] for k in show], show, meshes, photo)
    cv2.imwrite(os.path.join(args.out, "views.jpg"), grid, [cv2.IMWRITE_JPEG_QUALITY, 88])

    # overview: where the cameras are
    view = pt.virtual_camera(1280, 800, 56, (1500, -2700, 1700), (0, 60, 330))
    img = scene(view)
    img = pt.render(view, meshes, named["toward the shelf"], 0.0, img)
    for cam, label, col in ((taped, "taped (today)", COLORS["taped"]),
                            (cands[a], f"A: {a}", COLORS["A"]),
                            (cands[b], f"B: {b}", COLORS["B"])):
        frustum(img, view, cam, col, label)
        C = cam.center()
        draw_line3d(img, view, C, [C[0], C[1], 0], col, 1)
    pt.put_text(img, "spot D table (1290 x 1360 mm), wall behind; red circle: fingertip reach "
                     "on the table", (10, 24), (40, 40, 40), box=(236, 236, 236))
    cv2.imwrite(os.path.join(args.out, "overview.jpg"), img, [cv2.IMWRITE_JPEG_QUALITY, 90])

    for name in ("taped",) + (a, b):
        cam = taped if name == "taped" else cands[name]
        cam.scaled(4608, 2592).save(os.path.join(args.out, f"camera_{name}.json"),
                                    note=per_cam[name]["where"])
    if args.animate:
        animate(os.path.join(args.out, "views.mp4"), [taped, cands[a], cands[b]],
                ["taped (today's photo)", f"A: {a}", f"B: {b}"], named, meshes, photo)
    print(json.dumps(dict(taped_only=today, best_pairs=pairs[:6], best_single=singles[:3]),
                     indent=1))
    print(json.dumps({k: {kk: v[kk] for kk in ("position_mm", "azimuth_deg", "elevation_deg",
                                               "distance_from_J2_mm", "fingertips_seen_pct",
                                               "median_mm_per_px")}
                      for k, v in per_cam.items()}, indent=1))


if __name__ == "__main__":
    main()
