#!/usr/bin/env python3
"""Overhead camera plus two side cameras: does one Pi with two 500 mm cables cost accuracy? (#24)

The taped camera is gone, so the cell gets three fixed cameras: the overhead camera A from
docs/issue-24/camera-placement and two side cameras. If both side cameras hang off one Raspberry
Pi 5 (two CSI ports, two 500 mm ribbon cables) they can be at most ~1 m apart; three Pis remove
that limit. This scores every pair of side-camera spots around the table, together with A, on the
same 400 arm poses and 1 px noise model as piper_camera_placement.py, and asks how much the best
score drops when the pair has to fit the cables.

    python scripts/piper_camera_cable_check.py --out docs/issue-24/camera-literature

Cable model: a ribbon runs along the table edges or a frame, so its path from the Pi to a camera
is at least the Manhattan distance |dx| + |dy| + |dz| from the Pi. With the Pi at the best point
between the two cameras, the pair fits if that distance between the cameras is at most
2 x (500 mm - SLACK_MM). The straight-line distance is reported as well.

Frame and models as in piper_camera_placement.py (arm base frame, mm; x the way the arm faces at
J1 = 0, y toward the wall, z up from the plate; Camera Module 3 Wide at 2304 x 1296, no
distortion). Simulated only; never talks to the arm.
"""
import argparse
import itertools
import json
import math
import multiprocessing as mp
import os

for _v in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS"):
    os.environ.setdefault(_v, "1")  # one thread per worker; the pool does the parallelism

import numpy as np  # noqa: E402

import piper_camera_placement as pcp  # noqa: E402
import piper_twin as pt  # noqa: E402

CABLE_MM = 500.0
SLACK_MM = 50.0  # connector bends and strain relief at each end
FITS_MM = 2 * (CABLE_MM - SLACK_MM)
TARGET = (100, 0, 150)  # every side camera aims here: in front of J1, at the working height
OVERHEAD = dict(eye=(0, -75, 1200), target=(0, -75, 0), up=(0, 1, 0))  # camera A


def side_spots():
    """Side-camera spots around the table, outside the fingertips' reach.

    Room-side edge (y just past the front edge), both ends (x just past the table), the two
    room-side corners, and the wall (high only, since the wall is inside the reach lower down).
    """
    t = pcp.TABLE
    spots = {}
    for z in (150, 300, 450, 650):
        for x in range(-600, 601, 150):
            spots[f"room edge x{x:+d} z{z}"] = (x, t["y0"] - 20, z)
        for y in range(-600, 451, 150):
            spots[f"right end y{y:+d} z{z}"] = (t["x1"] + 100, y, z)
            spots[f"left end y{y:+d} z{z}"] = (t["x0"] - 100, y, z)
        spots[f"room-right corner z{z}"] = (t["x1"] + 60, t["y0"] - 20, z)
        spots[f"room-left corner z{z}"] = (t["x0"] - 60, t["y0"] - 20, z)
    for z in (650, 800):
        for x in range(-600, 601, 300):
            spots[f"wall x{x:+d} z{z}"] = (x, t["y1"] - 20, z)
    keep = {}
    for name, eye in spots.items():
        if np.linalg.norm(np.array(eye, float) - pcp.J2) > pcp.REACH_MM + 30:
            keep[name] = eye
    return keep


_WORK = {}


def _chunk(poses):
    cams, meshes = _WORK["cams"], _WORK["meshes"]
    seen, _, tips = pcp.evaluate(cams, poses, meshes)
    info = np.zeros((len(poses), len(cams), 3, 3))
    for i, j in zip(*np.nonzero(seen)):
        J = pcp.jac(cams[j], tips[i])
        info[i, j] = J.T @ J
    return seen, info, tips


def info_matrices(cams, poses, meshes, workers=None):
    """Per pose and camera: whether the fingertips are seen, and J^T J of the projection there."""
    _WORK.update(cams=cams, meshes=meshes)
    workers = workers or os.cpu_count() or 1
    chunks = [poses[k::workers * 4] for k in range(workers * 4)]
    with mp.get_context("fork").Pool(workers) as pool:
        parts = pool.map(_chunk, chunks)
    order = np.concatenate([np.arange(len(poses))[k::workers * 4] for k in range(workers * 4)])
    seen, info, tips = (np.concatenate(x) for x in zip(*parts))
    back = np.argsort(order)
    return seen[back], info[back], tips[back]


def score(idx, seen, info):
    """Score the cameras idx together, as piper_camera_placement.py does."""
    n_seen = seen[:, idx].sum(1)
    A = info[:, idx].sum(1)
    err = np.full(len(A), np.inf)
    ok = n_seen >= 2
    if ok.any():
        Ainv = np.linalg.inv(A[ok] + np.eye(3) * 1e-12)
        err[ok] = pcp.PX_SIGMA * np.sqrt(np.clip(np.trace(Ainv, axis1=1, axis2=2), 0, None))
    fin = err[np.isfinite(err)]
    return dict(seen_by_2plus_pct=round(100 * float(ok.mean()), 1),
                seen_by_any_pct=round(100 * float((n_seen >= 1).mean()), 1),
                median_err_mm=round(float(np.median(fin)), 2) if len(fin) else None,
                within_1mm_pct=round(100 * float((err <= 1.0).mean()), 1),
                within_2mm_pct=round(100 * float((err <= 2.0).mean()), 1))


def azimuth(eye):
    return math.degrees(math.atan2(eye[1], eye[0]))


def angle_between(e1, e2, target=TARGET):
    a, b = np.subtract(e1, target), np.subtract(e2, target)
    return math.degrees(math.acos(np.clip(a @ b / np.linalg.norm(a) / np.linalg.norm(b), -1, 1)))


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--out", default="docs/issue-24/camera-literature")
    ap.add_argument("--poses", type=int, default=400)
    ap.add_argument("--plot-only", action="store_true", help="redraw cable_check.png from the JSON")
    ap.add_argument("--overheads", action="store_true",
                    help="score a few overhead variants with the best pairs of an existing "
                         "cable_check.json (writes overhead_check.json)")
    args = ap.parse_args()
    os.makedirs(args.out, exist_ok=True)
    if args.plot_only:
        plot(args.out)
        return
    if args.overheads:
        overhead_check(args.out, args.poses)
        return

    meshes = pt.load_meshes()
    spots = side_spots()
    # the 2026-10-14 cameras, for reference
    ref = {"B (2026-10-14)": pcp.CANDIDATES["front-end"]["eye"],
           "taped (2026-10-13)": None}
    names = ["A overhead"] + list(spots) + list(ref)
    cams = [pcp.look_cam(OVERHEAD["eye"], OVERHEAD["target"], OVERHEAD["up"])]
    cams += [pcp.look_cam(eye, TARGET) for eye in spots.values()]
    cams += [pcp.look_cam(ref["B (2026-10-14)"], pcp.CANDIDATES["front-end"]["target"]),
             pcp.taped_camera()]
    eyes = [OVERHEAD["eye"]] + list(spots.values()) + [ref["B (2026-10-14)"],
                                                       tuple(cams[-1].center().round(0))]
    print(f"{len(spots)} side spots outside the reach; scoring on {args.poses} poses", flush=True)

    poses = pcp.sample_poses(args.poses)
    seen, info, _ = info_matrices(cams, poses, meshes)

    side = list(range(1, 1 + len(spots)))
    pairs = []
    for a, b in itertools.combinations(side, 2):
        ea, eb = np.array(eyes[a], float), np.array(eyes[b], float)
        r = dict(cameras=[names[a], names[b]],
                 straight_mm=round(float(np.linalg.norm(ea - eb))),
                 manhattan_mm=round(float(np.abs(ea - eb).sum())),
                 angle_at_target_deg=round(angle_between(ea, eb), 1),
                 azimuth_gap_deg=round(abs((azimuth(ea) - azimuth(eb) + 180) % 360 - 180), 1),
                 **score([0, a, b], seen, info))
        r["fits_two_500mm_cables"] = r["manhattan_mm"] <= FITS_MM
        pairs.append(r)
    key = lambda r: (-r["within_2mm_pct"], -r["seen_by_2plus_pct"])  # noqa: E731
    pairs.sort(key=key)
    fitting = [r for r in pairs if r["fits_two_500mm_cables"]]

    # the best score available under a cable budget (Manhattan distance between the cameras)
    frontier = []
    for limit in range(300, 2601, 100):
        ok = [r for r in pairs if r["manhattan_mm"] <= limit]
        if ok:
            best = min(ok, key=key)
            frontier.append(dict(max_manhattan_mm=limit, **{k: best[k] for k in (
                "cameras", "within_2mm_pct", "seen_by_2plus_pct", "median_err_mm",
                "straight_mm", "angle_at_target_deg")}))

    # how the score depends on the angle the two side cameras make at the working area
    bins = []
    for lo in range(0, 180, 15):
        sel = [r for r in pairs if lo <= r["angle_at_target_deg"] < lo + 15]
        if sel:
            w2 = np.array([r["within_2mm_pct"] for r in sel])
            bins.append(dict(angle_deg=[lo, lo + 15], n_pairs=len(sel),
                             median_within_2mm_pct=round(float(np.median(w2)), 1),
                             best_within_2mm_pct=round(float(w2.max()), 1)))

    i_b, i_t = names.index("B (2026-10-14)"), names.index("taped (2026-10-13)")
    out = dict(
        note="Simulated with the digital twin; 1 px noise at 2304x1296; side cameras aim at "
             f"{TARGET}; A is the overhead camera at {OVERHEAD['eye']} looking straight down.",
        cable_model=f"fits if |dx|+|dy|+|dz| between the cameras <= 2 x ({CABLE_MM:.0f} - "
                    f"{SLACK_MM:.0f}) = {FITS_MM:.0f} mm (Pi between them)",
        n_poses=len(poses), n_side_spots=len(spots), n_pairs=len(pairs),
        reference={"A + B + taped (2026-10-14 plan)": score([0, i_b, i_t], seen, info),
                   "A + B": score([0, i_b], seen, info),
                   "A only": score([0], seen, info)},
        per_camera={n: dict(position_mm=[round(v) for v in e],
                            fingertips_seen_pct=round(100 * float(seen[:, j].mean()), 1))
                    for j, (n, e) in enumerate(zip(names, eyes))},
        best_pairs=pairs[:25], best_fitting_pairs=fitting[:25],
        frontier=frontier, by_angle=bins)
    json.dump(out, open(os.path.join(args.out, "cable_check.json"), "w"), indent=1)
    plot(args.out)
    print(json.dumps(dict(reference=out["reference"], best=pairs[:5], best_fitting=fitting[:5],
                          by_angle=bins), indent=1))


# ---------------------------------------------------------------- overhead variants
OVERHEADS = {  # ALOHA 2 tilts its overhead camera 25 deg toward the operator; try a few
    "A: straight down, 1.2 m": dict(eye=(0, -75, 1200), target=(0, -75, 0), up=(0, 1, 0)),
    "straight down, 1.5 m": dict(eye=(0, -75, 1500), target=(0, -75, 0), up=(0, 1, 0)),
    "tilted 20 deg from the room side": dict(eye=(0, -480, 1150), target=(0, -60, 0),
                                              up=(0, 1, 0)),
    "tilted 30 deg from the room side": dict(eye=(0, -650, 1050), target=(0, -40, 0),
                                              up=(0, 1, 0)),
    "tilted 25 deg from the door end": dict(eye=(-520, -75, 1100), target=(0, -75, 0),
                                             up=(1, 0, 0)),
}


def overhead_check(out_dir, poses_n):
    """Each overhead variant with the best one-Pi pair and the best pair overall."""
    d = json.load(open(os.path.join(out_dir, "cable_check.json")))
    pos = {n: v["position_mm"] for n, v in d["per_camera"].items()}
    pairs = {"best one-Pi pair": d["best_fitting_pairs"][0]["cameras"],
             "best pair, no cable limit": d["best_pairs"][0]["cameras"]}
    names = list(OVERHEADS) + sorted({c for p in pairs.values() for c in p})
    cams = [pcp.look_cam(v["eye"], v["target"], v["up"]) for v in OVERHEADS.values()]
    cams += [pcp.look_cam(pos[n], TARGET) for n in names[len(OVERHEADS):]]
    meshes = pt.load_meshes()
    seen, info, _ = info_matrices(cams, pcp.sample_poses(poses_n), meshes)
    out = {}
    for j, (name, v) in enumerate(OVERHEADS.items()):
        out[name] = dict(position_mm=list(v["eye"]),
                         sees_fingertips_pct=round(100 * float(seen[:, j].mean()), 1),
                         **{k: score([j] + [names.index(c) for c in pr], seen, info)
                            for k, pr in pairs.items()})
    json.dump(dict(pairs=pairs, overheads=out), open(os.path.join(out_dir, "overhead_check.json"),
                                                      "w"), indent=1)
    print(json.dumps(out, indent=1))


# ---------------------------------------------------------------- figure
INK, INK2, MUTED, GRID, SURFACE = "#0b0b0b", "#52514e", "#a3a29c", "#e4e3df", "#fcfcfb"
BLUE, ORANGE = "#2a78d6", "#eb6834"


def plot(out_dir):
    """Map of the best pairs, best score vs. cable budget, and score vs. the cameras' angle."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    d = json.load(open(os.path.join(out_dir, "cable_check.json")))
    pos = {n: v["position_mm"] for n, v in d["per_camera"].items()}
    best, fit = d["best_pairs"][0], d["best_fitting_pairs"][0]
    plt.rcParams.update({"font.size": 10, "axes.edgecolor": GRID, "axes.labelcolor": INK2,
                         "xtick.color": INK2, "ytick.color": INK2, "text.color": INK})
    fig, axs = plt.subplots(1, 3, figsize=(17, 5.6), facecolor=SURFACE,
                            gridspec_kw=dict(width_ratios=[1.15, 1, 1]))
    for ax in axs:
        ax.set_facecolor(SURFACE)
        for side in ("top", "right"):
            ax.spines[side].set_visible(False)

    # (a) top-down map
    ax = axs[0]
    t = pcp.TABLE
    ax.add_patch(plt.Rectangle((t["x0"], t["y0"]), t["x1"] - t["x0"], t["y1"] - t["y0"],
                               fc="#f0efec", ec="#c3c2b7", lw=1, zorder=0))
    ax.plot([-1000, 1000], [t["y1"], t["y1"]], color=INK2, lw=3, solid_capstyle="butt")
    ax.text(-980, t["y1"] + 25, "wall", color=INK2, fontsize=9)
    r = math.sqrt(pcp.REACH_MM ** 2 - pcp.J2[2] ** 2)
    a = np.linspace(0, 2 * np.pi, 200)
    ax.plot(r * np.cos(a), r * np.sin(a), color=MUTED, lw=1)
    ax.text(-r * 0.71 - 30, -r * 0.71 - 70, "fingertip reach\nat table height", color=INK2,
            fontsize=8, ha="right")
    ax.plot(0, 0, "s", color=INK, ms=7)
    ax.text(25, 25, "J1", fontsize=9)
    ax.plot(*TARGET[:2], "+", color=INK2, ms=9, mew=1.5)
    side = [n for n in pos if n not in ("A overhead", "B (2026-10-14)", "taped (2026-10-13)")]
    ax.plot([pos[n][0] for n in side], [pos[n][1] for n in side], ".", color=MUTED, ms=4,
            label="side spots scored")
    ax.plot(*pos["A overhead"][:2], "D", color=INK, ms=8, mec=SURFACE, mew=2)
    ax.text(pos["A overhead"][0] + 30, pos["A overhead"][1] - 70, "A: 1.2 m up,\nstraight down",
            fontsize=8, color=INK2)
    for n, lab in (("B (2026-10-14)", "B (Oct 14)"), ("taped (2026-10-13)", "old taped")):
        ax.plot(*pos[n][:2], "o", mfc="none", mec=INK2, ms=9, mew=1.2)
        ax.text(pos[n][0] + 30, pos[n][1] + 30, lab, fontsize=8, color=INK2)
    labels = {}
    for pair, col, who, ring in ((best, BLUE, "3 Pis, no cable limit", True),
                                 (fit, ORANGE, "one Pi, 2 x 500 mm", False)):
        e1, e2 = (np.array(pos[c], float) for c in pair["cameras"])
        for e in (e1, e2):
            ax.plot([e[0], TARGET[0]], [e[1], TARGET[1]], color=col, lw=1, alpha=0.7)
            labels.setdefault(tuple(e[:2]), []).append(f"{e[2]:.0f} mm up ({who.split(',')[0]})")
        lab = (f"best pair, {who}: {pair['within_2mm_pct']:.0f} % within 2 mm, "
               f"{pair['angle_at_target_deg']:.0f} deg apart")
        if ring:  # hollow and larger, so a spot both pairs use shows both
            ax.plot([e1[0], e2[0]], [e1[1], e2[1]], "o", mfc="none", mec=col, ms=15, mew=2.5,
                    label=lab, zorder=5)
        else:
            ax.plot([e1[0], e2[0]], [e1[1], e2[1]], "o", color=col, ms=9, mec=SURFACE, mew=2,
                    label=lab, zorder=6)
        if not ring:  # ribbon route along the edges, Pi halfway along it
            path = np.array([e1[:2], [e2[0], e1[1]], e2[:2]])
            ax.plot(path[:, 0], path[:, 1], color=col, lw=2, ls=(0, (4, 3)))
            seg = np.cumsum(np.r_[0, np.abs(np.diff(path, axis=0)).sum(1)])
            half = seg[-1] / 2
            k = int(np.searchsorted(seg, half)) - 1
            pi = path[k] + (path[k + 1] - path[k]) * (half - seg[k]) / max(seg[k + 1] - seg[k], 1)
            ax.plot(*pi, "s", color=INK, ms=9, mec=SURFACE, mew=2, zorder=7)
            ax.text(pi[0] + 40, pi[1] - 60, "Pi", fontsize=9)
    for (x, y), lines in labels.items():
        ax.text(x + 45, y - 40 - 48 * len(lines), "\n".join(lines), fontsize=8, color=INK2)
    ax.set_xlim(-1000, 1250)
    ax.set_ylim(-1250, 720)
    ax.set_aspect("equal")
    ax.set_xlabel("x (mm), the way the arm faces at J1 = 0")
    ax.set_ylabel("y (mm), toward the wall")
    ax.set_title("Best side-camera pairs, with overhead camera A", loc="left", fontsize=11)
    ax.legend(loc="lower left", fontsize=8, frameon=False)

    # (b) best score vs. cable budget
    ax = axs[1]
    fr = d["frontier"]
    xs = [f["max_manhattan_mm"] for f in fr]
    ys = [f["within_2mm_pct"] for f in fr]
    ax.axvspan(0, FITS_MM, color=ORANGE, alpha=0.08, lw=0)
    ax.text(FITS_MM - 30, 3, f"fits two 500 mm\nribbons (<= {FITS_MM:.0f} mm)", ha="right",
            fontsize=8, color=INK2)
    ax.step(xs, ys, where="post", color=INK, lw=2)
    ax.plot(xs, ys, "o", color=INK, ms=5, mec=SURFACE, mew=1)
    ref = d["reference"]["A + B + taped (2026-10-14 plan)"]["within_2mm_pct"]
    ax.axhline(best["within_2mm_pct"], color=BLUE, lw=1)
    ax.text(xs[-1], best["within_2mm_pct"] - 5, f"no cable limit: {best['within_2mm_pct']:.0f} %",
            ha="right", fontsize=8, color=INK2)
    ax.axhline(ref, color=MUTED, lw=1)
    ax.text(xs[-1], ref - 9, f"Oct 14 plan (A + B + taped): {ref:.0f} %", ha="right",
            fontsize=8, color=INK2)
    ax.set_xlim(250, xs[-1] + 50)
    ax.set_ylim(0, 100)
    ax.grid(axis="y", color=GRID, lw=1)
    ax.set_axisbelow(True)
    ax.set_xlabel("cable budget: |dx| + |dy| + |dz| between the side cameras (mm)")
    ax.set_ylabel("poses with fingertips within 2 mm (%)")
    ax.set_title("Best score you can get on a cable budget", loc="left", fontsize=11)

    # (c) score vs. the angle the side cameras make at the working area
    ax = axs[2]
    bins = d["by_angle"]
    cx = [np.mean(b["angle_deg"]) for b in bins]
    ax.plot(cx, [b["best_within_2mm_pct"] for b in bins], "-o", color=INK, lw=2, ms=7,
            mec=SURFACE, mew=2, label="best pair in each 15 deg bin")
    ax.plot(cx, [b["median_within_2mm_pct"] for b in bins], "-o", color=MUTED, lw=2, ms=7,
            mec=SURFACE, mew=2, label="median pair in each 15 deg bin")
    ax.axvline(90, color=GRID, lw=1)
    ax.text(92, 96, "90 deg", fontsize=8, color=INK2)
    ax.set_xlim(0, 180)
    ax.set_ylim(0, 100)
    ax.set_xticks(range(0, 181, 30))
    ax.grid(axis="y", color=GRID, lw=1)
    ax.set_axisbelow(True)
    ax.set_xlabel("angle between the two side cameras, seen from the working area (deg)")
    ax.set_ylabel("poses with fingertips within 2 mm (%)")
    ax.set_title("Score vs. how far apart the side cameras look", loc="left", fontsize=11)
    ax.legend(loc="lower right", fontsize=8, frameon=False)
    fig.text(0.01, 0.005, f"Digital twin, simulated: {d['n_poses']} arm poses, {d['n_pairs']} "
             "side-camera pairs, each with overhead camera A; Camera Module 3 Wide, 1 px noise "
             "at 2304x1296. Side cameras aim at the + in front of J1.", fontsize=8, color=INK2)
    fig.tight_layout(rect=(0, 0.03, 1, 1))
    fig.savefig(os.path.join(out_dir, "cable_check.png"), dpi=110, facecolor=SURFACE)


if __name__ == "__main__":
    main()
