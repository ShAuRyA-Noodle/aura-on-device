# ADR-0003 — Silence Budget as Named State Variable (CRITICAL)

## Status

Accepted (2026-05-07). Source: `plan.md` §1.2, §4.4, §22; `technical_spec.md` §4.3.

This ADR is critical: the Silence Budget is the named state variable that distinguishes Aura from every reactive assistant on the comparison row of `plan.md` §8.

## Context

Aura's third design principle is *Silent by design* (`plan.md` §4.4): every notification is a tax, and the system caps proactive surfaces. The KPI report explicitly tracks attention-cost reduction as a Phase 2 metric. Without a named, persisted state variable, "silence" becomes a vague aspiration that any developer can quietly relax under feature pressure.

The orchestrator already enforces three hard caps (`technical_spec.md` §4.3): daily ≤3 surfaces, window ≤1 per 30 min, zero in `RECOVERING` state. These caps are imperative checks at decision time. They do not surface to the user, are not refundable, and are not visible to QA.

Constraints:

- The variable must be visible in the UI; users must be able to see how many surfaces remain today.
- The variable must be reportable as a Phase 2 KPI alongside effort reduction and satisfaction.
- The variable must respect that *some* surfaces (Wellness safety class) reduce attention rather than spend it.
- The variable must reward user-confirmed usefulness — the assistant should be able to earn back trust by being useful.
- The variable must be persisted so that a midnight reset is the only zeroing event, not an app relaunch.

## Decision

Aura defines a state variable named `silence_budget` with the following exact semantics.

**Default value.** The user starts each local day with **3 tokens**. The default is configurable in Settings between 1 and 5 tokens; the recommended setting for a learnable user is 3.

**Decrement rule.** Each non-safety proactive surface consumes one token. A "surface" is any orchestrator output where `expected_surface ∈ {WATCH, PHONE_CARD, EARBUD_TTS}`. A combined card that bundles two candidate actions into one user-facing card consumes one token total.

**Refund rule.** When the user taps the "Useful" affordance on a surfaced card, one token is refunded. Refunds are capped at the daily ceiling — `silence_budget` cannot exceed the configured default (3 by default). The "Useful" affordance is a small chip on the right of every action card.

**Exemption.** Safety-class Wellness actions (`MUTE_GROUP_30`, `MUTE_GROUP_15`, `BREATHE_478`, any other action where `agent==wellness && kind.startswith("MUTE_")||kind.startswith("BREATHE_")||kind.startswith("NAP_")`) do **not** consume from the budget and are not subject to the daily cap. Rationale: these actions reduce attention rather than spend it.

**Reset.** The budget resets to the default at 00:00 local time. Reset is a memory-graph audit event with `op=silence_budget_reset`.

**Persistence.** Stored in the `settings` table under the key `silence_budget_today` as a JSON object `{"tokens": int, "ceiling": int, "as_of": iso_date}`.

**UI rule.** The Settings home shows three small dots (filled = available, empty = spent) next to the label "Today". The dot row is also accessible from a long-press on any action card. When the budget reaches zero, the orchestrator emits no further non-safety surfaces and writes traces with `chosen=do_nothing, reason_code=silence_budget_exhausted`.

**Phase 2 KPI.** The mean `silence_budget_end_of_day` across the 30-user pilot is reported alongside the existing five KPIs as the sixth metric. Target: `mean_eod_budget >= 1.0` indicating users finish the day with at least one token unspent.

## Consequences

Positive:

- A named, persisted, refundable variable is observable in QA, in the deck, and in the UI. It cannot be quietly relaxed.
- The "Useful" tap creates a user-feedback loop on the orchestrator's ranking weights independent of any A/B framework.
- The Phase 2 KPI gives Samsung judges a number to point at on the slide 9 evidence panel.
- The exemption keeps safety-class Wellness interventions from being throttled at the wrong moment.

Negative / costs:

- The exemption list is itself a maintenance surface. Adding a new action kind requires a deliberate decision about whether it is safety class.
- Users on Tier C devices with reduced agent quality may exhaust the budget faster on bad-suggestion days, training the orchestrator down. Mitigated by the cold-start confidence cap (`technical_spec.md` §7.5).
- The "Useful" affordance increases the ink on every action card by one chip. Acceptable trade-off given that the chip is the wedge.

## Alternatives

- **Imperative caps only, no named variable.** Rejected: not visible to user or QA, no Phase 2 KPI surface, no refund mechanism.
- **Soft-decay budget that recovers continuously.** Rejected: harder to communicate ("you have 2.4 tokens") and creates a perverse incentive to surface frequently.
- **No daily ceiling on refund.** Rejected: a useful-tap economy without a ceiling could be gamed by users tapping "Useful" reflexively, defeating the silence wedge.
- **Per-agent budgets (one for Comms, one for Finance, etc.).** Rejected: explosion in mental complexity for the user with no improvement in calibration.

End of ADR-0003.
