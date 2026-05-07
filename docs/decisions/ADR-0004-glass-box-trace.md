# ADR-0004 — Glass-Box Reasoning Trace: Schema, Storage, UI Rule

## Status

Accepted (2026-05-07). Source: `plan.md` §9.3, §13; `technical_spec.md` §4.6, §5.

## Context

Aura's third product principle is *glass-box always* (`plan.md` §4.4). Every autonomous or semi-autonomous action emits a structured trace the user can inspect, edit, or reject. The Reasoning Trace is the trust-multiplier wedge versus Gemini, Apple Intelligence, Bixby, Pixel Assistant, Rabbit, Humane, and ChatGPT (`plan.md` §9.3). It is also the front-and-centre visual on slide 4 of the deck and a recurring beat in the demo script.

Constraints:

- Schema must be machine-validatable to prevent drift across agent emitters.
- Schema must support both rule-resolved (template rationale) and LLM-generated rationales without leaking which path produced the text into the user-visible string.
- Storage must allow fast purge by user request and tamper-evident audit of reads and writes.
- The UI must render the trace in five sections in a fixed order so users build muscle memory.
- Sensitive fields must be redacted on export and in the audit log preview without losing the trace's utility.

## Decision

The Reasoning Trace is a JSON object conforming to schema `trace.v1.json` (`technical_spec.md` §4.6). Required fields: `trace_id`, `ts`, `trigger`, `signals`, `candidates`, `chosen`, `rationale`, `confirm_required`, `outcome`. Optional but recommended: `rationale_source ∈ {"template", "llm"}`, `redactions[]`.

`trace_id` matches the regex `^tr_[a-z0-9]{12}$`. `rationale` is at most 500 characters. `outcome` is one of `pending | confirmed | dismissed | timed_out | executed_auto | failed`.

**Storage.** Traces are written to a dedicated `traces` table (`technical_spec.md` §6.2):

```sql
CREATE TABLE traces (
  trace_id TEXT PRIMARY KEY,
  ts INTEGER NOT NULL,
  payload_json TEXT NOT NULL,
  outcome TEXT NOT NULL
);
```

The table sits inside the SQLCipher-encrypted memory graph. Every read and write of `traces` produces an `audit_log` row with hash-chained `hash_chain`. Daily Merkle roots over the previous day's audit rows are computed at 00:05 local and surfaced in Settings.

**Retention.** Default 30 days. User-overridable per type to 7 / 30 / 90 / 365 / never-purge. Aggregated daily counters `(date, action_kind, count, accept_rate, dismiss_rate)` are retained 365 days even after individual traces purge.

**UI rule.** The Reasoning Trace renders as a drawer attached to the originating action card, not as a separate tab. Tapping any action card opens the drawer. The drawer renders five sections in this fixed order:

1. **Why now** — `trigger.source` + `trigger.value`, one line.
2. **What I saw** — `signals[]` as a three-column key/value/range table.
3. **What I considered** — `candidates[]` ranked highest first, score breakdown collapsible.
4. **What I chose and why** — `chosen` + `rationale`.
5. **What you can do** — Confirm / Dismiss / Edit / Tell-me-when-not-to.

Watch glance shows only `chosen` plus a three-word rationale. The full trace is available on the phone via tap-and-hold. The Edit affordance writes a `user_correction` row that will retrain the relevant agent's LoRA on the next training cycle (Phase 2 onwards).

**Redaction.** Sensitive fields (`signals[].channel`, `signals[].location`, `signals[].rmssd_ms`, `candidates[].args.text`, anything matching `phone:E.164`) are redacted on export per the redaction profile (`technical_spec.md` §5.4). The `redactions[]` list names the redacted fields without reproducing values.

**Schema validation.** Every emitted trace passes `jsonschema` validation against `trace.v1.json` before persistence. Validation failure causes the trace to be written to a quarantine path `errors/quarantine_traces.jsonl` and a telemetry event raised; the original action proceeds because the user has already confirmed it, but a follow-up bug is filed.

## Consequences

Positive:

- A schema-validated trace is the only artefact the system commits to producing on every decision; this gives QA, the deck, and the demo a single object to point at.
- The five-section UI rule lets users build muscle memory; tapping any card surfaces the same shape every time.
- Redaction profiles let users share traces with a friend or clinician without exposing channel names or message bodies.
- Daily Merkle roots create a tamper-evidence story for the audit log without burdening every read.

Negative / costs:

- Five sections on every drawer is a lot of vertical real estate on a phone. Mitigated by collapsing the score breakdown by default.
- Schema validation on every trace adds ~5 ms per decision; acceptable.
- Storing rationale strings makes traces searchable, which means an adversary with a decrypted DB has more context. Acceptable because the DB is encrypted at rest and a Merkle root provides tamper-evidence.

## Alternatives

- **Free-form prose trace, no schema.** Rejected: drift across agents, no machine validation, no programmatic redaction.
- **Trace as a separate tab, not a drawer.** Rejected: action and trace must be co-located to make the wedge visible at point-of-decision.
- **No retention; traces vanish after one tap.** Rejected: long-term aggregation supports the satisfaction KPI without storing individual traces beyond 30 days.
- **Cloud-mirrored trace store.** Rejected by ADR-0005 (no cloud egress).

End of ADR-0004.
