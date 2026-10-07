from app.models.job import Job
from app.services import job_service


def test_progress_calculation_zero_processed():
    """Task 3: Progress starts at 0 for a new job with 0 processed."""
    job = Job(
        id=1,
        certificate_title="Test Title",
        organization="Test Org",
        issue_date="2026-10-07",
        status="pending",
        total_count=4,
        successful_count=0,
        failed_count=0
    )

    response = job_service.build_job_status_response(job)
    assert response.progress_percentage == 0
    assert response.pending_count == 4
    assert response.successful_count + response.failed_count + response.pending_count == response.total_count


def test_progress_calculation_partial_processing():
    """Task 3: Progress calculation during partial processing."""
    job = Job(
        id=2,
        certificate_title="Test Title",
        organization="Test Org",
        issue_date="2026-10-07",
        status="processing",
        total_count=4,
        successful_count=1,
        failed_count=0
    )

    response = job_service.build_job_status_response(job)
    assert response.progress_percentage == 25
    assert response.pending_count == 3
    assert response.successful_count + response.failed_count + response.pending_count == response.total_count


def test_progress_calculation_all_successful():
    """Task 3: Progress calculation when all certificates succeed."""
    job = Job(
        id=3,
        certificate_title="Test Title",
        organization="Test Org",
        issue_date="2026-10-07",
        status="completed",
        total_count=5,
        successful_count=5,
        failed_count=0
    )

    response = job_service.build_job_status_response(job)
    assert response.progress_percentage == 100
    assert response.pending_count == 0
    assert response.successful_count + response.failed_count + response.pending_count == response.total_count


def test_progress_calculation_partial_failure():
    """Task 3: Failed certificates still count toward processing progress."""
    job = Job(
        id=4,
        certificate_title="Test Title",
        organization="Test Org",
        issue_date="2026-10-07",
        status="completed_with_errors",
        total_count=10,
        successful_count=8,
        failed_count=2
    )

    response = job_service.build_job_status_response(job)
    assert response.progress_percentage == 100
    assert response.pending_count == 0
    assert response.successful_count + response.failed_count + response.pending_count == response.total_count


def test_progress_calculation_all_failure():
    """Task 3: Progress calculation when all certificates fail."""
    job = Job(
        id=5,
        certificate_title="Test Title",
        organization="Test Org",
        issue_date="2026-10-07",
        status="failed",
        total_count=3,
        successful_count=0,
        failed_count=3
    )

    response = job_service.build_job_status_response(job)
    assert response.progress_percentage == 100
    assert response.pending_count == 0
    assert response.successful_count + response.failed_count + response.pending_count == response.total_count


def test_progress_calculation_clamping_bounds():
    """Task 3: Verify progress percentage is safely clamped between 0 and 100."""
    # Test upper bound clamping if counts exceed total unexpectedly
    job_over = Job(
        id=6,
        certificate_title="Test Title",
        organization="Test Org",
        issue_date="2026-10-07",
        status="completed",
        total_count=2,
        successful_count=3,
        failed_count=0
    )
    res_over = job_service.build_job_status_response(job_over)
    assert res_over.progress_percentage == 100

    # Test zero total count edge case
    job_zero = Job(
        id=7,
        certificate_title="Test Title",
        organization="Test Org",
        issue_date="2026-10-07",
        status="pending",
        total_count=0,
        successful_count=0,
        failed_count=0
    )
    res_zero = job_service.build_job_status_response(job_zero)
    assert res_zero.progress_percentage == 0
