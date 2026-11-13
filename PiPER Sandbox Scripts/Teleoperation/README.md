# SO-101 leader → PiPER teleoperation

Drive the lab's AgileX PiPER from an SO-101 leader arm plugged into your own computer, with
live video from the HQ camera on the gripper
([#46](https://github.com/vertical-cloud-lab/robot-arms/issues/46),
[PR #47](https://github.com/vertical-cloud-lab/robot-arms/pull/47),
[#67](https://github.com/vertical-cloud-lab/robot-arms/issues/67)). Everything it needs is in
this folder and [`../Arm Control/`](../Arm%20Control/), so a clone of the repo is enough.

**Status (2026-11-06): not yet run on the real arm.** It has run against a simulated arm
only: the tests below, and `--dry-run` sessions on the arm Pi (mpzy) from CI.

## Quick start

On the computer the leader is plugged into (Windows, macOS or Linux, Python 3.8+):

```bash
git clone https://github.com/vertical-cloud-lab/robot-arms
cd "robot-arms/PiPER Sandbox Scripts/Teleoperation"
pip install -r requirements.txt
python teleop.py --check     # preflight: leader, packages, SSH, arm Pi, camera Pi. Moves nothing
python teleop.py --dry-run   # a whole session against a simulated arm on the Pi: no relay, no CAN
python teleop.py             # the real arm (see "Before a real run")
```

- **The first run asks** for the arm Pi's address and login, and the camera Pi's (leave it
  blank for no video). It saves them to `teleop.local.json` here, which git ignores. Edit or
  delete that file to change them; command-line options (`--host`, `--user`, `--port`,
  `--cam-host`, …) win over it.
- **The leader's port** defaults to `COM10`. Use `--port /dev/ttyACM0` on Linux, or
  `--port /dev/tty.usbmodem…` on a Mac.
- **Your computer needs SSH** to the arm Pi (`rpi-5-mpzy`, the one with the USB-CAN adapter and
  the relay) and, for video, to the gripper Pi (`rpi-5-76zj`, the HQ camera). Either join the
  lab tailnet and get a grant in
  [`tailscale-policy`](https://github.com/vertical-cloud-lab/tailscale-policy) (an admin
  adds it), or be on the lab network with the Pis' logins. Only SSH is used, so no other port
  has to be opened. Windows 10 and 11 include the `ssh` command. On the lab network, an SSH
  key (`ssh-copy-id`) saves typing a password each session.
- **Nothing needs installing on the Pis.** Each session copies `follower.py` and the
  shared files to `~/so101/` on the arm Pi and runs them in its existing `~/piper-venv`. The
  video comes from `rpicam-vid`, which ships with Raspberry Pi OS.
- **Leader calibration.** If LeRobot calibrated the leader, `teleop.py` uses the newest file in
  `~/.cache/huggingface/lerobot/calibration/teleoperators/so101_leader/` or `so_leader/` (or `--calib FILE`).
  That file, or `--gripper-range CLOSED,OPEN`, is also the only way the gripper gets mapped;
  without either, the PiPER's gripper is left alone.

## Before a real run

Drop `--dry-run` only when all of these hold:

- the workspace is clear, including the printer's travel;
- someone is at the E-stop and can see the whole arm;
- the arm is resting parked on its rest, by `Up_and_Down.py` or the last session.

Without `--dry-run`, the session powers the arm through the relay
(`arm_power.py run`). The relay switches off again only once the follower has parked the
arm.

## In a session

1. The arm rises off its rest to **READY**: J2 +20°, J3 −20°, the gripper level, J6 −52°.
2. Line the leader up with it. The window shows each joint's difference from the arm, and the
   video if a camera Pi is set. The video shows the camera's whole sensor: left to itself,
   `rpicam-vid` picked a mode that reads only the middle of it, and the arm left the frame as
   it rose. `--cam-mode auto` gives that choice back to `rpicam-vid`.
3. **Hold SPACE to move**; let go to stop. On Windows the key is read directly, so it works
   whichever window has focus; elsewhere SPACE toggles.
4. **Q** (or Esc), from any pose: the arm goes back to READY by itself,
   parks, and then the relay switches it off. The leader doesn't have to be near READY.
5. **A** (while holding, SPACE released): with the leader in the arm's pose, take the
   difference as the leader's offsets. They are saved to `align.json`, which git ignores.
6. **The gripper follows the leader's** (`--no-gripper` leaves it alone). It is switched on
   at READY, holding where it is, and the log says whether it stayed on; if it didn't, the
   session goes on without it. The start enables joints 1–6 one by one, not with
   `EnablePiper()` ("all motors"): every start that used it set the gripper closing and
   reopening to find its zero, the custom finger sleeves stalled it, and it switched itself
   off (2026-11-12). Powering on alone, and enabling only joints 1–6, left it still.
   `--ready-grip-mm` (a follower option, after `--`) opens it to a width at READY. Q opens it
   wide before parking. This gripper reads 45.6 mm with the sleeves touching and 108.6 mm
   fully open (moved by hand), not the stock 0–70 mm, so the leader's gripper maps onto
   `--grip-min-mm 46` to `--grip-max-mm 108`.

When the session ends, it prints its latency: the ping round trip, the newest command's age at
the Pi, the leader's read time and the video's frame timing.

## Latency

What the code does:

- **One SSH connection carries the commands**, as plain text lines. OpenSSH turns off Nagle
  (`TCP_NODELAY`) on it even without a terminal (checked with `strace`), so a command leaves
  as soon as it is written.
- **The leader is read and commands are sent on their own thread at 200 Hz.** Before this, a
  slow window or video frame held back the next command, because all three ran in one loop.
  On Windows the script also asks for 1 ms timers, since the default 15.6 ms tick stretches
  short sleeps and key polls (and, before Python 3.11, would hold the loop well under 200 Hz).
- **The Pi acts on each command as it arrives** instead of on the next tick of a fixed clock.
  The command's age at the Pi went from 4.8 ms to 0.5 ms in a local test. The speed and
  acceleration limits still hold, because the limiter steps by the time that actually passed.
- **One SYNC READ fetches all six leader servos.** A single lost reply no longer drops the
  leader to six separate reads for the rest of the session.
- **Video never queues.** MJPEG comes over SSH, and only the newest complete frame is decoded
  and shown. Each frame stands alone, so there's no decoder buffer to wait for.

Measured from CI to mpzy on 2026-11-06, with the follower on the simulated arm: the round trip
was 49 ms, the same as the bare `tailscale ping` (relayed through Tailscale's Denver server),
so the code added nothing measurable.

What you can do:

1. **Get a direct Tailscale connection.** Run `tailscale ping <arm Pi>`. "via DERP(den)" means
   relayed through Denver, which adds roughly 15–40 ms. A home router with UPnP, NAT-PMP or PCP
   switched on, or a UDP port forward to 41641 on your computer, usually makes it direct.
2. **Check the leader's read time** with `--check`. Above about 5 ms, the USB adapter is
   batching. On an FTDI adapter, set Device Manager → Ports → the port → Port Settings →
   Advanced → Latency Timer to 1 ms.
3. **Turn the video down on a slow link:** `--cam-size 640x360 --cam-quality 40`, or
   `--no-cam`.
4. **Raise the arm's own speed limits once a supervised session has proven the map and the
   limits.** The follower starts conservative: 45°/s, 360°/s², and the arm's capped mode at
   40 %. Pass larger values after `--`, for example
   `python teleop.py -- --max-deg-s 90 --speed 60` (the follower's maximums). AgileX's
   uncapped "high follow" mode (`0xAD`) is the next step after that. It isn't in the code
   yet, because a wrong sign in the joint map would then move the arm at full speed.
5. **The Pis' Wi-Fi power saving** caused an 82 ms worst case at one ping a second (#47).
   During a session, the 200 commands a second keep the radio awake. Turning it off on the arm
   Pi is a one-line change for a person with sudo there.

## What the Pi does (`follower.py`)

**Start**
- Refuses unless the arm is resting at home with its motors off.
- Then it does what `Up_and_Down.py` does, using its code: widen J2/J3's firmware limits to
  just past the rest, enable, level the wrist, and raise to READY.

**While following**
- Nothing moves until SPACE is held **and** the leader is within 10° of the arm on every joint.
- Targets are clamped to `--envelope`:
  - J1 ±150°, J2 0–180°, J3 −170–0°, J5 ±70°, J6 −53.9–179°: the ranges the arm was moved
    through by hand (`../Arm Control/joint_watch.py`, 2026-11-12), 1° in, within the limits
    its firmware reports (J6's are ±180°, not the SDK's documented ±120°). J6's low end is
    where its cable stopped it;
  - J4 stays where it started.
  - The window's **limit** row marks a joint the leader is asking to take past its range
    (MAX or MIN): the arm stops there, which can look like a freeze.
- Speed and acceleration are limited to 45°/s and 360°/s², in the capped
  `MotionCtrl_2(1, 1, 40, 0)` mode.
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
| `teleop.py` | your computer | **The main script.** Reads the leader, runs the session over SSH, shows the status window and video, `--check` preflight |
| `follower.py` | arm Pi | The follower above; `teleop.py` copies it to `~/so101/` each session |
| `requirements.txt` | your computer | `pyserial`, `numpy`, `opencv-python` |
| `analysis/` | anywhere | `joint_map.py`: the SO-101 and PiPER joint layouts and the nominal map (`joint_map.json`, which `teleop.py` reads) |
| `tests/test_dry_run.py` | anywhere | Snag, lost connection, Q from far from READY, refusal off the rest, pose match to engage, the gripper left alone without `--gripper` and following with it, a whole `teleop.py` session, the leader protocol on a simulated Feetech bus, the camera reader |
| [`../Arm Control/`](../Arm%20Control/) | arm Pi | Shared by every sandbox script: `Up_and_Down.py`, `arm_power.py` + `arm_home.json`, `joint_watch.py` (prints and saves the joints' ranges while the arm is moved by hand, listen-only), and `fake_piper.py` (the simulated arm) |

**Test without the arm or the leader:**
```bash
python tests/test_dry_run.py
python teleop.py --fake-leader --local --dry-run --auto 8
```

## The joint map (`analysis/`)

- **The joint the SO-101 lacks is J4, the forearm roll.** The PiPER is yaw, pitch, pitch,
  **roll (J4)**, pitch, roll; the SO-101 is yaw, pitch, pitch, pitch, roll.
- **With J4 held at 0°, the other five joints map one to one.** J5's axis is then parallel to
  J2 and J3, so the PiPER has the SO-101's layout.
- **The nominal map:** J1 = −pan, J2 = lift + 96.2°, J3 = elbow − 88.4°,
  J5 = wrist_flex − 2.8°, J6 = −roll. It comes from the SO-101 URDF that matches LeRobot's
  calibration, so align it on the real arms (the A key).
- **What J4 would add** is tilting the gripper out of the arm's vertical plane. With J4 held,
  the gripper can still point straight down, straight out along the arm, and anywhere
  between, and J6 still turns it about its own axis.

`joint_map.py` needs only `numpy` and `matplotlib`, and rewrites `joint_map.json` and
`joint_map.png`.

## Still to do

- [x] First supervised real-arm sessions (2026-11-12, from Windows over Tailscale): the arm
      and gripper followed the leader. Latency: SSH round trip 34 ms median (41 ms 95th
      percentile), newest command 36 ms old at the Pi, leader read 1.1 ms, video frames
      33 ms apart.

**Calibration still to fix.** These were worked around to get teleop running, not fixed:

- [ ] **Gripper zero and range.** With the custom finger sleeves on, the gripper reads
      45.6 mm closed (sleeves touching) and 108.6 mm fully open, not 0–70 mm. The leader maps
      onto that range through `--grip-min-mm 46` / `--grip-max-mm 108`, measured by hand once.
      Re-measure with `../Arm Control/joint_watch.py`, which shows the gripper live, whenever
      the sleeves change, or re-zero the gripper (`GripperCtrl(set_zero=0xAE)`) and go back
      to the stock range.
- [ ] **The gripper's zero-finding.** Enabling every motor (`EnablePiper()`, `EnableArm(7)`)
      sets the gripper closing and reopening to find its zero, which the sleeves stall, and
      it switches itself off. The scripts now enable joints 1–6 one by one and switch the
      gripper on separately at READY, which hasn't triggered it. Whether it can be made to
      home correctly with the sleeves on is open.
- [ ] **J6's range and park pose.** J6 turns −54.8° to +188° by hand (its cable stops it at
      −55°; the firmware allows ±180°), far from symmetric about 0. The park pose,
      `arm_home.json`'s J6 −95 to −45, now sits at the cable stop. Decide where J6's zero and
      park angle should be for the new camera and its cable, and update `arm_home.json`,
      `--park-j6-deg` and `--envelope` together. With the motors off, J6 rolls freely, so
      `arm_power.py off` refuses until it is rolled back to about −52°.
- [ ] **The leader-to-PiPER joint map.** The nominal map comes from the SO-101 URDF and is
      corrected per operator by the A key (`align.json`, not in git). The signs and offsets
      haven't been checked joint by joint against the real arm, and the leader's own LeRobot
      calibration is per computer.
- [ ] **The cell camera's aim.** The video now uses mpzy's whole sensor, but the arm still
      leaves the top of the frame when raised high: tilt or move the camera.
- [ ] Video from the gripper: the gripper Pi (76zj) has to be online, with nothing else
      holding its HQ camera. mpzy's own camera (the imx708 wide, which sees the cell) has
      streamed into sessions since 2026-11-12, once its livestream was stopped.
- [ ] Tailnet grants for the operator's computer to SSH to mpzy and 76zj.
- [ ] Close PR #47 once this merges (its code is here now). PR #60 adds its own copy of
      `arm_power.py` and `arm_home.json` at `PiPER Sandbox Scripts/`; keep one copy, in
      `Arm Control/`.
