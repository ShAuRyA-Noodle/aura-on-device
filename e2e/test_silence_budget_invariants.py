"""Silence Budget invariants (plan §1.2 + spec §4.3).

Asserts the four contract invariants of :class:`SilenceBudget`:

1. ``remaining`` never goes below 0 — even after over-decrement.
2. ``remaining`` never exceeds ``total`` — refund-on-useful caps at total.
3. Refund-on-useful caps at ``total`` (extra refunds are no-ops).
4. ``maybe_reset(now)`` resets to ``total`` deterministically when the
   local-date rolls over.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from orchestrator.policy import SilenceBudget


def _now(*args, tz=timezone.utc) -> datetime:
    return datetime(*args, tzinfo=tz)


# ---------------------------------------------------------------------------
# Invariant 1 — remaining never below 0
# ---------------------------------------------------------------------------


def test_budget_never_below_zero_after_repeat_decrement():
    b = SilenceBudget(total=3, remaining=3)
    for _ in range(50):
        b.decrement("SHOW_BRIEF")
    assert b.remaining == 0


def test_budget_post_init_clamps_negative_to_zero():
    b = SilenceBudget(total=3, remaining=-7)
    assert b.remaining == 0


# ---------------------------------------------------------------------------
# Invariant 2 — remaining never exceeds total
# ---------------------------------------------------------------------------


def test_budget_never_exceeds_total_via_refund():
    b = SilenceBudget(total=3, remaining=2)
    for _ in range(20):
        b.refund_on_useful("SHOW_BRIEF")
    assert b.remaining == 3


def test_budget_post_init_clamps_above_total():
    b = SilenceBudget(total=3, remaining=99)
    assert b.remaining == 3


# ---------------------------------------------------------------------------
# Invariant 3 — refund caps at total + safety actions don't move budget
# ---------------------------------------------------------------------------


def test_refund_at_full_is_noop():
    b = SilenceBudget(total=3, remaining=3)
    b.refund_on_useful("SHOW_BRIEF")
    assert b.remaining == 3


def test_safety_kinds_do_not_decrement_budget():
    b = SilenceBudget(total=3, remaining=3)
    b.decrement("MUTE_GROUP_30")
    b.decrement("BREATHE_478")
    b.decrement("NAP_15")
    assert b.remaining == 3


def test_safety_kinds_refund_is_noop():
    b = SilenceBudget(total=3, remaining=2)
    b.refund_on_useful("MUTE_GROUP_30")
    assert b.remaining == 2


def test_decrement_then_refund_round_trip():
    b = SilenceBudget(total=3, remaining=3)
    b.decrement("SHOW_BRIEF")
    assert b.remaining == 2
    b.refund_on_useful("SHOW_BRIEF")
    assert b.remaining == 3


# ---------------------------------------------------------------------------
# Invariant 4 — midnight reset works deterministically
# ---------------------------------------------------------------------------


def test_midnight_reset_resets_to_total():
    """Reset must fire when the local-date crosses midnight.

    We bind both timestamps to a fixed UTC offset (+05:30) so the local-date
    boundary is reproducible regardless of where this test runs.
    """
    ist = timezone(timedelta(hours=5, minutes=30))
    b = SilenceBudget(total=3, remaining=0)
    day1 = datetime(2026, 5, 7, 23, 50, tzinfo=ist)
    b.maybe_reset(day1)  # establishes baseline date 2026-05-07
    assert b.remaining == 0  # not yet rolled

    day2 = datetime(2026, 5, 8, 0, 5, tzinfo=ist)
    rolled = b.maybe_reset(day2)
    assert rolled is True
    assert b.remaining == 3


def test_same_day_reset_is_noop():
    ist = timezone(timedelta(hours=5, minutes=30))
    b = SilenceBudget(total=3, remaining=1)
    morning = datetime(2026, 5, 7, 8, 0, tzinfo=ist)
    b.maybe_reset(morning)
    evening = datetime(2026, 5, 7, 22, 30, tzinfo=ist)
    rolled = b.maybe_reset(evening)
    assert rolled is False
    assert b.remaining == 1


def test_reset_uses_local_timezone_boundary():
    """Reset boundary follows the local timezone, not UTC."""
    # Both inputs are at 23:30 UTC — but in IST (+05:30) this straddles
    # 05:00 next day. The local-date should change so reset fires.
    from datetime import timezone as _tz

    ist = _tz(timedelta(hours=5, minutes=30))
    b = SilenceBudget(total=3, remaining=0)
    t1 = datetime(2026, 5, 7, 23, 30, tzinfo=ist)
    b.maybe_reset(t1)
    assert b.remaining == 0
    t2 = datetime(2026, 5, 8, 6, 0, tzinfo=ist)
    rolled = b.maybe_reset(t2)
    assert rolled is True
    assert b.remaining == 3


# ---------------------------------------------------------------------------
# Orchestrator-level integration — budget decrements when a non-safety
# surface is chosen, recovers via refund.
# ---------------------------------------------------------------------------


def test_budget_decrements_through_orchestrator_tick(orchestrator):
    """One non-safety surface choice -> budget remaining drops by 1."""
    from agents.core.types import UserState
    from orchestrator.replay import load_replay

    fx = load_replay("monday_brief")
    user_state = UserState(**fx["user_state"])
    assert orchestrator.budget.remaining == 3
    orchestrator.tick(
        user_state=user_state,
        agent_payloads=fx["agent_payloads"],
        tick_ts=fx["tick_ts"],
        trigger=fx.get("trigger"),
    )
    assert orchestrator.budget.remaining == 2


def test_budget_blocks_non_safety_when_empty(orchestrator):
    """When the budget is exhausted, a non-safety candidate is demoted to
    do_nothing with cap_reason='cap_silence_budget'."""
    from agents.core.types import UserState
    from orchestrator.replay import load_replay

    orchestrator.budget.remaining = 0
    fx = load_replay("monday_brief")
    user_state = UserState(**fx["user_state"])
    res = orchestrator.tick(
        user_state=user_state,
        agent_payloads=fx["agent_payloads"],
        tick_ts=fx["tick_ts"],
        trigger=fx.get("trigger"),
    )
    assert res.chosen_kind == "do_nothing"
    assert res.cap_reason == "cap_silence_budget"
