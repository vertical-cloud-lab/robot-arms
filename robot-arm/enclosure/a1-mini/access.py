"""Can the PiPER take a print off the A1 mini's bed with the gripper level with the bed, or only
from above? Layouts from jss265's comment on PR #9 (27 Oct 2026):

  wall     as it was in the photo: the printer against the block wall facing the arm, with the
           AMS lite turned to Bambu's layout behind it (toward the door)
  corner   sgbaird's 45 deg corner (render.py), the arm where it is
  moved    the same corner, the arm moved back toward the door (the smallest move, in 25 mm steps,
           that reaches as many spots on the bed as any move does)
  people-r the printer in the front-right corner facing the E-stop side, so its screen, plate and
           AMS lite face the people there; the arm, where it is, comes in from the purge side
  people   the printer at the middle of the front edge, facing the E-stop side; the bed parks at
           the back and the arm, moved back the same way, takes the print off the back of the plate

    python access.py      # access.json; then xvfb-run -a python access_render.py

A level grasp has the fingers opening sideways, nearly parallel to the bed (tool axis tipped down
0 or 10 deg), and their bottoms 2 mm above it. The gripper's housing (164 x 75 mm) is lower than
that and cannot pass over the bed, so only the 76 mm fingers do: the print has to be within 35 mm
of an open edge of the bed. From above, the tool points straight down with the fingertips 3 mm off
the bed. A pose counts if every joint is 3 deg or more inside its URDF limit and the arm clears the
printer, the AMS lite, the plywood and its own base by 2 mm.
"""

import json
import sys
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

import numpy as np
import trimesh
from scipy.optimize import least_squares

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE))
import render as A  # noqa: E402  the A1 mini, AMS lite and table
from piper_fk import Piper  # noqa: E402

B = A.B
TCP = 0.105                 # grasp point on the tool axis past the flange: 37 mm ahead of the housing
EDGE_IN = 35.0              # mm, level grasp: print centre in from the bed's edge
ABOVE_UP = 0.038            # from above: grasp point above the bed's top (fingertips 3 mm off it)
PITCHES = (0.0, 10.0)       # level grasp: tool axis this far below horizontal, flattest first
YAWS = (0, 20, -20, 40, -40, 60, -60)       # deg off square to the edge
MARGIN_DEG = 3.0
CLEAR = 0.002
BED_TOP = 0.082             # bed's top above the plywood (render.py's printer())
BED_FWD = A.TRAVEL[1] - A.BED_L / 2         # bed centre, fully forward (mm from the base's back)
BED_BACK = A.TRAVEL[0] + A.BED_L / 2        # fully back
ARM_TURN = A.ARM_TURN


# ------------------------------------------------------------------ layouts
def _R2(turn):
    t = np.radians(turn)
    return np.array([[np.cos(t), -np.sin(t)], [np.sin(t), np.cos(t)]])


def fit(turn, sx, sy):
    """Combo centre (world xy) for a turn, pushed toward the (sx, sy) corner until something is
    MARGIN from the plywood's edge; sx = 0 centres the bed on x = 0 instead. The bed's whole
    travel counts."""
    swept = A.printer(bed_v=BED_BACK) + A.printer(bed_v=BED_FWD) + A.ams_lite()
    xy = np.vstack([m.vertices[:, :2] for m, _ in swept]) @ _R2(turn).T / 1e3
    lim = B.P2 - A.MARGIN
    if sx == 0:
        cx = -(_R2(turn) @ [np.mean(A.BED_U) - A.COMBO_W / 2, 0])[0] / 1e3
    else:
        cx = lim - xy[:, 0].max() if sx > 0 else -lim - xy[:, 0].min()
    cy = lim - xy[:, 1].max() if sy > 0 else -lim - xy[:, 1].min()
    return np.array([cx, cy])


def wall_centre():
    """As in the photo: the printer's base centred on cameras/build.py's (0.40, 0.36), facing -x."""
    pc = np.array([-A.COMBO_W / 2 + A.PRINTER_W / 2, 0.0]) / 1e3
    return np.array(B.A1["xy"]) - _R2(-90.0) @ pc


def layout(name, back=0.0):
    """One layout. back: how far the arm is moved toward the door (m)."""
    d = dict(
        wall=dict(turn=-90.0, centre=wall_centre(), bed="fwd", edges=("front", "purge", "corner")),
        corner=dict(turn=-45.0, centre=A.CENTRE.copy(), bed="fwd", edges=("front", "purge", "corner")),
        moved=dict(turn=-45.0, centre=A.CENTRE.copy(), bed="fwd", edges=("front", "purge", "corner")),
        people=dict(turn=180.0, centre=fit(180.0, 0, 1), bed="back", edges=("back",)),
        **{"people-r": dict(turn=180.0, centre=fit(180.0, -1, 1), bed="fwd", edges=("purge", "corner", "front"))},
    )[name]
    d.update(name=name, arm=np.array([0.0, -back]), back=back)
    d["bed_v"] = BED_FWD if d["bed"] == "fwd" else BED_BACK
    return d


def combo_M(lay):
    """Combo frame (mm) -> world (m)."""
    M = np.eye(4)
    M[:3, :3] = trimesh.transformations.rotation_matrix(np.radians(lay["turn"]), (0, 0, 1))[:3, :3] / 1e3
    M[:3, 3] = [*lay["centre"], B.PLY_T]
    return M


def arm_M(lay):
    """Arm frame -> world: J1 on the plywood at lay['arm'], J1 = 0 facing the open front."""
    M = trimesh.transformations.rotation_matrix(np.radians(ARM_TURN), (0, 0, 1))
    M[:3, 3] = [*lay["arm"], B.PLY_T]
    return M


def obstacles(lay):
    """Axis-aligned boxes in the combo frame (mm): the printer with its bed parked, and the AMS
    lite's bounding box."""
    boxes = [m.bounds for m, _ in A.printer(bed_v=lay["bed_v"])]
    ams = np.vstack([m.bounds for m, _ in A.ams_lite()])
    boxes.append(np.array([ams.min(0), ams.max(0)]))
    return np.array(boxes)


def bed_box(lay):
    v = lay["bed_v"]
    return A.pbox(*A.BED_U, v - A.BED_L / 2, v + A.BED_L / 2, 72, 82).bounds      # combo frame, mm


# ------------------------------------------------------------------ arm
def _rz(a):
    c, s = np.cos(a), np.sin(a)
    return np.array([[c, -s, 0], [s, c, 0], [0, 0, 1.0]])


class Arm:
    def __init__(self):
        self.p = Piper()
        self.lo = np.array([self.p.limits[f"joint{i}"][0] for i in range(1, 7)])
        self.hi = np.array([self.p.limits[f"joint{i}"][1] for i in range(1, 7)])
        self.chain = [j for j in self.p.joints if j["name"] in {f"joint{i}" for i in range(1, 7)}]
        rng = np.random.default_rng(0)
        self.pts = {}
        for name, path in self.p.meshes.items():
            sc = trimesh.load(path, force="scene")
            vs = []
            for node in sc.graph.nodes_geometry:
                Tn, g = sc.graph[node]
                m = sc.geometry[g]
                if len(m.faces) >= 10:
                    vs.append(trimesh.transform_points(m.vertices[np.unique(m.faces)], Tn))
            v = np.vstack(vs)
            v = v[rng.choice(len(v), min(len(v), 900), replace=False)]
            self.pts[name] = trimesh.transform_points(v, self.p.visual_origin[name])

    def flange(self, q):
        """link6 pose in the arm frame (every PiPER joint turns about its local z)."""
        T = np.eye(4)
        for j, v in zip(self.chain, q):
            Rj = np.eye(4)
            Rj[:3, :3] = _rz(v)
            T = T @ j["T"] @ Rj
        return T

    def margin(self, q):
        return float(np.degrees(np.min(np.minimum(q - self.lo, self.hi - q))))

    def ik(self, M_arm, p, z_dir, x_dir=None, seeds=6, rng=None):
        """Joint angles putting the grasp point at p (world) with the tool axis along z_dir and the
        fingers' travel along x_dir (either sign), or horizontal if x_dir is None. Every distinct
        solution found, best joint margin first."""
        rng = rng or np.random.default_rng(1)
        Mi = np.linalg.inv(M_arm)
        pa, za = Mi[:3, :3] @ p + Mi[:3, 3], Mi[:3, :3] @ z_dir
        xa = None if x_dir is None else Mi[:3, :3] @ x_dir
        m = np.radians(MARGIN_DEG)
        lo, hi = self.lo + m, self.hi - m

        def res(q):
            T = self.flange(q)
            z, x = T[:3, 2], T[:3, 0]
            tail = np.cross(x, xa) * 200 if xa is not None else [x[2] * 200, 0.0, 0.0]
            return np.concatenate([(T[:3, 3] + z * TCP - pa) * 1e3, (z - za) * 200, tail])

        az = np.arctan2(pa[1], pa[0])
        sols = []
        for k in range(seeds):
            q0 = rng.uniform(lo, hi)
            if k % 2 == 0:
                q0[0] = np.clip(az + rng.normal(0, 0.3), lo[0], hi[0])
            s = least_squares(res, q0, bounds=(lo, hi), xtol=1e-10, ftol=1e-10, max_nfev=400)
            r = res(s.x)
            if np.linalg.norm(r[:3]) < 0.5 and np.linalg.norm(r[3:6]) < 200 * np.radians(0.5) and np.abs(r[6:]).max() < 2:
                if all(np.abs(s.x - o).max() > 1e-3 for o in sols):
                    sols.append(s.x)
        return sorted(sols, key=self.margin, reverse=True)

    def world_points(self, q, M_arm, grip=0.012):
        poses = self.p.fk(q, grip=grip)
        return {n: trimesh.transform_points(v, M_arm @ poses[n]) for n, v in self.pts.items()}, poses

    def clear(self, q, lay, boxes):
        """Smallest gap (m) from the arm to the printer, AMS lite, plywood and its own base and
        upper arm; negative is a hit."""
        Ma = arm_M(lay)
        pts, poses = self.world_points(q, Ma)
        P = np.vstack([pts[n] for n in pts if n not in ("arm_base", "link1")])
        Pc = trimesh.transform_points(P, np.linalg.inv(combo_M(lay)))       # combo frame, mm
        gaps = [(P[:, 2] - B.PLY_T).min()]
        for lo, hi in boxes:
            d = np.maximum(lo - Pc, Pc - hi)
            gaps.append(np.where(d.max(1) > 0, np.linalg.norm(np.maximum(d, 0), axis=1), d.max(1)).min() / 1e3)
        Mi = np.linalg.inv(Ma)
        Pa = trimesh.transform_points(np.vstack([pts[n] for n in ("link4", "link5", "link6", "link7", "link8")]), Mi)
        gaps.append(np.where(Pa[:, 2] < 0.16, np.hypot(Pa[:, 0] + 0.009, Pa[:, 1]) - 0.06, 1.0).min())
        a, b = poses["link2"][:3, 3], poses["link3"][:3, 3]                # upper arm as a 45 mm capsule
        G = trimesh.transform_points(np.vstack([pts[n] for n in ("link6", "link7", "link8")]), Mi)
        t = np.clip((G - a) @ (b - a) / ((b - a) @ (b - a)), 0, 1)
        gaps.append((np.linalg.norm(G - (a + t[:, None] * (b - a)), axis=1) - 0.045).min())
        return float(min(gaps))


# ------------------------------------------------------------------ grasps
def spots(lay):
    """Prints EDGE_IN inside each open edge of the bed: (edge, point and inward normal in the
    combo frame, mm)."""
    (x0, y0, _), (x1, y1, _) = bed_box(lay)
    out = []
    for e in lay["edges"]:
        if e == "front":                      # the printer's front, y_c = y0 (v = bed_v + 96)
            out += [(e, [x, y0 + EDGE_IN], [0, 1]) for x in np.linspace(x0 + 25, x1 - 25, 5)]
        elif e == "purge":                    # left side; the bed's back part is under the toolhead
            v_lo = max(lay["bed_v"] - A.BED_L / 2, 185.0)
            yb = A.BASE_D / 2 - v_lo
            out += [(e, [x0 + EDGE_IN, y], [1, 0]) for y in np.linspace(y0 + 25, min(y1, yb) - 25, 4)]
        elif e == "back":                     # behind the printer, left of the Z column
            out += [(e, [x, y1 - EDGE_IN], [0, -1]) for x in np.linspace(x0 + 25, 200 - A.COMBO_W / 2, 5)]
        elif e == "corner":
            out.append((e, [x0 + 40, y0 + 40], [np.sqrt(0.5), np.sqrt(0.5)]))
    return out


def level_pose(arm, lay, boxes, edge, pc, nc, seeds=6):
    """Flattest, most comfortable level grasp at one spot, or None."""
    M = combo_M(lay)
    n = M[:3, :3] @ np.r_[nc, 0.0] * 1e3
    p_xy = trimesh.transform_points([[*pc, 0.0]], M)[0][:2]
    radial = np.arctan2(*(p_xy - lay["arm"])[::-1])
    yaws = sorted(YAWS, key=lambda d: abs(np.angle(np.exp(1j * (np.arctan2(n[1], n[0]) + np.radians(d) - radial)))))
    for a in PITCHES:
        ar = np.radians(a)
        up = 0.002 + 0.035 * np.sin(ar) + 0.034 * np.cos(ar)
        p = np.r_[p_xy, B.PLY_T + BED_TOP + up]
        for d in yaws:
            ps = np.arctan2(n[1], n[0]) + np.radians(d)
            z = np.array([np.cos(ar) * np.cos(ps), np.cos(ar) * np.sin(ps), -np.sin(ar)])
            for q in arm.ik(arm_M(lay), p, z, seeds=seeds):
                g = arm.clear(q, lay, boxes)
                if g >= CLEAR:
                    return dict(edge=edge, pitch=a, yaw=d, margin=arm.margin(q), clear=g, q=q, p=p, z=z)
    return None


def above_pose(arm, lay, boxes, seeds=8):
    """From above, at the middle of the bed."""
    (x0, y0, _), (x1, y1, _) = bed_box(lay)
    M = combo_M(lay)
    p = trimesh.transform_points([[(x0 + x1) / 2, (y0 + y1) / 2, (BED_TOP + ABOVE_UP) * 1e3]], M)[0]
    best = None
    for fx in ([1, 0, 0], [0, 1, 0]):
        for q in arm.ik(arm_M(lay), p, np.array([0, 0, -1.0]), x_dir=M[:3, :3] @ np.array(fx, float) * 1e3, seeds=seeds):
            g = arm.clear(q, lay, boxes)
            if g >= CLEAR:
                if best is None or arm.margin(q) > best["margin"]:
                    best = dict(margin=arm.margin(q), clear=g, q=q, p=p)
                break
    return best


def people(lay):
    """How the printer meets people at the E-stop side (+y edge): the screen's distance in from
    that edge and how far it faces away from them, and the same distance for the bed's front."""
    M = combo_M(lay)
    scr = trimesh.transform_points([[274 - A.COMBO_W / 2, A.BASE_D / 2 - 306, 57]], M)[0]
    face = M[:3, :3] @ np.array([0, -1.0, 0]) * 1e3
    bed = trimesh.transform_points([[149 - A.COMBO_W / 2, A.BASE_D / 2 - A.TRAVEL[1], 82]], M)[0]
    return dict(screen_in_from_front_edge_mm=round((B.P2 - scr[1]) * 1e3),
                screen_turned_from_front_deg=round(float(np.degrees(np.arccos(np.clip(face[1], -1, 1))))),
                plate_in_from_front_edge_mm=round((B.P2 - bed[1]) * 1e3))


def evaluate(args):
    """Every spot for one layout: the level grasps that work, the best one, and from above."""
    name, back, with_above = args
    arm = _ARM
    lay = layout(name, back)
    boxes = obstacles(lay)
    rows = []
    for e, pc, nc in spots(lay):
        r = level_pose(arm, lay, boxes, e, pc, nc)
        rows.append(dict(edge=e, spot_mm=[round(v, 1) for v in pc], ok=r is not None,
                         **({} if r is None else dict(pitch=r["pitch"], yaw=r["yaw"], margin=round(r["margin"], 1),
                                                       clear_mm=round(r["clear"] * 1e3, 1),
                                                       q=[round(float(v), 5) for v in r["q"]],
                                                       p=[round(float(v), 5) for v in r["p"]]))))
    good = [r for r in rows if r["ok"]]
    best = max(good, key=lambda r: (-r["pitch"], r["margin"])) if good else None
    ab = above_pose(arm, lay, boxes) if with_above else None
    return dict(layout=name, back_mm=round(back * 1e3), spots=rows, best=best,
                above=None if ab is None else dict(margin=round(ab["margin"], 1), clear_mm=round(ab["clear"] * 1e3, 1),
                                                   q=[round(float(v), 5) for v in ab["q"]], p=[round(float(v), 5) for v in ab["p"]]),
                people=people(lay), turn_deg=lay["turn"], combo_centre_m=[round(float(v), 4) for v in lay["centre"]],
                arm_xy_m=[round(float(v), 4) for v in lay["arm"]], bed=lay["bed"])


def bands(arm=None, step=0.01):
    """How far from J1 each grasp works at bed height on an empty table, the gripper pointing
    straight out from J1: from above, and level (flat, or tipped 10 deg). [first, last] metres."""
    arm = arm or _ARM
    lay = layout("corner", 0.0)
    out = {}
    for mode in ("above", "level-flat", "level"):
        ok = []
        for r in np.arange(0.10, 0.80, step):
            found = False
            for a in ((0.0,) if mode == "level-flat" else PITCHES):
                if mode == "above":
                    p, z = np.array([0, r, B.PLY_T + BED_TOP + ABOVE_UP]), np.array([0, 0, -1.0])
                else:
                    ar = np.radians(a)
                    up = 0.002 + 0.035 * np.sin(ar) + 0.034 * np.cos(ar)
                    p, z = np.array([0, r, B.PLY_T + BED_TOP + up]), np.array([0, np.cos(ar), -np.sin(ar)])
                if any(arm.clear(q, lay, np.zeros((0, 2, 3))) >= CLEAR for q in arm.ik(arm_M(lay), p, z, seeds=6)):
                    found = True
                    break
            if found:
                ok.append(round(float(r), 3))
        out[mode] = [min(ok), max(ok)] if ok else None
    return out


_ARM = None


def _init():
    global _ARM
    _ARM = Arm()


def main():
    backs = [round(0.025 * k, 3) for k in range(1, 15)]
    jobs = [(n, 0.0, True) for n in ("wall", "corner", "people-r")]
    jobs += [("moved", b, False) for b in backs] + [("people", b, False) for b in backs]
    with ProcessPoolExecutor(4, initializer=_init) as ex:
        out = list(ex.map(evaluate, jobs))
    res = {r["layout"]: r for r in out[:3]}
    sweep = {}
    for r in out[3:]:
        sweep.setdefault(r["layout"], []).append((r["back_mm"], sum(s["ok"] for s in r["spots"]), len(r["spots"])))
    final = []
    for name in ("moved", "people"):          # the smallest move that reaches as many spots as any
        most = max(k for _, k, _ in sweep[name])
        final.append((name, next(b for b, k, _ in sweep[name] if k == most) / 1e3, True))
    with ProcessPoolExecutor(2, initializer=_init) as ex:
        for (name, back, _), r in zip(final, ex.map(evaluate, final)):
            r["sweep_back_mm_spots"] = sweep[name]
            r["first_works_back_mm"] = next((b for b, k, _ in sweep[name] if k >= 1), None)
            res[name] = r
    for r in res.values():
        print(r["layout"], r["back_mm"], f"{sum(s['ok'] for s in r['spots'])}/{len(r['spots'])}",
              None if r["best"] is None else {k: r["best"][k] for k in ("edge", "pitch", "yaw", "margin", "clear_mm")},
              "above" if r["above"] else "no above", r["people"])
    _init()
    res["bands_m"] = bands()
    print(res["bands_m"])
    (HERE / "access.json").write_text(json.dumps(res, indent=1) + "\n")
    return res


if __name__ == "__main__":
    main()
