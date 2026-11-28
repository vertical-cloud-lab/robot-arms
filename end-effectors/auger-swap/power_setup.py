"""Graphics of the wrist power idea for the Strategy 1 tool (issue #42, PR #44): the Pi 5 runs
off J6's XT30 (2+2) port, as answered in PR #44 on 2026-10-30.

    xvfb-run -a python power_setup.py          # -> renders/power_wiring.png, renders/power_on_tool.png

The chain: an XT30 (2+2) pigtail using only the + and - pins (CAN-H/L left unconnected, since
AgileX reserves the end CAN for its own devices) -> a <=2 A fuse -> a 47-100 uF 50 V
electrolytic across the 24 V -> a Pololu D36V28F5 (24 -> 5 V, 3.2 A, 3.3 g) -> two short
22 AWG leads to the Pi's header pins 4 (5 V) and 6 (GND). The servos' 24 -> 12 V buck
(Pololu D36V50F12) runs off the same 24 V in parallel, not in series with the Pi's.

The 3D view is a sketch on top of s1_tool.py's parts: it swaps the modelled D36V50F5 for the
D36V50F12 (same 25.4 mm board, same spot) and adds the D36V28F5, fuse, capacitor and leads.
s1_tool.py itself, its STEP file and its mass table are unchanged. AgileX's URDF does not
model J6's XT30 port, so the pigtail is drawn loose rather than at a guessed position.
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
OUT = HERE / "renders"

# wire colours, shared by both graphics (CAN as AgileX's own cable: yellow H, blue L)
V24, V12, V5, GND = "#d62728", "#ff7f0e", "#c2188f", "#1a1a1a"
CANH, CANL, DATA = "#e3b505", "#1f77b4", "#8c8c8c"
PCB_GREEN, PCB_BLUE, PCB_POLOLU, XT30_YEL = "#0b7336", "#1a3f8c", "#3c8d40", "#f2c12e"

D36V28F5 = dict(w=17.8, h=20.3, t=8.8, g=3.3)       # Pololu 3782: 0.7 x 0.8 x 0.345 in, 3.3 g
D36V50 = dict(w=25.4, h=25.4)                         # Pololu 4095 / 4091: 1 x 1 in


# ============================================================================ wiring diagram
def wiring(path: Path = OUT / "power_wiring.png"):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.patches import Circle, FancyBboxPatch, Rectangle

    fig = plt.figure(figsize=(16, 9.4), dpi=110)
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_xlim(0, 160)
    ax.set_ylim(0, 94)
    ax.set_aspect("equal")
    ax.axis("off")
    fs = 13.5

    def block(x0, y0, w, h, fc, title, sub=None, tc="white", r=1.2, fsz=fs):
        ax.add_patch(FancyBboxPatch((x0, y0), w, h, boxstyle=f"round,pad=0,rounding_size={r}",
                                    fc=fc, ec="#333333", lw=1.2, zorder=3))
        ax.text(x0 + w / 2, y0 + h - 2.4, title, ha="center", va="top", color=tc, fontsize=fsz,
                fontweight="bold", zorder=4)
        if sub:
            ax.text(x0 + w / 2, y0 + h - 6.4, sub, ha="center", va="top", color=tc, fontsize=fsz - 2,
                    zorder=4, linespacing=1.25)

    def wire(pts, c, lw=3.2, ls="-", z=2):
        p = np.array(pts, float)
        ax.plot(p[:, 0], p[:, 1], color=c, lw=lw, ls=ls, solid_capstyle="round", zorder=z)

    def dot(x, y, c):
        ax.add_patch(Circle((x, y), 0.75, fc=c, ec=c, zorder=5))

    def note(x, y, s, ha="left", c="#333333", size=fs - 1.5, va="center", **kw):
        ax.text(x, y, s, ha=ha, va=va, color=c, fontsize=size, zorder=6, linespacing=1.3, **kw)

    ax.text(2, 91.5, "Powering the Pi 5 from J6's XT30 (Strategy 1 tool)", fontsize=18, fontweight="bold",
            va="top")
    ax.text(2, 86.6, "Both bucks run straight off the 24 V, in parallel, so a stalled servo can't pull "
            "the Pi's 5 V down.", fontsize=fs, va="top", color="#444444")

    # ---- J6 port face, as drawn in the PiPER manual §2.9 (key on the left) -------------------
    fx, fy = 8.0, 40.0
    ax.add_patch(Rectangle((fx, fy), 10, 25, fc="#2b2b2b", ec="black", lw=1.2, zorder=3))
    ax.add_patch(Rectangle((fx - 3, fy + 8), 3, 12, fc="#2b2b2b", ec="black", lw=1.2, zorder=3))
    pins = {"+": (fx + 5, fy + 19.5, 3.0, V24), "-": (fx + 5, fy + 11.5, 3.0, GND),
            "H": (fx + 3, fy + 4.0, 1.4, CANH), "L": (fx + 7, fy + 4.0, 1.4, CANL)}
    for k, (x, y, r, c) in pins.items():
        ax.add_patch(Circle((x, y), r, fc="#d9b44a", ec=c, lw=2.6, zorder=4))
        ax.add_patch(Circle((x, y), r * 0.45, fc="#2b2b2b", ec="none", zorder=5))
    note(fx - 3.5, fy + 19.5, "+", ha="right", size=15, c=V24, fontweight="bold")
    note(fx - 3.5, fy + 11.5, "−", ha="right", size=15, c=GND, fontweight="bold")
    note(fx + 3, fy - 2.2, "H", ha="center", size=12, c="#7a5c00", fontweight="bold")
    note(fx + 7, fy - 2.2, "L", ha="center", size=12, c=CANL, fontweight="bold")
    note(fx + 5, fy + 31.5, "J6 end port\nXT30 (2+2), J6 side\n24 V, 2 A max", ha="center",
         size=fs - 1, fontweight="bold")

    # ---- pigtail plug (yellow Amass), wires out to the right -------------------------------
    px0 = fx + 13.0
    ax.add_patch(FancyBboxPatch((px0, fy + 1), 7, 23, boxstyle="round,pad=0,rounding_size=0.8",
                                fc=XT30_YEL, ec="#7a5c00", lw=1.2, zorder=3))
    note(px0 + 3.5, fy + 12.5, "XT30 (2+2)\nplug", ha="center", size=fs - 3, rotation=90)
    yP, yN = fy + 19.5, fy + 11.5
    wire([(fx + 5, yP), (px0, yP)], V24, lw=2)
    wire([(fx + 5, yN), (px0, yN)], GND, lw=2)
    # CAN pins: short stubs, cut back and insulated
    for y, c in ((fy + 4.6, CANH), (fy + 2.6, CANL)):
        wire([(px0 + 7, y), (px0 + 12, y)], c, lw=2.4)
        ax.plot([px0 + 12.2], [y], marker="x", ms=8, mew=2.4, color="#555555", zorder=6)
    note(px0 + 14, fy + 3.6, "CAN-H/L not connected\n(AgileX reserves the end CAN)", size=fs - 2.5,
         c="#555555")

    # ---- fuse, capacitor, split -----------------------------------------------------------
    x = px0 + 7
    wire([(x, yP), (x + 6, yP)], V24)
    ax.add_patch(Rectangle((x + 6, yP - 1.4), 7, 2.8, fc="white", ec=V24, lw=2.2, zorder=4))
    wire([(x + 6, yP), (x + 13, yP)], V24, lw=1.2, z=5)
    note(x + 9.5, yP + 3.6, "≤2 A fuse", ha="center", size=fs - 1, fontweight="bold")
    note(x + 9.5, yP + 7.0, "pigtail: + and − only", ha="center", size=fs - 2.5, c="#555555")
    xs = 63.0                                  # split column
    wire([(x + 13, yP), (xs, yP)], V24)
    wire([(x, yN), (xs, yN)], GND)
    # polarised electrolytic between the rails
    xc = 46.0
    ym = (yP + yN) / 2
    wire([(xc, yP), (xc, ym + 0.8)], V24, lw=2.2)
    wire([(xc, yN), (xc, ym - 1.4)], GND, lw=2.2)
    ax.plot([xc - 2.2, xc + 2.2], [ym + 0.8, ym + 0.8], color="#333333", lw=2.6, zorder=4)
    t = np.linspace(-1, 1, 30)
    ax.plot(xc + 2.2 * t, ym - 0.4 - 0.9 * (1 - t ** 2), color="#333333", lw=2.6, zorder=4)
    note(xc - 2.4, ym + 2.0, "+", ha="right", size=12, c="#333333")
    dot(xc, yP, V24)
    dot(xc, yN, GND)
    note(xc + 2.8, ym - 0.2, "47–100 µF\n50 V, ≈1 g", size=fs - 2.5)

    # ---- Pi branch (top) --------------------------------------------------------------------
    yA = 70.0
    bx, bw = 71.0, 21.0
    wire([(xs, yP), (xs, yA + 3.5), (bx, yA + 3.5)], V24)
    wire([(xs + 2.5, yN), (xs + 2.5, yA - 3.5), (bx, yA - 3.5)], GND)
    dot(xs, yP, V24)
    block(bx, yA - 10, bw, 19, PCB_POLOLU, "Pololu D36V28F5", "24 → 5 V, 3.2 A\n3.3 g, 18 × 20 mm\nEN, PG left open")
    note(bx - 0.6, yA + 3.5, "VIN", ha="right", size=fs - 3.5, va="bottom")
    note(bx - 0.6, yA - 3.5, "GND", ha="right", size=fs - 3.5, va="bottom")
    # Pi 5 with its header (pins 1..12 drawn, 2.54 mm pitch as 3 units)
    pix, piy, piw, pih = 104.0, 53.0, 40.0, 29.0
    block(pix, piy, piw, pih, PCB_GREEN, "Raspberry Pi 5", None)
    hx0, hy0, pitch = pix + 6.0, piy + pih - 14.0, 3.0
    ax.add_patch(Rectangle((hx0 - 2.0, hy0 - 2.0), 6 * pitch + 1.0, pitch + 4.0, fc="#111111", ec="none", zorder=4))
    for k in range(12):
        n = k + 1
        col = (k // 2) * pitch
        row = 0 if n % 2 == 1 else pitch      # odd pins inner row, even pins outer (board edge)
        c = "#b8b8b8"
        if n == 2:
            c = "#e6a8cf"
        if n == 4:
            c = V5
        if n == 6:
            c = "#5a5a5a"
        ax.add_patch(Rectangle((hx0 + col - 0.7, hy0 + row - 0.7), 1.4, 1.4, fc=c, ec="none", zorder=5))
    note(hx0 - 2.6, hy0, "1", ha="right", size=fs - 4, c="white")
    note(hx0 - 2.6, hy0 + pitch, "2", ha="right", size=fs - 4, c="white")
    p4 = (hx0 + 1 * pitch, hy0 + pitch)
    p6 = (hx0 + 2 * pitch, hy0 + pitch)
    # leads: VOUT -> pin 4, GND -> pin 6, entering from the board edge
    ex = bx + bw
    wire([(ex, yA + 3.5), (ex + 6, yA + 3.5), (ex + 6, piy + pih + 6.0), (p4[0], piy + pih + 6.0), p4], V5, z=6)
    wire([(ex, yA - 3.5), (ex + 9, yA - 3.5), (ex + 9, piy + pih + 3.0), (p6[0], piy + pih + 3.0), p6], GND, z=6)
    ax.add_patch(Circle(p4, 0.9, fc=V5, ec="white", lw=1.2, zorder=7))
    ax.add_patch(Circle(p6, 0.9, fc=GND, ec="white", lw=1.6, zorder=7))
    note(ex + 0.6, yA + 3.5, "VOUT", size=fs - 3.5, va="bottom")
    note(ex + 0.6, yA - 3.5, "GND", size=fs - 3.5, va="bottom")
    note(p6[0] + 3.0, piy + pih + 4.6, "2 short 22 AWG leads,\n1×2 Dupont on pins 4 + 6", size=fs - 2.5)
    note(hx0 + 6 * pitch + 1.0, hy0 + pitch, "pin 4: 5 V", size=fs - 2, c="white", fontweight="bold")
    note(hx0 + 6 * pitch + 1.0, hy0 - 0.2, "pin 6: GND", size=fs - 2, c="white", fontweight="bold")
    note(pix + piw / 2, piy + 4.0, "+ Active Cooler + 2 cameras ≈ 7 W\n≈ 0.3 A from J6 (≈ 0.6 A flat out)",
         ha="center", size=fs - 2.5, c="white")
    # cameras (data only)
    for i, (nm, y) in enumerate((("HQ Camera\n+ 6 mm lens", 73.0), ("Camera Module\n3 Wide", 58.0))):
        cx = 148.0
        block(cx, y, 11.5, 11.0, "#5a5a5a", "", None)
        note(cx + 5.75, y + 5.5, nm, ha="center", size=fs - 4, c="white")
        wire([(pix + piw, y + 5.5), (cx, y + 5.5)], DATA, lw=2.2, ls=(0, (3, 2)))
    note(145.0, 87.0, "CSI ribbons", ha="center", size=fs - 3.5, c="#666666")

    # ---- servo branch (bottom) ---------------------------------------------------------------
    yB = 24.0
    wire([(xs, yP), (xs, yB + 3.5), (bx, yB + 3.5)], V24)
    wire([(xs + 2.5, yN), (xs + 2.5, yB - 3.5), (bx, yB - 3.5)], GND)
    dot(xs + 2.5, yN, GND)
    block(bx, yB - 10, bw, 19, PCB_POLOLU, "Pololu D36V50F12", "24 → 12 V, 4.5 A\n25 × 25 mm\n(servos only)")
    ax2 = 98.0
    wire([(bx + bw, yB + 3.5), (ax2, yB + 3.5)], V12)
    wire([(bx + bw, yB - 3.5), (ax2, yB - 3.5)], GND)
    note((bx + bw + ax2) / 2, yB + 4.0, "12 V", ha="center", size=fs - 3, va="bottom", c=V12, fontweight="bold")
    block(ax2, yB - 10, 26, 19, PCB_BLUE, "Waveshare Bus", "Servo Adapter (A)\n12 V in, USB-C to the Pi")
    # USB from the Pi
    wire([(pix + 10, piy), (pix + 10, yB + 9)], DATA, lw=2.2, ls=(0, (3, 2)))
    note(pix + 11, (piy + yB + 9) / 2, "USB (data)", size=fs - 3.5, c="#666666")
    # servo bus: 12 V + GND + signal, daisy-chained
    sx = 130.0
    ly0, ly1 = yB - 5.5, 5.0                   # lift and hook servo boxes (bottom y)
    for i, (nm, y) in enumerate((("STS3215-C018\nlift", ly0), ("STS3215-C018\nhook", ly1))):
        block(sx, y, 18, 11, "#2647b8", "", None)
        note(sx + 9, y + 5.5, nm, ha="center", size=fs - 3, c="white", fontweight="bold")
    for dy, c, lw in ((7.0, V12, 2.0), (5.5, DATA, 1.6), (4.0, GND, 2.0)):
        wire([(ax2 + 26, ly0 + dy), (sx, ly0 + dy)], c, lw=lw)
        wire([(sx + 18, ly0 + dy), (sx + 21 + (7 - dy), ly0 + dy), (sx + 21 + (7 - dy), ly1 + dy), (sx + 18, ly1 + dy)], c, lw=lw)
    note(sx + 9, ly0 + 13.5, "3-wire bus: 12 V, GND, data", ha="center", size=fs - 3.5, c="#666666")
    note(ax2 + 13, yB - 13.0, "cap the torque (lift 60 %, hook 40 %)\nso stalls stay under J6's 2 A",
         ha="center", size=fs - 3, c="#444444")

    # ---- legend --------------------------------------------------------------------------
    lx, ly = 2.0, 18.0
    for i, (c, s, ls) in enumerate(((V24, "+24 V from J6", "-"), (V5, "+5 V to the Pi", "-"), (V12, "+12 V to the servos", "-"),
                                    (GND, "GND (one common ground)", "-"), (DATA, "data only", (0, (3, 2))))):
        y = ly - i * 3.4
        ax.plot([lx, lx + 5], [y, y], color=c, lw=3, ls=ls)
        note(lx + 6.5, y, s, size=fs - 2.5)

    OUT.mkdir(exist_ok=True)
    fig.savefig(path, dpi=110, facecolor="white")
    plt.close(fig)
    print("->", path.relative_to(HERE))


# ============================================================================ 3D sketch on the S1 tool
# Frame E (s1_tool.py): origin on the J6 flange face, +z toward the arm, the tool hangs below.
# The deck's arm-side face is z = -10.5; the Pi 5 stands on the +X side (board face x = 50).
DECK_TOP = -10.5
P28 = (22.0, 26.0)                       # D36V28F5 corner on the deck's +X/+Y corner (pins on its +Y edge)
PLUG = np.array([0.0, 44.0, 30.0])       # pigtail plug, loose (J6's port position is not in the URDF)


def _hex(c):
    c = c.lstrip("#")
    return tuple(int(c[i:i + 2], 16) / 255 for i in (0, 2, 4))


def _pale(rgb, k=0.55):
    return tuple(v + (1 - v) * k for v in rgb)


def _pi_pin(n: int) -> np.ndarray:
    """Tip of Pi 5 header pin n in E (pin 1 at u 8.37, odd pins inner row, 2.54 pitch)."""
    import s1_tool as S1
    u = 8.37 + 2.54 * ((n - 1) // 2)
    v = 51.23 if n % 2 else 53.77
    return (S1._pi_frame() @ np.array([u, v, 1.6 + 8.5, 1.0]))[:3]


def _power_parts():
    """New parts as (name, Workplane in E, rgb)."""
    import s1_tool as S1
    out = []
    # D36V28F5 on the deck, pins along its +Y edge
    w, h = D36V28F5["w"], D36V28F5["h"]
    b = S1.box(0, w, 0, h, 0, 1.6)
    for u in (2.2, w - 2.2):
        b = b.cut(S1.cyl_z(2.18, -1, 3, u, 2.2))
    comps = [S1.box(4.0, 13.8, 5.0, 13.0, 1.6, 6.8), S1.box(1.5, 4.5, 9.0, 15.0, 1.6, 3.2),
             S1.box(13.5, 16.3, 7.0, 13.0, 1.6, 3.6)]
    comps += [S1.box(2.0 + 2.54 * k, 2.64 + 2.54 * k, h - 1.6, h - 0.96, -1.0, 3.0) for k in range(5)]
    out.append(("Pololu D36V28F5 (24 -> 5 V)", S1.union_all([b] + comps).translate((P28[0], P28[1], DECK_TOP + 0.2)),
                _hex(PCB_POLOLU)))
    # D36V50F12 where the CAD has the D36V50F5 (same 25.4 mm board)
    out.append(("Pololu D36V50F12 (24 -> 12 V)", S1.place(S1.buck_local(), S1.T((-58.0, 12.0, DECK_TOP + 0.2))),
                _hex(PCB_POLOLU)))
    # electrolytic, standing on the deck by the splice
    cap = S1.cyl_z(6.3, DECK_TOP, DECK_TOP + 11.0, 12.0, 40.5)
    out.append(("47 uF 50 V electrolytic", cap, (0.10, 0.18, 0.45)))
    out.append(("cap top", S1.cyl_z(6.0, DECK_TOP + 11.0, DECK_TOP + 11.3, 12.0, 40.5), (0.75, 0.75, 0.78)))
    # inline fuse under heat-shrink on the + lead
    out.append(("fuse", S1.cyl_z(5.5, 6.0, 22.0, PLUG[0] - 2.0, PLUG[1]), (0.30, 0.30, 0.32)))
    # XT30 (2+2) plug
    plug = S1.box(-5.2, 5.2, -7.9, 7.9, 0.0, 16.0).translate(tuple(PLUG))
    out.append(("XT30 (2+2) plug", plug, _hex(XT30_YEL)))
    # 1 x 2 Dupont housing on pins 4 + 6 (outer row, 2.54 apart along u)
    p4, p6 = _pi_pin(4), _pi_pin(6)
    c = (p4 + p6) / 2
    hous = S1.box(c[0] - 6.0, c[0] + 8.0, c[1] - 1.27, c[1] + 1.27, c[2] - 2.54, c[2] + 2.54)
    out.append(("Dupont 1x2 housing on pins 4 + 6", hous, (0.08, 0.08, 0.09)))
    return out


def _routes():
    """Lead paths in E as (colour, radius, points)."""
    p4, p6 = _pi_pin(4), _pi_pin(6)
    zt = DECK_TOP + 1.0                       # leads lie on the deck
    x0 = P28[0]
    vin = np.array([x0 + 2.3 + 2.54 * 1, P28[1] + D36V28F5["h"] - 1.3, DECK_TOP + 0.2])
    gnd = np.array([x0 + 2.3 + 2.54 * 2, P28[1] + D36V28F5["h"] - 1.3, DECK_TOP + 0.2])
    vout = np.array([x0 + 2.3 + 2.54 * 4, P28[1] + D36V28F5["h"] - 1.3, DECK_TOP + 0.2])
    gnd2 = np.array([x0 + 2.3 + 2.54 * 3, P28[1] + D36V28F5["h"] - 1.3, DECK_TOP + 0.2])
    f12_in, f12_g = np.array([-50.0, 36.6, DECK_TOP + 3.2]), np.array([-46.0, 36.6, DECK_TOP + 3.2])
    f12_o, f12_og = np.array([-38.0, 36.6, DECK_TOP + 3.2]), np.array([-42.0, 36.6, DECK_TOP + 3.2])
    jack = np.array([-52.0, -4.0, -64.5])
    r = 0.8
    sp = np.array([12.0, 44.5, zt])           # splice by the cap
    plus = [PLUG + (-2.0, 0, 0), PLUG + (-2.0, 0, -8.0), (PLUG[0] - 2.0, PLUG[1], 2.0), (2.0, 44.5, zt + 1.5), sp]
    minus = [PLUG + (2.0, 0, 0), PLUG + (2.5, 0, -14.0), (6.0, 47.5, zt + 1.0), sp + (0, 3.0, 0)]
    return [
        (V24, r, plus),
        (GND, r, minus),
        # + to both bucks
        (V24, r, [sp, (vin[0] - 4, sp[1] - 0.5, zt), (vin[0], vin[1] + 0.5, zt), vin + (0, 0, 2.0)]),
        (V24, r, [sp, (-10.0, 44.5, zt), (-40.0, 42.0, zt), (f12_in[0], 39.0, zt + 1.0), f12_in + (0, 0.5, 0.5)]),
        (GND, r, [sp + (0, 3.0, 0), (gnd[0] - 2, 48.0, zt), (gnd[0], gnd[1] + 1.5, zt), gnd + (0, 0, 2.0)]),
        (GND, r, [sp + (0, 3.0, 0), (-10.0, 47.5, zt), (-40.0, 45.0, zt), (f12_g[0], 40.0, zt + 1.0), f12_g + (0, 0.5, 0.5)]),
        # 5 V leads, over the deck's +X edge onto pins 4 and 6
        (V5, r, [vout + (0, 0, 2.0), (vout[0] + 2, vout[1] + 2.5, zt), (44.0, 48.0, zt), (58.0, 48.5, -12.0),
                 (p4[0] + 9.5, p4[1] + 0.8, p4[2] + 6.0), (p4[0] + 8.0, p4[1], p4[2])]),
        (GND, r, [gnd2 + (0, 0, 2.0), (gnd2[0] + 2, gnd2[1] + 1.5, zt), (44.0, 46.0, zt), (56.0, 46.0, -14.0),
                  (p6[0] + 10.5, p6[1] - 0.8, p6[2] + 4.0), (p6[0] + 8.0, p6[1], p6[2])]),
        # 12 V leads down the -X side to the bus adapter's DC jack
        (V12, r, [f12_o + (0, 0.5, 0.5), (-38.0, 41.0, zt), (-63.5, 41.0, zt - 2.0), (-64.5, 30.0, -36.0),
                  (-63.0, 4.0, -58.0), (-55.0, -3.0, -67.0), jack + (0, 1.0, -1.5)]),
        (GND, r, [f12_og + (0, 0.5, 0.5), (-42.0, 43.0, zt), (-65.5, 43.0, zt - 2.0), (-66.5, 31.0, -38.0),
                  (-65.0, 2.0, -60.0), (-56.0, -6.0, -68.5), jack + (0, -1.5, -1.5)]),
    ]


def on_tool():
    import pyvista as pv
    import vtk
    from PIL import Image, ImageDraw, ImageFont
    import s1_tool as S1

    def _pv(shape, tol):
        v, f = shape.tessellate(tol, 0.2)
        v = np.array([(q.x, q.y, q.z) for q in v])
        return pv.PolyData(v, np.hstack([np.full((len(f), 1), 3), np.array(f)]).ravel())

    power_names = ("Raspberry Pi 5", "Waveshare Bus Servo Adapter")
    items = []
    for n, wp, c, M, grp in S1.posed_parts(S1.STROKE, 0.0, E=np.eye(4)):
        if "D36V50F5" in n:
            continue                                   # swapped for the D36V50F12 below
        shape = S1.solid_of(wp).moved(S1.loc(M))
        col = c if any(k in n for k in power_names) else _pale(c, 0.55)
        items.append((n, _pv(shape, 0.12), col))
    for n, wp, c in _power_parts():
        items.append((n, _pv(S1.solid_of(wp), 0.05), c))
    tubes = []
    for c, r, pts in _routes():
        line = pv.Spline(np.array(pts, float), 120)
        tubes.append((line.tube(radius=r, n_sides=14), _hex(c)))

    p4 = _pi_pin(4)
    anchors = {
        "plug": (PLUG + (0, 0, 16.0), "XT30 (2+2) pigtail, + and − only,\nto J6's port (drawn loose)"),
        "fuse": (np.array([PLUG[0] - 2.0, PLUG[1], 14.0]), "≤2 A fuse, inline"),
        "cap": (np.array([12.0, 40.5, DECK_TOP + 11.0]), "47–100 µF 50 V"),
        "f5": (np.array([P28[0] + 9, P28[1] + 10, DECK_TOP + 7.0]), "Pololu D36V28F5\n24 → 5 V, 3.3 g"),
        "f12": (np.array([-45.3, 24.7, DECK_TOP + 8.0]), "Pololu D36V50F12\n24 → 12 V (servos),\nin the D36V50F5's spot"),
        "pins": (p4 + (6.0, 0, 0), "pins 4 (5 V) + 6 (GND)\n1×2 Dupont"),
        "pi": (np.array([62.0, 20.0, -60.0]), "Raspberry Pi 5"),
        "jack": (np.array([-52.0, -4.0, -64.0]), "12 V into the bus\nservo adapter"),
    }
    def cam(target, off, k):
        t = np.array(target, float)
        return [tuple(t + k * np.array(off, float)), tuple(t), (0, 0, 1)]
    views = [
        ("from above (arm side): the deck", cam((2, 15, -42), (170, 200, 215), 1.22),
         ("plug", "fuse", "cap", "f5", "f12", "pins", "pi")),
        ("+X side: the 5 V leads to the Pi", cam((40, 25, -32), (190, 115, 55), 1.55),
         ("f5", "cap", "pins", "pi")),
        ("−X side: 12 V down to the servo adapter", cam((-40, 12, -40), (-200, 160, 95), 1.28),
         ("f12", "jack")),
    ]
    font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 15)
    fontb = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 17)
    tiles = []
    W, H = 660, 620
    for title, cam, keys in views:
        p = pv.Plotter(off_screen=True, window_size=(W, H))
        p.set_background("white")
        p.enable_anti_aliasing("fxaa")
        for n, m, c in items:
            p.add_mesh(m, color=c, smooth_shading=False)
        for m, c in tubes:
            p.add_mesh(m, color=c, smooth_shading=True)
        p.camera_position = cam
        p.camera.view_angle = 30
        p.render()
        im = Image.fromarray(p.screenshot(return_img=True))
        coord = vtk.vtkCoordinate()
        coord.SetCoordinateSystemToWorld()
        pts = {}
        for k in keys:
            coord.SetValue(*anchors[k][0])
            x, y = coord.GetComputedDoubleDisplayValue(p.renderer)
            pts[k] = (x, H - y)
        p.close()
        d = ImageDraw.Draw(im)
        # labels on the image's left and right margins, nearest side, stacked to avoid overlap
        sides = {"L": [], "R": []}
        for k in keys:
            sides["L" if pts[k][0] < W / 2 else "R"].append(k)
        for side, ks in sides.items():
            ks.sort(key=lambda k: pts[k][1])
            y = 50
            for k in ks:
                txt = anchors[k][1]
                bb = d.multiline_textbbox((0, 0), txt, font=font)
                tw, th = bb[2] - bb[0], bb[3] - bb[1]
                y = max(y, pts[k][1] - th / 2)
                x = 8 if side == "L" else W - tw - 16
                box_ = (x - 4, y - 4, x + tw + 4, y + th + 6)
                ax_, ay_ = (box_[2], (box_[1] + box_[3]) / 2) if side == "L" else (box_[0], (box_[1] + box_[3]) / 2)
                d.line([(ax_, ay_), pts[k]], fill=(60, 60, 60), width=2)
                d.ellipse([pts[k][0] - 3, pts[k][1] - 3, pts[k][0] + 3, pts[k][1] + 3], fill=(60, 60, 60))
                d.rectangle(box_, fill=(255, 255, 255), outline=(150, 150, 150))
                d.multiline_text((x, y), txt, fill=(25, 25, 25), font=font, spacing=3)
                y = box_[3] + 10
        d.rectangle([0, 0, W, 34], fill=(245, 245, 245))
        d.text((10, 7), title, fill=(25, 25, 25), font=fontb)
        tiles.append(im)
    canvas = Image.new("RGB", (W * len(tiles), H + 40), "white")
    for i, t in enumerate(tiles):
        canvas.paste(t, (i * W, 0))
    d = ImageDraw.Draw(canvas)
    x = 12
    for c, txt in ((V24, "+24 V from J6"), (V5, "+5 V to the Pi"), (V12, "+12 V to the servos"), (GND, "GND"),
                   (None, "new parts in full colour, s1_tool.py's parts pale; Pi and servo adapter kept in colour")):
        if c:
            d.line([(x, H + 20), (x + 34, H + 20)], fill=tuple(int(v * 255) for v in _hex(c)), width=6)
            x += 42
        d.text((x, H + 11), txt, fill=(40, 40, 40), font=font)
        x += d.textlength(txt, font=font) + 26
    OUT.mkdir(exist_ok=True)
    path = OUT / "power_on_tool.png"
    canvas.save(path)
    print("->", path.relative_to(HERE))


if __name__ == "__main__":
    which = sys.argv[1:] or ["wiring", "on_tool"]
    for w in which:
        globals()[w]()
