from sqlalchemy import Column, Integer, String, Numeric, Enum
import enum

from app.database import Base


class EmploymentType(str, enum.Enum):
    SALARIED = "SALARIED"
    SELF_EMPLOYED = "SELF_EMPLOYED"


class Gender(str, enum.Enum):
    MALE = "MALE"
    FEMALE = "FEMALE"
    OTHER = "OTHER"


class MaritalStatus(str, enum.Enum):
    SINGLE = "SINGLE"
    MARRIED = "MARRIED"
    DIVORCED = "DIVORCED"


class Customer(Base):
    __tablename__ = "customers"

    id = Column(Integer, primary_key=True, index=True)
    full_name = Column(String, nullable=False)
    age = Column(Integer, nullable=False)
    gender = Column(Enum(Gender), nullable=False)
    marital_status = Column(Enum(MaritalStatus), nullable=False)
    occupation = Column(String, nullable=False)
    company_name = Column(String, nullable=True)
    employment_type = Column(Enum(EmploymentType), nullable=False)
    years_of_experience = Column(Integer, nullable=False)
    monthly_salary = Column(Numeric(15, 2), nullable=False)
    other_income = Column(Numeric(15, 2), nullable=True, default=0)
    existing_emi = Column(Numeric(15, 2), nullable=False, default=0)
    current_loans = Column(Integer, nullable=False, default=0)
    credit_score = Column(Integer, nullable=False)
    missed_payments = Column(Integer, nullable=False, default=0)
    repayment_history = Column(String, nullable=True)
