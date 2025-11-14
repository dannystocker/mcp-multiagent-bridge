#!/usr/bin/env python3
"""Check for new messages using MCP bridge"""

import sys
import sqlite3
import argparse
from datetime import datetime
from pathlib import Path


def check_messages(db_path: str, conversation_id: str, token: str):
    """Check for unread messages"""
    try:
        if not Path(db_path).exists():
            print(f"⚠️  Database not found: {db_path}", file=sys.stderr)
            return

        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row

        # Get unread messages
        cursor = conn.execute(
            """SELECT id, sender, content, action_type, created_at
               FROM messages
               WHERE conversation_id = ? AND read_by_b = 0
               ORDER BY created_at ASC""",
            (conversation_id,)
        )

        messages = cursor.fetchall()

        if messages:
            print(f"\n📨 {len(messages)} new message(s):")
            for msg in messages:
                print(f"  From: {msg['sender']}")
                print(f"  Type: {msg['action_type']}")
                print(f"  Time: {msg['created_at']}")
                content = msg['content'][:100]
                if len(msg['content']) > 100:
                    content += "..."
                print(f"  Content: {content}")
                print()

                # Mark as read
                conn.execute(
                    "UPDATE messages SET read_by_b = 1 WHERE id = ?",
                    (msg['id'],)
                )

            conn.commit()
            print(f"✅ {len(messages)} message(s) marked as read")
        else:
            print("📭 No new messages")

        conn.close()

    except sqlite3.OperationalError as e:
        print(f"❌ Database error: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Check for new MCP bridge messages")
    parser.add_argument("--conversation-id", required=True, help="Conversation ID")
    parser.add_argument("--token", required=True, help="Worker token")
    parser.add_argument("--db-path", default="/tmp/claude_bridge_coordinator.db", help="Database path")

    args = parser.parse_args()
    check_messages(args.db_path, args.conversation_id, args.token)
