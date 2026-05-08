"""Real on-device LLM latency benchmark.

Measures, for each of the registered 4-bit quantised models:

- First-token latency (time from ``generate_stream`` start to first
  yielded text segment).
- Steady-state tokens-per-second over a 32-token decode.
- Peak resident-set memory (via ``psutil``) before/after the run.

Writes a JSON report to
``aura/benchmarks/results/llm_latency_<YYYY-MM-DD>.json``.

Usage::

    python -m aura.benchmarks.llm_latency
    python -m aura.benchmarks.llm_latency --runs 30 --models gemma-2b-4bit

Llama-3-8B is benchmarked only when the host has ≥16 GB RAM.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import math
import os
import statistics
import sys
import time
from datetime import date
from pathlib import Path
from typing import Any, Dict, List, Optional


# Allow `python -m aura.benchmarks.llm_latency` and direct execution.
sys.path.insert(0, str(Path(__file__).resolve().parents[1].parent))

import psutil  # type: ignore  # noqa: E402

from aura.models.llm import (  # type: ignore  # noqa: E402
    AdapterUnavailable,
    get_adapter,
    is_apple_silicon,
)
from aura.models.llm.registry import REGISTRY  # type: ignore  # noqa: E402


PROMPT = "Hello, my name is"
MAX_TOKENS = 32


def _peak_rss_gb() -> float:
    proc = psutil.Process(os.getpid())
    return proc.memory_info().rss / (1024 ** 3)


def _ci95_halfwidth(samples: List[float]) -> float:
    if len(samples) < 2:
        return 0.0
    sd = statistics.stdev(samples)
    return 1.96 * sd / math.sqrt(len(samples))


async def _measure_first_token(adapter, prompt: str) -> tuple[float, int, str]:
    """Drive ``generate_stream`` and time the very first non-empty piece."""
    start = time.perf_counter()
    first = None
    n_pieces = 0
    accum: List[str] = []
    async for piece in adapter.generate_stream(
        prompt, max_tokens=MAX_TOKENS, temperature=0.0
    ):
        if first is None and piece.strip():
            first = time.perf_counter() - start
        n_pieces += 1
        accum.append(piece)
    if first is None:
        first = time.perf_counter() - start
    return first, n_pieces, "".join(accum)


def _measure_run(adapter, prompt: str) -> Dict[str, float]:
    """One benchmark run. Returns ms / tokens / tps."""
    t0 = time.perf_counter()
    first_token_ms, n_pieces, _text = asyncio.run(_measure_first_token(adapter, prompt))
    total_s = time.perf_counter() - t0
    # Tokens-per-second is approximated as decoded pieces / wall clock.
    tps = n_pieces / total_s if total_s > 0 else 0.0
    return {
        "first_token_ms": first_token_ms * 1000.0,
        "total_ms": total_s * 1000.0,
        "tokens_decoded": n_pieces,
        "tokens_per_sec": tps,
    }


def _bench_one(
    nickname: str,
    runs: int,
    warmup: int,
    backend: Optional[str] = None,
) -> Dict[str, Any]:
    """Bench a single model. Returns a results dict (no exception on failure)."""
    rec: Dict[str, Any] = {
        "model": nickname,
        "runs": runs,
        "warmup": warmup,
    }
    try:
        adapter = get_adapter(nickname, backend=backend)
    except AdapterUnavailable as exc:
        rec["error"] = f"adapter unavailable: {exc}"
        return rec
    except Exception as exc:  # pragma: no cover
        rec["error"] = f"adapter init failed: {exc}"
        return rec

    rec["backend"] = getattr(adapter, "info", lambda: {})().get("backend", "?")
    rec["model_path"] = adapter.model_path

    rss_before = _peak_rss_gb()
    try:
        # Warm-up — first run loads weights so we exclude it from stats.
        for _ in range(max(0, warmup)):
            _measure_run(adapter, PROMPT)

        first_token_ms: List[float] = []
        tps_samples: List[float] = []
        decoded: List[int] = []
        for _ in range(runs):
            r = _measure_run(adapter, PROMPT)
            first_token_ms.append(r["first_token_ms"])
            tps_samples.append(r["tokens_per_sec"])
            decoded.append(int(r["tokens_decoded"]))
    except Exception as exc:  # pragma: no cover
        rec["error"] = f"benchmark failed: {exc}"
        return rec

    rss_after = _peak_rss_gb()

    rec.update({
        "first_token_ms_mean": statistics.fmean(first_token_ms),
        "first_token_ms_ci95": _ci95_halfwidth(first_token_ms),
        "first_token_ms_p50": statistics.median(first_token_ms),
        "first_token_ms_p95": (
            statistics.quantiles(first_token_ms, n=20)[18]
            if len(first_token_ms) >= 20
            else max(first_token_ms)
        ),
        "tokens_per_sec_mean": statistics.fmean(tps_samples),
        "tokens_per_sec_ci95": _ci95_halfwidth(tps_samples),
        "tokens_decoded_mean": statistics.fmean(decoded),
        "rss_gb_before": rss_before,
        "rss_gb_after": rss_after,
        "rss_gb_delta": rss_after - rss_before,
    })
    return rec


def _has_enough_ram_for_8b() -> bool:
    return psutil.virtual_memory().total / (1024 ** 3) >= 16.0


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Aura on-device LLM latency benchmark.")
    parser.add_argument(
        "--runs",
        type=int,
        default=int(os.environ.get("AURA_BENCH_RUNS", "100")),
    )
    parser.add_argument("--warmup", type=int, default=2)
    parser.add_argument(
        "--models",
        nargs="*",
        default=None,
        help="Subset of nicknames; default = all that fit on this host.",
    )
    parser.add_argument(
        "--backend",
        default=None,
        choices=("mlx", "llamacpp"),
        help="Pin the backend (default: auto).",
    )
    parser.add_argument(
        "--out",
        default=None,
        help="Output JSON path (default: benchmarks/results/llm_latency_<DATE>.json).",
    )
    args = parser.parse_args(argv)

    targets = args.models or ["gemma-2b-4bit", "phi-3-mini-4bit"]
    if "llama-3-8b-4bit" not in targets and _has_enough_ram_for_8b():
        targets.append("llama-3-8b-4bit")

    results: List[Dict[str, Any]] = []
    for nickname in targets:
        if nickname not in REGISTRY:
            results.append({"model": nickname, "error": "unknown nickname"})
            continue
        print(f"[bench] {nickname} ...", flush=True)
        rec = _bench_one(nickname, args.runs, args.warmup, args.backend)
        results.append(rec)
        if "error" in rec:
            print(f"[bench]   error: {rec['error']}")
        else:
            print(
                f"[bench]   first-token mean = {rec['first_token_ms_mean']:.1f} ms  "
                f"tps = {rec['tokens_per_sec_mean']:.1f}"
            )

    out_path = Path(
        args.out
        or Path(__file__).resolve().parent
        / "results"
        / f"llm_latency_{date.today().isoformat()}.json"
    )
    out_path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "date": date.today().isoformat(),
        "host": {
            "platform": sys.platform,
            "apple_silicon": is_apple_silicon(),
            "ram_gb_total": psutil.virtual_memory().total / (1024 ** 3),
            "cpu_count": psutil.cpu_count(logical=False),
        },
        "prompt": PROMPT,
        "max_tokens": MAX_TOKENS,
        "results": results,
    }
    out_path.write_text(json.dumps(payload, indent=2))
    print(f"[bench] wrote {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
