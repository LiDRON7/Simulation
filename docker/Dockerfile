FROM ubuntu:noble
ENV TZ=Etc/GMT-4

#QGroundControl Port
EXPOSE 18570 

RUN apt update && apt install locales -y
RUN locale-gen en_US en_US.UTF-8 && \
    update-locale LC_ALL=en_US.UTF-8 LANG=en_US.UTF-8 && \
    export LANG=en_US.UTF-8

RUN apt install software-properties-common -y && \
    add-apt-repository universe
RUN apt-get install -y curl gnupg2 lsb-release && \
    curl -sSL https://raw.githubusercontent.com/ros/rosdistro/master/ros.key \
    -o /usr/share/keyrings/ros-archive-keyring.gpg && \
    echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/ros-archive-keyring.gpg] \
    http://packages.ros.org/ros2/ubuntu $(lsb_release -cs) main" \
    > /etc/apt/sources.list.d/ros2.list

RUN apt update && apt upgrade -y && apt install ros-jazzy-ros-base -y
RUN echo "source /opt/ros/jazzy/setup.bash" > ~/.bashrc

RUN apt install sudo wget git -y
RUN curl https://packages.osrfoundation.org/gazebo.gpg --output /usr/share/keyrings/pkgs-osrf-archive-keyring.gpg
RUN echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/pkgs-osrf-archive-keyring.gpg] https://packages.osrfoundation.org/gazebo/ubuntu-stable $(lsb_release -cs) main" | sudo tee /etc/apt/sources.list.d/gazebo-stable.list > /dev/null && apt update
RUN apt install gz-harmonic ros-jazzy-ros-gz -y

RUN git clone https://github.com/PX4/PX4-Autopilot.git --recursive --depth 1 --shallow-submodules

RUN apt install python3-kconfiglib python3-jsonschema python3-jinja2 python3-pip -y
RUN python3 -m pip install pyros-genmsg --break-system-packages

CMD ["bash"]