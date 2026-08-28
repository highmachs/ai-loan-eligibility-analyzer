from datetime import datetime, timezone
from typing import List

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.audit_log import AuditLog, AuditAction
from app.models.customer import Customer
from app.models.document import CustomerDocument, VerificationStatus
from app.models.user import User, UserRole
from app.schemas.document import DocumentCreate, DocumentResponse, DocumentVerify
from app.services.auth_service import get_current_user

router = APIRouter(prefix="/api/documents", tags=["Customer Documents"])


def _require_verifier(current_user: User = Depends(get_current_user)) -> User:
    if current_user.role not in (UserRole.ADMIN, UserRole.SENIOR_CREDIT_MANAGER):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Senior Credit Manager or Admin access required.",
        )
    return current_user


@router.post("/", response_model=DocumentResponse, status_code=status.HTTP_201_CREATED)
def create_document(
    payload: DocumentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Upload a document record for a customer. Status defaults to PENDING."""
    customer = db.query(Customer).filter(Customer.id == payload.customer_id).first()
    if not customer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Customer with id {payload.customer_id} not found.",
        )

    doc = CustomerDocument(
        customer_id=payload.customer_id,
        document_type=payload.document_type,
        document_number=payload.document_number,
        verification_status=VerificationStatus.PENDING,
    )
    db.add(doc)
    db.commit()
    db.refresh(doc)
    return doc


@router.get("/customer/{customer_id}", response_model=List[DocumentResponse])
def list_documents_for_customer(
    customer_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    """List all document records for a given customer."""
    customer = db.query(Customer).filter(Customer.id == customer_id).first()
    if not customer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Customer with id {customer_id} not found.",
        )
    return (
        db.query(CustomerDocument)
        .filter(CustomerDocument.customer_id == customer_id)
        .order_by(CustomerDocument.created_at.desc())
        .all()
    )


@router.patch("/{doc_id}/verify", response_model=DocumentResponse)
def verify_document(
    doc_id: int,
    payload: DocumentVerify,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(_require_verifier),
):
    """Admin only: mark a document as VERIFIED or REJECTED and write an audit entry."""
    doc = db.query(CustomerDocument).filter(CustomerDocument.id == doc_id).first()
    if not doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Document with id {doc_id} not found.",
        )

    if payload.verification_status == VerificationStatus.PENDING:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot set status back to PENDING.",
        )

    previous = doc.verification_status.value
    doc.verification_status = payload.verification_status
    doc.verified_by_user_id = current_user.id
    doc.verified_at = datetime.now(timezone.utc)

    audit_action = (
        AuditAction.DOCUMENT_VERIFIED
        if payload.verification_status == VerificationStatus.VERIFIED
        else AuditAction.DOCUMENT_REJECTED
    )
    audit = AuditLog(
        user_id=current_user.id,
        action=audit_action,
        previous_status=previous,
        new_status=payload.verification_status.value,
        ip_address=request.client.host if request.client else None,
    )
    db.add(audit)
    db.commit()
    db.refresh(doc)
    return doc
