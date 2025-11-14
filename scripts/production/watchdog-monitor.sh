#!/bin/bash
# S² MCP Bridge External Watchdog
# Monitors all workers for heartbeat freshness, triggers alerts on silent agents
#
# Usage: ./watchdog-monitor.sh

DB_PATH="/tmp/claude_bridge_coordinator.db"
CHECK_INTERVAL=60  # Check every 60 seconds
TIMEOUT_THRESHOLD=300  # Alert if no heartbeat for 5 minutes
LOG_FILE="/tmp/mcp-watchdog.log"

if [ ! -f "$DB_PATH" ]; then
  echo "❌ Database not found: $DB_PATH" | tee -a "$LOG_FILE"
  echo "💡 Tip: Orchestrator must create conversations first" | tee -a "$LOG_FILE"
  exit 1
fi

echo "🐕 Starting S² MCP Bridge Watchdog" | tee -a "$LOG_FILE"
echo "📊 Monitoring database: $DB_PATH" | tee -a "$LOG_FILE"
echo "⏱️  Check interval: ${CHECK_INTERVAL}s | Timeout threshold: ${TIMEOUT_THRESHOLD}s" | tee -a "$LOG_FILE"

# Find reassignment script
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REASSIGN_SCRIPT="$SCRIPT_DIR/reassign-tasks.py"

while true; do
  TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')

  # Query all worker heartbeats
  SILENT_WORKERS=$(sqlite3 "$DB_PATH" <<EOF
SELECT
  conversation_id,
  session_id,
  last_heartbeat,
  CAST((julianday('now') - julianday(last_heartbeat)) * 86400 AS INTEGER) as seconds_since
FROM session_status
WHERE seconds_since > $TIMEOUT_THRESHOLD
ORDER BY seconds_since DESC;
EOF
)

  if [ -n "$SILENT_WORKERS" ]; then
    echo "[$TIMESTAMP] 🚨 ALERT: Silent workers detected!" | tee -a "$LOG_FILE"
    echo "$SILENT_WORKERS" | tee -a "$LOG_FILE"

    # Trigger reassignment protocol
    if [ -f "$REASSIGN_SCRIPT" ]; then
      echo "[$TIMESTAMP] 🔄 Triggering task reassignment..." | tee -a "$LOG_FILE"
      python3 "$REASSIGN_SCRIPT" --silent-workers "$SILENT_WORKERS" 2>&1 | tee -a "$LOG_FILE"
    else
      echo "[$TIMESTAMP] ⚠️  Reassignment script not found: $REASSIGN_SCRIPT" | tee -a "$LOG_FILE"
    fi
  else
    echo "[$TIMESTAMP] ✅ All workers healthy" >> "$LOG_FILE"
  fi

  sleep $CHECK_INTERVAL
done
