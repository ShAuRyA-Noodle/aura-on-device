-- Aura on-device memory graph schema.
-- Mirrors technical_spec.md §6.2 verbatim, with two pragmatic additions:
--   * `embeddings_local` table is a portable fallback used when sqlite-vss is
--     not loaded (e.g. test envs). Production uses the `embeddings_vss`
--     virtual table; both are kept in sync via embedding_refs.rowid.
--   * `audit_log.payload_json` mirrors the row that was appended for replay.

PRAGMA journal_mode = WAL;
PRAGMA foreign_keys = ON;

-- Nodes -------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS nodes (
    id              TEXT PRIMARY KEY,
    type            TEXT NOT NULL,
    data_json       TEXT NOT NULL,
    ts              INTEGER NOT NULL,
    retention_class TEXT NOT NULL DEFAULT 'default',
    CHECK (type IN ('User','Event','App','Person','Place','Transaction','Conversation','HealthSnapshot','Action','Trace'))
);
CREATE INDEX IF NOT EXISTS idx_nodes_type_ts ON nodes(type, ts DESC);
CREATE INDEX IF NOT EXISTS idx_nodes_ts ON nodes(ts DESC);

-- Edges -------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS edges (
    id     TEXT PRIMARY KEY,
    src    TEXT NOT NULL REFERENCES nodes(id) ON DELETE CASCADE,
    dst    TEXT NOT NULL REFERENCES nodes(id) ON DELETE CASCADE,
    type   TEXT NOT NULL,
    weight REAL DEFAULT 1.0,
    ts     INTEGER NOT NULL,
    CHECK (type IN ('attended','sent_to','located_at','paid_to','talked_about','felt_during','triggered_by','confirmed_by_user'))
);
CREATE INDEX IF NOT EXISTS idx_edges_src_type ON edges(src, type);
CREATE INDEX IF NOT EXISTS idx_edges_dst_type ON edges(dst, type);

-- Reasoning traces (separate for fast purge) -----------------------------
CREATE TABLE IF NOT EXISTS traces (
    trace_id     TEXT PRIMARY KEY,
    ts           INTEGER NOT NULL,
    payload_json TEXT NOT NULL,
    outcome      TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_traces_ts ON traces(ts DESC);
CREATE INDEX IF NOT EXISTS idx_traces_outcome ON traces(outcome);

-- Embedding refs ---------------------------------------------------------
-- rowid is what sqlite-vss vss0 indexes by. The local fallback table
-- mirrors the same rowid so the application code is identical.
CREATE TABLE IF NOT EXISTS embedding_refs (
    rowid     INTEGER PRIMARY KEY,
    node_id   TEXT NOT NULL REFERENCES nodes(id) ON DELETE CASCADE,
    chunk_idx INTEGER NOT NULL,
    text_hash TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_emb_refs_node ON embedding_refs(node_id);

-- Local fallback embeddings table — used when sqlite-vss is not loaded.
-- ``vector`` is a JSON array of 384 floats.
CREATE TABLE IF NOT EXISTS embeddings_local (
    rowid  INTEGER PRIMARY KEY REFERENCES embedding_refs(rowid) ON DELETE CASCADE,
    vector TEXT NOT NULL
);

-- Audit log (append-only) -----------------------------------------------
CREATE TABLE IF NOT EXISTS audit_log (
    seq         INTEGER PRIMARY KEY AUTOINCREMENT,
    ts          INTEGER NOT NULL,
    op          TEXT NOT NULL,
    target_type TEXT,
    target_id   TEXT,
    agent       TEXT,
    payload_json TEXT,
    hash_chain  TEXT NOT NULL,
    CHECK (op IN ('read','write','delete','export','wipe','delete_range','rotate'))
);
CREATE INDEX IF NOT EXISTS idx_audit_ts ON audit_log(ts);

-- Daily Merkle roots ----------------------------------------------------
CREATE TABLE IF NOT EXISTS merkle_daily (
    date         TEXT PRIMARY KEY,
    root         TEXT NOT NULL,
    leaf_count   INTEGER NOT NULL,
    computed_ts  INTEGER NOT NULL
);

-- User settings ---------------------------------------------------------
CREATE TABLE IF NOT EXISTS settings (
    key        TEXT PRIMARY KEY,
    value_json TEXT NOT NULL,
    updated_ts INTEGER NOT NULL
);
