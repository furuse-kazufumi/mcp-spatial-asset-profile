# Contributing to MCP Spatial Asset Profile v2

Thank you for your interest in improving **MCP Spatial Asset Profile Version 2.0** (referred to throughout this repository as **MCP Spatial Asset Profile v2**). This is an open Proof of Concept and we welcome contributions from anyone — language, time zone, or background. The notes below describe how to participate productively.

**Languages / 言語 / 语言:** **English** · [日本語](#日本語ガイド) · [简体中文](#简体中文指南)

---

## Where to bring what

| If you want to … | Use |
|---|---|
| Ask a question, share an idea, or float a half-formed proposal | [GitHub Discussions](https://github.com/furuse-kazufumi/mcp-spatial-asset-profile/discussions) |
| Report a concrete bug in the spec, schema, SDK, or examples | [Issue → Bug report](https://github.com/furuse-kazufumi/mcp-spatial-asset-profile/issues/new/choose) |
| Request a new feature, asset kind, or capability | [Issue → Feature request](https://github.com/furuse-kazufumi/mcp-spatial-asset-profile/issues/new/choose) |
| Propose a normative change to the spec | [Issue → Spec discussion](https://github.com/furuse-kazufumi/mcp-spatial-asset-profile/issues/new/choose), then PR |
| Submit code, schema, example, or doc changes | Pull request |

For larger or normative changes (anything that touches `spec/` or `spec/schema/`), please open an issue or Discussion first so the direction can be agreed before code is written.

---

## Scope of contribution

Contributions are welcome across the whole repository. The most common areas are:

- **Specification** (`spec/spatial-asset-profile-v2.md`, `spec/segmentation-workflow-v2.md`) — clarifications, corrections, additional asset kinds, capability vocabulary.
- **JSON Schema** (`spec/schema/`) — bug fixes, tightening of constraints, support for newly-specified fields. Schemas use JSON Schema Draft 2020-12.
- **Canonical examples** (`spec/examples/`) — every change to schema or spec should be reflected here so examples stay valid against the schema.
- **Python SDK** (`sdk/python/`) and **TypeScript SDK** (`sdk/typescript/`) — reference implementations. Both must remain in sync with the schema and with each other for interoperability tests to pass.
- **Documentation** (`docs/`, `README.md`, `README.ja.md`, `README.zh-CN.md`, `docs/i18n/`) — improvements, translations, additional language summaries.
- **Tests** (`tests/`) — schema tests, roundtrip tests, cross-SDK interoperability tests.

If you are unsure where a change belongs, open a Discussion and we will help route it.

---

## Design principles to keep in mind

The project intentionally evolves under a small set of constraints. Please keep these in mind when proposing changes:

1. **Additive v2.** v2 is a strict superset of v1. New fields are added, existing fields are not silently changed. Field renames or removals require a version bump and a migration note.
2. **Traceability.** Every derived asset must keep its lineage via `derived_from` and, where applicable, `workflow.target_asset_id`. The multi-view segmentation workflow depends on this — please do not introduce shortcuts that bypass it.
3. **Envelope, not payload.** The profile carries metadata that lets tools find, interpret, and trace a payload. Heavy payload formats stay behind URIs. New fields should be small, machine-readable, and clearly named.
4. **Interoperability between SDKs.** Python and TypeScript SDKs are reference implementations and are validated against each other. A change in one SDK that affects on-the-wire JSON must land in the other in the same PR (or with a tracking issue if scope makes that impractical).
5. **Spec, schema, examples, SDKs stay consistent.** A spec change that has no schema/example/SDK companion is incomplete. A schema change with no example update will fail the interoperability tests.

---

## How to propose a change

### Small fixes (typos, broken links, doc improvements, single-line clarifications)

Open a PR directly. No prior issue is needed.

### Schema, example, or SDK changes

1. Fork and create a topic branch.
2. Update the relevant files. Keep the change set focused — one concern per PR.
3. **Update spec, schema, examples, and both SDKs together** if the change is observable on the wire.
4. Run the validation steps below locally.
5. Open a PR. The PR template will ask you to confirm consistency across spec / schema / examples / SDKs.

### Specification proposals

1. Open a **Spec discussion** issue describing motivation, proposed wording, and impact on existing fields.
2. Once direction is agreed, submit a PR that updates spec text first, then schema, then examples, then SDKs.
3. Treat additive proposals as the default; subtractive or renaming proposals need a stronger justification and a migration note.

---

## Running tests locally

The same checks that CI runs can be reproduced locally. Anything reasonable to validate before opening a PR helps reviewers move faster.

### JSON Schema and examples

```bash
# Quick parse check on schemas and examples
python -c "import json, glob; [json.load(open(f)) for f in glob.glob('spec/schema/*.json') + glob.glob('spec/examples/*.json')]"
```

### Python SDK

```bash
cd sdk/python
pip install -e ".[dev]"
pytest tests/ -v
```

### TypeScript SDK

```bash
cd sdk/typescript
npm install
npm run build
npm test
```

### Repository-level tests

```bash
# From repo root, after Python SDK is installed
pytest tests/ -v
```

This runs schema tests, roundtrip tests, and cross-SDK interoperability tests.

---

## Pull request expectations

The PR template (`.github/PULL_REQUEST_TEMPLATE.md`) is the shortest accurate version of these expectations. In summary:

- Spec, schema, examples, and SDKs are updated together when the change is observable on the wire.
- New fields are additive; v1 assets continue to migrate cleanly.
- Tests are updated or added as needed and pass locally.
- Documentation (README sections, `docs/`, language variants where applicable) reflects the change.
- Traceability fields (`derived_from`, `workflow.target_asset_id`) are preserved for any new derived asset kind.

PRs do not need to be in English — Japanese and Simplified Chinese are also fine. Reviewers will translate if needed.

---

## Multilingual contributions

Documentation in this repository is maintained in English (primary), Japanese, and Simplified Chinese, with brief summaries in Korean, Spanish, and French under `docs/i18n/`. We welcome:

- Translation fixes in any of the existing languages.
- New language summaries under `docs/i18n/` (please follow the existing summary length and structure).
- Issue and PR descriptions in your strongest language.

When updating one of `README.md`, `README.ja.md`, or `README.zh-CN.md`, please update the language navigation block and try to keep the corresponding sections in step. If you can only update one language, that is still welcome — note in the PR which language pairs are still pending and a maintainer or another contributor can follow up.

---

## Code of Conduct

By participating in this project you agree to abide by the [Code of Conduct](CODE_OF_CONDUCT.md).

---

## License

By contributing, you agree that your contributions will be licensed under the [MIT License](LICENSE) that covers this project.

---

## 日本語ガイド

**MCP Spatial Asset Profile v2** への貢献を歓迎します。本プロジェクトはオープンな Proof of Concept であり、誰でも参加できます。

- **質問・アイデア・初期段階の提案** → [GitHub Discussions](https://github.com/furuse-kazufumi/mcp-spatial-asset-profile/discussions)
- **バグ報告・機能要望・仕様議論** → Issue（テンプレートから選択）
- **コード／スキーマ／サンプル／ドキュメント変更** → Pull Request

設計原則:

1. **追加的（additive）な v2** — v1 アセットは情報損失なく v2 に移行可能です。
2. **トレーサビリティ** — 派生アセットは必ず `derived_from` と `workflow.target_asset_id` で系譜を保持します。
3. **エンベロープであってペイロードではない** — 重い実体は URI 先にあり、プロファイルはメタデータのみを保持します。
4. **SDK 間の相互運用性** — Python / TypeScript の両 SDK は同期して更新します。
5. **仕様・スキーマ・サンプル・SDK の整合性** — オンザワイヤに影響する変更は 4 者を同時に更新します。

ローカルで実行できる検証コマンドは英語セクションを参照してください。Issue / PR は日本語でも歓迎します。

仕様（`spec/`）に触れる大きめの変更は、まず Issue / Discussion で方向性を合意してから PR を出していただけると助かります。

---

## 简体中文指南

欢迎为 **MCP Spatial Asset Profile v2** 做出贡献。本项目是一个开放的概念验证，欢迎任何人参与。

- **提问、想法、初步提案** → [GitHub Discussions](https://github.com/furuse-kazufumi/mcp-spatial-asset-profile/discussions)
- **Bug 报告、功能请求、规范讨论** → 通过 Issue 模板提交
- **代码 / Schema / 示例 / 文档变更** → 提交 Pull Request

设计原则：

1. **增量式（additive）v2** —— v1 资产可无损升级到 v2。
2. **可追溯性** —— 派生资产通过 `derived_from` 与 `workflow.target_asset_id` 保留血缘。
3. **是信封而非载荷** —— 庞大数据位于 URI 之后，Profile 仅承载元数据。
4. **SDK 之间的互操作性** —— Python / TypeScript 两个 SDK 同步更新。
5. **规范、Schema、示例、SDK 之间保持一致** —— 任何影响线上格式的变更须四者同时更新。

本地验证命令请参见英文章节。Issue / PR 可使用中文。

涉及 `spec/` 的较大变更，请先通过 Issue 或 Discussion 商定方向，再提交 PR。
