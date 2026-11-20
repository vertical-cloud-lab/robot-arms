"""Black-and-white AprilTag cubes, each with a mount made for the spot it goes in the PiPER cell.

The geometry library behind make_cubes.py (which writes the print files) and check_cubes.py
(which renders them and checks that a detector reads every tag). Units: mm.

A cube is printed in two filaments: a WHITE body (the cube and its mount) and BLACK inlays,
the tag's black cells sunk `inlay` mm into the faces. The white body is the tag's quiet zone,
so no white border has to be added afterwards. Each face carries a different tag36h11 ID, so
a single face is enough to tell which cube and which face the camera is looking at, and two
or three faces seen together pin the cube's pose with no planar flip (check_cubes.py).

Frames
------
Cube frame: origin at the centre of the cube's bottom face, z up, the cube's FRONT is -y,
RIGHT +x, BACK +y, LEFT -x (as seen from the front). Each face has a tag frame:

    z_t  out of the face
    y_t  "up" in the tag image as printed (the side faces' tags stand upright: y_t = +z)
    x_t  "right" in the tag image (x_t = y_t x z_t)

and the tag reads like the official AprilTag image (AprilRobotics/apriltag-imgs) when you
look at the face from outside with y_t up. OpenCV's generator draws the same tags turned by
180 degrees; that only changes which corner a detector lists first (see CORNER_ORDER).

Part frame: a printed part holds one or more cubes plus its mount. Its frame is tied to the
destination (the table's edge, the PiPER's base frame, the shelf's corner, ...), which is
what makes the tag corners in cube_tags.yaml directly usable for pose estimation there.

Where things are
----------------
    tag_bits()            which cells are black, for one ID (official orientation)
    CubeSpec              one cube: tag size, IDs, which faces get a tag, cube edge
    cube_body() / inlays()  the white cube and its black cells, in the cube frame
    MOUNTS                one builder per destination type: table_edge, base_collar,
                          shelf_corner, adhesive. Add a new destination by writing a builder.
    build_part()          cube(s) + mount -> white and black solids + every tag's corners
    write_3mf()           Bambu Studio / OrcaSlicer project: one object, two parts,
                          white on filament 1 and black on filament 2
"""
from __future__ import annotations

import math
import uuid
import zipfile
from dataclasses import dataclass, field

import numpy as np

try:
    import manifold3d as m3d
except ImportError as e:  # pragma: no cover
    raise SystemExit("needs manifold3d: pip install -r requirements.txt") from e

# ID order on a cube: first_id + index. A face that isn't printed keeps its ID unused.
FACES = ("top", "front", "right", "back", "left")

# (x_t, y_t, z_t) of each face in the cube frame (see the module docstring).
FACE_AXES = {
    "top": ((1, 0, 0), (0, 1, 0), (0, 0, 1)),
    "front": ((1, 0, 0), (0, 0, 1), (0, -1, 0)),
    "right": ((0, 1, 0), (0, 0, 1), (1, 0, 0)),
    "back": ((-1, 0, 0), (0, 0, 1), (0, 1, 0)),
    "left": ((0, -1, 0), (0, 0, 1), (-1, 0, 0)),
    "bottom": ((1, 0, 0), (0, -1, 0), (0, 0, -1)),
}

# Corners are stored top-left, top-right, bottom-right, bottom-left of the tag as printed.
# Detectors list them in their own order; index the stored corners with these to match:
CORNER_ORDER = {
    "stored": [0, 1, 2, 3],
    "opencv_aruco": [2, 3, 0, 1],    # cv2.aruco (DICT_APRILTAG_36h11): checked by check_cubes.py
    "apriltag_lib": [3, 2, 1, 0],    # AprilRobotics apriltag / pupil-apriltags (lb, rb, rt, lt)
}

EPS = 0.01  # mm: overlaps that keep booleans clean (far below what a printer resolves)


def _uid(*key) -> uuid.UUID:
    """A UUID fixed by its key, so rebuilding the same parts writes byte-identical files."""
    return uuid.uuid5(uuid.NAMESPACE_URL, "robot-arms/tag-cubes/" + "/".join(map(str, key)))


# ------------------------------------------------------------------------------------------
# Tags
# ------------------------------------------------------------------------------------------
def tag_bits(tag_id: int, family: str = "tag36h11") -> np.ndarray:
    """Black cells of one tag's black square (8 x 8 for tag36h11), True = black, row 0 at the
    top of the tag as printed. Official AprilTag orientation (OpenCV's, turned 180 degrees)."""
    import cv2  # opencv-python >= 4.7

    names = {"tag36h11": "DICT_APRILTAG_36h11", "tag25h9": "DICT_APRILTAG_25h9",
             "tag16h5": "DICT_APRILTAG_16h5"}
    d = cv2.aruco.getPredefinedDictionary(getattr(cv2.aruco, names[family]))
    n = d.markerSize + 2  # data bits + the black border
    img = cv2.aruco.generateImageMarker(d, int(tag_id), n, borderBits=1)  # one pixel per cell
    return np.rot90(img < 128, 2).copy()


def tag_cells(family: str = "tag36h11") -> int:
    """Cells across the black square (tag36h11: 6 data + 2 border = 8)."""
    return {"tag36h11": 8, "tag25h9": 7, "tag16h5": 6}[family]


# ------------------------------------------------------------------------------------------
# One cube
# ------------------------------------------------------------------------------------------
@dataclass
class CubeSpec:
    name: str
    first_id: int
    tag: float                          # edge of the black square, mm
    faces: tuple = FACES                # faces that get a tag (the mount side never does)
    family: str = "tag36h11"
    margin: float = 0.8                 # white beyond the one-cell quiet zone (covers the chamfer)
    chamfer: float = 0.6                # on every edge
    inlay: float = 1.0                  # depth of the black cells
    border_cells: float = 1.0           # quiet zone in cells: the detector needs at least 1

    @property
    def cell(self) -> float:
        return self.tag / tag_cells(self.family)

    @property
    def edge(self) -> float:
        """Cube edge: black square + quiet zone + margin on both sides."""
        return self.tag + 2 * (self.border_cells * self.cell + self.margin)

    def tag_id(self, face: str) -> int:
        return self.first_id + FACES.index(face)


def face_frame(spec: CubeSpec, face: str) -> np.ndarray:
    """4x4 pose of a face's tag frame in the cube frame (origin at the face centre)."""
    L = spec.edge
    x, y, z = (np.array(a, float) for a in FACE_AXES[face])
    centre = np.array([0.0, 0.0, L / 2]) + z * L / 2
    T = np.eye(4)
    T[:3, 0], T[:3, 1], T[:3, 2], T[:3, 3] = x, y, z, centre
    return T


def tag_corners_local(spec: CubeSpec) -> np.ndarray:
    """The black square's corners in a tag frame: TL, TR, BR, BL (z = 0, on the face)."""
    h = spec.tag / 2
    return np.array([[-h, h, 0], [h, h, 0], [h, -h, 0], [-h, -h, 0]], float)


def chamfered_box(lo, hi, c: float) -> "m3d.Manifold":
    """Axis-aligned box from lo to hi with every edge chamfered by c (convex hull of 24 points)."""
    lo, hi = np.asarray(lo, float), np.asarray(hi, float)
    pts = []
    for sx in (0, 1):
        for sy in (0, 1):
            for sz in (0, 1):
                corner = np.where([sx, sy, sz], hi, lo)
                inward = np.where([sx, sy, sz], -c, c)
                for axis in range(3):  # pull the corner in along the two other axes
                    p = corner + inward
                    p[axis] = corner[axis]
                    pts.append(p)
    return m3d.Manifold.hull_points(np.array(pts))


def box(lo, hi) -> "m3d.Manifold":
    lo, hi = np.asarray(lo, float), np.asarray(hi, float)
    return m3d.Manifold.cube(tuple(hi - lo)).translate(tuple(lo))


def cube_body(spec: CubeSpec) -> "m3d.Manifold":
    L = spec.edge
    return chamfered_box((-L / 2, -L / 2, 0), (L / 2, L / 2, L), spec.chamfer)


def _apply(m: "m3d.Manifold", T: np.ndarray) -> "m3d.Manifold":
    return m.transform(np.asarray(T, float)[:3, :4])


def face_inlay(spec: CubeSpec, face: str) -> "m3d.Manifold":
    """The black cells of one face as a solid `inlay` deep, in the cube frame.

    Each row's run of black cells is one rectangle, grown by EPS so cells that only touch at
    a corner overlap instead of meeting along a zero-width line (that keeps both solids
    manifold); the union is extruded into the face."""
    bits = tag_bits(spec.tag_id(face), spec.family)
    n, c = bits.shape[0], spec.cell
    rects = []
    for r in range(n):
        col = 0
        while col < n:
            if not bits[r, col]:
                col += 1
                continue
            c0 = col
            while col < n and bits[r, col]:
                col += 1
            x0, x1 = (c0 - n / 2) * c - EPS, (col - n / 2) * c + EPS
            y0, y1 = (n / 2 - r - 1) * c - EPS, (n / 2 - r) * c + EPS
            rects.append(np.array([[x0, y0], [x1, y0], [x1, y1], [x0, y1]]))
    section = m3d.CrossSection(rects, m3d.FillRule.NonZero)
    # From `inlay` below the face to EPS above it (trimmed to the body later).
    solid = m3d.Manifold.extrude(section, spec.inlay + EPS).translate((0, 0, -spec.inlay))
    return _apply(solid, face_frame(spec, face))


def cube_inlays(spec: CubeSpec) -> "m3d.Manifold":
    parts = [face_inlay(spec, f) for f in spec.faces]
    return m3d.Manifold.batch_boolean(parts, m3d.OpType.Add) if parts else m3d.Manifold()


def yaw_pose(x: float, y: float, z: float, yaw_deg: float) -> np.ndarray:
    a = math.radians(yaw_deg)
    T = np.eye(4)
    T[:2, :2] = [[math.cos(a), -math.sin(a)], [math.sin(a), math.cos(a)]]
    T[:3, 3] = (x, y, z)
    return T


def rot_x(deg: float) -> np.ndarray:
    a = math.radians(deg)
    T = np.eye(4)
    T[1:3, 1:3] = [[math.cos(a), -math.sin(a)], [math.sin(a), math.cos(a)]]
    return T


# ------------------------------------------------------------------------------------------
# Mounts: one builder per kind of destination
# ------------------------------------------------------------------------------------------
@dataclass
class Placed:
    """A cube placed in a part: its spec and its pose in the part frame."""
    spec: CubeSpec
    T: np.ndarray


@dataclass
class MountResult:
    cubes: list                      # [Placed]
    add: list = field(default_factory=list)       # white solids added to the cubes
    cut: list = field(default_factory=list)       # solids removed from the white body
    print_T: np.ndarray = field(default_factory=lambda: np.eye(4))  # part frame -> print bed
    frame: str = ""                  # what the part frame is, in words
    notes: list = field(default_factory=list)


def countersunk_hole(x: float, y: float, z_top: float, depth: float, d: float, head_d: float):
    """Vertical hole through a plate whose top is at z_top, countersunk 90 degrees at the top."""
    shaft = m3d.Manifold.cylinder(depth + 2, d / 2, d / 2, 48).translate((x, y, z_top - depth - 1))
    cone_h = (head_d - d) / 2
    cone = m3d.Manifold.cylinder(cone_h + EPS, d / 2, head_d / 2 + EPS, 48).translate(
        (x, y, z_top - cone_h))
    top = m3d.Manifold.cylinder(1, head_d / 2 + EPS, head_d / 2 + EPS, 48).translate((x, y, z_top))
    return shaft + cone + top


def mount_table_edge(p: dict, spec: CubeSpec) -> MountResult:
    """A cube that sits on the table at its edge: a flange under it with two countersunk holes
    for wood screws into the plywood, and a lip that hangs down over the table's edge so the
    cube always lands at the same distance from it.

    Part frame: origin on the table's top edge, below the cube's centre; x along the edge,
    y off the table (outward), z up. The table is y < 0, z < 0."""
    L = spec.edge
    t = p.get("flange", 3.0)           # flange thickness (under the cube)
    lip_t = p.get("lip_thickness", 3.0)
    lip_d = p.get("lip_depth", 12.0)   # how far the lip reaches down the table's edge
    ext = p.get("flange_reach", 14.0)  # flange in front of the cube, for the screws
    d, head = p.get("screw_hole", 4.4), p.get("screw_head", 8.6)  # No. 8 / M4 wood screws
    back = lip_t                       # the cube's back face is flush with the lip's outside
    y0 = back - L                      # the cube's front face
    flange = box((-L / 2, y0 - ext, 0), (L / 2, back, t))
    lip = box((-L / 2, 0, -lip_d), (L / 2, back, t))
    holes = [countersunk_hole(x, y0 - ext / 2, t, t, d, head) for x in (-L / 4, L / 4)]
    cube_T = yaw_pose(0, back - L / 2, t, 0)
    # Printed lying on its back: lip and back face on the bed (+y -> -z), every face a wall.
    print_T = rot_x(-90)
    return MountResult([Placed(spec, cube_T)], [flange, lip], holes, print_T,
                       "table edge: origin on the table's top edge under the cube's centre, "
                       "x along the edge, y outward (off the table), z up",
                       [f"two {d:.1f} mm holes, countersunk {head:.1f} mm: No. 8 or M4 wood "
                        "screws into the plywood", f"lip reaches {lip_d:.0f} mm down the edge"])


def mount_base_collar(p: dict, specs: list) -> MountResult:
    """One collar around the PiPER's base carrying a cube in front, on the right and on the left.

    The collar's opening is the base's bottom flange (measured from AgileX's base mesh,
    Digital Twin/assets/piper/base.stl: x -55..40, y -40..40 mm) plus a clearance, open at
    the back for the cables. Pushed against the flange, it puts the three cubes at known
    offsets in the arm's base frame, which is the part frame: piper_sdk's base frame (x
    forward, y left, z up, origin where the J1 axis meets the table)."""
    fx, fy = p.get("flange_x", [-55.0, 40.0]), p.get("flange_y", [-40.0, 40.0])
    clr = p.get("clearance", 0.4)
    band_w, band_h = p.get("band_width", 6.0), p.get("band_height", 4.0)
    d, head = p.get("screw_hole", 4.4), p.get("screw_head", 8.6)
    xf, yl, yr = fx[1] + clr, fy[1] + clr, fy[0] - clr      # inner faces of the collar
    by_name = {c["name"]: c for c in p["cubes"]}
    placed, add, cut = [], [], []
    for spec in specs:
        side = by_name[spec.name]["side"]
        L = spec.edge
        # Each cube's local front (-y) faces outward; its back (toward the base) has no tag.
        # The cubes stand on plinths as tall as the band: the band then meets them below the
        # tags' white border instead of beside a black corner (it pulled OpenCV's corner 7 px
        # off when it ran past the side cubes' forward faces at the black square's level).
        z = band_h
        if side == "front":
            T = yaw_pose(xf + L / 2, 0, z, 90)
        elif side == "right":
            T = yaw_pose(0, yr - L / 2, z, 0)
        elif side == "left":
            T = yaw_pose(0, yl + L / 2, z, 180)
        else:
            raise ValueError(f"collar side must be front, right or left, not {side}")
        placed.append(Placed(spec, T))
        plinth = box((-L / 2, -L / 2, -z), (L / 2, L / 2, spec.chamfer))  # fills the bottom chamfer too
        add.append(_apply(plinth, T))
    Lmax = max(s.edge for s in specs)
    # The U band: in front of the flange and along both sides back to the side cubes.
    x_back = -Lmax / 2
    add.append(box((xf, yr - band_w, 0), (xf + band_w, yl + band_w, band_h)))
    add.append(box((x_back, yl, 0), (xf + band_w, yl + band_w, band_h)))
    add.append(box((x_back, yr - band_w, 0), (xf + band_w, yr, band_h)))
    # A screw pad in each front corner, between the front cube and a side cube.
    pad = p.get("pad", 16.0)
    for sgn, y_in in ((1, yl), (-1, yr)):
        lo = (xf, min(y_in, y_in + sgn * pad), 0)
        hi = (xf + pad, max(y_in, y_in + sgn * pad), band_h)
        add.append(box(lo, hi))
        cut.append(countersunk_hole(xf + pad / 2, y_in + sgn * pad / 2, band_h, band_h, d, head))
    return MountResult(placed, add, cut, np.eye(4),
                       "PiPER base frame (piper_sdk): origin where the J1 axis meets the table, "
                       "x forward, y left, z up",
                       [f"slides onto the base's bottom flange from the front ({clr} mm "
                        "clearance), open at the back", "two countersunk holes in the front "
                        "corners for wood screws, or stick it down with VHB tape"])


def mount_shelf_corner(p: dict, spec: CubeSpec) -> MountResult:
    """A cube that sits on a corner of the black perforated shelf like a cap: a notch in its
    bottom takes the shelf plate's corner, so two of its faces run down past the plate's
    edges and the cube lands on the corner the same way every time. No screws, no holes used.

    Part frame: origin at the plate's corner on its top surface; x and y run along the
    plate's two edges, into the plate; z up. The plate is x > 0, y > 0, z < 0."""
    L = spec.edge
    plate_t = p.get("plate_thickness", 5.0)
    clr = p.get("clearance", 0.3)
    lip = p.get("lip", 3.0)            # wall of the cube outside the plate's edges
    drop = plate_t + p.get("below", 2.0)  # how far the lips reach below the shelf's top
    cx = cy = L / 2 - lip              # cube centre: its outer faces `lip` outside the edges
    lips = chamfered_box((cx - L / 2, cy - L / 2, -drop), (cx + L / 2, cy + L / 2, spec.chamfer + 1),
                         spec.chamfer)
    notch = box((-clr, -clr, -drop - 1), (L + 1, L + 1, 0))  # where the plate's corner goes
    T = yaw_pose(cx, cy, 0, 0)
    # Printed upside down: the top tag face on the bed, the notch open at the top.
    print_T = rot_x(180)
    return MountResult([Placed(spec, T)], [lips], [notch], print_T,
                       "shelf corner: origin at the plate's corner on its top surface, x and y "
                       "along the plate's edges (into the plate), z up",
                       [f"notch for a {plate_t:.1f} mm plate (+{clr} mm): measure the shelf",
                        "corners S1-S4 use the same part turned 0/90/-90/180 degrees"])


def mount_adhesive(p: dict, spec: CubeSpec) -> MountResult:
    """A plain cube for a surface we have no CAD for (the A1 mini's housing): stick its
    mounting face down with VHB foam tape. `mount_face` is bottom or back.

    Part frame: the cube frame (origin at the centre of the bottom face)."""
    face = p.get("mount_face", "bottom")
    print_T = rot_x(-90) if face == "back" else np.eye(4)  # back face on the bed
    T = np.eye(4)
    return MountResult([Placed(spec, T)], [], [], print_T,
                       f"cube frame: origin at the centre of the bottom face, front -y, z up "
                       f"(taped by its {face} face)",
                       [f"VHB tape on the {face} face; pick a spot the bed, the toolhead and "
                        "the cables never reach, then let the camera measure where it is"])


MOUNTS = {
    "table_edge": mount_table_edge,
    "base_collar": mount_base_collar,
    "shelf_corner": mount_shelf_corner,
    "adhesive": mount_adhesive,
}


# ------------------------------------------------------------------------------------------
# A whole part
# ------------------------------------------------------------------------------------------
@dataclass
class Part:
    name: str
    mount: str
    white: "m3d.Manifold"
    black: "m3d.Manifold"
    tags: list                      # dicts: id, cube, face, size, centre, R, corners (part frame)
    print_T: np.ndarray
    frame: str
    notes: list
    cubes: list                     # [Placed]

    def solids_for_print(self):
        """White and black solids turned for the bed and set on it (min z = 0)."""
        w, b = _apply(self.white, self.print_T), _apply(self.black, self.print_T)
        zmin = w.bounding_box()[2]
        return w.translate((0, 0, -zmin)), b.translate((0, 0, -zmin))


def spec_from(cfg: dict, style: dict, family: str) -> CubeSpec:
    kw = {k: style[k] for k in ("margin", "chamfer", "inlay", "border_cells") if k in style}
    faces = tuple(f for f in FACES if f in cfg.get("faces", FACES))
    return CubeSpec(cfg["name"], int(cfg["first_id"]), float(cfg["tag"]), faces, family, **kw)


def build_part(pcfg: dict, style: dict, family: str = "tag36h11") -> Part:
    """cubes.yaml entry -> the white and black solids and every tag's corners."""
    kind = pcfg["mount"]
    builder = MOUNTS[kind]
    if kind == "base_collar":
        specs = [spec_from({**c, "tag": c.get("tag", pcfg.get("tag")),
                            "faces": c.get("faces", ["top", "front", "right", "left"])},
                           style, family) for c in pcfg["cubes"]]
        res = builder(pcfg, specs)
    else:
        spec = spec_from({"name": pcfg["name"], "first_id": pcfg["first_id"], "tag": pcfg["tag"],
                          "faces": pcfg.get("faces", FACES)}, style, family)
        res = builder(pcfg, spec)
    body = [_apply(cube_body(pl.spec), pl.T) for pl in res.cubes] + list(res.add)
    white = m3d.Manifold.batch_boolean(body, m3d.OpType.Add)
    if res.cut:
        white = white - m3d.Manifold.batch_boolean(res.cut, m3d.OpType.Add)
    inl = [_apply(cube_inlays(pl.spec), pl.T) for pl in res.cubes]
    black = m3d.Manifold.batch_boolean(inl, m3d.OpType.Add) ^ white  # ^ = intersection
    white = white - black
    tags = []
    for pl in res.cubes:
        for f in pl.spec.faces:
            T = pl.T @ face_frame(pl.spec, f)
            corners = tag_corners_local(pl.spec) @ T[:3, :3].T + T[:3, 3]
            tags.append({"id": pl.spec.tag_id(f), "cube": pl.spec.name, "face": f,
                         "size": pl.spec.tag, "center": T[:3, 3].copy(), "R": T[:3, :3].copy(),
                         "corners": corners})
    return Part(pcfg["name"], kind, white, black, tags, res.print_T, res.frame, res.notes, res.cubes)


# ------------------------------------------------------------------------------------------
# Export
# ------------------------------------------------------------------------------------------
def mesh_arrays(m: "m3d.Manifold"):
    mesh = m.to_mesh()
    return np.asarray(mesh.vert_properties)[:, :3].astype(float), np.asarray(mesh.tri_verts).astype(int)


def write_stl(path: str, m: "m3d.Manifold"):
    """Binary STL."""
    v, f = mesh_arrays(m)
    tri = v[f]
    n = np.cross(tri[:, 1] - tri[:, 0], tri[:, 2] - tri[:, 0])
    n /= np.maximum(np.linalg.norm(n, axis=1, keepdims=True), 1e-12)
    rec = np.zeros(len(f), dtype=[("n", "<f4", 3), ("v", "<f4", (3, 3)), ("a", "<u2")])
    rec["n"], rec["v"] = n, tri
    with open(path, "wb") as fh:
        fh.write(b"AprilTag cube (robot-arms, PiPER Sandbox Scripts/AprilTags/Tag Cubes)".ljust(80, b" "))
        fh.write(np.uint32(len(f)).tobytes())
        fh.write(rec.tobytes())


def _mesh_xml(oid: int, m: "m3d.Manifold", key: str = "") -> str:
    v, f = mesh_arrays(m)
    vs = "".join(f'<vertex x="{a:.4f}" y="{b:.4f}" z="{c:.4f}"/>' for a, b, c in v)
    ts = "".join(f'<triangle v1="{a}" v2="{b}" v3="{c}"/>' for a, b, c in f)
    return (f' <object id="{oid}" p:UUID="{_uid(key, oid)}" type="model">\n  <mesh>\n'
            f'   <vertices>{vs}</vertices>\n   <triangles>{ts}</triangles>\n  </mesh>\n </object>\n')


_NS = ('xmlns="http://schemas.microsoft.com/3dmanufacturing/core/2015/02" '
       'xmlns:BambuStudio="http://schemas.bambulab.com/package/2021" '
       'xmlns:p="http://schemas.microsoft.com/3dmanufacturing/production/2015/06" '
       'requiredextensions="p"')


def write_3mf(path: str, name: str, white: "m3d.Manifold", black: "m3d.Manifold",
              bed_center=(90.0, 90.0)):
    """One part (white body + black inlays) as a Bambu Studio / OrcaSlicer project."""
    write_3mf_plate(path, [(name, white, black, bed_center)])


def write_3mf_plate(path: str, items: list):
    """A 3MF for Bambu Studio / OrcaSlicer with one object per item, each made of two parts:
    the white body on filament 1 and the black inlays on filament 2.

    items: [(name, white, black, (x, y) on the bed)], solids already turned for printing and
    sitting on z = 0. Same layout Bambu Studio writes: the meshes in 3D/Objects/object_N.model
    (3MF production extension), the parts and their filaments in Metadata/model_settings.config.
    """
    n = len(items)
    ident = "1 0 0 0 1 0 0 0 1 0 0 0"
    ident4 = "1 0 0 0 0 1 0 0 0 0 1 0 0 0 0 1"
    files, comps, build, settings, plate, assemble = {}, [], [], [], [], []
    for k, (name, white, black, (bx, by)) in enumerate(items, start=1):
        lo = np.minimum(white.bounding_box()[:3], black.bounding_box()[:3])
        hi = np.maximum(white.bounding_box()[3:], black.bounding_box()[3:])
        off = (-(lo[0] + hi[0]) / 2, -(lo[1] + hi[1]) / 2, -lo[2])  # object origin: bottom centre
        w, b = white.translate(off), black.translate(off)
        sub_w, sub_b, oid = 2 * k - 1, 2 * k, 2 * n + k        # ids unique across the package
        f = f"3D/Objects/object_{k}.model"
        files[f] = (f'<?xml version="1.0" encoding="UTF-8"?>\n<model unit="millimeter" xml:lang="en-US" {_NS}>\n'
                    f' <metadata name="BambuStudio:3mfVersion">1</metadata>\n <resources>\n'
                    f'{_mesh_xml(sub_w, w, name)}{_mesh_xml(sub_b, b, name)} </resources>\n <build/>\n</model>\n')
        comps.append(f'  <object id="{oid}" p:UUID="{_uid(name, oid)}" type="model">\n   <components>\n'
                     f'    <component p:path="/{f}" objectid="{sub_w}" p:UUID="{_uid(name, oid, sub_w)}" transform="{ident}"/>\n'
                     f'    <component p:path="/{f}" objectid="{sub_b}" p:UUID="{_uid(name, oid, sub_b)}" transform="{ident}"/>\n'
                     f'   </components>\n  </object>\n')
        build.append(f'  <item objectid="{oid}" p:UUID="{_uid(name, oid, "item")}" '
                     f'transform="1 0 0 0 1 0 0 0 1 {bx:.3f} {by:.3f} 0" printable="1"/>\n')
        settings.append(
            f'  <object id="{oid}">\n    <metadata key="name" value="{name}"/>\n'
            f'    <metadata key="extruder" value="1"/>\n'
            f'    <part id="{sub_w}" subtype="normal_part">\n      <metadata key="name" value="{name} white"/>\n'
            f'      <metadata key="matrix" value="{ident4}"/>\n      <metadata key="extruder" value="1"/>\n'
            f'    </part>\n    <part id="{sub_b}" subtype="normal_part">\n'
            f'      <metadata key="name" value="{name} black"/>\n'
            f'      <metadata key="matrix" value="{ident4}"/>\n      <metadata key="extruder" value="2"/>\n'
            f'    </part>\n  </object>\n')
        plate.append(f'    <model_instance>\n      <metadata key="object_id" value="{oid}"/>\n'
                     f'      <metadata key="instance_id" value="0"/>\n    </model_instance>\n')
        assemble.append(f'   <assemble_item object_id="{oid}" instance_id="0" '
                        f'transform="1 0 0 0 1 0 0 0 1 {bx:.3f} {by:.3f} 0" offset="0 0 0"/>\n')
    # No "Application" metadata: a file that says it is Bambu Studio's must also carry its
    # project settings, and Bambu Studio 2.9's CLI crashes without them. Without it, Studio
    # loads the geometry with the parts and filaments below (checked: one object, two parts,
    # extruders 1 and 2, with BambuStudio 2.9.1.70's --export-3mf).
    root = (f'<?xml version="1.0" encoding="UTF-8"?>\n<model unit="millimeter" xml:lang="en-US" {_NS}>\n'
            f' <metadata name="BambuStudio:3mfVersion">1</metadata>\n'
            f' <metadata name="Title">AprilTag cubes</metadata>\n <resources>\n{"".join(comps)} </resources>\n'
            f' <build p:UUID="{_uid("build", *[it[0] for it in items])}">\n{"".join(build)} </build>\n</model>\n')
    config = (f'<?xml version="1.0" encoding="UTF-8"?>\n<config>\n{"".join(settings)}  <plate>\n'
              f'    <metadata key="plater_id" value="1"/>\n    <metadata key="plater_name" value=""/>\n'
              f'    <metadata key="locked" value="false"/>\n{"".join(plate)}  </plate>\n'
              f'  <assemble>\n{"".join(assemble)}  </assemble>\n</config>\n')
    ctypes = ('<?xml version="1.0" encoding="UTF-8"?>\n'
              '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">\n'
              ' <Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>\n'
              ' <Default Extension="model" ContentType="application/vnd.ms-package.3dmanufacturing-3dmodel+xml"/>\n'
              ' <Default Extension="config" ContentType="text/xml"/>\n</Types>\n')
    rel = ('<?xml version="1.0" encoding="UTF-8"?>\n'
           '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">\n{}'
           '</Relationships>\n')
    one = (' <Relationship Target="/{t}" Id="rel-{i}" '
           'Type="http://schemas.microsoft.com/3dmanufacturing/2013/01/3dmodel"/>\n')
    def put(z, name, data):  # fixed timestamp: same parts, same bytes
        z.writestr(zipfile.ZipInfo(name, date_time=(2026, 1, 1, 0, 0, 0)), data, zipfile.ZIP_DEFLATED)

    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as z:
        put(z, "[Content_Types].xml", ctypes)
        put(z, "_rels/.rels", rel.format(one.format(t="3D/3dmodel.model", i=1)))
        put(z, "3D/_rels/3dmodel.model.rels",
            rel.format("".join(one.format(t=f, i=i) for i, f in enumerate(files, start=1))))
        put(z, "3D/3dmodel.model", root)
        for f, body in files.items():
            put(z, f, body)
        put(z, "Metadata/model_settings.config", config)


def colour_layers(white: "m3d.Manifold", black: "m3d.Manifold", layer: float = 0.2) -> int:
    """Layers (at `layer` mm, print orientation) that hold both colours: each one costs a
    filament change in and out on a single-nozzle printer with an AMS."""
    z0, z1 = black.bounding_box()[2], black.bounding_box()[5]
    zs = np.arange(layer / 2, white.bounding_box()[5], layer)
    return int(sum(1 for z in zs if z0 <= z <= z1 and black.slice(float(z)).area() > 1e-3))
