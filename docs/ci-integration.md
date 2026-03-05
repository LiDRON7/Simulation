# CI Integration

This document explains how repos in this org (obstacle avoidance, path
planning, landing) run their integration tests against this simulation.

The simulation repo publishes a headless CI Docker image to ghcr.io. Your
repo pulls that image and runs it as a service alongside your tests. You never
need to clone or build this simulation repo in your own CI pipeline.

## How it works

Your repo's GitHub Actions workflow:

1. Pulls the simulation CI image from ghcr.io
2. Starts it as a background service
3. Waits for the simulation to be ready
4. Runs your repo's test suite, which connects to the simulation via ROS 2
5. Reports results and tears everything down

## Adding simulation-based tests to your repo

In your repo (e.g. obstacle-avoidance), create this workflow file:

.github/workflows/integration-tests.yml

    name: Integration Tests

    on:
      push:
        branches: [main, develop]
      pull_request:
        branches: [main]

    jobs:
      integration:
        runs-on: ubuntu-24.04

        services:
          simulation:
            image: ghcr.io/your-org/drone-sim:ci
            credentials:
              username: ${{ github.actor }}
              password: ${{ secrets.GITHUB_TOKEN }}
            env:
              GZ_HEADLESS_RENDERING: "1"
              LIBGL_ALWAYS_SOFTWARE: "1"
              ROS_DOMAIN_ID: "0"
              PX4_SYS_AUTOSTART: "4006"
              PX4_GZ_MODEL: "hexacopter"
              PX4_GZ_WORLD: "outdoor_obstacles"
            options: >-
              --privileged

        steps:
          - name: Checkout your repo
            uses: actions/checkout@v4

          - name: Install ROS 2 Jazzy
            run: |
              sudo curl -sSL https://raw.githubusercontent.com/ros/rosdistro/master/ros.key \
                -o /usr/share/keyrings/ros-archive-keyring.gpg
              echo "deb [arch=$(dpkg --print-architecture) \
                signed-by=/usr/share/keyrings/ros-archive-keyring.gpg] \
                http://packages.ros.org/ros2/ubuntu noble main" \
                | sudo tee /etc/apt/sources.list.d/ros2.list
              sudo apt-get update
              sudo apt-get install -y ros-jazzy-ros-base python3-colcon-common-extensions

          - name: Wait for simulation to be ready
            run: |
              source /opt/ros/jazzy/setup.bash
              echo "Waiting for simulation topics..."
              for i in $(seq 1 30); do
                if ros2 topic list 2>/dev/null | grep -q "/lidar/points"; then
                  echo "Simulation is ready"
                  exit 0
                fi
                echo "Attempt $i/30 — waiting..."
                sleep 5
              done
              echo "Simulation did not become ready in time"
              exit 1

          - name: Build your package
            run: |
              source /opt/ros/jazzy/setup.bash
              cd ros2_ws
              colcon build --symlink-install

          - name: Run integration tests
            run: |
              source /opt/ros/jazzy/setup.bash
              source ros2_ws/install/setup.bash
              pytest tests/integration/ -v --timeout=120

          - name: Upload results
            if: always()
            uses: actions/upload-artifact@v4
            with:
              name: integration-test-results
              path: tests/integration/results/

## What the simulation exposes

All sensor data is published on ROS_DOMAIN_ID 0 and is available to your
test process on the same GitHub Actions runner network:

    /gps                            sensor_msgs/msg/NavSatFix
    /imu                            sensor_msgs/msg/Imu
    /lidar/points                   sensor_msgs/msg/PointCloud2
    /oakd/color/image               sensor_msgs/msg/Image
    /oakd/depth                     sensor_msgs/msg/Image
    /model/hexacopter/odometry      nav_msgs/msg/Odometry
    /mavros/state                   mavros_msgs/msg/State
    /hexacopter/command/twist       geometry_msgs/msg/Twist

## Sending commands to the drone in tests

To send velocity commands from your test:

    from geometry_msgs.msg import Twist
    import rclpy

    rclpy.init()
    node = rclpy.create_node('test_node')
    pub = node.create_publisher(Twist, '/hexacopter/command/twist', 10)

    msg = Twist()
    msg.linear.z = 1.0  # climb
    pub.publish(msg)

## Keeping the simulation image up to date

The CI image in this repo is rebuilt and pushed to ghcr.io automatically on
every merge to main. Your repo always pulls :ci which points to the latest
passing build. If you need to pin to a specific version use the SHA tag:

    ghcr.io/your-org/drone-sim:ci-<commit-sha>

## Required secret

Your repo needs read access to ghcr.io packages in this org. The default
GITHUB_TOKEN has this if both repos are in the same org. If you get a 403
when pulling the image, go to the drone-sim package settings on GitHub and
add your repo to the list of repos with read access.
