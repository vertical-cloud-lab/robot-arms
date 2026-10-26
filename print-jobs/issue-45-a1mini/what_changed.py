#!/usr/bin/env python3
"""Which wrist-camera parts changed between the set printed on 2026-10-13 and #4's latest?

    python what_changed.py      # from anywhere in the repo -> what_changed.json

The 13 October plate was piper_camera_mount_A1mini_PLA.3mf at b6e2da0, whose meshes matched every
STL in piper-camera-mount/exports at 19c3112 (PR #10's print_history_2026-10-24/). The latest is
claude/issue-4-20261023-1814 at 27db133, linked from #4. For each part this compares the two STLs'
git blobs, and for any that differ, the volume each one has that the other doesn't (manifold
booleans) and where that material is, in the STL's own print-orientation frame.
"""
from __future__ import annotations

import io
import json
import subprocess
from pathlib import Path

import numpy as np
import trimesh

HERE = Path(__file__).resolve().parent
PRINTED, LATEST = "b6e2da0", "27db133"
PARTS = ["bracket", "pod", "carrier", "spacers", "tag_wedge"]


def git(*args: str) -> bytes:
    return subprocess.run(["git", *args], cwd=HERE, check=True, capture_output=True).stdout


def bodies(mesh: trimesh.Trimesh) -> list[dict]:
    out = [{"mm3": round(float(b.volume), 1), "bbox_mm": np.round(b.bounds, 2).ravel().tolist()}
           for b in mesh.split(only_watertight=False) if abs(b.volume) >= 0.5]
    return sorted(out, key=lambda b: -b["mm3"])


def main() -> None:
    result = {"printed": PRINTED, "latest": LATEST, "parts": {}}
    for part in PARTS:
        path = f"piper-camera-mount/exports/{part}.stl"
        blobs = [git("rev-parse", f"{c}:{path}").decode().strip() for c in (PRINTED, LATEST)]
        rec = {"same_file": blobs[0] == blobs[1], "blobs": [b[:12] for b in blobs]}
        if not rec["same_file"]:
            old, new = (trimesh.load(io.BytesIO(git("show", f"{c}:{path}")), file_type="stl")
                        for c in (PRINTED, LATEST))
            removed = trimesh.boolean.difference([old, new], engine="manifold")
            added = trimesh.boolean.difference([new, old], engine="manifold")
            rec.update(volume_mm3=[round(float(old.volume), 1), round(float(new.volume), 1)],
                       removed_mm3=round(float(removed.volume), 1), added_mm3=round(float(added.volume), 1),
                       removed_bodies=bodies(removed), added_bodies=bodies(added))
        result["parts"][part] = rec
        print(part, json.dumps({k: v for k, v in rec.items() if not k.endswith("bodies")}))
    (HERE / "what_changed.json").write_text(json.dumps(result, indent=2) + "\n")


if __name__ == "__main__":
    main()
