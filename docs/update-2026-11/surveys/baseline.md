# Baseline: what earlier Edison (PaperQA) answers established on low-cost 6-DOF arms in SDLs

**Answers and IDs.**
- **A-Q1–Q4** (Sept 2026, `docs/edison-6dof/`): SOTA; metrology and reliability; perception, LeRobot and sandbox; safety and control plane.
- **B-Q3–Q5** (branch `…0846`): grippers and generative CAD; closed-loop design protocol; sandbox object set.
- **W1-Q1–Q8** (2026-11-04) and **W2-Q1–Q9** (2026-11-27): `docs/wrtg-316/edison/`.
- B-Q1 and B-Q2 are byte-identical to A-Q1 and A-Q2, so there are 24 distinct answers (26 if the duplicates are counted).

**Checking documents.**
- **C-ver**: `6dof-verification-and-ecosystem.md`.
- **C-plan**: `6dof-q3-sandbox-plan.md`.
- **SEL**: `selection.md`, which checked sources against full text.
- **SBX**: `sandbox-object-set.md`.
- **GRP**: the gripper and generative-CAD survey.

**Tags.** [chk] = verified against full text in SEL or C-ver. [unchk] = SEL says it was not checked, or could not be. [pp] = preprint. [th] = thesis or report. [ext] = Edison's own extrapolation or an uncited claim.

**Pending query.** `u1-future-work-then-and-now` has been submitted but has no answer yet. It asks for:
- the stated future work of the central SDL papers, and what has happened since;
- 2026 evidence on (a) interventions per operation, (b) independent metrology of an arm under $5k, (c) open-loop vs vision-corrected primitives, (d) arms tending printers or powder equipment, and (e) remote supervision and teleoperation.

Section 5 avoids duplicating it.

## 1. Established findings by topic

### 1.1 Deployed arm-based SDLs
| Finding | Source | From |
|---|---|---|
| KUKA LBR iiwa 14 on a KMR base. 688 experiments in 8 days, 319 station moves, ≤21.6 h/day, ~32% idle (the GC was the bottleneck). Robustness tests: 464/464 vial grasps and places, 400/400 cartridge operations. | Burger 2020, *Nature*, 10.1038/s41586-020-2442-2 [chk]; thesis 10.17638/03087073 | W1-Q1/Q2, W2-Q1/Q8/Q9, B-Q5 |
| Two KMR robots serving a Chemspeed, UPLC-MS and NMR. More than a year of integration; no MTBI. | Dai 2024, *Nature*, 10.1038/s41586-024-08173-7 | A-Q1, W2-Q4 |
| YuMi + KMR PXRD workflow. Base ±10 mm, corrected by a six-point cube calibration. Gripper force cut from 20 to 10 N after fingers snapped. | Lunt 2024, *Chem Sci*, 10.1039/D3SC06206F | A-Q1, B-Q5, W1-Q5 |
| Franka FR3 scooping with a spatula: 1.93 ± 2.04 mg mean absolute error over 7 powders. | Radulov 2026, *Digital Discovery*, 10.1039/d5dd00569h | A-Q1, B-Q5 |
| Ada: about 1 run-ending failure per 40 samples, so a 50-sample run finishes 28% of the time; finishing 90% of runs needs 99.8% per sample. | Rupnow 2024 [th] 10.14288/1.0434661 | A-Q1 |
| UR3 OSCAR biology cell: tips placed to ±0.5 mm; about $35k in total. | Pivin 2026, *ACS Synth Biol*, 10.1021/acssynbio.5c00733 | W2-Q1/Q3/Q9 |
| MARS SDL (UR5e): pick-and-place was the main failure source. Gripper communication faults failed 29–43% of campaigns. | Ahlquist 2024 [th][unchk] 10.2172/2459394 | W2-Q2/Q7 |
| Also: a NIMS COBOTTA arc-melting cell; STELA YuMi, 1,024 assays in 24 h unattended [pp]; a PF400 colour-matching cell that completed 387 commands without intervention (Ginsburg 2023, 10.1145/3624062.3624615). | — | A-Q1, W1-Q2/Q5, W2-Q2 |
| SDL hardware tiers: ~$1M / ~$10k / $100–2k. The review gives no count of SDLs; its growth claim is a prediction. | Tom 2024, *Chem Rev*, 10.1021/acs.chemrev.4c00055 [chk] | W1-Q1, W2-Q1/Q2/Q3/Q5 |

Two sub-$5k-arm lab systems were found only by the checking documents, not by Edison: WetRobo (one PiPER, three lab tasks; arXiv 2609.18435) and LabDex (arXiv 2608.18618) (SBX).

### 1.2 Low-cost vs industrial: measured performance
| Finding | Source | From |
|---|---|---|
| UR5, ISO 9283 with length gauges: AP 0.022 mm and RP 0.033 mm (full load, 10% speed). RP 0.015–0.075 mm overall, within the ±0.1 mm spec. | Pollák 2020, 10.1177/1687814020972893 [unchk] | W2-Q5/Q6 |
| UR3 measured with a Pi 4 camera and ArUco (0.103 mm/px): RPp 0.147–0.265 mm. A dial-indicator check gave 0.0109 mm against a 0.03 mm datasheet, so the camera mostly measures its own chain. | Chajón 2026, *Robotics*, 10.3390/robotics15050086 [chk] | W1-Q3, W2-Q2/Q3/Q6 |
| Dobot M1 Pro, 125 loaded plate transfers per speed, dial gauges: IQR 0.006–0.034 mm. Lid placement fails sharply beyond Δy = 2.19 mm. | Harazono 2024, *SLAS Technol*, 10.1016/j.slast.2024.100200 [chk] | W1-Q4, W2-Q3/Q4/Q7/Q8 |
| Dobot Magician (~€1.5k) matched a trained person's accuracy, but was 3.5× slower at pipetting, 1.6× at autosampling and 3.0× at inoculation; inoculation repeatability "severely limited". | Rupp 2022, *SLAS Technol*, 10.1016/j.slast.2022.07.001 [chk] | W2-Q1/Q3/Q7/Q8 |
| Research arms: Blue home returns within 3.7 mm; Forte SD 0.29–0.59 mm, $212 [pp]; CloudGripper XY SD 0.027 mm; REPLAB WidowX 2 cm at system level, >100k grasps without major breakage (10.1109/icra.2019.8794390). | Gealy 2019; Chebly 2025; Zahid 2024; Yang 2019 | W1-Q1/Q3/Q4, W2-Q6 |
| Self-calibration: Franka from 3.3–8.8 to 0.24–0.35 mm; Kinova Gen3 Lite only from 5.99 to 2.66 mm, limited by gear backlash. | Franzese 2026, *Commun Eng*, 10.1038/s44172-026-00633-4 [chk] | W1-Q4/Q8 |
| Mobile-base error: KMR encoder-only strafing error grew to 30 mm over 10 runs; 1.6–4.4 mm with feature mapping. | Hifi 2025, 10.1088/1361-6501/adf3d4 [unchk] | W2-Q2/Q7 |
| PiPER: the 1.5 kg / 626 mm / 0.1 mm figures are the vendor's own claims. The only other source is a thesis that repeats the datasheet. Gripper 0–70 mm, 40 N, ±0.5 mm. | C-ver, SBX | W2-Q6 |

### 1.3 Metrology and ISO 9283
| Finding | Source | From |
|---|---|---|
| ISO 9283: 5 poses, ≥30 unidirectional cycles, RP = l̄ + 3S. Edison got the details only from secondary sources. | Suarez 2020, RA-L, 10.1109/lra.2020.2972870 | A-Q2, W1-Q2/Q3, W2-Q3 |
| Certifying 0.1 mm needs a reference with ≤0.02–0.03 mm uncertainty (an LVDT or dial nest plus rented laser-tracker days) [ext]. "Minimum paper": 5 poses × 30 cycles × 3 directions × 2 payloads × 2 speeds, plus ≥500 reliability cycles; about $5–10k. | — | A-Q2 |
| Thermal drift: KUKA ±140 µm cold vs ±20 µm warm, after about 2 h of warm-up. No data for arms under $5k. | Poonyapak 2010 [th] 10.22215/etd/2010-09686 | A-Q2 |
| Error ellipsoids validated with a laser tracker: reliability 0.98 in the centre vs 0.70 at the edges (10.3390/math14030580). pytransform3d (10.3389/frobt.2026.1860457). No turnkey repeatability-map software exists. | Issametova 2026; Fabisch 2026 | W1-Q8 |

### 1.4 Station calibration and fiducial accuracy
| Finding | Source | From |
|---|---|---|
| Touch calibration on a cube: 100 runs started from ±15 mm errors converged to 0.12 mm / <0.005°. This is repeatability, not accuracy. Vials and cartridges need <0.5 mm. | Burger 2020/2023 [chk] | W2-Q1/Q2/Q4/Q9 |
| LIRA (KMR, D435i), 100 repeats per condition: 20 mm ArUco 2.42 mm raw / 1.51 mm filtered; 75 mm marker 1.02 mm / 1.01°; touch 0.92 mm. Visual calibration ~5 s vs ~53 s for touch. 600/600 pickups and insertions over 8 h; 195/200 deliberate misplacements caught. | Zhou 2025, *Commun Chem*, 10.1038/s42004-025-01770-1 [chk] | W1-Q5, W2-Q2/Q4/Q8 |
| Fiducials instead of touch: ±0.41 mm [pp] (Brass, 10.26434/chemrxiv-2025-bsfvz). On a Sawyer, touch gave 0.12 mm vs ≤1.42 mm for one marker (Pagani 2021, 10.3390/robotics10010045 [chk]). | — | W2-Q4, SEL |
| Measured tag errors: ~1 cm at 70 cm, ~12 cm with offset and yaw (Abbas 2019, 10.3390/s19245480). Hand camera +14 mm bias, 1.02 mm after fusion (Wilcock 2026). Error falls from 41.8 to 17.8 mm as the tag grows from 67.5 to 126 mm (Yu 2021). Pi camera + ArUco mapping a lab bench: 15 mm (Wienbruch 2025, 10.1038/s41598-025-05670-1). | — | A-Q3, W1-Q5, W2-Q1/Q4 |
| AprilTag alone met a 1.5 mm GC-syringe tolerance only 4.8–9.5% of the time vs 100% for learned visual servoing (21 trials per method). | Angelopoulos 2023, 10.1109/IROS55552.2023.10341743 | W1-Q5, W2-Q9 |
| Rules of thumb [ext]: stop and look (rolling shutter smears 3–9 mm); tag bundles on fixture sidewalls; matte tags (blooming ≤0.74 mm); Tsai–Lenz hand-eye 0.08 mm RMS with 25 poses; "tag the fixture, not the part". | — | A-Q3, C-plan |

### 1.5 Transparent, specular and thin labware
| Finding | Source | From |
|---|---|---|
| Transparent objects: TransGraspNet 91% over 100 trials [pp]; GraspNeRF 88.9% from 6 views. LabGlass-IS centroid error 38 mm, "an open gap". | arXiv 2607.29567; 2210.06575 | A-Q1/Q3 |
| Specular metal: 6.6 mm top-down vs 32 mm / 49° at a 45° view (10.1109/rcae66389.2025.11355205). Pose models take 0.4–139 s per image; none has been tested on glassware. | Ma 2025; Vaggelis 2025 | A-Q1/Q3 |
| Vial insertion: 48.78% with vision only vs 89.55% with vision, force and tactile feedback. | Butterworth 2023, CASE (arXiv 2307.00671) | W1-Q5, B-Q5 |
| Parts under 2 mm thick are "essentially unstudied". | — | A-Q3, SBX |

### 1.6 Learned policies
| Finding | Source | From |
|---|---|---|
| ACT on ALOHA, 50 demos, 25 trials: 20–96% by task. Open-loop replay scored 0% vs ACT 40–95% (Mobile ALOHA). | Zhao 2023, arXiv 2304.13705; Fu 2024, arXiv 2401.02117 | W1-Q1/Q6/Q7 |
| Diffusion Policy on a real UR5 (Push-T): 136 demos, 20 episodes, 95%. | Chi, IJRR, 10.1177/02783649241273668 | W1-Q7 |
| SO-101 demo scaling. ACT: 1/40, 11/40, 18/40, 37/40, 35/40 at 12/25/50/100/200 demos. π0.5 plateaued near 70%. Identical checkpoints re-tested differed by 2/10. | Cowling 2026 [pp][unchk] 10.48550/arxiv.2610.37170 | W1-Q1/Q2/Q4/Q7, W2-Q5/Q8/Q9 |
| ArmnetBench, SO-101 fleet: 12 tasks × 7 policies, 50 demos each, 2,518 rollouts. Strict success: π0.5 47.6%, ACT 19.2%, SmolVLA 15.0%; pooled 27.4%. | Selvaraj 2026 [pp][unchk] 10.48550/arxiv.2607.24481 | W1-Q4/Q6/Q7, W2-Q2/Q5/Q6 |
| SO-101 Bench: simulation preserved policy rankings but overestimated success by 9–31 pp. PiPER: ACT 27–46% and DP 26–48% by action space [pp]. SO-101 vial placement with ACT: 34/36 [unchk] (10.2172/3684119). | Hickok 2026; Feng 2026; Johns & Gongora 2026 | W1-Q1/Q7, W2-Q4 |
| Lab tasks on a UR5e: VLA-Precision 100% on 2 mL vial transfer vs 80% for π0 [pp]. AutoBio (simulation): π0 failed to chain two lid steps (3%). | Su 2026, arXiv 2609.04355; Lan 2025 | W1-Q5, W2-Q2 |
| Reliability ceiling: VLAs reach 30–60% out of the box. SAFE-CHEM with a scripted fallback reached 98–99% [pp]. Imitation plus offline and online RL: 1000/1000 episodes, about 13.9 h per task (10.1126/scirobotics.aed6267). | A-Q1 sources; Lei 2026, *Sci Robot* | A-Q1, W2-Q9 |
| Effort [ext]: 50–200 demos for 80–95%. Learned primitive 1–3 weeks vs scripted 3–5 days. Hybrid recommended: learned approach, then a scripted, compliant seat. | — | A-Q3 |

### 1.7 Reliability statistics and reporting
| Finding | Source | From |
|---|---|---|
| Zero-failure trials needed for a 95% lower bound, n = ⌈ln α / ln p⌉: 59 for 95%, 119 for 97.5%, 299 for 99%, 1,497 for 99.8%. 25/25 successes only bound p at 0.887. | Vincent 2024, RA-L, 10.1109/LRA.2024.3445635 [chk] | W1-Q6, A-Q2, C-ver |
| Comparing two conditions differs from certifying one: 97.5% vs 99.8% needs ~310 per arm; 90% vs 95% needs ~435–475 per group. | — | C-ver, B-Q4 |
| Typical trial counts are 10–30 per condition. On LIBERO only 20.8% of 789 comparisons are significant. Only one SDL-related paper uses Wilson CIs, and its fault-recovery tasks are simulated. | Kress-Gazit 2024 [pp]; Wu 2026 [pp] arXiv 2611.18496 | W1-Q6, W2-Q8 |
| No standard for mean cycles between interventions (MCBI). Clinical lab automation MTBF is ~95–100 days. 71% of 17 SDL studies reported no precision data. | Volk 2024, 10.1038/s41467-024-45569-5 [chk] | W1-Q6, W2-Q1 |

### 1.8 Failure taxonomies
| Finding | Source | From |
|---|---|---|
| LabRobFail: 5 categories, 11 subtypes, 4 severity levels. Its trajectories are **simulated injections**. The VLM detector scores 90.8% on seen vs 71.0% on unseen scenes. | Wang 2026 [pp] 10.48550/arxiv.2607.23704 | A-Q2/Q4, W2-Q5, C-ver |
| Three-level taxonomy (execution / state and identity / measurement) with 5 autonomy levels. | Cheng 2026 [pp] 10.20944/preprints202608.0273.v1 | A-Q1/Q2 |
| Observed failures: capping 88% and rack insertion 92% successful [pp]. YuMi powder dispensing averaged 23.1% failure (10.1039/D3DD00075C). Ada: instrument faults 23.2%. | Fakhruldeen 2025; Jiang 2023 | A-Q1, B-Q5, W1-Q5 |

### 1.9 Safety and control plane
| Finding | Source | From |
|---|---|---|
| No SDL has certified ISO 10218 or ISO 13849 safety functions. The PiPER can claim no performance level; a hardwired e-stop relay is the only defensible safety function. | — | A-Q4 |
| UR5e and UR10e exceeded ISO/TS 15066 pressure limits in every lab collision scenario tested. | Mariano 2026, 10.1016/j.slast.2026.100463 [unchk] | W2-Q7 |
| Lower-precision arms standing in for a UR3e: ~3 cm frame error, one silently ignored an infeasible command, and two collided without an alarm. | Wattoo 2024, RABIT, 10.1109/DSN58291.2024.00043 [chk] | W2-Q7 |
| Al dust Kst ≈144 bar·m/s (10 µm) and ≈43 (20 µm); no AlSi10Mg data. Insulating printed parts are ignition sources. | Chen 2022, 10.1021/acsomega.1c05224 | A-Q4 |
| Control plane: a state machine over MQTT, bounded retries then HOLD, RO-Crate provenance; latency above ~50 ms degrades remote awareness. | — | A-Q4 |

### 1.10 Grippers, end effectors and tool changers
| Finding | Source | From |
|---|---|---|
| Printed PLA/TPU fingers designed from a container taxonomy cover 6 mm tubes up to plates. | Zwirnmann 2023 (arXiv 2302.03644) | B-Q3, SBX |
| Cable-loop gripper: 0.8% failure over 1,000 vial manipulations. | Manes 2024, 10.1038/s41598-024-59372-1 | W1-Q5, W2-Q5 |
| No published tool changer for arms with <1.5 kg payload; printed PLA parts are accurate to 0.18 ± 0.07 mm. | Li 2026, 10.3389/fmed.2026.1911165 | B-Q3/Q4 |
| Compliance can stand in for precision [ext]: ≥1 mm clearance, 15–30° chamfers. A force-controlled hand reached 95.2% vs 85.4% for a rigid gripper. | Van Wyk 2018, 10.1109/tro.2018.2791591 | A-Q3, W1-Q2 |

### 1.11 Generative CAD and closed-loop design
| Finding | Source | From |
|---|---|---|
| No system closes the loop from requirements to CAD, print, robot test and redesign; Fit2Form is the closest. Text-to-CAD benchmarks score geometry, not function. | arXiv 2011.06498 | B-Q3 |
| Feed the generator scalar rewards plus failure labels; adding execution images cut VLMgineer's reward by 5.4%. Protocol: 5 AI designs + 1 human design × 6 object classes × 3 prints; fatigue to 100k cycles. | CEGB, Vagas 2026, 10.1109/lra.2026.3677707 | B-Q4, GRP |

### 1.12 Sandbox object set and benchmarks
| Finding | Source | From |
|---|---|---|
| Benchmarks with industrial baselines: YCB peg 10/10 → 4/10 at a 5 mm offset; NIST board on a UR5e 96–100%; SceneReplica 36–66/100; Peg-in-Bench (0.1/1/3 mm clearances) [pp]. | 10.1109/mra.2015.2448951; 10.1109/iros51168.2021.9636586 | W1-Q2, W2-Q5, B-Q5 |
| Lab census of 38 systems: racks 14, vials 12, SBS plates 2, crucibles 2. The PiPER's 70 mm stroke is narrower than an SBS plate; J6 turns only ±100°. Plan: the first 119 zero-failure operations come from vials in racks. | — | B-Q5, SBX |

### 1.13 Cost per task
| Finding | Source | From |
|---|---|---|
| No answer found a cost-per-task or TCO figure for any lab arm. The nearest are labour-only: Dembski's "up to 75%" (44% in the body) [chk]; an OT-2 that halved labour cost per sample without paying back in 5 years [unchk]. | 10.1038/s41598-023-38535-6; 10.1016/j.slast.2024.100180 | W1-Q4, all W2 |
| Frameworks to borrow: quality-weighted output per cost (Reed 2021); TCO dominated by wages, spares and energy. Prices: SO-101 ~$225, ALOHA ~$21k, cloud lab ~$50k/month. | Cadène 2026 [pp] | W2-Q1/Q5/Q7/Q8 |

### 1.14 The case against low-cost arms
| Finding | Source | From |
|---|---|---|
| Gear backlash limits calibration. Cost cuts generally sacrifice accuracy (Lo 2024, 10.1039/d3dd00223c). Servo offsets differ between arms; agreement across cells is untested. 1.6–3.5× slower than a person. Counterpoint: cheap arms allow fleets for parallel evaluation. | — | W1-Q4, W2-Q6/Q7 |

## 2. Explicit "no published evidence" statements and their status

| Gap | Stated by | Status after the Nov 2026 runs and the checks |
|---|---|---|
| No independent metrology of the PiPER, SO-101 or Koch | A-Q1/Q2, W1-Q1–Q4/Q8, W2-Q1/Q6/Q7 | **Still open.** Narrowed for cheap arms in general (Forte, Blue, Dobot M1 Pro, Gen3 Lite). |
| No arm-specific MTBI or MCBI in any SDL | A-Q1/Q2, B-Q3, W1-Q6, W2-Q8 | **Still open** as a metric. Partial counts exist (LIRA 600/600, Burger 464/464, Ada ~1/40, Ahlquist). LabRobFail is simulated, so it does not fill the gap. |
| No low-cost arm doing real lab science | A-Q1, W1-Q1/Q5, W2-Q1/Q3/Q7 | **Narrowed**: Rupp's Dobot, Harazono's M1 Pro, Johns & Gongora's SO-101 vials, WetRobo on a PiPER. None runs a full SDL campaign. |
| No head-to-head low-cost vs industrial comparison on the same lab tasks | W1-Q1/Q4/Q6, W2-Q2/Q7/Q8 | **Still open.** |
| No cost-per-task or TCO metric | W1-Q4, all W2, SEL | **Still open.** |
| No imitation learning on lab tasks | W2-Q2/Q3/Q8/Q9 | **Contradicted** by W2-Q4 (SO-101 vials), W1-Q5 (VLA-Precision), AutoBio and WetRobo. Still true for powder dosing, weighing and plate loading. |
| No learned policy above 99% | A-Q3 | **Narrowed**: SAFE-CHEM with a scripted fallback (A-Q1); Lei 2026, 1000/1000 with RL, not in a lab (W2-Q9). |
| No AprilTag-guided scripted vs imitation-learning comparison on the same low-cost task | W1-Q7 | Still open; the PiPER AprilTag + MoveIt2 pipeline exists only in simulation. |
| Fiducial station recalibration not validated | W2-Q1/Q3/Q4/Q7/Q9 | The SDL-wide version (W2-Q3) is **contradicted** by LIRA. Still open on arms under $2k. |
| No physical lab-object benchmark | A-Q2, B-Q4/Q5, W1-Q2, W2-Q2/Q3/Q5 | **Narrowed** by LabDex, WetRobo and autobio-bench, which run 2 missed. No buyable object set yet. |
| No thermal data for cheap arms; hand-eye drift and parts under 2 mm unstudied | A-Q2/Q3, B-Q4 | Not revisited; open. |
| No certified SDL; no collision testing of any low-cost arm | A-Q4, W1-Q4, W2-Q7 | Open. Even certified cobots fail ISO/TS 15066 limits (W2-Q7). |
| No tool changer for <1.5 kg payload; no module-swap data | B-Q3, W1-Q5, W2-Q9 | Open. |
| No S-N curves for FDM flexures; no closed generative design loop; no metal-matched powder surrogate | B-Q3/Q4/Q5 | Not revisited. |
| Setup time per new task never measured | W2-Q9 | Open; only LIRA reports calibration time. |
| No AprilTag accuracy from a Pi camera at 0.2–0.4 m | W2-Q4 | **Partly contradicted**: Chajón (fixed Pi 4 camera, ArUco) and Wienbruch (Pi camera, 15 mm). No wrist-camera data. |
| No VLA in production SDL chemistry | A-Q1 | Narrowed by VLA-Precision (preprint) and AutoBio (simulation). |
| No reliability data for end effectors specifically | B-Q3 | Narrowed on industrial arms (Manes 0.8% over 1,000; Burger 464/464). |
| No robotic DSC press-fit; no SEM-stub or atomizer transfer | B-Q3, SBX | Not revisited. |
| No standard for evaluating mobile manipulators or station-recalibrating arms | W2-Q2 (citing Hifi), W2-Q4 | Open. |
| No backlash data for the queried arms | W1-Q3, W2-Q6 | Adjacent data only: a PLA gearbox with 0.57° backlash; a servo backlash test stand (Kotov 2026, HardwareX) that was not retrieved. |
| "No deployed SDL prints in the loop" | A-Q3 | Doubtful: BU's BEAR (Gongora 2020) combines printing and testing (outside knowledge; verify). |

## 3. Contradictions and known Edison errors

### Contradictions between answers
- **PiPER payload:** 250–500 g (A-Q2) vs 1.5 kg (vendor).
- **FDM accuracy:** ±0.1 mm (A-Q3) vs 0.2–1 mm (A-Q2) vs 0.18 mm (B-Q4).
- **Diffusion Policy Push-T demos:** ~200 (A-Q3) vs 136 (W1-Q7).
- **Learned >99%:** "never shown" (A-Q3) vs SAFE-CHEM and Lei 2026.
- **Robot in MATTERIX:** Franka (W1-Q2, W2-Q2/Q3) vs KUKA (W2-Q5).
- **Robot in Manes 2024:** YuMi (W1-Q5) vs KUKA (W2-Q5); SEL says the paper uses a Franka Panda.
- **Chajón 2026:** a UR3 [chk] vs "a self-built robot" (W2-Q2).
- **Angelopoulos 2023:** 21 trials per method (W1-Q5) vs 63 (W2-Q9).
- **SO-101 literature:** "only Huang 2026" (W2-Q7) vs four other papers.
- **Sample sizes:** 118 (A-Q2/Q3, B-Q4) vs 119 (correct). The 1,497-trial certification count is not the ~310 per arm needed to compare two conditions (C-ver).

**Other descriptions of the same paper that disagree**
- **Robot in Nasertorabi's thesis:** RTA ARTIC6 (W1-Q2) vs UR5 (W2-Q2).
- **LIRA's camera:** D435i (W2-Q2) vs "unspecified" (W2-Q4).
- **Wilcock 2026:** AprilTag, 1.02 mm (W1-Q5) vs "ArUco, sub-millimetre" (W2-Q3).
- **REPLAB attempts:** >50k / 92k vs >100k; its 2 cm system-level figure is used as arm accuracy in W1-Q4.
- **Cowling 2026:** 3% / 93% vs 2.5% / 92.5%; "1,340 episodes in 126 blocks" does not multiply out.
- **SmolVLA size:** "2B" (A-Q1) vs ~0.45B (A-Q3).
- **MegaPose runtime:** 1.68 s (A-Q1) vs 11–139 s (A-Q3), from the same source.

**Contradictions within the W2 run**
- **PiPER benchmarks:** "PiPER is in no benchmark" (W2-Q2) vs Feng 2026 and RoboTwin 2.0 (W1-Q7) and WetRobo.
- **MCBI equivalents:** "no MCBI equivalent" (W2-Q8) vs Ada's ~1/40 (A-Q1) and Ginsburg's commands completed without intervention (W2-Q2).

**Printed parts in the powder path**
- A-Q4: insulating printed parts are ignition hazards.
- B-Q3: proposes printed scoops and a magnetic tool changer, although magnets do not hold Al or Si.

### Known Edison errors found on checking
- **LabRobFail** (C-ver): its 20,000 trajectories are simulated, and Edison mislabelled its severity scale.
- **Software** (C-plan): MATTERIX is open source (BSD-3); `piper_ros` ships an MJCF and a URDF.
- **Sandbox objects** (SBX): B-Q5 invented the atomizer-part geometry, and its SEM-stub mass and mount sizes are wrong.
- **Power calculation:** B-Q4 says 95% vs 98% needs >1,000 per group; it is ~590–650.
- **LIRA** (SEL): accuracy is measured against the robot's own recorded pose.
- **Burger** (SEL): the ±0.12 mm is repeatability, not accuracy.
- **Rupp** (SEL): only the Dobot Magician was used.
- **Wattoo** (SEL): the paper never says "low-cost".
- **Vincent** (SEL): cited with the arXiv DOI instead of the RA-L DOI.
- **Le Houx** (C-ver): the scale is BASE, built for large user facilities, and ESME is a metric he cites, not one he proposed.
- **Datasets** (C-plan): the LeRobot robot list is stale, and "no labware dataset" missed autobio-bench and lerobotForScienceEdu.
- **A-Q3** got the IMX477 resolution wrong (~0.078 mm/px is correct, not 0.15).
- **A-Q1** cites GPT-5.1 results to Dai 2024, which predates GPT-5.1.
- **A-Q4** gets MQTT QoS levels wrong.
- **More from SEL:**
  - LIRA never says "6P", and its 97.9% figure is image classification.
  - Ferraguti's payload and repeatability are datasheet values.
  - Edison's ADePT quote is not in the paper.
  - Thieme's quoted wording could not be found.
- **Recurring metadata errors:** theses labelled "ArXiv"; arXiv DOIs given for published RSS, CoRL, IROS, ICRA and CASE papers; garbled years ("Jul 2607").

## 4. The 15 most load-bearing papers

| # | Paper | DOI | Cited by (of 24) |
|---|---|---|---|
| 1 | Burger 2020, *Nature* (+ 2023 thesis) | 10.1038/s41586-020-2442-2 | 7 (thesis 12) |
| 2 | Zhou 2025, LIRA | 10.1038/s42004-025-01770-1 | 4 |
| 3 | Tom 2024, *Chem Rev* | 10.1021/acs.chemrev.4c00055 | 5 |
| 4 | Chajón 2026, *Robotics* | 10.3390/robotics15050086 | 4 |
| 5 | Harazono 2024, *SLAS Technol* | 10.1016/j.slast.2024.100200 | 5 |
| 6 | Salazar-Villacis 2026, ADePT | 10.1038/s42004-026-01932-9 | 8 |
| 7 | Cowling 2026 [pp] | 10.48550/arxiv.2610.37170 | 8 |
| 8 | Selvaraj 2026, ArmnetBench [pp] | 10.48550/arxiv.2607.24481 | 6 |
| 9 | Yang 2019, REPLAB | 10.1109/icra.2019.8794390 | 6 |
| 10 | Rupp 2022, *SLAS Technol* | 10.1016/j.slast.2022.07.001 | 4 |
| 11 | Wang 2026, LabRobFail [pp] | 10.48550/arxiv.2607.23704 | 3 |
| 12 | Pollák 2020 | 10.1177/1687814020972893 | 3 |
| 13 | Darvish, MATTERIX | 10.1038/s43588-025-00924-4 | 3 |
| 14 | Vincent 2024, RA-L | 10.1109/LRA.2024.3445635 | 1 |
| 15 | Franzese 2026, *Commun Eng* | 10.1038/s44172-026-00633-4 | 2 |

Next in line: Dai 2024 (10.1038/s41586-024-08173-7), Wattoo 2024 (10.1109/DSN58291.2024.00043), Hickok 2026 (10.48550/arxiv.2610.36420), Lunt 2024 (10.1039/D3SC06206F), Lo 2024 (10.1039/d3dd00223c). Sulaiman 2026 (10.1007/s41315-025-00518-3) is cited by 6 answers but contributes no numbers.

## 5. Questions not yet asked (and not covered by pending u1)

1. **Metallography and SEM preparation.** Which steps have been automated, by arms or dedicated machines, and with what throughput, failure rates and specimen quality compared with manual work?
   - Metallography: sectioning, mounting, grinding and polishing, etching.
   - SEM: stub mounting, powder on carbon tape, sputter coating.
   - Every coverage check found this absent.
2. **AM feedstock characterization.** What robot-tended workflows exist for measuring metal-powder PSD, flow and density, and how do they handle contamination and inert gas? B-Q5's Hausner values were extrapolated.
3. **LPBF in the loop.** Which closed-loop alloy campaigns automate build-plate handling, coupon removal and testing, and where is an arm used?
4. **Hot work.** What is published on robots handling crucibles and samples at temperature, with gripper limits and success counts?
5. **Arm-based dosing of dense metal powders.** How does it compare with chemistry powders and with dedicated dosers?
6. **Printer tending before 2026.** Which systems remove parts or swap plates on FDM or resin printers, and with what success rates? (u1 covers 2026 only.)
7. **Design–print–test loops.** In loops for mechanical structures, what share of failures comes from specimen handling?
8. **Cloud-lab operating metrics.** What uptime, queue latency, job success and intervention figures have cloud labs published?
9. **Remote teleoperation for demonstrations.** How do latency and jitter affect demonstration quality and the resulting policy's success?
10. **Learning from interventions.** What gains do intervention-based methods (HG-DAgger, HIL-SERL, RLIF) report on real arms, especially low-cost ones? Wanted: success against hours of human intervention, and how the intervention rate falls during deployment. None of the 24 answers covered this; LeRobot ships HIL-SERL (W1-Q7).
11. **Agentic LLM control.** How reliable are LLM agents that write or sequence robot programs for physical lab tasks, and which verification layers reduce failures?
12. **VLM success detection.** What precision and false-alarm rates do detectors achieve on real lab outcomes, and what latency on edge hardware?
13. **Digital twins.** What quantitative sim-to-real gaps are reported for lab tasks, and has any twin predicted failures before execution?
14. **Durability of low-cost actuators.** What thermal rise, backlash growth and failure rates have been measured for STS3215-class servos and PiPER joint modules?
15. **Future work in the low-cost benchmark papers.** What do Cowling, ArmnetBench, SO-101 Bench, Harazono, Chajón and LIRA propose next, and has anyone done it? (u1 covers the SDL papers.)
