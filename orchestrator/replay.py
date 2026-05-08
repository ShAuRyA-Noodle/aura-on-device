"""Replay runner for Aura orchestrator demos.

Loads a replay JSON from ``orchestrator/replays/<name>.replay.json``, builds
a fresh ``Orchestrator`` with the four agents, drives one tick, then prints
the Reasoning Trace and persists the trace to
``orchestrator/replays/output/<name>_trace.json``.

Usage::

    python -m orchestrator.replay monday_brief
    python -m orchestrator.replay quiet_group_chat
    python -m orchestrator.replay spend_mirror
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import Any, Dict

from agents.calendar.agent import CalendarAgent
from agents.comms.agent import CommsAgent
from agents.core.types import AgentName, UserState
from agents.finance.agent import FinanceAgent
from agents.wellness.agent import WellnessAgent

from .graph import Orchestrator, langgraph_status
from .policy import ActionHistory, DNDWindow, Policy, SilenceBudget
from .trace import pretty_render, trace_canonical_hash


_REPLAYS_DIR = Path(__file__).resolve().parent / "replays"
_OUTPUT_DIR = _REPLAYS_DIR / "output"


class _FinanceAdapter:
    """Same shape used by e2e/conftest.py — exposes name + sync tick."""

    name = AgentName.FINANCE
    latency_budget_ms = 350

    def __init__(self, inner: FinanceAgent) -> None:
        self._inner = inner

    def tick(self, payload):  # noqa: D401 — orchestrator calls with payload
        return self._inner.tick(payload)


def build_orchestrator() -> Orchestrator:
    """A fresh four-agent orchestrator with default policy + budget."""
    return Orchestrator(
        agents=[
            CommsAgent(),
            CalendarAgent(),
            _FinanceAdapter(FinanceAgent()),
            WellnessAgent(),
        ],
        policy=Policy(silence_budget_total=3),
        history=ActionHistory(),
        dnd=DNDWindow(),
        budget=SilenceBudget(total=3, remaining=3),
    )


def load_replay(name: str) -> Dict[str, Any]:
    """Load ``replays/<name>.replay.json`` and expand any synthetic burst markers."""
    path = _REPLAYS_DIR / f"{name}.replay.json"
    if not path.exists():
        raise FileNotFoundError(f"replay not found: {path}")
    fx = json.loads(path.read_text())
    _expand_burst(fx)
    return fx


def _expand_burst(fx: Dict[str, Any]) -> None:
    """Expand ``_burst_tail_count`` social messages so the comms payload has
    the full burst the test asserts (e.g. 134 social tail for the 137-message
    quiet-group-chat replay)."""
    comms = (fx.get("agent_payloads") or {}).get("comms") or {}
    tail = int(comms.pop("_burst_tail_count", 0) or 0)
    phrases = comms.pop("_burst_phrases", []) or []
    if tail <= 0 or not phrases:
        return
    notif = comms.setdefault("notif_events", [])
    seed_event = notif[0] if notif else {}
    channel = seed_event.get("channel", "group:default")
    ts = seed_event.get("ts", fx.get("tick_ts"))
    app_pkg = seed_event.get("app_pkg", "com.whatsapp")
    for i in range(tail):
        phrase = phrases[i % len(phrases)]
        notif.append({
            "id": f"n_soc_{i:03d}",
            "app_pkg": app_pkg,
            "channel": channel,
            "sender_hash": f"h_sender_{i % 12}",
            "preview": f"{phrase} {phrase}",
            "ts": ts,
        })


def run_replay(name: str, write_output: bool = True) -> Dict[str, Any]:
    """Run the replay and return ``{trace, hash, sha256, used_langgraph, ...}``."""
    fx = load_replay(name)
    user_state = UserState(**fx["user_state"])
    orch = build_orchestrator()
    res = orch.tick(
        user_state=user_state,
        agent_payloads=fx["agent_payloads"],
        tick_ts=fx["tick_ts"],
        trigger=fx.get("trigger", {"source": "replay", "value": name}),
    )
    trace_dict = res.trace.model_dump(mode="json")
    # Force a deterministic trace_id derived from the replay name + tick_ts so
    # identical fixtures always hash the same regardless of UUID seeding.
    deterministic_id = "tr_" + hashlib.sha256(
        (name + "|" + fx["tick_ts"]).encode()
    ).hexdigest()[:12]
    trace_dict["trace_id"] = deterministic_id
    out = {
        "name": name,
        "trace": trace_dict,
        "chosen_kind": res.chosen_kind,
        "cap_reason": res.cap_reason,
        "used_langgraph": res.used_langgraph,
        "state_path": res.state_path,
        "budget_remaining": orch.budget.remaining,
        "sha256": _sha256_struct(trace_dict, strip_ts=True),
    }
    if write_output:
        _OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        out_path = _OUTPUT_DIR / f"{name}_trace.json"
        out_path.write_text(json.dumps(trace_dict, indent=2, sort_keys=True))
    return out


def _sha256_struct(trace_dict: Dict[str, Any], strip_ts: bool = True) -> str:
    """Hash the trace JSON with timestamps stripped for deterministic compare."""
    payload = dict(trace_dict)
    if strip_ts:
        payload.pop("ts", None)
        # signals are agent-emitted dicts; their structure is deterministic
        # across runs because all classifiers/calculators are pure.
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode()).hexdigest()


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(prog="orchestrator.replay")
    parser.add_argument("name", help="replay name (without .replay.json)")
    parser.add_argument("--no-write", action="store_true", help="don't persist trace")
    parser.add_argument("--json-only", action="store_true", help="emit only the JSON trace")
    args = parser.parse_args(argv)

    out = run_replay(args.name, write_output=not args.no_write)

    if args.json_only:
        print(json.dumps(out["trace"], indent=2, sort_keys=True))
        return 0

    print(f"=== Aura replay: {args.name} ===")
    print(f"runtime: {'LangGraph' if out['used_langgraph'] else 'deterministic-fallback'}")
    print(f"state_path: {' -> '.join(out['state_path'])}")
    print(f"chosen_kind: {out['chosen_kind']}  cap_reason: {out['cap_reason']}")
    print(f"silence_budget_remaining: {out['budget_remaining']}")
    print(f"sha256(trace, ts-stripped): {out['sha256']}")
    print()
    # Reuse the existing pretty_render — feed it the trace dict.
    from agents.core.types import Trace

    trace_for_render = Trace.model_validate(out["trace"])
    print(pretty_render(trace_for_render))
    print()
    print(f"langgraph_status: {langgraph_status()}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
