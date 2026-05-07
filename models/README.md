# Aura — Models Layer

Everything model-shaped lives under this folder:

```
models/
  lora/
    configs/                   # YAML hyperparam configs — LOCKED
      comms_lora.yaml
      finance_lora.yaml
      orchestrator_lora.yaml   # Phase 2 contingent
    train_comms.py
    train_finance.py
    merge_and_quantize.sh      # LoRA -> merged HF -> GGUF Q4_K_M -> MLX 4-bit
    README.md                  # full training playbook
  eval/
    eval_comms.py
    eval_finance.py
    eval_orchestrator.py
    README.md
  exports/                     # adapters + GGUF + MLX artefacts (gitignored)
```

## Inventory

From `plan.md` §15:

| Role | Model | Quantization | Training plan |
|---|---|---|---|
| CommsAgent | Gemma 2B | Q4_K_M | LoRA r=16, ~5k examples |
| FinanceAgent | Gemma 2B | Q4_K_M | LoRA r=8, ~2k examples |
| Orchestrator | Phi-3-mini | Q4 | Off-the-shelf; LoRA Phase 2 if needed |
| Heavy fallback | Llama-3-8B Instruct | Q4 | Off-the-shelf; capable devices only |
| Embeddings | all-MiniLM-L6-v2 | int8 | Off-the-shelf |
| Prosody | Whisper-tiny encoder | int8 | Encoder only, never store transcripts |

## Compute

All training is local on the **Alienware M16 R1 — RTX 4080 Laptop GPU 12 GB VRAM**. No Colab, no RunPod. Total cloud spend across all training runs: **₹0**. Wall-clock budget per `technical_spec.md` §9.4: ~19 hours.

## Runtimes

| Platform | Runtime | Artefact |
|---|---|---|
| iOS dev | MLX | `models/exports/gemma-2b-aura-{agent}-mlx/` |
| iOS prod | llama.cpp Swift bindings | `models/exports/gemma-2b-aura-{agent}.Q4_K_M.gguf` |
| Android | MediaPipe LLM Inference (primary), llama.cpp JNI (fallback) | `.bin` from upstream MediaPipe converter, GGUF as fallback |
| Cross-platform fallback | llama.cpp | GGUF |

See `models/lora/README.md` for the full step-by-step.
