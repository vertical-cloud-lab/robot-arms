#!/usr/bin/env python3
"""Slice the #52 print job, one A1 mini plate in black PLA, with the Bambu Studio CLI.

    python slice_a1mini.py --bambu ~/bambu/squashfs-root                  # -> issue52_A1mini_PLA.3mf

The plate: the wrist-camera pod from PR #10 (its latest, with the Camera Module 3 Wide's lens
hole), one horizontal and two vertical camera-head cradles from PR #9. The STLs in stl/ are
byte-for-byte the exports of the commits in SOURCES, each in the print orientation it was
exported in.

It is #45's slice_a1mini.py (itself PR #10's, adapted) with the same settings: Bambu's system
presets (machine "Bambu Lab A1 mini 0.4 nozzle", process "0.20mm Standard @BBL A1M", filament
"Bambu PLA Basic @BBL A1M"), flattened, then 3 walls, 25 % infill, the Textured PEI plate, Bambu's
circle compensation and supports off. The cradles get PR #9's 4 walls and 40 % infill as
per-object settings. Nothing is turned. Writes issue52_A1mini_PLA.3mf and report.json here.
Thumbnails need a Wayland display and libOSMesa (see PR #10's slice README); without them the
slice is the same, without pictures.
"""
from __future__ import annotations

import argparse
import hashlib
import itertools
import json
import os
import re
import shutil
import subprocess
import sys
import xml.etree.ElementTree as ET
import zipfile
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
PARTS = HERE / "stl"
OUT_3MF = HERE / "issue52_A1mini_PLA.3mf"
BED = 180.0
PRESETS = {
    "machine": "Bambu Lab A1 mini 0.4 nozzle",
    "process": "0.20mm Standard @BBL A1M",
    "filament": "Bambu PLA Basic @BBL A1M",
}
OVERRIDES = {"wall-loops": "3", "sparse-infill-density": "25%", "curr-bed-type": "Textured PEI Plate"}
PROCESS_SETTINGS = {"enable_circle_compensation": "1", "enable_support": "0"}
HEAD_SETTINGS = {"wall_loops": "4", "sparse_infill_density": "40%"}  # PR #9's README
FILAMENT_COLOUR = "#000000"
OSMESA = Path("/usr/lib/x86_64-linux-gnu/libOSMesa.so.8")

SOURCES = {
    "pod": ("claude/issue-239-20260926-2347", "ba6f819", "piper-camera-mount/exports/pod.stl"),
    "head-cradle-horizontal": ("claude/issue-229-20261001-2322", "01e5a3e",
                               "robot-arm/enclosure/cameras/models/head-cradle-horizontal.stl"),
    "head-cradle-vertical": ("claude/issue-229-20261001-2322", "01e5a3e",
                             "robot-arm/enclosure/cameras/models/head-cradle-vertical.stl"),
}

# (object name, STL in stl/, turn about z in degrees, centre of its footprint on the bed).
# Front row: the three cradles (44 x 32 mm each), 14 mm apart; back: the pod (65 x 81 mm), centred.
# 5 mm or more between footprints, 2.5 mm from the edges.
LAYOUT = [
    ("head-cradle-vertical-1", "head-cradle-vertical", 0, (32.0, 35.0)),
    ("head-cradle-vertical-2", "head-cradle-vertical", 0, (90.0, 35.0)),
    ("head-cradle-horizontal", "head-cradle-horizontal", 0, (148.0, 35.0)),
    ("pod", "pod", 0, (90.0, 120.0)),
]


def read_stl(path: Path) -> tuple[bytes, np.ndarray]:
    data = path.read_bytes()
    n = int.from_bytes(data[80:84], "little")
    if len(data) != 84 + 50 * n:
        raise SystemExit(f"{path} is not a binary STL")
    tri = np.dtype([("normal", "<f4", 3), ("v", "<f4", (3, 3)), ("attr", "<u2")])
    return data, np.frombuffer(data, tri, count=n, offset=84).copy()


def turned(src: Path, dst: Path, deg: int) -> np.ndarray:
    """Write src turned by a multiple of 90 degrees about z (exact: only swaps and signs) to dst, and
    return its bounding box."""
    data, t = read_stl(src)
    for _ in range(deg // 90 % 4):  # (x, y) -> (-y, x)
        for key in ("normal", "v"):
            x = t[key][..., 0].copy()
            t[key][..., 0] = -t[key][..., 1]
            t[key][..., 1] = x
    dst.write_bytes(data[:84] + t.tobytes())
    v = t["v"].reshape(-1, 3)
    return np.array([v.min(0), v.max(0)])


def layout(build: Path, skip: set[str]) -> tuple[list[dict], list[str]]:
    placed, warnings = [], []
    for name, part, deg, (x, y) in LAYOUT:
        if name in skip:
            continue
        stl = build / f"{name}.stl"  # one file per object, so Studio names each one apart
        (x0, y0, z0), (x1, y1, z1) = turned(PARTS / f"{part}.stl", stl, deg)
        box = [x - (x1 - x0) / 2, y - (y1 - y0) / 2, x + (x1 - x0) / 2, y + (y1 - y0) / 2]
        placed.append({"object": name, "part": part, "turn_deg": deg,
                       "sha256": hashlib.sha256((PARTS / f"{part}.stl").read_bytes()).hexdigest()[:12],
                       "centre": [x, y], "footprint": [round(float(c), 2) for c in box],
                       "height": round(float(z1 - z0), 2), "stl": str(stl),
                       "pos": [float(x - (x0 + x1) / 2), float(y - (y0 + y1) / 2)],
                       "print_params": HEAD_SETTINGS if part.startswith("head") else {}})
        if min(box) < 0 or max(box) > BED:
            warnings.append(f"{name} leaves the bed: x {box[0]:.1f}..{box[2]:.1f}, y {box[1]:.1f}..{box[3]:.1f}")
    for a, b in itertools.combinations(placed, 2):
        fa, fb = a["footprint"], b["footprint"]
        gap = max(max(fa[0], fb[0]) - min(fa[2], fb[2]), max(fa[1], fb[1]) - min(fa[3], fb[3]))
        if gap < 5.0:
            warnings.append(f"{a['object']} and {b['object']}: {gap:.1f} mm apart (bounding boxes)")
    return placed, warnings


def index(folder: Path) -> dict[str, Path]:
    return {n: f for f in folder.rglob("*.json") if (n := json.loads(f.read_text()).get("name"))}


def resolve(name: str, files: dict[str, Path]) -> dict:
    own = json.loads(files[name].read_text())
    merged = resolve(own["inherits"], files) if own.get("inherits") else {}
    for inc in own.get("include", []):
        merged.update({k: v for k, v in resolve(inc, files).items() if k not in ("name", "instantiation")})
    merged.update(own)
    return merged


def flatten(kind: str, name: str, profiles: Path) -> dict:
    """The CLI does not follow "inherits" or "include", so give it one complete file per preset."""
    cfg = resolve(name, index(profiles / kind))
    for k in ("inherits", "include", "instantiation"):
        cfg.pop(k, None)
    cfg.update({"name": name, "from": "system", "type": kind})
    return cfg


def write_presets(resources: Path, build: Path) -> tuple[dict[str, Path], dict]:
    paths, stock_process = {}, {}
    for kind, name in PRESETS.items():
        cfg = flatten(kind, name, resources / "profiles" / "BBL")
        if kind == "filament":
            cfg["filament_colour"] = [FILAMENT_COLOUR]
        if kind == "process":
            stock_process = dict(cfg)
            cfg.update(PROCESS_SETTINGS)
        paths[kind] = build / f"{kind}.json"
        paths[kind].write_text(json.dumps(cfg, indent=2) + "\n")
    return paths, stock_process


def write_assemble_list(build: Path, placed: list[dict]) -> Path:
    objects = []
    for p in placed:
        obj = {"path": p["stl"], "count": 1, "filaments": [1],
               "pos_x": [p["pos"][0]], "pos_y": [p["pos"][1]], "pos_z": [0]}
        if p["print_params"]:
            obj["print_params"] = p["print_params"]
        objects.append(obj)
    path = build / "assemble.json"
    path.write_text(json.dumps({"plates": [{"plate_name": "Issue 52", "need_arrange": False,
                                            "objects": objects}]}, indent=1) + "\n")
    return path


def gl_env(build: Path) -> dict[str, str]:
    env = os.environ.copy()
    if not (env.get("WAYLAND_DISPLAY") and OSMESA.exists() and shutil.which("gcc")):
        print("no Wayland display or libOSMesa: slicing without thumbnails")
        return env
    shim = build / "libglxshim.so"
    subprocess.run(["gcc", "-shared", "-fPIC", "-O2", "-o", str(shim), str(HERE / "glxshim.c"),
                    f"-l:{OSMESA.name}"], check=True)
    env["LD_PRELOAD"] = f"{shim}:{OSMESA}"
    return env


def run_cli(bambu: Path, presets: dict[str, Path], assemble: Path, build: Path, env: dict, out: Path) -> str:
    cmd = [str(bambu / "AppRun"), "--debug", "3",
           "--load-settings", f"{presets['machine']};{presets['process']}",
           "--load-filaments", str(presets["filament"]),
           "--load-assemble-list", str(assemble)]
    for k, v in OVERRIDES.items():
        cmd += [f"--{k}", v]
    cmd += ["--slice", "0", "--outputdir", str(build), "--export-3mf", out.name]
    proc = subprocess.run(cmd, capture_output=True, text=True, env=env)
    log = proc.stdout + proc.stderr
    (build / "cli.log").write_text(log)
    if proc.returncode != 0:
        raise SystemExit(f"Bambu Studio CLI exited {proc.returncode}; see {build / 'cli.log'}")
    return log


def mark_overrides(path: Path, stock_process: dict) -> list[str]:
    """Name the process settings this job changes in the project's different_settings_to_system,
    so that Studio keeps them on opening the project (PR #10's slice_h2d.py). Only
    project_settings.config changes; the G-code and its MD5 stay as the CLI wrote them."""
    with zipfile.ZipFile(path) as z:
        entries = [(info, z.read(info.filename)) for info in z.infolist()]
    name = "Metadata/project_settings.config"
    project = json.loads(dict((i.filename, d) for i, d in entries)[name])
    ours = {k.replace("-", "_") for k in OVERRIDES} | set(PROCESS_SETTINGS)
    changed = sorted(k for k in ours if k in stock_process and project.get(k) != stock_process[k])
    project["different_settings_to_system"][0] = ";".join(changed)  # [process, filament..., machine]
    tmp = path.with_suffix(".tmp")
    with zipfile.ZipFile(tmp, "w") as out:
        for info, data in entries:
            out.writestr(info, (json.dumps(project, indent=4) + "\n").encode() if info.filename == name else data)
    tmp.replace(path)
    return changed


def object_settings(z: zipfile.ZipFile) -> dict[str, dict[str, str]]:
    """Per-object settings as stored in the project, to show the cradles' 4 walls and 40 % got in."""
    root = ET.fromstring(z.read("Metadata/model_settings.config"))
    out = {}
    for obj in root.findall("object"):
        meta = {m.get("key"): m.get("value") for m in obj.findall("metadata")}
        out[meta.get("name", obj.get("id"))] = {k: v for k, v in meta.items() if k in HEAD_SETTINGS}
    return out


def report(build: Path, log: str, placed: list[dict], warnings: list[str], marked: list[str], out: Path) -> dict:
    result = json.loads((build / "result.json").read_text())
    with zipfile.ZipFile(out) as z:
        info = ET.fromstring(z.read("Metadata/slice_info.config"))
        names = z.namelist()
        gcode = z.read("Metadata/plate_1.gcode").decode()
        per_object = object_settings(z)
    version = re.search(r"Current BambuStudio Version (\S+)", log)
    slicing_warnings = re.findall(r"plate (\d+): found (?:NON_CRITICAL )?slicing warnings: (.*)", log)
    support_flags = [{"object": m.group(1), "reason": m.group(2)} for _, w in slicing_warnings
                     if (m := re.search(r"It seems object (.+?) has (.+?)\. Please re-orient", w))]
    sliced, xml = result["sliced_plates"][0], info.find("plate")
    meta = {m.get("key"): m.get("value") for m in xml.findall("metadata")}
    fil = xml.find("filament")
    setting = lambda key: (m.group(1) if (m := re.search(rf"^; {key} = (.*)$", gcode, re.M)) else None)
    return {
        "bambu_studio": version.group(1) if version else None,
        "presets": PRESETS,
        "overrides": {**{k.replace("-", "_"): v for k, v in OVERRIDES.items()}, **PROCESS_SETTINGS},
        "head_overrides": HEAD_SETTINGS,
        "marked_in_different_settings_to_system": marked,
        "filament_colour": FILAMENT_COLOUR,
        "sources": {k: {"branch": b, "commit": c, "path": p} for k, (b, c, p) in SOURCES.items()},
        "return_code": result["return_code"], "error_string": result["error_string"],
        "support_necessity_checks_run": len(re.findall(r"is_support_necessary takes", log)),
        "support_necessity_flags": support_flags,
        "layout": [{k: v for k, v in p.items() if k not in ("pos", "stl")} for p in placed],
        "layout_warnings": warnings,
        "object_settings_in_3mf": per_object,
        "thumbnails_embedded": sorted(n for n in names if n.endswith(".png")),
        "plate": {
            "objects": [o["name"] for o in sliced["objects"]],
            "print_time_s": round(sliced["total_predication"]),
            "filament_g": float(fil.get("used_g")), "filament_m": float(fil.get("used_m")),
            "layers": int(re.search(r"^; total layer number: (\d+)", gcode, re.M).group(1)),
            "max_z_mm": float(re.search(r"^; max_z_height: ([\d.]+)", gcode, re.M).group(1)),
            "bed_type": setting("curr_bed_type"),
            "bed_temp_c": [int(t) for t in re.findall(r"^M1[49]0 S(\d+)", gcode, re.M)],
            "nozzle_temp_c": setting("nozzle_temperature"),
            "brim_type": setting("brim_type"),
            "toolpath_outside_bed": meta.get("outside") == "true",
            "support_used": meta.get("support_used") == "true",
            "slicer_warnings": [w for _, w in slicing_warnings],
            "gcode_warnings": [{"msg": w.get("msg"), "level": int(w.get("level")), "code": w.get("error_code")}
                               for w in xml.findall("warning")],
            "feature_time_s": {k: round(v) for k, v in sorted(sliced.get("feature_type_times", {}).items())},
        },
    }


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--bambu", type=lambda s: Path(s).expanduser().resolve(), required=True,
                    help="extracted AppImage (squashfs-root)")
    ap.add_argument("--build", type=Path, default=HERE / "build")
    ap.add_argument("--skip", nargs="*", default=[], choices=[name for name, *_ in LAYOUT],
                    help="objects to leave off the plate")
    args = ap.parse_args()
    suffix = "".join(f"_no-{name}" for name in args.skip)
    out = OUT_3MF.with_name(f"{OUT_3MF.stem}{suffix}.3mf")
    shutil.rmtree(args.build, ignore_errors=True)
    args.build.mkdir(parents=True)
    placed, warnings = layout(args.build, set(args.skip))
    for w in warnings:
        print(f"LAYOUT WARNING: {w}", file=sys.stderr)
    presets, stock_process = write_presets(args.bambu / "resources", args.build)
    log = run_cli(args.bambu, presets, write_assemble_list(args.build, placed), args.build, gl_env(args.build), out)
    shutil.copy(args.build / out.name, out)
    marked = mark_overrides(out, stock_process)
    rep = report(args.build, log, placed, warnings, marked, out)
    (HERE / f"report{suffix}.json").write_text(json.dumps(rep, indent=2) + "\n")
    print(json.dumps(rep, indent=2))


if __name__ == "__main__":
    main()
