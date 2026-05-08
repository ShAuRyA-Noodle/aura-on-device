"""End-to-end: Quiet Group Chat — the WhatsApp 137-message flood (plan §11).

Synthesises a 137-message burst on a single project channel where exactly 3
messages are actionable (one @you mention, one explicit deadline, one direct
ask) and 134 are SOCIAL chatter. Wires Comms + Wellness into the
Orchestrator and asserts:

- 3 actionable surfaced in the Comms payload.
- 134 muted (SOCIAL / SPAM / BROADCAST collapsed).
- Reasoning Trace emitted (schema-valid).
- Wellness Agent reaches a stress state and proposes a safety candidate
  (MUTE_GROUP_30 or BREATHE_478) — i.e. an intervention is triggered.
"""

from __future__ import annotations

from typing import Any, Dict, List

import pytest

from agents.core.types import AgentName, UserState, WellnessState
from orchestrator.graph import Orchestrator
from orchestrator.trace import validate_trace


_CHANNEL = "group:Thapar-DSA-Project"
_TS = "2026-05-07T22:31:47+05:30"


def _build_137_message_burst() -> List[Dict[str, Any]]:
    """3 actionable + 134 social messages, all on the same channel."""
    msgs: List[Dict[str, Any]] = []

    actionable = [
        {
            "id": "n_act_001",
            "preview": "@you can you confirm the schema diagram for tomorrow's quiz",
        },
        {
            "id": "n_act_002",
            "preview": "deadline is tonight 11pm for the DBMS submission please review",
        },
        {
            "id": "n_act_003",
            "preview": "need help merging the migration file before we deploy",
        },
    ]
    for i, a in enumerate(actionable):
        msgs.append({
            "id": a["id"],
            "app_pkg": "com.whatsapp",
            "channel": _CHANNEL,
            "sender_hash": f"h_actor_{i}",
            "preview": a["preview"],
            "ts": _TS,
        })

    # 134 social messages — each token in _SOCIAL_TOKENS triggers SOCIAL bucket.
    social_phrases = [
        "lol", "haha", "lmao", "gn", "gm", "brb", "nice", "cool",
        "ok", "okay", "thanks", "thx", "ty", "np", "same", "fr",
        "true", "bruh", "btw", "idk", "tbh", "ngl",
    ]
    for i in range(134):
        phrase = social_phrases[i % len(social_phrases)]
        msgs.append({
            "id": f"n_soc_{i:03d}",
            "app_pkg": "com.whatsapp",
            "channel": _CHANNEL,
            "sender_hash": f"h_sender_{i % 12}",
            "preview": f"{phrase} {phrase}",
            "ts": _TS,
        })
    assert len(msgs) == 137
    return msgs


def test_quiet_group_chat_e2e_full_run(orchestrator: Orchestrator) -> None:
    notif = _build_137_message_burst()

    user_state = UserState(
        load_score=78,
        wellness_state=WellnessState.STRESSED,
        in_focus_block=False,
    )
    payloads: Dict[str, Dict[str, Any]] = {
        "comms": {"notif_events": notif, "gmail_threads": []},
        "calendar": {"events_today": []},
        "finance": {
            "sms_unprocessed": [],
            "gmail_receipts": [],
            "balance_seed": None,
        },
        "wellness": {
            "hrv_window": {"rmssd_ms": 24.1, "samples": 12, "window_min": 5},
            "sleep_last_night": {"asleep_min": 312, "rem_min": 41, "deep_min": 33, "efficiency": 0.78},
            "typing_entropy_60s": 4.92,
            "app_switch_rate_60s": 16,
            "notif_dismiss_rate_60m": 0.81,
            "screen_on_min_60m": 47,
            "personal_baseline": {"rmssd_p50": 38.2, "rmssd_p10": 22.1, "switch_p50": 6},
            "active_channel": _CHANNEL,
        },
    }

    res = orchestrator.tick(
        user_state=user_state,
        agent_payloads=payloads,
        tick_ts=_TS,
        trigger={"source": "notif_burst", "value": {"count": 137, "channel": _CHANNEL}},
    )

    # 1. Comms payload — exactly 3 actionable, 134 muted.
    comms_out = next(o for o in res.agent_outputs if o.agent == AgentName.COMMS)
    urgent = comms_out.payload["urgent"]
    muted_count = comms_out.payload["muted_count"]
    assert len(urgent) == 3, f"expected 3 actionable, got {len(urgent)}: {urgent}"
    assert muted_count == 134, f"expected 134 muted, got {muted_count}"

    # 2. Reasoning Trace logged + schema valid.
    assert res.trace is not None
    validate_trace(res.trace)

    # 3. Wellness Agent triggered an intervention candidate.
    wellness_out = next(o for o in res.agent_outputs if o.agent == AgentName.WELLNESS)
    wellness_kinds = [c.kind for c in wellness_out.candidates]
    assert any(k in ("MUTE_GROUP_30", "BREATHE_478", "NAP_15") for k in wellness_kinds), (
        f"wellness produced no intervention: {wellness_kinds}"
    )

    # 4. Chosen action is the safety surface (MUTE_GROUP_30 wins under STRESSED).
    assert res.chosen_kind in ("MUTE_GROUP_30", "BATCH_DIGEST"), res.chosen_kind


def test_quiet_group_chat_matches_canonical_trace(canonical_traces_dir) -> None:
    """Trace JSON must structurally match the frozen canonical artifact."""
    import json

    from deepdiff import DeepDiff
    from orchestrator.replay import run_replay

    canonical = json.loads(
        (canonical_traces_dir / "quiet_group_chat_trace.json").read_text()
    )
    out = run_replay("quiet_group_chat", write_output=False)
    diff = DeepDiff(
        canonical,
        out["trace"],
        exclude_paths=["root['ts']"],
        ignore_order=False,
    )
    assert not diff, f"trace drift vs canonical: {diff}"


def test_quiet_group_chat_replay_137_messages(quiet_group_chat_replay) -> None:
    """The replay JSON expands to exactly 137 notifications (3 actionable
    + 134 social) before reaching the orchestrator."""
    notif = quiet_group_chat_replay["agent_payloads"]["comms"]["notif_events"]
    assert len(notif) == 137, len(notif)
    actionable = [n for n in notif if n["id"].startswith("n_act_")]
    social = [n for n in notif if n["id"].startswith("n_soc_")]
    assert len(actionable) == 3
    assert len(social) == 134


def test_quiet_group_chat_no_pii_in_trace(orchestrator: Orchestrator) -> None:
    notif = _build_137_message_burst()
    user_state = UserState(load_score=78, wellness_state=WellnessState.STRESSED)
    payloads = {
        "comms": {"notif_events": notif, "gmail_threads": []},
        "calendar": {"events_today": []},
        "finance": {"sms_unprocessed": [], "gmail_receipts": [], "balance_seed": None},
        "wellness": {
            "hrv_window": {"rmssd_ms": 24.1, "samples": 12, "window_min": 5},
            "sleep_last_night": {"asleep_min": 312},
            "typing_entropy_60s": 4.92,
            "app_switch_rate_60s": 16,
            "notif_dismiss_rate_60m": 0.81,
            "screen_on_min_60m": 47,
            "personal_baseline": {"rmssd_p50": 38.2, "rmssd_p10": 22.1, "switch_p50": 6},
            "active_channel": _CHANNEL,
        },
    }
    res = orchestrator.tick(user_state=user_state, agent_payloads=payloads, tick_ts=_TS)

    payload = res.trace.model_dump_json()
    for raw in ("schema diagram", "DBMS submission", "merging the migration"):
        assert raw not in payload, f"PII leak: {raw!r}"
