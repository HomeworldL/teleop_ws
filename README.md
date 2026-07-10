# teleop_ws

ROS 2 workspace for the combined dual-arm, dual-hand robot description used by the teleoperation setup.

The main entry package is [`robot_description`](src/robot_description/README.md). It composes the robot from the resource description packages under `src/` and provides the final URDF, RViz launch files, and MuJoCo scene files.

## Packages

- `robot_description`: top-level composed robot model. It calls the arm, hand, and camera description resources, adds the shared base, adapters, final URDF, RViz config, and MJCF scene.
- `marvin_description`: independent resource package for the left and right Marvin M6-S arm URDFs and meshes.
- `wuji_description`: independent resource package for the left and right Wuji hand URDFs, meshes, and hand-only MJCF files.
- `realsense2_description`: independent resource package for RealSense camera xacro models and meshes.

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
