# robot-arms

6-DOF robot arm work at the Vertical Cloud Lab @ BYU: the AgileX PiPER cell, its wrist
cameras and mounts, the enclosure, and the reliability campaign.

This was split out of [vertical-cloud-lab/byu-vcl](https://github.com/vertical-cloud-lab/byu-vcl)
on 2026-10-09. The arm issues were transferred here, so their old byu-vcl links redirect.
The open pull requests were re-created here from the same branches, and the full commit
history for that work stays on the original branches in byu-vcl.

## PiPER sandbox

- [`PiPER Sandbox Scripts/Teleoperation/`](PiPER%20Sandbox%20Scripts/Teleoperation/):
  drive the PiPER from an SO-101 leader arm on your own computer, with live video. Clone,
  `pip install -r requirements.txt`, `python teleop.py`.
- [`PiPER Sandbox Scripts/Arm Control/`](PiPER%20Sandbox%20Scripts/Arm%20Control/): the
  shared files that power, move, park and simulate the arm (`arm_power.py`,
  `Up_and_Down.py`, `fake_piper.py`).
