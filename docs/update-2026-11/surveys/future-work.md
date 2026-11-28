# Robot arms in self-driving labs: stated future work, and who has done it since (as of 2026-11-28)

Prepared for BYU's Vertical Cloud Lab: AgileX PiPER arm, Raspberry Pi cameras, AprilTags, LeRobot, a cloud-lab model, and SDL work on Al alloys for laser powder bed fusion, powder handling and printed tensegrity structures.

## How this was done

- **Seeds (29 papers).** Taken from the Edison answers on branch `claude/issue-1-20261010-2326` (`docs/edison-6dof/q1`–`q4`), from `docs/wrtg-316/edison/selection.md` and `Final_Selection.md` (the proposal's `refs.bib` holds only LaTeX placeholders), and from the priority list in the request. Full references are at the end ([S1]–[S29]).
- **Limitations and future work.** Quoted verbatim from full text wherever an open copy could be reached: PubMed Central XML (10 records), arXiv HTML (12), the accepted manuscript on Strathprints (Burger), the bioRxiv v1 preprint (Harazono), the ChemRxiv preprint (RoboChem) and Internet Archive copies of RSC pages (Lo, Doloi). Three seeds are **abstract only** because the publisher blocked every route and no preprint exists: Radulov 2026 (RSC), Abolhasani & Kumacheva 2023 (Nature Synthesis, paywalled) and RABIT (IEEE, closed). Locations are the paper's section heading, or the page number of the copy read.
- **Citation graph.** OpenAlex `cites:` with `from_publication_date:2025-01-01`, run for all 32 OpenAlex records (Ada and Diffusion Policy each have two). That gave **11,095 unique citing works**, **2,232** of them with laboratory context in the title or abstract. These were screened with keyword sets for the eight opportunities and the stated future-work themes. About 70 were opened: full text for 20 (arXiv, PMC or archived copies), abstract for the rest. Targeted OpenAlex searches outside the citation graph added three relevant papers that cite none of the seeds ([AR4Calib], [Forte], [SO101Fail]).
- **Caveats.** OpenAlex lags for late-2026 preprints, and works without an indexed abstract were screened on title only. RSC, ChemRxiv and OUP block this runner, so [SmartLab], [PolymerSDL], [RoboRXN] and [RackInsert] were read from their abstracts only. A follow-up marked "not found" means not found in this screen, not that it does not exist. Semantic Scholar was used only for spot lookups, because of its rate limit.

Status key: **done** (the stated item has been demonstrated), **partly** (some of it, or on different hardware or in a different domain), **open** (no follow-up found), **n/a**.

---

## Per-seed tables

### S1. Burger et al. 2020, *Nature*: mobile robotic chemist (KUKA KMR iiwa). Read: accepted manuscript (FT).

| Stated limitation / future work (verbatim; location) | Follow-ups that address it | Status |
|---|---|---|
| "This level of precision allows navigation to the various experimental stations in the laboratory, but it does not allow fine manipulations, such as placement of sample vials. The precision was therefore enhanced by using a touch-sensitive 6-point calibration method." (p. 5); "The robot uses laser scanning and touch feedback, rather than a vision system." (p. 1–2) | [S8] LIRA (2025, FT): a wrist camera reading ArUco markers recalibrates at each station in 5 s versus ~53 s for touch, at 1.02 mm/1.01° (75 mm marker) versus 0.92 mm/0.90° for the cube. [PolymerSDL] (2026, Abs): ArUco-tagged stations, TurtleBot4 transport, wrist-camera cobots. [RackInsert] (2026, Abs): markerless zero-shot 6D pose with closed-loop refinement on a docked Franka, 83.1% insertion success. | **done** on industrial arms; **open** on low-cost arms |
| "it will be straightforward to add further modules, such as NMR or X-ray diffraction, now that the basic principles are in place." (p. 4) | [S2] added UPLC–MS and benchtop NMR; [S3] added PXRD with an ABB YuMi; [MobileProcChem] (2026, FT) adds work-up and analysis for process chemistry. | **done** |
| "The robot was charged but idle for approximately 32% of the time in this experiment … In principle, this time could be utilized to run other experiments in parallel." (p. 6) | None found that schedules several workflows on one mobile manipulator and reports the recovered idle time. | **open** (low priority for BYU) |
| "It took a significant investment of time to build this workflow (approximately 2 years), but once operating with a low error rate (Supplementary Fig. S38), it can be used as a routine tool." (p. 4); "Most errors could be reset remotely without being in the laboratory since all stations were equipped with 24/7 CCTV cameras" (p. 6) | [TeleIntervene] (2026, FT): teleoperated fault recovery on a UR3e with a 3D mouse; a decoupled control mode raised success in the precision-critical vial-lifting scenario from 71% to 86%. [RAINBOT] (2026, Abs): browser digital twin with remote intervention and e-stop. Neither reports how often faults happen. | **partly**: remote recovery studied, error rates still unreported |
| "This approach also has some limitations. … The robotic search does not capture existing chemical knowledge, nor include theory or physical models … In the future, we propose to fuse theory and physical models with autonomous searches" (p. 4) | [S4] A-Lab (2023) used DFT data and text-mined recipes; many algorithmic follow-ups (outside arm scope). | **done** (outside arm scope) |

### S2. Dai et al. 2024, *Nature*: mobile robots linking synthesis, UPLC–MS and NMR. Read: PMC (FT).

| Stated | Follow-ups | Status |
|---|---|---|
| "In principle, those restocking steps could be automated, too, using mobile robots." (Autonomous divergent syntheses) | None. No title or abstract among the 2,232 lab-context citing works mentions restocking or replenishment. [SelfBuilding] (2026, Abs) builds layouts, skills and twins, not consumable logistics. | **open** |
| "This modular approach should be scalable into the largest industrial laboratories, if necessary connecting physically separated synthesis and analytical labs using mobile robots that can traverse buildings" (Conclusion) | [PolymerSDL] (2026, Abs): ROS 2 navigation across rooms, with stations identified by ArUco tags and cobot workcells for extrusion, injection molding, weighing and mechanical testing. | **partly** (rooms, not buildings) |
| "One practical learning point … is the need for very low failure rates per module. For example, the workflow illustrated here required more than a year of development and debugging before it was stable enough to carry out these experiments." (Conclusion) | [S8] 600 pickups and insertions over 8 h with no failure; [MMBT] (2025, Abs): multimodal behaviour trees that check capping and transport; [AnomalyBT] (2026, Abs); [RoboRXN] (2026, Abs): multi-year bottleneck analysis. None reports a per-module failure rate or an MTBI. | **partly** |
| "Other future directions might include … the implementation large language models … as an interface to improve accessibility for researchers inexperienced in automation." (Conclusion) | [LLMStress] (2026, Abs): LLM agents on 45 workstations; only 3.3% of 4,608 trials gave executable workflows. [CuriesJarvis] (2026, Abs): an arm runs bench chemistry from a photo of a printed protocol. [RoboChemist] (2025, Abs). | **partly**; measured reliability is low |

### S3. Lunt et al. 2024, *Chem. Sci.*: ABB YuMi with KUKA KMR iiwa for a PXRD workflow. Read: PMC (FT).

| Stated | Follow-ups | Status |
|---|---|---|
| "While the videos presented here show a single cycle (one rack of eight samples), it should be possible in the future to operate this workflow 24/7 over extended periods in a closed-loop way" (Outlook) | [S8] (same group, 2025): "the full pipeline from reaction execution to PXRD analysis remains to be demonstrated in future work". [MobileProcChem]: 20 h 52 min of continuous running, in a different chemistry. | **open** |
| "we will need to introduce a suitable database and data standards" (Outlook) | Not screened (outside arm focus). | n/a |
| "These challenges should be addressable via improvements to the sample preparation methods and the PXRD matching algorithms." (Outlook) | [Dara] (2026, Abs): automated multi-hypothesis PXRD phase identification; [AEGrind] (2026, Abs): acoustic-emission feedback for robotic grinding; [DualArmGrind] (2026, title only). | **partly** |

### S4. Szymanski et al. 2023, *Nature*: A-Lab (title now "…accelerated synthesis of inorganic materials"). Read: PMC (FT).

| Stated | Follow-ups | Status |
|---|---|---|
| "Algorithms that can more effectively account for impurity phases in XRD patterns, augmented with additional characterization techniques such as electron microscopy and mass spectrometry, would benefit the next generation of autonomous research platforms." (Outlook) | [Dara] (2026): multi-hypothesis Rietveld refinement; [SEM-EDS] (2026, Abs): automated SEM-EDS quantification for powders. | **partly/done** |
| "The A-Lab used a short hold time of 4 h during its syntheses, which could be extended and combined with intermittent regrinding to improve the phase purity." (Experimental synthesis outcomes) | [DualArmGrind], [AEGrind] automate grinding, but not inside the A-Lab loop. | **partly** |
| "In future iterations of the platform, such an oracle may be expanded to investigate factors beyond synthesizability, including microstructure and device performance." (Outlook) | [NIMS-PSP] (2026, Abs): a robot arm automates heat treatment, XRD and impact testing of bulk steel in ~800 s per sample; [AIMD-L] (2026, Abs): high-throughput characterization of structural metals and ceramics. | **partly** |
| Implicit: "…successfully realized at a rate of >2 additional materials per day with minimal human intervention." (Outlook): interventions are not quantified | None quantifies A-Lab interventions. | **open** (see opportunity 1) |

### S5. Ada: MacLeod et al. 2020, *Sci. Adv.* and 2022, *Nat. Commun.* (N9 4-axis robot and UR5e). Read: PMC (FT).

| Stated | Follow-ups | Status |
|---|---|---|
| "Each of the two 35-sample campaigns took under 30 hours (including time for restocking consumables), and each had one failed sample. This failure rate is typical for our system." (2020, Results); "Ada could run unattended for 40–60 experiments until the necessary consumables … were exhausted." (2022) | This is the only per-sample failure figure among the seeds. No 2025–26 paper reports Ada-style per-sample failures together with consumable-limited lifetimes for an arm cell. [S27] asks for exactly that. | **open** (reporting and consumable logistics) |
| "The next stage of development for this robotic platform is to introduce sequential film deposition …"; "we plan to develop stand-alone synthesis and characterization modules that can run in parallel." (2020, Discussion) | None found among 595 citing works from 2025 on. | **not found** |

### S6. Wang, Terashima & Takano 2026, *STAM Methods*: NIMS arc-melting cell (Denso COBOTTA on a slider, ROS 2). Read: arXiv (FT).

| Stated | Follow-ups | Status |
|---|---|---|
| "…capability to integrate additional devices or functionalities in the future" (Introduction); "flexibility for future expansion of functions" (Abstract) | [NIMS-PSP] (NIMS/Tohoku, Oct 2026, Abs; cites S6): a robot-arm system for heat treatment, XRD and impact testing of bulk metals. [AlloyBot] (2026, Abs): automatic weighing and arc-melting, 1 alloy per hour, load-lock crucible exchange. | **partly/done** (not yet one loop) |
| "…to easily ensure a safe working environment where the system needs human assistance in the construction or trials errors period, as well as continuous maintenance and refilling of consumables." (§3.2): intervention frequency not reported | None. | **open** |

### S7. Radulov et al. 2026, *Digital Discovery*: vision-guided powder scooping. Read: **abstract only** (RSC blocks; no preprint), so hardware and powders could not be checked.

| Stated | Follow-ups | Status |
|---|---|---|
| "Autonomous, high-accuracy powder dispensing of heterogeneous solid materials remains an open challenge in automated chemistry laboratories. Existing systems often fail with diverse powder morphologies because they neglect the critical initial material acquisition step (i.e., scooping)." (Abstract) | [ToolPolicy] (2026, FT): co-optimizes a printed dispensing-tool shape and an RL policy, validated on an FR3; cohesive powders unsolved. [FLIP] (ICRA 2026, FT): simulation calibrated by angle of repose, plus curriculum RL. [ScoopTune] (2026, Abs): demonstration base policy plus residual RL to reach a target mass. [STORMS] (2026, Abs): stochastic sub-mg microsampling. [SCUValve] (ICRA 2026, title). [DryInventory] (2026, Abs): D405 depth versus RGB for powder level. | **partly**; none uses metal AM powders or a low-cost arm |

### S8. Zhou et al. 2025, *Commun. Chem.*: LIRA (KUKA KMR iiwa, wrist RealSense, ArUco). Read: PMC (FT).

| Stated | Follow-ups | Status |
|---|---|---|
| "In future iterations, markerless calibration strategies-such as those leveraging learned keypoints or contextual visual features-may further reduce the need for human involvement" (Evaluation of vision-based localization) | [RackInsert] (same group, CASE 2026, Abs): zero-shot 6D pose plus closed-loop refinement, 83.1% over 4 rack types and 6 OT-2 slots. [FiducialExo] (2026, Abs): a printed fiducial on every link gives camera-robot extrinsics for low-cost arms without hand-eye calibration. | **partly** |
| "…the full pipeline from reaction execution to PXRD analysis remains to be demonstrated in future work." (Discussion) | None. | **open** |
| "…LIRA's error recovery function relies currently on hardcoded logic to process VLM responses. An end-to-end solution using embodied AI techniques … could further enhance adaptability and autonomy." (Discussion); "If the error is deemed unrecoverable (e.g., a rotational misalignment), the workflow is paused, and human intervention is requested." | [S13] LabRobFail: VLM failure reasoning trained on synthetic trajectories; [ChemistEye] (2026, Abs): VLM safety monitoring that talks to robots; [TeleIntervene]: remote human recovery. | **partly** |
| "Future enhancements could expand LIRA's capabilities … incorporating robot navigation inspection and global path planning using overhead camera systems." (Discussion) | None. | **open** |

### S9. Darvish et al. 2025, *Nat. Comput. Sci.*: MATTERIX digital twin (Isaac Sim). Read: arXiv (FT).

| Stated | Follow-ups | Status |
|---|---|---|
| "…while hierarchical state machines offer an intuitive and user-friendly way to define workflows, they have limitations in deployment—particularly in recovering from failures or generating contingency plans." (Discussion) | [MMBT] (2025); [RoboCulture] (2026, Abs; same Toronto group): behaviour trees with vision and force, a 15 h autonomous yeast experiment; [AnomalyBT] (2026). | **done/partly** |
| "…the reliance on FoundationPose may introduce inaccuracies in object pose estimation, affecting real-world deployment precision." (Discussion) | [RackInsert]; [quARtet] (2026, FT): a printable four-tag AprilTag marker cuts RMS position error from 1.50 to 0.17–0.20 mm against a single tag (UR5e, fixed camera). | **partly** |
| "Future versions of MatteriX will integrate real-time feedback from IoT sensors … to detect deviations between simulation and reality." (Discussion) | [RAINBOT] (2026, Abs): a digital twin kept in sync with a low-cost printer-gantry liquid handler. | **partly** |
| "Future work could expand the skill library to include manipulation policies for soft materials, such as tubing, and delicate glassware." (Discussion) | None lab-specific. | **open** |

### S10. Darvish et al. 2024, *Matter*: ORGANA (Franka, LLM planning). Read: arXiv (FT).

| Stated | Follow-ups | Status |
|---|---|---|
| "…there is much to be done to develop a robust model-free transparent object perception, considering their textureless and reflective surface" (Limitations) | [S15] TransGraspNet (2026); [TransBiolab] (2026, title): dataset; [DeLTa] (2025, title). | **partly** |
| "Additionally, it lacks support for online replanning, limiting its adaptability to uncertainties in task execution." (Limitations) | [BioMARS] (2025, Abs); [RoboChemist] (2025); [LLMStress] (3.3% executable). | **partly** |
| "To fulfill the promise of flexible lab automation, the robotic agent should be able to automatically prepare the experimental setup, a capability currently lacking in the present work. For example, a mobile robot could retrieve clean beakers or vials from their shelves, insert pump tubes or sensory probes …" (Limitations) | [SelfBuilding] (2026, Abs) configures layouts and skills from a goal; [RobInHood] (2026, FT) still "necessitates some manual intervention, for example, to change the filtration cartridges". | **partly**; setup and consumables still **open** |

### S11. Boiko et al. 2023, *Nature*: Coscientist. Read: PMC (FT).

| Stated | Follow-ups | Status |
|---|---|---|
| "Although our setup is not yet fully automated (plates were moved manually), no human decision-making was involved." (Integrated chemical experiment design) | [BioMARS]; [CuriesJarvis]; [WetRobo] (2026, FT): a coding agent drives **AgileX PiPER** arms through wet-lab tasks (Petri lid, bottle cap, incubator door) in two labs. | **done** (transfer integrated); reliability unproven |
| "The development of new intelligent agent systems … raises potential concerns about the safety and potential dual-use consequences …" (Discussion) | [LABSHIELD] (2026), [SafeLab] (2026), [Safe-SDL] (2026), [SteeringSafe] (2025): benchmarks and frameworks. | **partly** |

### S12. Slattery et al. 2024, *Science*: RoboChem (flow, no arm). Read: ChemRxiv preprint (FT).

| Stated | Follow-ups | Status |
|---|---|---|
| "We are particularly excited about the modularity of the system and foresee its integration with different types of flow reactors and process analytical technologies in the future. Furthermore, we are eager to conduct further investigations into how different machine‐learning settings and models impact the rate of reaction optimization." (Conclusion and outlook, p. 16) | Not relevant to arms; the 302 citing works were screened only for arm themes. | n/a |

### S13. Wang et al. 2026, arXiv: LabRobFail (failure taxonomy and benchmark). Read: arXiv (FT).

| Stated | Follow-ups | Status |
|---|---|---|
| "…training relies entirely on synthetic data, which leaves a visual domain gap for real-world deployment, and the deterministic Action Dictionary restricts recovery flexibility. Future work will extend the VLA experiments and adapt the policy to interpret open-ended language corrections directly." (Conclusion and Limitations) | Only 2 citing works, both surveys. The nearest real-hardware failure taxonomy is [SO101Fail] (2026, Abs), for VLAs on a low-cost SO-101, not a lab. | **open** (no real-lab failure dataset) |

### S14. Lan et al. 2026, ICLR: AutoBio (simulated biology lab). Read: arXiv (FT).

| Stated | Follow-ups | Status |
|---|---|---|
| "…the manual effort required for asset digitization and protocol design limits the diversity of instruments and workflows." (Limitations and Future Work) | [LabUtopia] (2025), [LabDex] (2026), [SafeLab] (2026: 63 assets, 64 tasks), [SelfBuilding]. | **partly** |
| "Bridging this sim-to-real gap will require improvements in material modeling, actuator dynamics, and domain randomization." | No real-world transfer of AutoBio-trained policies found. [WetRobo]: a VLA fine-tuned in one lab failed in a second lab, where a coding agent succeeded. | **open** |

### S15. Hu et al. 2026, IROS: TransGraspNet (AUBO i5, transparent labware). Read: arXiv (FT).

| Stated | Follow-ups | Status |
|---|---|---|
| The "Conclusion and Future Work" section contains no future-work statement (full text checked). It reports 86.0% grasp success under occlusion and reflection. | No citing works yet. | n/a |

### S16. Ha, Agrawal & Song 2020, CoRL: Fit2Form (generative finger design). Read: arXiv (FT).

| Stated | Follow-ups | Status |
|---|---|---|
| "…since our algorithm focuses on geometry optimization, it does not optimize for the gripper strength, kinematic structure and grasping policy." "As future directions, it will be interesting to investigate the joint optimization of gripper geometry, kinematic structure, material, and grasping policy." (Conclusion and Future Directions) | [SoftCoDesign] (CoRL 2025, Abs): co-optimizes stiffness distribution and grasp pose, then 3D-prints and tests the grippers. [Dextra] (ICLR 2026, Abs): designs, trains, fabricates and deploys a hand in under 24 h. [LatentCoDesign] (RSS 2026, Abs). [ToolPolicy] does this for lab powder tools. | **done** (general robotics); **partly** for labware |

### S17. Zwirnmann et al. 2023, IROS: 3D-printed fingers for labware. Read: arXiv (FT).

| Stated | Follow-ups | Status |
|---|---|---|
| "In the future, we intend to integrate the fingers into typical laboratory workflows to validate their functioning and features in long-term experiments." (Conclusion) | None among the 6 citing works. | **open** |
| "Complementing the hardware solution proposed here with software tools that report failed grasping attempts or reduce sloshing will yield valuable feedback that can be integrated into the control loop." | [MMBT] (multimodal checks); [S15] (zero-spillage transport). | **partly** |

### S18. Zhao et al. 2023, RSS: ALOHA/ACT (low-cost bimanual teleoperation). Read: arXiv (FT).

| Stated | Follow-ups | Status |
|---|---|---|
| "ALOHA also struggles with tasks that require high amount of forces … This is because the low-cost motors cannot generate enough torque to support these manipulations." (Appendix F) | [FACTR2] (2026, Abs): learned external-torque estimation on commodity arms, with no force sensor, improves force-aware policies (+17% task progress). Torque capacity itself is not addressed. | **partly** |
| "…there exist tasks that are beyond the capability of either the robots or the learning algorithm" (Limitations and Conclusion) | [Cowling] (2026, Abs): 1,340 scored SO-101 episodes; ACT rises from 1/40 at 12 demonstrations to 37/40 at 100. [SO101Fail]; [BioProVLA] (2026, FT): SO-ARM101, ~US$800–850, biology-lab tasks; [CompactIL] (2026, Abs). | **partly**; no lab task shown at >99% |

### S19. Chi et al. 2023 (RSS) and 2024 (IJRR): Diffusion Policy. Read: arXiv (FT).

| Stated | Follow-ups | Status |
|---|---|---|
| "First, our implementation inherits limitations from behavior cloning, such as suboptimal performance with inadequate demonstration data." (Limitations and Future Work) | [Cowling]: on SO-101, Diffusion Policy peaked near 50% and "hardly ever started until an idle lead-in was trimmed", i.e. it is sensitive to demonstration curation on a low-cost arm. | **open** for lab tasks |
| "Second, diffusion policy has higher computational costs and inference latency compared to simpler methods like LSTM-GMM." | Large generic literature (not enumerated). | n/a |

### S20. Cadène et al. 2026, ICLR: LeRobot. Read: arXiv (FT).

| Stated | Follow-ups | Status |
|---|---|---|
| "First, robots coverage is currently far from exhaustive, as we support a practical but incomplete set of arms, grippers, sensors, and controllers." (Limitations) | [WetRobo] ships its own PiPER stack and demonstrations; [BioProVLA] uses the LeRobot data format on SO-ARM101. | **partly** |

### S21. Lo et al. 2024, *Digital Discovery*: frugal-twin review. Read: Internet Archive copy (FT).

| Stated | Follow-ups | Status |
|---|---|---|
| "In sharp contrast to chemistry applications, low-cost examples of SDLs for solid-state materials science are effectively non-existent." (§3.1); "…we propose a solid-based color-matching demo extension (… CLSLab:Solid) that uses a low-cost mobile robot arm, mixtures of granulated colored wax powders …"; "Both CLSLab:Solid and RoboChocolatier act as toy examples for the more industry-relevant materials discovery task of additively manufactured metal alloys for aerospace and automotive applications." (§6.1) | [AlloyBot] and [NIMS-PSP] automate alloy synthesis and testing on non-frugal hardware. No low-cost-arm solid-state SDL found. | **open**, and squarely BYU's niche |
| "Autonomy levels could also include failure rate/tolerance, number of iterations without manual intervention, or use of physics-based simulations to supplement experiments." (§6.3) | [ADePT] (2026, FT) scores capability from published reports and says studies "should report quantitative error and robustness alongside ADePT scores", including "per-step error rates … failure modes with recovery outcomes"; [S22] is a scale for user facilities. No autonomy scale yet uses measured intervention rates. | **partly** |
| "…mobile and fixed robotic arms …" listed among frugal-twin topics (§6.1) | [WetRobo] (PiPER), [BioProVLA] (SO-101), [OSCAR] (2026, Abs), [Forte] (2025, Abs: a printed arm under US$215). | **partly** |

### S22. Le Houx 2026, arXiv: BASE autonomy scale for user facilities. Read: arXiv (FT).

| Stated | Follow-ups | Status |
|---|---|---|
| "Before an agent is granted write-access to instrument control systems, it must pass a standardised competency assessment within a Virtual Beamline. This digital twin simulates the physics, hardware kinematics, and failure modes of the real instrument." (Sim-to-Real Certification) | None of the 4 citing works implements it. [RAINBOT] uses a twin for supervision, not certification. | **open**; relevant to pre-flight checks for remote users |

### S23. Tom et al. 2024, *Chem. Rev.*: SDL review. Read: PMC (FT).

| Stated | Follow-ups | Status |
|---|---|---|
| "However, major challenges in perception and decision-making limit the robust deployment of general-purpose robotic systems for flexible lab automation." (General-Purpose Robot Applied for Chemistry) | [S8], [RackInsert], [S13], [RoboCulture]. | **partly** |
| "Nevertheless, high-fidelity and performant simulation of deformable objects and particle systems (such as fluids and powders) … remain areas for future exploration." (Manipulation Skill Learning and Digital Twin) | [FLIP]; [DiffSkill] (2025, Abs): differentiable granular physics for powder transport; [ToolPolicy], whose stated limit is that its simulation "cannot accurately reproduce cohesive powders". | **partly** |
| "Additional safety issues may arise from the manipulation and perception capabilities of robotic systems, as these remain open problems in the community." (Robotics Safety in Laboratories) | [RobotSafetySLAS] (2026, Abs): an ISO-based assessment at Swiss CAT+ found that cobots can exceed force and pressure thresholds; [SafeLab]; [LABSHIELD]; [SAFE-CHEM] (2026, Abs); [Safe-SDL]. | **partly** |
| "Specifically in structural materials, hardware automation remains a challenge because of the inherent difficulties in solid-dispensing, extreme temperatures, and complex testing instrumentation." (Structural materials, Outlook) | [NIMS-PSP]; [AlloyBot]; [AIMD-L]; [SolToFurnace] (2026, Abs): two arms load crucibles into a furnace at 1600 °C; [AMLab] (2026 perspective on co-designing material and shape with AM). | **partly** |
| "The cost of hardware automation is a limiting factor for SDLs." (Open Hardware); "Initiatives, such as the creation of low-cost SDL prototypes and educational programs, play a vital role…" (Conclusion and Outlook) | [OSCAR], [OpenModular] (2026, Abs), [RAINBOT], [WetRobo], [BioProVLA], [LowCostLIBS] (2026, FT: a CNC gantry instead of an arm). | **partly** |

### S24. Seifrid et al. 2022, *Acc. Chem. Res.*: building an SDL. Read: PMC (FT).

| Stated | Follow-ups | Status |
|---|---|---|
| "Dispensing solids automatically is a well-known challenge, especially for solids with very different properties and for amounts less than approximately 20 mg." "Advances are ongoing; however, there is considerable room for improvement." (Replacing or Replicating Motor Function) | [STORMS] (sub-mg to mg), [SCUValve] (mg), [S7], [ToolPolicy]. | **partly** |
| "Some steps still require human intervention such as loading new vials or chemicals into the Chemspeed. To automate them, we are implementing robotic arms directly into our workflow that imitate human actions." (Future Perspectives) | [RobInHood] (2026, FT): a Franka in a fume hood does liquid and solid handling, capping and filtration, but still needs manual cartridge changes. | **partly** |
| "The idea is to monitor every operation and detect experimental failure early on." (Future Perspectives) | [S8], [MMBT], [ChemistEye]. | **partly** |
| "At the moment, there is no direct link between solution phase synthesis and solid-state characterization, and much work remains to be done to connect these two areas…" (Future Perspectives) | [SolToFurnace]: solution dispensing, then crucible, furnace and recovery by two arms. | **partly** |

### S25. Abolhasani & Kumacheva 2023, *Nat. Synth.*: SDL review. Read: **abstract only**.

| Stated | Follow-ups | Status |
|---|---|---|
| The abstract says the review will "discuss their current limitations and future opportunities"; the specific items are behind the paywall. | Its 630 citing works fed the theme screens above. | n/a |

### S26. Harazono et al. 2024, *SLAS Technol.*: microplate-transfer accuracy of a Dobot M1 Pro. Read: bioRxiv v1 (FT).

| Stated | Follow-ups | Status |
|---|---|---|
| "The results presented in this paper regarding positional repeatability and probability of successful transfer were specific to the hardware setup and parameters employed." "To harness the robot arm more extensively in the field of biology, the effects of these conditions must be investigated in the future." (pp. 17–18: gripper, labware, weight, posture) | None among the 7 citing works. | **open** |
| "Wider laboratory automation could be adopted if affordable robots such as the Dobot magician or myPalletizer, priced at approximately 1000 USD, are demonstrated to be suitable for transfers." "The effect caused by the differences in the type of robot arm remains unknown and thus should be studied." (pp. 17–18; reference numbers omitted) | [AR4Calib] (2026, Abs): absolute-accuracy calibration of a low-cost 6-DOF arm, with no labware task; [WetRobo] and [BioProVLA] run low-cost arms in labs but report no transfer-success-versus-offset data. | **open**; a direct fit for a PiPER/SO-101 study |

### S27. Volk & Abolhasani 2024, *Nat. Commun.*: SDL performance metrics. Read: PMC (FT).

| Stated | Follow-ups | Status |
|---|---|---|
| "In addition, assisted and unassisted demonstrated lifetimes should be clarified to help identify labor requirements and therefore scalability of an SDL." (Operational lifetime) | [PhysTestbed] (2026, FT): 24 cumulative hours unattended (6 × 48 iterations); [MobileProcChem]: 20 h 52 min; [RoboCulture]: 15 h; [S8]: 8 h and 600 operations. | **partly**: durations reported, assisted/unassisted split rarely given |
| "Furthermore, 71% of the studies reported no data quantifying the precision of the automated experimental system of the built SDL." "It is critical to the development of future SDLs that studies include clear and precise efforts to quantify the capabilities of the presented platform." | [Chajon] (2026: ISO 9283 elements on a UR3 with a Pi camera); [AR4Calib]; [ADePT]. | **partly** |

### S28. Wattoo et al. 2024, DSN: RABIT safety-rule tool. Read: **abstract only**.

| Stated | Follow-ups | Status |
|---|---|---|
| "These labs are exposed to human errors by inexperienced researchers working in the lab (e.g., setting incorrect target location could cause a robot arm to collide with an expensive piece of equipment)." (Abstract; the paper's future work is not accessible) | [SteeringSafe] (2025, cites RABIT); [RobotSafetySLAS]; [Safe-SDL]. | **partly** |

### S29. Doloi et al. 2025, *Digital Discovery*: 3D printing for low-cost SDLs. Read: Internet Archive copy (FT).

| Stated | Follow-ups | Status |
|---|---|---|
| Commercial robots "are often prohibitively expensive ranging approximately between $20 000 to $40 000, thus limiting their accessibility for research and educational purposes in cost-sensitive SDLs." (§3.5); "…further research is also demanded for providing an economic and scientific solution to industrial problems." (§4) | [Forte], [OSCAR], [RAINBOT], [OpenModular]. | **partly** (the call is generic) |

---

## Future work still open as of November 2026

Ranked by how many seeds state it, weighted by relevance to a low-cost-arm cloud lab doing alloy/powder and printed-structure work.

| Rank | Open item | Stated by | Closest follow-ups (all partial) | Why it matters for BYU |
|---|---|---|---|---|
| 1 | **Quantified reliability**: per-operation failure rate, intervention rate or MTBI, assisted versus unassisted lifetime, with confidence intervals | 14: S1, S2, S3, S4, S5, S6, S8, S9, S10, S13, S17, S21, S24, S27 | [S8] (600 operations, 0 failures, no CI); [RoboRXN] (bottleneck taxonomy over >3,000 actions, not an arm); [PhysTestbed] (24 h); [MobileProcChem] (20 h 52 min); [SO101Fail] (taxonomy, not a lab) | The community keeps asking for it and nobody publishes it; [ADePT] (2026) now asks for per-step error rates and failure modes with recovery outcomes. Cheap to generate with logged PiPER cycles. |
| 2 | **Low-cost hardware validated for lab tasks**: which inexpensive arm types are accurate and reliable enough, and under what gripper, labware and payload conditions | 7: S18, S20, S21, S23, S26, S27, S29 | [AR4Calib], [Forte], [WetRobo], [BioProVLA], [Cowling] | Harazono's "type of robot arm remains unknown" is unanswered for 6-DOF arms under US$5k. |
| 3 | **Solid and powder handling** across morphologies and small masses | 6: S4, S7, S21, S23, S24, plus S3 (sample preparation) | [ToolPolicy], [FLIP], [ScoopTune], [STORMS], [SCUValve], [DryInventory], [AEGrind] | All on a Franka or bespoke hardware with chemistry powders. Metal AM powders (dense, free-flowing, combustible) on a low-cost arm: **open**. |
| 4 | **Restocking, consumables and setup preparation** by the robot | 6: S2, S5, S6, S10, S24, plus [RobInHood]'s own limitation | [SelfBuilding] (layout and skills only) | Unattended lifetime is consumable-limited (Ada: 40–60 experiments). A cloud lab needs this. |
| 5 | **Structural and solid-state materials hardware**: solid dispensing, high temperature, mechanical testing, and microstructure or device properties | 5: S4, S6, S21, S23, S24 | [NIMS-PSP], [AlloyBot], [AIMD-L], [SolToFurnace], [AMLab] | Directly the alloy and printed-structure programme. No low-cost-arm version exists. |
| 6 | **Perception without touch calibration**: markerless or transparent/reflective objects, and vision-based station registration | 5: S1, S8, S9, S10, S23 | [S8], [RackInsert], [quARtet], [FiducialExo], [S15] | Metal crucibles, polished parts and glass. Fiducials on fixtures remain the pragmatic route. |
| 7 | **Safety for unattended and remote operation** | 5: S11, S22, S23, S28, plus S6 (cobot choice) | [RobotSafetySLAS], [SafeLab], [LABSHIELD], [Safe-SDL], [SAFE-CHEM] | Mostly simulation and benchmarks. No certified pre-flight check for remote users ([S22]'s proposal is unimplemented). |
| 8 | **Simulation fidelity for powders and soft materials** | 4: S9, S13, S14, S23 | [FLIP], [DiffSkill], [ToolPolicy] | Cohesive powders and tubing are still unsolved. |
| 9 | **Long-term validation of printed fingers and tools, with hardware-in-the-loop design** | 3: S16, S17, S23 (Jubilee tools) | [SoftCoDesign], [Dextra], [ToolPolicy] | Design → print → test exists in simulation-in-the-loop form; long-term lab validation has not been done. |
| 10 | **Learned policies at SDL-grade reliability** | 4: S8, S10, S18, S19 | [Cowling], [SO101Fail], [CompactIL], [BioProVLA] | Crowded field; best real low-cost results are about 90%, far from the >99% overnight campaigns need. |

---

## Overlap check for opportunities 1–8

| # | Opportunity | Verdict | Overlapping work (all verified) | What remains novel |
|---|---|---|---|---|
| 1 | First measured MTBI/intervention-rate dataset for an arm-based SDL on real hardware | **Not scooped** (window narrowing) | [S8] LIRA: 100 loops, 600 pickups and insertions, 8 h, 100% success, no CI or MTBI. [RoboRXN] (IBM, Abs): >3,000 actions over a multi-year cloud deployment, three bottleneck classes, but a commercial synthesis robot, not an arm. [PhysTestbed] (LLNL): 24 h unattended. [MobileProcChem]: 3 runs in 20 h 52 min. [TeleIntervene] (LLNL/Nottingham): a recovery-interface study. [SO101Fail]: failure taxonomy for VLAs on SO-101 (not a lab). No title or abstract among the 2,232 lab-context citing works mentions MTBI or an intervention rate (two mention "downtime"). Demand is explicit: [ADePT] (Feb 2026) asks studies to report "per-step error rates, inter- and intra-run variance, failure modes with recovery outcomes". | ≥500-cycle campaign with a LabRobFail-compatible taxonomy, exact binomial CIs and assisted/unassisted lifetime per [S27]. Liverpool (LIRA, RackInsert, RobInHood) and LLNL are the likely competitors. |
| 2 | Metrological characterization of a sub-$5k arm (ISO 9283 style) | **Partly scooped** | [AR4Calib] (Manufacturing Letters, Oct 2026, Abs): calibrates a low-cost **Annin AR4 MK3** with a wrist camera and a fiducial in 3–5 min with no human intervention. Validation "drew from ISO 9283", with dial indicators in a custom test stand, and average position error fell from 51 mm to 6.0 mm. [Forte] (Humanoids 2025): a printed arm under US$215 with "submillimeter repeatability" (the authors' own arm). [Chajon]: ISO 9283 elements with a Pi camera, on a UR3. Nothing found for the PiPER. | A full ISO 9283 RP/AP/drift/payload study of a **commercial** sub-$5k arm in SDL poses, with traceable dial-indicator ground truth. Cite [AR4Calib] and [Forte], and narrow the "first" claim. |
| 3 | Vision/fiducial-corrected manipulation primitives benchmarked open-loop vs corrected | **Partly scooped** | [RackInsert]: closed-loop vision refinement for rack insertion, 83.1% (Franka, markerless). [quARtet]: printable multi-AprilTag fiducial; single-tag 2.18° → 0.24–0.47° and RMS 1.50 → 0.17–0.20 mm; closed-loop pose-hold test (UR5e). [PolymerSDL]: ArUco plus YOLO with wrist-camera cobots doing "closed-loop correction" (Abs). [AR4Calib]: fiducial-based calibration. | A primitive set (vial, crucible, stub, lid) on a low-cost arm, each run open-loop and corrected, with per-primitive success CIs. [quARtet] is directly reusable on BYU fixtures. |
| 4 | Cloud-operated frugal SDL with reported uptime | **Partly scooped** (no uptime anywhere) | [SmartLab] (GT/Konkuk/SNU, JCDE 2025, Abs): open-source remote lab with a mobile manipulator; an intercontinental remote class (Tanzania–Korea); **90 additively manufactured specimens made and material-tested without human intervention**; no uptime figures in the abstract. [PICO] (MIT, 2026, FT): a robotic optics cloud lab on an xArm7 with fiducial-localized, 3D-printed housings; no uptime. [RAINBOT]: a printer-converted liquid handler with a browser twin and remote e-stop. [RoboRXN]: cloud-hosted, not frugal. | Uptime, intervention rate and remote-user statistics for a low-cost-arm cloud lab. **SmartLab is the closest precedent to BYU's printed-structure testing; read and cite it.** |
| 5 | Wrist-camera powder handling on metal powders | **Not scooped** (adjacent work is dense) | [S7] (full text blocked; hardware and powders not verifiable), [FLIP], [ToolPolicy], [ScoopTune], [STORMS], [SCUValve], [DryInventory]. None found uses metal AM powders, a low-cost arm, or a wrist camera for fill estimation. | Al-alloy LPBF powders, a wrist-mounted camera, a low-cost arm, and combustible-dust handling. Liverpool (Pizzuto) is moving fast. |
| 6 | Closed-loop generative gripper design → print → measured performance | **Largely scooped as a concept** | [ToolPolicy] (Liverpool/VU, Sep 2026, FT): BOHB over tool shape with an RL inner loop; the top designs are **3D-printed and measured** on an FR3 for powder dispensing. [SoftCoDesign] (CoRL 2025): optimized soft grippers 3D-printed and hardware-tested. [Dextra] (ICLR 2026): design to deployed hand in under 24 h. [LatentCoDesign] (RSS 2026). | Hardware-in-the-loop iteration (measure → redesign → reprint) for **labware grippers on a low-cost arm**, with long-term lab validation (which [S17] left open). |
| 7 | Lightweight tool changer for sub-1.5 kg arms | **Partly** (generic low-cost interfaces exist) | [Anyttach] (Duke, 2026, FT): passive self-locking PLA-printed interface, 15 end effectors, ~96% attach/detach success, limits 75.4 N axial and 1.61 N·m off-axis, on a Franka FR3. [SwapBot] (UW, 2026, FT): US$10 printed tool adapters on Franka, UR5 and Tycho. [MultiToolSync]: UR5e with a commercial Wingman changer at a synchrotron. None on a sub-1.5 kg arm or with lab tools. | Mass/torque-budgeted changer for PiPER/SO-101 class arms with SDL tools (scoop, pipette, gripper) and swap-reliability statistics. Benchmark against [Anyttach]'s limits. |
| 8 | Station-to-station recalibration with fiducials | **Partly scooped** | [S8] LIRA (2025): ArUco recalibration at each station, 5 s versus 53 s for touch, 1.02 mm/1.01°, on a KUKA KMR iiwa. Accuracy was measured as the robot's recorded pose against a touch-calibrated reference, with no external instrument. [PolymerSDL]: stations identified by tags across rooms. [RackInsert]: a docked trolley. [PICO]: fiducial-localized components. | Low-cost fixed arm with fixture-mounted AprilTag bundles; external dial-indicator ground truth (LIRA had none); recalibration drift over time. |

**Same arm, nearest group.** [WetRobo] (Oikawa et al., Sep 2026, Tsuda lab) is the only 2025–26 lab paper found that uses the **AgileX PiPER**: two PiPER arms with head and wrist cameras, driven by a coding agent through three wet-lab tasks in two labs. It reports single-task successes with no reliability statistics, and says "such long-horizon performance remains to be evaluated". It is the obvious paper to cite as the PiPER precedent, and it does not touch opportunities 1–8.


---

## References: seed papers

- **[S1]** Benjamin Burger et al., "A mobile robotic chemist," *Nature*, 2020. doi:10.1038/s41586-020-2442-2, https://doi.org/10.1038/s41586-020-2442-2
- **[S2]** Tianwei Dai et al., "Autonomous mobile robots for exploratory synthetic chemistry," *Nature*, 2024. doi:10.1038/s41586-024-08173-7, https://doi.org/10.1038/s41586-024-08173-7
- **[S3]** Amy M. Lunt et al., "Modular, multi-robot integration of laboratories: an autonomous workflow for solid-state chemistry," *Chemical Science*, 2024. doi:10.1039/d3sc06206f, https://doi.org/10.1039/d3sc06206f (arXiv: 2309.00544)
- **[S4]** Nathan J. Szymanski et al., "An autonomous laboratory for the accelerated synthesis of inorganic materials," *Nature*, 2023. doi:10.1038/s41586-023-06734-w, https://doi.org/10.1038/s41586-023-06734-w
- **[S5a]** Benjamin P. MacLeod et al., "Self-driving laboratory for accelerated discovery of thin-film materials," *Science Advances*, 2020. doi:10.1126/sciadv.aaz8867, https://doi.org/10.1126/sciadv.aaz8867 (arXiv: 1906.05398)
- **[S5b]** Benjamin P. MacLeod et al., "A self-driving laboratory advances the Pareto front for material properties," *Nature Communications*, 2022. doi:10.1038/s41467-022-28580-6, https://doi.org/10.1038/s41467-022-28580-6 (arXiv: 2106.08899)
- **[S6]** Wei-Sheng Wang et al., "Orchestration of heterogeneous experimental machines via ROS2 for automated bulk intermetallic synthesis," *Science and Technology of Advanced Materials Methods*, 2026. doi:10.1080/27660400.2025.2611510, https://doi.org/10.1080/27660400.2025.2611510 (arXiv: 2509.12011)
- **[S7]** Nikola Radulov et al., "Vision-guided adaptive scooping for powder weighing in autonomous chemistry laboratories," *Digital Discovery*, 2026. doi:10.1039/d5dd00569h, https://doi.org/10.1039/d5dd00569h
- **[S8]** Zhengxue Zhou et al., "Localization, inspection, and reasoning (LIRA) module for autonomous workflows in self-driving laboratories," *Communications Chemistry*, 2025. doi:10.1038/s42004-025-01770-1, https://doi.org/10.1038/s42004-025-01770-1
- **[S9]** Kourosh Darvish et al., "MATTERIX: toward a digital twin for robotics-assisted chemistry laboratory automation," *Nature Computational Science*, 2025. doi:10.1038/s43588-025-00924-4, https://doi.org/10.1038/s43588-025-00924-4 (arXiv: 2601.13232)
- **[S10]** Kourosh Darvish et al., "ORGANA: A robotic assistant for automated chemistry experimentation and characterization," *Matter*, 2024. doi:10.1016/j.matt.2024.10.015, https://doi.org/10.1016/j.matt.2024.10.015 (arXiv: 2401.06949)
- **[S11]** Daniil A. Boiko et al., "Autonomous chemical research with large language models," *Nature*, 2023. doi:10.1038/s41586-023-06792-0, https://doi.org/10.1038/s41586-023-06792-0 (arXiv: 2304.05332)
- **[S12]** Aidan Slattery et al., "Automated self-optimization, intensification, and scale-up of photocatalysis in flow," *Science*, 2024. doi:10.1126/science.adj1817, https://doi.org/10.1126/science.adj1817
- **[S13]** Haobo Wang et al., "LabRobFail: A Benchmark for Robotic Failure Analysis in Chemical Self-driving Laboratory," *arXiv*, 2026. arXiv:2607.23704, https://arxiv.org/abs/2607.23704
- **[S14]** Zhiqian Lan et al., "AutoBio: A Simulation and Benchmark for Robotic Automation in Digital Biology Laboratory," *International Conference on Learning Representations*, 2026. arXiv:2505.14030, https://arxiv.org/abs/2505.14030
- **[S15]** Hailing Hu et al., "TransGraspNet: Physically and Geometrically Consistent Manipulation of Transparent Labware," *IEEE/RSJ International Conference on Intelligent Robots and Systems (IROS)*, 2026. doi:10.1109/iros61738.2026.11776343, https://doi.org/10.1109/iros61738.2026.11776343 (arXiv: 2607.29567)
- **[S16]** Huy Ha et al., "Fit2Form: 3D Generative Model for Robot Gripper Form Design," *Conference on Robot Learning (CoRL 2020; PMLR 155, 2021)*. arXiv:2011.06498, https://arxiv.org/abs/2011.06498
- **[S17]** Henning Zwirnmann et al., "Towards Flexible Biolaboratory Automation: Container Taxonomy-Based, 3D-Printed Gripper Fingers," *IEEE/RSJ International Conference on Intelligent Robots and Systems (IROS)*, 2023. doi:10.1109/iros55552.2023.10342218, https://doi.org/10.1109/iros55552.2023.10342218 (arXiv: 2302.03644)
- **[S18]** Tony Z. Zhao et al., "Learning Fine-Grained Bimanual Manipulation with Low-Cost Hardware," *Robotics: Science and Systems*, 2023. doi:10.15607/rss.2023.xix.016, https://doi.org/10.15607/rss.2023.xix.016 (arXiv: 2304.13705)
- **[S19a]** Cheng Chi et al., "Diffusion Policy: Visuomotor Policy Learning via Action Diffusion," *Robotics: Science and Systems*, 2023. doi:10.15607/rss.2023.xix.026, https://doi.org/10.15607/rss.2023.xix.026 (arXiv: 2303.04137)
- **[S19b]** Cheng Chi et al., "Diffusion policy: Visuomotor policy learning via action diffusion," *The International Journal of Robotics Research*, 2024. doi:10.1177/02783649241273668, https://doi.org/10.1177/02783649241273668
- **[S20]** Rémi Cadène et al., "LeRobot: An Open-Source Library for End-to-End Robot Learning," *International Conference on Learning Representations*, 2026. arXiv:2602.22818, https://arxiv.org/abs/2602.22818
- **[S21]** Stanley Lo et al., "Review of low-cost self-driving laboratories in chemistry and materials science: the “frugal twin” concept," *Digital Discovery*, 2024. doi:10.1039/d3dd00223c, https://doi.org/10.1039/d3dd00223c
- **[S22]** James Le Houx, "Benchmarking Autonomy in Scientific Experiments: A Hierarchical Taxonomy for Autonomous Large-Scale Facilities," *arXiv preprint*, 2026. arXiv:2601.06978, https://arxiv.org/abs/2601.06978
- **[S23]** Gary Tom et al., "Self-Driving Laboratories for Chemistry and Materials Science," *Chemical Reviews*, 2024. doi:10.1021/acs.chemrev.4c00055, https://doi.org/10.1021/acs.chemrev.4c00055
- **[S24]** Martin T. Seifrid et al., "Autonomous Chemical Experiments: Challenges and Perspectives on Establishing a Self-Driving Lab," *Accounts of Chemical Research*, 2022. doi:10.1021/acs.accounts.2c00220, https://doi.org/10.1021/acs.accounts.2c00220
- **[S25]** Milad Abolhasani and Eugenia Kumacheva, "The rise of self-driving labs in chemical and materials sciences," *Nature Synthesis*, 2023. doi:10.1038/s44160-022-00231-0, https://doi.org/10.1038/s44160-022-00231-0
- **[S26]** Yoritaka Harazono et al., "Evaluation of microplate handling accuracy for applying robotic arms in laboratory automation," *SLAS Technology*, 2024. doi:10.1016/j.slast.2024.100200, https://doi.org/10.1016/j.slast.2024.100200
- **[S27]** Amanda A. Volk and Milad Abolhasani, "Performance metrics to unleash the power of self-driving labs in chemistry and materials science," *Nature Communications*, 2024. doi:10.1038/s41467-024-45569-5, https://doi.org/10.1038/s41467-024-45569-5
- **[S28]** Zainab Saeed Wattoo et al., "RABIT, a Robot Arm Bug Intervention Tool for Self-Driving Labs," *IEEE/IFIP International Conference on Dependable Systems and Networks (DSN)*, 2024. doi:10.1109/dsn58291.2024.00043, https://doi.org/10.1109/dsn58291.2024.00043
- **[S29]** Sayan Doloi et al., "Democratizing self-driving labs: advances in low-cost 3D printing for laboratory automation," *Digital Discovery*, 2025. doi:10.1039/d4dd00411f, https://doi.org/10.1039/d4dd00411f

## References: follow-up works (2025-01 to 2026-11)

Metadata from OpenAlex records retrieved 2026-11-28. "Access" in the text says what was read: full text (FT) or abstract (Abs).

- **[TeleIntervene]** Ziheng Wu et al., "Toward Resilient Self-Driving Laboratories through Telerobotic Interventions," *arXiv*, 2026-11. arXiv:2611.18496, https://arxiv.org/abs/2611.18496
- **[RoboRXN]** Matteo Manica et al., "Lessons Learned from Multi-Year Operation of a Cloud-Hosted Commercial Robot Driven by Domain-Specific Language Models," *ChemRxiv*, 2026-04. doi:10.26434/chemrxiv.15002359/v1, https://doi.org/10.26434/chemrxiv.15002359/v1
- **[MobileProcChem]** Emma J. Brass et al., "A mobile robotic process chemist," *Digital Discovery*, 2026-01. doi:10.1039/d5dd00563a, https://doi.org/10.1039/d5dd00563a
- **[RobInHood]** Louis Longley et al., "RobInHood: a robotic chemist in a fume hood," *Digital Discovery*, 2026-06. doi:10.1039/d6dd00007j, https://doi.org/10.1039/d6dd00007j
- **[PhysTestbed]** Tony Qin et al., "A Physical Testbed for Self-Driving Laboratories: Comparing Bayesian and Agentic Optimization in a Minimal Closed-Loop Color Formulation Task," *arXiv*, 2026-11. arXiv:2611.11690, https://arxiv.org/abs/2611.11690
- **[AR4Calib]** Kevin Oghalai et al., "A Non-contact, low cost Calibration Method for Robotic Arms in Smart Manufacturing Applications," *Manufacturing Letters*, 2026-10. doi:10.1016/j.mfglet.2026.08.019, https://doi.org/10.1016/j.mfglet.2026.08.019
- **[Forte]** Georges Chebly et al., "Strong, Accurate, and Low-Cost Robot Manipulator," *IEEE-RAS International Conference on Humanoid Robots (Humanoids)*, 2025-09. doi:10.1109/humanoids65713.2025.11203141, https://doi.org/10.1109/humanoids65713.2025.11203141
- **[Chajon]** Sebastián Chajón et al., "Photogrammetric Characterization of Robot Positioning Accuracy and Repeatability," *Robotics*, 2026-04. doi:10.3390/robotics15050086, https://doi.org/10.3390/robotics15050086
- **[FiducialExo]** Cameron Smith et al., "Fiducial Exoskeletons: Image-Centric Robot State Estimation," *arXiv*, 2026-01. arXiv:2601.08034, https://arxiv.org/abs/2601.08034
- **[RackInsert]** Hadi Beyzaee Juneghani et al., "An End-to-End Robotic System for High-Precision Rack Insertion in Automated Laboratories," *IEEE International Conference on Automation Science and Engineering (CASE)*, 2026-08. doi:10.1109/case69030.2026.11704402, https://doi.org/10.1109/case69030.2026.11704402
- **[quARtet]** Araki Wakiuchi et al., "quARtet Marker: A 3D-Printable Multi-Tag Fiducial for Robust Near-Frontal Pose Estimation," *arXiv*, 2026-10. arXiv:2610.01072, https://arxiv.org/abs/2610.01072
- **[PolymerSDL]** Miguel Hernández‐del‐Valle et al., "PERCEPTION-DRIVEN EXPERIMENTAL WORKFLOWS FOR SELF-DRIVING POLYMER LABS WITH MOBILE ROBOTS AND COBOT WORKCELLS," *ChemRxiv*, 2026-08. doi:10.26434/chemrxiv.15007960/v1, https://doi.org/10.26434/chemrxiv.15007960/v1
- **[SmartLab]** Won-Jae Yun et al., "SmartLab: Flexible and interoperable manufacturing laboratory system for remote education and research using a mobile manipulator," *Journal of Computational Design and Engineering*, 2025-03. doi:10.1093/jcde/qwaf034, https://doi.org/10.1093/jcde/qwaf034
- **[PICO]** Sachin Vaidya et al., "A Programmable Optics Cloud Laboratory," *arXiv*, 2026-09. arXiv:2609.16413, https://arxiv.org/abs/2609.16413
- **[RAINBOT]** Mohamed Rami Ayeche et al., "Scalable Low-Cost Laboratory Automation: A Digital Twin-Integrated Robotic Platform for Autonomous Liquid Handling (RAINBOT)," *arXiv*, 2026-07. arXiv:2607.20662, https://arxiv.org/abs/2607.20662
- **[ToolPolicy]** Nikola Radulov et al., "Tool-Policy Co-Design for Powder Weighing in Laboratory Automation," *arXiv*, 2026-09. arXiv:2609.39797, https://arxiv.org/abs/2609.39797
- **[FLIP]** Nikola Radulov et al., "FLIP: Flowability-Informed Powder Weighing," *IEEE International Conference on Robotics and Automation (ICRA)*, 2026-06. doi:10.1109/icra57385.2026.11696021, https://doi.org/10.1109/icra57385.2026.11696021
- **[DiffSkill]** Minglun Wei et al., "Differentiable Skill Optimisation for Powder Manipulation in Laboratory Automation," *arXiv*, 2025-10. arXiv:2510.01438, https://arxiv.org/abs/2510.01438
- **[ScoopTune]** Yichuan Peng et al., "ScoopTune: A Coarse-to-Precise Framework for Goal-Conditioned Precision Scooping," *IEEE International Conference on Systems, Man, and Cybernetics (SMC)*, 2026-10. doi:10.1109/smc63593.2026.11788961, https://doi.org/10.1109/smc63593.2026.11788961
- **[STORMS]** Adam Lisowski et al., "High-throughput solid microsampling through stochastic robotic automation," *Communications Chemistry*, 2026-07. doi:10.1038/s42004-026-02153-w, https://doi.org/10.1038/s42004-026-02153-w
- **[DryInventory]** Mostafa Abd Al Kader et al., "VISION-BASED DRY-MATERIAL INVENTORY ESTIMATION IN AUTONOMOUS LABORATORIES: RGB SEGMENTATION VERSUS RGB-D SURFACE RECONSTRUCTION," *ChemRxiv*, 2026-10. doi:10.26434/chemrxiv.15010138/v1, https://doi.org/10.26434/chemrxiv.15010138/v1
- **[SCUValve]** Tomoya Takahashi et al., "SCU-Hand with Integrated Single-Sheet Valve: A Funnel-Shaped Robotic Hand for Milligram-Scale Powder Handling," *IEEE International Conference on Robotics and Automation (ICRA)*, 2026-06. doi:10.1109/icra57385.2026.11697543, https://doi.org/10.1109/icra57385.2026.11697543
- **[Anyttach]** Weizhe Ni et al., "Any-ttach: Quick End-effector Swapping Enables Manipulation Dexterity with Simplicity," *arXiv*, 2026-05. arXiv:2605.30569, https://arxiv.org/abs/2605.30569
- **[SwapBot]** Yunchu Zhang et al., "SwapBot: Tool-Centric Robot Manipulation via Interchangeable End-Effectors and Tactile Sensing," *arXiv*, 2026-10. arXiv:2610.40646, https://arxiv.org/abs/2610.40646
- **[MultiToolSync]** Aditya Bondada et al., "Multi-Tool Robotics Enables In-Situ Sample Manipulation for Time-Resolved Synchrotron Measurements," *arXiv*, 2026-08. arXiv:2608.19280, https://arxiv.org/abs/2608.19280
- **[WetRobo]** Yuna Oikawa et al., "WetRobo: A Reproducible Robot Kit for Coding Agents in Biological Laboratories," *arXiv*, 2026-09. arXiv:2609.18435, https://arxiv.org/abs/2609.18435
- **[BioProVLA]** Zhaohui Du et al., "BioProVLA-Agent: An Affordable, Protocol-Driven, Vision-Enhanced VLA-Enabled Embodied Multi-Agent System with Closed-Loop-Capable Reasoning for Biological Laboratory Manipulation," *arXiv*, 2026-05. arXiv:2605.07306, https://arxiv.org/abs/2605.07306
- **[Cowling]** Simon Cowling, "From 12 to 200 Demonstrations: How ACT, Diffusion Policy, SmolVLA and $π_{0.5}$ Scale on a Low-Cost Arm," *arXiv*, 2026-10. arXiv:2610.37170, https://arxiv.org/abs/2610.37170
- **[SO101Fail]** Yi Yu and Xinchuan Qiu, "Benchmarking Vision-Language-Action Models on SO-101: Failure and Recovery Analysis," *arXiv*, 2026-06. arXiv:2606.08881, https://arxiv.org/abs/2606.08881
- **[FACTR2]** Steven Oh et al., "FACTR 2: Learning External Force Sensing for Commodity Robot Arms Improves Policy Learning," *arXiv*, 2026-06. arXiv:2606.12406, https://arxiv.org/abs/2606.12406
- **[NIMS-PSP]** Yulin Xie et al., "Development of an automated evaluation system for the process–structure–property relationship of structural metallic materials towards autonomous exploration," *Science and Technology of Advanced Materials Methods*, 2026-10. doi:10.1080/27660400.2026.2735657, https://doi.org/10.1080/27660400.2026.2735657
- **[AlloyBot]** Vignesh Selvaraj et al., "AlloyBot: On-Demand Synthesis of Bulk Alloys by Automatic Arc-Melting," *Research Square*, 2026-05. doi:10.21203/rs.3.rs-9761885/v1, https://doi.org/10.21203/rs.3.rs-9761885/v1
- **[AIMD-L]** Todd C. Hufnagel et al., "AIMD-L: An automated laboratory for high-throughput characterization of structural materials for extreme environments," *arXiv*, 2026-03. arXiv:2603.06835, https://arxiv.org/abs/2603.06835
- **[AMLab]** Peter C. Collins and Thomas K. Ales, "Additive manufacturing enabled autonomous laboratory for materials discovery and concurrent design of materials and shape," *MRS Bulletin*, 2026-06. doi:10.1557/s43577-026-01078-y, https://doi.org/10.1557/s43577-026-01078-y
- **[Dara]** Yuxing Fei et al., "Dara: Automated Multiple-Hypothesis Phase Identification and Refinement from Powder X-ray Diffraction," *Chemistry of Materials*, 2026-01. doi:10.1021/acs.chemmater.5c02820, https://doi.org/10.1021/acs.chemmater.5c02820
- **[SEM-EDS]** Andrea Giunto et al., "Accurate SEM-EDS quantification, automation, and machine learning enable high-throughput compositional characterization of powders," *Nature Communications*, 2026-08. doi:10.1038/s41467-026-76633-x, https://doi.org/10.1038/s41467-026-76633-x
- **[DualArmGrind]** Liubo Kong et al., "Dual-arm robotic powder grinding system for automated chemical laboratories," *Robotics and Autonomous Systems*, 2026-11. doi:10.1016/j.robot.2026.105860, https://doi.org/10.1016/j.robot.2026.105860
- **[AEGrind]** Yusaku Nakajima et al., "Acoustic emission-based monitoring for size-controlled robotic powder grinding," *RSC Advances*, 2026-11. doi:10.1039/d6ra06905c, https://doi.org/10.1039/d6ra06905c
- **[SolToFurnace]** Mohammadreza Lalegani Dezaki et al., "Autonomous Robotic Workflow for Solution-Based Synthesis and High-Temperature Thermal Processing toward Self-Driving Laboratories," *ChemRxiv*, 2026-10. doi:10.26434/chemrxiv.15010111/v1, https://doi.org/10.26434/chemrxiv.15010111/v1
- **[LLMStress]** Lulu Guo et al., "Stress-testing large language model agents in a robotic chemistry laboratory," *arXiv*, 2026-07. arXiv:2607.23045, https://arxiv.org/abs/2607.23045
- **[RoboChemist]** Zongzheng Zhang et al., "RoboChemist: Long-Horizon and Safety-Compliant Robotic Chemical Experimentation," *Conference on Robot Learning*, 2025-10. arXiv:2509.08820, https://arxiv.org/abs/2509.08820
- **[LABSHIELD]** Qianpu Sun et al., "LABSHIELD: A Multimodal Benchmark for Safety-Critical Reasoning and Planning in Scientific Laboratories," *arXiv*, 2026-03. arXiv:2603.11987, https://arxiv.org/abs/2603.11987
- **[SafeLab]** Fengshuo Bai et al., "SafeLab: An Interactive High-Fidelity Benchmark for Embodied Safety in Scientific Robotics," *International Conference on Machine Learning*, 2026-09. OpenAlex W7238660872, https://openalex.org/W7238660872
- **[RobotSafetySLAS]** Edy Mariano et al., "Robotic safety in self-driving laboratories," *SLAS Technology*, 2026-08. doi:10.1016/j.slast.2026.100463, https://doi.org/10.1016/j.slast.2026.100463
- **[SAFE-CHEM]** Laura Jones et al., "SAFE-CHEM: Uncertainty-Aware Policy Switching for Robust Robotic Chemistry," *IEEE International Conference on Automation Science and Engineering (CASE)*, 2026-08. doi:10.1109/case69030.2026.11704449, https://doi.org/10.1109/case69030.2026.11704449
- **[Safe-SDL]** Zihan Zhang et al., "Safe-SDL:Establishing Safety Boundaries and Control Mechanisms for AI-Driven Self-Driving Laboratories," *arXiv*, 2026-02. arXiv:2602.15061, https://arxiv.org/abs/2602.15061
- **[SteeringSafe]** Shi Xuan Leong et al., "Steering towards safe self-driving laboratories," *Nature Reviews Chemistry*, 2025-08. doi:10.1038/s41570-025-00747-x, https://doi.org/10.1038/s41570-025-00747-x
- **[MMBT]** Hatem Fakhruldeen et al., "Multimodal Behaviour Trees for Robotic Laboratory Task Automation," *IEEE International Conference on Robotics and Automation (ICRA)*, 2025-05. doi:10.1109/icra55743.2025.11128408, https://doi.org/10.1109/icra55743.2025.11128408
- **[RoboCulture]** Kevin Angers et al., "RoboCulture enables modular robotic plate-based cell automation," *Cell Reports Physical Science*, 2026-06. doi:10.1016/j.xcrp.2026.103335, https://doi.org/10.1016/j.xcrp.2026.103335
- **[AnomalyBT]** Yang Yang et al., "Anomaly Management in Multi-Robot Coordination: Detection and Handling Framework for Self-Driving Laboratories," *IEEE Transactions on Automation Science and Engineering*, 2026-01. doi:10.1109/tase.2026.3726436, https://doi.org/10.1109/tase.2026.3726436
- **[SelfBuilding]** Jiaru Bai et al., "Self-Building Labs," *arXiv*, 2026-10. arXiv:2610.23826, https://arxiv.org/abs/2610.23826
- **[ChemistEye]** Francisco Munguia‐Galeano et al., "Chemist Eye: a visual language model-powered system for safety monitoring and robot decision-making in self-driving laboratories," *Digital Discovery*, 2026-05. doi:10.1039/d6dd00062b, https://doi.org/10.1039/d6dd00062b
- **[LabUtopia]** Rui Li et al., "LabUtopia: High-Fidelity Simulation and Hierarchical Benchmark for Scientific Embodied Agents," *NeurIPS*, 2025-01. doi:10.52202/085713-1158, https://doi.org/10.52202/085713-1158
- **[LabDex]** Zhipeng Tang et al., "LabDex: A Hierarchical Benchmark for Dexterous Manipulation in Laboratories," *arXiv*, 2026-08. arXiv:2608.18618, https://arxiv.org/abs/2608.18618
- **[TransBiolab]** Ke Ma et al., "TransBiolab: A Real-World Multi-View Dataset of Cluttered Transparent Biomedical Objects," *ACM International Conference on Multimedia (ACM MM)*, 2026-11. doi:10.1145/3767308.3838674, https://doi.org/10.1145/3767308.3838674
- **[DeLTa]** Taeyeop Lee et al., "DeLTa: Demonstration and Language-Guided Novel Transparent Object Manipulation," *arXiv*, 2025-10. arXiv:2510.05662, https://arxiv.org/abs/2510.05662
- **[OSCAR]** David Pivin et al., "OSCAR: A Modular Open-Source Robotic Platform for Biological Laboratories," *ACS Synthetic Biology*, 2026-03. doi:10.1021/acssynbio.5c00733, https://doi.org/10.1021/acssynbio.5c00733
- **[OpenModular]** Pablo Quijano Velasco et al., "Open-Source Modular Laboratory Robots as Building Blocks for Flexible," *ChemRxiv*, 2026-05. doi:10.26434/chemrxiv.15003474/v1, https://doi.org/10.26434/chemrxiv.15003474/v1
- **[Dextra]** Kehlani Fay et al., "House of Dextra: Cross-embodied Co-design for Dexterous Hands," *International Conference on Learning Representations*, 2026-04. arXiv:2512.03743, https://arxiv.org/abs/2512.03743
- **[SoftCoDesign]** Sha Yi et al., "Co-Design of Soft Gripper with Neural Physics," *Conference on Robot Learning*, 2025-10. arXiv:2505.20404, https://arxiv.org/abs/2505.20404
- **[LatentCoDesign]** Kei Ikemura et al., "Latent Diffeomorphic Co-Design of End-Effectors for Deformable and Fragile Object Manipulation," *Robotics: Science and Systems*, 2026-07. doi:10.15607/rss.2026.xxii.195, https://doi.org/10.15607/rss.2026.xxii.195
- **[ADePT]** Pablo José Salazar Villacis and Brahim Benyahia, "The ADePT framework for assessing autonomous laboratory robotics," *Communications Chemistry*, 2026-02. doi:10.1038/s42004-026-01932-9, https://doi.org/10.1038/s42004-026-01932-9
- **[LowCostLIBS]** Xuan Cao et al., "Autonomous elemental characterization enabled by a low cost robotic platform built upon a generalized software architecture," *Digital Discovery*, 2026-01. doi:10.1039/d5dd00263j, https://doi.org/10.1039/d5dd00263j
- **[CompactIL]** Kanata Suzuki et al., "Compact Task-Aligned Imitation Learning for Laboratory Automation," *arXiv*, 2026-03. arXiv:2603.01110, https://arxiv.org/abs/2603.01110
- **[BioMARS]** Yibo Qiu et al., "BioMARS: A Multi-Agent Robotic System for Autonomous Biological Experiments," *arXiv*, 2025-07. arXiv:2507.01485, https://arxiv.org/abs/2507.01485
- **[CuriesJarvis]** Rumi Loghmani et al., "Curie's Jarvis: Autonomous Robotic Chemistry Experiments from Printed Protocols," *arXiv*, 2026-11. arXiv:2611.13251, https://arxiv.org/abs/2611.13251
