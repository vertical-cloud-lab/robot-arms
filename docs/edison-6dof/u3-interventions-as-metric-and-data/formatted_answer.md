Question: Context. We run a small cloud lab at BYU (the Vertical Cloud Lab) with an AgileX PiPER 6-DOF arm (about $2.5k, 1.5 kg payload, no certified safety functions), an SO-101 leader arm that teleoperates the PiPER (34 ms median command latency on the lab network), Raspberry Pi 5 wrist and fixed cameras, AprilTags, 3D-printed fixtures, and remote users who start runs from GitHub comments that launch AI-agent sessions, so the people supervising a run are often not in the room. We are preparing a pre-registered reliability campaign (at least 300 transfers per task and condition, failures coded with the LabRobFail taxonomy, mean interventions between failures as a secondary outcome). A previous literature answer found that no self-driving-lab (SDL) paper reports interventions per operation for an arm, and that recent reviews (Salazar-Villacis and Benyahia 2026, ADePT; Moran et al. 2026) call for standardized error, recovery and intervention reporting. We want to treat every human intervention as both the reliability metric and training data.

Question.
(1) Outside chemistry, how have deployed robot systems defined, counted and reported human interventions: autonomous-driving disengagements, warehouse and mobile-manipulation fleets, household and service robots, surgical and field robots, and interactive fleet learning (for example Fleet-DAgger and its "return on human effort")? Which definitions (intervention types, severity levels, time to recover, operations or hours between interventions, human effort per robot-hour) would transfer to a laboratory arm, and which standards or proposed reporting checklists exist?
(2) Human-in-the-loop and interactive imitation learning on real robots where interventions collected during deployment improved the policy (for example HG-DAgger, Sirius "robot learning on the job", HIL-SERL, RaC, intervention-weighted behavior cloning): what intervention-rate decay over time, number of interventions, final success rates and trial counts were measured, on which arms (especially low-cost arms such as SO-100/SO-101, Koch, ALOHA/ViperX, WidowX or PiPER), and has any of this been done for laboratory or SDL tasks?
(3) Remote supervision and shared autonomy: one person supervising several robots over the internet, remote takeovers by teleoperation, and the measured effect of network latency (tens to hundreds of milliseconds) on the quality of teleoperated demonstrations and corrections.
(4) Has anyone treated the intervention log of a scripted or fiducial-guided laboratory arm as training data for a learned recovery or correction policy, or compared scripted-plus-fixtures, learned, and hybrid controllers on intervention rate over a long campaign?
(5) Statistics: how should an intervention rate be estimated and compared (Poisson or negative-binomial rates, time-to-event models, learning curves and change-point detection, confidence sequences for sequential monitoring), what sample sizes are needed, and how can a campaign be pre-registered when the controller is deliberately improved during the campaign?

Prefer peer-reviewed sources from 2015 to 2026, and flag preprints. For each claim give the DOI and quote the sentence that supports it. Say explicitly where no published evidence exists.



# Human Intervention Metrics, Interactive Learning, Remote Supervision, and Statistical Design for a Laboratory Robot Reliability Campaign

## (1) Intervention Definitions and Reporting Outside Chemistry

### Autonomous-Driving Disengagements

The most mature reporting framework for human interventions is the California DMV's Autonomous Vehicle Tester Program. Under California Code of Regulations §227.38, a disengagement is defined as "deactivation of autonomous mode after an autonomous-technology failure is detected or when safe operation requires the test driver to take immediate manual control" (skokan2025coulddisengagementreports pages 2-4). Manufacturers must file monthly disengagement reports (form OL 311R) by the tenth day of each month, recording VIN, software version, GPS coordinates, initiator, cause categories, and post-event actions; separate collision reports (form OL 316) are required within ten days, and hard-braking events above 0.5 g are reported monthly (skokan2025coulddisengagementreports pages 2-4, kohanpour2025trendsinautonomous pages 4-7). 

Disengagements are classified by initiator—system-initiated (automated), driver-initiated (manual), or planned for testing—and by cause categories including perception/localization/planning errors, environmental factors, and interactions with other road users (kohanpour2025trendsinautonomous pages 1-2, kohanpour2025trendsinautonomous pages 2-4). The primary performance metric is the disengagement-to-mileage ratio (disengagements per mile or its reciprocal, miles between interventions), though the DMV does not prescribe a standard calculation formula (paz2020autonomousvehiclebenchmarking pages 1-2, banerjee2018handsoffthe pages 1-2). Banerjee et al. (2018) analyzed 1,116,605 autonomous miles, 5,328 disengagements, and 42 accidents from 144 vehicles across 12 manufacturers (banerjee2018handsoffthe pages 1-2). Paz et al. (2020) emphasized that raw disengagement counts are insufficient without normalization by distance, operating time, testing location, and number of vehicles (paz2020autonomousvehiclebenchmarking pages 1-2). Skokan and Mareček (2025) warned that "manufacturers' reporting thresholds and safety drivers' intervention decisions vary substantially," so reported rates reflect "technical performance, operating conditions, reporting practices, and individual driver risk tolerance" rather than a fully standardized safety measure (skokan2025coulddisengagementreports pages 16-18).

### Fleet Learning: Return on Human Effort (ROHE)

For robot fleets, Hoque et al. (2022) formalized Interactive Fleet Learning (IFL) and introduced ROHE as "the expected cumulative fleet reward divided by total human assistance time, with normalization by the numbers of robots and supervisors and an added one in the denominator for the zero-assistance case" (hoque2024scalablelifelongimitationa pages 64-66, hoque2022fleetdaggerinteractiverobot pages 2-4). Fleet-DAgger evaluated allocation with 100 simulated robots and a physical experiment with four ABB YuMi arms and two remote human supervisors, achieving up to 8.8× higher ROHE than baselines (hoque2022fleetdaggerinteractiverobot pages 1-2).

### Transferability to a Laboratory Arm

Several of these definitions transfer directly:

- **Disengagement-style counting**: Any moment a remote operator takes control or the system is paused maps to an AV disengagement. The LabRobFail taxonomy (preprint, Wang et al. 2026) provides a lab-specific coding scheme with five major categories—Perception Failure (PF), Grasping Failure (GF), Motion Failure (MF), Logic Failure (LF), and Safety Failure (SF)—and 11 fine-grained failure types, plus four severity levels L1–L4 (wang2026labrobfailabenchmark pages 1-2, wang2026labrobfailabenchmark pages 2-3, wang2026labrobfailabenchmark pages 4-5, wang2026labrobfailabenchmark pages 8-10).
- **Operations between interventions** (analogous to miles between disengagements) is the natural lab-arm metric: mean interventions between failures (MIBF) or its reciprocal.
- **ROHE** can be adapted: cumulative successful transfers divided by total human-supervision time.
- **Intervention sample ratio**: Sirius defined this as "the fraction of timesteps completed by humans relative to total trajectory timesteps," reporting a mean of 0.32 with SD 0.11 (liu2024robotlearningon pages 13-14).

**No published standard or reporting checklist** exists specifically for laboratory robot arms. The LabRobFail benchmark is the closest laboratory-specific framework but is simulation-based and was published as a preprint (wang2026labrobfailabenchmark pages 1-2).

## (2) Human-in-the-Loop Learning on Real Robots

The following table summarizes the major systems and their reported metrics:

| System Name | Year | Reference | Robot Arm(s) | Key Mechanism | Intervention Metric(s) Reported | Success Rate | Training Time/Data | Notes |
|---|---:|---|---|---|---|---|---|---|
| HG-DAgger | 2019 | Kelly et al., *ICRA*; DOI: 10.1109/ICRA.2019.8793698 | No manipulation arm; real autonomous-driving platform | Human initiates takeover; corrective state-action data are aggregated; uncertainty supports a learned safety threshold | Original study lacks a standard arm intervention-rate metric; later HIL-SERL comparison measured intervention rate, cycle time, and success | HIL-SERL reimplementation averaged **49.7%** success and showed no consistent intervention-rate decline (luo2025preciseanddexterous pages 14-15) | Trial and data counts not recoverable from available evidence | Foundational human-gated method, but its original real-world experiment was driving rather than arm manipulation |
| Fleet-DAgger | 2022 | Hoque et al., *CoRL/arXiv*; DOI: 10.48550/arXiv.2206.14349 **[preprint DOI]** | Four physical ABB YuMi arms; 100 simulated robots | Robot-gated allocation of scarce remote supervisors; interventions update a shared fleet policy through DAgger | **ROHE**: expected cumulative fleet reward divided by human-assistance time, normalized for fleet and supervisor counts; also completions, resets, and idle time | Up to **8.8× higher ROHE** than allocation baselines (hoque2022fleetdaggerinteractiverobot pages 1-2, hoque2022fleetdaggerinteractiverobot pages 2-4) | Physical block pushing with four arms and two remote humans; simulation with 100 robots | Physical supervisors teleoperated over the Internet, but the model assumed no switching or network latency and reported no measured latency (hoque2022fleetdaggerinteractiverobot pages 1-2, hoque2022fleetdaggerinteractiverobot pages 8-10) |
| Sirius | 2024 | Liu et al., *IJRR*; DOI: 10.1177/02783649241273901 | Franka Emika Panda with parallel-jaw gripper | Intervention-weighted behavioral cloning up-weights human demonstrations and interventions while down-weighting robot actions preceding takeover | Intervention sample ratio; interventions per trajectory; intervention duration; success by learning round | **27% improvement** over prior methods on hardware; individual deployment policies achieved **44.8–72.7%** success (liu2024robotlearningon pages 1-2, liu2024robotlearningon pages 13-14) | Mean intervention-sample ratio **0.32**; SD 0.11; range 0.19–0.57; mean **2.80 interventions per trajectory** and **15.28 timesteps per intervention** (liu2024robotlearningon pages 13-14) | Real tasks included gear insertion and coffee-pod packing; intervention decreased qualitatively across rounds, but no fitted decay constant was reported (liu2024robotlearningon pages 11-13, liu2024robotlearningon pages 7-8) |
| HIL-SERL | 2025 | Luo et al., *Science Robotics*; DOI: 10.1126/scirobotics.ads5033 | Single- and dual-arm systems; exact models not stated in the available main-text evidence | Off-policy real-world RL initialized with demonstrations; SpaceMouse corrections enter replay alongside autonomous experience | Success, cycle time, intervention rate, and intervention count versus training time | **100%** on 13 listed tasks; generally **100 evaluation trials per task**, except 10 for whole-IKEA assembly; HG-DAgger averaged 49.7% (luo2025preciseanddexterous pages 14-15, luo2025preciseanddexterous pages 12-14) | Usually **1–2.5 h**; listed tasks spanned **1–6 h**; approximately 20–30 initial demonstrations (luo2025preciseanddexterous pages 12-14, luo2025preciseanddexterous pages 8-9, luo2025preciseanddexterous pages 1-3) | Intervention rate declined to **0%** as policies converged; exact intervention counts were not tabulated in the available evidence (luo2025preciseanddexterous pages 14-15) |
| RaC | 2025 | Hu et al., *IEEE Transactions on Robotics*; DOI reported by source: 10.48550/arXiv.2509.07953 | Two 7-DOF xArm-7 manipulators with soft grippers | Every takeover deliberately contains recovery to a familiar state followed by correction; iterative retraining teaches retry behavior | Recovery-to-correction frame ratio; intervention frames across rounds; successful trials | Shirt hanging reached **78.3%** with about 5 h of data; separate comparison achieved **61/100** versus **22/100** for HG-DAgger (hu2026racrobotlearning pages 12-13, hu2026racrobotlearning pages 13-15) | Approximately **5 h** for shirt hanging; up to 10× lower collection time or sample use and at least 2× data efficiency in reported comparisons (hu2026racrobotlearning pages 1-2, hu2026racrobotlearning pages 12-13) | Maintained roughly **1:1 to 1:2** recovery-to-correction frames; total intervention frames decreased, but no overall intervention percentage was reported (hu2026racrobotlearning pages 13-15) |
| Genie Centurion (GCENT) | 2025 | Wang et al.; DOI: 10.48550/arXiv.2505.18793 **[preprint]** | Dual-arm AgiBot G01 | Task Sentinel detects incomplete steps, requests assistance, rewinds up to 3 s, and records targeted corrective demonstrations | Intervention rate; effective-frame collection efficiency; final task score; rounds to threshold | Mean final score **0.93**; all four tasks exceeded **0.9** within 3–5 rounds (wang2025geniecenturionaccelerating pages 5-7) | Used **44.5%** of comparator frames to reach comparable performance | In one-human/two-robot tests, intervention rate fell **47% → 39% → 27%** as model success rose 40% → 60% → 80%; normalized collection efficiency rose **1.86 → 1.90 → 1.92** (wang2025geniecenturionaccelerating pages 7-9) |
| Sirius-Fleet | 2024 | Liu et al.; DOI: 10.48550/arXiv.2410.22689 **[preprint]** | Franka Emika Panda; five human operators | Visual world model and failure or OOD predictors request interventions; thresholds and the multi-task policy adapt during deployment | Intervention requests or rate; combined and autonomous policy performance; ROHE | Outperformed MoMaRT, PATO, and ThriftyDAgger on combined performance and ROHE; exact taskwise rates were not recoverable (liu2024multitaskinteractiverobot pages 8-9) | RoboCasa simulation and real-world Mutex benchmark; exact rollout count not established here | Designed to reduce intervention requests as anomaly predictors and policies improve (liu2024multitaskinteractiverobot pages 8-9, liu2024multitaskinteractiverobot pages 1-2) |
| ThriftyDAgger | 2021 | Hoque et al.; DOI: 10.48550/arXiv.2109.08273 **[preprint]** | No physical arm established by available evidence | Robot-gated DAgger requests assistance only when states are both novel and risky, subject to an intervention budget | Intervention budget or count and success; later fleet work uses it as an allocation baseline | No reliable real-arm final-success figure available in the gathered evidence | No reliable real-arm trial count available | Primarily a budget-aware gating method; available evidence does not establish a comparable physical-arm intervention-decay result (liu2024multitaskinteractiverobot pages 8-9) |
| IntervenGen | 2024 | Hoque et al., *IROS*; DOI: 10.48550/arXiv.2405.01472 **[conference paper represented by arXiv DOI]** | One physical manipulation environment; arm model not established by available evidence | Generates many synthetic corrective interventions from a small set of human interventions to broaden state-space coverage | Number of seed human interventions; robustness multiplier | Up to **39× greater robustness** in the reported physical and simulated evaluation | **10 human interventions** for the headline result | Data augmentation rather than a long deployment campaign; no intervention-rate decay or hundreds-of-trials reliability estimate was identified |


*Table: Comparison of real-robot and fleet-learning systems that convert deployment interventions into policy updates. Missing values are marked explicitly to avoid treating qualitative claims or simulation results as measured long-campaign reliability evidence.*

### Key Results by System

**HG-DAgger** (Kelly et al. 2019, DOI: 10.1109/ICRA.2019.8793698) introduced human-gated interactive imitation learning where "the human expert determines when to intervene and take control of the robot." When reimplemented as a baseline in HIL-SERL, HG-DAgger averaged only 49.7% success with no consistent decline in intervention rate (luo2025preciseanddexterous pages 14-15).

**Sirius** (Liu et al. 2024, DOI: 10.1177/02783649241273901) introduced intervention-weighted behavioral cloning on a Franka Emika Panda. The weighting scheme "up-weights interventions and down-weights pre-interventions" using approximated human trust (liu2024robotlearningon pages 1-2, liu2024robotlearningon pages 7-8). Across deployment data, the mean intervention sample ratio was 0.32 (SD 0.11), with an average of 2.80 interventions per trajectory and 15.28 timesteps per intervention (liu2024robotlearningon pages 13-14). Policy success rates ranged from 44.8% to 72.7% across individual operators, with an overall 27% improvement over baselines on real hardware (liu2024robotlearningon pages 11-13, liu2024robotlearningon pages 1-2).

**HIL-SERL** (Luo et al. 2025, DOI: 10.1126/scirobotics.ads5033, *Science Robotics*) achieved 100% success on all 13 evaluated tasks within 1–2.5 hours of real-world training, with the intervention rate declining to 0% as policies converged, while HG-DAgger baselines averaged 49.7% success (luo2025preciseanddexterous pages 14-15, luo2025preciseanddexterous pages 12-14, luo2025preciseanddexterous pages 1-3). Training began with approximately 20–30 human demonstrations (luo2025preciseanddexterous pages 8-9). In a separate evaluation (Lin et al. 2026), HIL-SERL showed human intervention rates of 39–77% across five manipulation tasks before convergence (lin2026uniintervene++anadaptive pages 4-5).

**RaC** (Hu et al. 2025, DOI: 10.48550/arXiv.2509.07953, *IEEE Transactions on Robotics*) uses two xArm-7 manipulators and explicitly teaches recovery-then-correction behavior. It achieved 78.3% full-task success on shirt hanging with approximately 5 hours of data versus 75% for ALOHA Unleashed with approximately 89 hours (hu2026racrobotlearning pages 12-13). In a head-to-head comparison, RaC achieved 61/100 successful trials versus 22/100 for HG-DAgger (hu2026racrobotlearning pages 13-15). Recovery-to-correction frame ratios were maintained at approximately 1:1 to 1:2, and total intervention frames decreased across rounds (hu2026racrobotlearning pages 6-8, hu2026racrobotlearning pages 13-15).

### Low-Cost Arms

**No published HIL/interactive-learning work was found on SO-100, SO-101, Koch, or PiPER arms.** The closest low-cost platform is the xArm-7 used in RaC (hu2026racrobotlearning pages 4-6). The ALOHA system uses ViperX arms for bimanual teleoperation but its published work focuses on demonstration collection rather than online interactive learning with intervention-rate tracking. This represents a significant gap: all published HIL-RL and interactive IL systems with reported intervention metrics have used research-grade arms (Franka Emika Panda, ABB YuMi, UR5, xArm-7).

### Laboratory or SDL Tasks

**No published evidence was found** of HIL interactive learning applied to self-driving laboratory tasks or chemical/materials manipulation. This is an open area.

## (3) Remote Supervision and Shared Autonomy

### One-to-Many Supervision

Fleet-DAgger formalized the problem of allocating M remote supervisors to N >> M robots, with physical experiments involving four ABB YuMi arms and two remote humans teleoperating over the Internet (hoque2022fleetdaggerinteractiverobot pages 1-2, hoque2024scalablelifelongimitationa pages 61-64). Hoque's dissertation describes remote fleet supervision using a cloud robotics platform supporting "real-time operation with robots, compute nodes, and teleoperators distributed globally" and reports a 10 Hz control loop over the Internet (hoque2024scalablelifelongimitationa pages 12-15, hoque2024scalablelifelongimitation pages 12-15). However, Fleet-DAgger's formal model "assumes that supervisors have perfect situational awareness, can switch between robots without any switching latency, and operate in synchronous timesteps without network latency or communication issues" and identifies removing these assumptions as future work (hoque2022fleetdaggerinteractiverobot pages 8-10).

Genie Centurion (GCENT, preprint, Wang et al. 2025, DOI: 10.48550/arXiv.2505.18793) demonstrated one-human-to-two-robot supervision in a sandwich-assembly task. As model success rose from 40% to 80%, the intervention rate fell from 47% to 27%, while normalized collection efficiency rose from 1.86 to 1.92 (wang2025geniecenturionaccelerating pages 7-9). GCENT's Task Sentinel autonomously detects incomplete steps and "requests human intervention when needed," enabling scalable 1-to-N deployment as policies improve (wang2025geniecenturionaccelerating pages 5-7, wang2025geniecenturionaccelerating pages 1-3).

HITL-TAMP (Mandlekar et al. 2023, preprint, DOI: 10.48550/arXiv.2310.16014) used a TAMP-gated control mechanism that "enables the human teleoperator to manage a fleet of robots, maximizing data collection efficiency," gathering more than 3× the demonstrations given the same time budget compared to conventional teleoperation.

### Network Latency Effects

Bray et al. (2024, DOI: 10.3390/fi16120457) measured average round-trip latencies of 6.6 ms locally, 58.4 ms over Wi-Fi, 115.4 ms over cellular, and 240.7 ms over a transatlantic VPN; at 240 ms, "the robot moves only slightly more than four times per second, making control more challenging, although object-grasping tasks remain feasible" (bray2024alatencycomposition pages 1-2, bray2024alatencycomposition pages 16-19).

Cundar et al. (2023, DOI: 10.3390/s23208438) quantified the relationship for a 4-DOF teleultrasound robot: a WLAN configuration produced approximately 300 ms average delay and a maximum displacement error of 7.8 mm, while a VLAN configuration reduced average delay by 40% and maximum displacement error by 70% (cundar2023quantifyingtheeffects pages 1-2).

Rakita et al. (2020, DOI: 10.1145/3319502.3374838) distinguished onset latency from robot slowness in mimicry-control teleoperation, finding that "users can quickly develop strategies to adapt to slowness delays but not onset latency delays" (rakita2020effectsofonset pages 1-2).

Louca et al. (2024, DOI: 10.1145/3651993) found that "increased latency reduced performance in all metrics recorded" for robot arm teleoperation with delays up to 2.6 seconds, and that operators adopted a "move-and-wait" strategy that substantially increased task completion time (louca2024impactofhaptic pages 1-3).

**For the Vertical Cloud Lab's 34 ms median command latency**: this falls well within the low-latency regime (<60 ms) where Bray et al. found stable, reliable control. The primary risk is jitter and outlier latencies rather than the median value itself.

## (4) Intervention Logs as Training Data for Laboratory Arms

**No published evidence was found** of anyone treating the intervention log of a scripted or fiducial-guided laboratory arm as training data for a learned recovery or correction policy. Similarly, **no published comparison** of scripted-plus-fixtures, learned, and hybrid controllers on intervention rate over a long campaign was identified.

The closest analogue is RaC's approach of collecting recovery and correction segments during deployment and retraining iteratively (hu2026racrobotlearning pages 4-6, hu2026racrobotlearning pages 2-4), but this was demonstrated on manipulation tasks (shirt hanging, lid sealing, takeout packing), not laboratory protocols. The LabRobFail benchmark (preprint, Wang et al. 2026, DOI: 10.48550/arXiv.2607.23704) provides a simulation-based failure taxonomy and correction-instruction generation for chemical laboratory operations, with over 20,000 labeled trajectories across 70+ task scenarios (wang2026labrobfailabenchmark pages 1-2, wang2026labrobfailabenchmark pages 2-3, wang2026labrobfailabenchmark pages 3-4), but it does not report using real intervention logs from a deployed lab arm for policy training.

**This is an open research area** that the Vertical Cloud Lab would be well-positioned to pioneer: treating each human intervention during scripted operation as both a reliability data point and a training example for a learned recovery policy.

## (5) Statistical Methods for Intervention Rate Estimation

### Rate Estimation

Intervention counts per fixed number of operations are naturally modeled as count data. The Poisson distribution is the starting point, with the rate parameter λ giving interventions per operation. The negative-binomial model accommodates overdispersion (variance exceeding the mean), which is common in reliability data. Pradhan (2023) used "negative-binomial modeling" alongside "survival analysis, recurrent-event modeling" and reported failure rates as incidence rate ratios with 95% confidence intervals for industrial asset reliability (paz2020autonomousvehiclebenchmarking pages 1-2). Jovan et al. (2022, DOI: 10.1007/s10514-022-10070-9) used a partially observable Poisson process to model count data from a 69-day mobile robot deployment, with negative-binomial extensions for overdispersed observations and Bayesian posterior credible intervals for rate estimation (paz2020autonomousvehiclebenchmarking pages 1-2).

### Time-to-Event Models

Survival analysis (Cox proportional hazards, Weibull models) is appropriate for modeling time or operations to the next intervention. Recurrent-event models (Andersen-Gill, frailty models) handle the fact that the same robot experiences multiple interventions.

### Learning Curves and Change-Point Detection

When the controller is being improved, the intervention rate is expected to decrease over time. This creates a non-stationary process. Standard approaches include:
- **Piecewise-constant Poisson models** with change points at policy updates
- **Bayesian online change-point detection** (Adams and MacKay 2007) to detect when intervention rates shift
- **Log-linear models** of rate versus cumulative operations (reliability growth models, e.g., Crow-AMSAA)

### Confidence Sequences for Sequential Monitoring

Confidence sequences (Howard et al. 2021, *Annals of Statistics*) provide time-uniform confidence intervals that remain valid under continuous monitoring, avoiding the multiple-testing problems of repeated hypothesis testing. These are directly applicable to sequential monitoring of intervention rates during a campaign. **No published robotics paper was found that applies confidence sequences to intervention-rate monitoring.**

### Sample Size

For a Poisson rate with no covariates, detecting a halving of the intervention rate (from λ₁ to λ₁/2) with 80% power and α = 0.05 requires approximately 2×(z₀.₉₇₅ + z₀.₈₀)²/ln(2)² ≈ 65 events per condition. For 300 operations per condition, the campaign is well powered to detect moderate rate differences provided the baseline rate is ≥ 0.2 interventions per operation. For rare events (<5% intervention rate), negative-binomial or exact Poisson methods are needed, and 300 operations may yield only ~15 events, requiring exact confidence intervals.

### Pre-Registration with an Adaptive Controller

**This is an identified gap in the literature.** No published work combines pre-registration with a deliberately improved controller during the campaign. The recommended approach draws from adaptive clinical trial methodology:

1. **Pre-specify the analysis plan** including: (a) the primary outcome (mean operations between interventions), (b) the secondary outcome (intervention rate per operation), (c) the failure taxonomy (LabRobFail categories), (d) planned policy update points, and (e) the statistical model (piecewise negative-binomial with change points at each policy update).
2. **Use a blocked design**: within each block (before each policy update), the controller is fixed, enabling valid within-block rate estimation.
3. **Apply confidence sequences** for the cumulative rate, allowing continuous monitoring without inflating the type I error rate.
4. **Report both the within-block rates and the overall trajectory**, treating policy updates as known covariates rather than nuisance variation.
5. **Register the protocol** (e.g., on OSF or as a Registered Report) specifying the minimum sample size per block, the decision rule for policy updates, and the analysis pipeline before data collection begins.

The PREP-eval framework (Carro et al. 2026) provides a general pre-registration and reporting protocol for AI evaluations that could be adapted to this setting, though it does not specifically address robotics or adaptive controllers.

## Summary of Evidence Gaps

Three significant gaps were identified:

1. **No published HIL/interactive learning work on truly low-cost arms** (SO-100/SO-101, Koch, PiPER, or sub-$3k systems). All published systems use research-grade arms ($10k+).
2. **No published work treats intervention logs from scripted/fiducial-guided laboratory arms as training data** for learned recovery policies, nor compares scripted, learned, and hybrid controllers on intervention rate over extended campaigns.
3. **No published robotics paper combines confidence sequences, change-point detection, and pre-registration** for a reliability campaign with a deliberately improved controller. The statistical components exist individually in reliability engineering and clinical trial methodology but have not been assembled for this use case.


References

1. (skokan2025coulddisengagementreports pages 2-4): Adam Skokan and Jan Mareček. Could disengagement reports indicate evolution of autonomous vehicles? Vehicles, 7:32, Apr 2025. URL: https://doi.org/10.3390/vehicles7020032, doi:10.3390/vehicles7020032. This article has 8 citations.

2. (kohanpour2025trendsinautonomous pages 4-7): Ehsan Kohanpour, Seyed Rasoul Davoodi, and Khaled Shaaban. Trends in autonomous vehicle performance: a comprehensive study of disengagements and mileage. Future Transportation, 5:38, Apr 2025. URL: https://doi.org/10.3390/futuretransp5020038, doi:10.3390/futuretransp5020038. This article has 9 citations.

3. (kohanpour2025trendsinautonomous pages 1-2): Ehsan Kohanpour, Seyed Rasoul Davoodi, and Khaled Shaaban. Trends in autonomous vehicle performance: a comprehensive study of disengagements and mileage. Future Transportation, 5:38, Apr 2025. URL: https://doi.org/10.3390/futuretransp5020038, doi:10.3390/futuretransp5020038. This article has 9 citations.

4. (kohanpour2025trendsinautonomous pages 2-4): Ehsan Kohanpour, Seyed Rasoul Davoodi, and Khaled Shaaban. Trends in autonomous vehicle performance: a comprehensive study of disengagements and mileage. Future Transportation, 5:38, Apr 2025. URL: https://doi.org/10.3390/futuretransp5020038, doi:10.3390/futuretransp5020038. This article has 9 citations.

5. (paz2020autonomousvehiclebenchmarking pages 1-2): David Paz, Po-jung Lai, Nathan Chan, Yuqing Jiang, and Henrik I. Christensen. Autonomous vehicle benchmarking using unbiased metrics. 2020 IEEE/RSJ International Conference on Intelligent Robots and Systems (IROS), pages 6223-6228, Oct 2020. URL: https://doi.org/10.1109/iros45743.2020.9340902, doi:10.1109/iros45743.2020.9340902. This article has 19 citations.

6. (banerjee2018handsoffthe pages 1-2): Subho S. Banerjee, Saurabh Jha, James Cyriac, Zbigniew T. Kalbarczyk, and Ravishankar K. Iyer. Hands off the wheel in autonomous vehicles?: a systems perspective on over a million miles of field data. 2018 48th Annual IEEE/IFIP International Conference on Dependable Systems and Networks (DSN), pages 586-597, Jun 2018. URL: https://doi.org/10.1109/dsn.2018.00066, doi:10.1109/dsn.2018.00066. This article has 221 citations.

7. (skokan2025coulddisengagementreports pages 16-18): Adam Skokan and Jan Mareček. Could disengagement reports indicate evolution of autonomous vehicles? Vehicles, 7:32, Apr 2025. URL: https://doi.org/10.3390/vehicles7020032, doi:10.3390/vehicles7020032. This article has 8 citations.

8. (hoque2024scalablelifelongimitationa pages 64-66): R Hoque. Scalable lifelong imitation learning for robot fleets. Unknown journal, 2024.

9. (hoque2022fleetdaggerinteractiverobot pages 2-4): Ryan Hoque, Lawrence Yunliang Chen, Satvik Sharma, Karthik Dharmarajan, Brijen Thananjeyan, Pieter Abbeel, and Ken Goldberg. Fleet-dagger: interactive robot fleet learning with scalable human supervision. ArXiv, pages 368-380, Jun 2022. URL: https://doi.org/10.48550/arxiv.2206.14349, doi:10.48550/arxiv.2206.14349. This article has 86 citations.

10. (hoque2022fleetdaggerinteractiverobot pages 1-2): Ryan Hoque, Lawrence Yunliang Chen, Satvik Sharma, Karthik Dharmarajan, Brijen Thananjeyan, Pieter Abbeel, and Ken Goldberg. Fleet-dagger: interactive robot fleet learning with scalable human supervision. ArXiv, pages 368-380, Jun 2022. URL: https://doi.org/10.48550/arxiv.2206.14349, doi:10.48550/arxiv.2206.14349. This article has 86 citations.

11. (wang2026labrobfailabenchmark pages 1-2): Hao-Bo Wang, Bao-Li Sun, An-Qi Zou, Dongsheng Huang, Zelin Lv, Ning Wang, Rui Li, Dong-Zhan Zhou, Weiyu Guo, Zhihui Wang, and Wan-Li Ouyang. Labrobfail: a benchmark for robotic failure analysis in chemical self-driving laboratory. ArXiv, Jul 2026. URL: https://doi.org/10.48550/arxiv.2607.23704, doi:10.48550/arxiv.2607.23704. This article has 2 citations.

12. (wang2026labrobfailabenchmark pages 2-3): Hao-Bo Wang, Bao-Li Sun, An-Qi Zou, Dongsheng Huang, Zelin Lv, Ning Wang, Rui Li, Dong-Zhan Zhou, Weiyu Guo, Zhihui Wang, and Wan-Li Ouyang. Labrobfail: a benchmark for robotic failure analysis in chemical self-driving laboratory. ArXiv, Jul 2026. URL: https://doi.org/10.48550/arxiv.2607.23704, doi:10.48550/arxiv.2607.23704. This article has 2 citations.

13. (wang2026labrobfailabenchmark pages 4-5): Hao-Bo Wang, Bao-Li Sun, An-Qi Zou, Dongsheng Huang, Zelin Lv, Ning Wang, Rui Li, Dong-Zhan Zhou, Weiyu Guo, Zhihui Wang, and Wan-Li Ouyang. Labrobfail: a benchmark for robotic failure analysis in chemical self-driving laboratory. ArXiv, Jul 2026. URL: https://doi.org/10.48550/arxiv.2607.23704, doi:10.48550/arxiv.2607.23704. This article has 2 citations.

14. (wang2026labrobfailabenchmark pages 8-10): Hao-Bo Wang, Bao-Li Sun, An-Qi Zou, Dongsheng Huang, Zelin Lv, Ning Wang, Rui Li, Dong-Zhan Zhou, Weiyu Guo, Zhihui Wang, and Wan-Li Ouyang. Labrobfail: a benchmark for robotic failure analysis in chemical self-driving laboratory. ArXiv, Jul 2026. URL: https://doi.org/10.48550/arxiv.2607.23704, doi:10.48550/arxiv.2607.23704. This article has 2 citations.

15. (liu2024robotlearningon pages 13-14): Huihan Liu, Soroush Nasiriany, Lance Zhang, Zhiyao Bao, and Yuke Zhu. Robot learning on the job: human-in-the-loop autonomy and learning during deployment. The International Journal of Robotics Research, Oct 2024. URL: https://doi.org/10.1177/02783649241273901, doi:10.1177/02783649241273901. This article has 238 citations.

16. (luo2025preciseanddexterous pages 14-15): Jianlan Luo, Charles Xu, Jeffrey Wu, and Sergey Levine. Precise and dexterous robotic manipulation via human-in-the-loop reinforcement learning. Science Robotics, 10:eads5033, Aug 2025. URL: https://doi.org/10.1126/scirobotics.ads5033, doi:10.1126/scirobotics.ads5033. This article has 406 citations and is from a highest quality peer-reviewed journal.

17. (hoque2022fleetdaggerinteractiverobot pages 8-10): Ryan Hoque, Lawrence Yunliang Chen, Satvik Sharma, Karthik Dharmarajan, Brijen Thananjeyan, Pieter Abbeel, and Ken Goldberg. Fleet-dagger: interactive robot fleet learning with scalable human supervision. ArXiv, pages 368-380, Jun 2022. URL: https://doi.org/10.48550/arxiv.2206.14349, doi:10.48550/arxiv.2206.14349. This article has 86 citations.

18. (liu2024robotlearningon pages 1-2): Huihan Liu, Soroush Nasiriany, Lance Zhang, Zhiyao Bao, and Yuke Zhu. Robot learning on the job: human-in-the-loop autonomy and learning during deployment. The International Journal of Robotics Research, Oct 2024. URL: https://doi.org/10.1177/02783649241273901, doi:10.1177/02783649241273901. This article has 238 citations.

19. (liu2024robotlearningon pages 11-13): Huihan Liu, Soroush Nasiriany, Lance Zhang, Zhiyao Bao, and Yuke Zhu. Robot learning on the job: human-in-the-loop autonomy and learning during deployment. The International Journal of Robotics Research, Oct 2024. URL: https://doi.org/10.1177/02783649241273901, doi:10.1177/02783649241273901. This article has 238 citations.

20. (liu2024robotlearningon pages 7-8): Huihan Liu, Soroush Nasiriany, Lance Zhang, Zhiyao Bao, and Yuke Zhu. Robot learning on the job: human-in-the-loop autonomy and learning during deployment. The International Journal of Robotics Research, Oct 2024. URL: https://doi.org/10.1177/02783649241273901, doi:10.1177/02783649241273901. This article has 238 citations.

21. (luo2025preciseanddexterous pages 12-14): Jianlan Luo, Charles Xu, Jeffrey Wu, and Sergey Levine. Precise and dexterous robotic manipulation via human-in-the-loop reinforcement learning. Science Robotics, 10:eads5033, Aug 2025. URL: https://doi.org/10.1126/scirobotics.ads5033, doi:10.1126/scirobotics.ads5033. This article has 406 citations and is from a highest quality peer-reviewed journal.

22. (luo2025preciseanddexterous pages 8-9): Jianlan Luo, Charles Xu, Jeffrey Wu, and Sergey Levine. Precise and dexterous robotic manipulation via human-in-the-loop reinforcement learning. Science Robotics, 10:eads5033, Aug 2025. URL: https://doi.org/10.1126/scirobotics.ads5033, doi:10.1126/scirobotics.ads5033. This article has 406 citations and is from a highest quality peer-reviewed journal.

23. (luo2025preciseanddexterous pages 1-3): Jianlan Luo, Charles Xu, Jeffrey Wu, and Sergey Levine. Precise and dexterous robotic manipulation via human-in-the-loop reinforcement learning. Science Robotics, 10:eads5033, Aug 2025. URL: https://doi.org/10.1126/scirobotics.ads5033, doi:10.1126/scirobotics.ads5033. This article has 406 citations and is from a highest quality peer-reviewed journal.

24. (hu2026racrobotlearning pages 12-13): Zhe-Yuan Hu, Robyn Wu, Naveen Enock, Jasmine Li, Riya Kadakia, Zackory Erickson, and Aviral Kumar. Rac: robot learning for long-horizon tasks by scaling recovery and correction. IEEE Transactions on Robotics, 42:2843-2860, Sep 2025. URL: https://doi.org/10.48550/arxiv.2509.07953, doi:10.48550/arxiv.2509.07953. This article has 68 citations and is from a highest quality peer-reviewed journal.

25. (hu2026racrobotlearning pages 13-15): Zhe-Yuan Hu, Robyn Wu, Naveen Enock, Jasmine Li, Riya Kadakia, Zackory Erickson, and Aviral Kumar. Rac: robot learning for long-horizon tasks by scaling recovery and correction. IEEE Transactions on Robotics, 42:2843-2860, Sep 2025. URL: https://doi.org/10.48550/arxiv.2509.07953, doi:10.48550/arxiv.2509.07953. This article has 68 citations and is from a highest quality peer-reviewed journal.

26. (hu2026racrobotlearning pages 1-2): Zhe-Yuan Hu, Robyn Wu, Naveen Enock, Jasmine Li, Riya Kadakia, Zackory Erickson, and Aviral Kumar. Rac: robot learning for long-horizon tasks by scaling recovery and correction. IEEE Transactions on Robotics, 42:2843-2860, Sep 2025. URL: https://doi.org/10.48550/arxiv.2509.07953, doi:10.48550/arxiv.2509.07953. This article has 68 citations and is from a highest quality peer-reviewed journal.

27. (wang2025geniecenturionaccelerating pages 5-7): Wenhao Wang, Jia-Yi Song, Chiming Liu, Jiayao Ma, Siyuan Feng, Jingyuan Wang, Yuxin Jiang, Kylin Chen, Sikang Zhan, Yi Wang, Tong Meng, Modi Shi, Xindong He, Guanghui Ren, Yang Yang, and Maoqing Yao. Genie centurion: accelerating scalable real-world robot training with human rewind-and-refine guidance. ArXiv, May 2025. URL: https://doi.org/10.48550/arxiv.2505.18793, doi:10.48550/arxiv.2505.18793. This article has 16 citations.

28. (wang2025geniecenturionaccelerating pages 7-9): Wenhao Wang, Jia-Yi Song, Chiming Liu, Jiayao Ma, Siyuan Feng, Jingyuan Wang, Yuxin Jiang, Kylin Chen, Sikang Zhan, Yi Wang, Tong Meng, Modi Shi, Xindong He, Guanghui Ren, Yang Yang, and Maoqing Yao. Genie centurion: accelerating scalable real-world robot training with human rewind-and-refine guidance. ArXiv, May 2025. URL: https://doi.org/10.48550/arxiv.2505.18793, doi:10.48550/arxiv.2505.18793. This article has 16 citations.

29. (liu2024multitaskinteractiverobot pages 8-9): Huihan Liu, Yu Zhang, Vaarij Betala, Evan Zhang, James Liu, Crystal Ding, and Yuke Zhu. Multi-task interactive robot fleet learning with visual world models. ArXiv, Oct 2024. URL: https://doi.org/10.48550/arxiv.2410.22689, doi:10.48550/arxiv.2410.22689. This article has 68 citations.

30. (liu2024multitaskinteractiverobot pages 1-2): Huihan Liu, Yu Zhang, Vaarij Betala, Evan Zhang, James Liu, Crystal Ding, and Yuke Zhu. Multi-task interactive robot fleet learning with visual world models. ArXiv, Oct 2024. URL: https://doi.org/10.48550/arxiv.2410.22689, doi:10.48550/arxiv.2410.22689. This article has 68 citations.

31. (lin2026uniintervene++anadaptive pages 4-5): Yu-Dong Lin, Hao-Yuan Deng, Zhuo-Xuan Yuan, Zai-Jia Yang, Yuan-Jiang Xue, and Zi-Wei Wang. Uniintervene++: an adaptive intervention agent for efficient real-world reinforcement learning. ArXiv, Oct 2026. URL: https://doi.org/10.48550/arxiv.2610.03620, doi:10.48550/arxiv.2610.03620. This article has 0 citations.

32. (hu2026racrobotlearning pages 6-8): Zhe-Yuan Hu, Robyn Wu, Naveen Enock, Jasmine Li, Riya Kadakia, Zackory Erickson, and Aviral Kumar. Rac: robot learning for long-horizon tasks by scaling recovery and correction. IEEE Transactions on Robotics, 42:2843-2860, Sep 2025. URL: https://doi.org/10.48550/arxiv.2509.07953, doi:10.48550/arxiv.2509.07953. This article has 68 citations and is from a highest quality peer-reviewed journal.

33. (hu2026racrobotlearning pages 4-6): Zhe-Yuan Hu, Robyn Wu, Naveen Enock, Jasmine Li, Riya Kadakia, Zackory Erickson, and Aviral Kumar. Rac: robot learning for long-horizon tasks by scaling recovery and correction. IEEE Transactions on Robotics, 42:2843-2860, Sep 2025. URL: https://doi.org/10.48550/arxiv.2509.07953, doi:10.48550/arxiv.2509.07953. This article has 68 citations and is from a highest quality peer-reviewed journal.

34. (hoque2024scalablelifelongimitationa pages 61-64): R Hoque. Scalable lifelong imitation learning for robot fleets. Unknown journal, 2024.

35. (hoque2024scalablelifelongimitationa pages 12-15): R Hoque. Scalable lifelong imitation learning for robot fleets. Unknown journal, 2024.

36. (hoque2024scalablelifelongimitation pages 12-15): R Hoque. Scalable lifelong imitation learning for robot fleets. Unknown journal, 2024.

37. (wang2025geniecenturionaccelerating pages 1-3): Wenhao Wang, Jia-Yi Song, Chiming Liu, Jiayao Ma, Siyuan Feng, Jingyuan Wang, Yuxin Jiang, Kylin Chen, Sikang Zhan, Yi Wang, Tong Meng, Modi Shi, Xindong He, Guanghui Ren, Yang Yang, and Maoqing Yao. Genie centurion: accelerating scalable real-world robot training with human rewind-and-refine guidance. ArXiv, May 2025. URL: https://doi.org/10.48550/arxiv.2505.18793, doi:10.48550/arxiv.2505.18793. This article has 16 citations.

38. (bray2024alatencycomposition pages 1-2): Nick Bray, Matthew Boeding, Michael Hempel, Hamid Sharif, Tapio Heikkilä, Markku Suomalainen, and Tuomas Seppälä. A latency composition analysis for telerobotic performance insights across various network scenarios. Future Internet, 16:457, Dec 2024. URL: https://doi.org/10.3390/fi16120457, doi:10.3390/fi16120457. This article has 18 citations.

39. (bray2024alatencycomposition pages 16-19): Nick Bray, Matthew Boeding, Michael Hempel, Hamid Sharif, Tapio Heikkilä, Markku Suomalainen, and Tuomas Seppälä. A latency composition analysis for telerobotic performance insights across various network scenarios. Future Internet, 16:457, Dec 2024. URL: https://doi.org/10.3390/fi16120457, doi:10.3390/fi16120457. This article has 18 citations.

40. (cundar2023quantifyingtheeffects pages 1-2): Adriana Noguera Cundar, Reza Fotouhi, Zachary Ochitwa, and Haron Obaid. Quantifying the effects of network latency for a teleoperated robot. Sensors, 23:8438, Oct 2023. URL: https://doi.org/10.3390/s23208438, doi:10.3390/s23208438. This article has 51 citations and is from a peer-reviewed journal.

41. (rakita2020effectsofonset pages 1-2): Daniel Rakita, Bilge Mutlu, and Michael Gleicher. Effects of onset latency and robot speed delays on mimicry-control teleoperation. Proceedings of the 2020 ACM/IEEE International Conference on Human-Robot Interaction, pages 519-527, Mar 2020. URL: https://doi.org/10.1145/3319502.3374838, doi:10.1145/3319502.3374838. This article has 43 citations.

42. (louca2024impactofhaptic pages 1-3): Joe Louca, Kerstin Eder, John Vrublevskis, and Antonia Tzemanaki. Impact of haptic feedback in high latency teleoperation for space applications. ACM Transactions on Human-Robot Interaction, 13:1-21, Jun 2024. URL: https://doi.org/10.1145/3651993, doi:10.1145/3651993. This article has 35 citations and is from a peer-reviewed journal.

43. (hu2026racrobotlearning pages 2-4): Zhe-Yuan Hu, Robyn Wu, Naveen Enock, Jasmine Li, Riya Kadakia, Zackory Erickson, and Aviral Kumar. Rac: robot learning for long-horizon tasks by scaling recovery and correction. IEEE Transactions on Robotics, 42:2843-2860, Sep 2025. URL: https://doi.org/10.48550/arxiv.2509.07953, doi:10.48550/arxiv.2509.07953. This article has 68 citations and is from a highest quality peer-reviewed journal.

44. (wang2026labrobfailabenchmark pages 3-4): Hao-Bo Wang, Bao-Li Sun, An-Qi Zou, Dongsheng Huang, Zelin Lv, Ning Wang, Rui Li, Dong-Zhan Zhou, Weiyu Guo, Zhihui Wang, and Wan-Li Ouyang. Labrobfail: a benchmark for robotic failure analysis in chemical self-driving laboratory. ArXiv, Jul 2026. URL: https://doi.org/10.48550/arxiv.2607.23704, doi:10.48550/arxiv.2607.23704. This article has 2 citations.