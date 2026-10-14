# Where to add two fixed cameras (issue #24)

The wrist mount in #10 already carries two cameras on the gripper, so these two are fixed
cameras that fill in what the taped side camera can't see. `scripts/piper_camera_placement.py`
scores candidate spots with the digital twin (`scripts/piper_twin.py`) and renders their views:

    python scripts/piper_camera_placement.py --out docs/issue-24/camera-placement \
        --poses 400 --photo docs/issue-24/camera_2026-10-14.jpg --animate

## Recommendation

Arm base frame, mm: x is the way the arm points at J1 = 0 (along the wall, to the right as seen
from the room), y toward the wall, z up from the arm's plate.

| | A: overhead | B: right-hand end |
|---|---|---|
| Position | (0, -75, 1200): 1.2 m above the table's centre, 7.5 cm toward the room from J1 | (800, 100, 420): 80 cm from J1, past the table's right-hand end, 10 cm toward the wall, 42 cm up |
| Aim | Straight down at (0, -75, 0). Long side of the image along the wall, wall at the top | Back at (0, 150, 150), between J1 and the shelf. 19 deg down, image level |
| From J2 | 1.08 m, outside the fingertips' 0.76 m reach | 0.86 m, outside the reach |
| Camera files | [`camera_overhead.json`](camera_overhead.json) | [`camera_front-end.json`](camera_front-end.json) |

Both assume a Camera Module 3 Wide (102 x 67 deg). With the dome from #2 in place, A can hang
from its top rails at 1.1 m and still cover the whole table.

## Scores

400 arm poses with the fingertips over the table (random joint angles in the working range). A
camera "sees" the fingertips if they are in frame and no part of the arm is in the way. The
error is the RMS 3D error of the fingertips triangulated from every camera that sees them, for
1 px of image noise at 2304 x 1296 (`placement.json` has every pair).

| Cameras | Seen by 2+ | Seen by any | Median error | Within 2 mm |
|---|---|---|---|---|
| Taped camera only (today) | 0 % | 75.0 % | no depth | 0 % |
| + B (best single addition) | 66.8 % | 95.5 % | 1.11 mm | 66.2 % |
| + A | 53.2 % | 92.2 % | 1.39 mm | 52.0 % |
| + a second camera 42 cm above the taped one | 67.2 % | 80.8 % | 1.71 mm | 41.0 % |
| **+ A + B (recommended, 2nd of 45 pairs)** | **88.8 %** | **98.5 %** | **1.02 mm** | **88.2 %** |
| + wall-high + front-end-high (1st) | 89.5 % | 98.0 % | 1.10 mm | 88.5 % |
| + wall-high + B (3rd) | 88.5 % | 98.2 % | 0.95 mm | 88.0 % |
| + A + end-back-corner | 89.5 % | 98.8 % | 1.22 mm | 82.2 % |
| + door-end + the raised taped camera (45th) | 78.5 % | 98.0 % | 1.31 mm | 60.2 % |

The top pairs are within the noise of 400 poses of each other. What they share is a camera at
the end the arm faces, plus one high up. A wins over the wall camera for reasons the score
doesn't count: it sees the whole table (the "workspace clear" check before any motion), gives
positions on the table directly, and needs nothing fixed to the wall.

## Caveats

- The candidate cameras use nominal Camera Module 3 Wide intrinsics with no lens distortion.
  The taped camera is the rough 5-point fit from 2026-10-13.
- The table and wall come from #9's spot D model (table 1290 x 1360 mm, J1 606 mm from the
  wall). The shelf is not modelled: from 3 cm up the taped camera can't place it in depth, and
  in today's photo it looks taller than #9's 75 mm design.
- 1 px is optimistic for a real tracker (the synthetic test in #24 managed 2-4 px), so read the
  errors as relative.
- The renders and `views.mp4` are simulated; nothing here was recorded.
