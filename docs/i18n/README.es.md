# MCP Spatial Asset Profile v2 — Resumen en español

**Idiomas:** [English](../../README.md) · [日本語](../../README.ja.md) · [简体中文](../../README.zh-CN.md) · [한국어](README.ko.md) · **Español** · [Français](README.fr.md)

**MCP Spatial Asset Profile Version 2.0** (denominado **MCP Spatial Asset Profile v2** en este repositorio) es un formato de envoltorio (envelope) basado en JSON para representar activos de datos 3D y espaciales en el ecosistema de herramientas del [Model Context Protocol (MCP)](https://modelcontextprotocol.io/).

Se construye sobre **[mcp-3d v1](https://github.com/puruyan2525/mcp-3d)** (Claude Code, abril de 2025) de forma **estrictamente aditiva**: cualquier activo v1 puede actualizarse a v2 sin pérdida de información.

## Novedades principales

- `asset_id` globalmente estable, basado en URN.
- Bloque `spatial` formal: `frame`, `axis`, `handedness`, `unit`, `bounds`.
- `viewpoints` con parámetros intrínsecos / extrínsecos de cámara.
- Negociación de capacidades por URI para las representaciones.
- Flujo de segmentación de primera clase: `rendered-view` → `segmentation-mask-2d` → `segmentation-mask-3d` → `object-asset`, con trazabilidad completa mediante `derived_from` y `workflow.target_asset_id`.

## Tipos de activo soportados

`point-cloud`, `mesh`, `gaussian-splat`, `depth-image`, `rendered-view`, `segmentation-mask-2d`, `segmentation-mask-3d`, `object-asset`.

## Estado

**Prueba de concepto (Proof of Concept)** — la especificación y los SDK de referencia (Python y TypeScript) son utilizables, pero el formato puede evolucionar antes de v2.1.

## Más información

Para la especificación completa, inicio rápido, validación / CI y guía de migración, véase el [README en inglés](../../README.md), el [README en japonés](../../README.ja.md) o el [README en chino simplificado](../../README.zh-CN.md).

## Licencia

MIT — véase [LICENSE](../../LICENSE).
