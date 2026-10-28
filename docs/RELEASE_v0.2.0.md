# v0.2.0 — Real MBPP evaluation milestone

**This is not a full numerical reproduction of AFlow's ICLR 2025 experimental results. The MCTS optimization phase is pending.**

## What was actually executed
- Successfully downloaded the original AFlow author's 15-file dataset archive; recorded SHA-256 and exact data split names.
- Verified 20/20 reference solutions on the original 86-example MBPP validation split using a Docker-isolated code execution boundary (reference oracle, not model accuracy).
- Executed a real publicly available model, Qwen2.5-Coder-0.5B-Instruct, locally on CPU with the unmodified AFlow CustomCodeGenerate operator: **1/6 passed (16.67%)**, with 160 max generated tokens. Model checkpoint pinned and raw CSV/logs uploaded as GitHub Actions artifacts.
- Recorded the author's separately published 1,538-file original workflow archive, keeping archived experiment traces separate from new measurements.
- Added tests checking source parity for all 102 upstream Git blobs, plus security checks for model-generated code execution, source and model data provenance.

## Primary evidence
- Dataset check: https://github.com/ZJY-HSBL/AFlow-Repro/actions/runs/40627997385
- 20 reference solutions: https://github.com/ZJY-HSBL/AFlow-Repro/actions/runs/40628141707
- 6 real CPU-model samples: https://github.com/ZJY-HSBL/AFlow-Repro/actions/runs/40628228601
- Real result plot: experiments/mbpp-cpu-160/scores.svg

## Limitations and next hypothesis
160-token generation saturated at 956 of a 960-token theoretical maximum, likely constraining output completeness. A paired 320-token validation ablation is being evaluated separately. The six-sample score cannot be compared directly to paper-reported optimized model accuracies.

Original algorithm code remains unchanged. CPU model inference is a reproduction adaptation, not the exact GPT-4o-based author experiment.
