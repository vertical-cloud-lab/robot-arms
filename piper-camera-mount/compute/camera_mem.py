#!/usr/bin/env python3
"""How much RAM the wrist's two cameras take on a Pi 5, measured on the Pi itself.

Runs on a Pi 5 with the HQ Camera (imx477) and the Camera Module 3 Wide (imx708_wide) attached,
using the system picamera2. No frames are written or sent anywhere: the Wide's H.264 goes to
/dev/null and the HQ frames are dropped as soon as they arrive. Three cases, in one process:

- A: the everyday wrist job. The Wide streams 720p30 H.264 (software, as on every Pi 5) from its
  full-field 2304 x 1296 mode, and the HQ feeds a perception loop at 2028 x 1520.
- A2: A plus one 12 MP HQ still (switch_mode_and_capture) while the Wide keeps streaming.
- B: both cameras at full 12 MP RGB at once, the worst case.

The cost of each case is the drop in MemAvailable from before picamera2 is imported, sampled every
0.1 s. That counts the camera buffers (dma-bufs, which aren't in the process's RSS), the kernel
drivers' own buffers and the Python process. If OpenCV is installed, A also runs AprilTag (36h11)
detection on the HQ's Y plane.

    ssh <user>@<camera Pi> 'python3 -' < compute/camera_mem.py    # prints one RESULT {...} line
"""
import json
import os
import threading
import time

os.environ.setdefault("LIBCAMERA_LOG_LEVELS", "*:ERROR")


def meminfo():
    d = {}
    for line in open("/proc/meminfo"):
        k, v = line.split(":")
        d[k] = int(v.split()[0]) / 1024  # MB
    return d


def status():
    d = {}
    for line in open("/proc/self/status"):
        if line.startswith(("VmRSS", "VmHWM", "RssAnon", "RssFile", "RssShmem")):
            k, v = line.split(":")
            d[k] = round(int(v.split()[0]) / 1024)
    return d


def dmabufs():
    """The dma-bufs this process holds, by exporter (from /proc/self/fdinfo, no root needed)."""
    seen, total, by_exp = set(), 0, {}
    for fd in os.listdir("/proc/self/fd"):
        try:
            if "dmabuf" not in os.readlink(f"/proc/self/fd/{fd}"):
                continue
            info = dict(l.split(":", 1) for l in open(f"/proc/self/fdinfo/{fd}").read().splitlines() if ":" in l)
            ino = info.get("ino", fd).strip()
            if ino in seen:
                continue
            seen.add(ino)
            size = int(info.get("size", "0").strip())
            total += size
            exp = info.get("exp_name", "?").strip()
            by_exp[exp] = by_exp.get(exp, 0) + size
        except OSError:
            pass
    return {"count": len(seen), "MB": round(total / 2**20, 1),
            "by_exporter_MB": {k: round(v / 2**20, 1) for k, v in by_exp.items()}}


class Sampler:
    """Tracks the lowest MemAvailable since the last reset()."""

    def __init__(self):
        self.min_avail, self.stop = 1e9, False
        threading.Thread(target=self.run, daemon=True).start()

    def run(self):
        while not self.stop:
            self.min_avail = min(self.min_avail, meminfo()["MemAvailable"])
            time.sleep(0.1)

    def reset(self):
        self.min_avail = 1e9


start = meminfo()
out = {"pi": open("/proc/device-tree/model").read().strip("\0"), "MemTotal_MB": round(start["MemTotal"]),
       "MemAvailable_before_MB": round(start["MemAvailable"])}

from picamera2 import Picamera2  # noqa: E402
from picamera2.encoders import H264Encoder  # noqa: E402
from picamera2.outputs import FileOutput  # noqa: E402

try:
    import cv2
    det = cv2.aruco.ArucoDetector(cv2.aruco.getPredefinedDictionary(cv2.aruco.DICT_APRILTAG_36h11))
    out["opencv"] = cv2.__version__
except Exception as e:  # not installed on the stock image
    det = None
    out["opencv"] = f"not installed ({type(e).__name__})"
out["cameras"] = [c.get("Model") for c in Picamera2.global_camera_info()]
out["picamera2_import_MB"] = round(start["MemAvailable"] - meminfo()["MemAvailable"])
s = Sampler()


def record(label, **extra):
    time.sleep(0.5)
    out[label] = {"MB": round(start["MemAvailable"] - s.min_avail), "process": status(),
                  "dmabufs_held": dmabufs(), **extra}


idx = {m: i for i, m in enumerate(out["cameras"])}
hq, wide = Picamera2(idx["imx477"]), Picamera2(idx["imx708_wide"])
hq_video = hq.create_video_configuration(main={"size": (2028, 1520), "format": "YUV420"},
                                         sensor={"output_size": (2028, 1520)})
wide_video = wide.create_video_configuration(main={"size": (1280, 720), "format": "YUV420"},
                                             sensor={"output_size": (2304, 1296)})
out["buffer_count"] = {"hq_video": hq_video["buffer_count"], "wide_video": wide_video["buffer_count"]}

# A: the everyday job
s.reset()
hq.configure(hq_video)
wide.configure(wide_video)
wide.start_recording(H264Encoder(bitrate=4_000_000), FileOutput("/dev/null"))
hq.start()
cpu0, t0, n, tags, t_det = os.times(), time.time(), 0, 0, 0.0
while time.time() - t0 < 20:
    y = hq.capture_array("main")[:1520, :2028]  # the Y plane, which is what a detector uses
    if det is not None:
        t1 = time.time()
        _, ids, _ = det.detectMarkers(y)
        t_det += time.time() - t1
        tags += 0 if ids is None else len(ids)
    n += 1
cpu1, wall = os.times(), time.time() - t0
record("A_wide_720p30_h264_plus_hq_2028x1520", hq_fps=round(n / wall, 1),
       cpu_cores=round((cpu1.user + cpu1.system - cpu0.user - cpu0.system) / wall, 2),
       apriltag_ms_per_frame=round(1000 * t_det / n) if det else None, tags_seen=tags if det else None)

# A2: one 12 MP HQ still while the Wide keeps streaming (point and shoot)
s.reset()
arr = hq.switch_mode_and_capture_array(hq.create_still_configuration(main={"size": (4056, 3040), "format": "RGB888"}))
shape = list(arr.shape)
del arr
record("A2_plus_one_12MP_hq_still", still_shape=shape)
hq.stop()
wide.stop_recording()

# B: both cameras at full 12 MP RGB at once
s.reset()
hq_still = hq.create_still_configuration(main={"size": (4056, 3040), "format": "RGB888"})
wide_still = wide.create_still_configuration(main={"size": (4608, 2592), "format": "RGB888"})
out["buffer_count"].update(hq_still=hq_still["buffer_count"], wide_still=wide_still["buffer_count"])
hq.configure(hq_still)
wide.configure(wide_still)
hq.start()
wide.start()
for _ in range(3):
    a, b = hq.capture_array("main"), wide.capture_array("main")
    del a, b
record("B_both_full_12MP_rgb_at_once", pairs_captured=3)
hq.stop()
wide.stop()
hq.close()
wide.close()
s.stop = True
print("RESULT " + json.dumps(out))
