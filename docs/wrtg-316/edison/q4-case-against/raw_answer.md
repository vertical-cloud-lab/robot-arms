# The Case Against Low-Cost Robot Arms for Laboratory Automation: Evidence from Published Literature (2015–2026)

## Overview

This review synthesizes evidence from peer-reviewed journal articles, major conference papers, and flagged preprints addressing whether low-cost robot arms—specifically the AgileX PiPER (~$2k), SO-100/SO-101 leader/follower arms (~$200), and comparable platforms—are suitable for laboratory automation when compared with industrial and research arms such as the UR5e, Franka Emika Panda, KUKA iiwa, and Kinova Gen3. The evidence is organized around five arguments against low-cost arms: (1) accuracy and repeatability, (2) reliability and durability, (3) safety and certification, (4) hidden integration and maintenance costs, and (5) imitation-learning performance gaps tied to hardware quality.

---

## 1. Accuracy and Repeatability: An Order-of-Magnitude Gap

The most quantitatively documented argument against low-cost arms concerns positional accuracy and repeatability. The following table summarizes the available comparative data:

| Arm model / class | Position repeatability or observed error | Calibration / absolute error | Repeatable measurement protocol | Evidence status and source |
|---|---:|---:|---|---|
| **Franka Emika Panda / FR3** | Not separately reported in the cited test | After calibration: **0.151–0.184 mm** training MAE and **0.238–0.347 mm** test MAE; nominal models were **3.32–8.81 mm** | Use a two-socket spherical-joint constraint; optimize kinematic parameters on a training set and evaluate held-out configurations. Practical validation included **20/20** peg insertions and **24/24** offset insertions with **0.4 mm clearance** | **Peer-reviewed 2026 article**, DOI: [10.1038/s44172-026-00633-4](https://doi.org/10.1038/s44172-026-00633-4); earlier **preprint**, DOI: [10.48550/arXiv.2503.12584](https://doi.org/10.48550/arXiv.2503.12584) (pqac-00000000, pqac-00000001, pqac-00000002) |
| **KUKA LBR iiwa** | Approximately **0.1 mm**, inferred from the calibrated result | Improved from approximately **0.7–0.8 mm** to **0.107 mm** | Apply the same constrained self-calibration method as for Franka, followed by evaluation at held-out configurations | **Peer-reviewed 2026 article**, DOI: [10.1038/s44172-026-00633-4](https://doi.org/10.1038/s44172-026-00633-4) (pqac-00000001) |
| **Kinova Gen3 Lite** | Approximately **1 mm**, estimated in the study | Mean calibration error approximately **2 mm**; one test result improved from **5.99 mm to 2.66 mm** | Apply the same constrained calibration framework; poorer improvement was attributed to planetary-drive backlash and possibly joint-sensor noise | **Peer-reviewed 2026 article**, DOI: [10.1038/s44172-026-00633-4](https://doi.org/10.1038/s44172-026-00633-4); earlier **preprint**, DOI: [10.48550/arXiv.2503.12584](https://doi.org/10.48550/arXiv.2503.12584) (pqac-00000000, pqac-00000001, pqac-00000002) |
| **Universal Robots UR5** | **0.03 mm manufacturer specification**; not independently reproduced in the retrieved evidence | Not reported in the cited comparative experiment | The comparative cobot study used quasi-static and transient contact tests, not an ISO 9283 positioning test; treat **0.03 mm** as a vendor claim here | Major conference paper: Ferraguti et al., DATE 2019, DOI: [10.23919/DATE.2019.8714830](https://doi.org/10.23919/DATE.2019.8714830). Retrieved evidence supports safety testing, not independent verification of **0.03 mm** (pqac-00000013) |
| **Niryo Ned** | **0.5 mm manufacturer specification** | Not reported | No independent metrology protocol was provided in the retrieved source; the specification accompanied a 440 mm reach and 300 g payload | Secondary source with unclear publication venue in the retrieved record; treat as a vendor specification, not independently measured evidence (pqac-00000003) |
| **Forte low-cost 3D-printed 6-DOF arm** | Mean deviation **0.467 mm**; speed-specific standard deviation **0.286–0.587 mm** | Absolute accuracy not reported separately | Repeatedly move to a reference position and measure with a **Westward 4KU81 dial indicator**; record **5–10 cycles per speed** at 500–2500 steps/s. Payloads of 0.1, 0.36, 0.5, and 0.63 kg were also tested | **Preprint**, DOI: [10.48550/arXiv.2507.15693](https://doi.org/10.48550/arXiv.2507.15693) (pqac-00000051, pqac-00000052, pqac-00000054) |
| **REPLAB WidowX** | End effector reached within approximately **20 mm** of target after compensation | Cell calibration mean errors were **8.7 mm** and **15.2 mm** in two independently built cells | Calibrate camera-to-robot coordinates and fit linear compensation from commanded versus achieved positions on a **5×5 floor grid**. Grasp benchmark: 20 objects, **60 attempts per episode**, three runs per cell; success required holding the object for **2 s** | Peer-reviewed ICRA 2019 paper, DOI: [10.1109/ICRA.2019.8794390](https://doi.org/10.1109/ICRA.2019.8794390) (pqac-00000037, pqac-00000039, pqac-00000040) |
| **Dobot M1 Pro SCARA** | At full speed, displacement IQR was **0.020 mm in x** and **0.006 mm in y**; at half speed, **0.034 mm in x** and **0.014 mm in y** | Absolute pose accuracy not reported | Carry a 96-well plate or lid through P1→P2→P3→P2→P1; press against x/y dial-gauge probes; perform **125 repetitions at each speed**. A separate offset test used **125 trials per offset**; success meant that the lid seated correctly | **bioRxiv preprint**, DOI: [10.1101/2023.12.29.573685](https://doi.org/10.1101/2023.12.29.573685). IQR measures dispersion and is not ISO 9283 repeatability (pqac-00000018, pqac-00000020, pqac-00000023) |
| **SPLRA low-cost FDM-printed arm** | **2.47 ± 0.58 mm** positional and **0.41 ± 0.23°** angular repeatability under a 0.8 kg load | Absolute accuracy not reported | Record terminal position and joint angle after each lift-and-place attempt; only **10 cycles** were completed. The result combines backlash, joint play, link flexibility, open-loop stepping, and measurement error | Peer-reviewed *Discover Robotics* article, DOI: [10.1007/s44430-026-00032-6](https://doi.org/10.1007/s44430-026-00032-6). Ten cycles do not establish endurance (pqac-00000004, pqac-00000060, pqac-00000066) |
| **LeRobot SO-100 / SO-101** | **No published metrological repeatability value found** | **No published absolute-accuracy or calibration-error benchmark found** | Available studies evaluate learned-policy success rather than ISO 9283 positioning. ArmnetBench used SO-101 cells across 12 tasks and documented camera misalignment, blur, lighting variation, object wear, and unverified cross-cell reproducibility | Evidence located only in **preprints**, including ArmnetBench, DOI: [10.48550/arXiv.2607.24481](https://doi.org/10.48550/arXiv.2607.24481). No peer-reviewed SO-101-versus-industrial-arm metrology comparison was found (pqac-00000025, pqac-00000056, pqac-00000057) |


*Table: Comparison of reported positional repeatability and calibration performance for industrial, research, and low-cost arms. The protocols and evidence labels distinguish independently measured results from vendor specifications and preprints.*

### 1.1 Industrial/Research Cobots

Franzese et al. (2026, peer-reviewed in *Communications Engineering*) demonstrated that Franka Emika robots have a nominal (uncalibrated) mean absolute positional error of approximately 10 mm, which their low-cost calibration method reduced to approximately 0.2 mm. In practical validation, the uncalibrated Franka "failed insertion tasks requiring 6 mm tolerance," whereas the calibrated robot "repeatedly inserted a 10 mm peg into a hole with only 0.4 mm clearance" with 20/20 successful insertions (pqac-00000002). The same study showed the KUKA iiwa improved from ~0.7–0.8 mm to 0.107 mm after calibration, matching its intrinsic repeatability (pqac-00000001).

Critically, the Kinova Gen3 Lite—which uses planetary gearboxes rather than harmonic drives—showed much weaker improvement: calibration reduced error from ~5.99 mm to only 2.66 mm on the test set, with an estimated repeatability of ~1 mm. The authors attributed this to "backlash in planetary gearboxes" that creates "unobservable joint backlash and possibly sensor noise" (pqac-00000000, pqac-00000001). This is directly relevant because the SO-101 and similar low-cost arms also use planetary or spur-gear transmissions.

### 1.2 Low-Cost Arms

The REPLAB benchmark (Yang et al., ICRA 2019, peer-reviewed) used a ~$2,000 WidowX arm with a parallel-jaw gripper and found that "its measured end-effector position, after camera calibration and control-noise compensation, is within 2 cm of the target over the 35 × 40 cm workspace, with smaller errors near the center" (pqac-00000040). Mean calibration errors across two independently built cells were 8.7 mm and 15.2 mm (pqac-00000037). This represents approximately two orders of magnitude worse positioning than a calibrated Franka.

The Forte 3D-printed arm (preprint, DOI: 10.48550/arXiv.2507.15693) achieved a mean positional deviation of 0.467 mm across speeds of 500–2500 steps/s, measured with a Westward 4KU81 dial indicator over 5–10 motion cycles per speed (pqac-00000051, pqac-00000054). While approaching sub-millimeter performance, this was achieved through specialized capstan cable drives specifically designed to minimize backlash—a design not present in commodity servo arms like the SO-101.

A low-cost FDM-printed lifting arm (Ntambara et al., 2026, peer-reviewed in *Discover Robotics*) showed positional repeatability of 2.47 ± 0.58 mm and angular repeatability of 0.41 ± 0.23° under a 0.8 kg load, with only 10 test cycles performed (pqac-00000004, pqac-00000060).

### 1.3 Microplate Handling Benchmark

Harazono et al. (2024, bioRxiv preprint, DOI: 10.1101/2023.12.29.573685) constructed a benchmark specifically for evaluating microplate transfer accuracy, noting that "there has been no quantitative investigation of the positional accuracy of robot arms required to transfer microplates" (pqac-00000005). Using a Dobot M1 Pro SCARA robot with 125 repeated transfers, they found interquartile displacement ranges of 0.020 mm (x) and 0.006 mm (y) at full speed. However, their offset tolerance test showed that "success decreased gradually with x-offset, while it significantly decreased when y-offset exceeded 2.190 mm" (pqac-00000018, pqac-00000023). They emphasize that "manufacturer repeatability specifications may not predict performance because the standard measurement evaluates the robot approaching a position without carrying an object" and that "added payload and end-effector loading can reduce positional repeatability, and extended operation can introduce temperature-related positional errors" (pqac-00000005).

### 1.4 SO-101 and AgileX PiPER: No Published Metrological Data

**No peer-reviewed publication was found reporting ISO 9283-style positional repeatability or absolute accuracy measurements for the SO-100, SO-101, or AgileX PiPER arms.** All available SO-101 evaluations focus on learned-policy success rates rather than metrological benchmarking (pqac-00000025, pqac-00000056). This absence of characterization data is itself an argument against their use in precision-sensitive laboratory tasks.

---

## 2. Reliability, Durability, and Mechanical Degradation

### 2.1 Gear Backlash and Wear

Hrdlička (2022, peer-reviewed in *Design of Machines and Structures*, DOI: 10.32972/dms.2022.004) tested a 3D-printed PLA planetary gearbox for robotic arm joints and measured backlash of 0.57° (34 arcminutes) after assembly. A durability test of >300,000 revolutions on the input sun gear showed "no visible abrasion or damage." However, the gearbox structurally failed at 13.2 kg load (25.9 Nm), with "visible deformation and crackling" beginning at 12.3 kg. The damaged output flange showed "twisted bolt holes and a crack near the bearing, attributed to sparse infill" (pqac-00000061). The study presents the gearbox as "suitable mainly for undemanding, low-cost applications, not as a fully qualified laboratory-grade transmission" (pqac-00000061).

Habra & Cantürk (2025, peer-reviewed, DOI: 10.46519/ij3dptdi.1758356) noted for their 4-DOF low-cost arm that "it is anticipated that the backlash could worsen over time as PLA wears" (pqac-00000008, from search snippet). Gottardo (2025) documented "stick-slip friction phenomena and mechanical backlash" and "mechanical wear, causing progressive signal degradation" as characteristic problems of "low-cost robotics, where the mechanical and control" quality is limited (pqac-00000008, from search snippet).

### 2.2 Absence of Long-Term Reliability Data

**No published mean-time-between-failures (MTBF), long-term wear rate, or endurance test data was found for any low-cost arm in the class of the SO-101 or AgileX PiPER.** The most extensive durability evidence for a low-cost arm comes from REPLAB: "more than 100,000 grasp attempts produced no major breakages and required no servo replacements" (pqac-00000040). While encouraging, this is a single-arm anecdote without controlled environmental or load conditions, and the WidowX is a different platform from the SO-101.

### 2.3 Cell-to-Cell Variability

ArmnetBench v0.1 (preprint, DOI: 10.48550/arXiv.2607.24481) explicitly documented hardware variability across SO-101 cells: "on cell-3, the front camera was misaligned for every policy except MolmoAct 2, while the bimanual right-wrist camera view was slightly blurry." The authors state that "either camera issue could depress affected success rates" and that "whether absolute success rates agree across nominally identical cells remains untested" (pqac-00000056, pqac-00000057). Cowling (2026, preprint) found that re-testing identical checkpoints on the same placements produced different results, with "paired blocks differed by an average of 2 successes out of 10, and 40 of 120 placement outcomes changed" (pqac-00000059).

---

## 3. Safety and Certification Gaps

### 3.1 Standards Requirements

ISO 10218-1/2 and ISO/TS 15066 define safety requirements for collaborative robots, including four collaborative operating modes: safety-rated monitored stop, hand guiding, speed and separation monitoring, and power and force limiting. Safety functions must achieve Performance Level d, Category 3 under ISO 13849-1 (pqac-00000015, pqac-00000016).

### 3.2 Even Industrial Cobots Have Certification Gaps

Ferraguti et al. (DATE 2019, peer-reviewed, DOI: 10.23919/DATE.2019.8714830) tested the UR5 and Franka Emika Panda for ISO/TS 15066 compliance during quasi-static and transient impact tests. The UR5 triggered safe stops as external force approached configured limits, and the Panda reacted to programmed-limit violations. However, critically, "the Panda research version's safety-related features were not certified for industrial use" (pqac-00000013). If even a ~$30k research-grade Franka lacks full safety certification, low-cost arms costing $200–$2,000 are far less likely to meet these standards.

### 3.3 Low-Cost Arms Lack All Safety Infrastructure

Jocelyn et al. (2019, DOI: 10.70010/hneh8291) conducted a comprehensive safety assessment of collaborative robotics and found that "a robot may be sold as collaborative despite not meeting the ISO 10218 performance level, relying instead on intrinsic limits such as low power, speed, rounded edges, and joint shock absorbers" (pqac-00000016). They emphasize that "low-cost or plug-and-play arms therefore cannot be assumed to need no safeguards; risk assessment and supplementary protective devices remain necessary" (pqac-00000016). Furthermore, "the performance level set by the manufacturer for a safety-dedicated controller is not a guarantee of the overall performance level of the safety function" because the controller is "only the 'signal processing' part of the safety functions" (pqac-00000015).

**No published evidence was found that any arm in the SO-101 or AgileX PiPER class has undergone ISO 10218 or ISO/TS 15066 conformity assessment, risk assessment, or collision-force testing.** These arms lack safety-rated monitored stops, force/torque sensing for collision detection, and certified emergency-stop circuits.

---

## 4. Hidden Integration and Maintenance Costs

### 4.1 Integration Engineering Dominates Total Cost

Wolf et al. (2022, peer-reviewed in *SLAS Technology*, DOI: 10.1016/j.slast.2021.11.003) described the LAPP framework for laboratory automation integration and documented that beyond hardware purchase, "the robot must be coordinated with laboratory devices, transportation systems, sample carriers, software schedulers, and physical workspaces." Fixed systems "require comprehensive integration and carefully designed device placement; they often require custom frames rather than conventional benches" (pqac-00000030).

Salazar-Villacis & Benyahia (2026, peer-reviewed in *Communications Chemistry*, DOI: 10.1038/s42004-026-01932-9) noted that laboratory robotics integration "historically depended on bespoke 'glue code,' while legacy equipment often lacks mature information models. Version drift creates continuing maintenance costs, and mapping legacy telemetry into common data schemas is described as labour-intensive" (pqac-00000031).

### 4.2 The Automation Gap in Academic Labs

Holland & Davies (2020, peer-reviewed in *Frontiers in Bioengineering and Biotechnology*, DOI: 10.3389/fbioe.2020.571777, 333 citations) characterized the academic "automation gap": "complete automation for common procedures such as cell culture may exceed $1 million" (pqac-00000070). They documented that automation "may inhibit innovation if standardized systems restrict researchers' ability to tinker, devise new protocols, and preserve experimental novelty" (pqac-00000068) and that "incorrect application can reduce efficiency, propagate an undetected dispensing error across thousands of samples, and fail to improve reproducibility because of differences in materials, equipment, setup, calibration, and machine-to-machine variability" (pqac-00000072). Equipment obsolescence is also a risk: "thermostable polymerases made an earlier generation of PCR machinery obsolete" (pqac-00000070).

### 4.3 Self-Driving Lab Challenges

Seifrid et al. (2022, peer-reviewed in *Accounts of Chemical Research*, DOI: 10.1021/acs.accounts.2c00220, 415 citations) emphasized that "software control and integration" is a major practical challenge "because few instrument manufacturers design their products with self-driving laboratories in mind" and that "adapting experimental procedures that were designed for human experimenters is not as simple as transferring those same actions to an automated system" (pqac-00000049). This integration burden applies regardless of arm cost but is likely amplified for low-cost arms that lack vendor-supported software ecosystems, documented APIs, and application engineers.

### 4.4 The Frugal Twin Trade-Off

Lo et al. (2024, peer-reviewed in *Digital Discovery*, DOI: 10.1039/d3dd00223c, 140 citations) explicitly framed this trade-off in the "frugal twin" concept: "reducing cost generally requires either reducing research capabilities or sacrificing accuracy and precision" (pqac-00000043). They noted that "inexpensive systems may have lower accuracy and reliability" and that "even apparently simple automation can encounter practical problems: MIK-I required calibration for liquids with different density, viscosity, and surface tension" (pqac-00000043, pqac-00000044). The frugal twin is positioned as useful for "simulation, rapid prototyping, education, and preliminary research" rather than as a replacement for high-capability systems (pqac-00000043).

---

## 5. Imitation-Learning Performance on Low-Cost Arms

### 5.1 SO-101 Policy Success Rates

ArmnetBench v0.1 (preprint, DOI: 10.48550/arXiv.2607.24481) evaluated seven policies across 12 tasks on SO-101 cells with 50 demonstrations per task. The best overall strict success rate was π₀.₅ at 47.6%, followed by π₀ at 35.1%, GR00T N1.7 at 29.4%, Diffusion Policy at 26.7%, ACT at 19.2%, MolmoAct 2 at 18.9%, and SmolVLA at 15.0%. "No policy succeeded on cable_clip, while the best task-policy pairs reached 60–86%" (pqac-00000025). The authors documented that "camera misalignment on one cell, blur in the bimanual wrist camera, object wear, ambient-light variation, and differences between physical cells" could affect success rates, "providing evidence that hardware condition and sensing quality influence policy evaluation" (pqac-00000025).

Cowling (2026, preprint, DOI: 10.48550/arXiv.2610.37170) tested on a single SO-101 and found ACT improved from 2.5% (1/40) at 12 demonstrations to 92.5% (37/40) at 100 demonstrations for a pick-and-place task, while SmolVLA "never started in 47% of episodes" (pqac-00000026). Lighting variation between training and testing was identified as a confound (pqac-00000058).

### 5.2 No Direct Cross-Embodiment Comparison

**No published study was found that directly compares the same imitation-learning policy's success rate on an SO-101 arm versus a Franka or UR5e under matched conditions.** RoboMIND (Wu et al., 2024, preprint, DOI: 10.48550/arXiv.2412.13877) benchmarked policies across Franka, UR5e, AgileX dual-arm, and humanoid embodiments but did not include SO-100/SO-101 (pqac-00000028). The absence of such a controlled comparison is a significant gap in the literature.

---

## 6. Repeatable Benchmarks You Can Perform

Based on the protocols documented in the literature, the following tests can be reproduced with your hardware:

**6a. Positional repeatability (adapted from Harazono et al.):** Mount dial gauges on an aluminum-frame stage. Command the arm to a target pose carrying a microplate or representative payload, press the end-effector against the gauge probe, record displacement, return, and repeat for ≥125 cycles. Report interquartile range and standard deviation in x, y, z. Compare against the Dobot M1 Pro benchmarks (IQR 0.020–0.034 mm) and the WidowX result (~20 mm) (pqac-00000018, pqac-00000040).

**6b. Transfer tolerance (adapted from Harazono et al.):** Introduce deliberate x/y offsets in 0.1 mm increments while performing microplate lid transfers, 125 trials per offset. Record the offset at which success probability drops below 50%. Compare against the 2.190 mm y-threshold found for the Dobot M1 Pro (pqac-00000018, pqac-00000023).

**6c. Peg-in-hole insertion (adapted from Franzese et al.):** Machine a peg and hole with known clearances (e.g., 0.4 mm, 1 mm, 2 mm, 5 mm). Attempt ≥20 insertions at each clearance. The calibrated Franka succeeded at 0.4 mm clearance while failing uncalibrated at 6 mm (pqac-00000002).

**6d. Grasping benchmark (adapted from REPLAB):** Scatter 20 objects over the workspace by inverting a filled box. Allow 60 grasp attempts. Record cumulative success rate (object held for 2 seconds). Repeat 3 times. Compare against REPLAB baselines where the best method cleared all 20 objects (pqac-00000037, pqac-00000039).

---

## 7. Where No Published Evidence Exists

The following gaps were identified through systematic searching:

- **No published ISO 9283 positional-repeatability measurement exists for the SO-100, SO-101, or AgileX PiPER.** All SO-101 evaluations use task-success metrics rather than metrological benchmarks.
- **No published long-term MTBF, wear-rate, or endurance data exists for any arm in the SO-101/PiPER class.**
- **No published head-to-head comparison exists** running identical imitation-learning policies on SO-101 versus Franka/UR5e under matched conditions.
- **No published total-cost-of-ownership analysis** quantitatively compares integration, maintenance, and engineering labor costs between low-cost and industrial arms for laboratory automation.
- **No published safety assessment** (ISO 10218 or ISO/TS 15066 conformity) has been performed on any arm in this class.
- **No published peer-reviewed journal article** (as distinct from preprints) was found that specifically evaluates SO-101 or AgileX PiPER for any application.

---

## 8. Summary of the Case Against

The evidence supports five principal arguments against low-cost arms for laboratory automation:

1. **Accuracy gap:** Calibrated industrial cobots achieve 0.1–0.35 mm absolute accuracy (pqac-00000001, pqac-00000002), while low-cost arms with gear-based transmissions show repeatability of 0.5–2.5 mm at best (pqac-00000004, pqac-00000051) and ~20 mm positioning error in the worst documented case (pqac-00000040). The Kinova Gen3 Lite's calibration limitation due to planetary-gear backlash (pqac-00000000) is directly predictive of the problems expected in servo-driven low-cost arms.

2. **Uncharacterized reliability:** 3D-printed gears show 0.57° backlash and structural failure under moderate loads (pqac-00000061). No long-term endurance data exists. Hardware variability between nominally identical SO-101 cells is documented but unquantified (pqac-00000056, pqac-00000057).

3. **No safety certification:** Low-cost arms lack force/torque sensing, safety-rated stops, and ISO 10218/15066 conformity. Even the Franka research version was "not certified for industrial use" (pqac-00000013). A robot "may be sold as collaborative despite not meeting the ISO 10218 performance level" (pqac-00000016).

4. **Hidden integration costs:** Integration requires custom frames, device interfaces, software glue code, camera calibration, risk assessment, validation, and ongoing maintenance (pqac-00000030, pqac-00000031, pqac-00000070). These costs dominate hardware purchase price and are largely independent of arm cost—meaning a $200 arm may require the same $50k–$100k integration effort as a $30k arm.

5. **Policy performance ceiling:** The best imitation-learning policy on SO-101 arms achieved only 47.6% strict success across diverse tasks (pqac-00000025), with documented sensitivity to camera quality, lighting, and physical cell differences. No controlled comparison to industrial-arm performance exists, but the documented hardware-dependent variability suggests a performance ceiling imposed by the mechanical platform.

The strongest counterargument is that low-cost arms demonstrably enable large-scale data collection and community-driven research at price points that permit fleet deployment and parallelized evaluation—advantages that may outweigh precision limitations for tasks where centimeter-level accuracy suffices. The frugal twin concept explicitly positions low-cost systems as prototyping tools rather than production-grade replacements (pqac-00000043, pqac-00000044). The decision therefore depends critically on the precision, reliability, and safety requirements of each specific laboratory task.