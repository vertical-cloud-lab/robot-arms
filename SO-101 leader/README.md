# SO-101 leader

Teleoperate the lab's AgileX PiPER from an SO-101 leader arm
([#46](https://github.com/vertical-cloud-lab/robot-arms/issues/46),
[PR #47](https://github.com/vertical-cloud-lab/robot-arms/pull/47)).

**Not yet run on the real arm.** Everything below has run against a simulated arm only
(`tests/test_dry_run.py`, and `--dry-run` on the arm Pi).

## Running it

On the PC the leader is plugged into:

```bash
git clone https://github.com/vertical-cloud-lab/robot-arms
pip install -r "robot-arms/SO-101 leader/requirements.txt"
python "robot-arms/SO-101 leader/teleop.py" --port COM10 --host <arm Pi> --user <login> --dry-run
python "robot-arms/SO-101 leader/teleop.py" --port COM10 --host <arm Pi> --user <login>
```

- **The arm Pi** is the one with the USB-CAN adapter and the relay: `rpi-5-mpzy` since
  2026-10-30 (#54, PR #60).
- **Your PC needs SSH to it.** Either the tailnet, which takes an admin grant in
  [`tailscale-policy`](https://github.com/vertical-cloud-lab/tailscale-policy), or the lab
  network with its login. Everything goes over that one SSH connection, so no other port is
  needed.
- **`--dry-run` first.** It runs the same code on the Pi against a simulated arm: no relay, no
  CAN frames.
- **Without `--dry-run`, the script powers the arm.** It runs the follower through
  `arm_power.py run`, so the relay switches the arm on and only switches it off once the
  follower has parked it.

**Before a real run:**
- the workspace is clear, including the printer's travel;
- someone is at the E-stop;
- the arm is resting on its rest, parked by `Up_and_Down.py` or the last session.

### In a session

1. The arm rises off its rest to **READY**: J2 +20°, J3 −20°, the gripper level, J6 −52°.
2. Line the leader up with it. The window shows each joint's difference.
3. **Hold SPACE to move**; let go to stop.
4. **Q** (within 25° of READY) parks the arm, and then the relay switches it off.
5. **A** (while holding, SPACE released): with the leader in the arm's pose, take the
   difference as the leader's offsets. They are saved to `align.json`, which git ignores.

**Leader calibration.** `teleop.py` uses LeRobot's calibration file for the leader if it
finds one under `~/.cache/huggingface/lerobot/calibration/teleoperators/so101_leader/`, or
`--calib FILE`. That file is also the only way the gripper gets mapped, besides
`--gripper-range CLOSED,OPEN`. Without either, the PiPER's gripper is left alone.

## What the Pi does (`pi/follower.py`)

**Start**
- Refuses unless the arm is resting at home with its motors off.
- Then it does what `Up_and_Down.py` does, using its code (`pi/Up_and_Down.py` is mpzy's copy,
  sha256 `f89ee7f6…`): widen J2/J3's firmware limits to just past the rest, enable, level the
  wrist, and raise to READY.

**While following**
- Nothing moves until SPACE is held **and** the leader is within 10° of the arm on every joint.
- Targets are clamped to `--envelope`:
  - J1 ±60°, J2 0–100°, J3 −150–0°, J5 ±60°;
  - J6 −52–0°, because the gripper Pi's cables jammed at J6 −55° in #54;
  - J4 stays where it started.
- Speed and acceleration are limited to 45°/s and 360°/s², streamed at 100 Hz. The mode is the
  capped `MotionCtrl_2(1, 1, 40, 0)`, not the `0xAD` mode.
- The gripper's lowest point can't go below 40 mm while descending.
- **Snags stop the arm where it is:**
  - a joint over its current limit (A: 3, 7, 6, 2, 4.5, 1.5);
  - a joint more than 10° behind its setpoint.

  It stays stopped until SPACE is released and the leader is lined up again.
- **Holds:** SPACE released, or no fresh command for 0.15 s.

**End:** on Q, a closed connection, or 10 s without commands.
- It returns to READY at 12°/s, unless the straight way there dips below the floor.
- Then it goes down, lands, lowers the gripper and disables, as `Up_and_Down.py` does, and
  exits 0, so `arm_power.py` switches the relay off.
- Anything that goes wrong leaves the motors on, holding, and exits 1. The relay then stays on,
  because the PiPER has no brakes.

## Files

| File | Runs on | What |
|---|---|---|
| `teleop.py` | your PC | Reads the leader on `--port`, maps it, runs the session over SSH, shows status (OpenCV window) |
| `requirements.txt` | your PC | `pyserial`, `numpy`, `opencv-python` |
| `pi/follower.py` | arm Pi | The follower above; `teleop.py` copies it to `~/so101/` each session |
| `pi/Up_and_Down.py` | arm Pi | mpzy's `~/Up_and_Down.py` as of 2026-11-06, unchanged; the follower imports it |
| `pi/fake_piper.py` | anywhere | The simulated arm behind `--dry-run` and the tests |
| `tests/test_dry_run.py` | anywhere | Snag, lost connection, Q refused far from READY, refusal off the rest, pose-match to engage |
| `analysis/` | anywhere | `joint_map.py`: the SO-101 and PiPER joint layouts and the nominal map |

**Test without the arm or the leader:**
```bash
python "SO-101 leader/tests/test_dry_run.py"
python "SO-101 leader/teleop.py" --fake-leader --local --dry-run --auto 8
```

## `analysis/`

`joint_map.py` compares the two arms' kinematic chains. It needs only `numpy` and `matplotlib`,
and writes `joint_map.json` and `joint_map.png`. `teleop.py` reads its nominal map from
`joint_map.json`.

- **The joint the SO-101 lacks is J4, the forearm roll.**
  - The PiPER is yaw, pitch, pitch, **roll (J4)**, pitch, roll.
  - The SO-101 is yaw, pitch, pitch, pitch, roll.
- **With J4 held at 0°, the other five joints map one to one.** J5's axis is then parallel to
  J2 and J3, so the PiPER has the SO-101's layout.
- **The nominal map:** J1 = −pan, J2 = lift + 96.2°, J3 = elbow − 88.4°,
  J5 = wrist_flex − 2.8°, J6 = −roll. It is worked out from the SO-101 URDF that matches
  LeRobot's calibration, so align it on the real arms (the A key).
- **What J4 would add** is tilting the gripper out of the arm's vertical plane. With J4 held
  at 0°, the gripper can still point straight down, straight out along the arm, and anywhere
  between, and J6 still turns it about its own axis.
