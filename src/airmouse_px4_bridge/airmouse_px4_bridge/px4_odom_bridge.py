"""
Converts PX4's VehicleOdometry (NED world, FRD body) into a standard
ROS2 nav_msgs/Odometry (ENU world, FLU body) plus a live odom->base_link
tf broadcast, so slam_toolbox and Nav2 can consume PX4's pose directly.
"""

import rclpy
from rclpy.node import Node
from rclpy.qos import QoSProfile, ReliabilityPolicy, HistoryPolicy

from px4_msgs.msg import VehicleOdometry
from nav_msgs.msg import Odometry
from geometry_msgs.msg import TransformStamped
from tf2_ros import TransformBroadcaster

NED_ENU_Q = (0.0, 0.70710678, 0.70710678, 0.0)
AIRCRAFT_BASELINK_Q = (0.0, 1.0, 0.0, 0.0)


def quat_mult(q1, q2):
    w1, x1, y1, z1 = q1
    w2, x2, y2, z2 = q2
    return (
        w1 * w2 - x1 * x2 - y1 * y2 - z1 * z2,
        w1 * x2 + x1 * w2 + y1 * z2 - z1 * y2,
        w1 * y2 - x1 * z2 + y1 * w2 + z1 * x2,
        w1 * z2 + x1 * y2 - y1 * x2 + z1 * w2,
    )


class Px4OdomBridge(Node):
    def __init__(self):
        super().__init__('px4_odom_bridge')

        qos = QoSProfile(
            reliability=ReliabilityPolicy.BEST_EFFORT,
            history=HistoryPolicy.KEEP_LAST,
            depth=5,
        )

        self.sub = self.create_subscription(
            VehicleOdometry, '/fmu/out/vehicle_odometry', self.callback, qos
        )
        self.pub = self.create_publisher(Odometry, '/odom', 10)
        self.tf_broadcaster = TransformBroadcaster(self)

        self.get_logger().info('px4_odom_bridge started')

    def callback(self, msg: VehicleOdometry):
        ned = msg.position
        enu_x = float(ned[1])
        enu_y = float(ned[0])
        enu_z = float(-ned[2])

        q_ned = (float(msg.q[0]), float(msg.q[1]), float(msg.q[2]), float(msg.q[3]))
        q_enu = quat_mult(quat_mult(NED_ENU_Q, q_ned), AIRCRAFT_BASELINK_Q)
        qw, qx, qy, qz = q_enu

        ned_v = msg.velocity
        enu_vx = float(ned_v[1])
        enu_vy = float(ned_v[0])
        enu_vz = float(-ned_v[2])

        ang = msg.angular_velocity
        flu_wx = float(ang[0])
        flu_wy = float(-ang[1])
        flu_wz = float(-ang[2])

        now = self.get_clock().now().to_msg()

        odom = Odometry()
        odom.header.stamp = now
        odom.header.frame_id = 'odom'
        odom.child_frame_id = 'base_link'

        odom.pose.pose.position.x = enu_x
        odom.pose.pose.position.y = enu_y
        odom.pose.pose.position.z = enu_z
        odom.pose.pose.orientation.w = qw
        odom.pose.pose.orientation.x = qx
        odom.pose.pose.orientation.y = qy
        odom.pose.pose.orientation.z = qz

        odom.twist.twist.linear.x = enu_vx
        odom.twist.twist.linear.y = enu_vy
        odom.twist.twist.linear.z = enu_vz
        odom.twist.twist.angular.x = flu_wx
        odom.twist.twist.angular.y = flu_wy
        odom.twist.twist.angular.z = flu_wz

        self.pub.publish(odom)

        tf = TransformStamped()
        tf.header.stamp = now
        tf.header.frame_id = 'odom'
        tf.child_frame_id = 'base_link'
        tf.transform.translation.x = enu_x
        tf.transform.translation.y = enu_y
        tf.transform.translation.z = enu_z
        tf.transform.rotation.w = qw
        tf.transform.rotation.x = qx
        tf.transform.rotation.y = qy
        tf.transform.rotation.z = qz
        self.tf_broadcaster.sendTransform(tf)


def main(args=None):
    rclpy.init(args=args)
    node = Px4OdomBridge()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()
