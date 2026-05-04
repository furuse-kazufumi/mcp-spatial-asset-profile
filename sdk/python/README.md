# mcp-spatial-asset-profile — Python SDK

Reference Python SDK for the **[MCP Spatial Asset Profile v2](https://github.com/furuse-kazufumi/mcp-spatial-asset-profile)** — a JSON envelope format for 3D / spatial assets in Model Context Protocol (MCP) tool ecosystems.

- **Distribution name (PyPI):** [`mcp-spatial-asset-profile`](https://pypi.org/project/mcp-spatial-asset-profile/)
- **Import package:** `spatial_asset_v2`
- **TypeScript counterpart:** [`@furuse-kazufumi/mcp-spatial-asset-profile`](https://www.npmjs.com/package/@furuse-kazufumi/mcp-spatial-asset-profile)
- **Spec & repository:** <https://github.com/furuse-kazufumi/mcp-spatial-asset-profile>
- **Release tag:** [`v0.1.0-poc`](https://github.com/furuse-kazufumi/mcp-spatial-asset-profile/releases/tag/v0.1.0-poc)

> **Status — Proof of Concept.** The format is usable for prototyping and interoperability experiments. The wire format is not yet frozen; feedback via [GitHub Discussions](https://github.com/furuse-kazufumi/mcp-spatial-asset-profile/discussions) is explicitly welcome before v2.1.

## Installation

Once published to PyPI:

```bash
pip install mcp-spatial-asset-profile
# Optional: enable JSON Schema validation
pip install "mcp-spatial-asset-profile[validate]"
```

From source (this repository):

```bash
cd sdk/python
pip install -e ".[dev]"
```

## Quick Start

```python
from spatial_asset_v2.models import SpatialAsset, Representation, Spatial
from spatial_asset_v2.codec import encode_asset, decode_asset
from spatial_asset_v2.validators import validate_asset
from spatial_asset_v2.workflow import WorkflowMockRunner

# Create a v2 asset
asset = SpatialAsset(
    asset_id="urn:uuid:550e8400-e29b-41d4-a716-446655440001",
    kind="point-cloud",
    representations=[
        Representation(format="ply", uri="samples/bunny.ply", point_count=35947)
    ],
    spatial=Spatial(unit="m", up_axis="+Y"),
    name="Stanford Bunny",
)

# Encode to dict / JSON
d = encode_asset(asset)

# Decode from dict
asset2 = decode_asset(d)

# Validate against JSON schema (requires jsonschema)
errors = validate_asset(d)
print("Valid:", len(errors) == 0)

# Run mock segmentation workflow
runner = WorkflowMockRunner(base_dir="samples/inspection")
pipeline = runner.run_full_pipeline(
    source_asset_id="urn:uuid:...",
    source_ply_path="bunny_full.ply"
)
```

## Modules

| Module | Description |
|---|---|
| `spatial_asset_v2.models` | Pydantic-free dataclass models for all asset kinds |
| `spatial_asset_v2.codec` | Encoder / decoder (dict ↔ model) |
| `spatial_asset_v2.validators.schema_validator` | JSON Schema validation (optional dep) |
| `spatial_asset_v2.validators.traceability` | Asset graph traceability validation |
| `spatial_asset_v2.workflow` | Mock workflow runner for pipeline testing |
| `spatial_asset_v2.samples` | Sample asset generator |
| `spatial_asset_v2.cli` | Command-line interface |

## CLI

```bash
# Validate a JSON asset file
spatial-asset-v2 validate spec/examples/pointcloud-asset.json

# Generate sample assets
spatial-asset-v2 generate --output /tmp/samples

# Run mock segmentation pipeline
spatial-asset-v2 workflow --source spec/examples/pointcloud-asset.json

# Migrate v1 asset to v2
spatial-asset-v2 migrate old-asset-v1.json new-asset-v2.json
```

## Running Tests

```bash
cd sdk/python
pip install -e ".[dev]"
pytest tests/ -v
```

## License

MIT — see the [LICENSE](https://github.com/furuse-kazufumi/mcp-spatial-asset-profile/blob/main/LICENSE) file at the repository root.
