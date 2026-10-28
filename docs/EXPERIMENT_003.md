# Experiment 003 — Original AFlow optimizer control flow and actual model-proposal feasibility

## Objective

Determine separately whether (i) the unmodified original AFlow optimization/control/evaluation pipeline executes end-to-end, and (ii) a small real open-weight model can generate a structurally executable graph optimization response. These are **different experiments** and their scores must never be conflated.

## A. Original optimizer with deterministic transport (integration test, NOT model search)

Evidence: https://github.com/ZJY-HSBL/AFlow-Repro/actions/runs/40632060645

- Original code: `Optimizer._optimize_graph`, `DataUtils`, `GraphUtils`, `ExperienceUtils`, and `EvaluationUtils` are used without modifying their source.
- Experimental adapter: original evaluator is restricted to first three author MBPP validation examples and executes generated code in an isolated no-network Docker container.
- A deterministic transport supplies one **scripted** AFlow workflow proposal and the author-provided reference code for every evaluated question. No neural model is used for this experiment.
- Actual results: round 1 score = 1.0 (3/3 reference solutions), round 2 score = 1.0 (3/3 reference solutions), six program executions, one proposal, one graph and one experience record.
- Original experience marks `succeed=false` because proposed and baseline scores were equal. This is correct behavior for this controlled test, not evidence of a useful model improvement.
- Discovered upstream state issue: tracked `workspace/MBPP/workflows/results.json` contains previously published scores; the CI harness isolates this file from the new experiment instead of silently mixing old and new data.

## B. Real Qwen optimization proposal (one observed model response, NOT full search)

Evidence: https://github.com/ZJY-HSBL/AFlow-Repro/actions/runs/40631906442

| Property | Measurement |
|---|---|
| Model | Qwen2.5-Coder-0.5B-Instruct |
| Model revision | ea3f2471cf1b1f0db85067f1ef93848e38e88c25 |
| Original optimizer prompt | 6,709 characters / 1,392 tokens |
| Generated tokens | 320 (limit 320) |
| Upstream XML parser | Accepted |
| Nonempty modification | No |
| Nonempty graph | Yes |
| Nonempty prompt | No |
| Generated graph parses as Python | No |
| Executed or evaluated model-generated candidate | **No** |

This result shows that the small model did not produce a usable AFlow graph modification in this one attempt. The original XML parser considers optional/defaulted fields successful even when the required downstream keys are missing. The new standalone `tools/validate_workflow_proposal.py` rejects missing fields and syntax errors before dynamic import.

## Interpretation and next controlled experiments

1. Evaluate proposal validity and Python compilability over multiple **independent, actually model-generated** proposals and larger open checkpoints, with fixed original prompts and decoding settings.
2. AFlow optimizer's original `while True` loop retries identical invalid or duplicate proposals indefinitely unless externally bounded. Limit trial time outside the algorithm, log each failure and never call timeouts successful results.
3. Once model-generated candidates pass strict preflight in a disposable sandbox, conduct multi-round original search on validation data and evaluate frozen winners on the untouched test split.
4. Record true search budget, proposal attempts, syntax success, validation pass-rate and computation cost separately.

**This phase validates the search infrastructure but does not establish the paper's optimization gain or reproduce its full benchmark tables.**

![Distinct provenance tracks](../experiments/aflow-v0.3.0/validation.svg)
