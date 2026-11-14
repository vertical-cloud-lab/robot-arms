"""Print-to-plate adhesion: the "little bit of stick", and when it lets go.

Model (engine-agnostic; each engine only has to report the bond's wrench and break it):

1. While bonded, a print is welded to the plate by a stiff constraint (MuJoCo: a `weld`
   equality, solved implicitly, so it is stable however stiff it is). The constraint carries
   whatever load the gripper puts through the print: that load is the bond's wrench.

2. The bond's strength comes from the print's footprint, the area actually touching the plate
   (rasterised at 0.5 mm from its convex parts, so a capsule lying on the plate gets a thin
   strip, a wing gets its whole outline):

       pull capacity   F_n = sigma * A                 (straight up)
       shear capacity  F_s = tau * A                   (sliding along the plate)
       peel capacity   M_x = sigma * I_x / c_y         (tipping about x: the footprint's
                       M_y = sigma * I_y / c_x          section modulus, like a beam)
       twist capacity  T   = tau * J / r_max           (turning about z)

   sigma = stick_kpa (prints.yaml / materials.py), tau = shear_ratio * sigma.

3. It breaks when the loads, each against its capacity, add up past one:

       (F_n+/F_n)^2 + (F_s/F_s)^2 + (M_x/M_x)^2 + (M_y/M_y)^2 + (T/T)^2 >= 1

   (F_n+ = tension only: pushing the print into the plate never breaks it). That is why
   rocking or twisting while lifting frees a print with less pull, as by hand. Once broken
   the bond stays broken; the print is then held only by friction and gravity.

The numbers are phenomenological, so calibrate them: pull a few real prints off with a
luggage scale and set stick_kpa to F / A.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from ..world.print_library import inside

RASTER_M = 0.0005  # footprint raster pitch
CONTACT_SLICE_M = 0.0003  # a part touches the plate where it is within 0.3 mm of it


@dataclass
class BondCapacity:
    area_m2: float
    centroid: np.ndarray  # (x, y) in the print frame, m
    pull_n: float
    shear_n: float
    peel_x_nm: float  # about the print's x axis through the centroid
    peel_y_nm: float
    twist_nm: float

    def summary(self) -> str:
        return (f"area {self.area_m2 * 1e6:.0f} mm^2: pull {self.pull_n:.2f} N, shear "
                f"{self.shear_n:.2f} N, peel {self.peel_x_nm * 1e3:.1f}/{self.peel_y_nm * 1e3:.1f} "
                f"N*mm, twist {self.twist_nm * 1e3:.1f} N*mm")


def footprint(geoms) -> np.ndarray:
    """(N, 2) raster points of the print's contact patch with the plate (print frame, m)."""
    from ..world.print_library import bounds
    lo, hi = bounds(geoms)
    xs = np.arange(lo[0], hi[0] + RASTER_M, RASTER_M)
    ys = np.arange(lo[1], hi[1] + RASTER_M, RASTER_M)
    X, Y = np.meshgrid(xs, ys)
    pts = np.column_stack([X.ravel(), Y.ravel(), np.full(X.size, CONTACT_SLICE_M)])
    mask = np.zeros(len(pts), bool)
    for g in geoms:
        mask |= inside(g, pts)
    return pts[mask, :2]


def capacity(geoms, stick_kpa: float, shear_ratio: float = 1.0) -> BondCapacity:
    """Bond capacities of a print from its geometry and bond stress (kPa)."""
    fp = footprint(geoms)
    sigma = stick_kpa * 1e3
    tau = shear_ratio * sigma
    if len(fp) == 0 or sigma <= 0:
        return BondCapacity(0.0, np.zeros(2), 0, 0, 0, 0, 0)
    dA = RASTER_M ** 2
    A = len(fp) * dA
    c = fp.mean(0)
    d = fp - c
    Ix = np.sum(d[:, 1] ** 2) * dA  # second moment for bending about x (lever arm along y)
    Iy = np.sum(d[:, 0] ** 2) * dA
    J = Ix + Iy
    cy = max(np.abs(d[:, 1]).max(), RASTER_M)
    cx = max(np.abs(d[:, 0]).max(), RASTER_M)
    rmax = max(np.linalg.norm(d, axis=1).max(), RASTER_M)
    return BondCapacity(A, c, sigma * A, tau * A, sigma * Ix / cy, sigma * Iy / cx, tau * J / rmax)


def failure_index(cap: BondCapacity, force_plate: np.ndarray, torque_plate_at_centroid: np.ndarray) -> float:
    """How close the bond is to breaking (>= 1 breaks). Inputs: the load the gripper puts on
    the bond, i.e. the force and torque the *bond* exerts on the print, negated, in the
    print's frame (z = plate normal), torque about the footprint's centroid."""
    if cap.pull_n <= 0:
        return np.inf
    F, M = force_plate, torque_plate_at_centroid
    tension = max(F[2], 0.0)
    terms = [tension / cap.pull_n, np.hypot(F[0], F[1]) / cap.shear_n,
             M[0] / cap.peel_x_nm, M[1] / cap.peel_y_nm, M[2] / cap.twist_nm]
    return float(np.sum(np.square(terms)))
