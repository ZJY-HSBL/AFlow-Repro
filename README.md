# AFlow-Repro

[![Reproduction checks](https://github.com/ZJY-HSBL/AFlow-Repro/actions/workflows/ci.yml/badge.svg)](https://github.com/ZJY-HSBL/AFlow-Repro/actions/workflows/ci.yml)

**AFlow (ICLR 2025 Oral): faithful source reproduction and independent evaluation.**  
**AFlow（ICLR 2025 Oral）：原始源码复现与独立实验验证。**

[ICLR 2025 paper / 正式论文](https://proceedings.iclr.cc/paper_files/paper/2025/hash/5492ecbce4439401798dcd2c90be94cd-Abstract-Conference.html) · [OpenReview](https://openreview.net/forum?id=z5uVAKwmjf) · [Official source / 官方源码](https://github.com/FoundationAgents/AFlow) · [Original README / 官方说明](docs/UPSTREAM_README.md)

> **Status / 当前状态：102 upstream text files imported with matching Git blob SHA. Offline regression tests added. The published benchmark results have NOT been reproduced.**
>
> **进度：102 个上游文本文件均已导入并通过 Git Blob SHA 一致性检查；已增加离线回归测试。原论文实验结果尚未复现。**

![AFlow conceptual pipeline](docs/workflow.svg)

## Research goal / 研究目标

AFlow optimizes code-represented Agent workflows through search, task execution, and experience feedback. **First reproduce the original code and experiments; only then study modifications.**

AFlow 通过搜索、任务执行与经验反馈来优化代码表示的 Agent 工作流。本仓库首先保持官方核心算法不变，复现其工作流优化与基准评测，再开展改进研究。

## Provenance / 源码溯源

| Item / 项目 | Description / 说明 |
|---|---|
| Upstream / 官方仓库 | [FoundationAgents/AFlow](https://github.com/FoundationAgents/AFlow) |
| Frozen commit / 固定版本 | [3f457218fc716093fe53f6df8a5d5e6379d66346](https://github.com/FoundationAgents/AFlow/commit/3f457218fc716093fe53f6df8a5d5e6379d66346) |
| Exact source verification / 哈希校验 | 102 of 102 upstream text files match |
| Source license / 许可证 | MIT, see [LICENSE](LICENSE) |
| Relocated upstream README / 原始 README | [docs/UPSTREAM_README.md](docs/UPSTREAM_README.md) |
| Not vendored / 未复制 | Three official JPG figures; externally hosted dataset and results archives |
| Core algorithm changes / 核心算法修改 | None / 无 |
| Reproduction additions / 新增 | CI, tests, tools, docs and local config example |

Details / 完整协议：[REPRODUCTION.md](docs/REPRODUCTION.md).

## Architecture / 核心模块

- **Node / Operator**: calls the model, generates code, tests or combines answers.
- **Workflow**: executable Python graph of operators.
- **Optimizer**: samples historical workflows, proposes modifications and learns from scores.
- **Evaluator**: runs real tasks and records accuracy and costs.

The original source remains in the official module layout: scripts/, benchmarks/, data/, workspace/.  
官方算法文件保持原样，以便对照验证。

## Environment / 环境

The upstream README specifies Python 3.9. Use a fresh virtual environment.

~~~bash
python3.9 -m venv .venv
source .venv/bin/activate                  # Windows: .venv\Scripts\activate
python -m pip install -r requirements-repro.txt
python -m unittest discover -s tests -v
python tools/preflight.py --dataset MBPP
~~~

The additional requirements file preserves the original pinned requirements and adds the missing direct downloader dependency (requests).

模型配置：将 config/local.example.yaml 复制到 config/config2.yaml，并修改为本地 OpenAI-compatible 模型推理端点（如 vLLM）。模型必须接受正确的名称。**本项目不依赖 Claude Code、Codex 等外部 Agent 宿主；但实际推理仍需要模型服务。**

~~~bash
cp config/local.example.yaml config/config2.yaml
~~~

A locally hosted model is an **adaptation**. It does not by itself reproduce the exact published metrics, which depend on model choice and inference settings.

## Dataset / 数据集

The authors publish archives outside GitHub, and raw data is intentionally not included here. Download the benchmark data only:

~~~bash
python -c "from data.download_data import download; download(['datasets'])"
python tools/preflight.py --dataset MBPP --strict
~~~

Inspect the archive and dataset filenames before execution. Data and generated-code execution must run in a disposable, restricted environment.

## Baseline / 基线

The frozen upstream run_baseline.py references workflow rounds absent from the official source tree. A separate, clearly labeled direct-model baseline runner was added; it uses the original CustomCodeGenerate operator and MBPPBenchmark evaluator.

~~~bash
# Two examples only: smoke test, NOT paper result
python tools/run_mbpp_baseline.py --model local-executor --split validate --limit 2
# Full validation baseline
python tools/run_mbpp_baseline.py --model local-executor --split validate
~~~

## AFlow optimization / 原方法工作流搜索

The official search entrypoint is left untouched:

~~~bash
python run.py --dataset MBPP --sample 4 --initial_round 1 --max_rounds 20 \
  --validation_rounds 5 --opt_model_name local-optimizer --exec_model_name local-executor
~~~

After freezing workflow selection, evaluate exactly once on the untouched test split. For the direct baseline:

~~~bash
python tools/run_mbpp_baseline.py --model local-executor --split test --allow-test
~~~

Do not use the test split to select prompts, workflow versions or hyperparameters. The original evaluator executes generated Python. Its thread timeout is **not a security sandbox**.

## Actual results only / 真实实验数据可视化

When a real optimization run has produced an actual results file, create its curve:

~~~bash
python tools/plot_results.py --input workspace/MBPP/workflows/results.json \
  --output experiments/mbpp/validation_curve.svg --title "MBPP measured validation accuracy"
~~~

No fabricated plots or paper-sourced results are presented as measurements. Real experiments must record checkpoint and dataset checksums, model/decoding parameters, search budget, seeds, raw trajectories and error cases.

## Progress / 复现进度

- [x] Confirm ICLR 2025 and pin the exact upstream commit.
- [x] Import and verify 102 upstream text files against original Git blob hashes.
- [x] Add offline tests, experiment preflight, MBPP baseline runner and measured-curve plotter.
- [x] CI green: Python 3.9 syntax, 18 offline tests, CLI import smoke tests.
- [ ] Download benchmark data and run a real-model baseline.
- [ ] Run official AFlow search and save raw optimization trajectories.
- [ ] Perform untouched test evaluation and multi-seed statistical analysis.
- [ ] Publish reproducible experimental plots and reports via GitHub Releases.

## Acknowledgement / 致谢

Independent reproduction, not an official AFlow release. Original method and MIT-licensed code belong to Jiayi Zhang et al. and FoundationAgents. Cite the [ICLR 2025 paper](https://openreview.net/forum?id=z5uVAKwmjf) and credit the [official project](https://github.com/FoundationAgents/AFlow).
