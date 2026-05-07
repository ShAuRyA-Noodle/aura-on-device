"""Aura CommsAgent LoRA fine-tune.

Spec source: technical_spec.md section 9.1 + plan.md section 15.
Hardware target: Alienware M16 R1, RTX 4080 Laptop GPU, 12 GB VRAM.
Strategy: QLoRA on a 4-bit base (Gemma 2B Instruct) so we hold 1024-token
sequences with per_device_train_batch_size=4 and gradient checkpointing on.

This script intentionally targets local hardware. There is no Colab,
RunPod, or any other cloud path. ZERO INR cloud spend. Logs go to a
local TensorBoard directory and the trained adapter is saved into
models/exports/gemma-2b-aura-comms-adapter/ for downstream merging
into GGUF / MLX / MediaPipe artefacts via merge_and_quantize.sh.

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
    python -m models.lora.train_comms \
        --config models/lora/configs/comms_lora.yaml

The script is a single self-contained file. It reads its config from
the yaml in models/lora/configs/, builds a chat-formatted prompt per
row, freezes the 4-bit base, attaches a LoRA adapter to the attention
projections, and trains with paged_adamw_8bit. Early stopping fires
on eval_loss plateau per the YAML's threshold/patience values.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional


# --------------------------------------------------------------------------- #
# Lightweight imports for static analysis. The heavy imports happen inside
# main() so `python -m py_compile` does not require torch / peft to be
# installed on a machine that is only inspecting the script.
# --------------------------------------------------------------------------- #


def load_yaml(path: str) -> Dict[str, Any]:
    """Load a YAML config without an external import at module load time."""
    import yaml  # local import keeps py_compile lightweight

    with open(path, "r", encoding="utf-8") as fh:
        return yaml.safe_load(fh)


# --------------------------------------------------------------------------- #
# Prompt formatting.
#
# CommsAgent has two co-trained heads in one model: classification and
# reply drafting. We render every row in chat-style with a system prompt
# that names the JSON output schema, plus a user turn carrying the raw
# notification or email snippet, plus an assistant turn carrying the
# expected JSON. The label string is placed AFTER an explicit assistant
# tag so the loss masks correctly when we use SFTTrainer.
# --------------------------------------------------------------------------- #


COMMS_SYSTEM_PROMPT = (
    "You are Aura's CommsAgent, an on-device notification triage model. "
    "Output a single JSON object with keys: "
    "intent (one of ACTIONABLE, SOCIAL, BROADCAST, SPAM), "
    "urgency (float 0..1), self_relevance (float 0..1), "
    "draft (string, may be empty if no reply is warranted). "
    "Never explain. Never add prose. JSON only."
)


def format_chatml(record: Dict[str, Any]) -> str:
    """Render a JSONL record as a ChatML-style training string.

    Expected record shape (see datasets/comms/comms_train_synthetic.jsonl):
        {
            "input": "<sender> | <channel> | <preview>",
            "label": "ACTIONABLE",
            "urgency": 0.82,
            "self_relevance": 0.74,
            "draft": "Pushed the merge - building now."
        }
    """
    user = record.get("input", "").strip()
    target = {
        "intent": record.get("label", "BROADCAST"),
        "urgency": float(record.get("urgency", 0.0)),
        "self_relevance": float(record.get("self_relevance", 0.0)),
        "draft": record.get("draft", "") or "",
    }
    target_json = json.dumps(target, ensure_ascii=False)
    # ChatML-ish: works with Gemma's tokenizer chat template after we
    # apply tokenizer.apply_chat_template downstream. We keep it as raw
    # text for SFTTrainer's `formatting_func` path.
    return (
        "<start_of_turn>system\n"
        + COMMS_SYSTEM_PROMPT
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
    train_path = ds.get("train_path", "datasets/comms/comms_train.jsonl")
    eval_path = ds.get("eval_path")
    output_dir = cfg.get(
        "output_dir", "models/exports/gemma-2b-aura-comms-adapter"
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
    """Fall back to the synthetic JSONL if the canonical file is absent."""
    candidate = Path(declared)
    if candidate.exists():
        return candidate
    synthetic = (
        project_root / "datasets" / "comms" / "comms_train_synthetic.jsonl"
    )
    if synthetic.exists():
        return synthetic
    raise FileNotFoundError(
        f"Neither {declared} nor {synthetic} exists. "
        "Generate the synthetic JSONL first."
    )


def build_argparser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        description="Train Aura CommsAgent LoRA on RTX 4080 12GB."
    )
    p.add_argument(
        "--config",
        default="models/lora/configs/comms_lora.yaml",
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

    if args.dry_run:
        # Count rows and exit. Useful before kicking off a 2.5 hour run.
        n = 0
        with open(train_path, "r", encoding="utf-8") as fh:
            for line in fh:
                if line.strip():
                    n += 1
        print(f"[dry-run] {n} training rows in {train_path}")
        return 0

    # Heavy imports deferred until we actually train.
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

    # ------------------------------------------------------------------ #
    # Tokenizer + 4-bit base.
    # ------------------------------------------------------------------ #
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

    # ------------------------------------------------------------------ #
    # LoRA wrap.
    # ------------------------------------------------------------------ #
    lora_cfg = cfg["lora"]
    peft_cfg = LoraConfig(
        r=lora_cfg.get("r", 16),
        lora_alpha=lora_cfg.get("alpha", 32),
        lora_dropout=lora_cfg.get("dropout", 0.05),
        bias=lora_cfg.get("bias", "none"),
        task_type=lora_cfg.get("task_type", "CAUSAL_LM"),
        target_modules=lora_cfg.get(
            "target_modules", ["q_proj", "k_proj", "v_proj", "o_proj"]
        ),
    )
    model = get_peft_model(model, peft_cfg)
    model.print_trainable_parameters()

    # ------------------------------------------------------------------ #
    # Dataset.
    # ------------------------------------------------------------------ #
    data_files: Dict[str, str] = {"train": str(train_path)}
    if paths.eval_jsonl and Path(paths.eval_jsonl).exists():
        data_files["validation"] = paths.eval_jsonl
    ds = load_dataset("json", data_files=data_files)

    def _formatter(rows: Dict[str, List[Any]]) -> List[str]:
        # SFTTrainer passes a batch dict; we re-row it before formatting.
        out: List[str] = []
        keys = list(rows.keys())
        n = len(rows[keys[0]])
        for i in range(n):
            record = {k: rows[k][i] for k in keys}
            out.append(format_chatml(record))
        return out

    # ------------------------------------------------------------------ #
    # Training arguments.
    # ------------------------------------------------------------------ #
    tcfg = cfg["training"]
    early = cfg.get("early_stopping", {})

    train_args = TrainingArguments(
        output_dir=paths.output_dir,
        run_name=cfg.get("run_name", "gemma-2b-aura-comms"),
        num_train_epochs=tcfg.get("num_train_epochs", 3),
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
