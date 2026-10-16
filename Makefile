.PHONY: run run-frontend run-backend test

run-frontend:
	cd frontend && npm run dev

run-backend:
	cd backend && uv run uvicorn app.main:app --reload

run:
	cd backend && uv run uvicorn app.main:app --reload & \
	PID_BACK=$$!; \
	cd frontend && VITE_API_URL=http://localhost:8000 npm run dev & \
	PID_FRONT=$$!; \
	trap 'kill $$PID_BACK $$PID_FRONT 2>/dev/null; exit' INT TERM; \
	wait

test:
	cd backend && uv run pytest
	cd frontend && npm test
