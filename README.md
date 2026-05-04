# MCP Spatial Asset Profile v2

[![CI](https://github.com/furuse-kazufumi/mcp-spatial-asset-profile/actions/workflows/ci.yml/badge.svg)](https://github.com/furuse-kazufumi/mcp-spatial-asset-profile/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Status: PoC](https://img.shields.io/badge/status-Proof_of_Concept-orange.svg)](#project-status)
[![Spec: v2.0.0](https://img.shields.io/badge/spec-v2.0.0-informational.svg)](spec/spatial-asset-profile-v2.md)

**Languages / 言語 / 语言:** **English** · [日本語](README.ja.md) · [简体中文](README.zh-CN.md) · [한국어 (요약)](docs/i18n/README.ko.md) · [Español (resumen)](docs/i18n/README.es.md) · [Français (résumé)](docs/i18n/README.fr.md)

---

**MCP Spatial Asset Profile Version 2.0** — referred to throughout this repository as **MCP Spatial Asset Profile v2** — is a JSON-based envelope format for representing 3D and spatial data assets in [Model Context Protocol (MCP)](https://modelcontextprotocol.io/) tool ecosystems.

It builds on **[mcp-3d v1](https://github.com/puruyan2525/mcp-3d)** (Claude Code, April 2025) and is **strictly additive**: every v1 asset is upgradable to v2 without information loss, and v2 introduces a first-class segmentation workflow with full provenance tracing.

## Project Status

> **Proof of Concept** — the specification and reference SDKs (Python and TypeScript) are usable for prototyping and interoperability experiments. The format is not yet frozen; feedback from real-world MCP integrations is explicitly welcome before v2.1.

| Component | Status |
|---|---|
| Specification (`spec/spatial-asset-profile-v2.md`) | Draft, complete |
| JSON Schemas (Draft 2020-12) | Complete for all 8 asset kinds |
| Python SDK | Reference implementation, tested |
| TypeScript SDK | Reference implementation, tested |
| Sample assets & cross-SDK interoperability | Covered by `tests/` |

---

## What is this profile?

MCP Spatial Asset Profile v2 is the **envelope** — the metadata wrapper — that MCP-aware tools exchange when they hand 3D / spatial data to each other. The actual heavy payload (point clouds, meshes, splats, masks) lives behind URIs; the profile carries the information needed to **find, interpret, and trace** that payload.

v2 extends the v1 core with:

- **Globally stable `asset_id`** — URN-based, stable across pipelines.
- **Formal `spatial` block** — coordinate `frame`, `axis`, `handedness`, `unit`, `bounds` collected in one place.
- **Viewpoints** with camera intrinsics / extrinsics for renders and projections.
- **URI capability negotiation** — clients pick the best representation they can actually consume.
- **First-class segmentation workflow** — `rendered-view` → `segmentation-mask-2d` → `segmentation-mask-3d` → `object-asset`, all chained by `derived_from` and `workflow.target_asset_id`.
- **Full asset graph traceability** — every derived asset carries its lineage.

---

## Supported Asset Kinds

| Kind (`kind` value) | Description |
|---|---|
| `point-cloud` | 3D point set (PLY, PCD, LAS, NPY) |
| `mesh` | Polygonal surface mesh (OBJ, glTF, GLB) |
| `gaussian-splat` | 3D Gaussian Splatting scene |
| `depth-image` | 2D depth / range image (16-bit PNG, EXR) |
| `rendered-view` | RGB / RGB-D render from a viewpoint *(v2 new)* |
| `segmentation-mask-2d` | Pixel-level segmentation mask *(v2 new)* |
| `segmentation-mask-3d` | Per-point / per-face 3D labels *(v2 new)* |
| `object-asset` | Extracted segmented object instance *(v2 new)* |

All kinds share the same envelope; they differ only in the `representations` they advertise and the additional kind-specific fields they carry.

---

## Segmentation Workflow

```
Source (point-cloud / mesh / gaussian-splat)
    │  render
    ▼
rendered-view
    │  segment_2d
    ▼
segmentation-mask-2d
    │  lift_3d
    ▼
segmentation-mask-3d
    │  extract_object
    ▼
object-asset
```

Each step produces a separate v2 asset. Provenance is preserved through:

- `derived_from` — direct parent asset(s).
- `workflow.target_asset_id` — the *original* asset the entire chain ultimately segments.

This design anticipates **multi-view segmentation**: many `rendered-view` / `segmentation-mask-2d` assets can be lifted into a single shared `segmentation-mask-3d`, with every intermediate step independently inspectable.

---

## Repository Layout

```
mcp-spatial-asset-profile/
├── README.md                       ← This file (English landing)
├── README.ja.md                    ← 日本語版
├── README.zh-CN.md                 ← 简体中文版
├── docs/
│   ├── i18n/                       ← Brief summaries (KO / ES / FR)
│   ├── implementation-plan-v2.md
│   ├── reference-architecture-v2.md
│   ├── migration-from-v1.md
│   ├── publication-plan-v2.md
│   └── slides-v2.md
├── spec/
│   ├── spatial-asset-profile-v2.md       ← Core v2 specification
│   ├── segmentation-workflow-v2.md       ← Segmentation workflow extension
│   ├── schema/                           ← JSON Schemas (Draft 2020-12)
│   └── examples/                         ← Canonical example assets
├── sdk/
│   ├── python/                     ← Python SDK (`spatial-asset-v2`)
│   └── typescript/                 ← TypeScript SDK (`spatial-asset-v2`)
├── samples/                        ← Sample payloads (carried over from v1)
└── tests/                          ← Schema, roundtrip, interoperability tests
```

---

## Quick Start

### JSON Schema only

The schemas are usable standalone with any JSON Schema 2020-12 validator (e.g. `ajv`, `jsonschema`):

```bash
# spec/schema/asset.schema.json is the master schema
# spec/examples/*.json are canonical instances
```

### Python SDK

```bash
cd sdk/python
pip install -e ".[dev]"

# Validate an example asset
python -m spatial_asset_v2.cli.main validate ../../spec/examples/pointcloud-asset.json

# Generate sample assets
python -m spatial_asset_v2.cli.main generate --output /tmp/samples

# Run the mock segmentation pipeline end-to-end
python -m spatial_asset_v2.cli.main workflow \
  --source ../../spec/examples/pointcloud-asset.json \
  --output /tmp/pipeline

# Run tests
pytest tests/ -v
```

### TypeScript SDK

```bash
cd sdk/typescript
npm install
npm run build
npm test
```

---

## Validation & CI

GitHub Actions (`.github/workflows/ci.yml`) runs on every push and pull request to `main`:

- **Python SDK & repo tests** — Python 3.11 and 3.12, `pytest` for SDK unit tests *and* repository-level schema / roundtrip / interoperability tests.
- **TypeScript SDK** — Node.js 20, `npm run build` and `npm test`.

The same checks can be run locally; see *Quick Start* above. The CI badge at the top of this README reflects the current state of `main`.

---

## Backward Compatibility with v1

v2 is a **strict superset** of v1. Migration is mechanical:

| v1 | v2 | Migration |
|---|---|---|
| `id` | `asset_id` | Rename field |
| `crs` | `spatial.frame` | Move into `spatial` block |
| `bounds` | `spatial.bounds` | Move into `spatial` block |
| `version: "1.0"` | `version: "2.0"` | Bump version string |

Both reference SDKs auto-migrate v1 assets on parse. See [`docs/migration-from-v1.md`](docs/migration-from-v1.md).

---

## Roadmap

Short-term, post-PoC priorities:

1. **Multi-view segmentation workflow** — formalize lifting from N `rendered-view`s into a single shared `segmentation-mask-3d`.
2. **Capability vocabulary registry** — agree on a shared lexicon for representation `capabilities` so independent tools can interoperate without ad-hoc strings.
3. **Streaming representations** — describe tiled / progressive payloads (Cesium 3D Tiles, Potree, splat tiles) inside the envelope.
4. **Reference viewer adapter** — a minimal browser viewer using the TypeScript adapter interface, to make the profile demo-able end-to-end.
5. **Spec freeze for v2.1** — once feedback from external integrations stabilizes the format.

See also [`docs/implementation-plan-v2.md`](docs/implementation-plan-v2.md) and [`docs/publication-plan-v2.md`](docs/publication-plan-v2.md).

---

## Contributing

This is an open Proof of Concept and contributions are very welcome. Particularly useful:

- Real-world integrations that surface gaps in the envelope.
- Schema corrections, additional asset kinds, or capability vocabulary proposals.
- Translations and documentation improvements (see the language navigation at the top).

Please start here:

- **[CONTRIBUTING.md](CONTRIBUTING.md)** — how to propose changes, run tests, and keep spec / schema / examples / SDKs in sync.
- **[Code of Conduct](CODE_OF_CONDUCT.md)** — community standards.
- **[GitHub Discussions](https://github.com/furuse-kazufumi/mcp-spatial-asset-profile/discussions)** — questions, ideas, early-stage spec proposals, implementation reports, i18n help. English / 日本語 / 简体中文 all welcome.
- **[docs/community.md](docs/community.md)** — where each kind of conversation belongs and how spec proposals progress.

For larger spec changes, please open a Discussion or `[spec]` issue first to align on direction before sending a PR.

---

## License

MIT — see [LICENSE](LICENSE).

---

## Provenance

This project builds on **[mcp-3d v1](https://github.com/puruyan2525/mcp-3d)** by [@puruyan2525](https://github.com/puruyan2525), created with Claude Code (Anthropic) in April 2025. v2 extends the v1 core with the segmentation workflow, richer spatial metadata, and reference SDKs.

---

## 日本語サマリ

**MCP Spatial Asset Profile v2** は、MCP（Model Context Protocol）ツールエコシステムにおいて 3D・空間データ資産を扱うための JSON ベースのエンベロープ形式です。v1（`mcp-3d`）の厳密な上位互換であり、URN ベースの安定 `asset_id`、`spatial` ブロックによる座標系メタデータの統一、そして `rendered-view` → `segmentation-mask-2d` → `segmentation-mask-3d` → `object-asset` という追跡可能なセグメンテーションワークフローを追加します。

詳しくは **[README.ja.md](README.ja.md)** をご覧ください。

## 简体中文摘要

**MCP Spatial Asset Profile v2** 是一种基于 JSON 的封装格式，用于在 [Model Context Protocol (MCP)](https://modelcontextprotocol.io/) 工具生态中表示三维与空间数据资产。它是 v1（`mcp-3d`）的严格超集，新增了基于 URN 的稳定 `asset_id`、统一的 `spatial` 元数据块，以及 `rendered-view` → `segmentation-mask-2d` → `segmentation-mask-3d` → `object-asset` 的可追溯分割工作流。

详情请参阅 **[README.zh-CN.md](README.zh-CN.md)**。
