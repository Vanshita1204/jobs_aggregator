# Job Aggregator

A personal **FastAPI + React application** that aggregates job listings from LinkedIn, Indeed, and Hirist, and helps you track applications end-to-end — with AI-powered CV tailoring built in.

---

## Features

**Job Discovery**
- Scrapes jobs from LinkedIn, Indeed, and Hirist on a daily schedule or on-demand
- Manually add any job by pasting a URL (supports Indeed, LinkedIn, Hirist natively; LLM extraction for others)
- External/manually-added jobs are visually distinguished with a purple badge

**Application Tracking**
- Track job statuses: Saved, Applied, Interviewed, Rejected, Irrelevant
- Filter job feed by status
- Hide irrelevant job roles

**CV Management**
- Upload and manage multiple CVs (stored in Google Cloud Storage)
- Attach a specific CV to a job application
- Download or delete CVs

**AI CV Tips**
- Get 5 specific, line-referenced tips to tailor your CV for a job
- Compares your CV text against the full job description
- Supports multiple LLM providers: Groq (default), OpenAI, Anthropic, Gemini — configurable in Settings

**Job Descriptions**
- Fetch and cache full job descriptions on demand

**Infrastructure**
- Background job fetching via Celery + Redis
- Docker Compose setup for easy deployment
- JWT-based authentication

---

## Tech Stack

**Backend**
- FastAPI, SQLModel, SQLite
- Celery + Redis (background tasks)
- curl_cffi (TLS fingerprint bypass for Indeed), Playwright (LinkedIn, Hirist)
- Google Cloud Storage (CV files)
- PyJWT (auth)

**Frontend**
- React 18 + Vite

**AI / LLM**
- Groq (`llama-3.3-70b`), OpenAI, Anthropic, Gemini

---

## Prerequisites

- Python 3.10+
- Node.js 18+
- Redis
- A Google Cloud Storage bucket (for CV uploads)
- At least one LLM provider API key (Groq is free to start)

### Install Redis

**Mac**
```bash
brew install redis
brew services start redis
```

**Linux**
```bash
sudo apt install redis-server
```

---

## Environment Variables

Create a `.env` file in the project root:

```
ENV=development
SECRET_KEY=<your-secret-key>
DATABASE_URL=sqlite:///./jobs.db
NEW_JOB_THRESHOLD_HOURS=24
GROQ_API_KEY=<your-groq-key>
GCS_BUCKET=<your-gcs-bucket-name>
PLAYWRIGHT_HEADLESS=false
REDIS_URL=redis://localhost:6379/0
```

---

## Running the Project

### One command (recommended)

```bash
source env/bin/activate
chmod +x run_all.sh
./run_all.sh
```

Starts: Redis · FastAPI backend · React frontend · Celery worker · Celery scheduler

### Individual services

```bash
source env/bin/activate
uvicorn app.main:app --reload                                   # API on :8000
npm run dev --prefix frontend/react-app                         # Frontend on :3000
celery -A app.core.celery:celery_app worker -l info             # Celery worker
celery -A app.core.celery:celery_app beat -l info               # Celery beat
```

### Docker

Docker Compose runs the full stack — Redis, FastAPI backend, Celery worker, Celery beat, and the React frontend — in isolated containers with a single command.

#### Prerequisites

- [Docker Desktop](https://www.docker.com/products/docker-desktop/) (includes Docker Compose)
- A GCP service account JSON key file in the project root (required for GCS CV uploads)

#### Before you start

1. Place your GCP service account key at the project root with this exact filename:
   ```
   job-aggregator-494212-4eef0bed8eb8.json
   ```
   The compose file mounts it read-only into each container at `/run/secrets/gcp-key.json`.

2. Make sure your `.env` file is present — compose loads it automatically. Docker overrides a few values internally:

   | Variable | Docker value | Why |
   |----------|-------------|-----|
   | `PLAYWRIGHT_HEADLESS` | `true` | Containers have no display server |
   | `DATABASE_URL` | `sqlite:////app/data/jobs.db` | Absolute path inside container |
   | `REDIS_URL` | `redis://redis:6379/0` | Service name on Docker network |
   | `GOOGLE_APPLICATION_CREDENTIALS` | `/run/secrets/gcp-key.json` | Mounted key path |

#### Start the stack

```bash
docker compose up --build
```

| Service | URL |
|---------|-----|
| React frontend | http://localhost:3000 |
| FastAPI backend | http://localhost:8000 |
| API docs | http://localhost:8000/docs |

Redis is internal-only (not exposed to the host).

#### Common commands

```bash
# Start in the background
docker compose up --build -d

# View logs (all services)
docker compose logs -f

# View logs for a specific service
docker compose logs -f backend
docker compose logs -f celery-worker

# Stop and remove containers (data volume is preserved)
docker compose down

# Stop and wipe the SQLite database volume
docker compose down -v

# Rebuild a single service after code changes
docker compose up --build backend
```

#### Services and images

| Service | Image | Role |
|---------|-------|------|
| `redis` | `redis:7-alpine` | Celery message broker |
| `backend` | Built from `Dockerfile` | FastAPI API on port 8000 |
| `celery-worker` | Same image as backend | Executes background tasks |
| `celery-beat` | Same image as backend | Sends scheduled tasks to Redis |
| `frontend` | Multi-stage Node → nginx | Serves built React app on port 3000 |

The backend, worker, and beat all use the same Docker image; `docker-compose.yml` overrides the `CMD` for the worker and beat containers.

#### Data persistence

SQLite is stored in a named Docker volume (`db_data`) shared by the backend, worker, and beat containers. The volume survives `docker compose down` — only `docker compose down -v` removes it.

```bash
# Inspect the volume
docker volume inspect jobs_aggregator_db_data
```

---

## Example Workflow

1. Register or log in
2. Add job designations (e.g., *Backend Developer*, *ML Engineer*)
3. Jobs are fetched automatically each day, or trigger a fetch manually
4. Browse your feed — filter by status or search by keyword
5. Mark jobs as Applied / Interviewed / Rejected / Irrelevant
6. Paste a job URL to manually add any listing
7. Upload a CV, attach it to an application, and get AI tips to tailor it

---

## Scraping Notes

| Source | Method | Notes |
|--------|--------|-------|
| Indeed | curl_cffi (`chrome124`) | Bypasses Cloudflare TLS fingerprint |
| LinkedIn | Playwright (browser) | May show login wall; returns 0 results intermittently |
| Hirist | Playwright (browser) | React SPA — requires JS rendering |

For production use you would typically add rate limiting, retries, and rotating proxies.
