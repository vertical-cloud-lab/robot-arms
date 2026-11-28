"""A simulated cell for --dry-run and the tests, so the whole workflow runs with no arm and no
camera: Arm Control/fake_piper.py's simulated PiPER, plus
- an auger the gripper can hold: closing on it stops the fingers at the tube, it then moves
  with the gripper, and opening drops it, into the box or not;
- the holder and the box, with their AprilTags where settings.py says they are;
- a camera (settings' guess of mpzy's) that renders what it would see, so the real tag
  detection and location code runs on it.
Nothing here is used on the real arm.
"""
import math
import os
import sys

import numpy as np

import kinematics as K
import settings as S
import vision as V

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(HERE), "Arm Control"))
from fake_piper import FakePiper  # noqa: E402

TUBE_READING = S.GRIPPER_CLOSED_READING_MM + S.AUGER_TUBE_DIAMETER_MM


class SimCell:
    """holder, box: (x, y, z, yaw) of the holder frame (z = the auger's axis) and the box
    frame (z = its inside floor), arm frame; box None = no box. auger: "holder" or "missing".
    stuck: the auger won't come out of the clips (the grip slips). scale: rendered image size
    relative to the real camera's (smaller is faster)."""

    def __init__(self, spot="1", holder=None, holder_z=60.0, box=None, box_z=3.0,
                 auger="holder", stuck=False, scale=0.5, cal_tag=False):
        h = holder or S.HOLDER_EXPECTED
        self.holder = V.Found(h[0], h[1], holder_z, h[2], [], 0.0)
        b = box if box is not None else S.SPOTS.get(spot)
        self.box = None if b is False or b is None else V.Found(b[0], b[1], box_z, b[2], [], 0.0)
        self.auger = auger          # "holder", "held", "box", "dropped" or "missing"
        self.auger_pose = None      # (middle, axis toward the gear end) once out of the holder
        self.held = None            # (axis, middle) in the flange frame while held
        self.stuck = stuck
        self.camera = V.Camera.nominal(scale)
        self.cal_tag = cal_tag      # show calibrate.py's card on the gripper
        # calibrate.py's card: held between the fingers, so it lies across their closing
        # line, its two tags centred 80 mm below the fingertips, one on each face
        f = np.array(K.FINGER_AXIS)
        down = np.array([0.0, 0.0, 1.0])       # the tool's axis, flange frame
        self.cal_tags_in_flange = {}
        for i, normal in zip(S.CAL_TAG_IDS, (f, -f)):
            top = -down                        # the tag's top edge toward the gripper
            T = np.eye(4)
            T[:3, :3] = np.column_stack([np.cross(top, normal), top, normal])
            T[:3, 3] = down * (S.FINGERTIP_MM + 80.0) + normal * 1.5
            self.cal_tags_in_flange[i] = T
        self.piper = None

    def make_arm(self):
        self.piper = SimPiper(self)
        return self.piper

    def reset(self):
        """What the operator does between runs: the auger back in its holder, the box empty."""
        if self.auger != "missing":
            self.auger, self.auger_pose, self.held = "holder", None, None

    # ---------------------------------------------------------------- the camera
    def tags(self):
        """(id, size, 4x4 pose) of every tag the camera could see."""
        out = []
        for obj, tags, size in ((self.holder, S.HOLDER_TAGS, S.HOLDER_TAG_SIZE_MM),
                                (self.box, S.BOX_TAGS, S.BOX_TAG_SIZE_MM)):
            if obj is None:
                continue
            for i, p in tags.items():
                out.append((i, size, V.flat_tag_pose(*obj.to_arm(p), obj.yaw)))
        if S.AUGER_TAG and self.auger != "missing":
            mid, axis = self.auger_now()
            yaw = math.degrees(math.atan2(axis[1], axis[0]))
            x, y, z = S.AUGER_TAG["pos"]
            c, s = math.cos(math.radians(yaw)), math.sin(math.radians(yaw))
            out.append((S.AUGER_TAG["id"], S.AUGER_TAG["size_mm"], V.flat_tag_pose(
                mid[0] + c * x - s * y, mid[1] + s * x + c * y, mid[2] + z, yaw)))
        if self.cal_tag and self.piper is not None:
            R, flange = K.UD.fk(self.piper_joints())
            T = np.eye(4)
            T[:3, :3], T[:3, 3] = np.array(R), flange
            for i, tag in self.cal_tags_in_flange.items():
                out.append((i, S.CAL_TAG_SIZE_MM, T @ tag))
        return out

    def capture(self, path=None):
        image = V.render(self.camera, self.tags())
        if path:
            import cv2
            cv2.imwrite(path, image)
        return image

    # ---------------------------------------------------------------- the auger
    def piper_joints(self):
        return K.UD.joints_deg(self.piper)

    def auger_now(self):
        """(middle, unit axis toward the gear end) of the auger, arm frame."""
        if self.auger == "holder":
            return self.holder.to_arm((0, 0, 0)), self.holder.axis()
        if self.auger == "held":
            R, p = K.tool(self.piper_joints())
            axis, mid = self.held
            return ([p[i] + K.dot(R[i], mid) for i in range(3)], [K.dot(R[i], axis)
                                                                   for i in range(3)])
        return self.auger_pose

    def try_grab(self):
        """The gripper is closing: is the tube between the fingers? Then it is held."""
        if self.auger not in ("holder", "box", "dropped"):
            return False
        mid, axis = self.auger_now()
        R, p = K.tool(self.piper_joints())
        rel = [a - b for a, b in zip(p, mid)]
        along = K.dot(rel, axis)
        across = math.dist(rel, [along * a for a in axis])
        crossing = abs(K.wrap90(K.finger_yaw(self.piper_joints())
                                - math.degrees(math.atan2(axis[1], axis[0])) - 90))
        if across > 6.0 or abs(along) > S.AUGER_LENGTH_MM / 2 - 20 or crossing > 15:
            return False
        Rt = [[R[j][i] for j in range(3)] for i in range(3)]  # R transposed
        self.held = ([K.dot(Rt[i], axis) for i in range(3)],
                     [K.dot(Rt[i], [a - b for a, b in zip(mid, p)]) for i in range(3)])
        self.from_holder = self.auger == "holder"
        self.grab_z = p[2]
        self.auger = "held"
        return True

    def slipped(self):
        """A stuck auger: once the gripper has pulled 10 mm, it slips off, still in the clips."""
        if self.auger == "held" and self.stuck and self.from_holder:
            if K.tcp(self.piper_joints())[2] > self.grab_z + 10:
                self.auger, self.held = "holder", None
                return True
        return False

    def release(self):
        """The gripper opened: the auger drops straight down, into the box or not (or, let go
        before it was lifted, stays in the holder's clips)."""
        mid, axis = self.auger_now()
        self.held = None
        if self.from_holder and K.tcp(self.piper_joints())[2] < self.grab_z + 5:
            self.auger = "holder"
            return
        ok = False
        if self.box is not None:
            c, s = math.cos(math.radians(self.box.yaw)), math.sin(math.radians(self.box.yaw))
            inside = []
            for end in (-1, 1):  # both ends of the auger inside the box's inside, seen from above
                p = [mid[i] + end * S.AUGER_LENGTH_MM / 2 * axis[i] for i in range(3)]
                dx, dy = p[0] - self.box.x, p[1] - self.box.y
                bx, by = c * dx + s * dy, -s * dx + c * dy
                inside.append(abs(bx) <= S.BOX_INSIDE_MM[0] / 2
                              and abs(by) <= (S.BOX_INSIDE_MM[1] - S.AUGER_TUBE_DIAMETER_MM) / 2)
            low = mid[2] - S.AUGER_GEAR_DIAMETER_MM / 2 - self.box.z
            ok = all(inside) and -1.0 <= low <= S.BOX_WALL_HEIGHT_MM
        if ok:
            self.auger, self.auger_pose = "box", ([mid[0], mid[1], self.box.z
                                                  + S.AUGER_GEAR_DIAMETER_MM / 2], axis)
        else:
            self.auger, self.auger_pose = "dropped", ([mid[0], mid[1], 12.5], axis)


class SimPiper(FakePiper):
    """fake_piper's arm, whose gripper closes on the cell's auger."""

    def __init__(self, cell):
        super().__init__()
        self.cell = cell
        with self.lock:
            self.grip = self.grip_cmd = 80.0  # a reading the real gripper could have
        self.requested = 80.0

    def GripperCtrl(self, gripper_angle=0, gripper_effort=0, gripper_code=0, set_zero=0):
        cmd = gripper_angle / 1000
        self.requested = cmd
        cell = self.cell
        if cell.auger == "held" and cmd > TUBE_READING + 2:
            cell.release()
        elif cmd < TUBE_READING and cell.auger != "held":
            cell.try_grab()
        if cell.auger == "held":
            cmd = max(cmd, TUBE_READING)  # the fingers stop on the tube
        super().GripperCtrl(round(cmd * 1000), gripper_effort, gripper_code, set_zero)

    def JointCtrl(self, *mdeg):
        self.check_slip()
        super().JointCtrl(*mdeg)

    def GetArmGripperMsgs(self):
        self.check_slip()
        return super().GetArmGripperMsgs()

    def check_slip(self):
        if self.cell.slipped():  # the fingers close on through where the tube was
            with self.lock:
                self.grip_cmd = max(0.0, self.requested)
