"""High-fidelity printed parts for the auger swap (issue #42, second round on PR #44).

* ``fixture_*``: the finger fixture: two thin forks on both faces of the tap collar, so the
  collar can't tip, each with a U-slot the Ø25 tube passes through, and a ledge on each
  fork that is the collar's own lower outline (taken from its STEP), so the collar sits
  coaxial with the slots and can't roll. Round 3 dropped the axis from 75 to 35 mm above
  the board (the custom tools lower their carriage first) and cut it to 25 cm3.
* ``sleeve_*``: the stock-finger sleeve as two printed shells: a main shell (blue in the
  photo on PR #44) on the grip face with the tube cradle, and a fixturing shell (green)
  over the back. Four M3 countersunk screws, two at each arrow, pass beside the finger into
  heat-set inserts in the green shell. Both shells are cut from AgileX's own finger
  (agilex.py), so they follow the 2 mm step in the grip face, the tapered sides and the
  curved back, and those lock them on.
* ``custom_finger``: a minimal finger that replaces the stock one: it bolts to the MGN7C
  carriage (4 x M2 x 8) and takes the linkage arm's M3 shoulder screw (heat-set insert).
* ``pin_*``: the tilt-lock slider for Alternative A: a printed bar in a printed guide, with
  a Ø25 knob the cradles grip like the auger tube and a compliant latch (a cantilever in the
  bar) that clicks into a window in the guide's roof and holds the slider out.

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
F1_T, F2_T = 6.0, 6.0                       # outlet-side and gear-side forks (F2 leaves 8.9 mm to the gear)
SLOT_W = 25.5                               # Ø25 tube passes, the collar (R16.75 and up) can't
TINE = 7.5                                  # fork material either side of the slot
FIX_HALF_W = SLOT_W / 2 + TINE              # forks are x = FIX_X -/+ 20.25
FORK_TOP = FIX_Z + 12.0                     # covers the collar's ring face up to where the slot clears it
MOUTH = (3.5, 5.0)                          # lead-in: the slot opens 3.5 mm a side over the top 5 mm
LEDGE = 4.5                                 # nest ledge on each fork's inner face, under the collar's ends
NEST_WALL_TOP = FIX_Z - 5.0                 # ledge top beside the ring (where the collar's own outline is higher)
NEST_CLEAR = 0.25
BASE_T = 4.0                                # plate between the ledges, 2 x M4 countersunk wood screws
FIX_SCREW_X = 11.0


def _collar_envelope(step: float = 0.5):
    """Lowest point of the tap collar + solenoid at each x (doser frame, axis at x = 0), so
    the nest can be the collar's own underside, open upward. The ring, the lug at x 11..20
    and the tab at -X run the collar's whole length, so every y slice has this outline."""
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
    """Everything above the collar's underside (offset NEST_CLEAR), between the forks."""
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
    """Fork plate y0..y0+t standing on the board: a U-slot the tube drops into, a 3.5 mm
    lead-in at the top and a tine either side. lead_side +1/-1 puts a 2 mm conical lead-in
    on the +Y/-Y face of the slot for the new auger's tip."""
    w, half = FIX_HALF_W, SLOT_W / 2
    mx, mz = MOUTH
    pts = [(FIX_X - w, 0.0), (FIX_X + w, 0.0), (FIX_X + w, FORK_TOP - 1.5), (FIX_X + w - 1.5, FORK_TOP),
           (FIX_X - w + 1.5, FORK_TOP), (FIX_X - w, FORK_TOP - 1.5)]
    f = cq.Workplane("XZ").polyline(pts).close().extrude(-t).translate((0, y0, 0))
    slot = (cq.Workplane("XZ").center(FIX_X, FIX_Z).circle(half).extrude(-t - 2).translate((0, y0 - 1, 0))
            .union(cq.Workplane("XY").box(SLOT_W, t + 2, 40, centered=(True, False, False)).translate((FIX_X, y0 - 1, FIX_Z))))
    mouth = cq.Workplane("XZ").polyline([(FIX_X - half, FORK_TOP - mz), (FIX_X - half - mx, FORK_TOP + 0.01),
                                         (FIX_X + half + mx, FORK_TOP + 0.01), (FIX_X + half, FORK_TOP - mz)]) \
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


def fixture_ys():
    """(F1 outer, F1 inner, F2 inner, F2 outer) faces along y."""
    y_f1 = COLLAR_Y[0] - FORK_GAP - F1_T
    y_f2 = COLLAR_Y[1] + FORK_GAP
    return y_f1, y_f1 + F1_T, y_f2, y_f2 + F2_T


def finger_fixture_hifi() -> cq.Workplane:
    """Two 6 mm forks, a 4.5 mm ledge on each fork's inner face that is the collar's own
    underside (so the collar can't roll and its bore sits on the slots' axis), and a 4 mm
    plate between the ledges with the two M4 screws, under where the collar sits. The old
    auger drops in with the collar between the forks; pulling it toward the cap strips the
    collar against F2. The new auger goes in outlet first through F2's lead-in, the collar
    and F1, and lifts out with the collar on it. Prints base-down with no supports."""
    y1o, y1i, y2i, y2o = fixture_ys()
    w = FIX_HALF_W
    body = _fork(y1o, F1_T, +1).union(_fork(y2i, F2_T, +1))
    cav = fixture_nest_cavity()
    for ya, yb in ((y1i - 0.01, y1i + LEDGE), (y2i - LEDGE, y2i + 0.01)):
        ledge = (cq.Workplane("XY").box(2 * w, yb - ya, NEST_WALL_TOP, centered=False)
                 .translate((FIX_X - w, ya, 0.0)).cut(cav))
        body = body.union(ledge)
    plate = cq.Workplane("XY").box(2 * w, y2i - y1i - 2 * LEDGE + 0.02, BASE_T, centered=False) \
        .translate((FIX_X - w, y1i + LEDGE - 0.01, 0.0))
    for sx in (-1, 1):
        plate = plate.cut(cs_hole(BASE_T + 1, 4.5, 9.0).rotate((0, 0, 0), (1, 0, 0), 180)
                          .translate((FIX_X + sx * FIX_SCREW_X, (y1i + y2i) / 2, BASE_T)))
    body = body.union(plate)
    # the tube's own channel, in case the collar sits high
    body = body.cut(cq.Workplane("XZ").center(FIX_X, FIX_Z).circle(SLOT_W / 2).extrude(-(y2i - y1i) - 0.2)
                    .translate((0, y1i - 0.1, 0)))
    return body.edges("|Z").edges("<Y or >Y").fillet(1.0) if False else body


# ------------------------------------------------------------------ tilt-lock slider (Alt A)
# A printed slider in a printed guide on the board beside the doser. Pushed in (-X), its tip
# lies 0.5 mm over the +X edge of the mounting-plate floor (x = 34), so the plate can't tip
# up while the arm pulls; pulled out, a compliant latch in the slider clicks into a window
# in the guide's roof and holds it there against the doser's vibration. The gripper moves it
# by a Ø25 knob, the auger tube's size, that its cradles wrap exactly as they wrap the tube.
PIN_Y = G.PIN_Y                   # slider centre plane (W y), over the rear of the floor
PIN_X_OUT, PIN_X_IN = G.PIN_X_OUT, G.PIN_X_IN   # tip out (latched) / in (16 mm over the floor)
STROKE_PIN = PIN_X_OUT - PIN_X_IN               # 22
BAR_W, BAR_Z0 = 8.0, G.FLOOR_Z + 0.5            # bar 8 wide, its underside 0.5 mm over the floor top
BAR_Z1 = BAR_Z0 + 10.0
BAR_L = 61.0                      # tip to the far end of the post
POST_U = (53.0, 61.0)             # post (bar -> knob), from the tip
KNOB_U = sum(POST_U) / 2          # knob axis, from the tip
BAR_Z = 47.0                      # Ø25 knob axis (W z): the custom fingers' finger plate clears the rear clip
KNOB_Y = (-BAR_W / 2, 32.0)       # knob along +Y from the slider's -Y face (y from PIN_Y)
KNOB_WALL, KNOB_END = 3.0, 3.0    # cup: 3 mm wall, closed at the post end, open at the free end
KNOB_FREE_Y = BAR_W / 2 + 2.0     # cradles go on the knob from here (2 mm past the post): 26 mm free
# latch: a beam cut into the bar's top, root toward the post, a bump on its free end
LATCH_U = 21.5                    # bump's -X base, from the tip
LATCH_L, LATCH_T, LATCH_SLOT = 20.0, 2.0, 1.5
BUMP_H, BUMP_RAMP, BUMP_HOOK, BUMP_TOP = 1.3, 40.0, 15.0, 0.65
# guide
GUIDE_X = (38.0, 69.0)
GUIDE_CLEAR, GUIDE_WALL, GUIDE_ROOF = 0.25, 3.0, 3.0
WEB_HALF, WEB_Z = 3.0, 8.0        # I-section below the tunnel
GUIDE_TAB = (38.0, 47.0)          # screw tabs at the -X end (the end the pin's load lifts)
GUIDE_SCREW_DY = 11.0
PET_E, PET_MU = 2000.0, 0.3       # PETG, printed along the beam (MPa), PETG on PETG


def _bump_pts():
    """Bump profile (u from the tip, z) on the beam's top: -X face a BUMP_RAMP ramp (the
    push-in unlatch), +X face undercut BUMP_HOOK deg (pulling out hooks it into the window)."""
    u0, z0, h = LATCH_U, BAR_Z1, BUMP_H
    run = h / math.tan(math.radians(BUMP_RAMP))
    top1 = u0 + run + BUMP_TOP
    return [(u0, z0), (u0 + run, z0 + h), (top1, z0 + h), (top1 - h * math.tan(math.radians(BUMP_HOOK)), z0)]


def knob_grip_y(sleeves: bool) -> float:
    """Gripper centre (W y) on the knob: the lower finger is the upper one turned 180 deg, so
    the pair reaches the same distance either way; both start 0.5 mm past KNOB_FREE_Y."""
    xs = SL_X if sleeves else CF_X
    return PIN_Y + KNOB_FREE_Y + 0.5 + max(A.AX_X - xs[0], xs[1] - A.AX_X)


def pin_slider(deflect: float = 0.0) -> cq.Workplane:
    """One PETG print, laid on its -Y face (the bar, beam and post are in the layer plane,
    so the latch beam flexes along its layers and the knob prints as an upright cup).
    Frame: tip at x = 0, y = 0 on the slider's centre plane (W y = PIN_Y), z = W z.
    deflect > 0 draws the latch beam pressed down that far at the bump, as it is under the
    guide's roof with the slider pushed in (turned about its root, which is close enough)."""
    hw = BAR_W / 2
    z0, z1 = BAR_Z0, BAR_Z1
    zk = BAR_Z - G.TUBE_R
    prof = [(0.0, z0 + 1.5), (2.6, z0), (POST_U[1], z0), (POST_U[1], zk + 3.0), (POST_U[0], zk + 3.0),
            (POST_U[0], z1), (1.0, z1), (0.0, z1 - 1.0)]
    body = cq.Workplane("XZ").polyline(prof).close().extrude(hw, both=True)
    # latch beam: slot under the bar's top, slit at the bump end, rounded root
    ub, ur = LATCH_U, LATCH_U + LATCH_L
    zs0, zs1 = z1 - LATCH_T - LATCH_SLOT, z1 - LATCH_T
    slot = cq.Workplane("XZ").polyline([(ub - 0.6, zs0), (ur, zs0), (ur, zs1), (ub, zs1), (ub, z1 + 1), (ub - 0.6, z1 + 1)]) \
        .close().extrude(hw + 1, both=True)
    root = cq.Workplane("XZ").center(ur, (zs0 + zs1) / 2).circle(LATCH_SLOT / 2 + 0.15).extrude(hw + 1, both=True)
    body = body.cut(slot).cut(root)
    bump = cq.Workplane("XZ").polyline(_bump_pts()).close().extrude(hw, both=True)
    body = body.union(bump)
    if deflect:
        zone = cq.Workplane("XY").box(ur - ub, BAR_W + 2, z1 + BUMP_H + 1 - zs1, centered=(False, True, False)).translate((ub, 0, zs1))
        beam = body.intersect(zone)
        top_u = _bump_pts()[2][0]                  # the bump top's far corner must drop by `deflect`
        ang = math.degrees(math.atan2(deflect + 0.05, ur - top_u))
        body = body.cut(zone).union(beam.rotate((ur, 0, (zs1 + z1) / 2), (ur, 1, (zs1 + z1) / 2), -ang))
    # knob: Ø25 cup along +Y on the post, the auger tube's size
    ku = KNOB_U
    knob = cq.Workplane("XZ").center(ku, BAR_Z).circle(G.TUBE_R).extrude(-(KNOB_Y[1] - KNOB_Y[0])).translate((0, KNOB_Y[0], 0))
    knob = knob.faces(">Y").edges().chamfer(1.0)
    cup = (cq.Workplane("XZ").center(ku, BAR_Z).circle(G.TUBE_R - KNOB_WALL)
           .extrude(-(KNOB_Y[1] - KNOB_Y[0] - KNOB_END) - 1).translate((0, KNOB_Y[0] + KNOB_END, 0)))
    return body.union(knob.cut(cup))


def pin_guide() -> cq.Workplane:
    """PETG print, base-down: a tunnel the slider's bar runs in (0.25 mm a side), an I-section
    web under it, a roof with the latch window, and two M4 countersunk wood screws in tabs
    at the -X end. In W (built in place)."""
    x0, x1 = GUIDE_X
    c, wl, rf = GUIDE_CLEAR, GUIDE_WALL, GUIDE_ROOF
    ti, tz0, tz1 = BAR_W / 2 + c, BAR_Z0 - c, BAR_Z1 + c
    bo = ti + wl
    top = tz1 + rf
    sec = [(-WEB_HALF, 0.0), (WEB_HALF, 0.0), (WEB_HALF, WEB_Z), (bo, WEB_Z + bo - WEB_HALF), (bo, top),
           (-bo, top), (-bo, WEB_Z + bo - WEB_HALF), (-WEB_HALF, WEB_Z)]
    g = cq.Workplane("YZ").polyline(sec).close().extrude(x1 - x0).translate((x0, PIN_Y, 0))
    g = g.cut(cq.Workplane("XY").box(x1 - x0 + 2, 2 * ti, tz1 - tz0, centered=(False, True, False)).translate((x0 - 1, PIN_Y, tz0)))
    # window for the bump (latched position): -X edge chamfered to the bump's ramp, +X wall
    # leaning to match its hook; the bump sits with 0.1 mm to the hook wall, 0.4 mm to the ramp
    b = [(PIN_X_OUT + u, z) for u, z in _bump_pts()]
    tr = math.tan(math.radians(BUMP_RAMP))
    th = math.tan(math.radians(BUMP_HOOK))
    xr = b[0][0] + (tz1 - b[0][1]) / tr - 0.4          # ramp at the roof underside, less the play
    xh = b[3][0] + (tz1 - b[3][1]) * th + 0.1          # hook face at the roof underside, plus the play
    win = [(xr, tz1 - 0.01), (xh, tz1 - 0.01), (xh + (top - tz1) * th + 0.01, top + 0.01),
           (xr + 1.0 / tr, top + 0.01), (xr + 1.0 / tr, tz1 + 1.0)]
    g = g.cut(cq.Workplane("XZ").polyline(win).close().extrude(ti, both=True).translate((0, PIN_Y, 0)))
    # lead-in under the roof's +X end, for the bump when the slider goes in
    g = g.cut(cq.Workplane("XZ").polyline([(x1 - 1.2 / tr, tz1 - 0.01), (x1 + 0.01, tz1 - 0.01), (x1 + 0.01, tz1 + 1.2)])
              .close().extrude(ti, both=True).translate((0, PIN_Y, 0)))
    # screw tabs
    tab = cq.Workplane("XY").box(GUIDE_TAB[1] - GUIDE_TAB[0], 2 * (GUIDE_SCREW_DY + 5.0), 4.0, centered=(False, True, False)) \
        .translate((GUIDE_TAB[0], PIN_Y, 0)).edges("|Z").fillet(3.0)
    g = g.union(tab)
    xs = sum(GUIDE_TAB) / 2
    for sy in (-1, 1):
        g = g.cut(cs_hole(5.0, 4.5, 9.0).rotate((0, 0, 0), (1, 0, 0), 180).translate((xs, PIN_Y + sy * GUIDE_SCREW_DY, 4.0)))
    return g


def latch_numbers() -> dict:
    """Cantilever latch (beam fixed at its root, bump at the free end), PETG."""
    b, t, L = BAR_W, LATCH_T, LATCH_L
    I = b * t ** 3 / 12
    d = BUMP_H - GUIDE_CLEAR                       # deflection to pass under the roof
    P = 3 * PET_E * I * d / L ** 3                 # bump on the roof (N)
    eps = 1.5 * t * d / L ** 2
    a = math.radians(BUMP_RAMP)
    F = P * (math.tan(a) + PET_MU) / (1 - PET_MU * math.tan(a))
    Fslide = PET_MU * P
    stop = 1.5 * t * LATCH_SLOT / L ** 2          # strain if pressed to the slot floor
    return dict(deflection=d, bump_force=P, strain=eps, unlatch=F, slide=Fslide, strain_bottomed=stop)
