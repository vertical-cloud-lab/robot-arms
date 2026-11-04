"""PiPER cell livestream with inline face blurring.

Pipeline::

    rpicam-vid (raw YUV420) -> this script (OpenCV: face blur, fixed masks,
    timestamp) -> ffmpeg (libx264) -> RTMP -> YouTube

The YouTube broadcast is created and ended through the lab's streaming Lambda
(vertical-cloud-lab/streamingLambda), with the same ``create``/``end`` calls as
the byu-vcl stream cams' ``device.py`` (ac-training-lab ``87a3ccb`` plus local
patches). Unlike those, every frame goes through Python, so faces can be
blurred on the Pi before anything is encoded or leaves it.

Two face detectors check every frame and the union of what they find is
pixelated: deface's CenterFace (the model and decoder from the ``deface``
package, run through OpenCV) and OpenCV's YuNet. ``STRICT_RECTS`` raise the
thresholds only over fixed objects they mistake for faces (the A1 mini's AMS
lite feeders). Nothing unblurred is ever
written to ffmpeg: if a detector cannot load, the script exits before going
live; if processing a frame fails, that frame is dropped.

Settings come from ``my_secrets.py`` next to this file; see
``my_secrets_example.py``.
"""

import json
import os
import shutil
import signal
import subprocess
import sys
import threading
import time
from pathlib import Path

import cv2
import numpy as np
import requests

import my_secrets as S

HERE = Path(__file__).resolve().parent

RESOLUTION_MAP = {
    "144p": (256, 144),
    "240p": (426, 240),
    "360p": (640, 360),
    "480p": (854, 480),
    "720p": (1280, 720),
    "1080p": (1920, 1080),
}

# Required settings.
CAM_NAME = S.CAM_NAME
WORKFLOW_NAME = S.WORKFLOW_NAME
LAMBDA_FUNCTION_URL = S.LAMBDA_FUNCTION_URL
PRIVACY_STATUS = getattr(S, "PRIVACY_STATUS", "private")

# Optional settings.
RESOLUTION = getattr(S, "RESOLUTION", "720p")
FRAME_RATE = getattr(S, "FRAME_RATE", 10)
SENSOR_MODE = getattr(S, "SENSOR_MODE", "2304:1296")
CAMERA_VFLIP = getattr(S, "CAMERA_VFLIP", False)
CAMERA_HFLIP = getattr(S, "CAMERA_HFLIP", False)
TIMESTAMP_OVERLAY = getattr(S, "TIMESTAMP_OVERLAY", True)
VIDEO_BITRATE = getattr(S, "VIDEO_BITRATE", "1500k")

# Face detectors run on every frame; their boxes are pooled.
FACE_DETECTORS = tuple(getattr(S, "FACE_DETECTORS", ("centerface", "yunet")))
# deface's CenterFace. deface's own default threshold is 0.2: it is tuned to
# blur anything that might be a face.
CENTERFACE_WIDTH = getattr(S, "CENTERFACE_WIDTH", 640)
CENTERFACE_THRESHOLD = getattr(S, "CENTERFACE_THRESHOLD", 0.2)
# OpenCV YuNet.
FACE_MODEL = getattr(S, "FACE_MODEL", str(HERE / "face_detection_yunet_2023mar.onnx"))
FACE_DETECT_WIDTH = getattr(S, "FACE_DETECT_WIDTH", 960)
FACE_SCORE_THRESHOLD = getattr(S, "FACE_SCORE_THRESHOLD", 0.5)
FACE_BOX_MARGIN = getattr(S, "FACE_BOX_MARGIN", 0.6)
FACE_HOLD_FRAMES = getattr(S, "FACE_HOLD_FRAMES", 8)
# Parts of the view, as (x0, y0, x1, y1) fractions of the frame, where a fixed
# object looks like a face (the A1 mini's AMS lite feeders: a dark housing with
# two orange couplers for eyes score up to about 0.4 with CenterFace and 0.55
# with YuNet). A box centred in one is blurred only if it scores at least
# STRICT_THRESHOLDS for its detector. Everywhere else nothing changes.
STRICT_RECTS = getattr(S, "STRICT_RECTS", [])
STRICT_THRESHOLDS = {"centerface": 0.6, "yunet": 0.7, **getattr(S, "STRICT_THRESHOLDS", {})}
# Rectangles that are always pixelated, as (x0, y0, x1, y1) fractions of the
# frame. Use them for parts of the view that look into the rest of the lab.
MASK_RECTS = getattr(S, "MASK_RECTS", [])
# OpenCV threads. The arm Pi also runs the arm, so leave it cores to spare.
CV_THREADS = getattr(S, "CV_THREADS", 2)
# Every SNAPSHOT_SEC, the last frame sent (already blurred) is saved here, so
# what goes out can be checked over SSH without opening YouTube.
SNAPSHOT_PATH = getattr(S, "SNAPSHOT_PATH", "/tmp/picam-stream-latest.jpg")
SNAPSHOT_SEC = getattr(S, "SNAPSHOT_SEC", 30)


def call_lambda(action, privacy_status="private"):
    payload = {
        "action": action,
        "cam_name": CAM_NAME,
        "workflow_name": WORKFLOW_NAME,
        "privacy_status": privacy_status,
    }
    print(f"Sending to Lambda: {payload}", flush=True)
    try:
        response = requests.post(LAMBDA_FUNCTION_URL, json=payload, timeout=60)
    except requests.exceptions.RequestException as e:
        raise RuntimeError(f"Lambda request failed: {e}")
    print(f"Lambda status code: {response.status_code}", flush=True)
    if not response.ok:
        raise RuntimeError(f"Lambda HTTP {response.status_code}: {response.text}")
    try:
        result = response.json()
    except ValueError:
        return response.text
    if isinstance(result, dict) and "statusCode" in result and "body" in result:
        return result["body"]
    return result


def create_broadcast():
    try:
        call_lambda("end")
    except RuntimeError as e:
        print(f"Could not end previous broadcast; continuing: {e}", flush=True)
    body = call_lambda("create", privacy_status=PRIVACY_STATUS)
    result = json.loads(body) if isinstance(body, str) else body
    try:
        ffmpeg_url = result["result"]["ffmpeg_url"]
    except (KeyError, TypeError) as e:
        raise RuntimeError(f"ffmpeg_url not in Lambda response: {e}")
    # Log the watch link but never the stream key.
    info = {k: v for k, v in result["result"].items() if k != "ffmpeg_url"}
    print(f"Broadcast: {info}", flush=True)
    return ffmpeg_url


class CenterFaceDetector:
    """deface's detector: the CenterFace model and decoder from ``deface``.

    Installed with ``pip install --no-deps deface``: ``deface.centerface``
    needs only numpy and OpenCV, and with ``backend="opencv"`` it never
    imports onnxruntime.
    """

    name = "centerface"

    def __init__(self, width, height):
        try:
            from deface.centerface import CenterFace, default_onnx_path
        except ImportError as e:
            raise SystemExit(f"deface is not installed ({e}); refusing to stream")
        if not Path(default_onnx_path).exists():
            raise SystemExit(f"CenterFace model missing: {default_onnx_path}; refusing to stream")
        self.scale = min(1.0, CENTERFACE_WIDTH / width)
        self.size = (int(round(width * self.scale)), int(round(height * self.scale)))
        self.net = CenterFace(in_shape=self.size, backend="opencv")
        self.net(np.zeros((self.size[1], self.size[0], 3), np.uint8))  # fail here, not live

    def __call__(self, frame):
        small = frame if self.scale == 1.0 else cv2.resize(
            frame, self.size, interpolation=cv2.INTER_AREA)  # fmt: skip
        # deface feeds the model RGB frames (from imageio); ours are BGR.
        dets, _ = self.net(cv2.cvtColor(small, cv2.COLOR_BGR2RGB),
                           threshold=CENTERFACE_THRESHOLD)  # fmt: skip
        k = 1 / self.scale
        return [(x0 * k, y0 * k, (x1 - x0) * k, (y1 - y0) * k, float(s))
                for x0, y0, x1, y1, s in dets]  # fmt: skip


class YuNetDetector:
    """OpenCV's YuNet (opencv_zoo, face_detection_yunet_2023mar.onnx)."""

    name = "yunet"

    def __init__(self, width, height):
        if not Path(FACE_MODEL).exists():
            raise SystemExit(f"Face model missing: {FACE_MODEL}; refusing to stream")
        self.scale = min(1.0, FACE_DETECT_WIDTH / width)
        self.size = (int(round(width * self.scale)), int(round(height * self.scale)))
        self.net = cv2.FaceDetectorYN.create(
            FACE_MODEL, "", self.size, FACE_SCORE_THRESHOLD, 0.3, 5000
        )

    def __call__(self, frame):
        small = frame if self.scale == 1.0 else cv2.resize(frame, self.size)
        _, faces = self.net.detect(small)
        if faces is None:
            return []
        return [(*(f[:4] / self.scale).tolist(), float(f[-1])) for f in faces]


DETECTORS = {"centerface": CenterFaceDetector, "yunet": YuNetDetector}


class FaceBlur:
    def __init__(self, width, height):
        if not FACE_DETECTORS or set(FACE_DETECTORS) - set(DETECTORS):
            raise SystemExit(f"FACE_DETECTORS must name some of {sorted(DETECTORS)}, "
                             f"not {FACE_DETECTORS!r}; refusing to stream")  # fmt: skip
        base = {"centerface": CENTERFACE_THRESHOLD, "yunet": FACE_SCORE_THRESHOLD}
        if any(STRICT_THRESHOLDS[k] < v for k, v in base.items()):
            raise SystemExit(f"STRICT_THRESHOLDS {STRICT_THRESHOLDS} is below the base "
                             f"thresholds {base}; refusing to stream")  # fmt: skip
        self.width, self.height = width, height
        self.detectors = [DETECTORS[name](width, height) for name in FACE_DETECTORS]
        self.counts = {d.name: 0 for d in self.detectors}  # boxes found, for the log
        self.held = []  # [(x0, y0, x1, y1, frames_left)]
        self.masks = [self.to_pixels(r) for r in MASK_RECTS]
        self.strict = [self.to_pixels(r) for r in STRICT_RECTS]
        self.skipped = {d.name: [0, 0.0] for d in self.detectors}  # [count, max score]

    def to_pixels(self, rect):
        x0, y0, x1, y1 = rect
        if not (0 <= x0 < x1 <= 1 and 0 <= y0 < y1 <= 1):
            raise SystemExit(f"Bad rectangle {rect!r}: want (x0, y0, x1, y1) fractions; "
                             "refusing to stream")  # fmt: skip
        w, h = self.width, self.height
        return int(x0 * w), int(y0 * h), int(x1 * w), int(y1 * h)

    def describe(self):
        base = {"centerface": CENTERFACE_THRESHOLD, "yunet": FACE_SCORE_THRESHOLD}
        out = []
        for d in self.detectors:
            s = f"{d.name} at {d.size[0]}x{d.size[1]} (threshold {base[d.name]}"
            if self.strict:
                s += f", {STRICT_THRESHOLDS[d.name]} in strict rects"
            out.append(s + ")")
        return ", ".join(out) + f", {len(self.strict)} strict rects"

    def summary(self):
        """Boxes found since the last call, for the log; resets the counts."""
        s = ", ".join(f"{k} {v}" for k, v in self.counts.items())
        if self.strict:
            s += "; strict rects skipped " + ", ".join(
                f"{k} {n} (max {m:.2f})" for k, (n, m) in self.skipped.items())
        self.counts = dict.fromkeys(self.counts, 0)
        self.skipped = {k: [0, 0.0] for k in self.skipped}
        return s

    def keep(self, name, box):
        """False for a box centred in a strict rectangle that scores below
        its detector's STRICT_THRESHOLDS."""
        x, y, w, h, score = box
        cx, cy = x + w / 2, y + h / 2
        if score >= STRICT_THRESHOLDS[name] or not any(
            x0 <= cx < x1 and y0 <= cy < y1 for x0, y0, x1, y1 in self.strict
        ):
            return True
        n, m = self.skipped[name]
        self.skipped[name] = [n + 1, max(m, score)]
        return False

    def detect(self, frame):
        boxes = []
        for det in self.detectors:
            found = det(frame)
            if self.strict:
                found = [b for b in found if self.keep(det.name, b)]
            self.counts[det.name] += len(found)
            for x, y, w, h, _ in found:
                mx, my = w * FACE_BOX_MARGIN, h * FACE_BOX_MARGIN
                boxes.append(
                    (
                        max(0, int(x - mx)),
                        max(0, int(y - my * 1.3)),  # extra room for hair
                        min(self.width, int(x + w + mx)),
                        min(self.height, int(y + h + my)),
                    )
                )
        return boxes

    @staticmethod
    def pixelate(frame, x0, y0, x1, y1, block=12):
        roi = frame[y0:y1, x0:x1]
        if roi.size == 0:
            return
        h, w = roi.shape[:2]
        small = cv2.resize(
            roi, (max(1, w // block), max(1, h // block)), interpolation=cv2.INTER_AREA
        )
        frame[y0:y1, x0:x1] = cv2.resize(small, (w, h), interpolation=cv2.INTER_NEAREST)

    def __call__(self, frame):
        new = self.detect(frame)
        # Hold every box for a few frames, so a face the detector misses for a
        # frame or two (motion blur, turning away) stays covered.
        self.held = [(*b, FACE_HOLD_FRAMES) for b in new] + [
            (*b[:4], b[4] - 1) for b in self.held if b[4] > 1
        ]
        for x0, y0, x1, y1, _ in self.held:
            self.pixelate(frame, x0, y0, x1, y1, block=max(6, (x1 - x0) // 5))
        for x0, y0, x1, y1 in self.masks:
            self.pixelate(frame, x0, y0, x1, y1, block=24)
        return len(new)


class LatestFrame(threading.Thread):
    """Reads raw I420 frames from the camera and keeps only the newest."""

    def __init__(self, stream, width, height):
        super().__init__(daemon=True)
        self.stream, self.size = stream, width * height * 3 // 2
        self.width, self.height = width, height
        self.cond = threading.Condition()
        self.frame, self.seq, self.eof = None, 0, False

    def run(self):
        while True:
            buf = self.stream.read(self.size)
            if not buf or len(buf) < self.size:
                break
            with self.cond:
                self.frame, self.seq = buf, self.seq + 1
                self.cond.notify()
        with self.cond:
            self.eof = True
            self.cond.notify()

    def get(self, last_seq, timeout=5.0):
        with self.cond:
            self.cond.wait_for(lambda: self.seq != last_seq or self.eof, timeout)
            if self.eof or self.seq == last_seq:
                return None, last_seq
            yuv = np.frombuffer(self.frame, np.uint8).reshape(
                self.height * 3 // 2, self.width
            )
            return cv2.cvtColor(yuv, cv2.COLOR_YUV2BGR_I420), self.seq


def wait_for_camera():
    """Block until libcamera lists a camera.

    Called before the Lambda is touched, so a Pi that boots without its camera
    (a loose ribbon, or a reboot the firmware's auto-detect missed) neither ends
    the broadcast that is live nor opens one that never gets video.
    """
    cmd = shutil.which("rpicam-hello") or shutil.which("libcamera-hello")
    if not cmd:
        raise SystemExit("rpicam-hello not found")
    while True:
        try:
            r = subprocess.run([cmd, "--list-cameras"], capture_output=True,
                               text=True, timeout=30)  # fmt: skip
            out = r.stdout + r.stderr
        except subprocess.TimeoutExpired:
            out = ""
        if "Available cameras" in out:
            return
        print("No camera found; checking again in 60 s", flush=True)
        time.sleep(60)


def camera_cmd(width, height):
    cmd = shutil.which("rpicam-vid") or shutil.which("libcamera-vid")
    if not cmd:
        raise SystemExit("rpicam-vid not found")
    args = [cmd, "--nopreview", "-t", "0", "--flush", "--codec", "yuv420",
            "--width", str(width), "--height", str(height),
            "--framerate", str(FRAME_RATE)]  # fmt: skip
    if SENSOR_MODE:
        args += ["--mode", SENSOR_MODE]
    if CAMERA_VFLIP:
        args.append("--vflip")
    if CAMERA_HFLIP:
        args.append("--hflip")
    return args + ["-o", "-"]


def ffmpeg_cmd(ffmpeg_url, width, height):
    gop = str(FRAME_RATE * 2)
    return [
        "ffmpeg", "-hide_banner", "-loglevel", "warning", "-stats_period", "60",
        "-f", "lavfi", "-i", "anullsrc=channel_layout=stereo:sample_rate=44100",
        "-thread_queue_size", "64", "-use_wallclock_as_timestamps", "1",
        "-f", "rawvideo", "-pix_fmt", "bgr24", "-s", f"{width}x{height}",
        "-i", "pipe:0",
        "-map", "1:v", "-map", "0:a",
        "-c:v", "libx264", "-preset", "ultrafast", "-tune", "zerolatency",
        "-pix_fmt", "yuv420p", "-r", str(FRAME_RATE), "-fps_mode", "cfr",
        "-g", gop, "-keyint_min", gop, "-sc_threshold", "0",
        "-b:v", VIDEO_BITRATE, "-maxrate", VIDEO_BITRATE, "-bufsize", "3000k",
        "-c:a", "aac", "-b:a", "64k",
        "-f", "flv", ffmpeg_url,
    ]  # fmt: skip


def draw_timestamp(frame):
    text = time.strftime("%Y-%m-%d %H:%M:%S %Z")
    scale = frame.shape[0] / 720 * 0.8
    thick = max(1, int(round(scale * 2)))
    (tw, th), base = cv2.getTextSize(text, cv2.FONT_HERSHEY_SIMPLEX, scale, thick)
    x, y = frame.shape[1] - tw - 12, 12 + th
    cv2.rectangle(frame, (x - 6, y - th - 6), (x + tw + 6, y + base + 4), (0, 0, 0), -1)
    cv2.putText(frame, text, (x, y), cv2.FONT_HERSHEY_SIMPLEX, scale,
                (255, 255, 255), thick, cv2.LINE_AA)  # fmt: skip


def stream_once(ffmpeg_url, width, height, blur):
    """Run one camera -> blur -> ffmpeg session until something exits."""
    # Buffered stdout, so read(n) returns a whole frame rather than whatever
    # the pipe holds. The camera's own log goes to the journal.
    cam = subprocess.Popen(camera_cmd(width, height), stdout=subprocess.PIPE)
    enc = subprocess.Popen(ffmpeg_cmd(ffmpeg_url, width, height), stdin=subprocess.PIPE)
    reader = LatestFrame(cam.stdout, width, height)
    reader.start()
    seq, n, faces, t0, slow = 0, 0, 0, time.monotonic(), 0.0
    last_snap = 0.0
    try:
        while enc.poll() is None:
            frame, seq = reader.get(seq)
            if frame is None:
                print("Camera stopped delivering frames", flush=True)
                break
            t = time.monotonic()
            try:
                faces += blur(frame)
            except Exception as e:  # never send a frame that was not blurred
                print(f"Frame dropped, blur failed: {e}", flush=True)
                continue
            if TIMESTAMP_OVERLAY:
                draw_timestamp(frame)
            slow = max(slow, time.monotonic() - t)
            enc.stdin.write(frame.tobytes())
            n += 1
            if SNAPSHOT_PATH and time.monotonic() - last_snap >= SNAPSHOT_SEC:
                last_snap = time.monotonic()
                cv2.imwrite(SNAPSHOT_PATH + ".tmp.jpg", frame)
                os.replace(SNAPSHOT_PATH + ".tmp.jpg", SNAPSHOT_PATH)
            if time.monotonic() - t0 >= 120:
                dt = time.monotonic() - t0
                print(f"{n / dt:.1f} fps out, {faces} face boxes ({blur.summary()}), "
                      f"slowest frame {slow * 1000:.0f} ms", flush=True)  # fmt: skip
                n, faces, t0, slow = 0, 0, time.monotonic(), 0.0
    except BrokenPipeError:
        print("ffmpeg closed its input", flush=True)
    finally:
        for p in (cam, enc):
            if p.poll() is None:
                p.terminate()
        for p in (cam, enc):
            try:
                p.wait(timeout=10)
            except subprocess.TimeoutExpired:
                p.kill()


def main():
    if RESOLUTION not in RESOLUTION_MAP:
        raise SystemExit(f"Invalid RESOLUTION {RESOLUTION!r}")
    if not isinstance(FRAME_RATE, int) or FRAME_RATE <= 0:
        raise SystemExit(f"Invalid FRAME_RATE {FRAME_RATE!r}")
    width, height = RESOLUTION_MAP[RESOLUTION]
    cv2.setNumThreads(CV_THREADS)
    blur = FaceBlur(width, height)  # load before going live: fail closed
    print(f"{RESOLUTION} {width}x{height} @ {FRAME_RATE} fps, sensor mode "
          f"{SENSOR_MODE or 'auto'}, face detection: {blur.describe()}, "
          f"{len(MASK_RECTS)} fixed masks", flush=True)  # fmt: skip

    signal.signal(signal.SIGTERM, lambda *_: sys.exit(0))
    wait_for_camera()
    ffmpeg_url = create_broadcast()
    while True:
        print("Starting stream", flush=True)
        stream_once(ffmpeg_url, width, height, blur)
        print("Stream ended; retrying in 5 s", flush=True)
        time.sleep(5)


if __name__ == "__main__":
    os.chdir(HERE)
    main()
