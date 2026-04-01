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
