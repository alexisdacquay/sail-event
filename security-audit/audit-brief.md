# Security Audit Brief — Sail-event

## Scope

Backend application (`backend/app/`) and supporting infrastructure. Focus areas:

### 1. Authentication and JWT (`backend/app/auth.py`, `backend/app/deps.py`)

- JWT signing with HS256, secret from `JWT_SECRET` env var
- Dev fallback secret `sail-event-dev-secret-do-not-use-in-prod` when env var is unset
- bcrypt password hashing
- Bearer token validation in `get_current_user` dependency
- Token expiry enforcement (`JWT_EXPIRY_MINUTES`, default 60)

### 2. API key gate (`backend/app/routers/search.py`)

- `POST /api/search/all` protected by `X-API-Key` header compared to `SEARCH_ALL_API_KEY` env var
- Returns 401 when key is missing, wrong, or env var is unset

### 3. ICS token secrecy (`backend/app/routers/calendar.py`)

- Calendar feed served at `/api/calendar/{ics_token}` — the token is a UUID4, acts as an unguessable URL
- `GET /api/calendar-url` returns the URL to the authenticated user only

### 4. Input validation (all routers)

- Pydantic model validation with 422-to-400 handler that strips raw input from error responses
- `DecisionRequest.decision` typed as `Literal["accepted", "rejected"]`
- Threshold validation: `lower_threshold < upper_threshold`
- Empty username/password checks in auth routes

### 5. Secrets handling (`docker-compose.yml`, `.env.example`)

- `JWT_SECRET`, `SEARCH_ALL_API_KEY`, `ANTHROPIC_API_KEY`, `TAVILY_API_KEY` in env vars
- `.env.example` uses placeholder values (`change-me`)
- Compose interpolates from host env / `.env` file

### 6. Incident responder (`incident-response/responder.py`, `autonomy-policy.yaml`, `responder-task.md`)

- Responder agent capabilities and credential exposure
- `--allowedTools` whitelist (lines 84-88 of `responder.py`)
- Worktree isolation
- Budget cap `--max-budget-usd 1`, subprocess timeout 300s

### 7. CI workflow permissions (`.github/workflows/ci.yml`)

- Default `GITHUB_TOKEN` permissions (no explicit `permissions:` block)
- Docker compose in CI with dev credentials
- No secrets used in CI beyond default token

## Out of scope

- Frontend JavaScript (client-side only, no secrets)
- Observability stack (internal network, no auth surface)
- Deployment infrastructure (not yet deployed)
