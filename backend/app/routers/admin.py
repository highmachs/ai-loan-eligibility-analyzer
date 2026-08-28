import calendar
from datetime import datetime, timedelta, timezone
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func, case, extract, text

from app.database import get_db
from app.models.loan_application import LoanApplication, LoanStatus, LoanType
from app.models.ai_prediction import AIPrediction, RiskLevel
from app.models.user import User, UserRole
from app.schemas.user import UserCreate, UserResponse
from app.schemas.admin import (
    AdminReportsResponse,
    LoanApplicationSummary,
    RiskDistributionItem,
    LoanTypeItem,
    LoanAmountAnalysis,
    OfficerPerformanceItem,
    MonthlyStatItem,
    RetrainResponse,
    UserRoleUpdate,
)
from app.services.auth_service import get_current_user, hash_password, get_user_by_username

router = APIRouter(prefix="/api/admin", tags=["Admin"])


def _require_admin(current_user: User = Depends(get_current_user)) -> User:
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required.",
        )
    return current_user


def _require_admin_or_scm(current_user: User = Depends(get_current_user)) -> User:
    if current_user.role not in (UserRole.ADMIN, UserRole.SENIOR_CREDIT_MANAGER):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Senior Credit Manager or Admin access required.",
        )
    return current_user


# ── User Management ───────────────────────────────────────────────────────────

@router.get("/users", response_model=list[UserResponse])
def list_users(
    db: Session = Depends(get_db),
    _: User = Depends(_require_admin),
):
    """Admin only: list all registered users."""
    return db.query(User).order_by(User.id).all()


@router.post("/users", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def create_user(
    payload: UserCreate,
    db: Session = Depends(get_db),
    _: User = Depends(_require_admin),
):
    """Admin only: create a new user (Loan Officer or Admin)."""
    if get_user_by_username(db, payload.username):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already registered.",
        )
    user = User(
        username=payload.username,
        hashed_password=hash_password(payload.password),
        role=payload.role,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@router.patch("/users/{user_id}/role", response_model=UserResponse)
def change_user_role(
    user_id: int,
    payload: UserRoleUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(_require_admin),
):
    """Admin only: change a user's role."""
    if user_id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You cannot change your own role.",
        )
    try:
        new_role = UserRole(payload.role)
    except ValueError:
        valid = ", ".join(r.value for r in UserRole)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid role '{payload.role}'. Must be one of: {valid}.",
        )
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found.")
    user.role = new_role
    db.commit()
    db.refresh(user)
    return user


@router.delete("/users/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(_require_admin),
):
    """Admin only: delete a user. Nulls FK references first to avoid cascade errors (B2)."""
    if user_id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You cannot delete your own account.",
        )
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found.")

    # B2: Null FK references before delete so ON DELETE SET NULL triggers cleanly
    from app.models.loan_application import LoanApplication
    from app.models.audit_log import AuditLog
    db.query(LoanApplication).filter(
        LoanApplication.submitted_by_user_id == user_id
    ).update({"submitted_by_user_id": None}, synchronize_session=False)
    db.query(AuditLog).filter(
        AuditLog.user_id == user_id
    ).update({"user_id": None}, synchronize_session=False)
    db.flush()
    db.delete(user)
    db.commit()


# ── Reports ───────────────────────────────────────────────────────────────────

@router.get("/reports", response_model=AdminReportsResponse)
def get_admin_reports(
    db: Session = Depends(get_db),
    _: User = Depends(_require_admin_or_scm),
):
    # ── 1. Application Summary ───────────────────────────────────────────────
    total = db.query(LoanApplication).count()
    approved = db.query(LoanApplication).filter(LoanApplication.status == LoanStatus.APPROVED).count()
    rejected = db.query(LoanApplication).filter(LoanApplication.status == LoanStatus.REJECTED).count()
    pending = db.query(LoanApplication).filter(LoanApplication.status == LoanStatus.PENDING).count()
    summary = LoanApplicationSummary(total=total, approved=approved, rejected=rejected, pending=pending)

    # ── 2. Risk Distribution ─────────────────────────────────────────────────
    risk_rows = (
        db.query(AIPrediction.risk_level, func.count(AIPrediction.id))
        .group_by(AIPrediction.risk_level)
        .all()
    )
    risk_distribution = [
        RiskDistributionItem(risk_level=row[0].value if hasattr(row[0], "value") else str(row[0]), count=row[1])
        for row in risk_rows
    ]

    # ── 3. Loan Type Breakdown ───────────────────────────────────────────────
    type_rows = (
        db.query(LoanApplication.loan_type, func.count(LoanApplication.id))
        .group_by(LoanApplication.loan_type)
        .all()
    )
    loan_type_breakdown = [
        LoanTypeItem(loan_type=row[0].value if hasattr(row[0], "value") else str(row[0]), count=row[1])
        for row in type_rows
    ]

    # ── 4. Loan Amount Analysis ──────────────────────────────────────────────
    total_requested = db.query(func.sum(LoanApplication.requested_amount)).scalar() or Decimal("0")
    total_recommended = db.query(func.sum(AIPrediction.recommended_amount)).scalar() or Decimal("0")
    avg_loan = (Decimal(str(total_requested)) / total) if total > 0 else Decimal("0")
    amount_analysis = LoanAmountAnalysis(
        total_requested=Decimal(str(total_requested)),
        total_recommended=Decimal(str(total_recommended)),
        average_loan=round(avg_loan, 2),
    )

    # ── 5. Officer Performance ───────────────────────────────────────────────
    officers = db.query(User).filter(User.role == UserRole.LOAN_OFFICER).all()
    officer_performance = []
    for officer in officers:
        apps = db.query(LoanApplication).filter(
            LoanApplication.submitted_by_user_id == officer.id
        )
        off_approved = apps.filter(LoanApplication.status == LoanStatus.APPROVED).count()
        off_rejected = apps.filter(LoanApplication.status == LoanStatus.REJECTED).count()
        officer_performance.append(
            OfficerPerformanceItem(
                username=officer.username,
                applications=apps.count(),
                approved=off_approved,
                rejected=off_rejected,
            )
        )

    return AdminReportsResponse(
        summary=summary,
        risk_distribution=risk_distribution,
        loan_type_breakdown=loan_type_breakdown,
        amount_analysis=amount_analysis,
        officer_performance=officer_performance,
    )


@router.get("/monthly-stats", response_model=list[MonthlyStatItem])
def get_monthly_stats(
    db: Session = Depends(get_db),
    _: User = Depends(_require_admin_or_scm),
):
    """Admin only: monthly loan application counts — last 12 calendar months (B7)."""
    twelve_months_ago = datetime.now(timezone.utc) - timedelta(days=365)
    year_col = extract("year", LoanApplication.created_date)
    month_col = extract("month", LoanApplication.created_date)

    rows = (
        db.query(
            year_col.label("year"),
            month_col.label("month"),
            func.count(LoanApplication.id).label("total"),
            func.sum(
                case((LoanApplication.status == LoanStatus.APPROVED, 1), else_=0)
            ).label("approved"),
            func.sum(
                case((LoanApplication.status == LoanStatus.REJECTED, 1), else_=0)
            ).label("rejected"),
            func.sum(
                case((LoanApplication.status == LoanStatus.PENDING, 1), else_=0)
            ).label("pending"),
        )
        .filter(LoanApplication.created_date >= twelve_months_ago)  # B7 fix
        .group_by(year_col, month_col)
        .order_by(year_col, month_col)
        .all()
    )

    result = []
    for row in rows:
        yr, mo = int(row.year), int(row.month)
        label = f"{calendar.month_abbr[mo]} {yr}"
        result.append(
            MonthlyStatItem(
                year=yr,
                month=mo,
                month_label=label,
                total=row.total,
                approved=int(row.approved or 0),
                rejected=int(row.rejected or 0),
                pending=int(row.pending or 0),
            )
        )
    return result


# ── Model Retraining ──────────────────────────────────────────────────────────

@router.post("/retrain", response_model=RetrainResponse)
def retrain_model_endpoint(
    _: User = Depends(_require_admin),
):
    from app.services.prediction_service import retrain_model
    try:
        result = retrain_model()
        return RetrainResponse(status=result["status"], output=result["output"])
    except RuntimeError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )
