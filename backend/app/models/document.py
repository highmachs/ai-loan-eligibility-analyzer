from sqlalchemy import Column, Integer, String, Enum, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum

from app.database import Base


class DocumentType(str, enum.Enum):
    PAN_CARD = "PAN_CARD"
    AADHAAR = "AADHAAR"
    FORM_16 = "FORM_16"
    BANK_STATEMENT = "BANK_STATEMENT"


class VerificationStatus(str, enum.Enum):
    PENDING = "PENDING"
    VERIFIED = "VERIFIED"
    REJECTED = "REJECTED"


class CustomerDocument(Base):
    __tablename__ = "customer_documents"

    id = Column(Integer, primary_key=True, index=True)
    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=False, index=True)
    document_type = Column(Enum(DocumentType), nullable=False)
    document_number = Column(String, nullable=False)
    verification_status = Column(
        Enum(VerificationStatus), nullable=False, default=VerificationStatus.PENDING
    )
    verified_by_user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    verified_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    customer = relationship("Customer", foreign_keys=[customer_id])
    verified_by = relationship("User", foreign_keys=[verified_by_user_id])
