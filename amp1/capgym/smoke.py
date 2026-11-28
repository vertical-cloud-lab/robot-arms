"""Smoke test: AMP's official CaP-Gym robosuite adapter, cube_lifting, rendered on CPU (Mesa EGL).

Run in the CaP-X robosuite venv with the client's environment:

    source /tmp/capgym_test/env.sh && python /tmp/capgym_test/smoke.py

It starts the way `python -m amp.robots.capgym` does (affinity, boundary hook, sandbox guards),
builds the adapter the backend would (task set capgym_robosuite_cube, cameras "droid", seed 0),
loads cube_lifting, resets episode 0, holds the arm for --steps control steps with the gripper
open, saves the scene camera's RGB and a depth picture, and prints timings. No robot server, no
model: the frame is packed with the client's own pack_frame instead of being sent.
"""

from __future__ import annotations

import argparse
import os
import sys
import time

T_START = time.perf_counter()

# What amp/robots/capgym/__main__.py and client.main() do before building the adapter.
from amp.robots.capgym import affinity  # noqa: E402

affinity.apply()
from amp.robots.capgym import boundary  # noqa: E402

boundary.install()
from amp.robots.capgym import sandbox  # noqa: E402

sandbox.install()
boundary.bind("robosuite")

import numpy as np  # noqa: E402

TASK_SET = "capgym_robosuite_cube"
CAMERAS = "droid"  # SlotSpec.cameras default, what CapgymBackend.command passes as --cameras


def depth_picture(depth: np.ndarray, path: str, title: str) -> None:
    """Metric depth as a one-hue sequential heatmap (near = light, far = dark) with a colorbar."""
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.colors import LinearSegmentedColormap

    # single-hue blue ramp, steps 100 -> 700 (dataviz skill's sequential default)
    ramp = ["#cce3fd", "#b6d5f8", "#9dc8f7", "#84b9f3", "#6aabf1", "#519ced", "#338ced",
            "#257de0", "#2370cd", "#1b64be", "#1757ac", "#0f4a96", "#0e3d7e"]
    cmap = LinearSegmentedColormap.from_list("depth_blue", ramp)
    cmap.set_bad("#9a9a9a")
    d = np.asarray(depth, dtype=np.float64)
    valid = np.isfinite(d) & (d > 0)
    lo, hi = (np.percentile(d[valid], [1, 99]) if valid.any() else (0.0, 1.0))
    fig, ax = plt.subplots(figsize=(6.4, 5.4), dpi=100)
    im = ax.imshow(np.where(valid, d, np.nan), cmap=cmap, vmin=lo, vmax=hi,
                   interpolation="nearest")
    ax.set_axis_off()
    ax.set_title(title, fontsize=10, color="#1f1f1f")
    cb = fig.colorbar(im, ax=ax, fraction=0.046, pad=0.03)
    cb.set_label("depth, optical z (m)", color="#1f1f1f")
    cb.outline.set_visible(False)
    cb.ax.tick_params(colors="#4a4a4a", labelsize=8)
    fig.tight_layout()
    fig.savefig(path)
    plt.close(fig)


def gl_strings() -> dict:
    """The current GL context's vendor/renderer/version (the one robosuite just rendered with)."""
    try:
        from OpenGL import GL

        return {k: GL.glGetString(getattr(GL, f"GL_{k.upper()}")).decode()
                for k in ("vendor", "renderer", "version")}
    except Exception as exc:  # noqa: BLE001
        return {"error": repr(exc)}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--task", default="cube_lifting")
    ap.add_argument("--episode", type=int, default=0)
    ap.add_argument("--steps", type=int, default=20)
    ap.add_argument("--out", default="/tmp/capgym_test")
    ap.add_argument("--render-repeats", type=int, default=10,
                    help="extra bare camera renders to time the renderer alone")
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)

    print("python", sys.version.split()[0], sys.executable)
    for k in ("MUJOCO_GL", "PYOPENGL_PLATFORM", "MUJOCO_EGL_DEVICE_ID", "CUDA_VISIBLE_DEVICES",
              "AMP_CAPX_ROOT", "PYTHONPATH", "OMP_NUM_THREADS", "AMP_CAPGYM_SANDBOX", "TMPDIR"):
        print(f"  {k}={os.environ.get(k)!r}")

    t = time.perf_counter()
    from amp.robots.capgym import official_robosuite as OR

    adapter = OR.make_adapter(task_set=TASK_SET, cameras=CAMERAS, seed=0)
    t_make = time.perf_counter() - t
    spec = adapter.embodiment()
    print(f"\nmake_adapter({TASK_SET!r}, cameras={CAMERAS!r}, seed=0): {t_make:.2f} s "
          f"(imports incl.)")
    print(f"embodiment: {spec.name}  dof={spec.dof} action_dim={spec.action_dim} "
          f"control_dt(spec)={spec.control_dt}")
    print(f"success_checks: {adapter.success_checks()}  features: {adapter.features}")
    tasks = adapter.tasks()
    print(f"tasks() -> {len(tasks)}:")
    for tk in tasks:
        print(f"  {tk['name']}: {tk['instruction']!r} attributes={tk['attributes']} "
              f"episode_length_s={tk['episode_length_s']}")

    t = time.perf_counter()
    adapter.load(a.task)
    t_load = time.perf_counter() - t
    print(f"\nload({a.task!r}): {t_load:.2f} s  controller_cfg={adapter.controller_cfg}")
    desc, meshes = adapter.robot_description()
    print(f"robot_description: root={desc.root} links={len(desc.links)} "
          f"joints={len(desc.joints)} meshes={len(meshes)}")

    t = time.perf_counter()
    adapter.reset(a.episode)
    t_reset = time.perf_counter() - t
    print(f"reset({a.episode}): {t_reset:.2f} s  unit={adapter.unit}")
    print(f"control_dt()={adapter.control_dt()}  horizon()={adapter.horizon()}  "
          f"fingerprint={adapter.fingerprint()}")

    t = time.perf_counter()
    frame0 = adapter.observe()
    t_obs0 = time.perf_counter() - t
    print(f"\nobserve() #0 (first render): {t_obs0 * 1e3:.1f} ms")
    print("GL:", gl_strings())
    q0 = np.asarray(frame0.q, dtype=np.float64)
    np.set_printoptions(precision=4, suppress=True)
    print("q =", q0)
    print("grippers =", frame0.grippers)
    for name, (pos, quat) in frame0.ee.items():
        print(f"ee[{name}] pos={pos} quat_wxyz={quat}")
    for name, cam in frame0.cameras.items():
        d = cam.depth
        print(f"camera {name}: rgb {cam.rgb.shape} {cam.rgb.dtype}, depth "
              f"{None if d is None else (d.shape, str(d.dtype))}, depth range "
              f"[{np.nanmin(d):.3f}, {np.nanmax(d):.3f}] m, median {np.nanmedian(d):.3f} m")
        print("  K =", cam.K.tolist())
        print("  T_root_cam translation =", cam.T_root_cam[:3, 3])

    from PIL import Image

    cam_name = next(iter(frame0.cameras))
    Image.fromarray(frame0.cameras[cam_name].rgb).save(os.path.join(a.out, "frame0.png"))
    depth_picture(frame0.cameras[cam_name].depth, os.path.join(a.out, "depth0.png"),
                  f"{a.task} episode {a.episode}, {cam_name} depth after reset")

    # The client packs every frame for the wire before sending it; do the same, without a server.
    from amp.robots.capgym.client import pack_frame, rig

    names = rig(CAMERAS, spec)
    t = time.perf_counter()
    header, blobs, encodings = pack_frame(
        frame0, episode=a.episode, step=0, control_dt=adapter.control_dt(),
        max_steps=adapter.horizon(), instruction=tasks[0]["instruction"], task=a.task,
        cameras=names, dof=spec.dof, spec=spec)
    t_pack = time.perf_counter() - t
    sizes = [len(b) for b in blobs] if isinstance(blobs, (list, tuple)) else type(blobs).__name__
    print(f"pack_frame: {t_pack * 1e3:.1f} ms, rig={names}, header keys="
          f"{sorted(header)[:12]}..., blobs={sizes}, encodings={encodings}")

    # Hold: the reset pose's q as the joint targets, gripper01 = 0 (open), for --steps steps,
    # in the client's order (observe, then apply).
    hold = np.concatenate([q0, [0.0]])
    obs_ms, apply_ms = [], []
    frame = frame0
    for _ in range(a.steps):
        t = time.perf_counter()
        frame = adapter.observe()
        t1 = time.perf_counter()
        adapter.apply(hold)
        t2 = time.perf_counter()
        obs_ms.append((t1 - t) * 1e3)
        apply_ms.append((t2 - t1) * 1e3)
    t = time.perf_counter()
    frame = adapter.observe()
    obs_ms.append((time.perf_counter() - t) * 1e3)
    drift = np.abs(np.asarray(frame.q) - q0)
    print(f"\n{a.steps} hold steps: sim steps now {adapter.sim_steps()}, horizon() "
          f"{adapter.horizon()}")
    print(f"observe(): mean {np.mean(obs_ms):.1f} ms, median {np.median(obs_ms):.1f} ms, "
          f"max {np.max(obs_ms):.1f} ms over {len(obs_ms)} calls")
    print(f"apply():   mean {np.mean(apply_ms):.1f} ms, median {np.median(apply_ms):.1f} ms, "
          f"max {np.max(apply_ms):.1f} ms over {len(apply_ms)} calls")
    print("q after hold =", np.asarray(frame.q))
    print("|q - q0| =", drift, " max", float(drift.max()))
    print("gripper after hold =", frame.grippers)
    Image.fromarray(frame.cameras[cam_name].rgb).save(
        os.path.join(a.out, f"frame{a.steps}.png"))

    # The renderer alone: robosuite's camera sensor (rgb + depth) + metric depth, as observe does.
    rend = []
    for _ in range(a.render_repeats):
        t = time.perf_counter()
        OR.render_camera(adapter.env, cam_name)
        rend.append((time.perf_counter() - t) * 1e3)
    if rend:
        print(f"render_camera({cam_name!r}) alone: mean {np.mean(rend):.1f} ms, median "
              f"{np.median(rend):.1f} ms over {len(rend)} renders (512x512 rgb + depth)")

    t = time.perf_counter()
    ok, score = adapter.success()
    print(f"\nsuccess() = {(ok, score)}  ({(time.perf_counter() - t) * 1e3:.1f} ms)")
    print("provenance:", adapter.provenance())
    rec = boundary.record()
    print("boundary:", {k: rec.get(k) for k in ("ok", "family", "modules", "files",
                                                "violations", "spawned")})
    adapter.close()
    print(f"\ntimes: make_adapter {t_make:.2f} s, load {t_load:.2f} s, reset {t_reset:.2f} s, "
          f"first observe {t_obs0 * 1e3:.0f} ms; total {time.perf_counter() - T_START:.1f} s")
    print("saved:", [os.path.join(a.out, f) for f in
                     ("frame0.png", "depth0.png", f"frame{a.steps}.png")])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
