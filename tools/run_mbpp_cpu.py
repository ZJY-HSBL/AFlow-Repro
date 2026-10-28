#!/usr/bin/env python3
"""Real zero-shot MBPP evaluation with a locally loaded, publicly available model.

Uses AFlow's unchanged CustomCodeGenerate operator and MBPP scoring semantics.
Only the model adapter and secure code-execution boundary differ from upstream.
Not equivalent to the ICLR author's model/decoding/search configuration.
"""
import argparse
import asyncio
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

from scripts.operators import CustomCodeGenerate
from tools.sandbox_mbpp import SandboxedMBPPBenchmark


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


class LocalTransformersAdapter:
    def __init__(self, name, max_new_tokens):
        import torch
        from huggingface_hub import HfApi
        from transformers import AutoModelForCausalLM, AutoTokenizer
        self.torch = torch
        self.name = name
        self.revision = HfApi().model_info(name).sha
        self.model = AutoModelForCausalLM.from_pretrained(
            name, revision=self.revision, torch_dtype=torch.float32
        ).eval()
        self.tokenizer = AutoTokenizer.from_pretrained(
            name, revision=self.revision
        )
        self.max_new_tokens = max_new_tokens
        self.prompt_tokens = 0
        self.output_tokens = 0
        torch.set_num_threads(2)

    def _infer(self, prompt):
        prompt_text = self.tokenizer.apply_chat_template(
            [{"role": "user", "content": prompt}],
            tokenize=False, add_generation_prompt=True,
        )
        inputs = self.tokenizer(prompt_text, return_tensors="pt")
        length = inputs["input_ids"].shape[-1]
        with self.torch.inference_mode():
            result = self.model.generate(
                **inputs, max_new_tokens=self.max_new_tokens,
                do_sample=False,
                pad_token_id=self.tokenizer.eos_token_id,
            )
        answer = self.tokenizer.decode(
            result[0, length:], skip_special_tokens=True
        )
        self.prompt_tokens += length
        self.output_tokens += result.shape[-1] - length
        return answer

    async def call_with_format(self, prompt, formatter):
        model_prompt = formatter.prepare_prompt(prompt)
        raw_output = await asyncio.to_thread(self._infer, model_prompt)
        valid, payload = formatter.validate_response(raw_output)
        if not valid or not isinstance(payload, dict) or not payload.get("response"):
            raise ValueError(f"Model format validation failed: {str(payload)[:200]}")
        return payload

    def get_usage_summary(self):
        return {
            "total_cost": 0.0,  # Local CPU evaluation has no priced API tokens.
            "total_input_tokens": self.prompt_tokens,
            "total_output_tokens": self.output_tokens,
        }


class DirectModelAgent:
    def __init__(self, model):
        self.model = model
        self.operator = CustomCodeGenerate(model)

    async def __call__(self, problem, entry_point):
        result = await self.operator(
            problem=problem, entry_point=entry_point, instruction=""
        )
        if "response" not in result:
            raise ValueError(f"Code generation failed: {result}")
        return result["response"], 0.0


async def evaluate(args):
    file = Path("data/datasets/mbpp_validate.jsonl")
    if not file.is_file():
        raise FileNotFoundError("Download the original AFlow author dataset first")
    rows = [json.loads(line) for line in file.read_text("utf-8").splitlines() if line.strip()]
    if not rows:
        raise ValueError("MBPP validation dataset is empty")
    output = Path(args.output)
    output.mkdir(parents=True, exist_ok=True)
    model = LocalTransformersAdapter(args.model, args.max_new_tokens)
    benchmark = SandboxedMBPPBenchmark("MBPP", str(file), str(output))
    score, _, _ = await benchmark.run_evaluation(
        DirectModelAgent(model), list(range(min(args.limit, len(rows)))),
        max_concurrent_tasks=1,
    )
    record = {
        "method": "direct_model_code_generation",
        "is_aflow_optimized": False,
        "is_paper_equivalent": False,
        "reference": "FoundationAgents/AFlow ICLR 2025 author MBPP validate data",
        "dataset_sha256": sha256(file),
        "data_rows": len(rows),
        "model": args.model,
        "model_sha": model.revision,
        "inference": "transformers CPU, float32, greedy",
        "max_new_tokens": args.max_new_tokens,
        "evaluated_examples": min(args.limit, len(rows)),
        "accuracy": float(score),
        "total_prompt_tokens": model.prompt_tokens,
        "total_generated_tokens": model.output_tokens,
        "execution": "Docker Python 3.11, no network and no host mounts",
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
    }
    (output / "model_baseline.json").write_text(
        json.dumps(record, indent=2), encoding="utf-8"
    )
    print("ACTUAL_MODEL_BASELINE=" + json.dumps(record))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--model", default="Qwen/Qwen2.5-Coder-0.5B-Instruct"
    )
    parser.add_argument("--limit", type=int, default=6)
    parser.add_argument("--max-new-tokens", type=int, default=192)
    parser.add_argument("--output", default="experiments/author-mbpp-cpu")
    args = parser.parse_args()
    if args.limit < 1 or args.max_new_tokens < 1:
        parser.error("limit and max-new-tokens must be positive")
    asyncio.run(evaluate(args))


if __name__ == "__main__":
    main()
