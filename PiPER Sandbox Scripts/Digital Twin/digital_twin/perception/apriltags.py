"""AprilTags in the twin: the tag images the engine paints on its tiles, and a detector that
finds them in rendered camera frames, the same way it would in mpzy's real frames.

    png = tag_png("tag36h11", 31, out_dir)        # texture for the engine
    dets = detect(image, K, tag_sizes)            # ids, corners, poses in the camera frame

Uses OpenCV's built-in AprilTag dictionaries (pip install opencv-python, >= 4.7). Without
OpenCV the tags render as plain white tiles and detection is unavailable.
"""
from __future__ import annotations

import os

import numpy as np

FAMILIES = {"tag36h11": "DICT_APRILTAG_36h11", "tag25h9": "DICT_APRILTAG_25h9",
            "tag16h5": "DICT_APRILTAG_16h5"}
CELL_PX = 16  # texture pixels per tag cell


def _cv2():
    try:
        import cv2
        return cv2 if hasattr(cv2, "aruco") else None
    except ImportError:
        return None


def tag_image(family: str, tag_id: int) -> np.ndarray | None:
    """Tag with its black border and a one-cell white margin, as printed (uint8, 10x10 cells
    for tag36h11). None without OpenCV."""
    cv2 = _cv2()
    if cv2 is None:
        return None
    d = cv2.aruco.getPredefinedDictionary(getattr(cv2.aruco, FAMILIES[family]))
    cells = d.markerSize + 2  # data bits + black border
    img = cv2.aruco.generateImageMarker(d, int(tag_id), cells * CELL_PX, borderBits=1)
    return np.pad(img, CELL_PX, constant_values=255)


def tag_png(family: str, tag_id: int, out_dir: str) -> str | None:
    img = tag_image(family, tag_id)
    if img is None:
        return None
    os.makedirs(out_dir, exist_ok=True)
    path = os.path.join(out_dir, f"{family}_{tag_id}.png")
    if not os.path.exists(path):
        import cv2
        # MuJoCo's texture rows run bottom-up relative to the mesh's v coordinate: flip so the
        # tile reads correctly (tests/test_perception.py checks the decoded ids).
        cv2.imwrite(path, np.ascontiguousarray(np.flipud(img)))
    return path


def intrinsics(fovy_deg: float, width: int, height: int) -> np.ndarray:
    """Pinhole camera matrix of a rendered camera (square pixels)."""
    f = height / 2 / np.tan(np.radians(fovy_deg) / 2)
    return np.array([[f, 0, width / 2], [0, f, height / 2], [0, 0, 1.0]])


def detect(image: np.ndarray, K: np.ndarray, tag_sizes: dict[int, float] | None = None,
           family: str = "tag36h11") -> list[dict]:
    """Find tags in an RGB image. With their sizes (m, by id) also solve each tag's pose in
    the camera frame (OpenCV convention: x right, y down, z forward)."""
    cv2 = _cv2()
    if cv2 is None:
        raise RuntimeError("AprilTag detection needs opencv-python >= 4.7")
    gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY) if image.ndim == 3 else image
    d = cv2.aruco.getPredefinedDictionary(getattr(cv2.aruco, FAMILIES[family]))
    params = cv2.aruco.DetectorParameters()
    params.cornerRefinementMethod = cv2.aruco.CORNER_REFINE_SUBPIX
    det = cv2.aruco.ArucoDetector(d, params)
    corners, ids, _ = det.detectMarkers(gray)
    out = []
    if ids is None:
        return out
    for c, i in zip(corners, ids.ravel()):
        entry = {"id": int(i), "corners": c.reshape(4, 2)}
        if tag_sizes and int(i) in tag_sizes:
            s = tag_sizes[int(i)] / 2
            obj = np.array([[-s, s, 0], [s, s, 0], [s, -s, 0], [-s, -s, 0]], float)
            ok, rv, tv = cv2.solvePnP(obj, entry["corners"], K, None, flags=cv2.SOLVEPNP_IPPE_SQUARE)
            if ok:
                entry["R"], entry["t"] = cv2.Rodrigues(rv)[0], tv.ravel()
        out.append(entry)
    return out


def camera_pose_cv(T_world_cam_mj: np.ndarray) -> np.ndarray:
    """MuJoCo camera frame (looks along -z, y up) -> OpenCV camera frame (z forward, y down)."""
    flip = np.diag([1.0, -1.0, -1.0, 1.0])
    return T_world_cam_mj @ flip
