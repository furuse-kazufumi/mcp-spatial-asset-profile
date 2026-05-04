/**
 * adapter/index.ts — Viewer adapter interface for spatial asset rendering.
 *
 * Design philosophy:
 * - Defines the ViewerAdapter interface; implementations are injected by callers
 * - Decouples the SDK from any specific renderer (Three.js, Babylon.js, WebGPU, etc.)
 * - Provides a no-op NullViewerAdapter for testing
 */

import type { SpatialAsset, Representation, Viewpoint, RenderHints } from "../types/index.js";

/**
 * Lifecycle events emitted by a viewer adapter.
 */
export type ViewerEvent =
  | { type: "loading"; rep: Representation }
  | { type: "loaded"; rep: Representation; durationMs: number }
  | { type: "error"; rep: Representation; error: Error }
  | { type: "viewpoint-changed"; viewpoint: Viewpoint }
  | { type: "disposed" };

/**
 * Callback for viewer events.
 */
export type ViewerEventCallback = (event: ViewerEvent) => void;

/**
 * Interface that a viewer implementation must satisfy to integrate with the SDK.
 */
export interface ViewerAdapter {
  /** Load an asset's preferred representation into the viewer. */
  loadAsset(
    asset: SpatialAsset,
    data: Uint8Array,
    rep: Representation,
  ): Promise<void>;

  /** Apply render hints to the viewer. */
  applyRenderHints(hints: RenderHints): void;

  /** Set the active viewpoint. */
  setViewpoint(viewpoint: Viewpoint): void;

  /** Get the current viewpoint. */
  getViewpoint(): Viewpoint | undefined;

  /** Register an event listener. */
  on(callback: ViewerEventCallback): void;

  /** Unregister an event listener. */
  off(callback: ViewerEventCallback): void;

  /** Release all resources. */
  dispose(): void;
}

/**
 * A no-op viewer adapter for testing and headless environments.
 * All methods are silent no-ops; loadAsset resolves immediately.
 */
export class NullViewerAdapter implements ViewerAdapter {
  private _viewpoint: Viewpoint | undefined;
  private _callbacks: ViewerEventCallback[] = [];

  async loadAsset(
    _asset: SpatialAsset,
    _data: Uint8Array,
    _rep: Representation,
  ): Promise<void> {
    // No-op
  }

  applyRenderHints(_hints: RenderHints): void {
    // No-op
  }

  setViewpoint(viewpoint: Viewpoint): void {
    this._viewpoint = viewpoint;
    this._emit({ type: "viewpoint-changed", viewpoint });
  }

  getViewpoint(): Viewpoint | undefined {
    return this._viewpoint;
  }

  on(callback: ViewerEventCallback): void {
    this._callbacks.push(callback);
  }

  off(callback: ViewerEventCallback): void {
    this._callbacks = this._callbacks.filter((cb) => cb !== callback);
  }

  dispose(): void {
    this._emit({ type: "disposed" });
    this._callbacks = [];
  }

  private _emit(event: ViewerEvent): void {
    for (const cb of this._callbacks) cb(event);
  }
}

/**
 * Utility: pick the first viewpoint that matches a given viewpoint_id.
 */
export function findViewpoint(
  viewpoints: Viewpoint[] | undefined,
  viewpoint_id: string,
): Viewpoint | undefined {
  return viewpoints?.find((vp) => vp.viewpoint_id === viewpoint_id);
}
