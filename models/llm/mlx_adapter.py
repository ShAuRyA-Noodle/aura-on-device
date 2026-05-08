"""MLX adapter — Apple Silicon path.

Wraps :mod:`mlx_lm` so the rest of Aura can stay backend-agnostic.
The adapter does no caching of decoded text — that is the agent's job.
What it does cache is the loaded ``(model, tokenizer)`` pair, since
``mlx_lm.load`` takes ~3-5 s on first call for Gemma 2B 4-bit.

Why not async?
--------------
``mlx_lm.stream_generate`` is a synchronous Python generator. The
``generate_stream`` async iterator below trampolines each step through
``asyncio.to_thread`` so callers can ``async for`` without blocking the
loop. That keeps the contract identical to the llama.cpp adapter.

Real MLX calls only — no mocking at this layer.
"""

from __future__ import annotations

import asyncio
import os
from typing import Any, AsyncIterator, Iterable, Optional

from .registry import AdapterUnavailable, LLMAdapter


try:  # pragma: no cover - import depends on host
    from mlx_lm import load as _mlx_load
    from mlx_lm import stream_generate as _mlx_stream_generate

    try:
        from mlx_lm.sample_utils import make_sampler as _make_sampler
    except Exception:  # older mlx_lm versions
        _make_sampler = None  # type: ignore[assignment]

    _MLX_OK = True
    _MLX_ERR: Optional[Exception] = None
except Exception as exc:  # pragma: no cover
    _MLX_OK = False
    _MLX_ERR = exc
    _make_sampler = None  # type: ignore[assignment]

    def _mlx_load(*args, **kwargs):  # type: ignore[no-redef]
        raise AdapterUnavailable(
            "mlx_lm is not installed. Run `pip install mlx mlx-lm`. "
            f"Original error: {_MLX_ERR}"
        )

    def _mlx_stream_generate(*args, **kwargs):  # type: ignore[no-redef]
        raise AdapterUnavailable("mlx_lm not installed")


class MLXAdapter(LLMAdapter):
    """MLX-backed adapter for ``mlx-community`` 4-bit checkpoints.

    Parameters
    ----------
    model_path:
        Either a local directory under ``~/.cache/aura/models/<name>``,
        a HuggingFace repo id (``mlx-community/...``), or any path
        ``mlx_lm.load`` accepts.
    name:
        Friendly nickname recorded in logs / traces.
    """

    def __init__(self, model_path: str, name: str = "mlx") -> None:
        if not _MLX_OK:
            raise AdapterUnavailable(
                "mlx_lm import failed. Install with `pip install mlx mlx-lm`. "
                f"Original error: {_MLX_ERR}"
            )
        self.name = name
        self.model_path = model_path
        self._model: Any = None
        self._tokenizer: Any = None

    # ------------------------------------------------------------------ #
    # Lazy load
    # ------------------------------------------------------------------ #

    def _ensure_loaded(self) -> None:
        if self._model is not None:
            return
        # mlx_lm.load auto-resolves a HF repo id or a local dir.
        self._model, self._tokenizer = _mlx_load(self.model_path)

    # ------------------------------------------------------------------ #
    # Sync generate
    # ------------------------------------------------------------------ #

    def _build_kwargs(self, max_tokens: int, temperature: float) -> dict[str, Any]:
        """Map our (max_tokens, temperature) onto current ``mlx_lm`` kwargs.

        ``mlx_lm`` 0.20+ replaced the legacy ``temp=`` kwarg with a
        sampler factory. We feature-detect at import time and build the
        appropriate kwargs here so the adapter works against both.
        """
        kwargs: dict[str, Any] = {"max_tokens": int(max_tokens)}
        if _make_sampler is not None:
            kwargs["sampler"] = _make_sampler(temp=float(temperature or 0.0))
        else:
            kwargs["temp"] = float(temperature or 0.0)
        return kwargs

    def generate(
        self,
        prompt: str,
        max_tokens: int = 128,
        temperature: float = 0.0,
        stop: Optional[Iterable[str]] = None,
    ) -> str:
        """Run a synchronous decode and return the completion text."""
        self._ensure_loaded()
        kwargs = self._build_kwargs(max_tokens, temperature)

        # Use stream_generate so we can apply stop strings ourselves.
        # mlx_lm.generate does not natively support stop strings.
        accum = ""
        for resp in _mlx_stream_generate(
            self._model, self._tokenizer, prompt=prompt, **kwargs
        ):
            piece = getattr(resp, "text", "")
            if piece:
                accum += piece
                if stop and any(s and s in accum for s in stop):
                    # Trim at the earliest stop occurrence and break.
                    earliest = min(
                        (accum.find(s), s) for s in stop if s and accum.find(s) >= 0
                    )
                    cut_at = earliest[0]
                    return accum[:cut_at]
        return accum

    # ------------------------------------------------------------------ #
    # Async stream
    # ------------------------------------------------------------------ #

    async def generate_stream(
        self,
        prompt: str,
        max_tokens: int = 128,
        temperature: float = 0.0,
        stop: Optional[Iterable[str]] = None,
    ) -> AsyncIterator[str]:
        """Yield decoded token segments one at a time.

        Each yielded item is the latest text segment from MLX
        (typically one or a few characters per step).
        """
        self._ensure_loaded()
        kwargs = self._build_kwargs(max_tokens, temperature)

        # Build the synchronous generator once, then pull from it inside a
        # worker thread so we don't block the asyncio loop.
        gen = _mlx_stream_generate(
            self._model, self._tokenizer, prompt=prompt, **kwargs
        )

        loop = asyncio.get_running_loop()
        sentinel = object()

        def _next() -> Any:
            try:
                return next(gen)
            except StopIteration:
                return sentinel

        accum = ""
        while True:
            resp = await loop.run_in_executor(None, _next)
            if resp is sentinel:
                break
            piece = getattr(resp, "text", "") or ""
            if not piece:
                continue
            accum += piece
            if stop and any(s and s in accum for s in stop):
                # Trim and stop.
                earliest = min(
                    (accum.find(s), s) for s in stop if s and accum.find(s) >= 0
                )
                cut_at = earliest[0]
                trimmed = accum[:cut_at]
                # Yield only the remainder of the trimmed text.
                # The caller may have already received earlier pieces;
                # we yield an empty string here to signal "done".
                already = len(accum) - len(piece)
                if cut_at > already:
                    yield trimmed[already:]
                return
            yield piece

    # ------------------------------------------------------------------ #
    # Diagnostics
    # ------------------------------------------------------------------ #

    def info(self) -> dict[str, Any]:
        """Expose a small JSON-friendly diagnostics dict."""
        return {
            "backend": "mlx",
            "name": self.name,
            "model_path": self.model_path,
            "loaded": self._model is not None,
            "host_pid": os.getpid(),
        }
