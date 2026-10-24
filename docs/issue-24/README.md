# Calibrating the PiPER with cameras, and fixturing them (issue #24)

Everything the #24 runs committed, gathered in PR #40 from the five branches they were pushed to.
The files are byte-for-byte copies, so this PR and those branches, #25's included, merge in either
order. Every run was simulation only: none moved the arm or printed anything.

| Folder or files | What it is | Scripts | From |
|---|---|---|---|
| `camera_2026-10-13.jpg` and `.json`, `plan_rest.json`, `twin_*`, [`selftest/`](selftest/) | The digital twin drawn through the taped side camera, the small-motion check protocol and its simulation, and a synthetic test of the comparison | [`piper_twin.py`](../../scripts/piper_twin.py), [`piper_camera_check.py`](../../scripts/piper_camera_check.py), [`piper_camera_compare.py`](../../scripts/piper_camera_compare.py) | [2026-10-13](https://github.com/vertical-cloud-lab/robot-arms/issues/24#issuecomment-6157460585), `claude/issue-24-20261013-2335` |
| [`camera-placement/`](camera-placement/), `camera_2026-10-14.jpg` | Where to add two fixed cameras: overhead, and past the table's right-hand end | [`piper_camera_placement.py`](../../scripts/piper_camera_placement.py) | [2026-10-14](https://github.com/vertical-cloud-lab/robot-arms/issues/24#issuecomment-6169873927), `claude/issue-24-20261014-1347` |
| [`rest-seat/`](rest-seat/), [`arm-check/`](arm-check/) | A printed seat that holds J1 at zero while the arm is parked, and the camera frame from #25's bus check | [`piper_rest_seat.py`](../../scripts/piper_rest_seat.py), [`piper_bus_check.py`](../../scripts/piper_bus_check.py) | [2026-10-14](https://github.com/vertical-cloud-lab/robot-arms/issues/24#issuecomment-6173269353) and [#25](https://github.com/vertical-cloud-lab/robot-arms/pull/25#issuecomment-6179239663), `claude/issue-24-20261014-1635` |
| [`camera-fixtures/`](camera-fixtures/) | Printable mounts (STL and STEP) for three cameras on corner posts, with install steps | [`piper_camera_fixtures.py`](../../scripts/piper_camera_fixtures.py) | [2026-10-21](https://github.com/vertical-cloud-lab/robot-arms/issues/24#issuecomment-6326304174), `claude/issue-24-20261021-2052` |
| [`camera-literature/`](camera-literature/) | The layout checked against the literature and four Edison answers, and re-scored for the 2 x 500 mm ribbon limit | [`piper_camera_cable_check.py`](../../scripts/piper_camera_cable_check.py) | [2026-10-21](https://github.com/vertical-cloud-lab/robot-arms/issues/24#issuecomment-6326320116), `claude/issue-24-20261021-2053` |

[`rest-seat/request_sketch_2026-10-14.jpg`](rest-seat/request_sketch_2026-10-14.jpg) is the photo
attached to the rest-seat request on #24. It marks where the seat goes and the cables A and B that
the rest-seat README refers to.

**The taped camera is gone.** It was removed on 2026-10-21. The first two rows, the camera model
`camera_2026-10-13.json` and CLAUDE.md's side-camera notes describe it as it was;
`camera-fixtures/` and `camera-literature/` plan the cameras without it.

## Checked from this branch (2026-10-23)

The scripts import each other from `scripts/`. In a fresh Python 3.12 venv with numpy,
opencv-python-headless, scipy, trimesh, imageio, imageio-ffmpeg, matplotlib, manifold3d,
networkx, lxml and cadquery 2.8.0:

- `piper_camera_check.py --plan-only` reproduced the 27 moves in `plan_rest.json` exactly.
- `piper_twin.py simulate` rendered the protocol. It imports `piper_camera_check.py`, which this
  branch didn't have before.
- `piper_camera_compare.py` ran end to end on a short synthetic run from
  `selftest/make_synthetic_run.py`. That script expects the repo at
  `/home/runner/work/robot-arms/robot-arms` and the still at `/tmp/pi24/still_full.jpg`; copy
  `camera_2026-10-13.jpg` there.
- `piper_rest_seat.py` rebuilt both seat STLs byte for byte, and the 3MF with the same mesh.
  `piper_camera_fixtures.py` rebuilt all ten fixture STLs byte for byte.
