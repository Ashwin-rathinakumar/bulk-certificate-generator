import os
from pathlib import Path
from app.services import job_service
from app.schemas.job import JobCreate, RecipientCreate
from app.core.config import settings


def test_path_traversal_safety_in_recipient_input(client, db_session):
    """Task 8: Verify recipient names with path traversal sequences do not affect output paths."""
    malicious_name = "../../../etc/passwd_or_secret"
    job_in = JobCreate(
        certificate_title="Path Traversal Test",
        organization="Security Org",
        date="2026-10-07",
        recipients=[RecipientCreate(name=malicious_name, email="hacker@example.com")]
    )

    job = job_service.create_job(db=db_session, job_in=job_in)
    job_service.process_bulk_job(job.id)

    cert = job_service.get_certificate(db=db_session, certificate_id=job.certificates[0].id)
    assert cert.status == "generated"
    assert cert.file_path is not None

    file_path = Path(cert.file_path)
    # Ensure generated file resides inside configured generated certificates directory
    assert file_path.exists()
    assert file_path.parent.resolve() == settings.generated_dir_path.resolve()
    assert "passwd" not in file_path.name

    # Download certificate via API
    download_resp = client.get(f"/api/v1/certificates/{cert.id}")
    assert download_resp.status_code == 200
    assert download_resp.headers["content-type"] == "application/pdf"


def test_download_missing_file_on_disk_returns_404(client, db_session):
    """Task 7: Verify downloading a certificate whose file was deleted from disk returns 404."""
    job_in = JobCreate(
        certificate_title="Missing File Test",
        organization="Test Org",
        date="2026-10-07",
        recipients=[RecipientCreate(name="Missing File User", email="missing@example.com")]
    )

    job = job_service.create_job(db=db_session, job_in=job_in)
    job_service.process_bulk_job(job.id)

    cert = job_service.get_certificate(db=db_session, certificate_id=job.certificates[0].id)
    file_path = Path(cert.file_path)
    assert file_path.exists()

    # Delete generated file from disk to simulate missing file scenario
    os.remove(file_path)

    response = client.get(f"/api/v1/certificates/{cert.id}")
    assert response.status_code == 404
    assert "could not be found on disk" in response.json()["detail"]
