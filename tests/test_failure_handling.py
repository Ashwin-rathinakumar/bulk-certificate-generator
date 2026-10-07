from unittest.mock import patch
from app.services.certificate_service import certificate_service


def test_individual_certificate_failure_isolation(client):
    """Test 5: Individual certificate failure isolation during bulk processing using mocking."""
    payload = {
        "certificate_title": "Data Science Fundamentals",
        "organization": "Data Academy",
        "date": "2026-10-07",
        "recipients": [
            {"name": "User One", "email": "user1@example.com"},
            {"name": "User Two", "email": "user2@example.com"},
            {"name": "User Three", "email": "user3@example.com"}
        ]
    }

    real_generate = certificate_service.generate_certificate

    def side_effect(*args, **kwargs):
        # Deliberately raise exception for one recipient without magic names/emails in production code
        if kwargs.get("recipient_email") == "user2@example.com":
            raise ValueError("Simulated rendering exception for user2")
        return real_generate(*args, **kwargs)

    with patch.object(certificate_service, "generate_certificate", side_effect=side_effect):
        response = client.post("/api/v1/jobs", json=payload)
        assert response.status_code == 202
        job_id = response.json()["job_id"]

    # Retrieve job status
    status_resp = client.get(f"/api/v1/jobs/{job_id}")
    assert status_resp.status_code == 200
    status_data = status_resp.json()

    assert status_data["status"] == "completed_with_errors"
    assert status_data["total_count"] == 3
    assert status_data["successful_count"] == 2
    assert status_data["failed_count"] == 1
    assert status_data["pending_count"] == 0

    # Retrieve job certificates detail
    certs_resp = client.get(f"/api/v1/jobs/{job_id}/certificates")
    assert certs_resp.status_code == 200
    certs_data = certs_resp.json()["certificates"]

    assert len(certs_data) == 3

    success_certs = [c for c in certs_data if c["status"] == "generated"]
    failed_certs = [c for c in certs_data if c["status"] == "failed"]

    assert len(success_certs) == 2
    assert len(failed_certs) == 1

    failed_cert = failed_certs[0]
    assert failed_cert["recipient_email"] == "user2@example.com"
    assert failed_cert["error_message"] is not None
    assert "Simulated rendering exception" in failed_cert["error_message"]
    assert failed_cert["download_url"] is None

    # Verify remaining successful certificates remain retrievable
    for sc in success_certs:
        download_resp = client.get(f"/api/v1/certificates/{sc['id']}")
        assert download_resp.status_code == 200
        assert download_resp.headers["content-type"] == "application/pdf"


def test_all_certificates_failure(client):
    """Test scenario where every certificate generation in a job fails."""
    payload = {
        "certificate_title": "Advanced Quantum Computing",
        "organization": "Quantum Institute",
        "date": "2026-10-07",
        "recipients": [
            {"name": "Alice Green", "email": "alice.g@example.com"},
            {"name": "Bob White", "email": "bob.w@example.com"}
        ]
    }

    def side_effect(*args, **kwargs):
        raise RuntimeError("System-wide rendering failure")

    with patch.object(certificate_service, "generate_certificate", side_effect=side_effect):
        response = client.post("/api/v1/jobs", json=payload)
        assert response.status_code == 202
        job_id = response.json()["job_id"]

    # Verify job status
    status_resp = client.get(f"/api/v1/jobs/{job_id}")
    assert status_resp.status_code == 200
    status_data = status_resp.json()

    assert status_data["status"] == "failed"
    assert status_data["total_count"] == 2
    assert status_data["successful_count"] == 0
    assert status_data["failed_count"] == 2
    assert status_data["pending_count"] == 0

    # Verify each failed certificate has an error reason stored
    certs_resp = client.get(f"/api/v1/jobs/{job_id}/certificates")
    assert certs_resp.status_code == 200
    certs_data = certs_resp.json()["certificates"]

    assert len(certs_data) == 2
    for cert in certs_data:
        assert cert["status"] == "failed"
        assert cert["error_message"] is not None
        assert "System-wide rendering failure" in cert["error_message"]
        assert cert["download_url"] is None
