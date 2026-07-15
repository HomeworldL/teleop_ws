# teleop_ws

这是用于遥操作系统的 ROS 2 工作区，包含双臂、双手整机模型和相关驱动集成。

主要入口包是 [`robot_description`](src/robot_description/README_zh.md)。它组合 `src/`
下的资源描述包，生成最终 URDF、RViz 启动文件和 MuJoCo 场景文件。

## 功能包

- `robot_description`：顶层整机模型，组合机械臂、手、相机描述资源，并提供底座、转接件、最终 URDF、RViz 配置和 MJCF 场景。
- `marvin_description`：Marvin M6-S 左右机械臂的 URDF 和 mesh 资源包。
- `wuji_description`：无极五指手左右手 URDF、mesh 和手部 MJCF 资源包。
- `wujihandros2`：无极手 ROS 2 驱动，已作为普通源码集成到当前工作区。
- `realsense2_description`：RealSense 相机 xacro 模型和 mesh 资源包。

## 本地集成说明

`src/wujihandros2` 来自上游 Wuji ROS 2 驱动仓库，但在当前工作区中按普通源码跟踪，
不再作为嵌套 Git 仓库使用。

相对上游布局的本地修改：

- 删除 `src/wujihandros2/.git`。
- 删除上游 `src/wujihandros2/external/` 子模块目录。
- 删除 `src/wujihandros2/.gitmodules`。
- 删除上游 GitHub workflow 元数据 `src/wujihandros2/.github/`。
- driver bringup 包通过当前工作区的 `src/wuji_description` 解析手部模型；该包只保留这里使用的简化一代无极手描述。

上游 `src/wujihandros2/README.md` 和 `src/wujihandros2/build_deb.sh` 保持不改，作为参考。

## 构建

```bash
cd /home/ccs/ros2/teleop_ws
colcon build --symlink-install
source install/setup.bash
```

zsh 环境：

```bash
source install/setup.zsh
```

## 运行

在 RViz 中查看组合后的整机：

```bash
ros2 launch robot_description view_robot.launch.py
```

从 xacro 重新生成展开后的 URDF：

```bash
xacro src/robot_description/urdf/robot.xacro > src/robot_description/urdf/robot.urdf
```

运行 MuJoCo 场景查看器和相机渲染：

```bash
python src/robot_description/mjcf/scene.py
```

只渲染指定相机：

```bash
python src/robot_description/mjcf/scene.py \
  --camera head_camera \
  --camera left_wrist_camera
```
