from pydantic import BaseModel, Field
from typing import Optional
from decimal import Decimal
from enum import Enum
from app.models.customer import EmploymentType, Gender, MaritalStatus


class RepaymentHistory(str, Enum):
    GOOD = "GOOD"
    FAIR = "FAIR"
    POOR = "POOR"
    NONE = "NONE"


class CustomerCreate(BaseModel):
    full_name: str
    age: int = Field(..., ge=18, le=75)
    gender: Gender
    marital_status: MaritalStatus

    occupation: str
    company_name: Optional[str] = None
    employment_type: EmploymentType
    years_of_experience: int = Field(..., ge=0)

    monthly_salary: Decimal = Field(..., gt=0)
    other_income: Optional[Decimal] = Decimal("0")
    existing_emi: Decimal = Field(..., ge=0)
    current_loans: int = Field(..., ge=0)

    credit_score: int = Field(..., ge=300, le=900)
    missed_payments: int = Field(..., ge=0)
    repayment_history: Optional[RepaymentHistory] = None


class CustomerResponse(BaseModel):
    id: int
    full_name: str
    age: int
    gender: Gender
    marital_status: MaritalStatus
    occupation: str
    company_name: Optional[str]
    employment_type: EmploymentType
    years_of_experience: int
    monthly_salary: Decimal
    other_income: Optional[Decimal]
    existing_emi: Decimal
    current_loans: int
    credit_score: int
    missed_payments: int
    repayment_history: Optional[str]  # str to handle legacy free-text DB rows

    class Config:
        from_attributes = True
