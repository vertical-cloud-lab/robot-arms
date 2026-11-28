#!/usr/bin/env python3
"""Put the tag cubes where they go in the Digital Twin's cell and look through mpzy's camera.

Builds the twin's cell (../../Digital Twin, its config/*.yaml), takes out the flat tags the
cubes replace (W1-W4, A1-A3, S1-S4, P1-P2), puts every part from cubes.yaml at its `place`,
and renders mpzy's camera at full resolution (4608 x 2592). Then:

  * runs the tag36h11 detector on the frame and, for every part, solves its pose from all
    the tags it shows and compares it with where it really is;
  * does the same for the twin's flat tags in the same spots, for comparison;
  * checks that no part runs into the table, the shelf, the printer, the rest stand or the
    bin (the boxes cell_layout.yaml describes).

    pip install -r requirements.txt -r "../../Digital Twin/requirements.txt"
    MUJOCO_GL=egl python cell_view.py

Writes docs/cell_mpzy.jpg (the frame, every part labelled) and docs/cell_report.json.
"""
from __future__ import annotations

import json
import math
import os
import sys
import xml.etree.ElementTree as ET

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
TWIN = os.path.abspath(os.path.join(HERE, "..", "..", "Digital Twin"))
sys.path.insert(0, HERE)
sys.path.insert(0, TWIN)

import check_cubes as cc  # noqa: E402
import make_cubes  # noqa: E402
import tag_cubes as tc  # noqa: E402

REPLACED = ["W1", "W2", "W3", "W4", "A1", "A2", "A3", "S1", "S2", "S3", "S4", "P1", "P2"]


def pose(x, y, z, yaw):
    return tc.yaw_pose(x, y, z, yaw)


def place(pcfg: dict, part, cell: dict) -> np.ndarray:
    """4x4 pose (mm) of a part's frame in the twin's world frame, from its `place`."""
    p = pcfg.get("place")
    if p == "arm":
        return pose(*cell["arm"]["pose"])
    if "edge" in p:
        sx, sy = cell["table"]["size"][:2]
        a = p.get("along", 0)
        return {"back": pose(a, sy / 2, 0, 0), "front": pose(a, -sy / 2, 0, 180),
                "right": pose(sx / 2, a, 0, -90), "left": pose(-sx / 2, a, 0, 90)}[p["edge"]]
    if "corner" in p:
        sh = cell["shelf"]
        sx, sy = sh["size"][:2]
        x, y, yaw = {"front_left": (-sx / 2, -sy / 2, 0), "front_right": (sx / 2, -sy / 2, 90),
                     "back_left": (-sx / 2, sy / 2, -90), "back_right": (sx / 2, sy / 2, 180)}[p["corner"]]
        return pose(*sh["pose"][:2], 0, sh["pose"][3]) @ pose(x, y, sh["top_z"], yaw)
    pr = cell["printer"]
    T_pr = pose(*pr["pose"])
    if "printer" in p:
        return T_pr @ pose(*p["printer"], 0)
    if "printer_front" in p:
        L = part.cubes[0].spec.edge
        b = pr["base"]
        y_front = b["center"][1] - b["size"][1] / 2
        f = p["printer_front"]
        return T_pr @ pose(f["x"], y_front - L / 2, f["z"] - L / 2, 0)
    raise ValueError(f"{pcfg['name']}: unknown place {p}")


def obstacles(cell: dict) -> dict:
    """The cell's big objects as boxes in the world frame (mm), from cell_layout.yaml."""
    out = {}
    t = cell["table"]
    out["table"] = tc.box((-t["size"][0] / 2, -t["size"][1] / 2, -t["size"][2]), (t["size"][0] / 2, t["size"][1] / 2, 0))
    sh = cell["shelf"]
    T = pose(*sh["pose"][:2], 0, sh["pose"][3])
    top = tc.box((-sh["size"][0] / 2, -sh["size"][1] / 2, sh["top_z"] - sh["size"][2]),
                 (sh["size"][0] / 2, sh["size"][1] / 2, sh["top_z"]))
    out["shelf plate"] = tc._apply(top, T)
    pr = cell["printer"]
    T = pose(*pr["pose"])
    b, c = pr["base"], pr["column"]
    out["printer base"] = tc._apply(tc.box(np.subtract(b["center"], np.divide(b["size"], 2)),
                                           np.add(b["center"], np.divide(b["size"], 2))), T)
    out["printer column"] = tc._apply(tc.box((c["center"][0] - c["size"][0] / 2, c["center"][1] - c["size"][1] / 2, 0),
                                             (c["center"][0] + c["size"][0] / 2, c["center"][1] + c["size"][1] / 2, c["size"][2])), T)
    plate_y = pr["bed_y"]
    ps = pr["bed_size"]
    out["printer bed"] = tc._apply(tc.box((-ps[0] / 2, plate_y - ps[1] / 2, pr["plate_top_z"] - ps[2]),
                                          (ps[0] / 2, plate_y + ps[1] / 2, pr["plate_top_z"])), T)
    rs = cell["rest_stand"]
    Ta = pose(*cell["arm"]["pose"])
    out["rest stand"] = tc._apply(tc.box(np.subtract(rs["center"], np.divide(rs["size"], 2)),
                                         np.add(rs["center"], np.divide(rs["size"], 2))), Ta)
    bx = cell["box"]
    out["bin"] = tc._apply(tc.box((-bx["outer_size"][0] / 2, -bx["outer_size"][1] / 2, 0),
                                  (bx["outer_size"][0] / 2, bx["outer_size"][1] / 2, bx["outer_size"][2])),
                           pose(*bx["pose"]))
    return out


def quat(R):
    """Rotation matrix -> MuJoCo quaternion (w, x, y, z)."""
    w = math.sqrt(max(0.0, 1 + np.trace(R))) / 2
    if w > 1e-6:
        return np.array([w, (R[2, 1] - R[1, 2]) / (4 * w), (R[0, 2] - R[2, 0]) / (4 * w), (R[1, 0] - R[0, 1]) / (4 * w)])
    i = int(np.argmax(np.diag(R)))
    j, k = (i + 1) % 3, (i + 2) % 3
    s = math.sqrt(max(0.0, 1 + R[i, i] - R[j, j] - R[k, k])) * 2
    q = np.zeros(4)
    q[i + 1] = s / 4
    q[0] = (R[k, j] - R[j, k]) / s
    q[j + 1] = (R[j, i] + R[i, j]) / s
    q[k + 1] = (R[k, i] + R[i, k]) / s
    return q


def cell_model(parts, places, mesh_dir, with_cubes=True):
    """The twin's MJCF with the flat tags the cubes replace taken out and the parts added."""
    import mujoco
    from digital_twin.sim import make_sim
    sim = make_sim(engine="mujoco", quiet=True)
    xml_path = sim.engine.xml_path
    tree = ET.parse(xml_path)
    root = tree.getroot()
    if with_cubes:
        parent = {c: p for p in root.iter() for c in p}
        for g in list(root.iter("geom")):
            if g.get("name", "").removeprefix("tag_") in REPLACED:
                parent[g].remove(g)
        asset, world = root.find("asset"), root.find("worldbody")
        for part in parts:
            T = places[part.name]
            q, pos = quat(T[:3, :3]), T[:3, 3] / 1000
            for colour, solid, rgba in (("white", part.white, "0.93 0.93 0.91 1"), ("black", part.black, "0.05 0.05 0.055 1")):
                f = os.path.join(mesh_dir, f"{part.name}_{colour}.stl")
                tc.write_stl(f, solid)
                ET.SubElement(asset, "mesh", name=f"cube_{part.name}_{colour}", file=f, scale="0.001 0.001 0.001")
                ET.SubElement(world, "geom", name=f"cube_{part.name}_{colour}", type="mesh",
                              mesh=f"cube_{part.name}_{colour}", pos=" ".join(f"{v:.6f}" for v in pos),
                              quat=" ".join(f"{v:.6f}" for v in q), rgba=rgba, contype="0", conaffinity="0")
    out = os.path.join(os.path.dirname(xml_path), "scene_tag_cubes.xml" if with_cubes else "scene_flat.xml")
    tree.write(out)
    m = mujoco.MjModel.from_xml_path(out)
    return sim, m


def render_mpzy(m, sim):
    import mujoco
    d = mujoco.MjData(m)
    # The arm's joints as the twin starts them (its rest pose).
    d.qpos[:] = sim.engine.d.qpos[:m.nq] if m.nq == sim.engine.m.nq else d.qpos
    mujoco.mj_forward(m, d)
    w, h = cc.MPZY["w"], cc.MPZY["h"]
    r = mujoco.Renderer(m, h, w)
    r.update_scene(d, camera="mpzy")
    img = r.render().copy()
    cid = m.camera("mpzy").id
    T_wc = np.eye(4)
    T_wc[:3, :3] = d.cam_xmat[cid].reshape(3, 3)
    T_wc[:3, 3] = d.cam_xpos[cid] * 1000
    T_wc = T_wc @ np.diag([1.0, -1.0, -1.0, 1.0])  # MuJoCo camera -> OpenCV camera
    fovy = float(m.cam_fovy[cid])
    r.close()
    return img, T_wc, cc.K_of(w, h, fovy)


def main():
    import cv2
    os.environ.setdefault("MUJOCO_GL", "egl")
    cfg = make_cubes.load()
    parts = make_cubes.build_all(cfg)
    from digital_twin.config import load_config
    cell = load_config().cell
    pcfg = {p["name"]: p for p in cfg["parts"]}
    places = {p.name: place(pcfg[p.name], p, cell) for p in parts}
    report = {"parts": {}, "interference": {}}

    # 1. Does any part run into the cell's furniture?
    obs = obstacles(cell)
    for p in parts:
        solid = tc._apply(p.white + p.black, places[p.name])
        hits = {k: round((solid ^ o).volume(), 1) for k, o in obs.items() if (solid ^ o).volume() > 1.0}
        report["interference"][p.name] = hits
    print("interference (mm^3):", {k: v for k, v in report["interference"].items() if v} or "none")

    # 2. mpzy's view with the cubes.
    mesh_dir = os.path.join(TWIN, "output", "_build", "tag_cubes")
    os.makedirs(mesh_dir, exist_ok=True)
    sim, m = cell_model(parts, places, mesh_dir)
    img, T_wc, K = render_mpzy(m, sim)
    dets = cc.detect(img, cc.TUNED_PERIM)
    dets_default = {i for i, _ in cc.detect(img, cc.DEFAULT_PERIM)}
    by_id = {t["id"]: (p, t) for p in parts for t in p.tags}
    order = tc.CORNER_ORDER["opencv_aruco"]
    out = img.copy()
    for p in parts:
        T_cw = np.linalg.inv(T_wc) @ places[p.name]   # part -> camera, truth
        obj, uv, ids = [], [], []
        for tid, c in dets:
            if tid in by_id and by_id[tid][0] is p:
                t = by_id[tid][1]
                obj.append(t["corners"][order])
                uv.append(c)
                ids.append(tid)
        row = {"tags_decoded": sorted(ids), "faces": sorted({by_id[i][1]["cube"] + " " + by_id[i][1]["face"] for i in ids}),
               "decoded_with_opencv_defaults": sorted(i for i in ids if i in dets_default)}
        if obj:
            P, U = np.vstack(obj), np.vstack(uv)
            flag = cv2.SOLVEPNP_SQPNP if len(obj) > 1 else cv2.SOLVEPNP_IPPE
            ok, rv, tv = cv2.solvePnP(P, U, K, None, flags=flag)
            ok, rv, tv = cv2.solvePnP(P, U, K, None, rv, tv, True, flags=cv2.SOLVEPNP_ITERATIVE)
            R = cv2.Rodrigues(rv)[0]
            row["rot_err_deg"] = round(cc.rot_err_deg(R, T_cw[:3, :3]), 3)
            row["pos_err_mm"] = round(float(np.linalg.norm(tv.ravel() - T_cw[:3, 3])), 2)
            row["distance_m"] = round(float(np.linalg.norm(T_cw[:3, 3])) / 1000, 2)
        report["parts"][p.name] = row
    # 3. The same spots with the twin's flat tags, same detector: one pose per tag (IPPE).
    sim0, m0 = cell_model(parts, places, mesh_dir, with_cubes=False)
    img0, T_wc0, K0 = render_mpzy(m0, sim0)
    flat = {t.id: t for t in sim0.cell.scene.tags if t.name in REPLACED}
    report["flat_tags_in_the_same_spots"] = {n: None for n in REPLACED}
    T_cw0 = np.linalg.inv(T_wc0)
    for tid, c in cc.detect(img0, cc.TUNED_PERIM):
        t = flat.get(tid)
        if t is None:
            continue
        h = t.size * 1000 / 2  # the twin's tile: OpenCV's own corner order
        sq = np.array([[-h, h, 0], [h, h, 0], [h, -h, 0], [-h, -h, 0]], float)
        ok, rv, tv = cv2.solvePnP(sq, c, K0, None, flags=cv2.SOLVEPNP_IPPE_SQUARE)
        T_tag = sim0.engine.body_pose(t.body) @ t.pose
        T_tag[:3, 3] *= 1000
        gt = T_cw0 @ T_tag
        n_err = math.degrees(math.acos(min(1.0, abs(cv2.Rodrigues(rv)[0][:, 2] @ gt[:3, 2]))))
        report["flat_tags_in_the_same_spots"][t.name] = {
            "normal_err_deg": round(n_err, 3), "pos_err_mm": round(float(np.linalg.norm(tv.ravel() - gt[:3, 3])), 2)}

    # Draw: every decoded tag outlined; every cube labelled "name: faces read", with a leader
    # line, labels nudged up until they don't overlap.
    for tid, c in dets:
        col = (20, 200, 60) if tid in by_id else (230, 160, 40)
        cv2.polylines(out, [c.astype(np.int32).reshape(-1, 1, 2)], True, col, 5)
    font, fs, th = cv2.FONT_HERSHEY_SIMPLEX, 2.2, 6
    boxes, labels = [], []
    for p in parts:
        for pl in p.cubes:
            top = (places[p.name] @ pl.T @ np.array([0, 0, pl.spec.edge, 1.0]))[:3]
            anchor = cc.project(top[None], T_wc, K)[0]
            rp = report["parts"][p.name]
            n_faces = len([f for f in rp["faces"] if f.startswith(pl.spec.name + " ")])
            text = f"{pl.spec.name}: {n_faces}"
            (tw, tht), _ = cv2.getTextSize(text, font, fs, th)
            x, y = int(anchor[0] - tw / 2), int(anchor[1] - 70)
            while any(x < bx + bw + 12 and bx < x + tw + 12 and y - tht - 12 < by and by - bh - 12 < y
                      for bx, by, bw, bh in boxes):
                y -= tht + 16
            boxes.append((x, y, tw, tht))
            labels.append((text, (x, y), anchor))
    for text, (x, y), anchor in labels:
        cv2.line(out, (int(anchor[0]), int(anchor[1]) - 8), (x + 30, y + 10), (10, 90, 200), 4, cv2.LINE_AA)
    for text, (x, y), anchor in labels:
        cv2.putText(out, text, (x, y), font, fs, (255, 255, 255), th + 10, cv2.LINE_AA)
        cv2.putText(out, text, (x, y), font, fs, (10, 90, 200), th, cv2.LINE_AA)
    title = "Tag cubes in the Digital Twin's cell, mpzy's camera (4608 x 2592 render). Label: cube: faces decoded"
    cv2.rectangle(out, (0, 0), (out.shape[1], 110), (250, 250, 248), -1)
    cv2.putText(out, title, (40, 75), font, 2.0, (30, 30, 30), 5, cv2.LINE_AA)
    small = cv2.resize(out, (2304, 1296), interpolation=cv2.INTER_AREA)
    cv2.imwrite(os.path.join(HERE, "docs", "cell_mpzy.jpg"), cv2.cvtColor(small, cv2.COLOR_RGB2BGR),
                [cv2.IMWRITE_JPEG_QUALITY, 85])
    with open(os.path.join(HERE, "docs", "cell_report.json"), "w") as f:
        json.dump(report, f, indent=1)
    print(f"{'part':9s} {'dist m':>6s} {'tags':>4s} {'faces read':40s} {'rot deg':>8s} {'pos mm':>7s}")
    for name, r in report["parts"].items():
        print(f"{name:9s} {r.get('distance_m', '-'):>6} {len(r['tags_decoded']):4d} {', '.join(r['faces'])[:40]:40s} "
              f"{r.get('rot_err_deg', '-'):>8} {r.get('pos_err_mm', '-'):>7}  (OpenCV defaults: {len(r['decoded_with_opencv_defaults'])})")
    ft = report["flat_tags_in_the_same_spots"]
    print(f"flat tags in the same spots: {sum(v is not None for v in ft.values())} of {len(REPLACED)} decoded")
    for n, v in ft.items():
        print(f"  {n:3s} " + ("not decoded" if v is None else f"normal {v['normal_err_deg']:.2f} deg, position {v['pos_err_mm']:.1f} mm"))
    print("wrote docs/cell_mpzy.jpg and docs/cell_report.json")


if __name__ == "__main__":
    main()
