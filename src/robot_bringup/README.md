# robot_bringup

`robot_bringup` starts the combined Marvin arms and Wuji hands in either real-driver or
dummy-driver mode, then publishes the whole-robot visualization state.

The package provides `scripts/joint_state_aggregator.py`, a Python ROS node installed as
`joint_state_aggregator`. It subscribes to per-device joint-state topics and publishes one
global `/joint_states` stream for `robot_state_publisher`.

The default joint list matches `robot_description/urdf/robot.xacro`: 14 Marvin arm joints
plus 40 Wuji hand joints. `/joint_states` is only the whole-robot visualization stream;
hardware and dummy drivers should keep publishing their own per-device topics.

Default inputs:

```text
/marvin/left/joint_states
/marvin/right/joint_states
/hand_left/joint_states
/hand_right/joint_states
```

If an input topic is missing, those joints stay at zero. When a topic later appears, the
matching joint names override the zero values.

## Real Bringup

Start the real low-level drivers for both arms and both hands, plus aggregation,
whole-robot `robot_state_publisher`, and RViz:

```bash
ros2 launch robot_bringup bringup_real.launch.py
```

`bringup_real.launch.py` includes `marvin_bringup` and
`wujihand_bringup/wujihand_dual_driver.launch.py`. The Marvin driver defaults to `/marvin`
with `arms:=both`. Wuji hands are discovered by USB serial number and each driver publishes
under `/hand_left` or `/hand_right` after detecting physical handedness.

Use another Marvin mode launch explicitly when needed:

```bash
ros2 launch robot_bringup bringup_real.launch.py \
  marvin_launch:=marvin_impedance.launch.py
```

## Dummy Bringup

Start a fake low-level driver for both arms and both hands, plus the same aggregation and
visualization:

```bash
ros2 launch robot_bringup bringup_dummy.launch.py
```

`dummy_driver` subscribes to the normal command topics and immediately republishes those
commands as device-scoped state feedback:

```text
/marvin/left/joint_commands   -> /marvin/left/joint_states
/marvin/right/joint_commands  -> /marvin/right/joint_states
/hand_left/joint_commands     -> /hand_left/joint_states
/hand_right/joint_commands    -> /hand_right/joint_states
```

This lets real teleoperation input and mapping nodes move the RViz robot without arm or hand
hardware.

Run either bringup without RViz:

```bash
ros2 launch robot_bringup bringup_dummy.launch.py rviz:=false
ros2 launch robot_bringup bringup_real.launch.py rviz:=false
```

Disable real hand drivers when testing arms only:

```bash
ros2 launch robot_bringup bringup_real.launch.py hands:=false
```
