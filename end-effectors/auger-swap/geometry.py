"""Medium-fidelity CAD for the PiPER auger swap on the powder doser (issue #42).

Everything is built with CadQuery in millimetres.  Two frames are used:

* **World (W)**: the powder doser's own layout frame from
  vertical-cloud-lab/powder-doser ``cad/full-assembly/onshape/layout.py``: Z up, z = 0 on the
  baseplate underside (= top of the board it is screwed to), auger axis along +Y at x = 0,
  z = 43.25, outlet at y = 33.8, cap at y = 283.8, hinge along X at (y, z) = (45.4, 43.25).
  The stepper (NEMA 11) is on the -X side.
* **Tool (E)**: origin on the PiPER flange face, +z towards the arm (so the tool hangs
  below z = 0 when it points down).  E is world-aligned when the tool is over the doser,
  so a part drawn at E (x, y, z) sits at W (x, y + GRIP_Y, z + FLANGE_Z) there.

Parts are kept deliberately simple (boxes, plates, arcs, pins): enough to check
clearances, reach and the order of operations, not printable designs.
"""
from __future__ import annotations

import math

import cadquery as cq

# ----------------------------------------------------------------------------- doser numbers
AXIS_Z = 43.25            # auger axis height (W)
OUTLET_Y = 33.8           # auger outlet (W)
AUGER_LEN = 250.0
TUBE_R = 12.5             # Ø25 tube
GEAR_FROM_OUTLET = 83.33  # 44T gear centre
COLLAR_FROM_OUTLET = (45.43, 62.43)   # tap collar body along the auger
FLOOR_Z = 14.0            # mounting-plate floor top
CLIP_ROWS_Y = (103.73, 169.4)          # where the old split clamps stood (front, rear)
STEPPER_PLATE_TOP = 61.2  # top of the NEMA 11 plate (x -50..-14, y 128.7..134.7)
STEPPER_FACE_X = -18.0    # stepper body: x -46..-18, y 134.7..179.7, z 29.2..57.2

# ----------------------------------------------------------------------------- compliant clip
CLIP_W = 10.0             # along the auger
CLIP_RI, CLIP_T = 12.55, 2.0
CLIP_MOUTH = 17.0         # opening at the lips (narrower than the Ø25 tube: it snaps)
FLARE_LEN, FLARE_DEG = 7.0, 35.0       # funnel lips, angle from vertical
MOUTH_HALF_DEG = math.degrees(math.asin(CLIP_MOUTH / 2 / CLIP_RI))      # 42.6°
LIP_Z = CLIP_RI * math.cos(math.radians(MOUTH_HALF_DEG))               # 9.24 above axis


def _pts_arc(r, a0, a1, n=24):
    """Points on a circle about the clip axis, angles in degrees from +X (CCW, XZ plane)."""
    return [(r * math.cos(math.radians(a0 + (a1 - a0) * i / n)),
             r * math.sin(math.radians(a0 + (a1 - a0) * i / n))) for i in range(n + 1)]


def clip_half(side: int) -> cq.Workplane:
    """One spring arm of the C-clip (side +1 = +X), as a closed profile in the XZ plane
    about the auger axis, extruded CLIP_W along Y and centred on y = 0.  Includes the
    funnel lip.  The arm is what bends when the auger snaps in or out."""
    ro = CLIP_RI + CLIP_T
    lip_a = 90 - MOUTH_HALF_DEG
    outer = _pts_arc(ro, -90.0, lip_a)
    inner = _pts_arc(CLIP_RI, lip_a, -90.0)
    d = (math.sin(math.radians(FLARE_DEG)), math.cos(math.radians(FLARE_DEG)))
    tip_in = (CLIP_MOUTH / 2, LIP_Z)
    tip_out = outer[-1]
    flare = [(tip_out[0] + FLARE_LEN * d[0], tip_out[1] + FLARE_LEN * d[1]),
             (tip_in[0] + FLARE_LEN * d[0], tip_in[1] + FLARE_LEN * d[1])]
    prof = outer + flare + inner
    wp = cq.Workplane("XZ").polyline(prof).close().extrude(CLIP_W / 2, both=True)
    return wp if side > 0 else wp.mirror("YZ")


def clip_base() -> cq.Workplane:
    """Stem and screw-down foot of the clip (the part that does not bend)."""
    ro = CLIP_RI + CLIP_T
    stem_top = -ro + 1.5
    foot_z = FLOOR_Z - AXIS_Z                 # floor, relative to the auger axis
    stem = (cq.Workplane("XY").box(12, CLIP_W, stem_top - (foot_z + 4), centered=(True, True, False))
            .translate((0, 0, foot_z + 4)))
    foot = (cq.Workplane("XY").box(30, CLIP_W + 2, 4, centered=(True, True, False))
            .translate((0, 0, foot_z))
            .faces(">Z").workplane().pushPoints([(-10, 0), (10, 0)]).hole(3.4))
    return stem.union(foot)


# ----------------------------------------------------------------------------- finger fixture
FIX_X = 150.0             # fixture slot centre (W)
FIX_AXIS_Z = 75.0         # auger axis when the auger lies in the fixture
FORK_FROM_OUTLET = (64.5, 70.5)   # fork plate sits between the collar and the 44T gear
FORK_SLOT = 26.5          # wide enough for the Ø25 tube, far too narrow for the collar
FIX_OUTLET_Y = OUTLET_Y   # the auger lies in the fixture at the same y as in the doser


def finger_fixture() -> cq.Workplane:
    """Fork ("fingers") + collar cradle, in world coordinates.  The tube drops into the
    open-top slot; pulling the auger towards the cap strips the collar, which stays in
    the cradle on the outlet side of the fork, coaxial with the slot, ready for the next
    auger to be pushed back through it."""
    y0 = FIX_OUTLET_Y + FORK_FROM_OUTLET[0]
    t = FORK_FROM_OUTLET[1] - FORK_FROM_OUTLET[0]
    base = (cq.Workplane("XY").box(110, 90, 6, centered=(True, False, False))
            .translate((FIX_X, FIX_OUTLET_Y + 22, 0)))
    fork_h = FIX_AXIS_Z + 30
    fork = (cq.Workplane("XY").box(90, t, fork_h, centered=(True, False, False))
            .translate((FIX_X, y0, 0)))
    slot = (cq.Workplane("XZ").center(FIX_X, FIX_AXIS_Z).circle(FORK_SLOT / 2)
            .extrude(-t - 2).translate((0, y0 - 1, 0)))
    slot_up = (cq.Workplane("XY").box(FORK_SLOT, t + 2, 60, centered=(True, False, False))
               .translate((FIX_X, y0 - 1, FIX_AXIS_Z)))
    # lead-in chamfer on the slot mouth
    lead = (cq.Workplane("XZ").polyline([(FIX_X - FORK_SLOT / 2, fork_h - 12), (FIX_X - FORK_SLOT / 2 - 10, fork_h + 1),
                                         (FIX_X + FORK_SLOT / 2 + 10, fork_h + 1), (FIX_X + FORK_SLOT / 2, fork_h - 12)])
            .close().extrude(-t - 2).translate((0, y0 - 1, 0)))
    fork = fork.cut(slot).cut(slot_up).cut(lead)
    # collar cradle: two rails under the collar body, either side of the tube
    c0 = FIX_OUTLET_Y + COLLAR_FROM_OUTLET[0] - 3
    cl = COLLAR_FROM_OUTLET[1] - COLLAR_FROM_OUTLET[0] + 3.5
    rail_top = FIX_AXIS_Z - 17.0
    rails = None
    for sx in (-1, 1):
        r = (cq.Workplane("XY").box(14, cl, rail_top, centered=(True, False, False))
             .translate((FIX_X + sx * 20, c0, 0)))
        rails = r if rails is None else rails.union(r)
    return base.union(fork).union(rails)


# ----------------------------------------------------------------------------- supply + bin
RACK_X = (240.0, 300.0, 360.0)   # three fresh augers waiting (W), axes along Y
RACK_AXIS_Z = 62.0
RACK_OUTLET_Y = 60.0


def auger_rack() -> cq.Workplane:
    base = (cq.Workplane("XY").box(170, 230, 5, centered=(True, False, False))
            .translate((sum(RACK_X) / 3, RACK_OUTLET_Y + 5, 0)))
    out = base
    for yb in (RACK_OUTLET_Y + 20, RACK_OUTLET_Y + 205):
        wall = (cq.Workplane("XY").box(170, 10, RACK_AXIS_Z - 5, centered=(True, False, False))
                .translate((sum(RACK_X) / 3, yb, 0)))
        for x in RACK_X:
            v = (cq.Workplane("XZ").polyline([(x - 15, RACK_AXIS_Z + 12), (x, RACK_AXIS_Z - TUBE_R - 0.5),
                                              (x + 15, RACK_AXIS_Z + 12)]).close()
                 .extrude(-12).translate((0, yb - 1, 0)))
            wall = wall.cut(v)
        out = out.union(wall)
    return out


BIN_X, BIN_Y, BIN_Z = (-185.0, -65.0), (200.0, 480.0), 90.0


def disposal_bin() -> cq.Workplane:
    w, l = BIN_X[1] - BIN_X[0], BIN_Y[1] - BIN_Y[0]
    outer = cq.Workplane("XY").box(w, l, BIN_Z, centered=False).translate((BIN_X[0], BIN_Y[0], 0))
    inner = (cq.Workplane("XY").box(w - 6, l - 6, BIN_Z, centered=False)
             .translate((BIN_X[0] + 3, BIN_Y[0] + 3, 3)))
    return outer.cut(inner)


def board() -> cq.Workplane:
    """Bench top the doser, fixture, rack, bin and arm share (top at z = 0)."""
    return cq.Workplane("XY").box(760, 640, 20, centered=False).translate((-300, 30, -20))


# ----------------------------------------------------------------------------- PiPER flange adapter
def flange_adapter(t: float = 6.0) -> cq.Workplane:
    """Ø57 plate that bolts to the PiPER's J6 flange (6×M3 on Ø50, Ø24.3 bore), z = -t..0."""
    return (cq.Workplane("XY").circle(28.5).circle(12.15).extrude(-t)
            .faces("<Z").workplane()
            .polarArray(25, 0, 360, 6).hole(3.4))


# ----------------------------------------------------------------------------- custom end effector
GRIP_Y = 149.0            # grip point along W y: between the NEMA 11 plate (134.7) and rear clip (163.4)
FLANGE_Z = 150.0          # flange height (W) when the tool is seated on the doser
HOOK_Z = AXIS_Z - FLANGE_Z      # tube axis in E with the carriage down (-106.75)
STROKE = 28.0             # carriage travel: hook centre 28 mm above the axis when up
JAW_W = 16.0              # jaw width along the auger (fits the 28.7 mm window)
HOOK_RI, HOOK_RO = 13.0, 17.0
HOOK_ARC = (25.0, -128.0)  # degrees from +X about the tube axis (wraps under the tube)
HOOK_PIVOT = (20.0, 22.0)  # hook pivot (x, z) relative to the hook centre
HOOK_OPEN_DEG = 38.0
FINGER_X = (-16.4, -13.4)  # thin fixed finger in the 5.5 mm gap beside the stepper
FINGER_DOWN = 11.0         # finger reaches this far below the tube axis


def hook() -> cq.Workplane:
    """Curved jaw (green in the issue sketch), in a frame with the hook centre at the
    origin and the pivot at HOOK_PIVOT.  Swings about the pivot (axis along Y)."""
    a0, a1 = HOOK_ARC
    outer = _pts_arc(HOOK_RO, a0, a1, 30)
    inner = _pts_arc(HOOK_RI, a1, a0, 30)
    arc = cq.Workplane("XZ").polyline(outer + inner).close().extrude(JAW_W / 2, both=True)
    px, pz = HOOK_PIVOT
    top = (HOOK_RO * math.cos(math.radians(a0)), HOOK_RO * math.sin(math.radians(a0)))
    arm = (cq.Workplane("XZ").polyline([(top[0] - 4.5, top[1] - 2), (px - 4, pz), (px + 4, pz),
                                        (top[0] + 0.5, top[1] - 4)]).close()
           .extrude(JAW_W / 2, both=True))
    boss = cq.Workplane("XZ").center(px, pz).circle(5).extrude(JAW_W / 2, both=True)
    return arc.union(arm).union(boss)


def carriage(top_above_hook: float = 30.0) -> cq.Workplane:
    """Moving carriage: plate + thin fixed finger + hook pivot bracket, frame = hook centre."""
    plate = (cq.Workplane("XY").box(52, 24, 6, centered=(False, True, False))
             .translate((-22, 0, top_above_hook - 6)))
    finger = (cq.Workplane("XY").box(FINGER_X[1] - FINGER_X[0], JAW_W, top_above_hook + FINGER_DOWN,
                                     centered=(False, True, False))
              .translate((FINGER_X[0], 0, -FINGER_DOWN)))
    # finger is bent outwards above the stepper so it can hang from the plate
    px, pz = HOOK_PIVOT
    bracket = (cq.Workplane("XY").box(8, 24, top_above_hook - pz + 3, centered=(True, True, False))
               .translate((px + 8, 0, pz - 3)))
    return plate.union(finger).union(bracket)


def fixed_frame(kind: str = "s1") -> cq.Workplane:
    """Fixed portion (red in the issue sketch): housing + two legs that press on the doser.
    Leg A lands on top of the NEMA 11 plate (-X side, the only rigid surface there),
    leg B on the mounting-plate floor beside the rear clip (+X side).  The resultant of
    the two contact forces passes under the jaws, so the pull-out force closes inside
    the tool and never reaches the arm.  Frame E."""
    gy = GRIP_Y
    housing_bot = 90.0 - FLANGE_Z           # housing underside at W z = 90 (clear of the lifted tube)
    housing = (cq.Workplane("XY").box(84, 62, -6 - housing_bot, centered=(True, True, False))
               .translate((-2, 3, housing_bot)))
    # pocket the carriage slides up into
    housing = housing.cut(cq.Workplane("XY").box(60, 30, 32, centered=(True, True, False))
                          .translate((4, 0, housing_bot - 1)))
    # leg A: down to the stepper plate top
    ya = (128.9 - gy, 134.4 - gy)
    za = STEPPER_PLATE_TOP - FLANGE_Z
    leg_a = (cq.Workplane("XY").box(16, ya[1] - ya[0], housing_bot - za, centered=(False, False, False))
             .translate((-40, ya[0], za)))
    # leg B: down to the floor on +X, beside the rear clip
    yb = (152.0 - gy, 171.0 - gy)
    zb = FLOOR_Z - FLANGE_Z
    leg_b = (cq.Workplane("XY").box(10, yb[1] - yb[0], housing_bot - zb, centered=(False, False, False))
             .translate((24, yb[0], zb)))
    pad_b = (cq.Workplane("XY").box(14, yb[1] - yb[0] + 4, 3, centered=(False, False, False))
             .translate((22, yb[0] - 2, zb)))
    return housing.union(leg_a).union(leg_b).union(pad_b)


def servo_box(l=40.7, w=19.7, h=36.0, tab=54.0) -> cq.Workplane:
    """MG996R-sized block (body + mounting tabs + spline boss), spline along +z at the origin."""
    body = cq.Workplane("XY").box(l, w, h, centered=(True, True, False)).translate((0, 0, -h))
    tabs = cq.Workplane("XY").box(tab, w, 2.5, centered=(True, True, False)).translate((0, 0, -9))
    boss = cq.Workplane("XY").circle(3).extrude(4)
    return body.union(tabs).union(boss)


def micro_servo() -> cq.Workplane:
    return servo_box(22.8, 12.2, 22.0, 32.0)


def gear_disc(r: float, t: float = 6.0, teeth: int = 0) -> cq.Workplane:
    g = cq.Workplane("XY").circle(r).extrude(t)
    if teeth:
        for i in range(teeth):
            a = 2 * math.pi * i / teeth
            g = g.union(cq.Workplane("XY").box(1.6, 1.6, t, centered=(True, True, False))
                        .rotate((0, 0, 0), (0, 0, 1), math.degrees(a)).translate((r * math.cos(a), r * math.sin(a), 0)))
    return g


def rack_bar(length=60.0) -> cq.Workplane:
    return cq.Workplane("XY").box(6, 8, length, centered=(True, True, False))


def guide_rods(top_z: float, bottom_z: float) -> cq.Workplane:
    out = None
    for x in (-14.0, 14.0):
        r = cq.Workplane("XY").circle(3).extrude(top_z - bottom_z).translate((x, 0, bottom_z))
        out = r if out is None else out.union(r)
    return out


# S2: one servo turns a wheel; a crank pin lowers/raises the carriage (crank-slider), a face
# cam on the same wheel opens/closes the hook through a follower lever
WHEEL_R = 20.0
CRANK_R = STROKE / 2      # 14 mm crank -> 28 mm stroke
ROD_L = 34.0
CARRIAGE_TOP = 30.0       # carriage plate top above the hook centre
WHEEL_Y = -36.0           # wheel plane, just in front of the housing (E y)
WHEEL_Z = HOOK_Z + STROKE + CARRIAGE_TOP + ROD_L - CRANK_R   # wheel centre (E z) = -28.75


def wheel() -> cq.Workplane:
    """Wheel in its own frame: axis along Y, face-cam groove, crank pin at +X."""
    disc = cq.Workplane("XZ").circle(WHEEL_R).extrude(5)
    groove = cq.Workplane("XZ").circle(WHEEL_R - 3).circle(WHEEL_R - 7).extrude(1.5).translate((0, -4, 0))
    pin = cq.Workplane("XZ").center(CRANK_R, 0).circle(2.5).extrude(-6)
    hub = cq.Workplane("XZ").circle(5).extrude(-4)
    return disc.cut(groove).union(pin).union(hub)


def carriage_ear() -> cq.Workplane:
    """S2: arm from the carriage plate out to the wheel plane, with the rod's lower pin."""
    arm = (cq.Workplane("XY").box(8, abs(WHEEL_Y) - 6, 5, centered=(True, False, False))
           .translate((0, WHEEL_Y + 2, CARRIAGE_TOP - 5)))
    pin = cq.Workplane("XZ").center(0, CARRIAGE_TOP - 2.5).circle(2.5).extrude(4).translate((0, WHEEL_Y + 2, 0))
    return arm.union(pin)


def rod(length: float = 1.0, r: float = 2.0) -> cq.Workplane:
    """Unit-length link along +Z (scaled per frame in the renders)."""
    return cq.Workplane("XY").circle(r).extrude(length)


# ----------------------------------------------------------------------------- stock gripper sleeves
SLEEVE_R = 12.7
SLEEVE_DEPTH = 13.4       # sleeve thickness at the tube: the two meet on the tube's centre plane
SLEEVE_TUBE_Z = 112.0     # tube axis along the gripper's z (fingertips at 135.8)
STOCK_GRIP_Y = 216.0      # grip point (W y): free tube between the rear clip and the cap


def sleeve(side: int) -> cq.Workplane:
    """Slip-on sleeve for one stock PiPER finger, in the gripper_base frame with the
    finger closed (inner face on y = 0).  A U-shaped cap over the finger's last 40 mm with
    a half-bore that cradles the Ø25 tube (axis along the gripper's x)."""
    y0 = 0.0
    block = (cq.Workplane("XY").box(56, SLEEVE_DEPTH + 3, 44, centered=(True, False, False))
             .translate((0, -(SLEEVE_DEPTH + 3), 96)))
    bore = (cq.Workplane("YZ").center(0, SLEEVE_TUBE_Z).circle(SLEEVE_R).extrude(30, both=True))
    pocket = (cq.Workplane("XY").box(57, 26.5, 41, centered=(True, False, False))
              .translate((0, -(SLEEVE_DEPTH + 3) - 26.5 + 3, 96)))
    s = block.cut(bore).translate((0, y0, 0))
    s = s.union(cq.Workplane("XY").box(60, 3, 44, centered=(True, False, False))
                .translate((0, -(SLEEVE_DEPTH + 3) - 26.5, 96)))
    s = s.union(cq.Workplane("XY").box(60, 26.5 + 6, 3, centered=(True, False, False))
                .translate((0, -(SLEEVE_DEPTH + 3) - 26.5, 137)))
    if side < 0:
        s = s.mirror("XZ")
    return s


# ----------------------------------------------------------------------------- Alt A: tilt-lock pin
PIN_Y = 156.0             # over the rear of the mounting-plate floor, in front of the rear clip
PIN_Z = FLOOR_Z + 4.5     # pin axis: just above the floor top, so the floor can't rise
PIN_X_OUT, PIN_X_IN = 40.0, 18.0   # pin tip positions (retracted / locked over the floor edge at x = 34)
PIN_HOUSING_X = (38.0, 70.0)
PIN_LEN, PIN_KNOB = 82.0, 76.0


def pin_housing() -> cq.Workplane:
    """Bracket on the board beside the doser (doesn't tilt).  The pin slides in -X over
    the +X edge of the mounting-plate floor (x = 34), so the floor can't tip up."""
    x0, x1 = PIN_HOUSING_X
    blk = (cq.Workplane("XY").box(x1 - x0, 20, PIN_Z + 7, centered=(False, True, False))
           .translate((x0, PIN_Y, 0)))
    bore = cq.Workplane("YZ").circle(4.2).extrude(x1 - x0 + 2).translate((x0 - 1, PIN_Y, PIN_Z))
    return blk.cut(bore)


def pin() -> cq.Workplane:
    """Pin with a vertical knob the closed stock gripper pushes/pulls, frame: tip at x = 0."""
    rod = cq.Workplane("YZ").circle(4).extrude(PIN_LEN)
    knob = cq.Workplane("XY").box(6, 6, 30, centered=(True, True, False)).translate((PIN_KNOB, 0, 0))
    ball = cq.Workplane("XY").sphere(6).translate((PIN_KNOB, 0, 30))
    return rod.union(knob).union(ball)


ALL_PARTS = {
    "clip_half_pos": lambda: clip_half(+1),
    "clip_half_neg": lambda: clip_half(-1),
    "clip_base": clip_base,
    "finger_fixture": finger_fixture,
    "auger_rack": auger_rack,
    "disposal_bin": disposal_bin,
    "board": board,
    "flange_adapter": flange_adapter,
    "hook": hook,
    "carriage": carriage,
    "frame_s1": lambda: fixed_frame("s1"),
    "frame_s2": lambda: fixed_frame("s2"),
    "servo_mg996r": servo_box,
    "servo_micro": micro_servo,
    "pinion": lambda: gear_disc(9.0, 6.0, 18),
    "rack_bar": rack_bar,
    "wheel": wheel,
    "carriage_ear": carriage_ear,
    "rod": lambda: rod(1.0, 2.0),
    "drive_gear": lambda: gear_disc(20.0, 5.0, 40),
    "driven_gear": lambda: gear_disc(10.0, 5.0, 20),
    "sleeve_pos": lambda: sleeve(+1),
    "sleeve_neg": lambda: sleeve(-1),
    "pin_housing": pin_housing,
    "pin": pin,
}
