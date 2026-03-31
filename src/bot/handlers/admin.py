from __future__ import annotations

from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import ContextTypes

from bot.services.membership_service import MembershipService


async def remove_everywhere(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.effective_user is None or update.message is None:
        return

    owner_ids: set[int] = context.application.bot_data["owner_user_ids"]
    if update.effective_user.id not in owner_ids:
        await update.message.reply_text("У вас нет прав для этой команды.")
        return

    if not context.args:
        await update.message.reply_text("Использование: /remove_everywhere <user_id>")
        return

    try:
        target_user_id = int(context.args[0])
    except ValueError:
        await update.message.reply_text("user_id должен быть целым числом.")
        return

    service: MembershipService = context.application.bot_data["membership_service"]
    chat_ids = await service.list_active_chat_ids()

    success: list[int] = []
    failed: list[tuple[int, str]] = []

    for chat_id in chat_ids:
        try:
            await context.bot.ban_chat_member(chat_id=chat_id, user_id=target_user_id)
            await context.bot.unban_chat_member(chat_id=chat_id, user_id=target_user_id, only_if_banned=True)
            success.append(chat_id)
        except Exception as exc:  # skeletal fallback, replace with explicit TelegramError handling in production
            failed.append((chat_id, str(exc)))

    result_lines = [
        f"Запрос на удаление пользователя <code>{target_user_id}</code> завершен.",
        f"Успешно: <b>{len(success)}</b>",
        f"С ошибками: <b>{len(failed)}</b>",
    ]
    if failed:
        preview = "\n".join(f"- {chat_id}: {reason}" for chat_id, reason in failed[:10])
        result_lines.append("\nПервые ошибки:\n" + preview)

    await update.message.reply_text("\n".join(result_lines), parse_mode=ParseMode.HTML)
