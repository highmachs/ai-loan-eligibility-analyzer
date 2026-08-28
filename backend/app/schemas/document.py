from pydantic import BaseModel, Field
from decimal import Decimal
from datetime import datetime
from typing import Optional

from app.models.document import DocumentType, VerificationStatus


class DocumentCreate(BaseModel):
    customer_id: int
    document_type: DocumentType
    document_number: str = Field(..., min_length=1, max_length=50)


class DocumentVerify(BaseModel):
    verification_status: VerificationStatus


class DocumentResponse(BaseModel):
    id: int
    customer_id: int
    document_type: DocumentType
    document_number: str
    verification_status: VerificationStatus
    verified_by_user_id: Optional[int] = None
    verified_at: Optional[datetime] = None
    created_at: datetime

    class Config:
        from_attributes = True
