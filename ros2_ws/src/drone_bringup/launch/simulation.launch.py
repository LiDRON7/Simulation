"""
ROS 2 launch file — brings up the full simulation stack:
  1. ros_gz_bridge  (Gazebo <-> ROS 2 topic bridge)
  2. MAVROS         (PX4 <-> ROS 2)
  3. robot_state_publisher (TF tree)
"""

import os

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, TimerAction
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare


def generate_launch_description():

    bridge_config = PathJoinSubstitution(["/drone_sim/config", "ros_gz_bridge.yaml"])

    return LaunchDescription(
        [
            DeclareLaunchArgument(
                "fcu_url",
                default_value="udp://:14540@localhost:14557",
                description="MAVLink FCU URL for MAVROS",
            ),
            # ── Gazebo <-> ROS 2 bridge ───────────────────────
            Node(
                package="ros_gz_bridge",
                executable="parameter_bridge",
                name="gz_ros_bridge",
                output="screen",
                parameters=[{"config_file": bridge_config}],
            ),
            # ── MAVROS — connects to PX4 SITL ─────────────────
            # Slight delay to let bridge and sim stabilize first
            TimerAction(
                period=5.0,
                actions=[
                    Node(
                        package="mavros",
                        executable="mavros_node",
                        name="mavros",
                        output="screen",
                        parameters=[
                            {
                                "fcu_url": LaunchConfiguration("fcu_url"),
                                "gcs_url": "",
                                "target_system_id": 1,
                                "target_component_id": 1,
                                "fcu_protocol": "v2.0",
                            }
                        ],
                    ),
                ],
            ),
            # ── Robot state publisher — TF frames ─────────────
            Node(
                package="robot_state_publisher",
                executable="robot_state_publisher",
                name="robot_state_publisher",
                output="screen",
                parameters=[
                    {
                        "robot_description": open(
                            "/drone_sim/models/hexacopter_sensors/model.sdf"
                        ).read()
                    }
                ],
            ),
        ]
    )
