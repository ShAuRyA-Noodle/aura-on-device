# Aura — FinanceAgent Dataset

Indian-bank SMS bodies and Gmail receipt subjects for the on-device transaction parser.

## Files

- `finance_train_synthetic.jsonl` — 100 SMS rows (HDFC, SBI, ICICI, Axis) + 50 receipt subjects (Zomato, Swiggy, Blinkit, Amazon, IRCTC, Uber). **Provenance: synthetic.** License: CC0.
- `finance_train.jsonl` *(not committed)* — synthetic + self-collected with consent (team + opt-in friends, anonymised).
- `finance_eval.jsonl` *(not committed)* — held-out 10–20% split.

## Provenance

- **Synthetic:** authored by the Aura team. The SMS lines mirror the real-format strings sent by HDFC, SBI, ICICI, and Axis — last-4 digits, amounts, merchant tokens, timestamps — but contain **no real account numbers**. `account_last4` is a plausible 4-digit sample chosen from a fixed pool, never a real card. License: CC0.
- **Self-collected:** SMS dumps from team and opt-in friends, exported from their phones manually, with sender names and account hashes scrubbed. Stored only in `finance_train.jsonl` (not committed). Consent log lives in `aura/datasets/CONSENT.md`.
- **No public PII corpora.** We do not train on scraped SMS dumps.

## Schema

Each row is a single JSON object on its own line:

```json
{
  "input":  "Sent Rs.350.00 from A/c **1234 to ZOMATO via UPI on 07-MAY",
  "merchant": "Zomato",
  "amount": 350.0,
  "currency": "INR",
  "account_last4": "1234",
  "ts": "2026-05-07T20:42:00+05:30",
  "category": "food_delivery",
  "source": "sms|gmail",
  "bank":   "HDFC|SBI|ICICI|Axis|null",
  "provenance": "synthetic|self_collected"
}
```

## Categories (14 fixed)

`food_delivery`, `groceries`, `transport`, `fuel`, `entertainment`, `education`, `rent`, `utilities`, `shopping`, `health`, `transfer_in`, `transfer_out`, `subscriptions`, `other`.

## Indian merchants

Top-8 we ship with regex hot-paths: **Zomato, Swiggy, Blinkit, Amazon, IRCTC, Uber, Ola, BMTC**. Long-tail merchants fall back to the LoRA forward pass.

## Bank SMS coverage

12 most common Indian banks (per `technical_spec.md` §3.3): HDFC, ICICI, SBI, Axis, Kotak, IndusInd, BoB, PNB, Yes, IDFC, AU, RBL. The synthetic seed covers the four most active ones. Self-collected rows extend coverage in `finance_train.jsonl`.

## Versioning

Append-only. Eval splits use a stable hash of `(input + merchant + amount)`.
