#!/usr/bin/env python3
"""The lens cradle bored out to O43 the whole length of the lens (2026-10-29), against the cradle
the bracket was printed with, which narrowed to O33 for the lens's last 11 mm.

On the first fit (2026-10-28) the 6 mm lens's aperture thumbscrew caught that O33 strip: the screw
sits further forward than lenses.py has it (17.4 mm in front of the CS seat), and the O43 stopped
just past that, at 20.4 mm. This slides a thumbscrew's head (O3, its tip 20 mm from the axis, both
estimates from photos) along the lens and measures how much of it each bracket would cut, at any
angle round the lens, then draws both brackets from outside the cradle, with what was taken out in
blue and the two walls left round the tab screws in orange.

    xvfb-run -a -s "-screen 0 1920x1080x24" python cradle_bore.py   # -> ../renders/cradle_bore.png, ../exports/cradle_bore.json
"""
from __future__ import annotations

import json
from pathlib import Path

import cadquery as cq
import numpy as np
import pyvista as pv

import lenses
import piper_mount as pm
from render import mesh

HERE = Path(__file__).resolve().parent
EXPORTS = HERE.parent / "exports"
RENDERS = HERE.parent / "renders"
PLA, BLUE, ORANGE = (0.22, 0.22, 0.24), (0.1, 0.35, 1.0), pm.ORANGE


def old_keepout(lens: lenses.Lens, seat_z: float, c: float) -> cq.Workplane:
    """lenses.lens_keepout_local as printed on 2026-10-13: the screws' circle only out to just past
    the aperture screw, then the lens alone."""
    k = lenses._cyl(lens.od + 2 * c, seat_z - lens.front_s - c, seat_z)
    s_max = max(s for s, _ in lens.screws) + lens.screw_d / 2 + c
    return k.union(lenses._cyl(2 * (lens.screw_tip_r + c), seat_z - s_max, 0.0))


def old_bracket(p: pm.Params) -> cq.Workplane:
    keep = pm.lens_keepout_local
    pm.lens_keepout_local = old_keepout
    try:
        return pm.make_bracket(p)
    finally:
        pm.lens_keepout_local = keep


def screw_at(p: pm.Params, s: float) -> cq.Workplane:
    """The circle a thumbscrew's head sweeps, centred s mm in front of the CS seat."""
    lens, seat = p.lens_spec, -p.hq_cs_seat
    return pm.hq_place(p)(lenses._cyl(2 * lens.screw_tip_r, seat - s - lens.screw_d / 2, seat - s + lens.screw_d / 2))


def main() -> None:
    p = pm.Params()
    lens, seat = p.lens_spec, -p.hq_cs_seat
    old, new = old_bracket(p), pm.make_bracket(p)
    removed = old.cut(new)
    bore = pm.hq_place(p)(lenses.lens_keepout_local(lens, seat, 1.5))
    walls = new.intersect(bore)                 # what is left inside the O43: the walls round the tab screws
    anywhere = pm.hq_place(p)(lenses.screw_sweep_local(lens, seat, anywhere=True))
    y_pad = p.collar_y0 + 0.05
    slab = pm.box(-200, 200, p.collar_y0, y_pad, -200, 200)

    half = lens.screw_d / 2
    centres = [round(s, 1) for s in np.arange(half, lens.front_s - half + 1e-6, 0.5)]
    hits = {k: [round(pm.overlap(screw_at(p, s), b), 1) for s in centres] for k, b in (("old", old), ("new", new))}
    first_hit = next((s for s, v in zip(centres, hits["old"]) if v > 0.05), None)
    out = {
        "what": "The lens cradle as printed (O43 out to 20.4 mm in front of the CS seat, then O33 round the rest of the "
                "lens) against the cradle now (O43 to 1.5 mm past the lens's front, with tab_wall left round each tab "
                "screw's hole). A thumbscrew head (O3, tip 20 mm from the axis) is slid along the lens, at any angle "
                "round it; overlap in mm3 (piper_mount.overlap).",
        "bracket volume (cm3)": {"as printed": round(old.val().Volume() / 1000, 2), "now": round(new.val().Volume() / 1000, 2)},
        "taken out (mm3)": round(removed.val().Volume(), 1),
        "left inside the O43, round the tab screws (mm3)": round(walls.val().Volume(), 1),
        "tab_wall (mm)": p.tab_wall,
        "thumbscrew anywhere along the lens to the bracket (mm)": {
            "as printed": round(anywhere.val().distance(old.val()), 2), "now": round(anywhere.val().distance(new.val()), 2)},
        "thumbscrew anywhere along the lens, cut into the bracket (mm3)": {
            "as printed": round(pm.overlap(anywhere, old), 1), "now": round(pm.overlap(anywhere, new), 1)},
        "screw head centred this far in front of the CS seat first hits the bracket as printed (mm)": first_hit,
        "pad face on the gripper's tab (mm2)": {
            "as printed": round(old.intersect(slab).val().Volume() / 0.05), "now": round(new.intersect(slab).val().Volume() / 0.05)},
        "screw head centre (mm in front of the CS seat)": centres,
        "cut into the bracket by a screw head there, at any angle (mm3)": hits,
    }
    (EXPORTS / "cradle_bore.json").write_text(json.dumps(out, indent=2) + "\n")
    print(json.dumps({k: v for k, v in out.items() if not isinstance(v, (list, dict)) or "volume" in k or "to the" in k
                      or "cut into the bracket (mm3)" in k or "pad face" in k}, indent=1))

    o, d, _ = pm.optical_axes(p)["hq"]
    ctr = np.array(o.toTuple()) - np.array(d.toTuple()) * 6
    views = ((ctr, ctr + np.array([-190, -75, 55]), 1.15), (ctr + np.array([12, 0, 0]), ctr + np.array([47, -230, 25]), 1.0))
    rows = (("As printed: O43 to 20.4 mm out, then O33 to the lens's front\n(blue: the strip taken out now)", old, removed),
            ("Now: O43 the whole length of the lens\n(orange: the 1 mm walls left round the two tab screws;\n"
             "beside them the hex-key channels now open into the cradle)", new, walls))
    pl = pv.Plotter(off_screen=True, window_size=(1800, 1500), shape=(2, 2), border=False)
    pl.set_background("white")
    pl.enable_anti_aliasing("ssaa")
    for r, (title, body, mark) in enumerate(rows):
        for col, (aim, eye, zoom) in enumerate(views):
            pl.subplot(r, col)
            pl.add_mesh(mesh(body, 0.03), color=PLA, smooth_shading=False, specular=0.35)
            pl.add_mesh(mesh(mark, 0.03), color=BLUE if r == 0 else ORANGE, smooth_shading=False)
            pl.camera_position = [tuple(eye), tuple(aim), (0, 0, 1)]
            pl.camera.zoom(zoom)
            pl.add_text(title if col == 0 else "the same, from the fingertips' side", position="upper_left",
                        font_size=10, color="black")
    pl.screenshot(RENDERS / "cradle_bore.png")
    pl.close()
    print(f"wrote {RENDERS / 'cradle_bore.png'} and {EXPORTS / 'cradle_bore.json'}")


if __name__ == "__main__":
    main()
