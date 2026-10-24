#!/usr/bin/env python3
"""Digital twin of the PiPER as the fixed side camera sees it (issue #24).

Runs on the runner or a laptop, never on the arm Pi (it needs numpy, opencv and trimesh, and it
never talks to the arm):

    python piper_twin.py --camera docs/issue-24/camera.json --joints 0,0,0,0,0,0 --out twin.png
    python piper_twin.py --camera docs/issue-24/camera.json --joints ... --background frame.jpg

Kinematics. The links are posed with AgileX's URDF (piper_ros, pinned to MESH_SHA). Its joint
origins reproduce piper_sdk's modified-DH forward kinematics (the table in piper_pick_tape.py)
to 0.1 mm and 0.01 deg over random joint angles, so SDK joint feedback can drive it directly.
Lengths are in mm in the arm's base frame: x forward along J1 = 0, z up, origin on the
mounting surface under J1.

Camera. A pinhole camera with OpenCV's radial-tangential distortion (k1, k2, p1, p2, k3), stored
as JSON with the image size the numbers belong to. rvec/tvec map base-frame points into the
camera frame (OpenCV convention: x right, y down, z forward). Camera.scaled() moves the same
camera to another output size of the same field of view (rpicam's 2304x1296 and 4608x2592
modes both cover the full sensor; the 1536x864 mode is a centre crop and is not the same view).

Rendering. Every mesh vertex goes through the same Camera.project() that predicts keypoints,
so the rendered arm and the predicted points can never disagree about the camera. Faces are
flat-shaded and painted far to near (no z-buffer), which is plenty for a picture of an arm.
"""
import argparse
import json
import math
import os
import urllib.request

import cv2
import numpy as np

MESH_SHA = "ac41fcbcdda598f01b51cf6175ed9a24d0dacadc"  # agilexrobotics/piper_ros (MIT)
MESH_URL = ("https://raw.githubusercontent.com/agilexrobotics/piper_ros/{sha}/src/"
            "piper_description/meshes/{name}.STL")
CACHE = os.path.expanduser("~/.cache/piper_twin")

# Joint origins from piper_description.urdf at MESH_SHA: (parent, child, xyz mm, rpy rad, joint).
# joint7/joint8 are the fingers (prismatic, metres in the URDF); each moves half the opening.
CHAIN = [
    ("base_link", "link1", (0, 0, 123), (0, 0, 0), 0),
    ("link1", "link2", (0, 0, 0), (1.5708, -0.1359, -3.1416), 1),
    ("link2", "link3", (285.03, 0, 0), (0, 0, -1.7939), 2),
    ("link3", "link4", (-21.984, -250.75, 0), (1.5708, 0, 0), 3),
    ("link4", "link5", (0, 0, 0), (-1.5708, 0, 0), 4),
    ("link5", "link6", (0.088259, -91, 0), (1.5708, 0, 0), 5),
    ("link6", "gripper_base", (0, 0, 0), (0, 0, 0), None),
    ("gripper_base", "link7", (0, 0, 135.8), (1.5708, 0, 0), "f+"),
    ("gripper_base", "link8", (0, 0, 135.8), (1.5708, 0, -3.1416), "f-"),
]
MESHES = ["base_link", "link1", "link2", "link3", "link4", "link5", "link6", "gripper_base",
          "link7", "link8"]
TIP_MM = 135.8  # fingertips along the link-6 z axis from the flange (URDF finger meshes)

# Points the comparison tracks: (name, link, offset in that link's frame, mm).
KEYPOINTS = [
    ("base", "base_link", (0, 0, 0)),
    ("J2", "link2", (0, 0, 0)),
    ("J3", "link3", (0, 0, 0)),
    ("wrist", "link5", (0, 0, 0)),
    ("flange", "link6", (0, 0, 0)),
    ("tip", "link6", (0, 0, TIP_MM)),
]
SKELETON = ["base", "J2", "J3", "wrist", "flange", "tip"]


def rpy_matrix(r, p, y):
    cr, sr, cp, sp, cy, sy = (math.cos(r), math.sin(r), math.cos(p), math.sin(p),
                              math.cos(y), math.sin(y))
    return (np.array([[cy, -sy, 0], [sy, cy, 0], [0, 0, 1]])
            @ np.array([[cp, 0, sp], [0, 1, 0], [-sp, 0, cp]])
            @ np.array([[1, 0, 0], [0, cr, -sr], [0, sr, cr]]))


def rot_z(t):
    c, s = math.cos(t), math.sin(t)
    return np.array([[c, -s, 0], [s, c, 0], [0, 0, 1]])


def link_poses(q_deg, gripper_mm=0.0):
    """4x4 pose (mm) of every link in the base frame for SDK joint angles (deg)."""
    T = {"base_link": np.eye(4)}
    for parent, child, xyz, rpy, j in CHAIN:
        M = np.eye(4)
        M[:3, :3] = rpy_matrix(*rpy)
        M[:3, 3] = xyz
        J = np.eye(4)
        if isinstance(j, int):
            J[:3, :3] = rot_z(math.radians(q_deg[j]))
        elif j == "f+":
            J[2, 3] = gripper_mm / 2
        elif j == "f-":
            J[2, 3] = -gripper_mm / 2  # joint8's axis is -z
        T[child] = T[parent] @ M @ J
    return T


def keypoints_3d(q_deg, gripper_mm=0.0):
    T = link_poses(q_deg, gripper_mm)
    return {n: (T[link] @ np.array([*off, 1.0]))[:3] for n, link, off in KEYPOINTS}


# ---------------------------------------------------------------- camera
class Camera:
    def __init__(self, width, height, K, dist, rvec, tvec):
        self.width, self.height = int(width), int(height)
        self.K = np.asarray(K, float).reshape(3, 3)
        self.dist = np.asarray(dist, float).ravel()
        self.rvec = np.asarray(rvec, float).ravel()
        self.tvec = np.asarray(tvec, float).ravel()

    @classmethod
    def load(cls, path):
        d = json.load(open(path))
        return cls(d["width"], d["height"], d["K"], d["dist"], d["rvec"], d["tvec"])

    def to_dict(self):
        return {"width": self.width, "height": self.height, "K": self.K.round(4).tolist(),
                "dist": self.dist.round(6).tolist(), "rvec": self.rvec.round(6).tolist(),
                "tvec": self.tvec.round(3).tolist()}

    def save(self, path, **extra):
        json.dump({**self.to_dict(), **extra}, open(path, "w"), indent=1)

    def scaled(self, width, height):
        """The same camera at another output size of the same field of view."""
        sx, sy = width / self.width, height / self.height
        K = self.K.copy()
        K[0] *= sx
        K[1] *= sy
        return Camera(width, height, K, self.dist, self.rvec, self.tvec)

    def cropped(self, x0, y0, w, h, out_w, out_h):
        """The camera that sees the crop (x0, y0, w, h) of this one's image, resized to out_w x
        out_h. Distortion acts before K, so only K changes."""
        K = self.K.copy()
        K[0, 2] -= x0
        K[1, 2] -= y0
        K[0] *= out_w / w
        K[1] *= out_h / h
        return Camera(out_w, out_h, K, self.dist, self.rvec, self.tvec)

    def R(self):
        return cv2.Rodrigues(self.rvec)[0]

    def center(self):
        """Camera position in the base frame (mm)."""
        return -self.R().T @ self.tvec

    def to_cam(self, pts):
        return np.asarray(pts, float).reshape(-1, 3) @ self.R().T + self.tvec

    def project(self, pts):
        """Pixel coordinates (N x 2) of base-frame points (N x 3, mm)."""
        pts = np.asarray(pts, float).reshape(-1, 3)
        uv, _ = cv2.projectPoints(pts, self.rvec, self.tvec, self.K, self.dist)
        return uv.reshape(-1, 2)

    def mm_per_px(self, pt):
        """Size of one pixel (mm) at a base-frame point, for turning pixel errors into mm."""
        return float(self.to_cam(pt)[0, 2] / self.K[0, 0])


def look_at(eye, target, up=(0, 0, 1)):
    """rvec, tvec of a camera at eye (mm) looking at target, image up roughly along up."""
    eye, target, up = (np.asarray(v, float) for v in (eye, target, up))
    z = target - eye
    z /= np.linalg.norm(z)
    x = np.cross(z, up)
    x /= np.linalg.norm(x)
    y = np.cross(z, x)
    R = np.stack([x, y, z])
    return cv2.Rodrigues(R)[0].ravel(), -R @ eye


def virtual_camera(width, height, hfov_deg, eye, target):
    f = width / 2 / math.tan(math.radians(hfov_deg) / 2)
    K = [[f, 0, width / 2], [0, f, height / 2], [0, 0, 1]]
    rvec, tvec = look_at(eye, target)
    return Camera(width, height, K, [0, 0, 0, 0, 0], rvec, tvec)


# ---------------------------------------------------------------- meshes and rendering
def load_meshes(cache=CACHE, faces_per_mesh=4000):
    """Download (once) and decimate the URDF meshes. Returns {link: (vertices mm, faces)}."""
    import trimesh
    out_dir = os.path.join(cache, MESH_SHA[:7])
    os.makedirs(out_dir, exist_ok=True)
    meshes = {}
    for name in MESHES:
        npz = os.path.join(out_dir, f"{name}_{faces_per_mesh}.npz")
        if not os.path.exists(npz):
            stl = os.path.join(out_dir, f"{name}.STL")
            if not os.path.exists(stl):
                urllib.request.urlretrieve(MESH_URL.format(sha=MESH_SHA, name=name), stl)
            m = trimesh.load(stl, force="mesh")
            if len(m.faces) > faces_per_mesh:
                try:
                    m = m.simplify_quadric_decimation(face_count=faces_per_mesh)
                except Exception:  # fast_simplification missing: render the full mesh
                    pass
            np.savez(npz, v=np.asarray(m.vertices) * 1000.0, f=np.asarray(m.faces))
        d = np.load(npz)
        meshes[name] = (d["v"], d["f"])
    return meshes


TWIN_RGB = (95, 170, 230)  # light blue, so the twin never passes for the real (black) arm


def render(cam, meshes, q_deg, gripper_mm=0.0, image=None, rgb=TWIN_RGB, alpha=1.0, ss=2):
    """Draw the arm at q_deg into image (BGR, or a grey canvas). ss is supersampling."""
    T = link_poses(q_deg, gripper_mm)
    big = cam.scaled(cam.width * ss, cam.height * ss)
    R, t = big.R(), big.tvec
    polys, depth, shade = [], [], []
    up_cam = R @ np.array([0.0, 0.0, 1.0])  # world up, in the camera frame
    for name, (v, f) in meshes.items():
        vw = v @ T[name][:3, :3].T + T[name][:3, 3]
        vc = vw @ R.T + t
        tri = vc[f]  # F x 3 x 3, camera frame
        n = np.cross(tri[:, 1] - tri[:, 0], tri[:, 2] - tri[:, 0])
        nn = np.linalg.norm(n, axis=1)
        ok = nn > 1e-9
        n[ok] /= nn[ok, None]
        cen = tri.mean(1)
        facing = (n * cen).sum(1) < 0  # STL faces point outward; keep the ones facing us
        keep = ok & facing & (tri[:, :, 2].min(1) > 1.0)
        if not keep.any():
            continue
        uv = big.project(vw).reshape(-1, 2)[f[keep]]
        polys.append(uv)
        depth.append(cen[keep, 2])
        view = -cen[keep] / np.linalg.norm(cen[keep], axis=1, keepdims=True)
        lam = np.clip((n[keep] * view).sum(1), 0, 1)
        top = np.clip(n[keep] @ up_cam, 0, 1)
        shade.append(0.30 + 0.55 * lam + 0.25 * top)
    if image is None:
        canvas = np.full((big.height, big.width, 3), 235, np.uint8)
    else:
        canvas = cv2.resize(image, (big.width, big.height), interpolation=cv2.INTER_LINEAR)
    layer = canvas.copy()
    mask = np.zeros(canvas.shape[:2], np.uint8)
    if polys:
        polys, depth, shade = np.concatenate(polys), np.concatenate(depth), np.concatenate(shade)
        order = np.argsort(-depth)
        pts = np.round(polys[order] * 16).astype(np.int32)  # 4 bits of subpixel precision
        bgr = np.array(rgb[::-1], float)
        cols = np.clip(shade[order, None] * bgr, 0, 255).astype(np.uint8)
        for p, c in zip(pts, cols):
            cv2.fillConvexPoly(layer, p, c.tolist(), lineType=cv2.LINE_8, shift=4)
            cv2.fillConvexPoly(mask, p, 255, lineType=cv2.LINE_8, shift=4)
    a = (mask.astype(np.float32) / 255.0 * alpha)[..., None]
    out = (canvas * (1 - a) + layer * a).astype(np.uint8)
    return cv2.resize(out, (cam.width, cam.height), interpolation=cv2.INTER_AREA)


def draw_skeleton(img, cam, q_deg, color=(0, 220, 255), thick=2, label=None):
    """Projected FK skeleton (base, J2, J3, wrist, flange, fingertips) with joint dots."""
    kp = keypoints_3d(q_deg)
    uv = cam.project(np.array([kp[n] for n in SKELETON]))
    pts = np.round(uv).astype(int)
    for a, b in zip(pts[:-1], pts[1:]):
        cv2.line(img, tuple(a), tuple(b), color, thick, cv2.LINE_AA)
    for p in pts:
        cv2.circle(img, tuple(p), thick + 2, color, -1, cv2.LINE_AA)
    if label:
        put_text(img, label, tuple(pts[-1] + np.array([8, -8])), color)
    return dict(zip(SKELETON, uv))


def put_text(img, text, org, color=(255, 255, 255), scale=None, box=(0, 0, 0)):
    """Text on a filled box (OpenCV 5 widens glyphs with thickness, so no outline trick)."""
    scale = scale or max(0.45, img.shape[1] / 1600)
    th = max(1, int(round(scale * 2)))
    (w, h), base = cv2.getTextSize(text, cv2.FONT_HERSHEY_SIMPLEX, scale, th)
    x, y = int(org[0]), int(org[1])
    if box is not None:
        cv2.rectangle(img, (x - 3, y - h - 4), (x + w + 3, y + base + 2), box, -1)
    cv2.putText(img, text, (x, y), cv2.FONT_HERSHEY_SIMPLEX, scale, color, th, cv2.LINE_AA)


def draw_ground(img, cam, step=100, extent=(-400, 700, -500, 500), color=(200, 200, 200)):
    """Grid on the table plane (z = 0), every step mm."""
    x0, x1, y0, y1 = extent
    for x in range(x0, x1 + 1, step):
        uv = cam.project([[x, y0, 0], [x, y1, 0]])
        cv2.line(img, tuple(np.round(uv[0]).astype(int)), tuple(np.round(uv[1]).astype(int)),
                 color, 1, cv2.LINE_AA)
    for y in range(y0, y1 + 1, step):
        uv = cam.project([[x0, y, 0], [x1, y, 0]])
        cv2.line(img, tuple(np.round(uv[0]).astype(int)), tuple(np.round(uv[1]).astype(int)),
                 color, 1, cv2.LINE_AA)


def draw_camera_marker(img, view, cam, size=60, color=(40, 40, 200)):
    """The real camera as a small frustum, drawn in another (virtual) view."""
    C = cam.center()
    R = cam.R()
    corners = [C + R.T @ np.array([sx * 0.8, sy * 0.45, 1.0]) * size
               for sx, sy in ((-1, -1), (1, -1), (1, 1), (-1, 1))]
    uv = np.round(view.project(np.array([C] + corners))).astype(int)
    for k in range(1, 5):
        cv2.line(img, tuple(uv[0]), tuple(uv[k]), color, 2, cv2.LINE_AA)
        cv2.line(img, tuple(uv[k]), tuple(uv[1 + k % 4]), color, 2, cv2.LINE_AA)
    put_text(img, "camera", tuple(uv[0] + np.array([8, 20])), color)


def remove_arm(image, cam, meshes, q_deg, grow_px=None):
    """The photo with the arm (where the twin puts it at q_deg) painted out, for a backdrop."""
    mask = render_mask(cam, meshes, q_deg)
    grow_px = grow_px or max(3, cam.width // 120)
    mask = cv2.dilate(mask, np.ones((2 * grow_px + 1, 2 * grow_px + 1), np.uint8))
    return cv2.inpaint(image, mask, 5, cv2.INPAINT_TELEA)


def render_mask(cam, meshes, q_deg, gripper_mm=0.0):
    black = np.zeros((cam.height, cam.width, 3), np.uint8)
    img = render(cam, meshes, q_deg, gripper_mm, black, rgb=(255, 255, 255), ss=1)
    return (img.max(2) > 0).astype(np.uint8) * 255


def simulate(args):
    """Render the planned protocol (piper_camera_check.py --json) as the camera would see it,
    next to a three-quarter view, into an MP4 and a sped-up GIF."""
    import imageio.v2 as imageio
    import piper_camera_check as pcc

    plan = json.load(open(args.plan))
    segs = plan["segments"]
    samples = pcc.timeline(segs, hz=args.fps)
    cam_full = Camera.load(args.camera)
    meshes = load_meshes()
    pw, ph = args.panel
    x0, y0, w, h = args.crop
    cam = cam_full.cropped(x0, y0, w, h, pw, ph)
    photo = cv2.imread(args.background)
    photo = cv2.resize(photo, (cam_full.width, cam_full.height), interpolation=cv2.INTER_AREA)
    crop = cv2.resize(photo[y0:y0 + h, x0:x0 + w], (pw, ph), interpolation=cv2.INTER_AREA)
    backdrop = remove_arm(crop, cam, meshes, args.photo_joints)
    backdrop = cv2.addWeighted(backdrop, 0.55, np.full_like(backdrop, 255), 0.45, 0)
    view = virtual_camera(pw, ph, 46, (1100, -1250, 750), (0, -330, 150))
    ground = np.full((ph, pw, 3), 246, np.uint8)
    draw_ground(ground, view, extent=(-400, 700, -900, 500))
    draw_camera_marker(ground, view, cam_full)

    trail_cam, trail_view = [], []
    writer = imageio.get_writer(args.out, fps=args.fps, codec="libx264", quality=8,
                                macro_block_size=8)
    for k, (t, label, q) in enumerate(samples):
        left = render(cam, meshes, q, 0.0, backdrop.copy(), alpha=0.92)
        right = render(view, meshes, q, 0.0, ground.copy())
        tip = keypoints_3d(q)["tip"]
        trail_cam.append(cam.project([tip])[0])
        trail_view.append(view.project([tip])[0])
        for img, tr in ((left, trail_cam), (right, trail_view)):
            if len(tr) > 1:
                cv2.polylines(img, [np.round(np.array(tr[-400:])).astype(np.int32)], False,
                              (0, 140, 255), 2, cv2.LINE_AA)
        draw_skeleton(left, cam, q, thick=1)
        put_text(left, "camera view (calibrated from today's photo)", (10, 24))
        put_text(right, "three-quarter view", (10, 24), (40, 40, 40), box=(246, 246, 246))
        frame = np.hstack([left, right])
        bar = np.full((48, frame.shape[1], 3), 30, np.uint8)
        put_text(bar, f"DIGITAL TWIN, planned protocol (not run yet)   t = {t:5.1f} s   "
                      f"{label:9s}  joints " + " ".join(f"{v:6.1f}" for v in q), (10, 31),
                 (255, 255, 255), scale=0.62, box=None)
        frame = np.vstack([bar, frame])
        writer.append_data(frame[:, :, ::-1])
    writer.close()
    if args.gif:
        mp4_to_gif(args.out, args.gif, args.gif_speed, args.gif_width)
    print(f"{len(samples)} frames, {samples[-1][0]:.1f} s -> {args.out}"
          + (f", {args.gif}" if args.gif else ""))


def mp4_to_gif(mp4, gif, speed=2.0, width=1024, fps=10):
    """A small GIF for GitHub comments: sped up, one shared palette, only changed areas."""
    import subprocess
    import imageio_ffmpeg
    vf = (f"setpts=PTS/{speed},fps={fps},scale={width}:-2:flags=lanczos,split[a][b];"
          "[a]palettegen=max_colors=128:stats_mode=diff[p];"
          "[b][p]paletteuse=dither=bayer:bayer_scale=4:diff_mode=rectangle")
    subprocess.run([imageio_ffmpeg.get_ffmpeg_exe(), "-y", "-loglevel", "error", "-i", mp4,
                    "-vf", vf, "-loop", "0", gif], check=True)


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    r = sub.add_parser("render", help="one pose, optionally over a photo")
    r.add_argument("--camera", required=True, help="camera JSON (see Camera)")
    r.add_argument("--joints", required=True, help="six joint angles, deg, comma separated")
    r.add_argument("--gripper-mm", type=float, default=0.0)
    r.add_argument("--background", help="photo to draw over (resized to the camera's size)")
    r.add_argument("--alpha", type=float, default=0.6)
    r.add_argument("--out", required=True)
    s = sub.add_parser("simulate", help="the planned protocol as a video")
    s.add_argument("--plan", required=True, help="piper_camera_check.py --json output")
    s.add_argument("--camera", required=True)
    s.add_argument("--background", required=True, help="photo from the camera")
    s.add_argument("--photo-joints", type=lambda v: [float(x) for x in v.split(",")],
                   default=[3.99, -1.96, 2.15, 1.38, 23.34, 64.29],
                   help="where the arm is in the photo, to paint it out of the backdrop")
    s.add_argument("--crop", type=lambda v: [int(x) for x in v.split(",")],
                   default=[700, 1080, 2400, 1350], help="x0,y0,w,h of the camera image")
    s.add_argument("--panel", type=lambda v: [int(x) for x in v.split("x")], default=[768, 432])
    s.add_argument("--fps", type=float, default=20.0)
    s.add_argument("--out", required=True, help=".mp4")
    s.add_argument("--gif", help="also write a GIF")
    s.add_argument("--gif-speed", type=float, default=3.0)
    s.add_argument("--gif-width", type=int, default=1024)
    args = ap.parse_args()
    if args.cmd == "simulate":
        simulate(args)
        return
    cam = Camera.load(args.camera)
    q = [float(v) for v in args.joints.split(",")]
    bg = cv2.imread(args.background) if args.background else None
    if bg is not None:
        bg = cv2.resize(bg, (cam.width, cam.height), interpolation=cv2.INTER_AREA)
    img = render(cam, load_meshes(), q, args.gripper_mm, bg,
                 alpha=args.alpha if bg is not None else 1)
    draw_skeleton(img, cam, q)
    cv2.imwrite(args.out, img)


if __name__ == "__main__":
    main()
