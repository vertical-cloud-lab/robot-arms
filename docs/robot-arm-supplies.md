# Robot arm supplies: wishlist, orders and receipts

A running list of parts and supplies for the PiPER cell, started in
[#66](https://github.com/vertical-cloud-lab/robot-arms/issues/66). It uses the same layout as the
lab-wide list in byu-vcl
([`docs/lab-supplies.md`, PR #323](https://github.com/vertical-cloud-lab/byu-vcl/pull/323)): one ME
purchase request per online vendor, with the same fields as the form. The picks are in the order
tables, and the other options for each item are ranked under [Options](#options).

Every Amazon price, rating and seller was read off its product page on the evening of 2026-11-04,
Utah time (2026-11-05 UTC), sold by the brand and shipped by Amazon unless noted. Amazon blocks CI
IP ranges, so the pages were fetched through a camera Pi with the rate capped, as in
[PR #41](https://github.com/vertical-cloud-lab/robot-arms/pull/41). The searches and pages are in
[`robot-arm-supplies_shopping_2026-11-05.json`](robot-arm-supplies_shopping_2026-11-05.json).
calib.io and AndyMark prices are from their own store pages the same evening. All of them drift,
so check at checkout.

**Status: wishlist. Nothing ordered yet.** When an order is placed, add it to
[Receipts](#receipts).

## Fields shared by every order

| Field | Value |
| --- | --- |
| Project Name/Course Number | Vertical Cloud Lab (*confirm the name/account the lab uses on ME orders*) |
| Purpose | Per order, below |
| Physical Location(s) | PiPER cell, *lab room number: fill in* |
| Is this expense food? | No |

## Order 1: Amazon

Purpose: USB-C adapters for the power lead of the Raspberry Pi 5 on the PiPER's gripper: a
right-angle adapter at the Pi, so the cord no longer sticks out toward J2
([#54](https://github.com/vertical-cloud-lab/robot-arms/issues/54)), and a coupler for joining the
lead.

| Merchant Name | Item Description | Website link | Unit Cost | Qty | Asked for by |
| --- | --- | --- | ---: | ---: | --- |
| Amazon | AuviPal USB-C coupler, female to female (straight), 2-pack: 240 W, USB4 40 Gbps, aluminum shell, LED that lights when power is passing through. Sold by AuviPal | [B0CTT1FJL6](https://www.amazon.com/dp/B0CTT1FJL6) | $6.99 | 1 | jss265 |
| Amazon | Silkland 90° USB-C adapter, male to female, "Combo" 2-pack: one up/down bend and one sideways bend. 240 W, USB4 40 Gbps, about 18 × 13 × 5 mm. Sold by Silkland-US | [B0GWQ6S4BX](https://www.amazon.com/dp/B0GWQ6S4BX) | $11.99 | 1 | jss265 |
| | | | **$18.98** | | |

## Order 2: calib.io

Purpose: a ChArUco target (a checkerboard with fiducial markers in its white squares) for finding
where the PiPER cell's cameras sit in the arm's frame
([#24](https://github.com/vertical-cloud-lab/robot-arms/issues/24),
[PR #40](https://github.com/vertical-cloud-lab/robot-arms/pull/40)).

| Merchant Name | Item Description | Website link | Unit Cost | Qty | Asked for by |
| --- | --- | --- | ---: | ---: | --- |
| calib.io | ChArUco target, 300 × 200 mm, "Coarse" pattern: 9 × 14 squares of 20 mm, DICT_5X5 markers. Aluminium/LDPE composite (SKU CCT300200C). The board in DROID's shopping list | [calib.io](https://calib.io/products/charuco-targets?variant=9400454807599) | $138.00 + shipping | 1 | jss265 |

The cheap alternative is AndyMark's ChArUco board at $51.00 (rank 2 below). But #66 asked for
good reviews or a Hugging Face recommendation, and the AndyMark board has neither: its page has no
reviews, and neither Hugging Face nor DROID uses it.

## Options

### USB-C coupler, female to female

Every option is rated for 5 A and is a full-pin USB4 part (see the [notes](#notes-on-the-picks)
for why that matters).

| Rank | Item | Link | Price | Rating | Notes |
| ---: | --- | --- | ---: | --- | --- |
| 1 | AuviPal 240 W coupler, 2-pack | [B0CTT1FJL6](https://www.amazon.com/dp/B0CTT1FJL6) | $6.99 | 4.3★ (884) | Most ratings of any coupler; #19 in USB-to-USB Adapters. Its LED shows when the plugs are the right way round |
| 2 | ELUTENG 240 W coupler, 3-pack | [B0CSVGGLH9](https://www.amazon.com/dp/B0CSVGGLH9) | $6.99 | 4.6★ (249) | Best rating, but fewer ratings, and no LED. The title says 3-pack but the details table says 1 item, so check the count at checkout. Sold by ELUTENG Direct |
| 3 | Poyiccot 240 W coupler, 2-pack | [B0BRCMGJS3](https://www.amazon.com/dp/B0BRCMGJS3) | $7.59 | 4.4★ (682) | Has an LED. Its spec line says "max 5V/3A–20V/5A", which is still 5 A |
| 4 | Duttek 140 W coupler, 2-pack | [B0CWV1DGHJ](https://www.amazon.com/dp/B0CWV1DGHJ) | $7.53 | 4.3★ (402) | 140 W is 28 V × 5 A. The only one that says it works with the plugs either way round (unverified) |

### USB-C 90° adapter, male to female

Amazon pools ratings across a listing's variants, so the up/down and sideways versions of the
JSAUX and Silkland adapters show the same rating count.

| Rank | Item | Bend | Link | Price | Rating | Notes |
| ---: | --- | --- | --- | ---: | --- | --- |
| 1 | Silkland "Combo" 2-pack, 240 W | one of each | [B0GWQ6S4BX](https://www.amazon.com/dp/B0GWQ6S4BX) | $11.99 | 4.7★ (1,124) | The thinnest listed: 0.7 × 0.5 × 0.2 in (18 × 13 × 5 mm). Two of one bend: up/down [B0CNGFZ1JD](https://www.amazon.com/dp/B0CNGFZ1JD) or sideways [B0CNGJTKNK](https://www.amazon.com/dp/B0CNGJTKNK), $9.99 each |
| 2 | JSAUX "Right Angle" 2-pack, 240 W | up/down | [B0B77CJD7T](https://www.amazon.com/dp/B0B77CJD7T) | $8.99 | 4.7★ (2,902) | Most ratings; #43 in USB-to-USB Adapters. Sold by JS Digital US. The sideways one is "Flat Right Angle", [B0B77J7D1R](https://www.amazon.com/dp/B0B77J7D1R), $9.99, rated 100 W (20 V × 5 A) |
| 3 | UGREEN 3-pack, 240 W | up/down (all three, from the photo) | [B0FNCT8NS7](https://www.amazon.com/dp/B0FNCT8NS7) | $9.99 | 4.7★ (744) | 0.83 × 0.47 × 0.24 in (21 × 12 × 6 mm); the listing claims 10,000 plug cycles. Sold by UGREEN |
| 4 | AreMe 2-pack, 100 W | up/down | [B0B2NJ3P3L](https://www.amazon.com/dp/B0B2NJ3P3L) | $4.99 | 4.5★ (2,690) | Cheapest. 100 W is 20 V × 5 A, so still 5 A. 0.79 × 0.51 × 0.31 in (20 × 13 × 8 mm) |
| 5 | Adafruit 5521 magnetic right-angle adapter | — | [Adafruit](https://www.adafruit.com/product/5521) | $14.95 | — | Breaks away under a pull: a magnetic nub stays in the Pi, which protects its socket. PR #41 lists it as the breakaway option. Rated 120 W, but gives no current rating or pull-off force, so check it at 5 A before relying on it |

### Fiducial calibration board ("mat")

**Hugging Face doesn't recommend one.** LeRobot has no camera calibration: a code search of
`huggingface/lerobot` finds no ChArUco, ArUco or AprilTag. `lerobot-calibrate` covers the motors
only ([lerobot#4496](https://github.com/huggingface/lerobot/issues/4496)), and the
[SO-101 docs](https://huggingface.co/docs/lerobot/so101) stop at motor calibration. The nearest
thing is DROID. Its
[shopping list](https://github.com/droid-dataset/droid/blob/33ae6a6/docs/hardware-setup/shopping-list.md)
names calib.io's 300 × 200 ChArUco, and its
[calibration code](https://github.com/droid-dataset/droid/blob/33ae6a6/droid/misc/parameters.py#L17-L22)
hard-codes that pattern (9 × 14, 20 mm squares, DICT_5X5). Hugging Face hosts DROID as the LeRobot
dataset [`lerobot/droid_1.0.1`](https://huggingface.co/datasets/lerobot/droid_1.0.1). DROID
calibrates each camera with the board held in the gripper, the same step PR #40 plans for this cell.

**No calibration board on Amazon has reviews.** ChArUco boards there start at $171 with no ratings
([B0HL4CC3ML](https://www.amazon.com/dp/B0HL4CC3ML)). The rated "calibration" items are colour
charts, lens-test charts and car-camera grid cloths, not fiducial boards.

| Rank | Item | Link | Price | Backing | Notes |
| ---: | --- | --- | ---: | --- | --- |
| 1 | calib.io ChArUco target, 300 × 200 mm, Coarse (9 × 14 squares of 20 mm, DICT_5X5), Aluminium/LDPE composite | [calib.io](https://calib.io/products/charuco-targets?variant=9400454807599) | $138 + shipping | DROID's board (it was $114 when DROID listed it). PhotonVision's docs also point to calib.io's ChArUco targets | Stiff enough to hold in the gripper; 400 g shipping weight. calib.io is in Denmark: in-stock targets ship in 1–2 business days, otherwise they're made to order in about 10. US import duties are paid at checkout |
| 2 | AndyMark ChArUco Calibration Board (am-5750), 11 × 8.5 in (279 × 216 mm), dye-sublimated on 0.040 in (1 mm) aluminum, matte. The pattern's specs are printed on the board | [AndyMark](https://andymark.com/products/am-calibration-board) | $51.00 | None: no reviews on its page. Sold for FRC's Limelight and PhotonVision cameras | The cheap one, in stock in the US. It flexes: on [Chief Delphi](https://www.chiefdelphi.com/t/diy-charuco-calibration-target/523384) (Aug 2026), 1/4 in polycarbonate is estimated at 7× stiffer, and one team got 0.8 px with a phone screen against 1.2 px with this board, at 1080p. Fine taped flat to the table, worse in the gripper |
| 3 | calib.io ChArUco target, 400 × 300 mm, Coarse (9 × 12 squares of 30 mm) | [calib.io](https://calib.io/products/charuco-targets) | $154 + shipping | As rank 1 | For a board that lives flat on the table as a mat for the fixed cameras across the table: the larger squares are easier to detect from there. 900 g shipping weight, heavy for the gripper |
| 4 | Print your own from calib.io's free [pattern generator](https://calib.io/pages/camera-calibration-pattern-generator) or OpenCV, on something flat and rigid | — | about $0–45 | [PhotonVision's calibration docs](https://docs.photonvision.org/en/latest/docs/calibration/calibration.html) describe this route | Print at 100 % scale, measure the squares with calipers, and use the measured size. Keep it completely flat. The Chief Delphi build used sticker paper ($6), laminating pouches ($10) and a 6 mm ACM panel from SendCutSend (about $30) |

## Notes on the picks

- **Both adapters go in the wrist Pi's 5 V line.** The Pi 5 runs off Raspberry Pi's 27 W supply,
  which offers 5.1 V at 5 A over USB-PD, through a 5 A USB-C extension (PR #41's plan). Everything in the two
  adapter tables is rated for 5 A (100–240 W) and passes all 24 pins, so the supply's offer reaches
  the Pi. Skip anything rated 60 W (3 A) or sold as "charging only" or USB 2.0.
- **After fitting them, run PR #41's check on the Pi.**
  `od -An -tu4 --endian=big /proc/device-tree/chosen/power/max_current` should print `5000`
  (`3000` means the PD offer was lost on the way). Then read `vcgencmd pmic_read_adc EXT5V_V` and
  `vcgencmd get_throttled` with both cameras streaming. Each adapter adds another plug-and-socket
  joint, so the Pi sees slightly less voltage than through the extension alone.
- **A coupler may only work with its plugs one way round.** A USB-C cable carries its CC (PD
  signalling) line on one wire. In a straight female-to-female coupler, two cables' CC wires only
  meet in half of the plug orientations. Otherwise the supply never sees the Pi and leaves the
  power off. AuviPal, Poyiccot and ELUTENG all say to flip one plug if nothing happens, and the
  LED on the first two shows when it's right. Once it works, tape or sleeve the joint so it can't
  come apart or get flipped on the arm. Nothing checks what the coupler joins, so only join 5 A
  (240 W) cables with it, such as PR #41's AINOPE extension.
- **Pick the bend for where the cord should go.** The Pi 5's USB-C socket lies flat at the board's
  edge:
  - An up/down adapter turns the cord square to the board, above or below it.
  - A sideways one keeps the cord in the board's plane, running along the edge.

  Plugging either one in upside down turns the cord the opposite way (up or down, left or right),
  so one part covers two directions. If it isn't clear which the gripper needs, the Silkland combo
  has one of each.
- **A right-angle plug is what PR #41's power README asks for** at the Pi. It shortens the lever a
  sideways pull on the cord acts through. The lead still needs clamping to the carrier near the
  plug, so a yank loads the printed part and not the Pi's socket.
- **"Mat" or board.** The bought targets are rigid boards, not roll-up mats. A rigid board works
  lying on the table as a mat, and it can also be held in the gripper. A flexible printed mat is
  the one thing to avoid, since calibration assumes the pattern is perfectly flat.

## Receipts

| Date ordered | Vendor | Order # | Items | Total | Receipt | Received |
| --- | --- | --- | --- | ---: | --- | --- |
| | | | | | | |
