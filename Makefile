.PHONY: dev test lint install frontend-install

dev:
	cd backend && uvicorn app.main:app --reload --port 8000 &
	cd frontend && npm run dev

install:
	cd backend && pip install -r requirements.txt

frontend-install:
	cd frontend && npm install

test:
	cd backend && python -m pytest tests/ -v

lint:
	cd backend && ruff check app/ tests/

migrate:
	cd backend && python -m app.db.migrate
