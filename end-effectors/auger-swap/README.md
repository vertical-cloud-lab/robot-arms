# PiPER auger swap on the powder doser: four strategies, medium fidelity (issue #42)

The PiPER pulls a spent auger out of the powder doser, strips the tethered tap collar
off it in a finger fixture, drops it in a bin, takes a fresh auger from a rack, threads
it back through the collar and presses it into the doser. The auger is held by
**compliant snap clips with a funnel mouth, not the old screw-and-nut clamp**.

| | What holds the auger during the pull | Who supplies the pull-out force |
|---|---|---|
| **Strategy 1**: custom tool, two servos | hook + thin finger on a lift carriage | the tool: its legs push on the doser while the carriage lifts |
| **Strategy 2**: custom tool, one servo | same; a wheel's crank pin lifts and a face cam closes the hook | the tool, the same way |
| **Alternative A**: stock gripper + sleeves + tilt-lock pin | printed sleeves that wrap the tube | the arm; a pin on the board stops the mounting plate tipping |
| **Alternative B**: stock gripper + sleeves | the same sleeves | the arm; the doser's tilt servos hold the plate |

## Files

- `geometry.py`: CadQuery parts in the doser's own layout frame: funnel clip, finger
  fixture, rack, bin, both custom tools, sleeves, pin.
- `scene.py`: fetches the doser STEP files and `layout.py` from
  [powder-doser `7f5b3b7`](https://github.com/vertical-cloud-lab/powder-doser/tree/7f5b3b7/cad/full-assembly)
  and the PiPER URDF/meshes from
  [`agilexrobotics/piper_ros`](https://github.com/agilexrobotics/piper_ros/tree/ac41fcbcdda598f01b51cf6175ed9a24d0dacadc/src/piper_description).
  It has PiPER forward kinematics and IK from the URDF.
- `animate.py`: the four GIFs in `renders/`, with the PiPER posed by IK every frame and the
  tool pointing down. Every frame lands within 0.5 mm of its target pose.
  Run `xvfb-run -a python animate.py s1 s2 alt_a alt_b`.
- `clip_force.py`: a rough curved-beam estimate of the clips' snap force.
- `export_step.py`, `onshape_upload.py`, `cad/`, `onshape/`: STEP exports and the Onshape
  document (see `onshape/onshape_document.json`).

## Assumptions

- **Cell layout.** The PiPER base is at (220, 400) mm in the doser frame. The finger
  fixture is 150 mm to +X of the auger, the rack is at x = 240–360 and the bin is at
  x = −185…−65, all on the doser's board. None of this is measured; move it once the cell
  is laid out.
- **Doser.** It is PR 170's current-design assembly with the two bolted brackets replaced by
  clips: Ø25.1 bore, 17 mm mouth, 2 mm wall, 10 mm wide (Sam's multi-doser numbers), plus a
  35° funnel lip.
- **Grip windows.** Between the 44T gear and the rear clip, the NEMA 11 body is only
  **5.5 mm** from the tube on −X. The custom tools therefore use a 3 mm fixed finger on that
  side and a hook from the open +X side. Leg A lands on the stepper plate, leg B on the
  floor. The stock fingers are 56 mm wide, so they can't fit that 41 mm window. Alternatives
  A and B grip the free tube behind the rear clip instead (y ≈ 188–244).
- **Gear.** Lifting the auger rolls the 44T gear off the 20T pinion over the first ~12 mm,
  which turns the auger ~30°. Either disable the stepper driver during a swap so the pinion
  can turn, or rely on the hook/sleeves cradling the tube rather than clamping it.

## Answers

**Does the 1.5 kg rating include the stock gripper?** Yes. The manual says the arm has "a 1.5kg payload at the end"
and lists Effective Load 1.5 kg and Weight 4.2 kg. The two-finger gripper (500 g) is an optional accessory
that bolts to the flange. In the URDF, links base→link6 add up to 4.16 kg (the 4.2 kg arm) and
`gripper_base` plus the fingers are another 0.50 kg. The rating is what the flange may carry, and the gripper
counts against it (ISO 9283 convention). With the gripper on, 1.0 kg is left near the base and 0.5 kg at
the 1 kg reach. Take it off and the whole 1 kg goes to the new tool and the auger.

| Carried by the arm | Tool | + auger, cap (+ powder) | Under the 1 kg rating? |
|---|---|---|---|
| Strategy 1 | ≈0.25 kg (printed frame ≈105 g, MG996R 55 g, micro servo 13 g, hardware, driver) | ≈0.1–0.2 kg | yes |
| Strategy 2 | ≈0.25 kg (one 20–25 kg·cm servo + wheel and gears instead of two servos) | ≈0.1–0.2 kg | yes |
| Alternatives A/B | ≈0.53 kg (stock gripper 0.50 + two sleeves) | ≈0.1–0.2 kg | yes |

**With a snap clip the limit is force, not mass.** `clip_force.py` estimates 6–21 N per clip to pull the
auger out (PETG to PLA, μ 0.2–0.35), so 12–40 N for the pair. The whole rating is only ≈15 N at the flange,
and the PiPER has no brakes. The clips can't simply be made soft either: the 20T pinion pushes the 44T gear
up or down with ≈10 N of tooth force (9.5 N·cm stepper on a 10 mm pitch radius), and the clips have to hold
it in mesh. The funnel lowers the push-in force and makes placement forgiving, but it doesn't change pull-out.

## Ranking (1 = best)

| | Complexity (1 = simplest) | Weight on the arm (1 = lightest) | Feasibility / recommendation |
|---|---|---|---|
| **Strategy 1**: two servos | 3 | 1 (tie) | **1** |
| **Strategy 2**: one servo, wheel | 4 | 1 (tie) | 2 |
| **Alternative A**: sleeves + pin | 2 | 3 (tie) | 3 |
| **Alternative B**: sleeves, doser servos hold | 1 | 3 (tie) | 4 |

1. **Strategy 1.** The legs push on the NEMA 11 plate and the floor while the carriage lifts, so the
   12–40 N snap force closes inside the tool and the arm only carries ≈0.35 kg. Lift and hook are
   separate, so it is easy to tune and can back out of a jam. An MG996R on a 9 mm pinion gives ≈100 N at
   stall. Costs: a servo driver and power at the wrist; a 3 mm finger in the 5.5 mm gap by the stepper
   (place it within ±1 mm); and pushing the new auger in still loads the arm, because the feet can only
   push. A hook under the floor edge at x = 34 would close that force inside the tool too.
2. **Strategy 2.** It has the same force advantage, and the crank sits near bottom dead centre exactly
   where the clip force peaks. But the cam fixes the order of moves, so the tool can't re-grip without
   cycling the whole stroke, and it is harder to design and tune. Getting 360° of wheel from a 180° servo
   needs a 2:1 step-up, so the servo needs ≈0.8 N·m at the peak, which is more than an MG996R's margin.
   The bigger servo cancels the weight saving. Build it after Strategy 1 has proven the geometry.
3. **Alternative A.** It is the least new hardware, and the pin keeps the doser safe. But the arm itself
   has to pull 12–40 N on top of a 0.5 kg gripper, 2–4× its rating. It only works if the clips measure
   under ≈5 N each, which fights the ≈10 N gear-mesh force. It also needs two extra moves per swap.
4. **Alternative B.** It has the same arm-force problem. On top of that, the two tilt servos must hold
   ≈2–4 N·m at the hinge, against 3.6–4.4 N·m stall (2 × MG996R through 14T:28T). The plate will rock and
   may stall. It is still a good first experiment: a luggage scale on the auger measures the real clip force.

**Before building anything, measure the printed clip's pull-out force.**

## Onshape

[PiPER auger-swap end effectors - medium fidelity (robot-arms #42)](https://cad.onshape.com/documents/a2afbff32210cfef4035e3a7/w/656f6668acfca73fa886bbb8), in
vcl-shared > 6DOF Robot Arm. It has five Part Studios
([doser + clips + fixture](https://cad.onshape.com/documents/a2afbff32210cfef4035e3a7/w/656f6668acfca73fa886bbb8/e/84da4bd471ae162bb09fd705), [S1 tool](https://cad.onshape.com/documents/a2afbff32210cfef4035e3a7/w/656f6668acfca73fa886bbb8/e/dde328d002bdd126c1aa604f),
[S2 tool](https://cad.onshape.com/documents/a2afbff32210cfef4035e3a7/w/656f6668acfca73fa886bbb8/e/62b0ce943acc1c2d5951923b), [Alt A](https://cad.onshape.com/documents/a2afbff32210cfef4035e3a7/w/656f6668acfca73fa886bbb8/e/0cddbb996c8dc474b02a109d),
[Alt B](https://cad.onshape.com/documents/a2afbff32210cfef4035e3a7/w/656f6668acfca73fa886bbb8/e/c35cc3f6cc387f21bf7cd736)) and four assemblies
([Strategy 1](https://cad.onshape.com/documents/a2afbff32210cfef4035e3a7/w/656f6668acfca73fa886bbb8/e/4b0e2b44f7762a4ba874dfba), [Strategy 2](https://cad.onshape.com/documents/a2afbff32210cfef4035e3a7/w/656f6668acfca73fa886bbb8/e/4c0d62fbf6e4fb0beda072f9),
[Alternative A](https://cad.onshape.com/documents/a2afbff32210cfef4035e3a7/w/656f6668acfca73fa886bbb8/e/c32900085919816e940d424b), [Alternative B](https://cad.onshape.com/documents/a2afbff32210cfef4035e3a7/w/656f6668acfca73fa886bbb8/e/55472b6c00b0741d6cf2e8af)).
The parts are imported STEP solids (no feature history). `python export_step.py && python onshape_upload.py`
re-syncs them. `cad/doser_compliant_clips.step` (29 MB) is regenerated by `export_step.py` and is not committed.

## Sources

- [PiPER quick-start manual (AgileX, via Generation Robots)](https://static.generation-robots.com/media/agilex-piper-user-manual.pdf):
  "1.5kg payload at the end", Effective Load 1.5 kg, Weight 4.2 kg, two-finger gripper 500 g, 0–70 mm, 40 N rated / 50 N max.
- [AgileX PiPER product page](https://global.agilex.ai/products/piper): "1.5 kg end-effector payload".
- [PiPER URDF (piper_ros)](https://github.com/agilexrobotics/piper_ros/blob/ac41fcbcdda598f01b51cf6175ed9a24d0dacadc/src/piper_description/urdf/piper_description.urdf): link masses and joint limits.
- Payload vs. reach curve: [issue #7 comment](https://github.com/vertical-cloud-lab/robot-arms/issues/7#issuecomment-6089393258).
