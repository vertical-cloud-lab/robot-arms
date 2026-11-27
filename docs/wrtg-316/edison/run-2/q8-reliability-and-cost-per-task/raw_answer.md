# Reliability Metrics, Statistical Reporting, and Cost-per-Task Benchmarks for Robot Arms in Self-Driving Laboratories

## 1. How Self-Driving Laboratory Papers Currently Report Reliability

A systematic survey of published SDL and laboratory-automation papers reveals that **most studies report robot-arm reliability descriptively**—as raw success counts, positioning precision, or campaign duration—without formal confidence intervals or intervention-frequency metrics.

### 1.1 Campaign-Level Reporting: The Burger Mobile Robotic Chemist

The landmark study by Burger et al. (2020) used a KUKA KMR mobile manipulator with an LBR iiwa arm. The robot "operated autonomously for 8 days and completed 688 experiments" in a 10-variable photocatalysis search, making "319 moves between laboratory stations and travelled 2.17 km" (pqac-00000024). Positioning precision was ±0.12 mm in x–y and <0.005° in orientation, established through "100 separate six-point (6P) calibration trials" with simulated noise up to ±15 mm and ±2.5° (pqac-00000025). The robot could operate "up to 21.6 hours per day," being "idle but charging for approximately 32% of the experiment, mainly while waiting for the GC analysis" (pqac-00000024). However, this paper does not report a formal success rate, failure rate, mean cycles between interventions (MCBI), confidence intervals, or even a total count of individual robotic actions. It notes that "the system automatically alerted operators when consumables ran out or a workflow failed, and most errors could be reset remotely using station CCTV" (pqac-00000024), but the frequency of such events is not quantified. **DOI: 10.1038/s41586-020-2442-2** (peer-reviewed, *Nature*).

### 1.2 Component-Level Testing with Explicit Trial Counts

**LIRA (Zhou et al. 2025)** provides the most rigorous testing protocol found in the SDL literature. The system was evaluated using "100 consecutive workflow loops, each lasting approximately five minutes, for eight hours of continuous operation. During these loops, the robot performed 600 pickup and insertion manipulations and achieved a 100% success rate" (pqac-00000030). For error inspection, "200 manual tests" were conducted with deliberately introduced placement errors, achieving "a 97.5% accuracy—or error-inspection success—rate, corresponding to 195 successful tests out of 200" (pqac-00000027). The fine-tuned VLM achieved "a 97.9% overall success rate" on the shared test dataset (pqac-00000028). Despite the relatively large trial counts (100, 200, 600), no binomial confidence intervals were reported. **DOI: 10.1038/s42004-025-01770-1** (peer-reviewed, *Communications Chemistry*).

**Harazono et al. (2024, preprint)** provide the most detailed positional-accuracy benchmark for a low-cost arm in lab automation. Using a Dobot M1 Pro SCARA robot (~few thousand USD), they "moved the microplate to a specific spatial coordinate...and evaluated the position repeatability by repeating this movement multiple times" with 125 repetitions at each of two speeds (pqac-00000016, pqac-00000017). The interquartile range was 0.020 mm (x) and 0.006 mm (y) at high speed. For transfer success, "transfer was repeated 125 times for each case" at various artificial offsets (Δx = 1.80–2.30 mm and Δy = 2.10–2.20 mm), and "the probability of success gradually decreased with an increase in Δx" while "significantly decreased when Δy exceeded 2.190 mm" (pqac-00000017). Success was determined via video analysis with colored markers. No confidence intervals were computed. **DOI: 10.1101/2023.12.29.573685** (preprint, *bioRxiv*).

**ORGANA (Darvish et al. 2025)** used a Franka Emika Panda for multi-step chemistry experiments. The solubility test was "performed for 2 times," recrystallization and pH each once, and electrochemistry "performed 2 times" (pqac-00000014). "In total, three complete electrochemistry experiments were performed, testing six buffer solutions for each experiment" (pqac-00000012). No task-completion success proportion was reported; validation was based on chemical accuracy of results (slope estimates of -61.3, -61.8, and -61.0 mV/pH unit across three runs). **DOI: 10.1016/j.matt.2024.10.015** (peer-reviewed, *Matter*).

The table below summarizes the published reliability benchmarks found across SDL and laboratory-automation literature:

| Reference | Robot arm model | Task description | Number of trials | Reported success rate / result | Statistical method | DOI |
|---|---|---|---:|---|---|---|
| Burger et al. (2020) | KUKA KMR mobile manipulator | Eight-day autonomous photocatalyst campaign; station-to-station operation and six-point calibration | 688 experiments; 319 inter-station moves; 100 calibration trials | No end-to-end success rate; positioning error within ±0.12 mm and orientation error <0.005° | No confidence interval reported | [10.1038/s41586-020-2442-2](https://doi.org/10.1038/s41586-020-2442-2) (pqac-00000023, pqac-00000024, pqac-00000025) |
| Zhou et al. (2025), LIRA | Cooper-lab mobile manipulator | Fiducial localization followed by rack/plate pickup, insertion, inspection, and reasoning | 100 localization loops; 600 pickup/insertion manipulations; 200 deliberately perturbed inspection tests | 600/600 manipulations successful (100%); 195/200 workflow inspections successful (97.5%); fine-tuned model test accuracy 97.9% | Descriptive proportions; no binomial CI reported | [10.1038/s42004-025-01770-1](https://doi.org/10.1038/s42004-025-01770-1) (pqac-00000027, pqac-00000028, pqac-00000029, pqac-00000030) |
| Harazono et al. (2024) **[preprint]** | Dobot M1 Pro SCARA | Repeated 96-well microplate/lid transfer; dial-gauge repeatability test and deliberately offset lid-placement test | 125 repetitions at each speed and 125 transfers per offset condition | High-speed positional IQR: 0.020 mm in x and 0.006 mm in y; transfer success declined with imposed offset, especially beyond Δy = 2.190 mm | Empirical distributions and success probability; no binomial CI reported | [10.1101/2023.12.29.573685](https://doi.org/10.1101/2023.12.29.573685) (pqac-00000015, pqac-00000016, pqac-00000017) |
| Darvish et al. (2025), ORGANA | Franka Emika Panda | Long-horizon solubility, recrystallization, pH, and electrochemistry workflows | Three complete electrochemistry experiments; two solubility runs; one recrystallization run; one pH run | No formal task-success proportion; three electrochemistry repeats produced comparable slope and pKa estimates | Means/standard deviations for planning time; no binomial CI for manipulation success | [10.1016/j.matt.2024.10.015](https://doi.org/10.1016/j.matt.2024.10.015) (pqac-00000012, pqac-00000013, pqac-00000014) |
| Wu et al. (2026), telerobotic intervention **[preprint]** | Simulated SDL robot-arm interface | Human teleoperation to recover simulated process interruptions, initialization errors, and escalated faults | 86 trials: 28 process-interruption, 30 initialization-error, and 28 escalated-fault trials | Success depended on fault and controller condition; a success required completion without collision, force stop, overextension, or workspace violation | Wilson binomial CIs; Fisher’s exact test; bootstrap CIs for paired continuous outcomes | [10.48550/arxiv.2611.18496](https://doi.org/10.48550/arxiv.2611.18496) (pqac-00000001) |
| Cowling (2026) **[preprint]** | SO-101 low-cost arm | LeRobot-style imitation learning for picking up a green ball and placing it in a basket across ten fixed placements | 1,340 scored episodes; commonly 40 episodes per policy/data-budget cell | ACT achieved 37/40 successes (92.5%, reported as 93%) after training on 100 demonstrations | Raw proportions; no binomial CI reported | [10.48550/arxiv.2610.37170](https://doi.org/10.48550/arxiv.2610.37170) (pqac-00000033, pqac-00000035, pqac-00000037) |
| Rupp et al. (2022) | Dobot Magician (~€1,500) and Dobot MG400 (~€3,000) | Low-cost laboratory automation using AutoIt and four-axis robots | Not reported as repeated end-to-end reliability trials | No formal success rate; automated processes were described as slower than manual work and unsuitable for high-throughput/time-critical use | Qualitative throughput assessment; no CI | [10.1016/j.slast.2022.07.001](https://doi.org/10.1016/j.slast.2022.07.001) (pqac-00000007) |
| Wienbruch et al. (2025) | Robot arm with inexpensive camera system; model not specified here | ArUco-based environment/object detection and automated reading of laboratory displays | Validation count not specified here | In-house display-reading error rate of 1.69%, described as comparable to manual readings | No CI reported in the available evidence | [10.1038/s41598-025-05670-1](https://doi.org/10.1038/s41598-025-05670-1) |


*Table: Published and preprint benchmarks vary from component-level positioning tests to hundreds of autonomous experiments, but most omit binomial confidence intervals and intervention metrics. The table identifies protocols that affordable-arm studies can reproduce and flags where evidence remains descriptive or statistically weak.*

### 1.3 Key Observation: Mean Cycles Between Interventions (MCBI)

**No published SDL paper found in this review reports MCBI or an equivalent metric.** The closest analog is the Burger et al. description of automated alerts when consumables ran out or workflows failed (pqac-00000024), but neither the alert frequency nor the total intervention count is disclosed. This represents a significant gap: MCBI—defined as the mean number of complete task cycles a robot executes between events requiring human intervention—would be the most practically useful reliability metric for comparing affordable and industrial arms.

## 2. Statistical Methods for Reporting Robot Task Success Rates

### 2.1 Appropriate Confidence Intervals

Vincent et al. (2023) provide the definitive treatment of distribution-free performance guarantees for robotic systems. They note that "bounds for the probability of success parameter in the Bernoulli distribution (often called binomial confidence intervals) have been studied extensively" and critically observe that "the majority of methods for binomial confidence intervals are not guaranteed to hold with a user-defined probability (e.g., Wald, Wilson, Jeffreys', Agresti-Coull)" (pqac-00000021). They identify the **Clopper–Pearson interval** as the method that provides guaranteed coverage: "the confidence interval we derive in Theorem 4 is analogous to the one-sided Clopper-Pearson interval, which is known to be unimprovable amongst non-randomized approaches" (pqac-00000020). **DOI: 10.48550/arxiv.2309.10874** (peer-reviewed, *IEEE Transactions on Robotics*).

The **Wilson score interval** is an approximate method that performs well for moderate sample sizes and is easier to compute. Wu et al. (2026, preprint) used "Wilson confidence intervals for binomial proportions" to report telerobotic intervention success rates and "Fisher's exact test" for comparing success rates between conditions (pqac-00000001). **DOI: 10.48550/arxiv.2611.18496** (preprint).

Fan et al. (2026, preprint) similarly report: "We use Wilson 95% intervals for these proportions. Safety and...Marginal success rates use Wilson intervals and small cells use Clopper–Pearson" (pqac-00000001). **DOI: 10.48550/arxiv.2606.00773** (preprint).

**Recommendation:** For robot-arm task validation, the **Clopper–Pearson (exact) interval** should be used when conservative guaranteed coverage is needed (e.g., regulatory or safety claims). The **Wilson score interval** is appropriate for routine reporting and moderate sample sizes (n > 30), as it has better average coverage properties and is less conservative.

### 2.2 Number of Trials Needed to Claim 95% Success with 95% Confidence

Using the one-sided Clopper–Pearson lower bound, if all n trials succeed, the lower confidence bound is L = 0.05^(1/n). To guarantee L ≥ 0.95, we solve n ≥ ln(0.05)/ln(0.95) = 58.4, so **n = 59 consecutive successes with zero failures** are needed (pqac-00000039, pqac-00000040). At n = 59, the lower bound is approximately 0.9505; at n = 58 it falls to approximately 0.9497, which is insufficient (pqac-00000039).

This calculation assumes independent trials, a fixed success criterion, and no failures. If even one failure occurs, more trials are needed: for example, with 1 failure in 90 trials (success rate 98.9%), the Clopper–Pearson 95% lower bound is approximately 0.942, below 0.95.

Cowling (2026, preprint) independently notes the statistical weakness of small evaluation sets: the study emphasizes that "ten evaluation episodes are generally too few for reliable model comparisons" and that "future automated testing aims for approximately 100 episodes per checkpoint" (pqac-00000042). **DOI: 10.48550/arxiv.2610.37170** (preprint).

### 2.3 Current Practice vs. Best Practice

The vast majority of SDL papers report raw proportions (e.g., "195/200" or "688 experiments completed") without any confidence interval. Of all papers reviewed, only Wu et al. (2026) explicitly used Wilson confidence intervals for robot-task success rates in an SDL context (pqac-00000001). This represents a significant methodological gap. For reproducible and comparable reporting, we recommend that all SDL papers report:

1. **Number of independent trials** (not just experiment count)
2. **Success criterion** (binary, clearly defined)
3. **Raw success count and proportion**
4. **95% Wilson or Clopper–Pearson confidence interval**
5. **Failure taxonomy** (categories of failure modes)
6. **Intervention count and MCBI** where applicable

## 3. Cost-per-Task, Throughput, and Economic Comparisons

### 3.1 Available Frameworks

No SDL paper provides a standardized **cost per robotic task** (e.g., cost per pick-and-place, cost per pipetting action) that would allow direct comparison between an affordable arm and an industrial arm. The available comparisons use heterogeneous proxies:

| Reference | Metric used | Robot/platform | Manual baseline | Automated result | Key finding | DOI |
|---|---|---|---|---|---|---|
| Reed (2021) | Quality-weighted output per total cost, \(N_Q/\mathrm{Cost}(N)\); weekly throughput | General automated materials-chemistry workflow | 560 samples/week; \(N_Q=392\); £12,127/week; efficiency 0.0323 £⁻¹ | 1,120 samples/week; \(N_Q=1{,}008\); £14,960/week; efficiency 0.0674 £⁻¹ | Automation doubled throughput and approximately doubled quality-adjusted cost efficiency, despite higher weekly expenditure. (pqac-00000004) | Not available |
| Tegally et al. (2020) | Hands-on time and personnel share of total sequencing cost | Hamilton Microlab STARlet; Agilent Bravo | 375 min hands-on library preparation; personnel represented 15% of total sequencing cost | 25 min hands-on time with Agilent Bravo—a 93% reduction; salaries fell to 4% of total cost under automated sample preparation | Quantifies labor displacement rather than full cost per experiment; capital, maintenance, depreciation, and consumables were not normalized. (pqac-00000005) | [10.1186/s12864-020-07137-1](https://doi.org/10.1186/s12864-020-07137-1) |
| Thieme et al. (2024) | Hands-on time, labor cost per sample, and five-year break-even assessment | Opentrons OT-2 liquid handler | Manual assay required 30 additional minutes of hands-on work; exact total cost per sample not reported | Hands-on time fell by 30 min per assay and labor cost per sample was halved | Labor savings alone did not recover hardware-usage costs within five years; sharing the OT-2 across workflows could improve utilization and break-even time. (pqac-00000006) | [10.1016/j.slast.2024.100180](https://doi.org/10.1016/j.slast.2024.100180) |
| Burger et al. (2020) | Available operating time, idle fraction, campaign throughput, and station moves | KUKA KMR mobile robotic chemist | No manual comparator reported | Up to 21.6 operating hours/day; 688 experiments in eight days; 319 inter-station moves; approximately 32% of campaign time idle/charging, largely while awaiting gas-chromatography analysis | Demonstrates campaign-scale utilization and exposes the analytical instrument—not manipulation—as the principal bottleneck, but does not calculate cost per task or intervention-adjusted uptime. (pqac-00000023, pqac-00000024) | [10.1038/s41586-020-2442-2](https://doi.org/10.1038/s41586-020-2442-2) |
| Langner et al. (2020) | Material consumption and maximum film-production throughput | Automated thin-film fabrication and SDL platform | Conventional screening estimated to require approximately 100 mg of material | Screened 2,000 compositions with <10 mg; platform capacity up to 6,048 films/day; autonomous optimization used <1 mg | Shows that automation can be valued through scarce-material efficiency and throughput even without a monetary cost-per-experiment calculation. | [10.1002/adma.201907801](https://doi.org/10.1002/adma.201907801) |
| Darvish et al. (2025), ORGANA | Human interaction/execution time and parallel-versus-sequential workflow duration | Franka Emika Panda with pumps, polisher, potentiostat, stirrer, and pH sensor | Human electrochemistry condition: 36.83 min for three buffer-solution iterations; sequential robotic plan averaged 21.67 min | ORGANA robot execution: 7.25 min of human-interaction burden; parallel plan averaged 17.10 min | Parallel scheduling reduced robotic workflow duration by 21.1%; the 7.25-versus-36.83-min comparison primarily measures human temporal workload and should not be treated as complete cost per experiment. (pqac-00000013, pqac-00000014) | [10.1016/j.matt.2024.10.015](https://doi.org/10.1016/j.matt.2024.10.015) |


*Table: Published comparisons use heterogeneous proxies—quality-adjusted output, hands-on labor, utilization, material consumption, and elapsed time—rather than a standardized cost per robotic task. The table identifies both the measured gains and the accounting limitations relevant to comparing affordable and industrial laboratory robots.*

The most rigorous framework is from Reed (2021), who defines laboratory efficiency as quality-weighted data points divided by total cost: NQ/Cost(N). In a worked example, manual processing of 560 samples/week at quality 0.7 yielded efficiency of 0.0323 £⁻¹, while automation (1,120 samples/week, quality 0.9) reached 0.0674 £⁻¹—"approximately twice the manual value" (pqac-00000004).

For genomics liquid handling, Tegally et al. (2020) reported that the Agilent Bravo "reduced hands-on library-preparation time from 375 minutes to 25 minutes, a reduction of approximately 93%," and that "laboratory salaries fell to 4% of total cost" under automation from 15% manually (pqac-00000005). **DOI: 10.1186/s12864-020-07137-1** (peer-reviewed, *BMC Genomics*).

Thieme et al. (2024) found that deploying the OT-2 for a metabolite-identification assay "reduced hands-on time by 30 minutes per assay and consequently halved labor cost per sample. However, the labor savings alone were not sufficient to recover the robot's hardware usage costs within a five-year period" (pqac-00000006). **DOI: 10.1016/j.slast.2024.100180** (peer-reviewed, *SLAS Technology*).

### 3.2 Toward Cost-per-Task for Affordable Arms

**No published evidence exists** for a standardized cost-per-task metric comparing affordable arms (e.g., AgileX PiPER, SO-101, Dobot) with industrial arms (UR5e, Franka, KUKA) in SDL settings. Rupp et al. (2022) report acquisition costs—Dobot Magician at approximately €1,500 and Dobot MG400 at approximately €3,000 (pqac-00000007)—but provide no throughput or cost-per-task calculations. **DOI: 10.1016/j.slast.2022.07.001** (peer-reviewed, *SLAS Technology*).

A practical cost-per-task metric for arm comparison should include: (1) capital amortization per task cycle, (2) consumable cost per cycle, (3) labor/intervention cost prorated by MCBI, (4) energy cost, and (5) opportunity cost of downtime. This calculation remains unpublished for SDL robot arms.

## 4. Benchmarks for Low-Cost Arms and Imitation Learning

### 4.1 SO-101 with LeRobot-Style Imitation Learning

Cowling (2026, preprint) provides the most detailed evaluation of imitation-learning policies on a low-cost arm in a LeRobot framework. Using an SO-101 arm for a pick-and-place task (green ball to basket), "1,340 episodes were scored in 126 blocks over 17 days" (pqac-00000037). ACT (Action Chunking with Transformers) "achieved 1/40 successes with 12 demonstrations and 37/40 with 100 demonstrations" (pqac-00000033). At 100 demonstrations, ACT reached 93% success; at 200 demonstrations, 88%. Fine-tuned π₀.₅ "performed best with scarce data, achieving 16/40 at 12 demonstrations and 28/40 at 25" (pqac-00000033). SmolVLA "failed to start moving in 47% of episodes" (pqac-00000033). **DOI: 10.48550/arxiv.2610.37170** (preprint).

### 4.2 Gaps: No SDL Application of LeRobot-Style Learning

**No published study applies LeRobot-style imitation learning (or any teleoperation-based policy learning on SO-100/SO-101 or similar low-cost arms) to SDL tasks** such as pipetting, vial transfer, powder dosing, or instrument loading. All published SO-100/SO-101 evaluations involve generic manipulation benchmarks (pick-and-place, sorting). Similarly, **no published study compares the AgileX PiPER arm** with any industrial arm for laboratory tasks. These represent clear research gaps.

### 4.3 ArUco/Fiducial-Based Calibration in SDL Systems

The use of fiducial markers for station recalibration is well-established. The LIRA system uses "20 mm ArUco markers" and achieves stable localization and 100% manipulation success across 600 pickup/insertion operations during 8 hours of continuous operation (pqac-00000030). The Burger mobile chemist uses a six-point calibration cube protocol achieving ±0.12 mm accuracy (pqac-00000025). Wienbruch et al. (2025) developed a system using "ArUco markers for object detection" with a robot arm and camera, achieving a "1.69% error rate" for automated display reading (peer-reviewed, *Scientific Reports*). **DOI: 10.1038/s41598-025-05670-1**.

## 5. Recommended Repeatable Tests for Validating an Affordable SDL Arm

Based on the published protocols identified above, the following tests can be repeated by anyone validating an affordable arm and directly compared with published results:

**Test 1 – Positional repeatability under load (after Harazono et al. 2024).** Attach a 96-well microplate to the gripper, move to a target position, and measure displacement with dial gauges. Repeat 125 times at each of two speeds. Report IQR in x and y. Compare with Dobot M1 Pro: IQR 0.020 mm (x) and 0.006 mm (y) (pqac-00000016, pqac-00000017).

**Test 2 – Transfer success vs. offset (after Harazono et al. 2024).** Introduce artificial positional offsets (Δx = 1.8–2.3 mm, Δy = 2.1–2.2 mm) when placing a lid onto a microplate. Repeat 125 times per offset. Record binary success/failure via video. Report success probability as a function of offset with Wilson 95% CI (pqac-00000017).

**Test 3 – Fiducial-based localization loop (after Zhou et al. 2025, LIRA).** Execute a station-calibrate-pick-insert loop using 20 mm ArUco markers. Run 100 consecutive loops (~5 min each, 8 hours total). Record number of successful manipulations. Compare with LIRA: 600/600 (100%) (pqac-00000030).

**Test 4 – Extended autonomous campaign (after Burger et al. 2020).** Run a multi-station workflow for ≥48 hours. Record total experiments completed, inter-station moves, idle time, and intervention count. Calculate MCBI. Compare with Burger: 688 experiments, 319 moves, 32% idle in 8 days (pqac-00000024).

**Test 5 – Imitation-learning pick-and-place (after Cowling 2026).** Collect teleoperated demonstrations (12, 25, 50, 100, 200). Train ACT policies. Evaluate on 10 fixed object placements × 4 episodes each = 40 episodes per condition. Report success rate with Wilson 95% CI. Compare with SO-101: 93% at 100 demos (pqac-00000033).

For all tests, report at minimum: arm model, gripper, task, number of independent trials, success criterion, success count, Wilson or Clopper–Pearson 95% CI, failure categories, and intervention count. To claim ≥95% true success with 95% confidence requires at least **59 consecutive successes with zero failures** using the one-sided Clopper–Pearson bound (pqac-00000039).

## 6. Summary of Evidence Gaps

- **No SDL paper reports MCBI** (mean cycles between interventions) or an equivalent metric for robot-arm tasks.
- **No standardized cost-per-task metric** exists for comparing affordable and industrial arms in SDL settings.
- **No published study evaluates the AgileX PiPER** arm for any laboratory task.
- **No published study applies LeRobot-style imitation learning to SDL tasks** (pipetting, vial handling, powder dosing, instrument loading).
- **Most SDL papers omit confidence intervals** for robot success rates; only one SDL-adjacent paper (Wu et al. 2026, preprint) used Wilson CIs.
- **No head-to-head comparison** of a low-cost arm (~$200–$2,000) versus an industrial arm (UR5e, Franka, KUKA) on a standardized SDL task has been published.
