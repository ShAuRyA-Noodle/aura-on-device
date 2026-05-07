# ADR-0007 — Memory Graph Encryption: Secure Enclave / Keystore + SQLCipher

## Status

Accepted (2026-05-07). Source: `plan.md` §14, §20.2; `technical_spec.md` §6.1, §6.7, §11.

## Context

The memory graph holds the user's structured personal history: events, transactions, conversations (summaries only), health snapshots, actions, and reasoning traces. ADR-0005 commits to on-device storage; this ADR commits to the encryption design.

Adversaries (`threat_model.md`):

- A curious app on the device trying to read Aura's storage.
- A lost or stolen device.
- A malicious app with elevated privilege (a11y, notification listener) trying to exfiltrate the graph.
- Parental coercion (a parent or partner forcing the user to unlock the device).

Constraints:

- Storage must be encrypted at rest with platform-grade keys.
- The encryption key must not be present in plaintext on disk.
- Backup (iCloud Backup, Android Auto Backup) must not exfiltrate the graph.
- Panic-wipe must be possible (`technical_spec.md` §11.6).
- The cipher choice must coexist with sqlite-vss for vector indexing (a known integration hazard, `technical_spec.md` §6.3).

## Decision

Aura uses **SQLCipher 4.x with AES-256** as the at-rest cipher for `memory.sqlite`. The cipher passphrase is derived from a platform-managed key wrapped by hardware where available.

**iOS.** A 32-byte seed is generated once via `SecRandomCopyBytes` and stored in the Keychain with `kSecAttrAccessibleWhenUnlockedThisDeviceOnly` plus `kSecAttrAccessControl` requiring user presence. The Secure Enclave wraps the seed where available (A12 Bionic and later). On launch, the seed is fetched and an HKDF-SHA256 derivation produces the SQLCipher passphrase: `passphrase = HKDF-SHA256(seed, salt=device_id, info="aura.memory.v1", len=32)`. File protection is set to `NSFileProtectionComplete` so the DB file is unreadable when the device is locked. iCloud Backup is disabled for the file via `kCFURLIsExcludedFromBackupKey`.

**Android.** A symmetric AES-256 GCM key is generated in the AndroidKeyStore under the alias `aura_memory_v1` with `setUserAuthenticationRequired(true)` and `AUTH_BIOMETRIC_STRONG`. A static seed encrypted under this key is stored in EncryptedSharedPreferences. On launch, the seed is decrypted (which forces a biometric / device-credential prompt if the auth window has expired) and SQLCipher is initialised with the resulting passphrase. `android:allowBackup="false"` is set on the manifest to disable Android Auto Backup.

**sqlite-vss coexistence.** `load_extension` may be disabled in default Android SQLite builds. The team will compile sqlite-vss as a static library and load it via `db.execSQL("SELECT load_extension('libvss0.so')")` after the SQLCipher passphrase is applied. [TEAM TO VERIFY in Week 4 against the asg017/sqlite-vss issue tracker that the static-link path works on AndroidX SQLite + SQLCipher 4.x. Reference: https://github.com/asg017/sqlite-vss]

**Panic wipe.** The 5-tap power gesture (`technical_spec.md` §11.6) wipes the seed from Keychain / Keystore (irreversible), revokes OAuth refresh tokens via the `oauth2.googleapis.com/revoke` endpoint, deletes the app sandbox files, and relaunches into fresh-install state. A 3-second hold-cancel window protects against accidental wipe.

**Audit log.** Every read, write, delete, export, and wipe operation produces an `audit_log` row with `hash_chain = sha256(prev_hash || row_canonical)`. A daily Merkle root is computed at 00:05 local time over the previous day's rows and stored in `merkle_daily`. The latest 30 roots are surfaced in Settings.

## Consequences

Positive:

- Hardware-wrapped keys give strong assurance against extracted-image attacks.
- Backup exclusion prevents Apple ID / Google account compromise from exfiltrating the graph (covers adversary C in `threat_model.md`).
- The hash-chained audit log plus daily Merkle roots give a tamper-evidence story that holds without a remote witness.
- Panic-wipe is a clean, irreversible primitive (key destruction implies plaintext is unrecoverable).

Negative / costs:

- Biometric prompt on every cold launch on Android is a UX cost. Mitigated by the 60-second auth window (`setUserAuthenticationParameters(60, AUTH_BIOMETRIC_STRONG)`).
- SQLCipher + sqlite-vss is a known-fragile combination. [TEAM TO VERIFY] in Week 4.
- A user who loses their Keychain (factory reset without iCloud Keychain) loses their memory graph permanently. This is the right trade for the privacy promise; an export reminder is shown weekly.
- Hardware-wrapping is best-effort: Android devices below API 28 fall back to software-backed keys. We block install on Android API <29 via `minSdk=29` (`technical_spec.md` §13.5).

## Alternatives

- **Plain SQLite, rely on app sandbox.** Rejected: a rooted or jailbroken device leaks the graph; `threat_model.md` adversary A is unhandled.
- **File-level encryption with NSFileProtectionComplete only.** Rejected: file is decrypted whenever the device is unlocked, even if Aura is not in the foreground. SQLCipher gives application-layer encryption that survives a hostile foreground app.
- **Realm with built-in encryption.** Rejected: Realm's vector-search story is weaker than sqlite-vss; we would have to re-implement embedding indexing.
- **Fully homomorphic encryption.** Out of scope for an EnnovateX student submission.

End of ADR-0007.
