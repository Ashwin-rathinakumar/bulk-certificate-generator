from unittest.mock import patch
from app.services import job_service
from app.schemas.job import JobCreate, RecipientCreate


def test_background_task_uses_independent_session(db_session):
    """Task 4: Verify background task creates its own independent session."""
    job_in = JobCreate(
        certificate_title="Session Test",
        organization="Session Org",
        date="2026-10-07",
        recipients=[RecipientCreate(name="Session User", email="session@example.com")]
    )

    job = job_service.create_job(db=db_session, job_in=job_in)

    # Close the request-scoped db session explicitly to simulate request completion
    db_session.close()

    # Process bulk job directly — should acquire its own SessionLocal session, complete, and close it
    job_service.process_bulk_job(job.id)

    # Re-open session to verify background task persisted the updates
    reopened_job = job_service.get_job(db=db_session, job_id=job.id)
    assert reopened_job.status == "completed"
    assert reopened_job.successful_count == 1


def test_unhandled_job_level_exception_marks_job_failed(db_session):
    """Task 5: Verify unhandled top-level worker exception marks job status as failed."""
    job_in = JobCreate(
        certificate_title="Unhandled Error Test",
        organization="Error Org",
        date="2026-10-07",
        recipients=[RecipientCreate(name="Error User", email="error@example.com")]
    )

    job = job_service.create_job(db=db_session, job_in=job_in)
    assert job.status == "pending"

    # Simulate an unexpected top-level exception during Certificate query inside process_bulk_job
    with patch("sqlalchemy.orm.Query.all", side_effect=RuntimeError("Database query fault")):
        job_service.process_bulk_job(job.id)

    db_session.expire_all()
    # Job should not be stuck in processing; it should be marked failed
    refreshed_job = job_service.get_job(db=db_session, job_id=job.id)
    assert refreshed_job.status == "failed"
