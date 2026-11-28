"""A simulated AgileX PiPER (MuJoCo Menagerie model) as an AMP SimAdapter.

AMP (apple-aiml-research/ml-amp) runs its harness unchanged across robots: a backend declares its
embodiment (arms, end effectors, cameras, action layout) and, for "chain" kinematics, sends its own
kinematic tree (/sim/robot). This module is that backend for the lab's 6-DOF PiPER: a MuJoCo scene
with a table, two fixed scene cameras and a wrist camera, and a small task library taken from
robot-arms issues (#30 tape onto the shelf, #21 vials into a rack) plus the paper's own demo task
(banana in the bowl).

Nothing here talks to real hardware.
"""

from __future__ import annotations

import math
import os
import re
import shutil
from pathlib import Path

import mujoco
import numpy as np

from amp.contracts.embodiment import (
    ActionSegment,
    ArmSpec,
    CameraSpec,
    DriveSpec,
    EmbodimentSpec,
    EndEffectorSpec,
    GripperSpec,
    JointSpec,
    Kinematics,
    LinkSpec,
    RobotDescription,
    WorkspaceSpec,
)
from amp.link.robot import description_sha256
from amp.robots.capgym.adapter import CameraImage, Frame

MENAGERIE = Path(os.environ.get("PIPER_MENAGERIE",
                                "/tmp/ext/menagerie/mujoco_menagerie/agilex_piper"))
WORK = Path(os.environ.get("PIPER_SIM_DIR", "/tmp/amp-piper/model"))

NAME = "agilex_piper_sim"
ROOT = "base_link"
FLANGE = "link6"
ARM, HAND = "arm", "hand"
JOINTS = tuple(f"joint{i}" for i in range(1, 7))
FINGERS = ("joint7", "joint8")
FINGER_OPEN, FINGER_CLOSED = (0.035, -0.035), (0.0, 0.0)
STROKE_M = 0.070
TCP_Z = 0.115             # TCP along link6 +z: middle of the finger pads (0.075 .. 0.135)
TIP_REACH = 0.020         # fingertips (0.135) past the TCP
CONTROL_DT = 1.0 / 15.0   # RoboLab's 15 Hz
CAM_W, CAM_H = 640, 480
VISUAL_GROUP = 2          # the menagerie model's visual geoms
GRIPPER_KP = 1000.0       # the menagerie's 40 N/m squeezes a held part with < 1 N; 10 N cap stays

# Joint limits as the menagerie model declares them (rad); speed limits conservative for the PiPER.
Q_MIN = (-2.618, 0.0, -2.697, -1.832, -1.22, -3.14)
Q_MAX = (2.618, 3.14, 0.0, 1.832, 1.22, 3.14)
QD_MAX = (2.0, 2.0, 2.0, 3.0, 3.0, 3.0)
# Home: the gripper over the table, pointing down (found by ik_home() below, then fixed).
Q_HOME = (0.0, 1.35, -1.20, 0.0, 1.10, 0.0)


# ----------------------------------------------------------------------------------------- scene

def _look_at(pos, target, up=(0, 0, 1)) -> str:
    """MuJoCo xyaxes for a camera at pos looking at target (cameras look along their -z)."""
    pos, target, up = (np.asarray(v, float) for v in (pos, target, up))
    fwd = target - pos
    fwd /= np.linalg.norm(fwd)
    right = np.cross(fwd, up)
    right /= np.linalg.norm(right)
    upv = np.cross(right, fwd)
    return " ".join(f"{v:.6f}" for v in (*right, *upv))


SCENE_CAMERAS = {
    # over the robot's left and right shoulders, like DROID's two fixed cameras
    "left": ((0.12, 0.50, 0.50), (0.33, -0.03, 0.0)),
    "right": ((0.12, -0.50, 0.50), (0.33, 0.03, 0.0)),
}
FOVY = {"left": 55.0, "right": 55.0, "wrist": 70.0}


def _qmul(a, b):
    w1, x1, y1, z1 = a
    w2, x2, y2, z2 = b
    return (w1 * w2 - x1 * x2 - y1 * y2 - z1 * z2, w1 * x2 + x1 * w2 + y1 * z2 - z1 * y2,
            w1 * y2 - x1 * z2 + y1 * w2 + z1 * x2, w1 * z2 + x1 * y2 - y1 * x2 + z1 * w2)


def _q_zy(yaw, pitch) -> str:
    """MuJoCo quat attribute of Rz(yaw) @ Ry(pitch)."""
    qz = (math.cos(yaw / 2), 0.0, 0.0, math.sin(yaw / 2))
    qy = (math.cos(pitch / 2), 0.0, math.sin(pitch / 2), 0.0)
    return " ".join(f"{v:.6f}" for v in _qmul(qz, qy))


def _ring(name, cx, cy, z0, r_in, r_out, height, n, rgba, mass, free=True, extra=""):
    """A hollow cylinder (tape roll, bowl wall) of n box segments in one body."""
    rm, t = 0.5 * (r_in + r_out), 0.5 * (r_out - r_in)
    seg = math.pi * r_out / n * 1.08  # half-length, a little overlap so it reads as closed
    geoms = []
    for i in range(n):
        a = 2 * math.pi * i / n
        geoms.append(
            f'<geom type="box" size="{t:.4f} {seg:.4f} {height / 2:.4f}" '
            f'pos="{rm * math.cos(a):.4f} {rm * math.sin(a):.4f} {height / 2:.4f}" '
            f'euler="0 0 {a:.4f}" rgba="{rgba}" mass="{mass / n:.5f}" {extra}/>')
    joint = '<freejoint/>' if free else ''
    return (f'<body name="{name}" pos="{cx} {cy} {z0}">{joint}' + "".join(geoms) + '</body>')


def _bowl(name, cx, cy, rgba="0.92 0.92 0.95 1"):
    r_base, r_top, h, n, wall = 0.050, 0.078, 0.055, 24, 0.005
    geoms = [f'<geom type="cylinder" size="{r_base:.3f} 0.004" pos="0 0 0.004" rgba="{rgba}" '
             f'mass="0.12"/>']
    tilt = math.atan2(r_top - r_base, h)
    rm = 0.5 * (r_base + r_top)
    seg = math.pi * r_top / n * 1.1
    for i in range(n):
        a = 2 * math.pi * i / n
        # wall segment tilted outward: rotate about the tangent axis
        geoms.append(
            f'<geom type="box" size="{wall / 2:.4f} {seg:.4f} {h / 2 / math.cos(tilt):.4f}" '
            f'pos="{rm * math.cos(a):.4f} {rm * math.sin(a):.4f} {h / 2 + 0.004:.4f}" '
            f'quat="{_q_zy(a, tilt)}" rgba="{rgba}" mass="{0.18 / n:.5f}"/>')
    return f'<body name="{name}" pos="{cx} {cy} 0"><freejoint/>' + "".join(geoms) + '</body>'


def _banana(name, cx, cy, yaw):
    """A curved banana: a middle capsule and two end capsules bent toward +y, and a stem."""
    r, hl, bend = 0.016, 0.034, 0.32
    he = hl * 0.8
    g = [f'<geom type="capsule" size="{r} {hl}" pos="0 0 {r}" quat="{_q_zy(0.0, 1.5708)}" '
         f'rgba="0.95 0.82 0.18 1" mass="0.03" friction="1.2 0.02 0.002"/>']
    for s in (-1.0, 1.0):
        x = s * (hl + he * math.cos(bend))
        y = he * math.sin(bend)
        g.append(f'<geom type="capsule" size="{r * 0.85:.4f} {he:.4f}" '
                 f'pos="{x:.4f} {y:.4f} {r:.4f}" quat="{_q_zy(s * bend, 1.5708)}" '
                 f'rgba="0.93 0.80 0.16 1" mass="0.015" friction="1.2 0.02 0.002"/>')
    sx = hl + 2 * he * math.cos(bend) + 0.004
    sy = 2 * he * math.sin(bend)
    g.append(f'<geom type="capsule" size="0.005 0.008" pos="{sx:.4f} {sy:.4f} {r:.4f}" '
             f'quat="{_q_zy(bend, 1.5708)}" rgba="0.40 0.30 0.10 1" mass="0.002"/>')
    return (f'<body name="{name}" pos="{cx} {cy} 0" euler="0 0 {yaw:.4f}"><freejoint/>'
            + "".join(g) + '</body>')


def _vial(name, cx, cy, cap_rgba, z0=0.0, r=0.0075, h=0.048):
    return (f'<body name="{name}" pos="{cx} {cy} {z0}"><freejoint/>'
            f'<geom type="cylinder" size="{r} {h / 2 - 0.006:.4f}" pos="0 0 {h / 2 - 0.006:.4f}" '
            f'rgba="0.80 0.88 0.92 1" mass="0.012" friction="1.0 0.02 0.002"/>'
            f'<geom type="cylinder" size="{r + 0.0008:.4f} 0.006" pos="0 0 {h - 0.006:.4f}" '
            f'rgba="{cap_rgba}" mass="0.004" friction="1.2 0.02 0.002"/>'
            '</body>')


RACK_PITCH, RACK_HOLE, RACK_H = 0.030, 0.0095, 0.030   # hole half-width 9.5 mm: 2 mm clearance


def _rack(name, cx, cy, n=3):
    """A static block with n square pockets along y (half-width RACK_HOLE), 3 cm deep."""
    w_half = 0.022
    span = (n - 1) * RACK_PITCH
    y0 = -span / 2
    rgba = "0.20 0.35 0.75 1"
    g = [f'<geom type="box" size="{w_half} {span / 2 + 0.025:.4f} 0.003" pos="0 0 0.003" '
         f'rgba="{rgba}"/>']
    # walls along x (between pockets and at the ends)
    ys = [y0 - RACK_PITCH / 2 + k * RACK_PITCH for k in range(n + 1)]
    ys[0] = y0 - RACK_HOLE - 0.0075
    ys[-1] = y0 + span + RACK_HOLE + 0.0075
    for k, y in enumerate(ys):
        half = 0.0075 if k in (0, n) else (RACK_PITCH / 2 - RACK_HOLE)
        yc = y if k in (0, n) else y0 - RACK_PITCH / 2 + k * RACK_PITCH
        g.append(f'<geom type="box" size="{w_half} {half:.4f} {RACK_H / 2}" '
                 f'pos="0 {yc:.4f} {RACK_H / 2}" rgba="{rgba}"/>')
    # front and back walls along y
    for s in (-1, 1):
        g.append(f'<geom type="box" size="{w_half - RACK_HOLE:.4f} {span / 2 + 0.025:.4f} '
                 f'{RACK_H / 2}" pos="{s * (RACK_HOLE + (w_half - RACK_HOLE)):.4f} 0 {RACK_H / 2}" '
                 f'rgba="{rgba}"/>')
    return f'<body name="{name}" pos="{cx} {cy} 0">' + "".join(g) + '</body>'


# ------------------------------------------------------- lab workflows (PR #87 follow-up)
# Three tasks taken from the lab's own threads. Dimensions are the lab's where it has them
# (each one is cited in amp1/README.md); the rest are labelled estimates.

def _box(size, pos, rgba, euler=None, extra=""):
    e = f' euler="{euler[0]:.5f} {euler[1]:.5f} {euler[2]:.5f}"' if euler is not None else ""
    return (f'<geom type="box" size="{size[0]:.5f} {size[1]:.5f} {size[2]:.5f}" '
            f'pos="{pos[0]:.5f} {pos[1]:.5f} {pos[2]:.5f}"{e} rgba="{rgba}" {extra}/>')


def _hex_mesh(name, r_corner, h):
    """A hexagonal prism (centred on its origin) as an inline convex mesh asset."""
    v = []
    for z in (-h / 2, h / 2):
        for k in range(6):
            a = math.pi / 6 + k * math.pi / 3
            v += [r_corner * math.cos(a), r_corner * math.sin(a), z]
    return f'<mesh name="{name}" vertex="{" ".join(f"{x:.5f}" for x in v)}"/>'


def _frustum_mesh(name, r0, r1, h, n=24):
    """A truncated cone, radius r0 at -h/2 and r1 at +h/2 (a chamfer), as a convex mesh."""
    v = []
    for z, r in ((-h / 2, r0), (h / 2, r1)):
        for k in range(n):
            a = 2 * math.pi * k / n
            v += [r * math.cos(a), r * math.sin(a), z]
    return f'<mesh name="{name}" vertex="{" ".join(f"{x:.5f}" for x in v)}"/>'


# --- Bambu Lab A1 mini (Thumbelina) ------------------------------------------------------------
# The cell's printer sits about 380 mm to the arm's right and 20 mm behind its base, both facing
# the room (+x), as in the twin's cell_layout.yaml and the cell photo (robot-arms PR #77): the Z
# column and the AMS lite are on the arm's side, the bed slides front to back. Footprint 347 x
# 315 mm; the bed parked fully forward as the end G-code leaves it (X-13 Y180: toolhead far
# left, nozzle high); plate top 85 mm above the table (80.5 mm from Bambu's drawing, 88 mm in
# the twin); a 184 x 184 mm PEI sheet on a 6-8 mm bed. The AMS lite (unmeasured) is left out.
# _a1_mini's local frame has the printer's front along +y and its arm side along -x; the body is
# turned -90 degrees so that front faces world +x.
A1_CENTER = (-0.020, -0.380)
A1_YAW = -math.pi / 2
A1_BED_FWD = 0.090          # plate centre in front of the printer centre with the bed forward
A1_PLATE = (0.092, 0.092, 0.0005)
A1_BED_TOP = 0.084
MAGNET_N = 25.0             # the sheet's magnetic hold, pulling straight off (estimate)
BOND = (5.0, 5.0, 0.08)     # the print's bond to cooled PEI: tension N, shear N, twist N*m
PRINT_HEX = (0.0254, 0.014)  # hex print, 44 mm across flats, 14 mm tall (a toy-drive-sized part)


def _a1_mini(cx, cy):
    """The printer's fixed parts: base, Y rail, bed carriage and bed, Z column, X arm, toolhead."""
    grey, dark, silver = "0.82 0.83 0.84 1", "0.24 0.24 0.26 1", "0.70 0.71 0.73 1"
    by = A1_BED_FWD
    g = [
        _box((0.1735, 0.1575, 0.0225), (0, 0, 0.0225), grey),                 # base
        _box((0.030, 0.002, 0.012), (-0.120, 0.1595, 0.026), "0.05 0.05 0.06 1"),  # screen
        _box((0.020, 0.150, 0.0075), (0, 0, 0.0525), dark),                   # Y rail
        _box((0.060, 0.060, 0.008), (0, by, 0.068), dark),                    # bed carriage
        _box((0.095, 0.095, 0.004), (0, by, A1_BED_TOP - 0.004), silver),     # heated bed
        _box((0.020, 0.040, 0.160), (-0.1485, -0.020, 0.205), grey),          # Z column (arm side)
        _box((0.004, 0.012, 0.150), (-0.1265, -0.020, 0.205), dark),          # its rail
        _box((0.135, 0.020, 0.015), (0.0, -0.020, 0.320), "0.74 0.75 0.77 1"),  # X arm
        _box((0.030, 0.035, 0.040), (0.105, 0.002, 0.300), "0.93 0.93 0.94 1"),  # toolhead, parked
        _box((0.010, 0.010, 0.006), (0.105, 0.002, 0.254), "0.55 0.45 0.20 1"),  # its nozzle
    ]
    return (f'<body name="a1_mini" pos="{cx:.4f} {cy:.4f} 0" euler="0 0 {A1_YAW:.6f}">'
            + "".join(g) + '</body>')


def _build_plate(cx, cy):
    hx, hy, hz = A1_PLATE
    return (f'<body name="build_plate" pos="{cx:.4f} {cy:.4f} {A1_BED_TOP + hz:.5f}"><freejoint/>'
            f'<geom type="box" size="{hx} {hy} {hz}" rgba="0.11 0.11 0.12 1" mass="0.15" '
            'friction="0.8 0.02 0.002" solref="0.004 1"/>'
            # the printable area's corner marks (visual only)
            + "".join(f'<geom type="box" size="0.006 0.0008 0.00005" pos="{sx * 0.084:.4f} '
                      f'{sy * 0.090:.4f} {hz + 0.00005:.5f}" rgba="0.85 0.75 0.35 1" contype="0" '
                      'conaffinity="0" group="2"/>' for sx in (-1, 1) for sy in (-1, 1))
            + '</body>')


def _print_part(cx, cy, z0, yaw):
    r, h = PRINT_HEX
    return (f'<body name="print" pos="{cx:.4f} {cy:.4f} {z0:.5f}" euler="0 0 {yaw:.4f}">'
            '<freejoint/>'
            f'<geom type="mesh" mesh="print_hex" pos="0 0 {h / 2:.4f}" rgba="0.96 0.47 0.10 1" '
            'mass="0.012" friction="1.0 0.02 0.002"/>'
            f'<geom type="cylinder" size="{0.45 * r:.4f} 0.0012" pos="0 0 {h + 0.0012:.4f}" '
            'rgba="0.20 0.45 0.90 1" mass="0.0005"/>'   # a second colour on top, as on the toys
            '</body>')


# --- powder doser and auger rack (robot-arms #42, PR #44, PR #77's twin, PR #83) -------------
# The auger lies horizontal in two C-clips that open upward and snaps in from above; its moulded
# gear drops beside the NEMA 11's pinion. Positions are mm from the outlet: front clip 47-59,
# gear 78-88, stepper mount 94-102, back clip 129-141; tube 25.0 mm, 250 mm long, cap 29 x 27 mm.
# Clip: 25.48 mm seat, about 18 mm mouth, 2 mm wall, 12 mm wide. The doser lies on the board as
# in PR #44 (axis 43.25 mm up), its auger pointing at the arm (as in the twin), cap end nearest.
AUG_R, AUG_LEN, AUG_TUBE = 0.0125, 0.250, 0.222
AUG_GEAR = (0.023, 0.078, 0.088)
AUG_CAP_R = 0.0145
CLIPS_S = ((0.047, 0.059), (0.129, 0.141))
CLIP_R_IN, CLIP_WALL = 0.01274, 0.002
AXIS_H = 0.04325
RACK_H = 0.045               # the tube's axis height resting in the rack's V cradles
CLIP_N = 10.0                # force to pull the tube out of one clip, or press it in (see README)
CRADLES_S = ((0.030, 0.042), (0.160, 0.172))


def _clip_arcs(prefix, xc, half_ax, yc, zc, rgba):
    """One C-clip around an axis along x: a fixed lower half-arc and two upper arcs (the snap
    arms) named PREFIX_lipK. Angles are in the y-z plane from +y; the mouth spans 45..135 deg."""
    rm = CLIP_R_IN + CLIP_WALL / 2
    seg = rm * math.tan(math.radians(7.5)) * 1.08
    g = []
    for k in range(24):
        th = math.radians(7.5 + 15 * k)
        if math.radians(45) < th < math.radians(135):
            continue                # the mouth
        upper = th < math.pi
        name = f' name="{prefix}_lip{k}"' if upper else ""
        g.append(f'<geom{name} type="box" size="{half_ax:.4f} {seg:.5f} {CLIP_WALL / 2:.4f}" '
                 f'pos="{xc:.4f} {yc + rm * math.cos(th):.5f} {zc + rm * math.sin(th):.5f}" '
                 f'euler="{th - math.pi / 2:.5f} 0 0" rgba="{rgba}" friction="0.4 0.01 0.001"/>')
    return g


def _doser(x_out, yd):
    """The powder doser's fixed parts. Body frame at the outlet end of the auger axis on the
    table, local x pointing from the outlet toward the cap end (toward the arm)."""
    alu, clip, dark = "0.72 0.74 0.76 1", "0.32 0.33 0.36 1", "0.12 0.12 0.13 1"
    g = [_box((0.115, 0.060, 0.007), (0.110, 0, 0.007), alu)]            # mounting plate
    for k, (s0, s1) in enumerate(CLIPS_S):
        g.append(_box(((s1 - s0) / 2, 0.016, 0.0083), ((s0 + s1) / 2, 0, 0.0223), clip))
        g += _clip_arcs(f"clip{k}", (s0 + s1) / 2, (s1 - s0) / 2, 0.0, AXIS_H, clip)
    g += [
        # NEMA 11 on its mount, pinion beside the gear (32 mm centre distance)
        f'<geom type="cylinder" size="0.0090 0.0060" pos="0.083 0.032 {AXIS_H}" '
        'euler="0 1.5708 0" rgba="0.78 0.62 0.25 1"/>',
        _box((0.004, 0.016, 0.028), (0.098, 0.034, 0.042), "0.30 0.30 0.32 1"),
        _box((0.019, 0.014, 0.014), (0.121, 0.032, AXIS_H), dark),
        # the tapper, moved onto the mounting plate (powder-doser #203)
        _box((0.012, 0.010, 0.010), (0.180, -0.040, 0.024), "0.85 0.30 0.25 1"),
    ]
    return (f'<body name="doser" pos="{x_out:.4f} {yd:.4f} 0" euler="0 0 3.14159265">'
            + "".join(g) + '</body>')


def _auger(name, x_out, y, z, rgba):
    """A free auger, body frame on its axis at the outlet end, local +x toward the cap end;
    placed with the cap end toward the arm (world -x)."""
    gr, g0, g1 = AUG_GEAR
    return (f'<body name="{name}" pos="{x_out:.4f} {y:.4f} {z:.5f}" euler="0 0 3.14159265">'
            '<freejoint/>'
            f'<geom name="{name}_tube" type="cylinder" size="{AUG_R} {AUG_TUBE / 2:.4f}" '
            f'pos="{AUG_TUBE / 2:.4f} 0 0" euler="0 1.5708 0" rgba="{rgba}" mass="0.085" '
            'friction="0.4 0.01 0.001"/>'
            f'<geom name="{name}_gear" type="cylinder" size="{gr} {(g1 - g0) / 2:.4f}" '
            f'pos="{(g0 + g1) / 2:.4f} 0 0" euler="0 1.5708 0" rgba="{rgba}" mass="0.015" '
            'friction="0.4 0.01 0.001"/>'
            f'<geom name="{name}_cap" type="cylinder" size="{AUG_CAP_R} 0.0135" '
            f'pos="0.2365 0 0" euler="0 1.5708 0" rgba="0.25 0.25 0.28 1" mass="0.02" '
            'friction="0.6 0.01 0.001"/>'
            # the open outlet end (visual)
            f'<geom type="cylinder" size="0.0105 0.0004" pos="-0.0003 0 0" euler="0 1.5708 0" '
            'rgba="0.35 0.33 0.30 1" contype="0" conaffinity="0" group="2"/>'
            '</body>')


def _auger_rack(x_out, slot_ys):
    """Open V cradles for two augers along x (outlets at x_out), on a base plate."""
    rgba, base = "0.30 0.36 0.48 1", "0.22 0.26 0.34 1"
    y0, y1 = min(slot_ys), max(slot_ys)
    g = [_box((0.115, (y1 - y0) / 2 + 0.035, 0.004), (-0.120, (y0 + y1) / 2, 0.004), base)]
    t = 0.003
    for y in slot_ys:
        for s0, s1 in CRADLES_S:
            xc, half = -(s0 + s1) / 2, (s1 - s0) / 2
            g.append(_box((half, 0.020, 0.011), (xc, y, 0.019), rgba))
            for side in (-1, 1):   # 90-degree V; the tube touches each face 45 deg below its axis
                cy = y + side * AUG_R * math.sin(math.pi / 4) + side * t * math.sin(math.pi / 4)
                cz = RACK_H - AUG_R * math.cos(math.pi / 4) - t * math.cos(math.pi / 4)
                g.append(_box((half, 0.012, t), (xc, cy, cz), rgba, euler=(side * math.pi / 4, 0, 0),
                              extra='friction="0.5 0.01 0.001"'))
    return f'<body name="auger_rack" pos="{x_out:.4f} 0 0">' + "".join(g) + '</body>'


# --- AMAZEMET rePowder: charge cups into the crucible (digital-alloy-lab SOP, #152, #179) -----
# SOP step 5, "the easiest step for an arm": the charge goes into the graphite crucible beside
# the sealing rod, through the open lid. Cups: 6063, 19.05 mm OD x 69.85 mm, plug-up, four fit
# around the rod. Crucible (model values, never calipered): 57.1 mm bore, 12.6 mm rod, 10-12 cm
# deep. The real rim is about 1.3 m up, 170 mm above the chamber top; here the arm's base is
# 120 mm below the rim (a raised mount beside the furnace, which a real cell would need too).
CRU_R_IN, CRU_R_OUT, CRU_DEPTH, CRU_RIM = 0.02855, 0.0385, 0.110, 0.120
ROD_R = 0.0063
CUP_R, CUP_H, CUP_CHAMFER = 0.009525, 0.06985, 0.0015


def _furnace(xc, yc):
    steel, graphite = "0.70 0.72 0.74 1", "0.17 0.17 0.18 1"
    floor = CRU_RIM - CRU_DEPTH
    h = CRU_RIM / 2
    g = [  # housing around a square opening 80 mm wide, top at the rim
        _box((0.030, 0.100, h), (-0.070, 0, h), steel), _box((0.030, 0.100, h), (0.070, 0, h), steel),
        _box((0.040, 0.030, h), (0, -0.070, h), steel), _box((0.040, 0.030, h), (0, 0.070, h), steel),
        # the crucible's floor: a thick box (a thin cylinder let dropped cups sink into it)
        _box((CRU_R_OUT, CRU_R_OUT, 0.015), (0, 0, floor - 0.015), graphite),
        # the sealing rod standing in the crucible, and its knob
        f'<geom type="cylinder" size="{ROD_R} 0.0950" pos="0 0 {floor + 0.095:.4f}" '
        'rgba="0.55 0.56 0.58 1" friction="0.3 0.01 0.001"/>',
        f'<geom type="cylinder" size="0.011 0.006" pos="0 0 {floor + 0.196:.4f}" '
        'rgba="0.20 0.20 0.22 1"/>',
    ]
    # the lid, hinged on the far side (+x), open 105 degrees and leaning away from the arm
    a = math.radians(105)
    hx, hz = 0.100, CRU_RIM + 0.015           # hinge line along y at the opening's far edge
    lx, lz = hx - 0.100 * math.cos(a), hz + 0.100 * math.sin(a)
    g.append(_box((0.100, 0.100, 0.015), (lx, 0, lz), "0.62 0.64 0.66 1", euler=(0, a, 0)))
    g.append(_box((0.012, 0.11, 0.012), (hx + 0.006, 0, hz), "0.40 0.41 0.43 1"))   # hinge
    body = f'<body name="furnace" pos="{xc:.4f} {yc:.4f} 0">' + "".join(g) + '</body>'
    return body + _ring("crucible", xc, yc, floor, CRU_R_IN, CRU_R_OUT, CRU_DEPTH, 36, graphite,
                        1.0, free=False, extra='friction="0.25 0.01 0.001"')


def _cup(name, x, y, z0):
    hb = (CUP_H - CUP_CHAMFER) / 2
    return (f'<body name="{name}" pos="{x:.4f} {y:.4f} {z0:.5f}"><freejoint/>'
            f'<geom type="cylinder" size="{CUP_R} {hb:.5f}" pos="0 0 {CUP_CHAMFER + hb:.5f}" '
            'rgba="0.80 0.82 0.85 1" mass="0.046" friction="0.4 0.01 0.001"/>'
            f'<geom type="mesh" mesh="cup_chamfer" pos="0 0 {CUP_CHAMFER / 2:.5f}" '
            'rgba="0.80 0.82 0.85 1" mass="0.001" friction="0.4 0.01 0.001"/>'
            f'<geom type="cylinder" size="0.00715 0.0004" pos="0 0 {CUP_H + 0.0004:.5f}" '
            'rgba="0.52 0.54 0.58 1" contype="0" conaffinity="0" group="2" mass="0.0001"/>'
            '</body>')


TASKS = {
    "banana_in_bowl": {
        "instruction": "Pick up the banana and place it in the bowl",
        "episode_length_s": 120.0,
        "source": "the AMP paper's demo task (RoboLab BananaInBowlTask), on the PiPER",
    },
    "tape_to_shelf": {
        "instruction": "Pick up the green tape and place it on the black shelf",
        "episode_length_s": 150.0,
        "source": "robot-arms #30 (Move tape onto shelf)",
    },
    "vial_in_rack": {
        "instruction": "Put the vial with the red cap into the empty slot of the blue rack",
        "episode_length_s": 150.0,
        "source": "robot-arms #21 (loading vials into the CubXL: a pocket with 2 mm clearance)",
    },
    "print_off_a1_mini": {
        "instruction": ("Take the finished print off the 3D printer's build plate and put it on "
                        "the black shelf. Leave the build plate on the printer."),
        "episode_length_s": 180.0,
        "source": "robot-arms #86 and PR #77, byu-vcl PR #402: clearing the A1 mini's plate",
        # the printer is to the arm's right, so both scene cameras look at it from the room side
        "cameras": {"left": ((0.62, -0.10, 0.50), (0.08, -0.36, 0.07)),
                    "right": ((0.50, -0.80, 0.48), (0.08, -0.36, 0.07))},
        "workspace": (-0.20, 0.65, -0.60, 0.45, -0.02, 0.60),
    },
    "auger_swap": {
        "instruction": ("Swap the powder doser's auger: put the auger that is in the doser's two "
                        "clips into the empty slot of the auger rack, then snap the new auger "
                        "from the rack into the doser's clips."),
        "episode_length_s": 300.0,
        "source": "robot-arms #42, PR #44, PR #83: swapping the doser's clip-in auger",
    },
    "atomizer_charge": {
        "instruction": ("Load the four charge cups from the tray into the atomizer's crucible, "
                        "standing upright around the sealing rod."),
        "episode_length_s": 300.0,
        "source": "digital-alloy-lab #251/PR #253 (SOP step 5), #152, PR #179: charging the "
                  "rePowder's crucible",
    },
}


def _objects(task: str, rng: np.random.Generator) -> tuple[str, dict]:
    j = lambda s: float(rng.uniform(-s, s))  # noqa: E731
    if task == "banana_in_bowl":
        bx, by = 0.27 + j(0.02), 0.11 + j(0.02)
        kx, ky = 0.30 + j(0.02), -0.12 + j(0.02)
        xml = _banana("banana", bx, by, 0.4 + j(0.5)) + _bowl("bowl", kx, ky)
        return xml, {"bowl_xy": (kx, ky)}
    if task == "tape_to_shelf":
        tx, ty = 0.25 + j(0.015), 0.0 + j(0.015)
        sx, sy = 0.43, 0.0 + j(0.02)
        xml = (_ring("tape", tx, ty, 0.0, 0.033, 0.044, 0.025, 28, "0.15 0.65 0.25 1", 0.06,
                     extra='friction="1.2 0.02 0.002"')
               + f'<body name="shelf" pos="{sx} {sy} 0"><geom type="box" size="0.07 0.13 0.04" '
                 f'pos="0 0 0.04" rgba="0.06 0.06 0.07 1"/></body>')
        return xml, {"shelf": (sx, sy, 0.08, 0.07, 0.13)}
    if task == "vial_in_rack":
        rx, ry = 0.36 + j(0.01), -0.10 + j(0.01)
        empty = int(rng.integers(0, 3))
        ys = [ry + (k - 1) * RACK_PITCH for k in range(3)]
        xml = _rack("rack", rx, ry)
        for k, y in enumerate(ys):
            if k != empty:
                xml += _vial(f"vial_blue{k}", rx, y, "0.15 0.3 0.85 1", z0=0.0061)
        vx, vy = 0.25 + j(0.02), 0.12 + j(0.02)
        xml += _vial("vial", vx, vy, "0.85 0.12 0.12 1")
        return xml, {"slot": (rx, ys[empty])}
    if task == "print_off_a1_mini":
        cx, cy = A1_CENTER[0] + j(0.005), A1_CENTER[1] + j(0.005)
        px, py = cx + A1_BED_FWD, cy                    # bed forward = toward world +x
        tx, ty = px + 0.015 + j(0.015), py + j(0.02)    # the print near the plate's centre
        sx, sy = cx + 0.1575 + 0.0975, cy               # the black shelf in front of the printer
        xml = (_a1_mini(cx, cy) + _build_plate(px, py)
               + _print_part(tx, ty, A1_BED_TOP + 2 * A1_PLATE[2], float(rng.uniform(0, math.pi)))
               + f'<body name="shelf" pos="{sx:.4f} {sy:.4f} 0">'
               + _box((0.065, 0.120, 0.0325), (0, 0, 0.0325), "0.07 0.07 0.08 1") + '</body>')
        return xml, {"plate": (px, py, A1_BED_TOP + A1_PLATE[2]), "shelf": (sx, sy, 0.065, 0.065, 0.12),
                     "_assets": _hex_mesh("print_hex", *PRINT_HEX),
                     "_equality": '<weld name="print_bond" body1="build_plate" body2="print" '
                                  'anchor="0 0 0"/>'}
    if task == "auger_swap":
        x_out, yd = 0.50 + j(0.005), 0.0 + j(0.01)
        slots = (-0.165, -0.235)
        new_slot = int(rng.integers(0, 2))
        xml = (_doser(x_out, yd) + _auger("auger_old", x_out, yd, AXIS_H + 0.0002, "0.90 0.88 0.82 1")
               + _auger_rack(x_out, slots)
               + _auger("auger_new", x_out, slots[new_slot], RACK_H + 0.0003, "0.55 0.75 0.95 1"))
        return xml, {"doser": (x_out, yd, AXIS_H), "rack_slot": (x_out, slots[1 - new_slot], RACK_H)}
    if task == "atomizer_charge":
        xc, yc = 0.30 + j(0.01), 0.09 + j(0.01)       # clear of the arm's home pose
        tx, ty = 0.16 + j(0.01), -0.21 + j(0.01)
        pitch, rgba = 0.040, "0.30 0.30 0.33 1"
        tray = [_box((0.040, 0.040, 0.003), (0, 0, 0.003), rgba)]
        for k in range(4):
            ox, oy = (k % 2 - 0.5) * pitch, (k // 2 - 0.5) * pitch
            w = 0.0105 + 0.0015                       # 1 mm clearance round each cup, 3 mm walls
            for sx_, sy_, hx_, hy_ in ((w, 0, 0.0015, w + 0.0015), (-w, 0, 0.0015, w + 0.0015),
                                       (0, w, w + 0.0015, 0.0015), (0, -w, w + 0.0015, 0.0015)):
                tray.append(_box((hx_, hy_, 0.0075), (ox + sx_, oy + sy_, 0.0135), rgba))
        xml = _furnace(xc, yc) + (f'<body name="cup_tray" pos="{tx:.4f} {ty:.4f} 0">'
                                  + "".join(tray) + '</body>')
        for k in range(4):
            ox, oy = (k % 2 - 0.5) * pitch, (k // 2 - 0.5) * pitch
            xml += _cup(f"cup{k}", tx + ox, ty + oy, 0.006)
        return xml, {"crucible": (xc, yc, CRU_RIM - CRU_DEPTH, CRU_RIM),
                     "_assets": _frustum_mesh("cup_chamfer", CUP_R - CUP_CHAMFER, CUP_R, CUP_CHAMFER)}
    raise ValueError(f"unknown task {task!r}; known: {', '.join(TASKS)}")


def _robot_xml() -> str:
    """piper.xml with a wrist camera on link6, a stronger gripper servo and no keyframe."""
    src = (MENAGERIE / "piper.xml").read_text()
    src = re.sub(r"<keyframe>.*?</keyframe>", "", src, flags=re.S)
    # wrist camera: 6 cm off the finger plane on link6's -x side, looking along the approach
    # (+z) tilted 12 degrees toward the fingers; image right = link6 +y (the closing axis)
    th = math.radians(12)
    cam_x = (0.0, 1.0, 0.0)
    look = (math.sin(th), 0.0, math.cos(th))
    up = (math.cos(th), 0.0, -math.sin(th))
    cam = (f'<camera name="wrist" pos="-0.065 0 0.005" xyaxes="{cam_x[0]} {cam_x[1]} {cam_x[2]} '
           f'{up[0]:.5f} {up[1]:.5f} {up[2]:.5f}" fovy="{FOVY["wrist"]}"/>'
           '<site name="tcp" pos="0 0 0.115" size="0.004" rgba="1 0 0 0" group="5"/>')
    del look
    src = src.replace('<joint name="joint6" axis="0 0 1" range="-3.14 3.14"/>',
                      '<joint name="joint6" axis="0 0 1" range="-3.14 3.14"/>' + cam, 1)
    src = src.replace('<position name="gripper" joint="joint7" class="finger" kp="40" kv="5"/>',
                      f'<position name="gripper" joint="joint7" class="finger" kp="{GRIPPER_KP}" '
                      'kv="20"/>', 1)
    # finger pads: more friction, torsional friction so a held part turns less
    src = src.replace('<default class="finger">',
                      '<default class="finger"><geom friction="1.5 0.05 0.005" condim="4"/>', 1)
    return src


def scene_xml(task: str, seed: int) -> str:
    rng = np.random.default_rng(seed)
    objs, meta = _objects(task, rng)
    assets, equality = meta.pop("_assets", ""), meta.pop("_equality", "")
    cams = "".join(
        f'<camera name="{n}" pos="{p[0]} {p[1]} {p[2]}" xyaxes="{_look_at(p, t)}" '
        f'fovy="{FOVY[n]}"/>' for n, (p, t) in TASKS[task].get("cameras", SCENE_CAMERAS).items())
    xml = f"""<mujoco model="piper_{task}">
  <include file="piper_amp.xml"/>
  <option timestep="0.002" cone="elliptic" impratio="10" noslip_iterations="3"/>
  <visual><headlight diffuse="0.55 0.55 0.55" ambient="0.35 0.35 0.35" specular="0 0 0"/>
    <quality shadowsize="0"/><map znear="0.01" zfar="8"/></visual>
  <asset>
    <texture type="2d" name="wood" builtin="flat" rgb1="0.62 0.52 0.40" width="64" height="64"/>
    <material name="table" texture="wood" rgba="0.75 0.66 0.55 1"/>
    <texture type="skybox" builtin="gradient" rgb1="0.85 0.87 0.9" rgb2="0.6 0.62 0.65"
      width="256" height="256"/>
    {assets}
  </asset>
  <worldbody>
    <light pos="0.3 0.3 1.6" dir="0 -0.2 -1" diffuse="0.5 0.5 0.5" castshadow="false"/>
    <light pos="0.3 -0.4 1.4" dir="0 0.3 -1" diffuse="0.35 0.35 0.35" castshadow="false"/>
    <geom name="table" type="box" size="0.55 0.6 0.02" pos="0.30 0 -0.02" material="table"/>
    <geom name="floor" type="plane" size="3 3 0.1" pos="0 0 -0.75" rgba="0.3 0.3 0.32 1"/>
    {cams}
    {objs}
  </worldbody>
  {f"<equality>{equality}</equality>" if equality else ""}
</mujoco>"""
    return xml, meta


def build_model(task: str, seed: int) -> tuple[mujoco.MjModel, dict]:
    WORK.mkdir(parents=True, exist_ok=True)
    assets = WORK / "assets"
    if not assets.exists():
        shutil.copytree(MENAGERIE / "assets", assets)
    (WORK / "piper_amp.xml").write_text(_robot_xml())
    xml, meta = scene_xml(task, seed)
    path = WORK / f"scene_{task}.xml"
    path.write_text(xml)
    return mujoco.MjModel.from_xml_path(str(path)), meta


# ---------------------------------------------------------------------------- AMP declarations

def _pose(pos, quat) -> np.ndarray:
    R = np.zeros(9)
    mujoco.mju_quat2Mat(R, np.asarray(quat, dtype=np.float64))
    T = np.eye(4)
    T[:3, :3], T[:3, 3] = R.reshape(3, 3), pos
    return T


def _visual_mesh(m, g):
    mid = m.geom_dataid[g]
    va, vn = m.mesh_vertadr[mid], m.mesh_vertnum[mid]
    fa, fn = m.mesh_faceadr[mid], m.mesh_facenum[mid]
    v = m.mesh_vert[va:va + vn].astype(np.float64)
    f = m.mesh_face[fa:fa + fn].astype(np.uint32)
    T = _pose(m.geom_pos[g], m.geom_quat[g])
    return (v @ T[:3, :3].T + T[:3, 3]).astype(np.float32), f


_TYPES = {int(mujoco.mjtJoint.mjJNT_HINGE): "revolute", int(mujoco.mjtJoint.mjJNT_SLIDE): "prismatic"}


def export_robot(m) -> tuple[RobotDescription, dict]:
    """The PiPER subtree (base_link and below) as AMP's /sim/robot description + visual meshes."""
    r = mujoco.mj_name2id(m, mujoco.mjtObj.mjOBJ_BODY, ROOT)
    bodies = [r] + [b for b in range(r + 1, m.nbody) if _under(m, b, r)]
    links, joints, meshes = [], [], {}
    for b in bodies:
        name = m.body(b).name
        names = []
        for g in range(m.ngeom):
            if (m.geom_bodyid[g] == b and m.geom_group[g] == VISUAL_GROUP
                    and m.geom_type[g] == mujoco.mjtGeom.mjGEOM_MESH):
                key = f"{name}.{m.geom(g).name or g}"
                meshes[key] = _visual_mesh(m, g)
                names.append(key)
        links.append(LinkSpec(name=name, meshes=tuple(names)))
        if b == r:
            continue
        parent = int(m.body_parentid[b])
        origin = tuple(_pose(m.body_pos[b], m.body_quat[b]).reshape(-1))
        js = [j for j in range(m.njnt) if m.jnt_bodyid[j] == b]
        if not js:
            joints.append(JointSpec(name=f"{name}_fixed", type="fixed", parent=m.body(parent).name,
                                    child=name, origin=origin))
            continue
        j = js[0]
        limits = tuple(map(float, m.jnt_range[j])) if m.jnt_limited[j] else (0.0, 0.0)
        joints.append(JointSpec(name=m.joint(j).name, type=_TYPES[int(m.jnt_type[j])],
                                parent=m.body(parent).name, child=name, origin=origin,
                                axis=tuple(map(float, m.jnt_axis[j])), limits=limits))
    return RobotDescription(root=ROOT, links=tuple(links), joints=tuple(joints)), meshes


def _under(m, b, root) -> bool:
    p = b
    while p not in (0, root):
        p = m.body_parentid[p]
    return p == root


WORKSPACE = (-0.15, 0.65, -0.45, 0.45, -0.02, 0.60)


def embodiment(sha: str, workspace=WORKSPACE) -> EmbodimentSpec:
    T_flange_ee = tuple(np.eye(4).reshape(-1))
    T_ee_tcp = np.eye(4)
    T_ee_tcp[2, 3] = TCP_Z
    gripper = GripperSpec(kind="parallel_jaw", model="linear", stroke_m=STROKE_M,
                          max_width_m=0.066, closed_empty=0.97, held_below=0.93,
                          finger_joints=FINGERS, finger_open=FINGER_OPEN,
                          finger_closed=FINGER_CLOSED, tip_reach_m=(TIP_REACH, TIP_REACH))
    arm = ArmSpec(name=ARM, joints=JOINTS, q_min=Q_MIN, q_max=Q_MAX, qd_max=QD_MAX,
                  q_home=Q_HOME, base_link=ROOT, flange_link=FLANGE,
                  kinematics=Kinematics("chain", sha))
    hand = EndEffectorSpec(name=HAND, arm=ARM, ee_link=FLANGE, T_flange_ee=T_flange_ee,
                           T_ee_tcp=tuple(T_ee_tcp.reshape(-1)), gripper=gripper,
                           closing_axis="y", approach_axis="z")
    cams = (CameraSpec("left", CAM_W, CAM_H, mount="root", depth=True, role="scene"),
            CameraSpec("right", CAM_W, CAM_H, mount="root", depth=True, role="scene"),
            CameraSpec("wrist", CAM_W, CAM_H, mount=FLANGE, depth=True, role="wrist"))
    return EmbodimentSpec(
        name=NAME, arms=(arm,), end_effectors=(hand,), cameras=cams,
        action=(ActionSegment("joint_pos_abs", ARM, len(JOINTS)),
                ActionSegment("gripper01", HAND, 1)),
        control_dt=CONTROL_DT,
        drive=DriveSpec(tau_s=0.10, tau_band_s=(0.04, 0.30)),
        workspace=WorkspaceSpec(support="table", box=tuple(workspace)),
    )


# ------------------------------------------------------------------------------------- adapter

class PiperAdapter:
    """amp.robots.capgym.adapter.SimAdapter for the simulated PiPER."""

    features = ("grade",)

    def __init__(self, seed: int | None = 0):
        self.seed = 0 if seed is None else int(seed)
        self.m, self.meta = build_model("banana_in_bowl", 0)
        self._desc, self._meshes = export_robot(self.m)
        self._sha = description_sha256(self._desc, self._meshes)
        # one link client serves one task's episodes here, so a task can widen the perception
        # box (PIPER_TASK, set by episode_up.sh); the embodiment is sent once, at hello
        task = os.environ.get("PIPER_TASK", "")
        self._spec = embodiment(self._sha, TASKS.get(task, {}).get("workspace", WORKSPACE))
        self.task = None
        self.d = None
        self._renderer = None
        self._frames_dir = None
        self._nframe = 0
        self._hooks = []
        self.events = []

    # declarations
    def embodiment(self):
        return self._spec

    def robot_description(self):
        return self._desc, self._meshes

    def success_checks(self) -> str:
        return "end"

    def tasks(self) -> list[dict]:
        return [{"name": k, "instruction": v["instruction"], "attributes": [v["source"]],
                 "episode_length_s": v["episode_length_s"]} for k, v in TASKS.items()]

    def horizon(self):
        return None

    def control_dt(self) -> float:
        return CONTROL_DT

    # scene
    def load(self, task: str) -> None:
        if task not in TASKS:
            raise ValueError(f"unknown task {task!r}")
        self.task = task

    def reset(self, episode: int) -> None:
        if self.task is None:
            raise ValueError("load a task first")
        if not 0 <= int(episode) < 1000:
            raise ValueError(f"{self.task} has episodes 0..999, not {episode}")
        self.close()
        self.m, self.meta = build_model(self.task, 1000 * self.seed + int(episode))
        self.d = mujoco.MjData(self.m)
        self._ids()
        self.d.qpos[self._qadr] = Q_HOME
        self.d.qpos[self._fadr] = FINGER_OPEN
        self.d.ctrl[self._act] = Q_HOME
        self.d.ctrl[self._gact] = FINGER_OPEN[0]
        mujoco.mj_forward(self.m, self.d)
        self._task_physics()
        for _ in range(int(0.6 / self.m.opt.timestep)):  # let objects settle
            self._step()
        self._renderer = mujoco.Renderer(self.m, CAM_H, CAM_W)
        rec = os.environ.get("PIPER_FRAMES_DIR")
        self._nframe = 0
        self._frames_dir = None
        if rec:
            self._frames_dir = Path(rec) / f"{self.task}_ep{int(episode)}"
            self._frames_dir.mkdir(parents=True, exist_ok=True)

    def _ids(self):
        m = self.m
        jid = [mujoco.mj_name2id(m, mujoco.mjtObj.mjOBJ_JOINT, j) for j in JOINTS]
        fid = [mujoco.mj_name2id(m, mujoco.mjtObj.mjOBJ_JOINT, j) for j in FINGERS]
        self._qadr = np.array([m.jnt_qposadr[j] for j in jid])
        self._vadr = np.array([m.jnt_dofadr[j] for j in jid])
        self._fadr = np.array([m.jnt_qposadr[j] for j in fid])
        self._act = np.array([mujoco.mj_name2id(m, mujoco.mjtObj.mjOBJ_ACTUATOR, j)
                              for j in JOINTS])
        self._gact = mujoco.mj_name2id(m, mujoco.mjtObj.mjOBJ_ACTUATOR, "gripper")
        self._flange = mujoco.mj_name2id(m, mujoco.mjtObj.mjOBJ_BODY, FLANGE)
        self._base = mujoco.mj_name2id(m, mujoco.mjtObj.mjOBJ_BODY, ROOT)

    # sensing
    def _camera(self, name: str) -> CameraImage:
        m, d, r = self.m, self.d, self._renderer
        cid = mujoco.mj_name2id(m, mujoco.mjtObj.mjOBJ_CAMERA, name)
        r.update_scene(d, camera=cid)
        rgb = r.render().copy()
        r.enable_depth_rendering()
        r.update_scene(d, camera=cid)
        depth = r.render().astype(np.float32).copy()
        r.disable_depth_rendering()
        depth[(depth <= 0) | (depth > 5.0)] = 0.0
        fy = 0.5 * CAM_H / math.tan(math.radians(m.cam_fovy[cid]) / 2)
        K = np.array([[fy, 0, (CAM_W - 1) / 2], [0, fy, (CAM_H - 1) / 2], [0, 0, 1.0]])
        T = np.eye(4)
        T[:3, :3] = d.cam_xmat[cid].reshape(3, 3) @ np.diag([1.0, -1.0, -1.0])  # GL -> OpenCV
        T[:3, 3] = d.cam_xpos[cid]
        return CameraImage(rgb=rgb, depth=depth, K=K, T_root_cam=T)

    def gripper_measured(self) -> float:
        g = float(self.d.qpos[self._fadr[0]])
        return float(np.clip(1.0 - g / FINGER_OPEN[0], 0.0, 1.0))

    def observe(self) -> Frame:
        d = self.d
        q = d.qpos[self._qadr].copy()
        pos = d.xpos[self._flange].copy()
        quat = d.xquat[self._flange].copy()
        cams = {n: self._camera(n) for n in ("left", "right", "wrist")}
        self._record(cams)
        return Frame.single(q, self.gripper_measured(), pos, quat, cams, ee=HAND)

    def _record(self, cams) -> None:
        """One composite JPEG per control step (left | right | wrist), for the episode video."""
        if not self._frames_dir:
            return
        import cv2
        tiles = [cv2.resize(cams[n].rgb, (480, 360), interpolation=cv2.INTER_AREA)
                 for n in ("left", "right", "wrist")]
        img = np.concatenate(tiles, axis=1)[:, :, ::-1].copy()
        t = self._nframe * CONTROL_DT
        cv2.putText(img, f"{self.task}  t={t:5.1f}s (executed motion)", (8, 22),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2, cv2.LINE_AA)
        cv2.imwrite(str(self._frames_dir / f"{self._nframe:05d}.jpg"), img,
                    [cv2.IMWRITE_JPEG_QUALITY, 85])
        self._nframe += 1

    # acting
    def apply(self, action) -> None:
        a = np.asarray(action, dtype=np.float64).reshape(-1)
        if a.shape != (7,):
            raise ValueError(f"action has 7 entries (6 joints, gripper), got {a.shape}")
        q = np.clip(a[:6], Q_MIN, Q_MAX)
        self.d.ctrl[self._act] = q
        g = float(np.clip(a[6], 0.0, 1.0))
        self.d.ctrl[self._gact] = FINGER_OPEN[0] * (1.0 - g) + FINGER_CLOSED[0] * g - 0.004 * g
        for _ in range(int(round(CONTROL_DT / self.m.opt.timestep))):
            self._step()

    # task physics: the A1 mini's magnetic sheet and the print's bond, the doser's snap clips
    def _step(self) -> None:
        mujoco.mj_step(self.m, self.d)
        for hook in self._hooks:
            hook()

    def _task_physics(self) -> None:
        m = self.m
        self._hooks = []
        self.events = []
        bid = lambda n: mujoco.mj_name2id(m, mujoco.mjtObj.mjOBJ_BODY, n)  # noqa: E731
        if self.task == "print_off_a1_mini":
            self._plate_b = bid("build_plate")
            self._bond = mujoco.mj_name2id(m, mujoco.mjtObj.mjOBJ_EQUALITY, "print_bond")
            self._bond_on = True
            self._mag_f = 0.0
            self._hooks += [self._magnet, self._bond_check]
        elif self.task == "auger_swap":
            self._augers = [bid("auger_old"), bid("auger_new")]
            self._auger_geoms = {g for g in range(m.ngeom) if m.geom_bodyid[g] in self._augers}
            self._lips = [[g for g in range(m.ngeom) if (m.geom(g).name or "").startswith(f"clip{k}_lip")]
                          for k in range(2)]
            self._lip_set = [set(x) for x in self._lips]
            self._lip_ct = {g: (int(m.geom_contype[g]), int(m.geom_conaffinity[g]))
                            for x in self._lips for g in x}
            self._clip_on = [True, True]
            self._clip_left = [None, None]   # the auger that was seated when the clip opened
            x_out, yd, h = self.meta["doser"]
            self._clip_c = [np.array([x_out - (a + b) / 2, yd, h]) for a, b in CLIPS_S]
            self._hooks.append(self._clips)

    def _magnet(self) -> None:
        d, b = self.d, self._plate_b
        p, R = d.xpos[b], d.xmat[b].reshape(3, 3)
        px, py, pz = self.meta["plate"]
        gap = p[2] - pz
        over = abs(p[0] - px) < 0.10 and abs(p[1] - py) < 0.10
        flat = R[2, 2] > math.cos(math.radians(8))
        f = MAGNET_N * float(np.clip(1.0 - gap / 0.003, 0.0, 1.0)) if over and flat else 0.0
        d.xfrc_applied[b, 2] -= f - self._mag_f      # only this hook's share of the plate's load
        self._mag_f = f

    def _eq_force(self, eq: int) -> np.ndarray:
        d = self.d
        n = d.nefc
        rows = np.nonzero((d.efc_type[:n] == mujoco.mjtConstraint.mjCNSTR_EQUALITY)
                          & (d.efc_id[:n] == eq))[0]
        return d.efc_force[rows] if len(rows) == 6 else np.zeros(6)

    def _bond_check(self) -> None:
        if not self._bond_on:
            return
        f = self._eq_force(self._bond)
        tension, shear, twist = max(f[2], 0.0), math.hypot(f[0], f[1]), abs(f[5]) / 2
        load = (tension / BOND[0]) ** 2 + (shear / BOND[1]) ** 2 + (twist / BOND[2]) ** 2
        if load > 1.0:
            self.d.eq_active[self._bond] = 0
            self._bond_on = False
            self.events.append({"t": round(float(self.d.time), 3), "event": "print bond broke",
                                "tension_N": round(float(tension), 2), "shear_N": round(shear, 2),
                                "twist_Nm": round(twist, 4)})

    def _axis(self, b):
        """An auger's axis segment (outlet end, cap end) in world coordinates."""
        p, R = self.d.xpos[b], self.d.xmat[b].reshape(3, 3)
        return p, p + AUG_LEN * R[:, 0]

    @staticmethod
    def _seg_dist(c, a, b, s0=0.0, s1=1.0):
        ab = b - a
        t = float(np.clip(np.dot(c - a, ab) / np.dot(ab, ab), s0, s1))
        return float(np.linalg.norm(c - (a + t * ab))), t

    def _clips(self) -> None:
        """Each clip's two snap arms ("lips") hold a seated tube until the tube pushes on them
        with more than CLIP_N, then let it through (contacts off) until the tube is seated
        again or clear of the clip. A rigid-body stand-in for the compliant PLA arms."""
        m, d = self.m, self.d
        for k in range(2):
            lips = self._lip_set[k]
            if self._clip_on[k]:
                f = 0.0
                c6 = np.zeros(6)
                for i in range(d.ncon):
                    g1, g2 = int(d.contact.geom1[i]), int(d.contact.geom2[i])
                    if (g1 in lips and g2 in self._auger_geoms) or (g2 in lips and g1 in self._auger_geoms):
                        mujoco.mj_contactForce(m, d, i, c6)
                        f += abs(c6[0])
                if f > CLIP_N:
                    for g in self._lips[k]:
                        m.geom_contype[g] = m.geom_conaffinity[g] = 0
                    self._clip_on[k] = False
                    # the tube being pulled out may not re-snap until it has left the seat
                    near = min(self._augers, key=lambda b: self._seg_dist(
                        self._clip_c[k], *self._axis(b), 0.0, AUG_TUBE / AUG_LEN)[0])
                    dn = self._seg_dist(self._clip_c[k], *self._axis(near), 0.0, AUG_TUBE / AUG_LEN)[0]
                    self._clip_left[k] = near if dn < 0.003 else None
                    self.events.append({"t": round(float(d.time), 3), "event": f"clip{k} opened",
                                        "force_N": round(f, 1)})
            else:
                c = self._clip_c[k]
                seated, clear = False, True
                for b in self._augers:
                    a0, a1 = self._axis(b)
                    dt, t = self._seg_dist(c, a0, a1)
                    tube = self._seg_dist(c, a0, a1, 0.0, AUG_TUBE / AUG_LEN)[0]
                    gear = self._seg_dist(c, a0, a1, AUG_GEAR[1] / AUG_LEN, AUG_GEAR[2] / AUG_LEN)[0]
                    cap = self._seg_dist(c, a0, a1, AUG_TUBE / AUG_LEN, 1.0)[0]
                    if b == self._clip_left[k] and tube > 0.003:
                        self._clip_left[k] = None
                    level = abs((a1 - a0)[0]) / AUG_LEN > math.cos(math.radians(4))
                    if tube < 0.0008 and level and b != self._clip_left[k]:
                        seated = True
                    reach = CLIP_R_IN + CLIP_WALL + 0.008
                    if tube < AUG_R + reach or gear < AUG_GEAR[0] + reach or cap < AUG_CAP_R + reach:
                        clear = False
                if seated or clear:
                    for g in self._lips[k]:
                        m.geom_contype[g], m.geom_conaffinity[g] = self._lip_ct[g]
                    self._clip_on[k] = True
                    self.events.append({"t": round(float(d.time), 3),
                                        "event": f"clip{k} closed ({'snapped on a tube' if seated else 'empty'})"})

    def clip_seated(self, k: int, body: str) -> bool:
        """Clip k holds `body`'s tube: arms closed and the tube within 0.8 mm of the seat."""
        b = mujoco.mj_name2id(self.m, mujoco.mjtObj.mjOBJ_BODY, body)
        a0, a1 = self._axis(b)
        return bool(self._clip_on[k]
                    and self._seg_dist(self._clip_c[k], a0, a1, 0.0, AUG_TUBE / AUG_LEN)[0] < 0.0008)

    # scoring (reads the simulator; never shown to the agent)
    def _body(self, name):
        b = mujoco.mj_name2id(self.m, mujoco.mjtObj.mjOBJ_BODY, name)
        return self.d.xpos[b].copy(), self.d.xmat[b].reshape(3, 3).copy()

    def _finger_contacts(self, name: str) -> int:
        """Contacts between body `name` and the gripper (link6's pads and both fingers)."""
        m, d = self.m, self.d
        obj = mujoco.mj_name2id(m, mujoco.mjtObj.mjOBJ_BODY, name)
        grip = {mujoco.mj_name2id(m, mujoco.mjtObj.mjOBJ_BODY, b)
                for b in (FLANGE, "link7", "link8")}
        g = np.asarray(d.contact.geom[:d.ncon], dtype=int).reshape(-1, 2)
        b = m.geom_bodyid[g] if len(g) else np.zeros((0, 2), dtype=int)
        return int(sum(1 for b1, b2 in b
                       if (b1 == obj and b2 in grip) or (b2 == obj and b1 in grip)))

    def success(self) -> tuple[bool, float]:
        """Placed where the instruction says AND let go: a part still held by (or jammed on)
        the gripper does not count. Before 2026-11-26 the release was not checked, which scored
        tape_to_shelf-ep0 (gripper still in the tape's hole) as a success."""
        if self.d is None:
            return False, 0.0
        held = {"banana_in_bowl": "banana", "tape_to_shelf": "tape", "vial_in_rack": "vial",
                "print_off_a1_mini": ["print", "build_plate"],
                "auger_swap": ["auger_old", "auger_new"],
                "atomizer_charge": [f"cup{k}" for k in range(4)]}.get(self.task)
        detail = {}
        if self.task == "banana_in_bowl":
            p, _ = self._body("banana")
            k, _ = self._body("bowl")
            placed = bool(np.hypot(*(p[:2] - k[:2])) < 0.070 and k[2] - 0.01 < p[2] < k[2] + 0.07)
        elif self.task == "tape_to_shelf":
            p, R = self._body("tape")
            sx, sy, top, hx, hy = self.meta["shelf"]
            placed = bool(abs(p[0] - sx) < hx + 0.01 and abs(p[1] - sy) < hy + 0.01
                          and top - 0.01 < p[2] < top + 0.06)
        elif self.task == "vial_in_rack":
            p, R = self._body("vial")
            sx, sy = self.meta["slot"]
            placed = bool(np.hypot(p[0] - sx, p[1] - sy) < 0.006 and p[2] < 0.012
                          and R[2, 2] > math.cos(math.radians(12)))
        elif self.task == "print_off_a1_mini":
            # on the shelf (any face down), and the plate still seated on the bed
            p, R = self._body("print")
            sx, sy, top, hx, hy = self.meta["shelf"]
            on_shelf = bool(abs(p[0] - sx) < hx and abs(p[1] - sy) < hy
                            and top - 0.005 < p[2] < top + 0.05)
            q, Rq = self._body("build_plate")
            px, py, pz = self.meta["plate"]
            plate_ok = bool(math.hypot(q[0] - px, q[1] - py) < 0.005 and abs(q[2] - pz) < 0.002
                            and Rq[2, 2] > math.cos(math.radians(3)))
            placed = on_shelf and plate_ok
            detail = {"print_on_shelf": on_shelf, "plate_seated": plate_ok,
                      "bond_broken": not self._bond_on,
                      "plate_offset_mm": round(1000 * math.hypot(q[0] - px, q[1] - py), 1)}
        elif self.task == "auger_swap":
            x_out, yd, h = self.meta["doser"]
            b_new = mujoco.mj_name2id(self.m, mujoco.mjtObj.mjOBJ_BODY, "auger_new")
            a0, a1 = self._axis(b_new)
            ax = (a1 - a0) / AUG_LEN
            gear = a0 + ax * (AUG_GEAR[1] + AUG_GEAR[2]) / 2
            pinion = np.array([x_out - (AUG_GEAR[1] + AUG_GEAR[2]) / 2, yd, h])
            gear_mm = abs(float(np.dot(gear - pinion, ax))) * 1000
            seated = [self.clip_seated(k, "auger_new") for k in range(2)]
            new_ok = bool(all(seated) and gear_mm < 3.0 and ax[0] < -0.99)
            # the old auger lying in the empty slot's two cradles (either way round)
            rx, ry, rh = self.meta["rack_slot"]
            b_old = mujoco.mj_name2id(self.m, mujoco.mjtObj.mjOBJ_BODY, "auger_old")
            o0, o1 = self._axis(b_old)
            oax = (o1 - o0) / AUG_LEN
            on_cradles = True
            for s0, s1 in CRADLES_S:
                c = np.array([rx - (s0 + s1) / 2, ry, rh])
                dist, t = self._seg_dist(c, o0, o1, 0.0, AUG_TUBE / AUG_LEN)
                on_cradles &= dist < 0.004
            old_ok = bool(on_cradles and abs(oax[0]) > 0.98)
            placed = new_ok and old_ok
            detail = {"new_in_clips": seated, "gear_to_pinion_mm": round(gear_mm, 1),
                      "new_cap_toward_arm": bool(ax[0] < -0.99), "old_in_empty_slot": old_ok}
        elif self.task == "atomizer_charge":
            xc, yc, floor, rim = self.meta["crucible"]
            cups = []
            for k in range(4):
                p, R = self._body(f"cup{k}")
                r = math.hypot(p[0] - xc, p[1] - yc)
                tilt = math.degrees(math.acos(float(np.clip(R[2, 2], -1, 1))))
                cups.append({"r_mm": round(1000 * r, 1), "bottom_mm": round(1000 * (p[2] - floor), 1),
                             "tilt_deg": round(tilt, 1),
                             "in": bool(r < CRU_R_IN and p[2] - floor < 0.004 and tilt < 6.0)})
            placed = all(c["in"] for c in cups)
            detail = {"cups": cups}
        else:
            placed = False
        names = held if isinstance(held, list) else [held] if held else []
        touching = sum(self._finger_contacts(n) for n in names)
        ok = placed and touching == 0
        if self._frames_dir:
            import json
            (self._frames_dir.parent / f"{self.task}_truth.json").write_text(json.dumps(
                {"success": ok, "placed": placed, "gripper_contacts": touching,
                 "gripper_cmd_closed": float(self.d.ctrl[self._gact] < FINGER_OPEN[0] / 2),
                 "detail": detail, "events": self.events[-40:],
                 "objects": self.ground_truth(), "meta": {
                     k: list(v) for k, v in self.meta.items()}}, indent=1))
        return ok, float(ok)

    def ground_truth(self) -> dict:
        """For the post-episode report only."""
        out = {}
        for b in range(self.m.nbody):
            n = self.m.body(b).name
            if self.m.body_jntnum[b] and self.m.jnt_type[self.m.body_jntadr[b]] == 0:
                out[n] = np.round(self.d.xpos[b], 4).tolist()
        return out

    def ended(self) -> bool:
        return False

    def idle(self) -> None:
        return None

    def close(self) -> None:
        if self._renderer is not None:
            try:
                self._renderer.close()
            except Exception:  # noqa: BLE001
                pass
            self._renderer = None


def make_adapter(*, task_set: str = "piper", cameras: str = "droid", seed: int | None = 0):
    return PiperAdapter(seed=seed)
