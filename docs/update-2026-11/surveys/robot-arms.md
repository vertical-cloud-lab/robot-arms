# vertical-cloud-lab/robot-arms: where the AgileX PiPER project stands on 2026-11-28

Survey of every issue and PR in [vertical-cloud-lab/robot-arms](https://github.com/vertical-cloud-lab/robot-arms) (44 issues, 46 PRs, 77 branches), the files on `main` at [41a21f8](https://github.com/vertical-cloud-lab/robot-arms/tree/41a21f8), and the unmerged branches, read on 2026-11-28 (comments up to ~09:50 UTC). Issue #1's own thread is deliberately not summarized. Conventions: times UTC unless marked; people by GitHub handle (sgbaird = PI; jss265 = main operator and WRTG 316 author; chris-policky, claytonblodgett = team members); Raspberry Pis by tailnet tag (**eufi** = `rpi-5-eufi`, named "the arm Pi" in CLAUDE.md; **mpzy** = `rpi-5-mpzy`; **76zj** = `rpi-5-76zj`). "REAL ARM" = commands reached the PiPER; "SIM" = simulation or fake arm only. Most technical text in the threads was written by `@claude` runs at a person's request; I attribute ideas to the person who asked.

## Ten things that matter most

1. **The arm has done very little physically, and nothing since 2026-11-14.** Real-arm work: tape-roll picks and shelf places (2026-10-09 → 10-16; 6 of 10 executed grasps succeeded across changing code), up/down/park cycles (10-09, 10-15, 10-30, 11-03), relay power tests (11-03, 11-06), and the first SO-101-leader teleop sessions (11-12 → 11-14). It has never gripped a vial, a carrier or an auger ([hardware check, 2026-11-27](https://github.com/vertical-cloud-lab/robot-arms/blob/c8b3408/docs/protocol/hardware-and-safety-check.md)). The last session ended in a J4 over-current fault, and the relay then stayed on for ~11.5 days ([#86](https://github.com/vertical-cloud-lab/robot-arms/issues/86#issuecomment-7174991697)).
2. **The vision hardware is down.** Of 4 installed cameras only mpzy's fixed front camera works. The wrist Pi (76zj, HQ + Camera Module 3 Wide) has been offline since 2026-11-11 and eufi (back camera) since 2026-11-06; on 11-28 neither answered even on the lab LAN ([PR #81](https://github.com/vertical-cloud-lab/robot-arms/pull/81#issuecomment-7236436886)). No camera has an intrinsic or hand–eye calibration on hardware. The only on-hardware tag test found 25 mm tags readable at ~1 m and 10 mm tags not readable (0 of 48) ([PR #40](https://github.com/vertical-cloud-lab/robot-arms/pull/40#issuecomment-6869819000)).
3. **The flagship study is a preregistration that is ready to register, but nothing on the bench exists.** The CubXL loading campaign (#21; [PR #89](https://github.com/vertical-cloud-lab/robot-arms/pull/89) + branch `claude/issue-21-20261127-2050`) is an OSF Preregistration, split in two registrations: carrier and vial loading, open loop vs wrist-camera AprilTag correction, ≥300 loads per cell, a 21-level capture envelope, ISO 9283-style RP. It totals 5,760 transfers and ~660 human resets, with power analysis and analysis code done. "None of the gates below is met yet": the dock, carriers and inserts are CAD only, there is no harness, no correction code and no metrology fixture. Realistic dates are registration 2027-01-29 and first counted block 2027-03-05.
4. **The team's stated semester priority differs from the PI's paper.** jss265 (2026-10-26): "Priority number 1 is the to automate the removal and replacement of augers from the powder-doser" ([#42](https://github.com/vertical-cloud-lab/robot-arms/issues/42)). The auger work is a CAD/print study (PR #44), a MuJoCo twin (PR #77) and a simulated test harness (PR #83). No auger has been touched by the arm, and the clip pull-out force (estimated 12–40 N, against ~15 N available at the flange) has never been measured. The protocol flags arm sharing as an open decision (HW10).
5. **The wrist is the binding hardware constraint.** The wrist Pi's cable jammed J6 at −55° (16 A), hits J2 at home, and limits J6 to about a 90° window. The wrist supply is marginal: 1.1–1.5 A measured while streaming, and 4.78 V modelled at the Pi through the planned 27 W supply + 2 m extension, against the Pi's 4.63 V under-voltage threshold. As of 11-28 the recommendation is a 12 V supply plus a Pololu D36V28F5 step-down ($48.85, nothing bought) ([PR #41](https://github.com/vertical-cloud-lab/robot-arms/pull/41#issuecomment-7237025252)).
6. **Safety is mostly on paper.** A POWERTEC 71970 magnetic-switch E-stop has been on the arm's supply since ≤2026-10-26 but has never been tested. The IoT Relay II power protocol works, but a reboot of mpzy cuts power mid-move and the arm has no brakes. The hazard analysis and SOP (PR #23) have never been reviewed or signed; a 2026-11-28 addendum adds motion monitoring and says unattended runs are "no for now".
7. **Measured numbers are scarce and mostly incidental.** These include hand-measured joint ranges (J1 ±150°, J2 0–180°, J3 −170–0°, J5 ±70°, J6 −53.9…179°), gripper span 45.6–108.6 mm with sleeves, grip-effort overshoot (1.0 N·m commanded → 4.9–7.2 N·m peaks), J1 reading jumps of multiples of ~7.95° on enable, a 15.2° J1 re-zero on 11-14, and teleop latency of 34 ms SSH RTT median. **No repeatability, MTBI or success-rate data exist.**
8. **New directions in November are mostly simulation or agentic.** They are SO-101 teleop (working on the real arm), a MuJoCo digital twin with AprilTag-layout and auger-swap scenarios (PR #77), Apple AMP1 agentic manipulation reproduced on CaP-Gym and a simulated PiPER (PR #87, extended on 11-28 to A1-mini print removal, auger swap and atomizer charging), AprilTag cubes, a livestream with on-device face blurring, and printer tending (#86).
9. **The WRTG 316 proposal (jss265) reframes the lab's question as test selection.** It asks which published tests show whether a low-cost arm can serve as an "automated manual manipulator" (one arm working a lab's stations and recalibrating at each from a calibration square). A Claude-drafted thesis on an unmerged branch reads: "Neither price nor datasheet repeatability can tell a lab whether an arm is good enough for an SDL". 11 sources were selected (DOIs in §g). The paper is due 2026-12-01.
10. **Almost nothing is merged.** On `main` there are only the arm-control and teleop scripts, the install guide, the PiPER STEP and the WRTG files. Everything else (enclosure, wrist mount, tape pick, safety, calibration, livestream, digital twin, auger work, AMP1, preregistration) sits on open PRs or bare branches. `main`'s CLAUDE.md still says eufi drives the arm.


## (a) Hardware as built, and its status

### a1. The arm

- **AgileX PiPER (6-DOF), on loan, not bought.** sgbaird reported on 2026-09-18 that a colleague "agreed to loan us the PiPER robot arm" ([#1](https://github.com/vertical-cloud-lab/robot-arms/issues/1#issuecomment-6089391974)), and confirmed on 2026-09-26 that it is the PiPER, not the PiPER-X ([#1](https://github.com/vertical-cloud-lab/robot-arms/issues/1#issuecomment-6089392232)). The loan matters for the campaign, which needs the lender to agree to ~6,000 transfers and ~750 power cycles (gate HW9, "Not asked") ([bench-readiness.md](https://github.com/vertical-cloud-lab/robot-arms/blob/c8b3408/docs/protocol/bench-readiness.md)). The price quoted for an equivalent unit is $1,999 + ~$250 gripper from AgileX and $2,950–3,990 from US resellers ([#3](https://github.com/vertical-cloud-lab/robot-arms/issues/3#issuecomment-6089391861)), or $2,499–2,799 new in the imported procurement guide ([PR #12](https://github.com/vertical-cloud-lab/robot-arms/pull/12)).
- **Vendor figures, none measured here:** 1.5 kg payload *including* the 500 g gripper (PiPER manual, [#42](https://github.com/vertical-cloud-lab/robot-arms/issues/42#issuecomment-6408947353)), which leaves ~1.0 kg near the base and ~0.5 kg at the derated reach with the gripper on; 626 mm reach (reseller); 0.1 mm repeatability; 4.2 kg arm; ≤120 W. The wrist offers only 24 V + CAN, with no USB ([#3](https://github.com/vertical-cloud-lab/robot-arms/issues/3#issuecomment-6089391861)), and the J6 XT30 port is rated "24V, current: 2A MAX" ([PR #44](https://github.com/vertical-cloud-lab/robot-arms/pull/44#issuecomment-6592170922)).
- **Firmware S-V1.8-1.** Collision-protection level read as `[1, 1, 1, 1, 1, 1]` (factory default, least sensitive "on") by a query-only script on 2026-10-09 ([PR #16](https://github.com/vertical-cloud-lab/robot-arms/pull/16#issuecomment-6091071751)). Two later runs say it has never been read: the 2026-11-27 hardware check and the 2026-11-28 safety update, which also warns that AgileX's own "read" demo first sets all joints to 0 ([PR #23](https://github.com/vertical-cloud-lab/robot-arms/pull/23#issuecomment-7237213210)). Both missed PR #16's reading, and it should be re-read on the current setup. **No brakes:** a disabled or tripped joint goes limp and a raised arm drops ([PR #16](https://github.com/vertical-cloud-lab/robot-arms/pull/16#issuecomment-6091071751); AgileX manual §8 quoted in [#18](https://github.com/vertical-cloud-lab/robot-arms/issues/18#issuecomment-6091246658)).
- **Joint envelope, measured by hand on 2026-11-12** with the listen-only `joint_watch.py`, and used 1° inside as the teleop limits: J1 ±150°, J2 0–180°, J3 −170–0°, J5 ±70°, J6 −53.9…179°. J6 physically turns from −54.8° (cable stop) to +188°. The firmware reports a J6 cap of ±180°, not the SDK docstring's ±120° ([PR #73](https://github.com/vertical-cloud-lab/robot-arms/pull/73)). **J1 was re-zeroed on 2026-11-14** (read 15.2°, then 0.0°, base centred by eye), so earlier J1 readings, including the ±150° range, may be offset by up to 15.2° (`main` [CLAUDE.md](https://github.com/vertical-cloud-lab/robot-arms/blob/41a21f8/CLAUDE.md); commit [d36efc8](https://github.com/vertical-cloud-lab/robot-arms/commit/d36efc8)).
- **Kinematic constraints found so far:**
  - The gripper can point straight down only below ~0.10 m above the base, because J5 stops at ±70° ([byu-vcl README](https://github.com/vertical-cloud-lab/byu-vcl/blob/f784f6b/robot-arm/cubxl-vial-handling/README.md)). Picks therefore tilt the tool 10–25° ([#19](https://github.com/vertical-cloud-lab/robot-arms/issues/19); [PR #77](https://github.com/vertical-cloud-lab/robot-arms/pull/77#issuecomment-6872965077)).
  - IK has no solution for a carrier lying across the arm's line ([byu-vcl README](https://github.com/vertical-cloud-lab/byu-vcl/blob/f784f6b/robot-arm/cubxl-vial-handling/README.md)).
  - J1 is limited to −20°…+60° to clear the A1 mini on the table ([PR #83](https://github.com/vertical-cloud-lab/robot-arms/pull/83)).
  - J6 is held to about a 90° window by the wrist-Pi wiring: −52…0° in the 11-06 follower, −52…+38° in PR #83 ([PR #47](https://github.com/vertical-cloud-lab/robot-arms/pull/47#issuecomment-6674437590)).
  - The rest pose with the motors off is about `[4, −2, 2, 1, 23, 64]`°, not zero. Because J2 = 0 and J3 = 0 are firmware limits, disabling at "home" used to drop the wrist ~10 mm, until a landing step was added on 2026-10-30 ([#19](https://github.com/vertical-cloud-lab/robot-arms/issues/19); [#54](https://github.com/vertical-cloud-lab/robot-arms/issues/54#issuecomment-6514656728)).
- **Gripper.** The AgileX parallel gripper is fitted with printed PLA "finger sleeves". It reads 45.6 mm with the sleeves touching and 108.6 mm fully open, so it is probably the 0–100 mm version (inference; never confirmed). Its zero-finding stalls on the sleeves, so motor 7 is never enabled through `EnablePiper()`/`EnableArm(7)`. Instead, joints 1–6 are enabled one by one ([PR #73](https://github.com/vertical-cloud-lab/robot-arms/pull/73)). Grip effort overshoots badly: 1.0 N·m commanded gave peaks of 4.9–7.2 N·m, and at 7.21 N·m the gripper motor overheated and released a roll on 2026-10-16 ([PR #20](https://github.com/vertical-cloud-lab/robot-arms/pull/20#issuecomment-6205733011); A2 trace check).

### a2. Controller, power chain, relay and E-stop

- **Which Pi drives the arm.**
  - **Until 2026-10-30, eufi** (Pi 5, 1 GB) drove the arm through a gs_usb/candleLight USB-CAN adapter, with `can0` at 1 Mbit/s brought up by hand, `piper_sdk` 0.6.2, and no ROS or LeRobot ([#15](https://github.com/vertical-cloud-lab/robot-arms/issues/15), [PR #16](https://github.com/vertical-cloud-lab/robot-arms/pull/16)).
  - **Since 2026-10-30, mpzy** (Pi 5, 1 GB; 990 MB RAM, ~374 MB free while it also runs the livestream) has held the CAN adapter ([#54](https://github.com/vertical-cloud-lab/robot-arms/issues/54#issuecomment-6514058123)), and since 2026-11-03 it has also switched the arm's supply ([PR #60](https://github.com/vertical-cloud-lab/robot-arms/pull/60#issuecomment-6592765858)). `main`'s CLAUDE.md still names eufi as the arm Pi ([hardware check, row 1](https://github.com/vertical-cloud-lab/robot-arms/blob/c8b3408/docs/protocol/hardware-and-safety-check.md)).
- **Relay.** A Digital Loggers IoT Relay II ($36.25, ranked first of four, approved by sgbaird on 2026-10-26; [#43](https://github.com/vertical-cloud-lab/robot-arms/issues/43#issuecomment-6409869724)) is driven from mpzy's GPIO17 (header pin 11) with ground on pin 9 ([#59](https://github.com/vertical-cloud-lab/robot-arms/issues/59#issuecomment-6592478476)). The protocol is `arm_power.py run -- PROG`: power the arm on, run the program, and switch off only if the program exits 0 *and* the arm's CAN feedback shows all six motors disabled, nothing moving, and every joint inside `arm_home.json` ([Arm Control README](https://github.com/vertical-cloud-lab/robot-arms/blob/41a21f8/PiPER%20Sandbox%20Scripts/Arm%20Control/README.md)). Since 2026-11-12, `can0` comes up with the relay and goes down after it, through a narrow sudoers rule on mpzy ([PR #73](https://github.com/vertical-cloud-lab/robot-arms/pull/73)). The relay does not latch, so a reboot or crash of mpzy cuts the arm's power mid-move ([PR #60](https://github.com/vertical-cloud-lab/robot-arms/pull/60#issuecomment-6592765858)).
- **E-stop.** A POWERTEC 71970 (120 V / 18 A magnetic switch with a latching mushroom button and anti-restart; $49.99; "not a certified safety E-stop") was recommended on 2026-10-09/10 ([#18](https://github.com/vertical-cloud-lab/robot-arms/issues/18#issuecomment-6092117783)). It was installed on the front right of the table by 2026-10-26 ([PR #9 photo comment](https://github.com/vertical-cloud-lab/robot-arms/pull/9#issuecomment-6409452390)). **It has never been tested:** the E-stop step of the relay test was not run because nobody was at the arm ([PR #60](https://github.com/vertical-cloud-lab/robot-arms/pull/60#issuecomment-6675357204)), and the 2026-11-27 check found "No recorded test". Whether it sits before or after the relay is not recorded ([hardware check, row 3](https://github.com/vertical-cloud-lab/robot-arms/blob/c8b3408/docs/protocol/hardware-and-safety-check.md)).
- **State on 2026-11-27/28:** mpzy up 16 days, CAN adapter present, `can0` down, relay off since a forced off on 2026-11-25 21:23 UTC ([#86](https://github.com/vertical-cloud-lab/robot-arms/issues/86#issuecomment-7174991697); [hardware check](https://github.com/vertical-cloud-lab/robot-arms/blob/c8b3408/docs/protocol/hardware-and-safety-check.md)).

### a3. SO-101 leader/follower

- jss265 owns a Hugging Face SO-101 leader and follower pair ([PR #47](https://github.com/vertical-cloud-lab/robot-arms/pull/47#issuecomment-6430891965), 2026-10-27). **The leader (on COM10 of jss265's Windows PC) drives the PiPER**; the SO-101 follower is not part of the PiPER setup. The SO-101 lacks the PiPER's J4 (forearm roll). With J4 held at 0°, the other five joints and the gripper map one to one, with agreement to 0.01° over 300 random poses ([PR #47](https://github.com/vertical-cloud-lab/robot-arms/pull/47#issuecomment-6430896968)). Since 2026-11-13, keys 1/2 jog J4 at 10°/s within ±90°, and each leader joint's calibrated range is scaled onto the arm's measured range ([d36efc8](https://github.com/vertical-cloud-lab/robot-arms/commit/d36efc8); [Teleoperation README](https://github.com/vertical-cloud-lab/robot-arms/blob/41a21f8/PiPER%20Sandbox%20Scripts/Teleoperation/README.md)). The WRTG framing treats the SO-101 (~$200) as a second low-cost arm to test ([edison/README.md](https://github.com/vertical-cloud-lab/robot-arms/blob/41a21f8/docs/wrtg-316/edison/README.md)).

### a4. Cameras and camera Pis

| Camera | Pi | Mount | Status (2026-11-28) |
|---|---|---|---|
| Camera Module 3 Wide, "taped side camera" (the only camera used for the October tape picks) | eufi | Taped to the table ~0.78 m from the base | **Removed 2026-10-21** ([#24](https://github.com/vertical-cloud-lab/robot-arms/issues/24#issuecomment-6326297579)) |
| Camera Module 3 Wide, front cam | mpzy | Front-left post, looking into the cell (sees "none of the lab") | **Live**: public stream since 2026-11-20 ([#61](https://github.com/vertical-cloud-lab/robot-arms/issues/61#issuecomment-7043250595)). Lent to teleop and PR #83 by the unmerged PR #81 mechanism |
| Camera Module 3 Wide, back cam | eufi | Back-right post (lab corner masked) | **Offline since 2026-11-06.** The Pi's power light turned red when jss265 fitted a homemade ribbon for an overhead camera ([PR #40](https://github.com/vertical-cloud-lab/robot-arms/pull/40#issuecomment-6843948205)) |
| Gripper Camera Module 3 Wide + HQ camera (IMX477, 6 mm CS lens, 55 × 43°) | 76zj (Pi 5, 8 GB) | Wrist mount from PR #10 | **Offline since 2026-11-11 20:47** ([PR #81](https://github.com/vertical-cloud-lab/robot-arms/pull/81#issuecomment-7236436886)). The HQ lens was "completely out of focus" on 11-05 ([#61](https://github.com/vertical-cloud-lab/robot-arms/issues/61#issuecomment-6646212844)); it cannot focus at ~60 mm (minimum ~0.2 m) ([PR #44](https://github.com/vertical-cloud-lab/robot-arms/pull/44#issuecomment-6426892475)) |
| Overhead camera | (eufi, planned) | 1.2 m post/boom designed ([#24](https://github.com/vertical-cloud-lab/robot-arms/issues/24#issuecomment-6326304174)) | **Never installed** (waiting on longer cables; the ribbon attempt shorted eufi) |

- **No calibration exists on hardware.** The fixed cameras' JSON files "are nominal CAD poses, not a calibration" ([#24](https://github.com/vertical-cloud-lab/robot-arms/issues/24#issuecomment-6326304174)). The only fits ever made to the arm were of the removed taped camera (A3 notes; numbers in §c).
- **Pi history.**
  - 76zj was offline 10-30 → 11-04 (a weak phone charger at 4.91 V, then a fresh SD card), then streamed from 11-05, then dropped again on 11-11.
  - eufi was offline from 11-06.
  - On 11-28, probes from mpzy at their last LAN addresses got "no ping, no ARP reply, no `tcp:22`", so both look powered off or disconnected ([PR #81](https://github.com/vertical-cloud-lab/robot-arms/pull/81#issuecomment-7236436886)).
  - The fixed cameras most likely sit on PR #9's printed ¾ in PVC clamp heads (printed 2026-10-26/28; [#45](https://github.com/vertical-cloud-lab/robot-arms/issues/45#issuecomment-6429988827), [#52](https://github.com/vertical-cloud-lab/robot-arms/issues/52#issuecomment-6486591949)). Their installed positions have not been measured (A3 notes).

### a5. Enclosure, table, shelf, printer

- **As built** (chris-policky, [#38](https://github.com/vertical-cloud-lab/robot-arms/issues/38), 2026-10-22): a 48 in cube of ¾ in Sch 40 PVC with 8 Charlotte side-outlet elbows and a canvas drop cloth on 8 spring clamps. The base rails are screwed into a 48 × 48 × ¾ in plywood base that the arm is bolted to. Clear height is 48.50 in, with ~13.5 in of headroom above the arm's ~35 in reach. **Cost $120.30.** The enclosure was apparently taken down for a table change on 2026-10-26 ("not in photo but ready to assemble", [PR #9](https://github.com/vertical-cloud-lab/robot-arms/pull/9#issuecomment-6409452390)), so whether the walls are up now is unverified. Designed but not built: Claude's 1283 × 1352 × 1098 mm dome (~$220), a raised hutch and an overhead camera bar (A1 notes).
- **Table contents (2026-10-26):** wooden legs, the E-stop front right, a power strip along the left side, and the **Bambu A1 mini ("Thumbelina") inside the cell, front right** ([PR #9](https://github.com/vertical-cloud-lab/robot-arms/pull/9#issuecomment-6409452390)). There is also a plywood pick-up shelf, a perforated "black shelf" plate, and a tool rack. PR #9's pocketed shelf is an unmerged design ([hardware check, row 14](https://github.com/vertical-cloud-lab/robot-arms/blob/c8b3408/docs/protocol/hardware-and-safety-check.md)). **No CubXL is in or near the cell** (row 12). A high-voltage atomizer transformer stands near the cell, under a secondhand "nothing within 7.5 in" (190 mm) rule that has never been measured ([#22](https://github.com/vertical-cloud-lab/robot-arms/issues/22#issuecomment-6103303798)).

### a6. Wrist camera mount and its power and cable problem

- **Mount** ([PR #10](https://github.com/vertical-cloud-lab/robot-arms/pull/10), open; CadQuery bracket + pod + carrier for a Pi 5 8 GB, HQ camera with 6 mm lens, and a Camera Module 3 Wide): printed in PLA on the A1 mini on 10-08 and 10-13, with pod and bracket reprints on 10-26, 10-28 and 10-29. Three physical fit failures forced CAD fixes: the HQ housing, the CM3 Wide square housing (the CAD had used Camera Module 2 numbers), and the lens-aperture thumbscrew. The cameras were installed by 2026-10-30 ([#54](https://github.com/vertical-cloud-lab/robot-arms/issues/54)). The recommended PAHT-CF version was never printed (A1 notes).
- **Power.**
  - Streaming both cameras drew 1.1–1.5 A (1.3 A mean) on 2026-10-24. The 8 GB board was then on a supply with no USB-PD (under-voltage flagged, 4.67–4.82 V while streaming) ([PR #41](https://github.com/vertical-cloud-lab/robot-arms/pull/41)).
  - Plan A was the official 27 W supply plus a 2 m AINOPE 240 W USB-C extension ($8.99; 6 ordered on ME 13562 and shared with the CubXL and atomizer, [comment](https://github.com/vertical-cloud-lab/robot-arms/pull/41#issuecomment-6388978965)), giving 4.78 V at 1.5 A, 4.67 V at 2.0 A, and 4.57 V at 2.5 A (low).
  - A 90° USB-C adapter and a coupler ($18.98, ME 13640) were ordered on 2026-11-05 ([#66](https://github.com/vertical-cloud-lab/robot-arms/issues/66#issuecomment-6647149651)). Whether they were fitted is unverified.
  - On 2026-11-28 the answer to sgbaird was "For streaming, probably. For a busy Pi, no.", with a recommendation of 12 V + Pololu D36V28F5 (4.93–4.96 V at 1.5–2.5 A) ([PR #41](https://github.com/vertical-cloud-lab/robot-arms/pull/41#issuecomment-7237025252)).
  - An alternative studied in PR #44 is to power the Pi from J6's 24 V/2 A XT30 through a D36V28F5 buck ("≈95 % confident the port has the capacity... ≈80 % confident it will run reliably 24/7", [PR #44](https://github.com/vertical-cloud-lab/robot-arms/pull/44#issuecomment-6592170922)). It has not been built.
- **Cable.** On 2026-10-30 jss265 reported that the wrist Pi's cord "will hit the J2 motor if I were to let the arm drop" ([#54](https://github.com/vertical-cloud-lab/robot-arms/issues/54)). The first roll toward J6 = −90° jammed at −55.0°, with current going from 0.1 to 16 A in 0.35 s ([#54](https://github.com/vertical-cloud-lab/robot-arms/issues/54#issuecomment-6514063980)). On one drop "the camera screws scratched the J2 housing" ([#54](https://github.com/vertical-cloud-lab/robot-arms/issues/54#issuecomment-6515341211)). Since then the park angle is J6 −52°, at the cable stop, and J6 is restricted to a ~90° window. The 12 V lead "up the arm" in the 11-28 proposal still has to be routed and strain-relieved.

### a7. Fingers, sleeves and end effectors

- **Printed and on the gripper:** PR #44's "Alternative A" parts in black PLA on the A1 mini: two-shell sleeves, a tilt-lock slider, a guide, and a finger fixture for the powder doser (printed 2026-10-30, with a main shell reprinted on 11-03; [#53](https://github.com/vertical-cloud-lab/robot-arms/issues/53#issuecomment-6511324753), [#55](https://github.com/vertical-cloud-lab/robot-arms/issues/55#issuecomment-6524897460)). That these are the sleeves now fitted is likely but unconfirmed (A5 notes). Claude's recommended Strategy 1 (a two-servo custom tool, ~0.62 kg) was never built.
- **For the CubXL campaign (CAD only):** PR 272's finger inserts (90° V-blocks with a rib, 67 g) with 1.5 mm Shore 30–50A silicone pads. They would replace the auger sleeves, and every swap is a configuration change ([PROTOCOL.md §4](https://github.com/vertical-cloud-lab/robot-arms/blob/c8b3408/docs/protocol/PROTOCOL.md)).


## (b) Software that exists, and what has actually run on the real arm

### b1. On `main` (41a21f8)

- **`PiPER Sandbox Scripts/Arm Control/`** ([README](https://github.com/vertical-cloud-lab/robot-arms/blob/41a21f8/PiPER%20Sandbox%20Scripts/Arm%20Control/README.md)), arriving via [PR #68](https://github.com/vertical-cloud-lab/robot-arms/pull/68) (2026-11-06) and [PR #73](https://github.com/vertical-cloud-lab/robot-arms/pull/73) (2026-11-12/13):
  - `arm_power.py` (relay protocol `status | check | on | off [--force] | run -- PROG`) with `arm_home.json` (park ranges; J6 −95…−45°);
  - `Up_and_Down.py`, a 702-line rewrite from the #54 work: level the wrist, raise, roll J6 to −52°, cycle, land 0.4° above rest, lower the gripper by current, disable. It has current and lag snag stops and widens/restores the J2/J3 firmware limits;
  - `joint_watch.py` (listen-only range logger);
  - `fake_piper.py` (simulated `piper_sdk`);
  - `test_arm_power.py` (32/32 passing on mpzy).
- **`PiPER Sandbox Scripts/Teleoperation/`** ([README](https://github.com/vertical-cloud-lab/robot-arms/blob/41a21f8/PiPER%20Sandbox%20Scripts/Teleoperation/README.md)):
  - `teleop.py` runs on the operator's PC. It reads the leader at 200 Hz on its own thread over one SSH connection, shows MJPEG video, and supports `--check`, `--dry-run` and `--record` (camera.mp4/window.mp4 rendered after the session), plus a Ctrl+SPACE latch and the J4 jog.
  - `follower.py` runs on mpzy under `arm_power.py`. It enforces 45°/s and 360°/s² in capped mode at 40 %, a 5 mm floor, current snag limits of 3, 7, 6, 2, 4.5 and 1.5 A, a >10° lag stop, and a park within 10 s if the link drops.
  - `analysis/joint_map.py` and the tests: 12/12 dry-run tests pass after [d36efc8](https://github.com/vertical-cloud-lab/robot-arms/commit/d36efc8).
- **Docs and CAD:** `docs/PiPER Install Guide R1` (Windows/WSL2 + pyAgxArm; read-only; [PR #17](https://github.com/vertical-cloud-lab/robot-arms/pull/17)) and `CAD/PIPER.STEP`.
- **`docs/wrtg-316/`** (§g).
- **Infrastructure PRs merged (no arm code):**
  - CI joins the tailnet with a federated identity and SSHes to the Pis ([#31](https://github.com/vertical-cloud-lab/robot-arms/pull/31), [#32](https://github.com/vertical-cloud-lab/robot-arms/pull/32), [#34](https://github.com/vertical-cloud-lab/robot-arms/pull/34));
  - approval-gated `@claude-print` for the Bambu printers ([#27](https://github.com/vertical-cloud-lab/robot-arms/pull/27), [#48](https://github.com/vertical-cloud-lab/robot-arms/pull/48), [#51](https://github.com/vertical-cloud-lab/robot-arms/pull/51), [#58](https://github.com/vertical-cloud-lab/robot-arms/pull/58), [#74](https://github.com/vertical-cloud-lab/robot-arms/pull/74));
  - an upload-only YouTube token ([#26](https://github.com/vertical-cloud-lab/robot-arms/pull/26), [#78](https://github.com/vertical-cloud-lab/robot-arms/pull/78), [#79](https://github.com/vertical-cloud-lab/robot-arms/pull/79));
  - the Onshape browser login ([#70](https://github.com/vertical-cloud-lab/robot-arms/pull/70), [#71](https://github.com/vertical-cloud-lab/robot-arms/pull/71));
  - 6-hour jobs, a seat pool, and new-branch PRs ([#80](https://github.com/vertical-cloud-lab/robot-arms/pull/80), [#88](https://github.com/vertical-cloud-lab/robot-arms/pull/88), [#84](https://github.com/vertical-cloud-lab/robot-arms/pull/84)).

### b2. Unmerged code and documents (all open unless noted)

| Where | What | Ran on the real arm? |
|---|---|---|
| [PR #16](https://github.com/vertical-cloud-lab/robot-arms/pull/16), [PR #14](https://github.com/vertical-cloud-lab/robot-arms/pull/14) | `piper_up_down.py`, `piper_status.py`, eufi inventory | Yes (10-09) |
| [PR #20](https://github.com/vertical-cloud-lab/robot-arms/pull/20) (+ branch `claude/issue-30-20261015-2243`, no PR) | `piper_pick_tape.py` (954 / 966 lines, two diverging copies), `piper_seek_tape.py`, `piper_vision.py`, IK table, camera model | Yes (10-10 → 10-16) |
| [PR #29](https://github.com/vertical-cloud-lab/robot-arms/pull/29) | 212-line `Up_and_Down.py` (superseded on main) | Yes (10-15) |
| [PR #23](https://github.com/vertical-cloud-lab/robot-arms/pull/23) | `docs/safety/` hazard analysis (15 hazards, now H16), SOP, checklist; new 2026-11-28 `motion-monitoring.md` + `analysis/joint_currents.py` | Docs only |
| [PR #25](https://github.com/vertical-cloud-lab/robot-arms/pull/25), [PR #40](https://github.com/vertical-cloud-lab/robot-arms/pull/40) (both conflict with main) | Camera comparison tools, fixture CAD, AprilTag detectability simulation, hand–eye recipe, printed-tag check | Only stills and the 11-14 tag check |
| [PR #9](https://github.com/vertical-cloud-lab/robot-arms/pull/9), [PR #10](https://github.com/vertical-cloud-lab/robot-arms/pull/10), [PR #41](https://github.com/vertical-cloud-lab/robot-arms/pull/41) | Enclosure model, wrist mount CAD/BOM, wrist power study | Hardware printed and installed |
| [PR #44](https://github.com/vertical-cloud-lab/robot-arms/pull/44) | Auger-swap end-effector study (CadQuery, Onshape, STLs, GIFs; 6 design rounds) | No (parts printed) |
| [PR #60](https://github.com/vertical-cloud-lab/robot-arms/pull/60) (closed; code landed via #68) | Relay wiring docs and run records | Yes (11-03, 11-06) |
| [PR #47](https://github.com/vertical-cloud-lab/robot-arms/pull/47) (closed) | First teleop code (superseded by #68/#73) | Dry run only |
| [PR #77](https://github.com/vertical-cloud-lab/robot-arms/pull/77) | `AprilTags/` (tag layout sim, tag cubes for an 11-print H2D plate) and `Digital Twin/` (MuJoCo + kinematic engines; print-clearing and auger-swap scenarios; 14 tests) | SIM |
| [PR #81](https://github.com/vertical-cloud-lab/robot-arms/pull/81) | `livestream/` (`device.py`, face blur, camera lending to teleop) | Deployed on mpzy (camera only) |
| [PR #83](https://github.com/vertical-cloud-lab/robot-arms/pull/83) | Powder-Doser Workflow 1 (`auger_test.py`, `vision.py`, `calibrate.py`, `report.py`; 11 tests) | SIM |
| [PR #87](https://github.com/vertical-cloud-lab/robot-arms/pull/87) | `amp1/`: Apple AMP1 harness + MuJoCo PiPER (`piper_sim.py`), CaP-Gym runs | SIM |
| [PR #89](https://github.com/vertical-cloud-lab/robot-arms/pull/89) + branch `claude/issue-21-20261127-2050` | `docs/protocol/`: PROTOCOL.md v2, OSF answers, `prereg_stats.py`, `power.py`, `simulate_and_check.py` | Docs/analysis only |
| [PR #8](https://github.com/vertical-cloud-lab/robot-arms/pull/8), [PR #11](https://github.com/vertical-cloud-lab/robot-arms/pull/11), [PR #12](https://github.com/vertical-cloud-lab/robot-arms/pull/12) | Imported research docs: gripper/generative-CAD survey, glovebox integration, procurement guide | Docs only |

### b3. Real-arm run log (everything found)

| Date (UTC) | What ran | Outcome | Source |
|---|---|---|---|
| ~2026-10-01 | Wrist-button record/playback and AgileX's Windows ArmRobotUA software (team meeting) | "Got the robot arm operational!"; playback "can dent plywood" | [#6](https://github.com/vertical-cloud-lab/robot-arms/issues/6), [#7](https://github.com/vertical-cloud-lab/robot-arms/issues/7#issuecomment-6089393334) |
| 2026-10-09 22:53 | **First Claude-commanded motion**: `piper_up_down.py --go`, J2 +25°/J3 −25° at 20 % | 3/3 cycles, then 3/3 again filmed (peak J3 −1.94 A) | [PR #16](https://github.com/vertical-cloud-lab/robot-arms/pull/16#issuecomment-6090632198) |
| 2026-10-10 00:51–01:46 | Tape pick stages 1–3 | Hover and descend OK (bottom pose within 0.13° of plan). Stage-3 grasp **failed**: the gripper slammed 64.3→18.1 mm in ~0.1 s, peaked at 5.37 N·m, and the roll squeezed out | [#19](https://github.com/vertical-cloud-lab/robot-arms/issues/19#issuecomment-6091917164), [PR #20](https://github.com/vertical-cloud-lab/robot-arms/pull/20#issuecomment-6202757985) |
| 2026-10-15 21:45–22:57 | Stage-3 retries; PR #29 `Up_and_Down.py`; #30 tape to shelf (requested by claytonblodgett) | One miss, then **success** (27.4 mm grip, 1.04 N·m, lifted ~88 mm); Up_and_Down 3/3; #30 **success** after two buggy surveys (roll placed upright on the shelf at 390 mm, 52 s) | [PR #20](https://github.com/vertical-cloud-lab/robot-arms/pull/20#issuecomment-6203175976), [PR #29](https://github.com/vertical-cloud-lab/robot-arms/pull/29#issuecomment-6203503431), [#30](https://github.com/vertical-cloud-lab/robot-arms/issues/30#issuecomment-6203807072) |
| 2026-10-16 01:01–04:14 | Shelf places (front, off-plane, behind), shelf→start, camera-guided seek of a hidden roll | Front ✓ (5.83 N·m overshoot); off-plane **dropped** (7.21 N·m, gripper overheated and released); behind ✓; shelf→start ✓; seek run 2 **missed by ~65 mm** because J1's reading jumped +7.9° on enable; run 3 **refused** (J1 jumped −23.84°); run 4 ✓ (released at r 248 mm / 0.6° vs target 247 mm / 0°). jss265: "Putting this test to bed" | [PR #20](https://github.com/vertical-cloud-lab/robot-arms/pull/20#issuecomment-6206324136), [report](https://github.com/vertical-cloud-lab/robot-arms/pull/20#issuecomment-6207992243) |
| 2026-10-30 03:14–04:57 | #54 `Up_and_Down.py` with the wrist Pi fitted (CAN adapter now on mpzy) | Run 1: J6 **jammed at −55°** (16 A), backed out. Run 2: J6 to −52°, 1/3 cycles (J3 4.4 A > 4 A limit), drop ≤0.41°. Run 3: 3/3 cycles, but J3 dropped 1.55° and the camera screws scratched the J2 housing. Run 4: 1/1, drop J3 0.60°, "near silent drop" | [#54](https://github.com/vertical-cloud-lab/robot-arms/issues/54#issuecomment-6514063980), [run 2](https://github.com/vertical-cloud-lab/robot-arms/issues/54#issuecomment-6514656728), [runs 3–4](https://github.com/vertical-cloud-lab/robot-arms/issues/54#issuecomment-6515079421) |
| 2026-10-30 evening | Lab-o-ween demo (sgbaird) | Only the up/down cycle and live camera views were ready; no record of how it went | [#56](https://github.com/vertical-cloud-lab/robot-arms/issues/56#issuecomment-6534737800) |
| 2026-11-03 01:37–01:49 | Relay tests through `arm_power.py` | On → arm talks in 2.1 s; `off` correctly refused with J6 at −22.8°; two `run -- Up_and_Down.py` cycles each ended parked with the relay off (silent 1.4 s later) | [PR #60](https://github.com/vertical-cloud-lab/robot-arms/pull/60#issuecomment-6592765858) |
| 2026-11-06 02:39–02:59 | mpzy reboot test (relay on, arm disabled); E-stop watch | Reboot cut the arm's power and the relay stayed off after boot (back in 42 s) ✓. **E-stop test not done** (nobody at the arm) | [PR #60](https://github.com/vertical-cloud-lab/robot-arms/pull/60#issuecomment-6675357204) |
| 2026-11-12 (MST evening) → 11-14 05:58 | **First SO-101-leader teleop sessions** (jss265, from Windows over Tailscale) | "The arm and gripper followed the leader, and sessions parked and powered off cleanly"; several calibration issues worked around. First test video https://youtu.be/E3Q9NqakqIE. The last session (11-14 05:53–05:58) stopped on "J4 drew -2.4 A (limit 2)" with the arm holding J2 113°/J3 −69°; the relay stayed on until a forced off on 11-25 21:23 | [PR #73](https://github.com/vertical-cloud-lab/robot-arms/pull/73), [PR #47](https://github.com/vertical-cloud-lab/robot-arms/pull/47#issuecomment-6846329256), [#86](https://github.com/vertical-cloud-lab/robot-arms/issues/86#issuecomment-7174991697) |
| 2026-11-14 | J1 re-zero (motors disabled) | 15.2° → 0.0° | `main` [CLAUDE.md](https://github.com/vertical-cloud-lab/robot-arms/blob/41a21f8/CLAUDE.md) |
| since 2026-11-14 | — | **No arm motion recorded.** Read-only checks only (11-25, 11-27, 11-28) | [#86](https://github.com/vertical-cloud-lab/robot-arms/issues/86), [hardware check](https://github.com/vertical-cloud-lab/robot-arms/blob/c8b3408/docs/protocol/hardware-and-safety-check.md) |

Pattern: at least six "first try didn't move" starts in October (STANDBY or teach mode after a reset). Claude refused to move six times (no "workspace clear", or people visible), and people entered the workspace around enabled runs at least three times (A2 notes; e.g. [PR #20](https://github.com/vertical-cloud-lab/robot-arms/pull/20#issuecomment-6205611798)). All October tape-pick videos were uploaded **private** (e.g. https://www.youtube.com/watch?v=M5MEyZLKfgI).


## (c) Measured results so far

**What does not exist:** no ISO 9283 repeatability or accuracy measurement, no success-rate estimate under a fixed configuration, no MTBI or intervention log, no vial, carrier or auger handling, and no camera-to-arm calibration of any installed camera ([hardware check, rows 7, 9, 19](https://github.com/vertical-cloud-lab/robot-arms/blob/c8b3408/docs/protocol/hardware-and-safety-check.md)). Everything below is incidental to development runs.

### c1. Real-arm measurements

**Joint ranges, zeros and settling**
- Hand-measured ranges (2026-11-12): J1 ±150°, J2 0–180°, J3 −170–0°, J5 ±70°, J6 −53.9…179° (by hand −54.8° to +188°); firmware J6 cap ±180° ([PR #73](https://github.com/vertical-cloud-lab/robot-arms/pull/73)). The script limits used in October were J1 ±150, J2 0–180, J3 −170–0, J4 ±100, J5 ±70, J6 ±120° ([PR #20](https://github.com/vertical-cloud-lab/robot-arms/pull/20) script; A2 notes).
- J1 reading jumps on enable, with no motion: +7.89° and −23.84° (multiples of ~7.95°) on 2026-10-16. A grasp missed by ~65 mm because of one ([PR #20](https://github.com/vertical-cloud-lab/robot-arms/pull/20#issuecomment-6206324136)). J1 was re-zeroed by 15.2° on 2026-11-14 ([CLAUDE.md](https://github.com/vertical-cloud-lab/robot-arms/blob/41a21f8/CLAUDE.md)). External report cited: the start pose shifts "up to 1 cm" after power cycles (piper_sdk #39, via [#24](https://github.com/vertical-cloud-lab/robot-arms/issues/24#issuecomment-6170144450)).
- Drop at disable (rest is below the J2/J3 firmware zeros):
  - before the landing step: ~2° on J2/J3, ~10 mm at the wrist in ~50 ms ([#19](https://github.com/vertical-cloud-lab/robot-arms/issues/19));
  - with landing: J2 0.15° / J3 0.41° (run 2), J3 1.55° and J5 0.82° (run 3, hand-moved start), and J2 0.25° / J3 0.60° / J4 0.33° / J5 0.08° (run 4) on 2026-10-30 ([#54](https://github.com/vertical-cloud-lab/robot-arms/issues/54#issuecomment-6515079421));
  - in the relay runs: J2 0.76°/0.64° and J3 0.75°/0.86° on 2026-11-03 ([PR #60](https://github.com/vertical-cloud-lab/robot-arms/pull/60#issuecomment-6592765858)).
- J3 rest varies between power-offs: +2.4°, +0.7° (moved by hand), +1.8°, +2.1° ([#54](https://github.com/vertical-cloud-lab/robot-arms/issues/54#issuecomment-6515079421)). J3 read ~0.4° differently after a power cycle ([PR #60](https://github.com/vertical-cloud-lab/robot-arms/pull/60#issuecomment-6592765858)).
- Placement and tracking: the tape-pick descent bottom pose was within 0.13° of plan, with roll displacement < 1 mm (< 2 px) ([#19](https://github.com/vertical-cloud-lab/robot-arms/issues/19#issuecomment-6091917164)). The camera-guided seek released at r 248 mm / 0.6° against a target of 247 mm / 0°, with fingertips at 83 mm against 81 planned ([PR #20](https://github.com/vertical-cloud-lab/robot-arms/pull/20#issuecomment-6207992243)). On 10-09 the real fingertips sat ~10–15 mm higher than modelled (the 150 mm TCP is a photo estimate; A2 notes).

**Motion, timing and currents**
- MOVE J speed is ~1.67°/s per speed percent (33.4°/s at 20 %); the joints are not synchronized ([PR #47](https://github.com/vertical-cloud-lab/robot-arms/pull/47#issuecomment-6430896968); A2 notes). Up_and_Down's raise of J2 +20°/J3 −20° lifts the wrist 94 mm and moves it 30 mm forward, in ~3 s each way at a 10°/s peak ([#54](https://github.com/vertical-cloud-lab/robot-arms/issues/54#issuecomment-6513508655)). PR #29's J2 +25°/J3 −25° lifts it 116 mm (+43 mm out) ([#28](https://github.com/vertical-cloud-lab/robot-arms/issues/28#issuecomment-6203158688)).
- Currents:
  - the J6 jam went 0.1 → 16 A in 0.35 s; the new per-joint limit (J6 1.5 A) "would have stopped the jam within about 50 ms at about 2 A" ([#54](https://github.com/vertical-cloud-lab/robot-arms/issues/54#issuecomment-6514063980));
  - run-3 peaks were J3 1.75 A (limit 4), J5 2.14 A (4.5) and J6 0.45 A (1.5); J5 holds −1.7 to −1.9 A at home ([#54](https://github.com/vertical-cloud-lab/robot-arms/issues/54#issuecomment-6515079421));
  - PR #16 peaks were J2 +1.125 A and J3 −1.942 A (A2 trace check);
  - the last teleop stop was on J4 at −2.4 A against a 2 A limit ([#86](https://github.com/vertical-cloud-lab/robot-arms/issues/86#issuecomment-7174991697)).
- Motors enable in 0.09–0.15 s ([PR #16](https://github.com/vertical-cloud-lab/robot-arms/pull/16); [#54](https://github.com/vertical-cloud-lab/robot-arms/issues/54#issuecomment-6514063980)). Joint feedback runs at 200 Hz, and the arm broadcasts ~3,100 CAN frames/s ([#28](https://github.com/vertical-cloud-lab/robot-arms/issues/28#issuecomment-6203158688)).
- Relay timings (2026-11-03): the arm talks 2.1 s after on and is silent 1.4 s after off. mpzy came back from a reboot in 42 s ([PR #60](https://github.com/vertical-cloud-lab/robot-arms/pull/60#issuecomment-6592765858), [11-06](https://github.com/vertical-cloud-lab/robot-arms/pull/60#issuecomment-6675357204)).

**Gripper**
- Span with sleeves: 45.6 mm closed, 108.6 mm open ([PR #73](https://github.com/vertical-cloud-lab/robot-arms/pull/73)). Before the sleeves it closed to 2.9–3.1 mm and opened to 61.2–65.4 mm in runs (A2 notes).
- Effort: 1.0 N·m commanded every time; peaks of 5.37, 5.83, 7.21, 4.92/4.90 and 5.88 N·m. At 7.21 N·m held, the motor overheated and the driver released 19 s into a carry ([PR #20](https://github.com/vertical-cloud-lab/robot-arms/pull/20#issuecomment-6205733011)). A "3 mm inside the roll" workaround cut the hold to 1.56–1.92 N·m. Position control slams at up to ~500 mm/s (A2 notes).

**Success counts (heterogeneous development history, code changing between runs)**
- Tape pick-and-place, 10-10 → 10-16: **6 of 10 executed grasps succeeded**. There were 2 misses (one closed on air, one ~65 mm off after the J1 jump), 1 squeeze failure (the roll squeezed out) and 1 drop (gripper overheat). This excludes ≥6 no-motion starts, 1 self-refusal and 2 empty-gripper survey bugs (A2 table; [PR #20](https://github.com/vertical-cloud-lab/robot-arms/pull/20#issuecomment-6207992243), [#30](https://github.com/vertical-cloud-lab/robot-arms/issues/30#issuecomment-6203807072)).
- Up/down cycles: 3/3 and 3/3 (10-09), 3/3 (10-15), 0 (run 1, jam), 1/3, 3/3 and 1/1 (10-30), 1/1 and 1/1 (11-03).
- Relay protocol: every on/off/run/refusal behaved as designed (4 hardware cases + 23/23, later 32/32 simulated cases). E-stop: 0 tests.

**Latency and network (teleop)**
- Real sessions (2026-11-12): SSH round trip 34 ms median; newest command 36 ms old at the Pi; leader read 1.1 ms; video 33 ms between frames ([PR #73](https://github.com/vertical-cloud-lab/robot-arms/pull/73)).
- CI → mpzy dry run: 49 ms RTT, equal to a bare `tailscale ping` relayed via Denver ([PR #68](https://github.com/vertical-cloud-lab/robot-arms/pull/68)); 19 ms median / 22 ms p95 on 11-06 ([PR #47](https://github.com/vertical-cloud-lab/robot-arms/pull/47#issuecomment-6674437590)). Locally, a command's age at the Pi fell from 4.8 to 0.5 ms after the threading change.
- Lab network ([PR #47](https://github.com/vertical-cloud-lab/robot-arms/pull/47#issuecomment-6430896968)): hard NAT; Pi → 1.1.1.1 6.7 ms (worst 7.5); Pi → Denver relay 15 ms; Pi↔Pi Wi-Fi 2.1 ms at 100 pings/s, or 10.7 ms average and 82 ms worst at 1 ping/s (Wi-Fi power saving).
- Recording overhead: commands went out a median 5.02 ms apart with recording on or off (39 vs 44 gaps > 10 ms of ~23,000) ([Teleop README](https://github.com/vertical-cloud-lab/robot-arms/blob/41a21f8/PiPER%20Sandbox%20Scripts/Teleoperation/README.md)). The livestream runs "several seconds behind, which is too slow to drive by" ([PR #47](https://github.com/vertical-cloud-lab/robot-arms/pull/47#issuecomment-6807316627)).

**Cameras, tags and calibration (real images)**
- Taped side camera fitted to the arm:
  - "within about 2 px" on 2026-10-09 ([#19](https://github.com/vertical-cloud-lab/robot-arms/issues/19#issuecomment-6091269791));
  - a 5-point refit at 9–19 px on the 4608-px image, ≈3–7 mm at the arm, on 10-13 ([#24](https://github.com/vertical-cloud-lab/robot-arms/issues/24#issuecomment-6157460585));
  - a video refit over ~900 frames on 10-16, with a median residual of 1.96 px at 2304×1296 and f = 860.98 px (~12 % below the nominal 1964 px at 4608 px that later work assumes), k1 = −0.1617 ([PR #20](https://github.com/vertical-cloud-lab/robot-arms/pull/20#issuecomment-6207992243));
  - "at the shelf 1 px of image height is about 10 mm along its line of sight". This camera was removed on 10-21.
- Printed tags from mpzy at 0.94–1.02 m and 57–67° tilt (2026-11-14), with uncalibrated intrinsics ([PR #40](https://github.com/vertical-cloud-lab/robot-arms/pull/40#issuecomment-6869819000)):
  - 25 mm tags: 9/9 read in 9/9 full-resolution frames;
  - lateral scatter 0.06–0.08 mm, depth SD 0.30–0.93 mm;
  - neighbour spacing within 0.6 mm for 10 of 12 pairs, one 1.25 mm off, and one **4.66 mm** off at a curled edge;
  - one pose flipped;
  - 2–3 of 9 tags read at 2304×1296, and 0 at 1280×720 (the stream resolution);
  - **10 mm tags 0 of 48.**
- The first on-printer tags: only ID 31 decoded at first. The bed tags (IDs 30, 32, likely 36) lacked a white margin on the black bed ([PR #77](https://github.com/vertical-cloud-lab/robot-arms/pull/77#issuecomment-6872104022)). A one-cell white border took detection on a dark surface from 0 % to ~100 % ([PR #77](https://github.com/vertical-cloud-lab/robot-arms/pull/77#issuecomment-6872476529)).

**Power and thermals**
- Wrist Pi streaming both cameras drew 1.1–1.5 A (PMIC 4.4–5.9 W; 2.1 W idle). Arm Pi and mpzy on 27 W supplies read 5.12–5.15 V idle; 76zj without USB-PD read 4.95–4.98 V idle and 4.67–4.82 V streaming ([PR #41](https://github.com/vertical-cloud-lab/robot-arms/pull/41)).
- On 2026-11-05 SoC temperatures were 54.5–61.2 °C with no throttling. Face blurring takes 89–93 % of each streaming Pi's CPU (1.84 / 1.77 / 3.56 cores) ([PR #40](https://github.com/vertical-cloud-lab/robot-arms/pull/40#issuecomment-6666130639)). Streams run at 720p and 5 fps (4.5–4.8 achieved; gripper Pi 2.9–3.6 fps) at 1.5 Mb/s ([#61](https://github.com/vertical-cloud-lab/robot-arms/issues/61#issuecomment-6617238309)).

**Printing and enclosure**
- Seven plates went to the A1 mini (0.4 mm nozzle, black PLA) between 10-26 and 11-03: ~368.6 g and ~13 h 55 min estimated (A4 sums; e.g. [#53](https://github.com/vertical-cloud-lab/robot-arms/issues/53#issuecomment-6511324753): 3 h 29 min, 99.52 g).
- The enclosure cost $120.30 ([#38](https://github.com/vertical-cloud-lab/robot-arms/issues/38)).

### c2. Simulated, modelled or synthetic results (not measurements)

- **CubXL protocol power and synthetic dry run:** see §d1 (e.g. H1a power 55 % at a true 99.8 % with n = 300).
- **Digital twin (MuJoCo, PR #77):**
  - 7/7 prints cleared;
  - grasps behind y ≈ +45 mm on the A1 mini bed collide with the printer;
  - J5 ±70° makes the gripper lean 10–20°;
  - compliance at 10 mm press: 3.95 / 8.11 / 16.13 N at K_z 400 / 800 / 1600 N/m;
  - 11 of 24 tags detected from mpzy's estimated pose;
  - auger swap: clip forces 18.0/16.7 N out and 18.1/19.1 N in, seated within 0.24 mm, 67 s ([PR #77](https://github.com/vertical-cloud-lab/robot-arms/pull/77#issuecomment-6872965077), [auger](https://github.com/vertical-cloud-lab/robot-arms/pull/77#issuecomment-6873360279)).
- **AprilTag simulations:**
  - one tag's tilt error 0.7°, with a mirror flip ~1 frame in 25; three tags solved jointly 0.1°; four 0.07°; base tags ≈1 mm at 0.5 m ([PR #77](https://github.com/vertical-cloud-lab/robot-arms/pull/77#issuecomment-6872207346));
  - flat tags flipped 3.2 % at 1 m with 40 mm tags, cubes never; cube placement 0.9–7.7 mm (median 2.7) vs flat tags 1.6–25 mm (median 8.6) ([PR #77](https://github.com/vertical-cloud-lab/robot-arms/pull/77#issuecomment-7050549455));
  - detectability is 100 % from 20 px up to 50° tilt, with a design target of ≥40 px and ≤65°; a hand–eye solve with assumed 0.5°/2 mm tag noise gives 0.18°/3.4 mm from 20 poses ([PR #40](https://github.com/vertical-cloud-lab/robot-arms/pull/40#issuecomment-6674437156));
  - a two-camera layout gives median 1.0 mm, with 88.7 % of poses seen by 2+ cameras ([#24](https://github.com/vertical-cloud-lab/robot-arms/issues/24#issuecomment-6326304174)).
- **Powder-Doser Workflow 1 (PR #83, SIM):** two-tag object localization within 0.2–1.6 mm, against 5–19 mm with a single tag; camera calibration within ~2 mm (5 mm with distortion + 0.2 px noise) ([PR #83](https://github.com/vertical-cloud-lab/robot-arms/pull/83#issuecomment-7147586012)).
- **AMP1 (PR #87, SIM, single episodes):**
  - robosuite 7/7, LIBERO-PRO 4/4, PiPER 3/4;
  - `vial_in_rack` inserted within 0.5 mm into a 2.5 mm-clearance pocket after the agent compensated sim joint deadbands of ~3 mrad (J1–J3) to 30 mrad (J5/J6);
  - `tape_to_shelf` ep1: 1.4 mm from centre;
  - `print_off_a1_mini` ep0: success by pushing, 32 min ([amp1 README](https://github.com/vertical-cloud-lab/robot-arms/blob/4809370/amp1/README.md), [PR #87](https://github.com/vertical-cloud-lab/robot-arms/pull/87#issuecomment-7236416277)).
- **Joint-current model (PR #23, 2026-11-28):**
  - it does not match #54's readings (it predicts ≥2.6× the recorded J3 current and ≥1.7× J2 at home);
  - with 0.5 kg in the gripper J5 needs up to 2.7 A and J4 up to 2.6 A (limits 1.5/2 A); with 1.5 kg J5 needs 5.2 A;
  - fixed current limits correspond to fingertip trip forces of ~40 N to >200 N depending on pose, and 6 % of poses trip while holding still;
  - accelerating at 360°/s² needs up to 4.2 A on J1/J2 ([PR #23](https://github.com/vertical-cloud-lab/robot-arms/pull/23#issuecomment-7237213210)).
- **Auger clip force (estimate):** 6–21 N per clip, 12–40 N for both, against "only about 15 N at the flange" ([#42](https://github.com/vertical-cloud-lab/robot-arms/issues/42#issuecomment-6408947353)). Never measured.


## (d) Planned campaigns and protocols

### d1. The CubXL loading reliability campaign (the "PiPER reliability paper")

**What the CubXL is.** The lab's CubXL is a Cubware (Ursa Laboratories) gantry (Cartesian) automation platform run by CubOS, configured with a capper and a pipette tool. Its "CubXL+ deck (Cubware `PandaDeck`)" is a 480 × 490 × 10 mm polycarbonate plate with 180 slots (18 × 10) at 45 mm × 25 mm pitch ([byu-vcl `robot-arm/cubxl-vial-handling/README.md` at f784f6b](https://github.com/vertical-cloud-lab/byu-vcl/blob/f784f6b/robot-arm/cubxl-vial-handling/README.md)). The arm task comes from chris-policky on [byu-vcl#266](https://github.com/vertical-cloud-lab/byu-vcl/issues/266#issuecomment-6038577665) (2026-10-07): "Automate vial handling between the 6DOF arm and the CubXL": pick up/replace single vials, move single vials to and from the CubXL, and "Move a carrier of 8–9 vials to and from the CubXL", starting with a printed mock-up. The 2026-10-07 review on that issue found the 9-vial holder fits only along gantry X (capper and pipette both reach 334 mm in X but only 220.7 mm in Y; the holder spans 264 mm), that the PiPER cannot grip straight down above about 0.10 m because J5 stops at ±70°, and that IK has no solution for a carrier lying across the arm's line; it proposed a fixed handoff dock with a handled carrier ([byu-vcl#266 comment](https://github.com/vertical-cloud-lab/byu-vcl/issues/266#issuecomment-6038926935); design in [byu-vcl PR 272](https://github.com/vertical-cloud-lab/byu-vcl/pull/272), open, CAD only, "untouched since 10-11").

**History.**
- 2026-10-10: sgbaird opened [#21](https://github.com/vertical-cloud-lab/robot-arms/issues/21) as "the first campaign ping for the PiPER reliability paper (how reliable the arm is at loading the CubXL with vial carriers and single vials)", specifying H1–H4, ≥300 trials per task × condition, 20 trials per capture-envelope offset, ISO 9283-style metrology at 5 poses × 30 cycles × 2 payloads, LabRobFail failure coding, Wilson/exact bounds, logistic ED50/ED90 and Kaplan–Meier MTBI. v1 `PROTOCOL.md` was written the same day on `claude/issue-21-20261010-2326` at [9652c43](https://github.com/vertical-cloud-lab/robot-arms/blob/9652c43/docs/protocol/PROTOCOL.md) ([comment](https://github.com/vertical-cloud-lab/robot-arms/issues/21#issuecomment-6103304073)); no PR was opened and it was never registered.
- 2026-11-27 18:58 UTC: sgbaird asked to "Push the pre-registered reliability protocol for loading the CubXL to the point where it can be registered" ([comment](https://github.com/vertical-cloud-lab/robot-arms/issues/21#issuecomment-7226065135)). That run opened [PR #89](https://github.com/vertical-cloud-lab/robot-arms/pull/89) (branch `claude/issue-21-20261127-1859`, 14 commits, last `ba0780b` after an independent review) and stopped at 20:38 UTC on a seat limit. A follow-up run pushed `claude/issue-21-20261127-2050` (PR #89's commits + 7, head `c8b3408`), not yet a PR, with the final summary ([comment 7227895694](https://github.com/vertical-cloud-lab/robot-arms/issues/21#issuecomment-7227895694)). **Nothing is registered.** References below are to files on that branch (`docs/protocol/`).

**Registry and format.** OSF Registries, *OSF Preregistration* template v4, as two registrations: **A** = E1 + E2 (H1–H3), **B** = E3 (H4) ([`README.md`](https://github.com/vertical-cloud-lab/robot-arms/blob/c8b3408/docs/protocol/README.md)). Rationale: no robotics or lab-automation journal offering Registered Reports was found; the hardware is not built; OSF is free/immediate with a DOI. No target journal has been named; Digital Discovery is suggested for the results paper.

**Question.** "How reliable is this arm at loading a CubXL deck with vial carriers and with single vials? And how much of the gap to 99 % per transfer does each of these close: (a) a lead-in dock, and (b) wrist-camera AprilTag correction?" Rationale table: probability that 50 transfers finish untouched is 28 % at 97.5 % per transfer, 61 % at 99 %, 78 % at 99.5 %, 95 % at 99.9 %; the 97.5 % "Ada" figure is still unchecked ([`PROTOCOL.md` §1](https://github.com/vertical-cloud-lab/robot-arms/blob/c8b3408/docs/protocol/PROTOCOL.md)).

**Error budget that motivates it** (byu-vcl#266, an estimate, "not a measurement"): ±0.64 mm combined (RSS) and ±1.15 mm worst case = ±0.10 mm repeatability + ±0.50 mm gripper + ±0.30 mm teaching/registration + ±0.25 mm structure/humidity. A tight pocket captures about ±0.6 mm; a 3 mm × 45° lead-in nest about ±3 mm. Correction cannot remove the ±0.5 mm gripper term ("an expectation, not a hypothesis").

**Design under test** (PR 272): two dock blocks with a 3 mm × 45° lead-in and cone pins 250 mm apart (v1 had assumed 225 mm), an 8 + 1 carrier with a handle post at slot 5, finger inserts (90° V-blocks with a rib, 67 g) with 1.5 mm Shore 30–50A silicone pads, and offset plates. A full carrier is 485 g with solid dummies (slicer estimate) or 0.53–0.66 kg by infill; printed dummy vial 64.2 mm tall, Ø27 mm body, Ø28 mm cap, 46.8 g solid (CubOS deck files say 83 mm; unresolved). The Cubware pocket squeezes the vial by 0.57 mm, which qualifies as ≤1 mm clearance.

**Hypotheses and decision rules** (§2; α = 0.05 each, no cross-hypothesis correction):
- **H1a**: open-loop carriers into the 3 mm lead-in dock succeed ≥99 %. Supported if the exact one-sided 95 % lower bound ≥0.99: at n = 300 that means 0 failures (0/300 → 0.9901; 1/300 → 0.9843); at n = 628 up to 2 failures. Refuted at ≥7 failures (n = 300) or ≥12 (n = 628). 1–6 failures at n = 300 is inconclusive and the cell is never extended.
- **H1b**: open-loop single vials into a ≤1 mm-clearance pocket stay below 99 % (supported at ≥7 failures in 300).
- **H2**: the dock's ED90 capture radius exceeds the ±1.15 mm worst-case arm error on both x and y (censored-curve and Fieller-bound rules; refutation per axis at one-sided 99 %).
- **H3a**: AprilTag correction raises single-vial success (one-sided Boschloo exact test). **H3b**: correction widens single-vial ED90 on both axes (delta-method bound; replaced a percentile bootstrap that falsely claimed a difference 10 % of the time). **H3c**: correction costs ≤ D8 seconds (suggested 5 s) per loading transfer (Hodges–Lehmann).
- **H4a** (registration B): unloaded ISO 9283 RP ≤ 0.10 mm at all five poses, with an instrument-adjusted refutation threshold (0.110 mm at U = 0.025 mm; 0.102 mm at U = 0.010 mm) and an "inconclusive" rule if U > 0.025 mm. **H4b/H4c**: RP grows with payload and with reach.
- Predictions Pred-1…Pred-8 are blanks for the PI, "recorded for calibration only".

**Tasks and conditions** (§5–§6). T1: carrier swap between dock and shelf; T2: single vial between a shelf pocket and the dock pocket. Each unit = one load (primary endpoint) + one unload (secondary). Conditions: **OL** (taught poses only) and **AT** (wrist camera reads the dock's tags at a look pose; x, y, yaw correction before every dock-side place and pick; abort, never fall back, if no valid pose or correction exceeds a 6 mm / 6° cap). Both conditions stop at the same look pose. No automatic retries. Success criteria are explicit (seated on both cone pins and flat, every vial upright and capped, clean release, no touch, no fault, within timeout; for T2 cap height within ±0.5 mm). Every failure and a random 10 % of successes are re-scored blind from witness stills; Cohen's κ reported.

**Trial counts and budget** (§8):
- **E1** (nominal reliability): 2 tasks × 2 conditions at zero offset; 300 loads per cell (D5 offers 628 for carriers-OL). 1,200 loads + 1,200 unloads at D5 = 300.
- **E2** (capture envelope): 21 levels (0; x and y ±1…±4 mm; yaw ±2°, ±4°) × 20 trials = 420 loads per task × condition, 1,680 in all (1,480 with D6's trimmed single-vial OL set). Expected ~660 failed loads, each needing a human reset (2–3 min each, 22–33 h of operator time, ~750 power cycles to ask the lender for).
- **E3** (metrology): 5 poses × 30 cycles × 2 payloads = 300 measured pose visits, ISO 9283-*style* (not conformant: 100 % rated load not used). Requires a fixture with expanded uncertainty U ≤ 0.025 mm (suggested: three 0.001 mm dial indicators on a sphere/cube target). No such fixture exists.
- Total 5,760 transfers at D5 = 300; ~48 h of arm time at 30 s/transfer or ~72 h at 45 s; 70–100 one-hour sessions.

**Power** ([`analysis/out/power.md`](https://github.com/vertical-cloud-lab/robot-arms/blob/c8b3408/docs/protocol/analysis/out/power.md); §8.4):
- H1a at n = 300: 22 % power if the true rate is 99.5 %, 41 % at 99.7 %, 55 % at 99.8 %, 74 % at 99.9 %; at n = 628: 39 %, 71 %, 87 %, 97 %. 80 % power at 99.7 % needs n = 913.
- H1b at n = 300: 99 % power at a true 95 %, 80 % at 97 %, 39 % at 98 %.
- H3a (Boschloo, 300 per arm): 95 → 99 %: 90 %; 97 → 99.5 %: 72 %; 97 → 99 %: 48 %. "A gain is only reliably detectable if open-loop single vials sit near 95 % or below."
- H2: supported 97–100 % if true ED90 ≥ 2 mm; 0–20 % at 1.5 mm; false refutation 1.0–5.1 % at exactly 1.15 mm (10,000 campaigns per curve shape).
- H4a (30 cycles, U = 0.025 mm): "meets" 94 % if true RP = 0.07 mm, 54 % at 0.08, 5 % at 0.09; "certified" 89 % at 0.04 mm; refuted 5.0 % for an arm exactly at 0.10 mm, 37 % at 0.11, 81 % at 0.12, 99 % at 0.13.
- H4b/H4c: 61 % and 83 % power for 0.01 mm effects; 98–100 % at 0.02 mm.
- MTBI (600 E1 transfers per cell): "Imprecise by design": at 1 intervention per 100 transfers the 95 % interval is 46–272 transfers.
- D11 run-of-failures stop (3 failed loads in a row in E1; 2 failed zero-offset loads per E2 block): 0.5 % chance of stopping a healthy 97.5 % cell over 300 loads, 9 % at 93 %; stops a 50 %-failing cell within ~14 loads; slow at 15–20 % failure (347 loads on average).

**Analysis plan** (§14): Wilson intervals and exact (Clopper–Pearson) one-sided bounds; Boschloo; Firth logistic ED50/ED90 with Fieller bounds; Kaplan–Meier MTBI (restricted mean, horizon τ = 300 transfers; Garwood when < 10 interventions); ISO 9283 RP with bootstrap-t bounds; outcome-neutral checks; failure coding with LabRobFail's five categories, eleven subtypes and four severities quoted verbatim from arXiv 2607.23704v2 (with a noted inconsistency in the paper's severity names). Code: [`prereg_stats.py`](https://github.com/vertical-cloud-lab/robot-arms/blob/c8b3408/docs/protocol/analysis/prereg_stats.py) (one `h*_decision` function per hypothesis), [`power.py`](https://github.com/vertical-cloud-lab/robot-arms/blob/c8b3408/docs/protocol/analysis/power.py) (`--check-rejected` takes ~54 min), [`simulate_and_check.py`](https://github.com/vertical-cloud-lab/robot-arms/blob/c8b3408/docs/protocol/analysis/simulate_and_check.py) (synthetic campaign; it caught RP percentile-bootstrap coverage of 71–76 % and MTBI intervals cut at every block end), `crossref_check.py` (23 of 23 DOIs match Crossref/DataCite; 30 references). Data plan: raw logs/video to a Hugging Face dataset under `byu-vcl` (D14), code at a tagged commit.

**PI decisions still open** (§0, D1–D16): e.g. D1 mock-up v2 deck vs real CubXL (suggested mock-up: "No CubXL is in or near the cell"), D2 printed dummies vs glass, D5 n = 300 vs 628, D6 full vs trimmed E2 levels, D10 metrology instrument, D11 stop rule, D12 end date (16 weeks after first counted block), D14 data home, D15 operators/blind reviewer, D16 contributors/embargo.

**Bench gates** ([`bench-readiness.md`](https://github.com/vertical-cloud-lab/robot-arms/blob/c8b3408/docs/protocol/bench-readiness.md); "None of the gates below is met yet"). Owners are suggestions ("Nobody has agreed to anything"): sgbaird (PI decisions, safety review SF1, lender OK for ~6,000 transfers and ~750 power cycles HW9, sharing the arm with the auger work HW10); chris-policky (print and test-fit PR 272 parts RA2/HW1, shelf RA3, AprilTags HW4); jss265 (E-stop test SF2, transformer clearance SF3, training SF6, inserts so the gripper homes HW2, wrist Pi back online HW3, payload weighing HW6, J1 zero stability HW8 = 20 relay cycles within ±0.2°, pilot PL1–PL3); `@claude` runs (harness SW1 incl. a 2-hour soak with the livestream on, AprilTag correction SW2, PR 23 update); nobody yet for the metrology fixture RB1.

**Realistic dates** (from bench-readiness): register A 2027-01-29 (earliest 2026-12-04 if registered on CAD and amended later); register B 2027-02-19; first counted block 2027-03-05 (earliest 2027-02-12); campaign done 2027-05-14; results paper submitted 2027-06-25.

**Protocol-vs-cell mismatches found on 2026-11-27** ([`hardware-and-safety-check.md`](https://github.com/vertical-cloud-lab/robot-arms/blob/c8b3408/docs/protocol/hardware-and-safety-check.md)): the arm has gripped "Only a tape roll ... No vial and no carrier, ever"; the dock/carrier/inserts/plates are "CAD and slices only"; no real CubXL is in or near the cell (v1 mock-up pitch 35.6 mm vs real 25 mm); no trial harness or correction code exists; no intrinsics or hand–eye calibration on hardware; the E-stop has no recorded test; the drivers' collision-protection level has never been read (another user's PiPER reported level 0); main's CLAUDE.md still says eufi drives the arm.

### d2. Powder-Doser Workflow 1: auger pick-and-place repeatability test (PR #83)

- Requested by chris-policky in the [PR #83](https://github.com/vertical-cloud-lab/robot-arms/pull/83) body (2026-11-24; issue [#82](https://github.com/vertical-cloud-lab/robot-arms/issues/82)), executed on jss265's ping ([comment 7147577873](https://github.com/vertical-cloud-lab/robot-arms/pull/83#issuecomment-7147577873)). Protocol: pick the powder-doser auger out of its clips (held on wood blocks), place it in a box whose inside is 10 mm larger than the auger in length and width; **3 placement spots × 30 iterations**; graded A (found, picked, placed in box), B (picked, not placed), C (found, not picked), D (not found), F (complete failure). Constraints: J1 limited to −20°…+60° to avoid the A1 mini; gripper twist limited to 90° (J6 −52°…+38°) by wiring; J4 held at 0°; AprilTags to find objects.
- Built ([comment 7147586012](https://github.com/vertical-cloud-lab/robot-arms/pull/83#issuecomment-7147586012), 2026-11-25, head `07cbb8d`): `auger_test.py`, `vision.py` (fits all corners of an object's two tags: holder and box within 0.2–1.6 mm in simulation vs 5–19 mm with a single tag), `calibrate.py` (camera-to-arm from a tag card carried through ~20 poses; within ~2 mm in simulation, ~5 mm with distortion and 0.2 px noise), `report.py` (grade counts per spot, success rates with 95 % intervals, run-to-run repeatability), `layout.py`, `make_tags.py` (tags 199–204), 11 tests passing on `fake_piper.py`.
- **Not run on the real arm.** Before a real run: measure tag offsets, TCP/fingertip lengths, box, A1 mini and shelf positions; install numpy/OpenCV in mpzy's `~/piper-venv` (absent); print tags; calibrate. Noted risks: the doser clips hold ~18 N each and straight pulls may fail (peeling worked in the digital twin); the finger direction (−25.7°) is inferred from a photo.

### d3. Other measurement plans on record (not campaigns yet)

- **WRTG 316 paper's test list** (literature-derived; no lab data in the paper): Chajón-style planar ISO 9283 repeatability with a Pi camera + dial indicator, Zhou-style station recalibration from 20 mm and 75 mm tags vs touch-on-cube with a 300 mm reference fixture, Harazono-style offset-tolerance and loaded-transfer tests, and Vincent-style lower confidence bounds ([`selection.md`](https://github.com/vertical-cloud-lab/robot-arms/blob/41a21f8/docs/wrtg-316/edison/selection.md)); see section (g).

## (e) Ideas and directions raised in October–November 2026, and who raised them

### e1. Early October: setting the direction

- **Camera choice:** an HQ camera for computer vision plus a Camera Module 3 Wide for streaming, two cameras on one 8 GB Pi 5 at the wrist (sgbaird, 2026-09-25, overriding Claude's CM3-Wide-first ranking; [#3](https://github.com/vertical-cloud-lab/robot-arms/issues/3#issuecomment-6089392023)).
- **No ROS:** "we will probably end up using the python package directly rather than ROS or ROS2" (sgbaird, 2026-10-02, [#5](https://github.com/vertical-cloud-lab/robot-arms/issues/5#issuecomment-6089392760)). Everything since uses `piper_sdk` directly.
- **Candidate workflows** at the 10-01 team meeting (jss265, chris-policky, claytonblodgett): "CubXL module replacement and Atomizer chamber cleaning" ([#6](https://github.com/vertical-cloud-lab/robot-arms/issues/6)). On 10-08 chris-policky printed a CubXL-like dock bed and benwhitney5463 designed keys for it ([#6](https://github.com/vertical-cloud-lab/robot-arms/issues/6#issuecomment-6089393210)). On 10-15 the action item for jss265 was "set up IK tools in the repo" ([#6](https://github.com/vertical-cloud-lab/robot-arms/issues/6#issuecomment-6220567889)).
- **Remote availability as the lab's purpose:** "the purpose of the lab is to have constantly available robots for remote use" (jss265, 2026-10-10, [#18](https://github.com/vertical-cloud-lab/robot-arms/issues/18#issuecomment-6091774765)). This motivated the E-stop and, later, the relay.
- **Reliability paper and safety docs** (sgbaird, 2026-10-10): the CubXL protocol ([#21](https://github.com/vertical-cloud-lab/robot-arms/issues/21)) and the hazard analysis and SOP ([#22](https://github.com/vertical-cloud-lab/robot-arms/issues/22)). On PR #23 sgbaird wrote: "Knowing that this is probably overkill, but we can use it as a starting point" ([comment](https://github.com/vertical-cloud-lab/robot-arms/pull/23#issuecomment-6157306212)).
- **Camera-based arm calibration and extra cameras** (sgbaird, 2026-10-13/14, [#24](https://github.com/vertical-cloud-lab/robot-arms/issues/24)); datum fixtures and a Pi-switched relay (jss265, 2026-10-14). The camera fixture layout moved to [PR #40](https://github.com/vertical-cloud-lab/robot-arms/pull/40). One stream per camera rather than composited (sgbaird, 2026-10-26, [PR #40](https://github.com/vertical-cloud-lab/robot-arms/pull/40#issuecomment-6427446348)).

### e2. Powder-doser cooperation and the auger swap (jss265, from 2026-10-26)

- **Stated goal:** "The purpose for the 6DOF team this semester (Fall 2026) is to create end effectors and workflows for the PiPER arm to help automate other projects in the lab. Priority number 1 is the to automate the removal and replacement of augers from the powder-doser" ([#42](https://github.com/vertical-cloud-lab/robot-arms/issues/42)).
- **Proposed workflow (jss265):** grip the auger mid-body, pull it from the doser's compliant clips, strip the tapping collar on a finger fixture, bin it, pick a new one, re-thread and press it in.
- **Options (jss265):** Strategy 1 (two-servo tool), Strategy 2 (one-servo linkage), Alternative A (sleeves on the stock gripper plus a pin or slider), Alternative B (sleeves plus the doser's servos).
- **Claude's assessment** ([#42](https://github.com/vertical-cloud-lab/robot-arms/issues/42#issuecomment-6408947353)): "Mass is not the limit; the snap force is." Clip pull-out was estimated at 12–40 N against ~15 N available at the flange, and Strategy 1 was ranked most feasible. "Next step either way: measure the printed clip's pull-out force with a luggage scale on the auger."
- **What happened:**
  - Six design rounds in [PR #44](https://github.com/vertical-cloud-lab/robot-arms/pull/44): a medium-fidelity Onshape document, a high-fidelity S1 tool (~0.62 kg, Feetech STS3215 servos, Pi + cameras on the tool, J6 XT30 power), a finger fixture shrunk from 155 to ~25 cm³, a compliant-latch slider, and counterbored sleeves.
  - The Alt A parts were printed in PLA on 10-30 and 11-03 ([#53](https://github.com/vertical-cloud-lab/robot-arms/issues/53#issuecomment-6511324753), [#55](https://github.com/vertical-cloud-lab/robot-arms/issues/55)).
  - claytonblodgett asked on 11-13 for a lower slider guide. The follow-up question about the doser floor height was never answered ([PR #44](https://github.com/vertical-cloud-lab/robot-arms/pull/44#issuecomment-6839992268)).
  - **No auger has been handled by the arm. The clip force has not been measured. Strategy 1 was not built.**
- **On the doser side,** ethanw-24 opened [powder-doser #203](https://github.com/vertical-cloud-lab/powder-doser/issues/203) (2026-11-07) to redesign the tap collar so augers can be swapped without removing it, which would remove the need for the finger fixture.
- **Simulation and test plan:** the digital twin's auger swap (PR #77, below) and chris-policky's Powder-Doser Workflow 1 (PR #83, §d2) are where this now continues.

### e3. SO-101 leader teleoperation (jss265, 2026-10-27 → 11-13)

- jss265 asked to drive the PiPER from home with their Hugging Face SO-101 leader, with live HQ-camera video and "LOWEST latency as possible" ([PR #47](https://github.com/vertical-cloud-lab/robot-arms/pull/47#issuecomment-6430891965)). It was built 2026-11-06 ([PR #68](https://github.com/vertical-cloud-lab/robot-arms/pull/68)), first run on the real arm 2026-11-12 ([PR #73](https://github.com/vertical-cloud-lab/robot-arms/pull/73)), and extended with recording, a latch, a J4 jog and full-range mapping on 2026-11-13 ([d36efc8](https://github.com/vertical-cloud-lab/robot-arms/commit/d36efc8)). First test video: https://youtu.be/E3Q9NqakqIE ([PR #47](https://github.com/vertical-cloud-lab/robot-arms/pull/47#issuecomment-6846329256)).
- jss265 then closed PR #47, noting the code "has been pushed to main so that any Tailscale authorized user can teleoperate the arm by cloning the repo." Open items: a joint-by-joint check of the map, the gripper zero and range, the J6 park at the cable stop, and the camera aim.
- This is the only route by which the arm has recently done non-trivial work, and the obvious route to LeRobot demonstration data. **No dataset has been recorded**, although `HF_TOKEN` exists "for LeRobot datasets and policies" (CLAUDE.md).

### e4. Relay power control (chris-policky wiring, jss265 protocol, 2026-11-03)

- [#59](https://github.com/vertical-cloud-lab/robot-arms/issues/59), [#57](https://github.com/vertical-cloud-lab/robot-arms/issues/57#issuecomment-6592498786) and [PR #60](https://github.com/vertical-cloud-lab/robot-arms/pull/60): power goes off only after a clean exit with the arm parked (see a2). jss265 asked for a protocol "where anytime a workflow or program is to be sent to the arm that it enables the relay and won't turn off the relay until that program returns saying the arm is in the safe home position" ([comment](https://github.com/vertical-cloud-lab/robot-arms/pull/60#issuecomment-6592760272)).

### e5. Livestream with on-device face blurring (sgbaird, 2026-11-03 → 11-20)

- sgbaird asked on [#61](https://github.com/vertical-cloud-lab/robot-arms/issues/61) for a stream from a camera "that doesn't point to the lab", with face blurring. Decisions: "change it to a public livestream, but make sure you've added face blurring" ([11-03](https://github.com/vertical-cloud-lab/robot-arms/issues/61#issuecomment-6617230097)) and "you can set the streams to public, as long as face blurring is active" ([11-05](https://github.com/vertical-cloud-lab/robot-arms/issues/61#issuecomment-6647533092)).
- **What was built:** YuNet plus deface's CenterFace on every frame, failing closed, with strict zones for false positives on the AMS lite. All four cameras were public on the *BYU VCL Hardware Streams* channel by 11-05 ([#61](https://github.com/vertical-cloud-lab/robot-arms/issues/61#issuecomment-6647538164)).
- **Now:** only mpzy's front cam is live (https://www.youtube.com/watch?v=h5TJ0nLUljU, since 11-20). [PR #81](https://github.com/vertical-cloud-lab/robot-arms/pull/81) (open) makes the stream "lend" its camera to teleop or a workflow: a PID file, release within ~1 s, and a "Camera in use" card. Tested: teleop's first frame arrived 2 s after asking ([#61](https://github.com/vertical-cloud-lab/robot-arms/issues/61#issuecomment-7043250595)).

### e6. Demos (sgbaird)

- **Lab-o-ween, 2026-10-30** ([#56](https://github.com/vertical-cloud-lab/robot-arms/issues/56#issuecomment-6534737800)): "Ready to demo tonight: the up-and-down cycle from #54 (`Up_and_Down.py`). The tape pick (#19) and SO-101 teleop (#46) are not ready." There is no record of how it went.
- **"Is the arm available for use?" (2026-11-03,** [#62](https://github.com/vertical-cloud-lab/robot-arms/issues/62)**):** a read-only check found the arm free, parked and unpowered behind the relay. A frame from the fixed camera showed tools on the bench and a person beside the arm, so the demo motion was not run ([comment](https://github.com/vertical-cloud-lab/robot-arms/issues/62#issuecomment-6613953160)).

### e7. AprilTag sandbox and digital twin (jss265, 2026-11-14; tag cubes by sgbaird, 2026-11-20)

- [#76](https://github.com/vertical-cloud-lab/robot-arms/issues/76) led to [PR #77](https://github.com/vertical-cloud-lab/robot-arms/pull/77) (open; the only rule is that every file stays inside `PiPER Sandbox Scripts/`).
- **Tag work:**
  - identifying the A1 mini's tags from mpzy, where only ID 31 decoded; the bed tags lacked a white margin ([comment](https://github.com/vertical-cloud-lab/robot-arms/pull/77#issuecomment-6872104022));
  - jss265's questions on planes from 3–4 tags, partial occlusion and base tags with forward kinematics, answered with `tag_layout_sim.py` and a recommended tag map. The 589-character recommendation: "Measure everything in the arm's base frame", calibrate lenses with ChArUco first, "touch each center once with the gripper", "Solve all tags in view together", "Coarse to fine: the fixed camera gets within about 1 cm; the wrist camera finishes" ([comment](https://github.com/vertical-cloud-lab/robot-arms/pull/77#issuecomment-6872207346)).
- **Digital twin:** jss265 asked (`@claude`:max) for an "ultra precision" open-source simulation of the arm picking prints off the A1 mini, "thinking forward to what our autonomous/compliant/modulation needs will be" ([comment](https://github.com/vertical-cloud-lab/robot-arms/pull/77#issuecomment-6872959510)).
  - The result is `PiPER Sandbox Scripts/Digital Twin/`: MuJoCo plus a numpy kinematic engine, piper_sdk's DH table, Menagerie meshes, 1 kHz joint and Cartesian impedance control, an adhesion model, YAML configs, and a `PiperSDK` facade so lab scripts can run against the twin. It clears 7/7 prints (private video https://www.youtube.com/watch?v=z6yoRY2fVWU) ([comment](https://github.com/vertical-cloud-lab/robot-arms/pull/77#issuecomment-6872965077)).
  - jss265 then asked for the same with powder-doser augers. The swap works in simulation, and the findings are design feedback for the doser: as drawn the auger cannot come out (closed collar); on 250 mm legs the doser is too tall for the PiPER (it works lowered 120 mm); the auger must be peeled out, not pulled; the clip arms reach ~48 MPa ([comment](https://github.com/vertical-cloud-lab/robot-arms/pull/77#issuecomment-6873360279)).
  - The twin found that AgileX's URDF matches piper_sdk's older DH table while `Up_and_Down.py` uses the newer one (J2 zero differs by 2°, the wrist by ~10 mm), and that the URDF masses total 2.4 kg against AgileX's 4.2 kg.
- **Tag cubes:** sgbaird suggested "a multi-color print with black and white with a cube with a mounting setup specific to the intended destination" ([comment](https://github.com/vertical-cloud-lab/robot-arms/pull/77#issuecomment-7050542319)). The result: 13 cubes and 60 tags (IDs 100–169) with destination-specific mounts (table flanges, a PiPER base collar, shelf-corner caps), an H2D two-colour plate at 11 h 55 min, **not printed** ([comment](https://github.com/vertical-cloud-lab/robot-arms/pull/77#issuecomment-7050549455)).

### e8. Fiducial calibration board and USB-C adapters (jss265, 2026-11-05)

- [#66](https://github.com/vertical-cloud-lab/robot-arms/issues/66): calib.io 300 × 200 mm ChArUco ($138) recommended, with AndyMark's ($51) as the cheap option. **Not bought:** jss265 decided to print mats "if needed". The 90° USB-C adapter and coupler ($18.98) were ordered as ME 13640 and approved by sgbaird ([comment](https://github.com/vertical-cloud-lab/robot-arms/issues/66#issuecomment-6647149651)).

### e9. Powder-Doser Workflow 1 (chris-policky, 2026-11-23/24)

- Auger pick-and-place repeatability test, 3 spots × 30, A–F grading, AprilTag localization; built and simulated only ([PR #83](https://github.com/vertical-cloud-lab/robot-arms/pull/83)). See §d2. Note that it borrows mpzy's livestream camera "as PR #81 describes".

### e10. Printer tending and the A1 mini bed temperature (jss265, 2026-11-25)

- [#86](https://github.com/vertical-cloud-lab/robot-arms/issues/86): "the A1-mini on the robot table (Thumbelina)'s print bed is hot. It's been hot for days."
  - A cloud job (`AOR_tester`) had stalled in `PREPARE` since 2026-11-17 (its unpacked G-code was 0 bytes), holding the bed at 65 °C for ~8 days.
  - The LAN commands `M140 S0` and `stop` were rejected, because the cloud-bound firmware refuses unsigned LAN commands (HMS `0500-0500-0001-0007`).
  - jss265's power cycle cleared it and restored the black screen and the camera. Firmware is 01.08.01.00 against 01.09.00.00 available, and the SD card holds 20.7 GB of print video ([comment](https://github.com/vertical-cloud-lab/robot-arms/issues/86#issuecomment-7175170366)).
- In the same thread the arm's relay was found on since 2026-11-14 and forced off ([comment](https://github.com/vertical-cloud-lab/robot-arms/issues/86#issuecomment-7174991697)).
- **Relevance:** the arm shares its table with a printer that cannot be commanded over LAN while bound to Bambu's cloud. Print removal by the arm was simulated in PR #77 (11-14) and PR #87 (11-28).

### e11. Apple AMP1 agentic manipulation (sgbaird, 2026-11-25 → 11-28)

- sgbaird: "thoroughly explore https://apple-aiml-research.github.io/ml-amp/ ... Attempt to reproduce as best you can. Then, try with some of the relevant tasks in this repo" ([#85](https://github.com/vertical-cloud-lab/robot-arms/issues/85)).
- **What AMP1 is** (arXiv 2611.09892): a frontier model writes Python against a robot SDK in a persistent kernel, looks at images, and has no skill library. Reported: RoboLab-120 82.8 % (Opus 5.5), CaP-Gym LIBERO-PRO 95.2 %, robosuite 98.4 %, real Franka 104/108. A real success averaged 280 s (69 s of motion, 211 s of reasoning) ([amp1 README](https://github.com/vertical-cloud-lab/robot-arms/blob/4809370/amp1/README.md)).
- **Reproduced on a CPU runner** with Claude Code agents bridged to AMP's tools (no API key). Results: robosuite 7/7, LIBERO-PRO 4/4, and a simulated PiPER 3/4: #21-style `vial_in_rack` ✓, the paper's banana ✓ with a caveat, `tape_to_shelf` ep0 ✗ (never released) and ep1 ✓. These are single episodes, "anecdotes, not success rates". Video: https://www.youtube.com/watch?v=_PlBarOj3K4 ([#85](https://github.com/vertical-cloud-lab/robot-arms/issues/85#issuecomment-7183974219); [PR #87](https://github.com/vertical-cloud-lab/robot-arms/pull/87), opened by sgbaird 11-27).
- **Lessons transferable to the real cell:** J5 ±70° rules out top-down placement over an 8 cm shelf at ~0.43 m (a 25° tilt worked), and the agent compensated sim joint deadbands. Before any real run it needs the re-measured gripper spec, RGB-only cameras (the paper's rgb_only/no-calibration setting still reached 75.8 %), the wrist pod and cable in the collision model, and measured tracking error.
- **11-28:** sgbaird asked to try "auto removal of prints from the A1 mini, the auger swapping workflow, interaction with the atomizer for autonomous atomization runs" ([comment](https://github.com/vertical-cloud-lab/robot-arms/pull/87#issuecomment-7236408042)). `print_off_a1_mini` ep0 was scored a success, but only by caging and pushing the print off, upside down, after two failed tilted grasps (32 min). `auger_swap` and `atomizer_charge` were still running at survey time ([comment](https://github.com/vertical-cloud-lab/robot-arms/pull/87#issuecomment-7236416277)).

### e12. 2026-11-27/28: preregistration, wrist power, motion-safety monitoring

- **CubXL preregistration pushed to registrable form** (sgbaird, 2026-11-27): §d1.
- **Wrist-Pi power via a 12 V step-down** (sgbaird, 2026-11-28): "For streaming, probably. For a busy Pi, no." Recommendation: a 12 V 3 A adapter + Pololu D36V28F5 (+ terminal), $48.85, giving 4.93–4.96 V at the Pi at 1.5–2.5 A. 6 V is ruled out by the regulator's ~1.0–1.2 V dropout. The PAHT-CF housing is not drawn and nothing was bought ([PR #41](https://github.com/vertical-cloud-lab/robot-arms/pull/41#issuecomment-7237025252)).
- **Slowdowns, collision checks and joint-current analysis "Especially for remote, unattended operation"** (sgbaird, 2026-11-28, [PR #23](https://github.com/vertical-cloud-lab/robot-arms/pull/23#issuecomment-7237206949)). Result ([comment](https://github.com/vertical-cloud-lab/robot-arms/pull/23#issuecomment-7237213210); [`motion-monitoring.md`](https://github.com/vertical-cloud-lab/robot-arms/blob/6a63ee8/docs/safety/motion-monitoring.md)):
  - proposed fingertip speed caps (transit ≤250 mm/s, approach ≤50 mm/s within 100 mm, contact ≤10 mm/s);
  - three layers of collision checks: path vs a measured cell model, measured-minus-expected current during moves, and back off/hold/alert after a detection;
  - "Unattended runs: SOP §J says no for now", with 12 conditions (U1–U12, including interlocked guarding);
  - the URDF-based current model disagrees with the #54 measurements, so thresholds need a measured baseline (M3).
- **WRTG proposal LaTeX draft** (jss265, 2026-11-28): §g.

## (f) Open problems, blockers, and what failed

### f1. Hardware availability and the wrist

1. **The wrist Pi (76zj) has been offline since 2026-11-11 and eufi since 2026-11-06.** On 11-28 neither answered ping or ARP on the LAN, so a person has to check their power and cabling ([PR #81](https://github.com/vertical-cloud-lab/robot-arms/pull/81#issuecomment-7236436886)). Until then the AprilTag-corrected condition of #21 "can't run today" ([hardware check, row 8](https://github.com/vertical-cloud-lab/robot-arms/blob/c8b3408/docs/protocol/hardware-and-safety-check.md)), teleop has no wrist video, and only one camera exists. eufi went down after a homemade overhead-camera ribbon turned its power light red ([PR #40](https://github.com/vertical-cloud-lab/robot-arms/pull/40#issuecomment-6843948205)). 76zj had earlier needed a fresh SD card after running on a weak charger.
2. **Wrist power is marginal and the fix is not bought.** See a6. A free check (27 W + AINOPE under `stress-ng`) waits on the Pi coming back ([PR #41](https://github.com/vertical-cloud-lab/robot-arms/pull/41#issuecomment-7237025252)).
3. **Wrist cabling restricts J6 and touches J2.** The jam at −55° (16 A), the cord hitting J2 at home, and the camera screws scratching the J2 housing ([#54](https://github.com/vertical-cloud-lab/robot-arms/issues/54#issuecomment-6515341211)) left J6 confined to ~90°, with the park at the cable stop. With the motors off J6 rolls freely, so `arm_home.json`'s J6 range (−95…−45°) often fails and `arm_power.py off` refuses. That is how the relay was left on for ~11.5 days after 2026-11-14 ([#86](https://github.com/vertical-cloud-lab/robot-arms/issues/86#issuecomment-7174991697)). The breakaway connector suggested on 2026-09-27 was never ordered (A1 notes).
4. **Gripper.**
   - The sleeves stall the gripper's zero-finding, so motor 7 is never enabled; "Whether it can home correctly with the sleeves on is open" ([PR #73](https://github.com/vertical-cloud-lab/robot-arms/pull/73)).
   - Grip force control overshoots 5–7× and once overheated and dropped a part.
   - The gripper version (0–70 vs 0–100 mm) was never confirmed.
   - The CubXL finger inserts must make motor 7 home and enable (gate HW2).
5. **Joint reference instability.** J1 jumps on enable (multiples of ~7.95°; root cause unknown; [PR #20](https://github.com/vertical-cloud-lab/robot-arms/pull/20#issuecomment-6207992243)), a 15.2° re-zero (11-14) invalidated earlier J1 numbers, and J3 rest varies by up to ~1.7° between power-offs. Gate HW8 (20 relay cycles within ±0.2°) has not been run.
6. **Payload margin is thin and unweighed.** The 1.5 kg rating includes the 0.5 kg gripper. The wrist pod (Pi, two cameras, mount) is unweighed, with a fitted estimate of ~0.40 kg ([PR #23](https://github.com/vertical-cloud-lab/robot-arms/pull/23#issuecomment-7237213210)). A full CubXL carrier is 0.53–0.66 kg. Gate HW6 is "Not started".
7. **Kinematic reach limits.**
   - No top-down grasps above ~0.10 m (J5 ±70°).
   - No IK across the arm's line for carriers.
   - J1 is boxed to −20…+60° by the A1 mini.
   - The back of the A1 mini bed is unreachable (y > +45 mm, simulated).
   - The powder doser on its 250 mm legs is too tall (simulated).

### f2. Safety and operations

1. **The E-stop has never been tested,** and its order relative to the relay is unrecorded ([hardware check, row 3](https://github.com/vertical-cloud-lab/robot-arms/blob/c8b3408/docs/protocol/hardware-and-safety-check.md)).
2. **The safety docs are an unreviewed draft.** PR #23 described the 2026-10-10 cell ("no E-stop installed", eufi drives the arm) until today's addendum. Its fifteen "Need" items have no owner, and the College Health & Safety review (gate SF1) has not been convened. The transformer clearance (190 mm rule, M1) has never been measured ([PR #23](https://github.com/vertical-cloud-lab/robot-arms/pull/23); A2 notes).
3. **Incident, 2026-11-14:** a teleop session ended on a J4 over-current with the motors enabled, holding J2 113°/J3 −69° ([#86](https://github.com/vertical-cloud-lab/robot-arms/issues/86#issuecomment-7174991697); the hardware check, row 5, gives J2 113.2°). The relay stayed on until it was forced off on 11-25.
4. **mpzy is a single point of failure.** It is a 1 GB Pi that drives CAN, switches the relay, and runs the face-blurred livestream (~375 MB free). A reboot drops GPIO17 and the arm falls (no brakes). Gate SW1 requires a 2-hour harness soak with the stream on ([hardware check, rows 2, 4](https://github.com/vertical-cloud-lab/robot-arms/blob/c8b3408/docs/protocol/hardware-and-safety-check.md)).
5. **Collision protection status is contradictory.** It was read as level 1 on all joints on 2026-10-09 ([PR #16](https://github.com/vertical-cloud-lab/robot-arms/pull/16#issuecomment-6091071751)), but 11-27/11-28 runs say "never read". AgileX's read demo zeroes it first ([PR #23](https://github.com/vertical-cloud-lab/robot-arms/pull/23#issuecomment-7237213210)). Fixed current limits correspond to 40 to >200 N fingertip trip forces depending on pose (model).
6. **People in the workspace.** People were in or near the workspace during October enabled runs at least three times. The remote-availability goal ("constantly available robots for remote use", [#18](https://github.com/vertical-cloud-lab/robot-arms/issues/18#issuecomment-6091774765)) conflicts with the draft SOP's "workspace clear" rule (a trained person at the E-stop for the whole run; "A remote person who can't see the cell can't declare it") and with "Unattended runs: ... no for now" ([PR #23](https://github.com/vertical-cloud-lab/robot-arms/pull/23#issuecomment-7237213210)).

### f3. Vision and calibration

1. **No intrinsics and no hand–eye calibration on hardware.** No ChArUco board was bought. The fixed cameras' poses are nominal CAD. The only arm fits were of a camera that has since been removed ([#24](https://github.com/vertical-cloud-lab/robot-arms/issues/24#issuecomment-6326304174)).
2. **Tag size and placement limits:**
   - 10 mm tags are unreadable from the fixed cameras (0/48);
   - 25 mm tags read only at full resolution and never at stream resolution;
   - flat tags flip;
   - tags need white borders on dark surfaces ([PR #40](https://github.com/vertical-cloud-lab/robot-arms/pull/40#issuecomment-6869819000), [PR #77](https://github.com/vertical-cloud-lab/robot-arms/pull/77#issuecomment-6872476529)).
   The protocol requires tags of at least 25 mm (rule R3). The tag cubes are unprinted.
3. **Cameras:** the overhead camera was never installed, and the HQ lens is unfocused and cannot focus at the ~60 mm close range.

### f4. The CubXL campaign specifically

- Every bench gate is open ([bench-readiness.md](https://github.com/vertical-cloud-lab/robot-arms/blob/c8b3408/docs/protocol/bench-readiness.md)):
  - PR 272's dock, carriers, inserts and plates are CAD only, "untouched since 10-11";
  - the shelf design is not fixed;
  - there is no trial harness or AprilTag correction code;
  - the metrology fixture (U ≤ 0.025 mm) has no owner;
  - the lender's consent has not been asked;
  - the 16 PI decisions in §0 are blank;
  - arm sharing with the auger work (HW10) is undecided;
  - the vial height (64.2 vs 83 mm) is unsettled;
  - ISO 9283 §6.8 is unchecked, because the free sample of the standard stops before it;
  - the "Ada 97.5 %" figure is unchecked;
  - no target journal has been named.
- Design-level caveats the protocol itself records:
  - 300 loads can certify 99 % only with zero failures (55 % power at a true 99.8 %);
  - H3a is detectable only if open-loop single vials are at ≤ ~95 %;
  - the yaw levels saturate for open-loop carriers;
  - correction cannot remove the ±0.5 mm gripper term;
  - E2 implies ~660 human reach-ins.

### f5. Repository state

- **Unmerged:** almost everything (b2). Two of the three issue-21 branches have no PR, and the newest one (`-2050`) supersedes PR #89.
- **Stale or inconsistent on `main`:**
  - CLAUDE.md says eufi drives the arm and that 76zj has "No cameras attached yet";
  - the Teleoperation README still says "not yet run on the real arm" ([PR #73 summary](https://github.com/vertical-cloud-lab/robot-arms/pull/73#issuecomment-6846316524));
  - mpzy's own `~/Up_and_Down.py` is an old copy that calls `EnablePiper()` (which sends the gripper hunting for its zero), while recovery hints point at it;
  - mpzy's `~/piper-venv` lacks numpy and OpenCV, which PR #83 needs;
  - teleop from `main` gets no mpzy video until PR #81 merges.
- **Divergence:** two diverging copies of `piper_pick_tape.py` (PR #20 vs the #30 branch).
- **Data hygiene:** PR #90 put ~72.8 MB of raw Edison JSON on `main` (A4 notes). Print records live only on bare branches.

### f6. Things that failed outright

- Stage-3 tape grasps on 10-10 and 10-15 (one squeeze-out, one miss). The 10-16 off-plane carry dropped the roll (gripper overheat). Seek run 2 missed by ~65 mm (J1 jump) ([PR #20](https://github.com/vertical-cloud-lab/robot-arms/pull/20#issuecomment-6207992243)).
- The #54 roll jam at −55° (16 A). Run 2 stopped after 1/3 cycles (J3 4.4 A). Run 3 scratched the J2 housing ([#54](https://github.com/vertical-cloud-lab/robot-arms/issues/54)).
- The E-stop test not done (11-06). The relay left on after 11-14.
- The wrist-mount fit failures (three CAD fixes) and the stringy sleeve shells (one reprint) (A1, A4 notes). A print run timed out waiting on a CAD round (180-minute limit, since raised to 360) ([#57](https://github.com/vertical-cloud-lab/robot-arms/issues/57#issuecomment-6591457131)).
- #24's camera-vs-joint check never ran, because the arm was off the bus and then the camera was removed. The synthetic tracker floor was ~4 mm ([#24](https://github.com/vertical-cloud-lab/robot-arms/issues/24#issuecomment-6157460585)).
- The A1 mini's stalled cloud job held its bed at 65 °C for ~8 days. Remote stop was impossible over LAN ([#86](https://github.com/vertical-cloud-lab/robot-arms/issues/86#issuecomment-7174926218)).
- Automation run failures:
  - runs ran out of usage credits or seat limits mid-task (#21 on 11-27, #85 on 11-25);
  - Claude twice misread a silent bus as "arm off" ([PR #25](https://github.com/vertical-cloud-lab/robot-arms/pull/25#issuecomment-6179239663));
  - on 10-21 and 11-04 a process listing or command echoed a token or a sudo password into the CI console (not posted; A3 notes).
- In simulation: AMP1 `tape_to_shelf` ep0 (no release), and print removal only by pushing. The twin's 176 g iron auger does not seat ([PR #77](https://github.com/vertical-cloud-lab/robot-arms/pull/77#issuecomment-6873360279)).


## (g) The WRTG 316 proposal: argument, framing and selected sources

**Who and what.** jss265 is writing a research proposal and paper for WRTG 316 (Technical Writing, BYU, Fall 2026) on the lab's PiPER work; "the paper may later feed into a manuscript" ([`docs/wrtg-316/README.md`](https://github.com/vertical-cloud-lab/robot-arms/blob/41a21f8/docs/wrtg-316/README.md)). The instructor approved AI use by e-mail on 2026-10-28 (Edison Scientific queries for finding sources; Claude Code "steering sessions"), on condition that sessions be public as issues: WRTG-Proposal-0 ([#63](https://github.com/vertical-cloud-lab/robot-arms/issues/63)), -1 ([#64](https://github.com/vertical-cloud-lab/robot-arms/issues/64), [PR #90](https://github.com/vertical-cloud-lab/robot-arms/pull/90), merged 2026-11-27), -2 ([#65](https://github.com/vertical-cloud-lab/robot-arms/issues/65), LaTeX, open). Deadlines: proposal due 2026-11-04; final report due 2026-12-01 ([`proposal questions.md`](https://github.com/vertical-cloud-lab/robot-arms/blob/41a21f8/docs/wrtg-316/Proposal/user%20context/proposal%20questions.md), Q0.7).

**State of the text on main.** `Proposal/main.tex` is titled *When Is a Low-Cost Arm Good Enough?* but its body is still "DEMO CONTENT: placeholder text to test the setup", and `refs.bib` holds two demo entries (Lamport, Knuth) ([`main.tex`](https://github.com/vertical-cloud-lab/robot-arms/blob/41a21f8/docs/wrtg-316/Proposal/main.tex)). The database-search plan (Scopus, Engineering Village, IEEE Xplore; searches S1–S6) has an empty search log ([`database-searches.md`](https://github.com/vertical-cloud-lab/robot-arms/blob/41a21f8/docs/wrtg-316/Proposal/database-searches.md)). The substance is in `proposal questions.md` (jss265's answers) and the Edison selection.

**How the topic evolved.**
- On 2026-10-28 jss265 proposed "Evaluating the Potential of Low-Cost Robotic Arms for Self-Driving Laboratories", with four themes: vision-guided manipulation, reliability during repeated lab tasks, AI-generated CAD for grippers and fixtures, and AI-assisted programming ([PR #50](https://github.com/vertical-cloud-lab/robot-arms/pull/50#issuecomment-6457373124)).
- Claude's reply tied the first two themes to the #21 reliability paper and said AI-generated CAD "is a separate paper". It suggested narrowing to "can an arm under $5,000 be made reliable enough for a self-driving lab, and what does that cost?" ([comment](https://github.com/vertical-cloud-lab/robot-arms/pull/50#issuecomment-6457378493)).
- sgbaird: "That's spot on" ([comment](https://github.com/vertical-cloud-lab/robot-arms/pull/50#issuecomment-6474908856)). This is the only PI feedback on the topic in the repo; no instructor comments or grade appear.

**Scope shift: from measuring to choosing tests.** Q0.2: "Not right now. The origional plan was to run my own tests to compare with industry standard. However, the focus of the paper has shifted to discovering the tests that determine the value of a robot arm in an SDL. In otherwords, discovering the very tests we will eventually run with our PiPER and SO-101 arms." Q1.3.4/Q2.1.3: no lab data; "only a literature review designs to systemmatically scope out benchmarks for testing and evaluate the the grading process for arm purchasing based on required tasks."

**Research question and thesis.**
- Main question (Q1.3.1): "What tests can we run with our PiPER robot arm that will compare it's value to industry standard arms used as automated manual manipulators in self driving labs?" Candidate framings (Q1.2.1): "What is the best way to analyze a robotic arm setup for SDL use?", "How do low-cost robotic arms compare to industrial standards?", "Can many industrial workflows me modified so that low-cost robot arms can fulfill the same purpose?"
- Larger question (Q1.3.6): "can affordable automation democratize self driving lab research?"
- **Thesis: not yet written** (Q1.3.2 "Help me come up with this."); position "Unknown" (Q1.4.3); counter-arguments not yet listed (Q1.4.4). Self-declared bias (Q3.1.6): leaning "towards the idea that affordable robotic arms can serve as useful automated manual maniplulators".
- Unique angle (Q1.4.5): "I am building a lab from scratch, where we have valued the cost-per-task which is often not the priority in expensive RnD." Reader's action (Q1.4.6): test their own arms against the chosen benchmarks.
- Working title alternatives (Q0.1): "Comparing Low-Cost Robot Arms to Industry Standards", subtitle "Research Paper Proposal".
- **Claude-drafted thesis in the LaTeX proposal (2026-11-28, unmerged branch `claude/issue-65-20261128-0218`, no PR):** "Neither price nor datasheet repeatability can tell a lab whether an arm is good enough for an SDL. A short set of task-level tests can: independently measured repeatability, accuracy at each station after recalibrating, each task's tolerance for error, success rate over repeated trials with a confidence bound, and cost per successful task. Judged by those tests, low-cost arms are good enough for much of the routine transfer work that labs now buy industrial arms to do." ([`sections/1-introduction.tex`](https://github.com/vertical-cloud-lab/robot-arms/blob/cf84db5/docs/wrtg-316/Proposal/sections/1-introduction.tex), lines 59–64)
  - The draft's main question: "Which published tests best show whether a robot arm can serve as an SDL's automated manual manipulator, and how should a low-cost arm's results be compared with an industrial arm's?"
  - Position: "Low-cost arms can be good enough for much of an SDL's station work, but only task-level tests, not a price tag or a datasheet, can show which tasks."
  - Counter-arguments: imprecision/unreliability (Rupp, Wattoo), 1.6–3.5× slower than a person (Rupp), special-purpose automation being more efficient (Tom), and datasheets already being the standard.
  - Scope excludes mobile bases, liquid handlers, learning-based control and safety certification; testing the PiPER and SO-101 is "next semester's work".
  - Status: 9 pages (~6.5 of body vs the ~4–5 asked), 7 `% CHECK:` markers, no figures, database searches not run ([#65](https://github.com/vertical-cloud-lab/robot-arms/issues/65#issuecomment-7232269211)).
  - The run also flagged that Tom et al. 2024 may list sgbaird as a co-author, a possible source-bias disclosure (unverified).

**The "automated manual manipulator" framing.** Defined in the run-2 Edison context ([`edison/README.md`](https://github.com/vertical-cloud-lab/robot-arms/blob/41a21f8/docs/wrtg-316/edison/README.md)): "one arm that does the hands-on work a person would otherwise do: it moves from station to station (for example a pipetting gantry, a powder doser, a balance, vial and plate racks), recalibrates itself at each station using a calibration square (a square fiducial target such as an AprilTag, or a square fixture at a known position), and takes on several new automated tasks. The term is ours". It prices the PiPER at "about $2k" and SO-101 leader/follower at "about $200". Edison run 2 q2: "no publication was found whose sole purpose is to define or run tests that evaluate, compare, or select a robot arm for use as an automated manual manipulator in a self-driving or automated laboratory", the term did not appear in any retrieved publication, and the usual term is "mobile manipulator" ([`selection.md`](https://github.com/vertical-cloud-lab/robot-arms/blob/41a21f8/docs/wrtg-316/edison/selection.md), "Closest to your exact question").

**Edison runs.** Run 1 (2026-11-04): 8 `LITERATURE_HIGH` queries (field development; repeatable benchmarks; low-cost vs industrial; case against; lab workflows/AprilTag accuracy; reliability statistics; learned vs scripted; visualizing repeatability), all successful. Run 2 (2026-11-27, PR #90): 9 queries re-centred on the automated manual manipulator (field growth; same-purpose papers; arm categories and selection metrics; station calibration; repeatable benchmarks; low-cost vs industrial; case against; reliability and cost per task; new tasks at stations), all successful ([`edison/README.md`](https://github.com/vertical-cloud-lab/robot-arms/blob/41a21f8/docs/wrtg-316/edison/README.md)). Gaps the selection names: no full cost-per-task figure for a lab arm was found; Volk & Abolhasani report "71% of the studies reported no data quantifying the precision of the automated experimental system" (17 studies, none arm-centred).

**Selected sources** ([`Final_Selection.md`](https://github.com/vertical-cloud-lab/robot-arms/blob/41a21f8/docs/wrtg-316/edison/Final_Selection.md), committed 2026-11-27 as "added final_selection sources"; quotes checked in [`selection.md`](https://github.com/vertical-cloud-lab/robot-arms/blob/41a21f8/docs/wrtg-316/edison/selection.md)):

| # | Role | Source | DOI | Key numbers the selection extracts |
|---|---|---|---|---|
| 1 | Review of Literature | Zhou, Veeramani, Munguia-Galeano, Fakhruldeen, Cooper, "Localization, inspection, and reasoning (LIRA) module for autonomous workflows in self-driving laboratories," *Commun. Chem.* 8:384 (2025) | 10.1038/s42004-025-01770-1 | KUKA KMR iiwa; 20 mm ArUco 2.42 mm / 3.46° unfiltered, 1.51 mm / 1.54° filtered; 75 mm ArUco 1.02 mm / 1.01°; cube touch 0.92 mm / 0.90°; ~5 s vs ~53 s per calibration; 600/600 pickups and insertions over 8 h; 36.1 % less arm time |
| 2 | Review of Literature | Chajón, Reiff-Stephan, Günther, "Photogrammetric characterization of robot positioning accuracy and repeatability," *Robotics* 15(5):86 (2026) | 10.3390/robotics15050086 | UR3, Raspberry Pi camera + ArUco, 30 reps × 5 poses; camera RPp 0.147–0.229 mm (linear), 0.195–0.265 mm (axial); dial indicator 0.0109 mm vs datasheet 0.03 mm; 0.103 mm/px |
| 3 | Annotated bib. | Burger et al., "A mobile robotic chemist," *Nature* 583:237–241 (2020) | 10.1038/s41586-020-2442-2 | 688 experiments over 8 days; six-point cube touch calibration ±0.12 mm, ±0.005°; vials/cartridges need better than 0.5 mm |
| 4 | Annotated bib. | Tom et al., "Self-driving laboratories for chemistry and materials science," *Chem. Rev.* 124:9633–9732 (2024) | 10.1021/acs.chemrev.4c00055 | SDL hardware price classes: High (~$1M), Medium (~$10K), Low ($100–2K) |
| 5 | Annotated bib. | Harazono, Shimono, Hata, Mitsuyama, Horinouchi, "Evaluation of microplate handling accuracy for applying robotic arms in laboratory automation," *SLAS Technol.* 29:100200 (2024) | 10.1016/j.slast.2024.100200 | Dobot M1 Pro SCARA; two dial gauges; 125 loaded transfers per speed; IQR x/y 0.020/0.006 mm (high speed), 0.034/0.014 mm (low); y failures rose past Δy 2.190 mm; ~1/3 failed at x 1.90 mm |
| 6 | Annotated bib. | Ferraguti, Pertosa, Secchi, Fantuzzi, Bonfè, "A methodology for comparative analysis of collaborative robots for Industry 4.0," DATE 2019, pp. 1070–1075 | 10.23919/DATE.2019.8714830 | KUKA LWR 4+, UR5, Franka Panda; robot-, application- and user-dependent criteria |
| 7 | Annotated bib. | Rupp, Peschke, Köppl, Drissner, Zuchner, "Establishment of low-cost laboratory automation processes using AutoIt and 4-axis robots," *SLAS Technol.* 27:312–318 (2022) | 10.1016/j.slast.2022.07.001 | Dobot Magician ~€1.5k, 0.5 kg, 320 mm, 0.2 mm advertised; matched a trained person's accuracy but 3.5× (pipetting), 1.6× (AAS autosampler), 3.0× (inoculation) slower |
| 8 | Annotated bib. (counter-argument) | Wattoo et al., "RABIT, a robot arm bug intervention tool for self-driving labs," IEEE/IFIP DSN 2024, pp. 353–361 | 10.1109/DSN58291.2024.00043 | ~3 cm error putting two educational arms in one frame; silent failure on an infeasible command; collision without an alarm |
| 9 | Annotated bib. (statistics) | Vincent, Nishimura, Itkina, Shah, Schwager, Kollar, "How generalizable is my behavior cloning policy? ...," *IEEE RA-L* 9:8619–8626 (2024) | 10.1109/LRA.2024.3445635 | Tighter-than-Clopper–Pearson lower bound; invalid practices (e.g. running until enough favourable outcomes) |
| 10 | Found by hand | Doloi et al., "Democratizing self-driving labs: advances in low-cost 3D printing for laboratory automation," *Digit. Discov.* 4:1685–1721 (2025) | 10.1039/D4DD00411F | — |
| 11 | Found by hand | Quigley, Asbeck, Ng, "A low-cost compliant 7-DOF robotic manipulator," ICRA 2011, pp. 6051–6058 | 10.1109/ICRA.2011.5980332 | — |

"Closest to your exact question" and swap candidates also listed in `selection.md`: Salazar-Villacis & Benyahia, ADePT framework, *Commun. Chem.* 9:99 (2026), doi:10.1038/s42004-026-01932-9; Volk & Abolhasani, *Nat. Commun.* 15:1378 (2024), doi:10.1038/s41467-024-45569-5; Pagani et al., *Robotics* 10:45 (2021), doi:10.3390/robotics10010045 (touch 5-point 0.12 mm vs single-fiducial camera method up to 1.42 mm on a Sawyer); Ginsburg et al., doi:10.1145/3624062.3624615; Hifi et al., doi:10.1088/1361-6501/adf3d4; Pollák et al., doi:10.1177/1687814020972893; Franzese et al., *Commun. Eng.* 5:138 (2026), doi:10.1038/s44172-026-00633-4 (backlash limits calibration of planetary-gear arms); Dembski et al., *Sci. Rep.* 13:11440 (2023), doi:10.1038/s41598-023-38535-6 (up to 75 % personnel-cost cut, staff time only); Thieme et al., *SLAS Technol.* 29:100180 (2024), doi:10.1016/j.slast.2024.100180 (unchecked). Not checked: LabRobFail (arXiv 2607.23704), ArmnetBench (arXiv 2607.24481), Johns & Gongora DOE report doi:10.2172/3684119 (Edison: SO-101 placed vials 34/36 with ACT).

## (h) What these threads update, contradict or narrow in the earlier issue-#1 recommendations

### 1. "Arm as transfer layer, with fixtures and fiducial correction"

- **Confirmed and operationalized.** The lab's flagship study (#21) tests exactly this pairing, with the lead-in dock as the fixture and wrist-camera AprilTags as the correction, against a 99 %-per-transfer target. It rests on the PR 272 error budget (±0.64 mm RSS, ±1.15 mm worst case), set against a tight pocket's ~±0.6 mm capture and a 3 mm lead-in's ~±3 mm ([PROTOCOL.md §1](https://github.com/vertical-cloud-lab/robot-arms/blob/c8b3408/docs/protocol/PROTOCOL.md)). The WRTG framing restates it as station-to-station recalibration from a "calibration square" ([edison/README.md](https://github.com/vertical-cloud-lab/robot-arms/blob/41a21f8/docs/wrtg-316/edison/README.md)). Its anchor source (Zhou 2025, LIRA) shows ~1 mm/1° with 75 mm ArUco markers, against 2.4 mm/3.5° with 20 mm markers, on an industrial arm.
- **Narrowed.**
  - The first target is a *mock-up* CubXL-geometry dock (no CubXL is in or near the cell) with printed dummy vials.
  - Carriers must point at J1.
  - The protocol itself expects correction to help single vials but not guarantee 99 %, because the ±0.5 mm in-gripper term remains.
  - Tag-only correction at realistic tag sizes (≥25 mm; 10 mm unreadable) is likely good to ~1–2.5 mm. That is consistent with lead-in fixtures doing the precision work and vision doing coarse alignment (a reading of LIRA, the tag tests and PR #77's "fixed camera ~1 cm, wrist camera finishes").
- **Contradicted in practice by the team's priority.** The team's semester goal (jss265) is the arm as a *tool/maintenance agent* for the powder doser (auger removal and replacement), not a transfer layer between instruments ([#42](https://github.com/vertical-cloud-lab/robot-arms/issues/42)). Auger extraction is force-limited (clips estimated at 12–40 N against ~15 N at the flange), not pose-limited. The two thrusts compete for the same arm and end effector (HW10).

### 2. "First measured MTBI / intervention-rate dataset for a low-cost arm in an SDL"

- **Still the plan, but demoted and delayed.** In #21, MTBI is a secondary outcome (Kaplan–Meier, restricted mean, τ = 300). The primary outcome is per-transfer success with exact bounds, and failures are coded with LabRobFail. The power analysis calls MTBI "Imprecise by design": at 1 intervention per 100 transfers over 600 transfers, the 95 % interval is 46–272.
- **Timing and setting.** The realistic first counted block is 2027-03-05 and the results paper 2027-06-25. Data will come from a mock-up deck in an attended cell (a person at the E-stop for every block; ~660 reach-in resets in E2), not from an operating SDL. A claim of "first MTBI for a low-cost arm *in an SDL*" would therefore need care.
- **Supporting gap evidence** from the WRTG search:
  - Volk & Abolhasani: "71% of the studies reported no data quantifying the precision of the automated experimental system";
  - run 2 q8: SDL papers mostly report raw counts without confidence bounds;
  - no publication defines tests for choosing an arm for this role ([selection.md](https://github.com/vertical-cloud-lab/robot-arms/blob/41a21f8/docs/wrtg-316/edison/selection.md)).
- **What intervention data actually exists:** informal and negative. Examples are the 11-14 J4 over-current stop with the relay left on for 11.5 days, J1 jumps, gripper overheat, and ≥6 "first try didn't move" starts. None of it is logged in a form that could be analysed.

### 3. "Metrology of a sub-$5k arm"

- **Kept as registration B (E3/H4):** ISO 9283-style RP at 5 poses × 30 cycles × 2 payloads, testing AgileX's 0.1 mm claim ("None has been measured here").
- **Blocked:** the fixture (U ≤ 0.025 mm; three 0.001 mm dial indicators suggested) "Doesn't exist" and has no owner. ISO 9283 §6.8 is unchecked. Power: "meets 0.10 mm" only 54 % of the time if the true RP is 0.08 mm, because instrument noise inflates RP.
- **What would get there sooner:**
  - The WRTG picks supply cheaper, copyable protocols. Chajón 2026 (Pi camera + dial indicators on a UR3) found camera RPp 0.15–0.27 mm against a dial-indicator 0.011 mm, so a camera alone cannot test a 0.1 mm claim. Harazono 2024 (two dial gauges, 125 loaded transfers, imposed offsets to find a task's tolerance) parallels #21's E2 capture envelope ([selection.md](https://github.com/vertical-cloud-lab/robot-arms/blob/41a21f8/docs/wrtg-316/edison/selection.md)).
  - Measurements the metrology agenda should absorb first: **joint-zero stability** (J1 jumps of ~7.95° multiples, a 15.2° re-zero, gate HW8), **settling at power-off** (0.15–1.55° drops; J3 rest spread ~1.7°), and **tracking error** (AMP1's simulated deadbands; untested on the real arm).

### 4. "Vision-corrected primitives"

- **Planned, not started on hardware.** The AT condition of #21 and PR #83's `vision.py`/`calibrate.py` are both simulation-only.
- **Prerequisites missing:** a camera calibration, a working wrist camera (offline since 11-11; HQ lens unfocused), and printed tags or cubes.
- **What the November work narrows:**
  - joint multi-tag solving beats per-tag estimation (0.1° vs 2.6° for a plane);
  - cubes remove pose flips;
  - two tags per object give 0.2–1.6 mm in simulation against 5–19 mm with one;
  - rule R3 sets tags of at least 25 mm, with 5 frames per look and a 6 mm / 6° correction cap.
- **New alternative: agentic correction (AMP1).** In simulation the agent measured and compensated joint deadbands, reaching ~0.5 mm insertion into a 2.5 mm-clearance pocket, without being prompted to calibrate. It is slow (minutes per task; the paper's real successes averaged 280 s) and untested on hardware. It is a complement for one-off or recovery tasks, not a substitute for fixtures in a 99 % campaign.

### 5. "An eight-primitive sandbox, from vials to lid press-fit to powder-atomizer transfer"

- **Reshaped by the lab's own workflows.** Lid press-fit appears nowhere in the Oct–Nov threads.
- **The physical sandbox so far is one object:** a tape roll picked and placed on shelves (10-10 → 10-16).
- **The task list that actually emerged:**
  1. CubXL carrier and single-vial loading (#21, planned);
  2. auger pick-and-place, 3 × 30 (PR #83, SIM);
  3. auger removal and replacement (#42/#44 CAD and prints; PR #77 SIM);
  4. A1 mini print removal (PR #77 SIM, PR #87 SIM);
  5. atomizer charging (PR #87, SIM, running 11-28);
  6. tape to shelf (#30, done on hardware; also AMP1 SIM).
- **Atomizer chamber cleaning and CubXL module replacement** were the first workflows the team discussed ([#6](https://github.com/vertical-cloud-lab/robot-arms/issues/6)).
- **Constraints found that any sandbox must respect:**
  - no top-down grasp above ~0.10 m (J5 ±70°);
  - J6 ~90° window (wrist cable);
  - J1 −20…+60° (A1 mini);
  - carriers must point at J1;
  - the doser stands too tall (lower it 120 mm);
  - payload ~0.5–1.0 kg after the gripper and the unweighed wrist pod.

### 6. "Generative gripper design loop"

- **The research project was not started.** PR #8's ranked project #1, a closed-loop spec → CadQuery → FDM → robot test → redesign loop (≥1,000 cycles per finalist, 9–18 months), has had no activity since import.
- **What did happen** is an informal human-in-the-loop version: six Claude CAD rounds of auger sleeves, a finger fixture and a slider, driven by jss265 and claytonblodgett feedback and printed on the A1 mini ([PR #44](https://github.com/vertical-cloud-lab/robot-arms/pull/44)). It had no measured manipulation endpoint.
- **A cautionary result from it:** the printed sleeves stall the gripper's homing (motor 7 never enabled) and cap its span at 45.6–108.6 mm, so end-effector changes are now configuration changes the campaign must control.
- **Scoping:** Claude scoped AI-generated CAD as "a separate paper" from the reliability work ([PR #50](https://github.com/vertical-cloud-lab/robot-arms/pull/50#issuecomment-6457378493)), and sgbaird endorsed that scoping ("That's spot on").

### 7. "Safety: hardwired E-stop; no unattended Al powder in the first 90 days"

- **E-stop: partly met.**
  - A plug-in POWERTEC magnetic-switch E-stop cuts the arm's mains without software ("hardwired" in that sense), installed by 10-26.
  - It is **not safety-rated**, it is **untested**, and its position relative to the software relay is unrecorded.
  - The relay adds a second, software-controlled cut that drops the arm on any mpzy reboot.
  - Issue #1's own Q4 advice ("The E-stop chain has to be hardwired… must not pass through MQTT, Tailscale, a Raspberry Pi or the cloud", [#1](https://github.com/vertical-cloud-lab/robot-arms/issues/1#issuecomment-6103303845)) is satisfied for the E-stop itself, but not verified.
- **Unattended operation: consistent so far, but the direction is shifting.**
  - The draft SOP allows no unattended runs.
  - The 2026-11-28 addendum keeps "no for now" but writes 12 conditions (U1–U12, including interlocked guarding) for when unattended runs become a goal. That was at sgbaird's request "Especially for remote, unattended operation" ([PR #23](https://github.com/vertical-cloud-lab/robot-arms/pull/23#issuecomment-7237213210)).
  - The team's stated purpose is "constantly available robots for remote use" ([#18](https://github.com/vertical-cloud-lab/robot-arms/issues/18#issuecomment-6091774765)).
- **Powder: not yet in scope.**
  - The safety drafts leave powders out ("The atomizer's metal powders belong to its own procedures").
  - The imported glovebox study warns "Do not put a robot in an acrylic box" (NFPA 484, Al/Mg powder static) ([PR #11](https://github.com/vertical-cloud-lab/robot-arms/pull/11)).
  - The first arm-atomizer interaction is a simulated AMP1 `atomizer_charge` scene (11-28).
  - The no-unattended-Al-powder rule is therefore not contradicted, but a written arm-and-powder rule is still missing from the SOP before any powder work.
- **Additions the threads justify:** test the E-stop (SF2); read the collision level without zeroing it; measure baseline currents before current-based collision checks (M3); park before any planned power-off; check at session end that the relay is off; and decide whether mpzy can carry the arm, the relay and a livestream at once.

### 8. Directions the earlier recommendations did not anticipate

- **Teleoperation as a working capability:** SO-101 leader, 34 ms RTT, recording built in. It is the cheapest route to demonstration datasets and to supervised remote operation, and it already runs on the real arm.
- **Simulation-first development:** the MuJoCo twin with a `PiperSDK` facade, and AMP1's MuJoCo PiPER. These are already producing design feedback for other instruments (doser height and collar) and reach maps for the A1 mini.
- **Agentic control (AMP1):** frontier-model-written control code with no skill library, which also bears on the protocol's rule that an `@claude` run never starts counted blocks.
- **Infrastructure:** face-blurred public livestreams, and remote power with park-before-off. These suit the "cloud lab" thesis, but they share one 1 GB Pi with arm control.
- **The arm is on loan,** so campaign wear (~6,000 transfers, ~750 power cycles) needs the lender's consent (HW9).


## Appendix: branches with relevant work but no PR (from `git ls-remote`, 2026-11-28)

| Branch | Head | What it holds |
|---|---|---|
| `claude/issue-21-20261127-2050` | c8b3408 | **Latest CubXL preregistration** (PR #89's branch + 7 commits: power rerun, D11 stop rates, consistency fixes, final summary). Supersedes PR #89 ([#21](https://github.com/vertical-cloud-lab/robot-arms/issues/21#issuecomment-7227895694)) |
| `claude/issue-21-20261010-2326` | 9652c43 | Protocol v1 (785 lines, never registered) |
| `claude/issue-65-20261128-0218` / `-0727` | cf84db5 / bd8cf97 | WRTG 316 LaTeX proposal draft (9 pp; `-0727` adds the built PDF) |
| `claude/issue-30-20261015-2243` | 91b91ad | #30 tape-to-shelf variant of `piper_pick_tape.py` (966 lines) + run trace |
| `claude/issue-54-20261030-0231/-0314/-0402/-0436` | be3f7bc…56eef28 | The four #54 `Up_and_Down.py` iterations with run records (traces, GIFs); the logic later landed on `main` via PR #68 |
| `claude/issue-61-*` (7 branches) | f206832…b45ba0e | Livestream iterations; the last one is PR #81 |
| `claude/issue-24-20261013-2335`, `-1347`, `-2052` | fb90d85, 24a03c2, af6e7a6 | Camera-calibration twin and tools, camera placement study, corner-post fixture CAD (all later imported into PR #40) |
| `claude/issue-4-20261023-1814` | 27db133 | HQ-housing clearance fix for the wrist pod (merged into PR #10's branch) |
| `claude/issue-1-20261010-2326` | 98fb17c | Edison 6DOF Q1–Q4 answers (incl. Q4 safety/control plane) and `scripts/edison_6dof.py` |
| `claude/issue-199-20260915-0844`, `claude/issue-233-20260925-0536`, `claude/issue-239-20261007-2023` | 9644beb, 622afa2, 6416cd1 | Imported byu-vcl work: early #1 scan, wrist-camera selection report (overridden), 6 mm vs 16 mm lens comparison (ported into PR #10) |
| `claude/issue-45-*`, `-52-*`, `-53-*`, `-55-*` | various | Print-job records (STLs/3MFs, frames, `print.json`) for the camera pod, clamp heads, sleeves, fixture and slider |
| `claude/issue-66-20261105-0045` | 7d05e62 | `docs/robot-arm-supplies.md` (ChArUco boards, USB-C adapters) |
| `claude/issue-72-20261112-0104` | 2fd52f8 | CLAUDE.md record of jss265's SSH key on mpzy (not on `main`) |
| `claude/issue-62-20261103-1952` | 103c623 | One fixed-camera still for the 11-03 demo check |
| `claude/issue-85-20261125-2125` | 1ebd2c8 | First (credit-limited) AMP1 run; superseded by PR #87's branch |


## Appendix: index of every issue and PR (state as of 2026-11-28)

| # | Type | State | Author | Created | Last updated | Title | Branch |
|---|---|---|---|---|---|---|---|
| [1](https://github.com/vertical-cloud-lab/robot-arms/issues/1) | issue | open | sgbaird | 2026-09-08 | 2026-11-28 | High-impact, timely projects with vision-enabled 6DOF robotic arm workflows |  |
| [2](https://github.com/vertical-cloud-lab/robot-arms/issues/2) | issue | open | jss265 | 2026-09-22 | 2026-10-22 | 6DOF Arm - Enclosure Design |  |
| [3](https://github.com/vertical-cloud-lab/robot-arms/issues/3) | issue | open | jss265 | 2026-09-25 | 2026-10-09 | 6DOF Arm - Computer Vision |  |
| [4](https://github.com/vertical-cloud-lab/robot-arms/issues/4) | issue | open | sgbaird | 2026-09-26 | 2026-10-23 | AgileX PiPER camera mount with Pi 5 and up to two cameras, one of them being an HQ camera |  |
| [5](https://github.com/vertical-cloud-lab/robot-arms/issues/5) | issue | open | jss265 | 2026-10-01 | 2026-10-09 | 6DOF Arm - PiPER ROS |  |
| [6](https://github.com/vertical-cloud-lab/robot-arms/issues/6) | issue | open | jss265 | 2026-10-02 | 2026-10-16 | 6DOF Arm - Meeting Notes |  |
| [7](https://github.com/vertical-cloud-lab/robot-arms/issues/7) | issue | open | jss265 | 2026-10-05 | 2026-10-09 | 6DOF Arm - PiPER first launch (User Manual) |  |
| [8](https://github.com/vertical-cloud-lab/robot-arms/pull/8) | PR | open | sgbaird | 2026-10-09 | 2026-10-09 | Gripper/end-effector design, generative CAD, and org survey (#1) | `claude/issue-199-20260915-0846` |
| [9](https://github.com/vertical-cloud-lab/robot-arms/pull/9) | PR | open | sgbaird | 2026-10-09 | 2026-10-28 | Robot arm enclosure (companion issues #2 and #38) | `claude/issue-229-20261001-2322` |
| [10](https://github.com/vertical-cloud-lab/robot-arms/pull/10) | PR | open | sgbaird | 2026-10-09 | 2026-11-10 | AgileX PiPER wrist camera mount: Pi 5, HQ Camera and Camera Module 3 Wide | `claude/issue-239-20260926-2347` |
| [11](https://github.com/vertical-cloud-lab/robot-arms/pull/11) | PR | open | sgbaird | 2026-10-09 | 2026-10-09 | Add glovebox research focused on robotic arm integration | `claude/glovebox-robotic-arm-integration` |
| [12](https://github.com/vertical-cloud-lab/robot-arms/pull/12) | PR | open (draft) | sgbaird | 2026-10-09 | 2026-10-09 | Add 6DOF robotic arms and mobile bases procurement guide | `copilot/research-6dof-robots` |
| [13](https://github.com/vertical-cloud-lab/robot-arms/issues/13) | issue | open | sgbaird | 2026-10-09 | 2026-10-09 | Read-only check: CI access to the arm Pi (rpi-5-eufi) |  |
| [14](https://github.com/vertical-cloud-lab/robot-arms/pull/14) | PR | open | app/claude | 2026-10-09 | 2026-10-09 | Record read-only inventory of the arm Pi in CLAUDE.md | `claude/issue-13-20261009-2219` |
| [15](https://github.com/vertical-cloud-lab/robot-arms/issues/15) | issue | open | jss265 | 2026-10-09 | 2026-10-09 | PiPER First Claude Launch |  |
| [16](https://github.com/vertical-cloud-lab/robot-arms/pull/16) | PR | open | jss265 | 2026-10-09 | 2026-10-09 | Add PiPER up/down script and record the arm Pi setup | `claude/issue-15-20261009-2246` |
| [17](https://github.com/vertical-cloud-lab/robot-arms/pull/17) | PR | merged | jss265 | 2026-10-09 | 2026-10-09 | Add install guide. Manual installation instructions for windows PC. | `add-manual-install-guide` |
| [18](https://github.com/vertical-cloud-lab/robot-arms/issues/18) | issue | closed | jss265 | 2026-10-09 | 2026-10-26 | Procure E-stop for PiPER arm |  |
| [19](https://github.com/vertical-cloud-lab/robot-arms/issues/19) | issue | open | jss265 | 2026-10-09 | 2026-10-10 | PiPER to pick up the tape |  |
| [20](https://github.com/vertical-cloud-lab/robot-arms/pull/20) | PR | open | jss265 | 2026-10-10 | 2026-10-16 | Tape pick (#19): streamed straight-line descent, effort-checked grip, softer park | `claude/issue-19-20261010-0111` |
| [21](https://github.com/vertical-cloud-lab/robot-arms/issues/21) | issue | open | sgbaird | 2026-10-10 | 2026-11-27 | Reliability campaign: pre-registered protocol for loading the CubXL |  |
| [22](https://github.com/vertical-cloud-lab/robot-arms/issues/22) | issue | open | sgbaird | 2026-10-10 | 2026-10-10 | Hazard analysis and SOP for the PiPER cell (docs only) |  |
| [23](https://github.com/vertical-cloud-lab/robot-arms/pull/23) | PR | open | sgbaird | 2026-10-13 | 2026-11-28 | Draft PiPER cell hazard analysis, SOP and checklist (docs/safety) | `claude/issue-22-20261010-2326` |
| [24](https://github.com/vertical-cloud-lab/robot-arms/issues/24) | issue | open | sgbaird | 2026-10-13 | 2026-10-24 | Calibrate robot position based on the taped camera |  |
| [25](https://github.com/vertical-cloud-lab/robot-arms/pull/25) | PR | open | sgbaird | 2026-10-14 | 2026-10-27 | Calibrate robot position based on the taped camera (companion to issue 24) | `claude/issue-24-20261014-1635` |
| [26](https://github.com/vertical-cloud-lab/robot-arms/pull/26) | PR | merged | sgbaird | 2026-10-15 | 2026-10-15 | Wire in the upload-only YouTube token | `youtube-upload-token` |
| [27](https://github.com/vertical-cloud-lab/robot-arms/pull/27) | PR | merged | sgbaird | 2026-10-15 | 2026-10-15 | Send prints only through an approval-gated `@claude-print` workflow | `claude/bambu-print-approval` |
| [28](https://github.com/vertical-cloud-lab/robot-arms/issues/28) | issue | open | jss265 | 2026-10-15 | 2026-10-15 | Sandbox Scripts |  |
| [29](https://github.com/vertical-cloud-lab/robot-arms/pull/29) | PR | open | jss265 | 2026-10-15 | 2026-10-15 | Up_and_Down.py: raise and lower the PiPER from its rest pose (#28) | `claude/issue-28-20261015-2159` |
| [30](https://github.com/vertical-cloud-lab/robot-arms/issues/30) | issue | open | claytonblodgett | 2026-10-15 | 2026-10-15 | Move tape onto shelf |  |
| [31](https://github.com/vertical-cloud-lab/robot-arms/pull/31) | PR | merged | sgbaird | 2026-10-21 | 2026-10-21 | Reach the camera Pi (rpi-5-76zj) from CI alongside the arm Pi | `tailscale-camera-pi` |
| [32](https://github.com/vertical-cloud-lab/robot-arms/pull/32) | PR | merged | sgbaird | 2026-10-21 | 2026-10-21 | tailscale-check: check the camera Pi even when the arm Pi is down | `tailscale-check-independent` |
| [33](https://github.com/vertical-cloud-lab/robot-arms/issues/33) | issue | closed | sgbaird | 2026-10-21 | 2026-10-21 | Read-only check: CI access to the camera Pi (rpi-5-76zj) |  |
| [34](https://github.com/vertical-cloud-lab/robot-arms/pull/34) | PR | merged | sgbaird | 2026-10-21 | 2026-10-21 | Reach the second camera Pi (rpi-5-mpzy) from CI | `tailscale-camera-pi-2` |
| [35](https://github.com/vertical-cloud-lab/robot-arms/pull/35) | PR | merged | app/claude | 2026-10-21 | 2026-10-21 | CLAUDE.md: record the camera Pi as found (read-only check, #33) | `claude/issue-33-20261021-2127` |
| [36](https://github.com/vertical-cloud-lab/robot-arms/issues/36) | issue | open | sgbaird | 2026-10-21 | 2026-10-21 | Read-only check: CI access to the second camera Pi (rpi-5-mpzy) |  |
| [37](https://github.com/vertical-cloud-lab/robot-arms/pull/37) | PR | open | app/claude | 2026-10-21 | 2026-10-21 | CLAUDE.md: record the second camera Pi as found (read-only check, #36) | `claude/issue-36-20261021-2147` |
| [38](https://github.com/vertical-cloud-lab/robot-arms/issues/38) | issue | open | chris-policky | 2026-10-22 | 2026-10-22 | Built robot arm enclosure specs & photos |  |
| [39](https://github.com/vertical-cloud-lab/robot-arms/issues/39) | issue | open | sgbaird | 2026-10-22 | 2026-10-22 | Camera Pis: setup record and open items |  |
| [40](https://github.com/vertical-cloud-lab/robot-arms/pull/40) | PR | open | jss265 | 2026-10-23 | 2026-11-14 | Camera Fixturing and Calibration | `claude/issue-24-20261021-2053` |
| [41](https://github.com/vertical-cloud-lab/robot-arms/pull/41) | PR | open | app/claude | 2026-10-24 | 2026-11-28 | Wrist Pi power: extend the official 27 W supply with a 240 W USB-C extension | `claude/wrist-pi-usb-c-extension` |
| [42](https://github.com/vertical-cloud-lab/robot-arms/issues/42) | issue | open | jss265 | 2026-10-26 | 2026-10-26 | 6DOF Cooperation with Powder-Doser |  |
| [43](https://github.com/vertical-cloud-lab/robot-arms/issues/43) | issue | closed | jss265 | 2026-10-26 | 2026-10-27 | Procure Electric relay to control PiPER arm power supply |  |
| [44](https://github.com/vertical-cloud-lab/robot-arms/pull/44) | PR | open | jss265 | 2026-10-26 | 2026-11-13 | Auger swap end-effector study (#42): strategies, Onshape models, GIFs | `claude/issue-42-20261026-0528` |
| [45](https://github.com/vertical-cloud-lab/robot-arms/issues/45) | issue | closed | jss265 | 2026-10-26 | 2026-10-28 | Print Request (Camera Pod, and PVC clamps) |  |
| [46](https://github.com/vertical-cloud-lab/robot-arms/issues/46) | issue | open | jss265 | 2026-10-27 | 2026-10-27 | SO-101 leader to control PiPER |  |
| [47](https://github.com/vertical-cloud-lab/robot-arms/pull/47) | PR | closed | jss265 | 2026-10-27 | 2026-11-13 | SO-101 leader to control PiPER | `claude/issue-46-20261027-0036` |
| [48](https://github.com/vertical-cloud-lab/robot-arms/pull/48) | PR | merged | sgbaird | 2026-10-27 | 2026-10-27 | CLAUDE.md: check installed nozzle diameters before printing | `claude/nozzle-diameter-check` |
| [49](https://github.com/vertical-cloud-lab/robot-arms/issues/49) | issue | closed | jss265 | 2026-10-28 | 2026-10-28 | Research Paper WRTG 316 - Inspiration for Robotics Manuscript |  |
| [50](https://github.com/vertical-cloud-lab/robot-arms/pull/50) | PR | merged | jss265 | 2026-10-28 | 2026-11-03 | WRTG 316 research paper: inspiration for robotics manuscript | `claude/issue-49-20261028-0028` |
| [51](https://github.com/vertical-cloud-lab/robot-arms/pull/51) | PR | merged | sgbaird | 2026-10-28 | 2026-10-28 | Plate check: 90-second abort wait instead of 5 minutes | `claude/plate-wait-90s` |
| [52](https://github.com/vertical-cloud-lab/robot-arms/issues/52) | issue | closed | jss265 | 2026-10-28 | 2026-10-29 | Print Request (Re-print pod, and head cradles) |  |
| [53](https://github.com/vertical-cloud-lab/robot-arms/issues/53) | issue | closed | jss265 | 2026-10-29 | 2026-11-03 | Print Request (End Effector Sleeves, Finger Fixture, and Slider) |  |
| [54](https://github.com/vertical-cloud-lab/robot-arms/issues/54) | issue | open | jss265 | 2026-10-30 | 2026-10-30 | Gripper Pi Power Cord Problem |  |
| [55](https://github.com/vertical-cloud-lab/robot-arms/issues/55) | issue | closed | jss265 | 2026-10-30 | 2026-11-05 | Print Request (new gripper sleeves) |  |
| [56](https://github.com/vertical-cloud-lab/robot-arms/issues/56) | issue | open | sgbaird | 2026-10-30 | 2026-10-30 | Lab-o-ween demo readiness: test ping |  |
| [57](https://github.com/vertical-cloud-lab/robot-arms/issues/57) | issue | open | jss265 | 2026-11-02 | 2026-11-14 | 🏓 FIND A PING 🏓 |  |
| [58](https://github.com/vertical-cloud-lab/robot-arms/pull/58) | PR | merged | sgbaird | 2026-11-03 | 2026-11-03 | claude-print: raise the job timeout to 360 minutes | `claude-print-timeout-360` |
| [59](https://github.com/vertical-cloud-lab/robot-arms/issues/59) | issue | open | chris-policky | 2026-11-03 | 2026-11-03 | Raspberry pi 5 wiring |  |
| [60](https://github.com/vertical-cloud-lab/robot-arms/pull/60) | PR | closed | jss265 | 2026-11-03 | 2026-11-13 | IoT Relay II power control for the PiPER: wiring, arm_power.py protocol, hardware tests (#59, #57) | `claude/issue-59-20261103-0055` |
| [61](https://github.com/vertical-cloud-lab/robot-arms/issues/61) | issue | open | sgbaird | 2026-11-03 | 2026-11-20 | Livestream camera setup |  |
| [62](https://github.com/vertical-cloud-lab/robot-arms/issues/62) | issue | open | sgbaird | 2026-11-03 | 2026-11-03 | Robot arm demo |  |
| [63](https://github.com/vertical-cloud-lab/robot-arms/issues/63) | issue | closed | jss265 | 2026-11-03 | 2026-11-04 | WRTG-Proposal-0 |  |
| [64](https://github.com/vertical-cloud-lab/robot-arms/issues/64) | issue | closed | jss265 | 2026-11-04 | 2026-11-27 | WRTG-Proposal-1: Edison Scientific Queries |  |
| [65](https://github.com/vertical-cloud-lab/robot-arms/issues/65) | issue | open | jss265 | 2026-11-04 | 2026-11-28 | WRTG-Proposal-2: Using LaTex |  |
| [66](https://github.com/vertical-cloud-lab/robot-arms/issues/66) | issue | closed | jss265 | 2026-11-05 | 2026-11-05 | Procurement: 90 * 180 deg USBC adapters, and Fiducial calibraiton mat |  |
| [67](https://github.com/vertical-cloud-lab/robot-arms/issues/67) | issue | closed | jss265 | 2026-11-06 | 2026-11-06 | SO-Leader/PiPER Teleoperation Consolidation attempt |  |
| [68](https://github.com/vertical-cloud-lab/robot-arms/pull/68) | PR | merged | app/claude | 2026-11-06 | 2026-11-06 | Teleop in PiPER Sandbox Scripts/: runnable from a clone, lower latency (#67, #47) | `claude/issue-67-20261106-0214` |
| [69](https://github.com/vertical-cloud-lab/robot-arms/pull/69) | PR | merged | sgbaird | 2026-11-09 | 2026-11-09 | CLAUDE.md: add digital-wetlab and digital-alloy-lab to the Bambu rotation list | `claude/claude-print-rotation-list` |
| [70](https://github.com/vertical-cloud-lab/robot-arms/pull/70) | PR | merged | sgbaird | 2026-11-10 | 2026-11-10 | Onshape: lab account login for `@claude`, and how to sign in through the browser | `claude/onshape-browser-login` |
| [71](https://github.com/vertical-cloud-lab/robot-arms/pull/71) | PR | merged | sgbaird | 2026-11-10 | 2026-11-10 | Onshape: sign-out check and rig.sh stop lessons from the first live test | `claude/onshape-cleanup-notes` |
| [72](https://github.com/vertical-cloud-lab/robot-arms/issues/72) | issue | closed | jss265 | 2026-11-12 | 2026-11-12 | add my key to mpzy |  |
| [73](https://github.com/vertical-cloud-lab/robot-arms/pull/73) | PR | merged | jss265 | 2026-11-13 | 2026-11-13 | Teleop: first real-arm sessions of the SO-101 leader driving the PiPER | `teleop-first-real-runs` |
| [74](https://github.com/vertical-cloud-lab/robot-arms/pull/74) | PR | merged | sgbaird | 2026-11-13 | 2026-11-13 | Nozzle rule: only the nozzles a print uses must be 0.2 or 0.4 mm | `claude/nozzle-rule-used-nozzles` |
| [75](https://github.com/vertical-cloud-lab/robot-arms/pull/75) | PR | merged | sgbaird | 2026-11-14 | 2026-11-17 | Let `@claude` run Python on PRs the Claude app opened | `claude/restrict-untrusted-prs-bot` |
| [76](https://github.com/vertical-cloud-lab/robot-arms/issues/76) | issue | closed | jss265 | 2026-11-14 | 2026-11-14 | PR For Sandbox |  |
| [77](https://github.com/vertical-cloud-lab/robot-arms/pull/77) | PR | open | jss265 | 2026-11-14 | 2026-11-20 | SandBox: AprilTags and Digital Twins | `claude/issue-76-20261114-0436` |
| [78](https://github.com/vertical-cloud-lab/robot-arms/pull/78) | PR | merged | sgbaird | 2026-11-19 | 2026-11-19 | YouTube: default uploads to public (unaudited projects no longer locked private) | `claude/youtube-public-default` |
| [79](https://github.com/vertical-cloud-lab/robot-arms/pull/79) | PR | merged | sgbaird | 2026-11-19 | 2026-11-19 | YouTube: link the triggering comment in each upload's description | `claude/youtube-source-link` |
| [80](https://github.com/vertical-cloud-lab/robot-arms/pull/80) | PR | merged | sgbaird | 2026-11-20 | 2026-11-20 | Raise `@claude` job timeout to 6 hours | `claude/timeout-360` |
| [81](https://github.com/vertical-cloud-lab/robot-arms/pull/81) | PR | open | sgbaird | 2026-11-20 | 2026-11-28 | Livestream the PiPER cell: front cam back up, and streams lend their camera to teleop | `claude/issue-61-20261120-1521` |
| [82](https://github.com/vertical-cloud-lab/robot-arms/issues/82) | issue | closed | chris-policky | 2026-11-23 | 2026-11-24 | Initial Issue for PR titled: "Powder-Doser Workflow 1" |  |
| [83](https://github.com/vertical-cloud-lab/robot-arms/pull/83) | PR | open | chris-policky | 2026-11-24 | 2026-11-25 | Powder-Doser Workflow 1 | `claude/issue-82-20261123-2331` |
| [84](https://github.com/vertical-cloud-lab/robot-arms/pull/84) | PR | merged | sgbaird | 2026-11-24 | 2026-11-24 | Let a run started on a PR open a new PR on a new claude/* branch | `claude/push-new-branch` |
| [85](https://github.com/vertical-cloud-lab/robot-arms/issues/85) | issue | open | sgbaird | 2026-11-25 | 2026-11-26 | Apple agent robot control |  |
| [86](https://github.com/vertical-cloud-lab/robot-arms/issues/86) | issue | open | jss265 | 2026-11-25 | 2026-11-25 | Check printer print bed temperature |  |
| [87](https://github.com/vertical-cloud-lab/robot-arms/pull/87) | PR | open | sgbaird | 2026-11-27 | 2026-11-28 | AMP1 (Apple's agentic manipulation policy) on CaP-Gym and a simulated PiPER (#85) | `claude/issue-85-20261126-0558` |
| [88](https://github.com/vertical-cloud-lab/robot-arms/pull/88) | PR | merged | sgbaird | 2026-11-27 | 2026-11-27 | claude.yml: seat pool (load balancing) and retry machinery from byu-vcl | `claude/seat-pool` |
| [89](https://github.com/vertical-cloud-lab/robot-arms/pull/89) | PR | open | app/claude | 2026-11-27 | 2026-11-27 | Pre-register the CubXL loading reliability campaign: OSF Preregistration, power analysis and analysis code (#21) | `claude/issue-21-20261127-1859` |
| [90](https://github.com/vertical-cloud-lab/robot-arms/pull/90) | PR | merged | jss265 | 2026-11-27 | 2026-11-28 | WRTG-Proposal-1: Edison Scientific Queries | `claude/issue-64-20261104-0017` |

---

*Compiled 2026-11-28 from the GitHub threads (comments to ~09:50 UTC), `main` at 41a21f8 and the branches listed. Intermediate thread dumps and per-slice notes (with every comment URL) are in `/tmp/survey/robot-arms-work/`. Nothing in the repository was modified and no Pi was contacted for this survey.*
