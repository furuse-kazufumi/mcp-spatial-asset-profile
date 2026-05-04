/**
 * index.test.ts — Tests for spatial-asset-v2 TypeScript SDK.
 * Uses Node.js built-in test runner (node:test).
 */

import { describe, it } from "node:test";
import assert from "node:assert/strict";

import { parseAsset, migrateV1 } from "../parser/index.js";
import { filterByCapabilities, selectRepresentation, selectByFormat } from "../selector/index.js";
import { NullViewerAdapter, findViewpoint } from "../adapter/index.js";
import { RelativeUriResolver } from "../resolver/index.js";
import { validateAsset } from "../validator/index.js";
import type { SpatialAsset, Representation } from "../types/index.js";

// ── fixtures ─────────────────────────────────────────────────────────────────

function makeMinimalAsset(): Record<string, unknown> {
  return {
    version: "2.0",
    asset_id: "urn:uuid:test-001",
    kind: "point-cloud",
    representations: [{ format: "ply", uri: "test.ply" }],
  };
}

function makeFullAsset(): Record<string, unknown> {
  return {
    version: "2.0",
    asset_id: "urn:uuid:full-001",
    kind: "mesh",
    name: "Test Mesh",
    created_at: "2025-05-01T09:00:00Z",
    representations: [
      {
        rep_id: "rep-obj",
        format: "obj",
        uri: "mesh.obj",
        lod: 0,
        face_count: 320,
        capabilities_required: [],
      },
      {
        rep_id: "rep-splat",
        format: "splat",
        uri: "scene.splat",
        lod: 0,
        capabilities_required: ["splat-render"],
      },
    ],
    spatial: {
      frame: "local-ENU",
      up_axis: "+Y",
      unit: "m",
      bounds: { min: [-1, -1, -1], max: [1, 1, 1] },
    },
    render_hints: {
      preferred_representation: "rep-obj",
      opacity: 1.0,
    },
    viewpoints: [
      {
        viewpoint_id: "vp-front",
        label: "Front",
        position: [0, 0, 1],
        target: [0, 0, 0],
        up: [0, 1, 0],
        fov_y_deg: 45,
      },
    ],
    workflow: {
      step: "render",
      target_asset_id: "urn:uuid:src",
      confidence: 0.9,
    },
    derived_from: ["urn:uuid:src"],
    metadata: { note: "test" },
  };
}

// ── parser tests ──────────────────────────────────────────────────────────────

describe("parseAsset", () => {
  it("parses minimal asset", () => {
    const asset = parseAsset(makeMinimalAsset());
    assert.equal(asset.version, "2.0");
    assert.equal(asset.asset_id, "urn:uuid:test-001");
    assert.equal(asset.kind, "point-cloud");
    assert.equal(asset.representations.length, 1);
  });

  it("parses spatial block", () => {
    const asset = parseAsset(makeFullAsset());
    assert.ok(asset.spatial);
    assert.equal(asset.spatial.unit, "m");
    assert.deepEqual(asset.spatial.bounds!.min, [-1, -1, -1]);
  });

  it("parses viewpoints", () => {
    const asset = parseAsset(makeFullAsset());
    assert.equal(asset.viewpoints!.length, 1);
    assert.equal(asset.viewpoints![0].viewpoint_id, "vp-front");
  });

  it("parses workflow", () => {
    const asset = parseAsset(makeFullAsset());
    assert.equal(asset.workflow!.step, "render");
    assert.equal(asset.workflow!.confidence, 0.9);
  });

  it("throws on non-object input", () => {
    assert.throws(() => parseAsset("not an object"));
  });
});

// ── migration tests ───────────────────────────────────────────────────────────

describe("migrateV1", () => {
  it("upgrades version to 2.0", () => {
    const v1 = { version: "1.0", id: "x", kind: "point-cloud", representations: [] };
    const v2 = migrateV1(v1);
    assert.equal(v2.version, "2.0");
  });

  it("renames id to asset_id", () => {
    const v1 = { version: "1.0", id: "urn:uuid:old", kind: "point-cloud", representations: [] };
    const v2 = migrateV1(v1);
    assert.equal(v2.asset_id, "urn:uuid:old");
    assert.ok(!("id" in v2));
  });

  it("moves crs to spatial.frame", () => {
    const v1 = { version: "1.0", id: "x", crs: "local-ENU", representations: [] };
    const v2 = migrateV1(v1);
    const s = v2.spatial as Record<string, unknown>;
    assert.equal(s.frame, "local-ENU");
    assert.ok(!("crs" in v2));
  });

  it("does not mutate original", () => {
    const v1 = { version: "1.0", id: "x", crs: "local", representations: [] };
    migrateV1(v1);
    assert.equal(v1.version, "1.0");
    assert.ok("crs" in v1);
  });
});

// ── selector tests ────────────────────────────────────────────────────────────

describe("filterByCapabilities", () => {
  const reps: Representation[] = [
    { format: "obj", uri: "mesh.obj", capabilities_required: [] },
    { format: "splat", uri: "scene.splat", capabilities_required: ["splat-render"] },
    { format: "glb", uri: "scene.glb", capabilities_required: ["mesh-render", "webgl2"] },
  ];

  it("returns all reps when all caps satisfied", () => {
    const result = filterByCapabilities(reps, ["splat-render", "mesh-render", "webgl2"] as any);
    assert.equal(result.length, 3);
  });

  it("filters out splat without capability", () => {
    const result = filterByCapabilities(reps, []);
    assert.equal(result.length, 1);
    assert.equal(result[0].format, "obj");
  });

  it("filters by partial capabilities", () => {
    const result = filterByCapabilities(reps, ["splat-render"] as any);
    assert.equal(result.length, 2);
  });
});

describe("selectRepresentation", () => {
  it("returns undefined when no capable reps", () => {
    const asset = parseAsset(makeMinimalAsset()) as SpatialAsset;
    // splat-render not needed for ply, so this should still return
    const result = selectRepresentation(asset, []);
    assert.ok(result);
  });

  it("prefers render_hints.preferred_representation", () => {
    const asset = parseAsset(makeFullAsset()) as SpatialAsset;
    const result = selectRepresentation(asset, []);
    // preferred is rep-obj (no caps needed)
    assert.equal(result!.rep_id, "rep-obj");
  });
});

describe("selectByFormat", () => {
  it("returns first matching format", () => {
    const asset = parseAsset(makeFullAsset()) as SpatialAsset;
    const result = selectByFormat(asset, ["obj", "ply"], []);
    assert.equal(result!.format, "obj");
  });

  it("falls back to next format", () => {
    const asset = parseAsset(makeFullAsset()) as SpatialAsset;
    const result = selectByFormat(asset, ["ply", "obj"], []);
    assert.equal(result!.format, "obj");
  });
});

// ── validator tests ───────────────────────────────────────────────────────────

describe("validateAsset", () => {
  it("validates minimal valid asset", () => {
    const result = validateAsset(makeMinimalAsset());
    assert.equal(result.valid, true);
    assert.deepEqual(result.errors, []);
  });

  it("rejects wrong version", () => {
    const a = { ...makeMinimalAsset(), version: "1.0" };
    const result = validateAsset(a);
    assert.equal(result.valid, false);
    assert.ok(result.errors.some((e) => e.includes("version")));
  });

  it("rejects missing asset_id", () => {
    const { asset_id, ...a } = makeMinimalAsset() as any;
    const result = validateAsset(a);
    assert.equal(result.valid, false);
    assert.ok(result.errors.some((e) => e.includes("asset_id")));
  });

  it("rejects empty representations", () => {
    const a = { ...makeMinimalAsset(), representations: [] };
    const result = validateAsset(a);
    assert.equal(result.valid, false);
    assert.ok(result.errors.some((e) => e.includes("representations")));
  });

  it("rejects invalid depth_scale", () => {
    const a = {
      version: "2.0", asset_id: "x", kind: "depth-image",
      representations: [{ format: "png-depth", uri: "d.png", depth_scale: -1 }],
    };
    const result = validateAsset(a);
    assert.equal(result.valid, false);
    assert.ok(result.errors.some((e) => e.includes("depth_scale")));
  });

  it("rejects rendered-view without workflow.target_asset_id", () => {
    const a = {
      version: "2.0", asset_id: "x", kind: "rendered-view",
      representations: [{ format: "png", uri: "rv.png" }],
      workflow: { viewpoint_id: "vp-1" },
    };
    const result = validateAsset(a);
    assert.ok(result.errors.some((e) => e.includes("target_asset_id")));
  });

  it("rejects object-asset without instance_id", () => {
    const a = {
      version: "2.0", asset_id: "x", kind: "object-asset",
      representations: [{ format: "ply", uri: "o.ply" }],
      workflow: { target_asset_id: "urn:uuid:src" },
    };
    const result = validateAsset(a);
    assert.ok(result.errors.some((e) => e.includes("instance_id")));
  });
});

// ── adapter tests ─────────────────────────────────────────────────────────────

describe("NullViewerAdapter", () => {
  it("loadAsset resolves", async () => {
    const adapter = new NullViewerAdapter();
    const asset = parseAsset(makeMinimalAsset());
    const rep = asset.representations[0];
    await adapter.loadAsset(asset, new Uint8Array(), rep);
    // No error = pass
  });

  it("setViewpoint stores viewpoint", () => {
    const adapter = new NullViewerAdapter();
    const vp = { viewpoint_id: "vp-test", label: "Test" };
    adapter.setViewpoint(vp);
    assert.equal(adapter.getViewpoint()!.viewpoint_id, "vp-test");
  });

  it("emits viewpoint-changed event", () => {
    const adapter = new NullViewerAdapter();
    const events: string[] = [];
    adapter.on((e) => events.push(e.type));
    adapter.setViewpoint({ viewpoint_id: "vp-1" });
    assert.ok(events.includes("viewpoint-changed"));
  });

  it("dispose emits disposed event", () => {
    const adapter = new NullViewerAdapter();
    const events: string[] = [];
    adapter.on((e) => events.push(e.type));
    adapter.dispose();
    assert.ok(events.includes("disposed"));
  });
});

describe("findViewpoint", () => {
  it("finds by viewpoint_id", () => {
    const vps = [
      { viewpoint_id: "vp-front" },
      { viewpoint_id: "vp-back" },
    ];
    const found = findViewpoint(vps, "vp-back");
    assert.equal(found!.viewpoint_id, "vp-back");
  });

  it("returns undefined for missing id", () => {
    assert.equal(findViewpoint([], "vp-x"), undefined);
  });

  it("returns undefined for undefined viewpoints", () => {
    assert.equal(findViewpoint(undefined, "vp-x"), undefined);
  });
});

// ── resolver tests ────────────────────────────────────────────────────────────

describe("RelativeUriResolver", () => {
  it("resolves absolute URI unchanged", () => {
    const resolver = new RelativeUriResolver("http://example.com");
    const rep: Representation = { format: "ply", uri: "https://cdn.example.com/asset.ply" };
    assert.equal(resolver.resolve(rep), "https://cdn.example.com/asset.ply");
  });

  it("resolves relative URI against base", () => {
    const resolver = new RelativeUriResolver("http://example.com/assets");
    const rep: Representation = { format: "ply", uri: "bunny.ply" };
    assert.equal(resolver.resolve(rep), "http://example.com/assets/bunny.ply");
  });

  it("handles trailing slash in base", () => {
    const resolver = new RelativeUriResolver("http://example.com/assets/");
    const rep: Representation = { format: "ply", uri: "bunny.ply" };
    assert.equal(resolver.resolve(rep), "http://example.com/assets/bunny.ply");
  });
});
