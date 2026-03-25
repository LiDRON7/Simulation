#!/bin/bash
set -e

source /opt/ros/jazzy/setup.bash
[ -f /drone_sim/ros2_ws/install/setup.bash ] && \
    source /drone_sim/ros2_ws/install/setup.bash

export DISPLAY=:99
export XDG_RUNTIME_DIR=/tmp/runtime-root
export QT_X11_NO_MITSHM=1
mkdir -p /tmp/runtime-root
chmod 700 /tmp/runtime-root

# ── Copy custom assets into PX4's gz resource paths ──────────
echo "[SIM] Installing custom models and worlds..."
mkdir -p /px4/Tools/simulation/gz/models
mkdir -p /px4/Tools/simulation/gz/worlds
cp -r /drone_sim/models/. /px4/Tools/simulation/gz/models/ 2>/dev/null || true
cp -r /drone_sim/worlds/. /px4/Tools/simulation/gz/worlds/ 2>/dev/null || true

echo "[SIM] Worlds available:"
ls /px4/Tools/simulation/gz/worlds/

# ── Verify world file ─────────────────────────────────────────
WORLD_NAME="outdoor_obstacles"
WORLD_FILE="/px4/Tools/simulation/gz/worlds/${WORLD_NAME}.sdf"
if [ ! -f "$WORLD_FILE" ]; then
    echo "[SIM] WARNING: Custom world not found, falling back to baylands"
    WORLD_NAME="baylands"
fi
echo "[SIM] Using world: $WORLD_NAME"

# ── Launch PX4 SITL via make (official supported method) ─────
# This is the correct way to launch PX4 v1.16 + Gazebo Harmonic.
# 'make px4_sitl gz_x500' spawns gz-sim internally with correct paths.
# Format: gz_<model>__<world>  (double underscore before world)
echo "[SIM] Launching PX4 SITL + Gazebo Harmonic via make..."
cd /px4
HEADLESS=0 make px4_sitl gz_x500_${WORLD_NAME} &
PX4_PID=$!
echo "[SIM] PX4 make PID=$PX4_PID"

# Wait for Gazebo and PX4 to initialize
echo "[SIM] Waiting for PX4 + Gazebo to initialize (45s)..."
sleep 45

# ── ROS 2 <-> Gazebo bridge ───────────────────────────────────
echo "[SIM] Starting ROS 2 <-> Gazebo bridge..."
ros2 run ros_gz_bridge parameter_bridge \
    /clock@rosgraph_msgs/msg/Clock[gz.msgs.Clock \
    /model/x500_0/odometry@nav_msgs/msg/Odometry[gz.msgs.Odometry \
    /lidar/points@sensor_msgs/msg/PointCloud2[gz.msgs.PointCloudPacked \
    /oakd/color/image@sensor_msgs/msg/Image[gz.msgs.Image \
    /oakd/depth@sensor_msgs/msg/Image[gz.msgs.Image \
    /gps@sensor_msgs/msg/NavSatFix[gz.msgs.NavSat \
    /imu@sensor_msgs/msg/Imu[gz.msgs.IMU &
BRIDGE_PID=$!

# ── MAVROS ────────────────────────────────────────────────────
echo "[SIM] Starting MAVROS..."
ros2 run mavros mavros_node \
    --ros-args \
    -p fcu_url:=udp://:14540@127.0.0.1:14557 \
    -p gcs_url:=udp://@:14550 \
    -p tgt_system:=1 \
    -p tgt_component:=1 &
MAVROS_PID=$!
# ── Launch Gazebo GUI ─────────────────────────────────────────
echo "[SIM] Launching Gazebo GUI..."
export XDG_RUNTIME_DIR=/tmp/runtime-root
mkdir -p /tmp/runtime-root
DISPLAY=:99 gz gui &
GZ_GUI_PID=$!

echo "[SIM] Gazebo GUI PID=$GZ_GUI_PID"
echo "[SIM] ================================================"
echo "[SIM] All systems launched."
echo "[SIM] PX4     PID=$PX4_PID"
echo "[SIM] Bridge  PID=$BRIDGE_PID"
echo "[SIM] MAVROS  PID=$MAVROS_PID"
echo "[SIM] World:  $WORLD_NAME"
echo "[SIM] Gazebo GUI will appear in VNC window shortly."
echo "[SIM] ================================================"

wait $PX4_PID
