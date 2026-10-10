# PiPER cell safety documents (DRAFT)

**Status:** draft, written 2026-10-10 for the College Health & Safety Officer to review before the
next campaign block ([#21](https://github.com/vertical-cloud-lab/robot-arms/issues/21)).
Requested in [#22](https://github.com/vertical-cloud-lab/robot-arms/issues/22). Nobody has
reviewed, approved or signed it yet.

| File | What it is |
|---|---|
| [`hazard-analysis.md`](hazard-analysis.md) | Job Hazard Analysis following §6 of the College [Laboratory & Shop Safety Plan](https://github.com/vertical-cloud-lab/byu-vcl/blob/b00e137/byu-engineering-lab-safety-plan-chemical-hygiene-plan-2024.pdf): tasks, 15 hazards, proposed ratings on the College matrix, controls in hierarchy order, What-If table |
| [`sop.md`](sop.md) | SOP in the plan's Appendix B layout. Includes the one-time pre-block steps (with measurement M1 at the transformer), the "workspace clear" rule, restart after an E-stop, emergencies, and training and sign-off |
| [`checklist.md`](checklist.md) | One page for the person at the arm, to print and post by the E-stop |

The format follows the College plan, but its text isn't copied in. The PDFs stay in byu-vcl.

Nothing in these files moves the arm or changes the Pi. Where a step needs something done on the
Pi, it says so and leaves it to the operator who owns the run.

## How numbers are marked

- **A number with a link:** I read it in that source while writing this, 2026-10-10. Some sources
  are measurements earlier runs logged in this repo's issues, and the link says which.
- **`[unverified]`:** I couldn't check it. It came secondhand, from a design model rather than the
  built cell, from a vendor page I couldn't open, or it's an estimate.
- **`[to measure]`:** nobody has measured it. It's a task before the block.
- **"Proposed":** a value this draft suggests, such as the 10-minute expiry. It's not a fact, and
  the review team should set it.

### Numbers I couldn't verify

| Number | Where it's used | Why it's unverified | How to check |
|---|---|---|---|
| **190 mm (7.5 in) transformer clearance**, "nothing within … or above it" | H10, SOP §A M1, sign | Secondhand: jss265 quoting @gage-erickson in [#2](https://github.com/vertical-cloud-lab/robot-arms/issues/2#issuecomment-6089392188). I found no written source in byu-vcl | Ask the transformer's owner. Read its nameplate without opening anything. NEC 450.9 may be the origin `[unverified]` |
| Distances from the transformer to the shelf, table, dome, canvas, cords, E-stop box, and the arm's reach | H10, SOP §A M1 | Never measured `[to measure]` | Measurement M1 |
| The transformer's voltage and rating | H10 | Not recorded | Nameplate |
| Whether the 626 mm reach includes the gripper | M1, reach marking | The listing doesn't say | AgileX datasheet, or measure with the power off |
| About 150 mm from flange to fingertips | M1 | Photo estimate in #19 (the tape script's `--tcp-mm` default) | Calipers, power off |
| Fingertip force at the gripper's 0–5 N·m effort range | H1 | Not found | AgileX gripper spec |
| About 167°/s at 100% speed | H3 | Extrapolated from 1.67°/s per percent, measured only at 10–20% | AgileX joint-speed spec |
| Speed of teach playback | H5 | Unknown | AgileX, or a supervised test at rest |
| 7% / 14% of the reach outside the dome, and a 0.26 m drop below the deck | H9 | Design models in #2, not the built cell | Measure as built |
| Parked elbow sweep of 317 mm, leaving 33 mm to the shelf | H2 | Design model. The shelf was later to be cut | Measure as built |
| Shelf top 1.35 m up and 0.96 m in | H14 | Raised-deck model. The deck may not be built | Measure as built |
| Brick input "100-240V" | H11 | #7 statement; label not checked | Read the brick's label |
| 120 W max and a 1–2 A draw | H11 | AgileX, quoted in #18. I couldn't open the manual | Label or manual |
| POWERTEC 71970: anti-restart, "approved according to UL508, UL61058-1", no interlock input | H6, H9, H11 | Product listing via #18 | Check the unit when it arrives |
| Up to about 40 s of moves after power drops | H15, SOP §G | Estimate in #18 | The operator checks the scripts' timeouts |
| AgileX manual §6.1 (power off after use) and §8 (arm drops on power-off; unplugging isn't a safety mechanism) | H6, SOP §F | Quoted in #18. The device.report copy returned 403 and the Scribd copy is paywalled | Read the manual |
| Firmware S-V1.8-5 as the fix for the drop on exiting teach mode | H6 | From #5's summary of the ROS driver docs | `agx_arm_ros` release notes |
| College phone numbers | SOP, checklist, sign | Copied from the March 2024 plan; may have changed | Confirm before posting |

### Numbers I did check

| Number | Source |
|---|---|
| 626 mm reach, 1.5 kg rated payload, 4.2 kg arm | [OpenELAB listing](https://openelab.io/products/agilex-piper-ros-ai-arm), a reseller, not AgileX |
| Joint drivers at 23–24 V. Motors enable in about 0.1 s | CAN log in [#18](https://github.com/vertical-cloud-lab/robot-arms/issues/18#issuecomment-6091246658) |
| Wrist drops about 10 mm in about 50 ms when the motors switch off at rest | Video analysis in [#19](https://github.com/vertical-cloud-lab/robot-arms/issues/19#issuecomment-6092030025) |
| About 1.67°/s per MOVE J speed percent. Firmware S-V1.8-1 | Arm notes in `CLAUDE.md` on the PR #20 branch |
| Script caps: 45° lift and 50% speed (`piper_up_down.py`), 30% (`piper_pick_tape.py`). Both refuse to run without joint feedback | The scripts on the PR #16 and PR #20 branches |
| `MotionCtrl_1(0x01, 0, 0)` lowers the arm with damping. `MotionCtrl_1(0x02, 0, 0)` resets it and it drops | AgileX's answer in [piper_sdk#20](https://github.com/agilexrobotics/piper_sdk/issues/20) |
| Review every other year. The 50 V electrical threshold | College plan §6, §7 and §10 |

## Open before the next campaign block

These are the **Need** items from the hazard analysis. Each one needs an owner and a date.

| # | Item | Owner | Done (date) |
|---|---|---|---|
| 1 | **Measurement M1:** transformer clearances (SOP §A.1), plus the rule's written source and the transformer's rating. Tape the zone | | |
| 2 | **E-stop installed and tested** (#18), and its label checked for a Listed mark. Decide whether the College needs a listed device | | |
| 3 | **Decide:** does the block wait for the E-stop? This draft recommends yes | | |
| 4 | Cover and label on the wrist teach button | | |
| 5 | Sign posted with the agreed text, and a photo committed. Align CLAUDE.md's "workspace clear" rule with it | | |
| 6 | Arm base bolted, with how it's fixed recorded | | |
| 7 | Brick and cord checked for NRTL marks. Brick outside the dome, uncovered, off the floor | | |
| 8 | Reach marked on the table and floor. Flap labelled | | |
| 9 | List of who can trigger `@claude` runs and who has SSH to the Pi | | |
| 10 | Lab layout attached (SOP Attachment) | | |
| 11 | SOP blanks filled: PI, contacts, lab #, building, Physical Facilities number, extinguisher location, College course names | | |
| 12 | **Decide** on the dome (H9 stays at II): a flap interlock or a rigid latched front, or accept the risk with a reason | | |
| 13 | Review team meets, sets the ratings, and signs the JHA. The College Health & Safety Officer reviews the SOP | | |

**Later:**
- A software keep-in box at the dome walls and the shelf.
- The camera check before enabling, enforced in the scripts.
- The damped stop for mid-run aborts, after a test at rest.
- Questions for AgileX: does a teach recording survive a power cycle, and how is one cleared?
  What is the gripper's force?
- A read-only query of the drivers' collision protection level. That needs its own explicit
  request.
- Whether a UPS suits the arm.

## What this draft didn't do

- I didn't move the arm, bring up CAN, run anything on the Pi, or connect to it.
- I didn't see the posted sign. Its proposed text is in [`sop.md`](sop.md#sign-text-proposed).
- I didn't measure anything. Every distance in the cell is a model figure or `[to measure]`.
- I couldn't open the AgileX manual: the device.report copy linked in #7 returned 403, and #7
  says the Scribd copy is paywalled. Its sections are quoted through #18 and marked.
- The risk ratings are proposals. The College plan has the review team set them.
