# wujihandros2

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE) [![Release](https://img.shields.io/github/v/release/wuji-technology/wujihandros2)](https://github.com/wuji-technology/wujihandros2/releases)

这是无极灵巧手的 ROS 2 驱动包，提供 1000 Hz 关节状态发布、实时控制接口、多手配置和 RViz 可视化。

**快速上手见 [Quick Start](#quick-start)。详细文档请参考 Wuji Docs Center 上的 [ROS2 Tutorial](https://docs.wuji.tech/docs/en/wuji-hand/latest/ros2-user-guide/index)。**

| ROS2 版本 | Ubuntu | 构建状态 | Deb 包 |
|:------------:|:------:|:------------:|:-----------:|
| Humble | 22.04 | [![CI](https://github.com/wuji-technology/wujihandros2/actions/workflows/ci.yml/badge.svg?branch=master)](https://github.com/wuji-technology/wujihandros2/actions/workflows/ci.yml) | [Download](https://github.com/wuji-technology/wujihandros2/releases) |
| Kilted | 24.04 | [![CI](https://github.com/wuji-technology/wujihandros2/actions/workflows/ci.yml/badge.svg?branch=master)](https://github.com/wuji-technology/wujihandros2/actions/workflows/ci.yml) | [Download](https://github.com/wuji-technology/wujihandros2/releases) |

## 仓库结构

```text
├── wujihand_bringup/            // 启动驱动的 launch 文件和 demo 脚本
│   ├── launch/
│   └── scripts/
├── external/
│   └── wuji-description/        // URDF 模型、mesh 文件和 RViz 配置（子模块）
├── wujihand_driver/             // 硬件通信核心 ROS 2 driver node
│   ├── include/
│   └── src/
├── wujihand_msgs/               // 自定义 ROS 2 message 和 service 定义
│   ├── msg/
│   └── srv/
├── docs/                        // API 参考和文档
└── README.md
```

## Quick Start

### 安装

```bash
git clone --recurse-submodules https://github.com/wuji-technology/wujihandros2.git
cd wujihandros2
# 如果 clone 时没有带 --recurse-submodules，运行：
# git submodule update --init --recursive
source /opt/ros/humble/setup.bash  # 或 kilted
colcon build
source install/setup.bash
```

### 运行

```bash
# 启动 driver
ros2 launch wujihand_bringup wujihand.launch.py

# 启动并打开 RViz 可视化
ros2 launch wujihand_bringup wujihand.launch.py rviz:=true

# 验证运行状态
ros2 topic echo /hand_0/joint_states --once
```

## 联系方式

如有问题，请联系 [support@wuji.tech](mailto:support@wuji.tech)。
