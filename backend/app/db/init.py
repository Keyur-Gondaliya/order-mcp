from __future__ import annotations

from .connection import cursor


def init_db() -> None:
    """Create all tables on first run; run migrations for existing databases."""
    with cursor() as cur:
        # businesses must exist before api_tokens and orders reference it
        cur.execute("""
            CREATE TABLE IF NOT EXISTS businesses (
                id            SERIAL        PRIMARY KEY,
                name          VARCHAR(255)  UNIQUE NOT NULL,
                password_hash VARCHAR(255)  NOT NULL,
                created_at    TIMESTAMPTZ   NOT NULL DEFAULT NOW()
            )
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS api_tokens (
                id          SERIAL       PRIMARY KEY,
                token       VARCHAR(64)  UNIQUE NOT NULL,
                business_id INTEGER      NOT NULL REFERENCES businesses(id) ON DELETE CASCADE,
                created_at  TIMESTAMPTZ  NOT NULL DEFAULT NOW()
            )
        """)
        cur.execute("""
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
            )
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS order_items (
                id        SERIAL        PRIMARY KEY,
                order_id  VARCHAR(50)   NOT NULL REFERENCES orders(id) ON DELETE CASCADE,
                sku       VARCHAR(100)  NOT NULL,
                qty       INTEGER       NOT NULL CHECK (qty > 0),
                price     NUMERIC(10,2) NOT NULL CHECK (price >= 0)
            )
        """)

        # Migrations for databases that existed before multi-tenancy was added
        cur.execute("""
            ALTER TABLE api_tokens
            ADD COLUMN IF NOT EXISTS business_id INTEGER REFERENCES businesses(id) ON DELETE CASCADE
        """)
        cur.execute("""
            ALTER TABLE orders
            ADD COLUMN IF NOT EXISTS business_id INTEGER REFERENCES businesses(id)
        """)
