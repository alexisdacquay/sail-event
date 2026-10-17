.PHONY: run run-frontend run-backend test test-integration test-e2e docker-build docker-run compose-up compose-down

HOST_PORT ?= 8000

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

compose-up:
	docker compose up --build -d --wait

compose-down:
	docker compose down

test-integration:
ifdef SAIL_BASE_URL
	cd backend && HOST_PORT=$(HOST_PORT) uv run pytest tests/integration/ -m integration -v
else
	HOST_PORT=$(HOST_PORT) docker compose up --build -d --wait; \
	rc=0; cd backend && HOST_PORT=$(HOST_PORT) uv run pytest tests/integration/ -m integration -v || rc=$$?; \
	cd $(CURDIR) && HOST_PORT=$(HOST_PORT) docker compose down -v; \
	exit $$rc
endif

test-e2e:
ifdef SAIL_BASE_URL
	cd e2e && SAIL_BASE_URL=$(SAIL_BASE_URL) npx playwright test
else
	HOST_PORT=$(HOST_PORT) docker compose up --build -d --wait; \
	rc=0; cd e2e && SAIL_BASE_URL=http://localhost:$(HOST_PORT) npx playwright test || rc=$$?; \
	cd $(CURDIR) && HOST_PORT=$(HOST_PORT) docker compose down -v; \
	exit $$rc
endif
