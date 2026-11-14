"""MuJoCo engine: THE physics engine of the twin (pip install mujoco).

What happens here:
1. build_mjcf() turns the engine-agnostic Scene into an MJCF XML file (written to
   output/_build/scene.xml so you can open it on its own: `python -m mujoco.viewer
   --mjcf=output/_build/scene.xml`). Collision groups become contype/conaffinity bits,
   materials become friction and contact softness, tags become textured tiles.
2. MujocoEngine steps it, applies the arm's joint torques and the gripper's force, and after
   every step checks each print's bond to the plate (physics/adhesion.py) and breaks it
   when the load gets too high: the "stick".

Why MuJoCo: its soft-contact solver handles grasping well (elliptic friction cones, no slip
creep with impratio > 1), it is fast enough for real-time and RL (MJX/MuJoCo Playground on a
GPU), it takes torque commands, so impedance and compliant control work the same as on the
real arm's MIT mode, and it is what LeRobot's simulated environments use.
"""
from __future__ import annotations

import os
import xml.etree.ElementTree as ET

import numpy as np

from ..physics import adhesion, materials
from ..transforms import mat_to_quat
from ..world.scene import Body, Geom, Scene
from .base import PhysicsEngine

# Collision groups -> (contype, conaffinity). Two geoms collide when
# (contype1 & conaffinity2) or (contype2 & conaffinity1) is non-zero.
#   env 1, print 2, arm 4, finger 8: env never touches env; the arm and fingers never touch
#   themselves or each other (the real arm's limits keep them apart), everything else does.
GROUP_BITS = {"env": (1, 2 | 4 | 8), "print": (2, 1 | 2 | 4 | 8), "arm": (4, 1 | 2),
              "finger": (8, 1 | 2), "none": (0, 0)}
# Which geoms show in the viewer by default (MuJoCo groups 0-2 are visible, 3+ hidden).
VIS_GROUP = {"env": 0, "print": 0, "arm": 3, "finger": 0, "none": 2}


def _f(v, fmt="{:.6g}"):
    return " ".join(fmt.format(float(x)) for x in np.ravel(v))


class _Builder:
    def __init__(self, scene: Scene, cfg, build_dir: str):
        self.scene, self.cfg, self.build_dir = scene, cfg, build_dir
        self.mj = cfg.sim["mujoco"]
        self.root = ET.Element("mujoco", model="piper_digital_twin")
        self.assets = None
        self.meshes: dict[str, str] = {}
        self.tag_materials: dict[str, str] = {}
        self.tag_meshes: dict[float, str] = {}
        self.actuators: list[ET.Element] = []

    def build(self) -> str:
        mj = self.mj
        ET.SubElement(self.root, "compiler", angle="radian", autolimits="true")
        ET.SubElement(self.root, "option", timestep=str(mj["timestep_s"]), integrator=mj["integrator"],
                      solver=mj["solver"], iterations=str(mj["iterations"]), cone=mj["cone"],
                      impratio=str(mj["impratio"]), gravity=_f(mj["gravity"]))
        ET.SubElement(self.root, "size", memory="256M")
        vis = ET.SubElement(self.root, "visual")
        ET.SubElement(vis, "global", offwidth=str(mj["offscreen_width"]), offheight=str(mj["offscreen_height"]),
                      azimuth="-120", elevation="-25")
        ET.SubElement(vis, "quality", shadowsize="4096", offsamples="4")
        ET.SubElement(vis, "headlight", diffuse="0.5 0.5 0.5", ambient="0.35 0.35 0.35", specular="0 0 0")
        ET.SubElement(vis, "map", znear="0.005")
        default = ET.SubElement(self.root, "default")
        ET.SubElement(default, "geom", solref=_f(mj["default_solref"]), solimp=_f(mj["default_solimp"]))
        self.assets = ET.SubElement(self.root, "asset")
        ET.SubElement(self.assets, "texture", name="skybox", type="skybox", builtin="gradient",
                      rgb1="0.85 0.85 0.82", rgb2="0.55 0.55 0.52", width="512", height="512")
        ET.SubElement(self.assets, "texture", name="floor_tex", type="2d", builtin="checker",
                      rgb1="0.45 0.45 0.45", rgb2="0.4 0.4 0.4", width="512", height="512")
        ET.SubElement(self.assets, "material", name="floor_mat", texture="floor_tex", texrepeat="8 8")
        world = ET.SubElement(self.root, "worldbody")
        ET.SubElement(world, "light", name="key", pos="0.6 -0.8 1.8", dir="-0.3 0.4 -1", directional="false",
                      diffuse="0.6 0.6 0.6", castshadow="true")
        ET.SubElement(world, "light", name="fill", pos="-0.8 0.2 1.6", dir="0.4 0 -1", diffuse="0.35 0.35 0.35",
                      castshadow="false")
        ET.SubElement(world, "geom", name="floor", type="plane", size="3 3 0.05", pos="0 0 -0.75",
                      material="floor_mat", contype="0", conaffinity="0")
        for cam in self.scene.info.get("world_cameras", []):
            self._camera(world, cam)
        for child in self.scene.root.children:
            self._body(world, child)
        self._equalities()
        if self.actuators:
            act = ET.SubElement(self.root, "actuator")
            for a in self.actuators:
                act.append(a)
        ET.indent(self.root)
        return ET.tostring(self.root, encoding="unicode")

    # --- pieces ----------------------------------------------------------------------------
    def _camera(self, parent, cam):
        R = cam.pose[:3, :3]
        ET.SubElement(parent, "camera", name=cam.name, pos=_f(cam.pose[:3, 3]),
                      xyaxes=_f(np.concatenate([R[:, 0], R[:, 1]])), fovy=f"{cam.fovy_deg:.3f}")

    def _body(self, parent_el, body: Body):
        el = ET.SubElement(parent_el, "body", name=body.name, pos=_f(body.pose[:3, 3]),
                           quat=_f(mat_to_quat(body.pose[:3, :3])))
        if body.inertial is not None:
            ET.SubElement(el, "inertial", pos=_f(body.inertial["com"]), mass=f"{body.inertial['mass']:.6g}",
                          fullinertia=_f(body.inertial["fullinertia"]))
        for j in body.joints:
            if j.type == "free":
                ET.SubElement(el, "freejoint", name=j.name)
                continue
            attrs = dict(name=j.name, type=j.type, axis=_f(j.axis), damping=f"{j.damping:g}",
                         frictionloss=f"{j.frictionloss:g}", armature=f"{j.armature:g}")
            if j.range is not None:
                attrs["range"] = _f(j.range)
            ET.SubElement(el, "joint", **attrs)
            if j.actuator:
                self._actuator(j)
        for g in body.geoms:
            self._geom(el, g, body)
        for s in body.sites:
            ET.SubElement(el, "site", name=s.name, pos=_f(s.pose[:3, 3]), quat=_f(mat_to_quat(s.pose[:3, :3])),
                          size=f"{s.size:g}", rgba=_f(s.rgba), group="4")
        for c in body.cameras:
            self._camera(el, c)
        for c in body.children:
            self._body(el, c)

    def _actuator(self, j):
        a = j.actuator
        lim = a.get("limit", 1e3)
        if a["type"] == "motor":
            self.actuators.append(ET.Element("motor", name=f"act_{j.name}", joint=j.name, ctrlrange=f"{-lim:g} {lim:g}"))
        elif a["type"] == "position":
            self.actuators.append(ET.Element("position", name=f"act_{j.name}", joint=j.name, kp=f"{a['kp']:g}",
                                             kv=f"{a.get('kv', 0):g}", forcerange=f"{-lim:g} {lim:g}"))

    def _mesh_asset(self, g: Geom) -> str:
        if g.mesh_file:
            key = os.path.abspath(g.mesh_file)
            if key not in self.meshes:
                name = f"mesh{len(self.meshes)}_{os.path.splitext(os.path.basename(key))[0]}"
                ET.SubElement(self.assets, "mesh", name=name, file=key)
                self.meshes[key] = name
            return self.meshes[key]
        name = f"mesh_inline_{len(self.meshes)}"
        ET.SubElement(self.assets, "mesh", name=name, vertex=_f(g.mesh_vertices))
        self.meshes[name] = name
        return name

    def _tag_assets(self, g: Geom) -> tuple[str, str]:
        """A textured tile mesh (one per size) and a material per tag."""
        _, family, tag_id = g.texture.split(":")
        half = round(g.size[0], 6)
        if half not in self.tag_meshes:
            name = f"tagtile_{len(self.tag_meshes)}"
            h, t = half, g.size[2]
            v = [(-h, -h, t), (h, -h, t), (h, h, t), (-h, h, t), (-h, -h, -t), (h, -h, -t), (h, h, -t), (-h, h, -t)]
            uv = [(0, 0), (1, 0), (1, 1), (0, 1), (0, 0), (1, 0), (1, 1), (0, 1)]
            faces = [(0, 1, 2), (0, 2, 3), (4, 6, 5), (4, 7, 6), (0, 4, 5), (0, 5, 1), (1, 5, 6), (1, 6, 2),
                     (2, 6, 7), (2, 7, 3), (3, 7, 4), (3, 4, 0)]
            ET.SubElement(self.assets, "mesh", name=name, vertex=_f(v), texcoord=_f(uv), face=_f(faces, "{:.0f}"))
            self.tag_meshes[half] = name
        mat = f"tagmat_{family}_{tag_id}"
        if mat not in self.tag_materials:
            from ..perception.apriltags import tag_png
            png = tag_png(family, int(tag_id), self.build_dir)
            if png is None:
                ET.SubElement(self.assets, "material", name=mat, rgba="0.9 0.9 0.9 1")
            else:
                ET.SubElement(self.assets, "texture", name=f"tex_{family}_{tag_id}", type="2d", file=png)
                ET.SubElement(self.assets, "material", name=mat, texture=f"tex_{family}_{tag_id}",
                              specular="0.1", shininess="0.1")
            self.tag_materials[mat] = mat
        return self.tag_meshes[half], mat

    def _geom(self, parent_el, g: Geom, body: Body):
        ct, ca = GROUP_BITS[g.collide]
        attrs = dict(name=g.name, pos=_f(g.pose[:3, 3]), quat=_f(mat_to_quat(g.pose[:3, :3])),
                     contype=str(ct), conaffinity=str(ca), group=str(VIS_GROUP[g.collide]))
        if g.texture and g.texture.startswith("apriltag:"):
            mesh, mat = self._tag_assets(g)
            attrs.update(type="mesh", mesh=mesh, material=mat, contype="0", conaffinity="0", group="1",
                         density="0")
            ET.SubElement(parent_el, "geom", **attrs)
            return
        m = materials.get(g.material)
        if g.type == "mesh":
            attrs.update(type="mesh", mesh=self._mesh_asset(g))
        else:
            attrs.update(type=g.type, size=_f(g.size))
        if g.collide != "none":
            attrs["friction"] = f"{m.friction:g} {m.torsional:g} {m.rolling:g}"
            sr = g.solref or m.solref
            if sr is not None:
                attrs["solref"] = _f(sr)
            if g.collide in ("print", "finger"):
                attrs["condim"] = "6"  # sliding + torsional + rolling friction for grasps
        attrs["rgba"] = _f(g.rgba)
        if body.inertial is not None or body.kind == "static":
            attrs["density"] = "0" if body.kind != "static" else attrs.get("density", "1000")
        elif g.collide == "none":
            attrs["density"] = "0"
        else:
            attrs["density"] = f"{(g.density if g.density is not None else m.density):g}"
        if g.collide == "none":
            attrs.pop("contype"); attrs.pop("conaffinity")
            attrs["contype"], attrs["conaffinity"] = "0", "0"
        ET.SubElement(parent_el, "geom", **attrs)

    def _equalities(self):
        if not self.scene.equalities and not self.scene.bonds:
            return
        eq = ET.SubElement(self.root, "equality")
        for e in self.scene.equalities:
            if e["type"] == "joint":
                ET.SubElement(eq, "joint", joint1=e["joint1"], joint2=e["joint2"], polycoef=_f(e["polycoef"]),
                              solref="0.002 1")
        for b in self.scene.bonds:
            ET.SubElement(eq, "weld", name=f"bond_{b.print_body}", body1=b.print_body, body2=b.plate_body,
                          solref=_f(self.mj["bond_solref"]))


def build_mjcf(scene: Scene, cfg, build_dir: str) -> str:
    os.makedirs(build_dir, exist_ok=True)
    return _Builder(scene, cfg, build_dir).build()


class MujocoEngine(PhysicsEngine):
    name = "mujoco"

    def __init__(self, scene: Scene, cfg, build_dir: str | None = None):
        super().__init__(scene, cfg)
        import mujoco
        self.mujoco = mujoco
        self.build_dir = build_dir or cfg.path("output/_build")
        xml = build_mjcf(scene, cfg, self.build_dir)
        self.xml_path = os.path.join(self.build_dir, "scene.xml")
        with open(self.xml_path, "w") as fh:
            fh.write(xml)
        self.m = mujoco.MjModel.from_xml_path(self.xml_path)
        self.d = mujoco.MjData(self.m)
        info = scene.info
        jid = [self.m.joint(n).id for n in info["arm_joints"]]
        self._qadr = np.array([self.m.jnt_qposadr[j] for j in jid])
        self._vadr = np.array([self.m.jnt_dofadr[j] for j in jid])
        self._act = np.array([self.m.actuator(f"act_{n}").id for n in info["arm_joints"]])
        gj = self.m.joint(info["gripper_joint"]).id
        self._g_qadr, self._g_vadr = self.m.jnt_qposadr[gj], self.m.jnt_dofadr[gj]
        self._g_act = self.m.actuator(f"act_{info['gripper_joint']}").id
        self._bed_act = self.m.actuator("act_bed_y").id if "act_bed_y" in [self.m.actuator(i).name
                                                                         for i in range(self.m.nu)] else None
        # Bonds: equality id, print body id, its free joint's dof address, capacity.
        self.bonds = {}
        for b in scene.bonds:
            eq = self.m.equality(f"bond_{b.print_body}").id
            body = self.m.body(b.print_body).id
            jnt = self.m.body_jntadr[body]
            self.bonds[b.print_body] = dict(eq=eq, body=body, dof=self.m.jnt_dofadr[jnt], cap=b.capacity,
                                            index=0.0, peak=0.0)
        self._efc_vec = None
        self._res = np.zeros(self.m.nv)
        self.renderers = {}
        self.reset()

    # --- time ----------------------------------------------------------------------------
    @property
    def time(self):
        return float(self.d.time)

    @property
    def dt(self):
        return float(self.m.opt.timestep)

    def reset(self):
        self.mujoco.mj_resetData(self.m, self.d)
        q0 = np.radians(self.cfg.robot["joints"]["home_deg"])
        self.d.qpos[self._qadr] = q0
        lo, _ = self.scene.info["finger_travel_range"]
        self.d.qpos[self._g_qadr] = lo + 0.02
        self.d.qpos[self.m.jnt_qposadr[self.m.joint("finger2_slide").id]] = lo + 0.02
        self.mujoco.mj_forward(self.m, self.d)

    def step(self, n: int = 1):
        mj = self.mujoco
        for _ in range(n):
            mj.mj_step(self.m, self.d)
            if self.bonds:
                self._update_bonds()

    # --- robot -----------------------------------------------------------------------------
    def arm_q(self):
        return self.d.qpos[self._qadr].copy()

    def arm_qd(self):
        return self.d.qvel[self._vadr].copy()

    def gripper_travel(self):
        return float(self.d.qpos[self._g_qadr])

    def gripper_speed(self):
        return float(self.d.qvel[self._g_vadr])

    def set_arm_torque(self, tau):
        self.d.ctrl[self._act] = tau

    def set_gripper_force(self, f):
        self.d.ctrl[self._g_act] = f

    def gravity_torque(self):
        return self.d.qfrc_bias[self._vadr].copy()

    def set_arm_q(self, q):
        self.d.qpos[self._qadr] = q
        self.d.qvel[self._vadr] = 0
        self.mujoco.mj_forward(self.m, self.d)

    # --- world -----------------------------------------------------------------------------
    def body_pose(self, name):
        b = self.m.body(name).id
        T = np.eye(4)
        T[:3, :3] = self.d.xmat[b].reshape(3, 3)
        T[:3, 3] = self.d.xpos[b]
        return T

    def site_pose(self, name):
        s = self.m.site(name).id
        T = np.eye(4)
        T[:3, :3] = self.d.site_xmat[s].reshape(3, 3)
        T[:3, 3] = self.d.site_xpos[s]
        return T

    # --- bonds -----------------------------------------------------------------------------
    def bonded(self, print_name):
        b = self.bonds.get(print_name)
        return bool(b and self.d.eq_active[b["eq"]])

    def bond_index(self, print_name):
        b = self.bonds.get(print_name)
        return b["index"] if b else 0.0

    def _update_bonds(self):
        """Load on each intact bond -> failure index -> break it at >= 1 (physics/adhesion.py)."""
        mj, m, d = self.mujoco, self.m, self.d
        eq_rows = np.where(d.efc_type == mj.mjtConstraint.mjCNSTR_EQUALITY)[0] if d.nefc else []
        for name, b in self.bonds.items():
            if not d.eq_active[b["eq"]]:
                continue
            rows = [r for r in eq_rows if d.efc_id[r] == b["eq"]]
            if not rows:
                continue
            vec = np.zeros(d.nefc)
            vec[rows] = d.efc_force[rows]
            mj.mj_mulJacTVec(m, d, self._res, vec)
            dof = b["dof"]
            f_world = self._res[dof:dof + 3]   # bond's force on the print (world frame)
            t_local = self._res[dof + 3:dof + 6]  # bond's torque on the print (print frame)
            R = d.xmat[b["body"]].reshape(3, 3)
            load_f = -(R.T @ f_world)  # what the gripper puts on the bond, print frame
            c = np.array([*b["cap"].centroid, 0.0])
            load_t = -t_local - np.cross(c, load_f)  # moved from the print origin to the centroid
            idx = adhesion.failure_index(b["cap"], load_f, np.abs(load_t))
            b["index"] = idx
            b["peak"] = max(b["peak"], idx)
            if idx >= 1.0:
                d.eq_active[b["eq"]] = 0
                self.bond_log.append(dict(print=name, time=self.time, force_n=load_f.round(3).tolist(),
                                          torque_nm=load_t.round(4).tolist(), index=round(idx, 3)))

    # --- collisions for planning ---------------------------------------------------------
    def arm_collisions(self, q, gripper_travel=None, ignore=()):
        """Contacts between robot geoms and anything else with the arm at q (state restored)."""
        mj, m, d = self.mujoco, self.m, self.d
        qpos, qvel = d.qpos.copy(), d.qvel.copy()
        d.qpos[self._qadr] = q
        if gripper_travel is not None:
            d.qpos[self._g_qadr] = gripper_travel
            d.qpos[m.jnt_qposadr[m.joint("finger2_slide").id]] = gripper_travel
        mj.mj_kinematics(m, d)
        mj.mj_collision(m, d)
        out = []
        robot_bodies = self._robot_body_ids()
        for i in range(d.ncon):
            c = d.contact[i]
            b1, b2 = m.geom_bodyid[c.geom1], m.geom_bodyid[c.geom2]
            if (b1 in robot_bodies) == (b2 in robot_bodies):
                continue
            if c.dist > -0.0005:  # touching within half a millimetre: not a collision
                continue
            g1, g2 = m.geom(c.geom1).name, m.geom(c.geom2).name
            if any(s in g1 or s in g2 for s in ignore):
                continue
            out.append((g1, g2) if b1 in robot_bodies else (g2, g1))
        d.qpos[:], d.qvel[:] = qpos, qvel
        mj.mj_forward(m, d)
        return out

    def _robot_body_ids(self):
        if not hasattr(self, "_rb"):
            names = {b.name for b, _ in self.scene.root.walk() if b.kind == "robot"}
            self._rb = {self.m.body(n).id for n in names}
        return self._rb

    # --- rendering -------------------------------------------------------------------------
    def render(self, camera="mpzy", width=1280, height=720):
        key = (width, height)
        if key not in self.renderers:
            self.renderers[key] = self.mujoco.Renderer(self.m, height, width)
        r = self.renderers[key]
        if isinstance(camera, str):
            r.update_scene(self.d, camera=camera)
        else:
            r.update_scene(self.d, camera=camera)
        return r.render()

    def free_camera(self, lookat, distance, azimuth, elevation):
        cam = self.mujoco.MjvCamera()
        cam.lookat[:] = lookat
        cam.distance, cam.azimuth, cam.elevation = distance, azimuth, elevation
        return cam

    def launch_viewer(self):
        import mujoco.viewer
        return mujoco.viewer.launch_passive(self.m, self.d)

    def close(self):
        for r in self.renderers.values():
            try:
                r.close()
            except Exception:
                pass
        self.renderers = {}
