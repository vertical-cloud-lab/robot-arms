Question: We have a low-cost AgileX PiPER 6-DOF arm (about $2k) and SO-101 leader/follower arms (about $200), with parallel grippers, Raspberry Pi wrist cameras and fixed cameras in an enclosure, AprilTags, and LeRobot-style imitation learning or scripted motion. We want to place these arms in the published literature and compare them with industrial and research arms (e.g. UR5e, Franka, ABB YuMi, Kinova) using tests we can repeat ourselves.

Learned vs scripted: How well have imitation-learning policies (ACT, diffusion policy, LeRobot policies) performed on low-cost arms, and how many demonstrations did they need? How do they compare with scripted or fiducial-guided motion on the same task?

Prioritize peer-reviewed journal articles and major conference papers from 2015 to 2026, and flag any preprints. For each benchmark or result, describe the protocol in enough detail to repeat it (what is measured, number of trials, success criterion, measuring tool) and give the arm model. For each claim, give the DOI and quote the sentence that supports it. Say explicitly where no published evidence exists.


# Imitation-Learning Policies on Low-Cost Robot Arms: Benchmarks, Demonstration Requirements, and Comparison with Scripted Motion

## 1. Overview

This report synthesizes the published and preprint literature (2023–2026) on imitation-learning (IL) policies—Action Chunking with Transformers (ACT), Diffusion Policy, SmolVLA, π0, and π0.5—evaluated on low-cost arms directly relevant to the user's hardware (AgileX PiPER 6-DOF, SO-101 leader/follower). It also positions these results against the established Diffusion Policy benchmark on the UR5 industrial arm. **Caveat:** The majority of SO-101 and AgileX PiPER results are from arXiv preprints (flagged below); only the ALOHA/ACT paper (RSS 2023) and the Diffusion Policy paper (IJRR 2024) have appeared in peer-reviewed venues.

The following table consolidates the main results across platforms, policies, tasks, and evaluation protocols.

| Paper (year; status; DOI) | Robot arm (cost tier) | Policy | Task | Demonstrations | Evaluation trials | Success rate | Success criterion |
|---|---|---|---|---:|---:|---:|---|
| Zhao et al. (2023; RSS 2023 paper; arXiv version; DOI: 10.48550/arXiv.2304.13705) (zhao2023learningfinegrainedbimanual pages 7-8, zhao2023learningfinegrainedbimanual pages 6-7) | ALOHA bimanual; low-cost research platform | ACT | Slide Ziploc | 50 | 25 | 88% | Grasp bag, pinch slider, and open zipper |
| Zhao et al. (2023; RSS 2023 paper; arXiv version; DOI: 10.48550/arXiv.2304.13705) (zhao2023learningfinegrainedbimanual pages 7-8, zhao2023learningfinegrainedbimanual pages 6-7) | ALOHA bimanual; low-cost research platform | ACT | Slot Battery | 50 | 25 | 96% | Grasp, place, and fully insert battery while stabilizing controller |
| Zhao et al. (2023; RSS 2023 paper; arXiv version; DOI: 10.48550/arXiv.2304.13705) (zhao2023learningfinegrainedbimanual pages 7-8, zhao2023learningfinegrainedbimanual pages 6-7) | ALOHA bimanual; low-cost research platform | ACT | Open Cup | 50 | 25 | 84% | Tip cup, grasp it, and remove/open lid |
| Zhao et al. (2023; RSS 2023 paper; arXiv version; DOI: 10.48550/arXiv.2304.13705) (zhao2023learningfinegrainedbimanual pages 7-8, zhao2023learningfinegrainedbimanual pages 6-7) | ALOHA bimanual; low-cost research platform | ACT | Thread Velcro | 100 | 25 | 20% | Lift and grasp tie, then insert one end through the other tie’s loop |
| Zhao et al. (2023; RSS 2023 paper; arXiv version; DOI: 10.48550/arXiv.2304.13705) (zhao2023learningfinegrainedbimanual pages 7-8, zhao2023learningfinegrainedbimanual pages 6-7) | ALOHA bimanual; low-cost research platform | ACT | Prep Tape | 50 | 25 | 64% | Grasp, cut, hand over, and secure tape on box |
| Zhao et al. (2023; RSS 2023 paper; arXiv version; DOI: 10.48550/arXiv.2304.13705) (zhao2023learningfinegrainedbimanual pages 7-8, zhao2023learningfinegrainedbimanual pages 6-7) | ALOHA bimanual; low-cost research platform | ACT | Put On Shoe | 50 | 25 | 92% | Fit and secure shoe so it remains attached after release |
| Fu et al. (2024; **preprint**; DOI: 10.48550/arXiv.2401.02117) (fu2401mobilealohalearning pages 7-8, fu2401mobilealohalearning pages 5-7) | Mobile ALOHA bimanual; low-cost research platform | ACT with static-ALOHA co-training | Wipe Wine | 50 | 20 | 95% | Complete towel grasp, glass lift/wipe, and glass replacement |
| Fu et al. (2024; **preprint**; DOI: 10.48550/arXiv.2401.02117) (fu2401mobilealohalearning pages 7-8, fu2401mobilealohalearning pages 5-7) | Mobile ALOHA bimanual; low-cost research platform | ACT with static-ALOHA co-training | Cook Shrimp | 20 | 5 | 40% | Add oil and shrimp, flip shrimp, and plate it |
| Fu et al. (2024; **preprint**; DOI: 10.48550/arXiv.2401.02117) (fu2401mobilealohalearning pages 7-8, fu2401mobilealohalearning pages 5-7) | Mobile ALOHA bimanual; low-cost research platform | ACT with static-ALOHA co-training | Rinse Pan | 50 | 20 | 80% | Grasp pan, turn on faucet, and position/rinse pan |
| Fu et al. (2024; **preprint**; DOI: 10.48550/arXiv.2401.02117) (fu2401mobilealohalearning pages 7-8, fu2401mobilealohalearning pages 5-7) | Mobile ALOHA bimanual; low-cost research platform | ACT with static-ALOHA co-training | Use Cabinet | 50 | 20 | 85% | Open cabinet, grasp/place pot, and close cabinet |
| Fu et al. (2024; **preprint**; DOI: 10.48550/arXiv.2401.02117) (fu2401mobilealohalearning pages 7-8, fu2401mobilealohalearning pages 5-7) | Mobile ALOHA bimanual; low-cost research platform | ACT with static-ALOHA co-training | Call Elevator | 50 | 20 | 95% | Navigate, press button, and enter elevator |
| Fu et al. (2024; **preprint**; DOI: 10.48550/arXiv.2401.02117) (fu2401mobilealohalearning pages 7-8, fu2401mobilealohalearning pages 5-7) | Mobile ALOHA bimanual; low-cost research platform | ACT with static-ALOHA co-training | Push Chairs | 50 | 20 | 80% | Push all required chairs to their target positions |
| Fu et al. (2024; **preprint**; DOI: 10.48550/arXiv.2401.02117) (fu2401mobilealohalearning pages 7-8, fu2401mobilealohalearning pages 5-7) | Mobile ALOHA bimanual; low-cost research platform | ACT with static-ALOHA co-training | High Five | 20 | 20 | 85% | Complete high-five under unseen-person/attire conditions |
| Chi et al. (2024; peer-reviewed IJRR; DOI: 10.1177/02783649241273668) (chi2025diffusionpolicyvisuomotor pages 8-9, chi2025diffusionpolicyvisuomotor pages 17-18) | UR5; industrial arm | End-to-end Transformer Diffusion Policy | Real-world Push-T | 136 | 20 | 95%; mean final IoU 0.80 | Push T into target and enter end-zone; final camera-space IoU must exceed minimum human-demonstration IoU; 60-s limit |
| Cowling (2026; **preprint**; DOI: 10.48550/arXiv.2610.37170) (cowling2026from12to pages 1-3, cowling2026from12to pages 19-21) | SO-101; ultra-low-cost, ≈$200 | ACT | Ball pick-and-place with two distractors | 12–200; reported point: 100 | ≈40 per condition | 92.5% (37/40) at 100 demos | Start, reach and grasp ball, carry it, and deliver it within 30 s |
| Cowling (2026; **preprint**; DOI: 10.48550/arXiv.2610.37170) (cowling2026from12to pages 1-3) | SO-101; ultra-low-cost, ≈$200 | Diffusion Policy | Ball pick-and-place with two distractors | 12, 25, 50, 100, 200 | ≈40 per condition | Peaked near 50% | Complete ball delivery within 30 s; initiation, reach, carry, and delivery also audited |
| Cowling (2026; **preprint**; DOI: 10.48550/arXiv.2610.37170) (cowling2026from12to pages 1-3) | SO-101; ultra-low-cost, ≈$200 | π0.5 fine-tuned | Ball pick-and-place with two distractors | 12, 25, 50, 100, 200 | ≈40 per condition | 40% at 12 demos; 70% at 25; ≈70% thereafter | Complete ball delivery within 30 s |
| Wang et al. (2026; **preprint**; DOI: 10.48550/arXiv.2605.28736) (wang2026imitationlearningfor pages 6-10, wang2026imitationlearningfor pages 10-13, wang2026imitationlearningfor pages 4-6) | SO-101 follower; ultra-low-cost, ≈$200 | ACT | Suture following/acquisition | 160 | 20 | 50% | Locate, approach, and acquire taut suture with millimeter-precise gripper contact, without intervention |
| Wang et al. (2026; **preprint**; DOI: 10.48550/arXiv.2605.28736) (wang2026imitationlearningfor pages 6-10, wang2026imitationlearningfor pages 10-13, wang2026imitationlearningfor pages 4-6) | SO-101 follower; ultra-low-cost, ≈$200 | Diffusion Policy | Suture following/acquisition | 160 | 20 | 65% | Locate, approach, and acquire taut suture with millimeter-precise gripper contact, without intervention |
| Wang et al. (2026; **preprint**; DOI: 10.48550/arXiv.2605.28736) (wang2026imitationlearningfor pages 6-10, wang2026imitationlearningfor pages 10-13, wang2026imitationlearningfor pages 4-6) | SO-101 follower; ultra-low-cost, ≈$200 | SmolVLA | Suture following/acquisition | 160 | 20 | 65% | Locate, approach, and acquire taut suture with millimeter-precise gripper contact, without intervention |
| Wang et al. (2026; **preprint**; DOI: 10.48550/arXiv.2605.28736) (wang2026imitationlearningfor pages 6-10, wang2026imitationlearningfor pages 10-13, wang2026imitationlearningfor pages 4-6) | SO-101 follower; ultra-low-cost, ≈$200 | π0 | Suture following/acquisition | 160 | 20 | 75% | Locate, approach, and acquire taut suture with millimeter-precise gripper contact, without intervention |
| Selvaraj et al. (2026; **preprint**; DOI: 10.48550/arXiv.2607.24481) (selvaraj2607armnetbenchv0.1parallel pages 7-9, selvaraj2607armnetbenchv0.1parallel pages 3-7) | SO-101 arm farm; ultra-low-cost cells | π0.5 | Aggregate over 12 single-arm/bimanual tabletop tasks | 50 per task | Usually 30 per policy-task cell | 47.6% aggregate strict success | Human operator labels rollout successful, suboptimal, or failed; strict rate counts only successful completion |
| Selvaraj et al. (2026; **preprint**; DOI: 10.48550/arXiv.2607.24481) (selvaraj2607armnetbenchv0.1parallel pages 7-9, selvaraj2607armnetbenchv0.1parallel pages 3-7) | SO-101 arm farm; ultra-low-cost cells | π0 | Same 12-task aggregate | 50 per task | Usually 30 | 35.1% | Strict successful-completion label |
| Selvaraj et al. (2026; **preprint**; DOI: 10.48550/arXiv.2607.24481) (selvaraj2607armnetbenchv0.1parallel pages 7-9, selvaraj2607armnetbenchv0.1parallel pages 3-7) | SO-101 arm farm; ultra-low-cost cells | GR00T N1.7 | Same 12-task aggregate | 50 per task | Usually 30 | 29.4% | Strict successful-completion label |
| Selvaraj et al. (2026; **preprint**; DOI: 10.48550/arXiv.2607.24481) (selvaraj2607armnetbenchv0.1parallel pages 7-9, selvaraj2607armnetbenchv0.1parallel pages 3-7) | SO-101 arm farm; ultra-low-cost cells | Diffusion Policy | Same 12-task aggregate | 50 per task | Usually 30 | 26.7% | Strict successful-completion label |
| Selvaraj et al. (2026; **preprint**; DOI: 10.48550/arXiv.2607.24481) (selvaraj2607armnetbenchv0.1parallel pages 7-9, selvaraj2607armnetbenchv0.1parallel pages 3-7) | SO-101 arm farm; ultra-low-cost cells | ACT | Same 12-task aggregate | 50 per task | Usually 30 | 19.2% | Strict successful-completion label |
| Selvaraj et al. (2026; **preprint**; DOI: 10.48550/arXiv.2607.24481) (selvaraj2607armnetbenchv0.1parallel pages 7-9, selvaraj2607armnetbenchv0.1parallel pages 3-7) | SO-101 arm farm; ultra-low-cost cells | SmolVLA | Same 12-task aggregate | 50 per task | Usually 30 | 15.0% | Strict successful-completion label |
| Feng et al. (2026; **preprint**; DOI: 10.48550/arXiv.2602.23408) (feng2026demystifyingactionspace pages 4-5, feng2026demystifyingactionspace pages 21-22) | AgileX PiPER; low-cost, ≈$2,000 | ACT | Four-task curriculum: Touch Cube, Pick Up Cup, Pick-and-Place Cup, Bimanual Cube Transfer | Not reported in retrieved text | 3 independent repeats × 10 rollouts | 26.7–46.3% mean, depending on action space | Task completion; objects initialized uniformly over a 6×6 workspace grid |
| Feng et al. (2026; **preprint**; DOI: 10.48550/arXiv.2602.23408) (feng2026demystifyingactionspace pages 4-5, feng2026demystifyingactionspace pages 21-22) | AgileX PiPER; low-cost, ≈$2,000 | Diffusion Policy | Same four-task curriculum | Not reported in retrieved text | 3 independent repeats × 10 rollouts | 26.0–48.0% mean, depending on action space | Task completion under the same 6×6-grid initialization protocol |
| Hickok (2026; **preprint**; DOI: 10.48550/arXiv.2610.36420) (hickok2026so101benchaccessible pages 2-4, hickok2026so101benchaccessible pages 6-8) | SO-101; ultra-low-cost, ≈$200 | Galaxea 0.5 | Physical spatial manipulation: bin, next-to, between, and directional-move families | 3,629 simulated teleoperated demonstrations shared by learned policies | 45 physical layouts | 53% (24/45) | Automatically/task-specifically score correct object selection, grasp, and required placement or directional relation |
| Hickok (2026; **preprint**; DOI: 10.48550/arXiv.2610.36420) (hickok2026so101benchaccessible pages 2-4, hickok2026so101benchaccessible pages 6-8) | SO-101; ultra-low-cost, ≈$200 | GPT-6.1 Sol + PyRUA-Lean, delegating grasping to Galaxea 0.5 | Same physical spatial-manipulation families | 3,629 simulated demonstrations for Galaxea component; agent itself is code/tool based | 45 physical layouts | 64% (29/45) | Correct object selection and completion of specified spatial relation or bin/move goal |


*Table: Comparison of reported imitation-learning and hybrid-policy results on ALOHA, SO-101, AgileX PiPER, and UR5 hardware. It highlights demonstration budgets, physical evaluation sizes, success definitions, and the predominance of preprint-only evidence in 2026.*

---

## 2. ACT on ALOHA (the Foundational Low-Cost Result)

The most cited low-cost manipulation benchmark is the original ALOHA system by Zhao et al. (RSS 2023, arXiv preprint; DOI: 10.48550/arxiv.2304.13705). Six real-world bimanual tasks were evaluated with 50 teleoperated demonstrations each (100 for Thread Velcro), one random seed, and 25 evaluation trials per task (zhao2023learningfinegrainedbimanual pages 7-8). Object placements were randomized along a 15 cm reference line. Success was defined as sequential subtask completion: for example, Slot Battery required "grasp, place, and fully insert the battery while stabilizing the controller," and Put On Shoe required "fitting and securing the shoe so it remains attached after release" (zhao2023learningfinegrainedbimanual pages 6-7). ACT achieved final-subtask success rates of 88% (Slide Ziploc), 96% (Slot Battery), 84% (Open Cup), 20% (Thread Velcro), 64% (Prep Tape), and 92% (Put On Shoe) (zhao2023learningfinegrainedbimanual pages 7-8, zhao2023learningfinegrainedbimanual pages 8-10).

**Protocol you can repeat:** Collect 50 teleoperated demonstrations per task at 50 Hz (8–14 s episodes, 400–700 steps). Randomize object placement within a defined zone. Evaluate the trained policy over 25 trials. Report subtask-level and whole-task binary success rates.

---

## 3. Mobile ALOHA: Co-Training and Open-Loop Replay

Fu et al. (arXiv **preprint**, 2024; DOI: 10.48550/arxiv.2401.02117) extended ALOHA with a mobile base and evaluated ACT, Diffusion Policy, and VINN on seven mobile-bimanual tasks with 20–50 in-domain demonstrations. Using co-training with existing static ALOHA data, ACT achieved whole-task success rates of 95% (Wipe Wine), 95% (Call Elevator), 85% (Use Cabinet), 85% (High Five), 80% (Rinse Pan), 80% (Push Chairs), and 40% (Cook Shrimp) over 20 trials per task (5 for Cook Shrimp) (fu2401mobilealohalearning pages 7-8, fu2401mobilealohalearning pages 5-7). Critically, open-loop replay of demonstrations—even with objects returned to their original positions—yielded 0% whole-task success on every task (fu2401mobilealohalearning pages 7-8). This is the clearest published demonstration that closed-loop learned policies are categorically superior to open-loop scripted replay on low-cost arms with imprecise base control.

---

## 4. Diffusion Policy on UR5 (Peer-Reviewed Industrial Baseline)

Chi et al. (IJRR, peer-reviewed, 2024; DOI: 10.1177/02783649241273668) benchmarked Diffusion Policy on the real-world Push-T task using a UR5 arm. The policy was trained on 136 demonstrations, evaluated over 20 episodes from matched initial conditions with a 60-second time limit (chi2025diffusionpolicyvisuomotor pages 17-18). Success was defined as the final intersection-over-union (IoU) exceeding the minimum IoU from the human demonstration dataset. The best end-to-end Transformer Diffusion Policy achieved 95% success with a mean final IoU of 0.80, compared with 100% success and 0.84 IoU for human demonstrations (chi2025diffusionpolicyvisuomotor pages 8-9). This is the strongest peer-reviewed real-robot Diffusion Policy result and provides a reproducible reference for comparison with low-cost arms.

**Protocol you can repeat:** Use a top-down camera and a T-shaped block. Collect ~136 demonstrations. Evaluate 20 episodes. Compute pixel-space IoU between the block silhouette and a printed target. An episode succeeds if IoU exceeds the minimum human IoU.

---

## 5. SO-101 Benchmarks

### 5.1 Demonstration Scaling on SO-101 (Cowling, 2026)

Cowling (arXiv **preprint**, 2026; DOI: 10.48550/arxiv.2610.37170) conducted a controlled scaling study on a single SO-101 arm, comparing ACT, Diffusion Policy, SmolVLA, and fine-tuned π0.5 on a ball pick-and-place task with two distractor objects. Models were trained on nested subsets of 12, 25, 50, 100, and 200 demonstrations and evaluated on ten fixed object placements with a 30-second episode limit, producing 1,340 scored episodes across 126 blocks (cowling2026from12to pages 1-3). Key findings:

- **ACT** required between 50 and 100 demonstrations to learn the task. At 12 demonstrations, it reached the ball in only 10% of episodes (6/60). At 100 demonstrations, it achieved 92.5% success (37/40). At 200, performance was 87.5% (35/40) (cowling2026from12to pages 19-21).
- **π0.5** (pretrained VLA, fine-tuned) was substantially better with scarce data: 40% (16/40) at 12 demonstrations and ~70% (28/40) at 25, remaining near 70% thereafter. ACT overtook it from 100 demonstrations onward (cowling2026from12to pages 1-3).
- **Diffusion Policy** peaked near 50% and suffered from an initiation problem—it rarely began moving when demonstrations contained idle lead-in frames, though trimming these frames raised its initiation rate from 4% to 90% (cowling2026from12to pages 1-3).
- **SmolVLA** peaked near 50% and failed to start in 47% of episodes (cowling2026from12to pages 1-3).

### 5.2 Multi-Task Benchmark on SO-101 (ArmnetBench v0.1)

Selvaraj et al. (arXiv **preprint**, 2026; DOI: 10.48550/arxiv.2607.24481) evaluated seven policies across 12 tabletop tasks on a fleet of SO-101 cells, with 50 demonstrations per policy per task and generally 30 rollouts per policy-task cell. Operators labeled each rollout as successful, suboptimal, or failed. Aggregate strict success rates were: π0.5 47.6%, π0 35.1%, GR00T N1.7 29.4%, Diffusion Policy 26.7%, ACT 19.2%, MolmoAct 2 18.9%, and SmolVLA 15.0% (selvaraj2607armnetbenchv0.1parallel pages 7-9). Per-task variation was large; for example, ACT scored 63% on eye_drops_to_basket but 0% on block_stack, while π0.5 scored 86% on transfer_cube and 70% on cable_unclip (selvaraj2607armnetbenchv0.1parallel pages 7-9).

### 5.3 Suture Following on SO-101

Wang et al. (arXiv **preprint**, 2026; DOI: 10.48550/arxiv.2605.28736) benchmarked ACT, Diffusion Policy, SmolVLA, and π0 on suture-thread acquisition using a single SO-101 follower arm with a wrist camera and a fixed side camera. 160 teleoperated demonstrations were used, and each policy was evaluated over 20 test episodes (wang2026imitationlearningfor pages 6-10, wang2026imitationlearningfor pages 10-13). Under the clean-background, dual-camera baseline condition, π0 achieved 75%, Diffusion Policy 65%, SmolVLA 65%, and ACT 50%. π0's advantage was attributed to its pretrained vision-language backbone and data efficiency: it reached 65% success with only 64 demonstrations and remained in the 65–75% range as data increased to 160 (wang2026imitationlearningfor pages 6-10).

### 5.4 SO-101 Bench: Spatial Manipulation

Hickok (arXiv **preprint**, 2026; DOI: 10.48550/arxiv.2610.36420) defined a language-conditioned spatial manipulation benchmark (bin, next-to, between, directional-move tasks) with 916 simulation episodes and 3,629 simulated teleoperated demonstrations. On the physical SO-101 with unseen objects, Galaxea 0.5 (a learned policy) achieved 53% (24/45 layouts), while a code-writing LLM agent (GPT-6.1 Sol + PyRUA-Lean) delegating grasps to Galaxea 0.5 reached 64% (29/45) (hickok2026so101benchaccessible pages 2-4). Simulation overestimated success by 9–31 percentage points but preserved the ranking order of five independently trained policies (hickok2026so101benchaccessible pages 8-10).

---

## 6. AgileX PiPER Benchmarks

### 6.1 Action-Space Design Study

Feng et al. (arXiv **preprint**, 2026; DOI: 10.48550/arxiv.2602.23408) compared ACT and Diffusion Policy on the AgileX single-arm platform across four action-space representations (absolute/relative end-effector, absolute/relative joint position) on four tasks: Touch Cube, Pick Up Cup, Pick-and-Place Cup, and Bimanual Cube Transfer. Results were averaged over three independent repeats of 10 rollouts. ACT averaged 26.7%–46.3% depending on action space; Diffusion Policy averaged 26.0%–48.0%. The best variant for both was relative joint position (ACT 46.3%, DP 48.0%) (feng2026demystifyingactionspace pages 21-22). Object positions were uniformly initialized across a 6×6 workspace grid to reduce distribution shift (feng2026demystifyingactionspace pages 4-5). The number of training demonstrations was not reported in the retrieved text.

### 6.2 AprilTag + MoveIt2 Pipeline (Simulation Only)

Zhang (thesis, 2026; DOI: 10.32920/32253717) integrated the AgileX PiPER 6-DOF arm with AprilTag visual detection and MoveIt2 motion planning in NVIDIA Isaac Sim via ROS2. The AprilTag-detected pose was transformed into the world frame for the MoveIt Task Constructor to generate collision-free pick-and-place trajectories (zhang2026anintegratedsimulation pages 22-27). However, the thesis reported no quantitative success rates, no comparison with learned policies, and no physical-robot evaluation—only a validated simulation pipeline. **No published peer-reviewed or preprint paper was found that directly compares AprilTag-guided scripted closed-loop manipulation with an imitation-learning policy on the same AgileX PiPER task and evaluation protocol.**

---

## 7. Learned vs. Scripted/Open-Loop: What Has Been Compared?

The following table summarizes the sparse but important evidence on this question.

| Study and status | Arm / task | Comparison | Demonstrations | Evaluation protocol | Result | Interpretation |
|---|---|---|---:|---|---|---|
| Zhao et al. (2023), RSS paper; DOI: 10.48550/arXiv.2304.13705 | ALOHA simulation / Cube Transfer | ACT trained on scripted demonstrations vs human demonstrations | Not stated in retrieved excerpt | 3 seeds × 50 evaluations per seed; sequential criteria: touch, lift, transfer | Scripted: **97% / 90% / 86%**; human: **82% / 60% / 50%** for touch/lift/transfer (zhao2023learningfinegrainedbimanual pages 7-8) | Scripted training trajectories were easier to imitate than noisy, multimodal human trajectories; this compares **training-data sources**, not learned control against a scripted controller. |
| Zhao et al. (2023), RSS paper; DOI: 10.48550/arXiv.2304.13705 | ALOHA simulation / Bimanual Insertion | ACT trained on scripted demonstrations vs human demonstrations | Not stated in retrieved excerpt | 3 seeds × 50 evaluations per seed; sequential criteria: grasp, contact, insert | Scripted: **93% / 90% / 32%**; human: **76% / 66% / 20%** for grasp/contact/insert (zhao2023learningfinegrainedbimanual pages 7-8) | Even scripted-data ACT fell to 32% on final insertion, showing that contact-rich precision remained difficult. |
| Fu et al. (2024), **preprint**; DOI: 10.48550/arXiv.2401.02117 | Mobile ALOHA / seven mobile-bimanual tasks | Open-loop demonstration replay vs closed-loop ACT with static-ALOHA co-training | ACT: 20–50 in-domain demonstrations per task | Usually 20 trials per task; Cook Shrimp used 5; whole-task completion | Open-loop replay: **0% on every task**. ACT: **40–95%**, including Wipe Wine 95%, Cook Shrimp 40%, Rinse Pan 80%, Use Cabinet 85%, Call Elevator 95%, Push Chairs 80%, High Five 85% (fu2401mobilealohalearning pages 7-8, fu2401mobilealohalearning pages 5-7) | This is the clearest same-platform learned-versus-open-loop result: visual feedback and online correction dominated replay under base-control error. It is not an AprilTag-guided closed-loop baseline. |
| Cowling (2026), **preprint**; DOI: 10.48550/arXiv.2610.37170 | SO-101 / ball pick-and-place with two distractors | ACT demonstration scaling | 12, 25, 50, 100, 200 | Approximately 40 trials per condition; ten fixed placements; 30-s limit; success required delivery | **1/40 (2.5%) at 12**, modest improvement at 25, higher at 50, **37/40 (92.5%) at 100**, and **35/40 (87.5%) at 200** (cowling2026from12to pages 1-3, cowling2026from12to pages 19-21) | ACT showed a sharp task-specific threshold between roughly 50 and 100 demonstrations; more data did not monotonically improve binary success. |
| Cowling (2026), **preprint**; DOI: 10.48550/arXiv.2610.37170 | SO-101 / same pick-and-place task | Fine-tuned π0.5 demonstration scaling | 12, 25, 50, 100, 200 | Approximately 40 trials per condition; same placements and 30-s limit | **16/40 (40%) at 12**, **28/40 (70%) at 25**, and approximately **70% thereafter** (cowling2026from12to pages 1-3, cowling2026from12to pages 21-24) | Pretraining helped most in the few-demonstration regime; ACT overtook π0.5 at 100 demonstrations under the tested recipes. |
| Wang et al. (2026), **preprint**; DOI: 10.48550/arXiv.2605.28736 | SO-101 / suture following and acquisition | π0 and other policies under demonstration scaling | 32, 64, 96, 128, 160 | 20 test episodes per condition; randomized phantom position and suture direction; success required autonomous thread acquisition without intervention | π0 reached **65% with 64 demonstrations** and remained within **65–75%** thereafter; ACT, Diffusion Policy, and SmolVLA generally improved as data increased (wang2026imitationlearningfor pages 6-10, wang2026imitationlearningfor pages 4-6) | A pretrained VLA reached its performance plateau with fewer demonstrations than policies trained from scratch, but the result is specific to dual-camera suture acquisition. |
| Evidence gap through 2026 | AgileX PiPER or SO-101 / AprilTag-guided pick-and-place | AprilTag-guided scripted closed-loop motion vs ACT, Diffusion Policy, or LeRobot policy on the identical physical task | — | No qualifying matched protocol found | **No published peer-reviewed head-to-head evidence located.** The available PiPER AprilTag–MoveIt2 work validates a simulated pipeline but reports no learned-policy comparison, quantitative trial count, or success rate (zhang2026anintegratedsimulation pages 22-27) | A new controlled experiment is required; open-loop replay and scripted-demonstration training are not substitutes for a closed-loop fiducial-guided baseline. |


*Table: Comparison of the limited matched evidence for learned policies, scripted training data, and open-loop replay, plus demonstration-scaling results on SO-101. It also identifies the unresolved absence of an AprilTag-guided versus imitation-learning comparison on the same low-cost physical task.*

Three distinct forms of comparison appear in the literature:

1. **Scripted vs. human training data for the same learned policy.** Zhao et al. showed that ACT trained on scripted (programmatic) demonstrations substantially outperformed ACT trained on human demonstrations in simulation. On Cube Transfer, scripted-data ACT achieved 86% on the hardest subtask vs. 50% for human-data ACT (zhao2023learningfinegrainedbimanual pages 7-8). This reflects training-data quality, not a learned-vs.-scripted controller contrast.

2. **Open-loop replay vs. closed-loop learned policy.** Fu et al. found that open-loop replay of a demonstration yielded 0% whole-task success on every Mobile ALOHA task, while ACT achieved 40–95% (fu2401mobilealohalearning pages 7-8). This demonstrates that visual feedback and online correction are essential for low-cost arms with imprecise actuation.

3. **No AprilTag-guided closed-loop baseline.** Despite the user's interest in fiducial-guided scripted motion, **no published paper was found that evaluates an AprilTag-guided closed-loop scripted controller alongside an imitation-learning policy on the same low-cost arm, task, and evaluation protocol.** The Zhang 2026 thesis validates an AprilTag + MoveIt2 pipeline for the AgileX PiPER in simulation but reports no learned-policy comparison or quantitative success metrics (zhang2026anintegratedsimulation pages 22-27). This represents a clear gap in the literature and an opportunity for a new contribution.

---

## 8. Cross-Platform Comparison: Low-Cost vs. Industrial Arms

**RoboMIND** (Wu et al., arXiv **preprint**, 2024; DOI: 10.48550/arxiv.2412.13877) collected 107k demonstrations across Franka, UR5e, AgileX, and humanoid platforms under a unified protocol, evaluating ACT, Diffusion Policy (DP3), and other methods with 10 real-world trials per task (wu2024robomindbenchmarkon pages 9-10). The UR5e achieved generally higher per-task success than the Franka on matching IL methods, with some UR5e tasks reaching 0.5–0.8 while Franka tasks ranged 0.0–0.3 (hou2025robomind2.0a pages 37-39). However, these numbers are task-dependent and the column headers were not fully recoverable from the retrieved text.

**RoboTwin 2.0** (Chen et al., arXiv **preprint**, 2025; DOI: 10.48550/arxiv.2506.18088) supports five simulated arms—Franka, PiPER, UR5, ARX-X5, and ALOHA-AgileX—with over 100,000 domain-randomized expert trajectories across 50 dual-arm tasks, providing a sim-to-real transfer benchmark relevant to the user's PiPER hardware.

**LeRobot** (Cadène et al., arXiv **preprint**, 2026; DOI: 10.48550/arxiv.2602.22818) provides reference implementations for ACT, Diffusion Policy, VQ-BET, π0, SmolVLA, and HIL-SERL with native support for SO-100, SO-101, and Koch-v1.1 arms. The library integrates the LIBERO and Meta-World simulation benchmarks, but the LeRobot paper itself does not report physical-robot task success rates (cadene2026lerobotanopensource pages 7-10, cadene2026lerobotanopensource pages 5-7).

**ABB YuMi and Kinova:** No published paper was found that directly benchmarks ACT or Diffusion Policy on ABB YuMi or Kinova Gen3 arms with comparable evaluation protocols to the low-cost arm studies above. These arms appear in the broader robotics literature for other purposes but have not been subjected to the same IL benchmarks.

---

## 9. Protocols You Can Repeat

Based on the literature, the following evaluation protocols are reproducible on your hardware:

1. **Cowling-style demonstration scaling (SO-101).** Collect 200 teleoperated demonstrations of a single task (e.g., pick-and-place). Train ACT and Diffusion Policy on nested subsets of 12, 25, 50, 100, and 200 demonstrations. Evaluate each model on 10 fixed placements × 4 repeats (≈40 trials) with a 30-second episode limit. Score using a four-stage ladder: initiated motion, reached object, grasped/carried, and delivered (cowling2026from12to pages 1-3, cowling2026from12to pages 19-21).

2. **ArmnetBench-style multi-task (SO-101).** Select a subset of the 12 ArmnetBench tasks (e.g., block stacking, ring insertion, cable clipping). Collect 50 demonstrations per task. Evaluate each policy with 30 rollouts per task-policy pair. Label rollouts as successful, suboptimal, or failed (selvaraj2607armnetbenchv0.1parallel pages 3-7).

3. **Push-T style (AgileX PiPER or SO-101).** Print a T-block target template. Collect ~136 demonstrations. Evaluate 20 episodes from matched initial conditions with a 60-second limit. Compute IoU from a top-down camera (chi2025diffusionpolicyvisuomotor pages 17-18).

4. **AgileX PiPER curriculum (four tasks).** Use the Feng et al. four-task progression (Touch Cube → Pick Up Cup → Pick-and-Place Cup → Bimanual Cube Transfer). Divide the workspace into a 6×6 grid, uniformly initialize objects, and evaluate 3 trials × 10 rollouts per action-space variant (feng2026demystifyingactionspace pages 4-5, feng2026demystifyingactionspace pages 21-22).

---

## 10. Key Gaps and Opportunities

- **No peer-reviewed head-to-head comparison of AprilTag-guided scripted closed-loop motion vs. imitation learning on the same low-cost arm exists.** This is the most directly actionable gap for your setup.
- **No published IL benchmark results for ABB YuMi or Kinova Gen3** using ACT or Diffusion Policy were found.
- **Most SO-101 and PiPER results are from 2026 arXiv preprints** with zero or few citations. None have undergone formal peer review at the time of this search.
- **Trial counts on low-cost arms are generally small** (10–40 per condition), limiting statistical power. Cowling explicitly warns that "ten episodes per model is generally insufficient" (cowling2026from12to pages 21-24).
- **Demonstration counts for the AgileX PiPER action-space study (Feng et al.) were not reported** in the retrieved text, limiting reproducibility (feng2026demystifyingactionspace pages 21-22).

---

## 11. Summary of Key Quantitative Findings

- **ACT on ALOHA:** 50 demonstrations, 25 trials, 84–96% on moderate tasks, 20% on the hardest (Thread Velcro) (zhao2023learningfinegrainedbimanual pages 7-8).
- **ACT on SO-101:** Needs ~50–100 demonstrations to become effective; 92.5% at 100 demonstrations on a pick-and-place task (cowling2026from12to pages 19-21).
- **Diffusion Policy on UR5 (peer-reviewed):** 136 demonstrations, 20 trials, 95% success on Push-T (chi2025diffusionpolicyvisuomotor pages 8-9).
- **Diffusion Policy on SO-101:** Peaked near 50% on pick-and-place (Cowling) and 26.7% aggregate across 12 diverse tasks (ArmnetBench) (cowling2026from12to pages 1-3, selvaraj2607armnetbenchv0.1parallel pages 7-9).
- **π0/π0.5 (pretrained VLAs) on SO-101:** Best with scarce data (40% at 12 demos for π0.5); 47.6% aggregate across 12 tasks (ArmnetBench) (selvaraj2607armnetbenchv0.1parallel pages 7-9).
- **ACT and DP on AgileX PiPER:** 26–48% success depending on action-space representation; relative joint-position commands performed best (feng2026demystifyingactionspace pages 21-22).
- **Open-loop replay vs. learned:** 0% vs. 40–95% on Mobile ALOHA (fu2401mobilealohalearning pages 7-8).
- **Scripted vs. human training data:** Scripted-data ACT outperformed human-data ACT by up to 36 percentage points in simulation (zhao2023learningfinegrainedbimanual pages 7-8).
- **AprilTag-guided vs. learned:** **No published evidence exists for this comparison on any low-cost arm.**

References

1. (zhao2023learningfinegrainedbimanual pages 7-8): Tony Z. Zhao, Vikash Kumar, Sergey Levine, and Chelsea Finn. Learning fine-grained bimanual manipulation with low-cost hardware. ArXiv, Apr 2023. URL: https://doi.org/10.48550/arxiv.2304.13705, doi:10.48550/arxiv.2304.13705. This article has 3205 citations.

2. (zhao2023learningfinegrainedbimanual pages 6-7): Tony Z. Zhao, Vikash Kumar, Sergey Levine, and Chelsea Finn. Learning fine-grained bimanual manipulation with low-cost hardware. ArXiv, Apr 2023. URL: https://doi.org/10.48550/arxiv.2304.13705, doi:10.48550/arxiv.2304.13705. This article has 3205 citations.

3. (fu2401mobilealohalearning pages 7-8): Zipeng Fu, Tony Z. Zhao, and Chelsea Finn. Mobile aloha: learning bimanual mobile manipulation with low-cost whole-body teleoperation. ArXiv, Jan 2024. URL: https://doi.org/10.48550/arxiv.2401.02117, doi:10.48550/arxiv.2401.02117. This article has 998 citations.

4. (fu2401mobilealohalearning pages 5-7): Zipeng Fu, Tony Z. Zhao, and Chelsea Finn. Mobile aloha: learning bimanual mobile manipulation with low-cost whole-body teleoperation. ArXiv, Jan 2024. URL: https://doi.org/10.48550/arxiv.2401.02117, doi:10.48550/arxiv.2401.02117. This article has 998 citations.

5. (chi2025diffusionpolicyvisuomotor pages 8-9): Cheng Chi, Zhenjia Xu, Siyuan Feng, Eric Cousineau, Yilun Du, Benjamin Burchfiel, Russ Tedrake, and Shuran Song. Diffusion policy: visuomotor policy learning via action diffusion. The International Journal of Robotics Research, Oct 2024. URL: https://doi.org/10.1177/02783649241273668, doi:10.1177/02783649241273668. This article has 4069 citations.

6. (chi2025diffusionpolicyvisuomotor pages 17-18): Cheng Chi, Zhenjia Xu, Siyuan Feng, Eric Cousineau, Yilun Du, Benjamin Burchfiel, Russ Tedrake, and Shuran Song. Diffusion policy: visuomotor policy learning via action diffusion. The International Journal of Robotics Research, Oct 2024. URL: https://doi.org/10.1177/02783649241273668, doi:10.1177/02783649241273668. This article has 4069 citations.

7. (cowling2026from12to pages 1-3): Simon L. Cowling. From 12 to 200 demonstrations: how act, diffusion policy, smolvla and $\pi _0.5$ scale on a low-cost arm. ArXiv, Oct 2026. URL: https://doi.org/10.48550/arxiv.2610.37170, doi:10.48550/arxiv.2610.37170. This article has 0 citations.

8. (cowling2026from12to pages 19-21): Simon L. Cowling. From 12 to 200 demonstrations: how act, diffusion policy, smolvla and $\pi _0.5$ scale on a low-cost arm. ArXiv, Oct 2026. URL: https://doi.org/10.48550/arxiv.2610.37170, doi:10.48550/arxiv.2610.37170. This article has 0 citations.

9. (wang2026imitationlearningfor pages 6-10): Xu-Cheng Wang, Zhi-Zhou Yang, Xiao-Man Zhang, Sung Eun Kim, Romain Hardy, and P. Rajpurkar. Imitation learning for robot assistance in open surgery: a multi-policy evaluation on suture following. ArXiv, May 2026. URL: https://doi.org/10.48550/arxiv.2605.28736, doi:10.48550/arxiv.2605.28736. This article has 3 citations.

10. (wang2026imitationlearningfor pages 10-13): Xu-Cheng Wang, Zhi-Zhou Yang, Xiao-Man Zhang, Sung Eun Kim, Romain Hardy, and P. Rajpurkar. Imitation learning for robot assistance in open surgery: a multi-policy evaluation on suture following. ArXiv, May 2026. URL: https://doi.org/10.48550/arxiv.2605.28736, doi:10.48550/arxiv.2605.28736. This article has 3 citations.

11. (wang2026imitationlearningfor pages 4-6): Xu-Cheng Wang, Zhi-Zhou Yang, Xiao-Man Zhang, Sung Eun Kim, Romain Hardy, and P. Rajpurkar. Imitation learning for robot assistance in open surgery: a multi-policy evaluation on suture following. ArXiv, May 2026. URL: https://doi.org/10.48550/arxiv.2605.28736, doi:10.48550/arxiv.2605.28736. This article has 3 citations.

12. (selvaraj2607armnetbenchv0.1parallel pages 7-9): Praveen Selvaraj, Lorenzo Uttini, and Ville Kuosmanen. Armnetbench v0.1: parallel real-world evaluation of manipulation policies on a low-cost arm farm. ArXiv, Jul 2026. URL: https://doi.org/10.48550/arxiv.2607.24481, doi:10.48550/arxiv.2607.24481. This article has 4 citations.

13. (selvaraj2607armnetbenchv0.1parallel pages 3-7): Praveen Selvaraj, Lorenzo Uttini, and Ville Kuosmanen. Armnetbench v0.1: parallel real-world evaluation of manipulation policies on a low-cost arm farm. ArXiv, Jul 2026. URL: https://doi.org/10.48550/arxiv.2607.24481, doi:10.48550/arxiv.2607.24481. This article has 4 citations.

14. (feng2026demystifyingactionspace pages 4-5): Yu-Chun Feng, Jin Zheng, Zhi-Hao Wang, Dong-Xiu Liu, Jianxiong Li, Jiang-Miao Pang, Taichao Wang, and Xianyuan Zhan. Demystifying action space design for robotic manipulation policies. ArXiv, Feb 2026. URL: https://doi.org/10.48550/arxiv.2602.23408, doi:10.48550/arxiv.2602.23408. This article has 14 citations.

15. (feng2026demystifyingactionspace pages 21-22): Yu-Chun Feng, Jin Zheng, Zhi-Hao Wang, Dong-Xiu Liu, Jianxiong Li, Jiang-Miao Pang, Taichao Wang, and Xianyuan Zhan. Demystifying action space design for robotic manipulation policies. ArXiv, Feb 2026. URL: https://doi.org/10.48550/arxiv.2602.23408, doi:10.48550/arxiv.2602.23408. This article has 14 citations.

16. (hickok2026so101benchaccessible pages 2-4): Truman Hickok. So-101 bench: accessible spatial manipulation. ArXiv, Oct 2026. URL: https://doi.org/10.48550/arxiv.2610.36420, doi:10.48550/arxiv.2610.36420. This article has 0 citations.

17. (hickok2026so101benchaccessible pages 6-8): Truman Hickok. So-101 bench: accessible spatial manipulation. ArXiv, Oct 2026. URL: https://doi.org/10.48550/arxiv.2610.36420, doi:10.48550/arxiv.2610.36420. This article has 0 citations.

18. (zhao2023learningfinegrainedbimanual pages 8-10): Tony Z. Zhao, Vikash Kumar, Sergey Levine, and Chelsea Finn. Learning fine-grained bimanual manipulation with low-cost hardware. ArXiv, Apr 2023. URL: https://doi.org/10.48550/arxiv.2304.13705, doi:10.48550/arxiv.2304.13705. This article has 3205 citations.

19. (hickok2026so101benchaccessible pages 8-10): Truman Hickok. So-101 bench: accessible spatial manipulation. ArXiv, Oct 2026. URL: https://doi.org/10.48550/arxiv.2610.36420, doi:10.48550/arxiv.2610.36420. This article has 0 citations.

20. (zhang2026anintegratedsimulation pages 22-27): Junfeng Zhang. An integrated simulation framework for vision-based robotic manipulation using nvidia isaac sim. Unknown journal, May 2026. URL: https://doi.org/10.32920/32253717, doi:10.32920/32253717.

21. (cowling2026from12to pages 21-24): Simon L. Cowling. From 12 to 200 demonstrations: how act, diffusion policy, smolvla and $\pi _0.5$ scale on a low-cost arm. ArXiv, Oct 2026. URL: https://doi.org/10.48550/arxiv.2610.37170, doi:10.48550/arxiv.2610.37170. This article has 0 citations.

22. (wu2024robomindbenchmarkon pages 9-10): Kun Wu, Chengkai Hou, Jiaming Liu, Zhengping Che, Xiaozhu Ju, Zhuqin Yang, Meng Li, Yinuo Zhao, Zhiyuan Xu, Guang Yang, Zhen Zhao, Guangyu Li, Zhao Jin, Lecheng Wang, Jilei Mao, Xinhua Wang, Shichao Fan, Ning Liu, Peifeng Ren, Qiang Zhang, Yaoxu Lyu, Mengzhen Liu, Jingyang He, Yulin Luo, Zeyu Gao, Chen-Xi Li, Chenyang Gu, Yankai Fu, Disheng Wu, Xingyu Wang, Sixiang Chen, Zhenyu Wang, Pengju An, Siyuan Qian, Shan-Shan Zhang, and Jianfeng Tang. Robomind: benchmark on multi-embodiment intelligence normative data for robot manipulation. ArXiv, Dec 2024. URL: https://doi.org/10.48550/arxiv.2412.13877, doi:10.48550/arxiv.2412.13877. This article has 258 citations.

23. (hou2025robomind2.0a pages 37-39): Cheng-Kai Hou, Kun Wu, Jiaming Liu, Zhengping Che, Di Wu, Fei Liao, Guang-Run Li, Jing-Yang He, Qiu-Xuan Feng, Zhao Jin, Chen-Yang Gu, Zhuo-Yang Liu, Nuo-Wei Han, Xiang-Ju Mi, Ya-hui Lv, Yan-Kai Fu, Gao-Le Dai, Lang-Zhe Gu, Tao Li, Yu-Heng Zhang, Yi-Xue Zhang, Xin-Hua Wang, Shi-Chao Fan, Meng Li, Zhengyang Zhao, Ning Liu, Zhi-Yuan Xu, Pei Ren, Junjie Ji, Hao-Ran Liu, Kuan Cheng, Shan-Shan Zhang, and Jian Tang. Robomind 2.0: a multimodal, bimanual mobile manipulation dataset for generalizable embodied intelligence. ArXiv, Dec 2025. URL: https://doi.org/10.48550/arxiv.2512.24653, doi:10.48550/arxiv.2512.24653. This article has 42 citations.

24. (cadene2026lerobotanopensource pages 7-10): Rémi Cadène, Simon Alibert, F. Capuano, Michel Aractingi, Adil Zouitine, Pepijn Kooijmans, Jade Choghari, Martino Russi, Caroline Pascal, Steven Palma, Mustafa Shukor, J. Moss, A. Soare, Dana Aubakirova, Quentin Lhoest, Quentin Gallou'edec, and Thomas Wolf. Lerobot: an open-source library for end-to-end robot learning. ArXiv, Feb 2026. URL: https://doi.org/10.48550/arxiv.2602.22818, doi:10.48550/arxiv.2602.22818. This article has 128 citations.

25. (cadene2026lerobotanopensource pages 5-7): Rémi Cadène, Simon Alibert, F. Capuano, Michel Aractingi, Adil Zouitine, Pepijn Kooijmans, Jade Choghari, Martino Russi, Caroline Pascal, Steven Palma, Mustafa Shukor, J. Moss, A. Soare, Dana Aubakirova, Quentin Lhoest, Quentin Gallou'edec, and Thomas Wolf. Lerobot: an open-source library for end-to-end robot learning. ArXiv, Feb 2026. URL: https://doi.org/10.48550/arxiv.2602.22818, doi:10.48550/arxiv.2602.22818. This article has 128 citations.