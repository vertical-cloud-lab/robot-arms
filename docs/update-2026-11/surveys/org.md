# VCL org survey (excluding byu-vcl, robot-arms, digital-alloy-lab) + borysgroup/aurora-cloud-infra

Scope: what changed since 2026-09-15, and where a PiPER cell (AgileX PiPER, Pi wrist/fixed cameras, AprilTags, SO-101 leader, LeRobot) could plug in.
Method: GitHub API reads on 2026-11-28 of every issue/PR list, every README, and comment threads (all of aurora-cloud-infra; selected threads elsewhere). People are GitHub handles; they/them.

---

## 0. Cross-cutting findings (decision-relevant)

1. **The doser's auger is the clearest arm target, and its design is changing under the arm team's plan.** Augers are still fitted, filled and swapped by hand ("One powder per doser, augers swapped by hand", status table, 2026-11-19, https://github.com/vertical-cloud-lab/powder-doser/issues/160#issuecomment-7018452935). robot-arms #42 (2026-10-26, https://github.com/vertical-cloud-lab/robot-arms/issues/42) plans a gripper plus a "finger fixture" to strip the wired tap collar. But on 2026-11-07 the doser team started moving the tapper onto the mounting plate so that an auger lifts straight out: "Now that the brackets are snap-in C-clips, the tap collar is the only thing that stops an auger from lifting straight out" (https://github.com/vertical-cloud-lab/powder-doser/issues/203#issuecomment-6713576689; ethanw-24's first bracket, https://github.com/vertical-cloud-lab/powder-doser/issues/203#issuecomment-6714762206). If that lands, the collar-stripping step in #42 goes away.
2. **No powder-doser thread mentions the PiPER cooperation.** The only robot-arms cross-reference there is a digital-twin issue (https://github.com/vertical-cloud-lab/powder-doser/issues/158, 2026-09-08). The one cross-team link is that the 6DOF team members claytonblodgett and jss265 printed a full set of doser parts, including "the clips that hold the auger", on 2026-11-12/13 (https://github.com/vertical-cloud-lab/powder-doser/pull/200#issuecomment-6839188674, https://github.com/vertical-cloud-lab/powder-doser/pull/200#issuecomment-6843437638).
3. **The multi-doser is being designed to need no arm.** The 2026-08-18 pitch was summarised as "No transfer arm, no cartridge handoff" (https://github.com/vertical-cloud-lab/powder-doser/issues/128#issuecomment-5372087570). The chain carousel (v1 to v12, CAD and simulation only, v7 the "main version") keeps auger swaps manual through a side hatch (https://github.com/vertical-cloud-lab/powder-doser/pull/185). An arm fits at the edges: refilling and swapping augers at the hatch, and moving the beaker or cup on and off the balance. The v8 front-cover ideas named "a sliding sash ... It suits a robot-served station" and a strip curtain, "the easiest for a gripper" (https://github.com/vertical-cloud-lab/powder-doser/pull/185#issuecomment-6831136790, 2026-11-12).
4. **Other manual steps an arm could take today:** placing and removing atomizer cups on the balance, clearing auger clogs, and moving cups to the atomizer (powder-doser #186); clearing Bambu print plates (all repos); filling 96-well plates and moving them for imaging (digital-wetlab: "The OT-2 has no gripper, so it never moves the plate"). Tensegrity, caliber and the furnace are poor fits for a fixed cell: their instruments are in shared facilities elsewhere, or the parts are tweezer-scale.
5. **The PiPER came from the Utah group, which no longer needs it.** "aurora does not need it" (kinstonwithoutg, 2026-09-04). It is "more relevant for doing things outside the glovebox and transferring things in and out" (sgbaird, 2026-09-26). The end-effector camera mount issue (aurora #5) is still open with no hardware built. The dual-camera Pi 5 (#16) is an Aurora overhead camera, not the wrist camera.
6. **Cameras and streaming:** BYU's OT-2 lid camera (Pi 5 + HQ + 8–50 mm) went to Utah on 2026-11-10, and its rebuild parts are still arriving. The lab's Pi stream cameras run through streamingLambda, with 96.7–96.8% uptime. The only AprilTag discussion is a July RFID-vs-AprilTag comparison in powder-doser #133, which favoured RFID for identifying augers.

---

## 1. Lab page: vertical-cloud-lab/.github (profile/README.md)

- **Mission (README, unchanged in substance since 2026-01):** "we integrate the concepts of vertical automation, cloud experimentation, and frugal twins into self-driving labs focused on discovering new structural, aerospace, and energy materials" (https://github.com/vertical-cloud-lab/.github/blob/main/profile/README.md).
- **Thrusts:** autonomous alloy discovery ("a vertical lift module, low-cost powder dosing units, an ultrasonic atomizer, a small-scale metal 3D printer, and mechanical testing equipment"), autonomous electrochemistry ("3D printed electrochemical cells, automated sample exchange"), and advanced Bayesian optimization (Honegumi).
- **Arm mention:** the vertical-lab figure caption says the tray comes back "to the operator (e.g., robotic arm, human)".
- **Project list:** the page has no repo list; it links Honegumi only. PI: `sgbaird`.
- **Since 2026-09-15:** MS&T 2026 temporary links (powder-doser PRs and byu-vcl atomizer PRs) were added on 2026-10-05 (https://github.com/vertical-cloud-lab/.github/commit/85b38a1) and removed on 2026-10-12 (https://github.com/vertical-cloud-lab/.github/commit/1826b95). The alloy-workflow figure request (https://github.com/vertical-cloud-lab/.github/issues/8, 2026-02-28) is still open.

---

## 2. vertical-cloud-lab/powder-doser (217 items; most active)

**Purpose.** "An open-source powder doser for autonomous alloy discovery". One printed tube is "both the powder reservoir and the dosing screw: the doser turns, tilts and taps it over a cup on the balance". The build costs under $200 plus a balance. "Every 1 g dose on seven of the 13 powders we tested landed within ±5%" (https://github.com/vertical-cloud-lab/powder-doser/blob/main/README.md; README rebuilt 2026-11-22 in https://github.com/vertical-cloud-lab/powder-doser/pull/217; project page merged 2026-11-24 in https://github.com/vertical-cloud-lab/powder-doser/pull/215).

### Current single-doser design: interfaces a gripper would touch

Sources: the PR #170 CAD from the lab Fusion files, 2026-10-01 to 10-02; the current Onshape set in #193.

- **Auger tube:** Ø25.0 mm; bracket and collar bores Ø25.5; cap thread Ø26.0 (https://github.com/vertical-cloud-lab/powder-doser/pull/170#issuecomment-5946129103, 2026-10-02). It prints 250 mm tall, threaded end up, on the H2D only (https://github.com/vertical-cloud-lab/powder-doser/pull/181; specs at https://github.com/vertical-cloud-lab/powder-doser/issues/193#issuecomment-6956001314, 2026-11-17).
- **Gears:** a 44T module-1 gear on the tube, driven by a 20T pinion on a NEMA 11 at a 32 mm centre distance. The tilt uses MG996R servos, 14T to 28T, 0–45° ("45° (maximum)"). The outlet sits about 11.6–12 mm in front of the hinge (https://github.com/vertical-cloud-lab/powder-doser/pull/170#issuecomment-5939524398, https://github.com/vertical-cloud-lab/powder-doser/pull/170#issuecomment-5943304090).
- **Retention:** current brackets are "the white open C-clip behind the 44T gear", and there is no STEP of them (https://github.com/vertical-cloud-lab/powder-doser/pull/170#issuecomment-6237498939, 2026-10-17). The tap collar (12 V Adafruit 412 solenoid) clamps around the tube, and its strike point is "42.3 mm behind the hinge" (https://github.com/vertical-cloud-lab/powder-doser/issues/203#issuecomment-6713576689).
- **Mass and capacity:** "weighs 53 grams empty, currently weighs ~155g" full of salt (williamulbz, https://github.com/vertical-cloud-lab/powder-doser/pull/166#issuecomment-5881925337, 2026-09-29). Capacity is given as "around 70 mL" (swcharles, https://github.com/vertical-cloud-lab/powder-doser/issues/117#issuecomment-6346637620, 2026-10-22) and as 58 mL (#160 table). Smaller 3.32 mL and 9.18 mL augers exist (https://github.com/vertical-cloud-lab/powder-doser/pull/170#issuecomment-5939645382). Augers are filled through a capped top opening on a "filling stand" (Fusion link in the same comment).
- **Frame:** the baseplate screws to a 1.5 in board. The outlet hangs 21.6 mm in front of the board edge, so the board stands above the balance (https://github.com/vertical-cloud-lab/powder-doser/pull/170#issuecomment-5945773617). A "centering device" jig aligns the auger tip over the balance-lid hole: "so far we've been eye-balling it", and v2 moves the tip 5 mm further over the opening (https://github.com/vertical-cloud-lab/powder-doser/issues/177, 2026-10-06/09).
- **Balances:** HR-100A (102 g × 0.1 mg) today. The new-design target is an A&D HR-250AZ (base about 260 × 190 mm, enclosure 183 × 240 mm, about 320 mm tall) (https://github.com/vertical-cloud-lab/powder-doser/issues/204#issuecomment-7116925935, https://github.com/vertical-cloud-lab/powder-doser/issues/204#issuecomment-7118208817, 2026-11-23/24).
- **Current Onshape files:** baseplate, mounting plate, auger, brackets, tap collar, pinions, stand (https://github.com/vertical-cloud-lab/powder-doser/issues/193#issuecomment-6504703603, 2026-10-29). "Augers need to be printed with maximum 0.4mm nozzle" (https://github.com/vertical-cloud-lab/powder-doser/issues/193#issuecomment-6551960707).

### State of the loop

**Automated: dosing on request.**
- An agent doses when asked in a GitHub comment. The Pico firmware runs bulk, trickle and tap phases under balance feedback. An Ax SOBOL→SAASBO campaign ran as an "Unattended optimization run on the rig: 42 doses" on 2026-09-29 (https://github.com/vertical-cloud-lab/powder-doser/pull/166#issuecomment-5881930157).
- Production doses: 8 g AlSi10Mg delivered as 7.9928 g (https://github.com/vertical-cloud-lab/powder-doser/pull/166#issuecomment-5900419828, 2026-09-29). Al 4047 reached 8.0010 g after a firmware MemoryError fix and a clog (https://github.com/vertical-cloud-lab/powder-doser/pull/166#issuecomment-5920106530, 2026-09-30).

**Manual: everything physical.**
- Loading and fitting augers, refilling, and placing or removing cups. Clogs are cleared by hand: "I have cleared the auger of large particles" (https://github.com/vertical-cloud-lab/powder-doser/issues/186#issuecomment-6302880128, 2026-10-20).
- Atomizer cups are cleaned, weighed and loaded by hand: "a new cup has been cleaned and loaded ... cup + plug is 37.2151g" (https://github.com/vertical-cloud-lab/powder-doser/issues/186#issuecomment-6301117396). Two cups were dosed to 3.0432 g and 6.5676 g on 2026-10-19/20 (https://github.com/vertical-cloud-lab/powder-doser/issues/186#issuecomment-6281871091, https://github.com/vertical-cloud-lab/powder-doser/issues/186#issuecomment-6302887672). The 22.5 wt% point is blocked on thin-walled crucibles (https://github.com/vertical-cloud-lab/powder-doser/issues/186#issuecomment-6428882791, 2026-10-26).
- The camera was moved by hand and its Pi went offline on 2026-10-21 (https://github.com/vertical-cloud-lab/streamingLambda/issues/5#issuecomment-6357097623).

### What changed since 2026-09-15 (key threads)

- **25 repeat dosers** (https://github.com/vertical-cloud-lab/powder-doser/pull/181, from 2026-10-15).
  - All 25 augers were printed on the H2D on 2026-10-23 (https://github.com/vertical-cloud-lab/powder-doser/pull/181#issuecomment-6357672576).
  - brandonmunk stopped agent printing on 2026-10-27 after failures (https://github.com/vertical-cloud-lab/powder-doser/pull/181#issuecomment-6448008026).
  - lshuldberg started the first assembly on 2026-11-05 (https://github.com/vertical-cloud-lab/powder-doser/pull/181#issuecomment-6671271179). Parts were still short for one doser on 2026-11-17 (https://github.com/vertical-cloud-lab/powder-doser/pull/181#issuecomment-6956360490).
  - Design reviews: https://github.com/vertical-cloud-lab/powder-doser/issues/191. Whether these are "standalone dosers or carousel modules" is still open (#181 body).
- **Plate-mounted tapper so augers lift out** (https://github.com/vertical-cloud-lab/powder-doser/issues/203, 2026-11-07). Four concepts were proposed: bolt-on tower, tap bracket, see-saw hammer, flip-away saddle. The recommendation is to try the tower and put a tap bracket on "the 25 new dosers". ethanw-24 has a first-iteration bracket in Onshape.
- **Fixed 2–3 auger "tri-star"** (https://github.com/vertical-cloud-lab/powder-doser/issues/204, 2026-11-07 to 11-24). Gearless modules are tilted by Actuonix P16 actuators on a one-piece 320.5 × 280.2 × 52.25 mm base, with hinges 32 mm from the beaker axis, on telescoping tripod legs (https://github.com/vertical-cloud-lab/powder-doser/issues/204#issuecomment-6867806741). It is driven by plampkin's block-copolymer use case at the U of U: "dose 0.25 to 5 g of monomer at a time ... 5 to 25 g of polymer" (https://github.com/vertical-cloud-lab/powder-doser/issues/117#issuecomment-6298772227, 2026-10-20). plampkin's clearance question is at https://github.com/vertical-cloud-lab/powder-doser/issues/204#issuecomment-6756895160.
- **Multi-doser chain carousel, v1 to v12** (https://github.com/vertical-cloud-lab/powder-doser/pull/185; history in https://github.com/vertical-cloud-lab/powder-doser/issues/128).
  - 2026-10-16: twin #35 chains, 13 PETG carriages, NEMA 34, plus a paternoster alternative (https://github.com/vertical-cloud-lab/powder-doser/pull/185#issuecomment-6216129591).
  - 2026-10-29: swcharles asked for a side hatch "so we can open it, switch out the augers, and close it again", and side tabs "so that, when you pull the auger off the mounting plate, you're pulling against the frame, not the chain" (https://github.com/vertical-cloud-lab/powder-doser/pull/185#issuecomment-6503653801).
  - 2026-10-29: simulations found "the station doesn't work as drawn yet" (https://github.com/vertical-cloud-lab/powder-doser/pull/185#issuecomment-6510926546).
  - 2026-11-17: v7 declared the main version (https://github.com/vertical-cloud-lab/powder-doser/pull/185#issuecomment-6957695003). v8 to v10 cut the auger-to-beaker gap to 50, 32 and then 18 mm.
  - 2026-11-27: v11's hatch was widened to 400 mm, and about 1 index in 4 jammed in simulation (https://github.com/vertical-cloud-lab/powder-doser/pull/185#issuecomment-7212924846). v12 adds a spring-loaded pinion and a hall switch (https://github.com/vertical-cloud-lab/powder-doser/pull/185#issuecomment-7224779545), with a public walkthrough at https://www.youtube.com/watch?v=abZlIeTuC0A.
  - Linear actuator (Actuonix with feedback): order status asked 2026-11-28 (https://github.com/vertical-cloud-lab/powder-doser/issues/202#issuecomment-7236831234).
- **Papers and talks.**
  - Hardware paper v2 figures merged 2026-11-27 (https://github.com/vertical-cloud-lab/powder-doser/pull/209).
  - TMS 2027 talk: "A Programmable Powder Doser with 15+ Reservoirs and Automated Auger Swapping…" (https://github.com/vertical-cloud-lab/powder-doser/pull/209#issuecomment-6807914209). Its status: "multi-doser in CAD only" and automated swap "Designed, not built" (#160).
  - The optimization paper "cannot be submitted yet" (https://github.com/vertical-cloud-lab/powder-doser/pull/184#issuecomment-7226066359, 2026-11-27).
- **Digital twin and simulation.** A LIGGGHTS DEM gives "105 mg/rev at 27.5° and 60 rpm, against 105 ± 11 measured" (https://github.com/vertical-cloud-lab/powder-doser/issues/158#issuecomment-6094253357, 2026-10-10; https://github.com/vertical-cloud-lab/powder-doser/pull/180). #158 cites MATTERIX and robot-arms #1 as motivation for sim-based design.

### Edison use and design decisions since September

- Edison is used heavily, for literature reviews only:
  - controller-optimization review (https://github.com/vertical-cloud-lab/powder-doser/pull/162, 2026-09-17);
  - flowability proxies (https://github.com/vertical-cloud-lab/powder-doser/issues/163#issuecomment-6032150664, 2026-10-07);
  - triboelectric models (#158, 2026-10-09) and drug-discovery uses (https://github.com/vertical-cloud-lab/powder-doser/issues/159#issuecomment-6088680565);
  - round-3 mock review of the hardware paper (https://github.com/vertical-cloud-lab/powder-doser/pull/97#issuecomment-5939998317, 2026-10-01);
  - 13 queries behind the physics-simulation survey (https://github.com/vertical-cloud-lab/powder-doser/pull/196#issuecomment-6538121768);
  - in-house powder tests (https://github.com/vertical-cloud-lab/powder-doser/pull/205, 2026-11-28).
  - None of these concern arms.
- Design decisions:
  - C-clip brackets replaced bolted split clamps (on the rig "since at least Aug 4").
  - Tap collar moving onto the plate (#203).
  - Fusion to Onshape migration (#193). "All files for this project should be on OnShape" (#177).
  - Carousel v7 as the baseline, a single actuator for lift and tilt, and a real balance with no shared funnel ("We can't use a funnel--the whole point of this is that there's no cross-contamination", 2026-10-29).
  - Reverse one auger revolution after dosing to limit leakage (https://github.com/vertical-cloud-lab/powder-doser/pull/185#issuecomment-6271740887, 2026-10-19).

### Ideas involving an arm

- **2026-07-15 meeting (before the cutoff):** "Ideas for an arm that clips modules in/out of the carousel" (https://github.com/vertical-cloud-lab/powder-doser/issues/128#issuecomment-4985379724).
- **swcharles, 2026-07-31:** a single-link arm "with a gripper on one end that grabs the augers" (https://github.com/vertical-cloud-lab/powder-doser/issues/128#issuecomment-5145184675). It was superseded by the arm-free station pitch in August.
- **Identity:** RFID vs AprilTags for identifying augers (https://github.com/vertical-cloud-lab/powder-doser/issues/133#issuecomment-5074223272, 2026-07-24). RFID "wins on robustness". AprilTags "win if ... you were going to add a camera anyway" and give "full 6-DOF pose".
- **Robot-served front covers** in carousel v8 (2026-11-12, above).
- **The PiPER plan itself** lives only in robot-arms #42 and #83 ("Powder-Doser Workflow 1": pick an auger from wood-block holders and place it in a box 10 mm larger than the auger, 3 spots × 30 trials, A–F grading; https://github.com/vertical-cloud-lab/robot-arms/issues/83, 2026-11-24).

---

## 3. vertical-cloud-lab/tensegrity-optimization

**Purpose.** "We print tensegrity-inspired structures in one piece from rigid PLA and flexible TPU on a dual-nozzle 3D printer, drop-test them on an instrumented drop tower, and let a Bayesian optimizer choose the next batch of designs" (https://github.com/vertical-cloud-lab/tensegrity-optimization/blob/main/README.md). The project page merged 2026-11-24 (https://github.com/vertical-cloud-lab/tensegrity-optimization/pull/139).

### The loop and how specimens are handled (project page, https://vertical-cloud-lab.github.io/tensegrity-optimization/)

- **Design (automated BO).** A GP surrogate in Ax recommends a batch over 5 geometry variables (R 25–40 mm, H 60–110 mm, twist 40–80°, strut Ø6–12 mm, tendon Ø3–5.5 mm), plus infill and filament settings from batch 3. Each design is projected onto a constant mass m\* = 30.95 g with a 250 cm³ envelope cap (https://github.com/vertical-cloud-lab/tensegrity-optimization/pull/35#issuecomment-5373292206).
- **Make.** One 9-specimen plate per batch, printed upright on the H2D (PLA left, TPU right), "with PLA supports painted by hand along the TPU tendons" in the slicer.
- **Handling (all manual).** Plate removal, support removal, an ID label around one strut, weighing, photos for the print log, then "we drop-test the labeled specimens one at a time on the drop-tower carriage".
- **Test.** A Lansmont Model 23 raises the carriage 60 in (1.524 m) and drops it onto polyurethane. There is a carriage accelerometer and a triaxial accelerometer on the top vertex. A seating check ("seat gauge", T1000/T180 ≥ 1.15 flags a bad seating; https://github.com/vertical-cloud-lab/tensegrity-optimization/pull/86#issuecomment-5648241877) gates the data. High-speed video at 959 fps comes from a camera that "we can only check it out for a day" from the PSC (https://github.com/vertical-cloud-lab/tensegrity-optimization/issues/91#issuecomment-5543835572, 2026-09-04).
- **Result.** 35 specimens over a seed batch and 3 BO batches. Hypervolume +56%. Best t180 0.803 (corny7).
- **Where it happens.** The drop tower is in CB 152A (SMASH lab) and is shared: "at least four research teams", booked by whole days. Setups must be put away after each session (https://github.com/vertical-cloud-lab/tensegrity-optimization/issues/115, 2026-10-03; https://github.com/vertical-cloud-lab/tensegrity-optimization/issues/115#issuecomment-6150496994, 2026-10-13).

### Changes since 2026-09-15

- Replicate plates: plate 1 was dropped 2026-10-17, with "56 mistimed captures; a knocking top sensor" (https://github.com/vertical-cloud-lab/tensegrity-optimization/pull/76#issuecomment-6455547099). "Drop tower use is temporarily halted" after the 10,000 g accelerometer broke on 2026-10-19 (https://github.com/vertical-cloud-lab/tensegrity-optimization/issues/115#issuecomment-6277017048). I found no resumption notice.
- Drop-tower SOP template (https://github.com/vertical-cloud-lab/tensegrity-optimization/issues/115#issuecomment-6511043024, 2026-10-29).
- JMD manuscript work (https://github.com/vertical-cloud-lab/tensegrity-optimization/pull/76, active 2026-11-28): Requests A, B, D and E merged 2026-11-05. Request C, which includes the noise-learning refit, merged 2026-11-26 (https://github.com/vertical-cloud-lab/tensegrity-optimization/pull/121).
- New threads: video-based tip velocity, 27 specimens and 81 filmed drops (https://github.com/vertical-cloud-lab/tensegrity-optimization/issues/134, 2026-11-16); crutch-tip collaboration with UNO (https://github.com/vertical-cloud-lab/tensegrity-optimization/issues/135, 2026-11-12); the campaign wrapping up toward lattices and crutch tips (https://github.com/vertical-cloud-lab/tensegrity-optimization/issues/110, 2026-09-15).
- "Storing T3 prism structures" has no answer (https://github.com/vertical-cloud-lab/tensegrity-optimization/issues/109, 2026-09-08).
- Printing now goes only through the approval-gated `@claude-print` (https://github.com/vertical-cloud-lab/tensegrity-optimization/pull/117, 2026-10-15).

### Simulation stack

- MuJoCo, PyBullet, PyChrono, Newton (Warp), DiffPD and PolyFEM+IPC demos (https://github.com/vertical-cloud-lab/tensegrity-optimization/pull/33).
- A MuJoCo drop-tower model ran a simulation-only BO campaign: BO reached 93.0% of the best-known hypervolume against 76.5–79.1% for the baselines. It was added to the paper 2026-11-05 (https://github.com/vertical-cloud-lab/tensegrity-optimization/pull/123). "The simulator benchmarks the optimizer and is not a substitute for the drop tower."

### Interfaces and arm ideas

- **Objects:** about 31 g PLA/TPU prisms, 60–110 mm tall, on an H2D plate.
- **Arm ideas:** none in the repo. The test step is off-site in a shared lab, so a BYU PiPER cell could at most clear plates, weigh, label and photograph specimens. The repo's automation is limited to the printer workflow.

---

## 4. vertical-cloud-lab/caliber

**Purpose.** CALIBER is an AI platform (RAG, a growing dataset and an uncertainty-aware loop) that "recommends high-fidelity acquisition settings" for SEM, EDS, EBSD and XRF on novel alloys (https://github.com/vertical-cloud-lab/caliber/blob/main/README.md).

### Loop state

- **Setting the parameters.** Sobol-seeded EDS parameter trials (https://github.com/vertical-cloud-lab/caliber/issues/21, 2026-10-14). A script prints each condition. The operator sets the beam on the SEM and types back the count rate and dead time (example, https://github.com/vertical-cloud-lab/caliber/issues/35#issuecomment-7044827089, 2026-11-20).
- **Where acquisition happens.** "It won't be able to happen during the actual imaging/data acquisition session since we are limited by the microscopy departments' computers" (https://github.com/vertical-cloud-lab/caliber/issues/5, 2026-07-23).
- **Analysis.** Quantification is done offline in DTSA-II. The six Sobol seeds were quantified 2026-11-16 to 11-20, with Mg at 0.36% after fixing the MgO standard (https://github.com/vertical-cloud-lab/caliber/issues/35#issuecomment-6932102975).
- **Manual sample handling.**
  - Polished pucks on Ted Pella 16111 pin stubs (Ø12.7 mm head, Ø3.2 × 8 mm pin), moved with groove-gripper tweezers after IPA sonication (https://github.com/vertical-cloud-lab/caliber/pull/6#issuecomment-5630207958, 2026-09-11).
  - Vacuum-desiccator storage holds for weeks (https://github.com/vertical-cloud-lab/caliber/issues/16#issuecomment-5917806283, 2026-09-30).
  - MgO standard cleaved by hand on 2026-10-09 (https://github.com/vertical-cloud-lab/caliber/issues/12#issuecomment-6090069989).

### Changes since 2026-09-15

- Standards bought and measured: Al, Si and MgO data on 2026-11-11/13 (https://github.com/vertical-cloud-lab/caliber/issues/12#issuecomment-6803490926).
- Stub-storage insert (https://github.com/vertical-cloud-lab/caliber/pull/17, 2026-09-23).
- Loaded-stub storage question (https://github.com/vertical-cloud-lab/caliber/issues/22, 2026-10-14).
- First NAB powder EDS (https://github.com/vertical-cloud-lab/caliber/issues/27, 2026-10-28).
- MSA proposals (https://github.com/vertical-cloud-lab/caliber/pull/14; scholarship .docx 2026-11-09).

### Arm idea

sgbaird asked: "what if this were meant to be something more automation friendly? ... automatically remove or insert samples ... A square or rectangular container would be easier to keep in a specific reference position" (https://github.com/vertical-cloud-lab/caliber/pull/17#issuecomment-5827730479, 2026-09-25). The reply recommended an SBS/ANSI-SLAS footprint (127.76 × 85.48 mm) and keyed carriers: "Robots move keyed carriers, not individual samples" (https://github.com/vertical-cloud-lab/caliber/pull/17#issuecomment-5828247331). This was not pursued further.

---

## 5. vertical-cloud-lab/digital-wetlab

**Purpose.** "Self-driving inorganic precipitation experiments on an Opentrons OT-2, Pitzer-model gaps for sulfide and sulfate scales, and the proposals built on them". The work moved here from a private repo in October 2026 (https://github.com/vertical-cloud-lab/digital-wetlab/blob/main/README.md).

### State

- The ACS PRF proposal was declined (https://github.com/vertical-cloud-lab/digital-wetlab/issues/81, 2026-10-24). Redirection options include AMPERE-2-style electrodeposition, brines, and oxide libraries on the OT-2 (https://github.com/vertical-cloud-lab/digital-wetlab/pull/83, 2026-10-29).
- **Hardware:** heater-shaker, HQ overhead camera, wireless colour sensor (https://github.com/vertical-cloud-lab/digital-wetlab/issues/80#issuecomment-6590137650, 2026-11-02).
- **BaSO4 "plate A"** (https://github.com/vertical-cloud-lab/digital-wetlab/pull/84):
  - "The OT-2 has no gripper, so it never moves the plate" (https://github.com/vertical-cloud-lab/digital-wetlab/pull/84#issuecomment-6804146306, 2026-11-11).
  - CI could not reach the robot (https://github.com/vertical-cloud-lab/digital-wetlab/pull/84#issuecomment-6934071142). timothy-commins filled the 96-well plate by hand with disposable pipettes on 2026-11-17 (https://github.com/vertical-cloud-lab/digital-wetlab/pull/84#issuecomment-6938864702).
  - A phone on a tripod inside the OT-2 took 1 photo every 2 min for 72 h (https://github.com/vertical-cloud-lab/digital-wetlab/pull/84#issuecomment-7049784223). The 5.16 GB of photos are in Box (https://github.com/vertical-cloud-lab/digital-wetlab/pull/84#issuecomment-7200675376, 2026-11-26).
  - Other manual steps: weighing powders in a fume hood in another lab, uncapping vials, and moving the OT-2 with "two people" (https://github.com/vertical-cloud-lab/digital-wetlab/pull/84#issuecomment-6686353276).
- **Camera.** The OT-2 lid camera and its network-link Pi went to the `borysgroup` lab at the U of U on 2026-11-10. Rebuild parts arrived 2026-11-17 and 11-24; the HQ camera and cable are still pending (https://github.com/vertical-cloud-lab/digital-wetlab/issues/92).

### Interfaces and arm ideas

- **Interfaces:** an SBS 96-well plate on the heater-shaker (slot 7); 20 mL vials, 27 mm Ø × 55 mm tall, in printed 6-vial holders (slots 4–5) (https://github.com/vertical-cloud-lab/digital-wetlab/pull/84#issuecomment-6804338336, https://github.com/vertical-cloud-lab/digital-wetlab/pull/84#issuecomment-6804648055).
- **Arm ideas:** none recorded.

---

## 6. vertical-cloud-lab/custom-induction-furnace

**Purpose.** "Retrofitting a commercial RF induction generator into a computer-controlled, vacuum and gas integrated annealing system for reactive-metal grain growth" (arXiv 2609.22118; https://github.com/vertical-cloud-lab/custom-induction-furnace/blob/main/README.md). The paper's spec table and BOM are "anchored on the current CEIA 'Power Cube' 6 kW + Master Controller v3+", with "the ~1970 LEPEL ... kept only as the originating prototype". Control is LabVIEW, with a custom graphite crucible/susceptor (https://github.com/vertical-cloud-lab/custom-induction-furnace/pull/3#issuecomment-4699230739, 2026-06-13).

**Status.** The paper is in review: "After 4 reviewers declined, one finally accepted on September 19th" (https://github.com/vertical-cloud-lab/custom-induction-furnace/pull/12#issuecomment-5768055473, 2026-09-21). An arXiv badge and citation were added 2026-09-24 (https://github.com/vertical-cloud-lab/custom-induction-furnace/pull/14). After that, only CI plumbing.

**Crucible handling (manual).**
- Crucible body OD 20.30 / ID 14.55 mm; alumina disc 14 mm; sapphire pyrometer window 9.5 mm (https://github.com/vertical-cloud-lab/custom-induction-furnace/pull/3#issuecomment-4859091445).
- Loading: "Specimen placed on an alumina sheet in the crucible body, then covered with a second alumina sheet", then the lid, then the window (https://github.com/vertical-cloud-lab/custom-induction-furnace/pull/3#issuecomment-4859268352, 2026-07-01).
- This is tweezer-scale work. No automation or arm plans.

---

## 7. CubOS, vclv, streamingLambda

**vertical-cloud-lab/CubOS** (https://github.com/vertical-cloud-lab/CubOS)
- A fork, created 2026-11-10, of Ursa Labs' CubOS: "Unified software interface for G-code based self driving lab systems" (https://github.com/Ursa-Laboratories/CubOS).
- What it does: a Python layer for GRBL gantries (Cub, CubXL, CubXL+), with YAML protocols, deck labware, offline motion validation, camera capture, SQLite records, a browser "Operator", an HTTP API and a SiLA 2 service.
- The fork has 0 commits of its own and is 28 behind upstream. Upstream ships `cub_xl_sterling*.yaml` gantry configs (https://github.com/vertical-cloud-lab/CubOS/tree/main/packages/core/configs/gantry). It has no issues.
- Arm relevance: it is the likely orchestration layer for the lab's CubXL. Its SiLA 2 and HTTP API are where an arm workflow could hand off to a gantry.

**vertical-cloud-lab/vclv** (https://github.com/vertical-cloud-lab/vclv)
- Created 2026-07-16. Its README is just "# vclv". It holds only Claude/Edison CI scaffolding and two scripts; its 8 items are workflow PRs and a seat-pool test (https://github.com/vertical-cloud-lab/vclv/issues/8, 2026-11-27).
- No stated purpose and no content to survey.

**vertical-cloud-lab/streamingLambda** (https://github.com/vertical-cloud-lab/streamingLambda)
- An AWS Chalice Lambda that "deploys ... automatic YouTube livestream creation and management" for the lab's Pi stream cameras: OT-2, powder doser, atomizer, OT-2 overhead.
- Since 2026-09-15:
  - Uptime by timestamp-overlay OCR: 96.77% for the OT-2 and 96.74% for the powder doser, Jul 30–Sep 25.
  - Pi fixes: IPv4 conflict detection off, a stream watchdog, and Wi-Fi recovery, installed on the doser Pi 2026-10-21 (https://github.com/vertical-cloud-lab/streamingLambda/pull/12, https://github.com/vertical-cloud-lab/streamingLambda/pull/12#issuecomment-6309055753).
  - The channel has 826 broadcasts (https://github.com/vertical-cloud-lab/streamingLambda/issues/15#issuecomment-6506426649, 2026-10-29).
  - "Deploy Chalice App" has failed since July on a cross-account IAM role (https://github.com/vertical-cloud-lab/streamingLambda/issues/16). The live Lambda still works.
- Arm relevance: PiPER wrist and fixed Pi cameras could reuse this pipeline and its watchdog.

---

## 8. vertical-cloud-lab/structural-alloy-sdl-workshop

- **What it is:** planning for a structural-alloys SDL workshop. Six planning issues were opened 2026-05-04 (sponsors, speakers, venues, related events, co-organizers, funders), each with an open, unmerged Copilot PR (https://github.com/vertical-cloud-lab/structural-alloy-sdl-workshop/pulls).
- **TMS 2028 symposium:** the proposal target deadline is Jan 31, 2027 (https://github.com/vertical-cloud-lab/structural-alloy-sdl-workshop/pull/6#issuecomment-4894673907; issue https://github.com/vertical-cloud-lab/structural-alloy-sdl-workshop/issues/13).
- **2026-09-24 discussion with Lianyi-Chen** (https://github.com/vertical-cloud-lab/structural-alloy-sdl-workshop/issues/15; notes in https://github.com/vertical-cloud-lab/structural-alloy-sdl-workshop/pull/16): "~\$10,000 baseline for University of Wisconsin venue", travel for "~3 to 5 invited speakers", "up to ~40 participants", NSF program-manager outreach.
- **2026-11-02:** a Radical AI contact is "OK to attend or have someone attend" (https://github.com/vertical-cloud-lab/structural-alloy-sdl-workshop/pull/16#issuecomment-6581892044). International invitees: "can invite, but likely won't be able to support" (https://github.com/vertical-cloud-lab/structural-alloy-sdl-workshop/pull/16#issuecomment-6582712959).
- No date is set and there are no outputs yet. Arms are not mentioned.

---

## 9. borysgroup/aurora-cloud-infra (all 42 items read)

**What it is.** Infrastructure for the `borysgroup` (U of U) MonArk/Aurora self-driving lab: cameras, streams, Claude CI and design files. It was transferred out of vertical-cloud-lab 2026-07-08 (https://github.com/borysgroup/aurora-cloud-infra/issues/14) and renamed from monark-cloud-infra 2026-09-04 (https://github.com/borysgroup/aurora-cloud-infra/issues/19). Aurora is a 2D-materials exfoliation glovebox with an Epson SCARA.

### PiPER history (#4) and the end-effector camera mount (#5)

**Purchase (#4).**
- Quote of 2025-09-23: "PiPer: $3150 ... XARM 6: $11150" (https://github.com/borysgroup/aurora-cloud-infra/issues/4#issuecomment-3324713466).
- The PiPER arrived 2025-11-18 (https://github.com/borysgroup/aurora-cloud-infra/issues/4#issuecomment-3549667940). A Utah PI paid for it, saying "even if MonArk is not using it, we can use it for our other SDLs in the future" (https://github.com/borysgroup/aurora-cloud-infra/issues/4#issuecomment-3555686881).
- 2026-09-04: not in use; "it seems like aurora does not need it" (https://github.com/borysgroup/aurora-cloud-infra/issues/4#issuecomment-5544630529).

**Mount (#5), open since 2025-09-27** (https://github.com/borysgroup/aurora-cloud-infra/issues/5).
- 2026-09-04 design notes (https://github.com/borysgroup/aurora-cloud-infra/issues/5#issuecomment-5543601164):
  - the flange mounts to J6 with "6× M3×8 countersunk bolts";
  - gripper base ≈70.5 × 145 × 63 mm, stroke 0–100 mm, 40 N, 500 g;
  - XT30 at the end joint, 24 V / 2 A;
  - J6 ±120° non-continuous;
  - prior art: ac-dev-lab #527 (xArm picam mount) and #328 (UR3e).
- Requirement (https://github.com/borysgroup/aurora-cloud-infra/issues/5#issuecomment-5543616570): "a Pi 5 with this, with two cameras attached to it (potentially two different types of cameras as well)". Payload 1.5 kg, reach 626.75 mm, standard–mini CSI cables up to about 500 mm.
- Glovebox space: "not sure if we are using this still for aurora as we are running out of space in the glovebox" (kinstonwithoutg, 2026-09-04, https://github.com/borysgroup/aurora-cloud-infra/issues/5#issuecomment-5544591812). sgbaird replied: "It would be more relevant for doing things outside the glovebox and transferring things in and out between other modules or stations. Though, it's not clear what that would be. Thanks for helping with getting things over to BYU so we can do some testing" (https://github.com/borysgroup/aurora-cloud-infra/issues/5#issuecomment-5845501930, 2026-09-26).
- No comments since, and no mount hardware committed here. A pan/tilt pod in #23 was "derived from the PiPER enclosure camera head in vertical-cloud-lab/robot-arms PR 9" (https://github.com/borysgroup/aurora-cloud-infra/issues/23#issuecomment-6697772005, 2026-11-06).

### Dual-camera Pi 5 (#16)

- Two HQ cameras on one Pi 5 for Aurora: "one doing livestreaming and the other available for command-based point-and-shoot ... or ... a wide-angle camera" (https://github.com/borysgroup/aurora-cloud-infra/issues/16, 2026-07-28).
- Parts were ordered in August. A parametric camera pod with an "AURORA-MNT-40" interface (4× M4 on 40 × 40 mm plus a central 1/4"-20) was designed 2026-09-15 (https://github.com/borysgroup/aurora-cloud-infra/issues/16#issuecomment-5677068919).
- Last activity: "status update? Do we have the parts in?" (2026-10-28, unanswered; https://github.com/borysgroup/aurora-cloud-infra/issues/16#issuecomment-6482619691).

### MonArk orchestration (#13)

- "They have a single computer for the semi-central orchestration; some station (like the microscope with picture vision ML) have their own computer ... their Epson robot 'arm' has detectors/sensors on other equipment so it knows how to stop - still runs code locally" (https://github.com/borysgroup/aurora-cloud-infra/issues/13#issuecomment-3367681193, 2025-10-04).
- No update since 2025-10-22. Prefect was put on hold (2026-06-25, https://github.com/borysgroup/aurora-cloud-infra/issues/8).

### New since 2026-09-15

- **Camera plan (#23).** At the 2026-10-26 walkthrough the goal became sample provenance. The pick-and-place camera was called "probably not the priority". Pi Zero 2 W + CM3 cameras go at the bulk-crystal unpacking area, mother-tape prep and exfoliator tip (https://github.com/borysgroup/aurora-cloud-infra/issues/23#issuecomment-6482728830).
- **Measured glovebox.** About 1.20 × 1.12 × 0.79 m (±5%), with an Epson T6-B602S on a 150–180 mm riser whose shaft reaches near the ceiling (https://github.com/borysgroup/aurora-cloud-infra/issues/23#issuecomment-6699337736, 2026-11-07). A reusable chamber model with robot-clearance checks is in `design/aurora-chamber` (https://github.com/borysgroup/aurora-cloud-infra/issues/23#issuecomment-6753055470, 2026-11-09).
- **Stud pan/tilt mounts.** Hardware, all-printed and kit variants (https://github.com/borysgroup/aurora-cloud-infra/pull/29). The ceiling camera "can't be tilted correctly", and the floor Pi saw under-voltage (https://github.com/borysgroup/aurora-cloud-infra/issues/23#issuecomment-6806606529, 2026-11-11).
- **BYU's OT-2 lid camera handed over** 2026-11-10 as the "cataloging stage overhead cam" (https://github.com/borysgroup/aurora-cloud-infra/issues/33, https://github.com/borysgroup/aurora-cloud-infra/pull/32, https://github.com/borysgroup/aurora-cloud-infra/pull/34). Aim and focus are still open.
- **Security cameras.** Amcrest cams relayed through the Pi 5 as "Exfoliation Overhead 1/2" (https://github.com/borysgroup/aurora-cloud-infra/pull/35#issuecomment-7015309878, 2026-11-19).
  - A YOLO segmentation model of the Epson was trained on mixed-reality renders: IoU 0.88 on held-out Overhead 1 frames, 123 ms on one Pi 5 core (https://github.com/borysgroup/aurora-cloud-infra/pull/35#issuecomment-7051650519, 2026-11-20).
  - The glovebox CAD now has an articulated URDF and gripper reach (https://github.com/borysgroup/aurora-cloud-infra/pull/35#issuecomment-7175055229, 2026-11-25).
  - Camera .150 has been offline since 2026-11-19 (https://github.com/borysgroup/aurora-cloud-infra/pull/35#issuecomment-7140740562).
- **Seven stream-cam Pis** given to CI (https://github.com/borysgroup/aurora-cloud-infra/pull/36, 2026-11-11).
- **Planned BYU trip.** Graphite-exfoliation test runs with chest cameras: McMaster graphite is the wrong form, so HOPG is suggested; the box has 15 in and 6 in antechambers (https://github.com/borysgroup/aurora-cloud-infra/issues/40#issuecomment-7141307009, 2026-11-24). U of U lab access was requested for sgbaird and jss265, and nickborys "submitted" it (https://github.com/borysgroup/aurora-cloud-infra/issues/41#issuecomment-7147349042, 2026-11-24).

### Arm-relevant interfaces at Aurora

- Antechamber transfers outside the box: 15 in and 6 in antechambers.
- Inside: a 6 × 10 chip tray on the exfoliator's heated stage; the Epson already does in-box pick and place.
- A PiPER (626.75 mm reach) inside a 0.79 m-tall box shared with the SCARA is unlikely. The stated fit is outside the box.

---

## Gaps / not verified

- I did not open repository files beyond READMEs and a few docs. CAD numbers above are as quoted in thread comments, at the commits they link.
- Powder-doser threads I skimmed rather than read in full: #131 (185 comments), #97, #124, #196, #205.
- Whether the tensegrity drop tower resumed after 2026-10-19 is not stated in the repo.
- The PiPER's arrival date at BYU is not recorded in aurora-cloud-infra beyond the 2026-09-26 thanks.
