#!/usr/bin/env python3
"""Print sheet for this workflow's AprilTags (tag36h11), at their real size, from the IDs and
sizes in settings.py: the holder's, the box's, the calibration card's and (if set) the auger's.

    python make_tags.py          # writes tags_to_print.pdf (US Letter)

Print it at 100% ("actual size", no "fit to page") and check the 50 mm scale bar with a ruler.
Cut each tag out with its white border (one data square wide: never trim into it), and stick
it flat. The small arrow marks the tag's top edge; settings.py's tag frames assume the tags on
one object all point the same way (locate() copes with any multiple of 90 deg, if two or more
of the object's tags are seen).
"""
import os

import settings as S
import vision as V

HERE = os.path.dirname(os.path.abspath(__file__))
PAGE_MM = (215.9, 279.4)  # US Letter


def tags():
    out = [(i, S.HOLDER_TAG_SIZE_MM, "holder") for i in S.HOLDER_TAGS]
    out += [(i, S.BOX_TAG_SIZE_MM, "box") for i in S.BOX_TAGS]
    out += [(i, S.CAL_TAG_SIZE_MM, "calibration card") for i in S.CAL_TAG_IDS]
    if S.AUGER_TAG:
        out.append((S.AUGER_TAG["id"], S.AUGER_TAG["size_mm"], "auger"))
    return out


def main(path=os.path.join(HERE, "tags_to_print.pdf")):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    fig = plt.figure(figsize=(PAGE_MM[0] / 25.4, PAGE_MM[1] / 25.4))
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_xlim(0, PAGE_MM[0])
    ax.set_ylim(0, PAGE_MM[1])
    ax.axis("off")
    ax.text(15, PAGE_MM[1] - 15, "Powder-Doser Workflow 1: AprilTags (tag36h11). Print at 100%.",
            fontsize=9, va="top")
    ax.plot([15, 65], [PAGE_MM[1] - 25] * 2, color="black", lw=1)
    ax.text(40, PAGE_MM[1] - 27, "50 mm", ha="center", va="top", fontsize=7)
    x, y, row_h = 15.0, PAGE_MM[1] - 45, 0.0
    for tag_id, size, what in tags():
        full = size * 10 / 8  # with the white border
        if x + full > PAGE_MM[0] - 10:
            x, y = 15.0, y - row_h - 18
            row_h = 0.0
        ax.imshow(V.tag_image(tag_id, 20), cmap="gray", vmin=0, vmax=255,
                  extent=[x, x + full, y - full, y], interpolation="nearest")
        ax.add_patch(plt.Rectangle((x, y - full), full, full, fill=False, lw=0.3, ls=":"))
        ax.annotate("", (x + full / 2, y + 4), (x + full / 2, y + 0.5),
                    arrowprops=dict(arrowstyle="->", lw=0.6))
        ax.text(x, y - full - 2, f"ID {tag_id} · {what} · {size:g} mm", fontsize=6, va="top")
        x += full + 15
        row_h = max(row_h, full)
    fig.savefig(path)
    plt.close(fig)
    print(f"wrote {path}: {', '.join(str(t[0]) for t in tags())}")


if __name__ == "__main__":
    main()
