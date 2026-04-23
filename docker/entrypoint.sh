#!/bin/bash
set -e

source /opt/ros/jazzy/setup.bash

if [ -f /drone_sim/ros2_ws/install/setup.bash ]; then
  source /drone_sim/ros2_ws/install/setup.bash
fi

export GZ_SIM_RESOURCE_PATH=/drone_sim/models:/drone_sim/worlds:$GZ_SIM_RESOURCE_PATH
export GZ_CONFIG_PATH=/opt/ros/jazzy/opt/gz_sim_vendor/share/gz:/opt/ros/jazzy/opt/gz_transport_vendor/share/gz

# Auto-detect GPU
if [ -f /proc/driver/nvidia/version ]; then
  echo "[entrypoint] NVIDIA GPU detected"
  export __GLX_VENDOR_LIBRARY_NAME=nvidia
  export NVIDIA_DRIVER_CAPABILITIES=all
  unset LIBGL_ALWAYS_SOFTWARE
  unset GALLIUM_DRIVER
  unset MESA_GL_VERSION_OVERRIDE
elif [ -d /dev/dri ]; then
  echo "[entrypoint] AMD/Intel GPU detected"
  unset LIBGL_ALWAYS_SOFTWARE
  unset GALLIUM_DRIVER
  unset MESA_GL_VERSION_OVERRIDE
else
  echo "[entrypoint] No GPU found, using software rendering"
fi

# Source PX4 environment if available
if [ -f /px4/Tools/simulation/gz/setup_gz.bash ]; then
  source /px4/Tools/simulation/gz/setup_gz.bash
fi

exec "$@"
