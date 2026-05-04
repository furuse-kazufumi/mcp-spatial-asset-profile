/**
 * resolver/index.ts — URI resolver interface for spatial asset representations.
 *
 * Design philosophy:
 * - Defines the UriResolver interface; implementations are injected by callers
 * - Supports relative URI resolution against a base URI
 * - No fetch() calls in this module; that is the implementation's responsibility
 */

import type { Representation } from "../types/index.js";

/**
 * Interface for resolving representation URIs to actual data.
 * Implementors may fetch from HTTP, local disk, MCP tool calls, etc.
 */
export interface UriResolver {
  /**
   * Resolve a representation URI to an absolute URI string.
   * @param rep The representation whose URI to resolve
   * @param baseUri Optional base URI to resolve relative URIs against
   */
  resolve(rep: Representation, baseUri?: string): string;

  /**
   * Fetch the raw binary data for a representation.
   * @param rep The representation to fetch
   * @param baseUri Optional base URI
   * @returns Promise resolving to the raw data as Uint8Array
   */
  fetch(rep: Representation, baseUri?: string): Promise<Uint8Array>;
}

/**
 * A simple URI resolver that handles relative paths against a base URI.
 * Does NOT fetch data; only resolves URIs.
 */
export class RelativeUriResolver implements UriResolver {
  constructor(private readonly baseUri: string = "") {}

  resolve(rep: Representation, baseUri?: string): string {
    const base = baseUri ?? this.baseUri;
    const uri = rep.uri;

    // Already absolute
    if (/^[a-zA-Z][a-zA-Z0-9+\-.]*:/.test(uri)) return uri;

    // Resolve relative to base
    if (!base) return uri;
    const separator = base.endsWith("/") ? "" : "/";
    return `${base}${separator}${uri}`;
  }

  async fetch(rep: Representation, baseUri?: string): Promise<Uint8Array> {
    const resolved = this.resolve(rep, baseUri);
    // In Node.js environments, use fs.readFile; in browser, use fetch()
    if (resolved.startsWith("http://") || resolved.startsWith("https://")) {
      const response = await globalThis.fetch(resolved);
      const buffer = await response.arrayBuffer();
      return new Uint8Array(buffer);
    }
    // Node.js file path
    try {
      const { readFile } = await import("fs/promises");
      const data = await readFile(resolved);
      return new Uint8Array(data.buffer);
    } catch {
      throw new Error(`Cannot fetch URI: ${resolved}`);
    }
  }
}

/**
 * Resolve all representation URIs in an asset and return a map of rep_id → absolute URI.
 */
export function resolveAllUris(
  representations: Representation[],
  resolver: UriResolver,
  baseUri?: string,
): Map<string, string> {
  const map = new Map<string, string>();
  for (const rep of representations) {
    const key = rep.rep_id ?? rep.uri;
    map.set(key, resolver.resolve(rep, baseUri));
  }
  return map;
}
