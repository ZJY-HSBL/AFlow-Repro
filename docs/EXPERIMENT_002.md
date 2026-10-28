# Experiment 002 — Paired output budget ablation

Runs: [160 Token](https://github.com/ZJY-HSBL/AFlow-Repro/actions/runs/40628228601) | [320 Token](https://github.com/ZJY-HSBL/AFlow-Repro/actions/runs/40628958327).

## Controls

- Both runs use the original AFlow MBPP author validation file with identical SHA256 04c54e076bb2cb1a583d8e57110e3a644ae3125699b3309104d3b8cf95436216.
- Both use Qwen/Qwen2.5-Coder-0.5B-Instruct, revision ea3f2471cf1b1f0db85067f1ef93848e38e88c25, Transformers CPU FP32 and greedy decoding.
- Same six ordered tasks, operator, prompts and isolated grading; **ONLY** max_new_tokens changed from 160 to 320.

## Measured results

| Metric | 160 Token | 320 Token |
|---|---:|---:|
| Correct | 1 / 6 | 1 / 6 |
| Accuracy | 16.67% | 16.67% |
| Generated tokens | 956 | 1,396 |
| Per-task correct indices (1-based) | 2 | 2 |

Two actual generated programs differed (tasks 1 and 4), but both remained incorrect. Paired change was 0 percentage points. With no discordant pass/fail outcomes, the exploratory exact McNemar p-value is 1.0, which does not establish equivalence of accuracy on the population.

At 320 Token, the bisect task reported a missing import rather than the prior sandbox timeout. Other mistakes remained algorithmic or assertion failures; output length alone is insufficient for the sampled tasks.

**Neither experiment ran AFlow's MCTS optimizer.** Next require a held-out workflow-search experiment and a stronger or comparable inference checkpoint. All claims are limited to the selected 6 validation tasks.

![Paired actual results](../experiments/mbpp-160-vs-320/comparison.svg)
