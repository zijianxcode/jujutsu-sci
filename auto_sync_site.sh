#!/bin/bash

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$SCRIPT_DIR"
BRANCH="main"
HOMEPAGE_REPO_URL="https://github.com/zijianxcode/personal-homepage.git"
HOMEPAGE_TMP="${TMPDIR:-/tmp}/personal-homepage-sync"
MODE="${1:-sync}"
TIMESTAMP="$(date '+%Y-%m-%d %H:%M:%S')"
REMOTE_STATUS="not_checked"
ACADEMY_REMOTE_STATUS="not_started"
ACADEMY_COMMIT_STATUS="not_started"

mapfile -t HTML_FILES < <(find "$PROJECT_ROOT" -maxdepth 1 -type f -name '*.html' -print | sed "s|$PROJECT_ROOT/||" | sort)

cd "$PROJECT_ROOT"

retry_command() {
  local attempt
  local max_attempts="$1"
  shift
  for attempt in $(seq 1 "$max_attempts"); do
    if "$@"; then
      return 0
    fi
    sleep 3
  done
  return 1
}

ensure_repo_clean() {
  local repo_path="$1"
  if ! git -C "$repo_path" diff --quiet || ! git -C "$repo_path" diff --cached --quiet || [ -n "$(git -C "$repo_path" ls-files --others --exclude-standard)" ]; then
    echo "[$TIMESTAMP] Abort: repository is not clean: $repo_path"
    git -C "$repo_path" status --short
    exit 1
  fi
}

ensure_only_html_changed() {
  local repo_path="$1"
  local status_output
  local non_html
  status_output="$(git -C "$repo_path" status --short || true)"
  if [ -z "$status_output" ]; then
    return 0
  fi
  non_html="$(printf '%s\n' "$status_output" | grep -vE '\.html"?$' || true)"
  if [ -n "$non_html" ]; then
    echo "[$TIMESTAMP] Abort: automatic data sync detected non-HTML changes and stopped."
    printf '%s\n' "$non_html"
    exit 1
  fi
}

commit_if_needed() {
  local repo_path="$1"
  local message="$2"
  shift 2
  local paths=("$@")
  git -C "$repo_path" add -- "${paths[@]}"
  if git -C "$repo_path" diff --cached --quiet; then
    return 1
  fi
  git -C "$repo_path" commit -m "$message" >/dev/null
  return 0
}

sync_academy_mirror() {
  rm -rf "$HOMEPAGE_TMP"
  if ! retry_command 3 git clone "$HOMEPAGE_REPO_URL" "$HOMEPAGE_TMP" >/dev/null 2>&1; then
    ACADEMY_REMOTE_STATUS="clone_failed"
    return 1
  fi

  ACADEMY_REMOTE_STATUS="cloned"
  ensure_repo_clean "$HOMEPAGE_TMP"
  rsync -a --delete --include='*.html' --exclude='*' "$PROJECT_ROOT/" "$HOMEPAGE_TMP/academy/"

  if commit_if_needed "$HOMEPAGE_TMP" "Auto sync academy content from academic source" academy/*.html; then
    if retry_command 3 git -C "$HOMEPAGE_TMP" push origin "$BRANCH" >/dev/null 2>&1; then
      ACADEMY_REMOTE_STATUS="pushed"
      ACADEMY_COMMIT_STATUS="committed"
      return 0
    fi
    ACADEMY_REMOTE_STATUS="push_failed"
    return 1
  fi

  ACADEMY_REMOTE_STATUS="no_changes"
  ACADEMY_COMMIT_STATUS="no_changes"
  return 0
}

ensure_repo_clean "$PROJECT_ROOT"

if retry_command 3 git fetch origin "$BRANCH"; then
  REMOTE_STATUS="ok"
  if ! git pull --ff-only origin "$BRANCH"; then
    echo "[$TIMESTAMP] Warning: git pull failed. Continue with local source sync only."
    REMOTE_STATUS="pull_failed"
  fi
else
  REMOTE_STATUS="unavailable"
  echo "[$TIMESTAMP] Warning: failed to reach GitHub after 3 attempts. Continue with local source sync only."
fi

python3 sync_from_source.py

ensure_only_html_changed "$PROJECT_ROOT"

CHANGED_FILES="$(git status --short -- "${HTML_FILES[@]}" || true)"
if [ -z "$CHANGED_FILES" ]; then
  echo "[$TIMESTAMP] Sync finished. No generated HTML changes detected. Remote status: $REMOTE_STATUS."
  exit 0
fi

echo "[$TIMESTAMP] Detected generated HTML changes:"
printf '%s\n' "$CHANGED_FILES"

if [ "$MODE" = "check" ]; then
  echo "[$TIMESTAMP] Check mode only. No commit or push was performed."
  exit 0
fi

if [ "$REMOTE_STATUS" = "unavailable" ] || [ "$REMOTE_STATUS" = "pull_failed" ]; then
  echo "[$TIMESTAMP] Skip publish because GitHub remote is unavailable."
  exit 1
fi

if commit_if_needed "$PROJECT_ROOT" "Auto sync latest source content" "${HTML_FILES[@]}"; then
  if ! retry_command 3 git push origin "$BRANCH" >/dev/null 2>&1; then
    echo "[$TIMESTAMP] Failed to push academic site repo after 3 attempts."
    exit 1
  fi
else
  echo "[$TIMESTAMP] No staged changes after sync."
fi

if ! sync_academy_mirror; then
  echo "[$TIMESTAMP] Academic site repo was updated, but academy mirror sync failed. Academy status: $ACADEMY_REMOTE_STATUS."
  exit 1
fi

echo "[$TIMESTAMP] Sync finished and published. Academic remote: $REMOTE_STATUS. Academy status: $ACADEMY_REMOTE_STATUS."
