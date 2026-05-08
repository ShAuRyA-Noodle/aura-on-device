"""Reasoning Trace emission, validation, and pretty rendering.

Implements technical_spec.md §4.6 + §5.

Schema is taken verbatim from spec §4.6 (`trace.v1.json`). The Pydantic
``Trace`` model in ``agents.core.types`` is the in-memory shape; this module
mirrors the JSON Schema and provides a ``jsonschema``-based validator so the
team's CI can fail loudly on any drift.
"""

from __future__ import annotations

import hashlib
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from jsonschema import Draft202012Validator, ValidationError

from agents.core.types import (
    Action,
    Candidate,
    Outcome,
    Trace,
    TraceCandidate,
    UserState,
)


TRACE_V1_SCHEMA: Dict[str, Any] = {
    "$id": "https://aura.local/schemas/trace.v1.json",
    "type": "object",
    "required": ["trace_id", "ts", "trigger", "signals", "candidates", "chosen", "rationale", "confirm_required", "outcome"],
    "properties": {
        "trace_id": {"type": "string", "pattern": "^tr_[a-z0-9]{12}$"},
        "ts": {"type": "string"},
        "trigger": {
            "type": "object",
            "required": ["source", "value"],
            "properties": {"source": {"type": "string"}, "value": {}},
        },
        "signals": {"type": "array", "items": {"type": "object"}},
        "candidates": {
            "type": "array",
            "items": {
                "type": "object",
                "required": ["kind", "score", "confirm_required"],
                "properties": {
                    "kind": {"type": "string"},
                    "score": {"type": "number"},
                    "components": {"type": "object"},
                    "confirm_required": {"type": "boolean"},
                },
            },
        },
        "chosen": {"type": "string"},
        "rationale": {"type": "string", "maxLength": 500},
        "rationale_source": {"enum": ["template", "llm"]},
        "confirm_required": {"type": "boolean"},
        "outcome": {"enum": ["pending", "confirmed", "dismissed", "timed_out", "executed_auto", "failed"]},
        "redactions": {"type": "array", "items": {"type": "string"}},
    },
    "additionalProperties": False,
}


_VALIDATOR = Draft202012Validator(TRACE_V1_SCHEMA)


def make_trace_id() -> str:
    """Return a `tr_<12 hex>` identifier matching the spec pattern."""
    return "tr_" + uuid.uuid4().hex[:12]


def emit_trace(
    *,
    trigger: Dict[str, Any],
    signals: List[Dict[str, Any]],
    scored: List,  # List[Tuple[Candidate, float, Dict[str, float]]]
    chosen_action: Optional[Action],
    rationale: str,
    rationale_source: str = "template",
    redactions: Optional[List[str]] = None,
    ts: Optional[datetime] = None,
    cap_reason: Optional[str] = None,
) -> Trace:
    """Build a Trace from the orchestrator's decision artefacts."""
    ts = ts or datetime.now(timezone.utc)
    trace_candidates: List[TraceCandidate] = []
    for c, score, comps in scored:
        trace_candidates.append(
            TraceCandidate(
                kind=c.kind,
                score=round(score, 3),
                components=comps,
                confirm_required=c.confirm_required,
            )
        )
    if chosen_action is not None:
        chosen = chosen_action.kind
        outcome = Outcome.PENDING if chosen_action.confirm_required else Outcome.EXECUTED_AUTO
        confirm_required = chosen_action.confirm_required
    else:
        chosen = "do_nothing"
        outcome = Outcome.PENDING
        confirm_required = False
        if cap_reason and not rationale:
            rationale = f"blocked by {cap_reason}"

    return Trace(
        trace_id=make_trace_id(),
        ts=ts.isoformat(),
        trigger=trigger,
        signals=signals,
        candidates=trace_candidates,
        chosen=chosen,
        rationale=rationale[:500],
        rationale_source=rationale_source,  # type: ignore[arg-type]
        confirm_required=confirm_required,
        outcome=outcome,
        redactions=redactions or [],
    )


def validate_trace(trace: Trace) -> None:
    """Validate against `trace.v1.json`. Raises ``jsonschema.ValidationError``."""
    payload = trace.model_dump(mode="json")
    _VALIDATOR.validate(payload)


def pretty_render_html(trace: Trace, *, embed_css: bool = True) -> str:
    """HTML rendering for the iOS Memory tab + HF Space.

    Mirrors the four-section layout from spec §5.3. The iOS WebView and the
    HF Space Gradio HTML component both feed this string verbatim. Pair with
    ``trace.css`` for the locked palette (deck slide 8a).
    """
    import html

    css_link = (
        "<style>" + _read_trace_css() + "</style>"
        if embed_css
        else '<link rel="stylesheet" href="trace.css" />'
    )

    def esc(v: Any) -> str:
        return html.escape(str(v))

    # Section 1 — trigger.
    trig_src = esc(trace.trigger.get("source", "?"))
    trig_val = esc(trace.trigger.get("value", ""))

    # Section 2 — signals: 3-column key/value table per agent.
    signal_rows = []
    for s in trace.signals:
        agent = esc(s.get("agent", "?"))
        decision = esc(s.get("decision", ""))
        drivers_html = ", ".join(esc(d) for d in s.get("drivers", []))
        slow_badge = (
            '<span class="aura-badge aura-badge--warn">slow</span>'
            if s.get("slow")
            else ""
        )
        signal_rows.append(
            f"<tr><td class='aura-key'>{agent}</td>"
            f"<td>{decision}{slow_badge}</td>"
            f"<td class='aura-drivers'>{drivers_html}</td></tr>"
        )

    # Section 3 — candidates: ranked, score breakdown.
    cand_rows = []
    for c in trace.candidates:
        comp = c.components or {}
        comp_html = " &middot; ".join(
            f'<span class="aura-comp">{esc(k)}={esc(v)}</span>' for k, v in comp.items()
        )
        confirm_badge = (
            '<span class="aura-badge aura-badge--confirm">confirm</span>'
            if c.confirm_required
            else '<span class="aura-badge aura-badge--auto">auto</span>'
        )
        cand_rows.append(
            f"<tr><td class='aura-kind'>{esc(c.kind)}</td>"
            f"<td class='aura-score'>{c.score:+.3f}</td>"
            f"<td>{comp_html}</td>"
            f"<td>{confirm_badge}</td></tr>"
        )

    # Section 4 — chosen + rationale.
    rationale = esc(trace.rationale or "")
    chosen = esc(trace.chosen)
    outcome = esc(trace.outcome.value if hasattr(trace.outcome, "value") else trace.outcome)
    confirm_badge = (
        '<span class="aura-badge aura-badge--confirm">confirm required</span>'
        if trace.confirm_required
        else '<span class="aura-badge aura-badge--auto">auto-execute</span>'
    )
    redactions_html = (
        f"<p class='aura-redactions'>Redacted: {esc(', '.join(trace.redactions))}</p>"
        if trace.redactions
        else ""
    )

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8" />
<title>Aura Reasoning Trace {esc(trace.trace_id)}</title>
{css_link}
</head>
<body class="aura-trace">
<header class="aura-header">
  <span class="aura-trace-id">{esc(trace.trace_id)}</span>
  <span class="aura-ts">{esc(trace.ts)}</span>
</header>

<section class="aura-section aura-section--why">
  <h2>Why now</h2>
  <p><span class="aura-key">{trig_src}</span> &middot; <span class="aura-val">{trig_val}</span></p>
</section>

<section class="aura-section aura-section--saw">
  <h2>What I saw</h2>
  <table class="aura-table">
    <thead><tr><th>Agent</th><th>Decision</th><th>Drivers</th></tr></thead>
    <tbody>
      {''.join(signal_rows) or '<tr><td colspan="3"><em>(no signals)</em></td></tr>'}
    </tbody>
  </table>
</section>

<section class="aura-section aura-section--considered">
  <h2>What I considered</h2>
  <table class="aura-table">
    <thead><tr><th>Kind</th><th>Score</th><th>Components</th><th>Surface</th></tr></thead>
    <tbody>
      {''.join(cand_rows) or '<tr><td colspan="4"><em>(no candidates)</em></td></tr>'}
    </tbody>
  </table>
</section>

<section class="aura-section aura-section--chose">
  <h2>What I chose</h2>
  <p class="aura-chosen">
    <span class="aura-kind aura-kind--chosen">{chosen}</span>
    {confirm_badge}
    <span class="aura-outcome">{outcome}</span>
  </p>
  <p class="aura-rationale">{rationale}</p>
  {redactions_html}
</section>
</body>
</html>"""


def _read_trace_css() -> str:
    """Read the locked-palette CSS that pairs with the HTML render."""
    from pathlib import Path

    css_path = Path(__file__).resolve().parent / "trace.css"
    if css_path.exists():
        return css_path.read_text()
    return ""


def pretty_render(trace: Trace) -> str:
    """Human-readable rendering for the Reasoning Trace drawer + CLI debug.

    Mirrors UI rendering rules in spec §5.3:
    1. Why now -> trigger
    2. What I saw -> signals
    3. What I considered -> candidates
    4. What I chose and why -> chosen + rationale
    """
    lines: List[str] = []
    lines.append(f"Trace {trace.trace_id} @ {trace.ts}")
    lines.append("Why now:")
    src = trace.trigger.get("source", "?")
    val = trace.trigger.get("value", "")
    lines.append(f"  {src} = {val}")
    lines.append("What I saw:")
    for s in trace.signals:
        for k, v in s.items():
            lines.append(f"  {k}: {v}")
    lines.append("What I considered:")
    for c in trace.candidates:
        comp = ", ".join(f"{k}={v}" for k, v in c.components.items())
        lines.append(f"  {c.kind:18s} score={c.score:+.3f}  ({comp})  confirm={c.confirm_required}")
    lines.append(f"Chosen: {trace.chosen}")
    if trace.rationale:
        lines.append(f"Why: {trace.rationale}")
    lines.append(f"Outcome: {trace.outcome.value}  confirm_required={trace.confirm_required}")
    if trace.redactions:
        lines.append(f"Redacted: {', '.join(trace.redactions)}")
    return "\n".join(lines)


def trace_canonical_hash(trace: Trace) -> str:
    """Deterministic SHA-256 over canonical JSON for the audit chain."""
    payload = trace.model_dump(mode="json")
    canonical = _canonical_json(payload)
    return hashlib.sha256(canonical.encode()).hexdigest()


def _canonical_json(value: Any) -> str:
    """Sort keys, no whitespace, ascii-safe."""
    import json

    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
