# SO-101 leader

Files for using an SO-101 leader arm to teleoperate the AgileX PiPER
([#46](https://github.com/vertical-cloud-lab/robot-arms/issues/46)).

Nothing here talks to an arm yet. The plan and its open questions are in
[PR #47](https://github.com/vertical-cloud-lab/robot-arms/pull/47).

## `analysis/`

`joint_map.py` compares the two arms' kinematic chains. It needs only `numpy` and `matplotlib`,
and writes `joint_map.json` and `joint_map.png`:

- The PiPER is yaw, pitch, pitch, **roll (J4)**, pitch, roll. The SO-101 is yaw, pitch, pitch,
  pitch, roll. The joint the SO-101 lacks is J4, the forearm roll.
- With J4 held at 0°, J5 is parallel to J2 and J3, so the PiPER has the SO-101's layout and the
  other five joints map one to one. The nominal map is J1 = −pan, J2 = lift + 96.2°,
  J3 = elbow − 88.4°, J5 = wrist_flex − 2.8°, J6 = −roll. It is worked out from the SO-101 URDF
  that matches LeRobot's calibration, so check the offsets and signs on the real arms first.
- What J4 adds is tilting the gripper out of the arm's vertical plane. With J4 held at 0°, the
  gripper can still point straight down, straight out along the arm and anywhere between, and
  J6 still turns it about its own axis.
