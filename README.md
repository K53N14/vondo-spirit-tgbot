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



## Управление через кнопки

После `/start` бот показывает **inline-клавиатуру**:
- базовые кнопки: помощь, синхронизация, просмотр своих групп;
- для владельца (`OWNER_USER_IDS`) — кнопка `🛠 Админ-панель` с действиями по пользователям и группам.

Для операций, где нужны параметры, бот сам запускает нужный сценарий, спрашивает только необходимые данные (например username, затем rank/права) и позволяет отменить действие кнопкой `❎ Отменить действие` с возвратом в начало.
Для операций по конкретному пользователю учитываются только те группы, где этот пользователь уже состоит (по данным БД). Группы, где пользователя нет, автоматически пропускаются и не считаются ошибкой.

## Команды

- `/start` — приветствие и краткое описание возможностей.
- `/help` — список команд и их назначение.
- `/add_users <username ...>` — вручную добавить одного или нескольких пользователей по username в БД (для OWNER_USER_IDS).
- `/users` — показать всех пользователей, сохраненных в БД (для OWNER_USER_IDS).
- `/delete_user <username>` — удалить пользователя из базы данных (для OWNER_USER_IDS).
- `/sync_me` — синхронизировать ваш id/имя и участие в известных группах бота (только если ваш username уже есть в БД).
- `/sync_everyone` — синхронизировать всех пользователей БД по известным группам (для OWNER_USER_IDS).
- `/groups` — показать все группы, в которых бот учитывается в базе (для OWNER_USER_IDS).
- `/remove_group <chat_id>` — убрать группу из списка активных/учитываемых (для OWNER_USER_IDS).
- `/refresh_groups` — перепроверить членство бота в известных группах и обновить активный список (для OWNER_USER_IDS).
- `/user_groups <username>` — показать, в каких группах состоит пользователь по логину (для OWNER_USER_IDS).
- `/remove_everywhere <username>` — удалить пользователя из всех известных активных групп по username (для OWNER_USER_IDS).
- `/promote_admin <chat_id|all> <username>` — назначить пользователя из БД администратором в указанной группе или во всех активных (для OWNER_USER_IDS).
- `/set_admin_rank <chat_id|all> <username> <rank>` — задать custom title (rank) администратору в группе/группах (для OWNER_USER_IDS).
- `/set_admin_rights <chat_id|all> <username> <right=true|false ...>` — изменить права администратора, например `can_delete_messages=true` (для OWNER_USER_IDS).



> Примечание: ID чатов Telegram (особенно supergroup, вида `-100...`) очень большие, поэтому в модели БД используется `BIGINT`.

## PostgreSQL (Docker)

### Файлы и безопасная структура

- `docker-compose.yml` — без секретов, использует переменные `POSTGRES_DB`, `POSTGRES_USER`, `POSTGRES_PASSWORD`.
- `docker-compose.override.example.yml` — пример локального/серверного override (публикация порта только на localhost).
- `.env.example` — только шаблон значений.
- На сервере создай приватные файлы `.env` и `docker-compose.override.yml` (они не должны попадать в git).

### Локально/сервер: запуск базы

```bash
cp .env.example .env
cp docker-compose.override.example.yml docker-compose.override.yml
# отредактируй .env: задай реальные POSTGRES_USER/POSTGRES_PASSWORD

docker compose up -d postgres
docker compose ps
docker compose logs -f postgres
```

### Строка подключения для бота

Используй `DATABASE_URL` в формате:

```env
DATABASE_URL=postgresql+asyncpg://<POSTGRES_USER>:<POSTGRES_PASSWORD>@<SERVER_IP_OR_HOST>:5432/<POSTGRES_DB>
```

### Как выбрать логин/пароль

- Логин/пароль **не генерируются автоматически** из `docker-compose.yml`.
- `POSTGRES_USER` и `POSTGRES_PASSWORD` ты задаешь сам в `.env`.
- Рекомендуется:
  - `POSTGRES_USER`: отдельный пользователь приложения, например `bot_app`.
  - `POSTGRES_PASSWORD`: случайный пароль длиной 24+ символов (буквы разных регистров, цифры, спецсимволы).
- Для генерации пароля можно использовать:

```bash
openssl rand -base64 36
```

### Развертывание PostgreSQL на сервере (Docker)

1. Установи Docker и Docker Compose plugin.
2. Скопируй в папку проекта `docker-compose.yml`, `docker-compose.override.example.yml`, `.env.example`.
3. Создай `.env` и `docker-compose.override.yml` из примеров.
4. Заполни в `.env` реальные `POSTGRES_DB`, `POSTGRES_USER`, `POSTGRES_PASSWORD` и `DATABASE_URL`.
5. Запусти базу: `docker compose up -d postgres`.
6. Проверь готовность: `docker compose ps` и `docker compose logs -f postgres`.
7. В firewall ограничь доступ к порту 5432 (или оставь только localhost bind).
8. Запусти бота: `python -m bot.main`.

> Для продакшна обязательно регулярно делать backup (pg_dump), менять пароль при утечках и не хранить реальные секреты в GitHub.



## Railway

В репозитории есть готовый `railway.json` без необходимости руками задавать Start Command в UI.

Что важно для Railway:
- зависимости ставятся из `requirements.txt` (через `nixpacks.toml`, без `pip install .`);
- бот стартует командой `PYTHONPATH=src python -m bot.main`;
- обязательно задай переменные окружения: `BOT_TOKEN`, `DATABASE_URL`, `OWNER_USER_IDS`.

Самый короткий рабочий сценарий:
1. Создай сервис из этого репозитория (Railway автоматически подхватит `railway.json` + `nixpacks.toml`).
2. Добавь PostgreSQL plugin в том же Railway-проекте.
3. В Variables сервиса бота задай:
   - `BOT_TOKEN=<токен_бота>`
   - `OWNER_USER_IDS=<id1,id2>`
   - `DATABASE_URL=postgresql+asyncpg://${{Postgres.PGUSER}}:${{Postgres.PGPASSWORD}}@${{Postgres.PGHOST}}:${{Postgres.PGPORT}}/${{Postgres.PGDATABASE}}?ssl=require`
4. Нажми Deploy.

Если Railway подставляет URL с `target_session_attrs=read-write`, код бота теперь автоматически убирает этот параметр на старте.

## Service deployment (systemd)

Готовые файлы для деплоя:
- `deploy/systemd/group-member-guardian.service`
- `scripts/restart.sh`
- `DEPLOY.md` (пошаговый гайд)

Пути в текущем шаблоне настроены для проекта в `/root/vondo-spirit-tgbot`.
Если у тебя другой путь — обнови `WorkingDirectory`, `EnvironmentFile`, `ExecStart` в unit-файле и `PROJECT_DIR` в `scripts/restart.sh`.
