# teleop_ws

这是 Marvin 双臂和 Wuji 灵巧手遥操作系统的 ROS 2 工作区。

仓库包含机器人侧 driver、遥操作输入设备、遥操作算法、整机可视化，以及不用真实硬件即可
验证算法链路的 dummy bringup。

## 功能包总览

### 机器人设备

- [`src/marvin_ros2`](src/marvin_ros2/README_zh.md)：Marvin 双臂 ROS 2 集成，
  包含底层 driver、launch、SDK vendor copy、控制模式配置和机械臂 bringup 说明。
- [`src/marvin_ros2/marvin_driver`](src/marvin_ros2/marvin_driver/README_zh.md)：
  旧版 Tianji Marvin 控制器 SDK 的 C++ ROS 2 封装。它持有控制器 TCP 连接，并暴露
  单臂反馈和命令话题。
- [`src/marvin_ros2/marvin_bringup`](src/marvin_ros2/marvin_bringup/README_zh.md)：
  Marvin 位置模式、关节阻抗、关节阻抗 PD 前馈、回零辅助节点和手动关节控制 UI 的
  launch/config 包。
- [`src/wujihandros2`](src/wujihandros2/README_zh.md)：集成到当前工作区的 Wuji Hand
  ROS 2 driver 包。
- `src/wujihandros2/wujihand_driver`：Wuji Hand 硬件 driver。
- `src/wujihandros2/wujihand_bringup`：Wuji Hand 单手和双手启动 launch。
- `src/wujihandros2/wujihand_msgs`：Wuji Hand 自定义消息和服务。

### 遥操作设备

- [`src/teleop_device/wuji_glove`](src/teleop_device/wuji_glove/README_zh.md)：
  通过 `wuji_sdk` 连接 Wuji Glove，并发布 21 个手部关键点。
- [`src/teleop_device/vive_openvr`](src/teleop_device/vive_openvr/README_zh.md)：
  通过 SteamVR/OpenVR 读取 HTC Vive Tracker，并发布 tracker TF 和 `PoseStamped`。

### 遥操作算法

- [`src/teleop_algorithm/wujihand_teleop`](src/teleop_algorithm/wujihand_teleop/README_zh.md)：
  把 Wuji Glove 关键点重定向为 Wuji Hand 关节命令。
- [`src/teleop_algorithm/vive_marvin_teleop`](src/teleop_algorithm/vive_marvin_teleop/README_zh.md)：
  把 Vive chest/wrist tracker TF 映射为 Marvin 机械臂 TCP 目标，使用 Marvin 运动学
  SDK 解 IK，并发布机械臂关节命令。

### 整机统合

- [`src/robot_description`](src/robot_description/README_zh.md)：整机 URDF/MJCF 模型，
  组合 Marvin 双臂、Wuji 双手、底座、转接件和 RViz 可视化 frame。它使用 Marvin 和
  Wuji 的描述资源包，但本身不是硬件 driver。
- [`src/robot_bringup`](src/robot_bringup/README_zh.md)：真实/dummy 硬件启动和整机
  `/joint_states` 聚合。这个包只负责硬件和可视化统合；遥操作输入和算法需要单独启动。

## 构建

不要在 conda 环境里编译 ROS 包。使用系统 ROS Python 环境。

bash：

```bash
conda deactivate 2>/dev/null || true
cd /home/ccs/ros2/teleop_ws
source /opt/ros/humble/setup.bash
colcon build --symlink-install
source install/setup.bash
```

zsh：

```bash
conda deactivate 2>/dev/null || true
cd /home/ccs/ros2/teleop_ws
source /opt/ros/humble/setup.zsh
colcon build --symlink-install
source install/setup.zsh
```

改动单个包时，优先做 focused build，例如：

```bash
colcon build --symlink-install --packages-select vive_openvr vive_marvin_teleop
```

## 遥操作 Python 环境

部分遥操作算法需要基础 ROS apt 环境之外的 Python 包。ROS 工作区构建仍使用系统 ROS
Python 环境；需要运行 Python 依赖较重的遥操作节点时，再使用配置好的运行环境。

手部 retarget 当前建议使用 Miniconda 运行环境。只有 Pinocchio 先从 conda-forge 安装，
其他 Python 依赖用 pip 安装；`wuji-retargeting` 使用官方 GitHub 最新版本。当前工作区
不把上游 Docker 流程作为主要安装路径。具体环境命令见
[`wujihand_teleop`](src/teleop_algorithm/wujihand_teleop/README_zh.md)。

## Wuji 灵巧手遥操作

下面流程用于用 Wuji Glove 驱动 Wuji Hand。每个代码块建议在单独且已 source 的终端中运行。

### 1. 启动机器人侧 bringup

dummy 模式，用于没有真实手硬件时在 RViz 里测试：

```bash
cd /home/ccs/ros2/teleop_ws
source /opt/ros/humble/setup.bash
source install/setup.bash
ros2 launch robot_bringup bringup_dummy.launch.py
```

真实手硬件：

```bash
cd /home/ccs/ros2/teleop_ws
source /opt/ros/humble/setup.bash
source install/setup.bash
ros2 launch robot_bringup bringup_real.launch.py
```

### 2. 检查并启动 Wuji Glove 输入

```bash
cd /home/ccs/ros2/teleop_ws
source /opt/ros/humble/setup.bash
source install/setup.bash

ros2 run wuji_glove wuji_glove_scan
ros2 run wuji_glove wuji_glove_verify --side both
ros2 launch wuji_glove wuji_glove.launch.py
```

单侧手套启动：

```bash
ros2 launch wuji_glove wuji_glove.launch.py enable_left:=false
ros2 launch wuji_glove wuji_glove.launch.py enable_right:=false
```

### 3. 启动手部重定向

```bash
cd /home/ccs/ros2/teleop_ws
source /opt/ros/humble/setup.bash
source install/setup.bash

ros2 launch wujihand_teleop wujihand_retarget.launch.py
```

单侧重定向：

```bash
ros2 launch wujihand_teleop wujihand_retarget.launch.py enable_left:=false
ros2 launch wujihand_teleop wujihand_retarget.launch.py enable_right:=false
```

### 4. 检查手部话题

```bash
ros2 topic hz /wuji_glove/right/keypoints
ros2 topic hz /hand_right/joint_states
ros2 topic hz /hand_right/joint_commands
ros2 topic echo /wujihand_teleop/right/diagnostics
```

详细手套配置和重定向说明见：

- [`wuji_glove`](src/teleop_device/wuji_glove/README_zh.md)
- [`wujihand_teleop`](src/teleop_algorithm/wujihand_teleop/README_zh.md)
- [`robot_bringup`](src/robot_bringup/README_zh.md)

## Marvin 机械臂遥操作

下面流程用于用 Vive Tracker 驱动 Marvin 机械臂。每个代码块建议在单独且已 source 的终端中运行。

### 1. 启动机器人侧 bringup

dummy 模式，建议先用它验证算法和 RViz：

```bash
cd /home/ccs/ros2/teleop_ws
source /opt/ros/humble/setup.bash
source install/setup.bash
ros2 launch robot_bringup bringup_dummy.launch.py
```

真实 Marvin 硬件，实时遥操作当前优先使用关节阻抗模式：

```bash
cd /home/ccs/ros2/teleop_ws
source /opt/ros/humble/setup.bash
source install/setup.bash
ros2 launch robot_bringup bringup_real.launch.py \
  marvin_launch:=marvin_impedance.launch.py
```

### 2. 启动 SteamVR 并检查 tracker

OpenVR 读取 tracker 前必须先启动 SteamVR。无头显使用 tracker 时，先配置 SteamVR null-HMD
模式：
[`steamvr_no_hmd_setup_zh.md`](src/teleop_device/vive_openvr/docs/steamvr_no_hmd_setup_zh.md)。

检查设备：

```bash
cd /home/ccs/ros2/teleop_ws
source /opt/ros/humble/setup.bash
source install/setup.bash

ros2 run vive_openvr list_trackers --all
```

`connected=True` 只表示 SteamVR 知道这个设备存在。只有 `valid=True` 且
`result=200 Running_OK` 时，tracker 位姿才可用于遥操作。

### 3. 启动 Vive 输入

```bash
cd /home/ccs/ros2/teleop_ws
source /opt/ros/humble/setup.bash
source install/setup.bash

ros2 launch vive_openvr vive_openvr.launch.py rviz:=true
```

检查期望的 pose 和 TF：

```bash
ros2 topic echo --once /vive/chest/pose
ros2 topic echo --once /vive/left_wrist/pose
ros2 topic echo --once /vive/right_wrist/pose
ros2 run tf2_ros tf2_echo left_chest tianji_left
ros2 run tf2_ros tf2_echo right_chest tianji_right
```

### 4. 启动机械臂遥操作

```bash
cd /home/ccs/ros2/teleop_ws
source /opt/ros/humble/setup.bash
source install/setup.bash

ros2 launch vive_marvin_teleop vive_marvin_teleop.launch.py
```

机械臂遥操作节点启动后默认禁用，不会发布命令。确认安全后手动 enable：

```bash
ros2 service call /vive_marvin_teleop/set_enabled std_srvs/srv/SetBool "{data: true}"
```

停止发布命令：

```bash
ros2 service call /vive_marvin_teleop/set_enabled std_srvs/srv/SetBool "{data: false}"
```

检查命令输出：

```bash
ros2 topic echo /marvin/right/joint_commands
ros2 topic hz /marvin/right/joint_commands
```

详细 tracker 配置、坐标系和 IK 行为见：

- [`vive_openvr`](src/teleop_device/vive_openvr/README_zh.md)
- [`vive_marvin_teleop`](src/teleop_algorithm/vive_marvin_teleop/README_zh.md)
- [`marvin_ros2`](src/marvin_ros2/README_zh.md)
- [`robot_bringup`](src/robot_bringup/README_zh.md)

## 完整遥操作流程

同时驱动机械臂和灵巧手时使用下面流程。每个代码块建议在单独且已 source 的终端中运行。

### 1. 启动整机 bringup

dummy 模式：

```bash
cd /home/ccs/ros2/teleop_ws
source /opt/ros/humble/setup.bash
source install/setup.bash
ros2 launch robot_bringup bringup_dummy.launch.py
```

真实硬件：

```bash
cd /home/ccs/ros2/teleop_ws
source /opt/ros/humble/setup.bash
source install/setup.bash
ros2 launch robot_bringup bringup_real.launch.py \
  marvin_launch:=marvin_impedance.launch.py
```

### 2. 启动遥操作输入

终端 A，Wuji Glove 输入：

```bash
cd /home/ccs/ros2/teleop_ws
source /opt/ros/humble/setup.bash
source install/setup.bash

ros2 launch wuji_glove wuji_glove.launch.py
```

终端 B，Vive Tracker 输入：

```bash
cd /home/ccs/ros2/teleop_ws
source /opt/ros/humble/setup.bash
source install/setup.bash

ros2 launch vive_openvr vive_openvr.launch.py rviz:=true
```

### 3. 启动遥操作算法

终端 C，手部重定向：

```bash
cd /home/ccs/ros2/teleop_ws
source /opt/ros/humble/setup.bash
source install/setup.bash

ros2 launch wujihand_teleop wujihand_retarget.launch.py
```

终端 D，机械臂遥操作：

```bash
cd /home/ccs/ros2/teleop_ws
source /opt/ros/humble/setup.bash
source install/setup.bash

ros2 launch vive_marvin_teleop vive_marvin_teleop.launch.py
```

确认 tracker TF 和 Marvin 反馈正常后，再打开机械臂命令输出：

```bash
ros2 service call /vive_marvin_teleop/set_enabled std_srvs/srv/SetBool "{data: true}"
```

### 4. 运行时监控

```bash
ros2 topic hz /joint_states
ros2 topic hz /hand_right/joint_commands
ros2 topic hz /marvin/right/joint_commands
ros2 run tf2_ros tf2_echo right_chest tianji_right
```

停止真实 Marvin 硬件前，先关闭机械臂遥操作：

```bash
ros2 service call /vive_marvin_teleop/set_enabled std_srvs/srv/SetBool "{data: false}"
```

## 重要注意事项

- 硬件 bringup 和遥操作 launch 分开启动。`robot_bringup` 只启动真实或 dummy 设备以及
  可视化；遥操作输入和映射节点需要显式启动。
- driver 启动时不得发送默认运动命令。遥操作节点应先等待真实反馈，并从当前测量状态初始化。
- 全局 `/joint_states` 只用于整机可视化，由 `joint_state_aggregator` 发布。设备反馈保持在
  `/marvin/right/joint_states`、`/hand_right/joint_states` 这类设备级话题下。
- Marvin SDK 连接是独占的。`marvin_driver_node` 已连接时，不要同时运行 MarvinPlatform、
  SDK demo、SDK check node 或第二个 Marvin driver。
- 真实 Marvin 机械臂遥操作前，先确认 `/marvin/*/joint_states` 存在，再调用
  `/vive_marvin_teleop/set_enabled`。
- Vive pose 位于 SteamVR standing tracking space，不是机器人 `base_link`。Marvin 机械臂
  遥操作使用 `right_chest -> tianji_right` 和 `left_chest -> tianji_left` 作为 SDK IK
  目标变换。
- Marvin IK 目标是 SDK TCP/法兰坐标系，不是 Wuji 手掌 URDF link。tracker 到 TCP 的对齐
  应在静态 TF 配置中调整，不要在控制循环里临时手写旋转。
- Wuji Studio 和 ROS 手套节点不要同时连接同一只手套。运行 ROS 手套检查或输入节点前关闭
  Wuji Studio。
