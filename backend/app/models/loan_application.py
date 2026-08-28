from sqlalchemy import Column, Integer, String, Numeric, Enum, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum

from app.database import Base


class LoanType(str, enum.Enum):
    HOME = "HOME"
    PERSONAL = "PERSONAL"
    CAR = "CAR"


class LoanStatus(str, enum.Enum):
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"


class LoanApplication(Base):
    __tablename__ = "loan_applications"

    id = Column(Integer, primary_key=True, index=True)
    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=False)
    loan_type = Column(Enum(LoanType), nullable=False)
    requested_amount = Column(Numeric(15, 2), nullable=False)
    tenure_months = Column(Integer, nullable=False)
    status = Column(Enum(LoanStatus), nullable=False, default=LoanStatus.PENDING)
    created_date = Column(DateTime(timezone=True), server_default=func.now())
    submitted_by_user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)

    customer = relationship("Customer", foreign_keys=[customer_id])
    submitted_by = relationship("User", foreign_keys=[submitted_by_user_id])
