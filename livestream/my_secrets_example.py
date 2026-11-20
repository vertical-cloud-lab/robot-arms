# Copy to my_secrets.py (mode 600) next to device.py. device.py reads it only
# at start, so restart picam-stream.service after editing. On a Pi with more
# than one camera, copy it to my_secrets_<name>.py for each camera instead, set
# CAMERA_SENSOR in each, and run picam-stream@<name>.service for each.

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
# - 76zj (gripper):         "PiPER arm gripper wide cam" (my_secrets_wide.py)
#                           "PiPER arm gripper HQ cam" (my_secrets_hq.py)
# Never use plain "PiPER arm": its "end" would end all of those.
CAM_NAME = "picam"
WORKFLOW_NAME = "PiPER arm front cam"

# "private", "unlisted" or "public". All four cameras are public, with face
# blurring on every frame (76zj's gripper cameras since 2026-11-05; they were
# unlisted at first, since they move and can look into the lab).
PRIVACY_STATUS = "public"

# The camera, by the sensor name `rpicam-hello --list-cameras` prints, or None
# for the first camera. Set it on a Pi with two cameras (76zj: "imx708_wide"
# and "imx477"): libcamera renumbers them when one is missing.
CAMERA_SENSOR = None

RESOLUTION = "720p"  # 144p, 240p, 360p, 480p, 720p, 1080p
FRAME_RATE = 5  # what two face detectors on every frame leave room for on 2 cores
# Full-field binned imx708 mode; None lets rpicam pick. The picture keeps the
# mode's shape, so the whole mode is shown: a mode of another shape than the
# stream's gets black bars. For the imx477 (HQ Camera) use "2028:1520", its
# full-field 4:3 mode; its 16:9 "2028:1080" leaves out the top and bottom 15%.
SENSOR_MODE = "2304:1296"
CAMERA_VFLIP = False
CAMERA_HFLIP = False
# Degrees clockwise to turn the picture, for a camera mounted on its side or
# upside down: 0, 90, 180 or 270. Turned on its side, a 16:9 stream shows it
# upright with black bars at the sides. 76zj's HQ camera: 270 (a quarter turn
# anticlockwise), with SENSOR_MODE "2028:1520".
CAMERA_ROTATION = 0
TIMESTAMP_OVERLAY = True
VIDEO_BITRATE = "1500k"

# Face blurring, on the Pi, before encoding. Every frame is checked by each
# detector listed and every box found is pixelated; there is no switch to turn
# it off (an empty or unknown list refuses to stream).
FACE_DETECTORS = ("centerface", "yunet")
# deface's CenterFace (pip deface, see requirements-deface.txt)
CENTERFACE_WIDTH = 640  # detector input width (its longer side, for a portrait picture)
CENTERFACE_THRESHOLD = 0.2  # deface's default; lower blurs more
# OpenCV YuNet
FACE_DETECT_WIDTH = 960  # the same for YuNet; larger finds smaller faces, costs CPU
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
# Last frame sent, every SNAPSHOT_SEC. Defaults to /tmp/picam-stream-latest.jpg,
# or /tmp/picam-stream-<name>-latest.jpg for picam-stream@<name>.service, so
# leave it unset on a Pi with two streams.
# SNAPSHOT_PATH = "/tmp/picam-stream-latest.jpg"
SNAPSHOT_SEC = 30
# A restart goes back to the broadcast that was live, keeping its link, if a
# frame went out less than this many seconds before; 0 always starts a new one.
# The broadcast and its stream key are kept in BROADCAST_STATE (mode 600).
BROADCAST_REUSE_SEC = 600
# BROADCAST_STATE = "/home/<user>/picam-stream/broadcast.json"  (broadcast-<name>.json
# for picam-stream@<name>.service)
