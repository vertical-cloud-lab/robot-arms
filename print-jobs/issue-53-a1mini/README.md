# #53: PR #44's slider, finger fixture and stock-finger sleeves on one A1 mini plate

Asked for on [#53](https://github.com/vertical-cloud-lab/robot-arms/issues/53): once the Claude run on
[PR #44's comment](https://github.com/vertical-cloud-lab/robot-arms/pull/44#issuecomment-6506342698) (a lower
finger fixture, and a compliant latch on the slider) had finished, "load the build plate on Thumbelina
(A1 mini) with the slider parts, the finger fixture, and the two shell sleeves needed to equip the stock
gripper fingers", in black PLA, and wait for the requester's approval before sending.

![The plate, from its own G-code](plate.png)

## The plate

| | [`issue53_A1mini_PLA.3mf`](issue53_A1mini_PLA.3mf) |
|---|---|
| Parts | the **slider** (bar, latch beam and Ø25 knob) and its **guide**; the **finger fixture**; **2 × main shell** and **2 × fixing shell**, one of each per stock finger |
| Time (Bambu's estimate) | 3 h 16 min (the GUI says 3 h 13 min: Studio's stock acceleration limits) |
| PLA | 98.81 g (32.60 m): slider 12.5 g, guide 7.2 g, fixture 17.4 g, main shells 2 × 20.5 g, fixing shells 2 × 10.3 g |
| Layers | 242, to 48.4 mm (the main shells) |

- **Printer and material:** A1 mini, **0.4 mm nozzle** (read from the printer on 29 Oct), **black Bambu PLA
  Basic** (AMS slot A3), Textured PEI plate at 65 °C, nozzle 220 °C.
- **Settings:** Bambu's `0.20mm Standard @BBL A1M`, circle compensation on, supports off.
  - Slider, guide and fixture: 3 walls, 20 % infill. PR #44 says 15–20 % is plenty for the fixture.
    The slider's latch beam is 2 mm thick, so its walls make it solid.
  - Sleeve shells: 4 walls, 40 % infill (per-object settings), for the grip and pull-out loads and the
    heat-set inserts.
- **Checks:** no toolpath leaves the bed, Bambu's support check flags nothing, no supports. The auto brim
  adds none. The only G-code warning is Bambu's usual timelapse note.
- **The GUI kept the settings.** Opened in Studio 02.08.02.61's GUI, the project kept 3 walls, 20 % infill
  and circle compensation (preset marked modified), and the sleeves kept their 4 walls and 40 %. Its own
  slice had the same 98.81 g, 242 layers and 48.40 mm top, and the same start G-code (`M620 S0A`, `M190 S65`,
  `M109 S220`). Net extrusion is within 0.39 mm of filament on every layer. Only Studio's stock acceleration
  limits differ. [Prepare view](plate_studio_prepare.png), [sliced](plate_studio_preview.png).

## Orientations

| Part | On the bed | Why |
|---|---|---|
| Slider | its −Y face, as exported (PR #44 turned the STL) | bar, latch beam and post in the layer plane; the knob prints as an upright cup |
| Guide | base-down, as exported | the tunnel roof is an 8.5 mm bridge |
| Finger fixture | base-down, as exported | no overhangs |
| Main shell | **stood on its −X end** (`y270`), so the cradle's half-bore is upright | see below |
| Fixing shell | on its split face, as exported: the four leg feet and the bands' ends | see below |

PR #44's README says to print "the main shell on its outer web with the cradle up, the fixing shell on its
back". With these STLs that doesn't work:

- **Main shell.** Its cradle opens the same way as the web's outer face, and the cradle block stands
  13 mm proud of that face, so the web can't sit on the bed. As exported (cradle down) it rests on the tooth
  and jaw faces (197 mm²), and turned cradle-up (`x180`) on the lip over the fingertip (306 mm²); Bambu's
  support check flags a floating cantilever either way.
  The shell is a straight extrusion along the tube, so standing it on its end puts the whole profile in every
  layer: 505 mm² on the bed, almost no overhang, a round half-bore, and the grip and screw loads along the
  layers. Its M3 holes print horizontal.
- **Fixing shell.** Its two bands stand 15.2 mm (gripper end) and 9.7 mm (tip end) off the split face, following
  the finger's back, so on its back it rests on one band, and Bambu flags a floating cantilever. On its split face it stands on all four legs
  (664 mm²); the spine between the bands is a short bridge over the finger channel. The insert holes print
  vertical.

## Material

PR #44 designs the slider and guide in **PETG**; #53 asks for **PLA**. By PR #44's own beam formula,
PLA's higher modulus (about 2.75 GPa against 2.0) makes the latch take about **9 N** to push in instead of
about 6 N (5.8 N on the bump instead of 4.2 N). The beam's strain is the same 0.8 % (1.1 % if pressed to the
slot floor). PLA takes that, but it is stiffer and more brittle than PETG, so it has less margin.

## Source

`stl/` is byte for byte PR #44's `end-effectors/auger-swap/cad/stl/` at `b9caa43` on
`claude/issue-42-20261026-0528`: `pin_slider.stl`, `pin_guide.stl` and `finger_fixture.stl` are round 3's (the
low fixture and the latched slider); the two sleeve shells are unchanged since round 2 (sha256 `acbbfe227b11`
and `955610231b4a`). Hardware, from PR #44's README: 2 × M4 countersunk wood screws each for the fixture and the
guide; per sleeve, 2 × M3 × 10 and 2 × M3 × 12 countersunk (ISO 10642) and 4 × M3 × 5.7 heat-set inserts.

## Files

| File | What |
|---|---|
| [`slice_a1mini.py`](slice_a1mini.py) | Turns, places and slices the plate with the Bambu Studio 02.08.02.61 CLI (the #52 bracket's script, with quarter turns and per-object settings). Writes the 3MF and `report.json` |
| [`report.json`](report.json) | The CLI slice's numbers and checks |
| [`plate_view.py`](plate_view.py) | Draws `plate.png` from the plate's G-code (#52's, relabelled) and writes `per_object.json` |
| `glxshim.c` | PR #10's OpenGL shim, for headless thumbnails |
| `print-20261029/` | The print run: camera frames, Device-page screenshots, and later the sent file and `print.json` |

To regenerate, with Bambu Studio's AppImage extracted to `~/bambu/squashfs-root`:

```bash
cd print-jobs/issue-53-a1mini
python slice_a1mini.py --bambu ~/bambu/squashfs-root
xvfb-run -a python plate_view.py --no-gif
```
