# MCP Spatial Asset Profile v2

**Status:** Proof of Concept  
**Version:** 2.0.0  
**Built on:** [mcp-3d v1](https://github.com/puruyan2525/mcp-3d) (Claude Code, April 2025)

---

## Overview

**MCP Spatial Asset Profile v2** is a JSON-based envelope format for representing 3D and spatial data assets in [Model Context Protocol (MCP)](https://modelcontextprotocol.io/) tool ecosystems.

v2 extends the v1 core (`mcp-3d`) with:

- Globally stable `asset_id` (URN-based)
- First-class segmentation workflow (`rendered-view`, `segmentation-mask-2d`, `segmentation-mask-3d`, `object-asset`)
- Formal `spatial` block (coordinate frame, axis, handedness, unit, bounds)
- Viewpoints and camera intrinsics/extrinsics
- URI capability negotiation
- Full asset graph traceability (`derived_from`, `workflow.target_asset_id`)

---

## Repository Structure

```
mcp-spatial-asset-profile/
├── README.md
├── LICENSE
├── spec/
│   ├── spatial-asset-profile-v2.md       ← Core v2 specification
│   ├── segmentation-workflow-v2.md        ← Segmentation workflow extension
│   ├── schema/
│   │   ├── asset.schema.json              ← Master schema (Draft 2020-12)
│   │   ├── representation.schema.json
│   │   ├── viewpoint.schema.json
│   │   ├── rendered-view.schema.json
│   │   ├── segmentation-mask-2d.schema.json
│   │   ├── segmentation-mask-3d.schema.json
│   │   └── object-asset.schema.json
│   └── examples/
│       ├── pointcloud-asset.json
│       ├── mesh-asset.json
│       ├── gaussian-splat-asset.json
│       ├── rendered-view.json
│       ├── segmentation-mask-2d.json
│       ├── segmentation-mask-3d.json
│       └── object-asset.json
├── sdk/
│   ├── python/                            ← Python SDK (spatial-asset-v2)
│   │   ├── pyproject.toml
│   │   ├── README.md
│   │   ├── spatial_asset_v2/
│   │   │   ├── models/                    ← Dataclass models
│   │   │   ├── codec/                     ← Encoder / decoder / migrate
│   │   │   ├── validators/                ← Schema + traceability validators
│   │   │   ├── workflow/                  ← Mock workflow runner
│   │   │   ├── samples/                   ← Sample asset generator
│   │   │   └── cli/                       ← CLI entry point
│   │   └── tests/
│   └── typescript/                        ← TypeScript SDK (spatial-asset-v2)
│       ├── package.json
│       ├── tsconfig.json
│       └── src/
│           ├── types/                     ← Type definitions
│           ├── parser/                    ← JSON → typed asset
│           ├── selector/                  ← Capability-aware representation selector
│           ├── resolver/                  ← URI resolver interface
│           ├── adapter/                   ← Viewer adapter interface
│           ├── validator/                 ← Structural validator
│           └── tests/
├── samples/
│   ├── inspection/                        ← Stanford Bunny samples (from v1)
│   ├── lidar/                             ← LiDAR depth samples (from v1)
│   └── gaussian-splat/                    ← Gaussian splat samples (from v1)
├── tests/
│   ├── schema/                            ← JSON schema validation tests
│   ├── interoperability/                  ← Cross-SDK tests
│   └── roundtrip/                         ← Encode/decode roundtrip tests
└── docs/
    ├── implementation-plan-v2.md
    ├── reference-architecture-v2.md
    ├── migration-from-v1.md
    ├── publication-plan-v2.md
    └── slides-v2.md
```

---

## Quick Start

### Python SDK

```bash
cd sdk/python
pip install -e ".[dev]"

# Validate an example asset
python -m spatial_asset_v2.cli.main validate ../../spec/examples/pointcloud-asset.json

# Generate sample assets
python -m spatial_asset_v2.cli.main generate --output /tmp/samples

# Run mock segmentation pipeline
python -m spatial_asset_v2.cli.main workflow \
  --source ../../spec/examples/pointcloud-asset.json \
  --output /tmp/pipeline

# Run tests
pytest tests/ -v
```

### TypeScript SDK

```bash
cd sdk/typescript
npm install
npm run build
npm test
```

---

## Asset Kinds

| Kind | Description |
|---|---|
| `point-cloud` | 3D point set (PLY, PCD, LAS, NPY) |
| `mesh` | Polygonal surface mesh (OBJ, glTF, GLB) |
| `gaussian-splat` | 3D Gaussian Splatting scene |
| `depth-image` | 2D depth map (16-bit PNG) |
| `rendered-view` | RGB/RGB-D render from a viewpoint *(v2 new)* |
| `segmentation-mask-2d` | Pixel-level segmentation mask *(v2 new)* |
| `segmentation-mask-3d` | Per-point/face 3D labels *(v2 new)* |
| `object-asset` | Extracted segmented object instance *(v2 new)* |

---

## Segmentation Workflow

```
Source (point-cloud/mesh)
    ↓ render
Rendered View
    ↓ segment_2d
Segmentation Mask 2D
    ↓ lift_3d
Segmentation Mask 3D
    ↓ extract_object
Object Asset
```

Each step is a separate v2 asset with full `derived_from` + `workflow.target_asset_id` provenance.

---

## Backward Compatibility with v1

v2 is a strict superset of v1. Breaking changes:

| Change | Migration |
|---|---|
| `id` → `asset_id` | Rename field |
| `crs` → `spatial.frame` | Move into `spatial` block |
| `bounds` → `spatial.bounds` | Move into `spatial` block |
| `version: "1.0"` → `"2.0"` | Bump version string |

Both SDKs auto-migrate v1 assets on parse.

---

## License

MIT — see [LICENSE](LICENSE).

---

## Provenance

This project builds on **mcp-3d v1** created by [@puruyan2525](https://github.com/puruyan2525) using Claude Code (Anthropic), April 2025. v2 extends the v1 core with segmentation workflow, richer spatial metadata, and SDK improvements.
