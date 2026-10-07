from unittest.mock import patch
from app.services.certificate_service import certificate_service


def test_download_successful_certificate(client):
    """Test 6: Downloading a successfully generated certificate PDF file."""
    payload = {
        "certificate_title": "DevOps Engineering",
        "organization": "Linux Foundation",
        "date": "2026-10-07",
        "recipients": [
            {"name": "Charlie Brown", "email": "charlie@example.com"}
        ]
    }

    create_resp = client.post("/api/v1/jobs", json=payload)
    job_id = create_resp.json()["job_id"]

    certs_resp = client.get(f"/api/v1/jobs/{job_id}/certificates")
    cert = certs_resp.json()["certificates"][0]
    cert_id = cert["id"]

    download_resp = client.get(f"/api/v1/certificates/{cert_id}")
    assert download_resp.status_code == 200
    assert download_resp.headers["content-type"] == "application/pdf"
    assert len(download_resp.content) > 0


def test_download_nonexistent_certificate(client):
    """Test downloading a non-existent certificate ID returns 404."""
    response = client.get("/api/v1/certificates/88888")
    assert response.status_code == 404
    assert response.json()["detail"] == "Certificate with ID 88888 not found"


def test_download_failed_certificate(client):
    """Test attempting to download a failed certificate returns HTTP 400 error."""
    payload = {
        "certificate_title": "Testing Title",
        "organization": "Testing Org",
        "date": "2026-10-07",
        "recipients": [
            {"name": "Failed User", "email": "failed.user@example.com"}
        ]
    }

    def side_effect(*args, **kwargs):
        raise ValueError("Rendering failure")

    with patch.object(certificate_service, "generate_certificate", side_effect=side_effect):
        create_resp = client.post("/api/v1/jobs", json=payload)
        job_id = create_resp.json()["job_id"]

    certs_resp = client.get(f"/api/v1/jobs/{job_id}/certificates")
    cert = certs_resp.json()["certificates"][0]
    cert_id = cert["id"]

    download_resp = client.get(f"/api/v1/certificates/{cert_id}")
    assert download_resp.status_code == 400
    assert "not available for download" in download_resp.json()["detail"]
