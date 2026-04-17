from __future__ import annotations

import os
from dataclasses import dataclass

from dotenv import load_dotenv


@dataclass(frozen=True)
class Settings:
    bot_token: str
    database_url: str
    owner_user_ids: set[int]



def load_settings() -> Settings:
    load_dotenv()

    token = os.getenv("BOT_TOKEN", "").strip()
    if not token:
        raise ValueError("BOT_TOKEN is not set")

    database_url = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./bot.db").strip()

    raw_owner_ids = os.getenv("OWNER_USER_IDS", "")
    owner_ids = {
        int(v.strip())
        for v in raw_owner_ids.split(",")
        if v.strip()
    }

    return Settings(
        bot_token=token,
        database_url=database_url,
        owner_user_ids=owner_ids,
    )
