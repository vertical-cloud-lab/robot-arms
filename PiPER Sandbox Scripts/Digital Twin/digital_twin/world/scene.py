"""The engine-agnostic scene graph: what the world is made of, before any engine sees it.

World objects (world/objects.py, world/robot.py) build trees of `Body` with `Geom`
primitives in metres. An engine (engines/) walks the tree once and turns it into its own
model (an MJCF file for MuJoCo, plain poses for the kinematic engine, ...). So:

- adding a new object to the cell = a class that returns a Body; no engine code changes;
- adding a new engine = one class that understands Body / Geom / Joint; no world changes.

Collision groups (Geom.collide) say who touches whom, independent of the engine:
    env     static cell surfaces: table, printer, shelf, box   (touches print, arm, finger)
    print   the prints                                          (touches everything)
    arm     arm links                                           (touches env, print)
    finger  finger pads and sleeves                             (touches env, print)
    none    visual only
"""
from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np

COLLIDE_GROUPS = ("env", "print", "arm", "finger", "none")


@dataclass
class Geom:
    name: str
    type: str                     # box | cylinder | capsule | sphere | ellipsoid | mesh
    size: tuple = ()              # box: half extents; cylinder/capsule: (radius, half length);
                                  # sphere: (radius,); ellipsoid: half axes; mesh: ()
    pose: np.ndarray = field(default_factory=lambda: np.eye(4))  # in the body frame
    material: str = "pla"         # physics/materials.py key
    rgba: tuple = (0.7, 0.7, 0.7, 1.0)
    collide: str = "env"
    mesh_file: str | None = None  # STL path (visual or collision mesh)
    mesh_vertices: np.ndarray | None = None  # inline convex mesh (N x 3, m)
    texture: str | None = None    # e.g. "apriltag:tag36h11:31" for tag tiles
    density: float | None = None  # kg/m^3 for mass; None = the material's
    solref: tuple | None = None   # contact softness override

    def volume(self) -> float:
        s = self.size
        if self.type == "box":
            return 8 * s[0] * s[1] * s[2]
        if self.type == "cylinder":
            return np.pi * s[0] ** 2 * 2 * s[1]
        if self.type == "capsule":
            return np.pi * s[0] ** 2 * 2 * s[1] + 4 / 3 * np.pi * s[0] ** 3
        if self.type == "sphere":
            return 4 / 3 * np.pi * s[0] ** 3
        if self.type == "ellipsoid":
            return 4 / 3 * np.pi * s[0] * s[1] * s[2]
        if self.type == "mesh" and self.mesh_vertices is not None:
            from scipy.spatial import ConvexHull  # convex meshes only
            return float(ConvexHull(self.mesh_vertices).volume)
        return 0.0


@dataclass
class Joint:
    name: str
    type: str                     # hinge | slide | free
    axis: tuple = (0, 0, 1)
    range: tuple | None = None    # rad or m
    damping: float = 0.0
    frictionloss: float = 0.0
    armature: float = 0.0
    actuator: dict | None = None  # {"type": "motor", "limit": N or N*m}
                                  # {"type": "position", "kp": .., "kv": .., "limit": ..}


@dataclass
class Site:
    name: str
    pose: np.ndarray = field(default_factory=lambda: np.eye(4))
    size: float = 0.004
    rgba: tuple = (1, 0, 0, 0.6)


@dataclass
class Camera:
    name: str
    pose: np.ndarray              # camera frame: looks along its -z, image up is its +y
    fovy_deg: float
    resolution: tuple = (640, 480)


@dataclass
class Body:
    name: str
    pose: np.ndarray = field(default_factory=lambda: np.eye(4))  # in the parent frame
    geoms: list = field(default_factory=list)
    joints: list = field(default_factory=list)
    sites: list = field(default_factory=list)
    cameras: list = field(default_factory=list)
    children: list = field(default_factory=list)
    inertial: dict | None = None  # {"mass": kg, "com": (3,), "fullinertia": (6,)}; None = from geoms
    kind: str = "static"          # static | robot | print | mechanism
    meta: dict = field(default_factory=dict)

    def add(self, child: "Body") -> "Body":
        self.children.append(child)
        return child

    def walk(self, parent_pose: np.ndarray | None = None):
        """Yield (body, world pose at the model's zero state) depth first."""
        T = (np.eye(4) if parent_pose is None else parent_pose) @ self.pose
        yield self, T
        for c in self.children:
            yield from c.walk(T)

    def find(self, name: str) -> "Body | None":
        for b, _ in self.walk():
            if b.name == name:
                return b
        return None


@dataclass
class Bond:
    """A print stuck to the plate (physics/adhesion.py decides when it lets go)."""
    print_body: str
    plate_body: str
    capacity: object              # physics.adhesion.BondCapacity


@dataclass
class TagInfo:
    """Ground truth for one AprilTag: which body it is on and where (for perception)."""
    name: str
    id: int
    family: str
    size: float                   # m, black square edge
    body: str                     # body the tag is attached to
    pose: np.ndarray              # tag frame in that body (z out of the tag face)


@dataclass
class Scene:
    root: Body
    equalities: list = field(default_factory=list)  # {"type": "joint", "joint1", "joint2", "polycoef"}
    bonds: list = field(default_factory=list)
    tags: list = field(default_factory=list)
    info: dict = field(default_factory=dict)        # named handles for tasks (plate body, tcp ...)

    def body(self, name: str) -> Body:
        b = self.root.find(name)
        if b is None:
            raise KeyError(name)
        return b
