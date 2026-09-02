# Software Requirements Specification

**Project:** AI-Powered Job Aggregator and Application Tracker
**Document standard:** IEEE 830-1998 SRS outline
**Prepared for:** IGNOU MCAOL Project (MCSP-232)
**Author:** Vanshita Jain
**Date:** 2026-08-30

> Every functional requirement, endpoint signature, and data constraint in
> this document was verified directly against the code in this repository
> (models in `app/models/`, routes in `app/api/v1/`, services in
> `app/services/`) rather than written from the intended design. Where the
> implementation diverges from what would normally be assumed — a missing
> constraint, an endpoint that behaves differently than its name suggests —
> that divergence is called out explicitly rather than smoothed over. See
> `PROJECT_SYNOPSIS.md` §9-10 for the underlying DDL/module audit this
> document is built on.

---

## Table of Contents

1. Introduction
   - 1.1 Purpose
   - 1.2 Scope
   - 1.3 Definitions, Acronyms, Abbreviations
   - 1.4 References
   - 1.5 Overview
2. Overall Description
   - 2.1 Product Perspective
   - 2.2 Product Functions
   - 2.3 User Characteristics
   - 2.4 Constraints
   - 2.5 Assumptions and Dependencies
3. Specific Requirements
   - 3.1 External Interface Requirements
   - 3.2 Functional Requirements (by module, with real endpoint contracts)
   - 3.3 Performance Requirements
   - 3.4 Design Constraints
   - 3.5 Software System Attributes
4. Data Requirements
5. Appendix A — Known Deviations From Idealized Behaviour

---

## 1. Introduction

### 1.1 Purpose

This SRS specifies the functional and non-functional requirements of the
Jobs Aggregator system as **actually implemented**, for use as the
requirements-traceability reference in the IGNOU MCSP-232 project
submission. Unlike a pre-implementation SRS, every requirement below is
backed by a route, model field, or service function that exists in the
codebase today.

### 1.2 Scope

The system aggregates job listings from Indeed, LinkedIn, and Hirist,
lets a user track application status per listing, stores CV documents in
Google Cloud Storage, and generates AI-authored CV tailoring tips via a
user-selectable LLM provider. It is a single-tenant, self-hosted
application (one FastAPI process, one SQLite file, one Redis broker) — not
a multi-tenant SaaS.

### 1.3 Definitions, Acronyms, Abbreviations

| Term | Meaning |
|------|---------|
| Designation | A job-role title (e.g. "Backend Engineer") that jobs and user subscriptions are organised around |
| UserJob | The per-user application-status record for one Job |
| External job | A job created via `POST /jobs/add` (pasted URL) rather than the scraper, flagged `is_external=true` |
| Unseen feed | The default `GET /jobs` response: jobs under the user's subscribed designations with no `UserJob` row yet |
| JWT | JSON Web Token, used as the bearer credential for all authenticated routes |

### 1.4 References

- `app/models/*.py` — SQLModel table definitions (schema ground truth)
- `app/api/v1/*.py` — FastAPI route definitions (endpoint ground truth)
- `app/services/*.py` — business logic
- `PROJECT_SYNOPSIS.md` — DFDs, ER diagram, module structure, DDL audit
- `tests/` — executable pytest suite doubling as behavioural specification

### 1.5 Overview

Section 2 describes the product at a high level. Section 3 gives the
concrete, per-endpoint functional requirements — this is the part meant to
be checked mechanically against the code (and is, by the test suite in
`tests/`). Section 4 covers data requirements. Section 5 lists places
where the system's actual behaviour is worth knowing precisely because it
is *not* what a reader would assume from the feature description alone.

---

## 2. Overall Description

### 2.1 Product Perspective

Standalone full-stack web application: FastAPI backend (`app/`), React SPA
frontend (`frontend/react-app/`), Celery+Redis for asynchronous scraping,
SQLite for persistence, GCS for CV file storage, and four pluggable LLM
providers (Groq/OpenAI/Anthropic/Gemini) for AI features. No requirement in
this document depends on functionality outside this repository.

### 2.2 Product Functions

1. User registration/login (JWT-based).
2. Designation creation and per-user subscription.
3. Daily and on-demand scraping of job listings across three portals.
4. Manual ingestion of a single job from any URL (native parser for the
   three supported portals, LLM-extraction fallback for anything else).
5. Personalised, keyword-filtered job feed with per-status views.
6. CV upload (PDF/DOCX/TXT), storage, download, deletion, and text
   extraction.
7. AI-generated CV tailoring tips against a specific job.

### 2.3 User Characteristics

Single user class: a job-seeker managing their own applications. There is
no admin role exercised anywhere in the API despite `User.is_superuser`
existing on the model (see §5).

### 2.4 Constraints

- SQLite is single-writer; concurrent scrape-writes and API writes share
  one file (`jobs.db`).
- Playwright-based scraping (`fetch_page_with_browser`) requires a real
  Chromium install and, per `PLAYWRIGHT_HEADLESS=False` default, a
  display unless overridden.
- LinkedIn and Hirist scraping depend on portal DOM structure that can
  change without notice — `parsers.py`/`external_ingestion.py` selectors
  are hard-coded CSS selectors, not resilient to markup changes.

### 2.5 Assumptions and Dependencies

- A valid `SECRET_KEY` and `DATABASE_URL` exist in `.env` at process start
  (`app/core/config.py` has no defaults for either — the process fails to
  start without them).
- At least one LLM provider API key is available to the user for CV tips
  and unsupported-portal ingestion (Groq has a server-side fallback key;
  the other three do not).

---

## 3. Specific Requirements

### 3.1 External Interface Requirements

- **User interface:** React 18 SPA, served by Vite dev server on `:3000`
  in development.
- **API interface:** REST/JSON over HTTP, FastAPI app mounted at
  `/api/v1`, documented automatically at `/docs` (FastAPI's built-in
  OpenAPI UI — not a hand-written API doc).
- **Auth interface:** OAuth2 password flow (`OAuth2PasswordBearer`,
  `tokenUrl="/api/v1/auth/login"`); all protected routes expect
  `Authorization: Bearer <jwt>`.
- **LLM interface:** provider selected per-request via `X-Llm-Provider`
  header, key via `X-Llm-Key` header — never persisted server-side.
- **Storage interface:** Google Cloud Storage, accessed only via V4 signed
  URLs from the browser, or server-side download for text extraction.

### 3.2 Functional Requirements

Each requirement below states the endpoint, its real request/response
contract, and its actual authorization/error behaviour.

#### FR-1 — User Registration

`POST /api/v1/auth/register` — public.
Request: `{email, password, full_name}`.
Response `200`: `UserRead` (`id, email, full_name, is_active, is_superuser, last_login, created_at, updated_at` — `hashed_password` excluded).
Side effect: the new user is subscribed (`UserDesignation` rows created)
to **every `Designation` that exists at the moment of registration**. A
designation created afterward is not retroactively subscribed.

#### FR-2 — Login

`POST /api/v1/auth/login` — public, OAuth2 form body (`username`, `password`).
Response `200`: `{access_token, token_type: "bearer"}`. Token expires in
60 minutes (`create_access_token`, hard-coded `timedelta(minutes=60)`).
Response `401` on unknown email or wrong password (`login_user` returns
`None` for either, which the route maps to a single 401 — a client cannot
distinguish "no such account" from "wrong password" from the response
alone).

#### FR-3 — Current User

`GET /api/v1/auth/users/me` — authenticated.
Response `200`: `UserRead` for the token's subject. `401` if the token is
missing/invalid, or if `user.is_active` is false.

#### FR-4 — Designation Create/List

`POST /api/v1/designation` — authenticated. Body: `{title}`.
`400` if a `Designation` with the same title already exists (service-layer
check, not a DB constraint — see §5).
`GET /api/v1/designation` — **public**, no auth dependency.

#### FR-5 — Designation Subscription

`POST /api/v1/user-designation` — authenticated. Body: `{designation_id}`.
`400` if the designation doesn't exist or the user is already subscribed.
`GET /api/v1/user-designation` — authenticated, lists the caller's own subscriptions.
`DELETE /api/v1/user-designation?user_designation_id=` — authenticated;
`400` if the row doesn't belong to the caller (returned as an error, not a 404).

#### FR-6 — Job Feed

`GET /api/v1/jobs?status=<optional>` — authenticated.
Without `status`: returns jobs under the user's subscribed designations
with no `UserJob` row yet, newest-first, each annotated `is_new` (true if
`created_at` is within `NEW_JOB_THRESHOLD_HOURS`, default 24h), with any
`UserJobPreference`-excluded keyword filtered out of the title (hyphen/space
-normalised whole-word match).
With `status`: returns jobs joined to a `UserJob` row at exactly that
status for the caller, each annotated `user_job_id`/`user_status`. **This
path also requires the user to be subscribed to the job's designation** —
a `UserJob` row alone is not sufficient (see §5).

#### FR-7 — On-Demand Scrape

`POST /api/v1/jobs/fetch-new` — authenticated. Dispatches one
`job_fetching_task_designation.delay(designation_id=...)` Celery task per
designation the caller is subscribed to, and returns immediately —
scraped jobs appear asynchronously on a later `GET /jobs` call, not in
this response.

#### FR-8 — Manual Job Ingestion

`POST /api/v1/jobs/add` — authenticated. Body: `{url, designation_id, status?}`.
Indeed URLs are canonicalised (`viewjob?jk=<id>`) before the duplicate
check. If `source_url` already exists, returns the existing job with
`is_new: false` and performs no fetch/LLM call. Otherwise: native parser
for indeed/linkedin/hirist, LLM-extraction fallback otherwise; `422` if no
title could be extracted; `502` on fetch/parse failure. On success, `Job`
is created with `is_external=true`, visible to **every** user subscribed
to `designation_id`, not only the caller. If `status` is supplied, a
`UserJob` is also created for the caller at that status.

#### FR-9 — Job Description Fetch

`GET /api/v1/jobs/{job_id}/description` — authenticated. Returns
`{description}`; if empty in the DB, fetches from source
(`fetch_job_description`, portal-specific) and caches the result on the
`Job` row for subsequent calls. `404` for an unknown `job_id`.

#### FR-10 — Application Status Update

`POST /api/v1/user-jobs` — authenticated. Body: `{job_id, status}` where
`status` must be one of `saved|applied|interviewed|rejected|irrelevant`
(`422` otherwise, Pydantic-level validation only — see §5). Upserts on
`(user_id, job_id)`: a second call for the same job moves the existing row
to the new status rather than creating a duplicate.

#### FR-11 — Keyword Exclusion

`POST /api/v1/user-job-preferences` — authenticated. Body:
`{keyword, is_excluded}`. `201` on success. No update/delete endpoint
exists for preferences as of this writing — only create.

#### FR-12 — CV Upload URL

`GET /api/v1/cvs/upload-url?filename=&content_type=` — authenticated.
`400` if the extension is not pdf/docx/txt. Returns a signed GCS PUT URL
plus a `gcs_path` scoped as `cvs/user_{id}/{uuid}.{ext}`.

#### FR-13 — CV Registration

`POST /api/v1/cvs` — authenticated, after the client has PUT the file to
the signed URL. Body: `{name, gcs_path, user_job_id?}`. Backend downloads
the object from GCS server-side and extracts text (`extract_text`); `502`
if the download fails, `422` if extraction fails. Response excludes the
extracted text.

#### FR-14 — CV List / Download / Delete

`GET /api/v1/cvs` — lists the caller's CVs, each with `job_title`/
`job_company` populated via a join through `UserJob` when `user_job_id` is
set. `GET /api/v1/cvs/{id}/download` — `404` if the CV isn't the caller's,
else a signed GET URL. `DELETE /api/v1/cvs/{id}` — removes the DB row;
GCS deletion failures are swallowed (the row is still deleted even if the
object can't be removed from the bucket).

#### FR-15 — AI CV Tips

`POST /api/v1/cvs/{cv_id}/tips/{job_id}` — authenticated, `X-Llm-Provider`/
`X-Llm-Key` headers. `404` if the CV or job isn't found; `422` if the CV
has no extracted text; `502` on LLM failure. If the job is an Indeed
listing with no cached description yet, the description is opportunistically
fetched and cached before the LLM call (this auto-fetch is Indeed-only;
LinkedIn/Hirist jobs are sent to the LLM without a description if one
hasn't already been fetched via FR-9).

### 3.3 Performance Requirements

No load testing has been performed; the following are design targets, not
measured SLAs:
- Interactive read endpoints (`GET /jobs`, `GET /cvs`, `GET /designation`)
  should respond within 2 seconds under normal single-user load.
- Scraping and LLM calls are always asynchronous (Celery) or client-await
  (LLM tip generation can legitimately take several seconds; no timeout is
  enforced on the FastAPI side beyond the underlying HTTP client defaults).

### 3.4 Design Constraints

- SQLite only — no requirement assumes a networked RDBMS.
- No pagination on any list endpoint (`GET /jobs`, `GET /cvs`,
  `GET /designation`, `GET /user-designation` all return full result sets).
- No rate limiting on any endpoint.

### 3.5 Software System Attributes

- **Security:** PBKDF2-SHA256 password hashing (`passlib`); JWT bearer
  auth with 60-minute expiry; CORS restricted to `http://localhost:3000`;
  CV access scoped by `user_id` ownership checks in every CV route.
- **Reliability:** Celery tasks retry up to 3 times with backoff on
  uncaught exceptions; a single designation's scrape failure inside
  `job_fetching_task`/`job_fetching_task_designation` is caught and logged
  without aborting the others.
- **Maintainability:** Layered structure (route → service → model);
  Google-style docstrings on service/route functions describing
  parameters, return shape, and error conditions.
- **Testability:** `tests/` provides a runnable pytest suite (43 tests)
  covering every endpoint listed in §3.2, using a throwaway SQLite DB per
  test and monkeypatched external services.

---

## 4. Data Requirements

See `PROJECT_SYNOPSIS.md` §8 (Data Dictionary) and §9.1 (actual DDL,
pulled directly from `sqlite3 jobs.db ".schema"`) for the authoritative
table-by-table field list. Two data-integrity facts worth stating here
because they affect how any future feature must be built:

- `Job.designation_id` has no foreign-key constraint — validate a
  designation's existence in application code before relying on it, never
  assume the database will reject a dangling reference.
- SQLite foreign-key enforcement is off process-wide (no
  `PRAGMA foreign_keys = ON` anywhere) — every declared FK in every table
  is advisory. Any future migration to Postgres would need to add explicit
  `ON DELETE` behaviour, since none exists to carry over.

---

## 5. Appendix A — Known Deviations From Idealized Behaviour

These are not bugs to be silently designed around — they are the actual,
current behaviour, listed here so a reader building on this system doesn't
assume stricter guarantees than exist:

1. `Designation.title` uniqueness is enforced only in application code
   (`create_designation`'s pre-insert `SELECT`), not by the database — a
   race between two concurrent requests could create duplicate titles.
2. `UserJob.status` is a free-form string column with no DB `CHECK`
   constraint; only the `UserJobCreateUpdate` Pydantic schema restricts
   values to the `JobStatus` enum at the API boundary. Any code that
   writes to `UserJob` outside that one endpoint would not be blocked from
   writing an arbitrary string.
3. The status-filtered job feed (`GET /jobs?status=`) additionally
   requires the caller to be subscribed to the job's designation via
   `UserDesignation` — a `UserJob` row by itself is not enough to make a
   job appear under a status tab. `POST /user-jobs` itself has no such
   check, so it is possible to mark a job's status without being able to
   see it afterward under that tab.
4. `POST /auth/login` returns an identical `401` for "no such user" and
   "wrong password" — this is a reasonable security choice (avoids
   user-enumeration) but is stated here because it means client-side
   error messages cannot be more specific without a backend change.
5. Two dead-code paths exist and should not be assumed live: the
   Groq-only `app/services/cv_tips.py::get_cv_tips` (superseded by
   `app/services/llm.py::get_cv_tips`), and
   `app/services/user_job.py::fetch_job_records` (superseded by
   `app/services/jobs.py::fetch_job_records`).
