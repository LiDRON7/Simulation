# LiDRON Simulation Environment

ROS 2 Jazzy · Gazebo Harmonic · PX4 · Docker

---

## Table of Contents

- [Overview](#overview)
- [Requirements](#requirements)
- [Setup: Linux (Ubuntu 24.04)](#setup-linux-ubuntu-2404)
- [Setup: macOS (via UTM Virtual Machine)](#setup-macos-via-utm-virtual-machine)
- [Setup: Windows (via WSL 2)](#setup-windows-via-wsl-2)
- [Build the Image](#build-the-image)
- [Run the Simulation](#run-the-simulation)
- [Build the ROS 2 Workspace](#build-the-ros-2-workspace)
- [Repository Structure](#repository-structure)
- [Troubleshooting](#troubleshooting)

---

## Overview

This repository packages a full drone simulation stack inside Docker. Gazebo handles the physics and rendering, PX4 runs as the flight controller, and your ROS 2 packages communicate with both over standard interfaces. The container runs the same way on a native Linux machine or a Linux VM on macOS.

---

## Requirements

| Tool | Version |
|------|---------|
| Docker Engine | 24+ |
| Docker Compose plugin | v2+ |
| Git | any |
| UTM *(macOS only)* | 4+ |

---

## Setup: Linux (Ubuntu 24.04)

### Install Docker

Do not use the `apt install docker.io` package. Use the official install script instead:

```bash
curl -fsSL https://get.docker.com -o get-docker.sh
sh get-docker.sh
```

Add your user to the `docker` group so you can run commands without `sudo`:

```bash
sudo usermod -aG docker $USER
newgrp docker
```

Install the Compose plugin:

```bash
sudo apt-get install docker-compose-plugin
```

Verify both are working:

```bash
docker version
docker compose version
```

### Clone the Repository

```bash
git clone https://github.com/LiDRON7/Simulation.git
cd Simulation
cp .env.example .env
```

Edit `.env` if you need to adjust any ports or paths.

### Configure X11 Display Access

Run this before starting the container each session. It grants Docker access to your local display so the Gazebo GUI can appear.

```bash
xhost +local:docker
touch /tmp/.docker.xauth
xauth nlist $DISPLAY | sed -e 's/^..../ffff/' | xauth -f /tmp/.docker.xauth nmerge -
```

You are ready to [build](#build-the-image).

---

## Setup: macOS (via UTM Virtual Machine)

Gazebo requires a Linux environment. On macOS, the recommended path is to run Ubuntu 24.04 inside a UTM virtual machine with a full desktop environment. The Gazebo GUI runs directly inside the VM window — no X forwarding needed.

### 1. Install UTM

Download UTM from [https://mac.getutm.app](https://mac.getutm.app) and install it.

### 2. Create an Ubuntu 24.04 VM

1. Download the Ubuntu 24.04 Server ISO from [https://ubuntu.com/download/server](https://ubuntu.com/download/server).
2. Open UTM and click **Create a New Virtual Machine**.
3. Select **Virtualize** (Apple Silicon) or **Emulate** (Intel Mac, slower).
4. Choose **Linux** and point it at the ISO you downloaded.
5. Allocate at least **8 GB RAM** and **60 GB disk**.
6. Complete the Ubuntu installer. Create a user and note the password.

### 3. Install a Desktop Environment

After the first boot, install Ubuntu Desktop and the SPICE guest agent:

```bash
sudo apt update
sudo apt install ubuntu-desktop spice-vdagent
sudo reboot
```

After the reboot, the VM will boot into a full graphical desktop. All remaining steps run inside a terminal in that desktop.

### 4. Install Docker

```bash
curl -fsSL https://get.docker.com -o get-docker.sh
sh get-docker.sh
sudo usermod -aG docker $USER
newgrp docker
sudo apt-get install docker-compose-plugin
```

Verify:

```bash
docker version
docker compose version
```

### 5. Clone the Repository

```bash
git clone https://github.com/LiDRON7/Simulation.git
cd Simulation
cp .env.example .env
```

### 6. Configure X11 Display Access

```bash
xhost +local:docker
touch /tmp/.docker.xauth
xauth nlist $DISPLAY | sed -e 's/^..../ffff/' | xauth -f /tmp/.docker.xauth nmerge -
```

Confirm your display variable is set:

```bash
echo $DISPLAY
```

It should print something like `:0` or `:1`. If it is empty, run:

```bash
export DISPLAY=:0
```

---

## Setup: Windows (via WSL 2)

Gazebo and Docker run inside a WSL 2 Ubuntu environment. The Gazebo GUI is handled by WSLg, which is built into Windows 11 and recent Windows 10 builds — no third-party X server needed.

### 1. Enable WSL 2

Open PowerShell as Administrator and run:

```powershell
wsl --install
```

This installs WSL 2 and Ubuntu by default. Restart your machine when prompted.

If WSL was already installed but on version 1, upgrade it:

```powershell
wsl --set-default-version 2
```

### 2. Open Ubuntu

Launch Ubuntu from the Start menu. On first run it will ask you to create a user and password.

Verify WSLg is working by running a simple GUI app:

```bash
sudo apt update
sudo apt install x11-apps -y
xeyes
```

A small window with eyes should appear on your Windows desktop. If it does, WSLg is working and Gazebo will render the same way. Close it and continue.

### 3. Install Docker

Do not install Docker Desktop. Run the official script inside Ubuntu:

```bash
curl -fsSL https://get.docker.com -o get-docker.sh
sh get-docker.sh
sudo usermod -aG docker $USER
newgrp docker
sudo apt-get install docker-compose-plugin
```

Verify:

```bash
docker version
docker compose version
```

### 4. Clone the Repository

```bash
git clone https://github.com/LiDRON7/Simulation.git
cd Simulation
cp .env.example .env
```

### 5. Configure X11 Display Access

```bash
xhost +local:docker
touch /tmp/.docker.xauth
xauth nlist $DISPLAY | sed -e 's/^..../ffff/' | xauth -f /tmp/.docker.xauth nmerge -
```

Confirm your display variable is set:

```bash
echo $DISPLAY
```

It should print something like `:0`. If it is empty, run:

```bash
export DISPLAY=:0
```

---

## Build the Image

```bash
docker compose -f docker-compose.dev.yml build
```

The first build takes 20 to 40 minutes depending on your machine. If you have more than 16 GB of RAM, you can speed up the PX4 compile step by editing `docker/Dockerfile.dev` and changing:

```
MAKEFLAGS="-j2"
```

to:

```
MAKEFLAGS="-j4"
```

---

## Run the Simulation

```bash
docker compose -f docker-compose.dev.yml up
```

The Gazebo window will appear on your desktop.

### Headless Mode (No Display)

If you are running on a server with no display, remove the `DISPLAY` and `/tmp/.X11-unix` entries from `docker-compose.dev.yml` and connect a VNC viewer to `localhost:5900`. The password is `px4vnc`.

### Stop

```bash
docker compose -f docker-compose.dev.yml down
```

---

## Build the ROS 2 Workspace

This only needs to be done the first time, or whenever you add new packages.

Open a shell inside the running container:

```bash
docker exec -it drone_sim_dev bash
```

Then build the workspace:

```bash
cd /drone_sim/ros2_ws
colcon build --symlink-install
```

---

## Repository Structure

```
Simulation/
├── docker-compose.dev.yml   # main compose file
├── .env                     # local config (gitignored, copy from .env.example)
├── .env.example             # template
│
├── docker/
│   ├── Dockerfile.dev       # container image definition
│   └── entrypoint.sh        # ROS 2 environment setup at container start
│
├── worlds/
│   └── outdoor_field.sdf    # default Gazebo world
│
├── models/
│   └── your_drone/          # drone model files (.sdf, .config, meshes/)
│
├── ros2_ws/
│   └── src/                 # ROS 2 packages
│
├── config/                  # ROS 2 params and flight configs
└── scripts/                 # helper scripts
```

The `ros2_ws/build/`, `ros2_ws/install/`, and `ros2_ws/log/` directories are generated by `colcon` and can be safely deleted. They will be recreated on the next build.

---

## Troubleshooting

**`could not select device driver "nvidia"`**  
Remove the `deploy.resources` GPU block from your compose file. This setup uses Mesa software rendering and does not need an Nvidia GPU.

**`Authorization required` / `could not connect to display`**  
Redo the X11 display setup for your platform. Make sure `$DISPLAY` is set and `/tmp/.docker.xauth` exists.

**`/tmp/.docker.xauth: no such file or directory`**  
Run `touch /tmp/.docker.xauth` before the `xauth nmerge` command.

**Gazebo opens but is very slow**  
Expected on a VM without GPU acceleration. The renderer falls back to llvmpipe (software). Lower world complexity or reduce the render resolution in `worlds/outdoor_field.sdf`.

**`colcon build` fails inside the container**  
Confirm the workspace is mounted correctly: `ls /drone_sim/ros2_ws/src` should list your packages. If the directory is empty, check the volume mounts in `docker-compose.dev.yml`.
