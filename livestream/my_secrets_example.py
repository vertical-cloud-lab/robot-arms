# Copy to my_secrets.py (mode 600) next to device.py. device.py reads it only
# at start, so restart picam-stream.service after editing.

# The lab's streaming Lambda (vertical-cloud-lab/streamingLambda). Its URL is
# the LAMBDA_FUNCTION_URL secret of vertical-cloud-lab/robot-arms.
LAMBDA_FUNCTION_URL = "https://<id>.lambda-url.<region>.on.aws/"

# Broadcast title is "<WORKFLOW_NAME> stream <CAM_NAME>, <time>". The Lambda
# files it into the first playlist whose title contains WORKFLOW_NAME, making
# "<WORKFLOW_NAME> Livestreams Playlist" (with this PRIVACY_STATUS) if there is
# none. "end" ends every live broadcast whose title contains WORKFLOW_NAME
# (case-insensitive substring), so no device's WORKFLOW_NAME may appear in
# another's titles. The cell's cameras use:
# - mpzy (front-left post): "PiPER arm front cam"
# - eufi (back post):       "PiPER arm back cam"
# Never use plain "PiPER arm": its "end" would end both of those.
CAM_NAME = "picam"
WORKFLOW_NAME = "PiPER arm front cam"

# "private", "unlisted" or "public".
PRIVACY_STATUS = "public"

RESOLUTION = "720p"  # 144p, 240p, 360p, 480p, 720p, 1080p
FRAME_RATE = 5  # what two face detectors on every frame leave room for on 2 cores
SENSOR_MODE = "2304:1296"  # full-field binned imx708 mode; None lets rpicam pick
CAMERA_VFLIP = False
CAMERA_HFLIP = False
TIMESTAMP_OVERLAY = True
VIDEO_BITRATE = "1500k"

# Face blurring, on the Pi, before encoding. Every frame is checked by each
# detector listed and every box found is pixelated; there is no switch to turn
# it off (an empty or unknown list refuses to stream).
FACE_DETECTORS = ("centerface", "yunet")
# deface's CenterFace (pip deface, see requirements-deface.txt)
CENTERFACE_WIDTH = 640  # detector input width
CENTERFACE_THRESHOLD = 0.2  # deface's default; lower blurs more
# OpenCV YuNet
FACE_DETECT_WIDTH = 960  # detector input width; larger finds smaller faces, costs CPU
FACE_SCORE_THRESHOLD = 0.5  # lower blurs more (and more false positives)
FACE_BOX_MARGIN = 0.6  # grow each face box by this fraction of its size
FACE_HOLD_FRAMES = 8  # keep blurring a face this many frames after it was last seen

# Always-pixelated rectangles, (x0, y0, x1, y1) as fractions of the frame, for
# parts of the view that look past the cell into the lab. They belong to one
# camera's view, so redo them whenever the camera or its mount changes.
# - mpzy's camera (front-left post, looking into the cell) sees only the cell,
#   the backdrop and the wall: no masks.
# - eufi's camera (back-right post, as of 2026-11-03) sees the lab in its
#   top-left third, which takes these two:
#   [(0.0, 0.0, 0.345, 0.34), (0.0, 0.34, 0.2, 0.62)]
MASK_RECTS = []

# Fixed objects in a view that look like faces to the detectors, (x0, y0, x1,
# y1) fractions of the frame. A box centred in one is blurred only if it scores
# at least STRICT_THRESHOLDS for its detector (default: centerface 0.6, yunet
# 0.7, against 0.2 and 0.5 everywhere else). Keep them tight around the object,
# and redo them whenever the camera or the object moves. As of 2026-11-04, both
# views have one, over the A1 mini's AMS lite feeders (dark housing, two orange
# couplers for eyes; CenterFace up to 0.43, YuNet up to 0.54):
# - mpzy: [(0.355, 0.208, 0.461, 0.347)]
# - eufi: [(0.512, 0.25, 0.617, 0.368)]
STRICT_RECTS = []
# STRICT_THRESHOLDS = {"centerface": 0.6, "yunet": 0.7}

CV_THREADS = 2  # OpenCV threads; the streaming Pi also drives the arm
SNAPSHOT_PATH = "/tmp/picam-stream-latest.jpg"  # last frame sent, every SNAPSHOT_SEC
SNAPSHOT_SEC = 30
# A restart goes back to the broadcast that was live, keeping its link, if a
# frame went out less than this many seconds before; 0 always starts a new one.
# The broadcast and its stream key are kept in BROADCAST_STATE (mode 600).
BROADCAST_REUSE_SEC = 600
# BROADCAST_STATE = "/home/<user>/picam-stream/broadcast.json"
