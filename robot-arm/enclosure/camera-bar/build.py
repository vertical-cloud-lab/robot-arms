"""Overhead camera bar for the as-built enclosure (#2, #38, cameras from #24).

    python build.py         # bar-results.json, camera_overhead.json, models/*.stl, camera-bar.glb

The frame is the 48 in PVC cube Chris built (#38): twelve 48.00 in pipes, side-outlet elbows with a
measured 5/8 in take-out (49.25 in centre to centre), bottom rails screwed into the edge of the
48 x 48 x 3/4 in plywood. A 2020 aluminium bar runs corner to corner across the top, on two printed
saddles that locate against the corner elbows, and the overhead camera hangs under its middle.

World coordinates match the other enclosure models: x along the wall (the way the arm faces at
J1 = 0), y from the room (-y) to the wall (+y), z up from the table top, metres. The STLs are in
mm, the saddle in its print orientation. camera_overhead.json is in the arm's frame (mm, origin on
J1 at the top of the plywood), the format piper_twin.py reads (#24).
"""

import json
import sys
from pathlib import Path

import numpy as np
import trimesh
from shapely.geometry import Polygon
from trimesh.creation import box, cylinder, icosphere

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE.parent))
from piper_fk import Piper, fk_points, sample_joints  # noqa: E402

IN = 0.0254

# ------------------------------------------------------------------ as built (#38)
PIPE_CUT = 48.00 * IN               # all twelve pieces
TAKE_OUT = 0.625 * IN               # measured, per socket
SPAN = PIPE_CUT + 2 * TAKE_OUT      # 49.25 in, elbow centre to centre
H = SPAN / 2                        # pipe axes at x, y = +-H
PIPE_OD, PIPE_WALL = 1.050 * IN, 0.113 * IN   # 3/4 in Sch 40 (ASTM D1785)
R = PIPE_OD / 2
HUB_R, HUB_L = 0.0165, 0.036        # elbow socket hub: radius, reach from the corner centre (estimated)
PLY = 48.0 * IN                     # plywood, square
PLY_T = 0.75 * IN                   # #38 draws it as a full 0.75 in
Z_BOT = R                           # bottom rails: pipe bottom flush with the plywood bottom, on the table
Z_TOP = R + SPAN                    # top rail axis
J1 = np.array([0.0, 0.0, PLY_T])    # arm's base: plywood centre (assumed, as in #24)

# ------------------------------------------------------------------ saddle (one part, print 2)
# Local frame: origin on the corner elbow's centre, u and v along the two top rails into the box,
# z up from the rail axis. Metres.
CLEAR = 0.0003                      # channel clearance on the pipe radius
SIDE = 0.0035                       # wall beside the pipe
E = R + SIDE
D0 = HUB_L + 0.0005                 # legs start here: their end faces butt against the elbow's hubs
LEG = 0.070                         # leg length along each rail
Z_FLOOR = 0.023                     # bar's underside above the rail axis (clears the elbow by 6 mm)
BAR = 0.020                         # 2020 extrusion
SOCK = 0.0205                       # socket width
WALL = 0.004
S0 = 0.035                          # socket's end stop, along the diagonal from the corner centre
SOCK_LEN = 0.050
Z_WALL = Z_FLOOR + 0.016            # side walls reach past the side slots' centres
PIN_D, PIN_CB = 0.0045, 0.009       # #8 pan-head screw into the rail: clearance, counterbore
M5, M5_HEAD = 0.0055, 0.010

# ------------------------------------------------------------------ bar and camera
DIAG = np.array([1.0, 1.0, 0.0]) / np.sqrt(2)     # front-left corner -> back-right corner
BAR_LEN = 2 * H * np.sqrt(2) - 2 * S0 - 0.001     # 1 mm total play between the two stops
Z_BAR_BOTTOM = Z_TOP + Z_FLOOR
PLATE_T, PLATE_D = 0.008, 0.076     # camera plate: #24's overhead spacer, ears turned 45 deg
EAR_X, M5_PITCH = 0.020, 0.030      # case ears +-20 mm (#24's interface), M5 +-30 mm along the bar
LENS_BELOW_CASE = 0.014             # #24's LENS_Z_CASE
LENS = np.array([0.0, 0.0, Z_BAR_BOTTOM - PLATE_T - LENS_BELOW_CASE])
PI_AT = 0.18                        # Pi 5 on top of the bar, this far from the middle toward the back

# #24's side cameras (corner posts on printed feet screwed to the plywood), for context only
FOOT, POST_IN = 0.090, 0.045
SIDE_CAMS = {"front-right": dict(xy=(PLY / 2 - POST_IN, -(PLY / 2 - POST_IN)), post=0.500, lens=0.350),
             "back-right": dict(xy=(PLY / 2 - POST_IN, PLY / 2 - POST_IN), post=0.600, lens=0.500)}

# Camera Module 3 Wide (#24): 4608 x 2592 px, f = 1964 px (102 x 67 deg)
CAM_W, CAM_H, CAM_F = 4608, 2592, 1964.0

PRINT, ALU, PVC, PLYC, CAMC, PIC = ((0.93, 0.55, 0.20), (0.72, 0.74, 0.77), (0.96, 0.96, 0.94),
                                    (0.89, 0.82, 0.68), (0.10, 0.10, 0.10), (0.12, 0.55, 0.27))
REST = np.zeros(6)
POSE = np.radians([35, 95, -75, 0, 55, 0])          # a reach toward the back-right, for the figures


def T(R_=np.eye(3), t=(0, 0, 0)):
    M = np.eye(4)
    M[:3, :3] = R_
    M[:3, 3] = t
    return M


def along(a, b, r, sections=24):
    """Cylinder of radius r from a to b."""
    a, b = np.asarray(a, float), np.asarray(b, float)
    return cylinder(radius=r, segment=np.array([a, b]), sections=sections)


def beam(a, b, w, h=None, up=(0, 0, 1)):
    """Box of w x h section from a to b (h along `up`, square if h is None)."""
    a, b = np.asarray(a, float), np.asarray(b, float)
    d = b - a
    L = np.linalg.norm(d)
    z = d / L
    y = np.asarray(up, float) - z * (np.asarray(up, float) @ z)
    y /= np.linalg.norm(y)
    x = np.cross(y, z)
    m = box((w, h or w, L))
    m.apply_transform(T(np.column_stack([x, y, z]), (a + b) / 2))
    return m


# ------------------------------------------------------------------ parts
def saddle():
    """Corner saddle, local frame (see above), metres."""
    hexagon = np.array([(D0, -E), (D0 + LEG, -E), (D0 + LEG, E), (E, D0 + LEG), (-E, D0 + LEG), (-E, D0)])
    body = trimesh.creation.extrude_polygon(Polygon(hexagon), Z_FLOOR)
    # socket walls and end stop, along the diagonal
    d2 = np.array([1.0, 1.0, 0.0]) / np.sqrt(2)
    a = d2 * (S0 - WALL) + [0, 0, Z_FLOOR - 0.004]
    b = d2 * (S0 + SOCK_LEN) + [0, 0, Z_FLOOR - 0.004]
    walls = beam(a, b, SOCK + 2 * WALL, Z_WALL - Z_FLOOR + 0.004)
    walls.apply_translation([0, 0, (Z_WALL - Z_FLOOR + 0.004) / 2])
    body = body.union(walls)
    cuts = []
    a = d2 * S0 + [0, 0, Z_FLOOR]
    b = d2 * (S0 + SOCK_LEN + 0.01) + [0, 0, Z_FLOOR]
    cav = beam(a, b, SOCK, 0.04)
    cav.apply_translation([0, 0, 0.02])
    cuts.append(cav)
    for ax in ((1, 0, 0), (0, 1, 0)):                       # the two rails, and the elbow's hubs
        ax = np.array(ax, float)
        cuts.append(along(-ax * 0.05, ax * 0.25, R + CLEAR, 64))
        cuts.append(along(-ax * 0.03, ax * D0, HUB_R + 0.0005, 64))
        p = ax * (D0 + LEG / 2)                             # #8 pin screw into the rail, counterbored
        cuts.append(along(p - [0, 0, 0.01], p + [0, 0, 0.05], PIN_D / 2, 24))
        cuts.append(along(p + [0, 0, Z_FLOOR - 0.004], p + [0, 0, 0.05], PIN_CB / 2, 24))
    corner = icosphere(subdivisions=3, radius=HUB_R + 0.0008)
    cuts.append(corner)
    side = np.array([-1.0, 1.0, 0.0]) / np.sqrt(2)            # M5 locks through one side wall
    for s in (0.012, 0.038):
        p = d2 * (S0 + s) + [0, 0, Z_FLOOR + BAR / 2]
        cuts.append(along(p + side * 0.002, p + side * 0.03, M5 / 2, 24))
    body = body.difference(trimesh.boolean.union(cuts))
    return body


def camera_plate():
    """#24's overhead spacer with the case's M3 ears turned 45 deg from the bar. Local: bar along
    the diagonal (1, 1)/sqrt2, ears along x, top face (against the bar) at z = 0."""
    disc = cylinder(radius=PLATE_D / 2, height=PLATE_T, sections=72)
    disc.apply_translation([0, 0, -PLATE_T / 2])
    d2 = np.array([1.0, 1.0, 0.0]) / np.sqrt(2)
    cuts = []
    for s in (-1, 1):
        p = d2 * s * M5_PITCH
        cuts.append(along(p - [0, 0, 0.02], p + [0, 0, 0.01], M5 / 2, 24))
        cuts.append(along(p - [0, 0, 0.02], p - [0, 0, PLATE_T - 0.0032], M5_HEAD / 2, 24))
        q = np.array([s * EAR_X, 0, 0])
        cuts.append(along(q - [0, 0, 0.02], q + [0, 0, 0.01], 0.0013, 16))
    return disc.difference(trimesh.boolean.union(cuts))


def camera_head():
    """Case, board and lens (simplified from #24's cam_case), hanging under the plate: [(mesh, rgb)]."""
    z0 = Z_BAR_BOTTOM - PLATE_T
    case = box((0.049, 0.0312, 0.003))
    case.apply_translation([0, 0, z0 - 0.0015])
    rim = box((0.0278, 0.0278, 0.0056))
    rim.apply_translation([0, -0.001, z0 - 0.003 - 0.0028])
    board = box((0.024, 0.025, 0.0016))
    board.apply_translation([0, -0.001, z0 - 0.003 - 0.0048])
    lens = along([0, 0, z0 - 0.007], LENS, 0.0045, 24)
    return [(case, PRINT), (rim, PRINT), (board, PIC), (lens, CAMC)]


def pi_on_bar():
    """Pi 5 on #24's pi5_plate, on top of the bar: [(mesh, rgb)]."""
    c = DIAG * PI_AT + [0, 0, Z_BAR_BOTTOM + BAR]
    Rz = trimesh.transformations.rotation_matrix(np.pi / 4, (0, 0, 1))[:3, :3]
    out = []
    for size, dz, rgb in (((0.094, 0.064, 0.005), 0.0025, PRINT), ((0.085, 0.056, 0.0016), 0.0108, PIC),
                          ((0.040, 0.040, 0.010), 0.0166, CAMC)):
        m = box(size)
        m.apply_transform(T(Rz, c + [0, 0, dz]))
        out.append((m, rgb))
    return out


def elbow(sx, sy, top):
    """Side-outlet elbow: three socket hubs and a round corner, legs pointing into the box."""
    c = np.array([sx * H, sy * H, Z_TOP if top else Z_BOT])
    ms = [icosphere(subdivisions=2, radius=HUB_R).apply_translation(c)]
    for d in ((-sx, 0, 0), (0, -sy, 0), (0, 0, -1 if top else 1)):
        ms.append(along(c, c + np.array(d) * HUB_L, HUB_R))
    return trimesh.util.concatenate(ms)


def frame():
    """The as-built cube: 12 pipes (axis to axis; the elbows hide the joints) and 8 elbows."""
    ms = []
    for sx in (-1, 1):
        for sy in (-1, 1):
            ms.append(along([sx * H, sy * H, Z_BOT], [sx * H, sy * H, Z_TOP], R))
            for z in (Z_BOT, Z_TOP):
                ms.append(elbow(sx, sy, z == Z_TOP))
    for z in (Z_BOT, Z_TOP):
        for s in (-1, 1):
            ms.append(along([-H, s * H, z], [H, s * H, z], R))
            ms.append(along([s * H, -H, z], [s * H, H, z], R))
    return trimesh.util.concatenate(ms)


def saddle_to_world(sx, sy):
    """Corner (sx, sy) of the top frame: u, v point along the rails into the box."""
    u, v = np.array([-sx, 0.0, 0.0]), np.array([0.0, -sy, 0.0])
    return T(np.column_stack([u, v, [0, 0, 1.0]]), [sx * H, sy * H, Z_TOP])


def bar():
    a = np.array([-H, -H, 0]) + DIAG * (S0 + 0.0005)
    b = np.array([H, H, 0]) - DIAG * (S0 + 0.0005)
    z = Z_BAR_BOTTOM + BAR / 2
    return beam(a + [0, 0, z], b + [0, 0, z], BAR)


def side_cameras():
    """#24's corner posts (FR, BR) as plain shapes: [(mesh, rgb)]."""
    out = []
    for c in SIDE_CAMS.values():
        x, y = c["xy"]
        foot = box((FOOT, FOOT, 0.006))
        foot.apply_translation([np.sign(x) * (PLY / 2 - FOOT / 2), np.sign(y) * (PLY / 2 - FOOT / 2), PLY_T + 0.003])
        post = box((BAR, BAR, c["post"]))
        post.apply_translation([x, y, PLY_T + 0.006 + c["post"] / 2])
        to = -np.array([x, y]) / np.hypot(x, y)
        head = box((0.012, 0.049, 0.031))
        yaw = np.arctan2(to[1], to[0])
        head.apply_transform(T(trimesh.transformations.rotation_matrix(yaw, (0, 0, 1))[:3, :3],
                               [x + to[0] * 0.03, y + to[1] * 0.03, PLY_T + c["lens"]]))
        out += [(foot, PRINT), (post, ALU), (head, CAMC)]
    return out


def arm_meshes(piper, q, grip=0.012):
    """PiPER meshes in the world, J1 on the plywood centre, facing +x at J1 = 0."""
    out = []
    poses = piper.fk(q, grip=grip)
    B = T(t=J1)
    for name, path in piper.meshes.items():
        scene = trimesh.load(path, force="scene")
        for node in scene.graph.nodes_geometry:
            Tn, g = scene.graph[node]
            m = scene.geometry[g]
            if len(m.faces) < 10:
                continue
            try:
                c = np.array(m.visual.material.main_color[:3]) / 255
            except AttributeError:
                c = np.array([0.6, 0.6, 0.6])
            m = trimesh.Trimesh(trimesh.transform_points(m.vertices, Tn), m.faces, process=False)
            m.apply_transform(B @ poses[name] @ piper.visual_origin[name])
            out.append((name, m, c))
    return out


def scene_parts(piper=None, q=POSE):
    """Everything, in the world: [(name, mesh, rgb)]."""
    sad = saddle()
    out = [("plywood", box((PLY, PLY, PLY_T)).apply_translation([0, 0, PLY_T / 2]), PLYC),
           ("frame", frame(), PVC), ("bar", bar(), ALU)]
    for k, (sx, sy) in enumerate(((-1, -1), (1, 1))):
        out.append((f"saddle-{k}", sad.copy().apply_transform(saddle_to_world(sx, sy)), PRINT))
    plate = camera_plate().apply_translation([0, 0, Z_BAR_BOTTOM])
    out.append(("camera-plate", plate, PRINT))
    out += [("camera", m, c) for m, c in camera_head()]
    out += [("pi", m, c) for m, c in pi_on_bar()]
    out += [("side-cameras", m, c) for m, c in side_cameras()]
    if piper is not None:
        out += [("arm", m, c) for _, m, c in arm_meshes(piper, q)]
    return out


# ------------------------------------------------------------------ stiffness (3D frame, N and mm)
PVC_SEC = dict(E=2800.0, G=1010.0, A=np.pi / 4 * ((PIPE_OD * 1e3) ** 2 - ((PIPE_OD - 2 * PIPE_WALL) * 1e3) ** 2))
PVC_SEC["I"] = np.pi / 64 * ((PIPE_OD * 1e3) ** 4 - ((PIPE_OD - 2 * PIPE_WALL) * 1e3) ** 4)
PVC_SEC["J"] = 2 * PVC_SEC["I"]
ALU_SEC = dict(E=69000.0, G=26000.0, A=175.0, I=7000.0, J=2000.0)       # 2020 B-type, nominal
CABLE_SEC = dict(E=100000.0, G=1.0, A=1.0, I=1e-3, J=1e-3)               # 1/16 in 7x7 steel wire rope


def k_beam(a, b, s):
    """12x12 global stiffness of a 3D Euler-Bernoulli beam from a to b (mm)."""
    d = np.asarray(b, float) - np.asarray(a, float)
    L = np.linalg.norm(d)
    x = d / L
    ref = np.array([0, 0, 1.0]) if abs(x[2]) < 0.9 else np.array([1.0, 0, 0])
    y = np.cross(ref, x)
    y /= np.linalg.norm(y)
    z = np.cross(x, y)
    E_, G_, A_, I_, J_ = s["E"], s["G"], s["A"], s["I"], s["J"]
    k = np.zeros((12, 12))
    k[0, 0] = k[6, 6] = E_ * A_ / L
    k[0, 6] = k[6, 0] = -E_ * A_ / L
    k[3, 3] = k[9, 9] = G_ * J_ / L
    k[3, 9] = k[9, 3] = -G_ * J_ / L
    for (v, t, sg) in ((1, 5, 1), (2, 4, -1)):          # bending in the two planes
        a1, a2, a3, a4 = 12 * E_ * I_ / L ** 3, 6 * E_ * I_ / L ** 2, 4 * E_ * I_ / L, 2 * E_ * I_ / L
        idx = [v, t, v + 6, t + 6]
        m = np.array([[a1, sg * a2, -a1, sg * a2], [sg * a2, a3, -sg * a2, a4],
                      [-a1, -sg * a2, a1, -sg * a2], [sg * a2, a4, -sg * a2, a3]])
        for i in range(4):
            for j in range(4):
                k[idx[i], idx[j]] = m[i, j]
    Rm = np.vstack([x, y, z])
    Tm = np.kron(np.eye(4), Rm)
    return Tm.T @ k @ Tm


def frame_model(variant):
    """Nodes (mm) and members for one variant. Bottom corners are fixed: the bottom rails are
    screwed into the plywood (#38), and every socket is taken as pinned with a screw (rigid)."""
    h, top = SPAN * 1e3 / 2, Z_TOP * 1e3
    nodes, members = {}, []
    for sx in (-1, 1):
        for sy in (-1, 1):
            nodes[f"b{sx}{sy}"] = np.array([sx * h, sy * h, Z_BOT * 1e3])
            nodes[f"t{sx}{sy}"] = np.array([sx * h, sy * h, top])
            members.append((f"b{sx}{sy}", f"t{sx}{sy}", PVC_SEC))
    if variant.startswith("straight"):                  # bar across the middle, on mid-rail saddles
        nodes["m-"], nodes["m+"] = np.array([-h, 0, top]), np.array([h, 0, top])
        for s in (-1, 1):
            members += [(f"t-1{s}", f"t1{s}", PVC_SEC)]
        members += [("t-1-1", "m-", PVC_SEC), ("m-", "t-11", PVC_SEC), ("t1-1", "m+", PVC_SEC), ("m+", "t11", PVC_SEC)]
        nodes["cam"] = np.array([0, 0, top + 30])
        members += [("m-", "cam", ALU_SEC), ("cam", "m+", ALU_SEC)]
    else:
        for s in (-1, 1):
            members += [(f"t-1{s}", f"t1{s}", PVC_SEC), (f"t{s}-1", f"t{s}1", PVC_SEC)]
        nodes["cam"] = np.array([0, 0, top + 30])
        members += [("t-1-1", "cam", ALU_SEC), ("cam", "t11", ALU_SEC)]
    if variant.endswith("cables"):                      # X-braced back and side walls, tensioned wire
        for a, b in (("b-11", "t11"), ("b11", "t-11"), ("b-1-1", "t-11"), ("b-11", "t-1-1"),
                     ("b1-1", "t11"), ("b11", "t1-1")):
            members.append((a, b, CABLE_SEC))
    return nodes, members


def solve(variant, loads):
    nodes, members = frame_model(variant)
    names = list(nodes)
    ix = {n: i for i, n in enumerate(names)}
    K = np.zeros((6 * len(names), 6 * len(names)))
    for a, b, s in members:
        k = k_beam(nodes[a], nodes[b], s)
        dofs = np.r_[6 * ix[a]:6 * ix[a] + 6, 6 * ix[b]:6 * ix[b] + 6]
        K[np.ix_(dofs, dofs)] += k
    F = np.zeros(len(K))
    for n, f in loads.items():
        F[6 * ix[n]:6 * ix[n] + 6] += f
    fixed = np.concatenate([np.arange(6 * ix[n], 6 * ix[n] + 6) for n in names if n.startswith("b")])
    free = np.setdiff1d(np.arange(len(K)), fixed)
    u = np.zeros(len(K))
    u[free] = np.linalg.solve(K[np.ix_(free, free)], F[free])
    return {n: u[6 * ix[n]:6 * ix[n] + 6] for n in names}


def camera_shift(u, h_mm):
    """Where the image centre lands on the plywood moves by the camera's own shift plus its tilt
    times the height: (dx - h*ry, dy + h*rx)."""
    dx, dy, dz, rx, ry, rz = u
    return np.array([dx - h_mm * ry, dy + h_mm * rx]), dz, np.hypot(rx, ry)


def stiffness():
    h_mm = (LENS[2] - PLY_T) * 1e3
    g = 9.81
    bar_kg = 0.49 * BAR_LEN
    out = {}
    for variant in ("diagonal", "diagonal+cables", "straight", "straight+cables"):
        # gravity: the bar's weight split between its ends and the middle, plus camera (0.05 kg) and Pi (0.12 kg)
        nodes, _ = frame_model(variant)
        ends = ("t-1-1", "t11") if variant.startswith("diagonal") else ("m-", "m+")
        loads = {n: np.array([0, 0, -g * bar_kg / 4, 0, 0, 0]) for n in ends}
        loads["cam"] = np.array([0, 0, -g * (bar_kg / 2 + 0.05 + 0.12), 0, 0, 0])
        sag = solve(variant, loads)["cam"][2]
        res = dict(sag_mm=round(float(-sag), 2))
        for name, n, f in (("push_10N_x_at_front_left_corner", "t-1-1", (10, 0, 0)),
                           ("push_10N_y_at_front_left_corner", "t-1-1", (0, 10, 0)),
                           ("push_10N_x_at_front_right_corner", "t1-1", (10, 0, 0))):
            u = solve(variant, {n: np.r_[f, 0, 0, 0]})
            shift, dz, tilt = camera_shift(u["cam"], h_mm)
            res[name] = dict(camera_move_mm=round(float(np.hypot(*u["cam"][:2])), 2),
                             camera_tilt_mrad=round(float(tilt * 1e3), 2),
                             image_shift_at_plywood_mm=round(float(np.hypot(*shift)), 2),
                             corner_move_mm=round(float(np.linalg.norm(u[n][:3])), 2))
        out[variant] = res
    return out


# ------------------------------------------------------------------ camera
def camera_json():
    h = (LENS[2] - PLY_T) * 1e3
    return {"width": CAM_W, "height": CAM_H, "K": [[CAM_F, 0.0, CAM_W / 2], [0.0, CAM_F, CAM_H / 2], [0, 0, 1.0]],
            "dist": [0.0] * 5, "rvec": [0.0, round(np.pi, 6), 0.0], "tvec": [0.0, 0.0, round(h, 1)],
            "note": f"{h / 1e3:.2f} m above the plywood, under the middle of the corner-to-corner top bar, "
                    "straight down with the image's long side along the wall (nominal, from the CAD; "
                    "calibrate after mounting)"}


def footprint():
    """Ground footprint of the image on the plywood (half-widths, m) and margin past the plywood."""
    h = LENS[2] - PLY_T
    hw, hh = h * (CAM_W / 2) / CAM_F, h * (CAM_H / 2) / CAM_F
    return dict(height_above_plywood_m=round(h, 3), half_width_along_wall_m=round(hw, 3),
                half_width_across_m=round(hh, 3), margin_past_plywood_edge_m=round(hh - PLY / 2, 3))


def main():
    (HERE / "models").mkdir(exist_ok=True)
    sad = saddle()
    assert sad.is_watertight, "saddle is not watertight"
    s = sad.copy().apply_scale(1e3)
    s.apply_translation([0, 0, -s.bounds[0][2]])
    s.export(HERE / "models/corner-saddle.stl")
    pl = camera_plate()
    pl = pl.copy().apply_scale(1e3)
    pl.apply_translation([0, 0, -pl.bounds[0][2]])
    pl.export(HERE / "models/camera-plate.stl")
    frame().apply_scale(1e3).export(HERE / "models/frame-as-built.stl")

    piper = Piper()
    sc = trimesh.Scene()
    for name, m, c in scene_parts(piper):
        m = m.copy()
        m.visual.face_colors = (np.r_[np.asarray(c) * 255, 255]).astype(np.uint8)
        sc.add_geometry(m, node_name=name, geom_name=name)
    sc.export(HERE / "camera-bar.glb")

    # what the arm can reach: highest fingertip or link over the plywood, vs the camera
    Q = sample_joints(piper, 200000, seed=1)
    pts = fk_points(piper, Q)
    top_tip = float(max(pts[k][:, 2].max() for k in ("elbow", "wrist", "flange", "tip")))

    res = dict(
        frame_as_built_in=dict(pipe_cut=48.0, elbow_centre_to_centre=round(SPAN / IN, 2),
                               outside=round((SPAN + PIPE_OD) / IN, 2), inside=round((SPAN - PIPE_OD) / IN, 2),
                               clear_height=round((Z_TOP - R - PLY_T) / IN, 2), overall_height=round((Z_TOP + R) / IN, 2)),
        bar=dict(length_mm=round(BAR_LEN * 1e3, 1), underside_above_table_mm=round(Z_BAR_BOTTOM * 1e3, 1),
                 underside_above_rail_top_mm=round((Z_FLOOR - R) * 1e3, 1)),
        saddle_mm=dict(legs_start_from_corner=round(D0 * 1e3, 1), leg_length=LEG * 1e3,
                       stop_from_corner_along_diagonal=S0 * 1e3,
                       bounds=[[round(v, 1) for v in row] for row in (s.bounds).tolist()],
                       volume_cm3=round(float(s.volume) / 1e3, 1)),
        camera=dict(lens_above_table_mm=round(LENS[2] * 1e3, 1), lens_above_plywood_mm=round((LENS[2] - PLY_T) * 1e3, 1),
                    footprint=footprint(),
                    highest_fingertip_above_plywood_mm=round(top_tip * 1e3, 0),
                    clearance_lens_to_highest_fingertip_mm=round((LENS[2] - PLY_T - top_tip) * 1e3, 0)),
        stiffness=stiffness(),
    )
    (HERE / "bar-results.json").write_text(json.dumps(res, indent=1) + "\n")
    (HERE / "camera_overhead.json").write_text(json.dumps(camera_json(), indent=1) + "\n")
    print(json.dumps(res, indent=1))


if __name__ == "__main__":
    main()
