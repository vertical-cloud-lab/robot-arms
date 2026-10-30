# PiPER auger swap on the powder doser (issue #42)

The PiPER pulls a spent auger out of the powder doser, strips the tethered tap collar
off it in a finger fixture, drops it in a bin, takes a fresh auger from a rack, threads
it back through the collar and presses it into the doser. The auger is held by
**compliant snap clips with a funnel mouth, not the old screw-and-nut clamp**.

| | What holds the auger during the pull | Who supplies the pull-out force | Fidelity |
|---|---|---|---|
| **Strategy 1**: custom tool, two servos | hook + thin finger on a lift carriage | the tool: its legs push on the doser while the carriage lifts | **high** |
| **Strategy 2**: custom tool, one servo | same; a wheel's crank pin lifts and a face cam closes the hook | the tool, the same way | medium |
| **Alternative A**: stock gripper + two-shell sleeves + tilt-lock slider | printed cradles that wrap 180° of the tube on each finger | the arm; a slider on the board stops the mounting plate tipping | **high** |
| **Alternative A, custom fingers**: minimal fingers on the gripper's own carriages + tilt-lock slider | the same cradle, built into the finger | the arm, with the same slider | **high** |
| **Alternative B**: stock gripper + the same sleeves | the same sleeves | the arm; the doser's tilt servos hold the plate | high (sleeves), medium (sequence) |

The finger fixture, sleeves, custom fingers, tilt-lock slider and Strategy 1 tool are high fidelity (rounds 2 to 4, [PR #44](https://github.com/vertical-cloud-lab/robot-arms/pull/44)):
real fasteners, fits and print orientations, and built against the real parts (AgileX's own gripper STEP, the doser's STEP files).
Round 3 made the fixture low and lean and replaced the steel pin with a printed slider that latches itself out (see below).
Round 4 gave the fixture thin side webs and 45° lead-ins, and moved the slider's post to the middle of its knob, with a relief notch in each cradle's jaw.
Strategy 2 is unchanged from round 1, except that it now lowers its carriage at the fixture as Strategy 1 does.

## The PiPER gripper's finger interface

Measured from AgileX's own gripper STEP (the file [PR #10](https://github.com/vertical-cloud-lab/robot-arms/pull/10) uses;
`agilex.py` fetches it, it is not committed because it has no licence). No AgileX document gives these.

| | What it is | Numbers |
|---|---|---|
| Rail | HIWIN MGNR07R size | 7.0 × 4.8 mm, Ø2.4 + Ø4.2 counterbored holes at 15 mm pitch |
| Carriage (one per finger) | HIWIN MGN07C size | 17 × 22.5 × 6.5 mm; **4 × M2**, 2.5 mm thread depth, on a **12 × 8 mm** rectangle (12 across the rail, 8 along it) |
| Finger on the carriage | 4 × Ø2.4 clearance through 6 mm, so **M2 × 8** | the finger sits in a 1 mm deep, 17.3 mm wide slot over the block's sides |
| Linkage arm pivot | slotted **M3 shoulder screw**, Ø2.5 tap hole 5.5 mm deep in the finger | a **Ø9 × 4 mm spacer with a Ø4 bore** (the shoulder) between the finger and the arm; pivot 14.65 mm beside the carriage centre (across the rail) and 1.25 mm off it along the travel |
| Grip face | the "slight curve" | flat for the first 36 mm from the finger's base, then an **R51.5 bend**, a **5.1° ramp** over 20 mm, and flat again for the last 10 mm: the tip half stands **2 mm** closer to the other finger. A 2 mm pad covers it all |
| Finger | | 56 mm wide at the carriage, 20 mm at the tip, 71 mm long, 24.5 mm deep at the carriage, 7 mm at the tip; a 17.3 mm channel down the back |
| J6 flange (for the custom tool) | | Ø57, 6 × M3 countersunk on a **Ø27** bolt circle; on the J6 side a 240° arc slot (Ø44–55.5, 3.8 mm deep) with Ø5.75 round ends at r 24.9 |

AgileX's STEP is the 0–100 mm gripper (164 mm finger plate). The older 0–70 mm one (about 145 mm) also runs on MGN7 carriages, but check
the hole pattern on the lab's unit before printing, as [#4](https://github.com/vertical-cloud-lab/robot-arms/issues/4) asked for the camera mount.

## Finger fixture (tap-collar nest)

![fixture with the collar and auger](renders/view_fixture.png)

| | Round 2 | Now (rounds 3 and 4) |
|---|---|---|
| Height | 89 mm | **47 mm** |
| Footprint | 80 × 49 mm | **40.5 × 31 mm** (1224 mm² on the board, against 3920) |
| Printed volume (solid) | 155 cm³ | **25.5 cm³** (round 3: 24.8; the side webs add 0.95, the lead-ins take 0.3) |
| Auger axis above the board | 75 mm | **35 mm** |
| Screws | 4 × M4 countersunk wood screws in a flange | 2 × M4 countersunk wood screws, under where the collar sits |

**Why it can be this low.** The 75 mm axis was only there for Strategy 1's leg B. With the carriage up, the leg hangs
57 mm below the tube. Strategy 1 now lowers its carriage over the fixture before the tube goes in (and raises it again after the strip),
so the leg ends 29.25 mm below the tube. Strategy 2 does the same with its wheel at 200°, where the cam still holds the hook shut,
leaving its leg 30.4 mm below the tube. At a 35 mm axis, `fit_check.py` gives these clearances to the board, with 0 interferences with the fixture:

| Holding the tube in the fixture | Lowest point above the board |
|---|---|
| Strategy 1 (carriage down), in the fixture and after the 80 mm strip | 5.75 mm (leg B) |
| Strategy 2 (round-1 frame, wheel at 200°) | 4.57 mm (leg B) |
| Sleeves or custom fingers (jaws 17.1 mm below the tube) | 17.9 mm |

The collar's ring hangs 16.75 mm below the tube and the 44T gear 23 mm, so the axis can't go much lower anyway.

![fixture alone](renders/view_fixture_alone.png)

- **Forks F1 (outlet side) and F2 (gear side), both 6 mm**, 1 mm from each face of the collar. F2 now leaves 8.9 mm to the 44T gear.
  The tines are 7.5 mm wide beside **25.5 mm U-slots**: the Ø25 tube passes through, the collar (R16.75 and up) can't.
  The slot floors hold the tube 0.25 mm low, the same as the collar's bore, so the tube goes straight in. Both forks keep
  the 2 mm × 45° conical lead-in on their +Y face for the new auger's tip.
- **45° lead-ins for arm error (round 4).** Each slot's mouth opens at 45° from flat, 5 mm a side over the top 5 mm (round 3: 3.5 mm over 5 mm, 55°),
  so a tube lowered up to 5 mm off across the auger slides down into the slot. That leaves a 1.5 mm flat on each tine, with a 1 mm chamfer outside it.
  The collar has only 1 mm a side between the forks, so each fork's top edge on the collar side also has a 2 mm × 45° chamfer, which catches a collar up to 3 mm off along the auger.
- **Side webs (round 4).** A 2.4 mm web fills the lower part of each side window, between the ledges: flush with the fixture's sides, from the board up to
  20 mm, with 45° on its inner top edge. With the plate and the two ledges they close the base into a box, so a strip load on F2 also goes to F1 through the webs,
  not only through the 4 mm plate. `fit_check.py` finds 0 interferences, and the webs are 3.6 mm from the collar's lug, 32 mm from the solenoid and 11.6 mm from the auger. The two screws stay reachable from above; the webs' inner faces are 2.35 mm outside the countersinks.
- **The nest is two 4.5 mm ledges**, one on each fork's inner face, under the collar's two ends. Their tops are the collar's own underside
  (ring, the lug at +X and the tab at −X), from its STEP, offset 0.25 mm. That outline is the same at every y along the collar,
  so two short ledges hold it as well as round 2's solid block did. The collar can't roll, because its +X lug sits on the ledge, and it lifts straight out.
  `fit_check.py` measures 0.25 mm to the collar and to the tube, and 0 interferences.
- **A 4 mm plate between the ledges** ties the forks together. The two screws go through it, 22 mm apart, where nothing covers them except the collar
  during a swap.
- **Strength.** If a jammed collar took the arm's full 40 N against F2, the forks' root (fork plus ledge, 10.5 mm) would see about 2 MPa and the tines about 5 MPa,
  across the layers, without counting the webs. PETG's interlayer strength is about 20 MPa. A free collar strips at a few newtons.
- **Printing:** base-down, no supports. 15–20 % infill is plenty.

## Alternative A, two ways

Both grip the tube 180° on each side, so the pull-out bears on the cradle walls. Neither depends on friction. The arm still supplies the
12–40 N pull, which is Alternative A's weakness (see Answers below). They grip the tilt-lock slider's Ø25 knob the same way; since round 4 each jaw
has a relief notch in its middle for the slider's post (see the slider below).

| | Two-shell sleeves on the stock fingers | Custom fingers |
|---|---|---|
| GIF | ![Alt A sleeves](renders/alt_a.gif) | ![Alt A custom fingers](renders/alt_a_cf.gif) |
| Tube axis from the J6 face | 135 mm | **89 mm** |
| Gripper command (pad-to-pad width) to hold a Ø25 tube | 34.5 mm | 24.0 mm |
| Command to release | 70 mm | 60 mm (never below 22: the fingers meet) |
| Printed parts per finger | main shell 22.7 cm³ + fixing shell 6.7 cm³ | 15.6 cm³ |
| Hardware per finger | 2 × M3 × 10 + 2 × M3 × 12 countersunk (ISO 10642), 4 × M3 × 5.7 heat-set inserts | 4 × M2 × 8 (the stock screws), 1 × M3 × 5.7 heat-set insert; the stock shoulder screw and spacer |

The custom-finger GIF lands every frame on its IK target (0.00 mm). The sleeves hold the tube 46 mm further from J6, so from the assumed base position
the arm runs out of reach on 20 frames, all around the bin, missing by up to 1.5 mm. With round 2's taller fixture it was 40 frames and 5.8 mm,
two of them lining up on the fixture. Every move at the slider, the doser, the fixture and the rack is exact. The Strategy 1 and Strategy 2 GIFs are exact on every frame.

### Two-shell sleeves (stock fingers)

![sleeves closed on the tube](renders/view_sleeves.png)
![one sleeve, exploded](renders/view_sleeve_exploded.png)

- **Main shell (blue).** It sits on the grip face, carrying a Ø25.2 half-bore with a tooth above and a jaw below that wrap 180° of the tube. Its inner face is the pad's
  own surface, cut from AgileX's finger with 0.15 mm clearance. The 2 mm step and ramp stop it sliding toward the tip, and a lip over
  the fingertip stops it sliding the other way. With both sleeves on the tube, their faces stand 2 mm apart, so all the grip force goes into the tube.
  The jaw has the slider-post relief notch in its middle (round 4): 10 mm wide, taking the jaw back to 4.5 mm from the tube's centre plane, so the cradle
  wraps 155° there and 171° over the rest of its 48 mm.
- **Fixing shell (green).** Two 8 mm bands go round the finger's sides and back at the two arrows, joined by a spine that follows the curved back and drops
  into the back's channel, which locks it sideways. 0.2 mm clearance.
- **Screws: 4 × M3 countersunk, two at each arrow.** They run along the finger travel, beside the finger (4.3 mm outside each edge), through the main shell and into
  heat-set inserts in the bands' legs. The upper pair is 30.5 mm from the fingertip, M3 × 10 through a 5 mm web. The lower pair sits in the bottom of the cradle,
  7.5 mm from the tip, M3 × 12; their heads sit below the half-bore's surface.
- **Printing:** the main shell on its outer web with the cradle up, the fixing shell on its back. Neither needs supports.
  **Re-download both STLs if you have round 2 or 3's:** that `sleeve_fixing_shell_x2.stl` had lost its finger clearance (10.8 cm³, 3.9 cm³ of it inside the finger),
  and that `sleeve_main_shell_x2.stl` wasn't watertight. Building the main shell first had changed the tolerances of the shared AgileX solids; `agilex.solids()` now hands out copies.

### Custom fingers

![custom fingers](renders/view_custom_fingers.png)

- Each finger is a 32 × 35 × 38 mm block that replaces the stock finger. It goes on the same MGN7C carriage with the same four M2 × 8 screws, in the same 1 mm locating
  slot, and takes the linkage arm's shoulder screw in an M3 heat-set insert, with the stock Ø9 spacer between the two.
- The cradle is 19.5 mm in front of the finger plate, against 65.5 mm with the sleeves, so the moment on the carriages and on J6 is much smaller. It is the same
  180° half-bore with tooth, jaw and 2 mm gap, and the same 10 mm relief notch in the jaw for the slider's post (round 4). The notch is centred on the J6 axis,
  so it lines up on both fingers, which are the same print.
- Prints on its side face with no supports; the half-bore is a horizontal arch.
- Make the gripper's lower limit 22 mm (two fingers meet below that) and use 24 mm to hold the tube.

### Tilt-lock slider

![tilt-lock slider, pushed in](renders/view_pin.png)
![latch, pulled out (section)](renders/view_pin_latch.png)

| Custom fingers on the knob | Sleeves on the knob |
|---|---|
| ![custom fingers on the knob](renders/view_knob_custom.png) | ![sleeves on the knob](renders/view_knob_sleeves.png) |

Two PETG prints and two wood screws. They replace round 2's Ø8 steel pin, its housing, the M6 ball plunger and the clamp-on handle with its M3 pinch screw.

| | Round 2 (pin) | Now (slider, rounds 3 and 4) |
|---|---|---|
| Printed volume (solid) | housing 25.5 + handle 24.9 = 50.4 cm³ | guide 7.7 + slider 15.5 = **23.2 cm³** (round 3: 21.2) |
| On the board | 36 × 48 mm flange | **380 mm²**: a 6 mm web, 31 mm long, with two screw tabs |
| Bought parts | Ø8 h6 × 96 shaft, M6 ball plunger, M3 × 16 + nut, 2 × M4 screws | **2 × M4 countersunk wood screws** |
| Holds itself out | ball detent (both ends) | **compliant latch** (out only) |
| Knob | Ø25 bar 75 mm up, on a post *under* it | Ø25 tube 50 mm up, on a post at its middle; notched jaws straddle the post (round 3: a cup 47 mm up, held from its end) |

- **Slider.** It is an 8 × 10 mm bar. Pushed in, its tip lies 0.5 mm over the mounting-plate floor's +X edge (x = 34) and overlaps it by 16 mm,
  so the plate can't tip up while the arm pulls. Pulled out, the tip is 6 mm clear of the floor (6.3 mm measured).
  The 22 mm stroke and positions are round 2's. The tip has a 30° chamfer underneath, in case the plate sits a little high.
- **Knob: the same Ø25 as the auger tube**, so the sleeves and custom fingers wrap it exactly as they wrap the tube. Since round 4 it is a T:
  a 40 mm tube with a 3 mm wall, centred on the bar, on a 6 × 6 mm post that rises from the bar's end into an 8 mm solid hub at the knob's middle.
  The gripper centres on the post, so its push and pull act in the bar's own centre plane and can't twist the bar in its 0.25 mm guide.
  Round 3's cup stuck out 28 mm to one side of the bar, so the gripper pushed about 20 mm off the bar's centre line.
  - **The post sits where the two jaws meet.** That is why round 3 held the knob from its end, after round 2's post under its bar overlapped the closed cradles
    by 286 mm³ per finger. Round 4 notches the jaws instead. Each cradle's jaw has a 10 mm wide relief notch in its middle that takes it back to 4.5 mm from
    the tube's centre plane, so the post (6 mm across) clears it by 1.5 mm across the knob and 2 mm along it. The notch is centred on the J6 axis, so it lines up
    on both fingers. The cradle still wraps 155° there (171° elsewhere), and on the auger tube the notch faces down, away from everything.
  - **Checked:** with the sleeves or custom fingers closed on the knob, in and out, `fit_check.py` gives 0 interferences with the slider, guide, doser (with its auger, 44T gear and stepper in place) and board.
    The cradles are 0.10 mm from the knob, the notches 1.50 mm from the post, and the jaws 32.9 mm above the board.
  - **Height.** The knob is now at 50 mm (round 3: 47). Centred on the slider, the custom-finger gripper's finger plate passes 0.9 mm to the side of the 44T gear;
    at 47 mm it would have been only 0.2 mm above the gear's top. At 50 mm it is 3.2 mm above it, and 9.8 mm over the rear clip's lips (z 59.7).
- **Guide.** A tunnel 0.25 mm a side over the bar, with a 3 mm roof, 3 mm walls and a 6 mm I-web underneath. Two tabs at the −X end take
  2 × M4 countersunk wood screws, at that end because the floor's push lifts it. It prints base-down; the tunnel roof is an 8.5 mm bridge.
- **Latch (holds the slider out against vibration).**
  - **The spring.** A 20 × 8 × 2 mm cantilever is cut into the top of the bar by a 1.5 mm slot. Its root is toward the knob, and its free end carries a 1.3 mm bump.
  - **Pulled out, it locks.** The bump springs up into a window in the guide's roof. Its −X face is a 40° ramp. Its +X face is undercut 15°, against a matching wall,
    so pulling harder hooks it in deeper. It is also the out stop.
  - **Pushing in (−X)** slides the ramp under the roof edge: the beam bends 1.05 mm, with 4.2 N on the bump and 0.8 % strain (PETG yields at about 4 %).
    It takes **≈6.4 N** (μ 0.3), and the gripper pushes it through the knob. Shaking can't produce that: the whole slider is about 20 g.
  - **Pushed in,** the bump rides under the roof with ≈1.3 N of friction. Nothing latches it there, as asked.
    The beam stays bent only for the length of a swap.
  - **The slot is also a stop.** Pressing the bump by hand bottoms the beam at 1.1 % strain. That is how to release it and take the slider out: press the bump through the window and pull.
- **Strength.** If the floor pushes up with the full 33 N, the bar sees 3 MPa at the guide's mouth and 6.7 MPa at the slot, which is 8 × 6.5 mm.
  The post, 25.5 mm from the bar's top to the knob's axis, sees about 5 MPa at the 6.4 N unlatch push and 15 MPa if the gripper pushes 20 N.
  All three are along the print layers, where PETG is good for about 45 MPa. The roof carries the ≈46 N reaction at about 5 MPa.
- **Printing:** the slider stands on one end of the knob (`cad/stl/pin_slider.stl` is already turned), so the bar, latch beam and post are in the layer plane
  and the knob prints as an upright tube. The bar is at the knob's mid-length, 16 mm off the bed, so it **needs supports** under it (tree supports from the plate are enough).
  The hub inside the knob bridges its Ø19 bore. The guide prints base-down with no supports.
- In the Alt A STEP files the slider is pushed in, with its latch beam drawn bent 1.05 mm under the roof.

## Strategy 1, high fidelity: two-servo tool with a Pi 5 and two cameras

![Strategy 1](renders/s1.gif)

![Strategy 1 tool](renders/view_s1_tool.png)

`s1_tool.py` builds it, checks it and exports `cad/s1_two_servo_tool.step` (56 solids). The motion, contact points and frames are round 1's, so it runs the same sequence.
Over the finger fixture it now lowers its carriage before the tube goes in, so leg B ends 5.75 mm above the board with the fixture's axis at 35 mm,
and it raises the carriage again after the strip and after the re-thread.

**Fixed in round 3:** round 2's GIF landed the tool 28 mm too low on the doser, with the legs 28 mm into the NEMA 11 plate and the floor and the hook
closing 28 mm under the tube. Strategy 2's GIF had the same error. Both now land the legs on their faces, lower the carriage, close the hook and lift.

**Load path.** Leg A presses on the NEMA 11 plate and leg B on the mounting-plate floor. The frame carries that load to the guide rail and the lift pinion,
and the rack and carriage take it down to the hook under the tube. The 12–40 N snap force closes inside the tool; the arm only carries the tool's weight.

| | Part | Notes |
|---|---|---|
| J6 adapter | Al 6061, Ø57 × 10.5, a copy of the stock gripper's flange | 6 × M3 × 8 countersunk (ISO 10642) into J6 on the Ø27 circle; the J6 side has the stock 240° arc slot (Ø44–55.5) and Ø5.75 ends; 4 × M3 into the deck. A PETG or PA-CF print also works with washers at ≈0.3 N·m |
| Frame | one PETG print, deck down, 4 perimeters, 40 % gyroid | 107 × 76 × 6 deck with lightening windows and a cable hole; leg A wall (10 mm) carrying the rail on 4 × M3 heat-set inserts; leg B post + 3.5 mm floor pad; the lift-servo cradle; the Pi plate |
| Guide | HIWIN MGN9H block on a 70 mm MGNR9 rail | 4 × M3 × 8 into the wall, 4 × M3 × 10 through the carriage; 28 mm stroke, the block stays on the rail at both ends |
| Lift | **Feetech STS3215-C018** (12 V), 18T m1 20° involute pinion (pitch Ø18, brass or PA12) on its horn, m1 rack 40 mm on the carriage | 40 N × 9 mm = 0.36 N·m against 2.94 N·m stall (8×); the 28 mm stroke is 178° of output, 0.66 s unloaded. The rack stays in mesh over the whole stroke |
| Carriage | PETG | plate on the MGN9H block; its Ø26 underside is a **presser** that pushes the new auger into the clips (round 1's carriage had nothing over the tube); two F686ZZ bearings for the hook shaft |
| Finger | 3 mm 304 stainless, 16 wide, 1.2 mm lead-in | 2 × M3 × 8 countersunk into inserts; 0.9 mm from the tube, 1.6 mm from the NEMA 11 |
| Hook | PETG jaw (R13–R17, 25° to −128°), Ø6 h6 D-shaft 41.5 mm in the two F686ZZ, Al hub, DIN 6799 e-clip | **Hook servo: a second STS3215-C018**, coaxial with the pivot behind the rear clip (there is no room for a servo case at the pivot itself) |
| Pi 5 | Raspberry Pi 5 + Active Cooler, vertical on the +X plate, M2.5 standoffs | top edge 18.5 mm below the flange face |
| Servo bus | Waveshare Bus Servo Adapter (A) on leg A's outer face | USB-C to the Pi; both servos on one half-duplex TTL bus with position, load, current and temperature feedback |
| Power | Pololu D36V50F5 (5 V, 5.5 A) on the deck for the Pi; a 24 → 12 V buck for the servos (not modelled) | fed from J6's XT30 (2+2) port, 24 V / 2 A max |
| Cameras | PR #10's: Raspberry Pi HQ Camera + the 6 mm CS lens, and the Camera Module 3 Wide | on a PETG pod at the +X/−Y corner, both aimed at the jaw 41° down from the open side, clear of both legs |

**Why two STS3215s.** When the carriage lifts, the tube pushes down on the jaw through its centre, 20 mm from the pivot. That pushes the hook open
with 0.24 N·m at 12 N and **0.8 N·m at 40 N**. An STS3032 (0.44 N·m stall) can't hold that; the C018 holds it at 27 % of stall.
One servo type also means one horn, one spare and one protocol.

**Checks** (`python s1_tool.py`, about 4.5 min): **0 interferences** with all 32 parts against the doser (mounting plate, NEMA 11 and pinion, baseplate,
collar base, auger with gear and cap, collar and solenoid, both clips) and each other. That holds seated with the hook closed, lifted 28 mm, and with the hook
open at s = 28, 14 and 0. Both legs touch their faces with a 0.000 mm gap. The smallest designed gaps are the finger to the tube (0.9 mm), the presser and jaw
to the tube (0.5 mm) and the hook servo to the tube (3.3 mm).

**Mass: ≈0.62 kg** on the arm with realistic infill (679 g with solid prints): 2 × STS3215 110 g, Pi 5 + cooler 69 g, HQ Camera + lens 95 g,
MGN9 53 g, Al adapter 41 g, the rest printed parts and hardware. With the auger, 0.7–0.8 kg, inside the 1 kg left with the gripper off.
Dropping the HQ Camera and lens (keeping the CM3 Wide) saves 95 g.

**Watch:**
- **J6 clocking** comes from the STEP-to-URDF mapping, not an arm. If the arc-slot key doesn't line up, rotate the pattern.
- **Close focus.** The 6 mm lens focuses no closer than 0.2 m, but the jaw is ≈60 mm away. Adjust the HQ Camera's back focus by ≈+0.7 mm, or let the CM3 Wide (autofocus) do the close-up.
- **Size.** The tool is 181 mm across x, because the cameras sit out at the corner to see past leg B.
- **Round-1 numbers.** The real STEPs corrected three of them. The NEMA 11 plate top is at z 61.35, not 61.2. Round 1's hook arm cut 2.1 mm³ into the tube, so the new jaw is trimmed to R13. Round 1's full-height leg B was in the opening hook's path, so the new post sits at y ≥ 9.

### Recommended servos and electronics to buy

| Item | Part | Qty | Price (each) | Where |
|---|---|---|---|---|
| Lift and hook servos | **Feetech STS3215-C018**, 12 V, 30 kg·cm (2.94 N·m) stall, 360° with multi-turn mode, 12-bit magnetic encoder, position/load/current/temperature feedback, 55 g | 2 (+1 spare) | $21.99 | [Waveshare SKU 22414](https://www.waveshare.com/st3215-servo.htm?sku=22414), [RobotShop](https://www.robotshop.com/products/feetech-12v-30kgcm-magnetic-encoding-servo-sts3215) |
| Bus adapter | Waveshare Bus Servo Adapter (A), USB-C to the Pi, 42 × 33 mm | 1 | $4.99 | [Waveshare](https://www.waveshare.com/bus-servo-adapter-a.htm) |
| 12 V rail | Pololu D36V50F12 (24 → 12 V, 4.5 A) | 1 | $39.95 | [Pololu 4095](https://www.pololu.com/product/4095) |
| 5 V rail | Pololu D36V50F5 (5 V, 5.5 A), modelled; or the smaller D24V50F5 (6–38 V in, 5 A) | 1 | $39.95 / $32.95 | [Pololu 4091](https://www.pololu.com/product/4091), [Pololu 2851](https://www.pololu.com/product/2851) |
| Wrist power | Amass XT30PW(2+2) to mate J6's XT30 port (check its gender first) and a ≤2 A fuse | 1 | | [datasheet](https://atta.szlcsc.com/upload/public/pdf/source/20240112/A815AE62CB016131F8636555ECBDABF7.pdf) |
| Compute and cameras | Raspberry Pi 5 + Active Cooler, HQ Camera + 6 mm CS lens, Camera Module 3 Wide (as in [#10](https://github.com/vertical-cloud-lab/robot-arms/pull/10)) | 1 each | | |
| Guide and bearings | HIWIN MGN9H block + MGNR9 rail (70 mm), 2 × F686ZZ, Ø6 h6 D-shaft | | | |

- **Why not the 7.4 V STS3215-C001 + STS3032** (the cheapest pair on one 7.2 V rail)? The C001 lifts fine (1.91 N·m stall), but the STS3032 can't hold the hook's 0.8 N·m.
  If the clips measure under ≈20 N, the C001 + STS3032 pair on a 7.2 V Pololu D30V33MAS works and draws less.
- **Why not PWM servos?** 28 mm on a 9 mm pinion is 178° of output, the whole travel of a 180° PWM servo (the MG996R does about 120°). PWM servos also give
  no load feedback, and that feedback is how the tool sees the clips let go or a jam.
- **Power budget.** J6 gives 24 V × 2 A = 48 W. Lifting at 40 N with the hook holding takes ≈0.3 + 0.7 A at 12 V; with the Pi 5 and cameras (≈7 W) that is
  ≈1 A from the 24 V port. Two stalled C018s plus the Pi would draw ≈3.3 A, so cap the torque (register 48): 60 % on the lift (≈1.8 N·m) and 40 % on the
  hook (≈1.2 N·m, 1.5× its need) keep a double stall at ≈1.8 A.
  AgileX reserves the end CAN pins for its own devices, so the Pi talks over the network and the tool uses the power pins only.
- **Software:** Feetech's [FTServo_Python](https://github.com/ftservo/FTServo_Python) or LeRobot's Feetech driver (it drives the same STS3215s on the SO-101).

### Powering the Pi from J6's XT30 (proposed)

![Wiring from J6's XT30 to the Pi 5 and the servos](renders/power_wiring.png)

![The same parts sketched on the Strategy 1 tool](renders/power_on_tool.png)

- **Pi chain.** The XT30 (2+2) pigtail uses only + and −; CAN-H/L stay unconnected. Then a ≤2 A fuse, a 47–100 µF 50 V electrolytic across the 24 V,
  a Pololu D36V28F5 (24 → 5 V, 3.2 A, 3.3 g), and two short 22 AWG leads in a 1×2 Dupont housing on header pins 4 (5 V) and 6 (GND). The cap, the buck
  and the leads come to ≈6 g, against 7 g for the D36V50F5 alone that `s1_tool.py` models.
- **In parallel, not in series.** The servos' D36V50F12 takes the same 24 V, so a stalled servo can't pull the Pi's 5 V down. `s1_tool.py` still feeds
  the 5 V buck from the 12 V rail.
- **Check the polarity before the first plug-in.** Nothing on the header protects against reversing it.
- **No USB-PD.** The Pi 5 assumes a 3 A supply, warns about low power and caps its USB ports at 600 mA. The servo adapter draws tens of mA, so that's fine.
- **Power cuts.** Nobody has checked yet whether J6's 24 V drops when the arm is disabled, so turn on raspi-config's overlay file system.
- **The 3D view is a sketch.** `power_setup.py` draws it on `s1_tool.py`'s parts, with the D36V50F12 in the D36V50F5's place and the D36V28F5 on the
  deck's +X/+Y corner. The CAD, STEP and mass table are unchanged. AgileX's URDF doesn't model J6's XT30 port, so the pigtail is drawn loose.

## Files

- `geometry.py`: round-1 CadQuery parts in the doser's layout frame: funnel clip, rack, bin, Strategy 2 tool, old sleeves and pin; also the layout numbers (fixture axis height, slider positions).
- `hifi.py`: the high-fidelity parts: finger fixture (with `fixture_side_webs()`), two-shell sleeves, custom finger, tilt-lock slider and guide (and `latch_numbers()`),
  the cradles' `post_relief()` notch, and their fasteners.
- `fit_check.py`: interference and clearance checks for the fixture (with the collar and every tool, and the side webs' gaps) and the slider (with the doser, its auger, 44T gear and stepper, and both grippers on its knob, notches round the post), about 20 min.
- `agilex.py`: fetches AgileX's gripper STEP and holds what was measured from it (carriage, pivot, frames).
- `s1_tool.py`: the high-fidelity Strategy 1 tool (see above).
- `scene.py`: fetches the doser STEP files and `layout.py` from
  [powder-doser `7f5b3b7`](https://github.com/vertical-cloud-lab/powder-doser/tree/7f5b3b7/cad/full-assembly)
  and the PiPER URDF/meshes from
  [`agilexrobotics/piper_ros`](https://github.com/agilexrobotics/piper_ros/tree/ac41fcbcdda598f01b51cf6175ed9a24d0dacadc/src/piper_description).
  It has PiPER forward kinematics and IK from the URDF.
- `animate.py`: the GIFs in `renders/`, with the PiPER posed by IK every frame and the tool pointing down.
  The stock-gripper GIFs draw AgileX's gripper from its STEP; Strategy 1 draws `s1_tool.py`'s parts.
  Run `xvfb-run -a python animate.py s1 alt_a alt_a_cf alt_b`.
- `clip_force.py`: a rough curved-beam estimate of the clips' snap force.
- `power_setup.py`: the wrist-power wiring diagram and its 3D sketch on the Strategy 1 tool (`xvfb-run -a python power_setup.py`).
- `export_step.py`, `onshape_upload.py`, `cad/`, `onshape/`: STEP exports and the Onshape document (see `onshape/onshape_document.json`).
  `cad/stl/` has the printable parts, each in its print orientation: the fixture, sleeve shells, custom finger, slider and guide (print `_x2` files twice).
  `cad/doser_compliant_clips.step` (29 MB) and the AgileX reference copies are regenerated by `export_step.py` and are not committed.

## Assumptions

- **Cell layout.** The PiPER base is at (220, 400) mm in the doser frame. The finger fixture is 150 mm to +X of the auger, the rack is at x = 240–360, and the bin
  is at x = −185…−65, all on the doser's board. None of this is measured; move it once the cell is laid out.
- **Doser.** It is PR 170's current-design assembly with the two bolted brackets replaced by clips: Ø25.1 bore, 17 mm mouth, 2 mm wall, 10 mm wide
  (Sam's multi-doser numbers), plus a 35° funnel lip.
- **Grip windows.** Between the 44T gear and the rear clip, the NEMA 11 body is only **5.5 mm** from the tube on −X. Strategy 1 therefore uses a 3 mm fixed finger
  on that side and a hook from the open +X side. The stock gripper's fingers are 56 mm wide and can't fit that 41 mm window, so Alternatives A and B grip the free
  tube behind the rear clip instead (y ≈ 216).
- **Gear.** Lifting the auger rolls the 44T gear off the 20T pinion over the first ~12 mm, which turns the auger ~30°. Either disable the stepper driver during a swap
  so the pinion can turn, or rely on the hook or cradles cradling the tube rather than clamping it.
- **Tap collar.** Its bore is Ø25.4 on a Ø25 tube: 0.2 mm a side. A 1 mm × 45° chamfer at both ends of the bore (a doser-repo change) would make re-threading far
  more forgiving than any fixture can.
- **Gripper version.** The STEP is AgileX's 0–100 mm gripper; see above.

## Answers

**Does the 1.5 kg rating include the stock gripper?** Yes. The manual says the arm has "a 1.5kg payload at the end"
and lists Effective Load 1.5 kg and Weight 4.2 kg. The two-finger gripper (500 g) is an optional accessory
that bolts to the flange. In the URDF, links base→link6 add up to 4.16 kg (the 4.2 kg arm) and
`gripper_base` plus the fingers are another 0.50 kg. The rating is what the flange may carry, and the gripper
counts against it (ISO 9283 convention). With the gripper on, 1.0 kg is left near the base and 0.5 kg at
the 1 kg reach. Take it off and the whole 1 kg goes to the new tool and the auger.

| Carried by the arm | Tool | + auger, cap (+ powder) | Under the 1 kg rating? |
|---|---|---|---|
| Strategy 1 (high fidelity) | ≈0.62 kg (2 × STS3215, Pi 5 + cooler, HQ Camera + 6 mm lens, CM3 Wide, MGN9 guide, Al adapter, printed frame/carriage/pod at ≈60 % of solid, cables) | ≈0.1–0.2 kg | yes |
| Strategy 2 | ≈0.25 kg (one 20–25 kg·cm servo + wheel and gears instead of two servos) | ≈0.1–0.2 kg | yes |
| Alternatives A/B, sleeves | ≈0.54 kg (stock gripper 0.50 + two two-shell sleeves ≈40 g printed at 50 % + 8 screws and inserts) | ≈0.1–0.2 kg | yes |
| Alternative A, custom fingers | ≈0.50 kg (the custom fingers weigh about what the stock ones do, 25 g each in the URDF) | ≈0.1–0.2 kg | yes |

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
| **Alternative A**: custom fingers or sleeves, + slider | 2 | 3 (tie) | 3 |
| **Alternative B**: sleeves, doser servos hold | 1 | 3 (tie) | 4 |

1. **Strategy 1.** The legs push on the NEMA 11 plate and the floor while the carriage lifts, so the
   12–40 N snap force closes inside the tool. Lift and hook are separate, so it is easy to tune and can
   back out of a jam. The STS3215-C018 on a 9 mm pinion gives ≈110 N at its rated torque and ≈330 N at
   stall (12 V), and it reports load, so the tool can see the clips let go. Costs: power at the wrist (J6's
   24 V / 2 A port covers it); a 3 mm finger in the 5.5 mm gap by the stepper (place it within ±1 mm);
   and pushing the new auger in still loads the arm, because the feet can only push. A hook under the
   floor edge at x = 34 would close that force inside the tool too.
2. **Strategy 2.** It has the same force advantage, and the crank sits near bottom dead centre exactly
   where the clip force peaks. But the cam fixes the order of moves, so the tool can't re-grip without
   cycling the whole stroke, and it is harder to design and tune. Getting 360° of wheel from a 180° servo
   needs a 2:1 step-up, so the servo needs ≈0.8 N·m at the peak, which is more than an MG996R's margin.
   The bigger servo cancels the weight saving. Build it after Strategy 1 has proven the geometry.
3. **Alternative A.** It is the least new hardware, and the tilt-lock slider keeps the doser safe. The 180° cradles
   make the grip itself positive. But the arm still has to pull 12–40 N on top of a 0.5 kg gripper, 2–4×
   its rating. It only works if the clips measure under ≈5 N each, which fights the ≈10 N gear-mesh force,
   and it needs two extra moves per swap. Of its two versions, the custom fingers are the better one: the
   tube sits 89 mm from the J6 face instead of 135 mm, which shortens the lever on the carriages and on
   J6. They also don't depend on the stock fingers' exact shape, and the arm reaches every pose in the GIF.
4. **Alternative B.** It has the same arm-force problem. On top of that, the two tilt servos must hold
   ≈2–4 N·m at the hinge, against 3.6–4.4 N·m stall (2 × MG996R through 14T:28T). The plate will rock and
   may stall. It is still a good first experiment: a luggage scale on the auger measures the real clip force.

**Before building anything, measure the printed clip's pull-out force.**

## Onshape

[PiPER auger-swap end effectors (robot-arms #42)](https://cad.onshape.com/documents/a2afbff32210cfef4035e3a7/w/656f6668acfca73fa886bbb8), in vcl-shared > 6DOF Robot Arm. Part Studios: [doser + clips + finger fixture](https://cad.onshape.com/documents/a2afbff32210cfef4035e3a7/w/656f6668acfca73fa886bbb8/e/84da4bd471ae162bb09fd705), [Strategy 1 tool](https://cad.onshape.com/documents/a2afbff32210cfef4035e3a7/w/656f6668acfca73fa886bbb8/e/dde328d002bdd126c1aa604f), [Strategy 2 tool](https://cad.onshape.com/documents/a2afbff32210cfef4035e3a7/w/656f6668acfca73fa886bbb8/e/62b0ce943acc1c2d5951923b), [Alt A sleeves + slider](https://cad.onshape.com/documents/a2afbff32210cfef4035e3a7/w/656f6668acfca73fa886bbb8/e/0cddbb996c8dc474b02a109d), [Alt A custom fingers + slider](https://cad.onshape.com/documents/a2afbff32210cfef4035e3a7/w/656f6668acfca73fa886bbb8/e/4d6e11d16ea5da425da28134), [Alt B sleeves](https://cad.onshape.com/documents/a2afbff32210cfef4035e3a7/w/656f6668acfca73fa886bbb8/e/c35cc3f6cc387f21bf7cd736), [AgileX gripper, sleeve pose](https://cad.onshape.com/documents/a2afbff32210cfef4035e3a7/w/656f6668acfca73fa886bbb8/e/4b031882d11b4ae954b45ec7), [AgileX gripper, custom-finger pose](https://cad.onshape.com/documents/a2afbff32210cfef4035e3a7/w/656f6668acfca73fa886bbb8/e/a66cfbff4e42ef06e9f2db39). Assemblies: [Strategy 1](https://cad.onshape.com/documents/a2afbff32210cfef4035e3a7/w/656f6668acfca73fa886bbb8/e/4b0e2b44f7762a4ba874dfba), [Strategy 2](https://cad.onshape.com/documents/a2afbff32210cfef4035e3a7/w/656f6668acfca73fa886bbb8/e/4c0d62fbf6e4fb0beda072f9), [Alternative A](https://cad.onshape.com/documents/a2afbff32210cfef4035e3a7/w/656f6668acfca73fa886bbb8/e/c32900085919816e940d424b), [Alternative B](https://cad.onshape.com/documents/a2afbff32210cfef4035e3a7/w/656f6668acfca73fa886bbb8/e/55472b6c00b0741d6cf2e8af), [Alternative A custom fingers](https://cad.onshape.com/documents/a2afbff32210cfef4035e3a7/w/656f6668acfca73fa886bbb8/e/5a5c127205394e863e2a013d).

The parts are imported STEP solids (no feature history). `python export_step.py && python onshape_upload.py` re-syncs them in place. The two AgileX gripper Part Studios are AgileX's own STEP, placed where the sleeves or custom fingers hold the tube. They are only in the (private) Onshape document, not in this repo.

| Strategy 1 | Alternative A, sleeves | Alternative A, custom fingers |
|---|---|---|
| ![](onshape/onshape_strategy_1_closeup.png) | ![](onshape/onshape_alternative_a_closeup.png) | ![](onshape/onshape_alternative_a_custom_fingers_closeup.png) |

## Sources

- [AgileX gripper STEP](https://cdn.shopify.com/s/files/1/0673/6848/5000/files/AgileX_Gripper-1-STP.STEP?v=1782224095) (sha256 `6e6c9bb0…`, as PR #10 fetched it): every finger, carriage and flange number above.
- [HIWIN MGN catalog](https://damencnc.com/userdata/file/3455-3_HIWIN_MGN_and_MGW_Product_Catalog_2023.pdf), pp. 97–99: MGN07C (W 17, L 22.5, B 12, C 8, M2 × 2.5) and MGNR07R.
- [PiPER user manual](https://cdn.shopify.com/s/files/1/0551/0630/6141/files/PIPER_Product_User_Manual.pdf?v=1791860528), §2.9: "The end joint reserves the XT30 2+2 interface … Voltage: 24V, current: 2A MAX"; the end CAN is for AgileX's own devices only.
- [PiPER quick-start manual (AgileX, via Generation Robots)](https://static.generation-robots.com/media/agilex-piper-user-manual.pdf):
  "1.5kg payload at the end", Effective Load 1.5 kg, Weight 4.2 kg, two-finger gripper 500 g, 40 N rated / 50 N max.
- [AgileX PiPER product page](https://global.agilex.ai/products/piper): "1.5 kg end-effector payload".
- [PiPER URDF (piper_ros)](https://github.com/agilexrobotics/piper_ros/blob/ac41fcbcdda598f01b51cf6175ed9a24d0dacadc/src/piper_description/urdf/piper_description.urdf): link masses and joint limits.
- Payload vs. reach curve: [issue #7 comment](https://github.com/vertical-cloud-lab/robot-arms/issues/7#issuecomment-6089393258).
- Feetech STS3215-C018 (12 V) [datasheet](https://www.feetechrc.com/Data/feetechrc/upload/file/20260622/6391772519923113075854851.pdf) and C001 (7.4 V) [datasheet](https://www.feetechrc.com/Data/feetechrc/upload/file/20260622/6391772523943436695270694.pdf); [Waveshare ST3215 page and drawing](https://www.waveshare.com/st3215-servo.htm); STS3032 [datasheet](https://www.feetechrc.com/Data/feetechrc/upload/file/20260622/6391772539739757769932408.pdf).
- [TheRobotStudio SO-ARM100 STS3215 STEP](https://github.com/TheRobotStudio/SO-ARM100/blob/main/STEP/SO100/STS3215_03a.step) (horn and hole cross-check); [LeRobot SO-101](https://huggingface.co/docs/lerobot/so101).
- [Waveshare Bus Servo Adapter (A)](https://www.waveshare.com/bus-servo-adapter-a.htm); [Pololu D36V50F5](https://www.pololu.com/product/4091), [D36V50F12](https://www.pololu.com/product/4095), [D24V50F5](https://www.pololu.com/product/2851).
- Raspberry Pi 5, HQ Camera, 6 mm CS lens and Camera Module 3 Wide: the official drawings as used in PR #10's `piper-camera-mount/cad/piper_mount.py` and `lenses.py`.
- [Feetech STS memory table](https://ftservo.github.io/ftservo-wiki/reference/parameter/memory-sts/) (torque limit, current readout).
