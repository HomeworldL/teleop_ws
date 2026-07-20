# teleop_ws

ROS 2 workspace for Marvin dual-arm and Wuji dexterous-hand teleoperation.

This repository contains the robot-side drivers, teleoperation input devices,
teleoperation algorithms, whole-robot visualization, and dummy bringup needed to
test the system before connecting real hardware.

Chinese translation: [README_zh.md](README_zh.md).

## Package Overview

### Robot Devices

- [`src/marvin_ros2`](src/marvin_ros2/README.md): Marvin dual-arm ROS 2
  integration. It contains the low-level driver, launch files, SDK vendor copy,
  control-mode configuration, and arm bringup notes.
- [`src/marvin_ros2/marvin_driver`](src/marvin_ros2/marvin_driver/README.md):
  C++ ROS 2 wrapper around the old Tianji Marvin controller SDK. It owns the
  controller TCP connection and exposes per-arm feedback and command topics.
- [`src/marvin_ros2/marvin_bringup`](src/marvin_ros2/marvin_bringup/README.md):
  launch/config package for Marvin position, joint impedance, joint impedance
  PD-feedforward, zero-motion helpers, and the manual joint-control UI.
- [`src/wujihandros2`](src/wujihandros2/README.md): Wuji Hand ROS 2 driver
  packages integrated into this workspace as normal source packages.
- `src/wujihandros2/wujihand_driver`: Wuji Hand hardware driver.
- `src/wujihandros2/wujihand_bringup`: Wuji Hand launch files for single-hand
  and dual-hand driver startup.
- `src/wujihandros2/wujihand_msgs`: Wuji Hand custom messages and services.

### Teleoperation Devices

- [`src/teleop_device/wuji_glove`](src/teleop_device/wuji_glove/README.md):
  connects Wuji Glove through `wuji_sdk` and publishes 21-keypoint hand
  skeletons.
- [`src/teleop_device/vive_openvr`](src/teleop_device/vive_openvr/README.md):
  reads HTC Vive Trackers through SteamVR/OpenVR and publishes tracker TF plus
  `PoseStamped` topics.

### Teleoperation Algorithms

- [`src/teleop_algorithm/wujihand_teleop`](src/teleop_algorithm/wujihand_teleop/README.md):
  retargets Wuji Glove keypoints into Wuji Hand joint commands.
- [`src/teleop_algorithm/vive_marvin_teleop`](src/teleop_algorithm/vive_marvin_teleop/README.md):
  maps Vive chest/wrist tracker TF into Marvin arm TCP targets, solves IK with
  the vendored Marvin kinematics SDK, and publishes arm joint commands.

### Whole-Robot Integration

- [`src/robot_description`](src/robot_description/README.md): composed
  whole-robot URDF/MJCF model for the Marvin arms, Wuji hands, base, adapters,
  and RViz visualization frames. It uses the Marvin and Wuji description
  resource packages instead of acting as a hardware driver.
- [`src/robot_bringup`](src/robot_bringup/README.md): real/dummy hardware
  startup and whole-robot `/joint_states` aggregation for RViz. This package is
  intentionally a hardware/visualization bringup layer; teleoperation devices
  and algorithms are launched separately.

## Build

Do not build ROS packages from a conda environment. Use the system ROS Python
environment.

For bash:

```bash
conda deactivate 2>/dev/null || true
cd /home/ccs/ros2/teleop_ws
source /opt/ros/humble/setup.bash
colcon build --symlink-install
source install/setup.bash
```

For zsh:

```bash
conda deactivate 2>/dev/null || true
cd /home/ccs/ros2/teleop_ws
source /opt/ros/humble/setup.zsh
colcon build --symlink-install
source install/setup.zsh
```

For package-level changes, prefer a focused build first, for example:

```bash
colcon build --symlink-install --packages-select vive_openvr vive_marvin_teleop
```

## Teleoperation Python Environment

Some teleoperation algorithms need Python packages that are not provided by the
base ROS apt installation. Build the ROS workspace from the system ROS Python
environment, but run Python-heavy teleoperation nodes from the configured
runtime environment when needed.

The hand retargeting path currently uses a Miniconda runtime environment.
Install only Pinocchio from conda-forge first, then install the remaining Python
dependencies with pip. `wuji-retargeting` should be installed from the latest
official GitHub version. This workspace does not use the upstream Docker flow as
the primary setup path. See
[`wujihand_teleop`](src/teleop_algorithm/wujihand_teleop/README.md) for the
current environment commands.

## Wuji Hand Teleoperation

Use this flow to drive the Wuji Hand from Wuji Glove input. Run each block in a
separate sourced terminal.

### 1. Start Robot-Side Bringup

Dummy mode, for RViz-only testing without hand hardware:

```bash
cd /home/ccs/ros2/teleop_ws
source /opt/ros/humble/setup.bash
source install/setup.bash
ros2 launch robot_bringup bringup_dummy.launch.py
```

Real hand hardware:

```bash
cd /home/ccs/ros2/teleop_ws
source /opt/ros/humble/setup.bash
source install/setup.bash
ros2 launch robot_bringup bringup_real.launch.py
```

### 2. Verify and Start Wuji Glove Input

```bash
cd /home/ccs/ros2/teleop_ws
source /opt/ros/humble/setup.bash
source install/setup.bash

ros2 run wuji_glove wuji_glove_scan
ros2 run wuji_glove wuji_glove_verify --side both
ros2 launch wuji_glove wuji_glove.launch.py
```

Single-side glove startup:

```bash
ros2 launch wuji_glove wuji_glove.launch.py enable_left:=false
ros2 launch wuji_glove wuji_glove.launch.py enable_right:=false
```

### 3. Start Hand Retargeting

```bash
cd /home/ccs/ros2/teleop_ws
source /opt/ros/humble/setup.bash
source install/setup.bash

ros2 launch wujihand_teleop wujihand_retarget.launch.py
```

Single-side retargeting:

```bash
ros2 launch wujihand_teleop wujihand_retarget.launch.py enable_left:=false
ros2 launch wujihand_teleop wujihand_retarget.launch.py enable_right:=false
```

### 4. Check Hand Topics

```bash
ros2 topic hz /wuji_glove/right/keypoints
ros2 topic hz /hand_right/joint_states
ros2 topic hz /hand_right/joint_commands
ros2 topic echo /wujihand_teleop/right/diagnostics
```

For detailed glove setup and retargeting notes, see:

- [`wuji_glove`](src/teleop_device/wuji_glove/README.md)
- [`wujihand_teleop`](src/teleop_algorithm/wujihand_teleop/README.md)
- [`robot_bringup`](src/robot_bringup/README.md)

## Marvin Arm Teleoperation

Use this flow to drive the Marvin arms from Vive Tracker input. Run each block
in a separate sourced terminal.

### 1. Start Robot-Side Bringup

Dummy mode, recommended before real hardware:

```bash
cd /home/ccs/ros2/teleop_ws
source /opt/ros/humble/setup.bash
source install/setup.bash
ros2 launch robot_bringup bringup_dummy.launch.py
```

Real Marvin hardware, using the current preferred joint impedance driver mode
for live arm teleoperation:

```bash
cd /home/ccs/ros2/teleop_ws
source /opt/ros/humble/setup.bash
source install/setup.bash
ros2 launch robot_bringup bringup_real.launch.py \
  marvin_launch:=marvin_impedance.launch.py
```

### 2. Start SteamVR and Check Trackers

SteamVR must be running before OpenVR can provide tracker poses. If using
trackers without a headset, configure SteamVR null-HMD mode first:
[`steamvr_no_hmd_setup_zh.md`](src/teleop_device/vive_openvr/docs/steamvr_no_hmd_setup_zh.md).

Check devices:

```bash
cd /home/ccs/ros2/teleop_ws
source /opt/ros/humble/setup.bash
source install/setup.bash

ros2 run vive_openvr list_trackers --all
```

`connected=True` means SteamVR knows the device exists. It is usable only when
`valid=True` and `result=200 Running_OK`.

### 3. Start Vive Input

```bash
cd /home/ccs/ros2/teleop_ws
source /opt/ros/humble/setup.bash
source install/setup.bash

ros2 launch vive_openvr vive_openvr.launch.py rviz:=true
```

Check the expected pose and TF streams:

```bash
ros2 topic echo --once /vive/chest/pose
ros2 topic echo --once /vive/left_wrist/pose
ros2 topic echo --once /vive/right_wrist/pose
ros2 run tf2_ros tf2_echo left_chest tianji_left
ros2 run tf2_ros tf2_echo right_chest tianji_right
```

### 4. Start Arm Teleoperation

```bash
cd /home/ccs/ros2/teleop_ws
source /opt/ros/humble/setup.bash
source install/setup.bash

ros2 launch vive_marvin_teleop vive_marvin_teleop.launch.py
```

The arm teleop node starts disabled and publishes no commands until explicitly
enabled:

```bash
ros2 service call /vive_marvin_teleop/set_enabled std_srvs/srv/SetBool "{data: true}"
```

Stop command publication:

```bash
ros2 service call /vive_marvin_teleop/set_enabled std_srvs/srv/SetBool "{data: false}"
```

Check command output:

```bash
ros2 topic echo /marvin/right/joint_commands
ros2 topic hz /marvin/right/joint_commands
```

For detailed tracker setup, coordinate-frame notes, and IK behavior, see:

- [`vive_openvr`](src/teleop_device/vive_openvr/README.md)
- [`vive_marvin_teleop`](src/teleop_algorithm/vive_marvin_teleop/README.md)
- [`marvin_ros2`](src/marvin_ros2/README.md)
- [`robot_bringup`](src/robot_bringup/README.md)

## Full Teleoperation Flow

Use this flow when driving both the arms and hands together. Keep each block in
a separate sourced terminal.

### 1. Start Whole-Robot Bringup

Dummy mode:

```bash
cd /home/ccs/ros2/teleop_ws
source /opt/ros/humble/setup.bash
source install/setup.bash
ros2 launch robot_bringup bringup_dummy.launch.py
```

Real hardware:

```bash
cd /home/ccs/ros2/teleop_ws
source /opt/ros/humble/setup.bash
source install/setup.bash
ros2 launch robot_bringup bringup_real.launch.py \
  marvin_launch:=marvin_impedance.launch.py
```

### 2. Start Teleoperation Inputs

Terminal A, Wuji Glove input:

```bash
cd /home/ccs/ros2/teleop_ws
source /opt/ros/humble/setup.bash
source install/setup.bash

ros2 launch wuji_glove wuji_glove.launch.py
```

Terminal B, Vive Tracker input:

```bash
cd /home/ccs/ros2/teleop_ws
source /opt/ros/humble/setup.bash
source install/setup.bash

ros2 launch vive_openvr vive_openvr.launch.py rviz:=true
```

### 3. Start Teleoperation Algorithms

Terminal C, hand retargeting:

```bash
cd /home/ccs/ros2/teleop_ws
source /opt/ros/humble/setup.bash
source install/setup.bash

ros2 launch wujihand_teleop wujihand_retarget.launch.py
```

Terminal D, arm teleoperation:

```bash
cd /home/ccs/ros2/teleop_ws
source /opt/ros/humble/setup.bash
source install/setup.bash

ros2 launch vive_marvin_teleop vive_marvin_teleop.launch.py
```

Enable arm command output only after checking tracker TF and Marvin feedback:

```bash
ros2 service call /vive_marvin_teleop/set_enabled std_srvs/srv/SetBool "{data: true}"
```

### 4. Monitor Runtime Topics

```bash
ros2 topic hz /joint_states
ros2 topic hz /hand_right/joint_commands
ros2 topic hz /marvin/right/joint_commands
ros2 run tf2_ros tf2_echo right_chest tianji_right
```

Before stopping real Marvin hardware, disable arm teleoperation first:

```bash
ros2 service call /vive_marvin_teleop/set_enabled std_srvs/srv/SetBool "{data: false}"
```

## Important Notes

- Keep hardware bringup and teleoperation launch separate. `robot_bringup`
  starts real or dummy devices and visualization; teleoperation input and
  mapping packages are started explicitly.
- Drivers must not send default motion commands on startup. Teleoperation nodes
  should wait for real feedback and initialize from the current measured state.
- The global `/joint_states` topic is for whole-robot visualization and is owned
  by `joint_state_aggregator`. Device feedback stays on per-device topics such
  as `/marvin/right/joint_states` and `/hand_right/joint_states`.
- Marvin SDK access is exclusive. Do not run MarvinPlatform, SDK demos, SDK
  check nodes, or another Marvin driver while `marvin_driver_node` is connected.
- For real Marvin arm teleoperation, verify `/marvin/*/joint_states` before
  enabling `/vive_marvin_teleop/set_enabled`.
- Vive poses are in SteamVR standing tracking space, not robot `base_link`.
  Marvin arm teleoperation uses `right_chest -> tianji_right` and
  `left_chest -> tianji_left` as SDK IK target transforms.
- The Marvin IK target is the SDK TCP/flange frame, not the Wuji hand palm URDF
  link. Adjust tracker-to-TCP alignment in the static TF configuration instead
  of adding ad hoc rotations in the teleop loop.
- Wuji Studio and ROS glove nodes should not connect to the same glove at the
  same time. Close Wuji Studio before running ROS glove verification or input.
