"""Write EPISODE_DIR/SYSTEM_PROMPT.md: a short preamble on how AMP1's tools map onto this run,
then AMP1's own system prompt (prompts/amp1.md) and the amp1_basic harness reference, verbatim,
joined as amp.agents.prompt.compose_system joins them.

python compose_prompt.py EPISODE_DIR WALL_LIMIT_MIN
"""

import sys
from pathlib import Path

AMP = Path("/tmp/ext/ml-amp/src/amp")
ep_dir = Path(sys.argv[1]).resolve()
wall = sys.argv[2] if len(sys.argv) > 2 else "45"

sys.path.insert(0, str(AMP.parent))
from amp.agents.prompt import compose_system  # noqa: E402

reference = "\n\n".join(
    (AMP / "harnesses" / p).read_text().rstrip("\n")
    for p in ("_sdk_amp1_basic/reference.md", "amp1_basic/reference.md"))
system = compose_system((AMP / "agents/prompts/amp1.md").read_text(), reference)

preamble = f"""# How the AMP1 tools work in this run (read first)

You are the policy in one episode of AMP1, the agentic manipulation policy of "On Agentic
Manipulation Policies" (Apple, 2026). Everything after this preamble is AMP1's own system prompt and
SDK reference, verbatim. AMP1's agent loop would give you its tools directly; in this run you reach
the same tools through shell commands, all run from your episode directory `{ep_dir}`:

| AMP1 tool | In this run |
|---|---|
| `python(code, timeout_s=600)` | Bash: `cd {ep_dir} && ./py <<'PY'` newline, your code, newline, `PY` (add `--timeout S` after `./py` for a longer cell). The kernel is persistent; `rh`, `ep`, `np`, `Image` and `show` are preloaded. Each result ends with the budget line. |
| images from `show(x, caption)` | `show()` saves the image and the result lists a `*.view.jpg` path for each one. **Open every listed path with the Read tool to see it**: an image you do not Read, you have not seen. |
| `view_image(path)` | the Read tool on that path |
| `finish_episode(reason)` | Bash: `cd {ep_dir} && ./finish_episode "<reason>"` |
| `submit_report(...)` | the Write tool: `{ep_dir}/report.json`, one JSON object with the fields "Your report" lists |

Rules for this run, on top of the information policy below:

- Use only those commands, the Read tool on images in `{ep_dir}/images/` (or files you wrote in
  `{ep_dir}`), and the Write tool for files in `{ep_dir}`. Do not read, list or search any other file
  or directory on this machine (no simulator, server, harness or SDK source, no other episode, no
  repository), and do not use the web. Inside the kernel, use the SDK through `ep` only, as the
  prompt says; do not open files outside your working directory from Python either.
- The wall-clock limit for this episode is {wall} minutes. The kernel's budget line shows the
  minutes used. The sim is paused while you think; only executed motion uses steps.
- Do not stop to ask anyone anything: there is no one to answer. Work the episode through to
  `finish_episode` (or until the episode ends), then write the report, then reply with a short
  summary: outcome belief, number of `./py` calls you made, steps used, and the report path.

"""
(ep_dir / "SYSTEM_PROMPT.md").write_text(preamble + system)
print(f"{ep_dir / 'SYSTEM_PROMPT.md'}: {len(preamble + system)} chars")
