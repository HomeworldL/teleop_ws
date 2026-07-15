# marvin_ros2

这个目录包含当前工作区中 Tianji Marvin 双臂控制器的第一版 ROS 2 driver 集成。

## 范围

当前实现针对旧版控制器 SDK：

```bash
/home/ccs/ros2/TJ_FX_ROBOT_CONTRL_SDK/contrlSDK
```

该包使用重新编译后的旧版 `libMarvinSDK.so` 导出的简明 C++ SDK API。共享库复制到
`marvin_driver/vendor/contrlSDK/lib`，所需头文件复制到
`marvin_driver/vendor/contrlSDK/include`，因此 ROS 包运行时不需要再通过
`LD_LIBRARY_PATH` 指回 SDK 源目录。

当前版本已实现：

- C++ `ament_cmake` driver 包：`marvin_driver`
- bringup/config 包：`marvin_bringup`
- 通过 `SetJointMode` 启动位置模式
- 通过 `SetImpJointMode` 启动关节阻抗模式
- 通过运行时 `JointPIDCtlType` 启动关节阻抗 PD 前馈模式
- 通过 `sensor_msgs/msg/JointState` 流式下发关节命令
- 按单臂发布状态话题，不发布全局 `/joint_states`
- connect、release、estop、单臂 disable 基础服务
- 等待反馈后再发命令的回零辅助节点
- 通过独立 `robot_bringup` 聚合包做整机可视化

暂未实现：

- 笛卡尔阻抗
- PVT/file 轨迹执行
- 拖动示教
- 工具和力控配置

## 话题布局

launch 文件默认把节点放在 `marvin` namespace 下。

反馈话题：

```text
/marvin/left/joint_states
/marvin/right/joint_states
```

命令话题：

```text
/marvin/left/joint_commands
/marvin/right/joint_commands
```

命令和反馈都使用 `sensor_msgs/msg/JointState`。ROS 侧位置和速度单位是弧度/弧度每秒，
driver 内部会和 SDK 的角度制 API 互相转换。

driver 有意不发布全局 `/joint_states`。全局状态由后续聚合节点合并 Marvin 双臂状态和
Wuji 双手状态后发布。

## 关节名

默认关节名和现有 Marvin URDF 一致：

```text
Joint1_L ... Joint7_L
Joint1_R ... Joint7_R
```

如果命令消息的 `name` 字段为空，前 7 个 position 会按上述顺序解释。如果带有 name，
则必须包含该臂配置中的全部关节名。

## 构建

从工作区根目录运行：

```bash
colcon build --packages-select marvin_driver marvin_bringup robot_bringup robot_description
source install/setup.bash
```

## 启动指令

先确认控制柜和上位机网络可达，并且没有 MarvinPlatform 或其他 SDK 程序正在连接控制器。
默认控制器 IP 按当前配置写为 `192.168.1.190`，实际不一致时用 `robot_ip:=...` 覆盖。

位置模式：

```bash
ros2 launch marvin_bringup marvin_position.launch.py robot_ip:=192.168.1.190 arms:=both
```

关节阻抗模式：

```bash
ros2 launch marvin_bringup marvin_impedance.launch.py robot_ip:=192.168.1.190 arms:=both
```

关节阻抗 PD 前馈模式：

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

常用 launch 参数：

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

## 服务

默认 namespace 下：

```text
/marvin/connect
/marvin/release
/marvin/estop
/marvin/left/disable
/marvin/right/disable
```

所有服务当前都使用 `std_srvs/srv/Trigger`。

## 安全说明

SDK 模式切换 API 要求机械臂处于静止状态。如果机械臂正在运动，启动时模式配置可能失败，
driver 会拒绝该臂的命令。

命令看门狗会在 `command_timeout_sec` 后报告命令流超时。默认只报警。若希望超时时调用
`Disable`，可在 YAML 中设置 `disable_on_timeout: true`。

driver 本身启动时不会发送默认关节命令。回零辅助节点会先等待初始反馈，先命令当前反馈位置，
然后再插值移动到零位。
