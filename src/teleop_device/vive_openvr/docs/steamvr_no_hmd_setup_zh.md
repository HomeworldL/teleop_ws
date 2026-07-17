# SteamVR 无头显 Vive Tracker 配置流程

本文记录在 Ubuntu + ROS 2 环境下，不使用 VR 头显，仅使用 HTC Vive Tracker、
USB dongle 和 Lighthouse，通过 SteamVR/OpenVR 给 `vive_openvr` 发布位姿的完整流程。

## 1. 安装 Steam 和 SteamVR

安装 Steam：

```bash
sudo apt install steam
```

启动 Steam：

```bash
steam
```

首次启动会更新 Steam，并要求登录账号。登录后，在 Steam 库中搜索并安装：

```text
SteamVR
```

确认 SteamVR 安装路径：

```bash
ls ~/.steam/debian-installation/steamapps/common/SteamVR
```

如果该路径不存在，再检查：

```bash
ls ~/.steam/steam/steamapps/common/SteamVR
```

本文后续命令以实际验证过的路径为准：

```text
~/.steam/debian-installation/steamapps/common/SteamVR
```

## 2. 启用 null driver

无头显时，需要让 SteamVR 使用 null HMD。

编辑 null driver 默认配置：

```bash
nano ~/.steam/debian-installation/steamapps/common/SteamVR/drivers/null/resources/settings/default.vrsettings
```

找到：

```json
"driver_null": {
   "enable": false
}
```

改为：

```json
"driver_null": {
   "enable": true
}
```

保存退出。

## 3. 启动一次 SteamVR 生成用户配置

Wayland 桌面建议使用 XWayland 参数启动：

```bash
GDK_BACKEND=x11 QT_QPA_PLATFORM=xcb steam steam://rungameid/250820
```

X11 桌面通常可以直接：

```bash
steam steam://rungameid/250820
```

确认用户配置已生成：

```bash
ls ~/.steam/debian-installation/config/steamvr.vrsettings
```

## 4. 写入无头显关键配置

编辑：

```bash
nano ~/.steam/debian-installation/config/steamvr.vrsettings
```

确保 `"steamvr"` 段包含：

```json
{
   "steamvr": {
      "requireHmd": false,
      "forcedDriver": "null",
      "activateMultipleDrivers": true
   }
}
```

如果不想手动处理 JSON 逗号，可以用下面脚本自动写入：

```bash
python3 - <<'PY'
import json
from pathlib import Path

p = Path.home() / ".steam/debian-installation/config/steamvr.vrsettings"
data = json.loads(p.read_text())
steamvr = data.setdefault("steamvr", {})
steamvr["requireHmd"] = False
steamvr["forcedDriver"] = "null"
steamvr["activateMultipleDrivers"] = True
p.write_text(json.dumps(data, indent=3) + "\n")
print(p)
PY
```

`activateMultipleDrivers` 很重要。没有它时，SteamVR 可能只暴露 null HMD，
tracker 虽然绿灯连接，但 OpenVR 设备列表里看不到有效 tracker pose。

## 5. 重启 SteamVR

```bash
pkill vrserver
pkill vrmonitor
GDK_BACKEND=x11 QT_QPA_PLATFORM=xcb steam steam://rungameid/250820
```

确认 null HMD 已生效：

```bash
ps aux | grep vrserver | grep -v grep
grep -i "null" ~/.steam/debian-installation/logs/vrserver.txt | tail -5
```

期望看到：

```text
Using existing HMD null.Null Serial Number
```

## 6. 连接硬件

推荐最小测试配置：

```text
1 x Vive Tracker
1 x USB Watchman Dongle
1 x Lighthouse Base Station
```

步骤：

1. Lighthouse 接电源，等待状态灯稳定绿色。
2. USB dongle 插到电脑。
3. 确认 dongle：

   ```bash
   lsusb | grep 28de
   ```

   常见输出：

   ```text
   ID 28de:2101 Valve Software Watchman Dongle
   ```

4. 短按 tracker 电源键开机。
5. 如未配对，在 SteamVR 小状态窗口中选择：

   ```text
   Devices -> Pair Controller -> I want to pair a different type of controller -> HTC Vive Tracker
   ```

6. 按提示长按 tracker 电源键进入配对。配对成功后 tracker 灯会变绿。

注意：tracker 绿灯只表示无线连接成功，不代表 Lighthouse 定位已经有效。

## 7. 安装 Python OpenVR 绑定

在实际运行 ROS 的 Python 环境里安装 `openvr`。如果使用虚拟环境，例如 `(teleop)`，
必须在该环境里安装：

```bash
python -m pip install openvr
```

验证：

```bash
python -c "import openvr; print(openvr.__file__)"
```

## 8. 构建 vive_openvr

```bash
cd /home/ccs/ros2/teleop_ws
colcon build --packages-select vive_openvr
source ./install/local_setup.zsh
```

## 9. 查看 tracker 列表和状态

```bash
ros2 run vive_openvr list_trackers --all
```

正常能看到 null HMD 和 tracker：

```text
index=0  class=HMD             serial=Null Serial Number connected=True  valid=True  result=200 Running_OK xyz=[0.000, 0.000, 0.000]
index=1  class=GenericTracker  serial=LHR-E651F39A      connected=True  valid=True  result=200 Running_OK xyz=[...]
```

只列 tracker：

```bash
ros2 run vive_openvr list_trackers
```

## 10. 配置 tracker serial

复制模板：

```bash
cp src/teleop_device/vive_openvr/config/vive_openvr.yaml.template \
  src/teleop_device/vive_openvr/config/vive_openvr.yaml
```

编辑：

```bash
nano src/teleop_device/vive_openvr/config/vive_openvr.yaml
```

示例：

```yaml
tracker_serials:
  left_wrist: "LHR-E651F39A"
  right_wrist: ""
  # chest: ""
```

重新构建安装配置：

```bash
colcon build --packages-select vive_openvr
source ./install/local_setup.zsh
```

也可以 launch 时直接指定 source 配置文件：

```bash
ros2 launch vive_openvr vive_openvr.launch.py \
  config:=/home/ccs/ros2/teleop_ws/src/teleop_device/vive_openvr/config/vive_openvr.yaml
```

## 11. 启动节点和 RViz

只启动节点：

```bash
ros2 launch vive_openvr vive_openvr.launch.py
```

启动节点和 RViz：

```bash
ros2 launch vive_openvr vive_openvr.launch.py rviz:=true
```

检查 topic：

```bash
ros2 topic list
ros2 topic hz /vive/left_wrist/pose
ros2 topic echo /vive/left_wrist/pose
```

检查 TF：

```bash
ros2 run tf2_ros tf2_echo vive_world vive/left_wrist
```

RViz preset 默认：

```text
Fixed Frame: vive_world
TF display enabled
Pose displays:
  /vive/left_wrist/pose
  /vive/right_wrist/pose
  /vive/chest/pose
```

## 12. 常见状态和排查

### 只看到 null HMD

输出：

```text
index=0 class=HMD serial=Null Serial Number
```

排查：

- SteamVR 是否已启动。
- `steamvr.vrsettings` 是否有：

  ```json
  "requireHmd": false,
  "forcedDriver": "null",
  "activateMultipleDrivers": true
  ```

- 是否已重启 `vrserver`。
- dongle 是否插入：

  ```bash
  lsusb | grep 28de
  ```

### tracker 绿灯但没有 ROS 数据

先看：

```bash
ros2 run vive_openvr list_trackers --all
```

如果看到：

```text
connected=True valid=False result=101 Calibrating_OutOfRange xyz=n/a
```

说明 tracker 和 dongle 已连接，但 Lighthouse 定位无效。此时 `/vive/.../pose`
不会发布数据。

处理：

- 调整 tracker 和 Lighthouse 距离。实测过近或位置太偏会导致没有有效 pose。
- 推荐先放在基站正前方 1-2 米。
- 让 tracker 大面积传感器区域朝向基站，慢慢转动几下。
- 确认没有手、衣物、桌面边缘遮挡 tracker 光敏区域。
- 先只用一个基站测试，减少 channel/mode 干扰。

目标状态：

```text
connected=True valid=True result=200 Running_OK xyz=[...]
```

一旦变成这个状态，`/vive/left_wrist/pose`、TF 和 RViz 会有数据。

### Base Station 1.0/2.0 模式

Base Station 1.0：

- 单个基站：设为 `A`
- 两个基站：通常设为 `B` 和 `C`

Base Station 2.0：

- 多个基站 channel 不能重复。
- 通常通过 SteamVR 管理 channel。

### 查看 SteamVR 关键日志

```bash
grep -i "LHR\\|lighthouse\\|watchman\\|dongle\\|out of range\\|calibrating" \
  ~/.steam/debian-installation/logs/vrserver.txt | tail -120
```

关键提示：

```text
No optical frames in past 5 seconds
SwSyncDetect Restart
```

通常表示 tracker 没有稳定收到 Lighthouse 光学扫描。

## 13. 后续多 tracker

一次连接多个 tracker 时：

- 每个 tracker 推荐一个 dongle。
- 先逐个配对，确认每个都能 `valid=True result=200`。
- 在 `vive_openvr.yaml` 中按 serial 映射角色：

  ```yaml
  tracker_serials:
    chest: "LHR-..."
    left_wrist: "LHR-..."
    right_wrist: "LHR-..."
    left_arm: "LHR-..."
    right_arm: "LHR-..."
  ```

启动一个 `vive_openvr_node` 即可管理所有 tracker，不需要每个 tracker 启一个节点。
