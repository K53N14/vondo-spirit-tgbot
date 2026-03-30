from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy.ext.asyncio import async_sessionmaker
from telegram import Chat, User

from bot.repositories.membership_repo import MembershipRepository


@dataclass(frozen=True)
class MemberSnapshot:
    chat: Chat
    user: User
    status: str


class MembershipService:
    def __init__(self, session_factory: async_sessionmaker) -> None:
        self.session_factory = session_factory

    async def save_member_update(self, snapshot: MemberSnapshot) -> None:
        is_current = snapshot.status in {"creator", "administrator", "member", "restricted"}

        async with self.session_factory() as session:
            repo = MembershipRepository(session)
            await repo.upsert_chat(
                chat_id=snapshot.chat.id,
                title=snapshot.chat.title,
                chat_type=snapshot.chat.type,
                is_active=True,
            )
            await repo.upsert_user(
                user_id=snapshot.user.id,
                username=snapshot.user.username,
                full_name=snapshot.user.full_name,
                is_bot=snapshot.user.is_bot,
            )
            await repo.upsert_membership(
                chat_id=snapshot.chat.id,
                user_id=snapshot.user.id,
                status=snapshot.status,
                is_current=is_current,
            )
            await session.commit()

    async def list_active_chat_ids(self) -> list[int]:
        async with self.session_factory() as session:
            repo = MembershipRepository(session)
            return await repo.list_active_chat_ids()
