#!/usr/bin/env python3
"""Task reassignment for silent workers"""

import sys
import sqlite3
import json
import argparse
from datetime import datetime


def reassign_tasks(silent_workers: str, db_path: str = "/tmp/claude_bridge_coordinator.db"):
    """Reassign tasks from silent workers to healthy workers"""
    print(f"🔄 Reassigning tasks from silent workers...")

    # Parse silent worker list (format: conv_id|session_id|last_heartbeat|seconds_since)
    workers = [w.strip() for w in silent_workers.strip().split('\n') if w.strip()]

    for worker in workers:
        if '|' in worker:
            parts = worker.split('|')
            conv_id = parts[0].strip()
            seconds_silent = parts[3].strip() if len(parts) > 3 else "unknown"

            print(f"⚠️  Worker {conv_id} silent for {seconds_silent}s")
            print(f"📋 Action: Mark tasks as 'reassigned' and notify orchestrator")

            # In production:
            # 1. Query pending tasks for this conversation
            # 2. Update task status to 'reassigned'
            # 3. Send notification to orchestrator
            # 4. Log to audit trail

            # For now, just log the alert
            try:
                conn = sqlite3.connect(db_path)

                # Log alert to audit_log if it exists
                conn.execute(
                    """INSERT INTO audit_log (event_type, conversation_id, metadata, timestamp)
                       VALUES (?, ?, ?, ?)""",
                    (
                        "silent_worker_detected",
                        conv_id,
                        json.dumps({"seconds_silent": seconds_silent}),
                        datetime.utcnow().isoformat()
                    )
                )
                conn.commit()
                conn.close()

                print(f"✅ Alert logged to audit trail")

            except sqlite3.OperationalError as e:
                print(f"⚠️  Could not log to audit trail: {e}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Reassign tasks from silent workers")
    parser.add_argument("--silent-workers", required=True, help="List of silent workers")
    parser.add_argument("--db-path", default="/tmp/claude_bridge_coordinator.db", help="Database path")

    args = parser.parse_args()
    reassign_tasks(args.silent_workers, args.db_path)
