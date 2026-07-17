# vive_openvr

`vive_openvr` 通过 SteamVR/OpenVR 读取 HTC Vive Tracker 位姿，并发布 ROS 2 TF 和
`geometry_msgs/msg/PoseStamped`。这个包只负责输入设备，不做 Marvin 机械臂 IK 或控制。

## 坐标语义

节点使用 OpenVR 的 `TrackingUniverseStanding` 查询 tracker 位姿。默认父坐标系是：

```text
vive_world
```

这表示 SteamVR standing tracking space，不是 Marvin `base_link`，也不是人的腰/胸/头。
如果只使用左右手腕 tracker，后续遥操作算法通常应先做增量式接管；如果要做人体系绝对映射，
建议再加 `chest` tracker，并在算法包中计算：

```text
T_chest_wrist = inverse(T_vive_world_chest) * T_vive_world_wrist
```

默认 TF：

```text
vive_world -> vive/left_wrist
vive_world -> vive/right_wrist
vive_world -> vive/chest       # 配置后发布
vive_world -> vive/left_arm    # 配置后发布
vive_world -> vive/right_arm   # 配置后发布
```

默认 PoseStamped 话题：

```text
/vive/left_wrist/pose
/vive/right_wrist/pose
/vive/chest/pose
/vive/left_arm/pose
/vive/right_arm/pose
```

## 参考资源

- 本包无头显配置实操流程：
  [docs/steamvr_no_hmd_setup_zh.md](docs/steamvr_no_hmd_setup_zh.md)
- Wuji 官方 Vive/SteamVR 遥操作说明：
  https://github.com/wuji-technology/wuji-hand-teleop/blob/main/docs/STEAMVR.md
- Wuji 官方 tracker 佩戴说明：
  https://github.com/wuji-technology/wuji-hand-teleop/blob/main/docs/tracker-wearing-guide.md
- HTC Vive Tracker 3.0 配对说明：
  https://www.vive.com/us/support/tracker3/category_howto/pairing-vive-tracker.html
- HTC Base Station 2.0 安装说明：
  https://www.vive.com/us/support/vive-pro/category_howto/installing-the-base-stations.html
- SteamVR 配置文件说明：
  https://developer.valvesoftware.com/wiki/SteamVR/steamvr.vrsettings
- OpenVR/SteamVR SDK 入口：
  https://partner.steamgames.com/doc/features/steamvr/openvr

## 硬件准备

最小调试配置：

```text
2 x Vive Tracker        左右手腕
2 x USB Dongle          每个 tracker 一个接收器
1-2 x Lighthouse        推荐 2 个，覆盖更稳定
1 x PC                  安装 Steam + SteamVR
```

推荐后续人体参考系配置：

```text
3 x Vive Tracker        chest + left_wrist + right_wrist
```

如果要使用上臂方向辅助 IK，可再增加：

```text
left_arm + right_arm
```

## 上电和连接顺序

1. 固定 Lighthouse。

   两个基站应面对操作区域中心，安装在稳定位置，避免振动。接入原装电源后等待状态灯稳定。
   基站不通过 USB 向 ROS 发送数据；tracker 通过光学定位看到基站后，位姿由 SteamVR 解算。

2. 插入 USB dongle。

   每个 tracker 需要一个 dongle。插入后可用下面命令粗略确认 Valve 设备存在：

   ```bash
   lsusb | grep 28de
   ```

3. 启动 SteamVR。

   Ubuntu Wayland 环境通常需要强制 X11 后端：

   ```bash
   GDK_BACKEND=x11 QT_QPA_PLATFORM=xcb steam steam://rungameid/250820
   ```

   X11 桌面可直接：

   ```bash
   steam steam://rungameid/250820
   ```

4. 打开 tracker。

   短按电源键开机。若未配对，按 SteamVR 界面进行配对。

5. 配对 tracker。

   SteamVR 窗口中选择：

   ```text
   Devices -> Pair Controller -> I want to pair a different type of controller -> HTC Vive Tracker
   ```

   按住 tracker 电源键约 2 秒进入配对，状态灯闪蓝；变绿表示配对成功。

## 无头显模式

如果没有 VR 头显，需要使用 SteamVR null driver。这个模式是工程常用方案，但 HTC 官方论坛中
也提到“无 HMD 使用 tracker”不属于标准消费者支持路径，实机部署前要单独验证稳定性。

1. 开启 null driver：

   ```bash
   nano ~/.steam/steam/steamapps/common/SteamVR/drivers/null/resources/settings/default.vrsettings
   ```

   确认：

   ```json
   {
     "driver_null": {
       "enable": true
     }
   }
   ```

2. 修改 SteamVR 用户配置：

   ```bash
   nano ~/.steam/debian-installation/config/steamvr.vrsettings
   ```

   在 `"steamvr"` 段中确认：

   ```json
   {
     "steamvr": {
       "requireHmd": false,
       "forcedDriver": "null",
       "activateMultipleDrivers": true
     }
   }
   ```

   Steam 安装路径可能因系统不同而变化，常见路径还有 `~/.local/share/Steam/`。

## 软件依赖

ROS 依赖由 `package.xml` 声明。OpenVR Python 绑定通常需要单独安装到当前 ROS 环境：

```bash
python3 -m pip install openvr
```

还需要 SteamVR 正在运行，否则 `openvr.init()` 会失败。

## 配置 serial

构建并 source 后，先列出 SteamVR 当前看到的 tracker：

```bash
cd /home/ccs/ros2/teleop_ws
colcon build --packages-select vive_openvr
source install/setup.bash
ros2 run vive_openvr list_trackers
```

输出类似：

```text
index=3  class=GenericTracker    serial=LHR-XXXXXXXX connected=True valid=True result=200 Running_OK xyz=[0.123, 1.234, -0.456]
index=4  class=GenericTracker    serial=LHR-YYYYYYYY connected=True valid=False result=101 Calibrating_OutOfRange xyz=n/a
```

只有 `valid=True` 且 `result=200 Running_OK` 时，`vive_openvr_node` 才会发布对应 pose。
`connected=True` 只表示 tracker 无线连接成功，不代表 Lighthouse 定位已经有效。

复制模板并填入 serial：

```bash
cp src/teleop_device/vive_openvr/config/vive_openvr.yaml.template \
  src/teleop_device/vive_openvr/config/vive_openvr.yaml
```

编辑：

```yaml
tracker_serials:
  left_wrist: "LHR-XXXXXXXX"
  right_wrist: "LHR-YYYYYYYY"
  # chest: "LHR-ZZZZZZZZ"
```

重新构建安装配置：

```bash
colcon build --packages-select vive_openvr
source install/setup.bash
```

也可以 launch 时直接指定 source 目录配置：

```bash
ros2 launch vive_openvr vive_openvr.launch.py \
  config:=/home/ccs/ros2/teleop_ws/src/teleop_device/vive_openvr/config/vive_openvr.yaml
```

## 启动

确认 SteamVR 已启动、tracker 为绿色状态后：

```bash
ros2 launch vive_openvr vive_openvr.launch.py
```

同时打开 RViz：

```bash
ros2 launch vive_openvr vive_openvr.launch.py rviz:=true
```

检查 TF：

```bash
ros2 run tf2_ros tf2_echo vive_world vive/left_wrist
ros2 run tf2_ros tf2_echo vive_world vive/right_wrist
```

检查话题：

```bash
ros2 topic hz /vive/left_wrist/pose
ros2 topic echo --once /vive/left_wrist/pose
```

RViz preset 默认使用 `vive_world` 作为 Fixed Frame，并显示 TF、
`/vive/left_wrist/pose`、`/vive/right_wrist/pose` 和 `/vive/chest/pose`。
没有配置的 tracker topic 会保持未接收状态，不影响查看已在线的 tracker。

## 重要参数

```yaml
publish_rate_hz: 120.0
parent_frame: "vive_world"
child_frame_prefix: "vive"
publish_tf: true
publish_pose_topics: true
pose_topic_prefix: "/vive"
apply_role_corrections: true
```

`apply_role_corrections` 默认保持 Wuji 官方 `openvr_input` 的角色修正矩阵，用于
`chest`、`left_wrist`、`right_wrist` 的佩戴方向约定。`left_arm`、`right_arm` 当前透传。

`wrist_offsets` 在 OpenVR 原始 tracker 局部坐标系下应用，用于把 tracker 原点平移到期望的
腕部控制点。第一版不确定安装外参时保持 `[0, 0, 0]`。

## 注意事项

- 不要把 `vive_world` 当作机器人基座坐标系。机器人控制算法必须单独做增量接管或外参标定。
- 运行前确认操作区无遮挡，tracker 能被至少一个 Lighthouse 看到。
- 基站通电后不要移动；移动后 SteamVR tracking space 可能变化，需要重新标定。
- 每个 tracker 推荐独立 dongle，dongle 之间尽量拉开距离，减少 USB/2.4GHz 干扰。
- 先验证 `list_trackers` 能看到 serial，再启动 ROS 节点。
- 遥操作机械臂前，先只看 TF/Pose 是否稳定，不要直接把 tracker 位姿送入硬件。
- 如果 SteamVR 无法启动，先确认桌面会话类型：

  ```bash
  echo $XDG_SESSION_TYPE
  ```

  Wayland 下优先使用前面的 `GDK_BACKEND=x11 QT_QPA_PLATFORM=xcb` 启动方式。

## 常见问题

`openvr` import 失败：

```bash
python3 -m pip install openvr
```

`OpenVR connect failed`：

- SteamVR 未启动。
- null driver 配置不完整。
- 当前 shell/容器环境看不到 SteamVR 运行时。

找不到某个 tracker：

- tracker 没开机或没配对。
- serial 填错。
- dongle 未插入或被其他设备占用。
- tracker 不在 Lighthouse 覆盖范围内。

Pose 间歇丢失：

- 检查遮挡、反光、基站振动。
- 拉开 dongle 间距。
- 给 tracker 充电。
