from __future__ import annotations

from contextvars import ContextVar

current_business_id: ContextVar[int | None] = ContextVar("current_business_id", default=None)
