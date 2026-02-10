# jobs_aggregator

A small web application that scrapes selected job sites and notifies users about new job openings matching their saved search criteria.

Key features
- User registration, login and profile management
- Users can save job titles / search keywords they're interested in
- Periodic scraping of configured websites for new job postings
- Store discovered jobs with source links and metadata
- Simple notification mechanism (email or in-app) for new matches

Motivation

This project collects and centralises job postings from multiple sites so users can track new openings for roles they care about without visiting each site individually.

Tech stack (suggested)
- Language: Python 3.10+
- Web framework: FastAPI 
- Scraping: requests + BeautifulSoup for simple sites; Playwright or Selenium for JS-heavy sites
- Database: SQLite for development, PostgreSQL for production
- Task scheduling: Celery + Redis (scalable)
- Auth: OAuth/JWT or FastAPI Users
- Testing: pytest

Architecture overview

- Web/API layer: user registration, authentication, job management UI/API
- Scraper workers: modular scrapers per target site that normalize job data
- Scheduler: triggers scrapers on an interval (daily by default)
- Database: stores users, saved searches, job records, and scrape history

Data model (high level)
- User: id, email, password_hash, preferences
- SavedSearch: id, user_id, title/keywords, locations (optional), frequency
- Job: id, title, company, location, posted_date, summary, url, source, scraped_at
- Notification: id, user_id, job_id, status, sent_at

Getting started (local development)

1. Create and activate a virtual environment

	python -m venv .venv
	source .venv/bin/activate

2. Install dependencies (example for FastAPI + scraping)

	pip install -r requirements.txt

3. Create a `.env` file with required environment variables (DB URL, secret keys, email settings)

4. Initialize the database (example using Alembic/SQLAlchemy)

	# configure your DATABASE_URL in .env, then run migrations
	alembic upgrade head

5. Run the API

	uvicorn app.main:app --reload

Scheduler / background scraping

- For a small/low-traffic setup, use APScheduler inside the web process to schedule daily scrapes.
- For a production-ready approach, run scrapers as separate worker processes (Celery + Redis) and schedule tasks via Celery Beat or an external cron.

Scraper design notes
- Make each target site scraper a small adapter that returns job records in a consistent schema.
- Respect robots.txt and site terms of service.
- Add rate-limiting and randomized delays to avoid hammering target sites.
- Consider using official APIs where available.

Notifications
- Start with in-app notifications recorded in the DB and displayed on the user dashboard.
- Add email notifications using an SMTP provider (SendGrid, Mailgun) or transactional email service later.

Testing
- Use pytest for unit tests. Add simple tests for scraper adapters (mock network), API endpoints, and DB models.

Security and privacy
- Store passwords hashed with a modern algorithm (bcrypt / argon2).
- Never commit secrets; use `.env` and environment variables for deployment.

Deployment
- Dockerize the app for consistent deployments.
- Use a managed Postgres DB and Redis in production.
- Use process managers (systemd, supervisord) or containers/orchestrators (Docker Compose, Kubernetes) to run the API and worker processes.

Roadmap / next steps
- Add a minimal FastAPI app and authentication endpoints
- Implement a scraper adapter for one site (example: Indeed or GitHub Jobs if available)
- Add a scheduler to run scrapes daily and save new job records
- Add a simple frontend (React / server-rendered templates) for user interactions

Contributing

Contributions are welcome. Please open an issue for bugs or feature requests and submit a PR with tests where practical.

License

Specify a license (e.g., MIT) in `LICENSE` if you want this project to be open source.




