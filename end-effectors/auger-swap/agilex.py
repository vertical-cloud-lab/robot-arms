"""AgileX's own PiPER gripper model (the two-finger gripper), fetched at run time.

AgileX publishes the STEP on its CDN with no licence attached, so, like PR #10's
piper-camera-mount, it is downloaded into the cache rather than committed. The new
sleeves and custom fingers are built in this file's frame, so the real finger, carriage
and linkage spacer are what they are cut from and checked against.

STEP frame (AgileX's): +Y runs from the fingertips toward the arm (J6 face at y = 64.98),
Z is the finger travel, the J6 axis is along Y through (x, z) = (-7.91, 1.92). The +Z
("upper") finger is solids 5-8; the other finger is the same parts turned 180 deg about
the J6 axis. The fingers are modelled 58.38 mm apart (pad to pad at the tip).

Measured here (faces of the STEP, see README):

* carriage: MGN7C block, 17 x 22.5 x 6.5, 4 x M2 tapped 2.5 deep on 12 x 8 mm, centre
  (x, z) = (-7.91, 45.11) as modelled; the finger sits in a 1 mm deep, 17.3 wide slot on it
* linkage pivot: M3 thread (Ø2.5 tap hole, 5.5 deep) in the finger at (-22.56, 46.36),
  with a Ø9 x 4 spacer (Ø4 bore) between the finger and the linkage arm
* finger: 56 wide at the carriage tapering to 20 at the tip, 71 long; its grip face
  steps 2 mm toward the other finger over the last 35 mm (R51.5 bend at y = -42.8, a
  5.1 deg ramp, flat from y = -67.6 to the tip at -77.52), with a 2 mm pad on it
"""
from __future__ import annotations

import hashlib
import os
import urllib.request
from functools import lru_cache
from pathlib import Path

import numpy as np

CACHE = Path(os.path.expanduser("~/.cache/auger-swap/agilex"))
URL = "https://cdn.shopify.com/s/files/1/0673/6848/5000/files/AgileX_Gripper-1-STP.STEP?v=1782224095"
SHA256 = "6e6c9bb04d7e4b3c7ebcd452dd5e730a4eba2af08b1b80f1e1d2607956a5815d"   # as PR #10 fetched it

BODY = (0, 1, 2, 3, 4)          # motor housing, linear rail, finger plate, back cover, flange
UPPER = {"carriage": 5, "pad": 6, "finger": 7, "spacer": 8}
LOWER = {"carriage": 9, "pad": 10, "finger": 11, "spacer": 12}
OPENING_AS_MODELLED = 31.11 - (-27.27)      # pad to pad at the tip
AX_X, AX_Z = -7.91, 1.92                     # J6 axis
FLANGE_Y = 64.98                             # J6 face

# MGN7C carriage and the linkage pivot (upper finger, as modelled)
CARR_C = (-7.91, 45.11)                      # (x, z) centre of the block
CARR_X, CARR_Z = (-16.41, 0.59), (33.86, 56.36)
CARR_FACE_Y = -7.52                          # the block's top face (the finger sits on it)
CARR_HOLES = [(-13.91, 41.11), (-13.91, 49.11), (-1.91, 41.11), (-1.91, 49.11)]   # M2
SLOT_X = (-16.56, 0.74)                      # the 1 mm locating slot in the finger's base
FINGER_BACK_Y = -6.52                        # finger base face outside the slot
PIVOT = (-22.56, 46.36)                      # M3 shoulder screw axis (along Y)
SPACER_Y = (-6.52, -2.52)
TIP_Y = -77.52


def fetch() -> Path:
    CACHE.mkdir(parents=True, exist_ok=True)
    p = CACHE / "AgileX_Gripper.STEP"
    if not p.exists():
        req = urllib.request.Request(URL, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=120) as r:
            p.write_bytes(r.read())
    h = hashlib.sha256(p.read_bytes()).hexdigest()
    if h != SHA256:
        print(f"warning: AgileX_Gripper.STEP sha256 {h[:12]} differs from the one measured ({SHA256[:12]})")
    return p


@lru_cache(maxsize=None)
def _solids():
    import cadquery as cq
    return tuple(cq.importers.importStep(str(fetch())).solids().vals())


def solids():
    """The STEP's solids, as fresh copies. OCCT's booleans can raise the tolerances of their
    arguments, so with one shared set a part's cuts depended on what had been built before it:
    built after the main shell, the fixing shell lost its finger clearance (3.9 cm3 overlap)."""
    return tuple(s.copy() for s in _solids())


def finger_solid(clearance: float = 0.0):
    """Upper finger + pad as one solid (as modelled)."""
    s = solids()
    return s[UPPER["finger"]].fuse(s[UPPER["pad"]]).clean()


# STEP frame -> URDF gripper_base / link6 frame (z out of the flange toward the fingertips,
# fingers travel along y, the +Z STEP finger is link7 on -y). Proper rotation, det +1.
R_STEP_TO_BASE = np.array([[-1.0, 0, 0], [0, 0, -1.0], [0, -1.0, 0]])
T_STEP_TO_BASE = np.array([AX_X, AX_Z, FLANGE_Y])


def step_to_base() -> np.ndarray:
    M = np.eye(4)
    M[:3, :3] = R_STEP_TO_BASE
    M[:3, 3] = T_STEP_TO_BASE
    return M


def base_z_of_step_y(y: float) -> float:
    """Distance from the J6 face (link6 z) of a STEP y on the axis."""
    return FLANGE_Y - y


def finger_shift(opening: float) -> float:
    """How far the upper finger moves along +Z (STEP) from its modelled place for a given
    stock pad-to-pad opening; the lower finger moves the same amount the other way."""
    return (opening - OPENING_AS_MODELLED) / 2


def lower_of(M_upper: np.ndarray | None = None) -> np.ndarray:
    """4x4 that turns an upper-finger part into the lower finger's (180 deg about J6)."""
    c = np.array([AX_X, 0.0, AX_Z])
    R = np.diag([-1.0, 1.0, -1.0])
    M = np.eye(4)
    M[:3, :3] = R
    M[:3, 3] = c - R @ c
    return M
