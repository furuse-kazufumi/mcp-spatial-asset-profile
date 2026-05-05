# MCP Spatial Asset Profile — v3 Working Drafts

**Status:** Working Drafts (RFC)
**Date:** 2026-05

This directory holds the v3 RFC and companion design documents. v3 introduces a
**multi-event, multi-camera spatial evidence** model on top of v2.

These documents are drafts. They are not yet normative. The RFC documents in
this directory are accompanied by an initial PoC drop:

- JSON Schemas (Draft 2020-12): [`../../spec/v3/`](../../spec/v3/)
- Python reference SDK skeleton: [`../../sdk/python/spatial_asset_v3/`](../../sdk/python/spatial_asset_v3/)
- Synthetic debug demo (Layer 1 reference fixture): [`../../samples/v3/synthetic-debug-demo/`](../../samples/v3/synthetic-debug-demo/)
- Tests: `../../tests/test_v3_schemas.py`, `test_v3_pipeline_inject.py`, `test_v3_adapters.py`, `test_v3_vllm.py`

The schemas, SDK skeleton, samples, and tests track the RFC and implementation
brief but are still subject to change as feedback comes in.

## Documents

| Document | Purpose |
|---|---|
| [`multi-event-camera-spatial-evidence-profile-v3.md`](multi-event-camera-spatial-evidence-profile-v3.md) | RFC draft: vocabulary, asset kinds, time/sync model, evidence bundle. |
| [`demo-debug-environment-requirements-v3.md`](demo-debug-environment-requirements-v3.md) | Japanese-first requirements document for the v3 demo/debug environment. Defines the synthetic-first reference fixture, public dataset replay, VLLM explanation demo, debug targets, test strategy, and M2-SYNTH-001 ticket. |
| [`claude-code-implementation-brief-v3.md`](claude-code-implementation-brief-v3.md) | Requirements & design brief for the v3 PoC, with milestone tickets (M0–M3), acceptance criteria, and risk log. Suited for handoff to Claude Code. |

## Reading order

1. Start with the [RFC draft](multi-event-camera-spatial-evidence-profile-v3.md) for vocabulary and rationale.
2. Read the [demo/debug requirements](demo-debug-environment-requirements-v3.md) to understand how v3 will be demonstrated and debugged, starting with the synthetic reference fixture.
3. Read the [implementation brief](claude-code-implementation-brief-v3.md) for what to build, in what order, and how it will be verified.
4. Cross-reference with v2 base specs linked below as needed.

## Status

- v2 (current stable PoC): see [`../../spec/spatial-asset-profile-v2.md`](../../spec/spatial-asset-profile-v2.md) and [`../../spec/segmentation-workflow-v2.md`](../../spec/segmentation-workflow-v2.md).
- v3 (drafting): the documents in this directory.

## Feedback

v3 is being drafted in the open. File issues against the repository for
feedback on terminology, asset kinds, or open questions. The companion
implementation brief tracks open issues alongside its own task list.
