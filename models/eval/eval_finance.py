"""Evaluation harness for Aura FinanceAgent.

Spec source: technical_spec.md section 9.2 + section 3.3 (Eval metric).
Targets:

    * SMS parse F1 ≥ 0.95 over the canonical fields
      (merchant, amount, currency, account_last4)
    * Categorisation accuracy ≥ 0.90 across the 14 fixed categories
    * Per-merchant precision/recall reported for the top 8 Indian
      merchants we ship a regex pack for: Zomato, Swiggy, Blinkit,
      Amazon, IRCTC, Uber, Ola, BMTC.

Like eval_comms.py this module is pure-Python by default. The CLI
entrypoint runs against a JSONL eval set and a stubbed
identity-predictor that uses a thin regex bank to give realistic
non-trivial numbers without requiring a trained adapter.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Callable, Dict, Iterable, List, Optional, Tuple


FINANCE_CATEGORIES: Tuple[str, ...] = (
    "food_delivery",
    "groceries",
    "transport",
    "fuel",
    "entertainment",
    "education",
    "rent",
    "utilities",
    "shopping",
    "health",
    "transfer_in",
    "transfer_out",
    "subscriptions",
    "other",
)


TOP_MERCHANTS: Tuple[str, ...] = (
    "Zomato",
    "Swiggy",
    "Blinkit",
    "Amazon",
    "IRCTC",
    "Uber",
    "Ola",
    "BMTC",
)


# --------------------------------------------------------------------------- #
# Field-level metrics.
# --------------------------------------------------------------------------- #


def _safe_div(num: float, den: float) -> float:
    return num / den if den else 0.0


def field_match(true: Dict[str, Any], pred: Dict[str, Any], field: str) -> bool:
    """Tolerant equality for one extraction field."""
    t = true.get(field)
    p = pred.get(field)
    if field == "amount":
        try:
            return abs(float(t) - float(p)) < 0.5
        except (TypeError, ValueError):
            return False
    if t is None and p is None:
        return True
    if t is None or p is None:
        return False
    return str(t).strip().lower() == str(p).strip().lower()


def parse_f1(
    records: List[Dict[str, Any]],
    predictions: List[Dict[str, Any]],
    fields: Iterable[str] = ("merchant", "amount", "currency", "account_last4"),
) -> Dict[str, Dict[str, float]]:
    """Per-field precision/recall/F1 across the eval set."""
    result: Dict[str, Dict[str, float]] = {}
    for field in fields:
        tp = 0
        fp = 0
        fn = 0
        for true, pred in zip(records, predictions):
            t_present = true.get(field) not in (None, "")
            p_present = pred.get(field) not in (None, "")
            match = field_match(true, pred, field)
            if t_present and p_present and match:
                tp += 1
            elif p_present and not match:
                fp += 1
            elif t_present and not match:
                fn += 1
        precision = _safe_div(tp, tp + fp)
        recall = _safe_div(tp, tp + fn)
        f1 = _safe_div(2 * precision * recall, precision + recall)
        result[field] = {
            "precision": round(precision, 4),
            "recall": round(recall, 4),
            "f1": round(f1, 4),
        }
    return result


def categorisation_accuracy(
    records: List[Dict[str, Any]],
    predictions: List[Dict[str, Any]],
) -> Dict[str, Any]:
    n = len(records)
    correct = sum(
        1
        for t, p in zip(records, predictions)
        if str(t.get("category", "")).lower()
        == str(p.get("category", "")).lower()
    )
    return {
        "n": n,
        "accuracy": round(_safe_div(correct, n), 4),
        "correct": correct,
    }


def per_merchant_pr(
    records: List[Dict[str, Any]],
    predictions: List[Dict[str, Any]],
    merchants: Iterable[str] = TOP_MERCHANTS,
) -> Dict[str, Dict[str, float]]:
    """Precision/recall per merchant (case-insensitive)."""
    out: Dict[str, Dict[str, float]] = {}
    for merchant in merchants:
        m = merchant.lower()
        tp = 0
        fp = 0
        fn = 0
        for true, pred in zip(records, predictions):
            t_match = str(true.get("merchant", "")).lower() == m
            p_match = str(pred.get("merchant", "")).lower() == m
            if t_match and p_match:
                tp += 1
            elif p_match and not t_match:
                fp += 1
            elif t_match and not p_match:
                fn += 1
        out[merchant] = {
            "precision": round(_safe_div(tp, tp + fp), 4),
            "recall": round(_safe_div(tp, tp + fn), 4),
            "support": tp + fn,
        }
    return out


# --------------------------------------------------------------------------- #
# Stub regex predictor (good enough for harness sanity checks).
# --------------------------------------------------------------------------- #


_AMOUNT_RX = re.compile(r"(?:Rs\.?|INR|₹)\s*([0-9,]+(?:\.\d{1,2})?)", re.IGNORECASE)
_LAST4_RX = re.compile(r"(?:A/c|XXXX|x{2,})\s*\*?\*?(\d{4})", re.IGNORECASE)


_MERCHANT_KEYWORDS: Tuple[Tuple[str, str, str], ...] = (
    ("zomato", "Zomato", "food_delivery"),
    ("swiggy", "Swiggy", "food_delivery"),
    ("blinkit", "Blinkit", "groceries"),
    ("instamart", "Swiggy Instamart", "groceries"),
    ("zepto", "Zepto", "groceries"),
    ("bigbasket", "BigBasket", "groceries"),
    ("amazon", "Amazon", "shopping"),
    ("flipkart", "Flipkart", "shopping"),
    ("irctc", "IRCTC", "transport"),
    ("uber", "Uber", "transport"),
    ("ola", "Ola", "transport"),
    ("bmtc", "BMTC", "transport"),
    ("netflix", "Netflix", "subscriptions"),
    ("spotify", "Spotify", "subscriptions"),
    ("hotstar", "Hotstar", "entertainment"),
    ("airtel", "Airtel", "utilities"),
    ("jio", "Jio", "utilities"),
)


def _stub_predict(text: str) -> Dict[str, Any]:
    t = text.lower()
    merchant = ""
    category = "other"
    for needle, name, cat in _MERCHANT_KEYWORDS:
        if needle in t:
            merchant = name
            category = cat
            break

    amount = 0.0
    m = _AMOUNT_RX.search(text)
    if m:
        try:
            amount = float(m.group(1).replace(",", ""))
        except ValueError:
            amount = 0.0

    last4: Optional[str] = None
    m4 = _LAST4_RX.search(text)
    if m4:
        last4 = m4.group(1)

    return {
        "merchant": merchant,
        "amount": amount,
        "currency": "INR",
        "account_last4": last4,
        "ts": None,
        "category": category,
    }


# --------------------------------------------------------------------------- #
# Top-level evaluator.
# --------------------------------------------------------------------------- #


def evaluate_finance(
    records: List[Dict[str, Any]],
    predictor: Callable[[str], Dict[str, Any]],
) -> Dict[str, Any]:
    predictions: List[Dict[str, Any]] = []
    parse_errors = 0
    for rec in records:
        try:
            predictions.append(predictor(rec.get("input", "")) or {})
        except Exception:
            parse_errors += 1
            predictions.append({})
    return {
        "n": len(records),
        "parse_errors": parse_errors,
        "field_metrics": parse_f1(records, predictions),
        "categorisation": categorisation_accuracy(records, predictions),
        "per_merchant": per_merchant_pr(records, predictions),
    }


# --------------------------------------------------------------------------- #
# I/O.
# --------------------------------------------------------------------------- #


def load_jsonl(path: Path) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    with open(path, "r", encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            rows.append(json.loads(line))
    return rows


def render_report(result: Dict[str, Any]) -> str:
    lines = [
        "# Aura FinanceAgent eval report",
        "",
        f"- n: {result['n']}",
        f"- parse errors: {result['parse_errors']}",
        f"- categorisation accuracy: "
        f"{result['categorisation']['accuracy']} "
        f"({result['categorisation']['correct']}/"
        f"{result['categorisation']['n']})",
        "",
        "## Field metrics",
        "",
        "| field | P | R | F1 |",
        "|---|---|---|---|",
    ]
    for field, scores in result["field_metrics"].items():
        lines.append(
            f"| {field} | {scores['precision']} | {scores['recall']} | "
            f"{scores['f1']} |"
        )
    lines.append("")
    lines.append("## Per-merchant P/R")
    lines.append("")
    lines.append("| merchant | P | R | n |")
    lines.append("|---|---|---|---|")
    for merchant, scores in result["per_merchant"].items():
        lines.append(
            f"| {merchant} | {scores['precision']} | {scores['recall']} | "
            f"{scores['support']} |"
        )
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Evaluate Aura FinanceAgent on Indian-bank SMS + receipts."
    )
    parser.add_argument(
        "--eval",
        default="datasets/finance/finance_eval.jsonl",
        help="JSONL of finance eval rows.",
    )
    parser.add_argument(
        "--project-root",
        default=str(Path(__file__).resolve().parents[2]),
    )
    parser.add_argument(
        "--out-json",
        default="",
        help="Optional path to dump the result dict as JSON.",
    )
    args = parser.parse_args()
    project_root = Path(args.project_root).resolve()

    eval_path = project_root / args.eval
    if not eval_path.exists():
        synthetic = (
            project_root
            / "datasets"
            / "finance"
            / "finance_train_synthetic.jsonl"
        )
        if synthetic.exists():
            print(
                f"[warn] {eval_path} missing; falling back to {synthetic}",
                file=sys.stderr,
            )
            eval_path = synthetic
        else:
            print(
                f"[fatal] no eval data at {eval_path} or {synthetic}",
                file=sys.stderr,
            )
            return 2

    records = load_jsonl(eval_path)
    result = evaluate_finance(records, _stub_predict)
    print(render_report(result))
    if args.out_json:
        out_path = project_root / args.out_json
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(json.dumps(result, indent=2), encoding="utf-8")
        print(f"\n[info] result JSON written to {out_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
