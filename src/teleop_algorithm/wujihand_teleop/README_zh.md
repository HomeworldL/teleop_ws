# wujihand_teleop

`wujihand_teleop` 只做 Wuji Glove 关键点到 Wuji Hand 关节命令的重定向。
它不连接手套，也不连接无极手本体。

## Python 环境

这个包依赖 Python IK/优化库。ROS 工作区构建仍然使用系统 ROS 环境；启动 retarget 节点时
使用独立 Miniconda 运行环境。

ROS 2 Humble + Ubuntu 22.04 当前建议：

```bash
conda create -n teleop python=3.10
conda activate teleop

# 先从 conda-forge 安装 Pinocchio。不要在这一步之前先装不匹配的 pip pinocchio/pin。
conda install -c conda-forge pinocchio

# 再用 pip 安装其他 Python 运行依赖。
python -m pip install numpy scipy pyyaml nlopt

# 从官方 GitHub 安装最新 wuji-retargeting。
python -m pip install git+https://github.com/wuji-technology/wuji-retargeting.git
```

检查运行环境：

```bash
python - <<'PY'
import pinocchio
import nlopt
import numpy
from wuji_retargeting import Retargeter
print("wujihand teleop Python environment OK")
PY
```

启动时在该环境里 source ROS 和当前工作区：

```bash
conda activate teleop
source /opt/ros/humble/setup.bash
source /home/ccs/ros2/teleop_ws/install/setup.bash
ros2 launch wujihand_teleop wujihand_retarget.launch.py
```

launch 文件会把当前 `CONDA_PREFIX` 的 site-packages 和 cmeel library path 加到 retarget
进程环境里。当前工作区采用 bare-metal ROS 加 conda 运行环境，不走上游 Docker 流程。

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

## 运行注意

- 这个包不会启动 `wuji_glove`、`wujihand_driver` 或 `robot_bringup`。输入设备和机器人侧
  driver 需要分开启动。
- 默认 `require_feedback:=true` 时，只有对应 `/hand_*/joint_states` 有新鲜反馈才会发布
  命令。dummy 测试时先启动 `robot_bringup bringup_dummy.launch.py`，让反馈门控能够打开。
- 如果 keypoints 超过 `input_timeout` 没有更新，命令输出会停止。这是预期行为，避免旧手势
  持续驱动灵巧手。
- 调 retarget 参数时可以使用 `dry_run:=true`。诊断仍会发布，但 `/hand_*/joint_commands`
  不会输出。
- 节点发布的是 retargeting URDF 和 hand driver 使用的 Wuji Hand 关节名。如果命令消息存在但
  手不动，先检查 driver 的 side namespace 是否是预期的 `/hand_left` 或 `/hand_right`。

## 依赖

运行时需要：

- `wuji_retargeting`
- `pinocchio`
- `nlopt`

手套连接由 `wuji_glove` 包负责，无极手硬件连接由 `wujihand_driver` /
`wujihand_bringup` 负责。
