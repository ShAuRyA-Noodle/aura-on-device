"""Candidate-action ranking policy.

Implements technical_spec.md §4.2 + §4.3 + plan.md §1.2 (Silence Budget).

The Policy is intentionally a pure object — no I/O, no global state. Tests
construct it with synthetic ``ActionHistory`` and ``DNDWindow`` objects and
assert exact scores.

Invariants enforced:
- Silence Budget: max ``silence_budget_total`` proactive surfaces per local-day
  (spec default 3, plan §1.2). Wellness ``MUTE_*`` and ``BREATHE_*`` are
  uncapped because they are safety-class actions.
- Window cap: ≤1 surface in any rolling 30-min window per kind.
- Recovering state: zero proactive surfaces while ``state==RECOVERING`` for
  60 minutes after entry.
- DND: surfaces during user-set DND windows are dropped except WATCH haptic
  for safety candidates.

Enforcement order (spec §4.3): DND -> Recovering -> Window -> Daily.
Each rejection becomes a trace entry with `chosen=do_nothing`.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional, Tuple

from agents.core.types import (
    Action,
    Candidate,
    Surface,
    UserState,
    WellnessState,
)


# Action kinds that bypass the daily Silence Budget cap.
SAFETY_KINDS = {"MUTE_GROUP_30", "BREATHE_478", "NAP_15"}

# Auto-execute allowlist (spec §4.4). Anything not in this set must require confirm.
AUTO_EXECUTE_ALLOWLIST = {
    "BATCH_DIGEST",
    "LEAVE_BY_ALERT",
    "SHOW_BRIEF",
    "CATEGORIZE_TXN",
    "SURFACE_ANOMALY",
    "PROJECT_BALANCE",
}


@dataclass
class ActionHistory:
    """Lightweight rolling-window buffer keyed by action.kind."""

    items: List[Tuple[datetime, str]] = field(default_factory=list)
    horizon_hours: int = 36

    def append(self, ts: datetime, kind: str) -> None:
        self.items.append((ts, kind))
        cutoff = ts - timedelta(hours=self.horizon_hours)
        self.items = [(t, k) for (t, k) in self.items if t >= cutoff]

    def count_today(self, kind: str, now: datetime) -> int:
        date = now.date()
        return sum(1 for t, k in self.items if t.date() == date and k == kind)

    def count_window(self, kind: str, minutes: int, now: datetime) -> int:
        floor = now - timedelta(minutes=minutes)
        return sum(1 for t, k in self.items if t >= floor and k == kind)

    def daily_total(self, now: datetime) -> int:
        date = now.date()
        return sum(1 for t, _ in self.items if t.date() == date)

    def daily_total_excluding_safety(self, now: datetime) -> int:
        date = now.date()
        return sum(1 for t, k in self.items if t.date() == date and k not in SAFETY_KINDS)


@dataclass
class DNDWindow:
    """Trivial day-clock DND window. Either always-off or a contiguous range."""

    active: bool = False
    start_hour: Optional[int] = None
    end_hour: Optional[int] = None

    def active_at(self, now: datetime) -> bool:
        if self.active:
            return True
        if self.start_hour is None or self.end_hour is None:
            return False
        h = now.astimezone().hour
        if self.start_hour <= self.end_hour:
            return self.start_hour <= h < self.end_hour
        return h >= self.start_hour or h < self.end_hour


# ---------------------------------------------------------------------------
# Scoring
# ---------------------------------------------------------------------------


def utility(c: Candidate, s: UserState) -> float:
    base = c.agent_priority * c.confidence
    state_mult = {
        WellnessState.BASELINE: 1.0,
        WellnessState.STRESSED: 1.4 if c.kind in SAFETY_KINDS else 0.6,
        WellnessState.RECOVERING: 0.4,
        WellnessState.FOCUSED: 0.7,
        WellnessState.UNKNOWN: 0.8,
    }[s.wellness_state]
    return base * state_mult


def cost(c: Candidate) -> float:
    surface_cost = {
        Surface.WATCH: 0.10,
        Surface.PHONE_CARD: 0.20,
        Surface.EARBUD_TTS: 0.35,
        Surface.SILENT: 0.0,
    }[c.surface]
    confirm_cost = 0.05 if c.confirm_required else 0.0
    return surface_cost + confirm_cost


def recent_penalty(c: Candidate, history: ActionHistory, now: datetime) -> float:
    return 0.25 * history.count_today(c.kind, now) + 0.50 * history.count_window(
        c.kind, minutes=30, now=now
    )


def dnd_penalty(c: Candidate, dnd: DNDWindow, now: datetime) -> float:
    if dnd.active_at(now) and c.surface != Surface.WATCH:
        return 1.0
    return 0.0


def score_candidate(
    c: Candidate,
    s: UserState,
    history: ActionHistory,
    dnd: DNDWindow,
    now: datetime,
) -> Tuple[float, Dict[str, float]]:
    util = utility(c, s)
    co = cost(c)
    rec = recent_penalty(c, history, now)
    dn = dnd_penalty(c, dnd, now)
    total = util - co - rec - dn
    return total, {"util": round(util, 3), "cost": round(co, 3), "recent": round(rec, 3), "dnd": round(dn, 3)}


# ---------------------------------------------------------------------------
# Policy
# ---------------------------------------------------------------------------


@dataclass
class PolicyDecision:
    """Tuple-style decision returned to graph.py for state transition."""

    chosen: Optional[Action]
    candidates: List[Tuple[Candidate, float, Dict[str, float]]]
    cap_reason: Optional[str] = None  # set if blocked by hard cap


@dataclass
class Policy:
    """Per spec §4.2 / §4.3."""

    threshold: float = 0.45
    silence_budget_total: int = 3
    recovering_block_minutes: int = 60

    def decide(
        self,
        candidates: List[Candidate],
        user_state: UserState,
        history: ActionHistory,
        dnd: DNDWindow,
        now: datetime,
        recovering_since: Optional[datetime] = None,
    ) -> PolicyDecision:
        scored: List[Tuple[Candidate, float, Dict[str, float]]] = []
        cap_reason: Optional[str] = None

        # Hard caps (DND -> Recovering -> Window -> Daily) — applied per-candidate.
        eligible: List[Candidate] = []
        for c in candidates:
            # 1. DND.
            if dnd.active_at(now) and c.surface != Surface.WATCH:
                cap_reason = cap_reason or "cap_dnd"
                continue
            # 2. Recovering state — zero proactive for the window.
            if user_state.wellness_state == WellnessState.RECOVERING:
                if recovering_since is not None and now - recovering_since <= timedelta(
                    minutes=self.recovering_block_minutes
                ):
                    cap_reason = cap_reason or "cap_recovering"
                    continue
            # 3. Window cap — ≤1 of this kind in the last 30 minutes.
            if history.count_window(c.kind, minutes=30, now=now) >= 1:
                cap_reason = cap_reason or "cap_window"
                continue
            # 4. Daily Silence Budget.
            if c.kind not in SAFETY_KINDS:
                if history.daily_total_excluding_safety(now) >= self.silence_budget_total:
                    cap_reason = cap_reason or "cap_daily"
                    continue
            eligible.append(c)

        # Score eligible candidates.
        for c in eligible:
            total, comps = score_candidate(c, user_state, history, dnd, now)
            scored.append((c, total, comps))

        scored.sort(key=lambda x: x[1], reverse=True)

        # Confirm-required guard: any kind not on the auto allowlist must confirm.
        chosen_action: Optional[Action] = None
        if scored and scored[0][1] >= self.threshold:
            top, total, comps = scored[0]
            confirm = top.confirm_required or top.kind not in AUTO_EXECUTE_ALLOWLIST
            chosen_action = Action(
                action_id="a_" + _short_hash(top.kind, now.isoformat()),
                kind=top.kind,
                agent=top.agent,
                score=round(total, 3),
                components=comps,
                confirm_required=confirm,
                surface=top.surface,
                args=top.args,
                ts=now.isoformat(),
            )

        return PolicyDecision(
            chosen=chosen_action,
            candidates=scored,
            cap_reason=cap_reason if chosen_action is None else None,
        )


def _short_hash(*parts: str) -> str:
    import hashlib

    h = hashlib.sha256("|".join(parts).encode()).hexdigest()
    return h[:12]
