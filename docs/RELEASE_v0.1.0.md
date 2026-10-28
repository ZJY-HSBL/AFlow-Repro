# AFlow-Repro v0.1.0 — Source-Verified Baseline

This is a **source and regression-test milestone, not a reproduction of published benchmark metrics**.

- Pinned original AFlow implementation to commit `3f457218fc716093fe53f6df8a5d5e6379d66346`.
- Imported all 102 upstream text files and verified exact Git blob SHA parity.
- Original core search and evaluator logic remains unmodified.
- Added Python 3.9 offline regression tests, CI, MBPP direct-model adapter, preflight checker, real-result SVG plotting, and bilingual documentation.
- Upstream image assets and externally hosted benchmark archives are not included.

**Validation scope:** GitHub CI successfully checks Python 3.9 syntax, 18 offline tests and entrypoint imports only; it does not perform LLM calls or author-scale experiments.

**Next:** Obtain datasets, configure a selected inference model, measure direct baseline, run original MCTS workflow search, and evaluate held-out tasks.
