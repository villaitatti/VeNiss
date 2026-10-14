#!/usr/bin/env bash
# Fast-forwards the live VeNiss checkout to origin/master and restarts
# ResearchSpace when config/ changed. Runs from the ubuntu crontab.
#
# This file is a reference copy. The crontab runs the installed copy in
# ~/bin, so a merged PR cannot change what executes on the host. After
# editing, reinstall by hand:
#   install -m 755 deploy/autopull/veniss-autopull.sh ~/bin/
#
# Usage:
#   veniss-autopull.sh                         check and deploy now
#   veniss-autopull.sh --if-triggered <file>   only if <file> exists (set by the webhook listener)

set -euo pipefail

REPO="${VENISS_REPO:-/home/ubuntu/veniss-app}"
REMOTE_URL="https://github.com/villaitatti/VeNiss.git"
CONTAINER="${VENISS_CONTAINER:-veniss-researchspace-1}"
STATE_DIR="${VENISS_AUTOPULL_DIR:-/home/ubuntu/veniss-autopull}"
LOG="$STATE_DIR/autopull.log"

log() { echo "$(date '+%Y-%m-%d %H:%M:%S') $*" >> "$LOG"; }

mkdir -p "$STATE_DIR"

if [ "${1:-}" = "--if-triggered" ]; then
    trigger="${2:?--if-triggered needs a file}"
    [ -e "$trigger" ] || exit 0
    rm -f "$trigger"
    log "webhook trigger received"
fi

exec 9> "$STATE_DIR/autopull.lock"
flock -n 9 || { log "another run is in progress, skipping"; exit 0; }

cd "$REPO"

branch=$(git symbolic-ref --short -q HEAD || echo "(detached)")
if [ "$branch" != "master" ]; then
    log "skip: checkout is on '$branch', not master"
    exit 0
fi
if [ -n "$(git status --porcelain)" ]; then
    log "skip: working tree has local changes"
    exit 0
fi

if ! git fetch -q "$REMOTE_URL" "+refs/heads/master:refs/remotes/origin/master" 2>> "$LOG"; then
    log "error: fetch failed"
    exit 1
fi

old=$(git rev-parse HEAD)
new=$(git rev-parse origin/master)
[ "$old" = "$new" ] && exit 0

changed=$(git diff --name-only "$old" "$new")
if ! git merge -q --ff-only "$new" 2>> "$LOG"; then
    log "error: cannot fast-forward ${old:0:7} to ${new:0:7} (diverged), fix by hand"
    exit 1
fi
log "updated ${old:0:7} -> ${new:0:7} ($(echo "$changed" | wc -l) files)"

if echo "$changed" | grep -q '^config/'; then
    log "config/ changed, restarting $CONTAINER"
    docker restart "$CONTAINER" > /dev/null 2>> "$LOG" || { log "error: restart failed"; exit 1; }
fi
