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
2. **CaP-Gym robosuite family on CPU**, installed exactly as
   [docs/capgym.md](https://github.com/apple-aiml-research/ml-amp/blob/main/docs/capgym.md)
   says, with CaP-X at its pin and the Python 3.10 venv. It renders through Mesa's EGL
   (llvmpipe) instead of an NVIDIA driver, and nothing in AMP or CaP-X was patched.
   `cube_lifting` loads through AMP's own adapter (`amp.robots.capgym.official_robosuite`) in 15 s,
   and `observe()` takes about 90 ms. [`capgym/env.sh`](capgym/env.sh) holds the environment the
   link client runs in.
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

## Results

_Filled in below once the episodes finish._

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
| `piper/recorder.py` | Saves a camera's frames from the robot server, for videos |
| `piper/sdk_smoke.py` | A scripted SDK check (not a policy) |
| `capgym/` | The CaP-X robosuite environment and smoke test for this runner |

## Running it

```bash
# AMP (Python 3.11 venv) and the PiPER model
git clone https://github.com/apple-aiml-research/ml-amp /tmp/ext/ml-amp && (cd /tmp/ext/ml-amp && uv sync --frozen)
uv pip install --python /tmp/ext/ml-amp/.venv/bin/python mujoco imageio-ffmpeg
git clone --depth 1 --filter=blob:none --sparse https://github.com/google-deepmind/mujoco_menagerie /tmp/ext/menagerie/mujoco_menagerie
git -C /tmp/ext/menagerie/mujoco_menagerie sparse-checkout set agilex_piper
sudo apt-get install -y libegl1 libegl-mesa0          # MuJoCo renders through Mesa EGL on CPU
cp amp1/piper/*.py amp1/piper/*.sh /tmp/amp-piper/      # the scripts expect /tmp/amp-piper
/tmp/amp-piper/episode_up.sh tape_to_shelf 8766 0       # server + link client + kernel; prints the episode dir
python /tmp/amp-piper/compose_prompt.py /tmp/amp-episodes/tape_to_shelf-ep0 45
# then give an agent the system prompt in that directory; it acts with ./py and ./finish_episode
```

With an `ANTHROPIC_API_KEY`, AMP's own loop can drive the same robot server instead of the bridge.
