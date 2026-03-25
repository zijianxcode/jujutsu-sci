#!/bin/bash

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$SCRIPT_DIR"
BRANCH="main"
MODE="${1:-check}"
TIMESTAMP="$(date '+%Y-%m-%d %H:%M:%S')"
REMOTE_STATUS="not_checked"
SYNC_PATHS=('*.html' '*.css' '*.js' '*.svg' '*.jpg' '*.jpeg' '*.png')

cd "$PROJECT_ROOT"

retry_git_fetch() {
  local attempt
  for attempt in 1 2 3; do
    if git fetch origin "$BRANCH"; then
      REMOTE_STATUS="ok"
      return 0
    fi
    sleep 3
  done
  REMOTE_STATUS="unavailable"
  return 1
}

if ! retry_git_fetch; then
  echo "[$TIMESTAMP] Warning: failed to reach GitHub after 3 attempts. Continue with local source sync only."
fi

if [ "$REMOTE_STATUS" = "ok" ]; then
  if ! git pull --ff-only origin "$BRANCH"; then
    echo "[$TIMESTAMP] Warning: git pull failed. Continue with local source sync only."
    REMOTE_STATUS="pull_failed"
  fi
fi

python3 sync_from_source.py

CHANGED_FILES="$(git status --short -- "${SYNC_PATHS[@]}" || true)"
if [ -z "$CHANGED_FILES" ]; then
  echo "[$TIMESTAMP] Sync finished. No generated asset changes detected. Remote status: $REMOTE_STATUS."
  exit 0
fi

echo "[$TIMESTAMP] Detected generated asset changes:"
printf '%s\n' "$CHANGED_FILES"

if [ "$MODE" != "publish" ]; then
  echo "[$TIMESTAMP] Check mode only. No commit or push was performed."
  exit 0
fi

git add "${SYNC_PATHS[@]}"
if git diff --cached --quiet; then
  echo "[$TIMESTAMP] No staged changes after sync."
  exit 0
fi

git commit -m "Auto sync latest source content"
git push origin "$BRANCH"
echo "[$TIMESTAMP] Sync finished and published."
