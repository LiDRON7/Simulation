#!/usr/bin/env python3
"""
ROS 2 launch file — gz bridge only.
mavros excluded due to ros-jazzy-mavros bug (companion_process_status allocator crash).
Use QGroundControl on udp://localhost:14550 for flight commands instead.
"""
import sys
from launch import LaunchDescription, LaunchService
from launch_ros.actions import Node


def generate_launch_description():
    return LaunchDescription([

        # ── Gazebo <-> ROS 2 bridge ───────────────────────────────────────────
        Node(
            package="ros_gz_bridge",
            executable="parameter_bridge",
            name="gz_ros_bridge",
            output="screen",
            parameters=[{"config_file": "/drone_sim/config/ros_gz_bridge.yaml"}],
        ),
    ])


if __name__ == "__main__":
    ls = LaunchService()
    ls.include_launch_description(generate_launch_description())
    sys.exit(ls.run())
