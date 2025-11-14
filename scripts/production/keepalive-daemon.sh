#!/bin/bash
# S² MCP Bridge Keep-Alive Daemon
# Polls for messages every 30 seconds to prevent idle session issues
#
# Usage: ./keepalive-daemon.sh <conversation_id> <worker_token>

CONVERSATION_ID="${1:-}"
WORKER_TOKEN="${2:-}"
POLL_INTERVAL=30
LOG_FILE="/tmp/mcp-keepalive.log"
DB_PATH="/tmp/claude_bridge_coordinator.db"

if [ -z "$CONVERSATION_ID" ] || [ -z "$WORKER_TOKEN" ]; then
  echo "Usage: $0 <conversation_id> <worker_token>"
  echo "Example: $0 conv_abc123 token_xyz456"
  exit 1
fi

echo "🔄 Starting keep-alive daemon for conversation: $CONVERSATION_ID" | tee -a "$LOG_FILE"
echo "📋 Polling interval: ${POLL_INTERVAL}s" | tee -a "$LOG_FILE"
echo "💾 Database: $DB_PATH" | tee -a "$LOG_FILE"

# Find the keepalive client script
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CLIENT_SCRIPT="$SCRIPT_DIR/keepalive-client.py"

if [ ! -f "$CLIENT_SCRIPT" ]; then
  echo "❌ Error: keepalive-client.py not found at $CLIENT_SCRIPT" | tee -a "$LOG_FILE"
  exit 1
fi

while true; do
  TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')

  # Poll for new messages and update heartbeat
  python3 "$CLIENT_SCRIPT" \
    --conversation-id "$CONVERSATION_ID" \
    --token "$WORKER_TOKEN" \
    --db-path "$DB_PATH" \
    >> "$LOG_FILE" 2>&1

  RESULT=$?

  if [ $RESULT -eq 0 ]; then
    echo "[$TIMESTAMP] ✅ Keep-alive successful" >> "$LOG_FILE"
  else
    echo "[$TIMESTAMP] ⚠️  Keep-alive failed (exit code: $RESULT)" >> "$LOG_FILE"
  fi

  sleep $POLL_INTERVAL
done
