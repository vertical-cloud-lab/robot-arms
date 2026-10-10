# PiPER cell: Job Hazard Analysis (DRAFT)

**Status:** draft for the College Health & Safety Officer to review before the next campaign
block. Written 2026-10-10 from this repo's record. The review team has not met yet, so every
rating below is a proposal.
**Format:** follows §6 (Job Hazard Analysis) of the College of Engineering
[Laboratory & Shop Safety Plan](https://github.com/vertical-cloud-lab/byu-vcl/blob/b00e137/byu-engineering-lab-safety-plan-chemical-hygiene-plan-2024.pdf)
(March 26, 2024). Hazards are named from its Appendix A checklist and rated with the
[College risk matrix](https://github.com/vertical-cloud-lab/byu-vcl/blob/b00e137/byu-engineering-safety-and-health-risk-assessment-matrix-v2.pdf),
and controls follow its hierarchy. The SOP that goes with it is [`sop.md`](sop.md).
**Numbers:** `[unverified]` marks a number I could not check. `[to measure]` marks one nobody
has measured yet. Every other number links to where I read it. See [`README.md`](README.md#how-numbers-are-marked).

## Review team (§6.B)

The plan asks for at least these four roles. One person can fill more than one.

| Role | Name | Date reviewed | Signature |
|---|---|---|---|
| Knows how to do the work (a person who runs the arm) | | | |
| Safety professional (College Health & Safety Officer, 801-422-6589) | | | |
| Subject-matter expert (robot arms, electrical) | | | |
| Can commit funds for controls (PI) | | | |

## Step 1. Job title and description

**Job:** running the AgileX PiPER cell at spot D, in person and remotely.

**The cell:**
- **Arm.** An AgileX PiPER 6-axis arm with its parallel gripper and a wrist camera. The reseller
  listing gives a 626 mm reach, a 1.5 kg rated payload and a 4.2 kg arm weight
  ([OpenELAB](https://openelab.io/products/agilex-piper-ros-ai-arm)). The listing doesn't say
  whether the 626 mm includes the gripper `[unverified]`, and the fingertips sit about 150 mm
  past the flange `[unverified]` (photo estimate in [#19](https://github.com/vertical-cloud-lab/robot-arms/issues/19)).
- **Mounting.** The arm sits on a plywood base at spot D. It isn't recorded anywhere whether the
  base is bolted down. In [#15](https://github.com/vertical-cloud-lab/robot-arms/issues/15#issuecomment-6090554296)
  it looked like it was just resting on the plywood.
- **Power.** A 24 V power brick on a US cord plugs into a wall outlet. The joint drivers report
  23–24 V ([#18](https://github.com/vertical-cloud-lab/robot-arms/issues/18#issuecomment-6091246658)),
  and the lab confirmed the brick is rated for BYU
  ([#7](https://github.com/vertical-cloud-lab/robot-arms/issues/7#issuecomment-6089393576)).
  The arm's only connections are power and CAN, so the only hardware stop is cutting power.
- **Control.** The arm is driven over CAN. Usually that's from the arm Pi (a Raspberry Pi 5),
  which remote users and `@claude` runs reach over Tailscale. A lab PC on WSL2 can also drive
  it through a USB-CAN adapter (`docs/PiPER Install Guide R1`), and so can the wrist teach button.
- **Enclosure and fixtures.** A canvas quarter dome on a PVC frame, with a front flap that rolls
  up and no interlock. There is also a pick-up shelf behind or beside the arm, and a side camera
  fixed on the table.
- **Neighbors.** The rePowder atomizer's high-voltage transformer stands near the pick-up shelf
  ([#2](https://github.com/vertical-cloud-lab/robot-arms/issues/2#issuecomment-6089392188)).

**The next block.** The reliability campaign in
[#21](https://github.com/vertical-cloud-lab/robot-arms/issues/21) loads a CubXL with vial
carriers and single vials. It runs at least 300 trials per task and condition, scripted or
agent-driven, and a person at the arm resets the scene between trials. That means people will
reach into the cell hundreds of times while the arm is powered and remotely startable. This JHA
is written around that pattern.

**What's in place today, and what isn't:**

| Control | Status |
|---|---|
| Hardware E-stop | **None installed.** #18 recommends the POWERTEC 71970, a latching plug-in switch with anti-restart. Until it arrives, the only stop is pulling the arm's plug |
| Anti-restart after an outage | **None.** After an outage the arm powers up again by itself in Stand By, holding its pose ([#7](https://github.com/vertical-cloud-lab/robot-arms/issues/7#issuecomment-6089393334), [#18](https://github.com/vertical-cloud-lab/robot-arms/issues/18#issuecomment-6091777194)) |
| Cover or label on the wrist teach button | None that I know of |
| Interlock on the dome flap | None |
| Software keep-in box at the dome walls | None in the arm scripts. [#2](https://github.com/vertical-cloud-lab/robot-arms/issues/2#issuecomment-6089393090) calls one required for the raised-deck layout |
| Script guards | `piper_up_down.py` (PR #16) and `piper_pick_tape.py` (PR #20) send nothing without `--go`, and refuse to start without live joint feedback or away from the rest pose. They cap speed (50% and 30%) and only turn the motors off at rest. Neither is merged yet |
| Collision detection level on the joint drivers | Not read. Another user's PiPER reported level 0 (no protection) ([piper_sdk#20](https://github.com/agilexrobotics/piper_sdk/issues/20)) |
| Sign at the cell | Posted, according to the request for this draft. Its text isn't in either repo, so attach a photo. [`sop.md`](sop.md#sign-text-proposed) proposes wording |
| Transformer clearance (190 mm `[unverified]`) | **Not measured** `[to measure]` |

**Out of scope:** the atomizer itself and its powder handling (byu-vcl #126), the CubXL's own
motion, whatever the vials hold (if they hold chemicals, those need an SDS and their own SOP),
and network security beyond who can start motion.

## Step 2. Tasks

| ID | Task |
|---|---|
| T1 | Power the arm up or down, or leave it powered for remote use |
| T2 | Work inside the reach: reset the scene between trials, load or unload the shelf or dock, adjust cameras or cables |
| T3 | Powered runs: scripts on the Pi over SSH, `@claude` runs, the lab PC on WSL2 |
| T4 | Teach (drag) mode and playback from the wrist button |
| T5 | Abnormal events: E-stop pressed, power outage, a run that fails or freezes partway |
| T6 | Work near the atomizer transformer: shelf loading, cable routing, the dome's edge |
| T7 | Maintenance with the power off: gripper or flange changes, camera mounts, base bolts |

## Step 3. Hazards

Appendix A categories are in brackets. "Abnormal" means the hazard needs something to go wrong.

| ID | Tasks | Hazard and how it happens | Normal / abnormal |
|---|---|---|---|
| H1 | T2, T3, T4 | **Gripper pinch** [crushing, laceration]. A hand at the fingers while they close, during a run, a test or a reset. The tape script sets effort up to 5 N·m, but I don't know what fingertip force that gives `[unverified]` | Normal |
| H2 | T2, T3, T4, T5 | **Elbow and link pinch** [crushing, amputation of a fingertip]. The forearm folds onto the upper arm at rest. The wrist settles onto the J2 motor when the motors switch off, dropping about 10 mm in about 50 ms ([#19](https://github.com/vertical-cloud-lab/robot-arms/issues/19#issuecomment-6092030025)). Links can also close against the table, the shelf, the dome frame or the CubXL. The parked elbow sweeps about 317 mm behind the base, which leaves about 33 mm to the shelf in the design model `[unverified]`. The shelf was then to be cut down, and the as-built gap isn't recorded ([#2](https://github.com/vertical-cloud-lab/robot-arms/issues/2#issuecomment-6089393358)) | Normal |
| H3 | T2, T3, T4 | **Strike by the moving arm** [impact injury]. The J1 swing, the elbow rising up and back, or a fingertip at face height. Eyes are the worst case. One MOVE J speed percent is about 1.67°/s, so the scripts' 10–20% is about 17–33°/s (arm notes on the PR #20 branch). Full speed would be about 167°/s, an extrapolation `[unverified]`. Playback speed isn't known `[unverified]` | Normal |
| H4 | T2, T3 | **Remote or agent motion while someone is in the reach** [impact, crushing]. Anything on the Pi can enable the motors in about 0.1 s ([#18](https://github.com/vertical-cloud-lab/robot-arms/issues/18#issuecomment-6091246658)). The "workspace clear" rule is a statement, not a lock. The side camera can't see depth, and one frame in #15 showed a person beside the table when a run had been requested | Abnormal |
| H5 | T4, and any time the arm is powered | **The teach button replays a stored path** [impact, crushing]. Two presses on the wrist button start playback whenever the arm has power, with or without the Pi. Playback "will not stop for obstacle including people" and has dented plywood ([#7](https://github.com/vertical-cloud-lab/robot-arms/issues/7#issuecomment-6089393334)). Nobody knows whether a recording survives a power cycle, so assume it does ([#18](https://github.com/vertical-cloud-lab/robot-arms/issues/18#issuecomment-6091777194)) | Abnormal |
| H6 | T1, T5 | **Power loss drops a raised arm** [crushing, impact]. With power cut by the E-stop, an outage, a pulled plug or a tripped breaker, the motors go limp and the arm falls onto whatever is under it. Software can do the same: a disable, or the SDK reset `MotionCtrl_1(0x02, 0, 0)` ([piper_sdk#20](https://github.com/agilexrobotics/piper_sdk/issues/20)). On firmware older than S-V1.8-5, the ROS driver's exit from teach mode restarts the arm and it can fall ([#5](https://github.com/vertical-cloud-lab/robot-arms/issues/5#issuecomment-6089392622)). This arm runs S-V1.8-1 (arm notes on the PR #20 branch) | Abnormal |
| H7 | T1, T5 | **The arm re-energizes after an outage** [crushing]. It comes back stiff in Stand By and holds its pose. It doesn't move, but it's live without anyone having turned it on | Abnormal |
| H8 | T2–T5 | **No E-stop, so stopping is slow** [makes H1–H5 worse]. Pulling the plug may mean reaching behind the table or past the arm | Normal, today |
| H9 | T2, T3 | **The canvas dome has no interlock** [impact, crushing, fire]. Anyone can lift the flap and reach in during a run, and nothing stops the arm. The canvas hides a moving arm from people outside. The arm can also reach past the walls: about 7% of its reach on the table layout and 14% on the raised deck, where the fingertip can drop 0.26 m below the deck edge. Both are model figures `[unverified]` ([#2](https://github.com/vertical-cloud-lab/robot-arms/issues/2#issuecomment-6089393090)). The arm can snag the canvas. The canvas is a cotton drop cloth with no stated flame rating `[unverified]` and may sit near the 24 V brick | Normal |
| H10 | T6 | **Atomizer transformer clearance** [shock, electrocution, arc blast, fire]. @jss265 relayed in #2 that, according to @gage-erickson, "nothing can be within 7.5″ of the transformer or above it". That is 190 mm ([#2](https://github.com/vertical-cloud-lab/robot-arms/issues/2#issuecomment-6089392188)). That rule is secondhand, and its written source and the transformer's rating are unknown `[unverified]`. No distances to the shelf, table, dome, cords or arm reach have been measured `[to measure]`. Ways in: loading the shelf by reaching past the transformer, fetching a dropped vial, routing cords along the wall, the dome's canvas hanging over it, the arm's reach | Abnormal |
| H11 | T1, T7 | **Arm power supply** [shock, fire]. 120 V AC on the cord and the brick's input side. Mains input is "100-240V" per #7 `[unverified]`, and the arm is rated 120 W max (AgileX, quoted in #18) `[unverified]`. The brick could overheat if covered by canvas, a damaged cord could shock, and cords on the floor are a trip hazard. The arm's 24 V side is below the plan's 50 V threshold (§10) | Abnormal |
| H12 | T2, T3 | **Dropped or crushed vials** [laceration]. A vial slips from the gripper or is crushed in a pocket or the dock. Whether the campaign's vials are glass isn't recorded `[unverified]` | Abnormal |
| H13 | T3, T7 | **The arm tips or the base shifts** [impact, crushing]. Fast moves or full reach with payload on an unbolted base (see Mounting above) | Abnormal |
| H14 | T2 | **Excessive reaching** [excessive reaching, repetitive motion]. Loading the shelf over or around the arm, hundreds of times per block. On the raised-deck design the shelf top is about 1.35 m up and 0.96 m in from the front edge (model, [#2](https://github.com/vertical-cloud-lab/robot-arms/issues/2#issuecomment-6089393358)) `[unverified]` | Normal |
| H15 | T3, T5 | **A failed run leaves the arm enabled and raised** [crushing]. The arm holds its last pose indefinitely, then drops on the next power cut. A run in progress can keep sending moves after power drops, for up to about 40 s by #18's estimate `[unverified]` | Abnormal |

## Step 4. Evaluate: proposed ratings

**Method.** This is a preliminary hazard analysis, with a What-If table for every hazard still
rated II after controls. The matrix sheet asks for "a higher degree of assessment" for orange and
red. Ratings combine the worst credible consequence with a likelihood from A (Unlikely) to E
(Frequent), which gives I, II or III. "Now" means today, with no E-stop. "After" assumes every
control in Step 5 is in place. The review team should set the final ratings.

| ID | Worst credible consequence | Now | Risk now | After | Risk after |
|---|---|---|---|---|---|
| H1 Gripper pinch | Moderate injury | D | **II** | B | I |
| H2 Elbow and link pinch | Serious injury (crushed finger) | C | **II** | A | I |
| H3 Strike | Serious injury (eye) | C | **II** | A | I |
| H4 Remote or agent motion | Serious injury | D | **II** | A | I |
| H5 Teach playback | Serious injury | C | **II** | A | I |
| H6 Power-loss drop | Moderate injury | C | I | B | I |
| H7 Re-energize after outage | Slight injury | B | I | A | I |
| H8 No E-stop | Serious injury (makes H1–H5 worse) | C | **II** | A | I |
| H9 Dome, no interlock | Serious injury | C | **II** | B | **II** |
| H10 Transformer | 1–3 deaths (electrocution, arc flash) | A, until measured | **II** | A | **II** |
| H11 Power supply | Serious injury | A | I | A | I |
| H12 Vials | Slight injury | C | I | B | I |
| H13 Tip or shift | Moderate injury | C | I | A | I |
| H14 Reaching | Slight injury | D | I | C | I |
| H15 Failed run | Moderate injury | C | I | B | I |

Two hazards stay at II after controls:
- **H9 (dome).** The flap is only a visual barrier. Getting to I needs an engineering control: an
  interlock that cuts power, or a rigid, latched front panel.
- **H10 (transformer).** On this matrix, any hazard whose worst case is 1–3 deaths is II even when
  unlikely. The control is to keep everything out of the clearance zone and the transformer's
  owner confirming the rule.

### What-If (for the II ratings)

| What if… | What happens | What protects people | Gap |
|---|---|---|---|
| Someone writes "workspace clear" from home while a student is resetting vials? | A run starts with a hand in the reach (H4) | With the E-stop pressed, the scripts exit with "no joint feedback" before sending a move (PR #16) | **No E-stop yet.** The phrase isn't tied to a person at the cell |
| The `@claude` job starts minutes after the "clear" comment, or is re-run? | The statement is stale. In #19 a "Go" was skipped and re-requested | The agent grabs a side-camera frame before enabling, by practice only | The camera can't see depth. No time limit on "clear" |
| The person at the arm presses START without telling remote users? | The arm is live. The next remote run can move it | None | Proposed: only the person who will then stand at the E-stop presses START, and says so in the lab channel |
| Someone double-presses the wrist button while wiping the gripper? | Playback of an unknown path that ignores people (H5) | Nothing physical | Proposed: a cover and label on the button. Work at the wrist only with power cut |
| The E-stop is pressed with the arm raised over the dock? | The arm drops onto the dock or CubXL and glass can break (H6, H12) | Stop only at rest unless it's an emergency. The SDK's damped stop is used by `piper_pick_tape.py` for parking, untested on this arm | The scripts have no damped stop for mid-run aborts |
| Someone lifts the flap to watch a run? | Their hand or head is inside the reach of a moving arm (H9) | The sign | No interlock. Proposed: a "flap down = may move" label, plus a flap interlock later |
| A vial rolls off the shelf toward the transformer? | Someone reaches into the 190 mm `[unverified]` zone to fetch it (H10) | None yet | Proposed: never reach into the zone; mark it on the floor and wall; a lip on the shelf |
| A run crashes with the arm raised and everyone leaves? | It holds, then drops at the next outage (H15) | Script logs | Proposed: an end-of-session status check by the run's operator |

### 2 Guide Word check of the restart procedure (SOP §G)

| Step | If skipped | If done wrong |
|---|---|---|
| Stop the job that was running before releasing the E-stop | The job may still be sending moves. After START the arm can jump toward its last target | The wrong job is stopped: confirm with the person who started it |
| Put the arm at rest by hand with the power off | It comes back stiff in a raised pose, and the next power cut drops it | Lifting a 4.2 kg arm alone in an awkward pose risks a strain or pinch. Support the forearm and keep fingers out of the elbow |
| Clear the reach before START | START with a hand in the reach. The arm only stiffens, but a queued remote run could follow | — |
| Check the wrist LED after START | Playback could run unnoticed | LED off is Stand By, on is recording, flashing is playback (#7). If it flashes, press the E-stop at once |
| Read-only status check before the next run | A run starts on a faulted arm | — |

## Step 5. Controls

Controls are listed in the plan's order: eliminate, substitute, engineering, administrative,
then PPE. Status is **Have**, **Need** (before the block) or **Later**.

**H1–H3, H8 (pinch, strike, no E-stop)**
- Engineering, **Need:** install and test the latching E-stop with anti-restart (#18). Mount it
  outside the arm's reach, where the person at the arm can hit it without leaning over the arm.
- Engineering, **Need:** use the E-stop as a lockout. Press it before any hand enters the reach,
  and only with the arm at rest. With power cut, the scripts can't start
  ([#18](https://github.com/vertical-cloud-lab/robot-arms/issues/18#issuecomment-6092117783)).
- Engineering, **Have:** speed caps and rest-pose checks in the scripts. **Later:** a software
  keep-in box at the dome walls and the shelf.
- Administrative, **Need:** nobody in the reach while the arm is powered. Mark the reach on the
  table. Stand outside it during runs.
- PPE, **Need:** safety glasses for anyone within about 1 m of a powered run (proposed distance).
  Glasses don't replace the lockout.

**H4 (remote and agent motion)**
- Engineering, **Need:** the E-stop lockout above. This is the only control that doesn't depend
  on remote people being right.
- Administrative, **Need:** define "workspace clear" as in [`sop.md` §D](sop.md#d-powered-runs-and-the-workspace-clear-rule).
  The requester names the person at the E-stop, who stays there for that run. The statement
  covers one run and expires (10 minutes proposed).
- Administrative, **Have, by practice:** `@claude` runs take a side-camera frame and stop if
  anyone is visible (#15). **Later:** enforce it in the run scripts.
- Administrative, **Need:** confirm who can trigger `@claude` runs in this repo. By default it's
  people with write access `[unverified]`. Keep that list short.

**H5 (teach button)**
- Eliminate, **Need:** no teach mode during a campaign block.
- Engineering, **Need:** a cover over the wrist button and a label ("Do not press: replays a path
  that does not stop for people").
- Administrative, **Need:** any teach session is supervised and starts and ends at the rest pose.
  Work at the wrist only with power cut. **Later:** ask AgileX whether a recording survives a
  power cycle and how to clear one.

**H6, H7, H15 (power loss, re-energizing, failed runs)**
- Engineering, **Need:** anti-restart (the POWERTEC 71970 has it, per its listing `[unverified]`).
- Administrative, **Need:** leave the arm powered and limp only at the rest pose. Cut power only
  at rest unless it's an emergency. Never put hands under a raised arm. After a failed run, the
  operator checks status and parks the arm before leaving.
- Engineering, **Later:** use the SDK's damped stop (`EmergencyStop(0x01)`) for mid-run aborts
  after it has been tested at rest. A UPS ahead of the E-stop would ride through short outages;
  check that it suits the load first.

**H9 (dome)**
- Engineering, **Later, recommended:** an interlock on the flap that cuts arm power through the
  E-stop's circuit, or a rigid, latched front panel. The POWERTEC has no interlock input
  `[unverified]`, so this may need a different switch.
- Administrative, **Need:** a label on the flap: "Flap down = arm may move. Press the E-stop
  before lifting." Mark the reach that pokes outside the dome. Keep the brick outside the dome
  and off the floor, never under canvas.

**H10 (transformer)**
- Eliminate, **Need:** keep everything at least 190 mm `[unverified]` from the transformer and nothing above it
  `[to measure]`. That covers the shelf, table, dome and canvas, cords, the E-stop box, and the
  arm's reach plus its fingertips. Measurement M1 in [`sop.md` §A](sop.md#a-before-the-next-campaign-block-one-time)
  is the check. If anything falls inside the zone, move it before the block.
- Administrative, **Need:** ask the transformer's owner (Physical Facilities or whoever installed
  the atomizer's supply) for the written source of the 7.5 in rule. It may be the
  ventilation clearance marked on the transformer. NEC 450.9 asks for that clearance to be marked
  on the unit `[unverified]`. Read the nameplate without opening anything.
- Administrative, **Need:** mark the zone with floor and wall tape. Never reach into it, including
  to fetch dropped items. Report anything inside it to the PI.
- Engineering, **Need:** a lip on the shelf's transformer side, so items can't roll off toward it.

**H11 (power supply)**
- Engineering, **Need:** check the brick and cord for an NRTL mark (UL, CSA, ETL), as §10 of the
  plan expects. The POWERTEC's "approved according to UL508, UL61058-1" isn't a Listed mark
  `[unverified]`, so check the label when it arrives. If the College requires a listed device, #18
  names the MAKESafe PTC-V120-P1 instead.
- Administrative, **Need:** plug only the arm's brick into the E-stop, not the Pi. Inspect the cord
  before each session. Route cords off the floor.

**H12–H14 (vials, tipping, reaching)**
- Engineering: bolt the base and record that it's done (**Need**). Keep the shelf low and reachable
  without reaching over the arm (**Later**).
- Administrative: sweep up broken glass with a brush and pan, not hands, and put it in a glass
  box (**Need**). Take breaks during long reset sessions (**Need**).

## Steps 6 and 7. Document and implement

This file is the documentation. The items marked **Need** are collected, with blanks for an owner
and a date, in [`README.md`](README.md#open-before-the-next-campaign-block).

## Periodic review

Review this JHA at least every other year (§6). Review it sooner if the work changes, for
example when:
- the E-stop is installed, or the enclosure changes;
- there's a new end effector, or a new control path such as ROS 2 or LeRobot;
- the arm moves next to the CubXL or OT-2;
- the firmware is updated;
- there's a near miss or an injury.
