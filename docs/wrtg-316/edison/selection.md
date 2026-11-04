# WRTG 316 proposal: nine selected sources

These nine sources come from the eight Edison answers in this folder (see the [README](README.md)) and were picked for
[issue #64](https://github.com/vertical-cloud-lab/robot-arms/issues/64) (WRTG-Proposal-1). Sources [1] and [2] are
for the Review of Literature and [3] to [9] are for the Annotated Bibliography, numbered in table order. All nine
are peer-reviewed and none is a preprint. The annotations and review paragraphs are not written here; Joshua writes those.

**How the sources were checked.** Every quote below appears word for word in the copy named in brackets after it.
That copy is the full text where one could be downloaded and the abstract otherwise. For some sources the only
open copy was the arXiv version or the accepted manuscript, so the published wording may differ slightly.
[How the picks were checked](#how-the-picks-were-checked) lists what was read for each source and where Edison got
something wrong.

## Selection

| # | Role | Reference (IEEE) | Peer-reviewed or preprint | Supporting quote (copy checked) | Why it fills its role |
|---|---|---|---|---|---|
| [1] | Review of Literature: positioning repeatability test | S. Chajón, J. Reiff-Stephan, and N. Günther, "Photogrammetric characterization of robot positioning accuracy and repeatability," *Robotics*, vol. 15, no. 5, Art. no. 86, Apr. 2026, doi: 10.3390/robotics15050086. | Peer-reviewed journal | "Experimental validation follows selected elements of ISO 9283:1998 and comprises 30 repetitions at five target poses for linear and axial motion strategies." … "To contextualize these results, the datasheet of the employed UR3 robot was consulted, which specifies a positioning repeatability of 0.03 mm in accordance with ISO 9283:1998." (publisher PDF) | It measures a UR3 industrial cobot with a Raspberry Pi camera, fiducial markers, a printed tool and dial indicators, which is the equipment we have. |
| [2] | Review of Literature: pick-and-place task test | A. S. Morgan *et al.*, "Benchmarking cluttered robot pick-and-place manipulation with the Box and Blocks Test," *IEEE Robot. Autom. Lett.*, vol. 5, no. 2, pp. 454–461, Apr. 2020, doi: 10.1109/LRA.2019.2961053. | Peer-reviewed journal | "Each task protocol should be completed consecutively at a minimum of five times as to allow for a general understanding of the system's robustness." … "Comparatively, the Panda setup scored much higher (13 ± 0.7 blocks), taking advantage of the precision evident in rigid manipulators and grippers." (authors' PDF, Yale GRAB Lab) | It gives scored pick-and-place protocols with Franka Panda and Barrett WAM baselines. They can be run with a parallel gripper, a box, cubes and printed templates. |
| [3] | Annotated Bibliography: development of the field (arms in SDLs) | B. Burger *et al.*, "A mobile robotic chemist," *Nature*, vol. 583, no. 7815, pp. 237–241, Jul. 2020, doi: 10.1038/s41586-020-2442-2. | Peer-reviewed journal | "The robot operated autonomously over 8 days, performing 688 experiments within a 10-variable experimental space, driven by a batched Bayesian search algorithm." … "This gave an (x, y) positioning precision of ± 0.12 mm and an orientation precision of θ ± 0.005 degrees within a standard laboratory environment with dimensions 7.3 m x 11 m" (accepted manuscript, Strathprints) | It is the landmark self-driving lab in which an industrial arm on a mobile base ran the experiments, and it reports the positioning precision that work needed. |
| [4] | Annotated Bibliography: development of the field (low-cost hardware) | S. Lo *et al.*, "Review of low-cost self-driving laboratories in chemistry and materials science: The 'frugal twin' concept," *Digit. Discov.*, vol. 3, no. 5, pp. 842–868, 2024, doi: 10.1039/D3DD00223C. | Peer-reviewed journal (review) | "Frugal twins range from simple toy examples to low-cost surrogates of high-cost research systems." … "They can also offer as test beds for software prototyping (e.g., optimization, data infrastructure), and a low barrier to entry for democratizing SDLs." (abstract, OSTI record) | It is the review that defines and surveys low-cost self-driving lab hardware, the category the PiPER and SO-101 belong to. |
| [5] | Annotated Bibliography: measured low-cost arm data | B. Yang, D. Jayaraman, J. Zhang, and S. Levine, "REPLAB: A reproducible low-cost arm benchmark for robotic learning," in *Proc. Int. Conf. Robot. Autom. (ICRA)*, Montreal, QC, Canada, May 2019, pp. 8691–8697, doi: 10.1109/ICRA.2019.8794390. | Peer-reviewed conference | "…a reproducible and self-contained hardware stack (robot arm, camera, and workspace) that costs about 2000 USD…" (ICRA abstract) … "we encountered no major breakages over more than 100,000 grasp attempts. No servos needed to be replaced." … "the end-effector positions are within 2 cm of the target over the 35 x 40 cm workspace floor, and within 1 cm near the center." (arXiv version) | It reports measured positioning error, durability and cost for a WidowX, one of the low-cost arms named in Q3, inside a reproducible benchmark cell. |
| [6] | Annotated Bibliography: measured low-cost arm data | D. V. Gealy *et al.*, "Quasi-direct drive for low-cost compliant robotic manipulation," in *Proc. Int. Conf. Robot. Autom. (ICRA)*, Montreal, QC, Canada, May 2019, pp. 437–443, doi: 10.1109/ICRA.2019.8794236. | Peer-reviewed conference | "All trials fell within a radius of 3.7 mm and the average deviation from the center of home poses was 2.6 mm." … "Bill of Materials (BoM) cost for each arm was tracked at $3328" (arXiv version) | It gives measured repeatability for a low-cost research arm, with the method (133 return-to-home motions, motion capture) and the price. That puts a data point between SO-101-class arms and the UR3 and Panda. |
| [7] | Annotated Bibliography: counter-argument | G. Franzese, M. Spahn, J. Kober, J. Alonso-Mora, and C. Della Santina, "Accurate and affordable cobot calibration without external measurement devices," *Commun. Eng.*, vol. 5, no. 1, Art. no. 138, Apr. 2026, doi: 10.1038/s44172-026-00633-4. | Peer-reviewed journal | "From the experiment, we conclude that robots that have harmonic drives, like the Franka and KUKA, result in very precise calibration. On the other hand, when calibrating robots that use planetary gearboxes, like the Kinova, the calibration did not have the same miraculous improvements. We identify the problem to be in the backlash in the joints, which is not observable in the encoder measurements." (publisher HTML) | It measures how joint backlash limits accuracy. The planetary-gear Kinova stayed near 2 mm after calibration, while the harmonic-drive Franka and KUKA reached about 0.1–0.2 mm. |
| [8] | Annotated Bibliography: reliability statistics | J. A. Vincent, H. Nishimura, M. Itkina, P. Shah, M. Schwager, and T. Kollar, "How generalizable is my behavior cloning policy? A statistical approach to trustworthy performance evaluation," *IEEE Robot. Autom. Lett.*, vol. 9, no. 10, pp. 8619–8626, Oct. 2024, doi: 10.1109/LRA.2024.3445635. | Peer-reviewed journal | "We revisit a rarely-used bound from the statistics literature, a tighter version of the more common Clopper-Pearson bound [8]." … "Practices which violate Assumption 1 include … running policy rollouts until enough favorable outcomes are observed (in which case confidence sequences would be more appropriate [37])" (arXiv version) | It shows how to put a lower confidence bound on a success rate from a few robot trials, and which testing practices make that bound invalid. |
| [9] | Annotated Bibliography: additional pick (Q7, learned vs scripted) | T. Z. Zhao, V. Kumar, S. Levine, and C. Finn, "Learning fine-grained bimanual manipulation with low-cost hardware," in *Proc. Robot.: Sci. Syst. (RSS)*, Daegu, Republic of Korea, Jul. 2023, doi: 10.15607/RSS.2023.XIX.016. | Peer-reviewed conference | "ACT allows the robot to learn 6 difficult tasks in the real world, such as opening a translucent condiment cup and slotting a battery with 80-90% success, with only 10 minutes worth of demonstrations." (RSS abstract) … "For real-world tasks, we run one seed and evaluate with 25 trials." (arXiv version) | It introduced ACT, one of the imitation-learning policies in LeRobot, on hardware under $20k. It reports how many demonstrations and evaluation trials were used. |

## Review of Literature picks: test protocols

### [1] Chajón et al. (2026): planar repeatability with a Raspberry Pi camera

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

### [2] Morgan et al. (2020): Box and Blocks Test protocols

- **What is measured.** Three robot versions of the clinical Box and Blocks Test:
  - *Modified*: move 16 blocks over the barrier, one at a time and in order, from fixed template positions. The score
    is the number of blocks transferred.
  - *Targeted*: the same, but each block must be placed in its target location.
  - *Standard*: move as many of 100 randomly placed blocks as possible, timed (60 s) and untimed.

  Each run also records pick attempts, end-effector travel distance, and planning, execution and total time.
- **Number of trials.** Each protocol at least five times in a row. A failed run scores zero. If a bin moves more than
  2.54 cm or rotates more than 10°, the run restarts and scores zero.
- **Equipment.**
  - The YCB box-and-blocks objects (#68 and #69): two containers with a barrier, and 2.54 cm cubes.
  - Printed templates with sixteen 3.2 × 3.2 cm squares, fixed to the container floor.
  - On the Panda, the parallel gripper had 140 mm 3D-printed finger extensions because the stock gripper was too wide
    for the container. An Intel RealSense D435i RGB-D camera was mounted at the wrist.
- **Published results and arms.**
  - Franka Panda, five runs per protocol (Table VI):

    | Protocol | Score (mean ± SD) | Total time |
    |---|---|---|
    | Modified | 14.4 ± 2.1 blocks | 247.9 s |
    | Targeted | 13.0 ± 0.7 | 307.1 s |
    | Standard, timed | 2.8 ± 0.8 blocks | 60 s |
    | Standard, untimed | 7.6 ± 2.3 blocks | 293.5 s |

  - Barrett WAM with a compliant hand (Table V): all 16 blocks in each of the five Modified runs (243.4 s on average),
    1.8 ± 1.5 on Targeted, 4.8 ± 0.4 blocks in the timed Standard test, and 32.4 ± 2.3 blocks untimed.
  - The paper also gives human norms.
- **What we would need to repeat it on the PiPER and SO-101.**
  - The YCB containers, or copies built to the same size.
  - About 100 cubes of 2.54 cm. Wooden blocks are inexpensive.
  - The templates, from the paper's multimedia attachment.
  - Possibly longer printed fingers if our grippers do not fit into the bins.
  - Our cameras. The templates fix the start positions, so the Modified and Targeted protocols can use scripted motion
    with AprilTags on the bins. Only the Standard protocol needs block detection, and the Panda used a depth camera for
    that, where we have RGB.
  - Five runs of each protocol per arm should take a day or two.

## How the picks were checked

| # | Cited in | What was read | Notes, including Edison errors |
|---|---|---|---|
| [1] | q3 §3.1, §7, §8 | Full text, publisher PDF from MDPI's file server (the article page blocks GitHub's runners) | Edison's figures all match: 30 repetitions × 5 poses, 0.229 and 0.265 mm, 0.0109 mm, Raspberry Pi 4, 0.103 mm/px. |
| [2] | q2 table and §2; q6 table | Full text, the authors' PDF on the Yale GRAB Lab site; the Panda table (Table VI) was read from an image of the page | Edison says the WAM's 4.8 ± 0.4 blocks was the *untimed* Standard result. The paper gives it for the *timed* 60 s test; the untimed WAM score was 32.4 ± 2.3. Edison's 248.73 s for the Panda's untimed run is execution time; the total was 293.52 s. |
| [3] | q1 §1.2 | Full text, accepted manuscript on Strathprints | Edison describes the arm as a "KUKA LBR iiwa 7-DOF arm (14 kg payload, 0.1 mm repeatability)". The text names a KUKA Mobile Robot (KMR) with a 14 kg payload and 820 mm reach, and gives ±0.12 mm positioning precision after calibration. It says nothing about "LBR iiwa", 7-DOF or 0.1 mm repeatability. The published Nature wording may differ (e.g. "eight days"). |
| [4] | q1 §1.2; q4 §4.4 | Abstract only (OSTI record). RSC and ChemRxiv refused the download from the runner and from a lab Pi | The q1 claim (low-cost surrogates of high-cost systems) matches the abstract. Edison's q4 quote, "reducing cost generally requires either reducing research capabilities or sacrificing accuracy and precision", could not be checked, so it is not used. |
| [5] | q1 §1.3; q3 §2.1, §7; q4 §1.2, §2.2 | ICRA abstract (Crossref); full text of the arXiv version, 1905.07447 | The arXiv version has a different author list (it adds V. Pong), so cite the ICRA version above. The durability and 2 cm sentences were checked in the arXiv text only. |
| [6] | q1 §1.3; q3 §2.2, §7 | Full text of the arXiv version, 1904.03815 | Matches Edison. Edison's q1 rounds the result to "~4 mm repeatability"; the paper says a 3.7 mm radius and a 2.6 mm average. |
| [7] | q4 §1, §1.1 | Full text, open-access publisher HTML | The numbers match. Edison's quoted phrase "failed insertion tasks requiring 6 mm tolerance" is not verbatim; the paper says the nominal model "even fails with a hole of 16 mm" for a 10 mm peg. |
| [8] | q6 §2.1–§3, §5 | Full text of the arXiv version, 2405.05439; RA-L abstract (Crossref) | Edison gave the RA-L citation with the arXiv DOI. The RA-L DOI is 10.1109/LRA.2024.3445635. |
| [9] | q1 §1.3; q6 table; q7 §2, §7 | RSS abstract (Crossref); full text of the arXiv version, 2304.13705 | Edison lists it as an arXiv preprint. It was published in the peer-reviewed RSS 2023 proceedings, the version cited here. |

## Considered but not selected

**Checked and usable, if you want alternatives for your own two picks:**

- M. Pollák and K. Goryl, *Machines*, vol. 11, no. 7, Art. no. 734, 2023, doi: 10.3390/machines11070734. ISO 9283
  repeatability of a Panasonic TM-2000 welding robot measured with a digital dial indicator, 30 readings at each of five
  points on two axes (checked in the full text). Use it as a Review of Literature alternative if you want an industrial
  arm measured with a dial indicator alone.
- L. Manes *et al.*, *Sci. Rep.*, 2024, doi: 10.1038/s41598-024-59372-1. A soft gripper on a Franka Emika Panda moved
  vials between trays 1,000 times with a 0.8% failure rate (checked in the full text). It is a repeatable vial-handling
  reliability test. Edison's q5 says this was done on an ABB YuMi; the paper says Panda.
- G. Tom *et al.*, *Chem. Rev.*, vol. 124, pp. 9633–9732, 2024, doi: 10.1021/acs.chemrev.4c00055. Its Table 1
  prices special-purpose SDL hardware at about $1M, general-purpose at about $10K and open hardware at $100–2K (checked
  in the full text). It is an alternative for the development of the field.

**Dropped after checking:**

- I. Holland and J. A. Davies (2020), the counter-argument candidate. Edison's quote "complete automation for common
  procedures such as cell culture may exceed $1 million" is not in the paper. Its table puts totally automatic systems,
  such as automated cell culture, at £100,000–1,000,000.
- A. Angelopoulos *et al.* (IROS 2023), on AprilTag-only localization (9.52% success against 100% with visual
  servoing). Those numbers are not in the abstract and the full text is paywalled, so they could not be checked.
- K. Kimble *et al.* (RA-L 2020), the NIST task-board protocols. Only the abstract could be read, so the reliability
  statistics Edison describes were not checked.
- Preprints were left out of the nine and were not checked. They include SmolVLA (arXiv 2506.01844), Cowling's SO-101
  demonstration-scaling study (arXiv 2610.37170), SO-101 Bench (arXiv 2610.36420), the Forte arm
  (arXiv 2507.15693), Harazono's microplate-handling study (bioRxiv, doi: 10.1101/2023.12.29.573685) and Mobile ALOHA
  (arXiv 2401.02117).
