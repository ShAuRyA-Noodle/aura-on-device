"""Audit-chain + Merkle round-trip tests on a 100-event sample.

These tests assert that for a realistic 100-event audit log:

1. ``audit_append`` produces strictly monotonic, non-repeating ``hash_chain``
   values; each one incorporates the previous via ``sha256(prev || row)``.
2. ``daily_merkle_root`` over those rows is deterministic and matches the
   pure ``compute_daily_merkle`` over the canonical row sequence.
3. ``merkle_inclusion_proof`` + ``verify_inclusion`` survive a full round-trip
   for every leaf in the day.
4. ``export_json`` validates against ``memory/export_schema.json`` (when the
   ``jsonschema`` package is installed).
"""

from __future__ import annotations

import json
from datetime import date as _date, datetime, timezone
from pathlib import Path

import pytest

from memory.audit import (
    chain_next,
    compute_daily_merkle,
    merkle_inclusion_proof,
    verify_inclusion,
)
from memory.store import MemoryGraph


# Indian-context names (pilot deck §3) — keep when synthesising chat data.
_PEOPLE = ("Anu", "Manish", "Riya", "Kabir", "Mira")


def _seed_100_events(g: MemoryGraph) -> None:
    """Append a 100-event mix of nodes + edges + traces."""

    base = datetime(2026, 5, 7, 9, 0, tzinfo=timezone.utc)
    persons = [
        g.add_node("Person", {"display_name_hash": f"h_{n.lower()}", "role": "friend"},
                   when=base)
        for n in _PEOPLE
    ]
    for i in range(45):
        g.add_node(
            "Conversation",
            {"summary": f"{_PEOPLE[i % len(_PEOPLE)]} confirmed schema diagram for DSA quiz #{i}"},
            when=base,
        )
    for i in range(20):
        # add_edge counts as one audit row each.
        src = persons[i % len(persons)]
        dst = persons[(i + 1) % len(persons)]
        g.add_edge(src, dst, "talked_about", when=base)
    for i in range(15):
        g.add_node("Transaction", {"merchant": f"merchant_{i}", "amount": 100 + i}, when=base)
    for i in range(15):
        g.add_node("Event", {"title": f"event_{i}"}, when=base)
    # 5 + 45 + 20 + 15 + 15 = 100 exactly.


def test_audit_chain_links_100_events():
    g = MemoryGraph(":memory:")
    _seed_100_events(g)
    rows = g.conn.execute(
        "SELECT seq, ts, op, target_type, target_id, agent, payload_json, hash_chain "
        "FROM audit_log ORDER BY seq"
    ).fetchall()
    assert len(rows) >= 100, f"expected >= 100 audit rows, got {len(rows)}"

    seen_hashes: set[str] = set()
    prev_hash = "genesis"
    for r in rows:
        canonical_row = {
            "ts": r["ts"],
            "op": r["op"],
            "target_type": r["target_type"],
            "target_id": r["target_id"],
            "agent": r["agent"],
            "payload": json.loads(r["payload_json"] or "{}"),
        }
        expected = chain_next(prev_hash, canonical_row)
        assert r["hash_chain"] == expected, "hash_chain breaks monotonic chain"
        assert r["hash_chain"] not in seen_hashes
        seen_hashes.add(r["hash_chain"])
        prev_hash = r["hash_chain"]


def test_daily_merkle_round_trip_100_events():
    g = MemoryGraph(":memory:")
    _seed_100_events(g)
    today = _date(2026, 5, 7)
    root_persisted = g.daily_merkle_root(today)
    assert len(root_persisted) == 64

    rows = g.conn.execute(
        "SELECT seq, ts, op, target_type, target_id, agent, payload_json, hash_chain "
        "FROM audit_log WHERE ts >= ? AND ts < ? ORDER BY seq",
        (
            int(datetime(2026, 5, 7, tzinfo=timezone.utc).timestamp() * 1000),
            int(datetime(2026, 5, 8, tzinfo=timezone.utc).timestamp() * 1000),
        ),
    ).fetchall()
    canonical_rows = [
        {
            "seq": r["seq"],
            "ts": r["ts"],
            "op": r["op"],
            "target_type": r["target_type"],
            "target_id": r["target_id"],
            "agent": r["agent"],
            "payload": json.loads(r["payload_json"] or "{}"),
            "hash_chain": r["hash_chain"],
        }
        for r in rows
    ]
    pure = compute_daily_merkle(canonical_rows, today)
    assert pure == root_persisted

    # Inclusion-proof round-trip for every leaf.
    for idx, row in enumerate(canonical_rows):
        proof = merkle_inclusion_proof(canonical_rows, idx)
        leaf = json.dumps(row, sort_keys=True, separators=(",", ":"))
        assert verify_inclusion(leaf, idx, proof, root_persisted), (
            f"inclusion proof failed at idx={idx}"
        )


def test_export_json_schema_validates():
    """Round-trip: export survives JSON-Schema validation."""

    pytest.importorskip("jsonschema")
    g = MemoryGraph(":memory:")
    _seed_100_events(g)
    g.daily_merkle_root(_date(2026, 5, 7))
    export = g.export_json()
    # If validation failed, export_json would have raised. Sanity-check shape.
    assert export["export_version"] == "1.0"
    assert len(export["nodes"]) >= 70
    assert len(export["edges"]) >= 20
    assert len(export["merkle_daily"]) >= 1


def test_export_schema_file_exists():
    schema_path = Path(__file__).parent / "export_schema.json"
    assert schema_path.exists(), "memory/export_schema.json missing"
    with schema_path.open() as f:
        schema = json.load(f)
    assert schema["$id"].endswith("memory_export.json")
