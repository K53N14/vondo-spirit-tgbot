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
- `/add_users <username ...>` — вручную добавить одного или нескольких пользователей по username в БД (для OWNER_USER_IDS).
- `/users` — показать всех пользователей, сохраненных в БД (для OWNER_USER_IDS).
- `/delete_user <username>` — удалить пользователя из базы данных (для OWNER_USER_IDS).
- `/sync_me` — синхронизировать ваш id/имя и участие в известных группах бота (только если ваш username уже есть в БД).
- `/groups` — показать все группы, в которых бот учитывается в базе (для OWNER_USER_IDS).
- `/remove_group <chat_id>` — убрать группу из списка активных/учитываемых (для OWNER_USER_IDS).
- `/user_groups <username>` — показать, в каких группах состоит пользователь по логину (для OWNER_USER_IDS).
- `/remove_everywhere <username>` — удалить пользователя из всех известных активных групп по username (для OWNER_USER_IDS).


## PostgreSQL (Docker)

### Локально/сервер: запуск базы

```bash
docker compose up -d postgres
docker compose ps
docker compose logs -f postgres
```

### Строка подключения для бота

Используй `DATABASE_URL` в формате:

```env
DATABASE_URL=postgresql+asyncpg://bot_user:bot_password@<SERVER_IP_OR_HOST>:5432/group_member_guardian
```

### Развертывание PostgreSQL на сервере (Docker)

1. Установи Docker и Docker Compose plugin.
2. Скопируй в папку проекта файл `docker-compose.yml`.
3. Запусти базу: `docker compose up -d postgres`.
4. Проверь готовность: `docker compose ps` и `docker compose logs -f postgres`.
5. Открой порт `5432` в firewall только для доверенных IP (или не публикуй наружу и используй private network/VPN).
6. В `.env` бота укажи правильный `DATABASE_URL` с адресом сервера.
7. Запусти бота: `python -m bot.main`.

> Для продакшна обязательно поменяй `POSTGRES_PASSWORD`, сделай бэкапы и ограничь доступ к порту БД.
