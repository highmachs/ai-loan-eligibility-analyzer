from pydantic import BaseModel
from datetime import datetime
from typing import Optional

from app.models.audit_log import AuditAction


class AuditLogResponse(BaseModel):
    id: int
    user_id: int
    application_id: Optional[int] = None
    action: AuditAction
    previous_status: Optional[str] = None
    new_status: Optional[str] = None
    ip_address: Optional[str] = None
    timestamp: datetime

    class Config:
        from_attributes = True
