"""Seeing the cell: take a still with mpzy's camera, find the AprilTags in it, and turn them
into where the holder and the box are, in the arm's frame.

1. capture(): a full-resolution still. mpzy livestreams this camera (livestream/device.py,
   PR #81), and a stream holds its camera, so each still borrows it: write our PID to
   /tmp/picam-pause-<camera>, wait for the stream to let go, take the still. The stream sends
   a "camera in use" card meanwhile and takes the camera back 5 s after the still.
2. detect(): every tag36h11 tag in the image (OpenCV's ArUco module, which has the AprilTag
   families), with its four corners.
3. Camera.tag_in_arm(): one tag's pose in the arm frame. solvePnP gives it relative to the
   camera; calibration.json (calibrate.py) says where the camera is relative to the arm.
4. locate(): an object's pose (x, y, z, yaw) from its tags, fitted to every corner of every
   one of its tags at once, using where settings.py says each sits on the object. Two tags
   fix the direction far better than one, and how well the corners fit is a check.

Tag frame (OpenCV's): origin at the tag's centre, x toward its right edge and y toward its top
edge as the tag is printed (make_tags.py prints an arrow), z out of its face.
"""
import json
import math
import os
import subprocess

import cv2
import numpy as np

import settings as S

HERE = os.path.dirname(os.path.abspath(__file__))
DICTIONARY = cv2.aruco.getPredefinedDictionary(cv2.aruco.DICT_APRILTAG_36h11)


# ---------------------------------------------------------------- the camera model
def look_at(position, target):
    """4x4 pose of a camera at position looking at target (arm frame, mm): camera z forward,
    x right, y down (OpenCV's convention), with the image's top edge level."""
    p, t = np.asarray(position, float), np.asarray(target, float)
    z = (t - p) / np.linalg.norm(t - p)
    x = np.cross(z, [0.0, 0.0, 1.0])
    x /= np.linalg.norm(x)
    y = np.cross(z, x)
    T = np.eye(4)
    T[:3, :3] = np.column_stack([x, y, z])
    T[:3, 3] = p
    return T


class Camera:
    """Pinhole camera with OpenCV's distortion model, and where it sits in the arm frame.

    K: 3x3 intrinsics (pixels). dist: OpenCV distortion coefficients. cam_in_arm: 4x4 pose of
    the camera in the arm frame (camera z forward, x right, y down)."""

    def __init__(self, K, dist, cam_in_arm, size):
        self.K = np.asarray(K, float)
        self.dist = np.asarray(dist, float).ravel()
        self.cam_in_arm = np.asarray(cam_in_arm, float)
        self.size = tuple(int(v) for v in size)

    @classmethod
    def nominal(cls, scale=1.0):
        """The camera settings.py guesses: before calibration, and for --dry-run."""
        w, h = (round(v * scale) for v in S.CAMERA_SIZE)
        f = S.CAMERA_FOCAL_PX * scale
        K = [[f, 0, w / 2], [0, f, h / 2], [0, 0, 1]]
        return cls(K, [0, 0, 0, 0, 0], look_at(S.CAMERA_GUESS_POSITION, S.CAMERA_GUESS_LOOK_AT),
                   (w, h))

    @classmethod
    def load(cls, path=None):
        """The camera calibrate.py measured, or None if it hasn't been run."""
        path = path or os.path.join(HERE, S.CALIBRATION_FILE)
        if not os.path.exists(path):
            return None
        with open(path) as f:
            c = json.load(f)
        return cls(c["K"], c["dist"], c["cam_in_arm"], c["image_size"])

    def scaled(self, scale):
        """The same camera taking images scale times the size (the simulation renders small)."""
        K = self.K.copy()
        K[:2] *= scale
        return Camera(K, self.dist, self.cam_in_arm, (round(self.size[0] * scale),
                                                      round(self.size[1] * scale)))

    def project(self, points_arm):
        """Pixels (N x 2) of arm-frame points (N x 3, mm)."""
        P = np.asarray(points_arm, float).reshape(-1, 3)
        arm_in_cam = np.linalg.inv(self.cam_in_arm)
        rvec, _ = cv2.Rodrigues(arm_in_cam[:3, :3])
        px, _ = cv2.projectPoints(P, rvec, arm_in_cam[:3, 3], self.K, self.dist)
        return px.reshape(-1, 2)

    def tag_in_arm(self, corners, size_mm, face_up=True):
        """4x4 pose of a tag in the arm frame from its four image corners (OpenCV's order).
        A square seen at an angle has two poses that fit almost equally well (the tag seems to
        "flip"); with face_up, the one whose face points more nearly up wins."""
        h = size_mm / 2
        obj = np.array([[-h, h, 0], [h, h, 0], [h, -h, 0], [-h, -h, 0]], float)
        n, rvecs, tvecs, errs = cv2.solvePnPGeneric(
            obj, np.asarray(corners, float).reshape(4, 1, 2), self.K, self.dist,
            flags=cv2.SOLVEPNP_IPPE_SQUARE)
        best = None
        for rvec, tvec, err in zip(rvecs, tvecs, np.ravel(errs)):
            T = np.eye(4)
            T[:3, :3] = cv2.Rodrigues(rvec)[0]
            T[:3, 3] = tvec.ravel()
            T = self.cam_in_arm @ T
            score = -T[2, 2] if face_up else 0.0  # lower is better: the face's normal, up
            if best is None or (err < 2 * best[2] + 0.5 and score < best[1]):
                best = (T, score, err)
        return best[0]


# ---------------------------------------------------------------- taking and reading images
def capture(path, camera_index=None):
    """Take a full-resolution still on this Pi, borrowing the camera from its livestream."""
    idx = S.CAMERA_INDEX if camera_index is None else camera_index
    w, h = S.CAMERA_SIZE
    stream = f"pgrep -f 'rpicam-vid .*--codec yuv420 .*--camera {idx} ' >/dev/null"
    script = (f"echo $$ > /tmp/picam-pause-{idx}; "
              f"for i in $(seq 100); do {stream} || break; sleep 0.1; done; "
              f"exec rpicam-still -n --camera {idx} -t 1500 --width {w} --height {h} "
              f"--lens-position {S.CAMERA_LENS_POSITION} -q 93 -o '{path}'")
    p = subprocess.run(["bash", "-c", script], capture_output=True, text=True, timeout=60)
    if p.returncode or not os.path.exists(path):
        raise RuntimeError(f"rpicam-still failed (exit {p.returncode}): "
                           f"{(p.stderr or p.stdout).strip()[-300:]}")
    image = cv2.imread(path)
    if image is None:
        raise RuntimeError(f"couldn't read {path}")
    return image


def detect(image):
    """{tag id: 4 x 2 corners in pixels} for every tag36h11 tag found."""
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY) if image.ndim == 3 else image
    params = cv2.aruco.DetectorParameters()
    params.cornerRefinementMethod = cv2.aruco.CORNER_REFINE_SUBPIX
    params.minMarkerPerimeterRate = 0.01  # small tags far away in a 12 MP image
    corners, ids, _ = cv2.aruco.ArucoDetector(DICTIONARY, params).detectMarkers(gray)
    if ids is None:
        return {}
    return {int(i): c.reshape(4, 2) for i, c in zip(ids.ravel(), corners)}


class Found:
    """An object located by its tags: x, y, z (mm) and yaw (deg) of its frame in the arm
    frame, the tags it used, and how well they fit (RMS of the corners, pixels)."""

    def __init__(self, x, y, z, yaw, tags, fit_px):
        self.x, self.y, self.z, self.yaw = x, y, z, yaw
        self.tags, self.fit_px = tags, fit_px

    def to_arm(self, p):
        """An object-frame point (mm) in the arm frame."""
        c, s = math.cos(math.radians(self.yaw)), math.sin(math.radians(self.yaw))
        return [self.x + c * p[0] - s * p[1], self.y + s * p[0] + c * p[1], self.z + p[2]]

    def axis(self):
        """The object's x axis in the arm frame."""
        return [math.cos(math.radians(self.yaw)), math.sin(math.radians(self.yaw)), 0.0]

    def __repr__(self):
        return (f"x {self.x:.1f}, y {self.y:.1f}, z {self.z:.1f} mm, yaw {self.yaw:.1f} deg "
                f"(tags {self.tags}, fit {self.fit_px:.2f} px)")


def _corners_in_arm(p, centres, turns, size_mm):
    """The four corners (OpenCV's order) of each flat, face-up tag of an object at
    p = (x, y, z, yaw in rad): centres in the object frame, turns (rad) of each tag on it."""
    x, y, z, yaw = p
    h = size_mm / 2
    out = []
    for (cx, cy, cz), t in zip(centres, turns):
        for u, v in ((-h, h), (h, h), (h, -h), (-h, -h)):
            ox = cx + u * math.cos(t) - v * math.sin(t)   # corner in the object frame
            oy = cy + u * math.sin(t) + v * math.cos(t)
            out.append([x + ox * math.cos(yaw) - oy * math.sin(yaw),
                        y + ox * math.sin(yaw) + oy * math.cos(yaw), z + cz])
    return out


def locate(detections, tags, size_mm, camera, z=None):
    """Where an object is, from its tags (settings: {id: (x, y, z) of the tag's centre in the
    object frame}), all lying flat and face up. None if none of them was seen, or if only one
    was and z (the object frame's height, known from an earlier look) isn't given: one tag on
    its own can't tell its distance from the camera well enough (5-20 mm off in tests).

    1. A first guess: each tag's pose on its own (solvePnP). With two or more tags, the line
       between their centres gives the direction, and each tag's own turn on the object is
       rounded to a multiple of 90 deg, so a tag stuck on sideways or upside down still works.
       With one tag, it must be stuck with its x along the object's x.
    2. Then x, y, z and the yaw are fitted to every corner of every tag at once (least
       squares, Gauss-Newton). The tags then act as one big tag, and lying flat is built in,
       which makes the height and position several times better than one tag's solvePnP."""
    seen = sorted(i for i in tags if i in detections)
    if not seen or (len(seen) == 1 and z is None):
        return None
    poses = {i: camera.tag_in_arm(detections[i], size_mm) for i in seen}
    m = np.array([poses[i][:3, 3] for i in seen])         # measured centres, arm frame
    c = np.array([tags[i] for i in seen], float)          # the same centres, object frame
    tag_yaw = {i: math.atan2(poses[i][1, 0], poses[i][0, 0]) for i in seen}
    if len(seen) == 1:
        yaw, turns = tag_yaw[seen[0]], [0.0]
    else:  # the best-fitting turn of the layout onto the measured centres (2D Kabsch)
        a, b = c[:, :2] - c[:, :2].mean(0), m[:, :2] - m[:, :2].mean(0)
        yaw = math.atan2(np.sum(a[:, 0] * b[:, 1] - a[:, 1] * b[:, 0]),
                         np.sum(a[:, 0] * b[:, 0] + a[:, 1] * b[:, 1]))
        turns = [math.radians(90 * round(math.degrees(tag_yaw[i] - yaw) / 90)) for i in seen]
    R = np.array([[math.cos(yaw), -math.sin(yaw)], [math.sin(yaw), math.cos(yaw)]])
    xy = (m[:, :2] - c[:, :2] @ R.T).mean(0)
    p = np.array([xy[0], xy[1], (m[:, 2] - c[:, 2]).mean() if z is None else z, yaw])
    seen_px = np.concatenate([detections[i] for i in seen]).ravel()
    free = [0, 1, 3] if z is not None else [0, 1, 2, 3]  # z known: fit only x, y and yaw

    def residual(pp):
        return camera.project(_corners_in_arm(pp, c, turns, size_mm)).ravel() - seen_px

    for _ in range(15):  # Gauss-Newton
        r = residual(p)
        J = np.column_stack([(residual(p + d) - r) / d[k]
                             for k, d in enumerate(np.diag([0.05, 0.05, 0.05, 1e-4])) if k in free])
        step = np.zeros(4)
        step[free] = np.linalg.lstsq(J, -r, rcond=None)[0]
        p = p + step
        if np.all(np.abs(step[:3]) < 1e-3) and abs(step[3]) < 1e-6:
            break
    fit = float(np.sqrt(np.mean(residual(p).reshape(-1, 2) ** 2) * 2))
    return Found(float(p[0]), float(p[1]), float(p[2]), math.degrees(p[3]), seen, fit)


# ---------------------------------------------------------------- pictures for people
def annotate(image, detections, camera, marks=(), path=None, width=1600):
    """A copy of image, scaled to width, with the tags outlined and labelled and each mark
    (label, arm-frame point, BGR colour) drawn as a dot."""
    k = width / image.shape[1]
    out = cv2.resize(image, (width, round(image.shape[0] * k)), interpolation=cv2.INTER_AREA)
    for i, c in detections.items():
        pts = (c * k).astype(np.int32)
        cv2.polylines(out, [pts], True, (0, 200, 0), 2)
        cv2.putText(out, str(i), tuple(pts[0] + [0, -6]), cv2.FONT_HERSHEY_SIMPLEX, 0.6,
                    (0, 200, 0), 2)
    for label, p, colour in marks:
        u, v = (camera.project([p])[0] * k).astype(int)
        cv2.circle(out, (int(u), int(v)), 6, colour, -1)
        cv2.putText(out, label, (int(u) + 8, int(v) - 8), cv2.FONT_HERSHEY_SIMPLEX, 0.55,
                    colour, 2)
    if path:
        cv2.imwrite(path, out, [cv2.IMWRITE_JPEG_QUALITY, 85])
    return out


def tag_image(tag_id, cell_px):
    """The tag as printed: its 8 x 8 black-bordered square plus a white border one cell wide
    (10 x 10 cells), cell_px pixels per cell."""
    inner = cv2.aruco.generateImageMarker(DICTIONARY, tag_id, 8 * cell_px)
    return cv2.copyMakeBorder(inner, cell_px, cell_px, cell_px, cell_px, cv2.BORDER_CONSTANT,
                              value=255)


def render(camera, tags, background=165, seed=0):
    """A synthetic camera image of tags (list of (id, size_mm, 4x4 pose in the arm frame)),
    for --dry-run and the tests: the real detection then runs on it."""
    w, h = camera.size
    rng = np.random.default_rng(seed)
    img = np.clip(rng.normal(background, 6, (h, w)), 0, 255).astype(np.uint8)
    cam_pos = camera.cam_in_arm[:3, 3]
    for tag_id, size, T in tags:
        T = np.asarray(T, float)
        if np.dot(T[:3, 2], cam_pos - T[:3, 3]) <= 0:
            continue  # facing away from the camera
        cell = 12
        bitmap = tag_image(tag_id, cell)
        half = size * 10 / 16  # with its white border the tag is 10/8 of its black square
        corners = [[-half, half, 0], [half, half, 0], [half, -half, 0], [-half, -half, 0]]
        world = [(T @ np.array([*p, 1.0]))[:3] for p in corners]
        dst = camera.project(world).astype(np.float32)
        if not (np.all(dst[:, 0] > 0) and np.all(dst[:, 0] < w) and np.all(dst[:, 1] > 0)
                and np.all(dst[:, 1] < h)):
            continue
        n = bitmap.shape[0]
        src = np.float32([[0, 0], [n, 0], [n, n], [0, n]])
        H = cv2.getPerspectiveTransform(src, dst)
        warped = cv2.warpPerspective(bitmap, H, (w, h), flags=cv2.INTER_AREA)
        mask = cv2.warpPerspective(np.full_like(bitmap, 255), H, (w, h))
        img[mask > 127] = warped[mask > 127]
    img = cv2.GaussianBlur(img, (3, 3), 0)
    return cv2.cvtColor(img, cv2.COLOR_GRAY2BGR)


def flat_tag_pose(x, y, z, yaw_deg):
    """4x4 pose of a tag lying flat, face up, its x axis at yaw_deg (arm frame)."""
    c, s = math.cos(math.radians(yaw_deg)), math.sin(math.radians(yaw_deg))
    T = np.eye(4)
    T[:3, :3] = [[c, -s, 0], [s, c, 0], [0, 0, 1]]
    T[:3, 3] = [x, y, z]
    return T
