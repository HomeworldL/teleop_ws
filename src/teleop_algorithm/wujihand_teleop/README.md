# wujihand_teleop

`wujihand_teleop` only retargets Wuji Glove keypoints into Wuji Hand joint
commands. It does not connect to the gloves or to the hand hardware.

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

## Dependencies

Runtime requires:

- `wuji_retargeting`
- `pinocchio`
- `nlopt`

Glove connection is owned by the `wuji_glove` package. Hand hardware connection
is owned by `wujihand_driver` / `wujihand_bringup`.
