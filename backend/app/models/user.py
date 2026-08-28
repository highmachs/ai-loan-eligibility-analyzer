from sqlalchemy import Column, Integer, String, Enum
import enum

from app.database import Base


class UserRole(str, enum.Enum):
    LOAN_OFFICER = "LOAN_OFFICER"
    SENIOR_CREDIT_MANAGER = "SENIOR_CREDIT_MANAGER"
    ADMIN = "ADMIN"


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, nullable=False, index=True)
    hashed_password = Column(String, nullable=False)
    role = Column(Enum(UserRole), nullable=False, default=UserRole.LOAN_OFFICER)
