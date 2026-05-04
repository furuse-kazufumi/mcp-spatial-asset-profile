# MCP Spatial Asset Profile v2 — Résumé en français

**Langues :** [English](../../README.md) · [日本語](../../README.ja.md) · [简体中文](../../README.zh-CN.md) · [한국어](README.ko.md) · [Español](README.es.md) · **Français**

**MCP Spatial Asset Profile Version 2.0** (désigné **MCP Spatial Asset Profile v2** dans ce dépôt) est un format d'enveloppe basé sur JSON pour représenter des actifs de données 3D et spatiales dans l'écosystème d'outils du [Model Context Protocol (MCP)](https://modelcontextprotocol.io/).

Il s'appuie sur **[mcp-3d v1](https://github.com/puruyan2525/mcp-3d)** (Claude Code, avril 2025) de manière **strictement additive** : tout actif v1 peut être mis à niveau vers v2 sans perte d'information.

## Principales nouveautés

- `asset_id` globalement stable, basé sur URN.
- Bloc `spatial` formel : `frame`, `axis`, `handedness`, `unit`, `bounds`.
- `viewpoints` avec paramètres intrinsèques / extrinsèques de caméra.
- Négociation de capacités par URI pour les représentations.
- Flux de segmentation de première classe : `rendered-view` → `segmentation-mask-2d` → `segmentation-mask-3d` → `object-asset`, traçabilité complète via `derived_from` et `workflow.target_asset_id`.

## Types d'actif pris en charge

`point-cloud`, `mesh`, `gaussian-splat`, `depth-image`, `rendered-view`, `segmentation-mask-2d`, `segmentation-mask-3d`, `object-asset`.

## État

**Preuve de concept (Proof of Concept)** — la spécification et les SDK de référence (Python et TypeScript) sont utilisables, mais le format peut évoluer avant v2.1.

## Pour aller plus loin

Pour la spécification complète, le démarrage rapide, la validation / CI et le guide de migration, consultez le [README en anglais](../../README.md), le [README en japonais](../../README.ja.md) ou le [README en chinois simplifié](../../README.zh-CN.md).

## Licence

MIT — voir [LICENSE](../../LICENSE).
