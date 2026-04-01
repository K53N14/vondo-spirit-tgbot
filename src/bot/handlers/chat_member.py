from __future__ import annotations

import logging

from telegram import Update
from telegram.ext import ContextTypes

from bot.services.membership_service import MemberSnapshot, MembershipService

logger = logging.getLogger(__name__)


async def on_chat_member_update(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.chat_member is None:
        return

    service: MembershipService = context.application.bot_data["membership_service"]

    chat_member_updated = update.chat_member
    snapshot = MemberSnapshot(
        chat=chat_member_updated.chat,
        user=chat_member_updated.new_chat_member.user,
        status=chat_member_updated.new_chat_member.status,
    )

    await service.save_member_update(snapshot)
    logger.info(
        "member_state_saved chat_id=%s user_id=%s status=%s",
        snapshot.chat.id,
        snapshot.user.id,
        snapshot.status,
    )
<<<<<<< HEAD
=======


async def on_my_chat_member_update(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.my_chat_member is None:
        return

    service: MembershipService = context.application.bot_data["membership_service"]
    my_update = update.my_chat_member
    status = my_update.new_chat_member.status
    is_active = status in {"creator", "administrator", "member", "restricted"}

    await service.set_chat_active(my_update.chat.id, is_active)
    await service.save_user_membership(
        chat_id=my_update.chat.id,
        chat_title=my_update.chat.title,
        chat_type=my_update.chat.type,
        user_id=my_update.new_chat_member.user.id,
        username=my_update.new_chat_member.user.username,
        full_name=my_update.new_chat_member.user.full_name,
        is_bot=my_update.new_chat_member.user.is_bot,
        status=status,
    )
    logger.info("bot_chat_state_saved chat_id=%s status=%s", my_update.chat.id, status)
>>>>>>> 8a5e6175f2b2ebbed776a29511eb21867e6bb4f4
