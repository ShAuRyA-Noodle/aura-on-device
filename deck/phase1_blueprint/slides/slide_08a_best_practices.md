---
slide: 8a
title: Best Practices & Creative AI Use (extended)
---
## BODY
One action, one trace. Every time.
Deterministic state machine. Typed JSON tool calls. Confirm-required by default.
No black box. No free-form chatter.

## SPEAKER NOTES
Three discipline choices that matter more than model selection. One: deterministic state machine. The orchestrator runs as a LangGraph DAG with seven named states: Idle, Listening, Deliberating, AwaitingConfirm, Executing, LoggingTrace, Cooldown. No state can be entered without a guarded transition. We can fuzz it with synthetic input fixtures committed to the repo. Two: typed JSON tool calls between agents. The LLM never produces free-form prose to talk to another agent. Every inter-agent call validates against a schema in orchestrator/tools.py. That kills hallucinated tool calls and lets us render the Reasoning Trace deterministically. Three: confirm-required by default. No non-trivial autonomous action without one user tap. The trace on the left is from a real stress-driven mute on Tuesday: Load Score crossed seventy from HRV and app-switch rate, candidate set ranked, mute selected, user tapped accept. The trace is local-only, immutable, and the user can inspect, edit, or reject every entry. That is the glass box.

## CITATIONS
[7] LangGraph, https://langchain-ai.github.io/langgraph/.
[4] Phi-3-mini, https://arxiv.org/abs/2404.14219.
[22] AutoGen tool-calling pattern reference, https://arxiv.org/abs/2308.08155.

## VISUAL BRIEF
Split layout. Cols 1-6 hold a single Reasoning Trace sample rendered as JetBrains Mono 16 pt code on #FAF8F5, no syntax-highlight colours except sunset-orange #FF5B2E on the keys chosen, rationale, and confirm_required. The trace is the eleven-step stress-driven mute from plan.md §11, collapsed to JSON, about 22 lines. Above the code block, kicker 18 pt sans tracked +40: ONE ACTION, ONE TRACE. Cols 7-12 hold a stack of three best-practice cards, each 540x220 px, separated by 24 px gap. Card 1 Deterministic state machine, with the seven-state list in mono 12 pt below. Card 2 Typed JSON tool calls, never free-form chat between agents. Card 3 Confirm-required by default, no autonomous action without one tap from user. Each card has a 1 px #0E0E0E top hairline, title in Fraunces 32 pt, body Inter Tight 18 pt. Reference: Stripe API docs JSON examples, Linear API reference.

## PERSUASION JOB
Convert the Engineer and Designer judges by making the Reasoning Trace JSON the artefact the team is remembered by.
