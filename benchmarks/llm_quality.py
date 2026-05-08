"""LLM-in-the-loop schema-validity benchmark.

Replays each fixture in ``aura/orchestrator/replays/`` with the LLM
narrator enabled (``AURA_USE_LLM=1``) and counts how many emitted
``Trace`` objects pass ``orchestrator.trace.validate_trace``. Reports
the percentage of schema-valid generations.

This is the regression check the Comms / Finance / Orchestrator changes
need: the structured-output path must keep producing valid JSON traces
even when the LLM is on.

Usage::

    python -m aura.benchmarks.llm_quality
    python -m aura.benchmarks.llm_quality --replays monday_brief
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import date
from pathlib import Path
from typing import Any, Dict, List, Optional


sys.path.insert(0, str(Path(__file__).resolve().parents[1].parent))


def _replay_dir() -> Path:
    return Path(__file__).resolve().parent.parent / "orchestrator" / "replays"


def _list_replays(only: Optional[List[str]] = None) -> List[Path]:
    files = sorted(_replay_dir().glob("*.replay.json"))
    if only:
        wanted = set(only)
        files = [p for p in files if p.stem.split(".")[0] in wanted]
    return files


def _run_one(path: Path) -> Dict[str, Any]:
    """Run one replay through the orchestrator and validate the trace."""
    # Lazy imports: pulling these at module load would force the whole
    # agents/orchestrator stack onto the path before argparse runs.
    from aura.agents.calendar.agent import CalendarAgent  # type: ignore
    from aura.agents.comms.agent import CommsAgent  # type: ignore
    from aura.agents.finance.agent import FinanceAgent  # type: ignore
    from aura.agents.wellness.agent import WellnessAgent  # type: ignore
    from aura.agents.core.types import UserState, WellnessState  # type: ignore
    from aura.orchestrator.graph import Orchestrator  # type: ignore
    from aura.orchestrator.trace import validate_trace  # type: ignore

    fixture = json.loads(path.read_text())
    user_state_dict = fixture["user_state"]
    user_state = UserState(
        load_score=int(user_state_dict.get("load_score", 0)),
        wellness_state=WellnessState(user_state_dict.get("wellness_state", "BASELINE")),
        in_focus_block=bool(user_state_dict.get("in_focus_block", False)),
        dnd_active=bool(user_state_dict.get("dnd_active", False)),
        open_app=user_state_dict.get("open_app", ""),
        local_time=user_state_dict.get("local_time", fixture["tick_ts"]),
        surfaces_today=int(user_state_dict.get("surfaces_today", 0)),
    )

    orch = Orchestrator(
        agents=[CommsAgent(), CalendarAgent(), FinanceAgent(), WellnessAgent()],
    )

    rec: Dict[str, Any] = {"replay": path.stem}
    try:
        result = orch.tick(
            user_state=user_state,
            agent_payloads=fixture["agent_payloads"],
            tick_ts=fixture["tick_ts"],
        )
    except Exception as exc:
        rec["error"] = f"tick failed: {type(exc).__name__}: {exc}"
        return rec

    rec["chosen_kind"] = getattr(result, "chosen_kind", None)
    rec["rationale"] = getattr(result.trace, "rationale", "")
    try:
        validate_trace(result.trace)
        rec["schema_valid"] = True
    except Exception as exc:
        rec["schema_valid"] = False
        rec["schema_error"] = f"{type(exc).__name__}: {exc}"
    return rec


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="LLM-in-the-loop schema validity.")
    parser.add_argument(
        "--replays",
        nargs="*",
        default=None,
        help="Subset of replay names (without extension).",
    )
    parser.add_argument(
        "--out",
        default=None,
        help="Output JSON path (default: benchmarks/results/llm_quality_<DATE>.json).",
    )
    args = parser.parse_args(argv)

    # Force LLM-on for this benchmark; the agents' artefact gate still
    # decides whether MLX actually gets called. If the artefact is
    # missing we still validate the deterministic fallback path.
    os.environ["AURA_USE_LLM"] = "1"

    files = _list_replays(args.replays)
    if not files:
        print("[quality] no replays found")
        return 1

    results: List[Dict[str, Any]] = []
    for p in files:
        print(f"[quality] {p.name} ...", flush=True)
        rec = _run_one(p)
        results.append(rec)
        if rec.get("schema_valid"):
            print("[quality]   schema valid")
        else:
            print(f"[quality]   schema FAIL: {rec.get('schema_error', rec.get('error'))}")

    valid = sum(1 for r in results if r.get("schema_valid"))
    pct = 100.0 * valid / len(results)

    out_path = Path(
        args.out
        or Path(__file__).resolve().parent
        / "results"
        / f"llm_quality_{date.today().isoformat()}.json"
    )
    out_path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "date": date.today().isoformat(),
        "replays_checked": len(results),
        "schema_valid": valid,
        "schema_valid_pct": pct,
        "results": results,
    }
    out_path.write_text(json.dumps(payload, indent=2))
    print(f"[quality] {valid}/{len(results)} valid ({pct:.1f}%) -> {out_path}")
    return 0 if valid == len(results) else 2


if __name__ == "__main__":
    raise SystemExit(main())
