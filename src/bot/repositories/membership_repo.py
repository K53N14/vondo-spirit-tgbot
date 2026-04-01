from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from sqlalchemy import Select, delete, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from bot.db.models import Chat, Membership, User


@dataclass(frozen=True)
class StoredUser:
    id: int
    username: Optional[str]
    full_name: str


@dataclass(frozen=True)
class StoredUserChat:
    chat_id: int
    title: Optional[str]
    chat_type: str
    status: str


@dataclass(frozen=True)
class StoredChat:
    chat_id: int
    title: Optional[str]
    chat_type: str


class MembershipRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def upsert_chat(self, chat_id: int, title: Optional[str], chat_type: str, is_active: bool = True) -> Chat:
        chat = await self.session.get(Chat, chat_id)
        if chat is None:
            chat = Chat(id=chat_id, title=title, type=chat_type, is_active=is_active)
            self.session.add(chat)
        else:
            chat.title = title
            chat.type = chat_type
            chat.is_active = is_active
        return chat

    async def upsert_user(self, user_id: int, username: Optional[str], full_name: str, is_bot: bool) -> User:
        user = await self.session.get(User, user_id)
        if user is not None:
            user.username = username
            user.full_name = full_name
            user.is_bot = is_bot
            return user

        existing_by_username: Optional[User] = None
        if username:
            stmt = select(User).where(User.username == username)
            existing_by_username = await self.session.scalar(stmt)

        if existing_by_username is not None and existing_by_username.id < 0:
            real_user = User(id=user_id, username=username, full_name=full_name, is_bot=is_bot)
            self.session.add(real_user)
            await self.session.flush()

            await self.session.execute(
                update(Membership)
                .where(Membership.user_id == existing_by_username.id)
                .values(user_id=user_id)
            )
            await self.session.execute(delete(User).where(User.id == existing_by_username.id))
            return real_user

        user = User(id=user_id, username=username, full_name=full_name, is_bot=is_bot)
        self.session.add(user)
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

    async def list_active_chats(self) -> list[StoredChat]:
        stmt: Select[tuple[Chat]] = select(Chat).where(Chat.is_active.is_(True)).order_by(Chat.id.asc())
        rows = await self.session.scalars(stmt)
        chats = rows.all()
        return [StoredChat(chat_id=c.id, title=c.title, chat_type=c.type) for c in chats]

    async def deactivate_chat(self, chat_id: int) -> bool:
        chat = await self.session.get(Chat, chat_id)
        if chat is None:
            return False
        chat.is_active = False
        return True

    async def list_users(self) -> list[StoredUser]:
        stmt: Select[tuple[User]] = select(User).order_by(User.username.asc().nulls_last(), User.full_name.asc())
        rows = await self.session.scalars(stmt)
        users = rows.all()
        return [StoredUser(id=u.id, username=u.username, full_name=u.full_name) for u in users]

    async def get_user_by_username(self, username: str) -> Optional[StoredUser]:
        normalized = username.lstrip("@")
        stmt: Select[tuple[User]] = select(User).where(User.username == normalized)
        user = await self.session.scalar(stmt)
        if user is None:
            return None
        return StoredUser(id=user.id, username=user.username, full_name=user.full_name)

    async def add_manual_user_by_username(self, username: str) -> StoredUser:
        normalized = username.strip().lstrip("@")
        existing = await self.get_user_by_username(normalized)
        if existing is not None:
            return existing

        min_negative_id_stmt = select(func.min(User.id)).where(User.id < 0)
        min_negative_id = await self.session.scalar(min_negative_id_stmt)
        next_id = -1 if min_negative_id is None else int(min_negative_id) - 1

        user = User(
            id=next_id,
            username=normalized,
            full_name=f"manual:{normalized}",
            is_bot=False,
        )
        self.session.add(user)
        await self.session.flush()
        return StoredUser(id=user.id, username=user.username, full_name=user.full_name)

    async def delete_user_by_username(self, username: str) -> bool:
        normalized = username.strip().lstrip("@")
        stmt = select(User).where(User.username == normalized)
        user = await self.session.scalar(stmt)
        if user is None:
            return False

        await self.session.execute(delete(Membership).where(Membership.user_id == user.id))
        await self.session.execute(delete(User).where(User.id == user.id))
        return True

    async def list_user_active_chats(self, user_id: int) -> list[StoredUserChat]:
        stmt = (
            select(Chat.id, Chat.title, Chat.type, Membership.status)
            .join(Membership, Membership.chat_id == Chat.id)
            .where(Membership.user_id == user_id, Membership.is_current.is_(True))
            .order_by(Chat.title.asc().nulls_last(), Chat.id.asc())
        )
        rows = await self.session.execute(stmt)
        return [
            StoredUserChat(chat_id=chat_id, title=title, chat_type=chat_type, status=status)
            for chat_id, title, chat_type, status in rows.all()
        ]
