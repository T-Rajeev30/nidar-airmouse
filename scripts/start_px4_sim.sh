#!/bin/bash
# Starts the uXRCE-DDS agent + PX4 SITL (Gazebo Harmonic, nidar_arena, lidar model).
# Run this FIRST, wait ~25s for it to fully connect, THEN run:
#   ros2 launch airmouse_mapping slam_stack.launch.py

pkill -9 -f px4 2>/dev/null
pkill -9 -f MicroXRCEAgent 2>/dev/null
pkill -9 -f "gz sim" 2>/dev/null
sleep 3

source ~/microxrce_ws/install/setup.bash
nohup MicroXRCEAgent udp4 -p 8888 > /tmp/agent.log 2>&1 &
sleep 3

export ROS_LOCALHOST_ONLY=0
export PX4_GZ_WORLD=nidar_arena
cd ~/PX4-Autopilot
nohup make px4_sitl gz_x500_lidar_2d > /tmp/px4.log 2>&1 &

echo "Waiting for PX4 <-> agent connection..."
sleep 20
grep "vehicle_odometry data writer" /tmp/px4.log && echo "CONNECTED - ready for slam_stack.launch.py" || echo "NOT CONNECTED YET - check /tmp/px4.log"
