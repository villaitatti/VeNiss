#!/bin/bash
set -Eeuo pipefail
PATH="/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin"

# Resolve BASE_DIR to the directory this script lives in
SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
BASE_DIR="$SCRIPT_DIR"

QUERY_FILE="$BASE_DIR/populate.sparql"
CREDENTIALS_FILE="$BASE_DIR/.env"
LOG_DIR="$BASE_DIR/logs"
LOG_FILE="$LOG_DIR/sparql_cron.log"

# ==== PICK YOUR ENDPOINT ====
# GraphDB example (replace repo name):
# SPARQL_ENDPOINT="https://veniss.net/repositories/veniss-app/statements"
# Fuseki example:
# SPARQL_ENDPOINT="https://veniss.net/update"
SPARQL_ENDPOINT="https://veniss.net/sparql"
# ============================

mkdir -p "$LOG_DIR"

log_message() { echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" >> "$LOG_FILE"; }

[ -f "$CREDENTIALS_FILE" ] || { log_message "ERROR: Missing $CREDENTIALS_FILE"; exit 1; }
# shellcheck disable=SC1090
source "$CREDENTIALS_FILE"

: "${SPARQL_USERNAME:?}"; : "${SPARQL_PASSWORD:?}"

[ -f "$QUERY_FILE" ] || { log_message "ERROR: Missing query $QUERY_FILE"; exit 1; }

log_message "Starting SPARQL update → $SPARQL_ENDPOINT"

response=$(curl -sS --fail-with-body -w "\n%{http_code}" \
  -X POST \
  -H "Content-Type: application/sparql-update" \
  -u "$SPARQL_USERNAME:$SPARQL_PASSWORD" \
  --data-binary "@$QUERY_FILE" \
  "$SPARQL_ENDPOINT" 2>&1) || { log_message "ERROR: curl failed: $response"; exit 1; }

http_code=$(echo "$response" | tail -n1)
response_body=$(echo "$response" | head -n -1)

if [ "$http_code" -eq 200 ] || [ "$http_code" -eq 204 ]; then
  log_message "SUCCESS: HTTP $http_code"
  [ -n "$response_body" ] && log_message "Response: $response_body"
else
  log_message "ERROR: HTTP $http_code"
  log_message "Response: $response_body"
  exit 1
fi

log_message "Finished SPARQL update"
