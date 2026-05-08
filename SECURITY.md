# Security policy

Aura is an on-device, multi-agent empathetic intelligence layer. Because
it processes notification metadata, calendar events, UPI SMS (Android),
HealthKit / Health Connect data, and an encrypted memory graph on a
personal phone, we take responsible-disclosure reports seriously.

This document describes how to report a vulnerability, what we treat as
in-scope, and how we credit reporters.

---

## How to report

Email both founders. Please include the words `aura security` in the
subject line. The same address handles regular contact, so the words
help us route the report quickly.

- spunj_be23@thapar.edu
- sgupta9_be24@thapar.edu

For machine-readable details and PGP keys, see
[`.well-known/security.txt`](.well-known/security.txt).

We aim to acknowledge a report within 72 hours and to publish a fix
or written rationale within 90 days. Please allow that window before
disclosing publicly.

---

## In-scope

The threat model — [`docs/threat_model.md`](docs/threat_model.md) —
covers five named adversaries with STRIDE per surface. We are
particularly interested in reports that target:

- **Memory graph confidentiality.** Any path that extracts plaintext
  from the SQLCipher graph without triggering the audit log.
- **Audit log tampering.** Any path that mutates a node, an edge, or
  a Reasoning Trace without changing the daily Merkle root.
- **Panic-wipe bypass.** Any path that leaves recoverable plaintext on
  disk after the panic-wipe gesture has been triggered. Spec lives in
  [`docs/threat_model.md`](docs/threat_model.md) §6 and
  `technical_spec.md` §11.6.
- **OAuth refresh-token leakage** out of the app sandbox.
- **Reasoning Trace forgery.** Any path that emits a trace with a
  trigger or signal set the orchestrator never observed.
- **Cross-app egress.** Any path that causes Aura to make a network
  call outside the four documented endpoints.

---

## Out-of-scope

- Issues that require a rooted or jailbroken device.
- Issues that depend on physical access to an unlocked device.
- Issues that depend on the user installing a malicious profile.
- Brute-force attacks against rate-limited authentication endpoints.
- Reports against the HuggingFace Space `Caramel_Coin`. The Space runs
  synthetic data only; please mail HuggingFace for hosting issues.
- Reports against third-party services (Google OAuth, Apple
  HealthKit, Google Health Connect). Forward to the upstream vendor.

---

## Disclosure timeline

1. **T+0.** Reporter emails the founders.
2. **T+72h.** We acknowledge receipt and request reproduction details.
3. **T+30d.** We respond with a fix plan or a written rationale.
4. **T+90d.** Public disclosure, with credit unless the reporter has
   asked otherwise.

For severe issues affecting the panic-wipe or audit log, we will
ship out-of-band patches and notify pilot users directly before the
public disclosure window closes.

---

## Acknowledgments

Reporters who help us harden Aura are credited in this section after
the fix lands. Reporters may opt out of credit at any time.

(No reports yet.)

---

## Related documents

- [`docs/threat_model.md`](docs/threat_model.md) — STRIDE per surface,
  five named adversaries, panic-wipe spec.
- [`docs/privacy_promises.md`](docs/privacy_promises.md) — five
  plain-English privacy promises tested against the threat model.
- [`docs/decisions/ADR-0007-memory-encryption.md`](docs/decisions/ADR-0007-memory-encryption.md) —
  encryption-at-rest decision.
- [`.well-known/security.txt`](.well-known/security.txt) — RFC 9116
  contact metadata.
