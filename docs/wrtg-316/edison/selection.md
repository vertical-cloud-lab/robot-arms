# WRTG 316 proposal: nine selected sources

These nine sources were picked from two rounds of Edison answers in this folder (see the [README](README.md)). Run 1
was asked for in [issue #64](https://github.com/vertical-cloud-lab/robot-arms/issues/64) (WRTG-Proposal-1). Run 2, in
[PR #90](https://github.com/vertical-cloud-lab/robot-arms/pull/90), re-asked the same request with the context from
[`proposal questions.md`](../Proposal/user%20context/proposal%20questions.md). It focuses on the **automated manual
manipulator**: one robot arm that moves from station to station, calibrates itself at each station with a calibration
square, and takes on several new automated tasks.

Sources [1] and [2] are for the Review of Literature and [3] to [9] are for the Annotated Bibliography, numbered in
table order. All nine are peer-reviewed and none is a preprint. The annotations and review paragraphs are not written
here; Joshua writes those. The first version of this list, from run 1 alone, is at
[commit 875cd80](https://github.com/vertical-cloud-lab/robot-arms/blob/875cd80/docs/wrtg-316/edison/selection.md).
[What changed from the first list](#what-changed-from-the-first-list) says why each source was kept or replaced.

**How the sources were checked.** Every quote below appears word for word in the copy named in brackets after it.
That copy is the full text where one could be downloaded and the abstract otherwise. For some sources the only open
copy was the arXiv version, the accepted manuscript or the bioRxiv preprint, so the published wording may differ
slightly. [How the picks were checked](#how-the-picks-were-checked) lists what was read for each source and where
Edison got something wrong.

## Why nine

The assignment asks for two Review of Literature sources and an Annotated Bibliography of at least seven others, so
nine is the fewest it allows. Nine is also enough: every idea the proposal questions call for is covered by at least
one pick. (Issue #64 planned for you to add two sources of your own. To stay at nine, swap each one in for the pick
closest to it.)

| Idea the proposal needs | Proposal questions | Covered by |
|---|---|---|
| Lab automation is growing, in materials science and in biology (the opening) | 1.1, 1.2.3 | [3], [4]; biology also [5], [7] |
| What an automated manual manipulator is: one arm working a lab's stations and recalibrating at each | your request, 1.3.1 | [1], [3], [4] |
| Affordable automation and democratizing SDLs (the larger question) | 1.3.6, 1.4.1 | [4], [5], [7] |
| Whether anyone has written on this exact question, and how the literature treats it | 1.2.4, 1.3.1, 1.3.7 #1 | [5], [6]; see also [Closest to your exact question](#closest-to-your-exact-question-131) |
| Categories of arms, and the metrics used to choose one | 1.3.7 #2–3 | [4], [6] |
| Test: the arm's own repeatability and accuracy (ISO 9283) | 1.3.1, 1.4.6 | [2]; also [5] |
| Test: recalibrating at a station from a calibration square | your request | [1]; also [3] |
| Test: task reliability over many repeated trials | 1.4.6 | [1], [5], [7] |
| How many trials to run, and how to state a success rate | 1.4.6 | [9] |
| Measured results for low-cost arms | 1.2.1, 1.4.1 | [5], [7] |
| Counter-arguments | 1.3.3, 1.4.4 | [8]; also [7] (slower than a person) and [4] (general-purpose arms are less efficient than special-purpose hardware) |
| Cost, and cost per task (your perspective) | 1.4.5 | [4], [7]. Neither run found a full cost per task (hardware, labor and upkeep per successful task) for a lab arm; the nearest is a labor-only figure (Dembski, under [Considered but not selected](#considered-but-not-selected)). The paper can name that gap. |
| Datasheet values versus measured values (source bias) | 3.1.6 | [2], [5] |
| Authorities: standards and leading groups | 3.1.3 | ISO 9283 in [2] and [5]; ISO 10218 and ISO/TS 15066 in [6]; the Cooper group (Liverpool) in [1] and [3] |

## Selection

| # | Role | Reference (IEEE) | Peer-reviewed or preprint | Supporting quote (copy checked) | Why it fills its role |
|---|---|---|---|---|---|
| [1] | Review of Literature: recalibrating at each station from a calibration square | Z. Zhou, S. Veeramani, F. Munguia-Galeano, H. Fakhruldeen, and A. I. Cooper, "Localization, inspection, and reasoning (LIRA) module for autonomous workflows in self-driving laboratories," *Commun. Chem.*, vol. 8, no. 1, Art. no. 384, Nov. 2025, doi: 10.1038/s42004-025-01770-1. | Peer-reviewed journal | "The robotic platform used is a KUKA KMR iiwa mobile manipulator, which performs object handling and transfers between stations." … "The 75 mm ArUco marker further improves stability, achieving a mean error of 1.02 mm in translation and 1.01 degrees in rotation." … "The cube-based calibration method demonstrates the highest precision, with minimal variance and a mean error of 0.92 mm in translation and 0.90 degrees in rotation." (publisher HTML) | It is the only peer-reviewed SDL study in either run that measures the calibration-square idea: an industrial arm that moves between stations and recalibrates at each from square fiducial markers, compared with touch calibration on a cube. It also reports calibration time and a 600-operation reliability run. |
| [2] | Review of Literature: the arm's own repeatability (ISO 9283) | S. Chajón, J. Reiff-Stephan, and N. Günther, "Photogrammetric characterization of robot positioning accuracy and repeatability," *Robotics*, vol. 15, no. 5, Art. no. 86, Apr. 2026, doi: 10.3390/robotics15050086. | Peer-reviewed journal | "Experimental validation follows selected elements of ISO 9283:1998 and comprises 30 repetitions at five target poses for linear and axial motion strategies." … "To contextualize these results, the datasheet of the employed UR3 robot was consulted, which specifies a positioning repeatability of 0.03 mm in accordance with ISO 9283:1998." (publisher PDF) | It measures a UR3 industrial cobot with a Raspberry Pi camera, fiducial markers, a printed tool and dial indicators, which is the equipment we have. |
| [3] | Annotated Bibliography: development of the field (the first automated manual manipulator) | B. Burger *et al.*, "A mobile robotic chemist," *Nature*, vol. 583, no. 7815, pp. 237–241, Jul. 2020, doi: 10.1038/s41586-020-2442-2. | Peer-reviewed journal | "The robot operated autonomously over 8 days, performing 688 experiments within a 10-variable experimental space, driven by a batched Bayesian search algorithm." … "Here, the robot touches six points on a cube that is associated with each experimental station to find the position and orientation of the cube relative to the robot (Supplementary Figs. S7–S11)." … "This gave an (x, y) positioning precision of ± 0.12 mm and an orientation precision of θ ± 0.005 degrees within a standard laboratory environment with dimensions 7.3 m x 11 m" (accepted manuscript, Strathprints) | It is the landmark automated manual manipulator: an arm on a mobile base that ran a lab's stations for 8 days and recalibrated at every station against a cube, a physical form of the calibration square. Its Supplementary Information gives a tolerance to test against: vials and cartridges need better than 0.5 mm. |
| [4] | Annotated Bibliography: development of the field (growth, hardware classes and cost) | G. Tom *et al.*, "Self-driving laboratories for chemistry and materials science," *Chem. Rev.*, vol. 124, no. 16, pp. 9633–9732, Aug. 2024, doi: 10.1021/acs.chemrev.4c00055. | Peer-reviewed journal (review) | "Cooper and co-workers have extended the concept of flexible automation to the use of mobile robots, operating multiple workstations which are distributed across the laboratory, mimicking a human researcher." … "Moreover, open hardware for lab automation has been proposed to lower the financial barrier to building a SDL." … Table 1, price row: "High (∼$1M)", "Medium (∼$10K)", "Low ($100 - 2K)" (ACS PDF and PubMed Central XML) | It is the most-cited SDL review. It describes arms that work a lab's stations like a person, prices the three classes of SDL hardware (special-purpose, general-purpose and open), and argues that open, low-cost hardware democratizes SDLs, which is your larger question (1.3.6). |
| [5] | Annotated Bibliography: closest study to your purpose (testing an affordable arm for lab work) | Y. Harazono, H. Shimono, K. Hata, T. Mitsuyama, and T. Horinouchi, "Evaluation of microplate handling accuracy for applying robotic arms in laboratory automation," *SLAS Technol.*, vol. 29, no. 6, Art. no. 100200, Dec. 2024, doi: 10.1016/j.slast.2024.100200. | Peer-reviewed journal | "Although the method to gauge this repeatability is detailed in ISO 9283[20], it solely considers the robot's approach to a specific location without holding any object." … "As evident, the interquartile range (IQR) along the x and y directions under high-speed condition was 0.020 and 0.006 mm, respectively, and under low-speed condition it was 0.034 and 0.014 mm, respectively (raw data is presented in supplemental Table S1)." … "Whereas, along the y-direction, the probability significantly decreased when Δy exceeded 2.190 mm." (bioRxiv preprint v1, doi: 10.1101/2023.12.29.573685) | It asks whether an inexpensive desktop arm (a Dobot M1 Pro SCARA) is accurate enough for lab automation, and answers with a test we could copy: two dial gauges, 125 loaded microplate transfers per speed, then imposed offsets to find the task's tolerance. It also explains why a datasheet's repeatability is not enough. |
| [6] | Annotated Bibliography: how arms are compared and chosen | F. Ferraguti, A. Pertosa, C. Secchi, C. Fantuzzi, and M. Bonfè, "A methodology for comparative analysis of collaborative robots for Industry 4.0," in *Proc. Design, Automation & Test in Europe Conf. (DATE)*, Florence, Italy, Mar. 2019, pp. 1070–1075, doi: 10.23919/DATE.2019.8714830. | Peer-reviewed conference | "The goal of the paper is to provide a framework for allowing the benchmarking, based on common robot parameters and standardized experiments that can be performed with the robot under investigation." … "Summarizing, a proper comparison of different collaborative robots should take into account robot-dependent aspects (i.e. technical data and experimental verification of declared features), application-dependent aspects (i.e. force/speed limits for risk assessments) and user-dependent aspects (i.e. perceived usability, physical/mental effort for teaching and programming)." (DATE proceedings PDF) | It answers what to compare when choosing an arm (1.3.7 #3). It compares a KUKA LWR 4+, a UR5 and a Franka Panda by checking datasheet claims with experiments, testing collision forces against ISO/TS 15066, and measuring programming effort and usability. Price shaped which arms were chosen: "the Panda robot is the cheapest redundant and collaborative robot currently available on the market". |
| [7] | Annotated Bibliography: a low-cost arm doing a person's lab work | N. Rupp, K. Peschke, M. Köppl, D. Drissner, and T. Zuchner, "Establishment of low-cost laboratory automation processes using AutoIt and 4-axis robots," *SLAS Technol.*, vol. 27, no. 5, pp. 312–318, Oct. 2022, doi: 10.1016/j.slast.2022.07.001. | Peer-reviewed journal | "The system is sold for approximately 1.5K €, has a maximum payload of 0.5 kg, a maximum reach of 320 mm and is advertised with a position repeatability of 0.2 mm." … "Compared to a trained professional who performed all experiments manually, all setups showed no significant differences in accuracy and precision." … "the automated processes take more time than the manual processes, by the following factors: pipetting process: 3.5, AAS autosampler: 1.6, inoculation of bacteria: 3.0." (publisher PDF, Internet Archive copy) | It gives measured results for a low-cost arm (a Dobot Magician) doing three lab jobs a person would do: pipetting, loading an atomic absorption spectrometer and inoculating bacteria. The arm matched a trained researcher's accuracy but was 1.6–3.5 times slower, and its repeatability was "severely limited", most of all when inoculating, which ruled out plates with smaller wells. It supports your thesis and a counter-argument at once. |
| [8] | Annotated Bibliography: counter-argument | Z. S. Wattoo *et al.*, "RABIT, a robot arm bug intervention tool for self-driving labs," in *Proc. IEEE/IFIP Int. Conf. Dependable Syst. Netw. (DSN)*, Brisbane, Australia, Jun. 2024, pp. 353–361, doi: 10.1109/DSN58291.2024.00043. | Peer-reviewed conference | "Both robot arms are designed for educational and research purposes. They have the same degree of freedom as the UR3e, but limited capabilities and precision." … "For example, transforming both robot arms’ coordinate systems to a global coordinate system using a transformation matrix [14] resulted in an average error of 3cm between the expected and computed positions." … "When ViperX was moved to a very high, clearly infeasible, position, it failed to compute the trajectory and silently ignored the command." (DSN 2024 proceedings PDF) | It makes the case against from inside an SDL. A lab used two lower-precision educational arms as stand-ins for its UR3e: putting both in one coordinate frame left about 3 cm of error, one arm skipped an infeasible command without an error, and the two collided without the safety tool raising an alarm. |
| [9] | Annotated Bibliography: reliability statistics | J. A. Vincent, H. Nishimura, M. Itkina, P. Shah, M. Schwager, and T. Kollar, "How generalizable is my behavior cloning policy? A statistical approach to trustworthy performance evaluation," *IEEE Robot. Autom. Lett.*, vol. 9, no. 10, pp. 8619–8626, Oct. 2024, doi: 10.1109/LRA.2024.3445635. | Peer-reviewed journal | "We revisit a rarely-used bound from the statistics literature, a tighter version of the more common Clopper-Pearson bound [8]." … "Practices which violate Assumption 1 include … running policy rollouts until enough favorable outcomes are observed (in which case confidence sequences would be more appropriate [37])" (arXiv version) | It shows how to put a lower confidence bound on a success rate from a few robot trials, and which testing practices make that bound invalid. |

## Review of Literature picks: test protocols

### [1] Zhou et al. (2025): recalibrating at each station from a fiducial square

- **What is measured.** How well the arm locates a station after arriving, by two methods: a wrist camera reading
  square ArUco markers fixed to the station, and the older touch method against a cube-mounted locator. After each
  calibration the arm is sent to a reference point 300 mm from the marker, and its recorded pose is compared with the
  pose found by touch calibration. The paper reports the mean translation and rotation error and the time each
  calibration takes. A separate run counts successful pickups and insertions over many station visits.
- **Number of trials.**
  - Accuracy: "This process was repeated 100 times to ensure statistical reliability". The paper does not say
    whether that is 100 per marker condition.
  - Reliability: 100 consecutive workflow loops of about 5 minutes (8 hours in all) on a two-station vial-rack loop
    with 20 mm × 20 mm markers, for 600 pickups and insertions.
  - Inspection: 200 tests in which racks and plates were misplaced by hand.
- **Equipment.**
  - A KUKA KMR iiwa mobile manipulator. The arm is a KUKA LBR iiwa 14; only the peer-review file names it.
  - An Intel RealSense D435i camera on the end effector.
  - ArUco markers of 20 mm and 75 mm in the accuracy test, and a cube-mounted locator for the touch method.
  - No external measuring instrument. The reference is the touch-calibrated pose and the measurement is the robot's
    own recorded pose; the paper cites the arm's documented ISO 9283 repeatability of ±0.15 mm.
- **Published results (KUKA KMR iiwa).**

  | Method | Mean translation error | Mean rotation error |
  |---|---|---|
  | 20 mm ArUco marker, unfiltered | 2.42 mm | 3.46° |
  | 20 mm ArUco marker, Gaussian and mean filtering | 1.51 mm | 1.54° |
  | 75 mm ArUco marker | 1.02 mm | 1.01° |
  | Touch calibration on the cube | 0.92 mm | 0.90° |

  - Each visual calibration took about 5 s and each touch calibration about 53 s. A workflow loop with 11 visual
    calibrations took 873 s of arm time, against 1367 s with 7 touch calibrations: 36.1% less. (The paper's
    introduction and discussion say 34%.)
  - All 600 pickups and insertions succeeded over 8 hours, and 195 of the 200 misplacements (97.5%) were correctly
    inspected.
- **Cautions.** The cube's 0.92 mm is measured against a cube calibration, so it is closer to repeatability than to
  accuracy against an independent reference. The success criterion for the 600 operations is not stated, and the
  stations' tolerances are not given as numbers. The 97.9% figure in the paper is an image-classification test, not
  the robot test.
- **What we would need to repeat it on the PiPER and SO-101.**
  - AprilTags (or ArUco markers) printed at 20 mm and 75 mm and fixed flat at each station, and the Pi wrist camera
    calibrated with a printed CharUco board, as in [2].
  - A printed reference fixture 300 mm from the tag, read with our dial indicator. That measures where the tool
    actually goes, rather than trusting the arm's encoders as the paper did.
  - For the touch comparison, a printed cube and a probe on the gripper that signals contact, such as a microswitch.
  - 100 calibrations per condition, then a station-to-station loop that counts pickups and insertions. Our arms do
    not drive between rooms, so a "station change" means moving the arm to another fixture, or moving the fixture,
    and recalibrating.
  - About a day to print and set up, then a day per arm.

### [2] Chajón et al. (2026): planar repeatability with a Raspberry Pi camera

- **What is measured.** Planar (x–y) positioning accuracy `APp` and positioning repeatability `RPp`, following selected
  elements of ISO 9283:1998 at constant height. `APp` is the distance from the barycentre of the measured positions to
  the target. `RPp = l̄ + 3·S_l` is the mean distance to the barycentre plus three standard deviations. Height (z) and
  tool orientation are not measured. The paper compares two ways of reaching each pose: a straight-line ("linear")
  move and a joint-interpolated ("axial") move.
- **Number of trials.** 30 repetitions at each of five target poses, for each motion strategy: 150 images per
  strategy. The poses are the centre of the measurement field and four points around it, labelled `X0|Y0` and
  `X±25|Y±25` in the paper.
- **Equipment.**
  - A Raspberry Pi 4 and Raspberry Pi camera module with a wide-angle lens of about 75°, on a carrier plate parallel
    to the tool.
  - Python 3.12 and OpenCV 4.12.
  - A CharUco board for camera calibration (1.01 px RMS reprojection error).
  - A 3D-printed tool attachment held in the robot's two-finger gripper. It carries 15 mm ArUco markers (two markers
    gave the lowest deviation) or a ruby sphere. The image scale was 0.103 mm/px.
  - Dial indicators fixed to the table, used for a separate reference check in x and y.
- **Published result and arm (UR3).**
  - Camera-measured `RPp` per pose was 0.147–0.229 mm with linear moves and 0.195–0.265 mm with axial moves.
  - `APp` was at most 0.488 mm (linear) and 0.474 mm (axial).
  - The dial-indicator reference gave a mean deviation of 0.0109 mm. The UR3 datasheet says 0.03 mm.
  - The camera numbers are about ten times the dial-indicator numbers, so for a UR3 they mostly measure the camera
    chain. The authors say the dial check "does not represent a full validation of the complete photogrammetric
    measurement chain".
- **What we would need to repeat it on the PiPER and SO-101.**
  - A Pi camera on a rigid printed mount at a fixed distance, a printed tool for each gripper, and a printed
    CharUco board.
  - AprilTags in place of ArUco markers. OpenCV detects both, but say in the paper that this was changed.
  - Our dial indicator, used one axis at a time (the paper used indicators on both sides).
  - A script that makes 30 approaches to each of the five poses in both modes, and the `APp`/`RPp` formulas above.
    The SO-101 has no built-in straight-line move, so its linear runs need an inverse-kinematics layer. Joint-space
    runs work directly.
  - The dial-indicator reading is the one comparable to the UR3's 0.0109 mm, so do that check on the PiPER. At about
    0.1 mm per pixel the camera alone is probably enough for the SO-101 if its errors are near a millimetre.
  - With the parts printed, testing should take a day or two per arm.

## What changed from the first list

The first list (run 1, issue #64) had 9 sources. This one keeps 3 and replaces 6. The replacements follow the
proposal questions, which add the station-to-station focus, the question of whether anyone has written on this exact
topic (1.3.1), and the question of which metrics guide the choice of an arm (1.3.7).

### Kept (3)

- **Chajón et al. (2026), still a Review of Literature pick, now [2].** It is still the best way to measure the
  arm's own repeatability by the ISO 9283 method with equipment the lab has (a Raspberry Pi camera, fiducial markers
  and a dial indicator), against an industrial arm (a UR3). Run 2 cited it again in q2, q3 and q6. Its UR3 numbers
  also cover source bias (3.1.6): 0.147–0.229 mm measured by camera, against a datasheet value of 0.03 mm.
- **Burger et al. (2020), still a development-of-the-field pick, now [3], with a sharper role.** Under the new focus
  it is the first automated manual manipulator, and its touch calibration on a cube at every station is a physical
  form of the calibration square. Six of the nine run-2 answers cite it.
- **Vincent et al. (2024), still the reliability-statistics pick, now [9].** Run 2's q8 answer says SDL papers mostly
  report raw counts without confidence bounds, and nothing in run 2 replaces Vincent as a checked source on how to
  bound a success rate from a small number of trials.

### Replaced (6)

| First list | Replaced by | Why |
|---|---|---|
| [2] Morgan et al. (2020), Box and Blocks Test (Review of Literature) | [1] Zhou et al. (2025) | The focus is now an arm that moves between stations and recalibrates at each with a calibration square. Zhou is the only peer-reviewed SDL paper in either run that measures exactly that, on an industrial arm, with 100-repeat accuracy trials, calibration times and a 600-operation run. That also covers what Morgan contributed: a scored, repeated task test with an industrial baseline. The Box and Blocks Test is generic block moving, not station work. Run 1's q5 answer already cited Zhou, but the first selection ranked generic task tests higher. |
| [4] Lo et al. (2024), frugal-twin review | [4] Tom et al. (2024) | Both reviews cover low-cost SDL hardware, and both runs cited both. Tom covers more of the ideas the proposal needs: the growth of SDLs (including biology), arms that work a lab's stations like a person, the three hardware classes with prices, and democratization through open hardware. Tom was also read in full; Lo could only be checked from its abstract, because RSC blocked the download. |
| [5] Yang et al. (2019), REPLAB | [7] Rupp et al. (2022) | REPLAB measures a ~$2,000 arm in a cell built for grasp learning. Rupp measures a ~€1,500 arm doing real lab work against a trained person, which is the question an automated manual manipulator raises. It also gives a counterpoint (1.6–3.5 times slower) and prices. |
| [6] Gealy et al. (2019), quasi-direct-drive arm | [5] Harazono et al. (2024) | Issue #64 asked for two sources with measured low-cost data. Harazono keeps a measured low-cost arm in the list and adds what the proposal questions now ask for. It is the closest peer-reviewed study to your purpose (is an affordable arm accurate enough for lab automation?), with a dial-gauge test we could copy and a measured task tolerance. In run 1 it was a bioRxiv preprint and was left out unchecked; *SLAS Technology* published it in October 2024. Gealy measures a research arm (3.7 mm home-pose repeatability) outside any lab task, and run 2 did not cite it. |
| [7] Franzese et al. (2026), calibration and backlash (counter-argument) | [8] Wattoo et al. (2024), RABIT | RABIT's evidence comes from inside an SDL and concerns working across a lab's devices, the automated-manual-manipulator setting: lower-precision arms could not share a coordinate frame better than about 3 cm, one failed silently, and they collided without an alarm. It also sets up [1], since recalibrating at each station is the published answer to that frame error. Franzese's finding (backlash limits the calibration of planetary-gear arms) is still true and checked; it is the best swap if you want a measured accuracy argument instead. Run 2 did not cite it. |
| [9] Zhao et al. (2023), ACT (the "any question" pick) | [6] Ferraguti et al. (2019) | The proposal no longer needs results for learned policies: the paper reviews tests, and imitation learning is not among the proposal questions. It does ask which metrics guide the choice of an arm (1.3.7 #3), which no pick covered. Ferraguti, cited in both runs, is a checked method for comparing arms on datasheet claims checked by experiment, collision tests and the user's effort. |

## How the picks were checked

| # | Cited in | What was read | Notes, including Edison errors |
|---|---|---|---|
| [1] | run 1 q5; run 2 q2, q4, q8 | Full text: publisher HTML and PDF, Supplementary Information, and the peer-review file | The numbers match. Edison's quoted protocol sentence merges two of the paper's sentences. Edison says LIRA replaced a "6P" (six-point) touch method; LIRA itself never says six-point. Edison does not mention that the accuracy test uses the robot's own recorded pose, with no external instrument, or that the 600-operation run was a two-station rack loop with 20 mm markers. The paper itself gives 36.1% in its results and 34% elsewhere. |
| [2] | run 1 q3; run 2 q2, q3, q6 | Full text, publisher PDF from MDPI's file server (the article page blocks GitHub's runners) | Edison's figures all match: 30 repetitions × 5 poses, 0.229 and 0.265 mm, 0.0109 mm, Raspberry Pi 4, 0.103 mm/px. |
| [3] | run 1 q1; run 2 q1–q4, q8, q9 | Accepted manuscript (Strathprints) and the free Supplementary Information | A correction to the first check: the Supplementary Information does name the arm, a "KUKA ... LBR iiwa"; the accepted manuscript does not. The ±0.12 mm comes from 100 calibrations started from deliberately perturbed estimates (Supplementary §1.3), with no measuring instrument named, so it is repeatability rather than accuracy. Calibration time is not stated. The published *Nature* wording may differ slightly (e.g. "six-point", "black location cube"). |
| [4] | run 1 q1; run 2 q1, q2, q3, q5 | Full text: the ACS PDF (ETH Zurich Research Collection) and PubMed Central XML | Table 1 is confirmed. The review gives no count of SDLs or of publications; its growth claim is a prediction ("explosive growth of SDLs") backed by investment figures. Citation numbers differ between the two copies, so cite the ACS version. |
| [5] | run 1 q4; run 2 q3, q4, q7, q8 | Full text of the bioRxiv preprint v1; the published article's abstract (Europe PMC) and Figs. 2–3 | The *SLAS Technology* text was blocked everywhere, so the quotes are from the preprint. The published abstract matches the preprint word for word, and the published figures show the same results. The paper gives neither the arm's price nor its datasheet repeatability; its ~$1,000 figure is for the Dobot Magician Lite and myPalletizer. In x, failures started well below the y limit (about a third failed at 1.90 mm). |
| [6] | run 1 q3, q4; run 2 q3 | Full text, the DATE proceedings archive PDF (printed pp. 1064–1069, which are IEEE pp. 1070–1075) | Edison says payload and repeatability were benchmarked; they are datasheet values. The collision tests cover only power and force limiting. The LWR 4+ stood in for an LBR iiwa that wasn't available. Edison leaves out the force-estimation error and stress-level measures. |
| [7] | run 2 q1, q3, q7, q8 | Full text, publisher PDF (an Internet Archive copy; the live site blocked the runner) | Only the Dobot Magician was used; Edison's Dobot MG400 (~€3,000) was only suggested. Edison's quote "did not significantly differ from manual work by a trained professional" is not verbatim. The 3.5× factor is for pipetting only (1.6× for the autosampler, 3.0× for inoculation). The "more than €1 million" figure for lab lines comes from a personal communication. |
| [8] | run 2 q7 | Full text, the DSN 2024 proceedings PDF and a co-author's copy | The paper never says "low-cost" and gives no prices. Edison's quoted list ("different vendors, gripper sizes, low precision, and coordinate-system incompatibility") is not in it, and the title has a comma, not a colon. The "later collision" is a hypothetical in a footnote. |
| [9] | run 1 q6 | Full text of the arXiv version, 2405.05439; RA-L abstract (Crossref) | Edison gave the RA-L citation with the arXiv DOI. The RA-L DOI is 10.1109/LRA.2024.3445635. Run 2 cited a different Vincent paper (on simulation rollouts, arXiv 2309.10874) instead; this one stays because it was checked and covers the same bound. |

## Closest to your exact question (1.3.1)

Neither Edison run found a paper with exactly your purpose. Run 2's q2 answer says "no publication was found whose
sole purpose is to define or run tests that evaluate, compare, or select a robot arm for use as an automated manual
manipulator in a self-driving or automated laboratory", and that the term "automated manual manipulator" did not
appear in any publication it retrieved. The usual term is "mobile manipulator". These come closest; the first six
were checked:

1. **Harazono et al. (2024)**, [5]: tests whether an affordable arm is accurate enough for microplate handling.
2. **P. Salazar-Villacis and B. Benyahia, "The ADePT framework for assessing autonomous laboratory robotics,"**
   *Commun. Chem.*, vol. 9, no. 1, Art. no. 99, Feb. 2026, doi: 10.1038/s42004-026-01932-9. A peer-reviewed
   Perspective. It scores lab robots on four capabilities (adaptability and learning, dexterity, perception, task
   complexity) from what 36 published studies report. It does not define physical tests, and it asks studies to
   "report quantitative error and robustness alongside ADePT scores".
3. **Ferraguti et al. (2019)**, [6]: a method for comparing and choosing cobots, in industry rather than labs.
4. **Zhou et al. (2025)**, [1]: tests one way of recalibrating at stations, on one arm.
5. **A. A. Volk and M. Abolhasani, "Performance metrics to unleash the power of self-driving labs in chemistry and
   materials science,"** *Nat. Commun.*, vol. 15, no. 1, Art. no. 1378, Feb. 2024, doi: 10.1038/s41467-024-45569-5.
   It proposes metrics for whole SDLs and found that "71% of the studies reported no data quantifying the precision of
   the automated experimental system of the built SDL". That figure covers 17 studies, none of them built around an
   arm, and "precision" there means the spread of repeated experiments, not robot positioning.
6. **R. Pagani *et al.*, "Cobot user frame calibration: Evaluation and comparison between positioning repeatability
   performances achieved by traditional and vision-based methods,"** *Robotics*, vol. 10, no. 1, Art. no. 45, Mar.
   2021, doi: 10.3390/robotics10010045. It compares touch and fiducial-marker calibration of a work frame on a Sawyer
   cobot, measured with an external sensor (see [Considered but not selected](#considered-but-not-selected)).
7. Ginsburg *et al.* (SC '23 Workshops), doi: 10.1145/3624062.3624615: a color-matching benchmark for whole SDL
   workcells, with a PF400 plate-handling arm. Not checked.
8. Hifi *et al.*, *Meas. Sci. Technol.* (2025), doi: 10.1088/1361-6501/adf3d4: the accuracy and repeatability of a
   KUKA KMR iiwa mobile manipulator, measured with a laser tracker. Not checked.
9. Pollák *et al.*, *Adv. Mech. Eng.* (2020), doi: 10.1177/1687814020972893: an ISO 9283 measurement of a UR5 with
   six length gauges. Not checked.

## Considered but not selected

**Checked and usable, if you want to swap one in:**

- **Pagani et al. (2021)** (above). On a Sawyer cobot, touch calibration of a work frame on 5 points gave 0.12 mm
  repeatability and on 3 points 0.33 mm, against a reference repeatability of 0.08 mm. The robot's built-in camera method,
  which uses a single fiducial marker, gave up to 1.42 mm. These are the abstract's figures: 1.42 mm is the z axis
  (x was 0.70 mm and y 0.39 mm), and the touch figures are for the closer of two set-ups. It used an inductive
  proximity sensor and 30 runs at each of five points. The authors still recommend fiducial markers when the robot has
  a wrist camera. It is the best swap for [1] or [2] if you want the calibration test measured by an external
  instrument.
- **Salazar-Villacis and Benyahia (2026), ADePT** (above). A swap for [6] if you prefer a lab-specific framework to
  arm-comparison criteria. Edison's quote "remain systems integrators: effective in controlled settings but limited in
  perception, adaptation, error recovery and generalisation" is not in the paper; it says "Robots, therefore, serve
  reliably as systems integrators in controlled laboratory settings."
- **Volk and Abolhasani (2024)** (above). Two of the paper's main-text references (18 and 28) carry the titles of
  unrelated papers, so cite the surveyed studies from its Supplementary Information.
- **G. Franzese *et al.*, *Commun. Eng.*, vol. 5, Art. no. 138, 2026, doi: 10.1038/s44172-026-00633-4** (the first
  list's [7]). The swap for [8].
- **S. Dembski *et al.*, *Sci. Rep.*, vol. 13, Art. no. 11440, 2023, doi: 10.1038/s41598-023-38535-6.** A dual-arm
  Yaskawa robot made silica nanoparticles more reproducibly than three technicians. Its abstract says "the use of the
  robot not only increased the synthesis accuracy and reproducibility but reduced the personnel time and costs up to
  75%". The cost counts staff time only; the body gives 44% less staff time and does not show how 75% follows. It is
  the nearest thing to cost per task in either run.
- From the first list, checked then and still usable: Morgan *et al.* (2020), Yang *et al.* (2019), Gealy *et al.*
  (2019), Zhao *et al.* (2023) and Lo *et al.* (2024, abstract only). The
  [first version](https://github.com/vertical-cloud-lab/robot-arms/blob/875cd80/docs/wrtg-316/edison/selection.md)
  has their references and quotes. So do Pollák and Goryl (2023) and Manes *et al.* (2024). Run 2's q5 says the Manes
  study used a KUKA iiwa; as the first check found, the paper says Franka Panda.

**Could not be checked:** A. Thieme *et al.*, *SLAS Technol.*, vol. 29, Art. no. 100180, 2024, doi:
10.1016/j.slast.2024.100180 (OT-2 liquid handlers at Roche). Edison says automation halved the labor cost per sample
but did not pay back the hardware within five years. The full text was blocked everywhere. A full-text search index
suggests similar phrases are in the paper, but Edison's quoted wording is not.

**Not checked (preprints, reports, or not needed for the nine):** ArmnetBench (arXiv 2607.24481), Cowling (arXiv
2610.37170), Brass *et al.* (ChemRxiv, doi: 10.26434/chemrxiv-2025-bsfvz), AutoBio (arXiv 2505.14030), LabRobFail
(arXiv 2607.23704), Johns and Gongora (DOE report, doi: 10.2172/3684119; Edison says an SO-101 placed vials in 34 of 36
trials with ACT), Ahlquist (OSTI report, doi: 10.2172/2459394; Edison says gripper faults stopped many runs on a
UR5e), Mariano *et al.* (*SLAS Technol.*, 2026; Edison says collision tests on a UR5e and UR10e exceeded pressure
limits), and the three unchecked papers in the list above.
