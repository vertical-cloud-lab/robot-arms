# AprilTags

Sandbox for AprilTag detection and pose estimation in the PiPER cell, for example to locate
the arm, fixtures or labware from the fixed cameras on the camera Pis.

Add scripts, notes and results to this folder as the work progresses.

| File | What it is |
|---|---|
| `printer_apriltags.jpg` | mpzy's camera on the A1 mini, its four tags boxed: green decoded (tag36h11 ID 31), orange found but not decoded. |
| `apriltag_locations.jpg` | Recommended tag locations in the cell: fixed anchors (table, arm base, printer), the plate and gripper, and fixtures. |
| `tag_layout_sim.py` | Monte Carlo of how well a tag layout pins the plate's plane and the arm's base, for a pinhole model of mpzy's camera. Needs `numpy` and `opencv-python`. |

The [Digital Twin](../Digital%20Twin/) places the tag set from PR #77 in a simulated cell, and
`python run_sim.py --scenario camera_check` there renders mpzy's view and reports which tags
a detector finds and how well it locates them.

Started from [#76](https://github.com/vertical-cloud-lab/robot-arms/issues/76).
