"""Build make_video.py's playlist from amp1/results/summary.json and each episode's report.

python playlist.py RESULTS_DIR VIDEOS_DIR OUT.json [MAX_STILLS] [SECTION...]

An episode whose motion video exists in VIDEOS_DIR (EPISODE.mp4, from summarize.py) plays it; one
without (its frames were not kept) gets a slideshow of its report's key images. SECTION keeps only
the sections whose title starts with it; a section with an intro of its own (INTROS) replaces the
video's opening card when it is the only one kept.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

res, vids, out = Path(sys.argv[1]), Path(sys.argv[2]), Path(sys.argv[3])
max_stills = int(sys.argv[4]) if len(sys.argv) > 4 else 6
only = sys.argv[5:]
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
    ("Lab workflows on the simulated PiPER", "PR #87: clearing the A1 mini's plate, swapping the "
     "powder doser's auger, charging the atomizer's crucible",
     ["print_off_a1_mini-ep0", "print_off_a1_mini-ep1", "auger_swap-ep0", "auger_swap-ep1",
      "atomizer_charge-ep0", "atomizer_charge_bare_rod-ep0", "atomizer_charge_bare_rod-ep1"]),
]
# make_video.py's opening card, [text, size, bold, colour] per line
INTROS = {
    "Lab workflows on the simulated PiPER": [
        ["AMP1 (Apple, \"On Agentic Manipulation Policies\", 2026) on three lab workflows", 34, True,
         "#ffffff"],
        ["A simulated AgileX PiPER clears the A1 mini's plate, swaps the powder doser's auger and "
         "charges the atomizer's crucible", 26, False, "#d0d4da"],
        ["Policy: Claude Opus 5.5 through Claude Code, given only AMP1's own prompt and SDK; each "
         "episode scored by the simulator's own check", 24, False, "#d0d4da"],
        ["Motion clips show executed motion in real time: the simulator pauses while the model "
         "thinks.", 21, False, "#9aa3ad"],
        ["vertical-cloud-lab/robot-arms PR #87", 22, False, "#9aa3ad"]],
}
if only:
    ORDER = [o for o in ORDER if any(o[0].startswith(x) for x in only)]


def pick(items, n):
    """n key images spread over the episode, always keeping the first and the last."""
    if len(items) <= n:
        return items
    idx = sorted({round(k * (len(items) - 1) / (n - 1)) for k in range(n)})
    return [items[k] for k in idx]


playlist = []
if len(ORDER) == 1 and ORDER[0][0] in INTROS:
    playlist.append({"intro": INTROS[ORDER[0][0]]})
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
