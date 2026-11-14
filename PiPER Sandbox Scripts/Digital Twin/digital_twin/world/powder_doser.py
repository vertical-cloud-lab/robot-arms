"""The powder doser from powder-doser PR 200, its augers, and a rack for the spares.

    PowderDoser   the doser standing on its legs: printed parts as meshes, collision boxes,
                  the two auger clips (snap fits), the tap collar and the drive pinion
    Auger         one auger: tube, drive gear and cap as collision shapes, the printed mesh,
                  and its mass from the plastic plus the powder inside (config/powder_doser.yaml)
    AugerRack     a printed rack on a riser, holding spare augers in the same clips
    clip_body_parts()  the clip's collision pieces, shared by the doser and the rack

Every clip is also returned as a `ClipSpec` (which body it's on, its seat frame), so
physics/snap_fit.py can push on the augers that pass through it.

Collision groups (world/scene.py) used here:
    env         cradles (the clip's rigid lower half), bases, the doser's parts
    print       the auger's tube: touches everything, but NOT the clip's arms (the snap model
                in physics/snap_fit.py stands in for the arms flexing around the tube)
    print_wide  the auger's gear and cap: like print, and they DO hit the clip's arms, so an
                auger set down with its gear over a clip jams, as it would
    clip_arm    the clip's arms above the tube's equator: only the gear, the cap and the
                gripper touch them
"""
from __future__ import annotations

import os
from dataclasses import dataclass

import numpy as np
import yaml

from ..config import deg, mm
from ..transforms import make_pose
from .objects import WorldObject, pose_from_cfg
from .scene import Body, Geom, Joint, Site

ASSETS = "assets/powder_doser"


def load_geometry(root: str) -> dict:
    with open(os.path.join(root, ASSETS, "geometry.yaml")) as fh:
        return yaml.safe_load(fh)


@dataclass
class ClipSpec:
    name: str
    body: str               # body the clip is fixed to (doser / rack)
    seat: np.ndarray        # seat frame in that body: origin at the seat centre, x across the
                            # mouth, y along the auger, z out of the mouth (up)


def _box(name, center_m, half_m, pose_parent, material, rgba, collide):
    return Geom(name, "box", tuple(half_m), pose_parent @ make_pose(None, center_m), material, tuple(rgba), collide)


def clip_body_parts(prefix: str, T_clip: np.ndarray, cg: dict, rgba, mesh_file: str | None,
                    closed_ring: bool = False) -> tuple[list[Geom], np.ndarray]:
    """Geoms of one clip placed at T_clip (the clip part's frame in the parent body) and the
    seat frame in the parent body. Geometry from geometry.yaml's `clip` block (mm).

    - visual: the printed clip's mesh
    - cradle (env): the ring's lower half, 95-265 deg from the top, as 12 flat pieces
    - arms (clip_arm): the ring from the equator up to the lips, and the flared tips
    - base (env): the screw flange and the block under the ring"""
    R = cg["seat_radius"] / 1000
    t = cg["wall_thickness"] / 1000
    w = cg["width"] / 1000
    cx, cz = (v / 1000 for v in cg["seat_center_xz"])
    y_mid = -w / 2  # the clip part spans y in [-width, 0]
    seat = T_clip @ make_pose(None, (cx, y_mid, cz))
    geoms = []
    if mesh_file:
        geoms.append(Geom(f"{prefix}_visual", "mesh", (), T_clip.copy(), "pla", tuple(rgba), "none",
                          mesh_file=mesh_file))

    def arc(name, a0, a1, n, collide, radius=R, thick=t):
        out = []
        for i in range(n):
            a = np.radians(a0 + (i + 0.5) * (a1 - a0) / n)
            span = np.radians(abs(a1 - a0) / n)
            rm = radius + thick / 2
            p = (np.sin(a) * rm, 0.0, np.cos(a) * rm)  # angle from the top, toward +x
            half = (thick / 2, w / 2, rm * np.tan(span / 2) * 1.08)
            Rl = np.array([[np.sin(a), 0, -np.cos(a)], [0, 1, 0], [np.cos(a), 0, np.sin(a)]])  # x radial
            out.append(Geom(f"{prefix}_{name}{i}", "box", half, seat @ make_pose(Rl, p), "pla", tuple(rgba), collide))
        return out

    if closed_ring:  # as drawn in the CAD (tap collar): a full rigid ring
        geoms += arc("ring", -180, 180, 24, "env")
    else:
        geoms += arc("cradle_r", 95, 180, 6, "env") + arc("cradle_l", -180, -95, 6, "env")
        lip_deg = np.degrees(np.arctan2(cg["lip_xz"][0], cg["lip_xz"][1] - cg["seat_center_xz"][1]))
        geoms += arc("arm_r", lip_deg, 92, 3, "clip_arm") + arc("arm_l", -92, -lip_deg, 3, "clip_arm")
        # Flared tips: from the lip up and out to the top of the clip.
        lx, lz = cg["lip_xz"][0] / 1000, (cg["lip_xz"][1] - cg["seat_center_xz"][1]) / 1000
        tz = (cg["tip_z"] - cg["seat_center_xz"][1]) / 1000
        tx = lx + 0.004
        for side in (1, -1):
            p0, p1 = np.array([side * lx, lz]), np.array([side * tx, tz])
            mid, L = (p0 + p1) / 2, np.linalg.norm(p1 - p0)
            ang = np.arctan2(p1[0] - p0[0], p1[1] - p0[1])
            Rl = np.array([[np.cos(ang), 0, np.sin(ang)], [0, 1, 0], [-np.sin(ang), 0, np.cos(ang)]])
            off = side * t / 2
            geoms.append(Geom(f"{prefix}_tip{'r' if side > 0 else 'l'}", "box", (t / 2, w / 2, L / 2),
                              seat @ make_pose(Rl, (mid[0] + off, 0.0, mid[1])), "pla", tuple(rgba), "clip_arm"))
    # Base: the screw flange (60 x 12 x 8) and the block (36 x 12 x 6) under the ring.
    geoms.append(_box(f"{prefix}_flange", (0, y_mid, 0.004), (0.030, w / 2, 0.004), T_clip, "pla", rgba, "env"))
    geoms.append(_box(f"{prefix}_block", (0, y_mid, 0.011), (0.018, w / 2, 0.003), T_clip, "pla", rgba, "env"))
    return geoms, seat


class PowderDoser(WorldObject):
    """The doser from powder-doser PR 200, standing on its three legs. Its frame is the doser
    frame of geometry.yaml; `pose` in config/powder_doser.yaml places it on the table."""
    name = "doser"

    def __init__(self, cfg: dict, geo: dict, root: str):
        super().__init__(cfg)
        self.geo, self.root = geo, root
        self.clips: list[ClipSpec] = []

    def mesh(self, name):
        f = os.path.join(self.root, ASSETS, f"{name}.stl")
        return f if os.path.exists(f) else None

    def build(self) -> Body:
        c, geo = self.cfg["doser"], self.geo
        black, wood, grey = c["color"], c["wood_color"], c["bought_color"]
        b = Body("doser", pose=pose_from_cfg(c["pose"]), kind="static")
        # Printed and wooden parts: meshes to look at, voxel boxes to collide with.
        for part in geo["parts"]:
            f = self.mesh(part)
            col = wood if part == "leg" else (0.55, 0.08, 0.08, 1) if part == "tap_collar" else black
            if f:
                b.geoms.append(Geom(f"doser_{part}_visual", "mesh", (), np.eye(4), "pla", tuple(col), "none",
                                    mesh_file=f))
            if part in ("stepper_pinion",):
                continue  # meshes with the auger's gear: checked geometrically, not collided
            for i, box in enumerate(geo["collision"].get(part, [])):
                b.geoms.append(Geom(f"doser_{part}_c{i}", "box", tuple(box["half"]), make_pose(None, box["center"]),
                                    "plywood" if part == "leg" else "pla", tuple(col), "env"))
        # Bought parts without STLs: boxes of their measured size at their placement (visual:
        # their exact offset from the part origin isn't known, so they don't collide).
        for name, p in geo["primitives"].items():
            if name == "auger_cap":
                continue  # the cap is part of each Auger
            ext = np.asarray(p["extent_mm"]) / 2000
            for i, T in enumerate(p["poses"]):
                b.geoms.append(Geom(f"doser_{name}{i}", "box", tuple(ext), np.asarray(T), "abs_plastic", tuple(grey),
                                    "none"))
        # The two clips (snap fits) at their CAD placements.
        clip_mesh = self.mesh("clip")
        for i, T in enumerate(geo["clip"]["poses_in_doser"]):
            gs, seat = clip_body_parts(f"doser_clip{i}", np.asarray(T), geo["clip"], black, clip_mesh)
            b.geoms += gs
            b.sites.append(Site(f"doser_clip{i}_seat", pose=seat, size=0.003, rgba=(1, 0.5, 0, 0.8)))
            self.clips.append(ClipSpec(f"doser_clip{i}", "doser", seat))
        # Tap collar: a cradle under the tube (open top) or the closed ring of the CAD.
        A = np.asarray(geo["auger"]["seated_pose_in_doser"])
        s0, s1 = 60.3, 77.3  # its span along the auger, mm (measured from the STLs)
        # Seat frame convention (x across, y along the auger, z up) on the auger's axis.
        T_col = self._seat_frame_on_axis(A, (s0 + s1) / 2000)
        cg = dict(geo["clip"], width=s1 - s0)
        T_part = T_col @ make_pose(None, (0, cg["width"] / 2000, -cg["seat_center_xz"][1] / 1000))
        gs, _ = clip_body_parts("doser_collar", T_part, cg, (0.55, 0.08, 0.08, 1), None,
                                closed_ring=not c.get("collar_open_top", True))
        b.geoms += [g for g in gs if "flange" not in g.name and "block" not in g.name and "arm" not in g.name
                    and "tip" not in g.name]
        # Where things are, for tasks and checks.
        b.sites.append(Site("doser_auger_seated", pose=A, size=0.004, rgba=(0, 1, 1, 0.6)))
        pin = geo["stepper_pinion"]
        b.sites.append(Site("doser_pinion", pose=make_pose(None, pin["center"]), size=0.004, rgba=(1, 0, 1, 0.6)))
        b.meta.update(auger_seated=A, pinion=pin, footprint=geo["bounds_m"])
        return b

    @staticmethod
    def _seat_frame_on_axis(A: np.ndarray, s: float) -> np.ndarray:
        """Seat-style frame (x across, y along the auger, z up) on the auger's axis at s (m)."""
        y = A[:3, 2]
        up = np.array([0, 0, 1.0]) - y * y[2]
        up /= np.linalg.norm(up)
        x = np.cross(y, up)
        return make_pose(np.column_stack([x, y, up]), A[:3, 3] + y * s)


class Auger(WorldObject):
    """One auger: a free body whose frame is the printed part's (origin at the centre of the
    outlet end, z along the tube toward the cap). Collision: the tube, the gear and the cap as
    cylinders. Mass: the plastic (from the STL's volume) + the cap + the powder inside."""

    def __init__(self, cfg: dict, dcfg: dict, geo: dict, root: str):
        super().__init__(cfg)
        self.name = cfg["name"]
        self.dcfg, self.geo, self.root = dcfg, geo, root
        a = geo["auger"]
        self.r = a["tube_radius"] / 1000
        self.length = a["length"] / 1000
        self.gear = a["gear"]
        self.thread_z0 = a["thread"]["z"][0] / 1000
        ac = dcfg["auger"]
        self.cap_r = ac["cap"]["diameter"] / 2000
        self.cap_len = ac["cap"]["length"] / 1000
        self.cap_z0 = self.length - self.cap_len + 0.002  # cap overhangs the tube's end by 2 mm
        powder = dcfg["powders"][cfg["powder"]]
        self.powder_g = cfg.get("fill", 0.0) * ac["bore_fill_volume_cm3"] * powder["bulk_density"]
        self.inertial, self.mass_kg = self._inertial(ac)

    def _inertial(self, ac):
        """Mass, centre of mass and inertia (auger frame). The printed part's from its mesh
        (trimesh), the cap and powder as cylinders; summed with the parallel-axis theorem."""
        from ..physics import materials
        rho = materials.get(ac.get("material", "PLA")).density * ac.get("fill", 1.0)
        parts = []  # (mass, com, inertia about com)
        f = os.path.join(self.root, ASSETS, "auger.stl")
        try:
            import trimesh
            m = trimesh.load(f)
            m.density = rho
            mp = m.mass_properties
            scale = self.geo["auger"]["volume_cm3"] * 1e-6 / max(m.volume, 1e-12)  # decimation drift
            parts.append((mp["mass"] * scale, np.asarray(mp["center_mass"]), np.asarray(mp["inertia"]) * scale))
        except Exception:  # no trimesh: a thick-walled tube of the STL's volume
            mass = self.geo["auger"]["volume_cm3"] * 1e-6 * rho
            parts.append((mass, np.array([0, 0, self.length / 2]),
                          np.diag([mass * (3 * self.r ** 2 + self.length ** 2) / 12] * 2 + [mass * self.r ** 2])))

        def cyl(mass, r, L, zc):
            Ixx = mass * (3 * r * r + L * L) / 12
            return (mass, np.array([0, 0, zc]), np.diag([Ixx, Ixx, mass * r * r / 2]))

        cap_m = ac["cap"]["volume_cm3"] * 1e-6 * rho
        parts.append(cyl(cap_m, self.cap_r, self.cap_len, self.cap_z0 + self.cap_len / 2))
        if self.powder_g > 0:
            bore = self.geo["auger"]["bore_radius"] / 1000
            z0, z1 = 0.003, self.thread_z0
            parts.append(cyl(self.powder_g / 1000, bore * 0.8, z1 - z0, (z0 + z1) / 2))
        M = sum(p[0] for p in parts)
        com = sum(p[0] * p[1] for p in parts) / M
        I = np.zeros((3, 3))
        for m_, c_, I_ in parts:
            d = c_ - com
            I += I_ + m_ * (np.dot(d, d) * np.eye(3) - np.outer(d, d))
        full = [I[0, 0], I[1, 1], I[2, 2], I[0, 1], I[0, 2], I[1, 2]]
        return {"mass": float(M), "com": com, "fullinertia": np.asarray(full)}, float(M)

    def build(self, T_world: np.ndarray) -> Body:
        rgba = tuple(self.cfg.get("color", (0.1, 0.1, 0.1, 1)))
        n = self.name
        g0, g1 = self.gear["z"][0] / 1000, self.gear["z"][1] / 1000
        tube_len = self.thread_z0
        geoms = [
            Geom(f"{n}/tube", "cylinder", (self.r, tube_len / 2), make_pose(None, (0, 0, tube_len / 2)), "PLA", rgba,
                 "print"),
            Geom(f"{n}/gear", "cylinder", (self.gear["tip_radius"] / 1000, (g1 - g0) / 2),
                 make_pose(None, (0, 0, (g0 + g1) / 2)), "PLA", rgba, "print_wide"),
            Geom(f"{n}/cap", "cylinder", (self.cap_r, self.cap_len / 2),
                 make_pose(None, (0, 0, self.cap_z0 + self.cap_len / 2)), "PLA", rgba, "print_wide"),
        ]
        f = os.path.join(self.root, ASSETS, "auger.stl")
        if os.path.exists(f):
            geoms.append(Geom(f"{n}/visual", "mesh", (), np.eye(4), "PLA", rgba, "none", mesh_file=f))
        s = self.dcfg["swap"]["grasp_at_mm"] / 1000
        sites = [Site(f"{n}/grasp", pose=make_pose(None, (0, 0, s)), size=0.003, rgba=(1, 1, 0, 0.8)),
                 Site(f"{n}/outlet", pose=np.eye(4), size=0.003, rgba=(0, 1, 0, 0.8)),
                 Site(f"{n}/gear", pose=make_pose(None, (0, 0, (g0 + g1) / 2)), size=0.003, rgba=(1, 0, 1, 0.8))]
        return Body(n, pose=T_world, geoms=geoms, sites=sites, joints=[Joint(f"{n}_free", "free")],
                    kind="auger", inertial=self.inertial,
                    meta={"mass": self.mass_kg, "powder_g": self.powder_g, "powder": self.cfg["powder"]})


class AugerRack(WorldObject):
    """A printed plate with `slots` pairs of the doser's clips, on a riser. Rack frame: origin
    at the centre of the plate's top, augers' outlets toward axis_yaw."""
    name = "rack"

    def __init__(self, cfg: dict, geo: dict, root: str):
        super().__init__(cfg)
        self.geo, self.root = geo, root
        self.clips: list[ClipSpec] = []
        self.slot_poses: list[np.ndarray] = []  # seated auger pose per slot, rack frame

    def build(self) -> Body:
        c = self.cfg["rack"]
        geo = self.geo
        X, Y, t = c["plate"]
        h = c["riser_height"]
        base = pose_from_cfg(c["pose"])
        b = Body("rack", pose=base @ make_pose(None, mm([0, 0, h])), kind="static")
        col = c["color"]
        b.geoms.append(Geom("rack_plate", "box", tuple(mm([X / 2, Y / 2, t / 2])), make_pose(None, mm([0, 0, -t / 2])),
                            "pla", tuple(col), "env"))
        rh = h - t
        if rh > 0:
            b.geoms.append(Geom("rack_riser", "box", tuple(mm([X / 2 - 20, Y / 2 - 30, rh / 2])),
                                make_pose(None, mm([0, 0, -t - rh / 2])), "plywood", tuple(c["riser_color"]), "env"))
        # Clip placement along the auger, copied from the doser: where each clip's seat sits
        # along the seated auger (s, from the outlet end).
        A = np.asarray(geo["auger"]["seated_pose_in_doser"])
        s_clips = []
        for T in geo["clip"]["poses_in_doser"]:
            seat = np.asarray(T) @ make_pose(None, (0, -geo["clip"]["width"] / 2000, geo["clip"]["seat_center_xz"][1] / 1000))
            s_clips.append(float((seat[:3, 3] - A[:3, 3]) @ A[:3, 2]))
        L = geo["auger"]["length"] / 1000
        yaw = float(deg(c.get("axis_yaw", 90)))
        out_dir = np.array([np.cos(yaw), np.sin(yaw), 0.0])  # toward the outlets
        across = np.array([-out_dir[1], out_dir[0], 0.0])
        z_seat = geo["clip"]["seat_center_xz"][1] / 1000
        clip_mesh = os.path.join(self.root, ASSETS, "clip.stl")
        for k in range(c["slots"]):
            off = (k - (c["slots"] - 1) / 2) * c["pitch"] / 1000
            centre = across * off
            # Seated auger: axis (outlet -> cap) along -out_dir, centred on the plate.
            z_ax = -out_dir
            x_ax = np.cross(np.array([0, 0, 1.0]), z_ax)
            y_ax = np.cross(z_ax, x_ax)
            outlet = centre + out_dir * (L / 2) + np.array([0, 0, z_seat])
            T_aug = make_pose(np.column_stack([x_ax, y_ax, z_ax]), outlet)
            self.slot_poses.append(T_aug)
            for j, s in enumerate(s_clips):
                p_seat = outlet + z_ax * s
                # Clip part frame: x across the mouth, y along the auger, z up; seat at
                # (0, -w/2, seat_z) in it.
                Rc = np.column_stack([np.cross(z_ax, [0, 0, 1.0]), z_ax, [0, 0, 1.0]])
                Rc[:, 0] /= np.linalg.norm(Rc[:, 0])
                T_clip = make_pose(Rc, p_seat - Rc @ np.array([0, -geo["clip"]["width"] / 2000, z_seat]))
                gs, seat = clip_body_parts(f"rack_s{k}_clip{j}", T_clip, geo["clip"], col, clip_mesh)
                if not c.get("snap", False):  # open cradles: the clip's arms are cut off
                    gs = [g for g in gs if "_arm_" not in g.name and "_tip" not in g.name and "_visual" not in g.name]
                    gs.append(Geom(f"rack_s{k}_clip{j}_visual", "mesh", (), T_clip.copy(), "pla", tuple(col), "none",
                                   mesh_file=os.path.join(self.root, ASSETS, "cradle.stl")))
                b.geoms += gs
                b.sites.append(Site(f"rack_s{k}_clip{j}_seat", pose=seat, size=0.003, rgba=(1, 0.5, 0, 0.8)))
                self.clips.append(ClipSpec(f"rack_s{k}_clip{j}", "rack", seat))
            b.sites.append(Site(f"rack_slot{k}", pose=T_aug, size=0.004, rgba=(0, 1, 1, 0.6)))
        b.meta.update(slot_poses=self.slot_poses, s_clips=s_clips)
        return b
