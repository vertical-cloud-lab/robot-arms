# Copy to my_secrets.py (mode 600) next to device.py. device.py reads it only
# at start, so restart picam-stream.service after editing.

# The lab's streaming Lambda (vertical-cloud-lab/streamingLambda). Its URL is
# the LAMBDA_FUNCTION_URL secret of vertical-cloud-lab/robot-arms.
LAMBDA_FUNCTION_URL = "https://<id>.lambda-url.<region>.on.aws/"

# Broadcast title is "<WORKFLOW_NAME> stream <CAM_NAME>, <time>". The Lambda
# files it into the "<WORKFLOW_NAME> Livestreams Playlist", and "end" ends every
# live broadcast whose title contains WORKFLOW_NAME (case-insensitive
# substring), so it must not be a substring of another device's workflow.
CAM_NAME = "picam-piper"
WORKFLOW_NAME = "PiPER arm"

# "private", "unlisted" or "public".
PRIVACY_STATUS = "unlisted"

RESOLUTION = "720p"  # 144p, 240p, 360p, 480p, 720p, 1080p
FRAME_RATE = 10
SENSOR_MODE = "2304:1296"  # full-field binned imx708 mode; None lets rpicam pick
CAMERA_VFLIP = False
CAMERA_HFLIP = False
TIMESTAMP_OVERLAY = True
VIDEO_BITRATE = "1500k"

# Face blurring (OpenCV YuNet). Every frame is checked; there is no switch to
# turn it off.
FACE_DETECT_WIDTH = 960  # detector input width; larger finds smaller faces, costs CPU
FACE_SCORE_THRESHOLD = 0.5  # lower blurs more (and more false positives)
FACE_BOX_MARGIN = 0.6  # grow each face box by this fraction of its size
FACE_HOLD_FRAMES = 8  # keep blurring a face this many frames after it was last seen

# Always-pixelated rectangles, (x0, y0, x1, y1) as fractions of the frame.
# With the full-field sensor mode, the PiPER camera's top-left third looks past
# the cell into the lab (benches, the floor, people walking by). The first
# rectangle covers the room above the bench; the second the floor on the left.
MASK_RECTS = [(0.0, 0.0, 0.345, 0.34), (0.0, 0.34, 0.2, 0.62)]

CV_THREADS = 2  # OpenCV threads; the arm Pi also runs the arm
SNAPSHOT_PATH = "/tmp/picam-stream-latest.jpg"  # last frame sent, every SNAPSHOT_SEC
SNAPSHOT_SEC = 30
