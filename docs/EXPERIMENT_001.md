# Experiment 001 — Real MBPP direct-model baseline

Actual run: https://github.com/ZJY-HSBL/AFlow-Repro/actions/runs/40628228601

## Fixed protocol

- Dataset: original author AFlow MBPP validation (86 examples), first six tasks only.
- Dataset SHA-256: 04c54e076bb2cb1a583d8e57110e3a644ae3125699b3309104d3b8cf95436216
- Model: Qwen/Qwen2.5-Coder-0.5B-Instruct; checkpoint revision ea3f2471cf1b1f0db85067f1ef93848e38e88c25.
- PyTorch/Transformers CPU float32, greedy decoding, max 160 new tokens.
- Unmodified AFlow CustomCodeGenerate and CodeFormatter; original MBPP scoring semantics with code executed in an isolated no-network Docker container (Python 3.11).
- Crucial: this is a local-model baseline, **NOT** AFlow MCTS optimization or a paper-equivalent reproduction.

## Results

- Correct: 1 of 6; pass rate 16.67%. Per-task scores: 0, 1, 0, 0, 0, 0.
- Prompt tokens: 677. Generated tokens: 956 out of maximum 960 (6 × 160).
- Among the five failed tasks, four produced AssertionError and one exceeded the sandbox wall-time timeout.
- The high token-budget utilization suggests truncated code may be a confound, but does not establish that as the cause of every failure.
- Sample size six is too small to estimate benchmark performance. No significance or paper improvement is claimed.

## Follow-up

Use the same six validation examples, checkpoint, prompt, code grader and greedy decoding; change ONLY max_new_tokens from 160 to 320. Compare per-task correctness and total output tokens. This is a controlled decoding-length ablation, not an AFlow optimization result.

![Real six-task results](../experiments/mbpp-cpu-160/scores.svg)
