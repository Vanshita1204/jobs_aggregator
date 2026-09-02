# PROJECT SYNOPSIS

---

**Title of the Project:**
AI-Powered Job Aggregator and Application Tracker

**Student Name:** Vanshita Jain
**Enrolment No.:** *(to be filled)*
**Email:** vanshitajain1204@gmail.com
**Programme:** Master of Computer Applications — Online (MCAOL)
**Course Code:** MCSP-232
**Institution:** IGNOU, School of Computer and Information Sciences

---

## Table of Contents

1. Introduction and Objectives
2. Project Category
3. Tools / Platform, Hardware & Software Requirements
4. Problem Definition, Requirement Specifications and Literature Review
   - 4.1 Literature Review
   - 4.2 Problem Definition
   - 4.3 Functional Requirements
   - 4.4 Non-Functional Requirements
5. Project Planning and Scheduling (Gantt Chart, PERT Chart, Cost Estimation)
6. Scope of the Solution
7. Analysis Diagrams
   - 7.1 DFD Level 0 (Context Diagram)
   - 7.2 DFD Level 1
   - 7.3 DFD Level 2 (Job Aggregation)
   - 7.4 ER Diagram with Cardinality
   - 7.5 Activity Diagram
   - 7.6 Class Diagram
   - 7.7 State Diagram
8. Data Dictionary
9. Complete Database Design and Normalization (3NF)
   - 9.1 Actual DDL
   - 9.2 Referential Integrity — what's actually enforced
   - 9.3 Normalization
10. Project Structure – Modules, Data Structures, Implementation Methodology, Expected Reports
    - 10.5 Automated Test Suite
    - 10.6 Test Case Log
11. Software Engineering Paradigm and Coding Standards
12. Network Architecture
13. Security Mechanisms
14. Future Scope and Enhancements
15. Bibliography (IEEE Format)

---

## 1. Introduction and Objectives

### 1.1 Introduction

The modern job-search process is fragmented and time-consuming. A job-seeker must visit multiple portals (Indeed, LinkedIn, Hirist, etc.), manually track which listings have been viewed or applied to, keep multiple CV versions, and tailor each application individually — all without a unified dashboard. This project, the **AI-Powered Job Aggregator and Application Tracker**, solves that problem by building a full-stack web application that:

- Automatically scrapes fresh job listings from major portals on a daily schedule.
- Lets users manually add any job by pasting its URL.
- Provides a single, filterable feed of relevant listings personalized to each user's target designations.
- Tracks application status (saved → applied → interviewed → rejected / irrelevant) per job.
- Manages multiple CV versions stored securely in Google Cloud Storage.
- Leverages Large Language Models (LLMs) to analyse a user's CV against a specific job description and return targeted, line-referenced improvement suggestions.

The system is built around a **FastAPI** backend, a **React** frontend, a **Celery + Redis** task queue for asynchronous scraping, and **SQLite** as the persistent store. LLM integration is provider-agnostic, supporting Groq (default), OpenAI, Anthropic, and Google Gemini.

### 1.2 Objectives

| # | Objective |
|---|-----------|
| 1 | Build a multi-source job scraper that reliably fetches listings from Indeed, LinkedIn, and Hirist despite bot-detection mechanisms. |
| 2 | Persist scraped data in a relational database and deduplicate listings by canonical URL. |
| 3 | Provide per-user, per-designation job feeds that hide already-actioned listings. |
| 4 | Implement full application lifecycle tracking with status management. |
| 5 | Allow secure upload, storage, and retrieval of CV documents (PDF / DOCX / TXT) via Google Cloud Storage. |
| 6 | Integrate an AI/LLM layer to extract job data from unstructured web pages and to generate personalised CV-improvement tips. |
| 7 | Expose a RESTful API secured with JWT authentication and a React-based single-page application as the user interface. |
| 8 | Schedule automated daily scraping using Celery Beat so that the database stays current without user intervention. |

---

## 2. Project Category

**Primary Category:** Artificial Intelligence (AI) / Web Application

**Sub-categories:**
- AI / LLM Integration (CV analysis, unstructured-page extraction)
- Web Scraping / Data Aggregation
- RDBMS (relational database design in SQLite)
- Cloud Computing (Google Cloud Storage for CV files)
- Distributed Systems (Celery + Redis asynchronous task queue)

The project involves substantive software development across backend API engineering, frontend UI, database design, automated scheduling, cloud storage, and AI integration — satisfying the IGNOU requirement for a project with real software-development components.

---

## 3. Tools / Platform, Hardware & Software Requirements

### 3.1 Software Requirements

| Component | Technology / Version |
|-----------|----------------------|
| Programming Language | Python 3.11+ |
| Backend Framework | FastAPI 0.111+ |
| ORM | SQLModel 0.0.18+ (wraps SQLAlchemy + Pydantic v2) |
| Database | SQLite 3 (file-based, zero-config) |
| Task Queue (broker) | Redis 7+ |
| Task Queue (worker/beat) | Celery 5.3+ |
| Web Scraping – TLS bypass | curl_cffi 0.7+ (Chrome TLS fingerprint impersonation) |
| Web Scraping – JS rendering | Playwright (Python) 1.44+ |
| HTML Parsing | BeautifulSoup4 4.12+ |
| HTTP Client | requests 2.31+, httpx |
| Authentication | PyJWT 2.8+, PBKDF2-SHA256 (via hashlib) |
| AI / LLM – Default | Groq Python SDK (llama-3.3-70b-versatile) |
| AI / LLM – Optional | openai SDK (gpt-4o-mini), anthropic SDK (claude-opus-4-6), google-generativeai (gemini-1.5-flash) |
| CV Text Extraction | pdfplumber (PDF), python-docx (DOCX) |
| Cloud Storage | Google Cloud Storage (GCS) Python client library |
| Frontend Framework | React 18 + Vite 5 |
| Frontend Language | JavaScript (ES2022, no TypeScript) |
| Package Manager | pip (Python), npm (JavaScript) |
| Containerisation | Docker + Docker Compose (optional) |
| OS | macOS / Linux / Windows (WSL2 recommended) |

### 3.2 Hardware Requirements

| Resource | Minimum | Recommended |
|----------|---------|-------------|
| CPU | Dual-core 2 GHz | Quad-core 2.5 GHz+ |
| RAM | 4 GB | 8 GB+ |
| Disk (application + DB) | 2 GB | 10 GB+ |
| Network | Broadband (for scraping + LLM API calls) | Stable broadband |

### 3.3 Platform / IDE

- **IDE:** Visual Studio Code / PyCharm
- **Browser:** Chrome / Firefox (for Playwright headless mode)
- **Version Control:** Git + GitHub
- **API Testing:** REST clients (curl / Postman)

### 3.4 Third-party Services (API Keys Required)

| Service | Purpose |
|---------|---------|
| Groq Cloud | Default LLM (free tier available) |
| OpenAI API | Optional LLM provider |
| Anthropic API | Optional LLM provider |
| Google Gemini API | Optional LLM provider |
| Google Cloud Storage | CV file storage (GCS bucket) |

---

## 4. Problem Definition, Requirement Specifications and Literature Review

### 4.1 Literature Review

Several tools exist in the job-search ecosystem, but none fully address the aggregation-plus-tracking-plus-AI-advice combination:

| Existing Tool | What It Does | Limitation |
|--------------|-------------|-----------|
| Indeed / LinkedIn / Hirist | Job posting portals | Siloed; no cross-portal view; no application tracking |
| Huntr / Trello (manual boards) | Application tracking via Kanban cards | Manual data entry; no scraping; no AI analysis |
| Resumake / Rezi | CV builder with keyword hints | No job feed; no portal scraping; no status tracking |
| Simplify (browser extension) | Auto-detects and saves jobs from portals | Extension only; no central backend; no AI CV tips |
| LinkedIn Easy Apply | One-click apply on LinkedIn | LinkedIn-only; no aggregation; no post-apply tracking |

**Research gap:** No single open-source, self-hosted tool combines (a) multi-portal automated scraping, (b) full application lifecycle management, and (c) LLM-based, context-aware CV tailoring against actual job descriptions. This project fills that gap.

Key technical areas referenced during development:

- **Web scraping resilience:** TLS fingerprinting bypass (curl_cffi, chrome131 impersonation) as documented in the curl_cffi project [5].
- **AI for recruitment:** LLM-powered CV screening and job-matching have been explored in academic literature (e.g., Qin et al., 2023, "RecruitPro: An LLM-Based Framework for Automated Resume-to-Job Matching").
- **Task queues:** Celery + Redis async architecture follows patterns in Massé (2011), "REST API Design Rulebook", O'Reilly.
- **Secure file storage:** GCS signed URL pattern follows Google Cloud documentation [12].

### 4.3 Problem Definition

Job seekers using multiple portals face several pain points:

1. **Information overload:** Listings repeat across portals; no single aggregated view exists.
2. **Manual tracking:** Application status (applied, interviewed, rejected) is tracked in spreadsheets or memory.
3. **CV management:** Maintaining and tailoring multiple CV versions is error-prone.
4. **Relevance filtering:** Portals show listings for irrelevant roles (e.g., intern positions when seeking senior roles).
5. **Stale data:** Job listings disappear or close; manual checking is tedious.
6. **Missed opportunities:** Without a daily check, new listings are discovered late.

### 4.4 Functional Requirements

| FR # | Description |
|------|-------------|
| FR-1 | Users shall register with email + password; login returns a JWT. |
| FR-2 | Authenticated users shall create / browse Designations (target job titles). |
| FR-3 | Users shall subscribe to one or more Designations. |
| FR-4 | The system shall scrape Indeed, LinkedIn, and Hirist daily and store de-duplicated listings. |
| FR-5 | Users shall trigger on-demand scraping for their designated roles. |
| FR-6 | Users shall view a personalised, status-filtered job feed (unseen / saved / applied / etc.). |
| FR-7 | Users shall mark jobs with statuses: saved, applied, interviewed, rejected, irrelevant. |
| FR-8 | Users shall define keyword exclusions (e.g., "intern") to hide unwanted listings. |
| FR-9 | Users shall manually add a job by pasting a URL from any supported or unsupported portal. |
| FR-10 | Users shall upload CV files (PDF/DOCX/TXT) to GCS via secure signed URLs. |
| FR-11 | Users shall link a CV to a specific job application. |
| FR-12 | Users shall request AI-generated CV improvement tips for a specific job. |
| FR-13 | Users shall select their preferred LLM provider and supply their own API key. |
| FR-14 | Jobs added via the UI shall be flagged as external (purple badge). |
| FR-15 | Job descriptions shall be fetched on demand and cached in the database. |

### 4.5 Non-Functional Requirements

| NFR # | Description |
|-------|-------------|
| NFR-1 | API response time < 2 seconds for read operations under normal load. |
| NFR-2 | Passwords shall be stored using PBKDF2-SHA256; never in plaintext. |
| NFR-3 | JWTs shall expire in 60 minutes. |
| NFR-4 | CV files shall be accessible only via time-limited signed GCS URLs. |
| NFR-5 | Scraping tasks shall run asynchronously; they shall not block API responses. |
| NFR-6 | The system shall deduplicate jobs at the database layer using a UNIQUE constraint on source_url. |
| NFR-7 | The React SPA shall be responsive and functional on standard desktop resolutions. |

---

## 5. Project Planning and Scheduling

### 5.1 Work Breakdown Structure (Tasks)

| Task ID | Task | Duration |
|---------|------|----------|
| T1 | Requirements Analysis & System Design | 1 week |
| T2 | Database Schema Design | 1 week |
| T3 | Authentication Module (register / login / JWT) | 1 week |
| T4 | Core Data Models (User, Job, Designation, UserJob) | 1 week |
| T5 | Job Scraping – Indeed (curl_cffi) | 1.5 weeks |
| T6 | Job Scraping – LinkedIn & Hirist (Playwright) | 1.5 weeks |
| T7 | Celery + Redis Task Queue Integration | 1 week |
| T8 | Job Listing & Status API Endpoints | 1 week |
| T9 | CV Upload Module (GCS integration) | 1.5 weeks |
| T10 | LLM Integration (multi-provider) | 1 week |
| T11 | External Job Ingestion (URL paste + LLM fallback) | 1 week |
| T12 | React Frontend – Auth & Navigation | 1 week |
| T13 | React Frontend – Jobs Feed & Status Management | 2 weeks |
| T14 | React Frontend – CV Manager | 1 week |
| T15 | React Frontend – AI Tips Modal | 0.5 weeks |
| T16 | Integration Testing & Bug Fixes | 1.5 weeks |
| T17 | Documentation & Synopsis Writing | 1 week |

**Total Project Duration: ~18 weeks**

### 5.2 Gantt Chart (Text Representation)

```
Week:  1   2   3   4   5   6   7   8   9  10  11  12  13  14  15  16  17  18
T1   [===]
T2       [===]
T3       [===]
T4           [===]
T5               [====]
T6               [====]
T7                   [===]
T8                       [===]
T9                       [====]
T10                          [===]
T11                              [===]
T12                          [===]
T13                              [========]
T14                                      [===]
T15                                          [=]
T16                                          [====]
T17                                              [===]
```

### 5.3 PERT Chart (Critical Path)

```
START → T1 → T2 → T3 → T4 → T5 → T7 → T8 → T11 → T16 → T17 → END
                           ↓         ↑
                          T6 ────────┘
                  T4 → T9 → T10 ──────────────────────→ T16
                  T4 → T12 → T13 → T14 → T15 ──────→ T16
```

**Critical Path:** T1 → T2 → T4 → T5 → T7 → T8 → T11 → T13 → T16 → T17

**Critical Path Duration:** ~14 weeks

### 5.4 Cost Estimation (Function Point Analysis)

Function Point (FP) analysis is used to estimate project size and effort.

**Counting Function Points:**

| Component Type | Count | Complexity | Unadjusted FP |
|---------------|-------|-----------|--------------|
| External Inputs (user forms, API requests) | 12 | Average (4) | 48 |
| External Outputs (job feed, CV list, tips) | 8 | Average (5) | 40 |
| External Inquiries (GET endpoints) | 10 | Average (4) | 40 |
| Internal Logical Files (DB tables: 7) | 7 | Average (10) | 70 |
| External Interface Files (GCS, LLM APIs) | 5 | Average (7) | 35 |
| **Total Unadjusted Function Points (UFP)** | | | **233** |

**Value Adjustment Factor (VAF):** Complexity adjustment using 14 general system characteristics rated 0–5 each. Estimated VAF = 1.10 (moderate complexity: distributed processing, heavy end-user efficiency requirements, online updates).

**Adjusted FP = UFP × VAF = 233 × 1.10 = ~256 FP**

**Effort Estimation (Jones' Rule of Thumb):** Effort (person-months) ≈ FP^0.4 = 256^0.4 ≈ **10–12 person-months** for a team; approximately **6 months** for a single full-stack developer (student project context), which aligns with the IGNOU project calendar.

---

## 6. Scope of the Solution

### 6.1 In Scope

1. **Multi-source scraping:** Indeed, LinkedIn, and Hirist job portals.
2. **User personalisation:** Designation-based filtering; keyword exclusions; per-user application status tracking.
3. **Application lifecycle management:** Five statuses covering the full hiring funnel.
4. **CV storage and retrieval:** GCS-backed secure storage with text extraction.
5. **AI-powered CV analysis:** Multi-provider LLM integration (Groq, OpenAI, Anthropic, Gemini) for targeted improvement tips.
6. **Manual job ingestion:** URL-paste flow with LLM fallback for unknown portals.
7. **Automated scheduling:** Daily Celery Beat task to refresh listings.
8. **REST API:** Fully documented, JWT-secured, CORS-enabled FastAPI backend.
9. **SPA frontend:** React 18 + Vite with real-time status updates and modal flows.

### 6.2 Out of Scope

- Email / push notification on new listings.
- Mobile application (iOS / Android).
- Browser extension for one-click job saving.
- Interview scheduling or calendar integration.
- Job application auto-filling (RPA).
- Multi-tenant SaaS deployment (the project is self-hosted).
- Paid job-portal API integrations (e.g., LinkedIn Jobs API).

---

## 7. Analysis Diagrams

### 7.1 Data Flow Diagram – Level 0 (Context Diagram)

```
                    ┌──────────────────────────────────┐
                    │                                  │
   ┌─────────┐      │    AI-Powered Job Aggregator     │      ┌──────────────────┐
   │  User   │◄────►│       and Application            │◄────►│  Job Portals     │
   │(Browser)│      │         Tracker                  │      │(Indeed/LinkedIn/ │
   └─────────┘      │                                  │      │     Hirist)      │
                    └──────────────────────────────────┘      └──────────────────┘
                                     │
                                     ▼
                             ┌───────────────┐
                             │  LLM Providers│
                             │(Groq/OpenAI/  │
                             │Anthropic/     │
                             │Gemini)        │
                             └───────────────┘
                                     │
                                     ▼
                             ┌───────────────┐
                             │ Google Cloud  │
                             │   Storage     │
                             └───────────────┘
```

**External Entities:**
- **User (Browser):** Registers, logs in, views jobs, manages CVs, requests AI tips.
- **Job Portals:** Indeed, LinkedIn, Hirist — data sources for job listings.
- **LLM Providers:** Groq, OpenAI, Anthropic, Gemini — AI inference endpoints.
- **Google Cloud Storage:** Object store for CV files.

---

### 7.2 Data Flow Diagram – Level 1

```
                          ┌────────────────────────────────────────┐
                          │              System                    │
   User ──login/register─►│ 1. Auth Module        ──JWT──►  User  │
                          │                                        │
   User ──fetch jobs─────►│ 2. Job Aggregation    ──job list─► User│
                          │    Module                              │
   Portals ──HTML────────►│      2.1 Scraper                      │
                          │      2.2 Parser                        │
                          │      2.3 Deduplicator ──jobs──► DB     │
                          │      2.4 Scheduler (Celery Beat)       │
                          │                                        │
   User ──update status──►│ 3. Application        ──status──► DB  │
   User ──view statuses──►│    Tracking Module    ──jobs──► User  │
                          │                                        │
   User ──upload CV──────►│ 4. CV Management      ──file──► GCS   │
                          │    Module             ──meta──► DB     │
                          │                                        │
   User ──CV+Job ID──────►│ 5. AI Analysis        ──prompt──►LLM  │
                          │    Module             ◄─tips────LLM   │
                          │                       ──tips──► User  │
                          │                                        │
   User ──paste URL──────►│ 6. Manual Ingestion   ──fetch──►Portal│
                          │    Module             ──parse──► DB    │
                          └────────────────────────────────────────┘
```

---

### 7.3 Data Flow Diagram – Level 2: Job Aggregation Module (Process 2)

```
 ┌────────────┐    designation   ┌─────────────────┐   query   ┌────────────┐
 │Celery Beat │─────────────────►│ 2.1 Fetch        │──────────►│  Job DB   │
 │(Scheduler) │                 │ Orchestrator     │           └────────────┘
 └────────────┘                 └────────┬─────────┘
                                         │ source+URL list
              ┌──────────────────────────┼──────────────────────┐
              ▼                          ▼                       ▼
   ┌──────────────────┐    ┌──────────────────────┐   ┌─────────────────┐
   │2.2 cffi Fetcher  │    │2.3 Playwright Fetcher │   │2.4 HTTP Fetcher │
   │(Indeed only)     │    │(LinkedIn, Hirist)     │   │(fallback)       │
   └────────┬─────────┘    └──────────┬────────────┘   └────────┬────────┘
            │ raw HTML                │ raw HTML                 │ raw HTML
            └──────────────┬──────────┘                          │
                           ▼                                     │
              ┌────────────────────────┐                         │
              │  2.5 HTML Parser       │◄────────────────────────┘
              │  (BeautifulSoup4)      │
              │  parse_indeed_jobs()   │
              │  parse_linkedin_jobs() │
              │  parse_hirist_jobs()   │
              └──────────┬─────────────┘
                         │ list[dict]
                         ▼
              ┌────────────────────────┐
              │  2.6 Deduplicator      │
              │  create_job_records()  │
              │  - in-memory URL set   │
              │  - DB IN-query         │
              │  - batch INSERT        │
              └──────────┬─────────────┘
                         │ new Job rows
                         ▼
                  ┌─────────────┐
                  │  Job DB     │
                  └─────────────┘
```

---

### 7.4 Entity-Relationship (ER) Diagram with Cardinality

```
┌──────────┐         ┌─────────────────┐         ┌─────────────┐
│  User    │         │ UserDesignation  │         │ Designation │
│──────────│         │─────────────────│         │─────────────│
│ PK id    │1──────M│ PK id            │M──────1 │ PK id       │
│ email    │         │ FK user_id       │         │ title       │
│ full_name│         │ FK designation_id│         │ FK created_by│
│ hashed_  │         └─────────────────┘         │  (→ User)   │
│ password │                                     │ created_at  │
│ is_active│                                     │ updated_at  │
│ is_super-│                                     └──────┬──────┘
│  user    │                                            ┊ 1
│ last_login│                                           ┊  (job.designation_id
│ created_at│                                           ┊   has NO db-level FK
│ updated_at│                                           ┊   — see §9.2)
└────┬──────┘                                           ┊ M
     │ 1                                         ┌──────┴──────┐
     │                                           │    Job      │
     │ M                                         │─────────────│
     │                                           │ PK id       │
┌────┴──────────┐                                │ title       │
│   UserJob     │                                │ company     │
│───────────────│                                │ location    │
│ PK id         │M┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈1│ description │
│ FK user_id    │  (job_id IS a declared FK;      │ source      │
│ FK job_id     │   dotted only because SQLite    │ source_url  │
│ status (str)  │   never enforces it — §9.2)     │ (UNIQUE)    │
│ notes         │                                │ designation_id│
│ created_at    │                                │  (indexed, not FK'd)│
│ updated_at    │                                │ is_external │
└────┬──────────┘                                │ created_at  │
     │ 1                                         │ updated_at  │
     │                                           └─────────────┘
     │ M
┌────┴──────────┐
│  UserCV       │
│───────────────│
│ PK id         │
│ FK user_id ──►│── User (1:M)
│ name          │
│ gcs_path      │
│ extracted_text│
│ FK user_job_id│(nullable)
│ created_at    │
│ updated_at    │
└───────────────┘

┌────────────────────┐
│ UserJobPreference  │
│────────────────────│
│ PK id              │
│ FK user_id ───────►│── User (1:M)
│ keyword            │
│ is_excluded (bool) │
│ created_at         │
│ updated_at         │
└────────────────────┘
```

Dotted (`┈`) edges mark relationships with a real `FOREIGN KEY` clause in
the DDL that SQLite still never enforces at runtime (no
`PRAGMA foreign_keys = ON`, confirmed on the live DB). The
`Designation → Job` edge is the one relationship with **no FK clause at
all** — `Job.designation_id` is a plain indexed column. Both facts are
detailed in §9.2.

**Cardinalities Summary:**

| Relationship | Type | DB-level FK declared? |
|-------------|------|:---:|
| User : Designation (created_by) | 1 : M | Yes |
| User : UserDesignation | 1 : M | Yes |
| Designation : UserDesignation | 1 : M | Yes |
| Designation : Job | 1 : M | **No** |
| User : UserJob | 1 : M | Yes |
| Job : UserJob | 1 : M | Yes |
| UserJob : UserCV | 1 : M (nullable FK) | Yes |
| User : UserCV | 1 : M | Yes |
| User : UserJobPreference | 1 : M | Yes |

"Declared" means present in the DDL; none of them are enforced by SQLite
at runtime (§9.2).

---

### 7.5 Activity Diagram – Job Application Flow

```
  User Opens Jobs Feed
         │
         ▼
  [View Unseen Jobs]
         │
         ▼
  <Job Relevant?> ──No──► [Mark Irrelevant] ──► Feed Updated
         │
        Yes
         │
         ▼
  [Click "Save"] ──► Status = saved
         │
         ▼
  [Prepare CV]
         │
         ▼
  [Attach CV] ──► Auto-mark as applied ──► UserJob.status = applied
         │
         ▼
  [Request CV Tips] ──► LLM call ──► Tips Displayed
         │
         ▼
  [Apply on Portal]
         │
         ▼
  <Result?> ──Interviewed──► Status = interviewed
            └─Rejected────► Status = rejected
```

---

### 7.6 Class Diagram (Key Backend Classes)

Class/field names below are copied directly from `app/models/*.py`; service
method names are copied directly from `app/services/*.py`. No invented
methods (e.g. no `fetch_indeed()` or `verify_token()` — those never
existed in the codebase).

```
┌────────────────┐     ┌────────────────┐     ┌──────────────┐
│      User       │     │  Designation   │     │     Job      │
│─────────────────│     │────────────────│     │──────────────│
│+id:int          │     │+id:int         │     │+id:int       │
│+email:str       │     │+title:str      │     │+title:str    │
│+full_name:str   │     │+created_by:int?│     │+company:str  │
│+hashed_password │     │+created_at     │     │+location:str?│
│+is_active:bool  │     │+updated_at     │     │+description  │
│+is_superuser:bool│    └────────────────┘     │+source:str   │
│+last_login:dt?  │                            │+source_url   │
│+created_at      │                            │+designation_id│
│+updated_at      │                            │  (no FK, §9.2)│
└─────────────────┘                            │+is_external  │
                                                │+created_at   │
┌────────────────┐     ┌────────────────┐      │+updated_at   │
│   UserJob      │     │   UserCV       │      └──────────────┘
│────────────────│     │────────────────│
│+id:int         │     │+id:int         │      ┌──────────────────┐
│+user_id:int    │     │+user_id:int    │      │JobStatus (Enum)  │
│+job_id:int     │     │+name:str       │      │──────────────────│
│+status:str     │     │+gcs_path:str   │      │saved             │
│  (no DB CHECK) │     │+extracted_text │      │applied           │
│+notes:str?     │     │+user_job_id:int?│     │interviewed       │
│+created_at     │     │+created_at     │      │rejected          │
│+updated_at     │     │+updated_at     │      │irrelevant        │
└────────────────┘     └────────────────┘      └──────────────────┘

┌───────────────────────┐  ┌──────────────────────────┐  ┌───────────────────┐
│ app.services.llm      │  │ app.services.jobs /       │  │ app.services.      │
│ (multi-provider LLM)  │  │ ingestion.job_fetcher     │  │ auth_service       │
│───────────────────────│  │───────────────────────────│  │────────────────────│
│+extract_job_data()    │  │+fetch_jobs_for_designation()│ │+register_user()   │
│+get_cv_tips()         │  │+create_job_records()      │  │+login_user()       │
│-_call_groq()          │  │+fetch_job_records()       │  │                    │
│-_call_openai()        │  │                            │  │ app.core.auth      │
│-_call_anthropic()     │  │ app.services.parsers       │  │+create_access_token│
│-_call_gemini()        │  │+parse_indeed_jobs()        │  │+get_current_user() │
│                       │  │+parse_linkedin_jobs()      │  │+hash_password()    │
│ app.services.         │  │+parse_hirist_jobs()        │  │+verify_password()  │
│ external_ingestion    │  │                            │  └────────────────────┘
│+ingest_job_from_url() │  │ app.services.fetchers      │
│+detect_source()       │  │+fetch_page_cffi()          │
└───────────────────────┘  │+fetch_page_with_browser()  │
                            └────────────────────────────┘
```

---

### 7.7 State Diagram – Job Application Status

```
                    ┌──────────────┐
        NEW JOB ───►│   (unseen)   │
                    └──────┬───────┘
                           │ user views
              ┌────────────┼────────────────┐
              ▼            ▼                ▼
         ┌─────────┐  ┌──────────┐   ┌───────────┐
         │  saved  │  │irrelevant│   │  applied  │
         └────┬────┘  └──────────┘   └─────┬─────┘
              │                             │
              │ apply / attach CV           │
              └────────────┬────────────────┘
                           ▼
                    ┌─────────────┐
                    │ interviewed │
                    └──────┬──────┘
                           │
                    ┌──────┴──────┐
                    ▼             ▼
               ┌─────────┐  (offer given)
               │ rejected │
               └──────────┘
```

---

## 8. Data Dictionary

The data dictionary defines every entity, attribute, and data flow used in the system. It provides the single source of truth for the ER diagram, DFDs, and database tables.

### 8.1 Entity Descriptions

| Entity | Description | Primary Key |
|--------|-------------|------------|
| **User** | A registered person using the system. Holds authentication credentials and personal info. | id |
| **Designation** | A job-role title (e.g., "Backend Engineer"). Shared across users. | id |
| **Job** | A single job listing scraped from a portal or added manually. | id |
| **UserDesignation** | Maps a User to the Designations they are interested in. | id |
| **UserJob** | Records a User's interaction with a Job, including application status. | id |
| **UserCV** | A CV document uploaded by a User, stored in GCS, with extracted text. | id |
| **UserJobPreference** | Stores keywords the user wants excluded from their job feed. | id |

### 8.2 Attribute Dictionary

> The tables below were re-derived directly from the live SQLModel classes in
> `app/models/*.py` and cross-checked against `sqlite3 jobs.db ".schema"`
> (see §9.1 for the raw DDL dump). Two corrections versus the previous draft
> of this section: `Designation.title` is **not** DB-enforced unique — only
> service-layer code checks for an existing title before insert, so a
> concurrent write could create duplicates — and `Job.designation_id`
> carries **no foreign-key constraint at all** (see the note in §9.9).

**Entity: User**

| Attribute | Data Type | Size | Description | Constraints |
|-----------|-----------|------|-------------|------------|
| id | Integer | 4 bytes | Auto-generated unique identifier | PK, NOT NULL |
| email | Text | 255 chars | User's email address (login credential) | NOT NULL, UNIQUE, INDEX |
| full_name | Text | 255 chars | User's display name | NOT NULL |
| hashed_password | Text | 255 chars | PBKDF2-SHA256 hash of user's password (via passlib `CryptContext`) | NOT NULL |
| is_active | Boolean | 1 byte | Deactivates the account when false; `get_current_user` rejects inactive users at every protected route | NOT NULL, DEFAULT true |
| is_superuser | Boolean | 1 byte | Reserved for future admin-only functionality | NOT NULL, DEFAULT false |
| last_login | DateTime | 8 bytes | Reserved column — declared on the model but never written to by `login_user()` | NULL |
| created_at | DateTime | 8 bytes | Account creation timestamp | NOT NULL, DEFAULT now() |
| updated_at | DateTime | 8 bytes | Last profile update timestamp | NOT NULL, DEFAULT now() |

---

**Entity: Designation**

| Attribute | Data Type | Size | Description | Constraints |
|-----------|-----------|------|-------------|------------|
| id | Integer | 4 bytes | Auto-generated unique identifier | PK, NOT NULL |
| title | Text | 255 chars | Job role label (e.g., "Data Engineer") | NOT NULL, INDEX (not DB-unique — see note above) |
| created_by | Integer | 4 bytes | FK to the User who created this designation | NULL, FK, INDEX |
| created_at | DateTime | 8 bytes | Record creation timestamp | NOT NULL, DEFAULT now() |
| updated_at | DateTime | 8 bytes | Last update timestamp | NOT NULL, DEFAULT now() |

---

**Entity: Job**

| Attribute | Data Type | Size | Description | Constraints |
|-----------|-----------|------|-------------|------------|
| id | Integer | 4 bytes | Auto-generated unique identifier | PK, NOT NULL |
| title | Text | 255 chars | Job posting title | NOT NULL, INDEX |
| company | Text | 255 chars | Hiring company name | NOT NULL, INDEX |
| location | Text | 255 chars | Work location (city / remote) | NULL, INDEX |
| description | Text | CLOB | Full job description text (empty for scraped listings until fetched on demand) | NOT NULL, DEFAULT '' |
| source | Text | 50 chars | Origin portal, e.g. "Indeed" / "LinkedIn" / "Hirist" (capitalisation as written by the scraper/ingestion code, not normalised) | NOT NULL, INDEX |
| source_url | Text | 1024 chars | Canonical URL of the original listing — the actual deduplication key | NOT NULL, UNIQUE |
| designation_id | Integer | 4 bytes | Id of the Designation this job belongs to | NOT NULL, INDEX, **no FK constraint** |
| is_external | Integer | 1 byte | Boolean (0/1): true if added via `POST /jobs/add` rather than the scraper | NOT NULL, DEFAULT 0 |
| created_at | DateTime | 8 bytes | Record creation timestamp | NOT NULL, DEFAULT now() |
| updated_at | DateTime | 8 bytes | Last update timestamp | NOT NULL, DEFAULT now() |

---

**Entity: UserJob**

| Attribute | Data Type | Size | Description | Constraints |
|-----------|-----------|------|-------------|------------|
| id | Integer | 4 bytes | Auto-generated unique identifier | PK, NOT NULL |
| user_id | Integer | 4 bytes | FK to User | NOT NULL, FK, INDEX |
| job_id | Integer | 4 bytes | FK to Job | NOT NULL, FK, INDEX |
| status | Text | no fixed limit (SQLite VARCHAR) | Application status; values are `JobStatus` enum members at the Pydantic layer, but the column itself is a plain string with **no DB-level CHECK constraint** — see §9.9 | NOT NULL, INDEX, DEFAULT 'saved' |
| notes | Text | CLOB | Free-text notes on the application (declared on the model; no current UI or endpoint writes to it) | NULL |
| created_at | DateTime | 8 bytes | Record creation timestamp | NOT NULL, DEFAULT now() |
| updated_at | DateTime | 8 bytes | Last status change timestamp | NOT NULL, DEFAULT now() |

UNIQUE(user_id, job_id) — enforced via an explicit `UniqueConstraint`, so `upsert_user_job()` can safely update-in-place rather than insert a duplicate.

---

**Entity: UserCV**

| Attribute | Data Type | Size | Description | Constraints |
|-----------|-----------|------|-------------|------------|
| id | Integer | 4 bytes | Auto-generated unique identifier | PK, NOT NULL |
| user_id | Integer | 4 bytes | FK to User (owner) | NOT NULL, FK, INDEX |
| name | Text | 255 chars | Display name of the CV document | NOT NULL |
| gcs_path | Text | 1024 chars | Google Cloud Storage object path | NOT NULL |
| extracted_text | Text | CLOB | Plain text extracted from the CV for LLM input | NOT NULL, DEFAULT '' (not nullable, despite the previous draft of this table) |
| user_job_id | Integer | 4 bytes | Id of the UserJob this CV is tied to (optional: links CV to a specific application) | NULL, FK, INDEX |
| created_at | DateTime | 8 bytes | Upload timestamp | NOT NULL, DEFAULT now() |
| updated_at | DateTime | 8 bytes | Last update timestamp | NOT NULL, DEFAULT now() |

---

**Entity: UserJobPreference**

| Attribute | Data Type | Size | Description | Constraints |
|-----------|-----------|------|-------------|------------|
| id | Integer | 4 bytes | Auto-generated unique identifier | PK, NOT NULL |
| user_id | Integer | 4 bytes | FK to User | NOT NULL, FK, INDEX |
| keyword | Text | no fixed limit (SQLite VARCHAR) | Word/phrase to filter (e.g., "intern"); matched against job titles with hyphen/space normalisation, not an exact substring match | NOT NULL, INDEX |
| is_excluded | Integer | 1 byte | Boolean: if true, jobs whose title contains this keyword are hidden from the unseen feed | NOT NULL, DEFAULT 1 |
| created_at | DateTime | 8 bytes | Record creation timestamp | NOT NULL, DEFAULT now() |
| updated_at | DateTime | 8 bytes | Last update timestamp | NOT NULL, DEFAULT now() |

### 8.3 Data Flow Dictionary (DFD Elements)

| Data Flow | From → To | Description |
|-----------|----------|-------------|
| credentials | User → Auth Module | Email + password for login or registration |
| JWT token | Auth Module → User | Signed JSON Web Token (60-min expiry) |
| designation_id | User → Job Aggregation | Which role to scrape for |
| raw HTML | Job Portals → Scraper | Unparsed webpage content |
| job_list | Parser → Deduplicator | List of {title, company, location, source_url} dicts |
| new_job_records | Deduplicator → Database | Batch of new Job rows after URL dedup |
| job_feed | Database → User | Filtered, sorted list of JobRead objects |
| status_update | User → Tracking Module | {job_id, status} to create/update UserJob |
| signed_upload_url | GCS → CV Module → User | Time-limited PUT URL for direct browser upload |
| cv_file | User → GCS | CV binary uploaded directly to cloud storage |
| cv_text + job_desc | CV Module → LLM Module | Input to LLM prompt for tip generation |
| cv_tips | LLM API → CV Module → User | 5 improvement suggestions in plain text |
| job_url | User → External Ingestion | URL of a job to add manually |
| extracted_job_data | LLM API → Ingestion Module | JSON {title, company, location, description} |

---

## 9. Complete Database Design and Normalization

### 9.1 Actual DDL (from `sqlite3 jobs.db ".schema"`)

The statements below are the real `CREATE TABLE`/`CREATE INDEX` output from
the project's live SQLite database, produced by `SQLModel.metadata.create_all()`
at application startup (`app/main.py`) from the model classes in
`app/models/`. Nothing here has been hand-adjusted.

```sql
CREATE TABLE user (
    id INTEGER NOT NULL,
    email VARCHAR NOT NULL,
    full_name VARCHAR NOT NULL,
    hashed_password VARCHAR NOT NULL,
    is_active BOOLEAN NOT NULL,
    is_superuser BOOLEAN NOT NULL,
    last_login DATETIME,
    created_at DATETIME NOT NULL,
    updated_at DATETIME NOT NULL,
    PRIMARY KEY (id)
);
CREATE UNIQUE INDEX ix_user_email ON user (email);

CREATE TABLE designation (
    id INTEGER NOT NULL,
    title VARCHAR NOT NULL,
    created_by INTEGER,
    created_at DATETIME NOT NULL,
    updated_at DATETIME NOT NULL,
    PRIMARY KEY (id),
    FOREIGN KEY(created_by) REFERENCES user (id)
);
CREATE INDEX ix_designation_title ON designation (title);
CREATE INDEX ix_designation_created_by ON designation (created_by);

CREATE TABLE job (
    id INTEGER NOT NULL,
    title VARCHAR NOT NULL,
    company VARCHAR NOT NULL,
    location VARCHAR,
    description VARCHAR NOT NULL,
    source VARCHAR NOT NULL,
    source_url VARCHAR NOT NULL,
    designation_id INTEGER NOT NULL,
    is_external BOOLEAN NOT NULL DEFAULT 0,
    created_at DATETIME NOT NULL,
    updated_at DATETIME NOT NULL,
    PRIMARY KEY (id),
    UNIQUE (source_url)
    -- NOTE: no FOREIGN KEY(designation_id) clause is emitted — see §9.9.
);
CREATE INDEX ix_job_title ON job (title);
CREATE INDEX ix_job_company ON job (company);
CREATE INDEX ix_job_location ON job (location);
CREATE INDEX ix_job_source ON job (source);
CREATE INDEX ix_job_designation_id ON job (designation_id);

CREATE TABLE userdesignation (
    id INTEGER NOT NULL,
    user_id INTEGER NOT NULL,
    designation_id INTEGER NOT NULL,
    created_at DATETIME NOT NULL,
    updated_at DATETIME NOT NULL,
    PRIMARY KEY (id),
    UNIQUE (user_id, designation_id),
    FOREIGN KEY(user_id) REFERENCES user (id),
    FOREIGN KEY(designation_id) REFERENCES designation (id)
);
CREATE INDEX ix_userdesignation_user_id ON userdesignation (user_id);
CREATE INDEX ix_userdesignation_designation_id ON userdesignation (designation_id);

CREATE TABLE userjob (
    id INTEGER NOT NULL,
    user_id INTEGER NOT NULL,
    job_id INTEGER NOT NULL,
    status VARCHAR NOT NULL,
    notes VARCHAR,
    created_at DATETIME NOT NULL,
    updated_at DATETIME NOT NULL,
    PRIMARY KEY (id),
    UNIQUE (user_id, job_id),
    FOREIGN KEY(user_id) REFERENCES user (id),
    FOREIGN KEY(job_id) REFERENCES job (id)
    -- NOTE: no CHECK(status IN (...)) clause is emitted — see §9.9.
);
CREATE INDEX ix_userjob_user_id ON userjob (user_id);
CREATE INDEX ix_userjob_job_id ON userjob (job_id);
CREATE INDEX ix_userjob_status ON userjob (status);

CREATE TABLE userjobpreference (
    id INTEGER NOT NULL,
    user_id INTEGER NOT NULL,
    keyword VARCHAR NOT NULL,
    is_excluded BOOLEAN NOT NULL,
    created_at DATETIME NOT NULL,
    updated_at DATETIME NOT NULL,
    PRIMARY KEY (id),
    FOREIGN KEY(user_id) REFERENCES user (id)
);
CREATE INDEX ix_userjobpreference_user_id ON userjobpreference (user_id);
CREATE INDEX ix_userjobpreference_keyword ON userjobpreference (keyword);

CREATE TABLE usercv (
    id INTEGER NOT NULL,
    user_id INTEGER NOT NULL,
    name VARCHAR NOT NULL,
    gcs_path VARCHAR NOT NULL,
    extracted_text VARCHAR NOT NULL,
    user_job_id INTEGER,
    created_at DATETIME NOT NULL,
    updated_at DATETIME NOT NULL,
    PRIMARY KEY (id),
    FOREIGN KEY(user_id) REFERENCES user (id),
    FOREIGN KEY(user_job_id) REFERENCES userjob (id)
);
CREATE INDEX ix_usercv_user_id ON usercv (user_id);
CREATE INDEX ix_usercv_user_job_id ON usercv (user_job_id);
```

A schema-creation migration also lives in `app/main.py`'s `lifespan`
handler: on every startup in `ENV=development`, it runs
`ALTER TABLE job ADD COLUMN is_external INTEGER NOT NULL DEFAULT 0` inside a
try/except that swallows the error once the column already exists. This is
a forward-migration shim for databases created before `is_external` was
added to the `Job` model — a fresh database gets the column directly from
`create_all()` instead.

### 9.2 Referential Integrity — what's actually enforced

| Foreign Key | Declared in DDL? | Enforced at runtime? |
|------------|:---:|:---:|
| designation.created_by → user.id | Yes | No |
| userdesignation.user_id → user.id | Yes | No |
| userdesignation.designation_id → designation.id | Yes | No |
| userjob.user_id → user.id | Yes | No |
| userjob.job_id → job.id | Yes | No |
| usercv.user_id → user.id | Yes | No |
| usercv.user_job_id → userjob.id | Yes | No |
| **job.designation_id → designation.id** | **No — absent from the model entirely** | No |

Two independent gaps, not one:

1. **`Job.designation_id` has no `foreign_key=` argument** in
   `app/models/job.py` (it is declared `Field(index=True)` only), so the
   column is a plain indexed integer with no FK clause in the generated
   DDL at all — confirmed above. This is why the ER diagram in §7.4 shows
   that edge with a dashed line rather than the same notation as the
   others.
2. **SQLite does not enforce declared foreign keys unless
   `PRAGMA foreign_keys = ON` is issued per connection**, and nothing in
   `app/db/session.py` sets it (`PRAGMA foreign_keys;` on the live DB
   returns `0`). So even the FKs that *are* declared above are advisory —
   SQLAlchemy uses them for its own join inference, but SQLite itself will
   happily insert a `userjob.user_id` that doesn't exist in `user`.

Consequently there is **no ON DELETE CASCADE/RESTRICT/SET NULL behaviour
anywhere in this system** — deleting a `User` row directly against the
database would silently orphan its `UserJob`, `UserCV`, and
`UserDesignation` rows rather than cascading or being blocked. In practice
this is low-risk today because the application never exposes a "delete
user" or "delete designation" endpoint — orphaning can only happen via
manual DB surgery, not through the API.

### 9.3 Normalization (up to 3NF)

**1NF:** All attributes hold atomic values; no repeating groups or arrays
are stored in any column (SQLite has no native array type, and none of the
models use a delimited-string workaround). `userjob.status` and
`usercv.extracted_text` are each single scalar values.

**2NF:** Every table uses a single-column integer surrogate key (`id`), so
there are no composite primary keys and therefore no partial-key
dependencies to violate. `userjob.notes` and `userjob.status` depend on the
whole of `userjob.id`, not on `user_id` or `job_id` alone.

**3NF:** No non-key attribute depends on another non-key attribute.
- Job title/company live only in `job`; `userjob` stores just the FK
  `job_id`, so a title correction never requires touching `userjob` rows.
- `designation.title` is stored once; `job` and `userdesignation` both
  reference it by id (in `job`'s case, an *unenforced* id — see §9.2 —
  but still structurally an id reference, not a copy of the title).

**Denormalization note:** `UserCVRead` (the API response schema, not a
table) includes `job_title`/`job_company`, computed via a `LEFT JOIN`
through `UserJob` → `Job` in `app/api/v1/cv.py::list_cvs`. This is a
response-shaping join, not stored denormalized data — the `usercv` table
itself has no `job_title`/`job_company` columns.

---

## 10. Project Structure – Modules, Data Structures, Implementation Methodology, Expected Reports

### 10.1 Module Breakdown

The project is organised into **9 functional modules**, each verified
against the actual files/functions in the repository (function names below
are copy-pasted from source, not paraphrased).

---

**Module 1 – Authentication Module**
- Files: `app/core/auth.py`, `app/api/v1/auth.py`, `app/services/auth_service.py`
- Endpoints: `POST /auth/register`, `POST /auth/login`, `GET /auth/users/me`
- Responsibilities: registration (auto-subscribes the new user to every
  existing designation), OAuth2-password-flow login, JWT issuance/verification,
  PBKDF2-SHA256 password hashing via `passlib`.
- Key functions: `register_user()`, `login_user()`, `create_access_token()`,
  `get_current_user()`, `hash_password()`, `verify_password()`
- Data structures: `User` SQLModel table (`id`, `email`, `full_name`,
  `hashed_password`, `is_active`, `is_superuser`, `last_login`,
  `created_at`, `updated_at`); `UserCreate` / `UserRead` schemas.
- Library actually used: `python-jose` (`from jose import jwt`) for JWT
  encode/decode — the project also depends on `PyJWT` in
  `requirements.txt`, but nothing imports it; `python-jose` is what
  `app/core/auth.py` uses.

---

**Module 2 – Designation Module**
- Files: `app/api/v1/designation.py`, `app/services/designation.py`,
  `app/models/designation.py`
- Endpoints: `POST /designation` (auth required), `GET /designation`
  (public — no `Depends(get_current_user)`)
- Key functions: `create_designation()`, `list_designations()`
- Note: `title` uniqueness is enforced only by a service-layer `SELECT`
  check before insert (`create_designation()`), not by a DB constraint —
  see §9.1/§9.2.

---

**Module 3 – User-Designation Subscription Module**
- Files: `app/api/v1/userdesignation.py`, `app/services/userdesignation.py`,
  `app/models/userdesignation.py`
- Endpoints: `POST /user-designation`, `GET /user-designation`,
  `DELETE /user-designation?user_designation_id=`
- Responsibilities: which designations a user follows, feeding the job
  feed's `JOIN` in `fetch_job_records()`.
- Key functions: `create_user_designation()`, `delete_user_designation()`,
  `list_user_designations()`

---

**Module 4 – Job Aggregation Module (Scraping)**
- Files: `app/services/ingestion/job_fetcher.py`,
  `app/services/fetchers/page_fetcher.py`,
  `app/services/fetchers/playwright.py`, `app/services/parsers.py`,
  `app/services/jobs.py`
- Responsibilities: multi-source scraping of search-results pages
  (Indeed, LinkedIn, Hirist), HTML parsing, in-memory + DB dedup, batch insert.
- Key functions: `fetch_jobs_for_designation()` (orchestrator, iterates the
  `SOURCES` dict), `fetch_page_cffi()` (curl_cffi, Chrome131 TLS
  impersonation, Indeed only), `fetch_page_with_browser()` (Playwright,
  LinkedIn/Hirist), `parse_indeed_jobs()`, `parse_linkedin_jobs()`,
  `parse_hirist_jobs()`, `create_job_records()`
- Data structures: `Job` SQLModel table; `list[dict]` intermediate parse
  buffer; `set[str]` in-memory URL-dedup set inside `create_job_records()`.

---

**Module 5 – Celery Scheduler Module**
- Files: `app/core/celery.py`, `app/services/tasks.py`
- Responsibilities: worker/beat configuration; daily full scrape; on-demand
  per-designation scrape.
- Key functions: `job_fetching_task()`, `job_fetching_task_designation()`
- Beat schedule: `crontab(hour=0, minute=0)` with
  `celery_app.conf.update(timezone="Asia/Kolkata", enable_utc=False)` —
  the cron fires at 00:00 **IST directly** (no separate UTC conversion is
  needed or performed, since `enable_utc=False` makes Celery interpret the
  crontab in the configured timezone).

---

**Module 6 – Job Listing & Application Tracking Module**
- Files: `app/api/v1/job.py`, `app/api/v1/userjob.py`,
  `app/services/jobs.py`, `app/services/user_job.py`
- Endpoints: `GET /jobs`, `POST /jobs/fetch-new`, `POST /jobs/add`,
  `GET /jobs/{job_id}/description`, `POST /user-jobs`
- Key functions: `fetch_job_records()` (in `jobs.py` — the one actually
  called by `GET /jobs`), `upsert_user_job()`, `ingest_job_from_url()`
  (lives in `app.services.external_ingestion`, not in this module's own
  files — imported by `job.py`), `fetch_job_description()`
- Data structures: `UserJob` table; `JobStatus` enum; `JobRead` schema with
  computed `is_new` (unseen mode) or `user_job_id`/`user_status`
  (status-filtered mode).
- **Dead code found:** `app/services/user_job.py` also defines a
  `fetch_job_records()` — a separate, near-duplicate implementation that is
  never imported by any route. Only the one in `app/services/jobs.py` is
  live; the one in `user_job.py` is unreachable and safe to delete.

---

**Module 7 – CV Management Module**
- Files: `app/api/v1/cv.py`, `app/services/gcs.py`, `app/services/extractor.py`
- Endpoints: `GET /cvs/upload-url`, `POST /cvs`, `GET /cvs`,
  `GET /cvs/{cv_id}/download`, `DELETE /cvs/{cv_id}`,
  `POST /cvs/{cv_id}/tips/{job_id}`
- Responsibilities: client-direct-to-GCS upload via signed URL, server-side
  text extraction on registration, CV listing (with linked job title/company
  via a `LEFT JOIN` through `UserJob`), download, deletion.
- Key functions: `generate_upload_url()`, `generate_download_url()`,
  `download_bytes()`, `delete_file()`, `extract_text()` (dispatches to
  `pdfplumber` / `python-docx` / plain UTF-8 decode by extension)
- Data structures: `UserCV` table; `UserCVRead` response schema (excludes
  `extracted_text` from the API response — it is never sent back to the client).
- **Unused function found:** `app.services.gcs.upload_bytes()` is defined
  but never called — every current upload goes client→GCS directly via the
  signed URL from `generate_upload_url()`; the backend only ever
  *downloads* the object afterward (for text extraction).

---

**Module 8 – AI / LLM Integration Module**
- Files: `app/services/llm.py`, `app/services/external_ingestion.py`,
  `app/services/description.py`
- Responsibilities: multi-provider LLM dispatch; CV-tip generation;
  unstructured job-page extraction (URL paste for unsupported portals);
  job-description caching for the description tab and CV-tips flow.
- Key functions: `extract_job_data()`, `get_cv_tips()`,
  `ingest_job_from_url()`, `detect_source()`, `fetch_job_description()`
- Providers and models actually hard-coded in `app/services/llm.py`:
  Groq (`openai/gpt-oss-120b`), OpenAI (`gpt-4o-mini`), Anthropic
  (`claude-opus-5`), Gemini (`gemini-1.5-flash`). Only Groq falls back to a
  server-side key (`settings.GROQ_API_KEY`); the other three require the
  caller to supply their own key via the `X-Llm-Key` header.
- **Orphaned file found:** `app/services/cv_tips.py` defines a second,
  Groq-only `get_cv_tips(job, cv_text)` that is not imported anywhere —
  superseded by the multi-provider version in `llm.py`, which is what
  `POST /cvs/{cv_id}/tips/{job_id}` actually calls.
- Naming collision to be aware of: `description.py`'s `_parse_indeed` /
  `_parse_hirist` / `_parse_linkedin` parse a **job detail page** (full
  description), while `parsers.py`'s `parse_indeed_jobs` /
  `parse_linkedin_jobs` / `parse_hirist_jobs` parse a **search-results
  page** (listing summaries). Similar names, different inputs/outputs,
  different files.

---

**Module 9 – React Frontend Module**
- Files: `frontend/react-app/src/`
- Responsibilities: SPA routing, JWT management (via `localStorage`), all
  UI screens.
- Sub-components:
  - `Login.jsx` / `Register.jsx` – Auth screens
  - `Jobs.jsx` – Job feed with filters, modals, status buttons
  - `CVManager.jsx` – Upload, list, download, delete CVs
  - `Designations.jsx` / `UserDesignation.jsx` – Designation management
  - `Settings.jsx` – LLM provider + API key persistence (localStorage only)
  - `api.js` – Centralized HTTP client with JWT injection

---

### 10.2 Key Data Structures

| Structure | Type | Used In |
|-----------|------|---------|
| `Job` | SQLModel ORM table | All job-related modules |
| `UserJob` | SQLModel ORM table | Application tracking |
| `UserCV` | SQLModel ORM table | CV management |
| `JobStatus` | Python Enum (str) | Pydantic-layer validation of `status` only — **not** a DB constraint (§9.1) |
| `JobRead` | Pydantic response schema | API → Frontend |
| `list[dict]` | Intermediate parse buffer | Scraper → Deduplicator |
| `set[str]` | In-memory dedup set | `create_job_records()` |
| JWT payload `{"sub": str(user_id), "exp": datetime}` | Dict | Auth token (note: `sub` is stringified, then cast back to `int` in `get_current_user`) |

### 10.3 Implementation Methodology

The project follows an **Iterative Incremental** development approach:

- **Iteration 1:** Database schema + Auth module.
- **Iteration 2:** Scraping modules (one portal at a time), Celery integration.
- **Iteration 3:** Job listing API, status management API.
- **Iteration 4:** CV upload/download, GCS integration, text extraction.
- **Iteration 5:** LLM module, CV tips API, external ingestion.
- **Iteration 6:** React frontend, end-to-end integration.
- **Iteration 7:** Testing, bug fixes, performance tuning.

Each iteration produces a testable increment, allowing early feedback.

### 10.4 Expected Reports / System Outputs

| Report | Trigger | Contents |
|--------|---------|---------|
| Job Feed (default) | GET /jobs | Unseen jobs relevant to user's designations, sorted newest-first, is_new badge. |
| Saved Jobs | GET /jobs?status=saved | Jobs marked saved, with user_job_id/user_status. |
| Applied Jobs | GET /jobs?status=applied | Jobs marked applied (CV linkage is looked up separately via GET /cvs, not joined into this response). |
| Interviewed Jobs | GET /jobs?status=interviewed | Jobs where user reached interview stage. |
| Rejected Jobs | GET /jobs?status=rejected | Jobs where application was rejected. |
| CV List | GET /cvs | All CVs uploaded by the user, with linked job title/company via a join through UserJob. |
| AI CV Tips | POST /cvs/{cv_id}/tips/{job_id} | 5 specific, line-referenced CV improvement suggestions. |
| Designation List | GET /designation | All available job-role designations (public endpoint). |

### 10.5 Automated Test Suite

A runnable `pytest` suite lives under `tests/` (43 tests across 7 files,
all passing against the current codebase — run with `pytest` from the
project root). It exercises every route in the table above plus the CV and
user-job-preference endpoints, using a fresh throwaway SQLite database per
test and monkeypatched GCS/LLM/Celery calls so no test hits a real external
service. See §10.6 (Test Case Log) for the endpoint-by-endpoint list.

Building this suite surfaced two real defects, both now fixed in the
committed code:

1. `POST /auth/register` returned an **empty JSON object** instead of the
   created user. Cause: `register_user()` calls `session.commit()` a
   second time (to insert auto-subscribed `UserDesignation` rows) after
   already having refreshed the `User` instance; SQLAlchemy's default
   `expire_on_commit=True` re-expires the instance's attributes, and
   `model_dump()`/`jsonable_encoder` read the (now-empty) `__dict__`
   directly rather than triggering a lazy reload. Fix: refresh the user a
   second time after the final commit. The route was also missing
   `response_model=UserRead`, which — once the first bug was fixed — would
   have leaked `hashed_password` back to the client; both are now fixed
   in `app/services/auth_service.py` and `app/api/v1/auth.py`.
2. `POST /jobs/add` (with a `status` supplied) returned a response with
   every `Job` field missing, for the identical reason: the second
   `session.commit()` (for the optional `UserJob` row) expired the
   already-committed `Job` instance before `job.model_dump()` was called
   in the return statement. Fixed in `app/api/v1/job.py` by capturing
   `job.model_dump()` into a local variable before the second commit.

### 10.6 Test Case Log

| Test ID | Endpoint | Scenario | Expected Result | Actual Result |
|---------|----------|----------|------------------|----------------|
| TC-01 | POST /auth/register | Valid new email | 200, user fields returned, no hashed_password | Pass |
| TC-02 | POST /auth/login | Correct credentials | 200, bearer token | Pass |
| TC-03 | POST /auth/login | Wrong password | 401 | Pass |
| TC-04 | POST /auth/login | Unknown email | 401 | Pass |
| TC-05 | GET /auth/users/me | No token | 401 | Pass |
| TC-06 | GET /auth/users/me | Valid token | 200, current user | Pass |
| TC-07 | POST /designation | No auth | 401 | Pass |
| TC-08 | POST /designation | New title | 200, created | Pass |
| TC-09 | POST /designation | Duplicate title | 400 | Pass |
| TC-10 | GET /designation | No auth | 200 (public) | Pass |
| TC-11 | POST /user-designation | New subscription | 200 | Pass |
| TC-12 | POST /user-designation | Duplicate subscription | 400 | Pass |
| TC-13 | POST /user-designation | Unknown designation_id | 400 | Pass |
| TC-14 | DELETE /user-designation | Another user's row | 400 (not found for this user) | Pass |
| TC-15 | GET /jobs | No subscription | 200, empty list | Pass |
| TC-16 | GET /jobs | Subscribed, unseen job | 200, job present | Pass |
| TC-17 | GET /jobs | Job already actioned | 200, job excluded from unseen feed | Pass |
| TC-18 | GET /jobs?status=applied | Job marked applied | 200, user_job_id/user_status populated | Pass |
| TC-19 | GET /jobs | Excluded keyword in title | 200, matching job hidden | Pass |
| TC-20 | POST /jobs/fetch-new | Subscribed designations | Celery `.delay()` called once per designation | Pass |
| TC-21 | POST /jobs/add | New URL (mocked ingestion) | 200, is_external=true, is_new=true | Pass |
| TC-22 | POST /jobs/add | Duplicate URL | 200, is_new=false, ingestion not called twice | Pass |
| TC-23 | POST /jobs/add | Extraction returns no title | 422 | Pass |
| TC-24 | GET /jobs/{id}/description | Empty description, mocked fetch | 200, description cached on second call without refetch | Pass |
| TC-25 | GET /jobs/{id}/description | Unknown job id | 404 | Pass |
| TC-26 | POST /user-jobs | New (user, job) pair | 200, status set | Pass |
| TC-27 | POST /user-jobs | Same pair again, new status | 200, same row id, status updated | Pass |
| TC-28 | POST /user-jobs | Invalid status string | 422 | Pass |
| TC-29 | POST /user-job-preferences | Valid keyword | 201 | Pass |
| TC-30 | POST /user-job-preferences | No auth | 401 | Pass |
| TC-31 | GET /cvs/upload-url | Disallowed extension | 400 | Pass |
| TC-32 | GET /cvs/upload-url | PDF extension | 200, signed URL + gcs_path | Pass |
| TC-33 | POST /cvs | Mocked GCS + extractor | 200, extracted_text not exposed in response | Pass |
| TC-34 | POST /cvs | Disallowed extension | 400 | Pass |
| TC-35 | POST /cvs | GCS download fails | 502 | Pass |
| TC-36 | GET /cvs | CV linked to a job | 200, job_title/job_company populated | Pass |
| TC-37 | GET /cvs/{id}/download | Owner | 200, signed URL | Pass |
| TC-38 | GET /cvs/{id}/download | Non-owner | 404 | Pass |
| TC-39 | DELETE /cvs/{id} | Owner | 200, row removed | Pass |
| TC-40 | POST /cvs/{id}/tips/{job_id} | Mocked LLM | 200, tips text returned | Pass |
| TC-41 | POST /cvs/{id}/tips/{job_id} | Unknown job_id | 404 | Pass |
| TC-42 | POST /cvs/{id}/tips/{job_id} | CV has no extracted text | 422 | Pass |
| TC-43 | POST /auth/register (auto-subscribe) | New designation created after a user registers | New user is not retroactively subscribed | Pass |

---

## 11. Software Engineering Paradigm and Cost Estimation

### 11.1 Software Engineering Paradigm

This project follows the **Iterative Incremental Model** of software development:

- Each iteration delivers a working, testable software increment.
- Requirements for later modules are refined based on feedback from earlier iterations.
- Suitable for a solo-developer project where the scope and priorities can shift as modules are built.

The development also draws principles from **Agile Software Development**:
- Short work cycles (1–2 week tasks as shown in the Gantt chart).
- Continuous integration of backend and frontend after each module completes.
- Lightweight documentation: code comments, this synopsis, and the final project report.

**SDLC Phases Covered:**

| Phase | Activities in This Project |
|-------|--------------------------|
| Requirements Engineering | FR/NFR tables (Section 4), Literature Review |
| System Analysis | DFDs, ER diagram, Data Dictionary (Sections 7–8) |
| System Design | Module breakdown, DB schema, UI design, network architecture |
| Implementation | FastAPI backend, React frontend, Celery tasks, GCS integration |
| Testing | Unit tests (auth, job parsing), API integration tests, UI manual testing |
| Deployment | `run_all.sh` script; Docker Compose for containerised deployment |
| Maintenance | Known issues list in CLAUDE.local.md; future enhancements (Section 14) |

### 11.2 Coding Standards Applied

- **Naming convention:** PEP 8 (snake_case) for Python; camelCase for JavaScript; UPPER_CASE for constants.
- **Type hints:** All Python functions use type annotations for input/output clarity.
- **Pydantic schemas:** Separate `Create` / `Read` models to prevent over-posting and control API response shape.
- **Error handling:** FastAPI `HTTPException` with descriptive messages; Python `try/except` around scraper calls.
- **Separation of concerns:** API layer → Service layer → DB layer; no business logic in route handlers.
- **Environment variables:** All secrets via `.env` (never hard-coded); loaded via `pydantic-settings`.
- **Code comments:** per the MCSP-232 guidelines (Section VI, "Coding"), every
  non-trivial function's docstring states its functional description,
  input parameters (with types), output/return value, the functions it
  calls and is called by, a description of its main variables, and a
  step-by-step logic walkthrough — not just a one-line summary. Applied
  across the service and API layers (`app/services/*.py`, `app/api/v1/*.py`).

---

## 12. Network Architecture

```
┌──────────────────────────────────────────────────────────────┐
│                     Developer Machine                        │
│                                                              │
│  ┌──────────────────┐    HTTP :3000    ┌─────────────────┐  │
│  │  User Browser    │◄───────────────►│  Vite Dev       │  │
│  │  (React SPA)     │                 │  Server         │  │
│  └────────┬─────────┘                 └─────────────────┘  │
│           │                                                  │
│           │ REST/JSON  HTTP :8000                            │
│           ▼                                                  │
│  ┌──────────────────┐    TCP :6379     ┌─────────────────┐  │
│  │  FastAPI / Uvicorn│◄──────────────►│  Redis Server   │  │
│  │  (ASGI)          │                 └─────────────────┘  │
│  └────────┬─────────┘                        ▲             │
│           │                                  │             │
│           │ SQLite file                      │ tasks       │
│           ▼                       ┌──────────┴──────────┐  │
│      jobs.db                      │  Celery Worker +    │  │
│                                   │  Celery Beat        │  │
│                                   └─────────────────────┘  │
└──────────────────────────────────────────────────────────────┘
              │                          │
              │ HTTPS                    │ HTTPS
              ▼                          ▼
   ┌─────────────────┐        ┌──────────────────────┐
   │ Google Cloud    │        │  Job Portals         │
   │ Storage (GCS)   │        │  Indeed / LinkedIn   │
   │ (CV files)      │        │  / Hirist            │
   └─────────────────┘        └──────────────────────┘
              │
              │ HTTPS
              ▼
   ┌─────────────────┐
   │  LLM APIs       │
   │  Groq / OpenAI  │
   │  Anthropic /    │
   │  Gemini         │
   └─────────────────┘
```

**Communication Protocols:**
- Browser ↔ React dev server: HTTP (port 3000)
- Browser / React ↔ FastAPI: REST/JSON over HTTP (port 8000); CORS enabled for `localhost:3000`
- FastAPI ↔ Redis: TCP (port 6379) via Celery AMQP-compatible protocol
- FastAPI / Celery ↔ External portals: HTTPS (outbound)
- FastAPI / Celery ↔ GCS: HTTPS (Google Cloud Storage REST API)
- FastAPI / Celery ↔ LLM APIs: HTTPS (outbound REST)
- FastAPI ↔ SQLite: File I/O (local disk, `jobs.db`)

---

## 13. Security Mechanisms

### 13.1 Authentication Layer

| Mechanism | Implementation |
|-----------|---------------|
| Password hashing | PBKDF2-SHA256 (via Python `hashlib`); never stored in plaintext. |
| Token-based auth | JWT (PyJWT), signed with `SECRET_KEY` from environment; 60-minute expiry. |
| Token transmission | `Authorization: Bearer <token>` header; never in URLs. |
| Protected routes | FastAPI `Depends(get_current_user)` dependency on every non-public endpoint. |
| Public endpoints | `/health`, `/auth/register`, `/auth/login`, `GET /designation` only. |

### 13.2 API Layer

| Mechanism | Implementation |
|-----------|---------------|
| CORS | Restricted to `http://localhost:3000`; no wildcard `*` origin in production. |
| Input validation | Pydantic v2 schemas validate all request bodies; type errors return 422 automatically. |
| SQL injection prevention | SQLModel/SQLAlchemy ORM parameterises all queries; raw SQL used only for DDL (ALTER TABLE). |
| HTTP error mapping | HTTPException with appropriate status codes (400, 401, 404, 422, 502). |

### 13.3 File Storage Layer

| Mechanism | Implementation |
|-----------|---------------|
| Signed URLs | GCS signed PUT / GET URLs with short expiry; clients cannot access the bucket directly. |
| Scoped access | Each user's CVs are stored under `users/{user_id}/` prefix; API enforces ownership checks. |
| File type validation | CV endpoint only accepts PDF, DOCX, TXT during text extraction. |

### 13.4 Secret Management

| Secret | Storage |
|--------|---------|
| `SECRET_KEY` | `.env` file; never committed to version control (in `.gitignore`). |
| `GROQ_API_KEY` | `.env` file. |
| GCS credentials | Google Application Default Credentials (ADC); service account JSON not committed. |
| LLM API keys (user-supplied) | Browser `localStorage` only; never sent to the backend except in headers per-request. |

### 13.5 Frontend Security

- LLM API keys stored in `localStorage` and transmitted per-request as custom headers; the backend does not persist them.
- No sensitive data (passwords, tokens) logged to the browser console.
- JWT stored in `localStorage`; cleared on logout.

---

## 14. Future Scope and Enhancements

| # | Enhancement | Rationale |
|---|------------|----------|
| 1 | **Email / Push Notifications** | Alert users immediately when new jobs matching their designations are scraped. |
| 2 | **Pagination & Infinite Scroll** | Current implementation loads all jobs; necessary as the database grows. |
| 3 | **Browser Extension** | One-click save of any job page from LinkedIn / Naukri without switching tabs. |
| 4 | **Mobile Application (React Native)** | Job-seeking is primarily a mobile activity; a native app improves UX. |
| 5 | **AI-Powered Job Matching Score** | LLM or embedding-based relevance score between a user's CV and each job. |
| 6 | **Interview Preparation Module** | LLM-generated interview questions tailored to the job description. |
| 7 | **Structured Logging (ELK / Loki)** | Replace `print()` statements with structured logs for observability. |
| 8 | **PostgreSQL Migration** | SQLite is single-writer; PostgreSQL supports concurrent writes and horizontal scaling. |
| 9 | **Unit & Integration Test Suite** | `pytest` + `httpx.AsyncClient` for API tests; Playwright for E2E tests. |
| 10 | **Multi-tenant SaaS Deployment** | Containerise with Docker Compose; deploy on GCP Cloud Run + Cloud SQL + Memorystore. |
| 11 | **Rate Limiting** | `slowapi` (FastAPI) middleware to prevent API abuse. |
| 12 | **LinkedIn Official API Integration** | Replace fragile Playwright scraping with the official LinkedIn Jobs API. |
| 13 | **Application Analytics Dashboard** | Charts showing application funnel (saved → applied → interviewed → offer rate). |
| 14 | **Auto-fill Integration** | RPA or browser extension to pre-fill application forms using CV data. |

---

## 15. Bibliography

### IEEE Format

[1] T. Christie, "FastAPI," *tiangolo/fastapi*, GitHub, 2024. [Online]. Available: https://github.com/tiangolo/fastapi

[2] S. Ramirez, "SQLModel," *tiangolo/sqlmodel*, GitHub, 2024. [Online]. Available: https://github.com/tiangolo/sqlmodel

[3] Celery Project, "Celery: Distributed Task Queue," *celery/celery*, GitHub, 2024. [Online]. Available: https://github.com/celery/celery

[4] Microsoft, "Playwright for Python," *microsoft/playwright-python*, GitHub, 2024. [Online]. Available: https://github.com/microsoft/playwright-python

[5] Yilong Liu, "curl_cffi: Python binding for curl-impersonate," *yifeikong/curl_cffi*, GitHub, 2024. [Online]. Available: https://github.com/yifeikong/curl_cffi

[6] L. Richardson, "Beautiful Soup Documentation," *crummy.com*, 2024. [Online]. Available: https://www.crummy.com/software/BeautifulSoup/bs4/doc/

[7] Meta AI, "LLaMA 3," *meta-llama/llama3*, GitHub / Meta AI Blog, 2024. [Online]. Available: https://ai.meta.com/blog/meta-llama-3/

[8] Groq, "Groq API Documentation," *console.groq.com*, 2024. [Online]. Available: https://console.groq.com/docs

[9] OpenAI, "OpenAI API Reference," *platform.openai.com*, 2024. [Online]. Available: https://platform.openai.com/docs

[10] Anthropic, "Claude API Documentation," *docs.anthropic.com*, 2024. [Online]. Available: https://docs.anthropic.com

[11] Google DeepMind, "Gemini API Documentation," *ai.google.dev*, 2024. [Online]. Available: https://ai.google.dev/docs

[12] Google Cloud, "Cloud Storage Documentation," *cloud.google.com*, 2024. [Online]. Available: https://cloud.google.com/storage/docs

[13] M. Jones, J. Bradley, and N. Sakimura, "JSON Web Token (JWT)," *RFC 7519*, Internet Engineering Task Force (IETF), May 2015. [Online]. Available: https://www.rfc-editor.org/rfc/rfc7519

[14] Facebook, "React – A JavaScript Library for Building User Interfaces," *react.dev*, 2024. [Online]. Available: https://react.dev

[15] Evan You, "Vite – Next Generation Frontend Tooling," *vitejs.dev*, 2024. [Online]. Available: https://vitejs.dev

[16] Redis Ltd., "Redis Documentation," *redis.io*, 2024. [Online]. Available: https://redis.io/docs

[17] Python Software Foundation, "Python 3.11 Documentation," *docs.python.org*, 2024. [Online]. Available: https://docs.python.org/3.11/

[18] OWASP Foundation, "OWASP Top Ten Security Risks," *owasp.org*, 2021. [Online]. Available: https://owasp.org/www-project-top-ten/

[19] SQLite Consortium, "SQLite Documentation," *sqlite.org*, 2024. [Online]. Available: https://www.sqlite.org/docs.html

[20] S. Lowe, "pdfplumber: Plumb a PDF for detailed information about each text character, rectangle, and line," *jsvine/pdfplumber*, GitHub, 2024. [Online]. Available: https://github.com/jsvine/pdfplumber

---

*End of Synopsis*

---
**Document prepared for:** IGNOU MCAOL Project (MCSP-232)
**Date:** June 2026
**Total Pages:** ~20
