# robot_bringup

`robot_bringup` 用于启动 Marvin 双臂和 Wuji 双手组合机器人的整机可视化。

该包提供 `scripts/joint_state_aggregator.py`，这是一个 Python ROS node，安装后可执行名为
`joint_state_aggregator`。它订阅各设备自己的关节状态话题，并发布一个全局 `/joint_states`
流给 `robot_state_publisher` 使用。

默认关节列表与 `robot_description/urdf/robot.xacro` 匹配：14 个 Marvin 机械臂关节加
40 个 Wuji 手部关节。`/joint_states` 只作为整机可视化状态流；硬件 driver 应继续发布各自
设备级的话题。

默认输入：

```text
/marvin/left/joint_states
/marvin/right/joint_states
/hand_left/joint_states
/hand_right/joint_states
```

如果某个输入话题不存在，对应关节会保持为零位。当该话题稍后出现时，匹配的关节名会覆盖默认零值。

运行可视化：

```bash
ros2 launch robot_bringup view_robot.launch.py
```

不打开 RViz：

```bash
ros2 launch robot_bringup view_robot.launch.py rviz:=false
```
