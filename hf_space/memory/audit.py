"""Tamper-evident audit chain + daily Merkle root.

Implements technical_spec.md §6.8.

Two responsibilities:
1. Append-only hash chain: ``hash_chain[n] = sha256(prev_hash || canonical(row))``.
2. Per-day Merkle tree over the day's audit rows; the root is what the
   Settings UI shows. The user can store the root externally and produce
   an inclusion proof on demand.

Pure functions only — no DB access. The store imports these and writes the
result to the ``audit_log`` / ``merkle_daily`` tables.
"""

from __future__ import annotations

import hashlib
import json
from datetime import date as _date
from typing import Dict, Iterable, List, Sequence


def hash_canonical(value: object) -> str:
    """Deterministic SHA-256 over canonical JSON."""
    canonical = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def chain_next(prev_hash: str, row: Dict[str, object]) -> str:
    """Compute the next hash in the audit chain."""
    canonical = json.dumps(row, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    h = hashlib.sha256()
    h.update(prev_hash.encode("utf-8"))
    h.update(canonical.encode("utf-8"))
    return h.hexdigest()


def compute_daily_merkle(rows: Sequence[Dict[str, object]], when: _date) -> str:
    """Per-day Merkle root over canonical-JSON rows.

    Empty days produce a deterministic ``sha256(b"empty:" + iso_date)`` so the
    UI always has a value to display. Odd leaf counts are handled by
    duplicating the last leaf, per spec §6.8.
    """
    if not rows:
        seed = f"empty:{when.isoformat()}".encode("utf-8")
        return hashlib.sha256(seed).hexdigest()

    leaves: List[bytes] = []
    for r in rows:
        canonical = json.dumps(r, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
        leaves.append(hashlib.sha256(canonical.encode("utf-8")).digest())

    while len(leaves) > 1:
        if len(leaves) % 2 == 1:
            leaves.append(leaves[-1])  # duplicate last for odd count
        leaves = [
            hashlib.sha256(a + b).digest() for a, b in zip(leaves[::2], leaves[1::2])
        ]
    return leaves[0].hex()


def merkle_inclusion_proof(
    rows: Sequence[Dict[str, object]], target_index: int
) -> List[str]:
    """Return sibling hashes (hex) for an inclusion proof of ``target_index``.

    Used by the audit-export UI: a user can re-derive the daily root from the
    leaf + this proof to prove a given trace existed at end-of-day.
    """
    if not 0 <= target_index < len(rows):
        raise ValueError("target_index out of range")
    leaves: List[bytes] = []
    for r in rows:
        canonical = json.dumps(r, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
        leaves.append(hashlib.sha256(canonical.encode("utf-8")).digest())

    proof: List[str] = []
    idx = target_index
    while len(leaves) > 1:
        if len(leaves) % 2 == 1:
            leaves.append(leaves[-1])
        sibling = idx ^ 1  # flip last bit -> sibling index
        proof.append(leaves[sibling].hex())
        leaves = [hashlib.sha256(a + b).digest() for a, b in zip(leaves[::2], leaves[1::2])]
        idx //= 2
    return proof


def verify_inclusion(
    leaf_canonical_json: str,
    target_index: int,
    proof: Iterable[str],
    expected_root_hex: str,
) -> bool:
    """Verify a Merkle inclusion proof. Returns True on match."""
    h = hashlib.sha256(leaf_canonical_json.encode("utf-8")).digest()
    idx = target_index
    for sib_hex in proof:
        sib = bytes.fromhex(sib_hex)
        if idx & 1:
            h = hashlib.sha256(sib + h).digest()
        else:
            h = hashlib.sha256(h + sib).digest()
        idx //= 2
    return h.hex() == expected_root_hex
