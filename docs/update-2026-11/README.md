# Vision-enabled 6-DOF arm projects: the November 2026 update

This update answers the [2026-11-28 request on issue #1](https://github.com/vertical-cloud-lab/robot-arms/issues/1):
an extensive and thorough update on high-impact, timely projects for the lab's AgileX PiPER cell. It covers the
latest literature, the future work that earlier papers asked for, and the current state and goals of the arm cell,
byu-vcl and digital-alloy-lab (DAL). Everything here is a snapshot as of 2026-11-28.


**How it was built.** Six parallel surveys covered the robot-arms, byu-vcl, DAL and other org repositories (every issue
and PR listed, about 260 threads read in full), the literature from May to November 2026 (80 checked entries), and the
stated future work of 29 central papers, checked against the 11,095 works that cite them since January 2025. A
seventh condensed the 24 Edison answers already on record so they would not be asked again. Then this round sent new
high-effort Edison queries one at a time, each written against the answers before it (U1 to U6, in
[`../edison-6dof/`](../edison-6dof/)). Separate agents checked their load-bearing claims against the papers' full
text, read through a tunnel that exits from BYU's network. The survey notes are in [`surveys/`](surveys/) and the
checks are in [`verification.md`](verification.md).

## The short version

<!-- SHORT-VERSION -->

## 1. Where the lab stands

### The PiPER cell (robot-arms)

- **The arm has done little physical work, and nothing since 2026-11-14.**
  - What it has done: tape-roll picks (6 of 10 executed grasps succeeded, with code changing between attempts),
    up/down cycles, relay power tests, and the first sessions with jss265's SO-101 leader arm driving the PiPER (34 ms
    median round trip).
  - It has never gripped a vial, a carrier or an auger. There is no repeatability, success-rate or intervention data
    yet ([hardware check](https://github.com/vertical-cloud-lab/robot-arms/blob/c8b3408/docs/protocol/hardware-and-safety-check.md)).
- **The cameras are mostly down.** Only the fixed front camera on the Pi that drives the arm works. The wrist Pi has
  been offline since 11-11 and the back-camera Pi since 11-06 ([PR #81](https://github.com/vertical-cloud-lab/robot-arms/pull/81)).
  - No camera has an intrinsic or hand-eye calibration on hardware.
  - The one on-hardware tag test read 25 mm tags at about 1 m but 0 of 48 10 mm tags ([PR #40](https://github.com/vertical-cloud-lab/robot-arms/pull/40)).
- **The flagship study is ready to register, but nothing on the bench exists yet.** The CubXL loading campaign
  ([#21](https://github.com/vertical-cloud-lab/robot-arms/issues/21), [PR #89](https://github.com/vertical-cloud-lab/robot-arms/pull/89))
  is an OSF preregistration: open-loop versus AprilTag-corrected carrier and vial loading, at least 300 loads per cell,
  a 21-level capture envelope and ISO 9283-style repeatability. In all that is 5,760 transfers and about 660 human
  resets. The dock, carriers and finger inserts are CAD only, and the realistic first counted block is 2027-03-05.
- **The arm's own limits shape every task.**
  - Grasps: J5 stops at ±70°, so there is no straight-down grasp near the table.
  - Wrist cable: it limits J6 to about a 90° window.
  - Zeroing: J1 has jumped by multiples of about 7.95° on enable, and was re-zeroed by 15.2° on 11-14.
  - Gripper: the force overshoots (1 N·m commanded, 4.9–7.2 N·m peaks), and the motor overheated once mid-carry.
- **Safety is mostly on paper.** The E-stop has been installed since late October but never tested. A reboot of the arm
  Pi cuts power mid-move, and the arm has no brakes. The hazard analysis ([PR #23](https://github.com/vertical-cloud-lab/robot-arms/pull/23))
  has not been reviewed, and unattended runs are "no for now".
- **The newer directions are mostly simulated or agentic:**
  - a MuJoCo twin with AprilTag and auger-swap scenarios ([PR #77](https://github.com/vertical-cloud-lab/robot-arms/pull/77));
  - Apple's AMP1 reproduced on CaP-Gym with a simulated PiPER, now extended to A1-mini print removal, auger swap and
    atomizer charging ([PR #87](https://github.com/vertical-cloud-lab/robot-arms/pull/87));
  - printer tending ([#86](https://github.com/vertical-cloud-lab/robot-arms/issues/86));
  - a livestream with on-device face blurring ([PR #81](https://github.com/vertical-cloud-lab/robot-arms/pull/81)).
- **The team's priority and the paper's differ.** jss265's semester priority is swapping augers on the powder doser
  ([#42](https://github.com/vertical-cloud-lab/robot-arms/issues/42)). That is force-limited: the clip pull-out is
  estimated at 12–40 N against about 15 N at the flange, and has never been measured. Meanwhile powder-doser
  [#203](https://github.com/vertical-cloud-lab/powder-doser/issues/203) is moving the tap collar so augers lift
  straight out, and the multi-doser carousel is being designed to need no arm at all.
- **The WRTG 316 proposal** (jss265, due 12-01) frames the lab's question as which published tests show whether a
  low-cost arm can serve as an "automated manual manipulator" ([`docs/wrtg-316/`](../wrtg-316/)).

### byu-vcl: what the lab is building toward

- **A "vertical cloud lab" for alloy discovery,** with an aluminium campaign (FLAIME, for DOE's Genesis Mission) and a
  copper campaign (the ONR YIP). The current design uses two MiR250 + UR12e mobile manipulators rather than the PiPER
  ([#303](https://github.com/vertical-cloud-lab/byu-vcl/issues/303)).
- **The lab's own analysis says transport doesn't bind and handling times are guesses.** byu-vcl's digital twin
  ([#407](https://github.com/vertical-cloud-lab/byu-vcl/issues/407), [PR 410](https://github.com/vertical-cloud-lab/byu-vcl/pull/410))
  found:
  - "Transport doesn't bind … the robots are 1–2 % busy."
  - What binds is "money, the atomizer, DED, the 30-day immersion and decision time … about 250 results a run wait
    a median of 77 h for a person."
  - "The handling times are stand-ins. Nobody has timed a MiR250 + UR12e at our instruments."
- **The throughput goal** is to go from about one alloy tested per day to ten ([PR 318](https://github.com/vertical-cloud-lab/byu-vcl/pull/318)).
- **The AI for Science application** (submitted 11-06, [#325](https://github.com/vertical-cloud-lab/byu-vcl/issues/325))
  asks "can a language-model agent design and validate this connecting hardware, and the robot workflows around it,
  well enough that the alloy loop runs with minimal human handling, with full provenance and traceability?" It puts
  fixtures (cup station, press nest, cup carrier, SEM stub holder) in months 1–2 and an **arm cell in months 2–4**.
- **The most fully specified arm task is CubXL vial and carrier handoff** ([#266](https://github.com/vertical-cloud-lab/byu-vcl/issues/266)):
  a 3 mm lead-in dock, an 8 + 1 carrier of 0.53–0.66 kg, a ±1.15 mm worst-case error budget, and 200-swap pass criteria.
- **The most timely task is clearing printer plates.** For the ME toy drive (first delivery Dec 10, last day Dec 18,
  [#399](https://github.com/vertical-cloud-lab/byu-vcl/issues/399)), sgbaird wrote "we will probably try
  auto-removing them via a ping to robot-arms" ([PR 402](https://github.com/vertical-cloud-lab/byu-vcl/pull/402)).
  Today people clear every plate, and an agent won't send a print until a camera frame shows the plate clear.
- **Constraints:**
  - The CubXL Pi is overloaded and dropped off on 11-17.
  - The OT-2 "needs new direction".
  - Budget is tight, and metal-powder safety rules apply.
  - Two people did hands-on hardware work in byu-vcl over the last two weeks, and the semester is ending.

### DAL: where the hours go

- **FLAIME's loop:** CALPHAD → AMAZEMET rePOWDER ultrasonic atomizer → LPBF → density, hardness, tensile and
  corrosion. Cost-aware BOFN/pKGFN chooses the next experiment.
- **The campaign** plans 40 atomizer runs and a paper targeted for Feb 28, 2027, realistically March–May
  ([DAL #277](https://github.com/vertical-cloud-lab/digital-alloy-lab/issues/277)).
- **The atomizer has been down since a cup failure on 11-13.** Restart is targeted for Dec 11–18, then about 20 Al
  runs from Jan 4 to Feb 9.
- **The bottleneck is the work after each run.** DAL's own schedule says "The atomizer isn't the bottleneck; the work
  after each run is. One run takes about 10–15 person-hours from charge to SEM", and none of it has been timed
  ([DAL #256](https://github.com/vertical-cloud-lab/digital-alloy-lab/issues/256)).
- **Arm-ready steps, ranked by the DAL survey:**
  1. post-run powder workup: the mass balance, loading the sieve shaker, splitting, jars and labels, and 5 g oxygen
     samples;
  2. SEM stub logistics, at 7–8 stubs per run (12.7 mm pin stubs in 3.4 mm holes);
  3. charge kitting from bar slugs and master-alloy pieces;
  4. an Archimedes density and Vickers hardness station.
- **Keep the arm out of the atomizer.** Only three trained operators may touch it, and a transducer slip costs $5–10K.
- **Aluminium powder is a combustible metal** (NFPA 484, now NFPA 660). DAL's guidance keeps unrated electronics out
  of the powder enclosure, so any cell handling powder needs an EHS review first.
- **FLAIME already plans to replace each human handoff with a robot in Phase II.** It notes a private door between the
  powder lab and the microscopy center.

### The rest of the org

- **powder-doser:** augers (Ø25 × ~250 mm; 53 g empty, ~155 g full) are filled and swapped by hand. 25 standalone
  dosers are being built.
- **tensegrity-optimization:** the drop tower is in a shared lab elsewhere and has been halted since its
  accelerometer broke on 10-19.
- **caliber:** this is about SEM/EDS acquisition settings, and the SEM belongs to a department facility.
- **custom-induction-furnace:** its 20 mm crucible is loaded with tweezers.
- **digital-wetlab:** "The OT-2 has no gripper", so 96-well plates move by hand.
- **CubOS:** a fork of Ursa Labs' gantry software, with a SiLA 2 / HTTP API.
- **borysgroup/aurora-cloud-infra:** the PiPER came from there, unused ("aurora does not need it"). The wrist-camera
  mount there (#5) is specified but not built.

Full notes: [`surveys/robot-arms.md`](surveys/robot-arms.md), [`surveys/byu-vcl.md`](surveys/byu-vcl.md),
[`surveys/dal.md`](surveys/dal.md), [`surveys/org.md`](surveys/org.md).

## 2. What changed in the literature since September

Most items below are 2026 preprints; the full list, with what each reports, is in
[`surveys/lit-latest.md`](surveys/lit-latest.md).

1. **Coding agents overtook vision-language-action models (VLAs) on manipulation benchmarks, but they are slow.**
   - Apple's AMP1 ([arXiv:2611.09892](https://arxiv.org/abs/2611.09892), Nov 6) has a frontier model write Python for
     the arm. It reports 85.6% on RoboLab-120 against 49.2% for the best VLA, and 104/108 real trials against 27.8%
     for π0.5, at 280 s per task and about $1.39 per episode. It is Franka-only, with calibrated depth.
   - CaP-X/CaP-Gym ([arXiv:2603.22435](https://arxiv.org/abs/2603.22435), ICML 2026) is now the shared benchmark.
   - WetRobo ([arXiv:2609.18435](https://arxiv.org/abs/2609.18435)) had a coding agent drive **PiPER** arms across two
     wet labs, but reports no reliability statistics.
2. **The PiPER became the default low-cost arm in lab-manipulation papers,** and none of them reports its accuracy or
   repeatability:
   - RoboSynChallenge ([arXiv:2608.12416](https://arxiv.org/abs/2608.12416)): π0.5 reached 33–38.5% on pipette and
     sample-loading tasks.
   - Robo-MLT ([arXiv:2611.13039](https://arxiv.org/abs/2611.13039)): 82% and 70% from about 1,000 demonstrations
     per task.
   - TVF-DiT: powder transfer, over only 10 trials per task.
   - LoRA-SP at ICRA 2026.
3. **Independent numbers for the SO-101 are far below launch claims.**
   - A failure benchmark ([arXiv:2606.08881](https://arxiv.org/abs/2606.08881)): π0.5 56% and SmolVLA 33% with 100
     demonstrations per task.
   - Cowling ([arXiv:2610.37170](https://arxiv.org/abs/2610.37170)): ACT went from 1/40 to 37/40 between 12 and 100
     demonstrations.
   - RoboColosseum ([arXiv:2611.02497](https://arxiv.org/abs/2611.02497)): SO-101 rankings were the least
     reproducible across sites.
4. **Lab-specific VLA benchmarks multiplied, and all show low success.** Examples are LabDex, SciVLABench, DexBioLab and
   Labference. In Labference, VLAs ignore the balance reading, so dosing to a target mass needs an explicit controller
   layer.
5. **Success and failure detection became an off-the-shelf part.**
   - Gemini Robotics ER 2 reports 82.4% video success detection.
   - Robometer and TOPReward ship inside LeRobot.
   - LIRA's fine-tuned edge VLM caught 195 of 200 hand-placed errors ([Zhou et al. 2025](https://doi.org/10.1038/s42004-025-01770-1)).
6. **LeRobot churned.**
   - v0.7.0 (Nov 5) replaced `async_inference` with a policy server.
   - Python 3.12 has been required since v0.5.
   - The PiPER is still supported only through third-party plugins.
   - LeRobot ships a HIL-SERL pipeline in which an **SO-101 leader arm can take over mid-episode** and the
     intervention rate is logged ([docs](https://huggingface.co/docs/lerobot/hilserl)).
7. **Cloud-lab and metals money landed in July–August 2026.**
   - NSF's Programmable Cloud Laboratories got $380M, plus up to $20M from Astera, and includes metals nodes.
   - CMU's Materials Innovation Cloud Lab starts by automating **Al-alloy powder production on an AMAZEMET rePOWDER,
     the same atomizer DAL uses** ([CMU news](https://engineering.cmu.edu/news-events/news/2026/08/07-accelerate-materials-discovery.html)).
   - Texas A&M is building a $24.9M metals SDL open to U.S. academics ([TAMU news](https://stories.tamu.edu/news/2026/08/05/texas-am-to-build-self-driving-laboratory-for-metals-open-to-researchers-nationwide/)).
   - DOE Genesis Phase I made 278 awards.
8. **Robots now load crucibles and arc melters:**
   - AlloyBot (preprint, [10.21203/rs.3.rs-9761885/v1](https://doi.org/10.21203/rs.3.rs-9761885/v1)): about one
     alloy an hour;
   - NIMS's COBOTTA + Quantos cell;
   - A-Lab follow-ups under inert gas.

   Metallographic preparation stays manual in academic labs except BAM's UR5e-based RASI. Printer farms use
   sheet-swapping harvesters (Prusa's automatic sheet changer).
9. **The Liverpool and LLNL groups are moving on the same questions.**
   - Liverpool: LIRA; closed-loop rack insertion ([RackInsert](https://doi.org/10.1109/case69030.2026.11704402));
     tool–policy co-design for powder weighing ([arXiv:2609.39797](https://arxiv.org/abs/2609.39797)); FLIP at ICRA
     2026; RobInHood.
   - LLNL (Gongora, of BU's BEAR): SO-101 vial placement with ACT, and a teleoperation interface for SDL fault recovery
     on a UR3e ([arXiv:2611.18496](https://arxiv.org/abs/2611.18496), Nov 13).
10. **The safety baseline moved.**
    - ISO 10218:2025 and R15.06-2025 add cybersecurity requirements for networked robots.
    - LabSafety Bench: no model reaches 70% on hazard identification.

    So an LLM or VLM cannot be the safety layer.

## 3. Future work the field keeps asking for

From 29 central papers' own limitations and future-work sections, with every citing work since January 2025 screened
([`surveys/future-work.md`](surveys/future-work.md)):

| Rank | Still open (Nov 2026) | Papers stating it | Closest follow-ups (all partial) | Fit for this lab |
|---|---|---|---|---|
| 1 | **Quantified reliability**: per-operation failure or intervention rate, MTBI, assisted vs unassisted lifetime, with confidence intervals | 14 of 29 | LIRA's 600/600 operations with no interval; IBM RoboRXN's multi-year report (not an arm); [ADePT 2026](https://doi.org/10.1038/s42004-026-01932-9) now explicitly asks for per-step error rates | Cheap to generate: log every cycle and every human touch |
| 2 | **Low-cost arms validated for lab tasks** ("the type of robot arm remains unknown", Harazono 2024) | 7 | [AR4Calib](https://doi.org/10.1016/j.mfglet.2026.08.019) (Annin AR4, Oct 2026), Forte (Humanoids 2025), WetRobo | Nothing on the PiPER |
| 3 | **Powder and solid handling** across powder types and small masses | 6 | Liverpool's FLIP and tool–policy co-design, SCU-Hand, all on a Franka or bespoke hardware with chemistry powders | Metal AM powders on a low-cost arm: open, but safety-gated |
| 4 | **Robots restocking consumables** and preparing setups | 6 | Self-Building Labs (layout and skills only) | **No follow-up found.** CubXL vials and tips, OT-2 tip racks and printer plates are all restocked by hand |
| 5 | **Hardware for structural and solid-state materials** (dispensing, high temperature, mechanical testing, microstructure) | 5 | NIMS 2026, AlloyBot, AIMD-L | No low-cost version exists; this is DAL's loop |
| 6 | Perception without touch calibration (markerless, transparent, reflective; vision-based station registration) | 5 | LIRA, RackInsert, [quARtet](https://arxiv.org/abs/2610.01072) multi-tag marker | Fiducials on fixtures remain the pragmatic route |
| 7 | Safety for unattended and remote operation | 5 | Mostly simulation and benchmarks | No certified pre-flight check for remote users |

### The earlier opportunities, checked again

| # | Opportunity from September | Status now | What remains new |
|---|---|---|---|
| 1 | First measured intervention-rate / MTBI dataset for an arm in a real SDL | **Not scooped**, but Liverpool and LLNL are close | A ≥500-cycle campaign with a LabRobFail-compatible taxonomy, exact intervals and assisted/unassisted lifetime |
| 2 | Metrology of a sub-$5k arm | **Partly scooped** by AR4Calib (Annin AR4, error 51 → 6.0 mm, validated with dial indicators per ISO 9283) | A full ISO 9283 study of a *commercial* sub-$5k arm (the PiPER) in lab poses, with drift and traceable ground truth |
| 3 | Vision-corrected primitives, open-loop vs corrected | **Partly**: RackInsert (Franka, 83.1%), quARtet (UR5e), Fontenot 2026 (xArm, no open-loop baseline) | Per-primitive success with intervals, open-loop and corrected, on a low-cost arm |
| 4 | Cloud-operated frugal SDL with reported uptime | **Partly**: [SmartLab](https://doi.org/10.1093/jcde/qwaf034) made and tested 90 printed specimens remotely; no uptime anywhere | Uptime and intervention statistics for remote users |
| 5 | Wrist-camera handling of metal powders | **Not scooped** | Al-alloy powders, a low-cost arm, combustible-dust handling |
| 6 | Generative gripper design → print → measure | **Largely scooped as a concept** (tool–policy co-design, soft-gripper co-design, Dextra) | Measure-redesign-reprint iteration for labware on a low-cost arm, with long-term validation |
| 7 | Lightweight tool changer | **Partly**: [Any-ttach](https://arxiv.org/abs/2605.30569) (96% swaps, printed PLA) and SwapBot, both on heavier arms | A changer budgeted for a 1.5 kg payload, with swap statistics |
| 8 | Station recalibration with fiducials | **Partly**: LIRA (industrial arm, no external ground truth) | Low-cost fixed arm, tag bundles, external dial-indicator truth, drift over time |

<!-- EDISON-SECTION -->
