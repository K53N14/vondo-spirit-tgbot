from __future__ import annotations

import os
from dataclasses import dataclass
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

from dotenv import load_dotenv


@dataclass(frozen=True)
class Settings:
    bot_token: str
    database_url: str
    owner_user_ids: set[int]


def _normalize_database_url(raw_url: str) -> str:
    """Normalize Railway/Postgres URLs for SQLAlchemy asyncpg engine."""
    url = raw_url.strip()
    if not url:
        return "sqlite+aiosqlite:///./bot.db"

    if url.startswith("postgres://"):
        url = "postgresql+asyncpg://" + url[len("postgres://") :]
    elif url.startswith("postgresql://") and not url.startswith("postgresql+asyncpg://"):
        url = "postgresql+asyncpg://" + url[len("postgresql://") :]

    parts = urlsplit(url)
    query_items = parse_qsl(parts.query, keep_blank_values=True)

    sanitized_query: list[tuple[str, str]] = []
    for key, value in query_items:
        lower_key = key.lower()

        # asyncpg may fail with this attribute on some managed proxies.
        if lower_key == "target_session_attrs":
            continue

        if lower_key == "sslmode":
            # asyncpg understands ssl=require/prefer/disable, use ssl key.
            sanitized_query.append(("ssl", value))
            continue

        sanitized_query.append((key, value))

    return urlunsplit((parts.scheme, parts.netloc, parts.path, urlencode(sanitized_query), parts.fragment))


def load_settings() -> Settings:
    load_dotenv()

    token = os.getenv("BOT_TOKEN", "").strip()
    if not token:
        raise ValueError("BOT_TOKEN is not set")

    database_url = _normalize_database_url(os.getenv("DATABASE_URL", ""))

    raw_owner_ids = os.getenv("OWNER_USER_IDS", "")
    owner_ids = {int(v.strip()) for v in raw_owner_ids.split(",") if v.strip()}

    return Settings(
        bot_token=token,
        database_url=database_url,
        owner_user_ids=owner_ids,
    )
