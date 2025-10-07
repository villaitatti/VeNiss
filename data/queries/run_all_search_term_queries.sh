#!/bin/bash
set -Eeuo pipefail
PATH="/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin"

# Resolve BASE_DIR to the directory this script lives in
SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
BASE_DIR="$SCRIPT_DIR"

# Configuration
CREDENTIALS_FILE="$BASE_DIR/.env"
LOG_DIR="$BASE_DIR/logs"
LOG_FILE="$LOG_DIR/search_term_cron.log"

# ==== SPARQL ENDPOINT CONFIGURATION ====
# Default endpoint - can be overridden in .env file
DEFAULT_SPARQL_ENDPOINT="https://veniss.net/sparql"
# =======================================

# Create log directory
mkdir -p "$LOG_DIR"

# Logging function
log_message() { 
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

# Check for credentials file
if [ ! -f "$CREDENTIALS_FILE" ]; then
    log_message "ERROR: Missing credentials file $CREDENTIALS_FILE"
    log_message "Please create it based on the template in primary_source/location/.env.template"
    exit 1
fi

# Source credentials
# shellcheck disable=SC1090
source "$CREDENTIALS_FILE"

# Validate required credentials
: "${SPARQL_USERNAME:?ERROR: SPARQL_USERNAME not set in $CREDENTIALS_FILE}"
: "${SPARQL_PASSWORD:?ERROR: SPARQL_PASSWORD not set in $CREDENTIALS_FILE}"

# Use endpoint from .env if set, otherwise use default
SPARQL_ENDPOINT="${SPARQL_ENDPOINT:-$DEFAULT_SPARQL_ENDPOINT}"

log_message "========================================="
log_message "Starting batch execution of search_term.rq queries"
log_message "Endpoint: $SPARQL_ENDPOINT"
log_message "Base directory: $BASE_DIR"
log_message "========================================="

# Find all search_term.rq files
query_files=()
while IFS= read -r -d '' file; do
    query_files+=("$file")
done < <(find "$BASE_DIR" -name "search_term.rq" -type f -print0)

if [ ${#query_files[@]} -eq 0 ]; then
    log_message "WARNING: No search_term.rq files found in $BASE_DIR"
    exit 0
fi

log_message "Found ${#query_files[@]} search_term.rq files to execute:"
for file in "${query_files[@]}"; do
    relative_path="${file#$BASE_DIR/}"
    log_message "  - $relative_path"
done

# Execute each query
success_count=0
error_count=0

for query_file in "${query_files[@]}"; do
    relative_path="${query_file#$BASE_DIR/}"
    entity_type=$(dirname "$relative_path")
    
    log_message "-----------------------------------------"
    log_message "Executing: $relative_path (Entity: $entity_type)"
    
    if [ ! -f "$query_file" ]; then
        log_message "ERROR: Query file not found: $query_file"
        ((error_count++))
        continue
    fi
    
    # Execute the SPARQL update query
    response=$(curl -sS --fail-with-body -w "\n%{http_code}" \
        -X POST \
        -H "Content-Type: application/sparql-update" \
        -u "$SPARQL_USERNAME:$SPARQL_PASSWORD" \
        --data-binary "@$query_file" \
        "$SPARQL_ENDPOINT" 2>&1) || {
        log_message "ERROR: curl failed for $relative_path: $response"
        ((error_count++))
        continue
    }
    
    # Parse response
    http_code=$(echo "$response" | tail -n1)
    response_body=$(echo "$response" | head -n -1)
    
    if [ "$http_code" -eq 200 ] || [ "$http_code" -eq 204 ]; then
        log_message "SUCCESS: $relative_path - HTTP $http_code"
        [ -n "$response_body" ] && log_message "Response: $response_body"
        ((success_count++))
    else
        log_message "ERROR: $relative_path - HTTP $http_code"
        log_message "Response: $response_body"
        ((error_count++))
    fi
done

log_message "========================================="
log_message "Batch execution completed"
log_message "Successful queries: $success_count"
log_message "Failed queries: $error_count"
log_message "Total queries: ${#query_files[@]}"
log_message "========================================="

# Exit with error code if any queries failed
if [ $error_count -gt 0 ]; then
    log_message "WARNING: $error_count queries failed. Check the log for details."
    exit 1
else
    log_message "All queries executed successfully!"
    exit 0
fi