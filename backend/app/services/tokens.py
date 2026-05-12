from __future__ import annotations

import secrets

from app.db.connection import cursor


def validate_token(token: str) -> int | None:
    """Return business_id for a valid token, or None if invalid/not found."""
    with cursor() as cur:
        cur.execute(
            "SELECT business_id FROM api_tokens WHERE token = %s",
            (token,),
        )
        row = cur.fetchone()
    return row["business_id"] if row else None


def rotate_token(business_id: int) -> str:
    token = secrets.token_hex(24)
    with cursor() as cur:
        cur.execute("DELETE FROM api_tokens WHERE business_id = %s", (business_id,))
        cur.execute(
            "INSERT INTO api_tokens (token, business_id) VALUES (%s, %s)",
            (token, business_id),
        )
    return token


def revoke_token(business_id: int) -> None:
    with cursor() as cur:
        cur.execute("DELETE FROM api_tokens WHERE business_id = %s", (business_id,))


def get_token(business_id: int) -> str | None:
    with cursor() as cur:
        cur.execute(
            "SELECT token FROM api_tokens WHERE business_id = %s ORDER BY id DESC LIMIT 1",
            (business_id,),
        )
        row = cur.fetchone()
    return row["token"] if row else None
