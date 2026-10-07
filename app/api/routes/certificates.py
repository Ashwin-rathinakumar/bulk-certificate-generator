from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.services import job_service

router = APIRouter(prefix="/certificates", tags=["Certificates"])


@router.get(
    "/{certificate_id}",
    summary="Download generated certificate file"
)
def download_certificate(certificate_id: int, db: Session = Depends(get_db)):
    """
    Retrieves and streams the generated PDF certificate for a recipient.
    Returns 404 if certificate does not exist.
    Returns 400 if certificate failed to generate or is missing.
    """
    cert = job_service.get_certificate(db=db, certificate_id=certificate_id)
    if not cert:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Certificate with ID {certificate_id} not found"
        )

    if cert.status != "generated" or not cert.file_path:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                f"Certificate {certificate_id} is not available for download. "
                f"Status: {cert.status}. Error: {cert.error_message or 'Generation pending or failed'}"
            )
        )

    file_path = Path(cert.file_path)
    if not file_path.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Certificate file for ID {certificate_id} could not be found on disk"
        )

    safe_filename = f"certificate_{cert.id}_{cert.recipient_name.replace(' ', '_')}.pdf"
    return FileResponse(
        path=file_path,
        media_type="application/pdf",
        filename=safe_filename
    )
