# Aura — Threat Model

STRIDE per surface, with named adversaries and concrete mitigations. Cross-reference: `plan.md` §20; `technical_spec.md` §11.

Document version: 1.0
Last updated: 2026-05-07

---

## 1. Scope and assumptions

Aura runs on the user's personal device, reads system signals and OAuth-scoped cloud APIs, and stores a structured graph encrypted at rest. The trust narrative on slide 9 (`plan.md` §20.3) is the load-bearing claim: the user owns their data, can see and erase it, and no byte leaves the device without an explicit user-initiated action.

This threat model assumes:

- The OS itself is trusted at the kernel level. We do not defend against a kernel-level compromise of iOS or Android. If that posture holds, Aura's encrypted graph is one more file the OS protects under its sandbox.
- Third-party apps installed by the user are untrusted. They may attempt to read Aura's UI, intercept notifications, or escalate privilege.
- The user's Google account or Apple ID may be compromised. Aura is responsible for not amplifying that compromise.
- The device may be lost, stolen, or coerced from the user.
- The team operates no backend; there is no server-side surface to defend.

Out of scope: nation-state adversaries, physical hardware attacks (chip decap), supply-chain attacks against Google or Apple themselves, unfixed kernel zero-days.

---

## 2. Surfaces and STRIDE

### 2.1 Phone — `memory.sqlite` and the agent service

| Threat | STRIDE | Concrete | Mitigation |
|---|---|---|---|
| Spoofing | S | Malicious app issues a deep link `aura://confirm?id=...` to fake a confirm | Deep links are signed with an app-internal HMAC; Aura ignores unsigned links. Tap-to-confirm requires foreground presentation of the originating card. |
| Tampering | T | Malicious app or rooted attacker modifies `memory.sqlite` | DB encrypted with SQLCipher AES-256 (ADR-0007). Daily Merkle root in Settings lets the user detect retroactive edits. |
| Repudiation | R | User claims they did not authorise an action | Every action's trace records `outcome ∈ {confirmed, dismissed, timed_out, executed_auto, failed}` with `tap_lat_ms` and the originating `trigger.source`. |
| Information disclosure | I | A curious app reads memory contents | App sandbox; SQLCipher; `android:allowBackup="false"`; iOS `NSFileProtectionComplete` and `kCFURLIsExcludedFromBackupKey`. |
| DoS | D | Notification storm overflows queues | Bounded queues with drop-oldest semantics (`signal_q` 1024, `notif_q` 256, `usage_q` 256, `ime_q` 64). Backpressure metric written to telemetry. Orchestrator runs in a single foreground service with WorkManager / BGProcessingTask scheduling that survives transient pressure. |
| Elevation of privilege | E | Non-Aura code calls a privileged tool | Tool dispatcher checks the caller via `Binder.getCallingUid()` (Android) / XPC peer audit token (iOS). The tool catalogue (ADR-0009) is locked at compile time. |

### 2.2 Watch and earbuds

| Threat | Mitigation |
|---|---|
| Sniffing the WatchConnectivity / Wear OS Data Layer payload | Apple's link is encrypted and device-paired. Wear OS pairing is over the Companion Device Manager. We ship no Bluetooth fallback that bypasses pairing. |
| Earbud TTS overheard by a bystander | Hard cap of 1 TTS per active session. The user can disable the EARBUD surface entirely from Settings → Surfaces. TTS payload contains only the action kind, never raw signal values. |
| Watch glance text leaks group name | Glance shows only `chosen` and a three-word rationale; channel names are redacted before send. |

### 2.3 Cross-device (tablet / laptop pull-tab)

| Threat | Mitigation |
|---|---|
| Pairing with attacker's device | First pair displays a 6-digit code on both ends; user must match. State expires after 24 hours idle. |
| Replay of an old payload | Each payload is timestamped and a 60-second replay window is enforced; older payloads are discarded. |
| Bystander on the same Wi-Fi reads payloads | Multipeer (iOS) uses encrypted sessions by default (`MCEncryptionPreference.required`). Nearby Connections uses encrypted point-to-point strategy. |

### 2.4 Cloud OAuth (Gmail, Calendar, Distance Matrix)

| Threat | Mitigation |
|---|---|
| OAuth token theft from disk | Stored in Keychain / EncryptedSharedPreferences. Refresh tokens encrypted under the platform Keystore. |
| Scope creep | Tokens are scoped to `gmail.metadata`, `gmail.readonly`, `calendar.readonly`, `calendar.events`. Aura never requests `gmail.modify` or `gmail.send`. |
| User unaware of connected accounts | Settings → Connected Accounts lists every provider with the granted scopes and a one-tap revoke. Revocation calls `oauth2.googleapis.com/revoke?token=...` and clears the local copy. |

### 2.5 Memory graph (export and read paths)

| Threat | Mitigation |
|---|---|
| Auto-upload of the export to cloud | Export is share-sheet only; user picks the destination. No background sync. |
| Plaintext export shared with a hostile party | Export profiles `share-with-friend` and `share-with-clinician` redact channel names, locations, balances, and HRV per `technical_spec.md` §5.4. The `raw` profile is the default for self-export only and warns the user before sharing. |
| Adversarial reads tracked but not stopped | Audit log captures every `op=read` with target id and agent. Daily Merkle root lets a user prove (or detect) reads at end-of-day. |

---

## 3. Adversaries

The plan names five classes (`plan.md` §20.1). Each is treated below with concrete mitigations and known residual risk.

### 3.1 Adversary A — Malicious accessibility app

Profile: another app installed by the user with the AccessibilityService permission. Such an app can read on-screen text, simulate taps, and observe view hierarchy in real time. This is the strongest hostile-app posture on Android.

Threat: read the Reasoning Trace drawer in real time, harvest `signals[]` and `rationale`, simulate a "Confirm" tap on Aura cards.

Mitigations:

- Mark sensitive views with `FLAG_SECURE` (Android) / `screenCaptureProtected=true` on relevant views (iOS 17+) to prevent screenshots and screen recording.
- Detect enabled accessibility services with `getEnabledAccessibilityServiceList()`; if a non-system service is enabled, show a one-time warning: "Aura works best with no third-party accessibility services."
- Decrypted memory rendered in UI is already redacted at ingest — there is no raw message body to read off the screen.
- Tap-to-confirm requires that the originating card was rendered by Aura's own process; a synthesised tap from a11y on a card that was never displayed does not match a pending `AwaitingConfirm` state.

Residual risk: an a11y app can harvest summarised content if rendered. The user's own decision to keep an a11y service running is in scope; we surface the risk and let the user decide.

### 3.2 Adversary B — Malicious notification listener

Profile: another app with `BIND_NOTIFICATION_LISTENER_SERVICE` permission.

Threat: read Aura's outbound proactive notifications and infer state.

Mitigations:

- Aura proactive notifications use minimal text ("New from Aura"). The actual content is rendered inside the app, behind biometric if enabled.
- Channel names in payloads are pre-hashed.
- A user-set DND window suppresses surfaces via PHONE_CARD entirely; only WATCH-class haptics remain for safety actions.

Residual risk: the *fact* that Aura emitted a notification is observable. Volume of notifications is observable. We accept this — the goal is silence, not steganography.

### 3.3 Adversary C — OS account compromise (Apple ID, Google account)

Profile: an attacker has obtained the user's Apple ID or Google credentials.

Threat: log into Gmail / Calendar from another device, read messages and calendar.

Mitigations:

- Out of scope for Aura's local hardening. We document this in onboarding.
- Aura's OAuth tokens are device-bound: refresh tokens are encrypted under the platform Keystore and tied to the originating device install. A stolen account does not yield the local memory graph.
- The graph itself stays on the user's device. A compromised Google account does not exfiltrate it.

Residual risk: Gmail and Calendar themselves are exposed. The user's defence is account-level (2FA, passkeys, recovery flows) and not Aura's.

### 3.4 Adversary D — Lost device

Profile: the device is stolen or misplaced. Attacker has physical possession.

Threat: extract `memory.sqlite`, read the graph, observe the audit log.

Mitigations:

- All data at rest encrypted (ADR-0007). SQLCipher key tied to Keystore / Secure Enclave; requires unlock.
- iOS file protection set to `NSFileProtectionComplete`: file is unreadable when device is locked.
- Optional Aura passcode required on cold launch (Settings → Privacy → Aura Passcode), in addition to OS unlock.
- Remote wipe inherits from MDM / Find My; we ship no proprietary remote wipe. The locked-device posture is sufficient for the plan's threat profile.

Residual risk: an attacker with the unlock PIN or biometric (forced unlock) reads the graph. Mitigated for that case by adversary E mitigations below.

### 3.5 Adversary E — Parental coercion / forced unlock

Profile: a parent, partner, or peer forces the user to unlock the device and reveal "what Aura knows".

Threat: scroll the Memory tab; read traces; infer relationships, spending, stress.

Mitigations:

- **Stealth mode** (Phase 2, ADR-0010 timeline). Settings → Privacy → Stealth: the Memory tab is replaced with a placeholder "Memory cleared" view. The real memory graph remains, encrypted; only the UI surface is hidden. Toggling out requires the Aura passcode (a separate secret from the OS unlock).
- **Panic-wipe gesture** (`technical_spec.md` §11.6). 5 rapid presses of the side / power button within 3 seconds, or a hold-and-shake gesture (configurable), triggers:
  1. SQLCipher key wiped from Keystore (immediate, irreversible).
  2. OAuth refresh tokens revoked via `https://oauth2.googleapis.com/revoke?token=...`.
  3. App sandbox files deleted; free-space overwrite optional.
  4. App relaunched into a fresh-install state.
  A 3-second hold-cancel window protects against accidental wipe ("panic-of-panic"). A single low-amplitude confirmation sound plays even on a muted device. Nothing is logged about the wipe — that is itself a feature.

Residual risk: a coercer who knows about Stealth and demands its toggle gets the full memory if the user discloses the Aura passcode. The product can't defend against revealing every secret to a sufficiently determined coercer; the panic-wipe gesture remains the durable answer.

---

## 4. Privacy invariants — enforced

The threat model is consistent with the privacy invariants stated in `plan.md` §10.1, §14, and §20.3:

- No raw message body persisted after agent processing.
- No audio persisted as audio.
- Location bucketed to 200 m grid, with raw coordinates aged out within an hour.
- Memory graph encrypted at rest under platform Keystore / Secure Enclave keys.
- Audit log is append-only and hash-chained, with daily Merkle roots in Settings.
- Export is share-sheet only and user-initiated.
- Panic-wipe is irreversible by design.

---

## 5. Open threats and `[TEAM TO VERIFY]` items

- **iOS DeviceActivity API limits.** [TEAM TO VERIFY against Apple's docs how much app-launch-sequence data is exposed and whether DeviceActivity events are visible to other apps.]
- **sqlite-vss + SQLCipher coexistence on Android.** [TEAM TO VERIFY in Week 4 against asg017/sqlite-vss issue tracker.]
- **OAuth revoke endpoint behaviour on a network-down panic-wipe.** Mitigation: queue revoke attempts on next network availability via a one-shot WorkManager job, with the local key already destroyed. [TEAM TO VERIFY round-trip on a real device.]
- **a11y service detection coverage.** [TEAM TO VERIFY whether `getEnabledAccessibilityServiceList()` returns services across user profiles on Android 14+.]

---

## 6. What this threat model commits to

- A named mitigation for every named adversary in `plan.md` §20.1.
- A panic-wipe primitive that destroys the SQLCipher key and revokes OAuth tokens in one user-triggered gesture.
- A daily Merkle root surfaced in Settings for tamper-evidence without a remote witness.
- An honest residual-risk statement: kernel-level OS compromise, account-level account compromise, and forced disclosure under coercion are not Aura's defences — they are the user's, the OS's, or unanswerable.

---

End of `threat_model.md`.
