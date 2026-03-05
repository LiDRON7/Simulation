# Gazebo Simulation

Shared simulation environment for the drone research project. This repo runs a
hexacopter in Gazebo and is used as the testing infrastructure for the other
repos in this org

You do not write flight code here. You run the simulation here so other repos
can test against it.

## What is in this repo

A hexacopter with:

- Velodyne Puck Lite LiDAR (16-beam, 360 degree)
- OAK-D Pro depth camera (RGB + stereo depth)
- GPS and IMU via simulated Pixhawk (PX4 SITL)

Running in:

- Gazebo Harmonic — outdoor world with obstacles
- ROS 2 Jazzy — all sensor data available as standard ROS topics

Two Docker environments:

- dev: visual output, connect to it from your machine to see Gazebo
- ci: headless, used by other repos for automated testing

## Requirements

- Docker
- Docker Compose v2
- Git

See your platform doc for exact install steps and how to view the simulation:

- docs/setup-macos.md
- docs/setup-linux.md
- docs/setup-windows.md

## Setup

    git clone https://github.com/your-org/drone-sim.git
    cd drone-sim
    cp .env.example .env

Then follow your platform doc. The first build takes 20-40 minutes because
PX4 compiles from source. Subsequent builds use the cache and are fast.

## ROS 2 topics

Once the simulation is running these topics are available on ROS_DOMAIN_ID 0:

    /gps                            sensor_msgs/msg/NavSatFix
    /imu                            sensor_msgs/msg/Imu
    /lidar/points                   sensor_msgs/msg/PointCloud2
    /oakd/color/image               sensor_msgs/msg/Image
    /oakd/depth                     sensor_msgs/msg/Image
    /model/hexacopter/odometry      nav_msgs/msg/Odometry
    /mavros/state                   mavros_msgs/msg/State
    /hexacopter/command/twist       geometry_msgs/msg/Twist

Your code in other repos subscribes and publishes to these topics.

## How other repos use this for CI

The obstacle avoidance, path planning, and landing repos pull the CI image
from this repo and run it as a service during their integration tests. You
never need to build this repo in another repo's pipeline.

See docs/ci-integration.md for setup instructions.

## Docs

- docs/setup-macos.md
- docs/setup-linux.md
- docs/setup-windows.md
- docs/ci-integration.md
- docs/troubleshooting.md
