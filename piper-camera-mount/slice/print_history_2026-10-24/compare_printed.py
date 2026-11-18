"""Compare the meshes inside the A1 mini plate 3MFs (as printed) with the STLs at a commit.
Fingerprint per mesh: triangle count, volume and area (both rotation- and translation-invariant)."""
import io, re, struct, subprocess, sys, zipfile, json
import numpy as np

REPO = "/home/runner/work/robot-arms/robot-arms"
def blob(commit, path):
    return subprocess.run(["git", "-C", REPO, "show", f"{commit}:{path}"], capture_output=True, check=True).stdout

def stats(v, t):
    a, b, c = v[t[:, 0]], v[t[:, 1]], v[t[:, 2]]
    vol = np.einsum("ij,ij->i", a, np.cross(b, c)).sum() / 6
    area = np.linalg.norm(np.cross(b - a, c - a), axis=1).sum() / 2
    return {"tris": int(len(t)), "volume_mm3": round(abs(vol), 2), "area_mm2": round(area, 2)}

def stl(data):
    n = struct.unpack("<I", data[80:84])[0]
    rec = np.frombuffer(data[84:84 + 50 * n], dtype=np.dtype([("n", "<3f4"), ("v", "<9f4"), ("a", "<u2")]))
    v = rec["v"].reshape(-1, 3).astype(float)
    return stats(v, np.arange(len(v)).reshape(-1, 3))

def threemf_objects(data):
    z = zipfile.ZipFile(io.BytesIO(data))
    out = {}
    for name in sorted(n for n in z.namelist() if n.startswith("3D/Objects/") and n.endswith(".model")):
        x = z.read(name).decode()
        v = np.array(re.findall(r'<vertex x="([^"]+)" y="([^"]+)" z="([^"]+)"', x), dtype=float)
        t = np.array(re.findall(r'<triangle v1="(\d+)" v2="(\d+)" v3="(\d+)"', x), dtype=int)
        if len(t):
            out[name.split("/")[-1]] = stats(v, t)
    names = dict(re.findall(r'<object id="(\d+)"[^>]*?name="([^"]*)"', z.read("Metadata/model_settings.config").decode()))
    return out, names

parts = ["bracket", "pod", "carrier", "spacers", "tag_wedge"]
head = sys.argv[1] if len(sys.argv) > 1 else "HEAD"
ref = {p: stl(blob(head, f"piper-camera-mount/exports/{p}.stl")) for p in parts}
old = {p: stl(blob("801431a", f"piper-camera-mount/exports/{p}.stl")) for p in parts}
res = {"head_stls": ref, "801431a_stls": old, "plates": {}}
for label, commit in [("2026-10-08 (source plate 801431a = byu-vcl b3dba57)", "801431a"), ("2026-10-13 (plate b6e2da0, same bytes at HEAD)", head)]:
    objs, names = threemf_objects(blob(commit, "piper-camera-mount/slice/piper_camera_mount_A1mini_PLA.3mf"))
    rows = []
    for k, s in objs.items():
        match = [p for p in parts if ref[p]["tris"] == s["tris"] and abs(ref[p]["volume_mm3"] - s["volume_mm3"]) < 0.05 and abs(ref[p]["area_mm2"] - s["area_mm2"]) < 0.05]
        match_old = [p for p in parts if old[p]["tris"] == s["tris"] and abs(old[p]["volume_mm3"] - s["volume_mm3"]) < 0.05]
        rows.append({"object": k, **s, "same_as_HEAD_stl": match, "same_as_801431a_stl": match_old})
    res["plates"][label] = rows
print(json.dumps(res, indent=1))
