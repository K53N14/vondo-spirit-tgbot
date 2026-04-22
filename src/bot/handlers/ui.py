from __future__ import annotations

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes

from bot.services.membership_service import MembershipService

CB_HELP = "main_help"
CB_SYNC_ME = "main_sync_me"
CB_MY_GROUPS = "main_my_groups"
CB_OPEN_ADMIN = "main_open_admin"
CB_BACK_MAIN = "main_back"
CB_DEFAULT_CHATS = "main_default_chats"

CB_ADMIN_USERS = "admin_users"
CB_ADMIN_GROUPS = "admin_groups"
CB_ACT_REMOVE = "act_remove_everywhere"
CB_ACT_PROMOTE = "act_promote_admin"
CB_ACT_DEMOTE = "act_demote_admin"
CB_ACT_RANK = "act_set_rank"
CB_ACT_RIGHTS_GROUPS = "act_set_rights_groups"
CB_ACT_RIGHTS_CHANNELS = "act_set_rights_channels"
CB_CANCEL = "act_cancel"

CB_RIGHTS_TOGGLE_PREFIX = "rights_toggle:"
CB_RIGHTS_APPLY = "rights_apply"

ACTION_REMOVE = "remove_everywhere"
ACTION_PROMOTE = "promote_admin"
ACTION_DEMOTE = "demote_admin"
ACTION_SET_RANK = "set_rank"
ACTION_SET_RIGHTS_GROUPS = "set_rights_groups"
ACTION_SET_RIGHTS_CHANNELS = "set_rights_channels"
ACTION_CREATE_CHAT_BUNDLE = "create_chat_bundle"

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

GROUP_ADMIN_RIGHTS = {
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
    "can_pin_messages",
    "can_manage_topics",
}

CHANNEL_ADMIN_RIGHTS = {
    "is_anonymous",
    "can_manage_chat",
    "can_delete_messages",
    "can_manage_video_chats",
    "can_promote_members",
    "can_change_info",
    "can_invite_users",
    "can_post_stories",
    "can_edit_stories",
    "can_delete_stories",
    "can_post_messages",
    "can_edit_messages",
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
        [InlineKeyboardButton("👤 Мои чаты", callback_data=CB_MY_GROUPS)],
        [InlineKeyboardButton("👤 Приглашения в основные чаты", callback_data=CB_DEFAULT_CHATS)],
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
            InlineKeyboardButton("⏬ Демоутить админа", callback_data=CB_ACT_DEMOTE),
            InlineKeyboardButton("🏷 Установить rank", callback_data=CB_ACT_RANK),
        ],
        [
            InlineKeyboardButton("🔐 Права для групп", callback_data=CB_ACT_RIGHTS_GROUPS),
            InlineKeyboardButton("📣 Права для каналов", callback_data=CB_ACT_RIGHTS_CHANNELS),
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


def build_rights_keyboard(selected: dict[str, bool], allowed_rights: set[str]) -> InlineKeyboardMarkup:
    rows: list[list[InlineKeyboardButton]] = []
    for right in sorted(allowed_rights):
        mark = "✅" if selected.get(right, False) else "⬜"
        rows.append([InlineKeyboardButton(f"{mark} {right}", callback_data=f"{CB_RIGHTS_TOGGLE_PREFIX}{right}")])

    rows.append([InlineKeyboardButton("💾 Применить выбранные права", callback_data=CB_RIGHTS_APPLY)])
    rows.append([InlineKeyboardButton("❎ Отменить действие", callback_data=CB_CANCEL)])
    rows.append([InlineKeyboardButton("↩️ В главное меню", callback_data=CB_BACK_MAIN)])
    return InlineKeyboardMarkup(rows)


def _clear_pending_action(context: ContextTypes.DEFAULT_TYPE) -> None:
    context.user_data.pop("pending_action", None)
    context.user_data.pop("pending_stage", None)
    context.user_data.pop("pending_username", None)
    context.user_data.pop("pending_rights", None)
    context.user_data.pop("pending_target_chat_ids", None)
    context.user_data.pop("pending_rights_allowed", None)


def _set_pending_action(context: ContextTypes.DEFAULT_TYPE, *, action: str, stage: str = "input") -> None:
    context.user_data["pending_action"] = action
    context.user_data["pending_stage"] = stage


def mark_removal_cleanup(context: ContextTypes.DEFAULT_TYPE, chat_id: int, user_id: int) -> None:
    storage = context.application.bot_data.setdefault("pending_removal_cleanup", {})
    chat_bucket = storage.setdefault(chat_id, set())
    chat_bucket.add(user_id)


async def _get_user_chat_ids(service: MembershipService, username: str) -> list[int]:
    _, chats = await service.list_user_chats_by_username(username)
    return [chat.chat_id for chat in chats]


def _parse_scope_input(raw_scope: str, available_chat_ids: list[int]) -> tuple[list[int], str | None]:
    scope = raw_scope.strip().lower()
    if scope == "all":
        if not available_chat_ids:
            return [], "У пользователя нет доступных чатов для операции."
        return available_chat_ids, None

    raw_parts = [part.strip() for part in raw_scope.replace(" ", "").split(",") if part.strip()]
    if not raw_parts:
        return [], "Укажи all или список chat_id через запятую."

    parsed_ids: list[int] = []
    for part in raw_parts:
        try:
            parsed_ids.append(int(part))
        except ValueError:
            return [], f"Некорректный chat_id: {part}"

    available_set = set(available_chat_ids)
    target_ids = [chat_id for chat_id in parsed_ids if chat_id in available_set]
    if not target_ids:
        return [], "Ни один из указанных chat_id не подходит (пользователь не состоит в этих чатах)."

    return target_ids, None


async def on_inline_button(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    if query is None or update.effective_user is None:
        return

    await query.answer()

    service: MembershipService = context.application.bot_data["membership_service"]
    is_owner = _is_owner(update, context)
    data = query.data or ""

    if data.startswith(CB_RIGHTS_TOGGLE_PREFIX):
        await _handle_rights_toggle(update, context, data)
        return

    if data == CB_RIGHTS_APPLY:
        await _apply_selected_rights(update, context, service)
        return

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
        username = (update.effective_user.username or "").strip()
        if not username:
            await update.message.reply_text("У вас не установлен username в Telegram. Установите username и повторите /sync_me.")
            return

        service: MembershipService = context.application.bot_data["membership_service"]
        existing_user = await service.get_user_by_username(username)
        if existing_user is None:
            await update.message.reply_text("Ваш username не найден в базе. Попросите администратора добавить вас через /add_users <username ...>.")
            return

        await service.upsert_user_profile(
            user_id=update.effective_user.id,
            username=username,
            full_name=update.effective_user.full_name,
            is_bot=update.effective_user.is_bot,
        )

        chats = await service.list_active_chats()
        synced = 0
        member_of = 0
        failed: list[str] = []

        for chat in chats:
            try:
                member = await context.bot.get_chat_member(chat_id=chat.chat_id, user_id=update.effective_user.id)
                status = member.status
                await service.save_user_membership(
                    chat_id=chat.chat_id,
                    chat_title=chat.title,
                    chat_type=chat.chat_type,
                    user_id=update.effective_user.id,
                    username=username,
                    full_name=update.effective_user.full_name,
                    is_bot=update.effective_user.is_bot,
                    status=status,
                )
                synced += 1
                if status in {"creator", "administrator", "member", "restricted"}:
                    member_of += 1
            except Exception as exc:
                failed.append(f"{chat.chat_id}: {exc}")

        lines = [
            f"Синхронизация завершена для @{username}.",
            f"Проверено чатов: {len(chats)}",
            f"Записано статусов: {synced}",
            f"Состоит в чатах: {member_of}",
        ]
        if failed:
            lines.append(f"Ошибок: {len(failed)}")
            lines.extend(["Первые ошибки:"] + [f"- {item}" for item in failed[:5]])

        await update.message.reply_text("\n".join(lines))
        return
    
    if data == CB_DEFAULT_CHATS:
        username = (update.effective_user.username or "").strip()
        if not username:
            await update.message.reply_text("У вас не установлен username в Telegram. Установите username и повторите /sync_me.")
            return

        # if not _is_owner(update, context):
        #     await update.message.reply_text("У вас нет прав.")
        #     return

        # if not context.args:
        #     await update.message.reply_text("Использование: /add_to_default_chats <username>")
        #     return

        service: MembershipService = context.application.bot_data["membership_service"]
        target_user = await service.get_user_by_username(username)

        if target_user is None:
            await update.message.reply_text(f"Пользователь @{username} не найден.")
            return

        chat_ids: set[int] = context.application.bot_data.get(DEFAULT_CHATS_KEY, set())

        if not chat_ids:
            await update.message.reply_text("Список дефолтных чатов пуст.")
            return

        success_links: list[str] = []
        failed: list[str] = []

        for chat_id in chat_ids:
            try:
                link = await context.bot.create_chat_invite_link(chat_id=chat_id, member_limit=1)
                success_links.append(link.invite_link)
            except Exception as exc:
                failed.append(f"{chat_id}: {exc}")

        lines = [
            f"Ссылки для @{username}:",
            *success_links
        ]

        if failed:
            lines.append("\nОшибки:")
            lines.extend(failed[:10])

        await update.message.reply_text("\n".join(lines))
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
            await query.message.reply_text("Нет активных чатов для вашего профиля.")
            return

        lines = [f"Ваши чаты (@{username}):"]
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
            await query.message.reply_text("Список чатов пуст.")
            return

        lines = ["Чаты (группы/каналы), в которых бот учитывается:"]
        for chat in chats:
            title = chat.title or "(без названия)"
            lines.append(f"- {title} | chat_id={chat.chat_id} | type={chat.chat_type}")
        await query.message.reply_text("\n".join(lines))
        return

    if data == CB_ACT_REMOVE:
        _set_pending_action(context, action=ACTION_REMOVE)
        await query.message.reply_text(
            "Введи username пользователя для удаления из всех активных чатов:\nПример: @alice",
            reply_markup=build_cancel_keyboard(),
        )
        return

    if data == CB_ACT_PROMOTE:
        _set_pending_action(context, action=ACTION_PROMOTE)
        await query.message.reply_text(
            "Введи username пользователя для назначения админом во всех активных чатах:\nПример: @alice",
            reply_markup=build_cancel_keyboard(),
        )
        return

    if data == CB_ACT_DEMOTE:
        _set_pending_action(context, action=ACTION_DEMOTE)
        await query.message.reply_text(
            "Введи username администратора, которого нужно демоутить во всех его чатах:\nПример: @alice",
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

    if data == CB_ACT_RIGHTS_GROUPS:
        _set_pending_action(context, action=ACTION_SET_RIGHTS_GROUPS, stage="username")
        await query.message.reply_text(
            "Введи username пользователя, которому нужно изменить ПРАВА ДЛЯ ГРУПП:\nПример: @alice",
            reply_markup=build_cancel_keyboard(),
        )
        return

    if data == CB_ACT_RIGHTS_CHANNELS:
        _set_pending_action(context, action=ACTION_SET_RIGHTS_CHANNELS, stage="username")
        await query.message.reply_text(
            "Введи username пользователя, которому нужно изменить ПРАВА ДЛЯ КАНАЛОВ:\nПример: @alice",
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

    if action == ACTION_DEMOTE:
        await _process_demote_admin(update, context, service, text)
        return

    if action == ACTION_SET_RANK:
        await _process_set_rank(update, context, service, text)
        return

    if action in {ACTION_SET_RIGHTS_GROUPS, ACTION_SET_RIGHTS_CHANNELS}:
        await _process_set_rights(update, context, service, text)
        return

    if action == ACTION_CREATE_CHAT_BUNDLE:
        await _process_create_chat_bundle(update, context, service, text)


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

    chat_ids = await _get_user_chat_ids(service, username)
    if not chat_ids:
        _clear_pending_action(context)
        await update.message.reply_text(
            f"Пользователь @{username} не состоит ни в одном активном известном чате. Нечего удалять.",
            reply_markup=build_main_keyboard(_is_owner(update, context)),
        )
        return

    success = 0
    failed: list[str] = []

    for chat_id in chat_ids:
        try:
            mark_removal_cleanup(context, chat_id=chat_id, user_id=target_user.id)
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
    stage = context.user_data.get("pending_stage", "input")

    if stage == "input":
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

        user_chat_ids = await _get_user_chat_ids(service, username)
        if not user_chat_ids:
            _clear_pending_action(context)
            await update.message.reply_text(
                f"Пользователь @{username} не состоит ни в одном активном известном чате. Операция не требуется.",
                reply_markup=build_main_keyboard(_is_owner(update, context)),
            )
            return

        context.user_data["pending_username"] = username
        context.user_data["pending_stage"] = "scope"
        await update.message.reply_text(
            "Укажи, где применить действие: all или список chat_id через запятую.\n"
            "Пример: all\n"
            "Пример: -100111,-100222",
            reply_markup=build_cancel_keyboard(),
        )
        return

    username = str(context.user_data.get("pending_username", "")).strip()
    target_user = await service.get_user_by_username(username)
    if target_user is None or target_user.id <= 0:
        await update.message.reply_text("Пользователь больше недоступен в БД.", reply_markup=build_cancel_keyboard())
        return

    user_chat_ids = await _get_user_chat_ids(service, username)
    chat_ids, scope_error = _parse_scope_input(raw_username, user_chat_ids)
    if scope_error:
        await update.message.reply_text(scope_error, reply_markup=build_cancel_keyboard())
        return

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


async def _process_demote_admin(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    service: MembershipService,
    raw_username: str,
) -> None:
    stage = context.user_data.get("pending_stage", "input")

    if stage == "input":
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

        user_chat_ids = await _get_user_chat_ids(service, username)
        if not user_chat_ids:
            _clear_pending_action(context)
            await update.message.reply_text(
                f"Пользователь @{username} не состоит ни в одном активном известном чате. Операция не требуется.",
                reply_markup=build_main_keyboard(_is_owner(update, context)),
            )
            return

        context.user_data["pending_username"] = username
        context.user_data["pending_stage"] = "scope"
        await update.message.reply_text(
            "Укажи, где применить демоут: all или список chat_id через запятую.\n"
            "Пример: all\n"
            "Пример: -100111,-100222",
            reply_markup=build_cancel_keyboard(),
        )
        return

    username = str(context.user_data.get("pending_username", "")).strip()
    target_user = await service.get_user_by_username(username)
    if target_user is None or target_user.id <= 0:
        await update.message.reply_text("Пользователь больше недоступен в БД.", reply_markup=build_cancel_keyboard())
        return

    user_chat_ids = await _get_user_chat_ids(service, username)
    chat_ids, scope_error = _parse_scope_input(raw_username, user_chat_ids)
    if scope_error:
        await update.message.reply_text(scope_error, reply_markup=build_cancel_keyboard())
        return

    demote_rights = {right: False for right in ALLOWED_ADMIN_RIGHTS}
    success = 0
    failed: list[str] = []
    for chat_id in chat_ids:
        try:
            await context.bot.promote_chat_member(chat_id=chat_id, user_id=target_user.id, **demote_rights)
            success += 1
        except Exception as exc:
            failed.append(f"{chat_id}: {exc}")

    _clear_pending_action(context)
    lines = [f"Демоут @{username} завершен.", f"Успешно: {success}", f"Ошибок: {len(failed)}"]
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

        user_chat_ids = await _get_user_chat_ids(service, username)
        if not user_chat_ids:
            _clear_pending_action(context)
            await update.message.reply_text(
                f"Пользователь @{username} не состоит ни в одном активном известном чате. Операция не требуется.",
                reply_markup=build_main_keyboard(_is_owner(update, context)),
            )
            return

        context.user_data["pending_username"] = username
        context.user_data["pending_stage"] = "scope"
        await update.message.reply_text(
            "Укажи, где применить rank: all или список chat_id через запятую.\n"
            "Пример: all\n"
            "Пример: -100111,-100222",
            reply_markup=build_cancel_keyboard(),
        )
        return

    if stage == "scope":
        username = str(context.user_data.get("pending_username", "")).strip()
        user_chat_ids = await _get_user_chat_ids(service, username)
        target_chat_ids, scope_error = _parse_scope_input(user_input, user_chat_ids)
        if scope_error:
            await update.message.reply_text(scope_error, reply_markup=build_cancel_keyboard())
            return
        context.user_data["pending_target_chat_ids"] = target_chat_ids
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

    chat_ids = context.user_data.get("pending_target_chat_ids") or await _get_user_chat_ids(service, username)
    if not chat_ids:
        _clear_pending_action(context)
        await update.message.reply_text(
            f"Пользователь @{username} не состоит ни в одном активном известном чате. Операция не требуется.",
            reply_markup=build_main_keyboard(_is_owner(update, context)),
        )
        return

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
    action = context.user_data.get("pending_action")
    allowed_rights = GROUP_ADMIN_RIGHTS if action == ACTION_SET_RIGHTS_GROUPS else CHANNEL_ADMIN_RIGHTS

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

        user_chat_ids = await _get_user_chat_ids(service, username)
        if not user_chat_ids:
            _clear_pending_action(context)
            await update.message.reply_text(
                f"Пользователь @{username} не состоит ни в одном активном известном чате. Операция не требуется.",
                reply_markup=build_main_keyboard(_is_owner(update, context)),
            )
            return

        context.user_data["pending_username"] = username
        context.user_data["pending_stage"] = "scope"
        await update.message.reply_text(
            "Укажи, где применить изменение прав: all или список chat_id через запятую.\n"
            "Пример: all\n"
            "Пример: -100111,-100222",
            reply_markup=build_cancel_keyboard(),
        )
        return

    if stage == "scope":
        username = str(context.user_data.get("pending_username", "")).strip()
        user_chat_ids = await _get_user_chat_ids(service, username)
        target_chat_ids, scope_error = _parse_scope_input(user_input, user_chat_ids)
        if scope_error:
            await update.message.reply_text(scope_error, reply_markup=build_cancel_keyboard())
            return

        context.user_data["pending_target_chat_ids"] = target_chat_ids
        context.user_data["pending_stage"] = "rights_select"
        context.user_data["pending_rights_allowed"] = list(sorted(allowed_rights))
        context.user_data["pending_rights"] = {right: False for right in allowed_rights}

        await update.message.reply_text(
            f"Выбери права для @{username}. ✅ — право будет выдано, ⬜ — право будет снято.",
            reply_markup=build_rights_keyboard(context.user_data["pending_rights"], allowed_rights),
        )
        return

    await update.message.reply_text("Используй кнопки выбора прав или отмени действие.", reply_markup=build_cancel_keyboard())


async def _process_create_chat_bundle(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    service: MembershipService,
    raw_title: str,
) -> None:
    title = raw_title.strip()
    if not title:
        await update.message.reply_text("Название не может быть пустым. Введите корректное название чата.")
        return

    inside_title = f"{title} — Inside"
    await service.add_manual_user_by_username("tishkova_vondo")

    chats = await service.list_active_chats()
    target_titles = {title, inside_title}
    matched_chat_ids = [chat.chat_id for chat in chats if (chat.title or "").strip() in target_titles]

    _clear_pending_action(context)
    lines = [
        "Готово. Шаблон набора чатов сформирован:",
        f"- {title}",
        f"- {inside_title}",
        "",
        "⚠️ Ограничение Telegram Bot API:",
        "Бот не может сам создавать группы/чаты и не может сам добавлять пользователя по @username в чат.",
        "",
        "Что делать дальше:",
        "1) Создай эти два чата вручную.",
        "2) Добавь в оба чата бота и @tishkova_vondo.",
        "3) После этого нажми /refresh_groups и выполни назначение прав.",
    ]

    if matched_chat_ids:
        scope = ",".join(str(chat_id) for chat_id in matched_chat_ids)
        lines.extend(
            [
                "",
                "Обнаружены подходящие чаты в базе (по названию).",
                "Для назначения admin-прав @tishkova_vondo можешь использовать:",
                f"/promote_admin {scope} tishkova_vondo",
            ]
        )
    else:
        lines.extend(
            [
                "",
                "Пока подходящие чаты не найдены в базе.",
                "После добавления бота в чаты и /refresh_groups команда для назначения будет такой:",
                "/promote_admin all tishkova_vondo",
            ]
        )

    await update.message.reply_text("\n".join(lines), reply_markup=build_main_keyboard(_is_owner(update, context)))


async def on_left_chat_member_cleanup(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.message is None or update.message.left_chat_member is None:
        return

    chat_id = update.effective_chat.id if update.effective_chat is not None else None
    if chat_id is None:
        return

    removed_user_id = update.message.left_chat_member.id
    storage = context.application.bot_data.get("pending_removal_cleanup", {})
    chat_bucket = storage.get(chat_id)
    if not isinstance(chat_bucket, set) or removed_user_id not in chat_bucket:
        return

    try:
        await context.bot.delete_message(chat_id=chat_id, message_id=update.message.message_id)
    except Exception:
        pass
    finally:
        chat_bucket.discard(removed_user_id)


async def _handle_rights_toggle(update: Update, context: ContextTypes.DEFAULT_TYPE, data: str) -> None:
    query = update.callback_query
    if query is None:
        return

    if context.user_data.get("pending_action") not in {ACTION_SET_RIGHTS_GROUPS, ACTION_SET_RIGHTS_CHANNELS} or context.user_data.get("pending_stage") != "rights_select":
        await query.message.reply_text("Нет активного сценария изменения прав. Запусти его из админ-панели.")
        return

    right = data.replace(CB_RIGHTS_TOGGLE_PREFIX, "", 1)
    allowed = set(context.user_data.get("pending_rights_allowed") or [])
    if right not in allowed:
        return

    selected = context.user_data.get("pending_rights")
    if not isinstance(selected, dict):
        selected = {r: False for r in allowed}

    selected[right] = not bool(selected.get(right, False))
    context.user_data["pending_rights"] = selected

    await query.edit_message_reply_markup(reply_markup=build_rights_keyboard(selected, allowed))


async def _apply_selected_rights(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    service: MembershipService,
) -> None:
    query = update.callback_query
    if query is None:
        return

    if context.user_data.get("pending_action") not in {ACTION_SET_RIGHTS_GROUPS, ACTION_SET_RIGHTS_CHANNELS} or context.user_data.get("pending_stage") != "rights_select":
        await query.message.reply_text("Нет активного сценария изменения прав. Запусти его из админ-панели.")
        return

    username = str(context.user_data.get("pending_username", "")).strip()
    selected = context.user_data.get("pending_rights")
    if not username or not isinstance(selected, dict):
        await query.message.reply_text("Не удалось применить права: потеряно состояние сценария.")
        _clear_pending_action(context)
        return

    target_user = await service.get_user_by_username(username)
    if target_user is None or target_user.id <= 0:
        await query.message.reply_text("Пользователь больше недоступен в БД.")
        _clear_pending_action(context)
        return

    chat_ids = context.user_data.get("pending_target_chat_ids") or await _get_user_chat_ids(service, username)
    if not chat_ids:
        _clear_pending_action(context)
        await query.message.reply_text(
            f"Пользователь @{username} не состоит ни в одном активном известном чате. Операция не требуется.",
            reply_markup=build_main_keyboard(_is_owner(update, context)),
        )
        return

    allowed = set(context.user_data.get("pending_rights_allowed") or [])
    rights_payload = {right: bool(selected.get(right, False)) for right in allowed}
    success = 0
    failed: list[str] = []

    for chat_id in chat_ids:
        try:
            await context.bot.promote_chat_member(chat_id=chat_id, user_id=target_user.id, **rights_payload)
            success += 1
        except Exception as exc:
            failed.append(f"{chat_id}: {exc}")

    _clear_pending_action(context)
    enabled = [right for right, value in rights_payload.items() if value]
    enabled_text = ", ".join(sorted(enabled)) if enabled else "(все права сняты)"

    lines = [
        f"Права для @{username} обновлены.",
        f"Выбраны права: {enabled_text}",
        f"Успешно: {success}",
        f"Ошибок: {len(failed)}",
    ]
    if failed:
        lines.extend(["Первые ошибки:"] + [f"- {item}" for item in failed[:10]])

    await query.message.reply_text("\n".join(lines), reply_markup=build_main_keyboard(_is_owner(update, context)))
