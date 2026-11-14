"""Scenario: what mpzy's camera sees, and which AprilTags a detector finds in it.

Renders the fixed camera (cell_layout.yaml cameras.mpzy) at its configured resolution, runs
OpenCV's tag36h11 detector on the frame, and compares each detected tag's pose with the
ground truth from the scene. Saves the frame with the detections drawn on it.

    python run_sim.py --scenario camera_check
    python run_sim.py --scenario camera_check --camera wrist

This is the loop the real cell will run (camera -> tags -> poses), so it is where to try
tag sizes, camera placement and resolution before printing and sticking anything.
"""
from __future__ import annotations

import numpy as np

from digital_twin.perception.apriltags import camera_pose_cv, detect, intrinsics


def run(sim, args) -> dict:
    import cv2
    e, cell = sim.engine, sim.cell
    cam_name = args.camera if args.camera in ("mpzy", "wrist") else "mpzy"
    cc = sim.cfg.cell["cameras"][cam_name]
    w, h = cc["resolution"]
    if cam_name == "wrist":
        from digital_twin.sim import ready
        ready(sim)
    img = e.render(cam_name, w, h)
    if img is None:
        print("this engine has no camera renderer; use --engine mujoco")
        return {}
    K = intrinsics(cc["fovy_deg"], w, h)
    sizes = {t.id: t.size for t in cell.scene.tags}
    dets = detect(img, K, sizes)
    # Ground truth: tag poses in the camera's OpenCV frame.
    m, d = e.m, e.d
    cid = m.camera(cam_name).id
    T_wc = np.eye(4)
    T_wc[:3, :3] = d.cam_xmat[cid].reshape(3, 3)
    T_wc[:3, 3] = d.cam_xpos[cid]
    T_cw = np.linalg.inv(camera_pose_cv(T_wc))
    by_id = {t.id: t for t in cell.scene.tags}
    rows = []
    for det in dets:
        t = by_id.get(det["id"])
        row = {"id": det["id"], "name": t.name if t else "?"}
        if t is not None and "t" in det:
            T_tag = e.body_pose(t.body) @ t.pose
            gt = T_cw @ T_tag
            row["pos_err_mm"] = float(np.linalg.norm(det["t"] - gt[:3, 3]) * 1000)
            row["dist_m"] = float(np.linalg.norm(gt[:3, 3]))
            # Tag frames differ in convention (OpenCV's tag z points into the tag); compare normals.
            row["normal_err_deg"] = float(np.degrees(np.arccos(np.clip(abs(det["R"][:, 2] @ gt[:3, 2]), -1, 1))))
        rows.append(row)
    rows.sort(key=lambda r: r["name"])
    missing = sorted(t.name for t in cell.scene.tags if t.id not in {r["id"] for r in rows})
    print(f"{cam_name}: {w}x{h}, {len(rows)} of {len(cell.scene.tags)} tags found")
    for r in rows:
        extra = (f"  {r['dist_m']:.2f} m away, position error {r['pos_err_mm']:.1f} mm, "
                 f"normal {r['normal_err_deg']:.1f} deg") if "pos_err_mm" in r else ""
        print(f"  {r['name']:3s} id {r['id']:3d}{extra}")
    print("  not found:", ", ".join(missing) or "none")
    out = img.copy()
    for det in dets:
        c = det["corners"].astype(int)
        cv2.polylines(out, [c.reshape(-1, 1, 2)], True, (0, 220, 0), 2)
        name = by_id[det["id"]].name if det["id"] in by_id else str(det["id"])
        cv2.putText(out, name, tuple(c[0] + np.array([0, -6])), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
    path = sim.cfg.path(f"output/camera_check_{cam_name}.png")
    import imageio
    imageio.imwrite(path, out)
    print("  image:", path)
    return {"camera": cam_name, "found": rows, "missing": missing, "image": path}
