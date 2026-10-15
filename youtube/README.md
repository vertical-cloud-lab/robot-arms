# YouTube uploads: BYU Vertical Cloud Lab channel

Target: **BYU Vertical Cloud Lab** ([@BYUVerticalCloudLab](https://www.youtube.com/@BYUVerticalCloudLab),
`UCKC7WzMu6QEh7O55zZlT2lw`). Not *BYU VCL Hardware Streams* (`UCZ5KNGkEEqDsRVn0Nlfn0IA`),
the livestream channel byu-vcl's stream cams push to.

This is a trimmed copy of byu-vcl's [`youtube/`](https://github.com/vertical-cloud-lab/byu-vcl/tree/main/youtube),
which holds the full write-up (why OAuth and not an API key, the OAuth client, consent-screen
settings) and the token-minting script. Only the **upload-only** token is wired in here:

| Secret | Scopes | Where |
| --- | --- | --- |
| `YOUTUBE_UPLOAD_TOKEN_PICKLE_B64` | `youtube.upload`, `youtube.readonly` | Repo secret, `claude.yml` env, `.claude/settings.local.json` |

`youtube.upload` can add videos and set thumbnails but **cannot delete or edit** anything,
so the worst this token can do is unwanted uploads. Deleting, editing metadata, playlists,
captions and changing privacy need byu-vcl's full-control token, which only exists in its
`youtube-admin` environment: ask for those with `@claude-youtube` on a byu-vcl issue
(sgbaird only, each run approved by sgbaird).

## Usage

```bash
pip install -r youtube/requirements.txt
python youtube/yt_service.py                        # which channel, which scopes
python youtube/yt_service.py upload clip.mp4 --title "PiPER pick-and-place, run 3"
```

```python
from youtube.yt_service import get_youtube_service, upload_video
```

Uploads default to `private`, and videos uploaded through the API from an unaudited Cloud
project are locked private anyway. Link the video in the comment and say it is private;
sgbaird publishes or unlists from YouTube Studio (or a `@claude-youtube` run in byu-vcl).

## Rotating

The value is the same one byu-vcl uses. Re-mint it there
(`python youtube/generate_youtube_token.py --profile upload --to-local --to-github`, see that
README), then copy it here without printing it, from the byu-vcl checkout's
`.claude/settings.local.json`:

```bash
python - <<'EOF'
import json, subprocess
v = json.load(open("../byu-vcl/.claude/settings.local.json"))["env"]["YOUTUBE_UPLOAD_TOKEN_PICKLE_B64"]
subprocess.run(["gh", "secret", "set", "YOUTUBE_UPLOAD_TOKEN_PICKLE_B64", "-R", "vertical-cloud-lab/robot-arms"], input=v, text=True, check=True)
s = json.load(open(".claude/settings.local.json")); s["env"]["YOUTUBE_UPLOAD_TOKEN_PICKLE_B64"] = v
json.dump(s, open(".claude/settings.local.json", "w"), indent=2)
EOF
```
