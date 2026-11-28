import sys, time, json, numpy as np
sys.path.insert(0, "/tmp/ext/ml-amp/src/amp/harnesses/_sdk_amp1_basic")
import robolab_harness as rh
from PIL import Image
ep = rh.Episode(worker_url="http://127.0.0.1:8765")
t = time.time(); obs = ep.observe(); print("observe", round(time.time()-t, 2), "s")
emb = obs["embodiment"]
print(obs["instruction"], ep.budget())
print(emb["name"], [(c["name"], c["role"]) for c in emb["cameras"]], [a["joints"] for a in emb["arms"]])
print("ee:", json.dumps(emb["end_effectors"][0])[:600])
print("workspace", emb["workspace"])
print("tcp", np.round(obs["robot"]["tcp_pose"], 3), "grip", obs["robot"]["gripper_measured"])
t = time.time(); objs = ep.objects(); print("objects", round(time.time()-t,2), "s")
for o in objs: print(" ", o.id, o.label, np.round(o.centroid, 3), np.round(o.size, 3))
img = ep.annotate("left", objects=True); img.save("ann_left.png") if hasattr(img, "save") else Image.fromarray(img).save("ann_left.png")
r = ep.render(view="iso"); r.save("iso.png")
tcp = obs["robot"]["tcp_pose"]
pv = ep.preview([rh.waypoint(2.0, rh.offset_pose(tcp, dz=0.05))])
print("preview ok", pv["ok"], rh.explain(pv), "dur", pv.get("duration"), "min", pv.get("min_duration"))
if pv["ok"]:
    t = time.time(); r = ep.execute(pv); print("execute", round(time.time()-t,2), "s", {k: r[k] for k in list(r)[:6]} if isinstance(r, dict) else r)
o2 = ep.observe(); print("tcp after", np.round(o2["robot"]["tcp_pose"][:3], 3), "last_chunk", o2.get("last_chunk"), ep.budget())
td = rh.top_down([0.27, 0.0, 0.10], 90)
print("top_down", np.round(td, 3)); ik = ep.ik(td); print("ik reachable", ik["reachable"], [ (round(s["pos_err_mm"],2), round(s["rot_err_deg"],2)) for s in ik["solutions"]][:2])
t = time.time(); g = ep.gripper(True); print("gripper close", round(time.time()-t,2), "s", ep.observe()["robot"]["gripper_measured"])
g = ep.gripper(False); print("gripper open", ep.observe()["robot"]["gripper_measured"])
