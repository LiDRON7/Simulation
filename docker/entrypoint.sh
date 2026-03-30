#!/bin/bash
# entrypoint.sh
# Sources the ROS 2 environment and then runs whatever CMD was passed.
# This is needed because Docker ENV doesn't run .bashrc.

set -e

source /opt/ros/jazzy/setup.bash

# Source the user workspace if it has been built
if [ -f /drone_sim/ros2_ws/install/setup.bash ]; then
  source /drone_sim/ros2_ws/install/setup.bash
fi

# Point Gazebo at your mounted model & world directories
export GZ_SIM_RESOURCE_PATH=/drone_sim/models:/drone_sim/worlds:${GZ_SIM_RESOURCE_PATH}

exec "$@"
