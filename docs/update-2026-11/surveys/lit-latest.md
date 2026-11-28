# Arm + vision projects for the Vertical Cloud Lab: what's new (literature scan, 2026-11-28)

**Scope.** This scan covers new work on robot arms and vision in labs, prioritising May–Nov 2026 (preprints flagged **[preprint]**), plus important 2025–early-2026 items that the Sept/Nov 2026 Edison/PaperQA scans missed. It does not re-summarize what those scans already covered: Liverpool mobile chemist and YuMi PXRD, A-Lab, Ada, NIMS COBOTTA, Franka powder scooping, MATTERIX, LabRobFail, autobio-bench, TransGraspNet, ACT/DP demo counts, VLA out-of-box rates, ISO 9283, Le Houx BASE, FoundationPose/MegaPose, Fit2Form, low-cost vs industrial comparisons, and fiducial station calibration. Those appear below only where a newer follow-up exists.

**Method.** WebSearch and WebFetch on primary pages (arXiv abstract/HTML, publisher or DOI pages, GitHub, Hugging Face, official announcements). Four parallel sub-scans covered topics 1+8, 2, 4+5 and 6+7; topic 3 and the assembly were done directly. Every entry was opened on its primary page, or carries "(record via …)" naming the reliable listing used instead. Twenty-four headline entries were then re-checked against their arXiv or primary pages: AMP1, CaP-X, ACE-CaP-0, AtomBridge, WetRobo, RoboColosseum, SO-101 Bench (including its real-robot table), the SO-101 failure benchmark (table), LoRA-SP, BioProVLA-Agent (hardware and table), Robo-MLT, RoboSynChallenge, Labference, Gemini Robotics 2, LeRobot v0.7.0, AnchorHEC, NSF PCL, CMU MICL, Texas A&M ARM-MIP, Prusa Pro AFS, PNNL AutoLabs, ORGANA, NIMO Controller and From Prompts to Protocols. Hardware details that come from a paper's body rather than its abstract are noted where they matter (e.g., PiPER use in WetRobo, RoboSynChallenge and Robo-MLT).

**Conventions.**
- "Findings (authors' claims)" are what the authors report, not independent results.
- "(our mean)" marks an average this scan computed from a paper's per-task table.
- Dates are the arXiv v1 date or the publication or announcement date.
- Model names such as "Claude Opus 5.5", "Gemini 4 Argon", "GPT-6.1 Sol" or "gpt-5.6-sol" are reproduced as the papers print them.

**Size.** 80 main entries plus 30 one-line entries in "Also verified" lists. Sections follow the requested topic order. Sections at the end cover what changed, open gaps, verification caveats and excluded leads.

## At a glance: published lab-manipulation work on the lab's own arm types

| Work (ID) | Arm | Lab task | Headline (authors' claims) | § |
| --- | --- | --- | --- | --- |
| RoboSynChallenge (arXiv:2608.12416, NeurIPS 2026 competition) | 2× AgileX PiPER | pipette, sample loading, mixer | π0.5 38.5% (sim-trained) / 33.0% (real-trained), averaged over 12 tasks | 1 |
| Robo-MLT (arXiv:2611.13039) | AgileX Static-Aloha (PiPER-class) | blood-gas analysis, tube sorting | 82% / 70% from 1,200 / 1,000 demos; +30 / +22 pp over π0.5 | 1 |
| TVF-DiT (arXiv:2603.01110) | AgileX Cobot Magic (PiPER arms) | tube cleaning and arranging, **powder transfer** | 86.6% average, but only 10 trials per task | 1 |
| AUTOHIAM (EPFL project) | PiPER + ArUco | hydrogel-infusion AM post-processing | no rates; docs report mm-scale PiPER drift | 1 |
| RoboChemist (CoRL 2025) | Cobot Magic ALOHA | flame test, neutralization | full protocols 65% / 40% vs π0 15% / 5% | 2 |
| LoRA-SP (ICRA 2026) | PiPER | tabletop (pour, pick-place) | 120 demos/task → π0 80–87%, SmolVLA 73–100% | 2 |
| WetRobo (arXiv:2609.18435) | PiPER (one arm used) | Petri lid, bottle cap, incubator door | Codex agent transferred across 2 labs; 25-demo π0.5 did not | 3 |
| BioProVLA-Agent (arXiv:2605.07306) | SO-ARM101 (~US$800–850) | centrifuge, cryotubes, water bath | AugSmolVLA 64% atomic (our mean), 100 demos/task | 2 |
| SO-101 failure benchmark (arXiv:2606.08881) | SO-101 | tabletop | π0.5 56%, ACT 34%, SmolVLA 33% (100 demos/task) | 4 |
| SO-101 Bench (arXiv:2610.36420) | SO-101 | spatial pick-place | real: agent + grasp policy 64%, π0.5 18% (sim-only training data) | 4 |
| RoboColosseum (arXiv:2611.02497) | SO-101 (+3 others) | tabletop, 124 sites | GR00T N1.7 82.4%, π0.5 77.6% (100 demos/task) | 4 |
| Gemini Robotics On-Device 2 (DeepMind, 2026-07-30) | shown on SO101 | — | adapts "typically with less than 200 examples"; early access only | 2 |
| NVIDIA SO-101 sim-to-real course | SO-101 | centrifuge vials into rack | no published success rates | 4 |
| RoboCOIN (Hub datasets) | Cobot Magic | e.g. organize test tubes (197 episodes) | data only | 4 |

No entry reports repeatability or accuracy measurements for either arm (see Gaps).

## 1. Robot arms, mobile manipulators and humanoids in labs; sub-$5k arms for lab tasks

WetRobo and Self-Building Labs are in §3, and RoboChemist is in §2.

- **CRESt** — Zhang, Z., Ren, Z., Hsu, C.-W., et al. (… J. Li) (2025). "A multimodal robotic platform for multi-element electrocatalyst discovery." *Nature*, 2025-09 (MIT News, 2025-09-25), DOI 10.1038/s41586-025-09640-5. https://www.nature.com/articles/s41586-025-09640-5 (record via MIT News and search; the Nature page needs a login)
  - Findings (authors' claims, per MIT News):
    - Hardware: a liquid handler, carbothermal-shock synthesis, automated electrochemistry, and electron and optical microscopy.
    - Scale and result: more than 900 chemistries and 3,500 tests in 3 months, giving an 8-element catalyst with 9.3× the power density per dollar of Pd.
    - Monitoring: cameras with VLMs flagged problems (a millimetre-scale deviation in sample shape, a pipette knocking an object out of place) and suggested fixes. Adopting some suggestions improved reproducibility, but humans still did most of the debugging.
  - Relevance: Real-SDL evidence that camera + VLM monitoring improves reproducibility, a model for a Pi-camera "watcher". The search is also a multi-element alloy-composition search.

- **Mobile robotic process chemist** — Brass, E. J., Veeramani, S., Zhou, Z., et al. (… A. I. Cooper) (2026). "A mobile robotic process chemist." *Digital Discovery* 5, 1363–1371, first published 2026-03-02, DOI 10.1039/D5DD00563A. https://pubs.rsc.org/en/content/articlelanding/2026/dd/d5dd00563a (record via the RSC listing and search; the full text returned 403)
  - Findings (authors' claims): A single mobile manipulator does all handling and transport between an automated synthesis reactor and a UHPLC-MS, and cleans the reactor between runs. The demonstration ran at 1000 mL; earlier mobile-robot chemistry stayed under 100 mL. Yields and purity matched human chemists. The authors estimate that weekly output with several reactors could reach about 12× a human process chemist's. That figure is extrapolated from timings, not measured.
  - Relevance: Liverpool's 2026 follow-up, using one general-purpose arm instead of several fixed arms at litre scale.

- **RoboSynChallenge** — Zhao, R., Wu, R., Li, C., et al. (2026). "RoboSynChallenge: Mastering Real-World Dexterity via Generalizing Synthesized Manipulation Skills." *arXiv:2608.12416* (NeurIPS 2026 Competition Track), 2026-08-12. **[preprint]** https://arxiv.org/abs/2608.12416
  - Findings (authors' claims):
    - Platform and tasks: real-world evaluation on two AgileX PiPER arms, across 12 tasks that include Manipulate Pipette, Sample Loading and Mixer Operating (beaker onto mixer).
    - Data: 1,000 synthetic trials per task (EmbodiChain) against 60 real samples per task.
    - Average success, sim-trained vs real-trained: π0.5 38.5% vs 33.0%; π0 22.0% vs 22.5%; Motus 31.5% vs 27.5%.
    - Item Assembly was 0/20 for every model.
  - Relevance: Off-the-shelf VLAs on PiPER pipette and sample-loading tasks currently succeed about a third of the time. Synthetic data roughly matched scarce real demos.

- **Robo-MLT** — Zeng, Z., Wang, K., Zhang, D. C., et al. (2026). "Robo-MLT: Dual-System Robotic Manipulation for Long-Horizon Medical Laboratory Tasks." *arXiv:2611.13039*, 2026-11-09. **[preprint]** https://arxiv.org/abs/2611.13039
  - Findings (authors' claims): Runs on an AgileX dual-arm Static-Aloha platform (PiPER-class arms) with 3 RealSense D435i cameras. A VLM planner, a multiframe execution monitor and a skill-conditioned VLA were trained on 1,200 (blood-gas analysis) and 1,000 (tube sorting) teleoperated episodes. Success was 82% and 70%, which is 30 and 22 points above π0.5 trained on the same data. Evaluation used 50 nominal configurations per method, plus 20 configurations in which an operator removes a sample and the system must replan.
  - Relevance: A budget estimate for long-horizon PiPER lab skills: getting above 70% took about 1k demos per task plus a planner and monitor.

- **TVF-DiT (compact imitation learning for lab automation)** — Suzuki, K., Nakamura, H., Miyamoto, K., Ogata, T. (2026). "Compact Task-Aligned Imitation Learning for Laboratory Automation." *arXiv:2603.01110*, v1 2026-03-01 (v2 2026-07-30). **[preprint]** https://arxiv.org/abs/2603.01110
  - Findings (authors' claims): Uses an AgileX CobotMagic dual-arm mobile manipulator (PiPER arms) with 3 RGB cameras. Training data was 500, 400 and 400 teleoperated episodes for test-tube cleaning, test-tube arrangement and **powder transfer**. The model is under 500M parameters, sized for low-VRAM GPUs. It scored 8/10, 9/10 and 9/10 (86.6% average), against 20.0% for SmolVLM2 alone and 36.6% for DINOv3 + SmolLM2. There were only 10 trials per task, and no comparison with ACT, Diffusion Policy or SmolVLA.
  - Relevance: Powder transfer on PiPER-class arms with a model a lab GPU can train, which bears on the powder doser. The trial counts are small.

- **Labimus** — Wu, Y., Jin, Z., Li, T., et al. (2026). "Labimus: A Simulation and Benchmark for Humanoid Dexterous Manipulation in Chemical Laboratory." *arXiv:2606.31037*, 2026-06-30. **[preprint]** https://arxiv.org/abs/2606.31037
  - Findings (authors' claims):
    - Setup: Isaac Sim (PhysX), a Tianyi dual-arm humanoid with BrainCo Revo 2 hands, more than 30 assets rebuilt from real organic-chemistry workstations, 6 atomic operations and a 7-step solid-weighing workflow.
    - Tier-1 completion (ACT / DP / π0): door open 56.7 / 49.3 / 47.3%; door close 24.7 / 6.7 / 40.7%; tare press 2.0 / 0.0 / 0.0%.
    - ACT grasp-and-place: 5.3% binary success, but only 3.3% also met the 15 mm placement tolerance.
    - The full weighing workflow is still being evaluated.
  - Relevance: Shows that task completion and protocol-valid results come apart. For PiPER weighing and dosing tasks, report the tolerance pass rate, not just success.

- **ASHE** — Fontenot, K., Gorti, A., Goel, I., et al. (… T. Buonassisi, A. E. Siemenn) (2025). "Closed-Loop Robotic Manipulation of Transparent Substrates for Self-Driving Laboratories using Deep Learning Micro-Error Correction." *arXiv:2512.06038*, 2025-12-04. **[preprint]** https://arxiv.org/abs/2512.06038
  - Findings (authors' claims):
    - Hardware: a UFACTORY xArm 5 (about US$6,000, plus a US$2,300 gripper) and a RealSense D435 imaging transparent glass substrates under blue light.
    - Error detection: a geometric model plus a shallow CNN flagged all 36 test placement errors (20 large, 12 medium, 4 small).
    - System result: 98.5% first-time placement over 130 trials (128/130). Both misplacements were caught and corrected on the second try.
  - Relevance: A cheap camera and small CNN that catch and correct placement errors on transparent labware. It should port to a PiPER + Pi HQ camera for vials and coupons.

- **AUTOHIAM** — Zhuang, S., Yee, D. (2025). "AUTOHIAM: Automated Robotic System for Hydrogel Infusion Additive Manufacturing Gen2&3." EPFL ALCHEMY lab project page and tutorial docs; no paper. **[project page]** https://epfl-alchemy.github.io/autohiam ; docs https://autohiam-tutorial.readthedocs.io/en/latest/troubleshooting.html
  - Findings (authors' claims):
    - Hardware and software: an AgileX PiPER arm (per the tutorial) on CAN, ROS 2 and cuRobo planning; ArUco-marker pose estimation, with beaker holders that have built-in marker slots.
    - Workflow: an Arduino peristaltic pump (about 1 mL per 2 s), an LLM front end for choosing protocols, and live camera monitoring for remote oversight.
    - Results: material performance "comparable to human operation" on Gen2 metal–ceramic workflows; no throughput or success numbers.
    - The docs warn that the PiPER accumulates millimetre-scale positional drift if left disconnected for a long time, and needs recalibration.
  - Relevance: PiPER plus fiducials running a metal/ceramic AM post-processing workflow, the closest analogue to this lab's alloy and AM work. It is also a field report of PiPER drift.

**Also verified (one line each):**
- **ADePT** — Salazar-Villacis, P., Benyahia, B. (2026). "The ADePT framework for assessing autonomous laboratory robotics." *Communications Chemistry*, 2026-02-20, DOI 10.1038/s42004-026-01932-9 (record via PMC12923569). https://www.nature.com/articles/s42004-026-01932-9 A perspective that defines four proficiency dimensions: adaptability and learning, dexterity, perception, and task complexity. It gives no scores, but offers a shared vocabulary for reporting PiPER vs SO-101 capability.
- **Tactus AI "Elsie"** — press release, 2026-07-27, https://www.newswise.com/articles/tactus-ai-brings-a-humanoid-lab-assistant-to-the-bench-at-adlm-2026. A wheeled two-armed humanoid for clinical labs. Each skill is stress-tested over "hundreds of simulated runs" in a digital twin of the bench, then validated on site and signed off by the customer's QA team. 3–5 launch labs planned in 2026; no performance data.
- **TARMAC** — Huang, K., Pipe, J., Martin, A. E., et al. (2025). *arXiv:2510.19289*, 2025-10-22, [preprint], https://arxiv.org/abs/2510.19289. A taxonomy of chemistry manipulation primitives built from teaching-lab demonstrations, composable into macros. Useful for structuring a PiPER skill library.
- **Affordable life-science arm** — Logan, Z., Dudash, A., Negrón, D. (2026). *arXiv:2603.20465*, 2026-03-20, [preprint], https://arxiv.org/abs/2603.20465. Open-source computer vision and ML on a modified 5-DOF arm for colony picking and liquid handling: mean position error under 1 mm, joint-angle error under 4°, colony IoU 0.537.

## 2. VLA and foundation-model policies applied to lab manipulation; lab-task benchmarks

### Lab applications (VLAs on chemistry and biology tasks)

- **LabVLA** — Ren, B., Liu, X., Chen, X., et al. (2026). "LabVLA: Grounding Vision-Language-Action Models in Scientific Laboratories." *arXiv:2606.13578*, 2026-06-11 (v2 2026-06-15). **[preprint]** https://arxiv.org/abs/2606.13578 (weights, MIT license: https://huggingface.co/zjunlp/labvla-4b-base)
  - Findings (authors' claims): 5B model (Qwen3-VL-4B + DiT flow-matching action expert) trained with the RoboGenesis simulation data engine (2,947 assets, 10,000 generated lab scenes). LabUtopia average success 71.1% in-distribution / 70.0% OOD, vs π0 63.3/63.2, X-VLA 57.5/52.9, GR00T N1.5 52.5/50.0, π0.5 52.4/52.1, SmolVLA 52.2/53.1. On a real Franka (4 tasks, 50 demos each, 50 rollouts) it is roughly tied with fine-tuned π0.5 and DreamZero: 86.5 vs 85.0 vs 87.0% (in-domain, clean) and 74.0 vs 71.5 vs 75.5% (OOD, clutter).
  - Relevance: first open lab-specific VLA, but its real-robot edge over a fine-tuned π0.5 is 1–3 points, so it is not yet a reason to pick it over π0.5/SmolVLA on the PiPER.

- **BioProVLA-Agent** — Du, Z., Wang, Z., Zhou, D., et al. (2026). "BioProVLA-Agent: An Affordable, Protocol-Driven, Vision-Enhanced VLA-Enabled Embodied Multi-Agent System with Closed-Loop-Capable Reasoning for Biological Laboratory Manipulation." *arXiv:2605.07306*, 2026-05-08 (v4 2026-10-19). **[preprint]** https://arxiv.org/abs/2605.07306
  - Findings (authors' claims): LLM protocol agent + VLM-RAG verifier + SmolVLA executor on SO-ARM101 hardware costing about US$800–850; 100 teleoperated demos per atomic task; 24-task benchmark (15 atomic, 6 composite, 3 bimanual). Single-arm atomic success (our mean of 12 tasks): AugSmolVLA 64.3%, SmolVLA 59.2%, ACT 43.6%, X-VLA 37.1%; bimanual 41.7 / 37.8 / 7.8 / 8.9%. Their augmentation for transparent labware and glare raised "place cryotube" under overexposure from 31.7% (SmolVLA) to 71.7%.
  - Relevance: the closest published match to this lab's SO-101 + LeRobot stack doing wet-lab work. Expect roughly 60% atomic success from 100 demos, and use cheap photometric augmentation against glassware glare.

- **RoboChemist** — Zhang, Z., Yue, C., Xu, H., et al. (2025). "RoboChemist: Long-Horizon and Safety-Compliant Robotic Chemical Experimentation." *CoRL 2025; arXiv:2509.08820*, 2025-09-10. https://arxiv.org/abs/2509.08820
  - Findings (authors' claims): π0 fine-tuned per primitive with 400 demos each on a Cobot Magic ALOHA dual-arm (4 RGB cameras, RTX 4090 inference at 20 Hz). A VLM (Qwen2.5-VL-72B) plans, supplies visual grasp/target prompts and monitors success and compliance. Primitive success rose from 40–85% (plain π0) to 85–100%. Full protocols: flame test 65% vs 15% (π0) and 5% (RDT); acid–base neutralization 40% vs 5% and 0%. Headline: +23.57% average success and +0.298 compliance rate over VLA baselines.
  - Relevance: a VLM monitor plus a VLA executor is what made multi-step chemistry work. 400 demos per primitive is the data cost to plan for.

- **Keyframe-guided RL for pipetting** — Qiu, Y., Sun, S., Ye, H., et al. (2026). "Keyframe-Guided Structured Rewards for Reinforcement Learning in Long-Horizon Laboratory Robotics." *arXiv:2603.00719*, 2026-02-28. **[preprint]** https://arxiv.org/abs/2603.00719
  - Findings (authors' claims): human-in-the-loop online RL on a VLA backbone, with rewards built from keyframes extracted from demos. 82% average success on four real lab tasks (including pipette-tip attachment and liquid transfer) after 40–60 min of online fine-tuning, vs 42% for HG-DAgger and 47% for Hil-ConRFT.
  - Relevance: for sub-millimetre steps such as tip pickup and vial insertion, an hour of on-robot RL may help more than extra demos.

- **Factory π0.5 deployment with transparent objects (Siemens)** — Zhu, B., Schmitt, P., Meister, P., et al. (2026). "A Factory-Floor Deployment Case Study of VLA Pipelines for Industrial Packaging Task: Workflow, Failures, and Lessons." *arXiv:2605.27461*, 2026-05-25. **[preprint]** https://arxiv.org/abs/2605.27461
  - Findings (authors' claims): π0.5 adapted over iterative collect–train–evaluate rounds with 2,535 episodes (~10 h) on two UR7e arms (LoRA on an RTX 5090, then full fine-tuning on a cluster). Final success "did not meet expectations" against a ≥70% gate. Of failed episodes, 23% were multiple transparent bags grasped together (bag borders not distinguished) and 15% incomplete insertions, partly from an occluded wrist view. They recommend human-in-the-loop interruption over scripted "teleoperate to failure" recovery data.
  - Relevance: transparent items and wrist-camera placement dominate failures. That applies directly to glass vials and the Pi HQ wrist camera.

### Fine-tuning evidence and data needs

The SO-101 benchmarks (the failure/recovery benchmark, SO-101 Bench and RoboColosseum) are in §4.

- **LoRA-SP on AgileX PiPER** — Kim, D., Bae, M., Nam, U., et al. (2026). "Adaptive Capacity Allocation for Vision Language Action Fine-tuning." *ICRA 2026; arXiv:2603.07404*, 2026-03-08. https://arxiv.org/abs/2603.07404 (code: github.com/dhkim-furiosa/LoRA-SP)
  - Findings (authors' claims): AgileX PiPER, 4 tasks (open pot, pour, press button, pick-place), 120 teleoperated demos per task, side + wrist RGB, 15 trials per cell. Multi-task full fine-tuning: π0 80–87%, SmolVLA 73–100%. LoRA-SP matches or beats this while training 9.2% (π0) or 17.1% (SmolVLA) of parameters. Standard LoRA r=16 collapses in multi-task training (0–40%), and the headline gain is up to +31.6% over standard LoRA.
  - Relevance: peer-reviewed fine-tuning numbers on this lab's own arm. About 120 demos per task gives 80–90% on simple tabletop skills, and low-rank LoRA should be avoided for multi-task policies.

- **How many demonstrations does a VLA need?** — Chand, R., Villa Floran, M. (2026). "How Many Demonstrations Does a VLA Need? On the Sample Efficiency of VLA Finetuning." *CoRL 2026 workshop; arXiv:2611.09964*, 2026-10-28. **[preprint/workshop]** https://arxiv.org/abs/2611.09964
  - Findings (authors' claims): six VLAs (π0, π0.5, GR00T N1–N1.7) on four LIBERO suites. π0.5 needs 2–5× fewer demos than π0 and is the most sample-efficient at every budget. Models within 2 points of each other at full data differ by up to 3× at 50 demos. GR00T N1.5 adapts more efficiently than N1.6/N1.7 on 3 of 4 suites. Freezing the VLM badly hurts π models but not GR00T.
  - Relevance: if demos are the bottleneck (remote teleop, student time), start from π0.5. Simulation only, so confirm on the arm.

- **LingBot-VLA / GM-100** — Wu, W., Lu, F., Wang, Y., et al. (2026). "A Pragmatic VLA Foundation Model." *arXiv:2601.18692*, 2026-01-26. **[preprint]** https://arxiv.org/abs/2601.18692
  - Findings (authors' claims): pretrained on ~20,000 h of real data from 9 dual-arm configurations, including an AgileX two-arm setup. GM-100 benchmark: 100 tasks per platform with 130 filtered demos per task. Average success: WALL-OSS 3.9%, GR00T N1.6 7.3%, π0.5 13.0%, LingBot-VLA 16.2–16.9%. On the AgileX platform: π0.5 17.2%, LingBot-VLA 18.9%. Code, base model and benchmark data are open.
  - Relevance: across broad many-task suites, real success is still in the teens even on AgileX hardware. Plan around narrow, repeated lab skills, not general instructions.

### Model releases most usable on PiPER / SO-101

- **GR00T N1.7 (and its LeRobot integration)** — NVIDIA (2026). "NVIDIA Isaac GR00T N1.7: Open Reasoning VLA Model for Humanoid Robots." *Hugging Face blog*, 2026-04-17; "NVIDIA Isaac Teleop and GR00T 1.7 Open VLA Model Available in LeRobot," 2026-07-07. https://huggingface.co/blog/nvidia/gr00t-n1-7 ; https://huggingface.co/blog/nvidia/nvidia-isaac-teleop-and-gr00t17-in-lerobot (N1.6, 2025-12-15: https://research.nvidia.com/labs/gear/gr00t-n1_6/)
  - Findings (authors' claims): 3B model with a Cosmos-Reason2-2B VLM and 32-layer DiT, pretrained with 20,854 h of human egocentric video; described as commercially licensed. In LeRobot it replaces N1.5, which is no longer supported. There is an SO-101 recipe (example: 50 episodes, 20k steps, batch 64) and LIBERO average 96.5% vs 87% for 1.5.
  - Relevance: the leading fine-tuned policy on SO-101 in RoboColosseum, with an official SO-101 path, though it scored only 24% real in SO-101 Bench's zero-real-data setting.

- **Gemini Robotics 2 / ER 2 / On-Device 2** — Google DeepMind (Parada, C.) (2026). "Gemini Robotics 2 brings whole body intelligence to robots." *Google DeepMind blog*, 2026-07-30. https://deepmind.google/blog/gemini-robotics-2-brings-whole-body-intelligence-to-robots/ ; ER 2 benchmarks: https://deepmind.google/models/gemini-robotics/embodied-reasoning/
  - Findings (authors' claims): On-Device 2 adapts to new bi-arm embodiments "typically with fewer than 200 examples" and was shown on Dexmate, SO101 and Trossen platforms; the VLA and On-Device 2 are early-access only. ER 2 is on Google AI Studio now. Its success detection scores 87.7% on images and 82.4% on video (vs 82.9/76.0 for ER 1.6), "generalized instrument reading" 65.7%, progress classification 57.4%, and human-proximity safety 93.0%.
  - Relevance: ER 2 can be used today as a video success/failure monitor and gauge reader for PiPER runs. On-Device 2 is the first frontier VLA shown on SO-101, but it needs early access.

- **MolmoAct2** — Fang, H., Duan, J., et al. (Ai2, 29 authors) (2026). "MolmoAct2: Action Reasoning Models for Real-world Deployment." *arXiv:2605.02881*, 2026-05-04. **[preprint]** https://arxiv.org/abs/2605.02881
  - Findings (authors' claims): fully open weights, data and training code, with LeRobot integration. It ships an SO-100/101 variant trained on 1,222 public LeRobot datasets (38,059 episodes, ~184 h). Zero-shot on real SO-100/101 (5 tasks × 15 trials, partial credit), the score was 56.7 vs 45.3 for π0-SO100/101 and 2.3 for SmolVLA. Control rate up to 55.8 Hz with caching.
  - Relevance: an open base pretrained on SO-101 community data, a natural starting checkpoint for the lab's SO-101s. It was weak (16%) in SO-101 Bench's spatial tasks.

### Benchmarks for lab manipulation

- **Pipette** — Liu, Z., Jin, H., Du, Z., et al. (2026). "Pipette: An Embodied Simulation Platform, Benchmark, and Data-Efficient Augmentation Framework for Wet-Lab Robotics." *arXiv:2606.12936*, 2026-06-11 (v3 2026-07-16). **[preprint]** https://arxiv.org/abs/2606.12936
  - Findings (authors' claims): Isaac Sim 5.1 / Isaac Lab 2.3, over 100 open wet-lab assets, 12 tasks, and three arm embodiments (Franka default; an AgileX arm is used for one shaker task). With 30 demos per task, ACT reaches 60.3%. Sim-replay augmentation lifts SmolVLA from 40.4% to 71.8% and π0 from 37.3% to 44.1%. No real-robot results.
  - Relevance: replaying a few real teleop demos with perturbed lighting, camera and speed is a cheap way to stretch scarce demos. It includes AgileX assets.

- **LabDex** — Tang, Z., Chen, S., Zhang, S., et al. (2026). "LabDex: A Hierarchical Benchmark for Dexterous Manipulation in Laboratories." *arXiv:2608.18618*, 2026-08-19. **[preprint]** https://arxiv.org/abs/2608.18618
  - Findings (authors' claims): real and simulated chemistry-lab benchmark (Franka FR3 + XHand, 3× RealSense D435i; 200 real demos per task, 50 in sim). Real atomic-skill success: π0.5 0.57, ACT 0.34, DP 0.02. No model completed the real long-horizon workflow (π0.5 averaged 0.62 atomic skills per attempt).
  - Relevance: even with 200 real demos per task, end-to-end lab workflows fail. Chain short skills behind checks rather than training one long policy.

- **DexBioLab (abstract calls it "AutoBio+")** — Wu, X., Shi, Y., Yang, Y., et al. (2026). "DexBioLab: Benchmarking Dexterous Manipulation with Dynamic Experimental Phenomena in Realistic Laboratories." *arXiv:2610.13643*, 2026-10-09 (v4 2026-10-16). **[preprint]** https://arxiv.org/abs/2610.13643 (AutoBio itself appeared at ICLR 2026: https://iclr.cc/virtual/2026/poster/10009217)
  - Findings (authors' claims): 14 tasks, 4 embodiments, flames, vapour and bubbles, and Gaussian-splat backgrounds from 6 real labs, built on mjlab. Mean task success (our mean over 12 tasks): π0.5 21.3%, GR00T N1.7 20.1%, DP 16.9%, Fast-WAM 16.8%. Real UR5e + XHand tube transfer trained on 10 real + 90 sim demos scored 66% with splat backgrounds vs 17% with plain MuJoCo backgrounds.
  - Relevance: if the lab builds a sim twin, photoreal (splat) backgrounds matter most when real demos are scarce.

- **SciHorizon-eLab / SciVLABench** — Qin, M., Qin, C., Zhang, Q., et al. (2026). "SciHorizon-eLab: An Agentic Protocol-to-Task Compiler for Scalable Benchmarking of Scientific Embodied Agents." *arXiv:2609.30971*, 2026-09-25. **[preprint]** https://arxiv.org/abs/2609.30971
  - Findings (authors' claims): compiles natural-language protocols into 300 certified MuJoCo tasks plus 15 human–agent coordination tasks. Average success: ACT 49.7%, π0.5 45.0%, DP 30.0%. Coordination tasks reach only 3–17%.
  - Relevance: shows that protocol-to-task compilation is automatable (a possible route to auto-generating training tasks for the OT-2 or doser workflows), and that hand-offs between humans and agents are the weakest link.

- **Labference** — Liu, S., Yang, X., Zhang, J., et al. (2026). "Labference: Benchmarking the Reasoning-Action Connection in Robotic Laboratories." *arXiv:2610.35252*, 2026-10-26 (v2 2026-11-02). **[preprint]** https://arxiv.org/abs/2610.35252
  - Findings (authors' claims): feedback-dependent weighing task (Franka in Isaac Sim 5.1; VLAs trained on 180 demos, 50 episodes each). π0.5 chose the correct weight 20% of the time and completed 16%; GR00T N1.5 18% and 8%. GPT-driven control chose correctly in 10/10 and completed 8/10, but with heavy computation.
  - Relevance: VLAs do not condition on measurement outcomes, such as a balance reading. Decisions that depend on the result (dosing to a mass) need an explicit reasoning or controller layer, which matters for the powder doser.

- **LabSafety Bench (journal version)** — Zhou, Y., Yang, J., Huang, Y., et al. (2026). "LabSafety Bench: Benchmarking LLMs on Safety Issues in Scientific Labs." *Nature Machine Intelligence* 8, 20–31 (2026); arXiv:2410.14182 v4 2026-02-12. https://doi.org/10.1038/s42256-025-01152-1 ; https://arxiv.org/abs/2410.14182
  - Findings (authors' claims): 765 multiple-choice questions and 404 scenarios (3,128 open-ended tasks), aligned with OSHA; 19 LLMs/VLMs evaluated; no model passes 70% on hazard identification.
  - Relevance: any LLM or VLM planner placed in front of the arm still needs hard-coded interlocks; it cannot be the safety layer.

- **LabShield** — Sun, Q., Chi, X., Rui, Y., et al. (2026). "LABSHIELD: A Multimodal Benchmark for Safety-Critical Reasoning and Planning in Scientific Laboratories." *arXiv:2603.11987*, 2026-03-12. **[preprint]** https://arxiv.org/abs/2603.11987
  - Findings (authors' claims): 164 operational tasks grounded in OSHA and GHS, tested on 20 proprietary, 9 open-source and 3 embodied models. Accuracy drops 32.0% on average in professional lab scenarios compared with general multiple-choice safety questions, worst on hazard interpretation and safety-aware planning.
  - Relevance: Evidence that LLM planners driving the arm need explicit safety layers, and a ready evaluation for any agent that controls the cell.

**Also verified (one line each):**
- **SmolVLA** — Shukor, M., et al. (Hugging Face, 14 authors) (2025). *arXiv:2506.01844*, 2025-06-02. **[preprint]** https://arxiv.org/abs/2506.01844 A 0.45B model pretrained on 481 community datasets. At launch it reported 78.3% on SO-100 (50 demos per task), against 61.7% for π0 and 48.3% for ACT, and async inference about 30% faster. Independent 2026 SO-101 results are far lower: 32.5% against 56.3% for π0.5 (§4).
- **π0.7** — Physical Intelligence (88 authors) (2026). "π0.7: a Steerable Generalist Robotic Foundation Model with Emergent Capabilities." *arXiv:2604.15483*, 2026-04-16. **[preprint]** https://arxiv.org/abs/2604.15483 Prompts carry metadata and subgoal images, so training can use imperfect autonomous data and non-robot data. It claims zero-shot cross-embodiment transfer. There are no open weights. openpi (https://github.com/Physical-Intelligence/openpi) still offers only π0, π0-FAST and π0.5, needing more than 8 GB of GPU memory for inference, 22.5 GB for LoRA and 70 GB for full fine-tuning. Local PiPER/SO-101 work therefore stays on π0.5.
- **Pi API beta** — Physical Intelligence (2026). "Frontier Models for Every Robot" (Pi API beta), 2026-10-13. (record via The AI Insider, 2026-10-14: https://theaiinsider.tech/2026/10/14/physical-intelligence-opens-pi-api-beta-for-robot-model-training-and-deployment/; pi.website returned HTTP 429.) Hosted fine-tuning and inference of PI's latest model by application; no pricing; one customer reached a deployable deburring policy after 4 days of iteration. Relevance: a route to PI's newest models on PiPER data without local GPUs, at the cost of cloud-inference latency.
- **π*0.6 / RECAP** — Physical Intelligence (2025). "π*0.6: a VLA That Learns From Experience." *arXiv:2511.14759*, 2025-11-18; listed in RSS 2026 proceedings (record via roboticsproceedings.org index; page blocked). https://arxiv.org/abs/2511.14759 — Advantage-conditioned offline RL on demos, autonomous rollouts and interventions; on the hardest tasks it more than doubles throughput and roughly halves failure rate. Relevance: a recipe for turning long cloud-lab autonomous runs plus operator corrections into policy gains.
- **LoRA SmolVLA on SO101 with an 8 GB GPU** — Omaisan, A. Y. A., Mohamed, I. S. (2025). "Towards Accessible Physical AI: LoRA-Based Fine-Tuning of VLA Models for Real-World Robot Control." *arXiv:2512.11921*, 2025-12-11. **[preprint]** https://arxiv.org/abs/2512.11921 — Button-press success by demo count: 20 → 18%, 50 → 45–52%, 100 → 68–72%, 200 → 74–76%. 4-bit quantization costs <2%; training takes 10–20 h and inference peaks at 6.8 GB VRAM on an RTX 4060. The paper calls its SmolVLA base "~3.1B", which conflicts with SmolVLA's 0.45B, so treat it with caution. Relevance: a demo-count curve on SO-101 class hardware with a student-laptop GPU.
- **RoboCulture** — Angers, K., et al. (2025). "RoboCulture: A Robotics Platform for Automated Biological Experimentation." *arXiv:2505.14941*, 2025-05. **[preprint]** https://arxiv.org/abs/2505.14941 (https://ac-rad.github.io/roboculture) — A non-learned baseline: behaviour trees with vision and force on a general-purpose arm. 15 h fully autonomous yeast culture; 99.0% pipette insertion over 576 attempts. Relevance: classical visual servoing plus force still beats VLAs on reliability for pipetting.
- **LabUtopia** — Li, R., Hu, Z., Qu, W., et al. (2025). "LabUtopia: High-Fidelity Simulation and Hierarchical Benchmark for Scientific Embodied Agents." *NeurIPS 2025 Datasets & Benchmarks; arXiv:2505.22634*, 2025-05-28. https://arxiv.org/abs/2505.22634 — 30 tasks in 5 levels, 200+ assets, chemistry-aware simulation. Results for π0, π0.5, GR00T N1.5 and SmolVLA (52–63%) appear in the LabVLA entry. Relevance: the de facto lab VLA leaderboard in 2026.
- **BioProBench** — Liu, Y., Lv, L., et al. (2025). "BioProBench: Comprehensive Dataset and Benchmark in Biological Protocol Understanding and Reasoning." *arXiv:2505.07889*, 2025-05-11 (v3 2026-01; ICML 2026 poster listed as "BioProBench: A Corpus and Benchmark for Biological Protocol Reasoning in Autonomous Science"). https://arxiv.org/abs/2505.07889 — ~27K protocols, ~556K instances, 5 tasks; LLMs handle comprehension but degrade on procedural reasoning. Relevance: text-only, so useful for protocol-agent layers rather than manipulation.
- **BEAKER** — Lin, F., Zhang, T., Gong, Z., et al. (2026). *arXiv:2611.06911*, 2026-11-04; NeurIPS 2026 Evaluations & Datasets (Spotlight). https://arxiv.org/abs/2611.06911 1,000 expert-written image and video questions across 11 task types for chemistry SDLs, tested on 28 MLLMs. Models follow coarse procedures but fail at affordance grounding and trajectory planning; the abstract gives no scores. A ready test for any VLM used as the cell's planner or monitor.
- **Robot Foundation Models in the Materials Lab (review)** — Takahara, I., Mizoguchi, T. (2026). "Robot Foundation Models in the Materials Lab: Benchmarks, Embodiments, and Open Challenges." *AI4Mat-NeurIPS 2026 workshop poster*. https://neurips.cc/virtual/2026/167815 (OpenReview: https://openreview.net/forum?id=f20usUpD66) — Argues task completion overstates experimental validity (precision, safety, protocol compliance) and lists seven open challenges. No numbers. Relevance: the first materials-focused review of VLA lab work, useful framing for proposals.

## 3. LLM and agentic robot control: code-as-policy, agentic manipulation policies, lab agents on real robots

### Agentic manipulation policies and code-as-policy

- **AMP1 (Apple)** — Bagherieh, O., Appiah Balaji, N. N., Chen, C., et al. (13 authors, Apple; incl. M. Müller and V. Koltun) (2026). "On Agentic Manipulation Policies." *arXiv:2611.09892*, v1 2026-11-06 (v4 2026-11-24). **[preprint]** https://arxiv.org/abs/2611.09892 ; code https://github.com/apple-aiml-research/ml-amp ; project page https://apple-aiml-research.github.io/ml-amp/
  - Findings (authors' claims):
    - **How it works:** a frontier model drives the arm by writing Python in a persistent interpreter against a small SDK, with no demos and no task-specific training. The SDK covers sensing (RGB, depth, camera pose, point clouds) and object segmentation and tracking, which the model can correct. Motion is timed TCP waypoints with damped-least-squares IK and sphere-based collision checks. The basic harness has no grasp primitive.
    - **Benchmarks:**
      - RoboLab-120: 85.6% zero-shot with Gemini 4 Argon and 82.8% with Claude Opus 5.5, against 49.2% for the best VLA and 42.9% for the best world-action model.
      - CaP-Gym: LIBERO-PRO 95.2% (π0.5 34.9%, CaP-Agent0 18.2%), robosuite 100% (700/700), BEHAVIOR-1K 96%.
      - RoboDojo (bimanual): a persistent memory folder of notes and code raised success from 26.4% to 84.1%, 4.6× fewer failures.
    - **Real world:** 104/108 trials (96.3%) on 12 tabletop tasks with a DROID-style Franka FR3 (three ZED cameras, stereo depth via S2M2). Baselines scored 45.4% (FLUX 3 Action) and 27.8% (π0.5).
    - **Speed and cost:** mean time to success was 280 s, 211 s of it reasoning, against 62 s for π0.5. A RoboLab episode with Opus 5.5 costs about US$1.39.
    - **Not tested:** bimanual and mobile setups were simulation only, and no low-cost arm was used.
  - Relevance:
    - This is the strongest evidence so far that a coding-agent harness can beat fine-tuned VLAs on quasi-static pick-and-place with zero demos.
    - Porting it to a 6-DoF PiPER with Pi cameras needs metric depth (stereo or an RGB-D camera) and good extrinsics.
    - At minutes per task, it suits slow, batch lab steps, not dynamic ones.

- **CaP-X / CaP-Gym / CaP-Bench** — Fu, L., Yu, J., El-Refai, K., et al. (16 authors; NVIDIA, UC Berkeley, Stanford, CMU; incl. K. Goldberg, Y. Zhu, F.-F. Li, L. Fan) (2026). "CaP-X: A Framework for Benchmarking and Improving Coding Agents for Robot Manipulation." *ICML 2026 (PMLR v306); arXiv:2603.22435*, v1 2026-03-23 (v2 2026-07-02). https://arxiv.org/abs/2603.22435 ; code https://github.com/capgym/cap-x (MIT licence)
  - Findings (authors' claims):
    - **CaP-Gym:** 187 tasks (7 robosuite, 130 LIBERO-PRO, 50 BEHAVIOR) packaged as Gymnasium environments. Agents act by writing programs over perception and control primitives.
    - **CaP-Bench:** 12 models evaluated (e.g. Gemini-3-Pro, GPT-5.1/5.2, Claude Opus 4.5). Success rises with human-crafted abstractions and falls as those priors are removed. No model matches human-written programs (88.5% average single-turn) zero-shot at Pass@1.
    - **CaP-Agent0** (training-free) matches or beats human code on 4 of 7 tasks.
    - **CaP-RL** (GRPO on Qwen2.5-Coder-7B), on a real Franka (N = 25): cube lift rose from 24% to 84% and cube stack from 12% to 76%, against 92% and 84% for human code.
  - Relevance: CaP-Gym is now the shared benchmark for code-as-policy agents (AMP1 reports on it). CaP-RL suggests a small, locally hosted code model can be RL-tuned in simulation and transfer to a real arm. That suits a cloud lab that cannot send every step to a paid API.

- **ACE-CaP-0** — ACE-CaP Team; Wei, C., et al. (28 listed authors) (2026). "ACE-CaP-0: Real-World Code-as-Policies in the Era of Experience." *arXiv:2611.16872*, 2026-11-12. **[preprint]** https://arxiv.org/abs/2611.16872
  - Findings (authors' claims): instead of querying a frontier model at run time, the agent's reasoning is turned into frozen code policies, refined through "Demonstrations on Request and Simulation on Demand". Across 8 real tasks (alignment, multi-object handling, bimanual), it succeeded in 92.1% of trials (221/240), with mean execution of 0.97–2.27 min. Perception and control run onboard, with no agent in the loop. The abstract gives no baseline comparison.
  - Relevance: tackles AMP1's practical drawbacks, latency and API cost per run, by developing with an agent and deploying frozen code. That fits repeated SDL steps on the PiPER.

### Lab-agent systems that drive real robots

- **WetRobo** — Oikawa, Y., Endo, K., Uzawa, T., et al. (incl. L. Pinto, S. Yang, K. Tsuda) (2026). "WetRobo: A Reproducible Robot Kit for Coding Agents in Biological Laboratories." *arXiv:2609.18435*, 2026-09-16. **[preprint]** https://arxiv.org/abs/2609.18435
  - Findings (authors' claims): The kit is two 6-DoF AgileX PiPER arms on CAN (every reported run uses the right arm), plus head and wrist cameras (2 in Lab X, 3 in Lab Y), iPhone RGB-D via Record3D, and 15 teleoperated demos per task used for replay. A coding agent (OpenAI Codex) completed bottle-cap removal in both labs. π0.5, fine-tuned for 100k steps on 25 Lab X demos, succeeded in Lab X but did not transfer to Lab Y. Outcomes come from single adaptation trials with successive attempts, not repeated independent runs, so the text gives no success-rate statistics.
  - Relevance: The closest published match to this lab's PiPER + camera cell. It gives a ready protocol for comparing coding-agent and VLA control across two sites (two cells, or two labs in a cloud-lab setting). Also one of the PiPER lab papers tabulated at the top.
  - Note: the abstract names the coding agent as "OpenAI Codex (gpt-5.6-sol)". The PiPER hardware and the π0.5 details come from the paper body.

- **Self-Building Labs** — Bai, J., Zhao, Y., Cao, Y., et al. (incl. T. Noël, A. Aspuru-Guzik) (2026). "Self-Building Labs." *arXiv:2610.23826*, 2026-10-16. **[preprint]** https://arxiv.org/abs/2610.23826
  - Findings (authors' claims):
    - What the agents generate: a lab layout reconstructed from photos, an Isaac Sim 6.1 (USD) digital twin, grasp and placement poses, cuRobo motions, and Python skill scripts with recovery branches. They also write and offline-check OT-2 protocols.
    - Real demonstration: an xArm5 on a linear rail, an OT-2, a plate sealer and a Cytation5 ran a 236-command OT-2 protocol plus 19 robotic stages for CdS quantum-dot synthesis.
    - Multi-robot coordination was shown only in simulation.
    - No time-saved or success-rate numbers.
  - Relevance: Uses the same ingredients as this lab (OT-2, an arm, a digital twin), so it is a template for agent-generated skills. It reports no reliability data.

- **AtomBridge** — Pang, Y., Zhou, B., Li, C., et al. (10 authors) (2026). "AtomBridge: Agentic VLA Inference Plugin for Long-Horizon Tasks in Scientific Experiments." *arXiv:2602.09430*, v1 2026-02-10 (v2 2026-08-14). **[preprint]** https://arxiv.org/abs/2602.09430
  - Findings (authors' claims): at each skill boundary, an LLM reasons about the mismatch between one skill's end state and the next skill's start state, then generates transition-motion code between frozen atomic-task VLA skills. On 8-step composed tasks, full-sequence success rises by 10–25% in simulation and in a real lab, with no extra demos.
  - Relevance: a cheap way to chain separately trained PiPER skills (e.g. uncap, then pipette, then recap) without collecting long-horizon demos.

**Also verified (one line each):**
- **ChemAgents** — USTC team (incl. T. Song, M. Luo, L. Chen, J. Jiang, Y. Luo) (2025). "A Multiagent-Driven Robotic AI Chemist Enabling Autonomous Chemical Research On Demand." *JACS*, 2025-03-08, DOI 10.1021/jacs.4c17738 (record via the Nature Index listing and ChemRxiv). A Task Manager agent directs Literature Reader, Experiment Designer, Computation Performer and Robot Operator agents on an on-board Llama-3.1-70B, across 7 tasks that include photocatalysis in a new robotic lab.
- **ORGANA** — Darvish, K., Skreta, M., Zhao, Y., et al. (12 authors) (2025). *Matter* 8(2):101897; arXiv:2401.06949 (v2 2025-01-07); journal record via an OUCI listing. https://arxiv.org/abs/2401.06949 An LLM-driven chemistry assistant with a robot arm. In the user study, users saved 80.3% of their time and frustration and physical demand fell by more than 50%; it ran a 19-step parallel plan to characterize quinones. It predates and complements MATTERIX.
- **AutoLabs (PNNL)** — Panapitiya, G. U., Saldanha, E. G., Job, H. M., Hess, O. R. (2026). *Scientific Reports* 16:19554, DOI 10.1038/s41598-026-45593-z (arXiv:2509.25651). https://www.pnnl.gov/publications/autolabs-cognitive-multi-agent-systems-self-correction-autonomous-chemical Multi-agent LLM that turns a request into a protocol for an Unchained Labs Big Kahuna liquid handler. A stronger reasoning model cut stoichiometry errors by more than 85%, and self-correction reached F1 > 0.89 on multi-step syntheses. Code at github.com/pnnl/autolabs. The same pattern would apply to the OT-2.
- **NIMO Controller** — Yoshikawa, N., Tamura, R. (2026). *arXiv:2605.15227*, v1 2026-05-13 (v2 2026-09-22). **[preprint]** https://arxiv.org/abs/2605.15227 Every SDL function is exposed as an MCP server, and agents either call the tools or generate NIMO workflows. Includes a user study on a colour-matching SDL; the abstract gives no numbers. A template for exposing the arm, doser and cameras to agents.
- **From Prompts to Protocols** — Angelopoulos, A., Cahoon, J. F., Alterovitz, R. (2026). *arXiv:2605.16552*, 2026-05-15. **[preprint]** https://arxiv.org/abs/2605.16552 An LLM agent inside the EOS orchestrator, with a synchronized node-graph editor. Across three simulated labs it generated a valid protocol on the first attempt 97% of the time and needed about 10× fewer interface actions.

**Cross-references (agentic results reported elsewhere in this file):**
- **RoboColosseum (§4):** zero-shot, frontier agents issuing one joint-target `move` call per turn out-progressed VLAs, but nothing exceeded 13% success.
- **SO-101 Bench (§4):** a GPT-6.1 Sol coding agent plus a learned grasp policy reached 64% on real layouts, against 18% for π0.5.
- **Labference (§2):** GPT-driven control picked the correct weight 10/10 times, against 20% for π0.5.
- **Guardian (§5):** a VLM failure detector used as a verifier for an LLM-based manipulation policy.
- **RoboChemist (§2):** a VLM planner and monitor wrapped around π0.
- **CRESt (§1):** camera + VLM monitoring in a real SDL.
- **Agentic SLS print–test loop (§6).**
- **DOE Genesis / CMU NREC project (§8):** agent-written robot code, tested in digital twins and shared across sites.

## 4. LeRobot ecosystem changes in 2026 and low-cost-arm reliability and benchmarks

- **LeRobot paper** — Cadene, Aliberts, Capuano et al. (Hugging Face, 17 authors) (2026). "LeRobot: An Open-Source Library for End-to-End Robot Learning." *ICLR 2026; arXiv:2602.22818*, 2026-02-26. https://arxiv.org/abs/2602.22818
  - Findings (authors' claims): "16K+ datasets from 2.2K+ individual contributors" in LeRobotDataset format as of Sept 2025. With SmolVLA on an SO-100, async inference vs sync: 19 vs 9 cubes moved per fixed 60 s episode (about 2.1x throughput), task time 137.5 s → 97.0 s, but average success 73.3% vs 78.3%. SO-100/101 listed at about €225 (€550 in parentheses, presumably the leader+follower pair).
  - Relevance: the reference to cite for the lab's SO-101 + LeRobot stack. Its async result (about 2x throughput for about 5 points of success) is the trade-off a Pi 5 client with an off-board GPU faces.

- **LeRobot v0.4.3 → v0.7.0 (2026 releases)** — Hugging Face (2026). "LeRobot releases v0.4.3, v0.4.4, v0.5.0, v0.5.1, v0.6.0, v0.6.1, v0.7.0." *GitHub huggingface/lerobot*, 2026-01-22 → 2026-11-05 (dates from the GitHub API). https://github.com/huggingface/lerobot/releases
  - Findings (release notes): v0.4.3 (Jan 22): Unitree G1, X-VLA, ROBOTIS OMX, SARM reward model, IsaacLab-Arena via EnvHub. v0.4.4 (Feb 27): Damiao CAN motors, OpenArm (incl. bimanual), streaming video encoding. v0.5.0 (Mar 9): Python ≥3.12, transformers v5. v0.5.1 (Apr 7): relative actions for pi0/pi0.5/pi0-FAST, HIL/DAgger collection. v0.6.0 (Jul 6): `lerobot-rollout` CLI; GR00T N1.7 replaces N1.5; MolmoAct2 (with SO-100/101 rollout support), TOPReward and ROBOMETER reward models; RoboTwin 2.0, RoboCasa365, LIBERO-plus and VLABench sim envs; native Seeed reBot B601 arm; training on HF Jobs (`--job.target`); about 2x faster dataloader; LeLab GUI (SO-101 only). v0.7.0 (Nov 5): `lerobot.async_inference` removed in favour of `lerobot[remote]` / `lerobot-policy-server` / remote rollout (JPEG image encoding option, router for robot↔GPU); pi0.5 MEM and training-time RTC; NVIDIA RoboLab benchmark; W&B replaced by Trackio; LanceDB dataset backend.
  - Relevance: breaking changes (Python 3.12, async API removed, GR00T N1.5 dropped) mean the lab should pin a LeRobot version per project. The remote policy server suits Pi 5 robot clients driven by a campus or cloud GPU in the cloud-lab model.

- **AgileX PiPER in LeRobot (plugins, not native)** — Hugging Face docs and AgileX (2025–2026). "Third-Party Robots & Teleoperators" (LeRobot docs) plus AgileX repos `piper_sdk`, `lerobot-agilex`, `agx_arm_sim`, `piper_isaac_sim`. *GitHub*, docs accessed 2026-11-28; agx_arm_sim last pushed 2026-07-29; piper_sdk 2026-10-14. https://github.com/huggingface/lerobot/blob/main/docs/source/third_party_robots.mdx ; https://github.com/agilexrobotics/agx_arm_sim
  - Findings: as of v0.7.0, upstream LeRobot has no native PiPER robot type. The docs list three drop-in PiPER plugins: AgRobotics Research `lerobot_robot_piper`; WeGo Robotics `lerobot_robot_piper` (multi-arm teleop, safety limits, GUI); FashionStar `lerobot-robot-piper` on PyPI (over CAN, paired with the `lerobot-teleoperator-pipermate` leader). AgileX's own `lerobot-agilex` is a fork for ACT training with ROS 2 inference. `agx_arm_sim` provides URDF/Xacro, **USD for Isaac Sim** and MoveIt 2 configs for piper/piper_h and other AgileX arms.
  - Relevance: the lab can record PiPER episodes in LeRobot format through a plugin, with no fork needed. agx_arm_sim's USD and URDF give a ready PiPER digital twin for Isaac Lab or MuJoCo work.

- **NVIDIA SO-101 sim-to-real course + GR00T N1.7 in LeRobot** — NVIDIA (course © 2026); Ben Horin et al., HF blog (2026-07-07). "Train an SO-101 Robot From Sim-to-Real With NVIDIA Isaac" and "NVIDIA Isaac Teleop and GR00T 1.7 Open VLA Model Available in LeRobot." *docs.nvidia.com learning path; huggingface.co/blog*. https://docs.nvidia.com/learning/physical-ai/sim-to-real-so-101/latest/index.html ; https://huggingface.co/blog/nvidia/nvidia-isaac-teleop-and-gr00t17-in-lerobot
  - Findings (authors' claims): the course task is unstructured pick-and-place of **centrifuge vials into a rack** with an SO-101, covering four sim-to-real strategies (domain randomization, co-training with real data, Cosmos augmentation, SAGE+GapONet actuator-gap estimation). Public data: 75 sim demos, with 5 real or 7/70 Cosmos-augmented episodes added. No success rates are published. GR00T N1.7 (3B) reaches a LIBERO average of 96.5% vs 87% for N1.5. The blog recommends about 50 episodes for the vial task.
  - Relevance: the closest ready-made lab-task sim-to-real recipe for the lab's SO-101, and a template for a PiPER version using agx_arm_sim's USD.

- **RoboCOIN** — Wu, Liu, Xie et al. (83 authors) (2025). "RoboCOIN: An Open-Sourced Bimanual Robotic Data Collection for Integrated Manipulation." *arXiv:2511.17441*, 2025-11-21 (v3 2026-04-13). **[preprint]** https://arxiv.org/abs/2511.17441
  - Findings (authors' claims and Hub metadata): 180,000+ demos, 421 bimanual tasks, 15 platforms, 432 objects. 820 LeRobot datasets on the Hub (`RoboCOIN/*`), about 21 of them lab-like. Examples: PiPER-based `Agilex_Cobot_Magic_organize_test_tube` (197 episodes) and `AI2_Alphabot_2_heat_test_tube` (404 episodes), plus shake beaker, organize lab equipment and scoop coffee beans.
  - Relevance: the largest public pool of PiPER-arm (AgileX Cobot Magic) demonstrations, including test-tube handling, for co-training a PiPER policy. Note that it is bimanual, not single-arm.

- **Lab-task LeRobot datasets on the Hub (snapshot)** — Hugging Face Hub API query by this scan (2026). Selected datasets: `DecisionFacts/Physical_AI_SO101_Test_Tube_Nesting_Task`, `labos-sim/real_human_pipetting_lerobot_anonymized`, `sreetz-nv/so101_teleop_vials_*`, `juyil/powder_weighing_sim_bowl8.25ml`, `lmsforAI/so101_powder_*`. *huggingface.co/datasets*, queried 2026-11-28. https://huggingface.co/datasets/DecisionFacts/Physical_AI_SO101_Test_Tube_Nesting_Task
  - Findings (dataset metadata): SO-101 test-tube nesting: 160 episodes, 264,190 frames, 2 RGB cameras, v3.0, CC BY-NC 4.0, updated 2026-11-22. Human pipetting video: 201 episodes. NVIDIA SO-101 vials-to-rack: for example, 49 real episodes. UR3 powder scooping onto a balance in Isaac Sim (scripted expert, target masses such as 0.850 g): 315 episodes. Bimanual SO-101 powder: 35 episodes (30 normal + 5 recovery). LeRobot-tagged search hits: "pipette" 63 (mostly Unitree G1 and YAM), "vial" 74, "test_tube" 70, "beaker" 25, "powder" 15; "chemistry", "glassware", "labware" and "build_plate" 0.
  - Relevance: lab-task data on low-cost single arms is sparse, and none of it covers LPBF plates or printer tending. An open PiPER/SO-101 lab dataset (vials, powder scooping, print removal) would be among the first.

### Low-cost-arm benchmarks and reliability

- **SO-101 VLA failure/recovery benchmark** — Yu, Y., Qiu, X. (2026). "Benchmarking Vision-Language-Action Models on SO-101: Failure and Recovery Analysis." *arXiv:2606.08881*, 2026-06-07 (v2 2026-06-11). **[preprint]** https://arxiv.org/abs/2606.08881
  - Findings (authors' claims):
    - Setup: 4 tasks, 100 teleoperated demos per task, and 20 real trials per model–task pair (320 episodes).
    - Average success: π0.5 56.25%, Wall-X 51.25%, ACT 33.75%, SmolVLA 32.5%. Colour sorting stayed at or below 10% for every model.
    - Execution instability (unstable grasps, repetition loops) causes most failures. Recovery rates: π0.5 30.8%, Wall-X 20.5%, ACT 6.5%, SmolVLA 3.2%.
    - Joint backlash and limited repeatability are named as noise sources but not measured.
  - Relevance: the realistic prior for SO-101 lab skills from about 100 demos: one-third success (ACT/SmolVLA) to one-half (π0.5). Gripper and grasp stability matter more than semantics.

- **SO-101 Bench** — Hickok, T. (2026). "SO-101 Bench: Accessible Spatial Manipulation." *arXiv:2610.36420*, 2026-10-27. **[preprint]** https://arxiv.org/abs/2610.36420 (code: github.com/5hadytru/so101_bench)
  - Findings (authors' claims): Isaac Lab digital twin of an SO-101 cell (overhead + wrist cameras, 640×480); 3,629 sim demos (18.5 h), 916 evaluation episodes, policies fine-tuned under an equal 36 h budget on 4×A100. On 45 real layouts: code-writing LLM agent + Galaxea 0.5 grasping 64% (84% in sim), Galaxea 0.5 53%, GR00T N1.7 24%, π0.5 18%, MolmoAct2-SO101 16%. Sim overestimates success by 9–31 pp but preserves the ranking exactly (Spearman ρ = 1.00).
  - Relevance: an open SO-101 twin for screening policies cheaply before real trials. An agent plus learned-grasp hybrid beat every pure VLA (see §3).
  - Note: the abstract's figures (best learned policy about 61%, agent hybrid 83.2%) are simulation results. The real-robot numbers above were re-checked against the paper's 45-layout table.

- **RoboColosseum** — Nguyen, T. S., Wang, Y. R., Shailesh, S., et al. (26–27 authors) (2026). "RoboColosseum: Evaluating Physical Intelligence at Scale In-The-Wild." *arXiv:2611.02497*, 2026-11-02. **[preprint]** https://arxiv.org/abs/2611.02497 ; https://robocolosseum.ai (LeRobot submission guide: docs/source/robocolosseum.mdx)
  - Findings (authors' claims):
    - Setup: more than 100 robots across 4 embodiments (SO-101, DROID Franka, bimanual YAM, Unitree G1). The Open Track has 5,699 blinded pairwise comparisons at 124 sites. The Fine-tune Track has 20 tasks with 100 demos each.
    - SO-101 fine-tuned success: GR00T N1.7 82.4%, π0.5 77.6%, MolmoAct2 59.2%, G0.5 40.0%, LingBot-VLA v2 36.8%.
    - Rankings barely transfer across embodiments (Kendall W = 0.24). SO-101 rankings were the least reproducible between random halves of the sites: 59% pairwise agreement, against about 85% for Franka and YAM.
    - Zero-shot, three frontier LLM agents (one joint-target `move` call per turn, at most 30 calls per trial) beat VLAs on task progress by 5.3 pp on average. Still, no system exceeded 13% success in any category, and the G1 completed no tasks.
    - Every run is published, failures included.
  - Relevance: the first public SO-101 leaderboard with fine-tuning numbers.
    - Choose policies on your own embodiment.
    - When reporting SO-101 results, use more trials and fixed, AprilTag-registered scenes.
    - Its remote policy-serving protocol is a template for remote evaluation in a cloud lab.

**Also verified (one line each):**
- **VLA-REPLICA** — Huang, A. S., Zhang, J., Tang, S., Xiang, Y. (2026). *arXiv:2605.20774*, 2026-05-20. **[preprint]** https://arxiv.org/abs/2605.20774 A low-cost, reproducible real-world VLA benchmark built from off-the-shelf parts, with tasks, a small adaptation set, and in- and out-of-distribution protocols. The abstract gives no numbers. A search snippet says it handles per-arm servo-offset differences between SO-101 builds.
- **Cutting the Cord** — Shaw, A., Liu, C., Costa, J., et al. (incl. N. Correll) (2026). *arXiv:2603.09051*, 2026-03-10. **[preprint]** https://arxiv.org/abs/2603.09051 A bimanual mobile manipulator built on XLeRobot with a Jetson Orin Nano, for under US$1,300. No experimental results. A low-cost way to move samples between stations.

## 5. Vision for lab manipulation beyond fiducials

### Success/failure detection and lab monitoring

Chemist Eye (VLM safety monitoring) is in §8. Gemini Robotics ER 2's success detector is in §2, and CRESt's camera + VLM monitoring is in §1.

- **Robometer** — Liang, Korkmaz, Zhang et al. (17 authors) (2026). "Robometer: Scaling General-Purpose Robotic Reward Models via Trajectory Comparisons." *RSS 2026; arXiv:2603.02115*, 2026-03-02 (v2 2026-05-13). https://arxiv.org/abs/2603.02115 (project: https://robometer.github.io/)
  - Findings (authors' claims): trained on RBM-1M (>1M trajectories, including failures). Zero-shot failure detection F1 0.81 vs RoboReward-4B 0.74 and GPT-5-mini 0.33. Progress VOC r 0.92/0.94 (ID/OOD), and 0.916 on a UT Dallas SO-101 set. Online RL (DSRL+π0) success rose from 0.20 to 0.85 with Robometer rewards. The 4B checkpoint ships in LeRobot (`lerobot/Robometer-4B`, added in v0.6.0).
  - Relevance: an off-the-shelf success/progress scorer for the lab's fixed and wrist Pi camera clips. Uses include auto-labelling episodes, filtering demos and flagging failed runs for remote users.

- **TOPReward** — Chen, Harrison, Lee et al. (9 authors) (2026). "TOPReward: Token Probabilities as Hidden Zero-Shot Rewards for Robotics." *arXiv:2602.19313*, 2026-02-22 (v2 2026-07-22). **[preprint]** https://arxiv.org/abs/2602.19313
  - Findings (authors' claims): training-free (reads the VLM's log P("True")). With Qwen3-VL-8B, mean VOC on Open X-Embodiment is 0.857 vs 0.194 for GVL. On ManiRewardBench (113 tasks), VOC on the LeRobot platform is 0.954. Success-detection ROC-AUC is 0.654 vs 0.519 for GVL on Qwen3-VL, and roughly tied with Gemini-2.5-Pro (0.826 vs 0.823). On a real SO-100 with 50 noisy demos per task, reward-weighted BC raised mean successes from about 4.8 to 6.8 out of 10 across 6 tasks.
  - Relevance: zero-training success scoring with an open 8B VLM, already shown on SO-100. It is a cheap way to weight or clean the lab's teleop data. In LeRobot since v0.6.0.

- **Guardian** — Pacaud, Garcia, Chen, Schmid (2025–2026). "Guardian: Detecting Robotic Manipulation Failures with Vision-Language Models." *WACV 2027 (accepted); arXiv:2512.01946*, 2025-12-01 (v6 2026-11-09). https://arxiv.org/abs/2512.01946
  - Findings (authors' claims): introduces the GuardianFail-36k failure-reasoning dataset and reports state of the art on three unseen real-world benchmarks (RoboFail, RoboVQA, UR5-Fail). Used as a verifier for an LLM-based manipulation policy, it "consistently boosts task success" in sim and real (no numbers in the abstract).
  - Relevance: a plan- and execution-error checker for agentic (LLM-driven) PiPER control; UR5-Fail is a real-arm failure set.

- **LIRA** — Zhou, Veeramani, Munguia-Galeano et al. (5 authors, Liverpool) (2025). "Localization, inspection, and reasoning (LIRA) module for autonomous workflows in self-driving laboratories." *Communications Chemistry* 8:384, 2025-11-28. DOI 10.1038/s42004-025-01770-1. https://pmc.ncbi.nlm.nih.gov/articles/PMC12663431/
  - Findings (authors' claims): visual ArUco localization reaches 1.02 mm / 1.01° (tactile reference 0.92 mm / 0.90°) in about 5 s vs about 53 s. A fine-tuned VLM inspects placement errors at 97.9% accuracy (42.9% zero-shot, 86.3% for a YOLOv11 classifier). It runs on a Jetson AGX Orin with about 28–45 ms image round-trips. An 8 h test completed 100 loops (600 pick/insert operations) with 100% success, and arm time fell by 34–36% per loop. Robot: KUKA KMR iiwa.
  - Relevance: the closest published template for this lab: fiducial localization plus a small fine-tuned VLM on an edge box that verifies each placement (vial seated, build plate placed).

### Transparent labware and liquid perception

ASHE (§1) is a deployed closed-loop correction system for transparent substrates.

- **Phase-interface segmentation (CTG 2.0)** — Li, Yang, Yan et al. (11 authors) (2026). "Phase-Interface Instance Segmentation as a Visual Sensor for Laboratory Process Monitoring." *arXiv:2603.10782*, 2026-03-11. **[preprint]** https://arxiv.org/abs/2603.10782
  - Findings (authors' claims): the CTG 2.0 dataset has 3,668 images, 23 glassware categories and 5 multiphase interface types. LGA-RCM-YOLO (on YOLO11m-seg) reaches 84.4% AP@0.5, +6.42 points over baseline, at 13.67 FPS on an RTX 3060. Its colored/colorless liquid head reaches 98.71% precision and 98.32% recall. Demonstrated on separatory-funnel separation and crystallization.
  - Relevance: fiducial-free liquid level and phase sensing from a fixed Pi HQ camera for OT-2 or vial workflows.

- **TransNormal / TransNormal-2** — Li, Fan, Yang (2026). "TransNormal: Dense Visual Semantics for Diffusion-based Transparent Object Normal Estimation." *arXiv:2602.00839*, 2026-01-31; ICML 2026 poster (record via icml.cc listing). Follow-up: "TransNormal-2: Geometry-Grounded Rectified Flow with Edge-Aware Decoding for Precise Normal Estimation," *arXiv:2609.06665*, 2026-09-06 **[preprint]**. https://arxiv.org/abs/2602.00839 ; https://arxiv.org/abs/2609.06665
  - Findings (authors' claims): TransNormal cuts mean error by 24.4% and raises 11.25° accuracy by 22.8% on ClearGrasp, and cuts mean error by 15.2% on ClearPose. It adds TransNormal-Synthetic (rendered beakers, pipettes, culture dishes). TransNormal-2 cuts MAE by a further 4.2° (ClearGrasp) and 3.1° (ClearPose) vs the strongest baselines, using 1.4% of MoGe-2's task-specific annotations. Neither reports robot experiments.
  - Relevance: monocular (RGB-only) glassware geometry, which suits the lab's Pi HQ cameras with no depth sensor. Grasp-level validation on lab glassware is still missing.

### Camera calibration for low-cost arms

- **AnchorHEC** — Hwang, Lee, Lee et al. (5 authors) (2026). "AnchorHEC: Targetless Hand-Eye Calibration of Wrist and Fixed Cameras." *arXiv:2611.02884*, 2026-11-02. **[preprint]** https://arxiv.org/abs/2611.02884
  - Findings (authors' claims): calibrates wrist and fixed cameras together from RGB images, forward kinematics and known intrinsics, using a shared foundation-model 3D reconstruction with no targets. In sim it cuts error by 86.4% (translation) and 71.6% (rotation) vs reconstruction-based baselines, averaged over 3 backbones, and is validated on a physical robot. No absolute errors or marker-based comparison are given.
  - Relevance: matches the lab's rig exactly (Pi wrist camera plus fixed Pi cameras on PiPER/SO-101). It could replace AprilTag-board recalibration after bumps, but compare it against the existing fiducial calibration first.

- **SyncHeC** — Hong (2026). "SyncHeC: Markerless Spatio-Temporal Hand-Eye Calibration via Differentiable Rendering and Continuous-Time Joint Optimization." *arXiv:2611.02999*, 2026-11-02. **[preprint]** https://arxiv.org/abs/2611.02999
  - Findings (authors' claims): calibrates from one 6.5 s trajectory (RGB-D plus link meshes). Translation error is 0.21 cm vs a marker board (0.34 cm touch test), and the camera-latency estimate is within 2.7 ms of an 87 ms reference. That is 3.7x better translation than CM-Calib. Compensating the latency raised policy success by 8.1 pp across 6 policy families and 6 tasks (1,800 matched pairs, 95% CI 6.3–9.9).
  - Relevance: Pi cameras over USB/CSI/network add tens of ms of latency. Measuring and compensating it is a cheap policy gain even if the lab keeps AprilTags for spatial calibration.

### Digital twins and sim-to-real

Lab-specific twins: Pipette (§2) and Self-Building Labs (§3). SO-101 Bench (§4) is an Isaac Lab twin of an SO-101 cell.

- **RoboTwin 2.0** — Chen, Chen, Chen et al. (28 authors) (2025). "RoboTwin 2.0: A Scalable Data Generator and Benchmark with Strong Domain Randomization for Robust Bimanual Robotic Manipulation." *arXiv:2506.18088*, 2025-06-22; ICML 2026 per the repo README. https://arxiv.org/abs/2506.18088
  - Findings (authors' claims): 731 objects in 147 categories, 50 dual-arm tasks, 5 embodiments; the default `aloha-agilex` embodiment has PiPER assets (README) and there are 100,000+ pre-collected trajectories. Synthetic data plus 10 real demos gives a +367% relative improvement over the 10-demo baseline, and zero-shot synthetic-only training gives +228%. A LeRobot sim env since v0.6.0.
  - Relevance: the most mature sim with PiPER arm assets and domain randomization, usable for pretraining or evaluating PiPER policies before real trials.

- **Isaac Lab 3.0 + Newton** — NVIDIA; Newton project (Linux Foundation; NVIDIA, Google DeepMind, Disney Research) (2025–2026). Isaac Lab paper: Mittal et al., "Isaac Lab: A GPU-Accelerated Simulation Framework for Multi-Modal Robot Learning," *arXiv:2511.04831*, 2025-11-06 (record via arXiv and NVIDIA Research listings). Isaac Lab v3.0.0 released 2026-10-20; Newton v1.0.0 2026-04-13 → v1.8.0 2026-11-11; MuJoCo Warp v4.0.0 2026-11-06 (GitHub releases). https://github.com/isaac-sim/IsaacLab/releases/tag/v3.0.0 ; https://github.com/newton-physics/newton/releases
  - Findings (release notes): Isaac Lab 3.0 runs one task API across backends. Its Warp-native Newton backend offers MuJoCo-Warp, VBD (cables and deformables) and **MPM (liquid pouring, particles)** solvers, and Isaac Sim becomes optional ("kit-less"). It targets Python 3.12, PyTorch 2.11/CUDA 13 and Newton 1.6.1.
  - Relevance: MPM liquids and granular media in a pip/uv-installable stack make digital twins of powder scooping (powder doser) and pouring more practical than in 2025. It still needs an NVIDIA GPU.

**Also verified (one line each):**
- **RoboLab (NVIDIA)** — Yang, et al. (8 authors) (2026). *RSS 2026; arXiv:2604.09860*, 2026-04-10. https://arxiv.org/abs/2604.09860 RoboLab-120: 120 Isaac Lab tasks on a DROID Franka, spanning visual, procedural and relational variation. It is in LeRobot v0.7.0 (about 7 GB VRAM per environment). AMP1 reports 85.6% on it, against 49.2% for the best VLA (§3).
- **Trans2Occ** — Yang, et al. (15 authors) (2026). *arXiv:2606.01777*, 2026-06-01. **[preprint]** https://arxiv.org/abs/2606.01777 Predicts voxel occupancy of transparent objects from a single image, then grasps with a rule-based method, in simulation and on real robots. The abstract gives no numbers. An RGB-only route to glassware; check the full paper's numbers before relying on it.

## 6. Robotic 3D-printer tending and closed-loop design–print–test

TeleopLab (§8) had remote students run tensile tests on 3D-printed specimens through a teleoperated arm.

- **Prusa Pro AFS (commercial)** — Prusa Research (2026). "Prusa Pro AFS" (Automated Farm System), official product page. *Commercial product page*; US debut at RAPID + TCT, 2026-04 (per All3DP); Prusa/ORNL webinar scheduled 2026-12-07. https://www.prusa3d.com/en/applications/prusa-pro-afs_236928/
  - Findings (vendor claims): one cell = 9 CoreXY printers (260×260×175 mm), a robotic "harvester" arm that removes finished prints to storage and puts a clean spring-steel sheet back on the printer, 120 storage slots in the basic configuration, Prusa Connect Farm scheduling. ORNL used an AFS to print parts for three drone sizes for an IMTS demo (webinar page). No throughput or uptime figures are published.
  - Relevance: the closest off-the-shelf analogue to a PiPER tending the Bambu printers; it supports swapping whole magnetic sheets rather than prying parts off, which suits a 1.5 kg-payload arm.

- **BU KABlab: from self-driving to community-driven lab** — Boston University Hariri Institute for Computing (2025). "Reimagining the Future of Materials Discovery: From Automation to Collaboration." *BU institutional news*, 2025-10-14. https://www.bu.edu/hic/2025/10/14/reimagining-the-future-of-materials-discovery-from-automation-to-collaboration/
  - Findings (authors' claims): MAMA BEAR (FFF printers, cobot, Instron) has run >25,000 experiments since 2023 (record 75.2% energy-absorbing efficiency). Cornell's Frazier group, testing new Bayesian-optimisation algorithms on BU's SDL, doubled the benchmark from 26 J/g to 55 J/g (the page cites no paper). Pilots include infrastructure for external users, a public interface to design and submit experiments, and a RAG LLM agent over the SDL datasets. The dataset had 89 downloads by June 2025.
  - Relevance: a direct template for opening BYU's printed-tensegrity design-print-test loop to remote users (cloud-lab model) with an LLM front end. This is a follow-up to Snapp et al. 2024 (Nat Commun).

- **IMDEA cobot specimen monitoring** — Stack, B., Hernández-del-Valle, M., Mascaraque-León, A., et al. (2025). "Streamlining material degradation testing: collaborative robotics for specimen monitoring." *Digital Discovery* 4(8):2001–2011, 2025 (ChemRxiv preprint 10.26434/chemrxiv-2024-54xvd, v2 2025-01-15). https://doi.org/10.1039/D5DD00016E
  - Findings (authors' claims): a UR10e moves specimens between a water bath, an air-drying station, a balance and a Charpy pendulum, using DIY add-ons (Arduino water exchange and a 3D-printed gripper that blows compressed air). Specimens were extracted, dried and weighed every 3 h over 5 days. The PLA Charpy campaign used 150 specimens, and PA12 absorbed ≤1.2% water.
  - Relevance: one arm plus printed fixtures ran a multi-day mass-and-mechanics campaign unattended. The PiPER could run the same loop on printed tensegrity struts and nodes.

- **AM-ARES multi-objective BO** — Myung, J. I., Deneault, J. R., Chang, J., et al. (2025). "Multi-objective Bayesian optimization: a case study in material extrusion." *Digital Discovery* 4(2):464–476, 2025. https://doi.org/10.1039/D4DD00281D
  - Findings (authors' claims): on AFRL's AM-ARES (an FDM printer with a syringe extruder and dual-camera vision), multi-objective BO tuned 6 print parameters and reached accurate target prints faster than simulated annealing or random sampling.
  - Relevance: closed-loop print optimisation scored by cameras, which maps onto a Bambu printer plus Pi HQ camera without needing an arm for the inner loop.

- **LLM-3D Print** — Jadhav, Y., Pak, P., Barati Farimani, A. (2025). "LLM-3D Print: Large Language Models To Monitor and Control 3D Printing." *Additive Manufacturing* 114:105027, 2025-09 (arXiv:2408.14307, v1 2024-08-26). https://doi.org/10.1016/j.addma.2025.105027
  - Findings (authors' claims): LLM agents read per-layer images from a Klipper-controlled consumer printer, diagnose inconsistent extrusion, stringing, warping and poor layer adhesion, query printer state, and apply corrective parameter changes without human intervention. It was deployed on two printers with different sensors and compared against a control group of engineers. The abstract gives no metrics.
  - Relevance: the monitoring half of an arm + Bambu cell (Pi camera + VLM). Bambu's cloud-bound firmware refuses unsigned LAN commands (see CLAUDE.md), so in-print correction there would be limited, unlike Klipper.

- **Agentic SLS print-test loop** — Pak, P., Alvarado, V., Barati Farimani, A. (2026). "AI Agentic Selective Laser Sintering Process Optimization." *arXiv:2608.25928*, 2026-08-26. **[preprint]** https://arxiv.org/abs/2608.25928
  - Findings (authors' claims): a coding-agent setup (the paper names a Claude model, "Claude Fable", run through agent harnesses) tuned SLS parameters on an Inova Mk1. PA11 Onyx reached 1571 MPa modulus (~94% of the 1680 MPa datasheet value) but 36.3 MPa strength (~66% of 55 MPa) in 4 builds, and a PA12 blend took 3 builds, against 15 hand-tuned batches for PA12 GF. Powder-cake removal, sifting and Instron 4469 testing are described as manual.
  - Relevance: agentic print-test loops converge in a handful of builds, but specimen handling stays the human bottleneck. That is the step an arm should own.

**Also verified (one line each):**
- **Hacking 3D printers as laboratory robots** — Baas, S., Carson, N., Saggiomo, V. (2026). *Digital Discovery* 5(4):1460–1469, DOI 10.1039/D5DD00451A. https://doi.org/10.1039/D5DD00451A A review of three routes: modified extruders, printers with the extruder swapped for a tool (pipette, microscope), and printers stripped into robot kits. No aggregate numbers. Cheap gantries can take repetitive XY work and leave the PiPER to move items between stations.

## 7. Robotic sample handling in metals, alloy and powder workflows

- **CMU Materials Innovation Cloud Lab (MICL)** — Carnegie Mellon University College of Engineering (2026). "Automated lab to accelerate materials discovery." *CMU news*, 2026-08-07 (date from URL). https://engineering.cmu.edu/news-events/news/2026/08/07-accelerate-materials-discovery.html
  - Findings (authors' claims): MICL (part of CMU's AI Science Foundry at Mill 19, and a node in NSF's Programmable Cloud Laboratory Testbed) is moving toward self-driving operation. Its initial aim is to automate production of aluminium-alloy powder for aerospace on an AMAZEMET rePOWDER (ultrasonic atomisation, as-cast or powder, re-atomisation), with instruments for powder size, morphology, composition, printability and yield. Co-directors are B. Webler (automation) and M. Taheri-Mousavi (AI and Al-alloy design). No dates or throughput are given.
  - Relevance: the closest peer programme to BYU's Al-alloy LPBF SDL (same atomiser class, same alloy family, cloud-lab framing), so both a competitor and a natural benchmark or collaborator.

- **Texas A&M ARM-MIP (national metals SDL)** — Texas A&M University (2026). "Texas A&M to build self-driving laboratory for metals, open to researchers nationwide." *TAMU news*, 2026-08-05. https://stories.tamu.edu/news/2026/08/05/texas-am-to-build-self-driving-laboratory-for-metals-open-to-researchers-nationwide/
  - Findings (authors' claims): an NSF Materials Innovation Platform, $24.9M over 6 years (director R. Arróyave, co-director I. Karaman). Robots will "melt, shape, heat-treat and test alloys around the clock". Targets are 50 alloys/month in year 1, rising to >200/month by year 6, and >200 users/yr. Use is free for US academics, including remotely by shipping samples or submitting a question. The predecessor programme, BIRDSHOT, made >1,150 alloys by hand in 4 years and claims a 100-fold acceleration.
  - Relevance: sets the national bar for alloy SDLs, is a possible external partner for characterisation, and its remote-user model matches BYU's cloud-lab model.
  - Also, per the topic-8 sub-scan, TAMU Engineering news (2026-08-03) gives the NSF award as DMR-2534344 and says data will be released, failed experiments included: https://news.engineering.tamu.edu/news/2026/08/03/texas-am-to-build-first-national-self-driving-laboratory-for-metals-open-to-researchers-nationwide/

- **AlloyBot (automatic arc-melting)** — Selvaraj, V., Boonpetch, P., Dutta, A., Pek, M. E., Kube, S. A. (2026). "AlloyBot: On-Demand Synthesis of Bulk Alloys by Automatic Arc-Melting." *Research Square preprint rs-9761885/v1*, 2026 (SI dated 2026-05). **[preprint]** https://www.researchsquare.com/article/rs-9761885/v1 (record via the preprint's SI PDF and UW–Madison research page of 2026-07-27; main abstract page did not render)
  - Findings (authors' claims, from SI): a mobile robot puts a copper crucible at a weighing station, dispenses element pellets or wire into a cup on a balance, pours them into the crucible and drives it to the arc melter's load-lock. An internal transfer mechanism seats it in the hearth, and a scoop flips the button between remelts. Example buttons are Ti-6Al-4V (~11.4 g), Ti20Zr20Hf20Nb20Ta20 and Zr55Cu30Ni5Al10. Feedstock cost (e.g., Al pellets $19 per 5 cm³) and impurity budgets (e.g., ~220–673 ppmw O in Ti-6Al-4V) are tabulated. The UW page frames it as a tungsten-alloy fusion SDL aiming for ">100× faster" testing.
  - Relevance: shows that pellet weighing and crucible loading by a mobile arm works at lab scale. The same pick-weigh-pour-load pattern applies to the powder doser and to charging the atomiser.

- **NIMS ROS2 arc-melting cell (journal version)** — Wang, W.-S., Terashima, K., Takano, Y. (2026). "Orchestration of heterogeneous experimental machines via ROS2 for automated bulk intermetallic synthesis." *Science and Technology of Advanced Materials: Methods* 6(1):2611510, 2026-02-02 (arXiv:2509.12011, 2025-09-15). https://doi.org/10.1080/27660400.2025.2611510
  - Findings (authors' claims): a Denso COBOTTA on a 1-axis slider moves Mettler-Toledo Quantos dosing heads (rack of up to 20) and a copper carrier between storage, balance and a 2-axis slider into a custom arc chamber. Argon purge (4 cycles) takes <3.5 min, with a motorised flipper and a USB camera. Three automated V3Ge syntheses gave matching XRD and Tc ≈ 6 K, and asynchronous ROS2 scheduling beat sequential control from binary to quaternary syntheses. The authors advise ~1 mm chunks, because fine powders splash or clog the dosing head.
  - Relevance: if this is the "NIMS COBOTTA" item from the earlier scan, the new part is the February 2026 journal version. The powder-clogging caveat matters for dosing fine Al powder.

- **LLNL APEX (alloy SDL) and Project ARMOR** — Lawrence Livermore National Laboratory (2025; update 2026). "Self-driving lab to automate the discovery of novel alloys." *LLNL news*, 2025-07-21; 2026 status in "LLNL harnesses AI, robotics to boost manufacturing" (LLNL article reprinted by Mirage News, 2026-07-29). https://www.llnl.gov/article/53131/self-driving-lab-automate-discovery-novel-alloys ; https://www.miragenews.com/llnl-harnesses-ai-robotics-to-boost-1717674/
  - Findings (authors' claims): APEX (with Cornell) prints samples by laser DED, then grinds and polishes them robotically (a vibration sensor turns the operator's "feel" into data), images them, indents for hardness and compression-tests them. Hand preparation takes 2–3 days per sample, against a target of dozens per day. Stainless steel is the control, and completion is expected in 2027. The 2026 article says instruments had to be retrofitted, and that the sister project ARMOR (led by A. Gongora) targets robots that adapt when samples shift.
  - Relevance: confirms metallographic preparation is the bottleneck worth automating, and sensorised grinding is a concrete idea for an arm holding a specimen on an auto-polisher.

- **AIMD-L (JHU high-throughput structural-materials lab)** — Hufnagel, T. C., Addepalli, P., Bhattacharjee, A., et al. (2026). "AIMD-L: An automated laboratory for high-throughput characterization of structural materials for extreme environments." *arXiv:2603.06835*, 2026-03-06. **[preprint]** https://arxiv.org/abs/2603.06835
  - Findings (authors' claims): six UR10e cobots (vacuum grippers, barcode readers), a UR3e and a puck conveyor (225 holders) serve three stations. HELIX does laser-driven shock tests ("thousands of tests per day", ~1000× throughput and lower cost per test), MAXIMA does XRD/XRF (usable patterns in as little as 1 s), and SPHINX does nanoindentation. Samples are standard 40×40 mm foils. Polishing for HELIX and SPHINX is still manual, so closed-loop optimisation is not yet possible.
  - Relevance: a reference design (standard holder, barcodes, conveyor, one cobot per station) that scales down to a PiPER cell with AprilTags. It also shows surface preparation is still manual even at a flagship lab.

- **A-Lab GPSS (glovebox A-Lab with agentic planner)** — Fei, Y., Rendy, B., Yang, X., et al. (2026). "Agentic LLM Reasoning in a Self-Driving Laboratory for Air-Sensitive Lithium Halide Spinel Conductors." *arXiv:2604.11957*, 2026-04-13. **[preprint]** https://arxiv.org/abs/2604.11957
  - Findings (authors' claims): an air-free A-Lab variant with an LLM planner that uses abductive reasoning (anomalies in explored regions) and inductive reasoning (new chemical space). It made 352 samples and realised 72% of 171 pairwise combinations of 19 metals. The share of samples with >0.05 mS/cm conductivity and high spinel purity rose from 1.33% (first 75) to 5.33% (last 75).
  - Relevance: an A-Lab follow-up that moves crucible and furnace robotics into inert atmosphere, which is relevant if reactive Al powders are handled under argon.

- **ALPHA-AM (active learning + laser DED alloy discovery)** — Talbot, A., Dash, S. S., Li, J., et al. (2026). "Active learning for the accelerated discovery of complex concentrated NiCoCr alloys in additive manufacturing." *npj Advanced Manufacturing* 3:36, 2026-06-23. https://doi.org/10.1038/s44334-026-00098-5 (metadata and abstract via OpenAlex; publisher page redirected to login)
  - Findings (authors' claims): six new printable NiCoCr alloys, up to ~40% harder than equiatomic NiCoCr at room temperature. Ni12Co62Cr26 keeps ~50% higher hardness at 600 °C, and Ni36Co14Cr50 cuts oxidation mass gain by 85% at 1000 °C versus conventional superalloys. Lab Manager's coverage adds 27 seed alloys, 6 active-learning rounds and 90 laser-power/speed/feed combinations, and U of T news calls it "robot-assisted manufacturing".
  - Relevance: the nearest published closed-loop alloy-for-AM campaign. Its staging (printability first, then properties) carries over directly to Al-alloy LPBF.

- **AMAZEMET rePOWDER AI process control (commercial)** — AMAZEMET (2025). "AI-Driven Process Automation" for rePOWDER, official Formnext 2025 page. *Commercial product page*, 2025-11 (Formnext 18–21 Nov 2025). https://www.amazemet.com/formnext2025
  - Findings (vendor claims): a proprietary "Ai-Vision" model watches the material on the sonotrode, the feed rate and atomisation in real time. New hardware is an Intelligent Torch, a Smart Wire Feeder and an Advanced Control Cabinet, and one operator can supervise several machines. Trade press (Metal AM / 3D Printing Industry, read via search because the pages returned 403) adds: welding-camera frames evaluated in 120 ms cycles, up to 0.5 kg/h, and ≥4 h unattended on Ti-6Al-4V wire (8 h planned).
  - Relevance: CMU's MICL uses this atomiser class. If BYU's atomiser is (or becomes) a rePOWDER, this upgrade plus an arm handling crucibles, wire and powder jars would make atomisation an SDL step.

- **SCU-Hand (powder scoop-and-dispense end-effector)** — Takahashi, T., Nakajima, Y., Beltran-Hernandez, C. C., et al. (2025). "SCU-Hand with Integrated Single-Sheet Valve: A Funnel-Shaped Robotic Hand for Milligram-Scale Powder Handling." *arXiv:2512.07091*, v1 2025-12-08, v2 2026-05-13. **[preprint]** https://arxiv.org/abs/2512.07091
  - Findings (authors' claims): one funnel hand both scoops and dispenses, with balance feedback. 80% of trials landed within ±2 mg, with a maximum error of ~20 mg across 20 mg–3 g targets, on glass beads, MSG and TiO2.
  - Relevance: a printable end-effector concept for the PiPER or SO-101 to feed the powder doser or weigh alloy powder blends without a dedicated dosing head.

- **EMSBot (printer-derived SEM/TEM powder prep)** — Milsted, D., Mishra, T. P., Walters, L. N., et al. (2025). "Automated electron microscopy sample preparation system." *Digital Discovery* 4(8):2244–2252, 2025. https://doi.org/10.1039/D5DD00116A
  - Findings (authors' claims): a solvent-free, modular device built on a modified Creality Ender-3 Pro that uses induced static charge to deposit powder on SEM stubs or TEM grids. The authors report more consistent, higher-quality dispersions than manual drop-casting, and size-selective deposition by tuning conditions. The abstract gives no aggregate numbers.
  - Relevance: a desktop printer turned into an SEM-prep station for atomised Al powder morphology, with the arm feeding it. This is from the A-Lab group.

- **AutoRASOR (autonomous SEM operator)** — Zhang, K., Taha, M., Espinosa Castañeda, R., et al. (2026). "AutoRASOR: Autonomous Rapid Scanning Electron Microscope Operator." *arXiv:2609.22411*, 2026-09-18. **[preprint]** https://arxiv.org/abs/2609.22411
  - Findings (authors' claims): DINOv3 embeddings with latent farthest-point sampling or active learning choose SEM regions of interest, and stage, autofocus and autostigmation are scripted on a Hitachi SU7000. On the synthetic benchmark, random sampling needed ~1.7× more images to match the same morphological coverage. The demo used 78 micrographs, and the code is on GitHub (zzy-kevin/AutoRASOR).
  - Relevance: drop-in autonomy for SEM imaging of powder and microstructure in the Al-alloy loop once samples are loaded, by hand or by arm.

- **Image-based flowability of AM metal powder** — Katagiri, J., Kusano, M., Watanabe, M. (2026). "Statistical Variability of Image-Derived Observables in Rotating-Drum Tests of a Cohesive Metal Powder: Dynamic Angle of Repose Versus Contour-Length Statistics." *Powders* 5(3):27, 2026-07-21. https://doi.org/10.3390/powders5030027
  - Findings (authors' claims): on gas-atomised Hastelloy X (29 µm mean), the dynamic angle of repose had a mean CV of 0.137 (range 0.095–0.186) and needed 21, 84 and 189 image cases for 3% error at 1σ, 2σ and 3σ. A contour-length index had CV ≈ 0.014 and needed only 1–2 cases.
  - Relevance: gives frame counts for an automated, Pi-camera flowability check of atomised Al powder, and points to a better image metric than angle of repose.

- **Autonomous LPBF processing maps** — Masinelli, G., Schlenger, L., Wasmer, K., et al. (2025). "Autonomous exploration of the PBF-LB parameter space: An uncertainty-driven algorithm for automated processing map generation." *Additive Manufacturing* 101:104677, 2025-02. https://doi.org/10.1016/j.addma.2025.104677 (metadata and abstract via Semantic Scholar/OpenAlex)
  - Findings (authors' claims): an unsupervised classifier of melting regime from photodiode data reaches F1 = 89.2% on Ti-6Al-4V and 316L. Uncertainty-driven sampling cuts experiments by up to 67% versus full factorial, with ≤8.88% performance loss.
  - Relevance: the in-situ-monitoring half of an autonomous LPBF loop for Al alloys. The other half, arm handling of plates and coupons, has no published academic demonstration.

**Also verified (one line each):**
- **Toward an Autonomous Laboratory for Accelerated Alloy Discovery** — Wanni, J. C., Mishra, A., Fensin, S. (2026). *TMS 2027 Annual Meeting, accepted abstract.* **[conference abstract]** https://www.programmaster.org/PM/PM.nsf/ApprovedAbstracts/518D395457B0BD7585258E27000EECD3 Claims a coordinated robotic chain covering arc melting, machining, heat treatment, metallographic prep, microscopy and mechanical testing, with AI agents and machine-vision anomaly flags. No throughput figures. Watch for the full paper.
- **RoboMet-3D (Fraunhofer IWS interview)** — Fraunhofer IWS (2025). "Serial sectioning provides insight into materials." 2025-01-15. https://www.iws.fraunhofer.de/en/newsandmedia/news/2025-02_news_serial-sectioning.html Robot-arm metallography (grinding, polishing, etching, light-microscope imaging) that runs unattended for a working day. A typical 3D study needs about 100 sections. It is not plug-and-play, and about 20 units exist worldwide.

## 8. Cloud labs, remote and teleoperated lab robotics, safety and standards

Texas A&M ARM-MIP, a remote metals user facility, is in §7. LabSafety Bench and LABSHIELD are in §2.

- **NSF Programmable Cloud Laboratories (PCL) Test Bed** — U.S. National Science Foundation (2026). "NSF announces $400M investment in new national network of AI-programmable cloud laboratories" (PCL Test Bed, NSF 25-541). NSF TIP news, 2026-07-22 (updated 2026-09-25). https://www.nsf.gov/tip/updates/nsf-announces-400m-investment-new-national-network-ai
  - Findings (authors' claims):
    - Funding: an initial $380M to 20 teams over four years, plus up to $20M from the Astera Institute.
    - Scope: nodes cover biology and biotech, chemistry, soft and 2D materials, **metals**, materials characterization and electronics. They are remotely accessible and run user-programmed AI workflows.
    - NSF frames the program as part of the Genesis Mission's "AI-Driven Autonomous Laboratories" challenge.
    - Example nodes: BU **CLAIRE**, about $20M (Densmore, Paschalidis, K. A. Brown), https://www.bu.edu/hic/2026/07/23/nsf-awards-boston-university-nearly-20-million-to-advance-national-cloud-lab-network/ ; Utah **AURORA**, $20M (T. Sparks), robotic exfoliation and stacking of 2D materials, "accessible from a laptop", https://science.utah.edu/?p=60476.
  - Relevance: The main 2026 funding vehicle for cloud labs. Its metals and characterization nodes are possible partners for the Al-alloy work, and the Utah node is regional.

- **CMU AI Science Foundry (PCL node)** — Carnegie Mellon University (2026). "Carnegie Mellon's AI Science Foundry selected by NSF to help build national infrastructure for AI." CMU News, 2026-07-22. https://www.cmu.edu/news/stories/archives/2026/july/carnegie-mellons-ai-science-foundry-selected-by-nsf-to-help-build-national-infrastructure-for-ai
  - Findings (authors' claims): Up to $20M over 4 years. More than 80 robotically controlled instruments across two cloud labs are unified on one platform. Initial focus areas include **high-temperature aluminum alloys** for aircraft engines, plus polymers, biomaterials and organoids. Researchers design, run and analyze experiments remotely.
  - Relevance: A remotely programmable node with an Al-alloy focus, the closest cloud-lab match to this lab's Al-alloy SDL.

- **DOE Genesis Mission (autonomous-lab challenge and awards)** — U.S. Department of Energy (2026). "Energy Department announces 26 Genesis Mission science and technology challenges," 2026-02-12; "Secretary of Energy Chris Wright announces first Genesis Mission projects selected," 2026-07-22. https://www.energy.gov/articles/energy-department-announces-26-genesis-mission-science-and-technology-challenges ; https://www.energy.gov/articles/secretary-energy-chris-wright-announces-first-genesis-mission-projects-selected-accelerate
  - Findings (authors' claims):
    - The challenges include "Achieving AI-Driven Autonomous Laboratories".
    - Phase I selected 278 awards: 87 led by DOE/NNSA labs, 168 by universities, 19 by companies and 4 by nonprofits.
    - PNNL co-leads OPAL, a four-lab autonomous-lab network (PNNL release, 2026-02-17).
    - One funded project, CMU (NREC) with Argonne and LLNL: AI agents write the robot instructions, test workflows in a digital twin of each lab, and share reusable robot skills across sites (CMU News, 2026-07-22, https://www.cmu.edu/news/stories/archives/2026/july/connecting-autonomous-laboratories-to-speed-scientific-advancement).
  - Relevance: The funded direction is agent-written robot code, digital twins and shareable skills. Proposals from this lab could align with the autonomous-labs challenge.

- **Ginkgo Cloud Lab and academic autonomous-lab nodes** — Ginkgo Bioworks (2026). "Ginkgo Bioworks Launches Ginkgo Cloud Lab, Powered by Autonomous Lab Infrastructure," PR Newswire, 2026-03-02; "Ginkgo Bioworks Expands Autonomous Lab Network to Caltech, MIT, Maryland and Northwestern," 2026-08-04. https://www.prnewswire.com/news-releases/ginkgo-bioworks-launches-ginkgo-cloud-lab-powered-by-autonomous-lab-infrastructure-302700458.html ; https://investors.ginkgobioworks.com/news/news-details/2026/Ginkgo-Bioworks-Expands-Autonomous-Lab-Network-to-Caltech-MIT-Maryland-and-Northwestern-2026-44Q8f7PNjN/default.aspx
  - Findings (authors' claims):
    - March launch: browser access to more than 70 instruments on Reconfigurable Automation Carts, which "combine high-precision robotic arms, maglev sample transport tracks". An LLM agent, "EstiMate", returns protocol feasibility and a price.
    - Pricing: third-party skill docs list $39 per sample for cell-free expression. Treat this as indicative only.
    - August: four academic nodes are planned, not yet installed: about 11 carts at Maryland and 5 at Northwestern. Three nodes come under the NSF PCL Test Bed. The MIT Media Lab node is a cloud lab for biotech, AI and robotics education.
  - Relevance: The first commercial pay-per-run autonomous cloud lab, a benchmark for pricing and user experience in this lab's remote-user model.

- **GPT-5-driven autonomous lab (OpenAI × Ginkgo)** — OpenAI and Ginkgo Bioworks (2026). "GPT-5 lowers protein synthesis cost" (blog), with the preprint "Using a GPT-5-driven autonomous lab to optimize the cost and titer of cell-free protein synthesis." 2026-02-05. **[preprint]** https://openai.com/index/gpt-5-lowers-protein-synthesis-cost
  - Findings (authors' claims): More than 36,000 reaction compositions on 580 automated plates over 6 closed-loop rounds; 3 rounds were enough for state of the art. Protein production cost fell 40% and reagent cost 57%. People still prepared reagents, loaded and unloaded, and fixed protocols. Results are for one protein (sfGFP) and one CFPS system.
  - Relevance: A benchmark for LLM-directed experiments through a cloud lab. The handling steps people still did are ones arms could take over.

- **TeleopLab** — Chen, Z., Yoon, Y. J., Bautista-Montesano, R., et al. (incl. A. Mandlekar, J. Liu) (2025). "TeleopLab: Accessible and Intuitive Teleoperation of a Robotic Manipulator for Remote Labs." *arXiv:2509.05547*, 2025-09-06. **[preprint]** https://arxiv.org/abs/2509.05547
  - Findings (authors' claims):
    - Setup: a smartphone motion interface plus a video call; ABB IRB-120 and UR5e arms, with a wrist RealSense D405 and a webcam.
    - Task: students ran **tensile tests of 3D-printed specimens** on a Mark-10 tester (load, test, reset).
    - Results: six students over 3 weeks (14 person-hours); task time fell 46.1% with familiarity; NASA-TLX 38.2; SUS 73.8.
    - Latency: motion latency fell from 500 ms to 10 ms; internet delay was not measured.
  - Relevance: Nearly this lab's own use case (remote students, printed specimens, mechanical testing). With n = 6 and industrial arms, a PiPER or SO-101 version is an open gap. Also relevant to §6.

- **ISO 10218-1/-2:2025 and ANSI/A3 R15.06-2025 (with a 2026 comparative analysis)** — ISO (2025) "Robotics — Safety requirements," Parts 1–2; A3 (2025) ANSI/A3 R15.06-2025, announced 2025-09-10. Hartmann, D., Hamříková, K., Vysocký, A., et al. (2026). "Evolution of Safety Requirements in Industrial Robotics: Comparative Analysis of ISO 10218-1/2 (2011 vs. 2025) and Integration of ISO/TS 15066." *arXiv:2602.17822*, 2026-02-19 (journal version DOI 10.1016/j.rineng.2026.110486, per the arXiv page). https://arxiv.org/abs/2602.17822 ; https://www.automate.org/robotics/news/new-ansi-a3-r15-06-2025-american-national-standard-for-industrial-robot-safety-now-available-for-purchase
  - Findings (authors' claims): The 2025 edition folds ISO/TS 15066 into the standard and replaces "collaborative robot" with "collaborative application". It adds robot classes with functional-safety requirements and cybersecurity requirements, including protection against unauthorized access to networked robots. R15.06-2025 is the U.S. adoption and replaces R15.06-2012.
  - Relevance: A networked, remotely operated PiPER cell now meets explicit cybersecurity expectations. The risk assessment covers the application, not the arm as a "cobot".

- **ISO 25785-1 (legged and balancing industrial mobile robots, humanoids included)** — ISO/CD 25785-1 (in development). "Robotics — Safety requirements for industrial mobile robots with actively controlled stability (legged, wheeled, or other forms of locomotion) — Part 1: Robots." The parallel CEN project prEN ISO 25785-1 (CEN/TC 310) started 2026-01-09. https://www.din.de/en/getting-involved/standards-committees/nam/projects/wdc-proj:din21:399126717 (the ISO page https://www.iso.org/standard/91469.html returned 403; the committee-draft stage comes from the ISO listing in search results)
  - Findings (authors' claims): Covers quadrupeds, bipeds and wheeled balancing robots in industrial settings. Part 2 on integration will follow. No publication date has been set.
  - Relevance: Would govern any humanoid or legged platform the lab adopts. Until it is published, there is no product safety standard for such platforms.

- **Chemist Eye** — Munguia-Galeano, F., Zhou, Z., Veeramani, S., et al. (… A. I. Cooper) (2025/2026). "Chemist Eye: A Visual Language Model-Powered System for Safety Monitoring and Robot Decision-Making in Self-Driving Laboratories." *arXiv:2508.05148* (2025-08-07); *Digital Discovery* 2026, first published 2026-04-15, DOI 10.1039/D6DD00062B. https://arxiv.org/abs/2508.05148
  - Findings (authors' claims): Monitoring stations with RGB-D and IR cameras run under ROS. A VLM checks PPE, accidents and fire, reroutes mobile robots and sends alerts; it was tested with 3 mobile robots. Hazard spotting is 97% in the arXiv abstract but 88% in the journal abstract (per the search listing). Decision-making is 95%.
  - Relevance: A template for a Pi-camera safety watcher that can also stop or redirect the arm in a remotely operated cell.

**Also verified (one line each):**
- **Georgia Tech–Duke PCL node** — Duke Pratt School of Engineering (2026). "Duke Materials Database to Power New AI-Driven Cloud Laboratory." 2026-08-03. https://pratt.duke.edu/news/materials-database-cloud-laboratory/ $18.1M from NSF. Pairs Georgia Tech's Advanced Manufacturing Pilot Facility with Duke's AFLOW database for "rapid optimization of ceramics and metallic alloys", with experiments directed remotely.
- **Safe-SDL** — Zhang, Z., Que, H., Chang, J., et al. (2026). *arXiv:2602.15061*, 2026-02-13, [preprint], https://arxiv.org/abs/2602.15061. Proposes operational design domains, control barrier functions and a transactional safety protocol (CRUTD) for SDLs; no quantitative results.
- **NIST equipment best-practice workshop** — "Towards a Best Practice Guide for Designing Equipment for Autonomous Materials R&D," 2026-08-11 to 2026-08-12, https://www.nist.gov/news-events/events/2026/08/towards-best-practice-guide-designing-equipment-autonomous-materials-rd. Planned outputs: a living guide, a consensus vocabulary, defined "levels of hardware interaction" and a review of interface standards. No guide has been published yet.
- **S-TORCH (University of York)** — https://www.york.ac.uk/safe-autonomy/research/cross-cutting/safe-tele-operated-robotic-chemistry/. VR digital twin plus haptic teleoperation of a dual-arm chemistry robot from another building; proof-of-concept stage, no results published.

## What changed since September 2026

This covers items dated Sept–Nov 2026, plus mid-2026 items the earlier scans did not pick up.

1. **Coding agents overtook VLAs on standard manipulation benchmarks, at a cost in speed.**
   - Apple's AMP1 (2026-11-06) scored 85.6% zero-shot on RoboLab-120, against 49.2% for the best VLA. On real hardware it went 104/108, against 27.8% for π0.5, but took 280 s per task against 62 s.
   - CaP-X (ICML 2026) made CaP-Gym the shared benchmark.
   - ACE-CaP-0 (2026-11-12) freezes agent-written code to remove per-run model calls: 92.1% over 240 real trials.
   - WetRobo (2026-09-16): on a PiPER, a Codex agent adapted to a second lab where a π0.5 fine-tuned on 25 demos did not.
   - SO-101 Bench (2026-10-27): an agent plus a learned grasp policy reached 64% on a real SO-101, against at most 53% for pure policies.
2. **Independent SO-101 numbers replaced launch-blog claims.** All three show large variance:
   - The June failure benchmark: π0.5 56%, SmolVLA 33% (100 demos per task).
   - SO-101 Bench: π0.5 18% on real layouts with simulation-only training data. Simulation overestimates success by 9–31 pp but keeps the ranking.
   - RoboColosseum (2026-11-02): GR00T N1.7 82.4% and π0.5 77.6% with 100 demos per task. SO-101 rankings were the least reproducible across sites (59% agreement), and rankings barely carry over between embodiments (W = 0.24).
3. **AgileX PiPER is now the usual low-cost arm in lab-manipulation papers.**
   - Examples: RoboSynChallenge, a NeurIPS 2026 competition with pipette tasks where π0.5 scored 33–38.5%; Robo-MLT, 82% and 70% with about 1k demos per task; WetRobo; TVF-DiT, with powder transfer; LoRA-SP at ICRA 2026.
   - None of them reports accuracy or repeatability.
   - LeRobot still has no native PiPER support (three third-party plugins). AgileX's `agx_arm_sim` provides USD and URDF for a digital twin.
4. **Lab-specific VLA benchmarks multiplied, and all show low success.**
   - LabDex (Aug): no real long-horizon workflow completed.
   - SciVLABench (Sept): best 49.7%.
   - DexBioLab (Oct): mean around 17–21%.
   - Labference (Oct): VLAs ignore the balance reading, so π0.5 completed 16% of weighing episodes against 8/10 for GPT-driven control.
   - BEAKER: NeurIPS 2026 spotlight.
   - The first open lab-specific VLA (LabVLA, June) beats a fine-tuned π0.5 by only 1–3 points on a real robot.
5. **Success and failure detection is now an off-the-shelf component.**
   - Gemini Robotics ER 2 (2026-07-30) is callable in AI Studio: 82.4% video success detection, 65.7% instrument reading.
   - Robometer (RSS 2026) and TOPReward ship in LeRobot since v0.6.0.
   - LIRA (Commun. Chem., Nov 2025): a fine-tuned VLM on an edge box verifies placements at 97.9%.
6. **LeRobot churned.**
   - v0.6.0 (Jul) added GR00T N1.7, MolmoAct2, reward models, RoboTwin 2.0 and HF Jobs training.
   - v0.7.0 (2026-11-05) removed `async_inference` in favour of a remote policy server.
   - Python 3.12 has been required since v0.5. Pin versions per project.
7. **Cloud-lab and metals funding landed in July–August 2026.**
   - NSF Programmable Cloud Laboratories: $380M to 20 teams, plus up to $20M from Astera, with metals nodes.
   - CMU's node includes MICL, which starts by automating Al-alloy powder production on an AMAZEMET rePOWDER.
   - Texas A&M ARM-MIP: $24.9M, free to U.S. academics, aiming for 50 rising to more than 200 alloys a month.
   - DOE Genesis Phase I: 278 awards, with an autonomous-labs challenge.
   - Ginkgo opened a commercial pay-per-run cloud lab (2026-03).
8. **Calibration and simulation tooling matured.**
   - Targetless calibration of wrist plus fixed cameras (AnchorHEC, 2026-11-02).
   - Camera-latency calibration worth +8.1 pp of policy success (SyncHeC, 2026-11-02).
   - Isaac Lab 3.0 general availability (2026-10-20), with Newton MPM solvers for powders and liquids.
   - Generated lab twins: Pipette (June, includes an AgileX arm) and Self-Building Labs (Oct; Isaac Sim twin plus OT-2 protocols).
9. **Robots now load crucibles and arc melters**: AlloyBot (preprint), the NIMS COBOTTA + Quantos journal version (Feb 2026) and A-Lab GPSS (Apr 2026). Metallographic prep and printed-specimen handling stay manual wherever papers report them (AIMD-L, the APEX plan, agentic SLS). The commercial printer-farm answer is sheet-swapping harvester arms (Prusa Pro AFS, US debut Apr 2026).
10. **The safety baseline moved.**
    - ISO 10218:2025 and R15.06-2025 frame safety around the "collaborative application" and add cybersecurity requirements for networked robots.
    - ISO 25785-1, for legged and balancing robots, is at committee-draft stage.
    - LabSafety Bench (NMI 2026): no model reaches 70% on hazard identification. LABSHIELD: accuracy drops 32% in lab scenarios.
    - So LLM or VLM planners cannot be the safety layer for the arm.

## Gaps that still look open

- **No independent accuracy, repeatability or drift data for PiPER or SO-101.**
  - Two sub-scans searched separately for repeatability, backlash and ISO 9283 results for SO-101, SO-100, PiPER, myCobot and xArm Lite 6 in 2025–2026. They found only vendor figures (PiPER ±0.1 mm, contradicted by a reseller's ±0.05 mm) and anecdotes.
  - Field evidence suggests the numbers matter:
    - AUTOHIAM's docs report mm-scale PiPER drift after long disconnection.
    - The SO-101 failure benchmark names backlash and limited repeatability as noise sources without measuring them.
    - RoboColosseum finds SO-101 results the least reproducible across sites.
  - An ISO 9283-style study of both arms, with drift over time, measured by the Pi cameras and AprilTags, would be new and widely cited.
- **No real-lab comparison of a coding agent and a VLA on a low-cost arm with repeated trials.**
  - AMP1 is Franka-only, with calibrated stereo depth.
  - WetRobo reports single adaptation attempts with no success statistics.
  - SO-101 Bench uses tabletop objects.
  - CaP-RL's real results are on a Franka.
  - Still needed: a PiPER/SO-101 study of an AMP1- or CaP-style harness against π0.5 or GR00T N1.7, with N ≥ 20 per task, latency, cost per run, and transfer to a second cell or the cloud lab.
- **No learned-policy or agent results on metals and powder workflows.**
  - The closest are TVF-DiT's single powder-transfer task (10 trials) and Labference's simulated weighing.
  - No academic arm-based LPBF build-plate, coupon or depowdering handling turned up, only industrial systems from trade press.
  - Metallographic prep is still manual at AIMD-L. APEX's robotic grinding has no paper yet, and only about 20 RoboMet-3D units exist.
  - No Al-alloy powder → LPBF → test loop has been published; CMU MICL is a plan.
- **No research arm has tended desktop 3D printers since 2023, and no autonomous tensegrity design–print–test loop exists.**
  - Searches found only 2021–2023 academic work, a simulation-only 2025 workshop draft, and commercial systems: Prusa Pro AFS, a Bambu plate cycler, and a single trade report of a 44-printer farm.
  - TeleopLab ran remote tensile tests of printed specimens, but with industrial arms and n = 6 students.
  - A PiPER/SO-101 cell tending the Bambu printers, with Pi-camera failure detection and robotic specimen transfer to a tester, would be a first.
- **Real-world lab benchmarks and open lab datasets for single low-cost arms are missing.**
  - Pipette, LabUtopia, SciVLABench, DexBioLab, Labference and Labimus are simulation-only.
  - A Hub snapshot found 0 LeRobot datasets tagged chemistry, glassware, labware or build_plate. RoboCOIN's PiPER data is bimanual.
  - Precision, safety and protocol compliance are not scored on real low-cost hardware, a point the AI4Mat 2026 review and Labimus (3.3% within tolerance vs 5.3% binary success) both make.
- **Transparent-labware perception lacks robot-level validation with RGB-only cameras.**
  - TransNormal/-2 report only ClearGrasp/ClearPose metrics, and Trans2Occ's abstract gives no numbers.
  - The newest liquid-volume dataset found dates from 2024.
  - ASHE shows a cheap camera plus a CNN correcting placements of transparent substrates (98.5%), but on an xArm with a RealSense.
- **Remote and teleoperated lab teaching on low-cost arms, with measured internet latency, is thin.** TeleopLab did not measure network delay. The only VLA remote-serving set-up is RoboColosseum's evaluation API. LADS OPC UA has had no release since Part 1 (2024-01-18).
- **Humanoid lab evidence is still simulation or press releases.** Labimus reports ≤5.3% grasp-and-place in simulation, and Tactus "Elsie" (2026-07) has no data. Low-cost arms remain the evidence-backed choice.

## Verification caveats (weaker items)

- **Secondary or listing-only sources:**
  - Pi API beta: from secondary coverage, because pi.website returned 429.
  - π*0.6 in RSS 2026: from the proceedings index.
  - Mobile robotic process chemist: the RSC page returned 403, so it rests on the listing.
  - ADePT: via PMC.
  - CRESt: numbers via MIT News, because Nature needs a login.
  - ISO 25785-1 stage: via DIN and a search listing.
  - Ginkgo's $39/sample: from third-party docs.
  - TransNormal's ICML acceptance and the Isaac Lab paper: via listings.
  - AlloyBot: via its SI PDF and UW pages.
  - ORGANA's journal version and ChemAgents: via bibliographic listings.
- **Press releases or project pages, not papers:** NSF PCL nodes, CMU MICL, Texas A&M ARM-MIP, LLNL APEX, DOE Genesis, Ginkgo, AUTOHIAM, Tactus Elsie, Prusa Pro AFS, and AMAZEMET (partly trade press).
- **Internal inconsistencies:**
  - Chemist Eye's hazard-detection rate is 97% in the arXiv abstract but 88% in the journal abstract (seen only as a search snippet).
  - The LoRA-SmolVLA-on-SO101 paper calls SmolVLA "~3.1B", which conflicts with its published 0.45B.
  - MolmoAct2's SO-101 scores are partial credit.
  - The BioProVLA and DexBioLab means are computed here; the BioProVLA ones were re-checked against Table 3.
- **Small-N results:** TVF-DiT (10 trials per task), TeleopLab (n = 6), WetRobo (single attempts), and AMP1's real-world set (108 trials, one arm type).
- **Hardware read from paper bodies, not abstracts:** PiPER use in WetRobo, RoboSynChallenge and Robo-MLT, read from the papers' bodies by the sub-scans. The abstracts were re-checked and are consistent but do not name the arm.

## Appendix: leads seen but not verified, or verified but left out

### Topic 3 (agentic control)
- "Toward Full Autonomous Laboratory Instrumentation Control with Large Language Models" (Xie, He, Castellanos-Gomez; arXiv:2604.03286, 2026-03-25). Opened: LLM-written control for an optics instrument; no arm, no numbers.
- Schema-Bound LLM Control of Scientific Instrumentation (arXiv:2607.17012) and LAP: Lab Agent Protocol (arXiv:2606.03755). Seen only in search snippets: a software-only validation and a specification.
- OpenLabAI (MCP server for OT-2, Hamilton and Biomek liquid handlers; GitHub, with a bioRxiv preprint cited). Results not verified.
- ACRA (Cronin group; LLM multi-agent synthesis on Chemputers; *Communications Chemistry* 2026) and Chemist-X (agent-written control scripts). Not opened.
- Press coverage of AMP1 that names specific models (e.g., cryptobriefing, 36kr). Not used; the arXiv HTML was used instead.

### Topics 1 and 8
- npj Computational Materials 2026, "Self-driving manufacturing…" (s41524-026-02204-9): paywall redirect, and the title could not be confirmed.
- *Bioanalysis* 2026 opinion piece on humanoids in bioanalytical labs (10.1080/17576180.2026.2674994): 403. Bioanalysis Zone report of humanoids trained for chemistry labs (CCTV, June 2026): 403.
- Yaskawa/RBI Maholo "99.5% pipetting accuracy" (NIBS Network trend article): secondary only.
- Insilico Medicine "Supervisor" bipedal humanoid (EurekAlert, 2025-03): prototype press item.
- ASEE 2026, "Closing the Adoption Gap: AI-Driven, Low-Latency, and Compatible Remote Robotics Laboratories" (Narayan, Salem, Saharan): 403. Deakin RoboCom haptic remote robot arm for schools (news, 2026-06).
- AgentChemist (*arXiv:2603.23886*) and BioMARS 2.0 (*arXiv:2611.12139*): opened, but no hardware or quantitative results.
- Rainbow (Nat. Commun. 2025-08-22, DOI 10.1038/s41467-025-63209-4) and Polybot (Nat. Commun. 2025-02): records verified, but arm use not confirmed.
- PiPER-based general-manipulation papers seen only in search snippets: E0.5 (2610.36011), H-VLA (2609.22895), "Beyond Monotonic Progress" (2606.24633), DyQ-VLA (2603.07904), InstructMove (2608.22990).
- Benchmarks seen only as titles: Labference (2610.35252), RoboChemGym (2610.02708). LeRobot library paper (2602.22818), not opened.
- Digital Discovery 2026 autonomous powder weighing with a robot arm and spatula (Pizzuto, Cooper; d5dd00569h): not opened (§7).
- RoboChem Flex (Pilon et al., Nature Synthesis 2026, DOI 10.1038/s44160-026-01053-0): a ~US$5k flow-chemistry SDL with no arm, so out of scope.
- AC Dev/Training Lab docs (myCobot 280 + AprilTags, livestreams, MQTT, Tailscale, OT-2): undated documentation, not a publication.

### Topic 2
- TANDEM (arXiv:2609.28314), FOCA (ICML 2026, PMLR v306), TwinVLA (arXiv:2511.05275), VLA-Corrector (arXiv:2607.01804): data-efficiency and inference methods seen only in search snippets.
- "A Practical Recipe Towards Improving Sim-and-Real Correlation for VLA Evaluation" (arXiv:2606.10366) and SimFoundry (arXiv:2606.28276): not opened; may suit §5.
- GR00T N2 (previewed at GTC 2026 as DreamZero-based, "by end of year"): secondary coverage only. N1.5/N1.6 non-commercial licence: seen only in an NVIDIA developer-page snippet.
- Wizwand "AgileX PiPER real-world" leaderboards: derived from LoRA-SP, so not a separate source.
- Community model card StrongRoboticsLab/pi05-so100-diverse (claims GR00T N1.5 adapts to SO-101 with 30 episodes and SmolVLA plateaus near 200 episodes): secondary, not used.
- Galaxea 0.5 (best pure VLA in SO-101 Bench) and the MolmoSpaces benchmark: not verified separately.
- BioMARS 2.0 (arXiv:2611.12139, 2026-11-09; opened, multi-agent robotic biologist, platform and policy not stated in abstract), BioProAgent (arXiv:2603.00876), AgentChemist (arXiv:2603.23886; opened, no policy details or numbers): agentic systems (§1/§3).

### Topics 4 and 5
- ABC-130K, "Scalable Behavior Cloning with Open Data, Training, and Evaluation" (arXiv:2606.27375, 2026-06-25): verified (3,553 h, 134,806 episodes; sim–real success correlation r = 0.85 over 12 checkpoints) but more §2 than §4.
- MolmoAct2 (arXiv:2605.02881, 2026-05-04; SO-100/101 one of its out-of-box embodiments) is verified and listed in §2. A secondary article's 86.7% pipette-to-tray figure is unconfirmed by a primary source.
- AnchorD (arXiv:2605.02667; monocular depth anchored to raw sensor depth) and Hydra (arXiv:2504.20584; RGB-D marker-free hand-eye calibration): seen, not included because they need depth sensors or have no numbers in the abstract.
- Real-to-Sim GS policy evaluation (arXiv:2511.04665): verified, but its abstract has no numbers and it is not lab-specific. RoboArena (arXiv:2506.18123, 2025): superseded for SO-101 by RoboColosseum.
- TCG-Depth (Symmetry, Feb 2026) and ADDFNet (Preprints.org, Apr 2026), transparent depth completion: seen only in search snippets.
- LeRobot hackathon 2026: no 2026 event record found (only the June 2025 worldwide hackathon).
- Isaac Lab-Arena (LeRobot EnvHub integration in v0.4.3) and LeIsaac (SO-101 in Isaac Lab; its LeRobot page is marked deprecated): mentioned in passing, not separate items.

### Topics 6 and 7
- Radulov et al., "Vision-guided adaptive scooping for powder weighing in autonomous chemistry laboratories," Digital Discovery 2026 (d5dd00569h; RSC returned 403). Very likely the already-covered "Franka powder scooping" item, so not re-listed; FLIP (arXiv:2506.03896, 2025) is its predecessor.
- DHR Engineering robot swapping plates on 44 Bambu X1C printers (Prism News; single source, no official page).
- Chitu PlateCycler C1M for the Bambu A1 mini ($79; Hackaday hands-on 2026-01-16; retailer page only). A plate swapper, not an arm.
- Almond AI "robot-as-a-service" for printer farms (Fabbaloo; page returned 403).
- Georgia Tech thesis, "Self-driving Lab of Photopolymer Synthesis and Mechanical Testing for Expedited Materials Discovery" (robotic tensile testing; repository returned 403).
- Daunert et al., "Automating 3D printing for mass production," Austrian Robotics Workshop 2025 (2-page draft, simulation only, KUKA KR10 with an MSLA printer).
- Solukon SFM-AT800-S robot-integrated depowdering (Formnext 2025, trade press only); Fraunhofer IPK 2025 robotic chiselling for support removal (>95% removal; repository blocked).
- ISI Brno, "Advanced Metallographic Preparation of Advanced Alloys" (IMAT 2026 poster on robot-assisted electrolytic etching; no numbers).
- AgentAM (arXiv:2611.05171, 2026-11-03): LLM/MCP agent over CFD surrogates for SS316L LPBF. Simulation only, no robot.
- Fadhel et al., IAAI 2026 (arXiv:2601.17587): adaptive design for DED GRCop-42, not robotic. AutoMAT (arXiv:2507.16005): degree of experimental automation unclear.
- NIMS JSAP spring 2026 talk (10 consecutive automated V3Ge syntheses; code reportedly on GitHub; page returned 403). BU's 26 → 55 J/g result (no citable paper found). Instron CT6 Cobot Test System (official page blocked). XtalPi NeoDispenser (vendor brochure only).
- Out of scope, passed to other forks: arXiv:2603.09051 (low-cost dual-arm mobile manipulator based on XLeRobot); "Labference" (arXiv:2610.35252, benchmark of reasoning-action links in robotic labs); PNNL "AutoLabs" multi-agent self-correction (2026-09); ADePT framework for assessing lab robotics (Salazar-Villacis & Benyahia, Commun Chem, 2026-02-20).

### Verified in sub-scans but dropped as low priority or redundant
- OpenVLA-OFT (arXiv:2502.19645), X-VLA (arXiv:2510.10274), RDT2 (arXiv:2602.03310), DreamZero (arXiv:2602.15922), openpi (folded into the π0.7 line), ChemBot/Skill-VLA (arXiv:2604.15671), Embodied Science Agents (arXiv:2611.12958), Aalborg sliding-mode control (arXiv:2602.06977), SAFE-CHEM (arXiv:2608.09303), PREVENT (arXiv:2510.21438), Matter 2026 community pieces (Brown et al.; ThinkFactory 2025), SDL 2.0 review (Materials Horizons 2026).
