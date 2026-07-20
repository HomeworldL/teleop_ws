# wuji_glove

`wuji_glove` 通过 `wuji_sdk` 连接 Wuji Glove，并把手套的 21 个手部关键点发布为
ROS 2 `geometry_msgs/PoseArray`。

## 配置

复制模板并填写真实手套序列号：

```bash
cp src/teleop_device/wuji_glove/config/wuji_glove.yaml.template \
  src/teleop_device/wuji_glove/config/wuji_glove.yaml
```

扫描已连接手套：

```bash
source install/setup.zsh   # zsh
ros2 run wuji_glove wuji_glove_scan
```

扫描默认只保留 UDP 发现结果。出厂线束通常用 `192.168.1.100` 表示左手套，
`192.168.1.101` 表示右手套，因此输出里会给出左右手建议。

遥操作前先运行只读检查：

```bash
ros2 run wuji_glove wuji_glove_verify --side both
```

这个检查会用 `ConnectOptions(enable_bridge=False)` 连接手套，只读取一帧
21 关节骨架，并检查 SDK 日志是否加载了用户手模型。它不会启动 Wuji Hand
driver，也不会发布手部控制命令。

单侧检查：

```bash
ros2 run wuji_glove wuji_glove_verify --side left
ros2 run wuji_glove wuji_glove_verify --side right
```

## 启动

先编译并 source 工作区：

```bash
colcon build --packages-select wuji_glove
source install/setup.zsh   # zsh
# source install/setup.bash  # bash
```

启动双手套：

```bash
ros2 launch wuji_glove wuji_glove.launch.py
```

只启动一只手套：

```bash
ros2 launch wuji_glove wuji_glove.launch.py enable_right:=false
ros2 launch wuji_glove wuji_glove.launch.py enable_left:=false
```

显式使用 source 目录配置：

```bash
ros2 launch wuji_glove wuji_glove.launch.py \
  config:=$PWD/src/teleop_device/wuji_glove/config/wuji_glove.yaml
```

发布话题：

```text
/wuji_glove/left/keypoints   geometry_msgs/PoseArray，21 个 pose
/wuji_glove/right/keypoints  geometry_msgs/PoseArray，21 个 pose
```

这 21 个 pose 使用 Wuji SDK 的 MediaPipe 手部关键点顺序。position 有效，
orientation 固定为单位四元数。

## 运行注意

- 先用 Wuji Studio 完成校准，启动 ROS 前关闭 Wuji Studio。
- 运行 `wuji_glove_verify` 前关闭 Wuji Studio，并停止 glove/hand/teleop 节点，
  因为这个检查需要独占连接手套。
- 如果能 scan 但 connect timeout，多半是多网卡同网段路由问题，需要给手套 IP
  添加指向正确网卡的 `/32` 路由。
- 当前 Python 环境需要安装 `wuji_sdk`。
