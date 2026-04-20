from __future__ import annotations

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes

from bot.services.membership_service import MembershipService

CB_HELP = "main_help"
CB_SYNC_ME = "main_sync_me"
CB_MY_GROUPS = "main_my_groups"
CB_OPEN_ADMIN = "main_open_admin"
CB_BACK_MAIN = "main_back"

CB_ADMIN_USERS = "admin_users"
CB_ADMIN_GROUPS = "admin_groups"
CB_ACT_REMOVE = "act_remove_everywhere"
CB_ACT_PROMOTE = "act_promote_admin"
CB_ACT_RANK = "act_set_rank"
CB_ACT_RIGHTS = "act_set_rights"
CB_CANCEL = "act_cancel"

ACTION_REMOVE = "remove_everywhere"
ACTION_PROMOTE = "promote_admin"
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


def build_main_keyboard(is_owner: bool) -> InlineKeyboardMarkup:
    rows = [
        [InlineKeyboardButton("📘 Помощь", callback_data=CB_HELP)],
        [InlineKeyboardButton("🔄 Синхронизировать меня", callback_data=CB_SYNC_ME)],
        [InlineKeyboardButton("👤 Мои группы", callback_data=CB_MY_GROUPS)],
    ]
    if is_owner:
        rows.append([InlineKeyboardButton("🛠 Админ-панель", callback_data=CB_OPEN_ADMIN)])
    return InlineKeyboardMarkup(rows)


def build_admin_keyboard() -> InlineKeyboardMarkup:
    rows = [
        [
            InlineKeyboardButton("📋 Пользователи", callback_data=CB_ADMIN_USERS),
            InlineKeyboardButton("📋 Группы", callback_data=CB_ADMIN_GROUPS),
        ],
        [
            InlineKeyboardButton("❌ Удалить везде", callback_data=CB_ACT_REMOVE),
            InlineKeyboardButton("⬆️ Назначить админом", callback_data=CB_ACT_PROMOTE),
        ],
        [
            InlineKeyboardButton("🏷 Установить rank", callback_data=CB_ACT_RANK),
            InlineKeyboardButton("🔐 Изменить права", callback_data=CB_ACT_RIGHTS),
        ],
        [InlineKeyboardButton("↩️ В главное меню", callback_data=CB_BACK_MAIN)],
    ]
    return InlineKeyboardMarkup(rows)


def build_cancel_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [
            [InlineKeyboardButton("❎ Отменить действие", callback_data=CB_CANCEL)],
            [InlineKeyboardButton("↩️ В главное меню", callback_data=CB_BACK_MAIN)],
        ]
    )


def _clear_pending_action(context: ContextTypes.DEFAULT_TYPE) -> None:
    context.user_data.pop("pending_action", None)
    context.user_data.pop("pending_stage", None)
    context.user_data.pop("pending_username", None)


def _set_pending_action(context: ContextTypes.DEFAULT_TYPE, *, action: str, stage: str = "input") -> None:
    context.user_data["pending_action"] = action
    context.user_data["pending_stage"] = stage


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


async def on_inline_button(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    if query is None or update.effective_user is None:
        return

    await query.answer()

    service: MembershipService = context.application.bot_data["membership_service"]
    is_owner = _is_owner(update, context)
    data = query.data or ""

    if data == CB_CANCEL:
        _clear_pending_action(context)
        await query.message.reply_text("Действие отменено. Возвращаю в главное меню.", reply_markup=build_main_keyboard(is_owner))
        return

    if data == CB_BACK_MAIN:
        _clear_pending_action(context)
        await query.message.reply_text("Главное меню.", reply_markup=build_main_keyboard(is_owner))
        return

    if data == CB_HELP:
        await query.message.reply_text(
            "Управляй ботом через inline-кнопки. Для операций с параметрами бот попросит ввод данных.",
            reply_markup=build_main_keyboard(is_owner),
        )
        return

    if data == CB_SYNC_ME:
        await query.message.reply_text("Для полной синхронизации текущего пользователя используй /sync_me.")
        return

    if data == CB_MY_GROUPS:
        username = (update.effective_user.username or "").strip()
        if not username:
            await query.message.reply_text("У вас не установлен username в Telegram.")
            return

        user, chats = await service.list_user_chats_by_username(username)
        if user is None:
            await query.message.reply_text("Ваш username не найден в базе. Попросите администратора добавить вас.")
            return

        if not chats:
            await query.message.reply_text("Нет активных групп для вашего профиля.")
            return

        lines = [f"Ваши группы (@{username}):"]
        for item in chats:
            title = item.title or "(без названия)"
            lines.append(f"- {title} | chat_id={item.chat_id} | status={item.status}")
        await query.message.reply_text("\n".join(lines))
        return

    if data == CB_OPEN_ADMIN:
        if not is_owner:
            await query.message.reply_text("У вас нет прав для админ-панели.")
            return
        await query.message.reply_text("Админ-панель:", reply_markup=build_admin_keyboard())
        return

    if not is_owner:
        await query.message.reply_text("У вас нет прав для этого действия.")
        return

    if data == CB_ADMIN_USERS:
        users = await service.list_users()
        if not users:
            await query.message.reply_text("В базе пока нет пользователей.")
            return

        lines = ["Пользователи в БД:"]
        for user in users[:200]:
            username = f"@{user.username}" if user.username else "(без username)"
            lines.append(f"- {username} | id={user.id} | {user.full_name}")
        await query.message.reply_text("\n".join(lines))
        return

    if data == CB_ADMIN_GROUPS:
        chats = await service.list_active_chats()
        if not chats:
            await query.message.reply_text("Список групп пуст.")
            return

        lines = ["Группы, в которых бот учитывается:"]
        for chat in chats:
            title = chat.title or "(без названия)"
            lines.append(f"- {title} | chat_id={chat.chat_id} | type={chat.chat_type}")
        await query.message.reply_text("\n".join(lines))
        return

    if data == CB_ACT_REMOVE:
        _set_pending_action(context, action=ACTION_REMOVE)
        await query.message.reply_text(
            "Введи username пользователя для удаления из всех активных групп:\nПример: @alice",
            reply_markup=build_cancel_keyboard(),
        )
        return

    if data == CB_ACT_PROMOTE:
        _set_pending_action(context, action=ACTION_PROMOTE)
        await query.message.reply_text(
            "Введи username пользователя для назначения админом во всех активных группах:\nПример: @alice",
            reply_markup=build_cancel_keyboard(),
        )
        return

    if data == CB_ACT_RANK:
        _set_pending_action(context, action=ACTION_SET_RANK, stage="username")
        await query.message.reply_text(
            "Введи username пользователя, которому нужно задать rank:\nПример: @alice",
            reply_markup=build_cancel_keyboard(),
        )
        return

    if data == CB_ACT_RIGHTS:
        _set_pending_action(context, action=ACTION_SET_RIGHTS, stage="username")
        await query.message.reply_text(
            "Введи username пользователя, которому нужно изменить права:\nПример: @alice",
            reply_markup=build_cancel_keyboard(),
        )


async def on_action_input(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.message is None or update.effective_user is None:
        return

    action = context.user_data.get("pending_action")
    if not action:
        return

    service: MembershipService = context.application.bot_data["membership_service"]
    text = (update.message.text or "").strip()

    if not text:
        await update.message.reply_text("Пустой ввод. Введи данные или нажми «Отменить действие».", reply_markup=build_cancel_keyboard())
        return

    if text.lower() in {"отмена", "cancel"}:
        _clear_pending_action(context)
        await update.message.reply_text("Действие отменено.", reply_markup=build_main_keyboard(_is_owner(update, context)))
        return

    if action == ACTION_REMOVE:
        await _process_remove_everywhere(update, context, service, text)
        return

    if action == ACTION_PROMOTE:
        await _process_promote_admin(update, context, service, text)
        return

    if action == ACTION_SET_RANK:
        await _process_set_rank(update, context, service, text)
        return

    if action == ACTION_SET_RIGHTS:
        await _process_set_rights(update, context, service, text)


async def _process_remove_everywhere(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    service: MembershipService,
    raw_username: str,
) -> None:
    username = raw_username.lstrip("@").strip()
    target_user = await service.get_user_by_username(username)
    if target_user is None:
        await update.message.reply_text(f"Пользователь @{username} не найден в базе.", reply_markup=build_cancel_keyboard())
        return

    if target_user.id <= 0:
        await update.message.reply_text(
            "У пользователя нет реального Telegram user_id. Сначала выполните /sync_me.",
            reply_markup=build_cancel_keyboard(),
        )
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

    _clear_pending_action(context)
    lines = [f"Удаление @{username} завершено.", f"Успешно: {success}", f"Ошибок: {len(failed)}"]
    if failed:
        lines.extend(["Первые ошибки:"] + [f"- {item}" for item in failed[:10]])

    await update.message.reply_text("\n".join(lines), reply_markup=build_main_keyboard(_is_owner(update, context)))


async def _process_promote_admin(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    service: MembershipService,
    raw_username: str,
) -> None:
    username = raw_username.lstrip("@").strip()
    target_user = await service.get_user_by_username(username)
    if target_user is None:
        await update.message.reply_text(f"Пользователь @{username} не найден в базе.", reply_markup=build_cancel_keyboard())
        return

    if target_user.id <= 0:
        await update.message.reply_text(
            "У пользователя нет реального Telegram user_id. Сначала выполните /sync_me.",
            reply_markup=build_cancel_keyboard(),
        )
        return

    chat_ids = await service.list_active_chat_ids()
    success = 0
    failed: list[str] = []

    for chat_id in chat_ids:
        try:
            await context.bot.promote_chat_member(chat_id=chat_id, user_id=target_user.id, **DEFAULT_ADMIN_RIGHTS)
            success += 1
        except Exception as exc:
            failed.append(f"{chat_id}: {exc}")

    _clear_pending_action(context)
    lines = [f"Назначение @{username} администратором завершено.", f"Успешно: {success}", f"Ошибок: {len(failed)}"]
    if failed:
        lines.extend(["Первые ошибки:"] + [f"- {item}" for item in failed[:10]])

    await update.message.reply_text("\n".join(lines), reply_markup=build_main_keyboard(_is_owner(update, context)))


async def _process_set_rank(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    service: MembershipService,
    user_input: str,
) -> None:
    stage = context.user_data.get("pending_stage", "username")

    if stage == "username":
        username = user_input.lstrip("@").strip()
        target_user = await service.get_user_by_username(username)
        if target_user is None:
            await update.message.reply_text(f"Пользователь @{username} не найден в базе.", reply_markup=build_cancel_keyboard())
            return
        if target_user.id <= 0:
            await update.message.reply_text(
                "У пользователя нет реального Telegram user_id. Сначала выполните /sync_me.",
                reply_markup=build_cancel_keyboard(),
            )
            return

        context.user_data["pending_username"] = username
        context.user_data["pending_stage"] = "rank"
        await update.message.reply_text(
            f"Введите rank для @{username}:\nПример: Senior Moderator",
            reply_markup=build_cancel_keyboard(),
        )
        return

    username = str(context.user_data.get("pending_username", "")).strip()
    rank = user_input.strip()
    if not rank:
        await update.message.reply_text("Rank не может быть пустым.", reply_markup=build_cancel_keyboard())
        return

    target_user = await service.get_user_by_username(username)
    if target_user is None or target_user.id <= 0:
        await update.message.reply_text("Пользователь больше недоступен в БД.", reply_markup=build_cancel_keyboard())
        return

    chat_ids = await service.list_active_chat_ids()
    success = 0
    failed: list[str] = []

    for chat_id in chat_ids:
        try:
            await context.bot.set_chat_administrator_custom_title(chat_id=chat_id, user_id=target_user.id, custom_title=rank)
            success += 1
        except Exception as exc:
            failed.append(f"{chat_id}: {exc}")

    _clear_pending_action(context)
    lines = [f"Rank '{rank}' для @{username} установлен.", f"Успешно: {success}", f"Ошибок: {len(failed)}"]
    if failed:
        lines.extend(["Первые ошибки:"] + [f"- {item}" for item in failed[:10]])

    await update.message.reply_text("\n".join(lines), reply_markup=build_main_keyboard(_is_owner(update, context)))


async def _process_set_rights(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    service: MembershipService,
    user_input: str,
) -> None:
    stage = context.user_data.get("pending_stage", "username")

    if stage == "username":
        username = user_input.lstrip("@").strip()
        target_user = await service.get_user_by_username(username)
        if target_user is None:
            await update.message.reply_text(f"Пользователь @{username} не найден в базе.", reply_markup=build_cancel_keyboard())
            return
        if target_user.id <= 0:
            await update.message.reply_text(
                "У пользователя нет реального Telegram user_id. Сначала выполните /sync_me.",
                reply_markup=build_cancel_keyboard(),
            )
            return

        context.user_data["pending_username"] = username
        context.user_data["pending_stage"] = "rights"
        await update.message.reply_text(
            "Введите права в формате right=true|false через пробел.\n"
            "Пример: can_delete_messages=true can_invite_users=false",
            reply_markup=build_cancel_keyboard(),
        )
        return

    username = str(context.user_data.get("pending_username", "")).strip()
    rights, parse_error = _parse_rights_assignments(user_input.split())
    if parse_error or rights is None:
        await update.message.reply_text(parse_error or "Не удалось разобрать права.", reply_markup=build_cancel_keyboard())
        return

    target_user = await service.get_user_by_username(username)
    if target_user is None or target_user.id <= 0:
        await update.message.reply_text("Пользователь больше недоступен в БД.", reply_markup=build_cancel_keyboard())
        return

    chat_ids = await service.list_active_chat_ids()
    success = 0
    failed: list[str] = []

    for chat_id in chat_ids:
        try:
            await context.bot.promote_chat_member(chat_id=chat_id, user_id=target_user.id, **rights)
            success += 1
        except Exception as exc:
            failed.append(f"{chat_id}: {exc}")

    _clear_pending_action(context)
    rights_preview = ", ".join(f"{k}={v}" for k, v in rights.items())
    lines = [
        f"Права для @{username} обновлены.",
        f"Права: {rights_preview}",
        f"Успешно: {success}",
        f"Ошибок: {len(failed)}",
    ]
    if failed:
        lines.extend(["Первые ошибки:"] + [f"- {item}" for item in failed[:10]])

    await update.message.reply_text("\n".join(lines), reply_markup=build_main_keyboard(_is_owner(update, context)))
