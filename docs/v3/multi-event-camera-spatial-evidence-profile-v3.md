# MCP Spatial Asset Profile — Multi-Event-Camera Spatial Evidence Extension (v3 Draft)

**Status:** Early Draft / RFC — *Concept exploration, not normative*
**Date:** 2026-05
**Extends (additively):** MCP Spatial Asset Profile v2.0 (`spec/spatial-asset-profile-v2.md`) and the Segmentation Workflow Extension v2 (`spec/segmentation-workflow-v2.md`)
**Audience:** GitHub Discussion / RFC review
**Authors:** MCP Spatial Asset Profile Working Group (initial draft prepared for Kazufumi Furuse)

> ⚠️ **Experimental.** This document is a *concept and design draft* for v3. Nothing here is normative. Field names, asset kinds, and tool interfaces are placeholders intended to seed discussion. Do not implement against this draft without further review. Sections explicitly marked **(experimental)** are particularly unstable.

---

## Table of Contents

1. [Introduction](#1-introduction)
2. [Status and Scope](#2-status-and-scope)
3. [Rationale](#3-rationale)
4. [Relationship to v2](#4-relationship-to-v2)
5. [Goals and Non-goals](#5-goals-and-non-goals)
6. [Terminology](#6-terminology)
7. [New Asset Kinds (v3)](#7-new-asset-kinds-v3)
8. [Core Data Model Snippets](#8-core-data-model-snippets)
9. [Multi-Camera Calibration and Time Synchronization Model](#9-multi-camera-calibration-and-time-synchronization-model)
10. [Traceability and Correspondence Model](#10-traceability-and-correspondence-model)
11. [Uncertainty Model](#11-uncertainty-model)
12. [VLLM Integration Model](#12-vllm-integration-model)
13. [Candidate MCP Tools](#13-candidate-mcp-tools)
14. [PoC Demo Plan](#14-poc-demo-plan)
15. [Public Dataset Candidates](#15-public-dataset-candidates)
16. [Open Questions](#16-open-questions)
17. [Implementation Milestones](#17-implementation-milestones)
18. [Appendix A — Worked Example (Sketch)](#18-appendix-a--worked-example-sketch)

---

## 1. Introduction

The MCP Spatial Asset Profile v2 already covers static-scene 3D and spatial assets (point clouds, meshes, Gaussian splats, depth images, rendered views, segmentation masks, and extracted object assets). Real-world perception pipelines — particularly those involving event-based cameras, fast motion, robotic manipulation, autonomous driving, and high-speed industrial inspection — generate a different category of evidence: **asynchronous, time-resolved, multi-view motion observations**.

This v3 draft proposes an *additive* extension that introduces asset kinds and metadata for **multi-event-camera spatial and motion evidence**. The aim is to let an MCP-aware agent reason about *what moved, where, when, seen by which camera, with what uncertainty* — and to let downstream tools (including VLLMs) consume compact, well-traceable summaries of those observations.

This draft assumes some familiarity with event cameras (DVS / DAVIS / Prophesee sensors), multi-view geometry (intrinsics, extrinsics, fundamental/essential matrices, triangulation), and time synchronization concepts (PTP / hardware trigger / TSC offset).

---

## 2. Status and Scope

**Status:** Working concept draft. Not a release candidate. Not part of the published v2 spec.

**In scope (this document):**

- Conceptual data model for event-camera-derived motion evidence as MCP spatial assets.
- Multi-camera calibration & synchronization metadata sufficient for cross-view correspondence and triangulation.
- Provenance / traceability rules linking 2D event clusters → 2D tracklets → multi-view correspondences → 3D tracklets → motion evidence.
- VLLM-readable textual / JSON summaries of motion evidence.
- Candidate MCP tool interfaces.
- PoC demo flow on public datasets.

**Out of scope (deliberately deferred):**

- Frozen schemas (JSON Schema files) — to be drafted only after the model stabilizes.
- Specific event-processing algorithms (SAE/SAEN, time-surface networks, EV-FlowNet, ESVO, etc.) — referenced as context only.
- Real-time wire protocols and chunked event streaming — see §16.
- Sensor fusion with frame-based RGB / IMU / LiDAR beyond what is needed for time alignment (a future v3.x topic).
- Storage formats for raw event payloads (HDF5 / AEDAT / RAW2 / RAW3) — these are payloads behind URIs, exactly as v2 treats PLY/glTF.

---

## 3. Rationale

Event cameras report per-pixel asynchronous brightness changes with microsecond-scale latency and very high temporal resolution. They are a poor fit for the v2 model in three ways:

1. **No global frame timestamp.** v2 assets implicitly assume a single "asset capture time"; event data has continuous time per pixel.
2. **No image-grid raster.** Event payloads are sparse 4-tuples `(x, y, t, polarity)`, not dense images. v2 has no canonical place to record this.
3. **Multi-view evidence is first-class.** A single 3D motion event is typically inferred from *several* event cameras simultaneously; v2's `viewpoints` array describes static cameras for rendered views, not synchronized multi-sensor capture rigs.

v3 closes those gaps additively. v2 assets remain valid; v3 adds new `kind` values and new top-level blocks (`capture_rig`, `time_base`, `motion_evidence`) that older parsers can ignore.

The motivating use cases include:

- **Industrial inspection / high-speed lines.** Multi-view event cameras observing a moving part for defect localization at sub-millisecond resolution.
- **Robot vision.** Hand-eye calibrated multi-camera rigs tracking grasped objects and end-effector motion.
- **Autonomous driving research.** Cross-checking event-based detections across stereo or quad event setups (DSEC, M3ED, MVSEC).
- **Scientific motion capture.** Tracking insects, droplets, or fast biological motion where frame-based capture is infeasible.

---

## 4. Relationship to v2

v3 is **strictly additive** with respect to v2:

- All v2 asset kinds remain valid. A v3-aware tool MUST accept v2 assets unchanged.
- `version` is bumped from `"2.0"` to `"3.0"` only on assets that use v3-only fields. v2 assets keep `"2.0"`.
- v3 introduces new `kind` values (see §7). v2 parsers will reject these — this is acceptable because v3-only assets are produced by v3-aware pipelines.
- The v2 segmentation workflow (rendered-view → seg-2d → seg-3d → object-asset) is unchanged and can be combined with v3 motion evidence (e.g., an `object-asset` may be referenced as the *what* of a `motion-evidence-3d` asset).
- The v2 `derived_from` provenance graph is reused; v3 only adds new node types into the same graph.

```
                   v2 segmentation graph (unchanged)
                   ┌────────────────────────────────────────────┐
                   │ point-cloud → rendered-view → seg-2d → ... │
                   └────────────────────────────────────────────┘

                              v3 additive layer
   event-stream-2d ─┐
                    ├─▶ event-cluster-2d ─▶ event-tracklet-2d ─┐
                    │                                          │
                    │                            multi-view-correspondence
                    │                                          │
                    │                                          ▼
                    │                                event-tracklet-3d
                    │                                          │
                    │                                          ▼
                    │                                  motion-evidence-3d ──▶ vllm-summary
                    ▼
              capture-rig (calibration + sync metadata)
```

---

## 5. Goals and Non-goals

### 5.1 Goals

- **Additivity** — never break v2.
- **Traceability** — every 3D tracklet can be traced back to the contributing 2D event clusters and to the calibration/sync metadata used to fuse them.
- **Calibration honesty** — calibration provenance (who calibrated, when, residuals) is part of the asset, not implicit.
- **Time honesty** — every temporal claim is qualified by a clock domain and an estimated offset/uncertainty.
- **Uncertainty as a first-class field** — covariances and confidence are not optional addenda; they live on the same object as the estimate.
- **VLLM consumability** — every motion evidence asset can be summarized into a short, structured, deterministic text/JSON record suitable for a VLLM tool input.
- **PoC viability** — the model must be demonstrable end-to-end on at least one public dataset with open-source tooling.

### 5.2 Non-goals

- A new event-camera *file format*. Existing formats (HDF5, AEDAT4, RAW3, ROS bags) are referenced via URIs.
- Replacing SLAM / VIO / event-based feature trackers. v3 wraps their *output*, not their internals.
- Specifying which detector or tracker to use.
- Realtime streaming / pub-sub semantics.
- Encoding raw IMU or RGB streams (only minimal cross-modality time alignment is in scope).

---

## 6. Terminology

| Term | Definition |
|---|---|
| **Event** | A 4-tuple `(x, y, t, p)` reported by an event camera: pixel coordinates, timestamp, polarity. |
| **Event stream** | A time-ordered sequence of events from a single sensor over a time window. |
| **Event cluster (2D)** | A spatially / temporally compact group of events on one sensor, treated as a candidate observation of a single moving entity at one short time slice. |
| **Event tracklet (2D)** | A time-ordered chain of 2D event clusters from one sensor representing a hypothesized single object's motion in image space. |
| **Multi-view correspondence** | A linkage between 2D tracklets (or clusters) on different sensors that are hypothesized to image the same physical entity at the same time. |
| **Event tracklet (3D)** | A time-resolved 3D trajectory inferred by triangulating multi-view correspondences. |
| **Motion evidence** | A summary asset that interprets one or more 3D tracklets as evidence of a higher-level motion event (e.g., "object X moved from A to B between t0 and t1"). |
| **Capture rig** | The set of synchronized event cameras (and optionally other sensors) with shared calibration and time base. |
| **Time base** | The reference clock domain and synchronization model used by a rig. |
| **Sync offset** | Per-sensor clock offset (with uncertainty) relative to the rig's time base. |
| **VLLM summary** | A compact, structured, human/agent-readable description derived deterministically from a v3 asset, intended for consumption by a vision-language LLM tool call. |

---

## 7. New Asset Kinds (v3)

All kinds below are **experimental** in this draft. Names may change.

| Kind (`kind` value) | Description |
|---|---|
| `event-stream-2d` | Sparse 2D event stream from one event camera over a time window. Wraps an external event payload (HDF5/AEDAT/RAW3/etc.). |
| `event-cluster-2d` | A single 2D spatiotemporal cluster of events on one sensor. |
| `event-tracklet-2d` | An ordered chain of `event-cluster-2d` from one sensor. |
| `multi-view-correspondence` | A hypothesized cross-sensor linkage between 2D clusters/tracklets. |
| `event-tracklet-3d` | A 3D trajectory triangulated from one or more `multi-view-correspondence` assets. |
| `motion-evidence-3d` | An interpretation asset summarizing one or more 3D tracklets as a motion event. |
| `capture-rig` | A description of a multi-sensor rig: per-sensor calibration, time base, and synchronization metadata. |
| `vllm-summary` | A textual/structured summary asset derived from a v3 evidence asset, formatted for VLLM tool input. |

A v3-aware tool advertising consumption of these kinds via the v2 capability negotiation mechanism is encouraged to declare the capability tokens `event-2d`, `event-3d`, `multi-view-rig`, and `vllm-summary` (final names TBD).

---

## 8. Core Data Model Snippets

> All snippets below are **non-normative sketches**. They are intentionally close to v2 conventions (envelope, `representations`, `derived_from`, `workflow`). Field names with a `?` suffix are tentative.

### 8.1 `event-stream-2d`

```jsonc
{
  "$schema": "https://mcp-spatial/spec/v3/asset.schema.json",
  "version": "3.0",
  "asset_id": "urn:uuid:c0ffee00-...-stream-cam-left",
  "kind": "event-stream-2d",
  "name": "DSEC zurich_city_04 — left event camera, 0.0–2.0 s",
  "created_at": "2026-05-04T10:00:00Z",
  "rig_id": "urn:uuid:...-rig-dsec-zurich-city-04",
  "sensor_id": "cam_event_left",
  "time_window": {
    "t_start_ns": 0,
    "t_end_ns": 2000000000,
    "time_base": "rig:tb-main"
  },
  "image_size": { "width": 640, "height": 480 },
  "event_count": 1843221,
  "representations": [
    {
      "rep_id": "rep-h5",
      "format": "h5-events",                    // experimental format token
      "uri": "samples/v3/dsec/left_events_0_2s.h5",
      "mime_type": "application/x-hdf5",
      "channels": ["x", "y", "t", "p"],
      "encoding": "h5-uint32-uint64-int8",
      "capabilities_required": ["event-2d"]
    }
  ],
  "derived_from": []
}
```

### 8.2 `event-cluster-2d` and `event-tracklet-2d`

```jsonc
{
  "version": "3.0",
  "asset_id": "urn:uuid:...-cluster-001",
  "kind": "event-cluster-2d",
  "sensor_id": "cam_event_left",
  "rig_id": "urn:uuid:...-rig-dsec-zurich-city-04",
  "time_window": { "t_start_ns": 12_500_000, "t_end_ns": 13_000_000, "time_base": "rig:tb-main" },
  "centroid_px": [312.4, 188.7],
  "extent_px":   { "u_sigma": 4.1, "v_sigma": 3.7 },
  "event_count": 412,
  "polarity_balance": 0.18,                     // (#pos - #neg) / total, range [-1,1]
  "confidence": 0.74,
  "label?": "vehicle",                           // optional, may come from a 2D classifier
  "derived_from": ["urn:uuid:...-stream-cam-left"]
}
```

```jsonc
{
  "version": "3.0",
  "asset_id": "urn:uuid:...-tracklet-2d-007",
  "kind": "event-tracklet-2d",
  "sensor_id": "cam_event_left",
  "rig_id": "urn:uuid:...-rig-dsec-zurich-city-04",
  "cluster_ids": [
    "urn:uuid:...-cluster-001",
    "urn:uuid:...-cluster-002",
    "urn:uuid:...-cluster-003"
  ],
  "time_window": { "t_start_ns": 12_500_000, "t_end_ns": 38_000_000, "time_base": "rig:tb-main" },
  "image_trajectory_summary?": {
     "polyline_px": [[312.4,188.7],[318.1,190.2],[325.0,191.6]],
     "speed_px_per_s_mean": 142.3,
     "speed_px_per_s_std":   31.0
  },
  "confidence": 0.69,
  "derived_from": ["urn:uuid:...-stream-cam-left"]
}
```

### 8.3 `multi-view-correspondence` and `event-tracklet-3d`

```jsonc
{
  "version": "3.0",
  "asset_id": "urn:uuid:...-mvc-014",
  "kind": "multi-view-correspondence",
  "rig_id": "urn:uuid:...-rig-dsec-zurich-city-04",
  "members": [
    { "sensor_id": "cam_event_left",  "tracklet_2d_id": "urn:uuid:...-tracklet-2d-007" },
    { "sensor_id": "cam_event_right", "tracklet_2d_id": "urn:uuid:...-tracklet-2d-019" }
  ],
  "association_method": "epipolar+temporal-window",
  "epipolar_residual_px": { "mean": 0.91, "p95": 2.4 },
  "time_residual_ns":     { "mean": 320,  "p95": 1100 },
  "confidence": 0.81,
  "derived_from": [
    "urn:uuid:...-tracklet-2d-007",
    "urn:uuid:...-tracklet-2d-019",
    "urn:uuid:...-rig-dsec-zurich-city-04"
  ]
}
```

```jsonc
{
  "version": "3.0",
  "asset_id": "urn:uuid:...-tracklet-3d-003",
  "kind": "event-tracklet-3d",
  "rig_id": "urn:uuid:...-rig-dsec-zurich-city-04",
  "spatial": {
    "frame": "rig",                              // see §9
    "up_axis": "+Z",
    "handedness": "right",
    "unit": "m"
  },
  "samples": [
    { "t_ns": 12_500_000, "p_xyz": [3.10,  0.02, 1.42], "cov_xyz": [0.012,0.011,0.034], "src_correspondence_id": "urn:uuid:...-mvc-014" },
    { "t_ns": 18_000_000, "p_xyz": [3.18,  0.05, 1.40], "cov_xyz": [0.013,0.011,0.036], "src_correspondence_id": "urn:uuid:...-mvc-014" },
    { "t_ns": 24_000_000, "p_xyz": [3.27,  0.09, 1.38], "cov_xyz": [0.015,0.012,0.039], "src_correspondence_id": "urn:uuid:...-mvc-014" }
  ],
  "kinematics_summary?": {
     "v_mean_mps": [1.45, 0.05, -0.02],
     "v_std_mps":  [0.08, 0.04,  0.05]
  },
  "confidence": 0.78,
  "derived_from": ["urn:uuid:...-mvc-014"]
}
```

### 8.4 `motion-evidence-3d`

```jsonc
{
  "version": "3.0",
  "asset_id": "urn:uuid:...-motion-evidence-042",
  "kind": "motion-evidence-3d",
  "rig_id": "urn:uuid:...-rig-dsec-zurich-city-04",
  "subject?": {
     "object_asset_id?": "urn:uuid:...-object-bike-12",   // link into v2 object-asset graph if known
     "label?":           "bicycle"
  },
  "time_window": { "t_start_ns": 12_500_000, "t_end_ns": 38_000_000, "time_base": "rig:tb-main" },
  "spatial_summary": {
     "frame": "rig",
     "p_start_xyz": [3.10, 0.02, 1.42],
     "p_end_xyz":   [3.27, 0.09, 1.38],
     "displacement_m": 0.179,
     "speed_mps_mean": 1.44,
     "trajectory_bounds_m": { "min": [3.08, 0.00, 1.36], "max": [3.30, 0.10, 1.43] }
  },
  "evidence": {
     "tracklet_3d_ids":     ["urn:uuid:...-tracklet-3d-003"],
     "supporting_views":    ["cam_event_left", "cam_event_right"],
     "calibration_id":      "urn:uuid:...-rig-dsec-zurich-city-04#calib-2026-01-12",
     "time_base":           "rig:tb-main"
  },
  "confidence": 0.78,
  "derived_from": ["urn:uuid:...-tracklet-3d-003"]
}
```

---

## 9. Multi-Camera Calibration and Time Synchronization Model

A `capture-rig` asset carries the calibration and sync metadata that all other v3 evidence references. This is intentionally separated from the evidence so that re-calibration produces a *new* `capture-rig` asset id and the provenance graph makes the relationship explicit.

### 9.1 `capture-rig` sketch

```jsonc
{
  "version": "3.0",
  "asset_id": "urn:uuid:...-rig-dsec-zurich-city-04",
  "kind": "capture-rig",
  "rig_label": "DSEC vehicle stereo event rig",
  "rig_frame": {
     "name":       "rig",
     "definition": "left event camera optical center, +Z forward, +X right, +Y down (TBD per dataset)"
  },
  "sensors": [
     {
        "sensor_id":    "cam_event_left",
        "modality":     "event",
        "vendor_model": "Prophesee Gen3",
        "image_size":   { "width": 640, "height": 480 },
        "intrinsics": {
           "model":      "pinhole-radtan",
           "fx": 558.7, "fy": 558.6, "cx": 320.5, "cy": 240.3,
           "distortion": [-0.31, 0.12, 0.00, 0.00, 0.0]
        },
        "extrinsics_T_rig_sensor": {            // rig ← sensor SE(3)
           "R": [[1,0,0],[0,1,0],[0,0,1]],
           "t_m": [0.0, 0.0, 0.0]
        },
        "calibration_residuals": { "reproj_px_rms": 0.34 },
        "time_offset": { "t_offset_ns": 0,      "t_offset_sigma_ns": 50,  "method": "hardware-trigger" }
     },
     {
        "sensor_id":    "cam_event_right",
        "modality":     "event",
        "vendor_model": "Prophesee Gen3",
        "image_size":   { "width": 640, "height": 480 },
        "intrinsics":   { "model": "pinhole-radtan", "fx": 559.0, "fy": 559.0, "cx": 321.0, "cy": 239.8, "distortion": [-0.30, 0.11, 0.0, 0.0, 0.0] },
        "extrinsics_T_rig_sensor": {
           "R": [[1,0,0],[0,1,0],[0,0,1]],
           "t_m": [0.51, 0.0, 0.0]               // 51 cm baseline along +X
        },
        "calibration_residuals": { "reproj_px_rms": 0.41 },
        "time_offset": { "t_offset_ns": -180,    "t_offset_sigma_ns": 70,  "method": "hardware-trigger" }
     }
  ],
  "time_base": {
     "id":              "rig:tb-main",
     "epoch":           "rig-start",
     "unit":            "ns",
     "sync_method":     "hardware-trigger",     // or "ptp" | "tsc-cross-correlation" | "audio-clap"
     "estimated_jitter_ns": 80
  },
  "calibration_provenance": {
     "calibrated_by":   "Kalibr 2024.1",
     "calibrated_at":   "2026-01-12T15:00:00Z",
     "input_sequence?": "samples/v3/calib_zurich_city_04.h5",
     "notes":           "Stereo event-camera calibration via blinking-LED checkerboard."
  }
}
```

### 9.2 Coordinate frames

- `world`, `rig`, `sensor:<id>` — transformations are SE(3) and always written `T_target_source` (target ← source). This convention should be stated in the spec so that downstream tools never guess.
- `event-tracklet-3d.spatial.frame` SHOULD be one of `rig`, `world`, or a registered project-specific frame; if `world`, a `T_world_rig` MUST be discoverable from the `capture-rig` or a separate registration asset.

### 9.3 Time synchronization

Every timestamp in v3 is in **nanoseconds** within a named **time base**. A v3 asset that carries timestamps without naming a `time_base` is malformed. Sync methods explicitly tracked:

| `sync_method` | Typical jitter | Notes |
|---|---|---|
| `hardware-trigger` | 10s of ns | Shared trigger line; preferred for stereo event rigs. |
| `ptp` | ~1 µs | IEEE-1588; good for distributed rigs. |
| `tsc-cross-correlation` | µs–ms | Post-hoc alignment using shared visual events. |
| `audio-clap` | ms | Last resort; useful for ad-hoc multi-camera shoots. |
| `nominal` | unknown | Strongly discouraged; only for sanity-check experiments. |

`time_offset.t_offset_sigma_ns` is **required** so consumers can decide whether a candidate cross-view correspondence is temporally plausible.

---

## 10. Traceability and Correspondence Model

The v2 `derived_from` convention is reused. For v3 evidence assets, the following invariants are intended (subject to refinement):

1. Every `event-cluster-2d` MUST list at least one `event-stream-2d` as a parent.
2. Every `event-tracklet-2d` MUST be reconstructible from its `cluster_ids` (or from one or more `event-stream-2d` parents if clusters are not materialized as separate assets).
3. Every `multi-view-correspondence` MUST list both (a) all 2D tracklets/clusters it associates and (b) the `capture-rig` whose calibration it relied on.
4. Every `event-tracklet-3d` MUST list at least one `multi-view-correspondence` as a parent and inherit its `rig_id`.
5. Every `motion-evidence-3d` MUST list at least one `event-tracklet-3d` as a parent.
6. The `capture-rig` referenced by any v3 evidence asset is **frozen at use time**: editing calibration creates a new `capture-rig` `asset_id`. This keeps evidence reproducible.
7. Cross-version: a v3 `motion-evidence-3d` MAY reference a v2 `object-asset` via `subject.object_asset_id` to bind motion evidence to a known segmented object.

---

## 11. Uncertainty Model

Uncertainty is intentionally surfaced at every layer:

- **2D level:** cluster `extent_px` (Gaussian σ in pixels) and per-cluster `confidence ∈ [0,1]`.
- **Correspondence level:** epipolar residual statistics (`mean`, `p95`) in pixels; temporal residual statistics in nanoseconds.
- **3D level:** per-sample diagonal covariance `cov_xyz` (m²) on each `event-tracklet-3d.samples[*]`. A future revision may allow full 3×3 covariances.
- **Evidence level:** an aggregate scalar `confidence`, plus the *option* to attach a `confidence_breakdown` block citing the limiting factor (calibration residual, time jitter, association ambiguity).

Tools producing v3 assets are strongly encouraged to *under-report* confidence rather than overstate it; downstream VLLM summaries should preserve the numerical values verbatim.

---

## 12. VLLM Integration Model

Vision-language LLMs are increasingly used as the reasoning layer over perception outputs. v3 standardizes how an evidence asset is rendered into a VLLM-friendly summary so the LLM does not need to parse raw event tensors.

### 12.1 `vllm-summary` sketch

```jsonc
{
  "version": "3.0",
  "asset_id": "urn:uuid:...-vllm-summary-019",
  "kind": "vllm-summary",
  "subject_asset_id": "urn:uuid:...-motion-evidence-042",
  "summary_text": "Between t=12.5 ms and t=38.0 ms (rig clock tb-main), one moving object — labeled 'bicycle' with confidence 0.78 — was triangulated by the left and right event cameras. It traveled from (3.10, 0.02, 1.42) m to (3.27, 0.09, 1.38) m in the rig frame, a displacement of 0.179 m, at a mean speed of 1.44 m/s. Calibration residual: 0.91 px (mean, epipolar). Time-sync jitter estimate: 80 ns.",
  "summary_struct": {
     "subject":       "bicycle (conf 0.78)",
     "time_window_ms": [12.5, 38.0],
     "frame":         "rig",
     "displacement_m": 0.179,
     "speed_mps":     1.44,
     "confidence":    0.78,
     "limiting_factor?": "association_ambiguity"
  },
  "render_policy": {
     "deterministic": true,
     "template_id":   "motion-evidence-3d/v3.0/default-en",
     "language":      "en"
  },
  "derived_from": ["urn:uuid:...-motion-evidence-042"]
}
```

### 12.2 Rendering rules (experimental)

- Summaries MUST be **deterministic** functions of the source asset under a named `template_id`. No LLM-in-the-loop generation at this stage; otherwise the summary loses provenance value.
- Numerical values MUST be quoted at full precision in `summary_struct`; `summary_text` may round for readability but MUST not invent numbers absent from the source.
- A summary MUST cite its `subject_asset_id` and is itself a normal v2-style asset with `derived_from` populated.
- VLLM tool calls SHOULD pass `summary_text` as the human-facing context and `summary_struct` as the machine-readable parameters.

---

## 13. Candidate MCP Tools

The v2 segmentation extension already lists tool-interface candidates. v3 proposes the following additions (all **experimental** — names may change):

| Tool name (proposed) | Input | Output | Purpose |
|---|---|---|---|
| `events.window` | `event-stream-2d` + time window | `event-stream-2d` (sliced) | Slice an event stream into a smaller asset. |
| `events.cluster_2d` | `event-stream-2d` | `event-cluster-2d[]` | Detect compact spatiotemporal clusters. |
| `events.track_2d` | `event-cluster-2d[]` | `event-tracklet-2d[]` | Link clusters into per-sensor tracklets. |
| `mvc.associate` | `event-tracklet-2d[]` from ≥2 sensors + `capture-rig` | `multi-view-correspondence[]` | Cross-sensor association via epipolar + temporal gating. |
| `mvc.triangulate` | `multi-view-correspondence` + `capture-rig` | `event-tracklet-3d` | Triangulate associated tracklets into 3D. |
| `motion.summarize` | `event-tracklet-3d[]` (+ optional `object-asset`) | `motion-evidence-3d` | Aggregate 3D tracklets into a labeled motion event. |
| `vllm.render_summary` | any v3 evidence asset | `vllm-summary` | Deterministic textual+structured summary. |
| `rig.calibrate` | raw calibration sequence URI | `capture-rig` | Wrap an external calibration tool's output. |
| `rig.validate` | `capture-rig` + held-out sequence | report | Sanity-check residuals. |

These should be exposed via MCP tool descriptors that advertise the v2/v3 capability tokens they require.

---

## 14. PoC Demo Plan

The PoC aims to demonstrate the end-to-end v3 flow with the smallest possible code path, using only public datasets and open-source tooling.

### 14.1 Scenario A — Stereo event triangulation on DSEC (recommended first PoC)

**Goal:** Take ~2 seconds of a DSEC sequence, run a simple 2D event clustering + tracking on each camera, associate via the published calibration, triangulate, and emit a `motion-evidence-3d` plus `vllm-summary` for one scene element.

**Steps:**

1. Author a `capture-rig` asset by transcribing DSEC's published calibration & extrinsics into the v3 format.
2. Wrap the left and right event streams as `event-stream-2d` assets.
3. Run a minimal Python script (NumPy + OpenCV) producing `event-cluster-2d` → `event-tracklet-2d`.
4. Cross-associate via epipolar + 1-ms temporal window into `multi-view-correspondence`.
5. Triangulate via DLT into `event-tracklet-3d`.
6. Aggregate into `motion-evidence-3d` and `vllm-summary`.
7. Validate the JSON envelope using the existing v2 SDK validators (extended to accept the new `kind` enum values), and dump a side-by-side text report.

### 14.2 Scenario B — Multi-event-camera object-tracking on M3ED

A more ambitious PoC using M3ED's multi-camera setup to emit several `event-tracklet-3d` per scene and link them to v2 `object-asset`s. Deferred until Scenario A is stable.

### 14.3 Scenario C — Industrial inspection mock (synthetic)

Simulate two virtual event cameras observing a moving CAD part (Stanford bunny in motion). Useful for unit-testing the schema before any real-sensor integration.

### 14.4 Out-of-scope for the PoC

- Realtime streaming.
- Learned event detectors / neural correspondence.
- Cross-modality fusion with RGB or LiDAR.

---

## 15. Public Dataset Candidates

The following datasets are candidates for PoC demos. Always re-check each dataset's license before redistributing or committing derived sample data.

| Dataset | Sensors / Notes | Primary URL |
|---|---|---|
| UZH Event Camera Dataset (DAVIS) | DAVIS 240C, indoor / outdoor; classic single-camera benchmark. | [https://rpg.ifi.uzh.ch/davis_data.html](https://rpg.ifi.uzh.ch/davis_data.html) |
| MVSEC | Stereo DAVIS 346B + LiDAR + IMU; driving / flying / handheld. | [https://daniilidis-group.github.io/mvsec/](https://daniilidis-group.github.io/mvsec/) |
| MVSEC — download portal | Direct download links for sequences. | [https://daniilidis-group.github.io/mvsec/download/](https://daniilidis-group.github.io/mvsec/download/) |
| DSEC | Stereo event + frame cameras, automotive; large-scale. | [https://arxiv.org/abs/2103.06011](https://arxiv.org/abs/2103.06011) |
| Prophesee GEN1 Automotive | Single Prophesee Gen1, automotive detection. | [https://www.prophesee.ai/2020/01/24/prophesee-gen1-automotive-detection-dataset/](https://www.prophesee.ai/2020/01/24/prophesee-gen1-automotive-detection-dataset/) |
| M3ED | Multi-modal multi-event-camera; ground / aerial. | [https://m3ed.io/data_overview/datafiles/](https://m3ed.io/data_overview/datafiles/) |
| EVIMO2 | Multi-camera event dataset with object motion ground truth. | [https://www.prophesee.ai/2025/01/27/evimo2-event-camera-dataset/](https://www.prophesee.ai/2025/01/27/evimo2-event-camera-dataset/) |
| DAVIS24 sample data | Small DAVIS sample sequences for quick prototyping. | [https://sites.google.com/view/davis24-davis-sample-data/home](https://sites.google.com/view/davis24-davis-sample-data/home) |

For a Scenario A PoC, **DSEC** is the most directly suitable due to its stereo event setup and well-published calibration. **MVSEC** is a strong fallback. **UZH** and **DAVIS24** are useful for unit-test-scale fixtures.

---

## 16. Open Questions

These are intentionally left open and should drive RFC discussion before any schema is frozen.

1. **Materialization granularity.** Should `event-cluster-2d` be a first-class asset, or only an internal intermediate that lives inside `event-tracklet-2d`? Trade-off: graph clarity vs. asset count blow-up on busy scenes.
2. **Time base portability.** Is `time_base` a sub-block of `capture-rig`, or a standalone first-class asset? Standalone makes re-syncing easier; sub-block keeps things simpler.
3. **Covariance representation.** Diagonal covariance is enough for most VLLM-facing summaries. Do we *also* allow full 3×3 covariances on `event-tracklet-3d.samples`?
4. **World vs rig frame.** Should the spec require either `rig` or `world` framing, or allow both freely? Mixed framings within one motion-evidence asset are a footgun.
5. **Event payload formats.** HDF5 (DSEC) vs. AEDAT4 (UZH) vs. RAW3 (Prophesee). Should v3 mint a canonical `event-stream-2d` payload format, or remain payload-agnostic and just enumerate format tokens?
6. **VLLM template registry.** Where do `template_id` values live? In the spec, in a separate registry doc, or per-implementation?
7. **Confidence semantics.** Are `confidence` values calibrated probabilities, ordinal scores, or "best effort"? The spec should pick one.
8. **Backwards path to v2.** When a v3 `motion-evidence-3d` references a v2 `object-asset`, can we offer a v2-only "shadow" envelope for tools that don't speak v3? Probably yes via a `kind: "object-asset"` summary, but the lifecycle of that shadow is unclear.
9. **Realtime / streaming.** Out of scope for the static-document v3, but the data model should not preclude a future v3-stream binding.
10. **Privacy.** Some event datasets contain pedestrians; the spec should at minimum point at a privacy-considerations section similar to v2 §13.

---

## 17. Implementation Milestones

A suggested staged rollout. Each milestone is gated on PoC validation, not calendar dates.

**M0 — RFC stabilization (this document).**
- Land this draft in `docs/v3/`. Open a GitHub Discussion / RFC. Collect feedback on §16 open questions.

**M1 — Minimal schema sketches (experimental).**
- Add JSON Schema *drafts* (not normative) for `capture-rig`, `event-stream-2d`, `event-tracklet-3d`, `motion-evidence-3d`, `vllm-summary`. Mark each schema clearly as `"$comment": "v3 experimental — do not depend on field names"`.
- Cross-validate with a single hand-authored example per kind.

**M2 — Scenario A PoC on DSEC.**
- One-shot Python script ingests a DSEC slice, emits the full v3 chain, validates against M1 schemas, prints a `vllm-summary`. No SDK changes yet — pure scripts under `samples/v3/`.

**M3 — SDK extension (Python first).**
- Add v3 enum values and minimal pydantic / dataclass models to the Python SDK behind an `experimental_v3` feature flag.
- Round-trip tests against M2 PoC outputs.

**M4 — Scenario B / M3ED PoC.**
- Multi-camera extension; add `multi-view-correspondence` association tooling.

**M5 — Spec hardening.**
- Resolve §16 open questions; promote schemas from experimental to draft. Author normative spec document(s) modeled on `spec/spatial-asset-profile-v2.md`.

**M6 — TypeScript SDK parity.**
- Mirror the Python SDK additions in TypeScript. Add cross-SDK interop tests under `tests/`.

**M7 — Optional realtime binding (future).**
- Out of v3.0 scope; sketch a streaming companion document.

---

## 18. Appendix A — Worked Example (Sketch)

A minimal end-to-end chain illustrating the asset graph for a single moving object on a stereo event rig (e.g., DSEC zurich_city_04, ~25 ms motion window):

```
capture-rig (urn:uuid:...-rig-dsec)
   ├── sensor cam_event_left   → event-stream-2d  (urn:uuid:...-stream-L)
   └── sensor cam_event_right  → event-stream-2d  (urn:uuid:...-stream-R)

event-stream-2d (urn:uuid:...-stream-L)
   └── event-tracklet-2d (urn:uuid:...-trk2d-L-007)

event-stream-2d (urn:uuid:...-stream-R)
   └── event-tracklet-2d (urn:uuid:...-trk2d-R-019)

multi-view-correspondence (urn:uuid:...-mvc-014)
   ├── trk2d-L-007
   ├── trk2d-R-019
   └── capture-rig (urn:uuid:...-rig-dsec)

event-tracklet-3d (urn:uuid:...-trk3d-003)
   └── mvc-014

motion-evidence-3d (urn:uuid:...-motion-042)
   └── trk3d-003
       (optionally also references v2 object-asset urn:uuid:...-object-bike-12)

vllm-summary (urn:uuid:...-vllm-019)
   └── motion-042
```

The full chain is a directed acyclic graph in the same v2 `derived_from` namespace, so existing v2 traceability tools — once they accept the new `kind` enum values — can render it without modification.

---

*End of draft.*
