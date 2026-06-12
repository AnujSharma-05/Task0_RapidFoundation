## Status: MOSTLY COMPLETE
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
| File | Contents |
|---|---|
| `auth.py` | router, config, middleware, routes |
| `config.py` | `JWT_SECRET_KEY` from `.env` |
| `schemas.py` | `UserCreate`, `Token` |

## Branch: Work done on `main`, migration happens in `feature/m0-monorepo-setup`
