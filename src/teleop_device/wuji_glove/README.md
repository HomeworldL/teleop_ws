# wuji_glove

`wuji_glove` connects Wuji Glove devices through `wuji_sdk` and publishes their
21 hand keypoints as ROS 2 `geometry_msgs/PoseArray` streams.

## Configure

Copy the template and fill in the real glove serial numbers:

```bash
cp src/teleop_device/wuji_glove/config/wuji_glove.yaml.template \
  src/teleop_device/wuji_glove/config/wuji_glove.yaml
```

Scan connected gloves:

```bash
source install/setup.zsh   # zsh
ros2 run wuji_glove wuji_glove_scan
```

The scanner filters non-UDP discoveries by default. Factory harnesses normally
use `192.168.1.100` for the left glove and `192.168.1.101` for the right glove,
so the scan output includes a best-effort side suggestion.

Run the read-only glove check before teleoperation:

```bash
ros2 run wuji_glove wuji_glove_verify --side both
```

This check connects to the glove with `ConnectOptions(enable_bridge=False)`,
reads one 21-joint skeleton frame, and verifies that the SDK log reports loading
the user hand model. It does not start the Wuji Hand driver and does not publish
hand commands.

Single-side checks:

```bash
ros2 run wuji_glove wuji_glove_verify --side left
ros2 run wuji_glove wuji_glove_verify --side right
```

## Launch

Build and source the workspace first:

```bash
colcon build --packages-select wuji_glove
source install/setup.zsh   # zsh
# source install/setup.bash  # bash
```

Start both gloves:

```bash
ros2 launch wuji_glove wuji_glove.launch.py
```

Start only one glove:

```bash
ros2 launch wuji_glove wuji_glove.launch.py enable_right:=false
ros2 launch wuji_glove wuji_glove.launch.py enable_left:=false
```

Use source-tree config explicitly:

```bash
ros2 launch wuji_glove wuji_glove.launch.py \
  config:=$PWD/src/teleop_device/wuji_glove/config/wuji_glove.yaml
```

Published topics:

```text
/wuji_glove/left/keypoints   geometry_msgs/PoseArray, 21 poses
/wuji_glove/right/keypoints  geometry_msgs/PoseArray, 21 poses
```

The 21 poses are in the Wuji SDK MediaPipe hand-keypoint order. Position is
filled; orientation is identity.

## Runtime Notes

- Calibrate with Wuji Studio first, then close Wuji Studio before launching ROS.
- Close Wuji Studio and stop glove/hand/teleop nodes before running
  `wuji_glove_verify`, because the check needs exclusive access to the glove.
- `ping 192.168.1.100` or `ping 192.168.1.101` only proves IP reachability. The
  SDK still connects by device identity, so `left_serial` and `right_serial` in
  `config/wuji_glove.yaml` must match the real glove serial numbers reported by
  `wuji_glove_scan`.
- If the launch log shows the correct glove IP and serial but reports
  `Device not found`, first check the configured serial, then close other Wuji
  SDK clients and rerun `wuji_glove_verify`.
- If scanning works but connection times out on a multi-NIC host, add per-glove
  `/32` routes to the NIC that can ping the glove IP.
- The Python package `wuji_sdk` must be installed in the active environment.
- `config/wuji_glove.yaml` is the local runtime file created from the template.
  Keep per-machine glove serials and network settings out of shared source
  changes unless the whole team agrees to standardize them.
- This package publishes keypoints only. It never publishes
  `/hand_*/joint_commands`; hand motion commands are produced by
  `wujihand_teleop`.
