"""Aura FinanceAgent.

Handles UPI SMS parsing, Gmail receipt parsing, transaction categorisation,
anomaly detection, end-of-month balance projection, and substitution
suggestions. All on-device. Persists only minimal redacted fields per
technical_spec §3.3.
"""

from .agent import (
    Anomaly,
    Balance,
    Category,
    FinanceAgent,
    Projection,
    Substitution,
    Transaction,
)

__all__ = [
    "FinanceAgent",
    "Transaction",
    "Anomaly",
    "Balance",
    "Category",
    "Projection",
    "Substitution",
]
