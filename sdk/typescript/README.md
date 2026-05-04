# @furuse-kazufumi/mcp-spatial-asset-profile — TypeScript SDK

Reference TypeScript SDK for the **[MCP Spatial Asset Profile v2](https://github.com/furuse-kazufumi/mcp-spatial-asset-profile)** — a JSON envelope format for 3D / spatial assets in Model Context Protocol (MCP) tool ecosystems.

- **Distribution name (npm):** [`@furuse-kazufumi/mcp-spatial-asset-profile`](https://www.npmjs.com/package/@furuse-kazufumi/mcp-spatial-asset-profile)
- **Python counterpart:** [`mcp-spatial-asset-profile`](https://pypi.org/project/mcp-spatial-asset-profile/) (import `spatial_asset_v2`)
- **Spec & repository:** <https://github.com/furuse-kazufumi/mcp-spatial-asset-profile>
- **Release tag:** [`v0.1.0-poc`](https://github.com/furuse-kazufumi/mcp-spatial-asset-profile/releases/tag/v0.1.0-poc)

> **Status — Proof of Concept.** The format is usable for prototyping and interoperability experiments; not yet frozen. Feedback via [GitHub Discussions](https://github.com/furuse-kazufumi/mcp-spatial-asset-profile/discussions) is welcome before v2.1.

## Installation

Once published to npm:

```bash
npm install @furuse-kazufumi/mcp-spatial-asset-profile
# or
pnpm add @furuse-kazufumi/mcp-spatial-asset-profile
# or
yarn add @furuse-kazufumi/mcp-spatial-asset-profile
```

From source (this repository):

```bash
cd sdk/typescript
npm install
npm run build
npm test
```

## Quick Start

```ts
import {
  parseAsset,
  validateAsset,
  selectRepresentation,
  PROFILE_VERSION,
} from "@furuse-kazufumi/mcp-spatial-asset-profile";

const asset = parseAsset({
  asset_id: "urn:uuid:550e8400-e29b-41d4-a716-446655440001",
  kind: "point-cloud",
  version: PROFILE_VERSION,
  representations: [
    { format: "ply", uri: "samples/bunny.ply", point_count: 35947 },
  ],
  spatial: { unit: "m", up_axis: "+Y" },
  name: "Stanford Bunny",
});

const result = validateAsset(asset);
console.log("Valid:", result.valid);

const best = selectRepresentation(asset, { preferredFormats: ["ply"] });
console.log("Selected URI:", best?.uri);
```

## Public API

See [`src/index.ts`](./src/index.ts) for the full public surface:

- `parseAsset`, `parseAssetJSON`, `migrateV1`
- `selectRepresentation`, `filterByCapabilities`, `selectByFormat`, `representationsAtLod`, `totalSizeBytes`
- `RelativeUriResolver`, `resolveAllUris`
- `NullViewerAdapter`, `findViewpoint`
- `validateAsset`
- Types: `SpatialAsset`, `Representation`, `Spatial`, `BoundingBox`, `Viewpoint`, `RenderHints`, `Workflow`, `WorkflowLabel`, `AssetKind`, `RepresentationFormat`, `CapabilityToken`, `Vec3`, `ValidationResult`

## License

MIT — see the [LICENSE](https://github.com/furuse-kazufumi/mcp-spatial-asset-profile/blob/main/LICENSE) file at the repository root.
