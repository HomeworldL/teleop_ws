# wujihand_teleop

`wujihand_teleop` maps Wuji Glove keypoint topics to Wuji Hand joint commands.
The first version intentionally focuses on hand teleoperation only.

## Data Flow

```text
wuji_glove_node -> /wuji_glove/{left,right}/keypoints
  -> wujihand_controller -> wuji_retargeting
  -> /hand_left|right/joint_commands
```

Each glove and each hand controller runs in its own Python process. This keeps
the input device layer reusable for arm teleoperation, visualization, and
recording while preserving per-side retargeting isolation.

## Configure

Copy the hand config template and fill in Wuji Hand serial numbers:

```bash
cp src/teleop_algorithm/wujihand_teleop/config/wujihand_teleop.yaml.template \
  src/teleop_algorithm/wujihand_teleop/config/wujihand_teleop.yaml
```

Configure glove serials in:

```text
src/teleop_device/wuji_glove/config/wuji_glove.yaml
```

For day-to-day hardware testing, either build with `--symlink-install`, or pass
the source config paths explicitly when launching. Without that, an older
non-symlink install may still use the installed `.yaml.template` files.

Default hand namespaces are:

```text
/hand_left
/hand_right
```

## Launch

Build and source the workspace first:

```bash
colcon build --packages-select wuji_glove wujihand_teleop
source install/setup.zsh   # zsh
# source install/setup.bash  # bash
```

Dual hand:

```bash
ros2 launch wujihand_teleop wujihand_teleop.launch.py
```

This launch starts both Wuji Glove publisher nodes, both Wuji Hand driver nodes,
and both retarget controller nodes.

Dual hand with source-tree configs:

```bash
ros2 launch wujihand_teleop wujihand_teleop.launch.py \
  hand_config:=$PWD/src/teleop_algorithm/wujihand_teleop/config/wujihand_teleop.yaml \
  glove_config:=$PWD/src/teleop_device/wuji_glove/config/wuji_glove.yaml \
  retarget_config_dir:=$PWD/src/teleop_algorithm/wujihand_teleop/config
```

Single hand:

```bash
ros2 launch wujihand_teleop wujihand_teleop.launch.py enable_right:=false
ros2 launch wujihand_teleop wujihand_teleop.launch.py enable_left:=false
```

Verify command rates:

```bash
ros2 topic hz /wuji_glove/left/keypoints
ros2 topic hz /wuji_glove/right/keypoints
ros2 topic hz /hand_left/joint_commands
ros2 topic hz /hand_right/joint_commands
```

## Dependencies

Runtime requires:

- `wuji_sdk`
- `wuji_retargeting`
- `pinocchio`
- `nlopt`
- `wujihand_driver`

The current workspace already contains `wujihand_driver`. The Python retargeting
dependencies are not vendored here yet; install or vendor them before hardware
bringup.
