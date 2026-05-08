"""MemoryGraph throughput benchmark.

Measures four real workloads against an on-disk MemoryGraph:

* node insertion + audit chain append, batched
* embedding insertion (uses the active embedder — sentence-transformers
  when installed, hash-bucket otherwise)
* semantic search latency
* daily Merkle root computation over the day's audit log

Outputs:
    benchmarks/results/memory_YYYY-MM-DD.json

Run as a script:
    python benchmarks/memory_throughput.py
"""

from __future__ import annotations

import json
import statistics
import sys
import tempfile
import time
from datetime import date as _date
from pathlib import Path
from typing import Dict


_REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_REPO))

from memory.store import MemoryGraph  # noqa: E402

_RESULTS_DIR = _REPO / "benchmarks" / "results"


_TEXTS = [
    "Anu confirmed schema diagram for DSA quiz",
    "Manish asked about hostel mess timing change",
    "Riya sent zomato receipt for biriyani 480 rupees",
    "Kabir wants to nap before evening lab",
    "Mira escalated the algo assignment due tomorrow",
] * 20  # 100 chunks


def measure(path: str) -> Dict[str, float]:
    g = MemoryGraph(path=path)

    # --- node-insert throughput ----------------------------------------
    t0 = time.perf_counter()
    nodes = []
    for i in range(200):
        nid = g.add_node("Conversation", {"summary": _TEXTS[i % len(_TEXTS)]})
        nodes.append(nid)
    node_dt = time.perf_counter() - t0
    node_per_s = 200.0 / node_dt

    # --- embedding throughput (single-text encode + insert) -------------
    t0 = time.perf_counter()
    for i, nid in enumerate(nodes[:100]):
        g.add_embedding(nid, 0, _TEXTS[i % len(_TEXTS)])
    emb_dt = time.perf_counter() - t0
    emb_per_s = 100.0 / emb_dt

    # --- search latency -------------------------------------------------
    samples_ms = []
    for q in (
        "schema diagram quiz",
        "hostel mess timing",
        "zomato receipt",
        "nap before lab",
    ) * 4:
        t0 = time.perf_counter()
        g.search(q, k=5)
        samples_ms.append((time.perf_counter() - t0) * 1000.0)
    samples_ms.sort()
    search_p50 = statistics.median(samples_ms)
    search_p95 = samples_ms[int(0.95 * (len(samples_ms) - 1))]

    # --- daily Merkle ---------------------------------------------------
    t0 = time.perf_counter()
    root = g.daily_merkle_root()
    merkle_ms = (time.perf_counter() - t0) * 1000.0

    # --- embedding-dim verification -------------------------------------
    sample_vec = g.embed("dimension probe sentence")

    g.close()

    return {
        "node_insert_per_s": node_per_s,
        "node_insert_dt_s": node_dt,
        "embedding_insert_per_s": emb_per_s,
        "embedding_insert_dt_s": emb_dt,
        "search_p50_ms": search_p50,
        "search_p95_ms": search_p95,
        "search_n": float(len(samples_ms)),
        "merkle_compute_ms": merkle_ms,
        "merkle_root_len": float(len(root)),
        "embedding_dim": float(len(sample_vec)),
        "vss_loaded": float(g._vss_loaded),
        "embedder_kind": 1.0 if g._embedder_kind == "minilm" else 0.0,
        "backend_sqlcipher": 1.0 if g.backend == "sqlcipher" else 0.0,
    }


def main() -> Dict[str, float]:
    with tempfile.TemporaryDirectory() as td:
        db_path = str(Path(td) / "aura_bench.db")
        stats = measure(db_path)

    _RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    out_path = _RESULTS_DIR / f"memory_{_date.today().isoformat()}.json"
    with out_path.open("w") as f:
        json.dump({"benchmark": "memory_throughput", **stats}, f, indent=2)

    print(
        f"node_insert/s={stats['node_insert_per_s']:.1f}  "
        f"emb_insert/s={stats['embedding_insert_per_s']:.1f}  "
        f"search p50={stats['search_p50_ms']:.2f}ms p95={stats['search_p95_ms']:.2f}ms  "
        f"merkle={stats['merkle_compute_ms']:.2f}ms  "
        f"dim={int(stats['embedding_dim'])}"
    )
    print(f"Wrote {out_path}")
    if int(stats["embedding_dim"]) != 384:
        raise SystemExit(f"FAIL: embedding dim {stats['embedding_dim']} != 384")
    return stats


if __name__ == "__main__":
    main()
