"""CommsAgent — notification triage and reply drafting (technical_spec.md §3.1).

The production agent is a Gemma 2B Q4 + LoRA model running via MediaPipe LLM
Inference (Android) or MLX (iOS dev). For the Python reference build, we use
a regex / heuristic classifier good enough for unit tests, and we mark every
spot where the LLM would slot in.

Privacy invariant (plan §10.1, spec §3.1): we never persist message bodies.
We only read `intent_hint` (already pre-extracted by the caller) and a
`preview_redacted` flag — actual text never leaves the caller. Internally we
allow a `preview` field on test fixtures for classifier evaluation, but the
agent itself logs only `sender_hash`, `intent_label`, `urgency_score`, `ts`.
"""

from __future__ import annotations

import hashlib
import re
import time
import uuid
from typing import Any, Dict, List, Optional

from agents.core.agent_base import Agent
from agents.core.types import (
    AgentInput,
    AgentName,
    AgentOutput,
    Candidate,
    Surface,
    ToolCall,
    ToolResult,
    TraceFragment,
)

# ---------------------------------------------------------------------------
# Heuristic classifier
# ---------------------------------------------------------------------------

_ACTIONABLE_TOKENS = re.compile(
    r"\b(deadline|due|tomorrow|tonight|asap|urgent|please|"
    r"can you|need|help|update|merge|push|deploy|fix|"
    r"submit|sent|share|reply|confirm|reschedule|attach|"
    r"meeting|quiz|review|sign-?off)\b",
    re.IGNORECASE,
)

_SOCIAL_TOKENS = re.compile(
    r"\b(lol|haha|lmao|gn|gm|brb|nice|cool|ok|okay|"
    r"thanks|thx|ty|np|same|fr|true|bruh|guys|"
    r":\)|:\(|<3|\bxd\b|\bbtw\b|\bidk\b|\btbh\b|\bngl\b)\b",
    re.IGNORECASE,
)

_BROADCAST_TOKENS = re.compile(
    r"\b(announcement|notice|attention all|everyone|"
    r"placement|alert|reminder for all)\b",
    re.IGNORECASE,
)

_SPAM_TOKENS = re.compile(
    r"\b(promo|coupon|offer|cashback|discount|"
    r"flash sale|loan|emi|win|congratulations you)\b",
    re.IGNORECASE,
)

_MENTION_TOKENS = re.compile(r"@you\b|@me\b", re.IGNORECASE)


def _classify_text(text: str) -> Dict[str, float]:
    """Reference heuristic classifier.

    [TEAM TO VERIFY] swap this for `gemma_lora.predict(text)` once the LoRA
    adapter is converted to GGUF / MLX.
    """

    actionable_hits = len(_ACTIONABLE_TOKENS.findall(text))
    social_hits = len(_SOCIAL_TOKENS.findall(text))
    broadcast_hits = len(_BROADCAST_TOKENS.findall(text))
    spam_hits = len(_SPAM_TOKENS.findall(text))
    mentioned = bool(_MENTION_TOKENS.search(text))

    # Pick highest-scoring class; fall back to SOCIAL.
    scores = {
        "ACTIONABLE": actionable_hits + (2 if mentioned else 0),
        "SOCIAL": social_hits,
        "BROADCAST": broadcast_hits,
        "SPAM": spam_hits,
    }
    intent = max(scores, key=lambda k: scores[k])
    if scores[intent] == 0:
        intent = "SOCIAL"  # default for short conversational chatter

    # Urgency 0..1 — actionable text gets a boost, mention pushes higher.
    raw = scores["ACTIONABLE"] / max(1, len(text.split()) / 4)
    urgency = max(0.0, min(1.0, raw + (0.3 if mentioned else 0.0)))

    self_relevance = 0.95 if mentioned else (0.7 if intent == "ACTIONABLE" else 0.2)

    return {
        "intent": intent,
        "urgency": urgency,
        "self_relevance": self_relevance,
        "model_low_conf": float(scores[intent]) < 1.0,
    }


def _hash_sender(s: str) -> str:
    """Deterministic short hash so the trace can refer to a sender without PII."""

    h = hashlib.sha256(s.encode("utf-8")).hexdigest()[:8]
    return f"h_{h}"


# ---------------------------------------------------------------------------
# Agent
# ---------------------------------------------------------------------------


class CommsAgent(Agent):
    name = AgentName.COMMS
    latency_budget_ms = 300

    # Tool names exposed to the orchestrator.
    TOOLS = (
        "classify",
        "draft_reply",
        "batch_summarize",
        "snooze",
        "triage_inbox",
    )

    # ---------- core public API ----------

    def tick(self, input: AgentInput) -> AgentOutput:
        notif_events: List[Dict[str, Any]] = list(input.payload.get("notif_events", []))
        gmail_threads: List[Dict[str, Any]] = list(input.payload.get("gmail_threads", []))

        # Classify everything.
        classifications: List[Dict[str, Any]] = []
        any_low_conf = False
        for ev in notif_events:
            text = ev.get("preview", "") or ev.get("intent_hint", "") or ""
            cls = _classify_text(text)
            classifications.append({"id": ev["id"], **cls})
            any_low_conf = any_low_conf or cls["model_low_conf"]

        urgent = [
            {"item_id": c["id"], "reason_code": "self_mention" if c["self_relevance"] > 0.9 else "actionable", "score": round(c["urgency"], 3)}
            for c in classifications
            if c["intent"] == "ACTIONABLE"
        ]
        muted = [c["id"] for c in classifications if c["intent"] in ("SOCIAL", "SPAM", "BROADCAST")]

        drafts: List[Dict[str, Any]] = []
        for u in urgent:
            ev = next(e for e in notif_events if e["id"] == u["item_id"])
            text = ev.get("preview", "")
            drafts.append({
                "item_id": u["item_id"],
                "draft_text": self._stub_draft(text),
                "tone": "casual",
                "confidence": 0.71,
            })

        # Decide top suggested action.
        burst = len(notif_events) >= 30
        if burst and len(urgent) >= 1:
            top_action = "BATCH_DIGEST"
        elif gmail_threads and any(t.get("subject_class") == "prof" for t in gmail_threads):
            top_action = "SHOW_BRIEF"
        elif len(urgent) >= 1:
            top_action = "SHOW_BRIEF"
        else:
            top_action = "DO_NOTHING"

        candidates: List[Candidate] = []
        if top_action == "BATCH_DIGEST":
            candidates.append(
                Candidate(
                    kind="BATCH_DIGEST",
                    agent=self.name,
                    confidence=0.78,
                    agent_priority=0.7,
                    confirm_required=False,
                    surface=Surface.PHONE_CARD,
                    args={"item_count": len(notif_events), "actionable_count": len(urgent)},
                    rationale_seed=f"{len(notif_events)} messages, {len(urgent)} actionable",
                )
            )
        elif top_action == "SHOW_BRIEF":
            candidates.append(
                Candidate(
                    kind="SHOW_BRIEF",
                    agent=self.name,
                    confidence=0.7,
                    agent_priority=0.7,
                    confirm_required=False,
                    surface=Surface.PHONE_CARD,
                    args={"urgent": len(urgent), "muted": len(muted)},
                    rationale_seed="prof email" if any(t.get("subject_class") == "prof" for t in gmail_threads) else "actionable items",
                )
            )

        # If volume is heavy, also propose the safety candidate MUTE_GROUP_30.
        # That keeps the orchestrator's ranker honest in stress conditions.
        if burst and input.user_state.load_score >= 70:
            channel = notif_events[0].get("channel") if notif_events else None
            candidates.append(
                Candidate(
                    kind="MUTE_GROUP_30",
                    agent=self.name,
                    confidence=0.6,
                    agent_priority=0.7,
                    confirm_required=True,
                    surface=Surface.WATCH,
                    args={"target_channel": channel, "ttl_seconds": 1800},
                    rationale_seed=f"{len(notif_events)} messages while load_score={input.user_state.load_score}",
                )
            )

        payload = {
            "urgent": urgent,
            "drafts": drafts,
            "muted_count": len(muted),
            "top_suggested_action": top_action,
        }

        frag = TraceFragment(
            agent=self.name,
            inputs_summary={
                "notif_count": len(notif_events),
                "gmail_count": len(gmail_threads),
            },
            decision=top_action.lower(),
            drivers=[
                f"volume_{len(notif_events)}",
                f"actionable_{len(urgent)}",
                f"load_score_{input.user_state.load_score}",
            ],
            model_low_conf=any_low_conf,
        )

        return AgentOutput(
            agent=self.name,
            tick_ts=input.tick_ts,
            candidates=candidates,
            payload=payload,
            trace_fragment=frag,
        )

    def tools(self) -> List[Dict[str, Any]]:
        notif_event_schema = {
            "type": "object",
            "required": ["id", "app_pkg", "ts"],
            "properties": {
                "id": {"type": "string"},
                "app_pkg": {"type": "string"},
                "channel": {"type": "string"},
                "sender_hash": {"type": "string"},
                "preview_redacted": {"type": "boolean"},
                "intent_hint": {"type": ["string", "null"]},
                "ts": {"type": "string", "format": "date-time"},
            },
        }
        return [
            {
                "name": "classify",
                "description": "Classify a notification's intent and urgency.",
                "parameters": {
                    "type": "object",
                    "required": ["item"],
                    "properties": {"item": notif_event_schema},
                },
            },
            {
                "name": "draft_reply",
                "description": "Draft a short reply for an actionable notification.",
                "parameters": {
                    "type": "object",
                    "required": ["item", "tone"],
                    "properties": {
                        "item": notif_event_schema,
                        "tone": {"enum": ["casual", "formal", "brief"]},
                        "length_max": {"type": "integer", "minimum": 1, "maximum": 280},
                    },
                },
            },
            {
                "name": "batch_summarize",
                "description": "One-line digest over many notifications.",
                "parameters": {
                    "type": "object",
                    "required": ["items"],
                    "properties": {"items": {"type": "array", "items": notif_event_schema}},
                },
            },
            {
                "name": "snooze",
                "description": "Suppress a notification for a window.",
                "parameters": {
                    "type": "object",
                    "required": ["item_id", "ttl_seconds"],
                    "properties": {
                        "item_id": {"type": "string"},
                        "ttl_seconds": {"type": "integer", "minimum": 60, "maximum": 86400},
                    },
                },
            },
            {
                "name": "triage_inbox",
                "description": "Triage Gmail-style inbox by scope.",
                "parameters": {
                    "type": "object",
                    "required": ["scope"],
                    "properties": {"scope": {"enum": ["unread_24h", "all_today"]}},
                },
            },
        ]

    def handle_tool_call(self, call: ToolCall) -> ToolResult:
        t0 = time.perf_counter()
        try:
            if call.tool == "classify":
                item = call.args["item"]
                text = item.get("preview") or item.get("intent_hint") or ""
                result = _classify_text(text)
                return self._ok(call, result, t0)

            if call.tool == "draft_reply":
                item = call.args["item"]
                text = item.get("preview") or ""
                draft = self._stub_draft(text, tone=call.args.get("tone", "casual"))
                return self._ok(
                    call,
                    {"draft_text": draft, "tone": call.args.get("tone", "casual"), "confidence": 0.71},
                    t0,
                )

            if call.tool == "batch_summarize":
                items = call.args.get("items", [])
                people = sorted({_hash_sender(i.get("sender_hash") or i.get("id", "")) for i in items})
                return self._ok(
                    call,
                    {
                        "one_line": f"{len(items)} messages, {len(people)} people, batch suppressed.",
                        "action_count": 0,
                        "people": people[:5],
                    },
                    t0,
                )

            if call.tool == "snooze":
                return self._ok(
                    call,
                    {"acked": True, "item_id": call.args["item_id"], "ttl": call.args["ttl_seconds"]},
                    t0,
                )

            if call.tool == "triage_inbox":
                return self._ok(call, {"unread": 0, "ok": True}, t0)

            return ToolResult(call_id=call.call_id, ok=False, error=f"unknown tool: {call.tool}", latency_ms=(time.perf_counter() - t0) * 1000.0)

        except Exception as exc:  # pragma: no cover - defensive
            return ToolResult(
                call_id=call.call_id,
                ok=False,
                error=f"{type(exc).__name__}: {exc}",
                latency_ms=(time.perf_counter() - t0) * 1000.0,
            )

    # ---------- internals ----------

    def _ok(self, call: ToolCall, result: Dict[str, Any], t0: float) -> ToolResult:
        return ToolResult(
            call_id=call.call_id,
            ok=True,
            result=result,
            latency_ms=(time.perf_counter() - t0) * 1000.0,
        )

    @staticmethod
    def _stub_draft(text: str, tone: str = "casual") -> str:
        """Stub reply generator. [TEAM TO VERIFY] replace with Gemma 2B LoRA call.

        Production path::

            tokens = gemma.generate(
                prompt=DRAFT_PROMPT.format(text=text, tone=tone), max_tokens=40
            )

        For tests we return a short canned shape so unit tests are deterministic.
        """

        snippet = (text or "").strip().split(".")[0][:60]
        if not snippet:
            snippet = "got it"
        if tone == "formal":
            return f"Acknowledged — {snippet}."
        if tone == "brief":
            return "On it."
        return f"On it — {snippet}."


def make_call_id() -> str:
    """Helper for tests; matches `^t_[a-z0-9]{10}$`."""

    return "t_" + uuid.uuid4().hex[:10]
