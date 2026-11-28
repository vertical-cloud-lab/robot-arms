Question: We have a low-cost AgileX PiPER 6-DOF arm (about $2k) and SO-101 leader/follower arms (about $200), with parallel grippers, Raspberry Pi wrist cameras and fixed cameras in an enclosure, AprilTags, and LeRobot-style imitation learning or scripted motion. We want to place these arms in the published literature and compare them with industrial and research arms (e.g. UR5e, Franka, ABB YuMi, Kinova) using tests we can repeat ourselves.

Lab workflows like ours: What published work has robot arms swapping modules or tools on lab instruments (vial carriers on a pipetting gantry, augers or hoppers on a powder doser, tool changers), and what positioning tolerance did the task need? How accurate was localization with AprilTags or wrist cameras, and what success rates were reported?

Prioritize peer-reviewed journal articles and major conference papers from 2015 to 2026, and flag any preprints. For each benchmark or result, describe the protocol in enough detail to repeat it (what is measured, number of trials, success criterion, measuring tool) and give the arm model. For each claim, give the DOI and quote the sentence that supports it. Say explicitly where no published evidence exists.


## Robot Arms in Laboratory Automation: Module/Tool Swapping, Positioning Tolerances, Fiducial-Based Localization, and Repeatable Benchmarks

This report synthesizes peer-reviewed journal articles, major conference papers, and flagged preprints from 2015–2026 that address robot arms swapping modules or tools on laboratory instruments, the positioning tolerances those tasks require, the accuracy of AprilTag or wrist-camera localization, and the success rates reported. Where no published evidence exists for a specific claim or arm, this is stated explicitly.

The following table provides a consolidated comparison of arms, tasks, tolerances, and success rates drawn from the literature surveyed.

| Arm model | Approx. cost tier | Published repeatability | Laboratory task | Required or achieved tolerance | Reported success | Trials and success criterion | DOI / evidence |
|---|---:|---:|---|---|---:|---|---|
| **Universal Robots UR5e** | Industrial cobot; about $30k–$50k configured | Not numerically reported in the retrieved laboratory-task passages | Imitation-learning tasks including flexible-object placement, chain insertion, and ring placement; a 2026 preprint also includes vial transfer, rack loading, cuvette transfer, and pipette operations | No UR5e-specific geometric tolerance reported for these experiments | ACT mean **43.8%** and Diffusion Policy mean **47.9%** over eight tasks; a **2026 preprint** reports 100% for its vial-transfer method but does not uniquely associate that task with one listed arm configuration | RoboManipBaselines reports binary task success, but the retrieved passage omits evaluation count and detailed pass criteria. The vial-transfer preprint varies object and initial arm poses but omits the evaluation count | [10.1109/access.2026.3691054](https://doi.org/10.1109/access.2026.3691054) (murooka2026robomanipbaselinesaunified pages 7-8); **preprint:** [10.48550/arxiv.2609.04355](https://doi.org/10.48550/arxiv.2609.04355) (su2026vlaprecisionasymmetriccobootstrapping pages 9-10) |
| **Franka Emika Panda / Franka Research 3** | Research cobot; about $25k–$40k configured | Not reported in the retrieved task passages; one contact-rich study states Cartesian impedance-controller translation error up to **2 mm** | FMB grasp–reorient–insert and assembly; autonomous powder scraping inside vials; tactile peg-in-hole assembly | FMB mating tolerance **1–2 mm**; tactile assembly controller error up to **2 mm** | No directly comparable laboratory-workflow success rate with a complete trial count was recovered | FMB used 3D-printed objects and a Franka arm: 50 grasp trajectories per object, **2,700** trajectories for 54 objects, **1,800** additional grasp trajectories, and **125 human demonstrations** for assembly; the retrieved passage omits evaluation-trial count | [10.1177/02783649241276017](https://doi.org/10.1177/02783649241276017) (luo2025fmbafunctional pages 3-5); **preprint:** [10.48550/arxiv.2506.22766](https://doi.org/10.48550/arxiv.2506.22766) (chen2025robustpeginholeassembly pages 9-10) |
| **ABB YuMi IRB 14000** | Dual-arm industrial/research cobot; about $40k–$80k+ | No formal repeatability value reported in the retrieved lab papers; one vial implementation observed **2–6 mm** positioning deviation | Vial picking, uncapping, and inversion; PXRD preparation; biomimetic powder dispensing; Drosophila vial/assay workflow; cable-loop vial grasping | Observed vial-picking deviation **2–6 mm**, judged inadequate for the intended operation; PXRD work did not publish a numerical YuMi placement tolerance | Solid dispensing: mean failure **23.1%**, implying **76.9%** non-failure; cable-loop gripper: **99.2%** successful vial manipulations; **2026 bioRxiv preprint:** 93.85% fly retention and 1.1% arena-loading error | Solid-dispensing trial count was not stated; failure meant mechanical failure, deliquescence, or robot error. Cable gripper: **1,000 vial manipulations**, 0.8% grasp failure, no transport loss; also nine vials × five repetitions, all grasped. STELA: 19 cycles, including 16 unattended cycles and 1,024 assays | [10.1039/D3DD00075C](https://doi.org/10.1039/D3DD00075C) (jiang2023autonomousbiomimeticsolid pages 10-11); [10.1038/s41598-024-59372-1](https://doi.org/10.1038/s41598-024-59372-1) (manes2024asoftcable pages 6-7); [10.1007/978-3-032-22823-9_36](https://doi.org/10.1007/978-3-032-22823-9_36) (rosas2026implementationofa pages 18-20); **preprint:** [10.64898/2026.10.20.758951](https://doi.org/10.64898/2026.10.20.758951) (manna2026endtoendautomationof pages 11-14, manna2026endtoendautomationof pages 14-17, manna2026endtoendautomationof pages 9-11, manna2026endtoendautomationof pages 3-5) |
| **KUKA LBR iiwa on KMR mobile base** | Premium mobile manipulator; about $100k+ system | Published arm repeatability **0.1 mm**; six-point station calibration located a cube within **0.12 mm**, with orientation residual below **0.005°** | GC-vial and rack manipulation, instrument calibration, autonomous workflows, and LIRA rack/PXRD-plate verification | Six-point tactile calibration achieved **0.12 mm** position and less than **0.005°** orientation error; LIRA reports comparable vision localization but the retrieved passage omits its numerical localization error | LIRA placement inspection **97.5%** over 200 deliberately erroneous placements; overall error-inspection rate **97.9%**; no numerical vial-transfer success rate | Six-point calibration: **100 tests** with simulated start-pose noise. LIRA: **200** manual placement-error tests; correct error detection was success, with five failures. Visual calibration took about 5 s versus about 53 s for tactile calibration | Dissertation: [10.17638/03087073](https://doi.org/10.17638/03087073) (burger2023amobilerobotic pages 52-56); [10.1038/s42004-025-01770-1](https://doi.org/10.1038/s42004-025-01770-1) (zhou2025localizationinspectionand pages 2-3, zhou2025localizationinspectionand pages 7-8) |
| **Mobile manipulator used for GC injection** | Premium/custom research system | Arm repeatability not reported in the retrieved passage | Vision-servoed syringe insertion into a Varian 450 gas chromatograph | Needle tip had to finish within **1.50 mm planar error** of the target | Proposed visual-servo method **100%**; AprilTag-only 2160p baseline **9.52%**; AprilTag-only 1080p baseline **4.76%** | **63 total trials: 21 per method**. Success was final XY needle-tip error no greater than 1.50 mm. Base pose, distance, and syringe grasp pose were perturbed; the needle detector was separately tested on 286 images | [10.1109/IROS55552.2023.10341743](https://doi.org/10.1109/IROS55552.2023.10341743) (angelopoulos2023highaccuracyinjectionusing pages 4-6, angelopoulos2026autonomoussciencelaboratoriesa pages 43-47, angelopoulos2023highaccuracyinjectionusing pages 7-8, angelopoulos2026autonomoussciencelaboratoriesa pages 34-38) |
| **Yaskawa SDA10F** | Dual-arm industrial robot; about $75k–$150k+ | **±0.1 mm** | Pipetting, vial handling, labware transport, sample preparation, and transfer into GC/LC autosamplers | No task-specific Cartesian tolerance reported in the retrieved article passage | No aggregate success percentage reported | Related dissertation testing reports **19** chiral-compound runs and **36** cholesterol runs, each containing hundreds to over 1,000 subtasks. Failures were catalogued by subtask, including tip loading, vial pickup, cap placement, pipetting, and plate transfer, but no aggregate numerator/denominator was provided | [10.1177/2211068216637352](https://doi.org/10.1177/2211068216637352) (fleischer2016applicationofa pages 3-5); dissertation: [10.18453/rosdok_id00002364](https://doi.org/10.18453/rosdok_id00002364) (chu2016automationstrategiesfor pages 121-126) |
| **UFactory xArm 5** | Lower-cost research/light-industrial arm; about $5k–$10k configured | **±0.1 mm** stated repeatability | Open-source liquid handler with Wingman tool changer; interchangeable gripper, syringe/fluidics tool, and proposed pipettes; camera-guided HPLC-vial localization | Iterative RGB-D centering continued until calculated offset was **less than 1 mm**; depth-distance accuracy stated as 1% | No physical vial-transfer or tool-change success rate reported; mAP values of 0.979 and 0.995 are detector metrics, not manipulation success | Physical tool-change/vial trial counts and pass/fail criteria were not reported in the retrieved thesis passage. Each vial position was individually visited and calibrated; tool offsets were measured manually | Publication DOI unavailable in the retrieved record (maroulis2026automationsystemsfor pages 28-33, maroulis2026automationsystemsfora pages 28-33, maroulis2026automationsystemsfor pages 33-37) |
| **AgileX PiPER** | Low-cost arm; about $2k | **No independent peer-reviewed repeatability or task-accuracy result located** | No peer-reviewed 2015–2026 study located for laboratory tool/module exchange, vial insertion, powder-doser component exchange, or comparable instrument tending | **No published task-specific evidence located** | **No published laboratory-task success rate located** | No repeatable published protocol or trial series located; local testing should therefore report metrology and task outcomes rather than relying solely on vendor specifications | No qualifying DOI located in the searched evidence |
| **LeRobot SO-101 leader/follower** | Ultra-low-cost pair; about $200–$500 depending on build | **No independent peer-reviewed Cartesian repeatability or absolute-accuracy result located** | LeRobot-style teleoperation and imitation learning appear in 2025–2026 work, but no peer-reviewed laboratory module/tool-swapping or instrument-tending evaluation with SO-101 was located | **No published laboratory-task tolerance located** | **No peer-reviewed laboratory-workflow success rate located** | No qualifying physical laboratory-task trial series located. Results from UR5e, Franka, or generic LeRobot platforms cannot be transferred directly because compliance, backlash, cameras, grippers, and kinematics differ | **Preprint examples only:** [10.48550/arxiv.2509.14349](https://doi.org/10.48550/arxiv.2509.14349) and [10.48550/arxiv.2603.20129](https://doi.org/10.48550/arxiv.2603.20129); no direct qualifying SO-101 laboratory benchmark |


*Table: Comparison of published laboratory tasks, positioning performance, success rates, and repeatable protocols across industrial, research, and low-cost arms. Missing entries explicitly identify where the retrieved literature provides no task-level evidence.*

---

### 1. Robot Arms Swapping Modules or Tools on Lab Instruments

#### 1.1 ABB YuMi in Multi-Robot PXRD Workflow (Peer-Reviewed)

Lunt et al. (2024) describe a 12-step autonomous solid-state workflow for powder X-ray diffraction (PXRD) using a team of three robots, including a dual-arm ABB YuMi IRB 14000. The YuMi performed vial transfer from a transport rack to a grinding station, unscrewed vial caps, inverted caps for powder transfer, and placed prepared samples into a PXRD plate. A mobile robot (KUKA KMR iiwa) transported racks between stations, and a six-point calibration procedure using calibration cubes improved arm precision at each modular station. The mobile robot's positioning precision was measured as ±10 mm, with orientation precision less than ±2.5° (lunt2024aroboticworkflow pages 49-57). The SmartGripper force had to be reduced from 20 N to 10 N because "the original 20 N setting caused the fingers to bend and eventually snap" (lunt2024aroboticworkflow pages 87-95). **DOI: 10.1039/D3SC06206F**

**Protocol detail:** The workflow involved crystal growth, sample preparation, and automated data capture across 12 steps. No aggregate vial-handling success rate or explicit trial count was reported in the retrieved passages. The tolerance required for vial-to-rack insertion was not numerically specified but demanded repeatable cap removal and inversion with the dual-arm system.

#### 1.2 ABB YuMi for Biomimetic Solid Dispensing (Peer-Reviewed)

Jiang et al. (2023) used an ABB YuMi to autonomously dispense solid powders in a biomimetic (human-like) workflow. They reported dispensing failure rates per material: 0% for nine solids (Al₂O₃, NaNO₂, pectin, sand, granulated sugar, LiOH·H₂O, SiC, activated carbon, molecular sieve), 0.8% for Na₂SO₃, and 100% for three deliquescent/problematic solids (CaCO₃, CH₃COOK, NH₄CH₃CO₂). The average failure rate across all solids was 23.1%, implying a 76.9% overall dispensing success rate. Failure categories included "mechanical failure, solid deliquescing, or robot reporting error" (jiang2023autonomousbiomimeticsolid pages 10-11). The number of dispensing trials per material was not stated in the retrieved passage. **DOI: 10.1039/D3DD00075C**

#### 1.3 Soft Cable-Loop Gripper on ABB YuMi (Peer-Reviewed)

Manes et al. (2024) developed a soft cable-loop gripper for chemistry automation and tested it in a reliability experiment involving 1,000 vial manipulations. The prototype achieved a 0.8% failure rate (99.2% success); "failures occurred during grasping, and no vial was lost during transport." A separate sorting test used nine vials repeated five times, with the gripper successfully grasping all vials in each repetition (manes2024asoftcable pages 6-7). **DOI: 10.1038/s41598-024-59372-1**

**Protocol:** Success was defined as a completed grasp-transport-release cycle without dropping the vial. The measuring tool was visual observation of grasp completion.

#### 1.4 STELA: ABB YuMi for Drosophila Behavioural Experiments (Preprint — bioRxiv)

Manna et al. (2026, **preprint**) describe STELA, an end-to-end robotic cell built around a dual-arm ABB YuMi IRB 14000 that autonomously runs Drosophila behavioural experiments, including "manipulation of fly culture vials, CO₂ fly anaesthesia, vision-guided sex classification, single live fly manipulation, and loading and disassembly of a behaviour assay." In a 24-hour unattended run, the system completed 16 experiments comprising 1,024 individual visual learning assays. Retention of flies fit for analysis was 93.85% for the robot versus 83.33% for a human operator, with a 12-fold improvement in handling consistency and a 1.1% arena-loading error rate (manna2026endtoendautomationof pages 1-1, manna2026endtoendautomationof pages 11-14, manna2026endtoendautomationof pages 14-17). **DOI: 10.64898/2026.10.20.758951**

#### 1.5 Tool Changer on UFactory xArm 5 (Thesis/Unpublished)

Maroulis (2026) describes a UFactory xArm 5 equipped with a TripleA Robotics Wingman tool changer for interchangeable end-effectors including a syringe-pump/fluidic-line tool, gripper, and proposed single- or multichannel autopipettes. The arm's stated repeatability is ±0.1 mm, and camera-guided vial centering continued until the calculated positional offset was "less than 1 mm" (maroulis2026automationsystemsfor pages 28-33, maroulis2026automationsystemsfor pages 33-37). However, no physical tool-change success rate or trial count was reported in the retrieved passages.

#### 1.6 Explicit Gap: No Published Module-Swap Data for AgileX PiPER or SO-101

No peer-reviewed publication or major conference paper from 2015–2026 was located that reports the AgileX PiPER 6-DOF arm or LeRobot SO-101 leader/follower arms performing laboratory module swapping, tool changing, vial carrier exchange on a pipetting gantry, or auger/hopper exchange on a powder doser. These arms appear in imitation-learning preprints for tabletop manipulation, but not in laboratory-instrument-tending contexts.

---

### 2. Positioning Tolerances Required by Laboratory Tasks

The literature reveals a range of positioning requirements:

- **Sub-millimeter (<1 mm):** Camera-guided vial centering for a liquid handler required "less than 1 mm" offset before recording coordinates (maroulis2026automationsystemsfor pages 33-37, maroulis2026automationsystemsfora pages 33-37).
- **≤1.5 mm:** GC syringe injection required the needle tip to finish within 1.50 mm planar error of the target port (angelopoulos2023highaccuracyinjectionusing pages 4-6, angelopoulos2026autonomoussciencelaboratoriesa pages 34-38).
- **1–2 mm:** The Functional Manipulation Benchmark (FMB) uses 3D-printed objects with "tolerance for mating all objects is between 1 mm and 2 mm" (luo2025fmbafunctional pages 3-5).
- **2–6 mm:** An ABB YuMi performing camera-guided vial picking exhibited 2–6 mm observed deviation, which the authors judged inadequate, noting the "manipulation accuracy did not meet the standards required for laboratory operations" (rosas2026implementationofa pages 18-20).
- **±10 mm:** A mobile robot base achieved ±10 mm positioning precision and <±2.5° orientation precision before arm-level calibration refined the final approach (lunt2024aroboticworkflow pages 49-57).

The ADePT framework for assessing autonomous laboratory robotics (Salazar-Villacis and Benyahia, 2026) identifies "sub-millimetre alignment for well-plate and vial insertion" and "milligram-level weighing accuracy" as key dexterity benchmarks, though numerical thresholds are deferred to supplementary materials (salazarvillacis2026theadeptframework pages 5-6). **DOI: 10.1038/s42004-026-01932-9**

---

### 3. AprilTag and Wrist-Camera Localization Accuracy

#### 3.1 AprilTag Pose Estimation for Industrial Manipulators (Conference Paper)

Nissler et al. (2016) evaluated AprilTag-based global pose estimation for an industrial robot in a 4.5 m × 4.5 m workspace. Raw single-marker detection yielded "an average error of approximately 15 mm" (nissler2016evaluationandimprovement pages 3-4). After particle filtering, "the translational errors were below 10 mm and the rotational errors were below 0.5 degrees" (nissler2016evaluationandimprovement pages 4-5). RANSAC-based multi-marker fusion reduced the total average translational error to approximately 8–10 mm over 28 measurement shots across three motion profiles (horizontal semicircle: 9 shots; vertical semicircle: 6 shots; linear: 13 shots) (nissler2016evaluationandimprovement pages 5-7). The initial raw error was 15–35 mm relative to a Leica AT901 laser-tracker ground truth (nissler2016evaluationandimprovement pages 1-2). **DOI: 10.1109/ETFA.2016.7733711**

**Protocol:** Three motion profiles were executed multiple times. Translational error was the Euclidean norm of the error translation vector; rotational error was the absolute axis-angle rotation. Ground truth was provided by a Leica AT901 laser tracker.

#### 3.2 Dual-Camera AprilTag Fusion for Robotic Assembly (Peer-Reviewed)

Wilcock and Iuorio (2026) fused a global RGB-D camera with an eye-in-hand camera using AprilTag markers on a KUKA iiwa manipulator. The hand camera showed a mean translational distance bias of +14 mm, while the global camera showed +69 mm. After inverse-variance fusion and temporal filtering, the mean position error was reduced to 1.02 mm (wilcock2026fusionoffiducial pages 18-18). **DOI: 10.1007/s41693-026-00183-3**

#### 3.3 AprilTag-Based Rover Arm Characterization (Conference Paper)

Franchini et al. (2023) used AprilTag fiducial markers and TagSLAM to characterize a 4-DOF rover arm. Overall positioning accuracy was 50 mm (0.050 m), with lateral accuracy better than 42 mm. Repeatability was better than 11 mm across five workspace points, each reached 10 times. Orientation accuracy was 0.061 rad (~3.5°), with angular repeatability of 0.004–0.006 rad (franchini2023mechatronicdesignand pages 6-7, franchini2023mechatronicdesignand pages 7-7). **DOI: 10.1109/MetroAeroSpace57412.2023.10190044**

#### 3.4 AprilTag Localization Is Insufficient Alone for Sub-mm Tasks

Angelopoulos et al. (2023) demonstrated that AprilTag-only localization for GC syringe injection achieved only 9.52% success (AT 2160p) and 4.76% success (AT 1080p) when the requirement was ≤1.50 mm needle-tip error. Their deep-learning visual-servoing approach achieved 100% success over 21 trials, being "11.44 times more accurate than AT 2160p and 12.35 times more accurate than AT 1080p" (angelopoulos2023highaccuracyinjectionusing pages 4-6, angelopoulos2026autonomoussciencelaboratoriesa pages 43-47). **DOI: 10.1109/IROS55552.2023.10341743**

**Protocol:** 63 total trials (21 per method). Success criterion: final XY needle-tip error ≤1.50 mm from the injection port center. Uncertainty was introduced in mobile-base yaw, robot distance, and syringe grasp position/orientation.

#### 3.5 LIRA Vision-Language Module for Self-Driving Labs (Peer-Reviewed)

Zhou et al. (2025) introduced LIRA, which uses ArUco fiducial markers and vision-language models for localization and error inspection. LIRA achieved "high localization accuracy, a tenfold reduction in localization time" compared with tactile calibration (~5 s vs. ~53 s per calibration), an overall error-inspection success rate of 97.9%, and a placement verification accuracy of 97.5% over 200 deliberately erroneous placements (five failures: two PXRD plates, three NMR racks) (zhou2025localizationinspectionand pages 2-3, zhou2025localizationinspectionand pages 7-8). The LIRA-enhanced workflow reduced total arm-manipulation time by 36.1%. **DOI: 10.1038/s42004-025-01770-1**

---

### 4. Vial Insertion Success Rates with Multimodal Sensing (Conference Paper)

Butterworth et al. (2023) specifically addressed robotic vial insertion in R&D chemistry laboratories. A vision-only baseline using classic computer vision and a CNN discriminator achieved a 48.78% vial-insertion success rate. Adding force and vision feedback increased this to 89.55%. The authors characterize prior workflows as open-loop, requiring "all equipment being used by the robot to be in well defined known locations" (butterworth2023leveragingmultimodalsensing pages 1-2). The robot model was not explicitly named in the retrieved passages. **DOI: 10.48550/arxiv.2307.00671** (CASE 2023 conference paper)

**Protocol:** The task involved picking a vial from a rack and inserting it into a target rack. Feedback modalities included a wrist camera, intrinsic end-effector force sensors, and camera-based tactile sensors. The number of trials per condition and the formal success criterion were not stated in the retrieved excerpt.

---

### 5. Repeatable Benchmarks Accessible to Low-Cost Arms

#### 5.1 Functional Manipulation Benchmark (FMB) (Peer-Reviewed)

Luo et al. (2024) propose FMB, consisting of 3D-printed objects with "tolerance for mating all objects is between 1 mm and 2 mm." Tasks include grasping, repositioning, insertion, and multi-stage assembly. Data collection used a Franka robot with 2,700 functional-grasping trajectories (50 per object across 54 objects), 1,800 additional trajectories, and 125 human demonstrations for assembly tasks (luo2025fmbafunctional pages 3-5). FMB is designed to be "easily replicable, encompassing all essential hardware and software components." All object CAD files, code, and datasets are publicly available. **DOI: 10.1177/02783649241276017**

**Repeatability for your lab:** 3D-print the FMB objects, mount them on a board, and measure grasp success, reorientation accuracy, and insertion success over N trials (N ≥ 50 recommended). The 1–2 mm insertion tolerance directly tests whether your arm's combined positioning + gripper accuracy is sufficient for laboratory vial/module insertion tasks.

#### 5.2 NIST Assembly Task Board (Conference Paper)

Kimble et al. (2020) present task boards with peg-in-hole and connector insertions. The selected subset includes four round pegs (4, 8, 12, 16 mm diameter), four rectangular pegs (4×4, 8×7, 12×8, 16×10 mm), and USB, RJ45, waterproof, and DSUB connectors. The nest "permits deviations from the nominal grasp pose of approximately ±3 mm in translation and ±5° in orientation" (lian2021benchmarkingofftheshelfsolutions pages 2-3). Benchmarking protocols and 3D-printable designs are publicly available. **DOI: 10.1109/LRA.2020.2965869**

#### 5.3 RAMP Benchmark (Peer-Reviewed)

Collins et al. (2024) introduce RAMP, an assembly benchmark using 3D-printed beams and pegs with AprilTag fixtures. Parts are "either 3D printed or otherwise constructed from materials that are readily obtainable." The benchmark incorporates AprilTag markers to enable researchers to focus on individual sub-tasks. A digital twin and baselines are provided. **DOI: 10.1109/LRA.2023.3330611**

#### 5.4 Box and Blocks Test (Peer-Reviewed)

Morgan et al. (2020) adapted the clinical Box and Blocks Test for robot benchmarking, providing three protocols (Modified-BBT, Targeted-BBT, Standard-BBT) on a Franka Emika Panda and a Barrett WAM. The BBT setup is part of the widely distributed YCB Object and Model Set, making it accessible and inexpensive to replicate. **DOI: 10.1109/LRA.2019.2961053**

---

### 6. Imitation Learning with Low-Cost and Research Arms

#### 6.1 ACT and Diffusion Policy on UR5e (Peer-Reviewed)

Murooka et al. (2026) report real-world imitation-learning results using a UR5e. Eight tasks were evaluated, with ACT averaging 43.8% (±38%) and Diffusion Policy averaging 47.9% (±32%) success. Tasks included folding, bag placement, chain insertion, and ring placement (murooka2026robomanipbaselinesaunified pages 7-8). The retrieved passage did not state the number of demonstrations or the number of evaluation trials per task. **DOI: 10.1109/access.2026.3691054**

#### 6.2 VLA-Precision on UR5e for Chemistry Tasks (Preprint)

Su et al. (2026, **preprint**) report results on chemistry-manipulation tasks including 2 mL Vial Transfer, Tube Rack Loading, Cuvette Transfer, Pipette Tip Attachment, and Pipette Transfer and Ejection using UR5e platforms with parallel grippers. Their VLA-Precision method achieved 100% on vial transfer, compared with 80% for π₀ and 5% for baseline methods, after 34 minutes of training (su2026vlaprecisionasymmetriccobootstrapping pages 9-10). Object and initial arm poses were varied, but the number of evaluation trials was not stated. **DOI: 10.48550/arxiv.2609.04355**

#### 6.3 LeRobot and SO-101 in Published Work

Several 2025–2026 preprints reference LeRobot-compatible platforms. EasyMimic (Zhang et al., ICRA 2026) demonstrates imitation learning "on a low-cost LeRobot platform" using 20 robot teleoperation trajectories. KUKAloha (Xu et al., 2026, **preprint**) adapts "the open-source LeRobot SO101 leader designs" for construction tasks. However, no peer-reviewed publication reports SO-101 arms performing laboratory module swapping, vial handling, or instrument tending with quantified success rates.

---

### 7. Summary of Explicit Gaps

- **AgileX PiPER:** No peer-reviewed paper reports this arm in laboratory automation. No independent repeatability, positioning accuracy, or task success rate was located.
- **SO-101 leader/follower:** No peer-reviewed laboratory-automation evaluation was located. The arm appears only in imitation-learning preprints for generic tabletop tasks.
- **Tool changing on a pipetting gantry (vial carriers):** No published study was found where a robot arm autonomously swaps vial carriers onto a commercial pipetting gantry.
- **Auger/hopper exchange on a powder doser:** No published study was found where a robot arm autonomously exchanges augers or hoppers on a powder-dosing instrument. Powder handling has been demonstrated biomimetically (Jiang et al., 2023) but not via instrument-module exchange.
- **Combined AprilTag + imitation learning for lab tasks:** No study was found that combines AprilTag-based localization with imitation learning specifically for laboratory module/tool swapping.

---

### 8. Recommendations for Your Setup

Based on the evidence, lab vial insertion tasks typically require sub-millimeter to ~2 mm positioning accuracy. AprilTag localization alone yields ~8–15 mm error in typical setups (nissler2016evaluationandimprovement pages 3-4, nissler2016evaluationandimprovement pages 4-5, nissler2016evaluationandimprovement pages 1-2), which is insufficient for direct vial insertion. Multi-camera fusion can reduce this to ~1 mm (wilcock2026fusionoffiducial pages 18-18), and visual servoing with wrist cameras can achieve sub-millimeter accuracy for tasks like GC injection (angelopoulos2023highaccuracyinjectionusing pages 4-6). For your low-cost arms, the FMB benchmark (1–2 mm tolerance 3D-printed insertions) and the NIST Assembly Task Board provide directly repeatable tests that will reveal whether your arms' combined positioning and sensing accuracy meets laboratory-task requirements. If AprilTags alone prove insufficient, the literature consistently shows that closed-loop visual servoing or multimodal (force + vision) feedback can bridge the accuracy gap, as demonstrated by the improvement from 48.78% to 89.55% vial insertion success when force feedback was added to vision (butterworth2023leveragingmultimodalsensing pages 1-2).

References

1. (murooka2026robomanipbaselinesaunified pages 7-8): Masaki Murooka, Tomohiro Motoda, Ryoichi Nakajo, Hanbit Oh, Koshi Makihara, Keisuke Shirai, Tetsuya Ogata, and Yukiyasu Domae. Robomanipbaselines: a unified framework for imitation learning in robotic manipulation across real and simulation environments. IEEE Access, 14:97896-97909, Jan 2026. URL: https://doi.org/10.1109/access.2026.3691054, doi:10.1109/access.2026.3691054. This article has 5 citations and is from a peer-reviewed journal.

2. (su2026vlaprecisionasymmetriccobootstrapping pages 9-10): Chen-Yu Su, Zhao-Long Shen, Yuan Qian, Chen Qian, Rui Zhang, Feng Yan, Wei-Xing Chen, Fei Zhang, Jia-Min Wang, Shuang Cong, and Wei-Wei Shang. Vla-precision: asymmetric co-bootstrapping for efficient real-world online rl of vision-language-action models. ArXiv, Sep 2026. URL: https://doi.org/10.48550/arxiv.2609.04355, doi:10.48550/arxiv.2609.04355. This article has 2 citations.

3. (luo2025fmbafunctional pages 3-5): Jianlan Luo, Charles Xu, Fangchen Liu, Liam Tan, Zipeng Lin, Jeffrey Wu, Pieter Abbeel, and Sergey Levine. Fmb: a functional manipulation benchmark for generalizable robotic learning. The International Journal of Robotics Research, Sep 2024. URL: https://doi.org/10.1177/02783649241276017, doi:10.1177/02783649241276017. This article has 161 citations.

4. (chen2025robustpeginholeassembly pages 9-10): Yiting Chen, Kenny Kimble, Howard H. Qian, Podshara Chanrungmaneekul, Robert Seney, and Kaiyu Hang. Robust peg-in-hole assembly under uncertainties via compliant and interactive contact-rich manipulation. ArXiv, Jun 2025. URL: https://doi.org/10.48550/arxiv.2506.22766, doi:10.48550/arxiv.2506.22766. This article has 23 citations.

5. (jiang2023autonomousbiomimeticsolid pages 10-11): Ying Jiang, Hatem Fakhruldeen, Gabriella Pizzuto, Louis Longley, Ai He, Tianwei Dai, Rob Clowes, Nicola Rankin, and Andrew I. Cooper. Autonomous biomimetic solid dispensing using a dual-arm robotic manipulator. Digital Discovery, 2:1733-1744, Jan 2023. URL: https://doi.org/10.1039/d3dd00075c, doi:10.1039/d3dd00075c. This article has 73 citations and is from a peer-reviewed journal.

6. (manes2024asoftcable pages 6-7): Lupo Manes, Sebastiano Fichera, Hatem Fakhruldeen, Andrew Cooper, and Paolo Paoletti. A soft cable loop based gripper for robotic automation of chemistry. Scientific Reports, Apr 2024. URL: https://doi.org/10.1038/s41598-024-59372-1, doi:10.1038/s41598-024-59372-1. This article has 17 citations and is from a peer-reviewed journal.

7. (rosas2026implementationofa pages 18-20): Isai Josue Rios Rosas, Francisco D. Calvo López, María Judith Percino Zacarías, Enrique Pérez-Gutiérrez, Manuel J. Heredia-Rios, David Pinto-Avendaño, and Humberto Salazar Ibargüen. Implementation of a collaborative robot for chemistry lab tasks. Proceedings of the XVI Ibero-American Congress of Mechanical Engineering, pages 504-523, Jan 2026. URL: https://doi.org/10.1007/978-3-032-22823-9\_36, doi:10.1007/978-3-032-22823-9\_36. This article has 0 citations.

8. (manna2026endtoendautomationof pages 11-14): Riddha Manna, Tomislav Štampar, Ivan Tomić, and Ana Marija Jakšić. End-to-end automation of behavioural experiments with a collaborative robot. bioRxiv, Oct 2026. URL: https://doi.org/10.64898/2026.10.20.758951, doi:10.64898/2026.10.20.758951. This article has 0 citations.

9. (manna2026endtoendautomationof pages 14-17): Riddha Manna, Tomislav Štampar, Ivan Tomić, and Ana Marija Jakšić. End-to-end automation of behavioural experiments with a collaborative robot. bioRxiv, Oct 2026. URL: https://doi.org/10.64898/2026.10.20.758951, doi:10.64898/2026.10.20.758951. This article has 0 citations.

10. (manna2026endtoendautomationof pages 9-11): Riddha Manna, Tomislav Štampar, Ivan Tomić, and Ana Marija Jakšić. End-to-end automation of behavioural experiments with a collaborative robot. bioRxiv, Oct 2026. URL: https://doi.org/10.64898/2026.10.20.758951, doi:10.64898/2026.10.20.758951. This article has 0 citations.

11. (manna2026endtoendautomationof pages 3-5): Riddha Manna, Tomislav Štampar, Ivan Tomić, and Ana Marija Jakšić. End-to-end automation of behavioural experiments with a collaborative robot. bioRxiv, Oct 2026. URL: https://doi.org/10.64898/2026.10.20.758951, doi:10.64898/2026.10.20.758951. This article has 0 citations.

12. (burger2023amobilerobotic pages 52-56): Benjamin Burger. A mobile robotic researcher. ArXiv, Jan 2023. URL: https://doi.org/10.17638/03087073, doi:10.17638/03087073. This article has 4 citations.

13. (zhou2025localizationinspectionand pages 2-3): Zhengxue Zhou, Satheeshkumar Veeramani, Francisco Munguia-Galeano, Hatem Fakhruldeen, and Andrew I. Cooper. Localization, inspection, and reasoning (lira) module for autonomous workflows in self-driving laboratories. Communications Chemistry, Nov 2025. URL: https://doi.org/10.1038/s42004-025-01770-1, doi:10.1038/s42004-025-01770-1. This article has 14 citations and is from a peer-reviewed journal.

14. (zhou2025localizationinspectionand pages 7-8): Zhengxue Zhou, Satheeshkumar Veeramani, Francisco Munguia-Galeano, Hatem Fakhruldeen, and Andrew I. Cooper. Localization, inspection, and reasoning (lira) module for autonomous workflows in self-driving laboratories. Communications Chemistry, Nov 2025. URL: https://doi.org/10.1038/s42004-025-01770-1, doi:10.1038/s42004-025-01770-1. This article has 14 citations and is from a peer-reviewed journal.

15. (angelopoulos2023highaccuracyinjectionusing pages 4-6): Angelos Angelopoulos, Matthew Verber, Collin McKinney, James F. Cahoon, and Ron Alterovitz. High-accuracy injection using a mobile manipulation robot for chemistry lab automation. 2023 IEEE/RSJ International Conference on Intelligent Robots and Systems (IROS), pages 10102-10109, Oct 2023. URL: https://doi.org/10.1109/iros55552.2023.10341743, doi:10.1109/iros55552.2023.10341743. This article has 22 citations.

16. (angelopoulos2026autonomoussciencelaboratoriesa pages 43-47): A Angelopoulos. Autonomous science laboratories with a unified software framework and robots. Unknown journal, 2026.

17. (angelopoulos2023highaccuracyinjectionusing pages 7-8): Angelos Angelopoulos, Matthew Verber, Collin McKinney, James F. Cahoon, and Ron Alterovitz. High-accuracy injection using a mobile manipulation robot for chemistry lab automation. 2023 IEEE/RSJ International Conference on Intelligent Robots and Systems (IROS), pages 10102-10109, Oct 2023. URL: https://doi.org/10.1109/iros55552.2023.10341743, doi:10.1109/iros55552.2023.10341743. This article has 22 citations.

18. (angelopoulos2026autonomoussciencelaboratoriesa pages 34-38): A Angelopoulos. Autonomous science laboratories with a unified software framework and robots. Unknown journal, 2026.

19. (fleischer2016applicationofa pages 3-5): Heidi Fleischer, Robert Ralf Drews, Jessica Janson, Bharath Reddy Chinna Patlolla, Xianghua Chu, Michael Klos, and Kerstin Thurow. Application of a dual-arm robot in complex sample preparation and measurement processes. SLAS Technology, 21:671-681, Oct 2016. URL: https://doi.org/10.1177/2211068216637352, doi:10.1177/2211068216637352. This article has 77 citations and is from a peer-reviewed journal.

20. (chu2016automationstrategiesfor pages 121-126): Xianghua Chu. Automation strategies for sample preparation in life science applications. Text, Jan 2016. URL: https://doi.org/10.18453/rosdok\_id00002364, doi:10.18453/rosdok\_id00002364. This article has 2 citations and is from a peer-reviewed journal.

21. (maroulis2026automationsystemsfor pages 28-33): A Maroulis. Automation systems for experimentation: design of open-source liquid handlers and self-driving liquid handling laboratories. Unknown journal, 2026.

22. (maroulis2026automationsystemsfora pages 28-33): A Maroulis. Automation systems for experimentation: design of open-source liquid handlers and self-driving liquid handling laboratories. Unknown journal, 2026.

23. (maroulis2026automationsystemsfor pages 33-37): A Maroulis. Automation systems for experimentation: design of open-source liquid handlers and self-driving liquid handling laboratories. Unknown journal, 2026.

24. (lunt2024aroboticworkflow pages 49-57): Amy Lunt. A robotic workflow to screen crystal forms using powder x-ray diffraction. Text, Jan 2024. URL: https://doi.org/10.17638/03178518, doi:10.17638/03178518. This article has 0 citations and is from a peer-reviewed journal.

25. (lunt2024aroboticworkflow pages 87-95): Amy Lunt. A robotic workflow to screen crystal forms using powder x-ray diffraction. Text, Jan 2024. URL: https://doi.org/10.17638/03178518, doi:10.17638/03178518. This article has 0 citations and is from a peer-reviewed journal.

26. (manna2026endtoendautomationof pages 1-1): Riddha Manna, Tomislav Štampar, Ivan Tomić, and Ana Marija Jakšić. End-to-end automation of behavioural experiments with a collaborative robot. bioRxiv, Oct 2026. URL: https://doi.org/10.64898/2026.10.20.758951, doi:10.64898/2026.10.20.758951. This article has 0 citations.

27. (maroulis2026automationsystemsfora pages 33-37): A Maroulis. Automation systems for experimentation: design of open-source liquid handlers and self-driving liquid handling laboratories. Unknown journal, 2026.

28. (salazarvillacis2026theadeptframework pages 5-6): Pablo Salazar-Villacis and Brahim Benyahia. The adept framework for assessing autonomous laboratory robotics. Communications Chemistry, Feb 2026. URL: https://doi.org/10.1038/s42004-026-01932-9, doi:10.1038/s42004-026-01932-9. This article has 17 citations and is from a peer-reviewed journal.

29. (nissler2016evaluationandimprovement pages 3-4): Christian Nissler, Stefan Buttner, Zoltan-Csaba Marton, Laura Beckmann, and Ulrike Thomasy. Evaluation and improvement of global pose estimation with multiple apriltags for industrial manipulators. 2016 IEEE 21st International Conference on Emerging Technologies and Factory Automation (ETFA), pages 1-8, Sep 2016. URL: https://doi.org/10.1109/etfa.2016.7733711, doi:10.1109/etfa.2016.7733711. This article has 35 citations.

30. (nissler2016evaluationandimprovement pages 4-5): Christian Nissler, Stefan Buttner, Zoltan-Csaba Marton, Laura Beckmann, and Ulrike Thomasy. Evaluation and improvement of global pose estimation with multiple apriltags for industrial manipulators. 2016 IEEE 21st International Conference on Emerging Technologies and Factory Automation (ETFA), pages 1-8, Sep 2016. URL: https://doi.org/10.1109/etfa.2016.7733711, doi:10.1109/etfa.2016.7733711. This article has 35 citations.

31. (nissler2016evaluationandimprovement pages 5-7): Christian Nissler, Stefan Buttner, Zoltan-Csaba Marton, Laura Beckmann, and Ulrike Thomasy. Evaluation and improvement of global pose estimation with multiple apriltags for industrial manipulators. 2016 IEEE 21st International Conference on Emerging Technologies and Factory Automation (ETFA), pages 1-8, Sep 2016. URL: https://doi.org/10.1109/etfa.2016.7733711, doi:10.1109/etfa.2016.7733711. This article has 35 citations.

32. (nissler2016evaluationandimprovement pages 1-2): Christian Nissler, Stefan Buttner, Zoltan-Csaba Marton, Laura Beckmann, and Ulrike Thomasy. Evaluation and improvement of global pose estimation with multiple apriltags for industrial manipulators. 2016 IEEE 21st International Conference on Emerging Technologies and Factory Automation (ETFA), pages 1-8, Sep 2016. URL: https://doi.org/10.1109/etfa.2016.7733711, doi:10.1109/etfa.2016.7733711. This article has 35 citations.

33. (wilcock2026fusionoffiducial pages 18-18): Samuel P. Wilcock and O. Iuorio. Fusion of fiducial marker and point cloud data for reliable multi-camera tracking in robotic assembly of construction elements. Construction Robotics, May 2026. URL: https://doi.org/10.1007/s41693-026-00183-3, doi:10.1007/s41693-026-00183-3. This article has 0 citations and is from a peer-reviewed journal.

34. (franchini2023mechatronicdesignand pages 6-7): Giacomo Franchini, Sebastiano Chiodini, Marco Ghetti, and Marco Pertile. Mechatronic design and positioning accuracy characterisation of a robotic arm for exploration rovers. 2023 IEEE 10th International Workshop on Metrology for AeroSpace (MetroAeroSpace), pages 452-457, Jun 2023. URL: https://doi.org/10.1109/metroaerospace57412.2023.10190044, doi:10.1109/metroaerospace57412.2023.10190044. This article has 6 citations.

35. (franchini2023mechatronicdesignand pages 7-7): Giacomo Franchini, Sebastiano Chiodini, Marco Ghetti, and Marco Pertile. Mechatronic design and positioning accuracy characterisation of a robotic arm for exploration rovers. 2023 IEEE 10th International Workshop on Metrology for AeroSpace (MetroAeroSpace), pages 452-457, Jun 2023. URL: https://doi.org/10.1109/metroaerospace57412.2023.10190044, doi:10.1109/metroaerospace57412.2023.10190044. This article has 6 citations.

36. (butterworth2023leveragingmultimodalsensing pages 1-2): Aaron Butterworth, Gabriella Pizzuto, Leszek Pecyna, Andrew I. Cooper, and Shan Luo. Leveraging multi-modal sensing for robotic insertion tasks in r&d laboratories. 2023 IEEE 19th International Conference on Automation Science and Engineering (CASE), pages 1-8, Jul 2023. URL: https://doi.org/10.48550/arxiv.2307.00671, doi:10.48550/arxiv.2307.00671. This article has 12 citations.

37. (lian2021benchmarkingofftheshelfsolutions pages 2-3): Wenzhao Lian, Tim Kelch, Dirk Holz, Adam Norton, and Stefan Schaal. Benchmarking off-the-shelf solutions to robotic assembly tasks. 2021 IEEE/RSJ International Conference on Intelligent Robots and Systems (IROS), pages 1046-1053, Sep 2021. URL: https://doi.org/10.1109/iros51168.2021.9636586, doi:10.1109/iros51168.2021.9636586. This article has 53 citations.