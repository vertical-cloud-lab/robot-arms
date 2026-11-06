"""Draw docs/wiring/iot-relay-pi5.png: Digital Loggers IoT Relay II control input -> Raspberry Pi 5.

    python docs/wiring/iot_relay_pi5.py

Sources for the geometry and labels:
- Board outline, header and port positions (mm): Raspberry Pi 5 mechanical drawing,
  https://datasheets.raspberrypi.com/rpi5/raspberry-pi-5-mechanical-drawing.pdf
  (the header's square pad, pin 1, is at the inner-row end farthest from the USB ports).
- Pin functions: https://www.raspberrypi.com/documentation/computers/raspberry-pi.html#gpio
- Relay polarity (facing the green connector: + left, - right) and outlet behaviour:
  https://www.digital-loggers.com/iot2faqs.html and https://www.digital-loggers.com/iot2spec.pdf
"""

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.patches import Circle, FancyArrowPatch, FancyBboxPatch, Rectangle  # noqa: E402

OUT = Path(__file__).with_name("iot-relay-pi5.png")

RED = "#c62828"  # + wire, GPIO17
BLACK = "#1b1b1b"  # - wire, GND
BLUE = "#1565c0"  # close-up marker
GREY = "#5f6368"
PCB = "#dcefe0"
PCB_EDGE = "#2e6b3a"
PORT = "#cfd3d6"
HEADER = "#3b3b3b"
GOLD = "#e8d590"
POWER = "#f4c7b8"
TERM = "#43a047"
TERM_EDGE = "#1b5e20"
YELLOW = "#f2c94c"
RELAY = "#262626"

PITCH = 2.54
HDR_CX, HDR_CY = 32.5, 52.5  # header centre, mm from the board's bottom-left corner

NAMES = {
    1: "3V3", 2: "5V", 3: "GPIO2", 4: "5V", 5: "GPIO3", 6: "GND",
    7: "GPIO4", 8: "GPIO14", 9: "GND", 10: "GPIO15", 11: "GPIO17", 12: "GPIO18",
}
POWER_PINS = {1, 2, 4}
PLUS_PIN, MINUS_PIN = 11, 9
WIRE = {PLUS_PIN: RED, MINUS_PIN: BLACK}


def board_pin(n):
    """Board position (mm) of header pin n. Odd pins are the inner row, even pins the edge row."""
    col = (n - 1) // 2
    x = HDR_CX + (col - 9.5) * PITCH
    y = HDR_CY - PITCH / 2 if n % 2 else HDR_CY + PITCH / 2
    return x, y


def draw_board(ax):
    ax.add_patch(FancyBboxPatch((0, 0), 85, 56, boxstyle="round,pad=0,rounding_size=3",
                                fc=PCB, ec=PCB_EDGE, lw=2, zorder=1))
    for x, y in [(3.5, 3.5), (61.5, 3.5), (3.5, 52.5), (61.5, 52.5)]:
        ax.add_patch(Circle((x, y), 1.4, fc="white", ec=PCB_EDGE, lw=1.2, zorder=2))

    # Ports, from the mechanical drawing
    for (x, y, w, h, label) in [
        (71.0, 40.3, 17.5, 13.6, "USB"),
        (71.0, 22.0, 17.5, 13.8, "USB"),
        (67.0, 1.0, 21.2, 17.3, "Ethernet"),
    ]:
        ax.add_patch(Rectangle((x, y), w, h, fc=PORT, ec=GREY, lw=1.2, zorder=2))
        ax.text(x + w / 2, y + h / 2, label, ha="center", va="center", fontsize=10, color="#333", zorder=3)
    for (x, w, label) in [(6.7, 8.9, None), (22.5, 6.7, None), (35.9, 6.6, None)]:
        ax.add_patch(Rectangle((x, -1.4), w, 7.6, fc=PORT, ec=GREY, lw=1.2, zorder=2))
    ax.text(11.2, 8.0, "USB-C\npower", ha="center", va="bottom", fontsize=8.5, color="#333", zorder=3)
    ax.text(32.5, 8.0, "micro-HDMI ×2", ha="center", va="bottom", fontsize=8.5, color="#333", zorder=3)
    for x in (47.3, 53.6):  # camera/display connectors
        ax.add_patch(Rectangle((x, 1.0), 3.0, 15.2, fc="#bfc5c9", ec=GREY, lw=0.8, zorder=2))

    # 40-pin header
    x1, _ = board_pin(1)
    x40, _ = board_pin(40)
    ax.add_patch(Rectangle((x1 - 1.6, HDR_CY - 2.9), (x40 - x1) + 3.2, 5.8, fc=HEADER, ec="black",
                           lw=1, zorder=3))
    for n in range(1, 41):
        x, y = board_pin(n)
        if n in WIRE:
            ax.add_patch(Circle((x, y), 1.0, fc=WIRE[n], ec="white", lw=1.0, zorder=5))
        elif n == 1:
            ax.add_patch(Rectangle((x - 0.6, y - 0.6), 1.2, 1.2, fc=GOLD, ec=GOLD, zorder=4))
        else:
            ax.add_patch(Circle((x, y), 0.55, fc=GOLD, ec=GOLD, zorder=4))
    ax.text(45, 45.6, "40-pin GPIO header", ha="center", va="center", fontsize=10, color="#222")

    # Pin 1 callout
    px, py = board_pin(1)
    ax.annotate("pin 1 = the square pad,\nat the end away from the USB ports",
                xy=(px, py - 0.8), xytext=(3.0, 36.5), fontsize=8.5, color="#222", ha="left", va="center",
                arrowprops=dict(arrowstyle="-|>", color="#222", lw=1.0, shrinkA=0, shrinkB=1), zorder=6)

    # Blue box around pins 1-12, linked to the close-up
    x12, _ = board_pin(12)
    ax.add_patch(Rectangle((x1 - 2.0, HDR_CY - 3.6), (x12 - x1) + 4.0, 7.2, fill=False, ec=BLUE, lw=2,
                           ls="--", zorder=6))
    ax.add_patch(FancyArrowPatch((x12 + 2.0, HDR_CY + 4.2), (99, 62), arrowstyle="-|>", mutation_scale=16,
                                 color=BLUE, lw=1.6, ls="--", zorder=6))

    ax.text(42.5, -5.5, "Raspberry Pi 5, seen from above", ha="center", va="top", fontsize=12.5,
            fontweight="bold", color="#222")


def draw_closeup(ax):
    x0, y_in, step, r = 118.0, 62.0, 14.2, 5.2
    y_out = y_in + step
    ax.add_patch(FancyBboxPatch((100, 44), 106, 52, boxstyle="round,pad=0,rounding_size=3",
                                fc="#f5f9ff", ec=BLUE, lw=2, ls="--", zorder=1))
    ax.text(153, 93, "Close-up of the blue box: pins 1–12", ha="center", va="center", fontsize=11.5,
            fontweight="bold", color=BLUE)
    ax.add_patch(Rectangle((x0 - 8, y_in - 8), 5 * step + 16, step + 16, fc=HEADER, ec="black", lw=1,
                           zorder=2))
    ax.text(202, (y_in + y_out) / 2, "···\n13–40", ha="center", va="center", fontsize=9, color=GREY)

    for n in range(1, 13):
        col = (n - 1) // 2
        x = x0 + col * step
        y = y_in if n % 2 else y_out
        if n in WIRE:
            fc, tc, lw, ec = WIRE[n], "white", 2.5, "white"
        elif n in POWER_PINS:
            fc, tc, lw, ec = POWER, "#7a1f0e", 1.0, "#b0442a"
        else:
            fc, tc, lw, ec = GOLD, "#222", 1.0, "#9c8a3d"
        if n == 1:
            ax.add_patch(Rectangle((x - r, y - r), 2 * r, 2 * r, fc=fc, ec=ec, lw=lw, zorder=5))
        else:
            ax.add_patch(Circle((x, y), r, fc=fc, ec=ec, lw=lw, zorder=5))
        ax.text(x, y, str(n), ha="center", va="center", fontsize=11, fontweight="bold", color=tc, zorder=6)

        label = NAMES[n]
        ly = y - r - 3.6 if n % 2 else y + r + 3.6
        if n in WIRE:
            color, weight = WIRE[n], "bold"
        elif n in POWER_PINS:
            color, weight = "#b0442a", "bold"
        else:
            color, weight = "#444", "normal"
        ax.text(x, ly, label, ha="center", va="center", fontsize=9.5, color=color, fontweight=weight,
                zorder=7, bbox=dict(boxstyle="round,pad=0.15", fc="#f5f9ff", ec="none"))

    ax.text(104.6, y_out, "edge\nrow", ha="center", va="center", fontsize=8, color=GREY)
    ax.text(104.6, y_in, "inner\nrow", ha="center", va="center", fontsize=8, color=GREY)
    return (x0 + 4 * step, y_in), (x0 + 5 * step, y_in)  # pin 9, pin 11


def draw_relay(ax, y_plus, y_minus):
    ax.add_patch(FancyBboxPatch((222, -4), 45, 66, boxstyle="round,pad=0,rounding_size=2.5",
                                fc=RELAY, ec="black", lw=1.5, zorder=2))
    ax.text(246, 56, "IoT Relay II", ha="center", va="center", fontsize=12, fontweight="bold", color="white")
    ax.text(246, 51, "(from above; green connector\nfacing the Pi)", ha="center", va="top", fontsize=8,
            color="#d0d0d0")
    ax.text(246, 36, "Outlets:\n2 × normally OFF\n1 × normally ON\n1 × always ON", ha="center", va="top",
            fontsize=8.8, color="white", linespacing=1.5)
    ax.text(246, 6, "PiPER brick →\na normally OFF outlet", ha="center", va="center", fontsize=8.5,
            color=YELLOW)

    # Green 2-way terminal block on the side, + / - printed on the top next to it
    ax.add_patch(Rectangle((212.5, y_minus - 6), 9.5, (y_plus - y_minus) + 12, fc=TERM, ec=TERM_EDGE, lw=1.5,
                           zorder=3))
    for y in (y_plus, y_minus):
        ax.add_patch(Circle((217.2, y), 2.7, fc="#b9c2b9", ec=TERM_EDGE, lw=1.2, zorder=4))
        ax.plot([215.4, 219.0], [y, y], color=TERM_EDGE, lw=1.6, zorder=5)
    ax.add_patch(FancyBboxPatch((223.6, y_minus - 4.5), 6.0, (y_plus - y_minus) + 9, boxstyle="round,pad=0.3",
                                fill=False, ec=YELLOW, lw=1.2, zorder=4))
    ax.text(226.6, y_plus, "+", ha="center", va="center", fontsize=14, fontweight="bold", color=YELLOW, zorder=5)
    ax.text(226.6, (y_plus + y_minus) / 2, "~", ha="center", va="center", fontsize=11, color=YELLOW, zorder=5)
    ax.text(226.6, y_minus, "−", ha="center", va="center", fontsize=14, fontweight="bold", color=YELLOW, zorder=5)


def draw_connector_front(ax):
    """The green connector as you see it standing in front of it: + is the left screw."""
    cx = 238
    ax.text(cx, 98, "Standing in front of the green connector:", ha="center", va="center", fontsize=10,
            fontweight="bold", color="#222")
    ax.add_patch(Rectangle((cx - 26, 84), 52, 9, fc=RELAY, ec="black", lw=1, zorder=2))
    ax.add_patch(FancyBboxPatch((cx - 9, 85.6), 18, 5.8, boxstyle="round,pad=0.3", fill=False, ec=YELLOW, lw=1.2,
                                zorder=3))
    ax.text(cx - 5.5, 88.5, "+", ha="center", va="center", fontsize=12, fontweight="bold", color=YELLOW, zorder=4)
    ax.text(cx, 88.5, "~", ha="center", va="center", fontsize=10, color=YELLOW, zorder=4)
    ax.text(cx + 5.5, 88.5, "−", ha="center", va="center", fontsize=12, fontweight="bold", color=YELLOW, zorder=4)
    ax.add_patch(Rectangle((cx - 13, 70.5), 26, 13.5, fc=TERM, ec=TERM_EDGE, lw=1.5, zorder=3))
    for dx in (-5.5, 5.5):
        ax.add_patch(Rectangle((cx + dx - 3, 72.5), 6, 5.2, fc=TERM_EDGE, ec=TERM_EDGE, zorder=4))
        ax.add_patch(Circle((cx + dx, 80.6), 2.1, fc="#b9c2b9", ec=TERM_EDGE, lw=1, zorder=4))
    ax.text(cx - 19.5, 75, "+", ha="center", va="center", fontsize=17, fontweight="bold", color=RED)
    ax.text(cx + 19.5, 75, "−", ha="center", va="center", fontsize=17, fontweight="bold", color=BLACK)
    ax.text(cx, 67.2, "+ is the LEFT screw, − the RIGHT", ha="center", va="center", fontsize=9, color="#222")


def draw_wires(ax, pin9, pin11, y_plus, y_minus):
    x_term = 214.5
    for (px, py), y_end, color in [(pin9, y_minus, BLACK), (pin11, y_plus, RED)]:
        ax.plot([px, px, x_term], [py, y_end, y_end], color=color, lw=5, solid_capstyle="round",
                solid_joinstyle="round", zorder=3)


def draw_table(ax):
    ax.add_patch(FancyBboxPatch((99, 3), 64, 33, boxstyle="round,pad=0,rounding_size=2", fc="white", ec="#9e9e9e",
                                lw=1.2, zorder=1))
    ax.text(131, 31.5, "Two wires", ha="center", va="center", fontsize=11.5, fontweight="bold", color="#222")
    rows = [
        ("relay  +", "pin 11  (GPIO17)", RED, 22.5),
        ("relay  −", "pin 9   (GND)", BLACK, 12.5),
    ]
    for left, right, color, y in rows:
        ax.text(102, y, left, ha="left", va="center", fontsize=11, fontweight="bold", color=color,
                family="DejaVu Sans Mono")
        ax.plot([120, 129], [y, y], color=color, lw=4, solid_capstyle="round")
        ax.text(131, y, right, ha="left", va="center", fontsize=11, fontweight="bold", color=color,
                family="DejaVu Sans Mono")
    ax.text(131, 6.2, "Any GND pin works: 6, 9, 14, 20, 25, 30, 34, 39", ha="center", va="center", fontsize=7.8,
            color=GREY)


def main():
    fig, ax = plt.subplots(figsize=(16, 7.9))
    ax.set_xlim(-8, 272)
    ax.set_ylim(-37, 101)
    ax.set_aspect("equal")
    ax.axis("off")

    y_plus, y_minus = 31.0, 20.0
    draw_board(ax)
    pin9, pin11 = draw_closeup(ax)
    draw_relay(ax, y_plus, y_minus)
    draw_connector_front(ax)
    draw_wires(ax, pin9, pin11, y_plus, y_minus)
    draw_table(ax)

    notes = [
        "GPIO17 high (3.3 V) turns the relay ON: the two normally-OFF outlets come on and the normally-ON outlet goes off. "
        "GPIO17 low, or the Pi rebooting or unplugged: relay OFF.",
        "Don't put + on a power pin (3V3 = pins 1 and 17, 5V = pins 2 and 4): the relay would then stay on whenever the Pi "
        "has power. Shut the Pi down and unplug it before wiring.",
    ]
    for i, line in enumerate(notes):
        ax.text(-6, -16 - 6.2 * i, line, ha="left", va="center", fontsize=10.2, color="#222")
    ax.text(-6, -32.5,
            "Sources: Raspberry Pi 5 mechanical drawing and GPIO pinout (raspberrypi.com); Digital Loggers IoT Relay II "
            "spec sheet and FAQ (digital-loggers.com). Drawn for vertical-cloud-lab/robot-arms#59; board not to scale "
            "with the relay.",
            ha="left", va="center", fontsize=7.8, color=GREY)

    fig.suptitle("Wiring the IoT Relay II's control input to a Raspberry Pi 5", fontsize=16, fontweight="bold",
                 y=0.985)
    fig.subplots_adjust(left=0.01, right=0.99, top=0.95, bottom=0.01)
    fig.savefig(OUT, dpi=150, facecolor="white")
    print(f"wrote {OUT}")


if __name__ == "__main__":
    main()
