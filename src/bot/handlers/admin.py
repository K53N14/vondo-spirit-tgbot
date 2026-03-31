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
        await update.message.reply_text("Использование: /remove_everywhere <username>")
        return

    username = context.args[0].strip().lstrip("@")
    if not username:
        await update.message.reply_text("Укажите корректный username.")
        return

    service: MembershipService = context.application.bot_data["membership_service"]
    target_user = await service.get_user_by_username(username)
    if target_user is None:
        await update.message.reply_text(f"Пользователь @{username} не найден в базе.")
        return

    if target_user.id <= 0:
        await update.message.reply_text(
            f"Пользователь @{username} добавлен вручную без Telegram user_id. "
            "Сначала дождитесь chat_member update, чтобы бот узнал реальный id."
        )
        return

    chat_ids = await service.list_active_chat_ids()

    success: list[int] = []
    failed: list[tuple[int, str]] = []

    for chat_id in chat_ids:
        try:
            await context.bot.ban_chat_member(chat_id=chat_id, user_id=target_user.id)
            await context.bot.unban_chat_member(chat_id=chat_id, user_id=target_user.id, only_if_banned=True)
            success.append(chat_id)
        except Exception as exc:  # skeletal fallback, replace with explicit TelegramError handling in production
            failed.append((chat_id, str(exc)))

    result_lines = [
        f"Запрос на удаление пользователя <code>@{username}</code> (id={target_user.id}) завершен.",
        f"Успешно: <b>{len(success)}</b>",
        f"С ошибками: <b>{len(failed)}</b>",
    ]
    if failed:
        preview = "\n".join(f"- {chat_id}: {reason}" for chat_id, reason in failed[:10])
        result_lines.append("\nПервые ошибки:\n" + preview)

    await update.message.reply_text("\n".join(result_lines), parse_mode=ParseMode.HTML)
