# Aura iOS — UI screens

Tracks every SwiftUI surface in the app and where it stands.

| Status legend |                                            |
| ------------- | ------------------------------------------ |
| `live`        | Wired to real services (HealthKit, EventKit, Bridge, GRDB) |
| `shipped`     | Implemented in `Sources/Aura/Views/` against stubs |
| `phase-2`     | Designed under `aura/design/screens/`; build pending |

## Phase 1 — implemented

| Screen | Source | Design prompt | Status |
| ------ | ------ | ------------- | ------ |
| Morning Brief | `Sources/Aura/Views/MorningBriefView.swift` | `aura/design/screens/01_morning_brief.md` | `live` (HealthKit + EventKit) |
| Reasoning Trace drawer | `Sources/Aura/Views/ReasoningTraceView.swift` | `aura/design/screens/02_reasoning_trace_drawer.md` | `live` (WebSocket stream from FastAPI bridge, JSON syntax-highlight in #FF5B2E) |
| Memory tab | `Sources/Aura/Views/MemoryView.swift` | `aura/design/screens/03_memory_tab.md` | `live` (GRDB SQLite, real export/delete/audit) |
| Silence Budget panel | `Sources/Aura/Views/SilenceBudgetView.swift` | — | `live` (UserDefaults + iCloud KVS) |
| Onboarding / Permissions | `Sources/Aura/Views/Onboarding/PermissionFlow.swift` | — | `live` (real HealthKit / Calendar / Notification prompts) |
| Settings (bridge status, budget reset, about) | `Sources/Aura/AuraApp.swift` (`SettingsView`) | — | `live` |

The four implemented tabs share the `RootTabView` defined in
`AuraApp.swift`: **Brief** → Morning Brief, **Memory** → Memory tab,
**Trace** → live Reasoning Trace, **Settings** → SettingsView.

## Phase 2 — to build

| Screen | Design prompt | Drives | Notes |
| ------ | ------------- | ------ | ----- |
| Spend Mirror | `aura/design/screens/04_spend_mirror.md` | FinanceAgent | Pull receipts via the Gmail OAuth flow that ships in `GmailService`. Categorise on-device, surface weekly digest. |
| Quiet Group Chat | `aura/design/screens/05_quiet_group_chat.md` | CommsAgent | Coalesces noisy group threads; budgeted by `SilenceBudget`. |
| Load Score Panel | `aura/design/screens/06_load_score_panel.md` | WellnessAgent | Shows the rolling Wellness Load Score from HealthKit (HRV + sleep + HR + steps). The data path is already live via `HealthService.snapshot()`. |

## Functional checklist (post Phase 1 wiring)

- [x] HealthKit reads (HRV SDNN, heart rate, sleep, steps) — `HealthService`.
- [x] EventKit reads (next 24 h, conflict detection) — `CalendarService`.
- [x] MapKit travel-time and leave-by suggestion — `CalendarService.leaveBy`.
- [x] Gmail OAuth via GoogleSignIn-iOS, receipt fetch, regex-based amount parsing — `GmailService`.
- [x] FastAPI bridge: REST `/healthz`, `/traces`, plus WebSocket `/ws/traces` — `AuraBridge`.
- [x] Live JSON syntax highlighting (sunset-orange `chosen`, `rationale`, `confirm_required`) — `TraceJSONView`.
- [x] On-device memory graph: schema, insert, delete-by-range, hash-chained audit log, JSON export — `MemoryService`.
- [x] Silence Budget persistence + iCloud KVS sync + midnight notification — `SilenceBudget`.
- [x] BGAppRefreshTask + BGProcessingTask registration — `AuraAppDelegate`.
- [x] Progressive permission flow — `PermissionFlow`.
- [ ] Spend Mirror view (Phase 2).
- [ ] Quiet Group Chat view (Phase 2).
- [ ] Load Score Panel view (Phase 2).
- [ ] iCloud KVS entitlement enabled in App Store Connect (manual step).

## Cross-cutting components

- `BriefCard` (`MorningBriefView.swift`) — re-used across Phase 2 surfaces.
- `Trace` model + `AnyCodable` (`Models/Trace.swift`) — every agent emits a
  Reasoning Trace; the drawer renders any of them.
- `SilenceBudget` (`Services/SilenceBudget.swift`) — every proactive
  surface must call `silenceBudget.spend(...)` before showing.
- `AuraBridge.shared` (`Services/AuraBridge.swift`) — single live link to
  the Mac orchestrator.
