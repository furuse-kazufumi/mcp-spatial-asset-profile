# Community Guide

**MCP Spatial Asset Profile v2** is developed in the open. This page describes where each kind of conversation belongs, so it is easy for newcomers to join and easy for maintainers to follow along.

**Languages / 言語 / 语言:** **English** · [日本語](#日本語) · [简体中文](#简体中文)

---

## Where conversations live

| Channel | Best for |
|---|---|
| **[GitHub Discussions](https://github.com/furuse-kazufumi/mcp-spatial-asset-profile/discussions)** | Open-ended questions, ideas, half-formed proposals, implementation reports, i18n coordination, "is anyone else doing X?" threads. |
| **GitHub Issues** | Concrete bugs, feature requests, and normative spec proposals. Use the issue templates so the right information is captured up front. |
| **Pull Requests** | Code, schema, example, and documentation changes. The PR template captures the spec ↔ schema ↔ examples ↔ SDK consistency checks. |

If you are unsure, start in Discussions. A maintainer or another contributor can help route it to an issue or PR when the direction is clearer.

---

## How to use Discussions

We suggest these categories (create them if not present):

- **Ideas** — early proposals, "what if v2 supported …", capability vocabulary brainstorming.
- **Q&A** — usage questions, "how do I express X with the envelope?", SDK questions.
- **Spec proposals (pre-issue)** — narrative-style writeups that are not yet ready to become a `[spec]` issue. Once the proposal is well-shaped, open a Spec discussion issue and link back.
- **Implementation reports** — share what happened when you integrated the profile into your tool. Real-world reports are exactly the feedback the PoC needs.
- **i18n / translations** — coordinate translations of the README, the `docs/i18n/` summaries, or new language additions.
- **Show & tell** — viewers, demos, sample assets, screenshots.

When you start a thread:

- One topic per thread. Long, multi-topic threads are hard to follow.
- Link related issues / PRs / specs.
- It is fine to write in English, 日本語, or 简体中文 — translations are not required.

---

## How spec proposals progress

1. **Discussion** — narrative writeup, motivation, integration scenarios.
2. **Spec discussion issue** — once direction is roughly agreed, open a `[spec]` issue using the template. Reference the Discussion thread.
3. **PR** — update spec text first, then schema, then examples, then both reference SDKs. The PR template covers the consistency checklist.

This staged path lets contributors with different skill sets help at the stage that suits them — writers in step 1 and 2, schema authors and SDK maintainers in step 3.

---

## How to help if you have …

- **A few minutes.** Translate a small section of `README.ja.md` or `README.zh-CN.md`, or fix a typo. PRs are welcome directly.
- **An hour.** Triage Discussions, answer a Q&A thread, or propose a missing example asset under `spec/examples/`.
- **A weekend.** Implement a missing capability in either SDK and add an interoperability test. Or write a new language summary under `docs/i18n/`.
- **A real integration.** Share an implementation report in Discussions describing what worked, what was awkward, and which envelope fields were missing. This is the most valuable feedback the PoC can receive before v2.1.

---

## Maintainers and decision-making

While the project is in PoC, decisions about the spec are made by the repository maintainers, taking community input from Discussions and issues into account. The bar for normative changes is:

1. **Additive by default** — additive changes are preferred and easier to land.
2. **Spec, schema, examples, both SDKs stay consistent** — a change that lands in only one of these is incomplete.
3. **Traceability is preserved** — `derived_from` and `workflow.target_asset_id` are not bypassed by new asset kinds or workflow steps.

Once v2.1 is frozen, this section will be revisited and a clearer governance model documented.

---

## 日本語

**MCP Spatial Asset Profile v2** はオープンに開発されています。会話の置き場所は次の通りです。

| 場所 | 用途 |
|---|---|
| [GitHub Discussions](https://github.com/furuse-kazufumi/mcp-spatial-asset-profile/discussions) | 質問、アイデア、初期段階の提案、実装報告、i18n の相談 |
| GitHub Issues | 具体的なバグ、機能要望、仕様提案 |
| Pull Requests | コード／スキーマ／サンプル／ドキュメント変更 |

迷ったら Discussions から始めてください。

仕様提案の進め方:

1. **Discussion** で動機と統合シナリオを書く。
2. 方向性が見えたら **Spec discussion issue**（テンプレートあり）に昇格させる。
3. **PR** で仕様 → スキーマ → サンプル → 両 SDK の順に更新する。

実利用統合の報告は、PoC が最も必要としているフィードバックです。日本語の投稿も歓迎します。

---

## 简体中文

**MCP Spatial Asset Profile v2** 在公开环境中开发。讨论位置如下：

| 渠道 | 用途 |
|---|---|
| [GitHub Discussions](https://github.com/furuse-kazufumi/mcp-spatial-asset-profile/discussions) | 提问、想法、初步提案、实现报告、i18n 协调 |
| GitHub Issues | 具体 Bug、功能请求、规范提案 |
| Pull Requests | 代码 / Schema / 示例 / 文档变更 |

不确定时请先在 Discussions 发起讨论。

规范提案的推进路径：

1. **Discussion** 撰写动机与集成场景。
2. 方向明确后，使用模板提交 **Spec discussion issue**。
3. 通过 **PR** 依次更新：规范文本 → Schema → 示例 → 两个参考 SDK。

来自真实集成的实现报告是 PoC 阶段最需要的反馈。欢迎使用中文发表。
