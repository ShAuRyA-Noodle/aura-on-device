"""Builder for the finance synthetic dataset (200 SMS + 100 Gmail = 300 rows).

Banks covered: HDFC, SBI, ICICI, Axis, Kotak, PNB.
Merchants covered: Zomato, Swiggy, Blinkit, Amazon, IRCTC, Uber, BookMyShow,
Myntra, Flipkart, Ajio, plus utility / subscription / transport extras.

The generated lines mirror real Indian bank SMS templates in production
inboxes. Each bank's pattern is stable enough that the regex parser in
``agents/finance/sms_patterns.py`` can hit ``>=95%`` accuracy.

Run::

    python -m datasets.finance.build_synthetic
"""

from __future__ import annotations

import json
import random
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Dict, List, Tuple

# (merchant_token, category)
MERCHANTS_DEBIT: List[Tuple[str, str]] = [
    ("ZOMATO", "food_delivery"),
    ("SWIGGY", "food_delivery"),
    ("BLINKIT", "groceries"),
    ("BIGBASKET", "groceries"),
    ("AMAZON", "shopping"),
    ("FLIPKART", "shopping"),
    ("MYNTRA", "shopping"),
    ("AJIO", "shopping"),
    ("IRCTC", "travel"),
    ("UBER", "transport"),
    ("OLA", "transport"),
    ("RAPIDO", "transport"),
    ("NAMMA-METRO", "transport"),
    ("BOOKMYSHOW", "entertainment"),
    ("PVR", "entertainment"),
    ("NETFLIX", "subscriptions"),
    ("SPOTIFY", "subscriptions"),
    ("HOTSTAR", "subscriptions"),
    ("AIRTEL", "bills_utilities"),
    ("JIO", "bills_utilities"),
    ("TATAPOWER", "bills_utilities"),
    ("ZERODHA", "investment"),
    ("GROWW", "investment"),
    ("PHARMEASY", "health"),
    ("PRACTO", "health"),
    ("UNACADEMY", "education"),
]

CREDIT_SOURCES: List[str] = [
    "STIPEND-INTERN",
    "PROJECT-INVOICE",
    "MOM-TRANSFER",
    "REFUND-AMAZON",
    "REFUND-SWIGGY",
]

# Bangalore / Patiala names occasionally appear in P2A descriptions
P2A_TAGS = ["Uber", "Zomato", "Swiggy", "Blinkit", "Amazon", "Myntra", "Flipkart", "Ajio", "BookMyShow", "IRCTC"]


def _date_str_dd_mon(dt: datetime, style: str) -> str:
    """Render the same datetime in the format each bank uses."""
    if style == "dd-MON":
        return dt.strftime("%d-%b").upper()  # 07-MAY
    if style == "dd-MM-yy":
        return dt.strftime("%d-%m-%y")  # 07-05-26
    if style == "dd-Mon-yy":
        return dt.strftime("%d-%b-%y")  # 07-May-26
    if style == "dd-MON-yy":
        return dt.strftime("%d-%b-%y").upper()  # 07-MAY-26
    if style == "ddMonyy":
        return dt.strftime("%d%b%y").upper()  # 07MAY26
    if style == "dd/MM/yyyy":
        return dt.strftime("%d/%m/%Y")
    if style == "dd-MON-yyyy":
        return dt.strftime("%d-%b-%Y").upper()
    raise ValueError(style)


# --------------------------------------------------------------------------
# Per-bank SMS template generators
# --------------------------------------------------------------------------


def hdfc_sms(merchant: str, amount: float, acct: str, dt: datetime, direction: str = "debit") -> str:
    # HDFC usually uses "Sent Rs.X from A/c **NNNN to MERCHANT via UPI on dd-MON"
    # OR  "Sent Rs. X From HDFC Bank A/C *NNNN To VPA m@hdfcbank On dd-mm-yy"
    if direction == "credit":
        return f"Received Rs.{amount:.2f} from {merchant} in A/c **{acct} via UPI on {_date_str_dd_mon(dt, 'dd-MON')}"
    if random.random() < 0.5:
        return f"Sent Rs.{amount:.2f} from A/c **{acct} to {merchant} via UPI on {_date_str_dd_mon(dt, 'dd-MON')}"
    return f"Sent Rs. {amount:.2f} From HDFC Bank A/C *{acct} To VPA {merchant.lower()}@hdfcbank On {_date_str_dd_mon(dt, 'dd-MM-yy')}"


def sbi_sms(merchant: str, amount: float, acct: str, dt: datetime, direction: str = "debit") -> str:
    # Real SBI: "Dear Customer, Rs.X debited from A/c X1234 on dd-MM-yy to VPA m@oksbi Ref nnn. -SBI"
    direction_word = "debited" if direction == "debit" else "credited"
    handle_root = merchant.lower().replace(" ", "")
    return (
        f"Dear Customer, Rs.{amount:.2f} {direction_word} from A/c X{acct} on {_date_str_dd_mon(dt, 'dd-MM-yy')} "
        f"to VPA {handle_root}@oksbi Ref {random.randint(400000, 499999)}. -SBI"
    )


def icici_sms(merchant: str, amount: float, acct: str, dt: datetime, direction: str = "debit") -> str:
    # ICICI card: "INR X.YY spent on ICICI Bank Card XX1234 at MERCHANT on dd-Mon-yy"
    # ICICI UPI:  "Dear Customer, Acct XX1234 debited with INR X on dd-Mon-yy; UPI:nnnn; toward m@icici."
    if random.random() < 0.5:
        return f"INR {amount:.2f} spent on ICICI Bank Card XX{acct} at {merchant} on {_date_str_dd_mon(dt, 'dd-Mon-yy')}"
    handle = merchant.lower().replace(" ", "")
    return (
        f"Dear Customer, Acct XX{acct} debited with INR {amount:.2f} on {_date_str_dd_mon(dt, 'dd-Mon-yy')}; "
        f"UPI:{random.randint(412000000000, 412999999999)}; toward {handle}@icici."
    )


def axis_sms(merchant: str, amount: float, acct: str, dt: datetime, direction: str = "debit") -> str:
    # Axis: "INR X debited A/c no. XX1234 dd-MM-yy HH:MM UPI/P2A/m@axis/Tag"
    direction_word = "debited" if direction == "debit" else "credited"
    handle = merchant.lower().replace(" ", "")
    tag = random.choice(P2A_TAGS)
    return (
        f"INR {amount:.2f} {direction_word} A/c no. XX{acct} {_date_str_dd_mon(dt, 'dd-MM-yy')} "
        f"{dt.strftime('%H:%M')} UPI/P2A/{handle}@axis/{tag}"
    )


def kotak_sms(merchant: str, amount: float, acct: str, dt: datetime, direction: str = "debit") -> str:
    # Kotak (real format):
    # "Sent Rs.X to MERCHANT from Kotak Bank A/c x1234. UPI Ref nnn. dd-MON-yy"
    # alt: "Rs.X debited from Kotak A/c x1234 to m@kotak on dd-MON-yyyy."
    if direction == "credit":
        return f"Rs.{amount:.2f} credited to Kotak A/c x{acct} from {merchant} on {_date_str_dd_mon(dt, 'dd-MON-yy')}. -Kotak"
    if random.random() < 0.5:
        return (
            f"Sent Rs.{amount:.2f} to {merchant} from Kotak Bank A/c x{acct}. "
            f"UPI Ref {random.randint(400000000, 499999999)}. {_date_str_dd_mon(dt, 'dd-MON-yy')}"
        )
    handle = merchant.lower().replace(" ", "")
    return (
        f"Rs.{amount:.2f} debited from Kotak A/c x{acct} to {handle}@kotak on "
        f"{_date_str_dd_mon(dt, 'dd-MON-yyyy')}. -Kotak"
    )


def pnb_sms(merchant: str, amount: float, acct: str, dt: datetime, direction: str = "debit") -> str:
    # PNB typical formats:
    # "Rs.X debited Ac XXXXNNNN on dd-MM-yyyy to MERCHANT. UPI/RefNNN. PNB"
    # "Ac XXNNNN debited by Rs.X on dd/MM/yyyy at MERCHANT. PNB"
    direction_word = "debited" if direction == "debit" else "credited"
    if random.random() < 0.5:
        return (
            f"Rs.{amount:.2f} {direction_word} Ac XXXX{acct} on {_date_str_dd_mon(dt, 'dd-MM-yy')} "
            f"to {merchant}. UPI/Ref{random.randint(100000, 999999)}. PNB"
        )
    return (
        f"Ac XX{acct} {direction_word} by Rs.{amount:.2f} on {_date_str_dd_mon(dt, 'dd/MM/yyyy')} "
        f"at {merchant}. PNB"
    )


BANK_GENERATORS = {
    "HDFC": hdfc_sms,
    "SBI": sbi_sms,
    "ICICI": icici_sms,
    "Axis": axis_sms,
    "Kotak": kotak_sms,
    "PNB": pnb_sms,
}


# --------------------------------------------------------------------------
# Gmail receipt generator (10 merchants × 10 examples)
# --------------------------------------------------------------------------


GMAIL_MERCHANTS: Dict[str, Dict[str, str]] = {
    "zomato": {"sender": "orders@zomato.com", "category": "food_delivery"},
    "swiggy": {"sender": "noreply@swiggy.in", "category": "food_delivery"},
    "blinkit": {"sender": "noreply@blinkit.com", "category": "groceries"},
    "amazon": {"sender": "auto-confirm@amazon.in", "category": "shopping"},
    "irctc": {"sender": "ticket-no-reply@irctc.co.in", "category": "travel"},
    "uber": {"sender": "receipts@uber.com", "category": "transport"},
    "bookmyshow": {"sender": "noreply@bookmyshow.com", "category": "entertainment"},
    "myntra": {"sender": "orders@myntra.com", "category": "shopping"},
    "flipkart": {"sender": "no-reply@flipkart.com", "category": "shopping"},
    "ajio": {"sender": "orders@ajio.com", "category": "shopping"},
}


def gmail_subject(merchant: str, amount: float) -> Tuple[str, str]:
    formats = {
        "zomato": (f"Zomato — Rs. {amount:.0f} paid", "Order delivered."),
        "swiggy": (f"Order delivered — Total Rs. {amount:.0f}", "Late lunch from Truffles."),
        "blinkit": (f"Blinkit order — INR {amount:.0f} charged", "Groceries delivered in 9 minutes."),
        "amazon": (f"Your Amazon.in order of Rs.{amount:,.2f}", "Arriving Friday."),
        "irctc": (f"IRCTC ticket booked — PNR {random.randint(8000000000, 8999999999)} Rs. {amount:.0f}", "Train departing."),
        "uber": (f"Your trip with Uber — Rs. {amount:.0f}", "From PG to office."),
        "bookmyshow": (f"BookMyShow — ticket Rs. {amount:.0f}", "PVR Forum Mall."),
        "myntra": (f"Your Myntra order — Rs. {amount:.0f} paid", "Order confirmed."),
        "flipkart": (f"Flipkart order placed — Rs. {amount:.0f}", "Out for delivery."),
        "ajio": (f"Ajio order — Rs. {amount:.0f}", "Confirmed, arriving in 3 days."),
    }
    return formats[merchant]


# --------------------------------------------------------------------------
# Builder
# --------------------------------------------------------------------------


def build_sms(n: int = 200, seed: int = 7) -> List[dict]:
    random.seed(seed)
    rows: List[dict] = []
    banks = list(BANK_GENERATORS.keys())
    base_dt = datetime(2026, 5, 1, 9, 0, tzinfo=timezone.utc)

    # 25% credit (income) for HDFC + Kotak (only banks with credit forms in
    # this fixture). The rest are debits across the 26 merchants.
    for i in range(n):
        bank = banks[i % len(banks)]
        merchant_token, category = random.choice(MERCHANTS_DEBIT)
        amount = round(random.uniform(45.0, 4500.0), 2)
        acct = str(random.randint(1000, 9999))
        dt = base_dt + timedelta(hours=random.randint(0, 24 * 30))
        direction = "debit"
        if bank in {"HDFC", "Kotak"} and random.random() < 0.08:
            # Occasional credit
            direction = "credit"
            merchant_token = random.choice(CREDIT_SOURCES)
            category = "p2p_transfer"
        body = BANK_GENERATORS[bank](merchant_token, amount, acct, dt, direction)
        rows.append({
            "id": f"s_{i+1:03d}",
            "from": _bank_sender(bank),
            "body": body,
            "ts": dt.isoformat(),
            "merchant": merchant_token.title(),
            "amount": amount,
            "currency": "INR",
            "account_last4": acct,
            "category": category,
            "source": "sms",
            "bank": bank,
            "direction": direction,
            "provenance": "synthetic",
        })
    return rows


def _bank_sender(bank: str) -> str:
    return {
        "HDFC": "VK-HDFCBK",
        "SBI": "AX-SBIINB",
        "ICICI": "VK-ICICIB",
        "Axis": "VM-AXISBK",
        "Kotak": "AD-KOTAKB",
        "PNB": "AY-PNBSMS",
    }[bank]


def build_gmail(n: int = 100, seed: int = 11) -> List[dict]:
    random.seed(seed)
    rows: List[dict] = []
    merchants = list(GMAIL_MERCHANTS.keys())
    base_dt = datetime(2026, 5, 1, 8, 0, tzinfo=timezone.utc)
    for i in range(n):
        merchant = merchants[i % len(merchants)]
        info = GMAIL_MERCHANTS[merchant]
        amount = round(random.uniform(75.0, 3600.0), 2)
        subject, snippet = gmail_subject(merchant, amount)
        dt = base_dt + timedelta(hours=random.randint(0, 24 * 30))
        rows.append({
            "thread_id": f"tg_r{i+1:03d}",
            "sender": info["sender"],
            "subject": subject,
            "snippet": snippet,
            "amount": amount,
            "merchant": merchant,
            "ts": dt.isoformat(),
            "category": info["category"],
            "source": "gmail",
            "bank": None,
            "provenance": "synthetic",
        })
    return rows


def main() -> None:
    out = Path(__file__).parent / "finance_train_synthetic.jsonl"
    rows = build_sms(200) + build_gmail(100)
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("w") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    print(f"wrote {len(rows)} rows to {out}")


if __name__ == "__main__":
    main()
