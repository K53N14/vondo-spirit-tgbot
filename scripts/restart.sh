#!/usr/bin/env bash
set -euo pipefail

SERVICE_NAME="group-member-guardian"
PROJECT_DIR="/opt/vondo-spirit-tgbot"

cd "$PROJECT_DIR"

if [ ! -d .venv ]; then
  python3 -m venv .venv
fi

source .venv/bin/activate
pip install -e .

sudo systemctl daemon-reload
sudo systemctl restart "$SERVICE_NAME"
sudo systemctl status "$SERVICE_NAME" --no-pager
