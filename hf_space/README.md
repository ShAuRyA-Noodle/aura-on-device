---
title: Aura — On-device proactive assistant
emoji: 🌅
colorFrom: red
colorTo: gray
sdk: gradio
sdk_version: 4.44.0
app_file: app.py
python_version: "3.11"
pinned: false
license: mit
short_description: Aura interactive demo - 6 tabs, real agent stack.
---

# Aura — public interactive Space

A live, interactive demo of Aura's on-device agent stack (Comms, Calendar,
Finance, Wellness) wired through the same orchestrator + Reasoning Trace
emitter that ships in the mobile build. The Space accepts your own pasted
inputs (SMS, chat, calendar events, sliders) and renders the real agent
output plus the full glass-box trace.

> **Demo runs on synthetic + your-pasted data. Nothing is logged.**
> Production runs on-device. The classifier and embedder fall back to the
> deterministic regex / hash-bucket path on this CPU-only Space.

## Tabs

1. **Morning Brief Builder** — HRV slider, sleep hours, three calendar events, five notifications. Real Calendar Agent conflict-detect + Comms Agent triage + Wellness load-score, ranked by the Policy decider. Reasoning Trace JSON rendered live.
2. **Quiet Group Chat** — paste up to 200 messages (one per line). The CommsAgent surfaces the top 3 actionable, mutes the rest, and reports the Silence Budget tokens spent. "Load 137-msg DBMS scenario" pre-loads the locked example.
3. **Spend Mirror** — paste 1-30 lines of Indian bank SMS. Six "Load example" buttons for HDFC / SBI / ICICI / Axis / Kotak / PNB. Output: parsed table (merchant, amount, currency, timestamp, category, anomaly_flag), projected end-of-month spend, suggested substitution.
4. **Load Score Live** — five sliders (HRV, typing entropy, app-switch rate, sleep debt, notification dismiss rate). Real Load Score (0-100) computed by the trained XGBoost regressor when present, else the linear fallback. Driver decomposition bars + intervention recommendation.
5. **Memory Graph Explorer** — add nodes via the form, search vector + keyword, download the full JSON export, view today's Merkle root.
6. **Reasoning Trace Library** — three pre-recorded glass-box trace replays (Monday Brief, Stress Spike, Calm Evening). Click a card to open the full Reasoning Trace JSON.

## What this is NOT

This is a CPU-only public showcase. The real Aura product is on-device. The
production stack runs Gemma 2B + Phi-3-mini via MLX (iOS) or MediaPipe LLM
Inference (Android) — none of that runs here. This Space exposes the same
orchestrator, schemas, and reasoning-trace contract; the classifier/embedder
are swapped for the deterministic lightweight path.

## Run locally

```bash
cd aura/hf_space
pip install -r requirements.txt
python app.py
# -> http://localhost:7860
```

## Visual language

Locked palette per `deck/deck_spec.md §0`:

| Token       | Hex      |
|-------------|----------|
| Parchment   | #FAF8F5  |
| Ink         | #0E0E0E  |
| Accent      | #FF5B2E  |

Typography: Fraunces (display) + Inter Tight (UI), via Google Fonts. The
Reasoning Trace JSON renders with the locked keys (`chosen`, `rationale`,
`confirm_required`) highlighted in the accent colour.

## File map

```
hf_space/
├─ app.py                    # Gradio Blocks — 6 tabs, hero, footer
├─ style.css                 # Locked palette, typography, components
├─ requirements.txt          # gradio, pydantic, jsonschema (CPU only)
├─ README.md                 # this file
├─ static/                   # hero image + memory_export download target
├─ agents/{comms,calendar,finance,wellness,core}/
├─ memory/                   # MemoryGraph + audit chain
└─ orchestrator/             # graph + policy + trace + replays/output/
```

## Privacy invariants enforced by code

- `CommsAgent` never persists message bodies — only `(sender_hash, intent, urgency)`.
- `FinanceAgent.persist()` returns only `(merchant_hash, amount, currency, account_last4, ts, category)`.
- `MemoryGraph.export_json()` lets the user dump and walk away — fully portable.
- The audit log's hash chain is tamper-evident; daily Merkle roots make retroactive edits detectable.
