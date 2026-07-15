from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, OpaqueFunction
from launch.substitutions import Command, FindExecutable, LaunchConfiguration, PathJoinSubstitution
from launch_ros.actions import Node
from launch_ros.parameter_descriptions import ParameterValue
from launch_ros.substitutions import FindPackageShare
from ament_index_python.packages import get_package_share_directory

import os


def launch_setup(context, *args, **kwargs):
    robot_description_content = Command(
        [
            PathJoinSubstitution([FindExecutable(name="xacro")]),
            " ",
            PathJoinSubstitution(
                [FindPackageShare("robot_description"), "urdf", "robot.xacro"]
            ),
        ]
    )
    robot_description = {"robot_description": robot_description_content.perform(context)}

    config_file = os.path.join(
        get_package_share_directory("robot_bringup"),
        "config",
        "joint_state_aggregator.yaml",
    )
    rviz_config_file = PathJoinSubstitution(
        [FindPackageShare("robot_description"), "rviz", "view_robot.rviz"]
    )

    nodes = [
        Node(
            package="robot_bringup",
            executable="joint_state_aggregator",
            name="joint_state_aggregator",
            output="screen",
            parameters=[
                config_file,
                {
                    "publish_rate_hz": ParameterValue(
                        LaunchConfiguration("publish_rate_hz"), value_type=float
                    ),
                    "stale_timeout_sec": ParameterValue(
                        LaunchConfiguration("stale_timeout_sec"), value_type=float
                    ),
                },
            ],
        ),
        Node(
            package="robot_state_publisher",
            executable="robot_state_publisher",
            output="screen",
            parameters=[robot_description],
        ),
    ]

    if LaunchConfiguration("rviz").perform(context).lower() in ("true", "1", "yes"):
        nodes.append(
            Node(
                package="rviz2",
                executable="rviz2",
                name="rviz2",
                arguments=["-d", rviz_config_file],
                output="screen",
            )
        )

    return nodes


def generate_launch_description():
    return LaunchDescription(
        [
            DeclareLaunchArgument("rviz", default_value="true"),
            DeclareLaunchArgument("publish_rate_hz", default_value="50.0"),
            DeclareLaunchArgument("stale_timeout_sec", default_value="0.0"),
            OpaqueFunction(function=launch_setup),
        ]
    )
