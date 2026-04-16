# Drone Simulation — Setup Guide

Tested on **Ubuntu 24.04 (native)** and **Ubuntu 24.04 VM on macOS** (Apple Silicon and Intel).  
Stack: ROS 2 Jazzy · Gazebo Harmonic · Docker.

---

## Requirements

| Tool | Version | Install |
|------|---------|---------|
| Docker Engine | 24+ | see below |
| Docker Compose plugin | v2+ | see below |
| Git | any | `sudo apt install git` |
| XQuartz *(macOS host only)* | 2.8+ | [xquartz.org](https://www.xquartz.org) |

---

## 1 — Install Docker

Do not use `apt install docker.io` — use the official script:

```bash
curl -fsSL https://get.docker.com -o get-docker.sh
sh get-docker.sh
```

Add your user to the docker group so you don't need `sudo`:

```bash
sudo usermod -aG docker $USER
newgrp docker
```

Install the Compose plugin:

```bash
sudo apt-get install docker-compose-plugin
```

Verify:

```bash
docker version
docker compose version
```

---

## 2 — Clone and configure

```bash
git clone https://github.com/LiDRON7/Simulation.git
cd Simulation
cp .env.example .env
```

Edit `.env` if you need to change any defaults (ports, paths).

---

## 3 — X11 display setup

The Gazebo GUI needs access to your display. Run this **before** starting the container each session.

### On a native Linux machine

```bash
xhost +local:docker
touch /tmp/.docker.xauth
xauth nlist $DISPLAY | sed -e 's/^..../ffff/' | xauth -f /tmp/.docker.xauth nmerge -
```

### On a Linux VM running on macOS

1. Install and launch **XQuartz** on your Mac.
2. In XQuartz → Preferences → Security, enable **"Allow connections from network clients"**.
3. Restart XQuartz after changing that setting.
4. SSH into your VM **with X11 forwarding**:
   ```bash
   ssh -X your_user@your_vm_ip
   ```
5. Inside the VM, run:
   ```bash
   xhost +local:docker
   touch /tmp/.docker.xauth
   xauth nlist $DISPLAY | sed -e 's/^..../ffff/' | xauth -f /tmp/.docker.xauth nmerge -
   ```
6. Confirm your display is set:
   ```bash
   echo $DISPLAY   # should print something like :10.0 or localhost:10.0
   ```
   If it's empty: `export DISPLAY=:0`

---

## 4 — Build

```bash
docker compose -f docker-compose.dev.yml build
```

First build takes 20–40 minutes. If your machine has more than 16 GB RAM, you can speed up the PX4 compile step by editing `docker/Dockerfile.dev` and changing:

```
MAKEFLAGS="-j2"   →   MAKEFLAGS="-j4"
```

---

## 5 — Run

```bash
docker compose -f docker-compose.dev.yml up
```

The Gazebo GUI will appear on your desktop (or forwarded via XQuartz on macOS).

### Headless / VNC mode

If you are on a server with no display, remove the `DISPLAY` and `/tmp/.X11-unix` entries from `docker-compose.dev.yml` and connect a VNC viewer to `localhost:5900` with password `px4vnc`.

---

## 6 — Build your ROS 2 workspace (first time)

Open a shell inside the running container:

```bash
docker exec -it drone_sim_dev bash
```

Then build:

```bash
cd /drone_sim/ros2_ws
colcon build --symlink-install
```

---

## 7 — OAK-D Pro USB access (Linux only)

If you're using the OAK-D Pro camera, add udev rules so the container can access the USB device:

```bash
echo 'SUBSYSTEM=="usb", ATTRS{idVendor}=="03e7", MODE="0666"' \
  | sudo tee /etc/udev/rules.d/80-movidius.rules
sudo udevadm control --reload-rules && sudo udevadm trigger
```

Replug the camera after running these commands.

---

## 8 — Stop

```bash
docker compose -f docker-compose.dev.yml down
```

---

## Repository structure

```
Simulation/
├── docker-compose.dev.yml   # main compose file
├── .env                     # local config (gitignored, copy from .env.example)
├── .env.example             # template
│
├── docker/
│   ├── Dockerfile.dev       # container image definition
│   └── entrypoint.sh        # ROS 2 env setup at container start
│
├── worlds/
│   └── outdoor_field.sdf    # default Gazebo world (required)
│
├── models/
│   └── your_drone/          # drone model files (.sdf, .config, meshes/)
│
├── ros2_ws/
│   └── src/                 # your ROS 2 packages (build/ install/ log/ are generated)
│
├── config/                  # ROS 2 params, flight configs (optional)
└── scripts/                 # helper scripts (optional)
```

The `ros2_ws/build/`, `ros2_ws/install/`, and `ros2_ws/log/` directories are generated inside the container and can be deleted safely — they'll be recreated on the next `colcon build`.

---

## Troubleshooting

**`could not select device driver "nvidia"`**  
The `deploy.resources` GPU block is still in your compose file. Delete it — this setup uses Mesa software rendering and does not require an Nvidia GPU.

**`Authorization required` / `could not connect to display`**  
Redo step 3. Make sure `$DISPLAY` is set and the xauth cookie file exists at `/tmp/.docker.xauth`.

**`/tmp/.docker.xauth: no such file or directory`**  
Run `touch /tmp/.docker.xauth` before the `xauth nmerge` command.

**Gazebo opens but is very slow**  
Expected on a VM with no GPU — the renderer is running in software (llvmpipe). Reduce world complexity or lower Gazebo's render resolution in the world `.sdf` file.

**`colcon build` fails inside the container**  
Make sure the workspace is mounted: `ls /drone_sim/ros2_ws/src` should list your packages. If it's empty, check the volume mounts in `docker-compose.dev.yml`.'
