#!/bin/bash
# Polled by homepanel-update.timer (every 5 min). Pulls main if it moved,
# reinstalls dependencies in case requirements.txt changed, and restarts
# the service. Runs as root (see homepanel-update.service) purely so it can
# call systemctl; the app itself still runs unprivileged as "homepanel".
set -euo pipefail

cd /opt/homepanel

git fetch origin main --quiet

LOCAL=$(git rev-parse HEAD)
REMOTE=$(git rev-parse origin/main)

if [ "$LOCAL" = "$REMOTE" ]; then
  echo "$(date -Iseconds) up to date ($LOCAL)"
  exit 0
fi

echo "$(date -Iseconds) updating $LOCAL -> $REMOTE"
git merge --ff-only origin/main
chown -R homepanel:homepanel /opt/homepanel
su -s /bin/bash homepanel -c "/opt/homepanel/.venv/bin/pip install -q -r requirements.txt"
systemctl restart homepanel
echo "$(date -Iseconds) restarted homepanel at $REMOTE"
