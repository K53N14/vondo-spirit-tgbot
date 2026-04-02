# Deploy Guide (Ubuntu + systemd + Docker PostgreSQL)

## 1) Clone project

```bash
git clone <YOUR_REPO_URL> /root/vondo-spirit-tgbot
cd /root/vondo-spirit-tgbot
```

## 2) Configure environment

```bash
cp .env.example .env
cp docker-compose.override.example.yml docker-compose.override.yml
nano .env
```

Required in `.env`:
- `BOT_TOKEN`
- `OWNER_USER_IDS`
- `POSTGRES_DB`
- `POSTGRES_USER`
- `POSTGRES_PASSWORD`
- `DATABASE_URL`

## 3) Start PostgreSQL via Docker

```bash
docker compose up -d postgres
docker compose ps
docker compose logs -f postgres
```

## 4) Create virtualenv and install app

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e .
```

## 5) Install systemd service

```bash
sudo cp deploy/systemd/group-member-guardian.service /etc/systemd/system/group-member-guardian.service
sudo systemctl daemon-reload
sudo systemctl enable group-member-guardian
sudo systemctl start group-member-guardian
sudo systemctl status group-member-guardian --no-pager
```

## 6) Logs

```bash
journalctl -u group-member-guardian -f
```

## 7) Update + restart

```bash
./scripts/restart.sh
```

## 8) Rollback (example)

```bash
cd /root/vondo-spirit-tgbot
git checkout <PREVIOUS_COMMIT>
./scripts/restart.sh
```

## Notes
- Service defaults to user/group `root` in `deploy/systemd/group-member-guardian.service` — adjust if needed.
- Keep `.env` private and never commit real secrets.
- Restrict DB network exposure (prefer localhost bind or private network).
