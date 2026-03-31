from __future__ import annotations

from telegram import Update
from telegram.ext import ContextTypes


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.message is None:
        return

    text = (
        "Привет! Я бот для контроля участников в группах.\n\n"
        "Что я умею:\n"
        "• отслеживать изменения участников через chat_member обновления;\n"
        "• хранить состояние участников в базе;\n"
        "• удалять пользователя из всех известных групп командой администратора.\n\n"
        "Напиши /help, чтобы увидеть список доступных команд."
    )
    await update.message.reply_text(text)


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.message is None:
        return

    text = (
        "Доступные команды:\n\n"
        "/start — приветствие и краткое описание возможностей бота.\n"
        "/help — список команд и их описание.\n"
        "/remove_everywhere <user_id> — удалить пользователя из всех известных активных групп "
        "(только для пользователей из OWNER_USER_IDS)."
    )
    await update.message.reply_text(text)
