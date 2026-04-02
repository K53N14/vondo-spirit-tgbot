from __future__ import annotations

from telegram import Update
from telegram.ext import ContextTypes

from bot.services.membership_service import MembershipService


def _is_owner(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    if update.effective_user is None:
        return False
    owner_ids: set[int] = context.application.bot_data["owner_user_ids"]
    return update.effective_user.id in owner_ids


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
        "/add_users <username ...> — вручную добавить одного или нескольких пользователей по username в БД (только OWNER_USER_IDS).\n"
        "/users — показать всех пользователей, сохраненных в БД (только OWNER_USER_IDS).\n"
        "/delete_user <username> — удалить пользователя из БД (только OWNER_USER_IDS).\n"
        "/sync_me — синхронизировать ваш id/имя и членство по всем известным группам бота.\n"
        "/sync_everyone — синхронизировать всех пользователей БД по известным группам (только OWNER_USER_IDS).\n"
        "/groups — показать все группы, в которых бот сейчас учитывается (только OWNER_USER_IDS).\n"
        "/remove_group <chat_id> — убрать группу из списка учитываемых (только OWNER_USER_IDS).\n"
        "/refresh_groups — перепроверить членство бота в известных группах и обновить список (только OWNER_USER_IDS).\n"
        "/user_groups <username> — показать группы пользователя по логину (только OWNER_USER_IDS).\n"
        "/remove_everywhere <username> — удалить пользователя из всех известных активных групп по username "
        "(только OWNER_USER_IDS)."
    )
    await update.message.reply_text(text)


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
            )
            synced += 1
            if status in {"creator", "administrator", "member", "restricted"}:
                member_of += 1
        except Exception as exc:
            failed.append(f"{chat.chat_id}: {exc}")

    lines = [
        f"Синхронизация завершена для @{username}.",
        f"Проверено групп: {len(chats)}",
        f"Записано статусов: {synced}",
        f"Состоит в группах: {member_of}",
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
        await update.message.reply_text("В базе нет активных групп для синхронизации.")
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
        await update.message.reply_text("Список групп пуст.")
        return

    lines = ["Группы, в которых бот учитывается:"]
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
        await update.message.reply_text(f"Группа с chat_id={chat_id} не найдена в базе.")
        return

    await update.message.reply_text(f"Группа с chat_id={chat_id} убрана из списка активных.")


async def refresh_groups_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.message is None:
        return

    if not _is_owner(update, context):
        await update.message.reply_text("У вас нет прав для этой команды.")
        return

    service: MembershipService = context.application.bot_data["membership_service"]

    me = await context.bot.get_me()

    if update.effective_chat is not None and update.effective_chat.type in {"group", "supergroup"}:
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
        await update.message.reply_text("В базе пока нет групп для обновления.")
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
        "Обновление списка групп завершено.",
        f"Всего проверено: {len(chats)}",
        f"Активных: {active_count}",
        f"Неактивных: {inactive_count}",
    ]
    if failed:
        lines.append(f"Ошибок: {len(failed)}")
        lines.extend(["Первые ошибки:"] + [f"- {item}" for item in failed[:5]])

    lines.append("Важно: команда не может обнаружить полностью неизвестные группы без update от Telegram.")
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
        await update.message.reply_text(f"Пользователь @{username} найден, но не состоит в активных группах.")
        return

    lines = [f"Группы пользователя @{username} (id={user.id}):"]
    for chat in chats:
        title = chat.title or "(без названия)"
        lines.append(f"- {title} | chat_id={chat.chat_id} | type={chat.chat_type} | status={chat.status}")

    await update.message.reply_text("\n".join(lines))
