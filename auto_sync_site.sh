#!/bin/bash

# =============================================================================
# auto_sync_site.sh — sync jujutsu-sci HTML output to GitHub + academy mirror
# Exit codes: 0=success  1=sync failed  2=git push failed  3=academy mirror failed
# =============================================================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$SCRIPT_DIR"
BRANCH="main"
HOMEPAGE_REPO_URL="https://github.com/zijianxcode/personal-homepage.git"
HOMEPAGE_TMP="${TMPDIR:-/tmp}/personal-homepage-sync"
MODE="${1:-sync}"
TIMESTAMP="$(date '+%Y-%m-%d %H:%M:%S')"
HTML_FILES=()

# --- Per-command timeout (seconds) --------------------------------------------
GIT_TIMEOUT=60
PUSH_TIMEOUT=90

# --- Collect HTML files -------------------------------------------------------
while IFS= read -r html_file; do
  HTML_FILES+=("$html_file")
done < <(find "$PROJECT_ROOT" -maxdepth 1 -type f -name '*.html' -print | sed "s|$PROJECT_ROOT/||" | sort)

cd "$PROJECT_ROOT"

# --- Helpers ------------------------------------------------------------------

with_timeout() {
  # Run "$@" with SIGTERM after $GIT_TIMEOUT seconds
  # Returns 124 if timed out, otherwise the command's exit code
  timeout "$GIT_TIMEOUT" "$@" 2>/dev/null
}

with_push_timeout() {
  timeout "$PUSH_TIMEOUT" "$@" 2>/dev/null
}

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

verify_remote_has_commit() {
  # After a push, verify the remote actually has our commit by fetching and
  # comparing SHAs. Returns 0 on match, 1 on mismatch, 2 on fetch error.
  local repo_path="$1"
  local local_commit="$2"
  local remote_commit

  if ! git -C "$repo_path" fetch origin "$BRANCH" --quiet 2>/dev/null; then
    return 2
  fi

  remote_commit=$(git -C "$repo_path" rev-parse FETCH_HEAD 2>/dev/null) || return 2

  if [ "$local_commit" = "$remote_commit" ]; then
    return 0
  else
    return 1
  fi
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
  # Returns 0 if committed, 1 if nothing to commit, exits with 2 on error
  local repo_path="$1"
  local message="$2"
  shift 2
  local paths=("$@")

  if ! git -C "$repo_path" add -- "${paths[@]}"; then
    echo "[$TIMESTAMP] ERROR: git add failed for ${paths[*]}"
    exit 2
  fi

  if git -C "$repo_path" diff --cached --quiet; then
    # Nothing to commit — this is OK, return 1 (not an error)
    return 1
  fi

  if ! git -C "$repo_path" commit -m "$message"; then
    echo "[$TIMESTAMP] ERROR: git commit failed"
    exit 2
  fi
  return 0
}

sync_academy_mirror() {
  local local_commit=""
  local push_ok=false

  rm -rf "$HOMEPAGE_TMP"

  # Clone with timeout — never hang indefinitely
  if ! with_timeout git clone --bare "$HOMEPAGE_REPO_URL" "$HOMEPAGE_TMP" >/dev/null 2>&1; then
    echo "[$TIMESTAMP] academy clone timed out or failed (timeout=${GIT_TIMEOUT}s)"
    return 3
  fi

  ensure_repo_clean "$HOMEPAGE_TMP"

  # rsync content into academy/ subdir of the bare repo working tree
  local work_tree="${HOMEPAGE_TMP}-work"
  mkdir -p "$work_tree"
  GIT_WORK_TREE="$work_tree" git -C "$HOMEPAGE_TMP" checkout -f "$BRANCH" >/dev/null 2>&1 || true

  rsync -a --delete \
    --include='*.html' --include='*.css' --include='*.js' \
    --include='*.svg' --include='*.jpg' --include='*.png' --include='*.webp' \
    --include='vendor/' --include='vendor/**' \
    --exclude='*' \
    "$PROJECT_ROOT/" "$work_tree/academy/"

  cd "$work_tree"
  git add academy/
  if git diff --cached --quiet; then
    echo "[$TIMESTAMP] academy: no HTML changes to sync"
    cd "$PROJECT_ROOT"
    rm -rf "$HOMEPAGE_TMP" "$work_tree"
    return 0
  fi

  git commit -m "Auto sync academy content from academic source" || {
    echo "[$TIMESTAMP] academy: commit failed"
    cd "$PROJECT_ROOT"
    rm -rf "$HOMEPAGE_TMP" "$work_tree"
    return 3
  }

  local_commit=$(git rev-parse HEAD)
  cd "$PROJECT_ROOT"

  if with_push_timeout git -C "$HOMEPAGE_TMP" push origin "$BRANCH" 2>/dev/null; then
    # Push succeeded — verify remote has the commit
    if verify_remote_has_commit "$HOMEPAGE_TMP" "$local_commit"; then
      echo "[$TIMESTAMP] academy: pushed and verified (commit=$local_commit)"
      push_ok=true
    else
      echo "[$TIMESTAMP] academy: push returned success but remote commit mismatch — retry needed"
    fi
  else
    echo "[$TIMESTAMP] academy: push timed out or failed (timeout=${PUSH_TIMEOUT}s)"
  fi

  rm -rf "$HOMEPAGE_TMP" "$work_tree"

  if $push_ok; then
    return 0
  else
    return 3
  fi
}

# =============================================================================
# Main
# =============================================================================

ensure_repo_clean "$PROJECT_ROOT"

# Fetch with timeout and retry
if with_timeout git fetch origin "$BRANCH" 2>/dev/null; then
  if ! git pull --ff-only origin "$BRANCH" 2>/dev/null; then
    echo "[$TIMESTAMP] Warning: git pull failed (non-fast-forward or conflict) — continuing with local state"
  fi
else
  echo "[$TIMESTAMP] Warning: git fetch timed out — continuing with local state"
fi

# Generate HTML
if ! python3 sync_from_source.py; then
  echo "[$TIMESTAMP] ERROR: sync_from_source.py failed"
  exit 1
fi

ensure_only_html_changed "$PROJECT_ROOT"

CHANGED_FILES="$(git status --short -- "${HTML_FILES[@]}" || true)"
if [ -z "$CHANGED_FILES" ]; then
  echo "[$TIMESTAMP] Sync finished. No generated HTML changes detected."
  exit 0
fi

echo "[$TIMESTAMP] Detected generated HTML changes:"
printf '%s\n' "$CHANGED_FILES"

if [ "$MODE" = "check" ]; then
  echo "[$TIMESTAMP] Check mode — no commit or push performed."
  exit 0
fi

# --- Commit + push jujutsu-sci repo ----------------------------------------
local_commit=""
if commit_if_needed "$PROJECT_ROOT" "Auto sync latest source content" "${HTML_FILES[@]}"; then
  local_commit=$(git -C "$PROJECT_ROOT" rev-parse HEAD)
  echo "[$TIMESTAMP] jujutsu-sci: committed $local_commit"

  if with_push_timeout git -C "$PROJECT_ROOT" push origin "$BRANCH" 2>/dev/null; then
    if ! verify_remote_has_commit "$PROJECT_ROOT" "$local_commit"; then
      echo "[$TIMESTAMP] jujutsu-sci: push succeeded but remote verification failed — will retry"
      # Don't exit yet — let retry loop handle it
    else
      echo "[$TIMESTAMP] jujutsu-sci: pushed and verified (commit=$local_commit)"
    fi
  else
    echo "[$TIMESTAMP] jujutsu-sci: push timed out (timeout=${PUSH_TIMEOUT}s) — will retry"
  fi
else
  # Nothing to commit — this is OK, not an error
  echo "[$TIMESTAMP] jujutsu-sci: no changes to commit"
fi

# Retry push up to 3 times if verification failed or push failed
push_ok=false
if [ -n "$local_commit" ]; then
  for attempt in $(seq 1 3); do
    sleep 5
    if with_push_timeout git -C "$PROJECT_ROOT" push origin "$BRANCH" 2>/dev/null; then
      if verify_remote_has_commit "$PROJECT_ROOT" "$local_commit"; then
        echo "[$TIMESTAMP] jujutsu-sci: push verified on attempt $attempt"
        push_ok=true
        break
      else
        echo "[$TIMESTAMP] jujutsu-sci: push attempt $attempt succeeded but verification failed"
      fi
    else
      echo "[$TIMESTAMP] jujutsu-sci: push attempt $attempt timed out"
    fi
  done
fi

# --- Sync academy mirror -------------------------------------------------------
sync_academy_mirror
academy_status=$?

echo "[$TIMESTAMP] Done. jujutsu-sci push: $( $push_ok && echo "ok" || echo "FAILED" ), academy mirror: exit=$academy_status"

if ! $push_ok; then
  echo "[$TIMESTAMP] FAILURE: jujutsu-sci push did not reach remote after 3 attempts."
  exit 2
fi

if [ "$academy_status" -ne 0 ]; then
  echo "[$TIMESTAMP] FAILURE: academy mirror sync failed (exit=$academy_status)."
  exit 3
fi

exit 0
