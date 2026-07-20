# AGENTS.md

Development notes for this ROS 2 teleoperation workspace.

## Workspace Layout

- Robot-side packages live under `src/marvin_ros2`, `src/wujihandros2`,
  `src/robot_description`, and `src/robot_bringup`.
- Teleoperation input devices live under `src/teleop_device`.
- Teleoperation algorithms live under `src/teleop_algorithm`.
- `robot_bringup` is the whole-system hardware/visualization integration layer.
  It should not launch teleoperation input devices or teleoperation algorithms.
- Keep launch files in `launch/`, runtime YAML in `config/`, and
  hardware-specific code inside the matching driver package.

## ROS 2 Package Style

- Prefer `ament_cmake` for new packages, including packages that install Python
  helper nodes.
- Install Python executables with
  `install(PROGRAMS ... DESTINATION lib/${PROJECT_NAME})`.
- Do not commit generated build artifacts, Python caches, local logs, or
  machine-specific runtime configs.

## Topic Ownership

- Hardware drivers publish device-scoped feedback topics, not global
  `/joint_states`.
- The global `/joint_states` stream is owned by the whole-robot aggregator in
  `robot_bringup` and is for `robot_state_publisher`/RViz.
- Marvin feedback stays under `/marvin/left/joint_states` and
  `/marvin/right/joint_states`.
- Wuji Hand feedback stays under `/hand_left/joint_states` and
  `/hand_right/joint_states`.
- Teleoperation algorithms publish commands to device command topics such as
  `/marvin/right/joint_commands` and `/hand_right/joint_commands`.

## Driver Safety

- Driver nodes must not send default motion commands during startup.
- Any node that publishes motion commands must wait for real feedback first and
  initialize from the current measured state.
- Keep Marvin position, joint impedance, and joint impedance PD-feedforward
  modes explicit at launch time.
- Do not persist controller parameters unless the user explicitly asks for it.
- Preserve SDK-documented minimum call intervals in driver code.

## Marvin SDK

- Marvin integration targets the old SDK under
  `/home/ccs/ros2/TJ_FX_ROBOT_CONTRL_SDK/contrlSDK`.
- Vendored SDK headers and `libMarvinSDK.so` under
  `marvin_driver/vendor/contrlSDK` should remain byte-for-byte copies of the
  selected SDK output unless a migration note explains the change.
- SDK check/demo nodes connect directly to the controller. Run them only when
  `marvin_driver_node` is stopped.

## Verification

- Do not build ROS packages from a conda environment; use the system ROS Python
  environment.
- For package changes, run a focused
  `colcon build --symlink-install --packages-select ...`.
- For bringup changes, verify `ros2 launch ... --show-args` or a short launch
  run when hardware is not required.
- For nodes that handle shutdown, verify Ctrl-C/SIGINT exits without Python
  tracebacks.
