from launch import LaunchDescription
from launch_ros.actions import Node


def generate_launch_description():
    sim_node = Node(
        package='drill_sim',
        executable='drill_sim',
        name='drill_sim',
        output='screen'
    )

    ld = LaunchDescription()
    ld.add_action(sim_node)
    return ld
