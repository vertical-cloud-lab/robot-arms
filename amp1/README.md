# AMP1 (Apple, "On Agentic Manipulation Policies") on a simulated PiPER

Work in progress for [#85](https://github.com/vertical-cloud-lab/robot-arms/issues/85).

[AMP1](https://apple-aiml-research.github.io/ml-amp/) ([arXiv 2611.09892](https://arxiv.org/abs/2611.09892),
[code](https://github.com/apple-aiml-research/ml-amp)) puts a frontier model in the control loop. The model
writes Python in a persistent kernel against a robot SDK and looks at camera images after every motion.
The SDK has sensing, a depth-based object model and timed TCP waypoints that the harness checks with IK
before it executes them. There are no grasp or place skills.

`piper/` plugs the lab's AgileX PiPER into AMP's own harness, unchanged. The robot is MuJoCo Menagerie's
`agilex_piper` model, with two scene cameras and a wrist camera, simulated on CPU. It plugs in through
AMP's backend interface (`SimAdapter`) and its link protocol:

| File | What it does |
|---|---|
| `piper/piper_sim.py` | The PiPER as an AMP `SimAdapter`: embodiment (6 joints, 70 mm parallel jaw, TCP 115 mm past the flange), kinematic chain exported from the MJCF, cameras (RGB-D), and three tasks |
| `piper/piper_link.py` | Runs the adapter as AMP's link client (`amp.robots.capgym.client.run_benchmark`) |
| `piper/stack.py` | Starts AMP's robot server with the `amp1_basic` harness config, starts the link client, and queues an episode |
| `piper/sdk_smoke.py` | A scripted check through the AMP1 SDK (`rh`/`ep`): observe, objects, annotate, render, preview, execute, IK, gripper |

Tasks:

| Task | Instruction | From |
|---|---|---|
| `banana_in_bowl` | Pick up the banana and place it in the bowl | the paper's demo task (RoboLab `BananaInBowlTask`) |
| `tape_to_shelf` | Pick up the green tape and place it on the black shelf | [#30](https://github.com/vertical-cloud-lab/robot-arms/issues/30) |
| `vial_in_rack` | Put the vial with the red cap into the empty slot of the blue rack | [#21](https://github.com/vertical-cloud-lab/robot-arms/issues/21) (vials into pockets with 2 mm clearance) |

Nothing here talks to the real arm.
