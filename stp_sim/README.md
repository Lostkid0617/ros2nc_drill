# Minimal README for the ROS2 drilling machine simulation PoC

This directory contains a minimal simulation skeleton for a 4-axis drilling machine (X/Y/Z prismatic + A rotary table) intended for use with ROS2, ros2_control and Gazebo.

Structure
- urdf/drill_machine.xacro      : xacro URDF model of the machine
- config/controllers.yaml       : ros2_control controllers configuration
- launch/sim_launch.py          : ROS2 launch file to start Gazebo & controller spawners
- scripts/send_demo_trajectory.py : simple ROS2 node to send a FollowJointTrajectory demo goal

Quick start (assumes ROS2 Humble and necessary packages installed)

1. Install dependencies (example for Ubuntu 22.04 / ROS2 Humble):
   sudo apt update
   sudo apt install -y ros-humble-desktop ros-humble-gazebo-ros-pkgs ros-humble-ros2-control ros-humble-ros2-controllers python3-colcon-common-extensions

2. From the repository root, run the launch:
   source /opt/ros/humble/setup.bash
   ros2 launch stp_sim/launch/sim_launch.py

3. In another terminal, run the demo trajectory sender (after sourcing ROS2):
   python3 stp_sim/scripts/send_demo_trajectory.py

Notes & next steps
- This is a lightweight PoC. The URDF and controller setup are intentionally simple. You should refine inertial/limit parameters, transmissions and the gazebo ros2_control hardware interface suited to your ROS2 distribution.
- Integrate your PoC STEP→feature→trajectory node by having it publish JointTrajectory goals to the same controller action server (/joint_trajectory_controller/follow_joint_trajectory).
- For more realistic drilling behavior, add Gazebo contact sensors and implement tool-workpiece interaction logic (e.g. detect penetration depth and mark holes completed).

