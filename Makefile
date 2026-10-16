.PHONY: run-frontend run-backend test

run-frontend:
	cd frontend && npm run dev

run-backend:
	cd backend && uv run uvicorn app.main:app --reload

test:
	cd backend && uv run pytest
	cd frontend && npm test
