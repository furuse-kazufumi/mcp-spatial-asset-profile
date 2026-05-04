# MCP Spatial Asset Profile v2 — 한국어 요약

**언어:** [English](../../README.md) · [日本語](../../README.ja.md) · [简体中文](../../README.zh-CN.md) · **한국어** · [Español](README.es.md) · [Français](README.fr.md)

**MCP Spatial Asset Profile Version 2.0**(이하 **MCP Spatial Asset Profile v2**)은 [Model Context Protocol (MCP)](https://modelcontextprotocol.io/) 도구 생태계에서 3D 및 공간 데이터 자산을 표현하기 위한 JSON 기반 봉투(envelope) 포맷입니다.

본 포맷은 **[mcp-3d v1](https://github.com/puruyan2525/mcp-3d)** (Claude Code, 2025년 4월) 위에 **순수 추가 방식(strictly additive)** 으로 확장되며, 모든 v1 자산은 정보 손실 없이 v2로 업그레이드할 수 있습니다.

## 주요 추가 사항

- URN 기반의 전역 안정 `asset_id`.
- 좌표 `frame`, `axis`, `handedness`, `unit`, `bounds`를 모은 정식 `spatial` 블록.
- 카메라 내부/외부 파라미터를 포함한 `viewpoints`.
- URI 기반 표현 능력 협상(capability negotiation).
- 일급(first-class) 분할 워크플로: `rendered-view` → `segmentation-mask-2d` → `segmentation-mask-3d` → `object-asset`, `derived_from` 및 `workflow.target_asset_id`로 완전한 계보 추적 가능.

## 지원 자산 종류

`point-cloud`, `mesh`, `gaussian-splat`, `depth-image`, `rendered-view`, `segmentation-mask-2d`, `segmentation-mask-3d`, `object-asset`.

## 상태

**Proof of Concept** — 사양 및 Python / TypeScript 참조 SDK는 사용 가능하지만 v2.1 이전에는 변경될 수 있습니다.

## 자세한 내용

전체 사양, 빠른 시작, 검증/CI, 마이그레이션 가이드는 [영문 README](../../README.md), [일본어 README](../../README.ja.md), 또는 [중국어 간체 README](../../README.zh-CN.md)를 참조하세요.

## 라이선스

MIT — [LICENSE](../../LICENSE) 참조.
