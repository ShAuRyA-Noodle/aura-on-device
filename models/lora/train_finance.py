"""Aura FinanceAgent LoRA fine-tune.

Spec source: technical_spec.md section 9.2 + plan.md section 15.
Hardware target: Alienware M16 R1, RTX 4080 Laptop GPU, 12 GB VRAM.

The FinanceAgent task is narrower than CommsAgent: it extracts a
structured transaction from a real Indian-bank SMS body or a Gmail
receipt subject line, and assigns one of fourteen fixed categories.
Because the task is narrower, the YAML config drops the LoRA rank
to 8 (vs 16 for Comms) and bumps epochs to 4. Everything else
- 4-bit base via bitsandbytes, paged_adamw_8bit, gradient
  checkpointing, bfloat16 compute - is identical to train_comms.py.

Pinned package versions (verified compatible on RTX 4080 + CUDA 12.1):
    torch==2.3.1
    transformers==4.43.3
    peft==0.12.0
    datasets==2.20.0
    accelerate==0.33.0
    bitsandbytes==0.43.3
    trl==0.9.6
    pyyaml==6.0.2
    tensorboard==2.17.0
    sentencepiece==0.2.0

Run:
    python -m models.lora.train_finance \
        --config models/lora/configs/finance_lora.yaml
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional


def load_yaml(path: str) -> Dict[str, Any]:
    import yaml

    with open(path, "r", encoding="utf-8") as fh:
        return yaml.safe_load(fh)


# --------------------------------------------------------------------------- #
# Prompt formatting.
#
# Finance has two co-trained tasks:
#   1. Extract (merchant, amount, currency, account_last4, ts) from SMS.
#   2. Assign a category from a fixed 14-category set.
# We collapse both into one JSON output so a single forward pass solves
# both at inference time. See agents/finance/contract for the full set.
# --------------------------------------------------------------------------- #


FINANCE_SYSTEM_PROMPT = (
    "You are Aura's FinanceAgent, an on-device transaction parser. "
    "Output a single JSON object with keys: "
    "merchant (string), amount (float, INR), currency (string, ISO-4217), "
    "account_last4 (string or null), ts (ISO-8601 string or null), "
    "category (one of food_delivery, groceries, transport, fuel, "
    "entertainment, education, rent, utilities, shopping, health, "
    "transfer_in, transfer_out, subscriptions, other). "
    "Never explain. JSON only."
)


FINANCE_CATEGORIES = (
    "food_delivery",
    "groceries",
    "transport",
    "fuel",
    "entertainment",
    "education",
    "rent",
    "utilities",
    "shopping",
    "health",
    "transfer_in",
    "transfer_out",
    "subscriptions",
    "other",
)


def format_chatml(record: Dict[str, Any]) -> str:
    """Render one finance JSONL row into a ChatML training string.

    Expected record shape (see datasets/finance/finance_train_synthetic.jsonl):
        {
            "input": "Sent Rs.350.00 from A/c **1234 to ZOMATO ...",
            "merchant": "Zomato",
            "amount": 350.0,
            "currency": "INR",
            "account_last4": "1234",
            "ts": "2026-05-07T20:42:00+05:30",
            "category": "food_delivery"
        }
    """
    user = record.get("input", "").strip()
    target = {
        "merchant": record.get("merchant", ""),
        "amount": float(record.get("amount", 0.0)),
        "currency": record.get("currency", "INR"),
        "account_last4": record.get("account_last4"),
        "ts": record.get("ts"),
        "category": record.get("category", "other"),
    }
    target_json = json.dumps(target, ensure_ascii=False)
    return (
        "<start_of_turn>system\n"
        + FINANCE_SYSTEM_PROMPT
        + "<end_of_turn>\n"
        + "<start_of_turn>user\n"
        + user
        + "<end_of_turn>\n"
        + "<start_of_turn>model\n"
        + target_json
        + "<end_of_turn>\n"
    )


# --------------------------------------------------------------------------- #
# Main pipeline.
# --------------------------------------------------------------------------- #


@dataclass
class Paths:
    config: str
    train_jsonl: str
    eval_jsonl: Optional[str]
    output_dir: str
    tb_dir: str


def resolve_paths(cfg: Dict[str, Any], project_root: Path) -> Paths:
    ds = cfg.get("dataset", {})
    train_path = ds.get("train_path", "datasets/finance/finance_train.jsonl")
    eval_path = ds.get("eval_path")
    output_dir = cfg.get(
        "output_dir", "models/exports/gemma-2b-aura-finance-adapter"
    )
    tb_dir = os.path.join(output_dir, "tb")
    return Paths(
        config=str(project_root),
        train_jsonl=str(project_root / train_path),
        eval_jsonl=str(project_root / eval_path) if eval_path else None,
        output_dir=str(project_root / output_dir),
        tb_dir=str(project_root / tb_dir),
    )


def _resolve_train_path(declared: str, project_root: Path) -> Path:
    candidate = Path(declared)
    if candidate.exists():
        return candidate
    synthetic = (
        project_root
        / "datasets"
        / "finance"
        / "finance_train_synthetic.jsonl"
    )
    if synthetic.exists():
        return synthetic
    raise FileNotFoundError(
        f"Neither {declared} nor {synthetic} exists. "
        "Generate the synthetic JSONL first."
    )


def build_argparser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        description="Train Aura FinanceAgent LoRA on RTX 4080 12GB."
    )
    p.add_argument(
        "--config",
        default="models/lora/configs/finance_lora.yaml",
        help="Path to YAML config (relative to project root).",
    )
    p.add_argument(
        "--project-root",
        default=str(Path(__file__).resolve().parents[2]),
        help="Project root; defaults to two levels up from this file.",
    )
    p.add_argument(
        "--dry-run",
        action="store_true",
        help="Validate config + dataset without launching training.",
    )
    return p


def main() -> int:
    args = build_argparser().parse_args()
    project_root = Path(args.project_root).resolve()

    cfg_path = project_root / args.config
    if not cfg_path.exists():
        print(f"[fatal] config not found: {cfg_path}", file=sys.stderr)
        return 2
    cfg = load_yaml(str(cfg_path))
    paths = resolve_paths(cfg, project_root)

    train_path = _resolve_train_path(paths.train_jsonl, project_root)
    print(f"[info] training data: {train_path}")
    print(f"[info] output dir   : {paths.output_dir}")
    print(f"[info] categories   : {len(FINANCE_CATEGORIES)} fixed labels")

    if args.dry_run:
        n = 0
        with open(train_path, "r", encoding="utf-8") as fh:
            for line in fh:
                if line.strip():
                    n += 1
        print(f"[dry-run] {n} training rows in {train_path}")
        return 0

    import torch
    from datasets import load_dataset
    from peft import LoraConfig, get_peft_model, prepare_model_for_kbit_training
    from transformers import (
        AutoModelForCausalLM,
        AutoTokenizer,
        BitsAndBytesConfig,
        EarlyStoppingCallback,
        TrainingArguments,
    )
    from trl import SFTTrainer

    if not torch.cuda.is_available():
        print(
            "[fatal] CUDA is not available. This script targets RTX 4080 "
            "local. Install CUDA 12.1 drivers and bitsandbytes>=0.43.",
            file=sys.stderr,
        )
        return 3

    base_model_name = cfg["base_model"]
    quant_cfg = cfg.get("quantization", {})
    bnb = BitsAndBytesConfig(
        load_in_4bit=quant_cfg.get("load_in_4bit", True),
        bnb_4bit_quant_type=quant_cfg.get("bnb_4bit_quant_type", "nf4"),
        bnb_4bit_compute_dtype=getattr(
            torch, quant_cfg.get("bnb_4bit_compute_dtype", "bfloat16")
        ),
        bnb_4bit_use_double_quant=quant_cfg.get(
            "bnb_4bit_use_double_quant", True
        ),
    )
    tokenizer = AutoTokenizer.from_pretrained(
        base_model_name, use_fast=True, trust_remote_code=False
    )
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token

    model = AutoModelForCausalLM.from_pretrained(
        base_model_name,
        quantization_config=bnb,
        torch_dtype=torch.bfloat16,
        device_map={"": 0},
        attn_implementation="sdpa",
    )
    model = prepare_model_for_kbit_training(
        model, use_gradient_checkpointing=True
    )

    lora_cfg = cfg["lora"]
    peft_cfg = LoraConfig(
        r=lora_cfg.get("r", 8),
        lora_alpha=lora_cfg.get("alpha", 16),
        lora_dropout=lora_cfg.get("dropout", 0.05),
        bias=lora_cfg.get("bias", "none"),
        task_type=lora_cfg.get("task_type", "CAUSAL_LM"),
        target_modules=lora_cfg.get(
            "target_modules", ["q_proj", "k_proj", "v_proj", "o_proj"]
        ),
    )
    model = get_peft_model(model, peft_cfg)
    model.print_trainable_parameters()

    data_files: Dict[str, str] = {"train": str(train_path)}
    if paths.eval_jsonl and Path(paths.eval_jsonl).exists():
        data_files["validation"] = paths.eval_jsonl
    ds = load_dataset("json", data_files=data_files)

    def _formatter(rows: Dict[str, List[Any]]) -> List[str]:
        out: List[str] = []
        keys = list(rows.keys())
        n = len(rows[keys[0]])
        for i in range(n):
            record = {k: rows[k][i] for k in keys}
            out.append(format_chatml(record))
        return out

    tcfg = cfg["training"]
    early = cfg.get("early_stopping", {})

    train_args = TrainingArguments(
        output_dir=paths.output_dir,
        run_name=cfg.get("run_name", "gemma-2b-aura-finance"),
        num_train_epochs=tcfg.get("num_train_epochs", 4),
        per_device_train_batch_size=tcfg.get(
            "per_device_train_batch_size", 4
        ),
        per_device_eval_batch_size=tcfg.get(
            "per_device_eval_batch_size", 4
        ),
        gradient_accumulation_steps=tcfg.get(
            "gradient_accumulation_steps", 4
        ),
        gradient_checkpointing=tcfg.get("gradient_checkpointing", True),
        learning_rate=float(tcfg.get("learning_rate", 2.0e-4)),
        lr_scheduler_type=tcfg.get("lr_scheduler_type", "cosine"),
        warmup_ratio=tcfg.get("warmup_ratio", 0.03),
        weight_decay=tcfg.get("weight_decay", 0.0),
        max_grad_norm=tcfg.get("max_grad_norm", 0.3),
        optim=tcfg.get("optim", "paged_adamw_8bit"),
        bf16=tcfg.get("bf16", True),
        fp16=tcfg.get("fp16", False),
        tf32=tcfg.get("tf32", True),
        logging_steps=tcfg.get("logging_steps", 10),
        eval_strategy=tcfg.get(
            "eval_strategy",
            "steps" if "validation" in ds else "no",
        ),
        eval_steps=tcfg.get("eval_steps", 50),
        save_strategy=tcfg.get("save_strategy", "steps"),
        save_steps=tcfg.get("save_steps", 100),
        save_total_limit=tcfg.get("save_total_limit", 3),
        load_best_model_at_end=(
            tcfg.get("load_best_model_at_end", True)
            and "validation" in ds
        ),
        metric_for_best_model=tcfg.get("metric_for_best_model", "eval_loss"),
        greater_is_better=tcfg.get("greater_is_better", False),
        report_to=tcfg.get("report_to", ["tensorboard"]),
        logging_dir=paths.tb_dir,
        seed=cfg.get("seed", 42),
        dataloader_pin_memory=True,
        remove_unused_columns=False,
    )

    callbacks = []
    if early.get("enabled", True) and "validation" in ds:
        callbacks.append(
            EarlyStoppingCallback(
                early_stopping_patience=int(early.get("patience", 3)),
                early_stopping_threshold=float(early.get("threshold", 0.005)),
            )
        )

    trainer = SFTTrainer(
        model=model,
        tokenizer=tokenizer,
        args=train_args,
        train_dataset=ds["train"],
        eval_dataset=ds.get("validation"),
        formatting_func=_formatter,
        max_seq_length=tcfg.get("max_seq_length", 1024),
        packing=tcfg.get("packing", False),
        callbacks=callbacks,
    )

    trainer.train()
    trainer.save_model(paths.output_dir)
    tokenizer.save_pretrained(paths.output_dir)
    print(f"[done] adapter saved to {paths.output_dir}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
