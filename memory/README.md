# Memory graph

Per `technical_spec.md` §6 + plan.md §14.

SQLite (WAL) with `sqlite-vss` for vector search and a per-day Merkle root
over the audit log for tamper evidence. Encryption at rest is platform-side
(Knox / iOS Secure Enclave); see `technical_spec.md` §6.7.

## Files

| File | Purpose |
|---|---|
| `schema.sql` | Canonical DDL (nodes, edges, traces, embeddings, audit_log, merkle_daily, settings). |
| `migrations/0001_init.sql` | First migration — applies the same schema; tracked via `schema_migrations`. |
| `store.py` | `MemoryGraph`: `add_node`, `add_edge`, `embed`, `search`, `delete_by_time_range`, `export_json`, `daily_merkle_root`, `audit_append`, `add_trace`. |
| `audit.py` | Pure: `chain_next`, `compute_daily_merkle`, `merkle_inclusion_proof`, `verify_inclusion`, `hash_canonical`. |
| `test_memory.py` | Round-trip tests for all of the above. |

## sqlite-vss shim

Production uses the [`sqlite-vss`](https://github.com/asg017/sqlite-vss)
extension built per platform:

- **macOS arm64 (dev)**: drop `vss0.dylib` into `aura/memory/` next to this
  package; the store calls `conn.load_extension("vss0.dylib")` automatically.
- **iOS**: link the static library into the SwiftPM target; load via
  `try db.execute(sql: "SELECT load_extension('vss0')")`.
- **Android**: ship `libvss0.so` in `app/src/main/jniLibs/<abi>/`; load via
  `db.execSQL("SELECT load_extension('libvss0.so')")`. Note: some Android
  SQLite builds disable `load_extension` by default — TEAM TO VERIFY a custom
  build is needed (see <https://github.com/asg017/sqlite-vss/issues>).

When the extension is unavailable the store transparently falls back to a
local `embeddings_local` table + Python cosine search. The application code
is identical — search returns the same `[{node_id, score, type, ts, data}]`
shape.

## Embedding model

`sentence-transformers/all-MiniLM-L6-v2` (384-d). When the package is not
installed, the store uses a deterministic hash-bucket embedding so tests
exercise the search path on a clean venv.

## Audit + Merkle

Every write goes through `audit_append`, which computes
`hash_chain[n] = sha256(prev_hash || canonical(row))`. At 00:05 local time
(or on demand for tests) `daily_merkle_root` walks the day's audit rows and
stores the Merkle root in `merkle_daily`. Settings UI displays the latest 30
roots; the user can store a root externally and produce an inclusion proof
on demand via `merkle_inclusion_proof` + `verify_inclusion`.

## Run tests

```bash
pytest memory -q
```
