## Coding Agent

- Set environment variables `PIP_TIMEOUT=600` and `PIP_RETRIES=2` prior to `conda` or `pip` installs
- Include plots directly in your comment reply via `![image name](https://github.com/<user/org>/<repo>/blob/<shortened-commit-hash>/<filename>?raw=true)`. Truncate the commit hash to the first 7 characters only. For example, `https://github.com/AccelerationConsortium/evaluation-metrics/blob/52754e7/scripts/bo_benchmarks/demonstrations/branin_campaign_demonstration_results.png?raw=true`. For provenance, ensure you use the shortened (7-character) commit hash, not the branch name
- If you mention files in your comment reply, add direct hyperlinks based on the shortened (7-character) commit hash
- IMPORTANT: Never echo/grep/print environment secrets. These should never be exposed in your terminal history or other outputs

This repo was split out of [vertical-cloud-lab/byu-vcl](https://github.com/vertical-cloud-lab/byu-vcl)
on 2026-10-09. The issues moved here with their comments, but older Claude comments link to
branches that stayed in byu-vcl (`claude/issue-199-…`, `claude/issue-229-…`, `claude/issue-239-…`
and so on). Those links still work, and the full commit history for that work is there: each
branch here is the same files squashed into one import commit. byu-vcl's CLAUDE.md is still the
reference for the rest of the lab (stream cams, OT-2, CubXL, Hugging Face Spaces, YouTube).

### The GitHub token dies at minute 60 (push early, re-mint to continue)

The GitHub App token a session starts with (`GITHUB_TOKEN`/`GH_TOKEN` in the
session environment, and embedded in the origin remote URL) expires exactly 60
minutes after the Run Claude Code step starts. The session keeps running, but
`git push` fails, `gh` fails, and the MCP tool that updates the progress
comment fails, all with 401, so from the outside the session goes silent while
finished work stops landing.

- Push and update the tracking comment early and often. Treat minute 50 as the
  deadline for anything that must reach GitHub, in case recovery fails.
- At the first 401 from a push or `gh` call (or proactively around minute 55),
  run `python scripts/refresh_github_app_token.py`. It re-runs the action's
  own OIDC exchange, saves a fresh one-hour token to `/tmp/.ghtok` (mode
  0600), and re-points the origin remote at it, so plain `git push` works
  again.
- `gh` keeps reading the dead token from the environment, so prefix each call:
  `GH_TOKEN=$(cat /tmp/.ghtok) gh ...`.
- The MCP comment tool cannot be re-keyed mid-session. After a re-mint, update
  the tracking comment over REST instead: write the body to a file and run
  `GH_TOKEN=$(cat /tmp/.ghtok) gh api -X PATCH
  repos/$GITHUB_REPOSITORY/issues/comments/<comment-id> -F body=@that-file`.
- A re-minted token also lives one hour, so re-run the script each hour it is
  needed. Never echo, log, or commit a token value; the script prints only
  statuses and lengths.

## Edison Scientific

When waiting on an Edison task in GitHub Actions, NEVER run the polling script in the background (run_in_background, nohup, &, or the Monitor tool) — the runner is destroyed the moment you post your final comment, killing background processes; Monitor counts as background and dies the same way. Also be aware that the agent harness BLOCKS the shell `sleep` builtin in foreground Bash calls (the error message suggests Monitor — do NOT follow that suggestion, it recreates the background-death failure). The pattern that works: put the wait INSIDE a single blocking Python call — Python-side `time.sleep` is not blocked — and run it as ONE foreground Bash call with an explicit long timeout (max 3600000 ms):

```bash
# ONE foreground Bash tool call with timeout: 3600000
python - <<'EOF'
import json, os, time
from edison_client import EdisonClient

client = EdisonClient(api_key=os.environ["EDISON_PLATFORM_API_KEY"])
task_id = json.load(open("outputs/<...>/_task_id.json"))["task_id"]
while True:
    task = client.get_task(task_id=task_id, verbose=True)
    status = str(task.status)
    print("status:", status, flush=True)
    if status in {"success", "fail", "failed", "cancelled", "error"}:
        break
    time.sleep(240)
EOF
```

Do not post your final comment until results are fetched and committed, or ~45 minutes of wall-clock have elapsed — in which case commit the task-id file and state that a follow-up @claude comment is needed to fetch. Whenever you retrieve results, fetch and commit all artifacts associated with a trajectory. If you need to upload files, use the analysis query type. Docs: https://edisonscientific.gitbook.io/edison-cookbook/edison-client. Endpoint: https://api.platform.edisonscientific.com. Pass the key in explicitly and never echo it:

```python
from edison_client import EdisonClient, JobNames
client = EdisonClient(api_key=os.environ["EDISON_PLATFORM_API_KEY"])
```

`scripts/edison_6dof.py` on the `claude/issue-199-…` branches is the helper the earlier 6DOF
scans used. Its answers live in `environment_frame`, not on the task object, which once made a
fetch helper silently drop every answer.

## The arm Pi (`rpi-5-eufi`) over Tailscale

The Pi that drives the AgileX PiPER is on the lab tailnet as `ARM_PI_HOSTNAME`, tagged
`tag:rpi-5-eufi`. **Treat it as live hardware that moves an arm.** Inspect read-only first
(`systemctl status`, `journalctl`, `crontab -l` as root, `ip -br link` for the CAN interface)
before changing anything, and never command arm motion, enable the CAN bus, or start a
controller unless the request explicitly asks for it and says the workspace is clear. Restart
services only when necessary and verify the arm is healthy end to end afterwards, reporting
failures as failures. Changes made on the Pi (systemd units, udev rules, cron, config) do not
live in this repo, so record them here so they can be reproduced.

**How CI gets on the tailnet.** `claude.yml`'s `Connect to Tailscale` step joins every session
as an ephemeral node carrying `tag:rpi-5-eufi`, so you are already on the tailnet; run
`tailscale status` to confirm, and do not run `tailscale up` or mint keys yourself. The step
authenticates with a Tailscale **federated identity** (admin console → Settings → Trust
credentials → OpenID Connect), not an OAuth client secret. The action presents this job's
GitHub OIDC token, Tailscale checks its subject against
`repo:vertical-cloud-lab@228975003/robot-arms@1412458486:*`, and only then issues an auth key,
which can only carry `tag:rpi-5-eufi`. There is no long-lived Tailscale secret to leak or
rotate. `TS_OAUTH_CLIENT_ID` and `TS_AUDIENCE` are stored as secrets but Tailscale itself says
neither value is secret. This needs `id-token: write` on the job and
`tailscale/github-action@v4`. Unlike byu-vcl's OAuth client, there is no "request every tag the
client owns" trap here: one identity, one tag.

**The subject carries numeric IDs, not just names.** This repo issues GitHub's *immutable*
subject format, `repo:<org>@<org id>/<repo>@<repo id>:ref:refs/heads/main`, so a pattern
written as `repo:vertical-cloud-lab/robot-arms:*` never matches and the join fails with
`token exchange failed with status 403: Unauthorized`. That cost the first check run. The
IDs survive renames, so a deleted-and-recreated repo of the same name cannot borrow the
identity. `gh api repos/vertical-cloud-lab/robot-arms/actions/oidc/customization/sub` shows
the prefix, and the credential's edit page shows the last subject Tailscale received. The
manual **Tailscale check** workflow (`tailscale-check.yml`) is the read-only way to prove the
whole path: it joins, prints the runner's tags, checks the Pi's `tcp:22`, and logs in over SSH
once `ARM_PI_USERNAME` is set.

**What the policy allows.** The policy lives in
[`vertical-cloud-lab/tailscale-policy`](https://github.com/vertical-cloud-lab/tailscale-policy)
(`policy.hujson`; edit by PR, the console copy is overwritten on merge). For this Pi it grants:

- **CI → Pi:** `tag:rpi-5-eufi` → `tag:rpi-5-eufi`, `tcp:22` only, SSH `accept` as
  `autogroup:nonroot`. Tagged sources never get check mode, so CI never sees a browser prompt.
  Root over Tailscale SSH is not allowed from CI; use `sudo` on the Pi.
- **People:** sgbaird has direct SSH (non-root and root). Other team members reach the Pi
  through `@claude` runs here until they are added to that rule.
- **Only `tcp:22` from CI.** A service that listens on the Pi (ROS 2, Zenoh, a camera stream, a
  web UI) is unreachable from a runner until a port is added to the `tag:rpi-5-eufi` grant. Bind
  new services to `127.0.0.1` and reach them over SSH unless they genuinely need the tailnet.
- Keep `tag:tailscale-ssh` **off** this Pi. That tag's `check` rule sits first in the policy and
  is first-match-wins, so adding it would put browser re-authentication in front of every human
  and give every tailnet member root.

**Connecting.** Tailscale SSH is authorized by the policy, not by keys, so there is no key to
find or generate:

```bash
ssh -o BatchMode=yes -o StrictHostKeyChecking=accept-new "$ARM_PI_USERNAME@$ARM_PI_HOSTNAME" 'hostname && uptime -p && id -un'
```

If SSH is refused (`tailnet policy does not permit you to SSH to this node`), the fix is a
policy or tag change only the tailnet admin can make; report it and stop rather than working
around it. sudo is password-gated, so feed the password over stdin so it never appears in a
process list or shell history: `ssh … "sudo -S -p '' <cmd>" <<< "$ARM_PI_PASSWORD"`. Never
print the hostname or any credential in comments, commits, or logs.

**What is on the Pi.** `piper_sdk` 0.6.2 lives in `~/piper-venv`. The arm scripts in the home
directory (`piper_status.py`, `piper_up_down.py`, `piper_pick_tape.py`) are copies, and
`piper_pick_tape.py` is versioned in `scripts/`. The only camera is a Pi Camera Module 3 Wide
(imx708_wide) on CSI. It is fixed on the table and looks at the arm side-on, so it shows reach
and height but not depth across the arm plane. Grab a frame with
`rpicam-still -n -t 1500 -o /tmp/f.jpg`. At rest the arm reads about
`[4, -2, 2, 1, 23, 64]` deg, not zero: the wrist (J5, J6) sits off zero when the motors are
disabled. J2 = -2 and J3 = +2 are just outside the joint limits, so a move "back to the start
joints" never completes; aim for the clamped pose (J2 = J3 = 0) and disable there.

**Recording motion.** The Pi 5 has no H.264 encoder and its `rpicam-vid` has no libav, so
record MJPEG: `rpicam-vid -n -t 0 --width 1536 --height 864 --framerate 20 --codec mjpeg
--quality 70 --save-pts f.pts -o f.mjpeg` (about 1.2 MB/s; that mode is a centre crop of the
sensor). The Pi has no ffmpeg; copy the file off with `scp -l 16000` and convert on the
runner. `piper_pick_tape.py --video PATH` does this for a run, and logs marks in place of
stills while the camera is busy. Only one process can hold the camera at a time.

**Using the Pi as a proxy.** Some vendor sites (and YouTube's player) block GitHub Actions IP
ranges; the Pi's residential IP is not blocked. The Pi is on constrained Wi-Fi and may be
running the arm, so rate-cap transfers (`curl --limit-rate`) and never run speed tests.

## Secret inventory

Names and purposes only — **never** echo, grep, or print the values. Every secret below is
passed through the `env:` block of `.github/workflows/claude.yml`. Adding one means editing that
block too, and the Claude GitHub App cannot modify `.github/workflows/`, so that step is always
a human commit. The same names are in the gitignored `.claude/settings.local.json` for local
sessions.

| Name | Kind | Purpose |
| --- | --- | --- |
| `CLAUDE_CODE_OAUTH_TOKEN` | secret | Claude Code login for the action (from `claude setup-token`). |
| `TS_OAUTH_CLIENT_ID` / `TS_AUDIENCE` | secret | Tailscale federated identity: client ID and audience (`api.tailscale.com/<client ID>`). Not sensitive, see above. Only useful from this repo's workflows, since the identity checks the GitHub OIDC subject. |
| `ARM_PI_PASSWORD` | secret | sudo password on the arm Pi. |
| `ARM_PI_USERNAME` / `ARM_PI_HOSTNAME` | variable | Login user and tailnet name of the arm Pi. Variables, not secrets: a 3-character secret is masked everywhere it appears as a substring, which once rewrote `byu-vcl` as `byu-***` throughout byu-vcl's logs. |
| `EDISON_PLATFORM_API_KEY` | secret | Edison Scientific platform API. |
| `HF_TOKEN` | secret | Hugging Face `byu-vcl` account, fine-grained read + write on its own repos (LeRobot datasets and policies). |
| `ONSHAPE_ACCESS_KEY` / `ONSHAPE_SECRET_KEY` | secret | Onshape REST API key pair. Prefer these for anything the API can do; the PiPER mount lives in vcl-shared > 6DOF Robot Arm. |
| `ONSHAPE_USERNAME` / `ONSHAPE_PASSWORD` | secret | Onshape login, for browser work only (WebGL canvas, so real pointer events on a display on a Pi). |
| `H2D_IP` / `H2D_ACCESS_CODE` / `H2D_SERIAL` | secret | Bambu Lab H2D, LAN mode. On the lab LAN, not the tailnet: connect from the Pi. |
| `A1_MINI_IP` / `A1_MINI_ACCESS_CODE` / `A1_MINI_SERIAL` | secret | The same for the A1 mini. |
| `BAMBU_USERNAME` / `BAMBU_PASSWORD` | secret | Bambu cloud login. A cloud-bound printer refuses LAN start/pause/stop commands not signed by Bambu's apps (HMS `0500-0500-0001-0007`); status, camera and SD upload still work over LAN. See byu-vcl's CLAUDE.md. |

**Setting or rotating.** `python scripts/set_secret.py NAME` reads a value without echoing it and
sets it both as a repo secret and in `.claude/settings.local.json` (add `--gh-only` for
`CLAUDE_CODE_OAUTH_TOKEN`, which would otherwise override the local Claude Code login). The
Tailscale identity: Settings → Trust credentials, delete and recreate with issuer GitHub,
subject `repo:vertical-cloud-lab@228975003/robot-arms@1412458486:*`, scope auth keys (write) with tag
`tag:rpi-5-eufi`, then update the two secrets. Everything else is shared with byu-vcl, so rotate
it in both repos.
