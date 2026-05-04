# Slide Figures

Explanatory diagrams for **MCP Spatial Asset Profile Version 2.0** (referred
to as **MCP Spatial Asset Profile v2** elsewhere in this repository).

These figures are referenced from [`docs/slides-v2.md`](../../slides-v2.md)
and are also embedded in the top-level READMEs.

| File | Description |
|---|---|
| `fig_01_architecture.png` | Schema structure: `SpatialAsset` envelope, `representations[]`, optional `segmentation`, the four representation kinds, and the `provenance` graph. |
| `fig_02_pipeline.png` | Multi-view segmentation workflow — six steps from `scene-asset` to `object-asset`, with full traceability via `derived_from` / `workflow.target_asset_id`. |
| `fig_03_representations.png` | Side-by-side comparison of the four spatial representations (`point-cloud`, `mesh`, `depth-image`, `3dgs`) rendered from the Stanford Bunny mesh. |
| `fig_04_seg_result.png` | Stanford Bunny head extraction example: `scene-asset` → `segmentation-mask-3d` → `object-asset`. |

## Regenerating

The figures are produced by [`scripts/slides/make_slide_figures.py`](../../../scripts/slides/make_slide_figures.py).

```bash
python scripts/slides/make_slide_figures.py
```

By default the script writes the four PNGs into this directory.
Figures 03 and 04 require a Stanford Bunny mesh sample at
`samples/inspection/bunny_mesh.npz` (with `xyz` and `faces` arrays); the
mesh is not bundled with the repository. To render only the diagrammatic
figures that have no data dependency:

```bash
python scripts/slides/make_slide_figures.py --only 1,2
```

See [`scripts/slides/README.md`](../../../scripts/slides/README.md) for
dependencies and provenance of the script.
