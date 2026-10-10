**Brigham Young University**

# Standard Operating Procedure (DRAFT): AgileX PiPER robot arm cell, spot D

Laid out like Appendix B of the College of Engineering
[Laboratory & Shop Safety Plan](https://github.com/vertical-cloud-lab/byu-vcl/blob/b00e137/byu-engineering-lab-safety-plan-chemical-hygiene-plan-2024.pdf)
(March 26, 2024). It goes with the [hazard analysis](hazard-analysis.md); H-numbers refer to
the hazards there. `[unverified]` and `[to measure]` mark numbers nobody has checked (see
[`README.md`](README.md#how-numbers-are-marked)). Blanks are for the lab to fill in.

| | |
|---|---|
| **Principal Investigator** | |
| **Primary Contact** | |
| **Secondary Contact** | |
| **Lab #** | |
| **Building** | |

**Contents**
- [Important phone numbers](#important-phone-numbers)
- [Description of work and scope](#description-of-work-and-scope-of-sop)
- [Prequalifications](#prequalifications)
- [Chemicals used](#chemicals-used)
- [Summary of physical hazards](#summary-of-physical-hazards)
- [Summary of chemical hazards](#summary-of-chemical-hazards)
- [Equipment required](#equipment-required-to-perform-work)
- [Engineering controls](#engineering-controls)
- [PPE](#personal-protective-equipment-ppe)
- Step-by-step procedures:
  - [A. Before the next campaign block (one time)](#a-before-the-next-campaign-block-one-time)
  - [B. Start of a session](#b-start-of-a-session)
  - [C. Reaching in (lockout)](#c-reaching-into-the-cell-lockout)
  - [D. Powered runs and "workspace clear"](#d-powered-runs-and-the-workspace-clear-rule)
  - [E. The teach button](#e-the-wrist-teach-button)
  - [F. End of session](#f-end-of-a-session)
  - [G. Restart after an E-stop](#g-restart-after-an-e-stop)
  - [H. After a power outage](#h-after-a-power-outage)
  - [I. After a failed or frozen run](#i-after-a-failed-or-frozen-run)
- [Emergency procedures](#emergency-procedures)
- [Unwanted lab material](#unwanted-lab-material-collection-procedures)
- [Training and sign-off](#summary-of-what-training-is-required)
- [Chemical spill / release](#chemical-spill--release-procedures)
- [Attachment: lab layout](#attachment-lab-layout)
- [Appendix: proposed sign text](#sign-text-proposed)

## Important phone numbers

These are from the College plan (March 2024). Confirm they're current before posting.

| | |
|---|---|
| Emergency | 911 |
| University Police | 801-422-2222 |
| Risk Management | 801-422-4468 |
| Chemicals Management | 801-422-6382 |
| College Health & Safety Officer | 801-422-6589 |
| Poison Control | 800-222-1222 |
| Physical Facilities (transformer) | ________ (not in the plan; fill in) |
| PI / lab manager (cell) | ________ |

| | Name | Date |
|---|---|---|
| **Completed By** | Draft by Claude (AI) from this repo's record, for review | 2026-10-10 |
| **Edited By** | | |
| **Reviewed By** (College Health & Safety Officer) | | |
| **Approved By** (PI) | | |

## Description of work and scope of SOP

This SOP covers anyone who works at, or starts motion on, the AgileX PiPER arm at spot D. That
includes the person at the arm, remote operators running scripts on the arm Pi, people who ask
`@claude` to move the arm, and anyone using the lab PC's WSL2 setup.

It covers:
- powering the arm;
- reaching into the cell;
- powered runs, including agent-driven ones;
- the wrist teach button;
- stops, outages and failed runs;
- work near the atomizer's transformer;
- emergencies.

It doesn't cover:
- the atomizer;
- the CubXL's own motion;
- whatever the vials hold;
- installing software on the Pi, or changing its configuration.

This draft doesn't move the arm or change the Pi, and none of its steps ask the reader to type
commands on the Pi. Where a step needs a Pi-side action (stopping a job, a read-only status
check), the remote operator who owns the run does it, as they do today.

The next block is the reliability campaign in [#21](https://github.com/vertical-cloud-lab/robot-arms/issues/21).
It runs hundreds of trials per condition, and a person resets the scene between trials. §C is the
step that person repeats most.

## Prequalifications

- **Person at the arm:** has done the training below and signed the sign-off table. Knows where
  the E-stop is and has pressed and restarted it at least once with the arm at rest, under
  supervision.
- **Remote operator** (runs scripts on the Pi or asks `@claude` for motion): has the same
  training, has read the "arm Pi" section of [`CLAUDE.md`](../../CLAUDE.md), and knows how to
  stop a running job and cancel a GitHub Actions run.
- **Visitors:** stay outside the marked reach and the transformer zone, with a trained person
  present.

## Chemicals Used

None in this SOP. If the campaign's vials hold anything other than air or inert solids, that
material needs its own SDS and SOP.

## Summary of Physical Hazards

All of these are rated in the [hazard analysis](hazard-analysis.md).

- **Moving arm** (H1–H5). Pinch at the gripper and the elbow, strikes from the arm, motion
  started remotely or by an agent, and the teach button replaying a stored path.
- **No hardware E-stop yet** (H8). Until one is installed, the only way to stop the arm is to
  pull its plug.
- **Power loss** (H6, H7, H15). The arm drops when power is cut, re-energizes by itself after an
  outage, and a failed run can leave it raised.
- **Canvas dome** (H9). It has no interlock, it hides the arm, and part of the arm's reach is
  outside it.
- **Atomizer high-voltage transformer** (H10). The 190 mm clearance hasn't been measured.
- **Power supply** (H11). 120 V AC on the cord and brick.
- **Vials, tipping and reaching** (H12–H14).

## Summary of Chemical Hazards

None in scope. The atomizer's metal powders belong to its own procedures.

## Equipment Required to Perform Work

- The arm, gripper, wrist camera, power brick and US cord. The USB-CAN adapter, the arm Pi, and
  the side camera.
- **The E-stop:** a latching plug-in switch with anti-restart. #18 recommends the POWERTEC 71970.
  **It isn't installed yet.**
- A cover and label for the wrist teach button. **Not fitted yet.**
- The sign (see the [proposed text](#sign-text-proposed)) and this SOP's [checklist](checklist.md),
  printed and posted at the cell.
- Floor and wall tape for the reach marking and the transformer zone. A tape measure for
  measurement M1.
- A logbook for stops, near misses and the end-of-session state. Paper or a GitHub issue both
  work.
- Safety glasses, a brush and pan, and a glass-disposal box.

## Engineering Controls

| Control | Status |
|---|---|
| Latching E-stop with anti-restart, mounted outside the reach | **Not installed.** Install and test before the block (§A) |
| E-stop used as a lockout before reaching in | Depends on the E-stop |
| Cover over the wrist teach button | **Not fitted** |
| Script guards: nothing sent without `--go`; refuse without joint feedback or away from rest; speed caps; motors off only at rest | In `piper_up_down.py` (PR #16) and `piper_pick_tape.py` (PR #20). Not merged |
| Dome | Visual barrier only. **No interlock.** An interlock or a rigid latched front is recommended (H9) |
| Transformer keep-out zone, taped | **Not marked.** Comes after measurement M1 |
| Base bolted to the plywood | **Not recorded.** Confirm in §A |
| Software keep-in box at the dome walls | Not implemented |

## Personal Protective Equipment (PPE)

- Safety glasses for anyone within about 1 m of a powered run (proposed distance).
- Closed-toe shoes.
- Cut-resistant gloves only for cleaning up broken glass. Don't wear gloves near the gripper
  during a run. Nobody should be there anyway.
- PPE doesn't replace the lockout in §C.

## Step-by-Step Procedures for How to Safely Perform Work

**Until the E-stop is installed:** wherever this SOP says "press the E-stop", unplug the arm's
power cord. The outlet must be reachable without reaching past the arm. Unplugging gives no
anti-restart: plugging back in powers the arm straight into Stand By. The draft's
recommendation, for the review team to decide, is to start the campaign block only once the
E-stop is installed and tested.

### A. Before the next campaign block (one time)

These are prerequisites. Record each one in [`README.md`](README.md#open-before-the-next-campaign-block)
with a name and date.

1. **Measurement M1: transformer clearance** `[to measure]`.
   - **The rule.** Per @gage-erickson in [#2](https://github.com/vertical-cloud-lab/robot-arms/issues/2#issuecomment-6089392188),
     nothing may be within 7.5 in (190 mm) of the atomizer's transformer or above it. Its written
     source is unknown `[unverified]`.
   - **Safety while measuring:**
     1. Power the arm down at rest first.
     2. Don't touch the transformer, open any cover, or put the tape measure on it. Measure from
        about 10 mm off its surface and add 10 mm, or use a laser distance meter.
     3. If anything touches or overhangs the transformer, stop and tell the PI. Don't move it
        yourself if that means reaching into the zone.
   - **Measure:**
     1. The shortest horizontal distance from each face of the transformer's enclosure to each
        item in the table below.
     2. Whether anything is above it.
     3. The distance from the arm's J1 axis (the base centre) to the nearest face. Subtract 626 mm
        plus the fingertip length beyond the flange (about 150 mm `[unverified]`) to get the
        reach margin.
   - **Record:** photos with the tape in frame, committed to this repo next to this file.

   | Item | Nearest transformer face | Distance (mm) | Anything above it? | ≥ 190 mm and nothing above? | Photo |
   |---|---|---|---|---|---|
   | Pick-up shelf (as built, after any cut) | | | | | |
   | Table / deck edge | | | | | |
   | Dome frame | | | | | |
   | Dome canvas, including the flap rolled up and down | | | | | |
   | Arm power cord, brick, Pi and camera cords | | | | | |
   | E-stop box and its cords | | | | | |
   | Arm reach margin (J1 axis to face, minus 626 mm, minus fingertip length) | | | | | |
   | Anything else nearby | | | | | |

   - **Pass:**
     - every row is 190 mm or more, and nothing is above the transformer;
     - the reach margin is 190 mm or more, or the review team accepts a software keep-out instead;
     - someone has asked the transformer's owner for the rule's source and its rating (read the
       nameplate, don't open anything).
   - Then tape the zone on the floor and wall.

2. **E-stop.**
   1. Install it per [#18](https://github.com/vertical-cloud-lab/robot-arms/issues/18#issuecomment-6092117783):
      plug only the arm's brick into it, not the Pi. Screw the box down.
   2. Mount it outside the reach, where someone standing at the arm can hit it without leaning
      over the arm. Record the location on the layout.
   3. Check its label for a Listed mark (§10 of the plan expects "Approved" equipment).
   4. Test it once with the arm at rest and nobody near: press, twist out and confirm nothing
      powers up, then START.
   5. The Pi side of the test (confirming the arm stops answering, then answers again) is a
      read-only check for an authorized operator. Request it separately.
3. **Teach button.** Fit the cover and the label.
4. **Sign.** Post the agreed text (see the [proposed text](#sign-text-proposed)) and commit a
   photo of it as posted.
5. **Base.** Confirm the arm is bolted to the plywood and the plywood is fixed to the table.
   Record how.
6. **Electrical.** Confirm the brick and cord carry an NRTL mark, and that the brick is outside
   the dome, uncovered and off the floor.
7. **Marking.** Tape the reach on the table and floor. Label the dome flap "Flap down = arm may
   move. Press the E-stop before lifting."
8. **Who can start motion.** List who can trigger `@claude` runs and who has SSH to the Pi. Share
   the list with the person at the arm.
9. **Layout.** Attach the marked-up layout (see the [Attachment](#attachment-lab-layout)).

### B. Start of a session

The person at the arm does this.

1. Read the sign. Check that the E-stop is reachable and nothing blocks it.
2. Look at the arm:
   - Is it at rest (folded)?
   - Is the wrist LED off (Stand By, or no power)?
   - Is the teach-button cover in place?
   - Are the cords undamaged and off the floor?
   - Is the transformer zone empty?
3. Tell the lab channel you're at the arm, and who the remote operator is for this session.
4. Check that nobody else is in the reach or under the dome.

### C. Reaching into the cell (lockout)

Do this every time a hand goes into the reach, including each scene reset.

1. Wait until the arm is **at rest and still**. If a run is going, wait for it to finish and
   park, or ask the operator to stop it. Don't cut power with the arm raised unless it's an
   emergency (H6).
2. **Press the E-stop.** The arm goes limp at rest, and any script that tries to start exits
   with no joint feedback.
   - If the motors were stiff (Stand By after a START), the wrist settles about 10 mm onto the
     J2 motor as power goes ([#19](https://github.com/vertical-cloud-lab/robot-arms/issues/19#issuecomment-6092030025)).
     Keep fingers away from there.
3. Lift the flap and do the work. Keep fingers out of the gripper and the elbow fold. Don't
   press the wrist button.
4. Hands, tools and loose items out. Flap down.
5. Restart as in [§G](#g-restart-after-an-e-stop), steps 5–7. That's the short version, because
   the stop was planned. The next run's own start checks (live feedback, arm at rest) stand in
   for step 8, and it still needs a "workspace clear" (§D).

### D. Powered runs and the "workspace clear" rule

**Before every powered run**, whoever starts it gets a "workspace clear" from the person at the
arm. Proposed meaning:

- A trained person is **physically at the cell**, and is standing at the E-stop, outside the reach.
- Nobody is inside the reach or under the dome. The flap is down and the arm is at rest.
- That person **stays at the E-stop for the whole run**. A run starts only while someone is
  there.
- It covers **one run** and expires after 10 minutes (proposed). A re-run, or a job that starts
  late, needs a fresh one.
- A remote person who can't see the cell can't declare it.

**For an `@claude` run,** the triggering comment says "workspace clear" and names the person at
the E-stop. That matches the CLAUDE.md rule: no motion unless the request asks for it and says
the workspace is clear. The agent also grabs a side-camera frame right before enabling the motors
and stops if anyone is visible, as in #15. That check is current practice; the scripts don't
enforce it. The camera can't see depth, so it adds to the person's check and doesn't replace it.

**During a run:**
- Stay at the E-stop and watch the arm.
- Press the E-stop if a person or anything unplanned enters the reach, or if the arm heads
  somewhere unexpected. That includes outside the dome, toward the shelf edge, or toward the
  transformer.
- Remember the arm drops when you press it.

**Afterwards:** the operator confirms the run ended at rest with the motors off. If it didn't,
see §I.

### E. The wrist teach button

- During a campaign block, nobody presses it.
- If a teach session is needed, it's a separate supervised task:
  - the arm starts at rest;
  - nobody else is in the reach;
  - the recording ends at rest;
  - afterwards, assume the recorded path is still stored (#18).
- LED states (#7):
  - off: Stand By, motors stiff;
  - on: recording;
  - flashing: playback.
- If it flashes when nobody meant it to, step out of the reach, then press the E-stop.

### F. End of a session

1. The operator confirms the arm is at rest with the motors off and no job running.
2. Look: the arm is folded, the LED is off, and the transformer zone and the floor are clear.
3. Decide on power:
   - Leave it on for remote use only if the arm is at rest and limp, and the sign is posted.
   - Turn it off overnight or when nobody will use it for a while. AgileX advises powering off
     after use (§6.1 of its manual, quoted in #18 `[unverified]`).
4. Log anything odd: stops, near misses, anything that touched something it shouldn't have.

### G. Restart after an E-stop

Use all of it after an unplanned stop. After a planned lockout (§C), do steps 5–7 only.

1. **Make it safe:**
   - Is anyone hurt? Do the [emergency steps](#emergency-procedures) first.
   - Don't release the E-stop yet.
2. **Stop every motion source:**
   - The remote operator stops the job on the Pi and cancels any queued or running `@claude`
     run in the Actions tab.
   - Post in the lab channel that the arm is stopped.
   - The Pi and the USB-CAN adapter keep their power, so a running script keeps sending moves.
     By #18's estimate that can go on for up to about 40 s `[unverified]`.
3. **Look, with power still off:**
   - Where is the arm? Did it drop, and onto what?
   - Check for damage to the arm, gripper, cords, shelf, dome and CubXL.
   - Pick up anything dropped. Use a brush and pan for glass. Don't reach into the transformer
     zone.
4. **Park by hand:**
   - Move the arm to the rest pose. It moves freely with the power off (#18).
   - Support the forearm and keep fingers out of the elbow fold.
   - Use two people if it's tangled.
5. **Clear the reach:** people, tools and loose items out. Flap down.
6. **Release the E-stop** (twist out). Confirm nothing powers up: that's the anti-restart.
7. **Say "arm power on" out loud** and in the lab channel, then press START from outside the reach.
   - The arm comes back stiff in Stand By and holds its pose (#7).
   - Check the wrist LED is off. If it flashes, press the E-stop.
8. **Status check:**
   - The operator runs the read-only status check: joint feedback present, no driver faults,
     joints at rest. After an unplanned stop, the next run needs a fresh "workspace clear" (§D).
   - If the stop involved an injury, a collision, damage, or a cause nobody understands, don't
     restart. Tell the PI, and leave the E-stop pressed until they say go.
9. **Log it:** time, who, why, what the arm did, and what was done. Report near misses to the PI,
   as §11 of the plan asks.

### H. After a power outage

1. Until the anti-restart E-stop is installed, the arm comes back on by itself in Stand By (H7).
   Treat it as live.
2. With the E-stop installed, it stays off until START.
3. Before START, ask the operator to confirm no job is waiting to resume, then do §G steps 3–9.
4. After a Pi reboot, CAN may need bringing up by an authorized operator before remote runs work
   (#18). That fails safe, and this SOP doesn't do it.

### I. After a failed or frozen run

1. The arm may be holding a raised pose with the motors on (H15). **Don't cut power** unless it's
   an emergency: it would drop.
2. Keep out of the reach. The operator decides with the PI how to bring it back to rest. A
   supported damped stop is one option, an authorized move home is another. Neither is written
   here, because this SOP doesn't move the arm.
3. Once it's at rest, run §G steps 3–9 and log it.

## Emergency procedures

§7 of the College plan asks every SOP for an emergency section. This one takes the place of the
template's chemical spill section, which doesn't apply here.

**Serious injury, fire, or electrical shock: call 911, then University Police 801-422-2222.**

| Event | Do this |
|---|---|
| **Arm hits or pins someone** | 1. Press the E-stop. The arm goes limp and drops, so support it if you can and keep clear of where it'll fall. 2. Free the person by moving the arm by hand; it moves freely with no power. Whether the gripper fingers open by hand with no power isn't known `[unverified]`. 3. First aid, then call. 4. Leave the E-stop pressed. Tell the PI and the College Health & Safety Officer (801-422-6589) |
| **Unexpected motion** (a remote run, teach playback) | 1. Step back out of the reach first. 2. Then press the E-stop if the arm is hitting something, heading out of the dome, or toward someone. 3. Tell the lab channel and cancel any runs. 4. Restart per §G only once the cause is known |
| **Arm falling** (power loss) | Don't reach under it or try to catch it. Let it settle, then follow §G |
| **Smoke or a burning smell from the arm, brick or cords** | Press the E-stop if you can reach it safely, and unplug at the wall if that's safe. Don't use water on electrical equipment. If it's burning, pull the fire alarm, evacuate and call 911. Fire extinguisher location: ________ |
| **Anything wrong at the transformer** (smoke, noise, smell, something touching it) | Don't approach it or touch it. Keep others back. Call Physical Facilities (________) and the PI. If there's fire or smoke, evacuate and call 911. If you can reach the arm's E-stop without going near the transformer, press it |
| **Electrical shock** | Don't touch the person while they may still be in contact. Cut power at the E-stop or the plug if safe, then call 911 |
| **Building alarm or evacuation** | If you can do it in a few seconds, press the E-stop. The arm should be at rest; if it's raised, leave it. Leave the building. With the E-stop pressed, remote runs can't start while the building is empty |
| **Earthquake** | Protect yourself first. Afterwards, check the arm, shelf, dome and transformer zone, and press the E-stop before touching anything |
| **Suspected unauthorized remote control** | Press the E-stop and leave it pressed. Tell the PI |

After any emergency or near miss: tell the PI the same day, log it, and review the JHA (it asks
for a review after near misses).

## "Unwanted Lab Material" Collection Procedures

The arm work makes no chemical waste. Broken glass goes in a glass-disposal box. Damaged parts
go to the PI. Anything from the atomizer follows its own procedures.

## Summary of What Training is Required

§8 of the College plan bases training on the JHA and the SOP.

| Who | Training |
|---|---|
| Everyone in the spot-D area | Read the sign. Know where the E-stop is, the reach marking, and the transformer zone |
| Person at the arm | 1. Read this SOP, the [hazard analysis](hazard-analysis.md) and the [checklist](checklist.md). 2. The College online safety course(s) the PI names: ________. 3. The safety sections of the AgileX manual. 4. Hands-on with a signed-off member: press and restart the E-stop with the arm at rest, the wrist LED states, the "workspace clear" handshake, the §C lockout, and the emergency steps |
| Remote operator | Everything above, plus the "arm Pi" section of [`CLAUDE.md`](../../CLAUDE.md), stopping a job, cancelling an Actions run, and the read-only status check |
| Refresher | Whenever this SOP changes, and at least every other year (§7, §8 of the plan) |

**Sign-off.** I have read this SOP and the hazard analysis, had the hands-on training, and agree
to follow them.

| Name | Role (at the arm / remote / both) | Trained by | Date | Signature |
|---|---|---|---|---|
| | | | | |
| | | | | |
| | | | | |
| | | | | |
| | | | | |
| | | | | |

## Chemical Spill / Release Procedures

Not applicable: this SOP uses no chemicals. For a spill from the vials or the atomizer, follow
that work's own SOP, or call Risk Management (801-422-4468) or University Police (801-422-2222).

## Attachment: Lab Layout

To attach before review: a plan of spot D, marked with:
- the arm and its reach (626 mm from the J1 axis, plus the fingertips);
- the dome outline and flap;
- the shelf, as built;
- the CubXL, if it's in the cell;
- the E-stop location;
- the transformer and its 190 mm zone;
- the door, the fire extinguisher and the nearest phone.

The floor plan used in [#2](https://github.com/vertical-cloud-lab/robot-arms/issues/2) is a
starting point. It needs the transformer added, as #2 notes.

## Sign text (proposed)

The sign's current wording isn't in the repo. This version builds on the four rules suggested in
[#18](https://github.com/vertical-cloud-lab/robot-arms/issues/18#issuecomment-6091777194) and the
CLAUDE.md "workspace clear" rule. If the posted sign says something different, reconcile the two
and update CLAUDE.md to match.

> **CAUTION: THIS ARM CAN MOVE AT ANY TIME.** Remote users and AI agents can start it.
> 1. **Press the E-stop before you reach in.** Release it only after you're out and have told
>    the lab channel.
> 2. **"Workspace clear"** means nobody in reach, the flap down, and you at the E-stop for the
>    whole run.
> 3. **Don't touch the button on the wrist.** Two presses replay a stored path that doesn't stop
>    for people.
> 4. **Leave the arm limp only when it's folded at rest.** It drops when power is cut.
> 5. **Keep everything 190 mm (7.5 in) from the transformer, and nothing on top of it.**
>
> Emergency: 911 · University Police 801-422-2222 · College Health & Safety 801-422-6589 ·
> PI ________
