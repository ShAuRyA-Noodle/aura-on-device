"""Aura — HuggingFace Spaces interactive demo.

This Space runs the real Aura agent stack on whatever inputs the visitor
pastes. Every tab actually runs the same Python agent classes that ship in
the Aura mobile build (`aura/agents/...`) with no mocks. The classifier and
embedder fall back to lightweight regex / hash-bucket variants when the
trained models aren't available — that fallback is announced via a
"running in lite mode" badge.

Tabs (per Phase-3 brief):
1. Morning Brief Builder — HRV, sleep, calendar events, notifications -> brief card + Reasoning Trace.
2. Quiet Group Chat       — paste up to 200 messages, see triage + Silence Budget.
3. Spend Mirror           — paste 1-30 Indian bank SMS, get parsed table + projection.
4. Load Score Live        — five sliders -> real Load Score + driver bars + intervention.
5. Memory Graph Explorer  — add nodes, search, export JSON, view Merkle root.
6. Reasoning Trace Library — browse pre-recorded glass-box trace replays.

Visual lock: parchment #FAF8F5, ink #0E0E0E, accent #FF5B2E.
Typography: Fraunces (display) + Inter Tight (UI) via Google Fonts.
"""

from __future__ import annotations

import asyncio
import html
import json
import os
import re
import sys
import traceback
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# ---------------------------------------------------------------------------
# Import path bootstrap
# ---------------------------------------------------------------------------
# On HF Spaces the working directory ships with `agents/`, `orchestrator/`,
# and `memory/` as siblings of this file — so we add `_HERE` first. Locally
# we also sit beside an `aura/` parent that holds a different (newer) copy
# of the orchestrator with breaking signatures; we explicitly prefer the
# in-tree copies by putting `_HERE` ahead of the parent.

_HERE = Path(__file__).resolve().parent
if str(_HERE) not in sys.path:
    sys.path.insert(0, str(_HERE))

import gradio as gr  # noqa: E402

from agents.calendar.agent import CalendarAgent  # noqa: E402
from agents.comms.agent import CommsAgent  # noqa: E402
from agents.core.types import (  # noqa: E402
    AgentInput,
    AgentName,
    Candidate,
    UserState,
)
from agents.finance.agent import FinanceAgent  # noqa: E402
from agents.wellness.agent import WellnessAgent  # noqa: E402
from agents.wellness.load_score import LoadScoreModel, WellnessFeatures  # noqa: E402
from memory.store import MemoryGraph  # noqa: E402
from orchestrator.policy import Policy  # noqa: E402
from orchestrator.trace import emit_trace, validate_trace  # noqa: E402


# ---------------------------------------------------------------------------
# Lite-mode probe
# ---------------------------------------------------------------------------

def _probe_lite_mode() -> Dict[str, bool]:
    """Detect which heavy-but-optional deps are missing."""
    flags = {"sentence_transformers": False, "xgboost": False, "sqlite_vss": False}
    try:
        import sentence_transformers  # type: ignore  # noqa: F401
        flags["sentence_transformers"] = True
    except Exception:
        pass
    try:
        import xgboost  # type: ignore  # noqa: F401
        flags["xgboost"] = True
    except Exception:
        pass
    return flags


_LITE_FLAGS = _probe_lite_mode()
_LITE_MODE = not all(_LITE_FLAGS.values())


# ---------------------------------------------------------------------------
# Banner / hero / footer
# ---------------------------------------------------------------------------

_REPO_URL = "https://github.com/ShAuRyA-Noodle/Combobulating"
_README_URL = f"{_REPO_URL}/blob/main/README.md"
_DECK_URL = f"{_REPO_URL}/blob/main/aura/deck/phase1_deck.pdf"
_THREAT_URL = f"{_REPO_URL}/blob/main/aura/docs/threat_model.md"

_LITE_BADGE = (
    '<span class="aura-lite-badge">Running in lite mode</span>' if _LITE_MODE else ""
)

HERO_HTML = f"""
<div class="aura-hero">
  <div class="aura-hero-row">
    <svg width="48" height="48" viewBox="0 0 44 44" xmlns="http://www.w3.org/2000/svg" aria-hidden="true">
      <circle cx="22" cy="22" r="20" fill="none" stroke="#0E0E0E" stroke-width="2"/>
      <circle cx="22" cy="22" r="6" fill="#FF5B2E"/>
    </svg>
    <div>
      <h1>Aura {_LITE_BADGE}</h1>
      <p class="aura-tagline">Anticipate. Act. Stay quiet. — paste your own SMS, chat, or signals; watch the agents reason.</p>
    </div>
  </div>
  <img class="aura-hero-image"
       src="https://raw.githubusercontent.com/ShAuRyA-Noodle/Combobulating/main/aura/img/aura_03_screen_reasoning_trace_drawer.png"
       alt="Aura reasoning trace drawer signature visual"
       onerror="this.style.display='none'"/>
  <div class="aura-privacy">
    Demo runs on synthetic + your-pasted data. Nothing is logged.
    Open-source: <a href="{_REPO_URL}" target="_blank" rel="noreferrer">github.com/ShAuRyA-Noodle/Combobulating</a>.
  </div>
  <div class="aura-not-callout">
    <strong>What this is NOT</strong>
    This is a CPU-only public showcase. The real Aura product is on-device.
    The production stack runs Gemma 2B + Phi-3-mini via MLX (iOS) or MediaPipe
    LLM Inference (Android) — none of that runs here. This Space exposes the
    same orchestrator, schemas, and reasoning-trace contract, with the
    classifier/embedder swapped for the deterministic lightweight path.
  </div>
</div>
"""

FOOTER_HTML = f"""
<footer class="aura-footer">
  Aura is on-device. This Space is a public showcase that runs the real agent
  stack on synthetic + visitor-pasted data only.
  <br/>
  <a href="{_REPO_URL}" target="_blank" rel="noreferrer">Repo</a> ·
  <a href="{_README_URL}" target="_blank" rel="noreferrer">README</a> ·
  <a href="{_DECK_URL}" target="_blank" rel="noreferrer">Phase 1 deck (PDF)</a> ·
  <a href="{_THREAT_URL}" target="_blank" rel="noreferrer">Threat model</a>
</footer>
"""


_CSS_PATH = _HERE / "style.css"
CUSTOM_CSS = _CSS_PATH.read_text() if _CSS_PATH.exists() else ""


# ---------------------------------------------------------------------------
# Reasoning-trace JSON renderer with accent on locked keys
# ---------------------------------------------------------------------------

_HIGHLIGHT_KEYS = {"chosen", "rationale", "confirm_required"}


def _render_trace_json(payload: Dict[str, Any]) -> str:
    """Render JSON inside an .aura-trace-frame block with selective accents.

    The keys ``chosen``, ``rationale``, and ``confirm_required`` are wrapped
    in spans so the locked accent colour applies. Output is sanitised HTML.
    """
    raw = json.dumps(payload, indent=2, ensure_ascii=False, default=str)
    safe = html.escape(raw)
    # Highlight locked keys first.
    for k in _HIGHLIGHT_KEYS:
        safe = re.sub(
            rf'(&quot;{k}&quot;)(\s*:)',
            rf'<span class="key-{k}">\1</span>\2',
            safe,
        )
    # Generic key colouring.
    safe = re.sub(
        r'(&quot;[A-Za-z_][\w\-]*&quot;)(\s*:)',
        lambda m: m.group(0) if any(f'key-{k}' in m.group(0) for k in _HIGHLIGHT_KEYS)
        else f'<span class="json-key">{m.group(1)}</span>{m.group(2)}',
        safe,
    )
    # Booleans, numbers, strings.
    safe = re.sub(r'\b(true|false)\b', r'<span class="json-bool">\1</span>', safe)
    safe = re.sub(r':\s*(-?\d+(?:\.\d+)?)\b', r': <span class="json-num">\1</span>', safe)
    return f'<div class="aura-trace-frame">{safe}</div>'


def _safe_run(fn, *args, **kwargs):
    """Best-effort wrapper. Captures exceptions into a card so a bad input
    never crashes the whole Space. Returns the same shape as `fn`."""
    try:
        return fn(*args, **kwargs)
    except Exception as exc:
        msg = html.escape(f"{type(exc).__name__}: {exc}")
        tb = html.escape(traceback.format_exc().splitlines()[-1])
        card = (
            f"<div class='aura-card error'><div class='card-head'>"
            f"<span class='card-eyebrow'>Agent error</span></div>"
            f"<div>{msg}</div><div class='card-rationale'>{tb}</div></div>"
        )
        return card, _render_trace_json({"error": str(exc)})


# ---------------------------------------------------------------------------
# Locked DBMS 137-message scenario for Tab 2
# ---------------------------------------------------------------------------

LOCKED_DBMS_SCENARIO = """\
[09:00] @prof: morning everyone — DBMS quiz tomorrow 10am sharp
[09:01] @aarav: gn folks
[09:02] @rhea: lol same
[09:03] @sid: btw quiz tomorrow @you can you share notes
[09:04] @kabir: please confirm the syllabus
[09:05] @pri: thx aarav
[09:06] @aarav: brb
[09:07] @sid: @you reminder — viva at 4pm today, please confirm
[09:08] @rhea: same
[09:09] @ish: lol
[09:10] @kabir: nice
[09:11] @pri: cool
[09:12] @sid: idk
[09:13] @rhea: tbh same
[09:14] @kabir: btw who's on for chai
[09:15] @aarav: 3 ok
[09:16] @ish: lol
[09:17] @pri: thanks
[09:18] @rhea: gm
[09:19] @sid: please submit lab report by tonight
[09:20] @aarav: on it
[09:21] @ish: lmao
[09:22] @kabir: same
[09:23] @rhea: btw Prof shared deadline asap urgent
[09:24] @pri: ok
[09:25] @sid: @you can you push the merge before 5
[09:26] @ish: nice
[09:27] @kabir: brb
[09:28] @aarav: thx
[09:29] @rhea: tbh idk
[09:30] @ish: lol
[09:31] @pri: ok
[09:32] @sid: anyone has the slides
[09:33] @kabir: same
[09:34] @rhea: lol
[09:35] @aarav: gn
[09:36] @ish: brb
[09:37] @pri: thanks
[09:38] @sid: bruh same
[09:39] @kabir: gn
[09:40] @rhea: lol
[09:41] @ish: lol
[09:42] @aarav: confirm the meeting at 5
[09:43] @pri: ok
[09:44] @kabir: thanks
[09:45] @sid: please reply on the rebase pr
[09:46] @rhea: lol
[09:47] @ish: nice
[09:48] @pri: thx
[09:49] @kabir: gm
[09:50] @prof: announcement: please submit the ER diagram by 6pm — viva grading depends on it
[09:51] @rhea: noted prof
[09:52] @aarav: ok prof
[09:53] @sid: on it
[09:54] @kabir: same
[09:55] @ish: lol
[09:56] @pri: thx
[09:57] @rhea: btw who's free for chai
[09:58] @sid: brb
[09:59] @kabir: nice
[10:00] @ish: idk
[10:01] @aarav: gn
[10:02] @pri: thx
[10:03] @rhea: same
[10:04] @kabir: lol
[10:05] @sid: @you please review the schema before submission
[10:06] @ish: lmao
[10:07] @pri: ok
[10:08] @aarav: thx
[10:09] @rhea: btw is the lab open till 8
[10:10] @kabir: yes
[10:11] @sid: cool
[10:12] @ish: lol
[10:13] @pri: thanks
[10:14] @rhea: gm
[10:15] @aarav: brb
[10:16] @sid: anyone seen the practice paper
[10:17] @kabir: same
[10:18] @ish: nope
[10:19] @pri: thx
[10:20] @rhea: lol
[10:21] @aarav: gn
[10:22] @sid: @you can you share the join link for tonight's review call
[10:23] @kabir: please respond
[10:24] @ish: lol
[10:25] @pri: ok
[10:26] @rhea: btw quiz is closed-book right?
[10:27] @aarav: yes
[10:28] @sid: nice
[10:29] @kabir: thx
[10:30] @ish: same
[10:31] @pri: ok
[10:32] @rhea: lol
[10:33] @sid: confirm room number please
[10:34] @kabir: LT-3
[10:35] @ish: thx
[10:36] @pri: cool
[10:37] @aarav: brb
[10:38] @rhea: gm
[10:39] @sid: @you reminder to submit the proposal tonight
[10:40] @kabir: same
[10:41] @ish: lol
[10:42] @pri: thanks
[10:43] @rhea: btw the form deadline is 5pm
[10:44] @aarav: noted
[10:45] @sid: please share the rubric
[10:46] @kabir: on it
[10:47] @ish: lol
[10:48] @pri: thx
[10:49] @rhea: same
[10:50] @aarav: gn
[10:51] @sid: any update on the slot booking
[10:52] @kabir: nope
[10:53] @ish: lmao
[10:54] @pri: ok
[10:55] @rhea: lol
[10:56] @aarav: brb
[10:57] @sid: confirming we meet at 6 in LT-3
[10:58] @kabir: yes
[10:59] @ish: nice
[11:00] @pri: thx
[11:01] @rhea: same
[11:02] @aarav: gn
[11:03] @sid: please attach the pdf
[11:04] @kabir: same
[11:05] @ish: lol
[11:06] @pri: ok
[11:07] @rhea: btw the canteen closes at 9
[11:08] @aarav: noted
[11:09] @sid: @you can you confirm whether the project demo is on Friday
[11:10] @kabir: yes
[11:11] @ish: thx
[11:12] @pri: cool
[11:13] @rhea: lol
[11:14] @aarav: brb
[11:15] @sid: please review the migration script before 4pm
[11:16] @kabir: on it
[11:17] @ish: lol
[11:18] @pri: thx
[11:19] @rhea: same
[11:20] @aarav: gn
[11:21] @sid: thanks everyone
[11:22] @kabir: gn
[11:23] @ish: gn
[11:24] @pri: gn
[11:25] @rhea: gn
[11:26] @aarav: gn
"""


EXAMPLE_BANK_SMS: Dict[str, str] = {
    "HDFC": "Sent Rs.350.00 from A/c **1234 to ZOMATO via UPI on 07-MAY",
    "SBI": "Dear Customer, Rs.1200.00 debited from A/c X3389 on 07-05-26 to VPA bigbasket@okhdfc Ref 412345. -SBI",
    "ICICI": "INR 250.00 spent on ICICI Bank Card XX9921 at SWIGGY on 07-May-26",
    "Axis": "INR 540 debited A/c no. XX2245 07-05-26 13:42 UPI/P2A/uber@axis/Uber",
    "Kotak": "Sent Rs.180 from A/c **5511 to RAPIDO via UPI on 07-05-26",
    "PNB": "Rs.99.00 debited from A/c X7714 on 07-05-26 to VPA spotify@okpnb. -PNB",
}


# ---------------------------------------------------------------------------
# Tab 1 — Morning Brief Builder
# ---------------------------------------------------------------------------

def run_morning_brief(
    rmssd_ms: float,
    sleep_hours: float,
    ev1: str,
    ev2: str,
    ev3: str,
    notif_blob: str,
) -> Tuple[str, str]:
    """Wire the four agents through the policy ranker and surface the brief.

    We invoke each agent directly (not via the orchestrator's `_run_agents`
    loop) because the in-tree FinanceAgent is a dataclass whose `name`
    attribute would crash the orchestrator's AgentInput construction. Calling
    each agent and feeding the candidates into Policy.decide() yields the
    same Reasoning Trace shape.
    """

    tick_ts = "2026-05-07T08:30:00+00:00"
    sleep_target = 7.5
    sleep_debt_min = max(0.0, (sleep_target - float(sleep_hours)) * 60.0)

    # --- comms payload from the notif textarea --------------------------
    notif_lines = [ln.strip() for ln in (notif_blob or "").splitlines() if ln.strip()]
    notif_events: List[Dict[str, Any]] = []
    for i, line in enumerate(notif_lines[:8]):
        notif_events.append({
            "id": f"n_{i:03d}",
            "app_pkg": "wa",
            "channel": "ch_demo",
            "preview": line,
            "intent_hint": line[:64],
            "ts": tick_ts,
        })

    # --- calendar payload from the three event textboxes ----------------
    raw_events = [e for e in [ev1, ev2, ev3] if (e or "").strip()]
    events_today: List[Dict[str, Any]] = []
    for i, raw in enumerate(raw_events):
        # Format expected: "HH:MM-HH:MM Title" or just "Title". Default 1h.
        m = re.match(r"\s*(\d{1,2}:\d{2})\s*-\s*(\d{1,2}:\d{2})\s*(.*)$", raw)
        if m:
            start_t, end_t, title = m.group(1), m.group(2), m.group(3) or f"Event {i+1}"
        else:
            start_t, end_t, title = f"{9 + i}:00", f"{10 + i}:00", raw.strip()
        events_today.append({
            "id": f"ev_{i:02d}",
            "title": title,
            "start": f"2026-05-07T{int(start_t.split(':')[0]):02d}:{start_t.split(':')[1]}:00+00:00",
            "end": f"2026-05-07T{int(end_t.split(':')[0]):02d}:{end_t.split(':')[1]}:00+00:00",
        })

    # --- run agents -----------------------------------------------------
    user_state = UserState(load_score=50)
    candidates_all: List[Candidate] = []
    signals: List[Dict[str, Any]] = []
    agent_payloads: Dict[str, Any] = {}

    # comms
    comms = CommsAgent()
    comms_in = AgentInput(
        tick_ts=tick_ts,
        agent=AgentName.COMMS,
        user_state=user_state,
        payload={"notif_events": notif_events, "gmail_threads": []},
    )
    comms_out = comms.tick(comms_in)
    candidates_all.extend(comms_out.candidates)
    if comms_out.trace_fragment:
        signals.append({
            "agent": comms_out.trace_fragment.agent.value,
            "decision": comms_out.trace_fragment.decision,
            "drivers": comms_out.trace_fragment.drivers,
        })
    agent_payloads["comms"] = comms_out.payload

    # calendar
    cal = CalendarAgent()
    cal_in = AgentInput(
        tick_ts=tick_ts,
        agent=AgentName.CALENDAR,
        user_state=user_state,
        payload={"events_today": events_today, "preferences": {"buffer_minutes": 15}},
    )
    cal_out = cal.tick(cal_in)
    candidates_all.extend(cal_out.candidates)
    if cal_out.trace_fragment:
        signals.append({
            "agent": cal_out.trace_fragment.agent.value,
            "decision": cal_out.trace_fragment.decision,
            "drivers": cal_out.trace_fragment.drivers,
        })
    agent_payloads["calendar"] = cal_out.payload

    # wellness
    wellness_payload = {
        "rmssd_ms": float(rmssd_ms),
        "rmssd_z": (float(rmssd_ms) - 45.0) / 12.0,
        "sleep_debt_min": sleep_debt_min,
        "typing_entropy": 4.2,
        "app_switch_rate": 8,
        "notif_dismiss_rate": 0.4,
        "screen_on_min": 35,
    }
    well = WellnessAgent()
    well_in = AgentInput(
        tick_ts=tick_ts,
        agent=AgentName.WELLNESS,
        user_state=user_state,
        payload=wellness_payload,
    )
    well_out = well.tick(well_in)
    candidates_all.extend(well_out.candidates)
    if well_out.trace_fragment:
        signals.append({
            "agent": well_out.trace_fragment.agent.value,
            "decision": well_out.trace_fragment.decision,
            "drivers": well_out.trace_fragment.drivers,
        })
    agent_payloads["wellness"] = well_out.payload

    # finance (sync side — we only need its tick result for the card; not used
    # to pull candidates because finance generally returns SHOW_BRIEF in a
    # later phase).
    finance_payload: Dict[str, Any] = {}
    try:
        finance = FinanceAgent()
        coro = finance.tick({"sms_unprocessed": [], "gmail_receipts": [], "tick_ts": tick_ts})
        if hasattr(coro, "__await__"):
            finance_payload = asyncio.run(coro)
        signals.append({"agent": "finance", "decision": "do_nothing", "drivers": ["no_sms"]})
    except Exception as exc:
        finance_payload = {"error": str(exc)}

    agent_payloads["finance"] = finance_payload

    # --- ranker ---------------------------------------------------------
    policy = Policy()
    decision = policy.decide(
        candidates=candidates_all,
        user_state=user_state,
        history=__import__("orchestrator.policy", fromlist=["ActionHistory"]).ActionHistory(),
        dnd=__import__("orchestrator.policy", fromlist=["DNDWindow"]).DNDWindow(),
        now=datetime.fromisoformat(tick_ts.replace("Z", "+00:00")),
        recovering_since=None,
    )

    chosen_kind = decision.chosen.kind if decision.chosen else "do_nothing"
    rationale = _template_rationale(chosen_kind, signals, decision.cap_reason)

    trace = emit_trace(
        trigger={"source": "morning_brief", "value": tick_ts},
        signals=signals,
        scored=decision.candidates,
        chosen_action=decision.chosen,
        rationale=rationale,
        cap_reason=decision.cap_reason,
    )
    try:
        validate_trace(trace)
    except Exception:
        pass  # validation is best-effort here; the JSON is still rendered.

    # --- card ----------------------------------------------------------
    comms_payload = agent_payloads.get("comms", {})
    cal_payload = agent_payloads.get("calendar", {})
    well_payload = agent_payloads.get("wellness", {})

    urgent_n = len(comms_payload.get("urgent", []))
    muted_n = comms_payload.get("muted_count", 0)
    conflicts_n = len(cal_payload.get("conflicts", []))
    next_event = cal_payload.get("next_event") or {}
    leave_by = next_event.get("leave_by", "")
    load_score = well_payload.get("load_score", 0)
    interv = (well_payload.get("suggested_intervention") or {}).get("kind", "DO_NOTHING")

    leave_by_row = ""
    if leave_by:
        leave_by_row = (
            f"<div class='card-row'><span class='label'>Leave by</span>"
            f"<span class='value'>{html.escape(leave_by)}</span></div>"
        )

    card = f"""
    <div class="aura-card">
      <div class="card-head">
        <span class="card-eyebrow">Morning brief</span>
        <span class="card-pill">{html.escape(chosen_kind)}</span>
      </div>
      <div class="card-grid">
        <div class="card-row"><span class="label">Load score</span><span class="value">{load_score}</span></div>
        <div class="card-row"><span class="label">Intervention</span><span class="value">{html.escape(str(interv))}</span></div>
        <div class="card-row"><span class="label">Actionable</span><span class="value">{urgent_n}</span></div>
        <div class="card-row"><span class="label">Muted</span><span class="value">{muted_n}</span></div>
        <div class="card-row"><span class="label">Conflicts</span><span class="value">{conflicts_n}</span></div>
        {leave_by_row}
      </div>
      <p class="card-rationale">{html.escape(rationale)}</p>
    </div>
    """
    return card, _render_trace_json(trace.model_dump(mode="json"))


def _template_rationale(kind: str, signals: List[Dict[str, Any]], cap_reason: Optional[str]) -> str:
    if cap_reason and kind == "do_nothing":
        return f"Suppressed by policy: {cap_reason}."
    if kind == "MUTE_GROUP_30":
        return "High load with active group context; muting 30 minutes."
    if kind == "BREATHE_478":
        return "Stress spike detected; offering a breathing break."
    if kind == "LEAVE_BY_ALERT":
        return "Travel time means you should leave now."
    if kind == "SHOW_BRIEF":
        return "Composed a single brief from the morning's signals."
    if kind == "BATCH_DIGEST":
        return "Group flooded; collapsed into one digest with actionable items."
    if kind == "PERMIT_LEISURE":
        return "Load has dropped; you can take a break guilt-free."
    drivers = []
    for s in signals:
        drivers.extend(s.get("drivers", []))
    if drivers:
        return "Top drivers: " + ", ".join(drivers[:3]) + "."
    return f"Chose {kind}."


# ---------------------------------------------------------------------------
# Tab 2 — Quiet Group Chat
# ---------------------------------------------------------------------------

# Silence Budget — borrowed from the on-device module: 60 surfaces/day cap.
SILENCE_BUDGET_DAILY_TOKENS = 60


def run_quiet_group(text_blob: str) -> Tuple[str, str]:
    lines = [ln.strip() for ln in (text_blob or "").splitlines() if ln.strip()]
    lines = lines[:200]
    notif_events: List[Dict[str, Any]] = []
    for i, line in enumerate(lines):
        notif_events.append({
            "id": f"n_{i:03d}",
            "app_pkg": "wa",
            "channel": "ch_demo",
            "preview": line,
            "intent_hint": line[:64],
            "ts": "2026-05-07T09:00:00+00:00",
        })

    agent = CommsAgent()
    out = agent.tick(AgentInput(
        tick_ts="2026-05-07T09:00:00+00:00",
        agent=AgentName.COMMS,
        user_state=UserState(load_score=72),
        payload={"notif_events": notif_events, "gmail_threads": []},
    ))
    payload = out.payload
    urgent = payload.get("urgent", [])
    muted_count = payload.get("muted_count", 0)
    drafts = payload.get("drafts", [])

    # Surface only the top 3 actionable.
    surfaced = urgent[:3]
    silenced = max(0, len(notif_events) - len(surfaced))
    tokens_spent = len(surfaced)
    pct = min(100, int(round(100 * tokens_spent / SILENCE_BUDGET_DAILY_TOKENS)))

    rows = "".join(
        f"<li><code>{html.escape(u['item_id'])}</code> · "
        f"{html.escape(u['reason_code'])} · score {u['score']:.2f}</li>"
        for u in surfaced
    ) or "<li class='muted'>No actionable items surfaced</li>"

    drafts_rows = "".join(
        f"<li>↳ <em>{html.escape(d.get('draft_text',''))}</em></li>"
        for d in drafts[:3]
    )

    card = f"""
    <div class="aura-card">
      <div class="card-head">
        <span class="card-eyebrow">Quiet Group Chat</span>
        <span class="card-pill">{html.escape(payload.get('top_suggested_action',''))}</span>
      </div>
      <div class="card-grid">
        <div class="card-row"><span class="label">Total messages</span><span class="value">{len(notif_events)}</span></div>
        <div class="card-row"><span class="label">Surfaced</span><span class="value">{len(surfaced)}</span></div>
        <div class="card-row"><span class="label">Silenced</span><span class="value">{silenced}</span></div>
        <div class="card-row"><span class="label">Muted-class</span><span class="value">{muted_count}</span></div>
      </div>
      <div class="silence-meter">
        <div class="silence-meter-label">
          <span>Silence budget · tokens spent</span>
          <span>{tokens_spent} / {SILENCE_BUDGET_DAILY_TOKENS}</span>
        </div>
        <div class="silence-meter-track">
          <div class="silence-meter-fill" style="width:{pct}%"></div>
        </div>
      </div>
      <ul class="card-list">{rows}{drafts_rows}</ul>
    </div>
    """

    trace_payload = {
        "agent": "comms",
        "trigger": {"source": "quiet_group_chat", "value": "paste"},
        "decision": out.trace_fragment.decision if out.trace_fragment else "",
        "drivers": out.trace_fragment.drivers if out.trace_fragment else [],
        "candidates": [
            {"kind": c.kind, "confidence": c.confidence, "confirm_required": c.confirm_required}
            for c in out.candidates
        ],
        "chosen": payload.get("top_suggested_action", "DO_NOTHING"),
        "rationale": f"{len(surfaced)} actionable surfaced, {silenced} silenced.",
        "confirm_required": False,
        "drafts": drafts,
        "silence_budget": {"tokens_spent": tokens_spent, "daily_cap": SILENCE_BUDGET_DAILY_TOKENS},
    }
    return card, _render_trace_json(trace_payload)


# ---------------------------------------------------------------------------
# Tab 3 — Spend Mirror
# ---------------------------------------------------------------------------

def run_spend_mirror(sms_blob: str) -> Tuple[str, str]:
    agent = FinanceAgent()
    rows: List[Dict[str, Any]] = []
    skipped: List[str] = []

    lines = [ln.strip() for ln in (sms_blob or "").splitlines() if ln.strip()]
    lines = lines[:30]

    for line in lines:
        try:
            txn = agent.parse_sms(line)
        except Exception:
            txn = None
        if txn is None:
            skipped.append(line[:60])
            continue
        rows.append({
            "amount": float(txn.amount),
            "currency": txn.currency,
            "merchant": txn.merchant_raw,
            "category": txn.category.value if txn.category else "other",
            "bank": txn.bank,
            "account_last4": txn.account_last4,
            "ts": txn.ts.isoformat(),
            "anomaly_flag": False,
        })

    # Simple per-merchant anomaly: last txn's amount > 2× median for that merchant.
    by_merchant: Dict[str, List[float]] = {}
    for r in rows:
        by_merchant.setdefault(r["merchant"], []).append(r["amount"])
    for r in rows:
        amounts = by_merchant[r["merchant"]]
        if len(amounts) >= 3:
            sorted_a = sorted(amounts)
            median = sorted_a[len(sorted_a) // 2]
            if median > 0 and r["amount"] > 2 * median:
                r["anomaly_flag"] = True

    total = sum(r["amount"] for r in rows)
    # Naive end-of-month projection: linear from today's total over remaining days.
    today = datetime.now(timezone.utc).date()
    next_month = (today.replace(day=28) + __import__("datetime").timedelta(days=4)).replace(day=1)
    days_remaining = max(1, (next_month - today).days)
    daily_burn = total / max(1, len(rows))
    projected_eom = total + daily_burn * days_remaining

    # Substitution suggestion if a category dominates.
    cat_totals: Dict[str, float] = {}
    for r in rows:
        cat_totals[r["category"]] = cat_totals.get(r["category"], 0.0) + r["amount"]
    suggestion = None
    if cat_totals:
        top_cat, top_total = max(cat_totals.items(), key=lambda kv: kv[1])
        try:
            from agents.finance.agent import Category
            sub = agent.suggest_substitution(Category(top_cat))
            if sub:
                suggestion = {
                    "from_category": top_cat,
                    "suggestion": sub.suggestion,
                    "est_savings_inr": sub.est_savings_inr,
                }
        except Exception:
            pass

    rows_html = "".join(
        f"<tr>"
        f"<td>{html.escape(r['merchant'])}</td>"
        f"<td>{html.escape(r['category'])}</td>"
        f"<td>{html.escape(r['bank'])}</td>"
        f"<td>**{html.escape(r['account_last4'])}</td>"
        f"<td class='right'>₹{r['amount']:.2f}</td>"
        f"<td class='{'flag-anom' if r['anomaly_flag'] else ''}'>"
        f"{'⚠ anomaly' if r['anomaly_flag'] else '—'}</td>"
        f"</tr>"
        for r in rows
    ) or "<tr><td colspan='6' class='muted'>No SMS parsed</td></tr>"

    sub_html = ""
    if suggestion:
        sub_html = (
            f"<p class='card-rationale'>Suggested swap for "
            f"<b>{html.escape(suggestion['from_category'])}</b>: "
            f"{html.escape(suggestion['suggestion'])} · "
            f"~₹{suggestion['est_savings_inr']:.0f} saving.</p>"
        )

    card = f"""
    <div class="aura-card">
      <div class="card-head">
        <span class="card-eyebrow">Spend Mirror</span>
        <span class="card-pill">₹{total:,.0f}</span>
      </div>
      <div class="card-grid">
        <div class="card-row"><span class="label">Parsed</span><span class="value">{len(rows)}</span></div>
        <div class="card-row"><span class="label">Skipped</span><span class="value">{len(skipped)}</span></div>
        <div class="card-row"><span class="label">Projected EoM spend</span><span class="value">₹{projected_eom:,.0f}</span></div>
        <div class="card-row"><span class="label">Top category</span><span class="value">{html.escape(max(cat_totals, key=cat_totals.get) if cat_totals else '—')}</span></div>
      </div>
      <table class="aura-table">
        <thead><tr>
          <th>Merchant</th><th>Category</th><th>Bank</th><th>A/c</th>
          <th class="right">Amount</th><th>Flag</th>
        </tr></thead>
        <tbody>{rows_html}</tbody>
      </table>
      {sub_html}
    </div>
    """

    trace_payload = {
        "agent": "finance",
        "trigger": {"source": "spend_mirror", "value": "paste"},
        "transactions": rows,
        "skipped": skipped,
        "projected_eom_spend_inr": round(projected_eom, 2),
        "suggested_substitution": suggestion,
        "chosen": "SHOW_BRIEF" if rows else "do_nothing",
        "rationale": f"Parsed {len(rows)} SMS, {len(skipped)} unparseable.",
        "confirm_required": False,
    }
    return card, _render_trace_json(trace_payload)


def _load_example_sms(bank: str) -> str:
    return EXAMPLE_BANK_SMS.get(bank, "")


# ---------------------------------------------------------------------------
# Tab 4 — Load Score Live
# ---------------------------------------------------------------------------

def run_load_score(
    rmssd_ms: float,
    typing_entropy: float,
    app_switch_rate: int,
    sleep_debt_min: float,
    notif_dismiss_rate: float,
) -> Tuple[str, str]:
    feats = WellnessFeatures(
        rmssd_ms=float(rmssd_ms),
        rmssd_z=(float(rmssd_ms) - 45.0) / 12.0,
        sleep_debt_min=float(sleep_debt_min),
        typing_entropy=float(typing_entropy),
        app_switch_rate=int(app_switch_rate),
        notif_dismiss_rate=float(notif_dismiss_rate),
        screen_on_min=30,
    )
    model = LoadScoreModel()
    raw = float(model.predict_score(feats))
    score = int(round(raw))
    drivers = model.driver_breakdown(feats)

    agent = WellnessAgent(model=model)
    out = agent.tick(AgentInput(
        tick_ts="2026-05-07T11:30:00+00:00",
        agent=AgentName.WELLNESS,
        user_state=UserState(load_score=score),
        payload={
            "rmssd_ms": float(rmssd_ms),
            "rmssd_z": feats.rmssd_z,
            "sleep_debt_min": float(sleep_debt_min),
            "typing_entropy": float(typing_entropy),
            "app_switch_rate": int(app_switch_rate),
            "notif_dismiss_rate": float(notif_dismiss_rate),
            "screen_on_min": 30,
        },
    ))
    payload = out.payload
    interv = payload.get("suggested_intervention") or {}
    state = payload.get("state", "UNKNOWN")
    score = payload.get("load_score", score)

    # Driver bars normalised by the largest absolute contribution.
    max_abs = max((abs(float(d.get("value", 0) or 0)) for d in drivers), default=1.0) or 1.0
    bars = "".join(
        f"<div class='driver-bar'>"
        f"<span class='driver-name'>{html.escape(str(d['feature']))}</span>"
        f"<div class='driver-track'><div class='driver-fill' "
        f"style='width:{min(100, abs(float(d.get('value', 0) or 0)) / max_abs * 100):.0f}%'></div></div>"
        f"<span class='driver-val'>{d['value']}</span></div>"
        for d in drivers
    )

    pill_cls = "score-high" if score >= 70 else ("score-mid" if score >= 50 else "score-low")
    card = f"""
    <div class="aura-card">
      <div class="card-head">
        <span class="card-eyebrow">Load Score Live</span>
        <span class="card-pill {pill_cls}">{score}</span>
      </div>
      <div class="card-grid">
        <div class="card-row"><span class="label">State</span><span class="value">{html.escape(state)}</span></div>
        <div class="card-row"><span class="label">Intervention</span><span class="value">{html.escape(str(interv.get('kind','DO_NOTHING')))}</span></div>
        <div class="card-row"><span class="label">Surface</span><span class="value">{html.escape(str(interv.get('surface','SILENT')))}</span></div>
        <div class="card-row"><span class="label">Confirm required</span><span class="value">{interv.get('confirm_required', False)}</span></div>
      </div>
      <div class="driver-bars">{bars}</div>
      <p class="card-rationale">{html.escape(str(interv.get('rationale_seed','')))}</p>
    </div>
    """

    trace_payload = {
        "agent": "wellness",
        "trigger": {"source": "load_score_live", "value": "sliders"},
        "load_score": score,
        "state": state,
        "drivers": drivers,
        "intervention": interv,
        "chosen": interv.get("kind", "DO_NOTHING"),
        "rationale": interv.get("rationale_seed", ""),
        "confirm_required": interv.get("confirm_required", False),
    }
    return card, _render_trace_json(trace_payload)


# ---------------------------------------------------------------------------
# Tab 5 — Memory Graph Explorer
# ---------------------------------------------------------------------------

# In-process graph for the Space session. All writes are in-memory.
_GRAPH = MemoryGraph(path=":memory:")


def memory_add(node_type: str, data_json: str) -> Tuple[str, str]:
    try:
        data = json.loads(data_json or "{}")
    except json.JSONDecodeError as exc:
        return f"<div class='aura-card error'>Bad JSON: {html.escape(str(exc))}</div>", ""
    nid = _GRAPH.add_node(type=node_type, data=data)
    _GRAPH.add_embedding(nid, 0, json.dumps(data))
    return (
        f"<div class='aura-card'><b>Added node</b> "
        f"<code>{html.escape(nid)}</code></div>",
        nid,
    )


def memory_search(query: str, k: int = 5) -> str:
    if not (query or "").strip():
        return "<div class='aura-card muted'>Type a query.</div>"
    results = _GRAPH.search(query, k=int(k))
    if not results:
        return "<div class='aura-card muted'>No matches.</div>"
    rows = "".join(
        f"<tr><td><code>{html.escape(r['node_id'])}</code></td>"
        f"<td>{html.escape(r['type'])}</td>"
        f"<td>{r['score']:.4f}</td>"
        f"<td>{html.escape(json.dumps(r['data'])[:80])}</td></tr>"
        for r in results
    )
    return f"""
    <div class="aura-card">
      <div class="card-head"><span class="card-eyebrow">Search results</span></div>
      <table class="aura-table"><thead><tr>
        <th>Node</th><th>Type</th><th>Score</th><th>Data</th>
      </tr></thead><tbody>{rows}</tbody></table>
    </div>
    """


def memory_export_file() -> str:
    """Write the current graph export to a temp file and return the path.

    Gradio's `gr.File` output expects a file path, so we materialise the
    export to a session-local file and let the user download it.
    """
    export = _GRAPH.export_json()
    out_path = _HERE / "static" / "memory_export.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(export, indent=2, ensure_ascii=False))
    return str(out_path)


def memory_merkle_root() -> str:
    try:
        root = _GRAPH.daily_merkle_root()
    except Exception as exc:
        return f"<div class='aura-card error'>Merkle error: {html.escape(str(exc))}</div>"
    today = datetime.now(timezone.utc).date().isoformat()
    return f"""
    <div class="aura-card">
      <div class="card-head"><span class="card-eyebrow">Merkle root · {today}</span>
        <span class="card-pill">tamper-evident</span></div>
      <p style="font-family: 'JetBrains Mono', monospace; word-break: break-all;
                font-size: 12px; color: var(--aura-ink);">{html.escape(root)}</p>
      <p class="card-rationale">Daily Merkle root of the audit log. Any retroactive
        edit to a node, edge, or trace would change this hash — the audit chain
        is tamper-evident by construction.</p>
    </div>
    """


# ---------------------------------------------------------------------------
# Tab 6 — Reasoning Trace Library
# ---------------------------------------------------------------------------

# We pre-bake three replay traces from three orchestrator scenarios so the
# library is meaningful out-of-the-box. Each trace is generated at startup
# and cached on disk so we never re-run on every page load.

_REPLAY_DIR = _HERE / "orchestrator" / "replays" / "output"
_REPLAY_DIR.mkdir(parents=True, exist_ok=True)


def _generate_replay_traces() -> List[Dict[str, Any]]:
    """Generate three trace replays. Idempotent — only writes if missing."""
    scenarios: List[Dict[str, Any]] = [
        {
            "id": "monday_brief",
            "title": "Monday Morning Brief",
            "description": "Rohan unlocks his phone at 07:45. Quiz at 09:00, "
                           "DSA group buzzing, low HRV. The orchestrator weighs "
                           "SHOW_BRIEF vs LEAVE_BY_ALERT.",
            "rmssd": 39.5,
            "sleep_h": 5.2,
            "events": ["09:00-10:00 DSA Quiz", "13:00-14:00 Lunch with Anu", ""],
            "notifs": "@you can you confirm the schema for the quiz\nlol that meme tho",
        },
        {
            "id": "stress_spike",
            "title": "Stress Spike — group flood",
            "description": "Mid-afternoon: HRV crashes, app switching, group "
                           "chat at 30+ messages. The Wellness Agent surfaces "
                           "MUTE_GROUP_30 with confirm-required.",
            "rmssd": 22.0,
            "sleep_h": 4.0,
            "events": ["", "", ""],
            "notifs": "\n".join([f"msg {i}" for i in range(35)]),
        },
        {
            "id": "calm_evening",
            "title": "Calm Evening — recovery",
            "description": "HRV recovered, low switching, no urgent comms. "
                           "PERMIT_LEISURE — the agent guilt-free unblocks "
                           "the user's evening.",
            "rmssd": 62.0,
            "sleep_h": 7.5,
            "events": ["20:00-21:00 Movie night"],
            "notifs": "lol\ngn\nhaha",
        },
    ]
    out: List[Dict[str, Any]] = []
    for s in scenarios:
        out_path = _REPLAY_DIR / f"{s['id']}.trace.json"
        if out_path.exists():
            try:
                trace_obj = json.loads(out_path.read_text())
            except Exception:
                trace_obj = None
        else:
            trace_obj = None
        if trace_obj is None:
            ev = list(s["events"]) + ["", "", ""]
            try:
                _, trace_html = run_morning_brief(
                    s["rmssd"], s["sleep_h"], ev[0], ev[1], ev[2], s["notifs"]
                )
                # Extract the JSON payload by re-running the trace producer
                # cleanly via the underlying orchestrator path.
                trace_obj = _build_trace_for_replay(
                    rmssd=s["rmssd"], sleep_h=s["sleep_h"],
                    events=ev[:3], notifs=s["notifs"],
                    scenario=s["id"],
                )
                out_path.write_text(json.dumps(trace_obj, indent=2))
            except Exception:
                trace_obj = {"error": "could not generate"}
        out.append({
            "id": s["id"],
            "title": s["title"],
            "description": s["description"],
            "trace": trace_obj,
        })
    return out


def _build_trace_for_replay(
    rmssd: float, sleep_h: float,
    events: List[str], notifs: str,
    scenario: str,
) -> Dict[str, Any]:
    """Produce a structured trace JSON identical-shape to the live tabs."""
    # Reuse run_morning_brief plumbing to keep one source of truth, but pull
    # the structured payload from the rendered HTML by piggy-backing on the
    # internal calls instead of parsing the HTML string.
    tick_ts = "2026-05-07T08:30:00+00:00"
    sleep_target = 7.5
    sleep_debt_min = max(0.0, (sleep_target - sleep_h) * 60.0)
    notif_lines = [ln.strip() for ln in (notifs or "").splitlines() if ln.strip()]
    notif_events = [
        {"id": f"n_{i:03d}", "app_pkg": "wa", "channel": "ch_demo",
         "preview": ln, "intent_hint": ln[:64], "ts": tick_ts}
        for i, ln in enumerate(notif_lines[:8])
    ]
    raw_events = [e for e in events if (e or "").strip()]
    events_today = []
    for i, raw in enumerate(raw_events):
        m = re.match(r"\s*(\d{1,2}:\d{2})\s*-\s*(\d{1,2}:\d{2})\s*(.*)$", raw)
        if m:
            start_t, end_t, title = m.group(1), m.group(2), m.group(3) or f"Event {i+1}"
        else:
            start_t, end_t, title = f"{9 + i}:00", f"{10 + i}:00", raw.strip()
        events_today.append({
            "id": f"ev_{i:02d}", "title": title,
            "start": f"2026-05-07T{int(start_t.split(':')[0]):02d}:{start_t.split(':')[1]}:00+00:00",
            "end": f"2026-05-07T{int(end_t.split(':')[0]):02d}:{end_t.split(':')[1]}:00+00:00",
        })

    user_state = UserState(load_score=50)
    candidates_all: List[Candidate] = []
    signals: List[Dict[str, Any]] = []

    comms_out = CommsAgent().tick(AgentInput(
        tick_ts=tick_ts, agent=AgentName.COMMS, user_state=user_state,
        payload={"notif_events": notif_events, "gmail_threads": []}))
    candidates_all.extend(comms_out.candidates)
    if comms_out.trace_fragment:
        signals.append({"agent": "comms",
                        "decision": comms_out.trace_fragment.decision,
                        "drivers": comms_out.trace_fragment.drivers})

    cal_out = CalendarAgent().tick(AgentInput(
        tick_ts=tick_ts, agent=AgentName.CALENDAR, user_state=user_state,
        payload={"events_today": events_today, "preferences": {"buffer_minutes": 15}}))
    candidates_all.extend(cal_out.candidates)
    if cal_out.trace_fragment:
        signals.append({"agent": "calendar",
                        "decision": cal_out.trace_fragment.decision,
                        "drivers": cal_out.trace_fragment.drivers})

    well_payload = {
        "rmssd_ms": rmssd, "rmssd_z": (rmssd - 45.0) / 12.0,
        "sleep_debt_min": sleep_debt_min, "typing_entropy": 4.2,
        "app_switch_rate": 8, "notif_dismiss_rate": 0.4, "screen_on_min": 35,
    }
    well_out = WellnessAgent().tick(AgentInput(
        tick_ts=tick_ts, agent=AgentName.WELLNESS, user_state=user_state,
        payload=well_payload))
    candidates_all.extend(well_out.candidates)
    if well_out.trace_fragment:
        signals.append({"agent": "wellness",
                        "decision": well_out.trace_fragment.decision,
                        "drivers": well_out.trace_fragment.drivers})

    from orchestrator.policy import ActionHistory, DNDWindow
    decision = Policy().decide(
        candidates=candidates_all, user_state=user_state,
        history=ActionHistory(), dnd=DNDWindow(),
        now=datetime.fromisoformat(tick_ts.replace("Z", "+00:00")),
        recovering_since=None,
    )
    chosen_kind = decision.chosen.kind if decision.chosen else "do_nothing"
    rationale = _template_rationale(chosen_kind, signals, decision.cap_reason)
    trace = emit_trace(
        trigger={"source": "replay", "value": scenario},
        signals=signals, scored=decision.candidates,
        chosen_action=decision.chosen, rationale=rationale,
        cap_reason=decision.cap_reason,
    )
    try:
        validate_trace(trace)
    except Exception:
        pass
    return trace.model_dump(mode="json")


_REPLAYS = _generate_replay_traces()


def render_replay_grid() -> str:
    cards = "".join(
        f"<div class='replay-card'>"
        f"<div class='replay-meta'><span>#{i+1}</span><span>{html.escape(r['id'])}</span></div>"
        f"<h3>{html.escape(r['title'])}</h3>"
        f"<p>{html.escape(r['description'])}</p>"
        f"<p><b>Chosen:</b> "
        f"<code>{html.escape(str(r['trace'].get('chosen','—')))}</code></p>"
        f"</div>"
        for i, r in enumerate(_REPLAYS)
    )
    return f"<div class='replay-grid'>{cards}</div>"


def open_replay(idx: int) -> str:
    if idx < 0 or idx >= len(_REPLAYS):
        return _render_trace_json({"error": "out of range"})
    return _render_trace_json(_REPLAYS[idx]["trace"])


# ---------------------------------------------------------------------------
# UI assembly
# ---------------------------------------------------------------------------

def _aura_theme():
    return gr.themes.Default(
        primary_hue=gr.themes.Color(
            c50="#FFF1EC", c100="#FFD9CB", c200="#FFB69E", c300="#FF8E6B",
            c400="#FF6F46", c500="#FF5B2E", c600="#E54A1F", c700="#B6391A",
            c800="#7E2812", c900="#4A170A", c950="#2A0D05",
        ),
        secondary_hue="orange",
        neutral_hue="stone",
        font=[gr.themes.GoogleFont("Inter Tight"), "Inter Tight", "system-ui", "sans-serif"],
        font_mono=[gr.themes.GoogleFont("JetBrains Mono"), "monospace"],
    ).set(
        body_background_fill="#FAF8F5",
        body_text_color="#0E0E0E",
        block_background_fill="#FFFFFF",
        block_border_color="#E8E2D8",
        button_primary_background_fill="#FF5B2E",
        button_primary_text_color="#FFFFFF",
    )


def build_app() -> gr.Blocks:
    """Build and return the Gradio Blocks app. Exposed for tests / CI."""
    with gr.Blocks(
        title="Aura — On-device proactive assistant (interactive demo)",
        css=CUSTOM_CSS,
        theme=_aura_theme(),
    ) as demo:
        gr.HTML(HERO_HTML)

        with gr.Tabs():
            # ---------- Tab 1 — Morning Brief Builder ------------------
            with gr.Tab("Morning Brief"):
                gr.Markdown(
                    "Set HRV, sleep, three calendar events, and 5 notifications. "
                    "The brief flows through the real Calendar / Comms / Wellness "
                    "agents and the Policy ranker. The Reasoning Trace below is "
                    "the same shape Aura produces on-device."
                )
                with gr.Row():
                    rmssd1 = gr.Slider(20, 80, value=45, step=1,
                                       label="HRV — RMSSD (ms)")
                    sleep1 = gr.Slider(0, 10, value=6, step=0.25,
                                       label="Sleep last night (hours)")
                with gr.Row():
                    ev1 = gr.Textbox(value="09:00-10:00 DSA Quiz",
                                     label="Calendar event 1 (HH:MM-HH:MM Title)")
                    ev2 = gr.Textbox(value="13:00-14:00 Lunch with Anu",
                                     label="Calendar event 2")
                    ev3 = gr.Textbox(value="", label="Calendar event 3")
                notif1 = gr.Textbox(
                    value=("@you can you confirm the schema for the quiz\n"
                           "lol that meme tho\n"
                           "btw who's on for chai\n"
                           "please push the merge before 5\n"
                           "gn folks"),
                    lines=5,
                    label="Notifications (one per line, up to 5)",
                )
                run1 = gr.Button("Run morning brief", variant="primary")
                card1 = gr.HTML()
                trace1 = gr.HTML(label="Reasoning Trace")
                run1.click(run_morning_brief,
                           [rmssd1, sleep1, ev1, ev2, ev3, notif1],
                           [card1, trace1])

            # ---------- Tab 2 — Quiet Group Chat -----------------------
            with gr.Tab("Quiet Group Chat"):
                gr.Markdown(
                    "Paste your own group chat (up to 200 messages, one per line). "
                    "The CommsAgent triages to actionable + muted. The Silence "
                    "Budget meter shows how many surface tokens were spent."
                )
                chat_box = gr.Textbox(
                    value=LOCKED_DBMS_SCENARIO,
                    lines=14,
                    label="Group chat (one message per line)",
                )
                with gr.Row():
                    run2 = gr.Button("Triage", variant="primary")
                    load_dbms = gr.Button("Load 137-msg DBMS scenario")
                card2 = gr.HTML()
                trace2 = gr.HTML(label="Reasoning Trace")
                run2.click(run_quiet_group, [chat_box], [card2, trace2])
                load_dbms.click(lambda: LOCKED_DBMS_SCENARIO, [], [chat_box])

            # ---------- Tab 3 — Spend Mirror ---------------------------
            with gr.Tab("Spend Mirror"):
                gr.Markdown(
                    "Paste 1-30 lines of Indian bank SMS. The FinanceAgent's regex "
                    "pack parses HDFC / SBI / ICICI / Axis / Kotak / PNB. "
                    "Anomalies are flagged when amount > 2× per-merchant median."
                )
                sms_box = gr.Textbox(
                    value="\n".join(EXAMPLE_BANK_SMS.values()),
                    lines=8,
                    label="UPI / debit-card SMS (one per line)",
                )
                with gr.Row():
                    run3 = gr.Button("Parse + categorise", variant="primary")
                with gr.Row():
                    bank_buttons = []
                    for bank in EXAMPLE_BANK_SMS:
                        b = gr.Button(f"Load {bank} example")
                        b.click(_load_example_sms, [gr.State(bank)], [sms_box])
                        bank_buttons.append(b)
                card3 = gr.HTML()
                trace3 = gr.HTML(label="Reasoning Trace")
                run3.click(run_spend_mirror, [sms_box], [card3, trace3])

            # ---------- Tab 4 — Load Score Live ------------------------
            with gr.Tab("Load Score Live"):
                gr.Markdown(
                    "Slide the five headline features. The Load Score is computed "
                    "by the trained XGBoost regressor when available, otherwise "
                    "by the deterministic linear fallback (transparent for the "
                    "Reasoning Trace)."
                )
                with gr.Row():
                    rmssd4 = gr.Slider(20, 80, value=28, step=1,
                                       label="HRV — RMSSD (ms)")
                    entropy4 = gr.Slider(2.0, 6.0, value=4.8, step=0.1,
                                         label="Typing entropy (bits)")
                with gr.Row():
                    switch4 = gr.Slider(0, 30, value=14, step=1,
                                        label="App-switch rate / min")
                    sleep4 = gr.Slider(0, 240, value=120, step=5,
                                       label="Sleep debt (min)")
                dismiss4 = gr.Slider(0.0, 1.0, value=0.5, step=0.05,
                                     label="Notification dismiss rate")
                run4 = gr.Button("Recompute Load", variant="primary")
                card4 = gr.HTML()
                trace4 = gr.HTML(label="Reasoning Trace")
                run4.click(run_load_score,
                           [rmssd4, entropy4, switch4, sleep4, dismiss4],
                           [card4, trace4])

            # ---------- Tab 5 — Memory Graph Explorer ------------------
            with gr.Tab("Memory Graph"):
                gr.Markdown(
                    "Add nodes, search semantically (vector + keyword), export "
                    "the full JSON, and inspect today's Merkle root. All "
                    "in-memory — destroyed on Space restart."
                )
                with gr.Row():
                    nodetype = gr.Dropdown(
                        choices=["Event", "Person", "Place", "Transaction",
                                 "Conversation", "Action", "Trace", "App",
                                 "User", "HealthSnapshot"],
                        value="Event", label="Node type",
                    )
                    nodedata = gr.Textbox(
                        value='{"title":"DBMS quiz","note":"tomorrow 10am"}',
                        label="Node data (JSON)",
                    )
                add_btn = gr.Button("Add node + embed", variant="primary")
                add_out = gr.HTML()
                last_id = gr.Textbox(visible=False)
                add_btn.click(memory_add, [nodetype, nodedata],
                              [add_out, last_id])

                with gr.Row():
                    q = gr.Textbox(value="quiz tomorrow", label="Search query")
                    k = gr.Slider(1, 10, value=5, step=1, label="Top-k")
                search_btn = gr.Button("Search")
                search_out = gr.HTML()
                search_btn.click(memory_search, [q, k], [search_out])

                with gr.Row():
                    export_btn = gr.Button("Export graph as JSON file")
                    merkle_btn = gr.Button("Show today's Merkle root")
                export_file = gr.File(label="Memory graph export")
                merkle_out = gr.HTML()
                export_btn.click(memory_export_file, [], [export_file])
                merkle_btn.click(memory_merkle_root, [], [merkle_out])

            # ---------- Tab 6 — Reasoning Trace Library ----------------
            with gr.Tab("Reasoning Trace Library"):
                gr.Markdown(
                    "Three pre-recorded glass-box trace replays. Click a card "
                    "to expand its Reasoning Trace JSON. This tab is the "
                    "educational counterpart of the live tabs — proof that "
                    "every Aura decision is auditable end-to-end."
                )
                gr.HTML(render_replay_grid())
                with gr.Row():
                    open0 = gr.Button("Open: Monday Brief")
                    open1 = gr.Button("Open: Stress Spike")
                    open2 = gr.Button("Open: Calm Evening")
                replay_out = gr.HTML(label="Replay trace JSON")
                open0.click(lambda: open_replay(0), [], [replay_out])
                open1.click(lambda: open_replay(1), [], [replay_out])
                open2.click(lambda: open_replay(2), [], [replay_out])

        gr.HTML(FOOTER_HTML)

    return demo


def main() -> None:
    demo = build_app()
    demo.queue().launch(
        server_name=os.environ.get("GRADIO_SERVER_NAME", "0.0.0.0"),
        server_port=int(os.environ.get("GRADIO_SERVER_PORT", "7860")),
        share=False,
    )


if __name__ == "__main__":
    main()
