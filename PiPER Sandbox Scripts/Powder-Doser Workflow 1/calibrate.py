#!/usr/bin/env python3
"""Measure where mpzy's camera is relative to the arm, and its lens, and save calibration.json.
auger_test.py needs it to turn the tags it sees into positions the arm can go to. Run it once,
and again whenever the camera is moved or bumped.

    python calibrate.py --dry-run --go --yes            # simulated arm and camera
    ~/piper-venv/bin/python ~/arm_power.py run -- ~/piper-venv/bin/python calibrate.py --go

How. The gripper holds a flat card with a tag on each face (settings.CAL_TAG_IDS, see the
README), hanging below the fingers. The arm takes it to about 24 poses spread over the work
area, turning it to face the camera, and the camera takes a still at each. Each pose gives
the card's corners in the image, and the arm's joint angles give where the gripper was
(forward kinematics). One least-squares fit over every corner then finds:
  - where the camera is and which way it looks (arm frame),
  - where each tag sits on the gripper (nobody has to measure the card),
  - the lens: focal length and two distortion terms (the principal point is left at the
    image centre).
It prints the fit's error in pixels and in mm. Take the holder and the box off the table first:
the card hangs about 80 mm below the fingertips.
"""
import argparse
import datetime as dt
import json
import math
import os
import sys
import time

import cv2
import numpy as np

import arm as A
import kinematics as K
import settings as S
import vision as V

HERE = os.path.dirname(os.path.abspath(__file__))


# ---------------------------------------------------------------- the poses
def poses(ready):
    """Joint angles for the calibration poses: three J1 angles across J1's range, two
    reaches, two heights, and two turns of the card about the camera-facing one."""
    lo, hi = S.J1_RANGE_DEG
    cam = S.CAMERA_GUESS_POSITION
    out = []
    for j1 in (lo + 8, (lo + hi) / 2, hi - 8):
        for r in (240.0, 330.0):
            for z in (140.0, 220.0):
                p = [r * math.cos(math.radians(j1)), r * math.sin(math.radians(j1)), z]
                facing = math.degrees(math.atan2(cam[1] - p[1], cam[0] - p[0]))
                for turn in (-15.0, 15.0):  # the card's face is across the fingers' line
                    try:
                        q = K.ik(p, facing + turn, out[-1] if out else None)
                        K.check_path(K.joint_line(out[-1] if out else ready, q), "to the pose")
                    except K.IKError:
                        continue
                    if all(K.tcp(x)[2] > 130 for x in K.joint_line(out[-1] if out else ready, q)):
                        out.append(q)
    return out


# ---------------------------------------------------------------- the fit
def rt_to_T(rvec, tvec):
    T = np.eye(4)
    T[:3, :3] = cv2.Rodrigues(np.asarray(rvec, float))[0]
    T[:3, 3] = tvec
    return T


def T_to_rt(T):
    return cv2.Rodrigues(T[:3, :3])[0].ravel(), T[:3, 3].copy()


def flange_T(q):
    R, p = K.UD.fk(q)
    T = np.eye(4)
    T[:3, :3], T[:3, 3] = np.array(R), p
    return T


def project(points_cam, f, k1, k2, cx, cy):
    """Pixels of camera-frame points: pinhole plus two radial terms (OpenCV's model)."""
    x, y = points_cam[:, 0] / points_cam[:, 2], points_cam[:, 1] / points_cam[:, 2]
    r2 = x * x + y * y
    d = 1 + k1 * r2 + k2 * r2 * r2
    return np.column_stack([f * x * d + cx, f * y * d + cy])


def fit(obs, ids, size, image_size, cam0, tags0, f0):
    """Least squares (Levenberg-Marquardt) over every corner of every observation.
    obs: list of (q, tag id, 4x2 corners). Returns (cam_in_arm, {id: tag_in_flange}, f, k1,
    k2, per-observation RMS px)."""
    cx, cy = image_size[0] / 2, image_size[1] / 2
    h = size / 2
    corners = np.array([[-h, h, 0, 1], [h, h, 0, 1], [h, -h, 0, 1], [-h, -h, 0, 1]], float).T
    flanges = [flange_T(q) for q, _, _ in obs]
    seen = np.concatenate([c for _, _, c in obs])

    def unpack(p):
        cam = rt_to_T(p[0:3], p[3:6])
        tags = {i: rt_to_T(p[6 + 6 * k:9 + 6 * k], p[9 + 6 * k:12 + 6 * k])
                for k, i in enumerate(ids)}
        f, k1, k2 = p[-3:]
        return cam, tags, f, k1, k2

    def residual(p):
        cam, tags, f, k1, k2 = unpack(p)
        arm_to_cam = np.linalg.inv(cam)
        pts = [(arm_to_cam @ F @ tags[i] @ corners)[:3].T for F, (_, i, _) in zip(flanges, obs)]
        r = (project(np.concatenate(pts), f, k1, k2, cx, cy) - seen).ravel()
        # A weak pull of the distortion terms toward 0 (1 px per 0.05 of k1, per 0.2 of k2):
        # the card covers only part of the image, where they can trade off against the rest.
        return np.concatenate([r, [k1 / 0.05, k2 / 0.2]])

    p = np.concatenate([*T_to_rt(cam0)] + [np.concatenate(T_to_rt(tags0[i])) for i in ids]
                       + [[f0, 0.0, 0.0]])
    steps = np.array([1e-6] * 3 + [1e-3] * 3 + ([1e-6] * 3 + [1e-3] * 3) * len(ids)
                     + [1e-2, 1e-6, 1e-6])
    lam, r = 1e-3, residual(p)
    for _ in range(100):
        J = np.column_stack([(residual(p + np.eye(len(p))[k] * steps[k]) - r) / steps[k]
                             for k in range(len(p))])
        A_ = J.T @ J
        g = J.T @ r
        step = np.linalg.solve(A_ + lam * np.diag(np.diag(A_) + 1e-12), -g)
        r_new = residual(p + step)
        if r_new @ r_new < r @ r:
            p, r, lam = p + step, r_new, lam / 3
            if np.max(np.abs(step / steps)) < 10:
                break
        else:
            lam *= 5
    cam, tags, f, k1, k2 = unpack(p)
    per_obs = np.sqrt((r[:-2].reshape(len(obs), 8) ** 2).mean(1) * 2)
    return cam, tags, float(f), float(k1), float(k2), per_obs


def first_guess(obs, size, camera):
    """The camera's pose from OpenCV's hand-eye calibration (eye-to-hand: the base-to-gripper
    transforms go in, the camera-to-base one comes out), then each tag's pose on the gripper
    averaged over its sightings."""
    by_id = {}
    for q, i, c in obs:
        by_id.setdefault(i, []).append((q, c))
    main = max(by_id, key=lambda i: len(by_id[i]))
    Rg, tg, Rt, tt = [], [], [], []
    for q, c in by_id[main]:
        F = np.linalg.inv(flange_T(q))  # base -> gripper
        T = np.linalg.inv(camera.cam_in_arm) @ camera.tag_in_arm(c, size, face_up=False)
        Rg.append(F[:3, :3])
        tg.append(F[:3, 3])
        Rt.append(T[:3, :3])
        tt.append(T[:3, 3])
    R, t = cv2.calibrateHandEye(Rg, tg, Rt, tt, method=cv2.CALIB_HAND_EYE_PARK)
    cam = np.eye(4)
    cam[:3, :3], cam[:3, 3] = R, t.ravel()
    tags = {}
    for i, sightings in by_id.items():
        Ts = [np.linalg.inv(flange_T(q)) @ cam @ np.linalg.inv(camera.cam_in_arm)
              @ camera.tag_in_arm(c, size, face_up=False) for q, c in sightings]
        U, _, Vt = np.linalg.svd(sum(T[:3, :3] for T in Ts))  # the mean rotation
        T = np.eye(4)
        T[:3, :3] = U @ Vt
        T[:3, 3] = np.mean([T_[:3, 3] for T_ in Ts], 0)
        tags[i] = T
    return cam, tags


# ---------------------------------------------------------------- the run
def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0],
                                 formatter_class=argparse.RawDescriptionHelpFormatter,
                                 epilog=__doc__.split("\n", 1)[1])
    ap.add_argument("--go", action="store_true", help="move the arm (without it: list the poses)")
    ap.add_argument("--yes", action="store_true", help="don't ask (--dry-run and tests)")
    ap.add_argument("--dry-run", action="store_true", help="simulated arm and camera")
    ap.add_argument("--out", default=os.path.join(HERE, S.CALIBRATION_FILE))
    ap.add_argument("--images", default=os.path.join(HERE, S.RESULTS_DIR, "calibration"))
    ap.add_argument("--can", default="can0")
    args = ap.parse_args()

    sim = None
    if args.dry_run:
        import sim as simulation
        sim = simulation.SimCell(box=False, auger="missing", cal_tag=True)
        sim.holder = None
        print("DRY RUN: simulated arm and camera")
    arm = A.connect(args.dry_run, sim, args.can)
    q0 = arm.joints()
    ready = A.UD.level([q0[0], S.READY_LIFT_DEG, -S.READY_LIFT_DEG, S.J4_DEG, q0[4], S.PARK_J6_DEG])
    plan = poses(ready)
    print(f"{len(plan)} calibration poses, the card's lowest point "
          f"{min(K.tcp(q)[2] for q in plan) - (S.FINGERTIP_MM - S.TCP_MM) - 80:.0f} mm up at the lowest")
    if not args.go:
        print("read-only (no --go): nothing was sent to the arm")
        return 0
    if len(plan) < 10:
        raise SystemExit("fewer than 10 poses fit inside J1's range and J6's window")
    camera = sim.camera if sim else (V.Camera.load(args.out) or V.Camera.nominal())
    os.makedirs(args.images, exist_ok=True)

    def ask(text):
        if args.yes:
            print(text + "(--yes)")
            return ""
        return input(text).strip()

    if ask("Holder and box off the table, workspace clear, someone at the E-stop? Enter = go, "
           "q = quit: ").lower().startswith("q"):
        return 0
    obs, rc = [], 1
    try:
        arm.start()
        if not sim:
            arm.gripper_to(S.GRIPPER_MAX_READING_MM)
            ask("Put the card in the gripper (tags below the fingers), hold it, Enter: ")
            arm.gripper_to(S.GRIPPER_CLOSED_READING_MM)
        for n, q in enumerate(plan, 1):
            why = arm.go(q, f"pose {n}/{len(plan)}")
            if why:
                raise A.ArmError(why[1])
            time.sleep(0.5)  # let it settle
            path = os.path.join(args.images, f"pose{n:02d}.jpg")
            image = sim.capture(path) if sim else V.capture(path)
            det = V.detect(image)
            q_now = arm.joints()
            for i in S.CAL_TAG_IDS:
                if i in det:
                    obs.append((q_now, i, det[i]))
            print(f"  saw {[i for i in S.CAL_TAG_IDS if i in det] or 'no card tag'}", flush=True)
        why = arm.go(arm.ready, "back to READY")
        if why:
            raise A.ArmError(why[1])
        if not sim:
            ask("Hold the card, Enter to open the gripper: ")
            arm.gripper_to(S.GRIPPER_MAX_READING_MM)
            ask("Card out? Enter: ")
        arm.park()
        rc = 0
    except A.ArmError as e:
        print(f"STOPPED: {e}", flush=True)
        if arm.enabled:
            arm.hold()
        return 1
    finally:
        if sim:
            arm.piper.close()

    poses_seen = len({tuple(np.round(q, 3)) for q, _, _ in obs})
    print(f"the card was seen in {poses_seen} of {len(plan)} poses")
    if poses_seen < 8:
        raise SystemExit("too few sightings to calibrate: is the card facing the camera, and "
                         "are its tags CAL_TAG_IDS at CAL_TAG_SIZE_MM?")
    cam0, tags0 = first_guess(obs, S.CAL_TAG_SIZE_MM, camera)
    ids = sorted(tags0)
    cam, tags, f, k1, k2, err = fit(obs, ids, S.CAL_TAG_SIZE_MM, camera.size, cam0, tags0,
                                    camera.K[0, 0])
    dist_mm = [np.linalg.norm((np.linalg.inv(cam) @ flange_T(q) @ tags[i])[:3, 3])
               for q, i, _ in obs]
    mm = err * np.array(dist_mm) / f  # a pixel at that distance, in mm
    print(f"fit: RMS {np.sqrt(np.mean(err ** 2)):.2f} px (worst pose {err.max():.2f} px), about "
          f"{np.median(mm):.2f} mm median, {mm.max():.2f} mm worst at the card")
    print(f"camera at ({cam[0, 3]:.0f}, {cam[1, 3]:.0f}, {cam[2, 3]:.0f}) mm in the arm frame, "
          f"f = {f:.0f} px, k1 = {k1:.4f}, k2 = {k2:.4f}")
    w, h = camera.size
    out = {
        "what": "mpzy's camera relative to the PiPER's base (calibrate.py)",
        "date_utc": dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "image_size": [w, h],
        "K": [[f, 0, w / 2], [0, f, h / 2], [0, 0, 1]],
        "dist": [k1, k2, 0, 0, 0],
        "cam_in_arm": np.round(cam, 6).tolist(),
        "tag_in_flange": {str(i): np.round(tags[i], 6).tolist() for i in ids},
        "rms_px": round(float(np.sqrt(np.mean(err ** 2))), 3),
        "median_mm": round(float(np.median(mm)), 3),
        "poses": poses_seen,
        "lens_position": S.CAMERA_LENS_POSITION,
        "dry_run": bool(sim),
    }
    with open(args.out, "w") as fh:
        json.dump(out, fh, indent=1)
    print(f"saved {args.out}")
    return rc


if __name__ == "__main__":
    sys.exit(main())
