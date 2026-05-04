# MCP Spatial Asset Profile v2

[![CI](https://github.com/furuse-kazufumi/mcp-spatial-asset-profile/actions/workflows/ci.yml/badge.svg)](https://github.com/furuse-kazufumi/mcp-spatial-asset-profile/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Status: PoC](https://img.shields.io/badge/status-Proof_of_Concept-orange.svg)](#项目状态)
[![Spec: v2.0.0](https://img.shields.io/badge/spec-v2.0.0-informational.svg)](spec/spatial-asset-profile-v2.md)

**语言 / Languages / 言語：** [English](README.md) · [日本語](README.ja.md) · **简体中文** · [한국어 (요약)](docs/i18n/README.ko.md) · [Español (resumen)](docs/i18n/README.es.md) · [Français (résumé)](docs/i18n/README.fr.md)

---

**MCP Spatial Asset Profile Version 2.0**（在本仓库中简称 **MCP Spatial Asset Profile v2**）是一种基于 JSON 的封装格式，用于在 [Model Context Protocol (MCP)](https://modelcontextprotocol.io/) 工具生态中表示三维与空间数据资产。

它构建于 **[mcp-3d v1](https://github.com/puruyan2525/mcp-3d)**（Claude Code，2025 年 4 月）之上，并采用**严格增量（additive）** 的方式扩展：每一个 v1 资产都可无损地升级到 v2，而 v2 引入了具备完整溯源能力的一等公民分割工作流。

## 项目状态

> **概念验证（Proof of Concept）** —— 规范及参考 SDK（Python 与 TypeScript）已可用于原型开发与互操作性实验。格式尚未冻结，在 v2.1 之前我们明确欢迎来自实际 MCP 集成的反馈。

| 组件 | 状态 |
|---|---|
| 规范（`spec/spatial-asset-profile-v2.md`） | 草案，已完成 |
| JSON Schema（Draft 2020-12） | 全 8 种资产类型已完成 |
| Python SDK | 参考实现，已测试 |
| TypeScript SDK | 参考实现，已测试 |
| 示例资产与跨 SDK 互操作 | 由 `tests/` 覆盖 |

**包与发布**

- PyPI: [`mcp-spatial-asset-profile`](https://pypi.org/project/mcp-spatial-asset-profile/) *(发布就绪，首次发布待执行)*
- npm: [`@furuse-kazufumi/mcp-spatial-asset-profile`](https://www.npmjs.com/package/@furuse-kazufumi/mcp-spatial-asset-profile) *(发布就绪，首次发布待执行)*
- GitHub 发布: [`v0.1.0-poc`](https://github.com/furuse-kazufumi/mcp-spatial-asset-profile/releases/tag/v0.1.0-poc)
- 发布指南: [`docs/package-publication.md`](docs/package-publication.md)

---

## 这个 Profile 是什么？

MCP Spatial Asset Profile v2 是 MCP 工具之间交换三维 / 空间数据时使用的**信封（元数据层）**。真正庞大的载荷（点云、网格、splat、掩膜）位于 URI 之后；Profile 仅承载用于**发现、解释与追溯**这些载荷所需的信息。

v2 在 v1 核心之上扩展了：

- **全局稳定的 `asset_id`** —— 基于 URN，跨流水线保持稳定。
- **正式的 `spatial` 块** —— 将坐标 `frame`、`axis`、`handedness`、`unit`、`bounds` 集中于一处。
- **viewpoints**（相机内外参）—— 用于渲染与投影。
- **URI 能力协商** —— 客户端可选择实际可消费的最佳表示。
- **一等公民的分割工作流** —— `rendered-view` → `segmentation-mask-2d` → `segmentation-mask-3d` → `object-asset`，全程通过 `derived_from` 与 `workflow.target_asset_id` 串联。
- **完整的资产图溯源** —— 每一个派生资产都携带其血缘。

---

## 支持的资产类型

| 类型（`kind` 值） | 说明 |
|---|---|
| `point-cloud` | 三维点集（PLY、PCD、LAS、NPY） |
| `mesh` | 多边形表面网格（OBJ、glTF、GLB） |
| `gaussian-splat` | 三维 Gaussian Splatting 场景 |
| `depth-image` | 二维深度／距离图（16-bit PNG、EXR） |
| `rendered-view` | 来自某视点的 RGB / RGB-D 渲染 *(v2 新增)* |
| `segmentation-mask-2d` | 像素级分割掩膜 *(v2 新增)* |
| `segmentation-mask-3d` | 逐点 / 逐面三维标签 *(v2 新增)* |
| `object-asset` | 已抽取的分割对象实例 *(v2 新增)* |

所有类型共享同一信封，仅在所声明的 `representations` 与类型特定字段上有所不同。

---

## 分割工作流

![多视角分割工作流](docs/assets/slides/fig_02_pipeline.png)

完整的说明图（架构、四种表示对比、分割结果）请参见
[`docs/slides-v2.md`](docs/slides-v2.md) 与
[`docs/assets/slides/`](docs/assets/slides/)。

```
源资产（point-cloud / mesh / gaussian-splat）
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

每一步都生成一个独立的 v2 资产。溯源通过两条路径保持：

- `derived_from` —— 直接父资产。
- `workflow.target_asset_id` —— 整条链最终所分割的**原始资产**。

该设计为**多视角分割**预留了空间：多个 `rendered-view` / `segmentation-mask-2d` 可被提升至同一个共享的 `segmentation-mask-3d`，而每一中间步骤仍可独立查看。

---

## 仓库结构

```
mcp-spatial-asset-profile/
├── README.md                       ← 英文落地页
├── README.ja.md                    ← 日本語版
├── README.zh-CN.md                 ← 本文件（简体中文）
├── docs/
│   ├── i18n/                       ← 简要摘要（KO / ES / FR）
│   ├── implementation-plan-v2.md
│   ├── reference-architecture-v2.md
│   ├── migration-from-v1.md
│   ├── publication-plan-v2.md
│   └── slides-v2.md
├── spec/
│   ├── spatial-asset-profile-v2.md       ← v2 核心规范
│   ├── segmentation-workflow-v2.md       ← 分割工作流扩展
│   ├── schema/                           ← JSON Schema（Draft 2020-12）
│   └── examples/                         ← 标准示例资产
├── sdk/
│   ├── python/                     ← Python SDK（`spatial-asset-v2`）
│   └── typescript/                 ← TypeScript SDK（`spatial-asset-v2`）
├── samples/                        ← 示例载荷（沿用自 v1）
└── tests/                          ← Schema、往返、互操作测试
```

---

## 快速开始

### 仅使用 JSON Schema

Schema 可与任何 JSON Schema 2020-12 验证器（如 `ajv`、`jsonschema`）独立配合使用：

```bash
# spec/schema/asset.schema.json 是主 schema
# spec/examples/*.json 是标准实例
```

### Python SDK

PyPI 包名为 **[`mcp-spatial-asset-profile`](https://pypi.org/project/mcp-spatial-asset-profile/)**（导入名仍为 `spatial_asset_v2`）。

```bash
# PyPI 发布后:
pip install mcp-spatial-asset-profile
# 启用 JSON Schema 验证:
pip install "mcp-spatial-asset-profile[validate]"
```

从仓库源码使用:

```bash
cd sdk/python
pip install -e ".[dev]"

# 验证示例资产
python -m spatial_asset_v2.cli.main validate ../../spec/examples/pointcloud-asset.json

# 生成示例资产
python -m spatial_asset_v2.cli.main generate --output /tmp/samples

# 端到端运行模拟分割流水线
python -m spatial_asset_v2.cli.main workflow \
  --source ../../spec/examples/pointcloud-asset.json \
  --output /tmp/pipeline

# 运行测试
pytest tests/ -v
```

### TypeScript SDK

npm 包名为 **[`@furuse-kazufumi/mcp-spatial-asset-profile`](https://www.npmjs.com/package/@furuse-kazufumi/mcp-spatial-asset-profile)**。

```bash
# npm 发布后:
npm install @furuse-kazufumi/mcp-spatial-asset-profile
```

从仓库源码使用:

```bash
cd sdk/typescript
npm install
npm run build
npm test
```

完整发布流程参见 [`docs/package-publication.md`](docs/package-publication.md)。

---

## 验证与 CI

GitHub Actions（`.github/workflows/ci.yml`）在每次向 `main` 的 push 与 pull request 时执行：

- **Python SDK 与仓库测试** —— Python 3.11 与 3.12，使用 `pytest` 运行 SDK 单元测试以及仓库级别的 schema / 往返 / 互操作测试。
- **TypeScript SDK** —— Node.js 20，执行 `npm run build` 与 `npm test`。

同样的检查也可在本地运行（参见上文“快速开始”）。README 顶部的 CI 徽章反映 `main` 当前状态。

---

## 与 v1 的向后兼容

v2 是 v1 的**严格超集**，迁移可机械完成：

| v1 | v2 | 迁移 |
|---|---|---|
| `id` | `asset_id` | 重命名字段 |
| `crs` | `spatial.frame` | 移入 `spatial` 块 |
| `bounds` | `spatial.bounds` | 移入 `spatial` 块 |
| `version: "1.0"` | `version: "2.0"` | 升级版本字符串 |

两个参考 SDK 在解析时都会自动迁移 v1 资产。详见 [`docs/migration-from-v1.md`](docs/migration-from-v1.md)。

---

## 路线图

PoC 之后的近期优先事项：

1. **多视角分割工作流** —— 形式化将 N 个 `rendered-view` 提升至单个共享 `segmentation-mask-3d` 的过程。
2. **能力词表注册** —— 为表示 `capabilities` 约定共享词汇，使独立工具间可在无须临时字符串的前提下互操作。
3. **流式表示** —— 在信封内描述瓦片化／渐进式载荷（Cesium 3D Tiles、Potree、splat 瓦片）。
4. **参考查看器适配器** —— 基于 TypeScript 适配器接口的最小浏览器查看器，使 Profile 可端到端演示。
5. **v2.1 规范冻结** —— 在外部集成反馈使格式稳定后实施。

亦可参阅 [`docs/implementation-plan-v2.md`](docs/implementation-plan-v2.md) 与 [`docs/publication-plan-v2.md`](docs/publication-plan-v2.md)。

---

## 贡献

本项目是开放的概念验证，欢迎贡献。以下方向的反馈尤其有价值：

- 暴露信封缺口的真实集成。
- Schema 修正、新增资产类型、能力词表提案。
- 翻译与文档改进（请参见 README 顶部的语言导航）。

请先阅读：

- **[CONTRIBUTING.md](CONTRIBUTING.md)** —— 如何提出变更、运行测试，以及保持规范 / Schema / 示例 / SDK 一致。
- **[行为准则（Code of Conduct）](CODE_OF_CONDUCT.md)** —— 社区准则。
- **[GitHub Discussions](https://github.com/furuse-kazufumi/mcp-spatial-asset-profile/discussions)** —— 提问、想法、早期规范提案、实现报告、i18n 协助。欢迎使用中文发表。
- **[docs/community.md](docs/community.md)** —— 各类讨论的归属与规范提案的推进路径。

涉及规范（`spec/`）的较大变更，请先在 Discussion 或 `[spec]` Issue 中商定方向，再提交 PR。

---

## 许可

MIT —— 见 [LICENSE](LICENSE)。

---

## 溯源

本项目构建于 [@puruyan2525](https://github.com/puruyan2525) 的 **[mcp-3d v1](https://github.com/puruyan2525/mcp-3d)** 之上（使用 Claude Code（Anthropic）创建于 2025 年 4 月）。v2 在该 v1 核心之上加入了分割工作流、更丰富的空间元数据以及参考 SDK。
