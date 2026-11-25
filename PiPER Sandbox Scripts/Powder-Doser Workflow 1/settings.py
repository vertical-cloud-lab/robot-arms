"""Every number Powder-Doser Workflow 1 uses, in one place. Edit this file, not the scripts.

Units are mm and degrees. Positions are in the ARM FRAME, the one piper_sdk's forward
kinematics uses (Up_and_Down.fk): origin under the arm's base on the table, x straight out in
front of the arm (J1 = 0), y to the arm's left, z up.

Numbers marked MEASURE are estimates. Measure them on the real cell before the first real run.
"""

# --------------------------------------------------------------------------------------------
# The auger (powder-doser PR 200's auger; dimensions from its STL, see the Digital Twin on
# PR #77). "Outlet end" is the end nearest the gear.
# --------------------------------------------------------------------------------------------
AUGER_LENGTH_MM = 250.0          # end to end
AUGER_TUBE_DIAMETER_MM = 25.0    # where the gripper holds it
AUGER_GEAR_DIAMETER_MM = 46.0    # the widest part, so the auger's "width"
# Where the gripper holds the auger, measured along it from its middle (+ toward the gear).
# 0 = the middle. It must land between the holder's two clips and clear of the gear; the
# finger sleeves are about 28 mm wide.
GRASP_OFFSET_MM = 0.0            # MEASURE (check it is between the clips)

# --------------------------------------------------------------------------------------------
# The holder ("test clamp"): the wood block with the two clips, on wood blocks on the table.
#
# HOLDER FRAME: origin on the auger's axis at the auger's middle, x along the auger toward the
# gear (outlet) end, y to the left of x, z up. Each tag is stuck flat, face up, on the holder.
# Give each tag's centre in this frame: (x, y, z), z negative because the block's top is below
# the auger's axis (the clips hold the axis about 29 mm above the block).
# Two tags, one near each end of the block, give the holder's direction far better than one.
# Put them on the side of the auger that faces the camera (here -y: the outer side, away from
# the arm), far enough out that the tube and gear (up to 52 mm above them) don't hide them.
# --------------------------------------------------------------------------------------------
HOLDER_TAGS = {                  # tag36h11 id: (x, y, z) of the tag's centre, mm   MEASURE
    201: (-90.0, -55.0, -29.0),
    202: (90.0, -55.0, -29.0),
}
HOLDER_TAG_SIZE_MM = 30.0        # edge of the tag's black square (not the white border)
# How high the clips' arms reach above the auger's axis: the gripper stays clear of them.
HOLDER_CLIP_TOP_ABOVE_AXIS_MM = 21.0

# --------------------------------------------------------------------------------------------
# The box the auger goes into. Its inside is 10 mm longer and 10 mm wider than the auger.
#
# BOX FRAME: origin at the centre of the box's inside floor, x along its long side, z up.
# Default tags: on the table, one against the middle of each short end, outside the box.
# --------------------------------------------------------------------------------------------
BOX_INSIDE_MM = (AUGER_LENGTH_MM + 10.0, AUGER_GEAR_DIAMETER_MM + 10.0)  # length, width
BOX_WALL_HEIGHT_MM = 40.0        # inside floor to the top of the walls     MEASURE
BOX_TAGS = {                     # tag36h11 id: (x, y, z) of the tag's centre, mm   MEASURE
    203: (-158.0, 0.0, -3.0),
    204: (158.0, 0.0, -3.0),
}
BOX_TAG_SIZE_MM = 30.0

# Optional: a tag on the auger itself (a small flat flag on top of the tube, away from where
# the gripper holds it). With it, every run also measures where the auger landed in the box,
# which gives placement accuracy and repeatability in mm. None = no auger tag.
# AUGER TAG FRAME position: (x, y, z) of the tag's centre in the AUGER frame (origin on the
# axis at the auger's middle, x toward the gear end, z up when the flag is on top).
AUGER_TAG = None                 # e.g. {"id": 205, "size_mm": 20.0, "pos": (-80.0, 0.0, 16.0)}

# Where you expect things (arm frame: x, y, yaw of the object's x axis). The run finds the
# holder and box with the tags; these are only for the simulation (--dry-run) and to warn if
# something is more than SPOT_TOLERANCE_MM from where it should be (the box on the wrong spot).
# Lay the auger and the box ACROSS the arm's reach (yaw = J1 + 90): see "Orientation" in the
# README for why.
# This example (layout.png) keeps clear of the A1 mini and the black shelf on the arm's right,
# so it uses the table in front of the arm and to its left: move the big cardboard box.
HOLDER_EXPECTED = (367.1, 98.4, 90.0)   # 380 mm out at J1 = 15, 15 deg off across the reach
SPOTS = {                        # name: (x, y, yaw) of the box's centre   MEASURE / choose
    "1": (251.1, 145.0, 90.0),   # 290 mm out at J1 = 30, parallel to the holder
    "2": (141.4, 141.4, 120.0),  # 200 mm out at J1 = 45, 15 deg off across the reach
    "3": (114.7, 163.8, 130.0),  # 200 mm out at J1 = 55, 15 deg off across the reach
}
SPOT_TOLERANCE_MM = 40.0

# --------------------------------------------------------------------------------------------
# The gripper, with the lab's custom finger sleeves.
# --------------------------------------------------------------------------------------------
TCP_MM = 125.0                   # flange to the middle of the finger pads (where the tube sits)   MEASURE
FINGERTIP_MM = 140.0             # flange to the fingertips                                        MEASURE
FINGER_THICKNESS_MM = 8.0        # one sleeve, inner face to outer face                            MEASURE
# The gripper's own reading (mm): 45.6 with the sleeves touching, 108.6 fully open (moved by
# hand, Teleoperation README). The gap between the sleeves is the reading minus this.
GRIPPER_CLOSED_READING_MM = 45.6
GRIPPER_MAX_READING_MM = 108.0
GRIP_EFFORT_NM = 2.0             # gripper effort while holding (piper_sdk's unit; 5 = its max, ~40 N)
GRIP_SQUEEZE_MM = 8.0            # close this much tighter than the tube, so it squeezes
GRIP_TOLERANCE_MM = 6.0          # "holding the tube" = the reading within this of the tube's
OPEN_FOR_GRASP_MM = 30.0         # on the way down, the gap is this much wider than the tube
OPEN_FOR_RELEASE_MM = 10.0       # in the box, open only this much wider (the box is narrow)
GRIPPER_MM_S = 40.0              # how fast the gripper's target moves

# Which way the fingers close. With J4 = 0 and the gripper pointing down, the two fingers line
# up with the arm's reach (one nearer the base, one farther out) at this J6. From PR #20's
# rest-pose photo: the fingers closed across the arm at J6 = +64.3, so along it at -25.7, and
# on 2026-11-20 mpzy's frame shows them opening up and down at the park angle (J6 = -52).
# CHECK on the arm before the first run (README, "First run").
FINGERS_ALONG_REACH_J6_DEG = -25.7

# --------------------------------------------------------------------------------------------
# Where the arm may go.
# --------------------------------------------------------------------------------------------
# J6 (the gripper's twist) stays inside a 90 degree window, for the wrist camera's cables. It
# includes the park angle, -52 (arm_home.json parks J6 between -95 and -45; the cable stops
# J6 at about -55).
J6_RANGE_DEG = (-52.0, 38.0)
J4_DEG = 0.0                     # the forearm roll is held here (centred) the whole time
# J1 (the base) only turns inside this range. The A1 mini is on the arm's right (negative J1,
# about -90 deg), and the black shelf at its front right: keep J1 well clear of them.
J1_RANGE_DEG = (-20.0, 60.0)     # MEASURE: set it from where the printer and shelf really are
# Boxes no part of the arm (or the auger it carries) may enter, arm frame, mm:
# (x_min, y_min, z_min, x_max, y_max, z_max). From the Digital Twin's estimate of the cell
# (PR #77), which mpzy's frame of 2026-11-24 agrees with roughly:            MEASURE both
# - the A1 mini: centre x = -20, y = -380, 347 x 315 x 365 mm, bed fully forward, + 50 mm;
# - the black shelf at the arm's front right: 400 x 300 mm, top 65 mm up, + 30 mm (the arm
#   may pass over it, not into it).
KEEP_OUT_BOXES = {
    "A1 mini": (-227.0, -603.0, -10.0, 277.0, -157.0, 450.0),
    "black shelf": (140.0, -495.0, -10.0, 500.0, -35.0, 95.0),
}
TABLE_CLEARANCE_MM = 5.0         # nothing below this height (the table is z = 0)
J5_COMFORT_DEG = 65.0            # the tool tips outward when pointing straight down needs more
                                 # J5 than this (J5's limit is 70)

# --------------------------------------------------------------------------------------------
# The moves.
# --------------------------------------------------------------------------------------------
APPROACH_MM = 70.0               # hover this far above the grasp / release point first
PULL_MM = 40.0                   # pull the auger straight up this far, slowly, out of the clips
CARRY_CLEARANCE_MM = 50.0        # carried auger's lowest point this far above the clips / box rim
RELEASE_HEIGHT_MM = 8.0          # auger's lowest point this far above the box floor when let go
MOVE_MM_S = 50.0                 # straight-line moves
APPROACH_MM_S = 20.0             # the last APPROACH_MM down to the grasp and to the release
PULL_MM_S = 8.0                  # pulling out of the clips
JOINT_DEG_S = 15.0               # peak joint speed (all moves)
SPEED_PERCENT = 25               # the arm's own speed cap (MotionCtrl_2), 1-30
# A joint drawing more than this (A, J1..J6), or more than LAG_DEG behind its target, is a
# snag: the arm stops. From follower.py (teleop) for normal moves; the pull may need more.
MAX_CURRENT_A = (3.0, 7.0, 6.0, 2.0, 4.5, 1.5)
PULL_MAX_CURRENT_A = (3.0, 7.0, 6.0, 2.0, 4.5, 2.0)
LAG_DEG = 5.0

# READY: the pose the arm waits in between runs (raised off its rest, like teleop's READY).
READY_LIFT_DEG = 20.0            # J2 up and J3 open by this
PARK_J6_DEG = -52.0              # J6 at READY and when parked (arm_home.json)
# Between runs the arm waits at READY with its motors on ("ready"), or lands on its rest and
# switches its motors off ("park"; slower, ~40 s more per run).
BETWEEN_RUNS = "ready"

# --------------------------------------------------------------------------------------------
# The camera: mpzy's front cam (Camera Module 3 Wide, on the front-left post). calibrate.py
# measures exactly where it is; these are the starting guesses and the --dry-run camera.
# --------------------------------------------------------------------------------------------
CAMERA_INDEX = 0
CAMERA_SIZE = (4608, 2592)       # full sensor
CAMERA_LENS_POSITION = 1.2       # fixed focus (dioptres, 1/m): autofocus would change the calibration
CAMERA_FOCAL_PX = 1964.0         # nominal: 2.75 mm lens, 1.4 um pixels
CAMERA_GUESS_POSITION = (920.0, -170.0, 560.0)  # arm frame (Digital Twin estimate)
CAMERA_GUESS_LOOK_AT = (250.0, 60.0, 40.0)
CALIBRATION_FILE = "calibration.json"

# calibrate.py: the card the gripper holds, a tag on each face (README, "Calibrate").
CAL_TAG_IDS = (199, 200)
CAL_TAG_SIZE_MM = 40.0

RESULTS_DIR = "results"
