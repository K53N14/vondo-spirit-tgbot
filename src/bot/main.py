from __future__ import annotations

from email.mime import application
import logging

from bot.handlers.common import add_to_default_chats
from telegram.ext import Application, CallbackQueryHandler, ChatMemberHandler, CommandHandler, MessageHandler, filters

from bot.config import load_settings
from bot.db.models import Base
from bot.db.session import build_engine, build_session_factory
from bot.handlers import (
    add_users_command,
    create_chat_bundle_command,
    delete_user_command,
    groups_command,
    help_command,
    list_users_command,
    on_chat_member_update,
    on_my_chat_member_update,
    on_action_input,
    on_inline_button,
    on_left_chat_member_cleanup,
    promote_admin_command,
    remove_everywhere,
    set_admin_rank_command,
    set_admin_rights_command,
    refresh_groups_command,
    remove_group_command,
    start_command,
    sync_everyone_command,
    sync_me_command,
    user_groups_command,
)
from bot.services import MembershipService

DEFAULT_CHATS_KEY = "default_chat_ids"

logging.basicConfig(
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
    level=logging.INFO,
)


async def post_init(application: Application) -> None:
    engine = application.bot_data["engine"]

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def post_shutdown(application: Application) -> None:
    engine = application.bot_data.get("engine")
    if engine is not None:
        await engine.dispose()


def build_application() -> Application:
    settings = load_settings()

    engine = build_engine(settings.database_url)
    session_factory = build_session_factory(engine)
    membership_service = MembershipService(session_factory)

    app = Application.builder().token(settings.bot_token).post_init(post_init).post_shutdown(post_shutdown).build()

    app.bot_data["settings"] = settings
    app.bot_data["engine"] = engine
    app.bot_data["owner_user_ids"] = settings.owner_user_ids
    app.bot_data["membership_service"] = membership_service

    #########################добавление дефолт чатов
    app.bot_data["default_chat_ids"] = settings.default_chat_ids
    if DEFAULT_CHATS_KEY not in app.bot_data:
        app.bot_data[DEFAULT_CHATS_KEY] = set()

    app.add_handler(ChatMemberHandler(on_chat_member_update, ChatMemberHandler.CHAT_MEMBER))
    app.add_handler(ChatMemberHandler(on_my_chat_member_update, ChatMemberHandler.MY_CHAT_MEMBER))
    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("add_users", add_users_command))
    app.add_handler(CommandHandler("create_chat_bundle", create_chat_bundle_command))
    app.add_handler(CommandHandler("delete_user", delete_user_command))
    app.add_handler(CommandHandler("sync_me", sync_me_command))
    app.add_handler(CommandHandler("sync_everyone", sync_everyone_command))
    app.add_handler(CommandHandler("groups", groups_command))
    app.add_handler(CommandHandler("remove_group", remove_group_command))
    app.add_handler(CommandHandler("refresh_groups", refresh_groups_command))
    app.add_handler(CommandHandler("users", list_users_command))
    app.add_handler(CommandHandler("user_groups", user_groups_command))
    app.add_handler(CommandHandler("remove_everywhere", remove_everywhere))
    app.add_handler(CommandHandler("promote_admin", promote_admin_command))
    app.add_handler(CommandHandler("set_admin_rank", set_admin_rank_command))
    app.add_handler(CommandHandler("set_admin_rights", set_admin_rights_command))
    app.add_handler(CommandHandler("add_to_default_chats", add_to_default_chats))
    app.add_handler(CallbackQueryHandler(on_inline_button))
    app.add_handler(MessageHandler(filters.StatusUpdate.LEFT_CHAT_MEMBER, on_left_chat_member_cleanup))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, on_action_input))

    return app


def main() -> None:
    application = build_application()
    application.run_polling(allowed_updates=["chat_member", "my_chat_member", "message", "callback_query"])


if __name__ == "__main__":
    main()
