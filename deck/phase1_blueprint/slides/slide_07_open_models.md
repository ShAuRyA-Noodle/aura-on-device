---
slide: 7
title: Open Models planned to be used / developed / trained / fine-tuned
---
## BODY
Eight models. Three trained by us.
Gemma 2B Q4 with LoRA for Comms and Finance.
Phi-3-mini Q4 orchestrator. Llama-3-8B Q4 fallback. All on device.

## SPEAKER NOTES
Eight models, three trained by us. Gemma 2B quantised to Q4 underpins Communications and Finance, each with its own LoRA. Comms is fine-tuned on Enron-classified-public plus a small consented Indian email and notification corpus. Finance is fine-tuned on UPI SMS samples and Gmail receipt threads from Zomato, Swiggy, Blinkit, IRCTC, and Amazon India. Phi-3-mini Q4 is the orchestrator and the Calendar agent's prose engine, off-the-shelf with a system prompt for Phase 1, LoRA in Phase 2 if needed. Llama-3-8B Q4 is the heavy fallback, only routed to on devices with at least eight gigabytes of RAM and battery above thirty percent. The LSTM next-app predictor is one million parameters, our own training, trained on LSApp plus Tsinghua. MiniLM does embeddings into sqlite-vss. Whisper-tiny is encoder-only, we use prosody features, never store transcripts. Load Score is an XGBoost regressor, two hundred trees, calibrated against self-rated stress. Runtime is MediaPipe LLM Inference on Android, MLX on iOS for development, llama.cpp as cross-platform fallback. ExecuTorch evaluated for production Android.

## CITATIONS
[4] Phi-3-mini, https://arxiv.org/abs/2404.14219.
[8] Gemma, https://ai.google.dev/gemma.
[10] MediaPipe LLM Inference, https://ai.google.dev/edge/mediapipe/solutions/genai/llm_inference.
[19] llama.cpp, https://github.com/ggml-org/llama.cpp.
[20] ExecuTorch, https://pytorch.org/executorch/.
[15] LSApp for the next-app LSTM training corpus, https://arxiv.org/abs/1911.04026.
Llama-3 license terms [TEAM TO VERIFY].

## VISUAL BRIEF
Single full-width spec table. Same visual grammar as slide 4a so the deck reads as a system. Cols 1-12, table 1700x760 px. Eight rows. Header row Inter Tight 18 pt bold tracked +40: Role / Model / Size / Quantization / License / Training plan. Role in Inter Tight 22 pt, Model in JetBrains Mono 18 pt. License column uses a small #0E0E0E square glyph for permissive (MIT, Apache, Gemma) and a #FF5B2E square for vendor-licensed check before ship, applied to Gemma terms and Llama license. Right-edge thin column Owned weights with a sunset-orange dot for any row where Aura's LoRA delta is the team's own training output: CommsAgent, FinanceAgent, App-prediction LSTM, and Load Score XGBoost. Rows: CommsAgent Gemma 2B Q4 LoRA / FinanceAgent Gemma 2B distil Q4 LoRA / CalendarAgent Phi-3-mini Q4 sysprompt / Orchestrator Phi-3-mini Q4 sysprompt / Heavy fallback Llama-3-8B Q4 off-the-shelf / App-pred LSTM 2L 128h fp16 trained / Embeddings all-MiniLM-L6-v2 int8 off-the-shelf / Prosody Whisper-tiny encoder int8 encoder only. Footer 14 pt: Runtime: MediaPipe LLM Inference (Android), MLX (iOS dev), llama.cpp. Reference: Hugging Face model index, Replicate.

## PERSUASION JOB
Engineering credibility through named models, sizes, quantisations, and an Owned weights column for the Engineer judge.
