# Arm Control

The files any sandbox script uses to power, move, park or simulate the PiPER. They run on the
arm Pi (`rpi-5-mpzy`, the one with the USB-CAN adapter and the relay), in its `~/piper-venv`.
[`../Teleoperation/teleop.py`](../Teleoperation/teleop.py) copies them to `~/so101/` on the Pi
at the start of each session, so nothing has to be installed there by hand.

| File | What it does |
|---|---|
| `arm_power.py` | Switches the arm's power with the IoT Relay II on GPIO17, and only cuts it once the arm is parked: all motors disabled, nothing moving, every joint inside `arm_home.json`. `arm_power.py run -- PROG …` powers on, runs PROG, and powers off only if PROG exits 0 with the arm parked. `status` and `check` are read-only. `can0` goes up with the relay and down after it (passwordless sudo for exactly those `ip link` commands, in `/etc/sudoers.d/arm-power-can`). From [#59 / PR #60](https://github.com/vertical-cloud-lab/robot-arms/pull/60). |
| `arm_home.json` | The home (parked) pose ranges `arm_power.py` checks. Edit this, not the script, when new parts change the rest pose, and update the Pi's `~/arm_home.json` to match. |
| `Up_and_Down.py` | Raises the arm off its rest, rolls the gripper Pi to the side, lowers, lands and disables, stopping on snags. Read-only unless `--go`; `--park --go` brings a raised arm home. `../Teleoperation/follower.py` reuses its moves and checks. This is mpzy's `~/Up_and_Down.py` as of 2026-11-06 (sha256 `f89ee7f6…`), except that it enables joints 1–6 one by one: `EnablePiper()` also enabled the gripper, which then closed onto its finger sleeves trying to find its zero (2026-11-12). |
| `joint_watch.py` | Prints the joints and gripper live while the arm is moved by hand (powered, motors off), then each joint's min and max, saved to `~/joint_watch_runs/`. Listen-only. |
| `fake_piper.py` | A simulated PiPER with the parts of `piper_sdk` the scripts use. `--dry-run` runs against it: no `piper_sdk`, no CAN frames, no relay. |
| `test_arm_power.py` | Runs `arm_power.py` against a simulated relay and arm. |

On the Pi, run every program that moves the arm through the power protocol:

```bash
~/piper-venv/bin/python ~/arm_power.py status                     # read-only
~/piper-venv/bin/python ~/arm_power.py run -- ~/piper-venv/bin/python ~/Up_and_Down.py --go
```

`teleop.py` uses the Pi's own `~/arm_power.py` when it has one, and says so if that differs
from the copy here. On 2026-11-06, `arm_power.py`, `arm_home.json` and `Up_and_Down.py` on mpzy
were byte-for-byte the files in this folder.

Test without the Pi: `python3 test_arm_power.py` (Linux or macOS).
