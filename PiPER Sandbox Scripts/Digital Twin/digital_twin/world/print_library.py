"""Shapes of the 3D prints: simple solids and templates for compound models.

THIS is where a print's geometry is defined. prints.yaml picks a shape by name and passes its
`params` (mm); the functions here turn them into Geom primitives in metres, in the print's
frame (origin at the centre of its footprint, on the plate, z up).

Add a template: write a function `my_shape(p: dict) -> list[Geom]` and add it to TEMPLATES.
Every part should be a convex primitive (box, cylinder, capsule, sphere, ellipsoid, or an
inline convex mesh): physics engines collide convex shapes exactly and fast. Concave prints are
unions of convex parts, which is how the action figure and airplane below are built.
"""
from __future__ import annotations

import numpy as np

from ..transforms import euler_xyz, make_pose, rot_y
from .scene import Geom

MM = 1e-3


def _box(name, size_mm, pos_mm, euler_deg=(0, 0, 0)):
    """Box from its full size and centre (mm)."""
    return Geom(name, "box", tuple(np.asarray(size_mm) * MM / 2),
                make_pose(euler_xyz(*np.radians(euler_deg)), np.asarray(pos_mm) * MM))


def _cyl(name, radius_mm, height_mm, pos_mm, euler_deg=(0, 0, 0)):
    """Cylinder (axis along its local z) from radius, full height and centre (mm)."""
    return Geom(name, "cylinder", (radius_mm * MM, height_mm * MM / 2),
                make_pose(euler_xyz(*np.radians(euler_deg)), np.asarray(pos_mm) * MM))


def _capsule(name, radius_mm, p0_mm, p1_mm):
    """Capsule between two end points (the centres of its hemispherical caps), mm."""
    p0, p1 = np.asarray(p0_mm, float) * MM, np.asarray(p1_mm, float) * MM
    axis = p1 - p0
    L = np.linalg.norm(axis)
    z = axis / L
    x = np.cross([0, 1, 0], z) if abs(z[1]) < 0.9 else np.cross([1, 0, 0], z)
    x /= np.linalg.norm(x)
    R = np.column_stack([x, np.cross(z, x), z])
    return Geom(name, "capsule", (radius_mm * MM, L / 2), make_pose(R, (p0 + p1) / 2))


# --- simple solids -----------------------------------------------------------------------

def box(p):
    """params: size [x, y, z] mm."""
    sx, sy, sz = p["size"]
    return [_box("body", (sx, sy, sz), (0, 0, sz / 2))]


def cylinder(p):
    """params: diameter, height (mm). Upright."""
    return [_cyl("body", p["diameter"] / 2, p["height"], (0, 0, p["height"] / 2))]


def hex_prism(p):
    """params: across_flats, height (mm). A nut blank: an inline convex mesh."""
    R = p["across_flats"] / np.sqrt(3) * MM  # circumradius
    h = p["height"] * MM
    ang = np.radians(np.arange(6) * 60 + 30)
    ring = np.column_stack([R * np.cos(ang), R * np.sin(ang)])
    verts = np.vstack([np.column_stack([ring, np.zeros(6)]), np.column_stack([ring, np.full(6, h)])])
    return [Geom("body", "mesh", (), np.eye(4), mesh_vertices=verts)]


def compound(p):
    """params: parts: list of {type, size, pos, euler}. box size = full x y z; cylinder size =
    [radius, height]; capsule = {type: capsule, radius, p0, p1}; sphere size = [radius]."""
    out = []
    for i, part in enumerate(p["parts"]):
        t = part["type"]
        name = part.get("name", f"part{i}")
        if t == "box":
            out.append(_box(name, part["size"], part["pos"], part.get("euler", (0, 0, 0))))
        elif t == "cylinder":
            out.append(_cyl(name, part["size"][0], part["size"][1], part["pos"],
                            part.get("euler", (0, 0, 0))))
        elif t == "capsule":
            out.append(_capsule(name, part["radius"], part["p0"], part["p1"]))
        elif t == "sphere":
            out.append(Geom(name, "sphere", (part["size"][0] * MM,),
                            make_pose(None, np.asarray(part["pos"]) * MM)))
        else:
            raise ValueError(f"compound part type {t!r} not supported")
    return out


# --- compound templates ------------------------------------------------------------------

def action_figure(p):
    """A standing figure on a round base, built from 9 convex parts. params: height (mm,
    default 95; everything scales with it). Proportions: base disc 36 mm wide, legs to 42 %,
    torso 26 x 16 x 30, arms hanging at the sides, head an ellipsoid a little thinner (front
    to back) than the torso, so a grasp across the torso takes the torso and head together."""
    s = p.get("height", 95) / 95.0
    g = [
        _cyl("base", 18 * s, 4 * s, (0, 0, 2 * s)),
        _capsule("leg_l", 4.5 * s, (-6 * s, 0, 8.5 * s), (-6 * s, 0, 37.5 * s)),
        _capsule("leg_r", 4.5 * s, (6 * s, 0, 8.5 * s), (6 * s, 0, 37.5 * s)),
        _box("torso", (26 * s, 16 * s, 30 * s), (0, 0, 57 * s)),
        _capsule("arm_l", 4 * s, (-17.5 * s, 0, 48 * s), (-17.5 * s, 0, 66 * s)),
        _capsule("arm_r", 4 * s, (17.5 * s, 0, 48 * s), (17.5 * s, 0, 66 * s)),
        _cyl("neck", 4 * s, 4 * s, (0, 0, 74 * s)),
        Geom("head", "ellipsoid", (9.5 * s * MM, 7.5 * s * MM, 9.5 * s * MM),
             make_pose(None, (0, 0, 85.5 * s * MM))),
        _box("belt", (26.5 * s, 16.5 * s, 3 * s), (0, 0, 43.5 * s)),
    ]
    return g


def model_airplane(p):
    """A small airplane printed flat: wing and tailplane on the plate, fuselage lying on top of
    them, fin standing up. Nose toward +x. params: length (fuselage, mm), wingspan (mm)."""
    L, S = p.get("length", 110), p.get("wingspan", 130)
    rf = 0.075 * L  # fuselage radius
    chord, tail_chord = 0.26 * L, 0.16 * L
    return [
        # Fuselage: a capsule touching the plate along its underside.
        _capsule("fuselage", rf, (-L / 2 + rf, 0, rf), (L / 2 - rf, 0, rf)),
        _box("wing", (chord, S, 3.0), (0.08 * L, 0, 1.5)),
        _box("tailplane", (tail_chord, 0.45 * S, 2.5), (-0.42 * L, 0, 1.25)),
        _box("fin", (tail_chord, 2.5, 0.22 * L), (-0.43 * L, 0, 2 * rf - 2 + 0.11 * L)),
        # Propeller spinner and a two-blade prop standing at the nose.
        Geom("spinner", "sphere", (0.45 * rf * MM,), make_pose(None, (L / 2 * MM, 0, rf * MM))),
        _box("prop", (2.0, 4.0, 2 * rf + 6), (L / 2 + 1.5, 0, rf + 3)),
    ]


TEMPLATES = {"box": box, "cylinder": cylinder, "hex_prism": hex_prism, "compound": compound,
             "action_figure": action_figure, "model_airplane": model_airplane}


def build_print_geoms(shape: str, params: dict) -> list[Geom]:
    try:
        fn = TEMPLATES[shape]
    except KeyError:
        raise KeyError(f"unknown print shape {shape!r}; templates: {', '.join(TEMPLATES)}") from None
    return fn(params or {})


# --- geometry queries used by adhesion and planning ---------------------------------------

def inside(g: Geom, pts: np.ndarray) -> np.ndarray:
    """Boolean mask: which points (N x 3, print frame) are inside geom g."""
    T = g.pose
    local = (pts - T[:3, 3]) @ T[:3, :3]  # into the geom frame
    s = g.size
    if g.type == "box":
        return np.all(np.abs(local) <= np.asarray(s) + 1e-12, axis=1)
    if g.type == "cylinder":
        return (np.hypot(local[:, 0], local[:, 1]) <= s[0]) & (np.abs(local[:, 2]) <= s[1])
    if g.type == "capsule":
        z = np.clip(local[:, 2], -s[1], s[1])
        return np.linalg.norm(local - np.column_stack([0 * z, 0 * z, z]), axis=1) <= s[0]
    if g.type == "sphere":
        return np.linalg.norm(local, axis=1) <= s[0]
    if g.type == "ellipsoid":
        return np.sum((local / np.asarray(s)) ** 2, axis=1) <= 1.0
    if g.type == "mesh" and g.mesh_vertices is not None:
        from scipy.spatial import ConvexHull
        hull = ConvexHull(g.mesh_vertices)
        return np.all(local @ hull.equations[:, :3].T + hull.equations[:, 3] <= 1e-9, axis=1)
    return np.zeros(len(pts), bool)


def bounds(geoms: list[Geom], n: int = 24) -> tuple[np.ndarray, np.ndarray]:
    """Axis-aligned bounds (print frame) of a list of geoms, from sampled surface points."""
    pts = []
    for g in geoms:
        T, s = g.pose, g.size
        if g.type == "box":
            c = np.array([[x, y, z] for x in (-1, 1) for y in (-1, 1) for z in (-1, 1)]) * s
        elif g.type in ("cylinder", "capsule"):
            a = np.linspace(0, 2 * np.pi, n, endpoint=False)
            ring = np.column_stack([s[0] * np.cos(a), s[0] * np.sin(a)])
            ext = s[1] + (s[0] if g.type == "capsule" else 0)
            c = np.vstack([np.column_stack([ring, np.full(n, z)]) for z in (-ext, ext)])
        elif g.type in ("sphere", "ellipsoid"):
            r = np.asarray(s if g.type == "ellipsoid" else (s[0],) * 3)
            c = np.array([[x, y, z] for x in (-1, 1) for y in (-1, 1) for z in (-1, 1)]) * r
        elif g.type == "mesh" and g.mesh_vertices is not None:
            c = g.mesh_vertices
        else:
            continue
        pts.append(c @ T[:3, :3].T + T[:3, 3])
    pts = np.vstack(pts)
    return pts.min(0), pts.max(0)
