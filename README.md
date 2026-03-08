# Job Aggregator

A small **FastAPI + React application** that aggregates job listings from multiple platforms and helps users track their job applications.

The app scrapes job postings for selected designations and provides a simple interface to:

- View relevant jobs
- Track application status
- Filter out irrelevant jobs
- Manage personal job preferences

---

# Features

- Scrapes jobs from multiple sources (LinkedIn, Indeed, Hirist)
- User authentication (register/login)
- Track job statuses:
  - Applied
  - Interviewed
  - Rejected
  - Irrelevant
- Filter jobs by status
- Hide irrelevant job roles
- Background job fetching using Celery
- Simple React frontend for managing jobs

---

# Tech Stack

**Backend**
- FastAPI
- SQLModel
- SQLite
- Celery
- Redis

**Frontend**
- React
- Vite

---

# Project Structure
app/
api/ FastAPI routes
models/ Database models
services/ Scrapers and job ingestion

frontend/react-app/
React frontend

jobs.db
SQLite database (created automatically)


---

# Prerequisites

- Python 3.10+
- Node.js 18+
- Redis

Install Redis:

### Mac

brew install redis
brew services start redis


### Linux

sudo apt install redis-server


---

# Running the Project

## Backend

From the project root:


source env/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload


Backend runs at:


http://localhost:8000


---

## Frontend


cd frontend/react-app
npm install
npm run dev


Frontend runs at:


http://localhost:3000


---

# Run Everything With One Command

You can start the entire stack using the provided script:


chmod +x run_all.sh
./run_all.sh


This starts:

- Redis
- FastAPI backend
- React frontend
- Celery worker
- Celery scheduler

---

# Example Workflow

1. Register or login
2. Add job designations (e.g., *Backend Developer*)
3. The system fetches relevant jobs
4. Track jobs by status:
   - Applied
   - Interviewed
   - Rejected
5. Mark irrelevant jobs to hide similar roles

---

# Scraping Notes

Some platforms block automated scraping.  
The included scrapers are minimal examples for development purposes.

For production usage you would typically add:

- Rate limiting
- Retries
- Rotating proxies
- Official APIs where available

---

# Future Improvements

- AI-assisted resume suggestions
- Job description analysis
- Pagination for job listings
- Better filtering and recommendations

