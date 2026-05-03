# LiDRON Simulation Environment

ROS 2 Jazzy · Gazebo Harmonic · PX4 · Docker

---

## Table of Contents

- [Overview](#overview)
- [Requirements](#requirements)
- [GPU Configuration](#gpu-configuration)
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

The stack runs three containers:

| Container | Role |
|---|---|
| `drone_sim_dev` | Gazebo Harmonic simulation server + GUI |
| `drone_px4` | PX4 SITL flight controller |
| `drone_ros` | ROS 2 gz bridge + optional MAVROS |

---

## Requirements

| Tool | Version |
|---|---|
| Docker Engine | 24+ |
| Docker Compose plugin | v2+ |
| Git | any |
| UTM _(macOS only)_ | 4+ |

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

Edit `.env` to set your GPU type — see [GPU Configuration](#gpu-configuration) above.

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

Edit `.env` to set your GPU type — see [GPU Configuration](#gpu-configuration) above. For an Apple Silicon VM, the default (everything commented out) is correct.

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

Edit `.env` to set your GPU type — see [GPU Configuration](#gpu-configuration) above.

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

The first build takes 20 to 40 minutes depending on your machine. PX4 is compiled from source during the build — this is the longest step.

---

## Run the Simulation

```bash
docker compose -f docker-compose.dev.yml up
```

The Gazebo window will appear on your desktop within a few seconds. The `drone_px4` container waits 20 seconds for Gazebo to finish loading before PX4 starts — this is normal.

When fully started you will see:

```
INFO  [commander] Ready for takeoff!
```

in the `drone_px4` logs. At this point the drone is spawned in Gazebo, all sensors are live, and the simulation is ready to accept commands.

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

Source ROS 2 inside any shell you open this way:

```bash
source /opt/ros/jazzy/setup.bash
```

---

### PX4 Flight Commands

PX4 module commands (`commander`, `param`, `listener`, etc.) are internal to the PX4 runtime — they are not Linux binaries. There are two ways to send them.

#### Option A — px4-commander binary (recommended)

The PX4 build exposes module commands as prefixed binaries inside the build directory. Run them directly with `docker exec`:

```bash
# Check vehicle status
docker exec drone_px4 bash -c "
  cd /px4/build/px4_sitl_default && ./bin/px4-commander status
"

# Arm the drone
docker exec drone_px4 bash -c "
  cd /px4/build/px4_sitl_default && ./bin/px4-commander arm
"

# Take off
docker exec drone_px4 bash -c "
  cd /px4/build/px4_sitl_default && ./bin/px4-commander takeoff
"

# Land
docker exec drone_px4 bash -c "
  cd /px4/build/px4_sitl_default && ./bin/px4-commander land
"

# Switch to Position Control mode
docker exec drone_px4 bash -c "
  cd /px4/build/px4_sitl_default && ./bin/px4-commander mode posctl
"

# Set a parameter
docker exec drone_px4 bash -c "
  cd /px4/build/px4_sitl_default && ./bin/px4-param set MPC_XY_VEL_MAX 5.0
"
```

#### Option B — QGroundControl (full GUI)

QGroundControl is the standard ground control station for PX4. It gives you a map view, HUD, parameter editor, and one-click takeoff/land/RTL.

**Install QGroundControl on your host machine:**

Download from [https://docs.qgroundcontrol.com/master/en/qgc-user-guide/getting_started/download_and_install.html](https://docs.qgroundcontrol.com/master/en/qgc-user-guide/getting_started/download_and_install.html)

**Connect to the simulation:**

PX4 SITL listens for MAVLink GCS connections on UDP port 14550. QGroundControl auto-detects this by default. Just launch QGroundControl while the simulation is running — it will connect automatically within a few seconds.

If it does not connect automatically, add a comm link manually:

1. Open **Application Settings** → **Comm Links**
2. Click **Add**
3. Set Type to **UDP**, port to **14550**
4. Click **Connect**

**What you can do in QGroundControl:**

- View live telemetry: altitude, speed, attitude, battery, GPS fix
- Arm and take off with the Takeoff button in the toolbar
- Set a target altitude for takeoff
- Switch flight modes from the mode selector
- Draw and upload waypoint missions
- View and edit all PX4 parameters
- Monitor sensor health and preflight checks
- Stream video from the depth camera (if configured)

---

### ROS 2 Topics

All `ros2` commands must be run with the ROS environment sourced. The easiest way is to prefix every `docker exec` call with the source command:

```bash
docker exec drone_ros bash -c "source /opt/ros/jazzy/setup.bash && ros2 topic list"
```

#### Active topics

When the simulation is running, the following topics are available:

| Topic | Message Type | Source | Description |
|---|---|---|---|
| `/clock` | `rosgraph_msgs/msg/Clock` | Gazebo | Simulation time |
| `/imu` | `sensor_msgs/msg/Imu` | Gazebo IMU sensor | Linear acceleration + angular velocity at 250 Hz |
| `/gps` | `sensor_msgs/msg/NavSatFix` | Gazebo NavSat sensor | GPS latitude, longitude, altitude at 10 Hz |
| `/oakd/color/image` | `sensor_msgs/msg/Image` | OAK-D camera | RGB color image at 30 Hz |
| `/oakd/color/camera_info` | `sensor_msgs/msg/CameraInfo` | OAK-D camera | Intrinsics for the color camera |
| `/oakd/depth/image` | `sensor_msgs/msg/Image` | OAK-D depth sensor | Depth image at 30 Hz |
| `/oakd/depth/points` | `sensor_msgs/msg/PointCloud2` | OAK-D depth sensor | 3D point cloud from depth camera |
| `/lidar/points` | `sensor_msgs/msg/PointCloud2` | 2D lidar | 360° laser scan as point cloud at 10 Hz |
| `/model/x500_depth_0/odometry` | `nav_msgs/msg/Odometry` | Gazebo | Ground-truth pose and velocity |

#### Useful commands

**List all active topics:**

```bash
docker exec drone_ros bash -c "source /opt/ros/jazzy/setup.bash && ros2 topic list"
```

**Print messages from a topic:**

```bash
docker exec drone_ros bash -c "source /opt/ros/jazzy/setup.bash && ros2 topic echo /imu"
docker exec drone_ros bash -c "source /opt/ros/jazzy/setup.bash && ros2 topic echo /gps"
docker exec drone_ros bash -c "source /opt/ros/jazzy/setup.bash && ros2 topic echo /model/x500_depth_0/odometry"
```

**Check publish rates:**

```bash
docker exec drone_ros bash -c "source /opt/ros/jazzy/setup.bash && ros2 topic hz /imu"
docker exec drone_ros bash -c "source /opt/ros/jazzy/setup.bash && ros2 topic hz /gps"
docker exec drone_ros bash -c "source /opt/ros/jazzy/setup.bash && ros2 topic hz /lidar/points"
docker exec drone_ros bash -c "source /opt/ros/jazzy/setup.bash && ros2 topic hz /oakd/depth/image"
```

**Inspect message type and fields:**

```bash
docker exec drone_ros bash -c "source /opt/ros/jazzy/setup.bash && ros2 topic info /imu"
docker exec drone_ros bash -c "source /opt/ros/jazzy/setup.bash && ros2 interface show sensor_msgs/msg/Imu"
```

**Check gz-level topics directly (bypasses the ROS bridge):**

```bash
docker exec drone_sim_dev gz topic -l
docker exec drone_sim_dev gz topic -e -t /world/outdoor_field/model/x500_depth_0/link/base_link/sensor/imu_sensor/imu -n 1
```

#### Subscribing from your own ROS 2 node

Your ROS 2 packages run in the `drone_ros` container and can subscribe to any of the topics above directly. The gz bridge is already running so no extra setup is needed. Example subscriber in Python:

```python
import rclpy
from rclpy.node import Node
from sensor_msgs.msg import NavSatFix

class GpsSubscriber(Node):
    def __init__(self):
        super().__init__('gps_sub')
        self.create_subscription(NavSatFix, '/gps', self.callback, 10)

    def callback(self, msg):
        self.get_logger().info(f'Lat: {msg.latitude:.6f}  Lon: {msg.longitude:.6f}')

rclpy.init()
rclpy.spin(GpsSubscriber())
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

PX4 exposes a MAVLink shell over UDP. The recommended way to send commands interactively is via the `mavlink_shell.py` script included with PX4.

**Open the MAVLink shell:**

```bash
docker exec -it drone_px4 bash
cd /px4
python3 Tools/mavlink_shell.py
```

Once connected you will see the `nsh>` prompt. Useful commands:

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

Exit the shell with `Ctrl+C` or type `exit`.

**Arm and take off in one sequence (quick test):**

```bash
commander arm && commander takeoff
```

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
docker exec -it drone_ros bash
```

Then build the workspace:

```bash
source /opt/ros/jazzy/setup.bash
cd /drone_sim/ros2_ws
colcon build --symlink-install
source install/setup.bash
```

---

## Repository Structure

```
Simulation/
├── docker-compose.dev.yml      # main compose file
├── .env                        # local config (gitignored, copy from .env.example)
├── .env.example                # template
│
├── docker/
│   ├── Dockerfile.dev          # container image definition
│   └── entrypoint.sh           # ROS 2 environment setup at container start
│
├── worlds/
│   └── outdoor_field.sdf       # Gazebo world with landing pad and obstacles
│
├── models/
│   └── x500_depth/             # local x500_depth model override (adds lidar)
│       ├── model.sdf
│       └── model.config
│
├── config/
│   ├── ros_gz_bridge.yaml      # gz <-> ROS 2 topic bridge configuration
│   ├── simulation_launch.py    # ROS 2 launch file (bridge + mavros)
│   └── px4_params.yaml         # PX4 parameter overrides
│
├── ros2_ws/
│   └── src/                    # your ROS 2 packages go here
│
└── scripts/                    # helper scripts
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

**`ros2: executable file not found in $PATH`**
Always source ROS before running ros2 commands via `docker exec`:
```bash
docker exec drone_ros bash -c "source /opt/ros/jazzy/setup.bash && ros2 topic list"
```

**`commander: command not found` in bash**
`commander` is an internal PX4 module, not a Linux binary. Use `./bin/px4-commander` from inside `/px4/build/px4_sitl_default/`, or use QGroundControl.

**Sensors show as missing in PX4 (`Preflight Fail: Accel Sensor 0 missing`)**
The world SDF is missing the sensor system plugins (`gz-sim-imu-system`, `gz-sim-air-pressure-system`, `gz-sim-navsat-system`). Verify they are present in `worlds/outdoor_field.sdf`.

**QGroundControl does not connect**
Make sure the simulation is fully started (`Ready for takeoff!` visible in logs) before launching QGroundControl. PX4 SITL listens on UDP port 14550. If auto-detect fails, add a manual UDP comm link to port 14550 in QGroundControl settings.

**`/lidar/points` topic not appearing**
Check that `worlds/outdoor_field.sdf` contains the `gz-sim-sensors-system` plugin with `<render_engine>ogre2</render_engine>`. The lidar sensor is rendered by the sensors system — it does not need a separate plugin.

**PX4 exits immediately after Gazebo starts**
The `sleep 20` in the px4 service is not long enough for your machine. Increase it to `sleep 30` in `docker-compose.dev.yml` and recreate the containers:
```bash
docker compose -f docker-compose.dev.yml down
docker compose -f docker-compose.dev.yml up --force-recreate
```
