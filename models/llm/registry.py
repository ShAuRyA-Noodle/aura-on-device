"""Adapter registry — picks MLX on Apple Silicon, llama.cpp elsewhere.

The registry exposes a tiny abstract ``LLMAdapter`` protocol plus a
single entry point ``get_adapter(name)`` that returns a ready-to-use
adapter for a known model nickname.

Selection logic
---------------
1. If the caller passes ``backend="mlx"`` or ``backend="llamacpp"``
   we honour it (used by tests and benchmarks that pin the runtime).
2. Otherwise we auto-detect:

   * Apple Silicon (``platform.machine() == "arm64"`` and
     ``platform.system() == "Darwin"``) -> MLX.
   * Anything else -> llama.cpp.
3. If the chosen backend's package is missing we raise
   :class:`AdapterUnavailable`. Agents catch that and fall back to
   their deterministic non-LLM path.

Model nicknames
---------------
- ``gemma-2b-4bit``  -> MLX: ``mlx-community/gemma-2-2b-it-4bit``,
                       GGUF: ``models/exports/gemma-2b-aura-comms.Q4_K_M.gguf``
                       or any local Gemma 2B Q4_K_M.
- ``phi-3-mini-4bit`` -> MLX: ``mlx-community/Phi-3-mini-4k-instruct-4bit``,
                         GGUF: a Phi-3-mini Q4_K_M file shipped with the build.
- ``llama-3-8b-4bit`` -> heavy fallback for tier-A devices (16 GB+).

Override the model path with the ``AURA_MODEL_<NAME>`` env var, e.g.::

    AURA_MODEL_GEMMA_2B_4BIT=/path/to/local/mlx_model

Disk paths default to ``~/.cache/aura/models/`` so iOS bundling
(see README) and CI can share the same convention.
"""

from __future__ import annotations

import abc
import os
import platform
from dataclasses import dataclass
from pathlib import Path
from typing import AsyncIterator, Iterable, Optional


class AdapterUnavailable(RuntimeError):
    """Raised when a requested backend is not installed on this host."""


class LLMAdapter(abc.ABC):
    """Common contract for MLX + llama.cpp adapters.

    The contract is intentionally narrow: every agent only needs
    ``generate`` (sync) and ``generate_stream`` (async). Anything fancier
    (KV cache reuse, batched decode, speculative decoding) is the
    adapter's private business.
    """

    name: str
    model_path: str

    @abc.abstractmethod
    def generate(
        self,
        prompt: str,
        max_tokens: int = 128,
        temperature: float = 0.0,
        stop: Optional[Iterable[str]] = None,
    ) -> str:
        """Synchronous generation. Returns the decoded completion text."""

    @abc.abstractmethod
    def generate_stream(
        self,
        prompt: str,
        max_tokens: int = 128,
        temperature: float = 0.0,
        stop: Optional[Iterable[str]] = None,
    ) -> AsyncIterator[str]:
        """Async generator yielding decoded tokens one piece at a time."""


# ---------------------------------------------------------------------------
# Model registry
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class ModelSpec:
    """How to find / fetch a model under each backend."""

    nickname: str
    mlx_repo: str           # huggingface repo id used by mlx_lm
    gguf_relative: str      # relative GGUF path under exports / cache
    description: str
    approx_disk_gb: float
    approx_ram_gb: float


REGISTRY: dict[str, ModelSpec] = {
    "gemma-2b-4bit": ModelSpec(
        nickname="gemma-2b-4bit",
        mlx_repo="mlx-community/gemma-2-2b-it-4bit",
        gguf_relative="gemma-2b-aura-comms.Q4_K_M.gguf",
        description="Gemma 2B Instruct 4-bit. Default for Comms + Finance.",
        approx_disk_gb=1.5,
        approx_ram_gb=2.0,
    ),
    "phi-3-mini-4bit": ModelSpec(
        nickname="phi-3-mini-4bit",
        mlx_repo="mlx-community/Phi-3-mini-4k-instruct-4bit",
        gguf_relative="phi-3-mini-4k-instruct.Q4_K_M.gguf",
        description="Phi-3-mini 4k Instruct 4-bit. Orchestrator default.",
        approx_disk_gb=2.3,
        approx_ram_gb=3.0,
    ),
    "llama-3-8b-4bit": ModelSpec(
        nickname="llama-3-8b-4bit",
        mlx_repo="mlx-community/Meta-Llama-3-8B-Instruct-4bit",
        gguf_relative="Meta-Llama-3-8B-Instruct.Q4_K_M.gguf",
        description="Llama-3-8B Instruct 4-bit. Heavy fallback (≥16 GB RAM).",
        approx_disk_gb=4.7,
        approx_ram_gb=6.0,
    ),
}


# ---------------------------------------------------------------------------
# Platform detection
# ---------------------------------------------------------------------------


def is_apple_silicon() -> bool:
    """True on M-series Mac. Used to pick the MLX backend."""
    return platform.system() == "Darwin" and platform.machine() == "arm64"


def default_cache_dir() -> Path:
    """``~/.cache/aura/models``, created on demand."""
    base = Path(os.environ.get("AURA_MODEL_CACHE", "~/.cache/aura/models"))
    base = base.expanduser()
    base.mkdir(parents=True, exist_ok=True)
    return base


def project_exports_dir() -> Path:
    """``aura/models/exports`` — checked second when the cache is empty."""
    return Path(__file__).resolve().parents[1] / "exports"


def _env_override(nickname: str) -> Optional[str]:
    key = "AURA_MODEL_" + nickname.upper().replace("-", "_")
    val = os.environ.get(key)
    return val or None


def _resolve_mlx_path(spec: ModelSpec) -> str:
    """Return either a HF repo id (mlx_lm will fetch) or a local dir."""
    override = _env_override(spec.nickname)
    if override:
        return override

    cached = default_cache_dir() / spec.nickname
    if cached.is_dir() and any(cached.iterdir()):
        return str(cached)
    # mlx_lm.load() accepts a HF repo id and caches into ~/.cache/huggingface.
    return spec.mlx_repo


def _resolve_gguf_path(spec: ModelSpec) -> str:
    override = _env_override(spec.nickname)
    if override:
        return override
    # Prefer locally exported, fall back to user cache.
    p = project_exports_dir() / spec.gguf_relative
    if p.is_file():
        return str(p)
    return str(default_cache_dir() / spec.gguf_relative)


# ---------------------------------------------------------------------------
# Public factory
# ---------------------------------------------------------------------------


def get_adapter(
    name: str,
    backend: Optional[str] = None,
) -> LLMAdapter:
    """Return a ready ``LLMAdapter`` for the given model nickname.

    Parameters
    ----------
    name:
        One of the keys in :data:`REGISTRY` (e.g. ``"gemma-2b-4bit"``).
    backend:
        ``"mlx"``, ``"llamacpp"`` or ``None`` (auto-detect).

    Raises
    ------
    KeyError
        Unknown nickname.
    AdapterUnavailable
        Backend selected but its package is missing on this host.
    """
    if name not in REGISTRY:
        raise KeyError(f"unknown model nickname: {name}")
    spec = REGISTRY[name]

    chosen = backend
    if chosen is None:
        chosen = "mlx" if is_apple_silicon() else "llamacpp"

    if chosen == "mlx":
        try:
            from .mlx_adapter import MLXAdapter
        except AdapterUnavailable:
            raise
        except Exception as exc:  # pragma: no cover - import-time issues
            raise AdapterUnavailable(f"MLX import failed: {exc}") from exc
        return MLXAdapter(model_path=_resolve_mlx_path(spec), name=name)

    if chosen == "llamacpp":
        try:
            from .llamacpp_adapter import LlamaCppAdapter
        except AdapterUnavailable:
            raise
        except Exception as exc:  # pragma: no cover
            raise AdapterUnavailable(
                f"llama-cpp-python import failed: {exc}"
            ) from exc
        return LlamaCppAdapter(model_path=_resolve_gguf_path(spec), name=name)

    raise ValueError(f"unknown backend: {chosen}")


def list_models() -> list[str]:
    """Convenience for tests / docs."""
    return sorted(REGISTRY.keys())
