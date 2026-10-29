#!/usr/bin/env python3
"""Ring spacers for #53: 4 mm tall with a 2 mm wall, four of them in one STL.

Writes `spacer.stl` (one ring) and `spacers_x4.stl` (four rings on a 2 x 2 grid, one object
in Studio). Standard library only:

    python make_spacers.py [--bore 4.2] [--wall 2.0] [--height 4.0] [--count 4]
"""
import argparse
import math
import struct
from pathlib import Path

SEGMENTS = 180  # 2 deg per facet: the facets sit < 0.001 mm inside a 4.2 mm bore


def ring(r_in, r_out, h, cx=0.0, cy=0.0, n=SEGMENTS):
    """Triangles of a closed tube (annulus extruded along Z), outward normals."""
    c = [math.cos(2 * math.pi * k / n) for k in range(n)]
    s = [math.sin(2 * math.pi * k / n) for k in range(n)]
    tris = []
    for i in range(n):
        j = (i + 1) % n
        oi0, oj0 = (cx + r_out * c[i], cy + r_out * s[i], 0), (cx + r_out * c[j], cy + r_out * s[j], 0)
        oi1, oj1 = (oi0[0], oi0[1], h), (oj0[0], oj0[1], h)
        ii0, ij0 = (cx + r_in * c[i], cy + r_in * s[i], 0), (cx + r_in * c[j], cy + r_in * s[j], 0)
        ii1, ij1 = (ii0[0], ii0[1], h), (ij0[0], ij0[1], h)
        tris += [(oi0, oj0, oj1), (oi0, oj1, oi1)]  # outside wall
        tris += [(ii0, ii1, ij1), (ii0, ij1, ij0)]  # bore
        tris += [(oi1, oj1, ij1), (oi1, ij1, ii1)]  # top
        tris += [(oi0, ii0, ij0), (oi0, ij0, oj0)]  # bottom
    return tris


def normal(p0, p1, p2):
    u = [p1[i] - p0[i] for i in range(3)]
    v = [p2[i] - p0[i] for i in range(3)]
    w = (u[1] * v[2] - u[2] * v[1], u[2] * v[0] - u[0] * v[2], u[0] * v[1] - u[1] * v[0])
    m = math.sqrt(sum(x * x for x in w))
    return [x / m for x in w]


def write_stl(path, tris, name):
    with open(path, "wb") as f:
        f.write(name.encode()[:80].ljust(80, b" "))
        f.write(struct.pack("<I", len(tris)))
        for t in tris:
            f.write(struct.pack("<12fH", *normal(*t), *t[0], *t[1], *t[2], 0))


def main():
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("--bore", type=float, default=4.2, help="bore diameter, mm")
    p.add_argument("--wall", type=float, default=2.0, help="radial wall, mm")
    p.add_argument("--height", type=float, default=4.0, help="height, mm")
    p.add_argument("--count", type=int, default=4, choices=[1, 2, 3, 4])
    p.add_argument("--pitch", type=float, default=16.0, help="centre spacing on the grid, mm")
    a = p.parse_args()

    r_in, r_out = a.bore / 2, a.bore / 2 + a.wall
    here = Path(__file__).resolve().parent
    tag = f"spacer OD{2 * r_out:g} ID{a.bore:g} H{a.height:g}"
    write_stl(here / "spacer.stl", ring(r_in, r_out, a.height), tag)
    centres = [(x, y) for y in (0.5, -0.5) for x in (-0.5, 0.5)][: a.count]
    tris = [t for x, y in centres for t in ring(r_in, r_out, a.height, x * a.pitch, y * a.pitch)]
    write_stl(here / f"spacers_x{a.count}.stl", tris, f"{a.count} x {tag}")
    vol = math.pi * (r_out**2 - r_in**2) * a.height
    print(f"{a.count} x {tag}: {vol:.1f} mm^3 each, pitch {a.pitch:g} mm")


if __name__ == "__main__":
    main()
