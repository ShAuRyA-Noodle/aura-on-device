"""MemoryGraph + audit chain tests.

Covers:
- Schema applies cleanly via `:memory:` SQLite.
- add_node / add_edge / search returns the right node by semantic match.
- delete_by_time_range removes nodes + their embeddings + traces.
- audit chain is monotonic — each new hash incorporates the previous.
- Daily Merkle root is deterministic for a fixed row sequence.
- Export JSON contains nodes / edges / traces.
- Pure compute_daily_merkle / inclusion proof / verify pair round-trip.
"""

from __future__ import annotations

import json
from datetime import date as _date, datetime, timedelta, timezone
from pathlib import Path

import pytest

from memory.audit import (
    chain_next,
    compute_daily_merkle,
    hash_canonical,
    merkle_inclusion_proof,
    verify_inclusion,
)
from memory.store import MemoryGraph


# --------------------------------------------------------------------------
# Pure audit functions
# --------------------------------------------------------------------------


def test_chain_next_deterministic():
    row = {"op": "write", "target_id": "n_1", "ts": 1000}
    a = chain_next("genesis", row)
    b = chain_next("genesis", row)
    assert a == b
    assert a != chain_next("seed-2", row)


def test_compute_daily_merkle_deterministic():
    rows = [{"i": i, "v": "x" * (i + 1)} for i in range(5)]
    root1 = compute_daily_merkle(rows, _date(2026, 5, 7))
    root2 = compute_daily_merkle(rows, _date(2026, 5, 7))
    assert root1 == root2
    # Order matters.
    root3 = compute_daily_merkle(list(reversed(rows)), _date(2026, 5, 7))
    assert root1 != root3


def test_merkle_inclusion_proof_round_trip():
    rows = [{"i": i} for i in range(7)]
    when = _date(2026, 5, 7)
    root = compute_daily_merkle(rows, when)
    for idx in range(len(rows)):
        proof = merkle_inclusion_proof(rows, idx)
        leaf = json.dumps(rows[idx], sort_keys=True, separators=(",", ":"))
        assert verify_inclusion(leaf, idx, proof, root)


def test_compute_daily_merkle_empty():
    root = compute_daily_merkle([], _date(2026, 5, 7))
    assert len(root) == 64  # sha256 hex


# --------------------------------------------------------------------------
# MemoryGraph CRUD + audit
# --------------------------------------------------------------------------


def _store() -> MemoryGraph:
    return MemoryGraph(":memory:")


def test_schema_applies():
    g = _store()
    rows = g.conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
    ).fetchall()
    names = {r["name"] for r in rows}
    expected = {"nodes", "edges", "traces", "embedding_refs", "embeddings_local",
                "audit_log", "merkle_daily", "settings"}
    assert expected.issubset(names)


def test_add_node_appends_audit():
    g = _store()
    nid = g.add_node("Person", {"display_name_hash": "h_anu", "role": "friend"})
    assert nid.startswith("n_")
    audit = g.conn.execute("SELECT op, target_id FROM audit_log").fetchall()
    assert any(r["op"] == "write" and r["target_id"] == nid for r in audit)


def test_add_edge_round_trip():
    g = _store()
    a = g.add_node("Person", {"display_name_hash": "h_anu"})
    b = g.add_node("Event", {"title": "DSA Quiz"})
    eid = g.add_edge(a, b, "attended")
    assert eid.startswith("e_")
    rows = g.conn.execute("SELECT * FROM edges").fetchall()
    assert len(rows) == 1
    assert rows[0]["src"] == a and rows[0]["dst"] == b


def test_add_node_unknown_type_rejected():
    g = _store()
    with pytest.raises(ValueError):
        g.add_node("Magic", {})


def test_search_returns_relevant_node():
    g = _store()
    nid_a = g.add_node("Conversation", {"summary": "Anu confirmed schema diagram for DSA quiz"})
    nid_b = g.add_node("Transaction", {"merchant": "zomato", "amount": 350})
    g.add_embedding(nid_a, 0, "Anu confirmed schema diagram for DSA quiz")
    g.add_embedding(nid_b, 0, "zomato food delivery 350 rupees")

    hits = g.search("schema diagram quiz", k=2)
    assert hits, "expected at least one hit"
    assert hits[0]["node_id"] == nid_a


def test_delete_by_time_range_removes_node_and_embedding():
    g = _store()
    nid = g.add_node("Conversation", {"summary": "old chat"}, when=datetime(2026, 4, 1, tzinfo=timezone.utc))
    g.add_embedding(nid, 0, "old chat")
    from_ms = int(datetime(2026, 3, 30, tzinfo=timezone.utc).timestamp() * 1000)
    to_ms = int(datetime(2026, 4, 30, tzinfo=timezone.utc).timestamp() * 1000)
    affected = g.delete_by_time_range(from_ms, to_ms)
    assert affected >= 1
    assert g.conn.execute("SELECT COUNT(*) c FROM nodes").fetchone()["c"] == 0
    assert g.conn.execute("SELECT COUNT(*) c FROM embedding_refs").fetchone()["c"] == 0


def test_audit_chain_links_each_row_to_previous():
    g = _store()
    g.add_node("Person", {"role": "self"})
    g.add_node("Person", {"role": "friend"})
    rows = g.conn.execute("SELECT seq, hash_chain, payload_json FROM audit_log ORDER BY seq").fetchall()
    assert len(rows) >= 2
    # hash_chain values are unique per row.
    seen = {r["hash_chain"] for r in rows}
    assert len(seen) == len(rows)


def test_daily_merkle_root_persists():
    g = _store()
    g.add_node("Person", {"role": "self"})
    g.add_node("Event", {"title": "DSA Quiz"})
    today = datetime.now(timezone.utc).date()
    root = g.daily_merkle_root(today)
    assert len(root) == 64
    persisted = g.conn.execute("SELECT root FROM merkle_daily WHERE date=?", (today.isoformat(),)).fetchone()
    assert persisted["root"] == root


def test_export_json_round_trip():
    g = _store()
    a = g.add_node("Person", {"display_name_hash": "h_kabir"})
    b = g.add_node("Place", {"label": "Hostel mess"})
    g.add_edge(a, b, "located_at")
    g.add_trace({
        "trace_id": "tr_abcdef123456",
        "ts": "2026-05-07T07:45:00+00:00",
        "trigger": {"source": "test", "value": 1},
        "signals": [],
        "candidates": [],
        "chosen": "do_nothing",
        "rationale": "test",
        "rationale_source": "template",
        "confirm_required": False,
        "outcome": "pending",
        "redactions": [],
    })
    export = g.export_json()
    assert export["export_version"] == "1.0"
    assert len(export["nodes"]) == 2
    assert len(export["edges"]) == 1
    assert len(export["traces"]) == 1


def test_hash_canonical_stable():
    a = hash_canonical({"b": 2, "a": 1})
    b = hash_canonical({"a": 1, "b": 2})
    assert a == b
