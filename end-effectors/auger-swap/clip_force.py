"""Rough snap force of the compliant C-clip (issue #42), to size the pull-out.

Each clip arm is a curved cantilever (mean radius 13.55 mm, 2 mm wall, 10 mm wide) from the
stem up to the lip.  A horizontal load P at the lip bends it (bending only, Castigliano):
delta = P / (E I) * integral (y_lip - y)^2 ds.  The Ø25 tube has to open the 17 mm mouth to
25 mm, 4 mm per lip.  With the lip edge as a point contact and Coulomb friction, the vertical
force on the tube is 2 N (sin a + mu cos a) while the lip is above the tube centre (pull-out)
and 2 N (-sin a + mu cos a) once it is below (push-in without a funnel).  The funnel lowers the
push-in force; it does nothing for pull-out.  Clip numbers are from Sam's multi-doser plate
(powder-doser PR 170 discussion); measure the printed clip before trusting these.

    python clip_force.py
"""
import math

import numpy as np

R_I, T_WALL, WIDTH = 12.55, 2.0, 10.0
MOUTH = 17.0
TUBE_R = 12.5
R_MEAN = R_I + T_WALL / 2
I = WIDTH * T_WALL ** 3 / 12
LIP_DEG = 90 - math.degrees(math.asin(MOUTH / 2 / R_I))     # 47.4° above horizontal
LIP_Z = R_I * math.cos(math.radians(90 - LIP_DEG))          # 9.24 mm above the axis


def lip_stiffness(E: float, root_deg: float) -> float:
    """N/mm at the lip for an arm fixed at root_deg (from +X, -90 = bottom of the ring)."""
    ph = np.radians(np.linspace(root_deg, LIP_DEG, 2000))
    y_lip = R_MEAN * math.sin(math.radians(LIP_DEG))
    c = np.trapezoid((y_lip - R_MEAN * np.sin(ph)) ** 2 * R_MEAN, ph)
    return E * I / c


def forces(E: float, root_deg: float, mu: float):
    k = lip_stiffness(E, root_deg)
    pull = push = 0.0
    for h in np.linspace(0, 25, 5001):            # tube centre height above its seat
        d = LIP_Z - h
        if abs(d) >= TUBE_R:
            continue
        x = math.sqrt(TUBE_R ** 2 - d ** 2)
        if x <= MOUTH / 2:
            continue
        a = math.atan2(d, x)
        n = k * (x - MOUTH / 2) / math.cos(a)
        pull = max(pull, 2 * n * (math.sin(a) + mu * math.cos(a)))
        push = max(push, 2 * n * (-math.sin(a) + mu * math.cos(a)))
    root_stress = k * 4.0 * (R_MEAN * math.sin(math.radians(LIP_DEG)) - R_MEAN * math.sin(math.radians(root_deg))) * (T_WALL / 2) / I
    return k, pull, push, root_stress


if __name__ == "__main__":
    print("material  E(MPa)  arm root  mu    lip k(N/mm)  pull-out/clip(N)  push-in no funnel(N)  root stress at 4 mm (MPa)")
    for name, E in (("PLA", 3300.0), ("PETG", 2000.0)):
        for root in (-64.0, -90.0):               # -64: stiff stem 12 mm wide; -90: arm bends from the bottom
            for mu in (0.2, 0.35):
                k, pull, push, s = forces(E, root, mu)
                print(f"{name:8s}  {E:6.0f}  {root:6.0f}°  {mu:4.2f}  {k:10.1f}  {pull:15.0f}  {push:19.0f}  {s:22.0f}")
