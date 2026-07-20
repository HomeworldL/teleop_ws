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

先检查手套。这个步骤只读，不会启动手部控制：

```bash
ros2 run wuji_glove wuji_glove_verify --side both
```

再启动手套输入：

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

retarget 节点还会在手套关键点超时后停止输出，启动时从当前手反馈渐入到
retarget 结果，并限制每个关节的命令速度。算法路径以 Wuji `v2026.05.26`
为基线，同时暴露官方 teleop 实际使用的优化器调参入口。常用 launch 参数：

```text
input_timeout:=0.3          关键点超过这个时间未更新就停止发布。
startup_ramp_sec:=0.5       从实测手状态渐入到 retarget 输出。
max_joint_velocity:=3.14    每个关节命令速度上限，单位 rad/s；0 表示关闭。
nlopt_max_eval:=25          NLOPT 迭代上限；0 表示使用 retargeting 库默认值。
min_keypoint_spread:=0.01   IK 前丢弃塌缩的 21 点骨架。
clip_to_joint_limits:=true  将最终命令夹紧到 retargeter URDF 的关节范围。
retarget_verbose:=false     发布 IK cost 和 pinch alpha 诊断；会增加 CPU 开销。
dry_run:=false              true 时只计算和发诊断，不发布控制命令。
publish_diagnostics:=true   发布 /wujihand_teleop/{left,right}/diagnostics。
```

如果捏合或极限姿态精度不够，可以把 `nlopt_max_eval` 提高到 50；正常实时遥操作
建议保持默认 25，延迟更低。

## 检查

```bash
ros2 topic hz /wuji_glove/left/keypoints
ros2 topic hz /hand_left/joint_states
ros2 topic hz /hand_left/joint_commands
ros2 topic echo /wujihand_teleop/left/diagnostics
```

## 依赖

运行时需要：

- `wuji_retargeting`
- `pinocchio`
- `nlopt`

手套连接由 `wuji_glove` 包负责，无极手硬件连接由 `wujihand_driver` /
`wujihand_bringup` 负责。
