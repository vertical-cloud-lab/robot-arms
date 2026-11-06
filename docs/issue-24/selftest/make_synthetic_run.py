"""Fake a filmed run from the twin itself, to test piper_camera_compare.py end to end."""
import sys, json, time, os, numpy as np, cv2
sys.path.insert(0, '/home/runner/work/robot-arms/robot-arms/scripts')
import piper_twin as tw, piper_camera_check as pcc
out = sys.argv[1]; nseg = int(sys.argv[2]) if len(sys.argv) > 2 else 9
plan = json.load(open('/home/runner/work/robot-arms/robot-arms/docs/issue-24/plan_rest.json'))
segs = plan['segments'][:nseg] + [plan['segments'][-1]]
segs[-1] = dict(segs[-1], **{'from': segs[-2]['to']})
cam_full = tw.Camera.load('/home/runner/work/robot-arms/robot-arms/docs/issue-24/camera_2026-10-13.json')
W, H = 1536, 864
cam = cam_full.scaled(W, H)
# the "true" camera differs from the model a little
rv, tv = cam.rvec + np.radians([0.3, -0.2, 0.1]), cam.tvec + np.array([4.0, -3.0, 5.0])
true = tw.Camera(W, H, cam.K, cam.dist, rv, tv)
meshes = tw.load_meshes()
photo = cv2.resize(cv2.imread('/tmp/pi24/still_full.jpg'), (W, H), interpolation=cv2.INTER_AREA)
REST = [3.99, -1.96, 2.15, 1.38, 23.34, 64.29]
bd = tw.remove_arm(photo, cam, meshes, REST)
fps, hz = 10.0, 100.0
tl = pcc.timeline(segs, hz=hz, lead_s=1.5)
U0 = 1_760_000_000.0
rng = np.random.default_rng(1)
with open(f'{out}/run.csv', 'w') as f:
    f.write('unix_t,phase,' + ','.join(f'j{i}' for i in range(1, 7)) + ',grip_mm,' + ','.join(f'cmd{i}' for i in range(1, 7)) + '\n')
    for t, lab, q in tl:
        qq = np.array(q) + rng.normal(0, 0.02, 6)
        f.write(f'{U0 + t:.3f},{lab},' + ','.join(f'{v:.3f}' for v in qq) + ',3.0,' + ',,,,,' + '\n')
# marks: hold windows
marks, t = [], 1.5
for s in segs:
    t += s['move_s']; marks.append({'label': s['label'], 'unix_t0': U0 + t, 'unix_t1': U0 + t + s['hold_s'], 'target': s['to'], 'measured': s['to']}); t += s['hold_s']
json.dump({'video_start_unix': U0 - 0.3, 'poses': marks}, open(f'{out}/run_marks.json', 'w'), indent=1)
# video: frames start 0.37 s after the trace's first sample (the compare tool must find this)
lag = 0.37
tq = np.array([x[0] for x in tl]); qs = np.array([x[2] for x in tl])
n = int((tq[-1] - lag) * fps)
jpgs = bytearray(); pts = []
for k in range(n):
    tt = lag + k / fps
    q = [np.interp(tt, tq, qs[:, j]) for j in range(6)]
    img = tw.render(true, meshes, q, 3.0, bd.copy(), rgb=(48, 48, 52), alpha=1.0)
    img = cv2.add(img, rng.normal(0, 2, img.shape).astype(np.int8), dtype=cv2.CV_8U) if False else img
    ok, buf = cv2.imencode('.jpg', img, [cv2.IMWRITE_JPEG_QUALITY, 85]); jpgs += buf.tobytes(); pts.append(k * 1000 / fps + 123.0)
open(f'{out}/run.mjpeg', 'wb').write(bytes(jpgs))
open(f'{out}/run.mjpeg.pts', 'w').write('# timecode format v2\n' + '\n'.join(f'{p:.3f}' for p in pts) + '\n')
print('frames', n, 'true first-frame unix', U0 + lag)
