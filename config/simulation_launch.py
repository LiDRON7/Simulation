#!/usr/bin/env python3
import os
import sys
import tempfile
from launch import LaunchDescription, LaunchService
from launch_ros.actions import Node

CONFIG = "/drone_sim/config/ros_gz_bridge.yaml"


def generate_launch_description():
    # the IMU and GPS topics carry the model's name: fill in the drone being flown
    bridge = tempfile.NamedTemporaryFile("w", suffix=".yaml", delete=False)
    bridge.write(open(CONFIG).read().replace("DRONE_0", os.environ.get("DRONE", "huntsman") + "_0"))
    bridge.close()
    return LaunchDescription([
        Node(
            package="ros_gz_bridge",
            executable="parameter_bridge",
            name="gz_ros_bridge",
            output="screen",
            parameters=[{"config_file": bridge.name}],
        ),
    ])


if __name__ == "__main__":
    launch_service = LaunchService()
    launch_service.include_launch_description(generate_launch_description())
    sys.exit(launch_service.run())
