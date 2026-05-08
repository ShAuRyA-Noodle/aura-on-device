"""FinanceAgent — Indian-context UPI / receipt intelligence.

Implements technical_spec.md §3.3.

Design notes
------------
- Pure regex hot path for the 4 most-common Indian banks (HDFC, SBI, ICICI,
  Axis). DistilBERT fallback is a [TEAM TO VERIFY] integration point;
  here we expose `parse_sms_with_fallback` that simply queues misses.
- Privacy: persist() returns a dict containing only
  ``(merchant_hash, amount, currency, account_last4, ts, category)``.
  Raw SMS body never leaves the parser.
- Categorisation uses a static merchant -> category map plus keyword
  heuristics. 14 fixed categories per spec.
- Anomaly detection: per-category Z-score against a 30-day rolling mean.
- EoM projection: simple linear extrapolation from daily burn rate; we
  intentionally avoid the 2-layer LSTM here (that is a Phase-2 trained
  artefact). The interface is identical so the LSTM can drop in later.

Async surface: ``FinanceAgent.tick`` is async because the orchestrator's
LangGraph loop awaits it. The hot regex path is sync; only Gmail / DB
calls would be awaited in production.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import statistics
from collections import Counter
from dataclasses import asdict, dataclass, field
from datetime import datetime, timedelta, timezone
from enum import Enum
from pathlib import Path
from typing import Any, Iterable, List, Optional

# Per-bank SMS parsers live in their own module so they are easy to extend
# without touching the agent. Importing keeps the regex pack hot in memory.
from .sms_patterns import dispatch as _sms_pattern_dispatch  # noqa: F401


# ---------------------------------------------------------------------------
# Optional on-device LLM extractor for unrecognised SMS.
#
# Activated when BOTH:
#   1. AURA_USE_LLM=1 in the environment.
#   2. The trained extractor artefact at
#      models/exports/comms_classifier.pkl exists (we share the gating
#      file with the Comms agent so the team flips one switch).
#
# Behaviour: when the regex pack returns ``None`` we ask Gemma 2B for a
# JSON extraction. If MLX/llama.cpp is missing or the JSON is invalid,
# we fall back to the deterministic queue-for-fallback behaviour.
# ---------------------------------------------------------------------------


_FINANCE_LLM_ADAPTER = None
_FINANCE_LLM_ATTEMPTED = False


def _finance_llm_enabled() -> bool:
    if os.environ.get("AURA_USE_LLM", "0") != "1":
        return False
    artefact = (
        Path(__file__).resolve().parents[2]
        / "models"
        / "exports"
        / "comms_classifier.pkl"
    )
    return artefact.exists()


def _get_finance_llm():
    global _FINANCE_LLM_ADAPTER, _FINANCE_LLM_ATTEMPTED
    if _FINANCE_LLM_ADAPTER is not None or _FINANCE_LLM_ATTEMPTED:
        return _FINANCE_LLM_ADAPTER
    _FINANCE_LLM_ATTEMPTED = True
    try:
        from models.llm import get_adapter

        _FINANCE_LLM_ADAPTER = get_adapter("gemma-2b-4bit")
    except Exception:
        _FINANCE_LLM_ADAPTER = None
    return _FINANCE_LLM_ADAPTER


def _llm_extract_sms(text: str) -> Optional[dict[str, Any]]:
    adapter = _get_finance_llm()
    if adapter is None:
        return None
    try:
        from models.llm.prompts import finance_extract_prompt, safe_json_extract

        out = adapter.generate(
            finance_extract_prompt(text[:480]),
            max_tokens=128,
            temperature=0.0,
            stop=("<end_of_turn>",),
        )
    except Exception:
        return None
    return safe_json_extract(out)


# ---------------------------------------------------------------------------
# Data model
# ---------------------------------------------------------------------------


class Category(str, Enum):
    """14 fixed spend categories (spec §3.3)."""

    FOOD_DELIVERY = "food_delivery"
    GROCERIES = "groceries"
    TRANSPORT = "transport"
    SHOPPING = "shopping"
    ENTERTAINMENT = "entertainment"
    BILLS_UTILITIES = "bills_utilities"
    RENT = "rent"
    EDUCATION = "education"
    HEALTH = "health"
    TRAVEL = "travel"
    P2P_TRANSFER = "p2p_transfer"
    SUBSCRIPTIONS = "subscriptions"
    INVESTMENT = "investment"
    OTHER = "other"


@dataclass
class Transaction:
    """Parsed, redacted transaction record.

    The fields are exactly the persistence contract from spec §3.3:
    ``(merchant_hash, amount, currency, account_last4, ts, category)``.
    ``merchant_raw`` is kept in-memory for categorisation only and is
    explicitly dropped before storage by :meth:`FinanceAgent.persist`.
    """

    amount: float
    currency: str
    account_last4: str
    ts: datetime
    merchant_raw: str = ""
    merchant_hash: str = ""
    category: Optional[Category] = None
    bank: str = ""
    direction: str = "debit"  # debit | credit
    source: str = "sms"  # sms | gmail
    raw_id: str = ""

    def __post_init__(self) -> None:
        if not self.merchant_hash and self.merchant_raw:
            self.merchant_hash = _hash_merchant(self.merchant_raw)

    def to_persisted(self) -> dict[str, Any]:
        """Privacy-preserving record. No raw text."""
        return {
            "merchant_hash": self.merchant_hash,
            "amount": float(self.amount),
            "currency": self.currency,
            "account_last4": self.account_last4,
            "ts": self.ts.isoformat(),
            "category": self.category.value if self.category else None,
        }


@dataclass
class Balance:
    account_hash: str
    amount: float
    as_of: datetime


@dataclass
class Anomaly:
    reason: str
    severity: str  # low | medium | high
    category: Optional[Category] = None
    z_score: float = 0.0


@dataclass
class Projection:
    balance_eom: float
    hits_zero: Optional[str]  # ISO date string or None
    confidence: float


@dataclass
class Substitution:
    from_category: Category
    suggestion: str
    est_savings_inr: float


# ---------------------------------------------------------------------------
# Regex pack — Indian bank UPI / debit alert templates
# ---------------------------------------------------------------------------
#
# Each pattern is named, anchored, and documented. Real banks vary the
# punctuation and word order slightly; we accept reasonable variants but
# reject ambiguous strings rather than guess.
#
# Capture groups required: amount, account_last4, vpa_or_merchant, date.

_AMOUNT = r"(?:Rs\.?|INR|₹)\s*([0-9]+(?:[,.][0-9]+)*(?:\.[0-9]{1,2})?)"
_ACCT = r"(?:A/[Cc]|A/c|Account|Acct)[^0-9*]*\*+\s*([0-9]{4})"
_DATE = r"([0-9]{1,2}[-/][A-Za-z0-9]{2,4}(?:[-/][0-9]{2,4})?)"

# HDFC: "Sent Rs.350.00 from A/c **1234 to ZOMATO via UPI on 07-MAY"
# HDFC alt: "Sent Rs. 450.00 From HDFC Bank A/C *1234 To VPA zomato@hdfcbank On 07-05-26"
_HDFC = re.compile(
    r"(?P<dir>Sent|Received|Credited|Debited)\s+"
    + _AMOUNT
    + r".*?(?:from|to|From|To)\s+(?:HDFC\s+Bank\s+)?"
    + _ACCT
    + r".*?(?:to|To|from|From)\s+(?:VPA\s+)?(?P<m>[A-Za-z0-9@._\-\s]+?)"
    + r"(?:\s+(?:via|On|on)\s+)" + _DATE,
    re.IGNORECASE | re.DOTALL,
)

# SBI: "Dear Customer, Rs.1200.00 debited from A/c X1234 on 07-05-26 to
#       VPA bigbasket@okhdfc Ref 412345. -SBI"
_SBI = re.compile(
    r"(?P<dir>debited|credited)\s+from\s+A/[Cc]\s*[Xx*]+\s*(?P<acct>[0-9]{4})"
    + r"\s+on\s+" + _DATE
    + r"\s+(?:to|from)\s+(?:VPA\s+)?(?P<m>[A-Za-z0-9@._\-]+)",
    re.IGNORECASE,
)
_SBI_AMOUNT = re.compile(_AMOUNT, re.IGNORECASE)

# ICICI: "INR 250.00 spent on ICICI Bank Card XX1234 at SWIGGY on 07-May-26"
_ICICI = re.compile(
    r"INR\s+([0-9]+(?:\.[0-9]{1,2})?)\s+spent\s+on\s+ICICI\s+Bank\s+(?:Card|Acct|A/c)\s*[Xx*]+\s*([0-9]{4})"
    + r"\s+at\s+(?P<m>[A-Za-z0-9@._\-\s]+?)\s+on\s+" + _DATE,
    re.IGNORECASE,
)

# ICICI UPI alt: "Dear Customer, Acct XX1234 debited with INR 800.00 on
#                 07-May-26; UPI:412345678912; toward swiggy@icici."
_ICICI_UPI = re.compile(
    r"Acct\s+[Xx*]+\s*([0-9]{4})\s+debited\s+with\s+INR\s+([0-9]+(?:\.[0-9]{1,2})?)"
    + r"\s+on\s+" + _DATE
    + r".*?(?:toward|to|UPI:[^;]+;\s*toward)\s+(?P<m>[A-Za-z0-9@._\-]+)",
    re.IGNORECASE | re.DOTALL,
)

# Axis: "INR 540 debited A/c no. XX1234 07-05-26 13:42 UPI/P2A/uber@axis/Uber"
_AXIS = re.compile(
    r"INR\s+([0-9]+(?:\.[0-9]{1,2})?)\s+(?P<dir>debited|credited)\s+A/c\s+no\.?\s*[Xx*]+\s*([0-9]{4})"
    + r"\s+" + _DATE
    + r".*?UPI/[A-Z0-9]+/(?P<m>[A-Za-z0-9@._\-]+)",
    re.IGNORECASE,
)


@dataclass
class _ParseHit:
    amount: float
    account_last4: str
    merchant: str
    bank: str
    direction: str
    date_str: str


def _parse_amount(raw: str) -> float:
    return float(raw.replace(",", ""))


def _parse_date_loose(raw: str, fallback_year: int) -> datetime:
    """Parse the messy assortment of date formats Indian banks use.

    Accepted: ``07-05-26``, ``07/05/2026``, ``07-MAY``, ``07-May-26``,
    ``07-MAY-2026``. All interpreted as DD-MM-YY (Indian ordering).
    """
    raw = raw.strip().replace("/", "-")
    parts = raw.split("-")
    months = {
        "JAN": 1, "FEB": 2, "MAR": 3, "APR": 4, "MAY": 5, "JUN": 6,
        "JUL": 7, "AUG": 8, "SEP": 9, "OCT": 10, "NOV": 11, "DEC": 12,
    }
    day = int(parts[0])
    month_token = parts[1].upper()
    if month_token.isdigit():
        month = int(month_token)
    else:
        month = months[month_token[:3]]
    if len(parts) == 3:
        year_token = parts[2]
        year = int(year_token)
        if year < 100:
            year += 2000
    else:
        year = fallback_year
    return datetime(year, month, day, tzinfo=timezone.utc)


def _hash_merchant(merchant_raw: str) -> str:
    norm = merchant_raw.strip().lower()
    return hashlib.sha256(norm.encode("utf-8")).hexdigest()[:16]


# ---------------------------------------------------------------------------
# Categorisation
# ---------------------------------------------------------------------------

_MERCHANT_TO_CATEGORY: dict[str, Category] = {
    # Food delivery
    "zomato": Category.FOOD_DELIVERY,
    "swiggy": Category.FOOD_DELIVERY,
    "swiggyit": Category.FOOD_DELIVERY,
    "eatfit": Category.FOOD_DELIVERY,
    # Groceries / quick commerce
    "blinkit": Category.GROCERIES,
    "zepto": Category.GROCERIES,
    "bigbasket": Category.GROCERIES,
    "instamart": Category.GROCERIES,
    "dmart": Category.GROCERIES,
    # Transport
    "uber": Category.TRANSPORT,
    "ola": Category.TRANSPORT,
    "rapido": Category.TRANSPORT,
    "namma": Category.TRANSPORT,
    "metro": Category.TRANSPORT,
    # Travel
    "irctc": Category.TRAVEL,
    "makemytrip": Category.TRAVEL,
    "goibibo": Category.TRAVEL,
    "indigo": Category.TRAVEL,
    "vistara": Category.TRAVEL,
    # Shopping
    "amazon": Category.SHOPPING,
    "flipkart": Category.SHOPPING,
    "myntra": Category.SHOPPING,
    "ajio": Category.SHOPPING,
    "meesho": Category.SHOPPING,
    "nykaa": Category.SHOPPING,
    # Entertainment
    "bookmyshow": Category.ENTERTAINMENT,
    "pvr": Category.ENTERTAINMENT,
    "inox": Category.ENTERTAINMENT,
    # Subscriptions
    "netflix": Category.SUBSCRIPTIONS,
    "spotify": Category.SUBSCRIPTIONS,
    "hotstar": Category.SUBSCRIPTIONS,
    "youtube": Category.SUBSCRIPTIONS,
    "primevideo": Category.SUBSCRIPTIONS,
    # Bills
    "airtel": Category.BILLS_UTILITIES,
    "jio": Category.BILLS_UTILITIES,
    "vi": Category.BILLS_UTILITIES,
    "tatapower": Category.BILLS_UTILITIES,
    "bescom": Category.BILLS_UTILITIES,
    # Investment
    "groww": Category.INVESTMENT,
    "zerodha": Category.INVESTMENT,
    "upstox": Category.INVESTMENT,
    "kite": Category.INVESTMENT,
    # Health
    "pharmeasy": Category.HEALTH,
    "1mg": Category.HEALTH,
    "apollo": Category.HEALTH,
    "practo": Category.HEALTH,
    # Education
    "byjus": Category.EDUCATION,
    "unacademy": Category.EDUCATION,
    "physicswallah": Category.EDUCATION,
    "thapar": Category.EDUCATION,
}


def _normalise_merchant_token(merchant: str) -> str:
    """Pull a stable token from ``zomato@hdfcbank``, ``swiggy.in`` etc."""
    s = merchant.strip().lower()
    # strip URL-ish noise
    s = re.sub(r"^(?:noreply@|no-reply@|orders@|payments@|receipts@)", "", s)
    # split on @ . space - _
    token = re.split(r"[@.\s\-_/]+", s)[0]
    return token


# ---------------------------------------------------------------------------
# Gmail receipt heuristics
# ---------------------------------------------------------------------------

_GMAIL_DOMAIN_TO_MERCHANT: dict[str, str] = {
    "zomato.com": "zomato",
    "swiggy.in": "swiggy",
    "swiggy.com": "swiggy",
    "blinkit.com": "blinkit",
    "amazon.in": "amazon",
    "amazon.com": "amazon",
    "irctc.co.in": "irctc",
    "uber.com": "uber",
    "ubereats.com": "uber",
    "bookmyshow.com": "bookmyshow",
    "flipkart.com": "flipkart",
    "myntra.com": "myntra",
}

_GMAIL_SUBJECT_AMOUNT = re.compile(
    r"(?:total|amount|paid|charged|bill|order)[^0-9]{0,12}(?:Rs\.?|INR|₹)\s*([0-9]+(?:[,.][0-9]+)*(?:\.[0-9]{1,2})?)",
    re.IGNORECASE,
)
_GMAIL_SUBJECT_AMOUNT_BARE = re.compile(
    r"(?:Rs\.?|INR|₹)\s*([0-9]+(?:[,.][0-9]+)*(?:\.[0-9]{1,2})?)",
    re.IGNORECASE,
)


@dataclass
class ThreadMeta:
    """A minimal Gmail thread descriptor.

    Mirrors what GoogleSignIn would surface to the agent layer in iOS,
    plus what the Gmail API thread.metadata response contains.
    """

    thread_id: str
    sender: str  # full email or just domain
    subject: str = ""
    snippet: str = ""
    amount: Optional[float] = None
    merchant: Optional[str] = None
    ts: Optional[datetime] = None


# ---------------------------------------------------------------------------
# Static substitution table (per-category nudges)
# ---------------------------------------------------------------------------

_STATIC_SUBSTITUTIONS: dict["Category", "Substitution"] = {}


def _build_static_substitutions() -> None:
    _STATIC_SUBSTITUTIONS.update({
        Category.FOOD_DELIVERY: Substitution(
            from_category=Category.FOOD_DELIVERY,
            suggestion="Cook + Blinkit groceries — typical save ₹220/order",
            est_savings_inr=220.0,
        ),
        Category.TRANSPORT: Substitution(
            from_category=Category.TRANSPORT,
            suggestion="Metro / shared auto for sub-5km hops",
            est_savings_inr=80.0,
        ),
        Category.SHOPPING: Substitution(
            from_category=Category.SHOPPING,
            suggestion="Add to cart, wait 24h, re-evaluate",
            est_savings_inr=400.0,
        ),
        Category.SUBSCRIPTIONS: Substitution(
            from_category=Category.SUBSCRIPTIONS,
            suggestion="Audit overlapping streaming subs",
            est_savings_inr=199.0,
        ),
        Category.ENTERTAINMENT: Substitution(
            from_category=Category.ENTERTAINMENT,
            suggestion="Weekday matinee pricing on BookMyShow",
            est_savings_inr=120.0,
        ),
    })


_build_static_substitutions()


# ---------------------------------------------------------------------------
# Agent
# ---------------------------------------------------------------------------


@dataclass
class FinanceAgent:
    """Per technical_spec §3.3."""

    rolling_window_days: int = 30
    z_threshold_medium: float = 1.5
    z_threshold_high: float = 2.5
    unparsed_log: list[str] = field(default_factory=list)

    # ---- public tools ----------------------------------------------------

    def parse_sms(self, text: str, fallback_year: int = 2026) -> Optional[Transaction]:
        """Parse a single Indian bank UPI SMS string.

        Tries the regex pack first (fast path). If that misses and the
        on-device LLM extractor is available (``AURA_USE_LLM=1`` and the
        classifier artefact present) we ask Gemma 2B for a JSON
        extraction with the structured-output prompt. Failing that, we
        push the string into ``unparsed_log`` for the DistilBERT
        fallback queue and return ``None``.
        """
        text = text.strip()
        hit = self._regex_dispatch(text)
        if hit is not None:
            ts = _parse_date_loose(hit.date_str, fallback_year)
            merchant_token = _normalise_merchant_token(hit.merchant)
            txn = Transaction(
                amount=hit.amount,
                currency="INR",
                account_last4=hit.account_last4,
                ts=ts,
                merchant_raw=merchant_token,
                bank=hit.bank,
                direction=hit.direction,
                source="sms",
            )
            txn.category = self.categorize(txn)
            return txn

        # Regex miss — try the LLM extractor when enabled.
        if _finance_llm_enabled():
            extracted = _llm_extract_sms(text)
            if extracted and "amount" in extracted:
                try:
                    amount = float(extracted.get("amount", 0))
                except (TypeError, ValueError):
                    amount = 0.0
                if amount > 0:
                    merchant_token = _normalise_merchant_token(
                        str(extracted.get("merchant", "") or "")
                    )
                    last4_raw = str(extracted.get("account_last4", "") or "")
                    last4 = re.sub(r"[^0-9]", "", last4_raw)[-4:] or "0000"
                    direction = str(
                        extracted.get("direction", "debit") or "debit"
                    ).lower()
                    if direction not in ("debit", "credit"):
                        direction = "debit"
                    txn = Transaction(
                        amount=amount,
                        currency=str(
                            extracted.get("currency", "INR") or "INR"
                        ).upper(),
                        account_last4=last4,
                        ts=datetime.now(timezone.utc).replace(
                            year=fallback_year
                        ),
                        merchant_raw=merchant_token,
                        bank="LLM",
                        direction=direction,
                        source="sms",
                    )
                    txn.category = self.categorize(txn)
                    return txn

        self.unparsed_log.append(text)
        return None

    def parse_gmail_receipt(
        self, thread_meta: ThreadMeta, fallback_year: int = 2026
    ) -> Optional[Transaction]:
        """Resolve a Gmail receipt thread into a Transaction.

        Strategy:
        1. Match sender domain against the known merchant table.
        2. Extract amount from explicit ``thread_meta.amount`` if present,
           else from subject / snippet via regex.
        3. If amount is still missing, return a Transaction with
           ``amount=0`` and category=OTHER — we never silently drop, but the
           caller is expected to flag ``amount_inferred=False`` via the
           returned ``raw_id``.
        """
        domain = self._sender_domain(thread_meta.sender)
        merchant_token = (
            thread_meta.merchant
            or _GMAIL_DOMAIN_TO_MERCHANT.get(domain)
            or _normalise_merchant_token(domain)
        )
        amount = thread_meta.amount
        if amount is None:
            amount = self._extract_amount_from_subject(thread_meta.subject)
        if amount is None:
            amount = self._extract_amount_from_subject(thread_meta.snippet)
        if amount is None:
            amount = 0.0
        ts = thread_meta.ts or datetime.now(timezone.utc)
        txn = Transaction(
            amount=float(amount),
            currency="INR",
            account_last4="0000",  # not visible in mail
            ts=ts,
            merchant_raw=merchant_token,
            bank="",
            direction="debit",
            source="gmail",
            raw_id=thread_meta.thread_id,
        )
        txn.category = self.categorize(txn)
        return txn

    def categorize(self, txn: Transaction) -> Category:
        token = _normalise_merchant_token(txn.merchant_raw)
        cat = _MERCHANT_TO_CATEGORY.get(token)
        if cat is not None:
            return cat
        # keyword fallbacks
        m = txn.merchant_raw.lower()
        if any(k in m for k in ("food", "restaurant", "cafe")):
            return Category.FOOD_DELIVERY
        if any(k in m for k in ("rent", "landlord")):
            return Category.RENT
        if any(k in m for k in ("@upi", "paytm", "phonepe", "gpay")) and txn.amount < 500:
            return Category.P2P_TRANSFER
        return Category.OTHER

    def anomaly_flag(
        self,
        history: list[Transaction],
        window_days: int = 14,
        as_of: Optional[datetime] = None,
    ) -> list[Anomaly]:
        """Z-score per-category against the previous ``window_days``.

        ``window_days`` is the lookback used for the count-based anomaly;
        the velocity vs. 30-day mean stays fixed (per spec)
        because the pilot baseline is monthly.
        """
        as_of = as_of or datetime.now(timezone.utc)
        recent_window = as_of - timedelta(days=window_days)
        long_window = as_of - timedelta(days=self.rolling_window_days)
        anomalies: list[Anomaly] = []

        # Per-category daily-spend Z-score
        per_cat_daily: dict[Category, dict[str, float]] = {}
        for txn in history:
            if txn.ts < long_window:
                continue
            cat = txn.category or Category.OTHER
            day = txn.ts.date().isoformat()
            per_cat_daily.setdefault(cat, {}).setdefault(day, 0.0)
            per_cat_daily[cat][day] += txn.amount

        for cat, daily_map in per_cat_daily.items():
            values = list(daily_map.values())
            if len(values) < 3:
                continue
            mean = statistics.fmean(values)
            stdev = statistics.pstdev(values) if len(values) > 1 else 0.0
            if stdev == 0:
                continue
            today_key = as_of.date().isoformat()
            today_spend = daily_map.get(today_key, 0.0)
            if today_spend == 0:
                continue
            z = (today_spend - mean) / stdev
            if abs(z) >= self.z_threshold_high:
                severity = "high"
            elif abs(z) >= self.z_threshold_medium:
                severity = "medium"
            else:
                continue
            anomalies.append(
                Anomaly(
                    reason=f"{cat.value} spend {z:+.1f}σ vs {self.rolling_window_days}d mean",
                    severity=severity,
                    category=cat,
                    z_score=z,
                )
            )

        # Velocity anomaly: same-category txn count in last `window_days`
        from collections import Counter

        recent_counts: Counter[Category] = Counter()
        baseline_counts: Counter[Category] = Counter()
        for txn in history:
            cat = txn.category or Category.OTHER
            if txn.ts >= recent_window:
                recent_counts[cat] += 1
            elif txn.ts >= long_window:
                baseline_counts[cat] += 1

        baseline_per_window = max(1, self.rolling_window_days // window_days)
        for cat, recent_n in recent_counts.items():
            baseline_n = baseline_counts.get(cat, 0) / baseline_per_window
            if baseline_n < 1:
                continue
            ratio = recent_n / baseline_n
            if ratio >= 3.0:
                anomalies.append(
                    Anomaly(
                        reason=f"{cat.value} {recent_n}x in {window_days}d vs baseline {baseline_n:.1f}",
                        severity="high",
                        category=cat,
                        z_score=ratio,
                    )
                )
            elif ratio >= 2.0:
                anomalies.append(
                    Anomaly(
                        reason=f"{cat.value} {recent_n}x in {window_days}d vs baseline {baseline_n:.1f}",
                        severity="medium",
                        category=cat,
                        z_score=ratio,
                    )
                )
        return anomalies

    def predict_eom_balance(
        self,
        history: list[Transaction],
        balance: Balance,
        as_of: Optional[datetime] = None,
    ) -> Projection:
        """End-of-month balance projection.

        Strategy:
        1. Linear extrapolation from the last 7 days of net debits (recent
           behaviour is more predictive than the 14-day average for
           students whose week-to-week spend swings).
        2. Add known recurring debits — RENT and any SUBSCRIPTIONS that have
           hit at least twice in the rolling window — that have not yet
           landed this calendar month.
        3. ``confidence`` is a coarse heuristic based on history depth and
           coefficient of variation; capped at 0.85 because the linear
           extrapolation never has the precision of the Phase-2 LSTM.
        """
        as_of = as_of or datetime.now(timezone.utc)
        lookback_start = as_of - timedelta(days=7)

        debits_per_day: dict[str, float] = {}
        for txn in history:
            if txn.ts < lookback_start or txn.direction != "debit":
                continue
            day = txn.ts.date().isoformat()
            debits_per_day.setdefault(day, 0.0)
            debits_per_day[day] += txn.amount

        if not debits_per_day:
            return Projection(
                balance_eom=balance.amount, hits_zero=None, confidence=0.2
            )

        daily = list(debits_per_day.values())
        burn = statistics.fmean(daily)
        var = statistics.pstdev(daily) if len(daily) > 1 else 0.0
        cv = (var / burn) if burn else 0.0

        # Days remaining in this calendar month
        next_month = (as_of.replace(day=28) + timedelta(days=4)).replace(day=1)
        days_remaining = max(0, (next_month - as_of).days)

        projected_burn = burn * days_remaining

        # Add known scheduled debits not yet seen this month.
        scheduled = self._scheduled_debits_remaining(history, as_of)
        projected_burn += scheduled

        balance_eom = balance.amount - projected_burn

        hits_zero: Optional[str] = None
        if burn > 0 and balance.amount > 0:
            days_to_zero = balance.amount / burn
            if days_to_zero < days_remaining:
                hits_zero = (as_of + timedelta(days=days_to_zero)).date().isoformat()

        # confidence: lower with high coefficient of variation, higher with depth
        depth_factor = min(1.0, len(daily) / 7.0)
        cv_factor = max(0.0, 1.0 - min(1.0, cv))
        confidence = round(0.4 + 0.45 * depth_factor * cv_factor, 2)
        confidence = min(confidence, 0.85)

        # Suppress projection if CI would be wider than 25% (spec failure mode)
        if cv > 0.6:
            return Projection(
                balance_eom=balance.amount, hits_zero=None, confidence=0.2
            )

        return Projection(
            balance_eom=round(balance_eom, 2),
            hits_zero=hits_zero,
            confidence=confidence,
        )

    @staticmethod
    def _scheduled_debits_remaining(
        history: list[Transaction], as_of: datetime
    ) -> float:
        """Sum of expected RENT + recurring SUBSCRIPTIONS not yet hit
        this calendar month.

        A subscription is "recurring" if the same merchant has hit at
        least twice in the past 60 days. RENT is identified by the
        :class:`Category.RENT` label (set by :meth:`categorize`).
        """
        cutoff = as_of - timedelta(days=60)
        merchant_hits: Counter[str] = Counter()
        merchant_amount: dict[str, float] = {}
        for t in history:
            if t.direction != "debit" or t.ts < cutoff:
                continue
            if t.category not in (Category.RENT, Category.SUBSCRIPTIONS):
                continue
            key = (t.merchant_hash or t.merchant_raw, t.category)
            merchant_hits[str(key)] += 1
            merchant_amount[str(key)] = t.amount

        # Already seen this calendar month?
        month_start = as_of.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        seen_this_month: set[str] = set()
        for t in history:
            if t.ts < month_start or t.direction != "debit":
                continue
            if t.category not in (Category.RENT, Category.SUBSCRIPTIONS):
                continue
            seen_this_month.add(str((t.merchant_hash or t.merchant_raw, t.category)))

        scheduled = 0.0
        for key, n in merchant_hits.items():
            if n >= 2 and key not in seen_this_month:
                scheduled += merchant_amount.get(key, 0.0)
        return scheduled

    def suggest_substitution(
        self,
        category_or_history,
        as_of: Optional[datetime] = None,
    ) -> Optional[Substitution]:
        """Return a frugal swap.

        Two call shapes are accepted for backwards compatibility with the
        original test suite and the new behaviour-driven contract:

        - ``suggest_substitution(Category.FOOD_DELIVERY)`` returns a
          deterministic table lookup (legacy path).
        - ``suggest_substitution(history)`` where ``history`` is a list of
          :class:`Transaction` triggers the real rule: 3+ Zomato or Swiggy
          orders within the last 7 days emits the "Cook tomorrow?" nudge
          with the average single-meal save (~₹400).
        """
        if isinstance(category_or_history, Category):
            return _STATIC_SUBSTITUTIONS.get(category_or_history)

        history: List[Transaction] = list(category_or_history)
        as_of = as_of or datetime.now(timezone.utc)
        cutoff = as_of - timedelta(days=7)

        food_orders = [
            t for t in history
            if t.ts >= cutoff
            and t.direction == "debit"
            and t.category == Category.FOOD_DELIVERY
            and _normalise_merchant_token(t.merchant_raw) in {"zomato", "swiggy"}
        ]
        if len(food_orders) < 3:
            return None
        avg_meal = statistics.fmean(t.amount for t in food_orders)
        save = round(avg_meal, 0) if avg_meal > 0 else 400.0
        return Substitution(
            from_category=Category.FOOD_DELIVERY,
            suggestion=(
                f"Cook tomorrow? You ordered {len(food_orders)} Zomato/Swiggy meals "
                f"in 7 days — typical home-cook save ~₹{int(save)}/meal."
            ),
            est_savings_inr=float(save),
        )

    # ---- agent entry-point ----------------------------------------------

    async def tick(self, agent_input: dict[str, Any]) -> dict[str, Any]:
        """Per-tick orchestrator entry point. Spec §3.3 input/output schema."""
        sms_unprocessed = agent_input.get("sms_unprocessed", [])
        gmail_receipts = agent_input.get("gmail_receipts", [])
        balance_seed = agent_input.get("balance_seed")
        history_in: Iterable[Any] = agent_input.get("history", [])
        tick_ts_raw = agent_input.get("tick_ts")
        tick_ts = (
            datetime.fromisoformat(tick_ts_raw)
            if tick_ts_raw
            else datetime.now(timezone.utc)
        )

        # Parse fresh
        new_txns: list[Transaction] = []
        for sms in sms_unprocessed:
            txn = self.parse_sms(sms.get("body", ""), fallback_year=tick_ts.year)
            if txn:
                txn.raw_id = sms.get("id", "")
                new_txns.append(txn)
        for r in gmail_receipts:
            tm = ThreadMeta(
                thread_id=r.get("thread_id", ""),
                sender=r.get("sender", ""),
                subject=r.get("subject", ""),
                snippet=r.get("snippet", ""),
                amount=r.get("amount"),
                merchant=r.get("merchant"),
                ts=datetime.fromisoformat(r["ts"]) if r.get("ts") else None,
            )
            txn = self.parse_gmail_receipt(tm, fallback_year=tick_ts.year)
            if txn:
                new_txns.append(txn)

        # Combined history
        history: list[Transaction] = list(self._coerce_history(history_in)) + new_txns

        # Today total
        today = tick_ts.date()
        today_total = sum(
            t.amount for t in history if t.ts.date() == today and t.direction == "debit"
        )
        # 30-day daily mean for vs_avg
        thirty_ago = tick_ts - timedelta(days=30)
        daily: dict[str, float] = {}
        for t in history:
            if t.ts < thirty_ago or t.direction != "debit":
                continue
            d = t.ts.date().isoformat()
            daily.setdefault(d, 0.0)
            daily[d] += t.amount
        avg = statistics.fmean(daily.values()) if daily else 0.0
        vs_avg_pct = round(((today_total - avg) / avg) * 100, 1) if avg else 0.0

        # Top category today
        from collections import Counter

        top_counter: Counter[str] = Counter()
        for t in history:
            if t.ts.date() == today and t.category:
                top_counter[t.category.value] += t.amount
        top_category = top_counter.most_common(1)[0][0] if top_counter else None

        # Anomalies
        anomalies = self.anomaly_flag(history, as_of=tick_ts)

        # Projection
        projection: Optional[Projection] = None
        if balance_seed:
            bal = Balance(
                account_hash=balance_seed.get("account_hash", ""),
                amount=float(balance_seed.get("amount", 0.0)),
                as_of=datetime.fromisoformat(balance_seed["as_of"]),
            )
            projection = self.predict_eom_balance(history, bal, as_of=tick_ts)

        return {
            "today_total": round(today_total, 2),
            "vs_avg_pct": vs_avg_pct,
            "top_category": top_category,
            "anomalies": [asdict(a) | {"category": a.category.value if a.category else None} for a in anomalies],
            "eom_projection": asdict(projection) if projection else None,
            "new_transactions": [t.to_persisted() for t in new_txns],
        }

    # ---- privacy ---------------------------------------------------------

    def persist(self, txn: Transaction) -> dict[str, Any]:
        """Return the only fields permitted to land in the memory graph."""
        return txn.to_persisted()

    # ---- diagnostics -----------------------------------------------------

    def diagnostic_accuracy(self) -> dict[str, Any]:
        """Replay the synthetic dataset through the parser pack and the
        merchant categoriser, return per-bank, per-merchant and overall
        accuracy. Used by the diagnostic CLI and by the test suite as the
        production gate (per-bank ≥0.95, per-merchant ≥0.90).
        """
        dataset = (
            Path(__file__).resolve().parents[2]
            / "datasets"
            / "finance"
            / "finance_train_synthetic.jsonl"
        )
        if not dataset.exists():
            return {"error": f"dataset missing: {dataset}"}

        sms_total: Counter[str] = Counter()
        sms_ok: Counter[str] = Counter()
        merchant_total: Counter[str] = Counter()
        merchant_ok: Counter[str] = Counter()
        gmail_total = 0
        gmail_ok = 0

        with dataset.open() as f:
            for line in f:
                row = __import__("json").loads(line)
                if row.get("source") == "sms":
                    bank = row.get("bank", "?")
                    sms_total[bank] += 1
                    txn = self.parse_sms(row["body"])
                    if (
                        txn
                        and txn.account_last4 == row["account_last4"]
                        and abs(txn.amount - row["amount"]) < 0.01
                    ):
                        sms_ok[bank] += 1
                else:
                    gmail_total += 1
                    tm = ThreadMeta(
                        thread_id=row["thread_id"],
                        sender=row["sender"],
                        subject=row.get("subject", ""),
                        snippet=row.get("snippet", ""),
                        amount=row.get("amount"),
                        merchant=row.get("merchant"),
                        ts=datetime.fromisoformat(row["ts"]) if row.get("ts") else None,
                    )
                    txn = self.parse_gmail_receipt(tm)
                    expected_cat = row.get("category", "")
                    if (
                        txn
                        and txn.category
                        and txn.category.value == expected_cat
                        and abs(txn.amount - row["amount"]) < 0.01
                    ):
                        gmail_ok += 1

                # per-merchant categorisation accuracy
                expected_cat = row.get("category", "")
                merchant_token = _normalise_merchant_token(str(row.get("merchant", "")))
                if expected_cat and merchant_token:
                    merchant_total[merchant_token] += 1
                    fake = Transaction(
                        amount=float(row.get("amount", 0)),
                        currency="INR",
                        account_last4="0000",
                        ts=datetime.now(timezone.utc),
                        merchant_raw=merchant_token,
                    )
                    cat = self.categorize(fake)
                    if cat.value == expected_cat:
                        merchant_ok[merchant_token] += 1

        per_bank = {
            b: round(sms_ok[b] / max(1, sms_total[b]), 4) for b in sms_total
        }
        per_merchant = {
            m: round(merchant_ok[m] / max(1, merchant_total[m]), 4)
            for m in merchant_total
        }
        sms_overall = sum(sms_ok.values()) / max(1, sum(sms_total.values()))
        merchant_overall = sum(merchant_ok.values()) / max(1, sum(merchant_total.values()))
        return {
            "sms_overall_accuracy": round(sms_overall, 4),
            "gmail_accuracy": round(gmail_ok / max(1, gmail_total), 4),
            "merchant_overall_accuracy": round(merchant_overall, 4),
            "per_bank": per_bank,
            "per_merchant": per_merchant,
            "sms_total": sum(sms_total.values()),
            "gmail_total": gmail_total,
        }

    # ---- internals -------------------------------------------------------

    def _regex_dispatch(self, text: str) -> Optional[_ParseHit]:
        """Dispatch to the per-bank parsers in :mod:`sms_patterns`.

        We keep a thin shim here so external callers can monkeypatch
        ``_regex_dispatch`` for tests / fault injection without touching
        the bank-pattern module.
        """
        hit = _sms_pattern_dispatch(text)
        if hit is None:
            return None
        return _ParseHit(
            amount=hit.amount,
            account_last4=hit.account_last4,
            merchant=hit.merchant,
            bank=hit.bank,
            direction=hit.direction,
            date_str=hit.date_str,
        )

    @staticmethod
    def _sender_domain(sender: str) -> str:
        s = sender.strip().lower()
        if "@" in s:
            s = s.split("@", 1)[1]
        return s.split(">")[0].strip()

    @staticmethod
    def _extract_amount_from_subject(text: str) -> Optional[float]:
        if not text:
            return None
        m = _GMAIL_SUBJECT_AMOUNT.search(text)
        if m:
            return _parse_amount(m.group(1))
        m = _GMAIL_SUBJECT_AMOUNT_BARE.search(text)
        if m:
            return _parse_amount(m.group(1))
        return None

    @staticmethod
    def _coerce_history(raw: Iterable[Any]) -> Iterable[Transaction]:
        for item in raw:
            if isinstance(item, Transaction):
                yield item
            elif isinstance(item, dict):
                ts = item.get("ts")
                if isinstance(ts, str):
                    ts = datetime.fromisoformat(ts)
                yield Transaction(
                    amount=float(item["amount"]),
                    currency=item.get("currency", "INR"),
                    account_last4=item.get("account_last4", "0000"),
                    ts=ts or datetime.now(timezone.utc),
                    merchant_raw=item.get("merchant_raw", item.get("merchant", "")),
                    category=Category(item["category"]) if item.get("category") else None,
                    direction=item.get("direction", "debit"),
                    source=item.get("source", "sms"),
                )
