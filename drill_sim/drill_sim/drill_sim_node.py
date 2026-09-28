import rclpy
from rclpy.node import Node
from sensor_msgs.msg import JointState
from std_msgs.msg import String
import math

class DrillSimNode(Node):
    def __init__(self):
        super().__init__('drill_sim')
        self.joint_pub = self.create_publisher(JointState, 'drill/joint_states', 10)
        self.cmd_sub = self.create_subscription(String, 'drill/command', self.command_cb, 10)
        self._spindle_rpm = 0.0
        self._running = False
        self._time = 0.0
        self.timer = self.create_timer(0.05, self.update)  # 20 Hz
        self.get_logger().info('drill_sim started')

    def command_cb(self, msg: String):
        cmd = msg.data.strip().lower()
        if cmd == 'start':
            self._running = True
            self.get_logger().info('Received START')
        elif cmd == 'stop':
            self._running = False
            self.get_logger().info('Received STOP')
        elif cmd.startswith('set_rpm'):
            parts = cmd.split()
            if len(parts) >= 2:
                try:
                    self._spindle_rpm = float(parts[1])
                    self.get_logger().info(f'Set RPM to {self._spindle_rpm}')
                except ValueError:
                    self.get_logger().warn('Invalid RPM value')
        else:
            self.get_logger().info(f'Unknown command: {cmd}')

    def update(self):
        # simple simulation: publish joint state with spindle velocity
        self._time += 0.05
        js = JointState()
        js.header.stamp = self.get_clock().now().to_msg()
        js.name = ['spindle']
        rad_per_sec = (self._spindle_rpm / 60.0) * 2.0 * math.pi if self._running else 0.0
        js.position = [rad_per_sec * self._time]
        js.velocity = [rad_per_sec]
        self.joint_pub.publish(js)


def main(args=None):
    rclpy.init(args=args)
    node = DrillSimNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()
