# Setup on Windows

Tested on Windows 10 (build 19041+) and Windows 11.

This setup uses WSL2 (Windows Subsystem for Linux) with Docker. You get a
full Ubuntu terminal environment and Docker runs inside it. This is the
recommended path for active development.

## Install WSL2 with Ubuntu 24.04

Open PowerShell as Administrator and run:

    wsl --install

This installs WSL2 with Ubuntu 24.04 by default. Restart when prompted.

After restart, open the Ubuntu app from the Start menu and complete the
first-time setup — it will ask you to create a Linux username and password.
These are separate from your Windows credentials.

Verify the install worked:

    wsl --list --verbose

You should see Ubuntu listed with VERSION 2. If it shows VERSION 1 run:

    wsl --set-version Ubuntu 2

## Install Docker Desktop

Download from https://docs.docker.com/desktop/install/windows-install

During install make sure "Use WSL 2 instead of Hyper-V" is selected.

After install, open Docker Desktop and go to:
Settings > Resources > WSL Integration

Enable integration for your Ubuntu distro. Apply and restart Docker Desktop.

Verify Docker is accessible from inside WSL by opening your Ubuntu terminal
and running:

    docker version
    docker compose version

If those commands are not found, Docker Desktop WSL integration is not enabled.
Go back to Settings > Resources > WSL Integration and make sure Ubuntu is toggled on.

## Install Git inside WSL

Open your Ubuntu terminal and run:

    sudo apt-get update && sudo apt-get install -y git

## Clone and configure

All remaining steps run inside your Ubuntu WSL terminal, not PowerShell.

    git clone https://github.com/your-org/drone-sim.git
    cd drone-sim
    cp .env.example .env

The defaults in .env work for local development.

## Build

    docker compose -f docker-compose.dev.yml build

Takes 20-40 minutes the first time. PX4 compiles from source during this step.
You will see a lot of compiler output — this is normal, do not close the terminal.

To speed up the build, open Docker Desktop > Settings > Resources and increase
CPUs to at least 4 and Memory to at least 8GB. Docker Desktop on Windows
defaults to low limits that will make this slow or cause it to run out of memory.

If your machine has more than 16GB of RAM you can also open docker/Dockerfile.dev
and change MAKEFLAGS="-j2" to MAKEFLAGS="-j4" to cut PX4 compile time roughly
in half.

## Run

    docker compose -f docker-compose.dev.yml up

You have two options for viewing the simulation.

### Option 1 — VNC viewer

Install RealVNC Viewer on Windows from https://www.realvnc.com/en/connect/download/viewer

Connect to localhost:5900. When asked for a password enter the value of
VNC_PASSWORD from your .env file. The default is px4vnc.

Gazebo will appear in the VNC window. It may take 10-15 seconds after
connecting for Gazebo to finish loading.

### Option 2 — X11 forwarding (Gazebo opens as a native window on your desktop)

Install VcXsrv from https://sourceforge.net/projects/vcxsrv

Launch XLaunch from the Start menu with these settings:

- Multiple windows
- Display number: 0
- Start no client
- Check "Disable access control"
- Leave everything else as default

In your Ubuntu WSL terminal, find the WSL gateway IP:

    cat /etc/resolv.conf | grep nameserver | awk '{print $2}'

Set your DISPLAY variable using that IP (replace 172.x.x.x with what you got):

    export DISPLAY=172.x.x.x:0

To make this permanent add that line to the bottom of your ~/.bashrc.

In your .env file set:

    ENABLE_VNC=false

In docker-compose.dev.yml add to the environment section:

    DISPLAY: $DISPLAY

And add to volumes:

    /tmp/.X11-unix:/tmp/.X11-unix

Start compose and Gazebo will open as a native window on your Windows desktop.

## Verify sensors are working

In a second Ubuntu terminal while the simulation is running:

    docker exec -it drone_sim_dev bash
    source /opt/ros/jazzy/setup.bash
    ros2 topic list

You should see all sensor topics listed. To confirm a topic is actively
publishing data:

    ros2 topic hz /lidar/points

## Stop

Press Ctrl+C in the terminal where compose is running, or run:

    docker compose -f docker-compose.dev.yml down

## Common issues

Docker Desktop says WSL 2 is not installed
Run `wsl --install` in PowerShell as Administrator and restart.

docker: command not found inside WSL
Docker Desktop WSL integration is not enabled. Go to Docker Desktop >
Settings > Resources > WSL Integration and toggle on your Ubuntu distro.

Build runs out of memory and fails
Open Docker Desktop > Settings > Resources and increase Memory to at least 8GB.

VNC connection refused
The VNC server starts a few seconds after the container comes up. Wait 10
seconds and try again. If it still fails check the container started:
`docker ps`

X11 window does not appear
Make sure XLaunch is running with "Disable access control" checked. Make sure
your DISPLAY variable is set to the WSL gateway IP not to localhost or 127.0.0.1.
Localhost does not route from inside WSL to the Windows host.

git clone asks for credentials
Use a GitHub personal access token as your password when prompted, or set up
SSH keys and clone with the SSH URL.

Port 5900 already in use
Change the host port in docker-compose.dev.yml from "5900:5900" to "5901:5900"
and connect VNC Viewer to localhost:5901 instead.
