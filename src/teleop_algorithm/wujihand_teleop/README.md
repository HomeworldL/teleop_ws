# wujihand_teleop

`wujihand_teleop` only retargets Wuji Glove keypoints into Wuji Hand joint
commands. It does not connect to the gloves or to the hand hardware.

## Python Environment

This package depends on Python IK/optimization libraries. Keep the ROS workspace
build in the system ROS environment; use a dedicated Miniconda runtime
environment when launching the retargeting node.

Recommended setup for ROS 2 Humble on Ubuntu 22.04:

```bash
conda create -n teleop python=3.10
conda activate teleop

# Install Pinocchio first from conda-forge. Avoid installing a mismatched pip
# pinocchio/pin package before this step.
conda install -c conda-forge pinocchio

# Then install the remaining Python runtime dependencies with pip.
python -m pip install numpy scipy pyyaml nlopt

# Install the latest official wuji-retargeting from GitHub.
python -m pip install git+https://github.com/wuji-technology/wuji-retargeting.git
```

Check the runtime environment:

```bash
python - <<'PY'
import pinocchio
import nlopt
import numpy
from wuji_retargeting import Retargeter
print("wujihand teleop Python environment OK")
PY
```

Launch from that environment after sourcing ROS and this workspace:

```bash
conda activate teleop
source /opt/ros/humble/setup.bash
source /home/ccs/ros2/teleop_ws/install/setup.bash
ros2 launch wujihand_teleop wujihand_retarget.launch.py
```

The launch file prepends the active `CONDA_PREFIX` site-packages and cmeel
library paths for the retargeting process. The current workspace setup is
bare-metal ROS plus this conda runtime, not the upstream Docker workflow.

## Data Flow

```text
/wuji_glove/left/keypoints
  -> wujihand_retarget --side left
  -> /hand_left/joint_commands

/wuji_glove/right/keypoints
  -> wujihand_retarget --side right
  -> /hand_right/joint_commands
```

Left and right hands run as separate `wujihand_retarget` processes. Each process
owns one retargeter, preserving per-side parallelism and avoiding one shared
Python GIL for both hands.

## Launch Order

Verify the gloves first. This is read-only and does not start hand control:

```bash
ros2 run wuji_glove wuji_glove_verify --side both
```

Start glove input:

```bash
ros2 launch wuji_glove wuji_glove.launch.py
```

Then start the Wuji Hand hardware driver. The driver package's dual-hand
auto-discovery launch is recommended:

```bash
ros2 launch wujihand_bringup wujihand_dual.launch.py
```

Finally start retargeting:

```bash
ros2 launch wujihand_teleop wujihand_retarget.launch.py
```

Left hand only:

```bash
ros2 launch wujihand_teleop wujihand_retarget.launch.py enable_right:=false
```

Right hand only:

```bash
ros2 launch wujihand_teleop wujihand_retarget.launch.py enable_left:=false
```

Use source-tree retarget configs explicitly:

```bash
ros2 launch wujihand_teleop wujihand_retarget.launch.py \
  retarget_config_dir:=$PWD/src/teleop_algorithm/wujihand_teleop/config
```

## Topics

Default inputs:

```text
/wuji_glove/left/keypoints
/wuji_glove/right/keypoints
```

Default outputs:

```text
/hand_left/joint_commands
/hand_right/joint_commands
```

Default feedback gates:

```text
/hand_left/joint_states
/hand_right/joint_states
```

By default, each retarget node waits for fresh feedback on the matching
`/hand_*/joint_states` topic before publishing commands. This prevents blind
command publication while the hand driver is not running or feedback is stale.
Pass `require_feedback:=false` to disable the gate.

The retarget node also stops output when glove keypoints become stale, ramps in
from the current hand feedback at startup, and limits per-joint command velocity.
It follows the Wuji `v2026.05.26` retarget path and exposes the same practical
optimizer knob used by the official teleop package. Useful launch parameters:

```text
input_timeout:=0.3          Stop publishing when keypoints are older than this.
startup_ramp_sec:=0.5       Blend from measured hand state into retarget output.
max_joint_velocity:=3.14    Per-joint command velocity limit in rad/s; 0 disables.
nlopt_max_eval:=25          NLOPT iteration cap; 0 keeps the retargeting library default.
min_keypoint_spread:=0.01   Drop collapsed 21-point skeletons before IK.
clip_to_joint_limits:=true  Clip final commands to retargeter URDF joint limits.
retarget_verbose:=false     Include IK cost and pinch alpha diagnostics; higher CPU cost.
dry_run:=false              Compute diagnostics without publishing commands when true.
publish_diagnostics:=true   Publish /wujihand_teleop/{left,right}/diagnostics.
```

Set `nlopt_max_eval` higher, up to the library default of 50, if pinch or
extreme-pose accuracy is more important than latency. Keep the default 25 for
normal live teleoperation.

## Checks

```bash
ros2 topic hz /wuji_glove/left/keypoints
ros2 topic hz /hand_left/joint_states
ros2 topic hz /hand_left/joint_commands
ros2 topic echo /wujihand_teleop/left/diagnostics
```

## Runtime Notes

- This package does not launch `wuji_glove`, `wujihand_driver`, or
  `robot_bringup`. Start input devices and robot-side drivers separately.
- With the default `require_feedback:=true`, no command is published until the
  matching `/hand_*/joint_states` topic is fresh. In dummy tests, start
  `robot_bringup bringup_dummy.launch.py` so the feedback gate can open.
- If keypoints stop updating for longer than `input_timeout`, command output
  stops. This is expected and prevents stale glove poses from continuing to
  drive the hand.
- Use `dry_run:=true` when tuning retargeting parameters. Diagnostics continue
  to publish, but `/hand_*/joint_commands` remains silent.
- The node commands the Wuji Hand joint names used by the retargeting URDF and
  the hand driver. If command messages appear but the hand does not move, check
  that the driver side namespace is `/hand_left` or `/hand_right` as expected.

## Dependencies

Runtime requires:

- `wuji_retargeting`
- `pinocchio`
- `nlopt`

Glove connection is owned by the `wuji_glove` package. Hand hardware connection
is owned by `wujihand_driver` / `wujihand_bringup`.
