"""The PiPER table as of 23 Oct 2026, its reach, and two layouts for the three fixed cameras.

    python build.py         # results.json, cameras-*.json, models/*.stl, reach.npz

The table is the one in Joshua's photo on PR #9: the 48 x 48 in plywood on new wooden legs, the
PVC cube from #38 screwed to its edge, the A1 mini and its AMS lite along the block wall, a power
strip down that side, and the POWERTEC magnetic switch on the front-right leg. The PVC frame and
its cloth come from ../camera-bar/build.py.

World coordinates follow the arm: origin at the plywood's centre, on the table top under it; x is
the way the arm faces at J1 = 0, which is toward the block wall; y points to the front (the open
side you stand at in the photo); z is up. So -x is the right-hand side and -y is the door. Metres.
The STLs are in mm, each in its print orientation. cameras-*.json are in the arm's frame (mm,
origin on J1 at the top of the plywood), the format piper_twin.py reads (#24).

Two layouts:
  edges    front and right cameras on posts at the middle of those edges, top camera at the
           middle of a crossbar across the top, looking straight down
  corners  the same posts in the front-right and back-right corners, the top camera on the
           middle of the left (wall) top rail, looking down and in
Every camera uses the same printed head, which clamps onto 3/4 in PVC: a post for the ground
cameras, the crossbar or a top rail for the top camera.
"""

import importlib.util
import json
import sys
from pathlib import Path

import numpy as np
import trimesh
from scipy import ndimage
from shapely.geometry import Polygon
from trimesh.creation import box, cylinder

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE.parent))
from piper_fk import Piper, fk_points, sample_joints  # noqa: E402

_spec = importlib.util.spec_from_file_location("camera_bar", HERE.parent / "camera-bar/build.py")
CB = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(CB)

IN = CB.IN
H, R, Z_BOT, Z_TOP = CB.H, CB.R, CB.Z_BOT, CB.Z_TOP
PLY, PLY_T = CB.PLY, CB.PLY_T
P2 = PLY / 2
along, beam, T = CB.along, CB.beam, CB.T

# ------------------------------------------------------------------ table (photo, PR #9, 23 Oct)
FLOOR = -0.74                       # floor below the plywood's underside (assumed: 30 in to the top)
LEG, LEG_IN = 0.038, 0.06           # 2x2 legs (1.5 in), inset from the plywood's edge
APRON_H = 0.064                     # 2x3 on edge under the plywood
BRACE = (0.019, 0.038)              # 1x2 X-braces on every side
A1 = dict(xy=(0.40, 0.36), base=(0.315, 0.347), h=0.365)   # A1 mini: base centre, depth (x) x width (y)
AMS = dict(xy=(0.44, -0.04), size=(0.22, 0.30), h=0.40)    # AMS lite stand, beside it along the wall
STRIP = dict(x=P2 - 0.03, len=1.10, w=0.045, h=0.032)      # power strip along the wall side, on the plywood
SWITCH = (0.090, 0.110, 0.140)      # POWERTEC magnetic switch, on the front-right leg

# colours
PRINT_C = {"front": (0.86, 0.22, 0.27), "right": (0.13, 0.62, 0.31), "top": (0.98, 0.65, 0.10)}
REACH_C = (0.16, 0.42, 0.90)
WOOD, PLYC, PVC = (0.85, 0.72, 0.52), (0.89, 0.82, 0.68), (0.96, 0.96, 0.94)
CLOTH = (0.93, 0.90, 0.82)
DARK, GREY, WHITE = (0.12, 0.12, 0.13), (0.45, 0.46, 0.48), (0.93, 0.93, 0.92)
PART = (0.20, 0.20, 0.22)           # printed fixtures, black PETG

# ------------------------------------------------------------------ camera (Camera Module 3 Wide)
CAM_W, CAM_H, CAM_F = CB.CAM_W, CB.CAM_H, CB.CAM_F        # 4608 x 2592 px, f = 1964 px
HFOV = 2 * np.degrees(np.arctan(CAM_W / 2 / CAM_F))
VFOV = 2 * np.degrees(np.arctan(CAM_H / 2 / CAM_F))

# ------------------------------------------------------------------ printed parts (mm)
PIPE_OD = 26.67                     # 3/4 in Sch 40
BORE = PIPE_OD + 0.5
RING_T, RING_L = 5.0, 18.0          # clamp wall, length along the pipe
RO = BORE / 2 + RING_T
EAR_W, EAR_T, SPLIT = 8.0, 6.0, 1.0  # bolt ears, and the gap left between body and cap
M3, M4, PIN, M2_TAP, SCREW8 = 3.4, 4.4, 2.2, 1.8, 4.5
TAB_T = 5.0                         # hinge plates
PIVOT_AT = RO + 16.0                # pivot from the pipe's axis
DISC = 16.0                         # hinge disc radius
INDEX_R, INDEX_STEP, INDEX_MAX = 12.0, 15, 45   # index holes for the tilt pin, every 15 deg
PLATE = (3.0, 32.0, 34.0)           # camera plate: thickness, width, height
PLATE_AT = 22.0                     # plate's back face, from the pivot
STANDOFF = 3.0
LENS_FWD = PLATE_AT + PLATE[0] + STANDOFF + 1.0 + 6.0   # lens front from the pivot, along the view
LENS_UP = 2.5                       # lens centre above the board centre
FOOT, FOOT_T, SOCKET_H = 56.0, 5.0, 32.0
POST_LEN = 400.0                    # 3/4 in PVC posts, from the enclosure's off-cuts
CROSS_Z = PIPE_OD + 4.0             # crossbar axis above the rail's axis in the cross clamp


def _cyl(r, h, axis="z", center=(0, 0, 0), sections=64):
    m = cylinder(radius=r, height=h, sections=sections)
    if axis == "x":
        m.apply_transform(trimesh.transformations.rotation_matrix(np.pi / 2, (0, 1, 0)))
    elif axis == "y":
        m.apply_transform(trimesh.transformations.rotation_matrix(np.pi / 2, (1, 0, 0)))
    return m.apply_translation(center)


def _box(lo, hi):
    lo, hi = np.asarray(lo, float), np.asarray(hi, float)
    return box(hi - lo).apply_translation((lo + hi) / 2)


def _cut(body, cuts):
    return body.difference(trimesh.boolean.union(cuts)) if len(cuts) > 1 else body.difference(cuts[0])


def half_ring(side):
    """Half of a 3/4 in PVC clamp, pipe axis on z, split on the y-z plane. side=+1 keeps x > 0."""
    ring = _cyl(RO, RING_L).difference(_cyl(BORE / 2, RING_L + 2))
    keep = _box([0 if side > 0 else -RO - 1, -RO - EAR_W - 1, -RING_L], [RO + 1 if side > 0 else 0, RO + EAR_W + 1, RING_L])
    ring = ring.intersection(keep)
    ears = []
    for s in (-1, 1):
        lo = [0 if side > 0 else -EAR_T, s * (BORE / 2 + 0.5) if s > 0 else -(RO + EAR_W), -RING_L / 2]
        hi = [EAR_T if side > 0 else 0, RO + EAR_W if s > 0 else -(BORE / 2 + 0.5), RING_L / 2]
        ears.append(_box(lo, hi))
    body = trimesh.boolean.union([ring] + ears)
    cuts = [_cyl(BORE / 2, RING_L + 2)]
    for s in (-1, 1):
        cuts.append(_cyl(M3 / 2, 40, "x", (0, s * (RO + EAR_W / 2 - 0.5), 0), 24))
    body = _cut(body, cuts)
    return body.apply_translation([side * SPLIT / 2, 0, 0])


def clamp_cap():
    """The loose half: bolts to a head clamp or a cross clamp. A #6 screw through it pins the pipe."""
    cap = half_ring(-1)
    return _cut(cap, [_cyl(1.8, 20, "x", (-RO, 0, 0), 24)])


def head_clamp():
    """Half ring plus the hinge plate, which sticks out along +x. Hinge axis is y, plate at y in [-TAB_T, 0]."""
    body = half_ring(+1)
    neck = _box([RO - 2, -TAB_T, -RING_L / 2], [PIVOT_AT, 0, RING_L / 2])
    disc = _cyl(DISC, TAB_T, "y", (PIVOT_AT, -TAB_T / 2, 0))
    body = trimesh.boolean.union([body, neck, disc])
    cuts = [_cyl(M4 / 2, 20, "y", (PIVOT_AT, 0, 0), 32), _cyl(BORE / 2, RING_L + 2)]
    for a in range(-INDEX_MAX, INDEX_MAX + 1, INDEX_STEP):      # tilt index, 0 deg straight up from the pivot
        t = np.radians(a)
        cuts.append(_cyl(PIN / 2, 20, "y", (PIVOT_AT + INDEX_R * np.sin(t), 0, INDEX_R * np.cos(t)), 20))
    return _cut(body, cuts)


def head_cradle():
    """Hinge plate (y in [0, TAB_T]) and the camera plate, local origin on the pivot, view along +x.
    The board screws to standoffs on the plate's front, landscape or portrait (8 holes)."""
    disc = _cyl(DISC, TAB_T, "y", (0, TAB_T / 2, 0))
    arm = _box([0, 0, -8], [PLATE_AT + 0.5, TAB_T, 8])
    pt, pw, ph = PLATE
    plate = _box([PLATE_AT, -pw / 2, LENS_UP - ph / 2], [PLATE_AT + pt, pw / 2, LENS_UP + ph / 2])
    lens = np.array([0.0, LENS_UP])
    holes = [(s * 10.5, 7.5) for s in (-1, 1)] + [(s * 10.5, -5.0) for s in (-1, 1)]   # from the lens centre
    holes += [(-v, u) for u, v in holes]                                                  # portrait
    posts = [_cyl(2.6, STANDOFF, "x", (PLATE_AT + pt + STANDOFF / 2, lens[0] + u, lens[1] + v), 24) for u, v in holes]
    body = trimesh.boolean.union([disc, arm, plate] + posts)
    cuts = [_cyl(M4 / 2, 20, "y", (0, 0, 0), 32), _cyl(PIN / 2, 20, "y", (0, 0, INDEX_R), 20)]
    cuts += [_cyl(M2_TAP / 2, 2 * (pt + STANDOFF), "x", (PLATE_AT + pt, lens[0] + u, lens[1] + v), 16) for u, v in holes]
    cuts.append(_box([PLATE_AT - 1, -9, LENS_UP - ph / 2 - 1], [PLATE_AT + pt + 1, 9, LENS_UP - ph / 2 + 4]))  # ribbon notch
    return _cut(body, cuts)


def ground_foot():
    """Square foot with a socket for the post. Its edges go flush with the plywood's edges."""
    base = _box([-FOOT / 2, -FOOT / 2, 0], [FOOT / 2, FOOT / 2, FOOT_T])
    sock = _cyl(BORE / 2 + 4, SOCKET_H, center=(0, 0, SOCKET_H / 2))
    body = trimesh.boolean.union([base, sock])
    cuts = [_cyl(BORE / 2, SOCKET_H, center=(0, 0, FOOT_T + SOCKET_H / 2)),
            _cyl(1.8, 30, "x", (BORE / 2 + 2, 0, FOOT_T + SOCKET_H / 2 + 4), 20)]
    for sx in (-1, 1):
        for sy in (-1, 1):
            c = (sx * 20.5, sy * 20.5)
            cuts.append(_cyl(SCREW8 / 2, 20, center=(c[0], c[1], 0), sections=24))
            cone = trimesh.creation.cone(radius=4.6, height=4.6, sections=24)
            cone.apply_transform(trimesh.transformations.rotation_matrix(np.pi, (1, 0, 0)))
            cuts.append(cone.apply_translation([c[0], c[1], FOOT_T + 0.01]))
    return _cut(body, cuts)


def cross_clamp():
    """Holds the crossbar on top of a top rail. Rail on y through a half ring (cap below), crossbar
    through a closed bore on x above it. Origin on the rail's axis."""
    upper = half_ring(+1)
    upper.apply_transform(trimesh.transformations.rotation_matrix(-np.pi / 2, (0, 1, 0)))   # split plane -> x-y
    upper.apply_transform(trimesh.transformations.rotation_matrix(np.pi / 2, (1, 0, 0)))    # pipe axis -> y
    block = _box([-20, -RING_L / 2, RO - 3], [20, RING_L / 2, CROSS_Z + RO])
    sleeve = _cyl(RO, 40, "x", (0, 0, CROSS_Z))
    body = trimesh.boolean.union([upper, block, sleeve])
    cuts = [_cyl(BORE / 2, 60, "x", (0, 0, CROSS_Z)), _cyl(BORE / 2, RING_L + 2, "y"),
            _cyl(1.8, 30, "z", (12, 0, CROSS_Z + RO), 20)]
    return _cut(body, cuts)


# ------------------------------------------------------------------ placing a head
def head_pose(axis_pt, a, r, tilt_deg=0.0):
    """World transforms (metres) for a head whose clamp sits on a pipe through axis_pt along a,
    with the hinge plate pointing along r, and the cradle tilted tilt_deg about the hinge (positive
    tips the view toward -a, i.e. down on a vertical post). Returns (clamp_T, cradle_T, lens, view, up)."""
    a, r = np.asarray(a, float) / np.linalg.norm(a), np.asarray(r, float) / np.linalg.norm(r)
    y = np.cross(a, r)
    Rc = np.column_stack([r, y, a])
    clamp_T = T(Rc, axis_pt)
    t = np.radians(tilt_deg)
    Rt = trimesh.transformations.rotation_matrix(t, (0, 1, 0))[:3, :3]     # about the hinge (local y)
    piv = np.asarray(axis_pt) + r * PIVOT_AT / 1e3
    cradle_T = T(Rc @ Rt, piv)
    view = Rc @ Rt @ np.array([1.0, 0, 0])
    up = Rc @ Rt @ np.array([0, 0, 1.0])
    lens = piv + Rc @ Rt @ np.array([LENS_FWD, 0, LENS_UP]) / 1e3
    return clamp_T, cradle_T, lens, view, up


def mm_to_world(mesh, M):
    return mesh.copy().apply_scale(1e-3).apply_transform(M)


GROUND_IN = FOOT / 2 / 1e3            # post axis from each flush edge
POST_TOP = PLY_T + FOOT_T / 1e3 + POST_LEN / 1e3
CLAMP_Z = POST_TOP - RING_L / 2e3     # head clamp at the top of the post


def layouts():
    """Camera layouts: name -> {camera: dict(kind, ...)}. Tilts are picked in pick_tilts()."""
    e = P2 - GROUND_IN
    return {
        "edges": {
            "front": dict(kind="post", xy=(0.0, e), look=(0.0, -1.0)),
            "right": dict(kind="post", xy=(-e, 0.0), look=(1.0, 0.0)),
            "top": dict(kind="crossbar", xy=(0.0, 0.0)),
        },
        "corners": {
            "front": dict(kind="post", xy=(-e, e), look=(1.0, -1.0)),
            "right": dict(kind="post", xy=(-e, -e), look=(1.0, 1.0)),
            "top": dict(kind="rail", xy=(H, 0.0), look=(-1.0, 0.0)),
        },
    }


def place(cam, tilt):
    """Head transforms for one camera at a given tilt (deg)."""
    if cam["kind"] == "post":
        x, y = cam["xy"]
        look = np.r_[cam["look"], 0.0]
        return head_pose([x, y, CLAMP_Z], [0, 0, 1], look, tilt)
    if cam["kind"] == "crossbar":                 # crossbar on x, resting on the left and right top rails
        p = np.array([0.0, 0.0, Z_TOP + CROSS_Z / 1e3])
        return head_pose(p, [-1, 0, 0], [0, 0, -1], 0.0)
    # on the wall-side top rail (along y), hinge plate pointing in and down by `tilt` below horizontal
    t = np.radians(tilt)
    r = np.array([np.cos(t) * cam["look"][0], 0.0, -np.sin(t)])
    clamp_T, cradle_T, lens, view, up = head_pose([cam["xy"][0], cam["xy"][1], Z_TOP], [0, 1, 0], r, 0.0)
    up = cradle_T[:3, :3] @ np.array([0, 1.0, 0])      # board on the portrait holes: long side along the rail
    return clamp_T, cradle_T, lens, view, up


# ------------------------------------------------------------------ reach
def reach(piper, n=1_500_000, voxel=0.02):
    """Where the fingertip can go with every joint inside its URDF limit, above the plywood.
    Returns the occupancy grid (arm frame, metres, origin on J1 at the plywood top)."""
    Q = sample_joints(piper, n, seed=3)
    pts = fk_points(piper, Q)
    ok = np.ones(n, bool)
    for k in ("elbow", "wrist", "flange", "tip"):
        ok &= pts[k][:, 2] > 0.005                 # nothing through the plywood
    tip = pts["tip"][ok]
    lo = np.array([-0.72, -0.72, 0.0])
    shape = np.ceil((np.array([0.72, 0.72, 0.92]) - lo) / voxel).astype(int)
    idx = np.floor((tip - lo) / voxel).astype(int)
    idx = idx[(idx >= 0).all(1) & (idx < shape).all(1)]
    occ = np.zeros(shape, bool)
    occ[tuple(idx.T)] = True
    pad = 3                                        # pad so closing does not eat the faces on the plywood
    occ = np.pad(occ, pad)
    occ = ndimage.binary_fill_holes(ndimage.binary_closing(occ, iterations=2))[pad:-pad, pad:-pad, pad:-pad]
    return occ, lo, voxel, tip


def in_view(P, lens, view, up):
    """Which world points fall inside the camera's image (no occlusion)."""
    z = view / np.linalg.norm(view)
    yv = up - z * (up @ z)
    yv /= np.linalg.norm(yv)
    xv = np.cross(z, yv)            # image right... sign does not matter for a symmetric frustum
    d = P - lens
    zc = d @ z
    u, v = np.abs(d @ xv) / np.maximum(zc, 1e-9), np.abs(d @ yv) / np.maximum(zc, 1e-9)
    return (zc > 0.03) & (u < CAM_W / 2 / CAM_F) & (v < CAM_H / 2 / CAM_F)


def plywood_grid(step=0.01):
    g = np.arange(-P2 + step / 2, P2, step)
    X, Y = np.meshgrid(g, g)
    return np.column_stack([X.ravel(), Y.ravel(), np.full(X.size, PLY_T)])


def coverage(cams, reach_pts, ply_pts):
    """Fraction of the reach volume and of the plywood each camera sees, and seen by 2+ cameras."""
    out, seen_r, seen_p = {}, [], []
    for name, c in cams.items():
        r = in_view(reach_pts, c["lens"], c["view"], c["up"])
        p = in_view(ply_pts, c["lens"], c["view"], c["up"])
        seen_r.append(r)
        seen_p.append(p)
        out[name] = dict(reach_pct=round(100 * r.mean(), 1), plywood_pct=round(100 * p.mean(), 1))
    sr, sp = np.sum(seen_r, 0), np.sum(seen_p, 0)
    out["any"] = dict(reach_pct=round(100 * (sr >= 1).mean(), 1), plywood_pct=round(100 * (sp >= 1).mean(), 1))
    out["two_or_more"] = dict(reach_pct=round(100 * (sr >= 2).mean(), 1), plywood_pct=round(100 * (sp >= 2).mean(), 1))
    return out


WORK_Z = 0.30                       # the work zone: reach volume up to this far above the plywood


def pick_tilts(reach_pts):
    """Tilt for each post camera (on the 15 deg index) and the rail camera (5 deg steps) that sees
    the most of the work zone: the reach volume within WORK_Z of the plywood."""
    reach_pts = reach_pts[reach_pts[:, 2] < PLY_T + WORK_Z]
    out = {}
    for lname, lay in layouts().items():
        out[lname] = {}
        for cname, cam in lay.items():
            if cam["kind"] == "crossbar":
                out[lname][cname] = 0.0
                continue
            cands = range(0, INDEX_MAX + 1, INDEX_STEP) if cam["kind"] == "post" else range(30, 85, 5)
            best = max(cands, key=lambda t: in_view(reach_pts, *place(cam, t)[2:]).mean())
            out[lname][cname] = float(best)
    return out


def cameras(tilts):
    out = {}
    for lname, lay in layouts().items():
        out[lname] = {}
        for cname, cam in lay.items():
            clamp_T, cradle_T, lens, view, up = place(cam, tilts[lname][cname])
            out[lname][cname] = dict(kind=cam["kind"], clamp_T=clamp_T, cradle_T=cradle_T, lens=lens,
                                     view=view, up=up, tilt=tilts[lname][cname], spec=cam)
    return out


def camera_json(c, name, layout):
    """OpenCV extrinsics in the arm's frame (mm, origin on J1 at the plywood top), as piper_twin.py reads."""
    z = c["view"] / np.linalg.norm(c["view"])
    yd = -(c["up"] - z * (c["up"] @ z))
    yd /= np.linalg.norm(yd)
    xd = np.cross(yd, z)
    Rwc = np.column_stack([xd, yd, z])                # camera axes in the world
    Rcw = Rwc.T
    t_arm = (c["lens"] - np.array([0, 0, PLY_T])) * 1e3
    tvec = -Rcw @ t_arm
    rvec = trimesh.transformations.rotation_from_matrix(np.vstack([np.c_[Rcw, [0, 0, 0]], [0, 0, 0, 1]]))
    ang, ax = rvec[0], np.asarray(rvec[1])
    return {"width": CAM_W, "height": CAM_H, "K": [[CAM_F, 0.0, CAM_W / 2], [0.0, CAM_F, CAM_H / 2], [0, 0, 1.0]],
            "dist": [0.0] * 5, "rvec": [round(float(v), 6) for v in ax * ang], "tvec": [round(float(v), 1) for v in tvec],
            "lens_mm": [round(float(v), 1) for v in t_arm], "view": [round(float(v), 4) for v in z],
            "note": f"{name} camera, '{layout}' layout: nominal pose from the CAD (calibrate after mounting)"}


# ------------------------------------------------------------------ scene
def table_base():
    """Legs, aprons and X-braces under the plywood: [(mesh, rgb)]."""
    out = []
    zt = 0.0
    c = P2 - LEG_IN
    for sx in (-1, 1):
        for sy in (-1, 1):
            out.append(_box([sx * c - LEG / 2, sy * c - LEG / 2, FLOOR], [sx * c + LEG / 2, sy * c + LEG / 2, zt]))
    for s in (-1, 1):
        out.append(_box([-c, s * c - 0.019, zt - APRON_H], [c, s * c + 0.019, zt]))
        out.append(_box([s * c - 0.019, -c, zt - APRON_H], [s * c + 0.019, c, zt]))
    lo, hi = FLOOR + 0.08, zt - APRON_H
    for s in (-1, 1):
        for a, b in (((-c, lo), (c, hi)), ((-c, hi), (c, lo))):
            p0, p1 = np.array([a[0], s * (c + 0.03), a[1]]), np.array([b[0], s * (c + 0.03), b[1]])
            out.append(beam(p0, p1, BRACE[0], BRACE[1], up=(0, 1, 0)))
            p0, p1 = np.array([s * (c + 0.03), a[0], a[1]]), np.array([s * (c + 0.03), b[0], b[1]])
            out.append(beam(p0, p1, BRACE[0], BRACE[1], up=(1, 0, 0)))
    return [(m, WOOD) for m in out]


def a1_mini():
    """Bambu A1 mini facing the arm (-x), bed toward the table's middle, and the AMS lite beside it."""
    out = []
    x, y = A1["xy"]
    d, w = A1["base"]
    z0 = PLY_T
    out.append((_box([x - d / 2, y - w / 2, z0], [x + d / 2, y + w / 2, z0 + 0.06]), (0.80, 0.80, 0.80)))
    out.append((_box([x - 0.20, y - 0.09, z0 + 0.06], [x + 0.02, y + 0.09, z0 + 0.075]), DARK))     # bed, slid out
    out.append((_box([x + 0.08, y - w / 2, z0], [x + 0.13, y - w / 2 + 0.06, z0 + A1["h"]]), (0.78, 0.79, 0.80)))  # Z column
    out.append((_box([x + 0.02, y - w / 2 + 0.02, z0 + 0.20], [x + 0.06, y + w / 2 - 0.02, z0 + 0.24]), (0.62, 0.63, 0.64)))  # gantry
    out.append((_box([x - 0.03, y - 0.03, z0 + 0.17], [x + 0.06, y + 0.04, z0 + 0.26]), WHITE))      # toolhead
    ax, ay = AMS["xy"]
    sx, sy = AMS["size"]
    out.append((_box([ax - 0.03, ay - sy / 2, z0], [ax + 0.03, ay + sy / 2, z0 + 0.02]), GREY))
    out.append((_box([ax - 0.02, ay - 0.04, z0], [ax + 0.02, ay + 0.04, z0 + AMS["h"]]), GREY))
    for s in (-1, 1):
        for zc in (0.13, 0.30):
            out.append((_cyl(0.095, 0.07, "y", (ax + s * 0.0, ay + s * 0.09, z0 + zc)), WHITE))
    return out


def power_strip():
    s = STRIP
    m = _box([s["x"] - s["w"] / 2, -s["len"] / 2, PLY_T], [s["x"] + s["w"] / 2, s["len"] / 2, PLY_T + s["h"]])
    return [(m, WHITE)]


def mag_switch():
    """On the front-right leg's front face, just under the apron."""
    c = P2 - LEG_IN
    w, d, h = SWITCH
    x0, y0 = -c, c + LEG / 2
    body = _box([x0 - w / 2, y0, -APRON_H - 0.02 - h], [x0 + w / 2, y0 + d, -APRON_H - 0.02])
    on = _cyl(0.012, 0.01, "y", (x0, y0 + d + 0.004, -APRON_H - 0.06))
    off = _cyl(0.016, 0.012, "y", (x0, y0 + d + 0.005, -APRON_H - 0.11))
    return [(body, (0.96, 0.80, 0.10)), (on, (0.15, 0.55, 0.20)), (off, (0.80, 0.12, 0.12))]


def cloth():
    """Drop cloth on the back, both sides and the top; the front (+y) is left open."""
    t, lo, hi = 0.002, -H, H
    walls = [_box([H - t, lo, Z_BOT], [H, hi, Z_TOP]), _box([-H, lo, Z_BOT], [-H + t, hi, Z_TOP]),
             _box([lo, -H, Z_BOT], [hi, -H + t, Z_TOP]), _box([lo, lo, Z_TOP + R], [hi, hi, Z_TOP + R + t])]
    return walls


def fixture_parts(cams_layout):
    """Every printed part and pipe for one layout, in the world: [(name, mesh, rgb)]."""
    parts = dict(clamp=head_clamp(), cap=clamp_cap(), cradle=head_cradle(), foot=ground_foot(), cross=cross_clamp())
    out = []
    for name, c in cams_layout.items():
        col = PRINT_C[name]
        out.append((f"{name}-clamp", mm_to_world(parts["clamp"], c["clamp_T"]), col))
        out.append((f"{name}-cap", mm_to_world(parts["cap"], c["clamp_T"]), col))
        out.append((f"{name}-cradle", mm_to_world(parts["cradle"], c["cradle_T"]), col))
        Mb = c["cradle_T"] @ T(t=np.array([PLATE_AT + PLATE[0] + STANDOFF + 0.5, 0, LENS_UP]) / 1e3)
        out.append((f"{name}-board", _box([-0.0005, -0.0125, -0.012], [0.0005, 0.0125, 0.012]).apply_transform(Mb), (0.10, 0.45, 0.25)))
        Ml = c["cradle_T"] @ T(t=np.array([LENS_FWD - 3, 0, LENS_UP]) / 1e3)
        out.append((f"{name}-lens", _cyl(0.0055, 0.006, "x").apply_transform(Ml), DARK))
        spec = c["spec"]
        if spec["kind"] == "post":
            x, y = spec["xy"]
            out.append((f"{name}-foot", mm_to_world(parts["foot"], T(t=[x, y, PLY_T])), col))
            out.append((f"{name}-post", along([x, y, PLY_T + FOOT_T / 1e3], [x, y, POST_TOP], PIPE_OD / 2e3), PVC))
        if spec["kind"] == "crossbar":
            zc = Z_TOP + CROSS_Z / 1e3
            out.append(("crossbar", along([-H - 0.02, 0, zc], [H + 0.02, 0, zc], PIPE_OD / 2e3), PVC))
            for s in (-1, 1):
                M = T(np.diag([s, s, 1.0]), [s * H, 0, Z_TOP])
                out.append((f"cross-{s}", mm_to_world(parts["cross"], M), col))
                Mc = M @ T(trimesh.transformations.rotation_matrix(np.pi / 2, (0, 1, 0))[:3, :3]
                           @ trimesh.transformations.rotation_matrix(np.pi / 2, (0, 0, 1))[:3, :3])
                out.append((f"cross-cap-{s}", mm_to_world(parts["cap"], Mc), col))
    return out


def table_parts(piper, q=np.zeros(6)):
    """Everything but cameras and reach: [(name, mesh, rgb, opacity)]."""
    out = [("floor", _box([-1.6, -1.6, FLOOR - 0.01], [1.6, 1.6, FLOOR]), (0.80, 0.80, 0.79), 1.0),
           ("plywood", _box([-P2, -P2, 0], [P2, P2, PLY_T]), PLYC, 1.0)]
    out += [("table", m, c, 1.0) for m, c in table_base()]
    out += [("a1", m, c, 1.0) for m, c in a1_mini()]
    out += [("strip", m, c, 1.0) for m, c in power_strip()]
    out += [("switch", m, c, 1.0) for m, c in mag_switch()]
    out += [("arm", m, c, 1.0) for _, m, c in CB.arm_meshes(piper, q)]
    out.append(("frame", CB.frame(), PVC, 0.35))
    out += [("cloth", m, CLOTH, 0.10) for m in cloth()]
    return out


def main():
    (HERE / "models").mkdir(exist_ok=True)
    for name, fn in (("head-clamp", head_clamp), ("clamp-cap", clamp_cap), ("head-cradle", head_cradle),
                     ("ground-foot", ground_foot), ("cross-clamp", cross_clamp)):
        m = fn()
        assert m.is_watertight, f"{name} is not watertight"
        m = m.copy()
        if name in ("head-clamp", "clamp-cap", "head-cradle"):       # print flat on the hinge or split face
            if name == "head-cradle":
                m.apply_transform(trimesh.transformations.rotation_matrix(-np.pi / 2, (1, 0, 0)))
            elif name == "head-clamp":
                m.apply_transform(trimesh.transformations.rotation_matrix(np.pi / 2, (1, 0, 0)))
        m.apply_translation(-m.bounds[0])
        m.export(HERE / f"models/{name}.stl")
        print(name, np.round(m.extents, 1), "mm,", round(m.volume / 1e3, 1), "cm3")

    piper = Piper()
    occ, lo, vox, tip = reach(piper)
    np.savez_compressed(HERE / "reach.npz", occ=occ, lo=lo, voxel=vox)
    reach_pts = (np.argwhere(occ) + 0.5) * vox + lo + [0, 0, PLY_T]       # world
    ply = plywood_grid()
    tilts = pick_tilts(reach_pts)
    cams = cameras(tilts)
    res = dict(
        hfov_deg=round(HFOV, 1), vfov_deg=round(VFOV, 1),
        reach=dict(max_radius_from_J1_m=round(float(np.hypot(tip[:, 0], tip[:, 1]).max()), 3),
                   max_height_above_plywood_m=round(float(tip[:, 2].max()), 3),
                   volume_m3=round(float(occ.sum() * vox ** 3), 3),
                   plywood_reachable_pct=None),
        layouts={},
    )
    # how much of the plywood the fingertip can touch (within 30 mm of its surface)
    touch = occ[:, :, :2].any(2)
    gx = (np.floor((ply[:, 0] - lo[0]) / vox)).astype(int).clip(0, occ.shape[0] - 1)
    gy = (np.floor((ply[:, 1] - lo[1]) / vox)).astype(int).clip(0, occ.shape[1] - 1)
    res["reach"]["plywood_reachable_pct"] = round(100 * float(touch[gx, gy].mean()), 1)
    for lname, lay in cams.items():
        res["layouts"][lname] = dict(
            cameras={n: dict(kind=c["kind"], tilt_deg=c["tilt"], lens_above_plywood_mm=round((c["lens"][2] - PLY_T) * 1e3),
                             lens_xy_mm=[round(v * 1e3) for v in c["lens"][:2]],
                             distance_to_J1_mm=round(float(np.linalg.norm(c["lens"] - [0, 0, PLY_T])) * 1e3))
                     for n, c in lay.items()},
            coverage=coverage(lay, reach_pts, ply),
            coverage_work_zone=coverage(lay, reach_pts[reach_pts[:, 2] < PLY_T + WORK_Z], ply))
        (HERE / f"cameras-{lname}.json").write_text(json.dumps(
            {n: camera_json(c, n, lname) for n, c in lay.items()}, indent=1) + "\n")
    # post cameras: how close the fingertip can get to each post
    for lname, lay in cams.items():
        for n, c in lay.items():
            if c["kind"] == "post":
                xy = np.array(c["spec"]["xy"])
                d = np.hypot(tip[:, 0] - xy[0], tip[:, 1] - xy[1]).min()
                res["layouts"][lname]["cameras"][n]["closest_fingertip_to_post_mm"] = round(float(d - PIPE_OD / 2e3) * 1e3)
            d = np.linalg.norm(tip - (c["lens"] - [0, 0, PLY_T]), axis=1).min()
            res["layouts"][lname]["cameras"][n]["closest_fingertip_to_lens_mm"] = round(float(d) * 1e3)
    (HERE / "results.json").write_text(json.dumps(res, indent=1) + "\n")
    print(json.dumps(res, indent=1))
    return res


if __name__ == "__main__":
    main()
