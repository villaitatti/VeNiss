#!/bin/bash

# SPARQL Query Execution Script for Cron Job
# Executes populate.sparql against the VeNiss SPARQL endpoint every hour

# Set the base directory (relative to script location)
BASE_DIR="."
QUERY_FILE="$BASE_DIR/populate.sparql"
CREDENTIALS_FILE="$BASE_DIR/.env"
SPARQL_ENDPOINT="https://veniss.net/sparql"
LOG_FILE="$BASE_DIR/logs/sparql_cron.log"

# Create logs directory if it doesn't exist
mkdir -p "$BASE_DIR/logs"

# Function to log messages with timestamp
log_message() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" >> "$LOG_FILE"
}

# Check if credentials file exists
if [ ! -f "$CREDENTIALS_FILE" ]; then
    log_message "ERROR: Credentials file not found at $CREDENTIALS_FILE"
    exit 1
fi

# Source the credentials
source "$CREDENTIALS_FILE"

# Check if required variables are set
if [ -z "$SPARQL_USERNAME" ] || [ -z "$SPARQL_PASSWORD" ]; then
    log_message "ERROR: SPARQL_USERNAME or SPARQL_PASSWORD not set in credentials file"
    exit 1
fi

# Check if query file exists
if [ ! -f "$QUERY_FILE" ]; then
    log_message "ERROR: Query file not found at $QUERY_FILE"
    exit 1
fi

log_message "Starting SPARQL query execution"

# Execute the SPARQL query using curl
# This uses HTTP Basic Authentication and sends the query as SPARQL Update
response=$(curl -sS --fail-with-body -w "\n%{http_code}" \
    -X POST \
    -H "Content-Type: application/sparql-update" \
    -H "Accept: application/json" \
    -u "$SPARQL_USERNAME:$SPARQL_PASSWORD" \
    --data-binary "@$QUERY_FILE" \
    "$SPARQL_ENDPOINT" 2>&1) || {
    log_message "ERROR: curl failed: $response"
    exit 1
}

# Extract HTTP status code (last line)
http_code=$(echo "$response" | tail -n1)
# Extract response body (all but last line)
response_body=$(echo "$response" | head -n -1)

if [ "$http_code" -eq 200 ] || [ "$http_code" -eq 204 ]; then
    log_message "SUCCESS: SPARQL query executed successfully (HTTP $http_code)"
    if [ -n "$response_body" ]; then
        log_message "Response: $response_body"
    fi
else
    log_message "ERROR: SPARQL query failed with HTTP code $http_code"
    log_message "Response: $response_body"
    exit 1
fi

log_message "SPARQL query execution completed"