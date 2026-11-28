"""The PiPER cell set up for the auger swap: the standard cell (cell_layout.yaml) without the
prints and the drop box, plus the powder doser, the auger rack and the augers
(config/powder_doser.yaml), their AprilTags, and the clips' snap-fit force field.

    cell = DoserCell(load_config())
    cell.augers["auger_salt"]      # Auger objects (mass, powder, geometry)
    cell.snap                      # physics.snap_fit.SnapFitField, also in scene.info["force_fields"]
    cell.doser_seat_world          # where an auger sits in the doser (world pose)
    cell.slot_world(k)             # where an auger sits in rack slot k
"""
from __future__ import annotations

import os

import numpy as np
import yaml

from ..config import mm
from ..physics.snap_fit import ClipGeometry, SnapFitField
from .cell import Cell
from .objects import apriltag_geom
from .powder_doser import Auger, AugerRack, PowderDoser, load_geometry
from .scene import TagInfo

DROP = ("box",)  # cell objects this job doesn't use (their tags go with them)


def load_doser_config(root: str) -> dict:
    with open(os.path.join(root, "config", "powder_doser.yaml")) as fh:
        return yaml.safe_load(fh)


class DoserCell(Cell):
    def __init__(self, cfg, dcfg: dict | None = None, drop=DROP):
        cfg = cfg.copy()
        cfg.prints = {"prints": []}
        super().__init__(cfg)
        self.dcfg = dcfg = dcfg or load_doser_config(cfg.root)
        self.geo = geo = load_geometry(cfg.root)
        root = self.scene.root
        root.children = [c for c in root.children if c.name not in drop]
        self.scene.tags = [t for t in self.scene.tags if t.body not in drop]

        self.doser = PowderDoser(dcfg, geo, cfg.root)
        root.add(self.doser.build())
        self.rack = AugerRack(dcfg, geo, cfg.root)
        root.add(self.rack.build())
        poses = {b.name: T for b, T in root.walk()}
        self.doser_seat_world = poses["doser"] @ np.asarray(geo["auger"]["seated_pose_in_doser"])

        self.augers: dict[str, Auger] = {}
        for a in dcfg["augers"]:
            aug = Auger(a, dcfg, geo, cfg.root)
            start = a.get("start", "doser")
            T = self.doser_seat_world if start == "doser" else self.slot_world(int(start.split(":")[1]))
            root.add(aug.build(T.copy()))
            self.augers[aug.name] = aug
        self.occupant = {"doser": next((n for n, a in zip(self.augers, dcfg["augers"]) if a["start"] == "doser"), None)}
        for k in range(dcfg["rack"]["slots"]):
            self.occupant[f"rack:{k}"] = next((n for n, a in zip(self.augers, dcfg["augers"])
                                               if a["start"] == f"rack:{k}"), None)
        self._add_tags(dcfg, root)

        # The snap fits: every clip (doser and rack) acts on every auger's plain tube.
        cg, ag = geo["clip"], geo["auger"]
        cc = dcfg["clip"]
        geom = ClipGeometry(seat_radius=cg["seat_radius"], wall=cg["wall_thickness"], width=cg["width"],
                            lip_x=cg["lip_xz"][0], lip_z=cg["lip_xz"][1] - cg["seat_center_xz"][1],
                            root_deg=cc["root_deg"], E_mpa=cc["E_mpa"], yield_mpa=cc["yield_mpa"], mu=cc["mu"])
        spans = [(0.0, ag["gear"]["z"][0] - 0.5), (ag["gear"]["z"][1] + 0.5, ag["thread"]["z"][0])]
        self.clip_geom = geom
        snap_clips = self.doser.clips + (self.rack.clips if dcfg["rack"].get("snap", False) else [])
        self.snap = SnapFitField(snap_clips, self.augers, geom, ag["tube_radius"], spans, cg["width"] / 2)
        self.scene.info["force_fields"] = [self.snap]
        self.scene.info.update(doser_body="doser", rack_body="rack", augers=list(self.augers))
        # Named views for videos (run_sim.py --camera doser / swap): free cameras, world frame.
        d_xy = self.doser_seat_world[:3, 3]
        r_xy = self.slot_world(1)[:3, 3]
        mid = (d_xy + r_xy) / 2
        self.scene.info["free_cameras"] = {
            "swap": dict(lookat=[mid[0], mid[1], 0.16], distance=1.0, azimuth=150, elevation=-34),
            "doser": dict(lookat=list(d_xy), distance=0.55, azimuth=35, elevation=-30),
        }
        self.poses0 = {b.name: T for b, T in root.walk()}

    def add_view(self, name: str, position, look_at, fovy_deg: float = 45.0, resolution=(1600, 1000)):
        """A fixed world camera (before the engine is built), e.g. for the tag-placement graphic."""
        from .cell import look_at_pose
        from .scene import Camera
        cam = Camera(name, look_at_pose(np.asarray(position, float), np.asarray(look_at, float)), fovy_deg,
                     tuple(resolution))
        self.scene.info["world_cameras"].append(cam)
        return cam

    def slot_world(self, k: int) -> np.ndarray:
        return self.rack_pose() @ self.rack.slot_poses[k]

    def rack_pose(self) -> np.ndarray:
        return {b.name: T for b, T in self.scene.root.walk()}["rack"]

    def _add_tags(self, dcfg, root):
        family = self.cfg.tags.get("family", "tag36h11")
        bodies = {b.name: b for b, _ in root.walk()}
        for t in dcfg.get("apriltags", []):
            if t["parent"] == "auger":  # one per auger, on the cap's end face
                for n, aug in self.augers.items():
                    tt = dict(t, name=f"U_{n}", id=aug.cfg["tag_id"], size=dcfg["auger"]["tag"]["size"],
                              pos=[0, 0, (aug.cap_z0 + aug.cap_len) * 1000])
                    self._tag(bodies[n], tt, family)
                continue
            if t["parent"].startswith("rack_slot"):
                k = int(t["parent"][len("rack_slot"):])
                if k >= len(self.rack.slot_poses):
                    continue
                # Under the slot's auger, between the gear and the back clip, on the plate.
                T_s = self.rack.slot_poses[k]
                s = self.dcfg["swap"]["grasp_at_mm"] / 1000
                p = T_s[:3, 3] + T_s[:3, 2] * s
                tt = dict(t, pos=[p[0] * 1000, p[1] * 1000, 0.0])
                self._tag(bodies["rack"], tt, family)
                continue
            self._tag(bodies[t["parent"]], t, family)

    def _tag(self, body, t, family):
        g, pose = apriltag_geom(t, family)
        body.geoms.append(g)
        self.scene.tags.append(TagInfo(t["name"], int(t["id"]), family, float(mm(t["size"])), body.name, pose))
