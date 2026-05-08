# Aura — On-Device LLM Inference

Real on-device generation. Two adapters share one contract:

| Adapter | Backend | Format | Where it runs |
|---|---|---|---|
| `MLXAdapter` | [`mlx-lm`](https://github.com/ml-explore/mlx-lm) | `mlx-community/...` 4-bit | Apple Silicon Mac (M-series), iOS dev |
| `LlamaCppAdapter` | [`llama-cpp-python`](https://github.com/abetlen/llama-cpp-python) | GGUF `Q4_K_M` | Linux / Windows / Android-host CI |

`registry.get_adapter(name)` picks MLX on Apple Silicon, llama.cpp
elsewhere, and raises `AdapterUnavailable` when the chosen backend is
not installed. Agents catch that and fall back to their deterministic
non-LLM path.

---

## 1. Install

### Apple Silicon (M-series Mac, iOS dev)

```bash
pip install mlx mlx-lm psutil
```

Verify:

```bash
python -c "import mlx, mlx_lm; print('MLX OK')"
```

### Linux / Windows (CI fallback, Android-host build)

```bash
# CPU-only (works everywhere):
pip install llama-cpp-python psutil

# Metal / CUDA / Vulkan: see https://github.com/abetlen/llama-cpp-python#installation
```

---

## 2. Models, downloads, disk usage

| Nickname | HF / file | Format | Disk | RAM peak | First-token (M2 Pro) |
|---|---|---|---|---|---|
| `gemma-2b-4bit` | `mlx-community/gemma-2-2b-it-4bit` | MLX 4-bit | ~1.5 GB | ~2.0 GB | ~250 ms |
| `gemma-2b-4bit` | `models/exports/gemma-2b-aura-comms.Q4_K_M.gguf` | GGUF Q4_K_M | ~1.5 GB | ~2.0 GB | ~350 ms |
| `phi-3-mini-4bit` | `mlx-community/Phi-3-mini-4k-instruct-4bit` | MLX 4-bit | ~2.3 GB | ~3.0 GB | ~600 ms |
| `phi-3-mini-4bit` | local `.Q4_K_M.gguf` | GGUF Q4_K_M | ~2.3 GB | ~3.0 GB | ~700 ms |
| `llama-3-8b-4bit` | `mlx-community/Meta-Llama-3-8B-Instruct-4bit` | MLX 4-bit | ~4.7 GB | ~6.0 GB | ~1200 ms |

First-token numbers are targets from `technical_spec.md §8.1`. Real
measurements live in `aura/benchmarks/results/llm_latency_<DATE>.json`.

### Default download locations

- MLX: `mlx-lm` lazy-pulls into `~/.cache/huggingface/hub/`. We also
  honour `~/.cache/aura/models/<nickname>/` for offline / iOS-bundle
  layouts (set `AURA_MODEL_CACHE` to override).
- GGUF: prefer `aura/models/exports/<nickname>.Q4_K_M.gguf`
  produced by `models/lora/merge_and_quantize.sh`. Falls back to
  `~/.cache/aura/models/<nickname>.Q4_K_M.gguf`.
- Per-model override: `AURA_MODEL_GEMMA_2B_4BIT=/abs/path/to/model`.

### Pre-download (CI / first-run on team Mac)

```bash
# Gemma 2B — 1.5 GB
python -m mlx_lm.generate \
  --model mlx-community/gemma-2-2b-it-4bit \
  --prompt "Hello, my name is" --max-tokens 32

# Phi-3-mini — 2.3 GB
python -m mlx_lm.generate \
  --model mlx-community/Phi-3-mini-4k-instruct-4bit \
  --prompt "test" --max-tokens 8

# Llama-3-8B — 4.7 GB; only on tier-A devices (≥16 GB RAM)
python -m mlx_lm.generate \
  --model mlx-community/Meta-Llama-3-8B-Instruct-4bit \
  --prompt "test" --max-tokens 8
```

The first MLX run for each model hits HuggingFace, then everything is
cached.

---

## 3. Switching backend at runtime

```python
from aura.models.llm import get_adapter

# Auto-detect (MLX on Apple Silicon, llama.cpp elsewhere)
adapter = get_adapter("gemma-2b-4bit")

# Pin the backend explicitly
adapter = get_adapter("gemma-2b-4bit", backend="mlx")
adapter = get_adapter("gemma-2b-4bit", backend="llamacpp")

text = adapter.generate("Hello", max_tokens=32, temperature=0.0)

import asyncio
async def stream():
    async for piece in adapter.generate_stream("Hello", max_tokens=32):
        print(piece, end="", flush=True)
asyncio.run(stream())
```

---

## 4. Wiring into the agents

The Comms / Finance / Orchestrator paths only call the LLM when **both**
of these are true:

1. `AURA_USE_LLM=1` is set in the environment.
2. The trained classifier artefact at
   `aura/models/exports/comms_classifier.pkl` exists. (We share this
   one gating file across Comms and Finance so the team flips one
   switch.)

When either condition is false, agents stay on their deterministic
heuristic / regex path. When `AURA_USE_LLM=1` but the adapter cannot
be loaded (MLX missing on a Linux host, GGUF missing on a Windows
host) the agents silently fall back to the deterministic path and
flag `model_low_conf=True` on the trace fragment.

| Caller | Trigger | Model | Prompt template |
|---|---|---|---|
| `agents/comms/agent.py::_classify_text` | top-1 prob < 0.7 | `gemma-2b-4bit` | `prompts.comms_rerank_prompt` |
| `agents/finance/agent.py::FinanceAgent.parse_sms` | regex miss | `gemma-2b-4bit` | `prompts.finance_extract_prompt` |
| `orchestrator/graph.py::_node_logging_trace` | always | `phi-3-mini-4bit` (Gemma 2B fallback) | `prompts.rationale_prompt` |

---

## 5. Tests

```bash
# Fast unit tests (no model load)
pytest aura/models/llm/ -q --tb=line -m "not slow"

# Full inference tests (loads Gemma 2B 4-bit, ~1.5 GB on first run)
pytest aura/models/llm/ -q -m slow
```

CI runs without `-m slow`; the live MLX tests are gated behind
`@pytest.mark.slow` and `is_apple_silicon()`.

---

## 6. Benchmarks

```bash
python -m aura.benchmarks.llm_latency --runs 100
python -m aura.benchmarks.llm_quality
```

Latency report: `aura/benchmarks/results/llm_latency_<DATE>.json`.
Quality report: `aura/benchmarks/results/llm_quality_<DATE>.json`.

The latency benchmark auto-includes Llama-3-8B on hosts with
≥16 GB RAM; otherwise just Gemma 2B and Phi-3-mini.

---

## 7. Shipping models with the iOS app

The MLX adapter accepts a local directory that mirrors the layout
`mlx_lm` produces:

```
aura-gemma-2b-mlx/
├── config.json
├── tokenizer.model
├── tokenizer_config.json
└── weights.npz
```

For the iOS dev build:

1. On the Mac, run `python -m mlx_lm.convert --hf-path google/gemma-2b-it
   --mlx-path aura-gemma-2b-mlx -q --q-bits 4` (or use the merged LoRA
   checkpoint from `models/lora/merge_and_quantize.sh`).
2. Copy `aura-gemma-2b-mlx/` into the iOS app target's **`Resources/`
   group** so it lands inside the app sandbox at
   `Bundle.main.url(forResource: "aura-gemma-2b-mlx", withExtension: nil)`.
3. On first launch the iOS code copies the bundle directory into the
   app's **Documents/** so the Files app can expose it (the entry in
   `Info.plist` is `LSSupportsOpeningDocumentsInPlace=YES`).
4. Set the env var equivalent on the Swift side:

   ```swift
   setenv("AURA_MODEL_GEMMA_2B_4BIT",
          documentsDir.appendingPathComponent("aura-gemma-2b-mlx").path,
          1)
   ```

5. Aura's Python bridge then resolves the model from that exact path —
   no network access required at runtime.

---

## 8. Troubleshooting

### `AdapterUnavailable: mlx_lm is not installed`

Run `pip install mlx mlx-lm`. MLX requires Apple Silicon;
on Intel Mac / Linux / Windows the registry will pick llama.cpp
instead.

### `AdapterUnavailable: GGUF model file not found: …`

The `LlamaCppAdapter` will not silently download. Run
`bash models/lora/merge_and_quantize.sh comms` (or `finance`) to
produce the GGUF, or set `AURA_MODEL_GEMMA_2B_4BIT=/path/to/your.gguf`.

### MLX first-token > 5 s

You are still in the cold-load. Run a short warm-up generate before
benchmarking. The MLX `load()` call alone is ~3-5 s for Gemma 2B 4-bit.

### `ModuleNotFoundError: No module named 'mlx'` on Linux CI

Expected. CI must run with `pytest -m "not slow"` to skip the
MLX-only tests. The fast tests cover the registry and prompt helpers
and pass on every host.

### Output looks truncated

The adapters honour the `stop` argument as a list of substrings.
Pass `stop=("<end_of_turn>", "\n\n")` to cut at Gemma's chat
delimiter. `MLXAdapter.generate` slices the accumulated text at the
earliest stop occurrence; `LlamaCppAdapter.generate` lets llama.cpp
do the same internally.
