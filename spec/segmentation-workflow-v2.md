# MCP Spatial Asset Profile — Segmentation Workflow Extension v2

**Status:** Working Draft (PoC)  
**Date:** 2025-05  
**Extends:** MCP Spatial Asset Profile v2.0 (`spatial-asset-profile-v2.md`)  
**Authors:** MCP Spatial Asset Profile Working Group

---

## Table of Contents

1. [Introduction](#1-introduction)
2. [Scope](#2-scope)
3. [Design Goals](#3-design-goals)
4. [Terminology](#4-terminology)
5. [Relationship to Core v2](#5-relationship-to-core-v2)
6. [New Asset Kinds](#6-new-asset-kinds)
7. [Common Extension Fields](#7-common-extension-fields)
8. [Asset Definitions](#8-asset-definitions)
9. [Workflow Model](#9-workflow-model)
10. [Tool Interface Candidates](#10-tool-interface-candidates)
11. [Traceability Rules](#11-traceability-rules)
12. [Validation Rules](#12-validation-rules)
13. [Guidance for Coding Agents](#13-guidance-for-coding-agents)
14. [Core vs Experimental](#14-core-vs-experimental)

---

## 1. Introduction

This extension specifies how segmentation pipelines — whether run by human annotators, classical algorithms, or AI models — produce and reference spatial asset artifacts within the MCP Spatial Asset Profile v2 ecosystem.

The segmentation workflow typically proceeds:

```
Source Asset (point-cloud / mesh)
    │
    ▼
Rendered View(s)     ── viewpoint metadata ──▶ Viewpoint
    │
    ▼
2D Segmentation Mask ── references ──▶ Rendered View
    │
    ▼
3D Segmentation Mask ── lifted from ──▶ Source Asset + 2D Masks
    │
    ▼
Object Asset(s)      ── extracted from ──▶ 3D Segmentation Mask
```

Each step produces a distinct asset with its own `asset_id` and `derived_from` provenance, enabling full reconstruction of the pipeline from any leaf node.

---

## 2. Scope

This extension covers:

- Definition of four new asset kinds: `rendered-view`, `segmentation-mask-2d`, `segmentation-mask-3d`, `object-asset`.
- The `workflow` block added to all assets involved in a segmentation pipeline.
- Common extension fields for segmentation results: `confidence`, `label`, `correspondence`.
- The workflow graph model and ordering semantics.
- Tool interface candidates for MCP tools that produce or consume segmentation assets.
- Traceability rules and validation.

This extension does **not** cover:

- Specific segmentation algorithms or model architectures.
- Real-time streaming of segmentation results.
- Annotation UI or labeling toolchains.
- Multi-session or collaborative annotation workflows.

---

## 3. Design Goals

1. **Composability** — each workflow step produces a standalone asset that can be stored, versioned, and referenced independently.
2. **Traceability** — any `object-asset` can be traced back to its source `point-cloud` or `mesh` through the asset graph.
3. **Agnosticism** — the schema does not encode which model or algorithm produced a result; that is stored in `workflow.tool` and `workflow.parameters`.
4. **Incrementality** — pipeline stages can be run in any order; the schema supports partial pipelines (e.g., 2D masks without 3D lifting).
5. **Agent-friendliness** — field names and structures are chosen to be easy to emit by code-generating LLM agents with minimal context.

---

## 4. Terminology

| Term | Definition |
|---|---|
| **Rendered view** | An RGB or RGB-D image rendered from a specific viewpoint of a source 3D asset. |
| **Segmentation mask (2D)** | A pixel-level class or instance map aligned to a rendered view. |
| **Segmentation mask (3D)** | A per-point or per-face label array aligned to a source point cloud or mesh. |
| **Object asset** | A spatially bounded, labeled instance extracted from a 3D segmentation mask. |
| **Lifting** | The process of projecting 2D mask labels onto 3D geometry using depth and camera intrinsics. |
| **Correspondence** | An array of index mappings between a segmentation mask and its source asset. |
| **Workflow block** | The `workflow` JSON object present on segmentation-related assets. |
| **Pipeline** | An ordered sequence of workflow steps that transforms a source asset into derived assets. |

---

## 5. Relationship to Core v2

This extension depends on and extends the core v2 schema:

- All new kinds conform to the `asset.schema.json` top-level structure.
- The `workflow` block is an optional field in the core schema; this extension defines its content.
- `derived_from`, `target_asset_id`, `viewpoint_id`, `instance_id`, `confidence` are all defined as optional core fields; this extension specifies when they are required.
- Validators for segmentation assets use the base `asset.schema.json` with additional overlay schemas.

---

## 6. New Asset Kinds

### 6.1 `rendered-view`

An image rendered from a viewpoint of a source 3D asset.

**Required fields:**
- `asset_id`
- `kind: "rendered-view"`
- `representations` (format: `png`, `jpeg`, or `png-depth`)
- `workflow.target_asset_id` — the source asset this was rendered from
- `workflow.viewpoint_id` — the viewpoint used

**Optional fields:**
- `derived_from` — SHOULD include `target_asset_id`
- `viewpoints` — SHOULD include the viewpoint used

### 6.2 `segmentation-mask-2d`

A pixel-level segmentation mask corresponding to a rendered view.

**Required fields:**
- `asset_id`
- `kind: "segmentation-mask-2d"`
- `representations` (format: `png-mask`)
- `workflow.target_asset_id` — the `rendered-view` this mask annotates
- `workflow.viewpoint_id` — inherited from the rendered view

**Optional fields:**
- `workflow.labels` — array of `{id, name, color}` label definitions
- `workflow.confidence` — mean confidence score for mask predictions
- `workflow.tool` — tool that produced this mask

### 6.3 `segmentation-mask-3d`

Per-point or per-face labels on a 3D asset.

**Required fields:**
- `asset_id`
- `kind: "segmentation-mask-3d"`
- `representations` (format: `npy`, `npz`, or `json-pc`)
- `workflow.target_asset_id` — the point-cloud or mesh being labeled

**Optional fields:**
- `workflow.labels` — label definitions
- `workflow.source_masks` — array of `segmentation-mask-2d` asset IDs used for lifting
- `workflow.correspondence` — index mapping from this mask to the target asset
- `workflow.confidence` — per-point confidence array URI

### 6.4 `object-asset`

A spatially bounded, labeled object instance.

**Required fields:**
- `asset_id`
- `kind: "object-asset"`
- `representations` (any format appropriate for the object geometry)
- `workflow.target_asset_id` — the source asset this was extracted from
- `workflow.instance_id` — unique instance identifier within the source

**Optional fields:**
- `workflow.label` — semantic class label
- `workflow.confidence` — detection confidence score
- `spatial` — bounding box of the extracted object
- `derived_from` — SHOULD include both source asset and segmentation mask

---

## 7. Common Extension Fields

These fields appear in the `workflow` block of segmentation-related assets.

### 7.1 Workflow Block Structure

```jsonc
{
  "workflow": {
    "step": "segmentation-2d",
    "target_asset_id": "urn:uuid:...",
    "viewpoint_id": "vp-front",
    "instance_id": "obj-001",
    "label": "bunny",
    "confidence": 0.95,
    "tool": "sam2",
    "tool_version": "2.1.0",
    "parameters": {
      "threshold": 0.5,
      "prompt_type": "point"
    },
    "source_masks": ["urn:uuid:...", "urn:uuid:..."],
    "correspondence": "rep-corr-npy",
    "labels": [
      {"id": 0, "name": "background", "color": [0, 0, 0]},
      {"id": 1, "name": "bunny", "color": [255, 128, 0]}
    ],
    "started_at": "2025-05-01T09:00:00Z",
    "completed_at": "2025-05-01T09:01:00Z"
  }
}
```

| Field | Type | Description |
|---|---|---|
| `step` | string | Workflow step name (e.g., `"render"`, `"segmentation-2d"`, `"lift-3d"`, `"extract-object"`). |
| `target_asset_id` | string | The primary input asset's `asset_id`. |
| `viewpoint_id` | string | Viewpoint identifier (for 2D assets). |
| `instance_id` | string | Object instance ID within source (for `object-asset`). |
| `label` | string | Semantic class label string. |
| `confidence` | number [0,1] | Prediction confidence score. |
| `tool` | string | Name of the tool/model that produced this asset. |
| `tool_version` | string | Version string of the tool. |
| `parameters` | object | Tool parameters used (arbitrary key-value). |
| `source_masks` | array of string | `asset_id` values of 2D masks used for 3D lifting. |
| `correspondence` | string | `rep_id` of a representation containing the index correspondence array. |
| `labels` | array | Label definitions: `[{id: int, name: str, color: [r,g,b]}]`. |
| `started_at` | string (date-time) | Step start time. |
| `completed_at` | string (date-time) | Step completion time. |

---

## 8. Asset Definitions

### 8.1 Rendered View Asset

```json
{
  "version": "2.0",
  "asset_id": "urn:uuid:rv-001",
  "kind": "rendered-view",
  "name": "Bunny front view render",
  "derived_from": ["urn:uuid:bunny-pc-001"],
  "representations": [
    {
      "format": "png",
      "uri": "rendered_front.png",
      "image_width": 640,
      "image_height": 480,
      "viewpoint_id": "vp-front"
    }
  ],
  "viewpoints": [
    {
      "viewpoint_id": "vp-front",
      "position": [0.0, 0.09, 0.4],
      "target": [0.0, 0.09, 0.0],
      "up": [0.0, 1.0, 0.0],
      "fov_y_deg": 45.0
    }
  ],
  "workflow": {
    "step": "render",
    "target_asset_id": "urn:uuid:bunny-pc-001",
    "viewpoint_id": "vp-front",
    "tool": "matplotlib-scatter-render"
  }
}
```

### 8.2 2D Segmentation Mask Asset

```json
{
  "version": "2.0",
  "asset_id": "urn:uuid:mask2d-001",
  "kind": "segmentation-mask-2d",
  "name": "Bunny front view mask",
  "derived_from": ["urn:uuid:rv-001"],
  "representations": [
    {
      "format": "png-mask",
      "uri": "mask_front.png",
      "image_width": 640,
      "image_height": 480
    }
  ],
  "workflow": {
    "step": "segmentation-2d",
    "target_asset_id": "urn:uuid:rv-001",
    "viewpoint_id": "vp-front",
    "labels": [
      {"id": 0, "name": "background", "color": [0, 0, 0]},
      {"id": 1, "name": "bunny", "color": [255, 128, 0]}
    ],
    "confidence": 0.92,
    "tool": "mock-segmenter-v1"
  }
}
```

### 8.3 3D Segmentation Mask Asset

```json
{
  "version": "2.0",
  "asset_id": "urn:uuid:mask3d-001",
  "kind": "segmentation-mask-3d",
  "name": "Bunny 3D segmentation",
  "derived_from": ["urn:uuid:bunny-pc-001", "urn:uuid:mask2d-001"],
  "representations": [
    {
      "rep_id": "rep-labels-npy",
      "format": "npy",
      "uri": "bunny_labels.npy",
      "point_count": 35947
    }
  ],
  "workflow": {
    "step": "lift-3d",
    "target_asset_id": "urn:uuid:bunny-pc-001",
    "source_masks": ["urn:uuid:mask2d-001"],
    "labels": [
      {"id": 0, "name": "background", "color": [0, 0, 0]},
      {"id": 1, "name": "bunny", "color": [255, 128, 0]}
    ],
    "confidence": 0.88,
    "tool": "depth-projection-lifter-v1"
  }
}
```

### 8.4 Object Asset

```json
{
  "version": "2.0",
  "asset_id": "urn:uuid:obj-bunny-001",
  "kind": "object-asset",
  "name": "Extracted bunny object",
  "derived_from": ["urn:uuid:bunny-pc-001", "urn:uuid:mask3d-001"],
  "representations": [
    {
      "format": "ply",
      "uri": "bunny_object.ply",
      "point_count": 31204
    }
  ],
  "spatial": {
    "unit": "m",
    "bounds": {
      "min": [-0.094, 0.033, -0.061],
      "max": [0.086, 0.161,  0.065]
    }
  },
  "workflow": {
    "step": "extract-object",
    "target_asset_id": "urn:uuid:bunny-pc-001",
    "instance_id": "obj-bunny-001",
    "label": "bunny",
    "confidence": 0.91
  }
}
```

---

## 9. Workflow Model

### 9.1 Pipeline Steps

A segmentation pipeline is modeled as a directed acyclic graph (DAG) of assets. Each edge in the DAG corresponds to a `derived_from` relationship.

| Step name | Input kind(s) | Output kind | Workflow.step value |
|---|---|---|---|
| Render | `point-cloud`, `mesh`, `gaussian-splat` | `rendered-view` | `"render"` |
| Segment 2D | `rendered-view` | `segmentation-mask-2d` | `"segmentation-2d"` |
| Lift 3D | `point-cloud` + `segmentation-mask-2d` | `segmentation-mask-3d` | `"lift-3d"` |
| Extract | `point-cloud` + `segmentation-mask-3d` | `object-asset` | `"extract-object"` |

### 9.2 Multi-View Lifting

When multiple rendered views are available, a 3D mask MAY be derived from multiple 2D masks via view fusion. The `source_masks` array in the `workflow` block lists all contributing 2D masks.

### 9.3 Incremental Updates

Pipeline steps can be re-run independently. When a step is re-run, a new asset with a new `asset_id` SHOULD be created, preserving the original. The `derived_from` chain grows accordingly.

---

## 10. Tool Interface Candidates

The following MCP tool signatures are proposed for a segmentation workflow server:

### `render_asset`

```json
{
  "tool": "render_asset",
  "input": {
    "source_asset_id": "urn:uuid:...",
    "viewpoint": { "position": [...], "target": [...], "up": [...], "fov_y_deg": 45 },
    "image_width": 640,
    "image_height": 480
  },
  "output": "rendered-view asset JSON"
}
```

### `segment_2d`

```json
{
  "tool": "segment_2d",
  "input": {
    "rendered_view_asset_id": "urn:uuid:...",
    "prompt": { "type": "everything" }
  },
  "output": "segmentation-mask-2d asset JSON"
}
```

### `lift_to_3d`

```json
{
  "tool": "lift_to_3d",
  "input": {
    "source_asset_id": "urn:uuid:...",
    "mask_asset_ids": ["urn:uuid:..."],
    "strategy": "nearest-point"
  },
  "output": "segmentation-mask-3d asset JSON"
}
```

### `extract_object`

```json
{
  "tool": "extract_object",
  "input": {
    "source_asset_id": "urn:uuid:...",
    "mask_3d_asset_id": "urn:uuid:...",
    "label_id": 1
  },
  "output": "object-asset JSON"
}
```

### `get_asset_graph`

```json
{
  "tool": "get_asset_graph",
  "input": {
    "asset_id": "urn:uuid:...",
    "direction": "ancestors"
  },
  "output": "array of asset JSON objects"
}
```

---

## 11. Traceability Rules

### 11.1 Mandatory Traceability (MUST)

- Every `rendered-view` MUST declare `workflow.target_asset_id`.
- Every `segmentation-mask-2d` MUST declare `workflow.target_asset_id` pointing to a `rendered-view`.
- Every `segmentation-mask-3d` MUST declare `workflow.target_asset_id` pointing to a `point-cloud` or `mesh`.
- Every `object-asset` MUST declare `workflow.target_asset_id` and `workflow.instance_id`.
- `derived_from` SHOULD be populated for all of the above.

### 11.2 Traceability Validation

The Python SDK `validators.traceability` module provides `validate_pipeline(assets: list[dict])` which:

1. Builds an asset graph from `derived_from` and `workflow.target_asset_id` links.
2. Checks that every `rendered-view` can reach a source `point-cloud`, `mesh`, or `gaussian-splat`.
3. Checks that every `segmentation-mask-2d` can reach a `rendered-view`.
4. Checks that every `segmentation-mask-3d` can reach a source 3D asset.
5. Checks that every `object-asset` can reach both a source 3D asset and a `segmentation-mask-3d`.
6. Reports any broken links or cycles.

### 11.3 Asset Graph Completeness

A pipeline is considered **complete** if:
- All `asset_id` values referenced in `derived_from` and `workflow.*_asset_id` are present in the asset collection.
- There are no cycles in the `derived_from` graph.

A pipeline is **partial** if some referenced assets are missing. Partial pipelines are valid but SHOULD be flagged by validators.

---

## 12. Validation Rules

### 12.1 Schema Validation

All segmentation assets MUST validate against `asset.schema.json`. Each new kind has an additional overlay schema:

| Kind | Overlay schema |
|---|---|
| `rendered-view` | `rendered-view.schema.json` |
| `segmentation-mask-2d` | `segmentation-mask-2d.schema.json` |
| `segmentation-mask-3d` | `segmentation-mask-3d.schema.json` |
| `object-asset` | `object-asset.schema.json` |

### 12.2 Semantic Validation

Beyond JSON Schema, the traceability validator checks:

- `workflow.viewpoint_id` (if present) MUST match an entry in the asset's `viewpoints` array OR in the referenced `rendered-view` asset.
- `workflow.confidence` (if present) MUST be in `[0.0, 1.0]`.
- `workflow.labels[].id` values MUST be unique within a labels array.
- `workflow.labels[].color` MUST be an array of 3 integers in `[0, 255]`.

---

## 13. Guidance for Coding Agents

When an LLM coding agent emits segmentation workflow assets, it SHOULD:

1. **Always mint a fresh `asset_id`**: Use `uuid.uuid4()` or equivalent; never reuse IDs.
2. **Populate `derived_from` fully**: Include all direct parent asset IDs.
3. **Set `workflow.step`** to one of the registered values; use `"custom-<name>"` for non-standard steps.
4. **Set `workflow.target_asset_id`** even if it duplicates `derived_from[0]`; the two serve different purposes (semantic vs. graph edge).
5. **Include `spatial.bounds`** whenever geometry is extracted or subsetted.
6. **Do not hallucinate file contents**: URIs in representations point to real files; leave them as `"<placeholder>"` if the file has not been generated.
7. **Validate before emitting**: Use `sdk/python/spatial_asset_v2/validators/schema_validator.py validate_asset(asset_dict)`.
8. **Use ISO 8601** for all timestamps.
9. **Keep `metadata` flat**: Avoid deep nesting in `metadata`; prefer top-level optional fields.

---

## 14. Core vs Experimental

### 14.1 Core (stable in v2)

The following are considered stable v2 core features:

- `workflow` block structure and all fields defined in §7.
- The four new asset kinds: `rendered-view`, `segmentation-mask-2d`, `segmentation-mask-3d`, `object-asset`.
- Traceability rules in §11.
- Overlay schemas for all four kinds.

### 14.2 Experimental (subject to change)

The following are experimental and may change in future versions:

- `workflow.correspondence` — the format of the correspondence array is not yet standardized.
- Multi-view fusion strategy — the `source_masks` array semantics for view fusion need further specification.
- `workflow.parameters` — schema for tool-specific parameters is not yet standardized.
- The `get_asset_graph` tool interface — implementation details are tool-specific.

Implementations SHOULD treat experimental features as advisory and handle unknown or missing experimental fields gracefully.

---

*End of MCP Spatial Asset Profile — Segmentation Workflow Extension v2*
