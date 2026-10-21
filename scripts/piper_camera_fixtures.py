#!/usr/bin/env python3
"""Printable fixtures for the PiPER cell's three fixed cameras (issue #24).

Places three Camera Module 3 Wide cameras around the arm on the 4 x 4 ft plywood topper and
builds the parts that hold them: two corner posts at the right-hand end (the end the arm faces)
and one overhead camera on a boom from the back-left corner. All three posts are 2020 aluminium
extrusion standing in printed feet at the topper's corners, the only places on the topper the
fingertips can't reach. The printed parts set every camera's aim, so a camera knocked off its post
goes back to the same pose.

    python scripts/piper_camera_fixtures.py --out docs/issue-24/camera-fixtures            # parts
    python scripts/piper_camera_fixtures.py --out docs/issue-24/camera-fixtures --render   # + figures
    python scripts/piper_camera_fixtures.py --out docs/issue-24/camera-fixtures --render --animate

Needs cadquery (parts, STEP) and numpy, opencv, trimesh, scipy (scores and renders, through
piper_twin.py and piper_camera_placement.py). Never talks to the arm.

Frame: the arm's base frame, mm. x is the way the arm points at J1 = 0 (the topper's right-hand
end, as seen from the room), y toward the wall, z up from the topper. J1 is assumed to stand in the
middle of the topper (it is 606 mm from the wall in #9's model; the topper is 1219 mm square).
Change TOPPER_MM or J1_XY_MM below if it doesn't.
"""
import argparse
import json
import math
import os

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))

# ---------------------------------------------------------------- the cell
TOPPER_MM = 1219.2  # 4 x 4 ft
J1_XY_MM = (0.0, 0.0)  # J1's axis in topper-centred coordinates
HALF = TOPPER_MM / 2
FOOT_MM = 90.0  # square foot plate; its two outer edges sit flush with the topper's edges
POST_IN = FOOT_MM / 2  # post centre, in from each edge
SOCKET_FLOOR = 6.0  # foot plate thickness: the post stands on this
TARGET = (0.0, 60.0, 180.0)  # where the corner cameras aim: just behind J1, at mid-arm height
REACH_MM = 760.0  # fingertips from J2 (z = 123 mm), arm straight; see piper_camera_placement.py
J2_Z = 123.0


def corner(sx, sy):
    return (sx * (HALF - POST_IN) - J1_XY_MM[0], sy * (HALF - POST_IN) - J1_XY_MM[1])


# Lens heights (mm above the topper) and aims. Scored in docs/issue-24/camera-fixtures/README.md.
CAMERAS = {
    "front-right": dict(post=corner(1, -1), lens_z=350.0, target=TARGET, post_len=500,
                        where="front-right corner (room side, the end the arm faces)"),
    "back-right": dict(post=corner(1, 1), lens_z=500.0, target=TARGET, post_len=600,
                       where="back-right corner (wall side, the end the arm faces), "
                             "high enough to see over the shelf"),
    "overhead": dict(post=corner(-1, 1), lens_xy=(-300.0, 100.0), lens_z=1200.0, post_len=1200,
                     where="1.2 m above the table, on a boom from the back-left corner, "
                           "looking straight down with the image's long side along the wall"),
}

# ---------------------------------------------------------------- hardware
CM3_BOARD = (25.0, 24.0)  # Camera Module 3 PCB, mm (x across, y along the ribbon)
CM3_HOLES = [(-10.5, 10.0), (10.5, 10.0), (-10.5, -2.5), (10.5, -2.5)]  # M2, board centre origin
EXTR = 20.0  # 2020 extrusion
SOCK = 20.5  # socket for it (print clearance)
M5_CLEAR, M5_HEAD, M3_PILOT, M3_CLEAR, M2_PILOT, M25_PILOT = 5.5, 10.0, 2.6, 3.4, 1.7, 2.2
EAR_X = 20.0  # the case's two M3 ears, +-EAR_X from the lens axis: the pattern every adapter uses
PI5_HOLES = [(-29.0, -24.5), (29.0, -24.5), (-29.0, 24.5), (29.0, 24.5)]  # 58 x 49 mm, M2.5


def aim(name):
    """Lens position (mm), viewing direction, and the post's yaw (deg): the yaw turns one post
    face toward the target (corner cameras) or along the boom (overhead)."""
    c = CAMERAS[name]
    px, py = c["post"]
    if name == "overhead":
        lx, ly = c["lens_xy"]
        yaw = math.degrees(math.atan2(ly - py, lx - px))
        return np.array([lx, ly, c["lens_z"]]), np.array([0.0, 0.0, -1.0]), yaw
    t = np.array(c["target"], float)
    yaw = math.degrees(math.atan2(t[1] - py, t[0] - px))
    u = np.array([math.cos(math.radians(yaw)), math.sin(math.radians(yaw)), 0.0])
    lens = np.array([px, py, c["lens_z"]])
    for _ in range(4):  # the lens sits out in front of the post face; settle the aim on it
        d = (t - lens) / np.linalg.norm(t - lens)
        out, _ = wedge_lens_offset(math.degrees(math.asin(-d[2])))
        lens = np.array([px, py, c["lens_z"]]) + u * (EXTR / 2 + out)
    return lens, d, yaw


def pitch_of(name):
    _, d, _ = aim(name)
    return math.degrees(math.asin(-d[2]))


def wedge_centre_z(name):
    """Height of the wedge's centre on the post (where to set it), for the lens at lens_z."""
    return CAMERAS[name]["lens_z"] - wedge_lens_offset(pitch_of(name))[1]


# ---------------------------------------------------------------- parts (cadquery)
def cyl(x, y, z0, h, d):
    import cadquery as cq
    return cq.Workplane("XY").workplane(offset=z0).center(x, y).circle(d / 2).extrude(h)


CASE_T, STANDOFF, WALL = 3.0, 4.0, 1.6
CASE_W, CASE_H = 2 * EAR_X + 9.0, CM3_BOARD[1] + 2 * WALL + 2.0
LENS_Z_CASE = CASE_T + STANDOFF + 1.0 + 6.0  # lens front-ish above the case back (optics only)
WEDGE_T0, WEDGE_W, WEDGE_L, TAB_T, TAB_V = 12.0, 50.0, 76.0, 6.0, 20.0


def wedge_lens_offset(pitch_deg):
    """(out from post face, up) of the lens relative to the wedge's centre on the post."""
    th = math.radians(pitch_deg)
    return np.array([WEDGE_T0, 0.0]) + np.array([math.cos(th), -math.sin(th)]) * LENS_Z_CASE


def cam_case():
    """Camera Module 3 holder. Prints back-down. Board on 4 M2 standoffs, ribbon out the bottom,
    two M3 ears at +-EAR_X that bolt it to any adapter below (wedge, overhead spacer)."""
    import cadquery as cq
    bw, bh = CM3_BOARD
    oy = -1.0  # board centre sits 1 mm below the case centre, leaving room for the ribbon bend
    case = cq.Workplane("XY").rect(CASE_W, CASE_H).extrude(CASE_T).edges("|Z").fillet(4)
    rim = (cq.Workplane("XY").workplane(offset=CASE_T).center(0, oy)
           .rect(bw + 0.6 + 2 * WALL, bh + 0.6 + 2 * WALL).rect(bw + 0.6, bh + 0.6)
           .extrude(STANDOFF + 1.0 + 0.6))
    gap = (cq.Workplane("XY").workplane(offset=CASE_T).center(0, oy - bh / 2 - WALL / 2)
           .rect(19.0, 3 * WALL).extrude(STANDOFF + 2))  # the ribbon leaves here
    case = case.union(rim).cut(gap)
    for x, y in CM3_HOLES:
        boss = (cq.Workplane("XY").workplane(offset=CASE_T).center(x, y + oy).circle(2.4)
                .extrude(STANDOFF))
        case = case.union(boss)
    for x, y in CM3_HOLES:
        case = case.cut(cyl(x, y + oy, 1.0, CASE_T + STANDOFF, M2_PILOT))
    for x in (EAR_X, -EAR_X):
        case = case.cut(cyl(x, 0, 0, CASE_T, M3_CLEAR))
    # a lens-centre mark on the back, so the case can be squared up by eye
    case = case.cut(cq.Workplane("XY").center(0, CM3_HOLES[0][1] - 6.0 + oy).rect(0.8, 6).extrude(0.6))
    return case


def wedge(pitch_deg):
    """Fixed-pitch block between a post face and the case. Prints on its side (the profile face).
    Two M5 screws into drop-in T-nuts in the post's slot; two M3 self-tapping screws hold the case."""
    import cadquery as cq
    th = math.radians(pitch_deg)
    f = np.array([math.sin(th), math.cos(th)])  # along the camera face, (out, up)
    n = np.array([math.cos(th), -math.sin(th)])  # face normal = viewing direction
    c = np.array([WEDGE_T0, 0.0])
    half = CASE_H / 2 + 1.0
    lo, hi = c - f * half, c + f * half
    v0 = TAB_V  # tabs carry the M5 screws, above and below the face
    pts = [(0, -WEDGE_L / 2), (TAB_T, -WEDGE_L / 2), (TAB_T, -v0), (max(lo[0], TAB_T), lo[1]),
           tuple(lo), tuple(hi), (max(hi[0], TAB_T), hi[1]), (TAB_T, v0), (TAB_T, WEDGE_L / 2),
           (0, WEDGE_L / 2)]
    pts = [p for k, p in enumerate(pts) if k == 0 or np.hypot(*np.subtract(p, pts[k - 1])) > 0.05]
    # profile in the (out = Z, up = Y) plane, extruded across X; post face on Z = 0
    prof = cq.Workplane("YZ").polyline([(v, u) for u, v in pts]).close().extrude(WEDGE_W / 2, both=True)
    body = prof
    for v in (-(WEDGE_L / 2 + v0) / 2, (WEDGE_L / 2 + v0) / 2):
        body = body.cut(cyl(0, v, -5, 45, M5_CLEAR)).cut(cyl(0, v, TAB_T - 2.5, 40, M5_HEAD))
    for x in (EAR_X, -EAR_X):
        p0 = c + n * 2.0
        drill = (cq.Workplane(cq.Plane(origin=(x, p0[1], p0[0]), xDir=(1, 0, 0),
                                       normal=(0, -n[1], -n[0])))
                 .circle(M3_PILOT / 2).extrude(12.0))
        body = body.cut(drill)
    # a slot key on the back: 6 mm rib into the post's T-slot, so the wedge can't twist
    key = cq.Workplane("XY").rect(5.6, WEDGE_L - 30).extrude(-1.6)
    body = body.union(key)
    return body


def foot(yaw_deg, corner_xy, overhead=False):
    """Square foot for a post. Its two outer edges sit flush with the topper's corner edges, so
    the post lands at the same spot every time; the socket is turned so one post face points at
    the target (or along the boom). The corner facing the arm is cut off to stay outside the
    fingertips' reach. Three countersunk wood screws hold it to the plywood."""
    import cadquery as cq
    s = FOOT_MM
    depth = 70.0 if overhead else 50.0
    plate = cq.Workplane("XY").rect(s, s).extrude(SOCKET_FLOOR).edges("|Z").fillet(6)
    ow = SOCK + 2 * 4.5
    sock = cq.Workplane("XY").rect(ow, ow).extrude(SOCKET_FLOOR + depth)
    for k in range(4):
        g = (cq.Workplane("XZ").polyline([(ow / 2 - 0.5, SOCKET_FLOOR), (s / 2 - 4, SOCKET_FLOOR),
                                           (ow / 2 - 0.5, SOCKET_FLOOR + depth * 0.7)]).close()
             .extrude(2.5, both=True).rotate((0, 0, 0), (0, 0, 1), 90 * k))
        sock = sock.union(g)
    sock = sock.rotate((0, 0, 0), (0, 0, 1), yaw_deg)
    body = plate.union(sock)
    inner = (cq.Workplane("XY").workplane(offset=SOCKET_FLOOR).rect(SOCK, SOCK)
             .extrude(depth + 1).rotate((0, 0, 0), (0, 0, 1), yaw_deg))
    body = body.cut(inner)
    body = body.cut(cyl(0, 0, 0, SOCKET_FLOOR, M5_CLEAR))  # optional M5 into the post's end bore
    for k in (0, 1):  # two M5 screws through adjacent socket walls into T-nuts
        a = math.radians(yaw_deg + 90 * k + 180)
        z = SOCKET_FLOOR + depth * 0.55
        o = (math.cos(a) * ow / 2, math.sin(a) * ow / 2, z)
        drill = cq.Workplane(cq.Plane(origin=o, xDir=(-math.sin(a), math.cos(a), 0),
                                      normal=(-math.cos(a), -math.sin(a), 0))).circle(M5_CLEAR / 2).extrude(6)
        body = body.cut(drill)
    w = -np.sign(corner_xy) / math.sqrt(2)  # toward the arm
    cut_at = s / math.sqrt(2) - 28.0  # from the post axis
    chop = (cq.Workplane("XY").box(200, 200, 300).translate((100 + cut_at, 0, 0))
            .rotate((0, 0, 0), (0, 0, 1), math.degrees(math.atan2(w[1], w[0]))))
    body = body.cut(chop)
    q = s / 2 - 9.0
    for x, y in ((q, q), (-q, q), (q, -q), (-q, -q)):  # #8 / 4 mm countersunk wood screws
        if x * w[0] + y * w[1] > 0:
            continue
        cone = cq.Solid.makeCone(2.25, 4.75, 2.5, cq.Vector(x, y, SOCKET_FLOOR - 2.5))
        body = body.cut(cyl(x, y, 0, SOCKET_FLOOR, 4.5)).cut(cq.Workplane("XY").add(cone))
        body = body.cut(cyl(x, y, SOCKET_FLOOR - 0.01, 40, 9.5))  # keep the screw head clear above
    return body


ELBOW_W, SLEEVE_X1 = SOCK + 2 * 5.0, 65.0
POST_TOP_IN_ELBOW, BOOM_FLOOR = 40.0, 58.0


def elbow():
    """Caps the overhead post and carries the boom 90 deg out from it (along +x here). The boom
    slides through, so its reach is set by sliding, then locked with two M5 screws from the top.
    Prints standing as modelled: a 45 deg knee under the sleeve, peaked socket roofs, no supports."""
    import cadquery as cq
    w = ELBOW_W
    top = BOOM_FLOOR + SOCK + SOCK / 2 + 4.0
    col = cq.Workplane("XY").center(0, 0).rect(w, w).extrude(top)
    sleeve = (cq.Workplane("XY").workplane(offset=BOOM_FLOOR - 5.0).center((SLEEVE_X1 - w / 2) / 2, 0)
              .rect(SLEEVE_X1 + w / 2, w).extrude(top - BOOM_FLOOR + 5.0))
    knee = (cq.Workplane("XZ").polyline([(w / 2 - 1, BOOM_FLOOR - 5.0), (SLEEVE_X1, BOOM_FLOOR - 5.0),
                                          (w / 2 - 1, BOOM_FLOOR - 5.0 - (SLEEVE_X1 - w / 2 + 1))]).close()
            .extrude(w / 2, both=True))
    body = col.union(sleeve).union(knee)
    # post socket from below, with a pyramid roof
    body = body.cut(cq.Workplane("XY").rect(SOCK, SOCK).extrude(POST_TOP_IN_ELBOW))
    body = body.cut(cq.Workplane("XY").workplane(offset=POST_TOP_IN_ELBOW)
                    .rect(SOCK, SOCK).workplane(offset=SOCK / 2).rect(0.2, 0.2).loft())
    # boom sleeve along x, with a peaked roof
    sl = (cq.Workplane("YZ").workplane(offset=-w)
          .polyline([(-SOCK / 2, BOOM_FLOOR), (SOCK / 2, BOOM_FLOOR), (SOCK / 2, BOOM_FLOOR + SOCK),
                     (0, BOOM_FLOOR + SOCK + SOCK / 2), (-SOCK / 2, BOOM_FLOOR + SOCK)]).close()
          .extrude(SLEEVE_X1 + 2 * w))
    body = body.cut(sl)
    for x in (0.0, SLEEVE_X1 - 12.0):
        body = body.cut(cyl(x, 0, BOOM_FLOOR + SOCK - 1, 30, M5_CLEAR))
    for k, (dx, dy) in enumerate(((-1, 0), (0, 1))):
        o = (dx * w / 2, dy * w / 2, POST_TOP_IN_ELBOW * 0.5)
        body = body.cut(cq.Workplane(cq.Plane(origin=o, xDir=(dy, -dx, 0), normal=(-dx, -dy, 0)))
                        .circle(M5_CLEAR / 2).extrude(6))
    return body


def overhead_spacer(rot_deg):
    """Flat plate under the boom's end for the overhead case. M5 x2 into the boom's bottom slot;
    the case's M3 ears are turned rot_deg from the boom so the image's long side runs along x."""
    import cadquery as cq
    t = 8.0
    body = cq.Workplane("XY").circle(38).extrude(t)
    for x in (-30.0, 30.0):  # M5 heads sit on the case side, under the case
        body = body.cut(cyl(x, 0, 0, t, M5_CLEAR)).cut(cyl(x, 0, t - 3.2, t, M5_HEAD))
    a = math.radians(rot_deg)
    for sgn in (1, -1):
        body = body.cut(cyl(sgn * EAR_X * math.cos(a), sgn * EAR_X * math.sin(a), 0, t, M3_PILOT))
    return body


def pi5_plate():
    """Raspberry Pi 5 carrier for a post or the boom: M2.5 standoffs, two M5 screws into the slot
    (counterbored under the board), so each camera's Pi rides on its own post."""
    import cadquery as cq
    t = 5.0
    body = cq.Workplane("XY").rect(94, 64).extrude(t).edges("|Z").fillet(5)
    for x, y in PI5_HOLES:
        body = body.union(cq.Workplane("XY").workplane(offset=t).center(x, y).circle(3.2).extrude(5))
    for x, y in PI5_HOLES:
        body = body.cut(cyl(x, y, 1.0, t + 5, M25_PILOT))
    for x in (-20.0, 20.0):
        body = body.cut(cyl(x, 0, 0, t, M5_CLEAR)).cut(cyl(x, 0, t - 3.2, t, M5_HEAD))
    return body


def ribbon_clip():
    """Slides into a post's T-slot from the open end and holds a camera ribbon flat on the post."""
    import cadquery as cq
    prof = [(-4.4, -3.6), (4.4, -3.6), (4.4, -2.1), (2.6, -2.1), (2.6, 1.0), (11.5, 1.0), (11.5, 4.6),
            (8.5, 4.6), (8.5, 3.6), (10.0, 3.6), (10.0, 2.4), (-10.0, 2.4), (-10.0, 3.6), (-8.5, 3.6),
            (-8.5, 4.6), (-11.5, 4.6), (-11.5, 1.0), (-2.6, 1.0), (-2.6, -2.1), (-4.4, -2.1)]
    return cq.Workplane("XY").polyline(prof).close().extrude(10.0)


def build_parts():
    """{file stem: (cadquery solid, how many, what it is)}"""
    parts = {"cam_case": (cam_case(), 3, "Camera Module 3 case, one per camera")}
    for name in ("front-right", "back-right"):
        p = pitch_of(name)
        parts[f"wedge_{name}"] = (wedge(p), 1, f"{p:.1f} deg aim block for the {name} camera")
        parts[f"foot_{name}"] = (foot(aim(name)[2], CAMERAS[name]["post"]), 1,
                                 f"foot for the {name} post")
    lens, d, boom_yaw = aim("overhead")
    parts["foot_overhead"] = (foot(boom_yaw, CAMERAS["overhead"]["post"], overhead=True), 1,
                              "foot for the overhead post")
    parts["elbow_overhead"] = (elbow(), 1, "post-to-boom elbow")
    parts["spacer_overhead"] = (overhead_spacer(boom_yaw), 1, "plate under the boom for the case")
    parts["pi5_plate"] = (pi5_plate(), 3, "Raspberry Pi 5 carrier, one per post")
    parts["ribbon_clip"] = (ribbon_clip(), 8, "ribbon clip for the T-slot")
    return parts


def print_pose(stem, solid):
    """The part as it goes on the build plate: every file is exported ready to print, no supports."""
    if stem.startswith("wedge_"):  # on its side, so the slot key and the sloped face both print
        solid = solid.rotate((0, 0, 0), (0, 1, 0), 90)
    bb = solid.val().BoundingBox()
    return solid.translate((-(bb.xmin + bb.xmax) / 2, -(bb.ymin + bb.ymax) / 2, -bb.zmin))


def export(parts, out):
    import cadquery as cq
    os.makedirs(out, exist_ok=True)
    info = {}
    for stem, (solid, n, what) in parts.items():
        solid = print_pose(stem, solid)
        cq.exporters.export(solid, os.path.join(out, f"{stem}.stl"), tolerance=0.05,
                            angularTolerance=0.1)
        cq.exporters.export(solid, os.path.join(out, f"{stem}.step"))
        bb = solid.val().BoundingBox()
        info[stem] = dict(count=n, what=what, size_mm=[round(bb.xlen, 1), round(bb.ylen, 1),
                                                       round(bb.zlen, 1)],
                          volume_cm3=round(solid.val().Volume() / 1000, 1))
    return info


# ---------------------------------------------------------------- assembly in the arm's frame
WOOD, ALU, PRINT, PCB, BLACK = (205, 170, 120), (175, 178, 185), (245, 130, 40), (40, 120, 60), (30, 30, 30)
PI_GREEN = (30, 140, 70)


def tess(solid, tol=0.3):
    v, f = solid.val().tessellate(tol, 0.4)
    return np.array([(p.x, p.y, p.z) for p in v]), np.array(f)


def box(lo, hi):
    import trimesh
    m = trimesh.creation.box(bounds=[lo, hi])
    return np.asarray(m.vertices), np.asarray(m.faces)


def frame(X, Y, Z, o):
    T = np.eye(4)
    T[:3, 0], T[:3, 1], T[:3, 2], T[:3, 3] = X, Y, Z, o
    return T


def moved(vf, T):
    v, f = vf
    return v @ T[:3, :3].T + T[:3, 3], f


def board_parts():
    """Camera Module 3 itself, in the case's frame, for the renders."""
    z0 = CASE_T + STANDOFF
    return [(box((-12.5, -13, z0), (12.5, 11, z0 + 1)), PCB),
            (box((-4.25, -4.25, z0 + 1), (4.25, 4.25, z0 + 5)), BLACK),
            (box((-3.5, -3.5, z0 + 5), (3.5, 3.5, LENS_Z_CASE)), BLACK)]


def assembly(parts, explode=0.0):
    """[(vertices, faces, rgb, tag)] in the arm's frame. explode moves the front-right head apart."""
    out = []

    def add(vf, T, rgb, tag):
        v, f = moved(vf, T)
        out.append((v, f, rgb, tag))

    mesh = {k: tess(v[0]) for k, v in parts.items()}
    for name in ("front-right", "back-right", "overhead"):
        c = CAMERAS[name]
        px, py = c["post"]
        lens, d, yaw = aim(name)
        a = math.radians(yaw)
        u, l, up = np.array([math.cos(a), math.sin(a), 0]), np.array([-math.sin(a), math.cos(a), 0]), \
            np.array([0, 0, 1.0])
        base = np.array([px, py, 0.0])
        add(mesh[f"foot_{name}"], frame([1, 0, 0], [0, 1, 0], [0, 0, 1], base), PRINT, "foot")
        add(box((-10, -10, 0), (10, 10, c["post_len"])), frame(u, l, up, base + [0, 0, SOCKET_FLOOR]),
            ALU, "post")
        if name != "overhead":
            e = explode if name == "front-right" else 0.0
            th = math.radians(pitch_of(name))
            Xw, Yw, Zw = -l, up, u  # wedge frame: across, up the post, out from the face
            Tw = frame(Xw, Yw, Zw, base + u * (EXTR / 2 + 70 * e) + [0, 0, wedge_centre_z(name)])
            add(mesh[f"wedge_{name}"], Tw, PRINT, "wedge")
            f_loc, n_loc = np.array([0, math.cos(th), math.sin(th)]), np.array([0, -math.sin(th), math.cos(th)])
            Tc = Tw @ frame([1, 0, 0], f_loc, n_loc, np.array([0, 0, WEDGE_T0]) + n_loc * 60 * e)
            add(mesh["cam_case"], Tc, PRINT, "case")
            for vf, rgb in board_parts():
                add(vf, Tc @ frame([1, 0, 0], [0, 1, 0], [0, 0, 1], [0, 0, 45 * e]), rgb, "camera")
            Tp = frame(up, l, -u, base - u * (EXTR / 2 + 60 * e) + [0, 0, c["lens_z"] - 170])
        else:
            Te = frame(u, l, up, base + [0, 0, SOCKET_FLOOR + c["post_len"] - POST_TOP_IN_ELBOW])
            add(mesh["elbow_overhead"], Te, PRINT, "elbow")
            reach = float(np.hypot(lens[0] - px, lens[1] - py))
            add(box((-ELBOW_W / 2 - 10, -10, BOOM_FLOOR), (reach + 45, 10, BOOM_FLOOR + 20)), Te, ALU, "boom")
            boom_bottom = (Te @ [0, 0, BOOM_FLOOR, 1])[2]
            Ts = frame(u, -l, -up, [lens[0], lens[1], boom_bottom])
            add(mesh["spacer_overhead"], Ts, PRINT, "spacer")
            Tc = frame([1, 0, 0], [0, -1, 0], [0, 0, -1], [lens[0], lens[1], boom_bottom - 8.0])
            add(mesh["cam_case"], Tc, PRINT, "case")
            for vf, rgb in board_parts():
                add(vf, Tc, rgb, "camera")
            Tp = Te @ frame([1, 0, 0], [0, 1, 0], [0, 0, 1], [reach * 0.45, 0, BOOM_FLOOR + 20])
        add(mesh["pi5_plate"], Tp, PRINT, "pi")
        add(box((-42.5, -28, 10), (42.5, 28, 11.6)), Tp, PI_GREEN, "pi")
        add(box((-30, -20, 11.6), (10, 20, 22)), Tp, BLACK, "pi")  # active cooler
    return out


def overhead_lens_z(parts):
    c = CAMERAS["overhead"]
    return SOCKET_FLOOR + c["post_len"] - POST_TOP_IN_ELBOW + BOOM_FLOOR - 8.0 - LENS_Z_CASE


def cameras(parts):
    """The three cameras as piper_twin Cameras (Camera Module 3 Wide, 2304 x 1296, nominal)."""
    import piper_camera_placement as pcp
    out = {}
    for name in CAMERAS:
        lens, d, _ = aim(name)
        if name == "overhead":
            lens = lens.copy()
            lens[2] = overhead_lens_z(parts)
            out[name] = pcp.look_cam(lens, lens + d * 1000, (0, -1, 0))
        else:
            out[name] = pcp.look_cam(lens, lens + d * 1000)
    return out


def clearance(items):
    """Per kind of part: how far its closest point is outside the fingertips' reach (a sphere of
    REACH_MM about J2), mm. Negative would mean the arm can touch it."""
    best = {}
    for v, f, rgb, tag in items:
        dist = np.linalg.norm(v - [0, 0, J2_Z], axis=1) - REACH_MM
        k = int(np.argmin(dist))
        if tag not in best or dist[k] < best[tag]["margin_mm"]:
            best[tag] = dict(margin_mm=round(float(dist[k]), 1), at_mm=v[k].round(0).tolist())
    return best


# ---------------------------------------------------------------- rendering
def subdivide(v, f, size=40.0):
    import trimesh
    if len(f) and np.ptp(v, axis=0).max() > size:
        v, f = trimesh.remesh.subdivide_to_size(v, f, max_edge=size, max_iter=12)
    return v, f


def render_items(cam, items, image=None, ss=2):
    """piper_twin.render's flat-shaded painter's algorithm, for many coloured meshes at once."""
    import cv2
    big = cam.scaled(cam.width * ss, cam.height * ss)
    R, t = big.R(), big.tvec
    up_cam = R @ np.array([0.0, 0.0, 1.0])
    polys, depth, cols = [], [], []
    for v, f, rgb in items:
        vc = v @ R.T + t
        tri = vc[f]
        n = np.cross(tri[:, 1] - tri[:, 0], tri[:, 2] - tri[:, 0])
        nn = np.linalg.norm(n, axis=1)
        ok = nn > 1e-9
        n[ok] /= nn[ok, None]
        cen = tri.mean(1)
        keep = ok & ((n * cen).sum(1) < 0) & (tri[:, :, 2].min(1) > 1.0)
        if not keep.any():
            continue
        uv = big.project(v).reshape(-1, 2)[f[keep]]
        view = -cen[keep] / np.linalg.norm(cen[keep], axis=1, keepdims=True)
        shade = 0.35 + 0.5 * np.clip((n[keep] * view).sum(1), 0, 1) + 0.2 * np.clip(n[keep] @ up_cam, 0, 1)
        polys.append(uv)
        depth.append(cen[keep, 2])
        cols.append(np.clip(shade[:, None] * np.array(rgb[::-1], float), 0, 255))
    canvas = (np.full((big.height, big.width, 3), 235, np.uint8) if image is None else
              cv2.resize(image, (big.width, big.height), interpolation=cv2.INTER_LINEAR))
    if polys:
        polys, depth, cols = np.concatenate(polys), np.concatenate(depth), np.concatenate(cols)
        order = np.argsort(-depth)
        pts = np.round(polys[order] * 16).astype(np.int32)
        cols = cols[order].astype(np.uint8)
        lim = 16 * 4 * max(big.width, big.height)
        for p, c in zip(pts, cols):
            if np.abs(p).max() < lim:
                cv2.fillConvexPoly(canvas, p, c.tolist(), lineType=cv2.LINE_8, shift=4)
    return cv2.resize(canvas, (cam.width, cam.height), interpolation=cv2.INTER_AREA)


def arm_items(meshes, q):
    import piper_twin as pt
    T = pt.link_poses(q)
    return [(v @ T[k][:3, :3].T + T[k][:3, 3], f, pt.TWIN_RGB) for k, (v, f) in meshes.items()]


def setup_scene():
    import piper_camera_placement as pcp
    pcp.TABLE = dict(x0=-HALF - J1_XY_MM[0], x1=HALF - J1_XY_MM[0], y0=-HALF - J1_XY_MM[1],
                     y1=HALF - J1_XY_MM[1])
    return pcp


def named_poses():
    import piper_camera_placement as pcp
    return {"rest": pcp.REST, "READY": pcp.READY,
            "toward the shelf": pcp.ik(np.array([60.0, 300.0, 300.0]), (0, 0.707, -0.707))[0],
            "table, in front": pcp.ik(np.array([380.0, -60.0, 30.0]), (0, 0, -1))[0],
            "table, room side": pcp.ik(np.array([250.0, -380.0, 40.0]), (0, -0.5, -0.866))[0],
            "far right, low": pcp.ik(np.array([560.0, 40.0, 60.0]), (0.5, 0, -0.866))[0]}


LABEL = {"front-right": "FR: front-right corner", "back-right": "BR: back-right corner",
         "overhead": "OH: overhead"}
CAM_COL = {"front-right": (30, 110, 220), "back-right": (200, 110, 20), "overhead": (30, 150, 30)}


def overview(view, pcp, fixtures, meshes, q, cams, title=None):
    import piper_twin as pt
    import cv2
    img = pcp.scene(view)
    img = render_items(view, fixtures + arm_items(meshes, q), img)
    for name, cam in cams.items():
        pcp.frustum(img, view, cam, CAM_COL[name], LABEL[name].split(":")[0], size=120)
    if title:
        pt.put_text(img, title, (10, 24), (40, 40, 40), box=(236, 236, 236))
    return img


def camera_view(cam, pcp, fixtures, meshes, q, label, w=640, h=360):
    import piper_twin as pt
    small = cam.scaled(w, h)
    img = render_items(small, fixtures + arm_items(meshes, q), pcp.scene(small))
    pt.draw_skeleton(img, small, q, thick=1)
    pt.put_text(img, label, (8, 22), scale=0.5)
    return img


def fit_view(v, w=420, h=320, direction=(1.0, -1.4, 0.9), hfov=30):
    import piper_twin as pt
    c = (v.min(0) + v.max(0)) / 2
    r = np.linalg.norm(v.max(0) - v.min(0)) / 2
    dist = r / math.tan(math.radians(hfov) / 2) * 1.15
    d = np.asarray(direction) / np.linalg.norm(direction)
    return pt.virtual_camera(w, h, hfov, c + d * dist, c)


def parts_sheet(parts, path):
    import cv2
    import piper_twin as pt
    tiles = []
    for stem, (solid, n, what) in parts.items():
        v, f = tess(print_pose(stem, solid), 0.1)
        v, f = subdivide(v, f, 15.0)
        cam = fit_view(v)
        img = render_items(cam, [(v, f, PRINT)], np.full((320, 420, 3), 250, np.uint8))
        bb = np.ptp(v, axis=0)
        pt.put_text(img, f"{stem}  x{n}  (as printed)", (8, 22), (30, 30, 30), scale=0.5,
                    box=(250, 250, 250))
        pt.put_text(img, f"{bb[0]:.0f} x {bb[1]:.0f} x {bb[2]:.0f} mm", (8, 310), (80, 80, 80),
                    scale=0.45, box=(250, 250, 250))
        tiles.append(img)
    while len(tiles) % 4:
        tiles.append(np.full((320, 420, 3), 250, np.uint8))
    rows = [np.hstack(tiles[k:k + 4]) for k in range(0, len(tiles), 4)]
    cv2.imwrite(path, np.vstack(rows), [cv2.IMWRITE_JPEG_QUALITY, 90])


def static_items(parts, explode=0.0, size=40.0):
    return [subdivide(v, f, size) + (rgb,) for v, f, rgb, tag in assembly(parts, explode)]


def render_all(parts, out, animate=False):
    import cv2
    import piper_twin as pt
    pcp = setup_scene()
    meshes = pt.load_meshes()
    cams = cameras(parts)
    for name, cam in cams.items():
        cam.scaled(4608, 2592).save(os.path.join(out, f"camera_{name}.json"),
                                    note=CAMERAS[name]["where"] + " (nominal, from the CAD; "
                                    "calibrate after mounting)")
    fixtures = static_items(parts)
    named = named_poses()
    view = pt.virtual_camera(1600, 1000, 52, (2100, -2500, 1650), (0, 40, 430))
    img = overview(view, pcp, fixtures, meshes, named["toward the shelf"], cams,
                   "4 x 4 ft topper, J1 at its centre; red circle: fingertip reach at table height")
    cv2.imwrite(os.path.join(out, "overview.jpg"), img, [cv2.IMWRITE_JPEG_QUALITY, 90])
    top = pt.virtual_camera(1000, 1000, 4.2, (0, -1, 25000), (0, 0, 0))  # nearly orthographic
    img = overview(top, pcp, fixtures, meshes, named["rest"], cams, "plan view")
    cv2.imwrite(os.path.join(out, "plan.jpg"), img, [cv2.IMWRITE_JPEG_QUALITY, 90])
    show = ["rest", "toward the shelf", "table, in front", "table, room side"]
    rows = []
    for name, cam in cams.items():
        rows.append(np.hstack([camera_view(cam, pcp, fixtures, meshes, named[k], f"{LABEL[name]}: {k}")
                               for k in show]))
    cv2.imwrite(os.path.join(out, "views.jpg"), np.vstack(rows), [cv2.IMWRITE_JPEG_QUALITY, 88])
    parts_sheet(parts, os.path.join(out, "parts.jpg"))
    head_closeups(parts, out, pcp, meshes)
    if animate:
        tour_video(os.path.join(out, "views.mp4"), pcp, fixtures, meshes, cams, named)
        assembly_video(os.path.join(out, "assembly.mp4"), parts, pcp, meshes)


def head_closeups(parts, out, pcp, meshes):
    """Each camera's mount, seen from the arm's side."""
    import cv2
    import piper_twin as pt
    items = static_items(parts, size=20.0)
    imgs = []
    for name in ("front-right", "back-right", "overhead"):
        lens, d, yaw = aim(name)
        a = math.radians(yaw)
        u, l = np.array([math.cos(a), math.sin(a), 0]), np.array([-math.sin(a), math.cos(a), 0])
        px, py = CAMERAS[name]["post"]
        if name == "overhead":
            mid = np.array([(px + lens[0]) / 2, (py + lens[1]) / 2, overhead_lens_z(parts) + 20])
            eye, tgt, title = mid - l * 900 + [0, 0, -260], mid + [0, 0, -40], "overhead: post top, elbow, boom, Pi, camera"
        else:
            tgt = np.array([px, py, CAMERAS[name]["lens_z"] - 60]) + u * 10
            eye, title = tgt + u * 420 + l * 260 + [0, 0, 130], f"{name}: camera and Pi on the post"
        cam = pt.virtual_camera(640, 480, 44, eye, tgt)
        img = render_items(cam, items + arm_items(meshes, pcp.REST), pcp.scene(cam))
        pt.put_text(img, title, (8, 22), (30, 30, 30), scale=0.5, box=(236, 236, 236))
        imgs.append(img)
    cv2.imwrite(os.path.join(out, "heads.jpg"), np.hstack(imgs), [cv2.IMWRITE_JPEG_QUALITY, 90])


_TOUR = {}


def _tour_frame(item):
    import piper_twin as pt
    label, q = item
    g = _TOUR
    tiles = [camera_view(cam, g["pcp"], g["fixtures"], g["meshes"], q, LABEL[n])
             for n, cam in g["cams"].items()]
    tiles.append(overview(g["view"], g["pcp"], g["fixtures"], g["meshes"], q, g["cams"]))
    frame = np.vstack([np.hstack(tiles[:2]), np.hstack(tiles[2:])])
    bar = np.full((36, frame.shape[1], 3), 30, np.uint8)
    pt.put_text(bar, f"DIGITAL TWIN (simulated)   {label}", (10, 25), scale=0.55, box=None)
    return np.vstack([bar, frame])[:, :, ::-1]


def tour_video(path, pcp, fixtures, meshes, cams, named, fps=8):
    import multiprocessing as mp
    import imageio.v2 as imageio
    import piper_twin as pt
    order = ["rest", "READY", "toward the shelf", "READY", "table, in front", "far right, low",
             "table, room side", "READY", "rest"]
    frames = pcp.tour(named, order, move_s=1.6, hold_s=0.4, fps=fps)
    _TOUR.update(pcp=pcp, fixtures=fixtures, meshes=pt.load_meshes(faces_per_mesh=1500), cams=cams,
                 view=pt.virtual_camera(640, 360, 56, (2100, -2500, 1650), (0, 40, 430)))
    writer = imageio.get_writer(path, fps=fps, codec="libx264", quality=8, macro_block_size=8)
    with mp.get_context("fork").Pool(max(1, os.cpu_count())) as pool:
        for img in pool.imap(_tour_frame, frames, chunksize=2):
            writer.append_data(img)
    writer.close()
    pt.mp4_to_gif(path, path.replace(".mp4", ".gif"), speed=1.5, width=960)


def assembly_video(path, parts, pcp, meshes, fps=12):
    """The front-right head going together: wedge onto the post, case onto the wedge, camera in."""
    import imageio.v2 as imageio
    import piper_twin as pt
    lens, d, yaw = aim("front-right")
    a = math.radians(yaw)
    u, l = np.array([math.cos(a), math.sin(a), 0]), np.array([-math.sin(a), math.cos(a), 0])
    px, py = CAMERAS["front-right"]["post"]
    tgt = np.array([px, py, CAMERAS["front-right"]["lens_z"] - 50]) + u * 40
    cam = pt.virtual_camera(800, 600, 42, tgt + u * 480 + l * 330 + [0, 0, 160], tgt)
    base = pcp.scene(cam)
    writer = imageio.get_writer(path, fps=fps, codec="libx264", quality=8, macro_block_size=8)
    steps = list(np.linspace(1, 0, 36)) + [0.0] * 14
    for k, e in enumerate(steps):
        e = float(pcp.min_jerk(e)) if 0 < e < 1 else e
        items = static_items(parts, explode=e, size=15.0)
        img = render_items(cam, items + arm_items(meshes, pcp.REST), base.copy())
        pt.put_text(img, "front-right head: wedge on the post, case on the wedge, camera in the case",
                    (8, 22), (30, 30, 30), scale=0.5, box=(236, 236, 236))
        writer.append_data(img[:, :, ::-1])
    writer.close()
    pt.mp4_to_gif(path, path.replace(".mp4", ".gif"), speed=1.0, width=640)


def score(n_poses=300):
    """Fingertip visibility and triangulation for the chosen layout and a few alternatives."""
    import piper_camera_placement as pcp
    import piper_twin as pt
    meshes = pt.load_meshes()
    poses = pcp.sample_poses(n_poses)
    k = HALF - POST_IN
    alt = {"FL350": pcp.look_cam((-k, -k, 350), TARGET), "FR500": pcp.look_cam((k, -k, 500), TARGET),
           "BR350": pcp.look_cam((k, k, 350), TARGET), "OH-centre": pcp.look_cam((0, -75, 1200), (0, -75, 0), (0, 1, 0))}
    chosen = cameras(None)
    cams = dict(chosen, **alt)
    names, cl = list(cams), list(cams.values())
    seen, mmpx, tips = pcp.evaluate(cl, poses, meshes)

    def sc(sel):
        idx = [names.index(s) for s in sel]
        errs, n2 = [], 0
        for i in range(len(poses)):
            use = [cl[j] for j in idx if seen[i, j]]
            n2 += len(use) >= 2
            errs.append(pcp.tri_error(use, tips[i]))
        errs = np.array(errs)
        fin = errs[np.isfinite(errs)]
        return dict(cameras=sel, seen_by_2plus_pct=round(100 * n2 / len(poses), 1),
                    seen_by_any_pct=round(100 * float(seen[:, idx].any(1).mean()), 1),
                    median_err_mm=round(float(np.median(fin)), 2) if len(fin) else None,
                    within_2mm_pct=round(100 * float((errs <= 2).mean()), 1))
    combos = [["overhead", "front-right", "back-right"], ["OH-centre", "front-right", "back-right"],
              ["overhead", "front-right", "BR350"], ["overhead", "FR500", "back-right"],
              ["overhead", "front-right", "FL350"], ["front-right", "back-right"],
              ["overhead", "front-right"], ["overhead", "back-right"]]
    return dict(n_poses=n_poses, pixel_noise_px=pcp.PX_SIGMA,
                per_camera={n: round(100 * float(seen[:, j].mean()), 1) for j, n in enumerate(names)},
                layouts=[sc(c) for c in combos])


def summary(parts, info, out, scores=None):
    items = assembly(parts)
    clr = clearance(items)
    cams = {}
    for name, c in CAMERAS.items():
        lens, d, yaw = aim(name)
        if name == "overhead":
            lens = lens.copy()
            lens[2] = overhead_lens_z(parts)
        cams[name] = dict(where=c["where"], post_centre_mm=[round(x, 1) for x in c["post"]],
                          post_length_mm=c["post_len"], lens_mm=lens.round(1).tolist(),
                          view_dir=d.round(3).tolist(), post_yaw_deg=round(yaw, 1),
                          from_J2_mm=round(float(np.linalg.norm(lens - [0, 0, J2_Z]))))
        if name != "overhead":
            cams[name].update(pitch_down_deg=round(pitch_of(name), 1),
                              wedge_centre_height_mm=round(wedge_centre_z(name), 1),
                              target_mm=list(c["target"]))
        else:
            cams[name].update(boom_from_post_axis_to_lens_mm=round(float(np.hypot(
                lens[0] - c["post"][0], lens[1] - c["post"][1]))))
    res = dict(frame="arm base frame, mm; x the way the arm faces at J1 = 0, y toward the wall, "
                     "z up from the topper; J1 at the topper's centre",
               topper_mm=TOPPER_MM, reach_from_J2_mm=REACH_MM, cameras=cams, parts=info,
               outside_reach_by=clr)
    if scores:
        res["scores"] = scores
    json.dump(res, open(os.path.join(out, "summary.json"), "w"), indent=1)
    return res


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--out", default="docs/issue-24/camera-fixtures")
    ap.add_argument("--render", action="store_true", help="figures (needs the twin's meshes)")
    ap.add_argument("--animate", action="store_true", help="also views.mp4/gif and assembly.mp4/gif")
    ap.add_argument("--score", type=int, default=0, help="score the layout on this many arm poses")
    args = ap.parse_args()
    import sys
    sys.path.insert(0, HERE)
    parts = build_parts()
    info = export(parts, os.path.join(args.out, "parts"))
    scores = score(args.score) if args.score else None
    old = os.path.join(args.out, "summary.json")
    if scores is None and os.path.exists(old):
        scores = json.load(open(old)).get("scores")
    if not args.animate and args.render:  # keep the videos' frames from going stale silently
        print("note: --render without --animate leaves views.mp4 / assembly.mp4 as they were")
    print(json.dumps(summary(parts, info, args.out, scores), indent=1))
    if args.render:
        render_all(parts, args.out, args.animate)
