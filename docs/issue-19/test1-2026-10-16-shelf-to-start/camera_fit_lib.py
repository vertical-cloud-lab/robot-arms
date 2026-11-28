"""Pieces for fit_camera.py (and the variants tried on 2026-10-16: bbox centre, roll bottom).
"""
"""Fit a camera model (pinhole + radial distortion, full-field 2304x1296 pixels) from the
green roll's image position in a run video and its 3D position from the arm trace."""
import sys, csv, math, json, cv2, numpy as np
from scipy.optimize import least_squares
sys.path.insert(0, __import__("os").path.join(__import__("os").path.dirname(__import__("os").path.abspath(__file__)), "..", "..", "..", "scripts"))
from piper_pick_tape import fk_all, tip, pos

def load_blobs(path, roi=(300, 450, 1700, 1296)):
    best = {}
    for r in csv.DictReader(open(path)):
        cx, cy, a = float(r["cx"]), float(r["cy"]), int(r["area"])
        if not (roi[0] <= cx <= roi[2] and roi[1] <= cy <= roi[3]):
            continue
        k = int(r["k"])
        if k not in best or a > best[k][3]:
            best[k] = (float(r["t"]), cx, cy, a, int(r["bw"]), int(r["bh"]))
    return best

def load_trace(path):
    rows = list(csv.DictReader(open(path)))
    t = np.array([float(r["t"]) for r in rows]); ph = [r["phase"] for r in rows]
    q = np.array([[float(r[f"j{i}"]) for i in range(1, 7)] for r in rows])
    g = np.array([float(r["grip_mm"]) for r in rows])
    return t, ph, q, g

def roll_points(t, ph, q, tcp=150.0, s_up=3.5, still=None):
    """3D roll centre per trace row, or None where unknown (in the fingers' way)."""
    P = []
    for i in range(len(t)):
        T6 = fk_all(list(q[i]))[5]
        tp = tip(T6, tcp); zt = [T6[0][2], T6[1][2], T6[2][2]]
        held = [a - s_up * b for a, b in zip(tp, zt)]
        P.append((ph[i], held))
    return P

SHELF = (360 * math.cos(math.radians(130)), 360 * math.sin(math.radians(130)), 60 + 24.5)

def build(blobs, t, ph, q, off, s_up=3.5, rel=(248.0, 0.0), max_static=40):
    """Pairs (image xy, 3D point, kind) for one trace-video time offset."""
    T6s = None
    img, P3, kind = [], [], []
    stat = {"shelf": 0, "table": 0}
    for k in sorted(blobs):
        tv, cx, cy, a, bw, bh = blobs[k]
        tt = tv + off
        if a < 300:
            continue
        if tt < t[0]:
            continue
        i = min(int(np.searchsorted(t, tt)), len(t) - 1)
        p = ph[i]
        if p in ("start", "open", "to_pregrasp"):
            if stat["shelf"] >= max_static: continue
            stat["shelf"] += 1; img.append((cx, cy)); P3.append(SHELF); kind.append(0)
        elif p in ("up", "hold", "place"):
            T6 = fk_all(list(q[i]))[5]
            tp = tip(T6, 150.0); zt = [T6[0][2], T6[1][2], T6[2][2]]
            img.append((cx, cy)); P3.append([a_ - s_up * b_ for a_, b_ in zip(tp, zt)]); kind.append(1)
        elif p in ("home", "gripper", "estop", "reset", "disable") or tt > t[-1]:
            if stat["table"] >= max_static: continue
            stat["table"] += 1; img.append((cx, cy)); P3.append((rel[0], rel[1], 24.5)); kind.append(2)
    return np.array(img, float), np.array(P3, float), np.array(kind)

def project(x, P3):
    rvec, tvec = x[0:3], x[3:6]
    f, cx, cy, k1, k2 = x[6:11]
    K = np.array([[f, 0, cx], [0, f, cy], [0, 0, 1.0]])
    pts, _ = cv2.projectPoints(P3.reshape(-1, 1, 3), rvec, tvec, K, np.array([k1, k2, 0, 0, 0.0]))
    return pts.reshape(-1, 2)

def fit(img, P3, x0=None):
    K = np.array([[982.0, 0, 1152], [0, 982.0, 648], [0, 0, 1]])
    if x0 is None:
        ok, rvec, tvec = cv2.solvePnP(P3, img, K, None, flags=cv2.SOLVEPNP_EPNP)
        ok, rvec, tvec = cv2.solvePnP(P3, img, K, None, rvec, tvec, True, flags=cv2.SOLVEPNP_ITERATIVE)
        x0 = np.r_[rvec.ravel(), tvec.ravel(), 982.0, 1152, 648, 0.0, 0.0]
    res = least_squares(lambda x: (project(x, P3) - img).ravel(), x0, loss="soft_l1", f_scale=3.0)
    r = np.linalg.norm((project(res.x, P3) - img), axis=1)
    return res.x, r

def project2(x, P3, cx=1152.0, cy=648.0):
    rvec, tvec, f, k1 = x[0:3], x[3:6], x[6], x[7]
    K = np.array([[f, 0, cx], [0, f, cy], [0, 0, 1.0]])
    pts, _ = cv2.projectPoints(P3.reshape(-1, 1, 3), rvec, tvec, K, np.array([k1, 0, 0, 0, 0.0]))
    return pts.reshape(-1, 2)

def fit2(img, P3, f0=950.0):
    K = np.array([[f0, 0, 1152], [0, f0, 648], [0, 0, 1]])
    ok, rvec, tvec = cv2.solvePnP(P3, img, K, None, flags=cv2.SOLVEPNP_EPNP)
    ok, rvec, tvec = cv2.solvePnP(P3, img, K, None, rvec, tvec, True, flags=cv2.SOLVEPNP_ITERATIVE)
    x0 = np.r_[rvec.ravel(), tvec.ravel(), f0, 0.0]
    res = least_squares(lambda x: np.r_[(project2(x, P3) - img).ravel(), 0.05 * (x[6] - f0)],
                        x0, loss="soft_l1", f_scale=3.0)
    r = np.linalg.norm((project2(res.x, P3) - img), axis=1)
    return res.x, r

def ray_to_plane(x, uv, z, cx=1152.0, cy=648.0):
    """Back-project pixel uv to the horizontal plane at height z (mm, arm frame)."""
    rvec, tvec, f, k1 = x[0:3], x[3:6], x[6], x[7]
    K = np.array([[f, 0, cx], [0, f, cy], [0, 0, 1.0]])
    n = cv2.undistortPoints(np.array(uv, float).reshape(-1, 1, 2), K, np.array([k1, 0, 0, 0, 0.0])).reshape(-1, 2)
    R, _ = cv2.Rodrigues(rvec)
    C = -R.T @ tvec  # camera centre in the arm frame
    out = []
    for u, v in n:
        d = R.T @ np.array([u, v, 1.0])
        s = (z - C[2]) / d[2]
        out.append(C + s * d)
    return np.array(out), C

def load_blobs_b(path, roi=(300, 450, 1700, 1296)):
    """Per frame: (t, u, v, area, bw, bh) with (u, v) the bottom-centre of the roll's bbox."""
    best = {}
    for r in csv.DictReader(open(path)):
        cx, cy, a = float(r["cx"]), float(r["cy"]), int(r["area"])
        if not (roi[0] <= cx <= roi[2] and roi[1] <= cy <= roi[3]):
            continue
        k = int(r["k"])
        if k not in best or a > best[k][3]:
            x0, y0, bw, bh = int(r["x0"]), int(r["y0"]), int(r["bw"]), int(r["bh"])
            best[k] = (float(r["t"]), x0 + bw / 2.0, y0 + bh, a, bw, bh)
    return best

def build_b(blobs, t, ph, q, off, rel=(248.0, 0.0), n_static=150):
    img, P3, kind = [], [], []
    stat = {0: 0, 2: 0}
    for k in sorted(blobs):
        tv, u, v, a, bw, bh = blobs[k]
        tt = tv + off
        if a < 300 or tt < t[0]:
            continue
        i = min(int(np.searchsorted(t, tt)), len(t) - 1)
        p = ph[i]
        if p in ("start", "open", "to_pregrasp"):
            if stat[0] >= n_static: continue
            stat[0] += 1; img.append((u, v)); P3.append((SHELF[0], SHELF[1], 60.0)); kind.append(0)
        elif p in ("up", "hold", "place"):
            T6 = fk_all(list(q[i]))[5]
            tp = tip(T6, 150.0); zt = [T6[0][2], T6[1][2], T6[2][2]]
            c = [a_ - 3.5 * b_ for a_, b_ in zip(tp, zt)]
            img.append((u, v)); P3.append((c[0], c[1], c[2] - 24.5)); kind.append(1)
        elif p in ("home", "gripper", "estop", "reset", "disable") or tt > t[-1]:
            if stat[2] >= n_static: continue
            stat[2] += 1; img.append((u, v)); P3.append((rel[0], rel[1], 0.0)); kind.append(2)
    return np.array(img, float), np.array(P3, float), np.array(kind)

def load_blobs_c(path, roi=(300, 450, 1700, 1296)):
    """Per frame: (t, u, v, area, bw, bh) with (u, v) the centre of the roll's bbox."""
    best = {}
    for r in csv.DictReader(open(path)):
        cx, cy, a = float(r["cx"]), float(r["cy"]), int(r["area"])
        if not (roi[0] <= cx <= roi[2] and roi[1] <= cy <= roi[3]):
            continue
        k = int(r["k"])
        if k not in best or a > best[k][3]:
            x0, y0, bw, bh = int(r["x0"]), int(r["y0"]), int(r["bw"]), int(r["bh"])
            best[k] = (float(r["t"]), x0 + bw / 2.0, y0 + bh / 2.0, a, bw, bh)
    return best

def build_c(blobs, t, ph, q, off, rel=(248.0, 0.0), n_static=150, zc=24.5):
    img, P3, kind = [], [], []
    stat = {0: 0, 2: 0}
    for k in sorted(blobs):
        tv, u, v, a, bw, bh = blobs[k]
        tt = tv + off
        if a < 300 or tt < t[0]:
            continue
        i = min(int(np.searchsorted(t, tt)), len(t) - 1)
        p = ph[i]
        if p in ("start", "open", "to_pregrasp"):
            if stat[0] >= n_static: continue
            stat[0] += 1; img.append((u, v)); P3.append((SHELF[0], SHELF[1], 60 + zc)); kind.append(0)
        elif p in ("up", "hold", "place"):
            T6 = fk_all(list(q[i]))[5]
            tp = tip(T6, 150.0); zt = [T6[0][2], T6[1][2], T6[2][2]]
            c = [a_ - 3.5 * b_ for a_, b_ in zip(tp, zt)]
            img.append((u, v)); P3.append((c[0], c[1], c[2])); kind.append(1)
        elif p in ("home", "gripper", "estop", "reset", "disable") or tt > t[-1]:
            if stat[2] >= n_static: continue
            stat[2] += 1; img.append((u, v)); P3.append((rel[0], rel[1], zc)); kind.append(2)
    return np.array(img, float), np.array(P3, float), np.array(kind)

def fit3(img, P3, kind, f0=950.0):
    """As fit2, plus a constant image offset for held-roll frames (a finger hides part of it)."""
    x2, _ = fit2(img, P3, f0)
    x0 = np.r_[x2, 0.0, 0.0]
    held = kind == 1
    def resid(x):
        pr = project2(x[:8], P3)
        pr[held] += x[8:10]
        w = np.where(held, 1.0, 2.0)[:, None]
        return np.r_[((pr - img) * w).ravel(), 0.05 * (x[6] - f0)]
    res = least_squares(resid, x0, loss="soft_l1", f_scale=3.0)
    pr = project2(res.x[:8], P3); pr[held] += res.x[8:10]
    return res.x, np.linalg.norm(pr - img, axis=1)
