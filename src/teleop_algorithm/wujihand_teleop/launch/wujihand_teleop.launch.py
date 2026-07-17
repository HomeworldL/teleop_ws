"""Launch Wuji Glove to Wuji Hand teleoperation for one or two hands."""

from __future__ import annotations

from pathlib import Path

import yaml
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, OpaqueFunction
from launch.conditions import IfCondition
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node
from launch_ros.parameter_descriptions import ParameterValue


def _config_path(package: str, filename: str) -> str:
    config_dir = Path(get_package_share_directory(package)) / "config"
    live = config_dir / filename
    if live.exists():
        return str(live)
    template = config_dir / f"{filename}.template"
    return str(template)


def _load_yaml(path: str) -> dict:
    with Path(path).expanduser().open("r", encoding="utf-8") as stream:
        return yaml.safe_load(stream) or {}


def _config_section(cfg: dict, canonical_key: str, legacy_key: str) -> dict:
    return cfg.get(canonical_key, cfg.get(legacy_key, {}))


def _override_or_config(context, arg_name: str, cfg_value, default_value="") -> str:
    override = LaunchConfiguration(arg_name).perform(context)
    if override != "":
        return override
    if cfg_value is None:
        return str(default_value)
    return str(cfg_value)


def _override_or_config_float(context, arg_name: str, cfg_value, default_value: float) -> float:
    override = LaunchConfiguration(arg_name).perform(context)
    if override != "":
        return float(override)
    if cfg_value is None:
        return float(default_value)
    return float(cfg_value)


def _launch_setup(context, *args, **kwargs):
    hand_config_path = LaunchConfiguration("hand_config").perform(context)
    hand_cfg = _load_yaml(hand_config_path)
    driver_cfg = hand_cfg.get("driver", {})
    left_hand = _config_section(hand_cfg, "hand_left", "left_hand")
    right_hand = _config_section(hand_cfg, "hand_right", "right_hand")

    enable_left = LaunchConfiguration("enable_left")
    enable_right = LaunchConfiguration("enable_right")
    glove_config = LaunchConfiguration("glove_config")
    left_keypoints_topic = LaunchConfiguration("left_keypoints_topic")
    right_keypoints_topic = LaunchConfiguration("right_keypoints_topic")

    retarget_config_dir = LaunchConfiguration("retarget_config_dir").perform(context)
    if retarget_config_dir == "":
        retarget_config_dir = str(Path(hand_config_path).expanduser().resolve().parent)

    left_serial = _override_or_config(context, "left_serial", left_hand.get("serial_number"))
    right_serial = _override_or_config(context, "right_serial", right_hand.get("serial_number"))
    left_hand_name = _override_or_config(
        context, "left_hand_name", left_hand.get("name"), "hand_left"
    )
    right_hand_name = _override_or_config(
        context, "right_hand_name", right_hand.get("name"), "hand_right"
    )
    driver_publish_rate = _override_or_config_float(
        context, "driver_publish_rate", driver_cfg.get("publish_rate"), 1000.0
    )
    driver_filter_cutoff_freq = _override_or_config_float(
        context, "driver_filter_cutoff_freq", driver_cfg.get("filter_cutoff_freq"), 10.0
    )
    driver_diagnostics_rate = _override_or_config_float(
        context, "driver_diagnostics_rate", driver_cfg.get("diagnostics_rate"), 10.0
    )

    def glove_node(side: str, topic, condition):
        return Node(
            package="wuji_glove",
            executable="wuji_glove_node",
            name=f"wuji_glove_{side}",
            output="screen",
            emulate_tty=True,
            arguments=[
                "--side",
                side,
                "--config",
                glove_config,
                "--topic",
                topic,
                "--publish-rate",
                LaunchConfiguration("glove_publish_rate"),
            ],
            condition=IfCondition(condition),
        )

    def hand_driver(hand_name, serial, condition):
        return Node(
            package="wujihand_driver",
            executable="wujihand_driver_node",
            name="wujihand_driver",
            namespace=hand_name,
            parameters=[
                {
                    "serial_number": ParameterValue(serial, value_type=str),
                    "publish_rate": ParameterValue(driver_publish_rate, value_type=float),
                    "filter_cutoff_freq": ParameterValue(
                        driver_filter_cutoff_freq, value_type=float
                    ),
                    "diagnostics_rate": ParameterValue(
                        driver_diagnostics_rate, value_type=float
                    ),
                }
            ],
            output="screen",
            emulate_tty=True,
            condition=IfCondition(condition),
        )

    def teleop_controller(side: str, hand_name, keypoints_topic, condition):
        return Node(
            package="wujihand_teleop",
            executable="wujihand_controller",
            name=f"wujihand_teleop_{side}",
            output="screen",
            emulate_tty=True,
            arguments=[
                "--side",
                side,
                "--hand-name",
                hand_name,
                "--config",
                hand_config_path,
                "--keypoints-topic",
                keypoints_topic,
                "--retarget-config-dir",
                retarget_config_dir,
            ],
            parameters=[
                {
                    "control_rate": ParameterValue(
                        LaunchConfiguration("control_rate"), value_type=float
                    )
                }
            ],
            condition=IfCondition(condition),
        )

    return [
        glove_node("left", left_keypoints_topic, enable_left),
        glove_node("right", right_keypoints_topic, enable_right),
        hand_driver(left_hand_name, left_serial, enable_left),
        hand_driver(right_hand_name, right_serial, enable_right),
        teleop_controller("left", left_hand_name, left_keypoints_topic, enable_left),
        teleop_controller("right", right_hand_name, right_keypoints_topic, enable_right),
    ]


def generate_launch_description() -> LaunchDescription:
    hand_config_default = _config_path("wujihand_teleop", "wujihand_teleop.yaml")
    glove_config_default = _config_path("wuji_glove", "wuji_glove.yaml")

    enable_left_arg = DeclareLaunchArgument(
        "enable_left", default_value="true", description="Enable left hand teleop"
    )
    enable_right_arg = DeclareLaunchArgument(
        "enable_right", default_value="true", description="Enable right hand teleop"
    )
    hand_config_arg = DeclareLaunchArgument(
        "hand_config", default_value=hand_config_default
    )
    glove_config_arg = DeclareLaunchArgument(
        "glove_config", default_value=glove_config_default
    )
    retarget_config_dir_arg = DeclareLaunchArgument(
        "retarget_config_dir",
        default_value="",
        description=(
            "Directory containing retarget_wuji_glove_{left,right}.yaml; "
            "empty means the selected hand_config directory"
        ),
    )
    left_serial_arg = DeclareLaunchArgument(
        "left_serial",
        default_value="",
        description="Override left hand serial; empty means read from hand_config",
    )
    right_serial_arg = DeclareLaunchArgument(
        "right_serial",
        default_value="",
        description="Override right hand serial; empty means read from hand_config",
    )
    left_hand_name_arg = DeclareLaunchArgument(
        "left_hand_name",
        default_value="",
        description="Override left hand namespace; empty means read from hand_config",
    )
    right_hand_name_arg = DeclareLaunchArgument(
        "right_hand_name",
        default_value="",
        description="Override right hand namespace; empty means read from hand_config",
    )
    control_rate_arg = DeclareLaunchArgument("control_rate", default_value="120.0")
    glove_publish_rate_arg = DeclareLaunchArgument("glove_publish_rate", default_value="120.0")
    left_keypoints_topic_arg = DeclareLaunchArgument(
        "left_keypoints_topic", default_value="/wuji_glove/left/keypoints"
    )
    right_keypoints_topic_arg = DeclareLaunchArgument(
        "right_keypoints_topic", default_value="/wuji_glove/right/keypoints"
    )
    publish_rate_arg = DeclareLaunchArgument(
        "driver_publish_rate",
        default_value="",
        description="Override hand driver publish rate; empty means read from hand_config",
    )
    filter_cutoff_arg = DeclareLaunchArgument(
        "driver_filter_cutoff_freq",
        default_value="",
        description="Override hand driver filter cutoff; empty means read from hand_config",
    )
    diagnostics_rate_arg = DeclareLaunchArgument(
        "driver_diagnostics_rate",
        default_value="",
        description="Override hand driver diagnostics rate; empty means read from hand_config",
    )

    return LaunchDescription(
        [
            enable_left_arg,
            enable_right_arg,
            hand_config_arg,
            glove_config_arg,
            retarget_config_dir_arg,
            left_serial_arg,
            right_serial_arg,
            left_hand_name_arg,
            right_hand_name_arg,
            control_rate_arg,
            glove_publish_rate_arg,
            left_keypoints_topic_arg,
            right_keypoints_topic_arg,
            publish_rate_arg,
            filter_cutoff_arg,
            diagnostics_rate_arg,
            OpaqueFunction(function=_launch_setup),
        ]
    )
