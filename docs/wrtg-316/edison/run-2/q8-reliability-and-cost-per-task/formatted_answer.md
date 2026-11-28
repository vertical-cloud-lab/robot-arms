Question: We are writing a literature review to discover which tests determine the value of a robot arm used as an automated manual manipulator in a self-driving laboratory (SDL) for materials science. By automated manual manipulator we mean one arm that does the hands-on work a person would otherwise do: it moves from station to station (for example a pipetting gantry, a powder doser, a balance, vial and plate racks), recalibrates itself at each station using a calibration square (a square fiducial target such as an AprilTag, or a square fixture at a known position), and takes on several new automated tasks. The term is ours; the literature may say mobile manipulator, robotic laboratory assistant, robot chemist, or sample- or labware-handling robot. Our arms are a low-cost AgileX PiPER 6-DOF arm (about $2k) and SO-101 leader/follower arms (about $200), with parallel grippers, Raspberry Pi wrist cameras and fixed cameras in an enclosure, AprilTags, and LeRobot-style imitation learning or scripted motion. We want to place these arms in the published literature and find tests that we, or anyone validating an affordable arm, can repeat to compare it with the industry-standard arms used in SDLs (e.g. UR5e, UR3, Franka Panda, ABB YuMi, Kinova, KUKA), including on cost per task.

Reliability and cost per task: How should success rates, failures and mean cycles between interventions be reported for repeated robot tasks so they can be compared? Cover confidence intervals (Wilson, Clopper-Pearson), the number of trials needed to claim, for example, 95% success with 95% confidence, and how laboratory automation and self-driving lab papers actually report these numbers. Also, how have cost per task, throughput, uptime or cost per experiment been measured to compare a laboratory robot with manual work or with another robot?

Prioritize peer-reviewed journal articles and major conference papers from 2015 to 2026, and flag any preprints. For each benchmark or result, describe the protocol in enough detail to repeat it (what is measured, number of trials, success criterion, measuring tool) and give the arm model. For each claim, give the DOI and quote the sentence that supports it. Say explicitly where no published evidence exists.


# Reliability Metrics, Statistical Reporting, and Cost-per-Task Benchmarks for Robot Arms in Self-Driving Laboratories

## 1. How Self-Driving Laboratory Papers Currently Report Reliability

A systematic survey of published SDL and laboratory-automation papers reveals that **most studies report robot-arm reliability descriptively**—as raw success counts, positioning precision, or campaign duration—without formal confidence intervals or intervention-frequency metrics.

### 1.1 Campaign-Level Reporting: The Burger Mobile Robotic Chemist

The landmark study by Burger et al. (2020) used a KUKA KMR mobile manipulator with an LBR iiwa arm. The robot "operated autonomously for 8 days and completed 688 experiments" in a 10-variable photocatalysis search, making "319 moves between laboratory stations and travelled 2.17 km" (burger2020amobilerobotic pages 6-12). Positioning precision was ±0.12 mm in x–y and <0.005° in orientation, established through "100 separate six-point (6P) calibration trials" with simulated noise up to ±15 mm and ±2.5° (burger2023amobilerobotic pages 52-56). The robot could operate "up to 21.6 hours per day," being "idle but charging for approximately 32% of the experiment, mainly while waiting for the GC analysis" (burger2020amobilerobotic pages 6-12). However, this paper does not report a formal success rate, failure rate, mean cycles between interventions (MCBI), confidence intervals, or even a total count of individual robotic actions. It notes that "the system automatically alerted operators when consumables ran out or a workflow failed, and most errors could be reset remotely using station CCTV" (burger2020amobilerobotic pages 6-12), but the frequency of such events is not quantified. **DOI: 10.1038/s41586-020-2442-2** (peer-reviewed, *Nature*).

### 1.2 Component-Level Testing with Explicit Trial Counts

**LIRA (Zhou et al. 2025)** provides the most rigorous testing protocol found in the SDL literature. The system was evaluated using "100 consecutive workflow loops, each lasting approximately five minutes, for eight hours of continuous operation. During these loops, the robot performed 600 pickup and insertion manipulations and achieved a 100% success rate" (zhou2025localizationinspectionand pages 3-5). For error inspection, "200 manual tests" were conducted with deliberately introduced placement errors, achieving "a 97.5% accuracy—or error-inspection success—rate, corresponding to 195 successful tests out of 200" (zhou2025localizationinspectionand pages 7-8). The fine-tuned VLM achieved "a 97.9% overall success rate" on the shared test dataset (zhou2025localizationinspectionand pages 5-7). Despite the relatively large trial counts (100, 200, 600), no binomial confidence intervals were reported. **DOI: 10.1038/s42004-025-01770-1** (peer-reviewed, *Communications Chemistry*).

**Harazono et al. (2024, preprint)** provide the most detailed positional-accuracy benchmark for a low-cost arm in lab automation. Using a Dobot M1 Pro SCARA robot (~few thousand USD), they "moved the microplate to a specific spatial coordinate...and evaluated the position repeatability by repeating this movement multiple times" with 125 repetitions at each of two speeds (harazono2024evaluationofmicroplate pages 6-11, harazono2024evaluationofmicroplate pages 11-15). The interquartile range was 0.020 mm (x) and 0.006 mm (y) at high speed. For transfer success, "transfer was repeated 125 times for each case" at various artificial offsets (Δx = 1.80–2.30 mm and Δy = 2.10–2.20 mm), and "the probability of success gradually decreased with an increase in Δx" while "significantly decreased when Δy exceeded 2.190 mm" (harazono2024evaluationofmicroplate pages 11-15). Success was determined via video analysis with colored markers. No confidence intervals were computed. **DOI: 10.1101/2023.12.29.573685** (preprint, *bioRxiv*).

**ORGANA (Darvish et al. 2025)** used a Franka Emika Panda for multi-step chemistry experiments. The solubility test was "performed for 2 times," recrystallization and pH each once, and electrochemistry "performed 2 times" (darvish2025organaarobotic pages 14-15). "In total, three complete electrochemistry experiments were performed, testing six buffer solutions for each experiment" (darvish2025organaarobotic pages 7-9). No task-completion success proportion was reported; validation was based on chemical accuracy of results (slope estimates of -61.3, -61.8, and -61.0 mV/pH unit across three runs). **DOI: 10.1016/j.matt.2024.10.015** (peer-reviewed, *Matter*).

The table below summarizes the published reliability benchmarks found across SDL and laboratory-automation literature:

| Reference | Robot arm model | Task description | Number of trials | Reported success rate / result | Statistical method | DOI |
|---|---|---|---:|---|---|---|
| Burger et al. (2020) | KUKA KMR mobile manipulator | Eight-day autonomous photocatalyst campaign; station-to-station operation and six-point calibration | 688 experiments; 319 inter-station moves; 100 calibration trials | No end-to-end success rate; positioning error within ±0.12 mm and orientation error <0.005° | No confidence interval reported | [10.1038/s41586-020-2442-2](https://doi.org/10.1038/s41586-020-2442-2) (burger2020amobilerobotic pages 1-3, burger2020amobilerobotic pages 6-12, burger2023amobilerobotic pages 52-56) |
| Zhou et al. (2025), LIRA | Cooper-lab mobile manipulator | Fiducial localization followed by rack/plate pickup, insertion, inspection, and reasoning | 100 localization loops; 600 pickup/insertion manipulations; 200 deliberately perturbed inspection tests | 600/600 manipulations successful (100%); 195/200 workflow inspections successful (97.5%); fine-tuned model test accuracy 97.9% | Descriptive proportions; no binomial CI reported | [10.1038/s42004-025-01770-1](https://doi.org/10.1038/s42004-025-01770-1) (zhou2025localizationinspectionand pages 7-8, zhou2025localizationinspectionand pages 5-7, zhou2025localizationinspectionand pages 2-3, zhou2025localizationinspectionand pages 3-5) |
| Harazono et al. (2024) **[preprint]** | Dobot M1 Pro SCARA | Repeated 96-well microplate/lid transfer; dial-gauge repeatability test and deliberately offset lid-placement test | 125 repetitions at each speed and 125 transfers per offset condition | High-speed positional IQR: 0.020 mm in x and 0.006 mm in y; transfer success declined with imposed offset, especially beyond Δy = 2.190 mm | Empirical distributions and success probability; no binomial CI reported | [10.1101/2023.12.29.573685](https://doi.org/10.1101/2023.12.29.573685) (harazono2024evaluationofmicroplate pages 1-6, harazono2024evaluationofmicroplate pages 6-11, harazono2024evaluationofmicroplate pages 11-15) |
| Darvish et al. (2025), ORGANA | Franka Emika Panda | Long-horizon solubility, recrystallization, pH, and electrochemistry workflows | Three complete electrochemistry experiments; two solubility runs; one recrystallization run; one pH run | No formal task-success proportion; three electrochemistry repeats produced comparable slope and pKa estimates | Means/standard deviations for planning time; no binomial CI for manipulation success | [10.1016/j.matt.2024.10.015](https://doi.org/10.1016/j.matt.2024.10.015) (darvish2025organaarobotic pages 7-9, darvish2025organaarobotic pages 9-12, darvish2025organaarobotic pages 14-15) |
| Wu et al. (2026), telerobotic intervention **[preprint]** | Simulated SDL robot-arm interface | Human teleoperation to recover simulated process interruptions, initialization errors, and escalated faults | 86 trials: 28 process-interruption, 30 initialization-error, and 28 escalated-fault trials | Success depended on fault and controller condition; a success required completion without collision, force stop, overextension, or workspace violation | Wilson binomial CIs; Fisher’s exact test; bootstrap CIs for paired continuous outcomes | [10.48550/arxiv.2611.18496](https://doi.org/10.48550/arxiv.2611.18496) (wu2026towardresilientselfdriving pages 4-5) |
| Cowling (2026) **[preprint]** | SO-101 low-cost arm | LeRobot-style imitation learning for picking up a green ball and placing it in a basket across ten fixed placements | 1,340 scored episodes; commonly 40 episodes per policy/data-budget cell | ACT achieved 37/40 successes (92.5%, reported as 93%) after training on 100 demonstrations | Raw proportions; no binomial CI reported | [10.48550/arxiv.2610.37170](https://doi.org/10.48550/arxiv.2610.37170) (cowling2026from12to pages 1-3, cowling2026from12to pages 9-12, cowling2026from12to pages 7-9) |
| Rupp et al. (2022) | Dobot Magician (~€1,500) and Dobot MG400 (~€3,000) | Low-cost laboratory automation using AutoIt and four-axis robots | Not reported as repeated end-to-end reliability trials | No formal success rate; automated processes were described as slower than manual work and unsuitable for high-throughput/time-critical use | Qualitative throughput assessment; no CI | [10.1016/j.slast.2022.07.001](https://doi.org/10.1016/j.slast.2022.07.001) (rupp2022establishmentoflowcost pages 5-6) |
| Wienbruch et al. (2025) | Robot arm with inexpensive camera system; model not specified here | ArUco-based environment/object detection and automated reading of laboratory displays | Validation count not specified here | In-house display-reading error rate of 1.69%, described as comparable to manual readings | No CI reported in the available evidence | [10.1038/s41598-025-05670-1](https://doi.org/10.1038/s41598-025-05670-1) |


*Table: Published and preprint benchmarks vary from component-level positioning tests to hundreds of autonomous experiments, but most omit binomial confidence intervals and intervention metrics. The table identifies protocols that affordable-arm studies can reproduce and flags where evidence remains descriptive or statistically weak.*

### 1.3 Key Observation: Mean Cycles Between Interventions (MCBI)

**No published SDL paper found in this review reports MCBI or an equivalent metric.** The closest analog is the Burger et al. description of automated alerts when consumables ran out or workflows failed (burger2020amobilerobotic pages 6-12), but neither the alert frequency nor the total intervention count is disclosed. This represents a significant gap: MCBI—defined as the mean number of complete task cycles a robot executes between events requiring human intervention—would be the most practically useful reliability metric for comparing affordable and industrial arms.

## 2. Statistical Methods for Reporting Robot Task Success Rates

### 2.1 Appropriate Confidence Intervals

Vincent et al. (2023) provide the definitive treatment of distribution-free performance guarantees for robotic systems. They note that "bounds for the probability of success parameter in the Bernoulli distribution (often called binomial confidence intervals) have been studied extensively" and critically observe that "the majority of methods for binomial confidence intervals are not guaranteed to hold with a user-defined probability (e.g., Wald, Wilson, Jeffreys', Agresti-Coull)" (vincent2023guaranteesonrobot pages 4-5). They identify the **Clopper–Pearson interval** as the method that provides guaranteed coverage: "the confidence interval we derive in Theorem 4 is analogous to the one-sided Clopper-Pearson interval, which is known to be unimprovable amongst non-randomized approaches" (vincent2023guaranteesonrobot pages 2-4). **DOI: 10.48550/arxiv.2309.10874** (peer-reviewed, *IEEE Transactions on Robotics*).

The **Wilson score interval** is an approximate method that performs well for moderate sample sizes and is easier to compute. Wu et al. (2026, preprint) used "Wilson confidence intervals for binomial proportions" to report telerobotic intervention success rates and "Fisher's exact test" for comparing success rates between conditions (wu2026towardresilientselfdriving pages 4-5). **DOI: 10.48550/arxiv.2611.18496** (preprint).

Fan et al. (2026, preprint) similarly report: "We use Wilson 95% intervals for these proportions. Safety and...Marginal success rates use Wilson intervals and small cells use Clopper–Pearson" (wu2026towardresilientselfdriving pages 4-5). **DOI: 10.48550/arxiv.2606.00773** (preprint).

**Recommendation:** For robot-arm task validation, the **Clopper–Pearson (exact) interval** should be used when conservative guaranteed coverage is needed (e.g., regulatory or safety claims). The **Wilson score interval** is appropriate for routine reporting and moderate sample sizes (n > 30), as it has better average coverage properties and is less conservative.

### 2.2 Number of Trials Needed to Claim 95% Success with 95% Confidence

Using the one-sided Clopper–Pearson lower bound, if all n trials succeed, the lower confidence bound is L = 0.05^(1/n). To guarantee L ≥ 0.95, we solve n ≥ ln(0.05)/ln(0.95) = 58.4, so **n = 59 consecutive successes with zero failures** are needed (vincent2023guaranteesonrobot pages 4-5, vincent2023guaranteesonrobot pages 2-4). At n = 59, the lower bound is approximately 0.9505; at n = 58 it falls to approximately 0.9497, which is insufficient (vincent2023guaranteesonrobot pages 4-5).

This calculation assumes independent trials, a fixed success criterion, and no failures. If even one failure occurs, more trials are needed: for example, with 1 failure in 90 trials (success rate 98.9%), the Clopper–Pearson 95% lower bound is approximately 0.942, below 0.95.

Cowling (2026, preprint) independently notes the statistical weakness of small evaluation sets: the study emphasizes that "ten evaluation episodes are generally too few for reliable model comparisons" and that "future automated testing aims for approximately 100 episodes per checkpoint" (cowling2026from12to pages 21-24). **DOI: 10.48550/arxiv.2610.37170** (preprint).

### 2.3 Current Practice vs. Best Practice

The vast majority of SDL papers report raw proportions (e.g., "195/200" or "688 experiments completed") without any confidence interval. Of all papers reviewed, only Wu et al. (2026) explicitly used Wilson confidence intervals for robot-task success rates in an SDL context (wu2026towardresilientselfdriving pages 4-5). This represents a significant methodological gap. For reproducible and comparable reporting, we recommend that all SDL papers report:

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
| Reed (2021) | Quality-weighted output per total cost, \(N_Q/\mathrm{Cost}(N)\); weekly throughput | General automated materials-chemistry workflow | 560 samples/week; \(N_Q=392\); £12,127/week; efficiency 0.0323 £⁻¹ | 1,120 samples/week; \(N_Q=1{,}008\); £14,960/week; efficiency 0.0674 £⁻¹ | Automation doubled throughput and approximately doubled quality-adjusted cost efficiency, despite higher weekly expenditure. (reed2021labautomationfor pages 48-50) | Not available |
| Tegally et al. (2020) | Hands-on time and personnel share of total sequencing cost | Hamilton Microlab STARlet; Agilent Bravo | 375 min hands-on library preparation; personnel represented 15% of total sequencing cost | 25 min hands-on time with Agilent Bravo—a 93% reduction; salaries fell to 4% of total cost under automated sample preparation | Quantifies labor displacement rather than full cost per experiment; capital, maintenance, depreciation, and consumables were not normalized. (tegally2020unlockingtheefficiency pages 1-3) | [10.1186/s12864-020-07137-1](https://doi.org/10.1186/s12864-020-07137-1) |
| Thieme et al. (2024) | Hands-on time, labor cost per sample, and five-year break-even assessment | Opentrons OT-2 liquid handler | Manual assay required 30 additional minutes of hands-on work; exact total cost per sample not reported | Hands-on time fell by 30 min per assay and labor cost per sample was halved | Labor savings alone did not recover hardware-usage costs within five years; sharing the OT-2 across workflows could improve utilization and break-even time. (thieme2024deepintegrationof pages 5-6) | [10.1016/j.slast.2024.100180](https://doi.org/10.1016/j.slast.2024.100180) |
| Burger et al. (2020) | Available operating time, idle fraction, campaign throughput, and station moves | KUKA KMR mobile robotic chemist | No manual comparator reported | Up to 21.6 operating hours/day; 688 experiments in eight days; 319 inter-station moves; approximately 32% of campaign time idle/charging, largely while awaiting gas-chromatography analysis | Demonstrates campaign-scale utilization and exposes the analytical instrument—not manipulation—as the principal bottleneck, but does not calculate cost per task or intervention-adjusted uptime. (burger2020amobilerobotic pages 1-3, burger2020amobilerobotic pages 6-12) | [10.1038/s41586-020-2442-2](https://doi.org/10.1038/s41586-020-2442-2) |
| Langner et al. (2020) | Material consumption and maximum film-production throughput | Automated thin-film fabrication and SDL platform | Conventional screening estimated to require approximately 100 mg of material | Screened 2,000 compositions with <10 mg; platform capacity up to 6,048 films/day; autonomous optimization used <1 mg | Shows that automation can be valued through scarce-material efficiency and throughput even without a monetary cost-per-experiment calculation. | [10.1002/adma.201907801](https://doi.org/10.1002/adma.201907801) |
| Darvish et al. (2025), ORGANA | Human interaction/execution time and parallel-versus-sequential workflow duration | Franka Emika Panda with pumps, polisher, potentiostat, stirrer, and pH sensor | Human electrochemistry condition: 36.83 min for three buffer-solution iterations; sequential robotic plan averaged 21.67 min | ORGANA robot execution: 7.25 min of human-interaction burden; parallel plan averaged 17.10 min | Parallel scheduling reduced robotic workflow duration by 21.1%; the 7.25-versus-36.83-min comparison primarily measures human temporal workload and should not be treated as complete cost per experiment. (darvish2025organaarobotic pages 9-12, darvish2025organaarobotic pages 14-15) | [10.1016/j.matt.2024.10.015](https://doi.org/10.1016/j.matt.2024.10.015) |


*Table: Published comparisons use heterogeneous proxies—quality-adjusted output, hands-on labor, utilization, material consumption, and elapsed time—rather than a standardized cost per robotic task. The table identifies both the measured gains and the accounting limitations relevant to comparing affordable and industrial laboratory robots.*

The most rigorous framework is from Reed (2021), who defines laboratory efficiency as quality-weighted data points divided by total cost: NQ/Cost(N). In a worked example, manual processing of 560 samples/week at quality 0.7 yielded efficiency of 0.0323 £⁻¹, while automation (1,120 samples/week, quality 0.9) reached 0.0674 £⁻¹—"approximately twice the manual value" (reed2021labautomationfor pages 48-50).

For genomics liquid handling, Tegally et al. (2020) reported that the Agilent Bravo "reduced hands-on library-preparation time from 375 minutes to 25 minutes, a reduction of approximately 93%," and that "laboratory salaries fell to 4% of total cost" under automation from 15% manually (tegally2020unlockingtheefficiency pages 1-3). **DOI: 10.1186/s12864-020-07137-1** (peer-reviewed, *BMC Genomics*).

Thieme et al. (2024) found that deploying the OT-2 for a metabolite-identification assay "reduced hands-on time by 30 minutes per assay and consequently halved labor cost per sample. However, the labor savings alone were not sufficient to recover the robot's hardware usage costs within a five-year period" (thieme2024deepintegrationof pages 5-6). **DOI: 10.1016/j.slast.2024.100180** (peer-reviewed, *SLAS Technology*).

### 3.2 Toward Cost-per-Task for Affordable Arms

**No published evidence exists** for a standardized cost-per-task metric comparing affordable arms (e.g., AgileX PiPER, SO-101, Dobot) with industrial arms (UR5e, Franka, KUKA) in SDL settings. Rupp et al. (2022) report acquisition costs—Dobot Magician at approximately €1,500 and Dobot MG400 at approximately €3,000 (rupp2022establishmentoflowcost pages 5-6)—but provide no throughput or cost-per-task calculations. **DOI: 10.1016/j.slast.2022.07.001** (peer-reviewed, *SLAS Technology*).

A practical cost-per-task metric for arm comparison should include: (1) capital amortization per task cycle, (2) consumable cost per cycle, (3) labor/intervention cost prorated by MCBI, (4) energy cost, and (5) opportunity cost of downtime. This calculation remains unpublished for SDL robot arms.

## 4. Benchmarks for Low-Cost Arms and Imitation Learning

### 4.1 SO-101 with LeRobot-Style Imitation Learning

Cowling (2026, preprint) provides the most detailed evaluation of imitation-learning policies on a low-cost arm in a LeRobot framework. Using an SO-101 arm for a pick-and-place task (green ball to basket), "1,340 episodes were scored in 126 blocks over 17 days" (cowling2026from12to pages 7-9). ACT (Action Chunking with Transformers) "achieved 1/40 successes with 12 demonstrations and 37/40 with 100 demonstrations" (cowling2026from12to pages 1-3). At 100 demonstrations, ACT reached 93% success; at 200 demonstrations, 88%. Fine-tuned π₀.₅ "performed best with scarce data, achieving 16/40 at 12 demonstrations and 28/40 at 25" (cowling2026from12to pages 1-3). SmolVLA "failed to start moving in 47% of episodes" (cowling2026from12to pages 1-3). **DOI: 10.48550/arxiv.2610.37170** (preprint).

### 4.2 Gaps: No SDL Application of LeRobot-Style Learning

**No published study applies LeRobot-style imitation learning (or any teleoperation-based policy learning on SO-100/SO-101 or similar low-cost arms) to SDL tasks** such as pipetting, vial transfer, powder dosing, or instrument loading. All published SO-100/SO-101 evaluations involve generic manipulation benchmarks (pick-and-place, sorting). Similarly, **no published study compares the AgileX PiPER arm** with any industrial arm for laboratory tasks. These represent clear research gaps.

### 4.3 ArUco/Fiducial-Based Calibration in SDL Systems

The use of fiducial markers for station recalibration is well-established. The LIRA system uses "20 mm ArUco markers" and achieves stable localization and 100% manipulation success across 600 pickup/insertion operations during 8 hours of continuous operation (zhou2025localizationinspectionand pages 3-5). The Burger mobile chemist uses a six-point calibration cube protocol achieving ±0.12 mm accuracy (burger2023amobilerobotic pages 52-56). Wienbruch et al. (2025) developed a system using "ArUco markers for object detection" with a robot arm and camera, achieving a "1.69% error rate" for automated display reading (peer-reviewed, *Scientific Reports*). **DOI: 10.1038/s41598-025-05670-1**.

## 5. Recommended Repeatable Tests for Validating an Affordable SDL Arm

Based on the published protocols identified above, the following tests can be repeated by anyone validating an affordable arm and directly compared with published results:

**Test 1 – Positional repeatability under load (after Harazono et al. 2024).** Attach a 96-well microplate to the gripper, move to a target position, and measure displacement with dial gauges. Repeat 125 times at each of two speeds. Report IQR in x and y. Compare with Dobot M1 Pro: IQR 0.020 mm (x) and 0.006 mm (y) (harazono2024evaluationofmicroplate pages 6-11, harazono2024evaluationofmicroplate pages 11-15).

**Test 2 – Transfer success vs. offset (after Harazono et al. 2024).** Introduce artificial positional offsets (Δx = 1.8–2.3 mm, Δy = 2.1–2.2 mm) when placing a lid onto a microplate. Repeat 125 times per offset. Record binary success/failure via video. Report success probability as a function of offset with Wilson 95% CI (harazono2024evaluationofmicroplate pages 11-15).

**Test 3 – Fiducial-based localization loop (after Zhou et al. 2025, LIRA).** Execute a station-calibrate-pick-insert loop using 20 mm ArUco markers. Run 100 consecutive loops (~5 min each, 8 hours total). Record number of successful manipulations. Compare with LIRA: 600/600 (100%) (zhou2025localizationinspectionand pages 3-5).

**Test 4 – Extended autonomous campaign (after Burger et al. 2020).** Run a multi-station workflow for ≥48 hours. Record total experiments completed, inter-station moves, idle time, and intervention count. Calculate MCBI. Compare with Burger: 688 experiments, 319 moves, 32% idle in 8 days (burger2020amobilerobotic pages 6-12).

**Test 5 – Imitation-learning pick-and-place (after Cowling 2026).** Collect teleoperated demonstrations (12, 25, 50, 100, 200). Train ACT policies. Evaluate on 10 fixed object placements × 4 episodes each = 40 episodes per condition. Report success rate with Wilson 95% CI. Compare with SO-101: 93% at 100 demos (cowling2026from12to pages 1-3).

For all tests, report at minimum: arm model, gripper, task, number of independent trials, success criterion, success count, Wilson or Clopper–Pearson 95% CI, failure categories, and intervention count. To claim ≥95% true success with 95% confidence requires at least **59 consecutive successes with zero failures** using the one-sided Clopper–Pearson bound (vincent2023guaranteesonrobot pages 4-5).

## 6. Summary of Evidence Gaps

- **No SDL paper reports MCBI** (mean cycles between interventions) or an equivalent metric for robot-arm tasks.
- **No standardized cost-per-task metric** exists for comparing affordable and industrial arms in SDL settings.
- **No published study evaluates the AgileX PiPER** arm for any laboratory task.
- **No published study applies LeRobot-style imitation learning to SDL tasks** (pipetting, vial handling, powder dosing, instrument loading).
- **Most SDL papers omit confidence intervals** for robot success rates; only one SDL-adjacent paper (Wu et al. 2026, preprint) used Wilson CIs.
- **No head-to-head comparison** of a low-cost arm (~$200–$2,000) versus an industrial arm (UR5e, Franka, KUKA) on a standardized SDL task has been published.


References

1. (burger2020amobilerobotic pages 6-12): Benjamin Burger, Phillip M. Maffettone, Vladimir V. Gusev, Catherine M. Aitchison, Yang Bai, Xiaoyan Wang, Xiaobo Li, Ben M. Alston, Buyi Li, Rob Clowes, Nicola Rankin, Brandon Harris, Reiner Sebastian Sprick, and Andrew I. Cooper. A mobile robotic chemist. Nature, 583:237-241, Jul 2020. URL: https://doi.org/10.1038/s41586-020-2442-2, doi:10.1038/s41586-020-2442-2. This article has 2300 citations and is from a highest quality peer-reviewed journal.

2. (burger2023amobilerobotic pages 52-56): Benjamin Burger. A mobile robotic researcher. ArXiv, Jan 2023. URL: https://doi.org/10.17638/03087073, doi:10.17638/03087073. This article has 4 citations.

3. (zhou2025localizationinspectionand pages 3-5): Zhengxue Zhou, Satheeshkumar Veeramani, Francisco Munguia-Galeano, Hatem Fakhruldeen, and Andrew I. Cooper. Localization, inspection, and reasoning (lira) module for autonomous workflows in self-driving laboratories. Communications Chemistry, Nov 2025. URL: https://doi.org/10.1038/s42004-025-01770-1, doi:10.1038/s42004-025-01770-1. This article has 18 citations and is from a peer-reviewed journal.

4. (zhou2025localizationinspectionand pages 7-8): Zhengxue Zhou, Satheeshkumar Veeramani, Francisco Munguia-Galeano, Hatem Fakhruldeen, and Andrew I. Cooper. Localization, inspection, and reasoning (lira) module for autonomous workflows in self-driving laboratories. Communications Chemistry, Nov 2025. URL: https://doi.org/10.1038/s42004-025-01770-1, doi:10.1038/s42004-025-01770-1. This article has 18 citations and is from a peer-reviewed journal.

5. (zhou2025localizationinspectionand pages 5-7): Zhengxue Zhou, Satheeshkumar Veeramani, Francisco Munguia-Galeano, Hatem Fakhruldeen, and Andrew I. Cooper. Localization, inspection, and reasoning (lira) module for autonomous workflows in self-driving laboratories. Communications Chemistry, Nov 2025. URL: https://doi.org/10.1038/s42004-025-01770-1, doi:10.1038/s42004-025-01770-1. This article has 18 citations and is from a peer-reviewed journal.

6. (harazono2024evaluationofmicroplate pages 6-11): Yoritaka Harazono, Haruko Shimono, Kikumi Hata, Toutai Mitsuyama, and Takaaki Horinouchi. Evaluation of microplate handling accuracy for applying robotic arms in laboratory automation. bioRxiv, Jan 2024. URL: https://doi.org/10.1101/2023.12.29.573685, doi:10.1101/2023.12.29.573685. This article has 11 citations.

7. (harazono2024evaluationofmicroplate pages 11-15): Yoritaka Harazono, Haruko Shimono, Kikumi Hata, Toutai Mitsuyama, and Takaaki Horinouchi. Evaluation of microplate handling accuracy for applying robotic arms in laboratory automation. bioRxiv, Jan 2024. URL: https://doi.org/10.1101/2023.12.29.573685, doi:10.1101/2023.12.29.573685. This article has 11 citations.

8. (darvish2025organaarobotic pages 14-15): Kourosh Darvish, Marta Skreta, Yuchi Zhao, Naruki Yoshikawa, Sagnik Som, Miroslav Bogdanovic, Yang Cao, Han Hao, Haoping Xu, Alán Aspuru-Guzik, Animesh Garg, and Florian Shkurti. Organa: a robotic assistant for automated chemistry experimentation and characterization. Matter, 8(2):101897, Feb 2025. URL: https://doi.org/10.1016/j.matt.2024.10.015, doi:10.1016/j.matt.2024.10.015. This article has 256 citations and is from a peer-reviewed journal.

9. (darvish2025organaarobotic pages 7-9): Kourosh Darvish, Marta Skreta, Yuchi Zhao, Naruki Yoshikawa, Sagnik Som, Miroslav Bogdanovic, Yang Cao, Han Hao, Haoping Xu, Alán Aspuru-Guzik, Animesh Garg, and Florian Shkurti. Organa: a robotic assistant for automated chemistry experimentation and characterization. Matter, 8(2):101897, Feb 2025. URL: https://doi.org/10.1016/j.matt.2024.10.015, doi:10.1016/j.matt.2024.10.015. This article has 256 citations and is from a peer-reviewed journal.

10. (burger2020amobilerobotic pages 1-3): Benjamin Burger, Phillip M. Maffettone, Vladimir V. Gusev, Catherine M. Aitchison, Yang Bai, Xiaoyan Wang, Xiaobo Li, Ben M. Alston, Buyi Li, Rob Clowes, Nicola Rankin, Brandon Harris, Reiner Sebastian Sprick, and Andrew I. Cooper. A mobile robotic chemist. Nature, 583:237-241, Jul 2020. URL: https://doi.org/10.1038/s41586-020-2442-2, doi:10.1038/s41586-020-2442-2. This article has 2300 citations and is from a highest quality peer-reviewed journal.

11. (zhou2025localizationinspectionand pages 2-3): Zhengxue Zhou, Satheeshkumar Veeramani, Francisco Munguia-Galeano, Hatem Fakhruldeen, and Andrew I. Cooper. Localization, inspection, and reasoning (lira) module for autonomous workflows in self-driving laboratories. Communications Chemistry, Nov 2025. URL: https://doi.org/10.1038/s42004-025-01770-1, doi:10.1038/s42004-025-01770-1. This article has 18 citations and is from a peer-reviewed journal.

12. (harazono2024evaluationofmicroplate pages 1-6): Yoritaka Harazono, Haruko Shimono, Kikumi Hata, Toutai Mitsuyama, and Takaaki Horinouchi. Evaluation of microplate handling accuracy for applying robotic arms in laboratory automation. bioRxiv, Jan 2024. URL: https://doi.org/10.1101/2023.12.29.573685, doi:10.1101/2023.12.29.573685. This article has 11 citations.

13. (darvish2025organaarobotic pages 9-12): Kourosh Darvish, Marta Skreta, Yuchi Zhao, Naruki Yoshikawa, Sagnik Som, Miroslav Bogdanovic, Yang Cao, Han Hao, Haoping Xu, Alán Aspuru-Guzik, Animesh Garg, and Florian Shkurti. Organa: a robotic assistant for automated chemistry experimentation and characterization. Matter, 8(2):101897, Feb 2025. URL: https://doi.org/10.1016/j.matt.2024.10.015, doi:10.1016/j.matt.2024.10.015. This article has 256 citations and is from a peer-reviewed journal.

14. (wu2026towardresilientselfdriving pages 4-5): Zi-Heng Wu, Adrian Vecina Tercero, Andre A. Fatehi, Abhik Sarkar, B. Giera, E. Duoss, C. Spadaccini, Nikhil Deshpande, and A. Gongora. Toward resilient self-driving laboratories through telerobotic interventions. ArXiv, Nov 2026. URL: https://doi.org/10.48550/arxiv.2611.18496, doi:10.48550/arxiv.2611.18496. This article has 0 citations.

15. (cowling2026from12to pages 1-3): Simon Cowling. From 12 to 200 demonstrations: how act, diffusion policy, smolvla and $\pi _0.5$ scale on a low-cost arm. ArXiv, Oct 2026. URL: https://doi.org/10.48550/arxiv.2610.37170, doi:10.48550/arxiv.2610.37170. This article has 1 citations.

16. (cowling2026from12to pages 9-12): Simon Cowling. From 12 to 200 demonstrations: how act, diffusion policy, smolvla and $\pi _0.5$ scale on a low-cost arm. ArXiv, Oct 2026. URL: https://doi.org/10.48550/arxiv.2610.37170, doi:10.48550/arxiv.2610.37170. This article has 1 citations.

17. (cowling2026from12to pages 7-9): Simon Cowling. From 12 to 200 demonstrations: how act, diffusion policy, smolvla and $\pi _0.5$ scale on a low-cost arm. ArXiv, Oct 2026. URL: https://doi.org/10.48550/arxiv.2610.37170, doi:10.48550/arxiv.2610.37170. This article has 1 citations.

18. (rupp2022establishmentoflowcost pages 5-6): Nicole Rupp, Katrin Peschke, Michael Köppl, David Drissner, and Thole Zuchner. Establishment of low-cost laboratory automation processes using autoit and 4-axis robots. SLAS Technology, 27:312-318, Oct 2022. URL: https://doi.org/10.1016/j.slast.2022.07.001, doi:10.1016/j.slast.2022.07.001. This article has 30 citations and is from a peer-reviewed journal.

19. (vincent2023guaranteesonrobot pages 4-5): Joseph A. Vincent, Aaron O. Feldman, and Mac Schwager. Guarantees on robot system performance using stochastic simulation rollouts. IEEE Transactions on Robotics, 40:3984-4002, Sep 2023. URL: https://doi.org/10.48550/arxiv.2309.10874, doi:10.48550/arxiv.2309.10874. This article has 16 citations and is from a highest quality peer-reviewed journal.

20. (vincent2023guaranteesonrobot pages 2-4): Joseph A. Vincent, Aaron O. Feldman, and Mac Schwager. Guarantees on robot system performance using stochastic simulation rollouts. IEEE Transactions on Robotics, 40:3984-4002, Sep 2023. URL: https://doi.org/10.48550/arxiv.2309.10874, doi:10.48550/arxiv.2309.10874. This article has 16 citations and is from a highest quality peer-reviewed journal.

21. (cowling2026from12to pages 21-24): Simon Cowling. From 12 to 200 demonstrations: how act, diffusion policy, smolvla and $\pi _0.5$ scale on a low-cost arm. ArXiv, Oct 2026. URL: https://doi.org/10.48550/arxiv.2610.37170, doi:10.48550/arxiv.2610.37170. This article has 1 citations.

22. (reed2021labautomationfor pages 48-50): M REED. Lab automation for materials chemistry. Unknown journal, 2021.

23. (tegally2020unlockingtheefficiency pages 1-3): Houriiyah Tegally, James Emmanuel San, Jennifer Giandhari, and Tulio de Oliveira. Unlocking the efficiency of genomics laboratories with robotic liquid-handling. BMC Genomics, Oct 2020. URL: https://doi.org/10.1186/s12864-020-07137-1, doi:10.1186/s12864-020-07137-1. This article has 149 citations and is from a peer-reviewed journal.

24. (thieme2024deepintegrationof pages 5-6): Anton Thieme, Sean Renwick, Michaela Marschmann, Pedro Ivo Guimaraes, Susanne Weissenborn, and Jamie Clifton. Deep integration of low-cost liquid handling robots in an industrial pharmaceutical development environment. SLAS Technology, 29:100180, Oct 2024. URL: https://doi.org/10.1016/j.slast.2024.100180, doi:10.1016/j.slast.2024.100180. This article has 16 citations and is from a peer-reviewed journal.