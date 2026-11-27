# Bench readiness: what has to be true before registering and before counting

Status checked on 2026-11-27, from the repo record and a read-only check of the Pis
([`hardware-and-safety-check.md`](hardware-and-safety-check.md)). **None of the gates below is met
yet**, except where the status says so. Gate IDs: RA (before registering A), SF (safety), HW
(hardware), SW (software), PL (pilot), RB (before registering B). They are distinct from the
hypotheses (H1–H4) and from the hazard IDs in PR 23's JHA (H1–H15).

Owners are **suggestions**, from who has done similar work in this repo's threads. Nobody has
agreed to anything. Each gate is closed by committing its evidence (a photo, a measurement, a log
or a link) to the `cfg-1` record, or by a dated line in this file.

- **sgbaird**: PI.
- **jss265**: the main operator so far.
- **chris-policky**: built the enclosure and the v1 mock-up, wired the relay, and wrote #266.
- **`@claude`**: a run in this repo. It writes code, but it can't move the arm, print, or meet anyone.

## A. Before registering A (transfer reliability, E1 and E2)

The text is ready to register now. These gates make it unlikely that the first amendment comes
within days of registering.

| ID | Gate | Evidence | Suggested owner | Status |
|---|---|---|---|---|
| RA1 | All PI decisions D1–D16 made ([PROTOCOL.md §0](PROTOCOL.md#0-decisions-before-locking)), including D5 (*n* = 300 or 628 for carriers OL) and D6 (full or trimmed single-vial levels) | Commit | sgbaird | Open |
| RA2 | **Design freeze.** PR 272's dock blocks, `plate_0` pair, a deck strip with the real deck's 25 mm pitch, one carrier with its post, the finger inserts with pads, and a few dummy vials, printed once and test-fitted by hand. The carrier seats on the blocks, the inserts close on the post and on a vial, and the vial height (64.2 or 83 mm) is settled | Photos | chris-policky, jss265 | Not started: CAD only |
| RA3 | The shelf's design is fixed (two carrier nests and one vial pocket, each generously chamfered), and its place is inside the reachable J1 window | CAD or sketch | chris-policky | Not started |
| RA4 | The harness's interfaces are agreed: it runs on mpzy, its schedule generator and ledger, and its per-transfer CSV in the format of [`analysis/out/synthetic_transfers.csv`](analysis/out/synthetic_transfers.csv) | Design note | `@claude` drafts, jss265 reviews | Not started |
| RA5 | The registration's contributors are named, and public or embargoed is chosen (D16) | — | sgbaird | Open |

## B. Before the first counted trial

### Safety (PR 23)

| ID | Gate | Evidence | Suggested owner | Status |
|---|---|---|---|---|
| SF1 | PR 23 updated to the cell as it is (mpzy, the relay, the installed E-stop, the wrist camera, about 660 E2 resets), then reviewed. The JHA review team meets and signs; the College Health & Safety Officer reviews the SOP. PR 23's 15 open items are each closed or accepted with a reason | Signed JHA, closed items in `docs/safety/README.md` | sgbaird convenes, jss265 as the person who runs the arm, `@claude` drafts the update | Draft, unreviewed since 2026-10-13 |
| SF2 | E-stop tested per SOP §A.2 with the arm at rest: press, twist out, nothing powers up, START. Record whether it sits before or after the relay, and check anti-restart with the relay cycling | Video or log | jss265, chris-policky | Installed 10-26, no test recorded |
| SF3 | The SOP's measurement M1: transformer clearances (§A.1), the rule's written source, the zone taped. The dock, the shelf and the arm's reach are outside the zone | Photos with tape in frame | jss265, with gage-erickson for the rule | Not measured |
| SF4 | Arm base bolted and plywood fixed to the table, recorded | Photo | chris-policky | Unverified |
| SF5 | Teach-button cover and label fitted | Photo | jss265 | Unknown |
| SF6 | Every operator trained on the SOP and signed off, including one supervised E-stop press and restart | Sign-off table | each operator | Not started |
| SF7 | A list of who can start motion (`@claude` triggers, SSH to mpzy) | List | sgbaird | Not started |
| SF8 | The joint drivers' collision protection level read (a read-only query that needs its own explicit request) and, if AgileX allows, set above 0 | Log | jss265 with an `@claude` run | Never read |
| SF9 | The harness parks the arm before any planned power-off, never powers off a raised arm, refuses a unit unless the arm reads its rest pose, and ends each session with the arm at rest and the motors off | Test log | harness author | Harness doesn't exist |

### Hardware

| ID | Gate | Evidence | Suggested owner | Status |
|---|---|---|---|---|
| HW1 | Everything printed: 2 dock blocks, 2 `plate_0`, the deck strip, 2 carriers with posts, the finger inserts, 16 dummy vials plus spares, and the shelf. Silicone pads glued. Every part weighed. R1 and R2 measured (pocket clearance and chamfer; datum, pin spacing, pocket distance) | `cfg-1` record | chris-policky (prints through `@claude-print` or in person) | Not started |
| HW2 | Finger inserts fitted. The gripper homes and enables (motor 7) with them. Grip effort set and checked so a vial and the post are held without crushing (one grip overshot 1.0 to 5.9 N·m) | Log | jss265 | Not started |
| HW3 | Wrist Pi back online, powered from the arm side with its adapter, cable strain-relieved so J6 can't jam on it, HQ lens focused and locked | Photo, `rpicam-hello --list-cameras` | jss265 | Offline since 11-13; no answer on 11-27 |
| HW4 | Camera intrinsics and hand–eye calibration done. Tags (R3) on the dock blocks decode at the look pose in ≥ 99 % of 100 looks | Calibration files, look log | chris-policky (AprilTags), `@claude` for code | Not started |
| HW5 | The witness camera's view covers the dock and the pocket at the check (mpzy's front camera, or a dedicated one) | Still | jss265 | Unknown |
| HW6 | Payload weighed: gripper with inserts, the wrist camera assembly, a full carrier. Compared with AgileX's rating at the reach used | Masses | jss265 | Not started |
| HW7 | Layout: the dock, shelf and look pose reachable with J1 inside −20° … +60° and J6 inside its wiring window, with ≥ 15° margin at every taught pose; each carrier points at J1 | Joint margins | harness author | Not started |
| HW8 | J1's zero is stable: 20 relay power cycles from rest, every joint reading within ±0.2° of its rest value. Needs CAN up and an explicit request, but no motion | Log | jss265 with an `@claude` run | Not done; J1 re-zeroed 11-14 |
| HW9 | The arm's lender agrees to about 6,000 transfers and about 750 power cycles (one per reset, about 660 of them in E2, plus a power-up per session) | Message | sgbaird | Not asked |
| HW10 | Decide how the arm is shared with the auger-swap work (#42) during the campaign. Every swap of finger inserts and auger sleeves is a configuration change | Decision | sgbaird, jss265 | Open |

### Software

| ID | Gate | Evidence | Suggested owner | Status |
|---|---|---|---|---|
| SW1 | Trial harness on mpzy: schedule generator from the block seed and the ledger; OL and AT paths through the same look pose; contact stop (R8); aborts and timeouts; logging at ≥ 50 Hz; operator scoring; a witness still per check; the registered CSV. A 2-hour soak test with the livestream on and no dropped samples | Code, soak log | `@claude` writes, jss265 tests | Not started |
| SW2 | AprilTag correction: detection, pose estimation, x/y/yaw correction with its cap, and the abort that never falls back to open loop | Code, look log | chris-policky, `@claude` | Not started |
| SW3 | The analysis code runs on pilot data in the registered format | Output | `@claude` | Runs on synthetic data ([`out/recovery.md`](analysis/out/recovery.md)) |
| SW4 | Logs flow to D14's dataset; schedules, the ledger and the configuration records are committed | Links | harness author | Not started |

### Pilot

| ID | Gate | Evidence | Suggested owner | Status |
|---|---|---|---|---|
| PL1 | Pilot blocks set R1–R8; every value is written into `cfg-1` with its measurement | `cfg-1` | jss265 | Not started |
| PL2 | Positive control: 20 nominal OL carrier loads all succeed at the R5 speed | Log | jss265 | Not started |
| PL3 | The contact stop (R8) stops a +4 mm carrier place and a +4° place without damage, at the campaign speed | Video | jss265 | Not started |
| PL4 | Registration A approved on OSF, and its DOI written into PROTOCOL.md | DOI | sgbaird | Not registered |

## C. Before registering and running B (pose repeatability, E3)

| ID | Gate | Evidence | Suggested owner | Status |
|---|---|---|---|---|
| RB1 | A metrology fixture that reads the TCP's 3D position with *U* ≤ 0.025 mm (k = 2), for example three 0.001 mm digital indicators against a sphere or cube target, checked on a static target | Fixture photo, static-target log | not yet assigned | Doesn't exist |
| RB2 | Poses P1–P5 checked against ISO 9283 §6.8 (the corner inset and the order of visits). The free sample stops before §6.8, so someone needs the standard | Note | sgbaird (library copy) | Open |
| RB3 | The loaded payload (D9) made and weighed | Mass | chris-policky | Not started |
| RB4 | Gates SF1–SF9 and HW2, HW6–HW9 above (the same arm, the same safety rules) | — | — | — |

## Realistic dates

These assume the work above starts the week of 2026-11-30 and that little happens over BYU's
winter break (about 2026-12-19 to 2027-01-05).

| Milestone | Earliest | Realistic | What sets it |
|---|---|---|---|
| Register A | 2026-12-04, if RA1 is done and you accept amending after the parts are printed | **2027-01-29** | RA2: printing and test-fitting PR 272's parts |
| Register B | 2027-01-29 | **2027-02-19** | RB1: building the fixture |
| First counted block | 2027-02-12 | **2027-03-05** | SF1 (the safety review), SW1–SW2 (harness and correction), HW3–HW4 (wrist camera) |
| Campaign done (70–100 sessions, about 2 a weekday) | 2027-04-09 | **2027-05-14** | Operator time and resets |
| Results paper submitted | 2027-05-14 | **2027-06-25** | Analysis is scripted; writing and figures |
