"""Build make_video.py's playlist from amp1/results/summary.json and each episode's report.

python playlist.py RESULTS_DIR VIDEOS_DIR OUT.json [MAX_STILLS]

An episode whose motion video exists in VIDEOS_DIR (EPISODE.mp4, from summarize.py) plays it; one
without (its frames were not kept) gets a slideshow of its report's key images.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

res, vids, out = Path(sys.argv[1]), Path(sys.argv[2]), Path(sys.argv[3])
max_stills = int(sys.argv[4]) if len(sys.argv) > 4 else 6
rows = {r["episode"]: r for r in json.loads((res / "summary.json").read_text())}


def started(ep: str) -> float:
    """When the episode's first kernel cell ran."""
    first = (res / ep / "transcript.jsonl").read_text().splitlines()[0]
    return json.loads(first)["t"]


ORDER = [
    ("CaP-Gym robosuite", "The paper's benchmark: CaP-X's own scenes and success checks",
     ["capgym_cube_lifting-ep0", "capgym_cube_stack-ep0", "capgym_cube_restack-ep0",
      "capgym_nut_assembly-ep0", "capgym_spill_wipe-ep0", "capgym_two_arm_lift-ep0",
      "capgym_two_arm_handover-ep0"]),
    ("CaP-Gym LIBERO-PRO", "Units drawn with a fixed seed from the 3,000 (60 tasks x 50 initial "
     "states), in the order run", sorted((n for n in rows if n.startswith("capgym_libero")),
                                        key=started)),
    ("Simulated AgileX PiPER", "This repo's tasks: #21 vials, #30 tape onto the shelf, and the "
     "paper's banana demo", ["vial_in_rack-ep0", "banana_in_bowl-ep0", "tape_to_shelf-ep0",
                             "tape_to_shelf-ep1"]),
]


def pick(items, n):
    """n key images spread over the episode, always keeping the first and the last."""
    if len(items) <= n:
        return items
    idx = sorted({round(k * (len(items) - 1) / (n - 1)) for k in range(n)})
    return [items[k] for k in idx]


playlist = []
for title, sub, eps in ORDER:
    playlist.append({"section": title, "subtitle": sub})
    for ep in eps:
        r = rows.get(ep)
        if r is None:
            continue
        sc = r.get("rescored") or r.get("scored") or {}
        ok = sc.get("success")
        verdict = {True: "SUCCESS", False: "FAILURE"}.get(ok, "NOT SCORED")
        verdict += " (scored by the simulator's own check" + (
            ", re-scored: the gripper never let go)" if r.get("rescored") else ")")
        task, k = ep.rsplit("-ep", 1)
        task = task.removeprefix("capgym_")
        label = f"{task}  ({'initial state' if task.startswith('libero') else 'episode'} {k})"
        steps = r["last_budget"].split(";")[0].strip("[")
        detail = (f"{r['python_calls']} code cells, {r['images_shown']} images looked at, "
                  f"{steps}, policy belief: {r.get('outcome_belief')}")
        it = {"episode": ep, "label": label, "instruction": r["instruction"], "verdict": verdict,
              "ok": ok, "detail": detail}
        mp4 = vids / f"{ep}.mp4"
        if mp4.exists():
            it["video"] = str(mp4)
        else:
            rep = json.loads((res / ep / "report.json").read_text())
            stills = []
            for k in rep.get("key_images", []):
                p = res / ep / "images" / (Path(k["path"]).name.split(".")[0] + ".jpg")
                if p.exists():
                    stills.append([str(p), k.get("caption", "")])
            fin = res / ep / "final_frame.jpg"
            it["stills"] = pick(stills, max_stills)
            if fin.exists():
                it["stills"].append([str(fin), "Final frame, recorded at the end of the episode"])
        playlist.append(it)
out.write_text(json.dumps(playlist, indent=1))
print(out, sum(1 for p in playlist if "episode" in p), "episodes")
