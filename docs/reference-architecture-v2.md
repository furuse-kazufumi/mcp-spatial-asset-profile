# Reference Architecture — MCP Spatial Asset Profile v2

**Status:** Working Draft  
**Date:** 2025-05

---

## 1. Overview

This document describes the reference architecture for deploying MCP Spatial Asset Profile v2 within an MCP tool ecosystem.

---

## 2. Component Diagram

```
┌─────────────────────────────────────────────────────┐
│  LLM Agent (Claude, GPT, etc.)                      │
│                                                     │
│  "Segment the bunny into foreground/background"     │
└──────────────────────┬──────────────────────────────┘
                       │ MCP tool calls
                       ▼
┌─────────────────────────────────────────────────────┐
│  MCP Server  (server.py / server.ts)                │
│                                                     │
│  Tools:                                             │
│    get_asset(asset_id, capabilities=[...])          │
│    render_asset(source_id, viewpoint)               │
│    segment_2d(rendered_view_id, prompt)             │
│    lift_to_3d(source_id, mask_ids)                  │
│    extract_object(source_id, mask_3d_id, label_id)  │
│    get_asset_graph(asset_id, direction)             │
└───────────┬───────────────┬───────────┬────────────┘
            │               │           │
            ▼               ▼           ▼
┌───────────────┐  ┌───────────────┐  ┌─────────────┐
│ Asset Store   │  │ Geometry      │  │ Segmentation│
│               │  │ Pipeline      │  │ Backend     │
│ JSON registry │  │               │  │ (optional)  │
│ + file store  │  │ PLY/NPY/OBJ   │  │             │
│               │  │ processing    │  │ SAM2, etc.  │
└───────────────┘  └───────────────┘  └─────────────┘
```

---

## 3. Asset Lifecycle

```
1. INGEST
   User uploads PLY / OBJ / splat file
   → Server creates SpatialAsset v2 JSON envelope
   → Assigns asset_id, computes SHA-256, detects bounds

2. DISCOVER
   Agent calls get_asset(asset_id, capabilities=["splat-render"])
   → Server filters representations by capability
   → Returns asset envelope with matching representations

3. RENDER (segmentation workflow only)
   Agent calls render_asset(source_id, viewpoint={...})
   → Server produces rendered-view asset
   → Returns rendered-view envelope with PNG URI

4. SEGMENT 2D
   Agent calls segment_2d(rendered_view_id, prompt={...})
   → Segmentation backend produces mask PNG
   → Server wraps in segmentation-mask-2d asset
   → Returns mask envelope with derived_from=[rendered_view_id]

5. LIFT TO 3D
   Agent calls lift_to_3d(source_id, mask_ids=[...])
   → Server projects 2D masks onto 3D geometry
   → Produces segmentation-mask-3d asset

6. EXTRACT OBJECT
   Agent calls extract_object(source_id, mask_3d_id, label_id=1)
   → Server filters points by label
   → Produces object-asset with own bounds and asset_id

7. QUERY GRAPH
   Agent calls get_asset_graph(object_asset_id, direction="ancestors")
   → Server traverses derived_from links
   → Returns full provenance chain
```

---

## 4. Data Flow: Segmentation Pipeline

```
bunny_full.ply  (point-cloud, urn:uuid:src)
      │
      │ render_asset(vp-front)
      ▼
rendered_front.png  (rendered-view, urn:uuid:rv)
      │
      │ segment_2d(everything prompt)
      ▼
mask_front.png  (segmentation-mask-2d, urn:uuid:m2d)
      │
      │ lift_to_3d(src, [m2d])
      ▼
bunny_labels.npy  (segmentation-mask-3d, urn:uuid:m3d)
      │
      │ extract_object(src, m3d, label_id=1)
      ▼
bunny_object.ply  (object-asset, urn:uuid:obj)
```

---

## 5. Deployment Topologies

### 5.1 Local Desktop (PoC / Development)

```
Claude Desktop ─MCP─▶ server.py (Python)
                            │
                     local filesystem
                     (samples/, out/)
```

### 5.2 Containerized Service

```
MCP Client ─HTTP+MCP─▶ Docker container
                            │ spatialasset-v2:latest
                      volume mount / S3 URI
```

### 5.3 Serverless / Edge

```
Agent ─▶ MCP Gateway ─▶ Lambda/Functions
                              │
                         S3 / R2 (assets)
                         DynamoDB (asset graph)
```

---

## 6. Security Boundaries

| Boundary | Enforcement |
|---|---|
| URI path traversal | Server validates all URIs before file I/O |
| SHA-256 integrity | Verified before processing binary payloads |
| Capability tokens | Advisory only; not a security boundary |
| Asset access control | External to this spec (IAM/API keys) |

---

## 7. Performance Considerations

- **Large point clouds**: Use `lod` representations; serve LOD-1 (downsampled) for initial display, LOD-0 on demand.
- **Gaussian Splat**: `splat` format is more compact than PLY; always include as alternative representation.
- **Segmentation masks**: NPZ (compressed NumPy) is preferred over NPY for label arrays > 1 MB.
- **Asset graph traversal**: For deep pipelines (>10 steps), cache the graph in a flat index rather than resolving `derived_from` recursively.
