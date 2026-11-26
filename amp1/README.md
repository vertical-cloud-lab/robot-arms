# AMP1 ("On Agentic Manipulation Policies", Apple 2026) on a CPU runner and a simulated PiPER

For [#85](https://github.com/vertical-cloud-lab/robot-arms/issues/85): explore
[apple-aiml-research.github.io/ml-amp](https://apple-aiml-research.github.io/ml-amp/), reproduce what
can be reproduced, then try it on this repo's tasks. Nothing here talks to the real arm.

## What AMP1 is

[Paper (arXiv 2611.09892, v4, 31 pp)](https://arxiv.org/abs/2611.09892) ·
[code (apple-aiml-research/ml-amp)](https://github.com/apple-aiml-research/ml-amp).

A frontier model (Gemini 4 Argon or Claude Opus 5.5) is the controller. It doesn't output actions.
It writes Python in a **persistent kernel** against a robot SDK, looks at camera images when its code
calls `show()`, and decides the next step from what happened:

- **Sensing:** `observe()`, `rgb()`, `depth()`, `cloud()`, the camera calibration, and the robot's own
  description (joints, limits, gripper, TCP axes).
- **Perception:** depth-only segmentation of a fused point cloud into tracked objects (`objects()`).
  The model checks it against the images and edits it (`segment`, `define_object`,
  `forget_object`). It can also draw on real images (`annotate`) and render any view (`render`,
  `closeup`, `render_plan`).
- **Motion:** timed TCP waypoints with gripper commands. The harness interpolates them (min-jerk),
  solves damped-least-squares IK at each control step, and refuses a trajectory with a reason
  (`unreachable`, `velocity`, `joint_limit`, `singular`, held-object `collision`). `check_batch`
  tests arm-vs-scene collisions with sphere models.
- **No skills:** the basic harness has no grasp, place or push function. The model writes its own,
  anew each episode. An "assistive" harness adds them, and it helps weaker models but *hurts*
  Opus 5.5 and Gemini 4 Argon (up to −7.5 points).
- **Pause while thinking:** the simulator pauses while the model reasons, so only executed motion
  counts against the step budget.

Reported results:

| Benchmark | AMP1 | Best non-agent baseline |
|---|---|---|
| RoboLab-120 (Isaac Sim, 1,200 eps per instruction set) | **85.6%** Gemini 4 Argon, **82.8%** Opus 5.5 | 49.2% VLA, 42.9% WAM |
| CaP-Gym LIBERO-PRO (3,000 eps) | **95.2%** | π0.5 34.9% |
| CaP-Gym robosuite (700 eps) | **100%** Gemini, 98.4% Opus 5.5 | human-written programs 82.6% |
| CaP-Gym BEHAVIOR-1K (50 eps) | 96.0% | |
| RoboDojo, bimanual, RGB-only, no calibration | 26.4% zero-shot → **84.1%** with a persistent memory after practice | |
| Real world: Franka FR3 + Robotiq 2F-85 + 3 ZED cams, 12 tasks × 9 trials | **104/108** (Opus 5.5) | FLUX 3 Action 49/108, π0.5 30/108 |

Other findings:

- The model matters most: on RoboLab, Opus 5.5 82.8%, Haiku 5.5 51.6%, Opus 4.5 35.2%.
- More reasoning effort helped every model.
- Opus 5.5 copes with missing sensing: no depth 81.1%; no depth and no calibration 75.8%. It
  triangulates, and it self-calibrates the wrist camera from images taken at known gripper poses.
- Text descriptions instead of images collapse to 36.8%.
- It's slow. A real-world success averaged **280 s**: 69 s of motion and 211 s of reasoning.

Emergent behaviours with no prompt or skill for them:

- searching under occluders;
- using a spoon or spatula as a tool;
- pushing a bowl over a bin's edge to make it graspable;
- inferring an unseen shelf from a blocked motion;
- correcting a miscalibrated camera from commanded-vs-seen gripper motion.

### What a full reproduction needs (and why this runner can't)

- **Hardware:** Linux x86_64 with NVIDIA GPUs. The paper ran simulation on 8×H100 with driver 580,
  and RoboLab needs about 9 GB of VRAM per episode plus Isaac Sim 5.0. RoboLab, RoboDojo and
  BEHAVIOR-1K are Isaac Sim, so they need the GPU.
- **A model API key:** `ANTHROPIC_API_KEY` or `GEMINI_API_KEY`, or a self-hosted open-weights
  server. AMP's agent loop calls the model over the provider's API.
- **This runner:** 4 CPUs, 15 GB RAM, **no GPU** and **no model API key**. Its only Claude
  access is Claude Code's own login.

## What was run here

1. **AMP itself, unchanged.** `uv sync --frozen` works on this runner (Python 3.11). The robot
   server, the `amp1_basic` harness and SDK, perception, IK/planning and the collision model all run
   on CPU.
2. **CaP-Gym's two MuJoCo families on CPU: robosuite and LIBERO-PRO.** Both are installed exactly
   as [docs/capgym.md](https://github.com/apple-aiml-research/ml-amp/blob/main/docs/capgym.md)
   says: CaP-X at its pin, the Python 3.10 robosuite venv, and the Python 3.12 LIBERO-PRO venv with
   its dataset. They render through Mesa's EGL (llvmpipe) instead of an NVIDIA driver, and nothing
   in AMP or CaP-X was patched.
   - **robosuite:** `cube_lifting` loads through AMP's own adapter
     (`amp.robots.capgym.official_robosuite`) in 15 s, and `observe()` takes about 90 ms.
     [`capgym/env.sh`](capgym/env.sh) holds the environment the link client runs in.
   - **LIBERO-PRO:** set up by [`capgym/libero_setup.sh`](capgym/libero_setup.sh), docs steps 2, 4
     and 5. The dataset's `SHA256SUMS` check passed. `mv` refused exactly the 2 + 6 directories the
     docs call expected, those directories matched LIBERO-PRO's own copies, and the checkout stayed
     clean. [`capgym/env_libero.sh`](capgym/env_libero.sh) holds the client's environment. The
     catalog lists all 60 tasks (`libero_{object,goal,spatial}_{swap,task}.00`–`.09`, 50 initial
     states each).
   - **BEHAVIOR-1K** needs Isaac Sim and a GPU, so it wasn't attempted.
3. **The PiPER inside AMP's harness** ([`piper/piper_sim.py`](piper/piper_sim.py)).
   - The adapter wraps MuJoCo Menagerie's `agilex_piper` and declares an AMP embodiment: 6 joints,
     the 70 mm parallel jaw, the TCP 115 mm past `link6`, closing along `y` and approaching along `z`.
   - It sends the kinematic chain exported from the MJCF. AMP builds FK/IK and collision spheres
     from that chain itself.
   - Cameras: two RGB-D scene cameras over the shoulders and an RGB-D wrist camera.
   - AMP's robot server and SDK run it without changes, the same way they run CaP-Gym's Panda or
     RoboDojo's ARX arms.
4. **A Claude agent as the model.** With no API key, AMP's agent loop can't call a model.
   [`piper/kernel_bridge.py`](piper/kernel_bridge.py) gives a Claude Code agent AMP1's tools
   instead:
   - a persistent kernel with `rh`, `ep`, `np`, `Image` and `show` preloaded;
   - images saved and viewed;
   - `finish_episode`;
   - the budget line after every result.

   Each episode's agent was a fresh Opus 5.5 instance, the model behind AMP1's real-world results.
   Its system prompt was [`compose_prompt.py`](piper/compose_prompt.py)'s output: a short preamble
   mapping the tools, then AMP1's own `prompts/amp1.md` and the `amp1_basic` SDK reference,
   verbatim. The instruction came only through `ep.observe()`.

### Differences from the paper's setup (read before comparing numbers)

- **One episode per task, not 10 to 100.** These are anecdotes, not success rates.
- **The model is called through Claude Code, not the API,** at Claude Code's default settings. The
  paper used `--reasoning high`. Images are viewed with a tool call, not attached to the tool result.
- **No bubblewrap sandbox and no gateway.** The kernel talks to the robot server directly
  (`Episode(worker_url=...)`). The information policy ("don't read the simulator") was a rule in
  the prompt, and the transcripts were audited afterwards.
- **PiPER tasks are new scenes,** not RoboLab's. Depth is exact and the cameras are calibrated, as
  in the paper's simulation runs.
- **Two runs, one runner each.** The first run (2026-11-25) ran nine episodes before it ran out of
  model credits. Its runner was then discarded, so its recorded frames and the simulator's result
  files were lost. Each of its episodes keeps the policy's report, every code cell with its output,
  the key images and the final frame, plus the score recorded at the time. The second run
  (2026-11-26) rebuilt everything from these instructions and ran the remaining episodes. They
  keep their motion videos, the simulator's own result and ground-truth files, and an
  [`audit.json`](piper/audit.py). The audit checks that each of the agent's tool calls stayed in
  its episode folder and that no kernel cell touched files or simulator internals.
- **LIBERO-PRO ran from a copy of the pinned CaP-X checkout.** It was built while a robosuite
  episode was running from the original. The two venvs editable-install into the same checkout, and
  the docs warn never to build them side by side. The copy is at the same commits as the original,
  and `git status` shows nothing in it but the dataset's untracked files.

## Results

One episode per task. Every policy was a fresh Opus 5.5 agent given only AMP1's prompt and SDK
reference; it got the instruction from `ep.observe()`. **Scored** is the simulator's own check: CaP-X's
for the CaP-Gym tasks, and [`piper_sim.py`](piper/piper_sim.py)'s `success()` for the PiPER tasks.
[`results/summary.json`](results/summary.json) has every row.
**Belief** is what the agent reported before it saw any score. **Cells** counts `python(code)` calls, from the kernel's transcript, not the agent's own count,
roughly the paper's "model calls". Each episode folder in [`results/`](results/) has the agent's
report, every code cell it ran with its output (`transcript.jsonl`), and its key images.

### CaP-Gym robosuite: the paper's benchmark, its own scenes and checks

| Task | Robot | Instruction | Scored | Belief | Steps used | Cells | Wall |
|---|---|---|---|---|---|---|---|
| [`cube_lifting`](results/capgym_cube_lifting-ep0/) | Panda | pick up the red cube and lift it. | ✅ | success | 251 / 1500 | 14 | 6 min |
| [`cube_stack`](results/capgym_cube_stack-ep0/) | Panda | Pick up the red cube and gently stack it on top of the green cube, then release it. | ✅ | success | 463 / 1500 | 18 | 8 min |
| [`cube_restack`](results/capgym_cube_restack-ep0/) | Panda | Gently place the red cube on top of the green cube and then open the gripper. Nothing should be dropped from a height. | ✅ | success | 581 / 1500 | 31 | 9 min |
| [`spill_wipe`](results/capgym_spill_wipe-ep0/) | Panda + wiper (no fingers) | wipe up the 'brown spill'. | ✅ | success | 587 / 4000 | 16 | 11 min |
| [`two_arm_lift`](results/capgym_two_arm_lift-ep0/) | two Pandas | The two arms should coordinate to lift a pot. … | ✅ | success | 267 / 5000 | 23 | 12 min |
| [`nut_assembly`](results/capgym_nut_assembly-ep0/) | Panda | grasp and insert the `brown square nut` onto the `brown square block`. | ✅ | success | 459 / 900 | 33 | 22 min |
| [`two_arm_handover`](results/capgym_two_arm_handover-ep0/) | two Pandas | Arm 0 should pick up the hammer, lift it, and hand it over to Arm 1. Arm 1 should then grasp the hammer handle (not hammer head). … | ✅ | success | 517 / 5000 | 29 | 23 min |

All seven robosuite tasks succeeded, one episode each. The paper reports 100% (Gemini 4 Argon) and
98.4% (Opus 5.5) over 700 robosuite episodes. Seven episodes can't confirm a rate, but in every task
here the policy did what the paper describes, with no skills supplied:

- it measured the table and objects from depth instead of trusting perception's boxes;
- it chose the wrist yaw by IK when the preview refused a half-turn;
- it judged the finger-sphere "contacts" geometrically;
- it found the table with the fingerless wiper from a 0.6 mm tracking shortfall;
- it found the pot's handles by colour after perception merged them into the pot;
- in the handover, it found that two top-down grips on a 19 cm handle put the two wrists into each
  other. Arm 0 held the hammer out along the line between the robots, and arm 1 came in tilted 45°
  and took the handle 2.6 cm from its end. It checked arm-to-arm clearance with both arms' collision
  spheres, because `check()` only tests against perceived objects. The instruction's "z between 0.15
  and 0.20" doesn't name a frame, so the policy read it in the robot's base frame and recorded the
  table-relative alternative in its report. CaP-X's check scored it a success.

### CaP-Gym LIBERO-PRO: the paper's headline CaP-Gym suite

LIBERO-PRO perturbs LIBERO so that a policy which memorised the demonstrations fails. *swap*
units move objects to new places; *task* units change the instruction while keeping the scene.
The paper reports AMP1 at 95.2% over 3,000 episodes, and π0.5 at 34.9%. Units were drawn with
`np.random.default_rng(85)` from all 60 tasks × 50 initial states, and run in the order drawn.
The Panda runs on CPU through AMP's `official` adapter, with the scene camera (`agentview`) and the
wrist camera.

| Unit (task, initial state) | Instruction | Scored | Belief | Steps used | Cells | Wall |
|---|---|---|---|---|---|---|
| [`libero_spatial_swap.02`, 34](results/capgym_libero_spatial_swap.02-ep34/) | Pick the akita black bowl from table center and place it on the plate | ✅ | success | 957 / 7990 | 28 | 18 min |
| [`libero_goal_swap.08`, 15](results/capgym_libero_goal_swap.08-ep15/) | Put the bowl on the plate | ✅ | success | 861 / 7990 | 22 | 14 min |
LIBERO_ROWS
- **Bowls wider than the gripper.** LIBERO's bowls are about 11 cm across, and the Panda opens to
  7.9 cm. Both bowl policies measured this from the cloud and pinched the rim instead.
  - One checked alignment first by projecting its fitted rim circle and planned fingertip points
    into the wrist image.
  - The other's bowl slid to a lip grip and hung about 15° tilted. That policy estimated the
    bowl's centre from the rim circle instead of the lowest points, and the bowl levelled on
    release 1.6 cm off the plate's centre.
- **Speed limits.** The harness refused the first, 3 s approach for exceeding joint speed limits,
  and the policy re-timed every move to the preview's `min_duration` (12.5 s for a 25 cm reach).
- **Held objects drop out of `objects()`.** Both policies found held objects in raw `ep.cloud()`
  points in a box under the TCP. After placing, perception merged the bowl with the plate, so they
  checked the result by fitting a circle to the points above the plate.
- **CPU cost.** LIBERO-PRO's scenes are heavier than robosuite's. On this 4-core runner a 13.5 s
  motion took over 2 minutes of wall clock, which one policy noticed and handled with longer cell
  timeouts and `ep.wait()`.

### The simulated PiPER: this repo's tasks

| Task | Instruction | Scored | Belief | Steps used | Cells | Wall |
|---|---|---|---|---|---|---|
| [`vial_in_rack`](results/vial_in_rack-ep0/) (#21) | Put the vial with the red cap into the empty slot of the blue rack | ✅ seated 1 mm from the slot centre, upright | success | 446 / 2250 | 34 | 16 min |
| [`banana_in_bowl`](results/banana_in_bowl-ep0/) (paper's demo) | Pick up the banana and place it in the bowl | ✅ with a caveat (below) | success | 359 / 1800 | 25 | 18 min |
| [`tape_to_shelf`](results/tape_to_shelf-ep0/) (#30), episode 0 | Pick up the green tape and place it on the black shelf | ❌ on the shelf, but the gripper never let go (re-scored, below) | unsure | 559 / 2250 | 52 | 32 min |
| [`tape_to_shelf`](results/tape_to_shelf-ep1/) (#30), episode 1 | Pick up the green tape and place it on the black shelf | ✅ flat on the shelf 1.4 mm from its centre, released | success | 303 / 2250 | 21 | 11 min |

- **`vial_in_rack`** is the most instructive episode.
  - The 2.5 mm pocket clearance was smaller than the simulated PiPER's tracking error. Each joint stops
    short of its command, about 3 mrad on J1–J3, 6 on J4 and 30 on J5/J6. That is exactly
    `frictionloss`/`kp` in the Menagerie model (0.3/80, 0.3/40, 0.3/10).
  - The agent measured those deadbands from images and joint readings and overshot each command by its
    deadband. It came in from the robot's side of the rack so the hanging vial wouldn't drag through the
    seated ones, and it inserted to within 0.5 mm.
  - Nothing in the prompt mentions calibration. It is the same behaviour as the paper's real-robot
    calibration fixes, here against an actuator error rather than a camera error.
- **`banana_in_bowl`** is scored a success, but the banana leans out of the bowl. My banana model is
  about 20 cm long and my bowl's rim about 15 cm across, so no placement fits it fully inside. The agent
  worked that out before placing ("compare object length with the container's inner rim diameter"). It
  planned the resting configuration, one end on the bowl floor and the other leaning on the far rim, and
  released 5 mm above it after correcting an 8 mm sag under load. Fix the scene before reusing this task.
- **`tape_to_shelf`, episode 0, is the one miss**, and the agent's own report says why:
  - The 9 cm ring is wider than the gripper, so it gripped the 1.2 cm wall with one finger inside the
    hole.
  - Closing rotated the ring about 35° in the grip. The 13.5 mm gap against 12 mm expected, and the
    wrist images, showed it, but it carried on instead of re-gripping.
  - On release, the inner finger swung into the narrow part of the hole and jammed. Six ways of freeing
    it failed.
  - Two things in this sim may make the jam worse than reality: a ring built from 28 box segments, and a
    gripper that can only be commanded fully open or fully closed.
  - The first run's success check didn't require a release, so it scored this as a success. A person
    wouldn't. `success()` now also requires zero contacts between the object and the gripper
    (`link6`, `link7`, `link8`) for all three PiPER tasks. Under that check this episode is a
    failure, and the table says so. Its final state wasn't kept, so it was re-scored from the
    agent's own diagnosis and final frame (fingers locked in the ring's wall), not re-run. The
    other two PiPER episodes' final frames show the gripper open and clear of the object.
- **`tape_to_shelf`, episode 1** (a new scene: the tape and shelf moved by the episode's seed) was
  scored by the fixed check and **succeeded**: placed, zero gripper contacts, gripper open.
  - The policy found the problem the first episode never reached. On this PiPER a straight-down
    gripper can't hold the ring above the 8 cm shelf: `ik_batch` scans put the highest top-down TCP
    at z ≈ 0.09 m at x = 0.40 m and none at x = 0.50 m, against z ≈ 0.11 m needed. Joint 5 is
    limited to ±70°.
  - It tilted the approach 25° forward and pinched the ring's wall at its ±y side, where the
    closing axis stays horizontal and normal to the wall under that tilt. It kept the same
    orientation from grasp to release, so the ring stayed level.
  - After the lift it measured the ring's offset from the TCP in the point cloud and aimed the
    ring's centre at the shelf's. The ring landed 1.4 mm from the centre, and the arm then opened
    and retracted.
  - 21 code cells, 303 of 2,250 steps (20 s of motion), 11 minutes. Its
    [report](results/tape_to_shelf-ep1/report.json) has the IK scans and five lessons.

### Cost and speed

- **Agent work:** each agent took 6–32 minutes of wall clock and roughly 100k–300k tokens. The
  second run's agents used 125k–200k tokens each.
- **Simulated motion:** 13–48 s per episode. The paper's real-world average was 69 s of motion and
  211 s of reasoning.
- **What the time went to:** for robosuite and the PiPER, almost all of the wall clock was the model
  reading images and writing code. One PiPER control step with three 640×480 RGB-D renders takes
  about 0.2 s. LIBERO-PRO is the exception: on CPU its motion ran several times slower than real
  time, with 13.5 s of motion taking over 2 minutes.

### Toward the real PiPER

What carries over:

- **Embodiment:** AMP's embodiment contract fits the PiPER as is, and the description in `piper_sim.py`
  is the arm's own URDF via MuJoCo Menagerie. Its joint zeros and limits are `piper_sdk`'s: J2 0–180°,
  J3 −170–0°, and the parked arm reads about 0 on both (`arm_home.json`).
- **Actions:** AMP's action is six absolute joint targets plus a 0/1 gripper command every
  `control_dt`. A real backend would send what `Up_and_Down.py` and the teleop follower already send:
  `MotionCtrl_2(0x01, 0x01, speed, 0x00)`, then `JointCtrl(*[round(deg * 1000)])`, plus
  `GripperCtrl(gripper_angle=round(mm * 1000))`. It would run under `arm_power.py run` so the
  relay/`can0` protocol and the parking checks stay in force.

What has to change first:

- **Gripper.** The lab's sleeved gripper reads 45.6 mm touching and 108.6 mm open, not 0–70 mm, so the
  `GripperSpec` (stroke, `max_width_m`, `closed_empty`, `held_below`) and the finger geometry need
  re-measuring. Enable joints 1–6 one at a time, never `EnablePiper()`, which sends this gripper hunting
  for its zero.
- **Cameras.** AMP1 expects RGB-D with calibration. The cell has RGB Pi cameras: the HQ camera on the
  gripper Pi, plus the fixed camera Pis. The paper's `rgb_only` and `no_calibration` overlays still
  reached 75.8% with Opus 5.5 on RoboLab, by triangulating and self-calibrating the wrist camera from
  known gripper poses. Adding a depth or stereo camera, or the fiducial calibration from #21/#24, would
  help more.
- **Collision model.** The paper's main real-world failure was collisions with hardware the model
  didn't include: mounts, cables, the table. The gripper-Pi pod and its cable belong in the PiPER
  description before any real motion.
- **Error recovery.** The paper added SDK calls to read the arm's state and recover after the Franka's
  collision reflex. The PiPER equivalents are `GetArmStatus` and re-enabling joints 1–6.
- **Tracking error.** If the real arm stops short of its commands the way this model does, AMP1
  compensated for it here. That should be measured on the real arm before relying on it.
- **Reach for #30.** The tape episodes found that this model's top-down gripper can't hold a part
  above an 8 cm shelf 0.43 m out, because joint 5 stops at ±70°. The real arm is no better: the
  teleop follower's envelope uses J5 ±70°, and its firmware allows −75° to 76°
  ([`follower.py`](../PiPER%20Sandbox%20Scripts/Teleoperation/follower.py)). A tilted approach
  worked. Check the real cell's shelf height and distance against that before planning top-down
  placements.
- **A model API key** (`ANTHROPIC_API_KEY`) for AMP's own loop, or this repo's bridge.
- **Speed.** Expect minutes per task.

None of this was tried on the arm. This request didn't say the workspace is clear.

## Files

| Path | What it is |
|---|---|
| `piper/piper_sim.py` | The PiPER as an AMP `SimAdapter`: scene builder, embodiment, exported chain, cameras, tasks, scoring |
| `piper/piper_link.py` | Runs the adapter as AMP's link client (`amp.robots.capgym.client.run_benchmark`) |
| `piper/stack.py` | AMP's robot server with the `amp1_basic` config + the link client; queues an episode |
| `piper/episode_up.sh` | One PiPER episode end to end: server, link client, kernel bridge, the agent's `py` and `finish_episode` commands |
| `piper/capgym_up.sh` | The same for a CaP-Gym robosuite task, with CaP-X's own env through AMP's official adapter |
| `piper/kernel_bridge.py` | AMP1's tool surface for a Claude Code agent |
| `piper/compose_prompt.py` | The agent's system prompt: preamble + AMP1's prompt + SDK reference |
| `piper/capgym_next.sh` | Queues the next CaP-Gym episode on a running stack |
| `piper/recorder.py` | Saves a camera's frames from the robot server, for videos |
| `piper/summarize.py` | One row per finished episode (cells, steps, belief, the simulator's score) and its motion video |
| `piper/collect.py` | Copies an episode's report, transcript, key images and final frame into `results/` |
| `piper/audit.py` | Checks a policy agent's tool calls and kernel cells against the information policy |
| `piper/playlist.py`, `piper/make_video.py` | The compilation video: motion clips, or the policy's own images where frames weren't kept |
| `piper/sdk_smoke.py` | A scripted SDK check (not a policy) |
| `capgym/env.sh`, `capgym/install_env.sh`, `capgym/smoke.py` | The CaP-X robosuite environment and smoke test for this runner |
| `capgym/libero_setup.sh`, `capgym/env_libero.sh` | The CaP-X LIBERO-PRO venv, dataset and config, and its client environment |
| `results/summary.json` | Every episode's row: instruction, cells, steps, wall time, belief, score (and re-score) |

## Running it

```bash
# AMP (Python 3.11 venv) and the PiPER model
curl -LsSf https://astral.sh/uv/install.sh | sh
git clone https://github.com/apple-aiml-research/ml-amp /tmp/ext/ml-amp && (cd /tmp/ext/ml-amp && uv sync --frozen)
uv pip install --python /tmp/ext/ml-amp/.venv/bin/python mujoco imageio-ffmpeg
git clone --depth 1 --filter=blob:none --sparse https://github.com/google-deepmind/mujoco_menagerie /tmp/ext/menagerie/mujoco_menagerie
git -C /tmp/ext/menagerie/mujoco_menagerie sparse-checkout set agilex_piper
sudo apt-get install -y libegl1 libegl-mesa0          # MuJoCo renders through Mesa EGL on CPU
cp amp1/piper/*.py amp1/piper/*.sh /tmp/amp-piper/      # the scripts expect /tmp/amp-piper
/tmp/amp-piper/episode_up.sh tape_to_shelf 8766 0       # server + link client + kernel; prints the episode dir
python /tmp/amp-piper/compose_prompt.py /tmp/amp-episodes/tape_to_shelf-ep0 45
# then give an agent the system prompt in that directory; it acts with ./py and ./finish_episode

# CaP-Gym: CaP-X at its pin, then the robosuite venv (docs/capgym.md step 3)
(cd /tmp/ext/ml-amp && make capx-sim)
source amp1/capgym/install_env.sh && uv python install 3.10 && uv venv $C/venv-robosuite --managed-python --python 3.10
(cd $X && VIRTUAL_ENV=$C/venv-robosuite uv sync --frozen --active --extra robosuite)
mkdir -p /tmp/capgym_test && cp amp1/capgym/env*.sh /tmp/capgym_test/
/tmp/amp-piper/capgym_up.sh two_arm_handover 8772 0 capgym_robosuite_two_arm_handover agentview
# LIBERO-PRO: its venv, dataset and config (steps 2, 4, 5), then one unit (task, initial state)
amp1/capgym/libero_setup.sh
/tmp/amp-piper/capgym_up.sh libero_goal_swap.08 8774 15 capgym_libero agentview /tmp/capgym_test/env_libero.sh
```

With an `ANTHROPIC_API_KEY`, AMP's own loop can drive the same robot server instead of the bridge.
