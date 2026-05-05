# Claude Code Implementation Brief — v3 Multi-Event, Multi-Camera Spatial Evidence Profile

**Status:** Working Draft (Requirements & Design)
**Date:** 2026-05
**Companion to:** [`multi-event-camera-spatial-evidence-profile-v3.md`](multi-event-camera-spatial-evidence-profile-v3.md)
**Audience:** Claude Code (and human reviewers handing work to it)

---

## Table of Contents

1. [Purpose of This Document](#1-purpose-of-this-document)
2. [Product / Problem Statement](#2-product--problem-statement)
3. [Target Users and Use Cases](#3-target-users-and-use-cases)
4. [Success Criteria](#4-success-criteria)
5. [Functional Requirements](#5-functional-requirements)
6. [Non-Functional Requirements](#6-non-functional-requirements)
7. [Data Model Requirements](#7-data-model-requirements)
8. [Schema Drafting Tasks](#8-schema-drafting-tasks)
9. [Python PoC Tasks](#9-python-poc-tasks)
10. [TypeScript / Viewer / Resolver Tasks](#10-typescript--viewer--resolver-tasks)
11. [Test Strategy](#11-test-strategy)
12. [Public Dataset Handling and License Caution](#12-public-dataset-handling-and-license-caution)
13. [Out of Scope (Explicit)](#13-out-of-scope-explicit)
14. [Recommended File Additions](#14-recommended-file-additions)
15. [Milestone Tickets — M0 to M3](#15-milestone-tickets--m0-to-m3)
16. [Acceptance Criteria Index](#16-acceptance-criteria-index)
17. [Risk and Open Issue Log](#17-risk-and-open-issue-log)

---

## 1. Purpose of This Document

This document is a **requirements and design brief** for v3 of the MCP Spatial
Asset Profile. It is the handoff document from the working group's RFC draft to
implementers — primarily Claude Code agents driven from PRs and issues.

It is *not* an implementation. It defines *what* needs to be built and *how to
verify* it, in language and structure suited for autonomous agents to pick up
discrete tickets without re-deriving context.

Companion documents:

- [`multi-event-camera-spatial-evidence-profile-v3.md`](multi-event-camera-spatial-evidence-profile-v3.md) — the RFC vocabulary and design.
- [`../../spec/spatial-asset-profile-v2.md`](../../spec/spatial-asset-profile-v2.md) — the v2 base profile.
- [`../../spec/segmentation-workflow-v2.md`](../../spec/segmentation-workflow-v2.md) — the v2 segmentation extension.

When this brief and the RFC disagree, the RFC is canonical for vocabulary and
the brief is canonical for tasks and acceptance.

---

## 2. Product / Problem Statement

v2 of the profile cleanly handles *one asset, one pipeline*. Real spatial
evidence is rarely shaped that way:

- Inspection rigs use 2–8 cameras with known calibration and capture per-event,
  not as a continuous stream.
- A finding ("anomaly on weld seam at 13:42 from cameras 1, 3, and 4") is the
  natural unit, and its supporting artifacts span multiple views and derived
  masks.
- Public datasets need provenance and license to travel with the evidence.

v3 introduces **events**, **rigs**, **observations**, and **evidence bundles**
so that this kind of evidence can be produced, stored, validated, and exchanged
without each implementer reinventing conventions inside `metadata`.

The goal of this milestone effort is to land v3 as a **working draft with a
runnable PoC**, not a stable 1.0. Stability work follows in a later phase.

---

## 3. Target Users and Use Cases

### 3.1 Primary users

- **Industrial inspection teams** producing per-event multi-camera evidence.
- **Robotics dataset authors** packaging events (manipulations, near-misses,
  anomalies) for sharing.
- **Tool implementers** building MCP servers that consume or produce such
  evidence (renderers, segmenters, viewers, archivers).
- **LLM agents** generating, validating, or routing evidence bundles in MCP
  workflows.

### 3.2 Representative use cases

- **U1.** Capture a 5-second event across 4 synchronized cameras and emit a
  signed evidence bundle with rig calibration, per-camera frame sequences, and
  a 2D segmentation mask per camera.
- **U2.** Resolve an existing bundle and render any single observation via the
  v2 viewer pipeline without modification.
- **U3.** Lift per-camera 2D masks into a single 3D mask aligned to a fused
  point cloud, recording all source masks and the rig used.
- **U4.** Re-publish a public-dataset event under its original license, with
  attribution and SPDX metadata preserved across export.
- **U5.** Diff two bundles of the same event captured days apart to detect
  rig drift via `rig.fingerprint`.

---

## 4. Success Criteria

The v3 PoC milestone is successful when **all** of the following hold:

- **S1.** A v3 evidence bundle round-trips through the Python SDK
  (parse → validate → serialize) byte-stable for canonical JSON.
- **S2.** A v3 bundle that contains a v2-style segmentation pipeline validates
  under both the v3 overlay schemas and the existing v2 schemas.
- **S3.** The TypeScript viewer renders any single observation referenced by
  a bundle without modifications to the v2 viewer code path.
- **S4.** The traceability validator can resolve every derived asset in a
  bundle back to at least one observation in the bundle.
- **S5.** A public-dataset bundle preserves SPDX license and attribution
  through ingest, validate, and export, with a CI test that fails if license
  metadata is dropped.
- **S6.** Documentation, schemas, examples, and tests are linked from
  `docs/v3/README.md` and pass `make test` (or equivalent) in CI.

---

## 5. Functional Requirements

| ID | Requirement | Source |
|---|---|---|
| F1 | Define `camera-rig`, `event`, `observation`, `evidence-bundle` asset kinds. | RFC §6 |
| F2 | Carry rig intrinsics, extrinsics (per camera), and `sync_class`. | RFC §8 |
| F3 | Carry event time range with declared `time_base` and optional `sync_jitter_ms_p99`. | RFC §7, §9 |
| F4 | Express observation→event and event→rig links explicitly (not only via `derived_from`). | RFC §6 |
| F5 | Support per-frame timestamps via inline arrays (short) or URI (long). | RFC §6.3 |
| F6 | Allow the v2 segmentation pipeline (render → segment-2d → lift-3d → extract) to be parented to an observation rather than a bare source asset. | RFC §11 |
| F7 | Provide an `evidence-bundle` that gathers rig + event + observations + derived assets + license + provenance. | RFC §10 |
| F8 | Bundle license MUST carry SPDX identifier and attribution requirements. | RFC §10 |
| F9 | Provide a Python `bundle_evidence(...)` function that produces a sealed bundle from a list of asset_ids. | This brief |
| F10 | Provide a Python `resolve_bundle(bundle_id_or_path)` that yields rig, event, observations, and derived assets in load order. | This brief |
| F11 | Provide a TypeScript resolver that loads a bundle JSON, validates it, and surfaces typed accessors for rig, event, observations. | This brief |
| F12 | Provide a TypeScript viewer adapter that renders a chosen observation via the existing v2 viewer code path. | This brief |
| F13 | Detect rig drift across two bundles via `rig.fingerprint`. | This brief |
| F14 | Validate that every derived asset in a bundle traces to at least one observation. | RFC §12 |

---

## 6. Non-Functional Requirements

| ID | Requirement |
|---|---|
| N1 | v3 envelopes MUST remain readable by a v2-only parser at the top level (graceful field ignore). |
| N2 | All schemas MUST be JSON Schema Draft 2020-12, consistent with v2. |
| N3 | Canonical JSON serialization MUST be deterministic (sorted keys, UTF-8, no trailing whitespace). |
| N4 | Python SDK MUST keep its v2 dependencies and add no required heavy deps (numpy, jsonschema OK; no torch). |
| N5 | TypeScript SDK MUST keep ESM/CJS dual builds and not require a browser-only runtime in core. |
| N6 | Per-bundle validation on a 4-camera × 5-second event bundle MUST complete in < 1 s on a developer laptop. |
| N7 | License metadata MUST never be silently dropped on export; missing SPDX MUST be a validation error for sealed bundles. |
| N8 | All new public APIs MUST be documented in their respective SDK READMEs. |
| N9 | All new code MUST follow the project's existing lint/format conventions (verified in CI). |
| N10 | All new tests MUST run offline; any test data MUST be either generated, stubbed, or licensed for redistribution. |

---

## 7. Data Model Requirements

The v3 data model extends v2 with four new top-level kinds and two new optional
blocks. Implementers MUST treat the model below as authoritative for the v3 PoC,
modulo open questions in §17.

### 7.1 New kinds

- `camera-rig`
- `event`
- `observation`
- `evidence-bundle`

### 7.2 New optional blocks

- `event` block, present on `event`, `observation`, and `evidence-bundle`:
  - `event_id` (string, required on `event` and `observation`)
  - `rig_id` (string, required on `event`)
  - `time_range`: `{start: ISO8601, end: ISO8601 | null, time_base: enum}`
  - `time_base`: enum `{utc, tai, monotonic-rig, monotonic-host}`
  - `sync_class`: enum `{hardware, software-ptp, software-ntp, best-effort, unknown}`
  - `sync_jitter_ms_p99`: number ≥ 0, optional
  - `label`, `summary`, `priors`: optional, free-form-but-typed
- `rig` block, present on `camera-rig`:
  - `cameras[]`: `{camera_id, intrinsics, extrinsics, lens_model?, sync_class}`
  - `time_base`, `sync_class` at rig level
  - `fingerprint`: SHA-256 over canonical calibration serialization
- `bundle` block, present on `evidence-bundle`:
  - `event_id`
  - `contents[]`: ordered list of asset_ids
  - `license`: `{spdx_id, url, attribution_required, redistribution_terms}`
  - `provenance`: `{captured_by, captured_at, processed_by[], publisher, dataset_doi?}`
  - `checksums`: `{<asset_id>: sha256}`, optional
  - `notes`: array of `{uri, mime_type}`, optional

### 7.3 Field-level constraints

- All timestamps MUST share a `time_base` within a bundle.
- `bundle.contents[]` MUST include the bundle's `event_id` and that event's
  `rig_id` and all `observation_ids[]`.
- `evidence-bundle.bundle.contents[]` MUST be deduplicated and stable in order.
- `rig.fingerprint` MUST change when any intrinsics or extrinsics change.

### 7.4 Backward compatibility with v2

- `version: "3.0"` for v3 assets.
- v2 segmentation assets remain valid when included in a v3 bundle.
- A v3 bundle MAY contain v2 assets unchanged; their `derived_from` is the
  primary trace.

---

## 8. Schema Drafting Tasks

Each schema is a JSON Schema Draft 2020-12 file under `spec/schema/v3/`. They
overlay the existing v2 `asset.schema.json` (do not fork it).

| Task ID | File | Purpose |
|---|---|---|
| SCH-1 | `spec/schema/v3/camera-rig.schema.json` | Validates `kind: "camera-rig"` + `rig` block. |
| SCH-2 | `spec/schema/v3/event.schema.json` | Validates `kind: "event"` + `event` block fields specific to events. |
| SCH-3 | `spec/schema/v3/observation.schema.json` | Validates `kind: "observation"` + per-observation event fields. |
| SCH-4 | `spec/schema/v3/evidence-bundle.schema.json` | Validates `kind: "evidence-bundle"` + `bundle` block. |
| SCH-5 | `spec/schema/v3/common-defs.schema.json` | Shared `$defs`: `time_base`, `sync_class`, `license`, `provenance`. |
| SCH-6 | `spec/schema/v3/index.json` | Lists all v3 schemas with stable URIs (placeholder host OK). |

Each schema task acceptance:

- Loads with `jsonschema` (Python) and `ajv` (TypeScript) without errors.
- Has at least one positive and one negative example under
  `spec/examples/v3/`.
- Uses `$ref` into v2 schemas where appropriate; does not duplicate v2 fields.

---

## 9. Python PoC Tasks

All Python work lives under `sdk/python/spatial_asset_v2/v3/` (a v3 sub-package
inside the v2 SDK to avoid a parallel package release in this milestone).

| Task ID | Module | Purpose |
|---|---|---|
| PY-1 | `v3/models.py` | Typed dataclasses / TypedDicts for `CameraRig`, `Event`, `Observation`, `EvidenceBundle`. |
| PY-2 | `v3/validators.py` | `validate_v3_asset(d)`, `validate_bundle(d)`, `validate_traceability(bundle, assets)`. |
| PY-3 | `v3/bundle.py` | `bundle_evidence(asset_ids, license, provenance, *, store) -> dict`; deterministic canonical JSON. |
| PY-4 | `v3/resolve.py` | `resolve_bundle(path_or_id, *, store) -> ResolvedBundle` with rig, event, observations, derived[]. |
| PY-5 | `v3/fingerprint.py` | `rig_fingerprint(rig_dict) -> str` (SHA-256 over canonical calibration). |
| PY-6 | `v3/cli.py` | `python -m spatial_asset_v2.v3 validate <path>` and `bundle <event_id>`. |
| PY-7 | `v3/__init__.py` | Re-exports public API; documents stability level. |

Acceptance for the Python PoC as a whole:

- `pytest tests/v3/` passes locally and in CI.
- A worked example under `samples/v3/` produces a sealed bundle whose JSON is
  byte-stable across two runs.
- Public API is documented in `sdk/python/README.md` under a "v3 (preview)"
  heading.

---

## 10. TypeScript / Viewer / Resolver Tasks

All TypeScript work lives under `sdk/typescript/src/v3/`.

| Task ID | Module | Purpose |
|---|---|---|
| TS-1 | `src/v3/types.ts` | Shared types for v3 kinds, blocks, and bundle. |
| TS-2 | `src/v3/validate.ts` | Ajv-based validators mirroring Python's `validate_v3_asset` and `validate_bundle`. |
| TS-3 | `src/v3/resolve.ts` | `resolveBundle(json, loader)` that returns `{ rig, event, observations, derived }`. |
| TS-4 | `src/v3/viewerAdapter.ts` | Adapter that picks one observation and feeds the existing v2 viewer entry point. |
| TS-5 | `src/v3/fingerprint.ts` | TS port of rig fingerprint; must match Python output bit-for-bit on shared fixtures. |
| TS-6 | `src/v3/index.ts` | Public re-exports, marked `@preview`. |

Viewer scope is intentionally narrow for the PoC: no new rendering UI. The
viewer adapter MUST be a thin shim over the v2 viewer; if the v2 viewer needs
changes, that is itself a ticket and MUST be added under "Recommended File
Additions" before work proceeds.

Acceptance for TypeScript PoC as a whole:

- `npm test` passes for v3 modules.
- Cross-language fixture: rig fingerprint computed in Python and TypeScript on
  the same JSON produces the same hex digest.
- Public API is documented in `sdk/typescript/README.md` under a
  "v3 (preview)" heading.

---

## 11. Test Strategy

### 11.1 Layers

- **Schema tests** — every v3 schema validates positive examples and rejects
  malformed ones (one negative case per required constraint).
- **Round-trip tests** — parse → validate → serialize → re-parse yields equal
  canonical JSON.
- **Cross-language fixture tests** — shared fixtures under
  `tests/v3/fixtures/` exercised by both Python (`pytest`) and TypeScript
  (`vitest` or existing runner).
- **Traceability tests** — synthesized bundles whose derived assets do or do
  not all trace to observations, asserting validator behavior.
- **License preservation tests** — ingest a bundle, export it, assert SPDX and
  attribution are byte-equal.
- **Drift detection test** — two synthetic rigs with one extrinsic perturbed
  yield different `rig.fingerprint`s; identical rigs yield equal fingerprints.

### 11.2 What we deliberately don't test in PoC

- Performance scaling beyond the 4-camera × 5-second bundle target.
- Real camera hardware or capture timing.
- Real segmentation models (mock outputs are sufficient).

### 11.3 CI

- Existing CI must add a `v3` test job that runs schema + Python + TypeScript
  v3 tests.
- A failing v3 job MUST NOT block v2 publication jobs (jobs run in parallel,
  fail independently).

---

## 12. Public Dataset Handling and License Caution

v3 intentionally makes license a first-class field on every bundle. This brief
adds the following rules for any public dataset used in this repo's samples,
tests, or fixtures:

- **DO NOT vendor data without a redistribution-friendly license** (CC-BY,
  CC-BY-SA, CC0, MIT-style, public-domain). When in doubt, do not vendor.
- **DO record provenance** for every sample under `samples/v3/<name>/PROVENANCE.md`
  with: source URL, original license, SPDX identifier, accessed date, any
  modifications, attribution string.
- **DO check before download.** Before pulling a dataset, verify the license
  text on the dataset's canonical page; do not rely on third-party mirrors.
- **DO redact identifying content where required.** If a dataset's license
  permits research use only, do not include it in the public repo; reference it
  by URL with a fetch script and a `LICENSE-NOTICE` file.
- **DO NOT commit raw faces, license plates, or other PII** into the repo even
  when license technically allows it; emit synthetic stand-ins instead.
- **DO mark synthetic data clearly** in `PROVENANCE.md` with `source: synthetic`
  and a generation script reference.
- **DO test license preservation.** A test MUST fail if a sample bundle's SPDX
  identifier is missing on round-trip.

When unsure, prefer **synthetic data** (rendered Stanford Bunny multi-view, or
ShapeNet items with explicit redistribution rights, or programmatically
generated point clouds). The PoC does not need real-world inspection footage.

---

## 13. Out of Scope (Explicit)

The following are **explicitly out of scope** for the v3 PoC milestone. Tickets
referencing these items SHOULD be deferred to a later milestone with an issue
link rather than expanded into this PoC.

- Real-time streaming of events or observations.
- Multi-rig handoff (two rigs observing one event).
- Geospatial / EPSG-based event location beyond what v2 already permits.
- Encryption, DRM, or signed bundles beyond plain SHA-256 checksums.
- A new viewer UI or rendering pipeline. v3 reuses the v2 viewer.
- Annotation UIs and labeling tools.
- IANA media type registration for v3 MIME types.
- Schema CDN hosting (placeholder URIs are acceptable in the PoC).
- ROS/ROS2 bag ingestion adapters (a separate effort).
- Performance work beyond N6.
- Translating new docs into ja/zh-CN (existing i18n process applies later).

---

## 14. Recommended File Additions

These are the *only* file additions expected for the v3 PoC. Anything beyond
this list SHOULD be raised as a separate ticket.

```
docs/v3/
  README.md                                    (already exists)
  multi-event-camera-spatial-evidence-profile-v3.md  (already exists)
  claude-code-implementation-brief-v3.md       (this file)

spec/schema/v3/
  camera-rig.schema.json
  event.schema.json
  observation.schema.json
  evidence-bundle.schema.json
  common-defs.schema.json
  index.json

spec/examples/v3/
  camera-rig.example.json
  event.example.json
  observation.example.json
  evidence-bundle.example.json
  evidence-bundle.invalid.example.json   (for negative tests)

sdk/python/spatial_asset_v2/v3/
  __init__.py
  models.py
  validators.py
  bundle.py
  resolve.py
  fingerprint.py
  cli.py

sdk/typescript/src/v3/
  index.ts
  types.ts
  validate.ts
  resolve.ts
  viewerAdapter.ts
  fingerprint.ts

samples/v3/
  bunny-4cam/
    PROVENANCE.md
    rig.json
    event.json
    observation_cam0..3.json
    bundle.json

tests/v3/
  fixtures/                  (shared cross-language)
  test_schema.py
  test_bundle_roundtrip.py
  test_traceability.py
  test_license_preservation.py
  test_fingerprint.py
  test_resolve.py
  v3.test.ts                 (TypeScript runner)
```

---

## 15. Milestone Tickets — M0 to M3

Each ticket below is intended to be pasted directly into a GitHub issue or
handed verbatim to Claude Code. They are self-contained: each names the input
state, the output, and the acceptance check.

### M0 — Drafting & alignment (this milestone)

**M0-T1. Land v3 RFC and brief in `docs/v3/`.**
- *Input:* current main branch.
- *Output:* `docs/v3/multi-event-camera-spatial-evidence-profile-v3.md`,
  `docs/v3/README.md`, `docs/v3/claude-code-implementation-brief-v3.md` on a
  branch, no schema/code changes.
- *Acceptance:* `git status` clean except the three docs; `grep -E "^# "
  docs/v3/*.md` shows expected H1s; README links resolve.

**M0-T2. Confirm out-of-scope list with maintainers.**
- *Input:* §13 of this brief.
- *Output:* PR comment thread with explicit thumbs-up from at least one
  maintainer, OR an updated §13 on the same branch.
- *Acceptance:* PR is mergeable to `main` once §13 is approved.

### M1 — Schemas and examples

**M1-T1. Implement `common-defs.schema.json`.**
- *Input:* §7 of this brief.
- *Output:* `spec/schema/v3/common-defs.schema.json` with `$defs` for
  `time_base`, `sync_class`, `license`, `provenance`.
- *Acceptance:* loads with `jsonschema` 4.x and `ajv` 8.x; referenced from at
  least one peer schema in subsequent tasks.

**M1-T2. Implement `camera-rig.schema.json`.**
- *Input:* M1-T1.
- *Output:* schema validating the `rig` block defined in §7.2.
- *Acceptance:* positive example validates; negative example missing `cameras[]`
  is rejected with a referenceable error path.

**M1-T3. Implement `event.schema.json` and `observation.schema.json`.**
- *Acceptance:* positive examples validate; an observation referencing a
  camera_id not present in its rig is rejected by the *traceability* validator
  (not by the schema itself).

**M1-T4. Implement `evidence-bundle.schema.json` and `index.json`.**
- *Acceptance:* sealed bundle example validates; bundle without
  `bundle.license.spdx_id` is rejected.

**M1-T5. Author positive and negative examples in `spec/examples/v3/`.**
- *Acceptance:* every schema has ≥1 positive and ≥1 negative example exercised
  in tests.

### M2 — Python PoC

**M2-T1. Land `v3/models.py` and `v3/validators.py`.**
- *Input:* M1.
- *Acceptance:* `validate_v3_asset` round-trips all positive examples and
  rejects all negative examples with descriptive errors.

**M2-T2. Land `v3/fingerprint.py` and cross-language fixtures.**
- *Acceptance:* deterministic SHA-256 over canonical calibration; fixture
  digests stored under `tests/v3/fixtures/` and consumed by TS in M3.

**M2-T3. Land `v3/bundle.py` (`bundle_evidence`).**
- *Acceptance:* bundle JSON is byte-stable across two runs on the same input;
  `bundle.contents[]` is deduplicated and ordered (rig → event → observations →
  derived).

**M2-T4. Land `v3/resolve.py` (`resolve_bundle`).**
- *Acceptance:* given a bundle JSON path, returns rig, event, observations, and
  derived arrays in the same order they appear in `contents[]`.

**M2-T5. Land traceability validator and license-preservation test.**
- *Acceptance:* tests in `tests/v3/test_traceability.py` and
  `tests/v3/test_license_preservation.py` pass; both fail on intentionally
  broken fixtures.

**M2-T6. Land `v3/cli.py` and document under `sdk/python/README.md`.**
- *Acceptance:* `python -m spatial_asset_v2.v3 validate samples/v3/bunny-4cam/bundle.json`
  exits 0; with a tampered bundle exits non-zero with a clear message.

### M3 — TypeScript PoC and viewer adapter

**M3-T1. Land `src/v3/types.ts` and `src/v3/validate.ts`.**
- *Acceptance:* parity with Python on all positive/negative examples.

**M3-T2. Land `src/v3/fingerprint.ts`.**
- *Acceptance:* digests match Python on shared fixtures; CI test asserts
  cross-language equality.

**M3-T3. Land `src/v3/resolve.ts`.**
- *Acceptance:* `resolveBundle` returns the same ordered structure as Python's
  `resolve_bundle` on shared fixtures.

**M3-T4. Land `src/v3/viewerAdapter.ts`.**
- *Acceptance:* given a bundle and a chosen `camera_id`, the adapter feeds the
  existing v2 viewer entry point with no v2 source changes; a smoke test
  imports the adapter and confirms the v2 entry point is callable with the
  selected observation.

**M3-T5. CI integration.**
- *Acceptance:* a `v3` job runs schema, Python, and TS tests on PRs; failure
  in `v3` job does not fail v2 publication jobs.

**M3-T6. Update `docs/v3/README.md` and root `README.md` "What's next" section.**
- *Acceptance:* `docs/v3/README.md` lists schemas, examples, SDK entry points,
  and the brief; root README mentions v3 as a preview track.

---

## 16. Acceptance Criteria Index

This is a flat index of every numbered acceptance criterion in this document
for quick reference by reviewers and agents.

| Reference | What is being accepted |
|---|---|
| S1 | Bundle round-trip is byte-stable. |
| S2 | v3 bundle containing v2 segmentation assets validates under both. |
| S3 | TS viewer renders observations via the v2 viewer. |
| S4 | Traceability validator reaches an observation from every derived asset. |
| S5 | SPDX and attribution survive ingest+export. |
| S6 | Docs, schemas, examples, tests pass CI. |
| F1–F14 | Functional requirements, table in §5. |
| N1–N10 | Non-functional requirements, table in §6. |
| SCH-1..6 | Schema drafting tasks, §8. |
| PY-1..7 | Python PoC tasks, §9. |
| TS-1..6 | TypeScript PoC tasks, §10. |
| M0-T1..M3-T6 | Milestone tickets, §15. |

---

## 17. Risk and Open Issue Log

| ID | Item | Likelihood | Impact | Owner | Notes |
|---|---|---|---|---|---|
| R1 | v2 viewer entry point may not accept a single observation cleanly. | Medium | Medium | TS lead | If true, raise a separate ticket *before* M3-T4; do not modify v2 viewer in PoC. |
| R2 | `time_base` enum may need refinement (e.g., `gps`, `unix-ns`). | Medium | Low | Spec lead | Tracked as open issue; PoC ships with the four values in §7.2. |
| R3 | Cross-language fingerprint determinism (key ordering, float canonicalization). | High | High | Python+TS leads | Fingerprint test is the gate; specify the canonicalization explicitly in `fingerprint.py` and `fingerprint.ts`. |
| R4 | Public datasets with ambiguous license get vendored. | Medium | High | Reviewer | §12 rules + CI check on `PROVENANCE.md` presence in `samples/v3/*`. |
| R5 | Schema drift between v3 overlays and existing v2 schemas. | Medium | Medium | Schema lead | Use `$ref`; do not duplicate v2 fields. |
| R6 | Multi-rig events demanded mid-milestone. | Low | Medium | Spec lead | Out of scope per §13; capture demand in an issue, defer. |
| R7 | Bundle addressing (content-hash vs asset-id) bikeshed delays M2. | Medium | Low | Spec lead | PoC uses asset-id addressing; revisit post-M3. |
| R8 | Viewer adapter accidentally pulls a browser-only dep into core. | Low | High | TS lead | Enforced by N5 and a test that imports `src/v3/index.ts` in Node. |
| R9 | Privacy / redaction needs (faces, plates) appear late. | Medium | Medium | Spec lead | Out of scope for PoC; add `bundle.redaction` open issue under R-Open. |
| R10 | Performance budget N6 is missed on slow disks. | Low | Low | Python lead | Cache schema compilation; profile only if violated. |

### Open issues (R-Open)

- **OI-1.** Should `evidence-bundle.bundle.contents[]` be content-addressed
  (hash of canonical contents) or asset-id addressed? — RFC §13.
- **OI-2.** Do we need a `bundle.redaction` block? — RFC §13.
- **OI-3.** v2 → v3 migration story for pipelines without an explicit event. —
  RFC §13.
- **OI-4.** Should `rig.fingerprint` cover lens distortion model parameters by
  default, or only intrinsics+extrinsics? — §7.
- **OI-5.** Naming: is "evidence" the right word, or "capture-bundle"? —
  RFC §10.

---

*End of Claude Code Implementation Brief — v3 Multi-Event, Multi-Camera Spatial Evidence Profile*
