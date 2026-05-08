"""On-device LLM inference adapters for Aura.

This package wires real on-device inference into Aura's agents and
orchestrator. Two adapters share a single contract (``LLMAdapter``):

- :class:`MLXAdapter` — Apple Silicon (M-series Mac, iOS dev). Uses
  ``mlx`` and ``mlx_lm`` against 4-bit quantised weights downloaded
  to ``~/.cache/aura/models/<name>``.
- :class:`LlamaCppAdapter` — cross-platform fallback for Linux / Windows
  / Android-host. Uses ``llama-cpp-python`` against GGUF Q4_K_M weights.

Selection happens through :func:`registry.get_adapter`, which picks
MLX on Apple Silicon and llama.cpp elsewhere. See
``models/llm/README.md`` for the full setup.
"""

from .registry import (
    LLMAdapter,
    AdapterUnavailable,
    get_adapter,
    is_apple_silicon,
)

__all__ = [
    "LLMAdapter",
    "AdapterUnavailable",
    "get_adapter",
    "is_apple_silicon",
]
