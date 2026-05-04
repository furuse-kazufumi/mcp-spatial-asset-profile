# Implementation Plan — MCP Spatial Asset Profile v2

**Status:** Working Draft  
**Date:** 2025-05  
**Phase:** PoC → Alpha

---

## 1. Scope

This document describes the phased implementation plan for MCP Spatial Asset Profile v2, from the current PoC state to a publishable Alpha version.

---

## 2. PoC Deliverables (Current State)

| Item | Status |
|---|---|
| Core spec v2 (`spatial-asset-profile-v2.md`) | ✅ Complete |
| Segmentation workflow spec (`segmentation-workflow-v2.md`) | ✅ Complete |
| JSON Schemas Draft 2020-12 (7 schemas) | ✅ Complete |
| Example JSON files (7 examples) | ✅ Complete |
| Python SDK skeleton | ✅ Complete |
| TypeScript SDK skeleton | ✅ Complete |
| Python tests (3 test files, ~40 tests) | ✅ Complete |
| TypeScript tests (1 test file, ~25 tests) | ✅ Complete |
| Documentation (5 docs) | ✅ Complete |

---

## 3. Phase 1 — Alpha (Target: 2025 Q3)

### 3.1 Specification

- [ ] Public review period for `spatial-asset-profile-v2.md`
- [ ] Finalize registered capability tokens
- [ ] Add formal ABNF grammar for `asset_id` schemes
- [ ] Add normative reference to MCP specification
- [ ] Resolve open questions in segmentation workflow extension

### 3.2 Schema

- [ ] Add `$defs` cross-references between overlay schemas
- [ ] Add `unevaluatedProperties: false` to all overlay schemas
- [ ] Publish schema to a stable CDN URL (`https://mcp-spatial.dev/spec/v2/`)
- [ ] Add CI/CD schema validation test with known-good and known-bad inputs

### 3.3 Python SDK

- [ ] Complete CLI with all subcommands
- [ ] Add `spatial_asset_v2.server` MCP server module (extends mcp-3d server.py)
- [ ] Add integration tests with real PLY/NPY files from samples/
- [ ] Publish to PyPI as `spatial-asset-v2`

### 3.4 TypeScript SDK

- [ ] Add `npm run build` to CI
- [ ] Add ESM build target alongside CJS
- [ ] Add integration tests against built JS with Node.js test runner
- [ ] Publish to npm as `spatial-asset-v2`

---

## 4. Phase 2 — Beta (Target: 2025 Q4)

### 4.1 MCP Server

- Implement `render_asset`, `segment_2d`, `lift_to_3d`, `extract_object`, `get_asset_graph` tool calls
- Integration with real segmentation tools (SAM2, optional/pluggable)
- MCP server tested with Claude Desktop

### 4.2 Storage Backend

- File-based asset registry (JSON index file)
- Optional SQLite backend for asset graph queries
- Asset deduplication by SHA-256

### 4.3 Developer Experience

- Interactive CLI wizard for creating new assets
- Asset graph visualization (ASCII tree)
- VS Code extension for `.schema.json` autocompletion

---

## 5. Phase 3 — 1.0 GA (Target: 2026 Q1)

- Stable specification with no breaking changes
- Reference implementations certified for all 8 kinds
- Test suite with 100+ cases including adversarial inputs
- Published to IANA Media Types for new MIME types
- Community governance model established

---

## 6. Known Risks

| Risk | Mitigation |
|---|---|
| MCP spec changes break compatibility | Track MCP spec changes; version separately |
| Heavy dependency creep | Keep all dependencies optional |
| Schema version fragmentation | Stable schema CDN with permanent URLs |
| Coordinate convention inconsistency | Mandatory `spatial.unit` enforcement |
