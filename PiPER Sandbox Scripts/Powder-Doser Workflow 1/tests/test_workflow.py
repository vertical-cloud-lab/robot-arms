#!/usr/bin/env python3
"""Tests for Powder-Doser Workflow 1, with no arm, camera or Pi: the simulated arm
(Arm Control/fake_piper.py) and rendered AprilTag images (sim.py).

    python tests/test_workflow.py          # or: python -m pytest tests

The whole-session tests run in real time (the simulated arm moves at the real one's speed),
so the full set takes about 4 minutes.
"""
import csv
import math
import os
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
WF = os.path.dirname(HERE)
sys.path.insert(0, WF)

import numpy as np  # noqa: E402

import calibrate as C  # noqa: E402
import kinematics as K  # noqa: E402
import settings as S  # noqa: E402
import sim  # noqa: E402
import vision as V  # noqa: E402


# ---------------------------------------------------------------- kinematics
def test_ik_reaches_and_points_the_fingers():
    for target, yaw in [((313, -66, 60), -12.0), ((208, 97, 34), -5.0), ((300, 0, 200), 0.0),
                        ((166, 238, 34), 55.0)]:
        q = K.ik(target, yaw)
        assert math.dist(K.tcp(q), target) < 0.5, (target, K.tcp(q))
        assert abs(K.wrap90(K.finger_yaw(q) - yaw)) < 0.5
        assert S.J6_RANGE_DEG[0] <= q[5] <= S.J6_RANGE_DEG[1]
        assert q[3] == S.J4_DEG and q[4] <= S.J5_COMFORT_DEG + 1e-6
        _, _, pitch = K.reach_and_pitch(q)
        if target[2] < 70:
            assert pitch < -85, f"near the table the gripper should point straight down ({pitch})"


def test_j6_window_is_enforced():
    try:  # fingers along the reach (yaw 0 here) need J6 -25.7; turned 45 deg (yaw 45, the
        K.ik((300, 0, 60), 45.0)  # same line as -135) they need -70.7 or +109.3: both outside
    except K.IKError as e:
        assert "J6" in str(e)
    else:
        raise AssertionError("a J6 outside the window was accepted")


def test_keep_out_box_and_j1_range():
    q = K.ik((200, -250, 150), -50.0)  # over the A1 mini's corner, and J1 -51
    bad = " ".join(K.problems(q))
    assert "A1 mini" in bad and "J1_RANGE_DEG" in bad, bad
    q = K.ik((300, 0, 120), 0.0)
    assert K.problems(q) == []


def test_paths_are_continuous_and_straight():
    q = K.ik((313, -66, 154), -12.0)
    path = K.line(q, (313, -66, 154), (313, -66, 60), -12.0, -12.0)
    for q in path:
        p = K.tcp(q)
        assert abs(p[0] - 313) < 0.5 and abs(p[1] + 66) < 0.5


# ---------------------------------------------------------------- vision
def scene(holder, box, turns=None):
    tags = []
    for obj, layout, size in ((holder, S.HOLDER_TAGS, S.HOLDER_TAG_SIZE_MM),
                              (box, S.BOX_TAGS, S.BOX_TAG_SIZE_MM)):
        for i, p in layout.items():
            tags.append((i, size, V.flat_tag_pose(*obj.to_arm(p), obj.yaw + (turns or {}).get(i, 0))))
    return tags


def test_tags_locate_the_holder_and_box():
    cam = V.Camera.nominal()  # full resolution, as on mpzy
    holder = V.Found(313, -66.5, 60, 78, [], 0)
    box = V.Found(*S.SPOTS["2"][:2], 3, S.SPOTS["2"][2], [], 0)
    det = V.detect(V.render(cam, scene(holder, box, {202: 90, 203: 180})))  # two stuck on turned
    for truth, tags, size in ((holder, S.HOLDER_TAGS, S.HOLDER_TAG_SIZE_MM),
                              (box, S.BOX_TAGS, S.BOX_TAG_SIZE_MM)):
        f = V.locate(det, tags, size, cam)
        assert f is not None and len(f.tags) == 2
        assert math.hypot(f.x - truth.x, f.y - truth.y) < 2.0, f
        assert abs(f.z - truth.z) < 2.0 and abs(K.wrap180(f.yaw - truth.yaw)) < 0.5, f


def test_one_tag_needs_a_known_height():
    cam = V.Camera.nominal()
    holder = V.Found(313, -66.5, 60, 78, [], 0)
    only = [t for t in scene(holder, holder) if t[0] == 201]
    det = V.detect(V.render(cam, only))
    assert V.locate(det, S.HOLDER_TAGS, S.HOLDER_TAG_SIZE_MM, cam) is None
    f = V.locate(det, S.HOLDER_TAGS, S.HOLDER_TAG_SIZE_MM, cam, z=60.0)
    assert math.hypot(f.x - holder.x, f.y - holder.y) < 2.0, f


# ---------------------------------------------------------------- calibration
def test_calibration_recovers_the_camera():
    """calibrate.fit on simulated sightings of the card (with lens distortion and 0.2 px of
    noise): the camera's position comes back within a few mm."""
    true = V.Camera.nominal()
    true.dist = np.array([-0.04, 0.02, 0, 0, 0])
    cell = sim.SimCell(cal_tag=True)
    ready = K.UD.level([0, S.READY_LIFT_DEG, -S.READY_LIFT_DEG, S.J4_DEG, 24, S.PARK_J6_DEG])
    rng = np.random.default_rng(1)
    obs = []
    for q in C.poses(ready):
        F = C.flange_T(q)
        for i, T in cell.cal_tags_in_flange.items():
            pose = F @ T
            if np.dot(pose[:3, 2], true.cam_in_arm[:3, 3] - pose[:3, 3]) <= 0:
                continue  # that face looks away from the camera
            h = S.CAL_TAG_SIZE_MM / 2
            corners = [(pose @ np.array([u, v, 0, 1]))[:3] for u, v in ((-h, h), (h, h), (h, -h), (-h, -h))]
            obs.append((q, i, true.project(corners) + rng.normal(0, 0.2, (4, 2))))
    assert len(obs) >= 12
    guess = V.Camera.nominal()
    cam0, tags0 = C.first_guess(obs, S.CAL_TAG_SIZE_MM, guess)
    cam, tags, f, k1, k2, err = C.fit(obs, sorted(tags0), S.CAL_TAG_SIZE_MM, guess.size, cam0,
                                      tags0, guess.K[0, 0])
    assert np.sqrt(np.mean(err ** 2)) < 0.5
    assert np.linalg.norm(cam[:3, 3] - true.cam_in_arm[:3, 3]) < 5.0, cam[:3, 3]
    assert abs(f - true.K[0, 0]) < 15


# ---------------------------------------------------------------- the layout and whole sessions
def test_every_spot_has_a_safe_plan():
    import layout
    _, plans = layout.plan_all()
    for spot, (plan, _) in plans.items():
        assert not isinstance(plan, str), f"spot {spot}: {plan}"


def session(*extra, runs=1):
    d = tempfile.mkdtemp()
    p = subprocess.run([sys.executable, os.path.join(WF, "auger_test.py"), "--dry-run", "--go",
                        "--yes", "--results", d, "--runs", str(runs), *extra],
                       capture_output=True, text=True, timeout=900)
    rows = []
    if os.path.exists(os.path.join(d, "results.csv")):
        with open(os.path.join(d, "results.csv"), newline="") as f:
            rows = list(csv.DictReader(f))
    return p, rows, d


def test_session_two_runs_both_A():
    p, rows, d = session("--spot", "2", runs=2)
    assert p.returncode == 0, p.stdout[-2000:] + p.stderr[-2000:]
    assert [r["grade"] for r in rows] == ["A", "A"], [(r["grade"], r["why"]) for r in rows]
    assert "firmware limits back to J2 >= 0" in p.stdout  # parked and switched off
    r = subprocess.run([sys.executable, os.path.join(WF, "report.py"), "--results", d],
                       capture_output=True, text=True)
    assert r.returncode == 0 and "2/2 = 100%" in r.stdout, r.stdout + r.stderr


def test_no_auger_is_D_stuck_is_C_no_box_is_F():
    for extra, want in ((("--sim", "missing"), "D"), (("--sim", "stuck"), "C"),
                        (("--sim", "nobox"), "F")):
        p, rows, _ = session(*extra)
        assert p.returncode == 0, p.stdout[-2000:] + p.stderr[-2000:]
        assert [r["grade"] for r in rows] == [want], (extra, [(r["grade"], r["why"]) for r in rows])


if __name__ == "__main__":
    failed = 0
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and callable(fn):
            try:
                fn()
                print(f"PASS {name}", flush=True)
            except Exception as e:  # noqa: BLE001
                failed += 1
                print(f"FAIL {name}: {e!r}", flush=True)
    sys.exit(1 if failed else 0)
