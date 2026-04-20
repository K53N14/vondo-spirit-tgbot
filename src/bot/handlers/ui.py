from __future__ import annotations

from telegram import ReplyKeyboardMarkup, Update
from telegram.ext import ContextTypes

from bot.services.membership_service import MembershipService

BTN_HELP = "📘 Помощь"
BTN_SYNC_ME = "🔄 Синхронизировать меня"
BTN_USER_GROUPS = "👤 Мои группы"
BTN_ADMIN_PANEL = "🛠 Админ-панель"
BTN_BACK = "↩️ Назад"

BTN_USERS = "📋 Пользователи"
BTN_GROUPS = "📋 Группы"
BTN_REMOVE_EVERYWHERE = "❌ Удалить везде"
BTN_PROMOTE_ADMIN = "⬆️ Назначить админом"
BTN_SET_RANK = "🏷 Установить rank"
BTN_SET_RIGHTS = "🔐 Изменить права"

ACTION_REMOVE_EVERYWHERE = "remove_everywhere"
ACTION_PROMOTE_ADMIN = "promote_admin"
ACTION_SET_RANK = "set_rank"
ACTION_SET_RIGHTS = "set_rights"

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


def build_main_keyboard(is_owner: bool) -> ReplyKeyboardMarkup:
    rows: list[list[str]] = [[BTN_HELP, BTN_SYNC_ME], [BTN_USER_GROUPS]]
    if is_owner:
        rows.append([BTN_ADMIN_PANEL])
    return ReplyKeyboardMarkup(rows, resize_keyboard=True)


def build_admin_keyboard() -> ReplyKeyboardMarkup:
    rows = [
        [BTN_USERS, BTN_GROUPS],
        [BTN_REMOVE_EVERYWHERE, BTN_PROMOTE_ADMIN],
        [BTN_SET_RANK, BTN_SET_RIGHTS],
        [BTN_BACK],
    ]
    return ReplyKeyboardMarkup(rows, resize_keyboard=True)


def _parse_target_chat_ids(raw_target: str, active_chat_ids: list[int]) -> tuple[list[int], str | None]:
    if raw_target.lower() == "all":
        if not active_chat_ids:
            return [], "В базе нет активных групп."
        return active_chat_ids, None

    try:
        return [int(raw_target)], None
    except ValueError:
        return [], "chat_id должен быть числом или 'all'."


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


async def on_menu_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.message is None or update.effective_user is None:
        return

    text = (update.message.text or "").strip()
    if not text:
        return

    service: MembershipService = context.application.bot_data["membership_service"]
    is_owner = _is_owner(update, context)

    pending_action = context.user_data.get("pending_action")
    if pending_action:
        await _handle_pending_action(update, context, service, pending_action)
        return

    if text == BTN_HELP:
        await update.message.reply_text(
            "Используй кнопки меню. Для админ-действий открой '🛠 Админ-панель'.",
            reply_markup=build_main_keyboard(is_owner),
        )
        return

    if text == BTN_SYNC_ME:
        await update.message.reply_text("Запусти /sync_me для синхронизации профиля и членств.")
        return

    if text == BTN_USER_GROUPS:
        username = (update.effective_user.username or "").strip()
        if not username:
            await update.message.reply_text("У вас не установлен username в Telegram.")
            return

        user, chats = await service.list_user_chats_by_username(username)
        if user is None:
            await update.message.reply_text("Ваш username не найден в базе. Попросите добавить вас.")
            return

        if not chats:
            await update.message.reply_text("Нет активных групп для вашего профиля.")
            return

        lines = [f"Ваши группы (@{username}):"]
        for item in chats:
            title = item.title or "(без названия)"
            lines.append(f"- {title} | chat_id={item.chat_id} | status={item.status}")
        await update.message.reply_text("\n".join(lines))
        return

    if text == BTN_ADMIN_PANEL:
        if not is_owner:
            await update.message.reply_text("У вас нет прав для админ-панели.")
            return
        await update.message.reply_text("Админ-панель открыта.", reply_markup=build_admin_keyboard())
        return

    if text == BTN_BACK:
        context.user_data.pop("pending_action", None)
        await update.message.reply_text("Главное меню.", reply_markup=build_main_keyboard(is_owner))
        return

    if not is_owner:
        return

    if text == BTN_USERS:
        users = await service.list_users()
        if not users:
            await update.message.reply_text("В базе пока нет пользователей.")
            return
        lines = ["Пользователи в БД:"]
        for user in users[:200]:
            username = f"@{user.username}" if user.username else "(без username)"
            lines.append(f"- {username} | id={user.id} | {user.full_name}")
        await update.message.reply_text("\n".join(lines))
        return

    if text == BTN_GROUPS:
        chats = await service.list_active_chats()
        if not chats:
            await update.message.reply_text("Список групп пуст.")
            return
        lines = ["Группы, в которых бот учитывается:"]
        for chat in chats:
            title = chat.title or "(без названия)"
            lines.append(f"- {title} | chat_id={chat.chat_id} | type={chat.chat_type}")
        await update.message.reply_text("\n".join(lines))
        return

    if text == BTN_REMOVE_EVERYWHERE:
        context.user_data["pending_action"] = ACTION_REMOVE_EVERYWHERE
        await update.message.reply_text("Введи username для удаления из всех активных групп: @username")
        return

    if text == BTN_PROMOTE_ADMIN:
        context.user_data["pending_action"] = ACTION_PROMOTE_ADMIN
        await update.message.reply_text("Введи: <chat_id|all> <username>\nПример: all alice")
        return

    if text == BTN_SET_RANK:
        context.user_data["pending_action"] = ACTION_SET_RANK
        await update.message.reply_text("Введи: <chat_id|all> <username> <rank>\nПример: all alice Senior Moderator")
        return

    if text == BTN_SET_RIGHTS:
        context.user_data["pending_action"] = ACTION_SET_RIGHTS
        await update.message.reply_text(
            "Введи: <chat_id|all> <username> <right=true|false ...>\n"
            "Пример: all alice can_delete_messages=true can_invite_users=false"
        )


async def _handle_pending_action(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    service: MembershipService,
    pending_action: str,
) -> None:
    if update.message is None:
        return

    raw_input = (update.message.text or "").strip()
    parts = raw_input.split()

    if raw_input.lower() in {"отмена", "cancel"}:
        context.user_data.pop("pending_action", None)
        await update.message.reply_text("Действие отменено.", reply_markup=build_admin_keyboard())
        return

    if pending_action == ACTION_REMOVE_EVERYWHERE:
        username = raw_input.lstrip("@")
        target_user = await service.get_user_by_username(username)
        if target_user is None:
            await update.message.reply_text(f"Пользователь @{username} не найден в базе.")
            return
        if target_user.id <= 0:
            await update.message.reply_text("У пользователя нет реального Telegram user_id. Сначала выполните /sync_me.")
            return

        chat_ids = await service.list_active_chat_ids()
        success = 0
        failed: list[str] = []
        for chat_id in chat_ids:
            try:
                await context.bot.ban_chat_member(chat_id=chat_id, user_id=target_user.id)
                await context.bot.unban_chat_member(chat_id=chat_id, user_id=target_user.id, only_if_banned=True)
                success += 1
            except Exception as exc:
                failed.append(f"{chat_id}: {exc}")

        context.user_data.pop("pending_action", None)
        lines = [f"Удаление @{username} завершено.", f"Успешно: {success}", f"Ошибок: {len(failed)}"]
        if failed:
            lines.extend(["Первые ошибки:"] + [f"- {item}" for item in failed[:10]])
        await update.message.reply_text("\n".join(lines), reply_markup=build_admin_keyboard())
        return

    if pending_action == ACTION_PROMOTE_ADMIN:
        if len(parts) < 2:
            await update.message.reply_text("Нужно: <chat_id|all> <username>")
            return
        target_chat_ids, error = _parse_target_chat_ids(parts[0], await service.list_active_chat_ids())
        if error:
            await update.message.reply_text(error)
            return

        username = parts[1].lstrip("@")
        target_user = await service.get_user_by_username(username)
        if target_user is None:
            await update.message.reply_text(f"Пользователь @{username} не найден в базе.")
            return
        if target_user.id <= 0:
            await update.message.reply_text("У пользователя нет реального Telegram user_id. Сначала выполните /sync_me.")
            return

        success = 0
        failed: list[str] = []
        for chat_id in target_chat_ids:
            try:
                await context.bot.promote_chat_member(chat_id=chat_id, user_id=target_user.id, **DEFAULT_ADMIN_RIGHTS)
                success += 1
            except Exception as exc:
                failed.append(f"{chat_id}: {exc}")

        context.user_data.pop("pending_action", None)
        lines = [f"Назначение @{username} администратором завершено.", f"Успешно: {success}", f"Ошибок: {len(failed)}"]
        if failed:
            lines.extend(["Первые ошибки:"] + [f"- {item}" for item in failed[:10]])
        await update.message.reply_text("\n".join(lines), reply_markup=build_admin_keyboard())
        return

    if pending_action == ACTION_SET_RANK:
        if len(parts) < 3:
            await update.message.reply_text("Нужно: <chat_id|all> <username> <rank>")
            return

        target_chat_ids, error = _parse_target_chat_ids(parts[0], await service.list_active_chat_ids())
        if error:
            await update.message.reply_text(error)
            return

        username = parts[1].lstrip("@")
        rank = " ".join(parts[2:]).strip()
        target_user = await service.get_user_by_username(username)
        if target_user is None:
            await update.message.reply_text(f"Пользователь @{username} не найден в базе.")
            return
        if target_user.id <= 0:
            await update.message.reply_text("У пользователя нет реального Telegram user_id. Сначала выполните /sync_me.")
            return

        success = 0
        failed: list[str] = []
        for chat_id in target_chat_ids:
            try:
                await context.bot.set_chat_administrator_custom_title(
                    chat_id=chat_id,
                    user_id=target_user.id,
                    custom_title=rank,
                )
                success += 1
            except Exception as exc:
                failed.append(f"{chat_id}: {exc}")

        context.user_data.pop("pending_action", None)
        lines = [f"Установка rank '{rank}' для @{username} завершена.", f"Успешно: {success}", f"Ошибок: {len(failed)}"]
        if failed:
            lines.extend(["Первые ошибки:"] + [f"- {item}" for item in failed[:10]])
        await update.message.reply_text("\n".join(lines), reply_markup=build_admin_keyboard())
        return

    if pending_action == ACTION_SET_RIGHTS:
        if len(parts) < 3:
            await update.message.reply_text("Нужно: <chat_id|all> <username> <right=true|false ...>")
            return

        target_chat_ids, error = _parse_target_chat_ids(parts[0], await service.list_active_chat_ids())
        if error:
            await update.message.reply_text(error)
            return

        username = parts[1].lstrip("@")
        rights, parse_error = _parse_rights_assignments(parts[2:])
        if parse_error or rights is None:
            await update.message.reply_text(parse_error or "Не удалось разобрать права.")
            return

        target_user = await service.get_user_by_username(username)
        if target_user is None:
            await update.message.reply_text(f"Пользователь @{username} не найден в базе.")
            return
        if target_user.id <= 0:
            await update.message.reply_text("У пользователя нет реального Telegram user_id. Сначала выполните /sync_me.")
            return

        success = 0
        failed: list[str] = []
        for chat_id in target_chat_ids:
            try:
                await context.bot.promote_chat_member(chat_id=chat_id, user_id=target_user.id, **rights)
                success += 1
            except Exception as exc:
                failed.append(f"{chat_id}: {exc}")

        context.user_data.pop("pending_action", None)
        rights_preview = ", ".join(f"{k}={v}" for k, v in rights.items())
        lines = [
            f"Обновление прав администратора для @{username} завершено.",
            f"Права: {rights_preview}",
            f"Успешно: {success}",
            f"Ошибок: {len(failed)}",
        ]
        if failed:
            lines.extend(["Первые ошибки:"] + [f"- {item}" for item in failed[:10]])
        await update.message.reply_text("\n".join(lines), reply_markup=build_admin_keyboard())
        return
