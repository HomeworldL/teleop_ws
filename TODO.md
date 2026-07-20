# TODO

Short-term engineering tasks for the teleoperation workspace.

## Marvin Impedance Tuning

- Tune Marvin joint impedance parameters for live teleoperation.
- Compare `marvin_impedance.launch.py` behavior against position mode and
  `marvin_impedance_pd.launch.py`.
- Record tested `joint_impedance_k`, `joint_impedance_d`, velocity ratio, and
  acceleration ratio values.
- Keep parameter changes in YAML only unless controller persistence is
  explicitly required.

## Vive-to-Marvin Static Transforms

- Test `src/teleop_algorithm/vive_marvin_teleop/config/static_transforms.yaml`
  with the real three-tracker setup:
  `chest`, `left_wrist`, and `right_wrist`.
- Validate `right_chest -> tianji_right` and `left_chest -> tianji_left` in
  RViz before enabling real arm commands.
- Tune chest alignment and `wrist_to_tianji` rotations until the SDK TCP target
  matches the operator wrist intent.
- Document the final tracker mounting direction and calibrated transforms.

## URDF-Based Arm Teleoperation IK

- Design a second Marvin arm teleoperation solver that uses the workspace URDF
  model instead of the Tianji SDK IK wrapper.
- Define the exact base and TCP frames for each arm, for example `Base_L` /
  `Base_R` to a flange or tool frame, and document how those frames relate to
  `tianji_left` and `tianji_right`.
- Choose and test an IK backend that can consume URDF models, such as Pinocchio
  plus a numerical IK loop or another ROS-compatible kinematics library.
- Compare URDF IK output against the current SDK IK path using the same
  `left_chest -> tianji_left` and `right_chest -> tianji_right` targets.
- Add command limiting, joint-limit handling, singularity behavior, and
  diagnostics before allowing real hardware command publication.

## Whole-Teleop Visualization

- Add unified RViz presets for full hand + arm teleoperation.
- Visualize commanded targets, tracker frames, robot feedback, and global
  `/joint_states` in one view.
- Make command-state mismatch visible for both Marvin arms and Wuji hands.
- Keep hardware bringup visualization and teleoperation visualization consistent.

## Performance Tests

- Measure end-to-end latency for glove-to-hand and Vive-to-arm command paths.
- Measure topic rates and jitter for tracker poses, glove keypoints, feedback,
  and command topics.
- Measure CPU load during full teleoperation, including IK, retargeting, TF, and
  RViz.
- Record test conditions, hardware mode, publish rates, and observed bottlenecks.
