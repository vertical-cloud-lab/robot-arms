# Edison Scientific answers for issue #1 (6-DOF arms in self-driving labs)

Verbatim answers from [Edison Scientific](https://edisonscientific.com/) tasks asked for in
[issue #1](https://github.com/vertical-cloud-lab/robot-arms/issues/1), which began as byu-vcl issue #199. They are
archived for provenance, so anyone can see exactly what the model said before it was paraphrased or checked. Each
directory holds the query, `_task_id.json`, `answer.md`, `formatted_answer.md` (with references), `raw_answer.md`,
`references.md`, `task.json`, `environment_frame.json` (the full trajectory, which is where the answer lives) and the
remaining answer fields as JSON (`contexts.json` holds the passages Edison quoted). Same convention as
[`powder-doser/docs/edison/`](https://github.com/vertical-cloud-lab/powder-doser/tree/main/docs/edison).

All tasks are `LITERATURE_HIGH` (`job-futurehouse-paperqa3-high`), sent through `https://api.platform.edisonscientific.com`.
Within each round the queries are sequential: each one was written after the previous answer returned.

**Read the answers with their checks.** Edison's "no published evidence" statements and headline numbers have been
wrong often enough to matter. Examples: an arm already tended printers in a closed loop in 2020; A-Lab's numbers were
revised by a 2026 correction; and some results are from simulation, or are design targets. The checks against full
text are in [`../update-2026-11/verification.md`](../update-2026-11/verification.md), and the September ones in
byu-vcl's `docs/6dof-verification-and-ecosystem.md` on branch `claude/issue-199-20260915-0844`.

## November 2026 update (this folder, `u1-…` to `u8-…`)

Written for the [2026-11-28 request](https://github.com/vertical-cloud-lab/robot-arms/issues/1) and synthesized in
[`../update-2026-11/README.md`](../update-2026-11/README.md). Every query starts from a short description of the lab,
and says which earlier answers it must not repeat. "Back by" is when a poll first saw the task finished, so each one
finished up to a few minutes earlier.

| Directory | Question | Written against | Edison `task_id` | Sent (UTC) | Back by |
|---|---|---|---|---|---|
| `u1-future-work-then-and-now/` | Limitations and future work stated by central arm-SDL papers, and what has been done since | the 24 earlier answers | `84b03519-39a4-4e89-9264-3433875a6ce8` | 09:33 | ~10:05 |
| `u2-alloy-powder-workflow-automation/` | Automating the hands-on steps of a powder-metallurgy / AM alloy loop (workup, SEM prep, metallography, charge prep, NFPA 660) | the DAL survey | `41170e8f-3e49-41d1-8da1-4245942b8147` | 10:07 | ~10:28 |
| `u3-interventions-as-metric-and-data/` | Defining and counting interventions; interactive learning from them; remote supervision and latency; statistics for a campaign whose controller improves | U1's top-ranked gap | `27ec77e4-4be9-42f0-921e-f494da79b016` | 10:28 | ~10:47 |
| `u4-printer-tending-and-print-test-loops/` | Robotic print removal and plate swapping; design–print–test loops; plate-clear checks; print farms; forces for a low-cost arm | U1's printer-tending claim and its correction | `2dc50277-5f2f-4670-a077-5116abdb77eb` | 10:47 | ~11:04 |
| `u5-agent-written-code-and-designed-hardware/` | Agent-written robot code on lab hardware; safeguards; agent-designed fixtures; provenance; evaluation design | byu-vcl's AI for Science proposal, robot-arms #85/#87 | `f666c15c-8baf-44f4-b8c6-8b848fc95fdc` | 11:04 | ~11:31 |
| `u6-handling-times-and-restocking/` | Measured handling times; validated SDL twins; human decision latency; robots restocking consumables; time-study methods | byu-vcl's twin (#407), the future-work analysis | `6304f40d-d416-4f86-9176-0b108760f45a` | 11:32 | ~12:06 |
| `u7-cameras-that-verify-and-log/` | Vision and VLM outcome checks, automatic intervention logging, insertion verification, calibration drift, gating false-clear rates, lab-video privacy | U4's missing plate-check rate, project 1's logging burden | `0d3b4d1d-8287-4648-9600-b89152862ee0` | 12:07 | <!-- U7-BACK --> |
<!-- U8-ROW -->

## Earlier rounds

**September 2026, first arc (this folder, `q1-…` to `q4-…`).** Copied unchanged from
[`claude/issue-1-20261010-2326`](https://github.com/vertical-cloud-lab/robot-arms/tree/claude/issue-1-20261010-2326)
(98fb17c), which never got a PR.

| Directory | Edison `task_id` | Status |
|---|---|---|
| `q1-sota-arms-in-sdls/` | `85b13938-c944-4f68-8dc8-f452a9a073a2` | success (34 min) |
| `q2-metrology-and-reliability-methods/` | `cbb5a078-5411-4391-a29b-902196894bc5` | success (submitted 2026-09-08 17:15 UTC) |
| `q3-perception-lerobot-and-sandbox/` | `29bb1dbe-7037-44fd-9fa5-b4e88881953e` | success (submitted 2026-09-15 08:47 UTC, 29 min) |
| `q4-safety-autonomy-and-control-plane/` | `8ac9a19f-e3aa-4f2b-a0b7-50a8fe18e210` | success (submitted 2026-09-15 09:24 UTC, fetched 2026-10-10) |

**September 2026, second arc (on [PR #8](https://github.com/vertical-cloud-lab/robot-arms/pull/8)'s branch,
`claude/issue-199-20260915-0846`).** Its Q1 and Q2 are the same tasks as above.

| Directory on that branch | Edison `task_id` |
|---|---|
| `q3-grippers-and-end-effectors/` | `bccdc402-47d0-44c0-955c-85bca64f182d` |
| `q4-closed-loop-design-protocol/` | `80856303-053c-4b8c-b450-ccc0808273a7` |
| `q5-sandbox-object-set/` | `c1c66197-fee2-4c28-bde1-2bb4f2ad1433` |

**WRTG 316, November 2026** ([`../wrtg-316/edison/`](../wrtg-316/edison/)): eight queries on 2026-11-04 and nine on
2026-11-27, on arm selection, benchmarks, low-cost vs industrial arms, the case against, station calibration,
reliability statistics, learned vs scripted control and cost per task.

## Reproducing or resuming

[`scripts/edison_6dof.py`](../../scripts/edison_6dof.py) on `main` writes to `docs/wrtg-316/edison/` by default. Set
`EDISON_OUT_DIR=docs/edison-6dof` for this folder. `edison-client` 0.19 doesn't resolve on Python 3.14, so use a
3.12 environment. Never run `wait` in the background: the Actions runner is destroyed when the final comment posts.

```bash
python3.12 -m venv /tmp/edenv && /tmp/edenv/bin/pip install edison-client==0.19.0
export EDISON_OUT_DIR=docs/edison-6dof
/tmp/edenv/bin/python scripts/edison_6dof.py submit <slug> <prompt-file>
/tmp/edenv/bin/python scripts/edison_6dof.py wait   <slug> [interval-s] [budget-s]   # blocking, foreground
/tmp/edenv/bin/python scripts/edison_6dof.py fetch  <slug>
```

## Notes on the September first arc

Q4's three `create_artifact` tables are in `artifacts.json` and split out as
`artifact-00.md` (powder explosibility), `artifact-01.md` (standards and what binds a US
university), and `artifact-02.md` (the 90-day plan).

The queries are deliberately **sequential**: each follow-up is written against the
previous answer, so Q2 is not composed until Q1 returns.

## Planned query arc

1. **Q1 — SOTA + gap analysis.** Low-cost 6-DOF arms with eye-in-hand cameras as the
   manipulation layer of SDLs: what is deployed, arm-vs-gantry trade study, vision
   pipelines (fiducial vs. learned pose, transparent/specular labware), VLA foundation
   models for lab manipulation, reliability/remote operation, and a ranked list of
   timely contributions for a small lab. **(returned — see `q1-sota-arms-in-sdls/answer.md`)**
2. **Q2 — metrology and reliability methods.** How to execute Q1's two top-ranked gaps
   rigorously: ISO 9283 / ASME B89.4.22 pose-accuracy testing without a laser tracker,
   thermal drift protocols, reliability statistics and failure taxonomies for autonomous
   labs, existing manipulation benchmarks, venue strategy, and the minimum credible
   paper. *(submitted, seeded by Q1's ranking)*
3. **Q3–Q5 — remaining axes**, to be narrowed further: (a) transparent/specular labware pose estimation and
   grasping for glass vials, quartz crucibles, and metal powder; (b) hand-eye calibration
   and closed-loop visual servoing accuracy achievable on a sub-$5k arm with a custom
   wrist camera; (c) an arm as the sample-exchange layer closing the loop on an existing
   drop-tower / tensile / LPBF workflow; (d) safety and autonomy architecture for an arm
   operating unattended near furnaces and reactive powders under remote supervision.

## Reproducing / resuming

[`scripts/edison_6dof.py`](../../scripts/edison_6dof.py) has three subcommands. Never run
`wait` in the background — the GitHub Actions runner is destroyed the moment the final
comment is posted, which kills backgrounded processes.

```bash
python scripts/edison_6dof.py submit <slug> <prompt-file>   # LITERATURE_HIGH
python scripts/edison_6dof.py wait   <slug> [interval] [budget]
python scripts/edison_6dof.py fetch  <slug>                 # answer + artifacts
```
