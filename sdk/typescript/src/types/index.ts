/**
 * types/index.ts — TypeScript type definitions for MCP Spatial Asset Profile v2.
 *
 * Design philosophy:
 * - Exact structural mapping to asset.schema.json
 * - All optional fields are explicitly typed as optional
 * - No runtime dependencies; types only
 */

export const PROFILE_VERSION = "2.0" as const;

export type Vec3 = [number, number, number];

export type AssetKind =
  | "point-cloud"
  | "mesh"
  | "gaussian-splat"
  | "depth-image"
  | "rendered-view"
  | "segmentation-mask-2d"
  | "segmentation-mask-3d"
  | "object-asset";

export type RepresentationFormat =
  | "ply" | "pcd" | "las" | "laz"
  | "obj" | "gltf" | "glb"
  | "splat"
  | "png-depth" | "png-mask" | "png" | "jpeg"
  | "npy" | "npz"
  | "json-pc";

export interface BoundingBox {
  min: Vec3;
  max: Vec3;
}

export interface Spatial {
  frame?: string;
  up_axis?: "+Y" | "+Z" | "-Y" | "-Z";
  handedness?: "right" | "left";
  unit?: "m" | "mm" | "cm" | "ft" | "in";
  bounds?: BoundingBox;
}

export interface Intrinsics {
  fx: number;
  fy: number;
  cx: number;
  cy: number;
  k1?: number;
  k2?: number;
  p1?: number;
  p2?: number;
  [key: string]: number | undefined;
}

export interface Extrinsics {
  rotation?: number[][];
  translation?: Vec3;
}

export interface Viewpoint {
  viewpoint_id: string;
  label?: string;
  position?: Vec3;
  target?: Vec3;
  up?: Vec3;
  fov_y_deg?: number;
  near?: number;
  far?: number;
  image_width?: number;
  image_height?: number;
  intrinsics?: Intrinsics;
  extrinsics?: Extrinsics;
}

export interface RenderHints {
  point_size?: number;
  opacity?: number;
  color_mode?: "rgb" | "intensity" | "classification" | "normal" | "height";
  lod_policy?: "none" | "screen-space-error" | "distance";
  background_color?: Vec3;
  show_bounding_box?: boolean;
  preferred_representation?: string;
}

export interface WorkflowLabel {
  id: number;
  name: string;
  color?: [number, number, number];
}

export interface Workflow {
  step?: string;
  target_asset_id?: string;
  viewpoint_id?: string;
  instance_id?: string;
  label?: string;
  confidence?: number;
  tool?: string;
  tool_version?: string;
  parameters?: Record<string, unknown>;
  source_masks?: string[];
  correspondence?: string;
  labels?: WorkflowLabel[];
  started_at?: string;
  completed_at?: string;
}

export interface Representation {
  format: RepresentationFormat;
  uri: string;
  rep_id?: string;
  mime_type?: string;
  size_bytes?: number;
  sha256?: string;
  lod?: number;
  point_count?: number;
  face_count?: number;
  channels?: string[];
  capabilities_required?: string[];
  encoding?: string;
  depth_scale?: number;
  depth_unit?: string;
  image_width?: number;
  image_height?: number;
  viewpoint_id?: string;
  instance_id?: string;
}

export interface SpatialAsset {
  version: "2.0";
  asset_id: string;
  kind: AssetKind;
  name?: string;
  created_at?: string;
  representations: Representation[];
  spatial?: Spatial;
  viewpoints?: Viewpoint[];
  render_hints?: RenderHints;
  workflow?: Workflow;
  derived_from?: string[];
  metadata?: Record<string, unknown>;
}

/** Result of a validation check */
export interface ValidationResult {
  valid: boolean;
  errors: string[];
}

/** Capability token registry */
export const CAPABILITY_TOKENS = [
  "splat-render",
  "mesh-render",
  "webgpu",
  "webgl2",
  "lod-streaming",
  "lidar-las",
  "depth-rgb-d",
  "segmentation-mask",
] as const;

export type CapabilityToken = typeof CAPABILITY_TOKENS[number] | `x-${string}`;
