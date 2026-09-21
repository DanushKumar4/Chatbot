-- Agent system tables for Supabase (PostgreSQL)

CREATE TABLE IF NOT EXISTS thread (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    customer_id     BIGINT REFERENCES customer(id) ON DELETE CASCADE,
    title           TEXT DEFAULT 'New Conversation',
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS message (
    id              BIGSERIAL PRIMARY KEY,
    thread_id       UUID REFERENCES thread(id) ON DELETE CASCADE,
    seq             INTEGER NOT NULL,
    role            TEXT NOT NULL CHECK (role IN ('user', 'assistant', 'system', 'tool')),
    content         TEXT NOT NULL,
    agent_name      TEXT,
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(thread_id, seq)
);

CREATE TABLE IF NOT EXISTS agent_log (
    id              BIGSERIAL PRIMARY KEY,
    thread_id       UUID REFERENCES thread(id) ON DELETE CASCADE,
    run_id          TEXT NOT NULL,
    agent_name      TEXT NOT NULL,
    action          TEXT NOT NULL,
    detail          JSONB,
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS run (
    id               TEXT PRIMARY KEY,
    thread_id        UUID REFERENCES thread(id) ON DELETE CASCADE,
    status           TEXT DEFAULT 'queued' CHECK (status IN ('queued', 'running', 'succeeded', 'failed', 'cancelled', 'dead')),
    routed_to        TEXT,
    lease_owner      TEXT,
    lease_until      TIMESTAMPTZ,
    attempts         INTEGER DEFAULT 0,
    cancel_requested BOOLEAN DEFAULT FALSE,
    available_at     TIMESTAMPTZ DEFAULT NOW(),
    started_at       TIMESTAMPTZ,
    completed_at     TIMESTAMPTZ,
    created_at       TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS run_step (
    id              TEXT PRIMARY KEY,
    run_id          TEXT REFERENCES run(id) ON DELETE CASCADE,
    step_seq        INTEGER NOT NULL,
    step_type       TEXT NOT NULL CHECK (step_type IN ('model', 'tool')),
    detail          JSONB,
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS idempotency (
    key             TEXT PRIMARY KEY,
    result          TEXT NOT NULL,
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_message_thread ON message(thread_id, seq);
CREATE INDEX IF NOT EXISTS idx_agent_log_thread ON agent_log(thread_id);
CREATE INDEX IF NOT EXISTS idx_run_thread ON run(thread_id);
CREATE INDEX IF NOT EXISTS idx_run_step_run ON run_step(run_id, step_seq);
CREATE INDEX IF NOT EXISTS idx_run_status ON run(status);
