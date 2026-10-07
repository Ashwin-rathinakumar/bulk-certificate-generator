from unittest.mock import patch
from app.services import job_service
from app.schemas.job import JobCreate, RecipientCreate
from app.services.certificate_service import certificate_service


def test_job_direct_lifecycle_completed(db_session):
    """Task 2: Test direct worker/service lifecycle for successful job."""
    job_in = JobCreate(
        certificate_title="Direct Worker Test",
        organization="Test Org",
        date="2026-10-07",
        recipients=[
            RecipientCreate(name="User 1", email="u1@example.com"),
            RecipientCreate(name="User 2", email="u2@example.com")
        ]
    )

    job = job_service.create_job(db=db_session, job_in=job_in)
    
    # 1. Job starts in PENDING before processing
    assert job.status == "pending"
    assert job.total_count == 2
    assert job.successful_count == 0
    assert job.failed_count == 0
    assert job.completed_at is None

    # 2. Execute process_bulk_job worker directly
    job_service.process_bulk_job(job.id)

    # Expire test session cache to see updates committed by worker session
    db_session.expire_all()

    # 3. Verify final state in DB
    refreshed_job = job_service.get_job(db=db_session, job_id=job.id)
    assert refreshed_job.status == "completed"
    assert refreshed_job.successful_count == 2
    assert refreshed_job.failed_count == 0
    assert refreshed_job.completed_at is not None


def test_job_direct_lifecycle_partial_failure(db_session):
    """Task 2: Test direct worker/service lifecycle for partial failure."""
    job_in = JobCreate(
        certificate_title="Partial Failure Test",
        organization="Test Org",
        date="2026-10-07",
        recipients=[
            RecipientCreate(name="User 1", email="u1@example.com"),
            RecipientCreate(name="User 2", email="u2@example.com")
        ]
    )

    job = job_service.create_job(db=db_session, job_in=job_in)
    assert job.status == "pending"

    real_generate = certificate_service.generate_certificate

    def side_effect(*args, **kwargs):
        if kwargs.get("recipient_email") == "u2@example.com":
            raise ValueError("Direct worker rendering failure")
        return real_generate(*args, **kwargs)

    with patch.object(certificate_service, "generate_certificate", side_effect=side_effect):
        job_service.process_bulk_job(job.id)

    db_session.expire_all()
    refreshed_job = job_service.get_job(db=db_session, job_id=job.id)
    assert refreshed_job.status == "completed_with_errors"
    assert refreshed_job.successful_count == 1
    assert refreshed_job.failed_count == 1


def test_job_direct_lifecycle_total_failure(db_session):
    """Task 2: Test direct worker/service lifecycle for total failure."""
    job_in = JobCreate(
        certificate_title="Total Failure Test",
        organization="Test Org",
        date="2026-10-07",
        recipients=[
            RecipientCreate(name="User 1", email="u1@example.com"),
            RecipientCreate(name="User 2", email="u2@example.com")
        ]
    )

    job = job_service.create_job(db=db_session, job_in=job_in)
    assert job.status == "pending"

    def side_effect(*args, **kwargs):
        raise RuntimeError("Total failure worker exception")

    with patch.object(certificate_service, "generate_certificate", side_effect=side_effect):
        job_service.process_bulk_job(job.id)

    db_session.expire_all()
    refreshed_job = job_service.get_job(db=db_session, job_id=job.id)
    assert refreshed_job.status == "failed"
    assert refreshed_job.successful_count == 0
    assert refreshed_job.failed_count == 2
