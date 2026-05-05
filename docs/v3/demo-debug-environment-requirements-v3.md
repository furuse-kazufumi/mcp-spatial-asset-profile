# Demo / Debug Environment Requirements — MCP Spatial Asset Profile v3

**Title (JA):** マルチイベントカメラ空間/動き証跡 v3 デモおよびデバッグ環境 要件定義書
**Status:** Working Draft (Requirements & Design — pre-implementation)
**Version:** v3 / 0.1
**Date:** 2026-05-04
**Audience:** Profile maintainers, Claude Code 実装エージェント, contributors evaluating v3
**Companion docs:**
- `multi-event-camera-spatial-evidence-profile-v3.md` (proposed — profile spec)
- `claude-code-implementation-brief-v3.md` (proposed — implementation brief)

> 本書は **v3 のデモ／デバッグ環境** を対象とする要件・設計書である。実装手順そのものは含まない。日本語を主体とし、用語・コード・ファイル名・スキーマ名は英語のまま記述する（bilingual: Japanese-first）。

---

## 1. Purpose / 目的

v3 では MCP Spatial Asset Profile を「**マルチイベントカメラによる空間／動きの証跡 (multi-event-camera spatial / motion evidence)**」へ拡張する。
イベントカメラ（DVS / event-based vision sensor）の出力は時間的に粗い・空間的にスパースで、従来の RGB を前提にしたデバッグ手法（フレーム単位の可視化、PSNR、IoU など）が機能しにくい。

本書は次を達成するための **デモ／デバッグ環境** の要件と設計を定義する：

1. v3 プロファイル（event-frame-2d / event-tracklet-3d / motion-evidence-3d / vllm-summary など）が **再現可能** に検証できること。
2. プロファイル実装者が **座標変換・時刻同期・対応付け・三角測量・derived_from グラフ** を最小コストで debug できること。
3. 公開デモが **重い依存・大容量データ・GPU・ネット接続なし** で動作し、CI に組み込めること。
4. 後段の VLLM (Vision-Language Large Model) による説明レイヤを、プロファイル準拠の証跡から駆動できることを示すこと。

## 2. Background / 背景

- v1 / v2 は静的な 3D アセット（PLY, splat, mesh）と segmentation workflow を中心に設計されている。
- v3 で追加対象となるイベントカメラ系は次の特徴を持つ：
  - 出力は `(x, y, t, polarity)` の event stream であり、固定 fps のフレームではない。
  - SNR・dropout・hot pixel の影響が大きく、生データを目視で「正しい／誤り」と判定しにくい。
  - 複数台間の **時刻同期 (sub-ms)** と **空間キャリブレーション (extrinsics)** が破綻すると、後段の 3D triangulation・tracklet linking が黙って崩れる。
- DSEC / MVSEC など公開データセットは有用だが、(a) 容量が大きい、(b) ライセンスと再配布制限がある、(c) ground truth が常に十分とは限らない、(d) バグ切り分けに **既知の正解 (known-answer)** を持たない。
- したがって、**「合成（synthetic）かつ決定的（deterministic）かつ小さい」リファレンス・フィクスチャを最初に置く** 戦略を v3 の中心に据える。

## 3. Core Principle / 設計原則

> **Synthetic-first, deterministic, small, CI-friendly, no heavy dependencies.**

| 原則 | 内容 |
|---|---|
| Synthetic-first | 公開データセット利用より先に、**合成イベントによる Debug Demo** を整備する。 |
| Deterministic | 乱数は固定 seed。同じ入力からは bit-exact ではないとしても、tolerance 内で同じ出力を得る。 |
| Small | リポジトリ同梱データは合計 **数 MB 以下** を目標 (single demo run < ~5 MB)。 |
| CI-friendly | CPU のみ・10 秒〜数十秒で完走。GPU / CUDA / ROS / 専用ハードウェアを **必須にしない**。 |
| No heavy dependencies | コア層は Python 標準 + `numpy` + 既存 SDK のみ。可視化や VLLM は **任意 (optional extras)**。 |
| Reproducible | `python -m ... --seed N` で誰でも同一結果を再現できる。 |
| Pedagogical | 各レイヤが「なぜ壊れているか／なぜ正しいか」を示す **既知の正解** を持つ。 |

## 4. Three-Layer Demo / Debug Architecture / 三層構造

```
┌──────────────────────────────────────────────────────────────┐
│ Layer 3 — VLLM Explanation Demo                              │
│   evidence assets → VLLM → vllm-summary asset (自然言語説明) │
└──────────────────────────────────────────────────────────────┘
                          ▲
┌──────────────────────────────────────────────────────────────┐
│ Layer 2 — Public Dataset Replay Demo                         │
│   DSEC / MVSEC 等の公開データを v3 envelope に変換し再生     │
└──────────────────────────────────────────────────────────────┘
                          ▲
┌──────────────────────────────────────────────────────────────┐
│ Layer 1 — Synthetic Debug Demo  ★ reference fixture          │
│   2 virtual event cameras + 既知軌跡 → 全 v3 アセットを生成  │
└──────────────────────────────────────────────────────────────┘
```

下層ほど **正解が既知** で **依存が軽く** 安定。上層ほど **現実的** だが **不確実性と依存** が増える。
**Layer 1 の合格** を Layer 2 / Layer 3 着手の前提とする。

### 4.1 Layer 1 — Synthetic Debug Demo (★ reference fixture)

- 仮想シーン上で 1〜数本の **既知の 3D 軌跡** を動かし、2 台以上の仮想イベントカメラに **解析的に投影** して event stream を生成する。
- ground truth (3D pose, 2D projection, intrinsics, extrinsics, time offset, polarity) を **すべて保持** し、各処理段の出力と直接照合する。
- 失敗注入（calibration ずれ、time skew、欠損 polarity, hot pixel）を **opt-in** で注入し、debug 経路を実証する。

### 4.2 Layer 2 — Public Dataset Replay Demo

- DSEC / MVSEC など公開データセットの **短いスライス** を v3 envelope (`event-frame-2d`, ...) に変換するアダプタ。
- データはリポジトリに **同梱しない**（download instructions のみ）。ライセンス・帰属・再配布制限を明記。
- 合成と同じ pipeline / CLI を通すことで、Layer 1 で固めた contract を実データで再検証する。

### 4.3 Layer 3 — VLLM Explanation Demo

- Layer 1 / Layer 2 の出力（event-frame-2d, event-tracklet-3d, motion-evidence-3d）を入力に、VLLM が自然言語サマリ (`vllm-summary` asset) を出す。
- VLLM 呼び出しは **モック実装と実 API** の両対応。CI ではモックのみ実行。
- 目的は「プロファイルが LLM/VLLM フレンドリな構造になっているか」を実証することで、モデル性能の評価ではない。

## 5. Why Synthetic-First Is Necessary / 合成優先の必然性

イベントカメラの debug が RGB と決定的に違う点：

1. **目視判定が難しい。** event stream は人間にとって「正しいか」が一目で分からない。known-answer がないとバグが silent に残る。
2. **時刻同期が支配的。** sub-ms の time skew が triangulation / tracklet linking を黙って壊す。実データでは ground truth な time offset を得にくい。
3. **キャリブレーションが支配的。** intrinsics / extrinsics の誤差が下流すべてに伝搬する。実データでは calibration 自体に誤差を含む。
4. **スパース性。** event window 幅・clustering 閾値の調整は、known trajectory がないと「何が正解か」を定義できない。
5. **責務切り分け。** 実データで失敗したとき、それがセンサ・キャリブ・コード・閾値のどこに起因するかは合成 fixture を経由しないと特定が難しい。

したがって **Synthetic Debug Demo を v3 の reference fixture / regression baseline とする**。実データはこれを通った後に追加する。

## 6. Functional Requirements / 機能要件

### 6.1 Layer 1 — Synthetic Debug Demo (FR-L1)

- **FR-L1.1** 2 台以上の仮想イベントカメラを定義できる（intrinsics, extrinsics, resolution, time offset を JSON で）。
- **FR-L1.2** 1 つ以上の 3D 軌跡（直線、円、ジグザグ等）を時刻関数として定義できる。
- **FR-L1.3** 各カメラへの **解析的投影** から event stream を生成する（ノイズ・dropout は opt-in）。
- **FR-L1.4** event stream を任意 window 幅で集積し `event-frame-2d` を生成する。
- **FR-L1.5** カメラ毎の 2D tracklet を生成し、多視点対応付けと triangulation により `event-tracklet-3d` を生成する。
- **FR-L1.6** 集合として `motion-evidence-3d` を生成する。
- **FR-L1.7** すべての成果物は v3 schema に **valid** な JSON envelope として出力される。
- **FR-L1.8** 各成果物の `derived_from` が source asset を正しく指す（DAG が閉じている）。
- **FR-L1.9** ground truth と推定値を比較する **assertion harness** を提供する（位置誤差・時刻誤差・本数等）。
- **FR-L1.10** failure injection モード（calibration error, time skew, dropped polarity, hot pixel）を CLI フラグで切り替えられる。

### 6.2 Layer 2 — Public Dataset Replay Demo (FR-L2)

- **FR-L2.1** DSEC / MVSEC 等の公式形式から `event-frame-2d` ほかへ変換するアダプタ。
- **FR-L2.2** データセットそのものはリポジトリ同梱せず、download script / instructions を提供する。
- **FR-L2.3** 各データセットの **ライセンス条項・帰属・再配布制限** を README に明記する。
- **FR-L2.4** 短い slice (数百 ms〜数秒) で完走できる。
- **FR-L2.5** Layer 1 と **同一の CLI / API** で動作する（adapter のみ差し替え）。

### 6.3 Layer 3 — VLLM Explanation Demo (FR-L3)

- **FR-L3.1** evidence asset 群を入力に、`vllm-summary` asset を出力する。
- **FR-L3.2** VLLM クライアントは interface 化し、**deterministic mock** と **real provider** を切り替えられる。
- **FR-L3.3** CI では mock のみを実行する。実 API キーは不要。
- **FR-L3.4** `vllm-summary.derived_from` が入力 evidence をすべて参照する。
- **FR-L3.5** プロンプト・モデル名・温度等を asset の `provenance` に記録する。

## 7. Non-Functional Requirements / 非機能要件

| ID | 要件 |
|---|---|
| NFR-1 | Layer 1 の full run は **CPU のみ** で **30 秒以内** に完了する（CI ターゲット）。 |
| NFR-2 | リポジトリ同梱データは 1 デモあたり **5 MB 以下** を目標とする。 |
| NFR-3 | コアの追加依存は `numpy` のみ必須。可視化 / VLLM は extras にする。 |
| NFR-4 | 乱数は固定 seed。固定 seed のもと、数値結果は許容誤差内で再現する。 |
| NFR-5 | 全成果物は対応する v3 JSON Schema に対して valid。CI で schema validation を行う。 |
| NFR-6 | 既存 v1 / v2 アセットおよび pipeline と **後方互換**（破壊しない）。 |
| NFR-7 | OS 依存を持たない（Linux / macOS / Windows で動作）。 |
| NFR-8 | ライセンスは本リポジトリの既存ライセンスに従う。第三者データの再配布は行わない。 |

## 8. Debugging Targets / デバッグ対象

本デモ／デバッグ環境が **明示的に検証する対象**：

1. **Coordinate transforms** — world / camera / pixel 間変換の正しさ。
2. **`T_target_source` convention** — 命名規約 `T_target_source` が「source frame の点を target frame に写す変換」として **一貫** していること。プロジェクト全体で逆向き混在を起こさない。
3. **Calibration** — intrinsics (fx, fy, cx, cy, distortion) と extrinsics (R, t) の往復で点が元に戻ること。
4. **Time synchronization** — カメラ間 time offset がメタデータで一貫し、補正後に投影が一致すること。
5. **Event windowing** — window 幅・stride・accumulator 種別 (count, polarity-signed) が再現的に効くこと。
6. **Clustering thresholds** — DBSCAN 等の `eps` / min-samples が known trajectory に対し expected cluster 数を返すこと。
7. **Tracklet linking** — フレーム間連結（IOU / nearest / Hungarian など）の安定性、ID switch の検出。
8. **Multi-view correspondence** — 複数カメラ間の epipolar / temporal による対応付け。
9. **Triangulation** — 2 視点以上からの 3D 復元誤差が tolerance 内に収まること。
10. **Uncertainty** — 共分散・誤差伝搬が空でなく、次段で消費可能なこと。
11. **`derived_from` graph** — DAG が閉じている、循環がない、root が source asset。
12. **Schema validation** — すべての出力 JSON が v3 Draft 2020-12 schema に valid。

## 9. Proposed Repository Structure / リポジトリ構成 (proposed)

```
samples/
  v3/
    README.md                          # v3 サンプル全体の入口
    synthetic-debug-demo/              # Layer 1 (★ reference fixture)
      README.md
      config/
        cameras.json                   # intrinsics / extrinsics / time offset
        scene.json                     # trajectories / objects / duration
      expected/
        event-frame-2d/*.json
        event-tracklet-3d/*.json
        motion-evidence-3d/*.json
        vllm-summary/*.json            # mock VLLM の決定的出力
      assertions/
        ground-truth.json              # 真値（軌跡・対応・三角測量）
    public-dataset-replay/             # Layer 2
      README.md                        # ライセンス・取得手順
      adapters/
        dsec/README.md
        mvsec/README.md
      download/
        fetch_dsec_slice.sh            # 取得スクリプトのみ。データ非同梱
    vllm-explanation-demo/             # Layer 3
      README.md
      prompts/
        summary.md
      mock/
        responses.json                 # 決定的モック応答
docs/
  v3/
    README.md
    demo-debug-environment-requirements-v3.md   # ← 本書
    multi-event-camera-spatial-evidence-profile-v3.md   # (companion)
    claude-code-implementation-brief-v3.md              # (companion)
```

> 上記は **proposed**。実装時に細部は調整される。

## 10. Minimal Data Flow / 最小データフロー

```
[scene.json]                [cameras.json]
     │                           │
     ▼                           ▼
  (trajectory generator) ── (analytic projector)
                                 │
              ┌──────────────────┴──────────────────┐
              ▼                                     ▼
        cam0 event stream                     cam1 event stream
              │                                     │
              ▼                                     ▼
        event-frame-2d (cam0)                 event-frame-2d (cam1)
              │                                     │
              ▼                                     ▼
        2D tracklets (cam0)                   2D tracklets (cam1)
              └──────────────┬──────────────────────┘
                             ▼
                    multi-view correspondence
                             │
                             ▼
                    triangulation + uncertainty
                             │
                             ▼
                       event-tracklet-3d (per asset)
                             │
                             ▼
                       motion-evidence-3d (集約)
                             │
                             ▼
                  VLLM (mock or real) → vllm-summary
```

`derived_from` は逆方向に張られ、`vllm-summary` から `scene.json`/`cameras.json` まで辿れる。

## 11. CLI / API Shape (proposed) / CLI・API 形式（提案）

> 以下は **proposed**。具体的な実装は Claude Code 側で行う。

### 11.1 CLI

```
# Layer 1 — Synthetic Debug Demo
python -m spatial_asset_v3.demos.synthetic \
  --config samples/v3/synthetic-debug-demo/config/scene.json \
  --cameras samples/v3/synthetic-debug-demo/config/cameras.json \
  --out out/synthetic/ \
  --seed 42 \
  [--inject calibration_error|time_skew|hot_pixel|drop_polarity]

# Layer 2 — Public Dataset Replay Demo
python -m spatial_asset_v3.demos.replay \
  --adapter dsec \
  --input /path/to/dsec_slice \
  --out out/replay/

# Layer 3 — VLLM Explanation Demo
python -m spatial_asset_v3.demos.vllm \
  --evidence out/synthetic/ \
  --provider mock \
  --out out/vllm/

# Validation harness
python -m spatial_asset_v3.demos.validate \
  --bundle out/synthetic/ \
  --ground-truth samples/v3/synthetic-debug-demo/assertions/ground-truth.json
```

### 11.2 Python API (sketch)

```python
from spatial_asset_v3.demos import synthetic, replay, vllm, validate

bundle = synthetic.run(scene="...", cameras="...", seed=42)
report = validate.run(bundle, ground_truth="...")
summary = vllm.run(bundle, provider="mock")
```

### 11.3 MCP tools (proposed)

```
synth_event_demo(scene_id, cameras_id, seed) -> bundle_id
replay_event_dataset(adapter, slice_uri)     -> bundle_id
vllm_explain_motion(bundle_id, provider)     -> vllm_summary_id
validate_bundle(bundle_id, ground_truth_id?) -> validation_report_id
```

## 12. Viewer / Debug UI Requirements / ビューア・デバッグ UI 要件

実装は **任意 / 段階的**。コア機能は CLI と JSON で完結する前提とし、UI は extras。

| パネル | 目的 | 入力 | 表示 |
|---|---|---|---|
| Asset graph inspector | `derived_from` DAG の検査 | bundle dir | ノード=asset / エッジ=derived_from。クリックで envelope JSON 表示。 |
| Event accumulation panel | window 幅と accumulator の効果 | event-frame-2d | カメラ毎の 2D 蓄積像（polarity を色分け）。time slider 付き。 |
| Tracklet overlay | カメラ視点 2D tracklet | event-frame-2d + 2D tracklets | 各カメラの蓄積像上に tracklet ID を重畳表示。 |
| 3D / top-view tracklet panel | 3D tracklet と triangulation 結果 | event-tracklet-3d | top-view 2D 投影で十分（重い 3D renderer は **不要**）。 |
| JSON / schema validation panel | schema 適合と必須フィールド | bundle dir | 各 asset の valid / invalid と原因 |
| VLLM summary panel | 自然言語サマリ | vllm-summary asset | テキスト + 参照される evidence へのリンク |

UI は CLI から起動するローカル Web ビューア（例: 静的 HTML + JSON）を想定し、サーバ常駐は要求しない。

## 13. Test Strategy & Acceptance Criteria / テスト戦略と受け入れ条件

### 13.1 Test layers

1. **Unit tests** — projection / windowing / clustering / triangulation の数学的性質。
2. **Schema validation tests** — 全成果物が v3 schema に valid。
3. **Golden-file tests** — 固定 seed で生成した envelope が `expected/` と一致（数値は tolerance 比較）。
4. **Failure-injection tests** — `--inject` 各モードで、validation harness が **意図した違反を検出する** こと。
5. **End-to-end smoke** — `synthetic → validate → vllm(mock)` が CI 内で完走する。

### 13.2 Acceptance criteria for Layer 1

- AC-1: clean run で全 envelope が schema valid。
- AC-2: triangulation 平均誤差 ≤ scene scale の 1%（synthetic noise なし）。
- AC-3: `derived_from` DAG が閉じており、循環なし。
- AC-4: `--inject` 各モードで validation harness が **明示的に** 失敗を返す。
- AC-5: full run が CPU のみ・30 秒以内に完走（NFR-1）。
- AC-6: 同一 seed で再実行した結果が tolerance 内で一致。

### 13.3 Acceptance criteria for Layer 2

- AC-7: 1 つ以上の公式データセット slice を `event-frame-2d` 等に変換できる。
- AC-8: ライセンス・帰属・取得手順が README に明記され、データ自体は非同梱。

### 13.4 Acceptance criteria for Layer 3

- AC-9: mock provider で deterministic な `vllm-summary` を出す。
- AC-10: `vllm-summary.derived_from` が evidence 群をすべて指す。
- AC-11: CI で API key なしに完走する。

## 14. Non-Goals / 明示的に対象外

- **No realtime streaming.** イベントを live で処理する pipeline は対象外（オフライン処理のみ）。
- **No neural models in the core demo.** SNN / CNN / detector などは Layer 1 / 2 のコアでは使わない。
- **No production-grade tracking accuracy.** 多目的 tracker を競合する目的ではない。プロファイル検証用のリファレンス実装。
- **No dataset redistribution.** DSEC / MVSEC 等の再配布は行わない。download 手順のみ。
- **No heavy 3D renderer initially.** Three.js / Open3D / WebGL の本格 viewer は不要。top-view 2D で十分。
- **No GPU requirement.** GPU を **必須** にしない。任意の高速化は可。
- **No new asset profile design here.** プロファイル本体の設計は `multi-event-camera-spatial-evidence-profile-v3.md` 側で扱う。
- **No publishing/release workflow changes.** PyPI / npm publish の構成は変更しない。

## 15. Public Dataset Replay Plan / 公開データセット再生計画

### 15.1 Order of integration

1. **Layer 1 を先に固める。** 上記 AC-1〜AC-6 を満たすまで Layer 2 に着手しない。
2. **DSEC** を最初の対象とする（屋外運転、stereo event、calibration あり）。
3. その後 **MVSEC** を追加（屋内外、IMU/GPS 同期）。
4. それ以外は demand-driven。

### 15.2 License & redistribution

- 各データセットの公式ライセンスを README に転載／参照。
- データ本体および派生 binary はリポジトリに含めない。
- サンプル envelope は **adapter の入出力例として最小限** に限り、原データを復元できない形に留める（必要に応じてダウンサンプル）。
- 第三者著作物への帰属を envelope の `provenance` / `attribution` フィールドに記録する。

### 15.3 Download instructions

- `samples/v3/public-dataset-replay/download/` に shell script / Python script の **取得補助** のみを置く。
- スクリプトは公式 URL を踏むだけで、自動再配布は行わない。
- 取得後のローカルパスを CLI に渡す形（`--input /local/path`）。

## 16. Claude Code Ticket — M2-SYNTH-001 / 実装チケット

> 本書は要件・設計のみ。下記は Claude Code 実装エージェントが Layer 1 を着手するためのチケット雛形。

**Ticket ID:** M2-SYNTH-001
**Title:** Build synthetic multi-event-camera debug demo (v3 Layer 1)
**Priority:** P0 (v3 のすべてに先行する reference fixture)

### 16.1 Goal

v3 プロファイルの **reference fixture** として、合成された 2 台以上のイベントカメラから `event-frame-2d` / `event-tracklet-3d` / `motion-evidence-3d` を決定的に生成し、ground truth と突き合わせ可能なデモを実装する。

### 16.2 Requirements

- §4.1, §6.1 (FR-L1.*), §7 (NFR-1〜8), §8 のデバッグ対象を満たす。
- §9 のディレクトリ構成 (`samples/v3/synthetic-debug-demo/`) に従う。
- §11 の CLI / API 形状を **proposed** として実装する（細部は実装時調整可）。
- 既存 v1 / v2 アセットおよび schema を破壊しない。

### 16.3 Outputs

- `samples/v3/synthetic-debug-demo/` 一式（config, expected, assertions）。
- 新規モジュール `spatial_asset_v3.demos.synthetic`（Python）と必要に応じた TypeScript 対応。
- v3 JSON schema（別チケット M2-SCHEMA-* で扱う場合は本チケットでは依存のみ宣言）。
- ground truth と推定値を比較する `validate` ハーネス。

### 16.4 Tests

- §13.1 の unit / schema / golden-file / failure-injection / smoke を CI に追加。
- `pytest` / `npm test` で従来の v1/v2 テストが通り続けること。

### 16.5 Acceptance Criteria

§13.2 の AC-1〜AC-6 をすべて満たす。

### 16.6 Non-Goals (このチケット内)

- Layer 2 (公開データセット) の実装。
- Layer 3 (VLLM) の実装。
- realtime / GPU / SNN。
- 本格 3D viewer。

## 17. Risks / リスク

| ID | リスク | 影響 | 緩和策 |
|---|---|---|---|
| R-1 | 合成データが実データの難しさを過小評価し、Layer 2 で大量の手戻りが出る。 | 中 | failure injection で SNR / time skew / calibration error を意図的に注入。Layer 2 着手前に injection の網羅を要求。 |
| R-2 | `T_target_source` convention の解釈が実装者間でずれる。 | 高 | 本書 §8 と spec で明文化。テストで往復恒等性を検査。命名 lint を CI に加えることを検討。 |
| R-3 | derived_from DAG が膨らみ可読性が低下する。 | 中 | viewer の graph inspector を提供。golden file で構造を固定。 |
| R-4 | 公開データセットのライセンス見落としで再配布違反。 | 高 | データ非同梱。README に license / attribution を必ず記載。CI で禁止ファイル名を検査。 |
| R-5 | VLLM 出力の非決定性で CI が flaky になる。 | 中 | mock provider を default。実 provider はオフライン的にスナップショット記録のみ。 |
| R-6 | デモが肥大化して NFR-1 (30 秒) を超える。 | 中 | scene を最小に保つ。重い処理は extras に切り出し。 |
| R-7 | UI 実装に引っ張られコア要件が遅れる。 | 中 | UI は §12 通り段階導入、CLI/JSON で完結する前提を維持。 |

## 18. Open Questions / 未解決事項

1. v3 の正式アセット種別名は最終確定か？ (`event-frame-2d`, `event-tracklet-3d`, `motion-evidence-3d`, `vllm-summary` で良いか)
2. polarity-signed accumulator 以外（time-surface 等）を Layer 1 でどこまでサポートするか。
3. 多視点対応付けの reference 実装は epipolar geometry ベースで十分か、temporal correlation を必須化するか。
4. uncertainty 表現は共分散行列か、対角分散＋スカラ化か。schema 側との整合をどこで取るか。
5. VLLM プロンプトのバージョニングを envelope の `provenance` にどの粒度で記録するか。
6. 公開データセット adapter の Python / TypeScript 両対応は必要か、Python 先行で良いか。
7. CI 制限が厳しくなった場合、Layer 1 の実行時間目標 30 秒（NFR-1）はさらに短縮できるか。

---

**Maintainer note:** 本書は要件・設計の **生きた文書** である。Layer 1 の実装が進んだ時点で、CLI / API の "proposed" マークを正式版に更新し、AC を実測値で更新すること。
