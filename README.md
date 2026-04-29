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
- [Using the Container](#using-the-container)
- [Build the ROS 2 Workspace](#build-the-ros-2-workspace)
- [Repository Structure](#repository-structure)
- [Troubleshooting](#troubleshooting)

---

## Overview

This repository packages a full drone simulation stack inside Docker. Gazebo handles the physics and rendering, PX4 runs as the flight controller, and your ROS 2 packages communicate with both over standard interfaces. The container runs the same way on a native Linux machine or a Linux VM on macOS.

---

## Requirements

| Tool                  | Version |
| --------------------- | ------- |
| Docker Engine         | 24+     |
| Docker Compose plugin | v2+     |
| Git                   | any     |
| UTM _(macOS only)_    | 4+      |

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

This must be repeated after every reboot. It grants the container permission to open windows on your local display.

**Step 1 — Confirm your display variable is set:**

```bash
echo $DISPLAY
```

It should print something like `:0` or `:1`. If it is empty, set it manually:

```bash
export DISPLAY=:0
```

Do not continue until `$DISPLAY` is non-empty. The `xauth` command will produce no output and write nothing to the auth file if `$DISPLAY` is unset, and Gazebo will fail to open a window.

**Step 2 — Grant Docker access and create the auth file:**

```bash
xhost +local:docker
touch /tmp/.docker.xauth
xauth nlist $DISPLAY | sed -e 's/^..../ffff/' | xauth -f /tmp/.docker.xauth nmerge -
```

**Step 3 — Verify the auth file has entries:**

```bash
xauth -f /tmp/.docker.xauth list
```

You should see at least one line containing your display number and a hex key, for example:

```
hostname/unix:0  MIT-MAGIC-COOKIE-1  <hex string>
```

If the output is empty, `$DISPLAY` was not set correctly in Step 1. Fix it and repeat from Step 2.

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

**Step 1 — Confirm your display variable is set:**

```bash
echo $DISPLAY
```

It should print something like `:0` or `:1`. If it is empty, run:

```bash
export DISPLAY=:0
```

**Step 2 — Grant Docker access and create the auth file:**

```bash
xhost +local:docker
touch /tmp/.docker.xauth
xauth nlist $DISPLAY | sed -e 's/^..../ffff/' | xauth -f /tmp/.docker.xauth nmerge -
```

**Step 3 — Verify the auth file has entries:**

```bash
xauth -f /tmp/.docker.xauth list
```

At least one line should appear. If the output is empty, revisit Step 1.

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

**Step 1 — Confirm your display variable is set:**

```bash
echo $DISPLAY
```

It should print something like `:0`. If it is empty, run:

```bash
export DISPLAY=:0
```

**Step 2 — Grant Docker access and create the auth file:**

```bash
xhost +local:docker
touch /tmp/.docker.xauth
xauth nlist $DISPLAY | sed -e 's/^..../ffff/' | xauth -f /tmp/.docker.xauth nmerge -
```

**Step 3 — Verify the auth file has entries:**

```bash
xauth -f /tmp/.docker.xauth list
```

At least one line should appear. If the output is empty, revisit Step 1.

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

The Gazebo window will appear on your desktop. The `drone_px4` container waits 8 seconds for Gazebo to finish loading before PX4 starts — this is normal.

### Headless Mode (No Display)

If you are running on a server with no display, remove the `DISPLAY` and `/tmp/.X11-unix` entries from `docker-compose.dev.yml` and connect a VNC viewer to `localhost:5900`. The password is `px4vnc`.

### Stop

```bash
docker compose -f docker-compose.dev.yml down
```

---

## Using the Container

### Open a Shell

Open an interactive shell inside the simulation container:

```bash
docker exec -it drone_sim_dev bash
```

Or inside the PX4 container:

```bash
docker exec -it drone_px4 bash
```

The ROS 2 environment is sourced automatically by the entrypoint, so `ros2` commands work immediately in any shell you open this way.

---

### PX4 Commands

PX4 module commands (`commander`, `param`, `listener`, etc.) are **internal PX4 modules**, not Linux binaries. They only exist inside the PX4 console — typing them directly in the container's bash shell will always give `command not found`.

PX4 runs inside a `screen` session named `px4` inside the `drone_px4` container. This gives it a real TTY and lets you attach and detach cleanly without killing the process.

#### Attach to the PX4 console

```bash
docker exec -it drone_px4 screen -r px4
```

You will land at the `pxh>` prompt. Everything typed here runs inside PX4.

**To detach without stopping PX4:** press `Ctrl+A` then `D`. This leaves PX4 running and returns you to your host terminal.

**Do not press `Ctrl+C`** — this sends SIGINT to PX4 and will shut it down.

#### Useful pxh> commands

| Command                           | Description                                           |
| --------------------------------- | ----------------------------------------------------- |
| `commander status`                | Show arming state, flight mode, and health flags      |
| `commander arm`                   | Arm the drone (requires no failsafes active)          |
| `commander disarm`                | Disarm the drone                                      |
| `commander takeoff`               | Take off to the default altitude                      |
| `commander land`                  | Land at the current position                          |
| `commander mode posctl`           | Switch to Position Control mode                       |
| `commander mode offboard`         | Switch to Offboard mode (needed for ROS 2 control)    |
| `param show <name>`               | Print the value of a parameter                        |
| `param set <name> <value>`        | Set a parameter (e.g. `param set MPC_XY_VEL_MAX 5.0`) |
| `listener vehicle_local_position` | Stream position estimates to the terminal             |
| `listener vehicle_status`         | Stream vehicle status                                 |
| `top`                             | Show PX4 task CPU and memory usage                    |

#### Arm and take off (quick test)

At the `pxh>` prompt:

```
commander arm
commander takeoff
```

Run these as two separate commands. The `&&` chaining syntax does not work inside `pxh>`.

---

### ROS 2 Topics

All ROS 2 commands below run inside the `drone_sim_dev` container.

**List all active topics:**

```bash
ros2 topic list
```

**Common topics published by PX4 via `px4_ros_com`:**

| Topic                              | Message Type                     | Description                               |
| ---------------------------------- | -------------------------------- | ----------------------------------------- |
| `/fmu/out/vehicle_local_position`  | `px4_msgs/VehicleLocalPosition`  | NED position and velocity estimate        |
| `/fmu/out/vehicle_global_position` | `px4_msgs/VehicleGlobalPosition` | GPS latitude, longitude, altitude         |
| `/fmu/out/vehicle_attitude`        | `px4_msgs/VehicleAttitude`       | Orientation quaternion                    |
| `/fmu/out/vehicle_status`          | `px4_msgs/VehicleStatus`         | Arming state, nav state, flight mode      |
| `/fmu/out/sensor_combined`         | `px4_msgs/SensorCombined`        | Raw IMU (gyro + accelerometer)            |
| `/fmu/out/battery_status`          | `px4_msgs/BatteryStatus`         | Battery voltage and percentage            |
| `/fmu/in/trajectory_setpoint`      | `px4_msgs/TrajectorySetpoint`    | Send position/velocity setpoints          |
| `/fmu/in/vehicle_command`          | `px4_msgs/VehicleCommand`        | Send MAVLink commands (arm, mode changes) |
| `/fmu/in/offboard_control_mode`    | `px4_msgs/OffboardControlMode`   | Enable offboard control heartbeat         |

**Subscribe to a topic and print messages:**

```bash
ros2 topic echo /fmu/out/vehicle_local_position
```

**Check the publish rate of a topic:**

```bash
ros2 topic hz /fmu/out/vehicle_local_position
```

**Inspect the message type and field definitions:**

```bash
ros2 topic info /fmu/out/vehicle_local_position
ros2 interface show px4_msgs/msg/VehicleLocalPosition
```

**Camera and sensor topics (if the OakD-Lite model is loaded):**

| Topic                           | Description                       |
| ------------------------------- | --------------------------------- |
| `/drone/camera/image_raw`       | RGB image from the forward camera |
| `/drone/camera/camera_info`     | Camera intrinsics                 |
| `/drone/stereo/left/image_raw`  | Left stereo image                 |
| `/drone/stereo/right/image_raw` | Right stereo image                |
| `/drone/depth/image_raw`        | Depth image                       |

**View the node graph** (run outside the container, requires `rqt` installed on the host):

```bash
rqt_graph
```

Or inside the container:

```bash
ros2 run rqt_graph rqt_graph
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
Redo the X11 display setup for your platform. Make sure `$DISPLAY` is set and the `xauth list` verification step shows at least one entry.

**`/tmp/.docker.xauth: no such file or directory`**  
Run `touch /tmp/.docker.xauth` before the `xauth nmerge` command.

**`xauth nlist` produces no output / auth file is empty**  
`$DISPLAY` was not set when you ran the xauth commands. Set it with `export DISPLAY=:0` and repeat the entire X11 setup block.

**Gazebo opens but is very slow**  
Expected on a VM without GPU acceleration. The renderer falls back to llvmpipe (software). Lower world complexity or reduce the render resolution in `worlds/outdoor_field.sdf`.

**`colcon build` fails inside the container**  
Confirm the workspace is mounted correctly: `ls /drone_sim/ros2_ws/src` should list your packages. If the directory is empty, check the volume mounts in `docker-compose.dev.yml`.

**`param: not found` or `commander: command not found` in bash**  
`param`, `commander`, and other PX4 modules are internal to the PX4 runtime — they are not Linux binaries and cannot be called from a bash shell. Connect to the running PX4 process first: `python3 Tools/mavlink_shell.py udp:127.0.0.1:14556` from inside the `drone_px4` container, then run these commands at the `nsh>` prompt.

**`mavlink_shell.py`: `Error: no serial connection found`**  
You ran `mavlink_shell.py` without arguments, which looks for a serial port. In SITL there is no serial port. Always pass the UDP address explicitly: `python3 Tools/mavlink_shell.py udp:127.0.0.1:14556`.

**PX4 topics are not visible in `ros2 topic list`**  
The `px4_ros_com` bridge may not be running. Inside `drone_sim_dev`, run `ros2 node list` and confirm you see a `micrortps_agent` or `micro_ros_agent` node. If not, start it manually:

```bash
MicroXRCEAgent udp4 -p 8888
```
