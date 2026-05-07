---
slide: 8
title: AI / GenAI / Agentic tools used / developed
---
## BODY
Six tools. Two built by us. Four open.
LangGraph state machine. sqlite-vss memory. MediaPipe and llama.cpp runtimes. PEFT for LoRA. ExecuTorch for Android prod.

## SPEAKER NOTES
Six tools. The two with the orange edge are the ones we extend ourselves. LangGraph runs the orchestrator as a deterministic state machine: Idle, Listening, Deliberating, AwaitingConfirm, Executing, LoggingTrace, Cooldown. Every transition is guarded. We can fuzz it. sqlite-vss is the on-device vector store inside the encrypted memory graph. We built the schema, the typed node and edge model, the Merkle audit log, and the per-day root display. MediaPipe LLM Inference is our Android runtime for the Q4 models. llama.cpp is our cross-platform fallback with Swift bindings on iOS. PEFT plus QLoRA at rank sixteen is the training pipeline, runs locally on the Alienware RTX 4080, no cloud GPU spend. ExecuTorch is the production Android target evaluated as a successor to MediaPipe LLM. Cursor and Claude Code are the development glue for code generation. Nothing here is exotic. The discipline is in the glue, typed JSON tool schemas between agents, never free-form chat.

## CITATIONS
[7] LangGraph, https://langchain-ai.github.io/langgraph/.
[10] MediaPipe LLM Inference, https://ai.google.dev/edge/mediapipe/solutions/genai/llm_inference.
[19] llama.cpp, https://github.com/ggml-org/llama.cpp.
[20] ExecuTorch, https://pytorch.org/executorch/.
[21] CrewAI reference, https://docs.crewai.com/.
[22] AutoGen tool-calling reference, https://arxiv.org/abs/2308.08155.
PEFT Hugging Face reference and sqlite-vss [TEAM TO VERIFY exact URLs].

## VISUAL BRIEF
Bento grid, six tiles, three rows by two columns. Each tile 800 px wide x 200 px tall. Inside each tile: tool name in Fraunces 32 pt top-left, one-line role in Inter Tight 18 pt directly under, then a 14 pt mono row showing the call-site or class. The orchestrator-related tiles LangGraph and sqlite-vss carry a 4 px sunset-orange top edge, mirroring the architecture diagram. Other tiles are neutral. Tile separators are 16 px gaps, no card strokes, no shadows. Six tiles: LangGraph deterministic state machine / MediaPipe LLM Inference Android runtime / sqlite-vss vector store on-device encrypted / llama.cpp cross-platform inference / PEFT LoRA training pipeline QLoRA r=16 local RTX 4080 / ExecuTorch production Android target. Bottom strip 14 pt sans colour key: team-built / open-source / vendor-licensed / trained by us. Reference: GitHub README badges page, Linear engineering blog tile layout.

## PERSUASION JOB
Engineering taste signal: name the exact glue, not generic AI agents and orchestration.
