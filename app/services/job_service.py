import logging
from datetime import datetime, timezone
from typing import List, Optional
from sqlalchemy.orm import Session
import app.core.database as database_module
from app.models.job import Job
from app.models.certificate import Certificate
from app.schemas.job import JobCreate, JobStatusResponse
from app.services.certificate_service import certificate_service

logger = logging.getLogger(__name__)


def create_job(db: Session, job_in: JobCreate) -> Job:
    """
    Creates a new bulk certificate job and associated recipient certificate records.
    
    Args:
        db: Active SQLAlchemy database session.
        job_in: Validated Pydantic JobCreate payload.

    Returns:
        Job: The created SQLAlchemy Job instance.
    """
    job = Job(
        certificate_title=job_in.certificate_title,
        organization=job_in.organization,
        issue_date=job_in.date,
        status="pending",
        total_count=len(job_in.recipients),
        successful_count=0,
        failed_count=0
    )
    db.add(job)
    db.flush()  # Populates job.id

    for recipient in job_in.recipients:
        cert = Certificate(
            job_id=job.id,
            recipient_name=recipient.name,
            recipient_email=str(recipient.email),
            status="pending"
        )
        db.add(cert)

    db.commit()
    db.refresh(job)
    return job


def process_bulk_job(job_id: int) -> None:
    """
    Background worker function to process certificate generation for a job.
    Processes each recipient independently, isolating failures.
    
    Args:
        job_id: ID of the Job to process.
    """
    # Create DB session using dynamic lookup on database_module so tests can override SessionLocal
    db: Session = database_module.SessionLocal()
    try:
        job = db.query(Job).filter(Job.id == job_id).first()
        if not job:
            logger.error(f"Job with ID {job_id} not found for background processing.")
            return

        # Mark job as processing
        job.status = "processing"
        db.commit()

        # Fetch all pending certificates for this job
        certificates = db.query(Certificate).filter(Certificate.job_id == job_id).all()

        for cert in certificates:
            try:
                file_path = certificate_service.generate_certificate(
                    recipient_name=cert.recipient_name,
                    recipient_email=cert.recipient_email,
                    certificate_title=job.certificate_title,
                    organization=job.organization,
                    issue_date=job.issue_date,
                    certificate_id=cert.id,
                    job_id=job.id
                )
                cert.status = "generated"
                cert.file_path = file_path
                job.successful_count += 1
                logger.info(f"Successfully generated certificate {cert.id} for {cert.recipient_email}")
            except Exception as exc:
                logger.error(f"Failed to generate certificate {cert.id} for {cert.recipient_email}: {exc}")
                cert.status = "failed"
                cert.error_message = str(exc)
                job.failed_count += 1

            # Commit status updates after each certificate
            db.commit()

        # Update final job status
        if job.failed_count == job.total_count and job.total_count > 0:
            job.status = "failed"
        elif job.failed_count > 0:
            job.status = "completed_with_errors"
        else:
            job.status = "completed"

        job.completed_at = datetime.now(timezone.utc)
        db.commit()
        logger.info(f"Finished processing job {job_id} with status '{job.status}'")

    except Exception as exc:
        logger.critical(f"Unhandled error in background job processing for job {job_id}: {exc}")
        try:
            job = db.query(Job).filter(Job.id == job_id).first()
            if job:
                job.status = "failed"
                db.commit()
        except Exception:
            pass
    finally:
        db.close()


def get_job(db: Session, job_id: int) -> Optional[Job]:
    """Retrieves a Job record by ID."""
    return db.query(Job).filter(Job.id == job_id).first()


def get_job_certificates(db: Session, job_id: int) -> Optional[List[Certificate]]:
    """Retrieves all certificate records for a given job ID."""
    job = get_job(db, job_id)
    if not job:
        return None
    return db.query(Certificate).filter(Certificate.job_id == job_id).all()


def get_certificate(db: Session, certificate_id: int) -> Optional[Certificate]:
    """Retrieves a Certificate record by ID."""
    return db.query(Certificate).filter(Certificate.id == certificate_id).first()


def build_job_status_response(job: Job) -> JobStatusResponse:
    """Calculates progress metrics and returns formatted JobStatusResponse schema."""
    processed = job.successful_count + job.failed_count
    pending_count = max(0, job.total_count - processed)
    
    if job.total_count > 0:
        raw_percentage = int((processed / job.total_count) * 100)
        progress_percentage = min(100, max(0, raw_percentage))
    else:
        progress_percentage = 0

    return JobStatusResponse(
        job_id=job.id,
        status=job.status,
        total_count=job.total_count,
        successful_count=job.successful_count,
        failed_count=job.failed_count,
        pending_count=pending_count,
        progress_percentage=progress_percentage
    )
