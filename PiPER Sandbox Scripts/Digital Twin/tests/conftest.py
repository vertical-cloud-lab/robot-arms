import os
import sys
import warnings

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
os.environ.setdefault("MUJOCO_GL", "egl")
warnings.filterwarnings("ignore", category=UserWarning)
