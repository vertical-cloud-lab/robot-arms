#!/usr/bin/env python3
"""Slice the PiPER camera mount for the lab's Bambu Lab H2D in PAHT-CF with the Bambu Studio CLI.

    python slice_h2d.py --bambu ~/bambu/squashfs-root   # an extracted Bambu Studio AppImage

slice_a1mini.py's one-plate job, moved to the H2D: every printed part in ../exports (bracket,
pod, carrier, spacers, 2 x tag_wedge) in the same arrangement, PRINT_LAYOUT in ../cad/render.py,
shifted so the A1 mini's 180 x 180 mm square sits in the middle of the H2D's 350 x 320 mm bed.
Bambu's system presets "Bambu Lab H2D 0.4 nozzle", "0.20mm Standard @BBL H2D" and
"Bambu PAHT-CF @BBL H2D", flattened by flatten_presets.py, with the same overrides as the A1 mini
and slice_configs.py: 3 walls, 25 % infill, circle compensation on, supports off, Textured PEI.

The filament is mapped by hand to the left nozzle (extruder 1). The H2D's status on 2026-09-27
showed a 0.4 mm hardened-steel hotend on the left and a 0.6 mm TPU High-Flow hotend on the right,
and carbon fibre would wear the right one out. Every footprint is checked against the bed and the
left nozzle's reach (x 0 to 325 mm, from the machine preset), and against the other parts.
Writes piper_camera_mount_H2D_PAHT-CF.3mf and report_h2d.json here. Thumbnails work as in
slice_a1mini.py: with WAYLAND_DISPLAY set and libOSMesa installed.
"""
from __future__ import annotations

import sys

sys.dont_write_bytecode = True  # importing ../cad/render.py leaves no __pycache__ in cad/

import argparse
import hashlib
import itertools
import json
import re
import shutil
import subprocess
import xml.etree.ElementTree as ET
import zipfile
from pathlib import Path

from flatten_presets import flatten
from slice_a1mini import gl_env, stl_bounds

HERE = Path(__file__).resolve().parent
EXPORTS = HERE.parent / "exports"
sys.path.insert(0, str(HERE.parent / "cad"))
from render import PRINT_LAYOUT  # noqa: E402  (imports cadquery and pyvista, like render.py itself)

OUT_3MF = HERE / "piper_camera_mount_H2D_PAHT-CF.3mf"
PRESETS = {
    "machine": "Bambu Lab H2D 0.4 nozzle",
    "process": "0.20mm Standard @BBL H2D",
    "filament": "Bambu PAHT-CF @BBL H2D",
}
OVERRIDES = {"wall-loops": "3", "sparse-infill-density": "25%", "curr-bed-type": "Textured PEI Plate"}
PROCESS_SETTINGS = {"enable_circle_compensation": "1", "enable_support": "0"}
# The nozzle. The CLI takes it from the plate's own settings, not the project's: left alone it picks
# "Auto For Flush" and Bambu's main extruder, the right one. "Manual" with filament 1 on extruder 1
# puts it on the left.
LEFT = 1
PLATE_PARAMS = {"filament_map_mode": "Manual", "filament_maps": str(LEFT)}
FILAMENT_COLOUR = "#000000"  # PAHT-CF only comes in black
BED = (350.0, 320.0)
A1M_BED = 180.0
SHIFT = ((BED[0] - A1M_BED) / 2, (BED[1] - A1M_BED) / 2)  # the A1 mini's square, centred

PLATES = [
    ("PiPER camera mount", [(part, x + SHIFT[0], y + SHIFT[1]) for part, (x, y) in PRINT_LAYOUT.items()]),
]


def reach(machine: dict, extruder: int) -> list[float]:
    """[xmin, ymin, xmax, ymax] that one nozzle can print, from extruder_printable_area."""
    pts = [[float(c) for c in p.split("x")] for p in machine["extruder_printable_area"][extruder - 1].split(",")]
    xs, ys = zip(*pts)
    return [min(xs), min(ys), max(xs), max(ys)]


def layout(area: list[float]) -> tuple[list[list[dict]], list[str]]:
    """slice_a1mini.layout() for a rectangular bed, checked against the nozzle's reach too."""
    plates, warnings = [], []
    for _, objs in PLATES:
        parts = []
        for part, x, y in objs:
            stl = EXPORTS / f"{part.split('#')[0]}.stl"
            (x0, y0, z0), (x1, y1, z1) = stl_bounds(stl)
            box = [x - (x1 - x0) / 2, y - (y1 - y0) / 2, x + (x1 - x0) / 2, y + (y1 - y0) / 2]
            parts.append({"part": part, "stl": stl.name, "sha256": hashlib.sha256(stl.read_bytes()).hexdigest()[:12],
                          "centre": [x, y], "footprint": [round(float(c), 2) for c in box],
                          "height": round(float(z1 - z0), 2),
                          "pos": [float(x - (x0 + x1) / 2), float(y - (y0 + y1) / 2)]})
            if box[0] < 0 or box[1] < 0 or box[2] > BED[0] or box[3] > BED[1]:
                warnings.append(f"{part} leaves the {BED[0]:g} x {BED[1]:g} mm bed")
            if box[0] < area[0] or box[1] < area[1] or box[2] > area[2] or box[3] > area[3]:
                warnings.append(f"{part} leaves the left nozzle's reach, x {area[0]:g}..{area[2]:g}, "
                                f"y {area[1]:g}..{area[3]:g}")
        for a, b in itertools.combinations(parts, 2):
            fa, fb = a["footprint"], b["footprint"]
            ox, oy = min(fa[2], fb[2]) - max(fa[0], fb[0]), min(fa[3], fb[3]) - max(fa[1], fb[1])
            if ox > 0 and oy > 0:
                warnings.append(f"{a['part']} and {b['part']} overlap by {ox:.1f} x {oy:.1f} mm (bounding boxes)")
        plates.append(parts)
    return plates, warnings


def write_presets(resources: Path, build: Path) -> tuple[dict[str, Path], dict]:
    paths, machine = {}, {}
    for kind, name in PRESETS.items():
        cfg = flatten(kind, name, resources / "profiles" / "BBL")
        if kind == "machine":
            machine = cfg
        if kind == "filament":
            cfg["filament_colour"] = [FILAMENT_COLOUR]
        if kind == "process":
            cfg.update(PROCESS_SETTINGS)
        paths[kind] = build / f"{kind}.json"
        paths[kind].write_text(json.dumps(cfg, indent=2) + "\n")
    return paths, machine


def write_assemble_list(build: Path, placed: list[list[dict]]) -> Path:
    # As slice_a1mini.py: one entry per copy, so both tag wedges are named "tag_wedge_1".
    plates = [{"plate_name": name, "need_arrange": False, "plate_params": PLATE_PARAMS,
               "objects": [{"path": str(EXPORTS / p["stl"]), "count": 1, "filaments": [1],
                            "pos_x": [p["pos"][0]], "pos_y": [p["pos"][1]], "pos_z": [0]} for p in parts]}
              for (name, _), parts in zip(PLATES, placed)]
    path = build / "assemble.json"
    path.write_text(json.dumps({"plates": plates}, indent=1) + "\n")
    return path


def run_cli(bambu: Path, presets: dict[str, Path], assemble: Path, build: Path, env: dict) -> str:
    cmd = [str(bambu / "AppRun"), "--debug", "3",
           "--load-settings", f"{presets['machine']};{presets['process']}",
           "--load-filaments", str(presets["filament"]),
           "--load-assemble-list", str(assemble)]
    for k, v in OVERRIDES.items():
        cmd += [f"--{k}", v]
    cmd += ["--slice", "0", "--outputdir", str(build), "--export-3mf", OUT_3MF.name]
    proc = subprocess.run(cmd, capture_output=True, text=True, env=env)
    log = proc.stdout + proc.stderr
    (build / "cli.log").write_text(log)
    if proc.returncode != 0:
        raise SystemExit(f"Bambu Studio CLI exited {proc.returncode}; see {build / 'cli.log'}")
    return log


def gcode_setting(gcode: str, key: str) -> str | None:
    m = re.search(rf"^; {key} = (.*)$", gcode, re.M)
    return m.group(1) if m else None


def report(build: Path, log: str, placed: list[list[dict]], layout_warnings: list[str], area: list[float]) -> dict:
    result = json.loads((build / "result.json").read_text())
    with zipfile.ZipFile(build / OUT_3MF.name) as z:
        info = ET.fromstring(z.read("Metadata/slice_info.config"))
        names = z.namelist()
        gcode = {n: z.read(f"Metadata/plate_{n}.gcode").decode() for n in range(1, len(PLATES) + 1)}
    version = re.search(r"Current BambuStudio Version (\S+)", log)
    slicing_warnings = re.findall(r"plate (\d+): found (?:NON_CRITICAL )?slicing warnings: (.*)", log)
    support_checks = len(re.findall(r"is_support_necessary takes", log))
    support_flags = [{"plate": int(p), "object": m.group(1), "reason": m.group(2)} for p, w in slicing_warnings
                     if (m := re.search(r"It seems object (.+?) has (.+?)\. Please re-orient", w))]
    plates = []
    for sliced, (name, _), xml in zip(result["sliced_plates"], PLATES, info.findall("plate")):
        meta = {m.get("key"): m.get("value") for m in xml.findall("metadata")}
        fil = xml.find("filament")
        g = gcode[sliced["id"]]
        plates.append({
            "plate": sliced["id"], "name": name,
            "objects": [o["name"] for o in sliced["objects"]],
            "print_time_s": round(sliced["total_predication"]),
            "filament_g": float(fil.get("used_g")), "filament_m": float(fil.get("used_m")),
            "filament_type": fil.get("type"),
            # which nozzle: slice_info.config's own record (extruder_id 1 is the left) and the G-code's map
            "nozzles_used": [dict(n.attrib) for n in xml.findall("nozzle")],
            "filament_map": gcode_setting(g, "filament_map"),
            "filament_map_mode": gcode_setting(g, "filament_map_mode"),
            "nozzle_type": gcode_setting(g, "nozzle_type"),
            "bed_type": gcode_setting(g, "curr_bed_type"),
            "bed_temp_c": [int(t) for t in re.findall(r"^M1[49]0 S(\d+)", g, re.M)],
            "nozzle_temp_c": int(gcode_setting(g, "nozzle_temperature").split(",")[0]),
            "chamber_temp_c": int(gcode_setting(g, "chamber_temperatures").split(",")[0]),
            "layers": int(re.findall(r"^; total layer number: (\d+)", g, re.M)[-1]),
            "toolpath_outside_bed": meta.get("outside") == "true",
            "support_used": meta.get("support_used") == "true",
            "slicer_warnings": [w for p, w in slicing_warnings if int(p) == sliced["id"]],
            "gcode_warnings": [{"msg": w.get("msg"), "level": int(w.get("level")), "code": w.get("error_code")}
                               for w in xml.findall("warning")],
            "feature_time_s": {k: round(v) for k, v in sorted(sliced.get("feature_type_times", {}).items())},
        })
    return {
        "bambu_studio": version.group(1) if version else None,
        "presets": PRESETS,
        "overrides": {**{k.replace("-", "_"): v for k, v in OVERRIDES.items()}, **PROCESS_SETTINGS},
        "plate_params": PLATE_PARAMS,
        "filament_colour": FILAMENT_COLOUR,
        "left_nozzle_reach_mm": area,
        "return_code": result["return_code"], "error_string": result["error_string"],
        "support_necessity_checks_run": support_checks,
        "support_necessity_flags": support_flags,
        "layout": [{k: v for k, v in p.items() if k != "pos"} for parts in placed for p in parts],
        "layout_warnings": layout_warnings,
        "thumbnails_embedded": sorted(n for n in names if n.endswith(".png")),
        "plates": plates,
        "total_print_time_s": sum(p["print_time_s"] for p in plates),
        "total_filament_g": round(sum(p["filament_g"] for p in plates), 2),
    }


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--bambu", type=lambda s: Path(s).expanduser().resolve(), required=True,
                    help="extracted AppImage (squashfs-root)")
    ap.add_argument("--build", type=Path, default=HERE / "build_h2d")
    args = ap.parse_args()
    shutil.rmtree(args.build, ignore_errors=True)
    args.build.mkdir(parents=True)
    presets, machine = write_presets(args.bambu / "resources", args.build)
    area = reach(machine, LEFT)
    placed, layout_warnings = layout(area)
    for w in layout_warnings:
        print(f"LAYOUT WARNING: {w}", file=sys.stderr)
    env = gl_env(args.build)
    log = run_cli(args.bambu, presets, write_assemble_list(args.build, placed), args.build, env)
    rep = report(args.build, log, placed, layout_warnings, area)
    shutil.copy(args.build / OUT_3MF.name, OUT_3MF)
    (HERE / "report_h2d.json").write_text(json.dumps(rep, indent=2) + "\n")
    print(json.dumps(rep, indent=2))


if __name__ == "__main__":
    main()
