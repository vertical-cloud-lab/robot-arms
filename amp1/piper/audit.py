"""Audit one policy agent: its Bash commands and Read/Write paths must stay in its episode dir,
and its kernel cells must use the SDK only (no file access, no simulator or server internals)."""
import json, re, sys
from pathlib import Path
out_file, ep_dir = sys.argv[1], sys.argv[2]
bad, n_bash, n_read, n_write, tools = [], 0, 0, 0, {}
for line in open(out_file):
    try:
        ev = json.loads(line)
    except json.JSONDecodeError:
        continue
    msg = ev.get("message") or {}
    content = msg.get("content") if isinstance(msg, dict) else None
    if not isinstance(content, list):
        continue
    for c in content:
        if c.get("type") != "tool_use":
            continue
        name, inp = c.get("name"), c.get("input", {})
        tools[name] = tools.get(name, 0) + 1
        if name == "Bash":
            n_bash += 1
            cmd = inp.get("command", "").strip()
            first = cmd.splitlines()[0] if cmd else ""
            ok = re.match(rf"^cd {re.escape(ep_dir)} && \./(py|finish_episode)\b", first) or \
                re.match(r"^\./(py|finish_episode)\b", first)
            if not ok:
                bad.append(("Bash", first[:160]))
        elif name in ("Read", "Write", "Edit"):
            p = inp.get("file_path", "")
            n_read += name == "Read"; n_write += name != "Read"
            if not p.startswith(ep_dir.rstrip("/") + "/"):
                bad.append((name, p))
        else:
            bad.append((name, json.dumps(inp)[:160]))
cells = [json.loads(x) for x in Path(ep_dir, "transcript.jsonl").read_text().splitlines() if x]
pat = re.compile(r"\bopen\(|\bimport (os|sys|subprocess|glob|mujoco|requests|urllib|socket|pathlib|shutil)\b|"
                 r"__import__|\bexec\(|\beval\(|/tmp/|\bep\._|\brh\._|worker_url|\.\./|globals\(\)|getattr\(ep")
flag = [(c["cell"], m.group(0)) for c in cells for m in [pat.search(c["code"])] if m]
print(json.dumps({"tools": tools, "bash": n_bash, "reads": n_read, "writes": n_write,
                  "outside_or_other": bad[:20], "n_outside": len(bad), "cells": len(cells),
                  "flagged_cells": flag[:20]}, indent=1))
