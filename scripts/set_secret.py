#!/usr/bin/env python3
"""Set one secret on this repo and in .claude/settings.local.json, without echoing it.

The value is read with getpass (nothing shown, nothing in shell history) and handed to
`gh secret set` over stdin, so it never appears in a process list either.

Usage, from the repo root:
    python scripts/set_secret.py ARM_PI_PASSWORD
    python scripts/set_secret.py CLAUDE_CODE_OAUTH_TOKEN --gh-only

Use --gh-only for CLAUDE_CODE_OAUTH_TOKEN: in the local env block it would override
your own Claude Code login.
"""

import argparse
import getpass
import json
import subprocess
from pathlib import Path

REPO = "vertical-cloud-lab/robot-arms"
SETTINGS = Path(__file__).resolve().parent.parent / ".claude" / "settings.local.json"

parser = argparse.ArgumentParser()
parser.add_argument("name")
parser.add_argument("--gh-only", action="store_true", help="skip settings.local.json")
args = parser.parse_args()

value = getpass.getpass(f"{args.name}: ")
if not value:
    raise SystemExit("empty value, nothing set")

subprocess.run(["gh", "secret", "set", args.name, "-R", REPO], input=value, text=True, check=True)
print(f"set {args.name} on {REPO}")

if not args.gh_only:
    settings = json.loads(SETTINGS.read_text(encoding="utf-8")) if SETTINGS.exists() else {}
    settings.setdefault("env", {})[args.name] = value
    SETTINGS.parent.mkdir(exist_ok=True)
    SETTINGS.write_text(json.dumps(settings, indent=2), encoding="utf-8")
    print(f"set {args.name} in {SETTINGS.relative_to(SETTINGS.parent.parent)}")
