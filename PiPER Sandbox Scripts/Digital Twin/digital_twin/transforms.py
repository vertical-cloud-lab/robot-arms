"""Small SE(3) helpers shared by every module (numpy only).

Poses are 4x4 homogeneous matrices. Quaternions are (w, x, y, z), MuJoCo's order.
"""
from __future__ import annotations

import numpy as np


def rot_x(a: float) -> np.ndarray:
    c, s = np.cos(a), np.sin(a)
    return np.array([[1, 0, 0], [0, c, -s], [0, s, c]])


def rot_y(a: float) -> np.ndarray:
    c, s = np.cos(a), np.sin(a)
    return np.array([[c, 0, s], [0, 1, 0], [-s, 0, c]])


def rot_z(a: float) -> np.ndarray:
    c, s = np.cos(a), np.sin(a)
    return np.array([[c, -s, 0], [s, c, 0], [0, 0, 1]])


def euler_xyz(rx: float, ry: float, rz: float) -> np.ndarray:
    """Rotation for intrinsic x, then y, then z angles (rad): R = Rx @ Ry @ Rz."""
    return rot_x(rx) @ rot_y(ry) @ rot_z(rz)


def make_pose(R: np.ndarray | None = None, p=(0.0, 0.0, 0.0)) -> np.ndarray:
    T = np.eye(4)
    if R is not None:
        T[:3, :3] = R
    T[:3, 3] = p
    return T


def pose_xyz_yaw(x: float, y: float, z: float, yaw: float) -> np.ndarray:
    return make_pose(rot_z(yaw), (x, y, z))


def inv(T: np.ndarray) -> np.ndarray:
    R, p = T[:3, :3], T[:3, 3]
    out = np.eye(4)
    out[:3, :3] = R.T
    out[:3, 3] = -R.T @ p
    return out


def mat_to_quat(R: np.ndarray) -> np.ndarray:
    """3x3 rotation -> unit quaternion (w, x, y, z), with w >= 0."""
    R = np.asarray(R, float)
    tr = np.trace(R)
    if tr > 0:
        s = np.sqrt(tr + 1.0) * 2
        q = [0.25 * s, (R[2, 1] - R[1, 2]) / s, (R[0, 2] - R[2, 0]) / s, (R[1, 0] - R[0, 1]) / s]
    elif R[0, 0] > R[1, 1] and R[0, 0] > R[2, 2]:
        s = np.sqrt(1.0 + R[0, 0] - R[1, 1] - R[2, 2]) * 2
        q = [(R[2, 1] - R[1, 2]) / s, 0.25 * s, (R[0, 1] + R[1, 0]) / s, (R[0, 2] + R[2, 0]) / s]
    elif R[1, 1] > R[2, 2]:
        s = np.sqrt(1.0 + R[1, 1] - R[0, 0] - R[2, 2]) * 2
        q = [(R[0, 2] - R[2, 0]) / s, (R[0, 1] + R[1, 0]) / s, 0.25 * s, (R[1, 2] + R[2, 1]) / s]
    else:
        s = np.sqrt(1.0 + R[2, 2] - R[0, 0] - R[1, 1]) * 2
        q = [(R[1, 0] - R[0, 1]) / s, (R[0, 2] + R[2, 0]) / s, (R[1, 2] + R[2, 1]) / s, 0.25 * s]
    q = np.array(q)
    q /= np.linalg.norm(q)
    return q if q[0] >= 0 else -q


def quat_to_mat(q) -> np.ndarray:
    w, x, y, z = np.asarray(q, float) / np.linalg.norm(q)
    return np.array([
        [1 - 2 * (y * y + z * z), 2 * (x * y - z * w), 2 * (x * z + y * w)],
        [2 * (x * y + z * w), 1 - 2 * (x * x + z * z), 2 * (y * z - x * w)],
        [2 * (x * z - y * w), 2 * (y * z + x * w), 1 - 2 * (x * x + y * y)],
    ])


def rotvec(R: np.ndarray) -> np.ndarray:
    """Axis * angle (rad) of a rotation matrix (log map)."""
    c = np.clip((np.trace(R) - 1) / 2, -1.0, 1.0)
    a = np.arccos(c)
    if a < 1e-9:
        return np.zeros(3)
    if np.pi - a < 1e-6:  # 180 deg: axis from the symmetric part
        w, v = np.linalg.eigh(R)
        axis = v[:, np.argmax(w)]
        return axis * a
    return a / (2 * np.sin(a)) * np.array([R[2, 1] - R[1, 2], R[0, 2] - R[2, 0], R[1, 0] - R[0, 1]])


def axis_angle(axis, a: float) -> np.ndarray:
    """Rotation matrix about a unit axis by angle a (Rodrigues)."""
    k = np.asarray(axis, float)
    k = k / np.linalg.norm(k)
    K = np.array([[0, -k[2], k[1]], [k[2], 0, -k[0]], [-k[1], k[0], 0]])
    return np.eye(3) + np.sin(a) * K + (1 - np.cos(a)) * K @ K


def normal_to_rot(normal: str) -> np.ndarray:
    """Rotation whose z axis points along a named axis ('+z', '-y', ...): for flat tags."""
    table = {
        "+z": np.eye(3),
        "-z": rot_x(np.pi),
        "+y": rot_x(-np.pi / 2),
        "-y": rot_x(np.pi / 2),
        "+x": rot_y(np.pi / 2) @ rot_z(np.pi / 2),
        "-x": rot_y(-np.pi / 2) @ rot_z(-np.pi / 2),
    }
    return table[normal.strip()]


def slerp_rot(R0: np.ndarray, R1: np.ndarray, s: float) -> np.ndarray:
    """Rotation a fraction s of the way from R0 to R1 (geodesic)."""
    rv = rotvec(R0.T @ R1)
    ang = np.linalg.norm(rv)
    if ang < 1e-12:
        return R0.copy()
    return R0 @ axis_angle(rv / ang, ang * s)
