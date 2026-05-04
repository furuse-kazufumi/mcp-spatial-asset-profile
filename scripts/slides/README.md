# Slide Figure Generation Scripts

Scripts that render the explanatory figures used in the MCP Spatial Asset
Profile v2 slide deck and documentation.

## Provenance

`make_slide_figures.py` is ported from the original v2 PoC project
(internally referenced as `mcp-3d`, April–May 2025). It has been
lightly adapted for this repository:

- Default output directory is now `docs/assets/slides/` (was `out/slides/`).
- Slide titles use the canonical name **MCP Spatial Asset Profile v2**.
- Step labels use ASCII numerals so the figures render without a
  CJK-aware font on CI hosts; Japanese fonts are still preferred
  when available.
- Added a `--only` flag so the data-free architectural and pipeline
  figures can be regenerated without the Stanford Bunny mesh sample.

## Files

| File | Purpose |
|---|---|
| `make_slide_figures.py` | Renders the four figures committed under `docs/assets/slides/`. |

## Usage

```bash
# Render all four figures (requires samples/inspection/bunny_mesh.npz for fig 3 & 4)
python scripts/slides/make_slide_figures.py

# Render only the diagrammatic figures (no data dependency)
python scripts/slides/make_slide_figures.py --only 1,2

# Custom output directory
python scripts/slides/make_slide_figures.py --out /tmp/slides
```

## Dependencies

- `numpy`
- `matplotlib`

These are not part of the runtime SDK requirements; install them only when
you need to regenerate the figures:

```bash
pip install numpy matplotlib
```

## Sample data

Figures 03 and 04 depend on the Stanford Bunny mesh, expected at
`samples/inspection/bunny_mesh.npz` with the keys:

- `xyz`: float array, shape `(N, 3)` — vertex positions
- `faces`: int array, shape `(F, 3)` — triangle vertex indices

The mesh itself is not redistributed in this repository. The pre-rendered
PNGs are committed under `docs/assets/slides/` for users who only want to
view the figures without regenerating them.
