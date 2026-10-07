from datetime import datetime
from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator


class RecipientCreate(BaseModel):
    """Schema for individual recipient input validation."""

    name: str = Field(..., description="Recipient full name", max_length=255)
    email: EmailStr = Field(..., description="Recipient valid email address")

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        cleaned = v.strip()
        if not cleaned:
            raise ValueError("Recipient name must not be blank")
        return cleaned


class CertificateResponse(BaseModel):
    """Schema for returning certificate details to the client."""

    id: int
    job_id: int
    recipient_name: str
    recipient_email: str
    status: str
    file_path: str | None = None
    error_message: str | None = None
    download_url: str | None = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class CertificateItemResponse(BaseModel):
    """Simplified schema for certificate list item response."""

    id: int
    recipient_name: str
    recipient_email: str
    status: str
    download_url: str | None = None
    error_message: str | None = None

    model_config = ConfigDict(from_attributes=True)
