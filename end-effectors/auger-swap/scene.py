"""Scene for the auger-swap studies: the powder doser (real lab STEP files), the new
parts from ``geometry.py``, and the PiPER arm (AgileX URDF meshes + kinematics).

The doser's files and its layout are fetched once from vertical-cloud-lab/powder-doser at a
pinned commit (``DOSER_SHA``, PR 170's full-assembly branch) into ``~/.cache/auger-swap``.
The PiPER URDF and meshes come from agilexrobotics/piper_ros at ``PIPER_SHA`` (MIT), the
same pin ``scripts/piper_twin.py`` uses on the issue-24 branches.
"""
from __future__ import annotations

import importlib.util
import math
import os
import sys
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path

import numpy as np
import trimesh

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import geometry as G  # noqa: E402

CACHE = Path(os.path.expanduser("~/.cache/auger-swap"))
DOSER_SHA = "7f5b3b7"   # powder-doser, branch claude/issue-165-20261001-1931
DOSER_RAW = "https://raw.githubusercontent.com/vertical-cloud-lab/powder-doser/{sha}/cad/full-assembly/{path}"
PIPER_SHA = "ac41fcbcdda598f01b51cf6175ed9a24d0dacadc"
PIPER_RAW = "https://raw.githubusercontent.com/agilexrobotics/piper_ros/{sha}/src/piper_description/{path}"

# doser parts kept from layout.placements() (the old bolted split clamps are replaced by the clip)
DOSER_STATIC = ["Baseplate", "Mounting plate", "Tap collar base (AI)", "Stepper pinion",
                "Stepper (NEMA 11)", "Servo pinion (+X)", "Servo pinion (-X)",
                "Servo MG996R (+X)", "Servo MG996R (-X)"]
DOSER_AUGER = ["Auger", "Auger cap"]
DOSER_COLLAR = ["Tap collar", "Solenoid (Adafruit 412)"]


def _fetch(url: str, dest: Path) -> Path:
    if not dest.exists():
        dest.parent.mkdir(parents=True, exist_ok=True)
        tmp = dest.with_suffix(dest.suffix + ".part")
        urllib.request.urlretrieve(url, tmp)
        tmp.rename(dest)
    return dest


def doser_layout():
    """powder-doser's layout.py (pinned), with its COMP pointing at the local cache."""
    root = CACHE / f"powder-doser-{DOSER_SHA}"
    path = _fetch(DOSER_RAW.format(sha=DOSER_SHA, path="onshape/layout.py"), root / "onshape" / "layout.py")
    spec = importlib.util.spec_from_file_location("doser_layout", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    mod.COMP = root / "components"
    return mod


def doser_step(rel: str) -> Path:
    root = CACHE / f"powder-doser-{DOSER_SHA}" / "components"
    return _fetch(DOSER_RAW.format(sha=DOSER_SHA, path=f"components/{rel}"), root / rel)


# ----------------------------------------------------------------------------- meshing
def tess(shape, tol: float = 0.15, ang: float = 0.3) -> trimesh.Trimesh:
    """CadQuery shape/Workplane -> trimesh (mm)."""
    import cadquery as cq
    if isinstance(shape, cq.Workplane):
        vals = shape.vals()
        shape = vals[0] if len(vals) == 1 else cq.Compound.makeCompound(vals)
    v, f = shape.tessellate(tol, ang)
    return trimesh.Trimesh(np.array([(p.x, p.y, p.z) for p in v]), np.array(f), process=False)


def cached_mesh(key: str, build, tol: float = 0.15) -> trimesh.Trimesh:
    p = CACHE / "mesh" / f"{key}.npz"
    if p.exists():
        d = np.load(p)
        return trimesh.Trimesh(d["v"], d["f"], process=False)
    m = tess(build(), tol)
    p.parent.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(p, v=m.vertices, f=m.faces)
    return m


def step_mesh(rel: str, tol: float = 0.25, max_faces: int = 60000) -> trimesh.Trimesh:
    """A doser STEP file as one mesh in its own frame (decimated if it is heavy)."""
    import cadquery as cq

    def build():
        shp = cq.importers.importStep(str(doser_step(rel)))
        return cq.Compound.makeCompound(shp.vals())
    key = "doser_" + rel.replace("/", "_").replace(".step", "")
    m = cached_mesh(key, build, tol)
    if len(m.faces) > max_faces:
        p = CACHE / "mesh" / f"{key}_dec{max_faces}.npz"
        if p.exists():
            d = np.load(p)
            return trimesh.Trimesh(d["v"], d["f"], process=False)
        m = m.simplify_quadric_decimation(face_count=max_faces)
        np.savez_compressed(p, v=m.vertices, f=m.faces)
    return m


def part_mesh(name: str) -> trimesh.Trimesh:
    return cached_mesh("part_" + name + "_" + _geom_hash(), G.ALL_PARTS[name], 0.1)


def _geom_hash() -> str:
    import hashlib
    return hashlib.sha1((HERE / "geometry.py").read_bytes()).hexdigest()[:8]


# ----------------------------------------------------------------------------- transforms
def T(t=(0, 0, 0), R=None) -> np.ndarray:
    M = np.eye(4)
    if R is not None:
        M[:3, :3] = R
    M[:3, 3] = t
    return M


def rot(axis, deg) -> np.ndarray:
    a = np.asarray(axis, float)
    a = a / np.linalg.norm(a)
    c, s = math.cos(math.radians(deg)), math.sin(math.radians(deg))
    K = np.array([[0, -a[2], a[1]], [a[2], 0, -a[0]], [-a[1], a[0], 0]])
    return np.eye(3) + s * K + (1 - c) * K @ K


def about(axis, deg, point) -> np.ndarray:
    """4x4 rotation about an axis through a point."""
    p = np.asarray(point, float)
    return T(p) @ T(R=rot(axis, deg)) @ T(-p)


# ----------------------------------------------------------------------------- PiPER
class Piper:
    """PiPER kinematics from the AgileX URDF (lengths in mm).  ``base`` places base_link
    in the world.  Joint limits are the URDF's."""

    LINKS = ["base_link", "link1", "link2", "link3", "link4", "link5", "link6",
             "gripper_base", "link7", "link8"]

    def __init__(self, base: np.ndarray):
        self.base = base
        urdf = _fetch(PIPER_RAW.format(sha=PIPER_SHA, path="urdf/piper_description.urdf"),
                      CACHE / "piper" / "piper_description.urdf")
        root = ET.parse(urdf).getroot()
        self.joints = {}
        for j in root.findall("joint"):
            o = j.find("origin")
            xyz = np.array([float(v) for v in o.get("xyz").split()]) * 1000.0
            rpy = [float(v) for v in o.get("rpy").split()]
            ax = j.find("axis")
            lim = j.find("limit")
            self.joints[j.find("child").get("link")] = dict(
                parent=j.find("parent").get("link"), type=j.get("type"), xyz=xyz, rpy=rpy,
                axis=np.array([float(v) for v in ax.get("xyz").split()]) if ax is not None else None,
                lim=(float(lim.get("lower")), float(lim.get("upper"))) if lim is not None else None)
        self.lower = np.array([self.joints[f"link{i}"]["lim"][0] for i in range(1, 7)])
        self.upper = np.array([self.joints[f"link{i}"]["lim"][1] for i in range(1, 7)])

    @staticmethod
    def _rpy(r, p, y):
        return rot((0, 0, 1), math.degrees(y)) @ rot((0, 1, 0), math.degrees(p)) @ rot((1, 0, 0), math.degrees(r))

    def poses(self, q, grip_mm: float = 0.0) -> dict:
        """World 4x4 of every link for joint angles q (rad, 6) and finger travel (mm each)."""
        out = {"base_link": self.base}
        for name in self.LINKS[1:]:
            j = self.joints[name]
            M = out[j["parent"]] @ T(j["xyz"], self._rpy(*j["rpy"]))
            if name.startswith("link") and name not in ("link7", "link8"):
                i = int(name[4:]) - 1
                M = M @ T(R=rot(j["axis"], math.degrees(q[i])))
            elif name in ("link7", "link8"):
                M = M @ T(j["axis"] * (grip_mm if name == "link7" else -grip_mm))
            out[name] = M
        return out

    def flange(self, q) -> np.ndarray:
        return self.poses(q)["link6"]

    def ik(self, target: np.ndarray, seed, w_rot: float = 150.0):
        from scipy.optimize import least_squares

        def res(q):
            M = self.flange(q)
            dp = M[:3, 3] - target[:3, 3]
            Rerr = target[:3, :3].T @ M[:3, :3]
            ang = np.arccos(np.clip((np.trace(Rerr) - 1) / 2, -1, 1))
            if ang < 1e-9:
                rv = np.zeros(3)
            else:
                rv = ang / (2 * math.sin(ang)) * np.array([Rerr[2, 1] - Rerr[1, 2], Rerr[0, 2] - Rerr[2, 0], Rerr[1, 0] - Rerr[0, 1]])
            return np.concatenate([dp, w_rot * rv])
        best = None
        seeds = [np.clip(np.asarray(seed, float), self.lower + 1e-3, self.upper - 1e-3)]
        for s in seeds:
            r = least_squares(res, s, bounds=(self.lower, self.upper), xtol=1e-10, ftol=1e-10, max_nfev=400)
            if best is None or r.cost < best.cost:
                best = r
        err = res(best.x)
        return best.x, float(np.linalg.norm(err[:3])), float(np.linalg.norm(err[3:]) / w_rot)

    def meshes(self, faces: int = 5000) -> dict:
        out = {}
        for name in self.LINKS:
            p = CACHE / "piper" / f"{name}_{faces}.npz"
            if not p.exists():
                stl = _fetch(PIPER_RAW.format(sha=PIPER_SHA, path=f"meshes/{name}.STL"),
                             CACHE / "piper" / f"{name}.STL")
                m = trimesh.load(stl, force="mesh")
                m.apply_scale(1000.0)
                if len(m.faces) > faces:
                    m = m.simplify_quadric_decimation(face_count=faces)
                np.savez_compressed(p, v=m.vertices, f=m.faces)
            d = np.load(p)
            out[name] = trimesh.Trimesh(d["v"], d["f"], process=False)
        return out


# tool frames: link6 z points down at the doser
R_TOOL_E = np.array([[1, 0, 0], [0, -1, 0], [0, 0, -1]], float)   # custom tool: link6 = E with y, z flipped
R_TOOL_G = np.array([[0, 1, 0], [1, 0, 0], [0, 0, -1]], float)    # stock gripper: fingers travel along W x


def flange_for_E(E: np.ndarray) -> np.ndarray:
    """link6 pose for a custom-tool frame E (E is world-aligned when the tool points down)."""
    return E @ T(R=R_TOOL_E)
