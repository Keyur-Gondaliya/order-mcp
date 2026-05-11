from __future__ import annotations

import psycopg2.extras

from .connection import cursor


def init_db() -> None:
    """Create all tables and insert demo seed data on first run."""
    with cursor() as cur:
        cur.execute("""
            CREATE TABLE IF NOT EXISTS orders (
                id            VARCHAR(50)   PRIMARY KEY,
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
        cur.execute("""
            CREATE TABLE IF NOT EXISTS api_tokens (
                id         SERIAL       PRIMARY KEY,
                token      VARCHAR(64)  UNIQUE NOT NULL,
                created_at TIMESTAMPTZ  NOT NULL DEFAULT NOW()
            )
        """)

        cur.execute("SELECT COUNT(*) AS cnt FROM orders")
        if cur.fetchone()["cnt"] == 0:
            psycopg2.extras.execute_values(cur, """
                INSERT INTO orders (id, customer, total, status) VALUES %s
            """, [
                ("ORD-1001", "alice@example.com", 19.99, "shipped"),
                ("ORD-1002", "bob@example.com",   19.00, "pending"),
                ("ORD-1003", "alice@example.com", 10.50, "paid"),
            ])
            psycopg2.extras.execute_values(cur, """
                INSERT INTO order_items (order_id, sku, qty, price) VALUES %s
            """, [
                ("ORD-1001", "BOOK-42", 1, 19.99),
                ("ORD-1002", "MUG-RED", 2,  9.50),
                ("ORD-1003", "PEN-BLK", 3,  2.00),
                ("ORD-1003", "PAD-A5",  1,  4.50),
            ])
