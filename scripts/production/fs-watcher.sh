#!/bin/bash
# S² MCP Bridge Filesystem Watcher
# Uses inotify to detect new messages immediately (no polling delay)
#
# Usage: ./fs-watcher.sh <conversation_id> <worker_token>
#
# Requirements: inotify-tools (Ubuntu) or fswatch (macOS)

DB_PATH="/tmp/claude_bridge_coordinator.db"
CONVERSATION_ID="${1:-}"
WORKER_TOKEN="${2:-}"
LOG_FILE="/tmp/mcp-fs-watcher.log"

if [ -z "$CONVERSATION_ID" ]; then
  echo "Usage: $0 <conversation_id> <worker_token>"
  exit 1
fi

# Check if inotify-tools is installed
if ! command -v inotifywait &> /dev/null; then
  echo "❌ inotify-tools not installed" | tee -a "$LOG_FILE"
  echo "💡 Install: sudo apt-get install -y inotify-tools" | tee -a "$LOG_FILE"
  exit 1
fi

if [ ! -f "$DB_PATH" ]; then
  echo "⚠️  Database not found: $DB_PATH" | tee -a "$LOG_FILE"
  echo "💡 Waiting for orchestrator to create conversations..." | tee -a "$LOG_FILE"
fi

echo "👁️  Starting filesystem watcher for: $CONVERSATION_ID" | tee -a "$LOG_FILE"
echo "📂 Watching database: $DB_PATH" | tee -a "$LOG_FILE"

# Find helper scripts
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CHECK_SCRIPT="$SCRIPT_DIR/check-messages.py"
KEEPALIVE_CLIENT="$SCRIPT_DIR/keepalive-client.py"

# Initial check
if [ -f "$DB_PATH" ]; then
  python3 "$CHECK_SCRIPT" \
    --conversation-id "$CONVERSATION_ID" \
    --token "$WORKER_TOKEN" \
    >> "$LOG_FILE" 2>&1
fi

# Watch for database modifications
inotifywait -m -e modify,close_write "$DB_PATH" 2>/dev/null | while read -r directory event filename; do
  TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')
  echo "[$TIMESTAMP] 📨 Database modified, checking for new messages..." | tee -a "$LOG_FILE"

  # Check for new messages immediately
  python3 "$CHECK_SCRIPT" \
    --conversation-id "$CONVERSATION_ID" \
    --token "$WORKER_TOKEN" \
    >> "$LOG_FILE" 2>&1

  # Update heartbeat
  python3 "$KEEPALIVE_CLIENT" \
    --conversation-id "$CONVERSATION_ID" \
    --token "$WORKER_TOKEN" \
    >> "$LOG_FILE" 2>&1
done
