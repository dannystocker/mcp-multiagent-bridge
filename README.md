# MCP Multiagent Bridge
### Secure, rate-limited coordination for multiple LLM agents
> *Because even AI agents need traffic lights.*

Multi-agent systems are already here: backend agents debugging frontend agents, compliance bots reviewing security agents, and specialized models coordinating prod deployments.
But nobody's built the safety layer that keeps them from trampling each other.

**MCP** is the protocol. **This** is the traffic control system.

---

## Why it exists

Multi-agent execution is both powerful and horrifying.
So this bridge adds layered safeguards:
- Environment gate (explicit opt-in)
- Typed confirmation phrase
- One-time validation codes
- Expiring approval tokens (because regret has a TTL)

> ⚠️ **Beta Software**: Built for development/testing environments with human supervision. See [Security Policy](SECURITY.md) before production use.

---

## Under the hood

**Security:**
- HMAC-SHA256 session authentication
- Automatic secret redaction (API keys, passwords, tokens)
- SQLite WAL mode for atomic operations
- Comprehensive audit trail (JSONL format)
- 3-hour conversation expiration

**YOLO Guard™ (4-stage confirmation):**
- Environment gate (`YOLO_MODE=1`)
- Interactive typed confirmation
- One-time validation codes
- Time-limited approval tokens (5-min TTL, single-use)
- Dry-run by default

**Rate Limiting:**
- Token bucket algorithm
- 10 requests/minute, 100/hour, 500/day
- Per-session tracking with automatic reset

---

## Paperwork

All the boring-but-necessary stuff is here:
- **[LICENSE](LICENSE)** - MIT (do what you want)
- **[SECURITY.md](SECURITY.md)** - Threat model + responsible disclosure
- **[CONTRIBUTING.md](CONTRIBUTING.md)** - How to help
- **Policy compliance** - Anthropic & OpenAI friendly

---

## Works with

Any MCP-compatible LLM:
- Claude (Code, Desktop, API)
- OpenAI models via MCP adapters
- Anthropic API models
- Future: Codex, GPT, custom models

Not tied to any specific backend. Build once, swap models freely.

## Installation

```bash
# Install dependencies
pip install mcp

# Make scripts executable
chmod +x claude_bridge_secure.py bridge_cli.py

# Test the bridge
python3 claude_bridge_secure.py --help
```

## Quick Start

### 1. Configure MCP Server

Add to `~/.claude.json`:

```json
{
  "mcpServers": {
    "bridge": {
      "command": "python3",
      "args": ["/absolute/path/to/claude_bridge_secure.py"],
      "env": {}
    }
  }
}
```

Or use project-scoped config in `.mcp.json` at your project root.

### 2. Start Session A (Backend Developer)

```bash
cd ~/projects/backend

claude-code --prompt "
You are Session A in a multi-agent collaboration.

Role: Backend API Developer

Instructions:
1. Use create_conversation tool with:
   - my_role: 'backend_developer'
   - partner_role: 'frontend_developer'
   
2. Save your conversation_id and token (keep token secret!)

3. Communicate using:
   - send_to_partner (to send messages)
   - check_messages (poll every 30 seconds)
   - update_my_status (keep partner informed)

4. IMPORTANT: Include your token in every tool call for authentication

Task: Design and implement REST API for a todo application.
Coordinate with Session B on API contract before implementing.

Poll for messages regularly with: check_messages
"
```

### 3. Start Session B (Frontend Developer)

```bash
cd ~/projects/frontend

claude-code --prompt "
You are Session B in a multi-agent collaboration.

Role: Frontend React Developer

Instructions:
1. Get conversation_id and your token from Session A
   (They should share these securely)

2. Check for messages from Session A:
   check_messages with conversation_id and your token

3. Reply using send_to_partner

4. Poll for new messages every 30 seconds

Task: Build React frontend for todo application.
Coordinate with Session A on API requirements before implementing.
"
```

## Tool Reference

### create_conversation

Initializes a secure conversation and returns tokens.

```json
{
  "my_role": "backend_developer",
  "partner_role": "frontend_developer"
}
```

**Returns:**
```json
{
  "conversation_id": "conv_a1b2c3d4e5f6g7h8",
  "session_a_token": "64-char-hex-token",
  "session_b_token": "64-char-hex-token",
  "expires_at": "2025-10-26T17:00:00Z"
}
```

### send_to_partner

Send authenticated, redacted message to partner.

```json
{
  "conversation_id": "conv_...",
  "session_id": "a",
  "token": "your-session-token",
  "message": "Proposed API endpoint: POST /todos",
  "action_type": "proposal",
  "files_involved": ["api/routes.py"]
}
```

### check_messages

Atomically read and mark messages as read.

```json
{
  "conversation_id": "conv_...",
  "session_id": "b",
  "token": "your-session-token"
}
```

### update_my_status

Heartbeat mechanism to show liveness.

```json
{
  "conversation_id": "conv_...",
  "session_id": "a",
  "token": "your-session-token",
  "status": "working"
}
```

Status values: `working`, `waiting`, `blocked`, `complete`

### check_partner_status

See if partner is alive and what they're doing.

```json
{
  "conversation_id": "conv_...",
  "session_id": "a",
  "token": "your-session-token"
}
```

## Management CLI

```bash
# List all conversations
python3 bridge_cli.py list

# Show conversation details and messages
python3 bridge_cli.py show conv_a1b2c3d4e5f6g7h8

# Get tokens (use carefully!)
python3 bridge_cli.py tokens conv_a1b2c3d4e5f6g7h8

# View audit log
python3 bridge_cli.py audit
python3 bridge_cli.py audit conv_a1b2c3d4e5f6g7h8 100

# Clean up expired conversations
python3 bridge_cli.py cleanup
```

## Secret Redaction

The bridge automatically redacts:

- AWS keys (AKIA...)
- Private keys (-----BEGIN...PRIVATE KEY-----)
- Bearer tokens
- API keys
- Passwords
- GitHub tokens (ghp_...)
- OpenAI keys (sk-...)

Redacted content is replaced with placeholders like `AWS_KEY_REDACTED`.

## Security Best Practices

### DO ✅

- Keep session tokens secret
- Use separate workspaces for each session
- Poll for messages regularly (every 30s)
- Update status frequently so partner knows you're alive
- Use `action_type` to clarify message intent
- Review redaction before sending sensitive info

### DON'T ❌

- Share tokens in chat messages
- Commit tokens to version control
- Use expired conversations
- Send unrestricted command execution requests
- Assume messages are end-to-end encrypted (local only)

## Architecture

```
Session A (claude-code)     Session B (claude-code)
     |                              |
     |--- MCP Tool Calls ---|      |
     |                      ↓      |
     |              Bridge Server  |
     |              (Python + SQLite)
     |                      ↓      |
     |--- Authenticated, ---|------|
          Redacted Messages
```

### Data Flow

1. Session A calls `create_conversation` → Gets conv_id + token_a + token_b
2. Session A shares conv_id + token_b with Session B
3. Session A calls `send_to_partner` → Message redacted → Stored in DB
4. Session B calls `check_messages` → Retrieves + marks read atomically
5. Session B replies via `send_to_partner`
6. Both sessions update status periodically

### Database Schema

- **conversations**: Conv ID, roles, tokens, expiration
- **messages**: From/to sessions, redacted content, read status
- **session_status**: Current status + heartbeat timestamp
- **audit_log**: All actions for forensics

## Limitations & Safeguards

- **No command execution**: Bridge only passes messages, never executes code
- **3-hour expiration**: Conversations auto-expire
- **50KB message limit**: Prevents token bloat
- **Interactive only**: Human must review all proposed actions
- **No file sharing**: Sessions must use shared workspace or Git
- **Local-only**: No network transport, Unix socket or stdio only

## Testing

```bash
# Basic connectivity test
python3 claude_bridge_secure.py /tmp/test.db &
BRIDGE_PID=$!

# Test tool calls (requires MCP client)
# ... test scenarios ...

kill $BRIDGE_PID
rm /tmp/test.db
```

## Troubleshooting

**"Invalid session token"**
- Check token hasn't expired (3 hours)
- Verify you're using correct token for your session
- Use `bridge_cli.py tokens` to retrieve if lost

**"No MCP servers connected"**
- Verify `~/.claude.json` has correct absolute path
- Restart Claude Code after config changes
- Check MCP server logs: `claude-code --mcp-debug`

**Messages not appearing**
- Confirm both sessions use same conversation_id
- Check token authentication with `bridge_cli.py show`
- Verify partner sent messages (check audit log)

**Redaction too aggressive**
- Review redaction patterns in `SecretRedactor.PATTERNS`
- Consider adding custom patterns if needed
- False positives are safer than leaking secrets

## Use Cases

### 1. API-First Development
- Session A: Backend - designs API, implements endpoints
- Session B: Frontend - consumes API, provides feedback
- **Benefit**: Contract-first design with real-time feedback

### 2. Security Review
- Session A: Feature developer - implements functionality
- Session B: Security auditor - reviews for vulnerabilities
- **Benefit**: Continuous security assessment

### 3. Specialized Expertise
- Session A: Python expert - backend services
- Session B: TypeScript expert - React frontend
- **Benefit**: Each operates in domain of strength

### 4. Parallel Problem-Solving
- Session A: Investigates bug in module X
- Session B: Implements workaround in module Y
- **Benefit**: Non-blocking progress on related tasks

## Advanced Configuration

### Custom Database Location

```bash
python3 claude_bridge_secure.py /path/to/custom.db
```

### Adjust Expiration Time

Edit `create_conversation` method:
```python
expires_at = datetime.utcnow() + timedelta(hours=6)  # 6 hours instead of 3
```

### Add Custom Redaction Patterns

Edit `SecretRedactor.PATTERNS`:
```python
PATTERNS = [
    # ... existing patterns ...
    (r'my_secret_format_[A-Z0-9]{10}', 'CUSTOM_SECRET_REDACTED'),
]
```

## Production Hardening (Future)

Current MVP is designed for local development. For production:

- [ ] Add TLS for network transport
- [ ] Implement rate limiting per session
- [ ] Add message size quotas
- [ ] Enable sandboxed command execution (Docker)
- [ ] Add Redis pub/sub for real-time notifications
- [ ] Implement message encryption at rest
- [ ] Add role-based access control
- [ ] Enable multi-conversation per session
- [ ] Add conversation export/import
- [ ] Implement backup/restore

## License

MIT - Use responsibly. Not liable for data loss or security issues.

## Credits

Inspired by Zen MCP Server's multi-model orchestration concepts.
Built for secure local multi-agent coordination without external dependencies.
