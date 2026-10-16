.PHONY: run run-frontend run-backend test docker-build docker-run

run-frontend:
	cd frontend && npm run dev

run-backend:
	cd backend && uv run alembic upgrade head && uv run uvicorn app.main:app --reload

run:
	cd backend && uv run alembic upgrade head && SEED_DEMO=1 uv run uvicorn app.main:app --reload & \
	PID_BACK=$$!; \
	cd frontend && VITE_API_URL=http://localhost:8000 npm run dev & \
	PID_FRONT=$$!; \
	trap 'kill $$PID_BACK $$PID_FRONT 2>/dev/null; exit' INT TERM; \
	wait

test:
	cd backend && uv run pytest
	cd frontend && npm test

docker-build:
	docker build -t sail-event:local .

docker-run:
	docker run --rm -p 8000:8000 -v sail-data:/data sail-event:local
