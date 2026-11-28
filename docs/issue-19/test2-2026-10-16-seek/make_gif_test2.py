"""Render the GIF (and an MP4) for a seek run from its raw MJPEG (~/seek/run2/test2.mjpeg, ~/seek/run4/run4.mjpeg on
the arm Pi; copied to /tmp to run this, since run videos stay out of git). Needs opencv, pillow, imageio-ffmpeg.

    python make_gif_test2.py VIDEO TRACE VISION_CSV OUT.gif TITLE [SPEEDUP, default 3]
"""
import sys, csv, numpy as np, cv2, mjpeg
sys.path.insert(0, __import__('os').path.dirname(__import__('os').path.abspath(__file__)))
sys.path.insert(0, __import__('os').path.join(__import__('os').path.dirname(__import__('os').path.abspath(__file__)), '..', 'test1-2026-10-16-shelf-to-start'))
from make_gif_test1 import save_gif, label
vid, trace, vcsv, out, title = sys.argv[1:6]
step = int(sys.argv[6]) if len(sys.argv) > 6 else 3  # every step'th frame of the 14 fps recording at 14 fps
data, idx = mjpeg.index(vid); t = mjpeg.pts(vid + '.pts')
rows = list(csv.DictReader(open(trace))); T = np.array([float(r['t']) for r in rows])
vis = list(csv.DictReader(open(vcsv))); tv = np.array([float(r['t']) for r in vis]); t0v = tv[0]
names = {"open": "open gripper", "to_look": "rise out of the camera's way", "seek": "look",
         "approach": "steer to the roll (re-aimed every frame)", "down": "straight down", "close": "close",
         "up": "no grip: rise", "lift": "lift", "carry": "carry to the start", "place": "set down",
         "release": "release", "rise": "rise", "home": "home", "gripper": "park", "park": "park"}
X0, Y0, X1, Y1 = 130, 160, 690, 600
fr = []
for k in range(0, len(idx), step):
    f = mjpeg.frame(data, idx, k)
    j = int(np.argmin(np.abs(tv - t0v - t[k])))
    r = vis[j]
    if r['u']:
        u, v, bw, bh = float(r['u']) / 2, float(r['v']) / 2, float(r['bw']) / 2, float(r['bh']) / 2
        cv2.rectangle(f, (int(u - bw / 2) - 3, int(v - bh / 2) - 3), (int(u + bw / 2) + 3, int(v + bh / 2) + 3), (60, 200, 60), 2)
    f = cv2.resize(f[Y0:Y1, X0:X1], (380, 300), interpolation=cv2.INTER_AREA)
    i = min(int(np.searchsorted(T, t0v + t[k])), len(T) - 1)
    ph = rows[i]['phase'] if t0v + t[k] >= T[0] else "start"
    if ph == "down" and float(rows[i]['grip_mm']) < 63.0:  # the close runs inside the "down" phase
        ph = "close"
    label(f, f"{title}  {t[k]:4.1f} s  ({step}x)"); label(f, names.get(ph, ph), y=50, scale=0.55)
    if r['u']:
        label(f, "green box: camera sees the roll", y=290, scale=0.45)
    fr.append(f)
save_gif(fr, out, 71)
print(len(fr), "frames")
