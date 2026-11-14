# Handoff: Digital Twin work in progress (PR #77)

A session building this folder may have stopped before finishing. If you are a later
`@claude` session picking this up: read this, finish the open items, then **delete this file**
in your final commit (the request on PR #77 asked for exactly that).

## Done so far
- `config/`: robot (DH, limits, gripper + sleeves), cell layout (estimates), AprilTags (the
  set listed on PR #77), prints (7, incl. action figure and model airplane), sim settings.
- `assets/piper/`: decimated PiPER meshes and inertias in the DH frames
  (`tools/build_piper_assets.py`).
- `digital_twin/`: kinematics (DH FK/Jacobian/IK), scene graph, world objects, print library,
  adhesion model, MuJoCo engine (builds MJCF, bonds that break, rendering), AprilTag textures.
- The cell builds and renders in MuJoCo (MuJoCo 4.0.1, Python 3.14 on the runner).

## Still to do (in order)
1. `digital_twin/control/`: controllers (joint PD + gravity comp = MIT mode, Cartesian
   impedance, gripper force), `SimPiper` with piper_sdk-like calls, trajectories.
2. `digital_twin/tasks/pick_place.py`: grasp -> twist/rock/pull release -> lift -> box/shelf.
3. `engines/kinematic_engine.py` (numpy-only fallback), `viz/` (matplotlib).
4. `run_sim.py`, `scenarios/clear_bed.py`, tests, README.
5. Run it, render a video/frames, post the summary on PR #77.
