# AGENTS.md

Development rules for this ROS 2 workspace.

## Package Style

- Prefer `ament_cmake` for new ROS 2 packages, including packages that install Python
  helper nodes.
- Install Python executables with `install(PROGRAMS ... DESTINATION lib/${PROJECT_NAME})`
  from `CMakeLists.txt`.
- Keep launch files under `launch/`, runtime YAML under `config/`, and hardware-specific
  code inside the corresponding driver package.
- Do not add generated build artifacts, Python caches, or local logs to source control.

## Topic Layout

- Hardware drivers should publish device-scoped feedback topics, not the global
  `/joint_states`.
- The global `/joint_states` stream is owned by a dedicated whole-robot aggregator node.
- Marvin arm feedback should stay under `/marvin/left/joint_states` and
  `/marvin/right/joint_states`.
- Wuji hand feedback should stay under `/hand_left/joint_states` and
  `/hand_right/joint_states`.

## Driver Safety

- Driver nodes must not send default motion commands during startup.
- If a command stream must be initialized, wait for real feedback first and initialize
  commands from the current measured state.
- Keep position mode, joint impedance mode, and joint impedance PD-feedforward mode
  explicit at launch time.
- Do not persist controller parameters unless the user explicitly asks for it.
- When SDK APIs document a minimum call interval, preserve that interval in driver code.

## Marvin SDK

- The Marvin driver targets the old SDK under
  `/home/ccs/ros2/TJ_FX_ROBOT_CONTRL_SDK/contrlSDK`.
- Vendored SDK headers and `libMarvinSDK.so` under `marvin_driver/vendor/contrlSDK`
  should remain byte-for-byte copies of the selected SDK output unless a migration note
  explains the change.
- SDK check/demo nodes connect directly to the controller; run them only when the main
  `marvin_driver_node` is stopped.

## Verification

- For package changes, run a focused `colcon build --packages-select ...`.
- For bringup changes, verify `ros2 launch ... --show-args` or a short launch run when
  hardware is not required.
- For nodes that handle shutdown, verify Ctrl-C/SIGINT exits without Python tracebacks.
