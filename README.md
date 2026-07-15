# teleop_ws

ROS 2 workspace for the combined dual-arm, dual-hand robot description used by the teleoperation setup.

The main entry package is [`robot_description`](src/robot_description/README.md). It composes the robot from the resource description packages under `src/` and provides the final URDF, RViz launch files, and MuJoCo scene files.

## Packages

- `robot_description`: top-level composed robot model. It calls the arm, hand, and camera description resources, adds the shared base, adapters, final URDF, RViz config, and MJCF scene.
- `marvin_description`: independent resource package for the left and right Marvin M6-S arm URDFs and meshes.
- `wuji_description`: independent resource package for the left and right Wuji hand URDFs, meshes, and hand-only MJCF files.
- `wujihandros2`: Wuji ROS 2 driver packages integrated into this workspace as ordinary source files.
- `realsense2_description`: independent resource package for RealSense camera xacro models and meshes.

## Local Integration Notes

`src/wujihandros2` was imported from the upstream Wuji ROS 2 driver repository and is tracked as part of this workspace, not as a nested Git repository.

Local changes from the upstream layout:

- Removed `src/wujihandros2/.git`.
- Removed the upstream `src/wujihandros2/external/` submodule tree.
- Removed `src/wujihandros2/.gitmodules`.
- Removed upstream GitHub workflow metadata under `src/wujihandros2/.github/`.
- The driver bringup package resolves the hand model through the workspace package `src/wuji_description`, which contains the simplified first-generation Wuji hand description used here.

The upstream `src/wujihandros2/README.md` and `src/wujihandros2/build_deb.sh` are left unchanged for reference.

## Build

```bash
cd /home/ccs/ros2/teleop_ws
colcon build --symlink-install
source install/setup.bash
```

For zsh:

```bash
source install/setup.zsh
```

## Run

View the composed robot in RViz:

```bash
ros2 launch robot_description view_robot.launch.py
```

Regenerate the expanded URDF from xacro:

```bash
xacro src/robot_description/urdf/robot.xacro > src/robot_description/urdf/robot.urdf
```

Run the MuJoCo scene viewer and camera renderer:

```bash
python src/robot_description/mjcf/scene.py
```

Render only selected cameras:

```bash
python src/robot_description/mjcf/scene.py \
  --camera head_camera \
  --camera left_wrist_camera
```
