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
extension. The Python `sqlite_vss` package ships pre-built `vector0` +
`vss0` extensions for macOS arm64, macOS x86_64, and Linux x86_64, so the
typical dev install is:

```bash
pip install sqlite-vss
```

`store.py` then calls `sqlite_vss.load(conn)` automatically. Verify with:

```bash
python -c "import sqlite_vss, sqlite3; \
  c=sqlite3.connect(':memory:'); c.enable_load_extension(True); \
  sqlite_vss.load(c); \
  print(c.execute('select vss_version()').fetchone())"
```

If the wheel is unavailable for your platform, drop `vss0.dylib` (macOS) or
`libvss0.so` (Linux/Android) next to this package and the loader will pick
it up. iOS / Android cross-platform notes:

- **iOS**: link the static library into the SwiftPM target; load via
  `try db.execute(sql: "SELECT load_extension('vss0')")`.
- **Android**: ship `libvss0.so` in `app/src/main/jniLibs/<abi>/`; load via
  `db.execSQL("SELECT load_extension('libvss0.so')")`. Some stock Android
  SQLite builds disable `load_extension` — a custom build is required.

When the extension is unavailable the store transparently falls back to a
local `embeddings_local` table + Python cosine search. The application code
is identical — `search` returns the same `[{node_id, score, type, ts, data}]`
shape.

## Embedding model

`sentence-transformers/all-MiniLM-L6-v2` (384-d). The model is downloaded
once and cached on disk under `$AURA_MODEL_CACHE` (default
`~/.cache/aura/models/`). Install with:

```bash
pip install sentence-transformers
```

Set `AURA_MEMORY_FORCE_HASH_EMBED=1` to skip the heavy load (used by the
fast unit-test path); the deterministic hash-bucket fallback then exercises
the same `search` API with a worse-but-fast embedding.

## Encryption at rest (SQLCipher)

The store optionally opens its connection through
[`pysqlcipher3`](https://pypi.org/project/pysqlcipher3/) for transparent
AES-256 encryption at rest. Enable by setting `AURA_MEMORY_KEY` to the
passphrase before constructing `MemoryGraph`. If `pysqlcipher3` isn't
installed the store logs a warning and falls back to plain `sqlite3`.

Manual install (when the pip wheel isn't available for your platform):

```bash
# macOS arm64 — build SQLCipher with OpenSSL via Homebrew, then build the
# Python binding against it.
brew install sqlcipher openssl@3
export C_INCLUDE_PATH=$(brew --prefix sqlcipher)/include
export LIBRARY_PATH=$(brew --prefix sqlcipher)/lib
SQLCIPHER_PATH="$(brew --prefix sqlcipher)" \
  pip install --no-binary :all: pysqlcipher3
```

For Linux build:

```bash
sudo apt-get install -y libsqlcipher-dev
pip install --no-binary :all: pysqlcipher3
```

For iOS / Android, link the SQLCipher amalgamation into the platform
target and use the platform driver (GRDB on iOS, SupportSQLiteDatabase on
Android). The Python binding is dev-only.

## JSON Schema for export

`export_json()` validates its return value against `export_schema.json`
(JSON Schema draft-07). The schema is shipped with the package; the
`jsonschema` validator is required at runtime (`pip install jsonschema`).

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
