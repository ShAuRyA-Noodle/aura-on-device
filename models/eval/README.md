# Aura — Eval Harness

Three independent harnesses, one per fine-tuned surface:

| File | Targets | KPIs |
|---|---|---|
| `eval_comms.py` | CommsAgent intent classifier + draft writer | macro-F1 ≥ 0.78, Cohen's kappa ≥ 0.65, draft pairwise win-rate ≥ 60% |
| `eval_finance.py` | FinanceAgent SMS + receipt parser, 14-cat classifier | parse F1 ≥ 0.95, categorisation accuracy ≥ 0.90, per-merchant P/R for top 8 Indian merchants |
| `eval_orchestrator.py` | Phi-3-mini orchestrator on replay fixture | tool-call hallucination ≤ 5%, schema validation ≥ 95%, end-to-end trace correctness ≥ 90% |

All three are pure-Python by default; the heavy `torch` / `peft` imports only fire when you supply a real predictor.

---

## Quick start

```bash
# From project root.
python -m models.eval.eval_comms          --eval datasets/comms/comms_eval.jsonl
python -m models.eval.eval_finance        --eval datasets/finance/finance_eval.jsonl
python -m models.eval.eval_orchestrator   --fixture orchestrator/replays/replay_fixture.jsonl
```

If the canonical eval JSONL is missing, each harness falls back to the synthetic seed (`*_train_synthetic.jsonl`) or an in-memory fallback fixture so the pipeline runs end-to-end on a fresh clone.

---

## Wiring a real predictor

Each harness exposes a top-level evaluate function that accepts a `predictor` callable:

```python
from models.eval.eval_comms import evaluate_classification, load_jsonl

def predict(text: str) -> dict:
    # Your trained Gemma 2B + LoRA goes here.
    return {"intent": "ACTIONABLE", "urgency": 0.8, "self_relevance": 0.9, "draft": "..."}

records = load_jsonl(Path("datasets/comms/comms_eval.jsonl"))
result = evaluate_classification(records, predict)
```

The CLI binds a stub identity-predictor so harnesses can be smoke-tested without a trained adapter.

---

## Phase 2 trigger logic

`eval_orchestrator.py` reports `phase2_lora_trigger=True` when tool-call hallucination on the replay fixture exceeds 5% (the threshold from `models/lora/configs/orchestrator_lora.yaml`). Until that flag flips, **we ship Phi-3-mini off-the-shelf** with a deterministic system prompt and JSON-schema-validated tool calls. Train the orchestrator LoRA only after the trigger fires.

---

## Output

Each CLI prints a Markdown report to stdout and optionally dumps the structured dict to `--out-json`. The CI gate reads the JSON. Suggested locations:

```
models/exports/eval_reports/comms_v1.json
models/exports/eval_reports/finance_v1.json
models/exports/eval_reports/orchestrator_v1.json
```

These paths are git-ignored alongside the merged adapters.
