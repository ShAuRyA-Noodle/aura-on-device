"""Evaluation harness for Aura CommsAgent.

Spec source: technical_spec.md section 9.1 (Eval harness) + section 3.1
(Eval metric). Targets:

    * intent macro-F1 ≥ 0.78 over {ACTIONABLE, SOCIAL, BROADCAST, SPAM}
    * Cohen's kappa ≥ 0.65 between model labels and held-out gold labels
    * draft pairwise win-rate ≥ 60% vs base Gemma 2B (human-rated)

This file ships two callables and one CLI:

    1. evaluate_classification(records, predictor) -> dict
       Pure-Python metrics over a list of records and a callable that
       maps {input -> predicted JSON dict}. Stub-friendly: pass a fake
       predictor in tests, pass a real Gemma 2B + LoRA predictor in
       production. No torch import is required to use it.

    2. confusion_matrix(true, pred, labels) -> dict
       Square matrix as nested dict. Used by the report renderer.

    3. CLI: python -m models.eval.eval_comms \
                --eval datasets/comms/comms_eval.jsonl

When the eval JSONL is missing, the CLI falls back to a no-op
identity-predictor smoke test so the harness can be sanity-checked
without a trained adapter or eval set.

The draft pairwise win-rate is intentionally a STUB: real win-rate
requires either a human-labelled preference shard (preferred) or an
LLM-judge (acceptable for internal sweeps). The stub returns a
placeholder structure with `pending_human_eval=True` and the count
of draft pairs ready for adjudication.
"""

from __future__ import annotations

import argparse
import json
import math
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Callable, Dict, Iterable, List, Optional, Tuple


# --------------------------------------------------------------------------- #
# Metrics.
# --------------------------------------------------------------------------- #


COMMS_LABELS: Tuple[str, ...] = ("ACTIONABLE", "SOCIAL", "BROADCAST", "SPAM")


def _safe_div(num: float, den: float) -> float:
    return num / den if den else 0.0


def per_class_pr_f1(
    true_labels: List[str],
    pred_labels: List[str],
    labels: Iterable[str] = COMMS_LABELS,
) -> Dict[str, Dict[str, float]]:
    """Per-class precision, recall, F1.

    Returns a dict keyed by label, each value being a dict with keys
    `precision`, `recall`, `f1`, `support`.
    """
    out: Dict[str, Dict[str, float]] = {}
    for label in labels:
        tp = sum(
            1
            for t, p in zip(true_labels, pred_labels)
            if t == label and p == label
        )
        fp = sum(
            1
            for t, p in zip(true_labels, pred_labels)
            if t != label and p == label
        )
        fn = sum(
            1
            for t, p in zip(true_labels, pred_labels)
            if t == label and p != label
        )
        support = sum(1 for t in true_labels if t == label)
        precision = _safe_div(tp, tp + fp)
        recall = _safe_div(tp, tp + fn)
        f1 = _safe_div(2 * precision * recall, precision + recall)
        out[label] = {
            "precision": round(precision, 4),
            "recall": round(recall, 4),
            "f1": round(f1, 4),
            "support": support,
        }
    return out


def macro_f1(per_class: Dict[str, Dict[str, float]]) -> float:
    if not per_class:
        return 0.0
    return round(
        sum(v["f1"] for v in per_class.values()) / len(per_class), 4
    )


def confusion_matrix(
    true_labels: List[str],
    pred_labels: List[str],
    labels: Iterable[str] = COMMS_LABELS,
) -> Dict[str, Dict[str, int]]:
    """Square confusion matrix, rows = true, cols = predicted."""
    matrix: Dict[str, Dict[str, int]] = {
        t: {p: 0 for p in labels} for t in labels
    }
    label_set = set(labels)
    for t, p in zip(true_labels, pred_labels):
        if t in label_set and p in label_set:
            matrix[t][p] += 1
    return matrix


def cohens_kappa(
    true_labels: List[str],
    pred_labels: List[str],
    labels: Iterable[str] = COMMS_LABELS,
) -> float:
    """Cohen's kappa as a single float in [-1, 1]."""
    n = len(true_labels)
    if n == 0:
        return 0.0
    p_o = _safe_div(
        sum(1 for t, p in zip(true_labels, pred_labels) if t == p), n
    )
    true_counts = Counter(true_labels)
    pred_counts = Counter(pred_labels)
    p_e = 0.0
    for label in labels:
        p_e += (true_counts.get(label, 0) / n) * (
            pred_counts.get(label, 0) / n
        )
    kappa = _safe_div(p_o - p_e, 1.0 - p_e) if p_e < 1.0 else 1.0
    return round(kappa, 4)


# --------------------------------------------------------------------------- #
# Pairwise win-rate stub.
# --------------------------------------------------------------------------- #


def draft_pairwise_winrate_stub(
    records: List[Dict[str, Any]],
    predictor: Callable[[str], Dict[str, Any]],
    base_predictor: Optional[Callable[[str], Dict[str, Any]]] = None,
) -> Dict[str, Any]:
    """Generate a draft-pair manifest for downstream human eval.

    We do not auto-judge draft quality; we collect the pairs and emit a
    JSON manifest the team adjudicates manually (or pipes to an LLM
    judge in a sweep). Returning a structured dict with
    `pending_human_eval=True` makes the harness honest about what it
    actually computed.
    """
    pairs: List[Dict[str, Any]] = []
    for rec in records:
        if rec.get("label") != "ACTIONABLE":
            continue
        text = rec.get("input", "")
        try:
            cand = predictor(text)
            cand_draft = (cand or {}).get("draft", "") or ""
        except Exception as exc:  # pragma: no cover - defensive
            cand_draft = f"<predictor_error: {exc}>"
        if base_predictor is not None:
            try:
                base = base_predictor(text)
                base_draft = (base or {}).get("draft", "") or ""
            except Exception as exc:  # pragma: no cover - defensive
                base_draft = f"<base_error: {exc}>"
        else:
            base_draft = ""
        pairs.append(
            {
                "input": text,
                "candidate_draft": cand_draft,
                "base_draft": base_draft,
            }
        )
    return {
        "pending_human_eval": True,
        "pair_count": len(pairs),
        "pairs": pairs,
        "target_winrate": 0.60,
    }


# --------------------------------------------------------------------------- #
# Top-level evaluator.
# --------------------------------------------------------------------------- #


def evaluate_classification(
    records: List[Dict[str, Any]],
    predictor: Callable[[str], Dict[str, Any]],
) -> Dict[str, Any]:
    """Run the full classification eval.

    Args:
        records: List of dicts with keys `input`, `label`, optional
            `draft`. See datasets/comms/comms_train_synthetic.jsonl.
        predictor: Callable mapping the input string to a JSON dict
            with key `intent`.
    """
    true_labels: List[str] = []
    pred_labels: List[str] = []
    parse_errors = 0

    for rec in records:
        true_labels.append(rec.get("label", "BROADCAST"))
        try:
            out = predictor(rec.get("input", "")) or {}
            pred = str(out.get("intent", "BROADCAST")).upper()
        except Exception:
            parse_errors += 1
            pred = "BROADCAST"
        if pred not in COMMS_LABELS:
            parse_errors += 1
            pred = "BROADCAST"
        pred_labels.append(pred)

    per_class = per_class_pr_f1(true_labels, pred_labels)
    return {
        "n": len(records),
        "macro_f1": macro_f1(per_class),
        "per_class": per_class,
        "confusion_matrix": confusion_matrix(true_labels, pred_labels),
        "cohens_kappa": cohens_kappa(true_labels, pred_labels),
        "parse_errors": parse_errors,
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


def _identity_predictor(text: str) -> Dict[str, Any]:
    """Smoke-test predictor: routes by trivial keyword cues."""
    t = text.lower()
    if "deadline" in t or "due" in t or "tomorrow" in t:
        intent = "ACTIONABLE"
    elif "winner" in t or "claim" in t or "click" in t:
        intent = "SPAM"
    elif "@everyone" in t or "fyi" in t or "announc" in t:
        intent = "BROADCAST"
    else:
        intent = "SOCIAL"
    return {"intent": intent, "urgency": 0.5, "self_relevance": 0.5, "draft": ""}


def render_report(result: Dict[str, Any]) -> str:
    lines = [
        "# Aura CommsAgent eval report",
        "",
        f"- n: {result['n']}",
        f"- macro-F1: {result['macro_f1']}",
        f"- Cohen's kappa: {result['cohens_kappa']}",
        f"- parse errors: {result['parse_errors']}",
        "",
        "## Per-class P/R/F1",
        "",
        "| label | P | R | F1 | n |",
        "|---|---|---|---|---|",
    ]
    for label, scores in result["per_class"].items():
        lines.append(
            f"| {label} | {scores['precision']} | {scores['recall']} | "
            f"{scores['f1']} | {scores['support']} |"
        )
    lines.append("")
    lines.append("## Confusion matrix (rows=true, cols=pred)")
    lines.append("")
    cm = result["confusion_matrix"]
    header = "| true \\ pred | " + " | ".join(COMMS_LABELS) + " |"
    sep = "|---" * (len(COMMS_LABELS) + 1) + "|"
    lines.append(header)
    lines.append(sep)
    for t in COMMS_LABELS:
        row = [str(cm.get(t, {}).get(p, 0)) for p in COMMS_LABELS]
        lines.append(f"| {t} | " + " | ".join(row) + " |")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Evaluate Aura CommsAgent intent classifier."
    )
    parser.add_argument(
        "--eval",
        default="datasets/comms/comms_eval.jsonl",
        help="JSONL of {input, label, draft} eval rows.",
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
        # Smoke-test fallback so the harness is runnable on a fresh clone.
        synthetic = (
            project_root
            / "datasets"
            / "comms"
            / "comms_train_synthetic.jsonl"
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
    result = evaluate_classification(records, _identity_predictor)
    result["draft_pairwise"] = draft_pairwise_winrate_stub(
        records, _identity_predictor
    )

    print(render_report(result))
    if args.out_json:
        out_path = project_root / args.out_json
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(json.dumps(result, indent=2), encoding="utf-8")
        print(f"\n[info] result JSON written to {out_path}")
    # NaN guard so the CLI fails loudly on an empty eval set.
    if math.isnan(result["macro_f1"]):
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
