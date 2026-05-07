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
import re
import statistics
from dataclasses import asdict, dataclass, field
from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Any, Iterable, Optional


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

        Returns ``None`` for non-financial / unparseable strings (and pushes
        them to ``unparsed_log`` for the DistilBERT fallback queue).
        """
        text = text.strip()
        hit = self._regex_dispatch(text)
        if hit is None:
            self.unparsed_log.append(text)
            return None
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
        """Linear-burn EoM projection.

        Phase 1: linear extrapolation of the last 14 days' net debit.
        Phase 2: drop in 2-layer LSTM trained on personal trace.
        ``confidence`` is a coarse heuristic based on history depth and
        variance; never reports >0.85 from this stub.
        """
        as_of = as_of or datetime.now(timezone.utc)
        lookback_start = as_of - timedelta(days=14)
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
        balance_eom = balance.amount - projected_burn

        hits_zero: Optional[str] = None
        if burn > 0 and balance.amount > 0:
            days_to_zero = balance.amount / burn
            if days_to_zero < days_remaining:
                hits_zero = (as_of + timedelta(days=days_to_zero)).date().isoformat()

        # confidence: lower with high coefficient of variation, higher with depth
        depth_factor = min(1.0, len(daily) / 14.0)
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

    def suggest_substitution(self, category: Category) -> Optional[Substitution]:
        """Return a frugal swap for the given category, or None."""
        table: dict[Category, Substitution] = {
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
        }
        return table.get(category)

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

    # ---- internals -------------------------------------------------------

    def _regex_dispatch(self, text: str) -> Optional[_ParseHit]:
        # HDFC — groups: 1=dir, 2=amount, 3=acct, 4=merchant, 5=date.
        m = _HDFC.search(text)
        if m:
            return _ParseHit(
                amount=_parse_amount(m.group(2)),
                account_last4=m.group(3),
                merchant=m.group("m"),
                bank="HDFC",
                direction="debit" if m.group("dir").lower().startswith(("sent", "debit")) else "credit",
                date_str=m.group(5),
            )
        # SBI — groups: 1=dir, 2=acct (named), 3=date, 4=merchant.
        m = _SBI.search(text)
        if m:
            am = _SBI_AMOUNT.search(text)
            if am:
                return _ParseHit(
                    amount=_parse_amount(am.group(1)),
                    account_last4=m.group("acct"),
                    merchant=m.group("m"),
                    bank="SBI",
                    direction="debit" if m.group("dir").lower() == "debited" else "credit",
                    date_str=m.group(3),
                )
        # ICICI card — groups: 1=amount, 2=acct, 3=merchant, 4=date.
        m = _ICICI.search(text)
        if m:
            return _ParseHit(
                amount=_parse_amount(m.group(1)),
                account_last4=m.group(2),
                merchant=m.group("m"),
                bank="ICICI",
                direction="debit",
                date_str=m.group(4),
            )
        # ICICI UPI — groups: 1=acct, 2=amount, 3=date, 4=merchant.
        m = _ICICI_UPI.search(text)
        if m:
            return _ParseHit(
                amount=_parse_amount(m.group(2)),
                account_last4=m.group(1),
                merchant=m.group("m"),
                bank="ICICI",
                direction="debit",
                date_str=m.group(3),
            )
        # Axis — groups: 1=amount, 2=dir, 3=acct, 4=date, 5=merchant.
        m = _AXIS.search(text)
        if m:
            return _ParseHit(
                amount=_parse_amount(m.group(1)),
                account_last4=m.group(3),
                merchant=m.group("m"),
                bank="AXIS",
                direction="debit" if m.group("dir").lower() == "debited" else "credit",
                date_str=m.group(4),
            )
        return None

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
