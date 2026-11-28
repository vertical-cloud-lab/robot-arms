# The protocol checked against the cell and the safety drafts (2026-11-27)

This compares [`PROTOCOL.md`](PROTOCOL.md) with the PiPER cell as it stands today and with the
safety drafts on [PR 23](https://github.com/vertical-cloud-lab/robot-arms/pull/23) (`docs/safety/`
at `8f2772c`). Each mismatch is either fixed in the protocol (v2) or turned into a gate in
[`bench-readiness.md`](bench-readiness.md).

**How it was checked.**
- I read the 49 issue and PR threads in this repo, plus byu-vcl issue 266 and PR 272, on 2026-11-27.
- The same day I ran a **read-only** check of the three Pis over Tailscale. I didn't command any
  motion, change CAN or the relay, or write anything to them.
- PR 23's four files were read at `8f2772c`.
- "Bot" marks a fact that only an earlier `@claude` comment records.

## 1. The cell today against what the protocol assumes

| # | Item | Today | What the protocol does about it |
|---|---|---|---|
| 1 | **Which Pi drives the arm** | `rpi-5-mpzy`: the USB-CAN adapter and the IoT Relay II on GPIO17 are there ([PR 47](https://github.com/vertical-cloud-lab/robot-arms/pull/47#issuecomment-6807316627), [#54](https://github.com/vertical-cloud-lab/robot-arms/issues/54#issuecomment-6514058123)). Read-only check today: mpzy up 16 days, CAN adapter present, `can0` down, **relay off since 2026-11-25 21:23 UTC** (forced off; arm silent after 2.1 s). The arm Pi `rpi-5-eufi` did not answer. Main's CLAUDE.md still says eufi drives the arm | §4 names mpzy. CLAUDE.md on main needs its own fix (not in this PR) |
| 2 | **mpzy's capacity** | 990 MB RAM, 374 MB free, while it runs the front livestream (`rpicam-vid` 1280×720 and `ffmpeg`) | Gate SW1: a 2-hour soak test of the harness with the stream on, with no dropped log samples |
| 3 | **E-stop** | POWERTEC 71970 installed front right ([10-26](https://github.com/vertical-cloud-lab/robot-arms/pull/9#issuecomment-6409452390)). **No recorded test**: PR 60 lists "The E-stop test has not been run yet". Where it sits relative to the relay isn't recorded | Gate SF2. App. A: no tested E-stop, no session |
| 4 | **Relay** | Works ([PR 60 tests, 11-03](https://github.com/vertical-cloud-lab/robot-arms/pull/60#issuecomment-6592765858)). A reboot of mpzy cut the arm's power mid-move on [11-06](https://github.com/vertical-cloud-lab/robot-arms/pull/60#issuecomment-6675357204), and the arm drops when power goes | Gate SF9: the harness parks before any planned power-off. Gate SW1: nothing reboots mpzy during a block |
| 5 | **Last incident** | On 2026-11-14 a run ended with the motors still enabled and J2 at 113.2°, outside home, after a J4 over-current stop (mpzy's `arm_power.log`, read today). The arm stayed powered until the forced off on 11-25 | Gate SF9: an end-of-session check that the arm is at rest with the motors off. SOP §I |
| 6 | **Gripper** | AgileX's gripper wears printed PLA auger sleeves. Its zero-finding stalls on them, so motor 7 is never enabled ([PR 73](https://github.com/vertical-cloud-lab/robot-arms/pull/73)). One grip asked for 1.0 N·m and peaked at 5.9 N·m ([PR 20](https://github.com/vertical-cloud-lab/robot-arms/pull/20#issuecomment-6207992243)) | §4 specifies PR 272's finger inserts. Gate HW2: the gripper homes with them, and grip effort is checked on a vial and the post |
| 7 | **What it has gripped** | Only a tape roll ([#30](https://github.com/vertical-cloud-lab/robot-arms/issues/30#issuecomment-6203807072)). No vial and no carrier, ever | Pilot gates PL1–PL3 |
| 8 | **Wrist camera** | HQ (6 mm lens) and Camera Module 3 Wide on the wrist Pi, installed 10-30. The HQ lens is unfocused. The wrist Pi has been offline since 2026-11-13 ([PR 40](https://github.com/vertical-cloud-lab/robot-arms/pull/40#issuecomment-6843948205)) and **did not answer today**. Its power adapter was ordered ([#66](https://github.com/vertical-cloud-lab/robot-arms/issues/66#issuecomment-6647149651)); fitted is unverified. Its cable jammed J6 at 16 A once ([#54](https://github.com/vertical-cloud-lab/robot-arms/issues/54#issuecomment-6514063980)) | The AT condition can't run today. Gates HW3, HW4 |
| 9 | **Calibration and tags** | No intrinsics and no hand–eye calibration on hardware. Seen from mpzy, 10 mm tags decoded 0 of 48 and 25 mm tags only at full resolution ([PR 40](https://github.com/vertical-cloud-lab/robot-arms/pull/40#issuecomment-6869819000)). PR 77's tag cubes aren't printed | R3 sets tags of at least 25 mm. Gate HW4 |
| 10 | **Correction code, trial harness** | Neither exists. The nearest thing is PR 83's graded auger test, run only in simulation | Gates SW1, SW2 |
| 11 | **Dock, carrier, inserts, plates** | CAD and slices only ([byu-vcl PR 272](https://github.com/vertical-cloud-lab/byu-vcl/pull/272), open, untouched since 10-11). "Nothing has been printed or fitted to the arm yet" | §4 cites PR 272. R1 and R2 measure the printed parts. Gates RA2, HW1 |
| 12 | **Deck** | No real CubXL in or near the cell. The v1 mock-up's slot pitch is 35.6 mm against the real deck's 25 mm (PR 272) | D1 (mock-up v2). §1 Scope says so |
| 13 | **Vial height** | Chris's printed vial is 64.2 mm, but the CubOS deck files say 83 mm (PR 272) | D2 |
| 14 | **Shelf** | PR 9's pocketed shelf is an unmerged design. What exists is a plywood shelf and a perforated plate | §4 asks for two nests and a pocket. Gates RA3, HW1 |
| 15 | **Logging rate** | Main's only `--trace` (`Up_and_Down.py`) logs at 50 Hz. PR 20's 100 Hz trace is unmerged | §4 and §11 now say ≥ 50 Hz |
| 16 | **Payload** | A full carrier is 0.53–0.66 kg (PR 272), the inserts 67 g, the gripper about 0.5 kg, plus the wrist Pi, two cameras and the mount. #42 reads the 1.5 kg rating as including the gripper (bot) | Gate HW6: weigh everything and compare it with AgileX's rating at the reach used |
| 17 | **Reach and layout** | J1 is limited to −20° … +60° to stay clear of the A1 mini on the table, and J6 to a 90° window by its wiring ([PR 83](https://github.com/vertical-cloud-lab/robot-arms/pull/83)). PR 272 found no IK solution for a carrier lying across the arm's line | §4 Layout. Gate HW7 |
| 18 | **Joint zeros** | J1 was re-zeroed by 15.2° on 2026-11-14 (CLAUDE.md). On 2026-10-16 J1's reading jumped 7.9° on enable and a grasp missed by about 65 mm ([PR 20](https://github.com/vertical-cloud-lab/robot-arms/pull/20#issuecomment-6206324136)) | §5: a rest-pose check before every unit. §15 threat. Gate HW8 |
| 19 | **Repeatability** | AgileX's 0.1 mm has never been measured here. No fixture exists | E3 measures it (registration B). Gate RB1 |
| 20 | **Collision protection** | The joint drivers' collision level has never been read. Another user's PiPER reported level 0, no protection ([piper_sdk#20](https://github.com/agilexrobotics/piper_sdk/issues/20)). E2 deliberately misplaces carriers by up to 4 mm and 4°, and about 180 of those loads are expected to fail | R8 (a contact stop on every place descent). Gate SF8 |
| 21 | **Ownership** | The arm is on loan to the lab ([#1](https://github.com/vertical-cloud-lab/robot-arms/issues/1#issuecomment-6089391974)) | Gate HW9: the lender agrees to about 6,000 transfers and about 600 power cycles |
| 22 | **Competing use** | The finger inserts replace the auger sleeves that #42's auger-swap work needs. jss265 called that work "Priority number 1" ([#42](https://github.com/vertical-cloud-lab/robot-arms/issues/42)) | Swapping end effectors is a configuration change (§10). Gate HW10: decide how the arm is shared |

## 2. The protocol against PR 23's safety drafts

| PR 23 says | The protocol (v2) | Status |
|---|---|---|
| **"Workspace clear"** covers one run and expires after 10 minutes. A trained person stands at the E-stop for the whole run (SOP §D) | A block is one run. The person at the arm gives the clear before it starts and again before it resumes after any reset, and stays at the E-stop throughout (§9, App. A) | Aligned in v2 |
| **Lockout before every reach-in**: the arm at rest, then the E-stop (SOP §C) | App. A's reset: wait for the harness to park, press the E-stop, restore, START, clear again. A planned E-stop between units is not a failure (§7) | Aligned in v2 |
| The JHA plans for "a person reaches in to reset the scene hundreds of times" | E2 alone is expected to need about 590 resets (§8.2), 400 of them for single vials under OL. D6 can cut that by about 200 | Gate SF1: the review team sees this number. The block log counts reach-ins |
| JHA H5: no teach mode during a block | App. A. Re-teaching is a configuration change (§10) | Aligned |
| JHA H6, H15: power cut only at rest; a failed run can leave the arm raised | Park before any power-off; end-of-session check. This happened on 11-14 | Gate SF9 |
| JHA H9: the dome has no interlock and stays at risk level II | Administrative control only: the person at the E-stop for every block | PR 23's open item 12 is still a decision for the PI |
| JHA H10: 190 mm transformer clearance, never measured | The dock, shelf and reach must be outside the zone | Gate SF3 (the SOP's measurement M1) |
| JHA H12: vials may be glass | D2 suggests printed dummies; glass only in a separate extension block (§15) | Aligned |
| JHA H13: base fixing unrecorded | — | Gate SF4 |
| JHA H14: repetitive reaching | R7 caps a block at about 50 minutes; breaks between blocks | Aligned |
| The scripts cap speed at 30–50 % | R5: one speed, never above the SOP's cap | Aligned |
| **Out of date:** "no E-stop installed", "a wrist camera is planned", "usually from the arm Pi" (eufi), "the next block" being #21 with its v1 numbers | — | Gate SF1: update PR 23 before its review |
| Fifteen "Need" items before the next block (`docs/safety/README.md`) | Every one is a gate before the first counted trial | Gate SF1 |

**Who starts a counted block.** The person at the cell starts it from the harness on mpzy, or a
remote operator does who is in contact with that person. An `@claude` run doesn't start one: a run
lasts at most six hours, its GitHub token expires after one, and the person at the E-stop has to be
there anyway. §9 says so.

## 3. Changes this check made to the protocol

- §4 now describes the cell as it is: mpzy, the relay and the E-stop, PR 272's parts, the wrist Pi,
  logging at ≥ 50 Hz, the payload and the layout limits.
- §5 adds a rest-pose check before every unit, and §10 rule 3 stops the block when it fails.
- §7 says a planned E-stop between units is not a failure. App. A follows the SOP's lockout.
- §8.2 corrects the yaw arithmetic to PR 272's 250 mm pin spacing, and counts the expected resets.
- R8 adds a contact stop on every place descent.
- §15 adds J1's history and the wrist Pi's history as threats.
