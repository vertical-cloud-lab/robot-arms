#!/usr/bin/env python3
"""Rebuild assets/piper/: the PiPER's link meshes and inertias, re-expressed in the DH frames.

You only need this if you want to regenerate the meshes (they are committed). It:

1. downloads AgileX's link meshes and inertias from MuJoCo Menagerie's `agilex_piper` model
   (MIT licence, derived from AgileX's own URDF) at a pinned commit;
2. finds, for every link, the fixed transform from the URDF's link frame to the DH frame the
   twin uses (piper_sdk's table). The URDF agrees with piper_sdk's dh_is_offset=0 table to
   0.02 mm, so the transform is computed against that table at q = 0; it is the same physical
   frame whichever DH variant you simulate (the variants only move the joints' zeros);
3. decimates each mesh (fewer triangles, same shape to well under a millimetre) and writes it
   in its DH frame, so engines attach it with no offset;
4. writes inertials.yaml: each link's mass, centre of mass and inertia in its DH frame.

    pip install trimesh fast-simplification mujoco numpy pyyaml
    python tools/build_piper_assets.py
"""
from __future__ import annotations

import os
import re
import sys
import tempfile
import urllib.request

import numpy as np
import yaml

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)

from digital_twin.kinematics.dh import DHChain, DHRow  # noqa: E402

COMMIT = "370c43965323c0944b433b202aac5058b5f907a9"  # mujoco_menagerie main, 2026-11-14
URL = f"https://raw.githubusercontent.com/google-deepmind/mujoco_menagerie/{COMMIT}/agilex_piper"
OUT = os.path.join(ROOT, "assets", "piper")
# Triangles to keep per link: enough to look right in the viewer, small enough for git.
FACES = {"base_link": 3000, "link1": 3000, "link2": 6000, "link3": 5000, "link4": 2500,
         "link5": 3000, "link6": 4000, "link7": 1500, "link8": 1500}
# piper_sdk dh_is_offset=0 (mm, deg): the table the URDF matches.
DH0 = [(0, 0, 0, 123), (0, -90, -174.22, 0), (285.03, 0, -100.78, 0),
       (-21.98, 90, 0, 250.75), (0, -90, 0, 0), (0, 90, 0, 91)]


def fetch(name: str, cache: str) -> str:
    path = os.path.join(cache, name.replace("/", "_"))
    if not os.path.exists(path):
        urllib.request.urlretrieve(f"{URL}/{name}", path)
    return path


def quat_to_mat(q):
    w, x, y, z = q
    return np.array([
        [1 - 2 * (y * y + z * z), 2 * (x * y - z * w), 2 * (x * z + y * w)],
        [2 * (x * y + z * w), 1 - 2 * (x * x + z * z), 2 * (y * z - x * w)],
        [2 * (x * z - y * w), 2 * (y * z + x * w), 1 - 2 * (x * x + y * y)],
    ])


def main():
    import mujoco
    import trimesh
    import fast_simplification

    cache = os.path.join(tempfile.gettempdir(), "piper_menagerie_cache")
    os.makedirs(cache, exist_ok=True)
    os.makedirs(OUT, exist_ok=True)
    xml = open(fetch("piper.xml", cache)).read()
    # Kinematics and inertias only: drop the meshes so the model loads without them.
    xml = re.sub(r'<mesh [^>]*/>', '', xml)
    xml = re.sub(r'<geom [^>]*mesh="[^"]*"[^>]*/>', '', xml)
    m = mujoco.MjModel.from_xml_string(xml)
    d = mujoco.MjData(m)
    mujoco.mj_kinematics(m, d)

    chain = DHChain([DHRow(a / 1000, np.radians(al), np.radians(th), dd / 1000)
                     for a, al, th, dd in DH0])
    F = [np.eye(4)] + chain.frames(np.zeros(6))  # DH frames 0..6 at q = 0

    def urdf_pose(body):
        T = np.eye(4)
        T[:3, :3] = d.xmat[m.body(body).id].reshape(3, 3)
        T[:3, 3] = d.xpos[m.body(body).id]
        return T

    # URDF body -> (twin body, DH frame index). The fingers (link7, link8) hang off frame 6.
    links = {"base_link": ("base", 0), "link1": ("link1", 1), "link2": ("link2", 2),
             "link3": ("link3", 3), "link4": ("link4", 4), "link5": ("link5", 5),
             "link6": ("link6", 6), "link7": ("finger1", 6), "link8": ("finger2", 6)}
    inertials = {}
    for urdf_body, (twin_body, k) in links.items():
        X = np.linalg.inv(F[k]) @ urdf_pose(urdf_body)  # DH frame k <- URDF link frame
        # Mesh: decimate, then move vertices into the DH frame.
        mesh = trimesh.load(fetch(f"assets/{urdf_body}.stl", cache), force="mesh")
        target = FACES[urdf_body]
        if len(mesh.faces) > target:
            v, f = fast_simplification.simplify(mesh.vertices, mesh.faces,
                                                target_reduction=1 - target / len(mesh.faces))
            mesh = trimesh.Trimesh(v, f, process=True)
        mesh.apply_transform(X)
        mesh.export(os.path.join(OUT, f"{twin_body}.stl"))
        # Inertial: MuJoCo already has it in the URDF link frame (body_ipos/iquat).
        bid = m.body(urdf_body).id
        p = X[:3, :3] @ m.body_ipos[bid] + X[:3, 3]
        R = X[:3, :3] @ quat_to_mat(m.body_iquat[bid])
        Ifull = R @ np.diag(m.body_inertia[bid]) @ R.T  # full inertia tensor in the DH frame
        inertials[twin_body] = {
            "mass_kg": round(float(m.body_mass[bid]), 6),
            "com_m": [round(float(v), 6) for v in p],
            # fullinertia order is MuJoCo's: Ixx Iyy Izz Ixy Ixz Iyz
            "fullinertia_kgm2": [float(f"{v:.6e}") for v in
                                 (Ifull[0, 0], Ifull[1, 1], Ifull[2, 2],
                                  Ifull[0, 1], Ifull[0, 2], Ifull[1, 2])],
        }
        print(f"{twin_body:13s} {len(mesh.faces):5d} faces  mass {m.body_mass[bid]:.4f} kg  "
              f"URDF->DH offset {np.round(X[:3, 3] * 1000, 2)} mm")
    with open(os.path.join(OUT, "inertials.yaml"), "w") as fh:
        fh.write("# Written by tools/build_piper_assets.py from MuJoCo Menagerie's agilex_piper\n"
                 f"# (commit {COMMIT}), which took them from AgileX's URDF. Expressed in the\n"
                 "# twin's DH frames. The URDF's masses add up to about 2.4 kg; AgileX lists the\n"
                 "# arm at 4.2 kg, so the dynamics (torques) are approximate even though the\n"
                 "# kinematics (positions) are exact to the DH table.\n")
        yaml.safe_dump(inertials, fh, sort_keys=False)
    with open(os.path.join(OUT, "LICENSE"), "w") as fh:
        fh.write(open(fetch("LICENSE", cache)).read())
    print("wrote", OUT)


if __name__ == "__main__":
    main()
