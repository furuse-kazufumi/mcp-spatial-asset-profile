/**
 * validator/index.ts — Structural validation for SpatialAsset objects.
 *
 * Design philosophy:
 * - No runtime schema loading; validation logic is inlined for zero-dep operation
 * - Returns ValidationResult with all errors collected (not fail-fast)
 * - Mirrors the Python schema_validator logic
 */

import type { SpatialAsset, ValidationResult } from "../types/index.js";

const VALID_KINDS = new Set([
  "point-cloud", "mesh", "gaussian-splat", "depth-image",
  "rendered-view", "segmentation-mask-2d", "segmentation-mask-3d", "object-asset",
]);

const VALID_FORMATS = new Set([
  "ply", "pcd", "las", "laz", "obj", "gltf", "glb", "splat",
  "png-depth", "png-mask", "png", "jpeg", "npy", "npz", "json-pc",
]);

export function validateAsset(asset: unknown): ValidationResult {
  const errors: string[] = [];

  if (typeof asset !== "object" || asset === null) {
    return { valid: false, errors: ["asset must be a JSON object"] };
  }

  const d = asset as Record<string, unknown>;

  // version
  if (d.version !== "2.0") {
    errors.push(`version must be '2.0', got: ${JSON.stringify(d.version)}`);
  }

  // asset_id
  if (typeof d.asset_id !== "string" || d.asset_id.length === 0) {
    errors.push("asset_id must be a non-empty string");
  }

  // kind
  if (typeof d.kind !== "string" || !VALID_KINDS.has(d.kind)) {
    errors.push(`kind '${d.kind}' is not a recognized kind`);
  }

  // representations
  if (!Array.isArray(d.representations) || d.representations.length === 0) {
    errors.push("representations must be a non-empty array");
  } else {
    (d.representations as unknown[]).forEach((rep, i) => {
      if (typeof rep !== "object" || rep === null) {
        errors.push(`representations[${i}] must be an object`);
        return;
      }
      const r = rep as Record<string, unknown>;
      if (typeof r.format !== "string" || !VALID_FORMATS.has(r.format)) {
        errors.push(`representations[${i}].format '${r.format}' is not recognized`);
      }
      if (typeof r.uri !== "string" || r.uri.length === 0) {
        errors.push(`representations[${i}].uri must be a non-empty string`);
      }
      if (r.depth_scale !== undefined && (typeof r.depth_scale !== "number" || r.depth_scale <= 0)) {
        errors.push(`representations[${i}].depth_scale must be > 0`);
      }
    });
  }

  // Kind-specific workflow checks
  const kind = typeof d.kind === "string" ? d.kind : "";
  const workflow = (typeof d.workflow === "object" && d.workflow !== null)
    ? d.workflow as Record<string, unknown>
    : {};

  if (kind === "rendered-view") {
    if (!workflow.target_asset_id) {
      errors.push("rendered-view: workflow.target_asset_id is required");
    }
    if (!workflow.viewpoint_id) {
      errors.push("rendered-view: workflow.viewpoint_id is required");
    }
  } else if (kind === "segmentation-mask-2d") {
    if (!workflow.target_asset_id) {
      errors.push("segmentation-mask-2d: workflow.target_asset_id is required");
    }
    if (!workflow.viewpoint_id) {
      errors.push("segmentation-mask-2d: workflow.viewpoint_id is required");
    }
  } else if (kind === "segmentation-mask-3d") {
    if (!workflow.target_asset_id) {
      errors.push("segmentation-mask-3d: workflow.target_asset_id is required");
    }
  } else if (kind === "object-asset") {
    if (!workflow.target_asset_id) {
      errors.push("object-asset: workflow.target_asset_id is required");
    }
    if (!workflow.instance_id) {
      errors.push("object-asset: workflow.instance_id is required");
    }
  }

  // Confidence range
  if (typeof workflow.confidence === "number") {
    if (workflow.confidence < 0 || workflow.confidence > 1) {
      errors.push(`workflow.confidence must be in [0, 1], got ${workflow.confidence}`);
    }
  }

  return { valid: errors.length === 0, errors };
}
