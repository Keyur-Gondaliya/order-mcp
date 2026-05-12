from __future__ import annotations

import secrets

import bcrypt
import psycopg2

from app.db.connection import cursor


def _hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def _check_password(password: str, hashed: str) -> bool:
    return bcrypt.checkpw(password.encode(), hashed.encode())


def _make_token(cur, business_id: int) -> str:
    token = secrets.token_hex(24)
    cur.execute(
        "INSERT INTO api_tokens (token, business_id) VALUES (%s, %s)",
        (token, business_id),
    )
    return token


def register_business(name: str, password: str) -> dict:
    password_hash = _hash_password(password)
    with cursor() as cur:
        try:
            cur.execute(
                "INSERT INTO businesses (name, password_hash) VALUES (%s, %s) RETURNING id, name, created_at",
                (name, password_hash),
            )
        except psycopg2.errors.UniqueViolation:
            raise ValueError(f"Business name '{name}' is already taken.")
        row = cur.fetchone()
        business = {
            "id": row["id"],
            "name": row["name"],
            "created_at": row["created_at"].isoformat(),
        }
        token = _make_token(cur, business["id"])
    return {"business": business, "token": token}


def login_business(name: str, password: str) -> dict:
    with cursor() as cur:
        cur.execute(
            "SELECT id, name, password_hash, created_at FROM businesses WHERE name = %s",
            (name,),
        )
        row = cur.fetchone()
        if not row or not _check_password(password, row["password_hash"]):
            raise ValueError("Invalid business name or password.")
        business = {
            "id": row["id"],
            "name": row["name"],
            "created_at": row["created_at"].isoformat(),
        }
        # Return existing token or create a new one
        cur.execute(
            "SELECT token FROM api_tokens WHERE business_id = %s ORDER BY id DESC LIMIT 1",
            (business["id"],),
        )
        token_row = cur.fetchone()
        token = token_row["token"] if token_row else _make_token(cur, business["id"])
    return {"business": business, "token": token}


def get_business_by_id(business_id: int) -> dict:
    with cursor() as cur:
        cur.execute(
            "SELECT id, name, created_at FROM businesses WHERE id = %s",
            (business_id,),
        )
        row = cur.fetchone()
    if not row:
        raise ValueError(f"Business {business_id} not found.")
    return {
        "id": row["id"],
        "name": row["name"],
        "created_at": row["created_at"].isoformat(),
    }
