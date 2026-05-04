# Publication Plan — MCP Spatial Asset Profile v2

**Status:** Working Draft  
**Date:** 2025-05

---

## 1. Publication Targets

### 1.1 Specification

| Target | Format | Timeline |
|---|---|---|
| GitHub repository (public) | Markdown | Q3 2025 |
| GitHub Pages (rendered docs) | HTML/MkDocs | Q3 2025 |
| Zenodo preprint | PDF | Q4 2025 |
| arXiv (cs.CV or cs.GR) | LaTeX → PDF | Q4 2025 |

### 1.2 Schema Registry

| Target | URL | Timeline |
|---|---|---|
| GitHub Raw CDN | `raw.githubusercontent.com/...` | Q3 2025 |
| Dedicated domain | `https://mcp-spatial.dev/spec/v2/` | Q4 2025 |
| JSON Schema Store | `schemastore.org` (via PR) | Q1 2026 |

### 1.3 SDK Packages

| Package | Registry | Timeline |
|---|---|---|
| `spatial-asset-v2` (Python) | PyPI | Q3 2025 |
| `spatial-asset-v2` (npm) | npmjs.com | Q3 2025 |

---

## 2. Community Engagement

### 2.1 MCP Ecosystem

- Submit RFC/proposal to the MCP community forum
- Coordinate with Anthropic developer relations
- Present at MCP hackathons / community calls

### 2.2 3D Community

- Post on r/computervision, r/3Dprinting, r/lidar
- Tweet thread / LinkedIn article with demo GIFs
- Submit to awesome-mcp-servers list

### 2.3 Research Community

- Reference relevant 3D data format papers (3D Tiles, glTF, USD)
- Cite Stanford Bunny dataset in examples
- Open issues for community feedback on segmentation workflow

---

## 3. Versioning Policy

- Patch releases (2.0.x): Bug fixes in schema/SDK only
- Minor releases (2.x.0): New optional fields, new capability tokens
- Major releases (3.0.0): Breaking changes (require migration)

All schema changes trigger a new `$id` URL. Old schema URLs remain permanently available.

---

## 4. Governance

- Specification maintained in `main` branch
- Changes via Pull Request with at least 1 review
- RFC process for major changes (new kinds, breaking changes)
- CHANGELOG.md documents all changes with dates and issue references

---

## 5. License Strategy

- Specification: CC BY 4.0 (attribution required)
- SDK code: MIT (permissive)
- Example files: CC0 1.0 (public domain)
- Stanford Bunny data: Original Stanford license applies
