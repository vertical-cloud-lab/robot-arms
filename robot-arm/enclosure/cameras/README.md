# PiPER table: reach and fixed cameras

Renderings of the PiPER table as it stood on 23 Oct 2026
([photo on PR #9](https://github.com/vertical-cloud-lab/robot-arms/pull/9)), with the arm's reach and
two layouts for the three fixed cameras, plus printable fixtures for them. The PVC cube from
[#38](https://github.com/vertical-cloud-lab/robot-arms/issues/38) and its drop cloth are drawn
see-through in every view.

| File | What it is |
|---|---|
| [`build.py`](build.py) | The table, the reach, the camera layouts, the printed parts and every number below |
| [`render.py`](render.py) | All the figures |
| [`models/*.stl`](models/) | The six printed parts, in mm, in their print orientation |
| [`cameras-edges.json`](cameras-edges.json), [`cameras-corners.json`](cameras-corners.json) | Nominal pose of each camera, in the format `piper_twin.py` reads (#24) |
| [`results.json`](results.json) | Reach, camera positions, tilts and coverage |
| `reach.npz` | The reach as a 20 mm voxel grid, and the plywood the fingertips can touch |

To regenerate, run `python build.py && xvfb-run -a python render.py`.

## Which side is which

I took the sides from the photo:

- **Front:** the open side you stand at, with the magnetic switch at its right end.
- **Left:** the block wall.
- **Back:** the door.
- **Right:** the side by the grey cabinet.

The arm faces the wall at J1 = 0 (its gripper points that way in the photo), and J1 is at the
plywood's centre.

**The A1 mini is where the photo shows it:** on the wall side, at the front-left corner, facing the
arm. The comment says front-right. If it moves there, layout 4's front camera should go in the
front-left corner instead. The feet and heads fit either corner.

## 1. The table

![The table](1-table.png)

## 2. Reach

![Reach](2-reach.png)

The blue volume is everywhere the fingertips can reach with every joint inside its URDF limit and no
link below the plywood. The darker blue on the plywood is where they can get within 30 mm of it.

- The fingertips reach up to **766 mm** from J1 and **889 mm** above the plywood.
- They can touch **93 %** of the plywood. They miss the far corners and the notch toward the right
  side, behind the arm, where J1 stops at ±150°.

## 3 and 4. Camera layouts

![Layout 3](3-cameras-edges.png)

![Layout 4](4-cameras-corners.png)

Both layouts use Camera Module 3 Wide: 99° × 67° with the nominal lens, no distortion. Coverage is
the share of the reach volume within 300 mm of the plywood (the "work zone") that falls inside a
camera's image. It ignores anything that blocks the view; the small images show what each camera
actually sees.

| | Layout 3: mid-edge, top in the middle | **Layout 4: corners, top on the wall-side rail** |
|---|---|---|
| Front camera | Post at the front edge's middle, 30° down | Post in the front-right corner, 30° down |
| Right camera | Post at the right edge's middle, 30° down | Post in the back-right corner, 30° down |
| Top camera | Under a crossbar at the centre, lens 1204 mm up, straight down | On the middle of the wall-side top rail, lens 1175 mm up, 65° down |
| Work zone seen by front / right / top | 70 % / 73 % / 97 % | **92 % / 92 % / 100 %** |
| Seen by 2 or more cameras | 86 % | **98 %** |
| Can the fingertips hit a post? | **Yes**, both: the posts are 582 mm from J1 | No, the posts are 46 mm out of reach |
| Extra parts | 1290 mm crossbar and 2 cross clamps | None |

**I recommend layout 4.** Each ground camera sees 92 % of the work zone instead of 70–73 %, almost all
of it is seen twice, the arm can't reach the posts, and no crossbar is needed. The corner cameras sit
90° apart, so between them they see both sides of whatever the gripper is holding. The top camera
is on the wall side, so it looks at the gripper's working side and is out of the way of anyone
reaching in from the front.

In layout 3, the front and right posts stand inside the arm's reach. They would need a keep-out
zone in software.

Before installing layout 4, two things need checking:

- **The plywood shelf in the photo** sits in the back-right corner. It has to move about 10 cm
  toward the middle to make room for that post.
- **Cables.** #39's plan puts the right and top cameras on mpzy, and they end up about 1.5 m apart in
  layout 4. One fix is a Pi on the middle of the back top rail, with 1 m camera cables to both
  cameras. The other is to give mpzy the two corner cameras (1.07 m apart) and eufi the top one.

## The fixtures

![Fixtures](fixtures.png)

![Printed parts](parts.png)

**All three cameras use the same printed clamp, and it clamps onto ¾ in PVC.** The cradle that holds
the camera comes in two versions: a vertical one for the posts and a horizontal one for the top
camera (see [The two cradles](#the-two-cradles)), each set for one board orientation.

- **Ground cameras:** a post of ¾ in PVC stands in a small printed foot. Two 400 mm posts can come
  from the enclosure's off-cuts: each 10 ft stick left about 24 in over.
- **Top camera, layout 4:** the head clamps straight onto the top rail.
- **Top camera, layout 3:** the head clamps onto a crossbar that rests on two top rails in two cross
  clamps.

The feet, posts and heads therefore move between layouts 3 and 4 unchanged.

- **Head (3 parts, about 23 cm³, 29 g):**
  - **Clamp:** a half ring with a hinge plate on it.
  - **Cap:** the other half ring. Two M3 bolts close the cap on any part of a pipe, so nothing has to
    come apart.
  - **Cradle:** carries the camera board on four standoffs, vertical or horizontal version. It pivots
    on an M4 bolt.
- **Locking the head (repeatability):**
  - Tilt is set by a 2 mm pin through one of seven index holes, every 15° from −45° to +45°, so it
    goes back to the same angle.
  - A #6 screw through the cap into the PVC stops the clamp from turning.
- **Ground foot:** 56 × 56 mm. Its edges go flush with the plywood's edges: two edges in a corner, one
  edge at a mid-edge mark. Four #8 screws hold it down, and a #6 screw pins the post in its socket.
  The post's axis ends up 28 mm in from each flush edge.
- **Cross clamp (layout 3 only):** a half ring over the top rail, closed by a cap from below, with a
  sleeve above for the crossbar.

### The two cradles

![The two cradles](cradles.png)

The first cradle had eight standoffs so one part could hold the board either way round. Printed, it
didn't work: two of the extra standoffs land on the board's ribbon connector, and the 18 mm notch
was too small for the 16 mm ribbon. Each cradle now has **four standoffs, set for one board
orientation**:

- **Vertical** ([`head-cradle-vertical.stl`](models/head-cradle-vertical.stl), print 2) for the
  posts. The connector edge points down the post, so the image is wide across the post (landscape).
- **Horizontal** ([`head-cradle-horizontal.stl`](models/head-cradle-horizontal.stl), print 1) for the
  top rail or the crossbar. The connector edge is at the plate's free edge, the bottom when the head
  hangs under a rail, so the image's long side runs along the pipe.

**The ribbon slot is now the whole connector edge.** The plate stops 6.3 mm short of the board's
connector edge, so there is nothing behind the connector and the ribbon bends straight back past the
plate. The holes, standoffs (Ø5.2 × 3 mm), hinge disc, M4 hole and tilt pin hole are unchanged, so
both cradles fit the clamps already printed.

Checked in `build.py` against Raspberry Pi's model of the board:

- The nearest standoff is 0.98 mm from the connector.
- The only part of the connector over the plate is its 2.16 mm-high lower back, 0.84 mm clear of it.
- Neither cradle hits the clamp, the cap or the pipe at any of the seven tilt holes, with the board,
  lens and ribbon on.

The lens axis sits 9.5 mm in from the connector edge, level with the near pair of holes. The first
cradle had assumed it was 5 mm further in. With the corrected position and the new plates, the ground
lenses come out 372 mm above the plywood instead of 381 mm. Every coverage figure moves by less than
1 %.

### Parts

| Item | Layout 3 | Layout 4 |
|---|---|---|
| [`head-clamp.stl`](models/head-clamp.stl) | 3 | 3 |
| [`head-cradle-vertical.stl`](models/head-cradle-vertical.stl) (posts) | 2 | 2 |
| [`head-cradle-horizontal.stl`](models/head-cradle-horizontal.stl) (top camera) | 1 | 1 |
| [`clamp-cap.stl`](models/clamp-cap.stl) | 5 | 3 |
| [`ground-foot.stl`](models/ground-foot.stl) | 2 | 2 |
| [`cross-clamp.stl`](models/cross-clamp.stl) | 2 | none |
| ¾ in Sch 40 PVC: posts 400 mm | 2 | 2 |
| ¾ in Sch 40 PVC: crossbar 1290 mm (50¾ in, needs a new stick) | 1 | none |
| M3 × 16 + nut (clamp to cap) | 10 | 6 |
| M4 × 16 + nyloc nut (pivot); M2 × 12 + nut (tilt pin) | 3 each | 3 each |
| M2 × 6 self-tapping (camera board) | 12 | 12 |
| #6 × ½ in pan-head (pins into PVC) | 9 | 5 |
| #8 × ⅝ in flat-head wood screws (feet) | 8 | 8 |
| Camera Module 3 Wide | 3 | 3 |

**Printing:** PETG, 0.2 mm layers, 4 walls, 40 % infill. No part is bigger than 76 mm, so all of
them fit the A1 mini. The clamp and the cap print on their split faces and the cradles on their hinge
plate, none of them with supports. Only the cross clamp needs support, inside its crossbar sleeve.

### Installing layout 4

1. **Feet.** Set one foot in the front-right corner and one in the back-right corner, each with two
   edges flush with the plywood's edges. Drill ⅛ in pilots and drive four #8 × ⅝ in screws.
2. **Posts.** Push a 400 mm post into each socket, then pin it with a #6 screw through the socket's
   side hole.
3. **Heads.**
   - Plug the ribbon into the camera board first. Then screw the board to its cradle with the ribbon
     connector at the plate's open edge: vertical cradles for the posts, the horizontal cradle for
     the top camera. The ribbon bends straight back past that edge.
   - Bolt each cradle to its clamp with the M4.
   - Ground cameras: put the tilt pin in the hole two steps (30°) from the middle, on the side that
     tips the lens down.
4. **Ground heads.**
   - Clamp each head at the top of its post, flush with the top, aimed along the diagonal at the
     arm's base.
   - Tighten the two M3s, then pilot through the cap's side hole and drive the #6 pin.
5. **Top head.**
   - Clamp it at the middle of the wall-side top rail. Put the tilt pin in the middle hole.
   - Turn the head on the rail until the camera looks in and 65° below horizontal. The camera
     plate's face is then 25° from horizontal; a phone inclinometer on it works.
   - Pin it like the others.
6. **Check each view** with `rpicam-still -o view.jpg` against the small images under rendering 4.
   Then calibrate as in #24; the JSON poses are only the nominal ones from the CAD.

## Assumptions

- **Table:** the 48 × 48 in plywood and the cube are #38's as-built numbers, through
  `../camera-bar/build.py`. The legs, braces and the 30 in height are from the photo and only
  affect the pictures.
- **A1 mini, AMS lite, power strip and switch:** boxes and discs at their approximate sizes and
  places. Their placement only matters for what the cameras can see.
- **Reach:** the fingertip is 140 mm past the flange (`piper_fk.py`). The reach is sampled from
  1.5 million random joint sets and closed with a 20 mm grid. It ignores self-collision and anything
  on the table except the plywood.
- **Tilts:**
  - Ground cameras: the 15° index step that sees most of the work zone.
  - Top rail camera: the 5° step that does.
  - Both ground cameras' lenses are 372 mm above the plywood (400 mm post).
- **Camera board:** from Raspberry Pi's Camera Module 3 Wide drawing and STEP model: 25 × 23.9 mm,
  M2 holes 21 × 12.5 mm apart, ribbon connector on the back along one 25 mm edge, lens axis 9.5 mm
  in from that edge.
- **Not covered:**
  - The gripper camera and the HQ camera (#39), which these renderings don't place. The HQ camera's
    38 mm board would need its own cradle.
  - The shelf, the black rack, the box and the loose Pis in the photo.
- **Nothing has been printed, fitted or tested.** I didn't touch the arm or the Pis.
