# Group Member Guardian Bot (Scaffold)

Скелет проекта на `python-telegram-bot` для сценария:
- отслеживать изменения участников в группах/каналах;
- хранить состояние участников в БД;
- удалять выбранного пользователя из всех известных чатов командой `/remove_everywhere <username>`.

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

- Бот должен быть администратором в целевых группах/каналах.
- Для массового удаления нужны права на ограничение пользователей в группах/каналах.
- В проде рекомендуются Postgres + webhook + миграции (Alembic).



## Управление через кнопки

После `/start` бот показывает **inline-клавиатуру**:
- базовые кнопки: помощь, синхронизация, просмотр своих чатов;
- для владельца (`OWNER_USER_IDS`) — кнопка `🛠 Админ-панель` с действиями по пользователям и чатам.

Для операций, где нужны параметры, бот сам запускает нужный сценарий, спрашивает только необходимые данные (например username, затем rank/права) и позволяет отменить действие кнопкой `❎ Отменить действие` с возвратом в начало.
Для изменения прав администратора используются 2 отдельные кнопки: `🔐 Права для групп` и `📣 Права для каналов`. В каждой кнопке открывается inline-меню с чекбоксами (✅/⬜) только для релевантных прав. Также есть отдельная кнопка демоута (снять все права сразу).
Для операций по конкретному пользователю учитываются только те чаты, где этот пользователь уже состоит (по данным БД). Чаты, где пользователя нет, автоматически пропускаются и не считаются ошибкой.
При удалении пользователя (`Удалить везде`) бот дополнительно пытается автоматически удалить сервисное сообщение Telegram о выходе/удалении пользователя из чата.
В сценариях inline-управления для назначения админа, изменения rank/прав и демоута бот теперь запрашивает область применения: `all` или список `chat_id` через запятую.

## Команды

> Дополнительно: при синхронизации членства сохраняется `rank` администратора (custom title), его видно в `/user_groups`, и он обновляется при изменениях.

> Важно: Telegram Bot API не позволяет боту самостоятельно создавать группы/каналы и автоматически добавлять в них пользователя по @username. Команда `/create_chat_bundle` делает мастер подготовки и дальнейших шагов.

- `/start` — приветствие и краткое описание возможностей.
- `/help` — список команд и их назначение.
- `/add_users <username ...>` — вручную добавить одного или нескольких пользователей по username в БД (для OWNER_USER_IDS).
- `/create_chat_bundle` — мастер подготовки набора чатов `<Название>` и `<Название> — Inside` (для OWNER_USER_IDS).
- `/invite_groups_add <chat_id ...>` — добавить чаты в дефолтный список приглашений (для OWNER_USER_IDS).
- `/invite_groups_remove <chat_id ...>` — удалить чаты из дефолтного списка приглашений (для OWNER_USER_IDS).
- `/invite_groups` — показать дефолтный список приглашений (для OWNER_USER_IDS).
- `/invite_me` — отправить вам инвайт-ссылки в дефолтный список чатов (если вы уже есть в БД).
- `/moderators_add <username ...>` — добавить пользователей в список модераторов (для OWNER_USER_IDS).
- `/moderators_remove <username ...>` — удалить пользователей из списка модераторов (для OWNER_USER_IDS).
- `/moderators` — показать список модераторов (для OWNER_USER_IDS).
- `/apply_admins_here` — в текущем чате выставить всем пользователям из БД, кто присутствует в чате, дефолтные admin-права и затем применить rank из БД (если есть).
- `/users` — показать всех пользователей, сохраненных в БД (для OWNER_USER_IDS).
- `/delete_user <username>` — удалить пользователя из базы данных (для OWNER_USER_IDS).
- `/sync_me` — синхронизировать ваш id/имя и участие в известных группах/каналах бота (только если ваш username уже есть в БД).
- `/sync_everyone` — синхронизировать всех пользователей БД по известным чатам (для OWNER_USER_IDS).
- `/groups` — показать все чаты, в которых бот учитывается в базе (для OWNER_USER_IDS).
- `/remove_group <chat_id>` — убрать чат из списка активных/учитываемых (для OWNER_USER_IDS).
- `/refresh_groups` — перепроверить членство бота в известных группах/каналах и обновить активный список (для OWNER_USER_IDS).
- `/user_groups <username>` — показать, в каких группах/каналах состоит пользователь по логину (для OWNER_USER_IDS).
- `/remove_everywhere <username>` — удалить пользователя из всех известных активных чатов по username (для OWNER_USER_IDS).
- `/promote_admin <chat_id|all|chat_id,chat_id,...> <username>` — назначить пользователя из БД администратором в указанном чате или во всех активных (для OWNER_USER_IDS).
- `/set_admin_rank <chat_id|all|chat_id,chat_id,...> <username> <rank>` — задать custom title (rank) администратору в чате/группе/канале (для OWNER_USER_IDS).
- `/set_admin_rights <chat_id|all|chat_id,chat_id,...> <username> <right=true|false ...>` — изменить права администратора, например `can_delete_messages=true` (для OWNER_USER_IDS).



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
