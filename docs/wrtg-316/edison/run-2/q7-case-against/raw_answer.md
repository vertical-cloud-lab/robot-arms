
# The Case Against Low-Cost Robot Arms as Automated Manual Manipulators in Self-Driving Laboratories

## Summary

This review synthesizes peer-reviewed evidence and flagged preprints (2015–2026) on whether low-cost robot arms (e.g., AgileX PiPER, SO-101, Dobot Magician) are suitable for use as automated manual manipulators in self-driving laboratories (SDLs) for materials science, compared with the industry-standard arms (KUKA LBR iiwa, UR5e/UR3e, Franka Panda) that dominate published SDL platforms. The evidence is organized into six dimensions: (1) positional accuracy and repeatability, (2) reliability and durability, (3) safety and certification, (4) hidden integration and total cost of ownership, (5) mobile-manipulator station-to-station performance, and (6) the absence of published evidence for specific low-cost arms. **A critical finding is that no peer-reviewed, head-to-head benchmark of a low-cost arm against an industrial arm on standardized SDL tasks currently exists.** Most evidence is indirect, drawn from separate studies of different arms in different contexts.

The following table summarizes the arms, their specifications, and their validation status in published laboratory workflows.

| Arm model | DOF | Repeatability reported by manufacturer or paper | Approx. arm price (USD, hardware only) | Payload | Safety/certification status | Validation in a published SDL or laboratory workflow |
|---|---:|---:|---:|---:|---|---|
| **KUKA LBR iiwa 14** | 7 | ±0.1 mm; station calibration located a reference cube within 0.12 mm after deliberately adding ±15 mm and ±2.5° initial error (pqac-00000034, pqac-00000055) | ≈$70k–$100k arm; KMR mobile system substantially more | 14 kg | Industrial collaborative arm with safety-rated torque sensing; the completed cell still requires application-specific risk assessment under ISO 10218/ISO/TS 15066 (pqac-00000020, pqac-00000023) | **Yes.** KUKA KMR iiwa mobile chemist completed 688 experiments over eight days; later KUKA systems were used for exploratory synthetic chemistry (pqac-00000034, pqac-00000028) |
| **Universal Robots UR5e** | 6 | ±0.03 mm nominal; published SDL pages reviewed did not independently verify this specification | ≈$30k–$40k | 5 kg | Collaborative industrial arm with safety-rated functions; not inherently safe after adding grippers, tools, or chemicals. UR5e/UR10e laboratory collision tests exceeded pressure limits in every tested scenario even at restrictive settings (pqac-00000025, pqac-00000066, pqac-00000067) | **Yes.** Used on a linear rail in the MARS SDL and on a Ridgeback mobile base; MARS reported pick/place as its principal failure source and 29–43% campaign failure from gripper communication faults (pqac-00000008, pqac-00000031, pqac-00000046) |
| **Universal Robots UR3e** | 6 | ±0.03 mm nominal; no independent arm-level metrology located in the reviewed SDL literature | ≈$25k–$35k | 3 kg | Collaborative industrial arm with configurable safety functions; final tooling and cell require separate validation (pqac-00000020, pqac-00000024) | **Yes.** Used in the Hein laboratory and represented in RABIT’s SDL safety evaluation; MATTERIX also includes a UR3e (pqac-00000043, pqac-00000045) |
| **Franka Emika Panda / Franka Research 3** | 7 | ±0.1 mm nominal | ≈$20k–$35k | 3 kg | Torque-sensing collaborative research arm, but complete-cell conformity and collision validation remain the integrator’s responsibility (pqac-00000023, pqac-00000024) | **Yes.** Used in ARChemist/MATTERIX-related chemistry automation and paired with a laboratory gripper reporting ≤1% grasp failures (pqac-00000028, pqac-00000029) |
| **Dobot Magician** | 4 | 0.2 mm nominal (pqac-00000037) | ≈$1.2k–$2k | 0.5 kg | Educational/desktop arm; no evidence located of ISO 10218/ISO/TS 15066 safety-rated functions or certification for barrier-free collaborative laboratory use | **Laboratory workflow: yes; full SDL: no.** Operated an electronic pipette, AAS autosampler, and inoculation loop. Automated pipetting agreed statistically with manual work, but cycles were about 3.5× slower and inoculation repeatability was described as “severely limited” (pqac-00000036, pqac-00000038) |
| **Dobot M1 Pro** | 4 | ±0.02 mm nominal; loaded plate-transfer IQR was 0.020 mm in x and 0.006 mm in y at full speed (pqac-00000004) | ≈$3k–$5k | 1.5 kg | Desktop SCARA; no evidence located of safety-rated collaborative functions equivalent to certified industrial cobots | **Laboratory benchmark only; not an SDL.** A **preprint** tested 125 loaded microplate transfers at each speed and 125 lid placements per imposed-offset condition using digital gauges and video/OpenCV scoring (pqac-00000004, pqac-00000005, pqac-00000006) |
| **Niryo Ned2** | 6 | 0.5 mm reported in a low-cost-arm comparison (pqac-00000000) | ≈$4k–$6k | 0.3 kg | Educational/research arm; no safety-rated PFL/SSM certification established in the reviewed publications | **SDL safety testbed only.** RABIT used Ned2 with ViperX as lower-precision surrogates for a UR3e; Ned2 halted on infeasible motion, unlike ViperX’s silent failure (pqac-00000043, pqac-00000048) |
| **Trossen ViperX 300** | 6 | Not quantitatively reported in the reviewed SDL paper; described as having limited precision (pqac-00000048) | ≈$3k–$5k | ≈0.75 kg, configuration-dependent | Research arm; no evidence located of industrial collaborative safety certification | **SDL safety testbed only.** It collided with Ned2 without RABIT raising an alarm; global-frame transformation produced about 3 cm mean error. It could also silently ignore infeasible trajectories (pqac-00000043, pqac-00000047) |
| **Forte open-source arm** | 6 | 0.467 mm summary value; dial-indicator tests gave 0.286–0.587 mm standard deviation across 500–2500 steps/s (pqac-00000000, pqac-00000001) | $212 material cost | 0.63 kg | **Preprint prototype** without documented industrial functional-safety certification | **No.** Validated only as a low-cost manipulation prototype; no published chemistry/materials SDL deployment or long-duration reliability study was located |
| **LeRobot SO-101** | 6 | No independently verified Cartesian repeatability value located; published work identifies STS3215 servos but does not establish laboratory-grade accuracy (pqac-00000049) | ≈$100–$250 per follower arm; ≈$1,050 for the cited complete benchmark cell | Not established by a peer-reviewed payload test | Educational/open research platform; no documented safety-rated controller, PFL validation, or industrial certification | **No.** A **2026 preprint** uses SO-101 in a reproducible vision-language-action benchmark, not an SDL; no published pipetting, powder dosing, balance tending, durability, or cost-per-task validation was located (pqac-00000049) |
| **AgileX PiPER** | 6 | Commonly advertised as approximately ±0.1 mm, but no independent peer-reviewed verification located | ≈$2k–$3k | ≈1.5 kg nominal | No peer-reviewed evidence located establishing ISO 10218/ISO/TS 15066 safety-rated functions or certification for shared laboratory operation | **No published evidence located.** No peer-reviewed SDL study, loaded station-recalibration benchmark, long-duration reliability test, chemical-compatibility study, or cost-per-successful-task comparison against UR, Franka, ABB, Kinova, or KUKA arms was found |


*Table: Comparison of industrial, collaborative, and low-cost arms by performance, price, payload, safety status, and published laboratory validation. Prices and uncited nominal specifications are approximate and should be verified with current manufacturer documentation.*

---

## 1. Positional Accuracy and Repeatability

### 1.1 The Industrial Baseline

The KUKA LBR iiwa, the arm used in the seminal Burger et al. (2020) mobile robotic chemist, has a manufacturer-specified repeatability of ±0.1 mm. In Burger's thesis, a six-point calibration procedure located a reference calibration cube within 0.12 mm and corrected orientation offsets to less than 0.005°, even after deliberately introducing ±15 mm translational and ±2.5° rotational noise to the initial position estimate (pqac-00000034, pqac-00000055). This system completed 688 experiments autonomously over eight days (pqac-00000034).

The UR5e (±0.03 mm nominal repeatability) and Franka Emika Panda (±0.1 mm nominal) are the other most-cited SDL arms (pqac-00000028, pqac-00000031). However, no independent metrology study in the reviewed SDL literature verified these manufacturer specifications under loaded laboratory conditions.

### 1.2 Low-Cost Arm Measurements

**Dobot Magician (4-DOF, ~$1.5k):** Manufacturer-specified position repeatability is 0.2 mm (pqac-00000037). Rupp et al. (2022, *SLAS Technology*, DOI: 10.1016/j.slast.2022.07.001) demonstrated that the Dobot Magician could operate an electronic pipette to transfer 20 µL and 100 µL aliquots of lissamine green into 96-well plates with "no significant differences in accuracy and precision" compared to manual operation by a trained researcher (pqac-00000036). However, the same study found that automated processes were approximately 3.5× slower than manual pipetting and that repeatability was "severely limited" in a bacterial inoculation task where the inoculation loop extended the robot axis (pqac-00000038). No formal positional-accuracy metrology (e.g., laser tracker, dial gauge under load) was reported.

**Protocol (Rupp et al. 2022):** Lissamine green dilutions transferred from 1.5 mL tubes to 96-well plates using a BRAND electronic micropipette. Volumes: 20 µL (multi-dispense) and 100 µL (single pipette). Comparison: absorbance readings (automated vs. manual). Measuring tool: plate reader absorbance. Number of trials: not explicitly stated per condition. Success criterion: no statistically significant difference in mean absorbance. Arm: Dobot Magician on a linear rail with 3D-printed PLA pipette holder and linear solenoid actuator (pqac-00000036, pqac-00000037).

**Dobot M1 Pro (4-DOF SCARA, ~$3–5k):** Harazono et al. (2024, **preprint**, bioRxiv, DOI: 10.1101/2023.12.29.573685) measured loaded microplate-transfer repeatability using digital dial gauges (DGN-125B) on an aluminum-frame platform. Over 125 repetitions at full speed, the interquartile range (IQR) was 0.020 mm in x and 0.006 mm in y; at 50% speed, IQR was 0.034 mm (x) and 0.014 mm (y) (pqac-00000004). Lid-placement tolerance was tested by introducing artificial offsets (Δx = 1.80–2.30 mm, Δy = 2.10–2.20 mm), with 125 trials per condition. Success was scored from video analysis using OpenCV and colored circular stickers. Transfer success declined gradually with increasing x-offset and dropped significantly when Δy exceeded 2.190 mm (pqac-00000005). This preprint explicitly notes that manufacturer repeatability specs (measured unloaded, per ISO 9283) may not predict performance under realistic laboratory loads (pqac-00000011, pqac-00000039).

**Forte (6-DOF, ~$212 material cost, preprint):** Chebly et al. (2025, arXiv, DOI: 10.48550/arxiv.2507.15693) measured repeatability using a Westward 4KU81 dial indicator. Standard deviations ranged from 0.286 mm at 500 steps/s to 0.587 mm at 2500 steps/s (pqac-00000001). The comparison table in this preprint lists Niryo Ned2 at 0.5 mm repeatability and WLKATA Mirobot at 0.2 mm, but Dobot Magician's repeatability was listed as not reported (pqac-00000000). The paper describes Forte's performance as "near industrial-grade" but provides no laboratory task validation.

**SO-101 (~$100–250):** The VLA-Replica benchmark (Huang et al. 2026, arXiv, DOI: 10.48550/arxiv.2605.20774, **preprint**) uses SO-101 arms with STS3215 Dynamixel servos. The complete benchmark cell costs approximately $1,050. The paper identifies servo motor variability across differently constructed SO-101 arms as a concern, noting that "an inaccurate grasp pose can cause the object" to fail tasks (pqac-00000049). No Cartesian repeatability, loaded accuracy, or laboratory-task validation was reported.

**Key gap:** No published study directly compares a low-cost arm (Dobot, Forte, SO-101, or PiPER) against a UR5e, Franka, or KUKA on the same laboratory task with the same protocol and measuring instruments.

---

## 2. Reliability, Durability, and Failure Modes

### 2.1 Industrial Arm Failures in SDLs

Even industrial arms experience significant reliability challenges in SDL operations. Ahlquist (2024, DOE OSTI report, DOI: 10.2172/2459394) reported that in the MARS SDL (UR5e on a linear rail), "the robotic arm's labware pick-and-place operation was identified as the principal source of experiment failures." A compliant 3D-printed plastic gripper produced inconsistent placement and was replaced with a rigid aluminum gripper. Communication errors with an OnRobot gripper caused campaigns to hang indefinitely, with 29–43% of campaigns failing before completion depending on campaign length (pqac-00000046, pqac-00000008).

### 2.2 Low-Cost Arm Failure Modes

Wattoo et al. (2024, IEEE DSN, DOI: 10.1109/dsn58291.2024.00043) documented failure modes in the RABIT SDL safety testbed using ViperX and Niryo Ned2 as low-cost surrogates for a UR3e. Critical findings include:

- **Silent failure:** "ViperX also silently ignored infeasible motions when trajectory computation failed, potentially causing later collisions, whereas Ned2 threw an exception and halted" (pqac-00000043). This behavioral difference between low-cost arms—one silently failing, one halting—illustrates the unpredictability of non-standardized error handling.
- **Collision without detection:** In a two-arm scenario, "ViperX and Ned2 were positioned near one another and collided, yet RABIT did not raise an alarm." Global-frame coordinate transformation produced an average 3 cm positional error due to "different vendors, gripper sizes, low precision, and coordinate-system incompatibility" (pqac-00000047).
- **Limited detection:** Of 16 introduced unsafe program changes, RABIT initially detected only 50%, rising to 75–81% after modifications (pqac-00000043).

Rupp et al. (2022) reported that Dobot Magician repeatability was "severely limited" in a bacterial inoculation task, apparently because the inoculation loop extended the robot axis beyond the arm's inherent accuracy envelope (pqac-00000038).

**Key gap:** No published long-term durability study (e.g., mean time between failures over thousands of hours) exists for any low-cost arm in continuous laboratory operation.

---

## 3. Safety and Certification

### 3.1 Regulatory Framework

Collaborative robots in shared workspaces are governed by ISO 10218-1/2 (industrial robot safety), ISO/TS 15066 (collaborative robot guidance), and in Europe, the Machinery Directive 2006/42/EC (now superseded by Regulation (EU) 2023/1230) (pqac-00000020, pqac-00000022, pqac-00000023). A robot arm alone is typically "partly completed machinery"—the integrator bears responsibility for the completed cell, including application-specific risk assessment (pqac-00000023). Valori et al. (2021, *Robotics*, DOI: 10.3390/robotics10020065) warn that "low weight, ease of use, or a friendly appearance does not itself ensure safety and that inexperienced users may wrongly assume a collaborative robot is inherently safe" (pqac-00000024).

### 3.2 Even Certified Cobots Exceed Safety Limits

Mariano et al. (2026, *SLAS Technology*, DOI: 10.1016/j.slast.2026.100463) performed collision force and pressure measurements on UR5e and UR10e arms using a CoboSafe measurement system in the Swiss Cat+ West Hub automated analytical laboratory. The study found that "pressure limits were exceeded in every evaluated collision scenario even with the robot's most restrictive safety settings" (pqac-00000025, pqac-00000065, pqac-00000067). End-effector geometry was identified as a potentially dominant determinant of injury severity (pqac-00000067). In chemistry laboratories, even low-energy collisions can cause "spills, contamination events, or sample loss" (pqac-00000067). Sixteen hazards were identified, with robot–human collisions and chemical exposure rated most critical (pqac-00000069).

### 3.3 Implications for Low-Cost Arms

If even certified collaborative robots (UR5e/UR10e) with built-in safety-rated torque sensing and power-and-force-limiting modes exceed ISO/TS 15066 pressure thresholds, low-cost arms—which lack safety-rated controllers, certified torque sensors, and validated collision-detection hardware—present substantially greater uncharacterized risk in shared laboratory spaces. No published evidence was found establishing that any low-cost arm (AgileX PiPER, SO-101, Dobot Magician, Forte, or similar) has undergone collision force/pressure testing, safety-rated monitored stop validation, or any equivalent safety certification process for barrier-free laboratory use.

**Protocol (Mariano et al. 2026):** Force and pressure measured using CoboSafe Force and Pressure Measurement System, designed to reproduce biomechanical characteristics of human body regions. Risk evaluated per ISO/TR 14121-2:2013 risk-graph method. Arms tested: UR5e and UR10e (Universal Robots). Hazard scenarios included transient head impacts and static upper-body crushing. Success criterion: collision forces and pressures below ISO/TS 15066 biomechanical limits. Result: limits exceeded in every scenario tested (pqac-00000066, pqac-00000067).

---

## 4. Hidden Integration Costs and Total Cost of Ownership

### 4.1 Purchase Price Is a Poor Proxy for Total Cost

Landscheidt and Kans (2016, *Procedia CIRP*, DOI: 10.1016/j.procir.2016.11.129) developed a TCO model for industrial robots based on expert interviews at a robot manufacturer and two large customers. Their analysis of arc-welding robots over five years found that operator wages, spare parts, and energy consumption together accounted for over 75% of total quantitative costs. The simplified TCO equation is: TCO = Σ(Initial price) + Σ(Operator's wages) + Σ(Spare parts) + Σ(Energy consumption) (pqac-00000063, pqac-00000064).

Genzen et al. (2018, *Clinical Chemistry*, DOI: 10.1373/clinchem.2017.274068) emphasized that laboratory automation implementation costs extend far beyond equipment purchase to include "remodeling or adapting constrained laboratory space, addressing floor load capacity, ventilation, heat, noise, waste disposal, electrical supply and backup," as well as staffing, training, vendor service, spare parts, and downtime prevention (pqac-00000014). They note that "ongoing maintenance, which may represent a significant percentage of the purchase price each year," must be included in total cost justification (pqac-00000015).

Khare et al. (2023, *J. Laboratory Physicians*, DOI: 10.1055/s-0043-1768634) demonstrated in a 10-year lifecycle analysis of robotic track-based laboratories that the vendor with the lowest initial equipment price did not have the lowest lifecycle cost—Vendor C had the lowest equipment price (Rs. 14.98 crore) but Vendor D had the lowest 10-year lifecycle cost (Rs. 111.22 crore vs. Rs. 130.85 crore for the initially selected vendor) (pqac-00000012).

### 4.2 Integration Costs for Low-Cost Arms

Jin et al. (2026) argue that lifecycle assessment should include "acquisition, site preparation, integration, training, supervision, energy, consumables, planned and unplanned maintenance, software, insurance, and eventual decommissioning" and that "excessive specialization can turn every sale into a new engineering project" (pqac-00000059, pqac-00000060). Wolf et al. (2022, *SLAS Technology*, DOI: 10.1016/j.slast.2021.11.003) note that laboratory robot systems require "comprehensive integration work, careful layout and device placement, and often custom frames rather than standard laboratory benches" (pqac-00000018).

**Key implication for low-cost arms:** A $200 SO-101 or $2,000 PiPER may cost far less to purchase, but the integration engineering—custom grippers, 3D-printed fixtures, camera calibration, software development, safety enclosures, and ongoing debugging—may equal or exceed the cost of an industrial arm whose ecosystem provides validated grippers, documented APIs, safety controllers, and vendor support. **No published study quantifies the integration cost of deploying a low-cost arm in an SDL, so this remains an important but unverified concern.**

---

## 5. Mobile Manipulator Station-to-Station Performance

The user's use case—an arm moving between stations and recalibrating at each using fiducial targets—mirrors the mobile manipulator paradigm. Evidence shows this is challenging even with industrial hardware:

- **KUKA KMR iiwa** mobile base returns to pre-recorded positions with approximately 10 mm translational and 0.5° rotational precision using 2D laser scanners—explicitly insufficient for manipulating small objects without additional calibration (pqac-00000051).
- Hifi et al. (2025, *Measurement Science and Technology*, DOI: 10.1088/1361-6501/adf3d4) measured KUKA KMR iiwa positioning with a Leica laser tracker (10 µm precision). Without feature mapping, encoder-only strafing error grew from 3.00 mm to 30.03 mm over ten runs; rotational error grew from 17.91 mm to 177.31 mm. With mapping enabled, errors dropped to approximately 1.6–4.4 mm for strafing and 1.9–6.7 mm for rotation, depending on speed (pqac-00000052). Repeatability errors were under 7 mm with mapping and approximately 2.5 mm in practical scenarios (pqac-00000053).
- Another cited study found that relying solely on SLAM left a dual-arm mobile robot 50–100 mm out of position; adding AR Tags and vision reduced errors to ≤10 mm (pqac-00000054).
- Burger's KUKA KMR used a touch-based six-point calibration at each station to achieve sub-0.12 mm accuracy after navigation (pqac-00000055), but this relied on the arm's native 0.1 mm repeatability to execute the calibration procedure itself.

**Implication:** A low-cost arm with 0.5–2 mm repeatability, mounted on a low-cost mobile base with ≥10 mm navigation uncertainty, compounds both error sources. Without the mechanical precision to perform a reliable calibration procedure at each station, the entire system accuracy may be insufficient for tasks like pipette tip insertion, vial placement in instrument holders, or balance tending.

---

## 6. Explicit Gaps in Published Evidence

The following specific gaps were identified:

1. **No peer-reviewed study of AgileX PiPER in any laboratory context** was found. No repeatability metrology, loaded accuracy test, chemical compatibility assessment, long-duration reliability study, or cost-per-task comparison exists in the indexed literature.

2. **No peer-reviewed study of SO-101 in any laboratory automation context** was found. The only publication using SO-101 (Huang et al. 2026) is a preprint for vision-language-action model benchmarking, not laboratory science (pqac-00000049).

3. **No published head-to-head comparison** of a low-cost arm against an industrial arm on the same standardized laboratory task (pipetting, plate handling, powder dosing, balance tending, vial transport) using the same protocol and measurement instruments exists.

4. **No published long-term durability or MTBF study** for any low-cost arm in continuous laboratory operation (24/7 SDL mode) was found.

5. **No published cost-per-successful-task analysis** comparing low-cost and industrial arms was found.

6. **No published safety (force/pressure) testing** of any low-cost arm was found—this gap is particularly concerning given that even certified UR5e/UR10e cobots exceeded ISO/TS 15066 pressure limits in laboratory collision scenarios (pqac-00000065, pqac-00000067).

7. **No published study of fiducial-based recalibration (AprilTag or similar)** at multiple stations using a low-cost arm was found, though the concept is well-established for industrial mobile manipulators (pqac-00000055).

---

## 7. Repeatable Benchmark Protocols from the Literature

For researchers seeking to validate an affordable arm, the following published protocols can be adapted:

**A. Microplate Transfer Repeatability (Harazono et al. 2024, preprint):** Construct an aluminum-frame platform with digital dial gauges (DGN-125B). Mount a 96-well microplate on the gripper. Repeatedly transfer the plate to a measurement position (path: P1→P2→P3→P2→P1) for 125 repetitions at each of two speeds. Record x and y displacement via gauge-to-spreadsheet communication at 2 s intervals. Report IQR. Test lid-placement tolerance by introducing controlled offsets (1.80–2.30 mm in x, 2.10–2.20 mm in y) over 125 trials per condition; score success/failure from video using OpenCV. Arm tested: Dobot M1 Pro (pqac-00000004, pqac-00000005, pqac-00000006).

**B. Pipetting Accuracy (Rupp et al. 2022, peer-reviewed):** Mount an electronic micropipette on the arm using a 3D-printed holder with a solenoid actuator. Transfer lissamine green dilutions from 1.5 mL tubes to 96-well plates at 20 µL (multi-dispense) and 100 µL (single pipette). Measure absorbance. Compare automated vs. manual results. Report mean, SD, and statistical significance. Arm tested: Dobot Magician (pqac-00000036, pqac-00000037).

**C. User-Frame Calibration Repeatability (Pagani et al. 2021, peer-reviewed):** Compare vision-based (fiducial marker) and rigid-marker calibration methods. Measure positioning repeatability at multiple calibrated points. Report repeatability for 3-point (0.33 mm), 5-point (0.12 mm), and vision-based (1.42 mm) methods against a reference repeatability (0.08 mm). Arm tested: Rethink Robotics Sawyer (pqac-00000003).

**D. Mobile Base Positioning (Hifi et al. 2025, peer-reviewed):** Use a Leica laser tracker (10 µm tracking precision) and Vicon orientation reference. Test strafing and rotational movements between 1 m-spaced targets at multiple speeds, with and without feature mapping, over ten runs each. Report mean displacement error and standard deviation. Arm/base tested: KUKA KMR iiwa (pqac-00000052, pqac-00000056).

**E. Collision Force/Pressure (Mariano et al. 2026, peer-reviewed):** Use a CoboSafe biofidelic measurement system. Create collision scenarios between the arm's end effector and measurement head simulating human body regions. Evaluate per ISO/TR 14121-2:2013 risk-graph method. Compare measured forces and pressures against ISO/TS 15066 biomechanical limits. Arms tested: UR5e, UR10e (pqac-00000066, pqac-00000067).

**F. Dial-Indicator Repeatability (Chebly et al. 2025, preprint):** Use a Westward 4KU81 dial indicator. Command repeated point-to-point motions at motor speeds from 500 to 2500 steps/s. Report standard deviation of measured displacement. Arm tested: Forte (pqac-00000001).

---

## 8. Conclusions

The published literature provides several lines of evidence suggesting that low-cost arms face significant challenges for SDL deployment:

1. **Repeatability gap:** Industrial SDL arms offer 0.03–0.1 mm repeatability; low-cost arms typically deliver 0.2–0.6 mm, with some configurations described as "severely limited" (pqac-00000038). This 3–10× difference may be tolerable for coarse tasks but problematic for pipette-tip insertion, instrument-holder vial placement, or balance tending.

2. **Reliability and error handling:** Low-cost arms may silently ignore infeasible motions (pqac-00000043), lack pressure sensors to verify grasps (pqac-00000043), and produce coordinate-frame errors of ~3 cm when operating alongside other devices (pqac-00000047). Even industrial UR5e systems experienced 29–43% campaign failure rates from gripper communication issues (pqac-00000046).

3. **Safety:** No low-cost arm has undergone published collision testing. Even certified industrial cobots exceeded ISO/TS 15066 pressure limits in every tested laboratory scenario (pqac-00000065, pqac-00000067). Using an uncertified arm in a shared chemistry workspace transfers the full burden of risk assessment and safety validation to the user (pqac-00000023, pqac-00000022).

4. **Hidden costs:** TCO studies show that the purchase price is a minor fraction of total robot system cost, with operator time, spare parts, energy, integration, and maintenance dominating (pqac-00000063). A $200 arm requiring extensive custom integration may not be cheaper over its lifecycle than a $30k arm with an established ecosystem.

5. **No published validation exists** for AgileX PiPER or SO-101 in any SDL or laboratory automation context. The literature provides no basis for claiming these arms are suitable—or unsuitable—for the described tasks; the evidence simply does not exist.

The strongest recommendation from this review is that any group deploying a low-cost arm as an automated manual manipulator should publish the repeatable benchmarks described in Section 7, thereby creating the comparative evidence that the field currently lacks.
