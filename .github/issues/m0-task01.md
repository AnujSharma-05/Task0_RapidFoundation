## Goal
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
1. `live/backend/` imports CaRAG's `services.py` directly (add `backend/` to Python path)
2. Move auth code (`auth.py`, `UserCreate`, `Token`, `JWT_SECRET_KEY`, `User` model) into `live/backend/src/`
3. Revert `backend/src/main.py` and `models.py` to original state (remove `owner_id`, auth imports)

## Acceptance check
- [ ] Both `backend/` (port 8000) and `live/backend/` (port 8001) start independently
- [ ] Original CaRAG API works exactly as before
- [ ] Live API starts and serves `/ping`

## Branch: `feature/m0-monorepo-setup`
