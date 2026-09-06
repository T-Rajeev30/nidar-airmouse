# NIDAR AirMouse — Today's Session Recap

**A visual summary of the stack pivot, debugging journey, and first successful flight**

---

## 1. The Big Decision — Why We Pivoted

```mermaid
flowchart LR
    A["sjtu_drone<br/>+ Gazebo Classic"] -->|"custom PID plugin,<br/>not hardware-representative"| B{Pivot Decision}
    B -->|"chosen"| C["PX4 Autopilot<br/>+ Gazebo Harmonic"]
    C --> D["Real flight-stack firmware<br/>= sim-to-real transferable"]

    style A fill:#f9d5d5
    style C fill:#d5f9d9
    style D fill:#d5f9d9
```

Everything built on `sjtu_drone` was a working *simulation*, but not a working *hardware path* — the custom Gazebo Classic plugin would never run on real flight-controller hardware. PX4 does.

---

## 2. Today's Timeline

```mermaid
timeline
    title From cleanup to first real flight
    Morning : Cleaned old sjtu_drone workspace : Decided to pivot to PX4 + Gazebo Harmonic
    Midday  : Installed PX4-Autopilot + Gazebo Harmonic : Built Micro-XRCE-DDS Agent (source, via colcon) : Built px4_msgs
    Afternoon : Debugged PX4 ↔ ROS2 bridge (QoS mismatch) : Ported NIDAR arena into Harmonic : Fixed magnetic field + physics bugs in world file
    Evening : Fixed Gazebo viewport navigation (gizmo tool) : Installed QGroundControl : First successful manual flight
    Wrap-up : Pushed everything to GitHub : Wrote full project roadmap
```

---

## 3. Bugs Fixed Today

| # | Symptom | Root Cause | Fix |
|---|---|---|---|
| 1 | Gazebo Classic wouldn't run alongside Fortress | Version confusion (`ign gazebo` vs `gz sim`) | Identified correct commands per Gazebo generation |
| 2 | `ros2 topic list` showed nothing for `/fmu/*` topics | **QoS mismatch** — PX4 publishes `BEST_EFFORT`, default ROS2 subscriber wants `RELIABLE` | Used `qos_profile_sensor_data` explicitly |
| 3 | Micro-XRCE-DDS-Agent build failed | Broken upstream git tag in `v2.4.2`'s CMake fetch | Built via `colcon` (uses rosdep-resolved deps) instead of raw CMake |
| 4 | Old snap-installed agent couldn't create PX4 entities | Snap package hadn't been updated since 2023 — didn't know newer message types | Rebuilt agent from source, matching PX4's actual version |
| 5 | World file wouldn't load in Harmonic | `PX4_GZ_WORLD` env var didn't match internal `<world name>` | Renamed to match |
| 6 | Magnetometer reading ~10,000x too weak | Tangled edit history across Fortress → Classic → Harmonic left world properties broken | **Rebuilt the world file from `default.sdf`'s known-good preamble**, keeping only the wall geometry |
| 7 | Couldn't navigate the Gazebo viewport | Transform/rotate tool was active instead of Select tool | Switched toolbar tool |
| 8 | QGroundControl download kept failing | Stale CloudFront URL + wrong OS-version release | Found correct v5.0.8 asset (compatible with Ubuntu 22.04) via GitHub releases |

Eight real, separate root causes — each one looked like it could've been any of the others at first. This is what "the debugging was slow because everything looked the same" actually looks like in hindsight.

---

## 4. What We Ended Up With

```mermaid
flowchart TB
    subgraph Verified["✅ Verified Working Today"]
        direction TB
        A1["Gazebo Harmonic + Custom NIDAR Arena"]
        A2["x500 Airframe (~10\" prop class)"]
        A3["IMU + Magnetometer + Barometer + GPS<br/>(all reading real-world-accurate values)"]
        A4["PX4 ↔ ROS2 Bridge (uXRCE-DDS)"]
        A5["QGroundControl — Real Arm/Takeoff/Hover"]
    end
    A1 --> A2 --> A3 --> A4 --> A5
```

---

## 5. The Milestone Moment

```mermaid
sequenceDiagram
    participant You as Operator (QGroundControl)
    participant PX4
    participant GZ as Gazebo (nidar_arena)

    You->>PX4: Arm
    PX4->>PX4: Preflight checks PASS
    You->>PX4: Takeoff
    PX4->>GZ: Command motors
    GZ-->>PX4: Sensor feedback (IMU, GPS, Mag, Baro)
    PX4-->>You: Status: Flying, Hold, Alt 3.0m
    Note over You,GZ: First clean flight inside our own arena —<br/>no force-arm, no shortcuts, real preflight pass
    You->>PX4: Land
    PX4->>GZ: Descend + disarm
```

This is the flight shown in today's screenshot: **"Flying" → "Hold" → 3.0m altitude → 10 satellites → clean preflight.** Real ground-control link, real arm sequence — not a shell-command hack.

---

## 6. Where This Leaves Us

- **Foundation phase: complete.** Everything from here builds *on top of* a verified-working stack, not around unresolved uncertainty.
- **Actual mission-brief scoring work**: still ahead — lidar, SLAM, GPS-denied config, survivor detection, the mission FSM, and the GCS dashboard (see the full Project Plan document for the phase-by-phase breakdown).
- **Repo status**: pushed to `github.com/T-Rajeev30/nidar-airmouse`, ready for the next phase to build on.
