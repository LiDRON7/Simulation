# Setup on macOS

Tested on macOS Ventura and Sonoma, Apple Silicon and Intel.

## Install dependencies

Install Docker Desktop from docker.com/products/docker-desktop. Once installed,
open Docker Desktop and let it finish starting up before continuing.

Install RealVNC Viewer from realvnc.com/en/connect/download/viewer. This is
what you use to see the Gazebo simulation running inside the container.

Install Git if you do not have it. Running `git --version` in Terminal will
prompt you to install it if missing.

## Apple Silicon note

The Dockerfiles are built for linux/amd64. On Apple Silicon (M1/M2/M3) Docker
Desktop runs this via Rosetta emulation. It works but the initial build will
be slower. To enable Rosetta emulation in Docker Desktop go to:

Settings > General > enable "Use Rosetta for x86/amd64 emulation"

If you skip this the build will fail with a platform mismatch error.

## Clone and configure

    git clone https://github.com/LiDRON7/Simulation.git
    cd Simulation
    cp .env.example .env

The defaults in .env work for local development. You only need to change
GITHUB_REPOSITORY if you are pushing images to the registry.

## Build

    docker compose -f docker-compose.dev.yml build

This takes 20-40 minutes the first time. Subsequent builds use the cache and
are much faster unless you change a Dockerfile.

## Run

    docker compose -f docker-compose.dev.yml up

Open RealVNC Viewer, click the plus button to add a connection, enter
localhost:5900 as the address. Connect. When prompted for a password enter
the VNC_PASSWORD from your .env file (default is px4vnc).

Gazebo will open in the VNC window showing the hexacopter in the outdoor
obstacle world. It may take 10-15 seconds after the VNC window opens for
Gazebo to fully load.

## Stop

Press Ctrl+C in the terminal where compose is running. If the container does
not stop cleanly run:

    docker compose -f docker-compose.dev.yml down

## Verify sensors are working

In a separate terminal while the simulation is running:

    docker exec -it drone_sim_dev bash
    source /opt/ros/jazzy/setup.bash
    ros2 topic list

You should see all the sensor topics listed. To check a specific topic is
publishing data:

    ros2 topic hz /lidar/points
