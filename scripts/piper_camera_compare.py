#!/usr/bin/env python3
"""Compare a filmed piper_camera_check.py run with its digital twin (issue #24).

Runs on the runner, after copying the run's files off the Pi:

    python piper_camera_compare.py --video run.mjpeg --trace run.csv --marks run_marks.json \
        --camera docs/issue-24/camera_2026-10-13.json --out docs/issue-24/run1

What it measures. Three patches on the arm are followed through every still hold of the run:
the elbow's motor cap (J3), the wrist's motor cap (J5) and the gripper. Each patch is cut from
the first READY hold, where it is centred on the twin's prediction of that point, and found in
every other hold by normalised cross-correlation. For each hold that gives
- observed: how far the patch moved in the image from READY, and
- predicted: how far the same point should move, from the joint feedback, the forward
  kinematics and the camera model.
Their difference, in pixels and in mm at the arm, is the error the issue asks about. It does
not depend on how well the camera was placed at READY, only on how well the model predicts
motion.

--refit refits the camera pose to all holds, leaving one pose out at a time. It shows how
consistent the model is across poses, but it cannot find the absolute camera pose: each patch
is anchored where the current model puts it at READY, so a camera error moves the anchors with
it. In the synthetic self-test (docs/issue-24/selftest) the refit moved the camera 7.4 mm, but
it ended 9.6 mm from the true pose, about as far as it started (7.6 mm). Checking the absolute
placement needs points found without the model (a marker, or the arm's outline).

Time. The video's frame times (rpicam's --save-pts) start at its first frame; the trace is in
Unix time. The offset between them starts from the recorded video start and is refined by
lining up the image motion with the joint speed.

Outputs in --out: errors.csv, summary.json, errors.png, side_by_side.mp4 and a sped-up GIF.
"""
import argparse
import csv
import glob
import json
import os
import subprocess
import sys
import tempfile

import cv2
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import piper_twin as tw  # noqa: E402

# (name, link, side offset along the link's z axis to the cap facing the camera, mm)
ANCHORS = [("elbow cap", "link3", 40.0), ("wrist cap", "link5", 32.0), ("gripper", "link6", None)]
GRIPPER_POINT = (0.0, 0.0, 95.0)  # on the tool axis, between the flange and the fingertips


# ---------------------------------------------------------------- inputs
def read_pts(path):
    """rpicam-vid --save-pts: '# timecode format v2', then one time per frame in ms."""
    vals = [float(x) for x in open(path).read().split() if x[0].isdigit()]
    return (np.array(vals) - vals[0]) / 1000.0


def extract_frames(mjpeg, out_dir):
    """Every frame of a raw MJPEG stream as a JPEG, without re-encoding."""
    import imageio_ffmpeg
    subprocess.run([imageio_ffmpeg.get_ffmpeg_exe(), "-y", "-loglevel", "error", "-f", "mjpeg",
                    "-i", mjpeg, "-c:v", "copy", "-f", "image2",
                    os.path.join(out_dir, "%06d.jpg")], check=True)
    return sorted(glob.glob(os.path.join(out_dir, "*.jpg")))


def read_trace(path):
    rows = list(csv.DictReader(open(path)))
    t = np.array([float(r["unix_t"]) for r in rows])
    q = np.array([[float(r[f"j{i}"]) for i in range(1, 7)] for r in rows])
    return t, q


def joints_at(t_trace, q_trace, t):
    return np.array([np.interp(t, t_trace, q_trace[:, j]) for j in range(6)])


# ---------------------------------------------------------------- geometry
def anchor_points(q, cam):
    """Base-frame positions of the three anchors at joints q; caps on the side facing cam."""
    T = tw.link_poses(q)
    out = []
    for name, link, side in ANCHORS:
        if side is None:
            out.append((T[link] @ np.array([*GRIPPER_POINT, 1.0]))[:3])
            continue
        cands = [(T[link] @ np.array([0, 0, s, 1.0]))[:3] for s in (side, -side)]
        out.append(min(cands, key=lambda p: cam.to_cam(p)[0, 2]))
    return np.array(out)


def anchor_link_points(q, cam):
    """The same anchors in their links' frames (fixed once chosen at READY)."""
    T = tw.link_poses(q)
    P = anchor_points(q, cam)
    return [np.linalg.inv(T[link]) @ np.array([*p, 1.0]) for (n, link, s), p in zip(ANCHORS, P)]


def project_anchors(q, cam, local):
    T = tw.link_poses(q)
    P = np.array([(T[link] @ a)[:3] for (n, link, s), a in zip(ANCHORS, local)])
    return cam.project(P), P


# ---------------------------------------------------------------- image measurements
def median_frame(paths):
    imgs = [cv2.imread(p) for p in paths]
    return np.median(np.stack(imgs), axis=0).astype(np.uint8)


def track(ref, img, center, guess, half=32, search=40):
    """Where the patch of ref centred on the pixel nearest center is in img, searching within
    search px of guess (the twin's prediction). Returns the patch centre and the NCC score."""
    cx, cy = int(round(center[0])), int(round(center[1]))
    gx, gy = int(round(guess[0])), int(round(guess[1]))
    g_ref = cv2.cvtColor(ref, cv2.COLOR_BGR2GRAY)
    g_img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    tpl = g_ref[cy - half:cy + half + 1, cx - half:cx + half + 1]
    x0, y0 = max(0, gx - half - search), max(0, gy - half - search)
    win = g_img[y0:gy + half + search + 1, x0:gx + half + search + 1]
    if tpl.shape != (2 * half + 1, 2 * half + 1) or win.shape[0] <= tpl.shape[0] \
            or win.shape[1] <= tpl.shape[1]:
        return None, 0.0
    r = cv2.matchTemplate(win, tpl, cv2.TM_CCOEFF_NORMED)
    _, score, _, (mx, my) = cv2.minMaxLoc(r)

    def sub(a, b, c):  # sub-pixel peak: parabola through the neighbours
        d = a - 2 * b + c
        return 0.0 if abs(d) < 1e-9 else 0.5 * (a - c) / d
    dx = sub(r[my, mx - 1], r[my, mx], r[my, mx + 1]) if 0 < mx < r.shape[1] - 1 else 0.0
    dy = sub(r[my - 1, mx], r[my, mx], r[my + 1, mx]) if 0 < my < r.shape[0] - 1 else 0.0
    return np.array([x0 + mx + dx + half, y0 + my + dy + half]), float(score)


def motion_energy(paths, box, step=1):
    """Mean absolute difference between consecutive frames inside box (x0, y0, x1, y1)."""
    x0, y0, x1, y1 = box
    prev, out = None, []
    for p in paths[::step]:
        g = cv2.cvtColor(cv2.imread(p), cv2.COLOR_BGR2GRAY)[y0:y1, x0:x1].astype(np.float32)
        out.append(0.0 if prev is None else float(np.abs(g - prev).mean()))
        prev = g
    return np.array(out)


def sync_offset(t_frames, energy, t_trace, q_trace, guess, span=3.0):
    """Unix time of the first frame: the guess, refined by matching image motion to joint speed."""
    speed = np.r_[0, np.abs(np.diff(q_trace, axis=0)).sum(1) / np.maximum(np.diff(t_trace), 1e-3)]
    e = (energy - energy.mean()) / (energy.std() + 1e-9)
    best = (-np.inf, guess)
    for off in np.arange(guess - span, guess + span, 0.01):
        s = np.interp(t_frames + off, t_trace, speed)
        s = (s - s.mean()) / (s.std() + 1e-9)
        c = float((e * s).mean())
        best = max(best, (c, off))
    return best[1], best[0]


# ---------------------------------------------------------------- camera refit
def refit_camera(cam, obs, local_pts, fit_focal=False):
    """Least-squares camera pose (and focal length) from observed anchor pixels.
    obs: list of (q, k, uv) with k the anchor index."""
    from scipy.optimize import least_squares

    def unpack(x):
        K = cam.K.copy()
        if fit_focal:
            K[0, 0] = K[1, 1] = x[6]
        return tw.Camera(cam.width, cam.height, K, cam.dist, x[:3], x[3:6])

    def resid(x):
        c = unpack(x)
        r = []
        for q, k, uv in obs:
            T = tw.link_poses(q)
            p = (T[ANCHORS[k][1]] @ local_pts[k])[:3]
            r.extend(c.project([p])[0] - uv)
        return np.array(r)

    x0 = np.r_[cam.rvec, cam.tvec, [cam.K[0, 0]] if fit_focal else []]
    sol = least_squares(resid, x0, x_scale="jac")
    return unpack(sol.x), resid(sol.x).reshape(-1, 2)


# ---------------------------------------------------------------- video
def side_by_side(frames, t_frames, t_trace, q_trace, cam, meshes, out_mp4, crop, panel, labels,
                 backdrop_q, fps, real_label="REAL camera"):
    import imageio.v2 as imageio
    x0, y0, w, h = crop
    pw, ph = panel
    ccam = cam.cropped(x0, y0, w, h, pw, ph)
    first = cv2.imread(frames[0])
    bd = cv2.resize(first[y0:y0 + h, x0:x0 + w], (pw, ph), interpolation=cv2.INTER_AREA)
    bd = tw.remove_arm(bd, ccam, meshes, backdrop_q)
    bd = cv2.addWeighted(bd, 0.55, np.full_like(bd, 255), 0.45, 0)
    writer = imageio.get_writer(out_mp4, fps=fps, codec="libx264", quality=8, macro_block_size=8)
    for path, t in zip(frames, t_frames):
        q = joints_at(t_trace, q_trace, t)
        real = cv2.resize(cv2.imread(path)[y0:y0 + h, x0:x0 + w], (pw, ph),
                          interpolation=cv2.INTER_AREA)
        tw.draw_skeleton(real, ccam, q, thick=1)
        twin = tw.render(ccam, meshes, q, 0.0, bd.copy(), alpha=0.92)
        tw.draw_skeleton(twin, ccam, q, thick=1)
        tw.put_text(real, f"{real_label} (yellow: joint feedback through the camera model)",
                    (10, 24))
        tw.put_text(twin, "DIGITAL TWIN driven by the same joint feedback", (10, 24))
        frame = np.hstack([real, twin])
        bar = np.full((48, frame.shape[1], 3), 30, np.uint8)
        lab = labels(t)
        tw.put_text(bar, f"t = {t - t_trace[0]:5.1f} s   {lab:10s}  joints "
                    + " ".join(f"{v:6.1f}" for v in q), (10, 31), scale=0.62, box=None)
        writer.append_data(np.vstack([bar, frame])[:, :, ::-1])
    writer.close()


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--video", required=True, help=".mjpeg from piper_camera_check.py --video")
    ap.add_argument("--pts", help="frame times (default: VIDEO.pts)")
    ap.add_argument("--trace", required=True)
    ap.add_argument("--marks", required=True)
    ap.add_argument("--camera", required=True, help="camera JSON for the full-sensor still")
    ap.add_argument("--out", required=True)
    ap.add_argument("--refit", action="store_true", help="refit the camera to all holds")
    ap.add_argument("--crop", type=lambda v: [int(x) for x in v.split(",")],
                    default=[700, 1080, 2400, 1350], help="x0,y0,w,h in full-sensor pixels")
    ap.add_argument("--panel", type=lambda v: [int(x) for x in v.split("x")], default=[768, 432])
    ap.add_argument("--search-px", type=int, default=40,
                    help="look for each patch this far around the twin's prediction")
    ap.add_argument("--min-score", type=float, default=0.8,
                    help="ignore matches with a lower normalised cross-correlation")
    ap.add_argument("--gif-speed", type=float, default=3.0)
    ap.add_argument("--real-label", default="REAL camera")
    args = ap.parse_args()
    os.makedirs(args.out, exist_ok=True)

    tmp = tempfile.mkdtemp(prefix="frames_")
    frames = extract_frames(args.video, tmp)
    t_pts = read_pts(args.pts or args.video + ".pts")[:len(frames)]
    frames = frames[:len(t_pts)]
    first = cv2.imread(frames[0])
    H, W = first.shape[:2]
    cam_full = tw.Camera.load(args.camera)
    cam = cam_full.scaled(W, H)
    t_tr, q_tr = read_trace(args.trace)
    marks = json.load(open(args.marks))
    poses = marks["poses"]
    meshes = tw.load_meshes()

    # time sync
    s = W / cam_full.width
    x0, y0, w, h = args.crop
    box = [int(x0 * s), int(y0 * s), int((x0 + w) * s), int((y0 + h) * s)]
    energy = motion_energy(frames, box)
    guess = marks.get("video_start_unix", t_tr[0]) + 0.5
    off, corr = sync_offset(t_pts, energy, t_tr, q_tr, guess)
    t_frames = t_pts + off
    print(f"{len(frames)} frames {W}x{H}; first frame at unix {off:.2f} "
          f"(guess {guess:.2f}, motion/speed correlation {corr:.2f})")

    # still frames at every hold
    holds = []
    for m in poses:
        sel = [p for p, t in zip(frames, t_frames) if m["unix_t0"] + 0.25 <= t <= m["unix_t1"] - 0.05]
        if not sel:
            continue
        q = np.median(q_tr[(t_tr >= m["unix_t0"]) & (t_tr <= m["unix_t1"])], axis=0)
        holds.append({"label": m["label"], "q": q, "img": median_frame(sel), "n": len(sel)})
    ready = [hd for hd in holds if hd["label"] == "READY"]
    if not ready:
        sys.exit("no READY hold found in the video")
    ref = ready[0]
    local = anchor_link_points(ref["q"], cam)
    uv_ref, _ = project_anchors(ref["q"], cam, local)

    uv_cut = np.round(uv_ref)  # patches are cut on whole pixels
    rows, obs = [], []
    for hd in holds:
        uv_pred, P = project_anchors(hd["q"], cam, local)
        for k, (name, link, _) in enumerate(ANCHORS):
            found, score = track(ref["img"], hd["img"], uv_cut[k], uv_pred[k],
                                 search=args.search_px)
            if found is None:
                continue
            obs_d = found - uv_cut[k]
            pred_d = uv_pred[k] - uv_ref[k]
            err = obs_d - pred_d
            mm = cam.mm_per_px(P[k])
            rows.append({"pose": hd["label"], "anchor": name, "score": round(score, 3),
                         "obs_dx": obs_d[0], "obs_dy": obs_d[1], "pred_dx": pred_d[0],
                         "pred_dy": pred_d[1], "err_px": float(np.hypot(*err)),
                         "err_mm": float(np.hypot(*err) * mm), "moved_px": float(np.hypot(*obs_d)),
                         "mm_per_px": mm})
            if score > args.min_score:
                obs.append((hd["q"], k, found - uv_cut[k] + uv_ref[k]))
    with open(os.path.join(args.out, "errors.csv"), "w", newline="") as f:
        wr = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        wr.writeheader()
        for r in rows:
            wr.writerow({k: round(v, 3) if isinstance(v, float) else v for k, v in r.items()})
    good = [r for r in rows if r["score"] > args.min_score]
    summary = {"frames": len(frames), "holds": len(holds), "sync_corr": round(corr, 3),
               "tracked": len(good), "of": len(rows),
               "median_err_px": round(float(np.median([r["err_px"] for r in good])), 2),
               "p95_err_px": round(float(np.percentile([r["err_px"] for r in good], 95)), 2),
               "median_err_mm": round(float(np.median([r["err_mm"] for r in good])), 2),
               "p95_err_mm": round(float(np.percentile([r["err_mm"] for r in good], 95)), 2)}
    ready_rows = [r for r in good if r["pose"] == "READY"]
    if ready_rows:
        summary["ready_repeat_px"] = round(float(np.median([r["moved_px"] for r in ready_rows])), 2)

    if args.refit and len(obs) >= 8:
        cam_fit, res = refit_camera(cam, obs, local)
        # leave one pose out
        loo = []
        labels = sorted({id(q) for q, _, _ in obs})
        for qid in labels:
            train = [o for o in obs if id(o[0]) != qid]
            test = [o for o in obs if id(o[0]) == qid]
            c, _ = refit_camera(cam, train, local)
            for q, k, uv in test:
                T = tw.link_poses(q)
                p = (T[ANCHORS[k][1]] @ local[k])[:3]
                loo.append(float(np.hypot(*(c.project([p])[0] - uv))))
        summary["refit_rms_px"] = round(float(np.sqrt((res ** 2).sum(1).mean())), 2)
        summary["refit_loo_median_px"] = round(float(np.median(loo)), 2)
        summary["refit_loo_p95_px"] = round(float(np.percentile(loo, 95)), 2)
        summary["refit_camera_moved_mm"] = round(float(np.linalg.norm(
            cam_fit.center() - cam.center())), 1)
        cam_fit.scaled(cam_full.width, cam_full.height).save(
            os.path.join(args.out, "camera_refit.json"), note="refit to the run's holds")
    json.dump(summary, open(os.path.join(args.out, "summary.json"), "w"), indent=1)
    print(json.dumps(summary, indent=1))
    plot_errors(rows, os.path.join(args.out, "errors.png"), args.min_score)

    def label_at(t):  # the pose being moved to or held
        for m in poses:
            if t <= m["unix_t1"]:
                return ("-> " if t < m["unix_t0"] else "") + m["label"]
        return "parked"

    side_by_side(frames, t_frames, t_tr, q_tr, cam, meshes,
                 os.path.join(args.out, "side_by_side.mp4"),
                 [int(v * s) for v in args.crop], args.panel, label_at,
                 joints_at(t_tr, q_tr, t_frames[0]),
                 fps=1.0 / np.median(np.diff(t_pts)), real_label=args.real_label)
    tw.mp4_to_gif(os.path.join(args.out, "side_by_side.mp4"),
                  os.path.join(args.out, f"side_by_side_{args.gif_speed:g}x.gif"),
                  args.gif_speed, 960)


def plot_errors(rows, path, min_score):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    names = [a[0] for a in ANCHORS]
    poses = []
    for r in rows:
        if r["pose"] not in poses:
            poses.append(r["pose"])
    fig, ax = plt.subplots(figsize=(10, 4), dpi=130)
    width = 0.27
    colors = ["#4C78A8", "#F58518", "#54A24B"]
    for i, n in enumerate(names):
        vals = []
        for p in poses:
            v = [r["err_mm"] for r in rows if r["pose"] == p and r["anchor"] == n and r["score"] > min_score]
            vals.append(np.median(v) if v else np.nan)
        ax.bar(np.arange(len(poses)) + (i - 1) * width, vals, width, label=n, color=colors[i])
    ax.set_xticks(range(len(poses)))
    ax.set_xticklabels(poses, rotation=45, ha="right")
    ax.set_ylabel("observed - predicted motion (mm at the arm)")
    ax.set_title("How far each point's image motion differs from the joint-angle prediction")
    ax.legend(frameon=False)
    ax.spines[["top", "right"]].set_visible(False)
    fig.tight_layout()
    fig.savefig(path)


if __name__ == "__main__":
    main()
