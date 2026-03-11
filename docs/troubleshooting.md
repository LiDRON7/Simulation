# Troubleshooting

## Build fails on "git clone PX4-Autopilot" with TLS or DNS errors

The full recursive clone pulls around 25 submodules. Some of them are for
simulators you are not using (FlightGear, Gazebo Classic, jsbsim) and their
repos occasionally time out or have DNS failures inside Docker, especially
on macOS where Docker runs in a Linux VM with its own network stack.

The error looks like one of these:

    error: RPC failed; curl 56 GnuTLS recv error (-9): Error decoding the received TLS packet.
    fatal: unable to access '...': Could not resolve host: github.com
    Failed to clone '...' a second time, aborting

The fix is to stop using --recursive and only init the submodules needed for
Gazebo Harmonic SITL. Make sure your Dockerfile.dev and Dockerfile.ci have
the selective submodule init as shown below instead of --recursive:

```dockerfile
RUN git clone --branch v1.16.0 --depth 1 \
      https://github.com/PX4/PX4-Autopilot.git /px4 \
 && cd /px4 \
 && git submodule update --init --depth 1 \
      Tools/simulation/gz \
      src/modules/uxrce_dds_client/Micro-XRCE-DDS-Client \
      src/lib/cdrstream/cyclonedds \
      src/lib/cdrstream/rosidl \
      src/lib/events/libevents \
      src/modules/mavlink/mavlink \
      src/drivers/gps/devices \
      src/drivers/cyphal/libcanard \
      src/drivers/cyphal/public_regulated_data_types \
      src/lib/crypto/libtomcrypt \
      src/lib/crypto/libtommath \
      src/lib/crypto/monocypher \
      src/lib/heatshrink/heatshrink
```

If you already have a failed build layer cached, force a clean rebuild after
making the change:

    docker compose -f docker-compose.dev.yml build --no-cache

If the build still fails on a specific submodule after this change, it is a
transient GitHub network issue. Wait a few minutes and try again. These
failures are not consistent and usually resolve on retry.

## Build fails with "Unable to locate package"

The most common cause is the build running on arm64 (Apple Silicon Mac) where
some ROS 2 packages are not published. The fix is two things:

1. Make sure docker-compose.dev.yml has `platform: linux/amd64` under the
   drone-dev service. Pull the latest repo if unsure.

2. Make sure Rosetta emulation is enabled in Docker Desktop:
   Settings > General > "Use Rosetta for x86/amd64 emulation on Apple Silicon"

Then run:

    docker compose -f docker-compose.dev.yml build --no-cache

The --no-cache flag forces Docker to discard any arm64 layers it already built.
If you skip it the broken cached layers will be reused and the error will repeat.

Specific packages that do not exist in ROS 2 Jazzy and should not be in the
Dockerfile:

- ros-jazzy-point-cloud-msgs (use ros-jazzy-sensor-msgs instead)
- ros-jazzy-velodyne-simulator (not needed, LiDAR runs via Gazebo gpu_lidar plugin)

## Build fails with "exec format error" or platform mismatch

Docker is trying to run an arm64 binary on an amd64 runner or vice versa.
Make sure both docker-compose files have `platform: linux/amd64` and that
Rosetta is enabled on Mac. See setup-macos.md for details.

## Build fails with "no space left on device"

Docker has run out of disk space. Clean up unused images and build cache:

    docker system prune -a

Then retry the build. Docker Desktop on macOS defaults to a small virtual disk
size. Increase it in Docker Desktop > Settings > Resources > Virtual disk limit.
This project needs at least 40GB free for the image.

## Build hangs on "make px4_sitl_default"

PX4 is compiling. This step takes 15-30 minutes and will appear to hang with
no output. It is normal. If it is still running after 60 minutes something
is wrong. Check Docker Desktop > Resources and make sure you have given Docker
at least 8GB of RAM and 4 CPUs.

## VNC viewer says connection refused

The VNC server takes a few seconds to start after the container comes up. Wait
10 seconds and try again. If it still fails check that the container actually
started:

    docker ps

If drone_sim_dev is not in the list the container crashed on startup. Check
logs with:

    docker compose -f docker-compose.dev.yml logs

## VNC connects but screen is black

Gazebo is still loading. Wait up to 30 seconds. If the screen stays black
after that, check the container logs for errors:

    docker compose -f docker-compose.dev.yml logs drone-dev

## Gazebo opens but no drone model appears

The hexacopter model path is not being found. Check that your models folder
is being mounted correctly. In docker-compose.dev.yml the line:

    - ./models:/drone_sim/models

must point to the models folder in this repo. Run from the root of the repo,
not from inside a subfolder.

## ros2 topic list shows no topics

The ROS 2 bridge between Gazebo and ROS 2 takes a few seconds to start. Wait
10-15 seconds after the simulation loads and try again. If topics never appear:

    docker exec -it drone_sim_dev bash
    source /opt/ros/jazzy/setup.bash
    ros2 topic list

If that also shows nothing, the bridge process crashed. Check logs.

## MAVROS not connecting

MAVROS connects to PX4 over UDP. If /mavros/state shows connected: false,
PX4 SITL may still be initializing. It can take up to 20 seconds after Gazebo
loads for the MAVLink handshake to complete. If it never connects, make sure
nothing on your host is using ports 14540 or 14557.

## OAK-D Pro not detected in container

On Linux make sure you have added the udev rules described in setup-linux.md
and replugged the camera. On macOS USB passthrough through Docker has
limitations — the OAK-D Pro passthrough works best on Linux hosts.

## CI image pull fails with 403

Your repo does not have permission to pull from the drone-sim package. Go to:

github.com/orgs/your-org/packages/container/drone-sim/settings

Under "Manage Actions access" add your repo with Read role.

## Apple Silicon build is very slow

See the Apple Silicon note in docs/setup-macos.md. Make sure Rosetta
emulation is enabled in Docker Desktop. Building under emulation is 2-3x
slower than native but will complete correctly.

## Port 5900 already in use

Another VNC server is running on your machine. Either stop it or change the
host port in docker-compose.dev.yml from 5900 to something else like 5901,
then connect VNC viewer to localhost:5901.
