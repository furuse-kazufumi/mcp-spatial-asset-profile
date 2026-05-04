/**
 * index.ts — Public API for spatial-asset-v2 TypeScript SDK.
 *
 * MCP Spatial Asset Profile v2 — TypeScript SDK
 * Version 2.0.0
 */

// Types
export type {
  SpatialAsset,
  Representation,
  Spatial,
  BoundingBox,
  Viewpoint,
  RenderHints,
  Workflow,
  WorkflowLabel,
  AssetKind,
  RepresentationFormat,
  CapabilityToken,
  Vec3,
  ValidationResult,
} from "./types/index.js";

export { PROFILE_VERSION, CAPABILITY_TOKENS } from "./types/index.js";

// Parser
export { parseAsset, parseAssetJSON, migrateV1 } from "./parser/index.js";

// Selector
export {
  filterByCapabilities,
  selectRepresentation,
  selectByFormat,
  representationsAtLod,
  totalSizeBytes,
} from "./selector/index.js";

// Resolver
export type { UriResolver } from "./resolver/index.js";
export { RelativeUriResolver, resolveAllUris } from "./resolver/index.js";

// Adapter
export type { ViewerAdapter, ViewerEvent, ViewerEventCallback } from "./adapter/index.js";
export { NullViewerAdapter, findViewpoint } from "./adapter/index.js";

// Validator
export { validateAsset } from "./validator/index.js";
