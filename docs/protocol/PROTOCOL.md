# Pre-registration: how reliably can the PiPER load a CubXL deck with vial carriers and single vials?

**Status: v2 draft, not locked.** No counted trial may run until this file is locked and registered.
To lock it, make every decision in [§0](#0-decisions-before-locking), commit, tag the commit
`prereg-v1`, and register it as described in [`README.md`](README.md#how-to-register-once-the-before-registration-gates-are-met).
Changes made after the lock go in [§16](#16-amendments), dated and with a reason. Never rewrite the
original text.

| | |
|---|---|
| Version | v2, 2026-11-27. It replaces v1 of 2026-10-10 (`9652c43`, never registered). What changed is listed in [§16](#16-amendments) |
| Locked commit / tag | `____` / `prereg-v1` |
| Registry | [OSF Registries](https://osf.io/registries), *OSF Preregistration* template (v4). **A**: E1 and E2, H1–H3 ([form answers](osf/A-transfer-reliability.md)). **B**: E3, H4 ([form answers](osf/B-pose-repeatability.md)) |
| Registration DOIs | A: `____` · B: `____` |
| Campaign issue | [#21](https://github.com/vertical-cloud-lab/robot-arms/issues/21) |
| Arm | AgileX PiPER, 6-DOF, on loan to the lab. Vendor figures: 1.5 kg payload, 626 mm reach (reseller listing), 0.1 mm repeatability. None has been measured here; E3 measures the last |
| Design under test | The dock blocks (3 mm × 45° lead-in, cone pins 250 mm apart), the 8 + 1 carrier, the finger inserts and the offset plates of [byu-vcl#266](https://github.com/vertical-cloud-lab/byu-vcl/issues/266) and [byu-vcl PR 272](https://github.com/vertical-cloud-lab/byu-vcl/pull/272) |
| Safety documents | [PR 23](https://github.com/vertical-cloud-lab/robot-arms/pull/23) (`docs/safety/`: hazard analysis, SOP, checklist). Still a draft; it must be reviewed before the first counted block ([`bench-readiness.md`](bench-readiness.md)) |
| Analysis code | [`analysis/prereg_stats.py`](analysis/prereg_stats.py) implements every confirmatory rule below; [`analysis/simulate_and_check.py`](analysis/simulate_and_check.py) runs it on a synthetic campaign |

This is the plan for the PiPER reliability paper. Before any counted trial, it fixes what we
measure, how each hypothesis is decided, and when we stop. Later pieces of the campaign must do
what this file says: the trial harness, the repeatability fixture and the fiducial correction.
Where one can't, amend this file first. Nothing in this document moves the arm.

---

## 0. Decisions before locking

Two kinds of blank remain. **Decisions** (D) are for the PI to make before registering.
**Rules** (R) are already fixed here; the *values* they produce are measured in the pilot and
written into the `cfg-1` record before the first counted trial, so registration doesn't wait for
them.

### Decisions for the PI

| ID | Decision | Where | Suggestion |
|---|---|---|---|
| D1 | Setting: the mock-up v2 deck (real deck's 25 mm pitch, PR 272) or the real CubXL | §4 | Mock-up v2. No CubXL is in or near the cell, and the v1 mock-up's 35.6 mm pitch doesn't match the real 25 mm |
| D2 | Vials: printed dummies or glass; which height | §4 | Printed dummies of Chris's vial (64.2 mm, Ø27 body, Ø28 cap), solid (46.8 g). PR 272 notes the CubOS deck files say 83 mm; settle which before printing |
| D3 | Carrier load | §4 | Both carriers full: 8 dummies each, 485 g per carrier with solid dummies (PR 272) |
| D4 | How E2's offsets are made: in software (the arm's belief about the dock) or with PR 272's offset plates | §8 | Software, with the plates as a physical cross-check (§15). Plates need a person to swap them, which rules out randomizing levels within a block |
| D5 | *n* for the carrier, open-loop cell of E1 | §8 | **628** (2 failures may still certify 99 %), if the arm time is there. 300 is the minimum #21 sets, and gives H1a 55 % power at a true 99.8 % |
| D6 | Single-vial open-loop levels in E2: all 21, or only 0, ±1, ±2 mm and ±2° | §8 | All 21, as #21 asks, unless operator time is short. The trimmed set saves about 200 resets for almost no information (§8) |
| D7 | Predictions for H1–H4 (blanks P1–P8 in §2) | §2 | Yours. They're recorded for calibration only and enter no decision |
| D8 | The time-cost cap for H3c, in seconds per loading transfer | §2 | 5 s |
| D9 | E3's loaded payload | §8 | A dummy mass equal to a full carrier, at the carrier's centre of gravity |
| D10 | E3's instrument, with its expanded uncertainty *U* (k = 2) | §8 | Three 0.001 mm digital indicators on a sphere or cube target. *U* must be ≤ 0.025 mm |
| D11 | Run-of-failures stop | §10 | 3 in a row in one cell, or 5 in the last 20 units of one cell |
| D12 | Campaign end date (cells still short then are reported as they stand) | §10 | 16 weeks after the first counted block |
| D13 | MTBI horizon τ in transfers | §14.4 | 300 |
| D14 | Where raw logs and videos live | §11 | A Hugging Face dataset under `byu-vcl`, made public with the paper |
| D15 | People: the operators, the blind reviewer of failures, the adjudicator, and who is called after a Catastrophic event | §7, App. A | The reviewer must not have operated the blocks they review. Call the PI and the College Health & Safety Officer |
| D16 | Registration contributors, and public or embargoed | README | Public at registration |

### Rules whose values come from the pilot

Each value goes into the `cfg-1` record, with its measurement, before the first counted trial.
If a rule can't be met (for example the pocket's clearance is over 1 mm), stop and amend before
counting anything.

| ID | What | Rule |
|---|---|---|
| R1 | T2's pocket: diametral clearance *c* and entry chamfer | Measured on the printed part with pin gauges and calipers, not taken from CAD. H1b needs *c* ≤ 1.0 mm; PR 272's Cubware pocket squeezes the vial by 0.57 mm, which qualifies |
| R2 | Dock datum, cone-pin spacing, pocket distance *r* from the datum | Measured as printed. The datum is the midpoint of the cone pins; the design spacing is 250 mm |
| R3 | AprilTags and the look | `tag36h11`, the largest size with a full white border that fits on the dock blocks, and at least 25 mm (10 mm tags failed 0 of 48 from the fixed camera in PR 40). 5 frames per look, 3 looks at most. The correction is capped at 6 mm and 6°, beyond the largest injected offset. The reprojection-error limit is the 99th percentile of 100 pilot looks |
| R4 | Seat check (T1) and cap height (T2) | A 0.2 mm feeler gauge at the four corners of each dock block, or a seat switch if one is fitted. Cap-top height within ±0.5 mm of nominal, by gauge |
| R5 | Speed | One speed in every condition and experiment: the pilot speed at which 20 nominal carrier loads all succeed, and never above the SOP's cap |
| R6 | Check delay; timeout | Check 2 s after the arm reaches its clear pose. Timeout per transfer: 3 × the pilot median, rounded up to 5 s |
| R7 | Units per block | Whole sub-blocks that fit in 50 minutes at the pilot's median unit time. A person can end a session sooner, between units |
| R8 | Contact stop on the place descent | The descent stops and the transfer aborts when any joint effort exceeds 1.5 × the largest effort in 20 nominal pilot places. It must stop a ±4 mm carrier place on a cone-pin tip before anything breaks, tested in the pilot at the campaign speed |

---

## 1. Question, estimands and scope

**Question.** How reliable is this arm at loading a CubXL deck with vial carriers and with single
vials? And how much of the gap to 99 % per transfer does each of these close: (a) a lead-in dock,
and (b) wrist-camera AprilTag correction?

**Why 99 %.** A self-driving-lab run is a chain of transfers. The chance that 50 transfers
finish untouched is *p*⁵⁰:

| Per-transfer success | 97.5 % | 99 % | 99.5 % | 99.9 % |
|---|---|---|---|---|
| 50 transfers with no intervention | 28 % | 61 % | 78 % | 95 % |

97.5 % is the rate Ada reports (about one run-ending failure per 40 samples, from the Q1 scan
in #1). 99 % is roughly where an overnight run becomes more likely than not to finish.

**Why these two interventions.** #266 estimates the arm's placement error at ±0.64 mm combined
(RSS) and ±1.15 mm worst case. That is an estimate from parts of a budget, not a measurement: the
linear sum of ±0.10 mm repeatability, ±0.50 mm gripper, ±0.30 mm teaching and registration, and
±0.25 mm structure and humidity. A tight pocket captures about ±0.6 mm, and a 3 mm × 45° lead-in
nest about ±3 mm (PR 272). So the two fixes attack the problem from opposite sides:

- **The dock widens capture.**
- **The correction shrinks error.** It measures where the dock really is, which removes the
  teaching, registration and structure terms. It can't see the vial's position in the fingers,
  so the ±0.5 mm gripper term stays. Once corrected, the worst case is about ±0.6 mm plus the
  tag-pose error, against ±0.5 mm in a pocket with 1 mm diametral clearance. So correction should
  help single vials without guaranteeing 99 %. This is an expectation, not a hypothesis.

**Estimands.** *T* is the task (C = carrier, V = single vial). *K* is the condition (OL = open
loop, AT = AprilTag-corrected).

- *p*(*T*, *K*): the probability that a loading transfer succeeds at zero injected offset. The
  primary endpoint.
- Gap to 99 %: *g*(*T*, *K*) = max(0, 0.99 − *p*(*T*, *K*)).
- Share of the gap closed by correction: *G*(*T*) = [*p*(*T*, AT) − *p*(*T*, OL)] /
  [0.99 − *p*(*T*, OL)], defined only when *p*(*T*, OL) < 0.99.
- Contribution of the lead-in dock, two ways:
  - (i) the task contrast *p*(C, OL) − *p*(V, OL), which the object confounds (§15);
  - (ii) the mechanism: the dock's ED90 capture radius against the arm's error budget (H2).
- ED50 and ED90: the injected offset at which predicted success falls to 50 % or 90 %.
- MTBI: the mean number of transfers between interventions.
- RP: pose repeatability as ISO 9283 defines it.

**Scope.** The claims are about this arm, this dock design and these objects, at spot D:

- **The deck is a mock-up** unless D1 says otherwise. Nobody has put a real CubXL in the cell.
- **The vials are printed dummies** unless D2 says otherwise. A dummy doesn't slip, chip or
  shatter like glass.
- **The arm is the borrowed PiPER** with its firmware as recorded in each configuration.
- **The CubXL's own motion is out of scope**, and so is anything a vial would hold.

---

## 2. Hypotheses and decision rules

Each hypothesis gets its own α = 0.05, one-sided where stated. There is no correction across
hypotheses, because each answers a separate question fixed here in advance; within a hypothesis,
"both axes" is an intersection–union test, which needs none. Every outcome is reported as
**supported**, **refuted** or **inconclusive**, whatever it is. The predictions (P1–P8) are
recorded for calibration only and enter no decision. The power of each rule is in [§8.4](#84-power).

### H1: the dock reaches 99 %, the tight pocket does not

- **H1a.** Open-loop carriers loaded into the 3 mm lead-in dock succeed at 99 % or better.
  - Prediction: *p*(C, OL) = `P1: ____ %`.
  - **Supported** if the exact (Clopper–Pearson) one-sided 95 % lower bound is ≥ 0.99. At
    *n* = 300 that allows no failures (0/300 gives 0.9901, 1/300 gives 0.9843). At *n* = 628
    it allows two.
  - **Refuted** if the exact one-sided 95 % upper bound is < 0.99: at least 7 failures at
    *n* = 300, or 12 at *n* = 628.
  - **Inconclusive** otherwise. The cell is never extended to resolve it (§10, rule 4).
- **H1b.** Open-loop single vials loaded into a pocket with ≤ 1 mm diametral clearance (R1)
  stay below 99 %.
  - Prediction: *p*(V, OL) = `P2: ____ %`.
  - **Supported** if the exact one-sided 95 % upper bound is < 0.99 (at *n* = 300, at least 7
    failures). **Refuted** if the exact one-sided 95 % lower bound is ≥ 0.99 (no failures).
    **Inconclusive** otherwise.

### H2: the dock's capture radius exceeds the arm's worst-case error

- **Claim.** For open-loop carriers, ED90 is larger than the ±1.15 mm worst-case arm error from
  #266, on both x and y. The capture radius is min(ED90ₓ, ED90ᵧ).
- **Prediction.** ED90ₓ = `P3: ____ mm`, ED90ᵧ = `____ mm`, ED90 for yaw = `____°`.
- **Decision, per axis** (x and y; yaw is reported but not tested):
  - If the capture curve is **not censored**: the Fieller one-sided 95 % lower bound of ED90 must
    exceed 1.15 mm.
  - If it **is censored**, the logistic fit can't place ED90. Censored means no failures at 4 mm,
    or a fitted success at 4 mm that is still ≥ 90 % (§14.3). Then monotonicity decides instead:
    success at 1.15 mm is at least the average success over the 2, 3 and 4 mm levels, so the
    exact one-sided 95 % lower bound of the pooled success at |*d*| ≥ 2 mm (120 trials) must be
    ≥ 0.90.
- **Supported** if both axes pass. **Refuted** if on either axis the Fieller one-sided 95 %
  upper bound of ED90 is below 1.15 mm. **Inconclusive** otherwise.
- **What the offset means.** It is injected on top of the arm's own error. "ED90 > 1.15 mm"
  therefore means the dock still catches 90 % of carriers after the arm has been pushed a further
  1.15 mm off.
- **Secondary check (reported, not decisive).** Whether the four ±2 mm translation levels
  together (80 trials) have an exact one-sided 95 % lower bound of at least 0.90, which allows 3
  failures. v1 made this part of the decision. The power analysis showed that the combination
  tests "ED90 > about 2.5 mm", not "> 1.15 mm": at a true ED90 of 2 mm the combined rule passes
  4 % of the time, the Fieller rule alone 100 % ([`out/power.md`](analysis/out/power.md)).

### H3: correction raises single-vial success and widens ED90, at a cost of a few seconds

- **H3a.** *p*(V, AT) > *p*(V, OL).
  - Prediction: OL `P4: ____ %`, AT `____ %`.
  - **Supported** if the one-sided Boschloo exact test gives *p* < 0.05. **Contrary** if the
    same test in the other direction gives *p* < 0.05. **Not supported** otherwise.
- **H3b.** For single vials, correction widens ED90 on both x and y.
  - Prediction: `P5: ____ mm` wider.
  - **Decision, per axis.** ED90 is floored at 0 first: a pocket that is below 90 % even at zero
    offset has a capture radius of 0.
    - If the AT curve is censored (§14.3), H3b holds on that axis when the Fieller one-sided
      95 % upper bound of ED90_OL is below 4 mm.
    - Otherwise the one-sided 95 % percentile-bootstrap lower bound of
      max(0, ED90_AT) − max(0, ED90_OL) must be > 0.
  - **Supported** if both axes pass, **not supported** otherwise.
- **H3c.** The correction costs no more than `D8` seconds per single-vial loading transfer.
  - Prediction: `P6: ____ s`.
  - **Supported** if the one-sided 95 % upper bound of the Hodges–Lehmann shift in transfer time
    (AT − OL, successful E1 loads only) is ≤ D8.
- **Also reported, not tested.** The same three contrasts for carriers.

### H4: ISO 9283 RP is within ±0.1 mm unloaded and grows with payload and reach (registration B)

- **H4a.** Unloaded RP ≤ 0.10 mm at all five poses.
  - **Supported** ("meets the spec") if the ISO 9283 point estimate is ≤ 0.10 mm at every pose.
    This is how manufacturers report RP. It is also reported as **certified** if the one-sided
    95 % bootstrap-t upper bound (§14.5) is ≤ 0.10 mm at every pose.
  - **Refuted** if the one-sided 95 % bootstrap-t lower bound exceeds 0.10 mm at any pose.
  - **Inconclusive** if the instrument's expanded uncertainty is above 0.025 mm (D10). ISO 9283
    §6.5 caps the total measurement uncertainty at 25 % of the characteristic under test.
- **H4b.** RP grows with payload.
  - Prediction: `P7: +____ mm` loaded vs unloaded.
  - **Supported** if the mean over poses of RP(loaded) − RP(unloaded) has a one-sided 95 %
    bootstrap lower bound > 0.
- **H4c.** RP grows with reach (the horizontal distance from the J1 axis to the TCP).
  - Prediction: `P8: +____ mm per 100 mm`.
  - **Supported** if, regressing RP on reach over 5 poses × 2 payloads with payload as a
    covariate, the slope's one-sided 95 % bootstrap lower bound is > 0.

---

## 3. Outcomes

**Primary outcome.** Success or failure of each *loading* transfer in E1, scored as in §7, per
task × condition.

**Secondary outcomes.**
- Success of each *unloading* transfer in E1.
- Success of each loading transfer in E2, against the injected offset (for ED50 and ED90).
- Transfer time: from the start of the pick approach to the arm reaching its clear pose after the
  release.
- Interventions, for MTBI and S(50).
- The LabRobFail category, subtype and severity of each failure (§13).
- ISO 9283 RP per pose and payload (E3, registration B).

**Exploratory, not tested.** Joint efforts and positions over time, the correction applied under
AT and its residual, tag-detection quality, temperature and humidity effects, drift within a
block, and anything else in the logs.

---

## 4. Set-up (the configuration)

Everything below is part of the **configuration** (§9). Changing any of it starts a new block,
and most changes start a new configuration.

| Item | Specification |
|---|---|
| Arm | AgileX PiPER at spot D, upright on the 48 × 48 in plywood top. Serial, firmware (S-V1.8-1 when last read), joint zero offsets (J1 was re-zeroed on 2026-11-14) and how the base is fixed are recorded per configuration |
| Controller | Driven over CAN (`can0`, 1 Mbit/s) from the Raspberry Pi 5 `rpi-5-mpzy`, which also switches the arm's supply through an IoT Relay II (`arm_power.py`). The POWERTEC 71970 E-stop is in the same supply. The order of relay and E-stop is recorded |
| Gripper | AgileX's gripper with PR 272's finger inserts (90° V-blocks with a rib) and 1.5 mm silicone pads, Shore 30–50A. The printed auger sleeves now on the gripper come off for the campaign. Motor 7 (the gripper) must home and enable with the inserts fitted |
| Wrist camera | The wrist Raspberry Pi (`rpi-5-76zj`) with the HQ camera (6 mm lens, focused and locked) and Camera Module 3 Wide, on PR 10's mount. Mounted and powered in **both** conditions, so the mass and cable drag are the same. Intrinsics and hand–eye calibration are part of the configuration |
| Dock | PR 272's two dock blocks on `plate_0`, bolted through to a deck strip with the real deck's 25 mm pitch, and the dock's single-vial pocket (R1, R2). AprilTags on the blocks (R3) |
| Carriers | Two identical PR 272 carriers, A and B, with the handle post at slot 5. Load and mass: D3. Each is weighed |
| Vials | D2. Each is numbered and weighed |
| Shelf | At spot D, two carrier nests and one single-vial pocket, each with a generous chamfer so the shelf is never the bottleneck. Geometry recorded. The shelf pocket and nests must be reachable with J1 inside the window that keeps the arm clear of the A1 mini (−20° to +60° in PR 83) |
| Layout | Each carrier points at J1 at the place (PR 272 found no IK solution for a carrier across the arm's line). Joint margins at every taught pose are recorded |
| Witness camera | Fixed, looking at the dock. The front camera on `rpi-5-mpzy` if its view covers the dock, otherwise a dedicated one. It takes a still at every check (R4) |
| Speed | R5 |
| Software | The trial harness commit is recorded per block. It logs joint positions, efforts and gripper state at ≥ 50 Hz (`Up_and_Down.py --trace` on main runs at 50 Hz; PR 20's runs at 100 Hz) |
| Environment | Temperature, relative humidity and illuminance at the dock, logged per block |
| Setting | D1 |

**Payload.** A full carrier (0.53–0.66 kg, PR 272) plus the finger inserts (67 g) rides on a
gripper of about 0.5 kg, and the wrist also carries a Pi, two cameras and their mount. #42 reads
the 1.5 kg rating as including the gripper. The masses are weighed and the total recorded before
the pilot (bench gate B6).

---

## 5. Tasks

Each task runs in **units**. Every unit holds exactly one *loading* transfer (into the dock: the
primary endpoint) and one *unloading* transfer (out of the dock: secondary). A unit leaves the
cell in a known state, so units of either task can be interleaved without anyone touching the
cell.

- **T1: carrier swap between the dock and the shelf.** Carrier A starts in the dock and B in shelf
  nest 2. Each unit swaps them:
  1. **Unload:** the carrier in the dock goes to the free shelf nest.
  2. **Load:** the other carrier goes from its shelf nest into the dock.

  The cell returns to its start state every two units.
- **T2: single vial between the shelf and the dock pocket.** One vial starts in the shelf pocket.
  Each unit:
  1. **Load:** shelf pocket → the dock's single-vial pocket (R1).
  2. **Unload:** dock pocket → shelf pocket.

A **transfer** is the pick at the source, the place at the destination, and the retreat to the
clear pose. If a leg fails, the person at the arm restores the cell to the state that leg should
have produced (App. A), and the unit goes on to its next leg, so every unit still has one load and
one unload. Before every unit the harness checks that the arm answers, has no driver fault, and
reads its rest pose to within 0.5° on every joint. If not, the unit doesn't start (§10, rule 3).

---

## 6. Conditions

- **OL: open loop.** Taught poses only. No camera data reaches the motion.
- **AT: AprilTag-corrected.**
  - At the look pose over the dock, the wrist camera grabs frames (R3), detects the dock's tags
    and estimates the dock's pose in the base frame through the hand–eye calibration.
  - The place pose is corrected in x, y and yaw before every dock-side place, and the pick pose
    the same way before every dock-side pick. z, roll and pitch stay as taught.
  - The shelf side is open loop in both conditions, because the question is about loading the
    deck.
  - If no valid pose arrives within the allowed looks, or the correction exceeds its cap (R3),
    the transfer aborts before descending. That counts as a failure. It never falls back to open
    loop, which would mix the conditions.

**Both conditions pass through the same look pose and stop there.** OL leaves at once. AT dwells
to capture and correct. The only differences between the conditions are the dwell and the
correction, so settling at a standstill can't pass for a benefit of vision.

**No automatic retries in either condition.** Each pick and each place is a single attempt. The
harness aborts a transfer it judges unsafe: a grip effort below threshold before the lift (#20),
or the contact stop on the place descent (R8). An abort counts as a failure.

---

## 7. Success and scoring

A transfer is scored at the **check**, 2 s after the arm reaches the clear pose (R6).

**Loading, T1: success requires all of these.**
1. The carrier is seated: both cone pins are engaged and it sits flat on the dock blocks (R4).
2. Every vial is still in its pocket, upright, with its cap on.
3. The gripper released cleanly, the arm reached the clear pose, and the carrier was not dragged
   out of its seat.
4. Nobody touched the cell between the start of the transfer and the check.
5. There was no fault: no controller or CAN error, no E-stop press, no contact stop (R8), and no
   contact with the enclosure.
6. The transfer finished within the timeout (R6).

**Loading, T2: success requires all of these.**
1. The vial sits fully in the pocket, with its cap-top height within ±0.5 mm of nominal (R4).
2. It is upright, capped and intact.
3. Criteria 3–6 from T1 hold.

**Unloading:** the same criteria, applied at the shelf.

**These still count as successes,** each flagged as a near miss:
- the lead-in doing its job, such as the carrier landing on the chamfer and sliding home before
  the check;
- an effort spike that didn't trip the contact stop.

**A planned E-stop is not a failure.** The SOP's lockout (§C of `docs/safety/sop.md`) has the
person at the arm press the E-stop before every reach-in. A press between units, with the arm
parked, belongs to the intervention that caused it. A press *during* a transfer fails that
transfer.

**Scoring.**
1. The operator scores every transfer on the spot (App. A).
2. A second person (D15) re-scores every failure and a random 10 % of successes from the witness
   stills. The stills are taken after the arm has left, so they don't show the condition.
3. A third person resolves any disagreement. The adjudicated score is the one analysed.
4. Cohen's κ between the operator and the reviewer is reported.

---

## 8. Experiments, sample size and power

### 8.1 E1: nominal reliability (registration A)

- 2 tasks × 2 conditions, at zero offset.
- **Loading transfers per cell:** 300 for C-AT, V-OL and V-AT, and D5 (300 or 628) for C-OL.
  Each is paired with an unloading transfer.
- With D5 = 300: 1,200 loads and 1,200 unloads. With D5 = 628: 1,528 of each.

### 8.2 E2: capture envelope (registration A)

- **What is offset** (D4 = software). The dock frame the arm *believes* in. The physical dock does
  not move.
- **The dock frame.** Its origin is the dock datum (R2). x runs along the carrier's long axis, z
  points up, and yaw is about z through the origin.
- **Levels,** one axis at a time:
  - 0;
  - x = ±1, ±2, ±3, ±4 mm;
  - y = ±1, ±2, ±3, ±4 mm;
  - yaw = ±2°, ±4°.

  That is **21 levels × 20 trials = 420 loading transfers per task × condition**, 1,680 in all.
  With D6 trimmed, single-vial OL runs 11 levels (220 trials) and E2 totals 1,480.
- **Which leg is offset.** Only the loading leg. The unloading leg runs at the nominal frame:
  after a successful load the object sits where the dock put it.
- **Under AT,** the look pose moves with the believed frame, and the correction has to find the
  real dock from the image. The injected offset never reaches the correction code.
- **For T2,** a yaw of the dock frame moves the pocket sideways by about *r*·θ (R2).

**The yaw levels will saturate for open-loop carriers.** With the pins 125 mm either side of the
datum, a yaw of θ moves each pin 125·sin θ: 4.4 mm at 2° and 8.7 mm at 4°, both past the 3 mm
lead-in, which covers about ±1.4° (PR 272). The OL carrier's yaw curve will have no informative
points. §15 lists an optional ±0.5° / ±1° extension.

**Expect many failed loads, and a reset for each.** Under one plausible scenario
([`out/power.md`](analysis/out/power.md)), E2 produces about 590 failed loads: about 180 for
carriers OL, about 400 for single vials OL, and about 12 for both AT cells together. Each needs a
person to park the arm, press the E-stop, restore the scene and restart (§C of the SOP). Trimming
single-vial OL to 0, ±1, ±2 mm and ±2° (D6) would cut its failures to about 200. Its ED90 is
expected below 1 mm, so the dropped levels carry almost no information.

### 8.3 E3: ISO 9283-style metrology (registration B)

- **Size.** 5 poses × 30 cycles × 2 payloads: 300 measured pose visits.
- **Poses.** P1–P5 lie on a diagonal plane of the largest cube that fits the volume the campaign
  uses, around the dock and the shelf. P1 is at the plane's centre and P2–P5 sit near its
  corners. Secondary sources put them 10 % ± 2 % of the diagonal in from the corners; check that,
  and the order of visits, against §6.8 of the standard before building the fixture.
- **Cycles.** Each cycle visits every pose in a fixed order, approaching each from the same
  direction, which keeps backlash out of RP. Dwell before measuring: 2 s after the arm reports
  arrival.
- **Payloads.** (1) Unloaded: the gripper, inserts and the measuring target. (2) Loaded: D9.
  ISO 9283 makes 100 % rated load mandatory and 10 % an optional extra, so E3 is ISO 9283-*style*,
  not conformant. Instrument parts carried by the arm count toward the payload (§6.6).
- **Speed.** R5, so RP describes the motion the trials use. A third run at 100 % override may be
  added by amendment.
- **Warm-up.** 15 minutes cycling over P1–P5 before the first measured cycle. ISO 9283 §6.2 asks
  for a warm-up if the manufacturer specifies one.
- **Instrument.** D10, with *U* ≤ 0.025 mm (k = 2), checked on a static target before E3.
- **Order.** Both payloads in one session, in random order, with temperature logged.

Only positional RP is measured. Orientation repeatability and pose accuracy (AP, which needs an
absolute reference such as a laser tracker) are out of scope.

### 8.4 Power

The full tables are in [`analysis/out/power.md`](analysis/out/power.md), from
[`analysis/power.py`](analysis/power.py) (fixed seeds, the registered rules from
`prereg_stats.py`). Binomial and Boschloo powers are exact. ED90, timing and RP powers are
simulated, 2,000 campaigns per scenario (1,000 for RP).

![Power for H1](analysis/out/fig_power_h1.png)

| Rule | What *n* buys |
|---|---|
| **H1a** (certify ≥ 99 %) | At *n* = 300 the cell must be perfect. Power: 22 % if the true rate is 99.5 %, 41 % at 99.7 %, **55 % at 99.8 %**, 74 % at 99.9 %. At *n* = 628 (D5): 39 %, 71 %, **87 %**, 97 %. 80 % power at 99.7 % would need 913 |
| **H1b** (show < 99 %) | At *n* = 300: 99 % power if the true rate is 95 %, 80 % at 97 %, 39 % at 98 % |
| **H3a** (Boschloo, 300 per arm) | OL → AT: 95 % → 99 %: 90 %. 97 % → 99.5 %: 72 %. 97 % → 99 %: 48 %. So a gain is only reliably detectable if open-loop single vials sit near 95 % or below |
| **H2** (ED90 > 1.15 mm) | 97–100 % if the true ED90 is 2 mm or more; 0–20 % at 1.5 mm, because no level lies between 1 and 2 mm; 0 % at or below 1.15 mm, as a test should |
| **H3b** (AT widens ED90) | 100 % when AT's ED90 is 1 mm or more against an OL pocket's 0.3 mm. For 0.6 vs 0.3 mm the registered bootstrap rule detects it 88 % of the time (200 simulated campaigns); with no difference it says so falsely 1 % of the time |
| **H3c** (time cap 5 s) | 100 % if the true extra time is 4 s or less, 73 % at 4.5 s |
| **H4a** (30 cycles) | "Meets": 94 % if the true RP is 0.07 mm, 54 % at 0.08 mm. "Certified": 93 % at 0.06 mm, 52 % at 0.07 mm. These include instrument noise at *U* = 0.025 mm |
| **H4b, H4c** | 60 % and 83 % power for a 0.01 mm payload effect and 0.01 mm per 100 mm; 98–100 % at 0.02 mm |
| **MTBI** (600 E1 transfers per cell) | Imprecise by design: at 1 intervention per 100 transfers, the 95 % interval runs from 46 to 272 transfers |

**Why these sample sizes.** #21 fixes the minimum: 300 per task and condition, 20 per offset
level, 30 cycles per pose. The tables show what that buys. The one place it falls short of what
the question needs is H1a: 300 can only certify 99 % if the dock is close to perfect, so D5 offers
628 for that cell alone (about 330 more units, 6–9 hours of arm time).

### 8.5 Budget

| | Scored | Transfers, including resets of the cell |
|---|---|---|
| E1 (D5 = 300) | 1,200 loads + 1,200 unloads | 2,400 |
| E1 extra if D5 = 628 | 328 loads + 328 unloads | 656 |
| E2 | 1,680 loads | 3,360 |
| E3 | 300 pose measurements | — |
| **Total (D5 = 300)** | | **5,760 transfers** |

At 30 s per transfer that is about 48 h of arm time; at 45 s, about 72 h. Add the human resets:
about 600 in E2 at 2–3 minutes each, or 20–30 hours. Sessions are about an hour (R7), so the
campaign is roughly 70–90 sessions.

---

## 9. Configurations, blocks and randomization

- **Configuration.** Everything that can change how the arm behaves:
  - the harness commit, including any code, configuration or calibration file on the trial path;
  - the arm, its firmware, its joint zeros and its mounting;
  - the fingers and pads;
  - the cameras, their mounts and calibrations;
  - the dock, carriers, vials and shelf, and where each of them sits;
  - the taught points.

  Each configuration gets an ID (`cfg-N`) and a record of its commit, hardware, measured values
  (R1–R8) and photos. The record may list **spares**, parts identical to ones in use, that can
  replace a broken part without creating a new configuration.
- **Block.** A contiguous run of units in one session, under one configuration, following one
  schedule. A new session always starts a new block. A block is one "run" under the SOP: the
  person at the arm gives the "workspace clear" before it starts and again before it resumes after
  any reset, and stays at the E-stop throughout. The person at the cell starts a counted block from
  the harness, or a remote operator does who is in contact with them. An `@claude` run does not
  start counted blocks (its job lasts at most six hours and its token one).
- **Ledger.** A committed file keeps the trials still owed to each task × condition × level.
  Each block's schedule is drawn from it, so a block that ends early just leaves its unrun units
  in the ledger.
- **Randomization.** Each block's schedule is generated and committed before its first unit, by
  the harness's schedule generator, from a seed equal to the block ID. Units run in that order.
  The operator doesn't choose, skip or reorder them.
  - **E1 sub-blocks:** C-OL, C-AT, V-OL and V-AT once each, in random order. With D5 = 628, C-OL
    appears twice in every sub-block, and 28 sub-blocks chosen by the seed carry a third C-OL.
  - **E2 sub-blocks:** for one task, the pair (level ℓ, OL) and (level ℓ, AT), in random order,
    with the levels taken in random order without replacement until all 21 have run once. Pairs
    keep the two conditions side by side in time at every level.
  - **Block size:** R7. A block is made of whole sub-blocks.
- **Session types.** E1 and E2 run in separate blocks. A seeded random sequence assigns each
  session to E1 or E2 in proportion to the work left, so wear, drift and season fall on both. E2
  sessions alternate tasks in the same way. E3 runs in its own sessions.

---

## 10. Starting and stopping rules

**Pilot and start.** Everything before the first counted block is pilot. Pilot runs set R1–R8 and
prove the harness, and their data are never pooled with counted data. Counting starts with the
first block whose schedule is committed as counted, after (a) the registration is approved and
(b) every "before the first counted trial" gate in [`bench-readiness.md`](bench-readiness.md) is
met and recorded.

1. **Any change to code or hardware ends the block.** The next unit starts a new block.
   - **The count restarts.** If the change makes a new configuration, its counts start at zero.
     Each cell's *n* must be reached within one configuration. Earlier configurations are
     reported as development history and never pooled into the primary estimates.
   - **These are changes:**
     - any commit on the trial path;
     - re-teaching a point or recalibrating;
     - replacing, re-printing, re-gluing, tightening or adjusting a part;
     - moving the arm, table, dock, shelf or deck;
     - a firmware update, or setting a joint zero;
     - new pads, or swapping the finger inserts for the auger sleeves and back;
     - cleaning or refocusing a camera.

     Swapping in a declared spare ends the block but keeps the configuration.
   - **These are not changes:** restoring the scene after a failure without adjusting anything
     (re-seating an object, re-homing, a power cycle by the E-stop or the relay). They are
     interventions (§14.4), logged, and the block continues.
2. **Safety.** A **Critical** or **Catastrophic** event (§13.4) stops the block at once. Make the
   cell safe per the SOP and record what happened. Resuming always starts a new block.
3. **Run of failures, or the arm not at rest.** D11 (3 in a row, or 5 in the last 20 of one cell)
   stops the block for an inspection. So does a unit that can't start because the arm doesn't
   read its rest pose (§5). Anything the inspection fixes is a change under rule 1. Trials before
   the stop stay in the data.
4. **No stopping on results.** Each cell's *n* is fixed. Don't stop early because it looks good
   or bad. Don't extend past *n* because one failure spoiled the bound: that is optional stopping,
   and it voids the exact bounds. Rules 2 and 3 are the only interim looks, and both are for
   safety and upkeep. Nobody computes a cell's running success rate during the campaign; the
   harness shows counts done and counts owed, not rates.
5. **End.** A cell ends at its *n*, or at D12. Cells still short then are reported with their
   actual *n*. Sessions end between units, never in the middle of one.

---

## 11. Data recorded and availability

- **Per block:**
  - block ID, configuration ID, harness commit and hardware record;
  - seed, schedule file and ledger state;
  - operator, start and end times;
  - temperature, relative humidity and illuminance.
- **Per transfer:**
  - unit ID, task, condition and leg (load or unload);
  - offset axis and value;
  - start, look, release and check timestamps;
  - under AT, the tag detections and the correction applied;
  - success, and which criterion failed if any;
  - LabRobFail category, subtype and severity, from both scorers and after adjudication;
  - whether there was an intervention, with a one-line description;
  - near-miss flags;
  - the witness still.
- **Streams:** joints, efforts and gripper at ≥ 50 Hz; wrist frames at the look pose; witness
  video.
- **Storage.** Raw logs, stills and video go to D14. Schedules, the ledger, configuration records
  and the block log are committed to this repository as the campaign runs.

**Availability (the statement the paper will carry).** All counted and pilot data, the schedules
and ledger, the configuration records and every analysis script are public by the time the paper
is submitted: data on D14 with a DOI, code in this repository at a tagged commit archived with a
DOI. The confirmatory analysis is `analysis/prereg_stats.py` at the registered commit; any change
to it after registration is an amendment (§16). Witness stills and video are checked before
release so that no person appears in them.

---

## 12. Exclusions and missing data

**Exclusions.** Only these two kinds are allowed. Each is logged with a reason, the unit is
re-queued in the ledger, and its transfers leave the primary analysis:
- (a) **An external interruption:** a person entering the workspace, an alarm, a building power
  cut, or a network outage that stops the harness between transfers.
- (b) **An operator error while restoring the scene:** the wrong object, the wrong place or the
  wrong orientation, confirmed by the reviewer from the stills.

Nothing else is excluded. There is no outlier rule: every counted transfer under the arm's
control counts, including aborts, timeouts and faults. If exclusions exceed 5 % of any cell, the
report says so up front, and a sensitivity analysis counts the excluded units as failures.

**Missing data.** A transfer whose outcome can't be scored (no operator score and no usable
still) is missing. The primary analysis uses the scored transfers. A sensitivity analysis counts
missing transfers as failures. More than 2 % missing in any cell is reported up front. In E3, a
missed reading is retaken in the same cycle if the arm hasn't moved; RP is computed from the
available cycles if at least 27 of 30 remain, and otherwise that pose × payload run is repeated in
a new session.

---

## 13. Failure coding: LabRobFail

**Source.** Wang, H., Sun, B., Zou, A., Huang, D., Lv, Z., Wang, N., Li, R., Zhou, D., Guo, W.,
Wang, Z. and Ouyang, W. (2026). *LabRobFail: A Benchmark for Robotic Failure Analysis in
Chemical Self-driving Laboratory.* arXiv:2607.23704v2 (29 Jul 2026),
[doi:10.48550/arXiv.2607.23704](https://doi.org/10.48550/arXiv.2607.23704). The code is at
[Su-ISE-2001/SciRobo](https://github.com/Su-ISE-2001/SciRobo), which now redirects to
`Su-ISE-2001/LabRobFail`.

LabRobFail's 20,000 trajectories are failures injected in simulation, so we take its labels
and none of its rates. Text in quotation marks is verbatim from v2. Everything labelled *ours*
is this campaign's rule.

### 13.1 Five categories

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

### 13.2 Eleven subtypes

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

### 13.3 Coding rules (ours)

- **Code what was seen, not the presumed cause.** The category names imply causes ("Perception")
  that an open-loop arm doesn't have. We follow the paper's definitions of the observed event,
  and record the suspected root cause in a separate free-text field.
- **One primary subtype per failure:** the first thing that went wrong in time. Secondary
  subtypes are optional.
- **When nothing fits,** code `Other (<category>)` with a description. Example: under AT, the
  tag can't be detected, which is `Other (Perception)`. If more than 10 % of failures are
  `Other`, that gap in the taxonomy's coverage is reported as a finding.
- **Two coders,** the operator and the reviewer from §7, code every failure. κ is reported.

### 13.4 Four severities

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
| Critical | The cell can't continue in its current configuration. Examples: something needs repair, adjustment, re-teaching or recalibration; a fault needs diagnosis; glass broke outside the CubXL | Stop the block (§10, rule 2) |
| Catastrophic | Damage to the CubXL or the arm, or a person at risk. Examples: an injury or near miss, glass or sample spilled inside the CubXL, a collision with the gantry | E-stop, make safe, stop the campaign until reviewed with the safety officer (#22) |

For comparison with LabRobFail-Data, the reviewer also assigns each failure a Table 8 option.
That is a second field, filled in at review and never by the operator.

---

---

## 14. Analysis plan

[`analysis/prereg_stats.py`](analysis/prereg_stats.py) implements this section, and
[`analysis/simulate_and_check.py`](analysis/simulate_and_check.py) shows it recovering known
values from a synthetic campaign ([`out/recovery.md`](analysis/out/recovery.md)). The analysis
runs on the adjudicated scores. Variables are coded success = 1, failure = 0; offsets enter as
the magnitude |*d*| in mm (or degrees for yaw); nothing else is transformed.

### 14.1 Success rates

For each cell, report *k*/*n* with:
- the **Wilson** 95 % interval;
- the **exact (Clopper–Pearson) one-sided 95 % lower and upper bounds**. When *k* = *n* the lower
  bound is 0.05^(1/*n*).

| Failures in 300 | Point estimate | Wilson 95 % | Exact one-sided 95 % lower bound |
|---|---|---|---|
| 0 | 100 % | 98.74–100 % | **99.01 %** |
| 1 | 99.67 % | 98.14–99.94 % | 98.43 % |
| 2 | 99.33 % | 97.60–99.82 % | 97.92 % |
| 3 | 99.00 % | 97.10–99.66 % | 97.44 % |

Certifying 99 % takes 299 transfers with no failures, 473 with one, 628 with two. Certifying
99.9 % takes 2,995 with no failures.

### 14.2 Comparisons between conditions

- **Difference in proportions,** AT − OL, with **Newcombe's** hybrid-score 95 % interval, built
  from the two Wilson intervals.
- **H3a:** a one-sided **Boschloo** exact test (`scipy.stats.boschloo_exact`).
- **Gap closed, *G*:** a percentile-bootstrap 95 % interval from 10,000 resamples. Not reported
  when *p*(OL) ≥ 0.99.
- **Transfer time (H3c):** the two-sample **Hodges–Lehmann** shift with its Moses (Mann–Whitney)
  one-sided 95 % upper bound, on successful loads.
- **Sensitivity check:** a logistic regression with a random intercept per block, plus time
  since power-on and temperature as covariates. If it disagrees with the primary result about
  the sign of AT − OL, the report says so.

### 14.3 Capture envelope (ED50 and ED90)

- **Model.** For each task × condition × axis (x, y, yaw), **logistic regression** of success on
  |*d*|, with both signs pooled and the zero level included. The fit uses **Firth's**
  bias-reduced likelihood, so complete separation (all successes to 3 mm, all failures at 4 mm)
  still gives finite estimates.
- **Estimate.** ED_q = (logit *q* − β₀) / β₁, for *q* = 0.5 and 0.9.
- **Intervals.** **Fieller** intervals from the inverse Fisher information at the estimate: 95 %
  two-sided for reporting, and the two ends of the 90 % interval as the one-sided 95 % bounds
  used in H2 and H3b. If the slope can't be told from zero at that level, the interval is
  unbounded and the rule that uses it is not met. As a check, a percentile bootstrap that
  resamples trials within each level, 10,000 times.
- **Censoring.** A curve is right-censored if it has no failures at its largest offset, or if its
  fitted success there is still ≥ 90 %. Its ED90 is reported as "> 4 mm" (or "> 4°"), with the
  exact lower bound of success at that level, and never extrapolated.
- **Not reached.** If fitted success at zero offset is already below 90 %, ED90 is reported as
  "not reached" and counts as 0 in differences.
- **Capture radius:** min(ED90ₓ, ED90ᵧ), each floored at 0.
- **Secondary.** Separate slopes for + and − offsets, to show asymmetry; a probit link as a
  sensitivity check; the ±2 mm model-free check (H2).
- **Consistency check.** The zero-offset level of E2 is compared with E1 (Newcombe interval).

### 14.4 MTBI (Kaplan–Meier)

- **Intervention.** Any unscheduled human action needed to keep the cell running: touching the
  arm, an object or a fixture; an E-stop press; restarting software; re-homing. Each is
  attributed to the task × condition whose failure caused it.
- **Clock.** Each task × condition counts its own transfers (loads and unloads). Interventions
  caused by another cell don't reset it. Interventions that can't be attributed (operator pauses)
  count for every cell.
  - An interval starts at the cell's first counted transfer in a configuration, or right after
    one of the cell's interventions.
  - It ends at the cell's next intervention, which is an event. Session ends and planned
    power-downs are pauses, not ends: the clock runs on across sessions within a configuration,
    and is censored when the configuration or the campaign ends. (Censoring at every block end,
    as v1 did, would cap every interval at about 20 transfers, and neither S(50) nor the
    restricted mean could be estimated.)
  - The primary analysis uses E1 only. E2 provokes failures on purpose, so its interventions are
    reported separately.
  - A secondary analysis counts operating hours instead of transfers.
- **Estimator.** A **Kaplan–Meier** curve of transfers between interventions.
  - **MTBI** is the restricted mean up to τ = D13 transfers, with a Greenwood-based 95 %
    interval. The plain KM mean is undefined when the longest interval is censored.
  - **Cross-check:** total transfers ÷ interventions, with an exact Poisson (Garwood) interval.
    In simulation the Greenwood interval covered 93 % with 24 interventions but 86 % with about
    6, so when a cell has fewer than 10 interventions the Garwood interval is reported first.
  - Also **S(50)**, the chance of 50 transfers without an intervention, to set against the Ada
    figure in §1.
- **Assumption.** Each restore leaves the cell as good as before (a renewal process). Checked by
  plotting the hazard against transfers since the block start.
- **Secondary analyses.** Cumulative incidence for each LabRobFail category (Aalen–Johansen), and
  a log-rank test of OL against AT.

### 14.5 Metrology (RP, registration B)

For each pose and payload, with the *n* = 30 attained positions (*x_j*, *y_j*, *z_j*) and their
barycentre (x̄, ȳ, z̄), as ISO 9283 defines it:

$$l_j=\sqrt{(x_j-\bar x)^2+(y_j-\bar y)^2+(z_j-\bar z)^2},\quad \bar l=\frac1n\sum_j l_j,\quad S_l=\sqrt{\frac{\sum_j (l_j-\bar l)^2}{n-1}},\quad RP=\bar l+3S_l$$

- **Intervals for RP (H4a).** A studentized bootstrap (bootstrap-t): 10,000 resamples of the 30
  cycles, each studentized by its own jackknife standard error. The plain percentile bootstrap was
  rejected after the synthetic check: on 30 Gaussian points its upper bound covered only 71–76 %
  of the time; the bootstrap-t's covers 91–94 % (82 % with heavy-tailed errors), so "certified" is
  reported with that caveat. Each RP is reported next to the instrument's *U*.
- **H4b and H4c** use percentile-bootstrap bounds on the difference and the slope (10,000
  resamples of cycles within each pose × payload). With no payload effect, this rule gave false
  positives 4.3 % of the time in simulation.
- **Drift.** Position is regressed on cycle number. Any drift of the barycentre during a run is
  reported. ISO 9283 tests drift separately, from a cold start.

### 14.6 Outcome-neutral checks

These show whether the data can test the hypotheses at all. They are reported whatever the
results, and none of them is a reason to drop data.
- **Offsets reach the arm.** The logged commanded TCP pose at each E2 place differs from nominal
  by the injected offset to within 0.1 mm and 0.1°.
- **The correction works at zero offset.** Under AT, tag detection succeeds at ≥ 99 % of looks.
- **Scoring is reliable.** κ between operator and reviewer is ≥ 0.8; if not, the report leads
  with it.
- **E1 and E2 agree at zero offset** (§14.3).
- **The instrument is good enough.** E3's *U* ≤ 0.025 mm on a static target (H4a).

### 14.7 What gets reported whatever happens

All cells and every hypothesis, each as supported, refuted or inconclusive (or contrary, for
H3a). Every block, including those from superseded configurations. All exclusions, all missing
data and all amendments. Anything not in this section is labelled exploratory.

---

## 15. Known threats and optional extensions

These are **not in the budget.** Each extension must be added by amendment *before* its first
trial.

| Threat | Effect | Optional extension |
|---|---|---|
| **The object confounds the dock contrast.** A carrier and a vial differ in mass, grasp and fixture at once | Estimand (i) in §1 overstates or understates what the lead-in itself buys | T2 into a chamfered pocket vs the tight one: same vial, OL, *n* = 300. That isolates the lead-in |
| **The yaw levels saturate for the OL carrier** (§8.2) | The yaw ED90 is only known to be below 2° | Add ±0.5° and ±1°, 20 trials each |
| **AT may never fail within ±4 mm** | ED90_AT is censored at > 4 mm | If AT has no failures at ±4 mm on an axis, run ±6 and ±8 mm, 20 trials each, AT only |
| **A software offset may not equal a physical one** | E2 may misstate real capture | PR 272's plates: 20 OL carrier trials on `x+2mm` and 20 on `yaw+2deg`, against the same software offsets |
| **Dummies are not glass, and the deck is a mock-up** | Slip, breakage and the real deck's tolerances are not represented | A confirmation block with glass vials on a real CubXL deck, reported separately |
| **The operator knows the condition** | Scoring bias | Blind review of the witness stills (§7) |
| **J1 has jumped before:** its reading moved 7.9° on one enable (PR 20), and it was re-zeroed by 15.2° on 2026-11-14 | Open-loop placements fail after a power cycle for a reason unrelated to the dock | The rest-pose check before every unit (§5), and a stop under rule 3 |
| **Printed parts wear** over about 6,000 transfers | Reliability drifts | Inspect at block boundaries. A worn part that gets replaced means a new block |
| **The wrist Pi or its cable fails mid-campaign** (it went offline on 2026-11-13; the J6 roll once jammed on its cable at 16 A) | AT blocks stop; OL is unaffected because the camera is mounted but unused | Spares of the Pi and the cable are declared in the configuration record |

---

## 16. Amendments

v2 (2026-11-27), before any registration and before any counted trial, changed v1 (2026-10-10) as
follows:

| Section | Change | Reason |
|---|---|---|
| Header, §0 | Registry chosen (OSF Preregistration, two registrations). Fill-ins split into PI decisions (D) and pilot-set rules (R) | So registration doesn't wait for bench measurements |
| §2 H1 | Each hypothesis can now be refuted as well as supported | Symmetric reporting |
| §2 H2 | The ±2 mm model-free check is secondary. A rule for censored curves is added | The combination tested ED90 > about 2.5 mm, not 1.15 mm (power analysis) |
| §2 H3b | ED90 is floored at 0, and the censored case is defined by the fit as well as by zero failures | A flat AT curve could give a meaningless negative ED90 |
| §0, §8 | D5 offers *n* = 628 for C-OL; D6 offers trimmed levels for single-vial OL | Power for H1a; operator burden in E2 |
| §3, §12 | Outcomes, exclusions and missing data get their own sections | The OSF template asks for each |
| §4 | Set-up updated to the cell as it is: mpzy, relay and E-stop, PR 272 parts, wrist Pi, ≥ 50 Hz logging, payload, layout limits | Checked against the repo on 2026-11-27 ([`hardware-and-safety-check.md`](hardware-and-safety-check.md)) |
| §7 | A planned E-stop between units is not a failure | Aligns with the SOP's lockout |
| §8.2 | Yaw pin displacement uses PR 272's 250 mm pin spacing (v1 assumed 225 mm) | PR 272 |
| §8.4 | Power analysis added | Required by the registry |
| §9 | Ledger and paired sub-blocks in E2 | Blocks can end early without unbalancing the design |
| §14.6 | Outcome-neutral checks added | So a null result can be told from a broken set-up |
| §14.4 | The MTBI clock runs on across sessions within a configuration; Garwood first when a cell has < 10 interventions | Censoring at every block end capped intervals at about 20 transfers; Greenwood undercovers with few events (synthetic check) |
| §14.5, H4a | RP's interval is a bootstrap-t, not a percentile bootstrap | The percentile upper bound covered 71–76 % on synthetic data (synthetic check) |
| §5 | A failed leg is restored to its intended end state and the unit continues | Keeps one load and one unload per unit |

After the lock:

| Date | Section | Change | Reason | Trials run before it |
|---|---|---|---|---|
| | | | | |

---

## References

The full list, with every DOI checked against Crossref, is in [`references.md`](references.md).

---

## Appendix A. Checklist for the person at the arm

*Print this page, one sheet per block, and post the SOP's own one-page checklist next to it.*
Block ID `______` · cfg `______` · Operator `______` · Date `______`

**Before the first unit**
- [ ] You've done the SOP training and signed it. The **E-stop is in reach, unobstructed and was
      tested today** (press, twist out, nothing powers up, START). No tested E-stop, no session.
- [ ] Nobody else is within reach of the arm. The flap is down. You'll stay at the E-stop for the
      whole block.
- [ ] Teach-button cover on. Nobody uses teach mode during a block.
- [ ] The commit on mpzy matches the block's schedule file, and **nothing has changed since the
      last block.** If something has, stop and record a new configuration.
- [ ] Temperature, RH and lux logged. Witness camera recording.
- [ ] The cell is at its start state: carrier A in the dock, B in shelf nest 2, the vial in the
      shelf pocket, the dock pocket empty.
- [ ] This block's schedule is generated and committed. Run it in order.
- [ ] Say "workspace clear" with your name, then start the block.

**Every unit**
- [ ] Hands out of the workspace.
- [ ] Don't touch anything during a transfer unless you're stopping it for safety. A stop is an
      intervention and a failure.
- [ ] At each check, score the leg against §7. On a failure, record the category, subtype,
      severity and one line on what you saw.

**After a failure (the reset)**
1. Wait for the harness to park the arm at rest. Never press the E-stop with the arm raised
   unless it's an emergency: it drops.
2. **Press the E-stop.** Keep fingers away from the wrist and the J2 motor.
3. Put the objects back where the schedule expects them. Adjust nothing.
4. Hands and tools out, flap down. Twist the E-stop out, say "arm power on", press START.
5. Say "workspace clear" again, then resume the block.

| Severity | What to do |
|---|---|
| Minor | Log it and continue |
| Recoverable | The reset above. Log the intervention and continue |
| Critical | **Stop the block.** Make it safe and log it. Anything you fix makes a new configuration |
| Catastrophic | **E-stop.** Make safe per the SOP, stop the campaign, and call D15's contacts before anything else |

- [ ] 3 failures in a row, or 5 in the last 20 of one cell (D11): stop the block and inspect.
- [ ] The harness refuses a unit because the arm isn't at its rest pose: stop the block.

**Never**
- Adjust, tighten, re-teach, recalibrate, clean a lens or swap a part in the middle of a block.
  End the block first.
- Skip, reorder or rerun a unit. The exception is an excluded unit (§12), which the ledger
  re-queues.
- Stop early, or add units, because of how the numbers look.

**End of session**
- [ ] Stop between units. Park the arm at rest.
- [ ] Turn the arm off, or leave it at rest and limp per the SOP.
- [ ] Upload the logs (D14), write anything odd in the block log, and push.
