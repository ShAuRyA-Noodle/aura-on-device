# Aura — Privacy Promises

Five plain-English promises. Each is tested against the threat model in `threat_model.md` and tied to specific architecture commitments.

---

## Promise 1 — Your data lives on your device.

What this means: Aura processes notification metadata, Gmail metadata, calendar events, SMS (Android only), HRV, sleep, and typing-entropy signals on the phone. The encrypted memory graph stays on your device. Inference (LLM rationale, embeddings, classifiers) runs on the device. We do not operate a backend; there is no `api.aura.ai`.

What this does *not* mean: we cannot prevent Gmail or Calendar from being read on a different device under the same Google account. That is account security, not Aura's security.

Tested against:

- Adversary C in `threat_model.md` (OS account compromise): a stolen Google account does not exfiltrate Aura's local memory; the graph stays on the device under SQLCipher (ADR-0007).
- Adversary D (lost device): file protection plus encryption-at-rest holds when the device is locked.

Architecture commitment: ADR-0005 (on-device only).

---

## Promise 2 — Nothing leaves the device unless you press export.

What this means: Aura performs no background sync of personal data. The only network calls Aura makes are OAuth token exchange, model weight download on first install, and Distance Matrix queries when computing a Leave-By Alert. The memory graph export to JSON is share-sheet driven; you pick the destination.

What this does *not* mean: Gmail's normal cloud-side state is unaffected — your messages still live on Google's servers. Aura does not change that; it just doesn't add another egress path.

Tested against:

- Adversary B (malicious notification listener): proactive notifications use minimal text; the actual content is rendered inside the app behind biometric if enabled.
- Threat model §2.5 (memory graph export paths): export is share-sheet only, profiles `share-with-friend` and `share-with-clinician` redact channel names, locations, balances, and HRV before the user shares.

Architecture commitment: ADR-0005 (on-device only); `technical_spec.md` §6.9 (export format).

---

## Promise 3 — Every action shows its work, and you can erase the work.

What this means: every autonomous or semi-autonomous Aura action emits a Reasoning Trace — the trigger, the signals it saw, the candidates it considered, the one it chose, the rationale, and the outcome. You can open the trace from any action card. You can delete a trace, a node, a time-range, or the entire graph in one tap. Daily Merkle roots in Settings let you verify the audit log has not been retroactively edited.

What this does *not* mean: the rationale string is short (≤500 characters) and may not capture every nuance the underlying model considered. We disclose this — `rationale_source ∈ {"template", "llm"}` is on every trace.

Tested against:

- Threat model §2.1 (tampering): tamper-evidence via daily Merkle root.
- Threat model §2.5 (memory graph): one-tap delete-by-time-range.

Architecture commitment: ADR-0004 (glass-box trace); `technical_spec.md` §5 (trace schema), §6.8 (Merkle root), §6.10 (delete-by-time-range).

---

## Promise 4 — Aura speaks at most three times a day, and you can take that to zero.

What this means: a named state variable, the **Silence Budget**, caps proactive non-safety surfaces at 3 per local day. Each surface decrements the budget by one token. Tapping "Useful" on a card refunds one token, capped at the daily ceiling. The budget is visible in Settings as three small dots. The default is configurable from 1 to 5.

Safety-class Wellness actions (mute, breathe, nap) do not consume tokens — those reduce attention rather than spend it.

What this does *not* mean: the third proactive surface still arrives unless you ratchet the ceiling down. Aura is silent by *design*, but the design is to earn three calls a day, not to be mute.

Tested against:

- Cognitive-overload framing of `plan.md` §1.1 and §3.1.
- The plan's anti-goal of optimising for engagement (`plan.md` §4.5).

Architecture commitment: ADR-0003 (Silence Budget as named state variable).

---

## Promise 5 — Five rapid taps wipe everything, including from us.

What this means: the panic-wipe gesture (5 rapid presses of the side / power button within 3 seconds, or hold-and-shake configurable) destroys the SQLCipher key, revokes OAuth refresh tokens, deletes the app sandbox files, and relaunches Aura into fresh-install state. There is a 3-second hold-cancel window to protect against accidental wipes. Nothing is logged about the wipe — that absence is a feature.

What this does *not* mean: it does not wipe what's already on Google's servers, what's already shared on a previous export, or what an attacker has already photographed off your screen.

Tested against:

- Adversary E (parental coercion / forced unlock): panic-wipe is the durable answer.
- Adversary D (lost device): a user can wipe before handing the device over for repair or sale.

Architecture commitment: `technical_spec.md` §11.6 (panic-wipe gesture); ADR-0007 (key destruction implies plaintext is unrecoverable).

---

## What we explicitly do not promise

- We do not promise unbreakable privacy. The OS itself is the floor; if iOS or Android is compromised at the kernel level, Aura's encryption is one more file the OS protects under its sandbox, no more, no less.
- We do not promise that a sufficiently determined coercer cannot extract every secret from the user. Stealth mode and panic-wipe help; they are not magic.
- We do not promise zero false positives in the orchestrator's decisions. Every action is reversible; the Reasoning Trace lets you see why, and the "Edit" affordance lets you correct.
- We do not promise no notifications. We promise at most three proactive non-safety surfaces a day under default settings.

---

End of `privacy_promises.md`.
