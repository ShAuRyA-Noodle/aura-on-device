# ADR-0005 — On-Device Only: No Cloud Egress

## Status

Accepted (2026-05-07). Source: `plan.md` §4.5, §20.3; `technical_spec.md` §1, §11.4.

## Context

Aura processes notification metadata, calendar events, Gmail receipts, SMS (on Android), HRV, sleep, and typing-entropy signals. Every byte of this is sensitive in the Indian context the product targets: UPI SMS leaks bank balance, WhatsApp metadata leaks group membership, HRV leaks emotional state. The privacy wedge in `plan.md` §9.5 promises a user-owned exportable memory graph with audit log; that promise is incompatible with background cloud sync of personal data.

Constraints:

- The architecture must support the trust narrative on slide 9 (`plan.md` §20.3): "the user owns their data, can see and erase it, and that no byte leaves the device without an explicit user-initiated action."
- The threat model (`threat_model.md`) names Apple ID / Google account compromise as a real adversary; Aura cannot create a new attack surface in our backend.
- Budget is ₹2,000 (`plan.md` §26). Running a backend has ongoing cost that the team will not pay.
- Latency budget for the stress-driven mute reference flow is 3000 ms (`technical_spec.md` §2). Round-trip to a cloud LLM exceeds that on Indian mobile data on a typical day.

## Decision

Aura performs **all hot-path inference, decision, storage, and audit on the device**. No personal data, no signal, no embedding, no trace is sent to any network endpoint operated by the team or by a third party for routine operation.

Specifically:

- LLM inference (Phi-3-mini, Gemma 2B, Llama-3-8B fallback) runs locally via MLX (iOS dev), llama.cpp (cross-platform), and MediaPipe LLM Inference (Android).
- Embeddings (all-MiniLM-L6-v2) run locally via ONNX Runtime Mobile.
- Memory graph storage is on-device SQLCipher (ADR-0007).
- Reasoning Traces are local-only.
- The audit log is local-only.

**Permitted network egress.**

1. OAuth flows (Gmail, Google Calendar). Tokens scoped to `gmail.metadata`, `gmail.readonly`, `calendar.readonly`, `calendar.events`. Refresh tokens stored in Keychain / EncryptedSharedPreferences. Aura never requests `gmail.modify` or `gmail.send`; drafts open in the user's mail app.
2. Google Distance Matrix for travel-time estimation, only when the user's calendar contains an event whose `Leave-By Alert` is being computed. Falls back to a local heuristic if quota is exhausted or the network is unavailable.
3. Public model weight downloads on first install (Phi-3-mini, Gemma 2B Q4 GGUF, MiniLM embeddings). One-time fetch, content-addressed.
4. **User-initiated export only.** Memory graph export to JSON via the Settings → Export action. The share sheet is invoked; the user picks the destination. No background sync, no auto-upload.
5. **User-initiated cloud heavy task.** Optional, opt-in per task, with a one-screen consent and a per-task scope. Off by default.

Aura ships **no backend operated by the team**. There is no `api.aura.ai`, no analytics endpoint, no crash reporter that captures user data. Crash reporting, if added in Phase 2, will be self-hosted and scrub all personal fields at source.

## Consequences

Positive:

- The trust narrative is defensible on stage and in the threat model.
- A compromised Google account does not leak Aura's local memory; tokens are device-bound and refresh tokens are encrypted per device.
- No backend means no operational cost, fitting the ₹2,000 budget.
- Latency budgets are achievable; LLM token generation is the only stage above 1500 ms (`technical_spec.md` §2).

Negative / costs:

- LoRA training has to happen offline on local hardware (RTX 4080); shipping new fine-tunes requires an app update, not a server deploy. Acceptable for the EnnovateX timeline.
- Heavy fine-tuning per user is impossible. Mitigated by the cold-start strategy and personal baseline EMA (`technical_spec.md` §7.5).
- Crash analytics are limited; we lose visibility into production issues. Mitigated by extensive on-device telemetry written to the audit log and surfaced to the user in Settings.
- Cross-device sync (phone ↔ tablet) cannot use a cloud relay; we use Multipeer Connectivity (iOS) and Nearby Connections (Android) with local pairing.

## Alternatives

- **Cloud-hosted heavy LLM by default.** Rejected: violates the privacy wedge, raises round-trip latency, creates an operational cost the team cannot meet.
- **Encrypted cloud sync with E2E keys.** Rejected: increases attack surface (server, transport, key management) for no architecture-level benefit; export-on-tap covers the user need.
- **Federated learning across users.** Rejected for Phase 1 and 2: feasibility is real but requires telemetry plumbing the team will not build at submission.
- **Hybrid: cloud for "novel" rationales, local for hot path.** Rejected: complicates the privacy promise on slide 9 and forces the user to reason about which prompt goes where.

End of ADR-0005.
