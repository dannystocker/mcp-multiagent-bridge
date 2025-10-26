#!/usr/bin/env python3
"""
CLI utility for managing Claude Code Bridge conversations
"""

import sqlite3
import sys
import json
from datetime import datetime
from pathlib import Path


class BridgeCLI:
    def __init__(self, db_path: str = "/tmp/claude_bridge_secure.db"):
        self.db_path = db_path
    
    def list_conversations(self):
        """List all active conversations"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        
        c.execute('''
            SELECT id, session_a_role, session_b_role, created_at, expires_at
            FROM conversations
            ORDER BY created_at DESC
        ''')
        
        print("\n📋 Active Conversations\n" + "="*80)
        
        for row in c.fetchall():
            conv_id, role_a, role_b, created, expires = row
            created_dt = datetime.fromisoformat(created)
            expires_dt = datetime.fromisoformat(expires)
            
            is_expired = datetime.utcnow() > expires_dt
            status_icon = "❌" if is_expired else "✅"
            
            print(f"\n{status_icon} {conv_id}")
            print(f"   Session A: {role_a}")
            print(f"   Session B: {role_b}")
            print(f"   Created: {created}")
            print(f"   Expires: {expires}")
        
        conn.close()
    
    def show_conversation(self, conv_id: str):
        """Show details and messages for a conversation"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        
        # Get conversation details
        c.execute('''
            SELECT session_a_role, session_b_role, created_at, expires_at
            FROM conversations WHERE id = ?
        ''', (conv_id,))
        
        row = c.fetchone()
        if not row:
            print(f"❌ Conversation {conv_id} not found")
            conn.close()
            return
        
        role_a, role_b, created, expires = row
        
        print(f"\n📝 Conversation: {conv_id}\n" + "="*80)
        print(f"Session A: {role_a}")
        print(f"Session B: {role_b}")
        print(f"Created: {created}")
        print(f"Expires: {expires}")
        
        # Get messages
        c.execute('''
            SELECT from_session, to_session, message, timestamp, read
            FROM messages
            WHERE conversation_id = ?
            ORDER BY timestamp ASC
        ''', (conv_id,))
        
        messages = c.fetchall()
        
        if messages:
            print(f"\n💬 Messages ({len(messages)}):\n")
            for msg in messages:
                from_s, to_s, text, ts, is_read = msg
                read_icon = "✓" if is_read else "○"
                print(f"{read_icon} {ts} | {from_s} → {to_s}")
                print(f"   {text[:100]}..." if len(text) > 100 else f"   {text}")
                print()
        else:
            print("\n📭 No messages yet")
        
        conn.close()
    
    def get_tokens(self, conv_id: str):
        """Retrieve tokens for a conversation (use carefully!)"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        
        c.execute('''
            SELECT session_a_token, session_b_token
            FROM conversations WHERE id = ?
        ''', (conv_id,))
        
        row = c.fetchone()
        conn.close()
        
        if not row:
            print(f"❌ Conversation {conv_id} not found")
            return
        
        print(f"\n🔑 Tokens for {conv_id}\n" + "="*80)
        print(f"Session A token: {row[0]}")
        print(f"Session B token: {row[1]}")
        print("\n⚠️  Keep these tokens secret! Anyone with a token can send messages.")
    
    def audit_log(self, conv_id: str = None, limit: int = 50):
        """Show audit log"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        
        if conv_id:
            c.execute('''
                SELECT timestamp, session_id, action, details
                FROM audit_log
                WHERE conversation_id = ?
                ORDER BY timestamp DESC
                LIMIT ?
            ''', (conv_id, limit))
        else:
            c.execute('''
                SELECT timestamp, conversation_id, session_id, action, details
                FROM audit_log
                ORDER BY timestamp DESC
                LIMIT ?
            ''', (limit,))
        
        print(f"\n📊 Audit Log (last {limit} entries)\n" + "="*80)
        
        for row in c.fetchall():
            if conv_id:
                ts, session, action, details = row
                print(f"{ts} | Session {session or 'N/A'} | {action}")
            else:
                ts, cid, session, action, details = row
                print(f"{ts} | {cid} | Session {session or 'N/A'} | {action}")
            
            if details:
                details_obj = json.loads(details)
                print(f"   {json.dumps(details_obj, indent=2)}")
        
        conn.close()
    
    def cleanup_expired(self):
        """Remove expired conversations"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        
        # Find expired
        c.execute('''
            SELECT id FROM conversations
            WHERE datetime(expires_at) < datetime('now')
        ''')
        
        expired = [row[0] for row in c.fetchall()]
        
        if not expired:
            print("✅ No expired conversations to clean up")
            conn.close()
            return
        
        print(f"🗑️  Removing {len(expired)} expired conversation(s)")
        
        for conv_id in expired:
            # Delete messages
            c.execute('DELETE FROM messages WHERE conversation_id = ?', (conv_id,))
            # Delete status
            c.execute('DELETE FROM session_status WHERE conversation_id = ?', (conv_id,))
            # Delete conversation
            c.execute('DELETE FROM conversations WHERE id = ?', (conv_id,))
            print(f"   Removed {conv_id}")
        
        conn.commit()
        conn.close()
        
        print("✅ Cleanup complete")


def main():
    if len(sys.argv) < 2:
        print("""
Claude Code Bridge CLI

Usage:
  python3 bridge_cli.py list                    - List all conversations
  python3 bridge_cli.py show <conv_id>          - Show conversation details
  python3 bridge_cli.py tokens <conv_id>        - Get tokens (sensitive!)
  python3 bridge_cli.py audit [conv_id] [limit] - Show audit log
  python3 bridge_cli.py cleanup                 - Remove expired conversations
        """)
        sys.exit(1)
    
    cli = BridgeCLI()
    command = sys.argv[1]
    
    if command == "list":
        cli.list_conversations()
    elif command == "show" and len(sys.argv) >= 3:
        cli.show_conversation(sys.argv[2])
    elif command == "tokens" and len(sys.argv) >= 3:
        cli.get_tokens(sys.argv[2])
    elif command == "audit":
        conv_id = sys.argv[2] if len(sys.argv) >= 3 else None
        limit = int(sys.argv[3]) if len(sys.argv) >= 4 else 50
        cli.audit_log(conv_id, limit)
    elif command == "cleanup":
        cli.cleanup_expired()
    else:
        print("❌ Unknown command. Run without arguments for help.")
        sys.exit(1)


if __name__ == "__main__":
    main()
