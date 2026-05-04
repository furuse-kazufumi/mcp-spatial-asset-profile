"""make_slide_figures.py — Generate slide figures for MCP Spatial Asset Profile v2.

Output (default: docs/assets/slides/):
  fig_01_architecture.png    — Schema structure diagram
  fig_02_pipeline.png        — Multi-view segmentation workflow flowchart
  fig_03_representations.png — Side-by-side comparison of 4 representations
  fig_04_seg_result.png      — Segmentation result (Stanford Bunny head extraction)

Originally generated for the v2 PoC slide deck and ported into the public
repository. Figures 03 and 04 require ``samples/inspection/bunny_mesh.npz``
(Stanford Bunny mesh, 35,947 vertices / 69,451 faces). That sample asset is not
bundled with this repository — fetch the Stanford Bunny mesh and convert it to
``{xyz, faces}`` keys, or skip those figures by passing ``--only 1,2``.

Usage:
    python scripts/slides/make_slide_figures.py
    python scripts/slides/make_slide_figures.py --out custom/dir --only 1,2
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "sdk" / "python"))

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch
import matplotlib.font_manager as _fm
from mpl_toolkits.mplot3d import Axes3D  # noqa: F401

for _jfont in ("Meiryo", "BIZ UDGothic", "MS Gothic", "Yu Gothic", "Noto Sans CJK JP"):
    if any(f.name == _jfont for f in _fm.fontManager.ttflist):
        matplotlib.rcParams["font.family"] = _jfont
        break

DEFAULT_OUT = ROOT / "docs" / "assets" / "slides"
MESH_NPZ = ROOT / "samples" / "inspection" / "bunny_mesh.npz"

C_BLUE   = "#2E6FD8"
C_TEAL   = "#1A9E8C"
C_ORANGE = "#E05C2A"
C_PURPLE = "#7B52AB"
C_GRAY   = "#6B7280"
C_LIGHT  = "#F0F4FF"


def _normalise(xyz: np.ndarray) -> np.ndarray:
    lo, hi = xyz.min(axis=0), xyz.max(axis=0)
    xyz = xyz - (lo + hi) / 2.0
    return xyz / (hi - lo).max()


def _fancy_box(ax, x, y, w, h, text, color, fontsize=10, text_color="white",
               sub_text=None):
    box = FancyBboxPatch((x - w/2, y - h/2), w, h,
                         boxstyle="round,pad=0.02",
                         facecolor=color, edgecolor="white",
                         linewidth=1.5, zorder=3)
    ax.add_patch(box)
    ty = y + h * 0.12 if sub_text else y
    ax.text(x, ty, text, ha="center", va="center",
            fontsize=fontsize, color=text_color,
            fontweight="bold", zorder=4)
    if sub_text:
        ax.text(x, y - h * 0.22, sub_text, ha="center", va="center",
                fontsize=fontsize - 2, color=text_color, alpha=0.85, zorder=4)


def _arrow(ax, x1, y1, x2, y2, color=C_GRAY, lw=2):
    ax.annotate("", xy=(x2, y2), xytext=(x1, y1),
                arrowprops=dict(arrowstyle="-|>", color=color, lw=lw),
                zorder=3)


def make_architecture(out_path: Path) -> None:
    fig, ax = plt.subplots(figsize=(14, 9), facecolor="white")
    ax.set_xlim(0, 14)
    ax.set_ylim(0, 9)
    ax.set_axis_off()
    fig.suptitle("MCP Spatial Asset Profile v2 — Schema Structure",
                 fontsize=16, fontweight="bold", y=0.97)

    _fancy_box(ax, 7, 8.0, 4.0, 0.8,
               "SpatialAsset", C_BLUE, fontsize=13,
               sub_text="asset_id · asset_type · created_at · provenance{}")

    _fancy_box(ax, 3.5, 6.1, 4.2, 0.8,
               "representations[ ]", C_TEAL, fontsize=11,
               sub_text="format · uri · resolution · encoding · metadata{}")

    _fancy_box(ax, 10.5, 6.1, 3.8, 0.8,
               "segmentation (optional)", C_PURPLE, fontsize=11,
               sub_text="mask_uri · object_id · confidence · method")

    _arrow(ax, 7, 7.6, 3.5, 6.5)
    _arrow(ax, 7, 7.6, 10.5, 6.5, color=C_PURPLE)

    formats = [
        (1.2,  4.0, "point-cloud",  C_BLUE,   "PLY / LAS\n[x,y,z,(r,g,b)]"),
        (4.0,  4.0, "mesh",         C_TEAL,   "PLY / OBJ / GLTF\nvertices + faces"),
        (6.8,  4.0, "depth-image",  C_ORANGE, "PNG / EXR\n[H×W float32]"),
        (9.6,  4.0, "3dgs",         C_PURPLE, "PLY (3DGS)\nGaussian primitives"),
    ]
    for fx, fy, label, color, sub in formats:
        _fancy_box(ax, fx, fy, 2.4, 1.0, label, color, fontsize=10, sub_text=sub)
        _arrow(ax, 3.5, 5.7, fx, 4.5, color=C_TEAL)

    _fancy_box(ax, 7, 2.2, 5.5, 0.8,
               "provenance graph", "#374151", fontsize=11,
               sub_text="source_asset_ids[ ] · operation · operator · parameters{}")
    _arrow(ax, 7, 7.6, 7, 2.6, color="#9CA3AF")
    ax.text(7.3, 5.0, "derived_from", fontsize=8, color="#9CA3AF",
            rotation=90, va="center")

    asset_types = [
        "scene-asset", "rendered-view", "segmentation-mask-2d",
        "segmentation-mask-3d", "object-asset",
    ]
    ax.text(7, 1.5, "asset_type: " + "  /  ".join(asset_types),
            ha="center", va="center", fontsize=9,
            color=C_GRAY, style="italic")

    fig.tight_layout(rect=[0, 0, 1, 0.95])
    fig.savefig(out_path, dpi=150, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    print(f"  fig_01_architecture.png -> {out_path}")


def make_pipeline(out_path: Path) -> None:
    fig, ax = plt.subplots(figsize=(16, 5.5), facecolor="white")
    ax.set_xlim(0, 16)
    ax.set_ylim(0, 5.5)
    ax.set_axis_off()
    fig.suptitle("MCP Spatial Asset Profile v2 — Multi-view Segmentation Workflow",
                 fontsize=15, fontweight="bold", y=0.98)

    steps = [
        (1.4,  2.8, "(1) Scene\nAsset",       C_BLUE,   "PLY / NPZ\npoints or mesh"),
        (4.0,  2.8, "(2) Render\nView",        C_TEAL,   "3 viewpoints PNG\n+ depth map"),
        (6.6,  2.8, "(3) Segment\n(SAM2 etc.)",   C_ORANGE, "per-view\n2D mask PNG"),
        (9.2,  2.8, "(4) Project\nto 3D",      C_PURPLE, "per-view\ncandidate points"),
        (11.8, 2.8, "(5) Merge\n(consensus)",  "#0E7490", "merged\n3D mask"),
        (14.4, 2.8, "(6) Object\nAsset",       "#065F46", "extracted\nPLY"),
    ]

    for i, (x, y, label, color, sub) in enumerate(steps):
        _fancy_box(ax, x, y, 2.2, 1.4, label, color, fontsize=11, sub_text=sub)
        if i < len(steps) - 1:
            _arrow(ax, x + 1.1, y, steps[i+1][0] - 1.1, y, color=C_GRAY, lw=2.5)

    asset_labels = [
        (1.4,  1.4, "scene-asset",             C_BLUE),
        (4.0,  1.4, "rendered-view",            C_TEAL),
        (6.6,  1.4, "segmentation-mask-2d",     C_ORANGE),
        (9.2,  1.4, "segmentation-mask-3d\n(candidate)", C_PURPLE),
        (11.8, 1.4, "segmentation-mask-3d\n(merged)",    "#0E7490"),
        (14.4, 1.4, "object-asset",             "#065F46"),
    ]
    for x, y, label, color in asset_labels:
        ax.text(x, y, label, ha="center", va="center",
                fontsize=7.5, color=color, fontweight="bold",
                bbox=dict(facecolor=C_LIGHT, edgecolor=color,
                          boxstyle="round,pad=0.15", linewidth=1))

    ax.annotate("", xy=(14.4, 1.0), xytext=(1.4, 1.0),
                arrowprops=dict(arrowstyle="-|>", color="#CBD5E1",
                                lw=1.5, connectionstyle="arc3,rad=0.0"))
    ax.text(7.9, 0.55,
            "provenance graph — every step's lineage recorded as JSON",
            ha="center", va="center", fontsize=9, color=C_GRAY, style="italic")

    fig.tight_layout(rect=[0, 0, 1, 0.94])
    fig.savefig(out_path, dpi=150, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    print(f"  fig_02_pipeline.png -> {out_path}")


def make_representations(out_path: Path) -> None:
    if not MESH_NPZ.exists():
        raise FileNotFoundError(
            f"Required mesh sample not found: {MESH_NPZ}. "
            "Provide a Stanford Bunny mesh as samples/inspection/bunny_mesh.npz "
            "with keys 'xyz' (N,3) float and 'faces' (F,3) int."
        )

    data = np.load(MESH_NPZ)
    xyz = _normalise(data["xyz"])
    faces = data["faces"]

    fig = plt.figure(figsize=(16, 5.5), facecolor="white")
    fig.suptitle(
        "Four spatial representations — Stanford Bunny "
        f"({len(xyz):,} vertices / {len(faces):,} faces)",
        fontsize=14, fontweight="bold", y=0.99,
    )

    AZIM, ELEV = 210, 20

    ax1 = fig.add_subplot(141, projection="3d")
    depth = xyz @ np.array([[np.cos(np.radians(AZIM))], [np.sin(np.radians(AZIM))], [0]])
    dn = (depth - depth.min()) / (depth.max() - depth.min() + 1e-9)
    ax1.scatter(xyz[::4, 0], xyz[::4, 1], xyz[::4, 2],
                s=1.5, c=dn[::4], cmap="Blues", alpha=0.7,
                linewidths=0, rasterized=True)
    ax1.view_init(elev=ELEV, azim=AZIM)
    ax1.set_axis_off()
    ax1.set_title("(1) point-cloud\n(PLY / LAS)", fontsize=10, color=C_BLUE,
                  fontweight="bold")

    ax2 = fig.add_subplot(142, projection="3d")
    ax2.plot_trisurf(xyz[:, 0], xyz[:, 1], xyz[:, 2],
                     triangles=faces,
                     color=C_TEAL, alpha=0.92,
                     linewidth=0, antialiased=True, shade=True)
    ax2.view_init(elev=ELEV, azim=AZIM)
    ax2.set_axis_off()
    ax2.set_title("(2) mesh\n(PLY / OBJ / GLTF)", fontsize=10, color=C_TEAL,
                  fontweight="bold")

    ax3 = fig.add_subplot(143)
    H = W = 128
    uv = xyz[:, :2].copy()
    uv -= uv.min(axis=0)
    scale = (min(H, W) - 4) / uv.max()
    uv = (uv * scale + 2).astype(int)
    uv = np.clip(uv, 0, min(H, W) - 1)
    depth_img = np.full((H, W), np.nan)
    for (u, v), z in zip(uv, xyz[:, 2]):
        if np.isnan(depth_img[v, u]) or z > depth_img[v, u]:
            depth_img[v, u] = z
    ax3.imshow(depth_img, cmap="plasma", origin="lower",
               interpolation="nearest")
    ax3.set_axis_off()
    ax3.set_title("(3) depth-image\n(PNG / EXR)", fontsize=10, color=C_ORANGE,
                  fontweight="bold")

    ax4 = fig.add_subplot(144, projection="3d")
    rng = np.random.default_rng(42)
    idx = rng.choice(len(xyz), size=4000, replace=False)
    gs_pts = xyz[idx]
    s_vals = rng.uniform(3, 18, size=4000)
    c_vals = rng.uniform(0, 1, size=4000)
    ax4.scatter(gs_pts[:, 0], gs_pts[:, 1], gs_pts[:, 2],
                s=s_vals, c=c_vals, cmap="RdPu",
                alpha=0.5, linewidths=0, rasterized=True)
    ax4.view_init(elev=ELEV, azim=AZIM)
    ax4.set_axis_off()
    ax4.set_title("(4) 3D Gaussian Splatting\n(PLY, Gaussian primitives)",
                  fontsize=10, color=C_PURPLE, fontweight="bold")

    labels_colors = [
        ("point-cloud",  C_BLUE),
        ("mesh",         C_TEAL),
        ("depth-image",  C_ORANGE),
        ("3DGS",         C_PURPLE),
    ]
    handles = [mpatches.Patch(facecolor=c, label=l) for l, c in labels_colors]
    fig.legend(handles=handles, loc="lower center", ncol=4,
               fontsize=9, frameon=False,
               bbox_to_anchor=(0.5, -0.02))

    fig.tight_layout(rect=[0, 0.04, 1, 0.96])
    fig.savefig(out_path, dpi=150, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    print(f"  fig_03_representations.png -> {out_path}")


def make_seg_result(out_path: Path) -> None:
    if not MESH_NPZ.exists():
        raise FileNotFoundError(
            f"Required mesh sample not found: {MESH_NPZ}. "
            "Provide a Stanford Bunny mesh as samples/inspection/bunny_mesh.npz "
            "with keys 'xyz' (N,3) float and 'faces' (F,3) int."
        )

    data = np.load(MESH_NPZ)
    xyz = _normalise(data["xyz"])
    faces = data["faces"]

    threshold = np.percentile(xyz[:, 1], 62)
    fg = xyz[:, 1] > threshold
    bg = ~fg

    fig = plt.figure(figsize=(15, 5), facecolor="white")
    fig.suptitle(
        "Segmentation result — Stanford Bunny head extraction\n"
        f"(scene {len(xyz):,} pts -> object {fg.sum():,} pts, {fg.mean()*100:.1f}%)",
        fontsize=13, fontweight="bold", y=0.99,
    )

    AZIM, ELEV = 30, 25

    ax1 = fig.add_subplot(131, projection="3d")
    ax1.plot_trisurf(xyz[:, 0], xyz[:, 1], xyz[:, 2],
                     triangles=faces,
                     color=C_BLUE, alpha=0.90,
                     linewidth=0, antialiased=True, shade=True)
    ax1.view_init(elev=ELEV, azim=AZIM)
    ax1.set_axis_off()
    ax1.set_title("scene-asset\n(full)", fontsize=11, color=C_BLUE, fontweight="bold")

    ax2 = fig.add_subplot(132, projection="3d")
    depth_bg = xyz[bg, 2]
    dn = (depth_bg - depth_bg.min()) / (depth_bg.max() - depth_bg.min() + 1e-9)
    ax2.scatter(xyz[bg, 0], xyz[bg, 1], xyz[bg, 2],
                s=3, c=dn, cmap="Blues", alpha=0.3,
                linewidths=0, rasterized=True)
    ax2.scatter(xyz[fg, 0], xyz[fg, 1], xyz[fg, 2],
                s=10, c=C_ORANGE, alpha=0.95,
                linewidths=0, rasterized=True)
    ax2.view_init(elev=ELEV, azim=AZIM)
    ax2.set_axis_off()
    ax2.set_title("segmentation-mask-3d\n(target highlighted)",
                  fontsize=11, color=C_ORANGE, fontweight="bold")

    ax3 = fig.add_subplot(133, projection="3d")
    fg_idx = np.where(fg)[0]
    fg_faces = faces[np.all(np.isin(faces, fg_idx), axis=1)]
    if len(fg_faces) > 0:
        remap = {old: new for new, old in enumerate(fg_idx)}
        remapped = np.vectorize(remap.get)(fg_faces)
        obj_xyz = xyz[fg_idx]
        ax3.plot_trisurf(obj_xyz[:, 0], obj_xyz[:, 1], obj_xyz[:, 2],
                         triangles=remapped,
                         color=C_ORANGE, alpha=0.92,
                         linewidth=0, antialiased=True, shade=True)
    else:
        ax3.scatter(xyz[fg, 0], xyz[fg, 1], xyz[fg, 2],
                    s=8, c=C_ORANGE, alpha=0.9, linewidths=0)
    ax3.view_init(elev=ELEV, azim=AZIM)
    ax3.set_axis_off()
    ax3.set_title("object-asset\n(extracted surface)",
                  fontsize=11, color="#065F46", fontweight="bold")

    fig.tight_layout(rect=[0, 0, 1, 0.93])
    fig.savefig(out_path, dpi=150, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    print(f"  fig_04_seg_result.png -> {out_path}")


FIGURES = {
    1: ("fig_01_architecture.png", make_architecture),
    2: ("fig_02_pipeline.png", make_pipeline),
    3: ("fig_03_representations.png", make_representations),
    4: ("fig_04_seg_result.png", make_seg_result),
}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT,
                        help=f"Output directory (default: {DEFAULT_OUT.relative_to(ROOT)})")
    parser.add_argument("--only", type=str, default="1,2,3,4",
                        help="Comma-separated figure numbers to render (default: 1,2,3,4)")
    args = parser.parse_args()

    out: Path = args.out
    out.mkdir(parents=True, exist_ok=True)
    selected = sorted({int(x) for x in args.only.split(",") if x.strip()})

    print(f"Output: {out}\n")
    for n in selected:
        if n not in FIGURES:
            print(f"  skip: unknown figure {n}")
            continue
        filename, fn = FIGURES[n]
        fn(out / filename)

    print("\n" + "-" * 60)
    print(f"Done. Wrote {len(selected)} figure(s) to {out}.")
    print("-" * 60)


if __name__ == "__main__":
    main()
