"""Launch per-hand Wuji Glove to Wuji Hand retarget nodes."""

from __future__ import annotations

import os
import sys
from pathlib import Path

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.conditions import IfCondition
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node
from launch_ros.parameter_descriptions import ParameterValue


def _default_config_dir() -> str:
    return str(Path(get_package_share_directory("wujihand_teleop")) / "config")


def _prepend_env_path(name: str, entries: list[Path]) -> str:
    existing = os.environ.get(name, "")
    values = [str(path) for path in entries if path.exists()]
    if existing:
        values.append(existing)
    return os.pathsep.join(values)


def _retarget_env() -> dict[str, str]:
    env = {"PYTHONNOUSERSITE": "1"}
    conda_prefix = os.environ.get("CONDA_PREFIX")
    if not conda_prefix:
        return env

    python_dir = f"python{sys.version_info.major}.{sys.version_info.minor}"
    site_packages = Path(conda_prefix) / "lib" / python_dir / "site-packages"
    cmeel_prefix = site_packages / "cmeel.prefix"
    env["PYTHONPATH"] = _prepend_env_path(
        "PYTHONPATH",
        [
            cmeel_prefix / "lib" / python_dir / "site-packages",
            site_packages,
        ],
    )
    env["LD_LIBRARY_PATH"] = _prepend_env_path(
        "LD_LIBRARY_PATH",
        [
            cmeel_prefix / "lib",
        ],
    )
    return env


def _retarget_node(side: str, hand_name, keypoints_topic, enable):
    return Node(
        package="wujihand_teleop",
        executable="wujihand_retarget",
        name=f"wujihand_retarget_{side}",
        output="screen",
        emulate_tty=True,
        # additional_env=_retarget_env(),
        arguments=[
            "--side",
            side,
            "--hand-name",
            hand_name,
            "--keypoints-topic",
            keypoints_topic,
            "--retarget-config-dir",
            LaunchConfiguration("retarget_config_dir"),
        ],
        parameters=[
            {
                "control_rate": ParameterValue(
                    LaunchConfiguration("control_rate"),
                    value_type=float,
                ),
                "require_feedback": ParameterValue(
                    LaunchConfiguration("require_feedback"),
                    value_type=bool,
                ),
                "feedback_timeout": ParameterValue(
                    LaunchConfiguration("feedback_timeout"),
                    value_type=float,
                ),
                "input_timeout": ParameterValue(
                    LaunchConfiguration("input_timeout"),
                    value_type=float,
                ),
                "startup_ramp_sec": ParameterValue(
                    LaunchConfiguration("startup_ramp_sec"),
                    value_type=float,
                ),
                "max_joint_velocity": ParameterValue(
                    LaunchConfiguration("max_joint_velocity"),
                    value_type=float,
                ),
                "dry_run": ParameterValue(
                    LaunchConfiguration("dry_run"),
                    value_type=bool,
                ),
                "publish_diagnostics": ParameterValue(
                    LaunchConfiguration("publish_diagnostics"),
                    value_type=bool,
                ),
                "diagnostics_rate": ParameterValue(
                    LaunchConfiguration("diagnostics_rate"),
                    value_type=float,
                ),
                "nlopt_max_eval": ParameterValue(
                    LaunchConfiguration("nlopt_max_eval"),
                    value_type=int,
                ),
                "min_keypoint_spread": ParameterValue(
                    LaunchConfiguration("min_keypoint_spread"),
                    value_type=float,
                ),
                "clip_to_joint_limits": ParameterValue(
                    LaunchConfiguration("clip_to_joint_limits"),
                    value_type=bool,
                ),
                "retarget_verbose": ParameterValue(
                    LaunchConfiguration("retarget_verbose"),
                    value_type=bool,
                ),
            }
        ],
        condition=IfCondition(enable),
    )


def generate_launch_description() -> LaunchDescription:
    enable_left = LaunchConfiguration("enable_left")
    enable_right = LaunchConfiguration("enable_right")
    left_hand_name = LaunchConfiguration("left_hand_name")
    right_hand_name = LaunchConfiguration("right_hand_name")
    left_keypoints_topic = LaunchConfiguration("left_keypoints_topic")
    right_keypoints_topic = LaunchConfiguration("right_keypoints_topic")

    return LaunchDescription(
        [
            DeclareLaunchArgument("enable_left", default_value="true"),
            DeclareLaunchArgument("enable_right", default_value="true"),
            DeclareLaunchArgument("left_hand_name", default_value="hand_left"),
            DeclareLaunchArgument("right_hand_name", default_value="hand_right"),
            DeclareLaunchArgument(
                "left_keypoints_topic",
                default_value="/wuji_glove/left/keypoints",
            ),
            DeclareLaunchArgument(
                "right_keypoints_topic",
                default_value="/wuji_glove/right/keypoints",
            ),
            DeclareLaunchArgument("retarget_config_dir", default_value=_default_config_dir()),
            DeclareLaunchArgument("control_rate", default_value="120.0"),
            DeclareLaunchArgument("require_feedback", default_value="true"),
            DeclareLaunchArgument("feedback_timeout", default_value="1.0"),
            DeclareLaunchArgument("input_timeout", default_value="0.3"),
            DeclareLaunchArgument("startup_ramp_sec", default_value="0.5"),
            DeclareLaunchArgument("max_joint_velocity", default_value="3.14"),
            DeclareLaunchArgument("dry_run", default_value="false"),
            DeclareLaunchArgument("publish_diagnostics", default_value="true"),
            DeclareLaunchArgument("diagnostics_rate", default_value="2.0"),
            DeclareLaunchArgument("nlopt_max_eval", default_value="25"),
            DeclareLaunchArgument("min_keypoint_spread", default_value="0.01"),
            DeclareLaunchArgument("clip_to_joint_limits", default_value="true"),
            DeclareLaunchArgument("retarget_verbose", default_value="false"),
            _retarget_node("left", left_hand_name, left_keypoints_topic, enable_left),
            _retarget_node("right", right_hand_name, right_keypoints_topic, enable_right),
        ]
    )
