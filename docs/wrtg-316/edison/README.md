# Edison Scientific queries for the WRTG 316 proposal

Raw answers from the eight [Edison Scientific](https://edisonscientific.com/) literature
queries asked for in [issue #64](https://github.com/vertical-cloud-lab/robot-arms/issues/64)
(WRTG-Proposal-1), kept verbatim so anyone can see what Edison said before a source was
checked or cited. The checked shortlist of sources is in [`selection.md`](selection.md).

Every task is `LITERATURE_HIGH` (`job-futurehouse-paperqa3-high`), submitted 2026-11-04 with
[`scripts/edison_6dof.py`](../../../scripts/edison_6dof.py), copied from byu-vcl.

| Directory | Question | Edison `task_id` | Status |
|---|---|---|---|
| `q1-field-development/` | Q1, how arms have been used in SDLs and how low-cost/open-source arms developed | `cdb6d84d-8b9a-4563-8ad9-747686d06a50` | submitted |
| `q2-repeatable-benchmarks/` | Q2, published benchmarks with industrial/research-arm results that we could rerun | `012eecd1-5e8f-4924-b308-1e0b1176aa4a` | submitted |
| `q3-low-cost-vs-industrial/` | Q3, measured low-cost vs industrial arm data | `beff3bc9-93ed-41dd-b459-94108c3f103e` | submitted |
| `q4-case-against/` | Q4, the case against low-cost arms in lab automation | `bd7bc674-13bb-4049-9242-3f1b303e1a8e` | submitted |
| `q5-lab-workflows/` | Q5, arms swapping modules or tools on lab instruments; AprilTag and wrist-camera accuracy | `3d2ee330-007d-4964-a7a7-e1dc435d0232` | submitted |
| `q6-reliability-statistics/` | Q6, reporting success rates, CIs, and trial counts | `dba83992-ac2a-4033-953b-a7ee7536d01c` | submitted |
| `q7-learned-vs-scripted/` | Q7, imitation learning vs scripted motion on low-cost arms | `c3400c3a-ec4a-4b17-808a-0bf9b164d809` | submitted |
| `q8-visualizing-repeatability/` | Q8 (lower priority), 3D views of positioning accuracy and repeatability | `dd9b8553-a779-4e70-9080-8045fd091ff7` | submitted |

Each directory holds `query.md` (the exact text sent) and `_task_id.json`, and after the fetch
`answer.md`, `formatted_answer.md` (answer plus reference list), `raw_answer.md`,
`references.md`, `task.json`, `environment_frame.json` (the full trajectory state, which is where
the answer lives) and the other answer fields as `.json` (`contexts.json` holds the passages
Edison quoted).

## What each query says

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

## Why no question was skipped

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

## Reproducing

```bash
python scripts/edison_6dof.py submit   <slug> <prompt-file>     # LITERATURE_HIGH
python scripts/edison_6dof.py wait-all <slug> [<slug> ...]      # one blocking call; fetches each
python scripts/edison_6dof.py fetch    <slug>                   # answer + all artifacts
```

Never run `wait` or `wait-all` in the background on GitHub Actions; the runner is destroyed when
the final comment is posted.
