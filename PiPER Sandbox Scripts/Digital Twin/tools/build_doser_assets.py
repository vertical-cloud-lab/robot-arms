#!/usr/bin/env python3
"""Rebuild assets/powder_doser/: the powder doser from powder-doser PR 200, ready for the twin.

You only need this to regenerate the doser's meshes (they are committed). It:

1. downloads the doser's STLs and the assembly's part placements (`parts.json`) from
   vertical-cloud-lab/powder-doser (MIT licence) at a pinned commit of PR 200's branch
   (`cad/onshape-193/`, exported from the lab's Onshape documents on 2026-11-13);
2. turns the assembly the right way up. Onshape's assembly is drawn upside down: its three
   250 mm wooden legs point up and the auger hangs under the baseplate. On the bench the doser
   stands on its legs, so the DOSER FRAME used everywhere in the twin is the Onshape assembly
   frame rotated 180 deg about x (x stays, y and z flip), raised so the legs stand on z = 0.
   The auger then lies on top in two C-clips that open upward, sloping 1.7 deg down toward its
   outlet, which sits over the baseplate's cut-out (where the powder falls into a cup);
3. writes each fixed part as a decimated STL in the doser frame (visual meshes), the auger and
   the clip in their own part frames (they are reused: every auger and every rack clip is a
   copy), the rack's open cradle (the clip without its arms), and the tap collar with the top
   of its ring cut away (as drawn it is a closed ring that would trap the auger);
4. measures what the simulation needs straight from the meshes and writes it to
   geometry.yaml: the auger's profile (tube, bore, gear, thread), the clip's seat and lips
   (the snap fit), where every clip, the collar and the pinion sit, and the doser's footprint;
5. writes collision boxes for the fixed parts: each part voxelised at 4 mm and the voxels
   merged into as few boxes as possible (MuJoCo collides meshes as their convex hulls, which
   would fill the baseplate's U-shaped cut-out and the mounting plate's gaps).

    pip install trimesh fast-simplification numpy scipy pyyaml
    python tools/build_doser_assets.py            # downloads into a temporary folder
    python tools/build_doser_assets.py --src DIR  # or use STLs you already have
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
import tempfile
import urllib.request

import numpy as np
import yaml

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
OUT = os.path.join(ROOT, "assets", "powder_doser")

REPO = "vertical-cloud-lab/powder-doser"
COMMIT = "4a66a72134a88e82230ae22a8fc0ef7b0b36c5d5"  # PR 200's head, claude/issue-197-20261103-0056
BASE_URL = f"https://raw.githubusercontent.com/{REPO}/{COMMIT}/cad/onshape-193"

# parts.json label -> (output name, kind, faces to keep). kind: fixed (part of the doser body,
# written in the doser frame), auger / clip (written in their own frame), skip.
PARTS = {  # the auger first: the collar is cut relative to the auger's axis
    "Auger": ("auger", "auger", 9000),
    "Baseplate": ("baseplate", "fixed", 4000),
    "Mounting plate": ("mounting_plate", "fixed", 5000),
    "Stand bracket (back)": ("stand_back", "fixed", 1500),
    "Stand bracket (left side)": ("stand_left", "fixed", 1500),
    "Stand bracket (right side)": ("stand_right", "fixed", 1500),
    "Wood leg": ("leg", "fixed", 800),
    "Servo pinion (Complete Servo Pinion)": ("servo_pinion", "fixed", 1200),
    "Stepper pinion (Stepper Pinion)": ("stepper_pinion", "fixed", 1500),
    "Tap collar (tapcollar)": ("tap_collar", "collar", 1500),
    "Auger clip (Bracket Recreation)": ("clip", "clip", 1500),
}
# Bought parts whose STLs aren't in the repo: drawn as boxes/cylinders of their measured size
# (parts.json `extent_mm`) at their assembly placement. label -> output name
PRIMITIVES = {"stepper_motor": "stepper_motor", "MG-996R servo": "servo",
              "solenoid_coil": "solenoid_coil", "solenoid_yoke": "solenoid_yoke",
              "tap_collar_base": "tap_collar_base", "auger_cap": "auger_cap"}

FLIP = np.diag([1.0, -1.0, -1.0])     # Onshape assembly -> right way up (180 deg about x)
VOXEL = 0.004                         # m, collision voxel pitch
VOXEL_NEAR_AUGER = 0.002              # finer for the parts the auger sits on and next to
NEAR_AUGER = ("mounting_plate", "baseplate")
COLLAR_CUT_DEG = 70                   # half-angle of the collar's ring removed at the top


def fetch(rel: str, src: str | None, cache: str) -> str:
    if src:
        return os.path.join(src, rel)
    dst = os.path.join(cache, rel.replace("/", "__"))
    if not os.path.exists(dst):
        print("  downloading", rel)
        urllib.request.urlretrieve(f"{BASE_URL}/{rel}", dst)
    return dst


def sha256(path: str) -> str:
    with open(path, "rb") as fh:
        return hashlib.sha256(fh.read()).hexdigest()


def mat(t) -> np.ndarray:
    return np.asarray(t, float).reshape(4, 4)


def to_doser(T_asm: np.ndarray) -> np.ndarray:
    """Onshape assembly pose (m) -> doser-frame pose, before the vertical offset."""
    T = np.eye(4)
    T[:3, :3] = FLIP @ T_asm[:3, :3]
    T[:3, 3] = FLIP @ T_asm[:3, 3]
    return T


def decimate(m, faces: int):
    if len(m.faces) <= faces:
        return m
    try:
        return m.simplify_quadric_decimation(face_count=faces)
    except Exception as exc:  # fast-simplification missing: keep the full mesh
        print("    (not decimated:", exc, ")")
        return m


def merge_voxels(occ: np.ndarray) -> list[tuple[tuple[int, int, int], tuple[int, int, int]]]:
    """Greedy merge of a boolean voxel grid into boxes: [(start ijk, size ijk)]."""
    occ = occ.copy()
    boxes = []
    nx, ny, nz = occ.shape
    for k in range(nz):
        for j in range(ny):
            for i in range(nx):
                if not occ[i, j, k]:
                    continue
                i1 = i
                while i1 + 1 < nx and occ[i1 + 1, j, k]:
                    i1 += 1
                j1 = j
                while j1 + 1 < ny and occ[i:i1 + 1, j1 + 1, k].all():
                    j1 += 1
                k1 = k
                while k1 + 1 < nz and occ[i:i1 + 1, j:j1 + 1, k1 + 1].all():
                    k1 += 1
                occ[i:i1 + 1, j:j1 + 1, k:k1 + 1] = False
                boxes.append(((i, j, k), (i1 - i + 1, j1 - j + 1, k1 - k + 1)))
    return boxes


def collision_boxes(mesh, pitch: float = VOXEL) -> list[dict]:
    """Axis-aligned boxes (doser frame, m) covering a mesh, from a filled voxel grid."""
    vg = mesh.voxelized(pitch).fill()
    occ = vg.matrix
    T = vg.transform  # voxel index -> centre position
    out = []
    for (i, j, k), (a, b, c) in merge_voxels(occ):
        lo = T @ np.array([i, j, k, 1.0])
        hi = T @ np.array([i + a - 1, j + b - 1, k + c - 1, 1.0])
        centre = (lo[:3] + hi[:3]) / 2
        half = (hi[:3] - lo[:3]) / 2 + pitch / 2
        out.append({"center": np.round(centre, 5).tolist(), "half": np.round(half, 5).tolist()})
    return out


def trim_to_auger(boxes: list[dict], A: np.ndarray, auger: dict, margin: float = 0.0005) -> list[dict]:
    """Drop collision boxes that cut into the seated auger (the CAD's parts clear it, so any
    overlap is a voxel artefact): tube, gear and cap, each as a cylinder plus `margin`."""
    o, a = A[:3, 3], A[:3, 2]
    r_t = auger["tube_radius"] / 1000
    g0, g1 = (z / 1000 for z in auger["gear"]["z"])
    cyls = [(0.0, auger["thread"]["z"][0] / 1000, r_t), (g0, g1, auger["gear"]["tip_radius"] / 1000),
            (auger["thread"]["z"][0] / 1000, auger["length"] / 1000 + 0.002, 0.0145)]
    keep = []
    for b in boxes:
        c, h = np.asarray(b["center"]), np.asarray(b["half"])
        hit = False
        for s0, s1, r in cyls:
            for s in np.arange(s0, s1 + 1e-9, 0.001):
                p = o + a * s
                d = np.maximum(np.abs(p - c) - h, 0.0)  # point-to-box distance
                if np.linalg.norm(d) < r + margin:
                    hit = True
                    break
            if hit:
                break
        if not hit:
            keep.append(b)
    return keep


def measure_auger(m) -> dict:
    """Profile of the auger (part frame: outlet end at z = 0, axis +z, mm)."""
    v = m.vertices
    r = np.hypot(v[:, 0], v[:, 1])
    z = v[:, 2]
    gear = v[r > 15.0]
    rg = np.hypot(gear[:, 0], gear[:, 1])
    tips = gear[rg > rg.max() - 0.3]
    ang = np.sort(np.degrees(np.arctan2(tips[:, 1], tips[:, 0])))
    teeth = int(1 + np.sum(np.diff(ang) > 2.0))
    thread = v[(z > 200) & (r > 12.6)]
    tube_r = float(np.round(np.median(r[(z > 95) & (z < 215) & (r > 12.0)]) if np.any((z > 95) & (z < 215) & (r > 12.0)) else 12.5, 2))
    return {
        "length": float(np.round(z.max() - z.min(), 2)),
        "tube_radius": tube_r,                                     # outer, where the clips hold it
        "bore_radius": float(np.round(np.percentile(r[(z > 10) & (z < 70)], 99.5), 2)),
        "screw_core_radius": float(np.round(np.percentile(r[(z > 10) & (z < 70)], 0.5), 2)),
        "gear": {"z": [float(np.round(gear[:, 2].min(), 2)), float(np.round(gear[:, 2].max(), 2))],
                 "tip_radius": float(np.round(rg.max(), 2)), "root_radius": float(np.round(rg.min(), 2)),
                 "teeth": teeth},
        "thread": {"z": [float(np.round(thread[:, 2].min(), 2)), float(np.round(z.max(), 2))],
                   "major_radius": float(np.round(np.hypot(thread[:, 0], thread[:, 1]).max(), 2))},
        "volume_cm3": float(np.round(m.volume / 1000, 3)),
        "outlet_hole_radius": 0.5,  # the end face's centre hole, from the STL (r < 0.5 mm)
    }


def measure_clip(m) -> dict:
    """The C-clip's section (part frame: x across, y along the auger, z up; mm). Fits the seat
    circle to the inner ring below the lips and finds the lips (the narrowest point of the
    mouth) and the arms' wall thickness."""
    from scipy.optimize import least_squares
    yc = 0.5 * (m.bounds[0][1] + m.bounds[1][1])
    sec = m.section(plane_origin=[0, yc, 0], plane_normal=[0, 1, 0])
    P = sec.vertices[:, [0, 2]]
    guess = np.array([0.0, 29.3])
    d = np.hypot(*(P - guess).T)
    a = np.degrees(np.arctan2(P[:, 0] - guess[0], P[:, 1] - guess[1]))
    inner = P[(d > 11) & (d < 13.5) & (np.abs(a) > 100)]
    cx, cz, R = least_squares(lambda p: np.hypot(inner[:, 0] - p[0], inner[:, 1] - p[1]) - p[2],
                              [0.0, 29.3, 12.7]).x
    outer = P[(np.hypot(P[:, 0] - cx, P[:, 1] - cz) > R + 0.5) & (np.hypot(P[:, 0] - cx, P[:, 1] - cz) < R + 4)
              & (np.abs(np.degrees(np.arctan2(P[:, 0] - cx, P[:, 1] - cz))) > 70)
              & (np.abs(np.degrees(np.arctan2(P[:, 0] - cx, P[:, 1] - cz))) < 120)]
    wall = float(np.median(np.hypot(outer[:, 0] - cx, outer[:, 1] - cz)) - R) if len(outer) else 2.0
    # Lips: the points of the mouth closest to the centre line, above the seat centre.
    mouth = P[(P[:, 1] > cz + 5) & (np.abs(P[:, 0]) < R + 1)]
    lip = mouth[np.argmin(np.abs(mouth[:, 0]))]
    # Root of the free arms: where the ring leaves the base block (lowest outer point of the
    # ring that is clear of the block, x beyond the neck).
    return {"seat_center_xz": [float(np.round(cx, 2)), float(np.round(cz, 2))],
            "seat_radius": float(np.round(R, 2)),
            "lip_xz": [float(np.round(abs(lip[0]), 2)), float(np.round(lip[1], 2))],
            "wall_thickness": float(np.round(wall, 2)),
            "width": float(np.round(m.bounds[1][1] - m.bounds[0][1], 2)),
            "tip_z": float(np.round(m.bounds[1][2], 2)),
            "base_z": [0.0, 8.0], "block": {"half_x": 18.0, "z": [8.0, 14.0]}}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--src", help="folder holding cad/onshape-193's files (default: download)")
    args = ap.parse_args()
    import trimesh

    os.makedirs(OUT, exist_ok=True)
    cache = tempfile.mkdtemp(prefix="doser_")
    pj = fetch("assembly/parts.json", args.src, cache)
    parts = {p["label"]: p for p in json.load(open(pj))["parts"]}

    # --- pass 1: load, place, and find the height that puts the legs on the table ----------
    placed = []  # (label, name, kind, faces, mesh_mm, [doser poses before lift])
    sources = {}
    for label, (name, kind, faces) in PARTS.items():
        p = parts[label]
        f = fetch(p["file"], args.src, cache)
        sources[name] = {"file": f"cad/onshape-193/{p['file']}", "sha256": sha256(f)}
        m = trimesh.load(f, force="mesh")
        poses = [to_doser(mat(i["transform"])) for i in p["instances"]]
        placed.append((label, name, kind, faces, m, poses))
    legs = [pl for pl in placed if pl[1] == "leg"][0]
    leg_bottoms = []
    for T in legs[5]:
        v = (legs[4].vertices / 1000) @ T[:3, :3].T + T[:3, 3]
        leg_bottoms.append(v[:, 2].min())
    lift = -min(leg_bottoms)
    # The CAD's two side legs end 16 mm above the back one; on the bench all three stand on
    # the table, so they are slid down their bolt holes by that much.
    leg_shift = [float(-(b - min(leg_bottoms))) for b in leg_bottoms]
    print(f"lift {lift * 1000:.1f} mm; leg shifts (mm): {[round(s * 1000, 1) for s in leg_shift]}")

    geo = {"source": {"repo": REPO, "commit": COMMIT, "path": "cad/onshape-193", "files": sources},
           "frame": ("Doser frame: Onshape's assembly frame rotated 180 deg about x (x kept, y and z "
                     "flipped), raised so the legs stand on z = 0. Units: m in poses, mm in sizes."),
           "lift_m": float(lift), "parts": {}, "primitives": {}, "collision": {}}

    for label, name, kind, faces, m, poses in placed:
        lifted = []
        for i, T in enumerate(poses):
            T = T.copy()
            T[2, 3] += lift + (leg_shift[i] if name == "leg" else 0.0)
            lifted.append(T)
        if kind == "auger":
            mm_ = decimate(m, faces)
            (mm_.copy().apply_scale(1e-3)).export(os.path.join(OUT, "auger.stl"))
            geo["auger"] = measure_auger(m)
            geo["auger"]["seated_pose_in_doser"] = np.round(lifted[0], 6).tolist()
            continue
        if kind == "clip":
            geo["clip"] = measure_clip(m)
            clip_m = decimate(m, faces).copy().apply_scale(1e-3)
            clip_m.export(os.path.join(OUT, "clip.stl"))
            # The rack's open cradle: the same clip with everything above the seat's centre
            # cut off (print the clip and snip its arms, or print this).
            cr = clip_m.copy()
            cr.update_faces(cr.triangles_center[:, 2] < geo["clip"]["seat_center_xz"][1] / 1000 + 0.001)
            cr.remove_unreferenced_vertices()
            cr.export(os.path.join(OUT, "cradle.stl"))
            geo["clip"]["poses_in_doser"] = [np.round(T, 6).tolist() for T in lifted]
            continue
        if kind == "collar":
            # Cut the top of the ring away (a wedge of +-COLLAR_CUT_DEG about the auger's axis,
            # pointing up), so the tube can be lifted out. Done in the doser frame.
            ax_T = np.asarray(geo["auger"]["seated_pose_in_doser"]) if "auger" in geo else None
            mw = m.copy()
            mw.apply_scale(1e-3)
            mw.apply_transform(lifted[0])
            if ax_T is not None:
                o, a = ax_T[:3, 3], ax_T[:3, 2]
                up = np.array([0, 0, 1.0]) - a * a[2]
                up /= np.linalg.norm(up)
                side = np.cross(a, up)
                c = mw.triangles_center - o
                ang = np.degrees(np.arctan2(c @ side, c @ up))
                rad = np.hypot(c @ side, c @ up)
                keep = ~((np.abs(ang) < COLLAR_CUT_DEG) & (rad < 0.0235))
                mw.update_faces(keep)
                mw.remove_unreferenced_vertices()
            decimate(mw, faces).export(os.path.join(OUT, "tap_collar.stl"))
            geo["parts"]["tap_collar"] = {"label": label, "instances": 1,
                                          "note": f"ring cut open +-{COLLAR_CUT_DEG} deg at the top"}
            continue
        # Fixed parts: one STL with every instance, in the doser frame.
        meshes = []
        for T in lifted:
            mw = m.copy()
            mw.apply_scale(1e-3)
            mw.apply_transform(T)
            meshes.append(mw)
        allm = trimesh.util.concatenate(meshes)
        decimate(allm, faces * len(lifted)).export(os.path.join(OUT, f"{name}.stl"))
        geo["parts"][name] = {"label": label, "instances": len(lifted)}
        boxes = []
        for mw in meshes:
            boxes += collision_boxes(mw, VOXEL_NEAR_AUGER if name in NEAR_AUGER else VOXEL)
        n0 = len(boxes)
        boxes = trim_to_auger(boxes, np.asarray(geo["auger"]["seated_pose_in_doser"]), geo["auger"])
        if len(boxes) < n0:
            print(f"    {name}: dropped {n0 - len(boxes)} boxes that overlapped the seated auger")
        geo["collision"][name] = boxes
        print(f"  {name:16s} {len(lifted)} instance(s), {len(boxes)} collision boxes")

    # Pinion: where it meshes with the auger's gear (centre, axis), for the gear check.
    for label, name, kind, faces, m, poses in placed:
        if name == "stepper_pinion":
            T = poses[0].copy()
            T[2, 3] += lift
            c = m.bounds.mean(0) / 1000
            geo["stepper_pinion"] = {"center": np.round(T[:3, :3] @ c + T[:3, 3], 5).tolist(),
                                     "axis": np.round(T[:3, 1], 5).tolist(),
                                     "tip_radius": float(np.round(m.extents[0] / 2, 2)),
                                     "face_width": float(np.round(m.extents[1], 2))}
    # Bought parts as primitives.
    for label, name in PRIMITIVES.items():
        p = parts[label]
        insts = []
        for i in p["instances"]:
            T = to_doser(mat(i["transform"]))
            T[2, 3] += lift
            insts.append(np.round(T, 6).tolist())
        geo["primitives"][name] = {"label": label, "extent_mm": p["extent_mm"], "poses": insts,
                                   "note": "STL not in the repo: drawn as a primitive of this size"}

    # Footprint (for placing the doser and keeping the arm clear of it).
    allv = []
    for label, name, kind, faces, m, poses in placed:
        for T in poses:
            allv.append((m.vertices / 1000) @ T[:3, :3].T + T[:3, 3] + np.array([0, 0, lift]))
    allv = np.vstack(allv)
    geo["bounds_m"] = [np.round(allv.min(0), 4).tolist(), np.round(allv.max(0), 4).tolist()]

    with open(os.path.join(OUT, "geometry.yaml"), "w") as fh:
        fh.write("# Written by tools/build_doser_assets.py: do not edit by hand (re-run it instead).\n")
        yaml.safe_dump(geo, fh, sort_keys=False, width=110)
    print("wrote", OUT)


if __name__ == "__main__":
    main()
