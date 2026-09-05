-- ============================================
-- FRAUD DETECTION DATABASE SCHEMA
-- ============================================

-- 1. Transactions table
CREATE TABLE transactions (
    transaction_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    customer_id TEXT NOT NULL,

    transaction_time TIMESTAMPTZ NOT NULL,

    merchant TEXT,
    category TEXT,
    amount NUMERIC(12, 2),

    gender TEXT,
    city TEXT,
    state TEXT,
    zip INTEGER,

    lat DOUBLE PRECISION,
    long DOUBLE PRECISION,
    city_pop INTEGER,

    merch_lat DOUBLE PRECISION,
    merch_long DOUBLE PRECISION,

    created_at TIMESTAMPTZ DEFAULT NOW()
);


-- 2. Predictions table
CREATE TABLE predictions (
    prediction_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    transaction_id UUID NOT NULL
        REFERENCES transactions(transaction_id)
        ON DELETE CASCADE,

    fraud_probability DOUBLE PRECISION NOT NULL,

    threshold DOUBLE PRECISION NOT NULL,

    decision TEXT NOT NULL,

    model_version TEXT,

    created_at TIMESTAMPTZ DEFAULT NOW()
);


-- Index for quickly finding a customer's transaction history
CREATE INDEX idx_transactions_customer_time
ON transactions(customer_id, transaction_time);


-- Index for quickly finding a prediction for a transaction
CREATE INDEX idx_predictions_transaction
ON predictions(transaction_id);

CREATE TABLE customers (
    customer_id TEXT PRIMARY KEY,
    dob DATE NOT NULL
);

-- 4. Analyst decisions / audit trail
CREATE TABLE analyst_decisions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    transaction_id UUID NOT NULL
        REFERENCES transactions(transaction_id)
        ON DELETE CASCADE,

    risk_level TEXT NOT NULL,

    action TEXT NOT NULL,

    created_at TIMESTAMPTZ DEFAULT NOW()
);