-- Bank domain tables for Supabase (PostgreSQL)

CREATE TABLE IF NOT EXISTS customer (
    id              BIGSERIAL PRIMARY KEY,
    full_name       TEXT NOT NULL,
    email           TEXT UNIQUE NOT NULL,
    phone           TEXT,
    pan_number      TEXT UNIQUE,
    aadhar_number   TEXT UNIQUE,
    date_of_birth   DATE,
    address         TEXT,
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS account (
    id              BIGSERIAL PRIMARY KEY,
    customer_id     BIGINT REFERENCES customer(id) ON DELETE CASCADE,
    account_number  TEXT UNIQUE NOT NULL,
    account_type    TEXT NOT NULL CHECK (account_type IN ('savings', 'current', 'fixed_deposit')),
    balance         NUMERIC(15, 2) DEFAULT 0.00,
    status          TEXT DEFAULT 'active' CHECK (status IN ('active', 'frozen', 'closed')),
    opened_at       TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS transaction (
    id              BIGSERIAL PRIMARY KEY,
    account_id      BIGINT REFERENCES account(id) ON DELETE CASCADE,
    txn_type        TEXT NOT NULL CHECK (txn_type IN ('credit', 'debit', 'transfer')),
    amount          NUMERIC(15, 2) NOT NULL,
    description     TEXT,
    reference_id    TEXT UNIQUE,
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS loan (
    id              BIGSERIAL PRIMARY KEY,
    customer_id     BIGINT REFERENCES customer(id) ON DELETE CASCADE,
    loan_type       TEXT NOT NULL CHECK (loan_type IN ('home', 'personal', 'car', 'education')),
    principal       NUMERIC(15, 2) NOT NULL,
    interest_rate   NUMERIC(5, 2) NOT NULL,
    tenure_months   INTEGER NOT NULL,
    emi             NUMERIC(15, 2),
    status          TEXT DEFAULT 'pending' CHECK (status IN ('pending', 'approved', 'rejected', 'disbursed', 'closed')),
    applied_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS card (
    id              BIGSERIAL PRIMARY KEY,
    customer_id     BIGINT REFERENCES customer(id) ON DELETE CASCADE,
    card_number     TEXT UNIQUE NOT NULL,
    card_type       TEXT NOT NULL CHECK (card_type IN ('debit', 'credit')),
    credit_limit    NUMERIC(15, 2),
    outstanding     NUMERIC(15, 2) DEFAULT 0.00,
    status          TEXT DEFAULT 'active' CHECK (status IN ('active', 'blocked', 'expired')),
    expiry_date     DATE NOT NULL,
    issued_at       TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS complaint (
    id              BIGSERIAL PRIMARY KEY,
    customer_id     BIGINT REFERENCES customer(id) ON DELETE CASCADE,
    category        TEXT NOT NULL CHECK (category IN ('transaction', 'loan', 'card', 'account', 'other')),
    subject         TEXT NOT NULL,
    description     TEXT NOT NULL,
    status          TEXT DEFAULT 'open' CHECK (status IN ('open', 'in_progress', 'resolved', 'closed')),
    priority        TEXT DEFAULT 'medium' CHECK (priority IN ('low', 'medium', 'high', 'critical')),
    resolution      TEXT,
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    resolved_at     TIMESTAMPTZ
);

-- Indexes for common lookups
CREATE INDEX IF NOT EXISTS idx_account_customer ON account(customer_id);
CREATE INDEX IF NOT EXISTS idx_transaction_account ON transaction(account_id);
CREATE INDEX IF NOT EXISTS idx_loan_customer ON loan(customer_id);
CREATE INDEX IF NOT EXISTS idx_card_customer ON card(customer_id);
CREATE INDEX IF NOT EXISTS idx_complaint_customer ON complaint(customer_id);
