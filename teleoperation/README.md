# SO-101 leader → PiPER teleoperation

One place to find the SO-101 leader / AgileX PiPER teleoperation work
([#67](https://github.com/vertical-cloud-lab/robot-arms/issues/67)). The code itself is still on
open branches; this page says where each piece is and how they fit together.

**Status (2026-11-06): not yet run on the real arm.** Everything has run against a simulated
arm only (`--dry-run` and `tests/test_dry_run.py`).

## Pieces

| Piece | Where | What it does |
| --- | --- | --- |
| `teleop.py` | [PR #47](https://github.com/vertical-cloud-lab/robot-arms/pull/47), `SO-101 leader/` | Runs on the PC the leader is plugged into. Reads the SO-101 over serial, shows each joint's difference from the arm, and streams commands over one SSH connection to the arm Pi. |
| `pi/follower.py` | PR #47, `SO-101 leader/pi/` | Runs on the arm Pi. Raises the PiPER off its rest to READY, follows the leader inside a joint envelope with speed, current and floor limits, then parks and disables. |
| `pi/fake_piper.py` | PR #47 | Simulated arm used by `--dry-run` and the tests. |
| `analysis/joint_map.*` | PR #47 | SO-101 → PiPER joint mapping and its plot. |
| `arm_power.py` | [#59](https://github.com/vertical-cloud-lab/robot-arms/issues/59) branch | Switches the arm on through the IoT relay, and off only once it is parked. `teleop.py` runs the follower through it on real runs. |
| `Up_and_Down.py` | [`PiPER Sandbox Scripts/`](../PiPER%20Sandbox%20Scripts/Up_and_Down.py) | Reference rise/land sequence that `follower.py` reuses. |

The arm Pi is the one with the USB-CAN adapter and the relay (`rpi-5-mpzy` since 2026-10-30,
#54 / PR #60).

## Running it

```bash
git clone https://github.com/vertical-cloud-lab/robot-arms
cd robot-arms && git checkout claude/issue-46-20261027-0036   # until PR #47 merges
pip install -r "SO-101 leader/requirements.txt"
python "SO-101 leader/teleop.py" --port COM10 --host <arm Pi> --user <login> --dry-run
```

Drop `--dry-run` only when the workspace is clear, someone is at the E-stop, and the arm is
resting parked. Without it the script powers the arm through the relay.

In a session: the arm rises to READY; line the leader up; **hold SPACE to move**, release to
stop; **Q** near READY parks it and powers it off; **A** saves leader offsets to `align.json`.

Your PC needs SSH to the arm Pi (tailnet grant in
[`tailscale-policy`](https://github.com/vertical-cloud-lab/tailscale-policy), or the lab LAN).

## To consolidate

- [ ] Merge PR #47 (SO-101 leader code) and the #59 `arm_power.py` work into `main`.
- [ ] First supervised real-arm run; record latency and any snags here.
- [ ] Move this page next to the code once it lands.
