# MCP Spatial Asset Profile — Version 2.0

**Status:** Working Draft (PoC)  
**Date:** 2025-05  
**Supersedes:** MCP Spatial Asset Profile v1.0 (mcp-3d)  
**Authors:** MCP Spatial Asset Profile Working Group

---

## Table of Contents

1. [Introduction](#1-introduction)
2. [Goals and Non-goals](#2-goals-and-non-goals)
3. [Terminology](#3-terminology)
4. [Asset Model](#4-asset-model)
5. [Representation Model](#5-representation-model)
6. [Spatial Metadata](#6-spatial-metadata)
7. [Viewpoints and Camera Metadata](#7-viewpoints-and-camera-metadata)
8. [Render Hints](#8-render-hints)
9. [URI and Capability Negotiation](#9-uri-and-capability-negotiation)
10. [Kind Definitions](#10-kind-definitions)
11. [Validation Rules](#11-validation-rules)
12. [Backward Compatibility](#12-backward-compatibility)
13. [Security Considerations](#13-security-considerations)
14. [Future Extensions](#14-future-extensions)

---

## 1. Introduction

The **MCP Spatial Asset Profile** defines a JSON-based envelope for representing 3D and spatial data assets in Model Context Protocol (MCP) tool ecosystems. Version 2.0 extends the v1.0 core schema with:

- A richer asset model with globally stable `asset_id` and asset graph traceability (`derived_from`, `target_asset_id`)
- First-class support for segmentation and annotation workflows via new asset kinds
- Viewpoints and camera metadata for rendered-view assets
- Render hints to drive client-side rendering pipelines
- URI capability negotiation for heterogeneous client populations
- A formal `spatial` block (coordinate frame, axis convention, units, bounds)
- Instance-level extensions for object-asset relationships

The profile is format-agnostic: it wraps any number of *representations* (PLY, glTF, Gaussian Splat `.splat`, PNG depth, etc.) with a uniform envelope that agents, tools, and storage backends can parse without knowledge of the underlying binary formats.

### 1.1 Relationship to v1

v2 is a strict superset of v1 in intent. Existing v1 assets remain valid under v2 parsers with minor field renames (see [Backward Compatibility](#12-backward-compatibility)). The `version` field is bumped from `"1.0"` to `"2.0"`.

### 1.2 Relationship to Segmentation Workflow Extension

The segmentation workflow is specified in a companion document: `segmentation-workflow-v2.md`. That extension introduces `rendered-view`, `segmentation-mask-2d`, `segmentation-mask-3d`, and `object-asset` kinds, all of which reference the core v2 schema.

---

## 2. Goals and Non-goals

### 2.1 Goals

- **Interoperability** — a single JSON envelope that any MCP-aware tool can parse to discover, select, and fetch a spatial asset.
- **Evolvability** — additive versioning; new fields are optional and ignored by older parsers.
- **Traceability** — every derived asset carries provenance (`derived_from`) back to its source.
- **Capability negotiation** — clients advertise capabilities; servers return appropriate representations.
- **Minimal dependencies** — the envelope is pure JSON; binary payloads live outside.
- **Language neutrality** — SDK implementations exist for Python and TypeScript; others are welcome.

### 2.2 Non-goals

- Real-time streaming protocols or chunked transfer (out of scope; see future extensions).
- Geometry compression codecs (envelope references URIs; compression is a representation concern).
- Scene graph hierarchies or multi-actor world state (consider MCP Scene Profile).
- Deep learning inference APIs (segmentation *results* are wrapped; models are not described).
- Rasterization pipelines or shader specifications.

---

## 3. Terminology

| Term | Definition |
|---|---|
| **Asset** | A logical spatial data entity described by one top-level JSON object conforming to this profile. |
| **asset_id** | A globally stable URI or UUID-URN identifying an asset across storage systems. |
| **Representation** | One concrete encoding of an asset (e.g., a PLY file). An asset carries 1..N representations. |
| **Kind** | The semantic type of an asset (e.g., `point-cloud`, `mesh`). Governs which fields are required. |
| **Spatial block** | The `spatial` field containing coordinate frame, axis, handedness, unit, and bounds. |
| **Viewpoint** | A camera position/orientation descriptor associated with a rendered-view or annotation. |
| **Render hint** | Guidance to the client renderer (point size, opacity, LOD policy, etc.). |
| **Capability token** | A short string (e.g., `"splat-render"`) that a client declares to unlock certain representations. |
| **derived_from** | Array of `asset_id` values that are direct parents in the asset provenance graph. |
| **Traceability** | The ability to reconstruct the full derivation chain of any asset. |
| **MCP** | Model Context Protocol — the tool-call protocol used to exchange assets between agents and tools. |

---

## 4. Asset Model

### 4.1 Top-level Object

```jsonc
{
  "$schema": "https://mcp-spatial/spec/v2/asset.schema.json",
  "version": "2.0",
  "asset_id": "urn:uuid:550e8400-e29b-41d4-a716-446655440000",
  "kind": "point-cloud",
  "name": "Stanford Bunny — full resolution",
  "created_at": "2025-05-01T09:00:00Z",
  "representations": [...],
  "spatial": {...},
  "viewpoints": [...],
  "render_hints": {...},
  "workflow": {...},
  "derived_from": [],
  "metadata": {}
}
```

#### Required fields

| Field | Type | Description |
|---|---|---|
| `version` | `"2.0"` | Profile schema version. Must be exactly `"2.0"`. |
| `asset_id` | string | Stable identifier. SHOULD be a URN (UUID or domain-specific). |
| `kind` | string enum | Asset kind (see §10). |
| `representations` | array (≥1) | Concrete data representations. |

#### Optional fields

| Field | Type | Description |
|---|---|---|
| `name` | string | Human-readable label. |
| `created_at` | string (date-time) | ISO 8601 creation timestamp. |
| `spatial` | object | Coordinate frame and bounds (see §6). |
| `viewpoints` | array | Camera positions (see §7). |
| `render_hints` | object | Renderer guidance (see §8). |
| `workflow` | object | Workflow metadata (see segmentation extension). |
| `derived_from` | array of string | Parent `asset_id` values. |
| `metadata` | object | Arbitrary domain key-value pairs. |

### 4.2 Asset Identity

`asset_id` MUST be globally unique. Recommended schemes:

- `urn:uuid:<UUID-v4>` — for locally generated assets
- `https://<domain>/assets/<id>` — for server-managed assets
- `mcp-spatial://<namespace>/<local-id>` — for MCP ecosystem assets

If omitted (legacy), a receiving tool SHOULD mint a new `asset_id` on first encounter.

---

## 5. Representation Model

Each representation describes one concrete encoding of the asset's data.

### 5.1 Representation Object

```jsonc
{
  "rep_id": "rep-ply-full",
  "format": "ply",
  "uri": "samples/inspection/bunny_full.ply",
  "mime_type": "application/x-ply",
  "size_bytes": 8124304,
  "sha256": "a3f...",
  "lod": 0,
  "point_count": 35947,
  "channels": ["x", "y", "z", "nx", "ny", "nz"],
  "capabilities_required": [],
  "encoding": "binary-little-endian"
}
```

#### Required fields

| Field | Type | Description |
|---|---|---|
| `format` | string enum | File format (see §5.2). |
| `uri` | string | Relative path or absolute URI. |

#### Optional fields

| Field | Type | Description |
|---|---|---|
| `rep_id` | string | Stable identifier for this representation within the asset. |
| `mime_type` | string | IANA media type. |
| `size_bytes` | integer | File size in bytes. |
| `sha256` | string | Hex SHA-256 digest for integrity verification. |
| `lod` | integer (≥0) | Level-of-detail index; 0 = full resolution. |
| `point_count` | integer | Number of points (point-cloud, gaussian-splat). |
| `face_count` | integer | Number of faces (mesh). |
| `channels` | array of string | Named data channels present in this representation. |
| `capabilities_required` | array of string | Capability tokens the client must declare. |
| `encoding` | string | Binary encoding hint (e.g., `"binary-little-endian"`, `"ascii"`). |
| `depth_scale` | number | Meters-per-unit for depth images (e.g., `0.001` for mm). |
| `depth_unit` | string | Human-readable unit label (`"mm"`, `"m"`, `"cm"`). |
| `image_width` | integer | Width in pixels (depth-image, rendered-view). |
| `image_height` | integer | Height in pixels (depth-image, rendered-view). |
| `viewpoint_id` | string | Reference to a viewpoint in `viewpoints[]` (rendered-view). |
| `instance_id` | string | Object instance identifier (object-asset). |

### 5.2 Supported Formats

| `format` | MIME type | Description |
|---|---|---|
| `ply` | `application/x-ply` | Polygon File Format (ASCII or binary) |
| `pcd` | `application/x-pcd` | Point Cloud Data (PCL format) |
| `las` | `application/x-las` | LAS point cloud |
| `laz` | `application/x-laz` | Compressed LAS |
| `obj` | `model/obj` | Wavefront OBJ mesh |
| `gltf` | `model/gltf+json` | GL Transmission Format |
| `glb` | `model/gltf-binary` | Binary glTF |
| `splat` | `application/x-gaussian-splat` | 3D Gaussian Splat (inria format) |
| `png-depth` | `image/png` | 16-bit depth map |
| `png-mask` | `image/png` | Segmentation mask (8/16-bit indexed) |
| `npy` | `application/x-npy` | NumPy binary array |
| `npz` | `application/x-npz` | NumPy compressed archive |
| `json-pc` | `application/json` | JSON-encoded point cloud (for small assets) |

---

## 6. Spatial Metadata

The `spatial` block standardizes coordinate conventions so tools can interoperate without guessing.

### 6.1 Spatial Object

```jsonc
{
  "frame": "local-ENU",
  "up_axis": "+Y",
  "handedness": "right",
  "unit": "m",
  "bounds": {
    "min": [-0.094, 0.033, -0.061],
    "max": [0.086, 0.161,  0.065]
  }
}
```

| Field | Type | Values / Description |
|---|---|---|
| `frame` | string | Coordinate reference: `"local-ENU"`, `"local-NED"`, `"ECEF"`, `"camera"`, `"EPSG:<code>"`, etc. |
| `up_axis` | string | `"+Y"` (default, OpenGL/glTF), `"+Z"` (engineering/ROS), `"-Y"` |
| `handedness` | string | `"right"` (default) or `"left"` |
| `unit` | string | `"m"` (default), `"mm"`, `"cm"`, `"ft"`, `"in"` |
| `bounds` | object | Axis-aligned bounding box with `min: [x,y,z]` and `max: [x,y,z]` |

All spatial fields are optional. A tool that cannot determine the coordinate frame SHOULD omit `spatial` rather than guess.

---

## 7. Viewpoints and Camera Metadata

Viewpoints describe camera positions for rendered views or annotation context.

### 7.1 Viewpoint Object

```jsonc
{
  "viewpoint_id": "vp-front",
  "label": "Front view",
  "position": [0.0, 0.0, 1.0],
  "target":   [0.0, 0.0, 0.0],
  "up":       [0.0, 1.0, 0.0],
  "fov_y_deg": 45.0,
  "near": 0.01,
  "far": 100.0,
  "image_width": 640,
  "image_height": 480,
  "intrinsics": {
    "fx": 525.0, "fy": 525.0,
    "cx": 319.5, "cy": 239.5
  },
  "extrinsics": {
    "rotation": [[1,0,0],[0,1,0],[0,0,1]],
    "translation": [0.0, 0.0, 1.0]
  }
}
```

| Field | Type | Description |
|---|---|---|
| `viewpoint_id` | string | Stable identifier referenced by representation `viewpoint_id`. |
| `label` | string | Human-readable label. |
| `position` | [x,y,z] | Camera origin in asset coordinate frame. |
| `target` | [x,y,z] | Look-at point. |
| `up` | [x,y,z] | Up vector (defaults to `spatial.up_axis`). |
| `fov_y_deg` | number | Vertical field of view in degrees. |
| `near` / `far` | number | Clipping planes. |
| `image_width` / `image_height` | integer | Render resolution. |
| `intrinsics` | object | Pinhole camera intrinsics (`fx`, `fy`, `cx`, `cy`, `k1`…). |
| `extrinsics` | object | World-to-camera rotation matrix and translation vector. |

---

## 8. Render Hints

Render hints guide client-side visualization without mandating any specific renderer.

### 8.1 Render Hints Object

```jsonc
{
  "point_size": 2.0,
  "opacity": 1.0,
  "color_mode": "rgb",
  "lod_policy": "screen-space-error",
  "background_color": [0.1, 0.1, 0.1],
  "show_bounding_box": false,
  "preferred_representation": "rep-ply-full"
}
```

| Field | Type | Description |
|---|---|---|
| `point_size` | number | Default point radius in pixels. |
| `opacity` | number (0–1) | Global opacity. |
| `color_mode` | string | `"rgb"`, `"intensity"`, `"classification"`, `"normal"`, `"height"` |
| `lod_policy` | string | `"none"`, `"screen-space-error"`, `"distance"` |
| `background_color` | [r,g,b] | Normalized RGB background color. |
| `show_bounding_box` | boolean | Whether to render the bounds wireframe. |
| `preferred_representation` | string | `rep_id` of the preferred representation for initial display. |

---

## 9. URI and Capability Negotiation

### 9.1 Client Capability Declaration

When requesting an asset, clients SHOULD include a `capabilities` array in the MCP tool call parameters:

```json
{
  "tool": "get_spatial_asset",
  "asset_id": "urn:uuid:...",
  "capabilities": ["splat-render", "webgpu", "lod-streaming"]
}
```

### 9.2 Server Selection

The server SHOULD filter `representations` to those whose `capabilities_required` is a subset of the declared capabilities, then sort by:

1. Highest resolution that fits the declared capability set
2. Preferred format for the capability (e.g., `splat` for `splat-render`)
3. Smallest file size for bandwidth-constrained clients

### 9.3 Registered Capability Tokens

| Token | Meaning |
|---|---|
| `splat-render` | Client can render 3D Gaussian Splats. |
| `mesh-render` | Client can render polygon meshes. |
| `webgpu` | Client has WebGPU support. |
| `webgl2` | Client has WebGL2 support. |
| `lod-streaming` | Client supports incremental LOD loading. |
| `lidar-las` | Client can parse LAS/LAZ files. |
| `depth-rgb-d` | Client can process RGB-D depth images. |
| `segmentation-mask` | Client can overlay segmentation masks. |

Implementors MAY define additional tokens using a `x-<vendor>-<name>` convention.

---

## 10. Kind Definitions

### 10.1 Core Kinds

#### `point-cloud`

A set of 3D points, optionally with per-point attributes (color, intensity, normal, etc.).

Required in `representations`: at least one representation with `format` in `{ply, pcd, las, laz, npy, npz, json-pc}`.

#### `mesh`

A polygonal surface mesh with vertices and face indices.

Required in `representations`: at least one representation with `format` in `{obj, gltf, glb, ply}`.

#### `gaussian-splat`

A 3D Gaussian Splatting scene representation.

Required in `representations`: at least one representation with `format` in `{splat, ply}`.

Additional representation fields: `point_count` (number of Gaussians), `channels` (MUST include `{x,y,z,opacity,scale_0..2,rot_0..3,f_dc_0..2}`).

#### `depth-image`

A 2D depth map encoded as a single-channel PNG (16-bit) or NumPy array.

Required in `representations`: at least one with `format` in `{png-depth, npy}`.
Required representation fields: `depth_scale`, `image_width`, `image_height`.

### 10.2 Extended Kinds (v2 addition)

The following kinds are defined in `segmentation-workflow-v2.md`:

| Kind | Description |
|---|---|
| `rendered-view` | RGB or RGB-D render from a specific viewpoint. References source asset and viewpoint. |
| `segmentation-mask-2d` | 2D pixel-level segmentation mask referencing a `rendered-view`. |
| `segmentation-mask-3d` | 3D point-level segmentation labeling a `point-cloud` or `mesh`. |
| `object-asset` | A segmented object instance extracted from a source asset. |

---

## 11. Validation Rules

### 11.1 Mandatory Rules (MUST)

- `version` MUST be `"2.0"`.
- `asset_id` MUST be non-empty string.
- `kind` MUST be one of the registered kind values.
- `representations` MUST contain at least one entry.
- Each representation MUST have `format` and `uri`.
- `format` MUST be one of the registered format values or start with `x-`.
- `sha256`, if present, MUST match the pattern `^[0-9a-f]{64}$`.
- `depth_scale`, if present, MUST be strictly positive.
- A `rendered-view` asset MUST have `target_asset_id` in its `workflow` block.
- A `segmentation-mask-2d` asset MUST have both `target_asset_id` and `viewpoint_id`.
- A `segmentation-mask-3d` asset MUST have `target_asset_id`.
- A `object-asset` MUST have `target_asset_id` and `instance_id`.
- `confidence`, if present, MUST be in `[0.0, 1.0]`.

### 11.2 Recommendation Rules (SHOULD)

- `asset_id` SHOULD be a URN.
- `spatial.frame` SHOULD be specified for outdoor/geospatial assets.
- `spatial.unit` SHOULD always be specified.
- `spatial.bounds` SHOULD be present for assets larger than 1 MB.
- `derived_from` SHOULD be populated for any non-primary asset.
- `viewpoints` SHOULD be populated for `rendered-view` assets.
- `sha256` SHOULD be included for assets shared across systems.
- `created_at` SHOULD be an ISO 8601 timestamp.

### 11.3 Extensibility Rules

- Unrecognized fields at the top level or within `metadata` MUST be silently ignored by parsers.
- Fields prefixed `x-` are private extensions and MUST NOT be interpreted by core validators.

---

## 12. Backward Compatibility

### 12.1 v1 → v2 Field Mapping

| v1 field | v2 equivalent | Notes |
|---|---|---|
| `version: "1.0"` | `version: "2.0"` | Bump required for v2 schema. |
| `id` | `asset_id` | Renamed for clarity. |
| `crs` | `spatial.frame` | Moved into spatial block. |
| `bounds` | `spatial.bounds` | Moved into spatial block. |
| `kind: "depth-image"` | `kind: "depth-image"` | Unchanged. |
| `representations[].format` | `representations[].format` | Unchanged. |
| `representations[].lod` | `representations[].lod` | Unchanged. |
| `representations[].depth_scale` | `representations[].depth_scale` | Unchanged. |

### 12.2 Migration Procedure

1. Set `version` to `"2.0"`.
2. Rename `id` → `asset_id` (or add `asset_id` if absent).
3. Move `crs` and `bounds` into a new `spatial` block.
4. Optionally add `spatial.up_axis`, `spatial.handedness`, `spatial.unit`.
5. Optionally add `asset_id` to each representation as `rep_id`.

A migration utility is provided in `sdk/python/spatial_asset_v2/codec/migrate.py`.

### 12.3 Parser Behavior for v1 Assets

v2 parsers encountering `version: "1.0"` SHOULD:
- Treat `id` as `asset_id`.
- Treat top-level `crs` as `spatial.frame`.
- Treat top-level `bounds` as `spatial.bounds`.
- Treat `kind: "depth-image"` as equivalent.

---

## 13. Security Considerations

### 13.1 URI Safety

- `uri` fields in representations MUST be validated before any I/O operation.
- Relative URIs are resolved against the base URI of the asset manifest.
- Path traversal attacks (e.g., `../../etc/passwd`) MUST be rejected by parsers.
- Remote URIs (http/https) SHOULD only be fetched with explicit user consent.

### 13.2 Integrity Verification

- When `sha256` is present, consumers SHOULD verify the digest before processing binary data.
- Assets transmitted over untrusted channels SHOULD always include `sha256`.

### 13.3 Schema Validation

- Parsers SHOULD validate incoming asset JSON against the published schema before processing.
- Maliciously large `representations` arrays or deeply nested `metadata` objects SHOULD be bounded.

### 13.4 Capability Tokens

- Capability tokens are advisory. A client MUST NOT grant elevated permissions based solely on capability tokens.
- Server-side filtering by capability is a UX affordance, not a security boundary.

### 13.5 Sensitive Data

- Asset metadata MAY contain personal or sensitive information (GPS coordinates, facility layouts).
- Implementors MUST apply appropriate access control at the storage and API layer.

---

## 14. Future Extensions

### 14.1 Streaming and Chunked Transfer

Future versions may define a streaming representation type for progressive loading of large point clouds and Gaussian Splat scenes over WebSockets or gRPC.

### 14.2 Scene Graph Profile

A companion *MCP Scene Profile* may define multi-asset scene graphs with hierarchical transforms.

### 14.3 Semantic Taxonomy

A shared semantic label taxonomy (object categories, material types) would enable richer cross-dataset queries and segmentation result interoperability.

### 14.4 Versioned Asset History

An `asset_history` array in the top-level object would allow compact representation of the full lineage chain without external resolution.

### 14.5 Geospatial Integration

Integration with OGC standards (3D Tiles, GeoJSON, CityGML) for large-scale outdoor scenes.

### 14.6 Encryption and DRM

End-to-end encryption of representation payloads with key exchange via MCP capability negotiation.

---

*End of MCP Spatial Asset Profile v2.0 Specification*
