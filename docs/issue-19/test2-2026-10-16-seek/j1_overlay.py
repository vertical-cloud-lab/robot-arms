# Draw the modelled folded arm at two J1 readings over a camera still (issue #19 J1 check).
# python docs/issue-19/test2-2026-10-16-seek/j1_overlay.py still.jpg out.jpg  (run from the repo root)
import sys; sys.path.insert(0, "scripts")
import piper_seek_tape as S
from PIL import Image, ImageDraw
cam = S.Cam("scripts/camera.json")
im = Image.open(sys.argv[1]).convert("RGB")
sx = im.size[0] / 2304
d = ImageDraw.Draw(im)
q0 = [None, -1.89, 0.84, 1.02, 29.66, 64.26]
for j1, col in [(23.45, (255, 0, 0)), (-3.9, (0, 160, 255))]:
    q = [j1] + q0[1:]
    for a, b, r in S.arm_segments(q):
        pa, pb = cam.project(a), cam.project(b)
        d.line([(pa[0]*sx, pa[1]*sx), (pb[0]*sx, pb[1]*sx)], fill=col, width=8)
    print(j1, [tuple(round(v) for v in cam.project(S.P.tip(S.P.fk_all(q)[5], 150.0))[:2])])
im.crop((int(300*sx), int(500*sx), int(1500*sx), int(1100*sx))).save(sys.argv[2], quality=85)
