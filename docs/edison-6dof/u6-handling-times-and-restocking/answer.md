## Measured Robot Handling Times, Digital Twins, Human Decision Latency, Consumable Restocking, and Time-Study Methods for Self-Driving Laboratories

This report synthesizes the available peer-reviewed and preprint evidence (2015–2026) across the five questions posed. A key finding is that **published per-operation handling times with statistical spread are extremely scarce**; most SDL papers report aggregate cycle times or campaign-level throughput without isolating individual robot manipulation operations or reporting robot idle fractions. The table below consolidates what has been published.

| System/source | Robot class | Operation or campaign metric | Published measurement | Spread / reliability | Evidence quality and caveat |
|---|---|---|---:|---|---|
| Xie et al., 2026, *STAM Methods*, DOI [10.1080/27660400.2026.2735657](https://doi.org/10.1080/27660400.2026.2735657) | Industrial robot arm; model not established in retrieved text | Pick up sample and load induction furnace | ≈60 s | Not reported | Explicit step time (xie2026developmentofan pages 9-13) |
| Xie et al., 2026 | Industrial robot arm | Weigh sample and transfer it to XRD | ≈40 s | Not reported | Combined operation; XRD loading was not timed separately (xie2026developmentofan pages 9-13) |
| Xie et al., 2026 | Integrated automated cell | XRD measurement and analysis | ≈400 s | Not reported | Instrument plus analysis time, not handling alone (xie2026developmentofan pages 9-13) |
| Xie et al., 2026 | Integrated automated cell | Impact testing and analysis | ≈120 s | Not reported | Instrument plus analysis time (xie2026developmentofan pages 9-13) |
| Xie et al., 2026 | Industrial robot arm | Recover fractured sample | ≈180 s | Not reported | Explicit recovery-step time (xie2026developmentofan pages 9-13) |
| Xie et al., 2026 | One arm, furnace, XRD and impact tester | Complete non-heat-treatment workflow | ≤800 s/sample (≈13.3 min) | Not reported | Listed steps total 800 s; adding the stated 3,600-s heat treatment gives ≈4,400 s, or 73.3 min (xie2026developmentofan pages 9-13, xie2026developmentofan pages 20-23) |
| Lunt et al., 2023 preprint; peer-reviewed version DOI [10.1039/D3SC06206F](https://doi.org/10.1039/D3SC06206F) | KUKA KMR iiwa mobile manipulator | Deliver samples to preparation station | ≈42 s | Not reported | Derived from successive demonstration-video timestamps, not a replicated time study (lunt2023modularmultirobotintegration pages 12-16, lunt2023modularmultirobotintegration pages 1-3) |
| Lunt et al., 2023/2024 | KUKA KMR iiwa | Transport prepared PXRD plate to diffractometer | ≈19 s | Not reported | Video-timestamp estimate (lunt2023modularmultirobotintegration pages 12-16) |
| Lunt et al., 2023/2024 | KUKA KMR iiwa | Open diffractometer sliding doors | ≈12 s | Not reported | Video-timestamp estimate (lunt2023modularmultirobotintegration pages 12-16) |
| Lunt et al., 2023/2024 | KUKA KMR iiwa | Load plate into diffractometer | ≈23 s | Not reported | Video-timestamp estimate (lunt2023modularmultirobotintegration pages 12-16) |
| Lunt et al., 2023/2024 | KUKA KMR iiwa | Close doors before collection | ≈25 s | Not reported | Video-timestamp estimate (lunt2023modularmultirobotintegration pages 12-16) |
| Lunt et al., 2023/2024 | ABB YuMi dual-arm cobot | Vial-cap manipulation | ≈88 s | Not reported | Video-timestamp estimate; operation boundary may include intervening motion (lunt2023modularmultirobotintegration pages 12-16) |
| Lunt et al., 2024 | ABB YuMi dual-arm cobot | Automated grinding/agitation | 2 min stirring + 2 min shaking per vial | Not reported | Programmed process time rather than observed manipulation time (lunt2024modularmultirobotintegration pages 8-16) |
| Ali et al., 2018, DOI [10.14313/JAMRIS_4-2017/36](https://doi.org/10.14313/JAMRIS_4-2017/36) | H20 dual-arm mobile robot | Charging station → grasp station → place station → charging station | Mean 15 min 32 s without fine correction; 11 min 26 s with correction | Across 50 runs: 13:22–17:20 without correction; 10:46–12:44 with correction | End-to-end route includes station interactions; pick/place and travel were not separated (ali2018mobilerobottransportation pages 8-9) |
| Ali et al., 2018 | H20 dual-arm mobile robot | Station pose correction | 4.5 s + distance error ÷ 8.3 cm/s | Depends on initial distance error | Formula comprises 3 s stabilization, 1.5 s sensing/communication, and corrective travel (ali2018mobilerobottransportation pages 11-13) |
| Ali et al., 2017, DOI [10.25046/aj0203155](https://doi.org/10.25046/aj0203155) | H20 dual-arm mobile robot | Arm motion from rest to labware manipulation point | ≈30 s | Not reported | Approach/grasp movement only; not a full pick-and-deliver cycle (ali2017graspingandplacing pages 8-10) |
| Ahlquist, 2024 report/preprint, DOI [10.2172/2459394](https://doi.org/10.2172/2459394) | MARS industrial arm on linear rail, liquid handler and plate reader | Complete serial experiment | Mean 86.2 min | CV 2.2% for labware-transport suboperations | Suboperations were timestamped, but retrieved prose does not print their individual numerical times (ahlquist2024improvingselfdrivinglabs pages 6-12) |
| Ahlquist, 2024 | MARS integrated cell | Illustrative parallelized schedule | 24.6 min | 71.4% shorter than serial schedule | Scheduling estimate based on measured operation durations, not a reported campaign validation (ahlquist2024improvingselfdrivinglabs pages 6-12) |
| Ahlquist, 2024 | MARS robot grippers | Campaign completion reliability | Earlier failures 29–43%; improved failures 4.4–7.2% | Improved campaign reliability ≥93% | Reliability depends on campaign length; handling and gripper communication dominated failures (ahlquist2024improvingselfdrivinglabs pages 1-6, ahlquist2024improvingselfdrivinglabs pages 6-12) |
| Crain et al., 2025, DOI [10.1063/5.0198335](https://doi.org/10.1063/5.0198335) | Low-payload Meca500 six-axis industrial arm | Automated XRD campaign | 84 samples in ≈24 h | Not reported | ≈17.1 min/sample is derived and includes alignment, long-exposure measurement and handling; loading alone was described only as taking seconds (crain2025designofa pages 1-5, crain2025designofa pages 5-10) |
| Chu, 2016 dissertation, DOI [10.18453/rosdok_id00002364](https://doi.org/10.18453/rosdok_id00002364) | Laboratory robotic sample-preparation platform | Complete automated preparation | 81 min 5 s | Not reported | Manual comparison was 30 min 40 s; no isolated pick/place distributions were published (chu2016automationstrategiesfor pages 135-138) |
| Chu, 2016 | Laboratory robotic platform | Dilute chiral compounds | 12 min 59 s | Not reported | Aggregate process step (chu2016automationstrategiesfor pages 135-138) |
| Chu, 2016 | Laboratory robotic platform | Prepare calibration / auxiliary / derivatization solutions | 5:57 / 15:05 / 24:01 | Not reported | Aggregate steps containing many pipetting and transfer actions (chu2016automationstrategiesfor pages 135-138) |
| Chu, 2016 | Laboratory robotic platform | Final dilution | 23 min 3 s | Not reported | Included reaction quenching and microplate transport (chu2016automationstrategiesfor pages 135-138) |
| Hernández-del-Valle et al., 2026 **preprint**, DOI [10.26434/chemrxiv.15007960/v1](https://doi.org/10.26434/chemrxiv.15007960/v1) | Low-cost TurtleBot4 mobile base | Mobile transport demonstration | ≈96 trips in 6 h; derived ≈3.75 min/trip | Included charging pause below 30% battery | Average includes task execution and charging, so it is not pure navigation or docking time (hernandezdelvalle2026perceptiondrivenexperimentalworkflows pages 10-12) |
| Hernández-del-Valle et al., 2026 **preprint** | Cobot specimen-processing cell | Detect, grasp, verify, align, cut, verify and store specimen | 190 specimens in 274 min; mean ≈86.5 s/specimen | 2 recoverable and 2 unresolved errors | Composite cycle rather than isolated pick/place time (hernandezdelvalle2026perceptiondrivenexperimentalworkflows pages 10-12) |
| Szymanski et al., 2023, *Nature*, DOI [10.1038/s41586-023-06734-w](https://doi.org/10.1038/s41586-023-06734-w) | A-Lab industrial robotic synthesis cell | Closed-loop campaign | 355 experiments over 17 continuous days | 130 successful recipes; 41 of 58 targets realized | Derived throughput ≈20.9 experiments/day and ≈2.4 successful target compounds/day; the paper does not report robot idle fraction or per-handling-operation spread (szymanski2023anautonomouslaboratory pages 2-3, szymanski2023anautonomouslaboratory pages 4-5) |


*Table: Measured or derivable robot-handling and campaign timings reported for laboratory automation systems. The table distinguishes explicit measurements from video-derived or aggregate estimates and highlights the pervasive absence of per-operation variance and robot-utilization data.*

---

### (1) Measured Cycle Times and Handling Times for Robot Arms and Mobile Manipulators

**Per-step times from materials-science SDLs.** The most granular published step-level timing comes from Xie et al. (2026), who report an automated structural-metallic-materials workflow comprising one robot arm, one induction furnace, one XRD, and one impact tester. Per-sample measured times are: "sample pick-up and loading into the induction furnace takes approximately 60 seconds; weighing the sample and transferring it to the XRD takes 40 seconds; X-ray diffraction measurement and analysis takes 400 seconds; impact testing and analysis takes 120 seconds; and recovery of the fractured sample takes 180 seconds," totaling ≤800 s excluding heat treatment (xie2026developmentofan pages 9-13). No standard deviations or replicate counts are reported for these individual steps.

**Video-derived times from multi-robot PXRD workflows.** Lunt et al. (2023/2024, Chemical Science) describe a 12-step autonomous PXRD workflow using a KUKA KMR iiwa mobile manipulator and an ABB YuMi dual-arm cobot. Video timestamps yield approximate per-operation times: mobile KUKA delivery ≈42 s, diffractometer door opening ≈12 s, plate loading ≈23 s, door closing ≈25 s, and vial-cap manipulation ≈88 s (lunt2023modularmultirobotintegration pages 12-16). These are demonstration-video estimates, not replicated time studies. PXRD acquisition was approximately one hour per sample (lunt2023modularmultirobotintegration pages 12-16).

**Mobile robot transport.** Ali et al. (2018) measured an H20 mobile robot completing a three-station round trip (charge → grasp → place → charge) in a life-science laboratory across 50 runs: mean 15 min 32 s without fine position correction, reduced to mean 11 min 26 s (range 10:46–12:44) with fine correction (ali2018mobilerobottransportation pages 8-9). Separately, the arm motion from rest to the labware manipulation point took approximately 30 seconds (ali2017graspingandplacing pages 8-10). Hernández-del-Valle et al. (2026, preprint) report a TurtleBot4 completing ~96 trips in 6 hours (derived ~3.75 min/trip including charging pauses), and a cobot cell processing 190 polymer specimens in 274 minutes (~86.5 s/specimen including detection, grasping, cutting, and storing) (hernandezdelvalle2026perceptiondrivenexperimentalworkflows pages 10-12).

**Aggregate campaign times.** Ahlquist (2024) measured the MARS SDL experiment at a mean of 86.2 minutes with a coefficient of variation of 2.2% for labware-transportation sub-operations. Parallelization could reduce this to 24.6 minutes (71.4% reduction) (ahlquist2024improvingselfdrivinglabs pages 6-12). Crain et al. (2025) report 84 XRD samples in ~24 h using a Meca500 arm, giving ~17 min/sample including long-exposure measurement; sample changes alone were described as taking "seconds" (crain2025designofa pages 1-5, crain2025designofa pages 5-10). Chu (2016) reports a complete robotic sample-preparation workflow of 81 min 5 s versus 30 min 40 s manually, with pipetting at ~30 mm/s and liquid withdrawal at ~40 mm/s contributing the majority of handling time (chu2016automationstrategiesfor pages 135-138).

**Robot idle fractions.** No retrieved publication reports a measured robot idle fraction or utilization percentage during an SDL campaign. This is a notable gap in the literature.

---

### (2) Discrete-Event Simulations and Digital Twins Using Measured Handling Times

**No validated DES of an SDL using measured handling times was found.** MATTERIX (Darvish et al., 2025, Nature Computational Science) is the closest system: a physics-based digital twin for robotics-assisted chemistry laboratory automation with sim-to-real deployment demonstrations, but the retrieved pages do not report that measured handling-time distributions were used as model inputs, nor is there a quantitative validation against a real experimental campaign comparing predicted and observed throughput (darvish2025matterixtowarda pages 2-5). The MARS system (Ahlquist 2024) timestamped sub-operations and used them to estimate campaign duration and illustrate parallelization opportunities, but this was an empirical timing analysis rather than a formal DES model (ahlquist2024improvingselfdrivinglabs pages 6-12). Zhang et al. (2026) define a reproducibility framework including a "seeded digital twin" for benchmark rollouts and cost functions based on makespan plus penalties, but do not report validation against a real campaign or sensitivity analysis separating handling, instrument, and decision-time effects (zhang2026makingselfdrivinglaboratories pages 8-9).

**Sensitivity analyses.** No retrieved publication performs a formal sensitivity analysis decomposing throughput into contributions from handling time, instrument time, and human decision latency. This represents a significant gap, particularly relevant to the BYU Vertical Cloud Lab's finding that transport does not bind but decision time does.

---

### (3) Human Decision Latency in Self-Driving Labs

**No published study was found that directly measures human decision latency (median or mean waiting time for approvals, analysis, or the next experimental decision) in a self-driving laboratory.** Multiple high-impact papers discuss the role of the human-in-the-loop qualitatively. Scheurer and Reuter (2025, Nature Catalysis) argue that human involvement "should not limit experimental throughput" but provide no measured latency (scheurer2025roleofthe pages 5-5, scheurer2025roleofthe pages 1-2). The ORNL/LCLS workshop report (Silva et al. 2024) provides one quantitative comparison: "human operators typically need 'minutes' to adjust experimental parameters," while modern instruments generate equivalent data in seconds, making human decision-making a potential bottleneck (silva2024shapingthefuture pages 10-12).

**What reduces decision latency.** Several algorithmic approaches have been proposed and benchmarked:

- *Asynchronous Bayesian optimization:* ELF-BO (Sutter et al., 2026, preprint) overlaps MCMC sampling with experimental evaluation, achieving decision latency "close to point-estimate BO and approximately 10 times lower than standard fully Bayesian BO with a Matérn kernel, 70–110 times lower with a deep kernel." On the Photo-WF3 benchmark, standard FBO latency reached up to 24 minutes while ELF-BO remained under 3 seconds (sutter2026workwhilethey pages 1-2, sutter2026workwhilethey pages 9-11).

- *Pipelined batch BO:* Taguchi et al. (2026, SLAS Technology) report that PipeBO "reduced average optimization processing time to approximately 56% of the comparison methods" for two-process experiments on 20 of 24 benchmark functions (taguchi2026asynchronousbatchbayesian pages 1-2).

- *Non-blocking expert feedback:* Kristiadi et al. (2024, preprint) show that asynchronous, intermittent expert feedback on an independent computing thread avoids blocking the BO loop while still improving or constraining optimization (kristiadi2024howusefulis pages 1-3).

- *Asynchronous parallel BO for cloud labs:* Frisby et al. (2021, Bioinformatics) demonstrate PROTOCOL, which "achieves exponential convergence with respect to simple regret" and reduces the number of experiments needed in shared cloud-lab queues (frisby2021asynchronousparallelbayesian pages 1-2).

However, **none of these papers measure how long a human scientist actually takes to review results and approve the next experiment in a physical SDL**. The 77-hour median waiting time mentioned in the user's context appears to be an internal estimate with no published counterpart found in the literature.

---

### (4) Robots Restocking Consumables and Unattended Run Lengths

**No published system was found in which a robot autonomously restocks pipette tips, vials, plates, powders, gas cylinders, or other consumables with measured success rates.** This confirms the user's citation-analysis finding. Multiple papers identify consumable management as a limitation stated as future work:

- Seifrid et al. (2022, Accounts of Chemical Research) explicitly state that "some workflow steps remain dependent on people loading new vials or chemicals into the Chemspeed" and propose "installing robotic arms to imitate human loading actions" as future work (seifrid2022autonomouschemicalexperiments pages 8-9).

- Moran et al. (2026, npj Robotics) propose "autonomous maintenance or 'self-maintainability' (SeM)" as a future concept including labware and device management, but state it "does not yet include autonomous installation and de-installation of robotic hardware" (moran2026theriseof pages 9-11).

- Hernández-del-Valle et al. (2026, preprint) note that injection-molding material "charging and material changes are not automated and therefore require human intervention" (hernandezdelvalle2026perceptiondrivenexperimentalworkflows pages 10-12).

- Müller et al. (2025, preprint/Biotechnology & Bioengineering) report that their bioreactor SDL "still depended on operators for auxiliary consumables and activities, including replenishing liquid containers, at-line analytics, and handling samples for offline analysis" (muller2025selfdrivingdevelopmentof pages 28-31).

**Unattended run lengths.** The longest documented autonomous campaign is the A-Lab (Szymanski et al., 2023, Nature), which operated continuously for 17 days, performing 355 experiments (~20.9 experiments/day) and realizing 41 of 58 target inorganic compounds (szymanski2023anautonomouslaboratory pages 2-3, szymanski2023anautonomouslaboratory pages 4-5). However, the degree to which this was truly unattended (no human restocking or intervention) is not fully described in the retrieved pages. Shorter documented runs include: Hernández-del-Valle et al.'s ~6-hour mobile-robot trial and ~4.5-hour specimen-manipulation demonstration, limited by battery life and material charging (hernandezdelvalle2026perceptiondrivenexperimentalworkflows pages 10-12); and Ahlquist's MARS campaigns, where prior campaign failure rates were 29–43% before gripper improvements reduced them to 4.4–7.2% (ahlquist2024improvingselfdrivinglabs pages 6-12, ahlquist2024improvingselfdrivinglabs pages 1-6).

**Consumable-limited factors.** Tegally et al. (2020, BMC Genomics) explicitly quantify tip consumption for a 96-library genomics preparation: "1,920 50-µL Hamilton tips, 576 300-µL tips, and 25 1,000-µL tips," demonstrating that deck consumable capacity directly limits unattended run length (tegally2020unlockingtheefficiency pages 11-12). Evaporation during long protocols is also identified as a consumable-management challenge (tegally2020unlockingtheefficiency pages 11-12).

---

### (5) Time-Study Methods for Measuring Handling Operations

**Stopwatch time study** is the foundational method. Duran et al. (2015) describe dividing operations into work elements, timing each across repeated observations with an electronic chronometer, excluding waiting periods (reported as 85 minutes of mold waiting time), and calculating standard time by applying performance ratings and allowances (duran2015productivityimprovementby pages 3-4). Hartanti (2016) specifies a 95% confidence level and ±5% precision target, with observed times classified into subgroups and checked via control charts (hartanti2016workmeasurementapproach pages 2-4, hartanti2016workmeasurementapproach pages 1-2). Bakar et al. (2026) recommend recording at least 10 observations per element and validating through pilot studies (bakar2026enhancingmanufacturingproductivity pages 15-17).

**Work sampling** is the preferred method for estimating time proportions. Musa (2025) provides the sample-size formula: **n = Z²P(1−P)/E²**, where Z is the standard-normal value for the chosen confidence level, P is the estimated activity proportion, and E is the allowable margin of error. "For a 95% confidence level, no prior estimate, and 5% precision, the study uses Z = 1.96, P = 0.5, and E = 0.05," yielding n = 384 observations as the minimum; using P = 0.5 is conservative because "it produces the largest required sample size when the true proportion is unknown" (musa2025worksamplingmethodology pages 4-8). The study separated observations into productive work (60%), machine downtime (10%), and material waiting time (30%) from 1,000 observations, with a 95% confidence interval of 56.96%–63.04% for productive work (musa2025worksamplingmethodology pages 4-8, musa2025worksamplingmethodology pages 1-4).

**Separating time categories.** Ramadhan et al. (2024) describe separating activities through direct observation and work sampling into productive and non-productive categories, with motion analysis identifying unnecessary movements. Observed times are adjusted with performance-rating factors, and allowances for personal needs, fatigue, and unavoidable delays are added (ramadhan2024productivityimprovementthrough pages 3-5). Rework must be defined as a separate observed activity category before data collection begins (musa2025worksamplingmethodology pages 4-8).

**Methods-Time Measurement (MTM)** is an alternative predetermined-time system described by Morlock et al. (2017) that assigns standard times to basic motions (reach, grasp, move, position, release) without requiring stopwatch observations. This can be useful for robot operations where motions are programmed and repeatable.

**Recommended approach for the BYU alloy-discovery lab.** Based on the literature:
1. Use **stopwatch time study** for each robot operation (pick, place, dock, load, door-open, decap), collecting ≥20–30 observations per element at the target confidence (95%) and precision (±5–10%).
2. Use **work sampling** with ≥384 random observations to estimate the proportion of hands-on, waiting, instrument-running, and rework time across the workflow.
3. Apply the formula n = Z²P(1−P)/E² to determine the number of observations needed for a given precision target.
4. Code each observation into predefined categories: hands-on manipulation, instrument processing (waiting), transport, decision/approval waiting, rework/recovery, and idle.
5. Validate the resulting distributions against 2–3 real campaigns before using them as inputs to the discrete-event simulation.

---

### Summary of Evidence Gaps

The literature review reveals several areas where **no published evidence exists**:

1. **Per-operation handling times with statistical spread** (means and standard deviations for individual pick, place, dock, load, decap operations) have not been published in a systematic timing table for any SDL.
2. **Robot idle fractions** during SDL campaigns have not been reported in any retrieved publication.
3. **Validated discrete-event simulations** of SDLs using measured (rather than assumed) handling times, with throughput sensitivity decomposed into handling, instrument, and decision-time components, do not appear to exist in the published literature.
4. **Measured human decision latency** (median or mean time a scientist takes to review results and approve the next experiment) has not been quantified in any retrieved SDL paper; the user's 77-hour estimate appears to be unprecedented in the literature.
5. **Automated consumable restocking by robots** (tips, vials, plates, powders) with measured success rates has not been demonstrated in any published system; it is consistently listed as future work.
6. **Time-study methodology applied specifically to laboratory robot operations** for simulation modeling has not been published, though the industrial engineering methods described above are directly transferable.

These gaps collectively suggest that the BYU Vertical Cloud Lab's planned time-study campaign and simulation validation would represent a novel and significant contribution to the SDL literature.