#!/bin/bash

set -euo pipefail

PROJECT_ROOT="/Users/zijian/Library/Mobile Documents/com~apple~CloudDocs/SCI/学术小龙虾-web"
BRANCH="main"
TIMESTAMP="$(date '+%Y-%m-%d %H:%M:%S')"

cd "$PROJECT_ROOT"

git pull --ff-only origin "$BRANCH"
python3 sync_from_source.py

if git diff --quiet -- '*.html'; then
  echo "[$TIMESTAMP] No generated HTML changes to publish."
  exit 0
fi

git add *.html
if git diff --cached --quiet; then
  echo "[$TIMESTAMP] No staged changes after sync."
  exit 0
fi

git commit -m "Auto sync latest source content"
git push origin "$BRANCH"
echo "[$TIMESTAMP] Sync finished and published."
