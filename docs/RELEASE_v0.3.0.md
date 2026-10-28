# v0.3.0 — Original AFlow optimization pipeline verification and actual proposal audit

**This release verifies an original optimizer integration loop and tests a genuine local-model proposal. It is NOT a full AFlow search-performance replication.**

## Executed work

- Original `Optimizer._optimize_graph` executed a complete 2-round control flow with 1 scripted modification and 6 sandboxed reference-answer evaluations on 3 author MBPP validation tasks. Generated Python graph and prompt imported successfully, results and experience files were saved.
- Round 1 and 2 reference scores each 3/3 because the transport uses **oracle reference solutions**. No improvement: `succeed=false`. These scores must never be interpreted as model performance.
- A separate real Qwen2.5-Coder-0.5B-Instruct optimizer proposal used the unmodified full graph-optimization prompt: 6,709 chars, 1,392 input tokens, 320 output tokens. It failed strict structure and Python compilation checks; **no AI-generated graph was evaluated**.
- Added an independent pre-import graph/prompt validation gate plus tests; preserved the original 102 text blobs unchanged and retained v0.2.0 MBPP baseline outcomes.

## Execution evidence

- Actual original optimizer and sandboxed reference evaluation: https://github.com/ZJY-HSBL/AFlow-Repro/actions/runs/40632060645
- Actual open-weight model optimizer proposal: https://github.com/ZJY-HSBL/AFlow-Repro/actions/runs/40631906442
- Analysis: docs/EXPERIMENT_003.md
- Pipeline SVG: experiments/aflow-v0.3.0/validation.svg

## Outstanding tasks

- Reproduce **genuine autonomous model-generated valid candidate graphs**, run multi-round AFlow graph search and compare against matched no-search controls.
- Freeze selected candidates and run independent MBPP test evaluation with multiple seeds and real model costs.
- Original authors' numerical results remain unverified. No fabricated MCTS improvement claims.
