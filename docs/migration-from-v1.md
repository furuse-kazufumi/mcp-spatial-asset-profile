# Migration Guide: v1 → v2

**Status:** Working Draft  
**Date:** 2025-05

---

## Overview

This guide helps you migrate assets, SDKs, and MCP servers from MCP Spatial Asset Profile v1 (`mcp-3d`) to v2.

---

## Breaking Changes

| Change | v1 | v2 | Auto-migrated? |
|---|---|---|---|
| Version field | `"1.0"` | `"2.0"` | ✅ Yes |
| Asset identifier | `id` | `asset_id` | ✅ Yes |
| Coordinate reference | `crs` (top-level) | `spatial.frame` | ✅ Yes |
| Bounding box | `bounds` (top-level) | `spatial.bounds` | ✅ Yes |

All other v1 fields are preserved without change.

---

## Automated Migration

### Python SDK

```python
from spatial_asset_v2.codec import migrate_v1_to_v2
import json

# Load v1 asset
with open("old_asset_v1.json") as f:
    v1 = json.load(f)

# Migrate to v2
v2 = migrate_v1_to_v2(v1)

# Save
with open("new_asset_v2.json", "w") as f:
    json.dump(v2, f, indent=2)
```

### CLI

```bash
spatial-asset-v2 migrate old_asset_v1.json new_asset_v2.json
```

### TypeScript SDK

```typescript
import { migrateV1, parseAsset } from "spatial-asset-v2";

const v1 = JSON.parse(fs.readFileSync("old_asset_v1.json", "utf-8"));
const v2 = migrateV1(v1);
const asset = parseAsset(v2);
```

### Auto-migration on Parse

Both SDKs automatically detect and migrate v1 assets when parsing:

```python
# Python: decode_asset handles v1 automatically
from spatial_asset_v2.codec import decode_asset
asset = decode_asset(v1_dict)  # version "1.0" → migrated to "2.0"
```

```typescript
// TypeScript: parseAsset handles v1 automatically
const asset = parseAsset(v1Object);  // auto-migrated
```

---

## Step-by-Step Manual Migration

### Step 1: Bump version

```diff
- "version": "1.0",
+ "version": "2.0",
```

### Step 2: Rename `id` to `asset_id`

```diff
- "id": "some-id-or-null",
+ "asset_id": "urn:uuid:550e8400-e29b-41d4-a716-446655440001",
```

If no `id` was present, mint a new URN:
```bash
python -c "import uuid; print(f'urn:uuid:{uuid.uuid4()}')"
```

### Step 3: Move `crs` into `spatial`

```diff
- "crs": "local-ENU",
+ "spatial": {
+   "frame": "local-ENU",
+   "up_axis": "+Y",
+   "handedness": "right",
+   "unit": "m"
+ },
```

### Step 4: Move `bounds` into `spatial`

```diff
- "bounds": { "min": [-1, -1, -1], "max": [1, 1, 1] },
  "spatial": {
    "frame": "local-ENU",
+   "bounds": { "min": [-1, -1, -1], "max": [1, 1, 1] }
  },
```

### Step 5 (Optional): Add v2 enhancements

- Add `spatial.unit`, `spatial.up_axis`, `spatial.handedness` if not present
- Add `rep_id` to each representation for stable references
- Add `render_hints` for visualization guidance
- Add `workflow` if the asset was derived from another

---

## SDK Migration

### Python SDK: v1 `spatial_asset` → v2 `spatial_asset_v2`

| v1 module | v2 equivalent |
|---|---|
| `spatial_asset.encode_asset(path)` | `spatial_asset_v2.codec.encode_asset(asset)` |
| `spatial_asset.decode_asset(envelope)` | `spatial_asset_v2.codec.decode_asset(d)` |
| `spatial_asset.models.SpatialAsset` | `spatial_asset_v2.models.SpatialAsset` |
| n/a | `spatial_asset_v2.validators.validate_asset(d)` |
| n/a | `spatial_asset_v2.workflow.WorkflowMockRunner` |

### TypeScript SDK: v1 → v2

| v1 | v2 equivalent |
|---|---|
| `decoder.ts` decode functions | `parseAsset(raw)` in `parser/` |
| n/a | `validateAsset(raw)` in `validator/` |
| n/a | `selectRepresentation(asset, caps)` in `selector/` |
| n/a | `UriResolver` interface in `resolver/` |
| n/a | `ViewerAdapter` interface in `adapter/` |

---

## MCP Server Migration

If you have an existing `server.py` from mcp-3d v1:

1. Update the `version` returned in all asset envelopes from `"1.0"` to `"2.0"`.
2. Import from `spatial_asset_v2` instead of `spatial_asset`.
3. Add `workflow` block to any derived assets (rendered views, etc.).
4. Register the new tool names if desired: `render_asset`, `segment_2d`, etc.

The v1 `get_spatial_asset`, `list_spatial_assets`, `encode_asset`, `decode_asset` tool names remain backward compatible.

---

## Validation After Migration

```bash
# Validate a migrated asset
spatial-asset-v2 validate my_migrated_asset.json

# Expected output:
# [OK] my_migrated_asset.json — valid v2 asset
```
