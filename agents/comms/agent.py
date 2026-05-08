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
import os
import re
import time
import uuid
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple

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

# Hybrid classifier: regex fast-path + sklearn LR head trained on the
# 500-row synthetic dataset. Pickled artefact lives at
# models/exports/comms_classifier.pkl.
from .classifier import (
    EXPORT_PATH as _CLASSIFIER_EXPORT_PATH,
    diagnostic_accuracy as _classifier_diagnostic,
    predict_label as _hybrid_predict,
    regex_fast_path as _regex_fast_path,
    train_and_export as _train_classifier,
)


# ---------------------------------------------------------------------------
# Optional on-device LLM re-ranker (Gemma 2B 4-bit via MLX or llama.cpp).
#
# Activated when BOTH:
#   1. AURA_USE_LLM=1 in the environment.
#   2. The trained classifier artefact at
#      models/exports/comms_classifier.pkl exists.
#
# When the local heuristic / classifier returns top-1 prob < 0.7 we route
# the message through Gemma 2B for a one-token re-rank. If MLX is missing
# (or any error), we fall back to the heuristic answer silently.
# ---------------------------------------------------------------------------


_LLM_INTENT_LABELS = {"ACTIONABLE", "SOCIAL", "BROADCAST", "SPAM"}
_RERANK_THRESHOLD = 0.7
_MAX_LLM_PREVIEW_CHARS = 240  # cap to avoid blowing past Gemma's context

_llm_adapter = None
_llm_attempted = False


def _classifier_artefact_path() -> Path:
    return (
        Path(__file__).resolve().parents[2]
        / "models"
        / "exports"
        / "comms_classifier.pkl"
    )


def _llm_enabled() -> bool:
    if os.environ.get("AURA_USE_LLM", "0") != "1":
        return False
    return _classifier_artefact_path().exists()


def _get_llm_adapter():
    """Lazy, cached. Returns None if MLX / llama.cpp unavailable."""
    global _llm_adapter, _llm_attempted
    if _llm_adapter is not None or _llm_attempted:
        return _llm_adapter
    _llm_attempted = True
    try:
        from models.llm import get_adapter

        _llm_adapter = get_adapter("gemma-2b-4bit")
    except Exception:
        _llm_adapter = None
    return _llm_adapter


def _llm_rerank(text: str, scores: Dict[str, float]) -> Optional[str]:
    """Ask Gemma 2B for a single-word intent label.

    Returns one of ACTIONABLE / SOCIAL / BROADCAST / SPAM, or ``None``
    if the LLM is unavailable or the response cannot be parsed.
    """
    if not text:
        return None
    adapter = _get_llm_adapter()
    if adapter is None:
        return None
    try:
        from models.llm.prompts import comms_rerank_prompt

        prompt = comms_rerank_prompt(text[:_MAX_LLM_PREVIEW_CHARS], scores)
        # We only need the first whitespace-bounded word.
        out = adapter.generate(
            prompt,
            max_tokens=8,
            temperature=0.0,
            stop=("\n", "<end_of_turn>"),
        )
    except Exception:
        return None
    if not out:
        return None
    token = out.strip().split()[0].upper().strip(".,:;\"' ")
    return token if token in _LLM_INTENT_LABELS else None

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


def _classify_text(text: str) -> Dict[str, Any]:
    """Hybrid classifier (regex fast-path + sklearn LR head).

    Returns the legacy contract used by :class:`CommsAgent`::

        {
            "intent":        "ACTIONABLE" | "SOCIAL" | "BROADCAST" | "SPAM",
            "urgency":       0.0..1.0,
            "self_relevance": 0.0..1.0,
            "model_low_conf": bool,
            "source":        "fast-path" | "model",
        }

    The hybrid pipeline lives in :mod:`agents.comms.classifier`. See its
    docstring for the training story; this function just adapts its output
    to the dict shape :class:`CommsAgent` expects.
    """
    text = text or ""
    label, confidence, source = _hybrid_predict(text)

    mentioned = bool(_MENTION_TOKENS.search(text))
    actionable_hits = len(_ACTIONABLE_TOKENS.findall(text))

    # Urgency: derived from the model's own confidence in ACTIONABLE plus
    # a kick from explicit @you mentions and per-word verb density.
    if label == "ACTIONABLE":
        density = actionable_hits / max(1, len(text.split()) / 4)
        urgency = max(0.0, min(1.0, 0.55 + 0.25 * density + (0.2 if mentioned else 0.0)))
    elif label == "BROADCAST":
        urgency = 0.2
    elif label == "SPAM":
        urgency = 0.05
    else:  # SOCIAL
        urgency = 0.2

    self_relevance = 0.95 if mentioned else (0.7 if label == "ACTIONABLE" else 0.2)

    return {
        "intent": label,
        "urgency": urgency,
        "self_relevance": self_relevance,
        "model_low_conf": confidence < 0.6,
        "source": source,
        "confidence": confidence,
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
                summary = self.batch_summarize(items)
                return self._ok(call, summary, t0)

            if call.tool == "snooze":
                return self._ok(
                    call,
                    {"acked": True, "item_id": call.args["item_id"], "ttl": call.args["ttl_seconds"]},
                    t0,
                )

            if call.tool == "triage_inbox":
                scope = call.args.get("scope", "unread_24h")
                return self._ok(call, self.triage_inbox(scope=scope), t0)

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
    def _stub_draft(text: str, tone: str = "casual", sender_name: Optional[str] = None) -> str:
        """Backwards-compatible draft helper.

        Delegates to :meth:`_template_draft` so existing call-sites keep
        working. Phase-2 swap-in for Gemma 2B LoRA goes through
        :meth:`_lora_draft`.
        """
        return CommsAgent._template_draft(text, tone=tone, sender_name=sender_name)

    @staticmethod
    def _template_draft(
        text: str, tone: str = "casual", sender_name: Optional[str] = None
    ) -> str:
        """Deterministic 1-2 sentence reply with sender name + intent.

        The drafter inspects the message for an action verb (push, submit,
        confirm, review, etc.) and the sender name (extracted by
        :meth:`_extract_sender` or supplied by the caller). The output is
        always 1-2 sentences and always polite.
        """
        text = (text or "").strip()
        name = sender_name or CommsAgent._extract_sender(text) or ""
        intent_verb = CommsAgent._infer_intent_verb(text)
        opener = "Hi " + name + "," if name else "Hi,"

        if tone == "formal":
            body = f"Acknowledged — will {intent_verb} and revert by EOD."
        elif tone == "brief":
            body = "On it."
        else:
            body = f"On it — will {intent_verb} and ping you shortly. Thanks!"
        # 1-sentence "brief" tone keeps it terse.
        if tone == "brief":
            return body
        return f"{opener} {body}"

    @staticmethod
    def _lora_draft(text: str, tone: str = "casual") -> Optional[str]:
        """Phase-2 integration point for the Gemma 2B + LoRA reply head.

        The plan in ``models/lora/configs/comms_lora.yaml`` is to fine-tune
        the same 500-row dataset (``draft`` field) with a chat-formatted
        prompt template and load the merged adapter via MLX (iOS dev) or
        MediaPipe LLM Inference (Android). When that lands, swap the body
        of this function to call ``adapter.generate(...)`` and the rest of
        the agent will pick up the higher-quality drafts automatically.
        """
        return None  # Phase-1: never used; Phase-2: real call.

    @staticmethod
    def _extract_sender(text: str) -> Optional[str]:
        """Heuristically pull the sender name from the text.

        Two common shapes:
          - ``surface | NAME | body``  (NAME alphabetic)
          - ``surface | group:... | NAME: body``
        Returns ``None`` if no name token is present.
        """
        if "|" in text:
            parts = [p.strip() for p in text.split("|")]
            # Format: surface | sender | body
            if len(parts) >= 3:
                cand = parts[1]
                if cand and cand[0].isalpha() and not cand.startswith("group:"):
                    return cand.split()[0]
        # Format: NAME: rest
        m = re.match(r"^([A-Z][a-z]{1,15})\s*:", text)
        if m:
            return m.group(1)
        return None

    @staticmethod
    def _infer_intent_verb(text: str) -> str:
        """Pull a single verb describing the action requested."""
        verbs = [
            ("push", "push the merge"),
            ("merge", "push the merge"),
            ("review", "review"),
            ("submit", "submit it"),
            ("confirm", "confirm"),
            ("share", "share it"),
            ("send", "send it"),
            ("approve", "approve"),
            ("sign-off", "sign off"),
            ("reply", "reply"),
            ("pay", "pay it"),
            ("rsvp", "RSVP"),
            ("attend", "attend"),
        ]
        low = text.lower()
        for needle, action in verbs:
            if needle in low:
                return action
        return "follow up"

    # ---------- larger public API (used by orchestrator + tests) ----------

    def batch_summarize(self, items: Iterable[Dict[str, Any]]) -> Dict[str, Any]:
        """Take ``N`` notification events, classify them, return:

        - ``actionable``: the top 3 items (by urgency) with their drafts
        - ``muted_count``: ``N - len(actionable)``
        - ``digest``: a 1-line summary of the muted topics

        The signature accepts any iterable of notification-shaped dicts
        (with at least a ``preview`` field).
        """
        items = list(items)
        scored: List[Tuple[Dict[str, Any], Dict[str, Any]]] = []
        for it in items:
            text = it.get("preview", "") or it.get("intent_hint", "") or ""
            scored.append((it, _classify_text(text)))

        actionable = [(it, cls) for it, cls in scored if cls["intent"] == "ACTIONABLE"]
        actionable.sort(key=lambda pair: pair[1]["urgency"], reverse=True)
        top3 = actionable[:3]
        actionable_payload = [
            {
                "item_id": it.get("id"),
                "draft": self._template_draft(
                    it.get("preview", ""),
                    sender_name=it.get("sender_hash", "").replace("h_", "").title() or None,
                ),
                "urgency": round(cls["urgency"], 3),
            }
            for it, cls in top3
        ]

        muted = [pair for pair in scored if pair not in top3]
        muted_topics = self._summarise_muted([m[0] for m in muted])

        return {
            "actionable": actionable_payload,
            "muted_count": len(items) - len(top3),
            "digest": muted_topics,
            "total": len(items),
        }

    def triage_inbox(
        self,
        scope: str = "unread_24h",
        notif_events: Optional[List[Dict[str, Any]]] = None,
        gmail_threads: Optional[List[Dict[str, Any]]] = None,
    ) -> Dict[str, Any]:
        """Triage scope and return the AgentOutput-payload shape.

        Returns the four contract keys ``urgent``, ``drafts``,
        ``muted_count``, ``top_suggested_action`` exactly as defined by
        the ``AgentOutput`` schema (``agents/core/types.py``). When
        ``notif_events`` / ``gmail_threads`` are not supplied this falls
        back to an empty inbox view.
        """
        notif_events = notif_events or []
        gmail_threads = gmail_threads or []
        urgent: List[Dict[str, Any]] = []
        drafts: List[Dict[str, Any]] = []
        muted = 0
        for ev in notif_events:
            text = ev.get("preview", "") or ev.get("intent_hint", "") or ""
            cls = _classify_text(text)
            if cls["intent"] == "ACTIONABLE":
                urgent.append({
                    "item_id": ev.get("id"),
                    "reason_code": "self_mention" if cls["self_relevance"] > 0.9 else "actionable",
                    "score": round(cls["urgency"], 3),
                })
                drafts.append({
                    "item_id": ev.get("id"),
                    "draft_text": self._template_draft(
                        text,
                        sender_name=ev.get("sender_hash", "").replace("h_", "").title() or None,
                    ),
                    "tone": "casual",
                    "confidence": round(cls.get("confidence", 0.7), 3),
                })
            else:
                muted += 1

        if any(t.get("subject_class") == "prof" for t in gmail_threads):
            top = "SHOW_BRIEF"
        elif urgent and len(notif_events) >= 30:
            top = "BATCH_DIGEST"
        elif urgent:
            top = "SHOW_BRIEF"
        else:
            top = "DO_NOTHING"

        return {
            "scope": scope,
            "urgent": urgent,
            "drafts": drafts,
            "muted_count": muted,
            "top_suggested_action": top,
        }

    @staticmethod
    def _summarise_muted(items: List[Dict[str, Any]]) -> str:
        """Cheap topic summary: count distinct channels / app_pkgs."""
        if not items:
            return "no muted messages"
        channels: Dict[str, int] = {}
        for it in items:
            ch = it.get("channel") or it.get("app_pkg") or "?"
            channels[ch] = channels.get(ch, 0) + 1
        top = sorted(channels.items(), key=lambda kv: -kv[1])[:3]
        parts = [f"{n} from {c}" for c, n in top]
        return ", ".join(parts) + f"; {len(items)} muted total"

    # ---------- diagnostics ----------

    def diagnostic_accuracy(self) -> Dict[str, Any]:
        """Held-out 20% macro-F1 of the hybrid pipeline. Used by tests."""
        if not _CLASSIFIER_EXPORT_PATH.exists():
            _train_classifier()
        return _classifier_diagnostic()


def make_call_id() -> str:
    """Helper for tests; matches `^t_[a-z0-9]{10}$`."""

    return "t_" + uuid.uuid4().hex[:10]
