FROM ubuntu:22.04

# Minimal devcontainer Dockerfile to set up ROS2 Humble and Python tooling for the PoC.
# Note: Building this image may take several minutes in Codespaces / local Docker.

ENV DEBIAN_FRONTEND=noninteractive

# Setup locales
RUN apt-get update && apt-get install -y locales && locale-gen en_US.UTF-8
ENV LANG en_US.UTF-8
ENV LC_ALL en_US.UTF-8

# Install basic tools
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    gnupg2 \
    lsb-release \
    build-essential \
    git \
    ca-certificates \
    python3-pip \
    python3-venv \
    wget \
    sudo \
    nano \
    vim \
    xz-utils \
    && rm -rf /var/lib/apt/lists/*

# Install ROS2 Humble (binary) - sources and apt-key
RUN apt-get update && apt-get install -y software-properties-common
RUN curl -sSL https://raw.githubusercontent.com/ros/rosdistro/master/ros.key | apt-key add - || true
RUN sh -c 'echo "deb http://packages.ros.org/ros2/ubuntu $(lsb_release -cs) main" > /etc/apt/sources.list.d/ros2.list'
RUN apt-get update && apt-get install -y --no-install-recommends \
    ros-humble-desktop \
    ros-humble-gazebo-ros-pkgs \
    ros-humble-ros2-control \
    ros-humble-ros2-controllers \
    gazebo11 \
    libgazebo11-dev \
    && rm -rf /var/lib/apt/lists/*

# Make sure pip, colcon are available
RUN python3 -m pip install --upgrade pip
RUN python3 -m pip install colcon-common-extensions

# Create a non-root user 'vscode' with sudo
ARG USERNAME=vscode
ARG USER_UID=1000
ARG USER_GID=$USER_UID
RUN groupadd --gid $USER_GID $USERNAME \
    && useradd --uid $USER_UID --gid $USER_GID -m $USERNAME \
    && echo "$USERNAME ALL=(ALL) NOPASSWD:ALL" > /etc/sudoers.d/$USERNAME \
    && chmod 0440 /etc/sudoers.d/$USERNAME

USER $USERNAME
WORKDIR /home/$USERNAME

# Install python requirements for PoC into user environment (may be extended later)
RUN python3 -m pip install --user --upgrade pip
RUN python3 -m pip install --user -r /workspace/stp_poc/requirements.txt || true

# Set environment to source ROS on container start
RUN echo "source /opt/ros/humble/setup.bash" >> /home/$USERNAME/.bashrc

CMD ["/bin/bash"]
