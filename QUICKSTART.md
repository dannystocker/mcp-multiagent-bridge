# Claude Code Multi-Agent Bridge - Complete Package

Production-ready MCP server enabling secure collaboration between two Claude Code sessions, with optional command execution (YOLO mode).

## 📦 Package Contents

```
.
├── claude_bridge_secure.py    # Main MCP bridge server (secure, production-ready)
├── yolo_mode.py                # Command execution extension (use with caution)
├── bridge_cli.py               # Management CLI tool
├── test_bridge.py              # Test suite
├── README.md                   # Main documentation
├── YOLO_MODE.md               # YOLO mode detailed docs
├── EXAMPLE_WORKFLOW.md        # Real-world usage example
└── QUICKSTART.md              # This file
```

## 🚀 Quick Start (3 Steps)

### 1. Install

```bash
pip install mcp
chmod +x *.py
```

### 2. Configure

Add to `~/.claude.json`:

```json
{
  "mcpServers": {
    "bridge": {
      "command": "python3",
      "args": ["/absolute/path/to/claude_bridge_secure.py"]
    }
  }
}
```

### 3. Run

**Terminal 1 - Session A:**
```bash
claude-code

# In Claude Code:
"Use create_conversation tool with my_role='backend' and partner_role='frontend'"
```

**Terminal 2 - Session B:**
```bash
claude-code

# In Claude Code:
"Use check_messages with conversation_id and token from Session A"
```

Done! Your agents are now chatting.

## 🎯 Use Cases & Modes

| Use Case | Mode | Risk | Tools Needed |
|----------|------|------|--------------|
| **Code review** | Safe (no exec) | 🟢 None | Messages only |
| **API design** | Safe (no exec) | 🟢 None | Messages only |
| **Development** | Safe + execution | 🟡 Low | `yolo_mode.py` |
| **CI/CD workflows** | Restricted exec | 🟠 Medium | `yolo_mode.py` |
| **Full automation** | YOLO exec | 🔴 High | `yolo_mode.py` + isolation |

## 📖 Documentation Guide

### For Getting Started
→ Read `README.md` (main concepts, tools, setup)

### For Command Execution
→ Read `YOLO_MODE.md` (safety levels, examples, risks)

### For Real Examples
→ Read `EXAMPLE_WORKFLOW.md` (full FastAPI + React workflow)

### For Reference
→ This file (quick commands, troubleshooting)

## 🔧 Essential Commands

### Bridge Management

```bash
# List conversations
python3 bridge_cli.py list

# Show conversation details
python3 bridge_cli.py show conv_a1b2c3d4

# Get tokens (careful!)
python3 bridge_cli.py tokens conv_a1b2c3d4

# View audit log
python3 bridge_cli.py audit conv_a1b2c3d4

# Cleanup expired
python3 bridge_cli.py cleanup
```

### Testing

```bash
# Run test suite
python3 test_bridge.py

# Test specific feature
python3 -c "from test_bridge import test_authentication; test_authentication()"

# Validate YOLO mode
python3 yolo_mode.py
```

## 🛠️ Tool Reference

### Safe Mode Tools (Always Available)

| Tool | Purpose | Auth Required |
|------|---------|---------------|
| `create_conversation` | Start new session | No |
| `send_to_partner` | Send message | Yes (token) |
| `check_messages` | Receive messages | Yes (token) |
| `update_my_status` | Set status | Yes (token) |
| `check_partner_status` | See partner | Yes (token) |

### YOLO Mode Tools (Requires yolo_mode.py)

| Tool | Purpose | Risk |
|------|---------|------|
| `enable_yolo_mode` | Enable execution | 🟡 Setup |
| `execute_command` | Run commands | 🔴 High |

## ⚙️ Configuration Options

### Conversation Creation

```python
create_conversation(
    my_role="backend_developer",      # Your role
    partner_role="frontend_developer"  # Partner's role
)
# Returns: conversation_id, session_a_token, session_b_token
```

### YOLO Mode Setup

```python
enable_yolo_mode(
    conversation_id="conv_...",
    session_id="a",
    token="your-token",
    mode="restricted",          # safe | restricted | yolo
    workspace="/path/to/work",  # Working directory
    timeout=60,                 # Command timeout (seconds)
    sandbox=False               # Docker isolation
)
```

### Command Execution Modes

```python
# Safe: Read-only (ls, cat, grep, find)
mode="safe"

# Restricted: Safe + git/npm/pip with validation
mode="restricted"

# YOLO: Most commands (except rm -rf /, sudo, etc.)
mode="yolo"
```

## 🔒 Security Checklist

Before using in production:

- [ ] Run as non-root user
- [ ] Enable Docker sandboxing
- [ ] Use restricted or safe mode only
- [ ] Isolate workspace directories
- [ ] Review audit logs regularly
- [ ] Set appropriate timeouts
- [ ] Test on non-production data first
- [ ] Have backups ready
- [ ] Monitor resource usage
- [ ] Use separate Git branches per session

## 🐛 Troubleshooting Guide

### "MCP server not found"

```bash
# 1. Verify config path
cat ~/.claude.json

# 2. Check absolute path
ls -l /path/to/claude_bridge_secure.py

# 3. Test server directly
python3 claude_bridge_secure.py /tmp/test.db

# 4. Restart Claude Code
```

### "Invalid session token"

```bash
# Check if token expired (3 hours)
python3 bridge_cli.py show conv_...

# Get fresh tokens
python3 bridge_cli.py tokens conv_...

# Create new conversation if expired
```

### "YOLO mode not available"

```bash
# 1. Verify yolo_mode.py exists
ls -l yolo_mode.py

# 2. Check same directory as bridge
ls -l claude_bridge_secure.py yolo_mode.py

# 3. Test import
python3 -c "from yolo_mode import YOLOMode; print('OK')"
```

### "Command blocked"

```bash
# 1. Check audit log for reason
python3 bridge_cli.py audit conv_... | grep blocked

# 2. Try safe mode first
enable_yolo_mode(mode="safe")

# 3. Review blocked patterns
python3 -c "from yolo_mode import CommandValidator; print(CommandValidator.BLOCKED_PATTERNS)"
```

### "Messages not syncing"

```bash
# 1. Verify same conversation ID
python3 bridge_cli.py show conv_...

# 2. Check heartbeat
check_partner_status()

# 3. Verify tokens match conversation
python3 bridge_cli.py tokens conv_...

# 4. Check for network issues (if remote)
# 5. Review audit log for errors
```

## 📊 Performance Tips

### Reduce Token Usage
- Use `action_type` to categorize messages
- Truncate large outputs before sending
- Summarize instead of forwarding full command output
- Use status updates instead of frequent messages

### Optimize Command Execution
- Set realistic timeouts
- Use background jobs for long tasks
- Cache expensive operations
- Batch related commands

### Scale to Multiple Conversations
- Cleanup expired conversations regularly
- Use separate database per project
- Monitor disk usage for audit logs
- Consider Redis for high-frequency messaging

## 🎓 Learning Path

### Beginner: Message-Only Mode
1. Read `README.md`
2. Set up basic bridge
3. Try the code review use case
4. Practice with `EXAMPLE_WORKFLOW.md` (skip YOLO parts)

### Intermediate: Safe Command Execution
1. Read `YOLO_MODE.md` (safe & restricted sections)
2. Enable safe mode
3. Try read-only exploration
4. Progress to restricted mode for git/npm

### Advanced: Full YOLO Mode
1. Read entire `YOLO_MODE.md`
2. Set up Docker sandboxing
3. Test in isolated VM
4. Implement custom validation rules
5. Build your own workflows

## 🔗 External Resources

### MCP Protocol
- [Official MCP Docs](https://docs.anthropic.com/claude/docs/claude-code/mcp)
- [MCP Servers Repository](https://github.com/modelcontextprotocol/servers)

### Claude Code
- [Claude Code Documentation](https://docs.anthropic.com/claude/docs/claude-code)
- [Claude API Reference](https://docs.anthropic.com/claude/reference)

### Related Projects
- [Zen MCP Server](https://github.com/BeehiveInnovations/zen-mcp-server) - Multi-model orchestration
- [Claude Code MCP](https://github.com/steipete/claude-code-mcp) - Run Claude Code from Cursor

## 💡 Pro Tips

1. **Start Small**: Begin with message-only mode, add execution later
2. **Git Everything**: Use Git for rollback capability
3. **Monitor Always**: Keep audit logs visible
4. **Separate Concerns**: Each session owns specific directories
5. **Review Proposals**: Have agents propose actions before executing
6. **Status Updates**: Update status every 30-60 seconds
7. **Heartbeat Check**: Verify partner alive before complex operations
8. **Timeout Awareness**: Set timeouts based on expected duration + buffer
9. **Sandbox by Default**: Enable Docker unless you have good reason not to
10. **Fail Fast**: Block unsafe patterns aggressively, unblock selectively

## 📝 Quick Reference Card

```bash
# Setup
pip install mcp
edit ~/.claude.json  # Add bridge config

# Start Session A
claude-code
> create_conversation(my_role="...", partner_role="...")
> enable_yolo_mode(mode="restricted")  # Optional

# Start Session B
claude-code
> check_messages()  # Get conv_id and token from A
> enable_yolo_mode(mode="restricted")  # Optional

# Communication
> send_to_partner(message="...")
> check_messages()  # Poll every 30s
> update_my_status(status="working")
> check_partner_status()

# Execution (if YOLO enabled)
> execute_command(command="pytest")

# Management
python3 bridge_cli.py list
python3 bridge_cli.py show conv_...
python3 bridge_cli.py audit conv_...
```

## 🎉 Success Metrics

You'll know it's working when:

✅ Both sessions can exchange messages reliably  
✅ Messages marked as read automatically  
✅ Status updates reflect in real-time  
✅ Commands execute successfully (if YOLO enabled)  
✅ Both agents see command results  
✅ Audit log shows all activity  
✅ No authentication errors  
✅ Conversations expire properly  
✅ Secrets are redacted automatically  

## 🆘 Get Help

1. **Check audit log**: `python3 bridge_cli.py audit`
2. **Review test output**: `python3 test_bridge.py`
3. **Verify setup**: Test without Claude Code first
4. **Simplify**: Remove YOLO mode, try messages only
5. **Isolate**: Test each component separately

## 📄 License

MIT License - Use responsibly, no warranty provided.

---

**Built with care. Use with caution. Debug with patience.** 🚀
