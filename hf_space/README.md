---
title: Aura — On-device proactive assistant
emoji: 🌅
colorFrom: red
colorTo: gray
sdk: gradio
sdk_version: 4.44.0
app_file: app.py
pinned: false
license: mit
short_description: Synthetic showcase of Aura's four on-device agents.
---

# Aura — public showcase Space

A *synthetic-data* live demo of Aura's four on-device agents (Comms,
Calendar, Finance, Wellness) wired through the same orchestrator that ships
in the mobile build.

> **DEMO ON SYNTHETIC DATA — NO USER DATA EVER LEAVES YOUR DEVICE IN PRODUCTION.**

The agents themselves are unchanged from the on-device build. The only
difference is that this Space is fed example inputs the visitor types,
slides, or pastes — never personal logs.

## Tabs

1. **Morning Brief** — Health + Calendar + Comms inputs flow through the orchestrator. See the brief card and the full Reasoning Trace JSON.
2. **Quiet Group Chat** — paste any chat blob; CommsAgent triages to actionable + muted with a Reasoning Trace.
3. **Spend Mirror** — paste Indian UPI SMS; FinanceAgent regex pack parses, hashes the merchant, and categorises.
4. **Load Score** — slide HRV / typing-entropy / app-switch / sleep-debt; watch the regressor + intervention picker.
5. **Memory Graph** — interact with the on-device sqlite-vss memory: add nodes, search, export JSON, see audit log.

## Run locally

```bash
cd aura/hf_space
pip install -r requirements.txt
python app.py
# -> http://localhost:7860
```

## Deploy to a HuggingFace Space

```bash
huggingface-cli login
git clone https://huggingface.co/spaces/Shaurya-Noodle/Caramel_Coin
cd Caramel_Coin
cp -R ../aura/hf_space/* .
# Make sure the agent stack is on the Python path. Two options:
#   (a) git submodule add the aura/ repo as `aura/` and set PYTHONPATH in app.py
#   (b) copy the four agent dirs + memory/ + orchestrator/ alongside app.py
git add .
git commit -m "Initial Aura showcase Space"
git push
```

The Space builds on the free CPU tier — no GPU is required since every model
call in the showcase is the deterministic reference path (XGBoost / regex /
hash-bucket embedder). Production swaps these for Gemma 2B Q4 + DistilBERT +
all-MiniLM-L6-v2 at the on-device call sites.

## Privacy invariants enforced by code

- `CommsAgent` never persists message bodies. Only `(sender_hash, intent, urgency)`.
- `FinanceAgent.persist()` returns only `(merchant_hash, amount, currency, account_last4, ts, category)`.
- `MemoryGraph.export_json()` lets a user dump and walk away — fully portable.
- The audit log's hash chain is tamper-evident; daily Merkle roots make
  retroactive edits detectable.

## Visual language

Locked palette per `deck/deck_spec.md §0`:

| Token       | Hex      |
|-------------|----------|
| Parchment   | #FAF8F5  |
| Ink         | #0E0E0E  |
| Accent      | #FF5B2E  |

Typography: Fraunces (display) + Inter Tight (UI). Linear / Arc aesthetic.

## File map

```
hf_space/
├─ app.py            # Gradio Blocks — 5 tabs, hero, footer
├─ style.css         # Locked palette + Fraunces / Inter Tight
├─ requirements.txt  # gradio + pydantic + jsonschema (CPU only)
├─ Dockerfile        # Optional non-Gradio path for self-host
├─ .gitattributes    # HF Spaces LFS hints
└─ README.md         # this file (with the YAML metadata above)
```
