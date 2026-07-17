"""Per-hand Wuji Glove keypoint to Wuji Hand controller node."""
from __future__ import annotations

import argparse
import sys
import threading
from pathlib import Path
from typing import Optional

import numpy as np
import rclpy
from geometry_msgs.msg import PoseArray
from rclpy.node import Node
from rclpy.utilities import remove_ros_args

from wujihand_teleop.wujihand_controller import WujiHandController
from wujihand_teleop.common import (
    ROS2LoggerAdapter,
    load_yaml_config,
    get_package_config_path,
)

# Default control-loop rate (Hz). Override with the `control_rate` ROS2 param.
# 120Hz matches the upper bound of wuji_glove skeleton frames; higher adds no
# new input. The wujihand C++ driver runs 1000Hz down to the firmware, so
# publishing faster from the controller is not useful.
DEFAULT_CONTROL_RATE_HZ = 120.0


def _pose_array_to_keypoints(msg: PoseArray) -> Optional[np.ndarray]:
    """Convert a 21-pose Wuji Glove PoseArray to a (21, 3) keypoint array."""
    if len(msg.poses) != 21:
        return None
    return np.array(
        [[pose.position.x, pose.position.y, pose.position.z] for pose in msg.poses],
        dtype=np.float32,
    )


class WujiHandControllerNode(Node):
    """Per-hand wujihand controller node.

    The node subscribes to one Wuji Glove PoseArray keypoint stream, retargets
    its 21-point skeleton, and publishes position commands to one wujihandros2
    driver namespace.
    """

    def __init__(self, side: str, hand_name: str, cfg: dict,
                 keypoints_topic: Optional[str] = None,
                 retarget_config_dir: Optional[str] = None):
        super().__init__(f"wujihand_controller_{side}")

        self._side = side
        self._logger_adapter = ROS2LoggerAdapter(self.get_logger())
        self._input_source = cfg.get("input_source", "wuji_glove")
        if self._input_source != "wuji_glove":
            raise ValueError(
                f"unsupported input_source: {self._input_source!r}; "
                "this package currently supports only 'wuji_glove'"
            )

        self._keypoints_topic = keypoints_topic or f"/wuji_glove/{side}/keypoints"
        self._pending_keypoints: Optional[np.ndarray] = None
        self._keypoints_lock = threading.Lock()

        # Controller (drives retargeter + wujihand driver)
        self.get_logger().info(
            f"Initializing {side}-hand controller (input_source={self._input_source})..."
        )
        self.controller = WujiHandController(
            side=side,
            hand_name=hand_name,
            input_source=self._input_source,
            node=self,
            logger=self._logger_adapter,
            retarget_config_dir=retarget_config_dir,
        )
        self.get_logger().info("Controller initialized")

        self._keypoints_sub = self.create_subscription(
            PoseArray,
            self._keypoints_topic,
            self._keypoints_callback,
            10,
        )

        # control_rate comes from a ROS2 param, default 120Hz (see the
        # DEFAULT_CONTROL_RATE_HZ comment at the top of this module). No
        # rebuild needed to change it: launch -p control_rate:=... works.
        self.declare_parameter('control_rate', DEFAULT_CONTROL_RATE_HZ)
        self._control_rate_hz = float(self.get_parameter('control_rate').value)
        if self._control_rate_hz <= 0.0:
            raise ValueError(
                f"control_rate must be > 0, got {self._control_rate_hz}")
        self.create_timer(1.0 / self._control_rate_hz, self._teleop_loop)

        self.get_logger().info(
            f"Ready: side={side}, source={self._input_source}, "
            f"rate={self._control_rate_hz:.1f}Hz, "
            f"{self._keypoints_topic} -> /{hand_name}/joint_commands"
        )

    def _keypoints_callback(self, msg: PoseArray) -> None:
        keypoints = _pose_array_to_keypoints(msg)
        if keypoints is None:
            self.get_logger().warn(
                f"ignored {self._keypoints_topic}: expected 21 poses, got {len(msg.poses)}"
            )
            return
        with self._keypoints_lock:
            self._pending_keypoints = keypoints

    # ==================== shared ====================

    def _teleop_loop(self) -> None:
        with self._keypoints_lock:
            keypoints = self._pending_keypoints
            self._pending_keypoints = None
        if keypoints is not None:
            self.controller.set_keypoints(keypoints)

    # ==================== lifecycle ====================

    def shutdown(self):
        self.get_logger().info("Shutting down...")
        self.controller.disable_and_release()
        self.get_logger().info("Exited cleanly")


# -------------------- Entry point --------------------

def _parse_args(argv: Optional[list[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Wuji-hand controller (per-hand)")
    parser.add_argument("--side", required=True, choices=["left", "right"],
                        help="which hand to drive")
    parser.add_argument("--hand-name", help="wujihandros2 driver namespace")
    parser.add_argument("-c", "--config", help="wujihand_teleop.yaml path")
    parser.add_argument("--keypoints-topic", help="input PoseArray topic")
    parser.add_argument(
        "--retarget-config-dir",
        help="Directory containing retarget yaml (overrides the wujihand_teleop "
             "package's default config/). Lookup order: "
             "retarget_{input_source}_{side}.yaml -> retarget_{input_source}.yaml. "
             "Use for cross-host deployments where launch passes an explicit "
             "override directory so retarget params follow the deploy host "
             "rather than the in-package default config/.",
    )
    return parser.parse_args(argv)


def _resolve_config_path(config_path: Optional[str]) -> Path:
    if config_path:
        return Path(config_path).expanduser().resolve()

    for filename in ("wujihand_teleop.yaml", "wujihand_teleop.yaml.template"):
        path = get_package_config_path("wujihand_teleop", filename)
        if path is not None and path.exists():
            return path

    raise FileNotFoundError(
        "Could not locate wujihand_teleop.yaml or wujihand_teleop.yaml.template"
    )


def main(argv: Optional[list[str]] = None):
    program_name = sys.argv[0] if sys.argv else "wujihand_controller"
    raw_argv = sys.argv if argv is None else [program_name, *argv]
    cli_argv = remove_ros_args(raw_argv)[1:]
    args = _parse_args(cli_argv)

    side = args.side
    default_hand_name = "hand_left" if side == "left" else "hand_right"
    hand_name = args.hand_name or default_hand_name

    config_path = _resolve_config_path(args.config)
    cfg = load_yaml_config(config_path)

    rclpy.init(args=raw_argv)
    node = None
    try:
        node = WujiHandControllerNode(
            side=side, hand_name=hand_name, cfg=cfg,
            keypoints_topic=args.keypoints_topic,
            retarget_config_dir=args.retarget_config_dir,
        )
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        if node is not None:
            node.shutdown()
            node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == "__main__":
    main()
