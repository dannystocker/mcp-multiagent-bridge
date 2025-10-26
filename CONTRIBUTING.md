# Contributing to Claude Code Bridge

## Welcome!

Thanks for your interest in contributing! This project aims to make multi-agent
coordination with Claude Code secure and practical.

## How to Contribute

### Reporting Bugs

Open a GitHub issue with:
- Description of the bug
- Steps to reproduce
- Expected vs actual behavior
- Environment (OS, Python version, MCP version)

### Suggesting Features

Open a GitHub issue with:
- Use case description
- Proposed solution
- Alternative approaches considered
- Potential security implications

### Pull Requests

1. **Fork the repository**
2. **Create a feature branch**: `git checkout -b feature/amazing-feature`
3. **Make your changes**
4. **Add tests** for new functionality
5. **Run the test suite**: `python test_bridge.py && python test_security.py`
6. **Lint your code**: `ruff check . --fix` (if available)
7. **Commit with descriptive message**: `git commit -m 'feat: Add amazing feature'`
8. **Push to your fork**: `git push origin feature/amazing-feature`
9. **Open a Pull Request**

### Commit Message Format

```
<type>: <subject>

<body>

<footer>
```

**Types:**
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `test`: Test additions/changes
- `refactor`: Code refactoring
- `chore`: Maintenance tasks
- `security`: Security improvements

**Example:**
```
feat: Add rate limiting per session

Implement token bucket rate limiter to prevent abuse.
Configurable limits: 10 req/min, 100 req/hour.

Closes #15
```

## Development Setup

```bash
# Clone your fork
git clone https://github.com/YOUR_USERNAME/claude-code-bridge.git
cd claude-code-bridge

# Install dependencies
pip install -r requirements.txt

# Run tests
python test_bridge.py
python test_security.py

# Run with MCP debug mode
claude-code --mcp-debug
```

## Code Style

- Follow PEP 8
- Use type hints
- Add docstrings to public methods
- Keep functions under 50 lines when possible
- Write self-documenting code

## Testing

- Add tests for all new features
- Maintain test coverage above 80%
- Include both positive and negative test cases
- Test security-critical paths thoroughly

## Security Considerations

When contributing:
- Never commit secrets or tokens
- Be extra cautious with YOLO mode changes
- Consider security implications of all changes
- Add security tests for authentication/authorization changes
- Update SECURITY.md if threat model changes

## Questions?

Open a GitHub discussion or issue. We're here to help!

## License

By contributing, you agree that your contributions will be licensed under
the same MIT License that covers this project.
