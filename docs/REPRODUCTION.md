# Reproduction protocol / 严格复现协议

## 1. Frozen provenance / 冻结源码

- Upstream: FoundationAgents/AFlow, Git commit 3f457218fc716093fe53f6df8a5d5e6379d66346.
- 102 of 102 original text files have the same Git blob SHA. The original README was moved to docs/UPSTREAM_README.md.
- Excluded: 3 original JPG illustrations, external dataset and results archives.
- No changes to upstream algorithm implementation. Added files are confined to tests, tools, docs, CI and config examples.

## 2. Reproduction protocol / 实验顺序

1. Fix Python, package versions, model checkpoint and server parameters.
2. Download the exact author-provided benchmark splits; compute SHA256 and count instances.
3. Run offline source and regression tests.
4. Run a direct-model baseline using the same model, prompts, and evaluator.
5. Run the original AFlow optimizer on validation data; preserve graph and prompt for every round, selection probabilities, costs and raw scores.
6. Freeze workflow selection BEFORE accessing the held-out test data.
7. Repeat with independent seeds and quantify mean, standard deviation and confidence intervals where justified.
8. Report wall time, task accuracy, token/API cost, failures and differences from authors' settings.

Paper-equivalent numerical reproduction requires the same optimizer model, executor model, operators, evaluation splits, search budget and decoding behavior. A local-model variant is a valid adapted experiment but NOT a strict reproduction of the reported numeric results.

## 3. Known upstream issues (not silently changed) / 已知上游问题

- The data downloader imports requests, but upstream requirements.txt does not directly list it. Added to requirements-repro.txt.
- Original run_baseline.py imports missing workspace.MBPP.workflows.round_8.graph and workspace.LiveCodeBench.workflows.round_2.graph. The new tools/run_mbpp_baseline.py is a separately marked direct-model alternative using the upstream operator and evaluator.
- Original run.py parses --check_convergence with type=bool; textual False may still evaluate True. Do not alter or claim an override without an explicit patch record.
- Original generated-code evaluators execute untrusted Python with exec(...); a thread-level timeout cannot isolate malicious code. Evaluate only on a disposable, resource-restricted host.
- Original data downloader extracts downloaded archives. Review the archive and extraction location before use.
- Upstream authors warn some migrated operators may contain errors. Validate each encountered failure and preserve proposed fixes separately.

## 4. Evidence checklist / 必要证据

For every experiment retain: UTC date, source/reproduction git SHA, OS/Python/GPU/CUDA, model checkpoint hash, inference engine, generation parameters, archive SHA256, split identity, sample count, search iterations, sampling seeds, actual result JSON/CSV, cost accounting, logs, and error examples. Never commit credentials.

## 5. Maturity / 成熟度

- L0: Source imported and verified — completed.
- L1: CI and offline algorithm regressions — pending verified CI.
- L2: Measured direct-model MBPP baseline — pending.
- L3: AFlow search and held-out benchmark — pending.
- L4: Multi-seed experiments and statistical ablations — pending.

**There are no new experimental accuracy claims yet.**
