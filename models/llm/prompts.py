"""Prompt templates shared between agents and the orchestrator.

Centralised so all on-device LLM calls have a single audited surface.
Each function returns a plain string ready to feed into
``LLMAdapter.generate`` or ``LLMAdapter.generate_stream``.
"""

from __future__ import annotations

import json
from typing import Any, Iterable, Mapping


# ---------------------------------------------------------------------------
# Comms — re-rank an ambiguous classification.
# ---------------------------------------------------------------------------


COMMS_RERANK_SYSTEM = (
    "You are Aura's CommsAgent. The local classifier was uncertain. "
    "Pick the single best intent among ACTIONABLE, SOCIAL, BROADCAST, SPAM "
    "for the message below. Reply with one word only — the chosen label."
)


def comms_rerank_prompt(
    message: str,
    candidate_scores: Mapping[str, float],
) -> str:
    score_lines = "\n".join(
        f"  {k}: {v:.2f}" for k, v in candidate_scores.items()
    )
    return (
        "<start_of_turn>system\n"
        + COMMS_RERANK_SYSTEM
        + "<end_of_turn>\n"
        + "<start_of_turn>user\n"
        + f"Message:\n{message}\n\n"
        + f"Local scores:\n{score_lines}\n\n"
        + "Best label?"
        + "<end_of_turn>\n"
        + "<start_of_turn>model\n"
    )


# ---------------------------------------------------------------------------
# Finance — structured extraction for unrecognised SMS.
# ---------------------------------------------------------------------------


FINANCE_EXTRACT_SYSTEM = (
    "You are Aura's FinanceAgent. Extract a single transaction from the "
    "Indian-bank SMS below. Output a JSON object with keys "
    "amount (number), currency (string, default INR), "
    "merchant (string, lowercased token), account_last4 (string of 4 digits "
    "or empty), direction (debit or credit). Output JSON only, no prose."
)


def finance_extract_prompt(sms_text: str) -> str:
    return (
        "<start_of_turn>system\n"
        + FINANCE_EXTRACT_SYSTEM
        + "<end_of_turn>\n"
        + "<start_of_turn>user\n"
        + sms_text.strip()
        + "<end_of_turn>\n"
        + "<start_of_turn>model\n"
    )


# ---------------------------------------------------------------------------
# Orchestrator — Reasoning Trace rationale.
# ---------------------------------------------------------------------------


RATIONALE_SYSTEM = (
    "You are Aura's orchestrator narrator. Write a single-sentence rationale "
    "of 30-50 words explaining why the chosen action fits the user state. "
    "Plain English. No emojis. No PII. Reference the agent decisions only."
)


def rationale_prompt(
    chosen_kind: str,
    signals: Iterable[Mapping[str, Any]],
    user_state: Mapping[str, Any] | None = None,
) -> str:
    signal_lines = []
    for s in signals:
        agent = s.get("agent", "?")
        decision = s.get("decision", "?")
        drivers = ", ".join(s.get("drivers", []) or [])
        signal_lines.append(f"- {agent}: {decision} ({drivers})")
    sig_block = "\n".join(signal_lines) if signal_lines else "(none)"

    state_summary = ""
    if user_state:
        try:
            state_summary = json.dumps({
                "load_score": user_state.get("load_score"),
                "wellness": user_state.get("wellness_state"),
                "in_focus": user_state.get("in_focus_block"),
            })
        except Exception:
            state_summary = ""

    return (
        "<start_of_turn>system\n"
        + RATIONALE_SYSTEM
        + "<end_of_turn>\n"
        + "<start_of_turn>user\n"
        + f"Chosen action: {chosen_kind}\n"
        + f"User state: {state_summary}\n"
        + f"Agent signals:\n{sig_block}\n"
        + "Write the one-sentence rationale now."
        + "<end_of_turn>\n"
        + "<start_of_turn>model\n"
    )


# ---------------------------------------------------------------------------
# JSON utilities used by agents to parse LLM output safely.
# ---------------------------------------------------------------------------


def safe_json_extract(text: str) -> dict[str, Any] | None:
    """Locate the first JSON object in ``text`` and parse it.

    LLMs often wrap output in markdown fences or trailing prose. We
    scan for the first ``{`` and the last ``}`` and try to parse that
    slice. Returns ``None`` if no valid object can be recovered.
    """
    if not text:
        return None
    start = text.find("{")
    end = text.rfind("}")
    if start < 0 or end <= start:
        return None
    slab = text[start : end + 1]
    try:
        obj = json.loads(slab)
        if isinstance(obj, dict):
            return obj
    except Exception:
        return None
    return None
