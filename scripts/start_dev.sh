#!/bin/bash
set -e

source /opt/ros/jazzy/setup.bash
[ -f /drone_sim/ros2_ws/install/setup.bash ] && \
    source /drone_sim/ros2_ws/install/setup.bash

export XDG_RUNTIME_DIR=/tmp/runtime-root
export QT_X11_NO_MITSHM=1
mkdir -p /tmp/runtime-root

# ── Display setup ─────────────────────────────────────────────
# ENABLE_VNC=true  → Mac / headless: Xvfb + VNC on port 5900
# ENABLE_VNC=false → Linux: use host DISPLAY passed via environment

if [ "${ENABLE_VNC:-true}" = "true" ]; then
    echo "[DEV] Starting Xvfb virtual display..."

    rm -f /tmp/.X99-lock /tmp/.X11-unix/X99 2>/dev/null || true
    Xvfb :99 -screen 0 1920x1080x24 &

    for i in $(seq 1 20); do
        xdpyinfo -display :99 >/dev/null 2>&1 && break
        sleep 0.5
    done
    echo "[DEV] Xvfb ready."

    export DISPLAY=:99

    fluxbox 2>/dev/null &
    sleep 2

    x11vnc -display :99 -forever -shared \
        -rfbport 5900 \
        -passwd "${VNC_PASSWORD:-px4vnc}" \
        -noxdamage \
        -quiet &

    echo "[DEV] VNC ready -> connect to localhost:5900"
    echo "[DEV] VNC password: ${VNC_PASSWORD:-px4vnc}"
    sleep 2
else
    echo "[DEV] Using host X11 display: $DISPLAY"
    echo "[DEV] Gazebo GUI will appear on your host desktop."
    # DISPLAY is already set from the host via docker-compose environment
fi

SIM_SCRIPT=/drone_sim/scripts/run_simulation.sh
if [ -f "$SIM_SCRIPT" ]; then
    chmod +x "$SIM_SCRIPT"
    echo "[DEV] Launching simulation..."
    "$SIM_SCRIPT" &
    SIM_PID=$!
    echo "[DEV] Simulation running as PID $SIM_PID"
else
    echo "[DEV] No run_simulation.sh found. Dropping to shell."
fi

tail -f /dev/null
