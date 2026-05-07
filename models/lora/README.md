# Aura — LoRA Training Playbook

Local fine-tuning recipe for Aura's two on-device agents:

- **CommsAgent** — Gemma 2B Instruct + LoRA r=16 on notification triage + reply drafting.
- **FinanceAgent** — Gemma 2B Instruct + LoRA r=8 on Indian-bank SMS + Gmail-receipt parsing.

The third config (`orchestrator_lora.yaml`) is **Phase 2 contingent** — it only runs if `models/eval/eval_orchestrator.py` reports a tool-call hallucination rate above 5% on the replay fixture, in which case we fine-tune Phi-3-mini on synthetic orchestrator traces. Until that bar is crossed we ship Phi-3-mini off-the-shelf with a deterministic system prompt and JSON-schema-validated tool calls.

> **Locked compute.** Everything in this folder targets the **Alienware M16 R1 — RTX 4080 Laptop GPU, 12 GB VRAM**. There is no Colab, no RunPod, no cloud GPU. Total cloud spend for training: **₹0**.

---

## 1. Hardware prerequisites

| Component | Requirement |
|---|---|
| GPU | NVIDIA RTX 4080 Laptop (12 GB VRAM) — or any 12 GB+ Ampere/Ada |
| CUDA | 12.1 or 12.4 (driver ≥ 535 on Linux, ≥ 552 on Windows) |
| RAM | 32 GB recommended, 16 GB minimum |
| Disk | ~25 GB free for base weights + adapters + GGUF exports |
| OS | Windows 11 with WSL2 Ubuntu 22.04, or Ubuntu 22.04 native |

Verify the GPU is visible:

```bash
nvidia-smi
python -c "import torch; print(torch.cuda.is_available(), torch.cuda.get_device_name(0))"
```

If `torch.cuda.is_available()` returns `False`, fix the driver / CUDA install before reading further. The training scripts hard-fail in that case.

---

## 2. Environment setup

We pin every package the training scripts touch. Versions below are the set verified against `bitsandbytes 0.43.3` + CUDA 12.1 on RTX 4080.

```bash
# Project root: aura/
python -m venv .venv
source .venv/bin/activate            # on Windows: .venv\Scripts\activate

pip install --upgrade pip wheel

# Pin file (also mirrored in models/lora/requirements-train.txt if you create one)
pip install \
  torch==2.3.1 \
  transformers==4.43.3 \
  peft==0.12.0 \
  datasets==2.20.0 \
  accelerate==0.33.0 \
  bitsandbytes==0.43.3 \
  trl==0.9.6 \
  pyyaml==6.0.2 \
  tensorboard==2.17.0 \
  sentencepiece==0.2.0
```

For the merge/quantize step you additionally need:

```bash
# llama.cpp is auto-cloned by merge_and_quantize.sh into third_party/llama.cpp
sudo apt install -y cmake build-essential   # one-time

# Mac dev box only:
pip install mlx-lm==0.16.0
```

---

## 3. Dataset preparation

Synthetic seed datasets live next to this folder:

- `datasets/comms/comms_train_synthetic.jsonl` — 200 hand-crafted WhatsApp / Insta / Slack / Gmail rows, cross-product of urgency × intent. Indian college context throughout (Anu, Manish, Riya, Kabir, Mira; Thapar / Christ University; HDFC / SBI / ICICI / Axis; Zomato / Swiggy / Blinkit / IRCTC).
- `datasets/finance/finance_train_synthetic.jsonl` — 100 real-format Indian-bank SMS + 50 Gmail receipt subjects.

You can train directly off the synthetic JSONL by running with `--config models/lora/configs/comms_lora.yaml` and letting the script auto-fall-back to `*_train_synthetic.jsonl` when the canonical `*_train.jsonl` is absent.

For the real run, merge synthetic + self-collected (with consent) rows into `comms_train.jsonl` / `finance_train.jsonl` and create matching `*_eval.jsonl` 80/10/10 splits.

---

## 4. Run commands

```bash
# Comms — ~2.5 hours on a single RTX 4080 with the synthetic 200-row seed.
python -m models.lora.train_comms \
  --config models/lora/configs/comms_lora.yaml

# Finance — ~1.5 hours.
python -m models.lora.train_finance \
  --config models/lora/configs/finance_lora.yaml

# Smoke test without launching training (validates config + data path):
python -m models.lora.train_comms --dry-run
python -m models.lora.train_finance --dry-run

# Launch TensorBoard for live loss curves:
tensorboard --logdir models/exports/gemma-2b-aura-comms-adapter/tb --port 6006
```

The scripts save adapters to:

- `models/exports/gemma-2b-aura-comms-adapter/`
- `models/exports/gemma-2b-aura-finance-adapter/`

Both also persist tokenizer + config so the merge step is fully self-contained.

---

## 5. Expected wall-clock and loss curves

| Run | Rows | Epochs | Wall-clock (RTX 4080) | Train loss start → end | Eval loss target |
|---|---|---|---|---|---|
| Comms LoRA | ~5,000 | 3 | ~2.5 h | 2.4 → 0.6 | within 0.2 of train |
| Comms LoRA (synthetic-only seed) | 200 | 3 | ~10 min | 2.6 → 1.0 | within 0.3 of train |
| Finance LoRA | ~2,000 | 4 | ~1.5 h | 2.1 → 0.5 | within 0.2 of train |
| Finance LoRA (synthetic-only seed) | 150 | 4 | ~8 min | 2.3 → 0.8 | within 0.3 of train |

Two retraining iterations are budgeted for each agent (so 5 wall-clock hours for Comms, 3 for Finance). Total compute budget across all training runs: ~19 hours, ₹0.

### How to read the curves

- **Healthy training:** train loss falls smoothly, eval loss tracks within 0.2 by step 100, neither curve flips upward in the last quarter.
- **Plateau:** eval loss flat for ≥ 3 evaluation calls (`patience=3`, `threshold=0.005` per the YAML). Early stopping fires automatically; treat the resulting checkpoint as the best one.
- **Divergence:** eval loss climbs while train loss falls — overfitting. Reduce `lora.r`, raise `lora.dropout`, or cut `num_train_epochs`.
- **Stagnation above 1.5 by step 200:** dataset or prompt-format problem. Re-check that the formatter in `train_comms.py::format_chatml` matches the JSONL schema.

---

## 6. Convert adapters to GGUF / MLX / MediaPipe

```bash
# From project root.
bash models/lora/merge_and_quantize.sh comms
bash models/lora/merge_and_quantize.sh finance

# RTX 4080 box: skip MLX (Apple Silicon only).
bash models/lora/merge_and_quantize.sh comms --skip-mlx
```

Outputs:

- `models/exports/gemma-2b-aura-comms-merged/` — fp16 merged HF checkpoint, the canonical source of truth.
- `models/exports/gemma-2b-aura-comms.Q4_K_M.gguf` — cross-platform GGUF for llama.cpp (used as the iOS prod and Android fallback runtime).
- `models/exports/gemma-2b-aura-comms-mlx/` — MLX 4-bit, iOS dev runtime.

### MediaPipe LLM Inference (.bin) for Android

MediaPipe consumes a different format. Convert the GGUF Q4_K_M to a MediaPipe `.bin` using the helper documented at https://ai.google.dev/edge/mediapipe/solutions/genai/llm_inference#convert_model. We do not vendor that converter into the repo because it is updated frequently. The convention is:

```bash
# Pseudo — exact CLI is the upstream MediaPipe converter for the chosen runtime version.
mediapipe-llm-converter \
  --input_path models/exports/gemma-2b-aura-comms.Q4_K_M.gguf \
  --output_path models/exports/gemma-2b-aura-comms.bin \
  --backend gpu
```

[TEAM TO VERIFY] in MediaPipe LLM Inference 0.10+ that Gemma 2B + merged LoRA round-trips through the converter. If it does not, fall back to llama.cpp through the JNI bridge on Android.

---

## 7. Hyperparameter sweep guidance

Default config is the LOCKED set. If a sweep is needed, change one knob at a time and rerun for two iterations. Knobs in priority order:

1. **`lora.r`** — 8 / 16 / 32. Comms benefits from r=16 (more head-room for reply drafting); Finance does not (narrow extraction task). Bump to 32 only if validation F1 is plateaued and VRAM allows.
2. **`training.learning_rate`** — 1e-4 / 2e-4 / 3e-4. The default 2e-4 is the QLoRA-paper default. Drop to 1e-4 if the eval loss oscillates.
3. **`training.num_train_epochs`** — 2 / 3 / 4. Stop sooner if early stopping fires before epoch 2.
4. **`lora.dropout`** — 0.0 / 0.05 / 0.10. Raise to 0.10 if eval loss flips upward in the second half of training.
5. **`lora.target_modules`** — start with `[q_proj, k_proj, v_proj, o_proj]`. Add `gate_proj`, `up_proj`, `down_proj` only if the previous four are saturated and you have VRAM left after enabling gradient checkpointing.

Every run gets a unique `run_name` in the YAML so TensorBoard can compare side-by-side. Discard any sweep that does not beat the previous best by ≥ 0.01 macro-F1 on the held-out eval set.

---

## 8. Artifact locations cheat sheet

| Artifact | Path |
|---|---|
| LoRA adapter (Comms) | `models/exports/gemma-2b-aura-comms-adapter/` |
| LoRA adapter (Finance) | `models/exports/gemma-2b-aura-finance-adapter/` |
| Merged fp16 checkpoint | `models/exports/gemma-2b-aura-{agent}-merged/` |
| GGUF Q4_K_M | `models/exports/gemma-2b-aura-{agent}.Q4_K_M.gguf` |
| MLX 4-bit | `models/exports/gemma-2b-aura-{agent}-mlx/` |
| TensorBoard logs | `models/exports/gemma-2b-aura-{agent}-adapter/tb/` |

---

## 9. Reproducibility

- `seed: 42` is locked in every YAML.
- `bf16: true`, `tf32: true`, `fp16: false` — bf16 is reproducible across Ampere/Ada GPUs.
- The training data file is a JSONL; commit the exact file used for each run alongside the adapter (we keep `datasets/comms/comms_train_synthetic.jsonl` checked in for the seed run).
- Pinned package versions are in section 2 above; export your `pip freeze` next to each adapter for forensics.

When in doubt, rerun from a clean venv with the pinned versions and the committed YAML.
