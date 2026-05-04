# Package Publication Guide

This document describes how the **MCP Spatial Asset Profile v2** reference SDKs are published to PyPI and npm, and how to perform a release.

> Status:
>
> - **PyPI — published.** Initial release `mcp-spatial-asset-profile` **0.1.0** is live at <https://pypi.org/project/mcp-spatial-asset-profile/0.1.0/>. Subsequent releases follow the workflow below.
> - **npm — pending.** Metadata, build, and the manual GitHub Actions workflow are in place; the first publish still has to be performed by a human once npm Trusted Publisher setup is complete.

---

## Package names

| Ecosystem | Package name | Install command | Registry URL | Status |
|---|---|---|---|---|
| PyPI | `mcp-spatial-asset-profile` | `pip install mcp-spatial-asset-profile` | <https://pypi.org/project/mcp-spatial-asset-profile/> | **Published — v0.1.0** |
| npm  | `@furuse-kazufumi/mcp-spatial-asset-profile` | `npm install @furuse-kazufumi/mcp-spatial-asset-profile` | <https://www.npmjs.com/package/@furuse-kazufumi/mcp-spatial-asset-profile> | Pending — first publish not yet performed |

The Python distribution name (`mcp-spatial-asset-profile`) differs from the import package name (`spatial_asset_v2`). This is intentional and matches PEP 8 / PEP 423 guidance: the distribution describes the project, while the import name remains a stable identifier inside user code.

The npm scoped name uses the GitHub owner (`@furuse-kazufumi`) so that the package is unambiguously associated with the upstream repository even if a future unscoped name becomes available.

---

## Cross-links

- **GitHub repository:** <https://github.com/furuse-kazufumi/mcp-spatial-asset-profile>
- **GitHub release (PoC):** <https://github.com/furuse-kazufumi/mcp-spatial-asset-profile/releases/tag/v0.1.0-poc>
- **GitHub Discussions:** <https://github.com/furuse-kazufumi/mcp-spatial-asset-profile/discussions>
- **Specification:** [`spec/spatial-asset-profile-v2.md`](../spec/spatial-asset-profile-v2.md)

`pyproject.toml` and `package.json` both declare these URLs in their metadata so the package pages on PyPI and npm display direct links back to the repository, the release, and the spec.

---

## First-time setup

### PyPI — Trusted Publishing (recommended)

> The steps below were completed for the initial **v0.1.0** release. They are kept here for reference and for any future re-configuration (e.g. new environment, transferred ownership).

Trusted Publishing uses GitHub OIDC, so no long-lived API token is stored in repository secrets.

1. Create the project on PyPI by registering the name `mcp-spatial-asset-profile` (the first publish will reserve the name; a placeholder is *not* required).
2. On PyPI, open **Your projects → mcp-spatial-asset-profile → Publishing → Add a new pending publisher** and enter:
   - **Owner:** `furuse-kazufumi`
   - **Repository name:** `mcp-spatial-asset-profile`
   - **Workflow name:** `publish-packages.yml`
   - **Environment name:** `pypi` (matches the workflow)
3. Optionally repeat the configuration for **TestPyPI** with environment name `testpypi` if you want to do dry-run uploads first.

The workflow at `.github/workflows/publish-packages.yml` already requests `id-token: write` and uses [`pypa/gh-action-pypi-publish`](https://github.com/pypa/gh-action-pypi-publish), which reads the OIDC token automatically.

### npm — Trusted Publishing (recommended)

npm supports **Trusted Publishing** for GitHub Actions: the workflow exchanges its OIDC token for a short-lived publish credential, so no long-lived `NPM_TOKEN` is stored in repository secrets. Provenance attestations are produced automatically.

Requirements (already satisfied by `.github/workflows/publish-packages.yml`):

- GitHub-hosted runner with **Node.js 22.14.0+** and **npm 11.5.1+** — the workflow installs Node 24 via `actions/setup-node`, which ships with a Trusted-Publishing-capable npm out of the box (no global `npm install -g npm@latest` required), and verifies the resolved npm version before publishing.
- Workflow permissions `id-token: write` and `contents: read`.
- Publish command `npm publish --access public --provenance`.

One-time setup on npm:

1. Make sure the npm account either owns the `@furuse-kazufumi` scope or is a member of an organization that does. The workflow publishes with `--access public`, so a paid npm plan is not required.
2. Open the package settings page on npmjs.com (after the first publish, or while creating a *pending* trusted publisher) and add a **Trusted Publisher** with:
   - **Publisher:** GitHub Actions
   - **Organization or user:** `furuse-kazufumi`
   - **Repository:** `mcp-spatial-asset-profile`
   - **Workflow filename:** `publish-packages.yml`
   - **Environment:** *(optional — leave empty unless you also gate the npm job behind a GitHub environment)*

Once configured, **no `NPM_TOKEN` secret is needed** — the workflow publishes tokenlessly via OIDC.

### npm — legacy `NPM_TOKEN` fallback

If you cannot enable Trusted Publishing (e.g. because the package is hosted on a registry that does not support it yet), you can fall back to a long-lived token:

1. Create an **Automation** access token at <https://www.npmjs.com/settings/your-username/tokens> (must be of type *Automation* so it bypasses 2FA in CI).
2. Add it as a repository secret named `NPM_TOKEN` under **Settings → Secrets and variables → Actions**.
3. Re-add `env: { NODE_AUTH_TOKEN: ${{ secrets.NPM_TOKEN }} }` to the `Publish to npm` step.

Trusted Publishing is preferred — prefer it whenever the registry supports it.

---

## Local build & validation

Before publishing, validate both packages locally:

### Python

```bash
cd sdk/python
python -m pip install --upgrade pip build twine
python -m build            # produces dist/*.whl and dist/*.tar.gz
python -m twine check dist/*
```

### TypeScript

```bash
cd sdk/typescript
npm ci
npm run build
npm test
npm pack --dry-run         # shows exactly what would be uploaded
```

Both commands are also exercised in CI (`.github/workflows/ci.yml`) on every push to `main`.

---

## Releasing

The recommended path is to use the **manual** workflow:

1. Bump the version in `sdk/python/pyproject.toml` and `sdk/typescript/package.json` (keep them in sync).
2. Update the changelog / release notes and tag the release (e.g. `v0.1.0`).
3. Go to **Actions → Publish packages → Run workflow**, choose the target (`pypi`, `npm`, or `both`), and run.

The workflow:

- builds the Python sdist + wheel and uploads with Trusted Publishing,
- builds the TypeScript SDK, runs `npm pack --dry-run`, and publishes with `--provenance --access public` via npm Trusted Publishing (OIDC) — no `NPM_TOKEN` secret is consumed.

If you prefer to release locally, the equivalent commands are:

```bash
# Python
cd sdk/python
python -m build
python -m twine upload dist/*

# TypeScript
cd sdk/typescript
npm ci
npm run build
npm publish --access public --provenance
```

> **Local npm publish** still requires `npm login` (or `NPM_TOKEN` exported) and that you have configured the scope to allow public publishing.

---

## Linking from GitHub

After the first publish, GitHub will display the packages on the repository sidebar under **Packages**. To improve discoverability:

- Verify the repository link on PyPI ("Verified" badge appears once OIDC-trusted publishing has been used).
- npm shows the repository, homepage, and bugs URLs directly from `package.json` — no extra step required.
- Update the GitHub release notes for `v0.1.0` (or successor) to reference both package URLs explicitly.

---

## 日本語まとめ

- **PyPI 配布名:** `mcp-spatial-asset-profile` — **公開済み (v0.1.0)**: <https://pypi.org/project/mcp-spatial-asset-profile/0.1.0/>（インポートは `spatial_asset_v2` のまま）
- **npm 配布名:** `@furuse-kazufumi/mcp-spatial-asset-profile` — **未公開**（npm Trusted Publisher の登録および初回公開は今後実施）
- 公開は手動ワークフロー `.github/workflows/publish-packages.yml` から実行します。
- PyPI は **Trusted Publishing (OIDC)** を使う想定です。事前に PyPI 側でリポジトリ／ワークフロー／環境名（`pypi`）を登録してください。
- npm は **Trusted Publishing (OIDC)** を推奨します。npm 側でリポジトリ／ワークフロー名 `publish-packages.yml` を Trusted Publisher として登録すれば、`NPM_TOKEN` シークレットは不要です（provenance も自動付与）。Trusted Publishing が使えない場合のみ、Automation token を `NPM_TOKEN` として登録するレガシー方式にフォールバックしてください。
- ローカル検証は `python -m build` および `npm pack --dry-run` で行えます。CI でも同じチェックを実施しています。
- PyPI の初回公開は完了済み（v0.1.0）です。npm の初回公開はリポジトリ管理者が Trusted Publisher 設定後に手動で実施してください。
