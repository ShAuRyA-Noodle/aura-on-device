"""Pytest suite for the on-device LLM adapters.

The fast tests (no ``@pytest.mark.slow``) exercise:

- The platform-detection / registry selection logic.
- That ``AdapterUnavailable`` is raised when a backend is missing.
- The prompt-template helpers.

The slow tests (marked with ``@pytest.mark.slow``) load Gemma 2B 4-bit
through MLX and run real inference. They are skipped automatically when
MLX is not installed or no Apple Silicon is detected.

Run with::

    pytest aura/models/llm/ -q --tb=line                  # fast only
    pytest aura/models/llm/ -q -m slow                    # slow only
    pytest aura/models/llm/ -q -m "not slow"              # CI default
"""

from __future__ import annotations

import asyncio
import importlib
import os
import time
from typing import Any

import pytest


# ---------------------------------------------------------------------------
# Module under test
# ---------------------------------------------------------------------------


from . import registry as registry_mod
from .prompts import (
    comms_rerank_prompt,
    finance_extract_prompt,
    rationale_prompt,
    safe_json_extract,
)


HAS_MLX = importlib.util.find_spec("mlx_lm") is not None
HAS_LLAMACPP = importlib.util.find_spec("llama_cpp") is not None


# ---------------------------------------------------------------------------
# Registry / selection logic
# ---------------------------------------------------------------------------


class TestRegistry:
    def test_known_models_listed(self) -> None:
        names = registry_mod.list_models()
        assert "gemma-2b-4bit" in names
        assert "phi-3-mini-4bit" in names
        assert "llama-3-8b-4bit" in names

    def test_unknown_model_raises(self) -> None:
        with pytest.raises(KeyError):
            registry_mod.get_adapter("does-not-exist")

    def test_apple_silicon_detection_returns_bool(self) -> None:
        assert isinstance(registry_mod.is_apple_silicon(), bool)

    def test_default_cache_dir_is_creatable(self, tmp_path, monkeypatch) -> None:
        monkeypatch.setenv("AURA_MODEL_CACHE", str(tmp_path / "cache"))
        path = registry_mod.default_cache_dir()
        assert path.exists()
        assert path.is_dir()

    def test_unknown_backend_raises(self) -> None:
        with pytest.raises(ValueError):
            registry_mod.get_adapter("gemma-2b-4bit", backend="nope")

    def test_llamacpp_missing_raises_unavailable(self) -> None:
        if HAS_LLAMACPP:
            pytest.skip("llama-cpp-python is installed; cannot test missing path")
        with pytest.raises(registry_mod.AdapterUnavailable):
            registry_mod.get_adapter("gemma-2b-4bit", backend="llamacpp")

    def test_mlx_missing_raises_unavailable(self) -> None:
        if HAS_MLX:
            pytest.skip("mlx_lm is installed; cannot test missing path")
        with pytest.raises(registry_mod.AdapterUnavailable):
            registry_mod.get_adapter("gemma-2b-4bit", backend="mlx")


# ---------------------------------------------------------------------------
# Prompt helpers
# ---------------------------------------------------------------------------


class TestPrompts:
    def test_comms_rerank_prompt_includes_message(self) -> None:
        p = comms_rerank_prompt(
            "@you can you confirm the schema diagram for the quiz",
            {"ACTIONABLE": 0.45, "SOCIAL": 0.40, "BROADCAST": 0.10, "SPAM": 0.05},
        )
        assert "ACTIONABLE" in p
        assert "schema diagram" in p
        assert "<start_of_turn>system" in p

    def test_finance_extract_prompt_round_trips_text(self) -> None:
        p = finance_extract_prompt("Sent Rs.450 to ZOMATO via UPI")
        assert "ZOMATO" in p
        assert "JSON" in p

    def test_rationale_prompt_targets_word_count(self) -> None:
        p = rationale_prompt(
            "SHOW_BRIEF",
            signals=[
                {"agent": "comms", "decision": "show_brief", "drivers": ["actionable_2"]},
                {"agent": "calendar", "decision": "leave_by", "drivers": ["travel_22"]},
            ],
            user_state={"load_score": 42, "wellness_state": "BASELINE"},
        )
        assert "30-50" in p
        assert "SHOW_BRIEF" in p

    def test_safe_json_extract_handles_fences(self) -> None:
        msg = 'okay here is the answer:```json\n{"a": 1, "b": "two"}\n```'
        obj = safe_json_extract(msg)
        assert obj == {"a": 1, "b": "two"}

    def test_safe_json_extract_returns_none_on_garbage(self) -> None:
        assert safe_json_extract("nothing here") is None
        assert safe_json_extract("") is None


# ---------------------------------------------------------------------------
# Slow tests — real MLX inference. Skipped if MLX not installed.
# ---------------------------------------------------------------------------


needs_mlx = pytest.mark.skipif(
    not (HAS_MLX and registry_mod.is_apple_silicon()),
    reason="MLX or Apple Silicon not available; slow inference tests skipped",
)


@pytest.mark.slow
@needs_mlx
class TestMLXLive:
    """Live MLX inference. Pulls Gemma 2B 4-bit on first run (~1.5 GB)."""

    @pytest.fixture(scope="class")
    def adapter(self) -> Any:
        return registry_mod.get_adapter("gemma-2b-4bit", backend="mlx")

    def test_generate_returns_nonempty(self, adapter) -> None:
        out = adapter.generate("Hello, my name is", max_tokens=8, temperature=0.0)
        assert isinstance(out, str)
        assert len(out.strip()) > 0

    def test_generate_latency_under_5s(self, adapter) -> None:
        # Warm-up so we measure steady-state, not first-load.
        adapter.generate("Hello", max_tokens=4)
        t0 = time.perf_counter()
        out = adapter.generate("Hello, my name is", max_tokens=32, temperature=0.0)
        elapsed = time.perf_counter() - t0
        assert out, "empty completion"
        assert elapsed < 5.0, f"32-token decode took {elapsed:.2f}s"

    def test_generate_stream_yields_incrementally(self, adapter) -> None:
        async def _consume() -> list[str]:
            chunks: list[str] = []
            async for piece in adapter.generate_stream(
                "Count to three:", max_tokens=12, temperature=0.0
            ):
                chunks.append(piece)
            return chunks

        chunks = asyncio.run(_consume())
        assert len(chunks) >= 2, "stream should produce >1 chunk for 12 tokens"
        assert sum(len(c) for c in chunks) > 0
