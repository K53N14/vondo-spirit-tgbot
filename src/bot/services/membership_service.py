from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from sqlalchemy.ext.asyncio import async_sessionmaker
from telegram import Chat, User

from bot.repositories.membership_repo import MembershipRepository, StoredChat, StoredUser, StoredUserChat


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

    async def save_user_membership(
        self,
        *,
        chat_id: int,
        chat_title: Optional[str],
        chat_type: str,
        user_id: int,
        username: Optional[str],
        full_name: str,
        is_bot: bool,
        status: str,
    ) -> None:
        is_current = status in {"creator", "administrator", "member", "restricted"}

        async with self.session_factory() as session:
            repo = MembershipRepository(session)
            await repo.upsert_chat(chat_id=chat_id, title=chat_title, chat_type=chat_type, is_active=True)
            await repo.upsert_user(user_id=user_id, username=username, full_name=full_name, is_bot=is_bot)
            await repo.upsert_membership(chat_id=chat_id, user_id=user_id, status=status, is_current=is_current)
            await session.commit()

    async def upsert_user_profile(self, user_id: int, username: Optional[str], full_name: str, is_bot: bool) -> None:
        async with self.session_factory() as session:
            repo = MembershipRepository(session)
            await repo.upsert_user(user_id=user_id, username=username, full_name=full_name, is_bot=is_bot)
            await session.commit()

    async def add_manual_user_by_username(self, username: str) -> StoredUser:
        async with self.session_factory() as session:
            repo = MembershipRepository(session)
            user = await repo.add_manual_user_by_username(username)
            await session.commit()
            return user

    async def list_active_chat_ids(self) -> list[int]:
        async with self.session_factory() as session:
            repo = MembershipRepository(session)
            return await repo.list_active_chat_ids()

    async def list_active_chats(self) -> list[StoredChat]:
        async with self.session_factory() as session:
            repo = MembershipRepository(session)
            return await repo.list_active_chats()

    async def list_users(self) -> list[StoredUser]:
        async with self.session_factory() as session:
            repo = MembershipRepository(session)
            return await repo.list_users()

    async def delete_user_by_username(self, username: str) -> bool:
        async with self.session_factory() as session:
            repo = MembershipRepository(session)
            deleted = await repo.delete_user_by_username(username)
            await session.commit()
            return deleted

    async def get_user_by_username(self, username: str) -> Optional[StoredUser]:
        async with self.session_factory() as session:
            repo = MembershipRepository(session)
            return await repo.get_user_by_username(username)

    async def list_user_chats_by_username(self, username: str) -> tuple[Optional[StoredUser], list[StoredUserChat]]:
        async with self.session_factory() as session:
            repo = MembershipRepository(session)
            user = await repo.get_user_by_username(username)
            if user is None:
                return None, []
            chats = await repo.list_user_active_chats(user.id)
            return user, chats
