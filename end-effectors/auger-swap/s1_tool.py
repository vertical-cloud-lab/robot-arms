"""High-fidelity CadQuery model of Strategy 1: the two-servo auger-swap end effector that
replaces the PiPER's stock gripper (issue #42, PR #44).

    python s1_tool.py        # clearance check, parts + mass list, cad/s1_two_servo_tool.step

Frames (unchanged from geometry.py, so animate.py poses these parts like the old ones):

* **E**: origin on the PiPER J6 flange face, +z towards the arm; the tool hangs below z = 0.
  Over the doser E is world-aligned: E (x, y, z) = W (x, y + GRIP_Y, z + FLANGE_Z).
* **Carriage**: E @ T(0, 0, HOOK_Z + STROKE - s), s in [0, STROKE]; origin on the hook centre,
  which is the auger axis when the carriage is down (s = STROKE).
* **Hook**: carriage frame rotated about +Y by -th about (HOOK_PIVOT x, 0, HOOK_PIVOT z).
* **Pinion**: its own frame (axis = local z), placed by ``pinion_pose(s)``.

The jaw, finger and leg contacts are geometry.py's; everything around them is new:

* Lift: Feetech STS3215 (12 V C018) in the fixed frame, 18T m1 involute pinion on its horn,
  m1 rack on the carriage, carriage on an MGN9H miniature rail on leg A's wall.
* Hook: a second STS3215 on the carriage, coaxial with the hook pivot (direct drive through a
  6 mm D-shaft in two F686ZZ bearings), because the pull-out load opens the hook with
  F x 20 mm about the pivot (0.8 N m at 40 N), far beyond a micro servo.
* Electronics: Raspberry Pi 5 + Active Cooler on the +X side, HQ Camera + 6 mm CS lens and
  Camera Module 3 Wide on a pod at the +X/-Y corner looking at the jaw, Waveshare Bus Servo
  Adapter (A) on leg A's outer face, Pololu D36V50F5 (12 V -> 5 V 5 A) on the deck.

Dimensions and sources are listed next to each purchased part below.
"""
from __future__ import annotations

import math
import sys
from pathlib import Path

import cadquery as cq
import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import geometry as G  # noqa: E402

GRIP_Y, FLANGE_Z, HOOK_Z, STROKE = G.GRIP_Y, G.FLANGE_Z, G.HOOK_Z, G.STROKE
PX, PZ = G.HOOK_PIVOT
OUT = HERE / "cad"

# colours
PRINT_RED = (0.85, 0.22, 0.20)      # fixed frame (as in the issue sketch)
PRINT_DGREEN = (0.05, 0.40, 0.22)   # carriage
PRINT_GREEN = (0.10, 0.62, 0.35)    # hook jaw
PRINT_GREY = (0.30, 0.30, 0.33)     # pods, plates
SERVO_BLUE = (0.15, 0.30, 0.75)
STEEL = (0.62, 0.64, 0.68)
ALU = (0.78, 0.79, 0.82)
BLACK = (0.08, 0.08, 0.09)
BRASS = (0.80, 0.65, 0.25)
PCB_GREEN = (0.05, 0.45, 0.20)
PCB_BLUE = (0.10, 0.25, 0.55)


# ============================================================================ helpers
def box(x0, x1, y0, y1, z0, z1) -> cq.Workplane:
    return cq.Workplane("XY").box(x1 - x0, y1 - y0, z1 - z0, centered=False).translate((x0, y0, z0))


def rbox(x0, x1, y0, y1, z0, z1, r: float, sel: str = "|Z") -> cq.Workplane:
    """Box with its `sel` edges filleted (falls back to sharp if OCC refuses)."""
    b = box(x0, x1, y0, y1, z0, z1)
    try:
        f = b.edges(sel).fillet(r)
        if f.val().isValid():
            return f
    except Exception:
        pass
    return b


def W(shape) -> cq.Workplane:
    return cq.Workplane("XY").add(shape)


def cyl(d, p0, axis, length) -> cq.Workplane:
    return W(cq.Solid.makeCylinder(d / 2, length, cq.Vector(*p0), cq.Vector(*axis)))


def cyl_x(d, x0, x1, y, z):
    return cyl(d, (x0, y, z), (1, 0, 0), x1 - x0)


def cyl_y(d, y0, y1, x, z):
    return cyl(d, (x, y0, z), (0, 1, 0), y1 - y0)


def cyl_z(d, z0, z1, x=0.0, y=0.0):
    return cyl(d, (x, y, z0), (0, 0, 1), z1 - z0)


def cone(d0, d1, p0, axis, length):
    return W(cq.Solid.makeCone(d0 / 2, d1 / 2, length, cq.Vector(*p0), cq.Vector(*axis)))


def prism(pts, z0, z1) -> cq.Workplane:
    """Vertical prism over a 2D outline, wound so the solid's volume is positive."""
    pts = [(float(x), float(y)) for x, y in pts]
    area = sum(x0 * y1 - x1 * y0 for (x0, y0), (x1, y1) in zip(pts, pts[1:] + pts[:1]))
    if area < 0:
        pts = pts[::-1]
    face = cq.Face.makeFromWires(cq.Wire.makePolygon([cq.Vector(x, y, z0) for x, y in pts], close=True))
    sol = cq.Solid.extrudeLinear(face, cq.Vector(0, 0, z1 - z0))
    if sol.Volume() < 0:
        sol = cq.Solid(sol.wrapped.Reversed())
    return W(sol)


def union_all(parts) -> cq.Workplane:
    out = None
    for p in parts:
        out = p if out is None else out.union(p)
    return out


def cut_all(base, cuts) -> cq.Workplane:
    for c in cuts:
        base = base.cut(c)
    return base


def T(t=(0, 0, 0), R=None) -> np.ndarray:
    M = np.eye(4)
    if R is not None:
        M[:3, :3] = R
    M[:3, 3] = t
    return M


def rot(axis, deg) -> np.ndarray:
    a = np.asarray(axis, float)
    a = a / np.linalg.norm(a)
    c, s = math.cos(math.radians(deg)), math.sin(math.radians(deg))
    K = np.array([[0, -a[2], a[1]], [a[2], 0, -a[0]], [-a[1], a[0], 0]])
    return np.eye(3) + s * K + (1 - c) * K @ K


def about(axis, deg, point) -> np.ndarray:
    p = np.asarray(point, float)
    return T(p) @ T(R=rot(axis, deg)) @ T(-p)


def loc(M: np.ndarray) -> cq.Location:
    from OCP.gp import gp_Trsf
    tr = gp_Trsf()
    tr.SetValues(*M[0, :4], *M[1, :4], *M[2, :4])
    return cq.Location(tr)


def place(wp: cq.Workplane, M: np.ndarray) -> cq.Workplane:
    """Move a part by a 4x4 (rigid) transform."""
    shp = solid_of(wp).moved(loc(M))
    return W(shp)


def solid_of(wp) -> cq.Shape:
    vals = wp.vals() if isinstance(wp, cq.Workplane) else [wp]
    vals = [v for v in vals if isinstance(v, cq.Shape)]
    return vals[0] if len(vals) == 1 else cq.Compound.makeCompound(vals)


def frame_from_axes(origin, x, y, z) -> np.ndarray:
    M = np.eye(4)
    M[:3, 0], M[:3, 1], M[:3, 2], M[:3, 3] = x, y, z, origin
    return M


def look_at(origin, target, up=(0, 0, 1)) -> np.ndarray:
    """Camera-board frame: local -z looks at the target (PR #10 convention: optical axis -Z,
    PCB front face at z = 0), local +y is image up (as close to `up` as possible)."""
    o, t = np.asarray(origin, float), np.asarray(target, float)
    f = (t - o) / np.linalg.norm(t - o)
    z = -f
    u = np.asarray(up, float)
    y = u - z * u.dot(z)
    y /= np.linalg.norm(y)
    x = np.cross(y, z)
    return frame_from_axes(o, x, y, z)


# ============================================================================ purchased parts
# ---- Feetech STS3215 serial bus servo ----------------------------------------------------
# Feetech STS3215 spec A/0 (2020-04-10) and the 1:1 Waveshare drawing "SCS215" (ST3215-2D.zip):
#   case 45.2 x 24.7 x 35; spline axis 10.11 from the output-end face, centred in W;
#   29 between top and bottom faces at the output end, main body 32 (+1.5 each side), 35 overall
#   (raised top band +2.6, bottom pad -3.4, both estimates off the drawing); 25T spline OD 5.9,
#   3.4 proud; rear idler boss O6 x 4.1; stock horn O19.2, 4 x O2.52 on a 14 PCD + O3.2 centre,
#   underside +2.2, top +4.7; B-PA2.0 self-tapping holes (O1.59) at 8.30 / 29.00 (top face) and
#   8.30 / 32.76 (bottom face) from the axis, +/-10.25 across; two 5264 sockets through the
#   bottom, block ~6.4 x 21.4 centred 14.1 from the axis; 55 g.
# Local frame: origin on the output axis at the 29 mm "top" face, case along +x, output +z.
STS = dict(L=45.2, Wd=24.7, ax=10.11, top_holes=(8.30, 29.00), bot_holes=(8.30, 32.76), hole_y=10.25,
           horn_d=19.2, horn_pcd=14.0, horn_z=(2.2, 4.7), spline_d=5.9, spline_h=3.4, mass=55.0)


def sts3215_case() -> cq.Workplane:
    L, Wd, a = STS["L"], STS["Wd"], STS["ax"]
    x0, x1 = -a, L - a
    end = rbox(x0, x0 + 17.0, -Wd / 2, Wd / 2, -29.0, 0.0, 2.0)            # output end: 29 tall
    main = rbox(x0 + 16.0, x1, -Wd / 2, Wd / 2, -30.5, 1.5, 2.0)          # main body: 32 tall
    band = rbox(x0 + 21.0, x1 - 1.0, -Wd / 2 + 1.0, Wd / 2 - 1.0, 1.4, 2.6, 1.0)   # raised top band (clear of the horn)
    pad = rbox(x0 + 16.0, x1 - 1.0, -Wd / 2 + 1.0, Wd / 2 - 1.0, -32.4, -30.4, 1.0)  # bottom pad
    boss_top = cyl_z(12.0, -0.01, 1.2)                                     # bearing boss round the spline
    rear = cyl_z(6.0, -33.1, -28.9)                                         # rear idler boss
    case = union_all([end, main, band, pad, boss_top, rear])
    holes = []
    for hx in STS["top_holes"]:
        for sy in (-1, 1):
            holes.append(cyl_z(1.6, -6.0, 3.0, hx, sy * STS["hole_y"]))
    for hx in STS["bot_holes"]:
        for sy in (-1, 1):
            holes.append(cyl_z(1.6, -34.0, -27.0, hx, sy * STS["hole_y"]))
    holes.append(box(14.1 - 3.2, 14.1 + 3.2, -10.7, 10.7, -33.0, -27.5))  # 2 x 5264 sockets (open)
    return cut_all(case, holes)


def sts3215_output() -> cq.Workplane:
    """Spline + stock round horn (turns with the output)."""
    z0, z1 = STS["horn_z"]
    spline = cyl_z(STS["spline_d"], 1.2, STS["spline_h"])
    horn = cyl_z(STS["horn_d"], z0, z1).union(cyl_z(8.0, 1.2, z0))
    r = STS["horn_pcd"] / 2
    cuts = [cyl_z(2.52, z0 - 1, z1 + 1, r * math.cos(math.radians(a)), r * math.sin(math.radians(a)))
            for a in (45, 135, 225, 315)]
    cuts.append(cyl_z(3.2, z0 - 1, z1 + 1))
    return cut_all(horn, cuts).union(spline)


# ---- HIWIN MGN9H miniature guide (rail + block) --------------------------------------------
# HIWIN MG series catalogue, MGN9H: W 20, L 39.9, H 10 (rail base to block top), H1 2, rail
# 9 x 6.5 (WR x HR), block 4 x M3 on B 15 x C 16, rail M3 holes O3.5 / cbore O6 x 3.5 at P 20,
# block 26 g, rail 0.38 kg/m.  Local frame: rail base on z = 0, rail along +x from x = 0,
# block centred on x = 0, mounting face at z = H.
MGN = dict(W=20.0, L=39.9, H=10.0, H1=2.0, WR=9.0, HR=6.5, B=15.0, C=16.0, P=20.0)


def mgn9_rail(length: float, e: float = 5.0) -> cq.Workplane:
    r = rbox(0, length, -MGN["WR"] / 2, MGN["WR"] / 2, 0, MGN["HR"], 0.5, "|X")
    for sy in (-1, 1):   # ball grooves
        r = r.cut(cyl_x(1.6, -1, length + 1, sy * MGN["WR"] / 2, MGN["HR"] - 1.6))
    xs = np.arange(e, length, MGN["P"])
    for x in xs:
        r = r.cut(cyl_z(3.5, -1, MGN["HR"] + 1, x, 0)).cut(cyl_z(6.0, MGN["HR"] - 3.5, MGN["HR"] + 1, x, 0))
    return r


def mgn9_block() -> cq.Workplane:
    L, Wb, H, H1 = MGN["L"], MGN["W"], MGN["H"], MGN["H1"]
    body = rbox(-L / 2 + 3.5, L / 2 - 3.5, -Wb / 2, Wb / 2, H1, H, 0.6, "|X")
    caps = rbox(-L / 2, L / 2, -Wb / 2 + 1.0, Wb / 2 - 1.0, H1 + 0.5, H - 0.5, 0.5, "|X")
    blk = body.union(caps)
    blk = blk.cut(box(-L / 2 - 1, L / 2 + 1, -MGN["WR"] / 2 - 0.4, MGN["WR"] / 2 + 0.4, 0, MGN["HR"] + 0.3))
    for sx in (-1, 1):
        for sy in (-1, 1):
            blk = blk.cut(cyl_z(2.5, H - 4, H + 1, sx * MGN["C"] / 2, sy * MGN["B"] / 2))
    return blk


# ---- F686ZZ flanged ball bearing: 6 x 13 x 5, flange O15 x 1.1 (ISO 15 / JIS B 1512) ------
def f686zz() -> cq.Workplane:
    """Local frame: axis +z, flange on z in [0, 1.1], ring down to z = -3.9."""
    ring = cyl_z(13.0, -3.9, 1.1).union(cyl_z(15.0, 0.0, 1.1))
    return ring.cut(cyl_z(6.0, -5, 3)).cut(cyl_z(10.4, 0.6, 2)).cut(cyl_z(10.4, -5, -3.4))


# ---- socket head cap screw heads (ISO 4762), countersunk heads (ISO 10642) ---------------
def shcs_head(d_head=5.5, k=3.0) -> cq.Workplane:
    """Head only, local: seats on z = 0, head along +z, hex socket on top."""
    h = cyl_z(d_head, 0, k)
    hexa = cq.Workplane("XY").polygon(6, 2.5 / math.cos(math.pi / 6)).extrude(1.6).translate((0, 0, k - 1.6))
    return h.cut(hexa)


def csk_head(d_head=6.0) -> cq.Workplane:
    """90-degree countersunk head, top flush at z = 0, cone down to the shank."""
    return cone(d_head, 3.0, (0, 0, 0), (0, 0, -1), (d_head - 3.0) / 2)


# ---- involute pinion and rack, module 1, 20 deg ------------------------------------------
M_GEAR, Z_PIN, PA = 1.0, 18, 20.0
R_PITCH = M_GEAR * Z_PIN / 2      # 9.0


def involute_outline(z=Z_PIN, m=M_GEAR, pa=PA, n_inv=7):
    rp, rb = z * m / 2, z * m / 2 * math.cos(math.radians(pa))
    ra, rf = rp + m, rp - 1.25 * m
    inv = lambda a: math.tan(a) - a  # noqa: E731
    half = math.pi / (2 * z) + inv(math.radians(pa))

    def psi(r):
        return half - inv(math.acos(min(rb / r, 1.0)))
    rs = [rb + (ra - rb) * (i / n_inv) ** 1.3 for i in range(n_inv + 1)]
    pts = []
    for k in range(z):
        c = 2 * math.pi * k / z
        r0 = max(rf, 0.0)
        fl = [(r, c - psi(r)) for r in rs]
        fr = [(r, c + psi(r)) for r in reversed(rs)]
        a_b = psi(rb)
        tooth = [(r0, c - a_b)] + fl + [(ra, c)] + fr + [(r0, c + a_b)]
        nxt = c + 2 * math.pi / z - a_b
        tooth += [(rf, c + a_b + (nxt - c - a_b) * t) for t in (1 / 3, 2 / 3)]
        pts += [(r * math.cos(a), r * math.sin(a)) for r, a in tooth]
    return pts


def pinion_gear(width=6.0) -> cq.Workplane:
    """18T m1 pinion, local frame: axis +z, mid-plane z = 0; bolts to the STS3215 horn
    (4 x M2 x 8 through O2.4 holes on the horn's 14 mm PCD, centred on its O3.2 hole)."""
    g = cq.Workplane("XY").polyline(involute_outline()).close().extrude(width).translate((0, 0, -width / 2))
    g = g.cut(cyl_z(3.2, -5, 5))
    r = STS["horn_pcd"] / 2
    for a in (45, 135, 225, 315):
        g = g.cut(cyl_z(2.4, -5, 5, r * math.cos(math.radians(a)), r * math.sin(math.radians(a))))
    return g


def rack_profile(z_lo, z_hi, centres, back=4.0, m=M_GEAR, pa=PA):
    """Rack teeth along v (= z), facing +u; pitch line u = 0. Returns (u, v) points."""
    at = math.pi * m / 4 - m * math.tan(math.radians(pa))
    ar = math.pi * m / 4 + 1.25 * m * math.tan(math.radians(pa))
    pts = [(-1.25 * m - back, z_lo), (-1.25 * m, z_lo)]
    for zc in sorted(centres):
        pts += [(-1.25 * m, zc - ar), (m, zc - at), (m, zc + at), (-1.25 * m, zc + ar)]
    pts += [(-1.25 * m, z_hi), (-1.25 * m - back, z_hi)]
    return pts


# ---- Raspberry Pi 5 (from PR #10's piper_mount.py, official mechanical drawing) ----------
def pi5_local() -> cq.Workplane:
    """Board frame (u, v, w): u along the 85 mm edge toward USB/Ethernet, v along 56 mm away
    from the USB-C/HDMI edge, w up from the underside. 4 x M2.5 holes at u 3.5/61.5, v 3.5/52.5."""
    board = rbox(0, 85, 0, 56, 0, 1.6, 3.0)
    for u in (3.5, 61.5):
        for v in (3.5, 52.5):
            board = board.cut(cyl_z(2.7, -1, 3, u, v))
    top = 1.6
    comps = [box(64.0, 87.0, 2.5, 18.5, top, top + 13.5), box(69.5, 87.0, 22.5, 35.5, top, top + 16.0),
             box(69.5, 87.0, 40.5, 53.5, top, top + 16.0), box(7.0, 58.0, 50.0, 55.0, top, top + 8.5),
             box(4.0, 56.0, 12.0, 50.0, top, top + 10.0),                 # Active Cooler
             box(6.7, 15.7, -1.0, 6.5, top, top + 3.3), box(22.8, 28.8, -1.0, 6.5, top, top + 3.0),
             box(36.2, 42.2, -1.0, 6.5, top, top + 3.0), box(45.5, 48.5, 4.0, 17.0, top, top + 4.0),
             box(50.5, 53.5, 4.0, 17.0, top, top + 4.0)]
    return union_all([board] + comps)


# ---- Raspberry Pi HQ Camera (CS) + official 6 mm CS lens, Camera Module 3 Wide ----------
# From PR #10 (piper-camera-mount/cad/piper_mount.py, lenses.py): HQ board 38 x 38 x 1.4,
# 4 x M2.5 on 30 x 30, CS seat 14.43 in front of the PCB face, mount ring O36 x 5.8, housing
# O34.8; 6 mm lens O30 x 34 (4 mm thread), 53 g. CM3 Wide 25 x 23.862 x 1.12, 4 x M2 at x +/-10.5,
# lens 9.462 from the top edge, module 8.5 sq x 4.07 + O6.95 lens to 8.3.  Camera frame: optical
# axis -z, PCB front face z = 0, image up +y.
HQ_SEAT = 14.43
LENS6 = ((0.0, 12.3, 29.0), (12.3, 21.9, 29.4), (21.9, 27.3, 30.0), (27.3, 28.8, 29.0), (28.8, 30.0, 30.0))


def hq_camera_local() -> cq.Workplane:
    pcb = rbox(-19, 19, -19, 19, 0, 1.4, 1.0)
    for sx in (-15, 15):
        for sy in (-15, 15):
            pcb = pcb.cut(cyl_z(2.5, -1, 3, sx, sy))
    pcb = pcb.union(box(-10, 10, -19 + 0.55, -19 + 6.25, 1.4, 4.15))        # FPC connector
    mount = cyl_z(36.0, -HQ_SEAT, -HQ_SEAT + 5.8).union(cyl_z(34.8, -HQ_SEAT + 5.8, 0.0))
    mount = mount.union(box(-6.985, 6.985, -30.35, -16.0, -10.35, 0.0))     # tripod foot (simplified)
    mount = mount.cut(cyl_z(25.6, -HQ_SEAT - 1, -HQ_SEAT + 4.2)).cut(cyl_z(20.0, -HQ_SEAT, -0.5))  # CS thread + bore
    return pcb.union(mount)


def lens6_local() -> cq.Workplane:
    body = cyl_z(25.4, -HQ_SEAT, -HQ_SEAT + 4.0)
    for s0, s1, d in LENS6:
        body = body.union(cyl_z(d, -HQ_SEAT - s1, -HQ_SEAT - s0))
    front = -HQ_SEAT - 30.0
    return body.cut(cyl_z(22.0, front - 1, front + 2.5))


CM_W, CM_H, CM_TOP = 25.0, 23.862, 9.462


def cm3w_local() -> cq.Workplane:
    """CM3 Wide in its own frame: lens axis through (0, 0), optical axis -z."""
    bot = -(CM_H - CM_TOP)
    pcb = box(-CM_W / 2, CM_W / 2, bot, CM_TOP, 0, 1.12)
    for sx in (-10.5, 10.5):
        for y in (CM_TOP - 2.0, CM_TOP - 14.5):
            pcb = pcb.cut(cyl_z(2.2, -1, 2, sx, y))
    pcb = pcb.union(box(-10, 10, bot, bot + 5.71, 1.12, 1.12 + 2.75))
    module = box(-4.25, 4.25, -4.25, 4.25, -4.07, 0).union(cyl_z(6.95, -8.3, -4.07))
    return pcb.union(module)


# ---- small boards ---------------------------------------------------------------------------
def bus_adapter_local() -> cq.Workplane:
    """Waveshare Bus Servo Adapter (A): 42 x 33, 4 x O2.5 on 37 x 28; input 9-12.6 V (DC jack /
    screw terminal), USB-C to the Pi, two 3-pin bus sockets. Board frame: underside z = 0."""
    b = rbox(0, 42, 0, 33, 0, 1.6, 2.0)
    for u in (2.5, 39.5):
        for v in (2.5, 30.5):
            b = b.cut(cyl_z(2.5, -1, 3, u, v))
    comps = [box(30.0, 43.5, 10.0, 19.0, 1.6, 12.6),    # DC jack 5.5 x 2.1
             box(0.0, 7.5, 12.5, 21.5, 1.6, 4.8),       # USB-C
             box(12.0, 30.0, 26.0, 33.0, 1.6, 8.0),     # 2 x bus sockets
             box(14.0, 26.0, 8.0, 18.0, 1.6, 3.0)]      # USB-UART + level shifter
    return union_all([b] + comps)


def buck_local() -> cq.Workplane:
    """Pololu D36V50F5 (12 V -> 5 V, 5.5 A): 25.4 x 25.4 x 1.57, parts +6.1 / -1.8,
    3 x O2.18 holes on 21.1 x 21.1 (three corners)."""
    b = box(0, 25.4, 0, 25.4, 0, 1.57)
    for u, v in ((2.15, 2.15), (23.25, 2.15), (2.15, 23.25)):
        b = b.cut(cyl_z(2.18, -1, 3, u, v))
    comps = [box(5.0, 20.0, 5.0, 21.0, 1.57, 7.67), box(6.0, 19.0, 6.0, 19.0, -1.8, 0.0),
             box(1.0, 24.4, 23.0, 25.4, 1.57, 3.0)]
    return union_all([b] + comps)


# ============================================================================ layout numbers
# Fixed frame (E).
DECK_Z = (-16.5, -10.5)            # deck under the adapter
ADAPTER_T = 10.5                   # as the stock gripper flange (y 54.48..64.98 in its STEP)
WALL_A = (-40.0, -30.0)            # leg A wall (x); its +X face carries the rail
LEG_A_Y = (128.9 - GRIP_Y, 134.4 - GRIP_Y)          # foot on the NEMA 11 plate (geometry.py)
LEG_A_X = (-40.0, -24.0)
LEG_A_Z = 61.35 - FLANGE_Z         # NEMA 11 plate top measured on mounting-plate.step: W 61.35 (geometry.py: 61.2)
LEG_B_X, LEG_B_Y = (24.0, 34.0), (152.0 - GRIP_Y, 171.0 - GRIP_Y)
LEG_B_Z = G.FLOOR_Z - FLANGE_Z                      # -136
POST_B_X, POST_B_Y = (30.0, 42.0), (9.0, 22.0)      # leg B's column (clear of the open hook, |y| <= 8)
RAIL_Z = (-88.0, -18.0)            # 70 mm MGN9 rail, along z on the wall's +X face
BLOCK_ZC = 38.95                   # block centre, carriage frame (block z 19.0..58.9)
PIN_C = np.array([-17.0, 25.0, -54.75])   # pinion centre (E); axis along +X
RACK_Y = PIN_C[1] - R_PITCH        # rack pitch line (y = 16)
RACK_Z = (18.0, 58.0)              # rack, carriage frame
RACK_TOOTH0 = PIN_C[2] - HOOK_Z    # carriage z of the tooth on the pitch point when seated (52.0)
LIFT_SERVO_TOP_X = -24.7           # lift servo's 29 mm face (its horn top lands on the pinion at x = -20)
# Carriage frame.
P1_X, P1_Y = (-20.0, -13.0), (-12.0, 11.0)   # plate bolted to the MGN block
CHEEK_X, CHEEK_Z = (10.0, 29.0), (12.0, 40.0)
CHEEK_Y = (8.5, 13.5)
SHAFT_Y = (-15.5, 26.0)
HUB_Y = (15.5, 28.5)
HOOK_SERVO_TOP_Y = 33.2            # hook servo's 29 mm face (horn top at y 28.5)
HOOK_SERVO_TILT = 10.0             # case leans 10 deg toward +X off vertical (clears tube and Pi plate)
FINGER_Z = (-G.FINGER_DOWN, 28.0)
# Electronics (E).
PI_PLATE_X = (42.0, 45.0)
PI_STANDOFF = 5.0
PI_TOP_Z, PI_Y0 = -18.5, -8.0
CAM_ORIGIN = np.array([75.0, -55.0, -52.0])   # HQ board front face centre
CM_X = 34.0                                    # CM3 Wide beside the HQ (camera +x), lens axes level
CAM_BAR_SCREWS = ((37.5, -22.0), (42.0, -17.5))
CAM_TARGET = np.array([6.0, 0.0, -96.0])      # between the seated (-106.75) and lifted (-78.75) axis


R_RAIL = np.column_stack([(0, 0, 1), (0, -1, 0), (1, 0, 0)]).astype(float)   # rail x -> +z, height -> +x


def lift_servo_pose() -> np.ndarray:
    """STS3215 #1 in E: output axis along +X through the pinion, case upward."""
    R = np.column_stack([(0, 0, 1), (0, -1, 0), (1, 0, 0)]).astype(float)
    return T((LIFT_SERVO_TOP_X, PIN_C[1], PIN_C[2]), R)


def hook_servo_pose() -> np.ndarray:
    """STS3215 #2 in the carriage frame: output axis = hook pivot axis, pointing -Y."""
    t = math.radians(HOOK_SERVO_TILT)
    R = np.column_stack([(math.sin(t), 0, math.cos(t)), (-math.cos(t), 0, math.sin(t)), (0, -1, 0)])
    return T((PX, HOOK_SERVO_TOP_Y, PZ), R)


def pinion_pose(s: float) -> np.ndarray:
    """Pinion (local axis z) placed in E for carriage travel s (STROKE = down): local z -> +X,
    turning -d/9 rad about +X as the rack rises d = STROKE - s."""
    ang = -math.degrees((STROKE - s) / R_PITCH)
    return T(PIN_C) @ T(R=rot((0, 1, 0), 90)) @ T(R=rot((0, 0, 1), ang))


def carriage_pose(s: float) -> np.ndarray:
    return T((0, 0, HOOK_Z + STROKE - s))


def cam_pose() -> np.ndarray:
    return look_at(CAM_ORIGIN, CAM_TARGET)


# ============================================================================ fixed parts
def flange_adapter() -> cq.Workplane:
    """Aluminium 6061 copy of the stock gripper's J6 flange (AgileX_Gripper.STEP solid 4), z -10.5..0:
    O57; 6 x O3.4 holes on a O27 PCD at 15 + k*60 deg (E), 90-deg countersinks O6.72 from the tool
    side in a O40 x 7 pocket (3.5 mm web, ISO 10642 M3 x 8 into J6, as the stock flange); J6 side:
    240-deg arc recess between O44 and O55.5, 3.8 deep, full-round O5.75 ends at 30 and 270 deg,
    plus the 0.2 mm index flat at 180 deg; tool side: 4 x M3 x 5 tapped holes on a O48 PCD for the deck."""
    t = ADAPTER_T
    a = cyl_z(57.0, -t, 0.0)
    a = a.cut(cyl_z(40.0, -t - 1, -t + 7.0))
    cuts = []
    for k in range(6):
        ang = math.radians(15 + 60 * k)
        x, y = 13.5 * math.cos(ang), 13.5 * math.sin(ang)
        cuts.append(cyl_z(3.4, -t + 6.0, 1.0, x, y))
        cuts.append(cone(6.72, 3.4, (x, y, -t + 7.0), (0, 0, 1), 1.66))
    # J6-side arc recess (centre 150 deg, 240 deg span)
    ring = cyl_z(55.5, -3.8, 1.0).cut(cyl_z(44.0, -5, 2))
    gap = (cq.Workplane("XY").moveTo(0, 0)
           .lineTo(40 * math.cos(math.radians(30)), 40 * math.sin(math.radians(30)))
           .lineTo(60, 0).lineTo(40 * math.cos(math.radians(-90)), 40 * math.sin(math.radians(-90)))
           .close().extrude(10).translate((0, 0, -6)))
    arc = ring.cut(gap)
    for ang in (30, 270):
        arc = arc.union(cyl_z(5.75, -3.8, 1.0, 24.875 * math.cos(math.radians(ang)), 24.875 * math.sin(math.radians(ang))))
    cuts.append(arc)
    cuts.append(box(-28.6, -28.3, -1.9, 1.9, -4.9, 1.0))           # index flat
    for ang in (45, 135, 225, 315):
        r = 24.0
        cuts.append(cyl_z(2.5, -t - 1, -t + 5.0, r * math.cos(math.radians(ang)), r * math.sin(math.radians(ang))))
    a = cut_all(a, cuts)
    try:
        a2 = a.faces("<Z").edges("not %LINE").edges(cq.selectors.RadiusNthSelector(-1)).chamfer(0.5)
        if a2.val().isValid():
            a = a2
    except Exception:
        pass
    return a


def j6_screws() -> list:
    out = []
    for k in range(6):
        ang = math.radians(15 + 60 * k)
        x, y = 13.5 * math.cos(ang), 13.5 * math.sin(ang)
        head = csk_head(6.0).rotate((0, 0, 0), (1, 0, 0), 180).translate((x, y, -ADAPTER_T + 7.0))
        out.append(head.union(cyl_z(3.0, -ADAPTER_T + 7.0, 4.5, x, y)))
    return union_all(out)


def frame() -> cq.Workplane:
    """One PETG print (deck face on the bed, 4 perimeters, 40 % gyroid): deck + leg A wall
    (carries the rail) + leg B post + lift-servo cradle + Pi 5 plate."""
    z0, z1 = DECK_Z
    deck = rbox(-62.0, 45.0, -26.0, 50.0, z0, z1, 8.0)
    wall = rbox(WALL_A[0], WALL_A[1], LEG_A_Y[0], 11.0, LEG_A_Z, z0 + 0.5, 1.5)
    toe = box(WALL_A[1] - 0.5, LEG_A_X[1], LEG_A_Y[0], LEG_A_Y[1], LEG_A_Z, LEG_A_Z + 9.0)
    # leg B: column + foot pad on the floor (pad x 24..34 as geometry.py, kept under the open hook)
    post = rbox(POST_B_X[0], POST_B_X[1], POST_B_Y[0], POST_B_Y[1], LEG_B_Z + 3.5, z0 + 0.5, 2.0)
    pad = rbox(LEG_B_X[0], POST_B_X[1], LEG_B_Y[0], LEG_B_Y[1], LEG_B_Z, LEG_B_Z + 3.5, 1.5)
    # lift servo cradle: plate on the servo's bottom face + shelf under its output end
    sx = LIFT_SERVO_TOP_X - 32.4              # bottom pad face (x -57.1)
    cradle = rbox(sx - 4.0, sx, 12.0, 38.0, -69.0, z0 + 0.5, 1.5)
    shelf = rbox(sx - 4.0, -27.0, 13.0, 37.0, -69.0, -65.6, 1.0)
    pi_plate = rbox(PI_PLATE_X[0], PI_PLATE_X[1], -10.0, 50.0, -107.0, z0 + 0.5, 2.0)
    # ribs tying the Pi plate and the cradle to the deck
    rib_pi = (cq.Workplane("XZ").polyline([(PI_PLATE_X[0], z0), (PI_PLATE_X[0] - 12, z0), (PI_PLATE_X[0], z0 - 30)])
              .close().extrude(-4).translate((0, -10.0, 0)))
    rib_cr = (cq.Workplane("XZ").polyline([(sx, z0), (sx + 12, z0), (sx, z0 - 26)])
              .close().extrude(-3).translate((0, 38.0, 0)))
    f = union_all([deck, wall, toe, post, pad, cradle, shelf, pi_plate, rib_pi, rib_cr])
    cuts = []
    # deck -> adapter: 4 x M3 x 8 SHCS, counterbored from below
    for ang in (45, 135, 225, 315):
        x, y = 24.0 * math.cos(math.radians(ang)), 24.0 * math.sin(math.radians(ang))
        cuts += [cyl_z(3.4, z0 - 1, z1 + 1, x, y), cyl_z(6.5, z0 - 1, z0 + 3.0, x, y)]
    cuts.append(cyl_z(16.0, z0 - 1, z1 + 1))                       # cable/air hole under the adapter
    for x, y in CAM_BAR_SCREWS:                                     # camera bar: 2 x M3 x 12 from the top
        cuts += [cyl_z(3.4, z0 - 1, z1 + 1, x, y), cyl_z(6.5, z1 - 3.0, z1 + 1, x, y)]
    cuts.append(box(-58.4, -32.2, 11.6, 37.8, z1 - 2.2, z1 + 1))     # pocket for the buck's underside parts
    # lightening pockets in the deck
    for (a0, a1, b0, b1) in ((-56.0, -44.0, -20.0, 6.0), (-26.0, -14.0, 32.0, 44.0), (24.0, 38.0, 30.0, 44.0)):
        cuts.append(rbox(a0, a1, b0, b1, z0 - 1, z1 + 1, 3.0))
    # rail: 4 x M3 heat-set inserts (O4.0 x 6) in the wall's +X face
    for zz in np.arange(RAIL_Z[0] + 5.0, RAIL_Z[1], MGN["P"]):
        cuts.append(cyl_x(4.0, WALL_A[1] - 6.0, WALL_A[1] + 1, 0.0, zz))
    # bus adapter: 4 x M2.5 inserts in the wall's -X face (37 x 28 pattern)
    for (yy, zz) in BUS_HOLES:
        cuts.append(cyl_x(3.5, WALL_A[0] - 1, WALL_A[0] + 5.0, yy, zz))
    # lift servo: 4 x PA2.0 x 8 through the cradle into the bottom face, boss + connector windows
    for hx in STS["bot_holes"]:
        for sy in (-1, 1):
            y, zz = PIN_C[1] - sy * STS["hole_y"], PIN_C[2] + hx
            cuts += [cyl_x(2.4, sx - 5, sx + 1, y, zz), cyl_x(4.2, sx - 5, sx - 2.5, y, zz)]
    cuts.append(cyl_x(7.0, sx - 5, sx + 1, PIN_C[1], PIN_C[2]))
    cuts.append(box(sx - 5, sx + 1, PIN_C[1] - 11.2, PIN_C[1] + 11.2, PIN_C[2] + 14.1 - 3.6, PIN_C[2] + 14.1 + 3.6))
    # Pi 5: 4 x M2.5 inserts in the plate (standoffs are separate)
    for (yy, zz) in PI_HOLES:
        cuts.append(cyl_x(3.5, PI_PLATE_X[1] - 5.0, PI_PLATE_X[1] + 1, yy, zz))
    # leg B pad: two M3 holes for a replaceable TPU sole (optional)
    f = cut_all(f, cuts)
    return f


def _pi_frame() -> np.ndarray:
    """Pi board (u, v, w) -> E: u -> -z (USB/Ethernet end down), v -> +y, w -> +x."""
    R = np.column_stack([(0, 0, -1), (0, 1, 0), (1, 0, 0)]).astype(float)
    x0 = PI_PLATE_X[1] + PI_STANDOFF
    return T((x0, PI_Y0, PI_TOP_Z), R)


PI_HOLES = [((_pi_frame() @ np.array([u, v, 0, 1]))[1], (_pi_frame() @ np.array([u, v, 0, 1]))[2])
            for u in (3.5, 61.5) for v in (3.5, 52.5)]


def _bus_frame() -> np.ndarray:
    """Bus adapter board on leg A's -X face: (u, v, w) -> (u -> -z, v -> +y... ) facing -X."""
    R = np.column_stack([(0, 0, -1), (0, -1, 0), (-1, 0, 0)]).astype(float)
    return T((WALL_A[0] - 5.0, 10.5, -20.0), R)


BUS_HOLES = [((_bus_frame() @ np.array([u, v, 0, 1]))[1], (_bus_frame() @ np.array([u, v, 0, 1]))[2])
             for u in (2.5, 39.5) for v in (2.5, 30.5)]


def standoffs(frame_M, holes_uv, length, od=5.0, hole=2.7) -> cq.Workplane:
    out = []
    for u, v in holes_uv:
        s = cyl_z(od, -length, 0.0, u, v).cut(cyl_z(hole, -length - 1, 1, u, v))
        out.append(s)
    return place(union_all(out), frame_M)


def cam_pod() -> cq.Workplane:
    """Camera pod (PETG): plate behind the HQ Camera and the CM3 Wide (side by side), boss
    standoffs, and a bar + column that hang it from the deck's +X/-Y corner from *behind* the
    cameras, so nothing of it is in either field of view.  Built in the camera frame, in E."""
    from scipy.spatial import ConvexHull
    pod = rbox(-23.0, CM_X + 15.0, -22.0, 22.0, 6.4, 9.4, 4.0)
    bosses = [cyl_z(5.5, 1.4, 6.5, sx, sy) for sx in (-15, 15) for sy in (-15, 15)]
    cm_holes = [(CM_X + sx, y) for sx in (-10.5, 10.5) for y in (CM_TOP - 2.0, CM_TOP - 14.5)]
    bosses += [cyl_z(4.5, 1.12, 6.5, x, y) for x, y in cm_holes]
    pod = pod.union(union_all(bosses))
    for sx in (-15, 15):
        for sy in (-15, 15):
            pod = pod.cut(cyl_z(2.2, 0, 10, sx, sy))             # M2.5 self-tapping into the boss
    for x, y in cm_holes:
        pod = pod.cut(cyl_z(1.7, 0, 10, x, y))                    # M2 self-tapping
    pod = pod.cut(rbox(-11.0, 11.0, -21.0, -12.0, 6.0, 10.0, 1.0))                     # HQ ribbon slot
    pod = pod.cut(rbox(CM_X - 11.0, CM_X + 11.0, -(CM_H - CM_TOP) + 0.5, -(CM_H - CM_TOP) + 6.5, 6.0, 10.0, 1.0))
    C = cam_pose()
    pod_E = place(pod, C)
    back = C @ np.array([CM_X / 2, 0.0, 9.4, 1.0])                # behind the pod's centre
    z0, z1 = DECK_Z[0] - 6.0, DECK_Z[0]                           # bar under the deck, 2 x M3 up into it
    sq = [(back[0] + dx, back[1] + dy) for dx in (-9, 9) for dy in (-9, 9)]
    root = [(x, y) for x in (34.0, 45.0) for y in (-26.0, -14.0)]
    pts = np.array(sq + root)
    hull = pts[ConvexHull(pts).vertices]
    bar = prism(hull, z0, z1)
    w_top = cq.Wire.makePolygon([cq.Vector(back[0] + dx, back[1] + dy, z0 + 3.0) for dx, dy in
                                 ((-9, -9), (9, -9), (9, 9), (-9, 9))], close=True)
    q = [C @ np.array([CM_X / 2 + dx, dy, 9.3, 1.0]) for dx, dy in ((-12, -12), (12, -12), (12, 12), (-12, 12))]
    w_bot = cq.Wire.makePolygon([cq.Vector(*p[:3]) for p in q], close=True)
    col = W(cq.Solid.makeLoft([w_bot, w_top], True))
    for x, y in CAM_BAR_SCREWS:
        bar = bar.cut(cyl_z(4.0, z1 - 5.0, z1 + 1, x, y))             # M3 heat-set inserts (O4.0 x 5)
    return pod_E.union(bar.union(col)).clean()


def fixed_parts() -> list:
    """Everything rigid with the flange, in frame E: (name, Workplane, rgb)."""
    out = [("PiPER J6 flange adapter (Al 6061)", flange_adapter(), ALU),
           ("J6 screws 6 x M3x8 ISO 10642", j6_screws(), BLACK),
           ("Frame: deck + leg A wall + leg B post + cradles (PETG)", frame(), PRINT_RED)]
    # deck -> adapter screws
    heads = []
    for ang in (45, 135, 225, 315):
        x, y = 24.0 * math.cos(math.radians(ang)), 24.0 * math.sin(math.radians(ang))
        heads.append(shcs_head().rotate((0, 0, 0), (1, 0, 0), 180).translate((x, y, DECK_Z[0] + 3.0)))
    out.append(("Deck screws 4 x M3x8 ISO 4762", union_all(heads), BLACK))
    # rail on the wall
    rail = place(mgn9_rail(RAIL_Z[1] - RAIL_Z[0]), T((WALL_A[1], 0.0, RAIL_Z[0]), R_RAIL))
    out.append(("MGN9 rail, 70 mm (HIWIN MGNR9)", rail, STEEL))
    rh = []
    for zz in np.arange(RAIL_Z[0] + 5.0, RAIL_Z[1], MGN["P"]):
        rh.append(shcs_head().rotate((0, 0, 0), (0, 1, 0), 90).translate((WALL_A[1] + MGN["HR"] - 3.5, 0.0, zz)))
    out.append(("Rail screws 4 x M3x8 ISO 4762", union_all(rh), BLACK))
    # lift servo (case only; its horn turns with the pinion)
    out.append(("Servo 1 lift: Feetech STS3215-C018 (12 V)", place(sts3215_case(), lift_servo_pose()), SERVO_BLUE))
    # Pi 5 + standoffs
    out.append(("Raspberry Pi 5 + Active Cooler", place(pi5_local(), _pi_frame()), PCB_GREEN))
    out.append(("Pi standoffs 4 x M2.5 x 5", standoffs(_pi_frame(), [(u, v) for u in (3.5, 61.5) for v in (3.5, 52.5)], PI_STANDOFF), BRASS))
    # bus adapter + buck
    out.append(("Waveshare Bus Servo Adapter (A)", place(bus_adapter_local(), _bus_frame()), PCB_BLUE))
    out.append(("Bus adapter standoffs 4 x M2.5 x 5", standoffs(_bus_frame(), [(u, v) for u in (2.5, 39.5) for v in (2.5, 30.5)], 5.0), BRASS))
    out.append(("Pololu D36V50F5 buck 12 V -> 5 V 5.5 A", place(buck_local(), T((-58.0, 12.0, DECK_Z[1] + 0.2))), PCB_BLUE))
    # cameras
    C = cam_pose()
    out.append(("Raspberry Pi HQ Camera (CS)", place(hq_camera_local(), C), PCB_GREEN))
    out.append(("Raspberry Pi 6 mm CS lens", place(lens6_local(), C), BLACK))
    out.append(("Camera Module 3 Wide", place(cm3w_local(), C @ T((CM_X, 0, 0))), PCB_GREEN))
    out.append(("Camera pod + arm (PETG)", cam_pod(), PRINT_GREY))
    return out


# ============================================================================ carriage parts
def carriage_body() -> cq.Workplane:
    """PETG carriage (carriage frame): plate on the MGN block, saddle over the tube (its
    O26 underside is the presser that pushes a new auger into the clips), pivot cheeks with
    F686ZZ bearings, and an arm out to the hook servo's cradle."""
    p1 = rbox(P1_X[0], P1_X[1], P1_Y[0], P1_Y[1], 19.0, 58.9, 1.5, "|X")
    saddle = rbox(P1_X[1] - 0.5, 10.0, -12.0, CHEEK_Y[1], 8.0, 40.0, 2.0, "|Y")
    cheeks = [rbox(CHEEK_X[0], CHEEK_X[1], sy0, sy1, CHEEK_Z[0], CHEEK_Z[1], 3.0, "|Y")
              for sy0, sy1 in ((-CHEEK_Y[1], -CHEEK_Y[0]), (CHEEK_Y[0], CHEEK_Y[1]))]
    bridge = rbox(CHEEK_X[0], CHEEK_X[1], -CHEEK_Y[1], CHEEK_Y[1], 30.0, 40.0, 2.0, "|Y")
    arm = rbox(8.0, 29.0, CHEEK_Y[0], 30.6, 30.0, 44.0, 2.0, "|Y")
    gus = (cq.Workplane("XZ").polyline([(P1_X[1] - 0.5, 40.0), (P1_X[1] - 0.5, 57.0), (6.0, 40.0)]).close()
           .extrude(2.5, both=True))
    # cradle plate against the hook servo's top band (y 27.4..30.6), outline = case footprint
    Hs = hook_servo_pose()
    a = STS["ax"]
    plate_local = rbox(-a - 1.0, STS["L"] - a + 1.0, -STS["Wd"] / 2 - 1.0, STS["Wd"] / 2 + 1.0, 2.6, 5.8, 3.0)
    plate = place(plate_local, Hs)
    body = union_all([p1, saddle] + cheeks + [bridge, arm, gus, plate])
    cuts = [cyl_y(26.0, -20, 20, 0.0, 0.0),                               # presser: tube r 12.5 + 0.5
            box(CHEEK_X[0] - 1, CHEEK_X[1] + 1, -CHEEK_Y[0], CHEEK_Y[0], 8.0, 30.0)]   # hook slot
    # hook servo: horn hole + 4 x PA2.0 x 10 clearance holes (heads on the cradle's -Y face)
    cuts.append(place(cyl_z(23.0, 0.0, 12.0), Hs))
    for hx in STS["top_holes"]:
        for sy in (-1, 1):
            cuts.append(place(cyl_z(2.4, 0.0, 12.0, hx, sy * STS["hole_y"]), Hs))
    # F686ZZ seats: O13 x 5 bore through each cheek, flange outside
    for y0 in (-CHEEK_Y[1] - 1.0, CHEEK_Y[0] - 1.0):
        cuts.append(cyl_y(13.0, y0, y0 + 7.0, PX, PZ))
    # MGN9H block: 4 x M3 x 10 from the +X face, counterbored
    for dz in (-MGN["C"] / 2, MGN["C"] / 2):
        for sy in (-1, 1):
            cuts.append(cyl_x(3.4, P1_X[0] - 1, P1_X[1] + 1, sy * MGN["B"] / 2, BLOCK_ZC + dz))
            cuts.append(cyl_x(6.0, P1_X[1] - 3.2, P1_X[1] + 30, sy * MGN["B"] / 2, BLOCK_ZC + dz))
    # finger pocket + 2 x M3 heat-set inserts (O4.0 x 5)
    cuts.append(box(G.FINGER_X[0], P1_X[1] + 1, -G.JAW_W / 2 - 0.2, G.JAW_W / 2 + 0.2, 18.0, FINGER_Z[1] + 0.2))
    for sy in (-4.0, 4.0):
        cuts.append(cyl_x(4.0, G.FINGER_X[0] - 5.0, G.FINGER_X[0] + 0.1, sy, 23.5))
    return cut_all(body, cuts)


def finger_strip() -> cq.Workplane:
    """3 mm stainless finger (laser-cut 304), 16 wide, 2 x M3 x 8 countersunk into the plate."""
    f = rbox(G.FINGER_X[0], G.FINGER_X[1], -G.JAW_W / 2, G.JAW_W / 2, FINGER_Z[0], FINGER_Z[1], 1.0, "|X")
    try:
        f2 = f.faces("<Z").edges("|Y").chamfer(1.2)    # lead-in at the tip
        f = f2 if f2.val().isValid() else f
    except Exception:
        pass
    for sy in (-4.0, 4.0):
        f = f.cut(cyl_x(3.4, G.FINGER_X[0] - 1, G.FINGER_X[1] + 1, sy, 23.5))
        f = f.cut(cone(6.4, 3.4, (G.FINGER_X[1] + 0.01, sy, 23.5), (-1, 0, 0), 1.5))
    return f


def rack() -> cq.Workplane:
    centres = [RACK_TOOTH0 + k * math.pi * M_GEAR for k in range(-11, 3)]
    centres = [c for c in centres if RACK_Z[0] + 1.4 < c < RACK_Z[1] - 1.4]
    pts = rack_profile(RACK_Z[0], RACK_Z[1], centres, back=(RACK_Y - 1.25) - P1_Y[1])
    r = cq.Workplane("YZ").polyline([(RACK_Y + u, v) for u, v in pts]).close().extrude(6.0)
    return r.translate((P1_X[0], 0, 0))


def carriage_parts() -> list:
    """Parts rigid with the carriage, in the carriage frame."""
    out = [("Carriage (PETG)", carriage_body(), PRINT_DGREEN),
           ("Finger, 3 mm stainless", finger_strip(), STEEL),
           ("Lift rack m1, 40 mm (printed PA12 or cut steel rack)", rack(), BRASS)]
    blk = place(mgn9_block(), T((WALL_A[1], 0.0, BLOCK_ZC), R_RAIL))
    out.append(("MGN9H block", blk, STEEL))
    heads = []
    for dz in (-MGN["C"] / 2, MGN["C"] / 2):
        for sy in (-1, 1):
            heads.append(shcs_head().rotate((0, 0, 0), (0, 1, 0), -90).translate((P1_X[1] - 3.2, sy * MGN["B"] / 2, BLOCK_ZC + dz)))
    out.append(("Block screws 4 x M3x10 ISO 4762", union_all(heads), BLACK))
    for i, y0 in enumerate((-CHEEK_Y[1], CHEEK_Y[1])):     # flange on the cheek's outer face
        b = f686zz()
        M = T((PX, y0, PZ), rot((1, 0, 0), 90 if i == 0 else -90))
        out.append((f"F686ZZ bearing {i + 1}", place(b, M), STEEL))
    out.append(("Servo 2 hook: Feetech STS3215-C018 (12 V)", place(sts3215_case(), hook_servo_pose()), SERVO_BLUE))
    return out


# ============================================================================ hook parts
def hook_jaw() -> cq.Workplane:
    """PETG (or PA-CF) hook: geometry.py's jaw (HOOK_RI/RO, HOOK_ARC, JAW_W) with true arcs, the
    arm to the pivot and a O14 boss with a 6 mm D-bore; e-clips locate it between the cheeks."""
    def pol(r, deg):
        return (r * math.cos(math.radians(deg)), r * math.sin(math.radians(deg)))
    a0, a1 = G.HOOK_ARC
    am = (a0 + a1) / 2
    ro, ri, jw = G.HOOK_RO, G.HOOK_RI, G.JAW_W
    arc = (cq.Workplane("XZ").moveTo(*pol(ro, a0)).threePointArc(pol(ro, am), pol(ro, a1))
           .lineTo(*pol(ri, a1)).threePointArc(pol(ri, am), pol(ri, a0)).close()
           .extrude(jw / 2, both=True))
    top = pol(ro, a0)
    arm = (cq.Workplane("XZ").polyline([(top[0] - 4.5, top[1] - 2), (PX - 6, PZ), (PX + 6, PZ),
                                        (top[0] + 0.5, top[1] - 4)]).close().extrude(jw / 2, both=True))
    boss = cyl_y(14.0, -jw / 2, jw / 2, PX, PZ)
    h = arc.union(arm).union(boss)
    dbore = cyl_y(6.05, -jw, jw, PX, PZ).cut(box(PX - 4, PX + 4, -jw - 1, jw + 1, PZ + 2.5, PZ + 4))
    h = h.cut(dbore).cut(cyl_y(2 * G.HOOK_RI, -jw, jw, 0.0, 0.0))     # keep the arm out of the tube's O26
    try:
        h2 = h.edges("|Y").edges(cq.selectors.BoxSelector((-20, -10, -20), (20, 10, 10))).fillet(0.8)
        if h2.val().isValid():
            h = h2
    except Exception:
        pass
    return h


def hook_parts() -> list:
    """Parts that turn with the hook, in the carriage frame, unrotated (th = 0)."""
    shaft = cyl_y(6.0, SHAFT_Y[0], SHAFT_Y[1], PX, PZ).cut(box(PX - 4, PX + 4, SHAFT_Y[0] - 1, SHAFT_Y[1] + 1, PZ + 2.5, PZ + 4))
    hub = cyl_y(14.0, HUB_Y[0], HUB_Y[1] - 2.0, PX, PZ).union(cyl_y(22.0, HUB_Y[1] - 2.0, HUB_Y[1], PX, PZ))
    hub = hub.cut(cyl_y(6.05, HUB_Y[0] - 1, HUB_Y[1] + 1, PX, PZ))
    r = STS["horn_pcd"] / 2
    for ang in (45, 135, 225, 315):
        x, z = PX + r * math.cos(math.radians(ang)), PZ + r * math.sin(math.radians(ang))
        hub = hub.cut(cyl_y(2.4, HUB_Y[1] - 3.0, HUB_Y[1] + 1, x, z))
    hub = hub.cut(cyl_z(2.6, PZ, PZ + 9, PX, (HUB_Y[0] + HUB_Y[1] - 2) / 2))      # M3 set screw (tapped)
    clips = union_all([cyl_y(9.0, y, y + 0.6, PX, PZ).cut(cyl_y(5.6, y - 1, y + 2, PX, PZ))
                       for y in (-CHEEK_Y[1] - 1.9, )])
    out = [("Hook jaw (PETG)", hook_jaw(), PRINT_GREEN),
           ("Hook shaft O6 h6 D-shaft, 41.5 mm", shaft, STEEL),
           ("Horn hub (Al), M3 set screw", hub, ALU),
           ("E-clip DIN 6799 for O6", clips, BLACK),
           ("Servo 2 spline + horn", place(sts3215_output(), hook_servo_pose()), (0.85, 0.85, 0.88))]
    return out


# ============================================================================ pinion parts
def pinion_parts() -> list:
    """Parts that turn with the lift pinion, in the pinion frame (axis = local z)."""
    g = pinion_gear()
    # the servo's horn + spline sit on the -z side of the pinion (horn top face = pinion face)
    out_local = sts3215_output().translate((0, 0, -STS["horn_z"][1] - 3.0))
    screws = union_all([shcs_head(3.8, 2.0).translate((7 * math.cos(math.radians(a)), 7 * math.sin(math.radians(a)), 3.0))
                        for a in (45, 135, 225, 315)])
    return [("Lift pinion 18T m1 (brass or PA12)", g, BRASS),
            ("Servo 1 spline + horn", out_local, (0.85, 0.85, 0.88)),
            ("Pinion screws 4 x M2x8", screws, BLACK)]


# ============================================================================ assembly / export
def posed_parts(s: float = STROKE, th: float = 0.0, E: np.ndarray | None = None):
    """All parts placed in the doser frame (W) for carriage travel s and hook opening th."""
    E = T((0, GRIP_Y, FLANGE_Z)) if E is None else E
    C = E @ carriage_pose(s)
    Hm = C @ about((0, 1, 0), -th, (PX, 0, PZ))
    out = []
    for n, wp, c in fixed_parts():
        out.append((n, wp, c, E, "fixed"))
    for n, wp, c in carriage_parts():
        out.append((n, wp, c, C, "carriage"))
    for n, wp, c in hook_parts():
        out.append((n, wp, c, Hm, "hook"))
    for n, wp, c in pinion_parts():
        out.append((n, wp, c, E @ pinion_pose(s), "pinion"))
    return out


def export_step(path) -> Path:
    """Seated pose (s = STROKE, th = 0) in the doser frame, like export_step.custom_tool."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    a = cq.Assembly(name="S1 two-servo tool (high fidelity)")
    for n, wp, c, M, grp in posed_parts(STROKE, 0.0):
        a.add(solid_of(wp), name=n, loc=loc(M), color=cq.Color(*c))
    a.export(str(path))
    return path


# ============================================================================ checks
PURCHASED_G = {
    "Servo 1 lift": 55.0, "Servo 2 hook": 55.0,          # Feetech spec: 55 +/- 1 g
    "Raspberry Pi 5 + Active Cooler": 46.0 + 23.0,       # retailer 46 g + cooler ~23 g (est.)
    "Raspberry Pi HQ Camera": 42.0,                      # Waveshare listing
    "6 mm CS lens": 53.0,                                # PR #10 lenses.py
    "Camera Module 3 Wide": 4.0,
    "Waveshare Bus Servo Adapter": 16.0,
    "Pololu D36V50F5": 7.0,
    "MGN9 rail": 0.38 * 70.0,                            # 0.38 kg/m
    "MGN9H block": 26.0,
    "F686ZZ": 2.5,
}
DENS = {"PETG": 1.24e-3, "steel": 7.85e-3, "Al": 2.70e-3, "brass": 8.5e-3}   # g/mm^3


def mass_table():
    rows = []
    for grp, parts in (("fixed", fixed_parts()), ("carriage", carriage_parts()), ("hook", hook_parts()),
                       ("pinion", pinion_parts())):
        for n, wp, c in parts:
            v = solid_of(wp).Volume()
            hit = next((g for k, g in PURCHASED_G.items() if k in n), None)
            if hit is not None:
                m, how = hit, "datasheet"
            elif "(PETG)" in n or "PETG" in n:
                m, how = v * DENS["PETG"], "printed, solid"
            elif "Al" in n or "adapter" in n.lower():
                m, how = v * DENS["Al"], "Al"
            elif "brass" in n.lower() or "rack" in n.lower():
                m, how = v * (DENS["PETG"] if "rack" in n.lower() else DENS["brass"]), "printed/brass"
            elif "standoff" in n.lower():
                m, how = v * DENS["brass"], "brass"
            else:
                m, how = v * DENS["steel"], "steel"
            rows.append((grp, n, v, m, how))
    return rows


_DOSER_CACHE = {}


def _doser_solids(s_lift: float):
    """Doser solids in W. The auger (with its gear, cap, tap collar and solenoid) is raised by
    STROKE - s_lift... i.e. it rides with the hook when the carriage lifts."""
    import scene as S
    if s_lift in _DOSER_CACHE:
        return _DOSER_CACHE[s_lift]
    L = S.doser_layout()
    P = L.placements()
    up = T((0, 0, STROKE - s_lift))
    out = []
    for n in ["Mounting plate", "Stepper (NEMA 11)", "Stepper pinion", "Baseplate", "Tap collar base (AI)"]:
        rel, M = P[n]
        out.append((n, solid_of(cq.importers.importStep(str(S.doser_step(rel)))).moved(loc(M))))
    for n in ["Auger", "Auger cap", "Tap collar", "Solenoid (Adafruit 412)"]:
        rel, M = P[n]
        out.append((n + (" (lifted)" if s_lift < STROKE else ""), solid_of(cq.importers.importStep(str(S.doser_step(rel)))).moved(loc(up @ M))))
    for tag, y in zip(("front", "rear"), G.CLIP_ROWS_Y):
        M = T((0, y, G.AXIS_Z))
        for nm, wp in (("base", G.clip_base()), ("arm +X", G.clip_half(+1)), ("arm -X", G.clip_half(-1))):
            out.append((f"Clip ({tag}) {nm}", solid_of(wp).moved(loc(M))))
    _DOSER_CACHE[s_lift] = out
    return out


def _common_volume(a: cq.Shape, b: cq.Shape) -> float:
    from OCP.BRepAlgoAPI import BRepAlgoAPI_Common
    ba, bb = a.BoundingBox(), b.BoundingBox()
    if (ba.xmax < bb.xmin or bb.xmax < ba.xmin or ba.ymax < bb.ymin or bb.ymax < ba.ymin
            or ba.zmax < bb.zmin or bb.zmax < ba.zmin):
        return 0.0
    op = BRepAlgoAPI_Common(a.wrapped, b.wrapped)
    op.Build()
    if not op.IsDone():
        return float("nan")
    return cq.Shape.cast(op.Shape()).Volume()


def _min_dist(a: cq.Shape, b: cq.Shape) -> float:
    from OCP.BRepExtrema import BRepExtrema_DistShapeShape
    d = BRepExtrema_DistShapeShape(a.wrapped, b.wrapped)
    d.Perform()
    return d.Value()


def clearance_check(verbose=True):
    """Interference volumes (mm^3).  Seated (s = STROKE, hook closed): every part against the
    doser and against every other tool part.  Lifted (s = 0, hook closed, auger + collar raised
    28 mm with it): moving parts against the doser and the fixed parts.  Hook open
    (th = HOOK_OPEN_DEG) at s = STROKE, STROKE / 2 and 0 (auger seated): hook parts against
    the doser, the fixed parts and the carriage."""
    report = []
    poses = ((STROKE, 0.0, "seated, hook closed", None), (0.0, 0.0, "lifted, hook closed", ("carriage", "hook", "pinion")),
             (STROKE, G.HOOK_OPEN_DEG, "seated, hook open", ("hook",)),
             (STROKE / 2, G.HOOK_OPEN_DEG, "mid-stroke, hook open", ("hook",)),
             (0.0, G.HOOK_OPEN_DEG, "up, hook open", ("hook",)))
    for s, th, tag, movers in poses:
        doser = _doser_solids(s if th == 0.0 else STROKE)
        parts = [(n, solid_of(wp).moved(loc(M)), grp) for n, wp, c, M, grp in posed_parts(s, th)]
        test = parts if movers is None else [p for p in parts if p[2] in movers]
        hits = []
        for n, p, grp in test:
            for dn, d in doser:
                v = _common_volume(p, d)
                if v > 1e-3 or v != v:
                    hits.append((n, dn, v))
        for i, (n1, p1, g1) in enumerate(parts):
            for n2, p2, g2 in parts[i + 1:]:
                if movers is not None and not ((g1 in movers) ^ (g2 in movers)):
                    continue
                if movers is None and g1 == g2 and g1 != "fixed":
                    continue
                v = _common_volume(p1, p2)
                if v > 1e-3:
                    hits.append((n1, n2, v))
        report.append((tag, hits))
        if verbose:
            print(f"[{tag}] {len(hits)} interference(s)", flush=True)
            for h in hits:
                print(f"    {h[0]}  x  {h[1]}: {h[2]:.2f} mm^3", flush=True)
    return report


def leg_gaps():
    """Gap from each foot's underside to its landing face, measured on the doser solid."""
    import scene as S
    L = S.doser_layout()
    rel, M = L.placements()["Mounting plate"]
    plate = solid_of(cq.importers.importStep(str(S.doser_step(rel)))).moved(loc(M))
    out = {}
    for tag, (x0, x1, y0, y1, zf) in {"A (NEMA 11 plate top)": (*LEG_A_X, *LEG_A_Y, LEG_A_Z),
                                      "B (floor)": (*LEG_B_X, *LEG_B_Y, LEG_B_Z)}.items():
        foot = box(x0 + 0.5, x1 - 0.5, y0 + GRIP_Y + 0.5, y1 + GRIP_Y - 0.5, zf + FLANGE_Z, zf + FLANGE_Z + 0.2)
        out[tag] = (_min_dist(solid_of(foot), plate), _common_volume(solid_of(box(x0, x1, y0 + GRIP_Y, y1 + GRIP_Y,
                                                                                    zf + FLANGE_Z - 0.5, zf + FLANGE_Z)), plate))
    return out


def validity():
    bad = []
    for grp, parts in (("fixed", fixed_parts()), ("carriage", carriage_parts()), ("hook", hook_parts()),
                       ("pinion", pinion_parts())):
        for n, wp, c in parts:
            for v in wp.vals():
                if isinstance(v, cq.Shape) and not v.isValid():
                    bad.append((grp, n))
    return bad


if __name__ == "__main__":
    bad = validity()
    print("invalid solids:", bad or "none")
    clearance_check()
    for k, (d, v) in leg_gaps().items():
        print(f"leg {k}: gap {d:.3f} mm, overlap of a 0.5 mm layer under the foot {v:.1f} mm^3")
    rows = mass_table()
    tot = 0.0
    print(f"\n{'group':9s} {'part':58s} {'vol cm3':>8s} {'mass g':>7s}")
    for grp, n, v, m, how in rows:
        tot += m
        print(f"{grp:9s} {n:58s} {v / 1000:8.1f} {m:7.1f}  {how}")
    print(f"total {tot:.0f} g (printed parts at 100 % infill)")
    p = export_step(OUT / "s1_two_servo_tool.step")
    print("->", p, f"{p.stat().st_size / 1e6:.1f} MB")
