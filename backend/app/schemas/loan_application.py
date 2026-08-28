from pydantic import BaseModel, Field
from decimal import Decimal
from datetime import datetime
from typing import Optional
from app.models.loan_application import LoanType, LoanStatus
from app.schemas.customer import CustomerResponse

# Max requestable loan amount: ₹10 crore (B11)
_MAX_LOAN_AMOUNT = Decimal("100_000_000")


class LoanApplicationCreate(BaseModel):
    customer_id: int
    loan_type: LoanType
    requested_amount: Decimal = Field(..., gt=0, le=_MAX_LOAN_AMOUNT)  # B11: max ₹10 crore
    tenure_months: int = Field(..., ge=6, le=360)


class LoanApplicationResponse(BaseModel):
    id: int
    customer_id: int
    submitted_by_user_id: Optional[int] = None  # B3: expose for Dashboard History link
    loan_type: LoanType
    requested_amount: Decimal
    tenure_months: int
    status: LoanStatus
    created_date: datetime
    customer: Optional[CustomerResponse] = None

    class Config:
        from_attributes = True


class LoanStatusUpdate(BaseModel):
    status: LoanStatus


class LoanStatsResponse(BaseModel):
    total: int
    approved: int
    rejected: int
    pending: int


class DeleteDuplicatesResponse(BaseModel):
    message: str
    deleted_count: int
    deleted_ids: list[int]
