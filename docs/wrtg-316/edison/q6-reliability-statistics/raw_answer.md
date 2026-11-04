# Reliability Statistics for Robot Manipulation: Reporting Success Rates, Confidence Intervals, and Mean Cycles Between Interventions

## 1. The Problem: How the Field Currently Reports Success

The dominant metric in physical robot-manipulation evaluation is "success rate"—the percentage of autonomous runs that succeed. Kress-Gazit et al. (2024, preprint) argue that this practice is insufficient: "it is common for papers to report this number with little to no information regarding the number of runs, the initial conditions, and the success criteria, little to no narrative description of the behaviors and failures observed, and little to no statistical analysis of the findings" (pqac-00000005, pqac-00000012). A recent audit of the five most-cited manipulation benchmarks (LIBERO, CALVIN, SimplerEnv, RoboCasa, RoboTwin 2.0) found that the majority of reported performance gaps between policies are statistically inconclusive when examined with paired Wald tests: across LIBERO, only 20.8% of 789 comparisons were provably significant at the 5% level (pqac-00000042).

The following table summarizes how major benchmarks actually report results, their trial counts, and whether they include any form of uncertainty estimate.

| Paper / benchmark | Year | Venue | Robot arm | Trials per task / condition | Success criterion | Statistical method | Notes |
|---|---:|---|---|---:|---|---|---|
| YCB Benchmarking | 2015 | IEEE Robotics & Automation Magazine | Various platforms | Typically 10 | Task-specific completion, such as successful peg insertion | Raw successes/trials; no proportion CI | Also reports timed-run means and SDs for some protocols; DOI: [10.1109/MRA.2015.2448951](https://doi.org/10.1109/MRA.2015.2448951) (pqac-00000015) |
| NIST Assembly Task Board | 2020 | IEEE RA-L | Platform-independent | User-selected number | Autonomous completion of an assembly or disassembly task/subtask; manual or teleoperated intervention prohibited | Binomial-CDF reliability bound using successes, trials, and confidence level; completion-time mean, SD, and 95% CI | Protocol variant and randomization level must remain fixed across systems; DOI: [10.1109/LRA.2020.2965869](https://doi.org/10.1109/LRA.2020.2965869) (pqac-00000037) |
| Box and Blocks robot benchmark | 2020 | IEEE RA-L | Franka Emika Panda; Barrett WAM | Timed runs; protocol-dependent | Blocks successfully transferred across the partition during the prescribed period | Means and SDs; no binomial CI reported | Measures throughput, misses, attempts, transfers, and failures; DOI: [10.1109/LRA.2019.2961053](https://doi.org/10.1109/LRA.2019.2961053) |
| ALOHA / ACT | 2023 | Preprint; associated with RSS-era work | Two Interbotix ViperX 300s follower arms | 25 real-robot evaluations per task | Final task completion plus named stage/subtask completion; randomized initial placement | Raw percentage; no CI | Six real tasks; reported final rates range from 20% to 96%; DOI: [10.48550/arXiv.2304.13705](https://doi.org/10.48550/arXiv.2304.13705) (pqac-00000026, pqac-00000028, pqac-00000029) |
| Mobile ALOHA | 2024 | Preprint; CoRL | Two Interbotix ViperX 300s follower arms on mobile base | Generally 20; Cook Shrimp used 5 | Each subtask succeeds if its specified goal is achieved; whole-task success requires all sequential subtasks | Raw subtask and whole-task percentages; no CI | Later-subtask denominators are conditional on reaching that subtask; DOI: [10.48550/arXiv.2401.02117](https://doi.org/10.48550/arXiv.2401.02117) (pqac-00000024) |
| FMB: Functional Manipulation Benchmark | 2024 | IJRR | Franka Emika Panda | 25 for reported insertion evaluations | Successful completion of the specified functional manipulation or insertion | Raw successes out of 25; no CI reported | Uses replicable, procedurally generated 3D-printed parts; DOI: [10.1177/02783649241276017](https://doi.org/10.1177/02783649241276017) |
| Robot Learning as an Empirical Science | 2024 | Preprint | Franka-based physical manipulation examples | 20 per policy in principal example | Explicit task rubric, subgoals, initial conditions, and failure modes | Bayesian Bernoulli/binomial posterior; no frequentist CI | Shows that 13/20 versus 14/20 does not justify a superiority claim; DOI: [10.48550/arXiv.2409.09491](https://doi.org/10.48550/arXiv.2409.09491) (pqac-00000003, pqac-00000004, pqac-00000010) |
| FurnitureBench | 2025 | IJRR | Franka Emika Panda | 10 episodes per reported condition | Binary skill/task completion plus number of completed assembly phases | Success percentage and phase-completion summary; no binomial CI | Standardized initialization and explicit stopping rules; DOI: [10.1177/02783649241304789](https://doi.org/10.1177/02783649241304789) (pqac-00000061, pqac-00000062, pqac-00000063, pqac-00000064) |
| Experiences from Benchmarking VLA Models | 2025 | Preprint | Mobile ALOHA bimanual platform | 50 per condition/task unless noted | Task-specific whole-task completion, with explicit criteria for cleaning, placement, unzipping, and folding | Wilson-score 95% CI | Includes a detailed failure taxonomy; DOI: [10.48550/arXiv.2511.11298](https://doi.org/10.48550/arXiv.2511.11298) (pqac-00000023) |
| CEGB Cross-Embodiment Gripper Benchmark | 2026 | IEEE RA-L | MELFA ASSISTA RV-5AS-D; aerial platform for transfer tests | 5 attempts per object-pose combination | Lift at least 5 cm within 3 s and hold for 3 s without slipping; 10 s timeout | Wilson-score CI for binomial grasp proportions; bootstrap CIs for continuous metrics | Reports micro- and macro-average success; DOI: [10.1109/LRA.2026.3677707](https://doi.org/10.1109/LRA.2026.3677707) (pqac-00000016, pqac-00000017, pqac-00000038) |
| LAP | 2026 | Preprint | Multiple embodiments | 20 independent trials per task | Binary completion before timeout or safety abort; randomized object placement | Finite-sample-valid 95% binomial CI | Safety abort includes collision, joint-limit violation, or unsafe motion; DOI: [10.48550/arXiv.2602.10556](https://doi.org/10.48550/arXiv.2602.10556) (pqac-00000008) |
| SafeVLA-Bench | 2026 | Preprint | Various embodiments | Protocol-dependent | Task success reported separately from safety violations | Wilson-score 95% CI for binomial proportions | Designed to expose the gap between successful and safe execution; DOI: [10.48550/arXiv.2606.00773](https://doi.org/10.48550/arXiv.2606.00773) |
| ArmnetBench v0.1 | 2026 | Preprint | Single and bimanual SO-101 5-DoF follower arms | Normally 30 per task-policy pair; two pairs retained 29 | Operator label: successful, suboptimal completion, or failure | Strict success rate and success-plus-suboptimal rate; no CI mentioned | 12 tasks, 7 policies, 50 demonstrations per task, randomized resets, three cameras, and Raspberry Pi 5; DOI: [10.48550/arXiv.2607.24481](https://doi.org/10.48550/arXiv.2607.24481) (pqac-00000058, pqac-00000059, pqac-00000060) |
| RoboDojo | 2026 | Preprint | Multiple standardized real and simulated platforms | 150 per task unless otherwise specified | Binary task completion with additional structured scoring | No CI mentioned in retrieved protocol | High trial count relative to most physical manipulation studies; DOI: [10.48550/arXiv.2607.04434](https://doi.org/10.48550/arXiv.2607.04434) |
| LADDER | 2026 | Preprint | Various benchmark embodiments | Protocol-dependent | Long-horizon completion with stage-level failure localization | Wilson 95% CI over episodes | Designed to isolate where failures occur rather than report only terminal success; DOI: [10.48550/arXiv.2610.18053](https://doi.org/10.48550/arXiv.2610.18053) |


*Table: Comparison of trial counts, success definitions, and uncertainty-reporting practices in major physical robot-manipulation studies. It highlights the historically common use of small raw success fractions and the more recent adoption of Wilson or other finite-sample confidence intervals.*

## 2. Binomial Confidence Intervals for Binary Task Success

### 2.1 Framing the Problem

Each manipulation trial is naturally modeled as a Bernoulli random variable X ∈ {0,1} with unknown success probability p (pqac-00000007). The NIST Assembly Task Board protocol defines reliability as "the probability of successfully completing a task or sub-task," computed from "a confidence level (CL), the number of successes (m), and the number of independent trials (n)" using the binomial cumulative distribution function (pqac-00000002, pqac-00000037). This requires independent, identically distributed trials—a condition that Vincent et al. (2024, IEEE RA-L) emphasize must be ensured by a pre-specified testing plan, warning that practices such as "running policy rollouts until enough favorable outcomes are observed" violate the i.i.d. assumption (pqac-00000040).

### 2.2 Clopper–Pearson (Exact) Intervals

The Clopper–Pearson method inverts exact binomial tail probabilities to produce a confidence interval whose coverage is guaranteed to be at least 1−α for all values of p (pqac-00000053, pqac-00000054, pqac-00000055). The two-sided 100(1−α)% interval allocates α/2 to each tail. Orawo (2021, Open Journal of Statistics) characterizes Clopper–Pearson as "very conservative" because its actual coverage typically exceeds the nominal level, especially at small sample sizes; mean coverage at n=15 with nominal 95% was measured at 0.974 (pqac-00000056). Vincent et al. (2024) note that the Clopper–Pearson lower bound is obtained from their uniformly most accurate (UMA) framework by "setting U = 0 in the test statistic," confirming it as a special case of the optimal bound and showing that their randomized UMA bound is always tighter (pqac-00000040, pqac-00000041, pqac-00000051).

### 2.3 Wilson Score Intervals

Wilson score intervals provide better-behaved coverage than the normal-approximation (Wald) interval, particularly when p is near 0 or 1 or when sample sizes are small (pqac-00000016). The Cross-Embodiment Gripper Benchmark (Vagas et al. 2026, IEEE RA-L) explicitly states that "we report Wilson score confidence intervals, which offer [well-behaved coverage] when sample sizes are small or observed proportions are close to 0 or 1" (pqac-00000016). Wilson intervals are increasingly adopted in 2025–2026 manipulation papers: Zhang et al. (2025, preprint) report "Wilson-score 95% confidence intervals for SR [success rate]" on their Mobile ALOHA VLA benchmarking (pqac-00000023); SafeVLA-Bench uses "Wilson score 95% intervals for binomial proportions"; and LADDER reports "95% Wilson confidence intervals over episodes."

Orawo (2021) recommends Wilson and likelihood intervals over both Wald and Clopper–Pearson for practical use, because they achieve near-nominal coverage without the excessive conservatism of the exact method (pqac-00000056).

### 2.4 Bayesian Approach

Kress-Gazit et al. (2024) illustrate a Bayesian alternative: model success as a Bernoulli distribution with unknown probability, place a uniform prior, and inspect the posterior distribution. They demonstrate that two policies achieving 13/20 (65%) and 14/20 (70%) have substantially overlapping posteriors, yielding only a 0.11 probability that the inferior policy is truly better—emphasizing that identical percentages from small samples cannot support superiority claims (pqac-00000003, pqac-00000004, pqac-00000010).

## 3. Minimum Number of Trials for Reliability Claims

The central sample-size question for robot reliability is: if all n trials succeed, how large must n be to claim that p ≥ p₀ with confidence 1−α? The exact one-sided binomial answer is n ≥ ⌈ln(α)/ln(p₀)⌉ (pqac-00000051, pqac-00000052, pqac-00000053). For the canonical claim of "at least 95% success with 95% confidence," this yields n = ⌈ln(0.05)/ln(0.95)⌉ = ⌈58.40⌉ = 59 trials with zero failures. The well-known "rule of three" approximates this as 3/(1−p₀) = 60 (pqac-00000051, pqac-00000052). If a two-sided 95% Clopper–Pearson interval is required instead, the lower tail uses α/2 = 0.025, yielding n = ⌈ln(0.025)/ln(0.95)⌉ = 72 (pqac-00000050, pqac-00000053).

The following table provides the exact trial counts for several practically relevant reliability targets.

| Desired lower bound on success probability | Confidence level | Bound type | Required trials—all must succeed | Derivation / formula |
|---|---:|---|---:|---|
| \(p \ge 0.95\) | 95% | One-sided exact binomial / Clopper–Pearson | **59** | \(n=\left\lceil\ln(0.05)/\ln(0.95)\right\rceil=\lceil58.40\rceil=59\) (pqac-00000051, pqac-00000052) |
| \(p \ge 0.95\) | 95% | Two-sided 95% Clopper–Pearson | **72** | Equal tails use \(\alpha/2=0.025\): \(n=\left\lceil\ln(0.025)/\ln(0.95)\right\rceil=\lceil71.92\rceil=72\) (pqac-00000050, pqac-00000053) |
| \(p \ge 0.95\) | Approximately 95% | Rule-of-three approximation | **≈60** | \(n\approx3/(1-0.95)=60\); use the exact one-sided result, 59, for a formal claim (pqac-00000051, pqac-00000052) |
| \(p \ge 0.90\) | 95% | One-sided exact binomial / Clopper–Pearson | **29** | \(n=\left\lceil\ln(0.05)/\ln(0.90)\right\rceil=\lceil28.43\rceil=29\) (pqac-00000050, pqac-00000051) |
| \(p \ge 0.99\) | 95% | One-sided exact binomial / Clopper–Pearson | **299** | \(n=\left\lceil\ln(0.05)/\ln(0.99)\right\rceil=\lceil298.07\rceil=299\) (pqac-00000050, pqac-00000051) |
| \(p \ge 0.95\) | 99% | One-sided exact binomial / Clopper–Pearson | **90** | \(n=\left\lceil\ln(0.01)/\ln(0.95)\right\rceil=\lceil89.78\rceil=90\) (pqac-00000050, pqac-00000051) |
| \(p \ge 0.80\) | 95% | One-sided exact binomial / Clopper–Pearson | **14** | \(n=\left\lceil\ln(0.05)/\ln(0.80)\right\rceil=\lceil13.43\rceil=14\) (pqac-00000050, pqac-00000051) |


*Table: Minimum all-success trial counts needed for selected lower-bound reliability claims. The distinction between a one-sided certification bound and a two-sided confidence interval materially changes the required sample size.*

**Critical implication for low-cost arms:** Most published manipulation papers use far fewer trials than the 59 required for a one-sided 95%/95% claim. ALOHA uses 25 real-robot trials per task (pqac-00000026, pqac-00000028); Mobile ALOHA uses 20 (pqac-00000024); FurnitureBench uses 10 (pqac-00000061, pqac-00000062); YCB protocols use 10 (pqac-00000014, pqac-00000015); and ArmnetBench uses 30 (pqac-00000058, pqac-00000059). With 25 all-success trials, the one-sided 95% Clopper–Pearson lower bound on p is only 0.05^(1/25) ≈ 0.887, not 0.95. To genuinely certify 95% success at 95% confidence, 59 consecutive successes with zero failures are necessary.

## 4. Mean Cycles Between Interventions and MTBF

### 4.1 In Lab Automation

Laboratory automation systems report reliability using mean time between failures (MTBF) measured in calendar days or operating hours. Croxatto et al. (2016, Clinical Microbiology and Infection, peer-reviewed) report that BD Kiestra TLA and WCA automated bacteriology systems achieve approximately 100 days MTBF, while the Copan WASPLab achieves approximately 95 days, with the caveat that "MTBF is difficult to specify because it depends substantially on system configuration, overall system complexity, the number and variety of samples processed each day, and user-induced factors" (pqac-00000030). In industrial manufacturing with Digital Twin/IIoT-enabled predictive maintenance, Mostofa (2024) reports baseline MTBF of 1,486.3 hours (SD 412.7; 95% CI [1,431.5, 1,541.1]) across 220 assets including robotic systems, improving to 2,176.8 hours post-intervention (pqac-00000032, pqac-00000033).

### 4.2 In Field Robotics

Honig and Oron-Gilad (2018, Frontiers in Psychology, peer-reviewed) note that "the Mean Time Between Failure (MTBF) for robots in field environments is often within a few hours" (pqac-00000049), highlighting the substantial gap between industrial automation and research robot reliability.

### 4.3 Explicit Gap: No Standard for Mean Cycles Between Interventions in Manipulation

**No published standard exists for reporting "mean cycles between interventions" (MCBI) as a reliability metric for robot manipulation tasks.** The NIST Assembly Task Board protocol uses binomial success probability and completion time (mean, SD, and 95% CI), but does not define a cycles-between-interventions metric (pqac-00000037). Lab automation papers report MTBF in time units rather than task cycles (pqac-00000030). For teams running repeated pick-and-place or assembly cycles on low-cost arms, defining and reporting MCBI—the mean number of autonomous task cycles completed before a human must intervene to reset, fix a jam, or correct an error—would fill a genuine gap in the literature. This metric can be modeled as a geometric or negative-binomial random variable and reported with appropriate confidence intervals.

## 5. Best Practices for Reporting: A Synthesis

Based on the surveyed literature, the following reporting practices are recommended for teams benchmarking low-cost arms:

**What to report for each task:**
1. **Raw counts:** Report k successes out of n trials, not just percentages (pqac-00000003, pqac-00000005, pqac-00000012).
2. **Confidence interval:** Report a Wilson score 95% CI for each success proportion (pqac-00000016, pqac-00000023), or a Clopper–Pearson interval if conservative coverage is preferred (pqac-00000053, pqac-00000054). If using Bayesian methods, show posterior distributions (pqac-00000003).
3. **Success criterion:** Define success semantically and unambiguously. The Cross-Embodiment Gripper Benchmark defines success as "lifting the object at least 5 cm within 3 seconds and holding it for 3 seconds without slipping, with a 10-second timeout" (pqac-00000016). FurnitureBench uses phase-completion scores alongside binary success (pqac-00000062). ArmnetBench uses three-way grading: successful, suboptimal, or failure (pqac-00000058).
4. **Initial conditions:** Specify the randomization range, whether initial conditions are matched across policies, and whether evaluations are interleaved (pqac-00000013).
5. **Failure modes:** Describe observed failure modes qualitatively (pqac-00000005, pqac-00000012).
6. **Completion time:** Report mean, standard deviation, and 95% CI for task-completion time (pqac-00000037).
7. **Trial independence:** Verify and state that trials are independent—no cherry-picking, no stopping-when-good, no environmental drift (pqac-00000040).

**How many trials to run:**
- For a **screening evaluation** during development: 20–30 trials per task are standard practice (pqac-00000024, pqac-00000058) and will give Wilson 95% CI half-widths of roughly ±15–20 percentage points at 80% success.
- For a **formal reliability claim** of p ≥ 0.95 at 95% confidence: 59 consecutive successes with zero failures are required (pqac-00000051, pqac-00000052).
- For **comparing two policies:** Use at least 20 trials per policy under matched initial conditions and apply a paired test or Bayesian comparison (pqac-00000003, pqac-00000010). Jiang et al. (2026, preprint) show that even with hundreds of comparisons, reported performance gaps are often statistically inconclusive (pqac-00000042).

## 6. Placing Low-Cost Arms in the Published Literature

### 6.1 Available Benchmarks for SO-101 and ALOHA-Class Arms

**ArmnetBench v0.1** (Selvaraj et al. 2026, preprint) is the most directly relevant benchmark for SO-101 arms. It evaluates 7 policies (ACT, Diffusion Policy, SmolVLA, π0, π0.5, GR00T N1.7, MolmoAct 2) across 12 tasks on a managed fleet of SO-101 cells, using 30 rollouts per task-policy pair with 50 demonstrations and three-way operator scoring (pqac-00000058, pqac-00000059, pqac-00000060).

**LeRobot** (Cadène et al. 2026, ICLR, peer-reviewed) provides the open-source software stack supporting SO-100, SO-101, Koch-v1.1, and ALOHA hardware. It integrates LIBERO and Meta-World simulation benchmarks and standardized dataset formats, but the paper itself does not report real-world success-rate benchmarks with confidence intervals for specific arms (pqac-00000046).

**RoboMIND** (Wu et al. 2024, preprint) provides a multi-embodiment dataset spanning Franka Emika Panda, UR5e, AgileX dual-arm robot, and a humanoid, with 107k demonstrations across 479 tasks, enabling cross-embodiment comparison.

### 6.2 Explicit Gaps

- **No published peer-reviewed paper benchmarks the AgileX PiPER 6-DOF arm** on any standard manipulation protocol with reported confidence intervals. Any reliability claim for PiPER would need to be generated de novo.
- **No published paper provides a head-to-head reliability comparison** (with binomial confidence intervals or MTBF) between low-cost arms (SO-101, PiPER, ALOHA) and industrial arms (UR5e, Franka, ABB YuMi, Kinova) on matched tasks. RoboMIND includes multiple embodiments but reports imitation-learning success rates rather than hardware-reliability metrics.
- **ABB YuMi** and **Kinova** arms appear in the manipulation literature but not in published benchmarks with the statistical rigor described here.

### 6.3 Repeatable Protocol Recommendation

For teams with PiPER and SO-101 arms seeking to generate publishable, comparable data:

1. **Select a standard object set** (YCB objects are freely available with 3D models) (pqac-00000015).
2. **Use the NIST Assembly Task Board protocol** for assembly tasks: record start/finish times, autonomous operation only (no manual intervention permitted), and report binomial reliability bounds (pqac-00000037).
3. **For imitation-learning policies**, follow the ArmnetBench protocol: 50 demonstrations, 30+ rollouts per task-policy pair, three-way scoring, randomized initial placement (pqac-00000058, pqac-00000059).
4. **Report Wilson score 95% CIs** for all success proportions, state the one-sided or two-sided convention, and report raw k/n alongside percentages.
5. **For reliability certification**, run at least 59 consecutive successful trials per task to claim p ≥ 0.95 at 95% confidence (pqac-00000051, pqac-00000052).
6. **For comparing with Franka or UR5e results**, use matched tasks from FMB (25 trials, Franka), FurnitureBench (10 trials, Franka Panda), or RoboMIND protocols and recompute confidence intervals on the published raw counts.

## 7. Publication Status of Cited Sources

The following papers cited in this review are **preprints** (not yet peer-reviewed in a journal or major conference proceedings): Kress-Gazit et al. (2024), Jiang et al. (2026), Selvaraj et al. (2026, ArmnetBench), Wu et al. (2024, RoboMIND), Zhao et al. (2023, ALOHA), Fu et al. (2024, Mobile ALOHA), Zhang et al. (2025, Experiences Benchmarking VLA), Fan et al. (2026, SafeVLA-Bench), Zha et al. (2026, LAP), Petkov et al. (2026, LADDER), and Chen et al. (2026, RoboDojo). The following are **peer-reviewed**: Vincent et al. (2024, IEEE RA-L), Kimble et al. (2020, IEEE RA-L), Calli et al. (2015, IEEE Robotics & Automation Magazine), Vagas et al. (2026, IEEE RA-L), Orawo (2021, Open Journal of Statistics), Heo et al. (2025, IJRR), Luo et al. (2024, IJRR), Denoun et al. (2023, IEEE Transactions on Robotics), Morgan et al. (2020, IEEE RA-L), Croxatto et al. (2016, Clinical Microbiology and Infection), Honig and Oron-Gilad (2018, Frontiers in Psychology), Cadène et al. (2026, ICLR), and Budde et al. (2025, Lecture Notes in Computer Science).