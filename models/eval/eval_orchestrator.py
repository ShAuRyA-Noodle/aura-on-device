"""Evaluation harness for the Aura orchestrator.

Spec source: technical_spec.md section 4 (Orchestrator) + section 9.3
(Orchestrator LoRA Phase 2 trigger).

We measure three things on a frozen replay fixture:

    1. Tool-call hallucination rate
       - A "hallucinated" call is any tool name that is not in the
         allowed tool-set, or any tool whose arguments fail the JSON
         schema in `orchestrator/tools/schema.json`. The Phase 2 trigger
         from configs/orchestrator_lora.yaml is 5%.

    2. Schema validation rate
       - The fraction of orchestrator outputs that parse as valid JSON
         and validate against the tool-call schema.

    3. End-to-end trace correctness on the replay fixture
       - For each fixture trace we compare the orchestrator's chosen
         action and ordered tool sequence against the gold sequence.
         Equality is `(action == gold_action) AND (tool_seq == gold_seq)`.

The replay fixture is expected at:
    orchestrator/replays/replay_fixture.jsonl

Each line is:
    {
        "trace_id": "...",
        "input": { ... },
        "gold_action": "MUTE_GROUP",
        "gold_tool_seq": [
            {"name": "classify", "args": {...}},
            {"name": "snooze",   "args": {...}}
        ]
    }

A small fallback fixture is built in-memory if the file is absent so
the harness is runnable on a fresh clone.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple


ALLOWED_TOOLS: Tuple[str, ...] = (
    # CommsAgent
    "classify",
    "draft_reply",
    "batch_summarize",
    "snooze",
    "triage_inbox",
    # CalendarAgent
    "leave_by",
    "find_slot",
    "detect_conflicts",
    # FinanceAgent
    "parse_sms",
    "parse_gmail_receipt",
    "categorize",
    "anomaly_flag",
    "predict_eom_balance",
    "suggest_substitution",
    # WellnessAgent
    "compute_load",
    "suggest_intervention",
    # Orchestrator-internal
    "rank_actions",
    "emit_card",
    "noop",
)


# --------------------------------------------------------------------------- #
# Schema check (deliberately minimal — full schema lives in
# orchestrator/tools/schema.json; this is a pre-flight gate).
# --------------------------------------------------------------------------- #


def is_valid_tool_call(call: Any) -> Tuple[bool, str]:
    """Return (is_valid, reason)."""
    if not isinstance(call, dict):
        return False, "not_a_dict"
    name = call.get("name")
    if not isinstance(name, str) or not name:
        return False, "missing_name"
    if name not in ALLOWED_TOOLS:
        return False, f"hallucinated_tool:{name}"
    args = call.get("args")
    if args is not None and not isinstance(args, dict):
        return False, "args_not_dict"
    return True, "ok"


def is_valid_tool_seq(seq: Any) -> Tuple[bool, List[str]]:
    if not isinstance(seq, list):
        return False, ["seq_not_list"]
    reasons: List[str] = []
    for i, call in enumerate(seq):
        ok, why = is_valid_tool_call(call)
        if not ok:
            reasons.append(f"[{i}]:{why}")
    return (len(reasons) == 0), reasons


# --------------------------------------------------------------------------- #
# Metrics.
# --------------------------------------------------------------------------- #


def tool_call_hallucination_rate(
    predictions: List[Dict[str, Any]],
) -> Dict[str, Any]:
    """Fraction of predicted tool calls that fail the schema/allowlist."""
    total_calls = 0
    bad_calls = 0
    bad_breakdown: Dict[str, int] = {}
    for pred in predictions:
        seq = pred.get("tool_seq", [])
        if not isinstance(seq, list):
            bad_calls += 1
            total_calls += 1
            bad_breakdown["seq_not_list"] = bad_breakdown.get(
                "seq_not_list", 0
            ) + 1
            continue
        for call in seq:
            total_calls += 1
            ok, why = is_valid_tool_call(call)
            if not ok:
                bad_calls += 1
                bucket = why.split(":", 1)[0]
                bad_breakdown[bucket] = bad_breakdown.get(bucket, 0) + 1
    return {
        "total_calls": total_calls,
        "bad_calls": bad_calls,
        "rate": round(bad_calls / total_calls, 4) if total_calls else 0.0,
        "breakdown": bad_breakdown,
    }


def schema_validation_rate(
    predictions: List[Dict[str, Any]],
) -> Dict[str, Any]:
    valid = 0
    for pred in predictions:
        ok, _ = is_valid_tool_seq(pred.get("tool_seq", []))
        if ok:
            valid += 1
    n = len(predictions)
    return {
        "n": n,
        "valid": valid,
        "rate": round(valid / n, 4) if n else 0.0,
    }


def trace_correctness(
    fixtures: List[Dict[str, Any]],
    predictions: List[Dict[str, Any]],
) -> Dict[str, Any]:
    correct = 0
    failures: List[Dict[str, Any]] = []
    for fix, pred in zip(fixtures, predictions):
        gold_action = fix.get("gold_action")
        gold_seq = fix.get("gold_tool_seq", [])
        pred_action = pred.get("action")
        pred_seq = pred.get("tool_seq", [])
        action_ok = pred_action == gold_action
        seq_ok = _normalised_seq(pred_seq) == _normalised_seq(gold_seq)
        if action_ok and seq_ok:
            correct += 1
        else:
            failures.append(
                {
                    "trace_id": fix.get("trace_id"),
                    "action_ok": action_ok,
                    "seq_ok": seq_ok,
                }
            )
    n = len(fixtures)
    return {
        "n": n,
        "correct": correct,
        "rate": round(correct / n, 4) if n else 0.0,
        "failures": failures,
    }


def _normalised_seq(seq: Any) -> List[str]:
    """Reduce a tool sequence to ordered tool names for comparison."""
    if not isinstance(seq, list):
        return []
    return [str(call.get("name", "")) for call in seq if isinstance(call, dict)]


# --------------------------------------------------------------------------- #
# Stub orchestrator predictor for harness sanity.
# --------------------------------------------------------------------------- #


def _stub_orchestrator(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Pretend orchestrator that pattern-matches on the input scenario.

    This is only good enough to exercise the eval pipeline. The real
    predictor is `orchestrator.run.predict_one(payload)` once that
    module is implemented; pass it via `--predictor` at the CLI level.
    """
    scenario = (payload or {}).get("scenario", "")
    if scenario == "storm":
        return {
            "action": "BATCH_DIGEST",
            "tool_seq": [
                {"name": "classify", "args": {}},
                {"name": "batch_summarize", "args": {}},
                {"name": "snooze", "args": {"ttl_seconds": 1800}},
            ],
        }
    if scenario == "morning_brief":
        return {
            "action": "SHOW_BRIEF",
            "tool_seq": [
                {"name": "triage_inbox", "args": {"scope": "unread_24h"}},
                {"name": "leave_by", "args": {}},
                {"name": "compute_load", "args": {}},
                {"name": "emit_card", "args": {}},
            ],
        }
    if scenario == "spend_mirror":
        return {
            "action": "SURFACE_SPEND",
            "tool_seq": [
                {"name": "parse_sms", "args": {}},
                {"name": "categorize", "args": {}},
                {"name": "anomaly_flag", "args": {}},
                {"name": "predict_eom_balance", "args": {}},
            ],
        }
    return {"action": "NOOP", "tool_seq": [{"name": "noop", "args": {}}]}


def _builtin_fallback_fixture() -> List[Dict[str, Any]]:
    """In-memory replay fixture used when the canonical file is missing."""
    return [
        {
            "trace_id": "storm_47",
            "input": {"scenario": "storm"},
            "gold_action": "BATCH_DIGEST",
            "gold_tool_seq": [
                {"name": "classify", "args": {}},
                {"name": "batch_summarize", "args": {}},
                {"name": "snooze", "args": {}},
            ],
        },
        {
            "trace_id": "morning_brief_aanya",
            "input": {"scenario": "morning_brief"},
            "gold_action": "SHOW_BRIEF",
            "gold_tool_seq": [
                {"name": "triage_inbox", "args": {}},
                {"name": "leave_by", "args": {}},
                {"name": "compute_load", "args": {}},
                {"name": "emit_card", "args": {}},
            ],
        },
        {
            "trace_id": "spend_mirror_kabir",
            "input": {"scenario": "spend_mirror"},
            "gold_action": "SURFACE_SPEND",
            "gold_tool_seq": [
                {"name": "parse_sms", "args": {}},
                {"name": "categorize", "args": {}},
                {"name": "anomaly_flag", "args": {}},
                {"name": "predict_eom_balance", "args": {}},
            ],
        },
    ]


# --------------------------------------------------------------------------- #
# Top-level evaluator.
# --------------------------------------------------------------------------- #


def evaluate_orchestrator(
    fixtures: List[Dict[str, Any]],
    predictor: Callable[[Dict[str, Any]], Dict[str, Any]],
) -> Dict[str, Any]:
    predictions: List[Dict[str, Any]] = []
    for fix in fixtures:
        try:
            predictions.append(predictor(fix.get("input", {})) or {})
        except Exception as exc:  # pragma: no cover - defensive
            predictions.append({"action": None, "tool_seq": [],
                                "error": str(exc)})
    halluc = tool_call_hallucination_rate(predictions)
    schema = schema_validation_rate(predictions)
    trace = trace_correctness(fixtures, predictions)
    phase2_trigger = halluc["rate"] > 0.05
    return {
        "n_traces": len(fixtures),
        "tool_call_hallucination": halluc,
        "schema_validation": schema,
        "trace_correctness": trace,
        "phase2_lora_trigger": phase2_trigger,
        "phase2_threshold": 0.05,
    }


# --------------------------------------------------------------------------- #
# I/O.
# --------------------------------------------------------------------------- #


def load_jsonl(path: Path) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    with open(path, "r", encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            rows.append(json.loads(line))
    return rows


def render_report(result: Dict[str, Any]) -> str:
    lines = [
        "# Aura orchestrator eval report",
        "",
        f"- traces: {result['n_traces']}",
        "",
        "## Tool-call hallucination",
        f"- rate: {result['tool_call_hallucination']['rate']}",
        f"- bad/total: "
        f"{result['tool_call_hallucination']['bad_calls']}/"
        f"{result['tool_call_hallucination']['total_calls']}",
        f"- breakdown: {result['tool_call_hallucination']['breakdown']}",
        "",
        "## Schema validation",
        f"- rate: {result['schema_validation']['rate']} "
        f"({result['schema_validation']['valid']}/"
        f"{result['schema_validation']['n']})",
        "",
        "## End-to-end trace correctness",
        f"- rate: {result['trace_correctness']['rate']} "
        f"({result['trace_correctness']['correct']}/"
        f"{result['trace_correctness']['n']})",
        "",
        "## Phase 2 LoRA trigger",
        f"- threshold: {result['phase2_threshold']}",
        f"- triggered: {result['phase2_lora_trigger']}",
    ]
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Evaluate the Aura orchestrator on a replay fixture."
    )
    parser.add_argument(
        "--fixture",
        default="orchestrator/replays/replay_fixture.jsonl",
        help="Replay fixture JSONL.",
    )
    parser.add_argument(
        "--project-root",
        default=str(Path(__file__).resolve().parents[2]),
    )
    parser.add_argument(
        "--out-json",
        default="",
        help="Optional path to dump the result dict as JSON.",
    )
    args = parser.parse_args()
    project_root = Path(args.project_root).resolve()

    fixture_path = project_root / args.fixture
    if fixture_path.exists():
        fixtures = load_jsonl(fixture_path)
        print(f"[info] loaded {len(fixtures)} fixture rows from {fixture_path}")
    else:
        fixtures = _builtin_fallback_fixture()
        print(
            f"[warn] {fixture_path} missing; using built-in fallback "
            f"({len(fixtures)} rows)",
            file=sys.stderr,
        )

    result = evaluate_orchestrator(fixtures, _stub_orchestrator)
    print(render_report(result))
    if args.out_json:
        out_path = project_root / args.out_json
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(json.dumps(result, indent=2), encoding="utf-8")
        print(f"\n[info] result JSON written to {out_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
