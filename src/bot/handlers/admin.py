from __future__ import annotations

from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import ContextTypes

from bot.handlers.ui import mark_removal_cleanup
from bot.services.membership_service import MembershipService

ALLOWED_ADMIN_RIGHTS = {
    "is_anonymous",
    "can_manage_chat",
    "can_delete_messages",
    "can_manage_video_chats",
    "can_restrict_members",
    "can_promote_members",
    "can_change_info",
    "can_invite_users",
    "can_post_stories",
    "can_edit_stories",
    "can_delete_stories",
    "can_post_messages",
    "can_edit_messages",
    "can_pin_messages",
    "can_manage_topics",
}

DEFAULT_ADMIN_RIGHTS: dict[str, bool] = {
    "can_manage_chat": True,
    "can_delete_messages": True,
    "can_manage_video_chats": True,
    "can_restrict_members": True,
    "can_change_info": False,
    "can_invite_users": True,
    "can_pin_messages": True,
    "can_manage_topics": True,
}


def _is_owner(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    if update.effective_user is None:
        return False
    owner_ids: set[int] = context.application.bot_data["owner_user_ids"]
    return update.effective_user.id in owner_ids


def _parse_target_chat_ids(raw_target: str, active_chat_ids: list[int]) -> tuple[list[int], str | None]:
    if raw_target.lower() == "all":
        if not active_chat_ids:
            return [], "В базе нет активных групп."
        return active_chat_ids, None

    raw_parts = [part.strip() for part in raw_target.replace(" ", "").split(",") if part.strip()]
    if not raw_parts:
        return [], "Укажи all или список chat_id через запятую."

    parsed_ids: list[int] = []
    for part in raw_parts:
        try:
            parsed_ids.append(int(part))
        except ValueError:
            return [], f"Некорректный chat_id: {part}"

    available = set(active_chat_ids)
    target_ids = [chat_id for chat_id in parsed_ids if chat_id in available]
    if not target_ids:
        return [], "Ни один из указанных chat_id не подходит (пользователь не состоит в этих чатах)."

    return target_ids, None


def _parse_rights_assignments(tokens: list[str]) -> tuple[dict[str, bool] | None, str | None]:
    rights: dict[str, bool] = {}

    for token in tokens:
        if "=" not in token:
            return None, f"Некорректный формат '{token}'. Используй right=true|false."

        key, raw_value = token.split("=", 1)
        key = key.strip().lower()
        value = raw_value.strip().lower()

        if key not in ALLOWED_ADMIN_RIGHTS:
            return None, f"Неизвестное право: {key}."

        if value in {"1", "true", "yes", "on"}:
            rights[key] = True
        elif value in {"0", "false", "no", "off"}:
            rights[key] = False
        else:
            return None, f"Некорректное значение для {key}: {raw_value}."

    if not rights:
        return None, "Укажи хотя бы одно право для изменения."

    return rights, None


async def _get_user_chat_ids(service: MembershipService, username: str) -> list[int]:
    _, chats = await service.list_user_chats_by_username(username)
    return [chat.chat_id for chat in chats]


async def remove_everywhere(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.effective_user is None or update.message is None:
        return

    if not _is_owner(update, context):
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

    chat_ids = await _get_user_chat_ids(service, username)
    if not chat_ids:
        await update.message.reply_text(
            f"Пользователь @{username} не состоит ни в одной активной известной группе. Нечего удалять."
        )
        return

    success: list[int] = []
    failed: list[tuple[int, str]] = []

    for chat_id in chat_ids:
        try:
            mark_removal_cleanup(context, chat_id=chat_id, user_id=target_user.id)
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


async def promote_admin_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.message is None:
        return

    if not _is_owner(update, context):
        await update.message.reply_text("У вас нет прав для этой команды.")
        return

    if len(context.args) < 2:
        await update.message.reply_text("Использование: /promote_admin <chat_id|all|chat_id,chat_id,...> <username>")
        return

    service: MembershipService = context.application.bot_data["membership_service"]
    username = context.args[1].strip().lstrip("@")
    user_chat_ids = await _get_user_chat_ids(service, username)
    if not user_chat_ids:
        await update.message.reply_text(
            f"Пользователь @{username} не состоит ни в одной активной известной группе. Операция не требуется."
        )
        return

    target_chat_ids, error = _parse_target_chat_ids(context.args[0], user_chat_ids)
    if error:
        await update.message.reply_text(error)
        return

    target_user = await service.get_user_by_username(username)
    if target_user is None:
        await update.message.reply_text(f"Пользователь @{username} не найден в базе.")
        return
    if target_user.id <= 0:
        await update.message.reply_text("У пользователя нет реального Telegram user_id. Сначала выполните /sync_me.")
        return

    success: list[int] = []
    failed: list[str] = []
    for chat_id in target_chat_ids:
        try:
            await context.bot.promote_chat_member(chat_id=chat_id, user_id=target_user.id, **DEFAULT_ADMIN_RIGHTS)
            success.append(chat_id)
        except Exception as exc:
            failed.append(f"{chat_id}: {exc}")

    lines = [
        f"Назначение @{username} администратором завершено.",
        f"Успешно: {len(success)}",
        f"Ошибок: {len(failed)}",
    ]
    if failed:
        lines.extend(["Первые ошибки:"] + [f"- {item}" for item in failed[:10]])

    await update.message.reply_text("\n".join(lines))


async def set_admin_rank_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.message is None:
        return

    if not _is_owner(update, context):
        await update.message.reply_text("У вас нет прав для этой команды.")
        return

    if len(context.args) < 3:
        await update.message.reply_text("Использование: /set_admin_rank <chat_id|all|chat_id,chat_id,...> <username> <rank>")
        return

    service: MembershipService = context.application.bot_data["membership_service"]
    username = context.args[1].strip().lstrip("@")
    user_chat_ids = await _get_user_chat_ids(service, username)
    if not user_chat_ids:
        await update.message.reply_text(
            f"Пользователь @{username} не состоит ни в одной активной известной группе. Операция не требуется."
        )
        return

    target_chat_ids, error = _parse_target_chat_ids(context.args[0], user_chat_ids)
    if error:
        await update.message.reply_text(error)
        return

    rank = " ".join(context.args[2:]).strip()
    if not rank:
        await update.message.reply_text("Укажите непустой rank.")
        return

    target_user = await service.get_user_by_username(username)
    if target_user is None:
        await update.message.reply_text(f"Пользователь @{username} не найден в базе.")
        return
    if target_user.id <= 0:
        await update.message.reply_text("У пользователя нет реального Telegram user_id. Сначала выполните /sync_me.")
        return

    raw_scope = context.args[0].strip().lower()
    apply_global_rank = raw_scope == "all"
    if apply_global_rank:
        await service.set_user_admin_rank(user_id=target_user.id, admin_rank=rank)

    success: list[int] = []
    failed: list[str] = []
    for chat_id in target_chat_ids:
        try:
            effective_rank = rank
            if apply_global_rank:
                membership_rank = await service.get_membership_admin_rank(chat_id=chat_id, user_id=target_user.id)
                effective_rank = membership_rank or rank
            await context.bot.set_chat_administrator_custom_title(
                chat_id=chat_id,
                user_id=target_user.id,
                custom_title=effective_rank,
            )
            if not apply_global_rank:
                await service.set_membership_admin_rank(chat_id=chat_id, user_id=target_user.id, admin_rank=rank)
            success.append(chat_id)
        except Exception as exc:
            failed.append(f"{chat_id}: {exc}")

    lines = [
        f"Установка rank '{rank}' для @{username} завершена.",
        f"Режим: {'all (основной rank в users + fallback по memberships)' if apply_global_rank else 'выбранные чаты (rank в memberships)'}",
        f"Успешно: {len(success)}",
        f"Ошибок: {len(failed)}",
    ]
    if failed:
        lines.extend(["Первые ошибки:"] + [f"- {item}" for item in failed[:10]])

    await update.message.reply_text("\n".join(lines))


async def set_admin_rights_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.message is None:
        return

    if not _is_owner(update, context):
        await update.message.reply_text("У вас нет прав для этой команды.")
        return

    if len(context.args) < 3:
        await update.message.reply_text(
            "Использование: /set_admin_rights <chat_id|all|chat_id,chat_id,...> <username> <right=true|false> [right=true|false ...]"
        )
        return

    service: MembershipService = context.application.bot_data["membership_service"]
    username = context.args[1].strip().lstrip("@")
    user_chat_ids = await _get_user_chat_ids(service, username)
    if not user_chat_ids:
        await update.message.reply_text(
            f"Пользователь @{username} не состоит ни в одной активной известной группе. Операция не требуется."
        )
        return

    target_chat_ids, error = _parse_target_chat_ids(context.args[0], user_chat_ids)
    if error:
        await update.message.reply_text(error)
        return

    target_user = await service.get_user_by_username(username)
    if target_user is None:
        await update.message.reply_text(f"Пользователь @{username} не найден в базе.")
        return
    if target_user.id <= 0:
        await update.message.reply_text("У пользователя нет реального Telegram user_id. Сначала выполните /sync_me.")
        return

    rights, parse_error = _parse_rights_assignments(context.args[2:])
    if parse_error or rights is None:
        await update.message.reply_text(parse_error or "Не удалось разобрать права.")
        return

    success: list[int] = []
    failed: list[str] = []
    for chat_id in target_chat_ids:
        try:
            await context.bot.promote_chat_member(chat_id=chat_id, user_id=target_user.id, **rights)
            success.append(chat_id)
        except Exception as exc:
            failed.append(f"{chat_id}: {exc}")

    rights_preview = ", ".join(f"{k}={v}" for k, v in rights.items())
    lines = [
        f"Обновление прав администратора для @{username} завершено.",
        f"Права: {rights_preview}",
        f"Успешно: {len(success)}",
        f"Ошибок: {len(failed)}",
    ]
    if failed:
        lines.extend(["Первые ошибки:"] + [f"- {item}" for item in failed[:10]])

    await update.message.reply_text("\n".join(lines))
