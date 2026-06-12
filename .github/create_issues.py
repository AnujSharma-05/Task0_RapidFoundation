import subprocess
import sys

GH_EXECUTABLE = r"C:\Program Files\GitHub CLI\gh.exe"

issues = [
    {
        "title": "[M0] Task 0.1 — Create live/backend/ folder structure (Monorepo)",
        "labels": "milestone:0-monorepo,type:infra,layer:backend,priority:critical-path",
        "body": """## Goal
Separate CaRAG Live platform code from the original CaRAG engine so both evolve independently.

## What to build
Create the `live/` directory tree inside the CaRAG repo:
```
CaRAG/
├── backend/              ← EXISTING. Original CaRAG. NEVER touch again.
├── live/
│   ├── backend/
│   │   ├── src/
│   │   │   ├── __init__.py
│   │   │   ├── main.py        ← New FastAPI app (port 8001)
│   │   │   ├── config.py      ← JWT_SECRET_KEY, DB URLs
│   │   │   ├── database.py    ← DB engine + session
│   │   │   ├── models.py      ← User, Group, GroupMember + re-exports
│   │   │   ├── schemas.py     ← All Pydantic schemas for Live
│   │   │   ├── auth.py        ← Moved from backend/src/auth.py
│   │   │   ├── groups.py      ← [NEW] Group CRUD router
│   │   │   ├── documents.py   ← [NEW] Group-scoped doc router
│   │   │   └── ws/            ← [Milestone 3+]
│   │   ├── requirements.txt
│   │   └── .env
│   ├── openclaw-plugin/       ← [Milestone 5]
│   └── README.md
```

## Key decisions
- `live/backend/` imports CaRAG's `services.py` directly (add `backend/` to Python path)
- Move auth code (`auth.py`, `UserCreate`, `Token`, `JWT_SECRET_KEY`, `User` model) into `live/backend/src/`
- Revert `backend/src/main.py` and `models.py` to original state (remove `owner_id`, auth imports)

## Acceptance check
- [ ] Both `backend/` (port 8000) and `live/backend/` (port 8001) start independently
- [ ] Original CaRAG API works exactly as before
- [ ] Live API starts and serves `/ping`

## Branch
`feature/m0-monorepo-setup`"""
    },
    {
        "title": "[M1] Auth Layer — Users table, JWT register/login, middleware ✅",
        "labels": "milestone:1-auth,type:feature,layer:backend",
        "body": """## Status: MOSTLY COMPLETE
Auth layer has been implemented in the current `backend/src/` and needs to be migrated to `live/backend/` during Milestone 0.

### Completed
- [x] `User` model (`id`, `email`, `hashed_password`, `created_at`)
- [x] `POST /auth/register` — bcrypt hashing, email uniqueness check
- [x] `POST /auth/login` — hash verification, JWT generation
- [x] `get_current_user` dependency — token decode, user lookup
- [x] `oauth2_scheme` wired to Swagger Authorize button
- [x] Applied to `/upload` and `/documents`

### Remaining
- [ ] Remove `owner_id` from `Document` model (replaced by `group_id` in M2)
- [ ] Migrate all auth code to `live/backend/src/auth.py`

### Key files
- `auth.py` — router, config, middleware, routes
- `config.py` — `JWT_SECRET_KEY` from `.env`
- `schemas.py` — `UserCreate`, `Token`

## Branch
Work done on `main`, migration happens in `feature/m0-monorepo-setup`"""
    },
    {
        "title": "[M2] Task 2.1 — Groups & GroupMembers tables (ORM models)",
        "labels": "milestone:2-groups,type:feature,layer:backend,priority:critical-path",
        "body": """## Goal
Create the relational foundation for multi-tenant group-based document isolation.

## DB relationships
```
User ──(1:many)──▶ GroupMember ◀──(many:1)── Group
                                                │
                                          (1:many)
                                                ▼
                                           Document
```

## Models to create in `live/backend/src/models.py`

### `Group`
- `id` — Integer, PK
- `name` — String, NOT NULL
- `created_by` — Integer, FK → `users.id`
- `created_at` — DateTime
- Relationships: `members` (→ GroupMember), `documents` (→ Document), `creator` (→ User)

### `GroupMember`
- `id` — Integer, PK
- `group_id` — Integer, FK → `groups.id`, CASCADE
- `user_id` — Integer, FK → `users.id`, CASCADE
- `joined_at` — DateTime
- Relationships: `group`, `user`

### Update `User` model
- Add: `memberships = relationship('GroupMember', back_populates='user', cascade='all, delete-orphan')`

### Update `Document` model
- **Remove:** `owner_id`, `owner` relationship
- **Add:** `group_id = Column(Integer, ForeignKey('groups.id', ondelete='CASCADE'), nullable=False, index=True)`
- **Add:** `group = relationship('Group', back_populates='documents')`

## Schemas to add
- `GroupCreate` — `name: str`
- `GroupResponse` — `id`, `name`, `created_by`, `member_count`, `doc_count`
- `GroupDetailResponse` — `id`, `name`, `created_by`, `members[]`, `doc_count`
- `GroupMemberResponse` — `user_id`, `email`, `joined_at`
- `InviteRequest` — `email: EmailStr`

## Acceptance check
- [ ] Server starts without errors
- [ ] `GET /debug/db` shows `groups: 0`, `group_members: 0`

## Branch
`feature/m2-groups-layer`"""
    },
    {
        "title": "[M2] Task 2.2 — Group CRUD endpoints (create, list, detail, delete)",
        "labels": "milestone:2-groups,type:feature,layer:backend",
        "body": """## Goal
REST endpoints for managing groups.

## File: `live/backend/src/groups.py` (new APIRouter)

## Endpoints

| Method | Path | Auth | Description |
|---|---|---|---|
| POST | `/groups` | ✅ | Create group. Creator auto-added as member. |
| GET | `/groups` | ✅ | List groups current user belongs to (JOIN query). |
| GET | `/groups/{id}` | ✅ | Group detail + member list. Must be member. |
| DELETE | `/groups/{id}` | ✅ | Delete group. Only `created_by` user. |

## Key patterns
**JOIN query for 'my groups':**
```python
groups = db.query(Group).join(GroupMember).filter(
    GroupMember.user_id == current_user.id
).all()
```

**Cascade delete handling:**
1. `group_members` → auto-deleted by CASCADE
2. `documents` → auto-deleted by CASCADE
3. `document_chunks` → auto-deleted by CASCADE
4. **Milvus vectors** → MUST manually delete before `db.delete(group)`
5. **Disk files** → MUST manually delete before `db.delete(group)`

## Acceptance check
- [ ] Create 2 groups as User A → login as User B → `GET /groups` returns `[]`
- [ ] Delete group → all related data cleaned up across all 3 storage layers

## Branch
`feature/m2-groups-layer`"""
    },
    {
        "title": "[M2] Task 2.3 — Invite system (POST /groups/{id}/invite)",
        "labels": "milestone:2-groups,type:feature,layer:backend",
        "body": """## Goal
Allow group members to invite other registered users by email.

## Endpoint: `POST /groups/{group_id}/invite`
**Request body:** `{ email: string }`

## Validation chain (order matters!)
1. Does the group exist? → **404** if not
2. Is the current user a member? → **403** if not
3. Does the invitee email exist in `users`? → **404** ('not registered')
4. Is the invitee already a member? → **409** Conflict
5. Is the inviter inviting themselves? → **400**
6. All pass → INSERT `GroupMember` row

## HTTP status codes
- `404` = resource doesn't exist (group or user)
- `403` = you don't have permission
- `409` = conflict with current state
- `400` = bad request

## Edge cases (from Flows doc)
- Email not registered → 'That email isn't registered on CaRAG Live yet.'
- Already a member → 'They're already in this group.'
- Inviting yourself → 'You're already in this group.'

## Acceptance check
- [ ] User A creates group → invites User B by email → User B's `GET /groups` shows the group

## Branch
`feature/m2-groups-layer`"""
    },
    {
        "title": "[M2] Task 2.4 — Group-scoped document routes",
        "labels": "milestone:2-groups,type:feature,layer:backend,priority:critical-path",
        "body": """## Goal
All document operations require `group_id` and validate group membership.

## File: `live/backend/src/documents.py` (new APIRouter)

## Endpoints

| Method | Path | Description |
|---|---|---|
| POST | `/upload` | Upload PDF. Requires `group_id` form field. Validates membership. |
| GET | `/documents?group_id=X` | List docs in group. Validates membership. |
| GET | `/documents/{id}` | Single doc. Validates doc belongs to user's group. |
| DELETE | `/documents/{id}` | Delete doc + Milvus + disk. Any group member can do this. |

## Reusable validation function
```python
def validate_group_membership(db, user_id, group_id) -> Group:
    # Raises 404 if group doesn't exist
    # Raises 403 if user isn't a member
```

## Key change: `POST /upload`
```python
new_doc = Document(
    filename=file.filename,
    file_path=file_path,
    file_size=file_size,
    status='uploaded',
    category=category or 'general',
    group_id=group_id,  # group_id instead of owner_id
)
```

## Acceptance check
- [ ] Upload doc to Group A → User B (not in Group A) → `GET /documents?group_id=A` returns **403**

## Branch
`feature/m2-groups-layer`"""
    },
    {
        "title": "[M2] Task 2.5 — Group-scoped CaRAG query (POST /chat)",
        "labels": "milestone:2-groups,type:feature,layer:backend",
        "body": """## Goal
Queries only search documents belonging to the specified group. Uses the existing CaRAG engine unchanged.

## Key insight: 'Don't touch the engine, control the fuel'
```python
doc_ids = [d.id for d in db.query(Document.id).filter(
    Document.group_id == group_id,
    Document.status == 'ready'
).all()]

result = await services.answer_question(
    question=payload.question,
    document_ids=doc_ids,   # existing parameter!
    top_k=payload.top_k,
)
```

## Schema update
`ChatRequest` gets required `group_id: int` field.

## Validation
1. JWT auth (`get_current_user`)
2. User is member of `group_id` (`validate_group_membership`)
3. Fetch `doc_ids` for that group
4. If no docs → return 'This group has no documents yet.'

## Acceptance check
- [ ] Two groups with different docs. Query Group A → never surfaces Group B's content.

## Branch
`feature/m2-groups-layer`"""
    },
    {
        "title": "[M3] Task 3.1 — Raw WebSocket echo server",
        "labels": "milestone:3-ws-ingestion,type:feature,layer:websocket",
        "body": """## Goal
Get a basic WebSocket endpoint working. Foundation for all real-time features.

## File: `live/backend/src/ws/handlers.py` (new)

## Implementation
```python
async def ws_endpoint(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            data = await websocket.receive_text()
            await websocket.send_text(f'Echo: {data}')
    except WebSocketDisconnect:
        pass
```

## Wire in main.py
```python
app.websocket('/ws')(ws_endpoint)
```

## Learning
- HTTP Upgrade handshake (`Connection: Upgrade`)
- `websocket.accept()` / `receive_text()` / `send_text()` lifecycle
- `WebSocketDisconnect` exception

## Acceptance check
- [ ] `npx -y wscat -c ws://localhost:8001/ws` → send 'hello' → receive 'Echo: hello'
- [ ] Closing client doesn't crash server

## Branch
`feature/m3-websocket-ingestion`"""
    },
    {
        "title": "[M3] Task 3.2 — ConnectionManager with group-aware rooms",
        "labels": "milestone:3-ws-ingestion,type:feature,layer:websocket,priority:critical-path",
        "body": """## Goal
A singleton manager that tracks who is connected and to which group. Enables targeted push and group broadcast.

## File: `live/backend/src/ws/manager.py` (new)

## Data structures
- `user_connections: dict[int, WebSocket]` — one WS per user ('last device wins')
- `group_rooms: dict[int, set[int]]` — group_id → set of connected user_ids

## Methods
- `connect(user_id, group_id, ws)` — close old connection if exists, accept new one, register in room
- `disconnect(user_id, group_id)` — remove from connections + room, clean up empty rooms
- `send_to_user(user_id, data)` — targeted push
- `broadcast_to_group(group_id, data)` — push to all users in a group room

## Edge case: 'last device wins'
If user connects from a second session, old WS gets `{event: 'replaced'}` then closed.

## Acceptance check
- [ ] Two users connect to same group → broadcast → both receive
- [ ] Third user in different group → receives nothing

## Branch
`feature/m3-websocket-ingestion`"""
    },
    {
        "title": "[M3] Task 3.3 — Authenticate WebSocket connections (JWT + group membership)",
        "labels": "milestone:3-ws-ingestion,type:feature,layer:websocket",
        "body": """## Goal
Secure WS connections with JWT auth AND group membership validation before accepting.

## Endpoint: `GET /ws?token=JWT&group_id=GROUP_ID`

## Auth flow
1. Decode `token` (same JWT logic as `get_current_user`)
2. Invalid/expired → `ws.close(code=4001)` → return
3. Query Postgres: is user a member of `group_id`?
4. Not a member → `ws.close(code=4003)` → return
5. All pass → `manager.connect(user_id, group_id, ws)`

## Why query param instead of header
Browsers' WebSocket API (`new WebSocket(url)`) **cannot** set custom headers.

## Custom close codes
| Code | Meaning |
|---|---|
| 4001 | Auth failed (invalid/expired JWT) |
| 4003 | Forbidden (not a member of group) |

## Acceptance check
- [ ] Invalid token → closed 4001
- [ ] Valid token, wrong group → closed 4003
- [ ] Valid token, correct group → stays open

## Branch
`feature/m3-websocket-ingestion`"""
    },
    {
        "title": "[M3] Task 3.4 — Push ingestion events to group members via WebSocket",
        "labels": "milestone:3-ws-ingestion,type:feature,layer:websocket,layer:backend",
        "body": """## Goal
When a document finishes processing, every connected group member sees it instantly — no polling.

## Challenge
`process_document_task` lives in the original CaRAG engine (untouchable). We wrap it.

## Solution: Wrapper function
```python
async def process_document_task_with_ws(doc_id, filename, group_id):
    await manager.broadcast_to_group(group_id, {
        'event': 'doc_processing', 'doc_id': doc_id, 'filename': filename
    })
    await services.process_document_task(doc_id, filename)
    # Check final status, broadcast doc_ready or doc_failed
```

## Events pushed
| Event | When | Payload |
|---|---|---|
| `doc_processing` | Ingestion starts | `doc_id`, `filename` |
| `doc_ready` | Ingestion complete | `doc_id`, `filename`, `category` |
| `doc_failed` | Ingestion failed | `doc_id`, `filename` |

## Acceptance check
- [ ] User A uploads doc. User B (same group, connected via WS) sees events live.

## Branch
`feature/m3-websocket-ingestion`"""
    },
    {
        "title": "[M3] Task 3.5 — Heartbeat ping/pong to detect dead connections",
        "labels": "milestone:3-ws-ingestion,type:feature,layer:websocket",
        "body": """## Goal
Proactively detect and clean up dead WebSocket connections (browser tab closed, network drop).

## Implementation
Background `asyncio` loop started on server startup:
- Every 30 seconds: ping all connected clients
- No response within 5 seconds → remove from manager

## Why this is necessary
Without heartbeat, `user_connections` slowly fills with dead WebSocket objects. Every `send_json()` to a dead connection throws an exception silently. The manager becomes polluted.

## Start in main.py
```python
@app.on_event('startup')
async def startup():
    asyncio.create_task(manager.heartbeat_loop())
```

## Acceptance check
- [ ] Connect client → kill it ungracefully → wait 35s → `manager.user_connections` is empty

## Branch
`feature/m3-websocket-ingestion`"""
    },
    {
        "title": "[M4] Task 4.1 — Gemini streaming mode wrapper",
        "labels": "milestone:4-ws-streaming,type:feature,layer:backend",
        "body": """## Goal
Create a streaming wrapper around Gemini's `generate_content` that yields answer chunks as an async generator.

## File: `live/backend/src/llm_service_live.py` (new — wraps original)

## Implementation
```python
async def generate_answer_stream(question, context):
    response = await asyncio.to_thread(
        model.generate_content, prompt, stream=True
    )
    for chunk in response:
        if chunk.text:
            yield chunk.text
```

## Learning
- `stream=True` returns an iterator instead of a complete response
- Async generators (`yield` inside `async def`)
- This is how ChatGPT's typewriter effect works

## Acceptance check
- [ ] Call function in test script → chunks print progressively, not all at once

## Branch
`feature/m4-websocket-streaming`"""
    },
    {
        "title": "[M4] Task 4.2 — WebSocket message type router + streaming chat handler",
        "labels": "milestone:4-ws-streaming,type:feature,layer:websocket,priority:critical-path",
        "body": """## Goal
Single `/ws` endpoint routes on incoming `type` field. Chat queries stream answers token-by-token.

## Message protocol

### Client → Server
| type | payload | description |
|---|---|---|
| `chat` | `question`, `group_id` | Start streaming RAG query |
| `ping` | — | Client heartbeat |
| `subscribe_doc` | `doc_id` | Want status updates for this doc |

### Server → Client
| event | payload | description |
|---|---|---|
| `chunk` | `text` | One piece of streaming answer |
| `done` | `citations[]` | End of stream + sources |
| `error` | `message` | Something went wrong |
| `doc_ready` | `doc_id`, `category` | Ingestion completed |
| `doc_processing` | `doc_id`, `filename` | Ingestion started |
| `pong` | — | Response to client ping |

## Acceptance check
- [ ] Send `{type: 'chat', question: '...', group_id: 1}` via wscat
- [ ] Chunks stream in progressively
- [ ] `done` received with citations array

## Branch
`feature/m4-websocket-streaming`"""
    },
    {
        "title": "[M5] Task 5.1 — Scaffold OpenClaw plugin + Telegram connection",
        "labels": "milestone:5-openclaw,type:infra,layer:plugin",
        "body": """## Goal
OpenClaw running locally with a Telegram bot. Minimal plugin that responds to any message.

## Folder: `live/openclaw-plugin/`
- `package.json`
- `tsconfig.json`
- `src/index.ts` — `onMessage(ctx)` handler

## Acceptance check
- [ ] DM anything → bot replies 'CaRAG Live is online 🟢'

## Branch
`feature/m5-openclaw-plugin`"""
    },
    {
        "title": "[M5] Task 5.2 — LLM-powered intent classifier (intent.ts)",
        "labels": "milestone:5-openclaw,type:feature,layer:plugin",
        "body": """## Goal
Classify raw Telegram messages into structured intents using an LLM.

## Intent types
`query`, `upload`, `new_group`, `list_docs`, `list_groups`, `switch_group`, `invite`, `remove_doc`, `delete_group`, `help`, `unknown`

## Fallback (malformed LLM response)
Keyword matching: file attached → upload, starts with 'ask/what/how' → query, else → unknown.

## Acceptance check
- [ ] 10 varied natural language messages → at least 8 correctly classified

## Branch
`feature/m5-openclaw-plugin`"""
    },
    {
        "title": "[M5] Task 5.3 — Group context manager with sticky memory (groupCtx.ts)",
        "labels": "milestone:5-openclaw,type:feature,layer:plugin",
        "body": """## Goal
Resolve which group to use for any group-scoped action.

## Logic
1. `GET /groups` → fetch user's groups
2. 0 groups → 'Create a group first' → STOP
3. 1 group → use directly, no picker
4. 2+ groups:
   - Memory hit + age < 24h → verify still valid → use it
   - Memory miss or expired → show Telegram inline keyboard → user taps → store

## Edge cases
- Active group deleted since last session → clear memory, show picker
- User removed from group → same handling
- Picker timeout (5 min) → next message re-triggers

## Acceptance check
- [ ] User with 3 groups → picker → tap → next query skips picker → 24h later → picker again

## Branch
`feature/m5-openclaw-plugin`"""
    },
    {
        "title": "[M5] Task 5.4 — CaRAG Live REST client (carag.ts)",
        "labels": "milestone:5-openclaw,type:feature,layer:plugin",
        "body": """## Goal
Typed TypeScript client that calls CaRAG Live REST endpoints.

## Methods
- `login(email, password)`
- `listGroups()`
- `listDocs(groupId)`
- `uploadFile(groupId, fileUrl)` — fetch from Telegram CDN, re-POST as multipart
- `inviteMember(groupId, email)`
- `authedFetch()` — auto-refresh JWT on 401

## Acceptance check
- [ ] DM 'list my docs' → bot replies with filenames from active group

## Branch
`feature/m5-openclaw-plugin`"""
    },
    {
        "title": "[M5] Task 5.5 — Stream query responses over WebSocket",
        "labels": "milestone:5-openclaw,type:feature,layer:plugin,layer:websocket",
        "body": """## Goal
Plugin opens WebSocket to CaRAG Live, streams answer, sends complete response to Telegram.

## Flow
1. Open `ws://localhost:8001/ws?token=JWT&group_id=GID`
2. Send `{"type": "chat", "question": "..."}`
3. Buffer `chunk` events
4. On `done` → close WS → send full answer + citations to Telegram
5. WS drops before `done` → reply 'Connection dropped. Ask again.'

## Telegram limit
4096 chars max per message. Chunk if longer.

## Acceptance check
- [ ] DM a question → Telegram replies with full answer + citations

## Branch
`feature/m5-openclaw-plugin`"""
    },
    {
        "title": "[M5] Task 5.6 — Invite flow end-to-end",
        "labels": "milestone:5-openclaw,type:feature,layer:plugin",
        "body": """## Goal
Handle invite intent: resolve group → `POST /groups/{id}/invite` → reply with result.

## Error mapping
| API Response | Telegram Reply |
|---|---|
| 200 | '✅ user@email.com added to Group Name' |
| 404 (email) | 'That email isn't registered yet.' |
| 409 | 'They're already in this group.' |
| 403 | 'You're not a member of that group.' |

## Acceptance check
- [ ] DM 'invite someone@email.com' → that user sees group in `GET /groups`

## Branch
`feature/m5-openclaw-plugin`"""
    },
    {
        "title": "[M6] Task 6.1 — Global structured error handling",
        "labels": "milestone:6-polish,type:feature,layer:backend",
        "body": """## Goal
Every REST error returns consistent JSON: `{error, code, detail}`.
Global FastAPI exception handler for 401, 403, 404, 409, 422, 429, 500.

## Branch
`feature/m6-polish`"""
    },
    {
        "title": "[M6] Task 6.2 — Pydantic v2 input validation",
        "labels": "milestone:6-polish,type:feature,layer:backend",
        "body": """## Goal
Add `Field()` constraints to all schemas:
- `question`: min 1, max 500 chars
- `top_k`: 1–10
- `group name`: 3–50 chars
- `password`: min 8 chars

Test invalid payloads → verify 422.

## Branch
`feature/m6-polish`"""
    },
    {
        "title": "[M6] Task 6.3 — Rate limiting on auth endpoints",
        "labels": "milestone:6-polish,type:feature,layer:backend",
        "body": """## Goal
`slowapi` — 5 login attempts/min/IP. `429 Too Many Requests` with `Retry-After` header.

## Branch
`feature/m6-polish`"""
    },
    {
        "title": "[M6] Task 6.4 — WebSocket reconnect with exponential backoff",
        "labels": "milestone:6-polish,type:feature,layer:websocket",
        "body": """## Goal
Client-side: on `onclose` → 1s → 2s → 4s → 8s → cap 30s. Reset on success.
Re-authenticate + re-join group room after reconnect.

## Branch
`feature/m6-polish`"""
    },
    {
        "title": "[M6] Task 6.5 — Write CaRAG Live README",
        "labels": "milestone:6-polish,type:infra",
        "body": """## Goal
- Architecture diagram (Mermaid)
- What each milestone adds
- How to run locally
- 'What I learned' section

## Branch
`feature/m6-polish`"""
    }
]

for issue in issues:
    # Create a temporary file for the body
    with open("temp_issue_body.md", "w", encoding="utf-8") as f:
        f.write(issue["body"])
    
    cmd = [
        GH_EXECUTABLE, "issue", "create",
        "--title", issue["title"],
        "--label", issue["labels"],
        "--body-file", "temp_issue_body.md"
    ]
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"Failed to create issue: {result.stderr}", file=sys.stderr)
        sys.exit(1)
    else:
        print(f"Successfully created: {result.stdout.strip()}")

print("All issues created successfully!")
