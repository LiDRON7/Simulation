#!/bin/bash
set -e

# Source ROS 2
source /opt/ros/jazzy/setup.bash

# Source workspace if already built
[ -f /drone_sim/ros2_ws/install/setup.bash ] && \
    source /drone_sim/ros2_ws/install/setup.bash

# Start virtual display + VNC for macOS viewing
if [ "${ENABLE_VNC}" = "true" ]; then
    echo "[DEV] Starting Xvfb virtual display..."
    Xvfb :99 -screen 0 1920x1080x24 &
    sleep 2
    fluxbox &
    sleep 1
    x11vnc -display :99 -forever -shared \
        -rfbport 5900 \
        -passwd "${VNC_PASSWORD:-px4vnc}" \
        -noxdamage &
    echo "[DEV] VNC ready → connect to localhost:5900"
    echo "[DEV] VNC password: ${VNC_PASSWORD:-px4vnc}"
fi

exec "$@"
