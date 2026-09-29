#!/bin/bash
# Polled by homepanel-update.timer (every 5 min). Pulls main if it moved,
# reinstalls dependencies in case requirements.txt changed, and restarts
# the service. Runs as root (see homepanel-update.service) purely so it can
# call systemctl; the app itself still runs unprivileged as "homepanel".
set -euo pipefail

cd /opt/homepanel

# /opt/homepanel is owned by "homepanel", not root, so git's ownership check
# (safe.directory, CVE-2022-24765) refuses to touch it otherwise. Scoped to
# this invocation rather than `git config --global`, so it doesn't depend on
# a one-off manual step on the box.
git() { command git -c safe.directory=/opt/homepanel "$@"; }

git fetch origin main --quiet

LOCAL=$(git rev-parse HEAD)
REMOTE=$(git rev-parse origin/main)

if [ "$LOCAL" = "$REMOTE" ]; then
  echo "$(date -Iseconds) up to date ($LOCAL)"
  exit 0
fi

echo "$(date -Iseconds) updating $LOCAL -> $REMOTE"
# reset --hard, not merge --ff-only: this checkout is a disposable mirror of
# origin/main, never a place for local edits, so any local drift (e.g. a
# manual chmod applied directly on the box) should always lose, not block
# the update. .env/.venv/.cache aren't tracked, so this never touches them.
git reset --hard origin/main
chown -R homepanel:homepanel /opt/homepanel
su -s /bin/bash homepanel -c "/opt/homepanel/.venv/bin/pip install -q -r requirements.txt"
systemctl restart homepanel
echo "$(date -Iseconds) restarted homepanel at $REMOTE"
