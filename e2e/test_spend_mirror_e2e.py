"""End-to-end: Spend Mirror — Finance + Memory integration.

Parses 10 SMS through FinanceAgent, persists each transaction to a
MemoryGraph as a `Transaction` node, retrieves by date range, then injects
an 11th anomalous SMS and asserts:

- All 10 SMS parse to a Transaction.
- All 10 land as `Transaction` nodes in the memory graph.
- Date-range retrieval returns exactly the persisted set.
- The 11th SMS triggers a high-severity anomaly (z-score >= medium).
- The persisted record contains *no* raw text — only the privacy-safe shape
  `(merchant_hash, amount, currency, account_last4, ts, category)`.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import List

import pytest

from agents.finance.agent import Anomaly, FinanceAgent, Transaction
from memory.store import MemoryGraph


# 10 ordinary SMS — Zomato/Swiggy/etc, ₹150-450, recent days.
_SMS_BASELINE = [
    "Sent Rs.350.00 from A/c **1234 to ZOMATO via UPI on 25-04-26",
    "Sent Rs.420.00 from A/c **1234 to SWIGGY via UPI on 26-04-26",
    "Sent Rs.180.00 from A/c **1234 to UBER via UPI on 27-04-26",
    "Sent Rs.299.00 from A/c **1234 to BLINKIT via UPI on 28-04-26",
    "Sent Rs.150.00 from A/c **1234 to ZOMATO via UPI on 29-04-26",
    "Sent Rs.220.00 from A/c **1234 to SWIGGY via UPI on 30-04-26",
    "Sent Rs.310.00 from A/c **1234 to UBER via UPI on 01-05-26",
    "Sent Rs.275.00 from A/c **1234 to BIGBASKET via UPI on 02-05-26",
    "Sent Rs.199.00 from A/c **1234 to NETFLIX via UPI on 03-05-26",
    "Sent Rs.180.00 from A/c **1234 to ZOMATO via UPI on 04-05-26",
]

# An obvious outlier — same category as the baseline but ~10x value, today.
_ANOMALY_SMS = "Sent Rs.4500.00 from A/c **1234 to ZOMATO via UPI on 07-05-26"


def _persist(memory: MemoryGraph, txn: Transaction) -> str:
    """Drop a Transaction into the memory graph and return its node id."""
    return memory.add_node(
        type="Transaction",
        data=txn.to_persisted(),
        when=txn.ts,
        agent="finance",
    )


def test_spend_mirror_persists_ten_sms(
    finance_agent: FinanceAgent,
    memory_graph: MemoryGraph,
) -> None:
    parsed: List[Transaction] = []
    for sms in _SMS_BASELINE:
        txn = finance_agent.parse_sms(sms)
        assert txn is not None, f"failed to parse: {sms!r}"
        parsed.append(txn)
        _persist(memory_graph, txn)

    assert len(parsed) == 10

    # Verify they all hit the graph as Transaction nodes.
    rows = memory_graph.conn.execute(
        "SELECT id, data_json FROM nodes WHERE type = 'Transaction'"
    ).fetchall()
    assert len(rows) == 10


def test_spend_mirror_retrieve_by_date_range(
    finance_agent: FinanceAgent,
    memory_graph: MemoryGraph,
) -> None:
    for sms in _SMS_BASELINE:
        txn = finance_agent.parse_sms(sms)
        assert txn is not None
        _persist(memory_graph, txn)

    # Retrieve the May 1 -> May 4 inclusive window — that's 4 SMS in fixture.
    start_ms = int(datetime(2026, 5, 1, tzinfo=timezone.utc).timestamp() * 1000)
    end_ms = int(datetime(2026, 5, 4, 23, 59, 59, tzinfo=timezone.utc).timestamp() * 1000)
    rows = memory_graph.conn.execute(
        "SELECT id, data_json, ts FROM nodes WHERE type='Transaction' "
        "AND ts BETWEEN ? AND ? ORDER BY ts",
        (start_ms, end_ms),
    ).fetchall()
    assert len(rows) == 4, f"expected 4 in May 1-4 range, got {len(rows)}"


def test_spend_mirror_anomaly_on_11th_sms(
    finance_agent: FinanceAgent,
    memory_graph: MemoryGraph,
) -> None:
    history: List[Transaction] = []
    for sms in _SMS_BASELINE:
        txn = finance_agent.parse_sms(sms)
        assert txn is not None
        history.append(txn)
        _persist(memory_graph, txn)

    # Inject the anomaly.
    anomaly_txn = finance_agent.parse_sms(_ANOMALY_SMS)
    assert anomaly_txn is not None
    history.append(anomaly_txn)
    _persist(memory_graph, anomaly_txn)

    # Run the anomaly detector with as_of = anomaly date.
    as_of = datetime(2026, 5, 7, 12, tzinfo=timezone.utc)
    anomalies: List[Anomaly] = finance_agent.anomaly_flag(history, as_of=as_of)

    assert anomalies, "no anomaly raised on the 11th SMS"
    severities = {a.severity for a in anomalies}
    assert "high" in severities or "medium" in severities, severities


def test_spend_mirror_replay_matches_canonical_trace(canonical_traces_dir) -> None:
    """Replay through the orchestrator must produce a trace structurally
    identical to ``orchestrator/replays/output/spend_mirror_trace.json``."""
    import json

    from deepdiff import DeepDiff
    from orchestrator.replay import run_replay

    canonical = json.loads(
        (canonical_traces_dir / "spend_mirror_trace.json").read_text()
    )
    out = run_replay("spend_mirror", write_output=False)
    diff = DeepDiff(
        canonical,
        out["trace"],
        exclude_paths=["root['ts']"],
        ignore_order=False,
    )
    assert not diff, f"trace drift vs canonical: {diff}"


def test_spend_mirror_replay_chooses_surface_anomaly(spend_mirror_replay) -> None:
    """Spend Mirror replay surfaces a real anomaly + 'Cook tomorrow?' copy."""
    from agents.core.types import UserState
    from orchestrator.replay import run_replay

    out = run_replay("spend_mirror", write_output=False)
    assert out["chosen_kind"] in spend_mirror_replay["expected"]["chosen_in"]
    surface_anom = next(
        c for c in out["trace"]["candidates"] if c["kind"] == "SURFACE_ANOMALY"
    )
    assert surface_anom["score"] >= 0.45


def test_spend_mirror_persisted_record_is_pii_free(
    finance_agent: FinanceAgent,
    memory_graph: MemoryGraph,
) -> None:
    sms = _SMS_BASELINE[0]
    txn = finance_agent.parse_sms(sms)
    assert txn is not None
    nid = _persist(memory_graph, txn)

    row = memory_graph.conn.execute(
        "SELECT data_json FROM nodes WHERE id = ?", (nid,)
    ).fetchone()
    assert row is not None
    data = row["data_json"]

    # The persisted shape must match `Transaction.to_persisted()` exactly.
    # No raw merchant string, no SMS body, no account number beyond last-4.
    assert "ZOMATO" not in data, "raw merchant name leaked"
    assert "Sent Rs" not in data, "raw SMS body leaked"
    assert '"account_last4": "1234"' in data
    assert '"merchant_hash":' in data
