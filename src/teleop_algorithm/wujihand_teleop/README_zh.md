# wujihand_teleop

`wujihand_teleop` 把 Wuji Glove 关键点话题映射为 Wuji Hand 关节命令。
第一版只做手部遥操作。

## 数据流

```text
wuji_glove_node -> /wuji_glove/{left,right}/keypoints
  -> wujihand_controller -> wuji_retargeting
  -> /hand_left|right/joint_commands
```

左右手套、左右手 retarget controller 都分别运行一个 Python 进程。这样手套输入层
可以被机械臂遥操作、可视化和 rosbag 复用，同时保留每侧 retarget 的进程隔离。

## 配置

复制手部配置模板并填写 Wuji Hand 序列号：

```bash
cp src/teleop_algorithm/wujihand_teleop/config/wujihand_teleop.yaml.template \
  src/teleop_algorithm/wujihand_teleop/config/wujihand_teleop.yaml
```

手套序列号配置在：

```text
src/teleop_device/wuji_glove/config/wuji_glove.yaml
```

日常硬件测试建议使用 `--symlink-install` 编译，或者启动时显式传入 source
目录下的配置文件路径。否则非 symlink 的旧 install 可能仍然读到安装目录里的
`.yaml.template` 占位配置。

默认手部命名空间：

```text
/hand_left
/hand_right
```

## 启动

先编译并 source 工作区：

```bash
colcon build --packages-select wuji_glove wujihand_teleop
source install/setup.zsh   # zsh
# source install/setup.bash  # bash
```

双手：

```bash
ros2 launch wujihand_teleop wujihand_teleop.launch.py
```

这个 launch 会同时启动左右手套 publisher、左右 Wuji Hand driver，以及左右
retarget controller。

双手，并显式使用 source 目录配置：

```bash
ros2 launch wujihand_teleop wujihand_teleop.launch.py \
  hand_config:=$PWD/src/teleop_algorithm/wujihand_teleop/config/wujihand_teleop.yaml \
  glove_config:=$PWD/src/teleop_device/wuji_glove/config/wuji_glove.yaml \
  retarget_config_dir:=$PWD/src/teleop_algorithm/wujihand_teleop/config
```

单手：

```bash
ros2 launch wujihand_teleop wujihand_teleop.launch.py enable_right:=false
ros2 launch wujihand_teleop wujihand_teleop.launch.py enable_left:=false
```

检查命令频率：

```bash
ros2 topic hz /wuji_glove/left/keypoints
ros2 topic hz /wuji_glove/right/keypoints
ros2 topic hz /hand_left/joint_commands
ros2 topic hz /hand_right/joint_commands
```

## 依赖

运行时需要：

- `wuji_sdk`
- `wuji_retargeting`
- `pinocchio`
- `nlopt`
- `wujihand_driver`

当前工作区已有 `wujihand_driver`。Python retarget 相关依赖还没有 vendor 到本仓库，
硬件启动前需要先安装或纳入仓库。
