# Example: Two-Agent Development with YOLO Mode

This example shows how two Claude Code sessions can collaborate on building a FastAPI + React application, with command execution enabled.

## Setup

### Terminal 1: Start the Bridge

```bash
cd /path/to/bridge
python3 claude_bridge_secure.py /tmp/dev_bridge.db
```

### Terminal 2: Backend Session (Session A)

```bash
cd ~/projects/todo-app/backend

claude-code
```

**Initial prompt for Session A:**

```
You are Session A: Backend API Developer

# Your Mission
Build a FastAPI backend for a todo application with YOLO mode enabled.

# Setup Instructions
1. Create conversation:
   - my_role: "backend_api_developer"
   - partner_role: "frontend_react_developer"
   
2. Save the conversation_id and your token

3. Enable YOLO mode with restricted access:
   - mode: "restricted"
   - workspace: "$PWD"
   - timeout: 60
   - sandbox: false (we trust our code for this demo)

4. Keep partner informed:
   - Update status regularly
   - Check messages every 30 seconds
   - Send progress updates

# Your Tasks
1. Initialize FastAPI project structure
2. Create todo API endpoints (GET, POST, DELETE)
3. Add SQLite database
4. Write tests
5. Coordinate with Session B on API contract

# Communication Pattern
- Propose endpoints before implementing
- Share test results
- Notify partner when API is ready
- Execute commands and share results

# Available Commands (restricted mode)
- File operations: cat, ls, find, grep
- Git: add, commit, status, diff
- Package management: pip install
- Testing: pytest
- Development: python manage.py, uvicorn

Start by creating the conversation and enabling YOLO mode.
```

### Terminal 3: Frontend Session (Session B)

```bash
cd ~/projects/todo-app/frontend

claude-code
```

**Initial prompt for Session B:**

```
You are Session B: Frontend React Developer

# Your Mission
Build a React frontend for a todo application, coordinating with the backend developer.

# Setup Instructions
1. Session A will share:
   - conversation_id
   - your token (session_b_token)
   
2. Enable YOLO mode:
   - mode: "restricted"
   - workspace: "$PWD"
   - timeout: 60

3. Communication:
   - Check messages every 30 seconds
   - Send updates to partner
   - Update status regularly

# Your Tasks
1. Initialize React project with Vite
2. Create todo components
3. Integrate with backend API (coordinate contract first!)
4. Style with Tailwind CSS
5. Write component tests

# Coordination Protocol
- Wait for API contract from Session A
- Propose UI mockups
- Share test results
- Request backend changes if needed

# Available Commands (restricted mode)
- File operations: cat, ls, find
- Git: add, commit, status
- Package management: npm install
- Development: npm run dev, npm run build
- Testing: npm test

Wait for conversation details from Session A, then check messages and respond.
```

## Example Workflow

### Phase 1: Initialization

**Session A:**
```
I'll create our conversation.

[Calls create_conversation with roles]
Result: conv_a1b2c3d4e5f6g7h8

My token: abc123...
Partner token: def456...

Share with Session B:
- Conversation ID: conv_a1b2c3d4e5f6g7h8
- Your token: def456...

[Calls enable_yolo_mode with mode="restricted"]
✅ YOLO mode enabled

[Updates status to "working"]

[Calls execute_command: "mkdir -p app/api app/models tests"]
[Calls execute_command: "pip install fastapi uvicorn sqlalchemy pytest"]

[Sends to partner: "API project initialized. Proposing endpoints:
- GET /api/todos - List all todos
- POST /api/todos - Create todo
- DELETE /api/todos/{id} - Delete todo
What do you think?"]
```

**Session B:**
```
[Receives conversation ID and token from Session A via secure channel]

[Calls check_messages]
📬 1 new message:
From: Session A
"API project initialized. Proposing endpoints..."

[Calls enable_yolo_mode with mode="restricted"]
✅ YOLO mode enabled

[Calls execute_command: "npm create vite@latest . -- --template react"]
[Calls execute_command: "npm install"]

[Sends to partner: "Endpoints look good! Can you add:
- PATCH /api/todos/{id} - Update todo status
Also, what's the todo schema?"]
```

### Phase 2: Implementation

**Session A:**
```
[Checks messages]
📬 Request for PATCH endpoint and schema

[Sends to partner: "Good call! Schema:
{
  id: int,
  title: string,
  completed: boolean,
  created_at: datetime
}"]

[Calls execute_command: "cat > app/models/todo.py << 'EOF'
from sqlalchemy import Column, Integer, String, Boolean, DateTime
from datetime import datetime
from app.database import Base

class Todo(Base):
    __tablename__ = 'todos'
    
    id = Column(Integer, primary_key=True)
    title = Column(String, nullable=False)
    completed = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
EOF"]

[Implements API endpoints...]

[Calls execute_command: "pytest tests/test_api.py -v"]
Result: 5 passed in 1.2s

[Sends to partner: "✅ All tests pass! API running on localhost:8000"]
```

**Session B:**
```
[Checks messages]
📬 API schema and test results

[Calls execute_command: "cat > src/api/todos.js << 'EOF'
const API_URL = 'http://localhost:8000/api';

export const getTodos = () => fetch(\`\${API_URL}/todos\`).then(r => r.json());
export const createTodo = (title) => fetch(\`\${API_URL}/todos\`, {
  method: 'POST',
  headers: {'Content-Type': 'application/json'},
  body: JSON.stringify({title})
}).then(r => r.json());
EOF"]

[Implements React components...]

[Calls execute_command: "npm run dev"]
Result: Server started on http://localhost:5173

[Sends to partner: "Frontend running! Can you enable CORS on the API?"]
```

### Phase 3: Integration

**Session A:**
```
[Checks messages]
📬 CORS request

[Calls execute_command: "cat > app/main.py << 'EOF'
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=['http://localhost:5173'],
    allow_methods=['*'],
    allow_headers=['*']
)
EOF"]

[Calls execute_command: "uvicorn app.main:app --reload"]

[Sends to partner: "✅ CORS enabled. Try it now!"]
```

**Session B:**
```
[Checks messages]
📬 CORS enabled

[Tests integration manually]

[Calls execute_command: "npm test"]
Result: All component tests pass

[Sends to partner: "🎉 Everything works! Ready to commit?"]
```

### Phase 4: Finalization

**Session A:**
```
[Calls execute_command: "git add ."]
[Calls execute_command: "git commit -m 'Add todo API with CRUD endpoints'"]
[Calls execute_command: "git log -1 --stat"]

[Updates status to "complete"]

[Sends to partner: "Committed! Can you handle frontend commit?"]
```

**Session B:**
```
[Calls execute_command: "git add ."]
[Calls execute_command: "git commit -m 'Add todo React frontend with API integration'"]

[Updates status to "complete"]

[Sends to partner: "✅ Done! Great collaboration!"]
```

## Monitoring from Outside

```bash
# Watch the conversation unfold
watch -n 2 'python3 bridge_cli.py show conv_a1b2c3d4e5f6g7h8'

# Check audit log
python3 bridge_cli.py audit conv_a1b2c3d4e5f6g7h8

# See what commands were executed
python3 bridge_cli.py audit conv_a1b2c3d4e5f6g7h8 | grep command_execute
```

## Safety Notes

This example uses `sandbox: false` for simplicity. In production:

1. **Use Docker sandboxing:**
   ```json
   {"sandbox": true}
   ```

2. **Start with safe mode:**
   ```json
   {"mode": "safe"}
   ```
   Then escalate only when needed.

3. **Use separate workspaces:**
   - Session A: `/home/user/project/backend`
   - Session B: `/home/user/project/frontend`

4. **Review before executing:**
   Each agent should propose commands via `send_to_partner` before executing in critical operations.

5. **Git snapshots:**
   Before major changes:
   ```bash
   git stash
   git branch backup-20251026
   ```

## Advanced Patterns

### Pattern 1: Code Review Flow

**Session A writes code, Session B reviews:**

```
Session A:
- Implements feature
- execute_command: "git diff"
- send_to_partner: "Review this diff?"

Session B:
- check_messages
- execute_command: "cat src/feature.py"
- execute_command: "pytest tests/test_feature.py"
- send_to_partner: "Looks good, but add error handling on line 42"

Session A:
- Makes changes
- execute_command: "git add .; git commit"
```

### Pattern 2: Parallel Testing

```
Session A:
- execute_command: "pytest tests/backend/ -v"

Session B (simultaneously):
- execute_command: "npm test -- tests/frontend/"

Both:
- check_messages (see each other's results)
- Fix failures in parallel
```

### Pattern 3: Debugging Together

```
Session A:
- execute_command: "tail -f logs/app.log"
- Spots error pattern

Session B:
- execute_command: "grep -r 'ErrorClass' src/"
- Finds problematic code

Session A:
- execute_command: "git blame src/problem.py | grep ErrorClass"
- Identifies who wrote it

Session B:
- Proposes fix
- Session A tests it
```

## Troubleshooting

**"Commands not executing"**
1. Verify YOLO mode enabled: `bridge_cli.py show conv_...`
2. Check audit log for blocks: `bridge_cli.py audit conv_...`
3. Try safe mode first to verify setup

**"Partner not seeing results"**
1. Results broadcast as system messages
2. Use `check_messages` to retrieve
3. Verify both sessions use same conversation ID

**"Timeout errors"**
1. Increase timeout: `enable_yolo_mode` with `timeout: 300`
2. Run long tasks in background
3. Use `screen` or `tmux` for persistent sessions

**"Git conflicts"**
1. Separate workspaces prevent most conflicts
2. Coordinate file ownership upfront
3. Use feature branches per session

This example demonstrates the power of multi-agent development with command execution. Use responsibly!
