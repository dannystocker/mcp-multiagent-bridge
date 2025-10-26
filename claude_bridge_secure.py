#!/usr/bin/env python3
"""
Secure Claude Code Multi-Agent Bridge
Production-lean MCP server with auth, redaction, and safety controls
"""

import asyncio
import json
import hmac
import hashlib
import secrets
import re
import sqlite3
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Optional
from contextlib import contextmanager

from mcp.server import Server
from mcp.types import Tool, TextContent

# Import YOLO mode (optional - only if yolo_mode.py is available)
try:
    from yolo_mode import YOLOMode, create_yolo_config
    YOLO_AVAILABLE = True
except ImportError:
    YOLO_AVAILABLE = False
    print("⚠️  YOLO mode not available (yolo_mode.py not found)", file=sys.stderr)

# Import rate limiter (critical security component)
try:
    from rate_limiter import RateLimiter
    RATE_LIMITER_AVAILABLE = True
except ImportError:
    RATE_LIMITER_AVAILABLE = False
    print("⚠️  Rate limiter not available (rate_limiter.py not found)", file=sys.stderr)


class SecretRedactor:
    """Redact sensitive data from messages"""
    
    PATTERNS = [
        (r'AKIA[0-9A-Z]{16}', 'AWS_KEY_REDACTED'),
        (r'-----BEGIN[^-]+PRIVATE KEY-----.*?-----END[^-]+PRIVATE KEY-----', 'PRIVATE_KEY_REDACTED'),
        (r'Bearer [A-Za-z0-9\-._~+/]+=*', 'BEARER_TOKEN_REDACTED'),
        (r'(?i)password["\s:=]+[^\s"]+', 'PASSWORD_REDACTED'),
        (r'(?i)api[_-]?key["\s:=]+[^\s"]+', 'API_KEY_REDACTED'),
        (r'(?i)secret["\s:=]+[^\s"]+', 'SECRET_REDACTED'),
        (r'ghp_[A-Za-z0-9]{36}', 'GITHUB_TOKEN_REDACTED'),
        (r'sk-[A-Za-z0-9]{48}', 'OPENAI_KEY_REDACTED'),
    ]
    
    @classmethod
    def redact(cls, text: str) -> str:
        """Redact secrets from text"""
        redacted = text
        for pattern, replacement in cls.PATTERNS:
            redacted = re.sub(pattern, replacement, redacted, flags=re.DOTALL)
        return redacted


class SecureBridge:
    """Secure message bridge with HMAC authentication"""
    
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.master_secret = secrets.token_bytes(32)  # Generate on startup

        # Initialize rate limiter (10 req/min, 100 req/hour, 500 req/day)
        if RATE_LIMITER_AVAILABLE:
            self.rate_limiter = RateLimiter(
                requests_per_minute=10,
                requests_per_hour=100,
                requests_per_day=500
            )
        else:
            self.rate_limiter = None

        self.init_db()
    
    def init_db(self):
        """Initialize SQLite schema"""
        with self._get_conn() as conn:
            c = conn.cursor()
            
            # Conversations with session tokens
            c.execute('''
                CREATE TABLE IF NOT EXISTS conversations (
                    id TEXT PRIMARY KEY,
                    session_a_role TEXT NOT NULL,
                    session_b_role TEXT NOT NULL,
                    session_a_token TEXT NOT NULL,
                    session_b_token TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    expires_at TEXT NOT NULL
                )
            ''')
            
            # Messages with atomic read tracking
            c.execute('''
                CREATE TABLE IF NOT EXISTS messages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    conversation_id TEXT NOT NULL,
                    from_session TEXT NOT NULL,
                    to_session TEXT NOT NULL,
                    message TEXT NOT NULL,
                    metadata TEXT,
                    timestamp TEXT NOT NULL,
                    read INTEGER DEFAULT 0,
                    FOREIGN KEY (conversation_id) REFERENCES conversations(id)
                )
            ''')
            
            # Session status
            c.execute('''
                CREATE TABLE IF NOT EXISTS session_status (
                    conversation_id TEXT NOT NULL,
                    session_id TEXT NOT NULL,
                    status TEXT NOT NULL,
                    last_heartbeat TEXT NOT NULL,
                    PRIMARY KEY (conversation_id, session_id)
                )
            ''')
            
            # Audit log
            c.execute('''
                CREATE TABLE IF NOT EXISTS audit_log (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    conversation_id TEXT,
                    session_id TEXT,
                    action TEXT NOT NULL,
                    details TEXT,
                    timestamp TEXT NOT NULL
                )
            ''')
            
            conn.commit()
    
    @contextmanager
    def _get_conn(self):
        """Thread-safe connection context manager"""
        conn = sqlite3.connect(self.db_path, timeout=10.0)
        conn.execute('PRAGMA journal_mode=WAL')  # Better concurrency
        try:
            yield conn
        finally:
            conn.close()
    
    def _generate_session_token(self, conv_id: str, session_id: str) -> str:
        """Generate HMAC token for session authentication"""
        data = f"{conv_id}:{session_id}:{datetime.utcnow().isoformat()}"
        return hmac.new(self.master_secret, data.encode(), hashlib.sha256).hexdigest()
    
    def _verify_token(self, conv_id: str, session_id: str, token: str) -> bool:
        """Verify session token"""
        with self._get_conn() as conn:
            c = conn.cursor()
            c.execute('''
                SELECT session_a_token, session_b_token, expires_at
                FROM conversations WHERE id = ?
            ''', (conv_id,))
            row = c.fetchone()
            
            if not row:
                return False
            
            # Check expiration
            expires_at = datetime.fromisoformat(row[2])
            if datetime.utcnow() > expires_at:
                return False
            
            # Verify token
            expected_token = row[0] if session_id == 'a' else row[1]
            return hmac.compare_digest(token, expected_token)
    
    def _audit_log(self, conv_id: Optional[str], session_id: Optional[str], 
                   action: str, details: dict):
        """Log action for audit trail"""
        with self._get_conn() as conn:
            c = conn.cursor()
            c.execute('''
                INSERT INTO audit_log (conversation_id, session_id, action, details, timestamp)
                VALUES (?, ?, ?, ?, ?)
            ''', (conv_id, session_id, action, json.dumps(details), datetime.utcnow().isoformat()))
            conn.commit()
    
    def create_conversation(self, session_a_role: str, session_b_role: str) -> dict:
        """Create new conversation with session tokens"""
        conv_id = f"conv_{secrets.token_hex(8)}"
        token_a = self._generate_session_token(conv_id, 'a')
        token_b = self._generate_session_token(conv_id, 'b')
        
        expires_at = datetime.utcnow() + timedelta(hours=3)
        
        with self._get_conn() as conn:
            c = conn.cursor()
            c.execute('''
                INSERT INTO conversations 
                (id, session_a_role, session_b_role, session_a_token, session_b_token, created_at, expires_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (conv_id, session_a_role, session_b_role, token_a, token_b, 
                  datetime.utcnow().isoformat(), expires_at.isoformat()))
            conn.commit()
        
        self._audit_log(conv_id, None, 'create_conversation', {
            'roles': [session_a_role, session_b_role]
        })
        
        return {
            'conversation_id': conv_id,
            'session_a_token': token_a,
            'session_b_token': token_b,
            'expires_at': expires_at.isoformat()
        }
    
    def send_message(self, conv_id: str, session_id: str, token: str,
                    message: str, metadata: dict = None) -> dict:
        """Send message with authentication and redaction"""

        # Check rate limit FIRST (before expensive operations)
        if self.rate_limiter:
            allowed, reason = self.rate_limiter.check_rate_limit(session_id)
            if not allowed:
                raise ValueError(f"Rate limit exceeded: {reason}")

        # Verify authentication
        if not self._verify_token(conv_id, session_id, token):
            raise PermissionError("Invalid session token")
        
        # Redact secrets
        redacted_message = SecretRedactor.redact(message)
        redacted_metadata = json.loads(SecretRedactor.redact(json.dumps(metadata or {})))
        
        to_session = 'b' if session_id == 'a' else 'a'
        
        # Atomic insert
        with self._get_conn() as conn:
            c = conn.cursor()
            c.execute('''
                INSERT INTO messages 
                (conversation_id, from_session, to_session, message, metadata, timestamp)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (conv_id, session_id, to_session, redacted_message, 
                  json.dumps(redacted_metadata), datetime.utcnow().isoformat()))
            conn.commit()
        
        self._audit_log(conv_id, session_id, 'send_message', {
            'to': to_session,
            'message_length': len(redacted_message),
            'redacted': message != redacted_message
        })
        
        return {'status': 'sent', 'redacted': message != redacted_message}
    
    def get_unread_messages(self, conv_id: str, session_id: str, token: str) -> list:
        """Get and mark messages as read atomically"""
        
        if not self._verify_token(conv_id, session_id, token):
            raise PermissionError("Invalid session token")
        
        with self._get_conn() as conn:
            c = conn.cursor()
            
            # Atomic read + mark
            c.execute('BEGIN IMMEDIATE')
            
            c.execute('''
                SELECT id, from_session, message, metadata, timestamp
                FROM messages
                WHERE conversation_id = ? AND to_session = ? AND read = 0
                ORDER BY timestamp ASC
            ''', (conv_id, session_id))
            
            messages = []
            message_ids = []
            
            for row in c.fetchall():
                messages.append({
                    'id': row[0],
                    'from': row[1],
                    'message': row[2],
                    'metadata': json.loads(row[3]) if row[3] else {},
                    'timestamp': row[4]
                })
                message_ids.append(row[0])
            
            # Mark as read
            if message_ids:
                placeholders = ','.join('?' * len(message_ids))
                c.execute(f'UPDATE messages SET read = 1 WHERE id IN ({placeholders})', message_ids)
            
            conn.commit()
        
        self._audit_log(conv_id, session_id, 'get_messages', {
            'count': len(messages)
        })
        
        return messages
    
    def update_status(self, conv_id: str, session_id: str, token: str, status: str):
        """Update session status with heartbeat"""
        
        if not self._verify_token(conv_id, session_id, token):
            raise PermissionError("Invalid session token")
        
        with self._get_conn() as conn:
            c = conn.cursor()
            c.execute('''
                INSERT OR REPLACE INTO session_status 
                (conversation_id, session_id, status, last_heartbeat)
                VALUES (?, ?, ?, ?)
            ''', (conv_id, session_id, status, datetime.utcnow().isoformat()))
            conn.commit()
    
    def get_partner_status(self, conv_id: str, session_id: str, token: str) -> dict:
        """Get partner session status"""
        
        if not self._verify_token(conv_id, session_id, token):
            raise PermissionError("Invalid session token")
        
        partner = 'b' if session_id == 'a' else 'a'
        
        with self._get_conn() as conn:
            c = conn.cursor()
            c.execute('''
                SELECT status, last_heartbeat
                FROM session_status
                WHERE conversation_id = ? AND session_id = ?
            ''', (conv_id, partner))
            
            row = c.fetchone()
            
            if row:
                heartbeat = datetime.fromisoformat(row[1])
                age = (datetime.utcnow() - heartbeat).total_seconds()
                return {
                    'status': row[0],
                    'last_heartbeat': row[1],
                    'age_seconds': int(age),
                    'alive': age < 120  # Consider alive if heartbeat within 2 min
                }
            
            return {'status': 'unknown', 'alive': False}


# MCP Server Setup
app = Server("claude-code-bridge-secure")
bridge = None  # Will be initialized with db_path
yolo = None    # Will be initialized if YOLO mode enabled


@app.list_tools()
async def list_tools() -> list[Tool]:
    """MCP tool definitions with strict schemas"""
    tools = [
        Tool(
            name="create_conversation",
            description="Initialize a new secure conversation. Returns tokens for both sessions.",
            inputSchema={
                "type": "object",
                "properties": {
                    "my_role": {
                        "type": "string",
                        "description": "Your role (e.g., 'backend_developer')",
                        "minLength": 3,
                        "maxLength": 100
                    },
                    "partner_role": {
                        "type": "string",
                        "description": "Partner's role (e.g., 'frontend_developer')",
                        "minLength": 3,
                        "maxLength": 100
                    }
                },
                "required": ["my_role", "partner_role"]
            }
        ),
        Tool(
            name="send_to_partner",
            description="Send a message to partner session (authenticated, redacted)",
            inputSchema={
                "type": "object",
                "properties": {
                    "conversation_id": {"type": "string", "pattern": "^conv_[a-f0-9]{16}$"},
                    "session_id": {"type": "string", "enum": ["a", "b"]},
                    "token": {"type": "string", "minLength": 64, "maxLength": 64},
                    "message": {"type": "string", "maxLength": 50000},
                    "action_type": {
                        "type": "string",
                        "enum": ["question", "info", "proposal", "blocked", "complete"]
                    },
                    "files_involved": {
                        "type": "array",
                        "items": {"type": "string"},
                        "maxItems": 20
                    }
                },
                "required": ["conversation_id", "session_id", "token", "message"]
            }
        ),
        Tool(
            name="check_messages",
            description="Check for new messages (atomic read + mark)",
            inputSchema={
                "type": "object",
                "properties": {
                    "conversation_id": {"type": "string", "pattern": "^conv_[a-f0-9]{16}$"},
                    "session_id": {"type": "string", "enum": ["a", "b"]},
                    "token": {"type": "string", "minLength": 64, "maxLength": 64}
                },
                "required": ["conversation_id", "session_id", "token"]
            }
        ),
        Tool(
            name="update_my_status",
            description="Update status with heartbeat",
            inputSchema={
                "type": "object",
                "properties": {
                    "conversation_id": {"type": "string", "pattern": "^conv_[a-f0-9]{16}$"},
                    "session_id": {"type": "string", "enum": ["a", "b"]},
                    "token": {"type": "string", "minLength": 64, "maxLength": 64},
                    "status": {
                        "type": "string",
                        "enum": ["working", "waiting", "blocked", "complete"]
                    }
                },
                "required": ["conversation_id", "session_id", "token", "status"]
            }
        ),
        Tool(
            name="check_partner_status",
            description="Get partner session status and liveness",
            inputSchema={
                "type": "object",
                "properties": {
                    "conversation_id": {"type": "string", "pattern": "^conv_[a-f0-9]{16}$"},
                    "session_id": {"type": "string", "enum": ["a", "b"]},
                    "token": {"type": "string", "minLength": 64, "maxLength": 64}
                },
                "required": ["conversation_id", "session_id", "token"]
            }
        )
    ]
    
    # Add YOLO mode tools if available
    if YOLO_AVAILABLE:
        tools.extend([
            Tool(
                name="enable_yolo_mode",
                description="⚠️  DANGEROUS: Enable command execution for this conversation. Use with extreme caution!",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "conversation_id": {"type": "string", "pattern": "^conv_[a-f0-9]{16}$"},
                        "session_id": {"type": "string", "enum": ["a", "b"]},
                        "token": {"type": "string", "minLength": 64, "maxLength": 64},
                        "mode": {
                            "type": "string",
                            "enum": ["safe", "restricted", "yolo"],
                            "description": "safe=read-only, restricted=git/npm/pip, yolo=most commands"
                        },
                        "workspace": {
                            "type": "string",
                            "description": "Working directory for command execution"
                        },
                        "timeout": {
                            "type": "integer",
                            "description": "Command timeout in seconds (default: 30)",
                            "default": 30
                        },
                        "sandbox": {
                            "type": "boolean",
                            "description": "Run in Docker sandbox (requires Docker)",
                            "default": False
                        }
                    },
                    "required": ["conversation_id", "session_id", "token", "mode"]
                }
            ),
            Tool(
                name="execute_command",
                description="Execute a command (requires YOLO mode enabled). Both agents will see the result.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "conversation_id": {"type": "string", "pattern": "^conv_[a-f0-9]{16}$"},
                        "session_id": {"type": "string", "enum": ["a", "b"]},
                        "token": {"type": "string", "minLength": 64, "maxLength": 64},
                        "command": {
                            "type": "string",
                            "description": "Shell command to execute",
                            "maxLength": 1000
                        }
                    },
                    "required": ["conversation_id", "session_id", "token", "command"]
                }
            )
        ])
    
    return tools


@app.call_tool()
async def call_tool(name: str, arguments: Any) -> list[TextContent]:
    """Handle tool calls with validation and error handling"""
    
    try:
        if name == "create_conversation":
            result = bridge.create_conversation(
                arguments["my_role"],
                arguments["partner_role"]
            )
            
            return [TextContent(
                type="text",
                text=f"""✅ Secure conversation created!

Conversation ID: {result['conversation_id']}

Your token (keep secret): {result['session_a_token']}
Partner token (share securely): {result['session_b_token']}

Expires: {result['expires_at']}

IMPORTANT: Tokens are required for all operations. Store your token securely.
Share the conversation ID and partner token with your partner session via a secure channel."""
            )]
        
        elif name == "send_to_partner":
            result = bridge.send_message(
                arguments["conversation_id"],
                arguments["session_id"],
                arguments["token"],
                arguments["message"],
                {
                    "action_type": arguments.get("action_type", "info"),
                    "files_involved": arguments.get("files_involved", [])
                }
            )
            
            redacted_notice = "\n⚠️  Secrets were redacted from your message" if result['redacted'] else ""
            
            return [TextContent(
                type="text",
                text=f"📤 Message sent to partner session{redacted_notice}"
            )]
        
        elif name == "check_messages":
            messages = bridge.get_unread_messages(
                arguments["conversation_id"],
                arguments["session_id"],
                arguments["token"]
            )
            
            if not messages:
                return [TextContent(type="text", text="📭 No new messages")]
            
            response = f"📬 {len(messages)} new message(s):\n\n"
            for msg in messages:
                response += f"From: Session {msg['from']}\n"
                response += f"Time: {msg['timestamp']}\n"
                if msg['metadata'].get('action_type'):
                    response += f"Type: {msg['metadata']['action_type']}\n"
                response += f"\nMessage:\n{msg['message']}\n"
                if msg['metadata'].get('files_involved'):
                    response += f"\nFiles: {', '.join(msg['metadata']['files_involved'])}\n"
                response += "\n" + "="*60 + "\n\n"
            
            return [TextContent(type="text", text=response)]
        
        elif name == "update_my_status":
            bridge.update_status(
                arguments["conversation_id"],
                arguments["session_id"],
                arguments["token"],
                arguments["status"]
            )
            return [TextContent(
                type="text",
                text=f"✅ Status updated: {arguments['status']}"
            )]
        
        elif name == "check_partner_status":
            status = bridge.get_partner_status(
                arguments["conversation_id"],
                arguments["session_id"],
                arguments["token"]
            )
            
            partner_id = "B" if arguments["session_id"] == "a" else "A"
            alive_indicator = "🟢" if status['alive'] else "🔴"
            
            return [TextContent(
                type="text",
                text=f"""{alive_indicator} Partner Session {partner_id}

Status: {status['status']}
Last heartbeat: {status.get('last_heartbeat', 'Never')}
Age: {status.get('age_seconds', 'N/A')}s
Alive: {status['alive']}"""
            )]
        
        # YOLO mode tools
        elif name == "enable_yolo_mode" and YOLO_AVAILABLE:
            global yolo
            if yolo is None:
                yolo = YOLOMode(bridge)
            
            config = yolo.set_mode(
                arguments["conversation_id"],
                arguments["mode"],
                workspace=arguments.get("workspace"),
                timeout=arguments.get("timeout", 30),
                sandbox=arguments.get("sandbox", False)
            )
            
            mode_warnings = {
                "safe": "✅ Safe mode: Read-only commands only",
                "restricted": "⚠️  Restricted mode: git, npm, pip commands allowed with validation",
                "yolo": "🔥 YOLO MODE: Most commands allowed! Use with extreme caution!"
            }
            
            return [TextContent(
                type="text",
                text=f"""{mode_warnings[config['mode']]}

Workspace: {config['workspace']}
Timeout: {config['timeout']}s
Sandbox: {'Enabled (Docker)' if config['sandbox'] else 'Disabled'}

Both agents can now execute commands using execute_command tool.
Results will be visible to both sessions."""
            )]
        
        elif name == "execute_command" and YOLO_AVAILABLE:
            if yolo is None:
                return [TextContent(
                    type="text",
                    text="❌ YOLO mode not initialized. Use enable_yolo_mode first."
                )]
            
            result = yolo.execute_command(
                arguments["conversation_id"],
                arguments["session_id"],
                arguments["token"],
                arguments["command"]
            )
            
            if result.get('blocked'):
                return [TextContent(
                    type="text",
                    text=f"""🚫 Command blocked

Command: {result['command']}
Reason: {result['reason']}"""
                )]
            
            if not result.get('success', False):
                return [TextContent(
                    type="text",
                    text=f"""❌ Command failed

{result.get('error', 'Unknown error')}"""
                )]
            
            snapshot_info = f"\n📸 Git snapshot: {result['snapshot']}" if result.get('snapshot') else ""
            
            return [TextContent(
                type="text",
                text=f"""✅ Command executed

Command: {result['command']}
Exit code: {result['exit_code']}
Duration: {result['duration']:.2f}s{snapshot_info}

STDOUT:
```
{result['stdout'][:2000]}{'...' if len(result['stdout']) > 2000 else ''}
```

STDERR:
```
{result['stderr'][:1000]}{'...' if len(result['stderr']) > 1000 else ''}
```

Note: Your partner can see this result via check_messages"""
            )]
        
        return [TextContent(type="text", text="❌ Unknown tool")]
    
    except PermissionError as e:
        return [TextContent(type="text", text=f"🔒 Authentication failed: {str(e)}")]
    except Exception as e:
        return [TextContent(type="text", text=f"❌ Error: {str(e)}")]


async def main(db_path: str = "/tmp/claude_bridge_secure.db"):
    """Run the secure MCP server"""
    global bridge
    bridge = SecureBridge(db_path)
    
    from mcp.server.stdio import stdio_server
    
    async with stdio_server() as (read_stream, write_stream):
        await app.run(
            read_stream,
            write_stream,
            app.create_initialization_options()
        )


if __name__ == "__main__":
    import sys
    db_path = sys.argv[1] if len(sys.argv) > 1 else "/tmp/claude_bridge_secure.db"
    print(f"Starting secure bridge with database: {db_path}", file=sys.stderr)
    asyncio.run(main(db_path))
