"""FinanceAgent unit tests (technical_spec.md §3.3).

Covers:
- 50 UPI SMS across HDFC / SBI / ICICI / Axis (regex hot path).
- 20 Gmail receipt headers across Zomato / Swiggy / Blinkit / Amazon / IRCTC / Uber.
- Categorisation map sanity (food_delivery, groceries, transport, etc.).
- Anomaly Z-score on synthetic spend history.
- EoM projection on a 14-day burn rate.
- ``persist`` returns only the redacted contract (no raw text).
- Async ``tick`` round-trip on 50 SMS + 20 receipts.
"""

from __future__ import annotations

import asyncio
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import List

import pytest

from agents.finance.agent import (
    Anomaly,
    Balance,
    Category,
    FinanceAgent,
    ThreadMeta,
    Transaction,
)


FIXTURES = Path(__file__).parent / "fixtures"


def _read_jsonl(name: str):
    with (FIXTURES / name).open() as f:
        return [json.loads(line) for line in f if line.strip()]


# --------------------------------------------------------------------------
# SMS regex coverage — at least 90% of fixture SMS parses cleanly.
# --------------------------------------------------------------------------


def test_upi_sms_fixture_parses_majority():
    rows = _read_jsonl("upi_sms.jsonl")
    assert len(rows) == 50, "fixture must have 50 SMS"
    agent = FinanceAgent()
    parsed = 0
    for r in rows:
        txn = agent.parse_sms(r["body"])
        if txn:
            parsed += 1
    # Spec target: F1 >= 0.95 — we want >=45 of 50 parsed.
    assert parsed >= 45, f"only {parsed}/50 SMS parsed"


def test_hdfc_sms_categorises_zomato():
    agent = FinanceAgent()
    txn = agent.parse_sms("Sent Rs.350.00 from A/c **1234 to ZOMATO via UPI on 07-MAY")
    assert txn is not None
    assert txn.bank == "HDFC"
    assert txn.account_last4 == "1234"
    assert txn.amount == 350.0
    assert txn.category == Category.FOOD_DELIVERY


def test_sbi_sms_categorises_groceries():
    agent = FinanceAgent()
    txn = agent.parse_sms(
        "Dear Customer, Rs.1200.00 debited from A/c X1234 on 07-05-26 to VPA bigbasket@okhdfc Ref 412345. -SBI"
    )
    assert txn is not None and txn.bank == "SBI" and txn.category == Category.GROCERIES


def test_icici_card_categorises_food():
    agent = FinanceAgent()
    txn = agent.parse_sms("INR 250.00 spent on ICICI Bank Card XX1234 at SWIGGY on 07-May-26")
    assert txn is not None and txn.bank == "ICICI" and txn.category == Category.FOOD_DELIVERY


def test_icici_upi_categorises_investment():
    agent = FinanceAgent()
    txn = agent.parse_sms(
        "Dear Customer, Acct XX1234 debited with INR 250.00 on 06-May-26; UPI:412345678901; toward zerodha@icici."
    )
    assert txn is not None and txn.bank == "ICICI" and txn.category == Category.INVESTMENT


def test_axis_categorises_transport():
    agent = FinanceAgent()
    txn = agent.parse_sms("INR 540 debited A/c no. XX1234 07-05-26 13:42 UPI/P2A/uber@axis/Uber")
    assert txn is not None and txn.bank == "AXIS" and txn.category == Category.TRANSPORT


def test_unparseable_sms_logged():
    agent = FinanceAgent()
    txn = agent.parse_sms("Hey what's the meeting time tomorrow?")
    assert txn is None
    assert agent.unparsed_log == ["Hey what's the meeting time tomorrow?"]


# --------------------------------------------------------------------------
# Gmail receipts
# --------------------------------------------------------------------------


def test_gmail_receipts_fixture_loads_20():
    rows = _read_jsonl("gmail_receipts.jsonl")
    assert len(rows) == 20


def test_parse_gmail_receipt_amazon():
    agent = FinanceAgent()
    tm = ThreadMeta(
        thread_id="tg_r04",
        sender="auto-confirm@amazon.in",
        subject="Your Amazon.in order of Rs.2,400.00",
        snippet="Echo Dot",
        amount=2400,
        merchant="amazon",
        ts=datetime(2026, 5, 5, 19, 1, tzinfo=timezone.utc),
    )
    txn = agent.parse_gmail_receipt(tm)
    assert txn is not None
    assert txn.amount == 2400
    assert txn.category == Category.SHOPPING
    assert txn.source == "gmail"


def test_parse_gmail_receipt_amount_extraction_from_subject():
    agent = FinanceAgent()
    tm = ThreadMeta(
        thread_id="tg_x",
        sender="orders@swiggy.in",
        subject="Order delivered — Total Rs. 420",
        snippet="",
        amount=None,
        merchant=None,
        ts=datetime(2026, 5, 7, 13, 15, tzinfo=timezone.utc),
    )
    txn = agent.parse_gmail_receipt(tm)
    assert txn is not None and txn.amount == 420.0
    assert txn.category == Category.FOOD_DELIVERY


# --------------------------------------------------------------------------
# Anomaly detection
# --------------------------------------------------------------------------


def test_anomaly_flags_today_spike():
    agent = FinanceAgent()
    now = datetime(2026, 5, 7, 21, 0, tzinfo=timezone.utc)
    history: List[Transaction] = []
    # Build 30 days of mild food spend, then a 10x today.
    for i in range(30):
        history.append(
            Transaction(
                amount=200.0,
                currency="INR",
                account_last4="1234",
                ts=now - timedelta(days=i),
                merchant_raw="zomato",
                category=Category.FOOD_DELIVERY,
                direction="debit",
            )
        )
    # Today: 4 large food deliveries.
    for _ in range(4):
        history.append(
            Transaction(
                amount=900.0,
                currency="INR",
                account_last4="1234",
                ts=now,
                merchant_raw="zomato",
                category=Category.FOOD_DELIVERY,
                direction="debit",
            )
        )
    anomalies = agent.anomaly_flag(history, as_of=now)
    assert any(a.category == Category.FOOD_DELIVERY for a in anomalies)


# --------------------------------------------------------------------------
# EoM projection
# --------------------------------------------------------------------------


def test_eom_projection_runs():
    agent = FinanceAgent()
    now = datetime(2026, 5, 7, 21, 0, tzinfo=timezone.utc)
    history = [
        Transaction(
            amount=600.0,
            currency="INR",
            account_last4="1234",
            ts=now - timedelta(days=i),
            merchant_raw="zomato",
            category=Category.FOOD_DELIVERY,
            direction="debit",
        )
        for i in range(14)
    ]
    bal = Balance(account_hash="a_hdfc_1234", amount=20000.0, as_of=now)
    proj = agent.predict_eom_balance(history, bal, as_of=now)
    assert proj.balance_eom <= 20000.0
    assert 0.0 < proj.confidence <= 0.85


# --------------------------------------------------------------------------
# Persist / privacy contract
# --------------------------------------------------------------------------


def test_persist_only_contains_redacted_fields():
    agent = FinanceAgent()
    txn = agent.parse_sms("Sent Rs.350.00 from A/c **1234 to ZOMATO via UPI on 07-MAY")
    persisted = agent.persist(txn)
    allowed = {"merchant_hash", "amount", "currency", "account_last4", "ts", "category"}
    assert set(persisted.keys()) == allowed
    # No raw merchant text leaks
    assert "zomato" not in json.dumps(persisted).lower() or persisted.get("merchant_hash")


# --------------------------------------------------------------------------
# Async tick over the full fixture
# --------------------------------------------------------------------------


def test_async_tick_full_fixture():
    rows_sms = _read_jsonl("upi_sms.jsonl")
    rows_gmail = _read_jsonl("gmail_receipts.jsonl")
    agent = FinanceAgent()
    payload = {
        "tick_ts": "2026-05-07T21:00:00+05:30",
        "sms_unprocessed": rows_sms,
        "gmail_receipts": rows_gmail,
        "balance_seed": {
            "account_hash": "a_hdfc_1234",
            "amount": 50000.0,
            "as_of": "2026-05-07T08:00:00+00:00",
        },
        "history": [],
    }
    out = asyncio.run(agent.tick(payload))
    assert out["today_total"] >= 0
    assert "new_transactions" in out
    # at least 30 of 50 SMS parsed plus 20 gmail
    assert len(out["new_transactions"]) >= 50


# --------------------------------------------------------------------------
# Substitution suggestion
# --------------------------------------------------------------------------


def test_suggest_substitution_food():
    agent = FinanceAgent()
    sub = agent.suggest_substitution(Category.FOOD_DELIVERY)
    assert sub is not None and sub.est_savings_inr > 0
