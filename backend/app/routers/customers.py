from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List

from app.database import get_db
from app.models.audit_log import AuditLog, AuditAction
from app.models.customer import Customer
from app.models.user import User, UserRole
from app.schemas.customer import CustomerCreate, CustomerResponse
from app.schemas.loan_application import LoanApplicationResponse
from app.services.auth_service import get_current_user

router = APIRouter(prefix="/api/customers", tags=["Customers"])


@router.post("/", response_model=CustomerResponse, status_code=status.HTTP_201_CREATED)
def create_customer(
    payload: CustomerCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # Normalize company name
    company = (payload.company_name or "").strip()

    # Comprehensive duplicate check matching all customer profile attributes safely in SQL
    existing = (
        db.query(Customer)
        .filter(
            Customer.full_name == payload.full_name,
            Customer.age == payload.age,
            Customer.gender == payload.gender,
            Customer.marital_status == payload.marital_status,
            Customer.occupation == payload.occupation,
            func.coalesce(Customer.company_name, "") == company,
            Customer.employment_type == payload.employment_type,
            Customer.years_of_experience == payload.years_of_experience,
            Customer.monthly_salary == payload.monthly_salary,
            Customer.other_income == payload.other_income,
            Customer.existing_emi == payload.existing_emi,
            Customer.current_loans == payload.current_loans,
            Customer.credit_score == payload.credit_score,
            Customer.missed_payments == payload.missed_payments,
        )
        .first()
    )
    if existing:
        return existing

    customer = Customer(**payload.model_dump())
    db.add(customer)
    db.flush()  # get customer.id before audit log

    # ── Audit Log: record new customer creation ───────────────────────────────
    audit = AuditLog(
        user_id=current_user.id,
        application_id=None,
        action=AuditAction.CREATED,
        new_status=f"Customer #{customer.id} created",
        ip_address=request.client.host if request.client else None,
    )
    db.add(audit)

    db.commit()
    db.refresh(customer)
    return customer


@router.get("/", response_model=List[CustomerResponse])
def list_customers(
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    return db.query(Customer).offset(skip).limit(limit).all()


@router.get("/{customer_id}", response_model=CustomerResponse)
def get_customer(
    customer_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    customer = db.query(Customer).filter(Customer.id == customer_id).first()
    if not customer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Customer with id {customer_id} not found.",
        )
    return customer


@router.get("/{customer_id}/loans", response_model=List[LoanApplicationResponse])
def get_customer_loans(
    customer_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Return all loan applications for a customer. Admins see all; officers see only their own."""
    from app.models.loan_application import LoanApplication
    from app.schemas.loan_application import LoanApplicationResponse

    customer = db.query(Customer).filter(Customer.id == customer_id).first()
    if not customer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Customer with id {customer_id} not found.",
        )
    query = db.query(LoanApplication).filter(LoanApplication.customer_id == customer_id)
    if current_user.role not in (UserRole.ADMIN, UserRole.SENIOR_CREDIT_MANAGER):
        query = query.filter(LoanApplication.submitted_by_user_id == current_user.id)
    loans = query.order_by(LoanApplication.created_date.desc()).all()
    return [LoanApplicationResponse.model_validate(l) for l in loans]
