"""
traceability.py — Asset graph traceability validation.

Design philosophy:
- Pure Python, no external dependencies
- validate_pipeline: takes list of asset dicts, checks graph integrity
- build_asset_graph: returns adjacency dict {asset_id: [parent_ids]}
- Detects: missing nodes, cycles, broken workflow references
"""

from __future__ import annotations
from typing import Any


def build_asset_graph(assets: list[dict]) -> dict[str, list[str]]:
    """
    Build an adjacency dict from derived_from + workflow references.

    Returns: {asset_id: [parent_asset_id, ...]}
    """
    graph: dict[str, list[str]] = {}

    for asset in assets:
        aid = asset.get("asset_id", "")
        if not aid:
            continue
        parents: list[str] = []

        # Explicit derived_from edges
        for p in asset.get("derived_from") or []:
            if p not in parents:
                parents.append(p)

        # Workflow target_asset_id as implicit edge
        workflow = asset.get("workflow") or {}
        target = workflow.get("target_asset_id")
        if target and target not in parents:
            parents.append(target)

        graph[aid] = parents

    return graph


def _detect_cycle(graph: dict[str, list[str]]) -> list[str]:
    """Return list of asset_ids involved in cycles (DFS)."""
    WHITE, GRAY, BLACK = 0, 1, 2
    color: dict[str, int] = {n: WHITE for n in graph}
    cycles: list[str] = []

    def dfs(node: str) -> bool:
        color[node] = GRAY
        for neighbor in graph.get(node, []):
            if neighbor not in color:
                color[neighbor] = WHITE
            if color[neighbor] == GRAY:
                cycles.append(neighbor)
                return True
            if color[neighbor] == WHITE:
                if dfs(neighbor):
                    return True
        color[node] = BLACK
        return False

    for node in list(graph.keys()):
        if color.get(node, WHITE) == WHITE:
            dfs(node)

    return cycles


def validate_pipeline(assets: list[dict]) -> list[str]:
    """
    Validate traceability of a collection of assets.

    Checks:
    1. Every asset has a non-empty asset_id.
    2. All referenced asset_ids (derived_from, workflow.*_asset_id) exist.
    3. No cycles in the derivation graph.
    4. rendered-view: workflow.target_asset_id points to a 3D source kind.
    5. segmentation-mask-2d: workflow.target_asset_id points to rendered-view.
    6. segmentation-mask-3d: workflow.target_asset_id points to 3D source.
    7. object-asset: workflow.target_asset_id points to 3D source.

    Returns list of error strings. Empty = valid.
    """
    errors: list[str] = []
    kind_map: dict[str, str] = {}  # asset_id → kind

    # Collect all ids and kinds
    for asset in assets:
        aid = asset.get("asset_id", "")
        kind = asset.get("kind", "")
        if not aid:
            errors.append(f"asset missing asset_id: {asset.get('name', '<unnamed>')}")
            continue
        kind_map[aid] = kind

    all_ids = set(kind_map.keys())

    # Check references exist
    for asset in assets:
        aid = asset.get("asset_id", "")
        if not aid:
            continue

        for parent_id in (asset.get("derived_from") or []):
            if parent_id not in all_ids:
                errors.append(f"{aid}: derived_from references unknown asset '{parent_id}'")

        workflow = asset.get("workflow") or {}
        target = workflow.get("target_asset_id")
        if target and target not in all_ids:
            errors.append(f"{aid}: workflow.target_asset_id references unknown asset '{target}'")

        for mask_id in (workflow.get("source_masks") or []):
            if mask_id not in all_ids:
                errors.append(f"{aid}: workflow.source_masks references unknown asset '{mask_id}'")

    # Kind-specific traceability
    _3d_source_kinds = {"point-cloud", "mesh", "gaussian-splat"}

    for asset in assets:
        aid = asset.get("asset_id", "")
        kind = asset.get("kind", "")
        workflow = asset.get("workflow") or {}
        target = workflow.get("target_asset_id")

        if kind == "rendered-view" and target:
            target_kind = kind_map.get(target)
            if target_kind and target_kind not in _3d_source_kinds:
                errors.append(
                    f"{aid}: rendered-view.target_asset_id points to '{target_kind}', "
                    f"expected one of {sorted(_3d_source_kinds)}"
                )

        elif kind == "segmentation-mask-2d" and target:
            target_kind = kind_map.get(target)
            if target_kind and target_kind != "rendered-view":
                errors.append(
                    f"{aid}: segmentation-mask-2d.target_asset_id points to '{target_kind}', "
                    f"expected 'rendered-view'"
                )

        elif kind == "segmentation-mask-3d" and target:
            target_kind = kind_map.get(target)
            if target_kind and target_kind not in _3d_source_kinds:
                errors.append(
                    f"{aid}: segmentation-mask-3d.target_asset_id points to '{target_kind}', "
                    f"expected one of {sorted(_3d_source_kinds)}"
                )

        elif kind == "object-asset" and target:
            target_kind = kind_map.get(target)
            if target_kind and target_kind not in _3d_source_kinds:
                errors.append(
                    f"{aid}: object-asset.target_asset_id points to '{target_kind}', "
                    f"expected one of {sorted(_3d_source_kinds)}"
                )

    # Cycle detection
    graph = build_asset_graph(assets)
    cycles = _detect_cycle(graph)
    for c in cycles:
        errors.append(f"cycle detected involving asset '{c}'")

    return errors
