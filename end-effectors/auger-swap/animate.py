"""GIFs of the auger swap (remove, strip the tap collar, dispose, fetch, re-thread, re-seat)
for the four strategies in issue #42.

    xvfb-run -a python animate.py s1 s2 alt_a alt_b      # -> renders/<strategy>.gif
    xvfb-run -a python animate.py s1 --still 40          # one frame, for checking

The PiPER is posed by numerical IK on the AgileX URDF every frame (tool pointing down);
frames whose IK misses by more than 0.5 mm are reported.  Layout (mm, doser frame): PiPER
base at (220, 400) facing -Y, finger fixture at x = 150, auger rack at x = 240..360, bin at
x = -185..-65.  These are assumptions for the study, not measured lab positions.
"""
from __future__ import annotations

import argparse
import math
import sys
from pathlib import Path

import cadquery as cq
import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import agilex as AGX  # noqa: E402
import geometry as G  # noqa: E402
import hifi as H  # noqa: E402
import scene as S  # noqa: E402

FPS = 10
import os
SIDE_OFFSET = np.array([400.0, -120.0, 235.0])    # at the doser: from +X, so the hook isn't behind the collar
FRONT_OFFSET = np.array([230.0, -430.0, 420.0])   # elsewhere: high front view
OUT = HERE / "renders"
ARM_BASE = S.T((220.0, 400.0, 0.0)) @ S.T(R=S.rot((0, 0, 1), -90))
L = S.doser_layout()
PLACE = L.placements()

TITLES = {
    "s1": "Strategy 1: custom tool, two servos (lift + hook)",
    "s2": "Strategy 2: custom tool, one servo (wheel: crank + cam)",
    "alt_a": "Alternative A: stock fingers + two-shell sleeves, tilt-lock pin",
    "alt_a_cf": "Alternative A: custom fingers on the PiPER gripper, tilt-lock pin",
    "alt_b": "Alternative B: stock gripper + sleeves, doser servos hold",
}
HIFI = {"s1", "alt_a", "alt_a_cf", "alt_b"}
HIFI_TITLES = {TITLES[k] for k in HIFI}
# stock gripper: tube axis from the J6 face, and the gripper opening (its pad-to-pad command)
# that closes the cradles on a Ø25 tube / opens them clear of it
AXIS_BASE_Z = {"alt_a": H.sleeve_axis_base_z(), "alt_b": H.sleeve_axis_base_z(), "alt_a_cf": H.custom_axis_base_z()}
GRIP_CLOSED = {"alt_a": H.sleeve_opening(), "alt_b": H.sleeve_opening(), "alt_a_cf": H.custom_opening()}
GRIP_OPEN = {"alt_a": 70.0, "alt_b": 70.0, "alt_a_cf": 60.0}
# the sleeves hold the tube 135 mm from the J6 face, so the arm runs out of height sooner:
# scale the clearance moves for them (the collar still clears the fixture's forks)
HEADROOM = {"alt_a": 0.65, "alt_b": 0.65}
COL = {
    "doser": (0.72, 0.74, 0.77), "plate": (0.62, 0.64, 0.68), "board": (0.86, 0.80, 0.70),
    "base": (0.93, 0.70, 0.20), "auger": (0.80, 0.80, 0.82), "new": (0.70, 0.86, 0.98),
    "collar": (0.95, 0.95, 0.95), "solenoid": (0.80, 0.50, 0.15), "clip": (0.98, 0.98, 0.98),
    "fixture": (0.40, 0.62, 0.86), "rack": (0.55, 0.45, 0.35), "bin": (0.45, 0.45, 0.48),
    "arm": (0.90, 0.90, 0.92), "frame": (0.85, 0.22, 0.20), "jaw": (0.10, 0.62, 0.35),
    "servo": (0.15, 0.30, 0.75), "metal": (0.55, 0.57, 0.60), "wheel": (0.95, 0.60, 0.10),
    "sleeve": (0.10, 0.62, 0.35), "pin": (0.85, 0.22, 0.20), "wire": (0.85, 0.10, 0.10),
    "hold": (1.00, 0.35, 0.10), "gripper": (0.20, 0.20, 0.22), "finger": (0.11, 0.11, 0.12),
    "blue": (0.20, 0.45, 0.95), "green": (0.20, 0.70, 0.30), "cfinger": (0.95, 0.55, 0.10), "screw": (0.85, 0.75, 0.30),
}


def ease(u: float) -> float:
    return 0.5 - 0.5 * math.cos(math.pi * min(max(u, 0.0), 1.0))


# ----------------------------------------------------------------------------- S2 wheel timing
def wheel_state(psi: float):
    """Carriage travel s (0 up .. STROKE down) and hook opening (deg) for wheel angle psi."""
    phi = math.radians(psi - 180.0)            # crank angle from bottom dead centre
    r, l = G.CRANK_R, G.ROD_L
    y = r * math.cos(phi) + math.sqrt(l * l - (r * math.sin(phi)) ** 2)
    s = y - (l - r)
    p = (psi % 360.0)
    if p < 160:
        th = G.HOOK_OPEN_DEG
    elif p < 200:
        th = G.HOOK_OPEN_DEG * (1 - ease((p - 160) / 40))
    else:
        th = 0.0
    if psi >= 360.0:
        th = 0.0
    return s, th


# ----------------------------------------------------------------------------- sequence builder
class Seq:
    """Keyframed state; every step appends interpolated frames."""

    def __init__(self, kind: str):
        self.kind = kind
        self.custom = kind in ("s1", "s2")
        self.frames = []
        rack_mid = S.T((G.RACK_X[1], G.RACK_OUTLET_Y - G.OUTLET_Y, G.RACK_AXIS_Z - G.AXIS_Z))
        self.st = dict(
            pos=np.array([0.0, G.GRIP_Y if self.custom else G.STOCK_GRIP_Y, 0.0]),
            s=0.0, th=G.HOOK_OPEN_DEG, psi=0.0, grip=GRIP_OPEN.get(kind, 0.0),
            old=np.eye(4), new=rack_mid, held=None, rel=None, collar="old",
            pin=G.PIN_X_OUT, hold=False, cap="", drop=None)
        self.st["pos"][2] = self.tool_z_for_axis(G.AXIS_Z + 90 * HEADROOM.get(kind, 1.0))

    # tool frame helpers --------------------------------------------------------------------
    def tool(self, st) -> np.ndarray:
        """E (custom) or gripper_base frame (stock) in the world."""
        if self.custom:
            return S.T(st["pos"])
        return S.T(st["pos"], S.R_TOOL_G)

    def holder(self, st) -> np.ndarray:
        """Frame that carries a held auger: hook centre (custom) or the sleeves' bore."""
        if self.custom:
            return self.tool(st) @ S.T((0, 0, G.HOOK_Z + G.STROKE - st["s"]))
        return self.tool(st) @ S.T((0, 0, AXIS_BASE_Z[self.kind]))

    def tool_z_for_axis(self, axis_z: float, s: float | None = None) -> float:
        """Tool origin height that puts the hook centre / sleeve bore at axis_z."""
        if self.custom:
            s = self.st["s"] if s is None else s
            return axis_z - (G.HOOK_Z + G.STROKE - s)
        return axis_z + AXIS_BASE_Z[self.kind]

    # steps ---------------------------------------------------------------------------------
    def _emit(self, st):
        st = dict(st)
        if st["held"]:
            st[st["held"]] = self.holder(st) @ st["rel"]
        self.frames.append(st)

    def step(self, cap: str, n: int, **target):
        """Interpolate scalar keys / pos to the targets over n frames."""
        a = dict(self.st)
        for i in range(1, n + 1):
            u = ease(i / n)
            st = dict(self.st)
            for k, v in target.items():
                if k == "pos":
                    st["pos"] = (1 - u) * np.asarray(a["pos"]) + u * np.asarray(v)
                else:
                    st[k] = (1 - u) * a[k] + u * v
            if self.kind == "s2":
                st["s"], st["th"] = wheel_state(st["psi"])
            st["cap"] = cap
            self._emit(st)
        self.st.update(target)
        if self.kind == "s2":
            self.st["s"], self.st["th"] = wheel_state(self.st["psi"])
        self.st["cap"] = cap
        if self.st["held"]:
            self.st[self.st["held"]] = self.holder(self.st) @ self.st["rel"]

    def path(self, cap: str, pts, n_per: int = 8):
        for p in pts:
            self.step(cap, n_per, pos=np.array(p, float))

    def hold(self, cap: str, n: int):
        self.step(cap, n)

    def grasp(self, which: str):
        self.st["held"] = which
        self.st["rel"] = np.linalg.inv(self.holder(self.st)) @ self.st[which]

    def release(self):
        self.st["held"] = None
        self.st["rel"] = None

    def drop(self, cap: str, which: str, z_axis: float, n: int = 8):
        a = self.st[which].copy()
        dz = z_axis - (a[2, 3] + G.AXIS_Z)
        for i in range(1, n + 1):
            u = (i / n) ** 2
            st = dict(self.st)
            st[which] = S.T((0, 0, dz * u)) @ a
            st["cap"] = cap
            self._emit(st)
        self.st[which] = S.T((0, 0, dz)) @ a


# ----------------------------------------------------------------------------- the four sequences
FIX = S.T((G.FIX_X, 0.0, G.FIX_AXIS_Z - G.AXIS_Z))       # auger pose (Δ) lying in the fixture


def build(kind: str) -> Seq:
    q = Seq(kind)
    st = q.st
    custom = q.custom
    gy = G.GRIP_Y if custom else G.STOCK_GRIP_Y
    fy = gy                                                  # same y in the fixture
    strip = 80.0
    rack_gy = G.RACK_OUTLET_Y + (gy - G.OUTLET_Y)
    z_seat = q.tool_z_for_axis(G.AXIS_Z, s=G.STROKE) if custom else q.tool_z_for_axis(G.AXIS_Z)
    hr = HEADROOM.get(kind, 1.0)
    up = 60.0 * hr
    GO, GC = GRIP_OPEN.get(kind, 0.0), GRIP_CLOSED.get(kind, 0.0)
    pin = kind in ("alt_a", "alt_a_cf")
    what = "fingers" if kind == "alt_a_cf" else "sleeves"

    if pin:
        # lock the plate first: grip the pin's Ø25 grab bar like a tube and slide it in over the floor edge
        kz = q.tool_z_for_axis(H.BAR_Z)
        kx = G.PIN_X_OUT + H.HANDLE_X
        q.step("Open over the tilt-lock pin's grab bar (same Ø25 as the tube)", 12, pos=np.array([kx, G.PIN_Y, kz + 40]))
        q.step("Lower round the grab bar", 10, pos=np.array([kx, G.PIN_Y, kz]))
        q.step(f"Close: the {what}' cradles wrap the bar", 6, grip=GC)
        q.step("Slide the pin in over the mounting-plate floor: plate can't tip up", 12,
               pos=np.array([kx - (G.PIN_X_OUT - G.PIN_X_IN), G.PIN_Y, kz]), pin=G.PIN_X_IN)
        q.step("Open and lift off the bar (ball detent holds the pin)", 6, grip=GO)
        q.step("Open and lift off the bar (ball detent holds the pin)", 8,
               pos=np.array([kx - (G.PIN_X_OUT - G.PIN_X_IN), G.PIN_Y, kz + 40]))

    # ---- remove
    if custom:
        q.step("Tool comes down over the auger, carriage up, hook open", 12,
               pos=np.array([0.0, gy, z_seat - G.STROKE + up]))
        q.step("Legs land: one on the NEMA 11 plate, one on the floor", 12,
               pos=np.array([0.0, gy, z_seat - G.STROKE]))
        if kind == "s1":
            q.step("Servo 1 lowers the carriage; thin finger drops beside the stepper", 12, s=G.STROKE)
            q.step("Servo 2 swings the hook under the tube", 8, th=0.0)
            q.grasp("old")
            q.step("Servo 1 lifts 28 mm: clips spring open, force stays in the tool", 16, s=0.0)
        else:
            q.step("Wheel 0-180°: crank lowers the carriage, cam keeps the hook open", 14, psi=180.0)
            q.step("Wheel near 180°: cam closes the hook (crank dwells at the bottom)", 8, psi=210.0)
            q.grasp("old")
            q.step("Wheel 210-360°: crank lifts 28 mm, clips spring open", 16, psi=360.0)
    else:
        q.step("Open gripper over the free tube behind the rear clip", 12,
               pos=np.array([0.0, gy, z_seat + up]), grip=GO)
        q.step(f"Lower until the {what} straddle the tube", 10, pos=np.array([0.0, gy, z_seat]))
        q.step(f"Close: the {what}' cradles wrap 180° of the tube each", 8, grip=GC)
        q.grasp("old")
        hold_txt = ("the pin stops the plate tipping" if pin
                    else "doser tilt servos hold the plate")
        st["hold"] = kind == "alt_b"
        q.step(f"Arm pulls 28 mm against the clips; {hold_txt}", 16, pos=np.array([0.0, gy, z_seat + 28]))
        st["hold"] = False

    # ---- to the finger fixture
    lift_z = st["pos"][2] + 62 * hr
    q.path("Short move (collar wires): carry to the finger fixture", [
        (0.0, gy, lift_z), (G.FIX_X, fy, lift_z)], 10)
    z_fix = q.tool_z_for_axis(G.FIX_AXIS_Z)
    q.step("Drop the tube into the fork; collar sits in the cradle", 12, pos=np.array([G.FIX_X, fy, z_fix]))
    q.step("Pull along the axis: the fork strips the tap collar", 16, pos=np.array([G.FIX_X, fy + strip, z_fix]))
    st["collar"] = "fix"
    q.frames[-1]["collar"] = "fix"

    # ---- dispose
    binx = sum(G.BIN_X) / 2
    biny = sum(G.BIN_Y) / 2 + (gy - G.OUTLET_Y) - G.AUGER_LEN / 2   # auger centred over the bin
    bin_z = q.tool_z_for_axis(G.BIN_Z + (45 if custom else 15))
    q.path("Carry the old auger to the bin", [(G.FIX_X, fy + strip, z_fix + (50 if custom else 30)), (binx, biny, bin_z)], 12)
    if custom and kind == "s2":
        q.step("Wheel 360-180°: carriage lowers, cam opens the hook at the bottom", 14, psi=180.0)
        q.release()
        q.drop("Old auger drops into the bin", "old", 3 + 23)
        q.step("Wheel 180-0°: carriage back up (hook open)", 10, psi=0.0)
    elif custom:
        q.step("Servo 2 opens the hook", 6, th=G.HOOK_OPEN_DEG)
        q.release()
        q.drop("Old auger drops into the bin", "old", 3 + 23)
    else:
        q.step("Open the gripper", 6, grip=GO)
        q.release()
        q.drop("Old auger drops into the bin", "old", 3 + 23)

    # ---- fetch a new auger
    rx = G.RACK_X[1]
    if custom:
        z_rack_down = q.tool_z_for_axis(G.RACK_AXIS_Z, s=G.STROKE)
        if kind == "s1":
            q.path("Fetch a fresh auger from the rack", [(binx, biny, z_rack_down + 35), (rx, rack_gy, z_rack_down + 35)], 12)
            q.step("Carriage down, hook open, over the new tube", 8, s=G.STROKE)
            q.step("Lower onto the new tube", 10, pos=np.array([rx, rack_gy, z_rack_down]))
            q.step("Servo 2 closes the hook", 8, th=0.0)
            q.grasp("new")
            q.step("Servo 1 lifts the tube 28 mm", 10, s=0.0)
        else:
            q.path("Fetch a fresh auger from the rack", [(binx, biny, z_rack_down + 35), (rx, rack_gy, z_rack_down + 35)], 12)
            q.step("Lower over the new tube (carriage up, hook open)", 10,
                   pos=np.array([rx, rack_gy, z_rack_down]))
            q.step("Wheel 0-210°: carriage down, hook closes", 14, psi=210.0)
            q.grasp("new")
            q.step("Wheel 210-360°: lift 28 mm", 12, psi=360.0)
    else:
        z_rack = q.tool_z_for_axis(G.RACK_AXIS_Z)
        q.path("Fetch a fresh auger from the rack", [(binx, biny, z_rack + 25), (rx, rack_gy, z_rack + 25)], 12)
        q.step("Lower around the new tube", 10, pos=np.array([rx, rack_gy, z_rack]))
        q.step(f"Close the {what}", 8, grip=GC)
        q.grasp("new")
    z_now = st["pos"][2]
    q.step("Lift clear of the rack", 8, pos=np.array([rx, rack_gy, z_now + (40 if custom else 25)]))

    # ---- re-thread through the collar held in the fixture
    z_fix = q.tool_z_for_axis(G.FIX_AXIS_Z)
    hop = 45 if custom else 22
    q.path("Line up on the fixture axis, outlet end first", [
        (G.FIX_X, fy + strip + 5, z_fix + hop), (G.FIX_X, fy + strip + 5, z_fix)], 10)
    q.step("Push the new auger through the fork and the collar", 18, pos=np.array([G.FIX_X, fy, z_fix]))
    st["collar"] = "new"
    q.frames[-1]["collar"] = "new"
    q.step("Lift straight up: the collar comes along", 12, pos=np.array([G.FIX_X, fy, z_fix + 60 * hr]))

    # ---- re-seat
    if custom:
        z_hover = q.tool_z_for_axis(G.AXIS_Z + G.STROKE)          # carriage up: tube 28 mm over its seat
        q.path("Carry back over the doser", [(0.0, gy, z_hover + 50), (0.0, gy, z_hover)], 12)
        if kind == "s1":
            q.step("Servo 1 pushes the tube down the funnels; clips snap shut", 16, s=G.STROKE)
            q.release()
            q.step("Servo 2 opens the hook", 6, th=G.HOOK_OPEN_DEG)
            q.step("Servo 1 raises the carriage", 8, s=0.0)
        else:
            q.step("Wheel 360-180°: carriage pushes the tube in; cam opens at the bottom", 18, psi=180.0)
            q.release()
            q.step("Wheel 180-0°: carriage up", 10, psi=0.0)
        q.step("Done: arm lifts away", 10, pos=np.array([0.0, gy, z_hover + 60]))
    else:
        z_hover = q.tool_z_for_axis(G.AXIS_Z + 28)
        q.path("Carry back over the doser", [(0.0, gy, z_hover + 50 * hr), (0.0, gy, z_hover)], 12)
        st["hold"] = kind == "alt_b"
        q.step("Arm pushes the tube down the funnels; clips snap shut", 16, pos=np.array([0.0, gy, z_seat]))
        st["hold"] = False
        q.step("Open the gripper", 6, grip=GO)
        q.release()
        q.step("Lift away", 10, pos=np.array([0.0, gy, z_seat + 60 * hr]))
        if pin:
            kz = q.tool_z_for_axis(H.BAR_Z)
            kx = G.PIN_X_IN + H.HANDLE_X
            q.step("Back to the pin: over the grab bar", 12, pos=np.array([kx, G.PIN_Y, kz + 40]))
            q.step("Back to the pin: over the grab bar", 8, pos=np.array([kx, G.PIN_Y, kz]))
            q.step("Back to the pin: grip the grab bar", 6, grip=GC)
            q.step("Slide the pin out: plate free to tilt for dosing again", 12,
                   pos=np.array([kx + (G.PIN_X_OUT - G.PIN_X_IN), G.PIN_Y, kz]), pin=G.PIN_X_OUT)
            q.step("Done", 8, grip=GO)
            q.step("Done", 8, pos=np.array([kx + (G.PIN_X_OUT - G.PIN_X_IN), G.PIN_Y, kz + 50]))
    q.hold(q.st["cap"], 6)
    return q


# ----------------------------------------------------------------------------- rendering
def clip_angle(delta: np.ndarray) -> float:
    """Opening of each clip arm (deg) for an auger displaced by delta from its seat."""
    dx, dy, dz = delta[0, 3], delta[1, 3], delta[2, 3]
    if abs(dx) > 2 or abs(dy) > 2:
        return 0.0
    r = G.TUBE_R
    d = G.LIP_Z - dz
    if abs(d) >= r or dz < -0.5:
        return 0.0
    need = math.sqrt(r * r - d * d) - G.CLIP_MOUTH / 2
    if need <= 0:
        return 0.0
    lever = G.LIP_Z + G.CLIP_RI + G.CLIP_T
    return math.degrees(math.atan2(need, lever))


class Renderer:
    def __init__(self, kind: str, w: int = 800, h: int = 520):
        import pyvista as pv
        self.pv = pv
        self.kind = kind
        self.custom = kind in ("s1", "s2")
        self.p = pv.Plotter(off_screen=True, window_size=(w, h))
        self.p.set_background("white")
        self.p.enable_anti_aliasing("fxaa")
        self.actors = {}
        self.arm = S.Piper(ARM_BASE)
        self.q = np.radians([0, 90, -80, 0, 60, 0])
        self.focus = None
        self._static()
        self._dynamic()
        self.p.camera_position = [(760, -520, 560), (70, 210, 70), (0, 0, 1)]
        self.p.camera.view_angle = 30

    def add(self, key, mesh, color, M=None, **kw):
        a = self.p.add_mesh(self.pv.wrap(mesh), color=color, smooth_shading=False, **kw)
        if M is not None:
            a.user_matrix = M
        self.actors[key] = a
        return a

    def _static(self):
        self.add("board", S.part_mesh("board"), COL["board"])
        for name in S.DOSER_STATIC:
            rel, M = PLACE[name]
            col = COL["plate"] if name == "Mounting plate" else (COL["base"] if name == "Baseplate" else COL["doser"])
            if "MG996R" in name:
                col = COL["servo"]
            self.add(name, S.step_mesh(rel), col, M)
        for i, y in enumerate(G.CLIP_ROWS_Y):
            self.add(f"clipbase{i}", S.part_mesh("clip_base"), COL["clip"], S.T((0, y, G.AXIS_Z)))
        self.add("fixture", S.hifi_mesh("fixture", H.finger_fixture_hifi), COL["fixture"])
        self.add("rack", S.part_mesh("auger_rack"), COL["rack"])
        self.add("bin", S.part_mesh("disposal_bin"), COL["bin"], opacity=0.35)
        if self.kind in ("alt_a", "alt_a_cf"):
            self.add("pin_housing", S.hifi_mesh("pin_housing", H.pin_housing_hifi), COL["pin"])

    def _dynamic(self):
        for i in range(2):
            self.add(f"clip{i}+", S.part_mesh("clip_half_pos"), COL["clip"])
            self.add(f"clip{i}-", S.part_mesh("clip_half_neg"), COL["clip"])
        aug, cap = S.step_mesh(PLACE["Auger"][0], max_faces=40000), S.step_mesh(PLACE["Auger cap"][0])
        self.add("old_auger", aug, COL["auger"])
        self.add("old_cap", cap, COL["auger"])
        for j, x in enumerate(G.RACK_X):
            self.add(f"new_auger{j}", aug, COL["new"])
            self.add(f"new_cap{j}", cap, COL["new"])
        self.add("collar", S.step_mesh(PLACE["Tap collar"][0]), COL["collar"])
        self.add("solenoid", S.step_mesh(PLACE["Solenoid (Adafruit 412)"][0]), COL["solenoid"])
        meshes = self.arm.meshes()
        for n in S.Piper.LINKS[:7]:
            self.add("arm_" + n, meshes[n], COL["arm"])
        if self.custom:
            self.add("adapter", S.part_mesh("flange_adapter"), COL["metal"])
            self.add("frame", S.part_mesh("frame_s1" if self.kind == "s1" else "frame_s2"), COL["frame"], opacity=0.5)
            self.add("carriage", S.part_mesh("carriage"), (0.05, 0.40, 0.22))
            self.add("hook", S.part_mesh("hook"), COL["jaw"])
            if self.kind == "s1":
                self.add("servo_lift", S.part_mesh("servo_mg996r"), COL["servo"])
                self.add("pinion", S.part_mesh("pinion"), COL["metal"])
                self.add("rackbar", S.part_mesh("rack_bar"), COL["metal"])
                self.add("servo_hook", S.part_mesh("servo_micro"), COL["servo"])
            else:
                self.add("servo_wheel", S.part_mesh("servo_mg996r"), COL["servo"])
                self.add("drive_gear", S.part_mesh("drive_gear"), COL["metal"])
                self.add("driven_gear", S.part_mesh("driven_gear"), COL["metal"])
                self.add("wheel", S.part_mesh("wheel"), COL["wheel"])
                self.add("ear", S.part_mesh("carriage_ear"), COL["jaw"])
                self.add("crank_rod", S.part_mesh("rod"), COL["metal"])
                self.add("cam_rod", S.part_mesh("rod"), COL["wheel"])
        else:
            # AgileX's own gripper (STEP, fetched at run time) instead of the URDF's meshes
            for i in AGX.BODY:
                self.add(f"agx{i}", S.agilex_mesh(i), COL["gripper"])
            for nm, idx in (("carr_u", 5), ("carr_l", 9), ("sp_u", 8), ("sp_l", 12)):
                self.add(nm, S.agilex_mesh(idx), COL["metal"])
            if self.kind == "alt_a_cf":
                cf = S.hifi_mesh("custom_finger", H.custom_finger)
                hw = S.hifi_mesh("custom_finger_hw", lambda: cq.Workplane().add([h.val() for _, h in H.custom_finger_hardware()]))
                for sfx in ("u", "l"):
                    self.add("cf_" + sfx, cf, COL["cfinger"])
                    self.add("hw_" + sfx, hw, COL["screw"])
            else:
                for nm, idx in (("fin_u", 7), ("pad_u", 6), ("fin_l", 11), ("pad_l", 10)):
                    self.add(nm, S.agilex_mesh(idx), COL["finger"])
                blue = S.hifi_mesh("sleeve_main", H.sleeve_main_shell)
                green = S.hifi_mesh("sleeve_fix", H.sleeve_fixing_shell)
                hw = S.hifi_mesh("sleeve_hw", lambda: cq.Workplane().add([h.val() for _, h in H.sleeve_hardware()]))
                for sfx in ("u", "l"):
                    self.add("blue_" + sfx, blue, COL["blue"])
                    self.add("green_" + sfx, green, COL["green"])
                    self.add("hw_" + sfx, hw, COL["screw"])
        if self.kind in ("alt_a", "alt_a_cf"):
            self.add("pin_rod", S.hifi_mesh("pin_rod", H.pin_rod), COL["metal"])
            self.add("pin_handle", S.hifi_mesh("pin_handle", H.pin_handle), COL["pin"])

    # ------------------------------------------------------------------------------------
    def pose(self, st, seq: Seq):
        A = self.actors
        # augers + collar
        rack = {j: S.T((x, G.RACK_OUTLET_Y - G.OUTLET_Y, G.RACK_AXIS_Z - G.AXIS_Z)) for j, x in enumerate(G.RACK_X)}
        rack[1] = st["new"]
        A["old_auger"].user_matrix = st["old"] @ PLACE["Auger"][1]
        A["old_cap"].user_matrix = st["old"] @ PLACE["Auger cap"][1]
        for j, D in rack.items():
            A[f"new_auger{j}"].user_matrix = D @ PLACE["Auger"][1]
            A[f"new_cap{j}"].user_matrix = D @ PLACE["Auger cap"][1]
        Dc = {"old": st["old"], "fix": FIX, "new": st["new"]}[st["collar"]]
        A["collar"].user_matrix = Dc @ PLACE["Tap collar"][1]
        A["solenoid"].user_matrix = Dc @ PLACE["Solenoid (Adafruit 412)"][1]
        # clips
        ang = max(clip_angle(st["old"]), clip_angle(st["new"]))
        for i, y in enumerate(G.CLIP_ROWS_Y):
            C = S.T((0, y, G.AXIS_Z))
            piv = (0, 0, -(G.CLIP_RI + G.CLIP_T))
            A[f"clip{i}+"].user_matrix = C @ S.about((0, 1, 0), ang, piv)
            A[f"clip{i}-"].user_matrix = C @ S.about((0, 1, 0), -ang, piv)
        # tool + arm
        tool = seq.tool(st)
        flange = S.flange_for_E(tool) if self.custom else tool
        self.q, ep, er = self.arm.ik(flange, self.q)
        poses = self.arm.poses(self.q)
        for n in S.Piper.LINKS[:7]:
            A["arm_" + n].user_matrix = poses[n]
        Tf = poses["link6"]
        if self.custom:
            E = Tf @ np.linalg.inv(S.T(R=S.R_TOOL_E))
            Cg = E @ S.T((0, 0, G.HOOK_Z + G.STROKE - st["s"]))
            for k in ("adapter", "frame"):
                A[k].user_matrix = E
            A["carriage"].user_matrix = Cg
            px, pz = G.HOOK_PIVOT
            A["hook"].user_matrix = Cg @ S.about((0, 1, 0), -st["th"], (px, 0, pz))
            hz = G.HOOK_Z + G.STROKE              # hook centre (s = 0), E frame
            if self.kind == "s1":
                A["servo_lift"].user_matrix = E @ S.T((30, 0, -40)) @ S.T(R=S.rot((1, 0, 0), -90))
                A["pinion"].user_matrix = E @ S.T((9 + 3, 8, -40)) @ S.T(R=S.rot((1, 0, 0), -90)) @ S.T(R=S.rot((0, 0, 1), -st["s"] / 9.0 * 57.3))
                A["rackbar"].user_matrix = Cg @ S.T((0, 12, G.CARRIAGE_TOP - 2))
                A["servo_hook"].user_matrix = Cg @ S.T((px, -16, pz)) @ S.T(R=S.rot((1, 0, 0), -90))
            else:
                psi = st["psi"]
                W = E @ S.T((0, G.WHEEL_Y, G.WHEEL_Z))
                A["wheel"].user_matrix = W @ S.T(R=S.rot((0, 1, 0), -90 - psi))
                A["driven_gear"].user_matrix = W @ S.T((0, -5, 0)) @ S.T(R=S.rot((1, 0, 0), 90)) @ S.T(R=S.rot((0, 0, 1), psi))
                A["drive_gear"].user_matrix = W @ S.T((30, -5, 0)) @ S.T(R=S.rot((1, 0, 0), 90)) @ S.T(R=S.rot((0, 0, 1), -psi / 2))
                A["servo_wheel"].user_matrix = W @ S.T((30, 12, 0)) @ S.T(R=S.rot((1, 0, 0), 90))
                A["ear"].user_matrix = Cg
                # crank pin (wheel frame, +X at psi = 0 rotated) -> carriage pin
                phi = math.radians(-psi)
                pin_w = (W @ S.T(R=S.rot((0, 1, 0), -90 - psi)) @ np.array([G.CRANK_R, 2, 0, 1]))[:3]
                pin_c = (Cg @ np.array([0, G.WHEEL_Y + 4, G.CARRIAGE_TOP - 2.5, 1]))[:3]
                A["crank_rod"].user_matrix = self._link(pin_c, pin_w)
                cam_top = (W @ np.array([-G.WHEEL_R + 5, 2, -3 - 6 * (1 - st["th"] / G.HOOK_OPEN_DEG), 1]))[:3]
                lever = (Cg @ S.about((0, 1, 0), -st["th"], (px, 0, pz)) @ np.array([px - 2, G.WHEEL_Y + 6, pz + 6, 1]))[:3]
                A["cam_rod"].user_matrix = self._link(lever, cam_top, r=0.7)
        else:
            dz = AGX.finger_shift(st["grip"])             # opening = the gripper's pad-to-pad command
            B = Tf @ AGX.step_to_base()
            U, Lw = B @ S.T((0, 0, dz)), B @ AGX.lower_of() @ S.T((0, 0, dz))
            for i in AGX.BODY:
                A[f"agx{i}"].user_matrix = B
            for k in ("carr_u", "sp_u"):
                A[k].user_matrix = U
            for k in ("carr_l", "sp_l"):
                A[k].user_matrix = B @ S.T((0, 0, -dz))
            if self.kind == "alt_a_cf":
                A["cf_u"].user_matrix = A["hw_u"].user_matrix = U
                A["cf_l"].user_matrix = A["hw_l"].user_matrix = Lw
            else:
                for k in ("fin_u", "pad_u"):
                    A[k].user_matrix = U
                for k in ("fin_l", "pad_l"):
                    A[k].user_matrix = B @ S.T((0, 0, -dz))
                for k in ("blue", "green", "hw"):
                    A[k + "_u"].user_matrix = U
                    A[k + "_l"].user_matrix = Lw
        if self.kind in ("alt_a", "alt_a_cf"):
            A["pin_rod"].user_matrix = A["pin_handle"].user_matrix = S.T((st["pin"], G.PIN_Y, G.PIN_Z))

        hold = st.get("hold", False)
        for n in ("Servo MG996R (+X)", "Servo MG996R (-X)"):
            A[n].prop.color = COL["hold"] if hold else COL["servo"]
        # collar wire
        top = (Dc @ np.array([22, 88, 104, 1]))[:3]
        anchor = np.array([80.0, 120.0, 30.0])
        mid = (top + anchor) / 2 + np.array([10, 10, 25])
        tt = np.linspace(0, 1, 30)[:, None]
        pts = (1 - tt) ** 2 * top + 2 * (1 - tt) * tt * mid + tt ** 2 * anchor
        self.p.add_mesh(self.pv.Spline(pts, 40).tube(radius=1.2), color=COL["wire"], name="wire")
        return ep, er

    @staticmethod
    def _link(a, b, r=1.0):
        a, b = np.asarray(a, float), np.asarray(b, float)
        v = b - a
        n = np.linalg.norm(v)
        z = v / n
        x = np.cross([0, 0, 1], z) if abs(z[2]) < 0.99 else np.array([1.0, 0, 0])
        x /= np.linalg.norm(x)
        y = np.cross(z, x)
        M = np.eye(4)
        M[:3, 0], M[:3, 1], M[:3, 2] = x * r, y * r, z * n
        M[:3, 3] = a
        return M

    def shot(self, focus, overview=True):
        """Close-up that follows the tool (main) with the whole cell as an inset."""
        f = np.asarray(focus, float)
        if self.focus is None:
            self.focus = f
        self.focus = 0.75 * self.focus + 0.25 * f
        c = self.focus
        u = min(max((c[0] - 40.0) / 80.0, 0.0), 1.0)
        side = SIDE_OFFSET if self.kind != "s2" else np.array([300.0, -320.0, 250.0])
        off = (1 - u) * side + u * FRONT_OFFSET
        self.p.camera_position = [tuple(c + off), tuple(c), (0, 0, 1)]
        at_doser = c[0] < 60
        self.actors["fixture"].prop.opacity = 0.25 if at_doser else 1.0
        for k in ("rack", "new_auger0", "new_cap0", "new_auger2", "new_cap2"):
            self.actors[k].prop.opacity = 0.3 if at_doser else 1.0
        self.p.camera.view_angle = 30
        self.p.render()
        main = self.p.screenshot(return_img=True)
        if not overview:
            return main
        self.p.camera_position = [(950, -760, 980), (40, 250, 120), (0, 0, 1)]
        self.p.camera.view_angle = 30
        for k in ("fixture", "rack", "new_auger0", "new_cap0", "new_auger2", "new_cap2"):
            self.actors[k].prop.opacity = 1.0
        self.p.render()
        ov = self.p.screenshot(return_img=True)
        from PIL import Image
        im = Image.fromarray(main)
        small = Image.fromarray(ov).resize((246, 160))
        im.paste((150, 150, 150), (im.width - 252, 38, im.width - 2, 202))
        im.paste(small, (im.width - 250, 40))
        return np.asarray(im)


def focus_of(seq: Seq, st) -> np.ndarray:
    """Point the close-up follows: the held tube / jaws, nudged towards the doser."""
    h = seq.holder(st)[:3, 3]
    return np.array([h[0], h[1] - 10.0, h[2] + 5.0])


def caption(img, title, cap, k, n):
    from PIL import Image, ImageDraw, ImageFont
    im = Image.fromarray(img)
    d = ImageDraw.Draw(im)
    fb = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 19)
    f = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 17)
    fs = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 12)
    d.rectangle([0, 0, im.width, 34], fill=(245, 245, 245))
    d.text((12, 7), title, fill=(20, 20, 20), font=fb)
    d.rectangle([0, im.height - 36, im.width, im.height], fill=(30, 30, 30))
    d.text((12, im.height - 28), cap, fill=(255, 255, 255), font=f)
    d.text((12, 40), f"{'high' if title in HIFI_TITLES else 'medium'} fidelity · issue #42 · lab layout assumed",
           fill=(120, 120, 120), font=fs)
    w = int((im.width - 24) * k / max(n - 1, 1))
    d.rectangle([12, im.height - 40, 12 + w, im.height - 37], fill=(230, 120, 30))
    return im


def render(kind: str, still: str | None = None, scale: float = 0.8):
    seq = build(kind)
    r = Renderer(kind)
    if still is not None:
        for i in [int(v) for v in still.split(",")]:
            r.focus = None
            st = seq.frames[i]
            ep, er = r.pose(st, seq)
            im = caption(r.shot(focus_of(seq, st)), TITLES[kind], st["cap"], i, len(seq.frames))
            OUT.mkdir(exist_ok=True)
            im.save(OUT / f"{kind}_still_{i}.png")
            print("->", OUT / f"{kind}_still_{i}.png", f"IK miss {ep:.2f} mm")
        return
    frames = seq.frames
    imgs, worst = [], 0.0
    for k, st in enumerate(frames):
        ep, er = r.pose(st, seq)
        worst = max(worst, ep)
        if ep > 0.5:
            print(f"  frame {k}: IK misses by {ep:.1f} mm / {math.degrees(er):.1f}°  ({st['cap']})")
        img = r.shot(focus_of(seq, st))
        imgs.append(caption(img, TITLES[kind], st["cap"], k, len(seq.frames)))
    OUT.mkdir(exist_ok=True)
    every = 2                                   # keep GIFs a few MB: every 2nd frame, a bit faster
    pal = [im.convert("RGB").resize((int(im.width * scale), int(im.height * scale))).quantize(colors=64, method=2)
           for im in imgs[::every]]
    p = OUT / f"{kind}.gif"
    pal[0].save(p, save_all=True, append_images=pal[1:], duration=int(1000 / FPS * every * 0.7), loop=0, optimize=True)
    print(f"-> {p} ({len(imgs)} frames, worst IK miss {worst:.2f} mm, {p.stat().st_size / 1e6:.1f} MB)")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("kinds", nargs="+", choices=list(TITLES))
    ap.add_argument("--still", type=str, help="comma-separated frame indices to save as PNG")
    ap.add_argument("--scale", type=float, default=0.8)
    ap.add_argument("--list", action="store_true", help="print the frame index of every step")
    a = ap.parse_args()
    for k in a.kinds:
        if a.list:
            last = None
            for i, st in enumerate(build(k).frames):
                if st["cap"] != last:
                    print(k, i, st["cap"])
                    last = st["cap"]
            continue
        render(k, a.still, a.scale)
