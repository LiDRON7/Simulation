#!/usr/bin/env python3
import sys
from launch import LaunchDescription, LaunchService
from launch_ros.actions import Node

def generate_launch_description():
    return LaunchDescription([
        Node(
            package="ros_gz_bridge",
            executable="parameter_bridge",
            name="gz_ros_bridge",
            output="screen",
            parameters=[{"config_file": "/drone_sim/config/ros_gz_bridge.yaml"}],
        ),
    ])

if __name__ == "__main__":
    launch_service = LaunchService()
    launch_service.include_launch_description(generate_launch_description())
    sys.exit(launch_service.run())
