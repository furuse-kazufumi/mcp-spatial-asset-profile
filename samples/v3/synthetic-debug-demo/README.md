# Synthetic Debug Demo — Layer 1

Reference fixture for the v3 profile. Two virtual event cameras observe one point object moving in a straight line.

## Scene geometry

- **cam0**: at world origin, facing +Z
- **cam1**: 0.5 m baseline in +X, facing +Z
- **obj0**: linear path from `[-0.5, 0, 3]` to `[0.5, 0, 3]` over 1 second
- Resolution: 346 × 260 px (DVS346 class), `fx = fy = 200`, `cx = 173`, `cy = 130`

## Analytical projections (verification reference)

| t (us)   | cam0 x_px   | cam1 x_px   |
|----------|-------------|-------------|
| 0        | 139.667     | 106.333     |
| 250 000  | 156.333     | 123.000     |
| 500 000  | 173.000     | 139.667     |
| 750 000  | 189.667     | 156.333     |
| 1 000 000| 206.333     | 173.000     |

y_px = 130.0 (constant, horizontal motion only)

## Files

```
config/
  cameras.json          # intrinsics / extrinsics / time offsets (validates against cameras.schema.json)
  scene.json            # trajectories / duration / seed (validates against scene.schema.json)
assertions/
  ground-truth.json     # analytical ground truth (validates against ground-truth.schema.json)
expected/               # populated by: python -m spatial_asset_v3.demos.synthetic ... (Layer 1 impl)
```

## Key constants for implementation

- `T_world_cam` follows **T_target_source** convention: transforms a point from camera frame to world frame
- `time_offset_us = 0` (synchronised cameras, nominal case)
- Acceptance criteria: position error ≤ 0.01 m RMS, reprojection error ≤ 1.0 px
