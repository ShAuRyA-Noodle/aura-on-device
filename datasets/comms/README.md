# Aura — CommsAgent Dataset

Triage labels and reply drafts for an on-device notification triage model.

## Files

- `comms_train_synthetic.jsonl` — 200 hand-crafted rows. Cross-product of surface (WhatsApp / Insta / Slack / Gmail), urgency, and intent. Indian college / hostel context throughout. **Provenance: synthetic.** License: CC0.
- `comms_train.jsonl` *(not committed)* — synthetic + self-collected with consent. Mixed in by the team during Week 5–6.
- `comms_eval.jsonl` *(not committed)* — held-out 10–20% from the merged set.

## Provenance

- **Synthetic:** authored by the Aura team using realistic Indian Gen Z scenarios. No real user data, no scraping. Released CC0 inside this repo.
- **Self-collected:** WhatsApp / Gmail snippets contributed by team members and opt-in friends after explicit consent. PII is scrubbed by `scripts/anonymise.py` (sender names → `<sender_n>`, phone numbers / emails removed) before any row enters `comms_train.jsonl`.
- **No public PII corpora.** We do not train on Enron at this stage; if added later it will be the publicly-released classified subset (https://www.cs.cmu.edu/~enron/) and noted in the row's `provenance` field.

## Schema

Each row is a single JSON object on its own line:

```json
{
  "input":  "<surface> | <sender> | <preview>",
  "label":  "ACTIONABLE | SOCIAL | BROADCAST | SPAM",
  "urgency": 0.0..1.0,
  "self_relevance": 0.0..1.0,
  "draft":  "<= 2 sentence reply, casual tone, may be empty for non-actionable",
  "surface": "whatsapp|instagram|slack|gmail",
  "provenance": "synthetic|self_collected"
}
```

Field semantics match `agents/comms/contract` and `technical_spec.md` §3.1.

## Label key

| Label | Meaning |
|---|---|
| `ACTIONABLE` | The user has to do something within hours. Reply, click, RSVP, decide, leave-by, pay. |
| `SOCIAL` | Friend or peer chat. Worth surfacing only when nothing more important is in flight. |
| `BROADCAST` | One-to-many announcement, FYI, group ping, channel message not directed at the user. |
| `SPAM` | Promotional, scam, or spray-and-pray marketing. |

## Indian context anchors

Names: Anu, Manish, Riya, Kabir, Mira, Aanya, Rohan, Shaurya, Shorya, Karthik, Priya, Nikhil, Tanvi.
Places: Thapar, Christ University, Manipal, Bangalore, Bandra, Hostel-G, LT-3, BMTC stop.
Apps / brands: WhatsApp, Insta DM, Slack, Gmail, HDFC, SBI, ICICI, Axis, Zomato, Swiggy, Blinkit, Amazon, IRCTC, Uber, Ola, BMTC, Netflix, Hotstar.

## Generation rule

Every row goes through this checklist before commit:

1. Is the language casual Indian English / Hinglish-rendered-in-English?
2. Does the scenario resemble a real Thapar / Christ / Manipal hostel-week?
3. Does at least one row per file mention each of: UPI, IRCTC, Zomato, BMTC, hostel mess?
4. Is the urgency / self-relevance rating internally consistent with the label?
5. For ACTIONABLE rows, is the `draft` ≤ 2 sentences and tonally appropriate?

## Versioning

Append-only. Every row gets a stable hash of `(input + label)`; reorderings are forbidden so eval splits stay reproducible.
