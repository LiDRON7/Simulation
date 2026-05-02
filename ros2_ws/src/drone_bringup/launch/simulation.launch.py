"""
ROS 2 launch file — full simulation bridge stack:
  1. ros_gz_bridge  (Gazebo <-> ROS 2 topic bridge)
  2. MAVROS         (PX4 SITL <-> ROS 2 via MAVLink UDP)
"""

import os
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, TimerAction
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():

    bridge_config = "/drone_sim/config/ros_gz_bridge.yaml"

    return LaunchDescription([

        DeclareLaunchArgument(
            "fcu_url",
            # PX4 SITL default MAVLink ports: listens on 14540, sends to 14557
            default_value="udp://:14540@127.0.0.1:14557",
            description="MAVLink FCU URL for MAVROS",
        ),

        # ── Gazebo <-> ROS 2 bridge ───────────────────────────────────────────
        Node(
            package="ros_gz_bridge",
            executable="parameter_bridge",
            name="gz_ros_bridge",
            output="screen",
            parameters=[{"config_file": bridge_config}],
        ),

        # ── MAVROS — connects to PX4 SITL over MAVLink UDP ───────────────────
        # Delayed 5s to let bridge stabilize first
        TimerAction(
            period=5.0,
            actions=[
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
            ],
        ),
    ])
