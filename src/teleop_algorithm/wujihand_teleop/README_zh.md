# wujihand_teleop

`wujihand_teleop` 只做 Wuji Glove 关键点到 Wuji Hand 关节命令的重定向。
它不连接手套，也不连接无极手本体。

## 数据流

```text
/wuji_glove/left/keypoints
  -> wujihand_retarget --side left
  -> /hand_left/joint_commands

/wuji_glove/right/keypoints
  -> wujihand_retarget --side right
  -> /hand_right/joint_commands
```

左右手各运行一个 `wujihand_retarget` 进程。每个进程只加载一侧 retargeter，
避免双手 IK/优化共享同一个 Python GIL。

## 启动顺序

先启动手套输入：

```bash
ros2 launch wuji_glove wuji_glove.launch.py
```

再启动无极手硬件 driver。推荐使用 driver 自带的双手自动发现 launch：

```bash
ros2 launch wujihand_bringup wujihand_dual.launch.py
```

最后启动重定向：

```bash
ros2 launch wujihand_teleop wujihand_retarget.launch.py
```

只启动左手：

```bash
ros2 launch wujihand_teleop wujihand_retarget.launch.py enable_right:=false
```

只启动右手：

```bash
ros2 launch wujihand_teleop wujihand_retarget.launch.py enable_left:=false
```

如果要直接使用 source 目录里的 retarget 配置：

```bash
ros2 launch wujihand_teleop wujihand_retarget.launch.py \
  retarget_config_dir:=$PWD/src/teleop_algorithm/wujihand_teleop/config
```

## 话题

默认输入：

```text
/wuji_glove/left/keypoints
/wuji_glove/right/keypoints
```

默认输出：

```text
/hand_left/joint_commands
/hand_right/joint_commands
```

默认反馈门控：

```text
/hand_left/joint_states
/hand_right/joint_states
```

节点默认等对应 `/hand_*/joint_states` 收到新鲜反馈后才发布命令。这样 hand
driver 没启动或反馈断流时，retarget 不会持续盲发命令。可以通过
`require_feedback:=false` 关闭这个门控。

## 检查

```bash
ros2 topic hz /wuji_glove/left/keypoints
ros2 topic hz /hand_left/joint_states
ros2 topic hz /hand_left/joint_commands
```

## 依赖

运行时需要：

- `wuji_retargeting`
- `pinocchio`
- `nlopt`

手套连接由 `wuji_glove` 包负责，无极手硬件连接由 `wujihand_driver` /
`wujihand_bringup` 负责。
