"""Per-bank Indian SMS regex patterns.

Each bank ships a stable family of UPI / debit alert templates. Real
production SMS from May-2026 inboxes were the reference; the patterns below
accept the common variants and reject ambiguous strings rather than guess.

Required capture fields per bank:
    - amount       (float-able string, may contain commas)
    - account_last4 (4 digits)
    - merchant      (token, may include dots, @ and dashes)
    - direction     ("debit" | "credit" | "refund" | "fee")
    - date_str      (raw, parsed by ``_parse_date_loose`` in agent.py)

Each pattern is documented inline with a representative real-world example
from each bank.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Optional

# --------------------------------------------------------------------------
# Shared atoms
# --------------------------------------------------------------------------

_AMOUNT = r"(?:Rs\.?|INR|₹)\s*([0-9]+(?:[,][0-9]+)*(?:\.[0-9]{1,2})?)"
_DATE_LOOSE = r"([0-9]{1,2}[-/][A-Za-z0-9]{2,4}(?:[-/][0-9]{2,4})?)"


@dataclass
class ParseHit:
    amount: float
    account_last4: str
    merchant: str
    bank: str
    direction: str  # debit | credit | refund | fee
    date_str: str


def _amount_to_float(raw: str) -> float:
    return float(raw.replace(",", ""))


# --------------------------------------------------------------------------
# HDFC
# --------------------------------------------------------------------------
# Examples seen:
#   "Sent Rs.350.00 from A/c **1234 to ZOMATO via UPI on 07-MAY"
#   "Sent Rs. 450.00 From HDFC Bank A/C *1234 To VPA zomato@hdfcbank On 07-05-26"
#   "Received Rs.85,000.00 from PROJECT-INVOICE in A/c **1234 via UPI on 04-MAY"

_HDFC_DEBIT = re.compile(
    r"Sent\s+" + _AMOUNT
    + r".*?(?:from|From)\s+(?:HDFC\s+Bank\s+)?A/[Cc]\s*\*+\s*([0-9]{4})"
    + r".*?(?:to|To)\s+(?:VPA\s+)?(?P<m>[A-Za-z0-9@._\-]+)"
    + r".*?(?:via\s+UPI|on)\s+" + _DATE_LOOSE,
    re.IGNORECASE | re.DOTALL,
)

_HDFC_CREDIT = re.compile(
    r"Received\s+" + _AMOUNT
    + r".*?from\s+(?P<m>[A-Za-z0-9@._\-]+)\s+in\s+A/[Cc]\s*\*+\s*([0-9]{4})"
    + r".*?on\s+" + _DATE_LOOSE,
    re.IGNORECASE | re.DOTALL,
)


def parse_hdfc(text: str) -> Optional[ParseHit]:
    m = _HDFC_DEBIT.search(text)
    if m:
        return ParseHit(
            amount=_amount_to_float(m.group(1)),
            account_last4=m.group(2),
            merchant=m.group("m"),
            bank="HDFC",
            direction="debit",
            date_str=m.group(4),
        )
    m = _HDFC_CREDIT.search(text)
    if m:
        return ParseHit(
            amount=_amount_to_float(m.group(1)),
            account_last4=m.group(3),
            merchant=m.group("m"),
            bank="HDFC",
            direction="credit",
            date_str=m.group(4),
        )
    return None


# --------------------------------------------------------------------------
# SBI
# --------------------------------------------------------------------------
# Example:
#   "Dear Customer, Rs.1200.00 debited from A/c X1234 on 07-05-26 to VPA
#    bigbasket@okhdfc Ref 412345. -SBI"

_SBI = re.compile(
    r"Rs\.?\s*([0-9]+(?:[,][0-9]+)*(?:\.[0-9]{1,2})?)\s+(?P<dir>debited|credited)\s+from\s+A/[Cc]\s*[Xx*]+\s*([0-9]{4})"
    + r"\s+on\s+" + _DATE_LOOSE
    + r"\s+(?:to|from)\s+(?:VPA\s+)?(?P<m>[A-Za-z0-9@._\-]+)",
    re.IGNORECASE,
)


def parse_sbi(text: str) -> Optional[ParseHit]:
    m = _SBI.search(text)
    if not m:
        return None
    return ParseHit(
        amount=_amount_to_float(m.group(1)),
        account_last4=m.group(3),
        merchant=m.group("m"),
        bank="SBI",
        direction="debit" if m.group("dir").lower() == "debited" else "credit",
        date_str=m.group(4),
    )


# --------------------------------------------------------------------------
# ICICI (card + UPI)
# --------------------------------------------------------------------------
# Card:
#   "INR 250.00 spent on ICICI Bank Card XX1234 at SWIGGY on 07-May-26"
# UPI:
#   "Dear Customer, Acct XX1234 debited with INR 800.00 on 07-May-26;
#    UPI:412345678912; toward swiggy@icici."

_ICICI_CARD = re.compile(
    r"INR\s+([0-9]+(?:\.[0-9]{1,2})?)\s+spent\s+on\s+ICICI\s+Bank\s+(?:Card|Acct|A/c)\s*[Xx*]+\s*([0-9]{4})"
    + r"\s+at\s+(?P<m>[A-Za-z0-9@._\-]+?)\s+on\s+" + _DATE_LOOSE,
    re.IGNORECASE,
)
_ICICI_UPI = re.compile(
    r"Acct\s+[Xx*]+\s*([0-9]{4})\s+debited\s+with\s+INR\s+([0-9]+(?:\.[0-9]{1,2})?)"
    + r"\s+on\s+" + _DATE_LOOSE
    + r".*?toward\s+(?P<m>[A-Za-z0-9@._\-]+)",
    re.IGNORECASE | re.DOTALL,
)


def parse_icici(text: str) -> Optional[ParseHit]:
    m = _ICICI_CARD.search(text)
    if m:
        return ParseHit(
            amount=_amount_to_float(m.group(1)),
            account_last4=m.group(2),
            merchant=m.group("m"),
            bank="ICICI",
            direction="debit",
            date_str=m.group(4),
        )
    m = _ICICI_UPI.search(text)
    if m:
        return ParseHit(
            amount=_amount_to_float(m.group(2)),
            account_last4=m.group(1),
            merchant=m.group("m"),
            bank="ICICI",
            direction="debit",
            date_str=m.group(3),
        )
    return None


# --------------------------------------------------------------------------
# Axis
# --------------------------------------------------------------------------
# Example:
#   "INR 540 debited A/c no. XX1234 07-05-26 13:42 UPI/P2A/uber@axis/Uber"

_AXIS = re.compile(
    r"INR\s+([0-9]+(?:\.[0-9]{1,2})?)\s+(?P<dir>debited|credited)\s+A/c\s+no\.?\s*[Xx*]+\s*([0-9]{4})"
    + r"\s+" + _DATE_LOOSE
    + r".*?UPI/[A-Z0-9]+/(?P<m>[A-Za-z0-9@._\-]+)",
    re.IGNORECASE,
)


def parse_axis(text: str) -> Optional[ParseHit]:
    m = _AXIS.search(text)
    if not m:
        return None
    return ParseHit(
        amount=_amount_to_float(m.group(1)),
        account_last4=m.group(3),
        merchant=m.group("m"),
        bank="AXIS",
        direction="debit" if m.group("dir").lower() == "debited" else "credit",
        date_str=m.group(4),
    )


# --------------------------------------------------------------------------
# Kotak
# --------------------------------------------------------------------------
# Examples:
#   "Sent Rs.X to MERCHANT from Kotak Bank A/c x1234. UPI Ref nnn. 07-MAY-26"
#   "Rs.X debited from Kotak A/c x1234 to m@kotak on 07-MAY-2026. -Kotak"
#   "Rs.X credited to Kotak A/c x1234 from STIPEND-INTERN on 07-MAY-26. -Kotak"

_KOTAK_SENT = re.compile(
    r"Sent\s+Rs\.?\s*([0-9]+(?:[,][0-9]+)*(?:\.[0-9]{1,2})?)\s+to\s+(?P<m>[A-Za-z0-9@._\-]+)\s+from\s+Kotak\s+Bank\s+A/c\s+x([0-9]{4})"
    + r".*?\.?\s*" + _DATE_LOOSE,
    re.IGNORECASE | re.DOTALL,
)
_KOTAK_DEBITED = re.compile(
    r"Rs\.?\s*([0-9]+(?:[,][0-9]+)*(?:\.[0-9]{1,2})?)\s+(?P<dir>debited|credited)(?:\s+from)?\s+(?:to\s+)?Kotak\s+A/c\s+x([0-9]{4})"
    + r"\s+(?:to|from)\s+(?P<m>[A-Za-z0-9@._\-]+)\s+on\s+" + _DATE_LOOSE,
    re.IGNORECASE,
)


def parse_kotak(text: str) -> Optional[ParseHit]:
    m = _KOTAK_SENT.search(text)
    if m:
        return ParseHit(
            amount=_amount_to_float(m.group(1)),
            account_last4=m.group(3),
            merchant=m.group("m"),
            bank="KOTAK",
            direction="debit",
            date_str=m.group(4),
        )
    m = _KOTAK_DEBITED.search(text)
    if m:
        return ParseHit(
            amount=_amount_to_float(m.group(1)),
            account_last4=m.group(3),
            merchant=m.group("m"),
            bank="KOTAK",
            direction="debit" if m.group("dir").lower() == "debited" else "credit",
            date_str=m.group(5),
        )
    return None


# --------------------------------------------------------------------------
# PNB
# --------------------------------------------------------------------------
# Examples:
#   "Rs.X debited Ac XXXX1234 on 07-05-26 to MERCHANT. UPI/Ref888. PNB"
#   "Ac XX1234 debited by Rs.X on 07/05/2026 at MERCHANT. PNB"

_PNB_DEBITED_TO = re.compile(
    r"Rs\.?\s*([0-9]+(?:[,][0-9]+)*(?:\.[0-9]{1,2})?)\s+(?P<dir>debited|credited)\s+Ac\s+[Xx*]+\s*([0-9]{4})"
    + r"\s+on\s+" + _DATE_LOOSE
    + r"\s+to\s+(?P<m>[A-Za-z0-9@._\-]+)",
    re.IGNORECASE,
)
_PNB_DEBITED_AT = re.compile(
    r"Ac\s+[Xx*]+\s*([0-9]{4})\s+(?P<dir>debited|credited)\s+by\s+Rs\.?\s*([0-9]+(?:[,][0-9]+)*(?:\.[0-9]{1,2})?)"
    + r"\s+on\s+" + _DATE_LOOSE
    + r"\s+at\s+(?P<m>[A-Za-z0-9@._\-]+)",
    re.IGNORECASE,
)


def parse_pnb(text: str) -> Optional[ParseHit]:
    m = _PNB_DEBITED_TO.search(text)
    if m:
        return ParseHit(
            amount=_amount_to_float(m.group(1)),
            account_last4=m.group(3),
            merchant=m.group("m"),
            bank="PNB",
            direction="debit" if m.group("dir").lower() == "debited" else "credit",
            date_str=m.group(4),
        )
    m = _PNB_DEBITED_AT.search(text)
    if m:
        return ParseHit(
            amount=_amount_to_float(m.group(3)),
            account_last4=m.group(1),
            merchant=m.group("m"),
            bank="PNB",
            direction="debit" if m.group("dir").lower() == "debited" else "credit",
            date_str=m.group(4),
        )
    return None


# --------------------------------------------------------------------------
# Refund / fee detection (any bank)
# --------------------------------------------------------------------------
# Refund SMS share the same skeleton as a credit but contain the keyword
# "refund" or "REFUND" in the merchant token. Fees are usually flagged with
# "service charge" / "fee" / "charge debited".

_REFUND_HINT = re.compile(r"\brefund\b", re.IGNORECASE)
_FEE_HINT = re.compile(r"\b(service\s+charge|charge|fee)\b", re.IGNORECASE)


def refine_direction(hit: ParseHit, raw_text: str) -> ParseHit:
    """Promote 'credit' to 'refund' or 'debit' to 'fee' based on keywords."""
    if _REFUND_HINT.search(raw_text) or "REFUND" in hit.merchant.upper():
        return ParseHit(
            amount=hit.amount,
            account_last4=hit.account_last4,
            merchant=hit.merchant,
            bank=hit.bank,
            direction="refund",
            date_str=hit.date_str,
        )
    if hit.direction == "debit" and _FEE_HINT.search(raw_text) and hit.amount < 100:
        return ParseHit(
            amount=hit.amount,
            account_last4=hit.account_last4,
            merchant=hit.merchant,
            bank=hit.bank,
            direction="fee",
            date_str=hit.date_str,
        )
    return hit


PARSERS = (parse_hdfc, parse_sbi, parse_icici, parse_axis, parse_kotak, parse_pnb)


def dispatch(text: str) -> Optional[ParseHit]:
    """Try each bank parser in priority order, return the first hit."""
    for fn in PARSERS:
        hit = fn(text)
        if hit is not None:
            return refine_direction(hit, text)
    return None
