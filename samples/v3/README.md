# MCP Spatial Asset Profile v3 — Samples

v3 extends the profile to **multi-event-camera spatial/motion evidence**.

## Structure

```
samples/v3/
  synthetic-debug-demo/   # Layer 1 — reference fixture (★ start here)
  public-dataset-replay/  # Layer 2 — adapters for DSEC / MVSEC (not yet implemented)
  vllm-explanation-demo/  # Layer 3 — VLLM summary generation (not yet implemented)
```

## Layer ordering

Layer 1 must pass all acceptance criteria before Layer 2 or 3 are started.

## Schema locations

```
spec/v3/
  spatial-asset-v3.schema.json   # Asset envelopes (event-frame-2d, event-tracklet-3d,
                                 #   motion-evidence-3d, vllm-summary)
  cameras.schema.json            # Camera rig configuration
  scene.schema.json              # Scene / trajectory configuration
  ground-truth.schema.json       # Assertion harness ground truth
```

## Quick validation

```bash
python -m pytest tests/test_v3_schemas.py
```
