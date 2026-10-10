# Pre-registration: how reliably can the PiPER load a CubXL?

**Status: draft, not locked.** No counted trial may run until this file is locked. To lock it,
fill every `F` field in [§0](#0-fill-in-before-locking), commit, tag the commit `prereg-v1`, and
write the hash below. Changes made after the lock go in [§14](#14-amendments), dated and with a
reason. Never rewrite the original text.

| | |
|---|---|
| Locked commit / tag | `F0: ____` / `prereg-v1` |
| Lock date | `____` |
| Campaign issue | #21 |
| Arm | AgileX PiPER: 6-DOF, 1.5 kg payload, 626 mm reach, 0.1 mm repeatability ([AgileX](https://global.agilex.ai/products/piper)) |
| Design this tests | The dock, the 8 + 1 carrier and the single-vial pockets from [byu-vcl#266](https://github.com/vertical-cloud-lab/byu-vcl/issues/266) ([README](https://github.com/vertical-cloud-lab/byu-vcl/blob/f784f6b/robot-arm/cubxl-vial-handling/README.md)), and the Spot D pick-up shelf (#9) |

This is the plan for the PiPER reliability paper. Before any counted trial, it fixes what we
measure, how each hypothesis is decided, and when we stop. Later pieces of the campaign land
on the same PR: the analysis scripts, the trial harness, the repeatability fixture and the
fiducial correction. Each must do what this file says. Where one can't, amend this file first.
Nothing in this document moves the arm.

---

## 0. Fill in before locking

Everything marked `F#` below is a number or choice for the PI. Suggestions in the last column
come from #266 and the arithmetic in this file. They are not decisions.

| ID | What | Where used | Suggestion |
|---|---|---|---|
| F1 | Setting: mock-up v2 or the real CubXL | §3 | Mock-up v2 for E1 and E2, with a short confirmation block on the real CubXL (§13) |
| F2 | Vials: printed dummies or glass; body OD; mass | §3 | Printed at 100 % infill (≈ 47 g, close to a full vial) |
| F3 | Carriers A and B: vial load and mass | §3 | Both full of dummies (≈ 0.50–0.63 kg for 8 + 1) |
| F4 | Dock pocket used by T2; diametral clearance *c* (≤ 1.0 mm); entry chamfer (0 = none) | §3, H1b | Choose *c* and chamfer as built and measure them. Don't design them to the result |
| F5 | Dock datum, cone-pin spacing, pocket distance *r* from the datum | §7 | Datum at the cone pins' midpoint |
| F6 | Wrist camera and lens; tag family, size, placement; frames per look; reprojection limit; look attempts; correction cap | §5 | `tag36h11`, 20 mm, non-coplanar bundle on the dock sidewalls; cap larger than the biggest injected offset |
| F7 | How seating is checked; witness camera | §6 | A seat switch or a 0.2 mm feeler at the corners, plus a fixed witness still after every transfer |
| F8 | Operating speed and velocity profile | §3 | The same in every condition and experiment |
| F9 | Check delay after release; per-transfer timeout; cap-height tolerance (T2) | §6 | 2 s; 3× the median transfer time; ±0.5 mm |
| F10–F17 | Predicted values for H1–H4 | §2 | Yours |
| F18 | *n* loading transfers per task × condition | §7 | 300. Zero failures in 299 is the fewest that certifies 99 % (§12.1) |
| F19 | Units per block | §8 | A whole number of permuted sub-blocks |
| F20 | Second metrology payload | §7 | A dummy mass equal to a full carrier at the carrier's CG |
| F21 | Metrology warm-up | §7 | 15 min of cycling over P1–P5 |
| F22 | Metrology instrument and its expanded uncertainty *U* (k = 2) | §7, H4a | Must be ≤ 0.025 mm |
| F23 | Run-of-failures stop | §9 | 3 in a row, or 5 in the last 20 |
| F24 | Campaign end date | §9 | |
| F25 | MTBI horizon τ (transfers) | §12.4 | 300 |
| F26 | Where raw logs live | §11 | A Hugging Face dataset under `byu-vcl` |
| F27 | Who the operator calls after a Catastrophic event | App. A | PI and the College Health and Safety Officer |

---

## 1. Question and estimands

**Question.** How reliable is this arm at loading a CubXL with vial carriers and with single
vials? And how much of the gap to 99 % per transfer does each of these close: (a) a lead-in
dock, and (b) wrist-camera AprilTag correction?

**Why 99 %.** A self-driving-lab run is a chain of transfers. The chance that 50 transfers
finish untouched is *p*⁵⁰:

| Per-transfer success | 97.5 % | 99 % | 99.5 % | 99.9 % |
|---|---|---|---|---|
| 50 transfers with no intervention | 28 % | 61 % | 78 % | 95 % |

97.5 % is the rate Ada reports (about one run-ending failure per 40 samples, from the Q1 scan
in #1). 99 % is roughly where an overnight run becomes more likely than not to finish.

**Why these two interventions.** #266 puts the arm's placement error at ±0.64 mm combined
(RSS) and ±1.15 mm worst case. The worst case is the linear sum of ±0.10 mm repeatability,
±0.50 mm gripper, ±0.30 mm teaching and registration, and ±0.25 mm structure and humidity.
A tight pocket captures about ±0.6 mm. A 3 mm × 45° lead-in nest captures about ±3 mm. So the
two fixes attack the problem from opposite sides:

- **The dock widens capture.**
- **The correction shrinks error.** It measures where the dock really is, which removes the
  teaching, registration and structure terms. It can't see the vial's position in the
  fingers, so the ±0.5 mm gripper term stays. Once corrected, the worst case is about
  ±0.6 mm plus the tag-pose error. A pocket with 1 mm diametral clearance allows ±0.5 mm. So
  correction should help single vials without guaranteeing 99 %. This is an expectation,
  not a hypothesis.

**Estimands.** *T* is the task (C = carrier, V = single vial). *K* is the condition (OL = open
loop, AT = AprilTag-corrected).

- *p*(*T*, *K*): the probability that a loading transfer succeeds at zero injected offset.
  This is the primary endpoint. Unloading is secondary.
- Gap to 99 %: *g*(*T*, *K*) = max(0, 0.99 − *p*(*T*, *K*)).
- Share of the gap closed by correction:
  *G*(*T*) = [*p*(*T*, AT) − *p*(*T*, OL)] / [0.99 − *p*(*T*, OL)]. It is defined only when
  *p*(*T*, OL) < 0.99.
- Contribution of the lead-in dock, measured two ways:
  - (i) The task contrast *p*(C, OL) − *p*(V, OL). This is confounded by the object (§13).
  - (ii) The mechanism: the dock's ED90 capture radius set against the arm's error budget
    (H2).
- ED50 and ED90: the injected offset at which predicted success falls to 50 % or 90 %.
- MTBI: the mean number of transfers between interventions.
- RP: pose repeatability as defined in ISO 9283.

---

## 2. Hypotheses

Each hypothesis gets its own α = 0.05, one-sided where stated. There is no multiplicity
correction, because each answers a separate question fixed here in advance. Every outcome is
reported, whether it supports the hypothesis, refutes it or is inconclusive. Predictions are
recorded for calibration only. They do not enter any decision rule.

### H1: the dock reaches 99 %, the tight pocket does not

- **H1a.** Open-loop carriers loaded into the 3 mm lead-in dock succeed at 99 % or better.
  - Prediction: *p*(C, OL) = `F10: ____ %`.
  - Supported if the exact one-sided 95 % lower bound is ≥ 0.99. At *n* = 300 that allows
    no failures: 0/300 gives 0.9901, while 1/300 gives 0.9843.
- **H1b.** Open-loop single vials loaded into dock pockets with ≤ 1 mm diametral clearance
  (`F4`) stay below 99 %.
  - Prediction: *p*(V, OL) = `F11: ____ %`.
  - Supported if the exact one-sided 95 % upper bound is < 0.99. At *n* = 300 that takes
    at least 7 failures.
- **Inconclusive band.** At *n* = 300, between 1 and 6 failures certifies neither "≥ 99 %"
  nor "< 99 %". That is reported as inconclusive, and the cell is not extended (§9, rule 4).

### H2: the dock's capture radius exceeds the arm's worst-case error

- **Claim.** The dock's ED90 capture radius is larger than the ±1.15 mm worst-case arm error
  from #266. The capture radius is min(ED90ₓ, ED90ᵧ) for the carrier, open loop.
- **Prediction.** ED90ₓ = `F12: ____ mm`, ED90ᵧ = `____ mm`, ED90 for yaw = `____°`.
- **Decision.** Supported if the one-sided 95 % lower bounds of both ED90ₓ and ED90ᵧ exceed
  1.15 mm. This is an intersection–union test, so it needs no adjustment. Yaw is reported
  but not tested.
- **Model-free check.** Supported only if the four ±2 mm translation levels together (80
  trials) also have an exact one-sided 95 % lower bound of at least 0.90, which allows 3
  failures at most. If success falls monotonically with offset, that alone puts ED90 above
  2 mm.
- **What the offset means.** It is injected on top of the arm's own error. "ED90 > 1.15 mm"
  therefore means the dock still catches 90 % of carriers after the arm has been pushed a
  further 1.15 mm off.

### H3: correction raises single-vial success and widens ED90, at a cost of a few seconds

- **H3a.** *p*(V, AT) > *p*(V, OL).
  - Prediction: OL `F13: ____ %`, AT `____ %`.
  - Decision: a one-sided Boschloo exact test with *p* < 0.05.
  - Power at *n* = 300 per condition, from the one-sided Fisher test (Boschloo is at least
    as powerful):

    | OL → AT | Power |
    |---|---|
    | 95 % → 99 % | ≈ 0.87 |
    | 97 % → 99.5 % | ≈ 0.67 |
    | 97 % → 99 % | ≈ 0.41 |

    So H3a can only be detected if open-loop single vials are around 95 % or worse.
- **H3b.** For single vials, ED90 under AT is larger than under OL.
  - Prediction: `F14: ____ mm` wider.
  - Decision: for both x and y, the one-sided 95 % bootstrap lower bound of
    ED90_AT − ED90_OL is > 0.
  - If AT shows no failures at ±4 mm on an axis, ED90_AT for that axis is censored at
    "> 4 mm" (§12.3). H3b then holds on that axis if the upper 95 % bound of ED90_OL is
    below 4 mm.
- **H3c.** The correction costs no more than `F15: ____ s` per loading transfer.
  - Decision: the upper 95 % bound of the Hodges–Lehmann shift in transfer time (AT − OL)
    is ≤ `F15`.
- **Also reported, not tested.** The same three contrasts for the carrier task.

### H4: ISO 9283 RP is within ±0.1 mm unloaded and grows with payload and reach

- **H4a.** Unloaded RP ≤ 0.10 mm at all five poses.
  - Decision: "meets the spec" if the ISO 9283 point estimate is ≤ 0.10 mm at every pose.
    This is how manufacturers report RP. "Certified" if the bootstrap upper 95 % bound is
    also ≤ 0.10 mm.
  - Inconclusive if the instrument's expanded uncertainty is above 0.025 mm (`F22`).
    ISO 9283 §6.5 caps the total measurement uncertainty at 25 % of the characteristic
    under test.
- **H4b.** RP grows with payload.
  - Prediction: `F16: +____ mm` loaded vs unloaded.
  - Decision: the mean over poses of RP(loaded) − RP(unloaded) has a one-sided 95 %
    bootstrap lower bound > 0.
- **H4c.** RP grows with reach. Reach is the horizontal distance from the J1 axis to the TCP.
  - Prediction: `F17: +____ mm per 100 mm`.
  - Decision: regress RP on reach over 5 poses × 2 payloads, with payload as a covariate.
    The slope's one-sided 95 % bootstrap lower bound must be > 0.

---

## 3. Set-up

Everything below is part of the **configuration** (§8). Changing any of it starts a new
block.

| Item | Specification |
|---|---|
| Arm | AgileX PiPER. Serial, firmware and the base mounting are recorded per configuration |
| Fingers | One set of finger inserts that grips a vial and the carrier's handle post the same way (#266). Pads are recorded per configuration; #266 suggests silicone |
| Wrist camera | `F6`. Mounted and powered in **both** conditions, so mass and cable drag are the same |
| Dock | A nest with a 3 mm × 45° lead-in and two cone pins (#266), pill-keyed and screwed down. Two single-vial pockets. T2 uses the pocket in `F4` |
| Carriers | Two identical 8 + 1 carriers, A and B, with a handle post in slot 5. Load and mass: `F3` |
| Vials | `F2` |
| Shelf | The Spot D pick-up shelf (#9). Two carrier nests and one single-vial pocket, each chamfered generously so the shelf is never the bottleneck. Geometry recorded |
| Witness camera | Fixed, looking at the dock. Takes a still at every check (`F7`) |
| Speed | `F8` |
| Software | The trial harness commit is recorded per block. Joint positions, efforts and gripper state are logged at 100 Hz, the rate `--trace` already uses in #20 |
| Environment | Temperature, relative humidity and illuminance at the dock, logged per block |
| Setting | `F1` |

---

## 4. Tasks

Each task is run in **units**. Every unit holds exactly one *loading* transfer (into the dock:
the primary endpoint) and one *unloading* transfer (out of the dock: secondary). A unit leaves
the cell in a known state, so units of either task can be interleaved.

- **T1: carrier swap between the dock and the shelf.** Carrier A starts in the dock and B in
  shelf nest 2. Each unit swaps them:
  1. **Unload:** the carrier in the dock goes to the free shelf nest.
  2. **Load:** the other carrier goes from its shelf nest into the dock.

  The cell returns to its start state every two units.
- **T2: single vial between the shelf and the dock pocket.** One vial starts in the shelf
  pocket. Each unit:
  1. **Load:** shelf pocket → dock pocket (`F4`).
  2. **Unload:** dock pocket → shelf pocket.

A **transfer** is the pick at the source, the place at the destination, and the retreat to the
clear pose.

---

## 5. Conditions

- **OL: open loop.** Taught poses only. No camera data reaches the motion.
- **AT: AprilTag-corrected.**
  - At the look pose over the dock, the camera grabs `F6` frames and detects the dock's tags.
    It estimates the dock's pose in the base frame through the hand–eye calibration.
  - The place pose is corrected in x, y and yaw before every dock-side place. The pick pose
    is corrected the same way before every dock-side pick. z, roll and pitch stay as taught.
  - The shelf side is open loop in both conditions, because the question is about loading the
    CubXL.
  - If no valid pose arrives within `F6` attempts, or the correction exceeds the cap (`F6`),
    the transfer aborts before descending. That counts as a failure. It never falls back to
    open loop, which would mix the two conditions.

**Both conditions pass through the same look pose and stop there.** OL leaves at once. AT
dwells there to capture and correct. The only differences between the conditions are the dwell
and the correction. Settling at a standstill before the final approach can't masquerade as a
benefit of vision.

**No automatic retries in either condition.** Each pick and each place is a single attempt.
The harness may abort a transfer it judges unsafe, for example a grip effort below threshold
before the lift (#20). An abort counts as a failure.

---

## 6. Success

A transfer is scored at the **check**, `F9` s after the arm reaches the clear pose.

**Loading, T1: success requires all of the following.**
1. The carrier is seated: both cone pins are engaged and it sits flat on the nest floor, as
   checked by `F7`.
2. Every vial is still in its pocket, upright, with its cap on.
3. The gripper released cleanly, the arm reached the clear pose, and the carrier was not
   dragged out of its seat.
4. Nobody touched the cell between the start of the transfer and the check.
5. There was no fault: no controller or CAN error, no E-stop, no collision stop, and no
   contact with the keep-out frame.
6. The transfer finished within the timeout `F9`.

**Loading, T2: success requires all of the following.**
1. The vial sits fully in the pocket, with its cap-top height within `F9` of nominal.
2. It is upright, capped and intact.
3. Criteria 3–6 from T1 hold.

**Unloading:** the same criteria, applied at the shelf.

**These still count as successes.** Each is flagged as a near miss:
- The lead-in doing its job, for example the carrier landing on the chamfer and sliding home
  before the check.
- An effort spike that did not trip a fault.

**Adjudication.**
1. The operator scores every transfer on the spot (App. A).
2. A second person re-scores every failure and a random 10 % of successes from the witness
   stills. The stills are taken after the arm has left, so they don't show the condition.
3. A third person resolves any disagreement.
4. Cohen's κ between the operator and the reviewer is reported.

---

## 7. Experiments and trial counts

### E1: nominal reliability

- 2 tasks × 2 conditions, at zero offset.
- **At least *n* = 300 loading transfers per task × condition** (`F18`). Each comes paired
  with an unloading transfer.
- That is 1,200 loading and 1,200 unloading transfers.

### E2: capture envelope

- **What is offset.** The dock frame the arm *believes* in. The physical dock does not move.
- **The dock frame.** Its origin is the dock datum (`F5`). x runs along the carrier's long
  axis, z points up, and yaw is about z through the origin.
- **Levels.** One axis at a time:
  - 0;
  - x = ±1, ±2, ±3, ±4 mm;
  - y = ±1, ±2, ±3, ±4 mm;
  - yaw = ±2°, ±4°.

  That is **21 levels × 20 trials = 420 loading transfers per task × condition**, and 1,680
  in all.
- **Which leg is offset.** Only the loading leg. The unloading leg runs at the nominal frame.
  After a successful load the object sits where the dock put it, so the nominal frame is
  correct.
- **Under AT,** the look pose moves with the believed frame, and the correction has to find
  the real dock from the image. The injected offset never reaches the correction code.
- **For T2,** a yaw of the dock frame moves the pocket sideways by about *r*·θ (`F5`).

**Expect the yaw levels to saturate for open-loop carriers.** If the cone pins are 225 mm apart
(the holder's key spacing), a yaw of θ moves each pin 112.5·sin θ:

| Yaw | 0.5° | 1° | 2° | 4° |
|---|---|---|---|---|
| Pin displacement | 1.0 mm | 2.0 mm | 3.9 mm | 7.9 mm |

So both ±2° and ±4° are past a 3 mm lead-in, and the OL carrier's yaw curve will probably
have no informative points. §13 lists an optional ±0.5° / ±1° extension.

### E3: ISO 9283-style metrology

- **Size.** 5 poses × 30 cycles × 2 payloads, which is 300 measured pose visits.
- **Poses.** P1–P5 lie on the diagonal plane of the largest cube that fits the volume the
  campaign uses, around the dock and the shelf. P1 is at the plane's centre and P2–P5 sit near
  its corners. Secondary sources put them at 10 % ± 2 % of the diagonal in from the corners;
  check that, and the visiting sequence, against §6.8 of the standard before building the
  fixture.
- **Cycles.** Each cycle visits every pose in a fixed order, approaching each one from the same
  direction. That one-way approach is how ISO 9283 keeps backlash out of RP. Dwell before
  measuring: `F21`.
- **Payloads.**
  - (1) Unloaded: the gripper plus the measuring target.
  - (2) Loaded: `F20`.

  ISO 9283 makes 100 % rated load (1.5 kg) mandatory, and 10 % of it an optional extra test.
  The loaded case here is the task load, which makes E3 ISO 9283-*style*, not conformant.
  Instrument parts carried by the arm count toward the payload (§6.6).
- **Speed.** The campaign speed (`F8`), so RP describes the motion the trials use. ISO 9283
  asks for 100 % override; add that as a third run if time allows.
- **Warm-up.** `F21`. ISO 9283 §6.2 asks for an appropriate warm-up if the manufacturer
  specifies one.
- **Instrument.** The repeatability fixture, which comes in a later ping. It must resolve the
  TCP's 3D position with *U* ≤ 0.025 mm (k = 2), as recorded in `F22`.
- **Order.** Both payloads run in one session, in random order, with temperature logged.

**Only positional RP is measured.** Orientation repeatability and AP (pose accuracy, which
needs an absolute reference such as a laser tracker) are out of scope.

### Budget

| | Scored | Transfers, including resets |
|---|---|---|
| E1 | 1,200 loads + 1,200 unloads | 2,400 |
| E2 | 1,680 loads | 3,360 |
| E3 | 300 pose measurements | — |
| **Total** | | **5,760 transfers** |

At 30 s per transfer that is about 48 h of arm time. At 45 s it is about 72 h.

---

## 8. Configurations, blocks and randomization

- **Configuration.** Everything that can change how the arm behaves:
  - the harness commit, including any code, config or calibration file on the trial path;
  - the arm, its firmware and its mounting;
  - the fingers and pads;
  - the camera and its mount;
  - the dock, carriers, vials and shelf, and where each of them sits;
  - the taught points and the hand–eye calibration.

  Each configuration gets an ID (`cfg-N`) and a record of its commit and hardware. The record
  can also list **spares**, parts identical to ones in use, that may replace a broken part
  without creating a new configuration.
- **Block.** A contiguous run of units in one session, under one configuration, following one
  schedule. A new session always starts a new block.
- **Randomization.** The schedule is generated and committed before the block's first unit,
  from a seed equal to the block ID. Units run in that order. The operator does not choose,
  skip or reorder them.
  - **E1 blocks** use permuted sub-blocks of 4 units: T1-OL, T1-AT, T2-OL and T2-AT, each once
    in random order.
  - **E2 blocks** use permuted sub-blocks of 84 units: 21 levels × 2 conditions × 2 tasks.
    Twenty sub-blocks complete E2.
  - **Block size** is `F19` units.
- **Block types.** E1 and E2 run in separate blocks. A pre-generated random sequence assigns
  each session to E1 or E2, so wear, drift and season fall on both.

---

## 9. Stop rules

1. **Any change to code or hardware ends the block.** The next unit starts a new block.
   - **The count restarts.** If the change creates a new configuration, its counts start at
     zero. Each cell's *n* must be reached within one configuration. Earlier configurations
     are reported as development history and are never pooled into the primary estimates.
   - **These are changes:**
     - any commit on the trial path;
     - re-teaching a point or recalibrating;
     - replacing, re-printing, re-gluing, tightening or adjusting a part;
     - moving the arm, table, dock, shelf or CubXL;
     - a firmware update;
     - new pads;
     - cleaning or refocusing the camera.

     Swapping in a declared spare ends the block but keeps the configuration.
   - **These are not changes:** the scripted reset, and restoring the scene after a failure
     without adjusting anything (re-seating an object, re-homing, a power cycle). These are
     interventions (§12.4). They are logged, and the block continues.
2. **Safety.** A **Critical** or **Catastrophic** event (§10.4) stops the block at once. Make
   the cell safe per the SOP (#22) and record what happened. Resuming always starts a new
   block.
3. **Run of failures.** `F23` (3 in a row, or 5 in the last 20) stops the block for an
   inspection. Anything the inspection fixes is a change under rule 1. Trials before the stop
   stay in the data.
4. **No stopping on results.** Each cell's *n* is fixed. Don't stop early because it looks good
   or bad. Don't extend past *n* because one failure spoiled the bound: that is optional
   stopping, and it voids the exact bounds. Rules 2 and 3 are the only interim looks, and both
   are for safety.
5. **End.** A cell ends at *n*, or at `F24`. Incomplete cells are reported with their actual
   *n*. Sessions end between units, never in the middle of one.

**Exclusions.** Only these two kinds are allowed:
- (a) An external interruption, such as a person entering the workspace, an alarm or a
  building power cut. The unit is marked *interrupted* and re-queued at the end of the
  schedule.
- (b) An operator error in the scripted reset. It is marked *operator error*.

Both are logged and counted. If they exceed 5 % of any cell, the report says so up front.

---

## 10. Failure coding: LabRobFail

**Source.** Wang, H., Sun, B., Zou, A., Huang, D., Lv, Z., Wang, N., Li, R., Zhou, D., Guo, W.,
Wang, Z. and Ouyang, W. (2026). *LabRobFail: A Benchmark for Robotic Failure Analysis in
Chemical Self-driving Laboratory.* arXiv:2607.23704v2 (29 Jul 2026),
[doi:10.48550/arXiv.2607.23704](https://doi.org/10.48550/arXiv.2607.23704). The code is at
[Su-ISE-2001/SciRobo](https://github.com/Su-ISE-2001/SciRobo), which now redirects to
`Su-ISE-2001/LabRobFail`.

LabRobFail's 20,000 trajectories are failures injected in simulation, so we take its labels
and none of its rates. Text in quotation marks is verbatim from v2. Everything labelled *ours*
is this campaign's rule.

### 10.1 Five categories

From *LabRobFail-Data → Fine-grained Failure Taxonomy*:

> "We design a systematic taxonomy covering 5 major categories and 11 fine-grained types
> (Fig. 3(b)), spanning the full spectrum of anomalies: (1) Perception Failure (PF): Arises
> from the challenging optical properties of materials. It includes Target Position Deviation
> and failures caused by transparent glassware or reflective fluid surfaces. (2) Grasping
> Failure (GF): Reflects end-effector control deficiencies, such as Object Slippage due to
> varying friction coefficients of wet surfaces or insufficient gripping force. (3) Motion
> Failure (MF): Corresponds to trajectory execution anomalies. A domain-specific highlight is
> Incomplete Trajectory, where premature termination of motion sequences leads to experimental
> failure. (4) Logic Failure (LF): Captures semantic planning errors (e.g., Step Omission,
> Sequence Reversal) that invalidate experimental outcomes. (5) Safety Failure (SF): This
> category covers Improper Handling and Protocol Violations (e.g., hazardous mixtures). Unlike
> reversible household failures, these pose risks of catastrophic damage or injury in chemical
> settings."

The annotation definitions, from Appendix A, Table 8 (Q5, Failure Classification):

| Option | Definition |
|---|---|
| (1) Perception Failure | "Failed to locate target objects or positions" |
| (2) Grasping Failure | "Object slippage or unstable grasp" |
| (3) Motion Failure | "Motion execution incomplete" |
| (4) Logic Failure | "Incorrect order or omitted steps" |
| (5) Safety Failure | "Violating laboratory safety protocols" |

### 10.2 Eleven subtypes

From Appendix B:

> "The 11 failure types include: (1) Protocol Violation and Improper Handling under Safety;
> (2) Sequence Reversal and Step Omission under Logic; (3) Pose Control Error and Incomplete
> Trajectory under Motion; (4) Gripper Control Failure and Object Slippage under Grasping; and
> (5) Target Positioning Deviation, Operation Position Error, and Grasp Target Misalignment
> under Perception."

The main text calls one of these "Target Position Deviation". Fig. 3(b) and Appendix B both say
"Target Positioning Deviation", and that is the name we use. Each row below gives the paper's
own example from Appendix B, then the rule we apply to this cell.

| Category | Subtype | Paper's example (verbatim, App. B) | Our coding rule for this cell |
|---|---|---|---|
| Safety | Protocol Violation | "A Protocol Violation occurs during the insertion phase, where an angular misalignment prevents the glass rod from being correctly inserted into the beaker, resulting in insufficient stirring that violates laboratory operation protocols." | The arm breaks a cell rule. Examples: entering the CubXL's keep-out while the gantry isn't parked, moving while the workspace isn't clear, exceeding the speed limit, or any step against the SOP (#22) |
| Safety | Improper Handling | "An Improper Handling event occurs during the returning phase, wherein the flask fails to be placed back at its designated original position, violating the chemical laboratory requirement for proper equipment placement after use, thereby leading to an abnormal task outcome." | The object ends up somewhere other than its destination: the wrong nest, the wrong pocket, or left on the deck |
| Logic | Sequence Reversal | "A Sequence Reversal event occurs at the beginning of the task, where the robotic arm executes a stirring motion without the glass rod prior to grasping it, leading to an incorrect task execution." | The harness runs steps out of order. Examples: descending to place before anything is picked, or loading into an occupied nest |
| Logic | Step Omission | "Step Omission occurs during the initial phase of the task when the robotic arm proceeded directly to stirring without gripping the glass rod." | The harness skips a step: no close, no open, no lift before travel, or no look under AT |
| Motion | Pose Control Error | "A Pose Control Error occurs during the beaker placement phase, where an abnormal twist in the robot arm’s pose leads to unsuccessful placement of the beaker at the target location, resulting in task failure." | The object reaches its destination tilted or twisted and doesn't seat, or the arm visibly leaves its planned path |
| Motion | Incomplete Trajectory | "An Incomplete Trajectory occurs during the approach phase: the arm stops prematurely and remains stationary in front of the button, causing task failure." | Motion stops before the transfer completes: a controller or CAN fault, a joint-limit or collision stop, a harness crash or the timeout |
| Grasping | Gripper Control Failure | "A Gripper Control Failure manifests during the grasping phase. Inadequate gripper closure aperture prevents successful object acquisition, leading to task failure." | The fingers are correctly placed but don't close, close too little, or miss the grip-effort threshold |
| Grasping | Object Slippage | "An Object Slippage event occurs during the transport phase, where insufficient gripper force causes the beaker to slip and fall, resulting in task failure." | After a good grasp, the object, or a vial it carries, moves in the fingers or falls during the lift, transport or descent |
| Perception | Target Positioning Deviation | "A Target Positioning Deviation occurs during the final phase of the task, where the beaker is not placed within the designated target region, resulting in an abnormal outcome." | The object is at the right destination but not seated: resting on the lead-in, on a cone-pin tip or on the pocket rim. Expected to be the most common open-loop failure |
| Perception | Operation Position Error | "An Operation Position Error occurs when the gripper moves to the front of the door handle, where misalignment between the gripper and the handle position causes the door-opening operation to fail." | The grasp happens but off-centre, and the transfer fails because of it. Example: the finger rib misses the post's groove and the carrier hangs tilted |
| Perception | Grasp Target Misalignment | "A Grasp Target Misalignment manifests during the grasping phase: the estimated target position deviates from the actual object position, so the gripper closes beside the object and fails to acquire it, leading to task failure." | The fingers close beside the object, or strike it on the way down, and nothing is picked |

### 10.3 Coding rules (ours)

- **Code what was seen, not the presumed cause.** The category names imply causes ("Perception")
  that an open-loop arm doesn't have. We follow the paper's definitions of the observed event,
  and record the suspected root cause in a separate free-text field.
- **One primary subtype per failure:** the first thing that went wrong in time. Secondary
  subtypes are optional.
- **When nothing fits,** code `Other (<category>)` with a description. Example: under AT, the
  tag can't be detected, which is `Other (Perception)`. If more than 10 % of failures are
  `Other`, that gap in the taxonomy's coverage is reported as a finding.
- **Two coders,** the operator and the reviewer from §6, code every failure. κ is reported.

### 10.4 Four severities

The paper names its severity levels two different ways, and never maps one onto the other.

The main text, under *LabRobFail-Bench → L3*:

> "Q4 assigns failures to four severity levels: Minor, Recoverable, Critical, and
> Catastrophic."

The annotation options, from Appendix A, Table 8 (Q4, Severity Assessment). These are the
labels the released data actually carries:

| Option | Definition |
|---|---|
| (1) Risk Level | "Collision, liquid spillage, or potential falling" |
| (2) Dangerous Level | "Requires manual intervention to proceed" |
| (3) Fatal Level | "Equipment damage, requiring manual intervention" |
| (4) Management Incident | "Non-compliant operations (e.g., unclosed cabinet)" |

**We log the main-text names.** They are ordinal, which suits a reliability log. The
operational definitions are ours, because the paper gives none:

| Severity | Definition for this cell (ours) | What happens |
|---|---|---|
| Minor | The transfer failed its criteria, but the cell could carry on untouched. Example: it finished but ran past the timeout | Log it and continue |
| Recoverable | A person has to restore the scene, but nothing is damaged and nothing needs changing. Examples: re-seating a carrier, picking up a dropped printed vial, re-homing | An intervention. Restore, log, continue |
| Critical | The cell can't continue in its current configuration. Examples: something needs repair, adjustment, re-teaching or recalibration; a fault needs diagnosis; glass broke outside the CubXL | Stop the block (§9, rule 2) |
| Catastrophic | Damage to the CubXL or the arm, or a person at risk. Examples: an injury or near miss, glass or sample spilled inside the CubXL, a collision with the gantry | E-stop, make safe, stop the campaign until reviewed with the safety officer (#22) |

For comparison with LabRobFail-Data, the reviewer also assigns each failure a Table 8 option.
That is a second field, filled in at review and never by the operator.

---

## 11. Data recorded

- **Per block:**
  - block ID, configuration ID, commit and hardware record;
  - seed and schedule file;
  - operator, start and end times;
  - temperature, relative humidity and illuminance.
- **Per transfer:**
  - unit ID, task, condition and leg (load or unload);
  - offset axis and value;
  - start, look, release and check timestamps;
  - under AT, the tag detections and the correction applied;
  - success, and which criterion failed if any;
  - LabRobFail category, subtype and severity;
  - whether there was an intervention, with a one-line description;
  - near-miss flags;
  - the witness still.
- **Streams:** joints, efforts and gripper at 100 Hz; wrist frames at the look pose; witness
  video.
- **Storage.** Raw logs go to `F26`. Schedules, configuration records and the block log are
  committed to this repo.

---

## 12. Analysis plan

The analysis scripts come in a later ping. They must implement this section. Before the first
counted trial, they are run on synthetic data with known *p*, ED90 and RP to show they recover
those values.

### 12.1 Success rates

For each cell, report *k*/*n* with two intervals:
- the **Wilson** 95 % interval;
- the **exact (Clopper–Pearson) one-sided 95 % lower bound**. When *k* = *n* this is
  0.05^(1/*n*).

What *n* = 300 buys:

| Failures in 300 | Point estimate | Wilson 95 % | Exact one-sided 95 % lower bound |
|---|---|---|---|
| 0 | 100 % | 98.74–100 % | **99.01 %** |
| 1 | 99.67 % | 98.14–99.94 % | 98.43 % |
| 2 | 99.33 % | 97.60–99.82 % | 97.92 % |
| 3 | 99.00 % | 97.10–99.66 % | 97.44 % |

How many transfers are needed to certify 99 %: 299 with no failures, 473 with one, 628 with
two. Certifying 99.9 % takes 2,995 with no failures.

### 12.2 Comparisons between conditions

- **Difference in proportions,** AT − OL, with **Newcombe's** hybrid-score 95 % interval,
  which is built from the two Wilson intervals.
- **H3a** uses a one-sided **Boschloo** exact test.
- **Gap closed, *G*,** gets a percentile bootstrap 95 % interval from 10,000 resamples. It is
  not reported when *p*(OL) ≥ 0.99.
- **Sensitivity check:** a logistic regression with a random intercept per block, plus time
  since power-on and temperature as covariates.

### 12.3 Capture envelope (ED50 and ED90)

- **Model.** For each task × condition × axis (x, y, yaw), fit **logistic regression** of
  success on offset magnitude |*d*|. Both signs are pooled and the zero level is included.
  The fit uses **Firth's** bias-reduced likelihood, so complete separation, such as all
  successes up to 3 mm and all failures at 4 mm, still gives finite estimates.
- **Estimate.** ED_q = (logit *q* − β₀) / β₁, for *q* = 0.5 and 0.9.
- **Intervals.** **Fieller** 95 % intervals. As a check, a percentile bootstrap that resamples
  trials within each level, 10,000 times.
- **Capture radius:** min(ED90ₓ, ED90ᵧ).
- **Secondary.** Separate slopes for + and − offsets, to show asymmetry. A probit link as a
  sensitivity check.
- **Censoring.** If a curve has no failures at its largest offset, its ED is reported as
  "> 4 mm" or "> 4°", together with the exact lower bound at that level. It is never
  extrapolated.
- **Consistency check.** The zero-offset level of E2 is compared against E1.

### 12.4 MTBI (Kaplan–Meier)

- **Intervention.** Any unscheduled human action needed to keep the cell running: touching the
  arm, an object or a fixture; an E-stop; restarting software; re-homing. Each one is
  attributed to the task × condition whose failure caused it.
- **Clock.** Each task × condition counts its own transfers. Interventions caused by another
  cell don't reset it. Interventions that can't be attributed (operator pauses) count for every
  cell.
  - An interval starts at the start of a block or right after an intervention.
  - It ends at the next intervention, which is an event, or at the end of the block, where it
    is censored.
  - The primary analysis uses E1 only. E2 provokes failures on purpose, so its interventions
    are reported separately.
  - A secondary analysis counts operating hours instead of transfers.
- **Estimator.** A **Kaplan–Meier** curve of transfers between interventions.
  - **MTBI** is the restricted mean up to τ = `F25` transfers, with a Greenwood-based 95 %
    interval. The plain KM mean is undefined when the longest interval is censored.
  - **Cross-check:** total transfers ÷ interventions, with an exact Poisson (Garwood)
    interval.
  - Also report **S(50)**, the chance of 50 transfers without an intervention, to set against
    the Ada figure in §1.
- **Assumption.** Each restore leaves the cell as good as before (a renewal process). This is
  checked by plotting the hazard against transfers since the block start.
- **Secondary analyses.** Cumulative incidence for each LabRobFail category
  (Aalen–Johansen). A log-rank test of OL against AT.

### 12.5 Metrology (RP)

For each pose and payload, using the *n* = 30 attained positions (*x_j*, *y_j*, *z_j*) and their
barycentre (x̄, ȳ, z̄), as ISO 9283 defines it:

$$l_j=\sqrt{(x_j-\bar x)^2+(y_j-\bar y)^2+(z_j-\bar z)^2},\quad \bar l=\frac1n\sum_j l_j,\quad S_l=\sqrt{\frac{\sum_j (l_j-\bar l)^2}{n-1}},\quad RP=\bar l+3S_l$$

- **Intervals.** RP gets a bootstrap 95 % interval, resampling the 30 cycles 10,000 times, and
  is reported next to the instrument's *U*. H4b and H4c follow the rules in §2.
- **Drift.** Position is regressed on cycle number. If the barycentre drifts during a run, that
  is reported. ISO 9283 tests drift separately, from a cold start.

### 12.6 What gets reported whatever happens

All cells and every hypothesis, each as supported, not supported or inconclusive. Every block,
including those from superseded configurations. All exclusions and all amendments.

---

## 13. Known threats and optional extensions

These are **not in the budget.** Each extension must be added by amendment *before* its first
trial.

| Threat | Effect | Optional extension |
|---|---|---|
| **The object confounds the dock contrast.** A carrier vs a vial differs in mass, grasp and fixture at once | Estimand (i) in §1 overstates or understates what the lead-in itself buys | T2 into a chamfered pocket vs the tight one: same vial, OL, *n* = 300. This isolates the lead-in |
| **The yaw levels saturate for the OL carrier** (§7) | The yaw ED90 is censored below 2° | Add ±0.5° and ±1°, 20 trials each |
| **AT may never fail within ±4 mm** | ED90_AT is censored at > 4 mm | If AT has no failures at ±4 mm on an axis, run ±6 and ±8 mm, 20 trials each, AT only |
| **A software offset may not equal a physical one** | E2 may misstate real capture | 20 OL carrier trials with the dock shifted +2 mm on a shim, vs the software offset |
| **Dummies are not glass** | Slip and breakage are not represented | A confirmation block with glass vials on the real CubXL (`F1`), reported separately |
| **The operator knows the condition** | Scoring bias | Blind review of the witness stills (§6) |
| **Printed parts wear** over about 5,800 transfers | Reliability drifts | Inspect at block boundaries. A worn part that gets replaced means a new block |

---

## 14. Amendments

| Date | Section | Change | Reason | Trials run before it |
|---|---|---|---|---|
| | | | | |

---

## References

- Wang, H. et al. (2026). LabRobFail: A Benchmark for Robotic Failure Analysis in Chemical
  Self-driving Laboratory. arXiv:2607.23704v2.
- ISO 9283:1998. *Manipulating industrial robots: performance criteria and related test
  methods.* §6.2 (warm-up), §6.5 (instrumentation and the 25 % uncertainty cap), §6.6 (load),
  §6.7 (velocities), §6.8 (test poses).
- Kuric, I. et al. (2018). Measurement of industrial robot pose repeatability. *MATEC Web of
  Conferences* 244, 01015. doi:10.1051/matecconf/201824401015. The ISO cube, the five-pose
  plane and the one-way approach.
- Wilson, E. B. (1927). Probable inference, the law of succession, and statistical inference.
  *JASA* 22, 209–212.
- Clopper, C. J. and Pearson, E. S. (1934). The use of confidence or fiducial limits
  illustrated in the case of the binomial. *Biometrika* 26, 404–413.
- Newcombe, R. G. (1998). Interval estimation for the difference between independent
  proportions: comparison of eleven methods. *Statistics in Medicine* 17, 873–890.
- Boschloo, R. D. (1970). Raised conditional level of significance for the 2 × 2-table when
  testing the equality of two probabilities. *Statistica Neerlandica* 24.
- Firth, D. (1993). Bias reduction of maximum likelihood estimates. *Biometrika* 80, 27–38.
- Fieller, E. C. (1954). Some problems in interval estimation. *JRSS B* 16, 175–185.
- Kaplan, E. L. and Meier, P. (1958). Nonparametric estimation from incomplete observations.
  *JASA* 53, 457–481.
- Royston, P. and Parmar, M. K. B. (2013). Restricted mean survival time: an alternative to
  the hazard ratio. *BMC Medical Research Methodology* 13, 152.
- Garwood, F. (1936). Fiducial limits for the Poisson distribution. *Biometrika* 28, 437–442.
- Aalen, O. O. and Johansen, S. (1978). An empirical transition matrix for non-homogeneous
  Markov chains based on censored observations. *Scandinavian Journal of Statistics* 5,
  141–150.
- Olson, E. (2011). AprilTag: a robust and flexible visual fiducial system. *ICRA*, 3400–3407.
- [byu-vcl#266](https://github.com/vertical-cloud-lab/byu-vcl/issues/266): the dock, carrier,
  error budget and capture ranges. #1: the Ada figure and the earlier reliability-statistics
  scan.

---

## Appendix A. Checklist for the person at the arm

*Print this page. One per session.* Block ID `______` · cfg `______` · Operator `______` ·
Date `______`

**Before the first unit**
- [ ] The SOP (#22) is read and signed. The **E-stop (#18) is installed, in reach, and tested
      today.** No E-stop, no session.
- [ ] The "workspace clear" sign is up and nobody else is within reach of the arm. The dome
      has no interlock, so watch it.
- [ ] On the real CubXL: the gantry is parked and CubOS is holding it.
- [ ] The commit on the Pi matches the block's schedule file, and **nothing has changed since
      the last block.** If something has, stop and record a new configuration.
- [ ] Temperature, RH and lux are logged. The witness camera is recording.
- [ ] The cell is at its start state: carrier A in the dock, B in shelf nest 2, the vial in the
      shelf pocket, the dock pocket empty.
- [ ] This block's schedule is generated and committed. Run it in order.

**Every unit**
- [ ] Hands out of the workspace before you press go.
- [ ] Don't touch anything during a transfer unless you're stopping it for safety. A stop is
      an intervention and a failure.
- [ ] At each check, score the leg against the success card (§6). On a failure, record the
      category, subtype, severity and one line on what you saw.

**After a failure**

| Severity | What to do |
|---|---|
| Minor | Log it and continue |
| Recoverable | Log the intervention. Restore the scene exactly as the reset card says, adjust nothing, and continue |
| Critical | **Stop the block.** Make it safe and log it. Anything you fix makes a new configuration |
| Catastrophic | **E-stop.** Make safe per the SOP, stop the campaign, and call `F27` before doing anything else |

- [ ] 3 failures in a row, or 5 in the last 20 (`F23`): stop the block and inspect.

**Never**
- Adjust, tighten, re-teach, recalibrate, clean the lens or swap a part in the middle of a
  block. End the block first.
- Skip, reorder or rerun a unit. The one exception is an *interrupted* unit, which goes to the
  end of the schedule.
- Stop or carry on because of how the numbers look.

**End of session**
- [ ] Stop between units. Park the arm, using the softer park from #20.
- [ ] Upload the logs (`F26`), write anything odd in the block log, and push.
