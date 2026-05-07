# Aura — Runbook

Bring up the orchestrator locally, run the iOS app, train a LoRA on the RTX 4080, export GGUF, run the test suite, and replay the demo. Real commands per the repo layout in `plan.md` §19 and the bootstrap notes in `technical_spec.md` §13.

All paths assume the repo root at `/Users/shauryapunj/Desktop/Samsung Hack/aura`.

---

## 1. Prerequisites

macOS 14+ on Apple Silicon for the iOS dev host. Xcode 16 installed. Android Studio Koala for the emulator path. Homebrew for fonts and uv. The Alienware M16 R1 (RTX 4080 Laptop, 12 GB VRAM) for LoRA training; CUDA 12.x, Python 3.11, PyTorch 2.4 with CUDA wheel.

```bash
# Mac side — fonts, Python toolchain
brew install --cask font-fraunces
brew install --cask font-inter
brew install uv

# RTX 4080 box — verify CUDA
nvidia-smi
python -c "import torch; print(torch.cuda.is_available(), torch.cuda.get_device_name(0))"
```

---

## 2. Repo bootstrap

```bash
cd "/Users/shauryapunj/Desktop/Samsung Hack/aura"
uv venv --python 3.11 .venv
source .venv/bin/activate
uv pip install -r requirements.txt
```

`requirements.txt` is fixed in `technical_spec.md` §13.3.

---

## 3. Bring up the orchestrator locally (Mac, MLX path)

The orchestrator can run in a Python reference implementation against synthetic fixtures, with the LLM served by MLX on Apple Silicon.

```bash
# Pull a Gemma 2B for smoke test
python -m mlx_lm.generate \
  --model mlx-community/gemma-2b-it-4bit \
  --prompt "respond with the word ok" \
  --max-tokens 4

# Pull Phi-3-mini for the orchestrator
python -m mlx_lm.generate \
  --model mlx-community/Phi-3-mini-4k-instruct-4bit \
  --prompt "tool call: classify" \
  --max-tokens 4

# Run a one-shot orchestrator tick from a fixture
python -m orchestrator.cli \
  --once \
  --fixture e2e/journeys/monday_brief.replay.json
```

Expected output: a JSON Reasoning Trace conforming to `trace.v1.json` printed to stdout. If the trace fails schema validation the CLI exits non-zero and writes the offending payload to `errors/quarantine_traces.jsonl`.

For interactive replay across all five user journeys:

```bash
python -m orchestrator.cli \
  --replay e2e/journeys/ \
  --speed 4x
```

---

## 4. Run the iOS app

```bash
open "apps/ios/Aura.xcworkspace"
```

In Xcode: select the `Aura` scheme, target an iPhone simulator (iPhone 15 or 14) or a paired physical device. Build and run.

First-launch checklist (manual):

- Permission flow: HealthKit, EventKit, Gmail OAuth, Notifications, Custom Keyboard.
- Confirm the Settings → Memory tab opens.
- Confirm the Silence Budget shows three filled dots.
- Trigger a synthetic Morning Brief via the dev menu (long-press the title bar in debug builds) and verify the Reasoning Trace drawer renders all five sections.

If GoogleSignIn fails with a redirect URI error, verify `GIDClientID` in `Info.plist` matches the OAuth client in the Google Cloud Console.

For TestFlight distribution to pilot users (`pilot/qual_protocol.md`):

```bash
xcodebuild -workspace apps/ios/Aura.xcworkspace \
  -scheme Aura \
  -archivePath build/Aura.xcarchive \
  archive

xcodebuild -exportArchive \
  -archivePath build/Aura.xcarchive \
  -exportPath build/export \
  -exportOptionsPlist apps/ios/ExportOptions.plist
```

---

## 5. Run the Android app (emulator path, ADR-0006)

```bash
cd apps/android
./gradlew assembleDebug
```

Open Android Studio Koala, launch the Galaxy AVD (Galaxy S22 image; download via SDK Manager → System Images), install the APK:

```bash
adb install -r app/build/outputs/apk/debug/app-debug.apk
```

Enable Notification Access for Aura: Settings → Apps → Special access → Notification access → Aura → ON.

For Health Connect mock data on the emulator, use the Health Connect Toolbox app from the Play Store; seed HRV and sleep records before running the WellnessAgent smoke test.

---

## 6. Train a LoRA on the RTX 4080

Run on the Alienware M16 R1. Reference: `technical_spec.md` §9.

```bash
cd "/path/to/aura"  # whatever path the Windows / Linux box uses
source .venv/bin/activate

# Step 1 — collect and anonymise data
python scripts/collect_comms_data.py \
  --raw-glob "data/raw/*.txt" \
  --out data/comms_train.jsonl \
  --anonymise

# Step 2 — split
python scripts/split_dataset.py \
  --in data/comms_train.jsonl \
  --train data/comms_train.jsonl \
  --eval data/comms_eval.jsonl \
  --test data/comms_test.jsonl \
  --ratio 80,10,10

# Step 3 — train
accelerate launch models/lora/train_comms.py \
  --base-model google/gemma-2b-it \
  --train-file data/comms_train.jsonl \
  --eval-file data/comms_eval.jsonl \
  --lora-r 16 \
  --lora-alpha 32 \
  --target-modules q_proj,v_proj,o_proj \
  --epochs 3 \
  --lr 2e-4 \
  --bf16 true \
  --max-seq-length 1024 \
  --gradient-accumulation-steps 4 \
  --output-dir models/lora/comms_v1

# Step 4 — eval
python models/eval/eval_comms.py \
  --model-dir models/lora/comms_v1 \
  --test-file data/comms_test.jsonl \
  --report models/eval/reports/comms_v1.json
```

Expected wall-clock on RTX 4080 12 GB: ~2.5 hours per epoch with QLoRA r=16, bf16, 4-bit base. Total 5 hours for two iterations including hyperparameter tweaks.

Train loss starts ~2.4, ends ~0.6 by epoch 3; eval loss tracks within 0.2. Plateau after epoch 2 → early stop.

---

## 7. Export GGUF and MLX artifacts

```bash
# Merge LoRA into base
python -m peft.scripts.merge_adapter \
  --base google/gemma-2b-it \
  --adapter models/lora/comms_v1 \
  --output models/exports/gemma-2b-aura-comms-merged

# Convert to GGUF Q4_K_M for llama.cpp / Android MediaPipe path
python third_party/llama.cpp/convert.py \
  models/exports/gemma-2b-aura-comms-merged \
  --outtype q4_K_M \
  --outfile models/exports/gemma-2b-aura-comms.Q4_K_M.gguf

# Convert to MLX 4-bit for iOS dev
python -m mlx_lm.convert \
  --hf-path models/exports/gemma-2b-aura-comms-merged \
  --mlx-path models/exports/gemma-2b-aura-comms-mlx \
  -q --q-bits 4
```

Verify the GGUF file size is ~1.5 GB and the MLX directory is ~1.5 GB. [TEAM TO VERIFY] MediaPipe LLM Inference 0.10+ Gemma 2B + LoRA conversion (`technical_spec.md` §9.1).

---

## 8. Run the test suite

```bash
# Unit tests
pytest agents/ -m unit

# Property-based fuzz tests
pytest agents/ -m hypothesis

# Latency assertions via pytest-benchmark
pytest agents/ -m benchmark

# Orchestrator state-machine tests
pytest orchestrator/tests/

# End-to-end journey replays (smoke set)
pytest e2e/ -m journey

# Full nightly run including all fixtures
pytest e2e/ --tb=short
```

Coverage target per `technical_spec.md` §12.1: 85% line, 75% branch per agent.

Update golden traces only with `UPDATE_GOLDEN=1`:

```bash
UPDATE_GOLDEN=1 pytest e2e/ -m journey
```

---

## 9. Replay the demo

The Phase 1 / Phase 2 demo runs five segments per `plan.md` §28: Morning Brief, Quiet Group Chat, Closed-Loop Stress, Spend Mirror, Memory Graph.

Live device path:

```bash
# 1. Wake iPhone, ensure Apple Watch is paired and worn.
# 2. Open Aura. Verify Silence Budget = 3.
# 3. Trigger demo notification storm from Mac:
python scripts/demo_notif_storm.py --target-device <udid> --count 47 --window-min 8

# 4. Trigger synthetic HRV drop via the dev menu (long-press title bar -> "Inject HRV drop").
# 5. Send a synthetic UPI SMS via the dev menu -> "Inject UPI debit".
# 6. Open Memory tab -> Export to JSON -> Audit log roots.
```

Backup video path (if live fails):

```bash
open "deck/phase3_pitch/demo_backup_90s.mp4"
```

The 90-second backup video is cued and ready on the laptop per `plan.md` §28 backup protocol.

---

## 10. Pilot data analysis

```bash
cd pilot/analysis
jupyter lab loadscore_eval.ipynb
```

The notebook reads anonymised raw CSVs from `pilot/analysis/raw_phase2.csv`, computes Spearman ρ between Load Score and self-rated stress, runs paired t-tests for the five baseline-vs-prototype tasks, and emits a slide-9 figure pack into `pilot/analysis/figures/`.

---

## 11. Known issues and `[TEAM TO VERIFY]`

- sqlite-vss + SQLCipher coexistence on Android requires a custom build. Verify in Week 4 (`technical_spec.md` §6.3).
- MediaPipe LLM Inference Gemma 2B + LoRA conversion (`technical_spec.md` §9.1).
- Hot-swap of Phi-3-mini ↔ Gemma 2B + LoRA on Tier B device timing (`technical_spec.md` §8.1).
- Phi-3-mini and Gemma 2B token-per-second numbers on iPhone 14 (MLX) and S22 (MediaPipe). Measure in Week 6.

---

End of `runbook.md`.
