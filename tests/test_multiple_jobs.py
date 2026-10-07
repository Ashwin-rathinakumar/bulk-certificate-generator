from unittest.mock import patch
from app.services import job_service
from app.schemas.job import JobCreate, RecipientCreate
from app.services.certificate_service import certificate_service


def test_multiple_jobs_concurrent_isolation(db_session, client):
    """Task 6: Test processing multiple jobs without state interference."""
    # Create Job 1 (2 recipients)
    job_1_in = JobCreate(
        certificate_title="Job One Workshop",
        organization="Org One",
        date="2026-10-07",
        recipients=[
            RecipientCreate(name="Job1 Recipient1", email="j1r1@example.com"),
            RecipientCreate(name="Job1 Recipient2", email="j1r2@example.com")
        ]
    )
    job1 = job_service.create_job(db=db_session, job_in=job_1_in)

    # Create Job 2 (3 recipients)
    job_2_in = JobCreate(
        certificate_title="Job Two Masterclass",
        organization="Org Two",
        date="2026-10-07",
        recipients=[
            RecipientCreate(name="Job2 Recipient1", email="j2r1@example.com"),
            RecipientCreate(name="Job2 Recipient2", email="j2r2@example.com"),
            RecipientCreate(name="Job2 Recipient3", email="j2r3@example.com")
        ]
    )
    job2 = job_service.create_job(db=db_session, job_in=job_2_in)

    assert job1.id != job2.id
    assert job1.status == "pending"
    assert job2.status == "pending"

    # Process Job 1 to completion
    job_service.process_bulk_job(job1.id)
    db_session.expire_all()

    # Verify Job 1 state
    status1 = client.get(f"/api/v1/jobs/{job1.id}").json()
    assert status1["status"] == "completed"
    assert status1["total_count"] == 2
    assert status1["successful_count"] == 2
    assert status1["failed_count"] == 0
    assert status1["progress_percentage"] == 100

    # Verify Job 2 remains pending and unaffected
    status2_before = client.get(f"/api/v1/jobs/{job2.id}").json()
    assert status2_before["status"] == "pending"
    assert status2_before["total_count"] == 3
    assert status2_before["successful_count"] == 0
    assert status2_before["failed_count"] == 0
    assert status2_before["progress_percentage"] == 0

    # Process Job 2 with partial failure
    real_generate = certificate_service.generate_certificate

    def side_effect(*args, **kwargs):
        if kwargs.get("recipient_email") == "j2r2@example.com":
            raise ValueError("Failure in Job 2 recipient 2")
        return real_generate(*args, **kwargs)

    with patch.object(certificate_service, "generate_certificate", side_effect=side_effect):
        job_service.process_bulk_job(job2.id)

    db_session.expire_all()

    # Verify Job 2 state after processing
    status2_after = client.get(f"/api/v1/jobs/{job2.id}").json()
    assert status2_after["status"] == "completed_with_errors"
    assert status2_after["total_count"] == 3
    assert status2_after["successful_count"] == 2
    assert status2_after["failed_count"] == 1
    assert status2_after["progress_percentage"] == 100

    # Re-verify Job 1 state remains unchanged
    status1_recheck = client.get(f"/api/v1/jobs/{job1.id}").json()
    assert status1_recheck["status"] == "completed"
    assert status1_recheck["successful_count"] == 2

    # Verify certificate isolation per job
    certs1 = client.get(f"/api/v1/jobs/{job1.id}/certificates").json()["certificates"]
    certs2 = client.get(f"/api/v1/jobs/{job2.id}/certificates").json()["certificates"]

    assert len(certs1) == 2
    assert len(certs2) == 3
    assert {c["recipient_email"] for c in certs1} == {"j1r1@example.com", "j1r2@example.com"}
    assert {c["recipient_email"] for c in certs2} == {"j2r1@example.com", "j2r2@example.com", "j2r3@example.com"}
