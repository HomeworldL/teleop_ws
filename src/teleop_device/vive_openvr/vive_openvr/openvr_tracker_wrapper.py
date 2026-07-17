"""Small OpenVR wrapper for HTC Vive Tracker poses."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

import numpy as np

from .transforms import ROLE_CORRECTIONS, pose_matrix_to_numpy

try:
    import openvr
except ImportError:  # pragma: no cover - depends on host SteamVR setup
    openvr = None


TRACKER_CLASS_NAME = "GenericTracker"


@dataclass(frozen=True)
class TrackedDevice:
    """A SteamVR tracked device discovered through OpenVR."""

    index: int
    device_class: int
    device_class_name: str
    serial: str


@dataclass(frozen=True)
class TrackedDeviceStatus:
    """Pose validity status for one OpenVR tracked device."""

    connected: bool
    pose_valid: bool
    tracking_result: int
    tracking_result_name: str
    position: Optional[tuple[float, float, float]]


def require_openvr():
    """Return the imported openvr module or raise a useful runtime error."""

    if openvr is None:
        raise RuntimeError(
            "Python package 'openvr' is not installed. Install pyopenvr in the "
            "active ROS environment, then make sure SteamVR is running."
        )
    return openvr


def _device_class_name(vr_module, device_class: int) -> str:
    names = {
        getattr(vr_module, "TrackedDeviceClass_HMD", -1): "HMD",
        getattr(vr_module, "TrackedDeviceClass_Controller", -1): "Controller",
        getattr(vr_module, "TrackedDeviceClass_GenericTracker", -1): TRACKER_CLASS_NAME,
        getattr(vr_module, "TrackedDeviceClass_TrackingReference", -1): "TrackingReference",
    }
    return names.get(device_class, str(device_class))


def _tracking_result_name(vr_module, tracking_result: int) -> str:
    for name in dir(vr_module):
        if name.startswith("TrackingResult_") and getattr(vr_module, name) == tracking_result:
            return name.removeprefix("TrackingResult_")
    return str(tracking_result)


class OpenVRTrackerWrapper:
    """Connect to SteamVR and return corrected tracker poses by configured role."""

    def __init__(
        self,
        tracker_serials: dict[str, str],
        wrist_offsets: Optional[dict[str, list[float]]] = None,
        apply_role_corrections: bool = True,
    ):
        self._openvr = require_openvr()
        self._tracker_serials = {
            role: serial
            for role, serial in tracker_serials.items()
            if serial and not str(serial).startswith("LHR-XXXXXXXX")
        }
        self._wrist_offsets = {
            role: np.array(offset, dtype=np.float64)
            for role, offset in (wrist_offsets or {}).items()
            if offset is not None
        }
        self._apply_role_corrections = apply_role_corrections
        self._vr_system = None
        self._detected: dict[int, str] = {}
        self._connected = False
        self._connect()

    def _connect(self) -> None:
        self._openvr.init(self._openvr.VRApplication_Other)
        self._vr_system = self._openvr.VRSystem()
        self._connected = True
        self.refresh_tracker_mapping()

    def refresh_tracker_mapping(self) -> None:
        """Rebuild OpenVR device-index to configured-role mapping."""

        serial_to_index = {}
        for device in self.list_devices(include_all=False):
            serial_to_index[device.serial] = device.index

        detected = {}
        for role, serial in self._tracker_serials.items():
            index = serial_to_index.get(serial)
            if index is not None:
                detected[index] = role
        self._detected = detected

    def list_devices(self, include_all: bool = True) -> list[TrackedDevice]:
        """List tracked devices currently known to SteamVR."""

        if self._vr_system is None:
            raise RuntimeError("OpenVR is not connected")

        devices = []
        for index in range(self._openvr.k_unMaxTrackedDeviceCount):
            device_class = self._vr_system.getTrackedDeviceClass(index)
            if device_class == self._openvr.TrackedDeviceClass_Invalid:
                continue
            class_name = _device_class_name(self._openvr, device_class)
            if not include_all and class_name != TRACKER_CLASS_NAME:
                continue
            serial = self._device_serial(index)
            if not serial:
                continue
            devices.append(
                TrackedDevice(
                    index=index,
                    device_class=device_class,
                    device_class_name=class_name,
                    serial=serial,
                )
            )
        return devices

    def device_statuses(self) -> dict[int, TrackedDeviceStatus]:
        """Return connection and pose validity status keyed by OpenVR device index."""

        if self._vr_system is None:
            raise RuntimeError("OpenVR is not connected")

        poses = self._vr_system.getDeviceToAbsoluteTrackingPose(
            self._openvr.TrackingUniverseStanding,
            0.0,
            self._openvr.k_unMaxTrackedDeviceCount,
        )
        statuses = {}
        for index, pose in enumerate(poses):
            position = None
            if pose.bPoseIsValid:
                matrix = pose_matrix_to_numpy(pose.mDeviceToAbsoluteTracking)
                position = (
                    float(matrix[0, 3]),
                    float(matrix[1, 3]),
                    float(matrix[2, 3]),
                )
            statuses[index] = TrackedDeviceStatus(
                connected=bool(pose.bDeviceIsConnected),
                pose_valid=bool(pose.bPoseIsValid),
                tracking_result=int(pose.eTrackingResult),
                tracking_result_name=_tracking_result_name(
                    self._openvr,
                    int(pose.eTrackingResult),
                ),
                position=position,
            )
        return statuses

    def detected_roles(self) -> dict[str, int]:
        """Return configured roles that are currently mapped to an OpenVR index."""

        return {role: index for index, role in self._detected.items()}

    def missing_roles(self) -> dict[str, str]:
        """Return configured roles whose serials are not currently visible."""

        found_roles = set(self._detected.values())
        return {
            role: serial
            for role, serial in self._tracker_serials.items()
            if role not in found_roles
        }

    def get_poses(self) -> dict[str, Optional[np.ndarray]]:
        """Return corrected 4x4 poses keyed by configured role."""

        if not self._connected or self._vr_system is None:
            raise RuntimeError("OpenVR is not connected")

        poses = self._vr_system.getDeviceToAbsoluteTrackingPose(
            self._openvr.TrackingUniverseStanding,
            0.0,
            self._openvr.k_unMaxTrackedDeviceCount,
        )

        result: dict[str, Optional[np.ndarray]] = {}
        for index, role in self._detected.items():
            if index >= len(poses) or not poses[index].bPoseIsValid:
                result[role] = None
                continue

            matrix = pose_matrix_to_numpy(poses[index].mDeviceToAbsoluteTracking)
            offset = self._wrist_offsets.get(role)
            if offset is not None:
                matrix[:3, 3] += matrix[:3, :3] @ offset

            if self._apply_role_corrections:
                correction = ROLE_CORRECTIONS.get(role)
                if correction is not None:
                    matrix = matrix @ correction

            result[role] = matrix

        return result

    def _device_serial(self, index: int) -> Optional[str]:
        try:
            return self._vr_system.getStringTrackedDeviceProperty(
                index,
                self._openvr.Prop_SerialNumber_String,
            )
        except Exception:
            return None

    def shutdown(self) -> None:
        """Close the OpenVR runtime connection."""

        if self._connected:
            try:
                self._openvr.shutdown()
            finally:
                self._connected = False
                self._vr_system = None
