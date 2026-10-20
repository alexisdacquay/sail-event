# Stage 1: build frontend
FROM node:24-alpine AS frontend
WORKDIR /build
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci
COPY frontend/ .
RUN VITE_API_URL="" npm run build

# Stage 2: production image
FROM python:3.12-slim
# Env vars the container recognises:
#   DATABASE_URL      — default sqlite:////data/sail_event.db
#   JWT_SECRET        — required for auth
#   SEARCH_ALL_API_KEY — shared secret for POST /api/search/all
#   CORS_ORIGINS      — default "" (not needed when same-origin)
#   SEED_DEMO         — set to 1 to create demo user on startup
ENV DATABASE_URL="sqlite:////data/sail_event.db"
COPY --from=ghcr.io/astral-sh/uv:0.11.15 /uv /usr/local/bin/uv
WORKDIR /app
COPY backend/pyproject.toml backend/uv.lock ./backend/
RUN cd backend && uv sync --no-dev --frozen
COPY backend/ ./backend/
COPY --from=frontend /build/dist ./frontend/dist
EXPOSE 8000
CMD ["sh", "-c", "cd /app/backend && uv run --no-dev alembic upgrade head && uv run --no-dev uvicorn app.main:app --host 0.0.0.0 --port 8000"]
