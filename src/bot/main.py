from __future__ import annotations

import logging

from telegram.ext import Application, ChatMemberHandler, CommandHandler

from bot.config import load_settings
from bot.db.models import Base
from bot.db.session import build_engine, build_session_factory
from bot.handlers import (
    add_users_command,
    delete_user_command,
    groups_command,
    help_command,
    list_users_command,
    on_chat_member_update,
<<<<<<< HEAD
    remove_everywhere,
=======
    on_my_chat_member_update,
    remove_everywhere,
    refresh_groups_command,
>>>>>>> 8a5e6175f2b2ebbed776a29511eb21867e6bb4f4
    remove_group_command,
    start_command,
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
<<<<<<< HEAD
=======
    app.add_handler(ChatMemberHandler(on_my_chat_member_update, ChatMemberHandler.MY_CHAT_MEMBER))
>>>>>>> 8a5e6175f2b2ebbed776a29511eb21867e6bb4f4
    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("add_users", add_users_command))
    app.add_handler(CommandHandler("delete_user", delete_user_command))
    app.add_handler(CommandHandler("sync_me", sync_me_command))
    app.add_handler(CommandHandler("groups", groups_command))
    app.add_handler(CommandHandler("remove_group", remove_group_command))
<<<<<<< HEAD
=======
    app.add_handler(CommandHandler("refresh_groups", refresh_groups_command))
>>>>>>> 8a5e6175f2b2ebbed776a29511eb21867e6bb4f4
    app.add_handler(CommandHandler("users", list_users_command))
    app.add_handler(CommandHandler("user_groups", user_groups_command))
    app.add_handler(CommandHandler("remove_everywhere", remove_everywhere))

    return app


def main() -> None:
    application = build_application()
<<<<<<< HEAD
    application.run_polling(allowed_updates=["chat_member", "message"])
=======
    application.run_polling(allowed_updates=["chat_member", "my_chat_member", "message"])
>>>>>>> 8a5e6175f2b2ebbed776a29511eb21867e6bb4f4


if __name__ == "__main__":
    main()
