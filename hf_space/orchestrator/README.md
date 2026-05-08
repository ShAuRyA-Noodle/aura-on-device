# Orchestrator

Per `technical_spec.md` §4 + plan.md §1.2.

LangGraph state machine that wires the four specialist agents into a single
deterministic decision loop. States: `Idle`, `Listening`, `Deliberating`,
`AwaitingConfirm`, `Executing`, `LoggingTrace`, `Cooldown`. Hard caps are
enforced before scoring; the trace records *why* a candidate was dropped.

## Files

| File | Purpose |
|---|---|
| `graph.py` | LangGraph-shaped state machine. Falls back to a deterministic in-process state machine when LangGraph isn't on the path; behaviour is identical so the team can develop without the dependency. |
| `policy.py` | Candidate-action ranking — `score = utility - cost - recent_action_penalty - dnd_penalty` with the Silence Budget enforced before scoring. |
| `tools.py` | JSON Schema for every agent tool, plus jsonschema-based `validate_tool_call`. |
| `trace.py` | `emit_trace` / `validate_trace` / `pretty_render` + canonical hash for the audit chain. |
| `replays/monday_brief.replay.json` | Plan §7 Journey A end-to-end replay fixture. |
| `test_orchestrator.py` | Stress-driven mute (plan §11), daily cap, DND, trace schema, tool schema, replay. |

## LangGraph

The team installs LangGraph with:

```bash
pip install langgraph
```

The fallback runs identically when LangGraph isn't present so unit tests pass
on a clean venv. Production sets `USE_LANGGRAPH=1` and the graph is wired with
`langgraph.StateGraph` per the public API:
<https://langchain-ai.github.io/langgraph/>.

## Silence Budget (plan §1.2)

Default 3 proactive surfaces per local-day. The user "earns back" a surface by
tapping "useful" on a card — the orchestrator decrements the daily counter.
Wellness `MUTE_*` and `BREATHE_*` are uncapped because they are safety-class.

## Auto-execute allowlist (spec §4.4)

Only these kinds can have `confirm_required=false`:

```
BATCH_DIGEST  LEAVE_BY_ALERT  SHOW_BRIEF  CATEGORIZE_TXN  SURFACE_ANOMALY  PROJECT_BALANCE
```

Anything else is forced to confirm — the orchestrator refuses to set
`confirm_required=false` for kinds outside the allowlist.

## Run tests

```bash
pytest orchestrator -q
```
