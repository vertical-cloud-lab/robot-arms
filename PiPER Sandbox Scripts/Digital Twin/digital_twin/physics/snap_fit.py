"""Snap-fit clips: the "little bit of stick" that holds an auger in the powder doser.

The doser's auger is a 25 mm tube held in two printed C-clips that open upward (powder-doser
PR 200, "Bracket Recreation"). Each clip wraps 280 deg around the tube: its mouth is only
17.5 mm wide, so the two arms spread 3.75 mm each as the tube passes, then spring back over it.
Pulling the auger out, or pushing it in, means beating that spring. This module computes the
force from the clip's measured geometry, with no tuning knobs beyond the material.

ENGINE-AGNOSTIC: everything here is plain numpy. An engine only has to call
`ClipContact.wrench(...)` every physics step and apply the result to the auger's body
(MuJoCo: `xfrc_applied`, see engines/mujoco_engine.py, `force_fields`).

The model, per clip (all in the clip's cross-section, mm; the seat centre is the origin):

1. ARM STIFFNESS (Castigliano, curved cantilever). Each arm is a circular arc of mean radius
   rho = seat radius + wall / 2, wall t, width b (the clip's 12 mm thickness), fixed where the
   ring joins the base (root_deg from the top) and free at the lip (lip angle). A horizontal
   force F at the lip moves it sideways by

       delta = F rho^3 / (E I) * integral_{lip}^{root} (cos(lip) - cos(theta))^2 d theta,
       I = b t^3 / 12,

   so k = F / delta. The root bending stress at full spread is reported as a design check.

2. CONTACT. The lip is a point at (+-x_lip, z_lip) that can only move sideways. With the tube's
   centre at (u, v), the tube's half-width at the lip's height is w = sqrt(r^2 - (z_lip - v)^2),
   and each lip is pushed out by delta = max(0, w +- u - x_lip). Its spring force k delta acts
   sideways, so the contact force along the tube's surface normal n (centre -> lip) is
   N = k delta / |n_x|, and the force on the tube is -N n: upward while the tube is above the
   lips (resisting insertion), downward once it is past them (holding it in: the "snap").
   Friction mu N opposes the tube's sliding at the lip, so pushing in and pulling out both
   take more than the frictionless spring force (the classic snap-fit mating force
   W = P (mu + tan a) / (1 - mu tan a), here with the lead angle a changing as the round
   tube rolls over the lip).

3. DAMPING. A little viscous damping on each lip's deflection rate (zeta ~ 0.3) keeps the
   explicit force stable at a 1 ms physics step.

Calibrate it: the numbers below come from beam theory and a datasheet modulus. Measure the
real push-in and pull-out force once (a luggage scale on a loop of string around the tube),
then scale `E_mpa` in config/powder_doser.yaml until `retention_curve()` matches.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np


@dataclass
class ClipGeometry:
    """One C-clip's section, from assets/powder_doser/geometry.yaml (mm)."""
    seat_radius: float      # inner radius of the ring (12.74)
    wall: float             # arm thickness (2.0)
    width: float            # along the auger (12.0): the arms' beam width b
    lip_x: float            # lip's distance from the centre line (8.75)
    lip_z: float            # lip's height above the seat centre (10.4)
    root_deg: float = 155.0  # where the free arm starts, degrees from the top
    E_mpa: float = 3000.0   # Young's modulus of the clip's plastic
    yield_mpa: float = 50.0  # for the stress check (PLA ~50-60 MPa, PETG ~45-50)
    mu: float = 0.3         # tube-on-lip friction (PLA on PLA)
    zeta: float = 0.3       # damping ratio of each lip

    @property
    def lip_deg(self) -> float:
        return float(np.degrees(np.arctan2(self.lip_x, self.lip_z)))

    @property
    def rho(self) -> float:
        return self.seat_radius + self.wall / 2

    def stiffness(self) -> float:
        """Each arm's sideways stiffness at the lip, N/mm (Castigliano, see module doc)."""
        a0, a1 = np.radians(self.lip_deg), np.radians(self.root_deg)
        th = np.linspace(a0, a1, 2001)
        integral = np.trapezoid((np.cos(a0) - np.cos(th)) ** 2, th)
        I = self.width * self.wall ** 3 / 12.0
        return float(self.E_mpa * I / (self.rho ** 3 * integral))

    def root_stress(self, delta_mm: float) -> float:
        """Bending stress at the arm's root with the lip pushed out by delta, MPa."""
        F = self.stiffness() * delta_mm
        M = F * self.rho * (np.cos(np.radians(self.lip_deg)) - np.cos(np.radians(self.root_deg)))
        I = self.width * self.wall ** 3 / 12.0
        return float(M * (self.wall / 2) / I)


def lip_forces(g: ClipGeometry, r: float, u: float, v: float, du: float = 0.0, dv: float = 0.0,
               ds: float = 0.0, k: float | None = None):
    """Force on the tube (section plane, N) from both lips, with the tube's centre at (u, v) mm
    from the seat centre, moving at (du, dv) mm/s in the section and ds mm/s along its axis.
    Returns (fx, fz, f_axial, list of (contact point (x, z), force (fx, fz, f_axial)))."""
    k = g.stiffness() if k is None else k
    h = g.lip_z - v
    out = []
    if abs(h) >= r:
        return 0.0, 0.0, 0.0, out
    w = np.sqrt(r * r - h * h)
    m_eff = 0.004  # kg: rough moving mass of one arm, only to size the damping
    c = 2 * g.zeta * np.sqrt(k * 1000 * m_eff)  # N*s/m
    fx = fz = fa = 0.0
    for side in (+1.0, -1.0):
        delta = w + side * u - g.lip_x
        if delta <= 0:
            continue
        px = side * (g.lip_x + delta)  # deflected lip position (contact point), x
        n = np.array([px - u, h]) / r  # unit normal from the tube's centre to the contact
        nx = max(abs(n[0]), 0.15)
        # Lip spring + damping on the rate the lip is being pushed out.
        ddelta = side * du + (-(h / w) * (-dv) if w > 1e-6 else 0.0)
        f_spring = k * delta + c * ddelta / 1000.0
        N = max(f_spring, 0.0) / nx
        f = -N * n  # on the tube
        # Friction: oppose the tube's sliding at the contact (section tangent + axial).
        t_dir = np.array([-n[1], n[0]])
        v_t = np.array([du, dv]) @ t_dir
        v_s = np.array([v_t, ds])
        speed = np.linalg.norm(v_s)
        if speed > 1e-9:
            ff = -g.mu * N * np.tanh(speed / 2.0) * v_s / speed  # smooth near zero (2 mm/s)
            f = f + ff[0] * t_dir
            f_ax = ff[1]
        else:
            f_ax = 0.0
        fx += f[0]
        fz += f[1]
        fa += f_ax
        out.append(((px, g.lip_z), (f[0], f[1], f_ax)))
    return fx, fz, fa, out


def retention_curve(g: ClipGeometry, r: float, speed_mm_s: float = 5.0, n: int = 400):
    """Vertical force needed to push the tube in and to pull it out of one clip, against the
    tube's height above the seat (quasi-static, at `speed_mm_s`). Returns (v, push_in_N,
    pull_out_N): push_in > 0 means you must push down that hard; pull_out > 0 means you must
    pull up that hard."""
    v = np.linspace(-0.5, g.lip_z + r + 0.5, n)
    push = np.array([-lip_forces(g, r, 0.0, vi, dv=-speed_mm_s)[1] for vi in v])  # moving down
    pull = np.array([-lip_forces(g, r, 0.0, vi, dv=+speed_mm_s)[1] for vi in v])  # moving up
    return v, -push, pull


class ClipContact:
    """One clip acting on one auger (engine-agnostic). The clip frame: origin at the seat
    centre, x across the mouth, y along the auger, z up (out of the mouth).

    `wrench(T_clip, T_auger, v_auger, w_auger)` returns the force and torque (world frame, N and
    N*m about the auger body's origin) that the clip's lips put on the auger, plus a dict of
    diagnostics. The auger's tube must be the part passing through the clip (its axial
    coordinate inside `tube_span`), otherwise the lips do nothing: the gear or the cap then
    meet the clip's arms as ordinary rigid contacts in the engine."""

    def __init__(self, geom: ClipGeometry, tube_radius_mm: float, tube_spans_mm, half_width_mm: float):
        self.g = geom
        self.r = tube_radius_mm
        self.spans = [tuple(s) for s in tube_spans_mm]  # plain-tube stretches along the auger
        self.hw = half_width_mm
        self.k = geom.stiffness()
        self.last = {}

    SLICES = (-1 / 3, 0.0, 1 / 3)  # across the clip's width: a tilted tube loads one edge first

    def wrench(self, T_clip: np.ndarray, T_auger: np.ndarray, v_auger: np.ndarray, w_auger: np.ndarray):
        """v_auger: world velocity of the auger's origin (m/s); w_auger: angular velocity (rad/s).
        The clip is split into three slices across its width, each with a third of the arms'
        stiffness, so a tube tilted in the clip spreads the lips at one edge before the other
        (levering it out by tilting takes far less force than pulling it straight out)."""
        Rc, pc = T_clip[:3, :3], T_clip[:3, 3]
        Ra, pa = T_auger[:3, :3], T_auger[:3, 3]
        a = Ra[:, 2]  # auger axis (world)
        y = Rc[:, 1]  # clip axis (world)
        denom = a @ y
        if abs(denom) < 0.5:  # auger far from parallel to the clip: lips can't act
            self.last = {"engaged": False}
            return np.zeros(3), np.zeros(3), self.last
        F, tau = np.zeros(3), np.zeros(3)
        info = {"engaged": False}
        k_slice = self.k / len(self.SLICES)
        for frac in self.SLICES:
            yk = frac * self.hw * 2 / 1000 * 0.9  # m, slice position across the clip's width
            p_plane = pc + y * yk
            s = ((p_plane - pa) @ y) / denom  # where the auger's axis crosses this slice
            s_mm = s * 1000
            if not any(lo <= s_mm <= hi for lo, hi in self.spans):
                continue
            p_axis = pa + a * s
            d = Rc.T @ (p_axis - pc)
            u, vv = d[0] * 1000, d[2] * 1000
            if abs(u) > 20 or vv > self.g.lip_z + self.r + 1 or vv < -5:
                continue
            vel = v_auger + np.cross(w_auger, p_axis - pa)
            vc = Rc.T @ vel * 1000
            ds = vel @ a * 1000
            fx, fz, fa, contacts = lip_forces(self.g, self.r, u, vv, vc[0], vc[2], ds, k=k_slice)
            F += Rc @ np.array([fx, 0.0, fz]) + a * fa
            for (px, pz), (cx, cz, ca) in contacts:
                pw = pc + Rc @ np.array([px / 1000, d[1], pz / 1000])
                fw = Rc @ np.array([cx, 0.0, cz]) + a * ca
                tau += np.cross(pw - pa, fw)
            if frac == 0.0 or not info["engaged"]:
                info = {"engaged": True, "s_mm": s_mm, "u_mm": u, "v_mm": vv,
                        "n_contacts": info.get("n_contacts", 0) + len(contacts)}
            else:
                info["n_contacts"] += len(contacts)
        if info["engaged"]:
            fz_c = (Rc.T @ F)[2]
            info.update(fz_n=fz_c, seated=abs(info["u_mm"]) < 1.0 and abs(info["v_mm"]) < 1.0)
        self.last = info
        return F, tau, info


class SnapFitField:
    """Applies every clip's snap force to every auger, each physics step (engine-agnostic).

    Engines that support force fields call `bind(engine)` once and `apply(engine)` before every
    step; they must provide site_pose(name), body_pose(name), body_velocity(name) -> (v, w) in
    the world frame, and apply_wrench(name, force, torque_about_body_origin). The kinematic
    engine has no forces, so it ignores fields (augers there are moved by attach/detach).

    `state[clip][auger]` keeps the latest diagnostics, and `events` logs every snap in and out
    (the moment the tube passes the lips), with the peak force it took."""

    def __init__(self, clips, augers: dict, geom: ClipGeometry, tube_radius_mm: float, tube_spans_mm,
                 half_width_mm: float):
        self.clips = clips            # [ClipSpec]: name, body, seat frame in that body
        self.augers = augers          # {auger body name: Auger}
        self.contacts = {(c.name, a): ClipContact(geom, tube_radius_mm, tube_spans_mm, half_width_mm)
                         for c in clips for a in augers}
        self.state: dict = {}
        self.events: list[dict] = []
        self._peak: dict = {}
        self._was_in: dict = {}
        self.enabled = True

    def bind(self, engine):
        self._seat_sites = {c.name: f"{c.name}_seat" for c in self.clips}

    def seated(self, engine, auger: str, clip_names=None, tol_mm: float = 0.6) -> bool:
        """True when the auger's tube centre is within tol of every given clip's seat."""
        names = clip_names or [c.name for c in self.clips]
        T_a = engine.body_pose(auger)
        for n in names:
            T_c = engine.site_pose(f"{n}_seat")
            a, y = T_a[:3, 2], T_c[:3, 1]
            denom = a @ y
            if abs(denom) < 0.5:
                return False
            s = ((T_c[:3, 3] - T_a[:3, 3]) @ y) / denom
            d = T_c[:3, :3].T @ (T_a[:3, 3] + a * s - T_c[:3, 3])
            if np.hypot(d[0], d[2]) * 1000 > tol_mm:
                return False
        return True

    def apply(self, engine):
        if not self.enabled:
            return
        poses = {a: engine.body_pose(a) for a in self.augers}
        vels = {a: engine.body_velocity(a) for a in self.augers}
        total = {a: [np.zeros(3), np.zeros(3)] for a in self.augers}
        for c in self.clips:
            T_c = engine.site_pose(self._seat_sites[c.name])
            for a, T_a in poses.items():
                if np.linalg.norm(T_a[:3, 3] - T_c[:3, 3]) > 0.32:  # auger nowhere near this clip
                    continue
                key = (c.name, a)
                F, tau, info = self.contacts[key].wrench(T_c, T_a, *vels[a])
                self.state.setdefault(c.name, {})[a] = info
                total[a][0] += F
                total[a][1] += tau
                # Snap events: the tube passing the lips' height (v = lip_z), either way.
                if info.get("engaged"):
                    inside = info["v_mm"] < self.contacts[key].g.lip_z
                    if info.get("n_contacts"):
                        self._peak[key] = max(self._peak.get(key, 0.0), abs(info["fz_n"]))
                    was = self._was_in.get(key)
                    if was is not None and was != inside and abs(info["u_mm"]) < 6:
                        self.events.append({"t": engine.time, "clip": c.name, "auger": a,
                                            "event": "snapped in" if inside else "snapped out",
                                            "peak_force_n": round(self._peak.get(key, 0.0), 2)})
                        self._peak[key] = 0.0
                    self._was_in[key] = inside
                else:
                    self._was_in.pop(key, None)
        for a, (F, tau) in total.items():
            engine.apply_wrench(a, F, tau)
