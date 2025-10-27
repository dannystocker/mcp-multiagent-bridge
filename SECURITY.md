# Security Policy

## Supported Versions

| Version | Supported          |
| ------- | ------------------ |
| 1.0.x   | :white_check_mark: |

## Reporting a Vulnerability

**DO NOT** open a public GitHub issue for security vulnerabilities.

Instead, please report security issues responsibly:
- Create a private security advisory on GitHub (preferred)
- Or email: danny.stocker@gmail.com
- Subject: "SECURITY: Claude Code Bridge - [brief description]"

Please include:
1. Description of the vulnerability
2. Steps to reproduce
3. Potential impact
4. Suggested fix (if any)

You will receive a response within 48 hours.

---

## Security Considerations

### ⚠️ YOLO Mode 

YOLO mode enables command execution. This is inherently dangerous and should only be used:
- In isolated development environments
- With explicit user confirmation
- With audit logging enabled
- By users who understand the risks

**Never enable YOLO mode:**
- On production systems
- With untrusted agents
- On shared machines
- Without proper backups

**Safety Features:**
1. Environment variable gate (`YOLO_MODE=1` required)
2. Double confirmation (typed phrase + one-time code)
3. Dry-run default (no actual execution without approval token)
4. Command validation (blocks dangerous patterns)
5. Audit logging (all actions logged with timestamps)
6. Timeout limits (commands killed after 30s by default)
7. Workspace restriction (commands run in specified directory)

### Token Security

Session tokens are cryptographically secure (64-char hex) but:
- Stored in plain text in SQLite
- Visible in MCP debug logs
- Not encrypted at rest
- Expire after 3 hours

For production use, consider:
- Encrypting database at rest
- Using environment-specific key management
- Shorter token lifetimes for sensitive operations

### Known Limitations

1. **No encryption in transit**: Messages stored as plain text in SQLite
2. **No user authentication**: Anyone with file access can read database
3. **Rate limiting**: Implemented but test in your environment
4. **Command execution risks**: YOLO mode can modify system
5. **Audit logs not tamper-proof**: SQLite database can be modified

---

## Threat Model

### In Scope:
- Local multi-agent coordination
- Development/testing environments
- Isolated workspaces
- Human-supervised operations

### Out of Scope:
- Production deployments without additional safeguards
- Multi-tenant systems
- Public-facing APIs
- Unattended automation

---

## Agentic AI Considerations

### Command Execution Risks

YOLO mode enables agentic behavior (AI taking actions in the real world).
This carries significant risks:

**Threat Model:**
- Malicious commands injected by adversarial prompts
- Unintended destructive operations from AI errors
- Privilege escalation attempts
- Data exfiltration
- Credential theft

**Mitigations:**
- Command validation (whitelist + blacklist)
- Execution timeout (30s default)
- Workspace restriction
- Audit logging
- Multi-step approval process
- Environment-specific gating

**Recommended Controls:**
- Run in Docker container with no network access
- Use read-only filesystem where possible
- Drop all unnecessary capabilities
- Monitor audit logs continuously
- Set up alerts for suspicious patterns
- Maintain offline backups

### Compliance with AI Provider Policies

**Anthropic Claude:**
- Comply with [Responsible Scaling Policy](https://www.anthropic.com/responsible-scaling-policy)
- Maintain human oversight
- Document intended use
- Implement operational safeguards

**OpenAI:**
- Comply with [Usage Policies](https://openai.com/policies/usage-policies)
- No unauthorized system access
- No malware development
- Human-in-the-loop for high-risk actions

**Your Responsibility:**
- Ensure compliance with provider terms
- Supervise all agent operations
- Report security issues responsibly
- Maintain appropriate logging

### Acceptable Use

**Allowed:**
- Development and testing workflows
- Automated code quality checks
- Safe file operations (within workspace)
- Git operations (with confirmation)
- Package management (npm/pip install)

**Not Allowed:**
- Production deployments without safeguards
- Unattended operation on critical systems
- Privilege escalation attempts
- Network attacks or exploitation
- Data theft or unauthorized access
- Malware development or deployment

---

## Security Roadmap

Future security enhancements:
- [ ] Message encryption at rest
- [ ] Rate limiting per session (implemented, needs hardening)
- [ ] Command execution sandboxing (Docker)
- [ ] Tamper-evident audit logs
- [ ] TLS for network transport
- [ ] OAuth/OIDC authentication
- [ ] Role-based access control

---

## Security Best Practices

When using this bridge:

1. **Isolate**: Run in dedicated VM or container
2. **Monitor**: Review audit logs regularly
3. **Limit**: Use restrictive YOLO modes
4. **Backup**: Maintain offline backups
5. **Update**: Keep dependencies current
6. **Test**: Validate before production use
7. **Document**: Record configuration decisions

---

## Contact

For security concerns:
- GitHub Security Advisories (preferred)
- Email: danny.stocker@gmail.com

For general questions:
- GitHub Issues
- GitHub Discussions

---

**Last Updated:** 2025-10-27
