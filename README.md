# jobs_aggregator

A small FastAPI + React application that scrapes configured sites for job postings and exposes a simple API + frontend to manage saved designations and view matched jobs.

This README focuses on how to run the repository as it exists in this workspace (development setup).

Quick links
- Backend API: http://localhost:8000 (prefixed by `/api/v1` in routes)
- Frontend (dev server): http://localhost:3000

What you'll find in this repo
- `app/` — FastAPI application, models (SQLModel), and API routes
- `app/services` — scraper and parser helpers (example LinkedIn parser)
- `frontend/react-app/` — small React + Vite frontend used for registration, login and viewing jobs
- `jobs.db` — SQLite database file (created automatically in local dev)

Prerequisites
- Python 3.10+ (the project uses modern typing features)
- Node.js + npm (for the frontend)

Backend (local development)

1. Activate the provided virtualenv (recommended):

    source env/bin/activate

2. Install Python dependencies (if you added/updated packages):

    pip install -r requirements.txt

3. Start the backend API (from project root):

    # if virtualenv is activated
    uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

    # or run the bundled uvicorn binary directly
    ./env/bin/uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

Notes
- The app calls `SQLModel.metadata.create_all(...)` on startup (in `app/main.py`), so the SQLite DB (`jobs.db`) and tables are created automatically in development. No migrations are required for quick local testing.
- CORS is already configured to allow the React dev server origin (`http://localhost:3000`) in `app/main.py`.

Frontend (local development)

1. Open a terminal and go to the frontend

    cd frontend/react-app

2. Install dependencies and run the dev server (Vite):

    npm install
    npm run dev

3. Open http://localhost:3000 in your browser. The header contains navigation to Register, Login, Designations, Manage User Designation and Jobs.

API endpoints (selected)
- POST /api/v1/auth/register — register a new user (public)
- POST /api/v1/auth/login — login (returns access_token)
- GET /api/v1/auth/users/me — get current authenticated user
- POST /api/v1/designation/add — create a designation (authenticated)
- POST /api/v1/designation/list — list all designations (public)
- POST /api/v1/user-designation/add — add a designation to the current user (authenticated)
- POST /api/v1/user-designation/delete?user_designation_id=<id> — remove a designation from the current user (authenticated)
- POST /api/v1/user-designation/list — list current user's designations (authenticated)
- GET  /api/v1/jobs/list — list jobs that match current user's designations (authenticated)

If you use the frontend, it stores `access_token` in `localStorage` and the `request` helper in `frontend/react-app/src/api.js` attaches it as a `Bearer` header.

Running the scraper / fetcher
- A basic example fetcher is provided at `app/services/job_fetcher.py`. You can run it manually from the project root:

    source env/bin/activate
    python -c "from app.services.job_fetcher import fetch_linkedin_jobs; print(fetch_linkedin_jobs())"

Notes on scraping
- LinkedIn (and many job sites) may block automated scraping. The included parser is a minimal example. For production use consider:
  - Using official APIs where available
  - Adding proper headers, rate limiting, retries and IP rotation
  - Respecting robots.txt and terms of service

Development tips
- If you change models, restarting the FastAPI server will recreate tables automatically (development only). For production, use proper migrations.
- If you already have `node_modules` tracked or present, the repo `.gitignore` now ignores `node_modules/`.

Troubleshooting
- CORS errors: `app/main.py` allows `http://localhost:3000`. If your frontend runs on a different port, update `allow_origins` in `app/main.py`.
- `ModuleNotFoundError` when running uvicorn: run the command from the repository root and make sure the `env` virtualenv is activated (or use the full path `./env/bin/uvicorn`).
- Database errors: check `jobs.db` permissions and that the app has write access in the repo directory.

Next steps / TODO (optional)
- Add tests (pytest) for API endpoints and scraper adapters
- Add background scheduling for scrapers (Celery/Redis or APScheduler)
- Improve frontend UX and add pagination for job lists

Contributing
- Contributions welcome. Open an issue or PR. Please include tests for new functionality where possible.

License
- Add a `LICENSE` file (MIT or others) if you want to open-source this project.




install python, install playwright