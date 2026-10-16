"""Joint table for tool-down fingertip poses in the arm plane (J1 = 0): (r, z) grid -> J2, J3, J5,
for piper_seek_tape.py (issue #19). J4 = 0 and J6 is constant; J1 is the azimuth. Each point is
piper_pick_tape.ik's damped least squares, warm-started down each column. The tool tilts outward
10 deg (as piper_pick_tape grasps) out to r = 280 mm, then more with reach so far points stay
under J5's 70 deg limit.

    python make_iktable.py iktable.json   # about a minute on 4 cores
"""
import sys, json, math
from multiprocessing import Pool
sys.path.insert(0, __import__("os").path.dirname(__import__("os").path.abspath(__file__)))
from piper_pick_tape import ik, target_rotation, in_limits, fk_all, tip, pos, REST_JOINTS_DEG

R0, R1, DR = 120, 470, 5
Z0, Z1, DZ = 0, 340, 5

def tilt(r):
    return 10.0 if r <= 280 else min(25.0, 10.0 + (r - 280) * 15.0 / 120.0)

def row(r):
    out, seed = [], None
    R_t = target_rotation(0.0, SIGN, tilt(r))
    for z in range(Z1, Z0 - 1, -DZ):  # top down, warm-started
        s = seed or [0, 60, -60, 0, 60, J6]
        q, pe, re = ik([r, 0.0, z], R_t, s, 150.0)
        if pe < 0.3 and re < 0.3 and in_limits(q):
            Ts = fk_all(q)
            low = min(pos(Ts[2])[2], pos(Ts[4])[2], pos(Ts[5])[2])
            out.append((z, [round(v, 4) for v in q], round(low, 1)))
            seed = q
        else:
            out.append((z, None, None))
            seed = None
    return r, out

# finger-axis sign and J6 as piper_pick_tape.plan picks them (J6 nearest the rest J6)
best = None
for sign in (1, -1):
    q, pe, re = ik([247, 0, 109], target_rotation(0.0, sign, 10.0), [0, 60, -60, 0, 60, 64.0], 150.0)
    if pe < 0.5 and re < 0.5 and in_limits(q):
        c = abs(q[5] - 64.0) + abs(q[3])
        if best is None or c < best[0]:
            best = (c, sign, q[5])
SIGN, J6 = best[1], best[2]

if __name__ == "__main__":
    with Pool(4) as p:
        rows = p.map(row, range(R0, R1 + 1, DR))
    grid = {"r0": R0, "r1": R1, "dr": DR, "z0": Z0, "z1": Z1, "dz": DZ, "sign": SIGN, "j6": J6,
            "tilt": "10 deg to r = 280 mm, then +15 deg per 120 mm, max 25", "rows": {}}
    for r, out in rows:
        grid["rows"][str(r)] = {str(z): q for z, q, low in out}
    json.dump(grid, open(sys.argv[1], "w"))
    n = sum(1 for r, out in rows for z, q, low in out if q)
    print("sign", SIGN, "J6", J6, "valid", n, "of", sum(len(o) for _, o in rows))
    for r, out in rows[::6]:
        zs = [z for z, q, low in out if q]
        print(r, "z valid", (min(zs), max(zs)) if zs else None, "J4 max", max((abs(q[3]) for z, q, l in out if q), default=None))
