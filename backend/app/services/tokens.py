from __future__ import annotations

import secrets

from app.db.connection import cursor


def get_or_create_token() -> str:
    with cursor() as cur:
        cur.execute("SELECT token FROM api_tokens ORDER BY id DESC LIMIT 1")
        row = cur.fetchone()
        if row:
            return row["token"]
        token = secrets.token_hex(24)
        cur.execute("INSERT INTO api_tokens (token) VALUES (%s)", (token,))
        return token


def rotate_token() -> str:
    token = secrets.token_hex(24)
    with cursor() as cur:
        cur.execute("DELETE FROM api_tokens")
        cur.execute("INSERT INTO api_tokens (token) VALUES (%s)", (token,))
    return token


def revoke_token() -> None:
    with cursor() as cur:
        cur.execute("DELETE FROM api_tokens")
