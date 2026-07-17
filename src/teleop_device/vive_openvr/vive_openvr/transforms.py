"""Transform helpers for OpenVR matrices."""

from __future__ import annotations

from typing import Any

import numpy as np


ROLE_CORRECTIONS = {
    "chest": np.array(
        [
            [1.0, 0.0, 0.0, 0.0],
            [0.0, 0.0, 1.0, 0.0],
            [0.0, -1.0, 0.0, 0.0],
            [0.0, 0.0, 0.0, 1.0],
        ],
        dtype=np.float64,
    ),
    "right_wrist": np.array(
        [
            [0.0, 0.0, -1.0, 0.0],
            [1.0, 0.0, 0.0, 0.0],
            [0.0, -1.0, 0.0, 0.0],
            [0.0, 0.0, 0.0, 1.0],
        ],
        dtype=np.float64,
    ),
    "left_wrist": np.array(
        [
            [0.0, 0.0, -1.0, 0.0],
            [-1.0, 0.0, 0.0, 0.0],
            [0.0, 1.0, 0.0, 0.0],
            [0.0, 0.0, 0.0, 1.0],
        ],
        dtype=np.float64,
    ),
}


def pose_matrix_to_numpy(pose_matrix: Any) -> np.ndarray:
    """Convert an OpenVR HmdMatrix34_t into a 4x4 homogeneous matrix."""

    mat = np.eye(4, dtype=np.float64)
    for row in range(3):
        for col in range(3):
            mat[row, col] = float(pose_matrix.m[row][col])
        mat[row, 3] = float(pose_matrix.m[row][3])
    return mat


def matrix_to_quaternion(matrix: np.ndarray) -> tuple[float, float, float, float]:
    """Convert a 3x3 rotation matrix to a ROS quaternion tuple (x, y, z, w)."""

    rotation = matrix[:3, :3]
    trace = float(np.trace(rotation))

    if trace > 0.0:
        scale = np.sqrt(trace + 1.0) * 2.0
        w = 0.25 * scale
        x = (rotation[2, 1] - rotation[1, 2]) / scale
        y = (rotation[0, 2] - rotation[2, 0]) / scale
        z = (rotation[1, 0] - rotation[0, 1]) / scale
    elif rotation[0, 0] > rotation[1, 1] and rotation[0, 0] > rotation[2, 2]:
        scale = np.sqrt(1.0 + rotation[0, 0] - rotation[1, 1] - rotation[2, 2]) * 2.0
        w = (rotation[2, 1] - rotation[1, 2]) / scale
        x = 0.25 * scale
        y = (rotation[0, 1] + rotation[1, 0]) / scale
        z = (rotation[0, 2] + rotation[2, 0]) / scale
    elif rotation[1, 1] > rotation[2, 2]:
        scale = np.sqrt(1.0 + rotation[1, 1] - rotation[0, 0] - rotation[2, 2]) * 2.0
        w = (rotation[0, 2] - rotation[2, 0]) / scale
        x = (rotation[0, 1] + rotation[1, 0]) / scale
        y = 0.25 * scale
        z = (rotation[1, 2] + rotation[2, 1]) / scale
    else:
        scale = np.sqrt(1.0 + rotation[2, 2] - rotation[0, 0] - rotation[1, 1]) * 2.0
        w = (rotation[1, 0] - rotation[0, 1]) / scale
        x = (rotation[0, 2] + rotation[2, 0]) / scale
        y = (rotation[1, 2] + rotation[2, 1]) / scale
        z = 0.25 * scale

    quat = np.array([x, y, z, w], dtype=np.float64)
    norm = np.linalg.norm(quat)
    if norm > 0.0:
        quat /= norm
    return (float(quat[0]), float(quat[1]), float(quat[2]), float(quat[3]))


def child_frame_id(prefix: str, role: str) -> str:
    """Build a TF child frame name without a leading slash."""

    clean_prefix = prefix.strip().strip("/")
    clean_role = role.strip().strip("/")
    if clean_prefix:
        return f"{clean_prefix}/{clean_role}"
    return clean_role
