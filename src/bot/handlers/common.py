from __future__ import annotations

from telegram import Update
from telegram.ext import ContextTypes

from bot.services.membership_service import MembershipService
from bot.handlers.ui import build_main_keyboard

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

FULL_ADMIN_RIGHTS: dict[str, bool] = {
    "is_anonymous": False,
    "can_manage_chat": True,
    "can_delete_messages": True,
    "can_manage_video_chats": True,
    "can_restrict_members": True,
    "can_promote_members": True,
    "can_change_info": True,
    "can_invite_users": True,
    "can_post_stories": True,
    "can_edit_stories": True,
    "can_delete_stories": True,
    "can_post_messages": True,
    "can_edit_messages": True,
    "can_pin_messages": True,
    "can_manage_topics": True,
}

def _is_owner(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    if update.effective_user is None:
        return False
    owner_ids: set[int] = context.application.bot_data["owner_user_ids"]
    return update.effective_user.id in owner_ids


async def _is_owner_or_chat_admin(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    if _is_owner(update, context):
        return True
    if update.effective_chat is None or update.effective_user is None:
        return False
    try:
        member = await context.bot.get_chat_member(update.effective_chat.id, update.effective_user.id)
        return member.status in {"creator", "administrator"}
    except Exception:
        return False


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.message is None:
        return

    text = (
        "Привет! Я бот для контроля участников в группах и каналах.\n\n"
        "Что я умею:\n"
        "• отслеживать изменения участников через chat_member обновления;\n"
        "• хранить состояние участников в базе;\n"
        "• удалять пользователя из всех известных чатов (группы/каналы) командой администратора.\n\n"
        "Используй кнопки ниже для управления. /help — справка по командам."
    )
    await update.message.reply_text(text, reply_markup=build_main_keyboard(_is_owner(update, context)))


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.message is None:
        return

    text = (
        "Доступные команды:\n\n"
        "/start — приветствие и краткое описание возможностей бота.\n"
        "/help — список команд и их описание.\n"
        "/add_users <username ...> — вручную добавить одного или нескольких пользователей по username в БД (только OWNER_USER_IDS).\n"
        "/create_chat_bundle — запустить мастер создания набора чатов по названию (только OWNER_USER_IDS).\n"
        "/invite_groups_add <chat_id ...> — добавить чаты в дефолтный список приглашений (только OWNER_USER_IDS).\n"
        "/invite_groups_remove <chat_id ...> — удалить чаты из дефолтного списка приглашений (только OWNER_USER_IDS).\n"
        "/invite_groups — показать дефолтный список приглашений (только OWNER_USER_IDS).\n"
        "/moderators_add <username ...> — добавить пользователей в список модераторов (только OWNER_USER_IDS).\n"
        "/moderators_remove <username ...> — удалить пользователей из списка модераторов (только OWNER_USER_IDS).\n"
        "/moderators — показать список модераторов (только OWNER_USER_IDS).\n"
        "/users — показать всех пользователей, сохраненных в БД (только OWNER_USER_IDS).\n"
        "/delete_user <username> — удалить пользователя из БД (только OWNER_USER_IDS).\n"
        "/sync_me — синхронизировать ваш id/имя и членство по всем известным чатам бота.\n"
        "/sync_everyone — синхронизировать всех пользователей БД по известным чатам (только OWNER_USER_IDS).\n"
        "/groups — показать все чаты, в которых бот сейчас учитывается (только OWNER_USER_IDS).\n"
        "/remove_group <chat_id> — убрать чат из списка учитываемых (только OWNER_USER_IDS).\n"
        "/refresh_groups — перепроверить членство бота в известных чатах и обновить список (только OWNER_USER_IDS).\n"
        "/user_groups <username> — показать чаты пользователя по логину (только OWNER_USER_IDS).\n"
        "/remove_everywhere <username> — удалить пользователя из всех известных активных чатов по username "
        "(только OWNER_USER_IDS).\n"
        "/promote_admin <chat_id|all> <username> — назначить пользователя из БД администратором "
        "(только OWNER_USER_IDS).\n"
        "/set_admin_rank <chat_id|all> <username> <rank> — установить custom title (rank) администратора "
        "(только OWNER_USER_IDS).\n"
        "/set_admin_rights <chat_id|all> <username> <right=true|false ...> — изменить права администратора "
        "(только OWNER_USER_IDS).\n"
        "/apply_admins_here — в текущем чате применить права как в /set_admin_rights для всех участников из БД, "
        "кто состоит в чате: модераторам выставляются FULL_ADMIN_RIGHTS, остальным — DEFAULT_ADMIN_RIGHTS; "
        "затем применяется rank из БД (если есть).\n"
        "/invite_me — отправить вам инвайт-ссылки в дефолтный список чатов (если вы есть в БД)."
    )
    await update.message.reply_text(text, reply_markup=build_main_keyboard(_is_owner(update, context)))


async def add_users_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.message is None:
        return

    if not _is_owner(update, context):
        await update.message.reply_text("У вас нет прав для этой команды.")
        return

    if not context.args:
        await update.message.reply_text("Использование: /add_users <username1> [username2] ...")
        return

    raw_usernames: list[str] = []
    for arg in context.args:
        parts = [p.strip() for p in arg.split(",") if p.strip()]
        raw_usernames.extend(parts)

    usernames: list[str] = []
    seen: set[str] = set()
    for raw in raw_usernames:
        username = raw.lstrip("@").strip()
        if username and username not in seen:
            seen.add(username)
            usernames.append(username)

    if not usernames:
        await update.message.reply_text("Укажите хотя бы один корректный username.")
        return

    service: MembershipService = context.application.bot_data["membership_service"]
    added: list[str] = []
    for username in usernames:
        user = await service.add_manual_user_by_username(username)
        added.append(f"@{username} (id={user.id})")

    await update.message.reply_text("Добавлены/обновлены пользователи:\n" + "\n".join(f"- {item}" for item in added))


async def create_chat_bundle_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.message is None:
        return

    if not _is_owner(update, context):
        await update.message.reply_text("У вас нет прав для этой команды.")
        return

    context.user_data["pending_action"] = "create_chat_bundle"
    await update.message.reply_text(
        "Введите базовое название чата.\n"
        "Бот подготовит набор из двух чатов:\n"
        "1) <Название>\n"
        "2) <Название> — Inside"
    )


async def delete_user_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.message is None:
        return

    if not _is_owner(update, context):
        await update.message.reply_text("У вас нет прав для этой команды.")
        return

    if not context.args:
        await update.message.reply_text("Использование: /delete_user <username>")
        return

    username = context.args[0].strip().lstrip("@")
    if not username:
        await update.message.reply_text("Укажите корректный username.")
        return

    service: MembershipService = context.application.bot_data["membership_service"]
    deleted = await service.delete_user_by_username(username)
    if not deleted:
        await update.message.reply_text(f"Пользователь @{username} не найден в базе.")
        return

    await update.message.reply_text(f"Пользователь @{username} удален из базы данных.")


async def sync_me_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.effective_user is None or update.message is None:
        return

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
                admin_rank=getattr(member, "custom_title", None),
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


async def list_users_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.message is None:
        return

    if not _is_owner(update, context):
        await update.message.reply_text("У вас нет прав для этой команды.")
        return

    service: MembershipService = context.application.bot_data["membership_service"]
    users = await service.list_users()
    if not users:
        await update.message.reply_text("В базе пока нет пользователей.")
        return

    lines = ["Пользователи в БД:"]
    for user in users[:200]:
        username = f"@{user.username}" if user.username else "(без username)"
        lines.append(f"- {username} | id={user.id} | {user.full_name}")

    if len(users) > 200:
        lines.append(f"... и еще {len(users) - 200} пользователей")

    await update.message.reply_text("\n".join(lines))


async def sync_everyone_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.message is None:
        return

    if not _is_owner(update, context):
        await update.message.reply_text("У вас нет прав для этой команды.")
        return

    service: MembershipService = context.application.bot_data["membership_service"]
    users = await service.list_users()
    chats = await service.list_active_chats()

    if not users:
        await update.message.reply_text("В базе нет пользователей для синхронизации.")
        return

    if not chats:
        await update.message.reply_text("В базе нет активных чатов для синхронизации.")
        return

    processed_users = 0
    synced_statuses = 0
    skipped_users = 0
    failed: list[str] = []

    for user in users:
        if user.id <= 0:
            skipped_users += 1
            continue

        processed_users += 1
        for chat in chats:
            try:
                member = await context.bot.get_chat_member(chat.chat_id, user.id)
                await service.save_user_membership(
                    chat_id=chat.chat_id,
                    chat_title=chat.title,
                    chat_type=chat.chat_type,
                    user_id=user.id,
                    username=user.username,
                    full_name=user.full_name,
                    is_bot=False,
                    status=member.status,
                    admin_rank=getattr(member, "custom_title", None),
                )
                synced_statuses += 1
            except Exception as exc:
                failed.append(f"user={user.id}, chat={chat.chat_id}: {exc}")

    lines = [
        "Синхронизация всех пользователей завершена.",
        f"Пользователей в БД: {len(users)}",
        f"Обработано пользователей: {processed_users}",
        f"Пропущено (без реального user_id): {skipped_users}",
        f"Записано статусов: {synced_statuses}",
    ]
    if failed:
        lines.append(f"Ошибок: {len(failed)}")
        lines.extend(["Первые ошибки:"] + [f"- {item}" for item in failed[:10]])

    await update.message.reply_text("\n".join(lines))


async def groups_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.message is None:
        return

    if not _is_owner(update, context):
        await update.message.reply_text("У вас нет прав для этой команды.")
        return

    service: MembershipService = context.application.bot_data["membership_service"]
    chats = await service.list_active_chats()
    if not chats:
        await update.message.reply_text("Список чатов пуст.")
        return

    lines = ["Чаты (группы/каналы), в которых бот учитывается:"]
    for chat in chats:
        title = chat.title or "(без названия)"
        lines.append(f"- {title} | chat_id={chat.chat_id} | type={chat.chat_type}")

    await update.message.reply_text("\n".join(lines))


async def remove_group_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.message is None:
        return

    if not _is_owner(update, context):
        await update.message.reply_text("У вас нет прав для этой команды.")
        return

    if not context.args:
        await update.message.reply_text("Использование: /remove_group <chat_id>")
        return

    try:
        chat_id = int(context.args[0])
    except ValueError:
        await update.message.reply_text("chat_id должен быть целым числом.")
        return

    service: MembershipService = context.application.bot_data["membership_service"]
    removed = await service.deactivate_chat(chat_id)
    if not removed:
        await update.message.reply_text(f"Чат с chat_id={chat_id} не найден в базе.")
        return

    await update.message.reply_text(f"Чат с chat_id={chat_id} убран из списка активных.")


async def refresh_groups_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.message is None:
        return

    if not _is_owner(update, context):
        await update.message.reply_text("У вас нет прав для этой команды.")
        return

    service: MembershipService = context.application.bot_data["membership_service"]

    me = await context.bot.get_me()

    if update.effective_chat is not None and update.effective_chat.type in {"group", "supergroup", "channel"}:
        try:
            current_chat_member = await context.bot.get_chat_member(update.effective_chat.id, me.id)
            await service.save_user_membership(
                chat_id=update.effective_chat.id,
                chat_title=update.effective_chat.title,
                chat_type=update.effective_chat.type,
                user_id=me.id,
                username=me.username,
                full_name=me.full_name,
                is_bot=me.is_bot,
                status=current_chat_member.status,
            )
        except Exception:
            # continue with best-effort refresh of known chats
            pass

    chats = await service.list_all_chats()
    if not chats:
        await update.message.reply_text("В базе пока нет чатов для обновления.")
        return

    active_count = 0
    inactive_count = 0
    failed: list[str] = []

    for chat in chats:
        try:
            member = await context.bot.get_chat_member(chat.chat_id, me.id)
            status = member.status
            is_active = status in {"creator", "administrator", "member", "restricted"}
            await service.set_chat_active(chat.chat_id, is_active)
            if is_active:
                active_count += 1
            else:
                inactive_count += 1
        except Exception as exc:
            failed.append(f"{chat.chat_id}: {exc}")

    lines = [
        "Обновление списка чатов завершено.",
        f"Всего проверено: {len(chats)}",
        f"Активных: {active_count}",
        f"Неактивных: {inactive_count}",
    ]
    if failed:
        lines.append(f"Ошибок: {len(failed)}")
        lines.extend(["Первые ошибки:"] + [f"- {item}" for item in failed[:5]])

    lines.append("Важно: команда не может обнаружить полностью неизвестные чаты (группы/каналы) без update от Telegram.")
    await update.message.reply_text("\n".join(lines))


async def user_groups_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.message is None:
        return

    if not _is_owner(update, context):
        await update.message.reply_text("У вас нет прав для этой команды.")
        return

    if not context.args:
        await update.message.reply_text("Использование: /user_groups <username>")
        return

    username = context.args[0].strip().lstrip("@")
    if not username:
        await update.message.reply_text("Укажите корректный username.")
        return

    service: MembershipService = context.application.bot_data["membership_service"]
    user, chats = await service.list_user_chats_by_username(username)

    if user is None:
        await update.message.reply_text(f"Пользователь @{username} не найден в базе.")
        return

    if not chats:
        await update.message.reply_text(f"Пользователь @{username} найден, но не состоит в активных чатах.")
        return

    lines = [f"Чаты пользователя @{username} (id={user.id}):"]
    for chat in chats:
        title = chat.title or "(без названия)"
        rank = chat.admin_rank or "-"
        lines.append(f"- {title} | chat_id={chat.chat_id} | type={chat.chat_type} | status={chat.status} | rank={rank}")

    await update.message.reply_text("\n".join(lines))


async def invite_groups_add_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.message is None:
        return
    if not _is_owner(update, context):
        await update.message.reply_text("У вас нет прав для этой команды.")
        return
    if not context.args:
        await update.message.reply_text("Использование: /invite_groups_add <chat_id1> [chat_id2] ...")
        return

    service: MembershipService = context.application.bot_data["membership_service"]
    added: list[int] = []
    for raw in context.args:
        try:
            chat_id = int(raw)
        except ValueError:
            continue
        await service.add_invite_target_chat(chat_id)
        added.append(chat_id)

    if not added:
        await update.message.reply_text("Не удалось добавить ни одного chat_id.")
        return
    await update.message.reply_text("Добавлены в дефолтный список приглашений:\n" + "\n".join(f"- {c}" for c in added))


async def invite_groups_remove_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.message is None:
        return
    if not _is_owner(update, context):
        await update.message.reply_text("У вас нет прав для этой команды.")
        return
    if not context.args:
        await update.message.reply_text("Использование: /invite_groups_remove <chat_id1> [chat_id2] ...")
        return

    service: MembershipService = context.application.bot_data["membership_service"]
    removed: list[int] = []
    for raw in context.args:
        try:
            chat_id = int(raw)
        except ValueError:
            continue
        if await service.remove_invite_target_chat(chat_id):
            removed.append(chat_id)

    if not removed:
        await update.message.reply_text("Ничего не удалено (chat_id не найдены в списке).")
        return
    await update.message.reply_text("Удалены из дефолтного списка приглашений:\n" + "\n".join(f"- {c}" for c in removed))


async def invite_groups_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.message is None:
        return
    if not _is_owner(update, context):
        await update.message.reply_text("У вас нет прав для этой команды.")
        return

    service: MembershipService = context.application.bot_data["membership_service"]
    chat_ids = await service.list_invite_target_chat_ids()
    if not chat_ids:
        await update.message.reply_text("Дефолтный список приглашений пуст.")
        return
    await update.message.reply_text("Дефолтный список приглашений:\n" + "\n".join(f"- {c}" for c in chat_ids))


async def invite_me_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.message is None or update.effective_user is None:
        return

    username = (update.effective_user.username or "").strip()
    if not username:
        await update.message.reply_text("У вас не установлен username в Telegram.")
        return

    service: MembershipService = context.application.bot_data["membership_service"]
    user = await service.get_user_by_username(username)
    if user is None:
        await update.message.reply_text("Ваш username не найден в базе. Попросите администратора добавить вас.")
        return

    chat_ids = await service.list_invite_target_chat_ids()
    if not chat_ids:
        await update.message.reply_text("Список чатов для приглашений пока пуст.")
        return

    links: list[str] = []
    failed: list[str] = []
    for chat_id in chat_ids:
        try:
            invite = await context.bot.create_chat_invite_link(chat_id=chat_id)
            links.append(f"- {chat_id}: {invite.invite_link}")
        except Exception as exc:
            failed.append(f"{chat_id}: {exc}")

    lines = ["Инвайт-ссылки в дефолтные чаты:"]
    if links:
        lines.extend(links)
    if failed:
        lines.append("")
        lines.append(f"Ошибок: {len(failed)}")
        lines.extend([f"- {item}" for item in failed[:10]])
    await update.message.reply_text("\n".join(lines))


async def moderators_add_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.message is None:
        return
    if not _is_owner(update, context):
        await update.message.reply_text("У вас нет прав для этой команды.")
        return
    if not context.args:
        await update.message.reply_text("Использование: /moderators_add <username1> [username2] ...")
        return

    service: MembershipService = context.application.bot_data["membership_service"]
    added: list[str] = []
    for raw in context.args:
        username = raw.strip().lstrip("@").lower()
        if not username:
            continue
        await service.add_moderator_username(username)
        added.append(username)

    if not added:
        await update.message.reply_text("Не удалось добавить ни одного модератора.")
        return
    await update.message.reply_text("Добавлены модераторы:\n" + "\n".join(f"- @{u}" for u in added))


async def moderators_remove_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.message is None:
        return
    if not _is_owner(update, context):
        await update.message.reply_text("У вас нет прав для этой команды.")
        return
    if not context.args:
        await update.message.reply_text("Использование: /moderators_remove <username1> [username2] ...")
        return

    service: MembershipService = context.application.bot_data["membership_service"]
    removed: list[str] = []
    for raw in context.args:
        username = raw.strip().lstrip("@").lower()
        if not username:
            continue
        if await service.remove_moderator_username(username):
            removed.append(username)

    if not removed:
        await update.message.reply_text("Ничего не удалено: модераторы не найдены.")
        return
    await update.message.reply_text("Удалены из модераторов:\n" + "\n".join(f"- @{u}" for u in removed))


async def moderators_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.message is None:
        return
    if not _is_owner(update, context):
        await update.message.reply_text("У вас нет прав для этой команды.")
        return

    service: MembershipService = context.application.bot_data["membership_service"]
    moderators = await service.list_moderator_usernames()
    if not moderators:
        await update.message.reply_text("Список модераторов пуст.")
        return
    await update.message.reply_text("Модераторы:\n" + "\n".join(f"- @{u}" for u in moderators))


async def apply_admins_here_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.message is None or update.effective_chat is None:
        return

    if not await _is_owner_or_chat_admin(update, context):
        await update.message.reply_text("Только владелец бота или админ этого чата может выполнить команду.")
        return

    service: MembershipService = context.application.bot_data["membership_service"]
    users = await service.list_users()
    moderators = set(await service.list_moderator_usernames())
    if not users:
        await update.message.reply_text("В базе нет пользователей.")
        return

    chat_id = update.effective_chat.id
    applied = 0
    skipped = 0
    failed: list[str] = []

    for user in users:
        if user.id <= 0:
            skipped += 1
            continue
        try:
            member = await context.bot.get_chat_member(chat_id, user.id)
        except Exception:
            skipped += 1
            continue

        if member.status not in {"creator", "administrator", "member", "restricted"}:
            skipped += 1
            continue

        try:
            user_username = (user.username or "").lower()
            rights = FULL_ADMIN_RIGHTS if user_username in moderators else DEFAULT_ADMIN_RIGHTS
            await context.bot.promote_chat_member(chat_id=chat_id, user_id=user.id, **rights)
            rank = await service.get_membership_admin_rank(chat_id=chat_id, user_id=user.id)
            if rank:
                try:
                    await context.bot.set_chat_administrator_custom_title(chat_id=chat_id, user_id=user.id, custom_title=rank)
                except Exception:
                    pass
            applied += 1
        except Exception as exc:
            failed.append(f"user={user.id}: {exc}")

    lines = [
        "Применение admin-прав в текущем чате завершено.",
        f"Применено: {applied}",
        f"Пропущено: {skipped}",
        f"Ошибок: {len(failed)}",
    ]
    if failed:
        lines.extend([f"- {item}" for item in failed[:10]])
    await update.message.reply_text("\n".join(lines))
