"""High-fidelity printed parts for the auger swap (issue #42, second round on PR #44).

* ``fixture_*``: the finger fixture, rebuilt as a nest for the tap collar between two thin
  forks. The forks sit on both faces of the collar, so the collar can't tip, and each has a
  U-slot the Ø25 tube passes through. The nest under the collar is the collar's own lower
  outline (taken from its STEP), so the collar sits coaxial with the slots and can't roll.
* ``sleeve_*``: the stock-finger sleeve as two printed shells: a main shell (blue in the
  photo on PR #44) on the grip face with the tube cradle, and a fixturing shell (green)
  over the back. Four M3 countersunk screws, two at each arrow, pass beside the finger into
  heat-set inserts in the green shell. Both shells are cut from AgileX's own finger
  (agilex.py), so they follow the 2 mm step in the grip face, the tapered sides and the
  curved back, and those lock them on.
* ``custom_finger``: a minimal finger that replaces the stock one: it bolts to the MGN7C
  carriage (4 x M2 x 8) and takes the linkage arm's M3 shoulder screw (heat-set insert).
* ``pin_*``: the tilt-lock pin for Alternative A: a Ø8 steel pin in a printed housing,
  with a ball-plunger detent and a Ø25 grab bar the cradles grip like the auger tube.

Sleeves and fingers are built in the STEP frame of agilex.py, for the +Z ("upper")
finger; agilex.lower_of() turns them into the other finger's. Fixture and pin are in the
doser's layout frame (geometry.py). Millimetres throughout.
"""
from __future__ import annotations

import math

import cadquery as cq

import agilex as A
import geometry as G

# ------------------------------------------------------------------------------- hardware
M3_CLEAR, M3_CSK_D, M3_INSERT_D, M3_INSERT_L = 3.4, 6.9, 4.0, 5.7   # Ø4.0 hole for an M3 x 5.7 insert
M2_CLEAR = 2.4


def cs_hole(depth: float, d: float = M3_CLEAR, csk: float = M3_CSK_D) -> cq.Workplane:
    """90 deg countersunk clearance hole along +Z, countersink at z = 0."""
    cone = cq.Solid.makeCone(csk / 2, 0, csk / 2, pnt=cq.Vector(0, 0, -0.01), dir=cq.Vector(0, 0, 1))
    return cq.Workplane("XY").circle(d / 2).extrude(depth).union(cq.Workplane().add(cone))


def cs_screw(length: float) -> cq.Workplane:
    """ISO 10642 M3 countersunk screw: head top at z = 0, shank along +Z, length incl. head."""
    head = cq.Solid.makeCone(6.72 / 2, 3.0 / 2, 1.86, pnt=cq.Vector(0, 0, 0), dir=cq.Vector(0, 0, 1))
    s = cq.Workplane().add(head).union(cq.Workplane("XY").circle(1.5).extrude(length).translate((0, 0, 0)))
    return s.cut(cq.Workplane("XY").polygon(6, 2.0 / math.cos(math.pi / 6)).extrude(1.2).translate((0, 0, -0.01)))


def socket_screw(d: float, length: float) -> cq.Workplane:
    """ISO 4762 socket head cap screw: underside of the head at z = 0, shank along +Z."""
    dk, k, s = {2.0: (3.8, 2.0, 1.5), 2.5: (4.5, 2.5, 2.0), 3.0: (5.5, 3.0, 2.5)}[d]
    head = cq.Workplane("XY").circle(dk / 2).extrude(k).translate((0, 0, -k))
    head = head.cut(cq.Workplane("XY").polygon(6, s / math.cos(math.pi / 6)).extrude(k * 0.6).translate((0, 0, -k - 0.01)))
    return head.union(cq.Workplane("XY").circle(d / 2).extrude(length))


def insert_m3() -> cq.Workplane:
    """Brass heat-set insert, M3 x 5.7 (Ø4.6 knurl), top face at z = 0, body along +Z."""
    body = cq.Workplane("XY").circle(2.3).extrude(M3_INSERT_L)
    for z in (1.2, 3.4):
        body = body.cut(cq.Workplane("XY").circle(2.3).circle(1.95).extrude(0.8).translate((0, 0, z)))
    return body.cut(cq.Workplane("XY").circle(1.5).extrude(M3_INSERT_L + 1).translate((0, 0, -0.5)))


def hex_nut(af: float = 5.5, m: float = 2.4, d: float = 3.0) -> cq.Workplane:
    return (cq.Workplane("XY").polygon(6, af / math.cos(math.pi / 6)).extrude(m)
            .cut(cq.Workplane("XY").circle(d / 2).extrude(m + 1).translate((0, 0, -0.5))))


def _yz(pts, x0: float, x1: float) -> cq.Workplane:
    """Polygon in the (Y, Z) plane, extruded along X from x0 to x1."""
    return cq.Workplane("YZ").polyline(pts).close().extrude(x1 - x0).translate((x0, 0, 0))


def _cradle_cut(yc: float, zc: float, r: float, z_tip: float, x0: float, x1: float, lead: float = 1.5):
    """Half-bore along X (opening toward -Z) with a 45 deg lead-in where it meets z_tip."""
    cyl = cq.Workplane("YZ").center(yc, zc).circle(r).extrude(x1 - x0 + 2).translate((x0 - 1, 0, 0))
    h = math.sqrt(r * r - (z_tip - zc) ** 2)
    h2 = math.sqrt(r * r - (z_tip + lead - zc) ** 2)
    fun = _yz([(yc - h - lead, z_tip - 1), (yc + h + lead, z_tip - 1), (yc + h + lead, z_tip),
               (yc + h2, z_tip + lead), (yc - h2, z_tip + lead), (yc - h - lead, z_tip)], x0 - 1, x1 + 1)
    return cyl.union(fun)


# ------------------------------------------------------------------- stock-finger sleeve (Alt A)
TUBE_R = G.TUBE_R
CRADLE_R = 12.6            # Ø25.2 half-bore: 0.1 mm over the Ø25 tube
SPLIT_Z = 33.11            # blue/green split plane = the pad's face over the finger's first 36 mm
SL_X = (-32.1, 16.3)       # sleeve width (along the tube), the finger's centre line is x = -7.91
SL_TOP_Y = -38.0           # blue shell's end toward the gripper
SL_OUT_Z = 28.1            # blue shell's outer face over the upper screws (5 mm thick)
SL_YC, SL_ZC = -70.0, 13.86     # cradle axis (as modelled): 7.5 mm in from the fingertip
SL_TIP_Z = SL_ZC + 1.0     # tooth/jaw faces: 2 mm gap between the two sleeves on the tube
BAND_Y = (-47.0, -70.0)    # the two arrows: screw pairs and the green shell's bands
BAND_W = 8.0
LEG_W, LEG_CLEAR = 8.0, 0.3
FIT = 0.15                 # blue on the pad; green gets 0.2


def _finger_clear(c: float, dirs) -> cq.Shape:
    f = A.finger_solid()
    out = f
    for d in dirs:
        out = out.fuse(f.translate(cq.Vector(*(c * v for v in d))))
    return out.clean()


def _finger_edges(y: float) -> tuple[float, float]:
    bb = A.finger_solid().intersect(cq.Solid.makeBox(200, 0.05, 0.05, pnt=cq.Vector(-100, y, 34.0))).BoundingBox()
    return bb.xmin, bb.xmax


def sleeve_screws() -> list[tuple[float, float, float]]:
    """(x, y, z of the countersink face) of the four M3 screws, upper arrow first."""
    out = []
    for y, z in ((BAND_Y[0], SL_OUT_Z), (BAND_Y[1], SL_ZC + CRADLE_R)):
        x0, x1 = _finger_edges(y)
        out += [(x0 - LEG_CLEAR - LEG_W / 2, y, z), (x1 + LEG_CLEAR + LEG_W / 2, y, z)]
    return out


def sleeve_main_shell() -> cq.Workplane:
    """Blue: the cradle side. Its inner face is the pad's own surface (the R51.5 bend and the
    5.1 deg ramp), so it can't slide toward the tip, and a lip over the fingertip stops it
    sliding the other way. Prints on its outer face's flat (the 5 mm web) with the cradle up."""
    yc, zc, zt = SL_YC, SL_ZC, SL_TIP_Z
    prof = [(SL_TOP_Y, SPLIT_Z), (SL_TOP_Y, SL_OUT_Z + 1.0), (SL_TOP_Y - 1.0, SL_OUT_Z),
            (-51.4, SL_OUT_Z), (-53.9, zt), (yc - CRADLE_R - 3.5, zt), (yc - CRADLE_R - 4.5, zt + 1.0),
            (yc - CRADLE_R - 4.5, SPLIT_Z - 0.1), (-84.0, 37.0), (A.TIP_Y - FIT, 37.0),
            (A.TIP_Y - FIT, SPLIT_Z)]
    blue = _yz(prof, *SL_X)
    blue = blue.edges("|X").fillet(0.8) if False else blue
    blue = blue.cut(_cradle_cut(yc, zc, CRADLE_R, zt, *SL_X))
    blue = blue.cut(cq.Workplane().add(_finger_clear(FIT, [(0, 0, -1), (1, 0, 0), (-1, 0, 0), (0, -1, 0)])))
    for x, y, z in sleeve_screws():
        blue = blue.cut(cs_hole(SPLIT_Z - z + 1).translate((x, y, z)))
    # soften the outer corners along the tube
    return blue


def sleeve_fixing_shell() -> cq.Workplane:
    """Green: two bands round the finger's back and sides at the arrows, joined by a spine
    that follows the curved back (and drops into the back's channel). The M3 screws thread
    into heat-set inserts in the band legs beside the finger. Prints back-down."""
    f = A.finger_solid()
    fc = cq.Workplane().add(_finger_clear(0.2, [(0, 0, 1), (1, 0, 0), (-1, 0, 0)]))
    t = 3.5
    parts = []
    for y in BAND_Y:
        y0, y1 = y - BAND_W / 2, y + BAND_W / 2
        top = max(f.intersect(cq.Solid.makeBox(200, 0.05, 200, pnt=cq.Vector(-100, yy, 0))).BoundingBox().zmax
                  for yy in (y0, y, y1)) + 0.2 + t
        x0, x1 = _finger_edges(y)
        box = cq.Workplane("XY").box(x1 - x0 + 2 * (LEG_CLEAR + LEG_W), BAND_W, top - SPLIT_Z, centered=False) \
            .translate((x0 - LEG_CLEAR - LEG_W, y0, SPLIT_Z))
        box = box.edges("|Y and >Z").fillet(2.0)
        parts.append(box.cut(fc))
    spine_box = cq.Workplane("XY").box(19.0, BAND_Y[0] - BAND_Y[1] + BAND_W, 30.0, centered=False) \
        .translate((A.AX_X - 9.5, BAND_Y[1] - BAND_W / 2, SPLIT_Z))
    parts.append(spine_box.intersect(cq.Workplane().add(f.translate(cq.Vector(0, 0, t + 0.2)))).cut(fc))
    shell = parts[0].union(parts[1]).union(parts[2])
    for x, y, _ in sleeve_screws():
        shell = shell.cut(cq.Workplane("XY").circle(M3_INSERT_D / 2).extrude(M3_INSERT_L + 0.8)
                          .translate((x, y, SPLIT_Z - 0.01)))
    return shell


def sleeve_hardware() -> list[tuple[str, cq.Workplane]]:
    out = []
    for i, (x, y, z) in enumerate(sleeve_screws()):
        L = 10.0 if i < 2 else 12.0
        out.append((f"M3x{L:.0f} countersunk (ISO 10642)", cs_screw(L).translate((x, y, z))))
        out.append(("M3 x 5.7 heat-set insert", insert_m3().translate((x, y, SPLIT_Z))))
    return out


def sleeve_opening() -> float:
    """Stock gripper opening (pad to pad) at which both cradles close on the tube."""
    return A.OPENING_AS_MODELLED + 2 * (A.AX_Z - SL_ZC)


def sleeve_axis_base_z() -> float:
    """Tube axis distance from the J6 face when the sleeves hold it."""
    return A.base_z_of_step_y(SL_YC)


# ------------------------------------------------------------------- custom finger (replaces stock)
CF_X = (-28.6, 3.4)        # width along the tube: covers the carriage and the linkage boss
CF_YC = -24.0              # cradle axis: 19.5 mm in front of the finger plate (stock: 73 mm)
CF_H = 26.0                # cradle axis below the carriage centre (along the travel)
CF_JAW_T = 4.5
CF_BRIDGE = 6.0            # material behind the cradle
CF_PLATE_Y = -13.52        # front face of the plate on the carriage (6 mm over the screws, as stock)


def cf_zc() -> float:
    return A.CARR_C[1] - CF_H


def custom_finger() -> cq.Workplane:
    """Minimal finger on the stock MGN7C carriage and linkage arm. Upper finger, as modelled
    (carriage centre z = 45.11). The cradle wraps 180 deg of the tube, so the pull-out force
    bears on the cradle wall instead of relying on grip friction. Prints on its side (the
    face at x = CF_X[0]) with no supports: the cradle is a horizontal arch of R12.6."""
    zc = cf_zc()
    zt = zc + 1.0
    z_top = A.CARR_Z[1] + 1.25                     # as the stock finger
    z_bridge = zc + CRADLE_R + CF_BRIDGE
    yj = CF_YC - CRADLE_R - CF_JAW_T
    prof = [(A.FINGER_BACK_Y, z_top), (A.FINGER_BACK_Y, zt), (CF_YC + CRADLE_R + 1.5, zt),
            (yj + 1.0, zt), (yj, zt + 1.0), (yj, z_bridge - 2.0), (yj + 2.0, z_bridge),
            (CF_PLATE_Y, z_bridge), (CF_PLATE_Y, z_top - 1.0), (CF_PLATE_Y + 1.0, z_top)]
    body = _yz(prof, *CF_X)
    body = body.edges("|Y").fillet(1.5)
    body = body.cut(_cradle_cut(CF_YC, zc, CRADLE_R, zt, *CF_X))
    # 1 mm locating slot over the carriage's sides, as in the stock finger
    body = body.cut(cq.Workplane("XY").box(A.SLOT_X[1] - A.SLOT_X[0], 1.0 + 0.01, 80, centered=False)
                    .translate((A.SLOT_X[0], A.CARR_FACE_Y, z_top - 79)))
    # 4 x M2 x 8 into the carriage (heads on the plate's front face)
    for x, z in A.CARR_HOLES:
        body = body.cut(cq.Workplane("XZ").center(x, z).circle(M2_CLEAR / 2).extrude(20).translate((0, A.CARR_FACE_Y + 0.5, 0)))
    # linkage arm: M3 heat-set insert for AgileX's shoulder screw, and a seat for the Ø9 spacer
    px, pz = A.PIVOT
    body = body.cut(cq.Workplane("XZ").center(px, pz).circle(M3_INSERT_D / 2).extrude(M3_INSERT_L + 0.5)
                    .translate((0, A.FINGER_BACK_Y + 0.01, 0)))
    return body


def custom_finger_hardware() -> list[tuple[str, cq.Workplane]]:
    out = []
    for x, z in A.CARR_HOLES:
        out.append(("M2x8 socket head (ISO 4762)",
                    socket_screw(2.0, 8.0).rotate((0, 0, 0), (1, 0, 0), -90).translate((x, CF_PLATE_Y, z))))
    px, pz = A.PIVOT
    out.append(("M3 x 5.7 heat-set insert", insert_m3().rotate((0, 0, 0), (1, 0, 0), 90).translate((px, A.FINGER_BACK_Y, pz))))
    return out


def custom_opening() -> float:
    """Stock-gripper opening command that puts the custom cradles on the tube (the gripper
    reads it as pad-to-pad width; with these fingers it is just a carriage position)."""
    return A.OPENING_AS_MODELLED + 2 * (A.AX_Z - cf_zc())


def custom_axis_base_z() -> float:
    return A.base_z_of_step_y(CF_YC)


# ------------------------------------------------------------------------------- finger fixture
FIX_X, FIX_Z = G.FIX_X, G.FIX_AXIS_Z       # auger axis in the fixture (W), along Y
COLLAR_Y = (79.23, 96.23)                   # tap collar (W y, same as in the doser)
GEAR_Y0 = 112.13                            # 44T gear's near face
FORK_GAP = 1.0                              # each fork to the collar face
F1_T, F2_T = 6.0, 8.0                       # outlet-side and gear-side forks (F2 leaves 6.9 mm to the gear)
SLOT_W = 25.5                               # Ø25 tube passes, the collar (R16.75 and up) can't
FORK_TOP = FIX_Z + 14.0
NEST_TOP = FIX_Z + 4.0
NEST_CLEAR = 0.25


def _collar_envelope(step: float = 0.5):
    """Lowest point of the tap collar + solenoid at each x (doser frame, axis at x = 0), so
    the nest can be the collar's own underside, open upward."""
    import scene as S
    from export_step import loc
    L = S.doser_layout()
    P = L.placements()
    shapes = []
    for n in ("Tap collar", "Solenoid (Adafruit 412)"):
        rel, M = P[n]
        c = cq.Compound.makeCompound(cq.importers.importStep(str(S.doser_step(rel))).vals())
        shapes.append(c.moved(loc(M)))
    pts = []
    x = -27.0
    while x <= 41.0:
        zs = []
        for s in shapes:
            sec = s.intersect(cq.Solid.makeBox(step, 400, 300, pnt=cq.Vector(x - step / 2, -50, -50)))
            if sec.Solids() or sec.Faces():
                try:
                    zs.append(sec.BoundingBox().zmin)
                except Exception:
                    pass
        pts.append((x, min(zs) - G.AXIS_Z if zs else None))
        x += step
    return pts


def fixture_nest_cavity() -> cq.Workplane:
    env = [(x, z) for x, z in _collar_envelope() if z is not None]
    xs = [x for x, _ in env]
    # lateral clearance: min over a +-NEST_CLEAR window
    zf = [min(z for x2, z in env if abs(x2 - x) <= NEST_CLEAR + 0.26) - NEST_CLEAR for x, z in env]
    top = 60.0
    pts = [(FIX_X + xs[0] - NEST_CLEAR, FIX_Z + top)] + [(FIX_X + x, FIX_Z + z) for x, z in zip(xs, zf)] + \
          [(FIX_X + xs[-1] + NEST_CLEAR, FIX_Z + top)]
    y0, y1 = COLLAR_Y[0] - FORK_GAP, COLLAR_Y[1] + FORK_GAP
    return cq.Workplane("XZ").polyline(pts).close().extrude(-(y1 - y0)).translate((0, y0, 0))


def _fork(y0: float, t: float, lead_side: int) -> cq.Workplane:
    """Fork plate y0..y0+t: full width at the bottom, two tines either side of the U-slot.
    lead_side +1/-1 puts a 2 mm conical lead-in on the +Y/-Y face of the slot."""
    xl, xr = FIX_X - 32.0, FIX_X + 30.0
    half = SLOT_W / 2
    tine = 9.0
    pts = [(xl, 5.0), (xr, 5.0), (xr, FIX_Z - 4), (FIX_X + half + tine, FORK_TOP - 4), (FIX_X + half + tine - 4, FORK_TOP),
           (FIX_X - half - tine + 4, FORK_TOP), (FIX_X - half - tine, FORK_TOP - 4), (xl, FIX_Z - 4)]
    f = cq.Workplane("XZ").polyline(pts).close().extrude(-t).translate((0, y0, 0))
    slot = (cq.Workplane("XZ").center(FIX_X, FIX_Z).circle(half).extrude(-t - 2).translate((0, y0 - 1, 0))
            .union(cq.Workplane("XY").box(SLOT_W, t + 2, 40, centered=(True, False, False)).translate((FIX_X, y0 - 1, FIX_Z))))
    mouth = cq.Workplane("XZ").polyline([(FIX_X - half, FORK_TOP - 6), (FIX_X - half - 6, FORK_TOP + 0.01),
                                         (FIX_X + half + 6, FORK_TOP + 0.01), (FIX_X + half, FORK_TOP - 6)]) \
        .close().extrude(-t - 2).translate((0, y0 - 1, 0))
    f = f.cut(slot).cut(mouth)
    if lead_side:
        yf = y0 + t if lead_side > 0 else y0
        cone = cq.Solid.makeCone(half + 2.0, half, 2.0, pnt=cq.Vector(FIX_X, yf + (0.01 if lead_side > 0 else -0.01), FIX_Z),
                                 dir=cq.Vector(0, -lead_side, 0))
        f = f.cut(cq.Workplane().add(cone)).cut(
            cq.Workplane("XY").box(SLOT_W + 4, 2.02, 40, centered=(True, False, False))
            .translate((FIX_X, yf - (2.0 if lead_side > 0 else 0.0) - 0.01 * lead_side, FIX_Z)))
    return f


def finger_fixture_hifi() -> cq.Workplane:
    """Base, two forks and the nest between them. The old auger drops in with the collar
    between the forks; pulling it toward the cap strips the collar against the gear-side
    fork (F2). The new auger goes in outlet first through F2's lead-in, the collar and F1,
    and lifts out with the collar on it. Prints base-down with no supports."""
    y_f1 = COLLAR_Y[0] - FORK_GAP - F1_T
    y_f2 = COLLAR_Y[1] + FORK_GAP
    base = (cq.Workplane("XY").box(80.0, y_f2 + F2_T + 8 - (y_f1 - 8), 5.0, centered=False)
            .translate((FIX_X - 41.0, y_f1 - 8, 0)).edges("|Z").fillet(6.0))
    for x in (FIX_X - 35.0, FIX_X + 33.0):
        for y in (y_f1 - 3.0, y_f2 + F2_T + 3.0):
            base = base.cut(cs_hole(6.0, 4.5, 9.0).rotate((0, 0, 0), (1, 0, 0), 180).translate((x, y, 5.0)))
    f1 = _fork(y_f1, F1_T, +1)
    f2 = _fork(y_f2, F2_T, +1)
    nest = (cq.Workplane("XY").box(62.0, y_f2 - (y_f1 + F1_T) + 0.02, NEST_TOP - 5.0, centered=False)
            .translate((FIX_X - 32.0, y_f1 + F1_T - 0.01, 5.0)))
    post = (cq.Workplane("XY").box(14.0, y_f2 - (y_f1 + F1_T) + 0.02, FIX_Z + 16.0 - 5.0, centered=False)
            .translate((FIX_X + 16.0, y_f1 + F1_T - 0.01, 5.0)))
    body = base.union(f1).union(f2).union(nest.union(post).cut(fixture_nest_cavity()))
    # the tube's own channel through the nest, in case the collar sits high
    body = body.cut(cq.Workplane("XZ").center(FIX_X, FIX_Z).circle(SLOT_W / 2).extrude(-(y_f2 - y_f1 - F1_T) - 0.2)
                    .translate((0, y_f1 + F1_T - 0.1, 0)))
    return body


# --------------------------------------------------------------------------- tilt-lock pin (Alt A)
PIN_D = 8.0                       # Ø8 h6 steel shaft
PIN_Y, PIN_Z = G.PIN_Y, G.PIN_Z
PIN_X_OUT, PIN_X_IN = G.PIN_X_OUT, G.PIN_X_IN
PIN_LEN = 96.0
HOUSING_X = (38.0, 74.0)
HANDLE_X = 70.0                   # handle (clamp + post + grab bar) from the pin tip
BAR_Z = 75.0                      # Ø25 grab bar axis, along Y: gripped like the auger tube
BAR_L = 34.0


def pin_housing_hifi() -> cq.Workplane:
    """Printed block on the board beside the doser: Ø8.2 bore for the pin just above the
    mounting-plate floor, an M6 ball plunger from the top into the pin's two detent grooves,
    and two M4 countersunk wood screws."""
    x0, x1 = HOUSING_X
    w, h = 24.0, PIN_Z + 9.0
    blk = (cq.Workplane("XY").box(x1 - x0, w, h, centered=(False, True, False)).translate((x0, PIN_Y, 0))
           .edges("|X and >Z").fillet(4.0))
    flange = (cq.Workplane("XY").box(x1 - x0, w + 24, 5.0, centered=(False, True, False)).translate((x0, PIN_Y, 0))
              .edges("|Z").fillet(4.0))
    blk = blk.union(flange)
    blk = blk.cut(cq.Workplane("YZ").center(PIN_Y, PIN_Z).circle(PIN_D / 2 + 0.1).extrude(x1 - x0 + 2).translate((x0 - 1, 0, 0)))
    xp = (x0 + x1) / 2
    blk = blk.cut(cq.Workplane("XY").circle(5.0 / 2).extrude(h).translate((xp, PIN_Y, PIN_Z)))    # M6 ball plunger, tapped
    for y in (PIN_Y - 18.0, PIN_Y + 18.0):
        blk = blk.cut(cs_hole(6.0, 4.5, 9.0).rotate((0, 0, 0), (1, 0, 0), 180).translate((xp, y, 5.0)))
    return blk


def pin_rod() -> cq.Workplane:
    """Ø8 x 96 steel pin, tip (chamfered) at x = 0, two detent grooves for the ball plunger."""
    r = cq.Workplane("YZ").circle(PIN_D / 2).extrude(PIN_LEN).faces("<X").chamfer(1.0)
    xp = (HOUSING_X[0] + HOUSING_X[1]) / 2
    for x in (xp - PIN_X_IN, xp - PIN_X_OUT):
        r = r.cut(cq.Workplane("YZ").circle(PIN_D / 2 + 1).circle(PIN_D / 2 - 0.8).extrude(2.0).translate((x - 1.0, 0, 0)))
    return r


def pin_handle() -> cq.Workplane:
    """Clamp on the pin (M3 pinch screw), a post up to a Ø25 x 34 grab bar along Y. The bar
    is the auger tube's size, so the sleeves and the custom fingers grip it in their cradles
    and push/pull along the finger travel, against the cradle walls. Frame: pin tip at x = 0."""
    hub = cq.Workplane("XY").box(16.0, 16.0, 16.0).translate((HANDLE_X, 0, 0)).edges("|X").fillet(3.0)
    post = cq.Workplane("XY").box(12.0, 12.0, BAR_Z - PIN_Z, centered=(True, True, False)).translate((HANDLE_X, 0, 0))
    bar = cq.Workplane("XZ").center(HANDLE_X, BAR_Z - PIN_Z).circle(G.TUBE_R).extrude(BAR_L / 2, both=True)
    bar = bar.faces("|Y").chamfer(1.0) if False else bar
    h = hub.union(post).union(bar)
    h = h.cut(cq.Workplane("YZ").circle(PIN_D / 2 + 0.1).extrude(30).translate((HANDLE_X - 15, 0, 0)))
    h = h.cut(cq.Workplane("XY").box(16.2, 1.2, 9.0, centered=(True, True, False)).translate((HANDLE_X, 0, -9.0)))
    h = h.cut(cq.Workplane("XZ").center(HANDLE_X, -5.0).circle(1.7).extrude(10, both=True))
    return h
