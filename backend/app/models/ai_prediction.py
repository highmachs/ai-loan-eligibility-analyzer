from sqlalchemy import Column, Integer, String, Numeric, Enum, ForeignKey, DateTime, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum

from app.database import Base


class RiskLevel(str, enum.Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"


class AIPrediction(Base):
    __tablename__ = "ai_predictions"

    id = Column(Integer, primary_key=True, index=True)
    application_id = Column(Integer, ForeignKey("loan_applications.id"), nullable=False, unique=True)
    approval_probability = Column(Numeric(5, 2), nullable=False)
    risk_level = Column(Enum(RiskLevel), nullable=False)
    recommended_amount = Column(Numeric(15, 2), nullable=False)
    foir = Column(Numeric(5, 2), nullable=True)
    reason = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    application = relationship("LoanApplication", foreign_keys=[application_id])
