def test_health_check(client):
    """Test health check endpoint."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_create_bulk_job_success(client):
    """Test 1: Creating a generation job successfully."""
    payload = {
        "certificate_title": "Python Developer Workshop",
        "organization": "OpenAI Academy",
        "date": "2026-10-07",
        "recipients": [
            {"name": "Ashwin Rathinakumar", "email": "ashwin@example.com"},
            {"name": "Rahul Kumar", "email": "rahul@example.com"}
        ]
    }

    response = client.post("/api/v1/jobs", json=payload)
    assert response.status_code == 202
    data = response.json()

    assert "job_id" in data
    assert data["status"] == "pending"
    assert data["total_count"] == 2

    job_id = data["job_id"]

    # Retrieve status (Test 4: Job status & progress)
    status_response = client.get(f"/api/v1/jobs/{job_id}")
    assert status_response.status_code == 200
    status_data = status_response.json()

    assert status_data["job_id"] == job_id
    assert status_data["status"] == "completed"
    assert status_data["total_count"] == 2
    assert status_data["successful_count"] == 2
    assert status_data["failed_count"] == 0
    assert status_data["pending_count"] == 0
    assert status_data["progress_percentage"] == 100


def test_get_nonexistent_job(client):
    """Test requesting status for a non-existent job ID."""
    response = client.get("/api/v1/jobs/99999")
    assert response.status_code == 404
    assert response.json()["detail"] == "Job with ID 99999 not found"


def test_get_job_certificates(client):
    """Test listing generated certificates for a job."""
    payload = {
        "certificate_title": "FastAPI Masterclass",
        "organization": "Tech Corp",
        "date": "2026-10-07",
        "recipients": [
            {"name": "Jane Doe", "email": "jane@example.com"}
        ]
    }

    create_resp = client.post("/api/v1/jobs", json=payload)
    job_id = create_resp.json()["job_id"]

    certs_resp = client.get(f"/api/v1/jobs/{job_id}/certificates")
    assert certs_resp.status_code == 200
    data = certs_resp.json()

    assert data["job_id"] == job_id
    assert len(data["certificates"]) == 1
    cert = data["certificates"][0]
    assert cert["recipient_name"] == "Jane Doe"
    assert cert["recipient_email"] == "jane@example.com"
    assert cert["status"] == "generated"
    assert cert["download_url"] == f"/api/v1/certificates/{cert['id']}"
