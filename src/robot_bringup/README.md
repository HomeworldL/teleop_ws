# robot_bringup

`robot_bringup` starts whole-robot visualization for the combined Marvin arms and Wuji
hands.

The package provides `scripts/joint_state_aggregator.py`, a Python ROS node installed as
`joint_state_aggregator`. It subscribes to per-device joint-state topics and publishes one
global `/joint_states` stream for `robot_state_publisher`.

The default joint list matches `robot_description/urdf/robot.xacro`: 14 Marvin arm joints
plus 40 Wuji hand joints. `/joint_states` is only the whole-robot visualization stream;
hardware drivers should keep publishing their own per-device topics.

Default inputs:

```text
/marvin/left/joint_states
/marvin/right/joint_states
/hand_left/joint_states
/hand_right/joint_states
```

If an input topic is missing, those joints stay at zero. When a topic later appears, the
matching joint names override the zero values.

Run visualization:

```bash
ros2 launch robot_bringup view_robot.launch.py
```

Run without RViz:

```bash
ros2 launch robot_bringup view_robot.launch.py rviz:=false
```
