from __future__ import annotations

import logging

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
    apply_admins_here_command,
    invite_groups_add_command,
    invite_groups_command,
    invite_groups_remove_command,
    invite_me_command,
    list_users_command,
    moderators_add_command,
    moderators_command,
    moderators_remove_command,
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

    app.add_handler(ChatMemberHandler(on_chat_member_update, ChatMemberHandler.CHAT_MEMBER))
    app.add_handler(ChatMemberHandler(on_my_chat_member_update, ChatMemberHandler.MY_CHAT_MEMBER))
    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("add_users", add_users_command))
    app.add_handler(CommandHandler("create_chat_bundle", create_chat_bundle_command))
    app.add_handler(CommandHandler("apply_admins_here", apply_admins_here_command))
    app.add_handler(CommandHandler("invite_groups_add", invite_groups_add_command))
    app.add_handler(CommandHandler("invite_groups_remove", invite_groups_remove_command))
    app.add_handler(CommandHandler("invite_groups", invite_groups_command))
    app.add_handler(CommandHandler("invite_me", invite_me_command))
    app.add_handler(CommandHandler("moderators_add", moderators_add_command))
    app.add_handler(CommandHandler("moderators_remove", moderators_remove_command))
    app.add_handler(CommandHandler("moderators", moderators_command))
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
    app.add_handler(CallbackQueryHandler(on_inline_button))
    app.add_handler(MessageHandler(filters.StatusUpdate.LEFT_CHAT_MEMBER, on_left_chat_member_cleanup))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, on_action_input))

    return app


def main() -> None:
    application = build_application()
    application.run_polling(allowed_updates=["chat_member", "my_chat_member", "message", "callback_query"])


if __name__ == "__main__":
    main()
