"""Render the GIF (and an MP4) for this run from its raw MJPEG (~/pick_tape_videos/test1.mjpeg on the arm Pi; copied to /tmp
to run this, since run videos stay out of git). Needs opencv, pillow, imageio-ffmpeg."""
import sys, csv, numpy as np, cv2, mjpeg
from PIL import Image

def save_gif(frames, path, ms):
    """Encode with ffmpeg (palettegen/paletteuse); also writes an MP4 next to it."""
    import subprocess, tempfile, os, imageio_ffmpeg
    ff = imageio_ffmpeg.get_ffmpeg_exe()
    h, w = frames[0].shape[:2]
    fps = 1000.0 / ms
    mp4 = os.path.splitext(path)[0] + ".mp4"
    p = subprocess.Popen([ff, "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "bgr24", "-s", f"{w}x{h}",
                          "-r", f"{fps:.3f}", "-i", "-", "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "18", mp4],
                         stdin=subprocess.PIPE)
    for f in frames:
        p.stdin.write(np.ascontiguousarray(f).tobytes())
    p.stdin.close(); p.wait()
    subprocess.run([ff, "-y", "-loglevel", "error", "-i", mp4, "-vf",
                    "split[a][b];[a]palettegen=max_colors=200:stats_mode=full[p];[b][p]paletteuse=dither=bayer:bayer_scale=4:diff_mode=rectangle",
                    "-loop", "0", path], check=True)

def label(f, text, y=26, scale=0.7):
    (w, h), _ = cv2.getTextSize(text, cv2.FONT_HERSHEY_SIMPLEX, scale, 1)
    cv2.rectangle(f, (4, y - h - 6), (14 + w, y + 6), (35, 35, 35), -1)
    cv2.putText(f, text, (9, y), cv2.FONT_HERSHEY_SIMPLEX, scale, (245, 245, 245), 1, cv2.LINE_AA)

if __name__ == "__main__":
    # ---- test 1: 2304x1296 @15 fps, crop away from the person on the right
    data, idx = mjpeg.index('/tmp/t1/test1.mjpeg'); t = mjpeg.pts('/tmp/t1/test1.mjpeg.pts')
    rows = list(csv.DictReader(open('/tmp/t1/test1_trace.csv'))); T = np.array([float(r['t']) for r in rows])
    names = {"start": "start", "open": "open gripper", "to_pregrasp": "to the hover over the shelf", "down": "straight down",
             "close": "close (1.0 N*m)", "up": "lift", "hold": "hold", "place": "carry round the base to the start",
             "release": "release", "place_back": "rise", "home": "home", "gripper": "park", "estop": "park", "reset": "park", "disable": "park"}
    fr = []
    for k in range(int(np.searchsorted(t, 2.0)), int(np.searchsorted(t, 81.0)), 5):
        f = mjpeg.frame(data, idx, k)[330:1250, 380:1330]
        f = cv2.resize(f, (360, 350), interpolation=cv2.INTER_AREA)
        i = min(int(np.searchsorted(T, t[k] + 0.7)), len(T) - 1)
        label(f, f"test 1  {t[k]:4.1f} s  (5x)"); label(f, names.get(rows[i]['phase'], rows[i]['phase']), y=52, scale=0.6)
        fr.append(f)
    save_gif(fr, '/tmp/out/test1_shelf_to_start_5x.gif', 66)
    print("test1 frames", len(fr))
