# NIDAR AirMouse — Autonomous Indoor Search & Rescue Drone

## Current Stack (as of this commit)
- **Flight stack**: PX4 Autopilot (main branch) — chosen for real hardware transferability
- **Simulator**: Gazebo Harmonic (gz-sim 8.15.0)
- **Airframe**: x500 (generic ~10" propeller quadrotor, matches target hardware class)
- **ROS2**: Humble, bridged via uXRCE-DDS

## External Dependencies (clone separately, not vendored in this repo)
```bash
git clone https://github.com/PX4/PX4-Autopilot.git --recursive ~/PX4-Autopilot
cd ~/PX4-Autopilot && bash ./Tools/setup/ubuntu.sh

git clone -b v2.4.2 https://github.com/eProsima/Micro-XRCE-DDS-Agent.git ~/microxrce_ws/src/Micro-XRCE-DDS-Agent
# build via colcon, NOT raw cmake (raw build hits a broken upstream git tag reference)

git clone https://github.com/PX4/px4_msgs.git ~/px4_ros_ws/src/px4_msgs
# build via colcon
```

## Critical environment setup
`ROS_LOCALHOST_ONLY` must be **consistently set (0 or 1) across every terminal** — a mismatch causes silent, total DDS discovery failure with no error message. Add to `~/.bashrc`:
```bash
export ROS_LOCALHOST_ONLY=0
source /opt/ros/humble/setup.bash
source ~/px4_ros_ws/install/setup.bash
source ~/microxrce_ws/install/setup.bash
```

## Running the sim
```bash
# Terminal 1
MicroXRCEAgent udp4 -p 8888

# Terminal 2
export PX4_GZ_WORLD=nidar_arena
cd ~/PX4-Autopilot && make px4_sitl gz_x500
```
World file must be copied to `~/PX4-Autopilot/Tools/simulation/gz/worlds/nidar_arena.sdf` — see `src/airmouse_worlds/worlds/nidar_arena.sdf` in this repo (source of truth).

**Known gotcha**: any ROS2 subscription to `/fmu/out/*` topics MUST use `qos_profile_sensor_data` (BEST_EFFORT) — PX4 publishes best-effort, and a default RELIABLE subscriber silently receives nothing with no error.

## Status against mission brief
- ✅ Sim stack, arena, airframe, sensors, ROS2 bridge, manual flight — all working
- ❌ Not started: lidar sensor, SLAM, GPS-denied EKF2 config, survivor detection, autonomy FSM, GCS display

See `docs/` for detailed design notes (add as you go).
