from pathlib import Path
from app.services.certificate_service import certificate_service
from app.services import job_service
from app.schemas.job import JobCreate, RecipientCreate


def test_certificate_file_generation_service(tmp_path):
    """Test 3: Direct certificate file generation service."""
    output_file_path = certificate_service.generate_certificate(
        recipient_name="Alice Smith",
        recipient_email="alice@example.com",
        certificate_title="AI & ML Bootcamp",
        organization="Google DeepMind",
        issue_date="2026-10-07",
        certificate_id=1,
        job_id=1
    )

    path = Path(output_file_path)
    assert path.exists()
    assert path.is_file()
    assert path.stat().st_size > 0
    assert path.suffix == ".pdf"


def test_long_recipient_name_rendering():
    """Task 2: Test rendering a very long recipient name safely without error or overflow."""
    long_name = "Dr. Bartholomew Christopher Montgomery-Wellington III Senior Specialist"
    output_file_path = certificate_service.generate_certificate(
        recipient_name=long_name,
        recipient_email="longname@example.com",
        certificate_title="Executive Leadership & Strategic Innovation Masterclass",
        organization="Global Academic Enterprise",
        issue_date="2026-10-07",
        certificate_id=101,
        job_id=10
    )

    path = Path(output_file_path)
    assert path.exists()
    assert path.is_file()
    assert path.stat().st_size > 0


def test_unicode_recipient_name_rendering():
    """Task 3: Test rendering names with international Unicode and special characters."""
    unicode_name = "José François Müller O'Connor"
    output_file_path = certificate_service.generate_certificate(
        recipient_name=unicode_name,
        recipient_email="unicode@example.com",
        certificate_title="International Language Studies",
        organization="World Institute",
        issue_date="2026-10-07",
        certificate_id=102,
        job_id=10
    )

    path = Path(output_file_path)
    assert path.exists()
    assert path.is_file()
    assert path.stat().st_size > 0


def test_date_formatting_and_rendering(client):
    """Task 4: Test deterministic ISO date formatting and PDF output generation."""
    payload = {
        "certificate_title": "Date Verification Course",
        "organization": "ISO Standards Board",
        "date": "2026-10-07",
        "recipients": [
            {"name": "Date User", "email": "dateuser@example.com"}
        ]
    }

    response = client.post("/api/v1/jobs", json=payload)
    assert response.status_code == 202
    job_id = response.json()["job_id"]

    certs_resp = client.get(f"/api/v1/jobs/{job_id}/certificates")
    cert = certs_resp.json()["certificates"][0]
    assert cert["status"] == "generated"


def test_moderate_bulk_job_batch(db_session, client):
    """Task 7: Test processing a moderate bulk batch (30 recipients) sequentially."""
    recipients = [
        RecipientCreate(name=f"Bulk User {i}", email=f"bulk_user_{i}@example.com")
        for i in range(1, 31)
    ]

    job_in = JobCreate(
        certificate_title="Batch Performance Test",
        organization="Scale Academy",
        date="2026-10-07",
        recipients=recipients
    )

    job = job_service.create_job(db=db_session, job_in=job_in)
    assert job.total_count == 30

    job_service.process_bulk_job(job.id)
    db_session.expire_all()

    refreshed_job = job_service.get_job(db=db_session, job_id=job.id)
    assert refreshed_job.status == "completed"
    assert refreshed_job.successful_count == 30
    assert refreshed_job.failed_count == 0
    assert refreshed_job.total_count == 30

    certs = job_service.get_job_certificates(db=db_session, job_id=job.id)
    assert len(certs) == 30
    for cert in certs:
        assert cert.status == "generated"
        assert Path(cert.file_path).exists()
