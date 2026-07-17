"""Launch one or two Wuji Glove keypoint publisher nodes."""

from __future__ import annotations

from pathlib import Path

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.conditions import IfCondition
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def _config_path() -> str:
    config_dir = Path(get_package_share_directory("wuji_glove")) / "config"
    live = config_dir / "wuji_glove.yaml"
    if live.exists():
        return str(live)
    return str(config_dir / "wuji_glove.yaml.template")


def generate_launch_description() -> LaunchDescription:
    enable_left = LaunchConfiguration("enable_left")
    enable_right = LaunchConfiguration("enable_right")
    config = LaunchConfiguration("config")
    publish_rate = LaunchConfiguration("publish_rate")
    left_topic = LaunchConfiguration("left_topic")
    right_topic = LaunchConfiguration("right_topic")

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
                config,
                "--topic",
                topic,
                "--publish-rate",
                publish_rate,
            ],
            condition=IfCondition(condition),
        )

    return LaunchDescription(
        [
            DeclareLaunchArgument("enable_left", default_value="true"),
            DeclareLaunchArgument("enable_right", default_value="true"),
            DeclareLaunchArgument("config", default_value=_config_path()),
            DeclareLaunchArgument("publish_rate", default_value="120.0"),
            DeclareLaunchArgument("left_topic", default_value="/wuji_glove/left/keypoints"),
            DeclareLaunchArgument("right_topic", default_value="/wuji_glove/right/keypoints"),
            glove_node("left", left_topic, enable_left),
            glove_node("right", right_topic, enable_right),
        ]
    )
