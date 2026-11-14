"""Check the two printed tag pages on the A1 mini as mpzy's camera sees them (robot-arms PR 40, 2026-11-14).

  python analyze.py FRAME.jpg [FRAME.jpg ...] [--out results.json]

Frames are full-resolution rpicam-still images (4608x2592) from mpzy cam0. Per 25 mm tag: frame-to-frame
position and normal scatter; spacing between neighbouring tags against the printed layout (25 mm page:
landscape, 7 columns, 35.25 mm pitch across, 40.25 mm down); detections after downscaling to smaller frame
sizes (1280x720 is the livestream); and attempts to decode the 10 mm page (IDs 60-107) from an upscaled crop.
Intrinsics are the nominal Module 3 Wide ones (f = 1964 px, no distortion), not a calibration.
"""
import argparse, sys, json
import numpy as np, cv2
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[4] / "scripts"))
from apriltag_tools import make_detector

F_FULL = 1964.0  # nominal Module 3 Wide focal length at 4608 px (uncalibrated)
ap = argparse.ArgumentParser()
ap.add_argument("frames", nargs="+")
ap.add_argument("--out", default="results.json")
args = ap.parse_args()
imgs = args.frames
det = make_detector()
def run(gray, f, size_m=0.025):
    h, w = gray.shape
    return det.detect(gray, estimate_tag_pose=True, camera_params=[f, f, w/2, h/2], tag_size=size_m)

poses = {}
for p in imgs:
    g = cv2.cvtColor(cv2.imread(p), cv2.COLOR_BGR2GRAY)
    for d in run(g, F_FULL):
        poses.setdefault(d.tag_id, []).append((d.pose_t.ravel()*1000, d.pose_R[:, 2], d.corners))
out = {"frames": len(imgs), "tags": {}}
print("frames", len(imgs))
for tid in sorted(poses):
    T = np.array([x[0] for x in poses[tid]]); N = np.array([x[1] for x in poses[tid]])
    n0 = N.mean(0); n0 /= np.linalg.norm(n0)
    ang = np.degrees(np.arccos(np.clip(np.abs(N @ n0), -1, 1)))
    t0 = T.mean(0); los = t0/np.linalg.norm(t0)
    depth = T @ los
    lat = T - np.outer(depth, los)
    sides = [np.linalg.norm(x[2][i]-x[2][(i+1)%4]) for x in poses[tid] for i in range(4)]
    tilt = np.degrees(np.arccos(abs(n0 @ los)))
    r = dict(n=len(T), dist_mm=float(np.linalg.norm(t0)), tilt_deg=float(tilt),
             side_px=[float(min(sides)), float(max(sides))],
             depth_sd_mm=float(depth.std()), lateral_sd_mm=float(np.linalg.norm(lat - lat.mean(0), axis=1).std() if len(T)>1 else 0),
             lateral_rms_mm=float(np.sqrt((np.linalg.norm(lat - lat.mean(0), axis=1)**2).mean())),
             normal_sd_deg=float(np.sqrt((ang**2).mean())))
    out["tags"][tid] = r
    print(tid, {k: (round(v, 2) if isinstance(v, float) else v) for k, v in r.items()})

# geometry check: neighbour spacing on the printed page (25 mm sheet, landscape, 7 columns)
PX, PY = 35.25, 40.25
def rc(t): return divmod(t-30, 7)
mean_t = {t: np.array([x[0] for x in poses[t]]).mean(0) for t in poses}
pairs = []
for a in poses:
    for b in poses:
        if a < b:
            (ra, ca), (rb, cb) = rc(a), rc(b)
            if (ra == rb and abs(ca-cb) == 1) or (ca == cb and abs(ra-rb) == 1):
                exp = PX if ra == rb else PY
                m = float(np.linalg.norm(mean_t[a]-mean_t[b]))
                pairs.append(dict(a=a, b=b, expected_mm=exp, measured_mm=m, err_mm=m-exp))
errs = np.array([p["err_mm"] for p in pairs])
print("neighbour spacing: n", len(pairs), "mean err %.1f mm, rms %.1f, max |%.1f|" % (errs.mean(), np.sqrt((errs**2).mean()), np.abs(errs).max()))
for p in pairs: print("  ", p["a"], p["b"], "exp", p["expected_mm"], "meas %.1f" % p["measured_mm"])
out["neighbour_pairs"] = pairs
# normals across tags (page is not flat, so this mixes curl with error)
n_all = {t: np.array([x[1] for x in poses[t]]).mean(0) for t in poses}
nm = np.mean(list(n_all.values()), 0); nm /= np.linalg.norm(nm)
out["normal_spread_deg"] = {t: float(np.degrees(np.arccos(abs(v @ nm / np.linalg.norm(v))))) for t, v in n_all.items()}
print("normal vs mean normal (deg):", {t: round(v, 1) for t, v in out["normal_spread_deg"].items()})

# resolution test: same frames at the stream's 1280x720 and at 2304x1296
res = {}
for W, H in [(4608, 2592), (2304, 1296), (1536, 864), (1280, 720)]:
    counts = []
    for p in imgs:
        g = cv2.cvtColor(cv2.imread(p), cv2.COLOR_BGR2GRAY)
        if W != 4608: g = cv2.resize(g, (W, H), interpolation=cv2.INTER_AREA)
        counts.append(len(run(g, F_FULL*W/4608)))
    res[f"{W}x{H}"] = counts
    print(W, H, "tags per frame", counts)
out["detections_by_resolution"] = res

# 10 mm page: try harder on the full-res frames (upscaled crop of the page area, sharpened)
tiny = []
for p in imgs:
    g = cv2.cvtColor(cv2.imread(p), cv2.COLOR_BGR2GRAY)
    crop = g[1050:1700, 650:1700]  # the two pages in this camera pose
    best = 0
    for s in (1, 2, 3):
        c = cv2.resize(crop, None, fx=s, fy=s, interpolation=cv2.INTER_CUBIC) if s > 1 else crop
        for dd in (det, make_detector(quad_sigma=0.8), make_detector(decode_sharpening=0.6)):
            ids = [d.tag_id for d in dd.detect(c) if 60 <= d.tag_id <= 107]
            best = max(best, len(ids))
    tiny.append(best)
print("10 mm tags decoded per frame (best of several settings):", tiny)
out["tiny_10mm_decoded_per_frame"] = tiny
json.dump(out, open(args.out, "w"), indent=1, default=float)
