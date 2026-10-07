# Bulk Certificate Generator Backend

A clean, modular, interview-ready FastAPI backend service designed to asynchronously validate recipient data and generate personalized PDF certificates in bulk.

---

## 📋 Table of Contents

- [Overview](#overview)
- [Tech Stack](#tech-stack)
- [Project Architecture](#project-architecture)
- [Project Structure](#project-structure)
- [Environment Setup & Installation](#environment-setup--installation)
- [Running the Application](#running-the-application)
- [API Reference & Example Usage](#api-reference--example-usage)
- [Status Definitions & Progress Metrics](#status-definitions--progress-metrics)
- [Running Automated Tests](#running-automated-tests)
- [Design Decisions & Rationale](#design-decisions--rationale)
- [BackgroundTasks Architecture & Limitations](#backgroundtasks-architecture--limitations)
- [Future Production Enhancements](#future-production-enhancements)

---

## 🎯 Overview

The **Bulk Certificate Generator** backend provides an asynchronous API workflow for bulk generating personalized PDF certificates from recipient lists.

When a client submits a job request (`POST /api/v1/jobs`), the system:
1. Validates input schema (non-blank recipient names, valid emails, non-empty list, valid ISO date).
2. Persists a `Job` record (`status: pending`) and associated `Certificate` records in SQLite.
3. Enqueues an asynchronous background task using FastAPI's `BackgroundTasks`.
4. Returns an immediate `HTTP 202 Accepted` response with the `job_id`.

In the background, a worker function processes recipients sequentially using Pillow to render recipient details onto a landscape certificate template (`templates/certificate_template.png`) and outputs standard PDF files to `generated/`. Individual recipient errors are caught and recorded without stopping remaining certificates.

---

## 🛠️ Tech Stack

- **Python 3.12+**: Modern typed Python codebase.
- **FastAPI**: High-performance web framework for building APIs.
- **Uvicorn**: ASGI web server implementation.
- **SQLAlchemy 2.0**: Relational ORM mapping.
- **SQLite**: Embedded relational database for zero-config local execution.
- **Pydantic v2**: Data validation and setting management via `pydantic-settings`.
- **Pillow (PIL)**: High-performance image rendering and PDF file creation.
- **Pytest & HTTPX**: Testing framework and API client for automated verification.

---

## 🏗️ Project Architecture

```
Client
  ↓
FastAPI API (POST /api/v1/jobs)
  ↓
Validate Request (Pydantic v2)
  ↓
Create Job + Certificate DB Records (Status: pending)
  ↓
FastAPI BackgroundTasks Enqueue
  ↓
Background Worker (process_bulk_job)
  ↓ (Independent DB session via SessionLocal)
Generate Certificates One-by-One (Pillow -> PDF)
  ↓
Update Certificate Result (Status: generated / failed)
  ↓
Update Overall Job Progress & Status (completed / completed_with_errors / failed)
  ↓
Client Retrieves Files (GET /api/v1/certificates/{id})
```

---

## 📁 Project Structure

```
bulk-certificate-generator/
│
├── app/
│   ├── __init__.py
│   ├── main.py                  # FastAPI app entry point & router mounting
│   │
│   ├── core/
│   │   ├── __init__.py
│   │   ├── config.py            # Pydantic BaseSettings environment config
│   │   └── database.py          # SQLAlchemy engine, session maker, base model
│   │
│   ├── models/
│   │   ├── __init__.py
│   │   ├── job.py               # Job ORM model (generation_jobs)
│   │   └── certificate.py       # Certificate ORM model (certificates)
│   │
│   ├── schemas/
│   │   ├── __init__.py
│   │   ├── job.py               # Job request & response Pydantic schemas
│   │   └── certificate.py       # Recipient & Certificate Pydantic schemas
│   │
│   ├── services/
│   │   ├── __init__.py
│   │   ├── job_service.py       # Job CRUD, progress calculation, & worker
│   │   └── certificate_service.py # Certificate layout rendering & PDF export
│   │
│   └── api/
│       ├── __init__.py
│       └── routes/
│           ├── __init__.py
│           ├── jobs.py          # /api/v1/jobs API endpoints
│           └── certificates.py  # /api/v1/certificates API endpoints
│
├── templates/
│   └── certificate_template.png # Predefined landscape certificate template
│
├── generated/                   # Output directory for generated PDF files
│   └── .gitkeep
│
├── tests/
│   ├── __init__.py
│   ├── conftest.py              # Pytest fixtures & in-memory test DB setup
│   ├── test_jobs.py             # Job creation and status query tests
│   ├── test_validation.py       # Payload validation error tests
│   ├── test_generation.py       # PDF rendering, long-name, & unicode tests
│   ├── test_failure_handling.py # Fault isolation and all-failure tests
│   ├── test_retrieval.py        # Certificate download endpoint tests
│   ├── test_lifecycle.py        # Direct worker service lifecycle tests
│   ├── test_progress.py         # Progress percentage calculation tests
│   ├── test_session_safety.py   # Database session safety tests
│   ├── test_multiple_jobs.py    # Multi-job concurrent isolation tests
│   └── test_security_retrieval.py # Path traversal safety & file edge case tests
│
├── requirements.txt
├── .env.example
├── .gitignore
└── README.md
```

---

## ⚙️ Environment Setup & Installation

### Prerequisites
- **Python 3.12+** installed on your system.

### 1. Virtual Environment Setup

**Windows PowerShell:**
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

**Linux / macOS:**
```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 2. Dependency Installation
```bash
pip install -r requirements.txt
```

### 3. Environment Configuration
Environment defaults are configured via Pydantic BaseSettings. Create a `.env` file from `.env.example` if customization is needed:
```powershell
Copy-Item .env.example .env
```

Default variables:
```ini
DATABASE_URL=sqlite:///./certificates.db
GENERATED_CERTIFICATES_DIR=generated
CERTIFICATE_TEMPLATE_PATH=templates/certificate_template.png
```

---

## 🚀 Running the Application

Start the Uvicorn ASGI server from the project root directory:

```bash
uvicorn app.main:app --reload
```

The server runs at `http://127.0.0.1:8000`.

Interactive documentation endpoints:
- **Swagger UI**: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- **ReDoc**: [http://127.0.0.1:8000/redoc](http://127.0.0.1:8000/redoc)

---

## 📡 API Reference & Example Usage

### 1. Health Check
`GET /health`

**Response (HTTP 200):**
```json
{
  "status": "ok"
}
```

---

### 2. Submit Bulk Generation Job
`POST /api/v1/jobs`

**Request Body:**
```json
{
  "certificate_title": "Python Workshop",
  "organization": "ABC Technologies",
  "date": "2026-10-07",
  "recipients": [
    {
      "name": "Ashwin Rathinakumar",
      "email": "ashwin@example.com"
    },
    {
      "name": "Rahul Kumar",
      "email": "rahul@example.com"
    }
  ]
}
```

**cURL Request:**
```bash
curl -X POST "http://127.0.0.1:8000/api/v1/jobs" \
     -H "Content-Type: application/json" \
     -d '{
       "certificate_title": "Python Workshop",
       "organization": "ABC Technologies",
       "date": "2026-10-07",
       "recipients": [
         {"name": "Ashwin Rathinakumar", "email": "ashwin@example.com"},
         {"name": "Rahul Kumar", "email": "rahul@example.com"}
       ]
     }'
```

**Response (HTTP 202 Accepted):**
```json
{
  "job_id": 1,
  "status": "pending",
  "total_count": 2
}
```

---

### 3. Get Job Status & Progress
`GET /api/v1/jobs/{job_id}`

**cURL Request:**
```bash
curl -X GET "http://127.0.0.1:8000/api/v1/jobs/1"
```

**Response (Processing / Completed):**
```json
{
  "job_id": 1,
  "status": "completed",
  "total_count": 2,
  "successful_count": 2,
  "failed_count": 0,
  "pending_count": 0,
  "progress_percentage": 100
}
```

---

### 4. List Job Certificates
`GET /api/v1/jobs/{job_id}/certificates`

**cURL Request:**
```bash
curl -X GET "http://127.0.0.1:8000/api/v1/jobs/1/certificates"
```

**Response:**
```json
{
  "job_id": 1,
  "certificates": [
    {
      "id": 1,
      "recipient_name": "Ashwin Rathinakumar",
      "recipient_email": "ashwin@example.com",
      "status": "generated",
      "download_url": "/api/v1/certificates/1",
      "error_message": null
    },
    {
      "id": 2,
      "recipient_name": "Rahul Kumar",
      "recipient_email": "rahul@example.com",
      "status": "generated",
      "download_url": "/api/v1/certificates/2",
      "error_message": null
    }
  ]
}
```

---

### 5. Download Certificate PDF
`GET /api/v1/certificates/{certificate_id}`

**cURL Request:**
```bash
curl -X GET "http://127.0.0.1:8000/api/v1/certificates/1" --output certificate_1.pdf
```

**Response:**
- Returns binary stream (`application/pdf`) on success.
- Returns `HTTP 400 Bad Request` if certificate status is failed or pending.
- Returns `HTTP 404 Not Found` if certificate ID does not exist or physical file was deleted from disk.

---

## 📊 Status Definitions & Progress Metrics

### Job Status Transitions

```
    Job Created
        ↓
     PENDING
        ↓
    PROCESSING
   /    |     \
  /     |      \
 v      v       v
COMPLETED  COMPLETED_WITH_ERRORS  FAILED
```

- `pending`: Job recorded in database; queued for background processing.
- `processing`: Background worker is actively rendering certificates.
- `completed`: All certificates generated successfully ($0$ failures).
- `completed_with_errors`: At least $1$ certificate succeeded and at least $1$ certificate failed.
- `failed`: All certificates in the job failed or a critical top-level error occurred.

### Certificate Statuses
- `pending`: Certificate record created; generation queued.
- `generated`: Certificate rendered successfully; PDF saved on disk.
- `failed`: Generation failed; `error_message` stored in DB.

### Progress Formula
$$\text{progress\_percentage} = \min\left(100, \max\left(0, \left\lfloor \frac{\text{successful\_count} + \text{failed\_count}}{\text{total\_count}} \times 100 \right\rfloor\right)\right)$$

---

## 🧪 Running Automated Tests

Run the full pytest suite:

```bash
pytest -q
```

Run with verbose output:
```bash
pytest -v
```

All test cases verify:
1. Job creation & immediate status response.
2. Input payload validation rules (names, emails, dates, empty recipient list).
3. Certificate file generation, dynamic font sizing for long names, and Unicode character support (`José François Müller`).
4. Worker service lifecycle and progress metrics.
5. Per-recipient error isolation (`completed_with_errors`) and all-failure scenarios (`failed`).
6. Certificate PDF downloading, missing file handling, and 404/400 status codes.
7. Database session safety and isolation across concurrent jobs.
8. Path traversal safety (`../../../etc/passwd`).

---

## 💡 Design Decisions & Rationale

### 1. Framework & ORM
- **FastAPI**: Selected for native async support, automated Pydantic schema validation, and OpenAPI documentation generation.
- **SQLAlchemy 2.0 & SQLite**: SQLite allows zero-config local setup. SQLAlchemy ORM decouples models from SQLite, allowing seamless migration to PostgreSQL by updating `DATABASE_URL`.

### 2. Filesystem Asset Storage
- Generated PDF files are saved in `generated/` with paths saved in the database. Storing PDF files on the filesystem rather than inside SQLite BLOB columns keeps database backups small and enables efficient streaming downloads via FastAPI `FileResponse`.

---

## ⚡ BackgroundTasks Architecture & Limitations

### Why FastAPI `BackgroundTasks` Was Chosen
FastAPI's built-in `BackgroundTasks` executes worker tasks in an in-process thread pool. This satisfies the requirement for non-blocking asynchronous bulk execution without introducing heavy external message queue infrastructure (Celery, Redis, RabbitMQ) for local assignment execution.

### Important Architectural Limitations
- **In-Process Scope**: `BackgroundTasks` runs in the same process as the web server. If the server process crashes or is restarted while processing a job, queued in-memory background tasks will be interrupted.
- **Worker Scaling**: Processing is constrained to the host machine's thread/CPU pool.
- **Production Recommendation**: For production-scale workloads with high job volume, `BackgroundTasks` should be replaced with a distributed task queue system like **Celery** or **ARQ** backed by **Redis** or **RabbitMQ**.

---

## 🔮 Future Production Enhancements

1. **Distributed Task Queue**: Deploy Celery/ARQ with Redis for durable task persistence and worker auto-scaling.
2. **PostgreSQL Relational DB**: Upgrade from SQLite to PostgreSQL to handle high-concurrency database writes.
3. **Cloud Object Storage**: Save PDF certificates to Amazon S3 / Google Cloud Storage and deliver pre-signed URLs.
4. **Authentication & Authorization**: Implement OAuth2 / JWT authentication to secure job submission and file retrieval.
5. **Rate Limiting**: Add rate-limiting middleware to guard endpoints against submission bursts.
