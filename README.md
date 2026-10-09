# Bulk Certificate Generator Backend

A RESTful backend service built with **FastAPI** that validates recipient data, generates personalized PDF certificates in bulk, tracks job progress, and provides APIs to retrieve generated certificates.

## Overview

Generating certificates individually is time-consuming and inefficient when handling large recipient lists. This project provides a bulk-processing API that accepts a single request containing multiple recipients and generates a personalized certificate for each recipient using a predefined template.

The application validates incoming requests, stores job and certificate metadata in a relational database, processes generation tasks in the background, and exposes endpoints for monitoring progress and downloading generated PDFs.

### Key Features

* **Bulk processing:** Generate certificates for multiple recipients through a single API request.
* **Input validation:** Validate recipient details and certificate metadata using Pydantic.
* **PDF generation:** Create personalized certificates from a predefined image template.
* **Background execution:** Process generation jobs without keeping the initial HTTP request open.
* **Job tracking:** Monitor job status, completion percentage, and success/failure counts.
* **Failure isolation:** Record individual certificate failures without unnecessarily stopping the remaining batch.
* **Certificate retrieval:** List job results and download successfully generated PDFs.
* **Persistent metadata:** Store job and certificate records using SQLAlchemy and SQLite.
* **Automated tests:** Cover validation, generation, lifecycle transitions, progress, failure handling, and retrieval.

## Technology Stack

| Technology     | Purpose                                 |
| -------------- | --------------------------------------- |
| Python 3.12+   | Application development                 |
| FastAPI        | REST API framework                      |
| Pydantic       | Request validation and response schemas |
| SQLAlchemy 2.x | Database ORM                            |
| SQLite         | Relational metadata storage             |
| Pillow         | Template rendering and image processing |
| Uvicorn        | ASGI application server                 |
| Pytest         | Automated testing                       |
| HTTPX          | API testing                             |

## Architecture

```text
                    Client
                      |
                      v
              FastAPI REST API
                      |
                      v
              Request Validation
                  (Pydantic)
                      |
                      v
             Create Job and Records
                 (SQLAlchemy)
                      |
                      v
              Return HTTP 202
                      |
                      v
            Background Job Processor
                      |
             +--------+--------+
             |                 |
             v                 v
       Generate PDF       Record Failure
             |                 |
             v                 v
       Save PDF File     Update Error Status
             |                 |
             +--------+--------+
                      |
                      v
             Update Job Progress
                      |
                      v
             Status and Download APIs
```

### Processing Workflow

1. The client submits a bulk certificate generation request.
2. Pydantic validates the request structure and recipient data.
3. The application creates a generation job and associated certificate records in the database.
4. The API returns `202 Accepted` with the job identifier.
5. A background task processes the recipients and generates personalized PDFs.
6. Each certificate is marked as generated or failed, with relevant error information recorded for failures.
7. The overall job status and progress are updated as processing continues.
8. The client polls the status endpoint, lists the job's certificates, and downloads completed PDFs.

## Project Structure

```text
bulk-certificate-generator/
├── app/
│   ├── main.py
│   ├── core/
│   │   ├── config.py
│   │   └── database.py
│   ├── models/
│   │   ├── job.py
│   │   └── certificate.py
│   ├── schemas/
│   │   ├── job.py
│   │   └── certificate.py
│   ├── services/
│   │   ├── job_service.py
│   │   └── certificate_service.py
│   └── api/
│       └── routes/
│           ├── jobs.py
│           └── certificates.py
├── templates/
│   └── certificate_template.png
├── generated/
│   └── .gitkeep
├── tests/
│   ├── conftest.py
│   ├── test_jobs.py
│   ├── test_validation.py
│   ├── test_generation.py
│   ├── test_failure_handling.py
│   ├── test_retrieval.py
│   ├── test_lifecycle.py
│   ├── test_progress.py
│   ├── test_session_safety.py
│   ├── test_multiple_jobs.py
│   └── test_security_retrieval.py
├── .env.example
├── .gitignore
├── requirements.txt
└── README.md
```

## Prerequisites

* Python 3.12 or later
* pip
* Git (optional, for cloning the repository)

## Installation and Setup

### 1. Clone the repository

```bash
git clone https://github.com/Ashwin-rathinakumar/bulk-certificate-generator.git
cd bulk-certificate-generator
```

### 2. Create a virtual environment

**Windows PowerShell**

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

**Linux/macOS**

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Install dependencies

```bash
python -m pip install --upgrade pip
pip install -r requirements.txt
```

### 4. Configure environment variables

The application includes an `.env.example` file. Create a local `.env` file if you need to override the default configuration.

```powershell
Copy-Item .env.example .env
```

Default configuration:

```dotenv
DATABASE_URL=sqlite:///./certificates.db
GENERATED_CERTIFICATES_DIR=generated
CERTIFICATE_TEMPLATE_PATH=templates/certificate_template.png
```

The database and output directories are initialized or used by the application according to its configuration.

### 5. Run the application

```bash
uvicorn app.main:app --reload
```

The API is available at:

* API base URL: `http://127.0.0.1:8000`
* Interactive Swagger documentation: `http://127.0.0.1:8000/docs`
* ReDoc documentation: `http://127.0.0.1:8000/redoc`
* Health endpoint: `http://127.0.0.1:8000/health`

## API Documentation

The following endpoints form the primary API workflow.

| Method | Endpoint                                | Description                             |
| ------ | --------------------------------------- | --------------------------------------- |
| `GET`  | `/health`                               | Check application health                |
| `POST` | `/api/v1/jobs`                          | Submit a bulk generation job            |
| `GET`  | `/api/v1/jobs/{job_id}`                 | Retrieve job status and progress        |
| `GET`  | `/api/v1/jobs/{job_id}/certificates`    | List certificates associated with a job |
| `GET`  | `/api/v1/certificates/{certificate_id}` | Download a generated certificate        |

### 1. Create a generation job

**Request**

`POST /api/v1/jobs`

```json
{
  "certificate_title": "Certificate of Achievement",
  "organization": "Example Organization",
  "date": "2026-10-09",
  "recipients": [
    {
      "name": "Alice Johnson",
      "email": "alice@example.com"
    },
    {
      "name": "Bob Smith",
      "email": "bob@example.com"
    }
  ]
}
```

**Expected response — HTTP `202 Accepted`**

```json
{
  "job_id": 1,
  "status": "pending",
  "total_count": 2
}
```

The identifiers and initial status in this example are illustrative. The actual response depends on the application state and response schema.

### 2. Check job status and progress

**Request**

```http
GET /api/v1/jobs/1
```

The response provides the job status, total recipients, success and failure counts, and progress percentage.

Possible job statuses:

* `pending` — waiting to be processed.
* `processing` — certificate generation is underway.
* `completed` — all certificates were generated successfully.
* `completed_with_errors` — processing finished with a mixture of successes and failures.
* `failed` — the job encountered a terminal failure according to the application's status rules.

### 3. List certificates for a job

**Request**

```http
GET /api/v1/jobs/1/certificates
```

The response lists certificate records associated with the job, including their statuses, download URLs, and error messages where applicable.

Possible certificate statuses:

* `pending`
* `generated`
* `failed`

### 4. Download a certificate

**Request**

```http
GET /api/v1/certificates/{certificate_id}
```

Successfully generated certificates are returned as downloadable PDF files. A certificate that is still pending or has failed cannot be downloaded as a successful output.

The application also handles unavailable certificate records and missing output files through appropriate error responses.

## Error Handling and Validation

The API uses Pydantic schemas to validate incoming requests before creating generation jobs.

Validation covers fields such as:

* Certificate title and organization
* Date format
* Recipient list
* Recipient names
* Email addresses
* Configured field-length constraints

Malformed requests are rejected with validation errors. During background processing, individual certificate-generation failures are recorded against the relevant certificate so that other recipients can continue to be processed.

## Database Design

The application uses two primary relational entities.

**Generation Job**

Stores job-level information, including status, recipient totals, progress-related counts, and lifecycle metadata.

**Certificate**

Stores recipient-specific certificate information, generation status, associated job ID, output file path, and error details where applicable.

A generation job can be associated with multiple certificate records through a one-to-many relationship.

SQLite is used to keep local setup simple. SQLAlchemy provides an ORM layer that supports migration to another relational database with appropriate configuration and migration work.

## Testing

The project uses Pytest and HTTPX to test the API and service behavior.

Run the complete test suite from the repository root:

```bash
python -m pytest -v
```

Run tests with coverage if `pytest-cov` is installed:

```bash
python -m pytest --cov=app --cov-report=term-missing
```

The suite is organized around the following areas:

| Test module                  | Focus                                          |
| ---------------------------- | ---------------------------------------------- |
| `test_jobs.py`               | Job creation and API behavior                  |
| `test_validation.py`         | Invalid request handling                       |
| `test_generation.py`         | PDF generation, long names, and Unicode inputs |
| `test_failure_handling.py`   | Per-certificate failure isolation              |
| `test_retrieval.py`          | Certificate listing and download behavior      |
| `test_lifecycle.py`          | Job status transitions                         |
| `test_progress.py`           | Progress and completion counts                 |
| `test_session_safety.py`     | Database session handling                      |
| `test_multiple_jobs.py`      | Handling separate jobs                         |
| `test_security_retrieval.py` | Retrieval and file-path security cases         |

Run the tests locally before submitting and report the actual test results rather than relying on previously recorded results.

## Design Decisions

### FastAPI

FastAPI provides request validation, automatic OpenAPI documentation, and a straightforward way to expose REST endpoints.

### Background processing

The API uses FastAPI `BackgroundTasks` to start certificate processing after the initial response. This keeps the request lifecycle separate from the full batch-generation workflow.

### Database persistence

SQLAlchemy and SQLite store job and certificate metadata, making job status and retrieval information available through subsequent API requests.

### Filesystem-based PDF storage

Generated certificates are saved as PDF files, while the database stores their associated metadata and paths. This avoids storing binary PDF content directly in database rows.

### Per-recipient error isolation

Certificate generation is handled individually, allowing a failure for one recipient to be recorded without automatically terminating the entire batch.

## Limitations

* FastAPI `BackgroundTasks` is an in-process mechanism, not a durable distributed job queue. A process crash or restart can interrupt work that has not completed.
* The local SQLite database and filesystem-based output storage are intended for a straightforward assignment deployment.
* Authentication, authorization, rate limiting, and production-grade multi-worker job coordination are outside the current scope.

For a production deployment, the architecture could be extended with a durable worker queue, PostgreSQL, object storage, monitoring, and appropriate access controls.

## Future Improvements

* Introduce a durable job queue such as Celery or ARQ.
* Support PostgreSQL for deployments with concurrent workloads.
* Store generated certificates in object storage such as Amazon S3 or Google Cloud Storage.
* Add authentication, authorization, and rate limiting.
* Add structured logging, metrics, and operational monitoring.
* Improve delivery guarantees and recovery for interrupted jobs.

## Assignment Scope

This implementation focuses on the requested backend workflow: bulk requests, validation, personalized certificate generation from one predefined template, job progress tracking, partial-failure handling, certificate retrieval, automated testing, and setup documentation.

The project deliberately avoids adding a template editor or a multi-template design system because those features are outside the assignment's stated scope.

## License

No license has been specified. Add an appropriate license if you intend to distribute the project for reuse.
