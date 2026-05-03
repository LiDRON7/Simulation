#!/usr/bin/env python3
import sys
from launch import LaunchDescription, LaunchService
from launch.actions import DeclareLaunchArgument, TimerAction
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node

def generate_launch_description():
    return LaunchDescription([
        DeclareLaunchArgument("fcu_url", default_value="udp://:14540@127.0.0.1:14557"),
        Node(
            package="ros_gz_bridge",
            executable="parameter_bridge",
            name="gz_ros_bridge",
            output="screen",
            parameters=[{"config_file": "/drone_sim/config/ros_gz_bridge.yaml"}],
        ),
        TimerAction(period=5.0, actions=[
            Node(
                package="mavros",
                executable="mavros_node",
                name="mavros",
                output="screen",
                parameters=[{
                    "fcu_url": LaunchConfiguration("fcu_url"),
                    "gcs_url": "",
                    "target_system_id": 1,
                    "target_component_id": 1,
                    "fcu_protocol": "v2.0",
                }],
            ),
        ]),
    ])

if __name__ == "__main__":
    ls = LaunchService()
    ls.include_launch_description(generate_launch_description())
    sys.exit(ls.run())
