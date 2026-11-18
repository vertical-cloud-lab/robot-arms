"""Upload the auger-swap STEP models to Onshape and render them there (issue #42).

1. creates a document owned by the "Vertical Cloud Lab" Onshape company (or reuses the
   one recorded in ``onshape/onshape_document.json``),
2. imports each STEP from ``cad/`` (``export_step.py``) as a flattened Part Studio and
   names the tab; a STEP whose sha256 changed is imported again and the old tab renamed
   "(superseded, safe to delete)" (the API key has no delete scope),
3. builds one assembly per strategy: the doser Part Studio + the strategy's Part Studio,
   both whole-Part-Studio instances at identity (everything is in the doser's frame),
4. saves Onshape's shaded views to ``onshape/*.png``.

Needs ONSHAPE_ACCESS_KEY / ONSHAPE_SECRET_KEY (an API key pair of a company member).

    python onshape_upload.py              # sync + render
    python onshape_upload.py --view-only  # just re-render the recorded document
    python onshape_upload.py --only alt_a_sleeves_pin.step alt_b_sleeves.step   # just these STEPs and their assemblies
"""
from __future__ import annotations

import argparse
import base64
import hashlib
import json
import os
import time
from pathlib import Path

import numpy as np
import requests
from requests.auth import HTTPBasicAuth

HERE = Path(__file__).resolve().parent
CAD = HERE / "cad"
OUT = HERE / "onshape"
DOC_JSON = OUT / "onshape_document.json"
API = "https://cad.onshape.com/api/v10"
COMPANY_NAME = "Vertical Cloud Lab"
DOC_NAME = "PiPER auger-swap end effectors - medium fidelity (robot-arms #42)"
NAME_PROP = "57f3fb8efa3416c06701d60d"   # Onshape "Name" metadata property
FOLDER = ("9a78d7989a97567e68bc153a", "vcl-shared > 6DOF Robot Arm")   # where the PiPER docs live

STUDIOS = {   # STEP file -> tab name
    "doser_compliant_clips.step": "Doser + compliant clips + finger fixture",
    "s1_two_servo_tool.step": "S1 two-servo tool",
    "s2_one_servo_wheel_tool.step": "S2 one-servo wheel tool",
    "alt_a_sleeves_pin.step": "Alt A sleeves + tilt-lock slider",
    "alt_b_sleeves.step": "Alt B sleeves",
    "alt_a_custom_fingers_pin.step": "Alt A custom fingers + tilt-lock slider",
    "agilex_gripper_ref_alt_a.step": "AgileX gripper (reference), Alt A pose",
    "agilex_gripper_ref_alt_a_cf.step": "AgileX gripper (reference), custom-finger pose",
}
ASSEMBLIES = {   # tab name -> (strategy STEP(s), close-up target (doser frame, mm), view direction, m/px)
    "Strategy 1": ("s1_two_servo_tool.step", (0.0, 149.0, 95.0), (1.0, -0.6, 1.25), 0.00022),
    "Strategy 2": ("s2_one_servo_wheel_tool.step", (0.0, 140.0, 80.0), (1.0, -0.6, 1.25), 0.00017),
    "Alternative A": (("alt_a_sleeves_pin.step", "agilex_gripper_ref_alt_a.step"), (30.0, 200.0, 90.0), (0.55, 1.0, 0.75), 0.00026),
    "Alternative B": (("alt_b_sleeves.step", "agilex_gripper_ref_alt_a.step"), (0.0, 210.0, 90.0), (0.45, 1.0, 0.7), 0.00024),
    "Alternative A custom fingers": (("alt_a_custom_fingers_pin.step", "agilex_gripper_ref_alt_a_cf.step"),
                                       (30.0, 200.0, 80.0), (0.55, 1.0, 0.75), 0.00024),
}


def _files(f):
    return (f,) if isinstance(f, str) else tuple(f)


class Onshape:
    def __init__(self):
        self.auth = HTTPBasicAuth(os.environ["ONSHAPE_ACCESS_KEY"], os.environ["ONSHAPE_SECRET_KEY"])
        self.s = requests.Session()

    def req(self, method, path, **kw):
        kw.setdefault("timeout", 300)
        headers = kw.pop("headers", {})
        headers.setdefault("Accept", "application/json;charset=UTF-8; qs=0.09")
        for attempt in range(5):
            r = self.s.request(method, API + path, auth=self.auth, headers=headers, **kw)
            if r.status_code in (429, 502, 503, 504):
                time.sleep(5 * (attempt + 1))
                continue
            break
        if not r.ok:
            raise RuntimeError(f"{method} {path} -> {r.status_code}: {r.text[:400]}")
        return r.json() if r.content and "json" in r.headers.get("Content-Type", "") else r

    def get(self, p, **kw):
        return self.req("GET", p, **kw)

    def post(self, p, **kw):
        return self.req("POST", p, **kw)


def company_id(c: Onshape) -> str:
    for it in c.get("/companies")["items"]:
        if it["name"] == COMPANY_NAME:
            return it["id"]
    raise RuntimeError(f"not a member of {COMPANY_NAME}")


def rename_element(c: Onshape, did, wid, eid, name) -> None:
    try:
        c.post(f"/metadata/d/{did}/w/{wid}/e/{eid}",
               json={"properties": [{"propertyId": NAME_PROP, "value": name}]})
    except RuntimeError as e:
        print("could not rename tab:", str(e)[:160])


def import_step(c: Onshape, did, wid, path: Path) -> str:
    data = path.read_bytes()
    files = {"file": (path.name, data, "application/step")}
    form = {"encodedFilename": path.name, "fileContentLength": str(len(data)), "translate": "true",
            "flattenAssemblies": "true", "yAxisIsUp": "false", "storeInDocument": "false"}
    res = c.post(f"/blobelements/d/{did}/w/{wid}", files=files, data=form, timeout=900)
    tid = res.get("translationId") or res["id"]
    for _ in range(400):
        st = c.get(f"/translations/{tid}")
        if st["requestState"] == "DONE":
            return st["resultElementIds"][0]
        if st["requestState"] == "FAILED":
            raise RuntimeError(f"translation of {path.name} failed: {st.get('failureReason')}")
        time.sleep(3)
    raise RuntimeError(f"translation of {path.name} timed out")


def _import_feature(c: Onshape, did, wid, eid):
    """(features response, the importForeign feature, its blob element id)."""
    fs = c.get(f"/partstudios/d/{did}/w/{wid}/e/{eid}/features")
    for ft in fs["features"]:
        if ft["featureType"] == "importForeign":
            for prm in ft["parameters"]:
                if prm["parameterId"] == "blobData":
                    return fs, ft, prm["namespace"].split("::")[0][1:]
    return fs, None, None


def update_in_place(c: Onshape, did, wid, eid, path: Path) -> bool:
    """Swap the geometry of an imported Part Studio without a new tab: upload the STEP over
    the blob its Import feature reads, then point the feature at the blob's new microversion
    (same approach as powder-doser's onshape_build.py)."""
    fs, ft, blob = _import_feature(c, did, wid, eid)
    if ft is None:
        return False
    data = path.read_bytes()
    c.post(f"/blobelements/d/{did}/w/{wid}/e/{blob}", files={"file": (path.name, data, "application/step")},
           data={"encodedFilename": path.name, "fileContentLength": str(len(data))}, timeout=900)
    mv = next(e["microversionId"] for e in c.get(f"/documents/d/{did}/w/{wid}/elements") if e["id"] == blob)
    for prm in ft["parameters"]:
        if prm["parameterId"] == "blobData":
            prm["namespace"] = f"e{blob}::m{mv}"
    fs = c.get(f"/partstudios/d/{did}/w/{wid}/e/{eid}/features")
    c.post(f"/partstudios/d/{did}/w/{wid}/e/{eid}/features/featureid/{ft['featureId']}",
           json={"feature": ft, "serializationVersion": fs["serializationVersion"],
                 "sourceMicroversion": fs["sourceMicroversion"]})
    return True


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def save_rec(rec):
    OUT.mkdir(exist_ok=True)
    DOC_JSON.write_text(json.dumps(rec, indent=1) + "\n")


def url(rec, eid=None) -> str:
    u = f"https://cad.onshape.com/documents/{rec['documentId']}/w/{rec['workspaceId']}"
    return u + (f"/e/{eid}" if eid else "")


def fill_assembly(c: Onshape, did, wid, aid, studio_ids) -> None:
    """Empty the assembly, then insert every part of each Part Studio at identity.  Inserting
    a whole Part Studio over the API places one instance per part as it is now, so the
    assembly is refilled whenever a Part Studio's geometry changes."""
    base = f"/assemblies/d/{did}/w/{wid}/e/{aid}"
    old = [i["id"] for i in c.get(base)["rootAssembly"]["instances"]]
    if old:
        c.post(f"{base}/modify", json={"deleteInstances": old, "editDescription": "refill from Part Studios"})
    for eid in studio_ids:
        c.post(f"{base}/instances", json={"documentId": did, "elementId": eid,
                                          "isAssembly": False, "isWholePartStudio": True})


def sync(c: Onshape, rebuild: bool = False, only=None) -> dict:
    if DOC_JSON.exists():
        rec = json.loads(DOC_JSON.read_text())
    else:
        doc = c.post("/documents", json={
            "name": DOC_NAME, "ownerId": company_id(c), "ownerType": 1, "isPublic": False,
            "description": "Medium-fidelity models for https://github.com/vertical-cloud-lab/robot-arms/issues/42 : "
                           "powder doser with compliant funnel clips + finger fixture, two custom PiPER tools "
                           "(two-servo, one-servo wheel) and stock-gripper sleeves (+ tilt-lock pin). Built by "
                           "end-effectors/auger-swap/export_step.py + onshape_upload.py in vertical-cloud-lab/robot-arms."})
        rec = {"documentId": doc["id"], "workspaceId": doc["defaultWorkspace"]["id"], "owner": COMPANY_NAME}
        rec["url"] = url(rec)
        try:
            c.post(f"/globaltreenodes/folder/{FOLDER[0]}",
                   json={"itemsToMove": [{"id": doc["id"], "resourceType": "document"}]})
            rec["folder"] = FOLDER[1]
        except RuntimeError as e:
            print("could not move the document into", FOLDER[1], str(e)[:160])
        save_rec(rec)
        print("created", rec["url"])
    did, wid = rec["documentId"], rec["workspaceId"]
    studios = rec.setdefault("partStudios", {})
    changed = set()
    for fname, tab in STUDIOS.items():
        if only and fname not in only:
            continue
        p = CAD / fname
        h = sha(p)
        old = studios.get(fname)
        if old and old["sha256"] == h:
            continue
        t0 = time.time()
        if old:
            try:
                if update_in_place(c, did, wid, old["elementId"], p):
                    old["sha256"] = h
                    if old.get("tab") != tab:
                        rename_element(c, did, wid, old["elementId"], tab)
                        old["tab"] = tab
                    changed.add(fname)
                    save_rec(rec)
                    print(f"updated {fname} in place ({time.time() - t0:.0f} s)", flush=True)
                    continue
            except RuntimeError as e:
                print(f"{fname}: in-place update failed ({str(e)[:160]}); re-importing")
        eid = import_step(c, did, wid, p)
        rename_element(c, did, wid, eid, tab)
        if old:
            rename_element(c, did, wid, old["elementId"], f"{tab} (superseded, safe to delete)")
        studios[fname] = {"elementId": eid, "sha256": h, "tab": tab, "url": url(rec, eid)}
        changed.add(fname)
        save_rec(rec)
        print(f"imported {fname} -> {eid} ({time.time() - t0:.0f} s)", flush=True)
    asms = rec.setdefault("assemblies", {})
    for name, (fname, *_) in ASSEMBLIES.items():
        a = asms.get(name)
        if a and not rebuild and not (changed & {"doser_compliant_clips.step", *_files(fname)}):
            continue
        if a:
            aid = a["elementId"]
        else:
            aid = None
            if not asms:
                for e in c.get(f"/documents/d/{did}/w/{wid}/elements", params={"elementType": "ASSEMBLY"}):
                    if e["name"] == "Assembly 1" and not c.get(
                            f"/assemblies/d/{did}/w/{wid}/e/{e['id']}")["rootAssembly"]["instances"]:
                        aid = e["id"]           # reuse the new document's empty default tab
                        break
            if aid is None:
                aid = c.post(f"/assemblies/d/{did}/w/{wid}", json={"name": name})["id"]
            rename_element(c, did, wid, aid, name)
        fill_assembly(c, did, wid, aid, [studios[f]["elementId"] for f in ("doser_compliant_clips.step", *_files(fname))])
        asms[name] = {"elementId": aid, "url": url(rec, aid)}
        save_rec(rec)
        print("assembly", name, asms[name]["url"], flush=True)
    return rec


def view_matrix(cam_dir, target_mm) -> str:
    """Onshape 3x4 view matrix (rows: screen right, screen up, towards the viewer; then the
    translation that puts the target at the image centre), metres."""
    back = np.asarray(cam_dir, float)
    back /= np.linalg.norm(back)
    right = np.cross([0.0, 0.0, 1.0], back)
    right /= np.linalg.norm(right)
    up = np.cross(back, right)
    R = np.vstack([right, up, back])
    t = -R @ (np.asarray(target_mm, float) / 1000.0)
    M = np.hstack([R, t[:, None]])
    return ",".join(f"{v:.6f}" for v in M.flatten())


def shaded(c: Onshape, path: str, out: Path, view="isometric", w=1400, h=1000, pixel=0.0) -> None:
    r = c.get(path + "/shadedviews", params={
        "viewMatrix": view, "outputHeight": h, "outputWidth": w, "pixelSize": pixel,
        "edges": "show", "useAntiAliasing": "true"})
    out.write_bytes(base64.b64decode(r["images"][0]))
    print("->", out.relative_to(HERE))


def render(c: Onshape, rec: dict, only=None) -> None:
    did, wid = rec["documentId"], rec["workspaceId"]
    ps = rec["partStudios"]["doser_compliant_clips.step"]["elementId"]
    if not only or "doser_compliant_clips.step" in only:
        shaded(c, f"/partstudios/d/{did}/w/{wid}/e/{ps}", OUT / "onshape_doser_clips_fixture_iso.png")
        shaded(c, f"/partstudios/d/{did}/w/{wid}/e/{ps}", OUT / "onshape_doser_clips_closeup.png",
               view=view_matrix((0.9, -0.75, 0.75), (40.0, 120.0, 50.0)), w=1400, h=1000, pixel=0.00022)
    for name, (fname, target, direction, px) in ASSEMBLIES.items():
        if only and not set(_files(fname)) & set(only):
            continue
        aid = rec["assemblies"][name]["elementId"]
        base = f"/assemblies/d/{did}/w/{wid}/e/{aid}"
        tag = name.lower().replace(" ", "_")
        shaded(c, base, OUT / f"onshape_{tag}_iso.png")
        shaded(c, base, OUT / f"onshape_{tag}_closeup.png",
               view=view_matrix(direction, target), w=1400, h=1000, pixel=px)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--view-only", action="store_true")
    ap.add_argument("--rebuild-assemblies", action="store_true", help="refill every assembly")
    ap.add_argument("--only", nargs="+", metavar="STEP", help="sync and render only these STEP files and the assemblies that use them")
    a = ap.parse_args()
    c = Onshape()
    rec = json.loads(DOC_JSON.read_text()) if a.view_only else sync(c, a.rebuild_assemblies, a.only)
    render(c, rec, a.only)


if __name__ == "__main__":
    main()
