"""The PiPER as a scene Body tree, built from config/robot_piper.yaml.

Body i is DH frame i (kinematics/dh.py), so a hinge about each body's z axis reproduces
piper_sdk's FK exactly, and the engine's joint angles are the SDK's joint angles. Meshes and
inertias (assets/piper/, from AgileX's URDF via MuJoCo Menagerie) were re-expressed in those
same frames by tools/build_piper_assets.py, so they attach with no offset.

Gripper: two fingers on slide joints along the flange's -y and +y, coupled so they move
together (one motor and a rack on the real gripper). Each finger carries the lab's sleeve:
a TPU pad on its gripping face, 3.5 mm thick, ending at the fingertip (the TCP).
"""
from __future__ import annotations

import os

import numpy as np
import yaml

from ..config import deg, mm
from ..kinematics.dh import fixed_part
from ..kinematics.piper import PiperKinematics
from ..transforms import make_pose
from .scene import Body, Camera, Geom, Joint, Site

LINKS = ["link1", "link2", "link3", "link4", "link5", "link6"]


def _inertial(entry: dict, mesh_file: str | None) -> dict:
    """URDF inertial; its placeholder 1e-3 kg*m^2 inertias (links 5, 6 and the fingers) are
    replaced by a solid box the size of the mesh, which is far closer for parts this small."""
    I = list(entry["fullinertia_kgm2"])
    if np.allclose(I[:3], 1e-3) and np.allclose(I[3:], 0) and mesh_file and os.path.exists(mesh_file):
        lo, hi = _stl_bounds(mesh_file)
        a, b, c = hi - lo
        m = entry["mass_kg"]
        I = [m / 12 * (b * b + c * c), m / 12 * (a * a + c * c), m / 12 * (a * a + b * b), 0, 0, 0]
    return {"mass": entry["mass_kg"], "com": np.asarray(entry["com_m"]), "fullinertia": np.asarray(I)}


def _stl_bounds(path: str):
    """Bounds of a binary STL without extra dependencies."""
    data = np.fromfile(path, dtype=np.uint8)
    n = int(np.frombuffer(data[80:84].tobytes(), dtype=np.uint32)[0])
    rec = np.frombuffer(data[84:84 + 50 * n].tobytes(), dtype=np.dtype(
        [("n", "<f4", 3), ("v", "<f4", (3, 3)), ("a", "<u2")]))
    v = rec["v"].reshape(-1, 3)
    return v.min(0).astype(float), v.max(0).astype(float)


def build_piper(robot_cfg: dict, base_pose: np.ndarray, root: str) -> tuple[Body, list, dict]:
    """Returns (base body, equality constraints, info). base_pose: world pose of the base."""
    kin = PiperKinematics(robot_cfg)
    jc = robot_cfg["joints"]
    vis = robot_cfg["visual"]
    mesh_dir = os.path.join(root, vis["meshes"])
    with open(os.path.join(root, vis["inertials"])) as fh:
        inert = yaml.safe_load(fh)
    rgba = tuple(vis["color_rgba"])

    def mesh(name):
        f = os.path.join(mesh_dir, f"{name}.stl")
        return f if os.path.exists(f) else None

    def link_geoms(name):
        f = mesh(name)
        if f is None:  # no meshes: a capsule placeholder so the arm still shows and collides
            return [Geom(f"{name}_capsule", "capsule", (0.03, 0.02), np.eye(4), "arm", rgba, "arm")]
        return [Geom(f"{name}_visual", "mesh", (), np.eye(4), "arm", rgba, "none", mesh_file=f),
                Geom(f"{name}_collision", "mesh", (), np.eye(4), "arm", rgba, "arm", mesh_file=f)]

    base = Body("piper_base", pose=base_pose, kind="robot",
                geoms=link_geoms("base"), inertial=_inertial(inert["base"], mesh("base")))
    parent = base
    lims = deg(jc["limits_deg"])
    for i, (row, name) in enumerate(zip(kin.chain.rows, LINKS)):
        p, R = fixed_part(row)
        act = {"type": "motor", "limit": float(jc["max_torque_nm"][i])}
        body = Body(name, pose=make_pose(R, p), kind="robot", geoms=link_geoms(name),
                    joints=[Joint(jc["names"][i], "hinge", (0, 0, 1), tuple(lims[i]),
                                  damping=jc["damping_nms"][i], frictionloss=jc["frictionloss_nm"][i],
                                  armature=jc["armature_kgm2"][i], actuator=act)],
                    inertial=_inertial(inert[name], mesh(name)))
        parent.add(body)
        parent = body
    link6 = parent
    link6.sites.append(Site("flange", size=0.004, rgba=(0, 0, 1, 0.6)))
    link6.sites.append(Site("tcp", pose=make_pose(None, kin.tcp[:3, 3]), size=0.004, rgba=(1, 0, 0, 0.8)))

    cams = robot_cfg.get("_cameras", {})
    if "wrist" in cams:
        c = cams["wrist"]
        # Looks along the tool axis (flange +z); a camera looks along its own -z.
        R = np.diag([-1.0, 1.0, -1.0])
        link6.cameras.append(Camera("wrist", make_pose(R, mm(c["position"])), c["fovy_deg"],
                                    tuple(c["resolution"])))

    # --- gripper ---------------------------------------------------------------------------
    g = robot_cfg["gripper"]
    sl = g["sleeve"]
    t, w, L, tip = mm(sl["thickness_mm"]), mm(sl["width_mm"]), mm(sl["length_mm"]), mm(sl["tip_z_mm"])
    travel = tuple(mm(g["finger_travel_mm"]))
    # Fingers start where the sleeves touch: travel = sleeve thickness.
    lo = max(travel[0], float(t))
    finger_info = {}
    for k, sign in ((1, -1.0), (2, 1.0)):
        name = f"finger{k}"
        f = mesh(name)
        geoms = []
        if f:
            geoms.append(Geom(f"{name}_visual", "mesh", (), np.eye(4), "arm", (0.25, 0.25, 0.27, 1), "none",
                              mesh_file=f))
        # Finger body behind the sleeve (outer side), and the sleeve pad on the gripping face.
        # In the finger's own frame the gripping face is at y = 0; the other finger is toward
        # -sign (finger1 opens toward -y, so its face points +y).
        geoms.append(Geom(f"{name}_body", "box", (w / 2, 0.003, L / 2),
                          make_pose(None, (0, sign * 0.003, tip - L / 2)), "arm", (0.2, 0.2, 0.2, 1), "finger"))
        geoms.append(Geom(f"{name}_sleeve", "box", (w / 2, t / 2, L / 2),
                          make_pose(None, (0, -sign * t / 2, tip - L / 2)), sl["material"],
                          (0.15, 0.15, 0.15, 1), "finger"))
        jrange = (lo, travel[1])
        body = Body(name, pose=np.eye(4), kind="robot", geoms=geoms,
                    joints=[Joint(f"{name}_slide", "slide", (0, sign, 0), jrange, damping=2.0,
                                  armature=0.01,
                                  actuator=({"type": "motor", "limit": 2.0 * g["max_force_n"]} if k == 1 else None))],
                    inertial=_inertial(inert[name], f))
        link6.add(body)
        finger_info[name] = body
    equalities = [{"type": "joint", "joint1": "finger2_slide", "joint2": "finger1_slide",
                   "polycoef": (0, 1, 0, 0, 0)}]
    info = {"arm_joints": list(jc["names"]), "gripper_joint": "finger1_slide",
            "finger_joints": ["finger1_slide", "finger2_slide"], "tcp_site": "tcp",
            "flange_body": "link6", "finger_bodies": ["finger1", "finger2"],
            "finger_travel_range": (lo, travel[1]), "sleeve_thickness": float(t)}
    return base, equalities, info
