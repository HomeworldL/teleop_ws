# vive_openvr

`vive_openvr` reads HTC Vive Tracker poses through SteamVR/OpenVR and publishes
ROS 2 TF plus `geometry_msgs/msg/PoseStamped` topics. This package is only the
teleoperation input driver; Marvin arm IK and robot commands are handled by
`vive_marvin_teleop`.

## Coordinate Semantics

The node queries OpenVR poses in `TrackingUniverseStanding`. The default parent
frame is:

```text
vive_world
```

This is SteamVR standing tracking space. It is not Marvin `base_link`, the
operator waist, chest, or head. The default arm teleoperation setup uses three
trackers: `chest`, `left_wrist`, and `right_wrist`. Downstream algorithms use
the chest tracker as the operator body reference and compute each wrist pose
relative to it:

```text
T_chest_wrist = inverse(T_vive_world_chest) * T_vive_world_wrist
```

Default TF frames for the three-tracker setup:

```text
vive_world -> vive/left_wrist
vive_world -> vive/right_wrist
vive_world -> vive/chest
vive_world -> vive/left_arm    # when configured
vive_world -> vive/right_arm   # when configured
```

Default pose topics:

```text
/vive/left_wrist/pose
/vive/right_wrist/pose
/vive/chest/pose
/vive/left_arm/pose
/vive/right_arm/pose
```

## References

- Local no-HMD setup notes:
  [docs/steamvr_no_hmd_setup_zh.md](docs/steamvr_no_hmd_setup_zh.md)
- Wuji official Vive/SteamVR teleoperation notes:
  https://github.com/wuji-technology/wuji-hand-teleop/blob/main/docs/STEAMVR.md
- Wuji official tracker wearing guide:
  https://github.com/wuji-technology/wuji-hand-teleop/blob/main/docs/tracker-wearing-guide.md
- HTC Vive Tracker 3.0 pairing:
  https://www.vive.com/us/support/tracker3/category_howto/pairing-vive-tracker.html
- HTC Base Station 2.0 installation:
  https://www.vive.com/us/support/vive-pro/category_howto/installing-the-base-stations.html
- SteamVR settings file:
  https://developer.valvesoftware.com/wiki/SteamVR/steamvr.vrsettings
- OpenVR/SteamVR SDK:
  https://partner.steamgames.com/doc/features/steamvr/openvr

## Hardware

Default arm teleoperation setup:

```text
3 x Vive Tracker        chest + left_wrist + right_wrist
3 x USB Dongle          one dongle per tracker
1-2 x Lighthouse        two are preferred for coverage
1 x PC                  Steam + SteamVR
```

Optional upper-arm trackers can be added later:

```text
left_arm + right_arm
```

## Power and Connection Order

1. Mount and power the Lighthouse base stations.

   The base stations should face the operation area and remain mechanically
   stable. They do not send ROS data over USB. SteamVR computes tracker poses
   after the trackers see the Lighthouse sweep.

2. Plug in USB dongles.

   Use one dongle per tracker. A rough USB check is:

   ```bash
   lsusb | grep 28de
   ```

3. Start SteamVR.

   On Ubuntu Wayland, force X11 backends:

   ```bash
   GDK_BACKEND=x11 QT_QPA_PLATFORM=xcb steam steam://rungameid/250820
   ```

   On X11:

   ```bash
   steam steam://rungameid/250820
   ```

4. Power on the trackers.

   Short-press the tracker power button. If a tracker is not paired, use the
   SteamVR pairing dialog.

5. Pair trackers.

   In SteamVR:

   ```text
   Devices -> Pair Controller -> I want to pair a different type of controller -> HTC Vive Tracker
   ```

   Hold the tracker power button for about two seconds to enter pairing mode.
   Blue blinking means pairing mode; green means wireless pairing succeeded.

## No-HMD Mode

Without a VR headset, SteamVR must be configured to use the null HMD driver.
This is a practical engineering setup, but tracker-only use is not the normal
consumer path, so verify it before relying on it for hardware teleoperation.

Enable the null driver:

```bash
nano ~/.steam/steam/steamapps/common/SteamVR/drivers/null/resources/settings/default.vrsettings
```

Confirm:

```json
{
  "driver_null": {
    "enable": true
  }
}
```

Set the user SteamVR configuration:

```bash
nano ~/.steam/debian-installation/config/steamvr.vrsettings
```

Confirm the `steamvr` section contains:

```json
{
  "steamvr": {
    "requireHmd": false,
    "forcedDriver": "null",
    "activateMultipleDrivers": true
  }
}
```

The Steam path may differ. Common alternatives include `~/.local/share/Steam/`.

## Software Dependency

ROS dependencies are declared in `package.xml`. Install the Python OpenVR
binding into the active ROS Python environment:

```bash
python3 -m pip install openvr
```

SteamVR must be running before `openvr.init()` can succeed.

## Configure Tracker Serials

Build and source the workspace, then list the devices SteamVR currently knows:

```bash
cd /home/ccs/ros2/teleop_ws
colcon build --packages-select vive_openvr
source install/setup.bash
ros2 run vive_openvr list_trackers --all
```

Example:

```text
index=1  class=GenericTracker    serial=LHR-XXXXXXXX connected=True  valid=True  result=200 Running_OK xyz=[0.123, 1.234, -0.456]
index=2  class=GenericTracker    serial=LHR-YYYYYYYY connected=True  valid=False result=101 Calibrating_OutOfRange xyz=n/a
index=3  class=TrackingReference serial=LHB-ZZZZZZZZ connected=True  valid=True  result=200 Running_OK xyz=[0.000, 0.000, 0.000]
```

Only `GenericTracker` devices are Vive Trackers. `TrackingReference` devices are
Lighthouse base stations. A green tracker LED only confirms wireless pairing;
the pose is usable only when `valid=True` and `result=200 Running_OK`.

Copy the template and fill in serials:

```bash
cp src/teleop_device/vive_openvr/config/vive_openvr.yaml.template \
  src/teleop_device/vive_openvr/config/vive_openvr.yaml
```

Default three-tracker arm setup:

```yaml
tracker_serials:
  left_wrist: "LHR-E651F39A"
  right_wrist: "LHR-F757F16E"
  chest: "LHR-F854821A"
```

Rebuild or pass the source-tree config explicitly:

```bash
colcon build --packages-select vive_openvr
source install/setup.bash
```

```bash
ros2 launch vive_openvr vive_openvr.launch.py \
  config:=/home/ccs/ros2/teleop_ws/src/teleop_device/vive_openvr/config/vive_openvr.yaml
```

## Launch and Visualization

Start the input node:

```bash
ros2 launch vive_openvr vive_openvr.launch.py
```

Start with RViz:

```bash
ros2 launch vive_openvr vive_openvr.launch.py rviz:=true
```

Check TF and topics:

```bash
ros2 run tf2_ros tf2_echo vive_world vive/chest
ros2 run tf2_ros tf2_echo vive_world vive/left_wrist
ros2 run tf2_ros tf2_echo vive_world vive/right_wrist
ros2 topic hz /vive/chest/pose
ros2 topic hz /vive/left_wrist/pose
ros2 topic hz /vive/right_wrist/pose
ros2 topic echo --once /vive/chest/pose
```

The RViz preset uses `vive_world` as the Fixed Frame and displays TF plus the
default wrist/chest pose topics. Unconfigured tracker topics may show as
unreceived; that does not affect configured trackers.

## Parameters

```yaml
publish_rate_hz: 120.0
parent_frame: "vive_world"
child_frame_prefix: "vive"
publish_tf: true
publish_pose_topics: true
pose_topic_prefix: "/vive"
apply_role_corrections: true
```

`apply_role_corrections` keeps the Wuji official `openvr_input` orientation
convention for `chest`, `left_wrist`, and `right_wrist`. `left_arm` and
`right_arm` are currently passed through.

`wrist_offsets` are applied in the raw tracker local frame before role
correction. Use them to move the tracker origin to the desired wrist control
point once the physical mount is fixed.

## Troubleshooting Notes

- `Unable to read VR Path Registry` usually means SteamVR has never been
  launched for this user or `openvrpaths.vrpath` has not been created yet.
- `OpenVR connect failed` usually means SteamVR is not running, null-HMD mode is
  incomplete, or the shell cannot see the SteamVR runtime.
- `connected=True valid=False` means SteamVR knows the device but is not
  providing a valid pose. Check Lighthouse power, tracker visibility, distance,
  reflections, battery, and occlusion.
- `connected=False result=1 Uninitialized` on a `GenericTracker` means that
  tracker is known from SteamVR history but is not currently active/pose-valid.
- `TrackingReference` is a Lighthouse base station, not a tracker. Do not use
  its serial for `left_wrist`, `right_wrist`, or `chest`.
- Each tracker should have its own dongle. If multiple trackers are paired to
  one dongle or dongles are too close together, tracking can become unstable.
- Do not use `vive_world` directly as the robot base frame. Arm teleoperation
  must use body-relative transforms or a separate robot-to-Vive calibration.
