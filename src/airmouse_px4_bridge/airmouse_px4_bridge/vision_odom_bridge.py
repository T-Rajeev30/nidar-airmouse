"""
Reads SLAM's corrected pose (map->base_link tf, ENU/FLU) and publishes it
to PX4 as external vision odometry (NED/FRD), replacing GPS as PX4's
position reference.

Uses the same fixed NED<->ENU / FRD<->FLU quaternions as px4_odom_bridge -
both rotations are 180-degree, self-inverse, so the identical formula
converts in either direction.

KNOWN SIMPLIFICATION: publishes position + yaw only, no velocity -
EKF2_EV_CTRL is configured to match (bits 0,1,3, not bit 2).

"""

import rclpy
from rclpy.node import Node
from rclpy.qos import QoSProfile, ReliabilityPolicy, HistoryPolicy

import tf2_ros
from px4_msgs.msg import VehicleOdometry

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


class VisionOdomBridge(Node):
    def __init__(self):
        super().__init__('vision_odom_bridge')

        qos = QoSProfile(
            reliability=ReliabilityPolicy.BEST_EFFORT,
            history=HistoryPolicy.KEEP_LAST,
            depth=5,
        )

        self.pub = self.create_publisher(
            VehicleOdometry, '/fmu/in/vehicle_visual_odometry', qos
        )

        self.tf_buffer = tf2_ros.Buffer()
        self.tf_listener = tf2_ros.TransformListener(self.tf_buffer, self)

        self.timer = self.create_timer(1.0 / 30.0, self.publish_vision_odom)

        self.get_logger().info('vision_odom_bridge started - map pose -> PX4 external vision')

    def publish_vision_odom(self):
        try:
            tf = self.tf_buffer.lookup_transform('map', 'base_link', rclpy.time.Time())
        except (tf2_ros.LookupException, tf2_ros.ExtrapolationException, tf2_ros.ConnectivityException):
            return

        enu_x = tf.transform.translation.x
        enu_y = tf.transform.translation.y
        enu_z = tf.transform.translation.z

        q_enu = (
            tf.transform.rotation.w,
            tf.transform.rotation.x,
            tf.transform.rotation.y,
            tf.transform.rotation.z,
        )

        # Same transform as px4_odom_bridge, applied in reverse -
        # both constituent rotations are self-inverse (180 degrees).
        ned_x = enu_y
        ned_y = enu_x
        ned_z = -enu_z

        q_ned = quat_mult(quat_mult(NED_ENU_Q, q_enu), AIRCRAFT_BASELINK_Q)

        msg = VehicleOdometry()
        msg.timestamp = int(self.get_clock().now().nanoseconds / 1000)
        msg.timestamp_sample = msg.timestamp
        msg.pose_frame = VehicleOdometry.POSE_FRAME_NED

        msg.position = [float(ned_x), float(ned_y), float(ned_z)]
        msg.q = [float(q_ned[0]), float(q_ned[1]), float(q_ned[2]), float(q_ned[3])]

        # Known simplification: no velocity estimate from this bridge yet -
        # NaN tells EKF2 this field is not available, matching EKF2_EV_CTRL
        # being configured without the velocity bit.
        nan = float('nan')
        msg.velocity = [nan, nan, nan]
        msg.angular_velocity = [nan, nan, nan]

        msg.position_variance = [0.05, 0.05, 0.08]
        msg.orientation_variance = [0.05, 0.05, 0.15]
        msg.velocity_variance = [nan, nan, nan]

        self.pub.publish(msg)


def main(args=None):
    rclpy.init(args=args)
    node = VisionOdomBridge()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()
