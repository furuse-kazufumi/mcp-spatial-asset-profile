<!--
Thank you for contributing to MCP Spatial Asset Profile v2!

PRs do not need to be in English — Japanese and Simplified Chinese are also fine.
For larger spec / schema changes, please link the related issue or Discussion thread.
-->

## Summary

<!-- One or two sentences on what this PR changes and why. -->

## Type of change

<!-- Tick all that apply. -->

- [ ] Spec text (`spec/spatial-asset-profile-v2.md`, `spec/segmentation-workflow-v2.md`)
- [ ] JSON Schema (`spec/schema/`)
- [ ] Canonical example (`spec/examples/`)
- [ ] Python SDK (`sdk/python/`)
- [ ] TypeScript SDK (`sdk/typescript/`)
- [ ] Tests (`tests/`)
- [ ] Documentation (`README*.md`, `docs/`, `docs/i18n/`)
- [ ] CI / repository tooling (`.github/`)

## Linked issue / discussion

<!-- e.g. Closes #123, Discusses #45 -->

## Consistency checklist

- [ ] **Spec ↔ schema ↔ examples ↔ SDKs are in sync.** Any change observable on the wire is reflected in all four where applicable.
- [ ] **Schemas validate.** `spec/schema/*.json` files parse as JSON and existing examples still validate against them.
- [ ] **Both reference SDKs updated** (Python and TypeScript), or a follow-up issue is filed if scope makes that impractical.
- [ ] **Cross-SDK interoperability tests pass** (`tests/interoperability/`, run via `pytest tests/`).

## Backward compatibility / additive design

- [ ] Change is **additive to v2** — no existing field is silently renamed, removed, or repurposed.
- [ ] v1 → v2 auto-migration still succeeds for existing v1 assets.
- [ ] If the change is not additive, a migration note is included and the rationale is described above.

## Traceability

- [ ] For any new derived asset kind or workflow step, lineage is preserved via `derived_from` and `workflow.target_asset_id`.
- [ ] Multi-view segmentation workflow (rendered-view → segmentation-mask-2d → segmentation-mask-3d → object-asset) is not broken by this change.

## Tests

- [ ] `pytest tests/ -v` passes locally (schema, roundtrip, interoperability).
- [ ] `cd sdk/python && pytest tests/ -v` passes.
- [ ] `cd sdk/typescript && npm run build && npm test` passes.
- [ ] New tests added where appropriate.

## Documentation

- [ ] README sections updated if user-facing behavior changed.
- [ ] Japanese (`README.ja.md`) and Simplified Chinese (`README.zh-CN.md`) variants updated, or follow-up noted.
- [ ] `docs/` updated if architecture, migration, or implementation plan is affected.

## Notes for reviewers

<!-- Anything reviewers should pay particular attention to: tricky edge cases, open questions, follow-ups. -->
