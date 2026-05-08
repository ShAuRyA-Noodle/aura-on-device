"""Tool registry + JSON-Schema validation for every agent ToolCall.

Implements technical_spec.md §4.5.

Each agent registers its ``tools()`` (list of ``{name, description, parameters}``
dicts). The orchestrator ``validate_tool_call`` checks every outgoing
``ToolCall`` against:
1. The envelope schema (`toolcall.v1.json`).
2. The agent-specific ``parameters`` JSON Schema.

Validation failure raises ``ToolValidationError`` — orchestrator falls back to
``do_nothing`` and logs the failure (spec §4.1 Executing on_timeout).

Public API:
- ``build_tool_registry(agents)`` — returns dict[(agent_name, tool_name)] -> schema.
- ``validate_tool_call(call, registry)`` — raises on schema mismatch.
- ``TOOLCALL_ENVELOPE_SCHEMA`` — exposed for unit tests.
"""

from __future__ import annotations

from typing import Any, Dict, Iterable, Tuple

from jsonschema import Draft202012Validator, ValidationError

from agents.core.types import ToolCall


TOOLCALL_ENVELOPE_SCHEMA: Dict[str, Any] = {
    "$id": "https://aura.local/schemas/toolcall.v1.json",
    "type": "object",
    "required": ["call_id", "agent", "tool", "args", "ts", "confirm_required"],
    "properties": {
        "call_id": {"type": "string", "pattern": "^t_[a-z0-9]{10}$"},
        "agent": {"enum": ["comms", "calendar", "finance", "wellness", "orchestrator"]},
        "tool": {"type": "string"},
        "args": {"type": "object"},
        "ts": {"type": "string"},
        "confirm_required": {"type": "boolean"},
        "expected_surface": {"enum": ["WATCH", "PHONE_CARD", "EARBUD_TTS", "SILENT"]},
        "deadline_ms": {"type": "integer", "minimum": 50, "maximum": 10000},
    },
    "additionalProperties": False,
}


class ToolValidationError(Exception):
    """Raised when a ToolCall fails envelope or per-tool schema validation."""


def build_tool_registry(agents: Iterable[Any]) -> Dict[Tuple[str, str], Dict[str, Any]]:
    """Compose `(agent_name, tool_name) -> tool_schema` from agents.

    Accepts heterogeneous agent objects: each must have either a ``tools()``
    callable returning the standard list or a ``TOOLS`` tuple of names.
    """
    registry: Dict[Tuple[str, str], Dict[str, Any]] = {}
    for agent in agents:
        agent_name = getattr(agent, "name", None)
        if agent_name is None:
            continue
        a_str = agent_name.value if hasattr(agent_name, "value") else str(agent_name)
        if hasattr(agent, "tools") and callable(agent.tools):
            for tool in agent.tools():
                registry[(a_str, tool["name"])] = tool
        elif hasattr(agent, "TOOLS"):
            for name in agent.TOOLS:
                registry[(a_str, name)] = {"name": name, "parameters": {"type": "object"}}
    return registry


def validate_tool_call(call: ToolCall, registry: Dict[Tuple[str, str], Dict[str, Any]]) -> None:
    """Raises ``ToolValidationError`` if anything is off."""
    # Envelope.
    payload = call.model_dump(mode="json")
    try:
        Draft202012Validator(TOOLCALL_ENVELOPE_SCHEMA).validate(payload)
    except ValidationError as exc:
        raise ToolValidationError(f"envelope: {exc.message}") from exc

    # Per-tool args.
    a_str = call.agent.value if hasattr(call.agent, "value") else str(call.agent)
    key = (a_str, call.tool)
    if key not in registry:
        raise ToolValidationError(f"unknown tool: {a_str}.{call.tool}")
    tool_schema = registry[key]
    params_schema = tool_schema.get("parameters", {"type": "object"})
    try:
        Draft202012Validator(params_schema).validate(call.args)
    except ValidationError as exc:
        raise ToolValidationError(f"{a_str}.{call.tool} args: {exc.message}") from exc
