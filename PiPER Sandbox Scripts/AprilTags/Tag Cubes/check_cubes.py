#!/usr/bin/env python3
"""Check the AprilTag cubes before printing: render them, detect the tags, solve their pose.

For every part in cubes.yaml this renders the white and black solids (exactly what
make_cubes.py exports) in MuJoCo, with the thing they mount on drawn next to them (the
table's edge, the PiPER's base, the shelf's corner), from a few viewpoints. Then it runs
OpenCV's tag36h11 detector on each frame and checks, for every tag it finds:

  * the ID belongs to that part and to the face it was expected on;
  * the corners land where cube_tags.yaml says (so the stored corners, and their order,
    are right for pose estimation);
  * the pose of the whole part, solved from every corner of every tag in view at once,
    against the truth; and how often a single tag on its own flips to its mirror-image tilt.

The last view of each part is mpzy's camera (Camera Module 3 Wide, full resolution) at the
distance the part will be from it in the cell, so it also says whether the tag size is
big enough. Then a Monte Carlo compares one flat tag with a cube of the same tag size.

    pip install -r requirements.txt
    MUJOCO_GL=egl python check_cubes.py          # headless Linux; drop MUJOCO_GL elsewhere
    python check_cubes.py --parts W1 S1          # a few parts only
    python check_cubes.py --no-render            # only the Monte Carlo

Writes docs/cubes_sheet.jpg (one frame per part, tags outlined) and docs/check_report.json.
"""
from __future__ import annotations

import argparse
import json
import math
import os
import sys
import tempfile

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import make_cubes  # noqa: E402
import tag_cubes as tc  # noqa: E402

TWIN = os.path.join(HERE, "..", "..", "Digital Twin")
PIPER_BASE_STL = os.path.join(TWIN, "assets", "piper", "base.stl")  # metres, arm base frame
DOCS = os.path.join(HERE, "docs")

# mpzy's camera (Digital Twin/config/cell_layout.yaml): Camera Module 3 Wide, full resolution.
MPZY = {"w": 4608, "h": 2592, "fovy": 67.0}
# How far each part is from mpzy in the cell (from cell_layout.yaml and apriltags.yaml), and
# from how high above it looks down. W1, on the far edge of the table, is the hardest case.
MPZY_RANGE = {"W1": (1.27, 26), "W2": (1.15, 29), "W3": (0.95, 36), "W4": (0.85, 41),
              "A_collar": (1.05, 33), "S1": (0.79, 42), "S2": (0.88, 39), "S3": (1.00, 36),
              "S4": (1.06, 33), "P1": (1.03, 31), "P2": (0.96, 33)}


# ------------------------------------------------------------------------------------------
# Scene
# ------------------------------------------------------------------------------------------
def look_at(eye, target, up=(0, 0, 1)):
    """4x4 camera pose (OpenCV frame: x right, y down, z forward) at eye, looking at target."""
    eye, target = np.asarray(eye, float), np.asarray(target, float)
    z = target - eye
    z /= np.linalg.norm(z)
    x = np.cross(z, up)
    x /= np.linalg.norm(x)
    y = np.cross(z, x)
    T = np.eye(4)
    T[:3, 0], T[:3, 1], T[:3, 2], T[:3, 3] = x, y, z, eye
    return T


def view(target, facing_deg, azim_deg, elev_deg, dist_mm):
    """Camera `dist_mm` from target: `facing_deg` is the direction the part's tags face (the
    camera's side), `azim_deg` turns the camera around the part from there, `elev_deg` up."""
    a, e = math.radians(facing_deg + azim_deg), math.radians(elev_deg)
    d = np.array([math.cos(e) * math.cos(a), math.cos(e) * math.sin(a), math.sin(e)])
    return look_at(np.asarray(target) + dist_mm * d, target)


def context(part) -> list:
    """What the part mounts on, as (name, mjcf geom/mesh xml) drawn around it, in mm."""
    wood, black, grey = "0.86 0.74 0.55 1", "0.06 0.06 0.07 1", "0.55 0.56 0.58 1"
    g = []
    if part.mount == "table_edge":    # the plywood table: y < 0, top at z = 0, 19 mm thick
        g.append(f'<geom type="box" pos="0 -0.25 -0.0095" size="0.25 0.25 0.0095" rgba="{wood}"/>')
    elif part.mount == "base_collar":  # the table and the PiPER's base
        g.append(f'<geom type="box" pos="0.05 0 -0.01" size="0.3 0.3 0.01" rgba="{wood}"/>')
        if os.path.exists(PIPER_BASE_STL):
            g.append(f'<geom type="mesh" mesh="piper_base" rgba="0.08 0.08 0.09 1"/>')
    elif part.mount == "shelf_corner":  # the black shelf's plate corner (x, y > 0), 5 mm thick
        g.append(f'<geom type="box" pos="0.09 0.07 -0.0025" size="0.09 0.07 0.0025" rgba="{black}"/>')
        g.append(f'<geom type="box" pos="0.1 0.1 -0.0675" size="0.3 0.3 0.0025" rgba="{wood}"/>')
    else:                              # a printer-grey surface under (or behind) the cube
        if "back" not in part.frame:
            g.append(f'<geom type="box" pos="0 0 -0.005" size="0.12 0.12 0.005" rgba="{grey}"/>')
        else:
            L = part.cubes[0].spec.edge / 1000
            g.append(f'<geom type="box" pos="0 {L / 2 + 0.005} {L / 2}" size="0.12 0.005 0.08" rgba="{grey}"/>')
            g.append(f'<geom type="box" pos="0 0 -0.08" size="0.2 0.2 0.005" rgba="{wood}"/>')
    return g


def build_model(part, mesh_dir, w, h, cams, fovy):
    import mujoco
    assets = [f'<mesh name="white" file="{mesh_dir}/white.stl" scale="0.001 0.001 0.001"/>',
              f'<mesh name="black" file="{mesh_dir}/black.stl" scale="0.001 0.001 0.001"/>']
    if part.mount == "base_collar" and os.path.exists(PIPER_BASE_STL):
        assets.append(f'<mesh name="piper_base" file="{os.path.abspath(PIPER_BASE_STL)}"/>')
    cam_xml = []
    for i, T in enumerate(cams):
        x, y, p = T[:3, 0], -T[:3, 1], T[:3, 3] / 1000  # OpenCV -> MuJoCo camera axes
        cam_xml.append(f'<camera name="c{i}" pos="{p[0]:.6f} {p[1]:.6f} {p[2]:.6f}" '
                       f'xyaxes="{x[0]:.6f} {x[1]:.6f} {x[2]:.6f} {y[0]:.6f} {y[1]:.6f} {y[2]:.6f}" '
                       f'fovy="{fovy}"/>')
    xml = f"""<mujoco>
  <visual><global offwidth="{w}" offheight="{h}"/><quality shadowsize="4096"/>
    <headlight ambient="0.35 0.35 0.35" diffuse="0.45 0.45 0.45" specular="0 0 0"/></visual>
  <asset>{''.join(assets)}
    <material name="white_pla" rgba="0.93 0.93 0.91 1" specular="0.05" shininess="0.1"/>
    <material name="black_pla" rgba="0.05 0.05 0.055 1" specular="0.05" shininess="0.1"/>
  </asset>
  <worldbody>
    <light directional="true" pos="0.3 -0.4 1" dir="-0.3 0.4 -1" diffuse="0.5 0.5 0.5" specular="0 0 0" castshadow="true"/>
    <geom type="mesh" mesh="white" material="white_pla"/>
    <geom type="mesh" mesh="black" material="black_pla"/>
    {''.join(context(part))}
    {''.join(cam_xml)}
  </worldbody>
</mujoco>"""
    return mujoco.MjModel.from_xml_string(xml)


def render_views(part, views, w, h, fovy):
    """Render the part from each camera pose (OpenCV frame, mm). Returns RGB images."""
    import mujoco
    with tempfile.TemporaryDirectory() as d:
        tc.write_stl(os.path.join(d, "white.stl"), part.white)
        tc.write_stl(os.path.join(d, "black.stl"), part.black)
        m = build_model(part, d, w, h, views, fovy)
    data = mujoco.MjData(m)
    mujoco.mj_forward(m, data)
    r = mujoco.Renderer(m, h, w)
    out = []
    for i in range(len(views)):
        r.update_scene(data, camera=f"c{i}")
        out.append(r.render().copy())
    r.close()
    return out


# ------------------------------------------------------------------------------------------
# Detection and pose
# ------------------------------------------------------------------------------------------
def K_of(w, h, fovy):
    f = h / 2 / math.tan(math.radians(fovy) / 2)
    return np.array([[f, 0, w / 2], [0, f, h / 2], [0, 0, 1.0]])


# OpenCV skips any quad whose perimeter is under minMarkerPerimeterRate x the image's larger
# side: by default 0.03, i.e. tags under ~35 px across in mpzy's 4608 px frame. TUNED lowers
# that to ~12 px, which is what a full-resolution pipeline should use.
DEFAULT_PERIM, TUNED_PERIM = 0.03, 0.01


def detect(img, perim=DEFAULT_PERIM):
    import cv2
    gray = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)
    d = cv2.aruco.getPredefinedDictionary(cv2.aruco.DICT_APRILTAG_36h11)
    p = cv2.aruco.DetectorParameters()
    p.minMarkerPerimeterRate = perim
    p.cornerRefinementMethod = cv2.aruco.CORNER_REFINE_SUBPIX
    corners, ids, _ = cv2.aruco.ArucoDetector(d, p).detectMarkers(gray)
    return [] if ids is None else [(int(i), c.reshape(4, 2)) for c, i in zip(corners, ids.ravel())]


def project(P, T_cam, K):
    """Part-frame points (mm) -> pixels, for a camera pose T_cam (OpenCV frame, part frame)."""
    Tc = np.linalg.inv(T_cam)
    pc = P @ Tc[:3, :3].T + Tc[:3, 3]
    uv = pc[:, :2] / pc[:, 2:3]
    return uv * [K[0, 0], K[1, 1]] + [K[0, 2], K[1, 2]]


def rot_err_deg(Ra, Rb):
    c = (np.trace(Ra.T @ Rb) - 1) / 2
    return math.degrees(math.acos(max(-1.0, min(1.0, c))))


def analyse(part, img, T_cam, K, perim=DEFAULT_PERIM):
    """Match detections to the part's tags; solve the part's pose from all of them."""
    import cv2
    by_id = {t["id"]: t for t in part.tags}
    order = tc.CORNER_ORDER["opencv_aruco"]
    found, obj, imgpts, shift_hits, single = [], [], [], {}, []
    for tid, c in detect(img, perim):
        t = by_id.get(tid)
        if t is None:
            found.append({"id": tid, "foreign": True})
            continue
        truth = project(t["corners"], T_cam, K)
        # Which order does the detector list the stored corners in? (expect opencv_aruco)
        errs = [np.abs(c - truth[np.roll(np.arange(4), -s)]).max() for s in range(4)]
        s = int(np.argmin(errs))
        shift_hits[s] = shift_hits.get(s, 0) + 1
        mapped = t["corners"][order]
        err_px = float(np.linalg.norm(c - project(mapped, T_cam, K), axis=1).max())
        # How far off the face's normal the camera looks at it: past ~60 deg the face is a
        # thin sliver and its corners are only roughly found.
        to_cam = T_cam[:3, 3] - t["center"]
        angle = math.degrees(math.acos(np.clip(to_cam @ t["R"][:, 2] / np.linalg.norm(to_cam), -1, 1)))
        found.append({"id": tid, "cube": t["cube"], "face": t["face"], "corner_err_px": round(err_px, 2),
                      "view_angle_deg": round(angle, 1)})
        obj.append(mapped)
        imgpts.append(c)
        # The same tag alone (what a per-tag detector pose gives): rotation error of its pose.
        # IPPE_SQUARE wants the square's corners in its own fixed order (TL, TR, BR, BL), so
        # put the detected corners back into the stored order first.
        h = t["size"] / 2
        sq = np.array([[-h, h, 0], [h, h, 0], [h, -h, 0], [-h, -h, 0]], float)
        ok, rv, tv = cv2.solvePnP(sq, c[np.argsort(order)], K, None, flags=cv2.SOLVEPNP_IPPE_SQUARE)
        R_tag_cam = cv2.Rodrigues(rv)[0]
        R_true = np.linalg.inv(T_cam)[:3, :3] @ t["R"]
        single.append(rot_err_deg(R_tag_cam, R_true))
    res = {"found": found, "corner_order_shift": shift_hits, "single_tag_rot_err_deg": [round(x, 2) for x in single]}
    if obj:
        P, uv = np.vstack(obj), np.vstack(imgpts)
        ok, rv, tv = cv2.solvePnP(P, uv, K, None, flags=cv2.SOLVEPNP_SQPNP)
        ok, rv, tv = cv2.solvePnP(P, uv, K, None, rv, tv, True, flags=cv2.SOLVEPNP_ITERATIVE)
        T_est = np.eye(4)
        T_est[:3, :3], T_est[:3, 3] = cv2.Rodrigues(rv)[0], tv.ravel()
        T_true = np.linalg.inv(T_cam)
        res["all_tags_rot_err_deg"] = round(rot_err_deg(T_est[:3, :3], T_true[:3, :3]), 3)
        res["all_tags_pos_err_mm"] = round(float(np.linalg.norm(T_est[:3, 3] - T_true[:3, 3])), 2)
    return res


def draw(img, part, T_cam, K, scale=1.0, perim=DEFAULT_PERIM, labels=True):
    import cv2
    out = img.copy()
    by_id = {t["id"]: t for t in part.tags}
    lw = max(2, int(round(3 * scale)))
    for tid, c in detect(img, perim):
        t = by_id.get(tid)
        col = (20, 200, 60) if t else (230, 40, 40)
        cv2.polylines(out, [c.astype(np.int32).reshape(-1, 1, 2)], True, col, lw)
        if not labels:
            continue
        label = f"{tid}" + (f" {t['face']}" if t else " ?")
        org = tuple(int(v) for v in c.mean(0) + [-9 * len(label) * scale / 2, 6 * scale])
        cv2.putText(out, label, org, cv2.FONT_HERSHEY_SIMPLEX, 0.6 * scale, (255, 255, 255), lw + 3, cv2.LINE_AA)
        cv2.putText(out, label, org, cv2.FONT_HERSHEY_SIMPLEX, 0.6 * scale, col, lw, cv2.LINE_AA)
    return out


def part_views(part):
    """(target, facing direction) for each part, in its frame: where its camera-side faces point."""
    cs = np.array([pl.T[:3, 3] + [0, 0, pl.spec.edge / 2] for pl in part.cubes])
    target = cs.mean(0)
    facing = {"table_edge": -90, "base_collar": 0, "shelf_corner": -90, "adhesive": -90}[part.mount]
    return target, facing


# ------------------------------------------------------------------------------------------
# Flat tag vs cube: Monte Carlo (pinhole model of mpzy at full resolution, noisy corners)
# ------------------------------------------------------------------------------------------
def study(n=2000, sigma=0.5, dist=1.0, elev=30.0, tag=40.0, seed=0):
    """Rotation error and planar-flip rate: one flat tag on the table vs a cube's faces."""
    import cv2
    rng = np.random.default_rng(seed)
    K = K_of(MPZY["w"], MPZY["h"], MPZY["fovy"])
    spec = tc.CubeSpec("study", 0, tag)
    target = np.array([0, 0, spec.edge / 2])
    T_cam = view(target, -90, 30, elev, dist * 1000)
    h = tag / 2
    sq = np.array([[-h, h, 0], [h, h, 0], [h, -h, 0], [-h, -h, 0]], float)
    cases = {}
    flat_T = np.eye(4)  # a flat tag lying on the table at the cube's spot
    faces = {f: tc.face_frame(spec, f) for f in ("top", "front", "right")}
    layouts = {"1 flat tag on the table": [flat_T],
               "cube: front face alone": [faces["front"]],
               "cube: top + front": [faces["top"], faces["front"]],
               "cube: top + front + right": [faces["top"], faces["front"], faces["right"]]}
    T_true = np.linalg.inv(T_cam)
    for name, frames in layouts.items():
        P = np.vstack([sq @ F[:3, :3].T + F[:3, 3] for F in frames])
        clean = project(P, T_cam, K)
        errs = []
        for _ in range(n):
            uv = clean + rng.normal(0, sigma, clean.shape)
            if len(frames) == 1:  # one square: IPPE, what a single-tag detector does
                Fr = frames[0]
                ok, rv, tv = cv2.solvePnP(sq, uv, K, None, flags=cv2.SOLVEPNP_IPPE_SQUARE)
                R = cv2.Rodrigues(rv)[0] @ Fr[:3, :3].T  # tag pose -> part pose
            else:
                ok, rv, tv = cv2.solvePnP(P, uv, K, None, flags=cv2.SOLVEPNP_SQPNP)
                ok, rv, tv = cv2.solvePnP(P, uv, K, None, rv, tv, True, flags=cv2.SOLVEPNP_ITERATIVE)
                R = cv2.Rodrigues(rv)[0]
            errs.append(rot_err_deg(R, T_true[:3, :3]))
        e = np.array(errs)
        cases[name] = {"median_deg": round(float(np.median(e)), 3), "p95_deg": round(float(np.percentile(e, 95)), 3),
                       "flips_over_10deg": round(float(np.mean(e > 10)), 4)}
    return {"camera": f"mpzy model, {dist} m, {elev} deg above, 30 deg to the side; {sigma} px corner noise; "
                      f"{tag:.0f} mm tags", "cases": cases}


# ------------------------------------------------------------------------------------------
def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--parts", nargs="*", default=None)
    ap.add_argument("--no-render", action="store_true")
    a = ap.parse_args(argv)
    os.makedirs(DOCS, exist_ok=True)
    report = {"parts": {}}
    cfg = make_cubes.load()
    parts = make_cubes.build_all(cfg, set(a.parts) if a.parts else None)
    tiles = []
    if not a.no_render:
        import cv2
        os.environ.setdefault("MUJOCO_GL", "egl")
        for part in parts:
            target, facing = part_views(part)
            span = max(pl.spec.edge for pl in part.cubes) * (3.2 if len(part.cubes) == 1 else 5.5)
            close = [view(target, facing, az, el, span) for az, el in ((0, 25), (35, 35), (-40, 30), (20, 60))]
            W, H, fov = 1200, 900, 40.0
            imgs = render_views(part, close, W, H, fov)
            K = K_of(W, H, fov)
            rep = {"views": []}
            for i, (img, T) in enumerate(zip(imgs, close)):
                r = analyse(part, img, T, K)
                r["view"] = ["front", "front-right", "front-left", "from above"][i]
                rep["views"].append(r)
            # mpzy at the part's real distance, full resolution.
            dist, elev = MPZY_RANGE.get(part.name, (1.0, 30))
            Tm = view(target, facing, 25, elev, dist * 1000)
            img = render_views(part, [Tm], MPZY["w"], MPZY["h"], MPZY["fovy"])[0]
            Km = K_of(MPZY["w"], MPZY["h"], MPZY["fovy"])
            rm = analyse(part, img, Tm, Km, TUNED_PERIM)
            rm["view"] = f"mpzy, {dist} m, {elev} deg above"
            rm["decoded_with_opencv_defaults"] = sum(
                1 for f in analyse(part, img, Tm, Km, DEFAULT_PERIM)["found"] if not f.get("foreign"))
            rep["mpzy"] = rm
            # Crop the mpzy frame around the part for the sheet.
            uv = project(np.vstack([t["corners"] for t in part.tags]), Tm, Km)
            c = uv.mean(0)
            half = max(60, int(np.ptp(uv, axis=0).max() * 0.9))
            x0, y0 = int(max(0, c[0] - half)), int(max(0, c[1] - half))
            crop = draw(img, part, Tm, Km, 1.0, TUNED_PERIM, labels=False)[y0:y0 + 2 * half, x0:x0 + 2 * half]
            expected = len(part.tags)
            seen = [v for v in rep["views"]]
            n_ok = sum(1 for f in rm["found"] if not f.get("foreign"))
            rep["summary"] = {
                "tags": expected,
                "decoded_in_close_views": sorted({f["id"] for v in seen for f in v["found"] if not f.get("foreign")}),
                "foreign_ids": sorted({f["id"] for v in seen + [rm] for f in v["found"] if f.get("foreign")}),
                "max_corner_err_px_close": max([f["corner_err_px"] for v in seen for f in v["found"]
                                                if f.get("view_angle_deg", 99) < 60] or [None]),
                "max_corner_err_px_oblique": max([f["corner_err_px"] for v in seen for f in v["found"]
                                                  if f.get("view_angle_deg", 0) >= 60] or [None]),
                "mpzy_decoded": n_ok, "mpzy_decoded_opencv_defaults": rm["decoded_with_opencv_defaults"]}
            report["parts"][part.name] = rep
            main_img = draw(imgs[1], part, close[1], K, 1.1)
            tiles.append((part.name, main_img, crop, rep))
            s = rep["summary"]
            print(f"{part.name:9s} close views: {len(s['decoded_in_close_views'])}/{expected} tags decoded, "
                  f"corner error <= {s['max_corner_err_px_close']} px (faces seen < 60 deg off-normal; "
                  f"oblique {s['max_corner_err_px_oblique']}), foreign {s['foreign_ids'] or 'none'}; "
                  f"order shifts {[v['corner_order_shift'] for v in seen]}; "
                  f"mpzy {dist} m: {n_ok} decoded ({s['mpzy_decoded_opencv_defaults']} with OpenCV's defaults), "
                  f"pose from all {rm.get('all_tags_rot_err_deg')} deg / "
                  f"{rm.get('all_tags_pos_err_mm')} mm, single tags {rm['single_tag_rot_err_deg']} deg")
        sheet(tiles, os.path.join(DOCS, "cubes_sheet.jpg"))
    report["flat_vs_cube"] = study()
    print("flat tag vs cube (Monte Carlo):", report["flat_vs_cube"]["camera"])
    for k, v in report["flat_vs_cube"]["cases"].items():
        print(f"  {k:28s} median {v['median_deg']:6.3f} deg, 95th {v['p95_deg']:6.3f} deg, flips {v['flips_over_10deg']:.2%}")
    with open(os.path.join(DOCS, "check_report.json"), "w") as f:
        json.dump(report, f, indent=1, default=lambda o: o.tolist() if hasattr(o, "tolist") else str(o))
    print("wrote docs/check_report.json" + ("" if a.no_render else " and docs/cubes_sheet.jpg"))


def sheet(tiles, path, cell=(600, 450)):
    """One row per part: the close render with detections, and mpzy's view of it (cropped)."""
    import cv2
    rows = []
    for name, big, crop, rep in tiles:
        a = cv2.resize(big, cell, interpolation=cv2.INTER_AREA)
        b = cv2.resize(crop, (cell[1], cell[1]), interpolation=cv2.INTER_AREA)
        s = rep["summary"]
        txt = np.full((cell[1], 420, 3), 250, np.uint8)
        lines = [name, f"{len(s['decoded_in_close_views'])}/{s['tags']} tags read up close",
                 f"mpzy at {rep['mpzy']['view'].split(', ')[1]}: {s['mpzy_decoded']} read",
                 f"  ({s['mpzy_decoded_opencv_defaults']} with OpenCV defaults)",
                 f"pose from all: {rep['mpzy'].get('all_tags_rot_err_deg')} deg,",
                 f"  {rep['mpzy'].get('all_tags_pos_err_mm')} mm"]
        for i, ln in enumerate(lines):
            cv2.putText(txt, ln, (14, 50 + 48 * i), cv2.FONT_HERSHEY_SIMPLEX, 0.8 if i else 1.1,
                        (30, 30, 30), 2 if i == 0 else 1, cv2.LINE_AA)
        rows.append(np.hstack([a, b, txt]))
    out = np.vstack(rows)
    cv2.imwrite(path, cv2.cvtColor(out, cv2.COLOR_RGB2BGR), [cv2.IMWRITE_JPEG_QUALITY, 85])


if __name__ == "__main__":
    main()
