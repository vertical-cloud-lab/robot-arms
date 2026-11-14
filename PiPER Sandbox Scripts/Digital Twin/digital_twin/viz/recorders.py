"""Watching a simulation: the live viewer (on your machine) and video files (anywhere).

    LiveViewer(sim)            MuJoCo's interactive window, kept in step with sim time
                               (drag to orbit, right-drag to pan, scroll to zoom, double-click
                               a body to track it; Ctrl+right-drag pushes things)
    VideoRecorder(sim, path)   renders a camera (mpzy by default) or an orbiting free camera
                               into an .mp4 (needs imageio + imageio-ffmpeg) or a .gif

Both attach to robot.on_frame, so every move the planner makes is shown. The kinematic
engine has no renderer of its own; recorders fall back to viz/matplotlib_view.py for it.
"""
from __future__ import annotations

import os
import time

import numpy as np


class LiveViewer:
    def __init__(self, sim, speed: float = 1.0):
        self.sim, self.speed = sim, speed
        self.handle = sim.engine.launch_viewer()
        if self.handle is None:
            from .matplotlib_view import MatplotlibView
            self.handle = MatplotlibView(sim)
        self.t0_wall, self.t0_sim = time.time(), sim.engine.time

    def __call__(self, robot):
        if hasattr(self.handle, "is_running") and not self.handle.is_running():
            raise KeyboardInterrupt("viewer closed")
        self.handle.sync()
        ahead = (self.sim.engine.time - self.t0_sim) / self.speed - (time.time() - self.t0_wall)
        if ahead > 0:
            time.sleep(ahead)

    def attach(self, fps: float = 60):
        self.sim.robot.on_frame.append(self)
        self.sim.robot.frame_every = 1 / fps
        return self


class VideoRecorder:
    def __init__(self, sim, path: str, camera: str = "mpzy", width: int = 960, height: int = 540,
                 fps: int = 30, speed: float = 1.0, overlay: bool = True):
        self.sim, self.path, self.camera = sim, path, camera
        self.width, self.height, self.fps, self.speed = width, height, fps, speed
        self.overlay = overlay
        self.frames = []
        self._mpl = None

    def _render(self):
        e = self.sim.engine
        if self.camera == "orbit" and hasattr(e, "free_camera"):
            az = -150 + 20 * np.sin(e.time / 12)
            cam = e.free_camera(lookat=[-0.12, 0.05, 0.12], distance=1.15, azimuth=az, elevation=-28)
            img = e.render(cam, self.width, self.height)
        else:
            img = e.render(self.camera, self.width, self.height)
        if img is None:  # engine without a renderer: draw it with matplotlib
            if self._mpl is None:
                from .matplotlib_view import MatplotlibView
                self._mpl = MatplotlibView(self.sim, show=False, size=(self.width, self.height))
            img = self._mpl.image()
        if self.overlay:
            img = self._stamp(img)
        return img

    def _stamp(self, img):
        try:
            import cv2
        except ImportError:
            return img
        img = np.ascontiguousarray(img)
        e = self.sim.engine
        log = self.sim.robot.log
        last = log[-1]["move"] if log else ""
        text = f"t = {e.time:5.1f} s   {last}"
        img[:36] = (img[:36] * 0.35).astype(img.dtype)
        cv2.putText(img, text, (12, 25), cv2.FONT_HERSHEY_SIMPLEX, 0.62, (255, 255, 255), 1, cv2.LINE_AA)
        return img

    def __call__(self, robot):
        self.frames.append(self._render())

    def attach(self):
        self.sim.robot.on_frame.append(self)
        self.sim.robot.frame_every = self.speed / self.fps
        return self

    def save(self):
        import imageio
        os.makedirs(os.path.dirname(os.path.abspath(self.path)), exist_ok=True)
        if self.path.endswith(".gif"):
            imageio.mimsave(self.path, self.frames, duration=1000 / self.fps, loop=0)
        else:
            imageio.mimsave(self.path, self.frames, fps=self.fps, macro_block_size=8, quality=7)
        return self.path
