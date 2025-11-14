# MCP Multiagent Bridge

Production-ready Python MCP server for secure multi-agent coordination with comprehensive safeguards.

## Overview

Enables multiple LLM agents (Claude, Codex, GPT, etc.) to collaborate safely through the Model Context Protocol without sharing workspaces or credentials. Built with security-first architecture and production-grade safeguards.

**Use cases:**
- Backend agent coordinating with frontend agent on different codebases
- Security review agent validating changes from development agent
- Specialized agents collaborating on complex multi-step workflows
- Any scenario requiring isolated agents to communicate securely

---

## Key Features

### 🔒 Security Architecture

**Authentication & Authorization:**
- HMAC-SHA256 session token authentication
- Automatic secret redaction (API keys, passwords, tokens, private keys)
- 3-hour session expiration with automatic cleanup
- SQLite WAL mode for atomic, race-condition-free operations

**4-Stage YOLO Guard™:**
Command execution (optional) requires multiple confirmation layers:
1. Environment gate - explicit `YOLO_MODE=1` opt-in
2. Interactive typed confirmation phrase
3. One-time validation code (prevents automation)
4. Time-limited approval tokens (5-minute TTL, single-use)

**Rate Limiting:**
- Token bucket algorithm with configurable windows
- Default: 10 requests/minute, 100/hour, 500/day
- Per-session tracking with automatic reset
- Prevents abuse while allowing legitimate bursts

**Audit Trail:**
- Comprehensive JSONL logging of all operations
- Timestamps, session IDs, actions, results
- Tamper-evident sequential logging
- Supports compliance and forensic analysis

### 🏗️ Production-Ready Architecture

- **Message-only bridge** - No auto-execution, returns proposals only
- **Schema validation** - Strict JSON schemas for all MCP tools
- **Command validation** - Configurable whitelist/blacklist patterns
- **Comprehensive error handling** - Graceful degradation, informative errors
- **Extensible design** - Plugin architecture for future backends

### 📦 Platform Support

**Works with any MCP-compatible LLM:**
- Claude Code, Claude Desktop, Claude API
- OpenAI models (via MCP adapters)
- Anthropic API models
- Custom/future models (not tied to specific backend)

---

## Installation

```bash
# Clone repository
git clone https://github.com/dannystocker/mcp-multiagent-bridge.git
cd mcp-multiagent-bridge

# Install dependencies
pip install mcp>=1.0.0

# Run tests
python test_security.py
```

Full setup: See [QUICKSTART.md](QUICKSTART.md)

---

## Documentation

**Getting Started:**
- [QUICKSTART.md](QUICKSTART.md) - 5-minute setup guide
- [EXAMPLE_WORKFLOW.md](EXAMPLE_WORKFLOW.md) - Real-world collaboration scenarios
- [PRODUCTION.md](PRODUCTION.md) - Production deployment & test results ⭐ **NEW**

**Production Hardening:**
- [scripts/production/README.md](scripts/production/README.md) - Keep-alive daemons, watchdog, task reassignment ⭐ **NEW**
- [PRODUCTION.md](PRODUCTION.md) - Complete test results with IF.TTT citations

**Security & Compliance:**
- [SECURITY.md](SECURITY.md) - Threat model, responsible disclosure policy
- [YOLO_MODE.md](YOLO_MODE.md) - Command execution safety guide
- Policy compliance: Anthropic AUP, OpenAI Usage Policies

**Contributing:**
- [CONTRIBUTING.md](CONTRIBUTING.md) - Development setup, PR workflow
- [LICENSE](LICENSE) - MIT License

---

## Technical Stack

- **Python 3.11+** - Modern Python with type hints
- **SQLite** - Atomic operations with WAL mode
- **MCP Protocol** - Model Context Protocol integration
- **pytest** - Comprehensive test suite
- **CI/CD** - GitHub Actions (tests, security scanning, linting)

---

## Project Statistics

- **Lines of Code:** ~6,700 (including tests, production scripts + documentation)
- **Test Coverage:** ✅ Core security validated (482 operations, zero failures)
- **Documentation:** 3,500+ lines across 11 markdown files
- **Dependencies:** 1 (mcp>=1.0.0, pinned for reproducibility)
- **License:** MIT

### Production Test Results (November 2025)

**10-Agent Stress Test:**
- ✅ **1.7ms average latency** (58x better than 100ms target)
- ✅ **100% message delivery** (zero failures)
- ✅ **482 concurrent operations** (zero race conditions)
- ✅ **Perfect data integrity** (SQLite WAL validated)

**9-Agent S² Production Hardening:**
- ✅ **90-minute test** (idle recovery, keep-alive, watchdog)
- ✅ **<5 min task reassignment** (automated worker failure recovery)
- ✅ **100% keep-alive delivery** (30-minute validation)
- ✅ **<50ms push notifications** (filesystem watcher, 428x faster than polling)

**Full Report:** See [PRODUCTION.md](PRODUCTION.md)

---

## Development

```bash
# Install dev dependencies
pip install -r requirements.txt

# Install pre-commit hooks
pip install pre-commit
pre-commit install

# Run test suite
pytest

# Run security tests
python test_security.py
```

See [CONTRIBUTING.md](CONTRIBUTING.md) for complete development workflow.

---

## Production Status

✅ **Production-Ready** (Validated November 2025)

**Successfully tested with:**
- ✅ 10-agent stress test (94 seconds, 100% reliability)
- ✅ 9-agent production deployment (90 minutes, full hardening)
- ✅ 1.7ms average latency (58x better than target)
- ✅ Zero data corruption in 482 concurrent operations
- ✅ Automated recovery from worker failures (<5 min)

**Recommended for:**
- Production multi-agent coordination
- Development and testing workflows
- Isolated workspaces (recommended)
- Human-supervised operations
- 24/7 autonomous agent systems (with production scripts)

**Production deployment:**
- See [PRODUCTION.md](PRODUCTION.md) for complete deployment guide
- Use [scripts/production/](scripts/production/) for keep-alive, watchdog, and task reassignment
- Follow [SECURITY.md](SECURITY.md) security best practices

---

## Support

- **Issues:** [GitHub Issues](https://github.com/dannystocker/mcp-multiagent-bridge/issues)
- **Discussions:** [GitHub Discussions](https://github.com/dannystocker/mcp-multiagent-bridge/discussions)
- **Security:** See [SECURITY.md](SECURITY.md) for responsible disclosure

---

## License

MIT License - Copyright © 2025 Danny Stocker

See [LICENSE](LICENSE) for full terms.

---

## Acknowledgments

Built with [Claude Code](https://docs.claude.com/claude-code) and [Model Context Protocol](https://modelcontextprotocol.io/).
