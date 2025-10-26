# 🔥 YOLO Mode - Command Execution

⚠️  **WARNING: This enables AI agents to execute commands on your system!**

YOLO mode allows both Claude Code sessions to execute shell commands, with configurable safety levels.

## Security Levels

### 1. Safe Mode ✅
**What it allows:**
- Read-only commands: `ls`, `cat`, `grep`, `find`, `head`, `tail`, `wc`, `pwd`, `ps`, `df`
- Zero risk of data modification

**Use case:** Code exploration, log analysis, system inspection

```bash
# Example safe commands
ls -la
cat README.md
grep "TODO" src/**/*.py
find . -name "*.js"
ps aux | grep python
```

### 2. Restricted Mode ⚠️
**What it allows:**
- Everything in Safe mode, plus:
- Git operations: `status`, `log`, `diff`, `add`, `commit`, `push`, `pull`
- Package managers: `npm install`, `pip install`, `cargo build`
- Test runners: `pytest`, `npm test`

**What it blocks:**
- Destructive git operations (`reset --hard`, `clean -fdx`)
- System modifications
- Unrestricted shell access

**Use case:** Development workflow with version control

```bash
# Example restricted commands
git status
git add src/
git commit -m "Update API"
npm install lodash
pip install requests
pytest tests/
```

### 3. YOLO Mode 🔥
**What it allows:**
- Almost everything except obvious disasters
- File creation/modification
- System commands
- Custom scripts

**What it ALWAYS blocks:**
- `rm -rf /` (recursive delete from root)
- `sudo` / `su` (privilege escalation)
- Writing to block devices (`> /dev/sda`)
- Piping curl/wget to bash
- Fork bombs
- `eval` and dangerous redirects

**Use case:** Experienced users in isolated environments

```bash
# Example YOLO commands
python train.py --epochs 10
docker-compose up -d
./build.sh
npm run build
```

## Setup Instructions

### 1. Place YOLO module

Ensure `yolo_mode.py` is in the same directory as `claude_bridge_secure.py`.

### 2. Enable YOLO mode in conversation

**Session A (or B) calls:**
```json
{
  "tool": "enable_yolo_mode",
  "arguments": {
    "conversation_id": "conv_...",
    "session_id": "a",
    "token": "your-token",
    "mode": "restricted",
    "workspace": "/home/user/projects/myapp",
    "timeout": 60,
    "sandbox": false
  }
}
```

**Parameters:**
- `mode`: `"safe"` | `"restricted"` | `"yolo"`
- `workspace`: Directory where commands execute (default: current dir)
- `timeout`: Max execution time in seconds (default: 30)
- `sandbox`: Run in Docker container (default: false, requires Docker)

### 3. Execute commands

**Either session can execute:**
```json
{
  "tool": "execute_command",
  "arguments": {
    "conversation_id": "conv_...",
    "session_id": "a",
    "token": "your-token",
    "command": "npm test"
  }
}
```

**Both sessions will see the result!**

## Safety Features

### Automatic Git Snapshots
Before any command execution, YOLO mode creates a Git snapshot branch:
```
snapshot-20251026-143022
```

If something goes wrong, you can rollback:
```bash
git checkout snapshot-20251026-143022
```

### Command Validation
All commands go through multi-layer validation:

1. **Blocked patterns check** - Reject known dangerous patterns
2. **Mode-specific whitelist** - Only allow commands for current mode
3. **Argument validation** - Check subcommands for restricted commands
4. **Timeout enforcement** - Kill long-running processes

### Audit Trail
Every command execution is logged:
```bash
python3 bridge_cli.py audit conv_abc123
```

Shows:
- Who executed the command
- When it was executed
- Exit code and duration
- Whether it was blocked

### Output Broadcasting
When Session A executes a command, Session B automatically receives:
- The command that was run
- Exit code
- stdout/stderr (truncated to 1000 chars each)
- Execution duration
- Git snapshot reference (if created)

This keeps both agents in sync about system state changes.

## Docker Sandbox Mode

For maximum safety, enable Docker sandboxing:

```json
{
  "sandbox": true
}
```

Commands run in isolated containers with:
- ❌ No network access (`--network=none`)
- 📊 Memory limit: 512MB
- ⚙️  CPU limit: 1 core
- 📁 Read-only workspace mount
- ⏱️  Timeout enforcement

**Requires Docker installed and running.**

Example:
```bash
# Instead of:
python my_script.py

# Runs as:
docker run --rm -i \
  --network=none \
  --memory=512m \
  --cpus=1 \
  -v "/workspace:/workspace:ro" \
  -w /workspace \
  python:3.11-slim \
  sh -c 'python my_script.py'
```

## Usage Examples

### Example 1: API Development Workflow

**Session A (Backend):**
```bash
# Enable YOLO mode
enable_yolo_mode(mode="restricted", workspace="/home/user/api-project")

# Create new endpoint
execute_command("cat > api/endpoints/todos.py << EOF
from fastapi import APIRouter
router = APIRouter()

@router.get('/todos')
async def get_todos():
    return {'todos': []}
EOF")

# Run tests
execute_command("pytest tests/test_todos.py -v")

# Commit if tests pass
execute_command("git add api/endpoints/todos.py")
execute_command("git commit -m 'Add todos endpoint'")
```

**Session B (Frontend) sees all results and can:**
```bash
# Check what was committed
execute_command("git log -1 --stat")

# Test the endpoint
execute_command("curl http://localhost:8000/todos")
```

### Example 2: Debugging in Parallel

**Session A:**
```bash
# Enable safe mode for read-only exploration
enable_yolo_mode(mode="safe")

# Analyze logs
execute_command("grep ERROR app.log | tail -20")
execute_command("cat /var/log/app/error.log")
```

**Session B:**
```bash
# Enable restricted mode to fix the issue
enable_yolo_mode(mode="restricted")

# Apply fix
execute_command("git checkout -b fix/logging-error")
execute_command("sed -i 's/logger.error/logger.exception/g' src/logger.py")
execute_command("pytest tests/test_logger.py")
```

### Example 3: System Reconnaissance

**Both sessions in safe mode:**
```bash
enable_yolo_mode(mode="safe")

# Session A: Check system resources
execute_command("df -h")
execute_command("free -m")
execute_command("ps aux --sort=-%mem | head -10")

# Session B: Check application state
execute_command("ls -lah /var/www/app")
execute_command("cat /var/www/app/.env | grep -v SECRET")
execute_command("find /var/www/app -name '*.log' -mtime -1")
```

## Best Practices

### DO ✅

1. **Start with safe mode** - Escalate only when needed
2. **Use workspace isolation** - Set `workspace` to project directory
3. **Enable sandboxing** - Use Docker when possible
4. **Review commands** - Check what partner executed via `check_messages`
5. **Create snapshots manually** - `git stash` before risky operations
6. **Set appropriate timeouts** - Long-running tasks need higher values
7. **Use restricted mode for CI/CD** - Perfect for build/test workflows

### DON'T ❌

1. **Don't use YOLO mode on production servers** - Too risky
2. **Don't disable sandboxing for untrusted code** - Always sandbox third-party scripts
3. **Don't execute commands you don't understand** - Review partner's suggestions
4. **Don't ignore blocked commands** - If it's blocked, there's a reason
5. **Don't run as root** - Use regular user account
6. **Don't trust agent judgment blindly** - AI can make mistakes
7. **Don't disable audit logging** - You need forensics if things break

## Troubleshooting

### "YOLO mode not enabled for this conversation"

You need to call `enable_yolo_mode` first:
```bash
python3 bridge_cli.py show conv_abc123  # Verify conversation exists
```

Then in Claude Code session:
```
Use enable_yolo_mode tool with mode="safe"
```

### "Command blocked: Blocked dangerous pattern"

The command matched a blocked pattern. Review the command for:
- `sudo` or `su`
- `rm -rf /`
- Piping to shell (`| bash`, `| sh`)
- Eval statements

If you believe it's a false positive, modify `yolo_mode.py` `BLOCKED_PATTERNS`.

### "Command timed out after Xs"

Increase timeout when enabling YOLO mode:
```json
{
  "timeout": 300  // 5 minutes
}
```

### Docker sandbox errors

Verify Docker is running:
```bash
docker ps
```

If Docker unavailable, disable sandbox:
```json
{
  "sandbox": false
}
```

### Commands not in allowed list (restricted mode)

**Restricted mode is strict.** Either:
1. Add command to `RESTRICTED_COMMANDS` in `yolo_mode.py`
2. Switch to YOLO mode (less safe)
3. Execute manually and report results via `send_to_partner`

## Architecture

```
┌─────────────────────┐
│   Session A calls   │
│  execute_command    │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│  CommandValidator   │
│  - Check mode       │
│  - Check patterns   │
│  - Validate args    │
└──────────┬──────────┘
           │
           ▼ (if allowed)
┌─────────────────────┐
│  CommandExecutor    │
│  - Create snapshot  │
│  - Execute command  │
│  - Capture output   │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│   Broadcast result  │
│   to both sessions  │
└─────────────────────┘
```

## Extending YOLO Mode

### Add custom safe commands

Edit `yolo_mode.py`:
```python
SAFE_COMMANDS = {
    'ls', 'cat', 'grep', 'find',
    'myapp',  # Your custom read-only tool
}
```

### Add custom blocked patterns

```python
BLOCKED_PATTERNS = [
    r'\brm\s+-rf\s+/',
    r'curl.*evil\.com',  # Block specific domains
]
```

### Add restricted commands

```python
RESTRICTED_COMMANDS = {
    'myapp': ['read', 'analyze', 'report'],  # Only these subcommands
}
```

## Security Considerations

YOLO mode is designed for **development environments** with informed users who understand the risks.

**DO NOT use in:**
- Production servers
- Shared hosting environments  
- Systems with sensitive data
- Untrusted networks
- Multi-tenant environments

**Threat model:**
- **Prompt injection:** Agent could be tricked into executing malicious commands
- **Privilege escalation:** If running as root or with sudo access
- **Data exfiltration:** Commands could leak secrets via network
- **Resource exhaustion:** Malicious loops or fork bombs
- **Lateral movement:** Compromised agent could attack other systems

**Mitigations:**
1. Run in isolated VM or container
2. Use non-privileged user account
3. Enable Docker sandboxing
4. Set aggressive timeouts
5. Monitor audit logs
6. Use network firewalls
7. Limit to development data only

## License & Liability

MIT License - Use at your own risk.

**We are NOT responsible for:**
- Data loss
- System damage
- Security breaches
- Lost work
- Angry sysadmins

By using YOLO mode, you acknowledge:
1. You understand the risks
2. You have backups
3. You're using appropriate isolation
4. You accept full responsibility

---

**Remember:** With great power comes great responsibility. YOLO mode is powerful but dangerous. Use wisely.
