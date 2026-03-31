# Group Member Guardian Bot (Scaffold)

Скелет проекта на `python-telegram-bot` для сценария:
- отслеживать изменения участников в группах;
- хранить состояние участников в БД;
- удалять выбранного пользователя из всех известных групп командой `/remove_everywhere <username>`.

## Требования

- Python 3.9+

## Quick start

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .
cp .env.example .env
python -m bot.main
```

## Структура

- `src/bot/main.py` — точка входа, инициализация PTB application и регистрация handlers.
- `src/bot/handlers/chat_member.py` — обработка `chat_member` обновлений.
- `src/bot/handlers/admin.py` — команда `/remove_everywhere`.
- `src/bot/db/models.py` — минимальные SQLAlchemy модели.
- `src/bot/services/membership_service.py` — бизнес-логика синхронизации member state.
- `src/bot/repositories/membership_repo.py` — слой доступа к данным.

## Важно

- Бот должен быть администратором в целевых группах.
- Для массового удаления нужны права на ограничение пользователей в группах.
- В проде рекомендуются Postgres + webhook + миграции (Alembic).


## Команды

- `/start` — приветствие и краткое описание возможностей.
- `/help` — список команд и их назначение.
- `/add_user <username>` — вручную добавить пользователя по username в БД (для OWNER_USER_IDS).
- `/users` — показать всех пользователей, сохраненных в БД (для OWNER_USER_IDS).
- `/user_groups <username>` — показать, в каких группах состоит пользователь по логину (для OWNER_USER_IDS).
- `/remove_everywhere <username>` — удалить пользователя из всех известных активных групп по username (для OWNER_USER_IDS).
