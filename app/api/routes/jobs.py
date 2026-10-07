from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.schemas.job import (
    JobCreate,
    JobCreateResponse,
    JobStatusResponse,
    JobCertificatesResponse,
)
from app.schemas.certificate import CertificateItemResponse
from app.services import job_service

router = APIRouter(prefix="/jobs", tags=["Jobs"])


@router.post(
    "",
    response_model=JobCreateResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Submit a bulk certificate generation job"
)
def create_bulk_job(
    job_in: JobCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    Creates a new bulk certificate generation job and enqueues background processing.
    """
    job = job_service.create_job(db=db, job_in=job_in)
    
    # Enqueue background task for generation
    background_tasks.add_task(job_service.process_bulk_job, job.id)

    return JobCreateResponse(
        job_id=job.id,
        status=job.status,
        total_count=job.total_count
    )


@router.get(
    "/{job_id}",
    response_model=JobStatusResponse,
    summary="Get job status and progress"
)
def get_job_status(job_id: int, db: Session = Depends(get_db)):
    """
    Retrieves the processing status, progress percentage, and generation counts for a job.
    """
    job = job_service.get_job(db=db, job_id=job_id)
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job with ID {job_id} not found"
        )
    return job_service.build_job_status_response(job)


@router.get(
    "/{job_id}/certificates",
    response_model=JobCertificatesResponse,
    summary="List certificates for a job"
)
def get_job_certificates(job_id: int, db: Session = Depends(get_db)):
    """
    Retrieves all recipient certificates for a specific bulk job.
    """
    job = job_service.get_job(db=db, job_id=job_id)
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job with ID {job_id} not found"
        )

    cert_items = []
    for cert in job.certificates:
        download_url = f"/api/v1/certificates/{cert.id}" if cert.status == "generated" else None
        cert_items.append(
            CertificateItemResponse(
                id=cert.id,
                recipient_name=cert.recipient_name,
                recipient_email=cert.recipient_email,
                status=cert.status,
                download_url=download_url,
                error_message=cert.error_message
            )
        )

    return JobCertificatesResponse(job_id=job_id, certificates=cert_items)
