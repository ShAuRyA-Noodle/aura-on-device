"""llama.cpp adapter — cross-platform fallback (Linux / Windows / Android host).

Wraps `llama-cpp-python <https://github.com/abetlen/llama-cpp-python>`_
so the orchestrator can run on machines without Apple's MLX. The
adapter accepts a path to a GGUF Q4_K_M file produced by
``models/lora/merge_and_quantize.sh``.

Same contract as :class:`MLXAdapter` so :func:`registry.get_adapter`
returns a drop-in replacement when MLX is unavailable.
"""

from __future__ import annotations

import asyncio
import os
from typing import Any, AsyncIterator, Iterable, Optional

from .registry import AdapterUnavailable, LLMAdapter


try:  # pragma: no cover - import depends on host
    from llama_cpp import Llama as _Llama

    _LLAMA_OK = True
    _LLAMA_ERR: Optional[Exception] = None
except Exception as exc:  # pragma: no cover
    _LLAMA_OK = False
    _LLAMA_ERR = exc

    class _Llama:  # type: ignore[no-redef]
        def __init__(self, *args, **kwargs):
            raise AdapterUnavailable(
                "llama-cpp-python is not installed. Run "
                "`pip install llama-cpp-python` (CPU) or follow the "
                "Metal / CUDA build flags in the project README. "
                f"Original error: {_LLAMA_ERR}"
            )


class LlamaCppAdapter(LLMAdapter):
    """Backend for GGUF Q4_K_M weights via llama.cpp Python bindings.

    Parameters
    ----------
    model_path:
        Absolute path to a ``*.Q4_K_M.gguf`` file. Must exist on disk.
    name:
        Friendly nickname recorded in logs / traces.
    n_ctx:
        Context window size. 4096 is enough for the Aura agents
        (longest prompt is the morning-brief reasoning trace
        prompt, ~1.5k tokens).
    n_threads:
        CPU threads. ``None`` lets llama.cpp decide.
    n_gpu_layers:
        How many transformer layers to offload to GPU. ``-1`` =
        all-on-GPU (Metal on Mac, CUDA on Linux), ``0`` = CPU only.
    """

    def __init__(
        self,
        model_path: str,
        name: str = "llamacpp",
        n_ctx: int = 4096,
        n_threads: Optional[int] = None,
        n_gpu_layers: int = -1,
    ) -> None:
        if not _LLAMA_OK:
            raise AdapterUnavailable(
                "llama-cpp-python is not installed. Run "
                "`pip install llama-cpp-python`. "
                f"Original error: {_LLAMA_ERR}"
            )
        if not os.path.exists(model_path):
            raise AdapterUnavailable(
                f"GGUF model file not found: {model_path}. "
                "Run `bash models/lora/merge_and_quantize.sh <agent>` "
                "to produce one, or download a Q4_K_M GGUF and place it "
                "at this path."
            )

        self.name = name
        self.model_path = model_path
        self._n_ctx = int(n_ctx)
        self._n_threads = n_threads
        self._n_gpu_layers = int(n_gpu_layers)
        self._llm: Any = None

    # ------------------------------------------------------------------ #
    # Lazy load
    # ------------------------------------------------------------------ #

    def _ensure_loaded(self) -> None:
        if self._llm is not None:
            return
        kwargs: dict[str, Any] = {
            "model_path": self.model_path,
            "n_ctx": self._n_ctx,
            "n_gpu_layers": self._n_gpu_layers,
            "verbose": False,
        }
        if self._n_threads is not None:
            kwargs["n_threads"] = int(self._n_threads)
        self._llm = _Llama(**kwargs)

    # ------------------------------------------------------------------ #
    # Sync generate
    # ------------------------------------------------------------------ #

    def generate(
        self,
        prompt: str,
        max_tokens: int = 128,
        temperature: float = 0.0,
        stop: Optional[Iterable[str]] = None,
    ) -> str:
        self._ensure_loaded()
        stop_list = list(stop) if stop else None
        out = self._llm(
            prompt,
            max_tokens=int(max_tokens),
            temperature=float(temperature),
            stop=stop_list,
            echo=False,
            stream=False,
        )
        # llama-cpp returns a dict in OpenAI-completion shape.
        if isinstance(out, dict):
            try:
                return out["choices"][0]["text"]
            except (KeyError, IndexError):  # pragma: no cover - defensive
                return str(out)
        return str(out)

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
        self._ensure_loaded()
        stop_list = list(stop) if stop else None

        # llama-cpp's streaming yields dicts in OpenAI-completion shape.
        # We trampoline through an executor so the asyncio loop stays free.
        loop = asyncio.get_running_loop()

        def _build() -> Any:
            return self._llm(
                prompt,
                max_tokens=int(max_tokens),
                temperature=float(temperature),
                stop=stop_list,
                echo=False,
                stream=True,
            )

        gen = await loop.run_in_executor(None, _build)
        sentinel = object()

        def _next() -> Any:
            try:
                return next(gen)
            except StopIteration:
                return sentinel

        while True:
            chunk = await loop.run_in_executor(None, _next)
            if chunk is sentinel:
                break
            try:
                piece = chunk["choices"][0]["text"]
            except (KeyError, IndexError, TypeError):  # pragma: no cover
                continue
            if piece:
                yield piece

    # ------------------------------------------------------------------ #
    # Diagnostics
    # ------------------------------------------------------------------ #

    def info(self) -> dict[str, Any]:
        return {
            "backend": "llamacpp",
            "name": self.name,
            "model_path": self.model_path,
            "n_ctx": self._n_ctx,
            "n_gpu_layers": self._n_gpu_layers,
            "loaded": self._llm is not None,
        }
