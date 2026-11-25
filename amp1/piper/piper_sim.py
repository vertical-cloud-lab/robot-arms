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
    cams = "".join(
        f'<camera name="{n}" pos="{p[0]} {p[1]} {p[2]}" xyaxes="{_look_at(p, t)}" '
        f'fovy="{FOVY[n]}"/>' for n, (p, t) in SCENE_CAMERAS.items())
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
  </asset>
  <worldbody>
    <light pos="0.3 0.3 1.6" dir="0 -0.2 -1" diffuse="0.5 0.5 0.5" castshadow="false"/>
    <light pos="0.3 -0.4 1.4" dir="0 0.3 -1" diffuse="0.35 0.35 0.35" castshadow="false"/>
    <geom name="table" type="box" size="0.55 0.6 0.02" pos="0.30 0 -0.02" material="table"/>
    <geom name="floor" type="plane" size="3 3 0.1" pos="0 0 -0.75" rgba="0.3 0.3 0.32 1"/>
    {cams}
    {objs}
  </worldbody>
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


def embodiment(sha: str) -> EmbodimentSpec:
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
        workspace=WorkspaceSpec(support="table", box=(-0.15, 0.65, -0.45, 0.45, -0.02, 0.60)),
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
        self._spec = embodiment(self._sha)
        self.task = None
        self.d = None
        self._renderer = None
        self._frames_dir = None
        self._nframe = 0

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
        for _ in range(int(0.6 / self.m.opt.timestep)):  # let objects settle
            mujoco.mj_step(self.m, self.d)
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
            mujoco.mj_step(self.m, self.d)

    # scoring (reads the simulator; never shown to the agent)
    def _body(self, name):
        b = mujoco.mj_name2id(self.m, mujoco.mjtObj.mjOBJ_BODY, name)
        return self.d.xpos[b].copy(), self.d.xmat[b].reshape(3, 3).copy()

    def success(self) -> tuple[bool, float]:
        if self.d is None:
            return False, 0.0
        if self.task == "banana_in_bowl":
            p, _ = self._body("banana")
            k, _ = self._body("bowl")
            ok = bool(np.hypot(*(p[:2] - k[:2])) < 0.070 and k[2] - 0.01 < p[2] < k[2] + 0.07)
        elif self.task == "tape_to_shelf":
            p, R = self._body("tape")
            sx, sy, top, hx, hy = self.meta["shelf"]
            ok = bool(abs(p[0] - sx) < hx + 0.01 and abs(p[1] - sy) < hy + 0.01
                      and top - 0.01 < p[2] < top + 0.06)
        elif self.task == "vial_in_rack":
            p, R = self._body("vial")
            sx, sy = self.meta["slot"]
            ok = bool(np.hypot(p[0] - sx, p[1] - sy) < 0.006 and p[2] < 0.012
                      and R[2, 2] > math.cos(math.radians(12)))
        else:
            ok = False
        if self._frames_dir:
            import json
            (self._frames_dir.parent / f"{self.task}_truth.json").write_text(json.dumps(
                {"success": ok, "objects": self.ground_truth(), "meta": {
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
