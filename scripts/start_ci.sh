#!/bin/bash
set -e

source /opt/ros/jazzy/setup.bash
[ -f /drone_sim/ros2_ws/install/setup.bash ] && \
    source /drone_sim/ros2_ws/install/setup.bash

export GZ_HEADLESS_RENDERING=1
export LIBGL_ALWAYS_SOFTWARE=1

echo "[CI] Installing custom models and worlds..."
mkdir -p /px4/Tools/simulation/gz/models
mkdir -p /px4/Tools/simulation/gz/worlds
cp -r /drone_sim/models/. /px4/Tools/simulation/gz/models/ 2>/dev/null || true
cp -r /drone_sim/worlds/. /px4/Tools/simulation/gz/worlds/ 2>/dev/null || true

WORLD_NAME="outdoor_obstacles"
WORLD_FILE="/px4/Tools/simulation/gz/worlds/${WORLD_NAME}.sdf"
if [ ! -f "$WORLD_FILE" ]; then
    echo "[CI] WARNING: Custom world not found, falling back to baylands"
    WORLD_NAME="baylands"
fi
echo "[CI] Using world: $WORLD_NAME"

echo "[CI] Launching PX4 SITL + Gazebo (headless)..."
cd /px4
HEADLESS=1 make px4_sitl gz_x500_${WORLD_NAME} &
PX4_PID=$!
echo "[CI] PX4 PID=$PX4_PID"

echo "[CI] Waiting for PX4 + Gazebo to initialize (45s)..."
sleep 45

echo "[CI] Starting ROS 2 <-> Gazebo bridge..."
ros2 run ros_gz_bridge parameter_bridge \
    /clock@rosgraph_msgs/msg/Clock[gz.msgs.Clock \
    /model/x500_0/odometry@nav_msgs/msg/Odometry[gz.msgs.Odometry \
    /lidar/points@sensor_msgs/msg/PointCloud2[gz.msgs.PointCloudPacked \
    /oakd/color/image@sensor_msgs/msg/Image[gz.msgs.Image \
    /oakd/depth@sensor_msgs/msg/Image[gz.msgs.Image \
    /gps@sensor_msgs/msg/NavSatFix[gz.msgs.NavSat \
    /imu@sensor_msgs/msg/Imu[gz.msgs.IMU &
BRIDGE_PID=$!

echo "[CI] Starting MAVROS..."
ros2 run mavros mavros_node \
    --ros-args \
    -p fcu_url:=udp://:14540@127.0.0.1:14557 \
    -p gcs_url:=udp://@:14550 \
    -p tgt_system:=1 \
    -p tgt_component:=1 &
MAVROS_PID=$!

echo "[CI] ================================================"
echo "[CI] Simulation ready for tests."
echo "[CI] PX4     PID=$PX4_PID"
echo "[CI] Bridge  PID=$BRIDGE_PID"
echo "[CI] MAVROS  PID=$MAVROS_PID"
echo "[CI] World:  $WORLD_NAME"
echo "[CI] ================================================"

# In CI the container stays alive for test runners to connect.
# If called with arguments, execute them as the test command.
if [ "$#" -gt 0 ]; then
    echo "[CI] Running: $@"
    exec "$@"
else
    wait $PX4_PID
fi
