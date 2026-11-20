"""Classes for everything placed in the cell. Each one reads its block of cell_layout.yaml
(mm, degrees) and returns a scene Body (metres) that any engine can build.

    Table, RestStand, PrinterA1Mini, PerforatedShelf, Bin, Print, apriltag_geom

To add an object to the cell: subclass WorldObject, implement build() -> Body, and add it in
world/cell.py. Engines need no changes.
"""
from __future__ import annotations

import numpy as np

from ..config import deg, mm
from ..physics import adhesion, materials
from ..transforms import make_pose, normal_to_rot, pose_xyz_yaw
from .print_library import bounds, build_print_geoms
from .scene import Body, Geom, Joint, Site

TAG_THICKNESS = 0.0003  # m: printed sticker on a backing


def pose_from_cfg(p) -> np.ndarray:
    """[x, y, z, yaw] in mm/deg -> 4x4 pose in m."""
    x, y, z, yaw = p
    return pose_xyz_yaw(*mm([x, y, z]), float(deg(yaw)))


def _box(name, center_mm, size_mm, material, rgba, collide="env"):
    return Geom(name, "box", tuple(mm(size_mm) / 2), make_pose(None, mm(center_mm)),
                material, tuple(rgba), collide)


class WorldObject:
    """Base class: one block of cell_layout.yaml -> one Body tree."""

    name = "object"

    def __init__(self, cfg: dict):
        self.cfg = cfg

    def build(self) -> Body:
        raise NotImplementedError


class Table(WorldObject):
    name = "table"

    def build(self) -> Body:
        c = self.cfg
        W, D, t = c["size"]
        b = Body("table", kind="static")
        b.geoms.append(_box("table_top", (0, 0, -t / 2), (W, D, t), c["material"], c["color"]))
        leg = 50
        for i, (sx, sy) in enumerate([(-1, -1), (1, -1), (-1, 1), (1, 1)]):
            h = c["height"] - t
            b.geoms.append(_box(f"table_leg{i}", (sx * (W / 2 - leg), sy * (D / 2 - leg), -t - h / 2),
                                (leg, leg, h), c["material"], [0.5, 0.42, 0.3, 1], "none"))
        return b


class RestStand(WorldObject):
    """The wooden box behind the arm. Its position is given in the arm's base frame."""
    name = "rest_stand"

    def __init__(self, cfg: dict, arm_pose: np.ndarray):
        super().__init__(cfg)
        self.arm_pose = arm_pose

    def build(self) -> Body:
        c = self.cfg
        b = Body("rest_stand", pose=self.arm_pose.copy(), kind="static")
        b.geoms.append(_box("rest_stand", c["center"], c["size"], c["material"], c["color"]))
        return b


class PrinterA1Mini(WorldObject):
    """Bambu Lab A1 mini: base, Z column, cantilevered X arm with the toolhead parked, and a
    bed that slides along the printer's y (a slide joint the sim can drive). The PEI plate is
    its own body ("plate"), with its frame at the centre of its top surface: prints are
    bonded to it and the B tags ride on it."""
    name = "printer"

    def build(self) -> Body:
        c = self.cfg
        mat, col = c["material"], c["color"]
        b = Body("printer", pose=pose_from_cfg(c["pose"]), kind="static")
        b.geoms.append(_box("printer_base", c["base"]["center"], c["base"]["size"], mat, col))
        cx, cy = c["column"]["center"]
        sx, sy, sz = c["column"]["size"]
        b.geoms.append(_box("printer_column", (cx, cy, sz / 2), (sx, sy, sz), mat, [0.75, 0.76, 0.78, 1]))
        # Gantry: the X arm and toolhead sit at the parked nozzle height.
        nz = c["plate_top_z"] + c["nozzle_z_above_plate"]
        xa = c["x_arm"]
        th = c["toolhead"]["size"]
        arm_z = nz + xa.get("above_nozzle", 25) + xa["size_yz"][1] / 2  # X arm, above the nozzle
        b.geoms.append(_box("printer_x_arm", ((xa["from_x"] + xa["to_x"]) / 2, xa["y"], arm_z),
                            (xa["to_x"] - xa["from_x"], *xa["size_yz"]), mat, [0.7, 0.72, 0.75, 1]))
        b.geoms.append(_box("printer_toolhead", (c["toolhead_x"], xa["y"], nz + th[2] / 2), th, mat, col))
        # Bed: its body sits at the configured bed_y; the slide joint's zero is that position.
        lo, hi = c["bed_travel_y"]
        y0 = c["bed_y"]
        bed = b.add(Body("printer_bed", pose=make_pose(None, mm([0, y0, 0])), kind="mechanism",
                         joints=[Joint("bed_y", "slide", (0, 1, 0), tuple(mm([lo - y0, hi - y0])),
                                       damping=50.0, armature=0.5,
                                       actuator={"type": "position", "kp": 20000, "kv": 400, "limit": 200})]))
        pz = c["plate_top_z"]
        bx, by, bt = c["bed_size"]
        sheet_t = c["plate_size"][2]
        bed.geoms.append(_box("heated_bed", (0, 0, pz - sheet_t - bt / 2), (bx, by, bt), "black_aluminium",
                              [0.2, 0.2, 0.22, 1]))
        carriage_h = pz - sheet_t - bt - c["base"]["size"][2]
        if carriage_h > 0:
            bed.geoms.append(_box("bed_carriage", (0, 0, c["base"]["size"][2] + carriage_h / 2),
                                  (60, 120, carriage_h), mat, [0.6, 0.6, 0.62, 1], "none"))
        plate = bed.add(Body("plate", pose=make_pose(None, mm([0, 0, pz])), kind="mechanism"))
        px, py, _ = c["plate_size"]
        plate.geoms.append(_box("pei_sheet", (0, 0, -sheet_t / 2), (px, py, sheet_t), "pei_textured",
                                [0.13, 0.12, 0.12, 1]))
        plate.sites.append(Site("plate_origin", size=0.003, rgba=(0, 1, 0, 0.5)))
        return b


class PerforatedShelf(WorldObject):
    """The black shelf with a grid of round holes, on four feet. Holes are modelled as square
    openings with the holes' diameter as their side (the top is built from solid strips
    between them), so a small print set down over a hole can drop into it, as on the real one."""
    name = "shelf"

    def build(self) -> Body:
        c = self.cfg
        W, D, t = c["size"]
        top = c["top_z"]
        mat, col = c["material"], c["color"]
        b = Body("shelf", pose=pose_from_cfg(c["pose"]) @ make_pose(None, mm([0, 0, top])), kind="static")
        nx, ny = c["hole_grid"]
        px, py = c["hole_pitch"]
        r = c["hole_diameter"] / 2
        xs = (np.arange(nx) - (nx - 1) / 2) * px
        ys = (np.arange(ny) - (ny - 1) / 2) * py
        # Full-width bands between hole rows, then short segments between holes in each row.
        y_edges = [-D / 2] + [v for y in ys for v in (y - r, y + r)] + [D / 2]
        for i in range(0, len(y_edges), 2):
            y0, y1 = y_edges[i], y_edges[i + 1]
            b.geoms.append(_box(f"shelf_band{i // 2}", (0, (y0 + y1) / 2, -t / 2), (W, y1 - y0, t), mat, col))
        x_edges = [-W / 2] + [v for x in xs for v in (x - r, x + r)] + [W / 2]
        for j, y in enumerate(ys):
            for i in range(0, len(x_edges), 2):
                x0, x1 = x_edges[i], x_edges[i + 1]
                b.geoms.append(_box(f"shelf_seg{j}_{i // 2}", ((x0 + x1) / 2, y, -t / 2),
                                    (x1 - x0, 2 * r, t), mat, col))
        fd, inset = c["foot"]["diameter"], c["foot"]["inset"]
        h = top - t
        for k, (sx, sy) in enumerate([(-1, -1), (1, -1), (-1, 1), (1, 1)]):
            b.geoms.append(Geom(f"shelf_foot{k}", "cylinder", (mm(fd / 2), mm(h / 2)),
                                make_pose(None, mm([sx * (W / 2 - inset), sy * (D / 2 - inset), -t - h / 2])),
                                mat, tuple(col), "env"))
        b.meta.update(hole_centers=[(x, y) for x in xs for y in ys], hole_radius=r, size=(W, D))
        return b

    def spots(self, footprint_radius_mm: float) -> list[tuple[float, float]]:
        """Places (shelf frame, mm) where a print can stand: centred between four holes, so its
        footprint covers solid land. Returned nearest-first to the shelf's back-right corner."""
        c = self.cfg
        nx, ny = c["hole_grid"]
        px, py = c["hole_pitch"]
        W, D, _ = c["size"]
        xs = (np.arange(nx - 1) - (nx - 2) / 2) * px
        ys = (np.arange(ny - 1) - (ny - 2) / 2) * py
        out = [(x, y) for x in xs for y in ys
               if abs(x) + footprint_radius_mm < W / 2 and abs(y) + footprint_radius_mm < D / 2]
        return out


class Bin(WorldObject):
    """The open box prints are dropped into. Its frame is the centre of the inner floor."""
    name = "box"

    def build(self) -> Body:
        c = self.cfg
        X, Y, Z = c["outer_size"]
        w, f = c["wall"], c["floor"]
        mat, col = c["material"], c["color"]
        b = Body("box", pose=pose_from_cfg(c["pose"]) @ make_pose(None, mm([0, 0, f])), kind="static")
        b.geoms.append(_box("box_floor", (0, 0, -f / 2), (X, Y, f), mat, col))
        hz = Z - f
        b.geoms.append(_box("box_wall_back", (0, Y / 2 - w / 2, hz / 2), (X, w, hz), mat, col))
        b.geoms.append(_box("box_wall_front", (0, -Y / 2 + w / 2, hz / 2), (X, w, hz), mat, col))
        b.geoms.append(_box("box_wall_left", (-X / 2 + w / 2, 0, hz / 2), (w, Y - 2 * w, hz), mat, col))
        b.geoms.append(_box("box_wall_right", (X / 2 - w / 2, 0, hz / 2), (w, Y - 2 * w, hz), mat, col))
        b.meta.update(inner=(X - 2 * w, Y - 2 * w, hz), rim_z=hz)
        return b


class Print(WorldObject):
    """One print from prints.yaml: geometry from print_library, mass from material and fill,
    bond capacity from its footprint (physics/adhesion.py)."""

    def __init__(self, cfg: dict):
        super().__init__(cfg)
        self.name = cfg["name"]
        self.geoms = build_print_geoms(cfg["shape"], cfg.get("params", {}))
        mat = materials.get(cfg.get("material", "PLA"))
        fill = cfg.get("fill", 0.35)
        for g in self.geoms:
            g.name = f"{self.name}/{g.name}"
            g.material = cfg.get("material", "PLA")
            g.rgba = tuple(cfg.get("color", (0.8, 0.8, 0.8, 1)))
            g.collide = "print"
            g.density = mat.density * fill
        self.stick_kpa = cfg.get("stick_kpa", mat.stick_kpa)
        self.capacity = adhesion.capacity(self.geoms, self.stick_kpa)
        lo, hi = bounds(self.geoms)
        self.bounds_m = (lo, hi)
        self.height_m = float(hi[2])
        self.mass_kg = sum(g.volume() * g.density for g in self.geoms)

    def local_pose(self) -> np.ndarray:
        """Print frame in the plate frame."""
        x, y = self.cfg["plate_xy"]
        return pose_xyz_yaw(*mm([x, y, 0]), float(deg(self.cfg.get("yaw", 0))))

    def build(self, plate_world: np.ndarray | None = None) -> Body:
        pose = (np.eye(4) if plate_world is None else plate_world) @ self.local_pose()
        return Body(self.name, pose=pose, geoms=self.geoms,
                    joints=[Joint(f"{self.name}_free", "free")], kind="print",
                    meta={"mass": self.mass_kg, "destination": self.cfg.get("destination", "box")})

    def footprint_radius_mm(self) -> float:
        lo, hi = self.bounds_m
        return 1000 * float(np.max(np.abs(np.concatenate([lo[:2], hi[:2]]))))


def apriltag_geom(tag: dict, family: str) -> tuple[Geom, np.ndarray]:
    """A thin, visual-only tile for one tag (black square + one-cell white border), and its
    pose in the parent body. `pos` is a point on the surface; the tile sits on top of it."""
    s = mm(tag["size"])
    full = float(s) * 10 / 8
    R = normal_to_rot(tag.get("normal", "+z"))
    p = mm(tag["pos"]) + R[:, 2] * TAG_THICKNESS / 2
    pose = make_pose(R, p)
    g = Geom(f"tag_{tag['name']}", "box", (full / 2, full / 2, TAG_THICKNESS / 2), pose,
             "pla", (1, 1, 1, 1), "none", texture=f"apriltag:{family}:{tag['id']}", density=0.0)
    return g, pose
