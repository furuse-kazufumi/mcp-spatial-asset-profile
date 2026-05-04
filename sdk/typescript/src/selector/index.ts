/**
 * selector/index.ts — Representation selector with capability negotiation.
 *
 * Design philosophy:
 * - selectRepresentation: chooses best representation given client capabilities
 * - filterByCapabilities: removes representations the client cannot use
 * - Pure functions; no I/O
 */

import type { SpatialAsset, Representation, CapabilityToken } from "../types/index.js";

/**
 * Filter representations to those the client can handle given its capabilities.
 *
 * @param reps All representations of an asset
 * @param capabilities Capability tokens declared by the client
 * @returns Representations whose capabilities_required are all satisfied
 */
export function filterByCapabilities(
  reps: Representation[],
  capabilities: CapabilityToken[] = [],
): Representation[] {
  const capSet = new Set<string>(capabilities);
  return reps.filter((rep) => {
    const required = rep.capabilities_required ?? [];
    return required.every((cap) => capSet.has(cap));
  });
}

/**
 * Select the preferred representation given client capabilities.
 *
 * Priority:
 * 1. render_hints.preferred_representation (if capable)
 * 2. Lowest LOD index (highest resolution) among capable representations
 * 3. First capable representation
 *
 * Returns undefined if no capable representation exists.
 */
export function selectRepresentation(
  asset: SpatialAsset,
  capabilities: CapabilityToken[] = [],
): Representation | undefined {
  const capable = filterByCapabilities(asset.representations, capabilities);
  if (capable.length === 0) return undefined;

  // Prefer the hint if it's in the capable set
  const preferred = asset.render_hints?.preferred_representation;
  if (preferred) {
    const hinted = capable.find((r) => r.rep_id === preferred);
    if (hinted) return hinted;
  }

  // Sort by LOD ascending (0 = full res), then pick first
  const sorted = [...capable].sort((a, b) => (a.lod ?? 0) - (b.lod ?? 0));
  return sorted[0];
}

/**
 * Select the best representation for a given format preference list.
 *
 * @param asset The spatial asset
 * @param preferredFormats Ordered list of preferred formats
 * @param capabilities Client capability tokens
 */
export function selectByFormat(
  asset: SpatialAsset,
  preferredFormats: Representation["format"][],
  capabilities: CapabilityToken[] = [],
): Representation | undefined {
  const capable = filterByCapabilities(asset.representations, capabilities);
  for (const fmt of preferredFormats) {
    const match = capable.find((r) => r.format === fmt);
    if (match) return match;
  }
  return capable[0];
}

/**
 * Get all representations at a specific LOD level.
 */
export function representationsAtLod(
  asset: SpatialAsset,
  lod: number,
): Representation[] {
  return asset.representations.filter((r) => (r.lod ?? 0) === lod);
}

/**
 * Get the total size in bytes of all representations.
 */
export function totalSizeBytes(asset: SpatialAsset): number {
  return asset.representations.reduce((sum, r) => sum + (r.size_bytes ?? 0), 0);
}
