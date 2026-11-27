# OSF Preregistration (template v4), registration A: transfer reliability and capture envelope

Paste each answer into the matching field on OSF Registries (**Add New** → *OSF Preregistration*).
The question order and wording are the template's, read from OSF's API
(`api.osf.io/v2/schemas/registrations/697b72f611a8e98484c6139b`) on 2026-11-27. Section numbers
(§) refer to [`PROTOCOL.md`](../PROTOCOL.md), which is attached as a PDF. Fill the blanks from
PROTOCOL.md §0 before pasting.

## Metadata (OSF's first page)

- **Title:** How reliably can a low-cost 6-DOF arm load a CubXL deck? Open-loop and AprilTag-corrected transfers of vial carriers and single vials (registration A of 2)
- **Description:** An AgileX PiPER arm loads a mock-up of a CubXL liquid-handling deck with 8 + 1
  vial carriers (into a dock with a 3 mm lead-in) and with single vials (into a pocket with ≤ 1 mm
  clearance), open loop and with wrist-camera AprilTag correction. We estimate per-transfer success
  against a 99 % target with exact bounds (at least 300 loads per task and condition), the dock's
  capture envelope from deliberate offsets (21 levels × 20 trials per task and condition), the
  time cost of correction, and the mean number of transfers between human interventions. Failures
  are coded with LabRobFail's taxonomy. Registration B covers the arm's ISO 9283 pose
  repeatability.
- **Contributors:** D16.
- **License:** CC-BY 4.0.
- **Subjects** (OSF's taxonomy, checked through its API): Engineering → Computer Engineering → Robotics; Physical Sciences and Mathematics → Chemistry → Analytical Chemistry; Physical Sciences and Mathematics → Statistics and Probability.
- **Tags:** robot reliability, self-driving laboratory, laboratory automation, preregistration, capture envelope, AprilTag, ISO 9283, LabRobFail.

---

## Overview

### Research questions or hypotheses

How reliable is a low-cost 6-DOF arm (AgileX PiPER) at loading a CubXL deck with vial carriers and
with single vials, and how much of the gap to 99 % success per loading transfer do (a) a lead-in
dock and (b) wrist-camera AprilTag correction each close? α = 0.05 for each hypothesis, one-sided
where stated. Each is reported with one of the labels fixed in §2: supported, refuted or
inconclusive (H1a, H1b, H2); supported, contrary or not supported (H3a); supported or not supported
(H3b, H3c).

- **H1a.** Open-loop carriers loaded into the 3 mm × 45° lead-in dock succeed at ≥ 99 %.
  Supported if the exact one-sided 95 % Clopper–Pearson lower bound is ≥ 0.99; refuted if the
  exact one-sided 95 % upper bound is < 0.99.
- **H1b.** Open-loop single vials loaded into a pocket with ≤ 1 mm diametral clearance succeed at
  < 99 %. Supported if the exact one-sided 95 % upper bound is < 0.99; refuted if the exact
  one-sided 95 % lower bound is ≥ 0.99.
- **H2.** For open-loop carriers, the dock's ED90 (the injected offset at which predicted success
  falls to 90 %) exceeds 1.15 mm, the worst-case arm error from the design's error budget, on both
  x and y. An axis supports H2 if its Firth logistic slope is significantly negative and the
  Fieller one-sided 95 % lower bound of ED90 exceeds 1.15 mm. If the curve is right-censored (no
  failures at 4 mm, or fitted success at 4 mm ≥ 90 %), it supports H2 instead when the exact
  one-sided 95 % lower bound of pooled success at |offset| ≥ 2 mm is ≥ 0.90. An axis refutes H2,
  at one-sided 99 % per axis (set by simulation so that H2 is refuted at most about 5 % of the
  time when the true ED90 is exactly 1.15 mm), if success over the 20 zero-offset loads has an
  exact upper bound below 0.90, or if the curve is not censored, its slope is significantly
  negative and the Fieller upper bound of ED90 is below 1.15 mm. An axis that meets both kinds of rule is inconclusive. Supported
  if both axes support it, refuted if either refutes it, inconclusive otherwise.
- **H3a.** AprilTag correction raises single-vial loading success: one-sided Boschloo exact test,
  p < 0.05. Contrary if the same test in the other direction gives p < 0.05; not supported
  otherwise.
- **H3b.** Correction widens the single-vial ED90 on both x and y. Each capture radius is ED90
  floored at 0 (0 if fitted success is below 90 % at zero offset). If the corrected curve is
  right-censored, an axis passes when the Fieller one-sided 95 % upper bound of ED90_OL is below
  4 mm. Otherwise it passes when the one-sided 95 % delta-method lower bound of
  radius_AT − radius_OL is > 0. Supported if both axes pass, not supported otherwise.
- **H3c.** Correction costs no more than [D8] s per single-vial loading transfer: the one-sided
  95 % upper bound of the Hodges–Lehmann shift in transfer time (corrected − open loop) is ≤ [D8];
  not supported otherwise.

Predictions, recorded for calibration only: Pred-1 to Pred-6 in §2.

### Foreknowledge of data or evidence

**Select:** *Data does not yet exist. No part of the data that will be used for this analysis plan
exists, and no part will be generated until after this plan is registered.*

### Explanation of foreknowledge and managing unintended influences

The arm has run other tasks (picking a tape roll, teleoperation), but nothing it has done involves
the dock, carriers or vials of this study. On 2026-11-27 those parts existed only as CAD; they are
printed after this protocol was written. Pilot runs, before or after registration but always before
counting, set eight procedural values by rules fixed in the protocol (R1–R8, §0: measured
clearances, tag size, timeouts, speed, block length, a contact-stop threshold); they are recorded in
the first configuration record with their measurements. Pilot data are never pooled
with counted data (§10). During the campaign nobody computes running success rates; the trial
harness shows counts done and owed, not rates (§10, rule 4). Every cell's sample size is fixed in
advance, and cells are not extended after a failure.

---

## Research design

### Study type

**Select:** *Randomized Experiment* and *Descriptive study*.

### Intention for causal interpretation

**Select:** *Direct inference on causal relationship(s)*.

The two conditions (open loop vs AprilTag-corrected) and the injected offset levels are assigned
at random within blocks, so H3 and the capture curves are causal contrasts. The task contrast
(carrier vs single vial, estimand (i) in §1) is not randomized in the same sense: the object
changes mass, grasp and fixture at once, so it is reported descriptively (§15).

### Blinding of experimental treatments

**Select:** *Subjects will not be aware of the assigned treatment during data collection (either
because the subjects are not human participants or because of blinding procedures)*.

Don't tick the coder option: the operator who scores every transfer knows the condition. The
blind second review is described in the next answer.

### Additional blinding during research or analysis

The subjects are transfers made by a robot. The operator at the arm knows the condition and scores
every transfer on the spot. A second person who did not operate those blocks re-scores every
failure and a random 10 % of successes from witness-camera stills taken after the arm has left,
which don't show the condition; a third person resolves disagreements, and the adjudicated score
is analysed. Cohen's κ between operator and reviewer is reported (§7). The confirmatory analysis is
a fixed script registered with this plan (`analysis/prereg_stats.py`).

### Study design

Two experiments share one cell and one configuration (§5–§9). They run in separate blocks, and a
seeded random sequence assigns each session to E1 or E2.

- **Tasks.** T1, carrier swap between a dock and a shelf; T2, a single vial between a shelf pocket
  and the dock's single-vial pocket. Each *unit* is one loading transfer (into the dock: the
  primary endpoint) and one unloading transfer (out of it), and leaves the cell in a known state.
- **Conditions.** OL, open loop (taught poses only), and AT, AprilTag-corrected (the dock's pose is
  measured from a wrist camera at a look pose and the dock-side pick and place are corrected in x,
  y and yaw). Both conditions stop at the same look pose; there are no automatic retries; any
  abort is a failure.
- **E1, nominal reliability:** 2 tasks × 2 conditions at zero offset, a fully crossed factorial in
  which every unit is one task × condition. Loading transfers per cell: 300, except [D5: 300 or
  628] for carriers under OL.
- **E2, capture envelope:** the dock frame the arm believes in is offset on one axis at a time:
  0; x = ±1, ±2, ±3, ±4 mm; y = ±1, ±2, ±3, ±4 mm; yaw = ±2°, ±4° (21 levels), 20 loading
  transfers per level per task × condition ([D6] may trim single-vial OL to 11 levels).
- **Success** (§7) is scored 2 s after the arm reaches its clear pose: the object fully seated
  (cone pins engaged and flat for a carrier; cap height within ±0.5 mm for a vial), every vial in
  place and upright, a clean release, no touch, no fault, and within the timeout.
- Within the factorial, task and condition vary between units; units are nested in blocks
  (sessions) and blocks in configurations. Counts must be reached within one configuration.

Full design: PROTOCOL.md (uploaded).

### Randomization

Blocked randomization with permuted sub-blocks, generated by the trial harness from a seed equal
to the block ID and committed before the block's first unit (§9). E1 sub-blocks contain each
task × condition once (with D5 = 628, carriers OL twice, plus a third in 28 sub-blocks chosen by
the seed) in random order. E2 sub-blocks are pairs (level, OL) and (level, AT) in random order,
with the 21 levels in random order without replacement. A ledger of owed trials lets a block end
early without unbalancing the design. A seeded random sequence assigns each session to E1 or E2
(and E2 sessions to a task) in proportion to the work left. The operator cannot choose, skip or
reorder units.

---

## Sampling

### Data collection procedures

The population is loading transfers by one AgileX PiPER arm (on loan to the lab, firmware recorded
per configuration) at the lab's spot D, with the dock, carriers, finger inserts and offset plates
of byu-vcl PR 272, printed vials, and a shelf at the cell. A trained operator stands at the
hardware E-stop for each block under the lab's SOP; a session of about an hour holds one block,
or more if a change or a stop ends one early. The
trial harness logs every transfer's timestamps, outcome, joint states at ≥ 50 Hz, the AprilTag
correction, and a witness-camera still; the operator records scores, failure codes (LabRobFail
categories, subtypes and severities, quoted in §13) and interventions. Temperature, humidity and
illuminance are logged per block.

Counting starts with the first block committed as counted after this registration is approved and
every pre-campaign bench gate is met (PROTOCOL.md §10; `bench-readiness.md`). Expected duration:
about 70–100 sessions over 8–16 weeks.

Inclusion: every loading and unloading transfer in a counted block. Exclusions: only external
interruptions and operator errors while restoring the scene (see below).

### Sample size

Unit of analysis: the loading transfer (unloading transfers are secondary).

- E1: 300 loading transfers for each of carrier-AT, vial-OL and vial-AT, and [D5: 300 or 628] for
  carrier-OL, each with a paired unloading transfer: 1,200 (or 1,528) loads and as many unloads.
- E2: 20 loading transfers at each of 21 offset levels for each task × condition: 420 per cell,
  1,680 in all (1,480 if [D6] trims single-vial OL to 11 levels). Per axis fit: 20 trials at zero
  plus 40 at each |offset| of 1–4 mm.
- Sizes are equal across conditions within a task, except carriers under OL when D5 = 628 and
  single vials under OL in E2 when D6 trims their levels. Units are nested in blocks, over about
  70–100 sessions.

### Sample size rationale

The minimum (300 per task and condition, 20 per offset level) was set by the PI in the campaign's
request (issue #21). The exact and simulated powers of every registered rule at these sizes are in
`analysis/out/power.md` (uploaded with `analysis.zip`; seeds fixed):

- H1a certifies 99 % at n = 300 only with zero failures; power is 55 % if the true rate is 99.8 %
  and 74 % at 99.9 %. At n = 628 (two failures allowed) it is 87 % and 97 %. This is why D5 offers
  628 for that one cell.
- H1b at n = 300: 80 % power if the true rate is 97 %, 99 % at 95 %.
- H3a (Boschloo, 300 per arm): 90 % power for 95 % → 99 %, 72 % for 97 % → 99.5 %, 48 % for
  97 % → 99 %.
- H2: supported 97–100 % of the time when the true ED90 is ≥ 2 mm, 0–20 % at 1.5 mm (no level
  lies between 1 and 2 mm), ≤ 0.2 % at or below 1.15 mm; refuted 1.0–5.1 % of the time at exactly
  1.15 mm (10,000 simulated campaigns per curve shape) and 79–100 % at 0.8 mm.
- H3b: 100 % when the corrected ED90 is ≥ 1 mm against an open-loop 0.3 mm; with no true
  difference, false support 0–1.4 %, including when the two curves' slopes differ.
- H3c: ≥ 99.6 % if the true extra time is ≤ 4 s against a 5 s cap.
- The run-of-failures stop ([D11], not a hypothesis) rarely fires on a healthy cell (a 9 % chance
  over 300 loads at 93 % success; at most 0.1 % over a task's E2 in the planning scenario). It
  stops an E1 cell that fails half its loads within about 14 loads, but is slow to flag one that
  fails 15–20 %, in E2 above all. PROTOCOL.md §8.4 gives the full rates.

### Starting and stopping rules

Start: pilot work (setting R1–R8 and proving the harness) ends, and counting begins, with the first
block committed as counted after registration approval and after every pre-campaign bench gate is
recorded as met. Pilot data are never analysed with counted data.

Stop (§10):
1. Each cell stops at its fixed n, or at the campaign end date [D12]; cells short at that date are
   reported with their actual n. No cell is stopped early or extended on the basis of results.
2. Any change to code or hardware ends the block; if it creates a new configuration, all counts
   restart at zero in it, and earlier configurations are reported as development history only.
3. A Critical or Catastrophic failure (§13.4) stops the block at once.
4. A run of failures ([D11]: in E1, 3 failed loads in a row in one cell; in E2, 2 failed
   zero-offset loads in one block, since E2's offset loads fail by design), or a unit that can't
   start because the arm isn't at its rest pose, stops the block for an inspection.
5. Each cell's primary estimate comes from the configuration in which it has the most counted
   loads (the later one if tied).

---

## Variables

### Manipulated variables

- **Task:** T1 carrier (an 8 + 1 printed carrier, [D3]) or T2 single vial ([D2]). Assigned per
  unit within blocks (E1) or per block (E2).
- **Condition:** OL (open loop) or AT (AprilTag-corrected, x, y and yaw, dock side only). Assigned
  per unit within blocks.
- **Injected offset (E2 only):** the dock frame the arm believes in is displaced along one axis:
  0; x or y = ±1, ±2, ±3, ±4 mm; yaw = ±2°, ±4° about the dock datum. Assigned per unit within
  blocks. Only the loading leg is offset.

### Measured variables

- **Loading success** (primary; 1/0) and **unloading success** (secondary), by the criteria in
  §7, adjudicated.
- **Failure code:** LabRobFail category (5), subtype (11, or "Other (category)") and severity
  (Minor, Recoverable, Critical, Catastrophic), plus LabRobFail's Table 8 severity label (§13).
- **Transfer time** (s): from the start of the pick approach to the arm reaching its clear pose
  after release.
- **Interventions:** any unscheduled human action needed to keep the cell running, with its
  attributed cell.
- **Near-miss flags:** lead-in recoveries, effort spikes below the contact stop.
- **Covariates and context:** block, configuration, time since power-on, temperature, relative
  humidity, illuminance; the AprilTag correction and detection quality under AT; joint positions
  and efforts.

### Indices

- **Per-cell success rate** k/n for loading transfers at zero offset (E1).
- **Gap to 99 %:** max(0, 0.99 − p). **Share of the gap closed by correction:**
  G = (p_AT − p_OL)/(0.99 − p_OL), defined only when p_OL < 0.99.
- **ED50 and ED90** per task × condition × axis: (logit q − β₀)/β₁ from a Firth logistic
  regression of loading success on |offset|. Capture radius = min(ED90ₓ, ED90ᵧ), each floored at
  0. Right-censored and "not reached" curves are handled as in §14.3.
- **MTBI:** the Kaplan–Meier restricted mean number of transfers between interventions up to
  τ = [D13] transfers, per task × condition, from E1. Each cell's clock counts only its own
  transfers, restarts after each of its interventions, runs on across sessions within a
  configuration, and is censored when the configuration or the campaign ends. **S(50):** the
  Kaplan–Meier probability of 50 transfers without an intervention.
- **Hodges–Lehmann shift** in transfer time, AT − OL.

---

## Analysis plan

### Statistical models

All rules are implemented in `analysis/prereg_stats.py` (uploaded) and shown recovering known
values from a synthetic campaign in `analysis/out/recovery.md`.

- **Success rates (H1):** per cell, k/n with a Wilson 95 % interval and exact Clopper–Pearson
  one-sided 95 % lower and upper bounds.
- **Condition contrasts (H3a):** AT − OL with Newcombe's hybrid-score 95 % interval; one-sided
  Boschloo exact test. Gap closed G with a percentile-bootstrap 95 % interval (10,000 resamples).
- **Capture envelope (H2, H3b):** per task × condition × axis (x, y, yaw), logistic regression of
  success on |offset| (both signs pooled, zero level included) by Firth's penalized likelihood.
  ED_q = (logit q − β₀)/β₁; Fieller intervals from the inverse Fisher information (95 % two-sided
  for reporting; the lower end of the 90 % interval supports H2 and the one-sided 99 % upper
  bound refutes it); delta-method standard errors for H3b's difference; a percentile bootstrap
  resampling trials within levels (10,000) as a check. Slope-significance, censoring and "not
  reached" rules as in §14.3.
- **Time cost (H3c):** two-sample Hodges–Lehmann shift (AT − OL) on successful single-vial loads in
  E1, with its Moses (Mann–Whitney) one-sided 95 % upper bound.
- **MTBI:** Kaplan–Meier estimate of transfers between interventions per task × condition (E1
  only; E2 reported separately), restricted mean up to τ with a Greenwood-based 95 % interval;
  the horizon is capped at the cell's longest observed interval; cross-check total transfers ÷
  interventions with an exact Poisson (Garwood) interval, reported first when a cell has fewer
  than 10 interventions; S(50).
- **Positive controls and checks (§14.6):** the logged commanded pose differs from nominal by the
  injected offset to within 0.1 mm and 0.1°; tag detection succeeds at ≥ 99 % of looks under AT;
  operator–reviewer κ ≥ 0.8; E2's zero level agrees with E1 (Newcombe interval). These are
  reported, never used to drop data.

### Transformations

Success is coded 1/0. Offsets enter the capture models as magnitudes |d| in mm (x, y) or degrees
(yaw), with signs pooled; separate-sign fits are secondary. ED90 is floored at 0 in differences.
Transfer times are analysed untransformed (rank-based). No other transformation, centering or
recoding.

### Inference criteria

α = 0.05 per hypothesis, one-sided where stated (all decisions are one-sided bounds or one-sided
tests as listed under Research questions). No multiplicity correction across hypotheses: each
answers a separate, pre-specified question, and every outcome is reported. Within H2 and H3b,
support on "both axes" is an intersection–union test, which needs no adjustment; refuting H2 on
"either axis" is a union, so each axis uses a one-sided 99 % bound (Bonferroni's 97.5 % let false
refutations at the boundary reach 5.1–10.4 % in simulation; 99 % gives 1.0–5.1 %). Each hypothesis
is reported as supported, refuted, or inconclusive (contrary or not supported for H3a, not
supported for H3b and H3c).

### Data inclusion and exclusion

All transfers in counted blocks are included, including aborts, timeouts and faults. There is no
outlier rule. Only two kinds of unit are excluded, logged with a reason and re-queued: (a) an
external interruption (a person entering the workspace, an alarm, a building power cut, a network
outage that stops the harness between transfers) and (b) an operator error while restoring the
scene, confirmed by the reviewer from the stills. If exclusions exceed 5 % of any cell, the report
says so up front and a sensitivity analysis counts them as failures. Blocks from superseded
configurations and pilot runs are reported but never pooled into the primary estimates.

### Missing data

A transfer with no operator score and no usable still is missing. Its unit is re-queued, like an
excluded unit, so every cell still reaches its n scored loads. The primary analysis uses scored
transfers; a sensitivity analysis counts missing transfers as failures. More than 2 % missing in
any cell is reported up front.

### Other planned analysis

Secondary: unloading success; the same H3 contrasts for carriers; ED50 and the yaw curves;
separate-sign slopes and a probit link; the ±2 mm model-free capture check; a logistic model with a
random intercept per block and time since power-on and temperature as covariates; MTBI in
operating hours; cumulative incidence of each LabRobFail category (Aalen–Johansen); a log-rank
test of OL against AT; the distribution of failures over LabRobFail's taxonomy, with the share
coded "Other" reported as a finding if above 10 %. Everything else is exploratory and labelled so.

---

## Other

### Context and additional information

- Design of the dock, carrier, finger inserts and offset plates: byu-vcl issue 266 and PR 272. The
  ±1.15 mm worst-case arm error is that design's estimate, not a measurement.
- Failure taxonomy: Wang et al. (2026), LabRobFail, arXiv:2607.23704 (v2). We use its labels, not
  its rates, which come from simulated failures.
- Safety: the cell runs under a job hazard analysis and SOP (repository PR 23), reviewed before the
  first counted block.
- Registration B (ISO 9283-style pose repeatability of the same arm) is registered separately
  because it needs a metrology fixture and shares no trials with this one.
- Protocol, power analysis and analysis code: github.com/vertical-cloud-lab/robot-arms, tag
  `prereg-v1`, `docs/protocol/`.
