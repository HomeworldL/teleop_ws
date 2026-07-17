"""Launch the Vive OpenVR tracker input node."""

from __future__ import annotations

from pathlib import Path

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.conditions import IfCondition
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def _config_path() -> str:
    config_dir = Path(get_package_share_directory("vive_openvr")) / "config"
    live = config_dir / "vive_openvr.yaml"
    if live.exists():
        return str(live)
    return str(config_dir / "vive_openvr.yaml.template")


def generate_launch_description() -> LaunchDescription:
    config = LaunchConfiguration("config")
    rviz = LaunchConfiguration("rviz")
    pkg_dir = Path(get_package_share_directory("vive_openvr"))
    return LaunchDescription(
        [
            DeclareLaunchArgument("config", default_value=_config_path()),
            DeclareLaunchArgument("rviz", default_value="false"),
            Node(
                package="vive_openvr",
                executable="vive_openvr_node",
                name="vive_openvr",
                output="screen",
                emulate_tty=True,
                arguments=["--config", config],
            ),
            Node(
                package="rviz2",
                executable="rviz2",
                name="rviz2",
                output="screen",
                arguments=["-d", str(pkg_dir / "rviz" / "vive_openvr.rviz")],
                condition=IfCondition(rviz),
            ),
        ]
    )
