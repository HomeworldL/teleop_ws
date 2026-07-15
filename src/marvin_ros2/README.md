# marvin_ros2

This directory contains the first ROS 2 driver integration for the Tianji Marvin dual-arm
controller used in this workspace.

## Scope

The implementation targets the old controller SDK in:

```bash
/home/ccs/ros2/TJ_FX_ROBOT_CONTRL_SDK/contrlSDK
```

The package uses the concise C++ SDK APIs exported by the rebuilt old `libMarvinSDK.so`.
The shared library is copied into `marvin_driver/vendor/contrlSDK/lib`, and the required
headers are copied into `marvin_driver/vendor/contrlSDK/include`, so the ROS package does
not need a runtime `LD_LIBRARY_PATH` pointing back to the SDK tree.

Implemented in this version:

- C++ `ament_cmake` driver package: `marvin_driver`
- Bringup/config package: `marvin_bringup`
- Position mode startup via `SetJointMode`
- Joint impedance startup via `SetImpJointMode`
- Joint impedance PD-feedforward startup via runtime `JointPIDCtlType`
- Joint command streaming via `sensor_msgs/msg/JointState`
- Per-arm state topics, not global `/joint_states`
- Basic services for connect, release, estop, and per-arm disable
- A zero-position helper node that waits for feedback before publishing commands
- Whole-robot visualization through the separate `robot_bringup` aggregator package

Not implemented yet:

- Cartesian impedance
- PVT/file trajectory execution
- Drag teaching
- Tool and force-control configuration

## Topic Layout

Launch files put the node in the `marvin` namespace by default.

Published feedback:

```text
/marvin/left/joint_states
/marvin/right/joint_states
```

Command topics:

```text
/marvin/left/joint_commands
/marvin/right/joint_commands
```

Both command and feedback messages use `sensor_msgs/msg/JointState`.
ROS-side positions and velocities are radians/radians per second. The driver converts
to and from the SDK's degree-based API internally.

The driver intentionally does not publish the global `/joint_states`. A later aggregator
node should merge Marvin arm states and Wuji hand states into one global stream.

## Joint Names

The default joint names match the existing Marvin URDF files:

```text
Joint1_L ... Joint7_L
Joint1_R ... Joint7_R
```

If a command message has an empty `name` field, the first seven positions are interpreted
in this order. If names are present, all configured joint names for that arm must be present.

## Build

From the workspace root:

```bash
colcon build --packages-select marvin_driver marvin_bringup robot_bringup robot_description
source install/setup.bash
```

## 启动指令

先确认控制柜和上位机网络可达，并且没有 MarvinPlatform 或其他 SDK 程序正在连接控制器。
默认控制器 IP 按当前配置写为 `192.168.1.190`，实际不一致时用 `robot_ip:=...`
覆盖。

Position mode:

```bash
ros2 launch marvin_bringup marvin_position.launch.py robot_ip:=192.168.1.190 arms:=both
```

Joint impedance mode:

```bash
ros2 launch marvin_bringup marvin_impedance.launch.py robot_ip:=192.168.1.190 arms:=both
```

Joint impedance PD-feedforward mode:

```bash
ros2 launch marvin_bringup marvin_impedance_pd.launch.py robot_ip:=192.168.1.190 arms:=both
```

整机 RViz 显示单独启动，负责合并 Marvin 双臂和 Wuji 双手的关节状态：

```bash
ros2 launch robot_bringup view_robot.launch.py
```

只启动 `robot_state_publisher` 和 `/joint_states` 聚合，不打开 RViz：

```bash
ros2 launch robot_bringup view_robot.launch.py rviz:=false
```

确认 driver 已经启动、`/marvin/*/joint_states` 已经稳定发布后，才可以手动运行回零节点：

```bash
ros2 launch marvin_bringup marvin_zero.launch.py arms:=both
```

`marvin_zero_position_node` 会先等待反馈，用当前反馈位置初始化命令，然后再插值到零位；
它不会在 driver 启动时自动运行。

## 分步启动和回零

推荐第一次实机测试先单臂、慢速回零。

终端 1：先只启动 Marvin driver，进入位置模式，不启动回零节点。

```bash
cd /home/ccs/ros2/teleop_ws
source install/setup.bash
ros2 launch marvin_bringup marvin_position.launch.py \
  robot_ip:=192.168.1.190 \
  arms:=left \
  auto_connect:=true
```

终端 2：确认左臂反馈已经发布。

```bash
cd /home/ccs/ros2/teleop_ws
source install/setup.bash
ros2 topic echo --once /marvin/left/joint_states
ros2 topic hz /marvin/left/joint_states
```

终端 2：确认反馈正常后，再单独运行回零节点。下面命令会从当前反馈位置开始，
用 15 秒插值到左臂 7 个关节的 `0.0 rad`。

```bash
ros2 launch marvin_bringup marvin_zero.launch.py \
  arms:=left \
  move_duration_sec:=15.0
```

右臂单独测试：

```bash
ros2 launch marvin_bringup marvin_position.launch.py \
  robot_ip:=192.168.1.190 \
  arms:=right \
  auto_connect:=true

ros2 topic echo --once /marvin/right/joint_states

ros2 launch marvin_bringup marvin_zero.launch.py \
  arms:=right \
  move_duration_sec:=15.0
```

双臂确认安全后再使用：

```bash
ros2 launch marvin_bringup marvin_position.launch.py \
  robot_ip:=192.168.1.190 \
  arms:=both \
  auto_connect:=true

ros2 launch marvin_bringup marvin_zero.launch.py \
  arms:=both \
  move_duration_sec:=15.0
```

Useful launch arguments:

```text
namespace:=marvin
robot_ip:=192.168.1.190
arms:=both | left | right
auto_connect:=true | false
velocity_ratio:=10
acceleration_ratio:=10
```

## 硬件启动前注意事项

- 确认急停、使能、电源、气路或外设处于预期状态，机械臂运动范围内无人和障碍物。
- 确认控制器 IP 可达，例如 `ping 192.168.1.190`。
- 确认 MarvinPlatform_EN、SDK demo、check node 等直接连接 SDK 的程序都已退出；同一时间只让一个主控进程连接控制器。
- 切换位置模式、关节阻抗模式或 PD 前馈模式前，机械臂应处于静止状态。SDK 在机械臂运动时可能拒绝模式切换。
- 第一次带硬件启动建议用 `arms:=left` 或 `arms:=right` 单臂确认，再切到 `arms:=both`。

## 启动硬件后的注意事项

- 先观察 driver 日志，确认连接成功、所选控制模式配置成功，再发布任何命令。
- 用下面命令确认反馈存在：

```bash
ros2 topic hz /marvin/left/joint_states
ros2 topic hz /marvin/right/joint_states
```

- 不要在没有反馈的情况下向 `/marvin/*/joint_commands` 发布目标位姿；遥操作节点应先读取当前反馈作为初始命令。
- 如果模式配置失败，先确认机械臂静止，再调用 `/marvin/release` 后重新 `/marvin/connect`，或重启对应 launch。
- 紧急停止使用 `/marvin/estop`。单臂软件禁用可用 `/marvin/left/disable` 或 `/marvin/right/disable`。
- `robot_bringup` 发布的 `/joint_states` 只用于整机显示，不应作为底层 driver 的控制输入。

## 软件参数注意事项

- `namespace` 默认是 `marvin`，因此话题和服务默认都在 `/marvin/...` 下。
- `arms` 可选 `left`、`right`、`both`；单臂调试时优先使用单臂。
- `auto_connect:=true` 会在节点启动时连接控制器并配置模式；设为 `false` 时需要手动调用 `/marvin/connect`。
- `control_mode` 由三个 launch 文件固定设置，通常不要在命令行混用覆盖。
- `velocity_ratio` 和 `acceleration_ratio` 会传给 SDK 模式设置接口，初次实机建议保持较低值。
- `feedback_rate_hz` 控制反馈发布频率，默认 `50.0`。
- `command_timeout_sec` 默认 `0.5`，用于检测命令流超时。
- `disable_on_timeout` 默认 `false`，只报警不禁用；设为 `true` 后命令超时会调用 SDK `Disable`。
- `joint_impedance_k` 和 `joint_impedance_d` 只用于关节阻抗/PD 前馈模式，先在 YAML 中调整并记录，不要持久化写入控制器。
- `left_joint_names`、`right_joint_names` 必须和 URDF 及命令消息一致，默认是 `Joint1_L ... Joint7_L` 和 `Joint1_R ... Joint7_R`。

## Services

With the default namespace:

```text
/marvin/connect
/marvin/release
/marvin/estop
/marvin/left/disable
/marvin/right/disable
```

All services currently use `std_srvs/srv/Trigger`.

## Safety Notes

The SDK mode-switch APIs require the arm to be stationary. If the arm is moving, startup
mode setup may fail and the driver will reject commands for that arm.

The command watchdog reports stale command streams after `command_timeout_sec`. By default
it only warns. Set `disable_on_timeout: true` in YAML if the driver should call `Disable`
when command input times out.

The driver itself does not send a default joint command during startup. The zero-position
helper waits for initial feedback, commands the current feedback position first, and only
then interpolates toward zero.
