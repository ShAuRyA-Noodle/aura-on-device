# Contributing to Aura

Engineering rules for the two-person team and any future contributor. This file is the source of truth for code style, commit format, branch naming, and PR process.

---

## 1. Code style

### 1.1 Python (agents, orchestrator, training)

- Python 3.11.
- Formatter: `ruff format`. Linter: `ruff check`. Type checker: `mypy --strict` for `agents/` and `orchestrator/`.
- Line length 100.
- Type annotations are required on every function signature in `agents/` and `orchestrator/`. `Any` is permitted only with a `# justified-any: <reason>` comment.
- Pydantic v2 for all I/O models. Dataclasses for in-memory containers.
- No bare `except:`. Always catch a specific exception class.
- Standard library logging via `logging.getLogger(__name__)`. No `print()` outside `scripts/` and `*_cli.py`.

### 1.2 Swift (iOS app, watch app, custom keyboard)

- Swift 5.10+.
- Formatter: `swift-format` with the repo's `.swift-format` config.
- SwiftUI for views, Combine for state where needed, async/await for concurrency. No `DispatchQueue` for new code.
- `actor` for any type that owns mutable state shared across tasks.
- Force-unwrap (`!`) is forbidden outside `#preview` blocks and unit tests. `try!` permitted only in deterministic constants.
- Access modifiers are explicit: `public`, `internal`, `fileprivate`, `private`. Default `internal` is allowed only inside the app target's main module.

### 1.3 Kotlin (Android app)

- Kotlin 2.0.
- Formatter: `ktlint`. Linter: `detekt`.
- Jetpack Compose for views. Coroutines + `Flow` for concurrency. Avoid `runBlocking` outside tests.
- `data class` for I/O DTOs; `value class` for opaque primitives where it pays.
- Null safety enforced: no `!!` outside test code.

### 1.4 SQL (memory schema, migrations)

- One migration per schema change in `memory/migrations/NNNN_<slug>.sql`.
- Schema changes require an ADR if they alter the public node or edge taxonomy.
- Foreign keys ON. WAL mode. Indexes named `idx_<table>_<cols>`.

### 1.5 JSON (tool calls, traces)

- Schema files live under `agents/<name>/schemas/` and `orchestrator/schemas/`.
- Every tool call and trace is validated against its schema before persistence (`technical_spec.md` §4.5, §4.6).
- Schema versions use `v1`, `v2`, etc.; backwards-incompatible changes increment the version and update the `$id`.

---

## 2. Commit format — Conventional Commits

Every commit message follows the Conventional Commits spec (https://www.conventionalcommits.org/).

Format:

```
<type>(<scope>): <subject>

<body — optional, wrap at 72 cols>

<footer — optional, e.g. Closes #123>
```

Allowed types:

- `feat` — new user-facing feature.
- `fix` — bug fix.
- `refactor` — code restructure without behaviour change.
- `perf` — performance improvement.
- `test` — tests only.
- `docs` — documentation only (this file, ADRs, runbook).
- `chore` — build, config, dependency updates.
- `ci` — CI / GitHub Actions changes.
- `style` — formatting only.

Scopes: `comms`, `calendar`, `finance`, `wellness`, `orch`, `memory`, `ios`, `android`, `watch`, `pilot`, `deck`, `adr`, `repo`.

Examples:

```
feat(wellness): compute Load Score from 9 features
fix(orch): respect 30-minute window cap on safety actions
docs(adr): 0003 Silence Budget as named state variable
test(comms): fixture replay for 47-message storm
```

Subject line is imperative mood, ≤72 characters, no trailing period. Body explains *why* not *what*.

Breaking changes: include a `BREAKING CHANGE:` footer. Bump major version.

---

## 3. Branch naming

```
<type>/<scope>-<short-slug>
```

Examples:

```
feat/wellness-load-score
fix/orch-window-cap
docs/adr-silence-budget
chore/repo-bump-deps
```

The `main` branch is protected. No direct pushes. All changes through PRs. Long-running feature branches rebase weekly to avoid drift.

---

## 4. PR process — 2-person review

Aura is a two-person team (`plan.md` §0). Every PR requires one reviewer who is not the author. The reviewer is mandatory because the team is small; we do not allow self-merge except in the cases listed below.

### 4.1 Self-merge exceptions

The author may merge their own PR only when:

- The PR is `docs(*)` or `chore(*)` and changes no code that ships in the binary.
- The PR is a deck or design asset change confined to `deck/` or `design/`.
- The other reviewer is unavailable for >24 hours and the change is on the critical path of the week's milestone.

In any self-merge, the author records the reason in the PR description and CCs the other team member.

### 4.2 Review checklist

The reviewer confirms:

1. The PR title is Conventional Commits format.
2. The change is covered by tests if it is `feat` or `fix` and ships behaviour.
3. Tests pass locally (`pytest`, `xcodebuild test`, `./gradlew test`).
4. Latency budget assertions are intact for changes inside `agents/` or `orchestrator/` (`technical_spec.md` §2).
5. No new banned word (`plan.md` §5.3) appears in user-visible strings or doc updates: empower, leverage, seamless, revolutionary, paradigm, holistic, robust, cutting-edge, AI-powered, transformative.
6. No new cloud egress is introduced without an ADR (ADR-0005).
7. If the PR touches the trace schema, the orchestrator tool catalogue, or the memory graph schema, an ADR is included or referenced.
8. If the PR is `feat` and adds an action kind, the action is registered in the auto-execute allowlist or the confirm-required map (`technical_spec.md` §4.4).

### 4.3 Merge strategy

- **Squash and merge** for `feat`, `fix`, `refactor`, `perf`. Squashed commit message follows Conventional Commits.
- **Rebase and merge** for `docs`, `chore` with multiple meaningful commits.
- **Never use** the GitHub "Create a merge commit" button on `main`.

### 4.4 PR size

Hard limit: 600 lines of diff per PR (excluding generated and lock files). PRs larger than 600 lines are split or, exceptionally, opened with an explicit reviewer agreement.

---

## 5. Tests are not optional

- Unit tests for every new tool function in an agent.
- Synthetic-input fixture under `agents/<name>/fixtures/` for any new behaviour that crosses an agent boundary.
- Property-based test (Hypothesis) for any parser (SMS, Gmail receipt, ICS).
- Schema validation test for any new tool call or trace field.
- Snapshot test against a fixture for any new orchestrator decision archetype.
- Latency assertion (`pytest-benchmark`) for any new agent `tick()` path.

Coverage target per agent: 85% line, 75% branch (`technical_spec.md` §12.1).

---

## 6. Documentation updates

A PR that touches behaviour also updates:

- `architecture.md` if the layer or component shape changes.
- `data_flow.md` if a user-visible flow changes.
- `runbook.md` if a build or run command changes.
- An ADR if a non-trivial decision is made (see `decisions/README.md`).
- `release_notes/<next>.md` for every user-visible feature, bugfix, or behaviour change.

---

## 7. Privacy invariants — never relax without an ADR

The following invariants are part of the privacy promise (`privacy_promises.md`). A PR that touches any of them requires a referenced ADR and a sign-off from both team members:

- No raw message body persisted past the rolling reasoning window.
- No background cloud sync of personal data.
- Memory graph encrypted at rest under platform Keystore / Secure Enclave keys.
- Reasoning Trace is local-only.
- Silence Budget default ≤5 tokens/day; auto-execute allowlist locked.

---

## 8. Working hours and rest

The plan caps build past 9 PM and reserves Sundays for review and decision records (`plan.md` §24.1, §27 R20). Reviewers respect that window for review SLAs.

---

End of `contributing.md`.
