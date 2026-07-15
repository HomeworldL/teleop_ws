# marvin_driver

`marvin_driver` 是旧版 Tianji Marvin 控制器 SDK 的 ROS 2 C++ 封装。
它把重新编译后的旧版 SDK 共享库和头文件放在 `vendor/contrlSDK` 下。

## SDK 迁移说明

原始 SDK demo 都是直接连接控制器的独立进程。ROS driver 把这个直接 SDK 连接所有权集中在
一个节点内部，并通过 ROS 话题和服务暴露常规操作接口。

当前包中已映射：

- `showcase_new_control_sdk_usage.cpp`
  - `Connect` -> driver 启动或 `/marvin/connect`
  - `SetJointMode` -> `control_mode:=position`
  - `SetImpJointMode` -> `control_mode:=joint_impedance`
  - `SetJointPostionCmd` -> `/marvin/left/joint_commands` 和 `/marvin/right/joint_commands`
- `showcase_link_check.cpp`
  - `marvin_link_check_node`
- `showcase_cmd_delay.cpp`
  - `marvin_cmd_delay_check_node`

暂未迁移：

- PVT 和 PLN 轨迹 demo
- 拖动示教 demo
- 笛卡尔阻抗和力控 demo
- 末端 CAN/485 demo

第一版 driver 的目标是遥操作和基础设备检查，因此暂时没有加入这些功能。

## 控制模式

driver 支持三种 launch-time 模式：

```text
position
joint_impedance
joint_impedance_pd
```

位置模式调用：

```cpp
SetJointMode(arm, velocity_ratio, acceleration_ratio)
```

关节阻抗模式调用：

```cpp
OnSetIntPara("R.A0.BASIC.JointPIDCtlType", 0)  // 左臂
OnSetIntPara("R.A1.BASIC.JointPIDCtlType", 0)  // 右臂
SetImpJointMode(arm, velocity_ratio, acceleration_ratio, K, D)
```

关节阻抗 PD 前馈模式使用相同的阻抗设置，但在进入关节阻抗模式前，把所选臂的
`JointPIDCtlType` 设置为 `1`。

driver 不调用 `OnSavePara()`。`JointPIDCtlType` 只在运行时设置，不持久化。

三种模式启动后使用同一个关节命令 API：

```cpp
SetJointPostionCmd(arm, joint_degrees)
```

ROS 命令保持弧度制，并在 driver 内部转换。

## 启动错误处理

driver 使用 SDK 的简明 `Connect` 函数。旧 SDK 中，`Connect` 内部会调用
`CheckArmError()` 和 `CheckServoError()`。`SetJointMode` 和 `SetImpJointMode`
在模式切换前也会重复这些检查。

这意味着启动时 driver 会通过 SDK 尝试清除 arm 和 servo 错误，然后才开始接受关节命令。
如果错误清除后仍然存在，模式配置会失败，该臂会拒绝命令。

## 命令行为

driver 启动时不会发送任何默认关节命令。它只会：

- 连接控制器
- 配置请求的控制模式
- 发布反馈
- 等待 `/marvin/*/joint_commands`

需要下发运动的节点应先等待 `/marvin/*/joint_states`，并用第一帧反馈位置作为初始命令。
`marvin_zero_position_node` 遵守这个规则。

## 检查节点

这些节点会直接连接 SDK，因此只能在 `marvin_driver_node` 没有运行时使用：

```bash
ros2 run marvin_driver marvin_link_check_node --ros-args -p robot_ip:=192.168.1.190
ros2 run marvin_driver marvin_cmd_delay_check_node --ros-args -p robot_ip:=192.168.1.190 -p arm:=A
```
