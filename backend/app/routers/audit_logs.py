from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.audit_log import AuditLog
from app.models.user import User, UserRole
from app.schemas.audit_log import AuditLogResponse
from app.services.auth_service import get_current_user

router = APIRouter(prefix="/api/audit-logs", tags=["Audit Logs"])


def _require_admin(current_user: User = Depends(get_current_user)) -> User:
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required.",
        )
    return current_user


@router.get("/", response_model=List[AuditLogResponse])
def list_audit_logs(
    application_id: Optional[int] = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    _: User = Depends(_require_admin),
):
    """Admin only: list all audit log entries, optionally filtered by application_id."""
    query = db.query(AuditLog)
    if application_id is not None:
        query = query.filter(AuditLog.application_id == application_id)
    return (
        query.order_by(AuditLog.timestamp.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )


@router.get("/{application_id}", response_model=List[AuditLogResponse])
def get_audit_logs_for_application(
    application_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(_require_admin),
):
    """Admin only: full audit history for a specific loan application."""
    logs = (
        db.query(AuditLog)
        .filter(AuditLog.application_id == application_id)
        .order_by(AuditLog.timestamp.asc())
        .all()
    )
    if not logs:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No audit logs found for application {application_id}.",
        )
    return logs
