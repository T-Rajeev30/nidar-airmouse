#!/bin/bash

echo "=== STEP 1: Killing everything ==="
pkill -9 -f "bin/px4" 2>/dev/null
pkill -9 -f "MicroXRCEAgent" 2>/dev/null
pkill -9 -f "gz sim" 2>/dev/null
pkill -9 -f "parameter_bridge" 2>/dev/null
pkill -9 -f "px4_odom_bridge" 2>/dev/null
pkill -9 -f "vision_odom_bridge" 2>/dev/null
pkill -9 -f "static_transform_publisher" 2>/dev/null
pkill -9 -f "slam_toolbox" 2>/dev/null
sleep 3

echo "=== STEP 2: Confirming clean slate ==="
LEFTOVER=$(ps aux | grep -E "bin/px4|MicroXRCEAgent|gz sim|parameter_bridge|px4_odom_bridge|static_transform_publisher|slam_toolbox" | grep -v grep)
if [ -n "$LEFTOVER" ]; then
    echo "FAILED - leftover processes still running:"
    echo "$LEFTOVER"
    exit 1
fi
echo "Clean."

echo "=== STEP 3: Starting agent + PX4 ==="
source ~/microxrce_ws/install/setup.bash
nohup MicroXRCEAgent udp4 -p 8888 > /tmp/agent.log 2>&1 &
sleep 3

export ROS_LOCALHOST_ONLY=0
export PX4_GZ_WORLD=nidar_arena
cd ~/PX4-Autopilot
nohup make px4_sitl gz_x500_lidar_2d > /tmp/px4.log 2>&1 &

echo "Waiting 25s for PX4 <-> agent connection..."
sleep 25
if ! grep -q "vehicle_odometry data writer" /tmp/px4.log; then
    echo "FAILED - PX4 never connected to agent. Check /tmp/px4.log"
    exit 1
fi
echo "Connected."

echo "=== STEP 4: Starting SLAM pipeline ==="
source /opt/ros/humble/setup.bash
source ~/nidar_airmouse_ws/install/setup.bash
nohup ros2 launch airmouse_mapping slam_stack.launch.py > /tmp/slam_full.log 2>&1 &

echo "Waiting 20s for SLAM to settle..."
sleep 20

echo "=== STEP 5: Checking /map ==="
MAP_OUTPUT=$(timeout 8 ros2 topic echo /map --once 2>&1)
if echo "$MAP_OUTPUT" | grep -q "does not appear to be published"; then
    echo "FAILED - /map has no data. Last 15 lines of SLAM log:"
    tail -15 /tmp/slam_full.log
    exit 1
fi

echo "SUCCESS - /map is publishing real data:"
echo "$MAP_OUTPUT" | head -20
