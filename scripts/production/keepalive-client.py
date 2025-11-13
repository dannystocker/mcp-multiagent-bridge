#!/usr/bin/env python3
"""Keep-alive client for MCP bridge - polls for messages and updates heartbeat"""

import sys
import json
import argparse
import sqlite3
from datetime import datetime
from pathlib import Path


def update_heartbeat(db_path: str, conversation_id: str, token: str) -> bool:
    """Update session heartbeat and check for new messages"""
    try:
        if not Path(db_path).exists():
            print(f"⚠️  Database not found: {db_path}", file=sys.stderr)
            print(f"💡 Tip: Orchestrator must create conversations first", file=sys.stderr)
            return False

        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row

        # Verify conversation exists
        cursor = conn.execute(
            "SELECT role_a, role_b FROM conversations WHERE id = ?",
            (conversation_id,)
        )
        conv = cursor.fetchone()

        if not conv:
            print(f"❌ Conversation {conversation_id} not found", file=sys.stderr)
            return False

        # Check for unread messages
        cursor = conn.execute(
            """SELECT COUNT(*) as unread FROM messages
               WHERE conversation_id = ? AND read_by_b = 0""",
            (conversation_id,)
        )
        unread_count = cursor.fetchone()['unread']

        # Update heartbeat (create session_status table if it doesn't exist)
        conn.execute(
            """CREATE TABLE IF NOT EXISTS session_status (
                conversation_id TEXT PRIMARY KEY,
                session_id TEXT NOT NULL,
                last_heartbeat TEXT NOT NULL,
                status TEXT DEFAULT 'active'
            )"""
        )

        conn.execute(
            """INSERT OR REPLACE INTO session_status
               (conversation_id, session_id, last_heartbeat, status)
               VALUES (?, 'session_b', ?, 'active')""",
            (conversation_id, datetime.utcnow().isoformat())
        )
        conn.commit()

        print(f"✅ Heartbeat updated | Unread messages: {unread_count}")

        if unread_count > 0:
            print(f"📨 {unread_count} new message(s) available - worker should check")

        conn.close()
        return True

    except sqlite3.OperationalError as e:
        print(f"❌ Database error: {e}", file=sys.stderr)
        return False
    except Exception as e:
        print(f"❌ Error: {e}", file=sys.stderr)
        return False


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="MCP Bridge Keep-Alive Client")
    parser.add_argument("--conversation-id", required=True, help="Conversation ID")
    parser.add_argument("--token", required=True, help="Worker token")
    parser.add_argument("--db-path", default="/tmp/claude_bridge_coordinator.db", help="Database path")

    args = parser.parse_args()

    success = update_heartbeat(args.db_path, args.conversation_id, args.token)
    sys.exit(0 if success else 1)
