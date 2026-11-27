# OSF Preregistration (template v4), registration B: ISO 9283-style pose repeatability

Paste each answer into the matching field on OSF Registries (**Add New** → *OSF Preregistration*).
The template is the same as registration A's ([`A-transfer-reliability.md`](A-transfer-reliability.md)).
Section numbers (§) refer to [`PROTOCOL.md`](../PROTOCOL.md), attached as a PDF. Register B when
its own gates in [`bench-readiness.md`](../bench-readiness.md) are met: it does not have to wait for
registration A, nor A for it.

## Metadata

- **Title:** ISO 9283-style pose repeatability of a low-cost 6-DOF arm (AgileX PiPER), unloaded and with a vial-carrier payload (registration B of 2)
- **Description:** We measure the positional pose repeatability (RP, ISO 9283:1998) of an AgileX
  PiPER at five poses spanning the volume a CubXL-loading campaign uses, 30 cycles per pose,
  unloaded and with a payload equal to a full 8 + 1 vial carrier. We test the vendor's ±0.1 mm
  repeatability claim and whether RP grows with payload and with reach. Registration A covers the
  arm's transfer reliability in the same cell.
- **Contributors, license, subjects, tags:** as registration A, with the tags robot repeatability,
  ISO 9283, metrology, low-cost robot arm.

---

## Overview

### Research questions or hypotheses

Is the arm's positional pose repeatability within the vendor's ±0.1 mm, and does it grow with
payload and reach? α = 0.05 for each, one-sided (§2, H4).

- **H4a.** Unloaded RP ≤ 0.10 mm at all five poses. Supported ("meets the spec") if the ISO 9283
  point estimate is ≤ 0.10 mm at every pose, and also reported as "certified" if the one-sided
  95 % bootstrap-t upper bound is ≤ 0.10 mm at every pose. Refuted if the one-sided 95 %
  bootstrap-t lower bound exceeds 0.10 mm at any pose. Inconclusive if the instrument's expanded uncertainty exceeds 0.025 mm
  (ISO 9283 §6.5's 25 % cap).
- **H4b.** RP grows with payload: the one-sided 95 % bootstrap lower bound of the mean over poses
  of RP(loaded) − RP(unloaded) is > 0.
- **H4c.** RP grows with reach (horizontal distance from the J1 axis to the TCP): in a regression
  of RP on reach over 5 poses × 2 payloads with payload as a covariate, the slope's one-sided 95 %
  bootstrap lower bound is > 0.

Predictions, recorded for calibration only: Pred-7 and Pred-8 in §2.

### Foreknowledge of data or evidence

**Select:** *Data does not yet exist. No part of the data that will be used for this analysis plan
exists, and no part will be generated until after this plan is registered.*

### Explanation of foreknowledge and managing unintended influences

The arm's repeatability has never been measured in this lab, and no metrology fixture exists yet.
A static-target run that measures the instrument's own uncertainty, before any arm cycles, is part
of the procedure and is not data for H4. Joint readings logged during earlier, unrelated tasks
(teleoperation, a tape pick) show joint-level drift but say nothing about TCP repeatability at
these poses, and they are not used.

---

## Research design

### Study type

**Select:** *Descriptive study* and *Other*: a controlled metrology experiment after ISO 9283:1998,
with the order of payloads randomized within the session.

### Intention for causal interpretation

**Select:** *Indirect inference on causal relationship(s)*. Payload is manipulated; reach varies
with the fixed poses, so its slope is descriptive of this arm at these poses.

### Blinding of experimental treatments

**Select:** *Subjects will not be aware of the assigned treatment during data collection (either
because the subjects are not human participants or because of blinding procedures)*.

### Additional blinding during research or analysis

Positions are read automatically by the instrument and logged by the harness; nobody transcribes
or judges a reading. The analysis is a fixed script registered with this plan.

### Study design

ISO 9283-style pose repeatability (§8.3). Five poses P1–P5 lie on a diagonal plane of the largest
cube that fits the volume the campaign uses, around its dock and shelf: P1 at the plane's centre,
P2–P5 near its corners (about 10 % of the diagonal in from each, to be checked against ISO 9283
§6.8 before the fixture is built). Each cycle visits every pose in a fixed order, always
approaching from the same direction; after a 2 s settle the instrument reads the TCP's 3D
position. 30 cycles per pose, with two payloads: (1) unloaded (gripper, finger inserts, the
measuring target) and (2) loaded with a dummy mass equal to a full carrier at its centre of
gravity ([D9]). Both payloads run in one session, in random order, after a 15-minute warm-up
cycling over P1–P5, at the campaign's speed (R5). Temperature is logged.

### Randomization

The order of the two payload runs within the session is drawn from a seed equal to the session ID
and committed before the session. Pose order within a cycle is fixed, as ISO 9283 prescribes.

---

## Sampling

### Data collection procedures

One AgileX PiPER at spot D, in the configuration of registration A (firmware, joint zeros, gripper
and finger inserts recorded). The instrument ([D10]: for example three 0.001 mm digital indicators
on a sphere or cube target) must have an expanded uncertainty ≤ 0.025 mm (k = 2), measured on a
static target before the arm runs. The harness commands each pose and logs the readings with
timestamps and the joint states. The session runs under the lab's SOP with a trained person at the
E-stop. Expected duration: one session of about 2–3 hours.

### Sample size

300 measured pose visits: 5 poses × 30 cycles × 2 payloads. Each RP is computed from the 30
positions of one pose × payload.

### Sample size rationale

30 cycles per pose is the ISO 9283 number for pose repeatability, as set in the campaign request
(issue #21). Simulated power, including instrument noise at U = 0.025 mm (`analysis/out/power.md`):
"meets" holds at all five poses with 96 % probability if the arm's true RP is 0.07 mm and 55 % at
0.08 mm; "certified" (bootstrap-t upper bound ≤ 0.10 mm at all five) with 88 % at 0.04 mm, 61 % at
0.05 mm and 30 % at 0.06 mm, because a valid upper bound from 30 cycles is wide. H4b and H4c have 60 % and 83 %
power for a 0.01 mm payload effect and a 0.01 mm per 100 mm reach slope, and 98–100 % at 0.02 mm.

### Starting and stopping rules

The session starts after the instrument's static check passes, the warm-up ends and the
configuration record is committed. It stops when both payload runs have 30 cycles. A fault, a
contact or an E-stop ends the session; it is repeated in full in a new session, and the incomplete
run is reported. No run is extended or repeated because of its results.

---

## Variables

### Manipulated variables

- **Payload:** unloaded, or loaded with a dummy mass equal to a full carrier ([D9]).

### Measured variables

- Attained TCP position (x, y, z) at each pose, cycle and payload.
- Reach of each pose (horizontal distance from J1's axis to the TCP), from the commanded pose.
- Joint positions and efforts during each visit; temperature; time since power-on.

### Indices

For each pose × payload, from the n = 30 positions and their barycentre:
l_j = √((x_j − x̄)² + (y_j − ȳ)² + (z_j − z̄)²), l̄ = mean of l_j,
S_l = √(Σ(l_j − l̄)²/(n − 1)), and **RP = l̄ + 3 S_l** (ISO 9283:1998).

---

## Analysis plan

### Statistical models

`analysis/prereg_stats.py` (`iso9283_rp`, `bootstrap_t_rp`, `bootstrap_rp`): RP per pose × payload
with studentized-bootstrap (bootstrap-t) bounds, 10,000 resamples of the 30 cycles each studentized
by its jackknife standard error. On synthetic data its one-sided 95 % upper bound covered 91–94 %
with Gaussian errors (82 % heavy-tailed), against 71–76 % for a plain percentile bootstrap, which
is why the percentile version is not used for H4a. H4b: the bootstrap distribution of the
mean over poses of RP(loaded) − RP(unloaded), resampling cycles within each pose × payload. H4c:
ordinary least squares of RP on reach (per 100 mm) with a payload indicator, refitted in each
bootstrap replicate; the slope's 5th percentile is the one-sided bound. Drift: position regressed
on cycle number per pose × payload, reported.

### Transformations

Reach in units of 100 mm; payload coded 0/1. Nothing else is transformed.

### Inference criteria

One-sided 95 % bootstrap bounds as stated for each hypothesis; no correction across H4a–c, which
answer separate questions. H4a requires all five poses (an intersection–union rule).

### Data inclusion and exclusion

All readings are used. No outlier rule. A reading taken while the arm reports a fault, or after a
contact or an E-stop, ends the session (see stopping rules) rather than being dropped.

### Missing data

A missed reading is retaken in the same cycle if the arm hasn't moved. RP is computed from the
available cycles if at least 27 of 30 remain; otherwise that pose × payload run is repeated in a
new session and the incomplete run is reported.

### Other planned analysis

ISO 9283 drift from a cold start, a third run at 100 % speed override, and orientation repeatability
are not planned; any of them would be added by amendment before it runs.

---

## Other

### Context and additional information

The vendor states 0.1 mm repeatability for the PiPER; the design error budget behind registration
A assumes it (byu-vcl issue 266). ISO 9283 makes the 100 % rated load mandatory, so this is
ISO 9283-*style*, not a conformance test. Protocol and code: github.com/vertical-cloud-lab/robot-arms,
tag `prereg-v1`, `docs/protocol/`.
