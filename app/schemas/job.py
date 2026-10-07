from datetime import datetime, date as date_type
from typing import List
from pydantic import BaseModel, ConfigDict, Field, field_validator
from app.schemas.certificate import RecipientCreate, CertificateItemResponse


class JobCreate(BaseModel):
    """Schema for bulk job creation request."""

    certificate_title: str = Field(..., description="Title of the certificate", max_length=255)
    organization: str = Field(..., description="Issuing organization name", max_length=255)
    date: str = Field(..., description="Certificate issue date (YYYY-MM-DD)")
    recipients: List[RecipientCreate] = Field(
        ...,
        description="List of certificate recipients",
        min_length=1
    )

    @field_validator("certificate_title", "organization")
    @classmethod
    def validate_non_blank(cls, v: str) -> str:
        cleaned = v.strip()
        if not cleaned:
            raise ValueError("Field must not be blank")
        return cleaned

    @field_validator("date")
    @classmethod
    def validate_date(cls, v: str) -> str:
        cleaned = v.strip()
        if not cleaned:
            raise ValueError("Date must not be blank")
        # Validate format YYYY-MM-DD
        try:
            date_type.fromisoformat(cleaned)
        except ValueError:
            raise ValueError("Date must be a valid ISO format string (YYYY-MM-DD)")
        return cleaned


class JobCreateResponse(BaseModel):
    """Schema returned immediately upon creating a job."""

    job_id: int
    status: str
    total_count: int


class JobStatusResponse(BaseModel):
    """Schema for tracking job status and progress."""

    job_id: int
    status: str
    total_count: int
    successful_count: int
    failed_count: int
    pending_count: int
    progress_percentage: int

    model_config = ConfigDict(from_attributes=True)


class JobCertificatesResponse(BaseModel):
    """Schema for listing all certificates belonging to a job."""

    job_id: int
    certificates: List[CertificateItemResponse]
