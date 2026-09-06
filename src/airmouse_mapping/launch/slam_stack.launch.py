"""
Brings up the full ROS2-side SLAM pipeline: clock bridge, lidar bridge,
PX4 odometry bridge, the static lidar-mount tf, and slam_toolbox.

Assumes PX4 SITL + the uXRCE-DDS agent are ALREADY running separately
(they're external processes, not ROS2 nodes) - see scripts/start_px4_sim.sh.
"""

import os
from launch import LaunchDescription
from launch.actions import ExecuteProcess
from launch_ros.actions import Node
from ament_index_python.packages import get_package_share_directory

LIDAR_TOPIC = "/world/nidar_arena/model/x500_lidar_2d_0/link/link/sensor/lidar_2d_v2/scan"


def generate_launch_description():
    slam_params = os.path.join(
        get_package_share_directory('airmouse_mapping'),
        'config', 'slam_params.yaml'
    )

    clock_bridge = ExecuteProcess(
        cmd=['ros2', 'run', 'ros_gz_bridge', 'parameter_bridge',
             '/clock@rosgraph_msgs/msg/Clock[gz.msgs.Clock'],
        output='screen'
    )

    lidar_bridge = ExecuteProcess(
        cmd=['ros2', 'run', 'ros_gz_bridge', 'parameter_bridge',
             f'{LIDAR_TOPIC}@sensor_msgs/msg/LaserScan[gz.msgs.LaserScan',
             '--ros-args', '-r', f'{LIDAR_TOPIC}:=/scan'],
        output='screen'
    )

    odom_bridge = Node(
        package='airmouse_px4_bridge',
        executable='px4_odom_bridge',
        name='px4_odom_bridge',
        parameters=[{'use_sim_time': True}],
        output='screen'
    )

    lidar_static_tf = Node(
        package='tf2_ros',
        executable='static_transform_publisher',
        name='lidar_static_tf',
        arguments=['--x', '-0.1', '--y', '0', '--z', '0.26',
                   '--frame-id', 'base_link', '--child-frame-id', 'link'],
        parameters=[{'use_sim_time': True}],
        output='screen'
    )

    slam = Node(
        package='slam_toolbox',
        executable='async_slam_toolbox_node',
        name='slam_toolbox',
        parameters=[slam_params],
        output='screen'
    )

    return LaunchDescription([
        clock_bridge,
        lidar_bridge,
        odom_bridge,
        lidar_static_tf,
        slam,
    ])
