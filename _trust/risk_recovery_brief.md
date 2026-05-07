# Risk Recovery Brief — Stage Glance

Phone-screenshot ready. Top five risks from `plan.md` §27 with
locked mitigations. Read once before walking on stage. If a judge
opens any of these threads, the recovery line is committed.

---

## R1 — Apple-only device on a Samsung-judged stage

**Severity 5 · Likelihood 5.**

We own iPhones, Apple Watches, AirPods, a Mac, and one Alienware
RTX 4080. No Galaxy device. Total budget ₹2,000.

Recovery line, verbatim:
> Production target is the Galaxy ecosystem. iOS reference build
> proves cross-platform feasibility on the hardest privacy substrate
> first. The plausibility table on slide 4a maps every iOS API
> one-to-one to its Android counterpart. We never claim a kernel
> hook we don't have.

Then move to slide 4. Do not dwell.

---

## R8 — Hallucinated autonomous actions

**Severity 5 · Likelihood 3.**

Recovery line:
> Two locks. Confirm-required by default for every non-trivial
> action. Inter-agent communication is typed JSON validated against
> a schema; the LLM never produces free-form prose to talk to
> another agent. The state machine has a Cooldown state with a hard
> timeout.

Then point at slide 8a. The Reasoning Trace JSON is the artefact.

---

## R15 — Demo failure on stage

**Severity 5 · Likelihood 2.**

Mitigation: 90-second backup video pre-loaded on the laptop, cued
to the title card. Three full dry runs before finals.

Recovery action:
1. Fail forward. One sentence: "Backup video, ten seconds."
2. Tap the cued video. Stand still. Let it play.
3. Resume on the slide that follows the demo segment.

Do not apologise. Do not try to debug live.

---

## R6 — Notification spam from Aura itself

**Severity 4 · Likelihood 3.**

Recovery line:
> The Silence Budget is a first-class state variable. Hard cap at
> three proactive surfaces per day per user. The orchestrator's
> ranker treats notification cost as a learned per-user weight,
> updated on every dismissal. The cap is the floor on the cost
> function, not the function itself.

Reference slide 5 (the Silence Budget wedge) and slide 8a
(Confirm-required by default).

---

## R19 — Privacy backlash if a feature feels creepy

**Severity 4 · Likelihood 3.**

Recovery line:
> We do not promise unbreakable privacy. We promise the user owns
> their data, can see it, can erase it, and that no byte leaves the
> device without an explicit user-initiated action. One-tap export
> to JSON. Per-day Merkle root for the audit log. Panic-wipe gesture
> on five rapid power-button presses.

Reference slide 9 (privacy story) and `docs/threat_model.md`.

---

## Stage glance — single line per risk

R1  → "Production target Galaxy. iOS reference. API parity on slide 4a."
R8  → "Confirm-required by default. Typed JSON tool calls."
R15 → "Backup video, ten seconds." Then play it.
R6  → "Silence Budget is the floor on the cost function, not the function."
R19 → "User owns the data. Export, audit log, panic-wipe."

Read this list one minute before stage. Phone in pocket. Eyes up.
