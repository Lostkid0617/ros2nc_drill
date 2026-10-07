#!/usr/bin/env python3
"""Simple ROS2 node to send a demo FollowJointTrajectory goal to the joint_trajectory_controller.
Requires rclpy and control_msgs/trajectory_msgs installed in your ROS2 environment.
"""
import rclpy
from rclpy.node import Node
from trajectory_msgs.msg import JointTrajectory, JointTrajectoryPoint
from control_msgs.action import FollowJointTrajectory
from rclpy.action import ActionClient
import math

class TrajSender(Node):
    def __init__(self):
        super().__init__('traj_sender')
        self._action_client = ActionClient(self, FollowJointTrajectory, '/joint_trajectory_controller/follow_joint_trajectory')
        self.joints = ['x_axis_joint','y_axis_joint','z_axis_joint','a_axis_joint']

    def send_demo(self):
        self._action_client.wait_for_server()
        goal_msg = FollowJointTrajectory.Goal()
        traj = JointTrajectory()
        traj.joint_names = self.joints

        # simple demo: move X,Y to a couple positions, Z down/up, A rotate
        p1 = JointTrajectoryPoint()
        p1.positions = [0.05, 0.0, 0.0, 0.0]
        p1.time_from_start = rclpy.duration.Duration(seconds=2.0).to_msg()

        p2 = JointTrajectoryPoint()
        p2.positions = [0.05, 0.05, -0.05, math.radians(45.0)]
        p2.time_from_start = rclpy.duration.Duration(seconds=4.0).to_msg()

        p3 = JointTrajectoryPoint()
        p3.positions = [0.0, 0.0, 0.0, 0.0]
        p3.time_from_start = rclpy.duration.Duration(seconds=6.0).to_msg()

        traj.points = [p1, p2, p3]
        goal_msg.trajectory = traj

        self.get_logger().info('Sending trajectory...')
        send_goal_future = self._action_client.send_goal_async(goal_msg)
        rclpy.spin_until_future_complete(self, send_goal_future)

        goal_handle = send_goal_future.result()
        if not goal_handle.accepted:
            self.get_logger().error('Goal rejected')
            return
        self.get_logger().info('Goal accepted')
        get_result_future = goal_handle.get_result_async()
        rclpy.spin_until_future_complete(self, get_result_future)
        result = get_result_future.result()
        self.get_logger().info('Result: {0}'.format(result.status))

def main(args=None):
    rclpy.init(args=args)
    node = TrajSender()
    try:
        node.send_demo()
    finally:
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()
