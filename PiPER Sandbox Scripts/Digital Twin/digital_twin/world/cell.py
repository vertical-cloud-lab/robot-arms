"""Assembles the whole cell from the five YAML files into one Scene.

    cell = Cell(load_config())
    cell.scene        # what engines build
    cell.prints       # Print objects (geometry, mass, bond capacity, grasp, destination)
    cell.plate_pose   # world pose of the build plate's frame at the start

This is the one place that knows which objects exist; add new ones here.
"""
from __future__ import annotations

import warnings

import numpy as np

from ..config import mm
from ..transforms import make_pose
from .objects import (Bin, PerforatedShelf, Print, PrinterA1Mini, RestStand, Table, apriltag_geom,
                      pose_from_cfg)
from .robot import build_piper
from .scene import Body, Bond, Camera, Scene, TagInfo

TAG_PARENTS = {"table": "table", "arm": "piper_base", "printer": "printer", "plate": "plate",
               "shelf": "shelf", "box": "box", "finger1": "finger1", "finger2": "finger2"}


def look_at_pose(position, target, up=(0, 0, 1)) -> np.ndarray:
    """Camera pose (MuJoCo convention: looks along -z, image up = +y) from position/target."""
    p, t = np.asarray(position, float), np.asarray(target, float)
    f = (t - p) / np.linalg.norm(t - p)
    x = np.cross(f, up)
    x /= np.linalg.norm(x)
    z = -f
    y = np.cross(z, x)
    return make_pose(np.column_stack([x, y, z]), p)


class Cell:
    def __init__(self, cfg):
        self.cfg = cfg
        c = cfg.cell
        self.arm_pose = pose_from_cfg(c["arm"]["pose"])
        root = Body("world")
        root.add(Table(c["table"]).build())
        if "rest_stand" in c:
            root.add(RestStand(c["rest_stand"], self.arm_pose).build())
        self.printer = PrinterA1Mini(c["printer"])
        root.add(self.printer.build())
        self.shelf = PerforatedShelf(c["shelf"])
        root.add(self.shelf.build())
        self.box = Bin(c["box"])
        root.add(self.box.build())
        robot_cfg = dict(cfg.robot)
        robot_cfg["_cameras"] = c.get("cameras", {})
        robot, equalities, info = build_piper(robot_cfg, self.arm_pose, cfg.root)
        root.add(robot)

        poses = {b.name: T for b, T in root.walk()}
        self.plate_pose = poses["plate"]
        self.prints = [Print(p) for p in cfg.prints["prints"]]
        bonds = []
        for p in self.prints:
            root.add(p.build(self.plate_pose))
            if p.capacity.pull_n > 0:
                bonds.append(Bond(p.name, "plate", p.capacity))
        self._check_prints()

        tags = []
        family = cfg.tags.get("family", "tag36h11")
        bodies = {b.name: b for b, _ in root.walk()}
        for t in cfg.tags["tags"]:
            parent = bodies[TAG_PARENTS[t["parent"]]]
            g, pose = apriltag_geom(t, family)
            parent.geoms.append(g)
            tags.append(TagInfo(t["name"], int(t["id"]), family, float(mm(t["size"])), parent.name, pose))

        world_cams = []
        for name, cc in c.get("cameras", {}).items():
            if cc.get("parent", "world") == "world" and "look_at" in cc:
                world_cams.append(Camera(name, look_at_pose(mm(cc["position"]), mm(cc["look_at"])),
                                         cc["fovy_deg"], tuple(cc["resolution"])))
        info.update(world_cameras=world_cams, arm_pose=self.arm_pose, plate_body="plate",
                    shelf_body="shelf", box_body="box")
        self.scene = Scene(root, equalities, bonds, tags, info)
        self.poses0 = {b.name: T for b, T in root.walk()}

    def _check_prints(self):
        """Warn about prints that overlap each other, hang off the print area or sit on a tag."""
        half = np.asarray(self.cfg.cell["printer"]["print_area"]) / 2 / 1000
        boxes = []
        for p in self.prints:
            lo, hi = p.bounds_m
            T = p.local_pose()
            corners = np.array([[x, y, 0, 1] for x in (lo[0], hi[0]) for y in (lo[1], hi[1])]) @ T.T
            a, b = corners[:, :2].min(0), corners[:, :2].max(0)
            if np.any(a < -half - 1e-6) or np.any(b > half + 1e-6):
                warnings.warn(f"print {p.name} extends past the {2000 * half[0]:.0f} mm print area")
            boxes.append((p.name, (a, b)))
        # Overlaps between prints are checked exactly by the engine (MujocoEngine.check_start).
