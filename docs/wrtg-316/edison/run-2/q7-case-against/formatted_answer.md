Question: We are writing a literature review to discover which tests determine the value of a robot arm used as an automated manual manipulator in a self-driving laboratory (SDL) for materials science. By automated manual manipulator we mean one arm that does the hands-on work a person would otherwise do: it moves from station to station (for example a pipetting gantry, a powder doser, a balance, vial and plate racks), recalibrates itself at each station using a calibration square (a square fiducial target such as an AprilTag, or a square fixture at a known position), and takes on several new automated tasks. The term is ours; the literature may say mobile manipulator, robotic laboratory assistant, robot chemist, or sample- or labware-handling robot. Our arms are a low-cost AgileX PiPER 6-DOF arm (about $2k) and SO-101 leader/follower arms (about $200), with parallel grippers, Raspberry Pi wrist cameras and fixed cameras in an enclosure, AprilTags, and LeRobot-style imitation learning or scripted motion. We want to place these arms in the published literature and find tests that we, or anyone validating an affordable arm, can repeat to compare it with the industry-standard arms used in SDLs (e.g. UR5e, UR3, Franka Panda, ABB YuMi, Kinova, KUKA), including on cost per task.

The case against: What evidence or arguments show that low-cost arms are not suitable for laboratory automation, or as automated manual manipulators that move between stations (accuracy, reliability, durability, safety, hidden integration and maintenance costs), compared to industrial and collaborative arms?

Prioritize peer-reviewed journal articles and major conference papers from 2015 to 2026, and flag any preprints. For each benchmark or result, describe the protocol in enough detail to repeat it (what is measured, number of trials, success criterion, measuring tool) and give the arm model. For each claim, give the DOI and quote the sentence that supports it. Say explicitly where no published evidence exists.



# The Case Against Low-Cost Robot Arms as Automated Manual Manipulators in Self-Driving Laboratories

## Summary

This review synthesizes peer-reviewed evidence and flagged preprints (2015–2026) on whether low-cost robot arms (e.g., AgileX PiPER, SO-101, Dobot Magician) are suitable for use as automated manual manipulators in self-driving laboratories (SDLs) for materials science, compared with the industry-standard arms (KUKA LBR iiwa, UR5e/UR3e, Franka Panda) that dominate published SDL platforms. The evidence is organized into six dimensions: (1) positional accuracy and repeatability, (2) reliability and durability, (3) safety and certification, (4) hidden integration and total cost of ownership, (5) mobile-manipulator station-to-station performance, and (6) the absence of published evidence for specific low-cost arms. **A critical finding is that no peer-reviewed, head-to-head benchmark of a low-cost arm against an industrial arm on standardized SDL tasks currently exists.** Most evidence is indirect, drawn from separate studies of different arms in different contexts.

The following table summarizes the arms, their specifications, and their validation status in published laboratory workflows.

| Arm model | DOF | Repeatability reported by manufacturer or paper | Approx. arm price (USD, hardware only) | Payload | Safety/certification status | Validation in a published SDL or laboratory workflow |
|---|---:|---:|---:|---:|---|---|
| **KUKA LBR iiwa 14** | 7 | ±0.1 mm; station calibration located a reference cube within 0.12 mm after deliberately adding ±15 mm and ±2.5° initial error (burger2023amobilerobotic pages 52-56) | ≈$70k–$100k arm; KMR mobile system substantially more | 14 kg | Industrial collaborative arm with safety-rated torque sensing; the completed cell still requires application-specific risk assessment under ISO 10218/ISO/TS 15066 (valori2021validatingsafetyin pages 19-20, valori2021validatingsafetyin pages 3-5) | **Yes.** KUKA KMR iiwa mobile chemist completed 688 experiments over eight days; later KUKA systems were used for exploratory synthetic chemistry (burger2023amobilerobotic pages 52-56, salazarvillacis2026theadeptframework pages 3-4) |
| **Universal Robots UR5e** | 6 | ±0.03 mm nominal; published SDL pages reviewed did not independently verify this specification | ≈$30k–$40k | 5 kg | Collaborative industrial arm with safety-rated functions; not inherently safe after adding grippers, tools, or chemicals. UR5e/UR10e laboratory collision tests exceeded pressure limits in every tested scenario even at restrictive settings (mariano2026roboticsafetyin pages 10-11, mariano2026roboticsafetyin pages 7-7) | **Yes.** Used on a linear rail in the MARS SDL and on a Ridgeback mobile base; MARS reported pick/place as its principal failure source and 29–43% campaign failure from gripper communication faults (ahlquist2024improvingselfdrivinglabs pages 1-6, sulaiman2026kinematicanalysisand pages 6-9) |
| **Universal Robots UR3e** | 6 | ±0.03 mm nominal; no independent arm-level metrology located in the reviewed SDL literature | ≈$25k–$35k | 3 kg | Collaborative industrial arm with configurable safety functions; final tooling and cell require separate validation (valori2021validatingsafetyin pages 19-20, valori2021validatingsafetyin pages 5-6) | **Yes.** Used in the Hein laboratory and represented in RABIT’s SDL safety evaluation; MATTERIX also includes a UR3e (wattoo2024rabitarobot pages 6-7, wattoo2024rabitarobot pages 1-2) |
| **Franka Emika Panda / Franka Research 3** | 7 | ±0.1 mm nominal | ≈$20k–$35k | 3 kg | Torque-sensing collaborative research arm, but complete-cell conformity and collision validation remain the integrator’s responsibility (valori2021validatingsafetyin pages 3-5, valori2021validatingsafetyin pages 5-6) | **Yes.** Used in ARChemist/MATTERIX-related chemistry automation and paired with a laboratory gripper reporting ≤1% grasp failures (salazarvillacis2026theadeptframework pages 3-4, wolf2022towardsroboticlaboratory pages 12-16) |
| **Dobot Magician** | 4 | 0.2 mm nominal (rupp2022establishmentoflowcost pages 2-3) | ≈$1.2k–$2k | 0.5 kg | Educational/desktop arm; no evidence located of ISO 10218/ISO/TS 15066 safety-rated functions or certification for barrier-free collaborative laboratory use | **Laboratory workflow: yes; full SDL: no.** Operated an electronic pipette, AAS autosampler, and inoculation loop. Automated pipetting agreed statistically with manual work, but cycles were about 3.5× slower and inoculation repeatability was described as “severely limited” (rupp2022establishmentoflowcost pages 4-5, rupp2022establishmentoflowcost pages 6-7) |
| **Dobot M1 Pro** | 4 | ±0.02 mm nominal; loaded plate-transfer IQR was 0.020 mm in x and 0.006 mm in y at full speed (harazono2024evaluationofmicroplate pages 11-15) | ≈$3k–$5k | 1.5 kg | Desktop SCARA; no evidence located of safety-rated collaborative functions equivalent to certified industrial cobots | **Laboratory benchmark only; not an SDL.** A **preprint** tested 125 loaded microplate transfers at each speed and 125 lid placements per imposed-offset condition using digital gauges and video/OpenCV scoring (harazono2024evaluationofmicroplate pages 11-15, harazono2024evaluationofmicroplate pages 15-20, harazono2024evaluationofmicroplate pages 6-11) |
| **Niryo Ned2** | 6 | 0.5 mm reported in a low-cost-arm comparison (chebly2025strongaccurateand pages 2-3) | ≈$4k–$6k | 0.3 kg | Educational/research arm; no safety-rated PFL/SSM certification established in the reviewed publications | **SDL safety testbed only.** RABIT used Ned2 with ViperX as lower-precision surrogates for a UR3e; Ned2 halted on infeasible motion, unlike ViperX’s silent failure (wattoo2024rabitarobot pages 6-7, wattoo2024rabitarobot pages 3-4) |
| **Trossen ViperX 300** | 6 | Not quantitatively reported in the reviewed SDL paper; described as having limited precision (wattoo2024rabitarobot pages 3-4) | ≈$3k–$5k | ≈0.75 kg, configuration-dependent | Research arm; no evidence located of industrial collaborative safety certification | **SDL safety testbed only.** It collided with Ned2 without RABIT raising an alarm; global-frame transformation produced about 3 cm mean error. It could also silently ignore infeasible trajectories (wattoo2024rabitarobot pages 6-7, wattoo2024rabitarobot pages 4-6) |
| **Forte open-source arm** | 6 | 0.467 mm summary value; dial-indicator tests gave 0.286–0.587 mm standard deviation across 500–2500 steps/s (chebly2025strongaccurateand pages 2-3, chebly2025strongaccurateand pages 6-7) | $212 material cost | 0.63 kg | **Preprint prototype** without documented industrial functional-safety certification | **No.** Validated only as a low-cost manipulation prototype; no published chemistry/materials SDL deployment or long-duration reliability study was located |
| **LeRobot SO-101** | 6 | No independently verified Cartesian repeatability value located; published work identifies STS3215 servos but does not establish laboratory-grade accuracy (huang2026vlareplicaalowcost pages 3-4) | ≈$100–$250 per follower arm; ≈$1,050 for the cited complete benchmark cell | Not established by a peer-reviewed payload test | Educational/open research platform; no documented safety-rated controller, PFL validation, or industrial certification | **No.** A **2026 preprint** uses SO-101 in a reproducible vision-language-action benchmark, not an SDL; no published pipetting, powder dosing, balance tending, durability, or cost-per-task validation was located (huang2026vlareplicaalowcost pages 3-4) |
| **AgileX PiPER** | 6 | Commonly advertised as approximately ±0.1 mm, but no independent peer-reviewed verification located | ≈$2k–$3k | ≈1.5 kg nominal | No peer-reviewed evidence located establishing ISO 10218/ISO/TS 15066 safety-rated functions or certification for shared laboratory operation | **No published evidence located.** No peer-reviewed SDL study, loaded station-recalibration benchmark, long-duration reliability test, chemical-compatibility study, or cost-per-successful-task comparison against UR, Franka, ABB, Kinova, or KUKA arms was found |


*Table: Comparison of industrial, collaborative, and low-cost arms by performance, price, payload, safety status, and published laboratory validation. Prices and uncited nominal specifications are approximate and should be verified with current manufacturer documentation.*

---

## 1. Positional Accuracy and Repeatability

### 1.1 The Industrial Baseline

The KUKA LBR iiwa, the arm used in the seminal Burger et al. (2020) mobile robotic chemist, has a manufacturer-specified repeatability of ±0.1 mm. In Burger's thesis, a six-point calibration procedure located a reference calibration cube within 0.12 mm and corrected orientation offsets to less than 0.005°, even after deliberately introducing ±15 mm translational and ±2.5° rotational noise to the initial position estimate (burger2023amobilerobotic pages 52-56). This system completed 688 experiments autonomously over eight days (burger2023amobilerobotic pages 52-56).

The UR5e (±0.03 mm nominal repeatability) and Franka Emika Panda (±0.1 mm nominal) are the other most-cited SDL arms (salazarvillacis2026theadeptframework pages 3-4, sulaiman2026kinematicanalysisand pages 6-9). However, no independent metrology study in the reviewed SDL literature verified these manufacturer specifications under loaded laboratory conditions.

### 1.2 Low-Cost Arm Measurements

**Dobot Magician (4-DOF, ~$1.5k):** Manufacturer-specified position repeatability is 0.2 mm (rupp2022establishmentoflowcost pages 2-3). Rupp et al. (2022, *SLAS Technology*, DOI: 10.1016/j.slast.2022.07.001) demonstrated that the Dobot Magician could operate an electronic pipette to transfer 20 µL and 100 µL aliquots of lissamine green into 96-well plates with "no significant differences in accuracy and precision" compared to manual operation by a trained researcher (rupp2022establishmentoflowcost pages 4-5). However, the same study found that automated processes were approximately 3.5× slower than manual pipetting and that repeatability was "severely limited" in a bacterial inoculation task where the inoculation loop extended the robot axis (rupp2022establishmentoflowcost pages 6-7). No formal positional-accuracy metrology (e.g., laser tracker, dial gauge under load) was reported.

**Protocol (Rupp et al. 2022):** Lissamine green dilutions transferred from 1.5 mL tubes to 96-well plates using a BRAND electronic micropipette. Volumes: 20 µL (multi-dispense) and 100 µL (single pipette). Comparison: absorbance readings (automated vs. manual). Measuring tool: plate reader absorbance. Number of trials: not explicitly stated per condition. Success criterion: no statistically significant difference in mean absorbance. Arm: Dobot Magician on a linear rail with 3D-printed PLA pipette holder and linear solenoid actuator (rupp2022establishmentoflowcost pages 4-5, rupp2022establishmentoflowcost pages 2-3).

**Dobot M1 Pro (4-DOF SCARA, ~$3–5k):** Harazono et al. (2024, **preprint**, bioRxiv, DOI: 10.1101/2023.12.29.573685) measured loaded microplate-transfer repeatability using digital dial gauges (DGN-125B) on an aluminum-frame platform. Over 125 repetitions at full speed, the interquartile range (IQR) was 0.020 mm in x and 0.006 mm in y; at 50% speed, IQR was 0.034 mm (x) and 0.014 mm (y) (harazono2024evaluationofmicroplate pages 11-15). Lid-placement tolerance was tested by introducing artificial offsets (Δx = 1.80–2.30 mm, Δy = 2.10–2.20 mm), with 125 trials per condition. Success was scored from video analysis using OpenCV and colored circular stickers. Transfer success declined gradually with increasing x-offset and dropped significantly when Δy exceeded 2.190 mm (harazono2024evaluationofmicroplate pages 15-20). This preprint explicitly notes that manufacturer repeatability specs (measured unloaded, per ISO 9283) may not predict performance under realistic laboratory loads (harazono2024evaluationofmicroplate pages 1-6).

**Forte (6-DOF, ~$212 material cost, preprint):** Chebly et al. (2025, arXiv, DOI: 10.48550/arxiv.2507.15693) measured repeatability using a Westward 4KU81 dial indicator. Standard deviations ranged from 0.286 mm at 500 steps/s to 0.587 mm at 2500 steps/s (chebly2025strongaccurateand pages 6-7). The comparison table in this preprint lists Niryo Ned2 at 0.5 mm repeatability and WLKATA Mirobot at 0.2 mm, but Dobot Magician's repeatability was listed as not reported (chebly2025strongaccurateand pages 2-3). The paper describes Forte's performance as "near industrial-grade" but provides no laboratory task validation.

**SO-101 (~$100–250):** The VLA-Replica benchmark (Huang et al. 2026, arXiv, DOI: 10.48550/arxiv.2605.20774, **preprint**) uses SO-101 arms with STS3215 Dynamixel servos. The complete benchmark cell costs approximately $1,050. The paper identifies servo motor variability across differently constructed SO-101 arms as a concern, noting that "an inaccurate grasp pose can cause the object" to fail tasks (huang2026vlareplicaalowcost pages 3-4). No Cartesian repeatability, loaded accuracy, or laboratory-task validation was reported.

**Key gap:** No published study directly compares a low-cost arm (Dobot, Forte, SO-101, or PiPER) against a UR5e, Franka, or KUKA on the same laboratory task with the same protocol and measuring instruments.

---

## 2. Reliability, Durability, and Failure Modes

### 2.1 Industrial Arm Failures in SDLs

Even industrial arms experience significant reliability challenges in SDL operations. Ahlquist (2024, DOE OSTI report, DOI: 10.2172/2459394) reported that in the MARS SDL (UR5e on a linear rail), "the robotic arm's labware pick-and-place operation was identified as the principal source of experiment failures." A compliant 3D-printed plastic gripper produced inconsistent placement and was replaced with a rigid aluminum gripper. Communication errors with an OnRobot gripper caused campaigns to hang indefinitely, with 29–43% of campaigns failing before completion depending on campaign length (ahlquist2024improvingselfdrivinglabs pages 1-6).

### 2.2 Low-Cost Arm Failure Modes

Wattoo et al. (2024, IEEE DSN, DOI: 10.1109/dsn58291.2024.00043) documented failure modes in the RABIT SDL safety testbed using ViperX and Niryo Ned2 as low-cost surrogates for a UR3e. Critical findings include:

- **Silent failure:** "ViperX also silently ignored infeasible motions when trajectory computation failed, potentially causing later collisions, whereas Ned2 threw an exception and halted" (wattoo2024rabitarobot pages 6-7). This behavioral difference between low-cost arms—one silently failing, one halting—illustrates the unpredictability of non-standardized error handling.
- **Collision without detection:** In a two-arm scenario, "ViperX and Ned2 were positioned near one another and collided, yet RABIT did not raise an alarm." Global-frame coordinate transformation produced an average 3 cm positional error due to "different vendors, gripper sizes, low precision, and coordinate-system incompatibility" (wattoo2024rabitarobot pages 4-6).
- **Limited detection:** Of 16 introduced unsafe program changes, RABIT initially detected only 50%, rising to 75–81% after modifications (wattoo2024rabitarobot pages 6-7).

Rupp et al. (2022) reported that Dobot Magician repeatability was "severely limited" in a bacterial inoculation task, apparently because the inoculation loop extended the robot axis beyond the arm's inherent accuracy envelope (rupp2022establishmentoflowcost pages 6-7).

**Key gap:** No published long-term durability study (e.g., mean time between failures over thousands of hours) exists for any low-cost arm in continuous laboratory operation.

---

## 3. Safety and Certification

### 3.1 Regulatory Framework

Collaborative robots in shared workspaces are governed by ISO 10218-1/2 (industrial robot safety), ISO/TS 15066 (collaborative robot guidance), and in Europe, the Machinery Directive 2006/42/EC (now superseded by Regulation (EU) 2023/1230) (valori2021validatingsafetyin pages 19-20, mariano2026roboticsafetyin pages 3-3, valori2021validatingsafetyin pages 3-5). A robot arm alone is typically "partly completed machinery"—the integrator bears responsibility for the completed cell, including application-specific risk assessment (valori2021validatingsafetyin pages 3-5). Valori et al. (2021, *Robotics*, DOI: 10.3390/robotics10020065) warn that "low weight, ease of use, or a friendly appearance does not itself ensure safety and that inexperienced users may wrongly assume a collaborative robot is inherently safe" (valori2021validatingsafetyin pages 5-6).

### 3.2 Even Certified Cobots Exceed Safety Limits

Mariano et al. (2026, *SLAS Technology*, DOI: 10.1016/j.slast.2026.100463) performed collision force and pressure measurements on UR5e and UR10e arms using a CoboSafe measurement system in the Swiss Cat+ West Hub automated analytical laboratory. The study found that "pressure limits were exceeded in every evaluated collision scenario even with the robot's most restrictive safety settings" (mariano2026roboticsafetyin pages 10-11, mariano2026roboticsafetyin pages 11-12). End-effector geometry was identified as a potentially dominant determinant of injury severity (mariano2026roboticsafetyin pages 10-11). In chemistry laboratories, even low-energy collisions can cause "spills, contamination events, or sample loss" (mariano2026roboticsafetyin pages 10-11). Sixteen hazards were identified, with robot–human collisions and chemical exposure rated most critical (mariano2026roboticsafetyin pages 1-2).

### 3.3 Implications for Low-Cost Arms

If even certified collaborative robots (UR5e/UR10e) with built-in safety-rated torque sensing and power-and-force-limiting modes exceed ISO/TS 15066 pressure thresholds, low-cost arms—which lack safety-rated controllers, certified torque sensors, and validated collision-detection hardware—present substantially greater uncharacterized risk in shared laboratory spaces. No published evidence was found establishing that any low-cost arm (AgileX PiPER, SO-101, Dobot Magician, Forte, or similar) has undergone collision force/pressure testing, safety-rated monitored stop validation, or any equivalent safety certification process for barrier-free laboratory use.

**Protocol (Mariano et al. 2026):** Force and pressure measured using CoboSafe Force and Pressure Measurement System, designed to reproduce biomechanical characteristics of human body regions. Risk evaluated per ISO/TR 14121-2:2013 risk-graph method. Arms tested: UR5e and UR10e (Universal Robots). Hazard scenarios included transient head impacts and static upper-body crushing. Success criterion: collision forces and pressures below ISO/TS 15066 biomechanical limits. Result: limits exceeded in every scenario tested (mariano2026roboticsafetyin pages 7-7, mariano2026roboticsafetyin pages 10-11).

---

## 4. Hidden Integration Costs and Total Cost of Ownership

### 4.1 Purchase Price Is a Poor Proxy for Total Cost

Landscheidt and Kans (2016, *Procedia CIRP*, DOI: 10.1016/j.procir.2016.11.129) developed a TCO model for industrial robots based on expert interviews at a robot manufacturer and two large customers. Their analysis of arc-welding robots over five years found that operator wages, spare parts, and energy consumption together accounted for over 75% of total quantitative costs. The simplified TCO equation is: TCO = Σ(Initial price) + Σ(Operator's wages) + Σ(Spare parts) + Σ(Energy consumption) (landscheidt2016methodforassessing pages 3-5, landscheidt2016methodforassessing pages 5-6).

Genzen et al. (2018, *Clinical Chemistry*, DOI: 10.1373/clinchem.2017.274068) emphasized that laboratory automation implementation costs extend far beyond equipment purchase to include "remodeling or adapting constrained laboratory space, addressing floor load capacity, ventilation, heat, noise, waste disposal, electrical supply and backup," as well as staffing, training, vendor service, spare parts, and downtime prevention (genzen2018challengesandopportunities pages 2-3). They note that "ongoing maintenance, which may represent a significant percentage of the purchase price each year," must be included in total cost justification (genzen2018challengesandopportunities pages 4-5).

Khare et al. (2023, *J. Laboratory Physicians*, DOI: 10.1055/s-0043-1768634) demonstrated in a 10-year lifecycle analysis of robotic track-based laboratories that the vendor with the lowest initial equipment price did not have the lowest lifecycle cost—Vendor C had the lowest equipment price (Rs. 14.98 crore) but Vendor D had the lowest 10-year lifecycle cost (Rs. 111.22 crore vs. Rs. 130.85 crore for the initially selected vendor) (khare2023impactoflife pages 3-5).

### 4.2 Integration Costs for Low-Cost Arms

Jin et al. (2026) argue that lifecycle assessment should include "acquisition, site preparation, integration, training, supervision, energy, consumables, planned and unplanned maintenance, software, insurance, and eventual decommissioning" and that "excessive specialization can turn every sale into a new engineering project" (jin2026commercializationpathwaysapplication pages 8-10, jin2026commercializationpathwaysapplication pages 6-8). Wolf et al. (2022, *SLAS Technology*, DOI: 10.1016/j.slast.2021.11.003) note that laboratory robot systems require "comprehensive integration work, careful layout and device placement, and often custom frames rather than standard laboratory benches" (wolf2022towardsroboticlaboratory pages 12-16).

**Key implication for low-cost arms:** A $200 SO-101 or $2,000 PiPER may cost far less to purchase, but the integration engineering—custom grippers, 3D-printed fixtures, camera calibration, software development, safety enclosures, and ongoing debugging—may equal or exceed the cost of an industrial arm whose ecosystem provides validated grippers, documented APIs, safety controllers, and vendor support. **No published study quantifies the integration cost of deploying a low-cost arm in an SDL, so this remains an important but unverified concern.**

---

## 5. Mobile Manipulator Station-to-Station Performance

The user's use case—an arm moving between stations and recalibrating at each using fiducial targets—mirrors the mobile manipulator paradigm. Evidence shows this is challenging even with industrial hardware:

- **KUKA KMR iiwa** mobile base returns to pre-recorded positions with approximately 10 mm translational and 0.5° rotational precision using 2D laser scanners—explicitly insufficient for manipulating small objects without additional calibration (carruthers2025amobilerobotic pages 24-27).
- Hifi et al. (2025, *Measurement Science and Technology*, DOI: 10.1088/1361-6501/adf3d4) measured KUKA KMR iiwa positioning with a Leica laser tracker (10 µm precision). Without feature mapping, encoder-only strafing error grew from 3.00 mm to 30.03 mm over ten runs; rotational error grew from 17.91 mm to 177.31 mm. With mapping enabled, errors dropped to approximately 1.6–4.4 mm for strafing and 1.9–6.7 mm for rotation, depending on speed (hifi2025aquantitativeinvestigation pages 10-11). Repeatability errors were under 7 mm with mapping and approximately 2.5 mm in practical scenarios (hifi2025aquantitativeinvestigation pages 1-3).
- Another cited study found that relying solely on SLAM left a dual-arm mobile robot 50–100 mm out of position; adding AR Tags and vision reduced errors to ≤10 mm (hifi2025aquantitativeinvestigation pages 3-4).
- Burger's KUKA KMR used a touch-based six-point calibration at each station to achieve sub-0.12 mm accuracy after navigation (burger2023amobilerobotic pages 52-56), but this relied on the arm's native 0.1 mm repeatability to execute the calibration procedure itself.

**Implication:** A low-cost arm with 0.5–2 mm repeatability, mounted on a low-cost mobile base with ≥10 mm navigation uncertainty, compounds both error sources. Without the mechanical precision to perform a reliable calibration procedure at each station, the entire system accuracy may be insufficient for tasks like pipette tip insertion, vial placement in instrument holders, or balance tending.

---

## 6. Explicit Gaps in Published Evidence

The following specific gaps were identified:

1. **No peer-reviewed study of AgileX PiPER in any laboratory context** was found. No repeatability metrology, loaded accuracy test, chemical compatibility assessment, long-duration reliability study, or cost-per-task comparison exists in the indexed literature.

2. **No peer-reviewed study of SO-101 in any laboratory automation context** was found. The only publication using SO-101 (Huang et al. 2026) is a preprint for vision-language-action model benchmarking, not laboratory science (huang2026vlareplicaalowcost pages 3-4).

3. **No published head-to-head comparison** of a low-cost arm against an industrial arm on the same standardized laboratory task (pipetting, plate handling, powder dosing, balance tending, vial transport) using the same protocol and measurement instruments exists.

4. **No published long-term durability or MTBF study** for any low-cost arm in continuous laboratory operation (24/7 SDL mode) was found.

5. **No published cost-per-successful-task analysis** comparing low-cost and industrial arms was found.

6. **No published safety (force/pressure) testing** of any low-cost arm was found—this gap is particularly concerning given that even certified UR5e/UR10e cobots exceeded ISO/TS 15066 pressure limits in laboratory collision scenarios (mariano2026roboticsafetyin pages 11-12, mariano2026roboticsafetyin pages 10-11).

7. **No published study of fiducial-based recalibration (AprilTag or similar)** at multiple stations using a low-cost arm was found, though the concept is well-established for industrial mobile manipulators (burger2023amobilerobotic pages 52-56).

---

## 7. Repeatable Benchmark Protocols from the Literature

For researchers seeking to validate an affordable arm, the following published protocols can be adapted:

**A. Microplate Transfer Repeatability (Harazono et al. 2024, preprint):** Construct an aluminum-frame platform with digital dial gauges (DGN-125B). Mount a 96-well microplate on the gripper. Repeatedly transfer the plate to a measurement position (path: P1→P2→P3→P2→P1) for 125 repetitions at each of two speeds. Record x and y displacement via gauge-to-spreadsheet communication at 2 s intervals. Report IQR. Test lid-placement tolerance by introducing controlled offsets (1.80–2.30 mm in x, 2.10–2.20 mm in y) over 125 trials per condition; score success/failure from video using OpenCV. Arm tested: Dobot M1 Pro (harazono2024evaluationofmicroplate pages 11-15, harazono2024evaluationofmicroplate pages 15-20, harazono2024evaluationofmicroplate pages 6-11).

**B. Pipetting Accuracy (Rupp et al. 2022, peer-reviewed):** Mount an electronic micropipette on the arm using a 3D-printed holder with a solenoid actuator. Transfer lissamine green dilutions from 1.5 mL tubes to 96-well plates at 20 µL (multi-dispense) and 100 µL (single pipette). Measure absorbance. Compare automated vs. manual results. Report mean, SD, and statistical significance. Arm tested: Dobot Magician (rupp2022establishmentoflowcost pages 4-5, rupp2022establishmentoflowcost pages 2-3).

**C. User-Frame Calibration Repeatability (Pagani et al. 2021, peer-reviewed):** Compare vision-based (fiducial marker) and rigid-marker calibration methods. Measure positioning repeatability at multiple calibrated points. Report repeatability for 3-point (0.33 mm), 5-point (0.12 mm), and vision-based (1.42 mm) methods against a reference repeatability (0.08 mm). Arm tested: Rethink Robotics Sawyer (pagani2021cobotuserframe pages 1-2).

**D. Mobile Base Positioning (Hifi et al. 2025, peer-reviewed):** Use a Leica laser tracker (10 µm tracking precision) and Vicon orientation reference. Test strafing and rotational movements between 1 m-spaced targets at multiple speeds, with and without feature mapping, over ten runs each. Report mean displacement error and standard deviation. Arm/base tested: KUKA KMR iiwa (hifi2025aquantitativeinvestigation pages 10-11, hifi2025aquantitativeinvestigation pages 4-5).

**E. Collision Force/Pressure (Mariano et al. 2026, peer-reviewed):** Use a CoboSafe biofidelic measurement system. Create collision scenarios between the arm's end effector and measurement head simulating human body regions. Evaluate per ISO/TR 14121-2:2013 risk-graph method. Compare measured forces and pressures against ISO/TS 15066 biomechanical limits. Arms tested: UR5e, UR10e (mariano2026roboticsafetyin pages 7-7, mariano2026roboticsafetyin pages 10-11).

**F. Dial-Indicator Repeatability (Chebly et al. 2025, preprint):** Use a Westward 4KU81 dial indicator. Command repeated point-to-point motions at motor speeds from 500 to 2500 steps/s. Report standard deviation of measured displacement. Arm tested: Forte (chebly2025strongaccurateand pages 6-7).

---

## 8. Conclusions

The published literature provides several lines of evidence suggesting that low-cost arms face significant challenges for SDL deployment:

1. **Repeatability gap:** Industrial SDL arms offer 0.03–0.1 mm repeatability; low-cost arms typically deliver 0.2–0.6 mm, with some configurations described as "severely limited" (rupp2022establishmentoflowcost pages 6-7). This 3–10× difference may be tolerable for coarse tasks but problematic for pipette-tip insertion, instrument-holder vial placement, or balance tending.

2. **Reliability and error handling:** Low-cost arms may silently ignore infeasible motions (wattoo2024rabitarobot pages 6-7), lack pressure sensors to verify grasps (wattoo2024rabitarobot pages 6-7), and produce coordinate-frame errors of ~3 cm when operating alongside other devices (wattoo2024rabitarobot pages 4-6). Even industrial UR5e systems experienced 29–43% campaign failure rates from gripper communication issues (ahlquist2024improvingselfdrivinglabs pages 1-6).

3. **Safety:** No low-cost arm has undergone published collision testing. Even certified industrial cobots exceeded ISO/TS 15066 pressure limits in every tested laboratory scenario (mariano2026roboticsafetyin pages 11-12, mariano2026roboticsafetyin pages 10-11). Using an uncertified arm in a shared chemistry workspace transfers the full burden of risk assessment and safety validation to the user (valori2021validatingsafetyin pages 3-5, mariano2026roboticsafetyin pages 3-3).

4. **Hidden costs:** TCO studies show that the purchase price is a minor fraction of total robot system cost, with operator time, spare parts, energy, integration, and maintenance dominating (landscheidt2016methodforassessing pages 3-5). A $200 arm requiring extensive custom integration may not be cheaper over its lifecycle than a $30k arm with an established ecosystem.

5. **No published validation exists** for AgileX PiPER or SO-101 in any SDL or laboratory automation context. The literature provides no basis for claiming these arms are suitable—or unsuitable—for the described tasks; the evidence simply does not exist.

The strongest recommendation from this review is that any group deploying a low-cost arm as an automated manual manipulator should publish the repeatable benchmarks described in Section 7, thereby creating the comparative evidence that the field currently lacks.


References

1. (burger2023amobilerobotic pages 52-56): Benjamin Burger. A mobile robotic researcher. ArXiv, Jan 2023. URL: https://doi.org/10.17638/03087073, doi:10.17638/03087073. This article has 4 citations.

2. (valori2021validatingsafetyin pages 19-20): Marcello Valori, Adriano Scibilia, Irene Fassi, José Saenz, Roland Behrens, Sebastian Herbster, Catherine Bidard, Eric Lucet, Alice Magisson, Leendert Schaake, Jule Bessler, Gerdienke B. Prange-Lasonder, Morten Kühnrich, Aske B. Lassen, and Kurt Nielsen. Validating safety in human-robot collaboration: standards and new perspectives. Robotics, 10:65, Apr 2021. URL: https://doi.org/10.3390/robotics10020065, doi:10.3390/robotics10020065. This article has 153 citations.

3. (valori2021validatingsafetyin pages 3-5): Marcello Valori, Adriano Scibilia, Irene Fassi, José Saenz, Roland Behrens, Sebastian Herbster, Catherine Bidard, Eric Lucet, Alice Magisson, Leendert Schaake, Jule Bessler, Gerdienke B. Prange-Lasonder, Morten Kühnrich, Aske B. Lassen, and Kurt Nielsen. Validating safety in human-robot collaboration: standards and new perspectives. Robotics, 10:65, Apr 2021. URL: https://doi.org/10.3390/robotics10020065, doi:10.3390/robotics10020065. This article has 153 citations.

4. (salazarvillacis2026theadeptframework pages 3-4): Pablo Salazar-Villacis and Brahim Benyahia. The adept framework for assessing autonomous laboratory robotics. Communications Chemistry, Feb 2026. URL: https://doi.org/10.1038/s42004-026-01932-9, doi:10.1038/s42004-026-01932-9. This article has 18 citations and is from a peer-reviewed journal.

5. (mariano2026roboticsafetyin pages 10-11): Edy Mariano, Maël Löwensberg, Théo Bloesch, Giuseppe Tommaso Costanzo, and Pascal Miéville. Robotic safety in self-driving laboratories. SLAS Technology, 42:100463, Nov 2026. URL: https://doi.org/10.1016/j.slast.2026.100463, doi:10.1016/j.slast.2026.100463. This article has 1 citations and is from a peer-reviewed journal.

6. (mariano2026roboticsafetyin pages 7-7): Edy Mariano, Maël Löwensberg, Théo Bloesch, Giuseppe Tommaso Costanzo, and Pascal Miéville. Robotic safety in self-driving laboratories. SLAS Technology, 42:100463, Nov 2026. URL: https://doi.org/10.1016/j.slast.2026.100463, doi:10.1016/j.slast.2026.100463. This article has 1 citations and is from a peer-reviewed journal.

7. (ahlquist2024improvingselfdrivinglabs pages 1-6): Maxwell Ahlquist. Improving self-driving labs: quantifying system-level experiment repeatability and broadening instrument-level compatibility. ArXiv, Oct 2024. URL: https://doi.org/10.2172/2459394, doi:10.2172/2459394. This article has 1 citations.

8. (sulaiman2026kinematicanalysisand pages 6-9): Shifa Sulaiman, Tobias Busk Jensen, Stefan Hein Bengtson, and Simon Bøgh. Kinematic analysis and integration of vision algorithms for a mobile manipulator employed inside a self-driving laboratory. International Journal of Intelligent Robotics and Applications, 10:584-600, Jan 2026. URL: https://doi.org/10.1007/s41315-025-00518-3, doi:10.1007/s41315-025-00518-3. This article has 5 citations and is from a peer-reviewed journal.

9. (valori2021validatingsafetyin pages 5-6): Marcello Valori, Adriano Scibilia, Irene Fassi, José Saenz, Roland Behrens, Sebastian Herbster, Catherine Bidard, Eric Lucet, Alice Magisson, Leendert Schaake, Jule Bessler, Gerdienke B. Prange-Lasonder, Morten Kühnrich, Aske B. Lassen, and Kurt Nielsen. Validating safety in human-robot collaboration: standards and new perspectives. Robotics, 10:65, Apr 2021. URL: https://doi.org/10.3390/robotics10020065, doi:10.3390/robotics10020065. This article has 153 citations.

10. (wattoo2024rabitarobot pages 6-7): Zainab Saeed Wattoo, Petal Vitis, Ruizhe Zhu, Noah Depner, Ivory Zhang, Jason Hein, Arpan Gujarati, and Margo Seltzer. Rabit, a robot arm bug intervention tool for self-driving labs. 2024 54th Annual IEEE/IFIP International Conference on Dependable Systems and Networks (DSN), pages 353-361, Jun 2024. URL: https://doi.org/10.1109/dsn58291.2024.00043, doi:10.1109/dsn58291.2024.00043. This article has 2 citations.

11. (wattoo2024rabitarobot pages 1-2): Zainab Saeed Wattoo, Petal Vitis, Ruizhe Zhu, Noah Depner, Ivory Zhang, Jason Hein, Arpan Gujarati, and Margo Seltzer. Rabit, a robot arm bug intervention tool for self-driving labs. 2024 54th Annual IEEE/IFIP International Conference on Dependable Systems and Networks (DSN), pages 353-361, Jun 2024. URL: https://doi.org/10.1109/dsn58291.2024.00043, doi:10.1109/dsn58291.2024.00043. This article has 2 citations.

12. (wolf2022towardsroboticlaboratory pages 12-16): Ádám Wolf, David A. Wolton, Josef Trapl, Julien Janda, Stefan Romeder-Finger, Thomas Gatternig, Jean-Baptiste Farcet, Péter Galambos, and Károly Széll. Towards robotic laboratory automation plug &amp; play: the “lapp” framework. SLAS Technology, 27:18-25, Feb 2022. URL: https://doi.org/10.1016/j.slast.2021.11.003, doi:10.1016/j.slast.2021.11.003. This article has 59 citations and is from a peer-reviewed journal.

13. (rupp2022establishmentoflowcost pages 2-3): Nicole Rupp, Katrin Peschke, Michael Köppl, David Drissner, and Thole Zuchner. Establishment of low-cost laboratory automation processes using autoit and 4-axis robots. SLAS Technology, 27:312-318, Oct 2022. URL: https://doi.org/10.1016/j.slast.2022.07.001, doi:10.1016/j.slast.2022.07.001. This article has 30 citations and is from a peer-reviewed journal.

14. (rupp2022establishmentoflowcost pages 4-5): Nicole Rupp, Katrin Peschke, Michael Köppl, David Drissner, and Thole Zuchner. Establishment of low-cost laboratory automation processes using autoit and 4-axis robots. SLAS Technology, 27:312-318, Oct 2022. URL: https://doi.org/10.1016/j.slast.2022.07.001, doi:10.1016/j.slast.2022.07.001. This article has 30 citations and is from a peer-reviewed journal.

15. (rupp2022establishmentoflowcost pages 6-7): Nicole Rupp, Katrin Peschke, Michael Köppl, David Drissner, and Thole Zuchner. Establishment of low-cost laboratory automation processes using autoit and 4-axis robots. SLAS Technology, 27:312-318, Oct 2022. URL: https://doi.org/10.1016/j.slast.2022.07.001, doi:10.1016/j.slast.2022.07.001. This article has 30 citations and is from a peer-reviewed journal.

16. (harazono2024evaluationofmicroplate pages 11-15): Yoritaka Harazono, Haruko Shimono, Kikumi Hata, Toutai Mitsuyama, and Takaaki Horinouchi. Evaluation of microplate handling accuracy for applying robotic arms in laboratory automation. bioRxiv, Jan 2024. URL: https://doi.org/10.1101/2023.12.29.573685, doi:10.1101/2023.12.29.573685. This article has 11 citations.

17. (harazono2024evaluationofmicroplate pages 15-20): Yoritaka Harazono, Haruko Shimono, Kikumi Hata, Toutai Mitsuyama, and Takaaki Horinouchi. Evaluation of microplate handling accuracy for applying robotic arms in laboratory automation. bioRxiv, Jan 2024. URL: https://doi.org/10.1101/2023.12.29.573685, doi:10.1101/2023.12.29.573685. This article has 11 citations.

18. (harazono2024evaluationofmicroplate pages 6-11): Yoritaka Harazono, Haruko Shimono, Kikumi Hata, Toutai Mitsuyama, and Takaaki Horinouchi. Evaluation of microplate handling accuracy for applying robotic arms in laboratory automation. bioRxiv, Jan 2024. URL: https://doi.org/10.1101/2023.12.29.573685, doi:10.1101/2023.12.29.573685. This article has 11 citations.

19. (chebly2025strongaccurateand pages 2-3): Georges Chebly, Spencer Little, Nisal Perera, Aliya Abedeen, Ken Suzuki, and Donghyun Kim. Strong, accurate, and low-cost robot manipulator. ArXiv, Jul 2025. URL: https://doi.org/10.48550/arxiv.2507.15693, doi:10.48550/arxiv.2507.15693. This article has 4 citations.

20. (wattoo2024rabitarobot pages 3-4): Zainab Saeed Wattoo, Petal Vitis, Ruizhe Zhu, Noah Depner, Ivory Zhang, Jason Hein, Arpan Gujarati, and Margo Seltzer. Rabit, a robot arm bug intervention tool for self-driving labs. 2024 54th Annual IEEE/IFIP International Conference on Dependable Systems and Networks (DSN), pages 353-361, Jun 2024. URL: https://doi.org/10.1109/dsn58291.2024.00043, doi:10.1109/dsn58291.2024.00043. This article has 2 citations.

21. (wattoo2024rabitarobot pages 4-6): Zainab Saeed Wattoo, Petal Vitis, Ruizhe Zhu, Noah Depner, Ivory Zhang, Jason Hein, Arpan Gujarati, and Margo Seltzer. Rabit, a robot arm bug intervention tool for self-driving labs. 2024 54th Annual IEEE/IFIP International Conference on Dependable Systems and Networks (DSN), pages 353-361, Jun 2024. URL: https://doi.org/10.1109/dsn58291.2024.00043, doi:10.1109/dsn58291.2024.00043. This article has 2 citations.

22. (chebly2025strongaccurateand pages 6-7): Georges Chebly, Spencer Little, Nisal Perera, Aliya Abedeen, Ken Suzuki, and Donghyun Kim. Strong, accurate, and low-cost robot manipulator. ArXiv, Jul 2025. URL: https://doi.org/10.48550/arxiv.2507.15693, doi:10.48550/arxiv.2507.15693. This article has 4 citations.

23. (huang2026vlareplicaalowcost pages 3-4): Alex Huang, Jia-Hui Zhang, Shi Tang, and Yu Xiang. Vla-replica: a low-cost, reproducible benchmark for real-world evaluation of vision-language-action models. ArXiv, May 2026. URL: https://doi.org/10.48550/arxiv.2605.20774, doi:10.48550/arxiv.2605.20774. This article has 9 citations.

24. (harazono2024evaluationofmicroplate pages 1-6): Yoritaka Harazono, Haruko Shimono, Kikumi Hata, Toutai Mitsuyama, and Takaaki Horinouchi. Evaluation of microplate handling accuracy for applying robotic arms in laboratory automation. bioRxiv, Jan 2024. URL: https://doi.org/10.1101/2023.12.29.573685, doi:10.1101/2023.12.29.573685. This article has 11 citations.

25. (mariano2026roboticsafetyin pages 3-3): Edy Mariano, Maël Löwensberg, Théo Bloesch, Giuseppe Tommaso Costanzo, and Pascal Miéville. Robotic safety in self-driving laboratories. SLAS Technology, 42:100463, Nov 2026. URL: https://doi.org/10.1016/j.slast.2026.100463, doi:10.1016/j.slast.2026.100463. This article has 1 citations and is from a peer-reviewed journal.

26. (mariano2026roboticsafetyin pages 11-12): Edy Mariano, Maël Löwensberg, Théo Bloesch, Giuseppe Tommaso Costanzo, and Pascal Miéville. Robotic safety in self-driving laboratories. SLAS Technology, 42:100463, Nov 2026. URL: https://doi.org/10.1016/j.slast.2026.100463, doi:10.1016/j.slast.2026.100463. This article has 1 citations and is from a peer-reviewed journal.

27. (mariano2026roboticsafetyin pages 1-2): Edy Mariano, Maël Löwensberg, Théo Bloesch, Giuseppe Tommaso Costanzo, and Pascal Miéville. Robotic safety in self-driving laboratories. SLAS Technology, 42:100463, Nov 2026. URL: https://doi.org/10.1016/j.slast.2026.100463, doi:10.1016/j.slast.2026.100463. This article has 1 citations and is from a peer-reviewed journal.

28. (landscheidt2016methodforassessing pages 3-5): Steffen Landscheidt and Mirka Kans. Method for assessing the total cost of ownership of industrial robots. Procedia CIRP, 57:746-751, Jan 2016. URL: https://doi.org/10.1016/j.procir.2016.11.129, doi:10.1016/j.procir.2016.11.129. This article has 59 citations and is from a peer-reviewed journal.

29. (landscheidt2016methodforassessing pages 5-6): Steffen Landscheidt and Mirka Kans. Method for assessing the total cost of ownership of industrial robots. Procedia CIRP, 57:746-751, Jan 2016. URL: https://doi.org/10.1016/j.procir.2016.11.129, doi:10.1016/j.procir.2016.11.129. This article has 59 citations and is from a peer-reviewed journal.

30. (genzen2018challengesandopportunities pages 2-3): Jonathan R Genzen, Carey-Ann D Burnham, Robin A Felder, Charles D Hawker, Giuseppe Lippi, and Octavia M Peck Palmer. Challenges and opportunities in implementing total laboratory automation. Feb 2018. URL: https://doi.org/10.1373/clinchem.2017.274068, doi:10.1373/clinchem.2017.274068. This article has 109 citations and is from a highest quality peer-reviewed journal.

31. (genzen2018challengesandopportunities pages 4-5): Jonathan R Genzen, Carey-Ann D Burnham, Robin A Felder, Charles D Hawker, Giuseppe Lippi, and Octavia M Peck Palmer. Challenges and opportunities in implementing total laboratory automation. Feb 2018. URL: https://doi.org/10.1373/clinchem.2017.274068, doi:10.1373/clinchem.2017.274068. This article has 109 citations and is from a highest quality peer-reviewed journal.

32. (khare2023impactoflife pages 3-5): Amitesh Khare, Angel Rajan Singh, Sudip Kumar Datta, Sheetal Singh, Anant Gupta, Sidhartha Satpathy, D. K. Sharma, and Ritu Gupta. Impact of life cycle costing in procurement of robotic track-based central laboratory at apex medical institute in india. Journal of Laboratory Physicians, 15:539-544, May 2023. URL: https://doi.org/10.1055/s-0043-1768634, doi:10.1055/s-0043-1768634. This article has 1 citations.

33. (jin2026commercializationpathwaysapplication pages 8-10): H Jin, J Guo, and Y Zou. Commercialization pathways, application scenarios, and development bottlenecks of embodied intelligent robots: a review. Unknown journal, 2026.

34. (jin2026commercializationpathwaysapplication pages 6-8): H Jin, J Guo, and Y Zou. Commercialization pathways, application scenarios, and development bottlenecks of embodied intelligent robots: a review. Unknown journal, 2026.

35. (carruthers2025amobilerobotic pages 24-27): S Carruthers. A mobile robotic researcher for autonomous solar fuels research. Unknown journal, 2025.

36. (hifi2025aquantitativeinvestigation pages 10-11): Amine Hifi, W Jackson, C Loukas, M Shields, A Poole, E Mohseni, S G Pierce, C N MacLeod, Gordon Dobie, T. O’Hare, G. Munro, J. O’Brian-O’Reilly, and R.W. K. Vithanage. A quantitative investigation of accuracy and repeatability for deployment of mobile collaborative robots in high-value manufacturing. Measurement Science and Technology, Aug 2025. URL: https://doi.org/10.1088/1361-6501/adf3d4, doi:10.1088/1361-6501/adf3d4. This article has 2 citations and is from a domain leading peer-reviewed journal.

37. (hifi2025aquantitativeinvestigation pages 1-3): Amine Hifi, W Jackson, C Loukas, M Shields, A Poole, E Mohseni, S G Pierce, C N MacLeod, Gordon Dobie, T. O’Hare, G. Munro, J. O’Brian-O’Reilly, and R.W. K. Vithanage. A quantitative investigation of accuracy and repeatability for deployment of mobile collaborative robots in high-value manufacturing. Measurement Science and Technology, Aug 2025. URL: https://doi.org/10.1088/1361-6501/adf3d4, doi:10.1088/1361-6501/adf3d4. This article has 2 citations and is from a domain leading peer-reviewed journal.

38. (hifi2025aquantitativeinvestigation pages 3-4): Amine Hifi, W Jackson, C Loukas, M Shields, A Poole, E Mohseni, S G Pierce, C N MacLeod, Gordon Dobie, T. O’Hare, G. Munro, J. O’Brian-O’Reilly, and R.W. K. Vithanage. A quantitative investigation of accuracy and repeatability for deployment of mobile collaborative robots in high-value manufacturing. Measurement Science and Technology, Aug 2025. URL: https://doi.org/10.1088/1361-6501/adf3d4, doi:10.1088/1361-6501/adf3d4. This article has 2 citations and is from a domain leading peer-reviewed journal.

39. (pagani2021cobotuserframe pages 1-2): Roberto Pagani, Cristina Nuzzi, Marco Ghidelli, Alberto Borboni, Matteo Lancini, and Giovanni Legnani. Cobot user frame calibration: evaluation and comparison between positioning repeatability performances achieved by traditional and vision-based methods. Robotics, 10:45, Mar 2021. URL: https://doi.org/10.3390/robotics10010045, doi:10.3390/robotics10010045. This article has 33 citations.

40. (hifi2025aquantitativeinvestigation pages 4-5): Amine Hifi, W Jackson, C Loukas, M Shields, A Poole, E Mohseni, S G Pierce, C N MacLeod, Gordon Dobie, T. O’Hare, G. Munro, J. O’Brian-O’Reilly, and R.W. K. Vithanage. A quantitative investigation of accuracy and repeatability for deployment of mobile collaborative robots in high-value manufacturing. Measurement Science and Technology, Aug 2025. URL: https://doi.org/10.1088/1361-6501/adf3d4, doi:10.1088/1361-6501/adf3d4. This article has 2 citations and is from a domain leading peer-reviewed journal.