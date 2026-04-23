#!/bin/bash
set -e

source /opt/ros/jazzy/setup.bash

if [ -f /drone_sim/ros2_ws/install/setup.bash ]; then
  source /drone_sim/ros2_ws/install/setup.bash
fi

export GZ_SIM_RESOURCE_PATH=/drone_sim/models:/drone_sim/worlds:/px4/Tools/simulation/gz/models:$GZ_SIM_RESOURCE_PATH
export GZ_CONFIG_PATH=/opt/ros/jazzy/opt/gz_sim_vendor/share/gz:/opt/ros/jazzy/opt/gz_transport_vendor/share/gz

# ── GPU configuration ──────────────────────────────────────────────────────
case "${GPU_VENDOR:-none}" in
  nvidia)
    echo "[entrypoint] NVIDIA GPU mode"
    export __GLX_VENDOR_LIBRARY_NAME=nvidia
    export NVIDIA_DRIVER_CAPABILITIES=all
    unset LIBGL_ALWAYS_SOFTWARE
    unset GALLIUM_DRIVER
    unset MESA_GL_VERSION_OVERRIDE
    unset MESA_GLSL_VERSION_OVERRIDE
    ;;
  amd|intel)
    echo "[entrypoint] AMD/Intel GPU mode"
    unset LIBGL_ALWAYS_SOFTWARE
    unset GALLIUM_DRIVER
    unset MESA_GL_VERSION_OVERRIDE
    unset MESA_GLSL_VERSION_OVERRIDE
    ;;
  none|*)
    echo "[entrypoint] No GPU — software rendering (ogre2 version override active)"
    # Keep LIBGL_ALWAYS_SOFTWARE, MESA_GL_VERSION_OVERRIDE etc. as set by compose
    ;;
esac

exec "$@"
