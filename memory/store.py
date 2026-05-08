"""MemoryGraph — SQLite + (optional) sqlite-vss memory store.

Implements technical_spec.md §6 + §14.

Design notes
------------
- SQLite stdlib driver. WAL journal mode + foreign keys ON.
- Embeddings: prefer ``sentence-transformers`` ``all-MiniLM-L6-v2`` (384d).
  The model is loaded lazily on first embed() call and cached on disk under
  ``$AURA_MODEL_CACHE`` (default ``~/.cache/aura/models/``). When the package
  isn't installed (clean CI env) we fall back to a deterministic hash-bucket
  embedding — same shape, worse model — so `search` keeps returning ranked
  hits. Set ``AURA_MEMORY_FORCE_HASH_EMBED=1`` to skip the heavy load (used
  by tests).
- sqlite-vss: production-loaded via the ``sqlite_vss`` Python package, which
  ships pre-built ``vss0`` + ``vector0`` extensions for macOS arm64. See the
  README for the manual install path on systems without the wheel.
- SQLCipher: best-effort encryption-at-rest via ``pysqlcipher3``. When that
  is unavailable we log a runtime warning and fall back to plain ``sqlite3``.
- Audit log: every write call appends a row whose ``hash_chain`` is
  ``sha256(prev_hash || canonical(row))``. Tamper-evident per spec.
- Daily Merkle root: computed at midnight (or on demand for tests) over the
  day's audit_log rows; stored in ``merkle_daily``.
"""

from __future__ import annotations

import json
import logging
import math
import os
import sqlite3
import time
import uuid
import warnings
from dataclasses import dataclass, field
from datetime import date as _date, datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple

from .audit import chain_next, compute_daily_merkle, hash_canonical


logger = logging.getLogger(__name__)

_PACKAGE_DIR = Path(__file__).resolve().parent
_SCHEMA_SQL = (_PACKAGE_DIR / "schema.sql").read_text()
_DEFAULT_MODEL_CACHE = Path(
    os.environ.get("AURA_MODEL_CACHE", os.path.expanduser("~/.cache/aura/models"))
)


# ---------------------------------------------------------------------------
# Embedding backend
# ---------------------------------------------------------------------------


def _try_sentence_transformers(cache_dir: Path = _DEFAULT_MODEL_CACHE):
    """Load all-MiniLM-L6-v2 with on-disk caching.

    The model is downloaded once into ``cache_dir`` and reused on subsequent
    runs. Returns ``None`` (and logs a warning) when the package isn't
    available — callers must fall back to :func:`_hash_bucket_embed`.
    """

    if os.environ.get("AURA_MEMORY_FORCE_HASH_EMBED") == "1":
        return None
    try:  # pragma: no cover - optional heavy dep
        cache_dir.mkdir(parents=True, exist_ok=True)
        os.environ.setdefault("SENTENCE_TRANSFORMERS_HOME", str(cache_dir))
        from sentence_transformers import SentenceTransformer  # type: ignore

        return SentenceTransformer(
            "sentence-transformers/all-MiniLM-L6-v2", cache_folder=str(cache_dir)
        )
    except Exception as exc:  # pragma: no cover - dep missing or offline
        logger.warning(
            "sentence-transformers unavailable (%s); falling back to hash-bucket embeddings.",
            exc,
        )
        return None


def _hash_bucket_embed(text: str, dim: int = 384) -> List[float]:
    """Deterministic hashing trick to produce a 384-d unit vector.

    Not a real embedding — but: deterministic, dependency-free, and good
    enough to keep the `search` API exercised in tests when the heavy model
    is intentionally skipped (``AURA_MEMORY_FORCE_HASH_EMBED=1``).
    """
    import hashlib

    vec = [0.0] * dim
    tokens = [t.lower() for t in text.split() if t]
    if not tokens:
        return vec
    for tok in tokens:
        h = hashlib.sha256(tok.encode("utf-8")).digest()
        # Use first 8 bytes for bucket, next 4 bytes for sign.
        bucket = int.from_bytes(h[:4], "big") % dim
        sign = -1.0 if (h[4] & 1) else 1.0
        vec[bucket] += sign
    norm = math.sqrt(sum(v * v for v in vec)) or 1.0
    return [v / norm for v in vec]


def _cosine(a: Sequence[float], b: Sequence[float]) -> float:
    num = sum(x * y for x, y in zip(a, b))
    da = math.sqrt(sum(x * x for x in a)) or 1.0
    db = math.sqrt(sum(y * y for y in b)) or 1.0
    return num / (da * db)


# ---------------------------------------------------------------------------
# Try sqlite-vss extension
# ---------------------------------------------------------------------------


def _try_load_vss(conn: sqlite3.Connection) -> bool:
    """Best-effort load of the sqlite-vss ``vss0`` extension.

    Strategy, in order of preference:

    1. ``sqlite_vss`` Python package — ships pre-built ``vector0`` + ``vss0``
       extensions for macOS arm64 / x86_64 and Linux x86_64. This is what
       production runs.
    2. ``vss0.dylib`` shipped next to this package (manual install).
    3. ``vss0`` on the system extension search path.

    Returns ``True`` on success; ``False`` triggers the local cosine fallback.
    """

    try:
        conn.enable_load_extension(True)  # type: ignore[attr-defined]
    except (sqlite3.OperationalError, AttributeError):
        return False

    # 1) Python wheel.
    try:  # pragma: no cover - optional heavy dep
        import sqlite_vss  # type: ignore

        sqlite_vss.load(conn)
        return True
    except Exception:
        pass

    # 2/3) manual paths.
    for path in (str(_PACKAGE_DIR / "vss0.dylib"), "vss0"):
        try:
            conn.load_extension(path)  # type: ignore[attr-defined]
            return True
        except (sqlite3.OperationalError, AttributeError):
            continue
    return False


def _open_connection(path: str) -> Tuple[sqlite3.Connection, str]:
    """Open the SQLite (or SQLCipher) connection.

    Returns ``(conn, backend)`` where backend is ``"sqlcipher"`` or
    ``"sqlite3"``. SQLCipher is loaded only when ``pysqlcipher3`` is
    importable AND ``AURA_MEMORY_KEY`` is set in the environment; otherwise
    we log a single warning and use plain sqlite3 so tests still run.
    """

    key = os.environ.get("AURA_MEMORY_KEY")
    if key:
        try:  # pragma: no cover - optional heavy dep
            from pysqlcipher3 import dbapi2 as sqlcipher  # type: ignore

            conn = sqlcipher.connect(path)
            conn.execute(f"PRAGMA key = '{key}'")
            return conn, "sqlcipher"
        except Exception as exc:
            logger.warning(
                "SQLCipher requested via AURA_MEMORY_KEY but pysqlcipher3 is unavailable (%s); "
                "falling back to plain sqlite3. See memory/README.md for the SQLCipher build steps.",
                exc,
            )
    return sqlite3.connect(path), "sqlite3"


# ---------------------------------------------------------------------------
# MemoryGraph
# ---------------------------------------------------------------------------


_NODE_TYPES = {
    "User", "Event", "App", "Person", "Place", "Transaction",
    "Conversation", "HealthSnapshot", "Action", "Trace",
}
_EDGE_TYPES = {
    "attended", "sent_to", "located_at", "paid_to", "talked_about",
    "felt_during", "triggered_by", "confirmed_by_user",
}


@dataclass
class MemoryGraph:
    """High-level on-device memory store."""

    path: str = ":memory:"
    eager_embedder: bool = False
    conn: sqlite3.Connection = field(init=False)
    backend: str = field(init=False, default="sqlite3")
    _vss_loaded: bool = field(init=False, default=False)
    _embedder: Any = field(init=False, default=None)
    _embedder_kind: str = field(init=False, default="hash")
    _last_audit_hash: str = field(init=False, default="")

    def __post_init__(self) -> None:
        self.conn, self.backend = _open_connection(self.path)
        self.conn.row_factory = sqlite3.Row
        # sqlite-vss is best-effort — if the extension is unavailable we fall
        # through to embeddings_local + Python cosine search.
        self._vss_loaded = _try_load_vss(self.conn)
        if self.eager_embedder:
            self._ensure_embedder()
        # Apply schema.
        self.conn.executescript(_SCHEMA_SQL)
        if self._vss_loaded:
            try:
                self.conn.execute(
                    "CREATE VIRTUAL TABLE IF NOT EXISTS embeddings_vss USING vss0(embedding(384))"
                )
            except sqlite3.OperationalError:
                # vss0 is loaded but virtual-table creation failed (e.g.,
                # schema mismatch from a previous run). We disable vss for
                # this connection and rely on the local cosine path.
                self._vss_loaded = False
        self.conn.commit()
        # Resume the audit hash chain from the latest persisted row.
        cur = self.conn.execute("SELECT hash_chain FROM audit_log ORDER BY seq DESC LIMIT 1")
        row = cur.fetchone()
        self._last_audit_hash = row["hash_chain"] if row else "genesis"

    # -- embedder lazy-load ----------------------------------------------

    def _ensure_embedder(self) -> None:
        """Load the sentence-transformers model on first use, then cache it."""

        if self._embedder is not None or self._embedder_kind == "minilm":
            return
        st = _try_sentence_transformers()
        if st is not None:
            self._embedder = st
            self._embedder_kind = "minilm"

    # -- timestamps -------------------------------------------------------

    @staticmethod
    def _now_ms(when: Optional[datetime] = None) -> int:
        when = when or datetime.now(timezone.utc)
        return int(when.timestamp() * 1000)

    # -- node / edge ------------------------------------------------------

    def add_node(
        self,
        type: str,
        data: Dict[str, Any],
        when: Optional[datetime] = None,
        retention_class: str = "default",
        node_id: Optional[str] = None,
        agent: str = "orchestrator",
    ) -> str:
        if type not in _NODE_TYPES:
            raise ValueError(f"unknown node type: {type}")
        nid = node_id or "n_" + uuid.uuid4().hex[:10]
        ts = self._now_ms(when)
        self.conn.execute(
            "INSERT INTO nodes(id, type, data_json, ts, retention_class) VALUES(?,?,?,?,?)",
            (nid, type, json.dumps(data, ensure_ascii=False), ts, retention_class),
        )
        self.audit_append("write", target_type=type, target_id=nid, agent=agent, payload={"data": data, "ts": ts})
        self.conn.commit()
        return nid

    def add_edge(
        self,
        src: str,
        dst: str,
        type: str,
        weight: float = 1.0,
        when: Optional[datetime] = None,
        agent: str = "orchestrator",
    ) -> str:
        if type not in _EDGE_TYPES:
            raise ValueError(f"unknown edge type: {type}")
        eid = "e_" + uuid.uuid4().hex[:10]
        ts = self._now_ms(when)
        self.conn.execute(
            "INSERT INTO edges(id, src, dst, type, weight, ts) VALUES(?,?,?,?,?,?)",
            (eid, src, dst, type, weight, ts),
        )
        self.audit_append("write", target_type="edge", target_id=eid, agent=agent, payload={"src": src, "dst": dst, "type": type})
        self.conn.commit()
        return eid

    def add_trace(self, trace_dict: Dict[str, Any], agent: str = "orchestrator") -> str:
        """Persist a Trace from `orchestrator/trace.py`'s emit_trace."""
        trace_id = trace_dict["trace_id"]
        ts_iso = trace_dict["ts"]
        try:
            ts = int(datetime.fromisoformat(ts_iso.replace("Z", "+00:00")).timestamp() * 1000)
        except Exception:
            ts = self._now_ms()
        self.conn.execute(
            "INSERT INTO traces(trace_id, ts, payload_json, outcome) VALUES(?,?,?,?)",
            (trace_id, ts, json.dumps(trace_dict, ensure_ascii=False), trace_dict["outcome"]),
        )
        self.audit_append("write", target_type="Trace", target_id=trace_id, agent=agent, payload={"outcome": trace_dict["outcome"]})
        self.conn.commit()
        return trace_id

    # -- embedding / search ----------------------------------------------

    def embed(self, text: str) -> List[float]:
        """Return a 384-d unit-norm embedding for ``text``.

        Production path: ``sentence-transformers/all-MiniLM-L6-v2`` (loaded
        lazily, cached on disk under ``$AURA_MODEL_CACHE``). Fallback path:
        deterministic hash-bucket vector. Both produce 384 floats.
        """
        if self._embedder is None and self._embedder_kind != "minilm":
            self._ensure_embedder()
        if self._embedder_kind == "minilm" and self._embedder is not None:  # pragma: no cover - heavy dep
            vec = self._embedder.encode(text, normalize_embeddings=True)
            return [float(v) for v in vec]
        return _hash_bucket_embed(text)

    def add_embedding(self, node_id: str, chunk_idx: int, text: str) -> int:
        """Compute + persist an embedding for ``text`` against ``node_id``.

        We always write to ``embeddings_local`` as a portable mirror; if the
        sqlite-vss extension is loaded we additionally write to the
        ``embeddings_vss`` virtual table so production queries can use
        ``vss_search``. The mirror keeps tests deterministic across envs.
        """

        import hashlib

        text_hash = hashlib.sha256(text.encode()).hexdigest()
        cur = self.conn.execute(
            "INSERT INTO embedding_refs(node_id, chunk_idx, text_hash) VALUES(?,?,?)",
            (node_id, chunk_idx, text_hash),
        )
        rowid = int(cur.lastrowid)
        vec = self.embed(text)
        if len(vec) != 384:
            raise ValueError(f"embedding dimension {len(vec)} != 384")
        # Mirror to local table — primary search backend in test env.
        self.conn.execute(
            "INSERT INTO embeddings_local(rowid, vector) VALUES(?,?)",
            (rowid, json.dumps(vec)),
        )
        if self._vss_loaded:  # pragma: no cover - environment dep
            try:
                self.conn.execute(
                    "INSERT INTO embeddings_vss(rowid, embedding) VALUES(?, ?)",
                    (rowid, json.dumps(vec)),
                )
            except sqlite3.OperationalError:
                # vss insert failed — local mirror still works.
                pass
        self.conn.commit()
        return rowid

    def search(self, query: str, k: int = 5) -> List[Dict[str, Any]]:
        """Top-k semantic search against persisted embeddings.

        When the sqlite-vss extension is loaded we issue a ``vss_search``
        against ``embeddings_vss``; otherwise we run a Python cosine over the
        ``embeddings_local`` mirror. Both return the same shape:
        ``[{node_id, score, type, ts, data}]``.
        """
        q_vec = self.embed(query)
        scored: List[Tuple[float, str]] = []
        if self._vss_loaded:  # pragma: no cover - environment dep
            try:
                rows = self.conn.execute(
                    "SELECT rowid, distance FROM embeddings_vss "
                    "WHERE vss_search(embedding, ?) LIMIT ?",
                    (json.dumps(q_vec), k * 4),
                ).fetchall()
                for r in rows:
                    nid_row = self.conn.execute(
                        "SELECT node_id FROM embedding_refs WHERE rowid=?",
                        (r["rowid"],),
                    ).fetchone()
                    if nid_row is None:
                        continue
                    score = 1.0 - float(r["distance"])  # vss returns L2-ish distance
                    scored.append((score, nid_row["node_id"]))
            except sqlite3.OperationalError:
                scored = []
        if not scored:
            rows = self.conn.execute(
                "SELECT er.rowid, er.node_id, el.vector "
                "FROM embedding_refs er JOIN embeddings_local el USING(rowid)"
            ).fetchall()
            for r in rows:
                v = json.loads(r["vector"])
                scored.append((_cosine(q_vec, v), r["node_id"]))
        scored.sort(reverse=True)
        out: List[Dict[str, Any]] = []
        seen: set = set()
        for score, nid in scored:
            if nid in seen:
                continue
            seen.add(nid)
            n = self.conn.execute(
                "SELECT id, type, data_json, ts FROM nodes WHERE id=?", (nid,)
            ).fetchone()
            if n is None:
                continue
            out.append({
                "node_id": nid,
                "score": round(float(score), 4),
                "type": n["type"],
                "ts": n["ts"],
                "data": json.loads(n["data_json"]),
            })
            if len(out) >= k:
                break
        return out

    # -- delete / export --------------------------------------------------

    def delete_by_time_range(self, from_ms: int, to_ms: int, agent: str = "user") -> int:
        """Delete nodes / edges / traces in [from_ms, to_ms]. Returns affected count."""
        cur = self.conn.cursor()
        cur.execute(
            "DELETE FROM edges WHERE src IN (SELECT id FROM nodes WHERE ts BETWEEN ? AND ?) "
            "OR dst IN (SELECT id FROM nodes WHERE ts BETWEEN ? AND ?)",
            (from_ms, to_ms, from_ms, to_ms),
        )
        edges_deleted = cur.rowcount
        cur.execute("DELETE FROM nodes WHERE ts BETWEEN ? AND ?", (from_ms, to_ms))
        nodes_deleted = cur.rowcount
        cur.execute("DELETE FROM traces WHERE ts BETWEEN ? AND ?", (from_ms, to_ms))
        traces_deleted = cur.rowcount
        cur.execute(
            "DELETE FROM embedding_refs WHERE node_id NOT IN (SELECT id FROM nodes)"
        )
        self.audit_append(
            "delete_range",
            target_type="time_range",
            target_id=f"{from_ms}-{to_ms}",
            agent=agent,
            payload={
                "from_ms": from_ms,
                "to_ms": to_ms,
                "nodes": nodes_deleted,
                "edges": edges_deleted,
                "traces": traces_deleted,
            },
        )
        self.conn.commit()
        return nodes_deleted + edges_deleted + traces_deleted

    def export_json(self, redaction_profile: str = "raw") -> Dict[str, Any]:
        """Export the entire graph + traces + Merkle roots (spec §6.9)."""
        nodes = [
            {
                "id": r["id"], "type": r["type"], "data": json.loads(r["data_json"]),
                "ts": r["ts"], "retention_class": r["retention_class"],
            }
            for r in self.conn.execute("SELECT * FROM nodes").fetchall()
        ]
        edges = [
            {"id": r["id"], "src": r["src"], "dst": r["dst"], "type": r["type"], "weight": r["weight"], "ts": r["ts"]}
            for r in self.conn.execute("SELECT * FROM edges").fetchall()
        ]
        traces = [
            json.loads(r["payload_json"])
            for r in self.conn.execute("SELECT payload_json FROM traces").fetchall()
        ]
        merkle_rows = self.conn.execute("SELECT date, root FROM merkle_daily").fetchall()
        merkle_daily = [{"date": r["date"], "root": r["root"]} for r in merkle_rows]
        export = {
            "export_version": "1.0",
            "user_id_local": "u_self",
            "exported_at": datetime.now(timezone.utc).isoformat(),
            "redaction_profile": redaction_profile,
            "nodes": nodes,
            "edges": edges,
            "traces": traces,
            "merkle_daily": merkle_daily,
        }
        # Validate against the published JSON Schema. Any drift in the export
        # shape is caught here before it reaches the user's filesystem.
        try:
            import jsonschema  # type: ignore

            schema_path = _PACKAGE_DIR / "export_schema.json"
            with schema_path.open() as f:
                schema = json.load(f)
            jsonschema.validate(export, schema)
        except ImportError:  # pragma: no cover - schema validation is best-effort
            logger.warning("jsonschema not installed — skipping export validation.")
        self.audit_append(
            "export",
            target_type="full",
            target_id="all",
            agent="user",
            payload={"node_count": len(nodes), "edge_count": len(edges), "trace_count": len(traces)},
        )
        self.conn.commit()
        return export

    # -- audit + Merkle ---------------------------------------------------

    def audit_append(
        self,
        op: str,
        *,
        target_type: Optional[str] = None,
        target_id: Optional[str] = None,
        agent: str = "orchestrator",
        payload: Optional[Dict[str, Any]] = None,
    ) -> str:
        """Append a row to the audit_log; returns the new chain hash."""
        ts = self._now_ms()
        row = {
            "ts": ts, "op": op, "target_type": target_type, "target_id": target_id,
            "agent": agent, "payload": payload or {},
        }
        new_hash = chain_next(self._last_audit_hash, row)
        self.conn.execute(
            "INSERT INTO audit_log(ts, op, target_type, target_id, agent, payload_json, hash_chain) "
            "VALUES(?,?,?,?,?,?,?)",
            (ts, op, target_type, target_id, agent, json.dumps(payload or {}, ensure_ascii=False), new_hash),
        )
        self._last_audit_hash = new_hash
        return new_hash

    def daily_merkle_root(self, when: Optional[_date] = None) -> str:
        """Compute (and persist) the Merkle root for ``when`` (default = today UTC)."""
        when = when or datetime.now(timezone.utc).date()
        day_start = int(datetime(when.year, when.month, when.day, tzinfo=timezone.utc).timestamp() * 1000)
        day_end = day_start + 86_400_000
        rows = self.conn.execute(
            "SELECT seq, ts, op, target_type, target_id, agent, payload_json, hash_chain "
            "FROM audit_log WHERE ts >= ? AND ts < ? ORDER BY seq",
            (day_start, day_end),
        ).fetchall()
        canonical_rows: List[Dict[str, Any]] = [
            {
                "seq": r["seq"], "ts": r["ts"], "op": r["op"], "target_type": r["target_type"],
                "target_id": r["target_id"], "agent": r["agent"],
                "payload": json.loads(r["payload_json"] or "{}"),
                "hash_chain": r["hash_chain"],
            }
            for r in rows
        ]
        root = compute_daily_merkle(canonical_rows, when)
        self.conn.execute(
            "INSERT OR REPLACE INTO merkle_daily(date, root, leaf_count, computed_ts) VALUES(?,?,?,?)",
            (when.isoformat(), root, len(canonical_rows), self._now_ms()),
        )
        self.conn.commit()
        return root

    # -- close ------------------------------------------------------------

    def close(self) -> None:
        try:
            self.conn.close()
        except Exception:  # pragma: no cover - defensive
            pass
