# vive_marvin_teleop

`vive_marvin_teleop` 使用 3 个 Vive Tracker 做 Marvin 双臂胸腔坐标系遥操作：

```yaml
left_wrist:  "LHR-E651F39A"
right_wrist: "LHR-F757F16E"
chest:       "LHR-F854821A"
```

数据流：

```text
vive_openvr TF
  -> left_chest/right_chest 坐标对齐
  -> tianji_left/tianji_right 末端目标
  -> Marvin IK
  -> /marvin/left/joint_commands
  -> /marvin/right/joint_commands
```

节点默认不发命令。启动后调用：

```bash
ros2 service call /vive_marvin_teleop/set_enabled std_srvs/srv/SetBool "{data: true}"
```

停止：

```bash
ros2 service call /vive_marvin_teleop/set_enabled std_srvs/srv/SetBool "{data: false}"
```

单独启动：

```bash
ros2 launch vive_marvin_teleop vive_marvin_teleop.launch.py
```

推荐启动顺序是硬件/dummy bringup 和 teleop 分开启动。先启动机械臂侧：

```bash
ros2 launch robot_bringup bringup_dummy.launch.py
```

或实机侧：

```bash
ros2 launch robot_bringup bringup_real.launch.py \
  marvin_launch:=marvin_impedance_pd.launch.py
```

然后分别启动 Vive Tracker 输入和 arm teleop：

```bash
ros2 launch vive_openvr vive_openvr.launch.py rviz:=true
ros2 launch vive_marvin_teleop vive_marvin_teleop.launch.py
```

当前节点按双臂配置初始化，但不会因为缺少左手腕 Tracker 退出。如果只连接
`chest` 和 `right_wrist`，并且左右 Marvin feedback 都在线，enable 后左臂会因为
找不到 `left_chest -> tianji_left` TF 而跳过命令，右臂会继续按
`right_chest -> tianji_right` 解 IK 并发布 `/marvin/right/joint_commands`。如果左臂
feedback 本身也没有启动，当前 enable 服务会拒绝使能。
