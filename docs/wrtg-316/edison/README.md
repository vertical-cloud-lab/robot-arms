# Edison Scientific queries for the WRTG 316 proposal

Raw answers from two rounds of [Edison Scientific](https://edisonscientific.com/) literature
queries, kept verbatim so anyone can see what Edison said before a source was checked or cited:

- **Run 1** (this folder's `q1-…` to `q8-…`): the eight queries asked for in
  [issue #64](https://github.com/vertical-cloud-lab/robot-arms/issues/64) (WRTG-Proposal-1),
  2026-11-04.
- **Run 2** ([`run-2/`](run-2/)): the same request re-run on 2026-11-27 in
  [PR #90](https://github.com/vertical-cloud-lab/robot-arms/pull/90), with the context from
  `Proposal/user context/proposal questions.md` and a focus on the *automated manual
  manipulator*. See [Run 2](#run-2-2026-11-27-the-automated-manual-manipulator) below.

The checked shortlist of sources, drawn from both runs, is in [`selection.md`](selection.md).

## Run 1 (2026-11-04)

Every task is `LITERATURE_HIGH` (`job-futurehouse-paperqa3-high`), submitted 2026-11-04 between
00:22 and 00:23 UTC with
[`scripts/edison_6dof.py`](../../../scripts/edison_6dof.py), copied from byu-vcl. The
"fetched by" times come from the 2-minute poll, so each task finished up to two minutes earlier.

| Directory | Question | Edison `task_id` | Status |
|---|---|---|---|
| `q1-field-development/` | Q1, how arms have been used in SDLs and how low-cost/open-source arms developed | `cdb6d84d-8b9a-4563-8ad9-747686d06a50` | success, fetched by 00:45 UTC |
| `q2-repeatable-benchmarks/` | Q2, published benchmarks with industrial/research-arm results that we could rerun | `012eecd1-5e8f-4924-b308-1e0b1176aa4a` | success, fetched by 00:57 UTC |
| `q3-low-cost-vs-industrial/` | Q3, measured low-cost vs industrial arm data | `beff3bc9-93ed-41dd-b459-94108c3f103e` | success, fetched by 00:49 UTC |
| `q4-case-against/` | Q4, the case against low-cost arms in lab automation | `bd7bc674-13bb-4049-9242-3f1b303e1a8e` | success, fetched by 00:57 UTC |
| `q5-lab-workflows/` | Q5, arms swapping modules or tools on lab instruments; AprilTag and wrist-camera accuracy | `3d2ee330-007d-4964-a7a7-e1dc435d0232` | success, fetched by 00:57 UTC |
| `q6-reliability-statistics/` | Q6, reporting success rates, CIs, and trial counts | `dba83992-ac2a-4033-953b-a7ee7536d01c` | success, fetched by 00:53 UTC |
| `q7-learned-vs-scripted/` | Q7, imitation learning vs scripted motion on low-cost arms | `c3400c3a-ec4a-4b17-808a-0bf9b164d809` | success, fetched by 00:47 UTC |
| `q8-visualizing-repeatability/` | Q8 (lower priority), 3D views of positioning accuracy and repeatability | `dd9b8553-a779-4e70-9080-8045fd091ff7` | success, fetched by 00:47 UTC |

Each directory holds `query.md` (the exact text sent) and `_task_id.json`, and after the fetch
`answer.md`, `formatted_answer.md` (answer plus reference list), `raw_answer.md`,
`references.md`, `task.json`, `environment_frame.json` (the full trajectory state, which is where
the answer lives) and the other answer fields as `.json` (`contexts.json` holds the passages
Edison quoted).

### What each query says

Every query is: the context paragraph from the issue, a blank line, one question, a blank line,
the closing paragraph from the issue.

**Text lost from the issue.** Several lines of the issue body lost a run of characters in the
middle (for example "orresult", "detmber of trials", "industrntly measured"). Those lines were
filled in as below before submitting; the intact lines are verbatim. `query.md` in each
directory is what Edison received.

| Issue text | Sent as |
|---|---|
| "…2015 to 2026, and For each benchmark orresult, describe the protocol in enough detmber of trials, successcriterion, measuring tool) and githe arm model. For eachclaim, give the DOI and quote the sentports it. Say explicitly where no published evidence exi" | "…2015 to 2026, and flag any preprints. For each benchmark or result, describe the protocol in enough detail to repeat it (what is measured, number of trials, success criterion, measuring tool) and give the arm model. For each claim, give the DOI and quote the sentence that supports it. Say explicitly where no published evidence exists." |
| Q1 "How have-driving and automatedlaboratories, and how has the movurce arms developed?Include review articles, perspectimation, and thepublished systems…" | "How have robot arms been used in self-driving and automated laboratories, and how has the movement toward low-cost and open-source arms developed? Include review articles, perspectives on laboratory automation, and the published systems…" |
| Q3 "Low-cost vs industrntly measuredrepeatability, accuracy, payload, speed, bace and failure data exist for low-cost arms (AgileX PiPER,, WidowX), and how dothey compare with UR5e, Franka and si Separate measuredvalues from manufacturer datash of each arm wherereported." | "Low-cost vs industrial: What independently measured repeatability, accuracy, payload, speed, backlash, endurance and failure data exist for low-cost arms (AgileX PiPER, SO-100/SO-101, Koch, WidowX), and how do they compare with UR5e, Franka and similar arms? Separate measured values from manufacturer datasheet values, and give the price of each arm where reported." |
| Q4 "The case against: W that low-cost arms arenot suitable for laboratory automatity, safety, hiddenintegration and maintenance costs,  to industrial arms." | "The case against: What evidence or arguments show that low-cost arms are not suitable for laboratory automation (accuracy, reliability, durability, safety, hidden integration and maintenance costs) compared to industrial arms?" |
| Q7 "Learned vs scriptedhave imitation-learningpolicies (ACT, diffusion policy, Lrms, and how manydemonstrations did they need? How do they cial-guided motion on the same task?" | "Learned vs scripted: How well have imitation-learning policies (ACT, diffusion policy, LeRobot policies) performed on low-cost arms, and how many demonstrations did they need? How do they compare with scripted or fiducial-guided motion on the same task?" |
| Q8 "(lower priority) Vibility: What methods and software show a robot's positioningity in 3D (errorellipsoids, repeatability maps,ath), computed fromrobot parameters?" | "(Lower priority) Visualizing repeatability: What methods and software show a robot's positioning accuracy and repeatability in 3D (error ellipsoids, repeatability maps, error along a path), computed from measurements or robot parameters?" |

### Why no question was skipped

The issue asked to skip any question already covered by the byu-vcl answers in
`docs/edison-6dof/` on `claude/issue-199-20260915-0846` and `-0844` (the two branches hold the
same q1 and q2). Both overlap these questions only in part:

- [byu-vcl q1](https://github.com/vertical-cloud-lab/byu-vcl/blob/7fc56b6/docs/edison-6dof/q1-sota-arms-in-sdls/answer.md)
  (arms in SDLs, 2023–2026) tabulates the deployed systems that use arms (Dai 2024, Lunt 2024,
  Radulov 2026, Ada, A-Lab), cites the Lo 2024 frugal-twin review, and benchmarks VLAs. It doesn't
  cover the earlier systems, reviews and perspectives that defined the field or how low-cost arms
  developed (Q1), or ACT or diffusion-policy results and demonstration counts on low-cost arms
  (Q7). It marks its own AprilTag-accuracy and lab-task-tolerance figures as extrapolation (Q5)
  and finds no measured PiPER data (Q3).
- [byu-vcl q2](https://github.com/vertical-cloud-lab/byu-vcl/blob/7fc56b6/docs/edison-6dof/q2-metrology-and-reliability-methods/answer.md)
  (metrology and reliability methods) gives the zero-failure binomial bound, Weibull and
  renewal models, LabRobFail and SDL autonomy scales. It cites no statistics source for these,
  does not cover Wilson or Clopper-Pearson intervals or how lab papers report success rates (Q6),
  and lists ISO 9283, the NIST task boards and YCB without industrial-arm results to compare
  against (Q2).

## Run 2 (2026-11-27): the automated manual manipulator

Joshua asked in [PR #90](https://github.com/vertical-cloud-lab/robot-arms/pull/90) for the
issue #64 query to be re-run with the context from
[`proposal questions.md`](../Proposal/user%20context/proposal%20questions.md), focusing on the
*automated manual manipulator*: a robot arm that moves from station to station, calibrates
itself at each station with a calibration square, and takes on several new automated tasks.

Every task is `LITERATURE_HIGH` (`job-futurehouse-paperqa3-high`), submitted 2026-11-27 between
22:06:01 and 22:06:29 UTC with the same script and `EDISON_OUT_DIR=docs/wrtg-316/edison/run-2`.
As in run 1, the "fetched by" times come from a 2-minute poll.

| Directory | Question | From | Edison `task_id` | Status |
|---|---|---|---|---|
| `run-2/q1-field-growth/` | How arms are used as automated manual manipulators in SDLs (materials and biology), how fast lab automation is growing, the low-cost movement, where researchers and vendors disagree | Q1; questions 1.1, 1.2.3, 1.2.4 | `2c1f38b6-0a5e-437e-b9f2-48e567e74702` | success, fetched by 22:30 UTC |
| `run-2/q2-same-purpose/` | Has anyone published tests for evaluating or choosing an arm for this role? Is "automated manual manipulator" a term in use? | new; 1.3.1, 1.3.7 #1 | `17186b74-0000-4359-b673-d26bb83bde38` | success, fetched by 22:39 UTC |
| `run-2/q3-arm-categories-and-selection-metrics/` | Arm categories; the metrics used to choose or buy an arm; the authorities; datasheet vs measured values | new; 1.3.7 #2–3, 3.1.3, 3.1.6 | `30c7e5b8-3f78-4320-a86d-eb91fb6f1ff4` | success, fetched by 22:24 UTC |
| `run-2/q4-station-calibration/` | Systems that recalibrate at each station against a cube, square or fiducial; accuracy, protocol, time; AprilTag accuracy at working distance | new (the request's focus); absorbs Q5's AprilTag part | `fb9a39a6-15c8-4b58-ad1a-bb630ff4a986` | success, fetched by 22:37 UTC |
| `run-2/q5-repeatable-benchmarks/` | Published benchmarks with industrial/research-arm results that a low-cost arm could rerun | Q2 | `3f54576d-62d4-4547-bad3-5049860e404d` | success, fetched by 22:32 UTC |
| `run-2/q6-low-cost-vs-industrial/` | Measured low-cost vs industrial arm data | Q3 (unchanged) | `97f9cc66-cc99-4a80-a866-5a5113ff0002` | success, fetched by 22:24 UTC |
| `run-2/q7-case-against/` | The case against low-cost arms, now including station-to-station use | Q4 | `f2f7a48c-25cb-4556-a13b-57aa8490e669` | success, fetched by 22:41 UTC |
| `run-2/q8-reliability-and-cost-per-task/` | Reporting success rates and CIs; how cost per task, throughput or uptime have been measured | Q6; 1.4.5 | `9f4e317d-a41f-4911-83cf-da7756b59ab2` | success, fetched by 22:28 UTC |
| `run-2/q9-new-tasks-at-stations/` | One arm taking over several tasks at different instruments; tolerances; scripted, fiducial-guided or learned | Q5 + Q7 | `8ffd6c55-63b0-4fcd-a1ab-9742cb2a8044` | success, fetched by 22:30 UTC |

"From" gives the run-1 question (Q1 to Q8) and the numbered questions in `proposal questions.md`
that each query carries. Run 1's Q8 (3D visualization of repeatability) was not re-run: the issue
marked it lower priority, and the paper no longer collects its own data
(`proposal questions.md` 0.2 and 1.3.4).

### What changed in the queries

**The context paragraph** that opens every query was rewritten from `proposal questions.md`. It
keeps run 1's description of the arms and adds what the paper is now for (a literature review to
find the tests, 0.2 and 1.3.4), the automated manual manipulator and its station-to-station
calibration, the materials-science SDL (1.3.5) and cost per task (1.4.5). Personal details from
that file (name, course, graduate-school plans) were left out, since the search doesn't need
them. Every run-2 query starts with:

> We are writing a literature review to discover which tests determine the value of a robot arm used as an automated manual manipulator in a self-driving laboratory (SDL) for materials science. By automated manual manipulator we mean one arm that does the hands-on work a person would otherwise do: it moves from station to station (for example a pipetting gantry, a powder doser, a balance, vial and plate racks), recalibrates itself at each station using a calibration square (a square fiducial target such as an AprilTag, or a square fixture at a known position), and takes on several new automated tasks. The term is ours; the literature may say mobile manipulator, robotic laboratory assistant, robot chemist, or sample- or labware-handling robot. Our arms are a low-cost AgileX PiPER 6-DOF arm (about $2k) and SO-101 leader/follower arms (about $200), with parallel grippers, Raspberry Pi wrist cameras and fixed cameras in an enclosure, AprilTags, and LeRobot-style imitation learning or scripted motion. We want to place these arms in the published literature and find tests that we, or anyone validating an affordable arm, can repeat to compare it with the industry-standard arms used in SDLs (e.g. UR5e, UR3, Franka Panda, ABB YuMi, Kinova, KUKA), including on cost per task.

**The closing paragraph** (peer-reviewed sources from 2015 to 2026, flag preprints, protocol
detail, DOI and quote for each claim, say where no evidence exists) is run 1's, unchanged.

**Installing the client.** On the runner's Python 3.14, `pip install edison-client` resolved to
`edison-client` 0.11.1 with `fhlmi` 0.45.3 and `ldp` 1.11.0, which fail to import
(`No module named 'lmi.config'`). Pinning `ldp==0.45.3` fixed it; newer `edison-client` releases
need Python below 3.14.

## Reproducing

```bash
python scripts/edison_6dof.py submit   <slug> <prompt-file>     # LITERATURE_HIGH
python scripts/edison_6dof.py wait-all <slug> [<slug> ...]      # one blocking call; fetches each
python scripts/edison_6dof.py fetch    <slug>                   # answer + all artifacts
```

Run 2 sets `EDISON_OUT_DIR=docs/wrtg-316/edison/run-2` for all three commands.

Never run `wait` or `wait-all` in the background on GitHub Actions; the runner is destroyed when
the final comment is posted.
