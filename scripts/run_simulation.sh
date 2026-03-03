#!/bin/bash
# ── Launch PX4 SITL + Gazebo Harmonic + ROS 2 bridge ─────────
set -e

source /opt/ros/jazzy/setup.bash
[ -f /drone_sim/ros2_ws/install/setup.bash ] && \
    source /drone_sim/ros2_ws/install/setup.bash

export PX4_SYS_AUTOSTART=4006        # Generic hexacopter airframe
export PX4_GZ_MODEL=hexacopter       # Our custom model name
export PX4_GZ_WORLD=outdoor_obstacles

echo "[SIM] Launching PX4 SITL with Gazebo Harmonic..."
cd /px4

# Start PX4 SITL — Gazebo Harmonic headless flag auto-applied in CI
make px4_sitl gz_hexacopter__outdoor_obstacles &
PX4_PID=$!

sleep 8

echo "[SIM] Starting ROS 2 <-> Gazebo bridge..."
ros2 run ros_gz_bridge parameter_bridge \
    /clock@rosgraph_msgs/msg/Clock[gz.msgs.Clock \
    /model/hexacopter/odometry@nav_msgs/msg/Odometry[gz.msgs.Odometry \
    /lidar/points@sensor_msgs/msg/PointCloud2[gz.msgs.PointCloudPacked \
    /oakd/color/image@sensor_msgs/msg/Image[gz.msgs.Image \
    /oakd/depth@sensor_msgs/msg/Image[gz.msgs.Image \
    /gps@sensor_msgs/msg/NavSatFix[gz.msgs.NavSat \
    &

echo "[SIM] Starting MAVROS..."
ros2 launch mavros px4.launch fcu_url:=udp://:14540@localhost:14557 &

echo "[SIM] All systems running. PX4 PID=$PX4_PID"
wait $PX4_PID
