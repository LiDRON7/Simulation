#!/bin/bash
set -e

# Headless software rendering
export LIBGL_ALWAYS_SOFTWARE=1
export GZ_HEADLESS_RENDERING=1

source /opt/ros/jazzy/setup.bash

[ -f /drone_sim/ros2_ws/install/setup.bash ] && \
    source /drone_sim/ros2_ws/install/setup.bash

exec "$@"
