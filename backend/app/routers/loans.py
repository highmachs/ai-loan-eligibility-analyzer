from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List

from app.database import get_db
from app.models.audit_log import AuditLog, AuditAction
from app.models.loan_application import LoanApplication, LoanStatus
from app.models.ai_prediction import AIPrediction, RiskLevel
from app.models.customer import Customer
from app.models.user import User, UserRole
from app.schemas.loan_application import (
    LoanApplicationCreate,
    LoanApplicationResponse,
    LoanStatusUpdate,
    LoanStatsResponse,
    DeleteDuplicatesResponse,
)
from app.services.auth_service import get_current_user
from app.services.prediction_service import evaluate_risk

router = APIRouter(prefix="/api/loans", tags=["Loan Applications"])

# Multi-level approval thresholds (B6 — 3-tier hierarchy)
OFFICER_MAX_AMOUNT = _OFFICER_APPROVAL_LIMIT = Decimal("500000")    # Loan Officer: <= 5 Lakhs
SCM_MAX_AMOUNT     = _SCM_APPROVAL_LIMIT     = Decimal("2500000")   # Senior Credit Manager: <= 25 Lakhs
# Admin has unlimited authority (up to system cap of 10 Crore)


@router.post("/", response_model=LoanApplicationResponse, status_code=status.HTTP_201_CREATED)
def create_loan_application(
    payload: LoanApplicationCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    customer = db.query(Customer).filter(Customer.id == payload.customer_id).first()
    if not customer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Customer with id {payload.customer_id} not found.",
        )
    # Deduplication guard: return existing pending application if identical details are re-submitted
    existing = (
        db.query(LoanApplication)
        .filter(
            LoanApplication.customer_id == payload.customer_id,
            LoanApplication.loan_type == payload.loan_type,
            LoanApplication.requested_amount == payload.requested_amount,
            LoanApplication.tenure_months == payload.tenure_months,
            LoanApplication.status == LoanStatus.PENDING,
        )
        .first()
    )
    if existing:
        return existing

    application = LoanApplication(
        **payload.model_dump(),
        submitted_by_user_id=current_user.id,
    )
    db.add(application)
    db.flush()  # get application.id before prediction and audit log

    # Evaluate AI risk prediction immediately on creation
    risk_level_str, approval_probability, reason, recommended_amount, foir = evaluate_risk(
        customer, application
    )
    prediction = AIPrediction(
        application_id=application.id,
        approval_probability=approval_probability,
        risk_level=RiskLevel(risk_level_str),
        recommended_amount=recommended_amount,
        foir=foir,
        reason=reason,
    )
    db.add(prediction)

    # Audit: record application creation and AI scoring for full lifecycle traceability
    audit_created = AuditLog(
        user_id=current_user.id,
        application_id=application.id,
        action=AuditAction.CREATED,
        new_status=application.status.value,
        ip_address=request.client.host if request.client else None,
    )
    audit_scored = AuditLog(
        user_id=current_user.id,
        application_id=application.id,
        action=AuditAction.AI_SCORED,
        new_status=risk_level_str,
        ip_address=request.client.host if request.client else None,
    )
    db.add(audit_created)
    db.add(audit_scored)
    db.commit()
    db.refresh(application)
    return application


@router.get("/stats", response_model=LoanStatsResponse)
def get_loan_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = db.query(LoanApplication)
    # ADMIN and SENIOR_CREDIT_MANAGER have cross-portfolio visibility; LOAN_OFFICER sees only their own
    if current_user.role not in (UserRole.ADMIN, UserRole.SENIOR_CREDIT_MANAGER):
        query = query.filter(LoanApplication.submitted_by_user_id == current_user.id)
    total = query.count()
    approved = query.filter(LoanApplication.status == LoanStatus.APPROVED).count()
    rejected = query.filter(LoanApplication.status == LoanStatus.REJECTED).count()
    pending = query.filter(LoanApplication.status == LoanStatus.PENDING).count()
    return LoanStatsResponse(total=total, approved=approved, rejected=rejected, pending=pending)


@router.get("/", response_model=List[LoanApplicationResponse])
def list_loan_applications(
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = db.query(LoanApplication)
    if current_user.role not in (UserRole.ADMIN, UserRole.SENIOR_CREDIT_MANAGER):
        query = query.filter(LoanApplication.submitted_by_user_id == current_user.id)
    return query.offset(skip).limit(limit).all()


@router.get("/{loan_id}", response_model=LoanApplicationResponse)
def get_loan_application(
    loan_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = db.query(LoanApplication).filter(LoanApplication.id == loan_id)
    if current_user.role not in (UserRole.ADMIN, UserRole.SENIOR_CREDIT_MANAGER):
        query = query.filter(LoanApplication.submitted_by_user_id == current_user.id)
    application = query.first()
    if not application:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Loan application with id {loan_id} not found.",
        )
    return application


@router.patch("/{loan_id}/status", response_model=LoanApplicationResponse)
def update_loan_status(
    loan_id: int,
    payload: LoanStatusUpdate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = db.query(LoanApplication).filter(LoanApplication.id == loan_id)
    if current_user.role not in (UserRole.ADMIN, UserRole.SENIOR_CREDIT_MANAGER):
        query = query.filter(LoanApplication.submitted_by_user_id == current_user.id)
    application = query.first()
    if not application:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Loan application with id {loan_id} not found.",
        )

    # ── Multi-Level Approval Hierarchy (B6 — 3 tiers) ──────────────────────────
    if payload.status == LoanStatus.APPROVED:
        amount = Decimal(str(application.requested_amount))
        role = current_user.role
        if role == UserRole.LOAN_OFFICER and amount > _OFFICER_APPROVAL_LIMIT:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=(
                    f"Loan Officers can only approve loans up to ₹5,00,000. "
                    f"This application (₹{amount:,.0f}) requires a Senior Credit Manager or Admin."
                ),
            )
        if role == UserRole.SENIOR_CREDIT_MANAGER and amount > _SCM_APPROVAL_LIMIT:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=(
                    f"Senior Credit Managers can only approve loans up to ₹25,00,000. "
                    f"This application (₹{amount:,.0f}) requires Admin / Credit Committee approval."
                ),
            )

    previous_status = application.status.value
    application.status = payload.status
    db.flush()  # write change before audit log to ensure consistency

    # ── Audit Log: record every APPROVED / REJECTED action ───────────────────
    if payload.status in (LoanStatus.APPROVED, LoanStatus.REJECTED):
        audit_action = (
            AuditAction.APPROVED
            if payload.status == LoanStatus.APPROVED
            else AuditAction.REJECTED
        )
        audit = AuditLog(
            user_id=current_user.id,
            application_id=application.id,
            action=audit_action,
            previous_status=previous_status,
            new_status=payload.status.value,
            ip_address=request.client.host if request.client else None,
        )
        db.add(audit)

    db.commit()
    db.refresh(application)
    return application


@router.delete("/duplicates", response_model=DeleteDuplicatesResponse)
def delete_duplicate_loan_applications(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Identifies and deletes duplicate loan application rows.
    Duplicates are records sharing the same (customer_id, loan_type,
    requested_amount, tenure_months, status). The earliest record
    (lowest id) is kept; all subsequent duplicates and their linked
    ai_predictions are permanently removed.
    """
    # Find the canonical (earliest) id for each unique customer loan application combination.
    canonical_subq = (
        db.query(func.min(LoanApplication.id).label("min_id"))
        .group_by(
            LoanApplication.customer_id,
            LoanApplication.loan_type,
            LoanApplication.requested_amount,
            LoanApplication.tenure_months,
        )
        .subquery()
    )

    # Query to build the scope: non-admins can only delete their own duplicates.
    scope = db.query(LoanApplication)
    if current_user.role != UserRole.ADMIN:
        scope = scope.filter(
            LoanApplication.submitted_by_user_id == current_user.id
        )

    # Collect all duplicate records (those NOT in the canonical set).
    duplicate_apps = (
        scope.filter(LoanApplication.id.notin_(db.query(canonical_subq.c.min_id)))
        .all()
    )

    if not duplicate_apps:
        return DeleteDuplicatesResponse(
            message="No duplicate records found.",
            deleted_count=0,
            deleted_ids=[],
        )

    duplicate_ids = [app.id for app in duplicate_apps]

    # Delete dependent ai_predictions first to satisfy foreign-key constraint.
    db.query(AIPrediction).filter(
        AIPrediction.application_id.in_(duplicate_ids)
    ).delete(synchronize_session=False)

    # Delete the duplicate loan applications.
    db.query(LoanApplication).filter(
        LoanApplication.id.in_(duplicate_ids)
    ).delete(synchronize_session=False)

    db.commit()

    return DeleteDuplicatesResponse(
        message=f"Successfully deleted {len(duplicate_ids)} duplicate record(s).",
        deleted_count=len(duplicate_ids),
        deleted_ids=sorted(duplicate_ids),
    )
