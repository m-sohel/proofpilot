.PHONY: test lint benchmark server frontend build seed all

# Run full test suite
test:
	backend/venv/Scripts/pytest.exe -v

# Run backend and frontend linters
lint:
	backend/venv/Scripts/ruff.exe check backend eval
	cd frontend && npm run lint

# Run benchmark evaluation
benchmark:
	backend/venv/Scripts/python.exe eval/run_benchmark.py

# Run benchmark on all 50 cases
benchmark-all:
	backend/venv/Scripts/python.exe eval/run_benchmark.py --all

# Start backend FastAPI server
server:
	backend/venv/Scripts/uvicorn.exe app.main:app --app-dir backend --reload --port 8000

# Start frontend development server
frontend:
	cd frontend && npm run dev

# Build frontend production bundle
build:
	cd frontend && npm run build
