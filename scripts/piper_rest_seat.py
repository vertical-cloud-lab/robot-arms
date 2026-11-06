#!/usr/bin/env python3
"""A printed rest seat that holds the PiPER's J1 at zero while the arm is parked (issue #24).

The seat stands on the table behind the base, under the upper arm (the J2-J3 link). At home
the upper arm sits between two side walls, so J1 can't be turned while the motors are off and
the arm powers up on its J1 zero mark. The walls are only as tall as the arm can clear after a
small J2 lift: their tops are the arm's underside turned up by --lift-deg about the J2 axis
(minus --top-margin), so they slope up away from J2 instead of running parallel to the table.
Under the cradle is a tunnel for the base connector and its two cables (A along the table, B up
to the side), with windows in both sides for B.

Everything is computed from AgileX's URDF meshes (piper_ros, pinned in piper_twin.py), in the
arm's base frame: x forward along J1 = 0, z up, mm, origin on the base's mounting face.

    python piper_rest_seat.py --out docs/issue-24/rest-seat           # STL, 3MF, checks, renders
    python piper_rest_seat.py --base-z-mm 10 --out /tmp/seat          # arm on a 10 mm plate

Runs on the runner or a laptop (numpy, opencv, trimesh, manifold3d); it never talks to the arm.
"""
import argparse
import json
import math
import os
import sys

import cv2
import numpy as np
import trimesh
from manifold3d import Manifold

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import piper_twin as pt  # noqa: E402

Q_HOME = [0, 0, 0, 0, 0, 0]
# Joints read with the motors off after a park (2026-10-09, #19/#24): J2 and J3 drop about
# 2 deg onto their stops. J1 is set to 0 here because holding it there is the point of the seat.
Q_REST = [0, -1.96, 2.15, 1.38, 23.34, 64.29]
BEAM_HALF = 20.5  # half-width of the upper arm's straight section (link2 local z), mm
ARM_LINKS = ["link1", "link2", "link3", "link4", "link5", "link6", "gripper_base", "link7",
             "link8"]
SEAT_RGB = (240, 140, 40)


# ---------------------------------------------------------------- arm geometry
def full_meshes():
    """Full-resolution URDF meshes in mm (downloaded once, like piper_twin.load_meshes)."""
    import urllib.request
    out = os.path.join(pt.CACHE, pt.MESH_SHA[:7], "full")
    os.makedirs(out, exist_ok=True)
    meshes = {}
    for name in pt.MESHES:
        stl = os.path.join(out, f"{name}.STL")
        if not os.path.exists(stl):
            urllib.request.urlretrieve(pt.MESH_URL.format(sha=pt.MESH_SHA, name=name), stl)
        m = trimesh.load(stl, force="mesh")
        m.apply_scale(1000.0)
        meshes[name] = m
    return meshes


def surface_points(meshes, per_mm2=0.5, seed=0):
    """Vertices plus random surface samples of every link, in link frames."""
    rng = np.random.default_rng(seed)
    pts = {}
    for name, m in meshes.items():
        n = int(m.area * per_mm2)
        s, _ = trimesh.sample.sample_surface(m, n, seed=int(rng.integers(1 << 31)))
        pts[name] = np.vstack([m.vertices, s])
    return pts


def posed(pts, q, links=ARM_LINKS):
    T = pt.link_poses(q)
    return np.vstack([pts[n] @ T[n][:3, :3].T + T[n][:3, 3] for n in links])


def binned_min(x, z, edges):
    """Min z in each x bin (inf where empty)."""
    idx = np.digitize(x, edges) - 1
    out = np.full(len(edges) - 1, np.inf)
    ok = (idx >= 0) & (idx < len(out))
    np.minimum.at(out, idx[ok], z[ok])
    return out


def arm_profiles(pts, a):
    """Per-station limits (1 mm stations along x behind the base) that shape the seat."""
    xs = np.arange(-260.0, -40.0, 1.0)
    edges = np.append(xs - 0.5, xs[-1] + 0.5)
    q_lift = [0, a.lift_deg, 0, *Q_REST[3:]]

    def under(q, ymax, links=("link2", "link3")):
        P = posed(pts, q, links)
        k = np.abs(P[:, 1]) <= ymax
        return binned_min(P[k, 0], P[k, 2], edges)

    y_in = BEAM_HALF + a.side_clear
    rest = under(Q_REST, y_in)              # underside of the beam at the power-off rest
    home = under(Q_HOME, y_in)              # ... at home, motors on
    # What the walls must stay under once J2 is at lift_deg, wherever J1 then points: every
    # point of the upper arm and forearm at horizontal radius r from J1 passes over radius r.
    P = posed(pts, q_lift, ("link1", "link2", "link3"))
    r = np.hypot(P[:, 0], P[:, 1])
    redges = np.arange(0.0, 400.0, 1.0)
    u_r = binned_min(r, P[:, 2], redges)
    u_r = np.minimum.accumulate(u_r[::-1])[::-1]  # conservative: min over r' >= r
    # The wall at station x spans radii hypot(x, y) for y in the wall; take the worst one.
    lift = np.full_like(xs, np.inf)
    for y in np.linspace(y_in, a.wall_outer, 6):
        rr = np.hypot(xs, y)
        lift = np.minimum(lift, np.interp(rr, redges[:-1] + 0.5, u_r))
    # The hubs at either end are wider than the beam: no wall where any part of the arm wider
    # than the cradle is low enough to touch it, anywhere from the rest pose up to lift_deg.
    hub = np.full_like(xs, np.inf)
    for j2 in np.linspace(Q_REST[1], a.lift_deg, 9):
        P = posed(pts, [0, j2, Q_REST[2] if j2 < 0 else 0, *Q_REST[3:]],
                  ("link1", "link2", "link3"))
        k = np.abs(P[:, 1]) > y_in - 0.5
        hub = np.minimum(hub, binned_min(P[k, 0], P[k, 2], edges))
    return dict(xs=xs, rest=rest, home=home, lift=lift, hub=hub, y_in=y_in)


# ---------------------------------------------------------------- seat geometry
def design(prof, a):
    """Station-wise heights of the deck and walls, in the arm's base frame (mm)."""
    xs, zt = prof["xs"], -a.base_z_mm
    sel = (xs >= a.x_far) & (xs <= a.x_near)
    xs = xs[sel]
    rest, home, lift, hub = (prof[k][sel] for k in ("rest", "home", "lift", "hub"))
    # Deck: a straight line floor_gap under the beam at rest, so it never lifts the arm.
    deck_line = rest - a.floor_gap
    k = np.polyfit(xs, deck_line, 1)
    off = np.max(np.polyval(k, xs) - deck_line)  # shift down until it's under everywhere
    deck = np.polyval(k, xs) - max(off, 0)
    # Walls: the lowest of "clears the arm at lift_deg", "clears the hubs" (less margin) and
    # "max_engage past the beam's underside at rest". The first drops them near J2, where a J2
    # lift raises the arm least; the last keeps them just deep enough everywhere else.
    top = np.minimum(np.minimum(lift, hub) - a.top_margin, rest + a.max_engage)
    # Printed standing on its far (-x) end, a top that rises toward +x would overhang. Keep
    # its slope under 45 deg that way (it's lowered, never raised, so clearances still hold).
    for i in range(1, len(top)):
        top[i] = min(top[i], top[i - 1] + (xs[i] - xs[i - 1]))
    engage = top - rest  # how far the wall rises past the beam's underside at rest
    wall = engage >= a.min_engage
    if not wall.any():
        raise SystemExit("no station leaves room for a wall: lower --min-engage or raise "
                         "--lift-deg")
    w0, w1 = np.flatnonzero(wall)[[0, -1]]
    return dict(xs=xs, zt=zt, deck=deck, top=top, rest=rest, home=home, lift=lift, hub=hub,
                engage=engage, wall_x=(xs[w0], xs[w1]), roof=deck.min() - a.deck_thick)


def simplify_top(xs, top, tol=0.6):
    """A few-segment polyline at or under top (Douglas-Peucker, then pushed down)."""
    keep = [0, len(xs) - 1]

    def rec(i, j):
        if j <= i + 1:
            return
        t = (xs[i + 1:j] - xs[i]) / (xs[j] - xs[i])
        line = top[i] + t * (top[j] - top[i])
        err = line - top[i + 1:j]
        k = int(np.argmax(np.abs(err)))
        if abs(err[k]) > tol:
            keep.append(i + 1 + k)
            rec(i, i + 1 + k)
            rec(i + 1 + k, j)
    rec(0, len(xs) - 1)
    keep = sorted(set(keep))
    px, pz = xs[keep], top[keep].copy()
    over = np.interp(xs, px, pz) - top
    pz -= max(over.max(), 0)  # never above the computed limit
    return px, pz


def hull(points):
    return Manifold.hull_points(np.asarray(points, np.float64))


def loft(xs, profile):
    """Union of convex hulls between consecutive stations; profile(x) -> (K, 2) y-z polygon."""
    parts = []
    for x0, x1 in zip(xs[:-1], xs[1:]):
        p0, p1 = profile(x0), profile(x1)
        parts.append(hull(np.vstack([np.column_stack([np.full(len(p0), x0), p0]),
                                     np.column_stack([np.full(len(p1), x1), p1])])))
    return Manifold.batch_boolean(parts, __import__("manifold3d").OpType.Add)


def box(x0, x1, y0, y1, z0, z1):
    return Manifold.cube([x1 - x0, y1 - y0, z1 - z0]).translate([x0, y0, z0])


def build_seat(d, a):
    """The seat as one manifold, in the arm's base frame."""
    xs, zt, roof = d["xs"], d["zt"], d["roof"]
    x0, x1 = xs[0], xs[-1]
    yi, yo, ti = a.side_clear + BEAM_HALF, a.wall_outer, a.tunnel_half
    deck_k = np.polyfit(xs, d["deck"], 1)

    def deck(x):
        return float(np.polyval(deck_k, x))

    # Body: two tunnel walls and the deck over them, one straight-topped loft.
    body = loft(np.array([x0, x1]), lambda x: np.array(
        [[-yo, zt], [yo, zt], [yo, deck(x)], [-yo, deck(x)]]))
    tunnel = box(x0 - 1, x1 + 1, -ti, ti, zt - 1, roof)
    # Side walls, from the wall's first to last station, with a 45 deg lead-in chamfer on the
    # inner top edge. Their -x ends ramp down at 45 deg so nothing overhangs when printed.
    wx0, wx1 = d["wall_x"]
    px, pz = simplify_top(xs, d["top"])
    sel = (px > wx0) & (px < wx1)
    wxs = np.concatenate([[wx0], px[sel], [wx1]])
    wtop = np.interp(wxs, xs, np.interp(xs, px, pz))
    ramp = max(wtop[0] - deck(wx0), 0.0)  # 45 deg ramp at the far (-x) end
    wxs = np.concatenate([[max(x0, wx0 - ramp)], wxs])
    wtop = np.concatenate([[deck(wxs[0]) + 0.5], wtop])
    cw = a.chamfer

    def wall_prof(x, sgn):
        zd, zw = deck(x) - 0.5, float(np.interp(x, wxs, wtop))
        c = min(cw, max(zw - zd - 0.5, 0.0))
        poly = [[yi, zd], [yo, zd], [yo, zw], [yi + c, zw], [yi, zw - c]]
        poly = [[sgn * y, z] for y, z in poly]
        return np.array(poly if sgn > 0 else poly[::-1])
    walls = [loft(wxs, lambda x, s=s: wall_prof(x, s)) for s in (1, -1)]
    # Feet with screw holes, so the seat can be screwed down where the arm puts it.
    fe = a.foot_out
    feet = [box(x0, x1, yo - 1, yo + fe, zt, zt + a.foot_thick),
            box(x0, x1, -yo - fe, -yo + 1, zt, zt + a.foot_thick)]
    seat = Manifold.batch_boolean([body, *walls, *feet],
                                  __import__("manifold3d").OpType.Add) - tunnel
    cuts = []
    # Teardrop screw holes (point toward +x, which is up when printed on end).
    for xh in (x0 + 12, x1 - 12):
        for yh in (yo + fe / 2 + 0.5, -yo - fe / 2 - 0.5):
            r = a.screw_d / 2
            ang = np.linspace(-np.pi * 0.75, np.pi * 0.75, 28)
            poly = np.column_stack([xh + r * np.cos(ang + np.pi), yh + r * np.sin(ang + np.pi)])
            poly = np.vstack([poly, [[xh + r * math.sqrt(2), yh]]])
            pts3 = np.vstack([np.column_stack([poly, np.full(len(poly), zt - 1)]),
                              np.column_stack([poly, np.full(len(poly), zt + a.foot_thick + 1)])])
            cuts.append(hull(pts3))
    # Cable windows in both tunnel walls, pointed toward +x for the same reason.
    wa, wb = a.window_x
    za, zb = zt + a.window_z[0], min(zt + a.window_z[1], roof - 4)
    h = (zb - za) / 2 * 1.2
    win = np.array([[wa, za], [wb - h, za], [wb, (za + zb) / 2], [wb - h, zb], [wa, zb]])
    for s in (1, -1):
        ys = (ti - 1, yo + 1) if s > 0 else (-yo - 1, -ti + 1)
        pts3 = np.vstack([np.column_stack([win[:, 0], np.full(len(win), y), win[:, 1]])
                          for y in ys])
        cuts.append(hull(pts3))
    if cuts:
        seat = seat - Manifold.batch_boolean(cuts, __import__("manifold3d").OpType.Add)
    return seat


def to_trimesh(man):
    m = man.to_mesh()
    return trimesh.Trimesh(np.asarray(m.vert_properties)[:, :3], np.asarray(m.tri_verts),
                           process=True)


def print_pose(mesh):
    """Stand the seat on its far (-x) end: base-frame +x becomes print +z."""
    R = np.array([[0, 0, -1], [0, 1, 0], [1, 0, 0]], float)  # x->z, z->-x
    T = np.eye(4)
    T[:3, :3] = R
    m = mesh.copy()
    m.apply_transform(T)
    lo, hi = m.bounds
    m.apply_translation([-(lo[0] + hi[0]) / 2, -(lo[1] + hi[1]) / 2, -lo[2]])
    return m


def overhangs(m, limit_deg=45.0, bed_tol=0.2):
    """Area (mm^2) of downward faces steeper than limit_deg from vertical, off the bed."""
    n = m.face_normals
    cen = m.triangles_center
    down = n[:, 2] < -math.cos(math.radians(90 - limit_deg)) - 1e-3
    off_bed = cen[:, 2] > bed_tol
    bad = down & off_bed
    worst = 0.0
    if (off_bed & (n[:, 2] < 0)).any():
        k = off_bed & (n[:, 2] < 0)
        worst = float(np.degrees(np.arcsin(np.clip(-n[k, 2], 0, 1))).max())
    return float(m.area_faces[bad].sum()), worst


# ---------------------------------------------------------------- checks
class Clearance:
    """Smallest distance (mm, negative = inside) from the arm's surface to the seat."""

    def __init__(self, seat_mesh, pts, links=ARM_LINKS):
        self.seat = seat_mesh
        self.pq = trimesh.proximity.ProximityQuery(seat_mesh)
        self.pts, self.links = pts, links
        lo, hi = seat_mesh.bounds
        self.lo, self.hi = lo - 25, hi + 25

    def __call__(self, q, links=None):
        P = posed(self.pts, q, links or self.links)
        k = np.all((P > self.lo) & (P < self.hi), axis=1)
        if not k.any():
            return 25.0
        sd = self.pq.signed_distance(P[k])  # trimesh: positive inside
        return float(-sd.max())


def run_checks(seat_mesh, pts, d, a):
    sparse = surface_points_sparse(pts, 3)
    clr = Clearance(seat_mesh, sparse)
    out = {}
    out["home"] = clr(Q_HOME)
    out["rest"] = clr(Q_REST)
    # J2 lift from rest with J1 held: nothing may touch on the way up.
    lift = [clr([0, j2, 0 if j2 > 0 else Q_REST[2], *Q_REST[3:]])
            for j2 in np.arange(Q_REST[1], 20.01, 1.0)]
    out["j2_lift_min"] = min(lift)
    # J1 swings once J2 is at lift_deg: how close the arm comes, and over which J1 range.
    sweep = {}
    for label, q in (("folded, J2 at lift_deg", [0, a.lift_deg, 0, *Q_REST[3:]]),
                     ("READY (J2 15, J3 -15, J5 25)", [0, 15, -15, Q_REST[3], 25, Q_REST[5]])):
        sweep[label] = [(float(j1), clr([j1, *q[1:]])) for j1 in np.arange(-150, 150.01, 3)]
    out["j1_sweep"] = {k: {"min_mm": min(v for _, v in vals),
                           "min_at_j1": min(vals, key=lambda t: t[1])[0],
                           "touch_j1": [j for j, v in vals if v < 0]}
                       for k, vals in sweep.items()}
    # J1 play while seated: the beam meets a wall first at the wall's far end.
    out["j1_play_deg"] = math.degrees(math.atan(a.side_clear / abs(d["wall_x"][0])))
    # Lowest J2 at which J1 can swing freely: every point of links 1-3 at radius r must be
    # above the wall top at radius r (the same test that shaped the walls, run backwards).
    wx0, wx1 = d["wall_x"]
    w = (d["xs"] >= wx0) & (d["xs"] <= wx1)
    wr = np.concatenate([np.hypot(d["xs"][w], y) for y in
                         np.linspace(BEAM_HALF + a.side_clear, a.wall_outer, 6)])
    wt = np.tile(d["top"][w], 6)
    redges = np.arange(0.0, 400.0, 1.0)
    j2_free = None
    for j2 in np.arange(0, 20.01, 0.25):
        P = posed(pts, [0, j2, 0, *Q_REST[3:]], ("link1", "link2", "link3"))
        u = binned_min(np.hypot(P[:, 0], P[:, 1]), P[:, 2], redges)
        u = np.minimum.accumulate(u[::-1])[::-1]
        if np.all(np.interp(wr, redges[:-1] + 0.5, u) > wt):
            j2_free = float(j2)
            break
    out["j2_free_deg"] = j2_free
    # Random poses inside the joint limits with the arm above the table and J2 >= lift_deg:
    # how many reach into the seat?
    rng = np.random.default_rng(1)
    lim = np.array([[-150, 150], [a.lift_deg, 180], [-170, 0], [-100, 100], [-70, 70],
                    [-120, 120]], float)
    hit, valid = [], 0
    for _ in range(600):
        q = rng.uniform(lim[:, 0], lim[:, 1])
        P = posed(sparse, q)
        if P[:, 2].min() < -a.base_z_mm + 5:  # through the table: not a pose anyone uses
            continue
        valid += 1
        if clr(q) < 0:
            hit.append([round(float(v), 1) for v in q])
    out["random_poses"] = {"valid": valid, "touch_seat": len(hit), "touching": hit}
    return out


def surface_points_sparse(pts, step=8):
    return {k: v[::step] for k, v in pts.items()}


# ---------------------------------------------------------------- pictures
def render_scene(cam, items, canvas=None, ss=2):
    """Flat-shaded painter's render of several meshes: items = [(V world, F, rgb)]."""
    big = cam.scaled(cam.width * ss, cam.height * ss)
    R, t = big.R(), big.tvec
    polys, depth, cols = [], [], []
    up_cam = R @ np.array([0.0, 0.0, 1.0])
    for V, F, rgb in items:
        vc = V @ R.T + t
        tri = vc[F]
        n = np.cross(tri[:, 1] - tri[:, 0], tri[:, 2] - tri[:, 0])
        nn = np.linalg.norm(n, axis=1)
        ok = nn > 1e-9
        n[ok] /= nn[ok, None]
        cen = tri.mean(1)
        keep = ok & ((n * cen).sum(1) < 0) & (tri[:, :, 2].min(1) > 1.0)
        if not keep.any():
            continue
        polys.append(big.project(V).reshape(-1, 2)[F[keep]])
        depth.append(cen[keep, 2])
        view = -cen[keep] / np.linalg.norm(cen[keep], axis=1, keepdims=True)
        lam = np.clip((n[keep] * view).sum(1), 0, 1)
        top = np.clip(n[keep] @ up_cam, 0, 1)
        shade = 0.30 + 0.55 * lam + 0.25 * top
        cols.append(np.clip(shade[:, None] * np.array(rgb[::-1], float), 0, 255))
    if canvas is None:
        img = np.full((big.height, big.width, 3), 246, np.uint8)
    else:
        img = cv2.resize(canvas, (big.width, big.height), interpolation=cv2.INTER_LINEAR)
    if polys:
        polys, depth, cols = np.concatenate(polys), np.concatenate(depth), np.concatenate(cols)
        for i in np.argsort(-depth):
            cv2.fillConvexPoly(img, np.round(polys[i] * 16).astype(np.int32),
                               cols[i].astype(np.uint8).tolist(), cv2.LINE_8, shift=4)
    return cv2.resize(img, (cam.width, cam.height), interpolation=cv2.INTER_AREA)


def arm_items(dec, q, rgb=pt.TWIN_RGB):
    T = pt.link_poses(q)
    return [(v @ T[n][:3, :3].T + T[n][:3, 3], f, rgb) for n, (v, f) in dec.items()]


def draw_table(img, cam, zt, extent=(-420, 260, -260, 260), step=50):
    x0, x1, y0, y1 = extent
    for x in range(x0, x1 + 1, step):
        uv = np.round(cam.project([[x, y0, zt], [x, y1, zt]])).astype(int)
        cv2.line(img, tuple(uv[0]), tuple(uv[1]), (215, 215, 215), 1, cv2.LINE_AA)
    for y in range(y0, y1 + 1, step):
        uv = np.round(cam.project([[x0, y, zt], [x1, y, zt]])).astype(int)
        cv2.line(img, tuple(uv[0]), tuple(uv[1]), (215, 215, 215), 1, cv2.LINE_AA)


def side_view(d, a, path):
    """Side elevation (from the room side, -y): beam underside at rest / home / lift_deg,
    the wall-top limits and the walls as built."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    xs = d["xs"]
    fig, ax = plt.subplots(figsize=(9, 4.2), dpi=130)
    ax.fill_between(xs, d["zt"], d["deck"], color="#f08c28", alpha=0.25, lw=0,
                    label="deck (tunnel under it)")
    wx0, wx1 = d["wall_x"]
    w = (xs >= wx0) & (xs <= wx1)
    ax.fill_between(xs[w], d["deck"][w], d["top"][w], color="#f08c28", alpha=0.85, lw=0,
                    label="side walls")
    ax.plot(xs, d["rest"], color="#1f4e79", lw=2, label="beam underside, power-off rest "
            f"(J2 {Q_REST[1]:.2f}°)")
    ax.plot(xs, d["home"], color="#1f77b4", lw=1.5, ls="--", label="beam underside, home "
            "(J2 0°)")
    ax.plot(xs, np.minimum(d["lift"], d["hub"]), color="#7f7f7f", lw=1.2, ls=":",
            label=f"lowest arm point once J2 = {a.lift_deg:g}° (any J1)")
    ax.axhline(d["zt"], color="k", lw=1)
    ax.set_xlim(xs[0] - 5, xs[-1] + 40)
    ax.set_ylim(d["zt"] + 60, np.nanmax(d["home"][np.isfinite(d["home"])]) + 30)
    ax.set_xlabel("x behind J1 (mm; J1 axis is at 0, the base's back face at -55)")
    ax.set_ylabel("height above the arm's\nmounting face (mm)")
    ax.set_title("Rest seat, side view: the wall tops follow the arm, and dip near J2 "
                 f"so it clears them by J2 = {a.lift_deg:g}°", fontsize=10)
    ax.legend(loc="upper left", fontsize=7.5, frameon=False)
    ax.grid(alpha=0.25)
    fig.tight_layout()
    fig.savefig(path)
    plt.close(fig)


def end_view(seat_mesh, pts, d, a, path):
    """Cross-sections at two stations, with the beam's section at rest and home."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    wx0, wx1 = d["wall_x"]
    stations = [round(wx0 + 8), round((wx0 + wx1) / 2), round(wx1 - 8)]
    fig, axs = plt.subplots(1, len(stations), figsize=(10, 4.2), dpi=130, sharey=True)
    for ax, xs_ in zip(axs, stations):
        sec = seat_mesh.section(plane_origin=[xs_, 0, 0], plane_normal=[1, 0, 0])
        if sec is not None:
            for ent in sec.discrete:
                ax.fill(ent[:, 1], ent[:, 2], color="#f08c28", alpha=0.85, lw=0)
        for q, col, lab in ((Q_REST, "#1f4e79", "beam at rest"), (Q_HOME, "#1f77b4", "home")):
            P = posed(pts, q, ("link2",))
            k = np.abs(P[:, 0] - xs_) < 0.6
            ax.scatter(P[k, 1], P[k, 2], s=0.4, color=col, label=lab)
        ax.axhline(d["zt"], color="k", lw=1)
        ax.set_title(f"x = {xs_} mm", fontsize=9)
        ax.set_aspect("equal")
        ax.set_xlim(-a.wall_outer - a.foot_out - 4, a.wall_outer + a.foot_out + 4)
        ax.grid(alpha=0.25)
        ax.set_xlabel("y (mm)")
    axs[0].set_ylabel("z (mm)")
    axs[0].legend(loc="lower center", fontsize=7, markerscale=12, frameon=False)
    fig.suptitle("Rest seat cross-sections (looking along the arm toward the base)",
                 fontsize=10)
    fig.tight_layout()
    fig.savefig(path)
    plt.close(fig)


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--out", required=True, help="output directory")
    ap.add_argument("--base-z-mm", type=float, default=0.0,
                    help="height of the arm's mounting face above the table the seat stands "
                         "on (0 = the arm sits straight on the table)")
    ap.add_argument("--side-clear", type=float, default=1.5,
                    help="gap from each wall to the side of the beam at J1 = 0")
    ap.add_argument("--lift-deg", type=float, default=8.0,
                    help="J2 angle by which the arm must clear the walls for any J1")
    ap.add_argument("--top-margin", type=float, default=2.0,
                    help="wall tops stay this far under the arm at --lift-deg")
    ap.add_argument("--floor-gap", type=float, default=4.0,
                    help="deck to beam underside at the power-off rest pose")
    ap.add_argument("--min-engage", type=float, default=8.0,
                    help="walls only where they rise this far past the beam's underside")
    ap.add_argument("--max-engage", type=float, default=16.0,
                    help="walls rise at most this far past the beam's underside at rest")
    ap.add_argument("--x-near", type=float, default=-80.0, help="seat end nearest the base")
    ap.add_argument("--x-far", type=float, default=-180.0, help="seat end nearest the elbow")
    ap.add_argument("--wall-outer", type=float, default=32.0, help="outer face of the walls, y")
    ap.add_argument("--tunnel-half", type=float, default=26.0,
                    help="half-width of the cable tunnel")
    ap.add_argument("--deck-thick", type=float, default=5.0)
    ap.add_argument("--chamfer", type=float, default=3.0, help="lead-in on the walls' inner tops")
    ap.add_argument("--foot-out", type=float, default=16.0)
    ap.add_argument("--foot-thick", type=float, default=6.0)
    ap.add_argument("--screw-d", type=float, default=4.6, help="hole for #8 / M4 wood screws")
    ap.add_argument("--window-x", type=float, nargs=2, default=(-148.0, -100.0))
    ap.add_argument("--window-z", type=float, nargs=2, default=(14.0, 70.0),
                    help="window height range above the table")
    ap.add_argument("--no-checks", action="store_true")
    ap.add_argument("--no-render", action="store_true")
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)

    meshes = full_meshes()
    pts = surface_points(meshes)
    prof = arm_profiles(pts, a)
    d = design(prof, a)
    seat = build_seat(d, a)
    sm = to_trimesh(seat)
    assert sm.is_watertight and sm.is_volume, "seat mesh is not a closed solid"
    sm.export(os.path.join(a.out, "piper_rest_seat_arm_frame.stl"))
    pm = print_pose(sm)
    pm.export(os.path.join(a.out, "piper_rest_seat.stl"))
    pm.export(os.path.join(a.out, "piper_rest_seat.3mf"))
    area, worst = overhangs(pm)

    wx0, wx1 = d["wall_x"]
    st = lambda x: int(np.argmin(np.abs(d["xs"] - x)))  # noqa: E731
    summary = {
        "params": {k: v for k, v in vars(a).items() if k not in ("out",)},
        "size_mm": {"x": float(np.ptp(sm.vertices[:, 0])), "y": float(np.ptp(sm.vertices[:, 1])),
                    "z": float(np.ptp(sm.vertices[:, 2]))},
        "print": {"standing_on": "far (-x) end, nothing else touches the bed",
                  "height_mm": float(pm.bounds[1, 2]),
                  "footprint_mm": [float(v) for v in np.ptp(pm.vertices[:, :2], axis=0)],
                  "overhang_area_mm2_over_45deg": area,
                  "steepest_downward_face_deg_from_vertical": 90 - worst if worst else 90.0,
                  "volume_cm3": float(pm.volume / 1000)},
        "walls": {"x_mm": [float(wx0), float(wx1)],
                  "inner_y_mm": BEAM_HALF + a.side_clear,
                  "rise_past_beam_at_rest_mm": [round(float(d["engage"][st(x)]), 1)
                                                for x in (wx0, wx1)],
                  "top_above_table_mm": [round(float(d["top"][st(x)] - d["zt"]), 1)
                                         for x in (wx0, wx1)],
                  "top_slope_deg_up_toward_elbow": round(math.degrees(math.atan2(
                      d["top"][st(wx0)] - d["top"][st(wx1)], wx1 - wx0)), 1),
                  "beam_underside_slope_deg_at_rest": round(math.degrees(math.atan2(
                      d["rest"][st(wx0)] - d["rest"][st(wx1)], wx1 - wx0)), 1)},
        "deck": {"gap_to_beam_at_rest_mm": round(float((d["rest"] - d["deck"]).min()), 1),
                 "gap_to_beam_at_home_mm": round(float((d["home"] - d["deck"]).min()), 1),
                 "tunnel_mm": {"width": 2 * a.tunnel_half,
                               "height": round(float(d["roof"] - d["zt"]), 1)}},
        "measure_before_printing": {
            "what": "table to the underside of the upper arm, arm at home (J2 = 0), "
                    "at x = -150 mm (about the middle of the AgileX label)",
            "model_mm": round(float(d["home"][st(-150)] - d["zt"]), 1)},
    }
    if not a.no_checks:
        summary["checks"] = run_checks(sm, pts, d, a)
    json.dump(summary, open(os.path.join(a.out, "summary.json"), "w"), indent=1)
    print(json.dumps(summary, indent=1))

    if a.no_render:
        return
    side_view(d, a, os.path.join(a.out, "side_view.png"))
    end_view(sm, pts, d, a, os.path.join(a.out, "sections.png"))
    dec = pt.load_meshes()
    seat_item = [(np.asarray(sm.vertices), np.asarray(sm.faces), SEAT_RGB)]
    views = [("three-quarter", pt.virtual_camera(1100, 760, 40, (-560, -500, 360),
                                                 (-100, 0, 90))),
             ("low side view", pt.virtual_camera(1100, 760, 44, (-140, -520, 95),
                                                 (-120, 0, 95)))]
    tiles = []
    for name, cam in views:
        img = np.full((cam.height, cam.width, 3), 246, np.uint8)
        draw_table(img, cam, d["zt"])
        img = render_scene(cam, arm_items(dec, Q_REST) + seat_item, img)
        pt.put_text(img, f"{name}: arm parked (J2 {Q_REST[1]}, J3 {Q_REST[2]}), "
                         "seat in orange", (10, 26), (40, 40, 40), box=(246, 246, 246))
        tiles.append(img)
    cv2.imwrite(os.path.join(a.out, "seat_with_arm.jpg"), np.hstack(tiles),
                [cv2.IMWRITE_JPEG_QUALITY, 90])
    cam = pt.virtual_camera(900, 760, 36, (-330, -380, 330), (-150, 0, 40))
    img = np.full((cam.height, cam.width, 3), 246, np.uint8)
    draw_table(img, cam, d["zt"])
    img = render_scene(cam, seat_item, img)
    pt.put_text(img, "seat alone (base is to the right)", (10, 26), (40, 40, 40),
                box=(246, 246, 246))
    pcam = pt.virtual_camera(700, 760, 34, (300, -330, 260), (0, 0, 50))
    pimg = np.full((pcam.height, pcam.width, 3), 246, np.uint8)
    draw_table(pimg, pcam, 0, extent=(-120, 120, -120, 120), step=20)
    pimg = render_scene(pcam, [(np.asarray(pm.vertices), np.asarray(pm.faces), SEAT_RGB)],
                        pimg)
    pt.put_text(pimg, "as printed: on its far end, no supports", (10, 26), (40, 40, 40),
                box=(246, 246, 246))
    cv2.imwrite(os.path.join(a.out, "seat_alone_and_print.jpg"), np.hstack([img, pimg]),
                [cv2.IMWRITE_JPEG_QUALITY, 90])
    animate(dec, seat_item, d, a, os.path.join(a.out, "lift_and_swing.mp4"))


def animate(dec, seat_item, d, a, path):
    """Park -> lift J2 -> swing J1 -> back -> park, from two angles."""
    import imageio.v2 as imageio
    keys = [(0.0, Q_REST), (1.0, [0, 0, 0, *Q_REST[3:]]),
            (2.4, [0, a.lift_deg + 2, 0, *Q_REST[3:]]),
            (4.4, [60, a.lift_deg + 2, 0, *Q_REST[3:]]),
            (6.4, [-60, a.lift_deg + 2, 0, *Q_REST[3:]]),
            (7.8, [0, a.lift_deg + 2, 0, *Q_REST[3:]]),
            (8.8, [0, 15, -15, Q_REST[3], 25, Q_REST[5]]),
            (10.0, [0, 15, -15, Q_REST[3], 25, Q_REST[5]]),
            (11.4, [0, 0, 0, *Q_REST[3:]]), (12.4, Q_REST), (13.0, Q_REST)]
    ts = np.array([k[0] for k in keys])
    qs = np.array([k[1] for k in keys], float)
    cams = [pt.virtual_camera(640, 480, 46, (-600, -560, 420), (-60, 0, 110)),
            pt.virtual_camera(640, 480, 48, (-140, -520, 95), (-120, 0, 95))]
    w = imageio.get_writer(path, fps=15, codec="libx264", quality=8, macro_block_size=8)
    grounds = []
    for cam in cams:
        g = np.full((cam.height, cam.width, 3), 246, np.uint8)
        draw_table(g, cam, d["zt"])
        grounds.append(g)
    for t in np.arange(0, ts[-1], 1 / 15):
        q = [float(np.interp(t, ts, qs[:, j])) for j in range(6)]
        tiles = [render_scene(c, arm_items(dec, q) + seat_item, g.copy(), ss=1)
                 for c, g in zip(cams, grounds)]
        frame = np.hstack(tiles)
        bar = np.full((40, frame.shape[1], 3), 30, np.uint8)
        pt.put_text(bar, f"DIGITAL TWIN (simulated)  t={t:4.1f}s  J1 {q[0]:6.1f}  J2 {q[1]:5.1f}"
                         f"  J3 {q[2]:6.1f}", (10, 27), (255, 255, 255), scale=0.6, box=None)
        w.append_data(np.vstack([bar, frame])[:, :, ::-1])
    w.close()
    pt.mp4_to_gif(path, path.replace(".mp4", ".gif"), speed=1.5, width=960)


if __name__ == "__main__":
    main()
