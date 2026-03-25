# Setup on Linux

Tested on Ubuntu 24.04. The host machine and container both run Ubuntu 24.04
so there is no emulation overhead and builds are fastest here.

## Install Docker Engine

Do not install Docker via apt directly, use the official script:

    curl -fsSL https://get.docker.com -o get-docker.sh
    sh get-docker.sh

Add your user to the docker group so you do not need sudo:

    sudo usermod -aG docker $USER
    newgrp docker

Install the Compose plugin:

    sudo apt-get install docker-compose-plugin

Verify both work:

    docker version
    docker compose version

## Clone and configure

    git clone https://github.com/LiDRON7/Simulation.git
    cd Simulation
    cp .env.example .env

## Build

    docker compose -f docker-compose.dev.yml build

First build takes 20-40 minutes. On a machine with more than 16GB of RAM you
can open docker/Dockerfile.dev and change MAKEFLAGS="-j2" to MAKEFLAGS="-j4"
to cut the PX4 compile time roughly in half.

## Run

    docker compose -f docker-compose.dev.yml up

Gazebo GUI will appear directly on your desktop. Before starting, allow the
container to use your X display:

    xhost +local:docker

If you prefer VNC instead (e.g. on a headless server), remove the DISPLAY
and X11 socket entries from docker-compose.dev.yml and connect a VNC viewer
to localhost:5900 with password px4vnc.

## OAK-D Pro USB access

On Linux you may need to add udev rules for the OAK-D Pro:

    echo 'SUBSYSTEM=="usb", ATTRS{idVendor}=="03e7", MODE="0666"' \
      | sudo tee /etc/udev/rules.d/80-movidius.rules
    sudo udevadm control --reload-rules && sudo udevadm trigger

Then replug the camera.

## Stop

    docker compose -f docker-compose.dev.yml down
