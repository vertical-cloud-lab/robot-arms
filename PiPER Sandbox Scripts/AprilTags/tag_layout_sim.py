"""How well do AprilTags pin down the build plate's plane, or the arm's base? A rough Monte Carlo.

The camera is a pinhole model of mpzy's Camera Module 3 Wide at full resolution (2.75 mm lens,
1.4 um pixels, so f = 1964 px), with Gaussian noise on every tag corner and no lens distortion
or calibration error. Real errors will be larger. What carries over is the comparison between
layouts: how much a third or fourth tag buys, and why tags should be solved together.

    pip install numpy opencv-python
    python tag_layout_sim.py

"Solved together" means one solvePnP over every corner of every tag, with the tags' layout on
the plate known: the tags act as one big tag. "Each alone" means one pose per tag.
"""
import cv2
import numpy as np

F, W, H = 1964.0, 4608, 2592  # px
K = np.array([[F, 0, W / 2], [0, F, H / 2], [0, 0, 1]])
SIGMA = 0.5  # px of corner noise: small tags seen at a slant
TAG = 0.030  # m, side of the black square
N = 2000  # noisy frames per case
rng = np.random.default_rng(0)


def camera(dist, elev_deg):
    """Camera `dist` m from the origin, looking at it from `elev_deg` above the table."""
    e = np.radians(elev_deg)
    c = np.array([0, -dist * np.cos(e), dist * np.sin(e)])
    z = -c / np.linalg.norm(c)
    x = np.array([1.0, 0, 0])
    R = np.vstack([x, np.cross(z, x), z])  # table -> camera
    return R, -R @ c


def corners(x, y, z=0.0, s=TAG):
    h = s / 2
    return np.array([[x - h, y + h, z], [x + h, y + h, z], [x + h, y - h, z], [x - h, y - h, z]])


def project(P, R, t):
    p = P @ R.T + t
    return (p[:, :2] / p[:, 2:]) * F + [W / 2, H / 2]


def angle(R_est, R):
    """Rotation error in degrees, and the tilt error of the table's normal."""
    rot = np.degrees(np.linalg.norm(cv2.Rodrigues(R_est @ R.T)[0]))
    tilt = np.degrees(np.arccos(min(1.0, abs(R_est[:, 2] @ R[:, 2]))))
    return rot, tilt


def together(tags, R, t, s=TAG):
    """All corners of all tags in one solve. tags: (x, y, z) centres in the plate's frame."""
    obj = np.vstack([corners(*c, s=s) for c in tags])
    clean = project(obj, R, t)
    out = []
    for _ in range(N):
        img = clean + rng.normal(0, SIGMA, clean.shape)
        _, rv, tv = cv2.solvePnP(obj, img, K, None, flags=cv2.SOLVEPNP_SQPNP)
        _, rv, tv = cv2.solvePnP(obj, img, K, None, rv, tv, True, flags=cv2.SOLVEPNP_ITERATIVE)
        out.append(angle(cv2.Rodrigues(rv)[0], R))
    return np.array(out)


def each_alone(tags, R, t):
    """One pose per tag (what a detector reports), then a plane through the tag centres."""
    local = corners(0, 0)
    clean = [project(corners(*c), R, t) for c in tags]
    out = []
    for _ in range(N):
        centres, tilts = [], []
        for img0 in clean:
            img = img0 + rng.normal(0, SIGMA, img0.shape)
            _, rv, tv = cv2.solvePnP(local, img, K, None, flags=cv2.SOLVEPNP_IPPE_SQUARE)
            centres.append(tv.ravel())
            tilts.append(angle(cv2.Rodrigues(rv)[0], R)[1])
        if len(tags) == 1:
            out.append(tilts[0])
        else:
            pts = np.array(centres)
            n = np.linalg.svd(pts - pts.mean(0))[2][-1]
            out.append(np.degrees(np.arccos(min(1.0, abs(n @ R[:, 2])))))
    return np.array(out)


def row(name, tilt):
    p50, p95 = np.percentile(tilt, [50, 95])
    print(f"  {name:<44} {p50:6.2f} {p95:7.2f} {np.mean(tilt > 10):7.1%}")


if __name__ == "__main__":
    R, t = camera(1.0, 30)
    # plate frame: origin at the plate's centre, x right, y back; corner tags 150 mm apart
    FL, FR, BL, BR = (-0.075, -0.075, 0), (0.075, -0.075, 0), (-0.075, 0.075, 0), (0.075, 0.075, 0)
    BACK = (0.04, 0.075, 0)  # the back-edge tag as placed now, right of centre
    PRINTER = (0.135, 0.0, -0.010)  # on the printer beside the plate, 10 mm lower, offset known
    print("Plate 1.0 m from the camera, seen from 30 deg above")
    print(f"  {'tilt error of the plate, degrees':<44} {'median':>6} {'95th %':>7} {'>10 deg':>7}")
    row("1 tag", each_alone([FL], R, t))
    row("the 3 plate tags, each alone, plane fit", each_alone([FL, FR, BACK], R, t))
    row("the 3 plate tags solved together", together([FL, FR, BACK], R, t)[:, 1])
    row("4 corner tags solved together", together([FL, FR, BL, BR], R, t)[:, 1])
    row("front 2 together", together([FL, FR], R, t)[:, 1])
    row("front 2 + printer tag together", together([FL, FR, PRINTER], R, t)[:, 1])

    print("Arm base 1.0 m from the camera: rotation error, and what it does 0.5 m out")
    for name, tags, s in [("3 x 40 mm tags flush round the base", [(0, -0.09, 0), (-0.09, 0, 0), (0.09, 0, 0)], 0.04),
                          ("3 x 60 mm table tags ~80 cm apart", [(-0.4, -0.3, 0), (0.4, -0.3, 0), (0, 0.4, 0)], 0.06)]:
        rot = together(tags, R, t, s)[:, 0]
        p50, p95 = np.percentile(rot, [50, 95])
        print(f"  {name:<44} {p50:.2f} / {p95:.2f} deg -> "
              f"{np.radians(p50) * 500:.1f} / {np.radians(p95) * 500:.1f} mm")
