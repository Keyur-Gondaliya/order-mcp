-- Order System Schema (multi-tenant)
-- Applied by Docker on first container start.
-- The backend also runs CREATE TABLE IF NOT EXISTS on startup.

CREATE TABLE IF NOT EXISTS businesses (
    id            SERIAL        PRIMARY KEY,
    name          VARCHAR(255)  UNIQUE NOT NULL,
    password_hash VARCHAR(255)  NOT NULL,
    created_at    TIMESTAMPTZ   NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS api_tokens (
    id          SERIAL       PRIMARY KEY,
    token       VARCHAR(64)  UNIQUE NOT NULL,
    business_id INTEGER      NOT NULL REFERENCES businesses(id) ON DELETE CASCADE,
    created_at  TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS orders (
    id            VARCHAR(50)   PRIMARY KEY,
    business_id   INTEGER       NOT NULL REFERENCES businesses(id),
    customer      VARCHAR(255)  NOT NULL,
    total         NUMERIC(10,2) NOT NULL,
    status        VARCHAR(20)   NOT NULL DEFAULT 'pending',
    cancel_reason TEXT,
    refund_reason TEXT,
    created_at    TIMESTAMPTZ   NOT NULL DEFAULT NOW(),
    updated_at    TIMESTAMPTZ   NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS order_items (
    id        SERIAL        PRIMARY KEY,
    order_id  VARCHAR(50)   NOT NULL REFERENCES orders(id) ON DELETE CASCADE,
    sku       VARCHAR(100)  NOT NULL,
    qty       INTEGER       NOT NULL CHECK (qty > 0),
    price     NUMERIC(10,2) NOT NULL CHECK (price >= 0)
);
