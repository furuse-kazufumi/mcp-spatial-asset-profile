/**
 * parser/index.ts — Parse JSON into typed SpatialAsset objects.
 *
 * Design philosophy:
 * - Tolerant parsing: unknown fields are preserved in metadata
 * - Never throws on unknown keys (forward compatibility)
 * - v1 assets are auto-migrated
 */

import type {
  SpatialAsset, Representation, Spatial, BoundingBox,
  Viewpoint, RenderHints, Workflow, WorkflowLabel, Vec3
} from "../types/index.js";

// ── helpers ──────────────────────────────────────────────────────────────────

function toVec3(v: unknown): Vec3 | undefined {
  if (Array.isArray(v) && v.length >= 3) {
    return [Number(v[0]), Number(v[1]), Number(v[2])];
  }
  return undefined;
}

function parseRepresentation(r: Record<string, unknown>): Representation {
  return {
    format: r.format as Representation["format"],
    uri: String(r.uri ?? ""),
    rep_id: r.rep_id != null ? String(r.rep_id) : undefined,
    mime_type: r.mime_type != null ? String(r.mime_type) : undefined,
    size_bytes: r.size_bytes != null ? Number(r.size_bytes) : undefined,
    sha256: r.sha256 != null ? String(r.sha256) : undefined,
    lod: r.lod != null ? Number(r.lod) : undefined,
    point_count: r.point_count != null ? Number(r.point_count) : undefined,
    face_count: r.face_count != null ? Number(r.face_count) : undefined,
    channels: Array.isArray(r.channels) ? r.channels.map(String) : undefined,
    capabilities_required: Array.isArray(r.capabilities_required)
      ? r.capabilities_required.map(String)
      : undefined,
    encoding: r.encoding != null ? String(r.encoding) : undefined,
    depth_scale: r.depth_scale != null ? Number(r.depth_scale) : undefined,
    depth_unit: r.depth_unit != null ? String(r.depth_unit) : undefined,
    image_width: r.image_width != null ? Number(r.image_width) : undefined,
    image_height: r.image_height != null ? Number(r.image_height) : undefined,
    viewpoint_id: r.viewpoint_id != null ? String(r.viewpoint_id) : undefined,
    instance_id: r.instance_id != null ? String(r.instance_id) : undefined,
  };
}

function parseSpatial(s: Record<string, unknown>): Spatial {
  let bounds: BoundingBox | undefined;
  if (s.bounds && typeof s.bounds === "object") {
    const b = s.bounds as Record<string, unknown>;
    const min = toVec3(b.min);
    const max = toVec3(b.max);
    if (min && max) bounds = { min, max };
  }
  return {
    frame: s.frame != null ? String(s.frame) : undefined,
    up_axis: (s.up_axis as Spatial["up_axis"]) ?? "+Y",
    handedness: (s.handedness as Spatial["handedness"]) ?? "right",
    unit: (s.unit as Spatial["unit"]) ?? "m",
    bounds,
  };
}

function parseViewpoint(v: Record<string, unknown>): Viewpoint {
  return {
    viewpoint_id: String(v.viewpoint_id ?? ""),
    label: v.label != null ? String(v.label) : undefined,
    position: toVec3(v.position),
    target: toVec3(v.target),
    up: toVec3(v.up),
    fov_y_deg: v.fov_y_deg != null ? Number(v.fov_y_deg) : undefined,
    near: v.near != null ? Number(v.near) : undefined,
    far: v.far != null ? Number(v.far) : undefined,
    image_width: v.image_width != null ? Number(v.image_width) : undefined,
    image_height: v.image_height != null ? Number(v.image_height) : undefined,
    intrinsics: v.intrinsics as Viewpoint["intrinsics"],
    extrinsics: v.extrinsics as Viewpoint["extrinsics"],
  };
}

function parseRenderHints(h: Record<string, unknown>): RenderHints {
  return {
    point_size: h.point_size != null ? Number(h.point_size) : undefined,
    opacity: h.opacity != null ? Number(h.opacity) : undefined,
    color_mode: h.color_mode as RenderHints["color_mode"],
    lod_policy: h.lod_policy as RenderHints["lod_policy"],
    background_color: toVec3(h.background_color),
    show_bounding_box: h.show_bounding_box != null ? Boolean(h.show_bounding_box) : undefined,
    preferred_representation: h.preferred_representation != null
      ? String(h.preferred_representation)
      : undefined,
  };
}

function parseWorkflowLabel(l: Record<string, unknown>): WorkflowLabel {
  const colorArr = Array.isArray(l.color)
    ? ([Number(l.color[0]), Number(l.color[1]), Number(l.color[2])] as [number, number, number])
    : undefined;
  return {
    id: Number(l.id ?? 0),
    name: String(l.name ?? ""),
    color: colorArr,
  };
}

function parseWorkflow(w: Record<string, unknown>): Workflow {
  const labels = Array.isArray(w.labels)
    ? (w.labels as Record<string, unknown>[]).map(parseWorkflowLabel)
    : undefined;
  return {
    step: w.step != null ? String(w.step) : undefined,
    target_asset_id: w.target_asset_id != null ? String(w.target_asset_id) : undefined,
    viewpoint_id: w.viewpoint_id != null ? String(w.viewpoint_id) : undefined,
    instance_id: w.instance_id != null ? String(w.instance_id) : undefined,
    label: w.label != null ? String(w.label) : undefined,
    confidence: w.confidence != null ? Number(w.confidence) : undefined,
    tool: w.tool != null ? String(w.tool) : undefined,
    tool_version: w.tool_version != null ? String(w.tool_version) : undefined,
    parameters: w.parameters as Record<string, unknown> | undefined,
    source_masks: Array.isArray(w.source_masks) ? w.source_masks.map(String) : undefined,
    correspondence: w.correspondence != null ? String(w.correspondence) : undefined,
    labels,
    started_at: w.started_at != null ? String(w.started_at) : undefined,
    completed_at: w.completed_at != null ? String(w.completed_at) : undefined,
  };
}

// ── public API ────────────────────────────────────────────────────────────────

/**
 * Parse a plain object (from JSON.parse) into a typed SpatialAsset.
 * Auto-migrates v1 assets (version="1.0").
 */
export function parseAsset(raw: unknown): SpatialAsset {
  if (typeof raw !== "object" || raw === null) {
    throw new Error("Expected a JSON object");
  }
  let d = raw as Record<string, unknown>;

  // v1 auto-migration
  if (d.version === "1.0") {
    d = migrateV1(d);
  }

  const spatial = d.spatial && typeof d.spatial === "object"
    ? parseSpatial(d.spatial as Record<string, unknown>)
    : undefined;

  const viewpoints = Array.isArray(d.viewpoints)
    ? (d.viewpoints as Record<string, unknown>[]).map(parseViewpoint)
    : undefined;

  const renderHints = d.render_hints && typeof d.render_hints === "object"
    ? parseRenderHints(d.render_hints as Record<string, unknown>)
    : undefined;

  const workflow = d.workflow && typeof d.workflow === "object"
    ? parseWorkflow(d.workflow as Record<string, unknown>)
    : undefined;

  const reps = Array.isArray(d.representations)
    ? (d.representations as Record<string, unknown>[]).map(parseRepresentation)
    : [];

  return {
    version: "2.0",
    asset_id: String(d.asset_id ?? ""),
    kind: d.kind as SpatialAsset["kind"],
    name: d.name != null ? String(d.name) : undefined,
    created_at: d.created_at != null ? String(d.created_at) : undefined,
    representations: reps,
    spatial,
    viewpoints,
    render_hints: renderHints,
    workflow,
    derived_from: Array.isArray(d.derived_from) ? d.derived_from.map(String) : undefined,
    metadata: d.metadata as Record<string, unknown> | undefined,
  };
}

/** Parse from JSON string */
export function parseAssetJSON(json: string): SpatialAsset {
  return parseAsset(JSON.parse(json));
}

/** v1 → v2 migration (same logic as Python SDK) */
export function migrateV1(v1: Record<string, unknown>): Record<string, unknown> {
  const v2: Record<string, unknown> = { ...v1, version: "2.0" };

  if ("id" in v2 && !("asset_id" in v2)) {
    v2.asset_id = v2.id;
    delete v2.id;
  }

  const spatial: Record<string, unknown> = typeof v2.spatial === "object" && v2.spatial !== null
    ? { ...(v2.spatial as Record<string, unknown>) }
    : {};

  if ("crs" in v2) {
    spatial.frame ??= v2.crs;
    delete v2.crs;
  }
  if ("bounds" in v2 && !("bounds" in spatial)) {
    spatial.bounds = v2.bounds;
    delete v2.bounds;
  }

  if (Object.keys(spatial).length > 0) {
    spatial.up_axis ??= "+Y";
    spatial.handedness ??= "right";
    spatial.unit ??= "m";
    v2.spatial = spatial;
  }

  return v2;
}
