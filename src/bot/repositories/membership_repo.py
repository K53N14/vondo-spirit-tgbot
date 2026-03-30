from __future__ import annotations

from sqlalchemy import Select, select
from sqlalchemy.ext.asyncio import AsyncSession

from bot.db.models import Chat, Membership, User


class MembershipRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def upsert_chat(self, chat_id: int, title: str | None, chat_type: str, is_active: bool = True) -> Chat:
        chat = await self.session.get(Chat, chat_id)
        if chat is None:
            chat = Chat(id=chat_id, title=title, type=chat_type, is_active=is_active)
            self.session.add(chat)
        else:
            chat.title = title
            chat.type = chat_type
            chat.is_active = is_active
        return chat

    async def upsert_user(self, user_id: int, username: str | None, full_name: str, is_bot: bool) -> User:
        user = await self.session.get(User, user_id)
        if user is None:
            user = User(id=user_id, username=username, full_name=full_name, is_bot=is_bot)
            self.session.add(user)
        else:
            user.username = username
            user.full_name = full_name
            user.is_bot = is_bot
        return user

    async def upsert_membership(self, chat_id: int, user_id: int, status: str, is_current: bool) -> Membership:
        stmt: Select[tuple[Membership]] = select(Membership).where(
            Membership.chat_id == chat_id,
            Membership.user_id == user_id,
        )
        membership = await self.session.scalar(stmt)
        if membership is None:
            membership = Membership(chat_id=chat_id, user_id=user_id, status=status, is_current=is_current)
            self.session.add(membership)
        else:
            membership.status = status
            membership.is_current = is_current
        return membership

    async def list_active_chat_ids(self) -> list[int]:
        stmt: Select[tuple[int]] = select(Chat.id).where(Chat.is_active.is_(True))
        rows = await self.session.execute(stmt)
        return list(rows.scalars().all())
