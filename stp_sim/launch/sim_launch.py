#!/usr/bin/env python3
"""
ROS2 Python launch file to start Gazebo (Ignition or classic) with the drill machine model
and spawn controllers via controller_manager spawners.

This launch assumes ROS2 Humble-style packages installed: gazebo_ros, robot_state_publisher,
ros2_control, ros2_controllers. Adjust paths and launch arguments to match your system.
"""

from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription, ExecuteProcess, TimerAction
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch_ros.actions import Node
import os

PACKAGE_SHARE = os.path.join(os.getcwd())
URDF_PATH = os.path.join(PACKAGE_SHARE, 'stp_sim', 'urdf', 'drill_machine.xacro')
CONTROLLERS = os.path.join(PACKAGE_SHARE, 'stp_sim', 'config', 'controllers.yaml')


def generate_launch_description():
    # Start Gazebo
    gazebo = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(os.path.join('/opt/ros/humble/share/gazebo_ros/launch', 'gazebo.launch.py')),
        launch_arguments={'verbose': 'true'}.items()
    )

    # Spawn robot state publisher to publish TF from URDF
    robot_state_pub = Node(
        package='robot_state_publisher',
        executable='robot_state_publisher',
        name='robot_state_publisher',
        output='screen',
        arguments=[URDF_PATH]
    )

    # Spawn controller manager spawners after a short delay to allow controller_manager to start
    spawn_joint_state_broadcaster = Node(
        package='controller_manager',
        executable='spawner',
        arguments=['joint_state_broadcaster'],
    )

    spawn_trajectory_controller = Node(
        package='controller_manager',
        executable='spawner',
        arguments=['joint_trajectory_controller'],
    )

    # A small demo publisher node to illustrate publishing a trajectory can be launched separately

    ld = LaunchDescription()
    ld.add_action(gazebo)
    ld.add_action(robot_state_pub)
    ld.add_action(TimerAction(period=3.0, actions=[spawn_joint_state_broadcaster]))
    ld.add_action(TimerAction(period=4.0, actions=[spawn_trajectory_controller]))

    return ld
