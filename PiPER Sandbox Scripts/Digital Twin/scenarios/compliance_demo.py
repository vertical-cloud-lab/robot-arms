"""Scenario: compliant control, the groundwork for force-limited and contact-rich tasks.

Two short experiments with the Cartesian impedance controller (control/controllers.py), the
same law you would run on the real arm through piper_sdk's MIT mode (JointMitCtrl) with
tau = J^T (K dx - D v) + gravity:

1. Spring test: hold the gripper in the air and push it sideways with 5 N. It should give way
   by F / K (robot_piper.yaml control.cartesian_stiffness), then spring back.
2. Press test: aim the closed fingertips 10 mm *below* the shelf top. The arm stops on the
   shelf and presses with about K_z x 10 mm, so the commanded stiffness sets the contact
   force: a stiff position controller would press as hard as its motors allow instead.

    python run_sim.py --scenario compliance_demo
"""
from __future__ import annotations

import numpy as np

from digital_twin.sim import ready
from digital_twin.tasks.pick_place import PickPlace


def run(sim, args) -> dict:
    if not sim.engine.has_dynamics:
        print("compliance needs a physics engine: use --engine mujoco")
        return {}
    r, e = sim.robot, sim.engine
    out = {}
    ready(sim)
    r.set_gripper(width_m=0.0)
    K = np.asarray(sim.cfg.robot["control"]["cartesian_stiffness"], float)

    # 1. Spring test.
    T0 = r.tcp_world()
    r.compliant(T0, 1.0)
    p_before = r.tcp_world()[:3, 3].copy()
    e.push("link6", [5.0, 0.0, 0.0], point_world=p_before)  # at the fingertips
    r.compliant(T0, 1.5)
    p_pushed = r.tcp_world()[:3, 3].copy()
    e.push("link6", [0.0, 0.0, 0.0])
    r.compliant(T0, 1.5)
    p_after = r.tcp_world()[:3, 3].copy()
    dx = (p_pushed - p_before)[0] * 1000
    print(f"spring test: 5 N sideways moved the TCP {dx:.1f} mm (F/K = {5 / K[0] * 1000:.1f} mm), "
          f"{np.linalg.norm(p_after - p_before) * 1000:.2f} mm off after release")
    out["spring"] = {"push_n": 5.0, "deflection_mm": round(float(dx), 2),
                     "expected_mm": round(5 / K[0] * 1000, 2)}

    # 2. Press test, at the shelf spot nearest the arm.
    pp = PickPlace(sim.cell, r, sim.cfg)
    pp.pad_half_gap = 0.003
    spot = None
    shelf_T = sim.cell.poses0["shelf"]
    for (x, y) in sim.cell.shelf.spots(10):
        w = shelf_T @ np.array([x / 1000, y / 1000, 0, 1.0])
        if spot is None or np.linalg.norm(w[:2] - sim.cell.arm_pose[:2, 3]) < np.linalg.norm(spot[:2] - sim.cell.arm_pose[:2, 3]):
            spot = w[:3]
    p = spot + np.array([0, 0, 0.010])
    u = p[:2] - sim.cell.arm_pose[:2, 3]
    u /= np.linalg.norm(u)
    sol = pp.solve_grasp(p, [np.array([-u[1], u[0], 0.0])], r.q_ref, rise=0.05)
    T_above, q_above = sol[2], sol[3]
    pp.transit(T_above, q_above, "press: above the shelf")
    r.move_linear(sol[0], label="press: 10 mm above")
    fingers = ["finger1", "finger2"]
    rows = []
    for kz in (400.0, 800.0, 1600.0):
        r.cart_ctrl.K[2, 2] = kz
        r.cart_ctrl.D[2, 2] = 2 * np.sqrt(kz)
        T_press = sol[0].copy()
        T_press[2, 3] -= 0.020  # the TCP starts 10 mm above the shelf: aim 10 mm into it
        r.compliant(T_press, 1.5, label=f"press: K_z {kz:.0f} N/m")
        forces = []
        for _ in range(10):  # average over the last 0.1 s, still under impedance control
            r.mode, r.T_ref = "cartesian", T_press
            r.run(0.01)
            forces.append(e.contact_force(fingers, ["shelf"]))
        r.mode = "joint"
        f = float(np.mean(forces))
        rows.append({"kz_n_per_m": kz, "force_n": round(float(f), 2), "expected_n": round(kz * 0.010, 2)})
        print(f"press test: K_z {kz:5.0f} N/m, aimed 10 mm into the shelf -> {f:5.2f} N on the shelf "
              f"(K_z x 10 mm = {kz * 0.010:.1f} N)")
        r.compliant(sol[0], 0.8, label="press: lift off")
    r.cart_ctrl.K[2, 2] = K[2]
    r.cart_ctrl.D[2, 2] = 2 * np.sqrt(K[2])
    out["press"] = rows
    r.move_linear(T_above, label="press: retreat")
    return out
