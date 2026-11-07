#!/usr/bin/env python3
"""Bring the lab's Onshape document up to date in place, ready to print from, in about 40 calls.

onshape_import.py made a new document for each import. This updates the existing one instead,
so its link keeps working:

    1. save the document as it stands as an Onshape version, named for the commit it holds,
       so the old parts can still be opened (Versions and history),
    2. import exports/assembly.step (our parts on the gripper's frame) and print_plate.py's
       plate (the printed parts in print orientation, laid out as on the A1 mini plate) as two
       new Part Studios,
    3. swap the old mount for the new one in the "Mount on gripper" assembly (the key may delete
       assembly instances; if that is ever refused, the assembly is rebuilt in a new tab), then
       try to delete the old mount's Part Studio and the empty default one. The lab's API key
       still can't delete tabs (HTTP 403 on 28 October, as in September), so the old mount's
       tab is renamed "OLD <commit>, superseded: do not print" for someone to delete in the web app,
    4. rename the document for this commit, check each printed part's volume in Onshape
       against the STEP, save shaded views, and save the result as a second version.

The document stays private (AgileX's gripper STEP is in it; see add_gripper.py).

    python onshape/update_doc.py --doc 93ef145982c24192bfd160be --ws e3d08fcb2dcad7c92e183721
"""
from __future__ import annotations

import sys

sys.dont_write_bytecode = True  # importing print_plate.py and ../cad leaves no __pycache__

import argparse
import base64
import json
import os
import re
import subprocess
import tempfile
import time
from pathlib import Path
from urllib.parse import quote

import requests

HERE = Path(__file__).resolve().parent
EXPORTS = HERE.parent / "exports"
sys.path.insert(0, str(HERE))
import print_plate  # noqa: E402

BASE = "https://cad.onshape.com/api/v10"
NAME_PROPERTY = "57f3fb8efa3416c06701d60d"      # Onshape's "Name" metadata property
VIEW = "0.9013,-0.4333,0,0,0.255,0.5304,0.8085,0,-0.3503,-0.7286,0.5885,0"     # as add_gripper.py
VIEW_PLATE = "1,0,0,0,0,0.6601,0.7512,0,0,-0.7512,0.6601,0"   # render.py's print_layout.png camera
MOUNT, PLATE, ASM = "Mount parts (exports/assembly.step)", "Print plate (printed parts, A1 mini layout)", "Mount on gripper"


class Api:
    def __init__(self):
        self.s = requests.Session()
        self.s.auth = (os.environ["ONSHAPE_ACCESS_KEY"], os.environ["ONSHAPE_SECRET_KEY"])
        self.s.headers["Accept"] = "application/json;charset=UTF-8; qs=0.09"
        self.calls = 0

    def call(self, method, path, **kw):
        self.calls += 1
        r = self.s.request(method, BASE + path, timeout=180, **kw)
        if not r.ok:
            raise RuntimeError(f"{method} {path} -> HTTP {r.status_code}: {r.text[:600]}")
        return r.json() if r.content else {}

    def refused(self, method, path) -> str | None:
        """Make a call that the key may not be allowed to make; the refusal, or None if it worked."""
        try:
            self.call(method, path)
            return None
        except RuntimeError as err:
            return str(err).split(" -> ")[1][:60]


def import_step(api: Api, did: str, wid: str, path: Path) -> str:
    with path.open("rb") as fh:
        tr = api.call("POST", f"/translations/d/{did}/w/{wid}", files={"file": (path.name, fh, "application/octet-stream")},
                      data={"formatName": "", "flattenAssemblies": "true", "translate": "true"})
    for _ in range(24):
        time.sleep(5)
        st = api.call("GET", f"/translations/{tr['id']}")
        if st["requestState"] != "ACTIVE":
            break
    if st["requestState"] != "DONE":
        raise SystemExit(f"importing {path.name}: {st['requestState']} {st.get('failureReason')}")
    return st["resultElementIds"][0]


def rename(api: Api, did: str, wid: str, eid: str, name: str) -> None:
    api.call("POST", f"/metadata/d/{did}/w/{wid}/e/{eid}", json={"properties": [{"propertyId": NAME_PROPERTY, "value": name}]})


def shaded(api: Api, kind: str, did: str, wid: str, eid: str, view: str, out: Path) -> str | None:
    r = api.call("GET", f"/{kind}/d/{did}/w/{wid}/e/{eid}/shadedviews",
                 params={"viewMatrix": view, "outputWidth": 1400, "outputHeight": 900, "pixelSize": 0,
                         "edges": "show", "useAntiAliasing": "true"})
    img = (r.get("images") or [None])[0]
    if img:
        out.write_bytes(base64.b64decode(img))
        return out.name
    return None


def update(api: Api, did: str, wid: str, sha: str, rec: dict) -> None:
    doc = api.call("GET", f"/documents/{did}")
    if doc.get("public") or doc.get("isPublic"):
        raise SystemExit("the document is public; AgileX's STEP should not be in it")
    old_name = doc["name"]
    old_sha = (re.search(r"\(([0-9a-f]{7})\)", old_name) or [None, "previous"])[1]
    els = {e["name"]: e for e in api.call("GET", f"/documents/d/{did}/w/{wid}/elements")}
    rec["tabs_before"] = {n: e["elementType"] for n, e in els.items()}
    old_mount, asm, empty = els[MOUNT]["id"], els[ASM]["id"], els.get("Part Studio 1", {}).get("id")
    old_plate = els.get(PLATE, {}).get("id")      # from an earlier update_doc.py run

    # 1. The document as it stands, kept as a version.
    v = api.call("POST", f"/documents/d/{did}/versions",
                 json={"documentId": did, "workspaceId": wid, "name": f"{old_sha} (before {sha})",
                       "description": f"{old_name}, as it stood before the update to {sha} on {rec['date']}."})
    rec["version_before"] = {"name": v["name"], "url": f"https://cad.onshape.com/documents/{did}/v/{v['id']}"}

    # 2. The new parts, and the plate.
    with tempfile.TemporaryDirectory() as tmp:
        plate_step = Path(tmp) / "print_plate.step"
        assy, check = print_plate.plate(print_plate.Params())
        if not all(check[n]["ok"] for n in print_plate.PRINTED):
            raise SystemExit("a part doesn't match its STL; re-export before uploading")
        assy.export(str(plate_step))
        rec["imports"] = {"assembly.step": (new_mount := import_step(api, did, wid, EXPORTS / "assembly.step"))}
        rec["imports"]["print_plate.step"] = (plate := import_step(api, did, wid, plate_step))

    # 3. Swap the mount in the assembly; delete or rename the old tabs.
    inst = api.call("GET", f"/assemblies/d/{did}/w/{wid}/e/{asm}")["rootAssembly"]["instances"]
    old = [i["id"] for i in inst if i.get("elementId") == old_mount]
    node = lambda nid: f"/assemblies/d/{did}/w/{wid}/e/{asm}/instance/nodeid/{quote(nid, safe='')}"
    refusal = api.refused("DELETE", node(old[0]))
    if refusal is None:
        for nid in old[1:]:
            api.call("DELETE", node(nid))
        rec["assembly"] = f"{ASM}: deleted the old mount's {len(old)} part instances, inserted the new mount whole"
    else:
        rename(api, did, wid, asm, f"{ASM}, {old_sha} (superseded)")
        asm = api.call("POST", f"/assemblies/d/{did}/w/{wid}", json={"name": ASM})["id"]
        api.call("POST", f"/assemblies/d/{did}/w/{wid}/e/{asm}/instances",
                 json={"documentId": did, "elementId": els["AgileX gripper (reference, do not share)"]["id"],
                       "isWholePartStudio": True, "isAssembly": False})
        rec["assembly"] = (f"deleting an instance was refused ({refusal}), so the old assembly was renamed "
                           f"and a new {ASM!r} tab holds the gripper and the new mount")
    api.call("POST", f"/assemblies/d/{did}/w/{wid}/e/{asm}/instances",
             json={"documentId": did, "elementId": new_mount, "isWholePartStudio": True, "isAssembly": False})
    rename(api, did, wid, new_mount, MOUNT)
    rename(api, did, wid, plate, PLATE)
    rec["deleted"] = {}
    for label, eid, old_label in (("old mount Part Studio", old_mount, f"OLD {old_sha}, superseded: do not print"),
                                  ("old print plate", old_plate, f"OLD {old_sha} print plate, superseded: do not print"),
                                  ("Part Studio 1 (empty default)", empty, None)):
        if eid is None:
            continue
        refusal = api.refused("DELETE", f"/elements/d/{did}/w/{wid}/e/{eid}")
        rec["deleted"][label] = "deleted" if refusal is None else f"refused ({refusal})"
        if refusal is not None and old_label:
            rename(api, did, wid, eid, old_label)

    # 4. Name, check, pictures, version.
    name = f"PiPER wrist camera mount ({sha})"
    api.call("POST", f"/documents/{did}", json={"name": name})
    rec["name"] = {"before": old_name, "after": name}
    parts = api.call("GET", f"/parts/d/{did}/w/{wid}/e/{plate}")
    mp = api.call("GET", f"/partstudios/d/{did}/w/{wid}/e/{plate}/massproperties", params={"massAsGroup": "false"})
    vols = [[p["name"], round(((mp.get("bodies") or {}).get(p["partId"]) or {}).get("volume", [0])[0] * 1e9, 1)]
            for p in parts]      # a list: the 4 spacers come in as 4 parts with one name
    rec["print_plate"] = {"parts_in_onshape": vols, "check_against_stl": {n: check[n] for n in print_plate.PRINTED},
                          "layout": check["placed"]}
    rec["shaded_views"] = [shaded(api, "partstudios", did, wid, plate, VIEW_PLATE, HERE / "onshape_print_plate.png"),
                           shaded(api, "partstudios", did, wid, new_mount, VIEW, HERE / "onshape_assembly.png"),
                           shaded(api, "assemblies", did, wid, asm, VIEW, HERE / "onshape_on_gripper.png")]
    rec["tabs_after"] = {e["name"]: e["elementType"] for e in api.call("GET", f"/documents/d/{did}/w/{wid}/elements")}
    v = api.call("POST", f"/documents/d/{did}/versions",
                 json={"documentId": did, "workspaceId": wid, "name": sha,
                       "description": f"This PR's parts at {sha}, with a print plate of the printed parts."})
    rec["version_after"] = {"name": v["name"], "url": f"https://cad.onshape.com/documents/{did}/v/{v['id']}"}


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--doc", required=True)
    ap.add_argument("--ws", required=True)
    args = ap.parse_args()
    did, wid = args.doc, args.ws
    sha = subprocess.run(["git", "rev-parse", "--short=7", "HEAD"], capture_output=True, text=True).stdout.strip()
    api = Api()
    rec: dict = {"date": time.strftime("%Y-%m-%d"), "commit": sha, "document": f"https://cad.onshape.com/documents/{did}/w/{wid}"}

    try:
        update(api, did, wid, sha, rec)
    except BaseException as err:     # keep what was done, so a failed run can be finished by hand
        rec["stopped"] = repr(err)[:300]
        raise
    finally:
        rec["api_calls_used"] = api.calls
        (HERE / f"run_{rec['date']}_update.json").write_text(json.dumps(rec, indent=2, ensure_ascii=False) + "\n")
        print(json.dumps(rec, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
