#!/usr/bin/env bash
# Aura — merge LoRA adapter into the Gemma 2B base, then export to:
#   1. GGUF Q4_K_M (cross-platform, llama.cpp + Android via MediaPipe-llama.cpp bridge)
#   2. MLX 4-bit  (iOS dev build on Apple Silicon)
#   3. Hugging Face merged checkpoint (kept as the canonical source of truth
#      for further conversions, including MediaPipe .bin via the MediaPipe
#      converter recipe documented in models/lora/README.md)
#
# This script targets the same Alienware M16 R1 (RTX 4080 12GB) that runs
# the LoRA training. It does not assume CUDA for the merge step itself
# (PEFT can dequantise on CPU) but the convert step benefits from RAM,
# so allow ~16 GB free.
#
# Usage:
#   bash models/lora/merge_and_quantize.sh comms
#   bash models/lora/merge_and_quantize.sh finance
#   bash models/lora/merge_and_quantize.sh comms --skip-mlx
#
# The script is idempotent: re-running it overwrites the export folder
# only after a successful merge.

set -euo pipefail

AGENT="${1:-}"
shift || true

if [[ -z "${AGENT}" ]]; then
  echo "usage: $(basename "$0") {comms|finance} [--skip-gguf] [--skip-mlx]" >&2
  exit 64
fi

case "${AGENT}" in
  comms|finance) ;;
  *)
    echo "[fatal] unknown agent: ${AGENT}" >&2
    exit 64
    ;;
esac

SKIP_GGUF=0
SKIP_MLX=0
for arg in "$@"; do
  case "$arg" in
    --skip-gguf) SKIP_GGUF=1 ;;
    --skip-mlx)  SKIP_MLX=1 ;;
    *)
      echo "[warn] unknown flag: ${arg}" >&2
      ;;
  esac
done

# --------------------------------------------------------------------------- #
# Resolve paths.
# --------------------------------------------------------------------------- #

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"

BASE_MODEL="google/gemma-2b-it"
ADAPTER_DIR="${PROJECT_ROOT}/models/exports/gemma-2b-aura-${AGENT}-adapter"
MERGED_DIR="${PROJECT_ROOT}/models/exports/gemma-2b-aura-${AGENT}-merged"
GGUF_OUT="${PROJECT_ROOT}/models/exports/gemma-2b-aura-${AGENT}.Q4_K_M.gguf"
MLX_OUT="${PROJECT_ROOT}/models/exports/gemma-2b-aura-${AGENT}-mlx"

LLAMA_CPP_DIR="${LLAMA_CPP_DIR:-${PROJECT_ROOT}/third_party/llama.cpp}"

echo "[info] agent          : ${AGENT}"
echo "[info] base model     : ${BASE_MODEL}"
echo "[info] adapter dir    : ${ADAPTER_DIR}"
echo "[info] merged dir     : ${MERGED_DIR}"
echo "[info] gguf out       : ${GGUF_OUT}"
echo "[info] mlx out        : ${MLX_OUT}"
echo "[info] llama.cpp at   : ${LLAMA_CPP_DIR}"

if [[ ! -d "${ADAPTER_DIR}" ]]; then
  echo "[fatal] adapter directory missing: ${ADAPTER_DIR}" >&2
  echo "        Train the adapter first with train_${AGENT}.py." >&2
  exit 2
fi

# --------------------------------------------------------------------------- #
# 1. Merge LoRA into base.
# --------------------------------------------------------------------------- #
#
# We prefer an inline Python heredoc over `peft.scripts.merge_adapter`
# because that script's CLI signature has shifted between PEFT releases.
# This block is stable against PEFT 0.10..0.13.

echo "[step] merging LoRA into base..."
python - <<PYEOF
import os
from peft import PeftModel
from transformers import AutoModelForCausalLM, AutoTokenizer

base = "${BASE_MODEL}"
adapter = "${ADAPTER_DIR}"
out = "${MERGED_DIR}"

print(f"[merge] loading base {base} in fp16 for merge")
model = AutoModelForCausalLM.from_pretrained(base, torch_dtype="auto")
print(f"[merge] attaching adapter from {adapter}")
model = PeftModel.from_pretrained(model, adapter)
print("[merge] merging weights")
model = model.merge_and_unload()
os.makedirs(out, exist_ok=True)
model.save_pretrained(out, safe_serialization=True)

tok = AutoTokenizer.from_pretrained(base)
tok.save_pretrained(out)
print(f"[merge] merged checkpoint written to {out}")
PYEOF

# --------------------------------------------------------------------------- #
# 2. GGUF Q4_K_M via llama.cpp.
# --------------------------------------------------------------------------- #

if [[ "${SKIP_GGUF}" -eq 0 ]]; then
  if [[ ! -d "${LLAMA_CPP_DIR}" ]]; then
    echo "[step] cloning llama.cpp into ${LLAMA_CPP_DIR}"
    git clone --depth 1 https://github.com/ggerganov/llama.cpp "${LLAMA_CPP_DIR}"
  fi

  pushd "${LLAMA_CPP_DIR}" > /dev/null

  if [[ ! -x "./build/bin/llama-quantize" && ! -x "./llama-quantize" ]]; then
    echo "[step] building llama.cpp (CMake, CUDA off for portability)"
    cmake -B build -DLLAMA_CURL=OFF
    cmake --build build --config Release -j
  fi

  QUANTIZE_BIN="./build/bin/llama-quantize"
  if [[ ! -x "${QUANTIZE_BIN}" ]]; then
    QUANTIZE_BIN="./llama-quantize"
  fi

  echo "[step] converting merged HF checkpoint to GGUF f16"
  python convert_hf_to_gguf.py \
    "${MERGED_DIR}" \
    --outfile "${GGUF_OUT}.f16.gguf" \
    --outtype f16

  echo "[step] quantising f16 GGUF to Q4_K_M"
  "${QUANTIZE_BIN}" \
    "${GGUF_OUT}.f16.gguf" \
    "${GGUF_OUT}" \
    Q4_K_M

  rm -f "${GGUF_OUT}.f16.gguf"
  popd > /dev/null
  echo "[ok] GGUF written to ${GGUF_OUT}"
else
  echo "[skip] GGUF export disabled"
fi

# --------------------------------------------------------------------------- #
# 3. MLX 4-bit (Apple Silicon).
# --------------------------------------------------------------------------- #
#
# This step is a no-op on the RTX 4080 box; it exists so the same script
# also runs on the M-series Mac that hosts the iOS dev build. The user
# can re-run with --skip-mlx on the Alienware to keep the script tidy.

if [[ "${SKIP_MLX}" -eq 0 ]]; then
  if python -c "import mlx_lm" 2>/dev/null; then
    echo "[step] exporting MLX 4-bit checkpoint"
    python -m mlx_lm.convert \
      --hf-path "${MERGED_DIR}" \
      --mlx-path "${MLX_OUT}" \
      -q --q-bits 4
    echo "[ok] MLX written to ${MLX_OUT}"
  else
    echo "[skip] mlx_lm not installed; install on the Mac dev box only"
  fi
else
  echo "[skip] MLX export disabled"
fi

echo "[done] merge + quantize complete for agent=${AGENT}"
