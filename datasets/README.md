# Aura — Datasets

```
datasets/
  comms/
    README.md
    comms_train_synthetic.jsonl    (200 rows, CC0)
    comms_train.jsonl              (synthetic + self-collected; not committed)
    comms_eval.jsonl               (held-out 10-20%; not committed)
  finance/
    README.md
    finance_train_synthetic.jsonl  (150 rows: 100 SMS + 50 receipts, CC0)
    finance_train.jsonl            (synthetic + self-collected; not committed)
    finance_eval.jsonl             (held-out 10-20%; not committed)
  orchestrator/                    (Phase 2 contingent — replay traces)
  lsapp/                           (LSApp arxiv 1911.04026 next-app LSTM data)
  pilot/                           (30-user pilot telemetry, Phase 2)
```

## Provenance posture

Three layers, in this order of preference:

1. **Synthetic, CC0.** Authored by the team. Indian college / hostel context. No PII. Released alongside the repo.
2. **Self-collected with explicit consent.** Team members + opt-in friends. PII scrubbed before merge. Consent log lives in `aura/datasets/CONSENT.md` (Phase 2). Never committed in raw form.
3. **Public open datasets.** LSApp (arxiv 1911.04026), Tsinghua App Usage Trace, Melbourne Context Query Logs, Android Usage Patterns, KV Cache Workloads. Loaded at training time, not vendored.

We do not scrape WhatsApp / Insta / SMS dumps. Every row in `comms_train.jsonl` and `finance_train.jsonl` traces back to either the synthetic CC0 seed or a consented self-collected source.

## Splits

80 / 10 / 10 train / val / test, hashed by a stable key per dataset. See each subfolder README for the exact key.

## Format

JSONL — one JSON object per line, UTF-8, no trailing newlines. The agent training scripts (`models/lora/train_*.py`) and the eval harnesses (`models/eval/eval_*.py`) both consume the same JSONL.

## License

- Synthetic seed JSONLs in this repo: **CC0** (per individual subfolder README).
- Self-collected JSONLs: not redistributed; remain on the team's machine and the on-device model artefact only.
- Public datasets: cited under their original licenses, never re-uploaded.
