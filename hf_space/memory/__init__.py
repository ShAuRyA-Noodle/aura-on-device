"""Aura on-device memory graph package.

Implements technical_spec.md §6 + §14.

The store is SQLite (WAL) plus a sentence-transformers `all-MiniLM-L6-v2`
embedding model behind a sqlite-vss virtual table. On clean test envs without
sentence-transformers / sqlite-vss installed, the store falls back to a
deterministic hash-bucket embedding and an in-memory cosine search so the
schema, audit chain, and Merkle daily root are exercised without heavy deps.

Public API:
- :class:`MemoryGraph` — high-level: ``add_node``, ``add_edge``, ``embed``,
  ``search``, ``delete_by_time_range``, ``export_json``, ``daily_merkle_root``,
  ``audit_append``.
- :func:`compute_daily_merkle` — pure function for unit tests.
"""

from .store import MemoryGraph
from .audit import compute_daily_merkle, hash_canonical

__all__ = ["MemoryGraph", "compute_daily_merkle", "hash_canonical"]
