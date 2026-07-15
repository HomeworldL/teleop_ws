# marvin_driver

`marvin_driver` is the ROS 2 C++ wrapper around the old Tianji Marvin controller SDK.
It vendors the rebuilt old SDK shared library and headers under `vendor/contrlSDK`.

## SDK Migration Notes

The original SDK demos are standalone processes that connect to the controller directly.
The ROS driver keeps that direct SDK ownership inside one node and exposes ROS topics and
services for normal operation.

Mapped in this package:

- `showcase_new_control_sdk_usage.cpp`
  - `Connect` -> driver startup or `/marvin/connect`
  - `SetJointMode` -> `control_mode:=position`
  - `SetImpJointMode` -> `control_mode:=joint_impedance`
  - `SetJointPostionCmd` -> `/marvin/left/joint_commands` and `/marvin/right/joint_commands`
- `showcase_link_check.cpp`
  - `marvin_link_check_node`
- `showcase_cmd_delay.cpp`
  - `marvin_cmd_delay_check_node`

Not migrated yet:

- PVT and PLN trajectory demos
- drag teaching demos
- Cartesian impedance and force-control demos
- end-effector CAN/485 demos

Those are left out of the first driver because the current goal is teleoperation and basic
device validation.

## Control Modes

The driver supports three launch-time modes:

```text
position
joint_impedance
joint_impedance_pd
```

Position mode calls:

```cpp
SetJointMode(arm, velocity_ratio, acceleration_ratio)
```

Joint impedance mode calls:

```cpp
OnSetIntPara("R.A0.BASIC.JointPIDCtlType", 0)  // left arm
OnSetIntPara("R.A1.BASIC.JointPIDCtlType", 0)  // right arm
SetImpJointMode(arm, velocity_ratio, acceleration_ratio, K, D)
```

Joint impedance PD-feedforward mode calls the same impedance setup but sets
`JointPIDCtlType` to `1` for the selected arm before entering joint impedance mode.

The driver does not call `OnSavePara()`. `JointPIDCtlType` is only set at runtime.

All three modes use the same joint command API after startup:

```cpp
SetJointPostionCmd(arm, joint_degrees)
```

ROS commands remain in radians and are converted inside the driver.

## Startup Error Handling

The driver uses the SDK concise `Connect` function. In the old SDK, `Connect` calls
`CheckArmError()` and `CheckServoError()` internally. `SetJointMode` and
`SetImpJointMode` also repeat those checks before mode switching.

That means startup currently attempts to clear arm and servo errors through the SDK before
the driver starts accepting joint commands. If errors remain after clearing, mode setup
fails and that arm rejects commands.

## Command Behavior

The driver does not send any default joint command during startup. It only:

- connects to the controller
- configures the requested control mode
- publishes feedback
- waits for `/marvin/*/joint_commands`

Nodes that need to command motion should wait for `/marvin/*/joint_states` first and use
the first feedback position as their initial command. `marvin_zero_position_node` follows
that rule.

## Check Nodes

Run these only when `marvin_driver_node` is not running, because they connect to the SDK
directly:

```bash
ros2 run marvin_driver marvin_link_check_node --ros-args -p robot_ip:=192.168.1.190
ros2 run marvin_driver marvin_cmd_delay_check_node --ros-args -p robot_ip:=192.168.1.190 -p arm:=A
```
